# BUILD NOTES — v3.82: referee cycle on the completed survey

Built 2026-09-20. Two referee reports, 26 numbered points and a set of
minors, worked one at a time. Full point-by-point reply in
`REFEREE_RESPONSE_V382.md`.

## The two errors the referees found, and where they came from

Both are the same failure family this project keeps meeting: **a number
derived from a frozen input that a later round moved past.**

- **"a factor 16"** was the ratio of the per-window rank floor to the
  survey-wide Bonferroni scale. The scale was read from
  `survey_numbers_round5.tex`, frozen on a 410-window catalogue, while the
  ratio was printed beside "1655 windows". Recomputed from the current
  catalogue it is **65**. Now derived in `v350_calc.py` from the catalogue
  itself, with the scale, the window count and the ratio asserted to be one
  calculation.
- **75 against 77 reserved blocks** came from differencing two populations
  that were never the same. Now read from the hold-out assignment.
- **0.405 against 0.44** were two different samples under one name. The
  processing-order calibration set's median was still being quoted in the
  conclusions while the abstract quoted the pre-registered hold-out's.

★ **A forward dependency, caught only by the clean-regeneration test.** The
fix for the factor-16 error made `v350_calc.py` read a macro that
`v351_calc.py` writes. Everything built fine incrementally and a clean
regeneration failed at the first generator. The assertion now lives in
`v351`, where both values already exist.

## What is new in the paper

- `audit_numbers_v382.py`: 56 automated checks over every headline
  quantity, inside `make_all.sh`, failing the build on disagreement.
- Table: the four unattributed stage-1 outliers, one row each.
- Table: the CP$-$72 2713 repeat test, both blocks side by side.
- Figure: a schematic of the Hanning response correction — the same
  carrier at three offsets, the channel values each produces, and the
  resulting $\times2.00$–$\times2.67$ penalty.
- $P_{90}$ promoted above $P_{\rm eff}$ and $P_{\rm trig}$ everywhere.
- The molecular mask's cost reported per class (Class A 0.9 per cent,
  Class B 0.3), with an explicit statement that nothing is constrained
  inside the mask at any signal strength.
- A physical cause for the radial non-exchangeability, and its effect on
  the completeness side: $+0.08\sigma$ at the star, so recovery is
  **pessimistic** by ~2 per cent of the threshold.
- The pre-registration chronology, generated from repository timestamps
  with the ordering asserted.
- An illustrative haystack fraction, each axis separate, flagged as not a
  bound.

## Editorial

Every mention of previous versions, peer review and revision history is
gone: the paper reads as a first presentation. The statistic comparison
survives as a property of the estimator rather than as a narrative of a
change. Title now names the archive. The abstract states the archive-
complete scope and the total data volume in its first sentence.

De-AI pass: em-dashes 0, antithesis constructions 116 → 110, the
five-criterion decision tree converted from one sentence to a list, and
the longest main-text sentences broken up. No number or qualification was
removed to achieve it.

★ **A new figure shipped Type 3 fonts** because it was the one generator
not setting `pdf.fonttype 42`. The gate caught it. Worth remembering when
adding any figure to this build.

## Gates

32 pages · 0 errors / 0 undefined / 0 multiply-defined / 0 overfull / 0
Type 3 · 13 underfull (the narrow measure) · 846 macros, 0 unused ·
abstract 1842/1920 · clean regeneration **64/64 byte-identical** · audit
**56 pass, 0 fail** · arXiv set builds clean.
