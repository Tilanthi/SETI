# ALMA-SETI on TRAPPIST-1 — live status

## ►► CURRENT: 20pc volume-limited survey + v2.09 paper (2026-09-04 06:20 UTC)
The project has grown well beyond the single-target TRAPPIST-1 work this
file was originally about (see below for that history). Current live
state:
- **Paper**: v2.09 pushed to `Tilanthi/SETI` at `paper_20pc/v2.09/` (see
  `paper_20pc/CHANGELOG.md` for full detail of this and every prior
  version). Main $\leq$20pc sample: 50/146 planned target/bands complete
  (39 unique stars). New this version: a preliminary, explicitly
  non-volume-complete 20-30pc extension appendix (7 usable measurements
  from the older, pre-pivot, non-distance-limited survey's archive) --
  NOT an active parallel campaign, see the paper's Appendix B for the
  honest framing.
- **Cluster driver**: main ≤20pc driver is `seti_search_driver.py`,
  which **requires** `SETI_TARGET_CSV=/data/SETI/targets/ranked_master20pc.csv`,
  `SETI_BAND_MOUS=/data/SETI/targets/band_mous_master20pc.json`,
  `SETI_SUMMARY_PATH=/data/SETI/logs/driver_summary_master20pc.json` to
  be exported before it is invoked -- **it silently defaults to the OLD,
  non-volume-limited `ranked_top100.csv` list otherwise** (found and
  fixed live during the v2.09 session, 2026-09-04 ~05:45 UTC, after a
  relaunch omitted these vars and ran the wrong list for ~20 min; no
  paper numbers were affected, but future relaunches must set these
  three env vars every time). Driver does not self-restart on
  completion -- must be manually noticed and relaunched.
- **Known outstanding pipeline issues** (see `paper_20pc/CHANGELOG.md`
  v2.09 entry and the paper's own Discussion section for full detail):
  (1) the continuum-imaging step lacks the narrowband step's
  pointing-offset sanity guard, so a known crossmatch failure
  (Giclas 9-38A/B) still produces a spurious ~8 Jy "detection"; (2) a
  specific recurring spectral window (seen in HD 10647 and the archive's
  "gamma Lupi") has anomalous noise/weight handling, now diagnosed as a
  reproducible defect (see paper), window-level workaround applied in
  the paper's own results, root cause not yet fixed in the pipeline.
- Full ongoing DONE/FAILED/candidate monitoring is tracked in
  `/workspace/MEMORY.md` (top section, search "SETI monitor").

---

# ALMA-SETI on TRAPPIST-1 — original live status (history below)

**BAND-7 TASK COMPLETE 2026-08-24 05:00 UTC; MULTI-BAND EXPANSION COMPLETE 2026-08-24 11:41 UTC.**

## ►► WRITTEN REPORT (2026-08-25 06:24 UTC)
4-page PDF report written and pushed to GitHub: [`/workspace/SETI/report/TRAPPIST1_ALMA_SETI_report.pdf`](/workspace/SETI/report/TRAPPIST1_ALMA_SETI_report.pdf)
(local copy) / https://github.com/Tilanthi/SETI/blob/main/report/TRAPPIST1_ALMA_SETI_report.pdf (pushed).
Source: [`/workspace/SETI/report/report.tex`](/workspace/SETI/report/report.tex) (pdflatex, texlive
installed to `/usr` this run). Covers motivation, data/bands table, method, compute infrastructure
(download optimization + disk discipline), results table+figure, robustness checks, discussion vs
Mason+24, and conclusion. All numbers pulled directly from MULTIBAND_FINAL_RESULT.json for accuracy.
Repo now has: `README.md`, `results/seti_results_full.tar.gz` (via git-lfs, >100MB), `results/multiband_summary.png`,
`report/TRAPPIST1_ALMA_SETI_report.pdf`. Pushed with the same `Tilanthi` org token used for
ASTRA_baseline (works across Tilanthi repos with push:true).

## ►► FINAL MULTI-BAND RESULT (2026-08-24 11:41 UTC)
[`/workspace/SETI/MULTIBAND_FINAL_RESULT.json`](/workspace/SETI/MULTIBAND_FINAL_RESULT.json),
figure [`/workspace/SETI/multiband_summary.png`](/workspace/SETI/multiband_summary.png).
Full archived results (all per-EB JSON, search.npz, logs, pipeline code):
[`/workspace/SETI/results/seti_results_full.tar.gz`](/workspace/SETI/results/seti_results_full.tar.gz) (115 MB).

**No detection in any band.** Combined EIRP_min per band (SNR>5, no candidates surviving vs.
empirical control-position ceiling):
| Band | Project | On-source | Channel width | EIRP_min (W) |
|---|---|---|---|---|
| 3 | 2017.1.00986.S | 6.85 h (8 EB) | 15.6 MHz (coarse/continuum) | 6.4e13 |
| 6 | 2024.A.00040.S | 26.76 h (30 EB) | 31.25 MHz (coarse/continuum) | 9.95e14 |
| 7 | 2017.1.00215.S | 4.64 h (6 EB) | 488 kHz (fine/spectral-line) | 4.9e13 |
| — | Band 9 | n/a | — | **no archival data exists** |

Band 7 remains the deepest limit (finest channels available). Band 3, despite coarse channels,
came out nearly as deep as Band 7 thanks to its large (43-antenna) array and long integration —
better than the naive "coarse channels = much worse" prediction I gave Glenn mid-task. Band 6 is
~20x worse than Band 7/3, driven by its compact 10-antenna array config (it's a flare-monitoring
project, not built for sensitivity).

**Robustness checks (Band 7):**
- Widened/finer drift search (+/-12000 Hz/s vs original +/-6000, quarter-channel vs half-channel
  steps): EIRP_min unchanged, confirms the original result isn't an artefact of drift-grid choice.
- Searched the SAME pipeline on the calibrator fields (not just TRAPPIST-1) as a systematics check:
  phase calibrator J2301-0158 clean in both EBs tested; the BANDPASS calibrator showed a genuine
  anomaly in 1 of 2 EBs tested (SNR 9.23, but an 8-channel-wide/~3.9 MHz smooth bump — NOT
  narrowband-signal-shaped, consistent with a residual self-calibration artefact from applying a
  bandpass solution back onto the exact data used to derive it). Does not affect the TRAPPIST-1
  result (whose calibration solutions come from a *different* field's data). 2nd EB's bandpass
  calibrator came back completely clean, confirming this is EB-specific, not systematic.

**Disk discipline maintained throughout**: peaked around 380 GB used (many EBs processed in
parallel across 3 bands + robustness checks), returned to <1 GB in `/data/SETI/` at the end via
aggressive cleanup (waterfalls, MeasurementSets, raw ASDMs, aux tars all removed once each EB's
final JSON/search.npz was banked). 343 GB free on cluster at completion.

**Real bugs found+fixed during this expansion (see git history / diffs in bin/ for detail):**
1. Watchdog used SIGKILL, which can corrupt an in-flight aria2c download's resume state without
   any error being raised — the tar reaches the "correct" final size and even passes `tar tf`,
   but is silently missing files (e.g. ExecBlock.xml). Fixed: SIGTERM + explicit presence check
   for ASDM.xml AND ExecBlock.xml, not just a clean tar listing.
2. Step3's "good integration" filter required ALL ~600 sky positions finite at every integration;
   Band-3/6's smaller arrays produce occasional zero-weight (NaN) control probes, which under the
   old strict filter silently discarded 100% of integrations. Fixed: filter on source positions
   only; drop chronically-bad probe columns instead of good time samples.
2b. Step3's spectral edge trim was a fixed 4% guess (tuned on Band-7's FDM data); Band-3's true
   dead-channel edge band is 8/128 channels (12.5%) each side. Fixed: auto-detect the true edge
   from the per-channel weight data instead of guessing a fraction.
3. Both the bandpass AND phase calibrator field names vary PER EXECUTION BLOCK within the same
   ALMA project (not just per-project) — e.g. Band-6 epoch X1ef used J1924-2914 as bandpass cal
   for one EB and J2232+1143 for another; one EB even swapped its phase calibrator to a different
   source entirely. Fixed: classify calibrator fields by INTENT (BANDPASS/AMPLITUDE vs PHASE) from
   each EB's own calapply.txt rather than assuming names are fixed across a project.
4. Several driver scripts (`calcheck.sh`, `band6_process.sh`) always passed `--import` to the
   calibration step even when a previous attempt had already produced a valid intermediate MS,
   forcing a wasted ~10-15 min re-import (and failing outright once the source tar had already
   been cleaned up). Fixed: check for the existing MS before deciding whether to re-import.
5. `mirror_pool_dl.sh`'s completion-marker directory (`$(dirname DEST)/logs`) doesn't match the
   `/data/SETI/logs/` path some driver scripts checked when DEST wasn't `/data/SETI/raw` directly
   (e.g. `/data/SETI/raw/band3`) — downloads could complete successfully but never unblock the
   waiting driver. Manually reconciled during this run; worth hard-coding a single canonical
   marker location in a future revision rather than deriving it from DEST.

## ►► BAND-7-ONLY RESULT (2026-08-24 05:00 UTC, superseded by multi-band above but kept for reference)
Final combined result (all 6 EBs): [`/workspace/SETI/FINAL_RESULT.json`](/workspace/SETI/FINAL_RESULT.json),
figure [`/workspace/SETI/trappist1_seti_summary.png`](/workspace/SETI/trappist1_seti_summary.png).
No detection; combined EIRP_min = 4.9e13 W (~1.4e4x deeper than Mason et al. 2024's published
6.91e17 W). See "RESULT SO FAR" below for the single-EB numbers this was built up from, and see
"DOWNLOAD SPEED OPTIMIZATION" below for follow-up tooling work done after completion.

## Task (from Glenn, 2026-08-22)
Reproduce the method of Mason, Garrett, Wandia & Siemion 2024 (arXiv:2411.19827,
"Conducting High Frequency Radio SETI using ALMA") on **TRAPPIST-1**, using ALMA
**Band 7**, spread across cluster cores, everything under a deletable `SETI/`
folder, with an EIRP estimate and a compute-time estimate.

## Data
- Project **2017.1.00215.S** (PI Marino), "Debris disks around UCDs, what lies
  beyond TRAPPIST-1h?", MOUS `uid://A001/X1273/X6bf`. PUBLIC.
- 6 execution blocks, raw total **295 GB**. 16 348 s on source, 43-44 antennas.
- TRAPPIST-1 is at the **phase centre** (no bycatch needed).
- Science spws 17,21,23,25. **spw 25 is the FDM SETI window**: 3840 ch x
  488.281 kHz spacing (976.56 kHz Hanning effective), 345.657-347.532 GHz.
  (spw 23 is a 128-ch TDM window - do NOT use it.)
- Only Gaia source in the 18" primary beam is TRAPPIST-1 itself (b = -57 deg)
  => N_star = 1.

## Where things live (ALL under /data/SETI on cluster astra-climate)
- `bin/` pipeline, `raw/` tars, `work/` scratch, `products/` results, `logs/`
- Local copies of code: `/workspace/SETI/bin/`
- Cluster: 224 cores, 220 GB RAM, /data 492 GB. Local /workspace is 98% FULL -
  never put ALMA data there.

## Pipeline
1. `step1b_calibrate.py <EB> --import` - importasdm (ocorr_mode='ca'), replay the
   pipeline's own flagdata commands from casa_commands.log, mstransform
   (reindex=False) to spw 25 + target/phasecal, applycal from the delivered
   calapply.txt, split.
2. `step2_extract.py` - direct DFT of visibilities to 603 sky positions
   (star + 1.1" ring + 512 control probes) for every integration & channel.
3. `step3_search.py` - spectral baseline removal, empirical per-channel rms from
   control probes, **Doppler de-drift search +/-6000 Hz/s** (179 trials).
4. `step4_combine.py` - combine EBs, EIRP, CWTFM, figures.
5. `pipeline_all.sh` - autonomous JIT download->calibrate->search->reclaim driver.

## KEY GOTCHAS ALREADY HIT (do not repeat)
- ALMA single-stream curl = 0.7 MB/s. **aria2c -x8 -s8 = 25-60 MB/s.** NAOJ
  mirror fastest. Parallel files give ~94 MB/s aggregate.
- ALMA tars preserve the whole project tree; the ASDM is ~6 levels down
  (find `**/ASDM.xml`).
- **Delivered CASA-5.1.1 flagversions CANNOT be restored in CASA 6.7** - row
  layout differs, `flagmanager restore` fails PART WAY and silently corrupts the
  FLAG column it already wrote. Replay casa_commands.log flagdata instead.
- calapply.txt uses pipeline shorthand `intent='TARGET'` etc. - CASA rejects it.
  Strip `intent=`; field selection is unambiguous.
- **AUTOCORRELATIONS**: split keeps them; ALMA gives them WEIGHT ~7.9e6 (4e5x the
  cross weights) and Re(V) ~13 Jy at u=v=0. They swamp SUM(w) and dilute any real
  signal. step2 now zeroes them via ANTENNA1==ANTENNA2. Fixing this improved
  sensitivity 21%.
- Set OMP_NUM_THREADS=1 in every worker: nested BLAS threads drove load to 1755
  and made step2 15x slower.
- `pkill -f <pattern>` kills my own ssh session if the pattern appears in the
  command line. Use a script file (`killsearch.sh`).
- scipy median_filter over 1e9 samples is unusable; use block-median + linear
  interpolation (`spectral_baseline`).

## VALIDATION (both passed)
- **Phase calibrator J2301-0158**: my independent DFT gives **470.00 mJy**; the
  ALMA pipeline's own setjy for the same EB/spw gives **471.12 mJy** -> **0.24%**.
  Weight consistency (measured scatter / predicted) = 1.18.
- Synthetic signal injection harness in step2 (`SETI_INJECT="Jy,Hz/s,chan"`).

## DOWNLOAD SPEED OPTIMIZATION (Aug 24, done after task completion, per Glenn's request)
**Full writeup + checklist: [`/shared/kb/skills/alma-archive-download.md`](/shared/kb/skills/alma-archive-download.md)** (team-shared, reusable for any future ALMA work).
- Empirically benchmarked (real transfers, `du`-based byte counting — `stat`/`ls` lie because
  aria2c sparse-preallocates): single stream 0.7 MB/s -> `aria2c -x8 -s8` 37-58 MB/s/file ->
  6 concurrent files one mirror 371 MB/s -> 6+3+3 across NAOJ+ESO+NRAO simultaneously **507 MB/s**.
- Checked Glenn's hypothesis that ESO/NRAO might beat NAOJ: **NAOJ was actually fastest** in every
  fair order-controlled test (cluster is in Singapore/GCP asia-southeast1 — Tokyo is just closer
  than Chile/Virginia). Splitting one file naively across all 3 mirrors is WORSE than the fastest
  mirror alone; the win is concurrent FILES weighted toward the fastest mirror, spilling overflow
  to the others once ~6 concurrent hit the per-mirror throttle ceiling.
- **Real bug found+fixed via live testing**: sustained (minutes-long) downloads can have aria2c's
  connection count silently collapse 8->1 without recovering (observed on ESO) — short benchmarks
  never reveal this. Fix = external watchdog restarting stalled downloads (confirmed CN:1->CN:8
  after restart). **Second bug caught+fixed**: watchdog wrote the "download done" marker on every
  restart even for partial files (40/52 GB) — now gated strictly on the `.aria2` control file being
  gone, since a wrong marker would have let the pipeline calibrate truncated data.
- New tools: `bin/mirror_pool_dl.sh` (weighted multi-mirror pool + watchdog, generic EBID/project
  handling) and `bin/pipeline_all.sh` v2 (prefetches EB[i+1]'s download while EB[i] calibrates —
  confirmed via live test that background download doesn't block the compute step). Not yet run
  through a full real production EB (would just redo already-banked results) but download-overlap
  mechanism and stall-recovery were both validated live on real ALMA transfers.

## RESULT SO FAR
- **EB A002_Xcccc19_X5564 (of 6): NO DETECTION.**
  rms 27.77 mJy/int (theory 25.01); de-drifted combined rms **1.277 mJy**;
  S_min(5s) 6.38 mJy; **EIRP_min = 5.80e13 W** at d = 12.467 +/- 0.011 pc.
  star peak SNR 4.60; empirical control ceiling 5.87 over 512 control positions;
  0 hits above SNR 5.
- Mason+24 got EIRP_min 6.91e17 W => this single EB is already **~1.2e4x deeper**.
- Drift physics: TRAPPIST-1b needs +/-4621 Hz/s at 346 GHz; the paper's
  +/-4 Hz/s@1GHz (=1386 Hz/s here) would MISS planets b and c.
