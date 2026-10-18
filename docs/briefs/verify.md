# Verification brief: second opinion on proposed modern forms

Another auditor proposed a modern spelling for each old Norwegian form below
(19th-century Dano-Norwegian/riksmål → modern bokmål, or landsmål → modern nynorsk for
nn packets). If accepted, the old form is replaced by the proposal **in every book of
the library**. The rule: **never change meaning**. Policy:

- Same word, modern form (spelling and inflection). No substitution of another word.
- Keeping the old form is always safe; a wrong form or the right form of a different
  word is the failure that matters.
- Names, foreign words, abbreviations stay.
- Words in Danish, Swedish, Faroese, Icelandic, Old Norse, German or Latin passages stay
  as printed, even when a Norwegian word looks alike (*hús* in a Faroese ballad).
- Compounds: check each part. The first element keeps its compound form (*hoved-* stays
  *hoved-* in *hovedsak*, not *hode-*), and the head must be the right word and
  inflection (*tømmermannens*, not *tømmermanndens*). `lookup.py` prints `compound`
  for a target it would accept as a compound; that is not proof the split is right.

For each line decide independently whether the proposal is right for this old form in
general (not only in the examples shown): is it the same word, in the same inflection,
correctly spelled in today's norm, and is there no other common reading of the old form
that the proposal would get wrong?

Check forms with `python3 tools/lookup.py form ...`
(`--nn` for nynorsk); batch many per call.

Output TSV, header `id\tagree\ttarget\tnote`, one line per input id, every id answered:
- `agree` = `yes` or `no`.
- When `no`: `target` is your better modern form if you are sure of it, or `=` to keep the
  old form; `note` says why in a few words (other reading, wrong inflection, name…).

Work through every line in order; do not stop early. When done, reply with only the
counts of yes and no.
