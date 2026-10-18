# Evaluation

## Method

Every round drew fresh random paragraphs (four per book, at least 40 words, never a
sample name used before) and showed each one as printed and in modern spelling, every
changed word numbered. Claude Opus reviewers judged every numbered change with
[`briefs/acceptance.md`](briefs/acceptance.md):

- **meaning**: the modern form is a different word, or changes what the sentence says.
- **form**: the same word, but the wrong inflection or not a valid form in today's norm.
- **case**: a name's capital wrongly lowered, or a noun's capital wrongly kept.
- **miss**: an old form left as printed that a modern reader would misread (reported
  only when it hurts; leaving a word as printed is allowed).

The release bar was at most 0.14% meaning errors among the changes in a fresh sample.

## The corpus it was built on

27 Norwegian school readers printed 1824–1931 (25 Dano-Norwegian/riksmål, 2 landsmål),
1.9 million words, of which 601,803 (31.5%) are changed.

| Rounds | Meaning errors among changes |
|---|---|
| 1–3 (first reviewer pool) | 0.50% → 0.25% → 0.14% |
| 4–8 (stricter reviewer pool) | about 0.19% → 0.156% → 0.142% → 0.124% → 0.099% (the last on 9,108 changes) |
| Final (four samples, 16 reviewers) | **15 in 16,954 changes (0.088%)** |

Between rounds, every reported error was fixed at its cause (a lexicon row or an engine
rule) and replayed against all earlier samples with `tools/recheck.py`.

Final round, all categories (share of changes):

| Kind | Count | Rate |
|---|---|---|
| meaning | 15 | 0.09% |
| form | 80 | 0.47% |
| case | 23 | 0.14% |
| harmful misses | 129 | (0.76 per 100 changes) |

The 15 meaning errors:

- *endnu* → *ennå* where it means *enda* ("even more": *endnu farligere*), 4.
- The regnal numeral read as the pronoun (*Fredrik Vilhelm I* → *dere*), 2.
- *hvorledes* → *hvordan*, 2. The reviewer flagged these as a word substitution, though the
  sense is the same.
- One each: *lod* (fate) → *lot*; *en penge* (a coin) → *penger*; *for Bagen* (from behind)
  → *bagen*; *i et Nu* → *nå*; the dog's name *Spids* → *spiss*; *sagte* (said) → *sakte*;
  *lave sig til* → *lavet*; *skibe* changed inside a grammar text that cites it as the old
  form.

Nynorsk is thinly measured: 803 of the 16,954 judged changes were in nynorsk paragraphs
(two landsmål readers in the corpus).

## Text it was not built on

48 random paragraphs from four Project Gutenberg books outside the corpus: Hamsun, *Sult*
(1890); Ibsen, *Vildanden* (1884); Wergeland, *Jan van Huysums Blomsterstykke* (1840); and
*Norsk literaturhistorie for gymnasiet* (c. 1900). N-gram frequencies for their new forms
were looked up first (`prepare()`). One Opus reviewer, same brief.

| Kind | Count |
|---|---|
| changes | 907 (27% of 3,304 words) |
| meaning | 0 |
| form | 11 (1.2%) |
| case | 2 |
| harmful misses | 95 (about two per paragraph) |

- Right: the regular Dano-Norwegian respellings (*mig*, *hvad*, *gik*, hard consonants,
  doubled consonants, *-ede* → *-et*, *aa*, *æ*, *øi*), *I* → *dere* with plural verbs,
  homographs such as *Kunde* (customer) left alone.
- Wrong: *forat* → *for at* where an infinitive follows (should be *for å*), 4 of the 11;
  single wrong forms (*nøklehullet*, *vallonerne*); book titles modernised in some places
  and not others.
- Left: much more of an author's own spelling than in the corpus (Hamsun's and Ibsen's
  *gøre*, *gennem*, *åbne*, *Øjeblik*), because those forms were never audited and their
  rule chains are not trusted. This is the cost of "when in doubt, leave it".

On unseen text, then: about as safe, noticeably less complete. A survey and one audit
round over the new text's forms closes most of the gap.
