# Response to referees — v3.63

Manuscript: *An ALMA Archival Technosignature Search toward 81 Stellar Systems
within 40 pc* (White & Dey). Built from v3.62 (`a815af59ca96`).

Build state: **32 pages**, 31.20 pp of content; 0 LaTeX errors, 0 undefined
references or citations, 0 multiply-defined labels, 0 overfull boxes, 0 Type 3
fonts, 12 underfull hboxes (the narrow two-column measure), 849 generated
macros with 0 unused, abstract 1833 of arXiv's 1920 characters, arXiv source
set 44 items with 0 missing files.

**The page constraint was not met: the paper is 32 pages, not 31.** Section 0
below states the size of the miss and gives the authors three costed ways to
close it. We have not closed it by deleting evidence a referee asked for.

---

## 0. The page budget, stated plainly

> **Author decision, 2026-09-13: 32 pages accepted.** The 31-page figure was the
> authors' own budget, not a journal limit. Options 2 and 3 below are recorded
> for completeness but are not taken. Three further rounds of internal review
> (`PEER_REVIEW_ROUNDS_SUMMARY.md`) did not change the count.


The brief was that the paper must not grow. Both reports required additions:
a formal array-split robustness table (R1-6), a cross-validation of the radial
repair (R1-2, R2-M1), a solar-system crossmatch (R2-M3), a combined worst-case
sensitivity debit (R2-M5), a regulation-based replacement for a single FCC
filing (R2-minor-11), an orbital-phase fraction for TRAPPIST-1 b
(R2-minor-8), four software citations (R2-minor-10) and a recurrence-coverage
statement in the Discussion (R2-M2). Referee 1 simultaneously asked for the
paper to be *substantially shortened* (R1-12).

Added: about 0.87 pp. Paid back: about 0.67 pp, by

* withdrawing the tabulated occurrence ladder from Appendix I (R1-9) — 0.33 pp
  of float;
* compressing §5.5 (the superseded statistic), §4.4 (ancillary and validation
  analyses), the line-mask discussion in §5 and §6, and the framework prose of
  Appendix I;
* seven float-width reductions and five table font reductions;
* trimming the longest caption in the paper (Table 11, the selection function).

That leaves **0.20 pp on page 32, which carries bibliography only**. Three
options, in our order of preference:

1. **Accept 32 pages.** The content gained is referee-requested and load-bearing.
2. **Move §5.5 and Table 10 into Appendix H** and cut the resulting duplication.
   Referee 1's point 12 explicitly sanctions this ("the history of the
   analysis ... belongs in a reproducibility appendix"). Cost: an earlier
   referee asked for Table 10 to stay in the main text, so this reverses a
   previous decision and needs the authors' ruling.
3. **Drop Appendix I entirely**, replacing it with two sentences in §6.2.
   Cost: five cross-references to repoint, and the conditioning framework
   (Eq. C1) leaves the paper.

We decline to shrink Figure 3, which an earlier referee called illegible, or
Figure 1, which referee 2 asks to be made *more* legible (P3).

---

## Referee 1

### R1-1. Stop calling the construction a statistical "null" — **done**

The construction is now called a *spatial-control screen* and, where it is
being characterised, *an empirically calibrated screen for extreme values, not
an exactly exchangeable rank test*. "Null" survives only in its ordinary
statistical senses ("under the null", "the null result") and in the historical
description, which is what the referee asked for. The §5.4 heading, the
Figure 4 caption, the Table 8 caption, the abstract and the Conclusions all
carry the new wording.

### R1-2. The repair is not independently validated — **agreed, and we adopt your third option**

You are right that measuring $m(u)$ on the held-out sample and then testing the
detrended statistic on the same sample is not a validation. Two changes:

1. **Leave-one-star-out cross-validation** (`radius_matched_v363.py`). Each of
   the 27 held-out stars is scored against a profile fitted without it. The
   result is median rank 0.437, $D=0.081$, against 0.437 and 0.081 in sample.
   The profile is therefore **not over-fitted** — and equally, it **does not
   restore exchangeability**: the held-out median moves only 0.429 → 0.437.
