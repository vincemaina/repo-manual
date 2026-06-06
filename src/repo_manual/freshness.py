"""Freshness — the wedge. Each narrated page pins the content-hash of every source file it was
written against; this module re-hashes those files on disk and reports drift. A page is:

* ``PENDING`` — never narrated (still a skeleton),
* ``FRESH``   — narrated and every ``relevant_file`` hash still matches,
* ``STALE``   — narrated but a ``relevant_file`` changed (or vanished) since.

Only ``STALE`` (and ``PENDING``) pages need an orchestrator to (re)write them; ``FRESH`` pages are left
untouched — that's how regeneration stays cheap and human edits survive.
"""

from __future__ import annotations

from pathlib import Path

from repo_manual.hashing import hash_file
from repo_manual.model import Manual, Page, PageSource, PageStatus


def current_hash(root: Path, relpath: str) -> str | None:
    """Hash a source file as it exists on disk now, or ``None`` if it no longer exists."""
    path = root / relpath
    if not path.exists():
        return None
    return hash_file(path)


def page_status(root: Path, page: Page) -> PageStatus:
    """Re-evaluate one page's freshness against the working tree (does not mutate the page)."""
    if page.source is PageSource.SKELETON:
        return PageStatus.PENDING
    for ref in page.relevant_files:
        if current_hash(root, ref.path) != ref.hash:
            return PageStatus.STALE
    return PageStatus.FRESH


def refresh(root: Path, manual: Manual) -> dict[str, PageStatus]:
    """Recompute and write back every page's ``status``. Returns the {page_id: status} map."""
    statuses: dict[str, PageStatus] = {}
    for pid, page in manual.pages.items():
        status = page_status(root, page)
        page.status = status
        statuses[pid] = status
    return statuses


def stale_pages(manual: Manual) -> list[Page]:
    """Pages an orchestrator still owes work on: never narrated (PENDING) or drifted (STALE)."""
    return [p for p in manual.ordered_pages() if p.status in (PageStatus.PENDING, PageStatus.STALE)]
