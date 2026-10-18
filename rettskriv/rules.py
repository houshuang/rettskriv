"""Orthographic respelling rules.

Obligatory rules first rewrite letter sequences modern Norwegian no longer has
(aa, qv, ph, øi). Optional rules then rewrite one site at a time (b d g after a
vowel, doubled consonants, æ). The engine keeps only candidates the modern word
bank contains and acts only when exactly one survives at any depth. Rules never choose between two modern words: they only find the modern
spelling of a word that has no modern spelling of its own.

Every rule is a pure respelling of the same word. Substitutions of one word for
another (thi -> for, ei -> ikke) are never rules and are not made at all.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_STEPS = 4
V = "aeiouyæøå"


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern
    repl: str
    # the modern form must carry one of these bank tags (a suffix rule only respells
    # an inflection, so its output must be that inflection)
    need: frozenset[str] = frozenset()


def r(name: str, pattern: str, repl: str, need: tuple[str, ...] = ()) -> Rule:
    return Rule(name, re.compile(pattern), repl, frozenset(need))


NEEDS: dict[str, frozenset[str]] = {}


# Obligatory rules rewrite letter sequences the modern norm no longer has. They are
# applied everywhere at once before any optional rule.
BOKMAL_OBLIGATORY = [
    r("aa", "aa", "å"),
    r("qv", "q[vu]", "kv"),
    r("ph", "ph", "f"),
    r("th", "^th", "t"),  # only word-initially: let|hed, kort|hed join t and h
    r("oej", "ø[ji]", "øy"),
    r("ej", "ej", "ei"),
    r("ii", "ii", "i"),
    r("hed", "hed(?=$|en$|er$|ens$|ene$|ers$|s$)", "het"),
    r("skab", "skab", "skap"),
    r("agtig", "agtig", "aktig"),
    r("igt", "(?<=l)igt$", "ig"),
]

BOKMAL = [
    r("ae", "æ", "e"),
    r("aj", "aj", "ai"),
    # 1907: soft b d g after a vowel become p t k
    r("b-p", f"(?<=[{V}])b(?![b])", "p"),
    r("d-t", f"(?<=[{V}])d(?![dt])(?!(?<=ed)e$)", "t"),  # not the -ede suffix, not before t
    r("g-k", f"(?<=[{V}])g(?![g])", "k"),
    r("bb-pp", "bb", "pp"),
    r("dd-tt", "dd", "tt"),
    r("gg-kk", "gg", "kk"),
    # assimilated clusters
    r("nd-nn", "nd", "nn"),
    r("ld-ll", "ld", "ll"),
    # final consonant doubled after a short vowel
    # (only word-finally: before an ending the vowel is often long, hære is not herre)
    r("double", f"(?<=[{V}])([bdfgklmnprst])$", r"\1\1"),
    r("ee", "ee(?!$)", "e"),  # final -ee is French é (idee, allee)
    r("oo", "oo", "o"),
    r("uu", "uu", "u"),
    # loan-word spellings
    r("ch-k", "(?<!s)ch(?=[aeiouyæøårl])", "k"),  # not German sch or final ch (Schiller, Hauch)
    r("c-k", "c(?=[aou]|$|[^eiyhæø])", "k"),
    r("c-s", "c(?=[eiyæø])", "s"),
    r("x", "x", "ks"),
    r("z", "z", "s"),
    r("w", "w", "v"),
    # suffixes
    r("ede", "ede$", "et", need=("verb:pret",)),
    r("erne", "erne$", "ene", need=("subst",)),
    r("erne-s", "ernes$", "enes", need=("subst",)),
]

NYNORSK_OBLIGATORY = [
    r("aa", "aa", "å"),
    r("qv", "q[vu]", "kv"),
]

NYNORSK = [
    r("ade", "ade$", "a", need=("verb:pret", "adj:part", "verb:perf-part")),
    r("ad", "(?<=[^d])ad$", "a", need=("verb:pret", "adj:part", "verb:perf-part")),
    r("i-a", "i$", "a", need=("subst",)),
    r("in-a", "ine$", "ane", need=("subst",)),
    r("ar-ane", "arne$", "ane", need=("subst",)),
    r("at-et", "at$", "et", need=("subst",)),
    r("dt", "dt$", "t"),
    r("ld-ll", "ld", "ll"),
    r("upp", "^upp", "opp"),
    r("u-o", "um$", "om"),
    r("ee", "ee", "e"),
    r("ch-k", "ch", "k"),
    r("c-k", "c(?=[aou]|$|[^eiyhæø])", "k"),
    r("x", "x", "ks"),
]

RULES = {"nob": BOKMAL, "nno": NYNORSK}
for _rule in BOKMAL + NYNORSK:
    if _rule.need:
        NEEDS[_rule.name] = _rule.need
OBLIGATORY = {"nob": BOKMAL_OBLIGATORY, "nno": NYNORSK_OBLIGATORY}


def obligatory(word: str, lang: str) -> tuple[str, tuple[str, ...]]:
    chain = []
    for rule in OBLIGATORY[lang]:
        new = rule.pattern.sub(rule.repl, word)
        if new != word:
            chain.append(rule.name)
            word = new
    return word, tuple(chain)


def candidates(word: str, lang: str, max_steps: int = MAX_STEPS) -> list[dict[str, tuple[str, ...]]]:
    """Respellings of word by depth: element d maps each word first reached after
    d optional rewrites (following the obligatory ones) to its rule chain."""
    rules = RULES[lang]
    base, chain0 = obligatory(word, lang)
    seen = {base}
    levels = [{base: chain0}]
    for _ in range(max_steps):
        level = {}
        for current, chain in levels[-1].items():
            for rule in rules:
                for match in rule.pattern.finditer(current):
                    new = current[: match.start()] + match.expand(rule.repl) + current[match.end():]
                    if new not in seen:
                        seen.add(new)
                        level[new] = chain + (rule.name,)
        if not level:
            break
        levels.append(level)
    return levels
