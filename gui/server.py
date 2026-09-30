#!/usr/bin/env python3
"""Local-only Mole GUI. No web dependencies, remote resources, or daemon install."""
import argparse
import hmac
import json
import os
from pathlib import Path
import platform
import re
import secrets
import selectors
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
import webbrowser

if __package__:
    from . import analysis_reports, browser, jobs, preview_reports, processes
else:
    import analysis_reports
    import browser
    import jobs
    import preview_reports
    import processes

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "gui" / "web"
CATALOG = json.loads((ROOT / "gui" / "catalog.json").read_text())
COMMANDS = {item["id"]: item for item in CATALOG}
PERSONAL = {"Downloads", "Desktop", "Documents", "Pictures", "Movies", "Music"}
MAX_OUTPUT = 2 * 1024 * 1024
SELECTION_TTL = 300
PLAN_TTL = 120
PREVIEW_ATTEMPT_BUDGET = 45
TRASH_ATTEMPT_BUDGET = 120
OPERATION_BUDGET = 180
TRASH_ACK = "GUI_TRASH_CONFIRMED"


class ShutdownRequested(BaseException):
    pass


def run_bounded(argv, timeout=20, env=None, cancel=None, input_data=None, owned=True, max_output=None, on_output=None):
    """Kill the whole subprocess group on timeout, including shell probe children."""
    if cancel is not None and cancel.is_set():
        raise jobs.Cancelled("Operation cancelled.")
    # Only the fixed selected-app dry-run runner supplies the one confirmation.
    # There is no API accepting executable, argv, environment, or stdin.
    if input_data is not None and input_data != b"y\n":
        raise ValueError("Unsupported preview input.")
    process = subprocess.Popen(argv, stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, start_new_session=True, env=env)
    deadline = time.monotonic() + timeout
    limit = MAX_OUTPUT if max_output is None else max_output
    data = bytearray()
    try:
        if input_data is not None:
            try:
                process.stdin.write(input_data)
                process.stdin.flush()
            except BrokenPipeError:
                pass
            finally:
                process.stdin.close()
        with selectors.DefaultSelector() as reader:
            reader.register(process.stdout, selectors.EVENT_READ)
            while reader.get_map():
                if cancel is not None and cancel.is_set():
                    raise jobs.Cancelled("Operation cancelled.")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(argv, timeout)
                for event, _ in reader.select(min(remaining, 0.1)):
                    chunk = os.read(event.fd, 65536)
                    if not chunk:
                        reader.unregister(event.fileobj)
                        continue
                    if on_output is not None:
                        on_output(chunk)
                    data.extend(chunk)
                    if len(data) > limit:
                        raise ValueError("Report is too large. Use the Terminal view for this operation.")
        # A process may close stdout and remain alive. Poll its lifecycle too so
        # cancellation never waits for the whole original timeout.
        while process.poll() is None:
            if cancel is not None and cancel.is_set():
                raise jobs.Cancelled("Operation cancelled.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(argv, timeout)
            try:
                process.wait(timeout=min(remaining, 0.1))
            except subprocess.TimeoutExpired:
                continue
        code = process.returncode
        if cancel is not None and cancel.is_set():
            raise jobs.Cancelled("Operation cancelled.")
    except BaseException as error:
        if owned:
            # Mole's timeout wrappers can create nested groups in the same
            # session. Enumerate numeric PID/PGID columns only, with an output
            # cap and one-second bound; revalidate session ownership at each
            # group signal. Native handoffs never enter this path.
            processes.stop_session(process, lambda: run_bounded(
                ["/bin/ps", "-axo", "pid=,pgid="], timeout=1, env={"LC_ALL": "C"},
                owned=False, max_output=256 * 1024))
        elif process.poll() is None:
            process.kill()
        process.wait()
        if isinstance(error, subprocess.TimeoutExpired):
            raise ValueError("Operation timed out. Refresh the view before trying again.") from None
        raise
    finally:
        process.stdout.close()
    output = data.decode("utf-8", errors="replace")
    if code:
        clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", output).strip()
        raise ValueError(clean[-2000:] or "Mole kept this item or could not complete the operation.")
    return output


def command_args(data):
    if (not isinstance(data, dict) or not isinstance(data.get("command"), str)
            or data["command"] not in COMMANDS):
        raise ValueError("Choose a supported Mole command.")
    if set(data) - {"command", "flags", "fields"}:
        raise ValueError("Unsupported command input.")
    cmd = COMMANDS[data["command"]]
    flags, fields = data.get("flags", []), data.get("fields", {})
    allowed = {flag[0] for flag in cmd["flags"]}
    allowed.add("debug")  # Global router flag.
    if cmd["id"] not in {"update", "remove", "help", "version"}:
        allowed.add("help")
    if (not isinstance(flags, list) or any(not isinstance(f, str) or f not in allowed for f in flags)
            or len(flags) != len(set(flags))):
        raise ValueError("Unsupported or duplicate command option.")
    specs = {field["key"]: field for field in cmd.get("fields", [])}
    if not isinstance(fields, dict) or set(fields) - set(specs):
        raise ValueError("Unsupported command field.")
    # Management flags enter interactive writers before later router options.
    # Help must remain a read-only handoff regardless of current form values.
    if "help" in flags:
        return [cmd["id"], "--help"]
    args = [cmd["id"]] + ["--" + flag for flag in flags]
    positionals = []
    for key, value in fields.items():
        if not isinstance(value, str) or len(value) > 4096 or "\0" in value:
            raise ValueError("Invalid field value.")
        value = value.strip()
        if not value:
            continue
        spec = specs[key]
        kind = spec["type"]
        if kind == "select" and value not in {v[0] for v in spec["values"]}:
            raise ValueError("Choose one of the available options.")
        if kind == "number":
            if not re.fullmatch(r"\d+(?:\.\d+)?", value):
                raise ValueError("Enter a positive number.")
            if not spec["min"] <= float(value) <= spec["max"] or (key == "limit" and not value.isdigit()):
                raise ValueError("The number is outside the supported range.")
        if kind == "duration" and (not re.fullmatch(r"(?:\d+(?:\.\d+)?(?:ms|s|m|h))+", value)
                                   or len(value) > 64
                                   or not any(float(n) > 0 for n in re.findall(r"\d+(?:\.\d+)?", value))):
            raise ValueError("Use a positive duration such as 2s or 5m.")
        if key == "interval" and "watch" not in flags:
            raise ValueError("Collection interval requires Stream snapshots.")
        if kind == "path":
            value = os.path.expanduser(value)
            if not Path(value).is_absolute() or any(c in value for c in "\r\n"):
                raise ValueError("Enter an absolute path or a path starting with ~/.")
        if kind == "apps":
            names = [name.strip() for name in value.splitlines() if name.strip()]
            if len(names) > 50 or any(name.startswith("-") for name in names):
                raise ValueError("Enter exact app names, one per line, without command flags.")
            positionals.extend(names)
        elif key in {"action", "shell", "path"}:
            positionals.append(value)
        elif key == "proc-cpu-alerts":
            args.append("--proc-cpu-alerts=" + value)
        else:
            args.extend(["--" + key, value])
    return args + positionals


def identity(path):
    item = path.lstat()
    parent = path.parent.stat()
    return (item.st_dev, item.st_ino, item.st_mtime_ns, item.st_size,
            parent.st_dev, parent.st_ino)


def readable_output(text):
    text = re.sub(r"\x1b\][^\x07]*(?:\x07|\x1b\\)", "", text)
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    return "".join(char for char in text if char in "\n\r\t" or ord(char) >= 32).replace("\r", "\n")


def complete_json(text):
    try:
        return json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    except (ValueError, RecursionError):
        raise ValueError("Mole did not return a complete JSON report. Open the Terminal view for details.") from None


class App:
    def __init__(self, home=None, runner=run_bounded):
        self.home = Path(home or Path.home()).resolve()
        self.token = secrets.token_urlsafe(32)
        self.runner = runner
        self.entries = {}
        self.plans = {}
        self.lock = threading.Lock()
        self.stopping = threading.Event()
        self.jobs = jobs.Registry(self.lock)
        self.selection_ttl = SELECTION_TTL
        self.executable = str(ROOT / "mole")
        self.terminal_dir = None
        self.terminal_files = []

    def executable_for(self, command):
        helper = ROOT / "bin" / (command + "-go")
        if command in {"analyze", "status"} and not (helper.is_file() and os.access(helper, os.X_OK)):
            return shutil.which("mo") or self.executable
        return self.executable

    def state(self):
        usage = shutil.disk_usage(self.home)
        version = re.search(r'^VERSION="([^"]+)"', (ROOT / "mole").read_text(), re.M)
        return {"catalog": CATALOG, "home": str(self.home), "version": version[1] if version else "dev",
                "system": platform.system(), "os": "macOS " + platform.mac_ver()[0],
                "host": platform.node().removesuffix(".local"), "architecture": platform.machine(),
                "disk": {"total": usage.total, "used": usage.used, "free": usage.free},
                "sampled_at": time.time(), "executable": self.executable,
                "locations": [str(self.home)] + [str(self.home / p) for p in sorted(PERSONAL)
                                               if (self.home / p).is_dir() and not (self.home / p).is_symlink()]}

    def browse_path(self, raw):
        if not isinstance(raw, str) or len(raw) > 4096 or any(ord(c) < 32 or ord(c) == 127 for c in raw):
            raise ValueError("Choose a valid folder inside your home directory.")
        if raw == "~" or raw.startswith("~/"):
            raw = str(self.home) + raw[1:]
        path = Path(raw)
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("Choose an absolute folder inside your home directory.")
        if not path.is_relative_to(self.home):
            raise ValueError("Browse a folder inside your home directory. Use the terminal analyzer for other volumes.")
        # Do not turn a symlink into an apparently ordinary browser selection.
        probe = self.home
        for part in path.relative_to(self.home).parts:
            probe = probe / part
            if probe.is_symlink():
                raise ValueError("Symbolic links cannot be browsed here. Use the terminal analyzer for this path.")
        if not path.is_dir():
            raise ValueError("Choose a folder inside your home directory.")
        if path.resolve(strict=True) != path:
            raise ValueError("The folder changed. Refresh the browser before continuing.")
        return path

    def eligible(self, path):
        try:
            relative = path.relative_to(self.home)
        except ValueError:
            return False
        if len(relative.parts) < 2 or relative.parts[0] not in PERSONAL:
            return False
        if any(p.startswith(".") or p.casefold().endswith(".app") or p.casefold() == "library"
               or any(ord(c) < 32 or ord(c) == 127 for c in p) for p in relative.parts):
            return False
        try:
            return (path.resolve(strict=True) == path and not path.is_symlink()
                    and (path.is_file() or path.is_dir()) and path.stat().st_uid == os.getuid())
        except (OSError, RuntimeError):
            return False

    def browse(self, raw, **options):
        return browser.browse(self, raw, **options)

    def child_env(self, readonly=False):
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        for key in tuple(env):
            if (key in {"BASH_ENV", "ENV", "MO_ANALYZE_PATH", "SUDO_USER", "SUDO_UID", "SUDO_GID", "SUDO_COMMAND"}
                    or key.startswith("BASH_FUNC_") or key.endswith("_LOADED")):
                env.pop(key)
        if readonly:
            env.update(MOLE_DRY_RUN="1", MOLE_TEST_NO_AUTH="1", NO_COLOR="1", TERM="dumb")
        return env

    def verify_entry(self, entry):
        path = entry["path"]
        try:
            matches = self.eligible(path) and identity(path) == entry["identity"]
        except OSError:
            matches = False
        if not matches:
            raise ValueError("The selected item changed or is protected. Refresh the folder and review it again.")

    def bridge(self, entry, preview, timeout=None):
        self.verify_entry(entry)
        dev, inode, mtime_ns, _size, parent_dev, parent_inode = entry["identity"]
        expected = f"{dev}:{inode}:{mtime_ns // 1_000_000_000}"
        env = self.child_env()
        env["MOLE_GUI_PYTHON"] = sys.executable
        # The fixed GUI attempt budget covers the project's 30s size/action
        # steps and 2s identity probes. CLI timeout overrides stay in Terminal.
        for key in ("MOLE_TIMEOUT_DISK_VERIFY_SEC", "MOLE_TIMEOUT_QUICK_DETECT_SEC", "MOLE_TIMEOUT_MEDIUM_PROBE_SEC"):
            env.pop(key, None)
        # The bridge sources its own safety policy, never a Bash startup file or
        # an inherited uninstall exemption. Preserve Mole's normal log settings.
        return self.runner(["/bin/bash", "--noprofile", "--norc", str(ROOT / "gui" / "trash.sh"),
                            "preview" if preview else "trash", str(entry["path"]), expected,
                            f"{parent_dev}:{parent_inode}"],
                           timeout=timeout or (PREVIEW_ATTEMPT_BUDGET if preview else TRASH_ATTEMPT_BUDGET), env=env)

    def active(self):
        if self.stopping.is_set():
            raise ValueError("The GUI is closing. No further items were submitted.")

    def plan(self, ids):
        self.active()
        if (not isinstance(ids, list) or not 1 <= len(ids) <= 5
                or any(not isinstance(i, str) or len(i) > 128 for i in ids) or len(set(ids)) != len(ids)):
            raise ValueError("Select between one and five items for each review.")
        now = time.monotonic()
        self.plans = {k: v for k, v in self.plans.items() if now - v["time"] < PLAN_TTL}
        chosen = []
        for key in ids:
            entry = self.entries.get(key)
            if not entry or now - entry["time"] >= SELECTION_TTL:
                raise ValueError("This selection expired. Refresh the folder and select the items again.")
            self.verify_entry(entry)
            chosen.append(entry)
        if any(a["path"].is_relative_to(b["path"]) for a in chosen for b in chosen if a is not b):
            raise ValueError("Select a folder or its contents, not both.")
        deadline = now + OPERATION_BUDGET
        for entry in chosen:
            self.active()
            remaining = deadline - time.monotonic()
            if remaining < PREVIEW_ATTEMPT_BUDGET:
                raise ValueError("Preview timed out. Review fewer items at once.")
            self.bridge(entry, True, PREVIEW_ATTEMPT_BUDGET)
        self.active()
        receipt = secrets.token_urlsafe(24)
        self.plans[receipt] = {"entries": chosen, "time": time.monotonic()}
        self.plans = dict(list(self.plans.items())[-20:])
        return {"receipt": receipt, "paths": [str(e["path"]) for e in chosen]}

    def trash(self, receipt):
        self.active()
        if not isinstance(receipt, str) or len(receipt) > 128:
            raise ValueError("Review the selection first.")
        plan = self.plans.pop(receipt, None)  # One use, even on failure.
        if not plan or time.monotonic() - plan["time"] >= PLAN_TTL:
            raise ValueError("The review expired. Review your selection again.")
        completed, unconfirmed, failure = [], [], None
        deadline = time.monotonic() + OPERATION_BUDGET
        for entry in plan["entries"]:
            dispatched = False
            try:
                self.active()
                remaining = deadline - time.monotonic()
                if remaining < TRASH_ATTEMPT_BUDGET:
                    raise ValueError("There was not enough time for another full Trash attempt. Remaining helpers were not started.")
                self.verify_entry(entry)
                dispatched = True
                output = self.bridge(entry, False, TRASH_ATTEMPT_BUDGET)
                if TRASH_ACK not in output.splitlines():
                    raise ValueError("Mole did not return a confirmed move receipt. Check the folder and Trash; source absence alone is unconfirmed.")
                if os.path.lexists(entry["path"]):
                    raise ValueError("The reviewed source path exists again. Check the folder and Trash; the current outcome is unconfirmed.")
                completed.append(str(entry["path"]))
            except (ValueError, OSError) as error:
                failure = str(error)
                if dispatched:
                    unconfirmed.append(str(entry["path"]))
                break  # Cancellation or refusal never advances to another target.
        remaining = [str(entry["path"]) for entry in plan["entries"] if str(entry["path"]) not in completed]
        return {"completed": completed, "error": failure, "remaining": remaining,
                "unconfirmed": unconfirmed,
                "not_attempted": [path for path in remaining if path not in unconfirmed]}

    def start_job(self, data):
        self.active()
        if not isinstance(data, dict) or not isinstance(data.get("kind"), str):
            raise ValueError("Choose a supported read-only operation.")
        kind = data["kind"]
        allowed = {"analyze": {"kind", "path"}, "report": {"kind", "report"},
                   "preview": {"kind", "command", "apps"}}
        if kind not in allowed or set(data) - allowed[kind]:
            raise ValueError("Unsupported read-only operation input.")
        request = dict(data)
        if kind == "analyze":
            request["path"] = str(self.browse_path(data.get("path", str(self.home))))
        elif kind == "report":
            if not isinstance(data.get("report"), str) or data["report"] not in {"status", "history", "apps"}:
                raise ValueError("Choose health, activity history, or installed apps.")
        else:
            if not isinstance(data.get("command"), str) or data["command"] not in {"clean", "uninstall"}:
                raise ValueError("Choose a cleanup or selected-app preview.")
            if data["command"] == "clean":
                if "apps" in data:
                    raise ValueError("Cleanup previews do not accept application arguments.")
                preview_reports.report_path(self.home)
            else:
                names = data.get("apps")
                if (not isinstance(names, list) or not 1 <= len(names) <= 50
                        or any(not isinstance(name, str) or not name or len(name) > 512
                               or name.startswith("-") or name != name.strip()
                               or any(ord(char) < 32 or ord(char) == 127 for char in name) for name in names)
                        or len(set(names)) != len(names)):
                    raise ValueError("Select exact installed app names for a read-only preview.")
                request["apps"] = list(names)
        return self.jobs.start(kind, lambda job: self.readonly_job(job, request), request)

    def readonly_job(self, job, request):
        self.active()
        job.check()
        # Only this instance's scratch directory is cleaned when a job ends.
        # Cancellation never asks Mole to clean the user's ordinary temp root.
        with tempfile.TemporaryDirectory(prefix="mole-gui-job-") as scratch:
            env = self.child_env(readonly=True)
            env.update(TMPDIR=scratch, MOLE_RESOLVED_TMPDIR=scratch, MOLE_TEMP_REGISTRY_FILE="")
            if request["kind"] == "report":
                job.set_stage("Reading " + request["report"])
                return self.report(request["report"], job=job, env=env)
            if request["kind"] == "analyze":
                job.set_stage("Measuring the selected folder")
                path = self.browse_path(request["path"])
                before = path.stat()
                output = self.runner([self.executable_for("analyze"), "analyze", "--json", str(path)],
                                     timeout=job.remaining(120), env=env, cancel=job.cancelled)
                job.check()
                after = self.browse_path(str(path)).stat()
                if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
                    raise ValueError("The measured folder changed. Start a fresh scan.")
                job.set_stage("Checking measurement coverage")
                return analysis_reports.normalized(complete_json(output), path, self.home)
            return self.preview_job(job, request, env)

    def preview_job(self, job, request, env):
        command = request["command"]
        before, started_ns = None, None
        args = [command, "--dry-run"]
        if command == "clean":
            report = preview_reports.report_path(self.home)
            before = preview_reports.fingerprint(report)
            started_ns = time.time_ns()
            job.set_stage("Previewing eligible cleanup targets")
        else:
            job.set_stage("Checking the selected installed apps")
            inventory = self.report("apps", job=job, env=env)
            if (not isinstance(inventory, list)
                    or any(not isinstance(entry, dict) or not isinstance(entry.get("name"), str)
                           or not isinstance(entry.get("path"), str)
                           or not isinstance(entry.get("uninstall_name"), str) for entry in inventory)):
                raise ValueError("Mole did not return a complete installed-app list.")
            # Resolve exact names from a fresh inventory. Pass display names to
            # the CLI's exact-match branch rather than allowing substring input.
            names = []
            for selected in request["apps"]:
                matches = [entry for entry in inventory if isinstance(entry, dict)
                           and selected in {entry.get("name"), entry.get("uninstall_name")}]
                if len(matches) != 1 or not isinstance(matches[0].get("name"), str):
                    raise ValueError("A selected app changed or is ambiguous. Refresh the installed-app list.")
                name = matches[0]["name"]
                if not name or name.startswith("-") or any(ord(char) < 32 for char in name):
                    raise ValueError("This installed-app name cannot be previewed safely.")
                exact = [entry for entry in inventory if name.casefold() in {
                    entry["name"].casefold(),
                    (Path(entry["path"]).name[:-4] if Path(entry["path"]).suffix.casefold() == ".app"
                     else Path(entry["path"]).name).casefold()}]
                if len(exact) != 1:
                    raise ValueError("A selected display name also matches another app's bundle name. Preview one app at a time in Terminal to review its matches.")
                names.append(name)
            if len(names) != len({name.casefold() for name in names}):
                raise ValueError("Two selected names refer to the same installed app. Select it once.")
            args.extend(names)
            env["MOLE_DELETE_MODE"] = "trash"
            job.set_stage("Previewing the selected app removals")
        kwargs = {"timeout": job.remaining(180), "env": env, "cancel": job.cancelled,
                  "on_output": job.activity.feed}
        if command == "uninstall":
            kwargs["input_data"] = b"y\n"
        output = self.runner([self.executable] + args, **kwargs)
        job.check()
        result = {"command": shlex.join(["mo"] + args), "output": readable_output(output),
                  "candidates": [], "limited": True, "sampled_at": time.time(),
                  "scope_note": "Read-only preview without administrator access. See the transcript for protection and scope details."}
        if command == "clean":
            job.set_stage("Checking the fresh preview report")
            fresh = preview_reports.fresh_report(self.home, before, started_ns)
            job.check()
            if fresh is not None:
                result.update(fresh)
                result["scope_note"] += " Rows come from a fresh, complete shared Mole preview report and never authorize deletion."
            else:
                result["scope_note"] += " No fresh complete file list was available; the transcript is the result."
        else:
            result["scope_note"] += " Mole reports this app preview as text; no structured file-removal plan is inferred."
        return result

    def file_action(self, data):
        self.active()
        if not isinstance(data, dict) or not isinstance(data.get("action"), str):
            raise ValueError("Choose a file action.")
        action = data["action"]
        if action not in {"reveal", "preview", "trash"}:
            raise ValueError("Choose Reveal, Preview, or Open Trash.")
        if set(data) != ({"action"} if action == "trash" else {"action", "id"}):
            raise ValueError("Choose a discovered item for this action.")
        if action == "trash":
            path = self.home / ".Trash"
            if path.is_symlink() or not path.is_dir() or path.resolve(strict=True) != path:
                raise ValueError("The local Trash folder is unavailable. Open Trash in Finder.")
            argv = ["/usr/bin/open", "-b", "com.apple.finder", str(path)]
        else:
            key = data.get("id")
            if not isinstance(key, str) or len(key) > 128:
                raise ValueError("Choose a discovered item.")
            entry = self.entries.get(key)
            if entry is None or time.monotonic() - entry["time"] >= SELECTION_TTL:
                raise ValueError("The selection expired. Refresh the folder.")
            path = entry["path"]
            self.browse_path(str(path.parent))
            if path.is_symlink() or identity(path) != entry["identity"]:
                raise ValueError("The selected item changed. Refresh the folder.")
            if action == "preview":
                if not path.is_file() or path.suffix.casefold() not in browser.PREVIEW_EXTENSIONS:
                    raise ValueError("Preview supports regular image and PDF files only.")
                argv = ["/usr/bin/open", "-b", "com.apple.Preview", str(path)]
            else:
                argv = ["/usr/bin/open", "-R", str(path)]
        if platform.system() != "Darwin":
            raise ValueError("Finder and Preview actions require macOS.")
        if os.environ.get("MOLE_TEST_NO_AUTH") == "1" or os.environ.get("MOLE_TEST_MODE") == "1":
            raise ValueError("Native file actions are disabled in test mode.")
        self.runner(argv, timeout=5, owned=False)
        return {"opened": True, "action": action, "path": str(path)}

    def report(self, kind, job=None, env=None):
        self.active()
        if not isinstance(kind, str):
            raise ValueError("Choose a report.")
        args = {"status": ["status", "--json"], "history": ["history", "--json", "--limit", "200" if job else "20"],
                "apps": ["uninstall", "--list"]}.get(kind)
        if not args:
            raise ValueError("Unknown report.")
        kwargs = {"timeout": job.remaining(40) if job else 40, "env": env or self.child_env(readonly=True)}
        if job:
            kwargs["cancel"] = job.cancelled
        text = self.runner([self.executable_for(args[0])] + args, **kwargs)
        if job:
            job.check()
        result = complete_json(text)
        if job and not isinstance(result, list if kind == "apps" else dict):
            raise ValueError("Mole did not return the requested report type.")
        if job and kind == "history" and isinstance(result, dict):
            result = dict(result, limit=200)
        return result

    def launch(self, data):
        self.active()
        args = command_args(data)
        if platform.system() != "Darwin":
            raise ValueError("Opening Terminal requires macOS. Copy the command instead.")
        if os.environ.get("MOLE_TEST_NO_AUTH") == "1" or os.environ.get("MOLE_TEST_MODE") == "1":
            raise ValueError("Terminal launches are disabled in test mode.")
        if self.terminal_dir is None:
            self.terminal_dir = Path(tempfile.mkdtemp(prefix="mole-gui-"))
        if len(self.terminal_files) >= 100:
            raise ValueError("Session launch limit reached. Restart the GUI.")
        path = self.terminal_dir / (secrets.token_hex(12) + ".command")
        executable = self.executable_for(args[0])
        mode = ('export MOLE_DELETE_MODE=' + ("permanent" if "--permanent" in args else "trash") + "\n") if args[0] == "uninstall" else ""
        content = "#!/bin/bash\n" + mode + shlex.join([executable] + args) + '\nresult=$?\nprintf "\\nMole exited with status %s. You may close this window.\\n" "$result"\nexit "$result"\n'
        with path.open("x") as script:
            script.write(content)
        path.chmod(0o700)
        self.terminal_files.append(path)
        self.runner(["/usr/bin/open", "-a", "Terminal", str(path)], timeout=5, owned=False)
        return {"launched": True, "command": shlex.join([executable] + args)}

    def close(self):
        self.stopping.set()
        self.jobs.close()
        # Only exact scratch files created by this instance; no recursive removal.
        for path in self.terminal_files:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        if self.terminal_dir:
            try:
                self.terminal_dir.rmdir()
            except OSError:
                pass


class Handler(BaseHTTPRequestHandler):
    server_version = "MoleGUI"

    def log_message(self, *_args):
        pass  # Do not log local paths or capability tokens.

    def respond(self, status, value, content_type="application/json"):
        data = json.dumps(value).encode() if content_type == "application/json" else value
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        # Accept origin-form targets only; an absolute URL must not bypass the
        # /api/ token check while still dispatching to a parsed API path.
        try:
            parsed = urlsplit(self.path)
        except ValueError:
            self.respond(400, {"error": "Invalid request path."})
            return False
        if (not self.path.startswith("/") or self.path.startswith("//")
                or parsed.scheme or parsed.netloc or parsed.fragment):
            self.respond(400, {"error": "Use the local browser URL."})
            return False
        host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get_all("Host", []) != [host]:
            self.respond(403, {"error": "Open the local URL printed by the GUI launcher."})
            return False
        origins = self.headers.get_all("Origin", [])
        if origins and origins != ["http://" + host]:
            self.respond(403, {"error": "Cross-origin access is not allowed."})
            return False
        if parsed.path.startswith("/api/"):
            tokens = self.headers.get_all("X-Mole-Token", [])
            if len(tokens) != 1 or not hmac.compare_digest(
                    tokens[0].encode("utf-8"), self.server.app.token.encode("ascii")):
                self.respond(401, {"error": "Session expired. Reopen the full URL printed by the launcher."})
                return False
        if self.server.app.stopping.is_set():
            self.respond(503, {"error": "The GUI is closing."})
            return False
        return True

    def do_GET(self):
        if not self.authorized():
            return
        parsed = urlsplit(self.path)
        try:
            if parsed.path == "/api/state":
                self.respond(200, self.server.app.state())
            elif parsed.path == "/api/jobs":
                self.respond(200, self.server.app.jobs.active_snapshot())
            elif match := re.fullmatch(r"/api/jobs/([A-Za-z0-9_-]{1,128})", parsed.path):
                self.respond(200, self.server.app.jobs.snapshot(match[1]))
            elif parsed.path == "/api/browse":
                query = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=8)
                options = browser.options(query)
                app = self.server.app
                if not app.lock.acquire(blocking=False):
                    self.respond(409, {"error": "An operation is already running. Let it finish before browsing."})
                    return
                try:
                    self.respond(200, app.browse(query.get("path", [str(app.home)])[0], **options))
                finally:
                    app.lock.release()
            elif parsed.path in {"/", "/index.html", "/app.js", "/styles.css", "/favicon.svg"}:
                name = parsed.path.lstrip("/") or "index.html"
                types = {"html": "text/html; charset=utf-8", "js": "text/javascript; charset=utf-8",
                         "css": "text/css; charset=utf-8", "svg": "image/svg+xml"}
                self.respond(200, (WEB / name).read_bytes(), types[name.rsplit(".", 1)[-1]])
            else:
                self.respond(404, {"error": "Not found."})
        except jobs.MissingJob as error:
            self.respond(404, {"error": str(error)})
        except (ValueError, OSError) as error:
            self.respond(400, {"error": str(error)})

    def do_POST(self):
        if not self.authorized():
            return
        content_types = self.headers.get_all("Content-Type", [])
        if (len(content_types) != 1
                or content_types[0].split(";", 1)[0].strip().lower() != "application/json"):
            self.respond(415, {"error": "JSON required."})
            return
        try:
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or self.headers.get("Transfer-Encoding") is not None:
                raise ValueError("Send one bounded JSON request body.")
            if not re.fullmatch(r"[0-9]+", lengths[0]):
                raise ValueError("Invalid request size.")
            length = int(lengths[0])
            if not 0 < length <= 16384:
                raise ValueError("Invalid request size.")
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError("Incomplete request body.")
            data = json.loads(body.decode("utf-8"), object_pairs_hook=unique_object,
                              parse_constant=invalid_constant)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object.")
            app = self.server.app
            if self.path == "/api/jobs":
                self.respond(200, app.start_job(data))
                return
            if match := re.fullmatch(r"/api/jobs/([A-Za-z0-9_-]{1,128})/cancel", self.path):
                if data:
                    raise ValueError("Cancellation does not accept options.")
                self.respond(200, app.jobs.cancel(match[1]))
                return
            if self.path == "/api/command":
                self.respond(200, {"command": shlex.join(["mo"] + command_args(data))})
                return
            if not app.lock.acquire(blocking=False):
                self.respond(409, {"error": "An operation is already running. Let it finish before starting another."})
                return
            try:
                expected = {"/api/launch": {"command", "flags", "fields"},
                            "/api/plan": {"ids"}, "/api/trash": {"receipt"},
                            "/api/report": {"kind"}, "/api/file-action": {"action", "id"}}
                if self.path in expected and set(data) - expected[self.path]:
                    raise ValueError("Unsupported request input.")
                if self.path == "/api/launch":
                    result = app.launch(data)
                elif self.path == "/api/plan":
                    result = app.plan(data.get("ids"))
                elif self.path == "/api/trash":
                    result = app.trash(data.get("receipt"))
                elif self.path == "/api/report":
                    if not isinstance(data.get("kind"), str):
                        raise ValueError("Choose a report.")
                    result = app.report(data["kind"])
                elif self.path == "/api/file-action":
                    result = app.file_action(data)
                else:
                    self.respond(404, {"error": "Not found."})
                    return
                self.respond(200, result)
            finally:
                app.lock.release()
        except jobs.Busy as error:
            self.respond(409, {"error": str(error)})
        except jobs.MissingJob as error:
            self.respond(404, {"error": str(error)})
        except (ValueError, OSError, RecursionError) as error:
            self.respond(400, {"error": str(error)})

    def setup(self):
        super().setup()
        self.connection.settimeout(10)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field.")
        result[key] = value
    return result


