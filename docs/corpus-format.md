# Corpus format

The batch tools (`tools/build.py`, `survey.py`, `sample.py`, `fetch_ngram.py`, …) read a
folder of books, one subfolder per book: `<corpus>/<book>/book.json`. Point
`RETTSKRIV_CORPUS` at the folder. This is the format of the Lesebok editions the
lexicon was built from; only the fields below are read.

```json
{
  "book": {"language": "dansk-norsk"},
  "printed_year": 1844,
  "items": [
    {
      "id": "002",
      "kind": "piece",
      "title": "Om Fabelen.",
      "blocks": [
        {"type": "p", "text": "Fabelen er en billedlig Fremstilling …", "marks": [[120, 21]]},
        {"type": "stanza", "lines": [{"t": "Mjølner, hans tunge Hammer,"}, {"t": "er dog …"}]},
        {"type": "figure", "caption": "Ræven og Ravnen."}
      ],
      "notes": [{"text": "Fodnote …"}]
    }
  ]
}
```

- `book.language`: `dansk-norsk` (Dano-Norwegian/riksmål → bokmål) or `landsmaal`
  (→ nynorsk). Each piece is also checked by function words, so a landsmål poem inside a
  riksmål reader goes to the nynorsk engine, and Swedish, German, English or Latin
  passages are left alone.
- `printed_year`: optional; a few lexicon rows depend on it (`before=YYYY`).
- `items`: only `kind: "piece"` items are modernised. Their `title`, `nav_title`,
  `subtitle`, `section`, every block's `text` or stanza `lines`, block `caption`s and
  `notes` are processed.
- `marks`: optional `[offset, value]` pairs in a block's text (page breaks); the layer
  remaps the offsets into the modern text.

All texts of a book are read first, to decide whether it capitalises common nouns and
which capitalised words are names there; so give whole books, not excerpts, where you can.

For a plain text there is no need for this format: use `python3 -m rettskriv file.txt`
or `rettskriv.modernise(text, context=[...])`.
