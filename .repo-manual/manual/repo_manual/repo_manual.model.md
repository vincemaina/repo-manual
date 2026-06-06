---
id: repo_manual.model
title: "repo_manual.model"
section: repo_manual
importance: high
source: skeleton
status: pending
generated_at: null
related_pages: []
relevant_files:
  - path: src/repo_manual/model.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "repo_manual.model"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# repo_manual.model

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/model.py`](../../../src/repo_manual/model.py)

</details>

## Symbols defined here

- `_enum_or(enum_cls: type[_E], value: object, default: _E) -> _E  [L20-27] — Parse an enum value, falling back to ``default`` for unknown/missing values instead of raising —`
- `SymbolKind  [L35-39]`
- `EdgeKind  [L42-44]`
- `SourceFile  [L48-71] — One analyzed source file. ``path`` is repo-relative & POSIX; ``content_hash`` powers freshness.`
- `SourceFile.to_dict(self) -> dict  [L56-62]`
- `SourceFile.from_dict(cls, d: dict) -> SourceFile  [L65-71]`
- `Symbol  [L75-113] — A definition. ``id`` is ``<file>::<qualname>`` (module symbol: ``<file>::<module>``).`
- `Symbol.to_dict(self) -> dict  [L88-99]`
- `Symbol.from_dict(cls, d: dict) -> Symbol  [L102-113]`
- `Edge  [L117-144] — A directed relationship. For ``IMPORTS`` src/dst are file paths; for ``CALLS`` they are`
- `Edge.to_dict(self) -> dict  [L127-134]`
- `Edge.from_dict(cls, d: dict) -> Edge  [L137-144]`
- `RepoIndex  [L148-176] — The whole deterministic picture: files, the symbols defined in them, and the edges between.`
- `RepoIndex.to_dict(self) -> dict  [L155-160]`
- `RepoIndex.from_dict(cls, d: dict) -> RepoIndex  [L163-168]`
- `RepoIndex.symbols_in(self, file_path: str) -> list[Symbol]  [L172-173]`
- `RepoIndex.internal_imports(self, file_path: str) -> list[str]  [L175-176]`
- `Importance  [L184-187]`
- `PageSource  [L190-196] — Provenance of a page's body. ``SKELETON`` = deterministic stub awaiting an orchestrator;`
- `PageStatus  [L199-202]`
- `FileRef  [L206-217] — A page's link to a source file, pinned to the hash it was last narrated against (freshness).`
- `FileRef.to_dict(self) -> dict  [L212-213]`
- `FileRef.from_dict(cls, d: dict) -> FileRef  [L216-217]`
- `Page  [L221-263] — One chapter of the manual: a system/subsystem the human reads. The deterministic core sets`
- `Page.to_dict(self) -> dict  [L236-248]`
- `Page.from_dict(cls, d: dict) -> Page  [L251-263]`
- `Section  [L267-279] — A grouping of pages. ``slug`` is the on-disk folder under ``manual/``.`
- `Section.to_dict(self) -> dict  [L274-275]`
- `Section.from_dict(cls, d: dict) -> Section  [L278-279]`
- `Manual  [L283-308] — The structure index: ordered sections + the flat page map. Persisted to ``manual.json``.`
- `Manual.to_dict(self) -> dict  [L289-293]`
- `Manual.from_dict(cls, d: dict) -> Manual  [L296-300]`
- `Manual.ordered_pages(self) -> list[Page]  [L302-308]`
- `GenerationTask  [L317-355] — Everything the orchestrator needs to narrate one page, with no hidden state. Emitted by the`
- `GenerationTask.to_dict(self) -> dict  [L332-342]`
- `GenerationTask.from_dict(cls, d: dict) -> GenerationTask  [L345-355]`
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
