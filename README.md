# rettskriv

Spelling modernisation for historical Norwegian: Dano-Norwegian and riksmål (about
1800–1930) to modern bokmål, and landsmål to modern nynorsk. Same words, today's
spelling and inflection, with **meaning preservation as the goal, not a guarantee**: when the program is not sure,
it leaves the word as printed.

> Glatsnogen er rødbrun, med sorte Flekker paa Hovedet og to mindre langs efter Ryggen.
> Den holder sig paa tørre Steder, men er sjeldnere end Buormen. Rygskjællene ere ganske
> glatte, medens de hos begge de andre norske Slangearter have en ophøiet Linie langsefter.

> Glattsnoken er rødbrun, med sorte flekker på hodet og to mindre langs etter ryggen.
> Den holder seg på tørre steder, men er sjeldnere enn Buormen. Ryggskjellene er ganske
> glatte, mens de hos begge de andre norske Slangearter have en opphøyd linje langsetter.

(*Jensen, Læsebog for Folkeskolen*, 1863. Unchanged output; note what it left: *have* and
two noun capitals.)

It was built to give 27 digitised Norwegian school readers (1824–1931, 1.9 million words)
a modern-spelling reading layer next to the printed text. It is deterministic, needs no
model at run time and has no dependencies beyond Python's standard library by default.
An experimental, explicitly enabled parser pass is available below. The
intelligence is in a lexicon of about 64,000 decisions, each audited by language models
against the actual passages.

## Quick start

```sh
git clone https://github.com/houshuang/rettskriv && cd rettskriv
python3 -m rettskriv.fetch_ordbank             # Norsk ordbank, ~25 MB, once
echo "Han gik ud af Huset, og hvad han saae der, vidste ingen." | python3 -m rettskriv --nouncaps
# Han gikk ut av huset, og hva han så der, visste ingen.
python3 -m rettskriv --changes book.txt        # mark every change as [old→new]
python3 -m rettskriv --lang nno landsmaal.txt  # landsmål -> nynorsk
python3 -m rettskriv --lookup book.txt         # first fetch N-gram data for new forms (network)
```

```python
from rettskriv import modernise, book_engine, prepare

modernise("Han gik ud af Huset.", nouncaps=True)       # 'Han gikk ut av huset.'
modernise("Eg hev set det.", lang="nno")               # 'Eg har set det.'

book = [...]                                           # every paragraph of the book
prepare(book)                                          # optional, network: N-gram data for new forms
reader = book_engine(book)                             # learn book context once
for paragraph in book:
    result = reader.modernise(paragraph)
    result.text, result.changes                        # changes: [{"at", "from", "to", "why"}]
```

Give it whole books where you can (`context=`): it decides per book whether common nouns
are capitalised and which capitalised words are names. Python 3.11 or newer.

## How good it is

Historical results for `ce74a11`, measured by Claude Opus reviewers on fresh random paragraphs, judging every change
([details](docs/evaluation.md)):

| | Corpus it was built on | Four unseen books (Hamsun, Ibsen, Wergeland, 1840–1900) |
|---|---|---|
| Changes judged | 17,232 | 907 |
| Meaning changed | **0.08%** (14) | **0%** (0) |
| Wrong form (inflection, invalid spelling) | 0.73% | 1.2% |
| Wrong capital | 0.23% | 0.2% |
| Old forms left that mislead a reader | ~0.75 per 100 changes | ~10 per 100 changes |
| Words changed | 32.0% | 27% |

(The corpus column is the latest release; the unseen books were measured one round
earlier, before about 120 context rows were added.)

These model-reviewed samples do not establish an independent error guarantee.
The robustness changes after `ce74a11` have not yet received human acceptance review.
On unseen text the evaluated version leaves more old spelling: an author's own forms that the lexicon has never seen are left
as printed unless a trusted rule covers them. A new corpus needs its own held-out evaluation; adding audited forms may improve coverage.

## Known weaknesses

