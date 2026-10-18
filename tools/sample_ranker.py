"""Freeze real-passage ranker targets and baseline before model evaluation.

python3 -m tools.sample_ranker CASES OUTPUT_DIRECTORY [--per-stratum 4] [--seed S]
Samples changed and preserved words separately per passage. Candidates come only
from the baseline, pending rules and dictionary morphology. The default guarded
policy adds narrow preservation rules and all matching past-tense paradigms;
--policy legacy reproduces the original proposal algorithm.
This is diagnostic sampling, not gold annotation or a production candidate policy.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random

from rettskriv import book_engine
from rettskriv.text import WORD
from tools.benchmark import validate_cases
from tools.context_ranker import targets
from tools.ranker_candidates import propose


def sample(cases, per_stratum=4, seed='real-passages-v1', policy='guarded'):
    validate_cases(cases)
    if policy not in {"legacy", "guarded"}:
        raise ValueError("unknown candidate policy")
    if type(per_stratum) is not int or per_stratum < 1:
        raise ValueError('per-stratum must be a positive integer')
    grouped = defaultdict(list)
    for case in cases:
        grouped[(case['book'],case['lang'])].append(case)
    packets, baseline = [], []
    for (_, lang), group in sorted(grouped.items()):
        eng = book_engine([c['original'] for c in group],lang)
        inferred_caps = eng.nouncaps
        for case in group:
            eng.nouncaps = case.get('nouncaps',inferred_caps)
            eng.year = case.get('year')
            result = eng.modernise(case['original'],verse=case.get('verse',False),
                                   protected=case.get('protected'))
            pools = defaultdict(list)
            for index,token in enumerate(result.tokens):
                if not token.word or token.reason in {'name','literal','protected'}:
                    continue
                choices = {token.text,token.out}
                if token.reason in {'pending','ambiguous','lexicon-nomatch','archaic-unresolved','unknown'}:
                    choices.update(eng.case(token,s) for s in token.meta.get('candidates','').split('|') if s)
                    past = eng.weak_past(token.lower)
                    if past:
                        choices.add(eng.case(token,past))
                # The adapter ranks one-word candidates. Baseline multiword changes
                # remain intact outside ranking scope, not silently truncated.
                choices = {s for s in choices if s and WORD.fullmatch(s)}
                notes = []
                if policy == "guarded":
                    choices,notes = propose(eng,token,result.tokens,index,case["original"])
                locked = bool(notes) and choices == {token.text}
                if not locked and not 2 <= len(choices) <= (6 if policy == "legacy" else 8):
                    continue
                kind = 'changed' if token.out != token.text else 'preserved'
                pools[kind].append(dict(at=token.start,**{'from':token.text},
                                        candidates=sorted(choices),origin=token.reason,
                                        **({"candidate_notes":notes} if notes else {})))
            selected = []
            for kind,pool in sorted(pools.items()):
                rng = random.Random(f"{seed}:{case['id']}:{kind}")
                selected.extend(rng.sample(pool,min(per_stratum,len(pool))))
            if selected:
                packets.append(dict(case,rank_targets=sorted(selected,key=lambda t:t['at'])))
                baseline.append(dict(id=case['id'],changes=result.changes))
    targets(packets)
    return packets,baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cases',type=Path)
    parser.add_argument('out',type=Path)
    parser.add_argument('--per-stratum',type=int,default=4)
    parser.add_argument('--seed',default='real-passages-v1')
    parser.add_argument('--policy',choices=['legacy','guarded'],default='guarded')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output directory exists; frozen packets are not overwritten')
    cases,baseline = sample(json.loads(args.cases.read_text(encoding='utf-8')),args.per_stratum,args.seed,args.policy)
    args.out.mkdir(parents=True)
    for name,data in [('cases',cases),('baseline',baseline)]:
        with (args.out/f'{name}.json').open('x',encoding='utf-8') as handle:
            json.dump(data,handle,ensure_ascii=False,indent=2)
            handle.write('\n')
    print(f'{len(cases)} passages; {sum(len(c["rank_targets"]) for c in cases)} ranking targets; no gold created')


if __name__ == '__main__':
    main()
