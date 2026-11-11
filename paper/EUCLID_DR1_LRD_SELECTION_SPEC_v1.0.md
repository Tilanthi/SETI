# Euclid DR1 LRD selection — PRE-REGISTERED SPECIFICATION v1.0 (FROZEN)

**Status: FROZEN** — v1.0 = draft v0.9 (SM-G, 2026-11-10/11) with Glenn J. White's decisions D1–D4 of 2026-11-11 ~10:40 UTC.
Everything here was fixed on Euclid Q1 and on the published Bisigello et al. (2026, A&A 711, A24) Table D1 **before** DR1 opens
(Thu 12 Nov 2026, 11:00 UTC); nothing may be tuned on DR1. A post-freeze change is a new version with a logged reason, and both versions are run
and published. Freeze record (code hashes, GitHub commit, UTC time): §13. Change log vs v0.9: §14. Evidence:
[`/workspace/LRD/reports/FREEZE_v1.0.md`](/workspace/LRD/reports/FREEZE_v1.0.md) (this freeze), `SMOKE_G_MEMBERSHIP.md` (Q1 readings),
`PR6_SELECTION_RUNNER.md` (runner), `SMOKE_H_HOTDUST.md` (Letter-B method), `SMOKE_F_GRISM.md` (grism criterion).
Implementation (hashed, §13): runner `code/release/selrun.py` + `selection_config_dr1.json` (every decision = one key in its `open` block),
ingest `code/dr1/ingest_hats.py` (and the FITS fallback `code/release/fits_fallback.py`), fit library `code/lrdlib`.

## 0. Principles
1. **Two named fit-based selections, both run on every DR1 object and both always written** (Glenn D1):
   * **PHYS** — *primary for our papers* (Letters A and B, Paper C). Honest S/N: every multiplicative flux correction (aperture→total APCORR and
     Galactic extinction) is applied to the flux **and** to its error alike, so every S/N equals the measured aperture S/N (§1, photometry "PHYS").
     Hα+[N II] veto **as written** in Bisigello et al. (§3 S5). Column `sel_PHYS`; catalogue `T1_candidates.parquet`.
   * **B25** — *Bisigello-compatible*, used for **every comparison with the published list**: the v0.9 readings that reproduce Table D1
     (photometry "P1" = corrections on the flux only; Hα veto **reversed**). Column `sel_B25`; catalogue `T1_B25_candidates.parquet`.
   * Also always written: `sel_PHYS_txt` (= `sel_PHYS`), `sel_PHYS_rev`, `sel_B25_txt`, `sel_B25_rev` (= `sel_B25`), `sel_B25_P0`
     (B25 steps, Hα as written, photometry P0), `sel_B25_rev_P0`.
   * **S-LCS** — the Letter-A companion **colour sample** (§6): Kocevski et al. (2025) slope limits translated into Euclid colours, compactness,
     and a VIS size cut against the stellar locus (Glenn D2). Model-free. Column `sel_LCS` (S/N per PHYS); `sel_LCS_B25` (S/N per P1) is a reference.
   Overlaps are quoted. None is tuned on DR1.
2. **The mid-IR is NOT used in any selection** (§8): WISE/IRAC are the test of Letter B. DR1 densities are therefore *upper limits* on the LRD
   density until the deep-field purity calibration (§8.2) is applied.
3. **Determinism**: the result for an object depends only on that object's catalogue row (§5). Shuffled input → bit-identical output.
4. **No visual inspection** in the main samples; automatic artefact flags (§7) and a random 5 % visual audit.
5. Every step is a named boolean column in the output, so any reader can recompute every variant listed here.

## 1. Inputs, column names and the three photometry conventions
DR1 MER FINAL catalogue + PHZ catalogue (+ CLASS for flags). Names: pipeline name (FITS route) → HATS name
(`code/dr1/hats_cols.py`, `core_map()`; `schema_diff.py` checks DR1 against it; exit 2 = refuse to run).

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
| Gaia | `GAIA_ID` (null = −99 HATS / 2⁶³−1 FITS), `GAIA_MATCH_QUALITY` | `mer_gaia_id`, `mer_gaia_match_quality` |
| size / artefacts | `SEMIMAJOR_AXIS`, `FWHM`, `POINT_LIKE_PROB`, `SPURIOUS_PROB`, `DEBLENDED_FLAG`, `ELLIPTICITY` | `mer_semimajor_axis`, `mer_fwhm`, `mer_point_like_prob`, … |

Derived at ingest (as Q1): `APCORR = FLUX_DETECTION_TOTAL / (VIS_DET==1 ? FLUX_VIS_2FWHM_APER : FLUX_NIR_STACK_2FWHM_APER)` (NaN if the denominator ≤ 0).
Galactic extinction factor `X_B = 10^(0.4 k_B E(B−V))`, G23, R_V = 3.1, band-averaged `k_B` from `lrdlib/data/ext_g23.json`. No PHZ zero points. Units µJy.