- **Conservative by design.** "Leave it as printed" is always allowed, so old forms
  remain where they have two readings and the neighbouring words do not settle which:
  *tog* (= *tok*, or the noun *tog*), *vare* (= *var*, or goods), *ved* (= *vet*, or the
  preposition), *have* (= *ha*/*har*, or *hage*), *lade*, *vide*, *Anden*. Context rows
  now change the certain cases (*han tog* → *tok*, *at vide* → *vite*, *vi vide, at* → *vet*,
  *en Have* → *hage*; about 9,000 occurrences); the rest stay as printed. Old plural
  verbs (*de sige*) and *-ede* participles are the commonest form errors.
- **Homographs read without enough context**: *ved* → *vet* where it is the preposition;
  *lade*/*lader* (reload, manners) read as *la*/*lar*; *baade* (boats) → *både*; *kaldet*
  (the call) → *kalt*; *I* after a regnal name read as the pronoun; *lod* (fate) → *lot*.
- **Names that are also words** are protected only when the book shows them as names
  (after a title, next to a first name, in the name bank): a dog called *Spids*, a place
  called *Krogen*, *for Bagen* (from behind) can still be lowered or respelled.
- **Grammar**: old plural present verbs (*de sige*) sometimes become infinitives (*si*)
  rather than *sier*; *-ede* participles before plural or definite nouns
  (*de udmærkede*) sometimes become *-et*; imperatives are sometimes read as present
  tense. *forat* + infinitive becomes *for at* rather than *for å*.
- **Capitals are normalised only partly.** A noun's capital is lowered when the word is
  respelled or is already a modern form, but a word left in its old spelling keeps its
  capital, and so does any word the book or the modern N-gram suggests is a name. In the
  13 noun-capitalising books about a third of the mid-sentence capitals remain (many of
  them real names: *Guds*, *Norges*, *Harald*). We tried
  lowering them all: on a 1,600-change check it turned names into common words (*Hans* →
  *hans*, *Halv*, *Kam*, *Ormen Lange*) and old spellings into misleading ones (*Sagen* →
  "the saw", *Billeder*, *Glas*), about 1% meaning errors, so it was reverted. The capital
  is often the only cue that an old form is a noun or a name.
- **Nynorsk is thinly tested**: two landsmål books in the corpus, about 6% of the judged
  changes.
- **Not a translation.** Archaic words (*thi*, *ei*, *atter*, *blot*) and word order stay;
  the text reads as old Norwegian in modern spelling, not as modern Norwegian.
- **Quotations, grammar examples and titles** are modernised like any other text unless
  they are detected as another language; a passage that discusses old spelling loses its
  point.

## How it works

Per word, in order: a curated, context-conditioned lexicon; name protection; forms
the modern word bank already allows (unless the NB N-gram shows the form died out after
1910); respelling rules, applied only when their chain has a one-sided 95% precision lower bound of ≥ 99.5% in the
audits (obligatory letter rules are an explicit policy exception); and grammar rules for the *-ede* past and plural verbs. The lexicon was built by
running every form of the corpus through Sonnet auditors, Opus verifiers and an Opus
homograph screen, then fixing every error the acceptance reviewers found.
[docs/how-it-works.md](docs/how-it-works.md) has the details, the lexicon format and the
tools for applying it to a new corpus; [docs/briefs/](docs/briefs/) has the model
instructions.

## Experimental dependency recovery

The default path remains conservative and model-free. An optional second pass
uses reviewed historical lemma identities plus agreement between Danish and Bokmål
dependency parsers. It never uses parser fluency to choose a word's historical sense.
It is experimental: agreement can reproduce shared parser mistakes, and the current
review is development evidence, not human gold. See the
[parser evaluation](docs/dependency-parser-evaluation.md) for measured results and limitations.

From a source checkout, explicitly install the optional dependency and models once:

```sh
python3 -m pip install -e '.[dependency-parser]'
python3 -c "import stanza; [stanza.download(lang, model_dir='data/stanza', package='default_fast', processors='tokenize,pos,lemma,depparse') for lang in ('da', 'nb')]"
```

```python
from rettskriv import book_engine
from rettskriv.dependency import DependencyResolver

resolver = DependencyResolver('data/stanza')  # local models; no automatic download
reader = book_engine(paragraphs, lang='nob', year=1852, nouncaps=True)
result = reader.modernise(paragraphs[0], resolver=resolver)
print(result.text)
print(resolver.errors)  # parse failures preserve the conservative output
```

For structured books, `tools/replay_book.py --dependency-models data/stanza`
opts in while preserving language and verse routing. Optional live tests run with
`RETTSKRIV_DEPENDENCY_MODELS=data/stanza python3 -m unittest tests.test_dependency_models`.
Stanza 1.15.0 is required; model installation is an explicit network operation.

## Related work

As far as we could find (October 2026), there is no other open tool that modernises
historical Norwegian to today's bokmål or nynorsk. Related work:

- **[MeMo corpus](https://huggingface.co/datasets/MiMe-MeMo/Corpus-v1.1)** (University of
  Copenhagen, CC BY 4.0): Danish and Dano-Norwegian novels 1870–1899 with a normalised
  layer (nouns lower-cased, *aa* → *å*, pattern rules towards the Danish 1948 norm). Same
  period and source language, but the target is Danish and normalisation is partial.
- **[Apertium nno-nob](https://github.com/apertium/apertium-nno-nob)** (GPL-2.0): rule-based
  translation between modern nynorsk and bokmål; a possible next step after rettskriv.
- **[Norsk ordbank](https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-5/)**
  (Språkbanken, CC BY 4.0): the modern word banks rettskriv checks every form against.
- General historical-text normalisation, none for Norwegian or Danish:
  [Bollmann's comparison of systems](https://aclanthology.org/N19-1389/) and
  [datasets](https://github.com/coastalcph/histnorm);
  [Pettersson et al. on Swedish and others](https://aclanthology.org/W14-0605/);
  [Norma](https://github.com/mbollmann/norma); [cSMTiser](https://github.com/clarinsi/csmtiser);
  [Transnormer](https://github.com/ybracke/transnormer) (German 1700–1900);
  [VARD 2](https://ucrel.lancs.ac.uk/vard/about/) (Early Modern English, a variant list like
  rettskriv's lexicon); and a [2025 comparison of LLM approaches](https://arxiv.org/abs/2506.23288).
- Edition practice: [Henrik Ibsens Skrifter's textual guidelines](https://www.ibsen.uio.no/tekstkritiskeRetningslinjer.html)
  keep the printed spelling (the diplomatic counterpart to a reading layer);
  [Bokselskap.no](https://www.bokselskap.no/hjelp_om/om_bokselskap) publishes texts in their
  original form. Background on the reforms: [Store norske leksikon](https://snl.no/.temaside/rettskrivingsreformer-i-norsk).

If you know of other work, please open an issue.

## Status

Built in October 2026 for its original corpus; robustness work is ongoing.
See the [campaign wrap-up](docs/robustness-wrapup.md) and
[robustness and benchmarking](docs/robustness.md) for safeguards, evaluation
commands, and the human review still required. Issues and pull requests with lexicon
corrections are welcome; a correction is a row in `lexicon/<norm>/core.csv`.

## Licence

Code: MIT. Lexicon: CC BY 4.0. Norsk ordbank (downloaded at setup) is © Språkbanken, CC BY
4.0; the N-gram snapshot is derived from the National Library of Norway's N-gram service.
See [DATA-LICENSE.md](DATA-LICENSE.md).
