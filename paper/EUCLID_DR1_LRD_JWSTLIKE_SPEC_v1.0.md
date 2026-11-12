# Euclid DR1 LRD programme — JWST-like LRD subsample and completeness programme: PRE-REGISTRATION v1.0

Paper A+C (Euclid DR1 census of compact V-shaped sources; Glenn J. White, Open University, and Robin Dey, VBRL Holdings Inc).
Written 2026-11-12 22:40–23:59 UTC by ASTRA PA. Builds on the frozen selection SPEC v1.0 / v1.0.1 (Tilanthi/SETI `b06d23dc531e`, 2026-11-11T11:40:13Z)
and analysis-plan addendum A1 (robust core; 2026-11-12 ~00:10 UTC). Nothing in this document changes the frozen selection.

**Purpose.** The paper asks one question: are the JWST little red dots (LRDs; z ≳ 4) the tip of a ubiquitous population, or an
early-epoch phenomenon? We answer it by measuring the comoving space density, or an upper limit, of **JWST-like LRDs** at
0.5 ≲ z ≲ 2.1 in Euclid DR1. Completeness comes from injecting real JWST LRD spectra through the frozen chain.
This document fixes four things before any density or completeness result for the subsample is computed:
- the subsample definition (§2);
- the injection and completeness programme (§3);
- the estimator (§4);
- the comparison models and the decision language (§5–§6).

It also lists what we had already seen (§7).

---------------------------------------------------------------------------------------------------------------------------------
## 1. Inputs (all frozen or pre-existing; read-only)
* Frozen selection v1.0.1: `sel_PHYS` (primary chain, PHYS photometry), `sel_B25` (comparison chain).
  - Hashes are in `SPEC_HASHES.txt` (sha256 `53397cf2…`): code `ce7ff7d4…`, runner `a422905b…`, spec v1.0.1 `86da05ca…`.
  - DR1 stores: WIDE = `/srv/LRD/dr1_lab` (8,947 tiles); DEEP = `/srv/LRD/dr1_esa_deep` (EDF-N/F/S).
* A1 robust core: `CORE_<chain> = sel_<chain> ∧ SEL_TEMPLFIT_<chain> ∧ P_SEL_<chain> ≥ 0.5`.
  - Code `/srv/LRD/code/core` (tree sha `2a934b55…`) plus BL tfcal refit `/srv/LRD/code/bl` (tree sha `cc9c2bdf…`).
  - Products: `/srv/LRD/post/{wide,deep}/core/report/core_table.parquet` and `/srv/LRD/post/{wide,deep}/bl/refit/tfcal/refit.parquet`.
* Areas: VMPZ effective coverage (`/srv/LRD/post/area`). Members with EFFCOV = 0 are excluded, as in `code/post/dens.py`.
* Region groups (as in `code/post/dens.py`, by tile):
  - DEEP: EDF-F, EDF-N, EDF-S.
  - WIDE: WIDE-S (Dec < 0, DES griz), WIDE-N-u (u band present in the tile), WIDE-N-nou.
* JWST LRD spectra: PX-2 `lrd_jwst_prism`, `/srv/LRD/px2/templates`.
  - 57 DJA NIRSpec/PRISM spectra of spectroscopically confirmed LRDs (z 2.0–8.4), plus the PX-2 median broad-line composite.
  - Synthetic photometry: PX-1 `templib` (container `/workspace/LRD/code/px1/templib`, concatenated-source sha `25762fd7…`).
  - Atlas machinery: PX-1 `atlas_make.py` (`aa87c7aa…`) and `atlas_select.py` (`1a06e2aa…`).
* **Definition code (pinned): `code/jwstlike/jl_define.py`, sha256 `422d920edf706f7eb1e9cd643ea55d6ab4adcebb7c9162c53c06be0cda9ffc1c`** (the same file on the cluster at `/srv/LRD/code/jwstlike/`).
  - It is a pure function of the columns listed in its docstring.
  - It is applied identically to real DR1 rows and to injected rows.

