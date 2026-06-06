"""The Python analyzer: parse every ``.py`` file with the stdlib ``ast`` and emit a deterministic
`RepoIndex` of modules/classes/functions/methods (symbols), internal ``import`` edges, and best-effort
internal ``calls`` edges. Best-effort means: we only record a call edge when the callee resolves to a
symbol we actually indexed (same file, or imported via ``from internal.mod import name``). External and
dynamic calls are dropped rather than guessed — the grounding stays accurate, never invented.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from repo_manual.config import ManualConfig
from repo_manual.hashing import hash_text
from repo_manual.model import Edge, EdgeKind, RepoIndex, SourceFile, Symbol, SymbolKind
from repo_manual.scan.base import iter_source_files


@dataclass
class _Parsed:
    relpath: str
    module: str  # dotted module name, e.g. "pkg.sub.mod"
    tree: ast.Module
    source_file: SourceFile


@dataclass
class _ModuleSymbols:
    """Top-level name -> symbol id, used to resolve calls and `from x import name` bindings."""

    by_name: dict[str, str] = field(default_factory=dict)


class PythonAnalyzer:
    language = "python"
    file_suffixes = (".py",)

    def analyze(self, config: ManualConfig) -> RepoIndex:
        parsed = self._parse_all(config)
        module_to_file = {p.module: p.relpath for p in parsed}

        index = RepoIndex()
        # Pass 1: symbols (and remember each module's top-level name table for resolution).
        top_tables: dict[str, _ModuleSymbols] = {}
        for p in parsed:
            index.files.append(p.source_file)
            mod_sym, table = self._symbols_for(p)
            index.symbols.extend(mod_sym)
            top_tables[p.relpath] = table

        # Pass 2: edges (imports + calls), now that every symbol is known.
        for p in parsed:
            index.edges.extend(self._import_edges(p, module_to_file))
            index.edges.extend(self._call_edges(p, module_to_file, top_tables))

        index.symbols.sort(key=lambda s: (s.file, s.line_start, s.qualname))
        index.edges.sort(key=lambda e: (e.kind.value, e.src, e.dst, e.dst_name))
        return index

    # -- parsing -----------------------------------------------------------------------

    def _parse_all(self, config: ManualConfig) -> list[_Parsed]:
        out: list[_Parsed] = []
        for path in iter_source_files(config, self.file_suffixes):
            text = path.read_text(encoding="utf-8")
            relpath = path.relative_to(config.root).as_posix()
            try:
                tree = ast.parse(text, filename=relpath)
            except SyntaxError:
                # A file we can't parse still exists and matters for freshness; index it without symbols.
                out.append(
                    _Parsed(
                        relpath=relpath,
                        module=self._module_name(relpath, config),
                        tree=ast.Module(body=[], type_ignores=[]),
                        source_file=SourceFile(relpath, "python", hash_text(text), text.count("\n") + 1),
                    )
                )
                continue
            out.append(
                _Parsed(
                    relpath=relpath,
                    module=self._module_name(relpath, config),
                    tree=tree,
                    source_file=SourceFile(relpath, "python", hash_text(text), text.count("\n") + 1),
                )
            )
        return out

    def _module_name(self, relpath: str, config: ManualConfig) -> str:
        """``src/pkg/mod.py`` (source_dir ``src``) -> ``pkg.mod``; ``__init__.py`` -> the package."""
        rel = relpath
        for src_dir in sorted(config.source_dirs, key=len, reverse=True):
            prefix = src_dir.rstrip("/") + "/"
            if rel.startswith(prefix):
                rel = rel[len(prefix) :]
                break
        parts = rel[:-3].split("/")  # strip ".py"
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    # -- symbols -----------------------------------------------------------------------

    def _symbols_for(self, p: _Parsed) -> tuple[list[Symbol], _ModuleSymbols]:
        symbols: list[Symbol] = []
        table = _ModuleSymbols()

        module_doc = _first_line(ast.get_docstring(p.tree) or "")
        module_id = f"{p.relpath}::{p.module or Path(p.relpath).stem}"
        last_line = max((getattr(n, "end_lineno", 1) or 1) for n in p.tree.body) if p.tree.body else 1
        symbols.append(
            Symbol(
                id=module_id,
                kind=SymbolKind.MODULE,
                name=p.module.split(".")[-1] if p.module else Path(p.relpath).stem,
                qualname=p.module or Path(p.relpath).stem,
                file=p.relpath,
                line_start=1,
                line_end=last_line,
                docstring=module_doc,
            )
        )

        for node in p.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym = self._def_symbol(p, node, node.name, SymbolKind.FUNCTION)
                symbols.append(sym)
                table.by_name[node.name] = sym.id
            elif isinstance(node, ast.ClassDef):
                cls_sym = self._def_symbol(p, node, node.name, SymbolKind.CLASS)
                symbols.append(cls_sym)
                table.by_name[node.name] = cls_sym.id
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append(
                            self._def_symbol(p, sub, f"{node.name}.{sub.name}", SymbolKind.METHOD)
                        )
        return symbols, table

    def _def_symbol(self, p: _Parsed, node: ast.AST, qualname: str, kind: SymbolKind) -> Symbol:
        name = qualname.split(".")[-1]
        return Symbol(
            id=f"{p.relpath}::{qualname}",
            kind=kind,
            name=name,
            qualname=qualname,
            file=p.relpath,
            line_start=getattr(node, "lineno", 1),
            line_end=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            signature=_signature(node),
            docstring=_first_line(ast.get_docstring(node) or "")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            else "",
        )

    # -- import edges ------------------------------------------------------------------

    def _import_edges(self, p: _Parsed, module_to_file: dict[str, str]) -> list[Edge]:
        edges: list[Edge] = []
        seen: set[str] = set()
        for node in ast.walk(p.tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = self._resolve_from_module(p.module, node)
                if base is None:
                    continue
                # `from pkg import mod` may name a submodule OR a symbol; try the submodule form too.
                targets = [base] + [f"{base}.{alias.name}" for alias in node.names]
            for mod in targets:
                dst = self._nearest_internal_file(mod, module_to_file)
                if dst and dst != p.relpath and dst not in seen:
                    seen.add(dst)
                    edges.append(Edge(EdgeKind.IMPORTS, p.relpath, dst))
        return edges

    def _resolve_from_module(self, current_module: str, node: ast.ImportFrom) -> str | None:
        if not node.level:
            return node.module or ""
        # Relative import: climb `level` packages up from the current module's package.
        pkg_parts = current_module.split(".")[:-1]  # current module's package
        if node.level - 1 > len(pkg_parts):
            return None
        base = pkg_parts[: len(pkg_parts) - (node.level - 1)]
        if node.module:
            base = base + node.module.split(".")
        return ".".join(base)

    def _nearest_internal_file(self, module: str, module_to_file: dict[str, str]) -> str | None:
        """Map a dotted module to an indexed file, walking up parents (``a.b.c`` -> ``a.b`` -> ``a``)."""
        parts = module.split(".")
        while parts:
            candidate = ".".join(parts)
            if candidate in module_to_file:
                return module_to_file[candidate]
            parts = parts[:-1]
        return None

    # -- call edges --------------------------------------------------------------------

    def _call_edges(
        self,
        p: _Parsed,
        module_to_file: dict[str, str],
        top_tables: dict[str, _ModuleSymbols],
    ) -> list[Edge]:
        # Resolution table for THIS module: same-file top-level names + imported internal names.
        resolve: dict[str, str] = dict(top_tables.get(p.relpath, _ModuleSymbols()).by_name)
        for node in ast.walk(p.tree):
            if isinstance(node, ast.ImportFrom):
                base = self._resolve_from_module(p.module, node)
                if base is None:
                    continue
                dst_file = self._nearest_internal_file(base, module_to_file)
                if not dst_file:
                    continue
                imported = top_tables.get(dst_file, _ModuleSymbols()).by_name
                for alias in node.names:
                    if alias.name in imported:
                        bound = alias.asname or alias.name
                        resolve.setdefault(bound, imported[alias.name])

        edges: list[Edge] = []
        seen: set[tuple[str, str]] = set()
        for caller, body in self._callables(p):
            for sub in ast.walk(body):
                if not isinstance(sub, ast.Call):
                    continue
                callee = _callee_name(sub.func)
                if callee and callee in resolve:
                    dst = resolve[callee]
                    key = (caller, dst)
                    if caller != dst and key not in seen:
                        seen.add(key)
                        edges.append(Edge(EdgeKind.CALLS, caller, dst, dst_name=callee))
        return edges

    def _callables(self, p: _Parsed) -> list[tuple[str, ast.AST]]:
        """Yield ``(symbol_id, body_node)`` for each function/method whose calls we attribute."""
        out: list[tuple[str, ast.AST]] = []
        for node in p.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append((f"{p.relpath}::{node.name}", node))
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out.append((f"{p.relpath}::{node.name}.{sub.name}", sub))
        return out


# -- small ast helpers -----------------------------------------------------------------


def _signature(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ""
    try:
        args = ast.unparse(node.args)
    except Exception:  # pragma: no cover - defensive; unparse is reliable on 3.12
        args = ""
    ret = ""
    if node.returns is not None:
        try:
            ret = f" -> {ast.unparse(node.returns)}"
        except Exception:  # pragma: no cover
            ret = ""
    return f"({args}){ret}"


def _callee_name(func: ast.AST) -> str | None:
    """The simple name being called: ``f()`` -> ``f``; ``obj.method()`` -> ``method``."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _first_line(text: str) -> str:
    line = text.strip().splitlines()[0].strip() if text.strip() else ""
    return line
