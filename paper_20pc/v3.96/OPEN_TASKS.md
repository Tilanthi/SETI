# SETI paper — open tasks

One authoritative list, version-independent. Per-version checklists
(`CHECKLIST_V3xx.md`) record what a given referee round closed; this file
records what is still outstanding. Current paper: **v3.96**, pushed
`003ddc82a19e`.

---

## 1. Visibility-domain localisation on all 75 threshold crossings
**Status: agreed with Glenn 2026-09-22. Highest priority. Queued behind
the archive-mining campaign.**

The referee's point is sound and it closes a real logical loop. As applied
in v3.96 the visibility test vets the output of a screen we have shown is
not exchangeable, rather than replacing that screen. Running it on all 75
crossings lets the candidate chain be stated as

> threshold crossing → visibility localisation → astrophysical
> identification → recurrence

with the 512-position statistic demoted to a background estimator.

### Specification, resolved 2026-09-22

| quantity | value |
|---|---|
| crossings total | 75 (13 already tested, **60 to do**) |
| blocks to re-fetch | **50**, **308 GB** — 7.5 % of the 4.1 TB, not a full re-download |
| frequencies and drift rates | **already known**: recoverable from the retained `_search.npz` (`best_src`, `best_drift`, `freqs`), so no re-search is needed, only re-calibration |
| old-cycle (≤2013) blocks | **6**, holding 6 crossing windows |
| expected legacy-replay failures | ~4 blocks, at the campaign's measured 67 % failure rate for that class |
| **realistically deliverable** | **~69–71 of 75 crossings, not all 75** |
| cost | **20–30 h** (the 15 h in the paper is the download+calibrate+**search** model; the visibility fit is a different final step) |
| vintage evidence | `visextend_vintage.json` (20 member OUS resolved by ALMA TAP on `member_ous_uid`) |

### Why it cannot be done from retained products
The visibility test is a phase test. We keep search products
(`_result.json`, `_search.npz`, `_srcspec.npz`) which contain extracted
spectra but no phase information, and the recalibrated measurement sets
were deleted in reclaiming 345 GB for the mining campaign — only four
survive (the unattributed candidates plus HD 48370). There is no shortcut.

### Commitment to make to the referee
Offer **~69–71 of 75**, naming the calibration-limited blocks, rather than
promising 75 and delivering fewer. The 6 old-cycle blocks should be listed
explicitly as unreachable-in-principle with the current calibration path,
which is the same class Glenn already ruled out pursuing (2026-09-22).

### Order of work
1. Wait for the mining campaign to drain (see the runbook).
2. Build the worklist from `visextend_worklist.json` (already written:
   60 windows, 50 blocks).
3. Re-fetch and recalibrate with the existing lane machinery, reserve ≥5×.
4. Run the v3.85 visibility fit at the frequencies and drifts from
   `_search.npz`.
5. Restructure §4.2/§5.2 and Figure 3 around the new chain; report the
   count actually achieved, not the count hoped for.

---

## 2. Injection-derived transfer scatter, as a figure
Referee request, still open. Plot $P_{90}^{\rm sel}/P_{\rm eff}$ against
channel width, observing band, integration time and array configuration,
to show there is no strong unmodelled trend inside the ×0.48–1.35 bracket.
If one variable dominates the scatter, parameterise on it instead of
carrying the whole range as an undifferentiated systematic.

## 3. Stratified end-to-end injection through the selection gate
Needs the pipeline host. Inject drifting carriers into a stratified subset
of Class A windows spanning band, channel width, integration length, array
and noise, and run them through the complete candidate selection including
the spatial gate, so that $P_{90}^{\rm sel}/P_{\rm eff}$ is measured
rather than transferred.

## 4. Per-hand polarisation on the 13 stage-1 windows
Needs the pipeline host. 198 of 200 resolvable blocks carry both parallel
hands; a per-hand search gains up to ×1.41 on a fully polarised carrier.

## 5. EIRP presentation order
Improved but not fully inverted: the referee asked for $P_{90}^{\rm sel}$
to be introduced *first*, with $P_{90}$, $P_{\rm eff}$ and $P_{\rm trig}$
following. Currently the convention is stated first and the hierarchy
still runs trigger-upward.

---

## Closed by decision, do not reopen
* **Legacy `scriptForCalibration` replay** — 11 old-cycle calibration
  failures are an accepted loss (Glenn, 2026-09-22).
* **Per-spectral-window calibration** for the one infeasible 67 GB η Crv
  block (Glenn, 2026-09-22).
* **Occurrence-rate interpretation** — removed at referee request; report
  only as an explicitly conditional survey-domain exclusion.

## Reachable population
174 unique blocks − 15 with no archive calibration − 11 legacy failures
− 1 infeasible = **about 148**. Any coverage statement must use that
denominator and must not imply the archive was exhausted.
