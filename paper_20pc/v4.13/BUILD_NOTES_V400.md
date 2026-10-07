# v4.00 build notes — referee round 5

Built 2026-09-25. Submitted for a further round of external refereeing.

## Gate state
44 pp: main text 17.3, appendices 25.0, bibliography 0.3. `pdflatex`:
**0 errors, 0 undefined references or citations, 0 multiply-defined labels,
0 overfull boxes, 0 Type 3 fonts**. `prosenum` 0, `macroleak` 0,
`consistency_v399` 0, `roundcollide` 69/69, `xrefcheck` 0 misplaced labels,
`audit_numbers_v385` **49 PASS / 0 FAIL**, catalogue reproducer **0 FAIL**,
**clean regeneration 100/100 byte-identical**. Abstract 243 words,
1549/1920 rendered characters.

## The three results that change what the paper claims

### 1. P90^sel is now measured end to end, and it is four times worse
The previous figure came from a campaign that injected into retained
per-integration spectra *after* the baseline step and never passed through
the 512-control rank — a completeness for a statistic the survey does not
use. The replacement injects Hanning-convolved carriers at random
sub-channel phase and random drift into **calibrated visibilities** and
recovers them through the unmodified pipeline, trigger and rank together,
scoring one criterion: peak de-drifted statistic at the injected cell
above the trigger *and* above every control.

8,860 tones over 52 block–window configurations. Null rate **0 of 9,543**
cells on the uninjected passes; positive control **1.000**.

| | was | now |
|---|---|---|
| Class A P90 (trigger alone) | ×1.2 nominal trigger | **×3.0** |
| Class A P90^sel (trigger + rank) | modelled, ×3.2 | **×5.7 measured** |
| per-system median P90^sel | 1.5e15 W | **2.9e15 W** |

Two properties of the measurement are reported because they bound it.
Recovery **saturates below unity** — at the top rung the trigger fires for
every Class A tone and 94.5 % are recovered — because the injected source
leaks into the control ring through the dirty beam, lifting the control
maximum from 4.8σ to 8.8σ. And the Class A 90 % point lies near the end of
the measured ladder: in 26 % of unit-level bootstrap resamples it is not
reached at all.

### 2. The ACA control ensemble is worth 13 controls, not 512
Requiring every control–control and control–star pair to be at least two
synthesised beams apart leaves a median of 229 independent controls in the
12 m windows and **13** in the ACA windows. The honest rank resolution is
therefore 1/230 and **1/14**, the latter 37× coarser than the 1/513 the
paper had been quoting.

The separated screen is **more permissive, not less**: stage-1 goes 12 → 28,
sixteen gained and none lost. Fewer controls resolve less, so a window
clears them more easily. The ensemble that looks most significant is the one
with the least power, which is the clearest available statement of why the
rank is used to prioritise and never to establish.

Note for any reader repeating this: once N_ctrl ≈ 13 the add-one rank takes
about thirteen values, and a continuous Kolmogorov–Smirnov test manufactures
D = 0.052 from the quantisation alone. Dithered within each rank's own cell,
D = 0.027 (p = 0.18).

### 3. The visibility test's power is stated, not assumed
An event of statistic T⋆ in a window of trigger flux S_min = 5σ corresponds
to a flux T⋆S_min/5, and the fit reports its own flux uncertainty in the
same units, so a compact source at the stellar position would return
Re/σ = 5.6–6.0 at the unattributed events. The largest actually returned is
2.47. **Emission at the stellar position is excluded at 3.3–6.1σ.**
"Decisive" and "no point source" have been replaced by that bounded claim.

## Referee round 5: what was closed
All **28** of Referee 2's numbered corrections, plus **M2**, **M3(1)**,
**M4**, **M5** (power and wording), **M7**, **R1-6**, **R1-7**, **R1-8**,
**R1-12**, **R1-x**, and **R2-S2/S5/S7/S9/S10**.

Substantive rather than editorial among them:

- A **catalogue gap**: the disposition map had no entry for 61 Vir, so the
  released file shipped a blank disposition for one of the twelve flagged
  windows while the table printed one from a fallback. An assertion now
  fails the build if any flagged window lacks a disposition.
- A **circular generator dependency** that left the uncertainty table
  printing ±8 % while the text quoted ±9 % and omitted the term entirely.
- A **table row that disagreed with its own arithmetic** (β Pic B3
  topocentric velocity).
- A **funnel that was not nested** — it placed a vetting outcome above the
  attribution split, and the second set is not contained in the first.
- **"36 proposal codes"** when the blocks carry **63**; all are now listed,
  as ALMA policy requires, with the two that cannot be resolved named.
- The **drift-trial median of 4** was a Class B number; Class A searches a
  median of **81**, and all of the survey's residual smear loss is in
  Class A.
- The "defect found and repaired" narrative is gone, and removing it
  exposed a **factual error**: it stated the released catalogue was computed
  under the original control geometry, which stopped being true when the
  corrected export was folded in.

## Known open items, for the next round
- **R2-M6** — the two new figures. Panel A (dynamic spectrum with drift
  track) is feasible without re-fetching anything: 3,022 `*_srcspec.npz`
  survive, including all three stars named. Panel B needs the calibrated
  measurement sets, most of which the pipeline deletes after search.
- **R2-S1** — the GCNS census cross-match. VizieR returns zero rows for the
  GCNS tables through every endpoint reachable from this container and its
  TAP returns HTTP 400. The census denominator is unchanged and still
  labelled as a Gaia DR3 temperature-selected count; **no census number has
  been invented**.
- **R2-M5 residue** — delete the single-channel estimator entirely and
  redraw Fig. 8 from Table 6.
- **R2-S3, S4, S6, S8** and **R1-2, R1-3, R1-5, R1-9, R1-11**.
- **Compression**: main text is at 17.3 pp against the referee's ~12. The
  appendices have grown to 25.0 pp, partly because six floats were moved
  there; further main-text reduction by the same route would make that
  worse, so what remains is deletion of measurement.
- **Two execution blocks** have no recoverable ALMA project code and are
  named in the Acknowledgements; they should be looked up by hand before
  submission (`AUTHOR_ACTIONS.md`).
