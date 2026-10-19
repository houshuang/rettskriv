# Whole-book regression review, 19 October 2026

## Latest remaining-case follow-up against3176829

One additional opt-in original recovery (`ægtede→ektet`) brings the audit to
**43/62 restored,19withheld**: two valid preserved forms and17 genuine misses.
All previous73 approved edits and all12 malformed-output protections survive.
Default behavior is unchanged. The new bounded source inversion frame disambiguates
a noun/past homograph while retaining complete parser-path and subject agreement.

Two additional whole books (Dunker1871, Thoresen1872) and a complete Thoresen1867
story add192,222 routed words. Their16 parser improvements are independently approved;
these validate existing safeguards and are not new-rule gains. Cumulative coverage:
**36 complete books plus one complete story,2,500,544 routed words**,90 reviewed
opt-in improvements. No new incorrect retained output observed, but unchanged text
is not exhaustive gold. The new rule's observed gain is only the original case.

See [the parser report](dependency-parser-evaluation.md) for every remaining case,
source provenance, actual-model adversaries and validation. PR remains draft.


## Latest lexical/parser campaign against d577afe

Default output is unchanged across 34 complete books: **2,308,322 routed words,
51,957 fields/paragraphs**, plus 132 external passages. The seven additional books
contribute 399,140 words/12,064 paragraphs. Historical lexical alternatives now
remain separate candidates, including alternatives without usable morphology.

Experimental opt-in Danish/Bokmål parsing retains **73 independently approved
improvements**: 58 across the original schoolbooks and 15 in the added Collett and
Kielland texts. Four recover original withheld decisions: cumulative **42/62 restored,
20 withheld with parsing**, versus **38/62 restored, 24 withheld by default**. Two
withheld forms are already valid, leaving 18 genuine misses with parsing. All 12
original malformed-output protections survive. No newly incorrect retained edit
was observed; unchanged text was not exhaustively judged.

The initial parser gate failed two caption counterexamples. The final gate requires
matching source-aligned finite structures, subject/object evidence or an independent
finite anchor, and a reviewed unambiguous lexical identity. Models remain opt-in,
with no automatic downloads. See [the parser report](dependency-parser-evaluation.md)
for design, source provenance, review coverage and limitations. This is development
evidence from model reviewers, not human gold or a universal no-regression claim.

## Prior bounded-clause campaign

The production patch improves the preceding version, but does **not** yet satisfy
“better without regressions” against the original engine. Keep the PR in draft.

## Final bounded-clause campaign against d718b50

Six candidate replays across **27 books, 1,909,182 routed word tokens and 39,893
fields** restore **11 additional original decisions**. The cumulative original
baseline audit is now **38/62 restored, 24 withheld**; all 27 previous recoveries
and all 12 malformed-output protections survive. Two of the 24 withheld choices
(`lønnede`, `samlede`) already have valid modern readings in their contexts, so
withheld decisions are not equivalent to malformed outputs. The other 22 still
need better syntactic or lexical evidence.

The added frames recognize complete possessive/genitive subjects, negated
inversion, verified name appositions with reflexives, bounded relative clauses,
and reporting coordination with an explicit clausal complement. They never skip
arbitrary intervening words. Typed, reviewed name entries supply subject evidence;
free-text audit labels do not. There are 921 old name-labelled audit entries, including
unreliable labels on ordinary nouns. The five new names do not alter global
name-span propagation: doing that incorrectly protected `Thinget` and `Kongesøn`,
and both real passages now have permanent regression fixtures.

Adversarial review also rejected quantifier `faa` (`at faa Breve besvarede`),
reflexive bridges alone (`roste sig og udmærkede Mænd`), and present-verb noun
homographs (`en elsker fremmede`). These counterexamples accompany the positive
real-book tests. The current frames are deliberately incomplete, not a general
Norwegian parser.

All 11 new recoveries occur in Faye; the other 26 books initially remained
identical. This demonstrates stability outside Faye, **not positive evidence of
recovery generalization**. A subsequent independent dependency-parser experiment
found an existing lexical error in Erichsen: `du vandede blomsten` became
`du vandet blomsten`. Modern `vande` means reject/dislike, whereas the historical
passage means water. An explicit ambiguity entry now preserves `vandede` rather
than choosing a wrong lemma. The same ambiguity prevents a new wrong replacement
in Hersleb. This adds one avoided malformed output to the 11 recoveries; the
original Faye/Schjøtt counts are unchanged.

