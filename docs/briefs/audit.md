# Audit brief: modern spelling of historical Norwegian

You judge single words from 19th- and early 20th-century Norwegian school readers
(Dano-Norwegian/riksmål, and landsmål). A reading layer shows each text in modern
spelling next to the original. The modernisation is mechanical; your verdicts become
its lexicon. The rule: **never change meaning.**

## The policy

- **Same word, modern form.** The modern form is the same word in today's spelling and
  inflection, in mainstream conservative-moderate bokmål (or modern nynorsk for nn
  packets): *havde* → *hadde*, *Øine* → *øyne*, *Skibe* → *skip*, *svarede* → *svarte*,
  *sengi* → *senga*. Prefer the form a modern bokmål school text would use
  (-en definite: *boken*, *-et* or *-te* past as the word takes it).
- **Never substitute another word.** *thi*, *ei* (= ikke), *blot*, *atter*, *stedse*, *kun*
  stay as they are: replacing them is rewording, not spelling. Archaic but still
  understandable words stay too.
- **When in doubt, keep.** Keeping the old spelling is always allowed. A wrong modern
  form, or the right form of the wrong word, is the one failure that matters.
- **Names, foreign words, Latin, abbreviations, numerals in words: keep.**
- **nn packets: the result must be nynorsk** (2012 norm), never bokmål.
- Case is handled by the program: give targets in lower case.

## Your input

A TSV with one item per line. `examples` holds up to three passages from the books, with
the word marked `[old→engine output]`.

- **rule packets** (`*-rule-*.tsv`): the engine changed `from` into `to` by respelling
  rules. Is `to` the same word, correctly modernised, in every example?
- **left / inbank packets**: the engine left `form` as printed. `left`: no rule found a
  modern form (`candidates` lists ties). `inbank`: the form is a valid modern word, but
  its use collapsed after 1910 (`candidates` holds the ratio), so it may be an old
  spelling of another word (*dit* for *ditt*, *lande* for *land*, *ønskede* for *ønsket*).
- `compound: x` in `candidates`: the program split the form into parts it already knows
  and modernised each. About one in ten of these is wrong: a split in the wrong place
  (*hovedsyssel* is *hoved-syssel*, not *hode-syssel*), a head that is not a word of
  its own (*tømmermandens* → *tømmermannens*, not *-manndens*), or no compound at all
  (*krevedes*, *burtyver*). Treat it as a suggestion: `fix` with the proposal, `fix`
  with a corrected target, or `keep`, exactly as for any other item.

Check any modern form you propose with
`python3 tools/lookup.py form ...` (add `--nn` for nynorsk):
`YES` means the norm allows it. `compound` means the bank lacks the whole word but
knows its parts (or it is a genitive in -s): that target is accepted too, so a
compound or genitive you are sure of is `fix`, not `keep`. A target that prints `no`
will be rejected.
Batch many forms in one call.

## Your output

Write a TSV to the path you are given, header `id\tverdict\ttarget\tnote`, one line per
input item, every item answered:

- `ok`: (rule packets) the engine's form is right in all examples. target empty.
- `fix`: the right modern form is `target` (one word or two, e.g. *i dag*), the same
  word, right in all examples you see and in any normal use of this old form.
- `keep`: leave as printed (a name, foreign, an archaic word without a modern spelling,
  a word substitution, or the old form is still the normal modern form).
- `context`: the right form depends on context (two different words or inflections
  share this old spelling). target lists the readings, e.g. `ta (verb) | tak (noun)`.
  The program will leave it as printed unless a context rule is written later.
- note: short, only when it helps (why fix, which reading, OCR error suspected).

`ok` and `fix` change text in every book, including books not yet in the library:
give them only when you are sure for this old form in general, not just these examples.
Use `context` when another common reading exists. A suspected OCR error is `keep`
with note `ocr`.

Work through every line in order. Do not stop early, do not summarise, do not skip.
When done, reply with only the counts per verdict.