2. **We no longer present the repaired statistic as a validated null.** The
   manuscript now says so in those words. The repairs are robustness checks on
   the dispositions; the survey's false-alarm budget is taken from the measured
   tail rate (§5.4, *The false-alarm rate, measured instead of assumed*), which
   is your preferred third route and was already how the paper's numbers were
   quoted.

### R1-3. Simplify the statistical narrative — **partially**

§4.4 is now explicitly labelled validation and robustness testing rather than
candidate generation, and compressed to a pointer-level summary. The three
operative levels — detection threshold, empirical spatial screen, astrophysical
and recurrence confirmation — are the structure of §5 and of Table 3. We have
**not** rebuilt Table 3 into a single master flow diagram, because at 0.20 pp
over budget we could not add a float; we flag it as the first thing to do if
the authors accept option 2 or 3 above.

### R1-4. "Pre-registered" — **done**

Three sites changed. The manuscript now claims only that the criteria were
"repository-timestamped before the validation sample was analysed" and, for the
CP−72 2713 repeat block, "prospectively frozen".

### R1-5. The ×1000.13 primary-beam correction — **you found a unit bug, and it is fixed**

This is the most important thing either report turned up. You were right to
refuse a beam correction of ~1000×, and the reason is that no such correction
exists. The twelve Band 9/10 rows restored at v3.60 were written by a separate
exporter that computed $S_{\min}$ in **millijanskys** while every other row of
the frozen export carries **janskys**. `v343_calc.py` infers the beam
correction as $S_{\min}/5\sigma_{\rm rms}$ and therefore read the unit error as
a factor of 1000.

* Verified independently: EIRP $=4\pi d^{2}S_{\min}\Delta\nu$ with
  $S_{\min}/1000$ reproduces the pipeline's own stored `EIRP_min_W` for those
  rows; with $S_{\min}$ as written it does not.
* Repaired at the point of use in `v342_calc.py`, with the freeze untouched and
  **an assertion added** that every row satisfy
  $0.95 < S_{\min}/5\sigma_{\rm rms} < 5$. That assertion would have caught
  this at v3.60.
* **The largest retained primary-beam correction is ×1.81**, at
  $0.46\,\theta_{\rm PB}$ (J1256−1257 Band 7). No EIRP, threshold or
  disposition ever used the corrupted column.
* We have also adopted the explicit cutoff you asked for: **a window is
  retained only where the primary-beam response at the stellar position is at
  least 0.5**, a correction of at most ×2. All 443 released windows satisfy it;
  the four withheld ε Eri windows fail it at ×2.9–3.4, which converts what was
  a case-by-case judgement into a rule.

This also answers referee 2's minor 4: the window is not in the released
catalogue because it never existed.

### R1-6. Re-extract the 141 ACA windows on the 7-m beam — **we give your stated minimum**

Re-extraction needs the raw visibilities and a full re-search of 141 windows,
which is beyond this cycle; the manuscript now says that in those words rather
than implying the choice was free. **Table 14 gives the formal robustness
table** you asked for as the minimum: windows, blocks, stars, systems,
crossings, rank-first windows against expectation, stage-1 outliers and the
stellar-rank KS statistic, for the 12-m and ACA 7-m strata side by side
(302/141 windows; 3/1 stage-1 outliers against 0.59/0.27 expected). No
disposition and no headline threshold depends on the ACA windows.

The two Band 9/10 blocks folded in at v3.62 were missing from the v3.43 archive
harvest; their array is now **measured** from ALMA TAP (0 of 45 and 0 of 44
antennas carry CM identifiers, so both are 12-m) rather than assumed.

### R1-7. Abstract vs Appendix A on the response+smearing product — **already fixed at v3.62**

$P_{\rm eff,total}=P_{\rm trig}\,C_{\rm resp}\,C_{\rm smear}$ is a released
catalogue column (range 1.33–3.98, median 2.29), and the Appendix A sentence
"no released column carries that product" was deleted when the column was
added. We checked: the string does not occur in the manuscript you read's
successor, and no contradiction remains.

### R1-8. One principal sensitivity quantity on every plot — **partially**

All three EIRP axes already read "nominal 5σ trigger EIRP" and the text leads
with $P_{\rm eff}$. Figure 1's caption now states explicitly that the plotted
values are triggers and what must be applied to them (see R2-M5). Rebuilding
the figures on $P_{\rm eff}$ itself is a data-regeneration job we did not
attempt in a cycle that was already over budget.

