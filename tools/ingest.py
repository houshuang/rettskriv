"""Turn audit verdicts into lexicon rows: lexicon/<norm>/audit.csv.

ok      -> the engine's form, pinned (source, target)
fix     -> the auditor's target, if every word of it is a non-archaic bank form
keep    -> "=" (leave as printed)
context -> "=" with the readings in the note, until a context rule is written
A verification verdict (results/verify-*.tsv: id, agree, target, note) overrides:
disagree turns the row into "=".
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv.archaism import Archaism  # noqa: E402
from rettskriv.bank import Bank  # noqa: E402

AUDIT = ROOT / "out" / "audit"
RESULTS = AUDIT / "results"
FOLDER = {"nob": "bokmal", "nno": "nynorsk"}


def packets() -> dict[str, dict]:
    items = {}
    for path in AUDIT.glob("*.tsv"):
        with open(path) as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                row["source"] = row.get("from") or row.get("form")
                row["packet"] = path.stem
                items[row["id"]] = row
    return items


def verdicts() -> dict[str, dict]:
    out = {}
    for path in sorted(RESULTS.glob("*.tsv")):
        if path.name.startswith("verify-"):
            continue
        with open(path) as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row.get("id"):
                    row["shard"] = path.stem
                    out[row["id"].strip()] = row
    return out


def verifications() -> dict[str, dict]:
    out = {}
    for path in sorted(RESULTS.glob("verify-*.tsv")):
        with open(path) as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row.get("id"):
                    out[row["id"].strip()] = row
    return out


def done_sources(lang: str) -> set[str]:
    items, results = packets(), verdicts()
    return {items[i]["source"] for i in results if i in items and i.startswith(lang)}


def main() -> None:
    items, results, checks = packets(), verdicts(), verifications()
    for lang in ("nob", "nno"):
        bank, archaism = Bank(lang), Archaism(lang)
        rows, seen, rejected = [], set(), 0
        for vid, verdict in sorted(results.items()):
            if not vid.startswith(lang) or vid not in items:
                continue
            item = items[vid]
            source = item["source"].lower()
            if source in seen:
                continue
            kind = verdict["verdict"].strip().lower()
            target = (verdict.get("target") or "").strip().lower()
            note = (verdict.get("note") or "").strip().replace("\n", " ")
            if kind == "ok":
                target = (item.get("to") or "").lower()
            elif kind in ("keep", "context"):
                note = f"{kind}: {target} {note}".strip() if target else f"{kind}: {note}".strip()
                target = "="
            elif kind != "fix":
                continue
            if target != "=":
                words = target.split()
                if not words or not all(bank.common(w) and not archaism.archaic(w) for w in words):
                    note = f"rejected target {target!r}: not a modern bank form. {note}".strip()
                    target, rejected = "=", rejected + 1
            check = checks.get(vid)
            if check and check.get("agree", "").strip().lower() == "no" and target != "=":
                note = f"verifier disagreed ({check.get('target', '')}: {check.get('note', '')}); was {target}"
                target = "="
            if target == source:
                continue
            seen.add(source)
            rows.append((source, target, "", note, f"audit:{verdict['shard']}"))
        path = ROOT / "lexicon" / FOLDER[lang] / "audit.csv"
        core = path.parent / "core.csv"
        curated = set()
        if core.exists():
            with open(core) as handle:
                curated = {r["source"].lower() for r in csv.DictReader(handle) if r["source"]}
        with open(path, "w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["source", "target", "when", "note", "origin"])
            for row in rows:
                if row[0] not in curated:
                    writer.writerow(row)
        print(lang, len(rows), "rows,", rejected, "targets rejected")


if __name__ == "__main__":
    main()
