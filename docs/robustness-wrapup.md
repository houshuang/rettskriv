# Robustness campaign wrap-up — 19 October 2026

The final experimental opt-in engine recovers **44 of the 62 previously withheld
correct modernizations**, with **18 still withheld**. Two preserved forms already
have valid modern readings, leaving **16 genuine missed modernizations**. All
12 original protections against malformed output remain intact. The default,
model-free engine remains at38/62; the parser is not silently enabled.

This is an improvement with **no newly incorrect replacement observed in the
reviewed changes**, not a universal no-regression guarantee. The original goal of
recovering every previously correct decision has not been met. Keep PR1 in draft;
no merge or deployment is included.

## What the final push established

The final code change recovers one additional `forøgede→forøket`: the subject is
`Kongens Føielighed` and the object is `Thrøndernes Overmod`, with a correlative
prepositional adjunct between subject and verb. One original parser incorrectly
labels the adjunct's `som` as a second subject.

The recognizer consumes a complete comma-delimited `saavel ved NP, som ved NP`
construction. It requires supported determiners, dictionary adjectives and nouns,
and at most one recognized location phrase. Unsupported clauses, words, quotations
and footnote bodies cause refusal. Reviewed source classifications for
[Offergilde](https://ordnet.dk/ods/ordbog?query=offer-) and Hlade (explicitly identified
as a farm elsewhere in Faye1852) provide syntax evidence only; spelling keep entries
remain unchanged.

The original parses must agree on the finite root, surviving subject and objects.
The only removable extra subject is the certified correlative `som`. Both parsers
then process copies with that entire adjunct removed, retaining exact original
word offsets. They must pass the existing strict gate with the **same original
subject and object witnesses**. Output never deletes the adjunct. A failed parser
call applies no partial edits, and protected adjunct text prevents this proof.

Independent reviewers challenged the design and code. Sixteen actual-model
negative/refusal controls passed, including nominal captions, relatives, incomplete
or unknown phrases, quotes, footnote text, passive/copular contexts and protection.
The positive control recovered correctly. The complete real passage passes the
public API live test. A replay of1,014 cached field/tree pairs produces only this
one new source occurrence (present in two overlapping evaluation sets), with no
lost edits. Cached evidence is valid here because parser input and tokenization
remain unchanged except for the explicitly tested certified reduction.

## Approaches rejected in the final push

- **Long introductory accompaniment phrase:** the proposed independent finite
  continuation was actually ambiguous between past and participle. Singular `han`
  does not settle this: a participle can describe the accompanying plural men.
  The provisional recognizer was discarded.
- **Remote passive inheritance:** a passive list can switch to a finite clause,
  as in `Huset blev malet, Døren lukket, og Taleren talede`. The final verb needs
  finite `talte`, not passive `talt`. No auxiliary-scope shortcut was enabled.
- **Saint-title recipient exception:** title/name evidence alone cannot distinguish
  dedication from a nominal identity predicate. Independently supported semantic
  roles are still missing.
- **Sentence-sized parser input:** six complete sentences with boundaries agreed
  by both parsers produced exactly the same trees and no recovery; a seventh case
  failed boundary agreement. No context-trimming heuristic was adopted.

The16 remaining genuine misses are original indices3,4,9,10,27,30,35,39,41,43,45,
47,53,57,64,70. Their dispositions are in the [parser evaluation](dependency-parser-evaluation.md).
They require independently validated clause reconstruction, passive/semantic roles,
or better historical parsing. Shared mistakes cannot be fixed by asking for more
agreement from the same models. Further isolated exceptions now have low observed
return; this campaign is wrapped with explicit abstentions.

## Validation and limits

Coverage totals **36 complete books plus one complete story,2,500,544 routed words**.
There are **91 independently reviewed opt-in improvements** over conservative output
across that corpus. Sixteen of these came from the two new books and complete story
in the preceding round; they validate existing safeguards and are not gains caused
by this final change. The final rule's measured gain is one original case, not a
new-book generalization result.

107 tests were discovered:103 core tests pass and4 optional model tests skip in
the dependency-free run. All4 optional live-model tests also pass, including163
real-book target assertions (159 distinct targets),91 earlier adversarial inputs,
4 name/protection controls and17 new correlative cases (16 refusal/preservation
controls plus1 positive). Frozen parser evidence, source-offset reconstruction,
wrong-witness refusal and reduced-parser failure behavior are tested. Compilation
and whitespace checks pass.

Default behavior is unchanged by the final two opt-in-only patches. Historical
transcription caveats, routing, exclusions and the lack of excerpt-overlap checks
remain documented in the earlier reports. Unchanged text has not been exhaustively
annotated. Reviewers were independent agents, not human gold annotators; experimental
parser agreement remains fallible. Changing model weights requires rerunning live tests.

Private `out/final-push/` retains exact sentence and correlative experiments,
rejected designs, adversarial cases and outputs, the final cached replay and review.
Prior frozen corpus evidence remains under `out/final-35/`, `out/parser-trial/`,
`out/parser-next/` and `out/parser-round2/`. No paid model calls were added; estimated
cumulative model spend remains$2.6259 of the$30 cap. No Skard source or published
assets were modified.
