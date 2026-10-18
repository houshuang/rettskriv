"""Split an acceptance sample into reviewer parts: out/eval/parts/<name>-pN.md.

    python3 tools/split_sample.py accept-17 [--parts 4]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

EVAL = Path(__file__).resolve().parent.parent / "out" / "eval"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--parts", type=int, default=4)
    args = parser.parse_args()
    _, *sections = re.split(r"\n(?=## )", (EVAL / f"{args.name}.md").read_text())
    size = -(-len(sections) // args.parts)
    (EVAL / "parts").mkdir(exist_ok=True)
    for i in range(args.parts):
        chunk = sections[i * size : (i + 1) * size]
        (EVAL / "parts" / f"{args.name}-p{i}.md").write_text(f"# {args.name} part {i}\n\n" + "\n".join(chunk))
    print(args.name, len(sections), "paragraphs in", args.parts, "parts")


if __name__ == "__main__":
    main()
