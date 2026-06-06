---
id: repo_manual.verify
title: "repo_manual.verify"
section: repo_manual
importance: medium
source: skeleton
status: pending
generated_at: null
related_pages: [repo_manual, repo_manual.config, repo_manual.model, repo_manual.store]
relevant_files:
  - path: src/repo_manual/verify.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "repo_manual.verify"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# repo_manual.verify

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/verify.py`](../../../src/repo_manual/verify.py)

</details>

## Symbols defined here

- `Violation  [L33-35]`
- `VerifyReport  [L39-59]`
- `VerifyReport.has_problems(self) -> bool  [L46-47]`
- `VerifyReport.format_lines(self) -> list[str]  [L49-59]`
- `verify_manual(config: ManualConfig, manual: Manual, strict: bool=False) -> VerifyReport  [L62-105]`
- `_line_count(root: Path, rel: str, cache: dict[str, int | None]) -> int | None  [L108-112]`

## Connects to

- [repo_manual](./repo_manual.md)
- [repo_manual.config](./repo_manual.config.md)
- [repo_manual.model](./repo_manual.model.md)
- [repo_manual.store](./repo_manual.store.md)
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