## 2. Definition of the JWST-like subsample (JL)
### 2.1 Primary: `JL_PRIMARY`
`JL_PRIMARY = sel_PHYS ∧ CORE_PHYS ∧ 0.5 ≤ z_fit ≤ 2.1 ∧ β_opt ≥ 1.0 ∧ β_UV ≤ −0.6 ∧ H_corr ≤ H_lim`

Where:
- z_fit, β_opt and β_UV come from the frozen PHYS-photometry double-power-law fit (`z_PHYS`, `beta_opt_PHYS`, `beta_uv_PHYS`; f_λ ∝ λ^β, break at 3645 Å).
- H_corr is `HMAG_CORR`.
- H_lim = 24.0 (WIDE) or 25.0 (DEEP).

The frozen chain already imposes β_opt > 0, −2.8 < β_UV < −0.37 and `MUMAX_MINUS_MAG` < −2.6.

Why each cut:
1. **Frozen PHYS chain plus the A1 robust core.** PHYS is the pre-registered primary chain. Under decision D-A1, the core is the sample used for quoted numbers. On DR1 the frozen chains are dominated by low-S/N members that do not persist at deep depth: only 3.6 % of Q1 members are re-selected on the DR1 deep stacks.
2. **β_opt ≥ 1.0: "at least as red in the rest optical as the typical JWST LRD".**
   - 0.98 is the median β_opt of the 341 photometric LRDs of Kocevski et al. (2025, Table 3; `ref/kocevski24_table3.dat`).
   - When the 57 DJA prism spectra are put through our own chain at z 0.6–2.1 (PX-1 atlas, Q1 noise), the per-template median at H < 22.5 is 1.47 (16th percentile 0.76).
   - Brown+14 galaxies that pass the chain land at β_opt 0.62 [0.17, 1.74], and unreddened QSOs at 0.32.
   - The two slope cuts together keep 62 % of chain-selected JWST spectra, 21 % of chain-selected galaxies and 18 % of chain-selected QSOs (PX-1 atlas; these are template-draw fractions, not population fractions).
3. **β_UV ≤ −0.6.**
   - 98.8 % of Kocevski+25 LRDs have β_UV ≤ −0.6; the through-chain JWST median is −1.38.
   - Contaminating galaxies and QSOs pile up at the red β_UV edge of the V-shape box (PX-1 §1.3: β_UV > −0.6 ∧ low β_opt is contaminant-rich).
4. **0.5 ≤ z_fit ≤ 2.1 and H_lim.**
   - This is the domain in which the injection model is defined (§3).
   - At fainter H the core fraction is < 5 % (Letter A Table 5), and the completeness model rests on extrapolated compactness behaviour.

No mid-IR, spectroscopic or visual criterion enters the primary definition. Those data cover only part of the sample, and the depth they need is not uniform.

### 2.2 Secondary variants (reported beside the primary; they never replace it)
| name | definition | purpose |
|---|---|---|
| `JL_S1_INCL` | as primary but β_opt ≥ 0.55 (16th percentile of the JWST atlas through the chain, Q1 noise) | inclusive envelope (more complete, less pure) |
| `JL_S2_PTLIKE` | primary ∧ `MUMAX_MINUS_MAG` ≤ −2.75 (95th percentile of the DR1 stellar locus) | strictly point-like: tests host-galaxy dilution |
| `JL_S3_NOHD` | primary minus objects with an individually measured hot-dust ratio K_P > 1 at > 3σ (DEEP IRAC2, WIDE unWISE W2; Letter-B engine) | removes hot-dust-dominated (quasar-like) objects, which JWST LRDs are not |
| `JL_S4_B25` | CORE_B25 ∧ the same z/β/H cuts on the P1 fit | comparison chain |
| `JL_S5_TFBETA` | primary ∧ the same β cuts also satisfied by the PHYS fit on calibrated-TEMPLFIT NISP fluxes (BL tfcal refit) | slope robustness against the photometry method |

