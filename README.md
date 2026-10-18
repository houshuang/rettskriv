# rettskriv

Spelling modernisation for historical Norwegian: Dano-Norwegian and riksmål (about
1800–1930) to modern bokmål, and landsmål to modern nynorsk. Same words, today's
spelling and inflection, and **never a change of meaning**: when the program is not sure,
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
model at run time and has no dependencies beyond Python's standard library. The
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
from rettskriv import modernise, modernise_result, prepare

modernise("Han gik ud af Huset.", nouncaps=True)       # 'Han gikk ut av huset.'
modernise("Eg hev set det.", lang="nno")               # 'Eg har set det.'

book = [...]                                           # every paragraph of the book
prepare(book)                                          # optional, network: N-gram data for new forms
for paragraph in book:
    result = modernise_result(paragraph, context=book)
    result.text, result.changes                        # changes: [{"at", "from", "to", "why"}]
```

Give it whole books where you can (`context=`): it decides per book whether common nouns
are capitalised and which capitalised words are names. Python 3.11 or newer.

## How good it is

Measured by Claude Opus reviewers on fresh random paragraphs, judging every change
([details](docs/evaluation.md)):

| | Corpus it was built on | Four unseen books (Hamsun, Ibsen, Wergeland, 1840–1900) |
|---|---|---|
| Changes judged | 16,954 | 907 |
| Meaning changed | **0.09%** (15) | **0%** (0) |
| Wrong form (inflection, invalid spelling) | 0.47% | 1.2% |
| Wrong capital | 0.14% | 0.2% |
| Old forms left that mislead a reader | ~0.8 per 100 changes | ~10 per 100 changes |
| Words changed | 31.5% | 27% |

On text like the corpus it is close to finished. On unseen text it stays as safe but
leaves more old spelling: an author's own forms that the lexicon has never seen are left
as printed unless a trusted rule covers them. One audit round over a new text's forms
(see [how it works](docs/how-it-works.md)) closes most of that gap.

## Known weaknesses

- **Conservative by design.** "Leave it as printed" is always allowed, so old forms
  remain: *tog* (= *tok*, reads as "train"), *vare* (= *var*), *ved* (= *vet*), *Have*
  (= *hage*), *bed* (= *bet*), *Anden* (= *annen*). Verbs and nouns whose old form is also
  a modern word are the hardest.
- **Homographs read without enough context**: *endnu* → *ennå* where it means *enda*
  ("even more"); *I* after a regnal name read as the pronoun (*Vilhelm I* → *dere*); the
  adjective *ven* (fair) → *venn* (friend) in books that capitalise nouns (*en ven Fugl*),
  found after the final measurement; *lod* (fate) → *lot*.
- **Names that are also words** are protected only when the book shows them as names
  (after a title, next to a first name, in the name bank): a dog called *Spids*, a place
  called *Krogen*, *for Bagen* (from behind) can still be lowered or respelled.
- **Grammar**: old plural present verbs (*de sige*) sometimes become infinitives (*si*)
  rather than *sier*; *-ede* participles before plural or definite nouns
  (*de udmærkede*) sometimes become *-et*; imperatives are sometimes read as present
  tense. *forat* + infinitive becomes *for at* rather than *for å*.
- **Capitals**: verse line starts and nouns after a semicolon are handled inconsistently;
  some noun capitals are kept mid-sentence.
- **Nynorsk is thinly tested**: two landsmål books in the corpus, 803 of the 16,954 judged
  changes.
- **Not a translation.** Archaic words (*thi*, *ei*, *atter*, *blot*) and word order stay;
  the text reads as old Norwegian in modern spelling, not as modern Norwegian.
- **Quotations, grammar examples and titles** are modernised like any other text unless
  they are detected as another language; a passage that discusses old spelling loses its
  point.

## How it works

Per word, in order: a curated, context-conditioned lexicon; name protection; forms
the modern word bank already allows (unless the NB N-gram shows the form died out after
1910); respelling rules, applied only when their chain has proved ≥ 99.5% precise in the
audits; and grammar rules for the *-ede* past and plural verbs. The lexicon was built by
running every form of the corpus through Sonnet auditors, Opus verifiers and an Opus
homograph screen, then fixing every error the acceptance reviewers found.
[docs/how-it-works.md](docs/how-it-works.md) has the details, the lexicon format and the
tools for applying it to a new corpus; [docs/briefs/](docs/briefs/) has the model
instructions.

## Status

Finished in October 2026 for its original purpose. Issues and pull requests with lexicon
corrections are welcome; a correction is a row in `lexicon/<norm>/core.csv`.

## Licence

Code: MIT. Lexicon: CC BY 4.0. Norsk ordbank (downloaded at setup) is © Språkbanken, CC BY
4.0; the N-gram snapshot is derived from the National Library of Norway's N-gram service.
See [DATA-LICENSE.md](DATA-LICENSE.md).
