I want to build a new developer tool. For now, assume the working name is **Repo Manual**.

The goal is to create a **local-first, version-controlled project brain that lives inside a codebase**. It is designed especially for projects where a developer has used AI coding tools like Claude Code, Cursor, Codex, etc. to build a working product quickly, but now does not fully understand how the code works.

This is not just a documentation generator. It should be closer to a permanent knowledge base / brain for the project: a place where architecture, runtime flows, feature explanations, design decisions, known issues, future ideas, notes, and AI context all live inside the repo.

The core product idea:

> Repo Manual helps developers understand, maintain, and regain ownership of codebases, especially AI-generated or AI-assisted codebases, by creating a source-linked, version-controlled project brain inside the repo.

Important positioning:

* This is more than generated documentation.
* This is more than chat-with-your-codebase.
* This is more than a static wiki.
* The product should help the user build a real mental model of the project.
* It should support multiple “lenses” for understanding the same repo.
* It should be tightly coupled to the source code, not disconnected from it.
* It should be useful both to humans and to future AI coding agents.

The user problem:

AI coding tools are now very good at writing code quickly. The fastest way to get value from them is often to let them build a lot. But the downside is that the final codebase can become something the developer owns but does not fully understand. This makes it harder to debug, modify, extend, onboard onto, or trust.

Repo Manual should solve that by making the project understandable after the fact.

Core concept:

The repo should contain a folder such as:

```text
.repo-manual/
```

This folder should hold the project brain. It should be version controlled with the repo. The canonical knowledge should live in readable files, ideally Markdown plus structured metadata/frontmatter, so it can be read directly in an IDE, diffed in Git, reviewed in PRs, and used by AI coding agents.

The live site, CLI, and IDE extension should be views over this repo-native knowledge base, not the only place the knowledge exists.

Possible folder structure:

```text
.repo-manual/
├── manual.config.json
├── overview.md
├── map.json
├── index/
│   ├── symbols.json
│   ├── links.json
│   ├── graph.json
│   └── search.json
├── features/
│   ├── auth.md
│   ├── billing.md
│   └── dashboard.md
├── flows/
│   ├── app-startup.md
│   ├── login-flow.md
│   └── checkout-flow.md
├── decisions/
│   ├── 0001-use-nextjs.md
│   └── 0002-use-sqlite-for-local-dev.md
├── issues/
│   └── known-edge-cases.md
├── ideas/
│   └── future-improvements.md
├── concepts/
│   └── data-model.md
├── tutorials/
│   └── learn-this-repo.md
├── ai/
│   └── agent-context.md
└── diagrams/
    ├── architecture.mmd
    └── login-flow.mmd
```

The exact structure can change, but the principle is important: human-readable knowledge lives inside the repo, while generated indexes/graphs support richer interactions.

Key knowledge types:

1. **Project overview**

   * What the app/tool/project is.
   * Main technologies.
   * Main systems.
   * How to run it.
   * Where to start reading.

2. **Feature explanations**

   * Human-level features such as Authentication, Billing, Dashboard, CLI Commands, Data Import, etc.
   * Each feature should link to relevant files, functions, classes, routes, tests, decisions, known issues, and flows.

3. **Runtime flows**

   * How execution moves through the project.
   * Examples: app startup, login flow, API request lifecycle, CLI command lifecycle, data import flow.
   * These should include Mermaid diagrams where useful.

4. **Source-linked function/file/class explanations**

   * Explanations of important files, functions, classes, modules, routes, and components.
   * These should link to exact source files and ideally source ranges.

5. **Architecture decisions**

   * ADR-style records explaining why major choices were made.
   * Example: “Why we use signed cookies”, “Why we use local SQLite”, “Why this is client-side only”.
   * Include context, decision, alternatives considered, consequences.

6. **Known issues**

   * Bugs, edge cases, fragile areas, technical debt, risky assumptions.

7. **Future ideas**

   * Potential improvements, roadmap items, half-formed product ideas, experiments.

8. **Concepts / glossary**

   * Project-specific language.
   * Important domain concepts.

9. **AI context**

   * Notes for future AI agents working on the repo.
   * Example: “Before changing auth, read features/auth.md and decisions/0004-session-cookies.md.”
   * Example: “Do not edit generated files directly.”
   * Example: “Prefer small focused functions in this repo.”

10. **Learning path**

    * A curated tutorial/course for understanding the repo step by step.
    * Especially useful for AI-generated projects where the human needs to work backwards from the final product to understand how it was built.

The main “lenses”:

1. **System / architecture lens**

   * Top-down overview of the main systems in the project.
   * Example: Authentication → Login form → Session handling → Protected routes.

2. **Feature lens**

   * Understand the project by human-facing features.
   * Example: “How does login work?”
   * Should show user flow, runtime flow, relevant files, key functions, diagrams, and safe-change notes.

