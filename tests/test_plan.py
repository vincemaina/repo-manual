"""Planner: sections/pages, importance heuristic, related pages, generation tasks."""

from __future__ import annotations

from repo_manual.model import Importance
from repo_manual.plan import OVERVIEW_ID, all_tasks, plan_manual
from repo_manual.scan import get_analyzer


def _plan(config):
    index = get_analyzer("python").analyze(config)
    return index, plan_manual(index)


def test_overview_first_and_entrypoint_grounded(config):
    _, manual = _plan(config)
    assert manual.sections[0].slug == "overview"
    overview = manual.pages[OVERVIEW_ID]
    # cli.py is an entry point -> the overview grounds in it
    assert "src/sample/cli.py" in [r.path for r in overview.relevant_files]
    assert overview.importance is Importance.HIGH


def test_one_page_per_module_in_package_section(config):
    _, manual = _plan(config)
    page_ids = set(manual.pages)
    assert {"sample.a", "sample.b", "sample.cli", "sample"} <= page_ids
    assert manual.pages["sample.a"].section == "sample"


def test_related_pages_follow_imports(config):
    _, manual = _plan(config)
    assert manual.pages["sample.b"].related_pages == ["sample.a"]
    assert manual.pages["sample.cli"].related_pages == ["sample.b"]


def test_cli_is_high_importance(config):
    _, manual = _plan(config)
    assert manual.pages["sample.cli"].importance is Importance.HIGH


def test_tasks_carry_grounding(config):
    index, manual = _plan(config)
    tasks = {t.page_id: t for t in all_tasks(index, manual)}
    b = tasks["sample.b"]
    assert b.relevant_files == ["src/sample/b.py"]
    assert any("process" in line for line in b.symbol_outline)
    assert "src/sample/a.py" in b.internal_deps
