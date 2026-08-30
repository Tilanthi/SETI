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

## Planned for v2.01+
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
