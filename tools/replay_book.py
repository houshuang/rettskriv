"""Replay a complete production book with a chosen checkout's engine.

Archive an older revision and give it the same read-only data/ordbank directory
before using --engine-root. Each invocation runs one isolated engine version.
Full text and token output belong in ignored out/, not in Git.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('book')
    parser.add_argument('--engine-root', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--compare', type=Path, help='Earlier replay JSON of the identical book input')
    parser.add_argument('--dependency-models', type=Path,
                        help='Opt in to experimental dependency recovery using installed Stanza models (no downloads)')
    args = parser.parse_args()
    sys.path.insert(0, str(args.engine_root.resolve()))
    from rettskriv import corpus
    from rettskriv.engine import Engine
    data = corpus.load(args.book)
    engines = {lang: Engine(lang) for lang in ('nob', 'nno')}
    resolver = None
    if args.dependency_models:
        from rettskriv.dependency import DependencyResolver
        resolver = DependencyResolver(args.dependency_models)
    for engine in engines.values():
        engine.learn_book(corpus.texts(data))
        engine.year = data.get('printed_year')
    rows, skipped = [], []
    for item in data['items']:
        if item.get('kind') != 'piece':
            continue
        lang = corpus.detect(' '.join(t for _, t, _ in corpus.units(item)),
                             corpus.LANGUAGE.get(data['book'].get('language'), 'nob'))
        if lang not in engines:
            skipped.append(item['id'])
            continue
        for path, text, verse in corpus.units(item):
            options = {'resolver': resolver} if resolver is not None else {}
            result = engines[lang].modernise(text, verse=verse, **options)
            rows.append(dict(item=item['id'], path=list(path), lang=lang, source=text,
                             output=result.text, tokens=[dict(at=t.start, source=t.text, out=t.out,
                                                             reason=t.reason)
                                                        for t in result.tokens if t.word]))
    output = dict(book=args.book, engine_root=str(args.engine_root.resolve()), rows=rows, skipped=skipped)
    if resolver is not None:
        output['dependency_errors'] = resolver.errors
    if args.compare:
        previous = json.loads(args.compare.read_text())
        if previous['skipped'] != skipped:
            raise ValueError('Language-skipped pieces differ; comparison is not like-for-like')
        changes = []
        for old, new in zip(previous['rows'], rows, strict=True):
            if any(old[k] != new[k] for k in ('item', 'path', 'lang', 'source')):
                raise ValueError('Book inputs or language routing differ')
            for a, b in zip(old['tokens'], new['tokens'], strict=True):
                if (a['at'], a['source']) != (b['at'], b['source']):
                    raise ValueError('Token alignment differs')
                if a['out'] != b['out']:
                    changes.append(dict(item=new['item'], path=new['path'], at=a['at'],
                                        source=a['source'], old=a['out'], new=b['out']))
        output['differences'] = changes
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(book=args.book, fields=len(rows), skipped=skipped,
                          words=sum(len(r['tokens']) for r in rows),
                          edits=sum(t['source'] != t['out'] for r in rows for t in r['tokens']),
                          differences=len(output.get('differences', [])))))


if __name__ == '__main__':
    main()
