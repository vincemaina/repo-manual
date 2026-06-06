"""Content hashing for freshness. One short, stable helper used by the analyzer (to stamp each
``SourceFile``) and by freshness (to detect drift). Format: ``sha256:<hex>`` over the file bytes."""

from __future__ import annotations

import hashlib
from pathlib import Path

ALGO = "sha256"


def hash_bytes(data: bytes) -> str:
    return f"{ALGO}:{hashlib.sha256(data).hexdigest()}"


def hash_text(text: str) -> str:
    return hash_bytes(text.encode("utf-8"))


def hash_file(path: Path) -> str:
    return hash_bytes(path.read_bytes())
