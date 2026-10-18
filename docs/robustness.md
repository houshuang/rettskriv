# Robustness and independent evaluation

The deterministic engine remains the baseline. Meaning preservation is the objective,
not a guarantee. The historical acceptance figures in the README belong to ce74a11;
the following changes need new linguistic acceptance, not an inherited accuracy claim.

## Implemented safeguards

- Unknown/malformed lexicon conditions and contradictory flags fail during loading,
  including rows later shadowed by another file. Empty targets also fail.
- Grammar may use a rule-derived candidate only if the chain is trusted.
- Optional chain trust uses a one-sided 95% exact binomial lower confidence bound,
  not observed precision. Replaying the existing audit data qualifies no optional
  chain at 99.5%. Obligatory letter rules remain a deliberate policy exception.
  These bounds assume independent trials and correct labels; correlated word forms
  and model judgments mean they are not a guarantee of future linguistic accuracy.
- Ordbank analyses retain lemma IDs, paradigm IDs and full grammatical tags. Verb
  inflection follows the same lemma/paradigm rather than constructing suffixes.
  Multiple present forms cause abstention; past-form variants are ranked by the
  existing frequency snapshot. This does not resolve lexical senses automatically.
- Ambiguous lader and voksede abstain. An abbreviated title protects the next
  capitalised token. These are safety regressions, not a comprehensive name model.
- engine() returns independent book state. Use book_engine(texts, lang=...) once
  and call its modernise() for each paragraph. Linguistic resources are shared and
  must be treated as read-only; do not mutate one book engine concurrently.
- modernise/modernise_result/Engine.modernise accept protected=[(start,end), ...],
  half-open Python character offsets into the original. Overlapping word tokens
  remain unchanged. Editors should protect names, foreign quotations and spelling
  examples explicitly when their structure is known.

## Acceptance reviews

New reviews must include one row per numbered change, including `kind=ok`, with
matching original and replacement. Missing, duplicated, unknown or stale judgments
cause failure. Every generated part needs its review file. Old error-only TSVs stay
valid historical evidence but cannot pass the new completeness check. There is no
automatic conversion from silence to approval. Review all harmful omissions; there
is no five-miss cap. New samples include short blocks, headings and notes.

```
python3 tools/sample.py --name new-run --seed new-run --per-book 4
python3 tools/split_sample.py new-run
# Review every part using docs/briefs/acceptance.md.
python3 tools/accept_report.py new-run
```

## Frozen benchmark

`python3 -m tools.benchmark` provides prepare, predict and score commands. Input is
JSON containing cases with id, book, author (stable identity), split (train/dev/test),
lang, original, optional year/nouncaps/verse/protected, and a source citation supplied
by the dataset curator. Multiple excerpts from one author/book must share a split.
Use actual piece authors in anthologies; editors are not a substitute. Author aliases
must be resolved by the curator. The check only knows the supplied identities; it
cannot prove that a lexicon or model has never seen an author.

```
python3 -m tools.benchmark prepare cases.json annotation-packet.json
python3 -m tools.benchmark predict cases.json rettskriv-predictions.json
# Human annotators fill accepted forms for EVERY token, including unchanged tokens,
# then set reviewer_kind=human and reviewed_by to their identity.
python3 -m tools.benchmark score adjudicated.json rettskriv-predictions.json
```

Each decision is {at, from, accepted:[...]} with original character offset. Every
word must have a decision. Empty annotations cannot be scored. Variants can have
multiple accepted replacements, including the original when preservation is valid.
Predictions are [{id,changes:[{at,from,to}]}]; all original-word changes must be listed.
The scoring interface deliberately restricts edits to original word spans so different
candidate systems cannot silently rewrite punctuation or whole sentences.

Report correct/incorrect replacements, missed required normalisations, correct
preservations, change precision and unchanged fraction, separately by split/language.
Incorrect replacements are not automatically labelled semantic errors: that severity
needs human adjudication. Predictions use the supplied excerpts as book context;
keep this identical across systems. Do not compare them with a run using more context.

`--development` allows model-authored regression fixtures, explicitly labelled
`development-only`; it does not make them an independent human benchmark. The checked
in `tests/fixtures/benchmark-development.json` is such a fixture. It tests the scoring
workflow and known traps, not generalisation. No human benchmark score is claimed.

See the [completed Apertium diagnostic comparison](apertium-comparison.md) for native
Bokmål/Nynorsk results, external-source sampling and a detected corpus overlap.
The [constrained-ranker comparison](context-ranker-comparison.md) tests a separate
model family on frozen constructed contrasts and documents a harmful unstable edit.
The [real historical passage comparison](historical-ranker-comparison.md) then tests
automatically generated alternatives on 31 passages and records source-grounded failures.
The [candidate-generation follow-up](candidate-generation-comparison.md) compares
guarded proposals on 30 more passages, adds schema-constrained responses and records
a remaining adjective failure plus the resulting deterministic preservation guard.

## Next comparison: evidence required before adoption

1. Freeze new, separately sourced author/book groups before additional lexicon tuning.
   Include substantial Landsmål, short passages, names, grammatical contrasts,
   quotations about spelling and mixed-language text. Check overlap with anthology
   authors and translated sources in the original corpus. Human adjudication is
   still outstanding; no model should fill this gap under a human label.
2. Compare full Ordbank morphology with [UiB's lemma/paradigm exports](https://ord.uib.no/ord_1_Ordlister.html).
   Freeze reviewed data versions; do not silently replace the target norm.
3. Test [Apertium Bokmål](https://github.com/apertium/apertium-nob) and
   [Nynorsk](https://github.com/apertium/apertium-nno) analysis/disambiguation components,
   not their translation output. They are GPL resources and need historical adaptation.
4. Compare a constrained contextual ranker only over permitted candidate readings plus
   abstention. Modern language-model fluency is not evidence that a historical reading
   is correct. Use the same benchmark predictions schema for each system.
5. Choose systems at matched incorrect-replacement rates and compare coverage, not
   overall accuracy alone. Tune thresholds on dev only; evaluate test once frozen.

[ODS](https://ordnet.dk/ods/) supplies historical Danish sense evidence, and
[Norsk Ordbok's corpus](https://oda.uib.no/noob/korpus.html) broader Nynorsk usage.
[NorNE](https://github.com/ltgoslo/norne) and Norwegian UD support name/grammar studies,
but are not historical-normalisation gold data. Check dataset permissions before
bulk reuse. None of these alternatives has yet been shown to improve this engine.

## Validation of this change

- 61 unit/regression tests pass, including malformed lexicon conditions, incomplete
  or stale acceptance reviews, author/book split leakage, protected spans, book
  isolation, passive voice, and participle/past-tense contrasts.
- Replayed accept-21 through accept-24: 432 paragraphs using the shipped N-gram
  snapshot for both baseline and candidate. Baseline: 17,232 changed words;
  candidate: 17,080. There are 155 differing decisions: 153 now preserve the original,
  and two correct plural-present replacements (sige -> sier; gjøre -> gjør).
  This is a behavior comparison, not fresh linguistic acceptance. Some preserved
  forms were correct normalisations before; the coverage tradeoff is intentional.
- Ten constructed development cases (36 words): baseline has four incorrect edits;
  candidate has none and one missed required normalisation (voksede, deliberately
  preserved). These cases were selected to expose known bugs, so this is regression
  evidence only, not an accuracy estimate.
- Python compilation, whitespace checks and a CLI smoke test pass.

Private corpus excerpts and audit packets are kept outside Git. They are not part of
this public benchmark. The public fixtures are newly constructed sentences.
