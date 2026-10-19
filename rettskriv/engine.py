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
import re
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
    "prest", "provst", "prost", "biskop", "bisp", "doktor", "dr", "professor", "prof", "kaptajn", "kaptein", "kaptejn",
    "lieutenant", "løitnant", "løjtnant", "løytnant", "general", "oberst", "major", "sogneprest", "sognepræst",
    "kapellan", "skipper", "kjøbmand", "kjøpmann", "lensmand", "lensmann", "fogd", "foged", "amtmand",
}
ABBREVIATED_TITLES = {"hr", "frk", "dr", "prof", "st"}
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
NAME_SHARE = 0.5
PATRONYMIC = ("søn", "sen", "son", "datter", "dotter", "døtter")
ROMAN = re.compile(r"[IVXLCDM]+")
BREAK = re.compile(r"[,.;:!?()«»\"“”—–\-\d]")
# Capitalised mid-sentence in a book that capitalises nouns, these still are what they say.
CAPITAL_FUNCTION_WORDS = {"i", "de", "dem", "deres", "eder", "eders", "jeg"}
MODALS = {"kan", "skal", "vil", "maa", "må", "kunde", "skulde", "vilde", "maatte", "måtte", "kunne", "skulle",
          "ville", "bør", "tør", "lod", "lade", "fik", "fikk", "monne", "gad", "turde", "burde"}

