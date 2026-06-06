"""Language analyzers: turn a repo's source into a `RepoIndex`. Python ships first; the
`LanguageAnalyzer` protocol keeps TypeScript (tree-sitter) addable without touching the core."""

from repo_manual.scan.base import LanguageAnalyzer, get_analyzer

__all__ = ["LanguageAnalyzer", "get_analyzer"]
