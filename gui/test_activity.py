"""Live preview activity uses reported text only and never authorizes cleanup."""
import json
from pathlib import Path
import sys
import threading
import time
import unittest

from gui import activity, jobs, server
from gui.test_server import Fixture


class TailTests(unittest.TestCase):
    def test_utf8_and_ansi_osc_sequences_split_across_every_byte(self):
        tail = activity.Tail()
        data = ("Visible \x1b[32mcafé\x1b[0m\n"
                "\x1b]0;private window title\x1b\\Ready \x1b]8;;https://example.invalid\x07link"
                "\x1b]8;;\x1b\\").encode()
        for byte in data:
            tail.feed(bytes([byte]))
        tail.finish()
        self.assertEqual(tail.snapshot(), {"lines": ["Visible café", "Ready link"],
                                          "total_lines": 2, "truncated": False})

    def test_partial_line_is_readable_without_newline_or_utf8_replacement(self):
        tail = activity.Tail()
        tail.feed(b"Scanning caf\xc3")
        self.assertEqual(tail.snapshot()["lines"], ["Scanning caf"])
        tail.feed(b"\xa9")
        self.assertEqual(tail.snapshot()["lines"], ["Scanning café"])
        tail.finish()
        self.assertEqual(tail.snapshot()["total_lines"], 1)

    def test_cr_progress_replaces_current_line_and_crlf_commits_once(self):
        tail = activity.Tail()
        tail.feed(b"First\rSecond\rThird")
        self.assertEqual(tail.snapshot()["lines"], ["Third"])
        self.assertEqual(tail.snapshot()["total_lines"], 1)
        tail.feed(b"\r\nNext\n\n")
        self.assertEqual(tail.snapshot()["lines"], ["Third", "Next", ""])
        self.assertEqual(tail.snapshot()["total_lines"], 3)

    def test_line_count_long_lines_and_serialized_payload_are_bounded(self):
        tail = activity.Tail()
        tail.feed(("x" * 10000 + "\n").encode())
        self.assertEqual(tail.snapshot()["lines"], ["x" * activity.MAX_LINE_CHARS])
        self.assertTrue(tail.snapshot()["truncated"])
        for _ in range(200):
            tail.feed(("🙂" * 1000 + "\n").encode())
        result = tail.snapshot()
        self.assertLessEqual(len(result["lines"]), activity.MAX_LINES)
        self.assertLessEqual(len(json.dumps(result["lines"])), activity.MAX_TEXT_PAYLOAD)
        self.assertEqual(result["total_lines"], 201)
        self.assertTrue(result["truncated"])

    def test_latest_partial_line_is_retained_at_line_limit(self):
        tail = activity.Tail()
        for index in range(150):
            tail.feed(f"Reported {index}\n".encode())
        tail.feed(b"Current reported text")
        result = tail.snapshot()
        self.assertEqual(len(result["lines"]), 120)
        self.assertEqual(result["lines"][-1], "Current reported text")
        self.assertEqual(result["total_lines"], 151)
        self.assertTrue(result["truncated"])

    def test_long_unfinished_osc_has_no_stored_payload_or_false_lines(self):
        tail = activity.Tail()
        tail.feed(b"Visible\x1b]" + b"x" * 1000000 + b"\n")
        self.assertEqual(tail.snapshot()["lines"], ["Visible"])
        self.assertEqual(tail.snapshot()["total_lines"], 1)
        tail.feed(b"\x1b\\ continued")
        self.assertEqual(tail.snapshot()["lines"], ["Visible continued"])


