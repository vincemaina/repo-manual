# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current status: working end-to-end (AI-grouped manual, narrated, verified)

`src/repo_manual/` is a Python CLI that produces a committed, version-controlled orientation manual.
The full loop works with **no bundled LLM** — the agent running the tool is the narrator. Commands
(run via `uv run repo-manual ...`):

- `scan` — analyze → structural index (`index/*.json`).
- `structure` — emit the grouping brief + a suggested `structure.json` for the orchestrator to turn
  package layout into real **systems** (named groups of files by what they do, cross-folder).
- `generate` — plan + write the manual. Uses `structure.json` if present (AI grouping), else a
  deterministic package seed. Writes skeleton pages (a `pending` marker — deliberately NOT the word
  "TODO", so we never pollute a documented repo's task tracker) + a `GenerationTask` in `plan.json`.
- `plan` — pages still needing narrative, and where to ground each.
- `brief <page>` — print one page's full narration brief (files + symbol outline + recipe rules), ready
  to hand to an orchestrator to write in one pass.
- `ingest` — promote orchestrator-filled pages to narrated, pin freshness hashes.
- `stale [--check]` — what drifted / is unwritten; `--check` is a non-zero gate for a pre-commit hook.
- `verify [--strict]` — **trust gate**: check every `Sources: [file:Ls-Le]` citation resolves to a real
  file + line range (catches fabricated/drifted references). No LLM.
- `hook [--install]` — print/install a pre-commit drift + citation check (`stale --check` + `verify`).

Build/lint/test: `uv sync`, `uv run pytest` (23 tests), `uv run ruff check src tests`. Note: page
metadata enums parse tolerantly (`model._enum_or`) so an older/edited `.repo-manual` degrades gracefully
rather than crashing the load.

**Flagship artifact:** `../dbt-test-lineage/.repo-manual/` is a complete, AI-grouped (5 systems +
overview), fully-narrated, citation-verified manual — the reference for what good output looks like.
This repo also has its own `.repo-manual/` (package-seed skeletons).

What's NOT built: an *autonomous* provider (`claude -p`/API) for headless CI runs — deliberately
deferred; the agent-as-orchestrator path is the primary one (see below).

Design docs (the spec / rationale):
- `docs/architecture.md` — the settled v0 decisions + build order (steps 1–8).
- `docs/generation-recipe.md` — the DeepWiki recipe we lift + our 7 adaptations.
- `docs/landscape.md` — prior art and where our wedge is.
- `docs/sample-orientation-manual.md` — the end-state a narrated manual should reach.
- `notes/chatgpt/PROMPT.md`, `docs/design-notes.md`, `docs/brainstorm.md` — earlier idea backlog;
  treat as context, not final spec (parts are superseded by `architecture.md`).

## What this project is

`repo-manual` is a **local-first, version-controlled "project brain" that lives inside
a codebase** — aimed at AI-assisted projects the developer owns but doesn't fully
understand. It is explicitly *not* just generated docs, *not* just chat-with-your-repo,
and *not* just a giant graph.

The core design rests on two deliberately-separated layers:

| Layer | What it is | Why separate |
|---|---|---|
| **Structural graph** | packages → modules → classes → functions as nodes; `imports`/`calls` edges | extractable, always accurate, dry |
| **AI narrative** | grounded natural-language explanation per node, system→function | illuminating, not in the code, goes stale |

The product's **wedge / differentiator is freshness (drift) tracking**: every narrated
unit is content-hashed and marked **stale** when its source changes, with visible
provenance (`source: generated|human`, `confidence`, `last_verified`). Generated prose
must never be presented as authoritative without a freshness signal. When implementing,
treat drift tracking and "never destructively overwrite human-authored content" as
load-bearing requirements, not nice-to-haves.

The canonical knowledge is intended to live in a repo-committed `.repo-manual/` folder
as **Markdown + YAML frontmatter** (human docs) plus **JSON indexes** (generated
graph/symbols/links). The CLI, web UI, and future IDE extension are all *views* over
that folder — the folder is the source of truth.

## Decisions settled (don't relitigate without the user)

- **Language: Python ≥3.12** (matches the sibling lineage tools; stdlib `ast` for the analyzer).
  TypeScript is a *later* analyzer behind the `LanguageAnalyzer` protocol, not a rewrite.
- **Primary view: outline/nested-Markdown-first.** The manual is committed Markdown browsed in the
  editor/GitHub; graphs are local (blast-radius), never a whole-repo dump. A viewer is optional/later.
- **Language scope: Python-first**, pluggable for more later.
- **The LLM is the *orchestrator*, not a bundled provider.** The agent running `repo-manual` (often the
  same agent that wrote the code) does the narration: the tool emits `GenerationTask`s + skeleton pages
  with fenced generated regions; the orchestrator reads `plan.json`, Reads the cited source, and fills
  the generated region; `repo-manual ingest` pins freshness. An autonomous `claude -p`/API provider is a
  *fallback* for standalone runs (CI/cron), planned for step 7. This is why there is no LLM dependency in
  `pyproject.toml`.

## Architectural template and test strategy

- The sibling repos `dbt-column-lineage` / `dbt-test-lineage` (referenced throughout
  the notes) are the intended **architectural template**: a typed in-memory IR → a JSON
  serializer → graph traversal for transitive upstream/downstream. `repo-manual` is
  "lineage for code" with the same shape. Lean on existing building blocks
  (SCIP/tree-sitter for extraction, Cytoscape/D3 for render, mkdocstrings/pdoc for the
  function-level reference leaf, an LLM for narrative) — spend novel effort on the
  **fusion + freshness + zoom UX**, not on re-solving parsing or chat.
- **First MVP target** in the notes is a TypeScript/React/Next.js repo, with the team's
  own small, well-docstringed repos used as the test case (so the output's correctness
  — and any AI hallucination — is immediately checkable).
- AI providers must be **pluggable adapters** (Claude Code headless via `claude -p`,
  Anthropic/OpenAI API, local models, and a no-AI deterministic mode), never a hard
  dependency.

## Conventions

- The repo is `repo-manual`, nested under a `data-tools/` parent alongside the dbt
  lineage tools — keep cross-references to those siblings intact.
- This project is itself a candidate for dogfooding once a slice exists.
