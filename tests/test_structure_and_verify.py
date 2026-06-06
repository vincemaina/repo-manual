"""AI grouping (structure.json) + the citation validator."""

from __future__ import annotations

import json

from repo_manual import store, verify
from repo_manual.config import ManualConfig
from repo_manual.plan import SYSTEMS_SLUG, Structure, plan_from_structure
from repo_manual.scan import get_analyzer


def _index(config: ManualConfig):
    return get_analyzer("python").analyze(config)


def _structure() -> Structure:
    return Structure.from_dict(
        {
            "overview": {"description": "A tiny sample."},
            "systems": [
                {
                    "id": "core",
                    "title": "Core",
                    "description": "leaf + dependent",
                    "importance": "high",
                    "files": ["src/sample/a.py", "src/sample/b.py"],
                    "related": ["entry"],
                },
                {
                    "id": "entry",
                    "title": "Entry",
                    "files": ["src/sample/cli.py"],
                },
            ],
        }
    )


def test_structure_groups_files_into_systems(config):
    index = _index(config)
    manual, warnings = plan_from_structure(index, _structure())
    # one page per system, files can span what were separate modules
    core = manual.pages["core"]
    assert core.section == SYSTEMS_SLUG
    assert {r.path for r in core.relevant_files} == {"src/sample/a.py", "src/sample/b.py"}
    # __init__.py wasn't claimed -> swept into the ungrouped page, nothing lost
    assert "ungrouped" in manual.pages
    assert "src/sample/__init__.py" in {r.path for r in manual.pages["ungrouped"].relevant_files}
    assert any("not assigned" in w for w in warnings)


def test_missing_file_warns_not_crashes(config):
    index = _index(config)
    structure = Structure.from_dict(
        {"systems": [{"id": "x", "title": "X", "files": ["src/sample/nope.py"]}]}
    )
    manual, warnings = plan_from_structure(index, structure)
    assert manual.pages["x"].relevant_files == []
    assert any("not found" in w for w in warnings)


def test_generate_uses_structure_when_present(config):
    store.init_store(config)
    (config.output_path / store.STRUCTURE_NAME).write_text(
        json.dumps(
            {
                "systems": [
                    {"id": "core", "title": "Core", "files": ["src/sample/a.py", "src/sample/b.py"]},
                    {"id": "entry", "title": "Entry", "files": ["src/sample/cli.py"]},
                ]
            }
        )
    )
    index = _index(config)
    manual, _ = store.build_manual(config, index)
    assert "core" in manual.pages and manual.pages["core"].section == SYSTEMS_SLUG


# -- citation validator ----------------------------------------------------------------


def _narrate(config: ManualConfig, page_id: str, section: str, body: str) -> None:
    path = config.output_path / "manual" / section / f"{page_id}.md"
    text = path.read_text()
    before, rest = text.split(store.GEN_START, 1)
    _, after = rest.split(store.GEN_END, 1)
    path.write_text(f"{before}{store.GEN_START}\n{body}\n{store.GEN_END}{after}")


def _build_seed(config: ManualConfig):
    store.init_store(config)
    index = _index(config)
    manual, _ = store.build_manual(config, index)
    store.write_manual(config, index, manual)
    return index


def test_verify_passes_on_real_citations(config):
    _build_seed(config)
    _narrate(
        config,
        "sample.a",
        "sample",
        "# a\n\nThe helper doubles its input. `Sources: [src/sample/a.py:4-6]()`\n"
        "It also defines Thing. `Sources: [src/sample/a.py:9-15]()`",
    )
    store.ingest_filled_pages(config, store.load_manual(config), now="t")
    report = verify.verify_manual(config, store.load_manual(config))
    assert not report.has_problems
    assert report.citations_checked >= 2


def test_verify_flags_out_of_range_and_missing(config):
    _build_seed(config)
    _narrate(
        config,
        "sample.a",
        "sample",
        "# a\n\nBad range. `Sources: [src/sample/a.py:900-999]()`\n"
        "Missing file. `Sources: [src/sample/ghost.py:1-2]()`",
    )
    store.ingest_filled_pages(config, store.load_manual(config), now="t")
    report = verify.verify_manual(config, store.load_manual(config))
    assert report.has_problems
    msgs = " ".join(v.message for v in report.violations)
    assert "out of bounds" in msgs
    assert "not found" in msgs


def test_verify_strict_flags_thin_pages(config):
    _build_seed(config)
    _narrate(config, "sample.a", "sample", "# a\n\nNo citations at all here.")
    store.ingest_filled_pages(config, store.load_manual(config), now="t")
    report = verify.verify_manual(config, store.load_manual(config), strict=True)
    assert "sample.a" in report.thin_pages


# -- stale --check gate + brief --------------------------------------------------------


def test_stale_check_gate(config):
    from typer.testing import CliRunner

    from repo_manual.cli import app

    runner = CliRunner()
    _build_seed(config)
    _narrate(config, "sample.a", "sample", "# a\n\nNarrative. `Sources: [src/sample/a.py:1-5]()`")
    store.ingest_filled_pages(config, store.load_manual(config), now="t")

    # clean: --check passes (drifted pages only; pending pages don't fail by default)
    assert runner.invoke(app, ["stale", str(config.root), "--check"]).exit_code == 0

    # drift the narrated source -> --check fails
    src = config.root / "src" / "sample" / "a.py"
    src.write_text(src.read_text() + "\n# changed\n")
    assert runner.invoke(app, ["stale", str(config.root), "--check"]).exit_code == 1


def test_brief_outputs_grounding(config):
    from typer.testing import CliRunner

    from repo_manual.cli import app

    runner = CliRunner()
    _build_seed(config)
    result = runner.invoke(app, ["brief", "sample.b", "--path", str(config.root)])
    assert result.exit_code == 0
    assert "src/sample/b.py" in result.stdout
    assert "process" in result.stdout  # a symbol to cover
    assert "Sources:" in result.stdout  # the citation rule is stated


def test_viewer_written_and_self_contained(config):
    from repo_manual.viewer import VIEWER_NAME, write_viewer

    _build_seed(config)
    write_viewer(config)
    html = (config.output_path / VIEWER_NAME).read_text()
    # it's a real page that fetches the data the tool emits, with no Python/server templating
    assert "<!doctype html>" in html.lower()
    for hook in ("manual.json", "index/symbols.json", "index/edges.json", "index/files.json"):
        assert hook in html, hook
    assert "mermaid" in html and "cytoscape" in html


def test_graph_data_contract(config):
    """Audit the graph's inputs: every edge endpoint resolves to a real node, and every file reaches a
    page — so the rendered graph has no dangling nodes and every node can navigate to its page."""
    index = _index(config)
    manual, _ = store.build_manual(config, index)

    file_ids = {f.path for f in index.files}
    symbol_ids = {s.id for s in index.symbols}
    for e in index.edges:
        if e.kind.value == "imports":
            assert e.src in file_ids and e.dst in file_ids, e
        else:  # calls
            assert e.src in symbol_ids and e.dst in symbol_ids, e

    paged_files = {r.path for p in manual.pages.values() for r in p.relevant_files}
    assert file_ids <= paged_files  # every file is reachable from some page (click-to-navigate works)