| convention | flux F_B | error E_B | S/N_B | used by |
|---|---|---|---|---|
| **PHYS** | `FLUX_APER × APCORR × X_B` | `FLUXERR_APER × APCORR × X_B` | `FLUX_APER / FLUXERR_APER` (measured aperture S/N) | **PHYS chain, S-LCS** |
| **P1** | `FLUX_APER × APCORR × X_B` | `FLUXERR_APER` | `FLUX_APER × APCORR × X_B / FLUXERR_APER` | **B25 chain**, `sel_LCS_B25` |
| P0 | `FLUX_APER × APCORR × X_B` | `FLUXERR_APER × X_B` | `FLUX_APER × APCORR / FLUXERR_APER` | `sel_B25_P0`, `sel_B25_rev_P0` |

The flux (hence every colour, slope and IE) is identical in the three conventions; they differ only in the error, i.e. in which bands count as
detections (S/N > 3), in the S/N < 3 → "0 ± 2σ" fit rule and in the fit weights. P1 is what the published list requires (SM-G: recall +7 % F/S,
+24 % N vs P0); it inflates S/N by APCORR·X_B. **Note (FREEZE E2):** APCORR < 1 for 32 % of compact Q1 objects (median 1.15), so PHYS S/N is
*not* always ≤ P1 S/N; the fit set is therefore every object with ≥ 4 detected bands under ANY of the three conventions (§3).
**Ingest pre-cut (superset of all three, proven on Q1 §4.3):** `NFILT_LOOSE` counts bands with `FLUX_APER × max(APCORR,1) × 10^(0.4 k_B max(E,0)) / FLUXERR_APER > 2.9`
(APCORR NaN → 1, E NaN → 0); row kept if `RELIABLE ∧ (NFILT_LOOSE ≥ 4 ∨ HMAG_LOOSE < 24.5)`; release-chain post-cut `MUMAX_MINUS_MAG < −2.4`.
Since `max(APCORR,1)·X_B ≥ max(1, APCORR·X_B, APCORR)`, the loose S/N bounds the PHYS, P1 and P0 S/N of every band.

## 2. Per-object band registry
* **B1 Candidate list** = VIS, Y, J, H + every ground band of the 17 in `hats_cols.EXT_BANDS` present in the DR1 schema. A NEW ground band reported
  by `schema_diff` is used only if lrdlib has its filter curve and G23 coefficient; otherwise excluded and logged (never silently).
* **B2 Availability per object**: band B available iff `FLUX_B` and `FLUXERR_B` finite and `FLUXERR_B > 0` (ground `FLAG_B` NOT used). On Q1 this
  reproduces the field band sets exactly.
* **B3 Duplicates (G1 = decided: smaller error)**: two available bands of one filter class (u/g/r/i/z) for one object → keep the band with the smaller
  `FLUXERR_B`; ties by DECam > HSC > MegaCam > Pan-STARRS > JPCAM > LSST; the other is unavailable. (Q1: no duplicates.)
* **B4 λ_eff**: Table 1 of the paper for its 13 bands, SVO pivot otherwise (lrdlib registry).
* **B5 Per-tile band set** (depth modelling only): bands available for ≥ 50 % of the tile's reliable objects → `tile_bands.parquet` (+ median 10σ depth).
* `FIELD_DR1` = `WIDE` / `DEEP-<EDF>` from the tile-ID prefix (wide 102…, deep 101…).

## 3. The fit-based selections (every step, in order; all AND-ed)
Steps are identical for PHYS and B25 except where marked; each step depends on the chain's photometry where it uses fluxes/errors.

| step | name | exact definition |
|---|---|---|
| S0 | `reliable` | `DET_QUALITY_FLAG==0 ∧ SPURIOUS_FLAG==0 ∧ FLAG_{VIS,Y,J,H,NIR_STACK}==0 ∧ PHZ_CLASSIFICATION ∉ {1, null}` |
| S0b | `not_gaia_star` | §7.1 |
| S1 | `zphz_lt3` | `PHZ_MEDIAN < 3` |
| S2 | `nfilt4` | ≥ 4 available bands with S/N > 3 (chain photometry), of which ≥ 2 rest-UV (1216 Å < λ_eff/(1+z) < 3645 Å) and ≥ 2 rest-optical (λ_eff/(1+z) ≥ 3645 Å) at **z = PHZ_MEDIAN** (G9 decided); knife-edge rule §5.2 (G3 decided) |
| S3 | `vshape` | point fit β_opt > 0 ∧ −2.8 < β_UV < −0.37 ∧ reddest-brightest (if the two longest-λ available bands both have S/N > 3, the longest is brighter in f_ν) |
| S4 | `compact` | `MUMAX_MINUS_MAG < −2.6` |
| S5 | `halpha_txt` (PHYS) / `halpha_rev` (B25) | windows Y 0.44–0.85 (vs J), J 0.77–1.39 (vs H), H 1.31–2.09 (no redder band in DR1 → skipped), z = z_fit, fluxes F_B: **as written** pass if F(contaminated) < F(next redward); **reversed** pass if F(contaminated) > F(next); skipped if either band unavailable. Both columns always written for both photometries. |
| S6 | `chi2_lt100` | point-fit χ² < 100 |
| S7 | `zfit_le21` | z_fit ≤ 2.1 |
| — | flags | §7.2 (none is a cut; `no_nb1` flag only, G10 decided) |

