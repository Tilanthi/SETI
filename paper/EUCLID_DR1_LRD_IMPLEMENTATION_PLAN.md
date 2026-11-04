# Euclid DR1 Little Red Dots — IMPLEMENTATION PLAN v4 (2026-11-04)

Authors: Glenn J. White (Open University) with ASTRA PA. Status: plan v4 AGREED by Glenn 2026-11-04. Work packages NOT to be launched until Glenn gives the go-ahead.
Context: Q1 reproduction of Bisigello et al. 2025 (A&A 711, A24) completed 2026-11-04 (images: paper/LRD_Q1_reproduction_images.zip).

Decisions (Glenn, 2026-11-04): work Letter 1 (hot-dust / screened-quasar test) and Letter 2 (grism Balmer lines) TOGETHER, decide
later whether one Letter or two; selection = safest well-defined, justifiable choice (mine); disk/CPU managed by me within existing
space (cluster root ~119 GB free, Taurus /shared ≤3 GB; /data and SETI untouchable; no extra disk); public data only; Glenn's
likelihood re-implemented from paper_v1_06. Release: DR1-Foundation Thu 12 Nov 2026 (~1900 deg²).

## 0. Paper portfolio (v4 — adds Letter A, Glenn's original Project-5 programme)
 Letter A (FIRST, fastest): "The wide-area incidence of compact red V-shaped sources at 0.5<z<4 from Euclid DR1" — Glenn's original
   programme: VIS+Y/J/H catalogues; colour–colour selection ("V–J excess") + VIS-FWHM size cut; small morphological cutouts;
   cross-match to available spectra; surface density vs z and magnitude over ~1900 deg² (bright end, rare objects, field-to-field
   variance from independent N/S patches); "are JWST LRDs the tip of a ubiquitous population?" via (i) injection of JWST LRD SEDs
   → predicted Euclid density vs observed and (ii) Euclid∩JWST compactness/resolved fraction; exclusion-curve comparison only as
   context + pointer to Letter B. Defines and publishes the frozen sample that Letter B uses. Draft target Tue 17 – Thu 19 Nov.
 Letter B (= Letters 1+2 below): hot dust + Balmer lines on the same frozen sample; one Letter or two by the rule in §1. Draft ≥ Sun 22 Nov.
 Paper C (= Paper 3 below): full MNRAS census paper.
 Why A first: selection-based, no new machinery → numbers within 2–3 days of release; it is the paper the Euclid Consortium is most
 likely to race on; Q1 (63 deg²) only partly filled the wide-field gap (single-object bright-end bins) — DR1 is ~30× the area.
 Letter A safeguards: "V–J" defined in OBSERVED Euclid colours (rest V–J is not reachable from Euclid at z>0.6; rest J needs WISE);
   colour box designed a priori from redshifted JWST LRD SEDs + star/brown-dwarf/quasar/dusty-galaxy loci and pre-registered;
   contamination measured (GOODS-S/JWST, deep fields with IRAC) and densities quoted as upper limits where purity is uncertain;
   no overlap of results with Letter B (the full hot-dust test lives only in B).

## 1. Science goal and the paper decision (Letter B, and Paper C)
Question: what makes the red optical light of compact V-shaped sources at cosmic noon, and are they the same phenomenon as JWST LRDs?
Two independent tests on ONE frozen sample:
 T1 (hot dust, continuum-normalised, "P-test"): rest ~1.5–3 µm (WISE W1/W2, W3 for the brightest) per unit observed rest-optical
    continuum vs SDSS quasars at the SAME rest wavelength; screen prediction K_P(A_V, λ) (Cardelli R_V=3.1 as paper_v1_06, G23/F19 as
    systematic); signed fluxes incl. non-detections; mixture likelihood; mock-calibrated 97.5% limits on K_med and screened fraction q.
 T2 (Balmer lines, Euclid NISP red grism 1.21–1.89 µm): broad Hα (z≈0.84–1.88), Hβ+[OIII] (1.48–2.89), Balmer decrement (1.48–1.88),
    individually for the bright end, stacked otherwise; plus DESI/SDSS spectra. Gives broad-line fraction, line widths, decrement,
    and the Hα-normalised T1 variant ("Q-test", as in paper_v1_06).