All changed outputs were reviewed in their complete source fields. The 132
external passages remain unchanged. Language routes, source fields, token
alignment and the 29 excluded pieces match the baseline. These are model-reviewed
output differences, not human gold, a universal accuracy score, or an exhaustive
review of unchanged output. No merge or deployment is implied.

The optional parser study is described in [Dependency-parser evaluation](dependency-parser-evaluation.md).
It is **not enabled in production**: two modern-language parsers agreed on one
wrong lexical replacement in the independent challenge. More syntactic confidence
cannot fix a wrong candidate lemma. The remaining 24 decisions are retained rather
than forcing the original exact-match count with an unsafe fallback.

88 tests pass, including 187 real-book fixture targets and the new lexical
counterexample. Compilation and whitespace checks pass. Private frozen source,
exact d718b50 archive, candidate snapshots and original-74 audit live in
`out/final-35/`; parser inputs, model outputs and independent judgments are in
`out/parser-trial/`. No paid calls were made. Historical sections below retain
their original checkpoint counts.

## Clause analysis against 8247129

The next four-round campaign recovers **5 more of the remaining 40 decisions**:
**27 of 62 recovered, 35 withheld** against the original engine. Every one of the
previous 22 recoveries and all 12 malformed-output protections remains unchanged.

The engine now recognizes bounded complete constituents rather than guessing from
one neighboring word. Its deliberately limited clause frames require:

- A complete indefinite object and terminal boundary in `hvor de oprettede en
  Fristat.`; `en/et` alone is insufficient, and a second predicate rejects the parse.
- A complete noun subject and clause-final predicate in `at Guden selv fortærede.`
- An inverted personal subject and unequivocal clause adverb in `bevarede de dog`.
- An immediately adjacent finite coordination anchor in `sloge eller adsplittede`.
  No noun, pronoun or participle bridges are allowed; modal/auxiliary anchors are
  excluded. A modern noun homograph is discounted only for a genuinely respelled
  source that is not itself a dictionary noun, in noun-capitalizing prose.
- A finite blive auxiliary, complete subject and clause-final participle in
  `bleve Ovnstuer indrettede`. Dictionary noun compounds can supply the subject;
  an unknown capital alone cannot. Both source and modern agreeing forms are
  checked for competing lexical adjective analyses.

A comma followed by a predicate, verified non-genitive name and reflexive sig is
also recognized. It does not recover unknown historical names by capitalization.
The frames abstain outside their bounded recognized constituents; this is not a
complete dependency parser. Remote coordination and passive ellipsis remain open.

| Book added in this campaign | Routed word tokens | Fields | Approved changes |
| --- | ---: | ---: | ---: |
| Beyer 1824 | 38,075 | 2,013 | 0 |
| Jensen, third reader, 1863 | 157,542 | 2,677 | 3 |
| Wergeland, second reader, 1844 | 87,992 | 2,464 | 0 |

Across all ten books the replay covers **673,989 tokens in 14,618 fields**. There
are **11 independently approved changed outputs** against 8247129: Faye 5, Hjort 2,
Knutzen 1 and Jensen 3. Jensen has 14 pieces and Wergeland four excluded by the
existing language routing in both versions. Source fields, language routes,
skipped-piece lists and token alignment match exactly. These are production-routed
book checks, not processing of every piece, scan or OCR layer. Additional books
are not claimed globally unseen project data.

All 11 changes were independently reviewed in their complete source fields. A
132-passage external replay is unchanged. No changed-token regression was observed;
unchanged output is not fully annotated and review remains model-based, not human
gold. Zero changes in a book demonstrates stability, not universal correctness.

Adversarial testing caught an inverted passive/adjective ambiguity: historical
`udmærkede` lacks the modern lexical adjective analysis, so inspecting its source
alone could incorrectly select `utmerket`. The final check examines same-lemma
modern agreeing forms too. It deliberately withdraws an otherwise correct Beyer
recovery. Object coordination (`saae dem og udmærkede Mænd`), nominalized
participles, remote passive coordination and have-object predicates stay protected.