**Fit set**: reliable ∧ `compact` ∧ `zphz_lt3` (fit-independent, identical finals to fitting everything — proven on Q1) ∧ ≥ 4 bands with S/N > 3 under
at least one of PHYS/P1/P0. Each object is fitted once per photometry (PHYS → columns `*_PHYS`, P1 → unsuffixed, P0 → `*_P0`).
**The fit** (`lrdlib.fit`, deterministic §5.1): continuous double power law in f_λ with break at 3645 Å, zero model flux below 1216 Å (1+z), S/N < 3 →
flux 0 ± 2σ, S/N ≥ 3 → error ⊕ 5 % of flux, z free within [min(PHZ_MODE_1, PHZ_MODE_2, PHZ_MEDIAN), max(…)] (missing mode 2 → mode 1; missing both →
median; all NaN → [0, 10]), grid Δz 0.02, Δβ 0.2 (β_UV ∈ [−6, 4], β_opt ∈ [−4, 8]) + one 7×7×7 refinement + Levenberg–Marquardt (30 iterations,
per-object convergence, **active-set z bound ON**, G7 decided, `LRD_FIT_LM_ACTIVE=1`). Amplitude profiled analytically (≥ 0).
**Uncertainties**: 100 Monte-Carlo flux realisations N(F, E) with the chain's photometry, per-object stream seeded with |OBJECT_ID|, for the objects
passing every step except S5 (`PHYS_noHa` with PHYS → `T1_candidates_mc.parquet`; `B25_noHa` with P1 → `T1_B25_candidates_mc.parquet`). Reported, never used for selection.

## 4. Readings chosen on Q1 and what they give
### 4.1 B25 (reproduces the published list) — unchanged from v0.9
| reading | adopted | evidence (SM-G §2) |
|---|---|---|
| photometry / S/N | P1 | recall (no veto) 0.769 → 0.881; EDF-N β agreement 0.19 → 0.01 |
| z bounds | PHZ modes ∪ PHZ_MEDIAN | z ≤ 2.1 losses 121 → 8 |
| LM refinement | active-set z bound | β on grid nodes 45 % → 10 %; recall +1–1.5 % |
| band-side count | λ_eff side at z_PHZ | F+S F1 +0.010; zero knife-edge ties |
| slopes | point estimate + reddest-brightest | MC median −0.10 F1; no rb −0.11 F1 |
| Hα veto | reversed | reversed removes 129 uncovered F+S objects (9 published); as written 37 (15 published) |
| z cut | z_fit ≤ 2.1 | |

### 4.2 Q1 numbers of the frozen code (whole Q1, release store, no IRAC veto, no visual inspection; Table D1 matched by position ≤ 0.3″)
| field (published) | **sel_PHYS** n / recall / precision | **sel_B25** n / R / P | sel_B25_txt n / R | sel_B25_P0 n / R | sel_LCS (sized) n / R |
|---|---|---|---|---|---|
| EDF-F (430) | 2,340 / 0.472 / 0.087 | 2,464 / **0.944** / 0.165 | 2,732 / 0.937 | 2,490 / 0.842 | 1,117 / 0.035 |
| EDF-N (971) | 4,935 / 0.445 / 0.088 | 6,476 / **0.917** / 0.137 | 7,216 / 0.896 | 5,404 / 0.654 | 2,639 / 0.028 |
| EDF-S (1,940) | 5,561 / 0.475 / 0.166 | 5,752 / **0.947** / 0.320 | 6,281 / 0.947 | 5,697 / 0.877 | 2,831 / 0.026 |
| **all (3,341)** | **12,836** | **14,692** | 16,229 | 13,591 | 6,587 (pre-size 7,295) |
Also: `sel_PHYS_rev` 11,837; `PHYS_noHa` 12,980; `B25_noHa` 16,461; `sel_B25_rev_P0` 12,514; `sel_LCS_B25` 7,947 → sized 7,068; fitted 644,144 objects
(× 3 photometries; 109 s wall / 4,560 task-CPU s at 48 procs). MC100: PHYS_noHa 12,980 objects in 204 s, B25_noHa 16,461 in 219 s (48 procs).
S/N conventions verified object by object (5,000 random fitted objects: n_det under PHYS / P1 / P0 = the count recomputed from the raw columns, 0 mismatches).
The published list is a P1 selection with an IRAC veto and visual inspection, hence the low precisions (like-for-like uncovered-zone numbers: SM-G).
**PHYS keeps 47 % of the published list** (1,556 of 3,331 fitted published objects pass all PHYS steps; 1,504 fail S2 `nfilt4`: their 4th
detected band exists only through the S/N inflation by APCORR·X_B — P1 S/N > 3, aperture S/N < 3 — and 245 fail S3). This is the expected
consequence of D1 and a result for the papers, not a defect (FREEZE E2).
B25 numbers are identical to the v0.9 runner reference (16,229 / 14,692 / 16,461 / 13,591 / 12,514).

