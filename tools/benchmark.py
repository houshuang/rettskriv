"""Prepare and score a fully annotated token benchmark, including unchanged words.

JSON input is a list of cases. Each case has id, book, author, split, lang,
original, and decisions [{at, from, accepted: [forms]}]. Every word must have
one decision. Human evaluation additionally requires reviewed_by and
reviewer_kind=human. Development fixtures are never reported as human evidence.

python3 -m tools.benchmark prepare cases.json packet.json
python3 -m tools.benchmark predict packet.json predictions.json
python3 -m tools.benchmark score gold.json predictions.json [--development]

Other systems produce the same predictions format: [{id, changes:[{at,from,to}]}].
This keeps candidate-system comparison independent of a particular library.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from rettskriv import book_engine
from rettskriv.text import tokenise


def validate_cases(cases: list[dict], gold: bool = False, human: bool = True) -> None:
    if not cases:
        raise ValueError("benchmark must contain cases")
    ids, books, authors = set(), {}, {}
    for case in cases:
        for key in ('id', 'book', 'author', 'split', 'lang', 'original'):
            if not isinstance(case.get(key), str) or not case[key].strip():
                raise ValueError(f"missing case field: {key}")
        if case['id'] in ids:
            raise ValueError(f"duplicate case ID: {case['id']}")
        ids.add(case['id'])
        if case['split'] not in {'train', 'dev', 'test'} or case['lang'] not in {'nob', 'nno'}:
            raise ValueError('invalid split or language')
        for registry, key in ((books, 'book'), (authors, 'author')):
            identity = case[key].strip().casefold()
            if registry.setdefault(identity, case['split']) != case['split']:
                raise ValueError(f"{key} crosses dataset splits: {identity}")
        if gold:
            if human and (case.get('reviewer_kind') != 'human' or not case.get('reviewed_by')):
                raise ValueError(f"{case['id']}: human adjudication required")
            words = {t.start: t.text for t in tokenise(case['original']) if t.word}
            decisions = case.get('decisions', [])
            if len(decisions) != len(words) or {d['at'] for d in decisions} != words.keys():
                raise ValueError(f"{case['id']}: every word must be annotated exactly once")
            for d in decisions:
                if d['from'] != words[d['at']] or not isinstance(d.get('accepted'), list) or not d['accepted']:
                    raise ValueError(f"{case['id']}: missing or stale gold decision")
                if any(not isinstance(v, str) or not v for v in d['accepted']):
                    raise ValueError('accepted forms must be nonempty strings')


def prepare(cases: list[dict]) -> list[dict]:
    validate_cases(cases)
    return [dict(c, reviewed_by=None, reviewer_kind=None,
                 decisions=[{'at': t.start, 'from': t.text, 'accepted': []}
                            for t in tokenise(c['original']) if t.word]) for c in cases]


def predict(cases: list[dict]) -> list[dict]:
    validate_cases(cases)
    grouped = defaultdict(list)
    for c in cases:
        grouped[(c['book'], c['lang'])].append(c)
    results = []
    for (_, lang), group in grouped.items():
        context = [c['original'] for c in group]
        eng = book_engine(context, lang)
        inferred_caps = eng.nouncaps
        for case in group:
            eng.nouncaps = case.get('nouncaps', inferred_caps)
            eng.year = case.get('year')
            result = eng.modernise(case['original'], verse=case.get('verse', False),
                                   protected=case.get('protected'))
            results.append({'id': case['id'], 'changes': result.changes})
    return results


def score(cases: list[dict], predictions: list[dict], human: bool = True) -> dict:
    validate_cases(cases, gold=True, human=human)
    by_id = {p['id']: p for p in predictions}
    if len(by_id) != len(predictions) or by_id.keys() != {c['id'] for c in cases}:
        raise ValueError('predictions must cover every case exactly once')
    counts = Counter()
    strata = defaultdict(Counter)
    for case in cases:
        gold = {d['at']: d for d in case['decisions']}
        changes = {}
        for c in by_id[case['id']]['changes']:
            at = c['at']
            if at in changes or at not in gold or c['from'] != gold[at]['from']:
                raise ValueError(f"{case['id']}: invalid predicted edit")
            if not isinstance(c['to'], str) or not c['to'] or c['to'] == c['from']:
                raise ValueError('replacement must be a nonempty changed string')
            changes[at] = c['to']
        local = Counter()
        for at, d in gold.items():
            out = changes.get(at, d['from'])
            changed = out != d['from']
            correct = out in d['accepted']
            local['words'] += 1
            local['changed'] += changed
            local['correct_changes'] += changed and correct
            local['incorrect_changes'] += changed and not correct
            local['missed_normalisations'] += not changed and not correct
            local['correct_preservations'] += not changed and correct
        counts.update(local)
        strata[f"{case['split']}:{case['lang']}"].update(local)
    def metrics(c):
        return dict(c, change_precision=c['correct_changes']/c['changed'] if c['changed'] else None,
                    unchanged_fraction=1-c['changed']/c['words'] if c['words'] else None)
    return {'evidence': 'human-adjudicated' if human else 'development-only',
            'total': metrics(counts), 'strata': {k: metrics(v) for k, v in sorted(strata.items())}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'predict', 'score'])
    parser.add_argument('cases', type=Path)
    parser.add_argument('other', type=Path, help='output file, or predictions for score')
    parser.add_argument('--development', action='store_true', help='score non-human fixtures, labelled as such')
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text())
    if args.action == 'score':
        print(json.dumps(score(cases, json.loads(args.other.read_text()), not args.development), indent=2))
    else:
        result = prepare(cases) if args.action == 'prepare' else predict(cases)
        with args.other.open('x') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write('\n')


if __name__ == '__main__':
    main()
