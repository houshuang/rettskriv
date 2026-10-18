"""Compound proposals for forms no rule or lexicon row decides.

A form is split into a first element (with an optional linking -s- or -e-) and a head,
each of which already has a context-free modern form that the bank lists as a common
word. When every split gives the same result, that result is the proposal. Proposals
are about nine in ten right, so they go to the auditors as candidates and never into
text by themselves.
"""
from __future__ import annotations

from rettskriv.engine import Engine

LINKS = ("", "s", "e")


def proposal(engine: Engine, form: str) -> str | None:
    results = set()
    for i in range(3, len(form) - 3):
        first, head = form[:i], form[i:]
        modern_head = engine.modern_lower(head)
        if not modern_head or not engine.bank.common(modern_head):
            continue
        for link in LINKS:
            if link and not first.endswith(link):
                continue
            stem = first[: len(first) - len(link)]
            if len(stem) < 3:
                continue
            modern_stem = engine.modern_lower(stem)
            if modern_stem and engine.bank.common(modern_stem):
                results.add(modern_stem + link + modern_head)
    return results.pop() if len(results) == 1 else None
