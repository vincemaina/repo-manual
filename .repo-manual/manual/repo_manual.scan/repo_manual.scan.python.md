---
id: repo_manual.scan.python
title: "repo_manual.scan.python"
section: repo_manual.scan
importance: medium
source: skeleton
status: pending
generated_at: null
related_pages: [repo_manual.config, repo_manual.hashing, repo_manual.model, repo_manual.scan.base]
relevant_files:
  - path: src/repo_manual/scan/python.py
    hash: ""
---

<!-- repo-manual:generated:start -->
<!-- repo-manual:pending  Orchestrator: replace this generated region with the page narrative.
     Read the relevant source files below (and plan.json, page id "repo_manual.scan.python"), then write
     the chapter per docs/generation-recipe.md: source-grounded, cite every claim
     (Sources: [file:Lstart-end]), vertical mermaid diagrams, progressive disclosure.
     Leave the human region untouched. -->

# repo_manual.scan.python

> _Skeleton — awaiting narrative. The facts below are deterministic; the prose is not yet written._

<details>
<summary>Relevant source files</summary>

- [`src/repo_manual/scan/python.py`](../../../src/repo_manual/scan/python.py)

</details>

## Symbols defined here

- `_Parsed  [L21-25]`
- `_ModuleSymbols  [L29-32] — Top-level name -> symbol id, used to resolve calls and `from x import name` bindings.`
- `PythonAnalyzer  [L35-251]`
- `PythonAnalyzer.analyze(self, config: ManualConfig) -> RepoIndex  [L39-59]`
- `PythonAnalyzer._parse_all(self, config: ManualConfig) -> list[_Parsed]  [L63-89]`
- `PythonAnalyzer._module_name(self, relpath: str, config: ManualConfig) -> str  [L91-102] — ``src/pkg/mod.py`` (source_dir ``src``) -> ``pkg.mod``; ``__init__.py`` -> the package.`
- `PythonAnalyzer._symbols_for(self, p: _Parsed) -> tuple[list[Symbol], _ModuleSymbols]  [L106-140]`
- `PythonAnalyzer._def_symbol(self, p: _Parsed, node: ast.AST, qualname: str, kind: SymbolKind) -> Symbol  [L142-156]`
- `PythonAnalyzer._import_edges(self, p: _Parsed, module_to_file: dict[str, str]) -> list[Edge]  [L160-178]`
- `PythonAnalyzer._resolve_from_module(self, current_module: str, node: ast.ImportFrom) -> str | None  [L180-190]`
- `PythonAnalyzer._nearest_internal_file(self, module: str, module_to_file: dict[str, str]) -> str | None  [L192-200] — Map a dotted module to an indexed file, walking up parents (``a.b.c`` -> ``a.b`` -> ``a``).`
- `PythonAnalyzer._call_edges(self, p: _Parsed, module_to_file: dict[str, str], top_tables: dict[str, _ModuleSymbols]) -> list[Edge]  [L204-239]`
- `PythonAnalyzer._callables(self, p: _Parsed) -> list[tuple[str, ast.AST]]  [L241-251] — Yield ``(symbol_id, body_node)`` for each function/method whose calls we attribute.`
- `_signature(node: ast.AST) -> str  [L257-270]`
- `_callee_name(func: ast.AST) -> str | None  [L273-279] — The simple name being called: ``f()`` -> ``f``; ``obj.method()`` -> ``method``.`
- `_first_line(text: str) -> str  [L282-284]`

## Connects to

- [repo_manual.config](../repo_manual/repo_manual.config.md)
- [repo_manual.hashing](../repo_manual/repo_manual.hashing.md)
- [repo_manual.model](../repo_manual/repo_manual.model.md)
- [repo_manual.scan.base](./repo_manual.scan.base.md)
<!-- repo-manual:generated:end -->

<!-- repo-manual:human:start -->
<!-- Human notes for this page are preserved across regeneration. Add yours below. -->
<!-- repo-manual:human:end -->