Paper decision rule (provisional at the Q1 pilot, final at release+5 days, Tue 17 Nov):
 ONE Letter "Hot dust and broad Balmer lines in ~N Euclid little red dots at 0.5<z<3" if T2 gives a usable broad-line subsample
 (≥10 individual broad Hα or ≥5σ stacked broad component) AND both fit in 5 pp (≈4 figures: sample/density; T1 measurements;
 T2 spectra/stacks; joint exclusion curve q vs A_V with the z≈3.5–8 MIRI limits). Otherwise: Letter 1 = T1; T2 goes to Letter 2
 (if strong) or into Paper 3. Paper 3 (full MNRAS census: catalogue, bright-end LF, JWST "tip of the iceberg" comparison,
 Euclid∩JWST compactness, clustering, X-ray/radio stacks, Bisigello reproducibility notes) follows in either case.

## 2. Selection — "safe and well defined" (frozen and pre-registered BEFORE DR1 opens)
Principle: use only criteria that are already published and justified, fix every free choice on Q1 (never on DR1), write the
specification to a file, hash it and commit it before 12 Nov — the analysis on DR1 then cannot tune the sample to the answer.
S1 Reliability: Euclid pipeline flags exactly as reproduced in Q1 (DET_QUALITY_FLAG=0, SPURIOUS_FLAG=0, FLAG_* =0 in VIS,Y,J,H,
   NIR_STACK; PHZ_CLASSIFICATION≠1; tile has PHZ). Star/brown-dwarf removal additionally by Gaia proper motion/parallax and the
   brown-dwarf colour locus.
S2 Detection: S/N>3 in ≥4 bands with ≥2 rest-UV and ≥2 rest-optical (λ_eff side of 3645 Å) — Bisigello+25, reproduced exactly on
   Table 8. PLUS an analysis floor HE ≤ H_lim (set from the Q1 pilot so WISE/grism measurements are meaningful; frozen).
S3 V-shape: Kocevski+24 slope criteria (β_opt>0, −2.8<β_UV<−0.37), our validated two-power-law fit (fixed: flux-only aperture
   correction, z within PHZ modes, Lyα cut-off; documented in RECIPE.md). These are the JWST-standard criteria → direct comparability.
S4 Compactness: MUMAX_MINUS_MAG<−2.6 (Euclid pipeline point-source criterion, as Bisigello). VIS-FWHM/PSF ratio is reported and used
   as a systematic, with its contamination measured in GOODS-S (Euclid EDF-F ∩ JWST).
S5 Mid-IR: NOT used in selection (it is the test). Line-emitter veto: as written in Bisigello (conservative); reversed version = systematic.
S6 χ²<100. No visual inspection in the main sample (irreproducible); an automatic artefact flag set + a visual check of a random 5%
   to quantify residual artefacts.
Letter-A colour sample (pre-registered with the rest): observed colour–colour box — red IE−JE / JE−HE ("V–J excess") together with a
blue rest-UV (IE−YE or ground g/r−IE) — + S1 + VIS-FWHM size cut (VIS FWHM / local PSF FWHM ≤ threshold, threshold set on GOODS-S where JWST
resolves the sources) + S4. Box boundaries derived beforehand from JWST LRD SED tracks at z=0.5–4 and contaminant loci; never tuned on DR1.
Its overlap with the fit-based (S1–S6) sample is quoted; both are published so readers can reproduce either from the catalogue alone.
Controls (needed for the tests): (i) compact non-V-shaped sources matched in HE and z; (ii) SDSS/DESI/Milliquas quasars inside DR1
(Euclid photometry + WISE measured identically); (iii) blank-sky positions for WISE and grism noise models.

## 3. Work packages (all on the cluster unless stated; subruns in parallel; reports in /workspace/LRD/reports/)
WP-A Infrastructure & ingest (Wed 4 – Fri 6 Nov)
 A1 git repo for all LRD code; disk ledger /srv/euclid_lrd/LEDGER.tsv + guard (refuse writes if root free <30 GB); job launcher that
    checks load and allocates cores (≤200, ≥16 left free, nice 10 for long jobs).
 A2 Ingest via IRSA HATS/Parquet (column projection + row pre-cuts + HEALPix count maps), timed on Q1; schema-diff tool; fallbacks
    (per-tile FITS streaming — proven; ESA archive TAP). Day-0 runbook.
