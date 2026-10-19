# Apertium comparison, 18 October 2026

**Decision: keep Apertium outside the production normalizer.** Its modern Norwegian
analysis and constraint grammar are useful experimental evidence, but recognition
and disambiguation are not historical sense preservation. The engine remains
standard-library-only. No GPL dictionaries, binaries or corpus texts are distributed
in this repository.

We built and ran both language analysers and contextual grammars locally. This was
an analysis comparison, not an Apertium translation or normalisation benchmark.

| Diagnostic sample | Before: unknown / word cohorts | After Rettskriv | After: ambiguous / word cohorts (CG) |
|---|---:|---:|---:|
| 24 Dano-Norwegian excerpts | 1,048 / 4,416 (23.7%) | 193 / 4,348 (4.4%) | 704 / 4,348 (16.2%) |
| 8 Landsmål pages | 318 / 2,659 (12.0%) | 98 / 2,637 (3.7%) | 541 / 2,637 (20.5%) |

Unknown counts above use the morphology stage, before CG guessing. Apertium can
join words into multiword cohorts, so denominators differ between original and
normalised text. These are not word-level accuracy or coverage scores. CG further
reduces ambiguity, but a single reading may still be wrong. Guessed readings are
counted separately by the probe; Bokmål CG guessed 286 original and 51 normalised
cohorts. No target annotations or human accuracy estimate were produced.

## Why a modern reading is insufficient

Constructed probes demonstrate the distinction:

- `Han lader geværet`: Apertium selects the verb `lade`, present tense, compatible
  with loading a gun. But it selects that same modern verb in `Han lader hende gaa`,
  where the historical intended verb is “let”. The latter needs historical context.
- `De sige det`: the modern analyser supplies infinitive `sige` (sink/seep), not the
  historical plural-present reading of “say”. Recognition alone cannot authorize
  keeping it or using its modern lemma to generate a replacement.
- `Han voksede Bordet`: CG supplies a participial/adjectival reading for `voksede`
  and guesses capitalised `Bordet` as a proper name. This does not resolve the wax/grow
  distinction that motivated the conservative safeguard.

Using “unique CG reading” as a safety gate would therefore be unsound. A future
candidate ranker needs historical senses, permitted alternatives and abstention,
then must be evaluated at matched incorrect-replacement rates on adjudicated data.

## Data and contamination

Dano-Norwegian source: [MeMo v1.1](https://huggingface.co/datasets/MiMe-MeMo/Corpus-v1.1),
CC BY 4.0. We used original `texts/` files, not the modern-Danish normalisation as
Bokmål gold: `1879_Elster_ToraTrondal.txt`,
`1887_SkramA_SjurGabrielHellemyrsfolket.txt`, and `1880_Kielland_GarmanOgWorse.txt`.
Eight blank-line blocks per novel with at least 40 whitespace-delimited words were
sampled using seed `rettskriv-external-v1`. The packet has 4,457 Rettskriv word tokens;
no OCR repair, dehyphenation or rewriting was applied during sampling.

Landsmål source: [Garborg, Bondestudentar, 1908 edition](https://runeberg.org/gaskriftir/1-1908/).
Predetermined printed pages 20, 45, 70, 95, 120, 145, 170 and 195 (HTML filenames are
printed page + 10, zero-padded to four digits). Extract the raw OCR between
`<!-- mode=normal -->` and `<!-- NEWIMAGE2 -->`, remove HTML tags and decode entities.
Retain line breaks and running headers. These are unproofread OCR, with mixed-language
dialogue, and must not be mistaken for clean historical orthography or gold targets.
Each case records its page URL and downloaded HTML hash.

A case-insensitive 12-word exact-shingle scan against all 27 existing corpus books
found **25 matching shingles on Garborg page 145** in corpus book `garborg`.
No other sampled case had an exact match at that length. This check misses spelling
variants, shorter overlaps and repeated authors. Neither sample is certified
book/author-disjoint; both are diagnostic samples only. Do not use either as the
final held-out benchmark or tune rules and then claim independent accuracy on it.

## Reproduce the analysis

Pinned upstream inputs:

- [lttoolbox 3.8.3](https://github.com/apertium/lttoolbox/releases/tag/v3.8.3)
- [utfcpp 4.0.6](https://github.com/nemtrif/utfcpp/releases/tag/v4.0.6)
- [CG-3 1.5.1](https://github.com/GrammarSoft/cg3/releases/tag/v1.5.1)
- [apertium-nob 3d63c61](https://github.com/apertium/apertium-nob/tree/3d63c61e55209cd847c8ef4b863715036cce04bf)
- [apertium-nno 2efb616](https://github.com/apertium/apertium-nno/tree/2efb61642310ca504b9f1b2ed29fc6bb7a030b13)

Build native lttoolbox and CG-3 with CMake (ICU, libxml2, Boost and utfcpp headers).
Build targets `lt-comp lt-proc lt-append lt-compose` and `cg-comp cg-proc` respectively.
For each language, reproduce the upstream Makefile's analyser pipeline: compile main
and proper-name `.dix` left-to-right with its `.acx`, then `lt-append` them. For
Bokmål also compile `detriple.dix` and apply `lt-compose --inverted --anywhere` to the
joined analyser. Save as `DATA/LANG/LANG.automorf.bin`. Compile the `LANG.seg.rlx`
and `LANG.rlx` grammars with `cg-comp` into that same folder. Nynorsk uses the joined
analyser directly. The probe runs `lt-proc -w -e`, then segmentation `cg-proc`, then
contextual `cg-proc -w`. Do not substitute translation output.

```sh
# Catalogue has book, author, lang, path, source, optional year/nouncaps.
# Source paths are relative to the catalogue file. Sampling emits empty gold fields.
python3 -m tools.sample_external catalogue.json cases.json --per-book 8
python3 -m tools.apertium_probe cases.json --data-dir DATA \
  --lt-proc /absolute/path/to/lt-proc --cg-proc /absolute/path/to/cg-proc \
  --out analysis.json
```

Each analysis file includes original/normalised text and full readings, counts, and
SHA-256 hashes of input cases, executables and analyser/grammar files. Freeze the
Rettskriv Git revision and Ordbank resources alongside it. This run used the engine
from `95ba9a01a2725eda94bb033bd49e5614a1c877f8` and its shipped frequency snapshot,
with no local corpus-frequency cache. Excerpts are the book context, not full novels.
Both tools refuse to overwrite output; unadjudicated packets cannot be scored as
gold even with `--development`.

Local evidence for this review is in ignored `out/comparison/` (source archives,
builds, frozen packets, raw analyses and overlap results). Human adjudication remains
unperformed. A subsequent [constrained-ranker experiment](context-ranker-comparison.md)
tests constructed contrasts; it is not a historical accuracy benchmark. These measurements do not
justify replacing the deterministic engine or advertising a new accuracy figure.
