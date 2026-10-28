# Response to referees C and D — v3.51

Both reports recommend major revision, and both make the same two structural
requests: lead with the sensitivity number a reader should actually use, and
simplify the statistical narrative down to the pipeline that decides a
disposition. v3.51 does both. The manuscript is **29 pages** (main 19.73,
back matter 0.82, appendices 8.12, bibliography 0.31 = **28.98**), all gates
zero, abstract 1888 source-expanded / 1893 rendered characters against arXiv's
1920, 567 macros with 0 unused, clean regeneration byte-identical in 46 of 46
generated files including all 13 figures, and an arXiv set of 34 items that
builds clean from an empty directory with no author comments in the source.

Below, for each point, what was done and **what was verified rather than
assumed**.

---

## The two changes that matter most

### 1. The spectral-response-corrected threshold is now the principal physical number (C3, D2)

Verified from the kernel and from the released catalogue, not taken from the
reports. ALMA's default online Hanning smoothing leaves 0.38 to 0.50 of a
sub-channel tone's power in the peak channel depending on sub-channel
placement, median 0.44, so nominal thresholds are optimistic by ×2.00 to
×2.67, **median ×2.29**. The three quantities the manuscript now keeps apart
throughout, in the rewritten boxed rule of §4:

* **`P_trig`**, the nominal EIRP<sub>5σ</sub> trigger. This is what the
  pipeline fires on, it is what every "5σ" in the paper means, and it is what
  every EIRP figure axis is now labelled: **"nominal 5σ trigger EIRP"** in
  Fig. 1 (y-axis), Fig. 3 (colour bar) and Fig. 7 (y-axis). The labels were
  verified by extracting the text back out of each figure PDF, not by eye,
  because a matplotlib axis label can be silently clipped by the figure's own
  bounding box.
* **`P_eff` = 2.29 `P_trig`**, the effective unresolved-carrier threshold,
  used wherever a physical transmitter power is compared.
* **`P_x`**, the completeness limit, determined for one configuration only.

**This changes an answer, and the change is stated plainly rather than
buried.** On the trigger, 1 of 81 systems reaches Arecibo-class total power
(2×10<sup>13</sup> W) and 2 reach twice it. On the effective threshold, the
deepest window in the survey is 3.7×10<sup>13</sup> W, so **0 systems reach
Arecibo-class power and 1 reaches twice it**. The nominal values (1, 2) are
re-derived in the generator and asserted against the published ones before the
corrected ones are computed, so the change is a change of definition and not
of data. The abstract now gives both ranges and uses the corrected one against
the benchmark; the conclusions do the same.

Also recomputed on `P_eff`: the 12-m / 1-MW geometric benchmark
(8×10<sup>14</sup> W), which the median Class A effective threshold now misses
by a factor 2.1, and detectability case (i) in §6.1.

### 2. The statistical narrative is reduced to the operative chain (C1, D8)

The main text now carries only the chain that decides a disposition: spectrum
→ T ≥ 5 → T exceeds all 512 controls → astrophysical and RFI vetting →
recurrence → candidate. Moved out:

* **Closure phase, chirped drift, per-channel periodicity and cross-target
  occupancy** are collected in an appendix retitled **"Exploratory diagnostics
  not used for candidate selection"**, which opens by saying that nothing in
  it gates a disposition or derives a limit. Their main-text treatment is one
  short paragraph.
* **RFI rejection stays in the main text**, compressed, because RFI vetting is
  an operative gate in the chain.
* **The five-component false-alarm construction** moves to
  Appendix G, where the worked derivation C2 asks for now lives. The main text
  keeps what was measured and what it licenses.
* **The exchangeability battery** is compressed to its four null results, with
  each test's construction left in the appendix.

Main-text characters fall from 137,808 to 134,800 (−2.2 per cent) with roughly
6,500 characters of new material added, so the reduction in the pre-existing
narrative is nearer 7 per cent than the 25–30 per cent both referees suggest.
The page ceiling, not reluctance, is the binding constraint: the paper is at
28.98 of 29 pages with 0.02 pages of slack. Referee D's five-question
reorganisation is therefore partially adopted (the ordering of §5 and §6
already follows it) and not completed.

---

## Campaign status, and the held-out validation set (D4, D7, C-major-4)

Read read-only over ssh from the processing host on 2026-09-12 (nothing
downloaded, no compute started; the campaign itself is running there).

At build time the epoch-extension campaign has searched **7 execution blocks
toward 4 stars, 28 spectral windows**, with the frozen pipeline and with no
change of any kind to statistic, mask, threshold or candidate rules after the
first was searched. A further **2 blocks failed calibration** and produced no
search product, **2 are running**, and the campaign continues. This replaces
v3.50's 20 windows / 5 blocks / 2 stars.

