# BUILD NOTES — v3.96

Two referee reports, 26 recommendations, worked one at a time in the order
given, each finished before the next was started. Ledger:
`CHECKLIST_V396.md`. Response letter: `REFEREE_RESPONSE_V396.md`. Every
recommendation is closed; none declined.

## Gates

| gate | value |
|---|---|
| pages | 45 (main 27.6 / back 0.8 / appendices 16.3 / bib 0.3) |
| LaTeX errors | 0 |
| undefined references / citations | 0 |
| multiply-defined labels | 0 |
| overfull boxes | 0 |
| Type 3 fonts | 0 |
| underfull boxes | 32 (the narrow two-column measure) |
| macros defined / unused | 1107 / 0 (16 read by generators, protected) |
| abstract | 1917 rendered characters (arXiv limit 1920, headroom 3) |
| clean regeneration | **88/88 byte-identical, incl. 14/14 figures** |
| number audit | 49 pass, 0 fail, 7 skipped (macro retired) |
| catalogue self-sufficiency | 36 pass, 0 fail |
| round-file ownership (new) | 45/45, 0 collisions |
| cross-reference resolution (new) | 0 misplaced labels |
| arXiv set | 86 items, clean from an empty directory |
| em-dashes / antithesis | 67 / 184 (v3.86: 66 / 175) |

## The one change that alters what the paper claims

**Every false-alarm expectation the paper quoted answered the wrong
question, and fixing that both resolves the "modest excess" and dissolves
the reference-class argument.**

A stage-1 event requires two conditions: the stellar statistic must
outrank all 512 controls *and* reach the trigger. Every expectation in the
paper — 3.2, 3.1, 3.9, 4.4, 4.7, 1.1 — imposed only the first, so each
predicted *rank-first windows*, not *stage-1 events*. Comparing the 4
observed unattributed events against those figures was a category error.

`stageonenull_v396.py` imposes both conditions. The per-window
probability is `1/(N_ctrl+1)` if that window's control maximum reaches the
trigger and **zero otherwise**, block-resampled 20,000 times with the
measured ×1.4 tail factor:

    windows where a no-signal position can reach the trigger: 460 of 1614 (29%)
      of which Class A: 391
    Class A, x1.4 tail:  mean 1.07, 95% 0-4, P(>=4) = 0.0251

So: **4 observed against 1.07 expected, P(≥4) = 0.025**. The abstract,
§5.3 and the conclusions now say that instead of "a modest population
excess".

The second consequence was not anticipated. Because only 460 windows can
reach the trigger from noise at all, and **391 of those are Class A**, the
choice between the all-window and the Class A reference class — which the
manuscript had treated as an unresolved interpretive question, and which
Table `tab:chance` existed to display — is largely forced by the data.
That is why every stage-1 event in the survey is Class A. §5.3 says so and
`tab:chance` is deleted.

## Four defects found by building the referees' requests

1. **The false-alarm table's header did not match its body.** The row
   tuples emit (sample, windows, rate, predicts, expected, observed) and
   the header said "Expected & Obs. & Purpose", so the rendered table
   labelled the `predicts` column "Expected" and the expectation "Obs."
   Found by reading the rendered page. The loop variables are now named
   for their columns, which is how the mismatch arose.

2. **A printed subtraction did not close.** HD 48370's boxed summary gives
   T★ = 27.10 against a ring maximum of 26.83 and a margin of 0.28,
   because the margin was computed on the unrounded values
   (27.104 − 26.826 = 0.278). A reader checks the arithmetic on the page,
   so `v381_calc.py` now computes it from the rounded values: 0.27.

3. **The deepest repeat of the four unattributed events crosses the
   trigger.** T★ = 5.42 for HD 14055's repeat. It does not outrank its own
   controls and so does not reproduce a stage-1 event, which is what "none
   recurs" means here, but the bare claim was closer to the line than the
   manuscript admitted. Now stated in the table and its caption.

4. **Appendix G.10 was mistitled, duplicative-looking, and
   unreferenced.** Called "Validation material moved from the main text",
   with three starred subsubsections repeating the main text's titles
   verbatim. It is in fact the detail layer for §5.3.2, §5.3.3 and §5.3.5,
   carrying 104 generated macros that appear nowhere else — and nothing in
   the paper pointed at it. Retitled, its parts numbered and labelled, and
   each main-text summary now references its own appendix subsection.

Plus, from the cross-reference pass: `sec:vistest` and `app:table` both
**anchored on tables rather than sections**, because their `\label` sat
after a float. Both printed the right number by luck; both hyperlinked to
the wrong place. And `sec:benchmarks` shared an anchor with `sec:frames`,
so a reader sent to §4.3 for the Arecibo benchmark arrived at the velocity
frames instead.

## Two process defects, both now gated

**`survey_numbers_round47.tex` was silently overwritten.**
`occurrence_v396.py`, added for R2-2, wrote the file
`stageonenull_v396.py` owns. The build reported 0 errors and 0 undefined
control sequences, because the destroyed macros were still in the `.aux`
from the previous run. Nothing in `gate.sh` could see it; I found it only
by checking `grep -rln survey_numbers_round47 *.py` before trusting the
build.

New `roundcollide.py`, now in `gate.sh`, asserts that no two generators
write the same round file, that every round file the manuscript inputs has
exactly one writer, and that none is orphaned. It knows about
`frozen_macros/` for rounds 5–7, whose generators are retired.

