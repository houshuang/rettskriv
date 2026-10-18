"""Tokenising and case handling.

A text is split into alternating separator and word tokens so that joining the
tokens gives back the text byte for byte. Only word tokens are ever changed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)
SENTENCE_END = re.compile(r"[.!?:;]['\"»”’)\]]*\s*$|^\s*$")
OPENERS = "«»\"“”„'‘’(—–-[ \t"


@dataclass
class Token:
    text: str
    word: bool
    start: int
    initial: bool = False      # first word of a sentence, line of verse or block
    out: str | None = None     # modern form, None while undecided
    reason: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def lower(self) -> str:
        return self.text.lower()

    @property
    def capitalised(self) -> bool:
        return self.text[:1].isupper()

    @property
    def upper(self) -> bool:
        return len(self.text) > 1 and self.text.isupper()


def tokenise(text: str, verse: bool = False) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    for match in WORD.finditer(text):
        if match.start() > pos:
            tokens.append(Token(text[pos:match.start()], False, pos))
        tokens.append(Token(match.group(), True, match.start()))
        pos = match.end()
    if pos < len(text):
        tokens.append(Token(text[pos:], False, pos))
    mark_initial(tokens, verse)
    return tokens


def mark_initial(tokens: list[Token], verse: bool) -> None:
    before = ""
    for token in tokens:
        if not token.word:
            before += token.text
            continue
        gap = before
        stripped = before.rstrip(OPENERS)
        token.initial = (
            not stripped.strip()
            or bool(SENTENCE_END.search(stripped))
            or (verse and "\n" in gap)
        )
        before = token.text


def apply_case(model: str, target: str, keep_capital: bool) -> str:
    """Give target the case pattern of model.

    keep_capital: whether an initial capital in model should survive.
    """
    if not target:
        return target
    if len(model) > 1 and model.isupper():
        return target.upper()
    if model[:1].isupper() and keep_capital:
        return target[:1].upper() + target[1:]
    return target


def join(tokens: list[Token]) -> str:
    return "".join(t.out if t.word and t.out is not None else t.text for t in tokens)


def offset_map(tokens: list[Token]):
    """Return a function mapping an offset in the original to one in the output.

    Offsets inside a changed word map to the start of its replacement.
    """
    spans = []
    new = 0
    for t in tokens:
        out = t.out if t.word and t.out is not None else t.text
        spans.append((t.start, t.start + len(t.text), new, new + len(out), out == t.text))
        new += len(out)

    def mapped(offset: int) -> int:
        for start, end, nstart, nend, same in spans:
            if offset < end or (offset == end and start == end):
                if same:
                    return nstart + (offset - start)
                return nstart
        return new

    return mapped
