"""The ``repo-manual`` CLI — the deterministic harness; the narrative is written by the *orchestrator*
running this tool (the agent), which reads each page's brief and fills the generated region. No LLM key.

Commands:
* ``init``      — create ``.repo-manual/`` + config.
* ``scan``      — analyze the repo -> write the structural index (``index/*.json``).
* ``structure`` — emit the grouping brief so the orchestrator can author ``structure.json`` (AI systems).
* ``generate``  — scan + plan + write the manual (systems if ``structure.json`` exists, else package seed).
* ``plan``      — show the pages still needing narrative, and where to ground each.
* ``brief``     — print one page's complete narration brief (files + symbols + rules), ready to write.
* ``ingest``    — after an orchestrator fills page skeletons, promote them into freshness tracking.
* ``stale``     — list (or ``--check`` gate) pages that drifted or were never narrated.
* ``verify``    — the trust gate: every source citation resolves to a real file + line range.
* ``hook``      — print/install a pre-commit drift + citation check.
* ``serve``     — interactive browser view (nav by system, Mermaid, function drill-down). No new deps.
* ``guide``     — print an onboarding guide for the agent driving the tool (give a fresh session this).

See docs/architecture.md §5 for the orchestration model.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from repo_manual import freshness, store
from repo_manual.config import CONFIG_NAME, DEFAULT_OUTPUT, ManualConfig
from repo_manual.model import PageStatus
from repo_manual.plan import task_for
from repo_manual.scan import get_analyzer
from repo_manual.verify import verify_manual

app = typer.Typer(
    add_completion=False,
    help="An AI-authored, human-read orientation manual that lives in your repo.",
    no_args_is_help=True,
)


def _load_or_init_config(path: str) -> ManualConfig:
    root = Path(path).resolve()
    config_file = root / DEFAULT_OUTPUT / CONFIG_NAME
    if config_file.exists():
        return ManualConfig.load(root)
    config = ManualConfig(root=root)
    if not (root / "src").exists():  # no src/ layout -> scan from the repo root
        config.source_dirs = ["."]
    return config


def _analyze(config: ManualConfig):
    return get_analyzer(config.language).analyze(config)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@app.command()
def init(path: str = typer.Argument(".", help="Repo root to initialize.")) -> None:
    """Create the ``.repo-manual/`` folder and config (idempotent)."""
    config = _load_or_init_config(path)
    out = store.init_store(config)
    typer.echo(f"Initialized {out}")
    typer.echo(f"  language={config.language}  source_dirs={config.source_dirs}")
    typer.echo("Next: repo-manual generate")


@app.command()
def scan(path: str = typer.Argument(".", help="Repo root to scan.")) -> None:
    """Analyze the repo and write only the deterministic structural index (no pages)."""
    config = _load_or_init_config(path)
    index = _analyze(config)
    store.init_store(config)
    store.write_index(config, index)
    typer.echo(
        f"Indexed {len(index.files)} files, {len(index.symbols)} symbols, {len(index.edges)} edges"
        f" -> {config.output_dir}/index/"
    )


@app.command()
def generate(
    path: str = typer.Argument(".", help="Repo root."),
    provider: str = typer.Option("none", help="LLM orchestrator. 'none' = deterministic skeletons."),
) -> None:
    """Scan + plan + write the manual. ``--provider none`` writes skeletons for an orchestrator to fill."""
    if provider != "none":
        raise typer.BadParameter(
            f"provider {provider!r} not bundled. The narrative is written by the orchestrator running "
            "this tool (the agent): run `generate` (none mode) for skeletons, then have the agent fill "
            "them from `plan.json`, then `ingest`. Autonomous providers (claude -p / API) come later."
        )
    config = _load_or_init_config(path)
    store.init_store(config)
    index = _analyze(config)
    manual, warnings = store.build_manual(config, index)
    grouping = "systems (structure.json)" if store.load_structure(config) else "package seed"
    result = store.write_manual(config, index, manual)

    typer.echo(f"Wrote {result.pages_total} pages to {config.output_dir}/manual/  [grouping: {grouping}]")
    typer.echo(
        f"  {result.skeletons_written} skeleton(s), {result.narratives_preserved} narrative(s) kept"
    )
    for w in warnings:
        typer.echo(f"  ! {w}")
    typer.echo(f"  {result.pending} page(s) pending narrative -> see `repo-manual plan`")


@app.command()
def plan(
    path: str = typer.Argument(".", help="Repo root."),
    as_json: bool = typer.Option(False, "--json", help="Print the raw plan.json."),
) -> None:
    """Show the pending generation tasks — what the orchestrator should narrate next, and from where."""
    config = _load_or_init_config(path)
    manual = store.load_manual(config)
    if manual is None:
        raise typer.Exit(_no_manual())
    freshness.refresh(config.root, manual)

    if as_json:
        plan_path = config.output_path / "plan.json"
        typer.echo(plan_path.read_text() if plan_path.exists() else "{}")
        return

    pending = freshness.stale_pages(manual)
    if not pending:
        typer.echo("Nothing pending — every page is narrated and fresh. ✅")
        return
    typer.echo(f"{len(pending)} page(s) need narrative:\n")
    for page in pending:
        flag = page.status.value.upper()  # PENDING (never narrated) or STALE (drifted)
        typer.echo(f"  [{flag:7}] {page.id}  ({page.section})")
        for ref in page.relevant_files:
            typer.echo(f"           ground in: {ref.path}")
    typer.echo("\nThe orchestrator fills each page's generated region, then run `repo-manual ingest`.")


@app.command()
def stale(
    path: str = typer.Argument(".", help="Repo root."),
    check: bool = typer.Option(
        False, "--check", help="Exit non-zero if any page has drifted (for a pre-commit hook)."
    ),
    include_pending: bool = typer.Option(
        False, "--include-pending", help="With --check, also fail on never-narrated pages."
    ),
) -> None:
    """List pages that are out of date (drifted source) or never narrated.

    With ``--check`` this becomes a gate: it exits 1 when source has drifted from the manual, so a
    pre-commit/pre-push hook can stop a commit that leaves the docs behind (see ``repo-manual hook``)."""
    config = _load_or_init_config(path)
    manual = store.load_manual(config)
    if manual is None:
        raise typer.Exit(_no_manual())
    statuses = freshness.refresh(config.root, manual)
    pending = [pid for pid, s in statuses.items() if s is PageStatus.PENDING]
    drifted = [pid for pid, s in statuses.items() if s is PageStatus.STALE]
    fresh = [pid for pid, s in statuses.items() if s is PageStatus.FRESH]

    typer.echo(f"fresh: {len(fresh)}   stale: {len(drifted)}   pending: {len(pending)}")
    for pid in drifted:
        typer.echo(f"  STALE    {pid}")
    for pid in pending:
        typer.echo(f"  PENDING  {pid}")

    if check and (drifted or (include_pending and pending)):
        typer.secho(
            "\nmanual is out of date — refresh the stale pages (`repo-manual plan`), or commit with "
            "--no-verify to skip.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(1)


@app.command()
def ingest(path: str = typer.Argument(".", help="Repo root.")) -> None:
    """Promote orchestrator-filled skeletons to narrated pages and pin their freshness hashes."""
    config = _load_or_init_config(path)
    manual = store.load_manual(config)
    if manual is None:
        raise typer.Exit(_no_manual())
    promoted = store.ingest_filled_pages(config, manual, _now())
    if not promoted:
        typer.echo("No newly-filled pages found.")
        return
    typer.echo(f"Ingested {len(promoted)} page(s): {', '.join(promoted)}")


@app.command()
def structure(path: str = typer.Argument(".", help="Repo root.")) -> None:
    """Emit the grouping brief + a suggested ``structure.json`` for the orchestrator to turn package
    layout into real *systems* (named groups of files by what they do)."""
    config = _load_or_init_config(path)
    store.init_store(config)
    index = _analyze(config)
    brief, suggested = store.write_structure_brief(config, index)
    has_structure = store.load_structure(config) is not None
    typer.echo(f"Wrote grouping brief -> {brief.relative_to(config.root)}")
    if has_structure:
        typer.echo(f"  {config.output_dir}/{store.STRUCTURE_NAME} already exists — left untouched.")
    else:
        typer.echo(f"  Seed to edit -> {suggested.relative_to(config.root)}")
        typer.echo(
            "  Orchestrator: group files into systems (cross-folder is fine), then save as "
            f"{config.output_dir}/{store.STRUCTURE_NAME} and run `repo-manual generate`."
        )


@app.command()
def verify(
    path: str = typer.Argument(".", help="Repo root."),
    strict: bool = typer.Option(False, "--strict", help="Also fail when a narrated page cites <2 sources."),
) -> None:
    """Check every narrated page's source citations resolve to real files and line ranges (no LLM).
    This is the trust gate: it catches the citations a narrator might fabricate."""
    config = _load_or_init_config(path)
    manual = store.load_manual(config)
    if manual is None:
        raise typer.Exit(_no_manual())
    report = verify_manual(config, manual, strict=strict)
    for line in report.format_lines():
        typer.echo(line)
    if report.has_problems:
        raise typer.Exit(1)


@app.command()
def brief(
    page_id: str = typer.Argument(..., help="The page id to narrate (see `repo-manual plan`)."),
    path: str = typer.Option(".", "--path", help="Repo root."),
    as_json: bool = typer.Option(False, "--json", help="Emit the raw GenerationTask JSON."),
) -> None:
    """Print one page's complete narration brief — the files to ground in, the symbol outline, and the
    recipe rules — so an orchestrator (or you) can write that page in a single pass."""
    config = _load_or_init_config(path)
    manual = store.load_manual(config)
    index = store.load_index(config)
    if manual is None or index is None:
        raise typer.Exit(_no_manual())
    page = manual.pages.get(page_id)
    if page is None:
        typer.echo(f"No page {page_id!r}. Known pages: {', '.join(sorted(manual.pages))}", err=True)
        raise typer.Exit(1)

    task = task_for(index, manual, page)
    if as_json:
        typer.echo(json.dumps(task.to_dict(), indent=2))
        return

    typer.secho(f"# Brief: {page.title}  ({page.id})", bold=True)
    typer.echo(f"section: {page.section}   importance: {page.importance.value}")
    if page.description:
        typer.echo(f"\n{page.description}")
    typer.secho("\nGround the narrative ONLY in these files:", bold=True)
    for f in task.relevant_files:
        typer.echo(f"  - {f}")
    if task.symbol_outline:
        typer.secho("\nSymbols to cover:", bold=True)
        for entry in task.symbol_outline:
            typer.echo(f"  - {entry}")
    if task.internal_deps:
        typer.secho("\nInternal deps (for 'how it connects'):", bold=True)
        for d in task.internal_deps:
            typer.echo(f"  - {d}")
    if task.related_pages:
        typer.echo(f"\nRelated pages: {', '.join(task.related_pages)}")
    typer.secho("\nRules:", bold=True)
    typer.echo(
        "  source-grounded (cite every claim as `Sources: [file:Lstart-end]()`), vertical mermaid\n"
        "  (graph TD), progressive disclosure, tables for facts. Write into the page's generated\n"
        f"  region, then run `repo-manual ingest` and `repo-manual verify`.\n"
        f"  Page file: {config.output_dir}/manual/{page.section}/{page.id}.md"
    )


@app.command()
def hook(
    path: str = typer.Argument(".", help="Repo root."),
    install: bool = typer.Option(False, "--install", help="Write the snippet to .git/hooks/pre-commit."),
) -> None:
    """Print (or --install) a git pre-commit hook that flags a manual gone stale + broken citations.
    Keeps the committed manual honest without any LLM — pure drift + citation checks."""
    snippet = _HOOK_SNIPPET
    if not install:
        typer.echo(snippet)
        return
    git_hooks = Path(path).resolve() / ".git" / "hooks"
    if not git_hooks.parent.exists():
        typer.echo("Not a git repository (no .git/). Run `git init` first.", err=True)
        raise typer.Exit(1)
    target = git_hooks / "pre-commit"
    if target.exists():
        typer.echo(f"{target} already exists — add these lines manually:\n\n{snippet}", err=True)
        raise typer.Exit(1)
    git_hooks.mkdir(parents=True, exist_ok=True)
    target.write_text(snippet)
    target.chmod(0o755)
    typer.echo(f"Installed pre-commit hook -> {target}")


_HOOK_SNIPPET = """\
#!/bin/sh
# repo-manual: keep the committed manual honest. Drift + citation checks only (no LLM).
# Adjust the invocation below if `repo-manual` isn't on PATH (e.g. `uv run repo-manual`).
repo-manual stale --check || exit 1
repo-manual verify || exit 1
"""


@app.command()
def guide() -> None:
    """Print an onboarding guide for an AGENT (e.g. a fresh Claude Code session): your role as the
    narrator, the full workflow, and how to write a page. Give a new session: `repo-manual guide`."""
    typer.echo(_GUIDE)


_GUIDE = r"""repo-manual — guide for the agent driving it
=============================================

