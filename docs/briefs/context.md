# Context brief: when can a two-reading form be changed?

A program modernises the spelling of 19th- and early 20th-century Norwegian school
readers (bokmål target). Some old forms are left as printed everywhere because they have
two readings: *tog* is *tok* (took) or *tog* (train, procession, campaign); *vare* is *var*
(were) or *vare* (goods, to last); *ved* is the preposition *ved* or *vet* (knows). The
rule is **never change meaning**; leaving a word as printed is always allowed. Your job:
find the contexts in which one reading is certain, and write them as rows, so that those
occurrences are modernised and the rest stay as printed.

## Tools (run from /Users/stian/src/rettskriv)

- `python3 tools/context_probe.py FORM` lists where FORM is left as printed: the commonest
  previous word / case / next word, and a sample with context. `nc` marks a book that
  capitalises common nouns: there a lower-case word mid-sentence is never a noun, and a
  capitalised one mid-sentence is a noun or a name.
- `python3 tools/context_probe.py FORM --when "CLAUSES" --all` prints **every** occurrence a
  row with those clauses would change. Read all of them before you propose the row.
- `python3 tools/context_probe.py FORM --changed` shows what the engine already changes.
- `python3 tools/lookup.py WORD ...` checks that a target is valid bokmål (`YES`).
- Existing rows: `grep -n '^FORM,' lexicon/bokmal/*.csv`. Rows are tried in order and
  the first match wins; your rows go before the final unconditional row.

The `when` syntax is at the top of `rettskriv/lexicon.py`. The useful keys:
`lower`/`cap`, `mid`/`initial`, `nouncaps`/`nonouncaps`, `prev=a|b`, `next=a|b`,
`notprev=`, `notnext=`, `prev2=` (the word before the previous one), `nextbreak=`
(next word after punctuation), `nexttags=`/`nexthas=` (bank tags of the next word's modern
form, e.g. `verb:inf`, `subst`, `adj`), `nextend=` (next word's ending). Neighbours are
the printed words, lower case; `prev`/`next` do not reach across punctuation.

## What a good row is

- **Right at every occurrence it matches.** If one match in fifty is the other reading,
  narrow the row (add `notnext=`, require `lower`, `nouncaps`, …) or drop it. A typical
  safe signal: a subject pronoun before the word (*han tog*, *jeg ved ikke*), a modal or
  *at* before an infinitive (*vil vide*, *at have*), an article before a noun (*et tog*),
  a lower-case word in a noun-capitalising book (not a noun), a capital mid-sentence in
  such a book (a noun or a name: careful).
- **The same word, modern form.** *tog* → *tok*, *vare* → *var*, *Have* → *hage*,
  *Haven* → *hagen*, *taget* → *tatt*. Never a different word. Inflection must fit the
  context (*de vare* → *var*; *at have* → *ha*; *have* after *vi/de* → *har*).
- **Coverage is secondary.** A narrow row that is always right beats a broad one.
- Names, quotations in other languages, and verse do not get special treatment; just
  make sure your matches are right.

## Output

Write a TSV to the path you are given, header `source\ttarget\twhen\tnote\tmatches`,
one line per proposed row, in the order they should be tried, `matches` = how many
occurrences the probe showed for it (all of which you read and judged right). Then reply
with, per form: rows proposed, occurrences they change, and what stays as printed and why.
