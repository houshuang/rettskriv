# Targeted check: one change at a time

Each item shows a passage from a 19th- or early 20th-century Norwegian school reader, as
printed and in a mechanically modernised spelling (bokmål; nynorsk for `nno` items), with
one word in brackets: the change to judge (`old → modern`). The rule is **never change
meaning**; the modern text should be the same words in today's spelling, inflection and
capitalisation (common nouns lower case, names capitalised). Leaving a word as printed is
always allowed. Other words in the passage are not under review.

For each item decide whether the bracketed modern form is right here:

- `meaning`: a different word, or the sentence now says something else (a name turned
  into a common word, the wrong one of two readings).
- `form`: the same word, but the wrong inflection or not a valid form in today's norm.
- `case`: a name's capital lowered, or a common noun's capital kept mid-sentence. A
  capital kept on a word left in its old spelling is fine.
- otherwise it is right: write nothing for it.

Write a TSV to the path you are given, header `n\tkind\tfrom\tto\tbetter\tnote`, one line
per wrong item only. Judge every item; do not stop early or sample. Then reply with:
items judged, meaning errors, form errors, case errors.
