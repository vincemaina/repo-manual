"""Shared fixtures: a tiny synthetic ``src/`` repo we can analyze deterministically."""

from __future__ import annotations

from pathlib import Path

import pytest

from repo_manual.config import ManualConfig

PKG = "sample"

A_PY = '''\
"""Module a: a leaf helper."""


def helper(x):
    """Return x doubled."""
    return x * 2


class Thing:
    """A small thing."""

    def run(self, n):
        """Run it."""
        return helper(n)
'''

B_PY = '''\
"""Module b: depends on a."""

from sample.a import Thing, helper


def process(items):
    """Process items using helper."""
    t = Thing()
    return [helper(i) + t.run(i) for i in items]
'''

CLI_PY = '''\
"""The CLI entry point."""

from sample.b import process


def main():
    """Entry."""
    return process([1, 2, 3])
'''


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    pkg = tmp_path / "src" / PKG
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('"""The sample package."""\n')
    (pkg / "a.py").write_text(A_PY)
    (pkg / "b.py").write_text(B_PY)
    (pkg / "cli.py").write_text(CLI_PY)
    return tmp_path


@pytest.fixture
def config(sample_repo: Path) -> ManualConfig:
    return ManualConfig(root=sample_repo, source_dirs=["src"])
