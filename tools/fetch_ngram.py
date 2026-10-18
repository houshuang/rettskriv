"""Fill the N-gram cache for every corpus form the modern bank allows, plus every
rule candidate the bank allows. Resumable; safe to rerun.

    python3 tools/fetch_ngram.py                 # look up what the cache lacks
    python3 tools/fetch_ngram.py --refresh-zero  # re-ask forms cached with no counts
    python3 tools/fetch_ngram.py --export        # write data/ngram.tsv.gz from the cache
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rettskriv import corpus  # noqa: E402
from rettskriv.archaism import DB, connect, export, fetch  # noqa: E402
from rettskriv.bank import Bank  # noqa: E402
from rettskriv.rules import candidates  # noqa: E402
from rettskriv.text import WORD  # noqa: E402


def main() -> None:
    if "--export" in sys.argv:
        print(export(), "forms written")
        return
    if "--refresh-zero" in sys.argv and DB.exists():
        conn = connect()
        for lang in ("nob", "nno"):
            words = [w for (w,) in conn.execute("SELECT word FROM freq WHERE lang=? AND old=0 AND new=0", (lang,))]
            print(lang, len(words), "without counts", flush=True)
            fetch(words, lang, refresh_zero=True)
        conn.close()
        return
    types: dict[str, Counter] = {"nob": Counter(), "nno": Counter()}
    for book in corpus.books():
        data = corpus.load(book)
        lang = corpus.LANGUAGE.get(data["book"].get("language"), "nob")
        for text in corpus.texts(data):
            for w in WORD.findall(text):
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
