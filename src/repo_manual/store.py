"""The ``.repo-manual/`` store: the folder IS the source of truth. This module writes (and safely
re-writes) it:

* ``index/{files,symbols,edges}.json`` — the deterministic structural index,
* ``manual.json`` — the structure + per-page metadata (provenance, freshness hashes),
* ``plan.json`` — the pending `GenerationTask`s for whatever orchestrator is driving,
* ``manual/<section>/<page>.md`` — one file per page, with two fenced regions:
    - a **generated** region (skeleton until an orchestrator narrates it; then the chapter), and
    - a **human** region that regeneration NEVER overwrites.

Re-running is safe: pages already narrated keep their prose, human notes always survive, and only the
metadata/skeletons are refreshed. The narrative text lives in the ``.md`` (authoritative); ``manual.json``
holds the metadata (authoritative for freshness/provenance).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from repo_manual import freshness
from repo_manual.config import ManualConfig
from repo_manual.hashing import hash_text
from repo_manual.model import (
    GenerationTask,
    Manual,
    Page,
    PageSource,
    RepoIndex,
)
from repo_manual.plan import (
    Structure,
    all_tasks,
    plan_from_structure,
    plan_manual,
    structure_brief,
    suggested_structure,
    task_for,
)

GEN_START = "<!-- repo-manual:generated:start -->"
GEN_END = "<!-- repo-manual:generated:end -->"
HUMAN_START = "<!-- repo-manual:human:start -->"
HUMAN_END = "<!-- repo-manual:human:end -->"
# Marks an un-narrated skeleton. Deliberately uses "pending" (not the word IDE/CI task trackers scan
# for) so this tool never pollutes the tracker of a repo it documents. Detection keys on this string.
PENDING_MARKER = "repo-manual:pending"
STRUCTURE_NAME = "structure.json"

HUMAN_SEED = (
    "<!-- Human notes for this page are preserved across regeneration. Add yours below. -->"
)


@dataclass
class WriteResult:
    pages_total: int
    skeletons_written: int
    narratives_preserved: int
    pending: int  # pages still un-narrated or stale after the write


# -- top-level operations --------------------------------------------------------------


def load_structure(config: ManualConfig) -> Structure | None:
    """Load the orchestrator-authored ``structure.json`` (the AI grouping), if present."""
    path = config.output_path / STRUCTURE_NAME
    if not path.exists():
        return None
    return Structure.from_dict(json.loads(path.read_text()))


def build_manual(config: ManualConfig, index: RepoIndex) -> tuple[Manual, list[str]]:
    """Pick the grouping: authored systems (``structure.json``) if present, else the package seed."""
    structure = load_structure(config)
    if structure is not None:
        return plan_from_structure(index, structure)
    return plan_manual(index), []


def write_structure_brief(config: ManualConfig, index: RepoIndex) -> tuple[Path, Path]:
    """Write the grouping brief + a deterministic suggested structure for the orchestrator to edit
    into real systems. Never overwrites an existing ``structure.json``."""
    out = config.output_path
    out.mkdir(parents=True, exist_ok=True)
    brief = out / "structure.brief.json"
    _write_json(brief, structure_brief(index))
    suggested = out / "structure.suggested.json"
    if not (out / STRUCTURE_NAME).exists():
        _write_json(suggested, suggested_structure(index))
    return brief, suggested


def init_store(config: ManualConfig) -> Path:
    """Create ``.repo-manual/`` + config + a short README. Idempotent."""
    out = config.output_path
    (out / "index").mkdir(parents=True, exist_ok=True)
    (out / "manual").mkdir(parents=True, exist_ok=True)
    config.save()
    readme = out / "README.md"
    if not readme.exists():
        readme.write_text(_README)
    return out


def write_manual(config: ManualConfig, index: RepoIndex, manual: Manual) -> WriteResult:
    """Write the whole store, preserving any existing narrative + human edits."""
    out = config.output_path
    (out / "index").mkdir(parents=True, exist_ok=True)
    (out / "manual").mkdir(parents=True, exist_ok=True)

    prev = load_manual(config)
    _carry_forward(prev, manual)

    skeletons = 0
    preserved = 0
    for page in manual.ordered_pages():
        narrated = _write_page(config, index, manual, page, prev)
        if narrated:
            preserved += 1
        else:
            skeletons += 1

    freshness.refresh(config.root, manual)

    _write_index(out, index)
    _write_json(out / "manual.json", manual.to_dict())
    _write_plan(out, index, manual)

    pending = len(freshness.stale_pages(manual))
    return WriteResult(len(manual.pages), skeletons, preserved, pending)


def write_index(config: ManualConfig, index: RepoIndex) -> None:
    """Write just the structural index (``index/*.json``) — used by ``scan`` without touching pages."""
    (config.output_path / "index").mkdir(parents=True, exist_ok=True)
    _write_index(config.output_path, index)


def load_manual(config: ManualConfig) -> Manual | None:
    path = config.output_path / "manual.json"
    if not path.exists():
        return None
    return Manual.from_dict(json.loads(path.read_text()))


def load_index(config: ManualConfig) -> RepoIndex | None:
    """Load the committed structural index (``index/*.json``), or None if it hasn't been written yet."""
    if not (config.output_path / "index" / "files.json").exists():
        return None
    return _load_index(config)


# -- per-page write --------------------------------------------------------------------


def _write_page(
    config: ManualConfig,
    index: RepoIndex,
    manual: Manual,
    page: Page,
    prev: Manual | None,
) -> bool:
    """Write one page file. Returns True if an existing narrative was preserved (vs a fresh skeleton)."""
    path = _page_path(config, page)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = path.read_text() if path.exists() else ""
    prev_gen = _extract_region(existing, GEN_START, GEN_END)
    human = _extract_region(existing, HUMAN_START, HUMAN_END)
    if human is None:
        human = f"\n{HUMAN_SEED}\n"

    narrated = prev_gen is not None and prev_gen.strip() != "" and PENDING_MARKER not in prev_gen
    if narrated:
        gen_body = prev_gen
        prev_page = prev.pages.get(page.id) if prev else None
        page.source = prev_page.source if prev_page and prev_page.source is not PageSource.SKELETON \
            else PageSource.GENERATED
        page.generated_at = prev_page.generated_at if prev_page else page.generated_at
        _carry_hashes(prev_page, page)
    else:
        gen_body = _render_skeleton(config, index, manual, page)
        page.source = PageSource.SKELETON
        for ref in page.relevant_files:
            ref.hash = ""

    # Resolve status now so the page's frontmatter matches manual.json (written post-refresh).
    page.status = freshness.page_status(config.root, page)

    text = (
        _frontmatter(page)
        + f"\n{GEN_START}\n{gen_body.strip()}\n{GEN_END}\n"
        + f"\n{HUMAN_START}\n{human.strip()}\n{HUMAN_END}\n"
    )
    path.write_text(text)
    return narrated


def _render_skeleton(config: ManualConfig, index: RepoIndex, manual: Manual, page: Page) -> str:
    task = task_for(index, manual, page)
    lines: list[str] = []
    lines.append(
        f"<!-- {PENDING_MARKER}  Orchestrator: replace this generated region with the page narrative.\n"
        f"     Read the relevant source files below (and plan.json, page id \"{page.id}\"), then write\n"
        f"     the chapter per docs/generation-recipe.md: source-grounded, cite every claim\n"
        f"     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.\n"
        f"     Leave the human region untouched. -->"
    )
    lines.append("")
    lines.append(f"# {page.title}")
    lines.append("")
    lines.append(
        "> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not "
        "yet written._"
    )
    lines.append("")
    if page.description:
        lines.append(page.description)
        lines.append("")

    lines.append("<details>")
    lines.append("<summary>Relevant source files</summary>")
    lines.append("")
    for ref in page.relevant_files:
        lines.append(f"- [`{ref.path}`]({_source_link(config, page, ref.path)})")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    if task.symbol_outline:
        lines.append("## Symbols defined here")
        lines.append("")
        for entry in task.symbol_outline:
            lines.append(f"- `{entry}`")
        lines.append("")

    if page.related_pages:
        lines.append("## Connects to")
        lines.append("")
        for rel in page.related_pages:
            lines.append(f"- [{rel}]({_relative_page_link(manual, page, rel)})")
        lines.append("")

    return "\n".join(lines)


# -- carry-forward / freshness metadata ------------------------------------------------


def _carry_forward(prev: Manual | None, manual: Manual) -> None:
    """Copy provenance from the previous manual onto freshly-planned pages so narrated pages keep
    their generated/human status across a re-plan."""
    if prev is None:
        return
    for pid, page in manual.pages.items():
        prev_page = prev.pages.get(pid)
        if prev_page and prev_page.source is not PageSource.SKELETON:
            page.source = prev_page.source
            page.generated_at = prev_page.generated_at
            page.body_hash = prev_page.body_hash
            _carry_hashes(prev_page, page)


def _carry_hashes(prev_page: Page | None, page: Page) -> None:
    if not prev_page:
        return
    prev_hashes = {r.path: r.hash for r in prev_page.relevant_files}
    for ref in page.relevant_files:
        ref.hash = prev_hashes.get(ref.path, "")


# -- ingest (orchestrator handoff back into the store) ---------------------------------


def ingest_filled_pages(config: ManualConfig, manual: Manual, now: str) -> list[str]:
    """Pin freshness for pages the orchestrator has (re)narrated. A page is (re)pinned when its generated
    region is real (pending marker gone) AND either it was a skeleton or its region changed since the last
    pin (``body_hash`` differs). Pinning stamps current source hashes + ``generated_at`` + the new
    ``body_hash``. This is the seam where agent-written prose re-enters freshness tracking — and it's what
    lets a STALE page return to FRESH after you rewrite it (not just newly-filled skeletons)."""
    promoted: list[str] = []
    for page in manual.ordered_pages():
        path = _page_path(config, page)
        if not path.exists():
            continue
        gen = _extract_region(path.read_text(), GEN_START, GEN_END)
        narrated = gen is not None and gen.strip() != "" and PENDING_MARKER not in gen
        if not narrated:
            continue
        body_hash = hash_text(gen.strip())
        rewritten = page.source is PageSource.SKELETON or body_hash != page.body_hash
        if rewritten:
            page.source = PageSource.GENERATED
            page.generated_at = now
            page.body_hash = body_hash
            for ref in page.relevant_files:
                ref.hash = freshness.current_hash(config.root, ref.path) or ""
            promoted.append(page.id)
    if promoted:
        freshness.refresh(config.root, manual)
        for pid in promoted:
            _rewrite_frontmatter(config, manual.pages[pid])
        _write_json(config.output_path / "manual.json", manual.to_dict())
        _write_plan(config.output_path, _load_index(config), manual)
    return promoted


def _rewrite_frontmatter(config: ManualConfig, page: Page) -> None:
    """Re-emit a page's frontmatter from its (now updated) metadata, preserving both fenced regions.
    Keeps the human-facing ``.md`` mirror in sync with ``manual.json`` after an ingest."""
    path = _page_path(config, page)
    text = path.read_text()
    gen = _extract_region(text, GEN_START, GEN_END)
    human = _extract_region(text, HUMAN_START, HUMAN_END)
    if gen is None or human is None:
        return
    path.write_text(
        _frontmatter(page)
        + f"\n{GEN_START}\n{gen.strip()}\n{GEN_END}\n"
        + f"\n{HUMAN_START}\n{human.strip()}\n{HUMAN_END}\n"
    )


# -- serialization helpers -------------------------------------------------------------


def _write_index(out: Path, index: RepoIndex) -> None:
    d = index.to_dict()
    _write_json(out / "index" / "files.json", {"files": d["files"]})
    _write_json(out / "index" / "symbols.json", {"symbols": d["symbols"]})
    _write_json(out / "index" / "edges.json", {"edges": d["edges"]})


def _load_index(config: ManualConfig) -> RepoIndex:
    out = config.output_path
    files = json.loads((out / "index" / "files.json").read_text()).get("files", [])
    symbols = json.loads((out / "index" / "symbols.json").read_text()).get("symbols", [])
    edges = json.loads((out / "index" / "edges.json").read_text()).get("edges", [])
    return RepoIndex.from_dict({"files": files, "symbols": symbols, "edges": edges})


def _write_plan(out: Path, index: RepoIndex, manual: Manual) -> None:
    pending = {p.id for p in freshness.stale_pages(manual)}
    tasks: list[GenerationTask] = [t for t in all_tasks(index, manual) if t.page_id in pending]
    _write_json(
        out / "plan.json",
        {"pending": [t.to_dict() for t in tasks], "pending_count": len(tasks)},
    )


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# -- markdown helpers ------------------------------------------------------------------


def _page_path(config: ManualConfig, page: Page) -> Path:
    return config.output_path / "manual" / page.section / f"{page.id}.md"


def _source_link(config: ManualConfig, page: Page, relpath: str) -> str:
    page_dir = _page_path(config, page).parent
    target = config.root / relpath
    return os.path.relpath(target, page_dir)


def _relative_page_link(manual: Manual, page: Page, other_page_id: str) -> str:
    """Link from this page's section folder to another page's file, resolving its section folder."""
    other = manual.pages.get(other_page_id)
    if other is None or other.section == page.section:
        return f"./{other_page_id}.md"
    return f"../{other.section}/{other_page_id}.md"


def _extract_region(text: str, start: str, end: str) -> str | None:
    if start not in text or end not in text:
        return None
    inner = text.split(start, 1)[1].split(end, 1)[0]
    return inner


def _frontmatter(page: Page) -> str:
    lines = ["---"]
    lines.append(f"id: {page.id}")
    lines.append(f"title: {_yaml_str(page.title)}")
    lines.append(f"section: {page.section}")
    lines.append(f"importance: {page.importance.value}")
    lines.append(f"source: {page.source.value}")
    lines.append(f"status: {page.status.value}")
    if page.description:
        lines.append(f"description: {_yaml_str(page.description)}")
    lines.append(f"generated_at: {page.generated_at if page.generated_at else 'null'}")
    if page.related_pages:
        lines.append(f"related_pages: [{', '.join(page.related_pages)}]")
    else:
        lines.append("related_pages: []")
    lines.append("relevant_files:")
    for ref in page.relevant_files:
        lines.append(f"  - path: {ref.path}")
        lines.append(f"    hash: {_yaml_str(ref.hash)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _yaml_str(s: str) -> str:
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


_README = """# .repo-manual

An **AI-authored, human-read orientation manual** for this repo, kept in version control.

- `manual/` — one Markdown page per system/module. Each page has a generated region (skeleton until
  narrated) and a human region that is never overwritten.
- `index/` — the deterministic structural index (files, symbols, import/call graph).
- `manual.json` — page structure + provenance + freshness hashes.
- `plan.json` — pages still needing narrative (the orchestrator's worklist).
- `structure.json` (optional) — the AI grouping of files into named *systems*.

Typical loop: `generate` → an orchestrator narrates pending pages (`plan` / `brief <page>`) → `ingest`
→ `verify`. Pages whose source files changed show as **stale** (`repo-manual stale`); only those are
rewritten — narrative + human notes are preserved. `repo-manual hook` installs a pre-commit drift +
citation check.
"""
