"""Validate complete per-change reviews before reporting acceptance results.

Review TSV columns: n, kind, from, to, better, note. Every numbered change must
occur exactly once, including kind=ok. Misses have an empty n. Older error-only
reviews remain historical evidence but cannot certify a new acceptance run.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

EVAL = Path(__file__).resolve().parent.parent / "out" / "eval"
FIELDS = ["n", "kind", "from", "to", "better", "note"]
KINDS = {"ok", "meaning", "form", "case", "miss"}


def validate(units: list[dict], rows: list[dict]) -> tuple[int, Counter]:
    changes = {}
    for unit in units:
        for change in unit["changes"]:
            if change["n"] in changes:
                raise ValueError(f"duplicate sample ID: {change['n']}")
            changes[change["n"]] = change
    seen = set()
    for row in rows:
        if any(row.get(key) is None for key in FIELDS):
            raise ValueError("review must contain all TSV columns")
        kind, n = row["kind"].strip(), row["n"].strip()
        if kind not in KINDS:
            raise ValueError(f"unknown review kind: {kind!r}")
        if kind == "miss":
            if n or not row["from"].strip():
                raise ValueError("miss must have empty n and nonempty from")
            continue
        if not n.isdigit() or int(n) not in changes:
            raise ValueError(f"unknown change ID: {n!r}")
        n = int(n)
        if n in seen:
            raise ValueError(f"duplicate review ID: {n}")
        seen.add(n)
        if any(row[key] != changes[n][key] for key in ("from", "to")):
            raise ValueError(f"review does not match sampled change {n}")
    missing = changes.keys() - seen
    if missing:
        raise ValueError(f"unreviewed changes ({len(missing)}): {sorted(missing)[:10]}")
    if not changes:
        raise ValueError("sample contains no changes; cannot estimate change-error rate")
    return len(changes), Counter(row["kind"].strip() for row in rows)


def report(name: str) -> tuple[int, Counter]:
    parts = sorted((EVAL / "parts").glob(f"{name}-p*.md"))
    reviews = sorted((EVAL / "parts").glob(f"{name}-p*.review.tsv"))
    if not parts or {p.with_suffix('.review.tsv') for p in parts} != set(reviews):
        raise ValueError(f"{name}: missing parts/reviews or unexpected reviewer files")
    rows = []
    for path in reviews:
        with path.open(encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle, delimiter="\t"))
    units = json.loads((EVAL / f"{name}.json").read_text())
    total, kinds = validate(units, rows)
    with (EVAL / f"{name}.review.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{name}: {total} reviewed changes, {dict(kinds)}, meaning {kinds['meaning'] / total:.3%}")
    return total, kinds


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python3 tools/accept_report.py SAMPLE [SAMPLE ...]")
    total, meaning = 0, 0
    try:
        for name in sys.argv[1:]:
            n, kinds = report(name)
            total += n
            meaning += kinds["meaning"]
    except ValueError as exc:
        raise SystemExit(f"INCOMPLETE/INVALID REVIEW: {exc}") from exc
    print(f"total: {meaning} meaning errors in {total} reviewed changes = {meaning / total:.3%}")


if __name__ == "__main__":
    main()
