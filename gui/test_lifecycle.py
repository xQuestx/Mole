"""Signal lifecycle and native receipt evidence, confined to a temporary HOME."""
import http.client
import json
import os
from pathlib import Path
import platform
import re
import selectors
import signal
import subprocess
import sys
import threading
import time
import unittest
from urllib.parse import urlencode, urlsplit, parse_qs

from gui import attempt_log, server
from gui.test_server import Fixture


class ReceiptTests(Fixture):
    def test_absence_or_stale_and_other_path_log_rows_do_not_confirm_a_move(self):
        log = self.home / "deletions.log"
        target = self.file()
        log.write_text(f"old\ttrash\t1\tok\t{target}\n")
        before = attempt_log.capture(log)
        with self.assertRaises(ValueError):
            attempt_log.confirmed(log, before, str(target))
        with log.open("a") as output:
            output.write(f"fresh\ttrash\t1\tok\t{self.home / 'different'}\n")
        with self.assertRaises(ValueError):
            attempt_log.confirmed(log, before, str(target))
        with log.open("a") as output:
            output.write(f"fresh\ttrash\t1\tok\t{target}\n")
        attempt_log.confirmed(log, before, str(target))

    def test_pending_record_must_actually_exist_before_it_can_be_persisted(self):
        log = self.home / "operations.log"
        target = self.file()
        log.write_text("unrelated log row\n")
        with self.assertRaises(ValueError):
            attempt_log.persist_pending(log, str(target), "unique-attempt")
        with log.open("a") as output:
            output.write(f"[fixture time] [analyze] TRASH_ATTEMPT {target} (GUI unique-attempt; outcome pending)\n")
        attempt_log.persist_pending(log, str(target), "unique-attempt")


BOOTSTRAP = r'''
import json, os, pathlib, subprocess, sys, tempfile, time
from gui import server
home = pathlib.Path(os.environ["GUI_SIGNAL_HOME"])
base = server.App

def fixture_runner(argv, **kwargs):
    if len(argv) > 4 and argv[4] == "trash":
        code = "import json,os,pathlib,sys,time; pathlib.Path(sys.argv[1]).touch(); time.sleep(.5); args=json.loads(sys.argv[2]); os.execv(args[0],args)"
        return server.run_bounded([sys.executable, "-c", code, str(home / "trash-started"), json.dumps(argv)], **kwargs)
    if len(argv) > 1 and argv[1] == "status":
        child = "import pathlib,time; time.sleep(1.5); pathlib.Path(" + repr(str(home / "leaked-child")) + ").touch()"
        code = ("import json,os,pathlib,subprocess,sys,time; child=subprocess.Popen([sys.executable,'-c',"
                + repr(child) + "],preexec_fn=os.setpgrp); pathlib.Path("
                + repr(str(home / "child-pids")) + ").write_text(json.dumps([os.getpid(),child.pid])); time.sleep(30)")
        return server.run_bounded([sys.executable, "-c", code], **kwargs)
    return server.run_bounded(argv, **kwargs)

class SignalFixture(base):
    def __init__(self):
        super().__init__(home=home, runner=fixture_runner)
        self.terminal_dir = pathlib.Path(tempfile.mkdtemp(prefix="signal-owned-", dir=home))
        command = self.terminal_dir / "fixture.command"
        command.write_text("synthetic scratch command\n")
        self.terminal_files.append(command)
        (home / "scratch-path").write_text(str(self.terminal_dir))
    def close(self):
        super().close()
        (home / "closed").touch()

server.App = SignalFixture
sys.argv = ["server.py", "--no-open"]
server.main()
'''


