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

## v2.04-v2.08 (2026-08-30 -- 2026-09-01)
- **Retroactive summary** (this file was not updated incrementally during
  these versions; full detail for each is in `/workspace/MEMORY.md`,
  search "v2.04" through "v2.08" -- reconstructed here briefly so the
  version history stays traceable from this file alone):
  - **v2.04**: Table 1 restructured to a full spectral-window-per-row
    format (previously one row per target); added N$_{\rm spw}$ column.
  - **v2.05**: abstract cut to ~1/3 length per journal guidance; found
    and excluded the first batch of 4 crossmatch-error target/bands.
  - **v2.06**: implemented full multi-spw search (previously only the
    single finest-resolution window per target was searched).
  - **v2.07**: full data refresh (21→36 valid target/bands incl.
    TRAPPIST-1); second candidate flag (AU Mic, judged not credible);
    found 19 MORE crossmatch-error target/bands beyond the original 4,
    plus the bookkeeping bug that would have permanently excluded them
    from retry.
  - **v2.08**: main 120-star driver finished its full first pass
    (146/146 attempted, 68 succeeded at process level); added eta Corvi
    (first Band-8 target); found and carefully handled a new
    data-quality category (gamma Lupi partial-crossmatch + an
    implausible short-integration result, withheld pending
    investigation).

## v2.09 (2026-09-04)
- **Full data refresh**: re-ran the aggregation against current cluster
  data. Main $\leq$20pc sample grows from 37→50 target/bands (28→39
  unique stars); 22 target/bands new or reprocessed this version. EIRP
  limits now $1.7\times10^{13}$--$7.1\times10^{16}$W (median
  $3.1\times10^{14}$W); continuum 14 detections / 33 non-detections
  (median UL 0.52 mJy, was 0.56).
- **NEW: preliminary 20-30 pc extension appendix** (Appendix B), per
  Glenn's request. Investigated what "the additional searches out to 30
  pc" actually are: **there is no actively-maintained, parallel 20-30pc
  campaign** -- only archived metadata from the older, non-distance-limited
  pre-pivot survey (`archive_gt20pc_metadata/`). Identified the 12 stars
  in that archive falling in 20-30pc, characterised each honestly: 5
  usable (narrowband+continuum), 2 continuum-only (narrowband failed), 5
  with no usable data at all (calibration/download/governor failures,
  never retried since that survey was stopped, not paused, at the
  pivot). Reported as a clearly-separated, explicitly non-volume-complete
  table -- NOT merged into the main Table 1, and the paper states plainly
  what it is and isn't.
- **Candidate-vetting catch (20-30pc data)**: HD 107146's archived result
  carried `credible_technosignature_candidate=true` (3 hits) but its
  control-ensemble peak SNR (6.013) is statistically indistinguishable
  from its source-region peak SNR (6.029) -- applied the same
  control-ensemble discipline used throughout the main survey and
  correctly rejected it as non-credible, rather than reporting the raw
  flag.
- **Two real pipeline findings, reported with the same rigour as
  v2.05-v2.08's crossmatch-bug disclosures**:
  1. A specific spectral window (recurring with byte-identical anomalous
     parameters: 12.1s on-source vs 393-520s for sibling windows, yet an
     implausibly *smaller* combined noise estimate) found in TWO
     independent targets sharing a similar Band-6 correlator setup
     (HD 10647 and the star catalogued as "gamma Lupi" -- NOT the famous
     naked-eye B-star of the same name, confirmed via grossly
     inconsistent Teff/distance). Cross-target recurrence with matching
     detail elevates this from "one target's odd result" (as left open
     in v2.08) to a diagnosed, reproducible pipeline defect. Both
     targets' affected window is excluded, contaminated continuum
     withheld, other windows retained.
  2. Confirmed a previously-reported (pre-v2.08) continuum-imaging gap is
     STILL outstanding: Giclas 9-38A/B remains unfixed and still produces
     a spurious ~8 Jy, 86sigma "detection" at an offset the code reports
     as 0.00 arcsec (actually ~52 arcmin off, since the continuum step
     lacks the narrowband step's pointing-offset guard). By contrast,
     confirmed that most of the OTHER crossmatch-affected targets
     (SCR J1845-6357, Wolf 358, eps Eridani, and others) have since been
     successfully reprocessed and now appear in Table 1 with legitimate
     data -- the retry mechanism is working as designed.
  3. **Separately, an operational (not scientific-pipeline) bug**: this
     version's cluster driver relaunch (following the exact command given
     in the task brief) omitted required `SETI_TARGET_CSV`/`SETI_BAND_MOUS`
     env vars and silently ran the OLD non-volume-limited target list for
     ~20 min before being caught and fixed. See `STATUS.md` and
     `/workspace/MEMORY.md` for detail; does not affect any number
     reported in this paper.
- Exoplanet-host subsample: 13/41 unique stars (32%, 33 planets), adding
  eps Eridani and HD 69830.
- Three supplementary-analysis subsections (molecular-line catalogue,
  chirped-drift/periodicity, frequency-occupancy) explicitly note their
  quoted counts are carried over unchanged from v2.08 -- re-running them
  against the larger sample needs the original scripts, not available
  this session; deferred honestly to next version rather than
  guessed/fabricated.
- Verified with the full discipline: rendered and eyeballed every page
  (not just first/last) via `pdftoppm`; `grep "Overfull \hbox"` = 0
  after one minor rewording fix; 0 unresolved `??`/undefined refs;
  clean-from-scratch rebuild MD5-verified before packaging. 17 pages
  (was 15).
- Figures: EIRP/continuum-vs-distance figure regenerated from fresh
  aggregate data with the 7 20-30pc points overlaid as visually distinct
  open orange diamonds, clearly labelled as the preliminary extension in
  both the legend and caption. Sample-distance-distribution figure
  (Fig. 2) carried forward unchanged (its underlying 2357-star/120-star
  lists did not change this version).
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.09/`; aggregate JSON and
  generation scripts pushed to `paper_20pc/v2.09_analysis/` for
  transparency, following the established pattern.

## Planned for v2.04+
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
