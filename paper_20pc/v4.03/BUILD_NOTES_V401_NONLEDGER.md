# Round-7 work that does NOT depend on the visibility refits

Done in `/workspace/SETI/paper_20pc/v4.01/` on 2026-09-25, after the parent run
handed the tree over. **The candidate chain was not touched**: `ledger_v401.py`,
`make_fig_ledger.py`, `visfit_r6_result.json`, `tab_ledger_v401.tex`,
`figures/ledger_vis.pdf` and §5.2.1 are exactly as they were.

Final state: **44 pp**, main text **16.53 pp**, appendices 26.7.
Gates 0 errors / 0 undef / 0 multdef / 0 overfull / 0 Type-3; roundcollide 70/70;
macrosyn 0; consistency 0; prosenum 0; macroleak 0; `audit_numbers` 49 PASS /
0 FAIL; reproducer 22 pass / 0 FAIL; **clean regeneration 101/101 byte-identical**.

---

## 1. The three frozen macro files are gone (R2-M2 headline)

`survey_numbers_round{5,6,7}.tex` were restored by `cp` from `frozen_macros/`
and no generator could rebuild them. **12 of their macros were typeset** (not 13
— `\PsFlagMu` had already been removed from the manuscript, so the diagnosis's
§17.5 is closed).

| macro | was | is | owner now |
|---|---|---|---|
| `\HdCorrectedT` / `\HdCorrectedRing` | 21.0 / 20.8 | **20.8 / 14.2** | `exfrozen_v401.py` |
| `\NonExcRingGe` | 16 | **38** | `exfrozen_v401.py` |
| `\NonExcRingMed` / `\NonExcHitMed` | 5.84 / 5.18 | 5.82 / 5.18 | `exfrozen_v401.py` |
| `\MaskBWTwenty` / `\MaskBWHundred` | 2.1 / 10 | **2.3 / 8.7** | `v361_calc.py` |
| `\DriftGridFineHalf` | 0.26 | 0.26 | `v343_calc.py` |
| `\KsFine` | 0.015 | **deleted**, use `\KsFineP` = 0.020 | `ksrank_v385.py` |
| `\OrbAccTrapb` / `\OrbAccTrapc` | 4.00 / 2.14 | 4.00 / 2.13 | `make_fig_accel2d.py` |
| `\HaystackFrac` | 6e-18 | same, with its source | `exfrozen_v401.py` |

★ **`\HdCorrectedT/Ring` = 21.0/20.8 is 27.10/1.29 and 26.83/1.29** — the
pre-repair T\* over the *pre-repair ring maximum*. Corrected, HD 48370 is
flagged by a wider margin (20.8 against 14.2), not a narrower one.

★ **The Appendix J ledger now closes and the generator asserts it**:
56 = 12 stage-1 (10 in mask, 2 not) + 6 in-mask unflagged + 38 other.

★ **Appendix I's mask ledger had four wrong literals**: AU Mic "+379" is
+373.5, LHS 1140 "+115" is +126.7, and HD 285968's "maximum 10.9 against a star
peak of 6.5" matches none of its three in-mask crossings (5.83–5.96 against
7.22–8.12). Replaced by a *bound* rather than examples: the closest of the 38
lies **127 km/s** from any masked transition, 2.5x the half-width, and 3 have no
such transition in the window at all.

## 2. Two new gates

**`macrosyn.py`** (in `make_all.sh`, so it fails the build, and in `gate.sh`):
11 declared macro GROUPS that must agree, 6 RELATIONS that must close, a SOURCES
check that fails on any macro file restored by `cp` or written by no `.py`, and a
DEFERRED list of 9 known divergences each naming its owner. Self-tested in both
directions. ★ `retire_macros.py` dropped `\MaskCrossInNoFlagN` the first time
because only the gate read it — it now imports `macrosyn.declared_macros()`.