**The important improvement is not the count.** Two of the seven blocks are
toward **HD 53143 and Wolf 359**, stars that carry no stage-1 outlier in the
survey, so the set is no longer only a re-test of already-flagged windows.
Recomputed from the products:

| | v3.50 | v3.51 |
|---|---|---|
| windows / blocks / stars | 20 / 5 / 2 | **28 / 7 / 4** |
| β Pic CO windows (positive control) | 4, T\* = 10.0–30.8 | 4, T\* = 10.0–30.8 |
| effectively null windows | 16 | **24** |
| median rank of the null windows | 0.62 | **0.50** |
| KS against U(0,1), null windows | D = 0.17, p = 0.65 | **D = 0.12, p = 0.87** |
| stage-1 spatial outliers among them | 0 | **0** |
| all windows together | D = 0.27, p = 0.09 | D = 0.17, p = 0.33 |

Reported as a partial result, with its three limitations stated (4 stars,
windows within a block are not independent epochs, and 24 null windows cannot
resolve a rank departure below about a tenth), and with the build date given
so the number can be updated at submission. §6.2 and the conclusions no longer
call the 346 unsearched blocks the survey's largest *untaken* resource; they
are being taken.

---

## Star-versus-control residual variance, D3

**Attempted, and it worked.** Referee D calls this the largest unresolved
assumption in the annulus method, and the retained products do support a
limited version of it. For each of the four stage-1 windows we took the
pipeline's own baseline-subtracted per-integration residuals at the star and at
the 8 retained control positions, standardised them by the pipeline's own noise
map σ(t,ν), and formed a robust scale over the (integration, channel) plane
with the channels around the crossing excluded at every position alike:

    R_sigma = sigma_star,residual / median(sigma_controls,residual)

    CP−72 2713   1.000        beta Pic B3   1.001
    HD 48370     0.995        beta Pic B6   1.001

The star agrees with its controls to better than **0.7 per cent** in every
window at 95 per cent confidence. The one window where the star is measurably
*quieter* than its ring is HD 48370, whose ring is full of CO, which is the
expected sign.

This bears directly on CP−72 2713. Because T\* scales inversely with the noise
the star is divided by, an unmodelled broadband excess of **2.2 per cent** at
the stellar position would bring that window's T\* below its own ring maximum
and dissolve the outlier; the measurement bounds any such excess at 0.7 per
cent, a factor of three smaller. The manuscript says "disfavoured without being
formally excluded", not "excluded".

**What 8 controls cannot do is stated in the same paragraph.** They estimate
the position-to-position scatter from eight draws, which is why the bound is at
the level of a per cent and not a tenth of one. More important, this is a
**broadband** variance test: it is sensitive to a stellar position that is
noisier throughout and it is *not* sensitive to an artefact confined to one or
two channels, which is the morphology the search is built to find and which
would raise T\* while leaving the robust scale untouched. That case is left to
the local null and to recurrence, and retaining all 512 control spectra is
already the recommendation in §6.4.

Measurement code and outputs ship as `rsigma_measure.py` and
`rsigma_v351.json`.

---

## The false-alarm arithmetic, worked through, C2

All three parts, in a new subsection of Appendix G.

**(a) The correlation-corrected trial count is now derived, not asserted.**
This exposed a real defect: up to v3.50 the correction was the hand-set
constant `OVERCOUNT = 4.0` in `v347_calc.py`, with the comment "Hanning in
frequency × drift oversampling" and no arithmetic anywhere. The arithmetic
gives a different number:

* frequency: the Hanning kernel gives ρ₁ = 2/3 and ρ₂ = 1/6, so the variance of
  a sum over *n* channels exceeds *n* by 1 + 2ρ₁ + 2ρ₂ = **8/3 = 2.67**;
* drift: the released extraction code steps the grid at `DRIFT_STEP_DIV = 2`
  points per channel of traverse over the track, so adjacent trials count
  **2** for one;
* the axes are independent, so the over-count is 2.67 × 2 = **5.33, not 4**.

The generator now computes it. Corrected predictions move from 5.50 to
**5.45** (fine) and 4.17 to **4.10** (coarse) against 5.77 and 4.41 observed,
so the residual is **+6 and +8 per cent** rather than +5 and +6.

