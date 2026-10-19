"""Target word banks: every form the modern norm allows, with coarse tags.

Built from Norsk ordbank (Språkbanken, CC BY 4.0): bokmål 2005 and nynorsk 2012.
A form maps to the set of coarse tags it can carry, e.g. {"verb:inf", "subst"}.
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass
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
        if "pass" in parts:
            return "verb:pass"
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
    cache = CACHE / f"bank-v2-{lang}.pickle"
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

    def analyses(self, word: str) -> tuple[Analysis, ...]:
        return morphology(self.lang)[0].get(word.lower(), ())

    def inflect(self, word: str, source_tag: str, target_tag: str) -> frozenset[str]:
        _, paradigms = morphology(self.lang)
        forms = set()
        for analysis in self.analyses(word):
            if coarse(analysis.tags) == source_tag:
                forms.update(paradigms.get((analysis.lemma, analysis.paradigm, target_tag), ()))
        return frozenset(forms)

    def tags(self, word: str) -> frozenset[str]:
        return self.lower.get(word.lower(), frozenset())

    def syntax_tags(self, word: str) -> frozenset[str]:
        """Tags for infinitive-marker conditions, retaining passive infinitives.

        Inflection uses the active-only coarse tags: treating a passive as an
        active infinitive there would turn ``de bruges`` into an active verb.
        """
        tags = self.tags(word)
        if "verb:pass" in tags:
            passive = [a for a in self.analyses(word) if "pass" in a.tags.split()]
            if passive and all("inf" in a.tags.split() for a in passive):
                return (tags - {"verb:pass"}) | {"verb:inf"}
        return tags

    def __contains__(self, word: str) -> bool:
        return word.lower() in self.lower

    def common(self, word: str) -> bool:
        """A lower-case (non-proper) entry exists."""
        tags = self.tags(word)
        return bool(tags - {"prop"})

    def proper_only(self, word: str) -> bool:
        tags = self.tags(word)
        return tags == frozenset({"prop"})


@dataclass(frozen=True, slots=True)
class Analysis:
    """An Ordbank analysis, retaining lemma and paradigm identity and all tags."""
    lemma: str
    paradigm: str
    tags: str


@lru_cache(maxsize=2)
def morphology(lang: str):
    """Read full analyses lazily; surface spelling alone cannot identify a lemma."""
    import sys
    analyses = {}
    verbs = {}
    with open(SOURCES[lang], encoding="latin-1") as handle:
        next(handle)
        for line in handle:
            cols = line.rstrip("\r\n").split("\t")
            if len(cols) < 5:
                raise ValueError(f"malformed Ordbank row: {line[:80]!r}")
            form = sys.intern(cols[2].lower())
            analysis = Analysis(sys.intern(cols[1]), sys.intern(cols[4]), sys.intern(cols[3]))
            analyses.setdefault(form, []).append(analysis)
            tag = coarse(analysis.tags)
            if tag.startswith("verb:"):
                verbs.setdefault((analysis.lemma, analysis.paradigm, tag), set()).add(form)
            parts = analysis.tags.split()
            if tag == "adj:part" and ("fl" in parts or "be" in parts):
                verbs.setdefault((analysis.lemma, analysis.paradigm, "adj:part:agreeing"), set()).add(form)
    return ({form: tuple(rows) for form, rows in analyses.items()},
            {key: frozenset(forms) for key, forms in verbs.items()})
