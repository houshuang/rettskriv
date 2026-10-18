# Homograph screen: does the old form have a second reading?

A reading layer shows 19th- and early 20th-century Norwegian school readers in modern
spelling (bokmål; nynorsk for `nno` packets). Each line below is a change the program
makes **everywhere**, without looking at context: the old form `from` becomes `to`. The
owner's rule is **never change meaning**; leaving a word as printed is always allowed.

Your one question per line: **can the old form, in a normal text of the period, be a
different word, inflection or a name, for which `to` would be wrong?**

- *lidt* → *litt* is risky: *lidt* is also the participle of *lide* (har lidt = suffered).
- *Eders* → *deres*: risky only as polite *Deres* (Eders Majestæt).
- *Lege* → *lege*: risky; capital *Lege* in a book that capitalises nouns can be the
  plural of *leg* (games), and *lege* reads as doctor.
- *Liv* → *liv*: risky; also a first name.
- *paa* → *på*, *Øine* → *øyne*, *havde* → *hadde*: safe.
- Words from foreign passages (Latin, French, Swedish, Danish quotations) also count as a
  second reading if the old form is common in them.

Readings that are only theoretical, or so rare you would not expect them in a school
reader, do not make a line risky. The examples show three uses; think beyond them.

## Output

TSV with header `id\tverdict\twhen\tnote`, one line per input id, every id answered:

- `safe`: change everywhere, as now. `when` empty.
- `risky`: give in `when` the context in which the change is still right, using these
  keys joined by `;` (all must hold), or leave `when` empty to keep the old form always:
  - `cap` / `lower`: the word is capitalised / lower case as printed
  - `mid` / `initial`: mid-sentence / sentence- or line-initial
  - `nouncaps` / `nonouncaps`: the book capitalises common nouns / does not
  - `prev=a|b`, `next=a|b`: previous / next word as printed, lower case, is one of these
  - `notprev=a|b`, `notnext=a|b`
  Only give a `when` that makes every match right; when no simple context is safe, leave
  it empty. `note`: the other reading, in a few words.

Work through every line in order; do not stop early. When done, reply with only the
counts of safe and risky.
