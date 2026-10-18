"""Swap a finished site build into out/site in one step.

renamex_np(RENAME_SWAP) exchanges the two directory entries atomically, so a reader
of out/site sees either the old tree or the new one, never a mix inside one book
folder or a missing folder. The previous tree is kept as out/site.prev-<UTC stamp>.
Refuses while any process holds a file open under out/site.

    python3 tools/swap_site.py out/site.next
"""
from __future__ import annotations

import ctypes
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "out" / "site"
RENAME_SWAP = 0x2


def main() -> None:
    new = Path(sys.argv[1]).resolve()
    if not new.is_dir() or new.parent != SITE.parent:
        sys.exit(f"{new}: not a folder beside {SITE}")
    books = {p.name for p in SITE.iterdir() if p.is_dir()}
    missing = books - {p.name for p in new.iterdir() if p.is_dir()}
    if missing:
        sys.exit(f"refused: the new build lacks {sorted(missing)}")
    busy = subprocess.run(["lsof", "-Fn", "+D", str(SITE)], capture_output=True, text=True).stdout.strip()
    if busy:
        sys.exit("refused: files under out/site are open:\n" + busy)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.renamex_np(str(new).encode(), str(SITE).encode(), RENAME_SWAP) != 0:
        sys.exit(f"renamex_np failed: errno {ctypes.get_errno()}")
    previous = SITE.parent / f"site.prev-{stamp}"
    new.rename(previous)
    print(json.dumps({"swapped_utc": stamp, "site": str(SITE), "previous": str(previous)}))


if __name__ == "__main__":
    main()