WP-B References & archives (Wed 4 – Sat 7)
 B1 DR1 footprint → HEALPix mask (digitised; replaced by DR1 MOC on day 0); overlap matrix with all candidate archives; ranked list.
 B2 Mirror now (CDS/IRSA unreliable): SDSS DR16Q + Wu & Shen 2022 line catalogue + AllWISE/unWISE fluxes for the quasar reference;
    Milliquas; public JWST LRD catalogues (Kocevski, Kokorev, Akins, Perger, RUBIES/Hviding, low-z analogues); DJA catalogue/spectra
    index; DESI DR1 redshift catalogue (footprint); Gaia DR3 (footprint, slim); Bisigello Table 8 + our Q1 candidates.
 B3 (Paper 3, lower priority) eROSITA DR1, 4XMM, CSC, RACS/EMU, VLASS, LoTSS catalogues within footprint (small).
WP-C Mid-IR photometry engine (Wed 4 – Sun 8)
 C1 unWISE coadds streamed per tile (download → photometer → delete): forced PSF photometry at Euclid positions with simultaneous
    fitting of Euclid-detected neighbours within ~15″ (6″ PSF), signed fluxes, blank-sky noise model (heavy tails, as paper_v1_06),
    injection-recovery response. Optional LS-DR10 forced unWISE values as a cross-check in the south.
 C2 Truth test on Q1 deep fields: compare with Cosmic Dawn IRAC ch1/ch2 (re-fetch EDF-F/EDF-N ch1-2 only, ~4 GB, deleted after).
WP-D Likelihood re-implementation (Thu 5 – Mon 9)
 D1 Ratios P(λ_rest) (and Q with grism Hα) per object; reference quasars at matched rest wavelength; K_P(A_V, λ) for each object.
 D2 Mixture likelihood (lognormal main + screened/uniform component), profile-likelihood limits, mock catalogues on the real noise
    and coverage, calibrated thresholds t*, validation grid — reproduce paper_v1_06's numbers on its own published inputs where
    possible as a unit test.
WP-E Grism engine (Thu 5 – Mon 9)
 E1 Q1 SIR 1D spectra by object (range reads from S3), contamination/quality flags, line fits (narrow + broad Hα/[NII], Hβ, [OIII],
    [SII]), z registration; stacking in z/M bins with bootstrap; Balmer decrement and broad fraction. DESI/SDSS spectrum fetch.
WP-F Selection, controls, selection function (Thu 5 – Tue 10)
 F1 Implement S1–S6 + companion + controls; Gaia/brown-dwarf rejection.
 F3 Letter-A colour box: JWST LRD SED tracks (Kocevski/RUBIES/DJA spectra) through Euclid+ground filters at z=0.5–4 vs loci of stars,
    brown dwarfs, quasars (Milliquas/SDSS), dusty star-forming galaxies, line emitters; choose box + VIS-FWHM threshold on Q1/GOODS-S; freeze.
 F4 Letter-A census pipeline: HEALPix surface-density maps vs z and magnitude (N/S, field-to-field/jackknife variance, depth/mask
    corrections), cutout galleries, spectra cross-match counts (Euclid grism, DESI, SDSS, JWST/DJA); run end-to-end on Q1.
 F2 LRD-SED injection (Kocevski β distributions + DJA LRD spectra) through Euclid Wide depths/PSF and WISE depths → completeness and
    predicted JWST-like density at 0.5<z<4; GOODS-S compactness contamination measurement.
WP-G Q1 pilot = full dress run of the science on Q1 (Sun 8 – Mon 9)
 T1 + T2 on Q1 candidates + controls + quasars. Report: achieved sensitivity vs the A_V=3 prediction (GO if ≥5σ for Q1 →
 decisive for DR1), grism yield (GO criteria §1), provisional one-vs-two-Letter decision, H_lim choice.
