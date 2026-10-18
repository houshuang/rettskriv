"""Command line: modernise a text file (or stdin) paragraph by paragraph.

    python3 -m rettskriv book.txt                 # riksmål/Dano-Norwegian -> bokmål
    python3 -m rettskriv --lang nno landsmaal.txt  # landsmål -> nynorsk
    python3 -m rettskriv --changes book.txt        # mark changes as [old→new]

Paragraphs are separated by blank lines. The whole input is the book context (noun
capitalisation, names). A paragraph that reads as Swedish, German, English or Latin is
left as printed; one in the other Norwegian norm goes to that norm's engine.
"""
from __future__ import annotations

import argparse
import re
import sys

from . import engine, prepare
from .corpus import detect


def main() -> None:
    parser = argparse.ArgumentParser(prog="python3 -m rettskriv", description=__doc__.split("\n\n")[0])
    parser.add_argument("file", nargs="?", help="text file (UTF-8); stdin when omitted")
    parser.add_argument("--lang", choices=("nob", "nno"), default="nob", help="the text's main norm (default nob)")
    parser.add_argument("--verse", action="store_true", help="the text is verse: keep every line break")
    parser.add_argument("--year", type=int, help="printing year, used by a few lexicon rows")
    parser.add_argument("--nouncaps", action=argparse.BooleanOptionalAction, default=None,
                        help="the text capitalises common nouns (default: guessed from the text)")
    parser.add_argument("--changes", action="store_true", help="show each change as [old→new]")
    parser.add_argument("--lookup", action="store_true",
                        help="first look up N-gram frequencies the shipped snapshot lacks (network)")
    args = parser.parse_args()
    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    parts = re.split(r"(\n\s*\n)", text)
    paragraphs = parts[0::2]
    langs = [detect(p, args.lang) for p in paragraphs]
    if args.lookup:
        for lang in ("nob", "nno"):
            mine = [p for p, l in zip(paragraphs, langs) if l == lang]
            if mine:
                print(f"looked up {prepare(mine, lang)} {lang} forms", file=sys.stderr)
    for lang in ("nob", "nno"):
        eng = engine(lang)
        eng.learn_book([p for p, l in zip(paragraphs, langs) if l == lang] or [""])
        eng.year = args.year
        if args.nouncaps is not None:
            eng.nouncaps = args.nouncaps
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append(part)
            continue
        lang = langs[i // 2]
        if lang not in ("nob", "nno") or not part.strip():
            out.append(part)
            continue
        result = engine(lang).modernise(part, verse=args.verse)
        if not args.changes:
            out.append(result.text)
            continue
        marked, last = [], 0
        for change in result.changes:
            marked.append(part[last : change["at"]])
            marked.append(f"[{change['from']}→{change['to']}]")
            last = change["at"] + len(change["from"])
        marked.append(part[last:])
        out.append("".join(marked))
    sys.stdout.write("".join(out))


if __name__ == "__main__":
    main()