@unittest.skipIf(os.geteuid() == 0, "The local server rejects root before startup.")
class SignalTests(Fixture):
    def start_server(self):
        tmpdir = self.home / "Tmp"
        tmpdir.mkdir(exist_ok=True)
        env = dict(os.environ, GUI_SIGNAL_HOME=str(self.home), HOME=str(self.home),
                   TMPDIR=str(tmpdir), MOLE_RESOLVED_TMPDIR=str(tmpdir), MOLE_TEMP_REGISTRY_FILE="",
                   MOLE_TEST_NO_AUTH="1", MOLE_TEST_MODE="0", NO_COLOR="1", MO_NO_OPLOG="0",
                   MOLE_DELETE_LOG=str(self.home / "Library/Logs/mole/deletions.log"),
                   MOLE_TEST_TRASH_DIR=str(self.home / "FixtureTrash"))
        process = subprocess.Popen([sys.executable, "-u", "-c", BOOTSTRAP],
                                   cwd=server.ROOT, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        self.addCleanup(self.stop_process, process)
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            self.assertTrue(selector.select(4), "Fixture server did not print its startup URL")
            line = process.stdout.readline().decode()
        match = re.search(r"http://127\.0\.0\.1:\d+/#token=[A-Za-z0-9_-]+", line)
        self.assertIsNotNone(match, line)
        url = urlsplit(match[0])
        self.port = url.port
        self.token = parse_qs(url.fragment)["token"][0]
        return process

    def stop_process(self, process):
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        process.stdout.close()
        process.stderr.close()

    def request(self, method, path, data=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=6)
        host = f"127.0.0.1:{self.port}"
        headers = {"Host": host, "Origin": "http://" + host, "X-Mole-Token": self.token}
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def await_path(self, path):
        deadline = time.monotonic() + 4
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(path.exists())

    def check_shutdown(self, signum):
        process = self.start_server()
        status, _ = self.request("POST", "/api/jobs", {"kind": "report", "report": "status"})
        self.assertEqual(status, 200)
        self.await_path(self.home / "child-pids")
        process.send_signal(signum)
        process.wait(timeout=6)
        self.assertEqual(process.returncode, 0, process.stderr.read().decode())
        self.assertTrue((self.home / "closed").exists())
        self.assertFalse(Path((self.home / "scratch-path").read_text()).exists())
        self.assertEqual(list((self.home / "Tmp").iterdir()), [])
        time.sleep(1.7)
        self.assertFalse((self.home / "leaked-child").exists())
        for pid in json.loads((self.home / "child-pids").read_text()):
            result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "stat="],
                                    capture_output=True, text=True, timeout=2)
            self.assertTrue(not result.stdout.strip() or result.stdout.strip().startswith("Z"),
                            f"Fixture child {pid} remained running: {result.stdout}")

    def test_sighup_cancels_children_joins_jobs_and_removes_owned_scratch(self):
        self.check_shutdown(signal.SIGHUP)

    def test_sigterm_cancels_children_joins_jobs_and_removes_owned_scratch(self):
        self.check_shutdown(signal.SIGTERM)

    @unittest.skipUnless(platform.system() == "Darwin", "The real Trash bridge requires BSD stat.")
    def test_repeated_shutdown_signals_finish_current_trash_and_stop_later_item(self):
        first, second = self.file("First"), self.file("Second")
        process = self.start_server()
        status, view = self.request("GET", "/api/browse?" + urlencode({"path": str(self.downloads)}))
        self.assertEqual(status, 200)
        keys = {entry["name"]: entry["id"] for entry in view["entries"]}
        status, plan = self.request("POST", "/api/plan", {"ids": [keys[first.name], keys[second.name]]})
        self.assertEqual(status, 200)
        responses = []
        worker = threading.Thread(target=lambda: responses.append(
            self.request("POST", "/api/trash", {"receipt": plan["receipt"]})))
        worker.start()
        try:
            self.await_path(self.home / "trash-started")
            process.send_signal(signal.SIGHUP)
            time.sleep(0.05)
            process.send_signal(signal.SIGTERM)
            process.send_signal(signal.SIGHUP)
            process.wait(timeout=6)
            worker.join(timeout=3)
            self.assertEqual(process.returncode, 0, process.stderr.read().decode())
            self.assertEqual(responses[0][0], 200)
            self.assertEqual(responses[0][1]["completed"], [str(first)])
            self.assertEqual(responses[0][1]["not_attempted"], [str(second)])
            self.assertEqual(responses[0][1]["unconfirmed"], [])
            self.assertFalse(first.exists())
            self.assertTrue(second.exists())
            self.assertFalse(Path((self.home / "scratch-path").read_text()).exists())
            log = self.home / "Library/Logs/mole/operations.log"
            self.assertIn("TRASH_ATTEMPT", log.read_text())
            self.assertIn("TRASHED", log.read_text())
        finally:
            worker.join(timeout=6)


if __name__ == "__main__":
    unittest.main()
