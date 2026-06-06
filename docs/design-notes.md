# repo-manual — design notes

> A navigable, multi-resolution **manual for a codebase**: start at the system level and zoom down to a
> single function, fusing the code's *structure* (a graph) with AI-written *explanation* (the "why").
> Status: early design exploration. This is a thinking document, not a committed spec.

## The problem

Software is now built fast, often AI-assisted — and the bottleneck shifts from *writing* code to
*understanding* what the built code actually does. The existing artifacts each cover one slice:

- **READMEs / architecture docs** — the conceptual "why," but high-level and quickly stale.
- **API reference (Sphinx/pdoc)** — every signature + docstring, but flat, dry, and structure-blind.
- **The code itself** — ground truth, but you have to already know where to look.

What's missing is a single surface that lets you **start high and click down** — System → Subsystem →
File → Function — where each level shows *both* the structure (what connects to what) *and* a plain-
language explanation of what it does and why. That's `repo-manual`.

There's a pleasing recursion here: the sibling projects (`dbt-column-lineage`, `dbt-test-lineage`) do
**lineage for SQL** — parse artifacts → build a graph → make it navigable. `repo-manual` is **lineage
for code** — the same shape, applied to a Python (later: any) repo.

## The core idea: graph × narrative

Two complementary layers, deliberately kept separate because they have opposite properties:

| Layer | What | Property |
|---|---|---|
| **Structural graph** | modules / files / functions as nodes; imports & calls as edges | *extractable, always accurate, dry* |
| **AI narrative** | natural-language explanation attached to each node / level | *not in the code, illuminating, goes stale* |

The drill-down experience = **zooming the graph** (collapse/expand nodes) **+ expanding the narrative**
(system summary → subsystem flow → function detail). Neither layer alone is enough: the graph without
narrative is a maze; the narrative without the graph is a wall of text you can't navigate.

## The graph view (the heart of it)

The thing worth building well. Sketch:

- **Levels / node types:** package → module (file) → class → function. A node collapses to hide its
  children (a module shown as one box) and expands to reveal them — that *is* the zoom / drill-down.
- **Edge types:** `imports` (module→module), `calls` (function→function), and optionally `data-flow` /
  `type-flow` (what produces the value a function consumes — closest to true "lineage").
- **Interaction:** click a node → side panel with its signature, source, docstring, **callers &
  callees**, and the AI explanation. Pan/zoom, full-text search, filter-by-subsystem, "show only what
  reaches this node" (transitive neighborhood — exactly the `upstream`/`downstream` traversal the
  lineage engine already does).
- **Extraction:** Python `ast` / `libcst` for definitions, imports, and (static) call edges; or consume
  a **SCIP/LSIF** index for precise cross-references that survive dynamic dispatch better than naive AST
  call-graphs. `tree-sitter` if/when multi-language.
- **Rendering:** Cytoscape.js or D3 in a web UI; Graphviz for static export. A graph DB (or just an
  in-memory IR + JSON, like the lineage tools) behind it.

The lineage engine's architecture is a direct template: a typed **IR** (here: code symbols + edges), a
**serializer** (JSON), and **graph traversal** (transitive callers/callees). We could lift that shape
almost verbatim.

## The AI-narrative layer

Where LLMs genuinely beat static tools — they can explain *call flow and intent across functions*, which
no signature dump captures and no human keeps updated. But it has to be done carefully:

- **Grounded, not freeform.** Generate each node's explanation from the *code + existing docstrings +
  commit messages + architecture docs* — never from thin air. (Our two repos already carry rich module
  & function docstrings and per-folder `CLAUDE.md` files — ideal substrate, and a good first test of
  "does the AI add anything beyond what's already written?")
- **Layered.** One-paragraph system overview → per-subsystem "how data flows here" → per-file role →
  per-function "what & why," each hyperlinked up/down. The levels mirror the graph's zoom.
- **Freshness is the whole game.** Generated docs that drift from code become a *liability*, not an
  asset (the same trust trap we hit in `dbt-test-lineage`'s cost feature — a confident-looking but wrong
  number). So each narrated unit is **content-hashed**; when the code changes, its narrative is marked
  **stale** (and regenerated incrementally). Every explanation shows provenance: *"AI-generated, synced
  at commit `abc123`."* Never present generated prose as authoritative without a freshness signal — the
  same principle as the test-lineage provenance guardrail.
- **Cost-aware.** Regenerate only changed units; cache the rest. Narrative for a large repo is the
  expensive part; incremental + cached keeps it viable.

## Prior art / reference projects

The space is crowded but no one tool does the full combination. Grouped by what they solve (commercial
status shifts — verify current state, knowledge here is ~early 2026):