**(b) Is the residual factor-of-4 excess consistent once the four
dispositioned windows are set aside? Yes at the 9 per cent level, and it is
reported as an open systematic anyway.** The factor 4.2 factorises, and only
one factor is a puzzle. Within a crossing window the multiplicity is 3.4 cells
observed against 1.2 expected under independence, a factor 2.8, which is what
the 2.67 frequency over-count predicts: one real threshold excursion is counted
about three times. What is left is the window-level factor, 16 windows with an
unattributed on-star crossing against 10.9 expected, a factor 1.5 whose
one-sided Poisson probability is **0.09**. Not significant; also not zero,
one-sided, and matched in sign at the controls. The manuscript reports it as an
open systematic and says a residual excess at the tens-of-per-cent level cannot
be excluded.

**(c) Where the factor of 16 comes from**, with the connection to N_eff. Rank
floor 1/(N_ctrl+1) = 1/513 = 1.95×10⁻³; Bonferroni scale α/N =
0.05/431 = 1.2×10⁻⁴; ratio 16. Correlation widens rather than closes the gap:
with N_eff ≃ 30–43 independent spatial trials the ensemble can really resolve
only 0.023–0.032, so the gap becomes a factor **196 to 278**. Drawing more
controls cannot help, because the primary beam bounds the annulus.

---

## The other decided items

**Statistical units and independence (D9).** New §4.1 defines catalogue entry
(88), physical system (81), target/band (114), execution block (102), spectral
window (431 rows → 396 distinct EB/window datasets), independent frequency
trial (about 5.3 grid cells per trial) and independent epoch, and then says
which unit enters which population-level probability, in bold: **431 windows
are not 431 independent trials**, occurrence-type statements must use 81
systems, persistence statements use epochs. The 396 was recomputed
independently in the new generator from the catalogue keys and agrees with the
existing `\NDistinctDatasets`. The overlapping definitions in §3 were deleted in
the same edit, so the subsection is nearly free of page cost.

**Occurrence material (C6, D10).** Already confined to Appendix I; the main
text now carries one explicit warning in bold — *it is not an occurrence rate
and should not be quoted as one* — with the four conditions it depends on and
the note that it vanishes under any prior spanning ALMA's tuning range.

**Molecular mask (D5).** Kept and reframed, not re-run. The discussion and the
conclusions now say that a carrier deliberately placed on CO(2→1) is not
undetectable by ALMA but unsearched here because this analysis vetoes that
frequency, that the channels are retained in the release for anyone who brings
independent discrimination, and that the cost is 3.1 per cent of gross
bandwidth (5.3 per cent of the unique-frequency union).

**CP−72 2713 (D6).** The standard description is now "an unattributed
first-epoch threshold event, absent in the second epoch". The subsection
heading, Table 5's disposition cell, Table 2's summary row and the released
catalogue's disposition string were all changed together (Data Availability
promises the catalogue column is verbatim from Table 5, so the generator was
changed with the table). The manuscript states explicitly that the absence two
hours later does not identify the first event as noise.

**Chronology (C4a).** Verified through the GitHub API against the released
repository, not asserted. AU Mic's flag is first committed 2026-08-31 and the
symmetric statistic is adopted 2026-09-09, so that redesign postdates that flag
by 9 days, which the paper already said. **For CP−72 2713 the order is the
other way round**: the earliest commit in which CP−72 2713 appears as a flagged
window is `0c465f2661bd`, the very commit that adopts the symmetric statistic,
and the preceding manuscript version contains no mention of the star. Because
that window's region maximum already lay on the star, both statistics return
the same T\* (Table 8), so no version of the analysis could have created it.

**Prospective criterion (C4b).** One sentence now states what a positive
recurrence had to look like: a crossing at the first epoch's channel *and*
drift rate reaching T ≥ 5 in the second block and exceeding all 512 of its
controls. A persistent emitter at the first epoch's flux would have returned
T\* = 6.21 against a largest control of 5.93, so the test could have produced
that outcome; the margin is narrow, which is why the retirement rests on the
flux comparison and not on the second flag.

**Polarisation (C5).** Quantified by querying `ivoa.obscore` for `pol_states`
on all 102 searched execution blocks: **102 of 102 are delivered with both
parallel hands (XX and YY)**, none single-polarisation. The promised
discrimination is therefore available from existing data, limited only by
per-correlation flagging inside QA2, which the retained products do not expose.
Query output ships as `polstates_v351.json`.

**Which configuration axis dominates (C, minor).** Band (55 of 118 windows) and
drift-trial count (55) account for almost all the mismatch, against 17 for
channel width, 20 for integration time and 12 for beam offset. The manuscript
draws the implication: what the transfer bracket least establishes is transfer
across band and across drift-grid size.

