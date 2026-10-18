"""Meaning-error rate of reviewed acceptance samples.

Joins out/eval/parts/<name>-pN.review.tsv to <name>.json, writes <name>.review.tsv (the
input of tools/recheck.py) and prints changes, errors by kind and the meaning rate.

    python3 tools/accept_report.py accept-17 accept-18 accept-19 accept-20
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

EVAL = Path(__file__).resolve().parent.parent / "out" / "eval"
FIELDS = ["n", "kind", "from", "to", "better", "note"]


def main() -> None:
    total, meaning = 0, 0
    for name in sys.argv[1:]:
        rows = []
        for path in sorted((EVAL / "parts").glob(f"{name}-p*.review.tsv")):
            with open(path) as handle:
                rows += list(csv.DictReader(handle, delimiter="\t"))
        with open(EVAL / f"{name}.review.tsv", "w") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        units = json.loads((EVAL / f"{name}.json").read_text())
        changes = {c["n"]: c for u in units for c in u["changes"]}
        kinds = Counter(r["kind"].strip() for r in rows)
        total, meaning = total + len(changes), meaning + kinds["meaning"]
        print(f"{name}: {len(changes)} changes, {dict(kinds)}, meaning {kinds['meaning'] / len(changes):.3%}")
        for r in rows:
            if r["kind"].strip() == "meaning" and r["n"].strip().isdigit():
                c = changes.get(int(r["n"]), {})
                print(f"  {r['n']:>5} {r['from']}→{r['to']} [{c.get('why', '?')}] {r['note'][:70]}")
    if total:
        print(f"total: {meaning} meaning errors in {total} changes = {meaning / total:.3%}")


if __name__ == "__main__":
    main()
