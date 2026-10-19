"""Precision of the respelling rules alone, measured against audit verdicts.

For every audited old form, the rules (no lexicon) either propose a modern form or
leave the word. Against the auditor's answer (ok/fix target, or keep/context = must
not change) each proposal is right, wrong, or a miss. Reports by rule-chain
signature, so the engine can trust only the chains that are reliably right.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv.statistics import precision_lower
from rettskriv.engine import Engine  # noqa: E402
from rettskriv.rules import OBLIGATORY  # noqa: E402
from tools.ingest import packets, verdicts  # noqa: E402


def signature(chain: tuple[str, ...], lang: str) -> str:
    obligatory = {r.name for r in OBLIGATORY[lang]}
    optional = sorted(set(chain) - obligatory)
    return "+".join(optional) or "obligatory"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="nob")
    parser.add_argument("--min-n", type=int, default=30)
    parser.add_argument("--min-precision", type=float, default=0.995)
    parser.add_argument("--write", action="store_true", help="write data/trusted-chains.json")
    args = parser.parse_args()
    engine = Engine(args.lang)
    items, results = packets(), verdicts()
    stats: dict[str, Counter] = defaultdict(Counter)
    wrong: dict[str, list] = defaultdict(list)
    seen = set()
    for vid, verdict in results.items():
        item = items.get(vid)
        if not item or not vid.startswith(args.lang):
            continue
        source = item["source"].lower()
        if source in seen:
            continue
        seen.add(source)
        kind = verdict["verdict"].strip().lower()
        answer = (item.get("to") or "").lower() if kind == "ok" else (verdict.get("target") or "").strip().lower()
        if engine.bank.common(source) or len(source) == 1:
            continue  # the engine never respells a form the bank allows
        proposal = engine.rule_target(source)
        if not isinstance(proposal, tuple):
            stats["(none)"]["miss" if kind in ("ok", "fix") else "right-left"] += 1
            continue
        target, chain = proposal
        sig = signature(chain, args.lang)
        if kind in ("ok", "fix") and target == answer:
            stats[sig]["right"] += 1
        else:
            stats[sig]["wrong"] += 1
            wrong[sig].append(f"{source}→{target} ({kind} {answer})")
    trusted = []
    print(f"{'n':>6} {'prec':>6}  chain")
    for sig, c in sorted(stats.items(), key=lambda kv: -sum(kv[1].values())):
        n = c["right"] + c["wrong"]
        if not n:
            print(f"{sum(c.values()):6d}     —   {sig} {dict(c)}")
            continue
        precision = c["right"] / n
        mark = ""
        lower = precision_lower(c["right"], n)
        if n >= args.min_n and lower >= args.min_precision:
            trusted.append(sig)
            mark = "  TRUSTED"
        print(f"{n:6d} {precision:6.3f}  {sig}{mark} lower95={lower:.4f}   e.g. {'; '.join(wrong[sig][:4])}")
    if args.write:
        path = ROOT / "data" / "trusted-chains.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        existing["_note"] = "Optional chains: one-sided 95% exact binomial precision lower bound >= 99.5%. Obligatory chains remain an explicit policy exception, not a statistical guarantee."
        existing[args.lang] = sorted(set(trusted) | {"obligatory"})
        path.write_text(json.dumps(existing, indent=1) + "\n")
        print("wrote", path)


if __name__ == "__main__":
    main()
