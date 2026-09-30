"""GUI job, listing, and native-action tests using only isolated fixtures."""
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

from gui import browser, jobs, processes, server
from gui.test_server import Fixture, HttpFixture


def wait_job(app, key, timeout=4):
    app.jobs.jobs[key].thread.join(timeout=timeout)
    result = app.jobs.snapshot(key)
    if result["status"] == "running":
        raise AssertionError("The fixture job did not finish")
    return result


def measured(path, state="complete"):
    return {"path": str(path), "total_size": 3, "scan_status": state, "overview": False,
            "entries": [{"name": "fixture.txt", "path": str(path / "fixture.txt"),
                         "size": 3, "is_dir": False, "scan_status": state}]}


def preview_text(path, annotation="3 KB"):
    return ("# Mole Cleanup Preview - fixture\n\n=== User caches ===\n"
            + str(path) + "  # " + annotation
            + "\n\n# Summary\n# Potential cleanup: 3 KB\n# Items: 1\n# Categories: 1\n")


class BrowseTests(Fixture):
    def test_pagination_reaches_more_than_1500_entries_without_skipping_tail(self):
        for index in range(1505):
            self.file(f"{index:04}.txt", "x")
        names, offset = [], 0
        while True:
            result = self.app.browse(str(self.downloads), offset=offset, sort="name", order="asc")
            self.assertFalse(result["partial"])
            self.assertEqual(result["total_visible"], 1505)
            self.assertEqual(result["total_filtered"], 1505)
            self.assertLessEqual(len(result["entries"]), 200)
            names.extend(row["name"] for row in result["entries"])
            if result["next_offset"] is None:
                break
            offset = result["next_offset"]
        self.assertEqual(names, [f"{index:04}.txt" for index in range(1505)])
        self.assertGreater(result["sampled_at"], 0)

    def test_filters_use_file_metadata_without_following_links(self):
        image = self.file("Holiday.JPG", "image data")
        video = self.file("Trip.mp4", "video")
        document = self.file("Notes.pdf", "pdf")
        archive = self.file("Archive.zip", "zip")
        self.file("Installer.dmg", "dmg")
        folder = self.downloads / "Folder"
        folder.mkdir()
        alias = self.downloads / "alias.JPG"
        alias.symlink_to(image)
        old = time.time() - 20 * 86400
        os.utime(image, (old, old))
        query = self.app.browse(str(self.downloads), q="holiday", type="image", min_size=8, older_days=10)
        self.assertEqual([row["name"] for row in query["entries"]], [image.name])
        self.assertTrue(query["entries"][0]["previewable"])
        for kind, expected in [("video", video.name), ("document", document.name),
                               ("archive", archive.name), ("installer", "Installer.dmg"),
                               ("folder", folder.name)]:
            result = self.app.browse(str(self.downloads), type=kind)
            self.assertEqual([row["name"] for row in result["entries"]], [expected])
        regular = self.app.browse(str(self.downloads), type="file")
        self.assertNotIn(alias.name, [row["name"] for row in regular["entries"]])
        unfiltered = self.app.browse(str(self.downloads))
        row = next(row for row in unfiltered["entries"] if row["name"] == alias.name)
        self.assertFalse(row["eligible"])
        self.assertFalse(row["previewable"])
        self.assertFalse(row["revealable"])
        self.assertEqual(self.calls, [])

    def test_incomplete_listing_does_not_claim_complete_counts_or_next_page(self):
        for index in range(5):
            self.file(str(index))
        with patch.object(browser, "MAX_ENTRIES", 3):
            result = self.app.browse(str(self.downloads))
        self.assertTrue(result["partial"])
        self.assertIsNone(result["total_visible"])
        self.assertIsNone(result["total_filtered"])
        self.assertIsNone(result["next_offset"])
        self.assertEqual(result["observed_visible"], 3)
        self.assertEqual(result["observed_filtered"], 3)

    def test_filter_invalid_types_and_ranges_refuse(self):
        cases = [{"offset": []}, {"offset": -1}, {"offset": True}, {"q": {}},
                 {"type": []}, {"type": "executable"}, {"sort": {}},
                 {"order": "sideways"}, {"min_size": "9"}, {"older_days": 365001}]
        for values in cases:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.app.browse(str(self.downloads), **values)

    def test_listings_are_fresh_after_file_changes_and_receipts_are_bounded(self):
        target = self.file(content="one")
        before = self.row(target)
        target.write_text("longer content")
        after = self.row(target)
        self.assertNotEqual(before["size"], after["size"])
        with self.assertRaises(ValueError):
            self.app.plan([before["id"]])
        with patch.object(browser, "MAX_RECEIPTS", 2):
            for _ in range(4):
                self.app.browse(str(self.downloads))
        self.assertEqual(len(self.app.entries), 2)


