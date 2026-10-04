# v3.33 — BUILD HALTED 2026-09-11 ~11:30 UTC on Glenn's instruction

Glenn will upload a later manuscript version to `Tilanthi/SETI` himself. **Do not push this
folder.** Do not resume the build or edit the manuscript until he says so; when he does, the
starting point is *his* uploaded version, not this `.tex`.

## State at the halt

| item | state |
|---|---|
| `technosignatures_20pc_v3.33.tex` | **byte-identical to v3.32's text** (only `\documentclass[numberedappendix]`). No prose edit was ever made. |
| `technosignatures_20pc_v3.33.pdf` | built 2026-09-10 12:48 — **stale**, predates the numbers below |
| `survey_stats.py` | extended (measured completeness curve, drift-excursion stats, line-mask bandwidth, coarse-inclusive occurrence); `SRC` now points at `v333_data_20260911.json` |
| `survey_stats.json`, `survey_numbers.tex` | regenerated 2026-09-11 against the fresh export |
| previous generation kept as | `survey_stats_20260910.json`, `survey_numbers_20260910.tex` |
| pushed to GitHub | **nothing**; repo HEAD is still v3.32 (`035fb39f18`) |

## Data snapshot used
`/workspace/SETI/figwork/v333_data_20260911.json` — export run 2026-09-11T11:21Z, 490 rows,
taken *after* the cluster driver finished its full pass (2026-09-11T06:04:38Z,
139 succeeded / 69 failed / 208 attempted). This is a complete-pass, stable snapshot.

Survey totals: **459 windows / 134 fine / 325 coarse / 91 stars / 85 systems / 113 star-bands /
107 EBs**, against v3.32's published 431 / 118 / 313 / 88 / 82 / 107 / 102.

New since v3.32: first **Band 10** windows (HD 61005, ~857 GHz), which move the searched upper
frequency from 495.1 to **873.1 GHz** and the union bandwidth from 93.1 to **117.9 GHz**.

## Work that was queued but NOT done (for whoever resumes)
1. Prose for the coarse-inclusive occurrence limit. The numbers exist
   (`\OccMeasured`=4.0 % over **85** systems; `\OccFineOnly`=6.0 % over the 61 fine-calibrated
   ones) but no sentence in the manuscript uses them yet — §6.1 still describes the measured form
   as fine-only, and `\OccFineOnly`, `\NOccSystemsFine`, `\InjTrials`, `\CFive*`, `\CEight*`,
   `\DrChan*`, `\NLines`, `\MaskLossGHz` are all defined-but-unused.
2. §6.1's "how far the curve should be carried" and "why this is a pilot number" paragraphs are
   now partly obsolete — the curve is measured on 12 windows / 11 targets / Bands 3, 6, 7, and the
   trial-level records were released with v3.32.
3. **Stale typed digits in `tab:occurrence` and `tab:f95duty`** — rows at 3e13, 1e14, 1e15, 1e17
   and the "29.0 %" duty cell are hand-typed and date from v3.28; they violate the paper's own
   single-source rule and are now wrong by ~0.2 pp. Fix by generating the table body.
4. Band range text says "Bands 3--8" in places; Band 10 is now in the sample.