**`retire_macros.py` did not know that generators read macros.** Three
v3.96 generators look their inputs up by name in the round files
(`V('BootMeanA')` and similar). Retirement commented out 13 of them as
unreferenced and **four rows of the new false-alarm table became `--`**.
Nothing caught it; I found it by re-running the generator after
retirement. `retire_macros.py` now scans the `.py` files for reader
patterns and protects what it finds — 16 macros this round, printed in its
report.

Both are the same failure as v3.61's stale 88.2 GHz literal and v3.62's
frozen-input arithmetic: one stage produces a value, another consumes it,
and nothing asserts the link. **The assertion is the defence, and it has
to be written at the moment the dependency is created.**

## New generators and tools

| file | purpose |
|---|---|
| `stageonenull_v396.py` | the correctly-conditioned stage-1 null (R1-1, R1-4) → round 47 |
| `falsealarm_v396.py` | one table of all seven expectations, with `predicts` (R1-1) → round 46 |
| `occurrence_v396.py` | CWTFM, Transmitter Rate, hosting fraction (R2-2) → round 48 |
| `rfi_v396.py` | three RFI vetting measurements (R2-3) → round 49 |
| `roundcollide.py` | gate: one writer per round file |
| `xrefcheck.py` | gate: cross-reference resolution (R2-t2) |
| `funnel_steps.tex` | the funnel's own step count, so caption and text agree (R2-m5) |

`occurrence_v396.py` cross-asserts its inputs against `NSysClassA`,
`UnionClassA` and `SysUnionAMed` as other generators publish them, so the
new metric cannot drift away from the rest of the paper.

## Ordering constraints in `make_all.sh`

Unchanged from v3.86, plus: `stageonenull_v396.py` **before**
`falsealarm_v396.py` (which reads its macros), and both before
`stagetable_v386.py`. `occurrence_v396.py` and `rfi_v396.py` read only the
catalogue and may run anywhere after it. `retire_macros.py` must still run
after every generator, and `macrosweep.py` after it.

## Author actions

Unchanged; see `AUTHOR_ACTIONS.md`. The White (2026) placeholder is no
longer a blocker for the text — the sentence citing it is now
self-contained and the bibliography entry carries no placeholder — but the
identifier should still be supplied if it becomes available.

---

## Post-push correction (same day), prompted by an author question

Glenn asked what §6.4 item (2) "Search the blocks already held" actually
means — whether an even more extensive search is possible from data we
already have. Checking it found three defects in the block accounting, all
now fixed and asserted.

**1. The block ledger did not close, and the assertion guarding it was
tautological.** §3 said "the execution-block accounting closes as follows"
and then printed 656 progenitor, 484 processed, 177 not processed. But
484 + 177 = 661, not 656. The assertion in `v381_calc.py` was

    catalogue + holdout + (processed - catalogue - holdout) == processed

which is true for any three numbers. It asserted nothing and could never
have caught this.

Recomputed from the progenitor lists, **two identities close exactly and
the paper had been mixing them**:

    656 progenitor = 479 searched in scope + 177 never searched
    484 processed  = 479 in scope + 5 with no recoverable member-OUS link

The 5 are named blocks whose progenitor link the archive does not expose;
3 of them are in the science sample. §3 now states both identities, says
the two counts must not be added to each other, and the real assertions
are in the build. The Introduction had also paired 656 with 404 (the
science sample) rather than 479 (searched in scope); fixed.

**2. §6 double-counted the uncalibrated blocks.** The remainder sentence
listed 77 hold-out, 20 no-calibration "and the rest duplicate coverage",
but the 20 are a *subset* of the 177 unsearched, as §3 says. Replaced with
the generated three-way split 656 = 401 + 78 + 177, asserted.

**3. Item (2) overstated what the held blocks buy, by a factor of about
two.** It said searching them "would make a multi-epoch survey of
\NStarMoreEB{} = 50 stars". `NStarMoreEB` counts stars whose available
blocks exceed those **in the science sample** — and 67 of the 202 "extra"
blocks have already been searched. They are the pre-registered hold-out,
withheld by design, not waiting to be processed. Like for like, the number
of stars with genuinely unsearched blocks is **29**, on **27 of 82
systems**, from **135** blocks.

Item (2) is rewritten to say what those blocks actually offer: every one
is repeat coverage of a star and tuning already searched, so they add no
star, no system and no frequency and extend only the time axis; they are
concentrated on Proxima Centauri, TRAPPIST-1 and HD 202628 rather than
spread; and of the 27 single-epoch systems, **only 5** would acquire a
second block, so they barely touch the confirmation gap that limits the
survey. The heading is also changed from "the blocks already held", which
reads as "already on disk", to "the remaining public blocks these stars
already hold".

New macros, all generated and asserted: `LedInScope` 479, `LedNoProgLink`
5, `LedSciInScope` 401, `LedHoldoutInScope` 78, `LedSciOutScope` 3,
`NStarUnsearchedEB` 29, `NSysUnsearchedEB` 27, `NExtraBlocksUnsearched`
135, `NExtraBlocksHeldOut` 67, `NSysOneEBGain` 5, `NSysOneEBNoGain` 22.

Gates after the correction: 46 pages, 0 errors / 0 undefined /
0 multiply-defined / 0 overfull / 0 Type 3, 1115 macros 0 unused, abstract
1917/1920, clean regeneration **88/88 byte-identical**, number audit
49/49, roundcollide 45/45, xrefcheck 0 misplaced.

**The lesson, and it is the third time this family has appeared in three
versions: an assertion that cannot fail is worse than no assertion, because
it advertises a check that is not being made.** v3.61 printed a stale
literal, v3.62 printed frozen-input arithmetic, and v3.96 printed a ledger
that does not close — each behind a guard that looked adequate.
