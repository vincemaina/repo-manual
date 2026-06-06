---
id: repo_manual.config
title: "repo_manual.config"
section: repo_manual
importance: high
source: skeleton
status: pending
generated_at: null
related_pages: []
relevant_files:
  - path: src/repo_manual/config.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "repo_manual.config"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# repo_manual.config

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/config.py`](../../../src/repo_manual/config.py)

</details>

## Symbols defined here

- `ManualConfig  [L28-76] — Resolved config. ``root`` is the absolute repo root; the rest is what lands in the JSON file.`
- `ManualConfig.output_path(self) -> Path  [L39-40]`
- `ManualConfig.to_dict(self) -> dict  [L42-50]`
- `ManualConfig.from_dict(cls, root: Path, d: dict) -> ManualConfig  [L53-61]`
- `ManualConfig.load(cls, root: Path) -> ManualConfig  [L64-70] — Load ``<root>/<output>/manual.config.json`` if present, else return defaults.`
- `ManualConfig.save(self) -> Path  [L72-76]`
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
