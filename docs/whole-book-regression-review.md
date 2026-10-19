# Whole-book regression review, 19 October 2026

The production patch improves the preceding version, but does **not** yet satisfy
“better without regressions” against the original engine. Keep the PR in draft.

## Compared versions and scope

- Original: `ce74a11`.
- Before this repair: `e01bec2`.
- Candidate: this commit's engine, bank, and unchanged dictionaries/frequency data.

Complete production-readable piece content was replayed from Skard's library
editions, including titles, prose, verse, captions and notes. All book context was
learned before normalization; printing year and language routing were retained.
No piece was skipped by language detection. Facsimile-only pages and non-piece
metadata are outside the production builder's scope. This is not a scan/OCR audit.

| Book | Word tokens | Fields | Reviewed improvements vs e01bec2 |
| --- | ---: | ---: | ---: |
| Faye 1852 | 15,222 | 255 | 20 |
| Schjøtt 1890 | 73,137 | 923 | 1 |
| Hersleb 1833 | 28,835 | 408 | 41 |
| Ræder 1899 | 93,447 | 1,346 | 60 |
| Total | 210,641 | 2,932 | 122 |

The earlier 132 external historical passages (30,974 tokens, including dialect and
Landsmål) produced another seven changed tokens, all reviewed as improvements.
An independent agent reviewed every changed output in the broader candidate; the
final narrowed candidate's 122 + 7 changes were verified to be a subset of those
approved outputs. No newly incorrect change was observed against e01bec2. These
are contextual model judgments, not independently human-annotated accuracy scores.
Unchanged output was not exhaustively adjudicated.

Hersleb and Ræder were first used after the initial patch design. Once their
failures informed repairs they became development evidence, not held-out tests.
None of these existing project books is claimed globally unseen.

## Production changes

Passive infinitives retain their voice during inflection, but infinitive-marker
conditions can now see their complete analysis. This restores `at bevares → å
bevares` and `aa forlikast → å forlikast` without turning `de bruges` into an active
verb. This interpretation is confined to at/aa conditions; applying it to other
lexicon conditions incorrectly changed the preposition in `I dettes sted`.

Old -ede forms use same-lemma/paradigm evidence for three different modern roles:
finite past, uninflected perfect participle, and agreeing adjective. An explicit
passive context can produce `bleve leverede → ble levert`, not `ble leverte`.
Verified adjective contexts can produce `sin adopterede Søn → sin adopterte sønn`.
Source lexicon decisions and multiple-lemma abstentions retain precedence.

A shared past/adjective form is used only after excluding plausible governors of
a perfect participle or object predicate across the whole preceding sentence,
including commas. Dictionary-known personal subjects require additional checks;
unknown capitals and following names do not establish a finite verb.

## Rejected approaches and permanent counterexamples

Broader drafts introduced real errors. The final tests cover these, not just the
successful examples:

- `Kristina havde udmerkede evner` must not become `utmerket evner`.
- `de blev fremmede for sine folk` must not become `fremmet`.
- `Han gav Olaf udmærkede Gaver` contains an indirect object, not a named subject.
- `Tak, udmærkede Peter!` is a vocative, not an inverted finite clause.
- `De udmærkede Soldater` and `De unge forøgede Antallet` have unresolved
  subject/determiner readings.
- `Børnene bleve vaskede, klædte og forsynede med Mad` cannot use `forsynte` merely
  because the governing auxiliary precedes a comma or a long modifier.
- `Han fik Brevene besvarede` and `Han ønskede Brevene besvarede` require an object
  predicate, not automatic `besvarte`.

Where the syntax remains uncertain the candidate preserves the source. The tests
also retain the prior multiple-lemma, dialect, command, name, and protected-span
safeguards. The offline ranker remains experimental and is not called in production.

## Remaining original-baseline regressions

The independent review refined the original 74 Faye/Schjøtt differences into
62 valid changes withheld and 12 malformed outputs avoided. This patch restores
13 of those 62 valid changes; **49 are still withheld**. All 12 malformed outputs
remain avoided: five now receive correct modern forms and seven remain preserved.

Examples still withheld include finite `ægtede → ektet`, `oprettede → opprettet`,
and several occurrences of `svarede → svarte`. A partial restoration is not evidence
that the original coverage regression has disappeared. No “zero regressions” claim
against ce74a11, global accuracy percentage, merge, or deployment is warranted.
Further recovery needs reviewed syntactic evidence rather than another default
that interprets absence of an adjective analysis as proof of a finite verb.

## Validation and reproduction

78 tests pass, including 122 exact real-book sentence targets with book/piece/field
provenance and learned book-name context. Compilation and whitespace checks pass.
Full replay data, source hashes and baseline snapshots are private under ignored
`out/skard-replay/`; external packets remain in `out/overnight/`.

`tools/replay_book.py` runs the production corpus routing against a selected engine
checkout or archived revision, in its own process. Give an archived version the
same read-only `data/ordbank` source; retain its own tracked lexicon, frequency data,
chain policy and generated cache. For example:

```sh
python3 tools/replay_book.py faye-1852 --engine-root out/skard-replay/e01bec2 --out out/faye-before.json
python3 tools/replay_book.py faye-1852 --compare out/faye-before.json --out out/faye-after.json
```

The comparison refuses differing source fields, language routing, skipped pieces
or token alignment. Inspect every difference: edit counts alone are not a quality
metric. Replay outputs contain full book text and should stay outside Git. Skard's
raw data and published library assets were not modified. No paid model calls were
made for this repair.
