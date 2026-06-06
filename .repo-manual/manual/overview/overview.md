---
id: overview
title: "Overview — start here"
section: overview
importance: high
source: skeleton
status: pending
description: "What this repo is, the mental model, and how the systems connect."
generated_at: null
related_pages: []
relevant_files:
  - path: src/repo_manual/cli.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "overview"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# Overview — start here

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

What this repo is, the mental model, and how the systems connect.

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/cli.py`](../../../src/repo_manual/cli.py)

</details>

## Symbols defined here

- `_load_or_init_config(path: str) -> ManualConfig  [L41-49]`
- `_analyze(config: ManualConfig)  [L52-53]`
- `_now() -> str  [L56-57]`
- `init(path: str=typer.Argument('.', help='Repo root to initialize.')) -> None  [L61-67] — Create the ``.repo-manual/`` folder and config (idempotent).`
- `scan(path: str=typer.Argument('.', help='Repo root to scan.')) -> None  [L71-80] — Analyze the repo and write only the deterministic structural index (no pages).`
- `generate(path: str=typer.Argument('.', help='Repo root.'), provider: str=typer.Option('none', help="LLM orchestrator. 'none' = deterministic skeletons.")) -> None  [L84-108] — Scan + plan + write the manual. ``--provider none`` writes skeletons for an orchestrator to fill.`
- `plan(path: str=typer.Argument('.', help='Repo root.'), as_json: bool=typer.Option(False, '--json', help='Print the raw plan.json.')) -> None  [L112-138] — Show the pending generation tasks — what the orchestrator should narrate next, and from where.`
- `stale(path: str=typer.Argument('.', help='Repo root.'), check: bool=typer.Option(False, '--check', help='Exit non-zero if any page has drifted (for a pre-commit hook).'), include_pending: bool=typer.Option(False, '--include-pending', help='With --check, also fail on never-narrated pages.')) -> None  [L142-176] — List pages that are out of date (drifted source) or never narrated.`
- `ingest(path: str=typer.Argument('.', help='Repo root.')) -> None  [L180-190] — Promote orchestrator-filled skeletons to narrated pages and pin their freshness hashes.`
- `structure(path: str=typer.Argument('.', help='Repo root.')) -> None  [L194-210] — Emit the grouping brief + a suggested ``structure.json`` for the orchestrator to turn package`
- `verify(path: str=typer.Argument('.', help='Repo root.'), strict: bool=typer.Option(False, '--strict', help='Also fail when a narrated page cites <2 sources.')) -> None  [L214-228] — Check every narrated page's source citations resolve to real files and line ranges (no LLM).`
- `brief(page_id: str=typer.Argument(..., help='The page id to narrate (see `repo-manual plan`).'), path: str=typer.Option('.', '--path', help='Repo root.'), as_json: bool=typer.Option(False, '--json', help='Emit the raw GenerationTask JSON.')) -> None  [L232-277] — Print one page's complete narration brief — the files to ground in, the symbol outline, and the`
- `hook(path: str=typer.Argument('.', help='Repo root.'), install: bool=typer.Option(False, '--install', help='Write the snippet to .git/hooks/pre-commit.')) -> None  [L281-302] — Print (or --install) a git pre-commit hook that flags a manual gone stale + broken citations.`
- `_no_manual() -> int  [L314-316]`
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
