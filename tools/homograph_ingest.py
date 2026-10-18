"""Write lexicon/<lang>/homograph.csv from the homograph screen results.

A risky form is changed only in the context the reviewer gave and is otherwise left as
printed; with no context it is always left as printed. homograph.csv is authoritative
for its forms (see rettskriv/lexicon.py), so it overrides core and audit rows.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv import lexicon  # noqa: E402
from rettskriv.lexicon import parse_when  # noqa: E402

FOLDER = {"nob": "bokmal", "nno": "nynorsk"}
# the first screen (forms changed five times or more) and the tail (two to four)
SCREENS = [ROOT / "out" / "audit" / "homograph", ROOT / "out" / "audit" / "homograph-tail"]


def main() -> None:
    for lang in ("nob", "nno"):
        out = ROOT / "lexicon" / FOLDER[lang] / "homograph.csv"
        out.unlink(missing_ok=True)
        # a form with curated context rows is already decided by context
        contextual = {
            source for source, entries in lexicon.load(lang).items()
            if any(e.when and not e.origin.startswith("audit") for e in entries)
        }
        items = {}
        for path in sorted(p for screen in SCREENS for p in screen.glob(f"{lang}-homograph-*.tsv")):
            with open(path) as handle:
                items.update({r["id"]: r for r in csv.DictReader(handle, delimiter="\t")})
        rows, unanswered, bad = [], 0, 0
        answered = set()
        for path in sorted(p for screen in SCREENS for p in (screen / "results").glob(f"{lang}-homograph-*.tsv")):
            with open(path) as handle:
                for r in csv.DictReader(handle, delimiter="\t"):
                    item = items.get(r["id"])
                    if not item:
                        continue
                    answered.add(r["id"])
                    if r["verdict"].strip().lower() != "risky":
                        continue
                    source, target = item["from"].lower(), item["to"].lower()
                    if source in contextual:
                        continue
                    note = (r.get("note") or "").strip().replace("\n", " ")
                    when = (r.get("when") or "").strip()
                    try:
                        parse_when(when)
                    except Exception:
                        when, bad = "", bad + 1
                    if when:
                        rows.append((source, target, when, note, "homograph"))
                    rows.append((source, "=", "", note, "homograph"))
        unanswered = len(set(items) - answered)
        with open(out, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["source", "target", "when", "note", "origin"])
            writer.writerows(rows)
        print(lang, len(items), "screened,", sum(r[1] == "=" for r in rows), "risky,",
              sum(r[1] != "=" for r in rows), "with a safe context,", bad, "bad contexts,", unanswered, "unanswered")


if __name__ == "__main__":
    main()
