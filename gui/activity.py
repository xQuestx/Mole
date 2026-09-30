"""Bounded plain-text activity from reported preview output, never a file plan."""
import codecs
from collections import deque
import json
import threading


MAX_LINES = 120
MAX_LINE_CHARS = 1000
MAX_TEXT_PAYLOAD = 64 * 1024


class Tail:
    def __init__(self):
        self.lock = threading.Lock()
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.lines = deque()
        self.stored_size = 0
        self.current = ""
        self.line_open = False
        self.carriage = False
        self.escape = "text"
        self.total_lines = 0
        self.truncated = False
        self.finished = False

    @staticmethod
    def encoded_size(line):
        # Count the JSON representation used by the HTTP serializer, including
        # non-ASCII escaping. Character limits alone do not bound its payload.
        return len(json.dumps(line)) + 2

    def trim(self):
        current_size = self.encoded_size(self.current) if self.line_open else 0
        current_lines = 1 if self.line_open else 0
        while self.lines and (len(self.lines) + current_lines > MAX_LINES
                              or self.stored_size + current_size > MAX_TEXT_PAYLOAD):
            _line, size = self.lines.popleft()
            self.stored_size -= size
            self.truncated = True

    def consume(self, text):
        for char in text:
            if self.escape == "escape":
                self.escape = {"[": "csi", "]": "osc"}.get(char, "text")
                continue
            if self.escape == "csi":
                if "@" <= char <= "~":
                    self.escape = "text"
                continue
            if self.escape == "osc":
                if char in ("\x07", "\x9c"):
                    self.escape = "text"
                elif char == "\x1b":
                    self.escape = "osc_escape"
                continue
            if self.escape == "osc_escape":
                if char in ("\\", "\x07", "\x9c"):
                    self.escape = "text"
                elif char != "\x1b":
                    self.escape = "osc"
                continue
            if char in ("\x1b", "\x9b", "\x9d"):
                self.escape = {"\x1b": "escape", "\x9b": "csi", "\x9d": "osc"}[char]
                continue
            if char == "\r":
                self.carriage = True
                continue
            if char == "\n":
                if not self.line_open:
                    self.total_lines += 1
                size = self.encoded_size(self.current)
                self.lines.append((self.current, size))
                self.stored_size += size
                self.current = ""
                self.line_open = False
                self.carriage = False
                self.trim()
                continue
            if char != "\t" and (ord(char) < 32 or 127 <= ord(char) <= 159):
                continue
            if self.carriage:
                self.current = ""
                self.carriage = False
            if not self.line_open:
                self.total_lines += 1
                self.line_open = True
            if len(self.current) < MAX_LINE_CHARS:
                self.current += char
            else:
                self.truncated = True
        self.trim()

    def feed(self, data):
        with self.lock:
            if not self.finished:
                self.consume(self.decoder.decode(data))

    def finish(self):
        with self.lock:
            if not self.finished:
                self.consume(self.decoder.decode(b"", final=True))
                self.finished = True

    def snapshot(self):
        with self.lock:
            lines = [line for line, _size in self.lines]
            if self.line_open:
                lines.append(self.current)
            return {"lines": lines, "total_lines": self.total_lines, "truncated": self.truncated}
