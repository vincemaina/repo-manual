"""Citation validation — the trust gate. The narrative's whole credibility rests on the recipe's rule:
*every claim cites its source*. This module checks, deterministically and with no LLM, that those
citations are real — the cited files exist and the cited line ranges are in bounds — and (in strict
mode) that a narrated page cites enough sources to be grounded at all.

It catches the failure mode that sinks AI doc tools: confident prose with fabricated or drifted line
references. Two citation forms are recognised:

* ``Sources: [path/to/file.py:start-end]()`` — the canonical claim citation (existence + line range), and
* relative source links like ``](../../../src/pkg/mod.py)`` — checked for existence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from repo_manual import store
from repo_manual.config import ManualConfig
from repo_manual.model import Manual, PageSource

# [path.ext:123-456]  — a source path (has an extension) followed by a line range
_RANGE_RE = re.compile(r"\[([^\]\s|]+\.[A-Za-z0-9_]+):(\d+)-(\d+)\]")
# ](relative/or/../path.ext)  or with a #Lxx anchor — a markdown link to a source file
_LINK_RE = re.compile(r"\]\((\.{1,2}/[^)\s]+?\.[A-Za-z0-9_]+)(?:#[^)]*)?\)")
_SOURCE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".sql", ".go", ".rs", ".java")

STRICT_MIN_SOURCES = 2  # the recipe suggests more; this is a floor that fits small modules


@dataclass
class Violation:
    page_id: str
    message: str


@dataclass
class VerifyReport:
    pages_checked: int = 0
    citations_checked: int = 0
    violations: list[Violation] = field(default_factory=list)
    thin_pages: list[str] = field(default_factory=list)

    @property
    def has_problems(self) -> bool:
        return bool(self.violations) or bool(self.thin_pages)

    def format_lines(self) -> list[str]:
        lines = [
            f"verified {self.pages_checked} narrated page(s), {self.citations_checked} citation(s)"
        ]
        for v in self.violations:
            lines.append(f"  ✗ {v.page_id}: {v.message}")
        for pid in self.thin_pages:
            lines.append(f"  ⚠ {pid}: cites < {STRICT_MIN_SOURCES} sources (strict)")
        if not self.has_problems:
            lines.append("  ✓ all citations resolve")
        return lines


def verify_manual(config: ManualConfig, manual: Manual, strict: bool = False) -> VerifyReport:
    report = VerifyReport()
    line_counts: dict[str, int | None] = {}

    for page in manual.ordered_pages():
        if page.source is PageSource.SKELETON:
            continue  # only narrated pages make claims
        page_path = config.output_path / "manual" / page.section / f"{page.id}.md"
        if not page_path.exists():
            continue
        body = store._extract_region(page_path.read_text(), store.GEN_START, store.GEN_END)
        if body is None:
            continue
        report.pages_checked += 1

        distinct_sources: set[str] = set()
        # 1) line-range citations: existence + range in bounds
        for m in _RANGE_RE.finditer(body):
            rel, start, end = m.group(1), int(m.group(2)), int(m.group(3))
            report.citations_checked += 1
            distinct_sources.add(rel)
            lc = _line_count(config.root, rel, line_counts)
            if lc is None:
                report.violations.append(Violation(page.id, f"cited file not found: {rel}"))
            elif not (1 <= start <= end <= lc):
                report.violations.append(
                    Violation(page.id, f"line range out of bounds: {rel}:{start}-{end} (file has {lc})")
                )

        # 2) relative source links: existence only
        for m in _LINK_RE.finditer(body):
            target = m.group(1)
            if not target.endswith(_SOURCE_SUFFIXES):
                continue
            report.citations_checked += 1
            resolved = (page_path.parent / target).resolve()
            distinct_sources.add(str(resolved))
            if not resolved.exists():
                report.violations.append(Violation(page.id, f"broken source link: {target}"))

        if strict and len(distinct_sources) < STRICT_MIN_SOURCES:
            report.thin_pages.append(page.id)

    return report


def _line_count(root: Path, rel: str, cache: dict[str, int | None]) -> int | None:
    if rel not in cache:
        path = root / rel
        cache[rel] = path.read_text(encoding="utf-8").count("\n") + 1 if path.exists() else None
    return cache[rel]
