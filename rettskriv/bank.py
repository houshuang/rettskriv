"""Target word banks: every form the modern norm allows, with coarse tags.

Built from Norsk ordbank (Språkbanken, CC BY 4.0): bokmål 2005 and nynorsk 2012.
A form maps to the set of coarse tags it can carry, e.g. {"verb:inf", "subst"}.
"""
from __future__ import annotations

import pickle
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORDBANK = ROOT / "data" / "ordbank"
CACHE = ROOT / "data" / "cache"

SOURCES = {
    "nob": ORDBANK / "20220201_norsk_ordbank_nob_2005" / "fullformsliste.txt",
    "nno": ORDBANK / "20220201_norsk_ordbank_nno_2012" / "fullformer_2012.txt",
}

VERB_FORMS = ("inf", "pres", "pret", "imp", "perf-part", "pass")


def coarse(tag: str) -> str:
    parts = tag.split()
    pos = parts[0]
    if pos == "verb":
        for form in VERB_FORMS:
            if form in parts:
                return f"verb:{form}"
        return "verb"
    if pos == "subst":
        return "prop" if "prop" in parts else "subst"
    if pos == "adj" and "<perf-part>" in parts:
        return "adj:part"
    return pos


def _build(lang: str) -> dict[str, frozenset[str]]:
    if not SOURCES[lang].exists():
        raise FileNotFoundError(f"{SOURCES[lang]} is missing: run python3 -m rettskriv.fetch_ordbank")
    forms: dict[str, set[str]] = {}
    with open(SOURCES[lang], encoding="latin-1") as handle:
        next(handle)
        for line in handle:
            cols = line.rstrip("\r\n").split("\t")
            if len(cols) < 4:
                continue
            form = cols[2]
            forms.setdefault(form, set()).add(coarse(cols[3]))
    return {form: frozenset(tags) for form, tags in forms.items()}


@lru_cache(maxsize=None)
def load(lang: str) -> dict[str, frozenset[str]]:
    """Form (case as in the bank: proper nouns capitalised) -> coarse tags."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"bank-{lang}.pickle"
    source = SOURCES[lang]
    if cache.exists() and (not source.exists() or cache.stat().st_mtime >= source.stat().st_mtime):
        with open(cache, "rb") as handle:
            return pickle.load(handle)
    forms = _build(lang)
    with open(cache, "wb") as handle:
        pickle.dump(forms, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return forms


class Bank:
    def __init__(self, lang: str):
        self.lang = lang
        self.forms = load(lang)
        lower: dict[str, set[str]] = {}
        for form, tags in self.forms.items():
            lower.setdefault(form.lower(), set()).update(tags)
        self.lower = {form: frozenset(tags) for form, tags in lower.items()}

    def tags(self, word: str) -> frozenset[str]:
        return self.lower.get(word.lower(), frozenset())

    def __contains__(self, word: str) -> bool:
        return word.lower() in self.lower

    def common(self, word: str) -> bool:
        """A lower-case (non-proper) entry exists."""
        tags = self.tags(word)
        return bool(tags - {"prop"})

    def proper_only(self, word: str) -> bool:
        tags = self.tags(word)
        return tags == frozenset({"prop"})