The subsample is given in two variables:
* M_UV: absolute magnitude at rest 1450 Å from the UV power law (frozen `MUV_PHYS`).
* M_5500: from the optical power law at rest 5500 Å (`jl_define.m5500`, same cosmology H0 = 70, Ωm = 0.27).

**M_UV is the primary comparison variable**: the JWST LFs we compare with (§5) are UV LFs. M_5500 is the comparison variable for models defined in the rest optical.

## 3. Completeness / injection programme (run only after this document is pushed)
Completeness is defined as
C_r(z, M | t) = P(object enters JL_PRIMARY | a true LRD with spectrum t, true z and true M (M_UV or M_5500), in region group r).

### 3.1 Catalogue-level injection (primary completeness)
* **Templates.**
  - **T1 = 57 DJA prism LRDs** (primary; equal weights; all 57 are used, not only those that ever pass).
  - T2 = PX-2 broad-line composite.
  - T3 = the 341 Kocevski+25 (β_UV, β_opt) pairs as lineless double power laws (the PR-4 construction).
  - T4 = local analogues: The Egg (J1025+1402; Lin+25) and J092359+415736 (An+26). These are photometric SEDs built from GALEX + SDSS/Legacy Survey + 2MASS/UKIDSS + WISE photometry, interpolated log-linearly in the rest frame and including the host light. If a usable SED cannot be built, we state so and drop T4.
  - The three SDSS local and 27 DESI low-z LRDs of Lin+25/26 are added to T4 only if GALEX rest-UV photometry exists for them. Their spectra cover only rest 2200–8000 Å.
* **Red extension.** At z < 2, H lies redward of the prism coverage for many templates. At z = 1.0 only 16 of the 57 templates cover H.
  - **Primary (E_BB):** beyond the last good pixel, splice the PX-2 composite (scaled to the template over its last 300 Å of continuum; this also supplies Hα when the template stops blueward of it). Beyond 9000 Å, continue with a blackbody fitted to the line-masked rest 4000–9000 Å continuum. This is the observed rest-near-IR turnover of LRDs and the "black-hole-star" photosphere.
  - Variants: E_FLAT (flat f_ν beyond coverage), E_PL (continue the fitted β_opt power law; no turnover), E_NONE (only template/z pairs whose observed bands are covered; no extrapolation).
* **Grids.**
  - True z uniform in [0.4, 2.4] (Δz = 0.05 synthetic photometry, linear interpolation in magnitude), including leakage from outside the window.
  - True H uniform in [19, 25.5] (WIDE) or [19, 26.5] (DEEP).
  - ≥ 300 objects per (template, Δz = 0.1, region group) for T1.
  - Region groups: WIDE-S, WIDE-N-u, WIDE-N-nou, DEEP-EDF-F, DEEP-EDF-N, DEEP-EDF-S.
* **Noise: real DR1 donors (PX-1 construction).** Each injected object takes a real DR1 compact row (MUMAX−MAG < −2.6) of the same region group with |ΔH| < 0.25. It inherits the donor's:
  - band availability, per-band 2FWHM aperture errors, APCORR, E(B−V), VIS_DET and tile.

  FLUX_APER = F_true/(APCORR·X_B) + N(0, σ_aper), so `selrun.corrected()` returns F_true + noise exactly as for real data.
* **TEMPLFIT fluxes (needed for SEL_TEMPLFIT).** F_TF = F_true + ε_TF, with ε_TF ~ N(0, σ_TF,donor).
  - ε_TF is correlated with the aperture noise by ρ_B(H, r). ρ_B is measured from isolated DR1 compact sources via
    Var(F_ap·APCORR − F_TF) = σ_ap² + σ_TF² − 2ρσ_apσ_TF, in bins of TEMPLFIT S/N.
  - SEL_TEMPLFIT is then computed by the unchanged BL tfcal route.
  - Variants: ρ = 0 and ρ = 0.8; the "pedestal" variant adds BL's measured median aperture-minus-g_B(TEMPLFIT) offset to the injected aperture fluxes.
