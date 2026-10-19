"""Reviewed historical lemma identities, separate from syntactic confidence.

A modern dictionary's single lemma does not prove the identity of a historical
word. Alternative identities remain alternatives even when they share a surface
inflection. This small inventory is deliberately incomplete.
"""
import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / 'lexicon' / 'historical-verbs.csv'


@dataclass(frozen=True)
class VerbIdentity:
    infinitive: str
    evidence: str


@dataclass(frozen=True)
class InflectionCandidate:
    infinitive: str
    lemma: str
    role: str
    forms: frozenset[str]
    evidence: str


@lru_cache(maxsize=1)
def identities():
    result = {}
    with PATH.open() as handle:
        for row in csv.DictReader(handle):
            source, target, evidence = (row[k].strip() for k in ('source', 'target', 'evidence'))
            if not source or not target or not evidence or not source.isalpha() or not target.isalpha():
                raise ValueError('Historical verb identities require source, target and evidence')
            entry = VerbIdentity(target, evidence)
            if entry in result.get(source, []):
                raise ValueError(f'Duplicate historical verb identity: {source}')
            result.setdefault(source, []).append(entry)
    return {source: tuple(entries) for source, entries in result.items()}


def infinitives(source):
    """None means unaudited; a tuple retains all reviewed possible identities."""
    return identities().get(source)


def candidates(bank, source, role='verb:pret', *, following=''):
    """Return reviewed identities with their own forms, never a merged ranking.

    An empty result is lack of evidence, not permission to use parser fluency.
    Multiple records require independent sense evidence before selection.
    """
    result = []
    for identity in infinitives(source) or ():
        lemmas = {a.lemma for a in bank.analyses(identity.infinitive)
                  if {'verb', 'inf'} <= set(a.tags.split()) and 'pass' not in a.tags.split()}
        if not lemmas:
            # Missing modern morphology is unresolved evidence, not a reason
            # to silently discard a competing historical identity.
            result.append(InflectionCandidate(identity.infinitive, '', role, frozenset(), identity.evidence))
        for lemma in sorted(lemmas):
            forms = bank.inflect(identity.infinitive, 'verb:inf', role, lemma=lemma)
            result.append(InflectionCandidate(identity.infinitive, lemma, role, forms, identity.evidence))
    # ODS kaare IV (choose) / V (card wool). A personal object assigned a
    # reviewed human role distinguishes choice from textile processing. Do not
    # infer this from the role noun alone: Ulden til sin Brud is still wool.
    if source == 'kaare' and re.match(
            r'^\s+(?:ham|hende)\s+til\s+sin\s+(?:brud|brudgom|konge|dronning)\b', following, re.I):
        return tuple(c for c in result if c.infinitive == 'kåre')
    return tuple(result)
