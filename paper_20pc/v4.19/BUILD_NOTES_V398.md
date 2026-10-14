# v3.99 — the ACA defect, repaired and verified

**Built 2026-09-24.** 43 pp. Gates: 0 errors, 0 undefined, 0 multiply-defined,
0 overfull, 0 misplaced labels; `roundcollide` 60/60, `prosenum` 0,
`macroleak` 0, `consistency` 0. Abstract 1913/1920. Clean regeneration
**83/83 byte-identical**.

## What changed

Referee 2 (M3) required the ACA control geometry to be re-extracted rather
than compensated for by argument. It has been.

**278 blocks / 739 GB re-fetched, re-calibrated and re-searched**, zero
failures, ~14.8 h on four lanes. The extractor now reads the dish diameter
from `ANTENNA::DISH_DIAMETER` and the longest baseline from `UVW`, so both
the primary beam and the synthesised beam are measured from the data, and
the annulus starts at `max(0.14 theta_PB, 2.0 theta_syn)`. The factor and
the success criterion were frozen in `ACA_REEXTRACTION_SPEC.md` before the
run.

### Primary test — PASSED

| ACA stellar ranks vs U(0,1) | D | p |
|---|---|---|
| before | 0.10 | < 0.001 |
| **after** (1067 windows) | **0.034** | **0.169** |

Criterion was p > 0.05. `acafix_v399.py` **asserts** it, so the build stops
rather than printing a claim the data no longer supports.

### Regression check — PASSED

Re-extracted 12 m windows reproduce their released statistics: 233 of 239
matched windows within 1 per cent, median fractional difference 6.4e-06.
The change is confined to the stratum it was aimed at.

### Three scientific consequences

1. **The positive control improves.** A beta Pictoris CO(2-1) window
   (T* = 9.8, -13 km/s) is recovered that the defective geometry had
   missed. A genuine repair should recover more of the control, and it does.
2. **Two unattributed events were artefacts.** HD 23484 and HD 14055 do not
   reach stage 1 once the controls are placed properly. Of the four the
   frozen catalogue lists, one survives among the ACA windows (61 Vir), and
   CP-72 2713 is a 12 m window and unaffected.
3. **M1 is discharged as a by-product**: every window now stores
   `star_peak_freq_GHz` and `star_peak_drift_Hz_s`, so each event has its
   own (nu, nu-dot) cell.

## The 68-window caveat — resolved, and it was mine

v3.97 flagged 68 ACA-labelled windows apparently still reporting a 12 m
beam. They were **stale duplicates in my export**, not a data problem: each
window appeared twice, once from a pre-patch product and once from the
corrected run. Restricting to the newest product per (eb, spw) under the
per-EB target directories gives a clean 1127 windows over all 278 blocks,
1067 at 7 m and 60 genuinely 12 m from crossing blocks. The extraction logs
confirm every ACA block was processed at 7 m with corrected radii.

**Lesson recorded: define the test population by the worklist, not by file
modification time.** A first pass also appeared to show the 12 m stratum
failing (p = 0.0000); that was the same contamination plus the fact that the
only 12 m blocks in scope are crossing-selected and therefore displaced by
construction.

## Text rewritten

- **Section 4.1** now describes a defect found, corrected and verified,
  rather than one to be argued around.
- **Section 6.4** retitled *The ACA control geometry, and what its repair
  changed*, and reports the repair's effects rather than carrying a caveat.
- **Conclusions** gain a numbered item: *A defect found, fixed and verified*.

## Still open

The released catalogue remains the frozen one computed under the original
geometry; the corrected numbers supersede its ACA dispositions and are
reported as the outcome of the repair. Fully re-deriving the frozen
catalogue and every downstream number from the corrected products is the
remaining engineering step, and it unlocks the last referee items: the
measured P90^sel through the rank gate (M3a), C_resp from the correlator
response (M3b), and the stellar-frame line-mask audit (R1-3), which now has
the crossing cells it needs.
