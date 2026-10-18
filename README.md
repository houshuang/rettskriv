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
   non-archaic bank form that is the only one reachable is accepted; suffix rules must
   land on the inflection they respell; and the chain must be trusted (below).
5. **Grammar** (`Engine.grammar`): the -ede past against the -ede adjective, and plural
   verbs after *vi*, *de*, *I*, decided by the neighbouring words.

Whether a book capitalises its nouns is detected per book; in such books a lower-case
word is no noun, which several lexicon rows use (*tog* → *tok*, but *Tog* stays).
Pieces in another language (Swedish, English, landsmål inside a riksmål reader) are
detected by function words and go to the right engine or are left as printed.

## Robustness: how the lexicon is made

Rules alone are right about 95–97% of the time per rule chain (`tools/rule_precision.py`),
not enough for "never change meaning". So every form the library contains is decided
once and stored:

1. `tools/survey.py` runs the engine over the library and lists what rules changed,
   what was left for want of a decision, and in-bank forms whose use collapsed.
2. `tools/packets.py --round N` cuts those into packets; a Sonnet auditor per packet
   follows `AUDIT-BRIEF.md` (ok / fix / keep / context, every target checked against the
   bank with `tools/lookup.py`).
3. `tools/verify_packets.py --round N`: every auditor `fix` (a target the rules did not
   find) goes to an independent Opus verifier (`VERIFY-BRIEF.md`). A fix changes text
   only after the verifier agrees; until then, and on disagreement, the form stays.
4. `tools/ingest.py` writes `lexicon/<norm>/audit.csv`. Curated files (`core.csv`,
   `context.csv`) take precedence. Context verdicts stay as printed unless a context row
   is written; the -ede past/participle and plural verbs are left to the grammar rules.

5. `tools/homograph_packets.py` and `HOMOGRAPH-BRIEF.md`: every change made at least
   five times without context goes to an Opus screen for a second reading of the old
   form (*lidt*: litt or lidd; *Lege*: games or doctor). `tools/homograph_ingest.py`
   writes `lexicon/<norm>/homograph.csv`, which is authoritative for its forms: a risky
   form changes only in the context given, otherwise it stays as printed.

Forms seen once get a compound proposal (`tools/compounds.py`) in their packet; about
one in ten proposals is wrong, so they only reach text through the auditor and verifier.

A rule result is applied without audit only when its chain is trusted
(`data/trusted-chains.json`, ≥ 99.5% over ≥ 30 audited forms, or the reforms' own letter
equivalences). Anything else is "pending": left as printed until audited.

## Adding a book

```sh
python3 tools/build.py <book>         # mechanical, no model calls: out/modern/<book>.json
python3 tools/render_site.py <book>   # piece pages with the edition's own builder: out/site/<book>/
```

About 98.7% of the lexicon-decided words in a reader also occur in the other readers, so
a new book is nearly fully modernised at once. Its remaining new forms are pending (left
as printed). Optional, cheap: `tools/survey.py --books <book>`, a packets round, one
auditor and one verifier, `tools/ingest.py`, rebuild.

To rebuild a live site, build beside it and swap it in, so a running export never sees
a half-written folder:

```sh
python3 tools/build.py --out out/modern.next
python3 tools/render_site.py --layers out/modern.next --site out/site.next
python3 tools/swap_site.py out/site.next   # atomic exchange; old tree kept as out/site.prev-<stamp>
```

Skard picks up `out/site/` (`MODERN_ROOT` in `web/delivery/library-assets.mjs`) and
shows an Original / Moderne switch on each piece page; the printed text is the default.

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
