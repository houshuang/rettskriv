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
4. Respelling rules: exactly one non-archaic bank form reachable at any depth, or
   nothing. (Preferring the shallowest made ræd "red" where it is "redd".) A rule
   result is applied only if its chain is trusted (data/trusted-chains.json: audit
   precision >= 99.5%); otherwise it is "pending", left as printed until an audit
   puts the form in the lexicon.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from dataclasses import dataclass, field

from . import lexicon as lexmod
from .archaism import Archaism
from .bank import Bank
from .rules import NEEDS, OBLIGATORY, candidates
from .text import Token, apply_case, join, offset_map, tokenise

TITLES = {
    "hr", "herr", "fru", "frue", "frøken", "frk", "jomfru", "madame", "monsieur", "kong", "dronning",
    "prins", "prinsesse", "hertug", "greve", "grev", "jarl", "baron", "sankt", "st", "pastor", "præst",
    "prest", "provst", "prost", "biskop", "bisp", "doktor", "dr", "professor", "prof", "kaptajn", "kaptein",
    "lieutenant", "løitnant", "løytnant", "general", "oberst", "major", "sogneprest", "sognepræst",
    "kapellan", "skipper", "kjøbmand", "kjøpmann", "lensmand", "lensmann", "fogd", "foged", "amtmand",
}
SUBJECTS = {"jeg", "du", "han", "hun", "vi", "man", "der", "som", "hvo", "hvem", "hvilken", "og", "eller", "men"}
OBJECTS = {"sig", "ham", "hende", "dem", "os", "mig", "dig", "eder", "det", "op", "ud", "ind", "ned", "af",
           "paa", "til", "frem", "hen", "bort", "over", "med", "ikke", "ei", "atter", "igjen", "nu", "da", "saa"}
DETERMINERS = {"den", "det", "de", "denne", "dette", "disse", "min", "mit", "mine", "din", "dit", "dine", "sin",
               "sit", "sine", "hans", "hendes", "dens", "dets", "vor", "vort", "vore", "eders", "deres", "hin",
               "hint", "hine", "alle", "begge", "mange", "nogle", "de", "en", "et", "saa", "meget", "mest", "mere"}
PLURAL_SUBJECTS = {"vi", "de"}
# after these a participle in -ede cannot be an adjective (objects, or the subject
# after an inverted verb: "Dermed tørrede han")
PRONOUN_OBJECTS = {"sig", "ham", "hende", "dem", "os", "mig", "dig", "eder", "jeg", "du", "han", "hun", "vi", "man"}