**The figure pass of `audit_numbers_v385.py`**, promised in its docstring since
v3.85 and never written. Every star designation drawn in a typeset figure must
be in the released catalogue and in `star_alias.designation` form. It found 13
in Fig. 7 and 12 more in `tables/tab_perstar.tex`; root cause was
`make_figures_v328.tidy()` calling `display()`, whose guard
`not n.startswith('HD')` left `HD14055` untouched. It also reports 9 figures
built and never typeset — dead output that ships in the deposit.

## 3. Other M2 rows closed

- **Row 11 is an analysis fix, not a labelling one.** `acaverify_v399.py` ran
  the ACA rank-uniformity KS on the **raw export** (1,725 rows, 1,071 ACA),
  including the rows the catalogue drops as duplicated, noise-defective or
  withheld. Both exports are now cut to the catalogue **by multiplicity**.
  ACA n 1071 -> **1048**, 12 m 634 -> **601**; D = 0.032 (p = 0.23) after,
  0.103 (p < 0.001) before. 6 catalogue windows have no export row, stated.
- Row 12: Table 8's denominator (`\SepNWin` 1,648 = 597 + 1,051) is now in its
  caption, and the split is a macrosyn RELATION.
- Row 15: Fig. 6's "recovery falls away below f_dwell ~= 0.3", which no campaign
  measured, is replaced by the generated `\DwellFineT`/`\DwellCoarseT` pair.
- Row 16: the two Splatalogue passages merged; App. I states 75.1 % against
  4.1 % and "changes no disposition".
- §17.3: Fig. 13's caption said "Both depart from uniformity" and then quoted
  p = 0.932. Now says the fine class departs and the coarse does not.
- §17.1: **Table 23 is generated.** Its two control columns were identical in
  all seven rows because they are the same quantity; its "symmetric outcome"
  column is constant once the rows are defined as the symmetric-promoted pairs.
  Five rows, six columns, single-column. Table 24's hand-typed `T*` column,
  whose HD 48370 entry was the pre-repair 27.10, is deleted.
- RC-4 was **already fixed** by the parent in `v381_calc.py` and
  `occurrence_v399.py` before I started.

## 4. R1-9 / R2 Fig. 3 — worse than a wrong number

`\AccelShortPct` was `A_WORST/CEIL_MAX - 1` = 0.01 % while the caption said
"exceeds the **median** boundary by". There are two margins:
**+11 % against the default/median ceiling (3.60 m/s^2)** and **-0.01 % against
the widened grid (4.00) used on TRAPPIST-1's own 5 windows**. Both are published
and named for the ceiling they are measured against.
- The 5–29 % phase exclusion is the same pair of ceilings; the text now says
  which is which: **29 % above the default, 1 % above the widened**. It was 5 %
  only because `v363_inputs.py` used the **rounded** 13.3 Hz/s/GHz.
- ★ That calculation is **moved out of `v363_inputs.py`/`v363_calc.py` into
  `make_fig_accel2d.py`**, which owns both a_max and the ceilings. Hard-coding
  `AMAX = 4.00` *"the value the manuscript quotes"* is how the caption came to
  compare the planet against one ceiling under the other's name.
- Fig. 3's lower panel deleted (R2).

## 5. M9 — Mason et al.

2025, MNRAS 536, 2127, arXiv:2411.19827; authors Mason, Garrett, Wandia,
Siemion; **28 Gaia DR3 stars in the fields of 4 ALMA calibrators, Band 3**.
The "~361x lower" sentence is deleted. `masoncmp_v401.py` computes the
like-for-like comparison in minimum detectable **received flux**:

| | best | median |
|---|---|---|
| Mason et al., 30.52 kHz, bare 5 sigma | 3.8e-23 | 4.9e-23 W/m^2 |
| this survey, rescaled to 30.52 kHz, same 5 sigma convention | **5.2e-24** (9x deeper) | **7.1e-23** (1.4x shallower) |
| this survey at P90^sel (not like for like) | 2.9e-23 | 4.0e-22 |

