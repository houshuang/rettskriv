# Dependency-parser evaluation, 19 October 2026

**Decision: retain the deterministic safeguards; do not authorize replacements
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