### 4.3 Pre-cut superset proof (both chains, Q1)
Store A = release pre-cut (1,522,173 rows after −2.4), store B = every RELIABLE ∧ MUMAX < −2.4 row (2,179,249 = the uncut catalogue for every selection,
since S0 and S4 are AND steps). Selection on A == selection on B: 644,144 = 644,144 fits, 0 differences in z/β_UV/β_opt/χ² for PHYS, P1 and P0,
0 mask mismatches, every `sel_*` identical (PHYS, PHYS_rev, B25, B25_txt, B25_P0, B25_rev_P0, LCS, LCS_B25). All 3,341 published objects are stored.

## 5. Determinism and the knife-edge rule
### 5.1 Fit determinism (`lrdlib/fit.py`)
Per-object z grid (K_i = max(2, ⌈(z_hi − z_lo)/0.02⌉ + 1) over the object's own bounds), per-object LM convergence (frozen once damping > 10⁶; failed batched
solve → per-object LAPACK), MC stream `default_rng([12345, |OBJECT_ID|])`. `LRD_FIT_LEGACY=1` reproduces the pre-fix code (the runner refuses it).
### 5.2 Knife-edge tie rule (G3 decided: `neither`, TIE_TOL = 1e-4)
A band with r = |λ_eff/(3645(1+z)) − 1| < 10⁻⁴ is counted neither UV nor optical. With the adopted z_PHZ counting there are no tied objects on Q1.
### 5.3 Shuffle test
Runner tasks, original vs randomly permuted rows (`selrun.py shuffle`): fits (all three photometries), every mask and chain membership **bit-identical**
on Q1 — the first 3 partitions (8,746 fitted objects) and the 2 largest (26,315 fitted objects), with the frozen code (FREEZE report).
The DR1 runner repeats it on 3 DR1 partitions before the release-day catalogue is accepted (`selrun.py shuffle`).

## 6. S-LCS: Letter-A companion colour sample
### 6.1 Box
* C1 rest-optical red: `JE − HE > 5·log10(λ_H/λ_J) = 0.552` (⇔ β_opt > 0 between J and H).
* C2 rest-UV blue: `2.5·(−0.8)·log10(λ_VIS/λ_g) < g − IE < 2.5·1.63·log10(λ_VIS/λ_g)` (⇔ −2.8 < β_UV < −0.37 between g and VIS), g = the per-object g band (§2 B3).
* **S/N > 3 in g, VIS, J and H** (G11 decided) with the **PHYS** errors (`sel_LCS`); the same box with P1 errors → `sel_LCS_B25` (reference; FREEZE E3).
* `compact` (S4), `not_gaia_star` (§7.1), VIS size cut (§6.3); no z requirement (PHZ_MEDIAN < 3 reported as a flag).
Track checks and contaminant loci as in v0.9 (`release/spec_support/colour_tracks.csv`): known residual contaminant = strong Hα+[N II] emitters in H at z 1.5–2.1.
### 6.2 Physics flag (unchanged)
The published B25 candidates have observed J−H median 0.28–0.34 although their fitted β_opt ≈ 0.4 (the V comes from the IE−Y jump); the box keeps only
3–4 % (pre-size; 2.6–3.5 % after the size cut) of the published list on Q1 (§4.2; `sel_LCS_B25` 5–6 %). S-B25/PHYS and S-LCS select largely different objects — a Letter-A result.
### 6.3 VIS size cut (Glenn D2; measure per FREEZE E1)
* **Star side-table at ingest** (`ingest_hats.star_sample`, also in the FITS fallback; taken BEFORE the row cut): every object with
  18 ≤ IE < 25 and (`GAIA_ID` valid ∨ `POINT_LIKE_PROB ≥ 0.5`), at most 60 per (ingest unit, tile, 0.5-mag IE bin), deterministic subset = lowest
  splitmix64(OBJECT_ID); columns OBJECT_ID, RA, DEC, TILE_ID, VIS_DET, FLAG_VIS, DET_QUALITY_FLAG, SPURIOUS_FLAG, PHZ_CLASSIFICATION, POINT_LIKE_PROB,
  FWHM, SEMIMAJOR_AXIS, ELLIPTICITY, MUMAX_MINUS_MAG, IE, STAR_GAIA, STAR_PLP. Written to `<ingest root>/stars/`. Q1: 0.39 M rows, ~40 MB → DR1 ≲ 1 GB.
  `IE = 23.9 − 2.5 log10(FLUX_VIS_2FWHM_APER × APCORR × X_VIS)` = the selection's F_VIS.
