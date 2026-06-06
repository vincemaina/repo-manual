---
id: repo_manual.store
title: "repo_manual.store"
section: repo_manual
importance: medium
source: skeleton
status: pending
generated_at: null
related_pages: [repo_manual, repo_manual.config, repo_manual.freshness, repo_manual.model, repo_manual.plan]
relevant_files:
  - path: src/repo_manual/store.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "repo_manual.store"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# repo_manual.store

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/store.py`](../../../src/repo_manual/store.py)

</details>

## Symbols defined here

- `WriteResult  [L57-61]`
- `load_structure(config: ManualConfig) -> Structure | None  [L67-72] — Load the orchestrator-authored ``structure.json`` (the AI grouping), if present.`
- `build_manual(config: ManualConfig, index: RepoIndex) -> tuple[Manual, list[str]]  [L75-80] — Pick the grouping: authored systems (``structure.json``) if present, else the package seed.`
- `write_structure_brief(config: ManualConfig, index: RepoIndex) -> tuple[Path, Path]  [L83-93] — Write the grouping brief + a deterministic suggested structure for the orchestrator to edit`
- `init_store(config: ManualConfig) -> Path  [L96-105] — Create ``.repo-manual/`` + config + a short README. Idempotent.`
- `write_manual(config: ManualConfig, index: RepoIndex, manual: Manual) -> WriteResult  [L108-133] — Write the whole store, preserving any existing narrative + human edits.`
- `write_index(config: ManualConfig, index: RepoIndex) -> None  [L136-139] — Write just the structural index (``index/*.json``) — used by ``scan`` without touching pages.`
- `load_manual(config: ManualConfig) -> Manual | None  [L142-146]`
- `load_index(config: ManualConfig) -> RepoIndex | None  [L149-153] — Load the committed structural index (``index/*.json``), or None if it hasn't been written yet.`
- `_write_page(config: ManualConfig, index: RepoIndex, manual: Manual, page: Page, prev: Manual | None) -> bool  [L159-199] — Write one page file. Returns True if an existing narrative was preserved (vs a fresh skeleton).`
- `_render_skeleton(config: ManualConfig, index: RepoIndex, manual: Manual, page: Page) -> str  [L202-247]`
- `_carry_forward(prev: Manual | None, manual: Manual) -> None  [L253-263] — Copy provenance from the previous manual onto freshly-planned pages so narrated pages keep`
- `_carry_hashes(prev_page: Page | None, page: Page) -> None  [L266-271]`
- `ingest_filled_pages(config: ManualConfig, manual: Manual, now: str) -> list[str]  [L277-300] — Detect pages an orchestrator has narrated (pending marker gone from the .md generated region) and`
- `_rewrite_frontmatter(config: ManualConfig, page: Page) -> None  [L303-316] — Re-emit a page's frontmatter from its (now updated) metadata, preserving both fenced regions.`
- `_write_index(out: Path, index: RepoIndex) -> None  [L322-326]`
- `_load_index(config: ManualConfig) -> RepoIndex  [L329-334]`
- `_write_plan(out: Path, index: RepoIndex, manual: Manual) -> None  [L337-343]`
- `_write_json(path: Path, data: dict) -> None  [L346-348]`
- `_page_path(config: ManualConfig, page: Page) -> Path  [L354-355]`
- `_source_link(config: ManualConfig, page: Page, relpath: str) -> str  [L358-361]`
- `_relative_page_link(manual: Manual, page: Page, other_page_id: str) -> str  [L364-369] — Link from this page's section folder to another page's file, resolving its section folder.`
- `_extract_region(text: str, start: str, end: str) -> str | None  [L372-376]`
- `_frontmatter(page: Page) -> str  [L379-399]`
- `_yaml_str(s: str) -> str  [L402-404]`

## Connects to

- [repo_manual](./repo_manual.md)
- [repo_manual.config](./repo_manual.config.md)
- [repo_manual.freshness](./repo_manual.freshness.md)
- [repo_manual.model](./repo_manual.model.md)
- [repo_manual.plan](./repo_manual.plan.md)
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
