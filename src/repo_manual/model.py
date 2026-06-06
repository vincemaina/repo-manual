"""The in-memory IR: a deterministic **structural index** of a repo (`RepoIndex`) and the
**manual structure** layered on top of it (`Manual` -> `Section` -> `Page`), plus the
`GenerationTask` packet that the orchestrator (the agent running this tool) consumes to write
each page's narrative. See docs/architecture.md §6 (data model).

Everything here is a plain dataclass with explicit ``to_dict``/``from_dict`` so the index and the
manual round-trip to the committed JSON in ``.repo-manual/index/`` losslessly. We avoid
``dataclasses.asdict`` for enums/nesting determinism (stable key order, str enums).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar

_E = TypeVar("_E", bound=Enum)


def _enum_or(enum_cls: type[_E], value: object, default: _E) -> _E:
    """Parse an enum value, falling back to ``default`` for unknown/missing values instead of raising —
    so an older or hand-edited ``.repo-manual`` (e.g. a status renamed between versions) degrades
    gracefully rather than crashing the load."""
    try:
        return enum_cls(value)
    except ValueError:
        return default


# --------------------------------------------------------------------------------------
# Structural index (the deterministic grounding the LLM later reads, and the blast-radius graph)
# --------------------------------------------------------------------------------------


class SymbolKind(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


class EdgeKind(str, Enum):
    IMPORTS = "imports"  # module -> module (internal import)
    CALLS = "calls"  # symbol -> symbol (best-effort resolved call)


@dataclass(frozen=True)
class SourceFile:
    """One analyzed source file. ``path`` is repo-relative & POSIX; ``content_hash`` powers freshness."""

    path: str
    language: str
    content_hash: str
    line_count: int

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "language": self.language,
            "content_hash": self.content_hash,
            "line_count": self.line_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SourceFile:
        return cls(
            path=d["path"],
            language=d["language"],
            content_hash=d["content_hash"],
            line_count=d["line_count"],
        )


@dataclass(frozen=True)
class Symbol:
    """A definition. ``id`` is ``<file>::<qualname>`` (module symbol: ``<file>::<module>``)."""

    id: str
    kind: SymbolKind
    name: str
    qualname: str
    file: str
    line_start: int
    line_end: int
    signature: str = ""
    docstring: str = ""  # first line only — a teaser, not the whole thing

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "name": self.name,
            "qualname": self.qualname,
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
            "docstring": self.docstring,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Symbol:
        return cls(
            id=d["id"],
            kind=SymbolKind(d["kind"]),
            name=d["name"],
            qualname=d["qualname"],
            file=d["file"],
            line_start=d["line_start"],
            line_end=d["line_end"],
            signature=d.get("signature", ""),
            docstring=d.get("docstring", ""),
        )


@dataclass(frozen=True)
class Edge:
    """A directed relationship. For ``IMPORTS`` src/dst are file paths; for ``CALLS`` they are
    symbol ids. ``dst_name`` keeps the raw callee even when ``dst`` couldn't be resolved to a symbol."""

    kind: EdgeKind
    src: str
    dst: str
    dst_name: str = ""
    resolved: bool = True

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "src": self.src,
            "dst": self.dst,
            "dst_name": self.dst_name,
            "resolved": self.resolved,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Edge:
        return cls(
            kind=EdgeKind(d["kind"]),
            src=d["src"],
            dst=d["dst"],
            dst_name=d.get("dst_name", ""),
            resolved=d.get("resolved", True),
        )


@dataclass
class RepoIndex:
    """The whole deterministic picture: files, the symbols defined in them, and the edges between."""

    files: list[SourceFile] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "files": [f.to_dict() for f in self.files],
            "symbols": [s.to_dict() for s in self.symbols],
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, d: dict) -> RepoIndex:
        return cls(
            files=[SourceFile.from_dict(x) for x in d.get("files", [])],
            symbols=[Symbol.from_dict(x) for x in d.get("symbols", [])],
            edges=[Edge.from_dict(x) for x in d.get("edges", [])],
        )

    # --- small read helpers used by the planner / store ---

    def symbols_in(self, file_path: str) -> list[Symbol]:
        return [s for s in self.symbols if s.file == file_path and s.kind is not SymbolKind.MODULE]

    def internal_imports(self, file_path: str) -> list[str]:
        return [e.dst for e in self.edges if e.kind is EdgeKind.IMPORTS and e.src == file_path]


# --------------------------------------------------------------------------------------
# Manual structure (the AI-grouped systems; in `none` mode this is a deterministic seed)
# --------------------------------------------------------------------------------------


