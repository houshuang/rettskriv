"""Offline Apertium analysis comparison. No Apertium dependency in the engine.

Use python3 -m tools.apertium_probe CASES.json --data-dir DIR --lt-proc PATH
--cg-proc PATH --out FILE. DIR contains nob/nob.automorf.bin, nob/nob.seg.rlx.bin,
nob/nob.rlx.bin, and corresponding nno files. CASES follow tools.benchmark.
Outputs recognition and ambiguity counts, NOT normalisation accuracy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from rettskriv import book_engine
from tools.benchmark import validate_cases


def escape_text(text: str) -> str:
    return re.sub(r'([\\\[\]{}^$/@<>])', r'\\\1', text)


def units(stream: str) -> list[dict]:
    """Read Apertium lexical units, respecting backslash-escaped delimiters."""
    result, fields, current = [], None, []
    escaped = False
    for char in stream:
        if escaped:
            if fields is not None:
                current.append(char)
            escaped = False
            continue
        if char == '\\':
            escaped = True
        elif char == '^':
            if fields is not None:
                raise ValueError('nested Apertium lexical unit')
            fields, current = [], []
        elif fields is not None and char in '/$':
            fields.append(''.join(current)); current = []
            if char == '$':
                if len(fields) < 2:
                    raise ValueError('lexical unit has no analyses')
                result.append(dict(surface=fields[0], readings=fields[1:]))
                fields = None
        elif fields is not None:
            current.append(char)
    if fields is not None or escaped:
        raise ValueError('incomplete Apertium stream')
    return result


class Analyzer:
    def __init__(self, data_dir: Path, lt_proc: Path, cg_proc: Path):
        self.data_dir, self.lt_proc, self.cg_proc = data_dir, lt_proc, cg_proc

    def analyze(self, text: str, lang: str, disambiguate: bool = True) -> list[dict]:
        if lang not in {'nob', 'nno'}:
            raise ValueError('unsupported language')
        folder = self.data_dir / lang
        def run(command, value):
            return subprocess.run([str(x) for x in command], input=value, text=True,
                                  capture_output=True, check=True, timeout=60).stdout
        stream = run([self.lt_proc, '-w', '-e', folder/f'{lang}.automorf.bin'], escape_text(text))
        if disambiguate:
            stream = run([self.cg_proc, folder/f'{lang}.seg.rlx.bin'], stream)
            stream = run([self.cg_proc, '-w', folder/f'{lang}.rlx.bin'], stream)
        return units(stream)


def statistics(analyses: list[dict]) -> Counter:
    counts = Counter()
    for unit in analyses:
        if not any(c.isalpha() for c in unit['surface']):
            continue
        counts['word_cohorts'] += 1
        readings = unit['readings']
        counts['unknown'] += all(r.startswith('*') for r in readings)
        counts['guessed'] += any('<cgguess>' in r for r in readings)
        counts['ambiguous'] += len(readings) > 1
        counts['single_reading'] += len(readings) == 1 and not readings[0].startswith('*')
    return counts


def compare(cases: list[dict], analyzer: Analyzer) -> dict:
    validate_cases(cases)
    grouped = defaultdict(list)
    for c in cases:
        grouped[(c['book'],c['lang'])].append(c)
    totals = defaultdict(Counter)
    records = []
    for (_, lang), group in grouped.items():
        eng = book_engine([c['original'] for c in group], lang)
        nouncaps = eng.nouncaps
        for case in group:
            eng.nouncaps = case.get('nouncaps', nouncaps)
            eng.year = case.get('year')
            modern = eng.modernise(case['original'], verse=case.get('verse',False), protected=case.get('protected'))
            record = dict(id=case['id'],lang=lang,variants={})
            for name, text in [('original',case['original']),('rettskriv',modern.text)]:
                raw = analyzer.analyze(text,lang,False)
                contextual = analyzer.analyze(text,lang)
                record['variants'][name] = dict(text=text,morph=raw,cg=contextual)
                totals[f'{lang}:{name}:morph'].update(statistics(raw))
                totals[f'{lang}:{name}:cg'].update(statistics(contextual))
            records.append(record)
    return dict(metric='recognition-and-ambiguity-not-accuracy',summary=dict(totals),cases=records)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('cases',type=Path)
    p.add_argument('--data-dir',type=Path,required=True)
    p.add_argument('--lt-proc',type=Path,required=True)
    p.add_argument('--cg-proc',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():
        p.error('output already exists; use a new name')
    cases=json.loads(a.cases.read_text(encoding='utf-8'))
    result=compare(cases,Analyzer(a.data_dir,a.lt_proc,a.cg_proc))
    resources=[a.cases,a.lt_proc,a.cg_proc]
    for lang in sorted({c['lang'] for c in cases}):
        resources.extend(a.data_dir/lang/f'{lang}.{suffix}'
                         for suffix in ('automorf.bin','seg.rlx.bin','rlx.bin'))
    result['resources']=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                         for p in resources]
    with a.out.open('x',encoding='utf-8') as handle:
        json.dump(result,handle,ensure_ascii=False,indent=2)
        handle.write('\n')
    print(json.dumps(result['summary'],indent=2))


if __name__ == '__main__':
    main()
