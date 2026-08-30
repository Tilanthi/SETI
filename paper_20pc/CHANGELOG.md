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

## Planned for v2.05+
- Add the full ALMA project-code list to the Acknowledgements section
  (deferred again — still meaningful to wait until survey completion so
  it's compiled once, not incrementally).
- Populate a quantitative transmitter-prevalence bound (Wright et al. 2018 /
  Margot et al. 2023 frameworks) once a statistically meaningful fraction
  of the 120-target sample is complete — explicitly deferred in §6 as
  premature at n=19.
- First real closure-phase-vetting result and first population-anomaly
  flag, whenever either actually triggers.
- Consider extending to 30/40/50 pc per the roadmap already stated in the
  paper, once the 20 pc sample is complete.
