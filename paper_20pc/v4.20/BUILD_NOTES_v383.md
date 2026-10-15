# BUILD NOTES — v3.83

Three rounds of internal review, a readability pass, and Figs 6, 9 and 10
resized. Findings and evidence in `REFEREE_ROUNDS_V383.md`.

## What changed in the science text

- Table 5 said every threshold crossing was Class A; 4 of 75 are Class B.
- The crossing ledger said the mask accounts for three stage-1 outliers;
  it accounts for nine.
- Fig. 2's decision-flow panel read "3 identified astrophysical; 1
  unexplained". The catalogue says 9 and 4. Hand-typed into the figure
  generator, stale since the catalogue grew, now generated.
- The abstract claimed every public observation "the archive holds"; 20
  blocks are offered as raw data with no pipeline calibration. Narrowed to
  "for which the archive holds a pipeline calibration".
- The abstract quoted only the deepest window's P90; the median is now
  beside it.
- The HD 48370 near-tie (27.10 against 26.83), the limiting case of the
  whole screen, was hand-typed. Generated.
- The full chain now appears in one place, in the Fig. 2 caption:
  1655 windows -> 75 crossings -> 13 stage-1 -> 9 CO -> 4 unattributed
  (3.2 expected) -> 0 candidates.

## Readability

The three densest main-text paragraphs rewritten: the radial evidence, the
transmitter benchmark, the beta Pic recurrence. Each now leads with what
the evidence shows and follows with the numbers. Nothing removed.
Main-text sentences over 400 characters: 44 -> 36.

## Figures

Figs 6, 9 and 10 were drawn on 302, 547 and 504 pt canvases and printed
into a single column at scales 0.58, 0.41 and 0.45. All three redrawn at
245 pt with type set for 1:1; Fig. 10's panels stacked, Fig. 9's legend
reduced to one column.

★ Fig. 10's canvas was hard-coded inside `fig_control_diagnostics`,
overriding `EXTRA_SIZES`, which is why the earlier sweep missed it. Check
for per-figure overrides before trusting a size table.

## Traps

★ **A forward dependency, caught only by the clean-regeneration test.**
`make_fig_funnel.py` now reads macros that `v381_calc.py` emits, so it has
to run after it. Incremental builds were fine; a clean regeneration failed
at 27/64. Second round running that this test has caught an ordering error.

★ **Nothing in this build checks a figure against its caption or against
the text.** Two rounds, two figures whose labelling disagreed with the
paper. The only method that works is extracting the text from each figure
PDF and reading it against the manuscript.

## Gates

32 pages, 0 errors / 0 undefined / 0 multiply-defined / 0 overfull /
0 Type 3, 850 macros 0 unused, abstract 1917/1920, clean regeneration
**64/64 byte-identical**, audit **56 pass 0 fail**, arXiv set clean.