class JobTests(Fixture):
    def test_analyze_has_exact_scope_argv_env_and_preserves_partial_coverage(self):
        calls = []

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return json.dumps(measured(self.downloads, "partial"))

        self.app.runner = runner
        with patch.dict(os.environ, {"MO_ANALYZE_PATH": "/outside", "BASH_ENV": "unsafe",
                                     "MO_NO_OPLOG": "1"}):
            key = self.app.start_job({"kind": "analyze", "path": str(self.downloads)})["id"]
            result = wait_job(self.app, key)
        self.assertEqual(result["status"], "completed")
        self.assertIsNone(result["progress"])
        self.assertEqual(result["request"], {"kind": "analyze", "path": str(self.downloads)})
        self.assertEqual(result["result"]["scan_status"], "partial")
        self.assertEqual(result["result"]["entries"][0]["scan_status"], "partial")
        self.assertEqual(result["sampled_at"], result["result"]["sampled_at"])
        self.assertEqual(calls[0][0][1:], ["analyze", "--json", str(self.downloads)])
        env = calls[0][1]["env"]
        self.assertEqual(env["HOME"], str(self.home))
        self.assertEqual(env["MOLE_DRY_RUN"], "1")
        self.assertEqual(env["MOLE_TEST_NO_AUTH"], "1")
        self.assertEqual(env["MO_NO_OPLOG"], "1")
        self.assertNotIn("MO_ANALYZE_PATH", env)
        self.assertNotIn("BASH_ENV", env)
        self.assertFalse(Path(env["TMPDIR"]).exists())

    def test_invalid_or_wrong_scope_json_is_not_published(self):
        wrong = measured(self.home.parent)
        malformed = measured(self.downloads)
        malformed["entries"][0]["path"] = "/etc/passwd"
        missing = measured(self.downloads)
        missing["entries"][0].pop("scan_status")
        for output in ["{", "null", json.dumps(wrong), json.dumps(malformed), json.dumps(missing)]:
            self.app.runner = lambda *args, value=output, **kwargs: value
            key = self.app.start_job({"kind": "analyze", "path": str(self.downloads)})["id"]
            result = wait_job(self.app, key)
            with self.subTest(output=output):
                self.assertEqual(result["status"], "failed")
                self.assertIsNone(result["result"])
                self.assertTrue(result["error"])

    def test_invalid_new_job_shapes_refuse_before_start(self):
        cases = [[], {}, {"kind": []}, {"kind": "analyze", "path": []},
                 {"kind": "report", "report": []}, {"kind": "report", "report": "shell"},
                 {"kind": "preview", "command": []},
                 {"kind": "preview", "command": "clean", "apps": []},
                 {"kind": "preview", "command": "uninstall", "apps": []},
                 {"kind": "preview", "command": "uninstall", "apps": ["--permanent"]},
                 {"kind": "preview", "command": "uninstall", "apps": [None]},
                 {"kind": "report", "report": "status", "argv": ["/bin/sh"]}]
        for data in cases:
            with self.subTest(data=data), self.assertRaises((ValueError, OSError)):
                self.app.start_job(data)
        self.assertEqual(self.calls, [])

    def test_cancellation_discards_late_output_and_next_job_still_works(self):
        entered = threading.Event()

        def runner(argv, **kwargs):
            entered.set()
            if not kwargs["cancel"].wait(3):
                raise AssertionError("Fixture did not receive cancellation")
            return json.dumps(measured(self.downloads))

        self.app.runner = runner
        first = self.app.start_job({"kind": "analyze", "path": str(self.downloads)})["id"]
        self.assertTrue(entered.wait(2))
        self.assertTrue(self.app.lock.locked())
        with self.assertRaises(jobs.Busy):
            self.app.start_job({"kind": "report", "report": "status"})
        self.assertEqual(self.app.jobs.active_snapshot()["active"]["id"], first)
        self.app.jobs.cancel(first)
        cancelled = wait_job(self.app, first)
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertIsNone(cancelled["result"])
        self.assertIsNone(cancelled["sampled_at"])
        self.app.runner = lambda *args, **kwargs: '{"health_score":80}'
        second = self.app.start_job({"kind": "report", "report": "status"})["id"]
        self.app.jobs.cancel(first)  # An old receipt cannot cancel a new worker.
        self.assertEqual(wait_job(self.app, second)["status"], "completed")

    def test_history_job_requests_200_and_registry_retention_is_bounded(self):
        calls = []
        self.app.runner = lambda argv, **kwargs: calls.append(argv) or '{"sessions":[],"deletions":[]}'
        with patch.object(jobs, "MAX_JOBS", 3):
            keys = []
            for _ in range(5):
                key = self.app.start_job({"kind": "report", "report": "history"})["id"]
                keys.append(key)
                result = wait_job(self.app, key)
                self.assertEqual(result["result"]["limit"], 200)
            self.assertEqual(len(self.app.jobs.jobs), 3)
            with self.assertRaises(jobs.MissingJob):
                self.app.jobs.snapshot(keys[0])
        self.assertEqual(calls[-1][1:], ["history", "--json", "--limit", "200"])
        completed = self.app.jobs.jobs[keys[-1]]
        completed.finished_mono = time.monotonic() - jobs.RETENTION_SECONDS
        with self.assertRaises(jobs.MissingJob):
            self.app.jobs.snapshot(keys[-1])

    def test_shutdown_cancels_and_joins_a_running_worker(self):
        entered = threading.Event()

        def runner(*args, **kwargs):
            entered.set()
            if not kwargs["cancel"].wait(3):
                raise AssertionError("Shutdown did not cancel the fixture worker")
            raise jobs.Cancelled("cancelled")

        self.app.runner = runner
        key = self.app.start_job({"kind": "report", "report": "status"})["id"]
        self.assertTrue(entered.wait(2))
        self.app.close()
        self.assertFalse(self.app.jobs.jobs[key].thread.is_alive())
        self.assertEqual(self.app.jobs.snapshot(key)["status"], "cancelled")
        with self.assertRaises(ValueError):
            self.app.start_job({"kind": "report", "report": "status"})

    def test_cancellation_kills_entire_owned_process_group(self):
        marker = self.home / "child-finished"
        started = self.home / "started"
        child = "import time,pathlib; time.sleep(0.7); pathlib.Path(" + repr(str(marker)) + ").touch()"
        parent = ("import subprocess,sys,time,pathlib; subprocess.Popen([sys.executable,'-c',"
                  + repr(child) + "]); pathlib.Path(" + repr(str(started)) + ").touch(); time.sleep(20)")
        event, errors = threading.Event(), []

        def run():
            try:
                server.run_bounded([sys.executable, "-c", parent], timeout=3, cancel=event)
            except jobs.Cancelled:
                errors.append("cancelled")

        worker = threading.Thread(target=run)
        worker.start()
        try:
            deadline = time.monotonic() + 2
            while not started.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(started.exists())
            event.set()
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, ["cancelled"])
            time.sleep(0.9)
            self.assertFalse(marker.exists())
            server.run_bounded([sys.executable, "-c", child], timeout=2)
            self.assertTrue(marker.exists())  # Positive control for the child side effect.
        finally:
            event.set()
            worker.join(timeout=4)

    def test_cancellation_after_stdout_closes_still_stops_process(self):
        event, errors = threading.Event(), []
        code = "import os,time; os.close(1); os.close(2); time.sleep(20)"

        def run():
            try:
                server.run_bounded([sys.executable, "-c", code], timeout=3, cancel=event)
            except jobs.Cancelled:
                errors.append("cancelled")

        worker = threading.Thread(target=run)
        worker.start()
        time.sleep(0.1)
        event.set()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, ["cancelled"])

    def test_cancel_stops_nested_group_and_preserves_unrelated_process(self):
        marker = self.home / "nested-child-finished"
        started = self.home / "nested-started"
        child = "import time,pathlib; time.sleep(0.7); pathlib.Path(" + repr(str(marker)) + ").touch()"
        parent = ("import subprocess,sys,time,pathlib,os; subprocess.Popen([sys.executable,'-c',"
                  + repr(child) + "],preexec_fn=os.setpgrp); pathlib.Path(" + repr(str(started))
                  + ").touch(); time.sleep(20)")
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, start_new_session=True)
        event, errors = threading.Event(), []

        def run():
            try:
                server.run_bounded([sys.executable, "-c", parent], timeout=4, cancel=event)
            except jobs.Cancelled:
                errors.append("cancelled")

        worker = threading.Thread(target=run)
        worker.start()
        try:
            deadline = time.monotonic() + 2
            while not started.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(started.exists())
            event.set()
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, ["cancelled"])
            time.sleep(0.9)
            self.assertFalse(marker.exists())
            self.assertIsNone(unrelated.poll())
            server.run_bounded([sys.executable, "-c", child], timeout=2)
            self.assertTrue(marker.exists())
        finally:
            event.set()
            worker.join(timeout=4)
            unrelated.kill()
            unrelated.wait(timeout=3)

    def test_group_signal_requires_live_session_and_group_rebind(self):
        with patch.object(processes.os, "getsid", return_value=10), \
                patch.object(processes.os, "getpgid", return_value=20), \
                patch.object(processes.os, "killpg") as kill:
            processes.kill_group(10, 20, [30])
            kill.assert_called_once_with(20, signal.SIGKILL)
        for sessions, actual_group in [([99], 20), ([10, 99], 20), ([10], 99)]:
            with patch.object(processes.os, "getsid", side_effect=sessions), \
                    patch.object(processes.os, "getpgid", return_value=actual_group), \
                    patch.object(processes.os, "killpg") as kill:
                processes.kill_group(10, 20, [30])
                kill.assert_not_called()