★ The transcription is a **positive control**: the generator reproduces their
published 6.91e17 W for their closest star from their own distance, field rms
and channel width, to 0.3 %, and stops the build if it cannot.
Fig. 8 (and Fig. 1) now plot **P90^sel**; the "NOT a like-for-like sensitivity
axis" label is gone. Wright et al.'s haystack bounds cite **their §3.2.2**,
verified against the published text.

## 6. R2-m26 — the known-answer vectors are now RUN

`katcheck_v401.py` re-implements Eq. (3) importing nothing from the search or
injection code and runs the 4 shipped vectors: null reaches only T = 4.0 on the
grid, the drifting 5 sigma carrier returns 5.8 at its own trial against 1.0 at
zero drift, the off-grid drift returns 4.4 (24 % lower). ★ **The stationary
vector returns 3.3, not 5** — the injected cell carries one unit-variance noise
draw and this realisation's is 1.7 sigma low. Stated in the paper, because a
reader running them will otherwise think the pipeline is broken.

## 7. Length — 18.86 -> 16.53 pp, and where the rest is

Deletion of narration, not measurement: the two-normalisations narrative, the
boxed "authoritative normalisation" statement, "honest" (x3), "it is worth
putting that before any counting argument", "We describe the count as a marginal
excess", the superseded top-hat qualification, the worked HD 61005 budget
example, the duplicated polarisation paragraph, the "In three sentences"
conclusion, the eta_drift class-mismatch discussion (m12), the dangling
five-criterion sentences (m7), the gamma Lupi aside (m9). Table 1 cut from ~36
rows to ~20 (M7.6). Barnard's Star / Wolf 359 fixed per m15–m17.
Rank material moved wholesale into the false-alarm appendix, which is now the
single rank appendix: §6.4 + Table 8, §4.1's calibration second half, §5.2.2,
and the chance-expectation block from §5.2. `\ClustStagePobs` added to
`v352_calc.py` so App. J quotes **P(>=2) = 0.22** instead of P(>=1) = 0.59
(R2-M5.2); the two chance expectations are now explicitly labelled as the same
quantity with and without the x1.4 tail factor, and registered in macrosyn's
DEFERRED list.

★★★ **MEASURED, NOT ESTIMATED: the remaining 1.9 pp is Tables 4, 5 and 6.**
Deleting those three `table*` floats — the ones R2-M1.5 says merge into the
ledger — takes the main text from **16.53 to 14.60 pp** and the paper from 44 to
42 pages, i.e. **under the 15-page cap**. Reverted immediately; it is the
parent's to do with the ledger.

★ **Below about 16.4 pp, deleting main-text prose stops helping.** Removing
2,534 characters from §5.2 moved the main text *up*, 16.42 -> 16.83, because
five full-width floats in that section set the floor and prose reflows around
them. Measure after every pass.

## 8. Open, and deliberately not touched

- §4.1's paragraph beginning *"The visibility test was applied to the
  `\VxNTestedWin` windows the screen flagged rather than to all `\VxNCross`
  threshold crossings"* is **now false** — the ledger tests all 56 — and so is
  the cost estimate that follows it. It is candidate-chain text.
- The "one β Pictoris window is absent from this table… We do not claim it was
  tested" paragraph, same reason.
- The twelve "four"s for the unattributed count (R2-M2 row 2).
- The transfer bracket x0.64–1.04 vs x0.48–1.35 (R2-M3.3, needs the campaign).
- `\CampUnOneT` = 6.16 for 61 Vir, from the pre-repair `campaign_v372.json`
  (RC-3). That file is the **held-out calibration sample of 1,322 windows**; if
  it was scored pre-repair then its measured tail rate is pre-repair too, which
  is a larger question than a stale macro.
- The catalogue filename `per_target_results_v3.99.csv` against paper v4.01:
  left for the release step, per your instruction.
