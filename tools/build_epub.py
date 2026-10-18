"""Build the modern-spelling EPUBs with the Lesebok EPUB builder itself.

Per book, two files flat in the output folder:

  <book>-moderne.epub    the edition as built, with the modern layer applied
  <book>-parallell.epub  every block as printed, its modern form beneath it in smaller
                         grey type (skipped where the two are identical)

The edition's own build_epub.build runs with load, SITE, blocks_html and a few other
names patched; nothing under bookifier is written. Both files are run through epubcheck.
Swap a finished folder in with `python3 tools/swap_site.py out/epub.next`.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import time
import types
import uuid
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from render_site import LESEBOK_SCRIPTS, apply  # noqa: E402

sys.path.insert(0, str(LESEBOK_SCRIPTS))
import build_epub  # noqa: E402
import render  # noqa: E402

LAYERS = ROOT / "out" / "modern"
OUT = ROOT / "out" / "epub.next"
LESEBOK_SITE = build_epub.SITE
BASE_CSS = build_epub.CSS
BASE_XHTML = build_epub.xhtml
BASE_BLOCKS_HTML = build_epub.blocks_html

KINDS = {
    "moderne": {"title": " (moderne rettskriving)", "css": ""},
    "parallell": {"title": " (parallell: original og moderne)", "css": """
div.mod { font-size: .82em; color: #666; margin: .1em 0 1em; }
div.mod p.stanza { margin-bottom: 0; }
div.mod h3 { font-size: 1em; }
.title p.note { font-size: .8em; color: #666; margin-top: 2em; }
"""},
}
NOTE = ('<p class="note">Denne utgaven viser teksten slik den ble trykt, og under hvert avsnitt '
        'og hver strofe den samme teksten i moderne rettskriving, med mindre og grå skrift.</p>')
LANG = {"nob": "nb", "nno": "nn"}


def null_marker(seq: int) -> str:
    return ""


def parallel_blocks(bk: dict, blocks: list[dict], start_seq: int, marker, img, xhtml: bool = False) -> str:
    shown = {start_seq}

    def once(seq: int) -> str:
        if seq in shown:
            return ""
        shown.add(seq)
        return marker(seq)

    out = []
    for block in blocks:
        printed = BASE_BLOCKS_HTML(bk, [block], start_seq, once, img, xhtml)
        out.append(printed)
        modern = block.get("_modern")
        if modern is None or block["type"] == "fig":
            continue
        same = BASE_BLOCKS_HTML(bk, [modern], start_seq, null_marker, img, xhtml)
        if same != BASE_BLOCKS_HTML(bk, [block], start_seq, null_marker, img, xhtml):
            out.append(f'<div class="mod">{same}</div>')
    return "\n".join(out)


def make_load(layer: dict, kind: str):
    suffix = KINDS[kind]["title"]

    def load(bid: str) -> dict:
        printed = render.load(bid)
        modern = apply(render.load(bid), layer)
        if kind == "parallell":
            for pc, mpc in zip(printed["pieces"], modern["pieces"]):
                for block, mblock in zip(pc["blocks"], mpc["blocks"]):
                    block["_modern"] = mblock
            book = printed
        else:
            book = modern
        book["book"]["title"] += suffix
        return book

    return load


def patch_language(path: Path, lang: str) -> None:
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w") as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "OEBPS/content.opf":
                text = data.decode()
                for old in ("da", "nn"):
                    text = text.replace(f"<dc:language>{old}</dc:language>", f"<dc:language>{lang}</dc:language>")
                data = text.encode()
            dst.writestr(info, data, compress_type=info.compress_type)
    tmp.replace(path)


def build(bid: str, layer: dict, kind: str, out_dir: Path) -> Path:
    lang = LANG[Counter(e["lang"] for e in layer["items"].values()).most_common(1)[0][0]] if layer["items"] else "nb"
    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp)
        (site / bid).mkdir()
        (site / bid / "img").symlink_to(LESEBOK_SITE / bid / "img")
        build_epub.SITE = site
        build_epub.load = make_load(layer, kind)
        build_epub.CSS = BASE_CSS + KINDS[kind]["css"]
        build_epub.uuid = types.SimpleNamespace(
            NAMESPACE_URL=uuid.NAMESPACE_URL, uuid5=lambda ns, name: uuid.uuid5(ns, f"{name}-{kind}"))
        if kind == "parallell":
            build_epub.blocks_html = parallel_blocks
            build_epub.xhtml = lambda title, body: BASE_XHTML(
                title, body.replace("</div>", NOTE + "</div>", 1) if 'class="title"' in body else body)
        else:
            build_epub.blocks_html = BASE_BLOCKS_HTML
            build_epub.xhtml = BASE_XHTML
        built = build_epub.build(bid)
        target = out_dir / f"{bid}-{kind}.epub"
        shutil.move(built, target)
    patch_language(target, lang)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("books", nargs="*")
    parser.add_argument("--layers", type=Path, default=LAYERS)
    parser.add_argument("--out", type=Path, default=OUT, help="output folder; build beside out/epub and swap it in with tools/swap_site.py")
    args = parser.parse_args()
    books = args.books or sorted(p.stem for p in args.layers.glob("*.json"))
    args.out.mkdir(parents=True, exist_ok=True)
    failed = 0
    started = time.time()
    total = 0
    for bid in books:
        layer = json.loads((args.layers / f"{bid}.json").read_text())
        for kind in KINDS:
            path = build(bid, layer, kind, args.out)
            res = subprocess.run(["epubcheck", "-q", str(path)], capture_output=True, text=True)
            total += path.stat().st_size
            print(f"{path.name} {path.stat().st_size // 1024} KB epubcheck exit {res.returncode}", flush=True)
            if res.returncode:
                failed += 1
                for line in (res.stdout + res.stderr).strip().splitlines()[-8:]:
                    print("  ", line)
    print(f"{len(books)} books, {total // 1024 // 1024} MB, {time.time() - started:.0f} s, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