ROOT = Path(__file__).resolve().parent.parent
NAME_SHARE = 0.3

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
        self.year: int | None = None
        trusted = ROOT / "data" / "trusted-chains.json"
        self.trusted = set(json.loads(trusted.read_text()).get(lang, [])) if trusted.exists() else set()
        self.obligatory = {r.name for r in OBLIGATORY[lang]}
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
        found = {}
        for level in candidates(low, self.lang):
            for cand, chain in level.items():
                if cand != low and self.bank.common(cand) and not self.archaism.archaic(cand) and all(
                    NEEDS[step] & self.bank.tags(cand) for step in chain if step in NEEDS
                ):
                    found[cand] = chain
        if len(found) == 1:
            result = next(iter(found.items()))
        elif found:
            result = "ambiguous:" + "|".join(sorted(found))
        else:
            result = "unknown"
        self._cand[low] = result
        return result

    def matches(self, entry: lexmod.Entry, tokens: list[Token], i: int, words: list[int]) -> bool:
        token = tokens[i]
        pos = words.index(i)
        prev = tokens[words[pos - 1]] if pos > 0 else None
        nxt = tokens[words[pos + 1]] if pos + 1 < len(words) else None
        for key, values in entry.when:
            if key == "before" and not (self.year and self.year < int(next(iter(values)))):
                return False
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
            if key in ("prev", "notprev", "prevout", "prevtags", "prevhas"):
                other = prev
            elif key in ("next", "notnext", "nextout", "nexttags", "nexthas"):
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
            if key in ("prevhas", "nexthas"):
                if not self.bank.tags((other.out or other.text).lower()) & values:
                    return False
            if key in ("prevtags", "nexttags"):
                tags = self.bank.tags((other.out or other.text).lower()) - MINOR_TAGS
                if self.nouncaps and not other.capitalised:
                    tags -= {"subst"}
                if not tags or not tags <= values:
                    return False
        return True

    # -- grammar: inflections that need the neighbouring words ------------------

    def modern_lower(self, low: str) -> str | None:
        """The modern form of a lower-case word by bank or rules, without context."""
        if self.bank.common(low) and not self.archaism.archaic(low):
            return low
        target = self.rule_target(low)
        return target[0] if isinstance(target, tuple) else None

    def weak_past(self, low: str) -> str | None:
        """Modern past tense of an old weak past in -ede: svarede -> svarte, kastede -> kastet."""
        if self.lang != "nob" or not low.endswith("ede") or len(low) < 6:
            return None
        infinitive = self.modern_lower(low[:-2])
        if not infinitive or "verb:inf" not in self.bank.tags(infinitive):
            return None
        stem = infinitive[:-1] if infinitive.endswith("e") else infinitive
        forms = [f for f in (stem + "et", stem + "te", stem + "de") if "verb:pret" in self.bank.tags(f)]
        if not forms:
            return None
        return max(forms, key=lambda f: self.archaism.freq.get(f, (0.0, 0.0))[1])

    def plural_present(self, low: str) -> str | None:
        """Modern present of an old plural present (vi komme -> vi kommer)."""
        if self.lang != "nob":
            return None
        infinitive = self.modern_lower(low)
        if not infinitive:
            return None
        tags = self.bank.tags(infinitive) - MINOR_TAGS
        if self.nouncaps:
            tags -= {"subst"}
        if not tags or not tags <= {"verb:inf", "verb:imp"}:
            return None
        present = infinitive + "r"
        return present if "verb:pres" in self.bank.tags(present) else None

    def grammar_candidate(self, low: str) -> bool:
        return self.weak_past(low) is not None or self.plural_present(low) is not None

    def grammar(self, tokens: list[Token], i: int, words: list[int]) -> bool:
        token = tokens[i]
        low = token.lower
        pos = words.index(i)
        prev = tokens[words[pos - 1]].lower if pos > 0 else None
        nxt = tokens[words[pos + 1]].lower if pos + 1 < len(words) else None
        past = self.weak_past(low)
        if past:
            respelled = self.modern_lower(low)
            adjective = respelled is not None and "adj:part" in self.bank.tags(respelled)
            verb_context = prev in SUBJECTS or nxt in OBJECTS
            if not adjective or nxt in PRONOUN_OBJECTS or (verb_context and prev not in DETERMINERS):
                token.out = self.case(token, past)
                token.reason = "grammar:weak-past"
                return True
            return False
        present = self.plural_present(low)
        after = tokens[words[pos + 1]] if pos + 1 < len(words) else None
        inverted = after is not None and (after.lower == "vi" or after.text == "I")
        if present and (inverted or prev in PLURAL_SUBJECTS or (prev == "i" and tokens[words[pos - 1]].text == "I")):
            if prev == "de" and pos > 1 and tokens[words[pos - 2]].lower in {"alle", "og", "for", "af", "med", "til", "paa"}:
                return False
            token.out = self.case(token, present)
            token.reason = "grammar:plural-present"
            return True
        return False

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
        if "prop" in tags:
            # both a name and a common word (Ola, Lie, Dag): a name if modern text
            # writes it capitalised at least 30% as often as lower case
            capital = target[:1].upper() + target[1:]
            if capital not in self.archaism.freq or (
                self.archaism.modern(capital) >= NAME_SHARE * self.archaism.modern(low)
            ):
                return capital
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
        if self.lang == "nob" and not token.capitalised or token.initial:
            if not second_pass and self.grammar_candidate(low):
                return False
            if second_pass and self.grammar(tokens, i, words):
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
            signature = "+".join(sorted(set(target[1]) - self.obligatory)) or "obligatory"
            if signature not in self.trusted:
                # measured below the trust bar: left as printed until audited
                token.out = token.text
                token.reason = "pending"
                token.meta["candidates"] = target[0]
                return True
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
