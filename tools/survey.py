"""Run the engine over the library and report what it changes and what it leaves.

Writes out/survey/<lang>-*.tsv work lists and prints a summary.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rettskriv import corpus  # noqa: E402
from rettskriv.engine import Engine  # noqa: E402

OUT = ROOT / "out" / "survey"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--books", nargs="*")
    parser.add_argument("--kwic", type=int, default=3, help="examples kept per pair")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    engines: dict[str, Engine] = {}
    flags: dict[str, Counter] = defaultdict(Counter)
    pairs: dict[str, Counter] = defaultdict(Counter)
    left: dict[str, Counter] = defaultdict(Counter)
    examples: dict[tuple, list] = defaultdict(list)
    languages = Counter()
    for book in args.books or corpus.books():
        data = corpus.load(book)
        default = corpus.LANGUAGE.get(data["book"].get("language"), "nob")
        texts = corpus.texts(data)
        for lang in ("nob", "nno"):
            engine = engines.get(lang) or engines.setdefault(lang, Engine(lang))
            engine.learn_book(texts)
            engine.year = data.get("printed_year")
        print(book, "nouncaps" if engines[default].nouncaps else "lowercase nouns",
              len(engines[default].names), "names", flush=True)
        for item in data["items"]:
            if item.get("kind") != "piece":
                continue
            lang = corpus.detect(" ".join(text for _, text, _ in corpus.units(item)), default)
            languages[(book, lang)] += 1
            if lang not in engines:
                continue
            engine = engines[lang]
            for _, text, verse in corpus.units(item):
                result = engine.modernise(text, verse=verse)
                flags[lang].update(result.flags)
                for t in result.tokens:
                    if not t.word:
                        continue
                    if t.out != t.text:
                        key = (t.lower, (t.out or "").lower(), t.reason.split(":")[0])
                        pairs[lang][key] += 1
                    elif t.reason == "modern" and t.lower not in engine.lexicon and (
                        (ratio := engine.archaism.ratio(t.lower)) is not None and ratio < 0.5
                    ):
                        key = (t.lower, "in-bank", f"{ratio:.3f}")
                        left[lang][key] += 1
                    elif t.reason in ("unknown", "ambiguous", "archaic-unresolved", "pending"):
                        key = (t.lower, t.reason, t.meta.get("candidates", ""))
                        left[lang][key] += 1
                    else:
                        continue
                    if len(examples[(lang, key)]) < args.kwic:
                        s = max(0, t.start - 60)
                        examples[(lang, key)].append(
                            f"{book}/{item.get('id')}: …{text[s:t.start]}[{t.text}→{t.out}]{text[t.start + len(t.text):t.start + len(t.text) + 60]}…".replace("\n", " / ")
                        )
    for lang in flags:
        total = sum(flags[lang].values())
        print(f"\n== {lang}: {total} words")
        for reason, n in flags[lang].most_common():
            print(f"  {reason:22s} {n:8d}  {100 * n / total:5.1f}%")
        with open(OUT / f"{lang}-changes.tsv", "w") as handle:
            handle.write("count\tfrom\tto\twhy\texamples\n")
            for (src, tgt, why), n in pairs[lang].most_common():
                handle.write(f"{n}\t{src}\t{tgt}\t{why}\t{' || '.join(examples[(lang, (src, tgt, why))])}\n")
        with open(OUT / f"{lang}-inbank.tsv", "w") as handle:
            handle.write("count\tform\treason\tratio\texamples\n")
            for (src, why, cands), n in left[lang].most_common():
                if why == "in-bank" and n >= 3:
                    handle.write(f"{n}\t{src}\t{why}\t{cands}\t{' || '.join(examples[(lang, (src, why, cands))])}\n")
        with open(OUT / f"{lang}-left.tsv", "w") as handle:
            handle.write("count\tform\treason\tcandidates\texamples\n")
            for (src, why, cands), n in left[lang].most_common():
                if why == "in-bank":
                    continue
                handle.write(f"{n}\t{src}\t{why}\t{cands}\t{' || '.join(examples[(lang, (src, why, cands))])}\n")
        print(f"  distinct changed pairs {len(pairs[lang])}, distinct left forms {len(left[lang])}")
    skipped = Counter(lang for (book, lang), n in languages.items() for _ in range(n))
    print("\npieces by detected language:", dict(skipped))
    with open(OUT / "languages.json", "w") as handle:
        json.dump({f"{b}:{l}": n for (b, l), n in languages.items()}, handle, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
