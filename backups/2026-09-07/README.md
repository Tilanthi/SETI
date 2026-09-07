# SETI reduced-data backup — 2026-09-07

Second full backup of the reduced/processed SETI technosignature search data (superseding/
supplementing the 2026-09-04 backup in the parent `backups/` directory), packaged in case of
platform relocation. Does NOT include raw ALMA archival downloads or transient calibration
workspace (those are large, ~100+ GB, and are cleaned up automatically after each target completes
processing — they are not needed to reconstruct or interpret the results), and does NOT include the
`software/` directory (the CASA installation itself, ~868 MB — a large third-party dependency, not
SETI-specific data).

## What changed since the 2026-09-04 backup
Covers the survey's progress through the Barnard's Star / Wolf 359 proper-motion crossmatch fix and
the associated recovery campaign (paper v2.10): 60/148 valid target/bands (up from 50/146), 46
unique stars (up from 39), including the first-ever ALMA technosignature data for Barnard's Star and
Wolf 359. See `/paper_20pc/CHANGELOG.md` (v2.10 entry) in this repository for full detail.

## Contents of the archive
- `targets/*/products/` and `targets/*/logs/` for all target/band directories processed so far
  (search result JSONs, continuum summary JSONs, spectral waterfall `.npz` arrays, continuum map
  PNGs/FITS, per-target process logs, and target-list/config files inside `targets/` itself:
  `ranked_master20pc.csv`, `band_mous_master20pc.json` — including its pre-proper-motion-fix backup
  `band_mous_master20pc.json.bak_pre_pmfix_20260906_065425`, a direct artefact of the crossmatch fix
  described in the v2.10 paper — `timeout_overrides.json`, `drift_coeffs.json`,
  `ranked_top100.csv`, `ranked_20pc_volumelimited.csv`, and others)
- Top-level `products/`, `logs/`, `figures/`, `verification/`, `archive_gt20pc_metadata/`,
  `injection_test/`
- `bin/` — the full pipeline codebase (driver, calibration incl. the new legacy
  scriptForCalibration.py replay path, search, continuum-mapping scripts)
- `band_files.json`

Uncompressed archive: `seti_reduced_data_backup_20260907.tar.gz`, 2,595,887,979 bytes (2.42 GiB).
SHA-256: `886e979bd5784b511b3eaa038b0880a86ec513857a1776471eab81055f56e62b`

Too large for a single GitHub file (100 MB limit), so split into 28 parts of 90 MB each (last part
~46 MB) using `split -b 90m -d -a 3`.

## To reassemble
```
cat seti_reduced_data_backup_20260907.tar.gz.part* > seti_reduced_data_backup_20260907.tar.gz
sha256sum seti_reduced_data_backup_20260907.tar.gz   # should read 886e979bd5784b511b3eaa038b0880a86ec513857a1776471eab81055f56e62b
tar -xzf seti_reduced_data_backup_20260907.tar.gz
```

Verified end-to-end before pushing: reassembled from parts, SHA-256 matched the original exactly,
and the reassembled archive was successfully extracted (3073 files).
