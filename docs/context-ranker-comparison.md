# Constrained contextual ranker, 18 October 2026

**Decision: useful experimental signal, insufficient for automatic corrections.**
A Gemini selector recovered cases the deterministic engine conservatively preserves,
but in one of three differently ordered batches it introduced the very meaning error
this review set out to prevent: `Han lader geværet før jakten.` became `Han lar …`.
Keep the engine deterministic and use contextual suggestions for review until a
separately adjudicated historical benchmark establishes the tradeoff.

A follow-up [real historical passage experiment](historical-ranker-comparison.md)
uses automatic candidates on 31 passages. It finds failures the constructed pilot
missed and fixes an adapter incompatibility with baseline word splitting.

## Frozen experiment

`tests/fixtures/ranker-development.json` contains 24 newly constructed sentences:
16 Bokmål and eight Nynorsk, 120 word tokens, one supplied ranking target per sentence.
The sentences, permitted alternatives and full token labels were frozen before the
first API call. They include loading/letting, waxing/growing, names, prepositions,
plural meanings and words mentioned specifically to discuss their spelling.
All labels are explicitly model-authored development labels, not human gold.

Candidates were manually supplied, including the desired answer. This tests selection
under favourable candidate availability; it does **not** test automatic candidate
recall or an end-to-end historical normalizer. Only the target may be changed by the
ranker. Non-target decisions come from the frozen Rettskriv baseline, engine revision
`9f7ac797738946df3cf4f67d35ae132e4dffd868`, shipped frequency snapshot, no local N-gram
cache. Baseline settings include `nouncaps=false` and separate constructed book IDs.

Three calls used `gemini-2.5-flash`, temperature 0, thinking budget 1,024 tokens,
maximum output 4,096, JSON schema output, and prompt seeds `ranker-v1-0`, `-1`, `-2`.
Each seed shuffles both sentence order and candidate order. Returned `modelVersion`
was `gemini-2.5-flash`; the API does not identify immutable weights in that response.
The model received no gold labels, accepted-answer fields, reviewer identity or baseline
selection. Each answer had to select a permitted form or null (preserve/abstain).

| System | Correct changes | Incorrect changes | Missed required changes |
|---|---:|---:|---:|
| Deterministic baseline | 10 | 4 | 3 |
| Baseline + explicitly protected word mentions | 10 | 0 | 3 |
| Ranker, order 0 | 13 | 0 | 0 |
| Ranker, order 1 | 13 | 0 | 0 |
| Ranker, order 2 | 13 | 1 | 0 |
| Unanimous across all three, otherwise preserve | 13 | 0 | 0 |

The unanimity row is a **post-hoc diagnostic**, not a pre-registered policy or a
validated threshold. Shared model errors can be unanimous. All rows score the full
120 tokens, including unchanged words, using the same development scorer. Do not
interpret the favourable rows as population accuracy or evidence of human-level quality.

The first two ranker orders made the same selections; the third differed only on
loading the gun. Because both orders changed and API sampling may still vary at
temperature zero, this is instability under reordered inputs, not a controlled proof
that candidate position alone caused the error. Three runs are not independent models.

## What this revealed

- Context helped with `lader henne gå` → `lar`, waxing a table → `vokset`, and a tree
  growing → `vokste`, in all three orders. Baseline abstained on these three.
- The baseline changed `aa`, `saag`, `paa` and `fraa` inside sentences explicitly
  talking about their spelling. All three ranker orders preserved those mentions.
  Quotation marks alone cannot establish protection: ordinary quoted speech often
  should be normalised. This needs source metadata or an editorial annotation.
- Supplying existing `protected` spans for the five spelling-discussion cases (one
  was already preserved) removes all four wrong baseline changes without a model.
  This is a test of supplied annotation, not an automatic quotation detector.
- The ranker can undo a correct deterministic decision. Restricting proposals and
  validating offsets prevents arbitrary rewrites; it does not prevent wrong senses.

For example, with `text = 'Ordet «paa» har tre bokstavar.'`, preserving the referenced
spelling is explicit:

```python
from rettskriv import engine
text = 'Ordet «paa» har tre bokstavar.'
at = text.index('paa')
result = engine('nno').modernise(text, protected=[(at, at + len('paa'))])
```

## Reproduction and boundaries

The committed adapter has no network or SDK dependency. It prepares prompts and
validates imported model output before producing the existing benchmark format:

```sh
python3 -m tools.benchmark predict tests/fixtures/ranker-development.json baseline.json
python3 -m tools.context_ranker prepare tests/fixtures/ranker-development.json packet.json --seed ranker-v1-0
# Submit packet.instruction and packet.cases through your chosen model API.
# Save its JSON array [{id, at, to}], with null meaning preserve, as answers.json.
python3 -m tools.context_ranker apply tests/fixtures/ranker-development.json predictions.json \
  --baseline baseline.json --answers answers.json
python3 -m tools.benchmark score tests/fixtures/ranker-development.json predictions.json --development
```

The adapter rejects duplicate/missing/unknown answers, stale offsets, unknown
alternatives and multiword candidates. Protected targets offer only their original
form. Null removes any baseline replacement at that target, so abstention genuinely
preserves source text. Other baseline edits remain unchanged. Output files are
exclusive writes. Six new tests cover these boundaries, including keeping labels
out of prompt packets and leaving baseline inputs unmodified.

Raw request/response bodies, predictions, usage and ablations are retained locally in
ignored `out/ranker/`. Only constructed sentences were sent to the model. Three calls
reserved $0.10 each; reported token usage totals approximately **$0.0145** at the
[published Gemini 2.5 Flash rates](https://ai.google.dev/gemini-api/docs/pricing)
($0.30/M input and $2.50/M output including thinking). This is a usage-based estimate,
not a billing statement. No retries or other paid comparisons were made in this step.

## Other approaches worth comparing

[Histnorm](https://github.com/coastalcph/histnorm) provides historical-normalisation
baselines, scripts and aligned datasets. Its published recommendations combine
memorised mappings with a learned model for unseen forms; it includes Norma and
character-level SMT approaches. Its listed benchmark languages do not include
Norwegian. It is useful methodology and tooling, not a missing Norwegian gold set.

[Makarov and Clematide's contextual transduction implementation](https://github.com/ZurichNLP/acl2020-historical-text-normalization)
is another relevant comparison: learned character transformations combined with
contextual decoding. It requires training data and its neural transducer dependency;
the published corpus list likewise does not include Norwegian. Neither system was
trained or evaluated in this review. A domain-trained candidate generator could be
more economical and controllable than a general model, but that is an untested hypothesis.

[NorDiaChange](https://arxiv.org/abs/2201.05123) supplies Norwegian semantic-change
annotations. Those could inform sense-change stress tests, but they are not aligned
historical-to-modern spelling targets. The central missing resource remains a
Norwegian benchmark with independently adjudicated *preserve/change* decisions,
names, quotation roles, historical senses and book/author separation. More unlabelled
text or a modern morphology library does not fill that gap.
