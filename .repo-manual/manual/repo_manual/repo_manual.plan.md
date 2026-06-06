---
id: repo_manual.plan
title: "repo_manual.plan"
section: repo_manual
importance: medium
source: skeleton
status: pending
generated_at: null
related_pages: [repo_manual.model]
relevant_files:
  - path: src/repo_manual/plan.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "repo_manual.plan"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# repo_manual.plan

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/plan.py`](../../../src/repo_manual/plan.py)

</details>

## Symbols defined here

- `plan_manual(index: RepoIndex) -> Manual  [L40-88] — Build the deterministic manual structure (sections + pages) from a `RepoIndex`.`
- `System  [L97-116] — One orchestrator-decided system = one page that may span several files.`
- `System.from_dict(cls, d: dict) -> System  [L108-116]`
- `Structure  [L120-131]`
- `Structure.from_dict(cls, d: dict) -> Structure  [L125-131]`
- `plan_from_structure(index: RepoIndex, structure: Structure) -> tuple[Manual, list[str]]  [L134-184] — Build the manual from authored systems (one page per system). Returns (manual, warnings).`
- `structure_brief(index: RepoIndex) -> dict  [L187-203] — The grounding an orchestrator needs to DECIDE systems: every file with its module docstring,`
- `suggested_structure(index: RepoIndex) -> dict  [L206-227] — A deterministic starting point for structure.json (package-based), for the orchestrator to edit`
- `task_for(index: RepoIndex, manual: Manual, page: Page) -> GenerationTask  [L230-251] — Assemble the orchestrator brief for one page from the index (symbols + internal deps).`
- `all_tasks(index: RepoIndex, manual: Manual) -> list[GenerationTask]  [L254-255]`
- `_import_in_degree(index: RepoIndex) -> dict[str, int]  [L263-268]`
- `_section_of(module: str) -> str  [L271-274]`
- `_stem(path: str) -> str  [L277-279]`
- `_trim(text: str, limit: int=110) -> str  [L282-283]`
- `_importance(path: str, module: str, in_degree: int) -> Importance  [L286-294]`
- `_overview_page(index: RepoIndex) -> Page  [L297-313] — The 'start here' page. Grounded in the repo's entry points so the narrative can open with how`

## Connects to

- [repo_manual.model](./repo_manual.model.md)
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