* **Stars used** = stored rows with `POINT_LIKE_PROB ≥ 0.5` ∧ `VIS_DET == 1` ∧ `FLAG_VIS == 0` ∧ `DET_QUALITY_FLAG == 0` ∧ `SPURIOUS_FLAG == 0` ∧ size > 0.
  (Gaia-matched rows only if also point-like: on Q1 the MER Gaia matches at IE < 19 are mostly bright galaxies, POINT_LIKE_PROB ≈ 0.)
* **Size measure S = `SEMIMAJOR_AXIS`** (MER VIS second-moment semi-major axis). **Not `FWHM`**: the MER `FWHM` column is the PSF FWHM at the object's
  position, not a source size (Q1, IE 20–21: Gaia stars 1.22/1.30/1.42 at 5/50/95 %, extended galaxies with A ≈ 8 px 1.22/1.31/1.41; corr(FWHM, A) = −0.02),
  so the literal R_FWHM cut is inert (FREEZE E1). R_FWHM is still computed and written (`R_FWHM`, `lcs_size_FWHM`).
* **PSF size per tile** S_PSF(tile) = median S of the stars with 19 < IE < 21 in the tile (≥ 5); otherwise the median of such stars within 0.5° of the
  object (≥ 5); otherwise the release median (`PSF_SRC_*` = 0/1/2). R = S / S_PSF(tile).
* **Stellar locus**: R_star,97.5(IE) = 97.5th percentile of R of the stars in the 0.5-mag IE bin, over the whole release (18 ≤ IE < 25; bins with < 30
  stars are unpopulated). Keep (`lcs_size`) if `VIS_DET == 1` ∧ R ≤ R_star,97.5 of the object's bin; objects in an unpopulated bin (in particular
  IE ≥ 25) use the nearest populated bin (ties → brighter) and are flagged `lcs_size_extrap` — since the point-source locus of S *shrinks* with IE,
  this is looser (conservative) for fainter objects. Products: `star_locus.csv`, `tile_psf.parquet`.
* **Q1 result**: 275,543 stars used, 55,305 PSF stars, 344 / 352 tiles with their own PSF size (every candidate had a tile PSF).
  R_star,97.5 per bin (IE 18.0 … 25.0): 1.62, 1.38, 1.30, 1.31, 1.26, 1.23, 1.19, 1.12, 1.03, 0.98, 1.02, 1.06, 0.89, 0.82 (R_star,50: 1.21 → 0.67).
  S-LCS: 7,295 pass box ∧ compact ∧ not-star → **6,587 pass the size cut (90.3 %)**; IE of the LCS objects 23.6 / 25.2 / 26.6 (2.5/50/97.5 %),
  58 % beyond the populated range (extrapolated threshold 0.82). The literal R_FWHM rule would keep 97 % (PSF variation inside a tile only).
  `sel_PHYS` / `sel_B25` objects would pass the size cut at 91 %.

## 7. Stars and artefacts
### 7.1 Gaia star rejection (`not_gaia_star`; G5 decided: 5σ, 0.5″)
Reject if (a) the MER row's `GAIA_ID` (valid) is a Gaia DR3 source with parallax/σ > 5 or total proper motion/σ > 5, or (b) PR-2's pre-staged Gaia DR3
(`/srv/LRD/prestage/cat/gaia_dr3`, propagated from 2016.0 to epoch 2024.0) has such a source within 0.5″. Gaia matches without significant astrometry are
kept and flagged `gaia_match`. Brown-dwarf flag `bd_locus` = S/N(g) < 3 ∧ S/N(r) < 3 ∧ IE − YE > 1.5 (flag only).
### 7.2 Automatic artefact flags (replace the paper's visual inspection; none is a cut)
A1 `no_nb1` (no MER neighbour within 1.0″; G10: flag only), A2 `spurious_prob_gt01` (`SPURIOUS_PROB > 0.1`), A3 `nb2` (neighbour within 2″),
A4 `line_emitter` (as-written Hα test fails), A5 cutout V1/V2 flags for the final samples, random 5 % visual audit of the final PHYS, B25 and LCS samples
(seed 20261112 on an OBJECT_ID hash).

## 8. Mid-IR policy and the Letter-B method (Glenn D3)
### 8.1 Not in the selection
No WISE/IRAC step in any selection. Every DR1 density, number count and LF is published without a mid-IR veto and labelled an upper limit to the
(V-shaped, compact) LRD population. WISE forced photometry (PR-4/SM-E engine) is the Letter-B measurement, made identically on the controls.
### 8.2 Purity calibration in the IRAC-covered deep fields
As v0.9: f_IRAC(H, z_fit) = N(IRAC-undetected, unc-map S/N ≤ 3 in ch1 and ch2) / N(all, IRAC-covered), measured per depth/region (Q1: F 0.11, N 0.15, S 0.34
for the B25 reading); Wide densities × f_IRAC only as a labelled, model-dependent estimate.
### 8.3 Letter-B hot-dust test — pre-registered estimators (D3)
* **Headline = the width-independent summed estimator** K_Σ = Σ_i f_obs,i / Σ_i f_pred,i(K = 1) (measured mid-IR flux over the flux an unscreened type-1
  quasar with the object's line-corrected 5100 Å luminosity would give; paper's line correction median 1.36 marginalised), with its bootstrap error,
  **plus the screened-fraction limits q3 (A_V = 3) and q2 (A_V = 2)**.
