# Ranked Target List for a 100-Star ALMA Archival Technosignature Survey

See [`../report/TRAPPIST1_followup_100star_feasibility_and_targets.pdf`](../report/TRAPPIST1_followup_100star_feasibility_and_targets.pdf)
for the full write-up (methodology, ranking algorithm, feasibility/resource
assessment).

## Contents
- `ranked_top100.csv` — the deliverable: 100 targets ranked by score, with
  coordinates, distance, brightness, effective temperature, M-dwarf/Sun-like/
  disk-host/exoplanet-host flags, proper motion (+ signal-to-noise), and the
  specific ALMA dataset (MOUS) identified for each target.
- `ranked_top100.json` / `ranked_all.json` — the same, in JSON (`ranked_all.json`
  contains all 748 scored candidates with confirmed ALMA archival coverage,
  not just the top 100).
- `target_list_summary.png` — summary figure (sky distribution, distance
  histogram, score composition, data-volume distribution).
- `alma_mous_dedup.ecsv` — the full ALMA archive query result: 27,499 unique
  public, calibrated pointings (position, band, spectral resolution,
  integration time, science keywords), bulk-pulled via the ALMA TAP/ADQL
  service in under 30 seconds. Useful as a standalone reference for any
  future archival cross-match work.
- `code/` — the full pipeline used to build the list, in run order:
  1. `get_exo_hosts.py` — pull confirmed exoplanet hosts from the NASA
     Exoplanet Archive.
  2. `get_nearby_gaia.py` — pull nearby (<50 pc) Gaia DR3 stars.
  3. `crossmatch.py` — bulk-query the ALMA archive and positionally
     cross-match against both star lists.
  4. `resolve_disk_hosts2.py` — resolve ALMA's own disk-tagged targets to
     Gaia counterparts (third candidate-discovery pathway).
  5. `resolve_exo_hosts_pm.py` — attach Gaia proper motions to matched
     exoplanet hosts.
  6. `build_master.py` — merge all three candidate pathways.
  7. `dedup_and_score.py` — deduplicate to one row per unique star.
  8. `fill_teff.py` / `fill_bprp.py` — fill missing effective temperatures
     (Gaia `teff_gspphot`, then a BP-RP colour proxy as fallback).
  9. `rank_targets.py` — apply the proper-motion gate and the weighted
     ranking algorithm; writes `ranked_top100.csv`/`.json`.
  10. `resolve_names_top100.py` — attempt common-name resolution (SIMBAD;
      unreachable from the platform used, so `rank_targets.py`'s ALMA
      target-name fallback was used instead in practice).
  11. `estimate_volume.py` / `make_target_figure.py` — feasibility numbers
      and the summary figure.

## Headline numbers
- 27,499 unique calibrated ALMA pointings surveyed archive-wide.
- 748 unique stars with confirmed ALMA coverage AND a measured Gaia proper
  motion (1 candidate excluded for lacking the latter — proper motion is a
  hard requirement, not just a scoring bonus, since it is needed to
  correctly propagate a star's position to the ALMA observation epoch).
- Top 100 targets' best available datasets total ~5.5 TB raw.
- #1 ranked target: **τ Ceti**. TRAPPIST-1 itself is recovered at **rank 5**
  as an internal consistency check on the algorithm.
