"""Write the modern-spelling layer of each Lesebok edition: out/modern/<book>.json.

The layer mirrors book.json: for each piece, the modern text of every field that
changed, keyed by its path ("title", "blocks/3/text", "blocks/4/lines",
"notes/0/text"). Paragraph marks (page breaks at character offsets) are remapped
into the modern text. A field absent from the layer is unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv import corpus  # noqa: E402
from rettskriv.engine import Engine  # noqa: E402

OUT = ROOT / "out" / "modern"


def version() -> dict:
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    digest = hashlib.sha256()
    for path in sorted((ROOT / "lexicon").rglob("*.csv")):
        digest.update(path.read_bytes())
    return {"commit": commit, "lexicon": digest.hexdigest()[:12]}


def build(book: str, engines: dict[str, Engine], *, resolver=None) -> dict:
    data = corpus.load(book)
    default = corpus.LANGUAGE.get(data["book"].get("language"), "nob")
    texts = corpus.texts(data)
    for engine in engines.values():
        engine.learn_book(texts)
        engine.year = data.get("printed_year")
    items, stats = {}, Counter()
    for item in data["items"]:
        if item.get("kind") != "piece":
            continue
        lang = corpus.detect(" ".join(text for _, text, _ in corpus.units(item)), default)
        stats[f"pieces:{lang}"] += 1
        if lang not in engines:
            continue
        engine = engines[lang]
        fields = {}
        for path, text, verse in corpus.units(item):
            result = engine.modernise(text, verse=verse, resolver=resolver)
            for t in result.tokens:
                if t.word:
                    stats["words"] += 1
                    stats["changed"] += t.out != t.text
            if result.text == text:
                continue
            key = "/".join(str(p) for p in path)
            if path[-1] == "lines":
                lines = result.text.split("\n")
                assert len(lines) == text.count("\n") + 1, (book, item["id"], key)
                fields[key] = lines
            elif path[0] == "blocks" and data_block(item, path).get("marks"):
                marks = [[result.map_offset(offset), seq] for offset, seq in data_block(item, path)["marks"]]
                fields[key] = {"text": result.text, "marks": marks}
            else:
                fields[key] = result.text
        if fields:
            items[item["id"]] = {"lang": lang, "fields": fields}
    return {"book": book, "version": version(), "items": items, "stats": dict(stats)}


def data_block(item: dict, path: tuple) -> dict:
    return item["blocks"][path[1]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("books", nargs="*")
    parser.add_argument("--out", type=Path, default=OUT, help="layer folder (default out/modern)")
    parser.add_argument("--dependency-models", type=Path,
                        help="Opt in to dependency recovery with installed local Stanza models")
    args = parser.parse_args()
    resolver = None
    if args.dependency_models:
        import torch
        from rettskriv.dependency import DependencyResolver
        torch.set_num_threads(4)
        resolver = DependencyResolver(args.dependency_models)
    args.out.mkdir(parents=True, exist_ok=True)
    engines = {"nob": Engine("nob"), "nno": Engine("nno")}
    for book in args.books or corpus.books():
        layer = build(book, engines, resolver=resolver)
        if resolver is not None:
            layer["version"]["dependency_recovery"] = True
            if resolver.errors:
                raise RuntimeError(f"Dependency parsing failed; refusing incomplete build: {resolver.errors}")
        with open(args.out / f"{book}.json", "w", encoding="utf-8") as handle:
            json.dump(layer, handle, ensure_ascii=False, indent=1)
        s = layer["stats"]
        print(f"{book}: {s.get('changed', 0)}/{s.get('words', 0)} words changed, {len(layer['items'])} pieces")


if __name__ == "__main__":
    main()
