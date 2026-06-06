"""The pluggable analyzer seam. A `LanguageAnalyzer` walks a configured repo and returns a
deterministic `RepoIndex`. Adding a language = implementing this protocol + registering it; nothing
else in the tool knows about Python specifically."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from repo_manual.config import ManualConfig
from repo_manual.model import RepoIndex


class LanguageAnalyzer(Protocol):
    """Static analysis for one language. Implementations must be pure & deterministic: same bytes in,
    same `RepoIndex` out (stable ordering), so the committed index and freshness hashes are stable."""

    language: str
    file_suffixes: tuple[str, ...]

    def analyze(self, config: ManualConfig) -> RepoIndex: ...


def iter_source_files(config: ManualConfig, suffixes: tuple[str, ...]) -> list[Path]:
    """Walk ``config.source_dirs`` (or the repo root) yielding files with a matching suffix, honoring
    ``excludes`` and the ``include_tests`` switch. Returns repo-absolute paths, sorted for determinism."""
    excludes = set(config.excludes)
    roots = [config.root / d for d in config.source_dirs] or [config.root]
    found: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # prune excluded directories in place so os.walk doesn't descend into them
            dirnames[:] = sorted(d for d in dirnames if d not in excludes)
            rel_dir = Path(dirpath).relative_to(config.root)
            if not config.include_tests and _is_test_path(rel_dir):
                continue
            for name in sorted(filenames):
                if not name.endswith(suffixes):
                    continue
                if not config.include_tests and _is_test_path(Path(name)):
                    continue
                found.append(Path(dirpath) / name)
    return sorted(found)


def _is_test_path(rel: Path) -> bool:
    parts = {p.lower() for p in rel.parts}
    if {"tests", "test"} & parts:
        return True
    return rel.name.startswith("test_") or rel.name.endswith("_test.py")


def get_analyzer(language: str) -> LanguageAnalyzer:
    """Return the analyzer for ``language`` (currently just Python). Raises on unknown languages."""
    if language == "python":
        from repo_manual.scan.python import PythonAnalyzer

        return PythonAnalyzer()
    raise ValueError(f"no analyzer registered for language {language!r} (supported: python)")
