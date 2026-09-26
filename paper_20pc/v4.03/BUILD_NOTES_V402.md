# v4.02 — the non-ledger correction pass, published

Built 2026-09-26 from `v4.01/` by `cp -a`. This version exists to **publish
work that until now existed only in one container**: the round-7 non-ledger
corrections were completed in the local `v4.01/` folder on 2026-09-25, *after*
`v4.01` had already been pushed, so the remote `v4.01` and the local one
differ materially. One version number, one content state — hence a new number
rather than a second commit on `v4.01`
(`/workspace/SETI/referee_r7/DECISIONS_R7.md`, B1–B3).

Full description of the science and code changes carried here:
[`BUILD_NOTES_V401_NONLEDGER.md`](BUILD_NOTES_V401_NONLEDGER.md) (written
against the local v4.01 folder; every item in it is in this version).

---

## 1. What changed relative to the **pushed** v4.01

Everything in `BUILD_NOTES_V401_NONLEDGER.md`, in summary:

1. **The three frozen macro files are gone** (R2-M2 headline).
   `survey_numbers_round{5,6,7}.tex` were restored by `cp` from
   `frozen_macros/` and no generator could rebuild them; their headers name
   `frozen_export_v3.31.json` / `per_target_results_v3.32.csv`, an extraction
   two revisions before the ACA control-annulus repair, and **12 of their
   macros were still typeset**. All 12 are now computed from the released
   catalogue by `exfrozen_v401.py` (round 77), `v361_calc.py`, `v343_calc.py`
   and `make_fig_accel2d.py`. `\HdCorrectedT/Ring` 21.0/20.8 → **20.8/14.2**;
   `\NonExcRingGe` 16 → **38**; `\MaskBWTwenty/Hundred` 2.1/10 → **2.3/8.7**;
   `\KsFine` deleted in favour of `\KsFineP`.
2. **Two new gates.** `macrosyn.py` (11 macro GROUPS that must agree, 6
   RELATIONS that must close, a SOURCES check that fails on any macro file no
   `.py` writes, and a DEFERRED list of 9 known divergences each naming its
   owner) — it is in `make_all.sh`, so it fails the build. And the **figure
   pass of `audit_numbers_v385.py`**: every star designation drawn in a
   typeset figure must be in the released catalogue and in
   `star_alias.designation` form.
3. **Other R2-M2 rows closed** — the ACA rank-uniformity KS now runs on the
   export *cut to the catalogue by multiplicity* (ACA n 1071 → 1048, 12 m 634
   → 601; D = 0.032, p = 0.23); Table 8's denominator in its caption; the
   dwell threshold generated rather than asserted; Table 23 generated; Table
   24's hand-typed pre-repair `T*` column deleted.
