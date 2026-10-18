"""Every occurrence of an old form in the corpus, for writing context rows.

    python3 tools/context_probe.py tog                      # where tog is left as printed, by neighbours
    python3 tools/context_probe.py tog --when "lower;prev=han|hun|jeg"   # what that row would match
    python3 tools/context_probe.py tog --when "..." --all   # every match, not a sample

A row is safe only if it is right at every occurrence it matches; read them all.
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv import corpus  # noqa: E402
from rettskriv import lexicon as lexmod  # noqa: E402
from rettskriv.engine import Engine  # noqa: E402


def occurrences(form: str, lang: str):
    """(book, nouncaps, tokens, i, words, engine) for every occurrence, after modernising."""
    engine = Engine(lang)
    for book in corpus.books():
        data = corpus.load(book)
        default = corpus.LANGUAGE.get(data["book"].get("language"), "nob")
        texts = corpus.texts(data)
        if not any(form in text.lower() for text in texts):
            continue
        engine.learn_book(texts)
        engine.year = data.get("printed_year")
        for item in data["items"]:
            if item.get("kind") != "piece":
                continue
            if corpus.detect(" ".join(t for _, t, _ in corpus.units(item)), default) != lang:
                continue
            for _, text, verse in corpus.units(item):
                if form not in text.lower():
                    continue
                result = engine.modernise(text, verse=verse)
                tokens = result.tokens
                words = [i for i, t in enumerate(tokens) if t.word]
                for i in words:
                    if tokens[i].lower == form:
                        yield book, tokens, i, words, engine


def kwic(tokens, i, width=70) -> str:
    left = "".join(t.text for t in tokens[:i])[-width:].replace("\n", " / ")
    right = "".join(t.text for t in tokens[i + 1 :])[:width].replace("\n", " / ")
    return f"{left}[{tokens[i].text}]{right}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("form")
    parser.add_argument("--lang", default="nob")
    parser.add_argument("--when", help="a when clause to test (lexicon.py syntax)")
    parser.add_argument("--all", action="store_true", help="print every match, not a sample of 60")
    parser.add_argument("--changed", action="store_true", help="look at occurrences the engine changes instead")
    args = parser.parse_args()
    form = args.form.lower()
    entry = lexmod.Entry(form, "?", lexmod.parse_when(args.when), "", "probe", "probe") if args.when else None
    total, rows, neighbours = 0, [], Counter()
    for book, tokens, i, words, engine in occurrences(form, args.lang):
        total += 1
        token = tokens[i]
        if (token.out != token.text) != args.changed:
            continue
        if entry is not None and not engine.matches(entry, tokens, i, words):
            continue
        prev, nxt = engine.neighbours(tokens, i, words)
        case = "Cap" if token.capitalised else "low"
        neighbours[(prev.lower if prev else "|", case, nxt.lower if nxt else "|")] += 1
        rows.append(f"{book:20s} {'nc' if engine.nouncaps else '  '} {kwic(tokens, i)}")
    label = "changed" if args.changed else "left as printed"
    print(f"{form}: {total} occurrences; {len(rows)} {label}" + (f" and matching {args.when!r}" if entry else ""))
    print("\nmost common  prev / case / next:")
    for (p, c, n), k in neighbours.most_common(40):
        print(f"  {k:5d}  {p} {c} {n}")
    shown = rows if args.all else random.Random(form).sample(rows, min(60, len(rows)))
    print(f"\n{'all' if args.all or len(shown) == len(rows) else 'a sample of'} {len(shown)} ('nc' = book capitalises nouns):")
    for row in shown:
        print(" ", row)


if __name__ == "__main__":
    main()
