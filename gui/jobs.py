"""Bounded, single-flight jobs for the local GUI's read-only work."""
import secrets
import threading
import time

if __package__:
    from . import activity
else:
    import activity


MAX_JOBS = 16
RETENTION_SECONDS = 600
JOB_BUDGET = 180


class Cancelled(ValueError):
    pass


class Busy(ValueError):
    pass


class MissingJob(ValueError):
    pass


class Job:
    def __init__(self, kind, request=None):
        self.id = secrets.token_urlsafe(18)
        self.kind = kind
        self.request = dict(request or {"kind": kind})
        self.started_at = time.time()
        self.started_mono = time.monotonic()
        self.finished_mono = None
        self.cancelled = threading.Event()
        self.lock = threading.Lock()
        self.status = "running"
        self.stage = "Starting"
        self.result = None
        self.error = None
        self.sampled_at = None
        self.thread = None
        self.activity = activity.Tail() if kind == "preview" else None

    def check(self):
        if self.cancelled.is_set():
            raise Cancelled("Operation cancelled.")

    def remaining(self, maximum):
        self.check()
        remaining = JOB_BUDGET - (time.monotonic() - self.started_mono)
        if remaining <= 0:
            raise ValueError("The read-only operation exceeded its time limit.")
        return min(maximum, remaining)

    def set_stage(self, stage):
        with self.lock:
            if not self.cancelled.is_set():
                self.stage = stage

    def snapshot(self):
        with self.lock:
            return {"id": self.id, "kind": self.kind, "status": self.status,
                    "stage": self.stage, "started_at": self.started_at,
                    "elapsed_seconds": round(max(0, (self.finished_mono or time.monotonic()) - self.started_mono), 2),
                    "progress": None, "result": self.result, "error": self.error,
                    "sampled_at": self.sampled_at, "request": self.request,
                    "activity": self.activity.snapshot() if self.activity is not None else
                    {"lines": [], "total_lines": 0, "truncated": False}}


class Registry:
    def __init__(self, work_lock):
        self.work_lock = work_lock
        self.lock = threading.Lock()
        self.jobs = {}
        self.active = None
        self.closing = False

    def _prune(self):
        now = time.monotonic()
        self.jobs = {key: job for key, job in self.jobs.items()
                     if job.finished_mono is None or now - job.finished_mono < RETENTION_SECONDS}
        while len(self.jobs) >= MAX_JOBS:
            removable = next((key for key, job in self.jobs.items() if job.finished_mono is not None), None)
            if removable is None:
                raise Busy("An operation is already running.")
            self.jobs.pop(removable)

    def start(self, kind, task, request=None):
        with self.lock:
            if self.closing:
                raise ValueError("The GUI is closing.")
            self._prune()
            if self.active is not None or not self.work_lock.acquire(blocking=False):
                raise Busy("An operation is already running. Let it finish or cancel it first.")
            job = Job(kind, request)
            self.active = job.id
            self.jobs[job.id] = job
            job.thread = threading.Thread(target=self._run, args=(job, task), name="mole-gui-job")
            try:
                job.thread.start()
            except BaseException:
                self.jobs.pop(job.id)
                self.active = None
                self.work_lock.release()
                raise
            return {"id": job.id}

    def _run(self, job, task):
        try:
            result = task(job)
            if job.activity is not None:
                job.activity.finish()
            with job.lock:
                # Cancellation is authoritative even if output arrived just
                # before the process finished. It never publishes a late result.
                if job.cancelled.is_set():
                    job.status, job.stage = "cancelled", "Cancelled"
                else:
                    job.result = result
                    job.sampled_at = result.get("sampled_at", time.time()) if isinstance(result, dict) else time.time()
                    job.status, job.stage = "completed", "Complete"
        except Exception as error:
            if job.activity is not None:
                job.activity.finish()
            with job.lock:
                if isinstance(error, Cancelled) or job.cancelled.is_set():
                    job.status, job.stage = "cancelled", "Cancelled"
                else:
                    job.error = str(error)[:2000] or "Mole could not complete this read-only operation."
                    job.status, job.stage = "failed", "Failed"
        finally:
            with job.lock:
                job.finished_mono = time.monotonic()
            with self.lock:
                if self.active == job.id:
                    self.active = None
                self.work_lock.release()

    def _get(self, key):
        if not isinstance(key, str) or len(key) > 128:
            raise ValueError("Choose a valid operation.")
        with self.lock:
            job = self.jobs.get(key)
            if job is None or (job.finished_mono is not None
                               and time.monotonic() - job.finished_mono >= RETENTION_SECONDS):
                raise MissingJob("This operation expired. Start a fresh request.")
            return job

    def snapshot(self, key):
        return self._get(key).snapshot()

    def active_snapshot(self):
        with self.lock:
            job = self.jobs.get(self.active)
        value = job.snapshot() if job is not None else None
        return {"active": value if value is not None and value["status"] == "running" else None}

    def cancel(self, key):
        job = self._get(key)
        with job.lock:
            if job.status == "running":
                job.cancelled.set()
                job.stage = "Stopping"
        return job.snapshot()

    def close(self):
        with self.lock:
            self.closing = True
            pending = list(self.jobs.values())
            for job in pending:
                job.cancelled.set()
        for job in pending:
            if job.thread is not None and job.thread is not threading.current_thread():
                job.thread.join()
