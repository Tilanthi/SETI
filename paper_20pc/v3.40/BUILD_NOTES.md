# BUILD_NOTES — v3.40 (round 10)

Baseline: copy of v3.39 (tex + figures + survey_numbers* + scripts + frozen
export), version stamp bumped first, per the standing versioning rule. v3.39
and all earlier folders untouched.

**Round 10 is a science round, not a referee round.** It reads the v3.32 dwell
campaign at trial level for the first time and folds the result into the
completeness and occurrence statements.

## The freeze is unchanged, deliberately

Every number is still computed from `frozen_export_v3.31.json` — 431 windows,
88 stars, 82 systems. A refreshed export exists (2026-09-11T11:21Z, 490 rows /
459 windows / 91 stars / 85 systems, including the survey's first Band 10 data
and a searched ceiling moving 495 → 873 GHz), and it was **not** used, because
§1(iv) pre-registers the unprocessed datasets as the held-out confirmatory
sample. Merging them would dissolve that split. Swapping the freeze is a
one-line change (`SRC` in `survey_stats_round10.py`) if the authors decide
otherwise; it then requires re-running rounds 5–9 against the new freeze.

## Result

- `pdflatex` ×3: **0 errors, 0 undefined references/citations, 0
  multiply-defined labels, 0 overfull boxes, 0 underfull hboxes**.
- **39 pages — one over the standing 38-page ceiling.** The overflow is
  ~3.5 kB of Appendix Q text. One provably duplicated passage was cut to pay
  for part of the addition (the uniform-prior calculation, stated verbatim
  earlier in the same appendix, 369 chars). The remainder is deliberately left
  to v3.41, which is a commissioned trimming round (main text −10 %,
  appendices −25 %) and will restore and beat the ceiling; making hasty cuts
  now would pre-empt that review.
- **3 Type 3 fonts on page 6 — PRE-EXISTING, also present in v3.39's released
  PDF.** They are DejaVu glyphs (σ, →, ≥) inside `figures/pipeline_schematic.pdf`,
  which was not generated with `pdf.fonttype=42`. The BUILD_NOTES gate in v3.34–
  v3.39 reported "0 Type 3": **that gate was reporting false**, because it was
  applied to the manuscript's own fonts and not to glyphs inherited from an
  included figure. The generator for this schematic is not in the version
  folder, so it cannot be regenerated here. `gs -dNoOutputFonts` removes the
  Type 3 by converting text to outlines and was tested (visually identical at
  110 dpi, file 40 kB → 237 kB) but **not applied**: it introduces faint glyph
  artefacts and loses text selectability, which is an author's call.
  `pipeline_schematic.pdf` also carries ~12 hand-typed survey numbers, which
  will all be wrong if the freeze is ever swapped.

## Round-10 computation lane

Two scripts, deliberately split by role:

- `survey_stats_round10.py` — the v3.32 statistics engine pointed at the SAME
  frozen export, extended with (a) a measured two-class completeness curve and
  (b) a coarse-inclusive occurrence limit. **It reproduces every published
  number exactly** (431/88/82/118/313 windows-stars-systems-fine-coarse, union
  93.113 GHz, `\OccMeasured` 6.2 % over 59 systems, `\OccUnit` 3.6,
  `\OccUniform` 8.6, `\DutyHalf` 10.8) — that reproduction is the validation of
  the port, and `round10_calc.py` re-asserts five of those values and aborts if
  any has drifted.
- `round10_calc.py` → `survey_numbers_round10.tex` (21 macros, letter-only
  names: `Comp*`, `OccAll*`) and `tab_compcurve.tex` (panel (b) of the dwell
  table).

### What the dwell campaign actually measures

The trigger acts on the stacked statistic and the de-drift step is an
inverse-variance-weighted sum, so a carrier of per-integration amplitude `A`
present for dwell fraction `f_dwell` over `N_int` integrations accumulates to
`a = A·f_dwell·√N_int`. Binning the 3,888 released trials in `a` unifies the
amplitude and dwell axes and puts all 12 injected windows on one axis. Those
windows span `N_int` = 21–1314 (×63), 11 targets, Bands 3/6/7, both classes,
so configuration-independence becomes measurable:

- in the 6 windows whose grid straddles the trigger, the 50 % recovery point is
  at `a` = 5.3–8.3 (median 6.2) — i.e. at the 5σ threshold itself, not at a
  value set by channelisation, integration count or band;
- in the other 6 the weakest injection already stacks to `a` = 3.4 and ≥97 % of
  injections are recovered — consistent, but uninformative about position;
- the two classes' pooled curves agree within sampling noise and both saturate
  by `a` ≈ 8.

### What it does NOT license (checked, and it changed the arithmetic)

**The injected carriers do not drift.** The campaign therefore measures the
persistent/partial-dwell, *non-drifting* class. That is the searched class on
Class B (coarse) windows, where every in-grid drift is sub-channel over the
track — so Class B now has a survey-threshold completeness curve where it had
none. It is *not* the searched class on Class A (fine) windows, whose drifting
curve remains the single v3.28 calibration configuration with its unbounded
transfer error. The occurrence calculation therefore uses a **morphology-matched
mix**: the drifting curve on Class A windows, the dwell curve on Class B. An
earlier draft applied the dwell curve to both and gave 4.2 % over 82 systems;
the corrected, morphology-matched calculation gives **4.3 % over 81**.

### Occurrence, coarse-inclusive

At EIRP ≥1e16 W the measured form extends from the 59 fine-calibrated systems
to **81**, moving the demonstration number from **6.2 % to 4.3 %**
(7.4 % at p_epoch = 0.5, 34 % at 0.1; 9.1 % over 75 systems at 1e15 W,
3.6 % over 81 at 1e17 W). Still conditional on F_i = D_i = 1, still a pilot,
still secondary to the non-detection and threshold range.

## Prose changes

- Abstract: the "no completeness number is validated across more than one
  instrumental configuration / the coarse class has no completeness curve at
  all" clause is replaced by the measured multi-configuration statement. The
  single-configuration caveat is **retained** for the drifting class.
- §4.4: new Eq. (stacked amplitude), new paragraph on the measurement, new
  paragraph "What this does and does not license", panel (b) of Table (dwell).
  "The one unmeasured cell" → "The one cell measured only in part".
- Appendix Q: the pilot-number paragraph corrected (the dwell campaign *does*
  release trial-level records; the coarse class *does* now have a curve) and
  the coarse-inclusive limit stated.

## Fixed along the way

- `\CompFiftyN` was used where `\CompSatN` was meant. Both happen to equal 6,
  so the PDF was correct by coincidence and would have silently diverged on any
  re-run. Caught by an unused-macro sweep, not by reading.
- `\input` of bare rows from inside a `tabular` breaks booktabs
  ("Misplaced \noalign" at `\bottomrule`) whichever way the last row is
  terminated — verified both ways in a minimal test. Generated table fragments
  must carry their own `tabular`, and be `\input` outside one.
