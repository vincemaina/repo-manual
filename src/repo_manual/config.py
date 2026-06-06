"""``ManualConfig`` — the small, committed ``.repo-manual/manual.config.json`` that pins where the
manual lives and what to scan. Kept deliberately tiny; defaults work for a ``src/`` layout repo."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "manual.config.json"
DEFAULT_OUTPUT = ".repo-manual"
DEFAULT_EXCLUDES = (
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".repo-manual",
    "node_modules",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
)


@dataclass
class ManualConfig:
    """Resolved config. ``root`` is the absolute repo root; the rest is what lands in the JSON file."""

    root: Path
    language: str = "python"
    source_dirs: list[str] = field(default_factory=lambda: ["src"])
    output_dir: str = DEFAULT_OUTPUT
    excludes: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    include_tests: bool = False

    @property
    def output_path(self) -> Path:
        return self.root / self.output_dir

    def to_dict(self) -> dict:
        # `root` is implied by the file's location, so it is not serialized.
        return {
            "language": self.language,
            "source_dirs": list(self.source_dirs),
            "output_dir": self.output_dir,
            "excludes": list(self.excludes),
            "include_tests": self.include_tests,
        }

    @classmethod
    def from_dict(cls, root: Path, d: dict) -> ManualConfig:
        return cls(
            root=root,
            language=d.get("language", "python"),
            source_dirs=list(d.get("source_dirs", ["src"])),
            output_dir=d.get("output_dir", DEFAULT_OUTPUT),
            excludes=list(d.get("excludes", DEFAULT_EXCLUDES)),
            include_tests=d.get("include_tests", False),
        )

    @classmethod
    def load(cls, root: Path) -> ManualConfig:
        """Load ``<root>/<output>/manual.config.json`` if present, else return defaults."""
        # The config can live at the repo root's default output dir; try the conventional spot.
        candidate = root / DEFAULT_OUTPUT / CONFIG_NAME
        if candidate.exists():
            return cls.from_dict(root, json.loads(candidate.read_text()))
        return cls(root=root)

    def save(self) -> Path:
        path = self.output_path / CONFIG_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n")
        return path
