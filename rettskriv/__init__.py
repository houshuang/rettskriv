"""Mechanical spelling modernisation of historical Norwegian.

    from rettskriv import modernise
    modernise("Han gik ud af Huset.")            # 'Han gikk ut av huset.'
    modernise("Eg hev set det.", lang="nno")     # landsmål -> nynorsk

See README.md for what it does and does not do.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache

from .engine import Engine, Result

__all__ = ["Engine", "Result", "engine", "book_engine", "modernise", "modernise_result", "prepare"]


@lru_cache(maxsize=None)
def _resources(lang: str = "nob") -> Engine:
    """A shared engine for "nob" (riksmål/Dano-Norwegian -> bokmål) or "nno"
    (landsmål -> nynorsk). Loading takes a few seconds the first time."""
    return Engine(lang)


def engine(lang: str = "nob") -> Engine:
    """Return isolated book state sharing the read-only linguistic resources."""
    from copy import copy
    eng = copy(_resources(lang))
    eng.names = set()
    eng.nouncaps = False
    eng.year = None
    eng._cand = {}
    return eng


def book_engine(texts: list[str], lang: str = "nob", *, year: int | None = None,
                nouncaps: bool | None = None) -> Engine:
    """Analyse book context once; reuse this engine for its paragraphs."""
    eng = engine(lang)
    eng.learn_book(texts)
    eng.year = year
    if nouncaps is not None:
        eng.nouncaps = nouncaps
    return eng


def modernise(
    text: str,
    lang: str = "nob",
    verse: bool = False,
    context: list[str] | None = None,
    year: int | None = None,
    nouncaps: bool | None = None,
    protected: list[tuple[int, int]] | None = None,
) -> str:
    """The modern spelling of `text`.

    `context` is the whole book (or as much of it as you have): the engine learns from
    it whether common nouns are capitalised and which capitalised words are names.
    Without it, `text` itself is used, which is less reliable for short snippets.
    `nouncaps` overrides that guess (True: the text capitalises common nouns, as most
    Dano-Norwegian before 1907 does). `year` is the printing year, used by a few lexicon
    rows. `verse` keeps line breaks.
    """
    return modernise_result(text, lang, verse, context, year, nouncaps, protected).text


def modernise_result(
    text: str,
    lang: str = "nob",
    verse: bool = False,
    context: list[str] | None = None,
    year: int | None = None,
    nouncaps: bool | None = None,
    protected: list[tuple[int, int]] | None = None,
) -> Result:
    """Like modernise(), but returns the Result: .text, and .changes, a list of
    {"at": offset in the printed text, "from", "to", "why": the deciding step}."""
    eng = book_engine(context if context is not None else [text], lang, year=year, nouncaps=nouncaps)
    return eng.modernise(text, verse=verse, protected=protected)


def prepare(texts: list[str], lang: str = "nob") -> int:
    """Look up the NB N-gram frequencies of forms in `texts` that the shipped snapshot
    lacks (network, api.nb.no). Without them a modern-looking but obsolete form can be
    accepted as a rule result. Returns the number of forms looked up."""
    from .archaism import fetch, known
    from .rules import candidates
    from .text import WORD

    counter = Counter(w.lower() for text in texts for w in WORD.findall(text))
    bank = engine(lang).bank
    wanted: list[str] = []
    for word, _ in counter.most_common():
        if bank.common(word):
            wanted.append(word)
        else:
            wanted.extend(c for level in candidates(word, lang) for c in level if bank.common(c))
    have = known(lang)
    todo = [w for w in dict.fromkeys(wanted) if w not in have]
    if todo:
        fetch(todo, lang)
        _resources.cache_clear()
    return len(todo)
