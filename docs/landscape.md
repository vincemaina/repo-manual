# Landscape — existing solutions (2026)

Research into prior art before committing to a design. **The honest headline: a mature, open-source,
locally-runnable tool already does most of the "AI repo wiki" idea — `DeepWiki-Open`.** This doc maps the
space, then isolates where (and whether) `repo-manual` has a real, defensible wedge.

## The space, grouped by what they solve

### 1. AI repo wikis — the closest competitors
Generate a browsable, AI-narrated wiki for a repo: architecture diagrams + source-linked explanations +
chat.
- **DeepWiki** (Devin / Cognition) — replace `github.com` → `deepwiki.com` and get architecture diagrams,
  file-linked summaries, and a grounded chat. 50k+ public repos pre-indexed. **Hosted / SaaS.** The
  category leader. ([devin docs](https://docs.devin.ai/work-with-devin/deepwiki), [deepwiki.com](https://deepwiki.com/))
- **DeepWiki-Open** (AsyncFuncAI) — **open-source, runs locally** (Docker), code never leaves the machine;
  auto **Mermaid** diagrams of architecture/data-flow, RAG Q&A, multi-provider (Gemini/OpenAI/Ollama).
  This is the one to study closely — it's ~80% of our stated idea, already built.
  ([github](https://github.com/AsyncFuncAI/deepwiki-open))
- **OpenDeepWiki** (AIDotNet) — another OSS DeepWiki (C#/TS), framed as a knowledge-management platform.
  ([github](https://github.com/AIDotNet/OpenDeepWiki))

### 2. Codebase Q&A / onboarding — chat + code graph
- **Greptile** — codebase intelligence + code graph + NL Q&A (and code review); pitched for onboarding.
  ([greptile.com](https://www.greptile.com/))
- **Bloop** — desktop "ChatGPT for your code," semantic search + navigation. ([review](https://aiagentslist.com/agents/bloop-ai))
- **Sourcegraph Cody**, **Cursor**, **Driver.ai** — codebase-aware chat. Ephemeral Q&A, not a durable manual.

### 3. Architecture-diagram generators — code → Mermaid
- **CodeBoarding** — interactive **Mermaid** diagrams from static analysis + LLM; multi-provider; embeds
  in docs/PRs. OSS. ([github](https://github.com/CodeBoarding/CodeBoarding))
- **GitDiagram** — repo → interactive Mermaid diagram (replace `hub`→`diagram`). OSS.
  ([github](https://github.com/ahmedkhaleel2004/gitdiagram))
- **Swark** — VS Code extension, code → Mermaid. OSS. ([github](https://github.com/swark-io/swark))
- These each do *one lens* (the diagram). Use as a **building block**, don't rebuild.

### 4. Docs drift / freshness — keep docs in sync (our "wedge" — but it exists)
- **Swimm** — pioneered **code-coupled documentation**: docs linked to specific snippets that flag/update
  when the code changes. Human-authored docs, though. ([swimm](https://doc.holiday/versus/swimm-vs-mintlify))
- **Mintlify Workflows** — autonomous agent monitors code + docs, detects drift, opens PRs (Claude-powered).
- **Ferndesk**, **Promptless** — drift detection + auto-update drafts.
- Freshness/drift is **not novel** — it's an active category. But it's mostly applied to *product/support*
  docs, not a code-understanding manual, and not fused with the AI repo wiki.

### 5. Repo-committed AI docs — the local-first/version-controlled angle
- **Docudoodle** — AI writes Markdown docs for a codebase (incl. legacy), renders in GitHub. OSS.
  ([github](https://github.com/genericmilk/docudoodle))
- **DocuWriter** — AI code docs for any codebase.
- **Repomix** — packs a codebase into an AI-friendly single file; a **building block** for feeding code to
  an LLM. ([repomix.com](https://repomix.com/))
- Emerging trend: *"local-first documentation for AI agents"* — Markdown + Mermaid committed in-repo,
  AI-maintained, PR-reviewed. ([neuledge](https://neuledge.com/blog/2026-02-19/local-first-documentation-for-ai),
  [torbensko](https://torbensko.com/blog/ai-managed-documentation/))

## What's already good enough (do NOT rebuild)

- **AI wiki + Mermaid diagrams + source links + chat** → DeepWiki / DeepWiki-Open. Local, OSS, multi-provider.
- **Mermaid generation from code** → CodeBoarding / GitDiagram / Swark.
- **Codebase chat / Q&A** → Greptile / Bloop / Cody.
- **Drift detection** → Swimm / Mintlify Workflows.
- **Packing code for an LLM** → Repomix.

## Where the genuine gaps are (the candidate wedge)

No single tool combines all of these, and the combination is the only honest reason to build:

1. **The manual as a *committed, version-controlled artifact the human owns*** — not a hosted/served wiki
   (DeepWiki) or a web app (DeepWiki-Open) regenerated on demand. `repo-manual`'s knowledge lives as
   Markdown + frontmatter *in the repo*: diffable, PR-reviewable, human-correctable, permanent. DeepWiki's
   knowledge lives in DeepWiki.
2. **Freshness fused into the AI wiki.** DeepWiki regenerates wholesale (no per-section drift tied to
   source hashes); Swimm has drift but human docs. The combination — *AI-authored manual with first-class,
   per-unit drift tracking* — is unoccupied.
3. **Authored in-the-loop by the agent that writes the code.** Everyone else does *post-hoc* static
   analysis of a finished repo. If Claude Code (the thing building the app) also maintains the manual, it
   captures *decisions and rationale* that no post-hoc analysis can recover. This is genuinely different.
4. **Sharper niche/framing:** "the AI that built your app writes you a human-friendly manual for it, and
   keeps it honest." Most tools target onboarding-to-someone-else's-repo or docs-for-users.

## Evaluation — tried it (2026-06-06)

Couldn't *run* DeepWiki-Open here (no Docker / no LLM API key), so I (a) read its source and (b) viewed
real DeepWiki output on a public repo. Both are conclusive.

**Its source confirms the approach is exactly our sketch.** The wiki structure is *AI-decided and nested*:
the LLM is asked for a `<wiki_structure>` of `<sections>` (with `<subsections>` → nesting), each `<page>`
carrying `<importance>` (high/medium/low), `<relevant_files>`, `<related_pages>`, `<parent_section>`. In
"comprehensive" mode it even templates an orientation manual (Overview → System Architecture → Core
Features → Data Flow → Frontend/Backend → Deployment → Extensibility). Pages are generated as Markdown
with H2/H3 sections, **must cite ≥5 source files**, and include Mermaid diagrams. (`api/`,
`src/app/[owner]/[repo]/page.tsx`.)

**Its real output is good.** DeepWiki's wiki for `tobymao/sqlglot` (which our tools depend on) is 12
nested sections — incl. "Core Architecture" with subsections and a "Dialect System" with 11 — with
source-file links (`sqlglot/__init__.py#L77-L198`), architecture diagrams, capability tables, and code
examples. Independent read: *"substantially more accessible than raw docstrings… groups concepts into
logical narrative, entry points before details."* In other words — **it already produces the
orientation manual we described.** Our `sample-orientation-manual.md` ≈ DeepWiki output.

**What it does NOT do (confirmed in source):** it's a **served Next.js web app with a cache** — the wiki
is *not* committed to the repo as version-controlled Markdown you own/edit; the cache key is
repo+language+mode with **no per-section source-hash → no freshness/drift tracking** (it regenerates
wholesale); and there's no in-loop authoring by the building agent.

## Honest assessment

- **DeepWiki-Open already does the core "AI orientation wiki" well, locally and open-source.** This is the
  single most important finding. Our sample manual (`sample-orientation-manual.md`) is, frankly, close to
  what DeepWiki-Open produces — minus the committed-artifact + freshness + in-loop-authoring angles.
- So the real choices are: **(a)** build fresh, betting that *local-first-committed + freshness + in-loop
  authoring* is a real enough wedge; **(b)** build *on top of / alongside* DeepWiki-Open (e.g., take its
  generation, add the committed-artifact + drift layer); or **(c)** decide the existing tools are good
  enough and don't build. This is exactly the "is it already good enough?" check to make *before* coding.
- Strong reusable building blocks regardless: **Repomix** (LLM packing), **CodeBoarding/GitDiagram**
  (Mermaid), tree-sitter (parsing), an LLM adapter (narrative), Swimm's drift concept.