4. **R1-9 / Fig. 3**: `\AccelShortPct` compared TRAPPIST-1 against one ceiling
   under the other's name. Both margins are now published and each is named
   for the ceiling it is measured against (+11 % against the default 3.60
   m s⁻², −0.01 % against the widened 4.00 used on TRAPPIST-1's own windows).
   The calculation moved into `make_fig_accel2d.py`, which owns both. Fig. 3's
   lower panel deleted.
5. **M9 — Mason et al. 2025** (MNRAS 536, 2127) redone like-for-like in
   minimum detectable *received flux* by `masoncmp_v401.py`, with their
   published 6.91e17 W reproduced from their own distance, field rms and
   channel width to 0.3 % as a positive control that stops the build if it
   fails. The "~361× lower" sentence is gone; Figs 1 and 8 plot P90^sel.
6. **R2-m26 — the known-answer vectors are RUN** (`katcheck_v401.py`), Eq. (3)
   re-implemented importing nothing from the search or injection code. The
   stationary vector returns 3.3, not 5, and the paper says why.
7. **Length: main text 18.86 → 16.53 pp** by deleting narration, not
   measurement.

## 2. What changed in v4.02 itself

**(a) Version bump.** `technosignatures_40pc_v4.01.{tex,pdf,aux,log,out}` and
`...v4.01Notes.bib` renamed to `v4.02`. Thirteen tools hard-code the
manuscript filename and were updated: `audit_numbers_v385.py`, `arxivset.sh`,
`gate.sh`, `floatsize.sh`, `abschars.py`, `inventory_v352.py`,
`macrosweep.py`, `measure.py`, `pagesplit.py`, `prosecount.py`,
`prosenum_v399.py`, `subrun5_check.py`, `widows.py`. Generator module names
(`cresp_v401.py`, `ledger_v401.py`, `katcheck_v401.py`, `masoncmp_v401.py`,
`exfrozen_v401.py`, `tab_ledger_v401.tex`, …) are **not** renamed: they name
the round in which the generator was written, not the manuscript. Historical
`# v4.01 (R2-M2): …` comments are likewise left alone — they are a record of
when a change was made.

**(b) Two paragraphs that the shipped ledger has already made false are
deleted** (DECISIONS_R7.md B4). A checkpoint is still a published artefact,
so these are removed rather than carried with a note:

- §4.1's paragraph beginning *"The visibility test was applied to the
  `\VxNTestedWin` windows the screen flagged rather than to all `\VxNCross`
  threshold crossings…"*, together with the cost estimate that follows it
  (`\VxNBlocks` blocks, `\VxTB` TB, `\VxHours` h). The ledger in §5.2.1 tests
  **all 56 crossings**, so the restriction and its cost are both false. The
  surviving sentence was reworded from *"Stage (iii) is worth its cost
  because…"* to *"Stage (iii) is worth the recalibration it requires
  because…"* so that it does not dangle on a cost estimate that is no longer
  there. Nothing else in the paragraph changed.
- The *"One β Pictoris window is absent from this table and should be
  accounted for … We do not claim it was tested"* paragraph, same reason.

**(c) Macros retired at the generator, not left dangling.** All seven macros
of `survey_numbers_round54.tex` (`visextend_v399.py`) — `\VxNCross`,
`\VxNTestedWin`, `\VxNUntestedWin`, `\VxNBlocks`, `\VxNEbHeld`, `\VxTB`,
`\VxHours` — became unreferenced and were dropped by `retire_macros.py`, which
runs last in `make_all.sh` and records the retirement in the file's header
comment. `visextend_v399.py` still runs and still computes them, so nothing is
lost and re-enabling one means citing it again. No generator and no gate reads
any of them (checked), so `macrosyn.py` and the reproducer are unaffected.
`\FixTBp` survives — it is used a second time in the false-alarm appendix.

**(d) Measured after deletion, as required.** §4.1 and §5.2 carry full-width
floats and prose deletion there can make the main text *longer*. It did not:
main text **16.53 → 16.03 pp**, appendices 26.7 → 26.19, total **44 → 43
pages**.

## 3. Gates — all clean

| gate | result |
|---|---|
| pdflatex errors | **0** |
| undefined references / citations | **0** |
| multiply-defined labels | **0** |
| Overfull boxes | **0** |
| Type-3 fonts | **0** |
| `roundcollide.py` | **70 round files, 70 inputs, 0 problems** |
| `macrosyn.py` | **0 problems** (11 groups, 6 relations, 76 macro files, 9 deferred) |
| `consistency_v399.py` | **0 problems** (frozen 12 = 10 + 2; corrected 11 = 10 + 1) |
| `prosenum_v399.py` | **0 literals disagreeing with a macro** |
| `macroleak.py` | **0 problems** |
| `audit_numbers_v385.py` | **49 PASS / 0 FAIL** (11 WARN, 7 SKIP — identical to v4.01) |
| `reproduce_from_catalogue_v385.py` | **22 pass / 0 FAIL**, 19 skipped |
| `xrefcheck.py` | 115 labels, 0 misplaced |
| **`cleanregen.py`** | **101/101 byte-identical** |

**Page split:** 43 pages total — main text **16.03 pp** (§1–Conclusions), back
matter 0.08, appendices **26.19**, bibliography 0.27. By the `\label`-anchored
count in `gate.sh`: appendix starts p. 17, so main 16 pp / appendix 27 pp.

**Abstract:** 1549 rendered characters, **243 words** (arXiv limit 1920,
headroom 371).

Underfull boxes: 53 (unchanged from v4.01; they are not a gate). `widows.py`
reports 4 short last lines, all pre-existing.

## 4. What is **NOT** in this version

This is the non-ledger pass. Deliberately absent, and landing in **v4.03**:

- **The round-7 refit ledger.** `ledger_v401.py`, `make_fig_ledger.py`,
  `tab_ledger_v401.tex`, `figures/ledger_vis.pdf` and §5.2.1 are **exactly as
  they were in v4.01**. The visibility-test ledger typeset here is the
  **superseded round-6 one** (44 of 56 crossings fitted, 12 localised, all 12
  attributed to CO, zero unattributed localised crossings).
- **The epoch convention change.** The refits decided by injection that
  `t0 = times[0]` — the search's own reference — is the correct one, and that
  the committed `median(TIME)` convention destroys narrow (unresolved) lines
  while sparing broad ones, are **not** in this version. Nor are the
  consequences: five crossings that change verdict under the corrected epoch,
  the η Crv crossing that localises under both conventions, or the withdrawal
  of round 6's rejections and of the three resolved-CO positive controls as
  validation of the estimator (DECISIONS_R7.md A1–A6).
- **The round-7 P90 campaign** (`p90_r7_result.json`, P90^sel re-measured
  through trigger → visibility localisation for Class A and B). The transfer
  bracket ×0.64–1.04 vs ×0.48–1.35 therefore remains an open macrosyn DEFERRED
  divergence.
- **The recurrence / block-versus-position results** for the epoch-corrected
  localisations.
- The twelve prose "four"s for the unattributed count (R2-M2 row 2).
- `\CampUnOneT` = 6.16 for 61 Vir, from the pre-repair `campaign_v372.json`
  (RC-3).
- The catalogue filename `per_target_results_v3.99.csv` against paper v4.02 —
  left for the release step.

## 5. Noticed in v4.02, out of scope, not changed

- **An appendix paragraph still describes the ACA control geometry defect as
  unrepaired, in the present tense.** Appendix "False-alarm accounting",
  §"Why no single window in this design can be significant": *"The control
  geometry uses a 12-m θ_PB for every window, so the `\NWinSevenM` ACA 7-m
  windows carry a known geometric error … Re-extracting the ACA windows on the
  correct 7 m beam would remove the error rather than bound it, and needs the
  raw visibilities and a full re-search."* The re-extraction **was done** —
  `acafix_v399.py`, 278 blocks, 739 GB, folded into the export at v3.99 — and
  the same appendix reports the after-repair KS (D = 0.032, p = 0.23) four
  hundred lines earlier. Appendix K's radial-gradient section reads the same
  way (*"The extraction code takes the primary beam from a fixed 12 m dish for
  every window"*). Either the passages are meant as a diagnosis of the
  original code and should say so in the past tense, or they are stale. This
  was already on the open list as R1-x laboratory-notebook voice; it needs
  someone who can confirm which ACA windows the released catalogue's control
  geometry actually uses, so it is flagged rather than guessed at.
- **`sec:acalimit` is now a label with no reference.** Deleting the β Pictoris
  paragraph removed its only `\ref`. `xrefcheck` "defined but never
  referenced" goes 21 → 22; it is a report, not a gate, and the list already
  contains `sec:intro`, `sec:background` and `sec:conclusions`. §6.3 should
  probably be cross-referenced from the array-split appendix when that
  paragraph is next touched.
- **Eight figures are built and never `\includegraphics`'d** (`completeness`,
  `completeness_sensitivity`, `cp72_control_distribution`, `eirp_context`,
  `noise_qa`, `occurrence_duty`, `selection`, `symcdf`) and ship in the
  deposit as dead output. Unchanged from v4.01.
- `tab_visibility_v384.tex`, `tab_visibility_v385.tex` and
  `tab_vispower_v400.tex` still write `HD14055` rather than `HD 14055`. They
  are not typeset, so the audit warns rather than fails. Unchanged from v4.01.
- The version folder carries `.aux`/`.log`/`.out`/`.pdf` from v3.87–v3.90 and
  a long tail of superseded `apply_v3xx_stage*.py` scripts. They are pushed
  with everything else. Harmless, but the deposit is larger than the paper.
