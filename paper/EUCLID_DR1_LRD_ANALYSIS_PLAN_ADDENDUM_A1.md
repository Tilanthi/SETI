# Euclid DR1 LRD programme — Analysis-plan addendum A1 (pre-registered before DR1 release)
Date: 2026-11-12 ~00:10 UTC (DR1-Foundation opens 11:00 UTC). Applies to selection spec v1.0.1 (unchanged; code/runner hashes unchanged).

## Trigger
Job BL (Q1, /workspace/LRD/reports/BL_BLENDS.md) found that re-running the frozen selection with the MER template-fit (TEMPLFIT) Y/J/H
fluxes instead of the 2FWHM aperture fluxes changes ~half of each sample's membership (sel_PHYS 12,836 → 9,167, 4,359 in both;
sel_B25 14,692 → 16,650, 7,297 in both; S-LCS 7,295 → 2,741, 1,575 in both). Cause: photometric noise in faint aperture colours
(aperture J−H scatter ≈ 2× TEMPLFIT at H 24–25), not blends (blend artefacts ≈ 1 % per chain).

## Decisions (no change to the frozen selection)
1. The frozen chains (sel_PHYS primary, sel_B25 comparison, S-LCS) remain the pre-registered samples.
2. Two stability columns are computed for every DR1 candidate and every quoted number:
   (a) SEL_TEMPLFIT: the same frozen selection code with calibrated TEMPLFIT Y/J/H fluxes (BL refit route);
   (b) P_SEL: selection probability from the existing 100 Monte-Carlo flux realisations (fraction of draws passing the chain).
3. "Robust core" samples are defined now: CORE_PHYS = sel_PHYS ∧ SEL_TEMPLFIT(PHYS) ∧ P_SEL ≥ 0.5 (likewise for B25, S-LCS).
   Every headline number (densities, fractions, hot-dust and Balmer tests, radio/X-ray, variability) is reported for the frozen sample AND
   its robust core; a result is called robust only if both agree within their uncertainties. Contamination/completeness for the core is
   taken from the injection and contaminant atlases re-run with the same core definition.
4. Day-1 empirical arbitration: over the Q1 deep fields, DR1 deep (combined-pass) photometry is deeper than Q1; we measure which Q1-level
   photometry (aperture vs TEMPLFIT) better predicts membership in the deeper data and report it — without changing (1)–(3).
5. BLEND_RISK (BL) is written beside the §7.2 automatic artefact flags as a flag only.
