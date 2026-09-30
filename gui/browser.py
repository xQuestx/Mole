"""Fresh, bounded metadata listings. Folder sizes are never guessed or cached."""
import os
from pathlib import Path
import secrets
import stat
import time


PAGE_SIZE = 200
SCAN_BUDGET = 4
MAX_ENTRIES = 20000
MAX_RECEIPTS = 5000
PREVIEW_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".heif",
                      ".tif", ".tiff", ".bmp", ".pdf"}
FILE_TYPES = {
    "image": PREVIEW_EXTENSIONS - {".pdf"} | {".svg", ".avif"},
    "video": {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm"},
    "audio": {".mp3", ".m4a", ".aac", ".wav", ".aiff", ".flac", ".ogg"},
    "archive": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"},
    "installer": {".dmg", ".pkg", ".mpkg", ".iso", ".xip"},
    "document": {".pdf", ".txt", ".md", ".rtf", ".doc", ".docx", ".pages",
                 ".xls", ".xlsx", ".csv", ".numbers", ".ppt", ".pptx", ".key"},
}


def options(query):
    allowed = {"path", "offset", "q", "type", "min_size", "older_days", "sort", "order"}
    if set(query) - allowed or any(len(values) != 1 for values in query.values()):
        raise ValueError("Choose one folder and one value for each filter.")
    result = {key: values[0] for key, values in query.items() if key != "path"}
    for key in ("offset", "min_size", "older_days"):
        if key in result:
            value = result[key]
            if not value.isascii() or not value.isdigit() or len(value) > 18:
                raise ValueError("Folder offsets and numeric filters must be nonnegative integers.")
            result[key] = int(value)
    return result


def browse(app, raw, *, offset=0, q="", type="all", min_size=0, older_days=0, sort="size", order="desc"):
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0
           for value in (offset, min_size, older_days)):
        raise ValueError("Folder offsets and numeric filters must be nonnegative integers.")
    if offset > MAX_ENTRIES or older_days > 365000 or min_size > 10**18:
        raise ValueError("The folder filter is outside the supported range.")
    if (not isinstance(q, str) or len(q) > 256 or any(ord(c) < 32 for c in q)
            or not isinstance(type, str) or type not in {"all", "file", "folder", *FILE_TYPES}
            or not isinstance(sort, str) or sort not in {"name", "size", "modified"}
            or not isinstance(order, str) or order not in {"asc", "desc"}):
        raise ValueError("Choose a supported folder filter and sort order.")
    path = app.browse_path(raw)
    now = time.monotonic()
    sampled_at = time.time()
    folder = path.stat()
    app.entries = {key: entry for key, entry in app.entries.items()
                   if now - entry["time"] < app.selection_ttl}
    rows, partial, visited = [], False, 0
    with os.scandir(path) as children:
        for child in children:
            visited += 1
            if visited > MAX_ENTRIES or time.monotonic() - now > SCAN_BUDGET:
                partial = True
                break
            if child.name.startswith("."):
                continue
            try:
                info = child.stat(follow_symlinks=False)
            except OSError:
                partial = True
                continue
            item = Path(child.path)
            regular, directory = stat.S_ISREG(info.st_mode), stat.S_ISDIR(info.st_mode)
            link = stat.S_ISLNK(info.st_mode)
            rows.append({"name": child.name, "path": str(item), "directory": directory, "symlink": link,
                         "size": info.st_size if regular else None, "modified": info.st_mtime,
                         "_identity": (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size,
                                       folder.st_dev, folder.st_ino)})
    # A replacement or alias introduced during listing must never inherit the
    # old directory's discovery receipts. An ordinary directory change is partial.
    rebound = app.browse_path(str(path)).stat()
    if (folder.st_dev, folder.st_ino) != (rebound.st_dev, rebound.st_ino):
        raise ValueError("The folder changed. Refresh its listing.")
    if folder.st_mtime_ns != rebound.st_mtime_ns:
        partial = True
    total_visible = len(rows)
    folded = q.casefold()
    cutoff = sampled_at - older_days * 86400

    def matches(row):
        if folded not in row["name"].casefold():
            return False
        regular = row["size"] is not None and not row["symlink"]
        if type == "folder" and not row["directory"]:
            return False
        if type == "file" and not regular:
            return False
        if type in FILE_TYPES and (not regular or Path(row["name"]).suffix.casefold() not in FILE_TYPES[type]):
            return False
        if min_size and (row["size"] is None or row["size"] < min_size):
            return False
        if older_days and row["modified"] > cutoff:
            return False
        return True

    filtered = [row for row in rows if matches(row)]
    filtered.sort(key=lambda row: ((row["name"].casefold() if sort == "name"
                                   else (row[sort] if row[sort] is not None else -1)),
                                  row["name"].casefold()), reverse=order == "desc")
    filtered.sort(key=lambda row: not row["directory"])
    page = filtered[offset:offset + PAGE_SIZE]
    for row in page:
        item = Path(row["path"])
        key = secrets.token_urlsafe(18)
        app.entries[key] = {"path": item, "identity": row.pop("_identity"), "time": now}
        row["id"] = key
        row["eligible"] = app.eligible(item)
        row["previewable"] = row["size"] is not None and not row["symlink"] and item.suffix.casefold() in PREVIEW_EXTENSIONS
        row["revealable"] = not row["symlink"]
    app.entries = dict(list(app.entries.items())[-MAX_RECEIPTS:])
    return {"path": str(path), "parent": str(path.parent) if path != app.home else None,
            "entries": page, "partial": partial, "offset": offset,
            "next_offset": offset + PAGE_SIZE if not partial and offset + PAGE_SIZE < len(filtered) else None,
            "total_visible": None if partial else total_visible,
            "total_filtered": None if partial else len(filtered),
            "observed_visible": total_visible, "observed_filtered": len(filtered),
            "sampled_at": sampled_at}