# Tags too rare to block a reading: letters as symbols, abbreviations, interjections.
MINOR_TAGS = frozenset({"symb", "fork", "interj"})
# first names ending in -s that are not genitives
FIRST_NAMES_IN_S = {"mogens", "hans", "klaus", "claus", "nils", "niels", "lars", "mons", "jens", "anders",
                    "vincents", "markus", "magnus", "thomas", "tomas", "andreas", "jonas", "elias", "mathias",
                    "matias", "tobias", "nikolaus", "paulus", "petrus", "julius", "ambrosius", "erasmus"}
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
                if prev is not None and prev.lower in TITLES and not token.initial and token.lower not in self.lexicon:
                    self.names.add(token.text)
                # a surname after a first name (Mogens Svale, Vincents Lunge), even if it is
                # also a common word; not after Jesu, Guds and the like
                if (
                    prev is not None and not token.initial and prev.capitalised
                    and token.lower not in self.lexicon
                    and self.bank.proper_only(prev.text) and prev.lower not in KEEP_CAPITAL
                    and (not prev.lower.endswith(("s", "u")) or prev.lower in FIRST_NAMES_IN_S)
                ):
                    self.names.add(token.text)
                # next to a known proper name (Jonas Lie, Ole Berg): a full name
                # (only for forms that are no known word: «Jesu Hænder» makes no name of Hænder)
                for other in (prev, nxt):
                    if other is not None and other.capitalised and self.bank.proper_only(other.text):
                        if not self.bank.common(token.lower) and token.lower not in self.lexicon:
                            self.names.add(token.text)
                if self.bank.proper_only(token.text):
                    self.names.add(token.text)

    # -- per word ---------------------------------------------------------

    def trusted_target(self, low: str) -> str | None:
        target = self.rule_target(low)
        if not isinstance(target, tuple):
            return None
        signature = "+".join(sorted(set(target[1]) - self.obligatory)) or "obligatory"
        return target[0] if signature in self.trusted else None

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

    @staticmethod
    def neighbours(tokens: list[Token], i: int, words: list[int]):
        """The previous and next word, or None when punctuation stands between."""
        pos = words.index(i)
        prev = nxt = None
        if pos > 0 and not BREAK.search("".join(t.text for t in tokens[words[pos - 1] + 1 : i])):
            prev = tokens[words[pos - 1]]
        if pos + 1 < len(words) and not BREAK.search("".join(t.text for t in tokens[i + 1 : words[pos + 1]])):
            nxt = tokens[words[pos + 1]]
        return prev, nxt

    def neighbour_form(self, other: Token) -> str:
        """A neighbour's modern form; one still undecided (deferred to the second pass)
        is looked up without context."""
        if other.out is not None:
            return other.out.lower()
        return self.modern_lower(other.lower) or other.lower

    def matches(self, entry: lexmod.Entry, tokens: list[Token], i: int, words: list[int]) -> bool:
        token = tokens[i]
        prev, nxt = self.neighbours(tokens, i, words)
        pos = words.index(i)
        before_prev = tokens[words[pos - 2]] if prev is not None and pos > 1 else None
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
            if key == "prev2":
                if before_prev is None or before_prev.lower not in values:
                    return False
                continue
            if key == "prevbreak" and (prev is not None or pos == 0 or token.initial):
                return False  # punctuation, not a sentence start, before the word ("Ja, sig")
            if key == "nextend":
                if nxt is None or not nxt.lower.endswith(tuple(values)):
                    return False
                continue
            if key == "nextlower":
                if pos + 1 >= len(words) or tokens[words[pos + 1]].capitalised:
                    return False
                continue
            if key == "notprev2":
                if before_prev is not None and before_prev.lower in values:
                    return False
                continue
            if key in ("nextany", "nextbreak"):
                pos = words.index(i)
                if pos + 1 >= len(words) or tokens[words[pos + 1]].lower not in values:
                    return False
                if key == "nextbreak" and nxt is not None:
                    return False  # nextbreak needs punctuation between ("ved, at")
                continue
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
            if key in ("prevout", "nextout") and self.neighbour_form(other) not in values:
                return False
            if key in ("prevhas", "nexthas"):
                tags = (self.bank.syntax_tags(self.neighbour_form(other)) if token.lower in {"at", "aa"} and "verb:inf" in values
                        else self.bank.tags(self.neighbour_form(other)))
                if not tags & values:
                    return False
            if key in ("prevtags", "nexttags"):
                tags = (self.bank.syntax_tags(self.neighbour_form(other)) if token.lower in {"at", "aa"} and "verb:inf" in values
                        else self.bank.tags(self.neighbour_form(other))) - MINOR_TAGS
                if self.nouncaps and not other.capitalised:
                    tags -= {"subst"}
                if not tags or not tags <= values:
                    return False
        return True

    # -- grammar: inflections that need the neighbouring words ------------------

    def modern_lower(self, low: str) -> str | None:
        """The modern form of a lower-case word by lexicon, bank or rules, without context."""
        rows = self.lexicon.get(low, [])
        if len(rows) == 1 and not rows[0].when:
            if rows[0].keep:
                return low if self.bank.common(low) else None
            return rows[0].target
        if rows:
            return None
        if self.bank.common(low) and not self.archaism.archaic(low):
            return low
        return self.trusted_target(low)

    def weak_past(self, low: str) -> str | None:
        """Modern past tense of an old weak past in -ede: svarede -> svarte, kastede -> kastet."""
        if self.lang != "nob" or not low.endswith("ede") or len(low) < 6:
            return None
        infinitive = self.modern_lower(low[:-2])
        if not infinitive or "verb:inf" not in self.bank.tags(infinitive):
            return None
        lemmas = {a.lemma for a in self.bank.analyses(infinitive)
                  if "verb" in a.tags.split() and "inf" in a.tags.split() and "pass" not in a.tags.split()}
        if len(lemmas) != 1:
            return None  # Frequency must not select between different lexemes.
        forms = sorted(self.bank.inflect(infinitive, "verb:inf", "verb:pret"))
        if not forms:
            return None
        # Keep the established weak-inflection preference when several paradigm
        # forms are valid; frequency alone must not introduce a different reading
        # (heldede -> hellet, not the frequent helte).
        stem = infinitive[:-1] if infinitive.endswith("e") else infinitive
        regular = set(forms) & {stem + "et", stem + "te", stem + "de"}
        if regular:
            forms = sorted(regular)
        elif len(forms) != 1:
            return None
        return max(forms, key=lambda f: (self.archaism.freq.get(f, (0.0, 0.0))[1], f.endswith("et"), f))

    def plural_present(self, low: str) -> str | None:
        """Modern present of an old plural present (vi komme -> vi kommer)."""
        if self.lang != "nob":
            return None
        infinitive = self.modern_lower(low)
        if not infinitive:
            return None
        tags = self.bank.tags(infinitive) - MINOR_TAGS
        source_tags = self.bank.tags(low) - MINOR_TAGS
        if low != infinitive and source_tags and source_tags <= {"verb:inf", "verb:imp"}:
            # A respelled verb can acquire a new homograph (sige -> si, also a
            # determiner). Keep the source's unambiguous verb analysis.
            tags &= {"verb:inf", "verb:imp"}
        if self.nouncaps:
            tags -= {"subst"}
        # an -e form that can also be an adjective (åpne) is checked in context
        if not tags or not tags <= {"verb:inf", "verb:imp", "adj"} or "verb:inf" not in tags:
            return None
        forms = self.bank.inflect(infinitive, "verb:inf", "verb:pres")
        return next(iter(forms)) if len(forms) == 1 else None

    def grammar_candidate(self, low: str) -> bool:
        # a curated or audited row for an -ede form is the answer (legede is lekte, not leget)
        past = self.weak_past(low) is not None and low not in self.lexicon
        rows = self.lexicon.get(low, [])
        # an unconditional keep says the form has two readings (lede: lead or search)
        kept = len(rows) == 1 and rows[0].keep and not rows[0].when
        return past or (self.plural_present(low) is not None and not kept)

    def weak_form(self, tokens: list[Token], i: int, words: list[int], past: str) -> tuple[str, str] | None:
        """Disambiguate old -ede with same-lemma inflections and local syntax.

        Candidate existence does not establish tense. In particular, the past
        ``leverte`` cannot replace the participle in ``bleve leverede``.
        """
        token = tokens[i]
        infinitive = self.modern_lower(token.lower[:-2])
        perfect = self.bank.inflect(infinitive, "verb:inf", "verb:perf-part")
        agreeing = self.bank.inflect(infinitive, "verb:inf", "adj:part:agreeing")
        pos = words.index(i)
        left, right = [], []
        for direction, dest in ((-1, left), (1, right)):
            previous = i
            for n in range(1, 13):
                at = pos + direction * n
                if not 0 <= at < len(words):
                    break
                other = words[at]
                a, b = sorted((previous, other))
                if BREAK.search("".join(t.text for t in tokens[a + 1:b])):
                    break
                dest.append(tokens[other])
                previous = other
        prev = left[0].lower if left else None
        nxt = right[0].lower if right else None
        auxiliaries = {"ble", "blev", "bleve", "bleven", "blevne", "blir", "blive", "bliver", "blitt", "blit",
                       "bli", "er", "ere", "var", "vare", "været", "være", "har", "have", "havde", "hadde"}
        adverbs = {"ei", "ikke", "aldrig", "altid", "allerede", "atter", "ogsaa", "også", "nu", "nå",
                   "her", "der", "dog", "selv", "derimod", "siden", "stundom", "endog", "just",
                   "fuldkommen", "fuldstændig", "meget", "saa", "så", "tappert", "hemmelig", "imidlertid"}

        def pick(forms):
            if not forms:
                return None
            # Prefer an already valid source spelling, then the established
            # -ede adjective over its equally valid -ete variant.
            if token.lower in forms:
                return token.lower
            if past in forms:
                return past
            return max(forms, key=lambda f: (f.endswith("ede"), self.archaism.modern(f), f))

        # An immediately governing auxiliary, possibly separated by adverbs.
        governor = next((t for t in left if t.lower not in adverbs), None)
        # Find an attributive noun head through adjective/adverb modifiers.
        head = None
        for t in right[:6]:
            form = self.modern_lower(t.lower) or t.lower
            tags = self.bank.tags(form) - MINOR_TAGS
            if tags & {"pron", "det", "prep", "sbu"}:
                break
            if (tags & {"subst", "prop"} or self.nouncaps and t.capitalised and not tags) and not tags & {"pron", "det", "adv", "prep", "verb:pres", "verb:pret"}:
                head = t
                break
            if t.lower in {"og", "eller", "desuden", "slet"} or tags & {"adj", "adj:part", "adv"}:
                continue
            break
        if governor and governor.lower in auxiliaries:
            lexical_adjective = any(a.tags.startswith("adj ") and "<perf-part>" not in a.tags
                                    for a in self.bank.analyses(token.lower))
            next_tags = self.bank.tags(self.neighbour_form(right[0])) if right else set()
            possible_head = "subst" in next_tags and not next_tags & {"prep", "pron", "det", "adv"}
            if head or possible_head or lexical_adjective or governor.lower in {"er", "ere", "var", "vare", "været", "være"}:
                return None  # Could be a lexical/predicative adjective or noun phrase.
            target = pick(perfect)
            return (target, "participle") if target else None
        # A reporting verb immediately after closed direct speech is finite.
        # The lexical restriction excludes quoted labels followed by adjectives.
        gap = "".join(t.text for t in tokens[words[pos - 1] + 1:i]) if pos else ""
        if infinitive in {"svare", "erklære"} and re.search(r'[,!?][”»“"]\s*$', gap):
            if right and (right[0].capitalised or nxt in PRONOUN_OBJECTS | {"de", "den"}):
                return past, "weak-reporting"
        # Relative subject der starts its own clause. Require its preceding
        # comma so locative 'vi saa der udmærkede Mænd' does not qualify.
        relative = next((t for t in left if t.lower not in adverbs - {"der"}), None)
        if relative and relative.lower == "der" and head is None:
            der_at = next((j for j in words[:pos] if tokens[j] is relative), None)
            if der_at is not None:
                der_pos = words.index(der_at)
                boundary = "".join(t.text for t in tokens[words[der_pos - 1] + 1:der_at]) if der_pos else ""
                # Locative contrast may omit its noun: 'her simple Folk,
                # der udmærkede'. A comma alone does not make der relative.
                preceding = []
                for t in reversed(tokens[:der_at]):
                    if not t.word and re.search(r"[.!?;:]", t.text):
                        break
                    if t.word:
                        preceding.append(t.lower)
                if re.fullmatch(r"\s*,\s*", boundary) and not {"her", "hist", "hisset"} & set(preceding):
                    return past, "weak-relative"
        clause = self.weak_clause(tokens, i, words, left, right, past, perfect)
        if clause:
            return clause
        if nxt in PRONOUN_OBJECTS:
            return past, "weak-past"
        # Only contiguous modifiers can connect an adjective to a determiner.
        # A noun or verb ends that evidence; a remote "de" may be a subject.
        determiner = False
        for offset, t in enumerate(left[:7]):
            if t.lower in DETERMINERS:
                outside = left[offset + 1] if offset + 1 < len(left) else None
                governed = outside and "prep" in self.bank.tags(self.neighbour_form(outside))
                # de/den/det can be subjects; Hans can be a personal name.
                determiner = bool((t.lower not in {"de", "den", "det", "denne", "dette", "disse"}
                                   or governed
                                   or head is not None and t.lower in {"den", "det", "de", "denne", "dette", "disse"}
                                   and right.index(head) + 1 < len(right)
                                   and right[right.index(head) + 1].lower in {"maatte", "måtte", "skulde", "skulle", "kunde", "kunne"})
                                  and not self.is_name(t))
                break
            if t.lower == "slet":  # historical adverb, also modern past of slite
                continue
            tags = self.bank.tags(self.neighbour_form(t)) - MINOR_TAGS
            if not tags or not tags <= {"adj", "adj:part", "adv"}:
                break
        if head and (determiner or prev in {"af", "av", "med", "uden", "uten"}):
            if self.is_name(head) or (head.capitalised and not self.nouncaps) or any(t.lower == "sig" for t in right[:5]):
                return None  # Could be an inverted named/reflexive subject.
            target = pick(agreeing)
            return (target, "adjective") if target else None
        if prev in DETERMINERS:
            return None
        direct = {"jeg", "du", "han", "hun", "vi", "man"}
        # A dictionary-known personal subject has no genitive suffix and no
        # governing preposition. Do not guess unknown capitals to be names.
        named_subject = bool(governor and self.subject_name(governor)
                             and not governor.lower.endswith("s")
                             and not any(self.bank.tags(self.neighbour_form(t)) & {"prep"}
                                         for t in left[left.index(governor) + 1:left.index(governor) + 2])
                             and not any(self.bank.tags(self.neighbour_form(t)) & {"verb:pres", "verb:pret"}
                                         for t in left[left.index(governor) + 1:]))
        if token.initial and nxt not in direct | {"de"}:
            return None
        sentence_governor = False
        for t in reversed(tokens[:i]):
            if not t.word and re.search(r"[.!?;:]", t.text):
                break
            if t.word and (t.lower in auxiliaries | {"faa", "få", "fik", "fikk", "faar", "får", "faaet", "fået", "fått"}
                           or self.bank.tags(self.neighbour_form(t)) & {"verb:pres", "verb:pret"}
                           or t.lower.endswith("ede")):
                sentence_governor = True
                break
        named_subject = named_subject and not sentence_governor
        if (past in agreeing and not self.bank.common(token.lower) and not sentence_governor):
            # Finite and agreeing readings converge on the same verified form;
            # an earlier verb can instead govern an object predicate or a
            # coordinated perfect participle (fik Brevene besvarede).
            return past, "weak-shared"
        if head and not (governor and governor.lower in direct) and not named_subject:
            return None  # Noun subjects and attributive modifiers can look alike.

        # An auxiliary elsewhere in the phrase can govern an object predicate
        # (havde elleve Langskibe samlede); do not assume the noun is a subject.
        if any(t.lower in auxiliaries for t in left) and not (governor and governor.lower in direct):
            return None
        if self.bank.tags(token.lower) & {"adj", "adj:part"} and not (governor and governor.lower in direct):
            return None
        if named_subject:
            return past, "weak-past"
        if nxt in PRONOUN_OBJECTS or (governor and governor.lower in direct):
            return past, "weak-past"
        return None

    def weak_clause(self, tokens, i, words, left, right, past, perfect):
        """Recognize bounded complete constituents, never skip unknown syntax.

        These proofs are alternatives to the conservative sentence-wide governor
        veto: a preceding subordinate clause need not govern this finite clause.
        """
        pos = words.index(i)
        before = "".join(t.text for t in tokens[words[pos - 1] + 1:i]) if pos else ""

        def tags(t):
            result = self.bank.tags(self.neighbour_form(t)) - MINOR_TAGS
            if (self.nouncaps and not t.capitalised and self.neighbour_form(t) != t.lower
                    and "subst" not in self.bank.tags(t.lower)):
                result -= {"subst"}
            return result

        def noun(t):
            ts = tags(t)
            if ts == {"subst"}:
                return True
            # Dictionary-attested noun + noun compounds (Ovnstuer), only in
            # capitalized-noun prose. Unknown capitals alone establish nothing.
            if not ts and self.nouncaps and t.capitalised and not self.is_name(t):
                w = t.lower
                return any(self.bank.tags(w[:n]) == {"subst"}
                           and "subst" in self.bank.tags(w[n:])
                           for n in range(3, len(w) - 2))
            return False

        def genitive(t):
            if not t.lower.endswith("s") or len(t.lower) < 4:
                return False
            stem = t.lower[:-1]
            form = self.modern_lower(stem) or stem
            return (self.bank.tags(form) <= {"subst", "prop"} and bool(self.bank.tags(form))
                    or t.capitalised and any(e.kind == "name" for e in self.lexicon.get(stem, [])))

        def noun_phrase(span, allow_present=False):
            if not span:
                return False
            determined = len(span) > 1 and (span[0].lower in DETERMINERS or genitive(span[0]))
            head_tags = tags(span[-1])
            headed = noun(span[-1])
            if (not headed and determined and "subst" in head_tags
                    and head_tags <= {"subst", "verb:inf", "verb:imp", "verb:pres"}
                    and (allow_present or "verb:pres" not in head_tags)):
                analyses = self.bank.analyses(self.neighbour_form(span[-1]))
                headed = any(a.tags.startswith("subst ") and
                             (span[0].lower not in {"en", "et"} or "ent" in a.tags.split())
                             for a in analyses)
            if not headed:
                return False
            modifiers = span[:-1]
            if modifiers and (modifiers[0].lower in DETERMINERS or genitive(modifiers[0])):
                modifiers = modifiers[1:]
            for n, t in enumerate(modifiers):
                ts = tags(t)
                if ts & {"adj", "adj:part"} and ts <= {"adj", "adj:part", "subst", "verb:imp"}:
                    continue
                if t.lower in {"mange", "flere"} and "adj" in ts:
                    continue
                if (ts == {"adv"} and n + 1 < len(modifiers)
                        and tags(modifiers[n + 1]) <= {"adj", "adj:part"}
                        and tags(modifiers[n + 1])):
                    continue
                return False
            return True

        def end_after(t, terminal=False):
            at = next(j for j in words if tokens[j] is t)
            n = words.index(at) + 1
            gap = "".join(x.text for x in tokens[at + 1:words[n] if n < len(words) else len(tokens)])
            return n == len(words) or bool(re.search(r"[.!?]" if terminal else r"[,.;:!?]", gap))

        # A complete indefinite object ends the subordinate clause. Looking
        # only at en/et would misread nominalized 'de besvarede en efter en'.
        if (len(left) >= 2 and left[0].lower == "de"
                and left[1].lower in {"hvor", "at", "fordi"}
                and right and right[0].lower in {"en", "et"}
                and noun_phrase(right) and end_after(right[-1], terminal=True)):
            return past, "weak-clause-object"

        # Complete sentence-initial nominal subject followed by a negated
        # predicate. Never skip an earlier verb to manufacture a subject.
        subject = list(reversed(left))
        if (subject and subject[0].initial and noun_phrase(subject)
                and right and right[0].lower in {"ei", "ikke"}):
            return past, "weak-clause-nominal-subject"

        # A terminal predicate after at + a complete noun subject. The
        # subject may have a clause adverb, but no copula/auxiliary is skipped.
        if end_after(tokens[i], terminal=True):
            subject = list(left)
            while subject and subject[0].lower in {"selv", "dog", "ikke", "aldrig"}:
                subject.pop(0)
            for n, t in enumerate(subject):
                if t.lower == "at":
                    if noun_phrase(list(reversed(subject[:n]))):
                        return past, "weak-clause-subject"
                    break

        # A relative object clause contains a complete possessive subject,
        # not merely a noun near som. Punctuation must introduce the relative.
        for n, t in enumerate(left):
            if t.lower not in {"som", "da"}:
                continue
            at = next(j for j in words if tokens[j] is t)
            tp = words.index(at)
            gap = "".join(x.text for x in tokens[words[tp - 1] + 1:at]) if tp else ""
            subject = list(reversed(left[:n]))
            if not re.fullmatch(r"\s*,\s*", gap) or not noun_phrase(subject):
                break
            if (t.lower == "som" and subject[0].lower in {"hans", "hendes", "deres", "vor", "vore"}
                    and end_after(tokens[i], terminal=True)):
                return past, "weak-relative-subject"
            if (t.lower == "da" and right and right[0].lower in {"en", "et"}
                    and noun_phrase(right) and end_after(right[-1], terminal=True)):
                return past, "weak-clause-transitive"
            break

        # Relative som with a fronted negative object closes at the predicate.
        if (len(left) >= 3 and [t.lower for t in left[:3]] == ["intet", "dog", "som"]
                and end_after(tokens[i])):
            at = next(j for j in words if tokens[j] is left[2])
            tp = words.index(at)
            gap = "".join(x.text for x in tokens[words[tp - 1] + 1:at]) if tp else ""
            if re.fullmatch(r"\s*,\s*", gap):
                return past, "weak-relative-object"

        # Inverted personal subject de with a clause adverb, not a noun modifier.
        if (re.fullmatch(r"\s*,\s*", before) and len(right) >= 2
                and right[0].lower == "de" and right[1].lower in {"dog", "ikke", "aldrig"}):
            return past, "weak-clause-inversion"

        # A negated inverted predicate followed by a complete possessive
        # subject, not an attributive fragment or an unresolved second verb.
        if (re.fullmatch(r"\s*,\s*", before) and len(right) >= 3
                and right[0].lower in {"ei", "ikke"}
                and right[1].lower in {"hans", "hendes", "deres", "mine", "vore"}
                and noun_phrase(right[1:], allow_present=True) and end_after(right[-1], terminal=True)):
            return past, "weak-clause-negative"

        # A dated relative has a verified proper-name object. Dates alone do
        # not license a verb: require the relative subject and full boundary.
        if len(left) == 1 and left[0].lower == "der" and len(right) == 1 and self.subject_name(right[0]):
            der_at = words[pos - 1]
            gap = "".join(t.text for t in tokens[words[pos - 2] + 1:der_at]) if pos >= 2 else ""
            obj_at = words[pos + 1]
            stop = words[pos + 2] if pos + 2 < len(words) else len(tokens)
            date = "".join(t.text for t in tokens[obj_at + 1:stop])
            prefix = "".join(t.text for t in tokens[:der_at]).lower()
            if (re.fullmatch(r"\s*,\s*", gap) and re.fullmatch(r"\s+[12][0-9]{3}[.!?]\s*", date)
                    and not re.search(r"\b(?:her|hist|hisset)\b", re.split(r"[.!?;:]", prefix)[-1])):
                return past, "weak-relative-date"

        # A reflexive after a verified non-genitive name makes that name the
        # subject. Require a new clause boundary, not arbitrary nearby names.
        if (re.fullmatch(r"\s*,\s*", before) and len(right) >= 2
                and self.subject_name(right[0]) and not right[0].lower.endswith("s")
                and right[1].lower == "sig"):
            return past, "weak-clause-reflexive"

        # An indefinite inverted subject can carry a verified name apposition.
        # Consume the whole subject before sig; unknown capitals are not names.
        if right and right[0].lower in {"en", "et"}:
            for stop, t in enumerate(right):
                if t.lower != "sig":
                    continue
                span = right[:stop]
                for split in range(2, len(span) + 1):
                    if (noun_phrase(span[:split]) and all(self.subject_name(n) and not n.lower.endswith("s")
                                                         for n in span[split:])):
                        return past, "weak-clause-reflexive-np"
                break

        # Reporting coordination needs positive clausal-complement evidence,
        # not just a reflexive bridge (roste sig og udmærkede Mænd is unsafe).
        infinitive = self.modern_lower(tokens[i].lower[:-2])
        if (infinitive in {"erklære", "svare"} and left and left[0].lower in {"og", "men"}
                and right and right[0].lower == "i" and noun_phrase(right[1:])):
            bridge = list(left[1:])
            while bridge and bridge[0].lower in {"nu", "atter", "derefter"}:
                bridge.pop(0)
            if bridge and bridge[0].lower == "sig":
                bridge.pop(0)
                anchor = tags(bridge[0]) if bridge else set()
                if anchor and "verb:pret" in anchor and anchor <= {"verb:pret", "adj:part"}:
                    after = pos + len(right) + 1
                    if after < len(words) and tokens[words[after]].lower == "at":
                        gap = "".join(t.text for t in tokens[words[after - 1] + 1:words[after]])
                        tail = []
                        for n in range(after + 1, min(after + 9, len(words))):
                            if BREAK.search("".join(t.text for t in tokens[words[n - 1] + 1:words[n]])):
                                break
                            tail.append(tokens[words[n]])
                        if re.fullmatch(r"\s*,\s*", gap):
                            for n, t in enumerate(tail[:-1]):
                                subject = tail[:n]
                                if subject and subject[-1].lower in {"ei", "ikke"}:
                                    subject = subject[:-1]
                                if (t.lower in {"vilde", "ville", "skulde", "skulle", "kunde", "kunne"}
                                        and noun_phrase(subject) and "verb:inf" in tags(tail[n + 1])):
                                    return past, "weak-reporting-complement"

        # Adjacent finite coordination: no noun, pronoun or participle bridge.
        if len(left) >= 2 and left[0].lower in {"og", "eller", "men"}:
            anchor = tags(left[1])
            if (anchor and anchor <= {"verb:pres", "verb:pret"}
                    and left[1].lower not in MODALS
                    and self.neighbour_form(left[1]) not in MODALS | {"ble", "blir", "var", "er", "har", "hadde"}):
                return past, "weak-clause-coordination"

        # Finite blive + complete subject + participle at the clause boundary.
        # Have + object predicates and lexical adjectives are deliberately out.
        if end_after(tokens[i]) and perfect:
            for n, t in enumerate(left):
                if t.lower in {"ble", "blev", "bleve", "blir", "bliver"}:
                    infinitive = self.modern_lower(tokens[i].lower[:-2])
                    adjective_forms = self.bank.inflect(infinitive, "verb:inf", "adj:part:agreeing")
                    lexical_adj = any(a.tags.startswith("adj ") and "<perf-part>" not in a.tags
                                      for form in adjective_forms | {tokens[i].lower}
                                      for a in self.bank.analyses(form))
                    if noun_phrase(list(reversed(left[:n]))) and not lexical_adj:
                        target = max(perfect, key=lambda f: (self.archaism.modern(f), f))
                        return target, "participle-inversion"
                    break
        return None

    def grammar(self, tokens: list[Token], i: int, words: list[int]) -> bool:
        token = tokens[i]
        low = token.lower
        pos = words.index(i)
        prev_token, next_token = self.neighbours(tokens, i, words)
        prev = prev_token.lower if prev_token is not None else None
        nxt = next_token.lower if next_token is not None else None
        past = self.weak_past(low) if low not in self.lexicon else None
        if past:
            selected = self.weak_form(tokens, i, words, past)
            if selected:
                target, role = selected
                token.out = self.case(token, target)
                token.reason = "grammar:" + role
                return True
            return False
        present = self.plural_present(low)
        after = next_token
        inverted = after is not None and (after.lower == "vi" or after.text == "I") and prev not in MODALS
        subject = prev in PLURAL_SUBJECTS or (prev == "i" and prev_token.text == "I")
        if present and "adj" in self.bank.tags(self.modern_lower(low) or "") and nxt not in PRONOUN_OBJECTS:
            return False  # de aabne Døre (the open doors) against de aabne sig (they open)
        if present and (inverted or subject):
            before = tokens[words[pos - 2]].lower if subject and pos > 1 else None
            # "skulle vi have", "fik de gaa": after an inverted verb the verb is an infinitive
            if before in MODALS or self.bank.tags(before or "") & {"verb:pres", "verb:pret"}:
                return False
            if prev == "de" and before in {"alle", "og", "for", "af", "med", "til", "paa"}:
                return False
            token.out = self.case(token, present)
            token.reason = "grammar:plural-present"
            return True
        return False

    def noun_reading(self, low: str) -> bool:
        """Whether the old form or any modern form found for it can be a noun or name."""
        forms = {low}
        for entry in self.lexicon.get(low, []):
            if not entry.keep:
                forms.update(entry.target.split())
        target = self.rule_target(low)
        if isinstance(target, tuple):
            forms.add(target[0])
        elif target.startswith("ambiguous:"):
            forms.update(target.split(":", 1)[1].split("|"))
        unknown = all(not self.bank.tags(f) for f in forms)
        return unknown or any(self.bank.tags(f) & {"subst", "prop"} for f in forms)

    def case(self, token: Token, target: str) -> str:
        """Case for a modern form: initial capitals stay, noun capitals go."""
        if token.upper:
            return target.upper()
        if not token.capitalised:
            return target
        if token.initial:
            return target[:1].upper() + target[1:]
        low = target.lower()
        capital = target[:1].upper() + target[1:]
        # in a book that writes nouns in lower case, a capital mid-sentence marks a name
        if not self.nouncaps and token.lower not in CAPITAL_FUNCTION_WORDS:
            return capital
        if token.text in self.names or token.lower in KEEP_CAPITAL or low in KEEP_CAPITAL:
            return capital
        tags = self.bank.tags(low)
        if not tags and low.endswith("s") and len(low) > 3:
            # the bank has no genitives: Kongens, Landets take the tags of Kongen, Landet
            base = self.bank.tags(low[:-1])
            if "subst" in base and "prop" not in base:
                tags = base
        if "prop" in tags and not (tags - {"prop"}):
            return capital
        if not tags:
            # unknown to the bank (genitives, compounds): lower only a respelled word
            return low if token.lower != low else capital
        # a name if modern text writes the form capitalised at least half as often as
        # lower case (Mose, Laban, Lee score above 1; nouns 0.01–0.15, from sentence starts)
        # names keep their spelling: a respelled word is a common word and loses its capital
        pairs = [(capital, low), (token.text, token.lower)] if token.lower == low else []
        for upper_form, lower_form in pairs:
            upper_use = self.archaism.modern(upper_form)
            if upper_use > 0 and upper_use >= NAME_SHARE * self.archaism.modern(lower_form):
                return capital
        if token.lower == low and "prop" in tags and capital not in self.archaism.freq:
            return capital
        return low

    def subject_name(self, other: Token) -> bool:
        """Typed names supply syntax evidence, not surname-span propagation.

        Hakon Thinget must not protect Thinget merely because Hakon is a name.
        """
        return self.is_name(other) or bool(other.capitalised and any(
            entry.kind == "name" for entry in self.lexicon.get(other.lower, [])))

    def is_name(self, other: Token) -> bool:
        """A capitalised word the book or the bank knows as a name (Jens, Peder), the
        genitive of one (Vincents) or a patronymic (Knutssøn)."""
        if not other.capitalised or other.lower in CAPITAL_FUNCTION_WORDS:
            return False
        text = other.text
        if text in self.names or self.bank.proper_only(text) or "prop" in self.bank.tags(text):
            return True
        if text.endswith("s") and len(text) > 3 and "prop" in self.bank.tags(text[:-1]):
            return True
        return not self.bank.common(other.lower) and any(
            other.lower.endswith(s) and len(other.lower) > len(s) + 2 for s in PATRONYMIC
        )

    def in_name(self, prev: Token | None, nxt: Token | None, token: Token | None = None) -> bool:
        """Whether a capitalised word belongs to a name: it follows a name or a title
        (Peder Kjæmpe, Knutssøn Baat, Hr. Lund) or precedes a patronymic (Mord Valgardssøn).
        After the genitive of a name (Olafs Sønner, Guds Ord) only a word that is no common
        word counts; a first name in -s (Vincents Lunge) is no genitive."""
        def name(other: Token | None) -> bool:
            if other is None:
                return False
            if other.lower in TITLES and token is not None and not token.initial:
                return True
            if not self.is_name(other):
                return False
            genitive = (
                other.text.endswith("s") and other.lower not in FIRST_NAMES_IN_S
                and other.text not in self.names and "prop" not in self.bank.tags(other.text)
            )
            return not (genitive and token is not None and self.bank.common(token.lower))

        def patronymic(other: Token | None) -> bool:
            return (
                other is not None and other.capitalised and not self.bank.common(other.lower)
                and any(other.lower.endswith(s) and len(other.lower) > len(s) + 2 for s in PATRONYMIC)
            )

        return name(prev) or patronymic(nxt)

    @staticmethod
    def literal(tokens: list[Token], i: int) -> bool:
        """A Roman numeral (VII), a word glued to a number (2net) or the first part of a
        suspended compound (Nord- og Syd-): never a word to respell."""
        token = tokens[i]
        if token.upper and ROMAN.fullmatch(token.text):
            return True
        before = tokens[i - 1].text if i > 0 else ""
        if before[-1:].isdigit():
            return True
        after = tokens[i + 1].text if i + 1 < len(tokens) else ""
        last = i + 2 >= len(tokens)
        return after.startswith("-") and (after[1:2].isspace() or (after == "-" and last))

    def decide(self, tokens: list[Token], i: int, words: list[int], second_pass: bool) -> bool:
        """Set tokens[i].out. Returns False if the decision needs the second pass."""
        token = tokens[i]
        low = token.lower
        # Abbreviated titles contain a sentence-looking period; do not respell
        # the following name merely because sentence detection marked it initial.
        if (token.capitalised and low not in TITLES and i >= 2
                and tokens[i - 2].lower in ABBREVIATED_TITLES):
            gap = tokens[i - 1].text
            if re.fullmatch(r"\s*\.\s*", gap):
                token.out, token.reason = token.text, "name"
                return True
        if token.text == "I" and (prev := self.neighbours(tokens, i, words)[0]) is not None and self.is_name(prev):
            # Otto I, Christian I: a numeral after a name, not the pronoun
            token.out = token.text
            token.reason = "literal"
            return True
        if (
            i + 2 < len(tokens) and tokens[i + 1].text == "-" and tokens[i + 2].word
            and token.capitalised and self.is_name(tokens[i + 2])
        ):
            # the first part of a hyphenated name (Gange-Rolf)
            token.out = token.text
            token.reason = "name"
            return True
        if self.literal(tokens, i):
            token.out = token.text
            token.reason = "literal"
            return True
        if (
            not self.nouncaps and token.capitalised and not token.initial and not token.upper
            and low not in CAPITAL_FUNCTION_WORDS and low not in KEEP_CAPITAL
        ):
            # a book that writes nouns in lower case: a capital mid-sentence is a name
            token.out = token.text
            token.reason = "name"
            return True
        if (
            self.nouncaps and token.capitalised and not token.initial and not token.upper
            and low not in CAPITAL_FUNCTION_WORDS and low not in KEEP_CAPITAL
            and self.in_name(*self.neighbours(tokens, i, words), token)
        ):
            # next to a name or patronymic: part of a name (Peder Kjæmpe, Mord Valgardssøn)
            token.out = token.text
            token.reason = "name"
            return True
        if (
            self.nouncaps and token.capitalised and not token.initial and not token.upper
            and low not in CAPITAL_FUNCTION_WORDS and low not in KEEP_CAPITAL
            and not self.noun_reading(low)
        ):
            # capitalised mid-sentence but no noun or name reading: a noun we do not know
            # (Hun = the female, Grim, Trofast); leave it as printed
            token.out = token.text
            token.reason = "name"
            return True
        if self.lang == "nob" and (not token.capitalised or token.initial) and self.grammar_candidate(low):
            if not second_pass:
                return False
            if self.grammar(tokens, i, words):
                return True
        entries = self.lexicon.get(low)
        if entries:
            if not second_pass and any(e.contextual for e in entries):
                return False
            for entry in entries:
                if self.matches(entry, tokens, i, words):
                    if entry.keep:
                        token.out = token.text
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
            if self.archaism.archaic(low):
                token.out, token.reason = token.text, "archaic-unresolved"
            else:
                token.out, token.reason = self.case(token, token.text), "modern"
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

    def modernise(self, text: str, verse: bool = False,
                  protected: list[tuple[int, int]] | None = None) -> Result:
        """Modernise text, preserving tokens overlapping explicit character spans."""
        spans = protected or []
        for start, end in spans:
            if not (0 <= start < end <= len(text)):
                raise ValueError(f"invalid protected span: {(start, end)}")
        tokens = tokenise(text, verse=verse)
        for token in tokens:
            if token.word and any(token.start < end and token.start + len(token.text) > start
                                  for start, end in spans):
                token.out, token.reason = token.text, "protected"
        words = [i for i, t in enumerate(tokens) if t.word]
        pending = [i for i in words if tokens[i].out is None and not self.decide(tokens, i, words, second_pass=False)]
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
