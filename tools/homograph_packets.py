"""Packets for the homograph screen: every frequent change the engine makes without
context, for a check that the old form has no second reading the change gets wrong.

Reads out/survey/<lang>-changes.tsv (run tools/survey.py first) and writes
out/audit/homograph/<lang>-homograph-NN.tsv; results go to
out/audit/homograph/results/<same name>.tsv (see HOMOGRAPH-BRIEF.md).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv import lexicon  # noqa: E402

SURVEY = ROOT / "out" / "survey"
OUT = ROOT / "out" / "audit" / "homograph"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=int, default=5)
    parser.add_argument("--size", type=int, default=400)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in ("nob", "nno"):
        entries = lexicon.load(lang)
        best: dict[str, dict] = {}
        with open(SURVEY / f"{lang}-changes.tsv") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                source = row["from"].lower()
                rows = [e for e in entries.get(source, []) if not e.origin.startswith("audit")]
                if row["why"] == "grammar" or int(row["count"]) < args.min or any(e.when for e in rows):
                    continue
                if source not in best or int(row["count"]) > int(best[source]["count"]):
                    best[source] = row
        items = sorted(best.values(), key=lambda r: -int(r["count"]))
        for n in range(0, len(items), args.size):
            path = OUT / f"{lang}-homograph-{n // args.size:02d}.tsv"
            with open(path, "w") as handle:
                handle.write("id\tcount\tfrom\tto\texamples\n")
                for i, row in enumerate(items[n : n + args.size]):
                    handle.write(f"{lang}-homograph-{n + i:05d}\t{row['count']}\t{row['from']}\t{row['to']}\t{row['examples']}\n")
        print(lang, len(items), "pairs")


if __name__ == "__main__":
    main()
