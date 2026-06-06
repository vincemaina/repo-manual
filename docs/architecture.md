# Architecture — repo-manual (MVP)

**A proposal to decide together — NOT locked.** The ChatGPT brief in
[`../notes/chatgpt/PROMPT.md`](../notes/chatgpt/PROMPT.md) is *unreviewed context*, not requirements
(e.g. its "TypeScript-first" was ChatGPT's own invention, not the user's). Some structure below (the
`.repo-manual/` layout, CLI set, knowledge-types) is borrowed from it and is **up for discussion**. The
user's own priorities live in [`brainstorm.md`](./brainstorm.md). This doc is a starting point; §2's
choices are confirmed/changed with the user before building.

## 1. What the MVP is

A **local-first CLI** that builds a version-controlled **`.repo-manual/` project brain** for a **Python**
repo: a committed, version-controlled **orientation manual** an AI authors and a human reads. We **reuse
DeepWiki-Open's source-grounded generation recipe** (LLM-decided nested "systems" → per-page Markdown
chapters, every claim cited to source) rather than fork its 17k-LOC web app, and add the wedge it lacks:
the manual lives as **owned Markdown in the repo** with **freshness/drift tracking** and human-edit
preservation. A deterministic **structural index** (symbols + import/call graph) *grounds* the LLM (and
powers the later blast-radius lens); it's testable with no LLM, but the narrative is the point and is
LLM-authored. See [`landscape.md`](./landscape.md) (why) and [`generation-recipe.md`](./generation-recipe.md) (what we lift).

## 2. Proposed decisions (v0 — to confirm together)

1. **Reuse the recipe, not the app.** Lift DeepWiki-Open's two-phase, source-grounded generation
   (structure → pages, with the "cite every claim, SOLELY from source files" anti-hallucination
   discipline). Build a focused tool; carry none of its served-web-app / RAG-chat code.
2. **Python tool, Python target first.** Deterministic grounding via stdlib `ast` (symbols, imports,
   calls) behind a pluggable `LanguageAnalyzer` (TS later). Dogfood on our two lineage repos.
3. **The `.repo-manual/` folder is the source of truth.** Committed Markdown + YAML frontmatter (+ JSON
   indexes), diffable and PR-reviewable. The manual *is* a repo artifact, not a served wiki.
4. **Freshness + provenance are load-bearing (the wedge).** Each page's frontmatter records its
   `relevant_files` + their **content-hashes**; re-run re-hashes → only **stale** pages regenerate;
   `source: generated|human`. **Human-edited regions are never overwritten.**
5. **LLM via pluggable provider; `claude -p` (headless Claude Code) primary** (already authenticated for
   us), plus API and a **`none` mode** that emits the deterministic skeleton (structure + source links +
   hashes, no narrative) so the whole pipeline is testable without a key.
6. **Mermaid for diagrams** (vertical `graph TD` / `sequenceDiagram`), per the recipe — not ASCII.
7. **Reuse the lineage architecture:** typed in-memory **IR** → **JSON serializer** → **graph traversal**
   (callers/callees = the `upstream`/`downstream` pattern). Stack mirrors the siblings: Python 3.12 ·
   `uv` · `pytest` · `ruff` (line-length 100) · `Typer` CLI · `src/` layout.

## 3. The `.repo-manual/` layout (v0)

```text
.repo-manual/
├── manual.config.json     # roots, language, ignore globs, generator version
├── overview.md            # generated project overview (human edits in marked regions preserved)
├── index/
│   ├── files.json         # SourceFile[]  (path, language, sha, loc)
│   ├── symbols.json       # Symbol[]      (id, kind, name, qualname, file, line range, signature, docstring)
│   └── graph.json         # Edge[]        (imports | calls | contains; src → dst)
├── symbols/               # generated per-module docs (md + frontmatter, source-linked) — GENERATED
│   └── <package>/<module>.md
├── decisions/             # ADRs (repo-manual decision …)                                — HUMAN
├── notes/                 # freeform notes (repo-manual note …)                          — HUMAN
├── issues/                # known issues                                                  — HUMAN
└── ideas/                 # future ideas                                                  — HUMAN
```

Generated = `index/`, `overview.md` (generated regions), `symbols/`. Human = `decisions/`, `notes/`,
`issues/`, `ideas/`, and any region of a generated file fenced as human-authored.

## 4. Data model (the IR)

Typed, immutable, JSON-serializable — the same shape as the lineage tools' IR.

- `SourceFile(path, language, sha, loc)`
- `Symbol(id, kind: module|class|function, name, qualname, file, start_line, end_line, signature, docstring)`
  — `id` is the stable qualname (e.g. `repo_manual.scan.PythonAnalyzer.analyze`).
- `Edge(kind: imports|calls|contains, src: id, dst: id)` — `contains` (module⊃class⊃function),
  `imports` (module→module), `calls` (function→function, best-effort static).
