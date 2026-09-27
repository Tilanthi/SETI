# Three rounds of internal review — v3.83

Each round was run against the released catalogue and the compiled PDF, not
against an impression of the paper. Every finding below was checked before
it was acted on, and the numbers in the paper were changed at the generator
rather than in the text.

---

## Round 1 — does the paper's own arithmetic hold, and can a reader follow it?

Recomputed the detection chain from `per_target_results_v3.83.csv` and
compared it with every macro: 1655 windows → 75 crossings → 13 stage-1
outliers → 9 CO-attributed → 4 unattributed → 0 candidates. The macros
agree.

**Three defects found.**

1. **Table 5 said every threshold crossing was Class A.** It is not: 71 of
   75, i.e. 95 per cent, with 4 in Class B. The stage-1 row is still
   correct (13 of 13 are fine-channel). Both rows now carry the split
   explicitly.
2. **"three of those are accounted for by the mask"** in the crossing
   ledger. The mask accounts for nine. A stale literal from when the
   catalogue held four outliers.
3. **No single place gave the whole chain.** A reader had to assemble it
   from four sections. The decision-flow caption now carries it in one
   line, end to end.

A duplicated `\label{fig:funnel}` was removed while there.

---

## Round 2 — is any number in the prose hand-typed, and does the abstract
overstate?

Swept the main text for two-or-more-digit literals not matching any
generated macro value: 21 distinct, almost all legitimate (star
designations, cited values, physical constants).

**Three findings.**

1. **The HD 48370 near-tie, $T_\star=27.10$ against 26.83, was hand-typed.**
   It happens to be right, but it is the limiting case of the entire
   screening argument and it is exactly the pairing that has gone stale in
   this analysis before. Now generated, together with the margin.
2. **The abstract overstated the scope by a hair.** "Every public ALMA
   observation of a star within 40 pc that the archive holds" — 20 blocks
   are offered as raw data with no pipeline calibration and were not
   searched. Now: "every public ALMA observation ... for which the archive
   holds a pipeline calibration".
3. **The abstract quoted only the deepest window's sensitivity**, which
   invites a reader to treat it as the survey's. The median is now given
   beside it, $1.9\times10^{15}$ W against $4.5\times10^{13}$ W, and the
   spread is named as a result in itself.

---

## Round 3 — do the figures agree with the text?

Extracted the text from every figure PDF and compared it with the captions
and the body.

**One serious defect.** The decision-flow panel of Fig. 2 read **"3
identified astrophysical; 1 unexplained, non-repeating"**. The catalogue
says nine and four. Those two numbers were hand-typed into the figure
generator while every other number in the panel was read from a macro, and
they went stale the moment the catalogue grew. They are generated now.

This is the second figure in two rounds whose labelling disagreed with the
paper — the previous one was a caption promising ringed symbols that were
never drawn. **Nothing in the build checks a figure against its own caption
or against the text**, which is worth stating plainly as a limitation of an
otherwise thorough reproducibility chain.

---

## Readability pass

Scored every main-text paragraph by quantitative tokens per sentence and by
sentence length, and rewrote the three worst. No number, qualification or
citation was removed; the punctuation and the order changed.

- **The radial evidence** was one 1200-character chain of "First … Second …
  Third". Now three short paragraphs, each led by a sentence saying what
  that piece of evidence shows before the numbers arrive.
- **The transmitter benchmark** carried a derivation, a worked value, a
  caveat, a second benchmark, a scaling law and a statement about which
  power scale to use, in four sentences. Now two paragraphs, one per
  benchmark.
- **The $\beta$ Pictoris recurrence** argued frequency, velocity and line
  width in one paragraph. Now three labelled findings: *the frequencies
  agree*, *the velocities agree across two transitions and nine years*,
  *the lines are too wide to be carriers*.

Main-text sentences over 400 characters: 36, down from 44.

---

## Figures 6, 9 and 10

All three had the same defect as Fig. 7 last round: drawn on wide canvases
and printed into a single column, so their type rendered at 41–58 per cent
of the size it was set in.

| | canvas before | printed | scale before | scale now |
|---|---|---|---|---|
| Fig. 6 | 302 pt | 177 pt | 0.58 | **1.00** |
| Fig. 9 | 547 pt | 226 pt | 0.41 | **1.00** |
| Fig. 10 | 504 pt | 226 pt | 0.45 | **1.00** |

Each is redrawn on a 245 pt single-column canvas with type set for 1:1
printing. Figure 10's two panels are stacked rather than side by side —
across one column they would have been 120 pt each. Figure 9's legend was
reduced to one column and its planet labels moved, because at the narrower
width the old two-column legend overran the panel.

★ Figure 10's canvas was **hard-coded inside its own generator**,
overriding the registered size table, which is why it had escaped the
earlier sweep.

---

## Build state

32 pages · 0 errors, 0 undefined references, 0 multiply-defined, 0 overfull
boxes, 0 Type 3 fonts · 850 macros, 0 unused · abstract 1917 of 1920
characters · clean regeneration **64/64 byte-identical** · numerical audit
**56 pass, 0 fail** · em-dashes 0.

★ **A forward dependency, caught only by the clean regeneration.** Making
the funnel figure read the outlier-taxonomy macros meant it had to run
after the generator that emits them; incremental builds passed and a clean
regeneration failed at 27/64. This is the second round running in which
that test has caught an ordering error nothing else would have found.
