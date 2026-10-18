"""Build verification packets: every auditor 'fix' not yet verified.

Writes out/audit/verify/<lang>-verify-NN.tsv (id, count, source, proposal, examples);
results go to out/audit/results/verify-<lang>-verify-NN.tsv.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.ingest import AUDIT, packets, verdicts, verifications  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=500)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()
    items, results, checks = packets(), verdicts(), verifications()
    folder = AUDIT / "verify"
    folder.mkdir(parents=True, exist_ok=True)
    for lang in ("nob", "nno"):
        rows = []
        for vid, verdict in sorted(results.items()):
            if not vid.startswith(lang) or vid in checks or vid not in items:
                continue
            if verdict["verdict"].strip().lower() != "fix":
                continue
            item = items[vid]
            rows.append((vid, item["count"], item["source"], (verdict.get("target") or "").strip(), item["examples"]))
        for n in range(0, len(rows), args.size):
            path = folder / f"{lang}-verify-r{args.round}-{n // args.size:02d}.tsv"
            with open(path, "w") as handle:
                handle.write("id\tcount\tsource\tproposal\texamples\n")
                for row in rows[n : n + args.size]:
                    handle.write("\t".join(row) + "\n")
        print(lang, len(rows), "fixes to verify")


if __name__ == "__main__":
    main()
