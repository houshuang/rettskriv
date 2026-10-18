# Data licences

- **`lexicon/`**: the curated and audited decisions of this project, © 2026 Stian Håklev,
  licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Every modern
  form was checked against Norsk ordbank (below).
- **`data/ngram.tsv.gz`**: relative frequencies of word forms, 1850–1910 and 1990–2020,
  queried from the National Library of Norway's N-gram service (DH-lab,
  `api.nb.no/dhlab/nb_ngram`), aggregated to two averages per form. Credit: National
  Library of Norway. `python3 tools/fetch_ngram.py` rebuilds it from the service.
- **Norsk ordbank** (bokmål 2005, nynorsk 2012), Språkbanken at the National Library of
  Norway, CC BY 4.0. Not included; `python3 -m rettskriv.fetch_ordbank` downloads it.

The source books the lexicon was built from are not included.
