# Six further rounds on unseen historical passages

This follows [the first candidate-generation comparison](candidate-generation-comparison.md).
The rounds improve the experimental proposal safeguards, but do **not** establish
production-grade contextual normalisation. The remaining failures increasingly
involve uncertain OCR and historical senses; further blanket abstention rules also
remove legitimate normalisations. The model remains outside the production engine.

## Sampling and method

Six sequential rounds contain **132 new passages, 30,974 engine word tokens and
1,415 ranking targets**. The final round separately checks eight fresh Landsmål pages.
They are fresh relative to all earlier packets and one another: the sampler rejects
case-insensitive exact 12-word shingle overlap, also checking the existing 27-book
corpus. This is not proof of author independence or freedom from training overlap.

Rounds 1–2: four passages each from Lie's *Den Fremsynte* (1870), Elster's
*Tora Trondal* (1879), Kielland's *Garman og Worse* (1880), Skram's *Sjur Gabriel*
(1887), and Garborg's *Bondestudentar* (1908). Rounds 3–5 add four passages each
from Bjørnson's *Magnhild* (1877) and Hamsun's *Pan* (1894). Round 6 contains eight Garborg pages. The two added books
are Norwegian originals according to the MeMo metadata, not Danish translations.

Sources: [MeMo v1.1](https://huggingface.co/datasets/MiMe-MeMo/Corpus-v1.1) and
[Runeberg's Garborg edition](https://runeberg.org/gaskriftir/1-1908/).
MeMo blocks contain 40–600 whitespace-delimited strings. Within each book, shuffle
with `overnight-<round>:<book>`, then stably rank by counts of historical `-ede`
forms and the predeclared dialect markers `æ inkje ikkje hu e ska va mæ dæ`.
Take the first four nonoverlapping blocks. Garborg pages start at `20 + round*3`,
advance by seven, and reject overlap until four are accepted (eight in the final round). This deliberately
concentrates difficult cases; it is not a prevalence sample. In round 6, page 38
was unavailable due to a TLS timeout and was skipped; the accepted pages are
52, 59, 66, 73, 87, 94, 101 and 108. No paid request was retried.

Before each model run, freeze original OCR, source URL/hash/block or page,
book/language context, deterministic baseline, candidate policy source and targets.
Sample up to eight changed and eight preserved targets per passage with
`overnight-<round>`. Gold remains empty. Fixes prompted by one round are tested on
new passages in later rounds; earlier packets are development evidence thereafter.
Round 2's initial local preflight was corrected before any paid call; both local
versions are retained. Later candidate-policy snapshots distinguish all paid inputs.

Each book uses one Gemini 2.5 Pro call: temperature 0, requested thinking budget
4,096, output cap 10,000, exact per-target schema enums and local validation. The
case/candidate ordering seed is `overnight-<round>`. No output is silently repaired,
no paid retries, and no provider SDK or runtime model dependency is introduced.
There is only one model run per packet, so sampling/order variability is not measured.

## Findings and fixes

| Round | Passages | Word tokens | Targets | Clear unsafe selections identified in inspection |
|---|---:|---:|---:|---|
| 1 | 20 | 4,624 | 231 | `krusede → kruset`, `kantede → kantet`, `Reisæ → reise`, `Tjærebrede → Tjærebredde` |
| 2 | 20 | 4,799 | 215 | `Passerede → passerte`, `bugtede → buktet`, `grumsede → grumset` |
| 3 | 28 | 6,310 | 293 | `krænkede → krenket` in an attributive phrase |
| 4 | 28 | 6,238 | 310 | suspected OCR `flet → flett` after `er` |
| 5 | 28 | 6,367 | 297 | suspected OCR `Hefterne → heftene`; participial `stadi → stada` after `hadde dei` |
| 6 | 8 | 2,636 | 69 | Unapproved lexical-sense choice `lærdt → lært`; no new structural fix |

These are **model-authored diagnostic findings, not human gold or error rates**.
They are a lower bound on errors noticed during inspection, not an exhaustive
adjudication of every output or a controlled accuracy curve across different samples.
Both harmful edits and missed legitimate modernisations remain possible.

The final proposal policy now:

- Preserves uncertain Bokmål words ending in `æ`, including unfootnoted dialect
  forms. New later passages exercise `Veeræ`, `Forbanedæ`, `Forældræ` and `sleiæ`.
  This also withholds OCR forms such as `Kampglædæ` and historical `Værkensforklæ`;
  final `æ` is a caution signal, not a language classification.
- Withholds finite `-ede` alternatives where nearby noun/coordination or determiner
  evidence leaves an attributive or nominal reading unresolved. This covers
  `den fint krusede Flade`, `kantede og forede Tøjstykke`, `det Passerede`,
  `den bugtede Strand`, and `Den krænkede, forskudte Kvinde`.
  Dictionary noun/verb homographs and capitalised unknown nouns in noun-capitalising
  books must not disable the guard. Closed-class readings prevent treating `med`
  or `så` as definite noun evidence.
- Preserves uncertain utterance-initial `-ede` forms unless an inverted subject
  supplies a finite reading. A shouted `Tjærebrede, tjære` is not evidence for past tense.
- Refuses to combine past forms across different verb lemma IDs. For example,
  `tørre` otherwise combines drying and daring (`tørret` versus `turte/torde`).
  This conservatively withholds some correct `svingede`, `stillede` and non-habitual
  `plejede` readings too. The explicit habitual `plejede at` rule still supplies
  `pleide`, which was selected in a fresh *Magnhild* passage in round 5.
- Removes imperative-only candidates immediately after an auxiliary, with an
  actual whitespace boundary. Thus `er flet` cannot become `er flett`; an independent
  command `Flet …` can still offer `Flett`. The suspected OCR is preserved, not repaired.

The final Landsmål fix preserves uncertain `-i` forms after a have-auxiliary,
including one intervening personal pronoun, when proposed replacements are noun-only.
In `hadde dei stadi`, `stada` is a modern noun, not the required participle;
`hadde han loti` has the same danger with `lota`. This guard does not invent
`stått` or another translation. Noun `-i` alternatives outside this context remain
available. Round 6 is a fresh check after this fix.

The noun lookahead is bounded to four words and cannot cross ordinary sentence
punctuation. These safeguards intentionally leave unresolved readings unchanged;
they are not a historical parser. In particular, formal `De`, inverted subjects
and coordinated finite verbs can lose valid alternatives. Tests exercise both
preservation and permitted finite/imperative contexts.

## A small production fix, checked against whole passages

MeMo's `Hr . Mack` bypassed the existing abbreviated-title name protection because
it spaces the period. Compact `Hr.Mack` also bypassed it. The deterministic engine
now accepts both spacing patterns and prevents the name from reaching the ranker.

Whole-passage replay caught two overbroad versions before finalisation:
`Doktor . Præsten` is a full-title sentence boundary, and `Hr . Løjtnant` contains
another title rather than a surname. Protection is now limited to actual recognised
abbreviations (`hr`, `frk`, `dr`, `prof`, `st`), and another recognised title can
still normalise. Historical `Løjtnant` and `Kaptejn` join the title vocabulary.

A direct replay using the complete engine implementation from commit `8a7c871`
and the final engine on all **132 complete passages produces identical output
text**. The observed `Mack` occurrences were previously withheld as pending, so the
improvement there is explicit name protection and exclusion from model proposals,
not a newly correct visible spelling. Regressions also cover names such as `Baat`
that would otherwise be respelled. No production lexicon is expanded in this round.
The final title refinements were validated offline after the paid packets froze.

## Where the return declined

Round 5 still selected `heftene` in a passage where a coach stops so the `Hefterne`
can rest (*Magnhild*, block 127). The context strongly suggests OCR for horses;
the intended printed form was not confirmed against a scan. A valid modern noun
and a schema-valid response do not make this normalisation defensible. The related
OCR case `stød` was instead preserved against baseline `støt`, showing that the
model sometimes catches such corruption but not reliably.

Round 6 added three proposals and vetoed none. It preserved `haldi` in a fresh
`hadde han haldi paa` passage. No new auxiliary-`i` lock fired among its 69 sampled
targets, so this round does not establish generalisation of that particular guard.
The two source-grounded regression cases exercise it directly.

The selection `tala lærdt → tala lært` remains unapproved on sense grounds. The
frozen Nynorsk bank assigns `lærd` its own adjective lemma and `lært` to the
participle of `lære`; [ODS documents historical adverbial lærdt](https://ordnet.dk/ods/ordbog/l%C3%A6rd).
It is not treated as a successful meaning-preserving edit merely because `lært`
is a valid form. This needs lexical adjudication rather than another broad suffix rule.

Adding a blacklist for this one OCR word would conceal the larger limitation.
The next useful step is scan-backed OCR verification and explicit protected spans,
plus independent historical-language adjudication. Modern morphology alone cannot
reconstruct the printed source or decide how much dialect should be normalised.
Existing protected spans can block reviewed suspect tokens without rewriting raw OCR.

After the targeted sixth round, this unattended campaign stops:
new failures have narrowed toward OCR/context adjudication, while increasingly broad
rules demonstrably sacrifice legitimate coverage. This is a practical stopping
judgment, not a statistical claim that the system has converged or become safe.

## Evidence and validation

Private `out/overnight/` retains the six frozen packets, policy snapshots, raw API
requests/responses, usage, explicit model-labelled inspection ledgers, final replays,
source text and source hashes. Earlier bad responses remain unchanged. The final
policy rejects the nine identified unsafe selections from rounds 1–4 and the
round-5 participle failure; rejected responses
are not converted into successful post-fix model results. Round 5's suspect OCR
selection remains documented and unresolved, not whitelisted.

The previous reproduction commands remain valid; use `--policy guarded` for the
current proposals and `--policy legacy` only to reproduce the original algorithm.
All runs use the provider-independent keyed adapter. No human benchmark score,
precision estimate or production model adoption follows from these experiments.

All **32/32** paid responses passed schema and local validation. Per-round additions
relative to the frozen baseline were 61, 36, 42, 55, 44 and 3; baseline vetoes were
4, 0, 6, 2, 6 and 0. These unpaired counts measure behavior on different selected
passages, not comparative precision or coverage. Final offline replay rejects all
ten identified structural/inflection failures from rounds 1–5; the OCR and final
lexical-sense cases above remain unresolved.

**68 tests pass**, with full-engine replay, Python compilation and whitespace checks.
The complete previous engine was loaded from `8a7c871` for the 132-passage comparison,
not approximated by toggling only its changed method. The campaign cost an estimated
**$1.7047**, bringing cumulative thread model spend to **$2.6259** of the $30 cap.
Costs include reported thinking/output tokens and are estimates, not billing statements.
All paid requests are reconciled; no retries or outstanding reservations remain.
