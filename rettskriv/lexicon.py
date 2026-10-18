"""Curated lexicon: decisions about specific old forms.

CSV columns: source, target, when, note, origin.

- source: the old form, lower case.
- target: the modern form, lower case, or "=" for "leave as printed".
- when: empty (always) or clauses joined by ";", all of which must hold:
    nouncaps           the book capitalises common nouns (so a lower-case word is no noun)
    nonouncaps         the book does not
    before=YYYY        the book was printed before that year
    cap / lower        the token is capitalised / lower case
    mid / initial      the token is mid-sentence / sentence- or line-initial
    prev=a|b           the previous word (lower case, as printed) is one of these
    next=a|b           the next word is one of these (prev/next stop at punctuation)
    nextany=a|b        the next word, even across punctuation
    nextbreak=a|b      the next word, with punctuation between
    notprev2=a|b       the word before the previous one is none of these
    prevout=a|b        the previous word's modern form is one of these
    nextout=a|b        the next word's modern form is one of these
    nexttags=t|u       every bank tag of the next word's modern form is one of these
    prevtags=t|u       likewise for the previous word
    nexthas=t|u        the next word's modern form has at least one of these tags
    prevhas=t|u        likewise for the previous word
    notnext=a|b / notprev=a|b
- Rows for one source are tried in file order; the first match wins. A source that
  has rows but no matching row is left as printed: listing a word means only its
  listed readings may be changed.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEXICON = ROOT / "lexicon"

CONTEXT_KEYS = {"prevout", "nextout", "nexttags", "prevtags", "nexthas", "prevhas"}


@dataclass(frozen=True)
class Entry:
    source: str
    target: str
    when: tuple[tuple[str, frozenset[str] | None], ...]
    note: str
    origin: str
    line: str

    @property
    def keep(self) -> bool:
        return self.target == "="

    @property
    def contextual(self) -> bool:
        return any(key in CONTEXT_KEYS for key, _ in self.when)


def parse_when(text: str) -> tuple[tuple[str, frozenset[str] | None], ...]:
    clauses = []
    for clause in filter(None, (c.strip() for c in text.split(";"))):
        if "=" in clause:
            key, values = clause.split("=", 1)
            clauses.append((key.strip(), frozenset(v.strip() for v in values.split("|"))))
        else:
            clauses.append((clause, None))
    return tuple(clauses)


def load(lang: str) -> dict[str, list[Entry]]:
    entries: dict[str, list[Entry]] = {}
    folder = LEXICON / {"nob": "bokmal", "nno": "nynorsk"}[lang]
    # homograph.csv (forms with a second reading) is authoritative for its forms; other
    # curated files follow; audit.csv (generated) only adds forms no curated file covers.
    paths = sorted(folder.glob("*.csv"), key=lambda p: (p.name != "homograph.csv", p.name == "audit.csv", p.name))
    screened: set[str] = set()
    for path in paths:
        curated = set(entries) if path.name == "audit.csv" else screened
        with open(path, newline="", encoding="utf-8") as handle:
            for number, row in enumerate(csv.DictReader(handle), start=2):
                source = row["source"].strip()
                if not source or source.startswith("#"):
                    continue
                if source.lower() in curated:
                    continue
                entry = Entry(
                    source=source.lower(),
                    target=row["target"].strip(),
                    when=parse_when(row.get("when") or ""),
                    note=(row.get("note") or "").strip(),
                    origin=(row.get("origin") or "").strip(),
                    line=f"{path.name}:{number}",
                )
                rows = entries.setdefault(entry.source, [])
                if any(e.when == entry.when for e in rows):
                    raise ValueError(f"{entry.line}: duplicate row for {entry.source!r}")
                rows.append(entry)
        if path.name == "homograph.csv":
            screened = set(entries)
    return entries