3. **Runtime lens**

   * Understand where execution starts and what happens next.
   * For a web app: route → handler/action → service → database → UI.
   * For a CLI: command → parser → handler → services → output.
   * Should support sequence diagrams / flowcharts.

4. **Dependency / call graph lens**

   * What calls this?
   * What does this call?
   * What depends on this file/function/module?
   * What is the blast radius of changing this?
   * Avoid giant unreadable graphs; prioritise filtered local graphs.

5. **Learning path lens**

   * “Learn this repo in 30/60/90 minutes.”
   * Step-by-step guided course.
   * Include exercises like “change this text”, “add a field”, “trace this request”, etc.

6. **Change lens**

   * User selects a file/function/feature and asks: “What do I need to understand before changing this?”
   * The tool responds with relevant docs, source files, known issues, decisions, tests, and suggested safe-change path.

7. **Knowledge base lens**

   * Search and browse all project knowledge: notes, decisions, ideas, issues, explanations, glossary, docs.
   * The user should be able to drill down into only the context they need, without being overwhelmed.

Important UX principle:

The product should use progressive disclosure. Do not dump huge walls of generated text by default. For any selected item, show:

* one-line meaning
* relevant feature/system
* source links
* related docs
* related decisions
* known issues
* “open full explanation”
* “show callers/callees”
* “show runtime flow”
* “what should I read before changing this?”

The default view should be calm and minimal, with the ability to drill deeper.

Source linking requirements:

Docs must be tightly coupled to code. They should not merely mention files; they should link to actual files and ideally symbol/source ranges.

For example, metadata could look like:

```yaml
related_symbols:
  - name: createSession
    file: src/lib/session.ts
    start_line: 14
    end_line: 48
  - name: middleware
    file: src/middleware.ts
    start_line: 6
    end_line: 30
```

This enables:

* open exact file location
* hover docs in IDE
* stale doc detection when linked source changes
* “called by / calls” relationships
* source-grounded explanations
* confidence/provenance indicators

Trust/provenance:

Generated docs should be distinguishable from human-authored docs.

Possible states:

```yaml
source: generated
verified_by: null
confidence: medium
last_verified: 2026-06-06
```

or:

```yaml
source: human
author: Vince
last_updated: 2026-06-06
```

Docs could move through states:

```text
Generated → Reviewed → Verified → Potentially stale
```

When code changes, linked docs should be marked potentially stale.

The tool should preserve human-written notes and avoid destructively overwriting them when regenerating docs.

Architecture direction:

The tool should have several layers:

```text
Repo source files
   ↓
Scanner / parser
   - file tree
   - symbols
   - imports/exports
   - routes
   - components
   - tests
   - env vars
   - package metadata

   ↓
Knowledge graph / index
   - files
   - functions
   - classes
   - modules
   - features
   - flows
   - decisions
   - notes
   - known issues
   - ideas
   - relationships

   ↓
Repo Manual files
   - Markdown
   - frontmatter
   - JSON indexes
   - Mermaid diagrams

   ↓
Views
   - CLI
   - local web app
   - VS Code extension
   - AI chat/adapter
```

Implementation direction:

Start local-first. The initial version should be a CLI plus generated `.repo-manual/` folder. A local web UI can come after or alongside this.

Possible CLI commands:

```bash
repo-manual init
repo-manual scan
repo-manual update
repo-manual open
repo-manual explain src/lib/auth.ts
repo-manual decision "Use signed cookies for sessions"
repo-manual note "Auth edge case"
repo-manual stale
repo-manual search "login flow"
```

MVP target:

Build an MVP that works well on a TypeScript / React / Next.js repo first.

MVP features:

1. Initialise `.repo-manual/`.
2. Scan repo file tree.
3. Detect package/framework info where possible.
4. Detect important files, routes, components, functions, imports/exports.
5. Generate a project overview Markdown file.
6. Generate a feature map.
7. Generate basic runtime entry points.
8. Generate source-linked Markdown docs.
9. Generate Mermaid diagrams where useful.
10. Build a local searchable index.
11. Provide a local web UI for browsing/searching.
12. Allow adding human notes/decisions/issues/ideas.
13. Preserve human-written content during regeneration.
14. Mark docs as potentially stale when linked source changes.
15. Optional: include an AI chat/query interface that uses the repo manual and source index as context.

Possible technical choices:

* Language: TypeScript/Node is a good default because the first target ecosystem is TypeScript/React/Next.js.
* CLI framework: choose something simple and maintainable.
* Parsing: use Tree-sitter and/or TypeScript compiler API where appropriate.
* Search: start with local full-text/fuzzy search; can use a local index.
* Storage: Markdown + YAML frontmatter for human docs; JSON for generated indexes.
* Diagrams: Mermaid `.mmd` files and Markdown Mermaid blocks.
* Web UI: local web app that reads `.repo-manual/`.
* Editor integration later: VS Code extension.

AI integration:

The tool should support pluggable AI providers. It should not require one specific provider.

