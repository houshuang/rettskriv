"""Build audit packets from the survey work lists.

rule:  every distinct pair made by an optional rule (pairs made only by obligatory
       letter rewrites are a pure change of letters and are sampled, not audited)
left:  every form left as printed for want of a decision (unknown, ambiguous,
       archaic-unresolved) seen at least --min times; candidates carries a compound
       proposal ("compound: x") when tools/compounds.py finds one and no tie is listed
Writes out/audit/<lang>-<kind>-NN.tsv.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv.engine import Engine  # noqa: E402
from rettskriv.rules import OBLIGATORY  # noqa: E402
from tools.compounds import proposal  # noqa: E402
from tools.ingest import done_sources  # noqa: E402

SURVEY = ROOT / "out" / "survey"
AUDIT = ROOT / "out" / "audit"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=500)
    parser.add_argument("--min", type=int, default=2)
    parser.add_argument("--sample", type=float, default=0.03, help="share of obligatory-only pairs audited")
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()
    AUDIT.mkdir(parents=True, exist_ok=True)
    rng = random.Random("rettskriv-audit")
    for lang in ("nob", "nno"):
        engine = Engine(lang)
        obligatory = {r.name for r in OBLIGATORY[lang]}
        rows = {"rule": [], "left": [], "inbank": []}
        done = done_sources(lang)
        with open(SURVEY / f"{lang}-changes.tsv") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["why"] != "rule":
                    continue
                target = engine.rule_target(row["from"])
                chain = target[1] if isinstance(target, tuple) else ()
                if row["from"] in done or set(chain) <= obligatory and rng.random() > args.sample:
                    continue
                rows["rule"].append((row["count"], row["from"], row["to"], "+".join(chain), row["examples"]))
        with open(SURVEY / f"{lang}-left.tsv") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if (int(row["count"]) < args.min and row["reason"] != "pending") or row["form"] in done:
                    continue
                candidates = row["candidates"]
                if not candidates and (compound := proposal(engine, row["form"])) and compound != row["form"]:
                    candidates = f"compound: {compound}"
                rows["left"].append((row["count"], row["form"], row["reason"], candidates, row["examples"]))
        inbank = SURVEY / f"{lang}-inbank.tsv"
        if inbank.exists():
            with open(inbank) as handle:
                for row in csv.DictReader(handle, delimiter="\t"):
                    if row["form"] in done:
                        continue
                    rows["inbank"].append((row["count"], row["form"], "in-bank", row["ratio"], row["examples"]))
        for kind, items in rows.items():
            for n in range(0, len(items), args.size):
                path = AUDIT / f"{lang}-{kind}-r{args.round}-{n // args.size:02d}.tsv"
                with open(path, "w") as handle:
                    if kind == "rule":
                        handle.write("id\tcount\tfrom\tto\trules\texamples\n")
                    else:
                        handle.write("id\tcount\tform\treason\tcandidates\texamples\n")
                    for i, item in enumerate(items[n : n + args.size]):
                        handle.write(f"{lang}-{kind}-r{args.round}-{n + i:05d}\t" + "\t".join(item) + "\n")
            print(lang, kind, len(items), "items")


if __name__ == "__main__":
    main()