* **PHZ.** NNPZ outputs are emulated as in PX-1: PHZ_CLASSIFICATION, PHZ_MEDIAN and MODE_1/2 are taken from one of the 10 nearest real DR1 compact rows of the same region group, in asinh-colour + H space.
  - Variant: PHZ_CLASSIFICATION forced to "not star" (upper bound).
* **Compactness.** MUMAX_MINUS_MAG of a point source is drawn from the image-level point-source injections (§3.2) as a function of IE and region group. Donor values are not used, because they are compact by construction.
* **Flags.** A flag-loss factor f_S0(IE, r) multiplies the completeness. It is the fraction of DR1 compact (MUMAX−MAG < −2.6), SPURIOUS_PROB < 0.7 sources from the full MER catalogue (IRSA HATS / ESA) that fail the frozen S0 reliability flags.
  - Variant: f_S0 = 1.
* **Selection.** The frozen chain is applied with `selrun.run_task`, unchanged and hash-checked, then CORE (P_SEL from `core_mc.py run` on the injected rows; SEL_TEMPLFIT as above), then `jl_define.jl_flags`. The Gaia star veto is passed (GAIA_ID null).
* **Outputs.** C_r(z, M | t) per template; the template mean C̄_r. The systematic envelope is min/max over {E_BB/E_FLAT/E_PL/E_NONE} × {ρ measured/0/0.8, pedestal} × {PHZ emulator/forced galaxy} × {f_S0 measured/1} × {T1 equal weights / T1 reweighted to the Kocevski (β_UV, β_opt) distribution / T3}.
  - **Conservative-low** and **conservative-high** completeness are the lowest and highest members of this envelope.

### 3.2 Image-level test: compactness and host-galaxy dilution
* **Data.** Real DR1 VIS (and NISP H) MER mosaic cutouts: ≥ 200 positions per region group, drawn at random positions free of catalogued sources within 3″. Source: IRSA DR1 or ESA DataLabs `/data/euclid_idr1/DR1`, within reasonable-use limits.
* **Injected models.**
  - (a) Point source, using the empirical PSF (median-stacked Gaia stars in the same mosaic).
  - (b) Point source plus host: Sérsic n = 1 with r_e = 0.2, 0.5, 1.0, 2.0 kpc and host fraction f_host(VIS) = 0.1, 0.3, 0.5, 0.7. These are mapped to log M★ ≈ 7–9.5 with a constant-SFH M/L (100 Myr–1 Gyr). Literature anchors: Judež+26 host log M★ = 7.3 at r ~ 1″ magnified; PAN-BH*-1 ~1 kpc host (Torralba+26).
  - IE from 20 to 26 in 0.5-mag steps.
* **Measurement: MER-equivalent.**
  - Background-subtracted SourceExtractor-style detection (`sep`) on the VIS cutout.
  - MU_MAX = peak-pixel surface brightness; MAG from the detection-image total flux; MUMAX_MINUS_MAG = MU_MAX − MAG.
  - Also: 2FWHM aperture flux fractions for host light in VIS/Y/J/H.
* **Validation.** The same code is run on real catalogued stars (Gaia) and galaxies in the same cutouts and compared with their MER MUMAX_MINUS_MAG and fluxes. The offset and scatter are reported.
  - If |median offset| > 0.05 mag or the scatter exceeds 0.1 mag at IE < 23, a linear mapping fitted on real sources is applied and recorded.
  - Limitation (stated in the paper): this is not the MER pipeline (no multi-resolution deblending; no exact MER background model).
* **Use.**
  - (i) The point-source P(MUMAX−MAG < −2.6 | IE, r) and its distribution feed §3.1.
  - (ii) The host grid gives C_host(z, M | t, f_host, r_e) = C_r × P(compact | host) with host light added to the catalogue fluxes (host SED: constant-SFH, low-dust stellar population; aperture fractions from (b)). It is reported as the host-dilution systematic.
  - Primary completeness assumes point sources. This follows from the < 0.2 kpc sizes of JWST LRDs; the prism spectra already include the integrated host light.

