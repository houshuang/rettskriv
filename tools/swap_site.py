"""Swap a finished build folder into place in one step.

The target is the argument's name with `.next` stripped, beside it: out/site.next goes
to out/site, out/epub.next to out/epub. renamex_np(RENAME_SWAP) exchanges the two
directory entries atomically, so a reader of the target sees either the old tree or
the new one, never a mix inside one book folder or a missing folder. The previous
tree is kept as <target>.prev-<UTC stamp>. Refuses while any process holds a file
open under the target, or when the new build lacks a book folder (site) or a file
(epub) the target has. When the target does not exist yet, the folder is renamed.

    python3 tools/swap_site.py out/site.next
    python3 tools/swap_site.py out/epub.next
"""
from __future__ import annotations

import ctypes
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENAME_SWAP = 0x2


def main() -> None:
    new = Path(sys.argv[1]).resolve()
    if new.suffix != ".next":
        sys.exit(f"{new}: expected a folder named <target>.next")
    target = new.with_suffix("")
    if not new.is_dir() or new.parent != ROOT / "out":
        sys.exit(f"{new}: not a folder beside {target}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not target.exists():
        new.rename(target)
        print(json.dumps({"swapped_utc": stamp, target.name: str(target), "previous": None}))
        return
    is_site = target.name == "site"
    have = {p.name for p in target.iterdir() if p.is_dir() == is_site}
    got = {p.name for p in new.iterdir() if p.is_dir() == is_site}
    missing = have - got
    if missing:
        sys.exit(f"refused: the new build lacks {'books' if is_site else 'files'} {sorted(missing)}")
    busy = subprocess.run(["lsof", "-Fn", "+D", str(target)], capture_output=True, text=True).stdout.strip()
    if busy:
        sys.exit(f"refused: files under out/{target.name} are open:\n" + busy)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.renamex_np(str(new).encode(), str(target).encode(), RENAME_SWAP) != 0:
        sys.exit(f"renamex_np failed: errno {ctypes.get_errno()}")
    previous = target.parent / f"{target.name}.prev-{stamp}"
    new.rename(previous)
    print(json.dumps({"swapped_utc": stamp, target.name: str(target), "previous": str(previous)}))


if __name__ == "__main__":
    main()
