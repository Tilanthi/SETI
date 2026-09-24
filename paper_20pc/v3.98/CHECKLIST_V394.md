# v3.98 referee checklist — one at a time

## From Glenn (2026-09-22)
- [x] G-1  Note arXiv:2609.16720 (Ortiz Ceballos et al. 2026): MeerKAT
      detection of auroral radio emission from the exoplanet beta Pic b,
      0.85-3.5 GHz, highly circularly polarised bursts + persistent
      emission, ECMI, implied field >= 1.25 kG.
      Three hooks, all verified by calculation (ecmi_v398.json):
        (a) beta Pic is THIS paper's positive control, so a genuine
            planet-localised radio source in the same system belongs in
            that discussion;
        (b) ECMI cuts off at the cyclotron frequency, 2.8 MHz/G x B.
            Their 1.25 kG gives exactly their own 3.5 GHz upper edge.
            Our lowest frequency, 89.6 GHz, needs 32 kG = 26x the
            beta Pic b field; Band 7 needs 99x. So auroral planetary
            radio emission is outside this survey BY PHYSICS, not by
            sensitivity -> sharpens what the non-detection excludes;
        (c) their signal is highly circularly polarised and ours is
            Stokes I only -> concrete astrophysical motivation for the
            per-hand polarisation task, replacing a methodological wish.

## Referee 1
- [x] R1-1  Visibility test on all 75 crossings (QUEUED behind the campaign;
      specified in OPEN_TASKS.md). State status honestly in the paper.
- [x] R1-2  Spatial statistic recast as a candidate-prioritisation
      diagnostic; main text keeps only 5 things; history to the appendix.
- [x] R1-3  ONE primary false-alarm formulation (trigger-conditioned,
      block-resampled); all others labelled diagnostic and moved.
- [!] R1-4  DEFERRED (needs a new compute campaign). Injection campaign to sample every major Class A configuration;
      report sensitivity as a distribution.
- [x] R1-5  "unresolved spectral-carrier technosignatures" + new title.
- [x] R1-6  Per-system bandwidth as the primary coverage metric.
- [x] R1-7  5 % occurrence out of the main conclusions, to an appendix.
- [x] R1-8  Line mask = classification mask, not detection mask.
- [x] R1-9  Temporal selection function into the Abstract (42/82, 23/82).
- [~] R1-10 PARTIAL: main text 170,055 -> 140,908 chars (-17.1 %),
      25.33 -> 21.62 pp. Achieved by moving four self-contained
      blocks to the appendices (dwell completeness, frequency
      frames, next-generation recommendations, RFI), not by
      deleting evidence. Short of 25-30 %; see BUILD_NOTES.
- [x] R1-A  Abstract: exactly five quantitative results + archive warning.
- [!] R1-F  BLOCKED on R1-1: the premise (all 75 through the
      visibility test) needs 0.40 TB of re-calibration. Cannot
      draw a figure asserting a test that has not been run.
- [x] R1-V  One sentence: same codebase, not independently reproduced.
- [~] R1-m  PARTIAL (Zenodo + conversational done). Standardise system/star/window denominators; remove
      conversational phrases; Zenodo DOI as the reference of record.

## Referee 2
- [x] R2-1  "internal validation only" in the Abstract AND §7.
- [x] R2-2  One visually distinct statement of which normalisation is
      authoritative.
- [!] R2-3  DEFERRED (needs a new compute campaign): no second
      source with resolved, recurring, blind-recovered emission
      exists in the searched set; HD 48370 is the displaced
      counter-example, not a second positive control.
- [x] R2-4  Activity/binarity status of the four unattributed hosts.
- [x] R2-5  Line-mask robustness as a table.
- [x] R2-6  Bonferroni/resolution-floor argument promoted to its own
      Discussion subsection.
- [x] R2-7  Quantify the gain from "use the visibilities".
- [x] R2-m  Fig. 1 annotation into the caption + warning on the figure;
      P_scr reminder in Table 5's caption; forward-reference Table 24.

## Release
- [ ] gates, clean regeneration, BUILD_NOTES, push
