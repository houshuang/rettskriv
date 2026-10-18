"""Download Norsk ordbank (Språkbanken, CC BY 4.0) into data/ordbank/: bokmål 2005 and
nynorsk 2012, the word banks every modern form is checked against. About 25 MB.

    python3 -m rettskriv.fetch_ordbank
"""
from __future__ import annotations

import tarfile
import urllib.request

from .bank import ORDBANK, SOURCES

URL = "https://www.nb.no/sbfil/leksikalske_databaser/ordbank/{name}.tar.gz"


def main() -> None:
    ORDBANK.mkdir(parents=True, exist_ok=True)
    for source in SOURCES.values():
        if source.exists():
            print(source.parent.name, "present")
            continue
        name = source.parent.name
        archive = ORDBANK / f"{name}.tar.gz"
        if not archive.exists():
            print("downloading", name, flush=True)
            urllib.request.urlretrieve(URL.format(name=name), archive)
        with tarfile.open(archive) as tar:
            tar.extractall(source.parent, filter="data")  # the archives have no top folder
        if not source.exists():
            raise SystemExit(f"{archive}: did not contain {source.relative_to(ORDBANK)}")
        print(name, "ready")


if __name__ == "__main__":
    main()