* **q3 headline = the model-light counting bound** (every object with K > 5 at > 5σ counted as screened, divided by the injection-measured completeness;
  95 % upper limit); the **model-based q3** (calibrated likelihood-ratio threshold t*, SM-H engine) is quoted alongside, never alone.
* The paper's fixed-width (σ = 0.5 dex) K_med is NOT quoted as a calibrated limit for Euclid samples (not calibratable at N ≳ 10³, SM-H E-H1); free-width
  K_med only with the calibrated inflation factor, as a secondary number.
* Run for `sel_PHYS` (primary) and `sel_B25` (comparison), identical code; controls as DR1_PLAN.

## 9. Sample tiers (G6 decided)
* **T1 photometric**: `sel_PHYS` (and `sel_B25`, `sel_LCS` separately).
* **T2 spectroscopically supported**: T1 objects with (a) a DR1 SPE redshift within ±0.1(1+z_fit) of z_fit with `z_spe_error_flag == 0` and SPE class GALAXY
  or QSO with probability ≥ 0.5; OR (b) an external spectroscopic redshift (PR-2 pre-stage: DESI DR1 `zwarn==0` primary, SDSS DR17 `zwarning==0`, OzDES/2dFGRS
  `q_z ≥ 3`, 6dFGS quality ≥ 3) matched ≤ 1″ and within ±0.1(1+z_fit); OR (c) a **broad Balmer line by SM-F's GOLD criterion** in the DR1 SIR spectrum:
  Glenn criteria (broad Hα FWHM_b ≥ 1000 km/s and < 9,500 km/s, S/N(F_b) ≥ 5, Δχ²(broad vs narrow-only) ≥ 25; narrow Hα+[N II] 1:3 tied, σ_int ≤ 250 km/s,
  |Δv_b| ≤ 1000 km/s; Hβ+[O III] jointly when covered; LSF-convolved, pixel-integrated) **AND per-dither consistency** (≥ 2 usable dithers; non-linear
  parameters frozen at the combined fit; χ²-consistency p ≥ 0.01 with a 20 % per-dither flux systematic; F_b > 2σ in ≥ 2 dithers). Q1 null rate 0.14 %
  (11/8,000; 95 % 0.07–0.25 %) → DR1 counts of GOLD objects are always stated against the expected false-GOLD background (0.14 % × N fitted).
  Stacks: continuum-normalised (rest-EW) only. Code `code/grism` (recorded hash, §13). The runner implements (b); (a) needs the `spe` ingest group and (c) the
  grism pipeline — both run after the catalogue, with these thresholds.
* **T3 benchmarks**: JWST-confirmed LRDs and spectroscopic AGN from PR-2's lists (Euclid-selected lists excluded); recall only, never selection.

## 10. What is NOT reproduced (residuals carried into the papers)
* The paper's visual inspection (it kept 76–79 % of its pre-visual no-IRAC objects): ~25 % of the B25 sample are objects its eyes would have removed —
  measured by the 5 % audit.
* EDF-N anomaly (G12 decided: accepted, unexplained): published density in the uncovered half ~3.6× below ours; published objects are u-bright in our
  photometry. **North and South are reported separately** in Letter A (columns `REGION`, `REGION_NAME`, `HEMI`).
* Fit details at the slope boundaries and few-band objects at S/N ≈ 3.
* The published β_opt > 0 is mostly driven by the IE−Y jump (§6.2).