WP-H Freeze & rehearsal (Tue 10 – Wed 11)
 Write SELECTION_SPEC.md, hash + commit (pre-registration); end-to-end rehearsal on Q1 from a clean directory under the ledger and
 CPU budget; tag dr1-ready. Draft Letter sections that do not depend on DR1 numbers (intro, data, method, tests' definitions).

## 4. Release day and after
Thu 12 Nov (day 0): watch IRSA bucket + ESA archive; schema diff; DR1 MOC → footprint; launch ingest with pre-cuts (~6–7 TB read,
 ~5–8 h at Q1 throughput; stored: candidate superset + controls + count maps only).
Day 1–2: Letter-A census numbers first (densities, maps, galleries, spectra matches); frozen selection; WISE forced photometry for sample + controls + quasars; grism spectra; Euclid cutouts; first numbers.
Day 2–5: T1 likelihood + mocks; T2 fits + stacks; joint exclusion curve; one-vs-two-Letter decision (Tue 17 Nov).
Day 5–7: Letter A draft to Glenn (target Tue 17 – Thu 19 Nov). Day 7–10+: Letter B draft(s); then Paper C.

## 5. Disk plan (hard limit ~119 GB free on cluster root; keep ≥30 GB free → ≤85 GB in use; Taurus ≤3 GB)
| item | peak GB | lifetime |
|---|---|---|
| Q1 HATS superset + controls + count maps | 3 | until rehearsal done |
| Q1 grism spectra (candidates+controls) | 2 | until rehearsal done |
| Cosmic Dawn IRAC EDF-F/N ch1-2 (truth for C2) | 4 | deleted after C2 |
| unWISE tiles in flight (streamed) | 5 | transient |
| reference sets (quasars+WISE, Milliquas, JWST LRDs, DESI zcat, Gaia slim) | 8 | kept |
| B3 X-ray/radio catalogues | 2 | kept |
| DR1 candidate superset + controls, full columns | 10 | kept |
| DR1 count/depth maps | 1 | kept |
| DR1 WISE photometry + grism spectra + cutouts | 10 | kept |
| scratch (RAM /dev/shm preferred) | 0–10 | transient |
| total peak | ≈ 45–55 | |
Rules: ledger entry per job (expected vs actual); guard aborts at <30 GB free; raw data streamed and deleted per partition;
parquet+zstd only; daily ledger review; anything re-downloadable and unused for 48 h is deleted.

## 6. CPU plan (224 vCPU, 220 GB RAM, shared machine)
Launcher checks load first; ≤200 cores; ≥16 free; nice 10 for long jobs. I/O-bound jobs (ingest, unWISE/grism/cutout fetches)
use 32–64 network streams on few cores and run concurrently with CPU-bound jobs (fits, forced photometry, mocks, injections,
stacks), which are chunked, checkpointed and resumable, sized from Q1 benchmarks. Mock calibration grids fill idle cores.
DR1 estimate 1–3 k core-h (fits ~1.4 ms/object/core; forced WISE photometry and mocks dominate).

## 7. Risks
Archive outages → mirror now, retries, ESA fallback. DR1 access lag/schema change → ready runbook + diff. Faint sample → bright-end
floor + stacks. WISE 6″ blending → neighbour-modelled forced photometry, validated against IRAC. Rest wavelength ~1.5–2.5 µm (not
3 µm) at z≈1–2 → reference quasars at matched λ, host-starlight term tested with compact non-V controls. Grism contamination
→ quality flags + stacks + controls. Competition → speed and pre-drafted text.

## 8. Calendar
Wed 4–Fri 6: WP-A, WP-B, WP-C start; D/E start Thu.  Sat 7–Mon 9: C/D/E/F complete; Q1 pilot (WP-G) Sun–Mon; report to Glenn Mon 9.
Tue 10–Wed 11: freeze + pre-register selection (incl. Letter-A colour box), rehearsal, Letter A + B skeletons.  Thu 12: DR1.
Tue 17: Letter-B one-or-two decision.  Tue 17–Thu 19: Letter A draft.  ~Sun 22 onwards: Letter B draft(s); then Paper C.
NOTHING is launched until Glenn gives the go-ahead.
