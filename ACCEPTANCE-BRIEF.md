# Acceptance read: modern spelling against the printed text

You read paragraphs from 19th- and early 20th-century Norwegian school readers, each
shown as printed and in the mechanically modernised spelling (bokmål; nynorsk for `nno`
paragraphs). Every changed word carries a number ⟨n⟩. The owner's rule is **never change
meaning**; the modern text should be the same words in today's spelling and inflection.

Judge **every numbered change**. Report only the bad ones:

- `meaning`: the modern form is a different word, or changes what the sentence says
  (wrong reading of a homograph, a name turned into a common word, a verb read as a noun).
- `form`: same word but wrong inflection or a misspelling (wrong tense, number, gender,
  definiteness; not a valid form in today's norm; bokmål in a nynorsk paragraph).
- `case`: a capital wrongly lowered (names) or a noun capital wrongly kept.

Also list up to five **misses** per paragraph only when they hurt reading badly (an old
form left that a modern reader would misread). Misses are not errors; leaving a word as
printed is allowed.

Do not report style preferences (a valid modern form you would not have chosen), rhyme,
or metre.

Write a TSV to the path you are given, header `n\tkind\tfrom\tto\tbetter\tnote`, one line
per bad change (`kind` = meaning, form or case) and one per miss (`kind` = miss, `n`
empty). Then reply with: changes judged, meaning errors, form errors, case errors, misses.