- `Doc(path, frontmatter, body)` where `frontmatter = {source, confidence, last_verified,
  related_symbols: [{id, file, start_line, end_line}], source_hash}`.
- `ManualConfig(roots, language, ignore, generator_version)`.

`KnowledgeGraph` wraps `symbols + edges` with traversal: `callers(id)`, `callees(id)`,
`blast_radius(id)` (transitive), `contains(module)`.

## 5. Pipeline / layers

```
repo source (Python)
   │  scan/  — LanguageAnalyzer (ast): SourceFile[], Symbol[], Edge[]
   ▼
KnowledgeGraph (typed IR)                         ← graph.py: traversal (callers/callees/blast radius)
   │  manual/ — writer: JSON indexes + generated Markdown (frontmatter, source links, content-hash)
   ▼                                                 …merging, never clobbering human content
.repo-manual/  (source of truth)
   │  freshness/ — re-hash source ranges vs stored → stale set
   ▼
views/ — cli (Typer) · open (minimal local web, later) · ai adapter (later, pluggable, optional)
```

## 6. CLI (v0)

- `repo-manual init [path]` — create `.repo-manual/` + `manual.config.json` (idempotent).
- `repo-manual scan` — analyze the repo → write `index/*.json` + generated `overview.md` + `symbols/*.md`
  (preserving human content).
- `repo-manual stale` — list docs whose linked source changed (hash drift).
- `repo-manual search <query>` — search symbols + docs.
- `repo-manual explain <file|symbol>` — print a symbol's doc + signature + callers/callees + source link.
- `repo-manual note|decision|issue|idea "<title>"` — scaffold a human doc, optionally linked to a symbol.
- `repo-manual open` — serve a minimal local web view of `.repo-manual/` *(later in the slice)*.

## 7. First vertical slice (build order)

**Steps 1–6 are the deterministic harness — fully buildable & testable here with no LLM.** Step 7 plugs
in the recipe behind the provider adapter and is where the manual gets its narrative.

> **Status (2026-06-06): working end-to-end, with an interactive viewer.** `src/repo_manual/` ships the
> analyzer, planner (package seed **and** AI system-grouping via `structure.json`), store, freshness,
> citation **verify**, the **`serve` viewer** (nav + Markdown/Mermaid + function drill-down + an
> interactive cytoscape import/call graph with blast-radius), `brief`, and the `stale --check`/`hook`
> drift gate; 26 tests pass. **Two fully-narrated, citation-verified flagships:** `../dbt-test-lineage`
> (5 systems, 62 citations) and repo-manual self-documenting (7 systems, 61 citations). Each page carries
> a `body_hash` so `ingest` re-pins a stale page to fresh only when its prose was actually rewritten.
> Still deferred: an **autonomous** `claude -p`/API provider for headless CI runs (§5) — the only
> remaining piece.

1. **Scaffold** — `uv` project, `src/repo_manual/`, Typer CLI entrypoint, ruff/pytest.
2. **IR + config** (`model.py`, `config.py`) — `SourceFile`/`Symbol`/`Edge`/`ManualConfig` + JSON.
3. **Python analyzer** (`scan/python.py`) — `ast`-based extraction behind a `LanguageAnalyzer` protocol.
   This is the **grounding** the LLM consumes (and what powers blast-radius later). Dogfood: `../dbt-test-lineage`.
4. **Structure planner (deterministic seed)** — turn the graph into candidate sections/pages +
   `relevant_files` (the input to Phase 1; in `none` mode it *is* the structure).
5. **`.repo-manual/` store** (`manual/store.py`) — write `index/*.json` + per-page Markdown with
   frontmatter (`relevant_files` + their **content-hashes**); **content-preserving merge** (never clobber
   human regions). Freshness: `stale` = re-hash vs stored.
6. **CLI + `none`-mode generation** — `init`, `generate --provider none` (emits the skeleton: structure +
   source links + hashes, no prose), `stale`. Run on a lineage repo → a committed `.repo-manual/` we can
   eyeball and diff. **First end-to-end milestone, no key needed.**
7. **Provider adapter + the recipe** — `claude -p` (primary) / API providers; wire Phase 1 (structure
   prompt) + Phase 2 (page prompt, grounded in `relevant_files`, cite-every-claim). `generate` now
   produces the real narrated, Mermaid-rich, source-cited manual; only **stale** pages regenerate.
8. *Then:* `search` / `explain` over the index; the **blast-radius** lens (graph traversal); a viewer.

**Validation throughout:** run against `dbt-column-lineage` / `dbt-test-lineage` — we know them, so wrong
symbols, broken links, or (later) AI hallucinations are immediately visible. That checkability is the
whole reason for Python-first.

## 8. Non-goals (v0)

Multi-language; the VS Code extension; the AI chat; rich web graph UI; the full lens set. All are
designed-for (pluggable analyzers, folder-as-truth, traversal-ready graph) but out of the first slice.
