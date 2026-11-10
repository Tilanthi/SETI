# Euclid DR1 LRD selection — PRE-REGISTERED SPECIFICATION — DRAFT v0.9 (SM-G)

**Status: DRAFT for Glenn's sign-off — NOT FROZEN.** Written 2026-11-10/11 by SM-G from the Q1 object-level reconciliation in
[`/workspace/LRD/reports/SMOKE_G_MEMBERSHIP.md`](/workspace/LRD/reports/SMOKE_G_MEMBERSHIP.md). Freeze procedure in §13.
Items marked **[OPEN-Gn]** need Glenn's explicit decision; the text states the DEFAULT that runs if no decision is taken.
Everything in this file was fixed on Q1 (and on the published Bisigello et al. 2026, A&A 711 A24, Table D1) **before** DR1 opens;
nothing may be tuned on DR1. Any post-freeze change is a new version with a logged reason, and both versions are run and published.

## 0. Principles
1. **Two published selections, both run on every DR1 tile, both frozen here:**
   * **S-B25** — the fit-based selection of Bisigello et al. (2026) in the "no-IRAC" form (DR1 has no IRAC), implemented as reconciled
     on Q1 (§3–§4). This is the primary catalogue (Letters A and B, Paper C). Its one physics-vs-practice choice (Hα veto sense, OPEN-G2) is run both
     ways: `sel_B25` (primary, per G2) and `sel_B25_rev` / `sel_B25_txt`; `sel_B25_rev` is the published-list-compatible version.
   * **S-LCS** — the Letter-A companion **colour sample** (§6): an observed colour box that is the Kocevski et al. (2025) slope criteria
     translated into Euclid colours, plus compactness and a VIS size cut. Model-free, reproducible from the catalogue alone.
   Their overlap is quoted. Neither is tuned on DR1.
2. **The mid-IR is NOT used in either selection** (§8): WISE/IRAC are the test of Letter B. DR1 densities are therefore *upper limits* on
   the LRD density until the deep-field purity calibration (§8.2) is applied.
3. **Determinism**: the result for an object depends only on that object's catalogue row (§5). Shuffled input → bit-identical output.
4. **No visual inspection** in the main sample; automatic artefact rules (§7) and a random 5 % visual audit (DR1_PLAN §2 S6).
5. Every step is a named boolean column in the output, so any reader can recompute every variant listed in §4.

## 1. Inputs and column names
DR1 MER FINAL catalogue + PHZ catalogue (+ CLASS for flags). Names: pipeline name (FITS route) → HATS name
(`/workspace/LRD/code/dr1/hats_cols.py`, `core_map()`; `schema_diff.py` checks DR1 against it; exit 2 = refuse to run).

| quantity | pipeline column | HATS column |
|---|---|---|
| ID, position | `OBJECT_ID`, `RIGHT_ASCENSION`, `DECLINATION`, `TILE_ID` | `object_id`, `ra`, `dec`, `tileid` |
| band flux / error (21 bands: VIS, Y, J, H + 17 ground) | `FLUX_<B>_2FWHM_APER`, `FLUXERR_<B>_2FWHM_APER` | `mer_flux_<b>_2fwhm_aper`, `mer_fluxerr_<b>_2fwhm_aper` |
| band flag | `FLAG_<B>` (VIS, Y, J, H, NIR_STACK used) | `mer_flag_<b>` (null → 2147483647) |
| aperture→total | `FLUX_DETECTION_TOTAL`, `VIS_DET`, `FLUX_NIR_STACK_2FWHM_APER` | `mer_flux_detection_total`, `mer_vis_det`, `mer_flux_nir_stack_2fwhm_aper` |
| reliability | `DET_QUALITY_FLAG`, `SPURIOUS_FLAG`, `PHZ_CLASSIFICATION` | `mer_det_quality_flag`, `mer_spurious_flag`, `phz_phz_classification` |
| compactness | `MUMAX_MINUS_MAG` | `mer_mumax_minus_mag` |
| PHZ | `PHZ_MEDIAN`, `PHZ_MODE_1`, `PHZ_MODE_2` | `phz_phz_median`, `phz_phz_mode_1`, `phz_phz_mode_2` |
| Galactic E(B−V) | `GAL_EBV` | `mer_gal_ebv` |
| Gaia | `GAIA_ID`, `GAIA_MATCH_QUALITY` | `mer_gaia_id`, `mer_gaia_match_quality` |
| size / artefacts | `FWHM`, `SPURIOUS_PROB`, `DEBLENDED_FLAG`, `ELLIPTICITY` | `mer_fwhm`, `mer_spurious_prob`, `mer_deblended_flag`, `mer_ellipticity` |

