# Localisation criterion — committed before it is run

**Committed 2026-09-25, before the drift-following visibility fit was run on
any previously untested crossing.** This file is written first, deliberately,
so that the criterion cannot be adjusted after the results are seen. That
ordering is the whole point: the ±50 km s⁻¹ line-mask half-width was
criticised in an earlier round precisely because it was set after the
β Pictoris crossings had been inspected, and repeating that fault here would
be worse, because this criterion decides the candidate list itself.

## The criterion (Referee 2, round 6, §3 item 3)

A threshold crossing is **localised at the stellar position** when all three
of the following hold for the drift-following, continuum-subtracted
visibility fit evaluated at that window's own recorded crossing cell
(ν_cross, ν̇):

1. **Re/σ ≥ 4** at the stellar position;
2. **|Im/σ| < 3** — a source at the phase-rotated stellar position must
   leave the imaginary part at zero; a displaced source does not;
3. **Re/σ strictly greater than the maximum** returned by the same fit at
   the 8 annulus control positions and the 4 off-event control frequencies
   in the same window (12 controls in total).

A crossing that fails any of the three is **not localised**. A crossing that
cannot be fitted — no measurement set, no recovered drift rate, frequency
not in any window, insufficient rows — is recorded as **untestable** and is
never silently counted as either.

## Prior calibration, also fixed here

The false-alarm rate of this criterion will be measured **before** it is
applied to the science sample, on:

- the **77-block hold-out**, and
- the control positions and control frequencies of the already-fitted
  windows, which carry no event by construction.

If the measured false-alarm rate exceeds **1 per cent per crossing**, the
criterion is recorded as too loose and the fact is reported; the thresholds
above are **not** retuned to make the answer come out.

## What is deliberately *not* specified here

Nothing about the expected number of localised events, and nothing that
depends on which stars or windows are involved. The criterion is a function
of the fit output alone.

## Scope of the run it governs

41 previously untested crossing windows in 36 execution blocks (249 GB),
listed in `visfit_scope.json`. The 13 already-fitted windows are re-scored
under this same criterion, so that all 56 crossings are dispositioned by one
rule.

## Provenance

- Author: ASTRA PA, on Glenn J. White's instruction of 2026-09-25 to adopt
  Referee 2's design.
- This file is pushed to `Tilanthi/SETI` before the fits are run; its commit
  timestamp is the record.