class PreviewTests(Fixture):
    def clean_report(self, text):
        report = self.home / ".config/mole/clean-list.txt"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(text)
        return report

    def test_clean_preview_accepts_only_fresh_complete_report_and_exact_dryrun(self):
        candidate = self.home / "Library/Caches/Fixture"
        calls = []
        self.clean_report(preview_text(self.home / "stale"))

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            self.clean_report(preview_text(candidate, "3 KB, counted under " + str(self.home / "Library/Caches")))
            return "\x1b[32mDry run complete\x1b[0m\n"

        self.app.runner = runner
        result = wait_job(self.app, self.app.start_job({"kind": "preview", "command": "clean"})["id"])
        self.assertEqual(result["status"], "completed")
        result = result["result"]
        self.assertTrue(result["limited"])
        self.assertEqual(result["output"], "Dry run complete\n")
        self.assertEqual(result["candidates"][0]["path"], str(candidate))
        self.assertIn("counted under", result["candidates"][0]["note"])
        self.assertIn(result["candidates"][0]["raw_line"], result["preview_report"])
        self.assertEqual(calls[0][0], [self.app.executable, "clean", "--dry-run"])
        self.assertEqual(calls[0][1]["env"]["MOLE_DRY_RUN"], "1")
        self.assertEqual(calls[0][1]["env"]["MOLE_TEST_NO_AUTH"], "1")
        self.assertNotIn("input_data", calls[0][1])
        self.assertEqual(self.app.plans, {})  # Display rows are never deletion receipts.

    def test_stale_partial_or_cancelled_preview_does_not_publish_old_candidates(self):
        stale = self.clean_report(preview_text(self.home / "stale"))
        self.app.runner = lambda *args, **kwargs: "Dry run complete\n"
        result = wait_job(self.app, self.app.start_job({"kind": "preview", "command": "clean"})["id"])
        self.assertEqual(result["result"]["candidates"], [])
        self.assertNotIn("preview_report", result["result"])
        self.assertIn("No fresh complete", result["result"]["scope_note"])

        def partial(*args, **kwargs):
            stale.write_text("# Mole Cleanup Preview - fixture\n=== Partial ===\n" + str(self.home / "partial") + "  # 3 KB\n")
            return "Dry run complete"

        self.app.runner = partial
        result = wait_job(self.app, self.app.start_job({"kind": "preview", "command": "clean"})["id"])
        self.assertEqual(result["result"]["candidates"], [])
        entered = threading.Event()

        def cancelled(*args, **kwargs):
            stale.write_text(preview_text(self.home / "cancelled"))
            entered.set()
            kwargs["cancel"].wait(3)
            return "late output"

        self.app.runner = cancelled
        key = self.app.start_job({"kind": "preview", "command": "clean"})["id"]
        self.assertTrue(entered.wait(2))
        self.app.jobs.cancel(key)
        result = wait_job(self.app, key)
        self.assertEqual(result["status"], "cancelled")
        self.assertIsNone(result["result"])

    def test_failed_preview_never_consumes_new_or_stale_shared_report(self):
        report = self.clean_report(preview_text(self.home / "stale"))
        calls = []

        def failed(argv, **kwargs):
            calls.append(argv)
            report.write_text(preview_text(self.home / "new-but-failed"))
            raise ValueError("Fixture command exited unsuccessfully")

        self.app.runner = failed
        key = self.app.start_job({"kind": "preview", "command": "clean"})["id"]
        result = wait_job(self.app, key)
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["result"])
        self.assertEqual(calls, [[self.app.executable, "clean", "--dry-run"]])
        self.assertEqual(self.app.plans, {})

    def test_preview_fails_closed_on_symlink_and_keeps_ambiguous_rows_verbatim(self):
        report = self.clean_report("")
        report.unlink()
        target = self.home / "outside"
        target.write_text("keep")
        report.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            self.app.start_job({"kind": "preview", "command": "clean"})
        self.assertEqual(target.read_text(), "keep")
        report.unlink()
        self.app.runner = lambda *args, **kwargs: self.clean_report(preview_text(
            self.home / "name  # contains delimiter")) and "Dry run complete"
        result = wait_job(self.app, self.app.start_job({"kind": "preview", "command": "clean"})["id"])
        candidate = result["result"]["candidates"][0]
        self.assertIsNone(candidate["path"])
        self.assertIsNone(candidate["size_label"])
        self.assertIn("name  # contains delimiter", candidate["raw_line"])

    def inventory(self, names):
        return [{"name": name, "uninstall_name": name.lower(), "path": "/Applications/" + name + ".app",
                 "size": "1 MB"} for name in names]

    def test_selected_app_preview_uses_fresh_exact_names_and_fixed_confirmation(self):
        calls = []
        inventory = self.inventory(["Demo"])

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return json.dumps(inventory) if "--list" in argv else "Mole dry-run kept the app.\n"

        self.app.runner = runner
        with patch.dict(os.environ, {"MOLE_DELETE_MODE": "permanent"}):
            result = wait_job(self.app, self.app.start_job(
                {"kind": "preview", "command": "uninstall", "apps": ["demo"]})["id"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(calls[0][0], [self.app.executable, "uninstall", "--list"])
        self.assertEqual(calls[1][0], [self.app.executable, "uninstall", "--dry-run", "Demo"])
        self.assertEqual(calls[1][1]["input_data"], b"y\n")
        self.assertEqual(calls[1][1]["env"]["MOLE_DELETE_MODE"], "trash")
        self.assertEqual(calls[1][1]["env"]["MOLE_DRY_RUN"], "1")
        self.assertEqual(calls[1][1]["env"]["MOLE_TEST_NO_AUTH"], "1")
        self.assertEqual(result["result"]["candidates"], [])
        self.assertIn("text", result["result"]["scope_note"])

    def test_selected_app_preview_rejects_substrings_alias_duplicates_and_bundle_collisions(self):
        cases = [(self.inventory(["Demo"]), ["Dem"]),
                 (self.inventory(["Demo"]), ["Demo", "demo"]),
                 ([{"name": "Foo", "uninstall_name": "foo", "path": "/Applications/Other.app"},
                   {"name": "Different", "uninstall_name": "different", "path": "/Applications/Foo.app"}], ["Foo"])]
        for inventory, names in cases:
            calls = []
            self.app.runner = lambda argv, value=inventory, **kwargs: calls.append(argv) or json.dumps(value)
            result = wait_job(self.app, self.app.start_job(
                {"kind": "preview", "command": "uninstall", "apps": names})["id"])
            with self.subTest(names=names):
                self.assertEqual(result["status"], "failed")
                self.assertIsNone(result["result"])
                self.assertEqual(len(calls), 1)

    def test_exact_multiple_app_names_keep_each_selected_app_when_combined_app_exists(self):
        inventory = self.inventory(["Foo", "Bar", "Foo Bar"])
        calls = []

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return json.dumps(inventory) if "--list" in argv else "Previewed Foo and Bar."

        self.app.runner = runner
        key = self.app.start_job({"kind": "preview", "command": "uninstall", "apps": ["Foo", "Bar"]})["id"]
        result = wait_job(self.app, key)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(calls[-1][0], [self.app.executable, "uninstall", "--dry-run", "Foo", "Bar"])
        self.assertEqual(calls[-1][1]["input_data"], b"y\n")


class NativeTests(Fixture):
    def test_native_actions_use_only_fixed_argv_and_supported_regular_files(self):
        pdf = self.file("report.pdf", "synthetic PDF fixture")
        row = self.row(pdf)
        trash = self.home / ".Trash"
        trash.mkdir()
        calls = []
        options = []
        self.app.runner = lambda argv, **kwargs: options.append(kwargs) or calls.append(argv) or ""
        with patch.object(server.platform, "system", return_value="Darwin"), \
                patch.dict(os.environ, {"MOLE_TEST_NO_AUTH": "0", "MOLE_TEST_MODE": "0"}):
            self.app.file_action({"action": "preview", "id": row["id"]})
            self.app.file_action({"action": "reveal", "id": row["id"]})
            self.app.file_action({"action": "trash"})
        self.assertEqual(calls, [["/usr/bin/open", "-b", "com.apple.Preview", str(pdf)],
                                 ["/usr/bin/open", "-R", str(pdf)],
                                 ["/usr/bin/open", "-b", "com.apple.finder", str(trash)]])
        self.assertTrue(all(values["owned"] is False for values in options))
        self.assertTrue(pdf.exists())

    def test_native_actions_refuse_executables_stale_and_symlink_selections(self):
        html = self.file("index.html", "<h1>fixture</h1>")
        row = self.row(html)
        for data in [{"action": []}, {"action": "shell"}, {"action": "trash", "id": row["id"]},
                     {"action": "reveal", "id": []}, {"action": "preview", "id": row["id"]}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.app.file_action(data)
        pdf = self.file("file.pdf")
        row = self.row(pdf)
        pdf.rename(self.downloads / "Original")
        pdf.symlink_to(self.downloads / "Original")
        with self.assertRaises(ValueError):
            self.app.file_action({"action": "preview", "id": row["id"]})
        self.assertEqual(self.calls, [])

    def test_native_actions_are_disabled_in_test_mode_and_uninstall_handoff_binds_mode(self):
        pdf = self.file("file.pdf")
        row = self.row(pdf)
        with patch.object(server.platform, "system", return_value="Darwin"), \
                patch.dict(os.environ, {"MOLE_TEST_NO_AUTH": "1"}):
            with self.assertRaisesRegex(ValueError, "disabled"):
                self.app.file_action({"action": "preview", "id": row["id"]})
        self.app.runner = lambda *args, **kwargs: ""
        with patch.object(server.platform, "system", return_value="Darwin"), \
                patch.dict(os.environ, {"MOLE_TEST_NO_AUTH": "0", "MOLE_TEST_MODE": "0", "MOLE_DELETE_MODE": "permanent"}):
            self.app.launch({"command": "uninstall", "flags": ["dry-run"]})
            self.assertIn("export MOLE_DELETE_MODE=trash\n", self.app.terminal_files[-1].read_text())
            self.app.launch({"command": "uninstall", "flags": ["permanent"]})
            self.assertIn("export MOLE_DELETE_MODE=permanent\n", self.app.terminal_files[-1].read_text())


class JobHttpTests(HttpFixture):
    def test_all_new_routes_reject_cross_origin_and_invalid_tokens(self):
        self.app.runner = lambda *args, **kwargs: "{}"
        routes = [("GET", "/api/jobs", None), ("GET", "/api/jobs/unknown", None),
                  ("POST", "/api/jobs", {"kind": "report", "report": "status"}),
                  ("POST", "/api/jobs/unknown/cancel", {}),
                  ("POST", "/api/file-action", {"action": "trash"})]
        for method, route, data in routes:
            for headers, status in [({"Origin": "https://outside.example"}, 403),
                                    ({"X-Mole-Token": "invalid"}, 401)]:
                with self.subTest(route=route, headers=headers):
                    self.assertEqual(self.request(method, route, data=data, headers=headers)[0], status)

    def test_jobs_poll_recovery_and_cancel_bypass_held_work_lock(self):
        entered = threading.Event()

        def runner(*args, **kwargs):
            entered.set()
            kwargs["cancel"].wait(3)
            raise jobs.Cancelled("cancelled")

        self.app.runner = runner
        status, _, response = self.request("POST", "/api/jobs", data={"kind": "report", "report": "status"})
        self.assertEqual(status, 200)
        key = response["id"]
        self.assertTrue(entered.wait(2))
        self.assertTrue(self.app.lock.locked())
        status, _, active = self.request("GET", "/api/jobs")
        self.assertEqual(status, 200)
        self.assertEqual(active["active"]["request"], {"kind": "report", "report": "status"})
        self.assertEqual(self.request("GET", "/api/jobs/" + key)[0], 200)
        self.assertEqual(self.request("POST", "/api/jobs", data={"kind": "report", "report": "status"})[0], 409)
        self.assertEqual(self.request("POST", "/api/jobs/" + key + "/cancel", data={})[0], 200)
        self.assertEqual(wait_job(self.app, key)["status"], "cancelled")
        self.assertIsNone(self.request("GET", "/api/jobs")[2]["active"])

    def test_invalid_new_route_bodies_and_unknown_jobs_have_bounded_errors(self):
        for route, data in [("/api/jobs", {"kind": []}), ("/api/jobs", {"kind": "analyze", "path": []}),
                            ("/api/file-action", {"action": []}), ("/api/file-action", {"action": "reveal", "id": []})]:
            with self.subTest(route=route, data=data):
                self.assertEqual(self.request("POST", route, data=data)[0], 400)
        self.assertEqual(self.request("GET", "/api/jobs/missing")[0], 404)
        self.assertEqual(self.request("POST", "/api/jobs/missing/cancel", data={})[0], 404)
        self.assertEqual(self.request("POST", "/api/jobs/missing/cancel", data={"argv": []})[0], 400)

    def test_browse_http_filter_types_and_page_metadata(self):
        self.file("image.png", "png")
        self.file("document.txt", "text")
        query = urlencode({"path": str(self.downloads), "offset": 0, "q": "image", "type": "image",
                           "min_size": 1, "older_days": 0, "sort": "name", "order": "asc"})
        status, _, result = self.request("GET", "/api/browse?" + query)
        self.assertEqual(status, 200)
        self.assertEqual(result["total_visible"], 2)
        self.assertEqual(result["total_filtered"], 1)
        self.assertEqual(result["entries"][0]["name"], "image.png")
        for value in ["-1", "NaN", "1.5", "9" * 100]:
            self.assertEqual(self.request("GET", "/api/browse?" + urlencode(
                {"path": str(self.downloads), "offset": value}))[0], 400)


@unittest.skipUnless(platform.system() == "Darwin" and os.geteuid() != 0,
                     "The real analyzer fixture requires a regular macOS user.")
class AnalyzerIntegrationTests(Fixture):
    def test_real_analyzer_measures_only_synthetic_folder_with_no_auth(self):
        executable = self.app.executable_for("analyze")
        if executable == self.app.executable and not (server.ROOT / "bin/analyze-go").exists():
            self.skipTest("No compiled analyzer or installed mo is available")
        self.file(content="abc")
        self.app.runner = server.run_bounded
        key = self.app.start_job({"kind": "analyze", "path": str(self.downloads)})["id"]
        result = wait_job(self.app, key, timeout=20)
        self.assertEqual(result["status"], "completed", result["error"])
        self.assertEqual(result["result"]["total_size"], 3)
        self.assertEqual(result["result"]["path"], str(self.downloads))
        self.assertEqual(result["result"]["entries"][0]["size"], 3)
        self.assertTrue((self.downloads / "fixture.txt").exists())


if __name__ == "__main__":
    unittest.main()