class Importance(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PageSource(str, Enum):
    """Provenance of a page's body. ``SKELETON`` = deterministic stub awaiting an orchestrator;
    ``GENERATED`` = LLM-authored narrative; ``HUMAN`` = hand-written, never overwritten."""

    SKELETON = "skeleton"
    GENERATED = "generated"
    HUMAN = "human"


class PageStatus(str, Enum):
    PENDING = "pending"  # never narrated (skeleton only)
    FRESH = "fresh"  # narrated and source hashes match
    STALE = "stale"  # narrated but a relevant_file changed since


@dataclass
class FileRef:
    """A page's link to a source file, pinned to the hash it was last narrated against (freshness)."""

    path: str
    hash: str = ""  # the content_hash of `path` when the page was last (re)generated; "" until then

    def to_dict(self) -> dict:
        return {"path": self.path, "hash": self.hash}

    @classmethod
    def from_dict(cls, d: dict) -> FileRef:
        return cls(path=d["path"], hash=d.get("hash", ""))


@dataclass
class Page:
    """One chapter of the manual: a system/subsystem the human reads. The deterministic core sets
    everything except the narrative body; the orchestrator writes the body into the page file."""

    id: str
    title: str
    section: str
    relevant_files: list[FileRef] = field(default_factory=list)
    related_pages: list[str] = field(default_factory=list)
    importance: Importance = Importance.MEDIUM
    description: str = ""
    source: PageSource = PageSource.SKELETON
    status: PageStatus = PageStatus.PENDING
    generated_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "section": self.section,
            "relevant_files": [f.to_dict() for f in self.relevant_files],
            "related_pages": list(self.related_pages),
            "importance": self.importance.value,
            "description": self.description,
            "source": self.source.value,
            "status": self.status.value,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Page:
        return cls(
            id=d["id"],
            title=d["title"],
            section=d["section"],
            relevant_files=[FileRef.from_dict(x) for x in d.get("relevant_files", [])],
            related_pages=list(d.get("related_pages", [])),
            importance=_enum_or(Importance, d.get("importance"), Importance.MEDIUM),
            description=d.get("description", ""),
            source=_enum_or(PageSource, d.get("source"), PageSource.SKELETON),
            status=_enum_or(PageStatus, d.get("status"), PageStatus.PENDING),
            generated_at=d.get("generated_at"),
        )


@dataclass
class Section:
    """A grouping of pages. ``slug`` is the on-disk folder under ``manual/``."""

    slug: str
    title: str
    page_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"slug": self.slug, "title": self.title, "page_ids": list(self.page_ids)}

    @classmethod
    def from_dict(cls, d: dict) -> Section:
        return cls(slug=d["slug"], title=d["title"], page_ids=list(d.get("page_ids", [])))


@dataclass
class Manual:
    """The structure index: ordered sections + the flat page map. Persisted to ``manual.json``."""

    sections: list[Section] = field(default_factory=list)
    pages: dict[str, Page] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "sections": [s.to_dict() for s in self.sections],
            "pages": {pid: p.to_dict() for pid, p in self.pages.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> Manual:
        return cls(
            sections=[Section.from_dict(x) for x in d.get("sections", [])],
            pages={pid: Page.from_dict(p) for pid, p in d.get("pages", {}).items()},
        )

    def ordered_pages(self) -> list[Page]:
        out: list[Page] = []
        for section in self.sections:
            for pid in section.page_ids:
                if pid in self.pages:
                    out.append(self.pages[pid])
        return out


# --------------------------------------------------------------------------------------
# The orchestrator seam: a self-contained brief for writing one page's narrative.
# --------------------------------------------------------------------------------------


@dataclass
class GenerationTask:
    """Everything the orchestrator needs to narrate one page, with no hidden state. Emitted by the
    planner, surfaced by ``repo-manual plan``, and embedded (as a pending stub) into skeleton page files so
    the agent driving the tool can fill the page in place. This is the contract that replaces a
    bundled LLM provider (docs/architecture.md §5: the LLM is the orchestrator, not a dependency)."""

    page_id: str
    title: str
    section: str
    importance: Importance
    relevant_files: list[str]  # repo-relative paths the narrative must be grounded in
    related_pages: list[str]
    symbol_outline: list[str]  # "qualname(signature) — docstring  [Lstart-end]" per defined symbol
    internal_deps: list[str]  # repo-relative paths this page's files import (for "how it connects")

    def to_dict(self) -> dict:
        return {
            "page_id": self.page_id,
            "title": self.title,
            "section": self.section,
            "importance": self.importance.value,
            "relevant_files": list(self.relevant_files),
            "related_pages": list(self.related_pages),
            "symbol_outline": list(self.symbol_outline),
            "internal_deps": list(self.internal_deps),
        }

    @classmethod
    def from_dict(cls, d: dict) -> GenerationTask:
        return cls(
            page_id=d["page_id"],
            title=d["title"],
            section=d["section"],
            importance=Importance(d.get("importance", "medium")),
            relevant_files=list(d.get("relevant_files", [])),
            related_pages=list(d.get("related_pages", [])),
            symbol_outline=list(d.get("symbol_outline", [])),
            internal_deps=list(d.get("internal_deps", [])),
        )
