"""Acceptance sample: paragraphs from every book, original beside modern, each changed
word numbered. Reviewers judge every change; the result is the error rate per 1,000
changed words. Writes out/eval/<name>.md and out/eval/<name>.json.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv import corpus  # noqa: E402
from rettskriv.engine import Engine  # noqa: E402

OUT = ROOT / "out" / "eval"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--seed", default="rettskriv-eval")
    parser.add_argument("--per-book", type=int, default=4)
    parser.add_argument("--min-words", type=int, default=1)
    parser.add_argument("--forms", type=Path, help="only paragraphs that change one of these old forms (one per line)")
    args = parser.parse_args()
    forms = set(args.forms.read_text().split()) if args.forms else None
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / f"{args.name}.json").exists() or (OUT / f"{args.name}.md").exists():
        raise SystemExit("sample name already exists; use a new name")
    rng = random.Random(args.seed)
    engines = {"nob": Engine("nob"), "nno": Engine("nno")}
    units, md = [], [f"# Acceptance sample {args.name}\n"]
    change_id = 0
    for book in corpus.books():
        data = corpus.load(book)
        default = corpus.LANGUAGE.get(data["book"].get("language"), "nob")
        texts = corpus.texts(data)
        for engine in engines.values():
            engine.learn_book(texts)
            engine.year = data.get("printed_year")
        candidates = []
        for item in data["items"]:
            if item.get("kind") != "piece":
                continue
            lang = corpus.detect(" ".join(t for _, t, _ in corpus.units(item)), default)
            if lang not in engines:
                continue
            for path, text, verse in corpus.units(item):
                if len(text.split()) >= args.min_words:
                    candidates.append((item, path, text, verse, lang))
        if forms is not None:
            hits = []
            for candidate in candidates:
                item, path, text, verse, lang = candidate
                result = engines[lang].modernise(text, verse=verse)
                if any(t.word and t.out != t.text and t.lower in forms for t in result.tokens):
                    hits.append(candidate)
            candidates = hits
        for item, path, text, verse, lang in rng.sample(candidates, min(args.per_book, len(candidates))):
            result = engines[lang].modernise(text, verse=verse)
            changes = []
            marked = []
            for t in result.tokens:
                if t.word and t.out != t.text:
                    change_id += 1
                    changes.append({"n": change_id, "at": t.start, "from": t.text, "to": t.out, "why": t.reason})
                    marked.append(f"{t.out}⟨{change_id}⟩")
                else:
                    marked.append(t.out if t.word and t.out is not None else t.text)
            unit = {"book": book, "piece": item["id"], "path": "/".join(map(str, path)), "lang": lang,
                    "original": text, "modern": result.text, "changes": changes}
            units.append(unit)
            md.append(f"\n## {book} {item['id']} {unit['path']} ({lang})\n")
            md.append("**Original**\n\n" + text.replace("\n", "  \n") + "\n")
            md.append("**Modern** (⟨n⟩ follows each changed word)\n\n" + "".join(marked).replace("\n", "  \n") + "\n")
            md.append("Changes: " + "; ".join(f"{c['n']}: {c['from']}→{c['to']}" for c in changes) + "\n")
    (OUT / f"{args.name}.json").write_text(json.dumps(units, ensure_ascii=False, indent=1))
    (OUT / f"{args.name}.md").write_text("\n".join(md))
    words = sum(len(u["original"].split()) for u in units)
    print(f"{len(units)} paragraphs, {words} words, {change_id} changes -> {OUT / args.name}.md")


if __name__ == "__main__":
    main()
