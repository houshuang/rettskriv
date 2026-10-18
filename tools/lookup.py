"""Look up forms in the modern word bank: python3 tools/lookup.py [--nn] form ...

Prints each form, whether the bank allows it, its tags and its NB N-gram ratio
(modern use / 1850–1910 use; below 0.15 means the form fell out of use)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rettskriv.archaism import Archaism  # noqa: E402
from rettskriv.bank import Bank  # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    lang = "nob"
    if args and args[0] in ("--nn", "--nno"):
        lang, args = "nno", args[1:]
    bank, archaism = Bank(lang), Archaism(lang)
    for form in args:
        tags = sorted(bank.tags(form))
        ratio = archaism.ratio(form)
        print(f"{form}\t{'YES' if tags else 'no'}\t{','.join(tags)}\t{'' if ratio is None else f'{ratio:.3f}'}")


if __name__ == "__main__":
    main()
