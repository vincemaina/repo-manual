"""Analyzer: symbols, internal import edges, and best-effort call edges."""

from __future__ import annotations

from repo_manual.model import EdgeKind, SymbolKind
from repo_manual.scan import get_analyzer


def _index(config):
    return get_analyzer("python").analyze(config)


def test_finds_all_source_files(config):
    index = _index(config)
    paths = {f.path for f in index.files}
    assert paths == {
        "src/sample/__init__.py",
        "src/sample/a.py",
        "src/sample/b.py",
        "src/sample/cli.py",
    }
    assert all(f.content_hash.startswith("sha256:") for f in index.files)


def test_symbol_kinds_and_qualnames(config):
    index = _index(config)
    by_qual = {(s.file, s.qualname): s for s in index.symbols}
    a = "src/sample/a.py"
    assert by_qual[(a, "sample.a")].kind is SymbolKind.MODULE
    assert by_qual[(a, "helper")].kind is SymbolKind.FUNCTION
    assert by_qual[(a, "Thing")].kind is SymbolKind.CLASS
    assert by_qual[(a, "Thing.run")].kind is SymbolKind.METHOD
    assert by_qual[(a, "helper")].signature == "(x)"
    assert by_qual[(a, "helper")].docstring == "Return x doubled."


def test_internal_import_edges(config):
    index = _index(config)
    imports = {(e.src, e.dst) for e in index.edges if e.kind is EdgeKind.IMPORTS}
    assert ("src/sample/b.py", "src/sample/a.py") in imports
    assert ("src/sample/cli.py", "src/sample/b.py") in imports
    # no edge to a non-existent / external module
    assert all(dst.startswith("src/sample/") for _, dst in imports)


def test_call_edges_resolve_across_files(config):
    index = _index(config)
    calls = {(e.src, e.dst) for e in index.edges if e.kind is EdgeKind.CALLS}
    # b.process calls helper and the Thing constructor (both names imported from a)
    assert ("src/sample/b.py::process", "src/sample/a.py::helper") in calls
    assert ("src/sample/b.py::process", "src/sample/a.py::Thing") in calls
    # cli.main calls process (imported from b)
    assert ("src/sample/cli.py::main", "src/sample/b.py::process") in calls
    # Thing.run calls helper (same module, top-level name)
    assert ("src/sample/a.py::Thing.run", "src/sample/a.py::helper") in calls
    # an instance-method call (t.run()) is NOT guessed — we never invent unresolved edges
    assert ("src/sample/b.py::process", "src/sample/a.py::Thing.run") not in calls


def test_deterministic_ordering(config):
    a = _index(config)
    b = _index(config)
    assert a.to_dict() == b.to_dict()