83 tests pass with **173 real-book targets**, including the 11 new complete-field
fixtures and all previous protections. Compilation and whitespace checks pass.
Frozen inputs, 8247129 archive, four candidate snapshots, replay scripts and the
complete original-74 audit remain private in `out/clause-40/`. No paid calls.
The PR remains a draft: 35 original modernization decisions are still withheld.

## Earlier recovery against 532a114


Four successive candidate replays evaluated all seven books below. The final
candidate recovers **9 more of the remaining 49 decisions**: **22 of 62 recovered,
40 still withheld** relative to the original engine. All 12 malformed original
outputs remain avoided (five corrected, seven preserved). These are token
occurrences, not distinct words. Some withheld source forms are already valid
modern adjectives; “withheld” measures the previously approved modernization
choice, not necessarily malformed text.

| Book | Word tokens | Fields | Improvements vs 532a114 |
| --- | ---: | ---: | ---: |
| Faye 1852 | 15,222 | 255 | 9 |
| Schjøtt 1890 | 73,137 | 923 | 0 |
| Hersleb 1833 | 28,835 | 408 | 6 |
| Ræder 1899 | 93,447 | 1,346 | 1 |
| Hjort 1843 | 77,015 | 2,133 | 11 |
| Knutzen 1836 | 32,920 | 632 | 1 |
| Garborg 1885 | 69,804 | 1,767 | 0 |
| Total | 390,380 | 7,464 | 28 |

Hjort, Knutzen and Garborg add 179,739 tokens to this repair's whole-book check.
They are additional validation books, not globally unseen project data. Garborg
adds Landsmål coverage; zero differences establish stability, not correctness of
all existing outputs. All input fields, language routes and skipped-piece lists
matched. No pieces were skipped.

An independent agent reviewed all 28 changed outputs as correct in context. The
132 external passages yielded one further approved change, Skram's finite
`der lammede alle hans Lemmer → ... lammet ...`. No new error was observed among
these 29 changes. Unchanged text was not exhaustively reviewed, and these are
model judgments, not human gold or proof of zero regressions on arbitrary text.

The nine recoveries are five quoted `svarede → svarte`, relative `beilede → beilet`
and `udartede → utartet`, passive `blevne ansporede → ... ansporet`, and attributive
`Den slet forsynede ... Hær maatte vige → ... forsynte ...`.

The implementation requires speech punctuation and a reporting lemma for quotation
clauses. Relative `der` requires a comma, no detected attributive noun head, and no
preceding locative her/hist/hisset contrast. A following modal supplies additional
noun-phrase evidence for demonstrative adjectives. Historical blevne/bleven govern
participle selection with the existing adjective vetoes. An explicit infinitive
mapping `udarte → utarte` supplies dictionary-backed candidates; it does not bypass
tense/agreement disambiguation for inflected forms.

Adversarial review rejected the apparently useful `hvor/at de -ede en/et` rule:
`de besvarede en efter en blev lagt bort` can mean the answered letters, one by one.
It also narrowed relative `der`: `her simple Folk, der udmærkede [Mænd]` is locative
contrast, and must not become `utmerket`. Three correct book changes were willingly
withheld again to enforce the stronger noun-head guard. No broad default-past,
name-subject or remote-coordination fallback was restored.

The remaining 40 cases comprise 34 finite readings and six passive/object-predicate
readings. They need stronger clause/argument analysis; local heuristics still
confuse these with adjectives, nominalized participles and remote auxiliaries.
This is a measured coverage improvement, not completion of the no-regressions bar.

81 tests pass, with the previous 122 real-book targets plus 40 new full-context
targets: all 28 changed outputs and all 12 malformed-output protections. New
adversarial contrasts cover each rejected expansion. Frozen inputs, exact 532a114
archive, four candidate snapshots, complete original-74 audit and replay scripts
are private in `out/recovery-49/`. No paid calls, publication changes or deployment.

## Previous repair against e01bec2 (historical checkpoint)

The following records the preceding 532a114 checkpoint, before the recovery above.

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