Derived (ingest, exactly as Q1): `APCORR = FLUX_DETECTION_TOTAL / (VIS_DET==1 ? FLUX_VIS_2FWHM_APER : FLUX_NIR_STACK_2FWHM_APER)`
(NaN if the denominator ≤ 0). **Photometry used by every step** (Table 8 of the paper 10/10, re-confirmed object-by-object on D1):
`F_B = FLUX_B_2FWHM_APER × APCORR × 10^(0.4 k_B E(B−V))`, `E_B = FLUXERR_B_2FWHM_APER`
(**"P1"**: aperture→total AND Galactic extinction applied to the FLUX ONLY — the error stays the raw aperture error; G23, R_V = 3.1, band-averaged
`k_B` from `lrdlib/data/ext_g23.json`; NO PHZ zero points). `S/N_B = F_B / E_B`. Units µJy. **[OPEN-G8]** P1 is what the published list requires
(recall of the published list +7 % in EDF-F/S and +24 % in EDF-N; median |Δβ| in EDF-N 0.19 → 0.01); it inflates S/N by 10^(0.4 k_B E(B−V))
(g band: ×1.05 at E(B−V)=0.015, ×1.40 at 0.10; u ×1.54 at 0.10), so in DR1 Wide the effective depth depends on dust. DEFAULT P1 for S-B25; the physically
consistent "P0" (extinction on flux and error) is always run as well (`sel_B25_P0`), and all densities are also reported in E(B−V) bins.
**Consequence for the DR1 ingest pre-cut (must fix before release day):** the `lrd`/`lrd_compact` pre-cut counts bands with
F·max(APCORR,1)/σ > 2.9 WITHOUT the extinction factor, which is not a superset under P1 once 10^(0.4kE) > 1.034 (g band at E(B−V) > 0.010).
`NFILT_LOOSE` must use F·max(APCORR,1)·10^(0.4 k_B E(B−V))/σ > 2.9 (SM-B/PR-6). Q1 numbers here are therefore lower limits on recall
(6 published objects are absent from the Q1 pre-cut catalogue — plausibly this effect).

## 2. Per-object band registry (replaces the hard-wired Q1 field band sets)
Q1 code keyed the band list on the field (`lrdlib.bands.FIELD_BANDS`). DR1 Wide has different ground surveys per region (north: UNIONS
MegaCam u/r + Pan-STARRS i + HSC/WISHES g/z (+JPCAM g); south: DES DECam g/r/i/z) and overlaps. Rule:
* **B1 Candidate list** = VIS, Y, J, H + every ground band of the 17 in `hats_cols.EXT_BANDS` present in the DR1 schema. A NEW ground band
  reported by `schema_diff` is used only if lrdlib has its filter curve and G23 coefficient; otherwise it is excluded and logged (never silently).
* **B2 Availability is per object**: band B is available iff `FLUX_B` and `FLUXERR_B` are finite and `FLUXERR_B > 0` (ground-band `FLAG_B`
  values are NOT used — Q1 pinned). On Q1 this reproduces the field band sets exactly: every band outside a field's set is 0 % finite there
  (checked on the 3,335 published objects present in the pre-cut catalogue).
* **B3 Duplicates** (two available bands of the same filter class u/g/r/i/z for one object, e.g. DECam r and MegaCam r in an overlap):
  **[OPEN-G1]** DEFAULT = keep, per object and per class, the band with the **smaller FLUXERR_B** (the deeper measurement), ties broken by the
  fixed order DECam > HSC > MegaCam > Pan-STARRS > JPCAM > LSST; the other is set unavailable. Rationale: two measurements of the same
  spectral interval must not count twice toward "≥ 2 rest-UV bands". Alternative: use all. Q1 is unaffected (no duplicates in Q1).
* **B4 λ_eff** for the band-side classification and the fit: Table 1 of the paper for its 13 bands, SVO pivot for the others (lrdlib registry).
* **B5 Per-tile band set** (for completeness/depth modelling only, not for selection): bands available for ≥ 50 % of the tile's RELIABLE objects;
  written to `tile_bands.parquet` with the per-tile median 10σ depth of each band. (Implementation: PR-6 runner.)
