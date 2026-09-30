"""Local GUI safety tests. Every filesystem mutation is confined to a temp HOME."""
import contextlib
import http.client
import io
import json
import os
from pathlib import Path
import platform
import shlex
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

from gui import server


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mole-gui-test-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.downloads = self.home / "Downloads"
        self.downloads.mkdir()
        self.calls = []
        self.app = server.App(home=self.home, runner=self.runner)
        self.addCleanup(self.app.close)

    def runner(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if len(argv) < 8 or argv[4] not in {"preview", "trash"}:
            raise AssertionError(f"Unexpected subprocess: {argv}")
        if argv[4] == "trash":
            trash = self.home / "FixtureTrash"
            trash.mkdir(exist_ok=True)
            Path(argv[5]).rename(trash / Path(argv[5]).name)
            return server.TRASH_ACK + "\n"
        return ""

    def file(self, name="fixture.txt", content="synthetic data"):
        path = self.downloads / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def row(self, path):
        return next(row for row in self.app.browse(str(path.parent))["entries"]
                    if row["path"] == str(path))


class CommandTests(unittest.TestCase):
    def test_catalog_commands_and_options_are_allowlisted(self):
        for command in server.CATALOG:
            with self.subTest(command=command["id"]):
                flags = [spec[0] for spec in command["flags"]]
                self.assertEqual(server.command_args({"command": command["id"], "flags": flags}),
                                 [command["id"]] + ["--" + flag for flag in flags])

    def test_malformed_commands_and_flags_refuse(self):
        inputs = [None, [], 1, {"command": []}, {"command": {}}, {"command": "unknown"},
                  {"command": "clean", "flags": None},
                  {"command": "clean", "flags": [[]]},
                  {"command": "clean", "flags": ["dry-run", "dry-run"]},
                  {"command": "clean", "flags": ["permanent"]},
                  {"command": "clean", "fields": []},
                  {"command": "clean", "fields": {"shell": "bash"}},
                  {"command": "clean", "executable": "/bin/sh"}]
        for data in inputs:
            with self.subTest(data=data), self.assertRaises(ValueError):
                server.command_args(data)

    def test_fields_refuse_option_injection_and_invalid_ranges(self):
        inputs = [("uninstall", {"apps": "--permanent"}),
                  ("analyze", {"path": "relative/path"}),
                  ("clean", {"external": "/Volumes/Bad\nname"}),
                  ("history", {"limit": "1.5"}), ("history", {"limit": "201"}),
                  ("history", {"limit": "NaN"}), ("history", {"limit": 20}),
                  ("status", {"interval": "2s"}), ("status", {"proc-cpu-window": "0s"}),
                  ("status", {"proc-cpu-window": "1s; touch anything"}),
                  ("touchid", {"action": "status; whoami"}),
                  ("completion", {"shell": "pwsh"})]
        for command, fields in inputs:
            with self.subTest(command=command, fields=fields), self.assertRaises(ValueError):
                server.command_args({"command": command, "fields": fields})
        self.assertEqual(server.command_args(
            {"command": "status", "flags": ["watch"], "fields": {"interval": "2s"}}),
            ["status", "--watch", "--interval", "2s"])
        self.assertEqual(server.command_args(
            {"command": "status", "fields": {"proc-cpu-alerts": "false"}}),
            ["status", "--proc-cpu-alerts=false"])

    def test_help_takes_precedence_over_editable_managers(self):
        for command, flags in [("clean", ["whitelist", "help"]),
                               ("optimize", ["dry-run", "whitelist", "help"]),
                               ("purge", ["paths", "yes", "help"])]:
            with self.subTest(command=command):
                self.assertEqual(server.command_args({"command": command, "flags": flags}),
                                 [command, "--help"])


class SelectionTests(Fixture):
    def test_browser_measures_file_sizes_and_leaves_folder_size_unknown(self):
        file = self.file(content="abc")
        directory = self.downloads / "Folder"
        directory.mkdir()
        (directory / "nested.txt").write_text("nested data")
        rows = {row["name"]: row for row in self.app.browse(str(self.downloads))["entries"]}
        self.assertEqual(rows[file.name]["size"], 3)
        self.assertIsNone(rows[directory.name]["size"])
        self.assertTrue(rows[file.name]["eligible"])
        self.assertFalse(self.row(self.downloads)["eligible"])
        self.assertEqual(self.calls, [])

    def test_browser_refuses_traversal_outside_home_and_symlink_navigation(self):
        inside = self.downloads / "Inside"
        inside.mkdir()
        alias = self.downloads / "Alias"
        alias.symlink_to(inside)
        outside = self.home / "OutsideAlias"
        outside.symlink_to(self.home.parent)
        for path in [str(alias), str(alias / "missing"), str(outside),
                     str(self.downloads) + "/../Downloads", str(self.home.parent),
                     "relative", "\x00", None, []]:
            with self.subTest(path=path), self.assertRaises((ValueError, OSError)):
                self.app.browse(path)
        row = self.row(alias)
        self.assertTrue(row["symlink"])
        self.assertFalse(row["directory"])
        self.assertFalse(row["eligible"])
        self.assertEqual(self.calls, [])

    def test_personal_roots_hidden_paths_apps_and_library_are_kept(self):
        for index, name in enumerate(["Regular.app", "UPPER.APP", "Library", "library"]):
            target = self.downloads / f"Case{index}" / name
            target.mkdir(parents=True)
            child = target / "child.txt"
            child.write_text("kept")
            self.assertFalse(self.row(target)["eligible"])
            self.assertFalse(self.row(child)["eligible"])
        hidden = self.file(".state/secret")
        self.assertFalse(self.app.eligible(hidden))
        self.file(".hidden")
        names = [row["name"] for row in self.app.browse(str(self.downloads))["entries"]]
        self.assertNotIn(".hidden", names)
        self.assertNotIn(".state", names)
        projects = self.home / "Projects"
        projects.mkdir()
        other = projects / "source.txt"
        other.write_text("kept")
        self.assertFalse(self.row(other)["eligible"])

    def test_review_uses_opaque_discovery_ids_and_rejects_overlap(self):
        file = self.file("Folder/child.txt")
        folder = file.parent
        child_row, folder_row = self.row(file), self.row(folder)
        for ids in [str(file), [str(file)], [], [child_row["id"]] * 2, [None],
                    [folder_row["id"], child_row["id"]], [child_row["id"]] * 6]:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.app.plan(ids)
        self.assertEqual(self.calls, [])

    def test_expired_selection_receipt_cannot_preview(self):
        row = self.row(self.file())
        self.app.entries[row["id"]]["time"] = time.monotonic() - server.SELECTION_TTL
        with self.assertRaisesRegex(ValueError, "selection expired"):
            self.app.plan([row["id"]])
        self.assertEqual(self.calls, [])

    def test_preview_is_read_only_and_confirmed_receipt_is_one_use(self):
        file = self.file()
        row = self.row(file)
        plan = self.app.plan([row["id"]])
        self.assertTrue(file.exists())
        self.assertEqual(self.calls[0][0][4], "preview")
        self.assertEqual(self.calls[0][0][-1],
                         f"{file.parent.stat().st_dev}:{file.parent.stat().st_ino}")
        result = self.app.trash(plan["receipt"])
        self.assertEqual(result, {"completed": [str(file)], "error": None, "remaining": [],
                                  "unconfirmed": [], "not_attempted": []})
        self.assertFalse(file.exists())
        self.assertEqual((self.home / "FixtureTrash" / file.name).read_text(), "synthetic data")
        before = len(self.calls)
        with self.assertRaisesRegex(ValueError, "review expired"):
            self.app.trash(plan["receipt"])
        self.assertEqual(len(self.calls), before)

    def test_expired_plan_is_consumed_without_mutation(self):
        file = self.file()
        plan = self.app.plan([self.row(file)["id"]])
        self.app.plans[plan["receipt"]]["time"] = time.monotonic() - server.PLAN_TTL
        with self.assertRaisesRegex(ValueError, "review expired"):
            self.app.trash(plan["receipt"])
        self.assertNotIn(plan["receipt"], self.app.plans)
        self.assertTrue(file.exists())
        self.assertEqual(len(self.calls), 1)

    def test_replaced_target_is_kept_after_review(self):
        file = self.file()
        plan = self.app.plan([self.row(file)["id"]])
        file.rename(self.downloads / "Original")
        file.write_text("replacement")
        result = self.app.trash(plan["receipt"])
        self.assertEqual(result["completed"], [])
        self.assertEqual(result["remaining"], [str(file)])
        self.assertIn("changed", result["error"])
        self.assertEqual(file.read_text(), "replacement")
        self.assertEqual(len(self.calls), 1)

    def test_parent_replacement_refuses_even_when_target_inode_is_unchanged(self):
        file = self.file("Folder/child.txt")
        plan = self.app.plan([self.row(file)["id"]])
        original_inode = file.stat().st_ino
        old_parent = self.downloads / "OldFolder"
        file.parent.rename(old_parent)
        file.parent.mkdir()
        (old_parent / file.name).rename(file)
        self.assertEqual(file.stat().st_ino, original_inode)
        result = self.app.trash(plan["receipt"])
        self.assertIn("changed", result["error"])
        self.assertTrue(file.exists())
        self.assertEqual(len(self.calls), 1)

    def test_nanosecond_change_or_symlink_swap_invalidates_selection(self):
        file = self.file()
        base = file.stat()
        mtime = (base.st_mtime_ns // 1_000_000_000) * 1_000_000_000 + 10000
        os.utime(file, ns=(base.st_atime_ns, mtime))
        plan = self.app.plan([self.row(file)["id"]])
        os.utime(file, ns=(base.st_atime_ns, mtime + 10000))
        result = self.app.trash(plan["receipt"])
        self.assertIn("changed", result["error"])
        plan = self.app.plan([self.row(file)["id"]])
        file.rename(self.downloads / "Original")
        file.symlink_to(self.downloads / "Original")
        result = self.app.trash(plan["receipt"])
        self.assertIn("protected", result["error"])
        self.assertTrue(file.is_symlink())

    def test_failed_preview_stops_before_other_eligible_item(self):
        first, second = self.file("First"), self.file("Second")
        original = self.app.runner

        def runner(argv, **kwargs):
            if argv[5] == str(first):
                self.calls.append((argv, kwargs))
                raise ValueError("Fixture safety probe failed")
            return original(argv, **kwargs)

        self.app.runner = runner
        with self.assertRaisesRegex(ValueError, "probe failed"):
            self.app.plan([self.row(first)["id"], self.row(second)["id"]])
        self.assertEqual([call[0][5] for call in self.calls], [str(first)])
        self.assertEqual(self.app.plans, {})
        self.app.plan([self.row(second)["id"]])  # Positive control: the later item is eligible.
        self.assertEqual(self.calls[-1][0][5], str(second))

    def test_partial_completion_stops_before_remaining_eligible_item(self):
        files = [self.file(name) for name in ["First", "Second", "Third"]]
        plan = self.app.plan([self.row(file)["id"] for file in files])
        original = self.app.runner

        def runner(argv, **kwargs):
            if argv[4] == "trash" and argv[5] == str(files[1]):
                self.calls.append((argv, kwargs))
                raise ValueError("Fixture removal timed out")
            return original(argv, **kwargs)

        self.app.runner = runner
        result = self.app.trash(plan["receipt"])
        self.assertEqual(result["completed"], [str(files[0])])
        self.assertEqual(result["remaining"], [str(file) for file in files[1:]])
        self.assertIn("timed out", result["error"])
        self.assertEqual([call[0][5] for call in self.calls if call[0][4] == "trash"],
                         [str(files[0]), str(files[1])])
        self.assertTrue(files[2].exists())
        self.app.trash(self.app.plan([self.row(files[2])["id"]])["receipt"])
        self.assertFalse(files[2].exists())  # Positive control for the skipped sink.

    def test_shutdown_finishes_current_attempt_and_stops_remaining_items(self):
        first, second = self.file("First"), self.file("Second")
        plan = self.app.plan([self.row(first)["id"], self.row(second)["id"]])
        original = self.app.runner

        def runner(argv, **kwargs):
            result = original(argv, **kwargs)
            if argv[4] == "trash":
                self.app.stopping.set()
            return result

        self.app.runner = runner
        result = self.app.trash(plan["receipt"])
        self.assertEqual(result["completed"], [str(first)])
        self.assertEqual(result["remaining"], [str(second)])
        self.assertIn("closing", result["error"])
        self.assertTrue(second.exists())

    def test_preview_requires_full_budget_and_discards_unfinished_review(self):
        files = [self.file(str(i)) for i in range(4)]
        ids = [self.row(file)["id"] for file in files]
        clock = [time.monotonic()]

        def runner(argv, **kwargs):
            self.calls.append((argv, kwargs))
            clock[0] += 60
            return ""

        self.app.runner = runner
        with patch.object(server.time, "monotonic", side_effect=lambda: clock[0]):
            with self.assertRaisesRegex(ValueError, "Preview timed out"):
                self.app.plan(ids)
        self.assertEqual([call[1]["timeout"] for call in self.calls], [45, 45, 45])
        self.assertEqual(self.app.plans, {})

    def test_near_exhausted_trash_budget_never_starts_next_eligible_helper(self):
        first, second = self.file("First"), self.file("Second")
        plan = self.app.plan([self.row(first)["id"], self.row(second)["id"]])
        original = self.app.runner
        clock = [time.monotonic()]

        def runner(argv, **kwargs):
            result = original(argv, **kwargs)
            if argv[4] == "trash":
                clock[0] += 80
            return result

        self.app.runner = runner
        with patch.object(server.time, "monotonic", side_effect=lambda: clock[0]):
            result = self.app.trash(plan["receipt"])
        self.assertEqual(result["completed"], [str(first)])
        self.assertEqual(result["unconfirmed"], [])
        self.assertEqual(result["not_attempted"], [str(second)])
        attempts = [call for call in self.calls if call[0][4] == "trash"]
        self.assertEqual([call[0][5] for call in attempts], [str(first)])
        self.assertEqual(attempts[0][1]["timeout"], server.TRASH_ATTEMPT_BUDGET)
        self.assertTrue(second.exists())
        self.app.runner = original
        later = self.app.trash(self.app.plan([self.row(second)["id"]])["receipt"])
        self.assertEqual(later["completed"], [str(second)])

    def test_missing_source_without_bridge_receipt_is_unconfirmed(self):
        first, second = self.file("First"), self.file("Second")
        plan = self.app.plan([self.row(first)["id"], self.row(second)["id"]])

        def disappearing(argv, **kwargs):
            self.calls.append((argv, kwargs))
            Path(argv[5]).unlink()  # Only this test's synthetic file.
            return ""

        self.app.runner = disappearing
        result = self.app.trash(plan["receipt"])
        self.assertEqual(result["completed"], [])
        self.assertEqual(result["unconfirmed"], [str(first)])
        self.assertEqual(result["not_attempted"], [str(second)])
        self.assertIn("absence alone", result["error"])
        self.assertTrue(second.exists())

    def test_timed_out_helper_may_have_moved_path_but_is_never_reported_kept(self):
        first, second = self.file("First"), self.file("Second")
        plan = self.app.plan([self.row(first)["id"], self.row(second)["id"]])
        original = self.app.runner

        def timeout(argv, **kwargs):
            original(argv, **kwargs)
            raise ValueError("Operation timed out. Refresh the view before trying again.")

        self.app.runner = timeout
        result = self.app.trash(plan["receipt"])
        self.assertFalse(first.exists())
        self.assertEqual(result["completed"], [])
        self.assertEqual(result["unconfirmed"], [str(first)])
        self.assertEqual(result["not_attempted"], [str(second)])
        self.assertNotIn("kept", result["error"].lower())
        self.assertTrue(second.exists())

    def test_bridge_drops_startup_overrides_and_keeps_fixture_home(self):
        file = self.file()
        with patch.dict(os.environ, {"BASH_ENV": str(self.home / "unsafe"),
                                     "ENV": "unsafe", "MOLE_COMMON_LOADED": "1"}):
            self.app.plan([self.row(file)["id"]])
        env = self.calls[0][1]["env"]
        self.assertNotIn("BASH_ENV", env)
        self.assertNotIn("MOLE_COMMON_LOADED", env)
        self.assertEqual(env["HOME"], str(self.home))

    def test_disk_summary_reports_real_free_bytes(self):
        usage = server.shutil.disk_usage(self.home)
        state = self.app.state()
        self.assertEqual(state["disk"]["total"], usage.total)
        self.assertGreaterEqual(state["disk"]["free"], 0)
        self.assertEqual(set(state["disk"]), {"total", "used", "free"})


class HttpFixture(Fixture):
    def setUp(self):
        super().setUp()
        self.http = server.LocalServer(self.app)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.host = f"127.0.0.1:{self.http.server_port}"

    def stop_server(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=3)

    def request(self, method, path, data=None, headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.http.server_port, timeout=5)
        request_headers = {"Host": self.host, "X-Mole-Token": self.app.token,
                           "Origin": "http://" + self.host}
        if data is not None:
            body = json.dumps(data).encode()
            request_headers["Content-Type"] = "application/json"
        request_headers.update(headers or {})
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        content = response.read()
        result = (response.status, dict(response.getheaders()), json.loads(content))
        connection.close()
        return result


class HttpTests(HttpFixture):
    def test_host_origin_and_token_are_checked(self):
        for headers, expected in [
                ({"Host": "localhost:" + str(self.http.server_port)}, 403),
                ({"Host": "evil.test"}, 403),
                ({"Origin": "https://evil.test"}, 403),
                ({"Origin": "null"}, 403),
                ({"X-Mole-Token": ""}, 401),
                ({"X-Mole-Token": "wrong"}, 401),
                ({"X-Mole-Token": "\xe9"}, 401)]:
            with self.subTest(headers=headers):
                self.assertEqual(self.request("GET", "/api/state", headers=headers)[0], expected)
        status, headers, _ = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])

    def test_absolute_form_targets_do_not_bypass_token(self):
        status, _, _ = self.request("GET", "http://" + self.host + "/api/state",
                                   headers={"X-Mole-Token": ""})
        self.assertEqual(status, 400)

    def test_invalid_json_shapes_always_return_400(self):
        inputs = [[], None, 1, {"command": []}, {"command": {}},
                  {"command": "clean", "flags": [[]]},
                  {"command": "clean", "fields": {"external": []}}]
        for data in inputs:
            with self.subTest(data=data):
                body = json.dumps(data).encode()
                self.assertEqual(self.request("POST", "/api/command", body=body,
                                             headers={"Content-Type": "application/json"})[0], 400)
        for path, data in [("/api/report", {"kind": []}), ("/api/plan", {"ids": [None]}),
                           ("/api/trash", {"receipt": []}), ("/api/plan", {"path": str(self.home)})]:
            with self.subTest(path=path, data=data):
                self.assertEqual(self.request("POST", path, data=data)[0], 400)

    def test_invalid_encoding_duplicate_keys_and_nonfinite_json_refuse(self):
        for body in [b"{", b'{"command":"help","command":"clean"}', b'{"command":NaN}',
                     b"\xff", b"[" * 1500 + b"]" * 1500]:
            with self.subTest(body=body[:60]):
                self.assertEqual(self.request("POST", "/api/command", body=body,
                                             headers={"Content-Type": "application/json"})[0], 400)

    def test_request_size_and_media_type_refuse(self):
        self.assertEqual(self.request("POST", "/api/plan", body=b"{}")[0], 415)
        for length in ["0", "-1", "abc", "16385"]:
            with self.subTest(length=length):
                self.assertEqual(self.request("POST", "/api/plan", body=b"{}",
                                             headers={"Content-Type": "application/json",
                                                      "Content-Length": length})[0], 400)
        status, _, body = self.request("POST", "/api/command", data={"command": "version"},
                                      headers={"Content-Type": "application/json; charset=utf-8"})
        self.assertEqual(status, 200)
        self.assertEqual(body["command"], "mo version")

    def test_duplicate_security_headers_refuse(self):
        with socket.create_connection(("127.0.0.1", self.http.server_port), timeout=5) as connection:
            payload = (f"GET /api/state HTTP/1.1\r\nHost: {self.host}\r\nHost: {self.host}\r\n"
                       f"X-Mole-Token: {self.app.token}\r\nConnection: close\r\n\r\n")
            connection.sendall(payload.encode())
            self.assertIn(b" 403 ", connection.recv(2048).split(b"\r\n", 1)[0])
        with socket.create_connection(("127.0.0.1", self.http.server_port), timeout=5) as connection:
            payload = (f"POST /api/plan HTTP/1.1\r\nHost: {self.host}\r\n"
                       f"X-Mole-Token: {self.app.token}\r\nContent-Type: application/json\r\n"
                       "Content-Length: 2\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
            connection.sendall(payload.encode())
            self.assertIn(b" 400 ", connection.recv(2048).split(b"\r\n", 1)[0])

    def test_server_rejects_overlapping_operations(self):
        self.app.lock.acquire()
        try:
            self.assertEqual(self.request("POST", "/api/command", data={"command": "help"})[0], 200)
            self.assertEqual(self.request("POST", "/api/launch", data={"command": "help"})[0], 409)
            query = urlencode({"path": str(self.downloads)})
            self.assertEqual(self.request("GET", "/api/browse?" + query)[0], 409)
        finally:
            self.app.lock.release()
        self.assertEqual(self.request("POST", "/api/command", data={"command": "help"})[0], 200)

    def test_api_browse_review_and_trash_return_confirmed_ledger(self):
        file = self.file()
        status, _, view = self.request("GET", "/api/browse?" + urlencode({"path": str(self.downloads)}))
        self.assertEqual(status, 200)
        status, _, plan = self.request("POST", "/api/plan", data={"ids": [view["entries"][0]["id"]]})
        self.assertEqual(status, 200)
        self.assertTrue(file.exists())
        status, _, result = self.request("POST", "/api/trash", data={"receipt": plan["receipt"]})
        self.assertEqual(status, 200)
        self.assertEqual(result["completed"], [str(file)])
        self.assertFalse(file.exists())
        self.assertEqual(self.request("POST", "/api/trash", data={"receipt": plan["receipt"]})[0], 400)

    def test_server_close_waits_for_current_destructive_request(self):
        file = self.file()
        plan = self.app.plan([self.row(file)["id"]])
        entered, release, closed = threading.Event(), threading.Event(), threading.Event()
        original = self.app.runner

        def runner(argv, **kwargs):
            entered.set()
            if not release.wait(3):
                raise AssertionError("Test did not release its active fixture request")
            return original(argv, **kwargs)

        self.app.runner = runner
        responses = []
        request = threading.Thread(target=lambda: responses.append(
            self.request("POST", "/api/trash", data={"receipt": plan["receipt"]})))
        request.start()
        try:
            self.assertTrue(entered.wait(3))
            self.http.shutdown()

            def close():
                self.http.server_close()
                closed.set()

            closer = threading.Thread(target=close)
            closer.start()
            self.assertFalse(closed.wait(0.1))
            release.set()
            closer.join(timeout=3)
            request.join(timeout=3)
            self.assertTrue(closed.is_set())
            self.assertEqual(responses[0][0], 200)
            self.assertEqual(responses[0][2]["completed"], [str(file)])
            self.assertFalse(file.exists())
        finally:
            release.set()
            request.join(timeout=3)


class SubprocessTests(Fixture):
    def test_bounded_output_and_stdin_are_observable(self):
        result = server.run_bounded([sys.executable, "-c",
                                     "import sys; print(repr(sys.stdin.read()))"], timeout=2)
        self.assertEqual(result.strip(), "''")
        with patch.object(server, "MAX_OUTPUT", 1024):
            with self.assertRaisesRegex(ValueError, "too large"):
                server.run_bounded([sys.executable, "-c", "print('x' * 2048)"], timeout=2)
        with self.assertRaisesRegex(ValueError, "fixture failure"):
            server.run_bounded([sys.executable, "-c",
                                "import sys; print('fixture failure'); sys.exit(3)"], timeout=2)

    def test_timeout_kills_child_process_group(self):
        marker = self.home / "child-finished"
        child_code = "import pathlib,time; time.sleep(0.8); pathlib.Path(" + repr(str(marker)) + ").touch()"
        parent_code = ("import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',"
                       + repr(child_code) + "]); print('child-started',flush=True); time.sleep(10)")
        with self.assertRaisesRegex(ValueError, "timed out"):
            server.run_bounded([sys.executable, "-c", parent_code], timeout=0.3)
        time.sleep(1)
        self.assertFalse(marker.exists())
        # Positive control proves the same child would perform the side effect.
        server.run_bounded([sys.executable, "-c", child_code], timeout=2)
        self.assertTrue(marker.exists())

    def test_terminal_handoff_quotes_argv_without_executing_interpolation(self):
        marker = self.home / "injected"
        capture = self.home / "argv.json"
        executable = self.home / "Fixture Mole"
        executable.write_text("#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n"
                              f"Path({str(capture)!r}).write_text(json.dumps(sys.argv[1:]))\n")
        executable.chmod(0o700)
        self.app.executable = str(executable)
        names = ["Demo'App;$(touch " + str(marker) + ")",
                 "App" + chr(96) + "touch " + str(marker) + chr(96)]
        opens = []
        self.app.runner = lambda argv, **kwargs: opens.append(argv) or ""
        with patch.object(server.platform, "system", return_value="Darwin"):
            with patch.dict(os.environ, {"MOLE_TEST_NO_AUTH": "0", "MOLE_TEST_MODE": "0"}):
                result = self.app.launch({"command": "uninstall", "flags": ["dry-run"],
                                          "fields": {"apps": "\n".join(names)}})
        self.assertEqual(len(opens), 1)
        self.assertEqual(opens[0][:3], ["/usr/bin/open", "-a", "Terminal"])
        command_file = Path(opens[0][3])
        self.assertEqual(command_file.stat().st_mode & 0o777, 0o700)
        self.assertEqual(shlex.split(result["command"]), [str(executable), "uninstall", "--dry-run"] + names)
        server.run_bounded(["/bin/bash", str(command_file)], timeout=3)
        self.assertEqual(json.loads(capture.read_text()), ["uninstall", "--dry-run"] + names)
        self.assertFalse(marker.exists())
        self.app.close()
        self.assertFalse(command_file.exists())

    def test_terminal_launch_is_disabled_during_test_mode(self):
        with patch.object(server.platform, "system", return_value="Darwin"):
            with patch.dict(os.environ, {"MOLE_TEST_NO_AUTH": "1"}):
                with self.assertRaisesRegex(ValueError, "disabled"):
                    self.app.launch({"command": "help"})
        self.assertEqual(self.calls, [])

    def test_reports_have_exact_read_only_argv_and_require_complete_json(self):
        calls = []
        self.app.runner = lambda argv, **kwargs: calls.append(argv) or '{"fixture":true}'
        self.app.report("history")
        self.assertEqual(calls[-1], [self.app.executable, "history", "--json", "--limit", "20"])
        self.app.report("apps")
        self.assertEqual(calls[-1], [self.app.executable, "uninstall", "--list"])
        for kind in [[], {}, None, "arbitrary"]:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.app.report(kind)
        self.app.runner = lambda *args, **kwargs: '{"unfinished"'
        with self.assertRaisesRegex(ValueError, "complete JSON"):
            self.app.report("history")

    def test_root_startup_stops_before_app_creation(self):
        with patch.object(server.os, "geteuid", return_value=0), \
                patch.object(server, "App") as app, \
                patch.object(sys, "argv", ["gui/server.py"]), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                server.main()
        self.assertEqual(result.exception.code, 2)
        app.assert_not_called()


@unittest.skipUnless(platform.system() == "Darwin" and os.geteuid() != 0,
                     "The production shell helpers require BSD stat and a regular macOS user.")
class ShellBridgeTests(Fixture):
    def setUp(self):
        super().setUp()
        tmpdir = self.home / "Tmp"
        tmpdir.mkdir()
        fixture_env = {"HOME": str(self.home), "MOLE_TEST_NO_AUTH": "1", "MOLE_TEST_MODE": "0",
                       "MOLE_TEST_TRASH_DIR": str(self.home / "FixtureTrash"), "NO_COLOR": "1",
                       "MOLE_DELETE_LOG": str(self.home / "Library/Logs/mole/deletions.log"),
                       "MO_NO_OPLOG": "0", "TMPDIR": str(tmpdir),
                       "MOLE_RESOLVED_TMPDIR": str(tmpdir), "MOLE_TEMP_REGISTRY_FILE": ""}
        self.env = patch.dict(os.environ, fixture_env)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app.runner = server.run_bounded

    def test_actual_helper_preview_and_trash_log_confirmed_synthetic_file(self):
        file = self.file("Fixture 'quote;$(echo literal).txt")
        plan = self.app.plan([self.row(file)["id"]])
        self.assertTrue(file.exists())
        log = self.home / "Library/Logs/mole/deletions.log"
        self.assertIn("\ttrash\t", log.read_text())
        self.assertIn("\tdry-run\t", log.read_text())
        result = self.app.trash(plan["receipt"])
        self.assertEqual(result["completed"], [str(file)])
        self.assertIsNone(result["error"])
        self.assertFalse(file.exists())
        trashed = list((self.home / "FixtureTrash").iterdir())
        self.assertEqual(len(trashed), 1)
        self.assertEqual(trashed[0].read_text(), "synthetic data")
        self.assertIn("\tok\t", log.read_text())
        operation_logs = list((self.home / "Library/Logs/mole").glob("*.log"))
        self.assertTrue(any("TRASHED" in path.read_text() for path in operation_logs))
        self.assertIn("TRASH_ATTEMPT", (self.home / "Library/Logs/mole/operations.log").read_text())

    def test_disabled_operation_log_keeps_native_forensic_receipt_without_pending_rows(self):
        file = self.file()
        with patch.dict(os.environ, {"MO_NO_OPLOG": "1"}):
            plan = self.app.plan([self.row(file)["id"]])
            result = self.app.trash(plan["receipt"])
        self.assertEqual(result["completed"], [str(file)])
        operation_log = self.home / "Library/Logs/mole/operations.log"
        self.assertFalse(operation_log.exists())
        self.assertIn("\tok\t", (self.home / "Library/Logs/mole/deletions.log").read_text())

    def test_bridge_missing_target_at_native_entry_never_acknowledges_a_move(self):
        file = self.file()
        dev, inode, mtime_ns, _, parent_dev, parent_inode = server.identity(file)
        wrapper = self.home / "fixture-python"
        wrapper.write_text(
            "#!/usr/bin/env python3\n"
            "import pathlib,subprocess,sys\n"
            "result = subprocess.run([sys.executable] + sys.argv[1:])\n"
            "if result.returncode == 0 and sys.argv[2] == 'pending':\n"
            "    pathlib.Path(sys.argv[4]).unlink()\n"
            "raise SystemExit(result.returncode)\n")
        wrapper.chmod(0o700)
        argv = ["/bin/bash", str(server.ROOT / "gui/trash.sh"), "trash", str(file),
                f"{dev}:{inode}:{mtime_ns // 1_000_000_000}", f"{parent_dev}:{parent_inode}"]
        with patch.dict(os.environ, {"MOLE_GUI_PYTHON": str(wrapper)}):
            with self.assertRaises(ValueError) as result:
                server.run_bounded(argv, timeout=10)
        self.assertIn("unconfirmed", str(result.exception))
        self.assertNotIn(server.TRASH_ACK, str(result.exception))
        self.assertFalse(file.exists())
        self.assertFalse((self.home / "FixtureTrash").exists())
        operations = (self.home / "Library/Logs/mole/operations.log").read_text()
        self.assertIn("TRASH_ATTEMPT " + str(file), operations)
        self.assertIn("TRASH_UNCONFIRMED " + str(file), operations)

    def test_actual_preview_refuses_shared_whitelist_and_protected_name(self):
        file = self.file()
        config = self.home / ".config/mole/whitelist"
        config.parent.mkdir(parents=True)
        config.write_text(str(file) + "\n")
        with self.assertRaisesRegex(ValueError, "protects this path"):
            self.app.plan([self.row(file)["id"]])
        protected = self.file("com.apple.Settings.cache")
        with patch.dict(os.environ, {"MOLE_UNINSTALL_MODE": "1"}):
            with self.assertRaisesRegex(ValueError, "protects this path"):
                self.app.plan([self.row(protected)["id"]])
        self.assertTrue(file.exists())
        self.assertTrue(protected.exists())
        self.assertFalse((self.home / "FixtureTrash").exists())

    def test_bridge_refuses_personal_root_with_or_without_trailing_slash(self):
        dev, inode, mtime_ns, _, parent_dev, parent_inode = server.identity(self.downloads)
        expected = f"{dev}:{inode}:{mtime_ns // 1_000_000_000}"
        for path in [str(self.downloads), str(self.downloads) + "/", str(self.downloads) + "//"]:
            argv = ["/bin/bash", str(server.ROOT / "gui/trash.sh"), "trash", path,
                    expected, f"{parent_dev}:{parent_inode}"]
            cause = "selection is invalid" if path.endswith("/") else "inside personal folders"
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, cause):
                server.run_bounded(argv, timeout=10)
        self.assertTrue(self.downloads.exists())
        self.assertFalse((self.home / "FixtureTrash").exists())

    def test_bridge_rechecks_approved_parent_and_refuses_symlinks_independently(self):
        file = self.file("Folder/child.txt")
        selected = server.identity(file)
        dev, inode, mtime_ns, _, parent_dev, parent_inode = selected
        expected = f"{dev}:{inode}:{mtime_ns // 1_000_000_000}"
        argv = ["/bin/bash", str(server.ROOT / "gui/trash.sh"), "trash", str(file),
                expected, f"{parent_dev}:{parent_inode}"]
        original_parent = file.parent
        old_parent = self.downloads / "OldFolder"
        original_parent.rename(old_parent)
        original_parent.mkdir()
        (old_parent / file.name).rename(file)
        with self.assertRaisesRegex(ValueError, "folder changed"):
            server.run_bounded(argv, timeout=10)
        self.assertTrue(file.exists())
        alias = self.downloads / "Alias"
        alias.symlink_to(original_parent)
        alias_target = alias / file.name
        argv[3] = str(alias_target)
        argv[-1] = f"{file.parent.stat().st_dev}:{file.parent.stat().st_ino}"
        with self.assertRaisesRegex(ValueError, "folder changed"):
            server.run_bounded(argv, timeout=10)
        self.assertTrue(file.exists())
        self.assertFalse((self.home / "FixtureTrash").exists())


if __name__ == "__main__":
    unittest.main()