## 4. Estimator
* **Counts.** N_r(z-bin, M-bin) of JL_PRIMARY members with EFFCOV > 0.
  - z bins [0.5, 1.0), [1.0, 1.5), [1.5, 2.1].
  - M_UV bins 1 mag wide (−25…−17); M_5500 bins 1 mag wide (−26…−19).
* **Effective volume.** V_eff,r(bin) = A_r ∫_bin C̄_r(z, M) (dV/dz/dΩ) dz, averaged over M within the bin. Here A_r is the VMPZ effective area of region group r.
* **Density.** φ(bin) = Σ_r N_r / (Σ_r V_eff,r · ΔM). This is a completeness-weighted effective-volume estimator, computed per layer (WIDE, DEEP) and for WIDE+DEEP.
  - **Primary = WIDE** (area); DEEP is the depth check.
  - If corrected WIDE and DEEP densities differ by more than a factor 2 beyond their 2σ errors, the result is labelled depth-dependent. DEEP is then quoted as the best estimate and WIDE as the upper envelope (consistent with D-A1).
* **Analysis domain D.** Bins with C̄ ≥ 0.10 under conservative-low completeness. Bins outside D are reported as "unconstrained", never as limits.
* **Upper limits (95 %).**
  - JL counts include contaminants (galaxies, reddened QSOs; PX-1), so N_obs is an upper bound on the number of true JWST-like LRDs.
  - φ_95 = N_95(N_obs) / V_eff, with N_95 the one-sided Poisson 95 % upper limit, inflated in quadrature by the tile-to-tile (cosmic-variance) scatter. The scatter is measured by bootstrap over tiles within each region group.
  - **No purity correction is applied to upper limits.**
* **Lower limits and purity (used only for D2 in §6).**
  - P_lo is the binomial 95 % lower bound on the fraction of JL members, within the spectroscopically covered subset (Euclid grism GOLD at H ≤ 23.6; DESI/SDSS), that show a broad Balmer line (FWHM ≥ 1000 km/s) at |Δz| ≤ 0.1(1+z_fit).
  - φ_lo = P_lo · N_05(N_obs) / V_eff (conservative-high completeness).
* **1/V_max.** 1/V_max,eff (Σ_i 1/V_eff(M_i)) is shown as a display alternative.
* **Forward model (primary statistical test).** For each comparison model m (§5): N_pred,m = Σ_r A_r ∫∫_D φ_m(M, z) C̄_r(z, M) dV dM, at conservative-low and conservative-high completeness.
  - p_m = P_Poisson(N ≤ N_obs | N_pred,m), with cosmic variance as a negative-binomial dispersion from the tile bootstrap.
* **Evolution index.** k in n(z) ∝ (1+z)^k between the JWST z ≈ 4.5–6.5 density and our z-bin densities at matched M_UV (−21 ≤ M_UV ≤ −19 where in D). It is quoted with 95 % bounds and compared with the k implied by local LRDs.

## 5. Comparison models (functional forms fixed here; numbers verified against the papers in `literature/AC_COMPARISON_MODELS.md` / `ac_models.csv`, sha256 `2f775585…`, 154 rows)
* **M1 "ubiquitous / non-evolving".** The JWST LRD UV LF at z ≈ 4.5–6.5 held constant to z = 0.5. Two versions:
  - M1a, primary: the Kocevski+25 Table 4 binned UV LF at 4.5 < z < 6.5 (e.g. log φ = −4.69 at M_UV = −19 and −5.10 at −20, in Mpc⁻³ mag⁻¹), interpolated in log φ;
  - M1b: the Kokorev+24 Schechter fit at ⟨z⟩ = 5 (M* = −20.64, φ* = 8×10⁻⁶ Mpc⁻³ mag⁻¹, α = −1.76).
  - In the rest optical, M1c is the Ma+26b VoR Schechter fit at 4.5 < z < 4.9 in observed M5100 (Φ* = 5.5×10⁻⁵, M* = −21.7, α = −1.28), with M5500 = M5100 − 0.25 ± 0.09.
  - **Slope-distribution consistency.** Only 42 % of Kocevski+25 LRDs at 4.5 < z < 6.5 satisfy β_opt ≥ 1 ∧ β_UV ≤ −0.6. The full JWST LF is compared with N_obs/C̄, because C̄ (template-averaged) already contains the probability that a JWST LRD passes the slope cuts. The variant compares N_obs/C_cut with M1 × 0.42, where C_cut is the completeness for templates that intrinsically satisfy the cuts. It enters the systematic envelope.