* FIELD for DR1 = `WIDE` / `DEEP-<EDF>` from the tile-ID prefix (wide 102…, deep 101…), not from distance to the EDF centres.

## 3. S-B25: the fit-based selection (every step, in order)
All steps are AND-ed. Column names are those of the output catalogue (§11).

| step | name | exact definition | Q1 reading (task-1 evidence) |
|---|---|---|---|
| S0 | `reliable` | `DET_QUALITY_FLAG==0 ∧ SPURIOUS_FLAG==0 ∧ FLAG_{VIS,Y,J,H,NIR_STACK}==0 ∧ PHZ_CLASSIFICATION ∉ {1, null}` | reproduces Table-3 totals exactly (WP1, SM-B, SM-C) |
| S0b | `not_gaia_star` | §7.1 | 1 of 3,341 published objects has a MER Gaia match |
| S1 | `zphz_lt3` | `PHZ_MEDIAN < 3` | 2 published fail = IRAC-branch objects (z 3.08, 3.66) |
| S2 | `nfilt4` | ≥ 4 available bands with S/N > 3, of which ≥ 2 rest-UV and ≥ 2 rest-optical, where a detected band is rest-UV if 1216 Å < λ_eff/(1+z) < 3645 Å and rest-optical if λ_eff/(1+z) ≥ 3645 Å with **z = PHZ_MEDIAN** (the count precedes the fit, as in Table 3), knife-edge rule of §5.2 | **[OPEN-G9]** λ_eff side at z_PHZ: best F1 in F+S (+0.010 vs z_fit; removes 46 objects of which 9 published) and no knife edges; z_fit counting = variant `nfilt4_zfit`; Fig-1 "wholly" edges −0.06 F1 (rejected) |
| S3 | `vshape` | point-fit β_opt > 0 ∧ −2.8 < β_UV < −0.37 ∧ reddest-brightest (if the two longest-λ available bands both have S/N > 3, the longest must be brighter in f_ν) | POINT estimate (MC-median slopes lose 10–15 % of the published objects); reddest-brightest ON (off adds 25–28 % more objects, no published object gained) |
| S4 | `compact` | `MUMAX_MINUS_MAG < −2.6` | every published object passes |
| S5 | `halpha_txt` / `halpha_rev` | windows Y 0.44–0.85 (vs J), J 0.77–1.39 (vs H), H 1.31–2.09 (vs IRAC1: no redder band in DR1 → test skipped), using z_fit and F_B: **as written** pass if F(contaminated band) < F(next redward band); **reversed** pass if F(contaminated) > F(next); test skipped if either band unavailable | **[OPEN-G2]** the published list requires the REVERSED sense (§4); the written sense is the physical one; both columns always written, primary per G2 (DEFAULT as written, DR1_PLAN) |
| S6 | `chi2_lt100` | point-fit χ² < 100 | |
| S7 | `zfit_le21` | z_fit ≤ 2.1 | on the fitted z (z_PHZ ≤ 2.1 loses ~5 % of the published list) |
| — | flags | §7.2 automatic artefact flags (none is a cut) | `no_nb1` (our WP4 proxy V3, not in the paper's text) is F1-neutral in F+S (−0.005) → flag only **[OPEN-G10]** |

**The fit** (`lrdlib.fit`, deterministic version §5.1): continuous double power law in f_λ with break at 3645 Å (Eq. 1), zero model flux below
1216 Å (1+z), S/N < 3 → flux 0 ± 2σ, S/N ≥ 3 → error ⊕ 5 % of flux, z free within **[min(PHZ_MODE_1, PHZ_MODE_2, PHZ_MEDIAN), max(PHZ_MODE_1, PHZ_MODE_2, PHZ_MEDIAN)]** (missing mode 2 → mode 1; missing both → median),
grid (Δz 0.02, Δβ 0.2; β_UV ∈ [−6, 4],
β_opt ∈ [−4, 8]) + one 7×7×7 refinement + Levenberg–Marquardt (30 iterations, per-object convergence, **active-set z bound** `LRD_FIT_LM_ACTIVE=1`, **[OPEN-G7]**). Amplitude profiled analytically (≥ 0).
Uncertainties: 100 Monte-Carlo flux realisations N(F, E), per-object random stream seeded with |OBJECT_ID| (§5.1), run only for objects that
pass S0–S4 and S6–S7 (MC values are reported, never used for selection: MC-median slopes lose 10–15 % of the published list).
Objects without PHZ modes (both NaN): z free in [0, 10] (Q1: 3,871 of 2.24 M fitted objects in EDF-F).

## 4. Readings chosen on Q1 (task 1) — and what they buy
Metric: object-level recall R, precision P, F1 against D1, **in the IRAC-uncovered zone** (where the paper could not apply its IRAC veto, so its
no-IRAC list = selection without veto), F + S separately from N (EDF-N is anomalous, report §3). Full tables in the report §2.

| reading | adopted | evidence (published-list agreement; report §2) |
|---|---|---|
| photometry / S/N | P1: APCORR and Galactic extinction on the flux only | recall (no veto) 0.769 → 0.881; EDF-N β agreement 0.19 → 0.01 |
| z bounds | PHZ modes ∪ PHZ_MEDIAN | z ≤ 2.1 losses 121 → 8 (published z = PHZ_MEDIAN below both modes) |
| LM refinement | active-set z bound (defect fix) | β on 0.1-grid nodes 45 % → 10 %; recall +1–1.5 % in every field |
| band-side count | λ_eff side at z_PHZ | F+S F1 +0.010; zero knife-edge ties |
| slopes | point estimate + reddest-brightest | MC median −0.10 F1; no reddest-brightest −0.11 F1 |
| Hα+[N II] veto | reversed reproduces the list; as written is physical → OPEN-G2 | reversed removes 129 uncovered F+S objects (9 published); as-written removes 37 (15 published) |
| z cut | z_fit ≤ 2.1 | |
| IRAC (Q1 only) | unc-map errors, S/N > 3 in ch1 or ch2 | F1 covered zone F 0.56 / N 0.23 / S 0.68 vs ≤ 0.48 / 0.23 / 0.60 for the alternatives |

Adopted-set agreement (Q1): uncovered zone R 0.965 / 0.924 / 0.970, P 0.774 / 0.254 / 0.749, F1 0.859 / 0.399 / 0.845 (F/N/S); all zones, no veto,
recall 0.944 / 0.912 / 0.946 (3,128 of 3,341; of the 3,312 no-IRAC objects 94.4 %); with the Q1 IRAC veto (unc S/N>3) F1 F 0.737 / N 0.374 / S 0.740, overall R 0.861, P 0.432.
Pinned v2 chain for comparison: uncovered F1 0.811 / 0.366 / 0.796, recall (no veto) 0.769.
Each reading was chosen between alternatives the paper's text allows; no numeric threshold was moved.

## 5. Determinism and the knife-edge rule (both NEW relative to Q1 v1/v2; old behaviour kept behind flags)
### 5.1 Fit determinism (`lrdlib/fit.py`, `wp4/common.py`, `wp4/run_mc.py`)
* Each object's z grid has K_i = max(2, ⌈(z_hi − z_lo)/0.02⌉ + 1) points over its OWN bounds (objects grouped on the exact K_i). Before the fix K was
  the maximum over the object's fit chunk, so an object's grid depended on its chunk-mates (row order, nproc).
* Levenberg–Marquardt convergence is per object (an object is frozen once its damping exceeds 10⁶); a failed batched linear solve falls back to the
  same LAPACK solve per object.
* MC noise: per-object stream `numpy.random.default_rng([12345, |OBJECT_ID|])`, independent of chunking.
* `LRD_FIT_LEGACY=1` (or `legacy=True`) reproduces the pre-fix code bit-for-bit (verified). Shuffle test: §5.3.
### 5.2 Knife-edge tie rule (`lrdlib/uvopt.py classify(..., tie_tol, tie_rule)`)
The fit is attracted to redshifts where 3645 (1+z) equals a band's λ_eff (the model kinks there): on Q1 the fixed fit puts 3,531 / 9,814 / 9,550 (F/N/S)
fitted compact objects within r = |λ_eff / (3645(1+z_fit)) − 1| < 10⁻⁴ of a band (a smooth distribution predicts 88 / 251 / 237); the excess spans
r = 10⁻⁹…10⁻⁴ (LM precision). **TIE_TOL = 1e-4** (fixed from this pile-up, not from the published list). A tied band is counted
**[OPEN-G3] DEFAULT `neither`** UV nor optical (it constrains the normalisation at the kink, not either slope). With the adopted z_PHZ counting
there are **no** tied objects on Q1; with z_fit counting the rule flips 1–5 selected objects per field and no published object (`opt`/`uv`/`both`: same order).
### 5.3 Shuffle test
EDF-F, full WP4 chain (run_fit → run_select → run_mc), original order with 20 processes vs randomly permuted rows with 13 processes: fits
(2,239,102), all selection masks and MC (5,026 × 100) **bit-identical** with the fixed code; the legacy code changes 76,770 fits and 1,203 band-count
masks under the same test. The DR1 runner repeats this test on one DR1 tile set (shuffled) before the release-day run is accepted.

## 6. S-LCS: Letter-A companion colour sample (defined a priori)
**Box** (pure power law between band effective wavelengths ⇒ the Kocevski slope limits become colour limits; derived analytically and checked
with synthetic photometry of double-power-law tracks through the filter curves, `release/spec_support/colour_tracks.csv`):
* C1 rest-optical red: `JE − HE > 2.5·2·log10(λ_H/λ_J) = 0.552` (⇔ β_opt > 0 between J and H; J and H wholly redward of the break for z < 2.08).
* C2 rest-UV blue: `2.5·(−0.8)·log10(λ_VIS/λ_g) < g − IE < 2.5·1.63·log10(λ_VIS/λ_g)` (⇔ −2.8 < β_UV < −0.37 between g and VIS): DECam g
  −0.359 … 0.731; HSC g −0.346 … 0.705 (g = the per-object g band of §2 B3).
* S/N > 3 in g, VIS, J and H; `compact` (S4); `not_gaia_star` (§7.1); VIS size cut (below); no z requirement (PHZ_MEDIAN < 3 reported as a flag).
* Track check: double power laws with β_UV ∈ [−2.6, −0.5], β_opt ∈ [0.05, 2] at z = 1.2–2.4 satisfy C1 and C2 (J−H 0.58–1.12; g−IE −0.24…0.68);
  at z ≈ 1.0 the flattest-UV/reddest-optical tracks leave C2 (VIS straddles the break); for z > 2.6 J straddles the break and C1 fails.
  Contaminant loci: single power laws β ≤ −0.5 (QSO-like, normal SF) fail C1 (J−H ≤ 0.42) unless Hα+[N II] with rest EW ≳ 500 Å sits in H
  (z 1.5–2.1: J−H up to 0.55 — **known residual contaminant**, quantified by the line-emitter flag §7.2 A4); red power laws β ≥ 0.5 fail C2
  (g−IE ≥ 1.07); M/L/T dwarfs fail C2 (no g flux) and are removed by §7.1.
* **VIS size cut [OPEN-G4]:** `R_FWHM = FWHM / FWHM_PSF(tile)` with FWHM_PSF(tile) = median MER `FWHM` of Gaia-matched sources with 19 < IE < 21 in
  the tile (≥ 5 such sources; else the neighbouring tiles). Keep if `R_FWHM ≤ R_star,97.5(IE)`, the 97.5th percentile of R_FWHM of stars
  (`PHZ_CLASSIFICATION == 1`) in the same 0.5-mag IE bin over the whole release — a property of the PSF and the noise, computed on DR1 itself
  before any LRD is looked at, not tuned on LRDs. Q1 facts: published candidates have R_FWHM median 0.98–1.00, 95 % ≤ 1.05–1.06 (unresolved, as JWST
  LRDs with r_e ≲ 100 pc ≈ 0.012″ must be); the compact cut alone already gives R_FWHM ≤ 1.2 for 99.7–100 % of compact objects, so a fixed 1.2 would
  be inert. The star-locus percentile could not be computed on Q1 by the deadline (the HATS pre-cut contains reliable, i.e. non-star, rows only),
  and the GOODS-S/JWST calibration (EDF-F ∩ JWST) was not available: **stated**; both are done on release day before the LCS is built.
* **Q1 result of the frozen box** (task-1 universe): 1,252 / 2,885 / 2,990 objects (F/N/S); it keeps only 5–7 % of the published B25 list: the published candidates have median
  observed J−H = 0.28–0.34 (β ≈ −0.9) although their fitted β_opt ≈ 0.4 — their V comes from a large IE−Y jump (median 1.1 mag) absorbed by the
  continuous double power law. **This is a physics result for Letter A, not a defect of the box (ESCALATED, report §6).**

## 7. Stars and artefacts
### 7.1 Gaia star rejection (`not_gaia_star`)
Reject if (a) the MER row has `GAIA_ID > 0` and the matched Gaia DR3 source has parallax/σ > 5 or total proper motion/σ > 5 (5σ either), or
(b) PR-2's pre-staged Gaia DR3 (`/srv/LRD/prestage/cat/gaia*`, epoch-propagated to 2016.0 → MER epoch) has such a source within 0.5″.
Sources with a Gaia match but no significant astrometry are KEPT and flagged `gaia_match` (compact AGN are Gaia sources). Q1: 1 of 3,341 published
objects has a MER Gaia match (EDF-S, GAIA_MATCH_QUALITY 0.001). Brown dwarfs: flag `bd_locus` = S/N(g) < 3 ∧ S/N(r) < 3 ∧ IE − YE > 1.5 (reported,
not a cut: the ≥ 2 rest-UV detections of S2 are expected to exclude them; the flag measures it). **[OPEN-G5]** confirm 5σ / 0.5″.
### 7.2 Automatic artefact rules (replace the paper's visual inspection)
* A1 `no_nb1`: no other MER object within 1.0″ (flag; WP4 proxy V3; F1-neutral on Q1, so not a cut — OPEN-G10).
* A2 `spurious_prob_gt01`: `SPURIOUS_PROB > 0.1` (flag; Q1 uncovered zone: 0.6 % of published vs 4–6 % of our extras).
* A3 `nb2`: any MER neighbour within 2″ (flag; 18–26 % of published vs 48–52 % of our extras — a cut would be a numeric threshold tuned to the list,
  so it is NOT adopted).
* A4 `line_emitter`: the AS-WRITTEN Hα+[N II] test fails (flag, both senses always written: `halpha_txt`, `halpha_rev`).
* A5 cutout-based V1 (coverage < 0.98 or bad centre pixels in VIS/Y/J/H 6″ cutouts) and V2 (NISP extent > 1.5 PSF at S/N > 5): computed only for
  the final sample (range-read cutouts), flags.
* Random 5 % visual audit of the final S-B25 and S-LCS samples (fixed seed 20261112 on OBJECT_ID hash).

## 8. Mid-IR policy
### 8.1 Not in the selection
No WISE/IRAC step in S-B25 or S-LCS. The paper's no-IRAC branch had "IRAC-undetected"; in DR1 Wide there is no IRAC and unWISE is ~3 mag shallower
with a 6″ PSF. Every DR1 density, number count and LF is published **without** a mid-IR veto and labelled an **upper limit** to the LRD
(V-shaped, compact) population. WISE measurements (forced photometry, PR-4/SM-E engine) are the Letter-B test, measured identically on the
controls (DR1_PLAN §2).
### 8.2 Purity calibration in the IRAC-covered deep fields
In the DR1 deep fields with Cosmic-DAWN IRAC (and in Q1 now), the same selection is run and each candidate's IRAC S/N is measured
(WP2/SM-C aperture photometry, point-source aperture correction 2.21/2.08, **unc-map errors** — the reading that reproduces the paper, §4;
empirical errors reported). Purity factor f_IRAC(H mag, z_fit) = N(IRAC-undetected at S/N ≤ 3 in both channels) / N(all, IRAC-covered).
Q1 values from this reconciliation: of our selected objects inside IRAC coverage, F 237 / 2,140 = 0.11, N 511 / 3,418 = 0.15 and S 1,616 / 4,788 = 0.34
survive the unc-map S/N > 3 veto (published covered-zone objects: F 171, N 137, S 1,198). The field-to-field spread (×3) shows f_IRAC must be measured
per depth/region, not transferred as one number. The Wide densities may be multiplied by f_IRAC only as a labelled, model-dependent estimate.

## 9. Sample tiers
* **T1 photometric**: S-B25 (and separately S-LCS) as above.
* **T2 spectroscopically supported**: T1 objects with a DR1 SPE redshift (SPE_Z within ±0.1(1+z_fit) of z_fit and `z_spe_error_flag == 0`,
  SPE class GALAXY or QSO with probability ≥ 0.5) OR an external spectroscopic redshift (PR-2 pre-staged: DESI/SDSS/6dF/2dF/OzDES, matched ≤ 1″)
  OR a broad Balmer line in SPE (Hα FWHM > 1000 km s⁻¹ at S/N > 5). **[OPEN-G6]** thresholds.
* **T3 benchmarks**: JWST-confirmed LRDs and spectroscopic AGN from the PR-2 benchmark lists (`/workspace/LRD/results/prestage/bench/`) that fall in
  DR1 (any tier membership reported; used for recall, never for selection).

## 10. What is NOT reproduced (residuals carried into the papers)
* Visual inspection of the paper (it kept 76–79 % of its pre-visual no-IRAC objects): our Q1 uncovered-zone precision 0.75–0.77 = that fraction.
  The DR1 sample without visual inspection therefore contains ~25 % objects the paper's eyes would have removed (blends, artefacts) — measured
  by the 5 % audit.
* EDF-N: published density in the uncovered half ~3.6× below ours; published objects are u-bright in our photometry → u-band photometry difference
  (report §3). Relevant for DR1 Wide North (UNIONS u).
* Fit details at the slope boundaries (v-shape losses 6/60/38 of the published list) and few-band objects at S/N ≈ 3 (nfilt 11/14/40).
* The published fitted β_opt > 0 is mostly driven by the IE−Y jump (observed J−H median 0.3, i.e. β ≈ −0.9 over rest 5000–6600 Å): S-B25 and S-LCS
  select largely different objects (the frozen LCS box contains ≈ 6 % of the published list on Q1).

## 11. Output columns
One row per object reaching S2 (stored) and counts for S0–S1 (maps): `OBJECT_ID, RA, DEC, TILE_ID, FIELD, every F_B/E_B, APCORR, z_fit, zlo, zhi,
beta_uv, beta_opt, chi2, A, MUV, n_det, n_uv, n_opt, n_tie, (MC: z/beta/MUV p16/p50/p84/std), and one boolean per step/flag:
reliable, not_gaia_star, gaia_match, zphz_lt3, nfilt4, vshape, compact, halpha_txt, halpha_rev, chi2_lt100, zfit_le21, no_nb1, spurious_prob_gt01,
nb2, bd_locus, knife_edge, lcs_box, lcs_size, sel_B25, sel_B25_txt, sel_B25_rev, sel_LCS, tier`, plus `SPEC_VERSION` and `SPEC_SHA256` in the metadata.

## 12. Open decisions for Glenn (summary)
| id | decision | DEFAULT if not decided |
|---|---|---|
| G1 | duplicate filter classes in overlaps (§2 B3) | keep the smaller-error band per class |
| **G2** | **Hα+[N II] veto sense for the PRIMARY S-B25** | **as written (DR1_PLAN v4/v5)**; the reversed sense (what the published list requires) runs as `sel_B25_rev` and is used for every Q1/B25 comparison |
| G3 | knife-edge tie rule | `neither`, TIE_TOL 1e-4 |
| G4 | VIS size cut for S-LCS | stellar-locus 97.5th percentile per 0.5-mag IE bin |
| G5 | Gaia rejection | 5σ parallax or proper motion, 0.5″ |
| G6 | T2 spectroscopic thresholds | as §9 |
| G7 | LM active-set fix (defect found here) | ON |
| **G8** | **photometry convention P1 (extinction on flux only)** | **P1** for S-B25; P0 always run; densities in E(B−V) bins |
| G9 | band-side count at z_PHZ (vs z_fit) | z_PHZ |
| G10 | MER neighbour < 1″ | flag only |
| G11 | S-LCS S/N threshold in g, VIS, J, H | 3 (alternative 5 for σ(J−H) ≤ 0.3) |
| G12 | EDF-N anomaly | accept as unexplained; report north/south separately in Letter A |

## 13. Freeze procedure
1. Glenn signs off the [OPEN] items (or accepts the defaults).
2. Parent sets `SPEC_VERSION 1.0`, removes DRAFT, writes `SELECTION_SPEC_v1.0.md`; `sha256sum SELECTION_SPEC_v1.0.md` and
   `tar --sort=name --mtime=@0 -cf - code/lrdlib code/wp4 code/dr1 | sha256sum` → `SPEC_HASHES.txt`; commit + push before Thu 12 Nov 11:00 UTC.
3. The DR1 runner (PR-6) refuses to run if the code hash differs from `SPEC_HASHES.txt` (override only with a logged new version).
