"""Which forms fell out of use: NB N-gram frequency, 1850–1910 against 1990–2020.

A form the modern bank allows but whose frequency collapsed (sagde, mig, blev,
kunde) is an old spelling of another word, not a modern word. Such forms are only
changed by the curated lexicon and never accepted as rule output.
"""
from __future__ import annotations

import json
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "cache" / "ngram.sqlite"
API = "https://api.nb.no/dhlab/nb_ngram/ngram/query"
OLD = range(1850, 1911)
NEW = range(1990, 2021)
ARCHAIC_RATIO = 0.15


def connect() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS freq (lang TEXT, word TEXT, old REAL, new REAL,"
        " PRIMARY KEY (lang, word))"
    )
    return conn


def fetch(words: list[str], lang: str, batch: int = 20) -> None:
    """Fill the cache for words not yet in it. Case-sensitive lower-case lookups."""
    conn = connect()
    have = {w for (w,) in conn.execute("SELECT word FROM freq WHERE lang=?", (lang,))}
    todo = [w for w in dict.fromkeys(words) if w not in have and "," not in w]
    for i in range(0, len(todo), batch):
        chunk = todo[i : i + batch]
        query = urllib.parse.urlencode(
            {"terms": ",".join(chunk), "lang": lang, "case_sens": 1, "freq": "relative", "corpus": "bok"}
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(f"{API}?{query}", timeout=60) as response:
                    data = json.load(response)
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
        found = {}
        for series in data:
            values = {int(v["x"]): v["y"] for v in series["values"]}
            old = sum(values.get(y, 0.0) for y in OLD) / len(OLD)
            new = sum(values.get(y, 0.0) for y in NEW) / len(NEW)
            found[series["key"]] = (old, new)
        rows = [(lang, w, *found.get(w, (0.0, 0.0))) for w in chunk]
        conn.executemany("INSERT OR REPLACE INTO freq VALUES (?,?,?,?)", rows)
        conn.commit()
    conn.close()


class Archaism:
    def __init__(self, lang: str):
        self.lang = lang
        self.freq: dict[str, tuple[float, float]] = {}
        if DB.exists():
            conn = connect()
            for word, old, new in conn.execute("SELECT word, old, new FROM freq WHERE lang=?", (lang,)):
                self.freq[word] = (old, new)
            conn.close()

    def ratio(self, word: str) -> float | None:
        old, new = self.freq.get(word.lower(), (0.0, 0.0))
        if old <= 0:
            return None
        return new / old

    def modern(self, word: str) -> float:
        """Relative frequency 1990–2020 of the form exactly as given (case-sensitive)."""
        return self.freq.get(word, (0.0, 0.0))[1]

    def archaic(self, word: str) -> bool:
        ratio = self.ratio(word)
        return ratio is not None and ratio < ARCHAIC_RATIO
