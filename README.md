# rettskriv

Mechanical spelling modernisation for historical Norwegian texts: Dano-Norwegian and
riksmål (1800–1930) to modern bokmål, landsmål to modern nynorsk. It powers the
"modern spelling" reading layer of the Lesebok library editions shown on Læreplanatlas.

## The rule

Stian, 18 October 2026: switch every library book to a modern spelling; mechanical, so a
new book costs nothing; spend tokens on making it robust; ignore rhyme and metre; **never
change meaning**.

From that:

- **Same word, modern form.** A word is respelled and reinflected in its modern form
  (*havde* → *hadde*, *Øine* → *øyne*, *at gaa* → *å gå*, *sengi* → *senga*). One word is
  never replaced by another (*thi*, *ei*, *blot* and *atter* stay).
- **When in doubt, leave it as printed.** A word left in its old spelling is a
  harmless miss. A wrong modern form is the one failure that is not allowed.
- **The printed text is never touched.** The modern text is a derived layer; evidence
  and quotes always use the original.
- **Landsmål becomes nynorsk, never bokmål.** Every modern form must be in the target
  norm's word bank (bokmål 2005 or nynorsk 2012).
- Rhyme and metre do not constrain the result.

## How a word is decided

`rettskriv/engine.py`, in order:

1. **Curated lexicon** (`lexicon/<norm>/*.csv`): rows for one old form, optionally
   conditioned on context (capitalised or not, the neighbouring words, the bank tags of the
   next word). A form with rows but no matching row is left as printed.
2. **Names** are left as printed: bank proper nouns, and capitalised forms the book uses
   after a title or next to a known first name.
3. **A form the modern bank allows** is left as printed (only a noun's capital is
   lowered), unless its use collapsed after 1910 by the NB N-gram (*sagde*, *mig*, *blev*:
   "archaic"); those only the lexicon may change.
4. **Respelling rules** (`rettskriv/rules.py`): obligatory letter rewrites (*aa*, *qv*,
   *ph*, *øi*) then optional ones (*b d g* → *p t k*, doubled consonants, *æ*). Only a
   unique non-archaic bank form at the shallowest depth is accepted; suffix rules must
   land on the inflection they respell.

Whether a book capitalises its nouns is detected per book; in such books a lower-case
word is no noun, which several lexicon rows use (*tog* → *tok*, but *Tog* stays).
Pieces in another language (Swedish, English, landsmål inside a riksmål reader) are
detected by function words and go to the right engine or are left as printed.

## Data

- `data/ordbank/`: Norsk ordbank bokmål 2005 and nynorsk 2012 (Språkbanken, CC BY 4.0),
  downloaded tarballs, not in Git.
- `data/cache/ngram.sqlite`: NB N-gram relative frequencies 1850–1910 and 1990–2020,
  `tools/fetch_ngram.py` fills it.

## Commands

```sh
python3 tools/fetch_ngram.py      # once, resumable
python3 tools/survey.py           # whole library: what changes, what is left, why
python3 -m unittest discover tests
```