## 11. Output columns (per object reaching the fit or any final sample)
`OBJECT_ID, RA, DEC, TILE_ID, FIELD_DR1, REGION, REGION_NAME, HEMI, EDF_LABEL, CELL64`, every input column, `F_<B>/E_<B>` (P1; PHYS error = E × APCORR × X_B),
`APCORR_2FWHM, BANDSET, BANDSET_KEYS, zlo, zhi`; fit values per photometry `z, beta_uv, beta_opt, chi2, A, MUV` (P1), `*_PHYS`, `*_P0`; masks per photometry
`nfilt4, nfilt4_zfit, n_det, n_uv, n_opt, n_tie, knife_edge, rb, vshape_slopes, vshape, halpha_txt, halpha_rev, chi2_lt100, zfit_le21` (+ `_PHYS`, `_P0`);
photometry-independent `reliable, zphz_lt3, compact, not_gaia_star, gaia_match, gaia_checked, no_nb1, no_nb1_cut, nb2, spurious_prob_gt01, bd_locus, line_emitter`;
LCS `lcs_box, lcs_box_B25, LCS_JH, LCS_gIE, LCS_lcs_g_band, IE_SEL, R_SEMIMAJOR_AXIS, R_THR_SEMIMAJOR_AXIS, PSF_SEMIMAJOR_AXIS, PSF_SRC_SEMIMAJOR_AXIS,
R_FWHM, R_THR_FWHM, lcs_size, lcs_size_SEMIMAJOR_AXIS, lcs_size_FWHM, lcs_size_extrap, lcs_size_nisp_det`; chain memberships `IN_<chain>`; selections
`sel_PHYS, sel_PHYS_txt, sel_PHYS_rev, sel_B25, sel_B25_txt, sel_B25_rev, sel_B25_P0, sel_B25_rev_P0, sel_LCS, sel_LCS_pre_size, sel_LCS_B25, sel_LCS_B25_pre_size`;
tiers `tier_T2, tier_T3, tier, specz, specz_src`; `DUP_ID, PAIR_LT0p3`; `SPEC_VERSION, SPEC_CODE_SHA256`.
Files: `T1_candidates.parquet` (= sel_PHYS), `T1_B25_candidates.parquet` (= sel_B25), `LCS_candidates.parquet` (= sel_LCS), `previs_superset.parquet`,
`funnel_region.csv`/`funnel_cell64.parquet` (every chain; `_maps` denominators), `denominators_cell64.parquet`, `tile_bands.parquet`, `star_locus.csv`,
`tile_psf.parquet`, `bandsets.json`, `summary.json`; MC `T1_candidates_mc.parquet`, `T1_B25_candidates_mc.parquet`.

## 12. Decision record (all OPEN items of v0.9 resolved)
| id | decision (2026-11-11) | config key (`open`) |
|---|---|---|
| **D1** | two named chains always computed: **PHYS** primary (PHYS photometry, Hα as written) and **B25** (P1, Hα reversed) for comparisons with the published list; P0 variants kept | `D1_primary` PHYS, `D1_PHYS_halpha` txt, `D1_PHYS_photometry`, `D1_B25_halpha` rev, `G8_photometry` P1, `G8_also_run_P0` true |
| **D2** (G4) | star side-table at ingest; stellar-locus 97.5th percentile per 0.5-mag IE bin, per-tile PSF from point-like stars 19 < IE < 21; size measure SEMIMAJOR_AXIS (E1) | `G4_lcs_size_rule` star_locus, `G4_lcs_size_measure` SEMIMAJOR_AXIS |
| **D3** | Letter B: summed estimator + screened-fraction limits; q3 headline = counting bound, model-based alongside (§8.3) | — (analysis) |
| G1 | smaller-error band per filter class | `G1_duplicates` min_err |
| G2 | superseded by D1 (PHYS as written, B25 reversed) | `D1_*_halpha` |
| G3 | `neither`, TIE_TOL 1e-4 | `G3_tie_rule`, `G3_tie_tol` |
| G5 | Gaia 5σ parallax or proper motion, 0.5″ | `G5_*` |
| G6 | T2 as §9, broad line = SM-F GOLD | `G6_t2` |
| G7 | LM active-set fix ON | `G7_lm_active` |
| G8 | superseded by D1 | — |
| G9 | band-side count at z_PHZ | `G9_count_z` phz |
| G10 | MER neighbour < 1″ = flag only | `G10_no_nb1_is_cut` false |
| G11 | S-LCS S/N 3 (PHYS errors) | `G11_lcs_snr` 3, `D1_LCS_photometry` PHYS |
| G12 | EDF-N anomaly stated; N and S reported separately | — |

## 13. Freeze procedure and FREEZE RECORD
Procedure: (1) decisions in `selection_config_dr1.json` (`spec.version` "1.0"); (2) deploy to `/srv/LRD/code`; (3) on the cluster
`python3 -B code/release/selrun.py hash > release/SPEC_HASHES.txt` (code = `tar --sort=name --mtime=@0 --exclude=__pycache__ --exclude=*.pyc -cf - code/lrdlib code/wp4 code/dr1 | sha256sum`
in /srv/LRD; runner = sha256 over selrun.py, chain.py, fits_fallback.py, hooks/selection_dr1.sh and the resolved config), + sha256 of this file, + recorded
(not enforced) hashes of the analysis code `code/grism`, `code/smh`; (4) Q1 check must show `frozen True` and the reference numbers; (5) commit + push this file and
SPEC_HASHES to GitHub. The runner refuses to run (exit 10, ALERT) if the code or runner hash differs (override only with a logged reason = a new version).