* **M2 "declining (Ma+26a)".** Their observed-M5500 LF at 1.7 < z < 2.7 (≈1.2×10⁻⁶ Mpc⁻³ mag⁻¹ at M5500 = −21 and −22) and n(M5500 < −20.5) = 2.1×10⁻⁶ (z ≈ 2.2) and 4.6×10⁻⁶ Mpc⁻³ (z ≈ 3.2).
  - It is applied in M5500 against our M5500. Below z = 1.7 there are two variants: (a) log-linear extrapolation of the z = 3.2 → 2.2 trend; (b) flat.
  - The UV-LF transfer is a variant: M1a × the M5500 decline factor.
  - Ma+26a regard these values as upper limits (contamination).
* **M3 "sharp drop / log-normal".** The published log-normal n(z) models (Inayoshi 2025; Kapoor+26), normalised to M1a at z = 5, as evaluated in AC_COMPARISON_MODELS.md. The Ma+26b luminous cutoff (λL5100 ≈ 2.2×10⁴⁴ erg s⁻¹) is applied to the bright end.
* **M4 "local anchor".** A power law in (1+z) between M1 (z ≈ 5) and the local lower limits: n ≳ 5×10⁻¹⁰ (SDSS, z < 0.5; Lin X.+26a) and ≳ 7.5×10⁻¹⁰ Mpc⁻³ (DESI DR1, z < 1; Lin X.+26b).
  - Both local values are integrated lower limits and are luminosity-matched only approximately. The M4 comparison is therefore stated as a bracket, not a test.
* **External cosmic-noon measurements (compared, not modelled):** VIPERS broad-line n = 2.9×10⁻⁷ (0.5–1.0) and 7.1×10⁻⁷ Mpc⁻³ (1.0–1.75); Kapoor+26; Rinaldi+26; Euclid Q1 n(M_UV < −19, 1.5–2.0) = 8.3×10⁻⁶ (Bisigello+26).
* **M5 "quasar-like evolution"** (upper envelope only). M1 scaled by the Kulkarni+19 quasar n(M_UV < −21) ratio, as in PR-4.
* **Conversion notes.**
  - Cosmology differences (≤ 3 %) are ignored. M_UV at 1450 Å vs 1600–2000 Å differs by ≤ 0.1 mag.
  - Rest-optical models use our M5500 of the fitted power law (observed, not dust-corrected).
  - Bolometric LFs (dust-corrected L_bol) are not used for tests.

## 6. Decision language (pre-registered)
Let R = φ_JL / φ_M1a (M1b and M1c as variants), evaluated with the forward model over the domain D at −22 ≤ M_UV ≤ −19 (primary) and per z bin.

1. **D1 "early-epoch phenomenon"**: the 95 % upper limit on R is < 0.1 at conservative-low completeness. Even counting every JL member as a true LRD, JWST-like LRDs at z ≈ 0.5–2.1 are at least 10× rarer per comoving volume than at z ≈ 5, at fixed M_UV. We then quote the 95 % bound on the evolution index k and state which of M2/M3/M4 remain allowed (p_m > 0.05).
2. **D2 "tip of a ubiquitous population"**: the purity-corrected 95 % lower limit on R is ≥ 0.3 at conservative-high completeness.
3. **D3 "declining but present / intermediate"**: neither D1 nor D2. We quote R (central value with the full systematic envelope) and k, and say which models are excluded at p < 0.05.
   - "Consistent with M_m" means p_m ≥ 0.05 for N ≤ N_obs and N_obs within the model's predicted range after allowing for contamination.
   - An excess over M2/M3 is reported as an excess of *candidates* and is not called a detection of JWST-like LRDs unless the purity lower bound alone requires it.