**Structural graph & navigation**
- **Sourcetrail** — *the* reference for the drill-down UX: click a symbol → see its graph neighborhood
  (callers, callees, definition). Open-sourced, but development was discontinued (~2021) — dated, no AI.
  The clearest "this is the target experience" to study.
- **Understand (SciTools)** — commercial, deep dependency/call-graph analysis & metrics. Powerful,
  closed, enterprise, no AI narrative.
- **Sourcegraph** — code search + precise navigation across repos; defined the **SCIP** index format
  (successor to Microsoft's **LSIF**). Great cross-reference substrate; added **Cody** for AI Q&A.
- **CodeSee** — visual codebase maps/diagrams (note: appears to have wound down; included for the idea).

**API docs from docstrings (the "leaf level" done well)**
- **mkdocs + mkdocstrings** (Material theme), **Sphinx** (+autoapi/napoleon), **pdoc** — auto-generate
  navigable, searchable per-module/per-function reference from docstrings. Solid drill-down nav, but
  reference-style: no graph, no synthesized "why."

**Docs coupled to code (anti-staleness)**
- **Swimm** — docs that live next to code and **break the build when they drift**. The freshness/
  coupling idea we'd adopt — but human-authored, no graph, no AI generation.

**AI codebase explanation**
- **Sourcegraph Cody**, **Cursor**, **Claude Code**, **GitHub Copilot chat**, **Devin**, "chat-with-
  your-repo" tools — strong at *ephemeral Q&A* ("how does auth work?"). Weak at producing a *persistent,
  navigable, multi-resolution* map you can browse and trust over time.

**Building blocks (don't rebuild these)**
- Call/import graphs: `pyan3`, `code2flow`, `pydeps`, `pycallgraph2`. Parsing: `ast`/`libcst`,
  `tree-sitter`. Rendering: Cytoscape.js, D3, Graphviz. Indexing: SCIP/LSIF.

## What to add / improve — the wedge (or: is it already good enough?)

Honest read of where to build vs. reuse:

- **API reference → already good enough.** Don't rebuild mkdocstrings/Sphinx. *Use* one as the
  function-level leaf.
- **AI Q&A → already good enough.** Don't rebuild chat (Cody/Cursor/Claude Code). Possibly *embed* a
  chat as a secondary affordance.
- **Structural graph → good but dated.** Sourcetrail/Understand prove the value; both are old/closed/
  AI-less. Room for a modern, web-native, open take.
- **The actual gap (the wedge):** *no tool fuses* **graph structure × AI "why" narrative × multi-
  resolution zoom × freshness/drift tracking.** Each does one or two. `repo-manual` = a **persistent,
  navigable code graph where every node carries a grounded, freshness-tracked AI explanation, zoomable
  from system to function.** The **drift detector is the differentiator** — it's what makes AI-generated
  docs trustworthy instead of a stale liability, and nobody combines it with AI generation + a graph.

Strategy: lean hard on existing building blocks (SCIP/tree-sitter for extraction, Cytoscape for render,
an LLM for narrative, mkdocstrings for the reference leaf) and spend the novel effort on the **fusion +
freshness + zoom UX** — not on re-solving parsing or chat.

## Open questions / risks

- **Is a graph the right *primary* UI?** Big graphs overwhelm. Many devs prefer a file/symbol **tree or
  outline** as the spine, with the graph as an on-demand "show neighborhood" view. Maybe the manual is
  outline-first, graph-second.
- **Static call graphs are imprecise in Python** (duck typing, dynamic dispatch) — naive AST misses
  calls; SCIP/type-inference helps but isn't perfect. Set expectations: "best-effort call edges."
- **Narrative staleness & cost at scale** — the freshness machinery and incremental regeneration are
  load-bearing, not optional.
- **Scope creep** — "documentation tool" vs. "code-exploration IDE" vs. "onboarding tool." Pick the job.
- **Language scope** — Python-first (matches the lineage tools, fast to validate) vs. multi-language via
  tree-sitter/SCIP from the start.

## A possible phasing (to validate cheaply)

Use our own two repos as the test case — they're small, well-structured, richly docstringed, and we
*know* them, so we can tell immediately whether the output is right (and whether the AI lies).

1. **Extract + render the structural graph** for one Python repo (modules + functions + import/call
   edges), with collapse/expand zoom and a click-to-detail panel.
2. **Wire the reference leaf** — signatures + docstrings per function (embed mkdocstrings or render from
   the AST).
3. **Add grounded AI narrative** per node (system → function), with provenance.
4. **Add freshness/drift detection** (content-hash per unit; mark stale; incremental regen).
5. **Polish the zoom/search UX**; consider multi-language later.

The honest checkpoint after step 1–2: *does this already beat a plain mkdocstrings site enough to
justify the rest?* If yes, the AI narrative + freshness (3–4) are the payoff. If not, the off-the-shelf
docs site was the right answer and `repo-manual` is a research curiosity — better to learn that early.
