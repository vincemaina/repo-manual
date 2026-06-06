"""The structure planner — how the repo is carved into the pages a human reads.

Two modes:

* **AI grouping (the real product):** the orchestrator decides *systems* — named groups of files by
  *what the code does*, which need not share a folder (e.g. "Propagation Core" = propagate + rules +
  verdict). It writes those into `.repo-manual/structure.json`; `plan_from_structure` turns them into
  one page per system. This is what makes the output an orientation manual rather than a file index.
* **Deterministic seed (the no-LLM fallback):** `plan_manual` emits one page per module, grouped by
  package. Honest and instant, but mechanical — used until a `structure.json` exists.

Either way the planner derives, per page, the `GenerationTask`: the self-contained brief
(relevant files + symbol outline + internal deps) the orchestrator needs to write the narrative.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from repo_manual.model import (
    EdgeKind,
    FileRef,
    GenerationTask,
    Importance,
    Manual,
    Page,
    RepoIndex,
    Section,
    SymbolKind,
)

OVERVIEW_ID = "overview"
OVERVIEW_SLUG = "overview"
SYSTEMS_SLUG = "systems"
UNGROUPED_ID = "ungrouped"
_ENTRYPOINT_STEMS = {"cli", "app", "main", "__main__"}


def plan_manual(index: RepoIndex) -> Manual:
    """Build the deterministic manual structure (sections + pages) from a `RepoIndex`."""
    module_by_file = {s.file: s.qualname for s in index.symbols if s.kind is SymbolKind.MODULE}
    in_degree = _import_in_degree(index)

    pages: dict[str, Page] = {}
    file_to_page: dict[str, str] = {}
    section_pages: dict[str, list[str]] = defaultdict(list)

    for sf in index.files:
        module = module_by_file.get(sf.path, _stem(sf.path))
        page_id = module or _stem(sf.path)
        if page_id in pages:  # extremely defensive against odd layouts
            page_id = sf.path
        section_slug = _section_of(module)
        file_to_page[sf.path] = page_id
        pages[page_id] = Page(
            id=page_id,
            title=module or _stem(sf.path),
            section=section_slug,
            relevant_files=[FileRef(path=sf.path)],
            importance=_importance(sf.path, module, in_degree.get(sf.path, 0)),
        )
        section_pages[section_slug].append(page_id)

    # related_pages: link each page to the pages of the files it imports (internal deps).
    for sf in index.files:
        page = pages[file_to_page[sf.path]]
        related = [
            file_to_page[dep] for dep in index.internal_imports(sf.path) if dep in file_to_page
        ]
        page.related_pages = sorted(set(related) - {page.id})

    manual = Manual()
    manual.pages[OVERVIEW_ID] = _overview_page(index)
    manual.sections.append(Section(slug=OVERVIEW_SLUG, title="Overview", page_ids=[OVERVIEW_ID]))

    for section_slug in sorted(section_pages):
        ordered = sorted(
            section_pages[section_slug],
            key=lambda pid: (_IMPORTANCE_RANK[pages[pid].importance], pid),
        )
        manual.sections.append(
            Section(slug=section_slug, title=section_slug, page_ids=ordered)
        )
        for pid in ordered:
            manual.pages[pid] = pages[pid]

    return manual


# --------------------------------------------------------------------------------------
# AI grouping: build the manual from an orchestrator-authored structure.json
# --------------------------------------------------------------------------------------


@dataclass
class System:
    """One orchestrator-decided system = one page that may span several files."""

    id: str
    title: str
    files: list[str]
    description: str = ""
    importance: Importance = Importance.MEDIUM
    related: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> System:
        return cls(
            id=d["id"],
            title=d.get("title", d["id"]),
            files=list(d.get("files", [])),
            description=d.get("description", ""),
            importance=Importance(d.get("importance", "medium")),
            related=list(d.get("related", [])),
        )


@dataclass
class Structure:
    systems: list[System] = field(default_factory=list)
    overview_description: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> Structure:
        return cls(
            systems=[System.from_dict(s) for s in d.get("systems", [])],
            overview_description=d.get("overview", {}).get("description", "")
            if isinstance(d.get("overview"), dict)
            else "",
        )


def plan_from_structure(index: RepoIndex, structure: Structure) -> tuple[Manual, list[str]]:
    """Build the manual from authored systems (one page per system). Returns (manual, warnings).

    Files named by a system that aren't in the index are dropped (with a warning); files in the index
    that no system claims are collected into an `ungrouped` page so nothing is silently lost."""
    known = {f.path for f in index.files}
    warnings: list[str] = []
    assigned: set[str] = set()

    manual = Manual()
    overview = _overview_page(index)
    if structure.overview_description:
        overview.description = structure.overview_description
    manual.pages[OVERVIEW_ID] = overview
    manual.sections.append(Section(slug=OVERVIEW_SLUG, title="Overview", page_ids=[OVERVIEW_ID]))

    system_ids: list[str] = []
    for sys in structure.systems:
        files = []
        for f in sys.files:
            if f in known:
                files.append(f)
                assigned.add(f)
            else:
                warnings.append(f"system {sys.id!r}: file not found in index: {f}")
        manual.pages[sys.id] = Page(
            id=sys.id,
            title=sys.title,
            section=SYSTEMS_SLUG,
            relevant_files=[FileRef(path=f) for f in files],
            related_pages=list(sys.related),
            importance=sys.importance,
            description=sys.description,
        )
        system_ids.append(sys.id)

    leftover = sorted(known - assigned)
    if leftover:
        warnings.append(f"{len(leftover)} file(s) not assigned to any system -> 'ungrouped' page")
        manual.pages[UNGROUPED_ID] = Page(
            id=UNGROUPED_ID,
            title="Ungrouped",
            section=SYSTEMS_SLUG,
            relevant_files=[FileRef(path=f) for f in leftover],
            importance=Importance.LOW,
            description="Files not yet assigned to a system — group these in structure.json.",
        )
        system_ids.append(UNGROUPED_ID)

    manual.sections.append(Section(slug=SYSTEMS_SLUG, title="Systems", page_ids=system_ids))
    return manual, warnings


def structure_brief(index: RepoIndex) -> dict:
    """The grounding an orchestrator needs to DECIDE systems: every file with its module docstring,
    symbol count, and internal import targets. Emitted by `repo-manual structure`."""
    module_by_file = {s.file: s for s in index.symbols if s.kind is SymbolKind.MODULE}
    files = []
    for sf in index.files:
        mod = module_by_file.get(sf.path)
        files.append(
            {
                "path": sf.path,
                "module": mod.qualname if mod else _stem(sf.path),
                "summary": mod.docstring if mod else "",
                "symbols": len(index.symbols_in(sf.path)),
                "imports": index.internal_imports(sf.path),
            }
        )
    return {"files": files}


def suggested_structure(index: RepoIndex) -> dict:
    """A deterministic starting point for structure.json (package-based), for the orchestrator to edit
    into real systems. Honest scaffold, not the final grouping."""
    seed = plan_manual(index)
    systems = []
    for section in seed.sections:
        if section.slug == OVERVIEW_SLUG:
            continue
        files: list[str] = []
        for pid in section.page_ids:
            files.extend(r.path for r in seed.pages[pid].relevant_files)
        systems.append(
            {
                "id": section.slug.replace(".", "-"),
                "title": section.title,
                "description": "",
                "importance": "medium",
                "files": sorted(set(files)),
                "related": [],
            }
        )
    return {"overview": {"description": ""}, "systems": systems}


def task_for(index: RepoIndex, manual: Manual, page: Page) -> GenerationTask:
    """Assemble the orchestrator brief for one page from the index (symbols + internal deps)."""
    symbol_outline: list[str] = []
    internal_deps: list[str] = []
    for ref in page.relevant_files:
        for sym in index.symbols_in(ref.path):
            sig = sym.signature or ""
            doc = f" — {_trim(sym.docstring)}" if sym.docstring else ""
            symbol_outline.append(
                f"{sym.qualname}{sig}  [L{sym.line_start}-{sym.line_end}]{doc}"
            )
        internal_deps.extend(index.internal_imports(ref.path))
    return GenerationTask(
        page_id=page.id,
        title=page.title,
        section=page.section,
        importance=page.importance,
        relevant_files=[r.path for r in page.relevant_files],
        related_pages=list(page.related_pages),
        symbol_outline=symbol_outline,
        internal_deps=sorted(set(internal_deps)),
    )


def all_tasks(index: RepoIndex, manual: Manual) -> list[GenerationTask]:
    return [task_for(index, manual, p) for p in manual.ordered_pages()]


# -- internals -------------------------------------------------------------------------

_IMPORTANCE_RANK = {Importance.HIGH: 0, Importance.MEDIUM: 1, Importance.LOW: 2}


def _import_in_degree(index: RepoIndex) -> dict[str, int]:
    deg: dict[str, int] = defaultdict(int)
    for e in index.edges:
        if e.kind is EdgeKind.IMPORTS:
            deg[e.dst] += 1
    return deg


def _section_of(module: str) -> str:
    if not module:
        return "root"
    return module.rsplit(".", 1)[0] if "." in module else module


def _stem(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return name[:-3] if name.endswith(".py") else name


def _trim(text: str, limit: int = 110) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _importance(path: str, module: str, in_degree: int) -> Importance:
    stem = _stem(path)
    if stem in _ENTRYPOINT_STEMS:
        return Importance.HIGH
    if in_degree >= 3:
        return Importance.HIGH
    if path.endswith("__init__.py") and in_degree == 0:
        return Importance.LOW
    return Importance.MEDIUM


def _overview_page(index: RepoIndex) -> Page:
    """The 'start here' page. Grounded in the repo's entry points so the narrative can open with how
    a person actually runs the thing."""
    entry_files = sorted(
        {sf.path for sf in index.files if _stem(sf.path) in _ENTRYPOINT_STEMS}
    )
    if not entry_files:
        # fall back to package __init__ files
        entry_files = sorted({sf.path for sf in index.files if sf.path.endswith("__init__.py")})
    return Page(
        id=OVERVIEW_ID,
        title="Overview — start here",
        section=OVERVIEW_SLUG,
        relevant_files=[FileRef(path=p) for p in entry_files],
        importance=Importance.HIGH,
        description="What this repo is, the mental model, and how the systems connect.",
    )