**FREEZE RECORD (hashes; computed on the cluster in /srv/LRD, 2026-11-11, before this file was hashed)**
| item | sha256 |
|---|---|
| code = `tar --sort=name --mtime=@0 --exclude=__pycache__ --exclude=*.pyc -cf - code/lrdlib code/wp4 code/dr1` (cwd /srv/LRD; tar records owner/mode, so recompute there or with the same ownership) | `ce7ff7d4ef695300199caf768f9d1d3e8ec2b25e4dc8f6734483ddcb163644bf` |
| runner = sha256 over (name‖NUL‖bytes) of selrun.py, chain.py, fits_fallback.py, hooks/selection_dr1.sh, then the resolved config JSON (sort_keys) — `selrun.py hash` | `9364e7d234fdcbdc9447ab6c09863cff6e985ce894c72f64455c54edf11e1baa` |
| analysis (recorded, not enforced): `code/grism` (cwd /srv/LRD, same tar) | `cf9e9ec74d3cd7f3394e9073f3e8f3616b83a1ce65c96ae1c0595576a8d07e8a` |
| analysis (recorded, not enforced): `code` in /srv/LRD/smh (Letter-B engine) | `1cf9aead2798ef6fe0e8159a7b5f9773e924dd6c8a8302acf01279bb08504be7` |
| config | `selection_config_dr1.json`, `spec.version` "1.0" |
| lrdlib | `/srv/LRD/code/lrdlib` v0.1.0, deterministic fit, LM_ACTIVE, tie rule available |
The sha256 of this file (as frozen, i.e. up to and including the line `END OF FROZEN TEXT` at the bottom) is in `SPEC_HASHES.txt`.
The GitHub commit and UTC push time are appended below that line after the push (not part of the hashed text) and in
`/workspace/LRD/release/FREEZE_RECORD.md`.

## 14. Change log v0.9 → v1.0
1. **D1**: two named chains. NEW photometry convention PHYS (APCORR and extinction on flux and error); PHYS chain = PHYS + Hα as written = PRIMARY
   (`sel_PHYS`, `T1_candidates.parquet`). B25 chain = P1 + Hα **reversed** (`sel_B25`; v0.9's `sel_B25` was P1 + as written, now `sel_B25_txt`).
   `sel_B25_P0` keeps v0.9's definition (as written, P0). MC runs per chain with that chain's photometry.
2. Fit set = ≥ 4 bands at S/N > 3 under ANY photometry (was P1 only): +81,281 Q1 fits (APCORR < 1 objects); B25 selections unchanged.
3. **D2**: star side-table written at ingest (HATS route and FITS fallback); size cut implemented in the runner; size measure SEMIMAJOR_AXIS instead of FWHM (E1).
4. S-LCS S/N with PHYS errors (`sel_LCS`); v0.9's P1 version kept as `sel_LCS_B25`.
5. Gaia null sentinel of the FITS route (2⁶³−1) no longer counted as a Gaia match (the fallback route flagged every row `gaia_match`; no selection effect).
6. D3 (Letter-B estimators) and D4 (G1, G3, G5, G6 with GOLD, G7, G9, G10, G11, G12) recorded; DRAFT removed.
7. Runner hash now covers selrun.py, chain.py, fits_fallback.py, hooks/selection_dr1.sh (+ resolved config).

## 15. Escalations raised at freeze (not silently resolved)
* **E1** MER `FWHM` is a PSF property → the D2 size cut uses `SEMIMAJOR_AXIS`; one key (`G4_lcs_size_measure`) switches to the literal rule.
* **E2** "PHYS S/N ≤ B25 S/N" holds only for APCORR·X ≥ 1 (false for 32 % of compact objects); the pre-cut is a superset regardless (max(APCORR,1)), and the fit
  set is the OR over photometries. PHYS keeps 47 % of the published list (S2 losses) — expected from D1; state in the papers.
* **E3** S-LCS uses PHYS S/N (honest S/N for our papers); the P1 version is written as `sel_LCS_B25`.
* **E4** T2 parts (a) SPE and (c) GOLD run outside the selection runner (need the `spe` ingest group / the grism pipeline on release day).

END OF FROZEN TEXT

---
**§13.1 PUSH RECORD (appended after hashing; not part of the frozen text).** Frozen text = this file up to and including the line
`END OF FROZEN TEXT`; verify with `sed '/^END OF FROZEN TEXT$/q' EUCLID_DR1_LRD_SELECTION_SPEC_v1.0.md | sha256sum` =
`cc0208c95c4c50f61053084840f245d1acb6543f308b56da0eb240e598969905` (line 3 of `EUCLID_DR1_LRD_SPEC_HASHES_v1.0.txt`).
Freeze commit: **Tilanthi/SETI `b06d23dc531e91bc2bf68c4318ea32365eccb21f`**, pushed **2026-11-11T11:40:13Z**
(`paper/EUCLID_DR1_LRD_SELECTION_SPEC_v1.0.md` blob 2124e0d96aa1199e13ad3f46e819cb600b795189, `paper/EUCLID_DR1_LRD_SPEC_HASHES_v1.0.txt` blob
2bb216895de585eaf55560ade4bca41273956091; both verified against the GitHub contents API). SPEC_HASHES written 2026-11-11T11:37:36Z on the cluster;
Q1 check on the frozen code 11:37:46Z: `frozen True`, all 14 finals = reference. DR1 opens 2026-11-12T11:00Z.
