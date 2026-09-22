# v3.93 referee checklist — one at a time, in order

Both referees converge on one thing: **adopt the radius-corrected
statistic as the primary analysis**. That is R1-1 and R2-2 and it is done
first, because most other items depend on it.

## Referee 1 — major
- [x] R1-1  **Radius-corrected/per-position normalisation becomes the
      PRIMARY statistic.** Rerun principal candidate selection on it;
      retain the frozen statistic as a documented robustness comparison;
      state the change was motivated by the independently demonstrated
      radial dependence, not by which candidates survived.
- [ ] R1-2  **One ordered decision procedure.** Rewrite 4.2 and the start
      of 5.3 around: raw window -> threshold crossing -> spatially
      significant/localised event -> molecular-line classification ->
      independent repeat -> disposition. One criterion per step, each
      labelled before/after inspection. Fig. 3 to match exactly.
      Reserve "candidate" for an event that survives all vetting and
      awaits recurrence; everything earlier is "event" or "outlier".
- [x] R1-3  **P(>=4) must not read as an astrophysical excess.** Wherever
      quoted, including the Abstract, immediately qualify that it belongs
      to the original screen later shown to have a position-dependent
      rank bias. Abstract rewritten to the referee's wording.
- [ ] R1-4  **Visibility localisation becomes the principal spatial
      test** for all crossings surviving the first screen. Explain the
      phase argument, use beta Pic as positive control, state the
      localisation sensitivity quantitatively.
- [ ] R1-5  **Joint drift x dwell injection experiment.** A stratified
      subset; produce P_recover(P/P90, f_dwell, nudot) and use it instead
      of transferring the zero-drift dwell result.
- [x] R1-6  **Only P90sel as the sensitivity** in Abstract, Discussion,
      Conclusions, captions; hierarchy to methods/tables. Headline
      becomes the **per-system best-window** distribution.
- [ ] R1-7  **Effective-survey hosting fraction**: N_eff(P) = sum_i C_i(P)
      from the measured per-system completeness; plot f95(P) vs EIRP;
      replaces the 3/N treatment.
- [x] R1-8  **CWTFM demoted** to a literature-convention comparison; the
      per-system frequency-coverage version is the preferred quantity.
- [x] R1-9  **Lead with 60 systems / 403 windows / 47.7 GHz** as the
      primary narrowband experiment; 1252 Class B as secondary; the 1655
      total describes the archive-processing exercise.
- [x] R1-10 **Line mask becomes a classification flag, not an exclusion.**
      Search the complete coverage; line coincidence affects the prior.
- [x] R1-11 **P(0 repeats | f_duty)** from the actual temporal sampling of
      the 23 repeats; replace "does not recur" with a duty-cycle statement.
- [x] R1-12 **Shorten substantially.** Main text to Introduction ->
      Sample -> Search method -> completeness -> candidates -> constraints
      -> discussion/conclusions. Audit trail to appendices. Keep Fig. 3.

## Referee 2 — major (1-3 are conditions for acceptance)
- [ ] R2-1  **Shorten and de-jargonise.** 5.3 to one summary table plus a
      paragraph, narrative to the appendix. Aphoristic prose to
      conventional declarative prose. Glossary: fold pseudo-star,
      stratum, hold-out, add-one rank into first-use parentheticals.
- [x] R2-2  **Radius-corrected as primary** in Abstract and Conclusions;
      uncorrected demoted to a robustness figure. (= R1-1)
- [x] R2-3  **Abstract must carry the dominant uncertainty**: the transfer
      bracket numerically, and that the power is a one-sided upper bound
      on reach, not a central estimate.
- [x] R2-4  **Abstract sample-representativeness caveat**: disc/planet
      programmes, F/G-enriched, M-dwarf-poor, does not constrain the local
      habitable-zone population.
- [x] R2-5  **Round tail probabilities to one significant figure** and
      fold the factor 1.2-1.9 pseudo-star rate uncertainty into the
      primary assumption.
- [ ] R2-6  **Re-run polarisation on the 13 stage-1 windows**, or justify
      explicitly why it cannot be done.

## Referee 2 — minor
- [ ] R2-m1 Fig. 1(a): separate subpanels per survey, or drop it in favour
      of panel (b).
- [ ] R2-m2 White (2026): make available as a preprint or reduce reliance.
- [x] R2-m3 Attach the regeneration-script output as supplementary
      verification material.
- [x] R2-m4 Title: "An archival ALMA search toward 82 stellar systems
      within 40 pc" or similar, to avoid a volume-complete reading.
- [ ] R2-m5 Appendix G trim: G.5, G.8, G.9 to a table with one-line
      outcomes.

## Release
- [ ] gates, clean regeneration, arXiv set, BUILD_NOTES, CHANGELOG, push