Possible providers:

1. **Claude Code local adapter**

   * If the user already has Claude Code installed and authenticated locally, allow using it in non-interactive/headless mode.
   * For example, call Claude Code via `claude -p` / `--print` with carefully constructed prompts and repo context.
   * This should be optional.

2. **API provider adapter**

   * Anthropic API, OpenAI API, etc.
   * User provides API key/config.

3. **Local model adapter**

   * Future support for Ollama or other local models.

4. **No-AI mode**

   * Still scan, index, and show deterministic structure without generating rich explanations.

The AI chat is not the core product, but it could be useful. The user might ask natural language questions like:

* “How does login work?”
* “What should I understand before changing this file?”
* “Where is the pricing calculation implemented?”
* “What features depend on this database table?”
* “Explain this repo to me like I’m new to it.”
* “What docs are stale?”
* “What did the previous design decisions say about auth?”

The chat should use the repo manual as the first source of truth, then source code as supporting context. It should cite or link to relevant docs and files.

IDE extension idea:

A VS Code extension would be very valuable later.

Possible features:

1. CodeLens above important functions/classes:

   * “Open docs”
   * “Explain”
   * “Related decisions”
   * “Show call flow”
   * “Add note”

2. Hover cards:

   * One-line project-specific meaning.
   * Related feature.
   * Related docs.
   * Called by / calls.
   * Known issues.
   * Link to full Repo Manual page.

3. Side panel:

   * Current file docs.
   * Related feature.
   * Related decisions.
   * Known issues.
   * Future ideas.
   * Call graph.
   * Learning path step.

4. Command palette:

   * Repo Manual: Open docs for current file
   * Repo Manual: Explain current symbol
   * Repo Manual: Add note linked to current selection
   * Repo Manual: Create architecture decision
   * Repo Manual: Show stale docs
   * Repo Manual: Open local manual

Important product distinction:

This should not be a generic PKM tool. It should be specifically designed around source code understanding.

This should not be only generated documentation. It should be a living project memory.

This should not be only chat. Chat is one interface; the durable knowledge is the `.repo-manual/` content.

This should not be only a giant graph. Graphs should be filtered and useful.

This should not overwhelm the user. It should help them access the smallest relevant bit of context at the right time.

Competitive inspiration / adjacent tools:

* DeepWiki: generated repository wiki with diagrams and source links.
* Swimm: code-coupled documentation and knowledge management.
* Sourcegraph Cody: codebase-aware chat.
* Dendron / Obsidian-like tools: local Markdown knowledge bases.
* ADRs: architecture decision records.
* Docs-as-code: documentation versioned alongside source code.

But this product’s sharper niche is:

> A local-first, source-linked, version-controlled project brain for understanding and maintaining AI-generated codebases.

Suggested tagline:

> Repo Manual — the project brain that lives in your repo.

Or:

> Understand the code AI wrote for you.

Or:

> A version-controlled brain for your codebase.

Please help me design and begin implementing this project.

Start by doing the following:

1. Propose a practical MVP architecture.
2. Recommend a folder/file structure.
3. Recommend the initial TypeScript/Node project setup.
4. Define the core data model for files, symbols, docs, links, features, flows, decisions, issues, and notes.
5. Define the CLI commands for v0.
6. Define how scanning should work for a TypeScript/Next.js repo.
7. Define how Markdown/frontmatter docs should be generated and updated safely.
8. Define how to preserve human-authored content.
9. Define how to mark docs as stale when source files change.
10. Define the first implementation plan in small steps.
11. Then begin implementing the MVP incrementally.

Important implementation preferences:

* Keep it local-first.
* Keep the canonical project brain as Markdown/frontmatter plus JSON indexes inside `.repo-manual/`.
* Do not overbuild the first version.
* Prioritise a working vertical slice over a huge architecture.
* Make the codebase clean, modular, and easy to extend.
* Use deterministic static analysis where possible, and AI only where it adds value.
* Design AI providers as adapters, not hard dependencies.
* Start with TypeScript/Node and TypeScript/Next.js repo support.
* Make sure generated docs are source-linked and traceable.
* Make sure updates do not wipe human notes.
* Build with future VS Code extension support in mind, but do not implement the extension until the core CLI/data model is solid.

A good first vertical slice would be:

1. `repo-manual init`
2. Creates `.repo-manual/` with config and starter files.
3. `repo-manual scan`
4. Scans a TypeScript/Next.js repo.
5. Writes `index/files.json`, `index/symbols.json`, `index/links.json`.
6. Generates `overview.md`.
7. Generates one or two feature docs if obvious features/routes are detected.
8. Generates a simple Mermaid architecture diagram.
9. `repo-manual search <query>`
10. Searches the generated manual/index.
11. `repo-manual open`
12. Opens a simple local web UI or serves the Markdown/index in a basic browser interface.

Before coding, please propose the architecture and implementation plan, then implement step by step.
