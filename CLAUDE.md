# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current status: design exploration, no implementation yet

This repo currently contains **only design documents** — there is no source code, no
build, no tests, and no CLI. Do not look for or invent commands to build/lint/test;
they don't exist yet. The first real work is to turn the design below into a first
vertical slice.

Read these before doing anything substantive (they are the spec):
- `docs/design-notes.md` — the "graph × narrative" framing, prior art, and phasing.
- `notes/chatgpt/PROMPT.md` — the fuller product vision, `.repo-manual/` folder
  layout, data model, CLI command set, and MVP checklist.
- `docs/brainstorm.md` — loose idea backlog (decision tracking, test coverage links).

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

## Decisions still open (resolve before building, don't assume)

- **Implementation language is unsettled.** `pyproject.toml` declares a Python ≥3.12
  package named `repo-manual` with no dependencies, but `notes/chatgpt/PROMPT.md`
  argues for **TypeScript/Node** (since the first target ecosystem is TS/React/Next.js,
  using tree-sitter / the TS compiler API). These conflict. Confirm the intended
  language with the user before scaffolding — don't silently pick one.
- **Primary UI:** graph-first vs. outline/tree-first with graph as an on-demand
  "show neighborhood" view (design notes lean toward outline-first).
- **Language scope:** Python-first (matches sibling lineage tools) vs. multi-language
  via tree-sitter/SCIP from the start.

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
