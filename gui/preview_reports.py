"""Read-only preview report extraction; report paths never authorize deletion."""
import os
from pathlib import Path
import re
import stat


MAX_REPORT_BYTES = 2 * 1024 * 1024
MAX_CANDIDATES = 3000


def report_path(home):
    path = home / ".config" / "mole" / "clean-list.txt"
    probe = home
    for part in path.relative_to(home).parts:
        probe = probe / part
        try:
            info = probe.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise ValueError("The cleanup preview report uses a symbolic link. Review the configuration in Terminal.")
        if probe != path and not stat.S_ISDIR(info.st_mode):
            raise ValueError("The cleanup preview report directory is unavailable.")
        if probe == path and (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()):
            raise ValueError("The cleanup preview report is not an owned regular file.")
    return path


def fingerprint(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError("The cleanup preview report could not be inspected safely.")
    parent = path.parent.stat()
    return (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns, info.st_size,
            parent.st_dev, parent.st_ino)


def fresh_report(home, before, started_ns):
    path = report_path(home)
    after = fingerprint(path)
    if after is None or after == before or after[2] < started_ns:
        return None
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as source:
        opened = os.fstat(source.fileno())
        if (opened.st_dev, opened.st_ino, opened.st_mtime_ns, opened.st_ctime_ns, opened.st_size) != after[:5]:
            return None
        if not stat.S_ISREG(opened.st_mode) or opened.st_size > MAX_REPORT_BYTES:
            return None
        content = source.read(MAX_REPORT_BYTES + 1)
        if len(content) > MAX_REPORT_BYTES or fingerprint(path) != after:
            return None
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    lines = text.splitlines()
    if (not text.endswith("\n") or not lines or not lines[0].startswith("# Mole Cleanup Preview - ")
            or "# Summary" not in lines or len(lines) < 3
            or re.fullmatch(r"# Items: [0-9]+", lines[-2]) is None
            or re.fullmatch(r"# Categories: [0-9]+", lines[-1]) is None):
        return None
    candidates, section = [], ""
    for line in lines:
        if line.startswith("=== ") and line.endswith(" ==="):
            section = line[4:-4]
            continue
        if not line.startswith("/") or "  # " not in line:
            continue
        # Keep every original line. Ambiguous display delimiters are not turned
        # into invented exact paths or byte counts.
        if line.count("  # ") != 1:
            candidates.append({"path": None, "section": section, "size_label": None,
                               "note": "See the original preview line.", "raw_line": line})
        else:
            raw_path, annotation = line.split("  # ", 1)
            size_label, _, note = annotation.partition(", ")
            if (len(raw_path) > 4096 or any(ord(c) < 32 for c in raw_path)
                    or not (size_label == "size unknown" or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?\s*[KMGTPE]?B", size_label))):
                candidates.append({"path": None, "section": section, "size_label": None,
                                   "note": "See the original preview line.", "raw_line": line})
            else:
                candidates.append({"path": raw_path, "section": section, "size_label": size_label,
                                   "note": note, "raw_line": line})
        if len(candidates) >= MAX_CANDIDATES:
            break
    return {"candidates": candidates, "preview_report": text, "report_path": str(path),
            "candidates_truncated": len(candidates) == MAX_CANDIDATES}
