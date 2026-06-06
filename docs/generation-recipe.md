# Generation recipe (adapted from DeepWiki-Open)

What we **reuse** from [DeepWiki-Open](https://github.com/AsyncFuncAI/deepwiki-open) (MIT): its proven
two-phase, source-grounded generation approach — distilled here so we don't carry its 17k-LOC web app.
Plus the **adaptations** that make repo-manual *ours* (committed artifact + freshness).

## Phase 1 — Structure (one LLM call): decide the nested "systems"

Given the repo (file tree + key files), the LLM returns a nested structure — **AI-decided, not
folder-based**. DeepWiki's schema (we keep the shape):

- `sections` (can contain `subsections` → **nesting**), each section groups `pages`.
- each `page`: `title`, `description`, `importance: high|medium|low`, `relevant_files[]`,
  `related_pages[]`, `parent_section`.
- comprehensive mode seeds an orientation skeleton: *Overview → System Architecture → Core Features →
  Data Flow → Frontend/Backend → Deployment → Extensibility* (we adapt the seed per repo).

This is exactly our "AI-grouped nested systems" — each `page` ≈ a system/subsystem chapter.

## Phase 2 — Pages (one LLM call per page): write the chapter, grounded

Per page, the LLM is given the page topic + the **full content of its `relevant_files`** and must write
Markdown following these rules (the parts worth keeping):

1. **Start with a `<details>` "Relevant source files" block** listing the source files used (linked). ≥5 files.
2. **H1 title**, then a concise **introduction** (purpose/scope), linking to related pages.
3. **Detailed H2/H3 sections** — architecture, components, data flow, logic; name key functions/classes.
4. **Mermaid diagrams, extensively** — `graph TD` (vertical only), `sequenceDiagram`, `classDiagram`,
   `erDiagram`; brief context around each; diagrams derived from the source. *(This is our "use mermaid,
   not ascii" requirement, already baked in.)*
5. **Tables** for features/params/config/data-model summaries.
6. **Code snippets** (optional) lifted from the source files.
7. **Source citations — for EVERY significant claim**, `Sources: [file.ext:start-end]()`. ≥5 files cited.
8. **Technical accuracy: SOLELY from the provided source files** — no inference, no external knowledge,
   state absence rather than invent. *(This is the anti-hallucination discipline — the most important
   rule to keep, and exactly the "facts not vibes" line we've used throughout.)*
9. Clarity/conciseness; brief conclusion.

The trust mechanism is the pairing of **(a) feed real source files** and **(b) cite line ranges for every
claim + forbid outside knowledge.** That's what makes it checkable, and we keep it verbatim in spirit.

## Our adaptations (the wedge — what DeepWiki does NOT do)

1. **Commit the output as owned Markdown in the target repo's `.repo-manual/`** (per-page files + an
   overview + the structure index), not a served-from-cache web wiki. Diffable, PR-reviewable, editable.
2. **Frontmatter per page** carrying `relevant_files` + **content-hashes of those files** → freshness.
3. **Freshness/drift:** on re-run, re-hash each page's `relevant_files`; only **stale** pages regenerate;
   the rest stay. A `stale` command + a status banner. *(DeepWiki regenerates wholesale.)*
4. **Preserve human edits** — fenced human regions are never overwritten by regeneration.
5. **Grounding upgrade:** feed the LLM not just raw files but our **structural index** (symbols +
   import/call graph) so structure/blast-radius claims are accurate and the future change-lens is free.
6. **Pluggable provider, `claude -p` (headless Claude Code) as the primary** — the user already has it
   authenticated; plus API and a `none` deterministic-skeleton mode (structure + source links + hashes,
   no narrative) so the whole pipeline is testable without a key.
7. **Orientation-first framing** — tuned for "an AI built this and I don't understand it," not generic
   docs.