class LiveTests(Fixture):
    def await_activity(self, key, text):
        deadline = time.monotonic() + 3
        value = None
        while time.monotonic() < deadline:
            value = self.app.jobs.snapshot(key)
            if any(text in line for line in value["activity"]["lines"]):
                return value
            time.sleep(0.01)
        self.fail(f"Activity was not published while running: {value}")

    def fixed_subprocess(self, code):
        def runner(argv, **kwargs):
            self.calls.append((argv, kwargs))
            return server.run_bounded([sys.executable, "-u", "-c", code], **kwargs)
        self.app.runner = runner

    def wait(self, key):
        self.app.jobs.jobs[key].thread.join(timeout=4)
        value = self.app.jobs.snapshot(key)
        self.assertNotEqual(value["status"], "running")
        return value

    def test_partial_first_output_is_live_before_exit_and_recovered_verbatim(self):
        release, finished = self.home / "release", self.home / "finished"
        code = ("import pathlib,sys,time; sys.stdout.buffer.write(b'\\x1b[32mScanning caf\\xc3'); "
                "sys.stdout.flush(); release=pathlib.Path(" + repr(str(release)) + "); "
                "\nwhile not release.exists(): time.sleep(.01)\n"
                "sys.stdout.buffer.write(b'\\xa9\\x1b[0m\\n'); sys.stdout.flush(); "
                "sys.stderr.write('Reported discovery group\\n'); sys.stderr.flush(); "
                "pathlib.Path(" + repr(str(finished)) + ").touch()")
        self.fixed_subprocess(code)
        key = self.app.start_job({"kind": "preview", "command": "clean"})["id"]
        try:
            value = self.await_activity(key, "Scanning caf")
            self.assertEqual(value["status"], "running")
            self.assertFalse(finished.exists())
            self.assertEqual(value["activity"]["lines"], ["Scanning caf"])
            self.assertEqual(self.app.jobs.active_snapshot()["active"]["activity"], value["activity"])
            self.assertEqual(self.app.plans, {})
            env = self.calls[0][1]["env"]
            self.assertEqual(env["MOLE_DRY_RUN"], "1")
            self.assertEqual(env["MOLE_TEST_NO_AUTH"], "1")
            release.touch()
            result = self.wait(key)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["activity"]["lines"], ["Scanning café", "Reported discovery group"])
            self.assertEqual(result["result"]["candidates"], [])
        finally:
            release.touch()
            self.app.jobs.cancel(key)
            self.app.jobs.jobs[key].thread.join(timeout=4)

    def test_cancelled_preview_retains_reported_partial_tail_and_no_result(self):
        code = "import sys,time; sys.stdout.write('Inspecting reported target'); sys.stdout.flush(); time.sleep(30)"
        self.fixed_subprocess(code)
        key = self.app.start_job({"kind": "preview", "command": "clean"})["id"]
        value = self.await_activity(key, "Inspecting reported target")
        self.app.jobs.cancel(key)
        result = self.wait(key)
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(result["activity"], value["activity"])
        self.assertIsNone(result["result"])

    def test_failed_preview_retains_stdout_and_stderr_activity(self):
        code = "import sys; print('Reported discovery',flush=True); sys.stderr.write('Reported refusal\\n'); sys.exit(3)"
        self.fixed_subprocess(code)
        key = self.app.start_job({"kind": "preview", "command": "clean"})["id"]
        result = self.wait(key)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["activity"]["lines"], ["Reported discovery", "Reported refusal"])
        self.assertIsNone(result["result"])
        self.assertEqual(self.app.plans, {})

    def test_output_limit_still_stops_worker_with_bounded_activity_retained(self):
        code = "import sys; print('Reported before limit',flush=True); sys.stdout.write('x'*2200000); sys.stdout.flush()"
        self.fixed_subprocess(code)
        key = self.app.start_job({"kind": "preview", "command": "clean"})["id"]
        result = self.wait(key)
        self.assertEqual(result["status"], "failed")
        self.assertIn("too large", result["error"])
        self.assertTrue(result["activity"]["truncated"])
        self.assertEqual(result["activity"]["lines"][0], "Reported before limit")
        self.assertLessEqual(len(json.dumps(result["activity"]["lines"])), activity.MAX_TEXT_PAYLOAD)

    def test_report_and_analyze_never_attach_stream_callbacks_or_activity(self):
        from gui.test_jobs import measured
        for data, output in [
                ({"kind": "report", "report": "status"}, '{"health_score":80}'),
                ({"kind": "analyze", "path": str(self.downloads)}, json.dumps(measured(self.downloads)))]:
            calls = []
            self.app.runner = lambda argv, value=output, **kwargs: calls.append(kwargs) or value
            key = self.app.start_job(data)["id"]
            result = self.wait(key)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["activity"], {"lines": [], "total_lines": 0, "truncated": False})
            self.assertNotIn("on_output", calls[0])


if __name__ == "__main__":
    unittest.main()
