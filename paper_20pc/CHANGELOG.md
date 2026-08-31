# Version history — "A Volume-Limited Search for Technosignatures within 20 pc"

Each version lives in its own subfolder (`v1.00/`, `v1.01/`, ...) so any
previous version can be recovered without relying on git history alone.
Bump the **minor** number (1.00 → 1.01) for content edits/additions within
the same broad draft stage; bump the **major** number (1.x → 2.00) once
Paper II's actual results/discussion/conclusions sections are added.

## v1.00 (2026-08-30)
- First draft. MNRAS-format LaTeX (official `mnras.cls`/`mnras.bst` v3.2
  from CTAN), authors Glenn J. White & Robin Dey.
- **Content**: full Introduction and Background/Literature Review sections
  (six decades of radio SETI history; modern large-scale surveys —
  Breakthrough Listen, FAST, LOFAR/NenuFAR, Sardinia Radio Telescope, ATA,
  commensal VLA/MeerKAT/MWA systems; the very small mm/submm literature,
  centred on Mason et al. 2024's ALMA Band 3 bycatch survey and our own
  prior TRAPPIST-1/100-star pilot work; machine-learning/anomaly-detection
  approaches (Ma et al. 2023 deep learning, GLOBULAR clustering, Parkes/GBT
  anomaly search); statistical frameworks for interpreting non-detections
  (Wright et al. 2018 Cosmic Haystack, Sheikh 2020 nine axes of merit,
  Margot et al. 2023 representative-sample formalism); the explicit case
  for a volume-limited, disc/planet-status-agnostic sample; and prospects
  for SKA/ngVLA). Sample Selection and Data/Methodology sections summarise
  the already-established 20pc target list and pipeline design. Results,
  Discussion and Conclusions sections are NOT yet written — this version
  is background/motivation only, as instructed.
- All literature citations were individually verified against arXiv
  listing pages (author lists, years, journal/volume/page or arXiv ID)
  before inclusion — several initial draft citations had incorrect
  author attributions from search-snippet-only research and were
  corrected against the primary source before this version was finalised.
- 6 pages, clean compile, no undefined references, no overfull boxes.
- Pushed to `Tilanthi/SETI` GitHub repo.

