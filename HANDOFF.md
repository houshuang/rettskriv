# Handoff: final round (written 18 Oct 2026)

Goal: one last round with parallel agents, then stop. Close the best-known error classes,
add modern and parallel EPUBs, pass one large fresh acceptance check, swap, clean up, done.

## State

- Repo `~/src/rettskriv` (this one), HEAD 9ceaa96 or later, clean. README explains the engine
  and the lexicon pipeline; read it first.
- Live output: `out/site/<book>/<nnn>.html` (3,351 pages), swapped in 2026-10-18 14:52:45 UTC.
  Rollback copy `out/site.prev-20261018T145245Z`. Layers `out/modern/`.
- Measured: 9 meaning errors in 9,108 fresh changes (0.099%), samples `out/eval/accept-15/16`.
  602,189 of 1,909,182 words change.
- skard: the Original/Moderne switch is on skard main (679791077) and reads `out/site`. The last
  skard export is from 15 Oct, so the switch is not public yet. **The skard coordinator owns main,
  exports and deploys. Do not merge into skard, run an export or deploy.**
- Owner's rule: never change meaning; leaving a word as printed is always allowed. Bar for a
  swap: ≤ 0.14% meaning errors on fresh paragraphs, judged by Opus (`ACCEPTANCE-BRIEF.md`).

## Lanes (spawn in parallel; always pass the model)

Each agent works only on the files named for it; the coordinator (you) integrates, rebuilds and
judges. Use private scratch folders under `/private/tmp/claude-501/rettskriv-<lane>/`.

1. **Known errors (you, no agent).** Fix at cause, as curated rows (`lexicon/bokmal/core.csv`,
   `lexicon/nynorsk/context.csv`, conditional rows before unconditional ones) or engine rules,
   then `python3 tools/recheck.py accept-7 … accept-16` must show them fixed. Open list:
   *lidt* = suffered in *levet og lidt*; *at* as conjunction becoming *å* (accept-13 1924,
   accept-15 1378); imperative *sig* (*sig ikke det*, *sig din herre*); *bid → bit* (noun bitt);
   *andet Stokverk* (ordinal); *Kaldet* noun at sentence start; *lagad* (meta-text, accept).

2. **Homograph screen, tail (Opus, ~35 agents in waves of ≤ 20).**
   `tools/homograph_packets.py --min 2` (edit it to skip pairs already screened: ids differ, so
   filter on `from` against existing `out/audit/homograph/results/*`; write to a new folder, e.g.
   `out/audit/homograph-tail/`). Same `HOMOGRAPH-BRIEF.md`. This catches the remaining class of
   capitalised words that are also names or places (*Varer* = beacons, *Pen*, *Rum*, *Peisen*).
   Then `tools/homograph_ingest.py` reading both folders (make it glob both) → `homograph.csv`.
   Trap: the ingest once overwrote a results file through a reused loop variable; it is fixed,
   but diff the result folders before and after.

3. **EPUBs (one Sonnet agent).** New `tools/build_epub.py`, modelled on `tools/render_site.py`:
   monkeypatch `/Users/stian/src/bookifier/lesebok/scripts/build_epub.py` (`load`, `SITE`) the
   same way, never edit bookifier. Two outputs per book:
   - `out/epub/<book>-moderne.epub`: the modern text only.
   - `out/epub/<book>-parallell.epub`: each block printed, then its modern form beneath in a
     distinct style (smaller, muted; verse line by line), with a short title-page note naming
     the two layers.
   Both must pass epubcheck the way the Lesebok build does. Build beside and swap like the site
   (`out/epub.next` → `out/epub`; extend `tools/swap_site.py` with a folder argument rather than
   copying it). A skard link to these files is a coordinator task: write the request into the
   final report, do not edit skard.

4. **Acceptance (Opus, 16 agents).** After lanes 1–2 are in: rebuild beside
   (`build.py --out out/modern.next`, `render_site.py --layers out/modern.next --site
   out/site.next`), then draw **four** fresh samples with new names and seeds
   (`tools/sample.py --name accept-17 … accept-20 --seed rettskriv-final-1 … 4`; never reuse a
   name), `tools/split_sample.py <name>` for 4 parts each, one Opus reviewer per part with
   `ACCEPTANCE-BRIEF.md` (input `out/eval/parts/<name>-pN.md`, output `<name>-pN.review.tsv`).
   About 18,000 changes. `tools/accept_report.py accept-17 … accept-20` gives the rate and the
   error list and writes the files `tools/recheck.py` reads.

## Finish

- Pass (≤ 0.14%): `python3 tools/swap_site.py out/site.next`; swap EPUBs the same way; record the
  UTC time it prints. Do **not** change anything after the measured build.
- Fail: do not swap; report the rate and the error list. No further rounds: the owner said this
  is the last one.
- Commit rettskriv. Delete process state: `out/site.prev-*` except the newest, `out/modern.prev-*`,
  `out/eval/parts/`, `out/audit/*/` packets may stay (they are the audit evidence).
- Update memory `~/.claude/projects/-Users-stian-src-skard/memory/modern-spelling-rettskriv.md`.
- Final report to the owner (under 300 words): error rate with the four-sample total, words
  changed, swap time, EPUB paths and count, and the one-line skard request for the coordinator
  ("export picks up out/site; add EPUB links for out/epub/<book>-moderne.epub and -parallell.epub").
