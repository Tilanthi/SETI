# SETI reduced-data backup — 2026-09-04

Full backup of the reduced/processed SETI technosignature search data (results, continuum
summaries, spectral waterfall arrays, logs, pipeline code, and target lists), packaged in case of
platform relocation. Does NOT include raw ALMA archival downloads or transient calibration
workspace (those are large, ~100+ GB, and are cleaned up automatically after each target completes
processing — they are not needed to reconstruct or interpret the results).

## Contents of the archive
- `targets/*/products/` and `targets/*/logs/` for all 163 target/band directories processed so far
  (search result JSONs, continuum summary JSONs, spectral waterfall `.npz` arrays, continuum map
  PNGs/FITS, per-target process logs)
- Top-level `products/`, `logs/`, `figures/`, `verification/`, `archive_gt20pc_metadata/`
- `bin/` — the full pipeline codebase (driver, calibration, search, continuum-mapping scripts)
- Target list / configuration files: `ranked_master20pc.csv`, `band_mous_master20pc.json`,
  `timeout_overrides.json`, `drift_coeffs.json`, `ranked_top100.csv`, `ranked_20pc_volumelimited.csv`

Uncompressed archive: `seti_reduced_data_backup.tar.gz`, 1,944,797,762 bytes (1.81 GiB).
SHA-256: `396203d5abf55066d9de20d669215c410a28f952dbd7ca30a4ec67b5d4d4653f`

Too large for a single GitHub file (100 MB limit), so split into 21 parts of 90 MB each (last part
smaller) using `split -b 90m -d -a 3`.

## To reassemble
```
cat seti_reduced_data_backup.tar.gz.part* > seti_reduced_data_backup.tar.gz
sha256sum seti_reduced_data_backup.tar.gz   # should read 396203d5abf55066d9de20d669215c410a28f952dbd7ca30a4ec67b5d4d4653f
tar -xzf seti_reduced_data_backup.tar.gz
```