## v1.01 (2026-08-30)
- **Journal target corrected**: Glenn confirmed the paper will likely go to
  the **Open Journal of Astrophysics (OJA)**, not MNRAS as originally
  assumed. Re-typeset using OJA's official `openjournal.cls`
  (http://www.thphys.nuim.ie/staff/pcoles/openjournal.cls, v09/06/15,
  AASTeX/emulateapj-style, built on `revtex4-1`) instead of `mnras.cls`.
  **Content is otherwise identical to v1.00** — same title, authors,
  abstract, full Background/Lit-Review text, Sample Selection, Methodology,
  Scope-of-Paper-II placeholder, and the same (corrected, individually
  verified) ~30-entry bibliography — only the document class, front-matter
  markup (`\shorttitle`/`\altaffilmark`/`\altaffiltext` instead of MNRAS's
  `\author[]{}`/`\pubyear`), and resulting page layout (OJA is single-column
  AASTeX-style vs MNRAS's two-column) changed.
- Dependencies: `openjournal.cls` requires `revtex4-1.cls` (now installed on
  this container via `apt-get install texlive-publishers`; NOT bundled in
  the repo since it's a standard TeXLive component, unlike the one-off
  `openjournal.cls` itself, which IS bundled per-version for
  recoverability) and the small legacy `epsf.sty` (bundled in `v1.01/`,
  fetched from `fits.gsfc.nasa.gov/standard30/epsf.sty` since it is not in
  this container's TeXLive install and CTAN's own mirrors served an HTML
  error page for the direct .sty path tried first).
  Kept natbib-compatible `\citet`/`\citep` and `\bibitem[Author(Year)]{key}`
  bibliography entries unchanged from v1.00 — `openjournal.cls` restores
  natbib internally, so no citation-syntax changes were needed, only the
  front matter.
  6 pages, clean compile (pdfLaTeX only needed, no BibTeX step — bibliography
  is a manual `thebibliography` block, same as v1.00), 1 negligible 3pt
  overfull \vbox (page-break rounding, not a real content overflow).
- **v1.00 (MNRAS-format) is now superseded but kept in place** for the
  record, per the "any previous version can be recovered" versioning policy
  — do not delete it.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v1.01/`.

## v2.00 (2026-08-30)
- **Major restructure, per Glenn's instruction**: "Paper I" and "Paper II"
  are no longer separate — this is now a single, standalone paper that is
  updated in place as the survey progresses, rather than a background-only
  piece promising results in a future companion paper. All "Paper I of a
  series"/"will be presented in Paper II" language removed from title,
  abstract, introduction, and the old placeholder "Scope of Paper II"
  section (§5) is replaced with real content.
- **New content**:
  - §4.1 Closure-phase point-source vetting, §4.2 Population-level
    spectral-type-normalised continuum anomaly check — full methodology
    write-ups of the two new analyses added to the live pipeline this
    session (see MEMORY.md 2026-08-30 07:25 entry for implementation
    details). Both explicitly framed as novel relative to the entire
    technosignature literature reviewed in §2, not just re-implementations
    of Ma et al./GLOBULAR/Poznanski.
  - §5 Results (real, current data): pulled and rigorously filtered actual
    campaign output — 26 target/bands had *some* data on disk, but 7 of
    those were STALE, pre-fix results for targets on the known
    "needs-redo" list (multi-field/phase-centre/mosaic-continuum bugs,
    or old pre-budget-fix timeouts) that the volume-limited campaign
    hasn't reprocessed yet (it's still working through nearer targets
    first) — these 7 were explicitly excluded from every statistic and
    from the appendix table, not silently included. Final dataset: 19
    valid target/bands. Caught and correctly explained, not silently
    reported as anomalous: (a) the one flagged "candidate" (β Pictoris,
    Band 3, 115.26 GHz) is the CO(1-0) line; (b) G 272-61A/B showing
    bit-identical continuum flux is NOT a bug recurrence — verified via
    `calibrate_status.json` that both share one single-field MOUS with
    `target_field=uv_cet`, i.e. these ARE the two components of the
    well-known UV Ceti visual binary, genuinely unresolved by ALMA at
    this configuration — flagged as an honest caveat, not excluded.
  - §6 Discussion, §7 Conclusions — new, grounded in the actual (partial,
    honestly labelled as preliminary — 19/120 = 16%) results.
  - Appendix A (`Table~1`, `tabularx`-based for proper text wrapping —
    plain `tabular` overflowed the page width by ~68pt on first attempt,
    caught by the standard `Overfull \hbox` log check and fixed): full
    per-target table (target, band, distance, frequency range searched,
    EIRP_min, candidate flag, continuum value, notes) — kept OUT of the
    main body per Glenn's explicit instruction; main text has summary
    statistics and two figures only.
  - Figure 1: EIRP and continuum vs. distance (two-panel), Figure 2:
    full 120-star sample distance distribution — both generated from real
    pipeline output, not illustrative/mock data.
- **Process notes**: gathered fresh data directly from the cluster
  (`/data/SETI/logs/driver_summary_master20pc.json` + all
  `*_result.json`/`continuum_summary.json` files), built a local
  `paper_data.json` → filtered → `paper_data_valid.json` pipeline so the
  filtering-out of stale data is itself reproducible/auditable, not a
  one-off manual edit.
- Verified with the full compile-3x + `pdftotext | grep "??"` = 0 discipline
  established after the v1.01 unresolved-references incident, on a
  completely clean rebuild (deleted the PDF and recompiled from scratch)
  as the final check before packaging for push.
- 9 pages, clean compile, 1 negligible 3pt page-break `Overfull \vbox`
  (not a content defect).
- **v1.00 and v1.01 kept in place**, superseded but recoverable, per the
  standing versioning policy.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.00/`.

## v2.01 (2026-08-30)
- Glenn: Figure 2 should be a cumulative plot (total number of stars out
  to distance $d$) rather than a binned histogram of counts per bin.
  Regenerated from the same underlying 120-star master list as a step
  plot of $N(<d)$ vs.\ $d$; updated the figure caption to describe the
  cumulative curve (steepening reflects increasing shell volume at larger
  $d$) rather than the old per-bin-count description. No other content
  changed from v2.00.
  Verified with the same compile-3x + zero-`??` + visual-render check as
  every version since the v1.01 incident. 9 pages, clean, 1 negligible
  page-break `Overfull \vbox`.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.01/`.

## v2.02 (2026-08-30)
- Glenn asked a clarifying question: does Figure 2 (and the "120-star
  volume-limited sample") represent the total stellar population within
  20 pc, or just the subset with ALMA archival coverage? Answer: the
  latter — this was already stated in words in §3, but Figure 2 itself
  didn't make the completeness gap visually or numerically explicit, and
  one leftover "Paper II" reference from the pre-merge draft (§2.6) had
  never actually been given a real number to point to.
- **Computed the real completeness fraction**: cross-matched the 120-star
  sample against our own reference Gaia DR3 catalogue of the solar
  neighbourhood — 2357 individually catalogued stars within 20 pc, of
  which our sample is only ~5.1%.
- Rebuilt Figure 2 as two cumulative curves on a log axis: the full
  2357-star Gaia census (grey) vs. our 120-star ALMA-covered sample
  (blue), with the completeness fraction annotated directly on the plot.
  Rewrote the caption to state explicitly that the two curves are not
  expected to track each other, since ALMA proposal pressure on the solar
  neighbourhood is not spectral-type- or distance-uniform.
- Added an explicit paragraph to §3 (Sample Selection) and tightened the
  Abstract's and §2.6's wording: the sample is volume-limited and
  unbiased *within* the ALMA-observed population, but is NOT a complete
  census of the local stellar neighbourhood — stated plainly rather than
  left for a reader to assume from the word "volume-limited" alone. Fixed
  the leftover "we quantify explicitly in Paper~II" reference (missed in
  the v2.00 merge) to point to the actual §3 discussion with the real
  number.
- Verified with the standard compile-3x + zero-`??` + visual-render
  discipline. 9 pages, clean, 1 negligible page-break `Overfull \vbox`.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.02/`.

## v2.03 (2026-08-30)
- Glenn raised three substantive, well-founded questions after reading
  v2.02 closely:
  1. **Spectral window coverage**: does the narrowband search cover every
     correlator sub-band configured together, or just one? Verified
     against real data (`calibrate_status.json` per target): ALMA
     configures 4-24 spectral windows simultaneously per observation in
     our sample (median 4; tau Cet's spectral-scan setup has 24), and we
     only ever search the single finest-resolution one — meaning, on
     average, only ~23% (range 4-25%) of the instantaneously configured
     spectral windows are actually searched narrowband. Added an explicit
     paragraph to §4 stating this with real numbers, and a new N$_{\rm
     spw}$ column in the Appendix table giving the exact count per
     target, rather than leaving it as an aggregate-only statement.
  2. **Continuum upper limit definition**: "(UL)" wasn't quantitative
     enough — is it 1σ, 3σ, 5σ, the raw measurement? Fixed by (a)
     explicitly restating throughout that a UL = 5×rms (the same
     threshold used to define a detection), (b) adding an explicit RMS
     (mJy) column to the Appendix table so the underlying measurement is
     given directly, not just the pre-multiplied 5σ value, letting a
     reader rescale to any confidence level they want, (c) switching from
     the ambiguous "X.XXX (UL)" notation to the standard astronomical
     "$<$X.XXX" convention.
  3. **EIRP context**: added a new §4.1 "Reference transmitter
     benchmarks" citing two real, precisely-sourced values from
     \citet{EarthDetectingEarth2025} — an Arecibo-like planetary radar
     ($2\times10^{13}$ W, the most powerful deliberate transmitter humans
     have built) and typical unintentional Earth radio leakage
     ($\sim4\times10^{9}$ W, LTE/cellular). Both added as horizontal
     reference lines on Figure 1's EIRP panel, with matching discussion
     in §5.1 (Results): our deepest limits are only just competitive with
     an Arecibo-equivalent transmitter at the very nearest handful of
     stars, and nowhere near sensitive enough yet to detect
     Earth-leakage-equivalent activity at any distance probed so far — an
     honest, useful calibration of what the survey can and cannot claim.
- Precise sourcing: fetched the actual Sheikh et al. (2025) "Earth
  Detecting Earth" paper text rather than relying on memory for these
  numbers — confirmed "Arecibo's characteristic EIRP at S-band is 20 TW"
  and the 4 GW LTE-leakage figure directly from the source text before
  citing either.
- Verified with the standard compile-3x + zero-`??` + visual-render
  discipline. 10 pages (grew by 1 from the new benchmarks subsection),
  clean, 1 negligible page-break `Overfull \vbox`.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.03/`.

## v2.04 (2026-08-30)
- **Pipeline extended to search every configured spectral window, not just
  the finest one.** `select_finest_spw.py` rewritten to enumerate *all*
  distinct spws per observation (deduplicated across repeated execution
  blocks, capped at 8/target to bound compute cost), splitting each to
  its own MS; `process_one_target.sh` now loops the extract+search steps
  once per spw (via the pre-existing `SETI_MS`/`SETI_SFX` env-var
  override mechanism, previously used only for injection tests);
  `seti_drift_search_generic.py`'s closure-phase-vetting MS path fixed to
  respect the `SETI_MS` override (was hardcoded, would have silently
  vetted against the wrong MS once multi-spw naming took effect).
  `SETI_SEARCH_FAILED` now only fires if *all* spws for a target fail,
  not just the first.
- **19 already-completed targets identified as needing full
  reprocessing** (not cheap re-analysis) since their raw per-spw MS data
  had already been cleaned up under the project's disk-discipline policy
  before the multi-spw extension existed. Confirmed with Glenn
  ("Yes, they should be requeued") and requeued: DONE/failure markers
  cleared for all 19, `driver_summary_master20pc.json` trimmed
  accordingly, and a `chain_multispw_repeat.sh` wrapper launched that
  waits for the main 120-target driver to finish before automatically
  re-running the multi-spw pipeline against just those 19.
- **Table 1 (Appendix) restructured** per direct instruction:
  - Added a **Spectral Type** column immediately after Dist. (pc),
    sourced from Gaia GSP-Phot-derived Teff/radius where available and a
    literature-value override (`LITERATURE_SPTYPE`) for five well-known
    stars lacking Gaia atmospheric parameters (Wolf 359, Sirius B, and
    the UV Ceti AB pair), each individually WebSearch-verified against a
    named literature source.
  - **Band numbers now given without the "B" prefix** (e.g. "6" not
    "B6") to avoid visual confusion with B-type spectral classes now
    sitting in the adjacent column; caption states this explicitly.
    Also backfilled 5 previously-blank Band cells (tau Ceti, GJ 581,
    GJ 849, HD 285968, HD 53143 — all inferred as Band 6 from their
    211–275 GHz observed frequency range, consistent with the pipeline's
    own band-edge lookup table).
  - **"Cand." column dropped** (redundant with the Notes-column flag
    already given for the one automatically-flagged candidate).
  - **Flux and RMS columns swapped** so Flux (mJy) now precedes RMS
    (mJy).
  - Notes column and Appendix intro text updated to explicitly flag,
    per-row, which of the 19 target/bands are legacy single-window
    results now queued for multi-window reprocessing.
- §4 (Data and methodology) rewritten to describe the new multi-window
  search explicitly (superseding the old "we search only the single
  finest-resolution spectral window" statement), and to note that once
  several windows have been searched per target, Figure 1 will continue
  to plot only the single deepest (lowest EIRP$_{\rm min}$) result per
  target/band, to avoid crowding the plot — per direct instruction.
- Verified with the standard compile-3x + zero-`??` + visual-render
  discipline (rendered and inspected the table and Figure 1 pages
  directly, not just grepped the log). 10 pages, clean, only a
  negligible 4pt page-break `Overfull \vbox` and expected underfull
  hboxes from narrow Notes-column word-wrapping in `tabularx`.
- **Live validation gap, noted honestly**: the new multi-spw search code
  has been deployed and syntax-checked but had not yet been exercised
  end-to-end on real ALMA data at the time of this push — the one live
  target being processed under the new code (`LSR_J1835-3259`, Band 3)
  turned out to be an unusually large/complex case (33 GB raw MS, ~65
  configured spws) still in calibration after 40+ minutes. Will confirm
  correctness on the next update once that target (or a smaller one)
  completes, before treating the 19-target repeat pass as trustworthy.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.04/`.

## v2.05 (2026-08-30)
- **Abstract cut to ~1/3 length** (316 → 111 words), per direct instruction.
- **Citation fix**: `(White & Dey, in prep.; archived at
  https://github.com/Tilanthi/SETI)` → `\citep{White2026}` = "(White 2026)";
  added `White G. J., 2026, MNRAS, submitted` to the bibliography.
- Removed the parenthetical `(an "ichnoscale" of unity)` aside in §2.5.
- **New methodology paragraph**: automated spectral-line-contamination
  check. Added `check_known_line()` to `seti_drift_search_generic.py`,
  cross-referencing every hit's frequency (at its best-fit drift rate)
  against the same known-molecular-transition table already used by
  `continuum_map_generic.py`'s line exclusion; a hit within one channel
  width of a known line AND consistent with zero drift is now
  automatically flagged `likely_line_contamination` and excluded from
  `credible_technosignature_candidate` — previously this check was only
  ever done by hand, once, for the one hit produced so far (β Pic CO(1-0)).
- **New methodology paragraph**: confirmed and made explicit (i) the
  drift/frequency-shift correction has no dependence on the target's
  position relative to the phase centre (verified directly from the
  code: the trial-drift shift grid depends only on elapsed time/channel
  width, applied identically to every sky position); (ii) Earth's own
  orbital-motion-induced drift (~0.02 Hz/s/GHz peak) is >100x smaller
  than the 12 Hz/s/GHz generic search margin, so needs no separate
  correction.
- **Primary-beam correction — found not implemented, now added**: neither
  the EIRP nor the continuum pipeline had ever applied a primary-beam
  correction (`tclean(..., pbcor=False)`, and no PB term anywhere in the
  DFT-based narrowband extraction). Added an explicit Gaussian-PB
  correction (`1/exp(-4 ln2 (offset/FWHM)^2)`) to both
  `seti_drift_search_generic.py` (new `S_min_measured_Jy`,
  `primary_beam_offset_arcsec`, `primary_beam_atten`,
  `primary_beam_corrected` fields; `S_min_Jy`/`EIRP_min_W` now
  PB-corrected) and `continuum_map_generic.py` (new
  `primary_beam_correction`/`primary_beam_corrected` fields; `rms`/`peak`
  corrected before both the PNG title and JSON summary are written).
  Quantified impact: negligible (<0.3%) for nearly all targets (offsets
  ≲2″ against 17–70″ beams), but 3.6–16% for Sirius~B specifically
  (7–8″ offset, high proper motion since the archival epoch) — its three
  Table 1 rows (B3/B4/B5) recomputed by hand with the correct factor,
  since its raw MS data has already been cleaned up and can't be cheaply
  rerun. UV Ceti's own ~2″ offset gives a merely 0.2% (negligible)
  correction, confirmed and left unchanged.
- **Found and fixed a second live pipeline bug while implementing the
  above**: `continuum_map_generic.py` had no equivalent of the
  narrowband path's crossmatch/pointing sanity check. Caught live:
  G~9-38A/B produced a bogus ~8 Jy "detection" (wildly inconsistent with
  every other continuum measurement in the survey, all sub-10 mJy) from
  a MOUS whose real pointing is ~3150″ from the star (>40x its own 70″
  beam) — an upstream target-MOUS crossmatch error, not a real result.
  Also caught for SCR~J1845-6357 (offset 205499″) and Wolf~358
  (offset 65590″, a *different* star from Wolf 359, dist 6.97 pc vs
  2.41 pc). Added the same `>2x primary beam FWHM → abort` check already
  used by `seti_extract_generic.py`. These 4 target/bands are excluded
  from Table 1 and all statistics in this version; flagged in §5/§6 for
  re-investigation and reprocessing against a corrected dataset.
- **Table 1 updated with new/corrected values**:
  - "NAME Barnard's star" → "Barnard's Star" (the literal SIMBAD
    identifier-type prefix had leaked into the target list/paper).
  - Sirius B (B3/B4/B5): primary-beam-corrected EIRP/Flux/RMS (see above).
  - GJ 581: now 4 rows (all configured spectral windows searched, no
    candidate in any) — the first target/band with full multi-window
    coverage under the pipeline extended in v2.04.
  - tau Ceti: refreshed with a freshly-reprocessed measurement (same
    correlator setup, consistent with the prior value).
  - Two new target/bands added: **HD 33793** = Kapteyn's Star (subdwarf
    sdM1, 3.93 pc) and **Wolf 28** = Van Maanen's Star (white dwarf DZ7,
    4.31 pc) — both literature spectral types confirmed via WebSearch.
  - Table caption/intro clarify EIRP$_{\rm min}$'s exact definition
    (minimum EIRP for a 5σ detection, same threshold and PB-correction
    as the continuum column) per direct instruction.
  - All summary statistics in Abstract/§5/§6 recomputed for consistency:
    21 of 120 target/bands (was 19); EIRP median 3.1e14 W (was 2.1e14,
    driven up mainly by GJ 581's four new ~6e14 W values); continuum
    5 detections/16 non-detections (was 5/14), median UL 0.55 mJy.
- **Figure 1**: Earth-radio-leakage reference line removed from the EIRP
  panel (now shown only in caption + main text) so the y-axis auto-scales
  to the actual data range; Arecibo-radar line kept. Regenerated with all
  19 current EIRP points (deepest-per-spw for GJ 581, per instruction)
  and 21 continuum points.
- Verified with the standard compile-3x + zero-`??` + visual-render
  discipline; caught and fixed one caption self-reference bug
  (`\S\ref{app:table}` should have been `\S\ref{sec:method}`) and one
  factual slip (initially over-stated the negligible UV Ceti PB
  correction as if it matched Sirius B's) before finalizing. 11 pages.
- Live cluster validation: the new `continuum_map_generic.py` crossmatch
  check and PB correction have been deployed and syntax/unit-tested but
  not yet exercised end-to-end on a fresh live target at push time (the
  fix landed after GJ_581_B6/Wolf_358_B7 had already completed under the
  pre-fix code) — flagged honestly as an open verification item, same as
  the analogous v2.04 gap, which *was* subsequently confirmed correct.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.05/`.

## v2.06 (2026-08-31)
- **Four new/extended analyses added**, per Glenn's explicit request for
  "Tier 1" scientific-usefulness additions that reuse already-downloaded/
  already-retained data at essentially zero marginal cost:
  1. **Injection-recovery sensitivity validation** (§4.4): synthetic
     narrowband tones (1–10× the noise level, 24 trials, 3 channel
     positions per amplitude) injected into Proxima Cen's own
     already-validated calibrated MS (reusing the extraction code's
     existing `SETI_INJECT` mechanism) and recovered through the
     unmodified search pipeline. Finding: recovered SNR is ~10% below
     injected at high SNR (small, expected coherence loss); the actual
     50%-recovery point sits at injected SNR≈6, not the nominal 5σ design
     value — i.e. our quoted 5σ limits are, if anything, mildly
     *conservative*. Single-target pilot; broader multi-band campaign
     recommended as future work.
  2. **Chirped-drift + periodicity re-analysis of retained spectra**
     (§4.5, new `reanalyze_srcspec.py`): extends the primary linear-drift
     search with (i) a quadratic-drift (chirp) term and (ii) a
     time-domain FFT periodicity/pulse search, both run entirely off the
     already-retained `*_srcspec.npz` files (star + 8 controls) — no
     re-download, no CASA. Applied to all 79 retained spectra to date:
     8 (10%) chirp-credible, 10 (13%) periodicity-credible, both
     statistically indistinguishable from the ~11% expected purely by
     chance from a 1-vs-8-control "max" comparison. Clean null result;
     validates the star-vs-control differencing design (caught, and
     correctly rejected, one large but *shared* systematic in a first
     single-file test, confirming controls and star are compared fairly).
  3. **Cross-target frequency-occupancy RFI check** (§4.6, new
     `frequency_occupancy.py`): since this single-pointing archival
     survey has no ON/OFF cadence, uses the fact that many unrelated
     targets share near-identical correlator setups instead — flags any
     frequency where ≥2 distinct targets' peak channel or formal hit
     coincide within 5 MHz. Applied to 101 target/spw results (60 formal
     hits): zero coincidences found to date (a modest, currently
     under-powered but genuinely clean null result that strengthens as
     the survey grows and more targets share a given tuning).
  4. **Serendipitous molecular-line catalogue** (§5.3): the continuum
     line-exclusion step's outlier list, aggregated across all completed
     targets as a free byproduct — 18 outlier groups, 12 unidentified
     (likely noise), 6 plausibly real: confirmed β Pictoris CO(1–0)/
     CO(2–1) (already known, matches literature), a tentative few-channel
     CO(2–1)-consistent feature towards HD 285968 (reported honestly as
     unconfirmed, not a detection), and a likely-spurious single-channel
     SiO(5–4)-adjacent bump towards HD 53143 (large offset, low
     significance, flagged as probably not real).
- **Two subsample framing notes added to Discussion**: (a) exoplanet-host
  subsample — 8 of 18 distinct stars processed to date (44%, 16 planets
  total) are confirmed exoplanet hosts, extractable directly from Table 1
  without compromising the volume-limited framing of the main sample;
  (b) white-dwarf subsample — Sirius B and Van Maanen's Star (Wolf 28)
  are white dwarfs included only by accident of ALMA coverage, tied to
  the small but active post-main-sequence-SETI literature (new citation:
  Huang, Tao & Zhang 2026, ApJ, 1006, 9, a very recent chemical-pollution
  white-dwarf technosignature search — different modality, same
  motivating question).
- Abstract, Introduction roadmap, and Conclusions updated to reflect all
  four new analyses (now "four supplementary analyses" throughout,
  distinguished from the original two — closure-phase vetting and the
  population-anomaly check — which remain separately described).
- All underlying data products and analysis scripts pushed alongside the
  paper in `paper_20pc/v2.06_analysis/` for transparency/reproducibility:
  `reanalyze_srcspec.py`, `frequency_occupancy.py`, `run_injection_test.sh`,
  plus the raw JSON/JSONL results each produced.
- Verified with the standard compile-3x + zero-`??` + visual-render
  discipline. 12 pages, clean, no overfull boxes, no undefined refs.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.06/`.

## v2.07 (2026-08-31)
- **Full data refresh**: Table 1 grew from 21 to 36 valid target/bands
  (92 rows; 28 distinct stars), reflecting everything the live 120-star
  driver had completed by the time of writing. Fourteen new target/bands
  added for the first time (61 Vir, AU Mic, HD 207129, HD 38858, HR 1010
  ×2 bands, the AT Mic pair, **TRAPPIST-1** ×3 bands, γ Leporis ×2 bands,
  γ Virginis ×2 bands); three previously single-window entries (GJ 849,
  HD 285968, HD 23484) expanded to their full multi-spw results.
  Spectral types assigned via Teff-interpolation against a documented
  Pecaut & Mamajek main-sequence table (consistent with the method
  already used for radii), with literature overrides for well-known
  cases (TRAPPIST-1 M8V, AU Mic M1Ve, γ Vir F0V, 61 Vir G5V).
- **★ Second automated candidate flag: AU Mic, Band 6, 230.83 GHz.**
  Investigated in full before writing anything: does not coincide with
  any catalogued line (287 MHz from nearest, CO(2-1)); closure phase
  consistent with a point source; but the gating statistic (star
  check-ring peak 5.97 vs control-ensemble peak 5.85) differs by only
  0.12 — well within the expected false-positive rate for a survey
  running many thousands of independent trials. Judged not credible;
  flagged prominently and honestly rather than either hidden or
  oversold, with AU Mic's well-known high flare activity noted as by far
  the more parsimonious explanation if the excess turns out to be real.
  Cross-checked against the frequency-occupancy tool: does not recur at
  any other target.
- **★★ Major finding: a bookkeeping bug was silently marking crossmatch-failed
  target/bands as permanently "complete".** While building this update's
  aggregate dataset, found 19 additional target/bands (beyond the 4
  reported in v2.05: e.g. ε Eridani, HD 188088, LHS 1140) where the
  pointing sanity check had correctly intercepted a wrong-MOUS assignment
  on *both* the narrowband and continuum steps (zero bogus output
  produced, unlike the earlier 4) — but `process_one_target.sh` still
  unconditionally `touch`ed `logs/DONE` at the end regardless, which
  would have permanently excluded these stars from ever being retried
  once a corrected dataset association becomes available. **Fixed**:
  `DONE` is no longer written if both `SETI_SEARCH_FAILED` and
  `CONTINUUM_MAP_FAILED` are set (i.e. zero science product resulted).
  Total crossmatch-excluded target/bands now 23 of the ~96 attempted in
  this phase (roughly half) — a materially higher rate than previously
  visible, now stated plainly in the paper (§6) as a finding in its own
  right, not just a data-quality footnote.
- **A third bug found and fixed**: `calibrate_generic.py`'s
  `gentle_download()` crashed with an opaque, uncaught
  `TypeError: expected str, bytes or os.PathLike object, not NoneType`
  whenever a MOUS's file listing had no `_auxiliary.tar` entry at all
  (`aux_file is None`, called unconditionally). Now fails cleanly with an
  informative message instead, correctly bucketed with the other
  "no calibration recipe available" cases. Found live (LP 649-72, and
  G 70-43/44, which share one MOUS).
- **Download budget raised 45→85 GB** per Glenn's explicit instruction
  ("you can exceed the self-imposed download-budget cap if need be"),
  recovering 4 previously-unreachable targets (HD 69830, GJ14, G 3-14,
  1RXS J0336+3118, whose smallest available EB ranges 50–67 GB). Verified
  this doesn't bypass real protection first: a *separate*, always-on
  check against live free disk space (100 GB margin) and the outer
  driver's emergency watchdog (kills any target if free space drops
  below 80 GB, polled every 30s) remain fully intact regardless of the
  fixed cap's value.
- **Figure 1 and all summary statistics recomputed**: EIRP now
  1.6e13–6.3e15 W (median 4.2e14 W, up from 3.1e14 — driven by several
  new, more distant targets with intrinsically shallower limits);
  continuum 12 detections / 24 non-detections (up from 5/16), deepest UL
  now 0.036 mJy (TRAPPIST-1 Band 3, the tightest continuum limit in the
  survey to date, replacing the previous 0.16 mJy record).
  Exoplanet-host subsample grew to 11 of 28 stars (39%, 30 planets),
  now headlined by TRAPPIST-1's 7 planets.
- Chirp/periodicity and frequency-occupancy checks re-run on the larger,
  current dataset (91 retained spectra; 113 target/spw results) —
  results unchanged in character (clean null, statistically as
  expected), numbers updated throughout.
- **★★★ Found, and fixed, a serious LaTeX bug before it reached Glenn**:
  the growing Table 1 (92 rows) was silently overflowing off the bottom
  of the page in a plain `table*` environment — LaTeX does not
  automatically paginate floats, so roughly the second half of the table
  was being rendered *outside the visible page area* with no error or
  warning (`Overfull \vbox` was not triggered; the float simply extended
  past the page boundary). First attempted the standard fix
  (`xltabular`, combining `longtable`-style pagination with `tabularx`'s
  auto-wrapping `X` column) but found this to be **fundamentally
  incompatible with `openjournal.cls`** (a revtex4-1-derived class) —
  reproducibly isolated via binary search down to a 1-row minimal test
  case (`Undefined control sequence` / `Missing \endgroup` errors
  originating in `array.sty`'s low-level preamble-parsing macros).
  Reverted to the traditional, reliable fix instead: manually split the
  table into 4 separate `table*` blocks (never splitting a single
  target's multi-row block across parts), letting LaTeX's normal float
  placement handle pagination as it always has. Verified rigorously:
  confirmed all 92 rows, including the final row, are present and
  correctly rendered across all 4 parts before pushing.
- Verified with the standard compile-3x + zero-`??` + visual-render
  discipline, **applied to every one of the 4 table parts individually**
  given the pagination bug just found. 14 pages, clean, only the same
  negligible pre-existing 2.98pt title-page `Overfull \vbox`.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.07/`, with the full
  per-target aggregate JSON and the two fixed pipeline scripts
  (`process_one_target.sh`, `calibrate_generic.py`) pushed alongside in
  `paper_20pc/v2.07_analysis/` for transparency.

## Planned for v2.08+
- Add the full ALMA project-code list to the Acknowledgements section
  (deferred again — still meaningful to wait until survey completion so
  it's compiled once, not incrementally).
- Populate a quantitative transmitter-prevalence bound (Wright et al. 2018 /
  Margot et al. 2023 frameworks) once a statistically meaningful fraction
  of the 120-target sample is complete — explicitly deferred in §6 as
  premature at n=36.
- Re-investigate and reprocess the 23 crossmatch-error target/bands
  (4 from v2.05 + 19 newly found in v2.07).
- Re-run the frequency-occupancy and chirp/periodicity checks again as
  the survey grows further — both gain statistical power with N and cost
  nothing to re-run incrementally.
- Broader, multi-band injection-recovery campaign (beyond the
  single-target v2.06 pilot).
- Refresh Table 1 again once the live driver + chain-repeat pass finish
  their current run (survey was at 36 valid / ~96 attempted target/bands
  at the time of writing, still climbing).
- Consider extending to 30/40/50 pc per the roadmap already stated in the
  paper, once the 20 pc sample is complete.
- Refresh Table 1 with the ~20 additional target/bands completed by the
  live driver since v2.05/v2.06 (currently at 41 completed target/bands
  vs. 21 reflected in the current table).
