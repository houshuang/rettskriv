"""Freeze reproducible external excerpts without inventing gold annotations.

python3 -m tools.sample_external catalogue.json cases.json --per-book 8 --seed study1
Catalogue: [{book, author, lang, path, source, optional year, optional nouncaps}].
Paths are relative to the catalogue. Texts use blank lines between blocks/pages.
No rewriting, dehyphenation or modernisation occurs during sampling.
"""
import argparse
import hashlib
import json
import random
import re
from pathlib import Path

from tools.benchmark import prepare


def sample(catalogue: list[dict], directory: Path, per_book: int, seed: str) -> list[dict]:
    if per_book < 1:
        raise ValueError('per-book must be positive')
    cases=[]
    for book in sorted(catalogue,key=lambda b:b['book']):
        if not book.get('source'):
            raise ValueError('every text needs a source citation')
        raw=(directory/book['path']).read_bytes()
        text=raw.decode('utf-8-sig')
        blocks=re.split(r'\r?\n\s*\r?\n',text)
        eligible=[(i,b) for i,b in enumerate(blocks) if len(b.split())>=40]
        if not eligible:
            raise ValueError(f"no eligible blocks: {book['book']}")
        rng=random.Random(seed+':'+book['book'])
        for i,block in sorted(rng.sample(eligible,min(per_book,len(eligible)))):
            case={k:book[k] for k in ('book','author','lang','source')}
            case.update({k:book[k] for k in ('year','nouncaps') if k in book})
            case.update(id=f"{book['book']}:{i}",split='test',original=block,
                        source_block=i,source_sha256=hashlib.sha256(raw).hexdigest())
            cases.append(case)
    return prepare(cases)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('catalogue',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--per-book',type=int,default=8);p.add_argument('--seed',default='rettskriv-external-v1')
    a=p.parse_args()
    if a.out.exists():p.error('output exists; frozen samples are not overwritten')
    cases=sample(json.loads(a.catalogue.read_text(encoding='utf-8')),a.catalogue.parent,a.per_book,a.seed)
    with a.out.open('x',encoding='utf-8') as handle:
        json.dump(cases,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(f'{len(cases)} unadjudicated excerpts; {sum(len(c["decisions"]) for c in cases)} words')


if __name__=='__main__':main()