4. **D4 "inconclusive: completeness too low"** in any of these cases:
   - D is empty in the primary M_UV range;
   - N_pred,M1 < 10 at conservative-low completeness;
   - the systematic envelope spans more than a factor 3, so that the verdict (D1 vs D3, or D2 vs D3) flips within it.

   Then we state the limiting factor (depth, compactness/host dilution, photo-z, S/N) and the depth that would be needed.

The verdict is given per z bin and for the combined window. **The z ≈ 0.5–1.0 bin is compared with M4 (local LRDs) separately.** Verdicts from JL_PRIMARY are the result. The secondary variants are robustness checks: if they disagree, the disagreement is reported, and the verdict is not changed.

## 7. Disclosure: what had been seen before this pre-registration
Seen (all aggregate; none for the JL subsample as defined here):
1. Frozen PHYS / CORE_PHYS β_opt distributions in DR1 (Letter A v0.01 Table 6):
   - WIDE PHYS p16/50/84 = 0.076/0.288/0.725, β_UV median −1.80; CORE_PHYS 0.187/0.485/1.00, β_UV median −1.25.
   - DEEP PHYS 0.070/0.270/0.687; CORE 0.190/0.492/1.033.
   - Fractions ≥ the JWST atlas median (1.52): PHYS 2.2 % (WIDE) / 1.8 % (DEEP); CORE 4.5 % / 4.7 %.
   - Fractions ≥ the atlas 16th percentile (0.55): PHYS 26 % / 23 %; CORE 44 % / 45 %.
   - **Fraction β_opt > 0.98: PHYS 8.4 % / 7.0 %; CORE_PHYS 16.9 % / 17.8 %.** The primary threshold 1.0 was chosen from the Kocevski+25 median (0.98); these fractions at 0.98 had been seen.
   - The joint (β_UV, β_opt) distribution of DR1 members, the H/z/M distribution of members with β_opt ≥ 1, and any count of JL members had **not** been computed or seen.
2. Densities: PHYS WIDE 144.5 / DEEP 314 deg⁻²; CORE_PHYS WIDE 23.9 / DEEP 43.4 deg⁻²; per-region values (DR1_POSTSEL §3).
   - LF of the frozen PHYS and CORE samples (bright end M_UV ≤ −21.5 robust; Q1 bright end 2.1×/2.8× DR1).
   - Core fraction vs H (75–85 % at H < 22, < 5 % at H > 24); median z 1.6–1.65, H 22.6 (WIDE CORE), M_UV −19.4.
3. Population-level Letter-B results:
   - hot dust K_med < 0.55 (DEEP IRAC2) / < 0.93 (WIDE W2); bright end quasar-like;
   - grism GOLD broad Hα 7/1,209 DEEP PHYS at H ≤ 22.5 (controls 1.4 %);
   - LoTSS/eRASS stacks.
4. Pre-DR1 predictions (PR-4, Q1 noise, parametric Kocevski SEDs, no CORE): selected JWST-like density 411 deg⁻² (no evolution) and 8–26 deg⁻² (declining) vs Q1 observed 57–74 deg⁻².
   - Since CORE_PHYS is 24–43 deg⁻², the outcome against M1 can partly be anticipated *if* the DR1 completeness for JL is not much below PR-4's. **Measuring that completeness (core, β cuts, PHZ, compactness, host dilution) is the information this programme adds.** The decision rules in §6 are written so that a low completeness gives D4, not D1.
5. PX-1 atlas (synthetic, Q1 noise) β-plane landing of JWST spectra and contaminants. It was used to motivate the cuts (§2.1).

## 8. Deviations
Any change after the push is recorded in a dated "Deviations" section of a new version (v1.0.x / v1.1), with the reason and both results. `jl_define.py` is hash-pinned. The injection code is new and will be hash-recorded at run time; procedural choices not fixed here are listed in the results report as analyst decisions.

END OF FROZEN TEXT
