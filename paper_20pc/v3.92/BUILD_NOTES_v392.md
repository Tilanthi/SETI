# BUILD NOTES — v3.92

Two referee reports, worked in order. **16 of 20 items closed.**

## Gates

| gate | value |
|---|---|
| **main text** | **24 pp** (29 at v3.90); appendices 22; total 46 |
| errors / undefined / multiply-defined / overfull / Type 3 | 0 / 0 / 0 / 0 / 0 |
| macros defined / unused | 1119 / 0 |
| abstract | 1910 characters (limit 1920, both counters) |
| clean regeneration | **98/98 byte-identical** |
| number audit | 49 / 0 |
| primary-statistic consistency | 0 problems |
| round-file ownership | 52/52 |
| main-text prose | **94,448 characters, a 22.7 % cut from the v3.90 baseline** |

## Two findings that changed the paper

**1. The visibility-calibration term can be bounded, and it moves the
budget (R2-1).** Earlier versions listed it as "not separately quantified"
while quoting the combined budget as authoritative. It is now measured:
if the delivered amplitude scale were inconsistent between execution
blocks, the ratio of each window's measured per-integration rms to its
radiometric prediction would scatter beyond thermal noise. Over 2,271
windows in 559 blocks that ratio has a **robust block-to-block scatter of
4.5 per cent**, against 0.8 per cent within a block. Including it raises
the quoted combination from ±8 to **±9 per cent**, and every EIRP in the
paper now carries the larger figure.

**2. Repeat blocks are not independent epochs, and the difference is
large (R1-8).** The paper had been quoting the 55 systems with more than
one searched block as though each had a confirmation opportunity.
**Thirteen of those 55 have all their blocks within one day** — one
observing session, not a test of persistence. Only **42 of 82 systems
(51 per cent)** have epochs separated by more than a day: 12 over days,
7 over months, 23 over years. Recurrence over years can be tested for
fewer than a third of the sample.

## Closed this round

* **R1-1** The candidate hierarchy is restated so visibility-domain
  localisation is the primary *physical* test and the spatial screen is
  explicitly only a prioritisation. The test covers the 13 flagged windows
  rather than all 75 crossings because visibilities were retained only for
  flagged windows; extending it needs 50 blocks and 0.31 TB, about 15 h on
  this pipeline's measured cost model, and that is stated in the text.
* **R1-2** No quasi-significance for the four events. The Conclusions and
  Figure 3 no longer carry a chance expectation for them; the screen is
  said plainly to assign no calibrated false-alarm probability.
* **R1-3, R1-4** The narrowband experiment is 60 systems / 403 windows /
  47.7 GHz throughout; Class B is the *coarse-channel spectral-excess
  search*; and the searched signal is defined unambiguously in the
  Introduction with the 15.3–1953 kHz channel range.
* **R1-9** CWTFM moved to an appendix; the Discussion compares axis by axis.
* **R1-11** Figure 3's right panel now shows three named operations —
  data selection, automated candidate generation, physical validation —
  with heavy rules at the boundaries.
* **R1-12** Conclusions are four compact statements in the referee's order.
* **R1-7** No occurrence-rate interpretation except explicitly conditional.
* **R2-2** The mask-removal robustness result is in the main line, and the
  ambiguity is resolved: the statistic **is** computed inside masked
  channels; the mask is applied afterwards, at the reporting stage.
* **R2-3** "Primary" disambiguated at first use.
* **R2-4** Edge channels: none were trimmed; the effect is carried in the
  calibration-residual budget, and crossing-to-edge distance is released.
* **R2-5** The radius-correction argument is one subsection, conclusion
  first, with the demonstrations in a single appendix; an appendix roadmap
  is added.
* **R2-6** There is **no overlap** with Mason et al. (2024): their targets
  are all beyond 1.01 kpc and every star here is within 40 pc. Recorded as
  a real limitation — the null rests on internal validation alone — with
  a blind third-party injection recommended as the check we would want.
* **R1-10** 22.7 per cent of main-text prose cut over two passes.
* Minors: bold callouts restricted to Abstract and Conclusions (60
  removed); acronym glossary and notation pointer added; Figure 1
  annotation explained; VBRL clause added. The γ Lupi point needed no
  change — the released catalogue already carries `HD 139664`.

## Still open

R1-5 (the EIRP presentation order is improved but not fully inverted),
R1-6 (the transfer-scatter figure against channel width, band, integration
time and array), and the two items needing the pipeline host: the
stratified end-to-end injection through the selection gate, and per-hand
polarisation.

## Trap

`viscal_v392.py` reads `survey_numbers_round38.tex`, which
`p90_budget_v385.py` writes, and it was registered to run **before** it —
the fourth forward dependency in this project's history, and again only the
clean-regeneration test caught it (34/98 on the first attempt). The
collision gate also needed repair: it had counted a *reader* of a round
file as a writer.