### R1-9. Hanning ×2.29 derivation and the injection caveat — **partially**

The derivation and the simulation agreement (×2.02–2.69, median ×2.31) remain in
Appendix B. The abstract now states the correction where the sensitivity is
first quoted. We did not move the derivation into the main text: it costs a
display equation we cannot afford.

### R1-10. Class A/B should be physical, not instrumental — **terminology changed**

Class A is now introduced as "the fine-channel spectral-carrier search" and
Class B as "the coarse-channel spectral-excess search"; "drift-resolved" is no
longer used as a synonym for Class A. The overlap is now given both ways: 6
Class A windows have $\eta_{\rm drift}<1$, 12 Class B windows reach
$\eta_{\rm drift}\geq1$, and **on the physical criterion alone 132 of 443
windows resolve drift against 126 in Class A**. We kept the labels rather than
reclassifying, because $\eta_{\rm drift}$ is a released column and any reader
can reclassify without us.

### R1-11. 4.474 GHz is 3.9 per cent, not 4.4 — **already fixed at v3.61**

The error was real and we found it independently one round earlier: a hand-set
literal measured on a superseded 93.1-GHz union. The manuscript now prints
4.474 of 113.86 GHz = 3.9 per cent, per band, from a generator. No "4.4 per
cent" remains.

### R1-12. Report masked crossings in a parallel table — **partially**

The cost of the mask in candidates, as opposed to bandwidth, is already
quantified in §5: 7 of the crossings fall inside a tube, 3 are the stage-1
outliers already dispositioned as CO, and the other 4 lie below their own
controls. We agree the parallel-table form is better and could not afford the
float. We have kept and sharpened the statement that these are *excluded search
space*, not searched-and-empty, and that a successor should search them with a
lower prior rather than delete them.

### R1-13. CP−72 2713 stays an unexplained event — **agreed, and made consistent**

One sentence in §5.3 could be read as saying astrophysical evidence disposes of
all four outliers. It now reads: the three are disposed of by astrophysical
evidence, "CP−72 2713 is disposed of by the absence of a repeat alone, and no
astrophysical attribution for it exists."

### R1-14. Reprocess the stage-1 windows in the visibility domain — **declined, with reason**

The visibility-domain fit for CP−72 2713 is already in §5.3 and is already
named in §6.4 as the first change a successor should make. Extending it to all
4 stage-1 or all 20 crossing windows requires re-downloading and recalibrating
the parent measurement sets, which is a new analysis campaign rather than a
revision. We have instead given the visibility result more weight in the text,
and said explicitly that the residual displacement in the rank statistic is why
we prefer visibility localisation to any further repair of a position-ranking
statistic.

### R1-15. Three sensitivity categories as a catalogue column — **not done**

The injection-grid reach (108 of 126 Class A windows interpolated, 18
extrapolated) is stated in Appendix B. Promoting it to a released column means
regenerating and re-freezing the catalogue, which we did not do in a cycle that
also repaired the catalogue's $S_{\min}$ column; doing both at once would make
the unit repair harder to audit. Flagged for the next build.

### R1-16. Shorten Appendix I — **done**

The tabulated occurrence ladder is withdrawn and the framework prose cut by
about a third. What remains is the conditioning equation, the two numbers, and
the three facts that bound how far they travel.

### R1-17. Figure 1 legibility — **declined, with reason** (see also R2-P3)

Splitting Figure 1 into two panels linking EIRP to spectral resolution is
already what panel (b) does. A third, linewidth-normalised representation would
need a transmitter-linewidth assumption the paper otherwise refuses to make,
and a larger float we cannot afford. The caption now carries the warning
explicitly.

### R1-18. The paper is too long — **agreed in principle, constrained in practice**

See section 0. We have cut where we could without deleting evidence; the
structural cut you are pointing at (moving the analysis history out of the main
text) is option 2 above and is the authors' call.

### R1-19. Restructure the abstract — **done**

The abstract now runs: sample and frequency range → fine/coarse class
distinction → effective sensitivity and the worst-case debit → the
non-detection → the four outliers and their dispositions → the methodological
contribution in two sentences → the scope caveat. The history of the repair is
one clause instead of three sentences. 1833 of 1920 characters.

