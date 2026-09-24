# v3.99 — every downstream number regenerated from the corrected extraction

**Built 2026-09-24.** 43 pp. Gates: 0 errors, 0 undefined, 0 multiply-defined,
0 overfull, 0 misplaced labels; `roundcollide` 60/60, `prosenum` 0,
`macroleak` 0, `consistency` 0; `audit_numbers` PASS 49 / FAIL 0.
Clean regeneration **83/83 byte-identical**.

## What was done

v3.98 reported the repaired ACA extraction but left the released catalogue
on the original geometry. This version rebuilds the catalogue and every
number derived from it.

**The correct insertion point is the export, not the catalogue.** The first
attempt patched `per_target_results_*.csv` directly; `v342_calc.py` rewrites
that file from a single export on every build, so the patch was silently
discarded. Recorded here so it is not tried again. The chain is

```
apply_holdout  ->  frozen_export  ->  corrected_export_v399  ->  survey_stats
                                                             ->  v342_calc -> catalogue -> everything
```

`corrected_export_v399.py` merges the 1131 re-measured windows into the
export: stellar statistic, full 512-element control vector and its
summaries, noise and sensitivity columns, nearest-line association, and the
peak frequency and drift rate the original extraction did not retain.

Generators were split deliberately. Those computing the **result** now read
the corrected export; those **documenting the defect** (`acageom`,
`radial_null`) stay on the frozen export and say so in a comment, because
their job is to describe the pre-repair state.

## What changed

| | before | after |
|---|---|---|
| threshold crossings | 75 | **56** |
| stage-1 flagged | 13 | **12** |
| line-attributed | 9 | **10** |
| **unattributed** | **4** | **2** |
| windows with a retained crossing cell | 451 | **1401** |

Unchanged, as they must be: 1655 windows, 403 Class A, 90 stars, 82 systems,
404 blocks, and the headline sensitivity 1.5e15 W. The repair touched the
screen, not the thresholds.

The two events that disappear are HD 23484 and HD 14055, both ACA, both
artefacts of controls contaminated by the star's own synthesised beam. The
window that appears is beta Pictoris CO(2-1), attributed by the paper's own
+-50 km/s rule, so the line-attributed count rises to 10 while the
positive control strengthens.

## Four latent bugs the corrected data exposed

1. **`v342_calc` overwrote the catalogue** from the export, discarding a
   direct CSV patch. Fixed by moving the correction upstream.
2. **`apply_holdout_v381.py` WRITES the export.** A blanket repoint of
   "frozen_export -> corrected_export" redirected its output onto the
   corrected file, clobbering it. Only read sites should have moved.
3. **`EDGE.sort()` in `v343_calc`** sorted tuples containing dicts, so it
   crashed the moment two windows tied on edge fraction -- which they now do,
   because the repair retains a peak frequency for 1401 windows instead of
   451.
4. **A hard-coded frequency literal** identified the recurring beta Pic
   Band 6 window to 10 kHz. The repair re-measures that peak (it moved
   245 kHz), so the lookup now matches on proximity with a physical
   tolerance and fails loudly with an explanation if it cannot.

Three frozen constants that encoded the old result were made derived rather
than asserted: the unattributed count in `rfi_v399`, the stage-1 count in
`catalogue_constants.json` (regenerated: 13 -> 12), and the frozen
visibility-test event list, which now tolerates events the repair removed.

## Text

The Band 8 [C I] passage was removed: in the corrected extraction **no**
Band 8 window toward HD 48370 reaches the trigger, so the crossing it
described no longer exists. Stale counts in prose were replaced by the
generated macros; `prosenum` is clean.

## Still open

- **M3a**, P90^sel measured through the rank gate by injection, and **M3b**,
  C_resp from the correlator response, both need new injection runs.
- **R1-3**, the stellar-frame line-mask audit, is now unblocked: 1401 windows
  carry their crossing cell. It needs per-star systemic velocities, which are
  not in the catalogue.
