---
id: repo_manual.scan.base
title: "repo_manual.scan.base"
section: repo_manual.scan
importance: medium
source: skeleton
status: pending
generated_at: null
related_pages: [repo_manual.config, repo_manual.model, repo_manual.scan.python]
relevant_files:
  - path: src/repo_manual/scan/base.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "repo_manual.scan.base"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# repo_manual.scan.base

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/scan/base.py`](../../../src/repo_manual/scan/base.py)

</details>

## Symbols defined here

- `LanguageAnalyzer  [L15-22] — Static analysis for one language. Implementations must be pure & deterministic: same bytes in,`
- `LanguageAnalyzer.analyze(self, config: ManualConfig) -> RepoIndex  [L22-22]`
- `iter_source_files(config: ManualConfig, suffixes: tuple[str, ...]) -> list[Path]  [L25-46] — Walk ``config.source_dirs`` (or the repo root) yielding files with a matching suffix, honoring`
- `_is_test_path(rel: Path) -> bool  [L49-53]`
- `get_analyzer(language: str) -> LanguageAnalyzer  [L56-62] — Return the analyzer for ``language`` (currently just Python). Raises on unknown languages.`

## Connects to

- [repo_manual.config](../repo_manual/repo_manual.config.md)
- [repo_manual.model](../repo_manual/repo_manual.model.md)
- [repo_manual.scan.python](./repo_manual.scan.python.md)
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