### R1-20. Conclusions: results before lessons — **done**

*What was found* now opens with your sentence, essentially verbatim: "Within
the 126 drift-resolving windows toward 59 systems and the 317 coarse
spectral-excess windows toward the remainder, we find no persistent,
independently confirmed spectral technosignature at the calibrated sensitivity
of the archival observations."

---

## Referee 2

### M1. The exchangeability repair — **done, three ways**

* **Why detrending rather than radius matching**, from the physics: the trend
  is a property of the field, not of the star — pseudo-stars carrying no star
  at all are displaced as far as real ones — so removing a measured profile
  uses every probe, where radius matching discards nine in ten of them to
  approximate the same correction and costs a factor of nine in rank
  resolution. This is now stated where the choice is made.
* **Both repairs side by side across the whole survey**: Table 8 now carries a
  *Flagged, whole survey* row (5 under radius matching, 4 under detrending,
  against 8.1 and 0.86 expected by chance at the respective resolutions) as
  well as the per-window dispositions. The one window radius matching adds is a
  Class A window at $T_\star=5.11$ against 8.1 expected — i.e. it is what that
  screen's coarser resolution buys.
* **Why not a parametric beam model**: the windows mix 12-m and 7-m primary
  beams, and a displacement that survives at positions where no star is present
  is not the beam acting on a star. Stated in §5.4.

### M2. State the real detection limit and the recurrence coverage — **done, and it is now in §6.2**

New paragraph in §6.2: no single event in this design can clear the
survey-wide threshold, so a genuine but weak one-epoch transmitter is not
separable from the 1.2 chance events the survey expects — which is exactly
the position CP−72 2713 leaves us in. What separates them is a second epoch or
an independent identification, and **only 18 of 81 systems (22 per cent) were
searched in more than one execution block**. A further 45 hold archived blocks
that were not both processed, so the recurrence test could be extended to 78
per cent of the sample with no new observing time.

### M3. CP−72 2713: solar-system or near-field origin — **checked, and the answer is no**

We had not done this check; we have now. An IMCCE SkyBoT cone search at the
pointing and at each of the three sub-scan epochs of the flagged block
(2022-10-02, 00:25–00:40 UT) returns **zero** known minor planets at radii of
30, 300 and 1800 arcsec. The field is at ecliptic latitude −56°, and the
nearest major body (Saturn) is 57° away. **Positive control**: the same query
at the same epoch centred on the ecliptic returns 118–444 objects, so the null
return measures the field and is not a failed query. The frozen record is
`ssobody_cp72_v363.json`.

On follow-up: the manuscript now states that we intend to request a third
epoch — a single Band 7 execution reproducing the tuning — since two blocks two
hours apart cannot separate an intermittent emitter from a noise excursion.
**The authors should confirm they are content to commit to this in print**
(`AUTHOR_ACTIONS.md`).

### M4. Sample bias in the abstract — **done in part**

The abstract's closing sentence now reads that the sample "over-represents F
and G stars, so it constrains ALMA's observed stars and carries little weight
for the habitable-zone question", and its opening sentence says the 88/81 is
"the subset of a larger archive-covered set that carries usable spectral data"
(this also answers P5). The expanded "lessons for future archival
crossmatches" paragraph on the 53-of-168 phantom coverage is **not** added —
page budget — though we agree it would be useful and it is the cheapest
addition to make if option 2 or 3 in section 0 is taken.

### M5. Combine the two sensitivity debits — **done**

The abstract now states: searching Stokes $I$ alone forgoes a further ×1.41
that the individual parallel hands would give on a fully polarised carrier, so
the worst case debits a nominal 5σ trigger by **×3.2**. Figure 1's caption now
says explicitly that the plotted values are nominal triggers that exclude
*both* the ×2.29 median response correction and the ×1.41 polarisation factor.
The polarisation sentence is also reworded along the lines you suggested, so it
can no longer be read as claiming Stokes $I$ loses 29 per cent of a polarised
signal.

### P1. Terminology density — **partially**

The "second-stage local null" is renamed the **local scramble test**
throughout, which removes the false implication that it is stage 2 of the
stage-1 screening ladder. Table 1 is not restructured into two logical halves:
that is a float rebuild we could not afford.

