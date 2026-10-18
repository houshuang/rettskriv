"""The modernising engine.

Principle: same word, modern form. A word is changed only when its modern form is
certain; otherwise it is left exactly as printed. Leaving a word as printed is
always allowed, changing it to a different word never is.

Order for each word:
1. Curated lexicon rows for the form (possibly conditioned on context).
2. A protected name: left as printed.
3. A form the modern bank allows: left as printed, apart from the case of a
   capitalised noun. If the form is archaic (its use collapsed after 1910), it is
   reported, because only the lexicon may decide it.
4. Respelling rules: exactly one non-archaic bank form at the shallowest depth
   that has any, or nothing.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from . import lexicon as lexmod
from .archaism import Archaism
from .bank import Bank
from .rules import NEEDS, candidates
from .text import Token, apply_case, join, offset_map, tokenise

TITLES = {
    "hr", "herr", "fru", "frue", "frøken", "frk", "jomfru", "madame", "monsieur", "kong", "dronning",
    "prins", "prinsesse", "hertug", "greve", "grev", "jarl", "baron", "sankt", "st", "pastor", "præst",
    "prest", "provst", "prost", "biskop", "bisp", "doktor", "dr", "professor", "prof", "kaptajn", "kaptein",
    "lieutenant", "løitnant", "løytnant", "general", "oberst", "major", "sogneprest", "sognepræst",
    "kapellan", "skipper", "kjøbmand", "kjøpmann", "lensmand", "lensmann", "fogd", "foged", "amtmand",
}
# Tags too rare to block a reading: letters as symbols, abbreviations, interjections.
MINOR_TAGS = frozenset({"symb", "fork", "interj"})
KEEP_CAPITAL = {"gud", "guds", "herren", "herrens", "herre", "jesus", "jesu", "kristus", "kristi",
                "christus", "christi", "de", "dem", "deres", "frelseren", "frelserens"}


@dataclass
class Result:
    text: str
    tokens: list[Token]
    changes: list[dict] = field(default_factory=list)
    flags: Counter = field(default_factory=Counter)

    def map_offset(self, offset: int) -> int:
        return self._map(offset)


class Engine:
    def __init__(self, lang: str = "nob"):
        self.lang = lang
        self.bank = Bank(lang)
        self.lexicon = lexmod.load(lang)
        self.archaism = Archaism(lang)
        self.names: set[str] = set()
        self.nouncaps = False
        self._cand: dict[str, tuple[str, tuple[str, ...]] | str] = {}

    # -- book-level context -------------------------------------------------

    def learn_book(self, texts: list[str]) -> None:
        """Book-level context: whether nouns are capitalised, and which capitalised
        forms occur in a name context anywhere in the book (those are protected)."""
        self.names = set()
        capital = lower = 0
        for text in texts:
            for token in tokenise(text):
                if token.word and not token.initial and self.bank.tags(token.lower) == {"subst"}:
                    if token.capitalised:
                        capital += 1
                    else:
                        lower += 1
        self.nouncaps = capital > lower
        for text in texts:
            tokens = [t for t in tokenise(text) if t.word]
            for i, token in enumerate(tokens):
                if not token.capitalised:
                    continue
                prev = tokens[i - 1] if i else None
                nxt = tokens[i + 1] if i + 1 < len(tokens) else None
                if prev is not None and prev.lower in TITLES and not token.initial:
                    self.names.add(token.text)
                # next to a known proper name (Jonas Lie, Ole Berg): a full name
                for other in (prev, nxt):
                    if other is not None and other.capitalised and self.bank.proper_only(other.text):
                        if not token.initial or not self.bank.common(token.lower):
                            self.names.add(token.text)
                if self.bank.proper_only(token.text):
                    self.names.add(token.text)

    # -- per word ---------------------------------------------------------

    def rule_target(self, low: str):
        """The unique non-archaic bank respelling of low, or a reason string."""
        if low in self._cand:
            return self._cand[low]
        result = "unknown"
        for level in candidates(low, self.lang):
            found = {
                cand: chain for cand, chain in level.items()
                if cand != low and self.bank.common(cand) and not self.archaism.archaic(cand)
                and all(NEEDS[step] & self.bank.tags(cand) for step in chain if step in NEEDS)
            }
            if len(found) == 1:
                result = next(iter(found.items()))
                break
            if found:
                result = "ambiguous:" + "|".join(sorted(found))
                break
        self._cand[low] = result
        return result

    def matches(self, entry: lexmod.Entry, tokens: list[Token], i: int, words: list[int]) -> bool:
        token = tokens[i]
        pos = words.index(i)
        prev = tokens[words[pos - 1]] if pos > 0 else None
        nxt = tokens[words[pos + 1]] if pos + 1 < len(words) else None
        for key, values in entry.when:
            if key == "nouncaps" and not self.nouncaps:
                return False
            if key == "nonouncaps" and self.nouncaps:
                return False
            if key == "cap" and not token.capitalised:
                return False
            if key == "lower" and token.capitalised:
                return False
            if key == "mid" and token.initial:
                return False
            if key == "initial" and not token.initial:
                return False
            if key in ("prev", "notprev", "prevout", "prevtags"):
                other = prev
            elif key in ("next", "notnext", "nextout", "nexttags"):
                other = nxt
            else:
                continue
            if key.startswith("not"):
                if other is not None and other.lower in values:
                    return False
                continue
            if other is None:
                return False
            if key in ("prev", "next") and other.lower not in values:
                return False
            if key in ("prevout", "nextout") and (other.out or other.text).lower() not in values:
                return False
            if key in ("prevtags", "nexttags"):
                tags = self.bank.tags((other.out or other.text).lower()) - MINOR_TAGS
                if self.nouncaps and not other.capitalised:
                    tags -= {"subst"}
                if not tags or not tags <= values:
                    return False
        return True

    def case(self, token: Token, target: str) -> str:
        """Case for a modern form: initial capitals stay, noun capitals go."""
        if token.upper:
            return target.upper()
        if not token.capitalised:
            return target
        if token.initial:
            return target[:1].upper() + target[1:]
        low = target.lower()
        if token.text in self.names or token.lower in KEEP_CAPITAL or low in KEEP_CAPITAL:
            return target[:1].upper() + target[1:]
        tags = self.bank.tags(low)
        if not tags or "prop" in tags and not (tags - {"prop"}):
            return target[:1].upper() + target[1:]
        return low

    def decide(self, tokens: list[Token], i: int, words: list[int], second_pass: bool) -> bool:
        """Set tokens[i].out. Returns False if the decision needs the second pass."""
        token = tokens[i]
        low = token.lower
        entries = self.lexicon.get(low)
        if entries:
            if not second_pass and any(e.contextual for e in entries):
                return False
            for entry in entries:
                if self.matches(entry, tokens, i, words):
                    if entry.keep:
                        token.out = self.case(token, token.text) if token.capitalised else token.text
                        token.reason = f"lexicon-keep:{entry.line}"
                    else:
                        token.out = self.case(token, entry.target)
                        token.reason = f"lexicon:{entry.line}"
                    return True
            token.out = token.text
            token.reason = "lexicon-nomatch"
            return True
        if token.text in self.names or self.bank.proper_only(token.text):
            token.out = token.text
            token.reason = "name"
            return True
        if len(low) == 1 or "'" in low or "’" in low:
            token.out = token.text
            token.reason = "short"
            return True
        if self.bank.common(low):
            token.out = self.case(token, token.text)
            token.reason = "archaic-unresolved" if self.archaism.archaic(low) else "modern"
            return True
        target = self.rule_target(low)
        if isinstance(target, tuple):
            token.out = self.case(token, target[0])
            token.reason = "rule:" + "+".join(target[1])
        else:
            token.out = token.text
            token.reason = target.split(":")[0]
            if target.startswith("ambiguous"):
                token.meta["candidates"] = target.split(":", 1)[1]
        return True

    def modernise(self, text: str, verse: bool = False) -> Result:
        tokens = tokenise(text, verse=verse)
        words = [i for i, t in enumerate(tokens) if t.word]
        pending = [i for i in words if not self.decide(tokens, i, words, second_pass=False)]
        for i in pending:
            self.decide(tokens, i, words, second_pass=True)
        result = Result(join(tokens), tokens)
        result._map = offset_map(tokens)
        for t in tokens:
            if not t.word:
                continue
            result.flags[t.reason.split(":")[0]] += 1
            if t.out != t.text:
                result.changes.append({"at": t.start, "from": t.text, "to": t.out, "why": t.reason})
        return result