def invalid_constant(_value):
    raise ValueError("Invalid JSON number.")


class LocalServer(ThreadingHTTPServer):
    # Ctrl+C waits for a bounded in-flight request. Daemon request threads
    # would otherwise leave an independently launched Trash child running.
    daemon_threads = False
    block_on_close = True

    def __init__(self, app):
        super().__init__(("127.0.0.1", 0), Handler)
        self.app = app

    def server_close(self):
        self.app.stopping.set()
        self.app.jobs.close()
        super().server_close()


def main():
    parser = argparse.ArgumentParser(description="Open Mole’s local web interface.")
    parser.add_argument("--no-open", action="store_true", help="Print the URL without opening a browser")
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error("Run as your regular user, without sudo.")
    app = App()
    server = LocalServer(app)
    url = f"http://127.0.0.1:{server.server_port}/#token={app.token}"
    closing = False
    previous = {}

    def request_shutdown(signum, _frame):
        nonlocal closing
        if closing:
            return
        closing = True
        app.stopping.set()
        raise ShutdownRequested(signum)

    for signum in (signal.SIGINT, signal.SIGHUP, signal.SIGTERM):
        previous[signum] = signal.signal(signum, request_shutdown)
    try:
        print(f"Mole GUI: {url}\nPress Ctrl+C to stop.", flush=True)
        if not args.no_open:
            webbrowser.open(url)
        server.serve_forever()
    except (KeyboardInterrupt, ShutdownRequested):
        # A closed Terminal may no longer accept output. It must not prevent
        # the cleanup below, or allow repeated signals to interrupt cleanup.
        closing = True
        app.stopping.set()
        try:
            print("\nClosing Mole GUI; waiting for the current bounded operation.", flush=True)
        except OSError:
            pass
    finally:
        closing = True
        app.stopping.set()
        try:
            # Do not call HTTPServer.shutdown from its serving thread: that
            # waits on itself. Closing waits for bounded request threads and
            # cancels/joins read-only jobs; a started Trash attempt may finish.
            server.server_close()
        finally:
            app.close()
            for signum, handler in previous.items():
                signal.signal(signum, handler)


if __name__ == "__main__":
    main()
