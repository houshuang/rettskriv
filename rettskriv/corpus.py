"""Reading the Lesebok editions (bookifier/lesebok/work/<book>/book.json), read-only."""
from __future__ import annotations

import json
import re
from pathlib import Path

LESEBOK = Path("/Users/stian/src/bookifier/lesebok/work")

LANGUAGE = {"dansk-norsk": "nob", "landsmaal": "nno"}

MARKERS = {
    "nob": {"jeg", "ikke", "hvad", "hun", "mig", "dig", "sig", "af", "efter", "nu", "hvor", "kunde", "havde", "blev"},
    "nno": {"eg", "ikkje", "kva", "ho", "meg", "deg", "seg", "av", "etter", "no", "kvar", "hev", "vart", "dei", "ein", "eit"},
    "sv": {"och", "icke", "jag", "är", "hvad", "hon", "mig", "sig", "af", "efter", "nu", "ej", "honom", "också", "skulle"},
    "de": {"und", "ich", "nicht", "ist", "der", "die", "das", "sie", "mit", "auf", "für"},
    "en": {"the", "and", "of", "to", "is", "that", "with", "was", "his"},
    "la": {"et", "est", "in", "non", "quod", "ad", "cum", "sed", "ut"},
}
DECISIVE = {
    "sv": {"och", "är", "också", "icke"},
    "de": {"und", "ich", "nicht", "ist"},
    "en": {"the", "and", "of"},
    "nno": {"eg", "ikkje", "kva", "ein", "eit", "dei", "ho", "korleis", "kvar"},
}
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def books() -> list[str]:
    return sorted(p.parent.name for p in LESEBOK.glob("*/book.json"))


def load(book: str) -> dict:
    with open(LESEBOK / book / "book.json", encoding="utf-8") as handle:
        return json.load(handle)


def detect(text: str, default: str) -> str:
    """The language of a piece, from function-word markers. Returns default when unclear."""
    words = [w.lower() for w in WORD.findall(text)]
    if len(words) < 8:
        return default
    counts = {lang: sum(1 for w in words if w in marks) for lang, marks in MARKERS.items()}
    decisive = {lang: sum(1 for w in words if w in marks) for lang, marks in DECISIVE.items()}
    for lang in ("sv", "de", "en"):
        if decisive[lang] >= 2 and counts[lang] > counts[default]:
            return lang
    if default == "nob" and decisive["nno"] >= 3 and counts["nno"] > counts["nob"]:
        return "nno"
    if default == "nno" and counts["nob"] > 2 * counts["nno"] + 3:
        return "nob"
    return default