### P2. Inline bold — **done**

Sentence-level bolding in running prose is cut from 12 to 4 (8 removed): the non-detection
statement in the abstract, the multiple-testing caveat in §4, the
calibrated-screen statement in §5.4 and the habitable-zone scope caveat in §6.3
— the four you identified as load-bearing. The remaining `\textbf` uses are
short labels inside Table 2.

### P3. Figure legibility — **declined, with reason**

See R1-17 for Figure 1. Figure 3 we will not shrink or split: an earlier
referee called it illegible at a smaller size, and splitting it into two panels
costs more total height than it saves. Both are flagged for the authors if the
page budget is relaxed.

### P4. Symbol overloading on "T" — **done**

The on-source track duration in Eq. (1) is renamed $\tau_{\rm track}$, and the
text says so explicitly, leaving $T$ for the search statistic.

### P5. Title/abstract numeric consistency — **done**, see M4.

### Minor comments

| # | Action |
|---|--------|
| 1 | Not done — the Wright et al. (2018) citation placement is a one-line move we could not verify was the first use in every rendering. Flagged. |
| 2 | Not done (page budget); the forward pointer costs a line in a packed column. |
| 3 | Not done. $\sigma(t,\nu)$ is per-integration, per-channel, from the window's own control ensemble; the statement is in Appendix G but not beside Eq. (2). Flagged as cheap. |
| 4 | **Moot** — see R1-5; the ×1000 window was a unit error, not a window. |
| 5 | Not done (float width). |
| 6 | Not done as a promotion to the Discussion; the point (spatial nulls lose power exactly where disc contamination is likeliest) is already made in §5.3 and in the exchangeability-violation list. |
| 7 | **The phrase you quote does not occur in the manuscript.** We checked the whole file; we think it is an artefact of text extraction from the PDF. The substantive worry is real and is fixed — see R1-13. |
| 8 | **Done, and measured.** TRAPPIST-1 b exceeds the drift ceiling over **5–29 per cent of its orbital phase** edge-on (the range spans the 13.3 and 12.0 Hz s⁻¹ GHz⁻¹ ceilings), falling to 0.3–10 per cent averaged over isotropic inclination. It is not generically unsearchable, and the text now says so. |
| 9 | **Done.** The sentence was not wrong but was unreadable, partly because 81−18 is also 63. It now reads: 18 of 81 searched in more than one block, *a further 45* holding archived blocks not both processed. |
| 10 | **Done.** CASA Team et al. (2022), Astropy Collaboration (2022), Harris et al. (2020) and Virtanen et al. (2020) added and cited in the Software section. |
| 11 | **Done, and strengthened.** Rather than add a caveat to one operator's filing, the argument is re-anchored on ITU Radio Regulations No. 5.340, which prohibits *all* emissions in bands covering **13.3 GHz, 11.6 per cent of the searched union**; a further **44 per cent** of the union lies above 275 GHz, which carried no allocation to any active service before the WRC-19 identifications. The SpaceX filing is retained and labelled as a snapshot. |
| 12 | Author action — the Zenodo placeholder DOI is in `AUTHOR_ACTIONS.md`. |
| 13 | Author action — affiliation ordering and corresponding-author marking, in `AUTHOR_ACTIONS.md`. |

---

## What we changed that neither referee asked for

* **A cross-assertion between rounds.** Twelve array-split macros were already
  generated in round 20 by a different code path. `v363_calc.py` recomputes all
  of them and *asserts* agreement instead of redefining them. This is the same
  defence that would have caught the v3.61 and v3.62 stale-literal defects, and
  it costs one line each.
* **An assertion on the $S_{\min}$ unit**, described under R1-5.

## Frozen inputs added this round

`radius_matched_v363.json` (both repairs, the leave-one-star-out
cross-validation, and the survey-wide flagged sets), `ssobody_cp72_v363.json`
(SkyBoT, with its positive control recorded inside the file),
`trappist_phase_v363.json`, `itu5340_v363.json`, `b910_array_v363.json`,
`pbatten_v363.json`. The two deterministic ones are rebuilt by
`v363_inputs.py`; the two network harvests ship frozen.
