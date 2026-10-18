# Contextual selection on real historical passages

18 October 2026. **The real-source experiment does not support automatic model
promotion of pending candidates.** The candidates sometimes omit the correct reading,
and the model may accept a wrong modern word even when preservation is available.

## Source and frozen selection

31 real passages, 6,830 Rettskriv word tokens, from four books:

- Kristian Elster, *Tora Trondal* (1879), eight excerpts.
- Alexander Kielland, *Garman og Worse* (1880), eight excerpts.
- Amalie Skram, *Sjur Gabriel* (1887), eight excerpts.
- Arne Garborg, *Bondestudentar*, 1908 edition, seven pages of Landsmål.

The first three are the original-text files from
[MiMe-MeMo, Corpus v1.1](https://huggingface.co/datasets/MiMe-MeMo/Corpus-v1.1), CC BY 4.0.
Garborg comes from [Project Runeberg's raw OCR](https://runeberg.org/gaskriftir/1-1908/).
See [the source sampling record](apertium-comparison.md) for filenames, page selection,
checksums and transcription limitations. Garborg page 145 was excluded because of
known 12-word-shingle overlap with the development corpus. This does not establish
complete author/book independence. OCR errors, dialect, foreign phrases, running
headers and truncated page-boundary sentences remain in the input.

Unlike the constructed pilot, alternatives were generated automatically, with no
manually inserted correct answer. For each passage we sampled up to four baseline
changes and four preserved words having pending rule or weak-past alternatives,
using seed `real-passages-v1`. All candidates, source offsets and baseline edits were
frozen before the calls. Total: **178 targets — 124 changed, 54 preserved**. Of these,
149 are Bokmål and 29 Nynorsk; only one Nynorsk target is a proposed additional edit.
The sample is enriched for alternatives and does not represent the population of words.

Baseline engine revision: `fcbbfc1839de7199d3d849e33766b8a53a07a63c`; shipped frequency
snapshot and local Ordbank, without corpus-frequency cache. Book context is the sampled
passages grouped by book. No gold annotations were created. The new public sampler
reproduces the private frozen cases and baseline exactly.

## Flash results

Gemini 2.5 Flash, same instruction as the constructed pilot, temperature 0, thinking
budget 1,024, output cap 8,192. Four book batches per order, two shuffled orders
(`historical-v1-0` and `historical-v1-1`). All 178 answers were returned in each order.
The model saw passage text and allowed choices; no baseline preferences or review labels.

| Observation | Order 0 | Order 1 |
|---|---:|---:|
| Additional edits to preserved words | 54 | 53 |
| Vetoes of baseline changes | 0 | 0 |
| Changed replacement for a baseline edit | 0 | 1 |
| Answers outside supplied choices | 0 | 2 |
| Entire book batches accepted by validator | 4 / 4 | 2 / 4 |

Order 1 counts describe raw model proposals, **not applied changes**. Its invalid
book batches were rejected and no combined predictions file was produced. The two
out-of-choice proposals were `Nu` → `Nå` (only `Nu`/`nå` offered) and `Vejret` → `veiret`
(only `Vejret`/`veirett` offered). The capitalization attempt may be linguistically
reasonable, but bypassing the supplied choices is still disallowed. Five target
selections differed between orders, including two different readings of `skrævede`.

Codex read the context of all 54 added edits in the valid first order. The review
record labels 49 plausible, four unsafe and one unresolved dialect-policy case.
This is **model review of selected proposals**, not human gold or a measured precision
estimate. The complete 6,830-word output and every existing baseline edit have not
received fresh linguistic adjudication.

## Concrete failures

| Source location | Model proposal | Source evidence and problem |
|---|---|---|
| Skram block 23, offset 233 | `Vejret` → `veirett` | A raised leg “i Vejret”: the air, not a road right. The needed reading is missing from the candidate set. |
| Skram block 41, offset 762 | `Væræ` → `være` | Dialect noun; the same supplied passage's footnote glosses it as `Verden`. The model selects an infinitive instead. |
| Kielland block 355, offset 1084 | `mixed` → `mikset` | Partially translates the foreign expression `mixed drops`, contrary to the instruction. |
| Elster block 115, offset 849 | `plejede` → `pleiet` | Habitual “plejede at strides”; the candidate belongs to the care/tend reading, whereas habitual modern `pleie` takes `pleide`. |

The [official dictionary distinguishes the two verb readings](https://ordbokene.no/bm/pleie).
The local Ordbank likewise gives habitual lemma 52210 paradigm 030 and no `pleiet`
form; that form belongs to care/tend lemma 52209. A valid target-bank form is therefore
insufficient. The correct `pleide` alternative was absent. Both Flash orders still
selected `pleiet`; both also selected `mikset`. Repetition/agreement would retain
these errors. The deterministic baseline preserves all four source forms.

Do not confuse `skrevet` with an automatic error: it is also a legitimate preterite
of *skreve*. The second order chose adjectival `skrevede` in a finite-verb position.
Likewise, dialect `trøit` requires an editorial policy, not simply the most familiar
modern word. These are precisely the distinctions an undifferentiated word list misses.

## Stronger-model comparison

Gemini 2.5 Pro was then run on the **same frozen inputs and order 0**, with the same
instruction, temperature 0, requested thinking budget 4,096 and output cap 16,384.
All four calls completed. The API reported modelVersion `gemini-2.5-pro`; reported
thinking usage was used for cost accounting even where it exceeded the requested budget.

Pro proposed 52 additional edits, vetoed one baseline capitalization change, and
returned one out-of-candidate answer (`Sypigen` → `Sypiken`). Three book batches passed
validation; the invalid batch was rejected, so there is no combined applied Pro output.
These counts, like the second Flash order, describe raw proposals, not successful edits.

Pro abstained on `Vejret` and `Væræ`, an improvement on Flash order 0. However, it still
selected `pleiet` and `mikset`, and chose adjectival `skrevede` where a finite past-tense
verb is needed. It also chose `trøyt`, whose local Bokmål analyses are noun/imperative,
in the dialect adjective position. More reasoning helped some cases but did not
establish reliable preservation. No prompt or candidate was corrected between models.

Four Pro calls cost approximately $0.3126; this real-source experiment totals about
$0.3897, or $0.4042 including the earlier constructed pilot. All are estimates from
reported tokens and [published rates](https://ai.google.dev/gemini-api/docs/pricing),
not billing statements. There were no paid retries. Pro evidence is in
`out/historical-pro/`, separate from the Flash records.

## Engineering improvements from the real run

1. Fixed an adapter bug the constructed examples missed: legitimate baseline splits
   such as `tilslut` → `til slutt` were rejected by an overly broad single-word check.
   Baseline replacements now retain the benchmark's nonempty-string contract. New
   ranker choices remain restricted to supplied single-word alternatives.
2. Added `tools.sample_ranker`: deterministic sampling by changed/preserved stratum,
   actual engine alternatives, original offsets and source metadata. It respects
   explicit protected spans, verse and book settings, leaves multiword baseline edits
   intact, creates no gold and refuses an existing output directory.
3. Added exact, attributed source excerpts as conservative-preservation regressions.
   These protect existing abstention on the four harmful candidates; they do not
   whitelist model suggestions or pretend to establish human-reviewed translations.
4. Added one dictionary-backed lexicon variant: `øjeblik` → `øyeblikk`, alongside
   the existing `øieblik` entry. [ODS explicitly connects the Danish form to Norwegian
   øyeblikk](https://www.ordnet.dk/ods/ordbog/60001206), and the
   [Bokmål dictionary records the modern spelling](https://ordbokene.no/nob/bm/%C3%B8yeblikk).
   Both real occurrences are the noun after `et`. A full replay of all 31 passages
   changes exactly these two decisions, with no other word-level replacement changes.
   Explicit protected spans still preserve the original. This is a source/dictionary
   decision, not automatic promotion from the model. The sample is now development
   evidence and cannot be reused as an untouched test set.
5. Kept output validation strict. Invalid batches are retained for diagnosis and never
   silently repaired or scored as successful. The first paid response was recovered
   from disk after the adapter fix, without making the same paid request again.

```sh
# input.json: the prior source packet, excluding the identified overlapping page.
python3 -m tools.sample_ranker input.json frozen --per-stratum 4 --seed real-passages-v1 --policy legacy
python3 -m tools.context_ranker prepare frozen/cases.json prompt.json --seed historical-v1-0
# Run each book's prompt through the chosen model; retain raw outputs and usage.
python3 -m tools.context_ranker apply frozen/cases.json predictions.json \
  --baseline frozen/baseline.json --answers answers.json
```

Apart from the documented dictionary-backed spelling variant, sampled alternatives
remain untrusted; the four harmful candidates remain preserved. Introducing a model into
production would require a different candidate-generation/selection design and a
separate evaluation. Priorities supported by these failures: source annotations for
foreign/dialect/quoted spans; lemma-specific alternatives; genuine abstention when no
candidate fits; and validation on unseen books. A blanket quote detector or a majority
vote is not established by this experiment.

Private evidence: `out/historical-ranker/` contains frozen inputs, requests, responses,
validation errors, predictions, usage and the explicitly model-labelled review ledger.
Eight Flash calls cost approximately $0.0771 at published token rates; no retries.

Validation: 52 tests pass; Python compilation, whitespace checks, exact sampler replay,
and the full 31-passage before/after replacement comparison pass.
