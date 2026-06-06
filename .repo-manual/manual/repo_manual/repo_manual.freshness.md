---
id: repo_manual.freshness
title: "repo_manual.freshness"
section: repo_manual
importance: medium
source: skeleton
status: pending
generated_at: null
related_pages: [repo_manual.hashing, repo_manual.model]
relevant_files:
  - path: src/repo_manual/freshness.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "repo_manual.freshness"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# repo_manual.freshness

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/freshness.py`](../../../src/repo_manual/freshness.py)

</details>

## Symbols defined here

- `current_hash(root: Path, relpath: str) -> str | None  [L20-25] — Hash a source file as it exists on disk now, or ``None`` if it no longer exists.`
- `page_status(root: Path, page: Page) -> PageStatus  [L28-35] — Re-evaluate one page's freshness against the working tree (does not mutate the page).`
- `refresh(root: Path, manual: Manual) -> dict[str, PageStatus]  [L38-45] — Recompute and write back every page's ``status``. Returns the {page_id: status} map.`
- `stale_pages(manual: Manual) -> list[Page]  [L48-50] — Pages an orchestrator still owes work on: never narrated (PENDING) or drifted (STALE).`

## Connects to

- [repo_manual.hashing](./repo_manual.hashing.md)
- [repo_manual.model](./repo_manual.model.md)
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
