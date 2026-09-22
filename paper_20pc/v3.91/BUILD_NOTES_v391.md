# BUILD NOTES — v3.91: the presentational revision

Both referees made presentation a condition. This version does that work.

## Gates

| gate | value |
|---|---|
| **main text** | **26 pp (was 29)**; appendices 20; total 46 |
| LaTeX errors / undefined / multiply-defined / overfull / Type 3 | 0 / 0 / 0 / 0 / 0 |
| macros defined / unused | 1100 / 0 |
| abstract | 1910 characters (limit 1920, both counters) |
| clean regeneration | **95/95 byte-identical** |
| number audit | 49 / 0 |
| primary-statistic consistency | 0 problems |
| round-file ownership | 49/49 |
| cross-reference resolution | 0 misplaced |

## Length

Main-text prose **122,142 → 100,539 characters, a cut of 17.7 per cent**,
against the 20–25 per cent both referees asked for. The main text is three
pages shorter; nothing was deleted from the release.

I did not reach 20 per cent and would rather say so than pad the number.
What remains in the main text is, by section: sample, search domain,
detection statistic, injection/recovery completeness, the candidate
sequence, the null result, the population interpretation and the
limitations — the order Referee 1 specified. Further cuts would start
removing content rather than duplication.

## What moved, and where

| material | from | to |
|---|---|---|
| Glossary (Table 1) | before §2 | Appendix A, *Notation* |
| Reproducibility and audit narrative | §Data Availability | Appendix, *Reproducibility and provenance* |
| Extraction, control geometry, position-correlated systematics | §4.2 | same appendix |
| Sample bookkeeping: entry counts, coverage criteria, pointed vs serendipitous | §3 | same appendix |
| Dwell campaign: end-to-end check, scope, representativeness | §4.5 | Appendix B |
| Statistical units and independence; data-quality screening; data-quality exclusions; CP−72 2713 narrative; continuum ("Ancillary results") | main text | appendices |
| Figure 1(a), cross-survey EIRP | main text | Appendix A |
| Acceleration/drift figure | discussion | methodology, immediately after the drift grid |
| $R_\sigma$, region-max, polarisation, CP−72 diagnostics, β Pic block-by-block | Appendix G subsections | one summary table, `tab:summarised` |

The Data Availability statement in the main text is now four sentences, as
Referee 1 asked.

## Required changes closed this round

* **R1-4** The three frequency-union quantities are now generated and
  asserted by `freqdef_v391.py`: $\Delta\nu_A = 47.7$, $\Delta\nu_B = 90.5$
  (the **full** Class B union, overlapping Class A by 20.1), 
  $\Delta\nu_{B\rm -only} = 70.4$ and $\Delta\nu_{A\cup B} = 118.1$ GHz.
  Referee 1's diagnosis was exactly right — 90.5 and 70.4 were different
  quantities. The identity is asserted in the build.
* **R1-5** "stage-1 spatial outlier" → "stage-1 flagged window", 40
  occurrences. "Outlier" did overstate what a rank screen establishes.
* **R1-9** Figure 1 split; the channel-width panel stays in the main text
  with the warning stated once; the EIRP panel is relocated.
* **R1-12** After $P_{\rm eff}$: "every EIRP quoted here is the *total*
  radiated power of an unresolved monochromatic carrier, not the power
  falling in the peak ALMA channel."
* **R1-14** RFI: we now claim only that *no identified interference
  mechanism accounts for these events*.
* **R1-15** The acceleration figure is in the methodology.
* **R2-2** Glossary relocated; both referees satisfied, since Referee 1
  asked that it be retained and Referee 2 that it leave the reader's path.
* **R2-3** Appendix G consolidated; six subsections become one table.
* **R2-4** Tail quantities computed against the screen's own
  exchangeability-violating null are now written $\mathcal{P}_{\rm scr}$,
  never $p$, with the convention fixed in §4.2 before first use. $p$ is
  reserved for genuine tests.
* **R2-5** The sample-representativeness caveat is on the first page.
* **R2-minor** The injection campaign's coverage is justified: the limit is
  computational, each injected window being re-searched end to end over the
  full drift grid.
* **R2-minor** The γ Lupi relabelling was **already** correct in the
  released catalogue: all seven rows carry `HD 139664`. No change needed;
  reported as verified.

## Still open

R1-2 (stratified end-to-end injection through the selection gate) and the
previous round's per-hand polarisation both need the pipeline host, which
the archive-mining campaign still occupies. R1-3 (effective-exposure
occurrence likelihood) and R1-6 (time-domain completeness figure) are
computable and are the next analysis increment.