**Terminology (C, minor).** "Flag" as a noun for the screening state is gone,
replaced by "stage-1 spatial outlier", shortened to "stage-1 outlier" after
first use in a section, with the abbreviation recorded in the nomenclature
table. "Flagged" survives only where another author flags something, or where
visibilities are flagged.

**Other minors.** A summary sentence at the head of the AU Mic appendix giving
the conclusion the three tests converge on; "wholly unsearched" above 115 GHz
qualified to "very sparsely searched"; "stared at 88 of the nearest stars"
removed; "every star within 40 pc with public-archive coverage" replaced by
"every star we identify as having qualifying public ALMA coverage", with the
main text now saying that the quoted field of view admitted 53 stars no
observation in fact contains, so "covered" is a property of our selection and
not a guarantee; the abstract states immediately that the 313 Class B windows
are 73 per cent of the sample and carry no drift discrimination.

---

## Bibliography: three of the four claims are stale, one is real

Checked entry by entry against the manuscript's own `thebibliography`.

* **C9a, Margot (2023) and Mason (2024) sharing a volume and page — not
  present.** Margot et al. 2023 is *AJ* **166**, 206; Mason et al. 2024 is
  *MNRAS* **536**, 2127. Different journal, volume and page. No change made.
* **C9c, the Fouqué citation carrying a 2023-looking volume — not present.**
  The entry reads Fouqué et al. 2018, *MNRAS* **475**, 1960, which is correct
  for that paper. No change made.
* **C minor, "whose sits" — not present.** The string does not occur in the
  manuscript. No change made.
* **C9b, "Sheikh et al. (2025a)" with no 2025b — real, and fixed.** The label
  carried a disambiguating suffix with nothing to disambiguate against; there
  is exactly one 2025 Sheikh entry. The suffix is dropped.

---

## Declined, with reasons

* **C1's worked numerical example in §4**, walking one real window from raw
  statistic to disposition. Declined on the page budget: the paper is at 28.98
  of 29 pages. What the round does instead is what the brief asked for, which
  is to expand the compressed, note-like passages into connected prose (the
  boxed rule, the false-alarm section, the exchangeability battery and the
  held-out check were all rewritten this way). The β Pictoris case already runs
  through the paper as the worked example, and Fig. 2's right-hand panel is the
  decision flow from window to disposition.
* **C8's enlargement of Fig. 3.** Declined on the page budget, but not
  worsened: the float sweep that closed the last page had shrunk this figure,
  and it was **restored to its v3.50 size** rather than left smaller than the
  referee found illegible. The figure is vector art and enlarges losslessly on
  screen.
* **C3(i) and D1's additional injection-recovery campaigns**, and D7's
  processing of all blocks for a 10-pc subset. Declined per the brief; the
  price is paid where referee C offers it, with the 0.5–2× completeness-transfer
  bracket now in the abstract and the conclusions and not only in an appendix.
* **D5's re-run with the mask removed.** Declined; the mask is reframed
  instead, as above.
* **C7's single consolidated exclusion table.** Declined on the page budget.
  The four classes of excluded entry are already itemised in one appendix
  subsection, and §5.2 cross-references it.
* **D's Zenodo DOI before acceptance, the arXiv identifier for White (2026),
  the CRediT split, the VBRL affiliation and competing-interest statement, and
  the submission git tag.** These are the authors', and they are recorded
  verbatim in `AUTHOR_ACTIONS.md`. Note that the tag comment still names
  `submitted-v3.32` in a v3.51 manuscript.
* **D's automated radiometer-equation sanity check (`Q = σ_measured /
  σ_radiometer`) in the pipeline.** Agreed in substance and already the
  mechanism by which the coarse-noise defect was caught, but adding it to the
  pipeline is future work and would not change a number here.

---

## Honest reporting of the metrics

The de-AI sweep was run after every prose increment, not once at the end, and
the antithesis count still rose from 38 to 42 (v3.50 → v3.51), almost all of it
my own new "rather than" constructions, of which the worst were removed in
stage 8 (28 → 12 for that construction alone). Em-dashes remain **0**.
Colon-explainers 110 → 113. Sentences stacking three or more quantities 247 →
248, four or more 191 → 190.

**One metric moved the wrong way and it should be said.** Main-text sentences
fell from 629 to 574 under the compression while the quantities stayed, so the
mean quantitative tokens per sentence rose from **1.85 to 1.94**. Compression
concentrates numbers. Referee C's complaint is specifically about missing
connecting logic, which the rewritten passages address directly, but the
density metric records the trade-off honestly.
