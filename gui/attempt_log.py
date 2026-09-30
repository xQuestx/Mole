"""Verify GUI attempt records in Mole's existing logs, without moving files."""
import json
import os
from pathlib import Path
import stat
import sys


LIMIT = 2 * 1024 * 1024


def open_log(path):
    descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        os.close(descriptor)
        raise ValueError("The Mole log is not an owned regular file.")
    return os.fdopen(descriptor, "r+b")


def capture(path):
    try:
        with open_log(path) as source:
            info = os.fstat(source.fileno())
            return [info.st_dev, info.st_ino, info.st_size]
    except FileNotFoundError:
        return None


def persist_pending(path, target, token):
    with open_log(path) as source:
        source.seek(max(0, os.fstat(source.fileno()).st_size - LIMIT))
        lines = source.read(LIMIT + 1).decode("utf-8").splitlines()
        suffix = f" [analyze] TRASH_ATTEMPT {target} (GUI {token}; outcome pending)"
        if not any(line.endswith(suffix) for line in lines):
            raise ValueError("The GUI attempt record could not be verified in Mole's operation log.")
        os.fsync(source.fileno())


def confirmed(path, before, target):
    with open_log(path) as source:
        info = os.fstat(source.fileno())
        if before is not None and [info.st_dev, info.st_ino] != before[:2]:
            raise ValueError("The Mole deletion log changed during the attempt.")
        offset = before[2] if before is not None else 0
        if info.st_size < offset or info.st_size - offset > LIMIT:
            raise ValueError("The Mole deletion evidence is incomplete.")
        source.seek(offset)
        data = source.read(LIMIT + 1)
        if not data.endswith(b"\n"):
            raise ValueError("The Mole deletion evidence is incomplete.")
        match = False
        for line in data.decode("utf-8").splitlines():
            fields = line.split("\t", 4)
            if len(fields) == 5 and fields[1] == "trash" and fields[3] == "ok" and fields[4] == target:
                match = True
        if not match:
            raise ValueError("No fresh successful Mole Trash record exists for this reviewed path.")
        os.fsync(source.fileno())


def sync(path):
    with open_log(path) as source:
        os.fsync(source.fileno())


def main():
    try:
        args = sys.argv[1:]
        if len(args) == 2 and args[0] == "capture":
            print(json.dumps(capture(Path(args[1]))))
        elif len(args) == 4 and args[0] == "pending":
            persist_pending(Path(args[1]), args[2], args[3])
        elif len(args) == 4 and args[0] == "confirmed":
            confirmed(Path(args[1]), json.loads(args[2]), args[3])
        elif len(args) == 2 and args[0] == "sync":
            sync(Path(args[1]))
        else:
            raise ValueError("Invalid Mole log verification request.")
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
