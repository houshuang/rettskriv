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
1.9 million words, of which 610,572 (32.0%) are changed in the current release.

| Rounds | Meaning errors among changes |
|---|---|
| 1–3 (first reviewer pool) | 0.50% → 0.25% → 0.14% |
| 4–8 (stricter reviewer pool) | about 0.19% → 0.156% → 0.142% → 0.124% → 0.099% (the last on 9,108 changes) |
| 9 (four samples, 16 reviewers) | 15 in 16,954 changes (0.088%) |
| 10, current (four samples, 16 reviewers) | **14 in 17,232 changes (0.081%)** |

Between rounds, every reported error was fixed at its cause (a lexicon row or an engine
rule) and replayed against all earlier samples with `tools/recheck.py`.

All categories, share of changes:

| Kind | Round 9 | Round 10 (current) |
|---|---|---|
| meaning | 15 (0.09%) | 14 (0.08%) |
| form | 80 (0.47%) | 126 (0.73%) |
| case | 23 (0.14%) | 39 (0.23%) |
| harmful misses | 129 (0.76 per 100 changes) | 130 (0.75 per 100 changes) |

Round 10 added about 120 context rows for two-reading forms (*tog*, *vare*, *have*, *ved*,
*vide*, *lade*, *taget* …; about 9,000 more words changed) and lowered genitive noun
capitals. The higher form and case counts come mostly from error classes the round did not
touch (old plural verbs, *-ede* participles, kept noun capitals) and are within what two
different samples and reviewer pools give; the miss rate per change did not move
measurably. Only one of round 10's 14 meaning errors comes from a new row (*at* = "so
that" read as the infinitive marker).

Before the four-sample check, round 10 had a targeted check: the old and new engines were
run over the whole corpus and 1,600 of the words whose output differed were judged on
their own ([`briefs/targeted.md`](briefs/targeted.md)). That check caught an attempt to
lower every kept capital, which turned names and old spellings into other words at about
1%; it was reverted before the release.

Round 10's meaning errors: *ved* → *vet* where it is the preposition (2); *lader*
(manners) → *lar* (2); *lade* (reload) → *la*; *voksede* (waxed) → *vokste*; *bøde*
(offered) → *bøte*; *træde* → *tre*; *besjelede* → *besjelte*; *at* (so that) → *å*;
*Kjødet* (the flesh, religious) → *kjøttet*; *baade* (boats) → *både*; *end høiere* →
*enn*; *kaldet* (the call) → *kalt*.

Round 9's 15 meaning errors:

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
