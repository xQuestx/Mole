"""Validate measured Mole JSON without computing or caching directory sizes."""
from pathlib import Path
import time


STATES = {"complete", "partial", "unavailable"}


def nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def normalized(data, requested, home):
    if (not isinstance(data, dict) or data.get("path") != str(requested)
            or not isinstance(data.get("scan_status"), str) or data["scan_status"] not in STATES
            or not nonnegative_integer(data.get("total_size")) or not isinstance(data.get("entries"), list)
            or data.get("overview") not in (False, None)):
        raise ValueError("Mole did not return a measured report for the selected folder.")
    for entry in data["entries"]:
        if (not isinstance(entry, dict) or not isinstance(entry.get("path"), str)
                or not isinstance(entry.get("name"), str) or not nonnegative_integer(entry.get("size"))
                or not isinstance(entry.get("is_dir"), bool)
                or not isinstance(entry.get("scan_status"), str) or entry["scan_status"] not in STATES):
            raise ValueError("Mole returned an incomplete folder entry.")
        path = Path(entry["path"])
        if (not path.is_absolute() or ".." in path.parts or path.parent != requested
                or not path.is_relative_to(home) or path.name != entry["name"]):
            raise ValueError("The folder report includes a path outside the requested scope.")
    if "total_files" in data and not nonnegative_integer(data["total_files"]):
        raise ValueError("Mole returned an invalid file count.")
    large_files = data.get("large_files", [])
    if not isinstance(large_files, list):
        raise ValueError("Mole returned an incomplete large-file list.")
    for entry in large_files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not nonnegative_integer(entry.get("size")):
            raise ValueError("Mole returned an incomplete large-file entry.")
        path = Path(entry["path"])
        if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(requested):
            raise ValueError("The large-file report includes an unexpected path.")
    result = dict(data)
    result["sampled_at"] = time.time()
    return result
