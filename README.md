# ALMA SETI — TRAPPIST-1 Multi-Band Technosignature Search, and a Ranked
# 100-Star Follow-up Target List

Results from an ALMA-archive technosignature (narrowband SETI) search on
TRAPPIST-1, reproducing and extending the method of Mason, Garrett, Wandia
& Siemion (2024), arXiv:2411.19827, across ALMA Bands 3, 6 and 7 — plus a
feasibility study and ranked target list for extending the same method to
the 100 best available ALMA archival targets (see
[`targets/`](targets/) and [`report/TRAPPIST1_followup_100star_feasibility_and_targets.pdf`](report/TRAPPIST1_followup_100star_feasibility_and_targets.pdf)).

**No detection in any band.**

| Band | ALMA project | On-source | Channel width | EIRP_min |
|---|---|---|---|---|
| 3 | 2017.1.00986.S | 6.85 h (8 EBs) | 15.6 MHz (continuum) | 6.4×10¹³ W |
| 6 | 2024.A.00040.S | 26.76 h (30 EBs) | 31.25 MHz (continuum) | 9.95×10¹⁴ W |
| 7 | 2017.1.00215.S | 4.64 h (6 EBs) | 488 kHz (spectral-line) | 4.9×10¹³ W |
| 9 | — | — | — | no archival data exists |

Band 7 gives the deepest limit (only band with a fine spectral window).
Band 3 nearly matches it despite coarse channels, thanks to its large
(43-antenna) array and long integration. Band 6 is weakest, reflecting its
compact 10-antenna flare-monitoring array configuration.

## Robustness checks (Band 7)
- Widened/finer drift-rate search (±12,000 Hz/s vs. the original ±6,000,
  quarter-channel vs. half-channel trial spacing): EIRP_min unchanged.
- Ran the identical search pipeline on the calibrator fields as a
  systematics check: the phase calibrator was clean in both EBs tested;
  the bandpass calibrator showed a real but clearly non-technosignature
  -shaped anomaly (an 8-channel/~3.9 MHz wide smooth bump, not a narrow
  spike) in 1 of 2 EBs, consistent with a residual self-calibration
  artefact. Does not affect the TRAPPIST-1 result, whose calibration
  solutions come from different fields' data.

## Contents
- `search/` — **the "SETI search": the 100-target follow-up survey, in
  progress.** Per-target continuum maps (line-blanked, full-bandwidth) and
  narrowband technosignature search results, one subdirectory per star,
  added as each target completes. See `search/README.md`.
- `report/TRAPPIST1_ALMA_SETI_report.pdf` — short (4-page) written report
  summarising the motivation, data, method, computational infrastructure,
  robustness checks and results of the TRAPPIST-1 search itself.
- `report/TRAPPIST1_followup_100star_feasibility_and_targets.pdf` — feasibility
  study and ranked 100-star follow-up target list, with the full ranking
  methodology.
- `targets/` — the ranked target list (CSV/JSON), summary figure, the full
  ALMA-archive pointing catalogue used to build it, and all pipeline code.
  See `targets/README.md` for details.
- `results/seti_results_full.tar.gz` — full archived TRAPPIST-1 results:
  per-execution-block JSON summaries, search output arrays, processing
  logs, and the complete, generalized pipeline code (`bin/`) used to
  produce them.
- `results/multiband_summary.png` — summary figure (EIRP_min by band, and
  vs. frequency) for the TRAPPIST-1 search.

## Method summary
1. Restore the ALMA pipeline calibration from archival calibration tables
   (CASA 6.7), replaying the delivered `casa_commands.log`/`calapply.txt`
   recipes rather than trusting the delivered flag-versions directly
   (those were written by CASA 5.1.x and don't restore cleanly in 6.7).
2. Direct-DFT extraction of the visibility data to TRAPPIST-1's Gaia
   DR3-propagated sky position (plus a ring of nearby positions and ~500
   control positions for empirical noise/false-alarm calibration) for every
   channel and integration.
3. Doppler de-drift search across a physically-motivated drift-rate range
   (covering the orbital acceleration of all seven TRAPPIST-1 planets, with
   headroom for a close artificial satellite).
4. SNR > 5 threshold against the empirical control-position ceiling;
   EIRP_min = 4π d² S_min δν.

## Follow-up: ranked 100-star target list

A bulk query of the full ALMA archive (27,499 unique calibrated pointings,
retrieved via TAP/ADQL in <30s) cross-matched against nearby stars (Gaia
DR3, <50 pc), confirmed exoplanet hosts (NASA Exoplanet Archive), and known
disk hosts (identified from ALMA's own science-keyword metadata) yields 748
stars with confirmed public ALMA coverage and a measured Gaia proper
motion (required to correctly propagate position to the ALMA observation
epoch — the same effect that offset TRAPPIST-1 by 0.22" in the search
above). Ranked by a weighted score (distance, brightness, M-dwarf/Sun-like
stellar type, disk-host status, exoplanet-host status, proper-motion
quality, ALMA spectral-resolution/data quality), the top targets are
**τ Ceti, AU Mic, 61 Vir, GJ 581**, with **TRAPPIST-1 recovered at rank 5**
as an internal consistency check. Top-100 targets' best available archival
datasets total ~5.5 TB, estimated at 1-2 days of wall-clock compute with
the infrastructure already validated for TRAPPIST-1.

Produced by ASTRA-PA (Taurus platform) for Glenn J. White, Open University.
