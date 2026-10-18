"""Render the modern-spelling piece pages with the Lesebok site builder itself.

The edition's own build_site.build_book runs with the modern layer applied to the
book, writing out/site/<book>/<nnn>.html. Only piece pages are kept; images and the
page viewer belong to the original edition.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESEBOK_SCRIPTS = Path("/Users/stian/src/bookifier/lesebok/scripts")
LAYERS = ROOT / "out" / "modern"
SITE = ROOT / "out" / "site"

sys.path.insert(0, str(LESEBOK_SCRIPTS))
import build_site  # noqa: E402
import render  # noqa: E402


def apply(book: dict, layer: dict) -> dict:
    pieces = {piece["id"]: piece for piece in book["pieces"]}
    for piece_id, entry in layer["items"].items():
        piece = pieces[piece_id]
        for key, value in entry["fields"].items():
            path = [int(p) if p.isdigit() else p for p in key.split("/")]
            if path[-1] == "lines":
                lines = piece["blocks"][path[1]]["lines"]
                assert len(lines) == len(value), (book["id"], piece_id, key)
                for line, text in zip(lines, value):
                    line["t"] = text
            elif isinstance(value, dict):
                block = piece["blocks"][path[1]]
                block["text"], block["marks"] = value["text"], value["marks"]
            else:
                target = piece
                for p in path[:-1]:
                    target = target[p]
                target[path[-1]] = value
    return book


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("books", nargs="*")
    parser.add_argument("--layers", type=Path, default=LAYERS)
    parser.add_argument("--site", type=Path, default=SITE, help="output folder; build beside out/site and swap it in with tools/swap_site.py")
    args = parser.parse_args()
    books = args.books or sorted(p.stem for p in args.layers.glob("*.json"))
    original_load = render.load
    build_site.SITE = args.site
    build_site.link_file = lambda src, dst: None
    for book_id in books:
        layer = json.loads((args.layers / f"{book_id}.json").read_text())
        build_site.load = lambda bid, layer=layer: apply(original_load(bid), layer)
        build_site.build_book(book_id)
        out = args.site / book_id
        for path in out.iterdir():
            if path.is_dir() or not path.name[:3].isdigit():
                if path.is_dir():
                    path.rmdir()
                else:
                    path.unlink()
        print(book_id, len(list(out.glob("*.html"))), "pages")


if __name__ == "__main__":
    main()
