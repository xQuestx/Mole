"""Exercise the macOS launcher with fake Python runtimes; never start a GUI."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


LAUNCHER = Path(__file__).with_name("Mole GUI.command")
COMMON_PYTHONS = (
    "/opt/homebrew/bin/python3",
    "/usr/local/bin/python3",
    "/Library/Frameworks/Python.framework/Versions/Current/bin/python3",
    "/usr/bin/python3",
)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mole-launcher-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.gui = self.root / "Mole checkout with spaces" / "gui"
        self.gui.mkdir(parents=True)
        self.launcher = self.gui / LAUNCHER.name
        self.server = self.gui / "server.py"
        self.server.write_text("# Fixture only; fake Python never executes this file.\n")
        self.bin = self.root / "runtime bin"
        self.bin.mkdir()
        self.common = [self.root / f"common runtime {index}" for index in range(4)]
        self.log = self.root / "launch.argv"
        self.probes = self.root / "probes.log"
        self.label = self.root / "runtime.log"
        self.pid = self.root / "pid.log"
        self.hung_pid = self.root / "hung.pid"
        self.hung_child = self.root / "hung-child.pid"

        source = LAUNCHER.read_text()
        # Map only external runtime locations and uid to the fixture. This keeps
        # failure tests hermetic even on a Mac with several Python installs or
        # under a root CI runner; the launcher exposes no production test switch.
        guard = '[[ "$EUID" -eq 0 ]]'
        self.assertEqual(source.count(guard), 1)
        source = source.replace(guard, '[[ "${LAUNCH_TEST_UID:-501}" -eq 0 ]]')
        for real, fixture in zip(COMMON_PYTHONS, self.common):
            self.assertEqual(source.count(f'"{real}"'), 1)
            source = source.replace(f'"{real}"', f'"{fixture}"')
        self.launcher.write_text(source)
        self.launcher.chmod(0o755)

        self.env = os.environ.copy()
        self.env.update({
            "PATH": str(self.bin),
            "LAUNCH_LOG": str(self.log),
            "PROBE_LOG": str(self.probes),
            "RUNTIME_LOG": str(self.label),
            "PID_LOG": str(self.pid),
            "TEST_REAL_PYTHON": sys.executable,
            "HUNG_PID_LOG": str(self.hung_pid),
            "HUNG_CHILD_LOG": str(self.hung_child),
            "LAUNCH_TEST_UID": "501",
        })
        self.env.pop("BASH_ENV", None)
        self.env.pop("ENV", None)

    def fake_python(self, path=None, *, name="python3", supported=True, run_status=0):
        path = path or self.bin / name
        path.write_text(
            "#!/bin/bash\n"
            "if [[ \"$1\" == '-I' && \"$2\" == '-c' ]]; then\n"
            f"    printf '%s\\n' '{name}' >> \"$PROBE_LOG\"\n"
            f"    exec \"$TEST_REAL_PYTHON\" -I -c 'import sys; sys.version_info = {repr((3, 10) if supported else (3, 9))}; exec(sys.argv[1])' \"$3\"\n"
            "fi\n"
            "printf '%s\\0' \"$@\" > \"$LAUNCH_LOG\"\n"
            f"printf '%s\\n' '{name}' > \"$RUNTIME_LOG\"\n"
            "printf '%s\\n' \"$$\" > \"$PID_LOG\"\n"
            f"exit {run_status}\n"
        )
        path.chmod(0o755)
        return path

    def run_launcher(self, *args, path=None):
        return subprocess.run(
            ["/bin/bash", str(path or self.launcher), *args],
            cwd=self.root, env=self.env, capture_output=True, text=True, timeout=5,
        )

    def argv(self):
        return self.log.read_bytes().decode().rstrip("\0").split("\0")

    def hanging_python(self, *, early_exit=False):
        path = self.bin / "python3"
        path.write_text(
            "#!/bin/bash\n"
            "printf '%s\\n' \"$$\" > \"$HUNG_PID_LOG\"\n"
            "/bin/sleep 30 &\n"
            "printf '%s\\n' \"$!\" > \"$HUNG_CHILD_LOG\"\n"
            + ("exit 1\n" if early_exit else "wait\n")
        )
        path.chmod(0o755)

    def assert_probe_group_stopped(self):
        pid = int(self.hung_pid.read_text())
        child = int(self.hung_child.read_text())
        # Allow launchd a moment to reap the killed child after its parent exits.
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                os.killpg(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)
        with self.assertRaises(ProcessLookupError):
            os.kill(child, 0)
        with self.assertRaises(ProcessLookupError):
            os.killpg(pid, 0)

    def test_checked_in_launcher_is_executable_and_bash_compatible(self):
        self.assertTrue(os.access(LAUNCHER, os.X_OK))
        self.assertEqual(LAUNCHER.read_text().splitlines()[0], "#!/bin/bash")
        checked = subprocess.run(
            ["/bin/bash", "-n", str(LAUNCHER)], capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_paths_with_spaces_and_arguments_reach_python_unchanged(self):
        self.fake_python()
        result = self.run_launcher("--no-open")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.argv(), [str(self.server), "--no-open"])
        self.assertEqual(self.probes.read_text().splitlines(), ["python3"])

    def test_unsupported_path_python_yields_to_a_supported_versioned_runtime(self):
        self.fake_python(supported=False)
        self.fake_python(name="python3.11")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.label.read_text().strip(), "python3.11")
        self.assertEqual(self.probes.read_text().splitlines(), ["python3", "python3.11"])

    def test_common_mac_location_is_used_when_path_runtime_is_old(self):
        self.fake_python(supported=False)
        self.fake_python(self.common[0], name="common-python")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.label.read_text().strip(), "common-python")

    def test_no_python_gives_a_specific_cause_and_next_step(self):
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Python 3.10 or newer was not found", result.stderr)
        self.assertIn("Next: Make a supported Python available", result.stderr)
        self.assertFalse(self.log.exists())

    def test_old_runtimes_do_not_start_the_server(self):
        self.fake_python(supported=False)
        self.fake_python(self.common[1], name="old-common", supported=False)
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Python 3.10 or newer", result.stderr)
        self.assertEqual(self.probes.read_text().splitlines(), ["python3", "old-common"])
        self.assertFalse(self.log.exists())

    def test_nonexecutable_runtime_is_not_probed(self):
        runtime = self.fake_python(self.common[0])
        runtime.chmod(0o644)
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.probes.exists())

    def test_hanging_runtime_is_stopped_and_supported_fallback_launches(self):
        self.hanging_python()
        self.fake_python(self.common[0], name="common-python")
        started = time.monotonic()
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(time.monotonic() - started, 4)
        self.assertEqual(self.label.read_text().strip(), "common-python")
        self.assert_probe_group_stopped()

    def test_hanging_runtime_is_stopped_before_missing_python_refusal(self):
        self.hanging_python()
        started = time.monotonic()
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertLess(time.monotonic() - started, 4)
        self.assertIn("Python 3.10 or newer was not found", result.stderr)
        self.assertFalse(self.log.exists())
        self.assert_probe_group_stopped()

    def test_early_exiting_runtime_cannot_leave_its_child_behind(self):
        self.hanging_python(early_exit=True)
        self.fake_python(self.common[0], name="common-python")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.label.read_text().strip(), "common-python")
        self.assert_probe_group_stopped()

    def test_termination_during_probe_stops_and_reaps_the_probe_group(self):
        self.hanging_python()
        with subprocess.Popen(
            ["/bin/bash", str(self.launcher)], cwd=self.root, env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ) as process:
            deadline = time.monotonic() + 2
            while not self.hung_child.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(self.hung_child.exists(), "Probe child did not start")
            process.send_signal(signal.SIGTERM)
            process.communicate(timeout=3)
            self.assertEqual(process.returncode, 143)
        self.assertFalse(self.log.exists())
        self.assert_probe_group_stopped()

    def test_root_is_rejected_before_any_runtime_probe(self):
        self.fake_python()
        self.env["LAUNCH_TEST_UID"] = "0"
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Run as your regular Mac user", result.stderr)
        self.assertIn("Next: Open this file without sudo", result.stderr)
        self.assertFalse(self.probes.exists())
        self.assertFalse(self.log.exists())

    def test_missing_server_is_reported_before_runtime_selection(self):
        self.fake_python()
        self.server.unlink()
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn("server.py is missing beside this launcher", result.stderr)
        self.assertIn("Next: Keep this file", result.stderr)
        self.assertFalse(self.probes.exists())

    def test_relative_symlink_resolves_to_the_original_gui_folder(self):
        self.fake_python()
        link = self.root / "Open Mole.command"
        link.symlink_to(self.launcher.relative_to(self.root))
        result = self.run_launcher(path=link)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.argv(), [str(self.server)])

    def test_server_exit_status_and_foreground_pid_are_preserved(self):
        self.fake_python(run_status=7)
        with subprocess.Popen(
            ["/bin/bash", str(self.launcher)], cwd=self.root, env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ) as process:
            _, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 7, stderr)
            self.assertEqual(int(self.pid.read_text()), process.pid)


if __name__ == "__main__":
    unittest.main()
