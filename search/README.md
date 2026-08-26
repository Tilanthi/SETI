# SETI Search — 100-Target ALMA Archival Survey (in progress)

This directory holds the per-target data products of the "SETI search":
the full-scale application of the TRAPPIST-1 method (see the top-level
[`README.md`](../README.md)) to the ranked 100-star list in
[`../targets/ranked_top100.csv`](../targets/ranked_top100.csv), processed
in priority (rank) order.

**This is a live, ongoing survey** — targets are added here as they
complete. Each target gets its own subdirectory, named after the star.

For each completed target, the subdirectory contains:
- `<star>_continuum.png` / `.fits` — a naturally-weighted (dirty, no CLEAN
  iterations) continuum map using the full available ALMA bandwidth for
  that target, with any spectral windows/channels found to carry strong
  molecular line emission (e.g. CO) excluded ("blanked") from the image.
  Line identification is a data-driven outlier search (>5σ above a
  median-filtered local baseline) on a cheap single-position spectrum —
  any exclusions made are documented, with distances to known bright
  mm-wave transitions, in `continuum_notes.txt`. **PNG axes are labelled
  with real RA/Dec sky coordinates (J2000, WCS-projected), not pixels or
  a plain arcsec offset** — the field-of-view size in arcsec is still
  noted in the plot title for a quick sense of scale. (Note: tau Cet's
  map below predates this convention and still uses an arcsec-offset
  grid; will be regenerated to match on request.)
- `continuum_notes.txt` — which channels (if any) were excluded and why,
  plus the map's rms/peak flux density.
- `drift_search_result.json` — the narrowband Doppler-drift technosignature
  search result for that target's finest available spectral resolution
  (source-region vs. off-source control-position peak SNR, detection
  flag, search parameters).

## Completed targets

### tau Cet (rank #1)
- ALMA project 2016.1.00803.S (Band 6, ~230 GHz), 3 execution blocks.
- Continuum map: rms = 0.107 mJy/beam, peak = 0.863 mJy/beam (~8σ) — this
  peak is centred on the star and is the expected stellar photospheric/
  free-free continuum, **not a technosignature candidate**. No molecular
  line channels were flagged/blanked for this dataset at the search
  sensitivity used.
- Narrowband drift search: no detection (source-region peak SNR 5.47 vs.
  off-source control peak SNR 5.75 — consistent with noise, not a
  candidate).

### PDS 70 (rank #22)
- ALMA project 2019.1.01619.S (Band 6, ~262 GHz), 1 execution block (of
  33 candidate datasets available for this star — one of the most
  intensively ALMA-observed objects in the archive, famous for its
  directly-imaged forming planets; a size-aware per-EB download budget
  automatically skipped two oversized (~32/41 GB) execution blocks from
  the same dataset to stay within this survey's resource limits).
- Continuum map: rms = 0.685 mJy/beam, **peak = 30.4 mJy/beam (44.4σ),
  exactly on the phase centre (0.0″ offset)** — the disk/star itself,
  a strong and expected detection, **not a technosignature candidate**.
  No molecular line channels were flagged/blanked at the sensitivity used.
- Narrowband drift search: no detection (source-region peak SNR 5.56 vs.
  off-source control peak SNR 6.03 — consistent with noise, not a
  candidate).

## Method notes specific to this phase

- Processing is deliberately **sequential** (one target at a time, not
  parallel) and resource-governed (disk-free floor, CPU-core cap,
  load-average ceiling, nice/ionice) since this survey runs on shared
  infrastructure as an explicitly secondary/background task.
- Each target is capped at a maximum of 3 execution blocks (of however
  many are available for its identified ALMA dataset) to bound the
  per-target resource footprint; all raw/intermediate data (downloaded
  ASDMs, working MeasurementSets) are deleted immediately after each
  target's products are written, leaving only the compact deliverables
  in this directory.
- Where a star's finest-resolution ALMA dataset predates the modern
  pipeline calibration-delivery format (no machine-readable calibration
  recipe), the pipeline automatically falls back to the star's
  next-best available dataset.
