"""Replay acceptance findings against the current engine.

For each reviewed sample (out/eval/<name>.json + <name>.review.tsv), re-modernise the
same paragraphs and report, per flagged change, whether the current output still
contains the flagged modern form at that place.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv import corpus  # noqa: E402
from rettskriv.engine import Engine  # noqa: E402

EVAL = ROOT / "out" / "eval"


def main() -> None:
    engines = {"nob": Engine("nob"), "nno": Engine("nno")}
    status = Counter()
    for name in sys.argv[1:]:
        units = json.loads((EVAL / f"{name}.json").read_text())
        by_n = {c["n"]: (u, c) for u in units for c in u["changes"]}
        books = {}
        for row in csv.DictReader(open(EVAL / f"{name}.review.tsv"), delimiter="\t"):
            if row["kind"] in {"miss", "ok"} or not row["n"].strip().isdigit():
                continue
            unit, change = by_n[int(row["n"])]
            book = unit["book"]
            if book not in books:
                data = corpus.load(book)
                for engine in engines.values():
                    engine.learn_book(corpus.texts(data))
                    engine.year = data.get("printed_year")
                books[book] = True
            result = engines[unit["lang"]].modernise(unit["original"], verse=unit["path"].endswith("lines"))
            now = next((t.out for t in result.tokens if t.word and t.start == change["at"]), None) if "at" in change else None
            if now is None:
                now = next((t.out for t in result.tokens if t.word and t.text == change["from"]), change["from"])
            fixed = now != change["to"]
            status[(row["kind"], fixed)] += 1
            if not fixed and row["kind"] == "meaning":
                print(f"STILL {name} {row['n']}: {change['from']}→{now}  ({row['note'][:70]})")
    for (kind, fixed), n in sorted(status.items()):
        print(f"{kind:8s} {'fixed' if fixed else 'still'} {n}")


if __name__ == "__main__":
    main()
