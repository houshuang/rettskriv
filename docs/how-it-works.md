# How it works

## The rule

The project brief (October 2026): modernise the spelling of every book in a library of
19th- and early 20th-century Norwegian school readers; mechanical, so a new book costs
nothing; spend model tokens on making it robust, not on each book; ignore rhyme and
metre; **never change meaning**.

From that:

- **Same word, modern form.** A word is respelled and reinflected in its modern form
  (*havde* → *hadde*, *Øine* → *øyne*, *at gaa* → *å gå*, *sengi* → *senga*). One word is
  never replaced by another (*thi*, *ei*, *blot* and *atter* stay).
- **When in doubt, leave it as printed.** A word left in its old spelling is a harmless
  miss. A wrong modern form is the one failure that is not allowed.
- **The printed text is never touched.** The modern text is a derived layer; quotes and
  citations should use the original.
- **Landsmål becomes nynorsk, never bokmål.** Every modern form must be in the target
  norm's word bank (Norsk ordbank: bokmål 2005 or nynorsk 2012).
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
   follows [`briefs/audit.md`](briefs/audit.md) (ok / fix / keep / context, every target checked against the
   bank with `tools/lookup.py`).
3. `tools/verify_packets.py --round N`: every auditor `fix` (a target the rules did not
   find) goes to an independent Opus verifier ([`briefs/verify.md`](briefs/verify.md)). A fix changes text
   only after the verifier agrees; until then, and on disagreement, the form stays.
4. `tools/ingest.py` writes `lexicon/<norm>/audit.csv`. Curated files (`core.csv`,
   `context.csv`) take precedence. Context verdicts stay as printed unless a context row
   is written; the -ede past/participle and plural verbs are left to the grammar rules.
5. `tools/homograph_packets.py` and [`briefs/homograph.md`](briefs/homograph.md): every change
   made at least twice without context (first five or more, then a second screen of the
   forms made two to four times, `--min 2 --skip`) goes to an Opus screen for a second reading of the old
   form (*lidt*: litt or lidd; *Lege*: games or doctor). `tools/homograph_ingest.py`
   writes `lexicon/<norm>/homograph.csv`, which is authoritative for its forms: a risky
   form changes only in the context given, otherwise it stays as printed.

6. `tools/context_probe.py` and [`briefs/context.md`](briefs/context.md): forms left as
   printed because they have two readings (*tog*, *vare*, *have*, *ved*) get context rows
   for the contexts where one reading is certain. The probe prints every occurrence a
   candidate row would change, so each row is read against all its matches before it is
   added; the rest stays as printed.

Forms seen once get a compound proposal (`tools/compounds.py`) in their packet; about
one in ten proposals is wrong, so they only reach text through the auditor and verifier.

A rule result is applied without audit only when its chain is trusted
(`data/trusted-chains.json`, ≥ 99.5% over ≥ 30 audited forms, or the reforms' own letter
equivalences). Anything else is "pending": left as printed until audited.

The audits were run with Claude models (Sonnet auditors, Opus verifiers and screeners)
as one agent per packet of a few hundred forms; the briefs in [`briefs/`](briefs/) are the
complete instructions they were given. The packets and verdicts themselves are not in the
repository (they quote the source books); the outcome is in `lexicon/`, each row with its
origin (`core`, `acceptance`, `audit:<packet>`, `homograph`).

## The lexicon files

`lexicon/bokmal/` and `lexicon/nynorsk/`, CSV with columns `source, target, when, note,
origin` (`target` `=` means "leave as printed"). The `when` syntax is documented at the top
of [`rettskriv/lexicon.py`](../rettskriv/lexicon.py). Load order:

- `homograph.csv`: forms with a second reading; authoritative for their forms.
- `core.csv`, `context.csv`: hand-curated rows, including every fix from the acceptance
  rounds. Rows for one form are tried in order; the first match wins.
- `audit.csv`: generated by `tools/ingest.py`; only for forms no curated file covers.

To correct a form, add a row to `core.csv` (a conditional row before an unconditional
one), then check it with `tools/recheck.py` against earlier acceptance samples.

## Applying it to a corpus

The tools under `tools/` work on a corpus of books in the format described in
[`corpus-format.md`](corpus-format.md) (set `RETTSKRIV_CORPUS` to its folder):

```sh
python3 tools/build.py [book ...]          # out/modern/<book>.json: the modern layer, no model calls
python3 tools/survey.py                    # what changes, what is left and why, per form
python3 tools/fetch_ngram.py               # N-gram frequencies the snapshot lacks (network)
python3 tools/sample.py --name s1 --seed x # an acceptance sample (out/eval/s1.md) for a reviewer
python3 tools/split_sample.py s1           # split it into reviewer parts
python3 tools/accept_report.py s1          # meaning-error rate from the reviews
python3 tools/recheck.py s1                # replay reviewed errors against the current engine
python3 tools/context_probe.py tog --when "lower;prev=han"   # every occurrence a context row would change
```

The layer is keyed by field path (`blocks/3/text`), so a renderer can show the original
and the modern text side by side. `tools/render_site.py` and `tools/build_epub.py` are the
integration with the Lesebok edition builder (HTML piece pages, and a modern and a
parallel EPUB per book); they need that builder (`RETTSKRIV_LESEBOK_SCRIPTS`) and serve as
examples. `tools/swap_site.py out/<x>.next` swaps a finished build into `out/<x>`
atomically, so a reader never sees a half-written folder.

A new book from the same period is mostly covered by the existing lexicon (about 98.7% of
the lexicon-decided words in each reader also occur in the others). Its new forms are
"pending" and left as printed unless their rule chain is trusted. To cover them: a survey,
a packets round with an auditor and a verifier, `tools/ingest.py`, rebuild.
