# v3.91 referee checklist — recommendation by recommendation, in order

Glenn's instruction: implement each before going on to the next.

## Referee 1 — major
- [x] R1-1  **One compact table of every false-alarm expectation** in 5.3
      (sample / windows / rate / expected / observed / purpose), and ONE
      primary expectation (Class A) for the four unattributed events. The
      all-window figure becomes a pipeline diagnostic only.
- [x] R1-2  **Visibility localisation into the formal candidate definition**
      in 4.2 and Fig. 3: threshold -> spatial prioritisation -> visibility
      localisation -> line identification -> recurrence. The spatial
      statistic described consistently as candidate generation.
- [x] R1-3  **P90_sel as the single headline sensitivity everywhere**;
      P_trig and P_eff retained only as intermediates. Table 1 restructured
      to show the hierarchy P_trig -> P_eff -> P90 -> P90_sel with a line
      naming P90_sel as the quantity used for interpretation.
- [x] R1-4  **Empirical P(>=4) under the calibrated null**, with clustering;
      replace "modest population excess" with observed/expected/tail
      probability.
- [x] R1-5  **Table for the four unattributed events**: epoch, n repeats,
      min/max elapsed time, depth of deepest repeat relative to the event,
      recurrence result. Replaces "23 repeat observations, which span days".
- [x] R1-6  **One completeness formulation**: "work-list-complete but
      epoch-incomplete". No "archive-complete" or equivalent anywhere.
- [x] R1-7  **Class A and Class B as two experiments in the conclusions**;
      no combined sensitivity or completeness statement.
- [x] R1-8  **Move the methodological defence out of the Introduction**
      (pre-registration detail, repository timestamps, the 135-position
      region-max experiment) to 4.2 or Appendix F.

## Referee 1 — secondary
- [x] R1-s1 disc/M-dwarf limitation into the opening paragraph of 6
- [x] R1-s2 Fig. 1 panel title: "parameter-space location; vertical
      sensitivities not directly comparable"
- [x] R1-s3 point at Fig. 4 wherever the frequency range is quoted
- [x] R1-s4 "excluded from the experiment", never "vetoed", uniformly
- [x] R1-s5 decorrelation qualification beside the principal sensitivity in
      6 and in the conclusions

## Referee 2 — major
- [x] R2-1  **Radius-correction promoted to the headline**: both counts side
      by side with their chance expectations in the abstract, 5.3 and 7, and
      the reason it is not primary stated at first mention.
- [x] R2-2  **A standard occurrence-rate metric** (DFM-style or
      transmitter-fraction), computed and quoted with the paper's caveats.
- [x] R2-3  **RFI vetting statement for the four unattributed events.**
- [x] R2-4  **Drop sigma notation for the trigger**: T_trig = 5 etc.,
      reserving sigma for genuine noise scales.

## Referee 2 — minor
- [x] R2-m1 distinguish the transfer bracket from the calibration budget at
      first mention in the abstract
- [x] R2-m2 White (2026) identifier, or remove and self-contain the sentence
- [x] R2-m3 one summary row per worked example (CP-72, HD 48370)
- [x] R2-m4 rank the six follow-ups in 6.4
- [x] R2-m5 Fig. 3's step list earlier in the running text

## Referee 2 — technical
- [x] R2-t1 no "identifier to be supplied" in the version of record
- [x] R2-t2 dedicated cross-reference resolution pass
- [x] R2-t3 glossary gains a first-use section reference per term
- [x] R2-t4 consistent appendix heading style
- [x] R2-t5 Fig. 1 caption: bold only the one critical sentence

## Release
- [x] gates, clean regeneration, arXiv set, BUILD_NOTES, CHANGELOG, push
      **DONE 2026-09-21: pushed `dc2deaf6f312`, 414 entries, PDF and .tex
      byte-verified against the repo after pushing.**
