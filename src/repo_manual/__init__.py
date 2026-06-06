"""repo-manual: an AI-authored, human-read orientation manual that lives in the repo.

The package is split into a deterministic core (scan -> plan -> store, no LLM) and an
orchestrator-facing seam (`GenerationTask` packets + content-preserving page regions) that
the agent running this tool fills with narrative. See docs/architecture.md.
"""

__version__ = "0.1.0"