WHAT THIS IS
  An AI-authored, human-read orientation manual committed to a repo's `.repo-manual/`.
  YOU (the agent running this tool) are the NARRATOR. The tool scans the code, groups it into
  systems, and writes skeleton pages + a per-page brief; you write the prose. There is NO bundled
  LLM. The tool then tracks freshness and verifies your citations. Run commands as `repo-manual ...`
  (or `uv run repo-manual ...` if it's project-local).

DOCUMENT A REPO FROM SCRATCH
  1. repo-manual structure <repo>
       -> writes .repo-manual/structure.suggested.json (a package-based seed) + structure.brief.json.
  2. Author <repo>/.repo-manual/structure.json — group files into SYSTEMS: named groups by what the
     code DOES (cross-folder is fine), each {id, title, description, importance, files[], related[]}.
     Start from the suggested seed; MERGE modules that form one concept into one system.
  3. repo-manual generate <repo>            # one skeleton page per system
  4. For each pending page (`repo-manual plan <repo>` lists them):
       repo-manual brief <page-id> --path <repo>     # files + symbol outline + the rules
       Read the listed source files, then open
         <repo>/.repo-manual/manual/<section>/<page-id>.md
       and REPLACE the text between
         <!-- repo-manual:generated:start -->  and  <!-- repo-manual:generated:end -->
       with the chapter. NEVER touch the <!-- repo-manual:human:... --> region.
  5. repo-manual ingest <repo>              # pins each narrated page to its source
  6. repo-manual verify <repo> --strict     # every citation must resolve — fix any it flags
  7. repo-manual serve <repo>               # browse it (Ctrl-C to stop)

HOW TO WRITE A PAGE (the recipe — non-negotiable)
  - Ground ONLY in the page's relevant files. Never invent. If something isn't in the source, say so.
  - Cite every significant claim with a REAL line range:  `Sources: [path/to/file.py:START-END]()`
  - Lead with purpose + the mental model; progressive disclosure (overview -> detail).
  - Use Mermaid for diagrams (```mermaid then `graph TD`), tables for facts, a "Decisions & gotchas"
    section for what bites, and end with "How it connects".

KEEP IT FRESH (after the code changes)
  repo-manual stale <repo>          # STALE = drifted, PENDING = never written
  Re-narrate the stale pages (same brief -> rewrite -> ingest loop), then verify --strict.
  repo-manual hook --install <repo> # optional pre-commit gate (fails on stale / broken citation)

UNDERSTAND THE TOOL ITSELF
  repo-manual self-documents. In the repo-manual repo, run `repo-manual serve` (or read
  .repo-manual/manual/ — 7 systems, start at overview). Its CLAUDE.md lists commands + conventions.
"""


@app.command()
def serve(
    path: str = typer.Argument(".", help="Repo root."),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve on."),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open a browser tab."),
) -> None:
    """Serve an interactive browser view of the manual: sidebar nav by system, rendered Markdown +
    Mermaid, freshness badges, and drill-down to each system's functions. Stdlib server, no new deps."""
    import errno
    import functools
    import http.server
    import socketserver
    import webbrowser

    from repo_manual.viewer import VIEWER_NAME, write_viewer

    config = _load_or_init_config(path)
    if store.load_manual(config) is None:
        raise typer.Exit(_no_manual())
    write_viewer(config)

    class _Server(socketserver.TCPServer):
        allow_reuse_address = True  # don't trip over a just-stopped server stuck in TIME_WAIT

    # Serve from the repo root so the viewer reaches both .repo-manual/ and the source files it links to.
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(config.root))
    httpd = None
    for candidate in range(port, port + 20):  # a busy port shouldn't crash — find the next free one
        try:
            httpd = _Server(("127.0.0.1", candidate), handler)
            break
        except OSError as e:
            if e.errno != errno.EADDRINUSE:
                raise
    if httpd is None:
        typer.secho(
            f"No free port in {port}..{port + 19}. Free one up or pass --port.",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(1)

    actual = httpd.server_address[1]
    if actual != port:
        typer.secho(f"port {port} was busy — using {actual} instead", fg=typer.colors.YELLOW)
    url = f"http://127.0.0.1:{actual}/{config.output_dir}/{VIEWER_NAME}"
    typer.echo(f"Serving the manual at {url}\n(Ctrl-C to stop)")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 - headless / no browser is fine
            pass
    with httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            typer.echo("\nstopped")


def _no_manual() -> int:
    typer.echo("No manual found. Run `repo-manual generate` first.", err=True)
    return 1


if __name__ == "__main__":
    app()
