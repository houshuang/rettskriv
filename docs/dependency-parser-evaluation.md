# Dependency-parser evaluation, 19 October 2026

## Final campaign result

The final push adds one certified-correlative recovery: **44/62 restored with
opt-in parsing,18withheld**, including two valid preserved forms and16 genuine
misses. Default38/62 and all12 malformed-output protections remain unchanged.
No previously approved recovery was lost. See [the wrap-up](robustness-wrapup.md)
for the final rule, rejected approaches, validation and limits. The snapshots
below describe earlier stages; their remaining-case tables precede this final gain.


## Remaining-case follow-up against 3176829

This round recovers **one additional original case**, `ægtede→ektet`, in Olaf's
voyages and marriages. The opt-in original audit is now **43/62 restored, 19 withheld**:
two preserved forms are already valid modern readings, leaving **17 genuine misses**.
Default output remains at 38/62. All 12 malformed-output protections and all 73
previously approved opt-in improvements remain intact.

The added evidence resolves a noun/past homograph only inside a complete bounded
source construction: `Da` + personal subject + `var/blev/ble` + adjective, comma,
inverted verb + personal subject + direction, optional single-noun prepositional
phrase, then overt coordination. It skips no intervening words. Original morphology
must be exactly noun/past-verb; names, protected words, keep entries and unresolved
mappings still veto anchor use. Both parsers must still agree on the existing full
finite path and subject. This adds an independent source proof, not an exception
to parser agreement. Historical *vikingetog* is reviewed noun evidence from
[NAOB's vikingtog entry](https://naob.no/ordbok/vikingtog); its spelling keep entry
is not overridden. Other bank nouns and a direction without a PP are also tested.

Independent challenge used actual models on 11 new grammatical negatives, including
prepositional noun coordination (`til Børn og bedrøvede Enker`), four protected/name
controls, and two positive controls. All 15 preservation controls remained unchanged;
both positives recovered. An exact replay of 1,014 cached field/tree pairs found
only the intended new original occurrence, duplicated in two evaluation sets, with
no lost edits. Model inputs and tokenization are unchanged by this patch.

Two additional complete books and one complete story were processed in full:
[Dunker, Gamle Dage (1871)](https://www.bokselskap.no/boker/gamledage/tittelside),
[Thoresen, Billeder fra Vestkysten af Norge (1872)](https://www.bokselskap.no/boker/vestkysten/tittelside),
and [Thoresen, Min Bedstemoders Fortælling (1867)](https://www.bokselskap.no/boker/bedstemoder/tittelside).
The story is not its containing anthology. The set has 1,919 paragraphs and 192,381
engine-token words; three foreign paragraphs/159 words are skipped, leaving
**192,222 routed words**. Dependency parsing also skips 199 verse paragraphs.
All 87 eligible prose paragraphs were parsed, with no model errors. Independent
review approves all **16 existing-parser improvements** (Dunker13, Vestkysten2,
Bedstemoder1), with zero incorrect or uncertain replacements. These 16 validate
previous safeguards on more sources; they are **not gains caused by the new rule**.

Cumulative corpus coverage is **36 complete books plus one complete story,
2,500,544 routed words**. The new rule does not add a recovery in these new works;
its observed gain is still confined to one original case. Across this enlarged
corpus, 90 opt-in improvements versus conservative output have independent review
(73 earlier +16 new-source validations +1 new recovery). Unchanged text is not
exhaustively labelled, and these judgments are not human gold. Historical edition
transcriptions, foreign routing and source/paragraph boundaries are retained;
no facsimile verification or excerpt-overlap claim is made.

### Disposition of every remaining case

| Original index / form | Why it remains withheld |
| --- | --- |
| 3 udvandrede | Parsers disagree on finite versus adjective; inverted subject is misanalysed. |
| 4 forøgede | Relation, subject and coordination disagree. |
| 9 kaarede | Fresh parsing still disagrees on finite/adjective and yields a spurious extra subject; resolving lexical sense alone would not suffice. |
| 10 oprettede | Subject and object are reversed between parsers. |
| 12 forøgede | Danish adds `som` as a second subject inside a correlative phrase. |
| 27 straffede | `drog` remains ambiguous; the long fronted PP is outside the new complete temporal frame. |
| 30 forøgede | Both parsers bury the real direct object under the prepositional phrase; a shared oblique also occurs in bad captions. |
| 35 helligede | Passive recipient/title structure is misparsed; finite evidence cannot authorize passive inflection. |
| 39 krænkede | Elliptical passive scope and attachment disagree. |
| 41 overraskede | Fresh parsing: Danish finite coordination, Bokmål adjectival modifier. Expanding eligibility would not recover it. |
| 43 befæstede | Passive ellipsis and participle attachment disagree. |
| 45 svækkede | Immediate governor agrees but inherited subject ancestry differs, including a nonfinite governor; local agreement cannot replace full-path proof. |
| 47 foraarsagede | Finite clause versus participial complement disagreement. |
| 53 erobrede | One parser coordinates with an infinitive, the other with a finite verb. |
| 57 lettede | Contextual lexical meaning is correct, but fresh parsing attaches it nonfinitely to embedded `kommen`. |
| 64 forenede | Both parsers misread the predicate as an adjective modifying `Flid`. |
| 70 udfærdigede | Both parsers attach the predicate as a participial modifier of the calendar date. |

Case17 is the one newly recovered case and is excluded from this table. The two
already-valid preserved forms are excluded as before. No broader oblique, immediate-
governor or extra-subject exception was enabled. These cases need independently
validated clause reconstruction or better historical parsing, not a weaker gate.

Validation:102 tests discovered;99 pass without models and3 optional tests skip.
All3 optional live-model tests also pass:163 real-book target assertions (159 distinct,
four repeated across evaluation sets),91 constructed no-new-edit inputs and4 explicit
protected/name controls. The frozen-parser tests include the new original recovery.
Compilation and whitespace checks pass. No paid model calls; no merge or deployment.


Private reproduction artifacts: `out/parser-round2/` holds the pinned3176829
archive, full-source default/parser JSONL, aligned trees, baseline summary, exact
cached replay, remaining-case dispositions, actual-model challenges and independent
reviews. The complete new-book default pass uses the identical default code; this
patch changes only the optional evidence path. No paid calls were added.


## Lexical identities and opt-in parser follow-up (against d577afe)

The default output is unchanged across **34 complete books, 2,308,322 routed word
tokens and 51,957 fields/paragraphs**, and the existing 132 external passages.
The seven added books contribute 399,140 tokens in 12,064 paragraphs. Default
coverage remains **38/62 restored, 24 withheld**, including two valid modern forms.

A reviewed inventory covers 75 historical infinitive families (77 identities).
Candidate records preserve historical identity, modern lemma and role-specific
forms separately. For example, historical *vande* can map to modern *vanne*
(water) or *vande* (reject/dislike); modern dictionary uniqueness cannot resolve
that distinction. Missing morphology also remains an unresolved alternative.
*Kaare* retains choose/card-wool identities except in a bounded personal-object
role-assignment frame such as `kaarede hende til sin Brud`. Past and participle
candidates use the same identity resolution. Lexical uncertainty still abstains.

`DependencyResolver` is an **experimental opt-in**, not a new default. Danish
parses the complete original field; Bokmål parses conservative output. Both must
agree on exact source-aligned finite-past nodes, coordination paths and subject
heads, with matching direct objects or an independently unambiguous finite source
anchor. Passive auxiliaries, nonfinite governors, token splits/merges, names,
protected text, verse, other languages and explicit lexicon decisions cannot be
overridden. Both parses are frozen before edits. External parser failure leaves
all output unchanged and records an error. Local models are required; normalization
never downloads them. This is selected local structural agreement, not agreement
on entire trees or a guarantee of grammatical correctness.

The first gate was rejected after both parsers misread two constructed captions:
`Soldaterne forfærdede ved Synet af Fienden` and `Fanerne foldede ved Kongens Baare`.
Requiring object evidence or an independent finite anchor removes these mistakes.
The tightened gate recovers **four of the remaining 22 original cases**:
`ægtede→ektet`, `kløvede→kløvde`, `indviklede→innviklet`, `betegnede→betegnet`.
With opt-in parsing the cumulative original result is **42/62 restored, 20 withheld**;
two withheld forms are already valid, leaving **18 genuine missed modernizations**.
All 12 original malformed-output protections remain intact.

The original 27-book parser scan covers 731 eligible fields/802 eligible targets.
The seven added books contribute 181 eligible targets; complete books were used
for context and default comparison, with parsing restricted to eligible fields.
The final gate retains **73 independently approved improvements**: 58 in the
original schoolbooks (including the four original-audit recoveries) and 15 in
the added books (Collett 10, Kielland 5). No newly incorrect replacement was
observed in those retained changes. The stricter anchor exclusions remove three
earlier optional proposals; seven Wergeland proposals from the completed scan
were separately reviewed before inclusion. All 58 schoolbook decisions are covered
by recorded approvals with zero conflicting judgments.
Independent agents reviewed changes in full source context. These are model
judgments, not human annotations. Unchanged text was not exhaustively labelled;
“no observed new errors” is not a global error-rate or no-regression guarantee.

The seven added texts are [Ibsen, Vildanden (1884)](https://www.gutenberg.org/ebooks/13041),
[Undset, Jenny (1911)](https://www.gutenberg.org/ebooks/32245),
[Hamsun, Sult (1890)](https://www.gutenberg.org/ebooks/30027),
[Jessen, S/S Styggen (1917)](https://www.gutenberg.org/ebooks/34183),
[Kielland, Skipper Worse (1899 collected edition)](https://runeberg.org/skipwors/),
[Hansen, Mordet paa Maskinbygger Roolfsen (1840)](https://www.bokselskap.no/boker/roolfsen/tittelside),
and [Collett, Amtmandens Døttre (1854/55 first edition)](https://www.bokselskap.no/boker/ad1utg/tittelside).
These are development texts, not held-out gold; school-reader excerpt overlap was
not checked. Sult's transcriber converted aa to å, and Ibsen's transcription uses
å; neither establishes aa accuracy. Scholarly transcriptions correct some printing
errors. Modern commentary is excluded, but no new facsimile comparison was made.
The new-book runs use declared Bokmål paragraphs, whereas schoolbook runs preserve
structured language/verse routing and the same 29 excluded pieces.

Reproduction evidence lives privately in `out/parser-next/`: frozen books and
metadata, exact d577afe archive, default replays, full original/conservative parser
inputs, aligned DA/NB trees, rejected and retained proposals, independent reviews,
and gate-filter scripts. Current retained-output files reconstruct text from the
conservative baseline and retained edits. Unit fixtures freeze actual parser
outputs, not manually invented gold trees; live fixtures exercise real models.
No paid model calls were added. Earlier experiments below are historical evidence,
not the current acceptance rule.


Validation: 100 tests discovered, 98 pass and two optional live-model tests skip
without explicit models. Both live tests also pass with installed models: 147 real
book target assertions (143 distinct targets, four repeated across original-audit
and schoolbook fixtures) plus 80 constructed inputs, including eligibility controls.
The 60 frozen real-parser decisions pass without models. Compilation and whitespace
checks pass. Independent review covers all 73 retained changes with no conflicting
judgments; no new incorrect replacement was observed. All seven new books and all
27 schoolbooks are compared in full for default-output stability. Unchanged output
was not exhaustively annotated. Model packages can change independently of the
pinned library; rerun the optional suite after changing installed weights.

## Prior parser trial (before this follow-up)

**Earlier decision: retain the deterministic safeguards; do not authorize replacements
from parser consensus.** Modern Danish and Bokmål parsing is useful for locating
missed finite verbs, but agreement did not ensure the proposed modern word had
the correct historical meaning. No parser dependency or model is loaded by the
production engine.

## Method

Local CPU experiment: Stanza 1.15.0, Torch 2.14.1, official Danish DDT and Norwegian
Bokmål `default_fast` packages, processors `tokenize,pos,lemma,depparse`, four CPU
threads, no character language models. Models and environment are private ignored
artifacts, approximately 435 MB of models. No paid model calls were used.

The Danish parser sees the original complete source field. The Bokmål parser sees
conservative d718b50 output with the target word left in its original spelling.
Neither sees a proposed replacement. A target must align exactly by start and end
character offsets to one parser token containing one word. The experimental gate
requires `VerbForm=Fin` from both parsers and the same dependency-relation label.
This is agreement on a label, **not agreement on a full dependency tree**.

Official references: [Stanza models](https://stanfordnlp.github.io/stanza/download_models.html),
[Stanza pipeline](https://stanfordnlp.github.io/stanza/pipeline.html),
[Danish DDT](https://universaldependencies.org/treebanks/da_ddt/index.html), and
[Norwegian Bokmål](https://universaldependencies.org/treebanks/no_bokmaal/index.html).
These treebanks do not establish accuracy on historical Norwegian.

## Results

| Set | Size | Gate result | Interpretation |
| --- | ---: | --- | --- |
| Development | 57 targets | 19/30 finite positives; 0/27 nonfinite controls accepted | Gate selected after observing failures; not held-out precision |
| Earlier reviewed real-book targets, excluding development overlap | 130 | 84 compatible outputs accepted; 0 incompatible | Output compatibility, not independent POS gold; some adjective/past forms coincide |
| New deterministic sample from other books, excluding Faye | 191 | 55 proposed changes; 54 correct, 1 wrong after independent review | 98.2% observed proposed-output correctness; insufficient for automatic use |

The development set contains 35 previously withheld cases, 12 malformed-output
protections and 10 constructed adversaries. With only finite agreement, three
wrong development readings survived; requiring relation-label agreement excluded
those three. That tuning is why its zero cannot be treated as validation.

The challenge sample uses seed 20261019, up to eight eligible tokens per book,
across the remaining 26 books. Eligibility: Bokmål route, historical `-ede`, no
explicit lexicon entry, a generated weak-past candidate different from conservative
output. It yielded 191 targets. Both independent reviewers read complete original
fields; a third reviewer checked finite readings across all 55 proposals. These
are model judgments, not human annotations. One selected target is verse; no
production routing rule was relaxed. One accepted target (`elskede`) has an
incorrect shared `xcomp` label despite a correct proposed finite surface form.

The error is Hersleb's `vandede hendes Hjord`: Jacob gives Rachel's animals water.
The generated candidate `vandet` belongs to modern **vande**, reject/dislike;
the intended word is **vannet/vatnet**. Both parsers correctly recognized a finite
verb, yet neither checked historical lexical identity. Compare
[Bokmålsordboka: vande](https://ordbokene.no/bm/vande) and
[Bokmålsordboka: vanne](https://ordbokene.no/bm/vanne).

A targeted corpus inspection found the same wrong output already produced for
Erichsen's `du vandede blomsten`. The production repair explicitly preserves this
ambiguous historical form. It does not globally rewrite the infinitive `vande`,
which also has historical noun and rejecting-verb readings. Correct preservation
is preferable to silently choosing either modern meaning.

## Remaining original decisions

Of 24 withheld original decisions, two (`lønnede`, `samlede`) already permit valid
modern readings. The other 22 require evidence beyond the bounded current frames:

| Structural issue | Original audit indices |
| --- | --- |
| Remote coordination, objects and prepositional phrases | 1, 15, 17, 27, 31, 41, 45, 53, 57, 64 |
| Nested/appositive subjects | 12, 30, 47 |
| Fronted/purpose/subordinate clauses | 3, 9, 10 |
| Pronoun plus complex genitive object | 4 |
| Passive recipient and gapped passive coordination | 35, 39, 43 |
| Coordinated genitive noun subject | 50 |
| Demonstrative subject, calendar date and object | 70 |

A final independent challenge considered a small rule for 70: initial demonstrative,
predicate, complete calendar date, then indefinite noun phrase. It remains unsafe
without determining that phrase's role: `en Gang` can be an adverbial, and the
preceding historical form can still be a nominalized participle. An arbitrary
list of temporal exclusions would not establish complete clause analysis. The
recipient `St. Olaf` in 35 similarly needs argument evidence, not merely another
recognized name. These expansions were not enabled.

The practical limit of this campaign is now lexical sense and broader clause
structure, not a missing general-purpose parser package. Further automatic recovery
needs independently reviewed historical sense/valency evidence and evaluation of
complete clause analyses, including negatives. The 54 good parser proposals are
useful review candidates, not a safe authorization rule. Do not turn these specific
source occurrences into production allowlists to inflate the recovery count.

## Evidence and reproduction

Private `out/parser-trial/` retains `prepare.py`, `run.py`, `heldout.py`,
`run-heldout.py`, `challenge.py`, `run-challenge.py`, frozen inputs, DA/NB outputs,
`challenge-proposals.json`, and per-item `review-a.json`/`review-b.json`. Parsing
scripts use `download_method=None` after explicit model installation. Source text
stays outside Git. `out/final-35/` retains exact baseline and candidate snapshots,
all 27 frozen books, source-aligned comparisons and the original-74 audit. Use the
existing `tools/replay_book.py` for production comparisons; the experimental parser
scripts never write normalized books or authorize engine changes.
