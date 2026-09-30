"""Stop only process groups proven to belong to a GUI-created session."""
import os
import re
import signal


def members(output, session):
    groups = {}
    for line in output.splitlines():
        match = re.fullmatch(r"\s*([1-9][0-9]*)\s+([1-9][0-9]*)\s*", line)
        if match is None:
            continue
        pid, group = map(int, match.groups())
        try:
            if os.getsid(pid) == session and os.getpgid(pid) == group:
                groups.setdefault(group, []).append(pid)
        except OSError:
            continue  # Vanished or unreadable processes are not kill authority.
    return groups


def kill_group(session, group, candidates):
    for pid in candidates:
        try:
            # Rebind both facts at the signal boundary. Process names, ancestor
            # heuristics, and a previously cached PID never authorize a signal.
            if (os.getsid(pid) == session and os.getpgid(pid) == group
                    and os.getsid(pid) == session):
                os.killpg(group, signal.SIGKILL)
                return
        except OSError:
            continue


def stop_session(process, enumerate_processes):
    session = process.pid  # Popen starts this process in a fresh session.
    for _ in range(2):
        try:
            groups = members(enumerate_processes(), session)
        except (ValueError, OSError):
            groups = {}
        # Stop the leader group first so it cannot dispatch another probe.
        # The next bounded enumeration catches groups created during the first.
        kill_group(session, session, [process.pid] + groups.pop(session, []))
        for group, candidates in groups.items():
            kill_group(session, group, candidates)
