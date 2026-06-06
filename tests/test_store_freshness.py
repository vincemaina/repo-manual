"""Store + freshness: skeleton writing, narrative/human preservation, drift, and ingest."""

from __future__ import annotations

from pathlib import Path

from repo_manual import freshness, store
from repo_manual.config import ManualConfig
from repo_manual.model import PageSource, PageStatus
from repo_manual.plan import plan_manual
from repo_manual.scan import get_analyzer


def _generate(config: ManualConfig):
    store.init_store(config)
    index = get_analyzer("python").analyze(config)
    manual = plan_manual(index)
    result = store.write_manual(config, index, manual)
    return index, manual, result


def _page_file(config: ManualConfig, page_id: str, section: str) -> Path:
    return config.output_path / "manual" / section / f"{page_id}.md"


def _fill_page(path: Path, prose: str) -> None:
    """Simulate an orchestrator narrating a page: replace the generated region body."""
    text = path.read_text()
    before, rest = text.split(store.GEN_START, 1)
    _, after = rest.split(store.GEN_END, 1)
    path.write_text(f"{before}{store.GEN_START}\n{prose}\n{store.GEN_END}{after}")


def test_generate_writes_skeletons(config):
    _, _, result = _generate(config)
    assert result.skeletons_written == result.pages_total
    assert result.narratives_preserved == 0
    assert result.pending == result.pages_total
    page = _page_file(config, "sample.a", "sample")
    assert store.PENDING_MARKER in page.read_text()


def test_ingest_promotes_filled_page(config):
    _generate(config)
    page = _page_file(config, "sample.a", "sample")
    _fill_page(page, "# a\n\nReal narrative grounded in source. Sources: [src/sample/a.py:1-20]()")

    manual = store.load_manual(config)
    promoted = store.ingest_filled_pages(config, manual, now="2026-06-06T00:00:00+00:00")
    assert promoted == ["sample.a"]

    manual = store.load_manual(config)
    p = manual.pages["sample.a"]
    assert p.source is PageSource.GENERATED
    assert p.status is PageStatus.FRESH
    assert p.relevant_files[0].hash.startswith("sha256:")

    # the .md frontmatter mirror is kept in sync with manual.json after ingest
    fm = page.read_text().split("---", 2)[1]
    assert "source: generated" in fm
    assert "sha256:" in fm


def test_regenerate_preserves_narrative_and_human_edits(config):
    _generate(config)
    page = _page_file(config, "sample.a", "sample")
    _fill_page(page, "# a\n\nHand/agent-written prose.")
    # add a human note inside the human region
    text = page.read_text()
    text = text.replace(store.HUMAN_END, "My private note.\n" + store.HUMAN_END)
    page.write_text(text)

    store.ingest_filled_pages(config, store.load_manual(config), now="2026-06-06T00:00:00+00:00")

    # regenerate from scratch
    _generate(config)
    after = page.read_text()
    assert "Hand/agent-written prose." in after  # narrative kept
    assert store.PENDING_MARKER not in after  # not reverted to skeleton
    assert "My private note." in after  # human region survived
    p = store.load_manual(config).pages["sample.a"]
    assert p.source is PageSource.GENERATED
    # frontmatter status mirrors the post-refresh state in manual.json (not the pre-refresh default)
    assert "status: fresh" in after.split("---", 2)[1]


def test_source_change_marks_stale(config):
    _generate(config)
    page = _page_file(config, "sample.a", "sample")
    _fill_page(page, "# a\n\nNarrative.")
    store.ingest_filled_pages(config, store.load_manual(config), now="2026-06-06T00:00:00+00:00")

    manual = store.load_manual(config)
    assert freshness.page_status(config.root, manual.pages["sample.a"]) is PageStatus.FRESH

    # mutate the underlying source file
    src = config.root / "src" / "sample" / "a.py"
    src.write_text(src.read_text() + "\n# a change\n")

    manual = store.load_manual(config)
    statuses = freshness.refresh(config.root, manual)
    assert statuses["sample.a"] is PageStatus.STALE
    assert "sample.a" in {p.id for p in freshness.stale_pages(manual)}


def test_stale_page_returns_to_fresh_after_rewrite(config):
    _generate(config)
    page = _page_file(config, "sample.a", "sample")
    _fill_page(page, "# a\n\nOriginal narrative.")
    store.ingest_filled_pages(config, store.load_manual(config), now="t0")

    # drift the source -> stale
    src = config.root / "src" / "sample" / "a.py"
    src.write_text(src.read_text() + "\n# changed\n")
    assert freshness.refresh(config.root, store.load_manual(config))["sample.a"] is PageStatus.STALE

    # ingest WITHOUT rewriting must NOT mark it fresh (the prose wasn't updated)
    assert store.ingest_filled_pages(config, store.load_manual(config), now="t1") == []
    assert freshness.refresh(config.root, store.load_manual(config))["sample.a"] is PageStatus.STALE

    # rewrite the page, then ingest -> re-pinned to FRESH
    _fill_page(page, "# a\n\nUpdated narrative covering the change.")
    assert store.ingest_filled_pages(config, store.load_manual(config), now="t2") == ["sample.a"]
    assert freshness.refresh(config.root, store.load_manual(config))["sample.a"] is PageStatus.FRESH


def test_deleted_source_is_stale_not_crash(config):
    _generate(config)
    page = _page_file(config, "sample.a", "sample")
    _fill_page(page, "# a\n\nNarrative.")
    store.ingest_filled_pages(config, store.load_manual(config), now="2026-06-06T00:00:00+00:00")

    (config.root / "src" / "sample" / "a.py").unlink()
    manual = store.load_manual(config)
    statuses = freshness.refresh(config.root, manual)
    assert statuses["sample.a"] is PageStatus.STALE
