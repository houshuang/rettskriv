"""Fill the N-gram cache for every corpus form the modern bank allows, plus every
rule candidate the bank allows. Resumable; safe to rerun."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rettskriv import corpus  # noqa: E402
from rettskriv.archaism import fetch  # noqa: E402
from rettskriv.bank import Bank  # noqa: E402
from rettskriv.rules import candidates  # noqa: E402
from rettskriv.text import WORD  # noqa: E402


def main() -> None:
    types: dict[str, Counter] = {"nob": Counter(), "nno": Counter()}
    for book in corpus.books():
        data = corpus.load(book)
        lang = corpus.LANGUAGE.get(data["book"].get("language"), "nob")
        for item in data["items"]:
            for block in item.get("blocks", []):
                for w in WORD.findall(block.get("text", "")):
                    types[lang][w.lower()] += 1
    for lang, counter in types.items():
        bank = Bank(lang)
        wanted = []
        for word, _ in counter.most_common():
            if bank.common(word):
                wanted.append(word)
            else:
                wanted.extend(c for level in candidates(word, lang) for c in level if bank.common(c))
        wanted = list(dict.fromkeys(wanted))
        print(lang, len(counter), "types;", len(wanted), "to look up", flush=True)
        fetch(wanted, lang)


if __name__ == "__main__":
    main()
