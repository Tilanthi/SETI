# Referee report — round 1 of 5: internal consistency and arithmetic

**Manuscript:** `technosignatures_40pc_v3.85.tex` / `.pdf` (37 pp)
**Released catalogue checked against:** `per_target_results_v3.85.csv` (1655 rows, 50 columns)
**Scope of this round:** arithmetic, internal consistency, table/figure captions vs content,
cross-references, abstract support, and assertions the paper does not demonstrate.
No stylistic comments are offered.

Line numbers refer to `technosignatures_40pc_v3.85.tex`. Where a number is generated,
I name the macro so the author can find the generator rather than patch the prose.

---

## Summary of the referee's own checks

I re-derived from the released CSV: star/system/block counts, class split, crossing and
stage-1 counts, both stage-1 flags, the region-max flag, band histogram, channel widths,
`smin`, distances, `eta_drift`, `eta_smear`, drift ceilings, accelerations, all four power
columns and their ratios, per-system best thresholds, exposure, and the per-band table.
**Most of the paper's headline accounting is exactly right** (see §7 below for the list of
things I verified as correct). What follows are the places where it is not.

I raise **73 numbered points: 34 MAJOR, 37 MINOR, 1 borderline (C33), and 2 entries (C39, C40)
recorded as verified-correct**. The MAJOR ones cluster into three families:

1. **Numbers frozen at an earlier, 104-block / 443-window / 20-crossing / 4-flagged-window
   release**, which the completed sweep moved past (C1, C6, C16, C17, C20, C21, C24, C33, C35).
   The paper's own build machinery evidently does not assert these.
2. **Two statistics running in parallel** (the released rank and the radius-corrected rank),
   with the text switching between them mid-paragraph without telling the reader (C7, C8, C10, C12).
3. **A visibility-domain test reported with two opposite outcomes** for the same data (C4, C5, C37).

---

## 1. Numbers that disagree with the released catalogue

**C1 — MAJOR. "104 of the 104 searched execution blocks" — the survey has 404.**
> l.799: "Both parallel hands are delivered for \NPolBoth{} of the \NPolEB{} searched
> execution blocks, **which is all of them**"
> l.1536: "**All 104 of the 104** execution blocks deliver both parallel hands and 0 deliver
> a cross-hand product, so no Stokes Q, U or V is recoverable **for any searched window**"
> l.2624: "a per-hand search of the 104 blocks that deliver both parallel hands"

`\NPolEB = \NPolBoth = \NEbBothHands = 104` (`survey_numbers_round19/30.tex`). The science
sample is 404 execution blocks (CSV: 404 distinct `eb`). The polarisation-state query was run
on 104 blocks, i.e. **26 per cent of the survey**, and the paper generalises it to "all of them"
and to "any searched window". This is simultaneously an arithmetic error and a claim the paper
does not demonstrate for ~300 blocks. Either re-run the query on 404 blocks or state the figure
as "104 of the 404 blocks we queried".

**C2 — MAJOR. Table 5: "Threshold crossings (≥5σ at the stellar position) — 75 windows (all
Class A)". Four of them are Class B.**
l.666. CSV: of the 75 rows with `crossing = True`, **71 are Class A and 4 are Class B**. The body
says so itself — §5.3: "75 of the 1655 windows contain one, and **95 per cent of them are Class
A**" (71/75 = 94.7 %). The adjacent Table 5 row, "Star-exceeds-ring windows — 13 windows (all
Class A)", *is* correct (CSV: 13, all A). Fix the crossings row to "71 Class A, 4 Class B".

**C3 — MAJOR. The drift-ceiling range 1.1–5.9 kHz s⁻¹ is wrong; the true maximum is 10.5 kHz s⁻¹.**
> l.651 (Table 5): "Drift-rate ceilings — 1.1–5.9 kHz s⁻¹ (12.0–13.3 Hz s⁻¹ GHz⁻¹)"
> l.1191: "Across the 1655 windows maximum searched drift rates span 1.1–5.9 kHz s⁻¹"

CSV `drift_max_Hz_s`: **1085.9 to 10 466.7 Hz s⁻¹, i.e. 1.1–10.5 kHz s⁻¹**. Both numbers are
hard-typed in the source. The paper's own §6.4 and Fig. 12 give the right answer — "3.60 m s⁻²,
which is 1.4 kHz s⁻¹ at 115 GHz and **10.5 kHz s⁻¹ at 872 GHz**" — so §4.2/Table 5 contradict
§6.4 as well as the data. 5.9 kHz s⁻¹ corresponds to ~470 GHz, i.e. it omits Bands 9 and 10.

**C4 — MAJOR. Table 10's caption says the visibility test was not done; §5.3 and Table 9 say it was.**
> l.1878 (Table 10 caption): "**None of the four has been tested in the visibility domain.**"
> l.1808 (§5.3): "***All four have been tested in the visibility domain**, and none behaves like
> a source at the star*"

Table 9 tabulates the test for all four, and Fig. 7 plots it. Delete the caption sentence.

**C5 — MAJOR. The CP−72 2713 visibility test is reported with two opposite results.**
> Table 9 (l.~1841): CP−72 2713, N_vis = 405 860, **Re/σ = +2.30**, Im/σ = −0.71, verdict
> "**no significant point source**"; and §5.3: "**0 of the 4 events shows a point source at the
> star.** The largest real part is 2.5σ, which is not a detection"
> §G.5: "Over **405 860** visibilities the fit returns 10.4 mJy at the star, **5.5σ** against
> 1.89 mJy noise (Δχ² = 30), an imaginary part of 0.03σ *as a real source on the phase centre
> requires*, and a best-fitting position on the star. … **The feature is point-source-like and at
> the stellar position in the first block**, a stronger statement than the image-plane statistic
> alone supported"

Same block, same 405 860 visibilities, opposite conclusions (2.3σ vs 5.5σ; Im/σ = −0.71 vs 0.03).
The macros behind §G.5 (`VisStarSnr = 5.5`, `VisStarImagSnr = 0.03`, `VisNVis = 405 860`) are from
the older continuum-subtracted fit; Table 9 is from `vistest_v384/85`. One of the two must be
withdrawn or the difference in method (continuum removed? channel choice?) stated explicitly —
as it stands the paper contains a 5.5σ point source at a star it reports as a non-detection.
**This is the single most damaging inconsistency in the manuscript.**

**C6 — MAJOR. Table 22 claims to audit "every window the region-maximum statistic flags"; it has 7
rows, and the statistic flags 66.**
> Introduction (l.~170): "Over this survey the region form **flags 66 windows, 19 per cent of its
> 350 crossings**, against 13 under Eq. 2 … and **Table 22 audits every window the region form flags**"
> Table 22 caption (l.3859): "**Every window the region-maximum statistic flags**, under both statistics"
> §5 (l.1634) and §G.4 (l.4070): "the symmetric form … flags a strict subset … **seven windows
> against four**"

CSV: `stage1_flag_regionmax` is True in **66** rows; `star_snr_regionmax ≥ 5` in **350** rows. So
the intro is right and Table 22 + §G.4 + §5 are a leftover from a 7-window reprocessing subset.
Either the caption should read "the seven locally reprocessed windows" (consistent with §F/§G.2)
or the table must be rebuilt with 66 rows. As printed, "seven windows against four" also flatly
contradicts "66 … against 13" three pages earlier.

**C7 — MAJOR. The paper adopts one statistic as primary and reports the other everywhere.**
> §5.3.2 (l.2095): "**We therefore adopt the radius-corrected statistic as the primary one.** On it
> the survey has **10** stage-1 outliers, **8** attributed to circumstellar or foreground CO and
> **2 unattributed**."
> Abstract, §4.6 step 9, Table 11, Fig. 3 step 9, Conclusions 2: **13 / 9 / 4**, "**4** … against
> **3.2** expected by chance".

If the radius-corrected statistic is primary, the abstract and conclusions quote a secondary
statistic; if the released statistic is primary, §5.3.2 should not say "adopt … as the primary
one". The chance comparison inherits the problem: 3.2 = 1655/513 is the expectation for the
*released* screen, and it is compared in §5.3.2 with the *corrected* count of 2. Pick one.

**C8 — MAJOR. "2 are observed" inside a paragraph whose subject is the 4 unattributed events.**
> §5.3 (l.~1770): "The remaining **4** have no astrophysical attribution. How many should chance
> produce? … a survey of this shape produces **3.5** unattributed stage-1 outliers on average, with
> a 95 per cent interval of 0–7 … The naive Poisson figure, 3.1, sits inside that interval …
> **2 are observed, and P(≥2) = 0.87** on the resampled null. The unexplained population is what
> chance predicts."

`\LocCorrUnattrib = 2` is the radius-corrected count (C7), silently substituted into a paragraph
about the 4. On its own terms the sentence should read "4 are observed, and P(≥4) = …".
Also in the same paragraph: "over 404 blocks and **1614** windows" — the survey is 1655 windows
(1616 distinct datasets); 1614 appears nowhere else and is not defined (see also C22).

**C9 — MAJOR. The trials-denominator comparison in §4.1 is the wrong way round.**
> l.536: "We use **the larger number** as the trials denominator throughout, which is conservative
> and makes no practical difference: **it predicts 3.1 chance outliers against 3.2 for the smaller**."

1655/513 = 3.23 and 1616/513 = 3.15. The larger denominator predicts **3.2**, the smaller **3.1** —
the values are swapped (`\BootPoisson = 3.1`, `\ExpDistinctDen = 3.2`). Appendix F confirms the
correct arithmetic: "the survey expectation 1655/513 = 3.23 flags". As printed, the sentence also
contradicts its own word "conservative".

**C10 — MAJOR. Five different chance expectations, and Table 8 names the wrong one as the one in use.**
Values in circulation: **3.1** (Poisson, §4.1/Table 8), **3.2** (abstract, §4.6, Table 11, Fig. 3,
conclusions, Appendix F), **3.5** (block resampling, §5.3/Table 8), **3.9** (tail-corrected,
Table 8), **4.7** (§5.3.6, §6.2, §G.3.3), plus **3.13** (§F, C24) and **8.1** (§G.3.1, radius
matching). Table 8's caption states: "**the block-resampled figure is the one the text uses**,
because it is the only one that respects the dependence structure of the survey" — but the text
uses 3.2 in the abstract and conclusions and 4.7 in §5.3.6 and §6.2. Related: the tail factor is
1.2 (§5.3.1, hold-out), 1.4 (Table 20 caption, §G.3.3 "read as multiplied by 1.4") and 1.5
(§G.3.3 recomputed). One number should carry the headline, with the others explicitly labelled
as alternatives.

**C11 — MAJOR. A point estimate outside its own confidence interval.**
> §5.3.1 (l.2045): "clustering removes neither the shift nor its significance, 99 of the 149
> blocks having a mean rank below 0.5 (sign test p < 0.001) and a **star-clustered bootstrap
> placing the median at 0.405 (95 per cent interval 0.42–0.46)**"

0.405 is not in [0.42, 0.46]. The interval (`\HOBootLo/\HOBootHi`) was measured for a median of
0.419 in the previous release; the median has since moved to 0.405 and the interval has not.

**C12 — MAJOR. "improves from 0.445 to 0.432" — that is a worsening, and it undercuts the section's thesis.**
> §5.3.2 (l.2103): "The median add-one rank **improves** from 0.445 to 0.432 over the whole survey,
> which is the residual the correction cannot reach"

0.5 is the exchangeable value. Moving 0.445 → 0.432 moves **away** from 0.5. CSV confirms:
median `p_rank_addone` = 0.4464, median `p_rank_local` = 0.4327. So the radius correction, which
§5.3.2 introduces as the repair that "removes the gradient by construction", leaves the stellar
rank *more* displaced than before. Two paragraphs earlier the same section's radius-matching test
correctly reports an improvement ("the survey median moves from 0.448 to 0.455"). This needs
either a correction of the word or — better — an honest sentence about what it means that the
adopted repair increases the displacement.
Related: the survey median add-one rank appears as **0.45** (§5.3.1), **0.448** (§5.3.2),
**0.445** (§5.3.2), **0.466** (§G.3.1) and 0.4464 in the CSV. At most two of these can be the
same quantity; none is defined differently in the text.

**C13 — MAJOR. β Pictoris: four blocks or eight?**
> §4.4: "the recovery and localisation of β Pictoris CO in two transitions and **four execution blocks**"
> §5.3.4 (l.2191): "recovered blind by the frozen pipeline, in two transitions, **in four execution
> blocks**, across nine years"
> §5.3, Table 11 area and conclusions: "8 are β Pictoris, in 5 Band 3 and 3 Band 6 windows drawn
> from **8 execution blocks**"; abstract: "**8 observations**"

CSV: the 8 β Pic stage-1 windows come from **8 distinct execution blocks** (5 in B3: `…Xeb8`,
`…Xe19`, `…Xcc5`, `…X32f1`, `…Xf4df6f_Xc7`; 3 in B6). "Four" is the block count of the single
Band 3 member OUS. The introduction adds a third value: "across two transitions and **three epochs**".

**C14 — MAJOR. "by the same number" cannot give two different p-values.**
> §5.3.4: "the Band 3 peak T⋆ = 30.76 is matched or exceeded by **0 of the 1655** per-window control
> maxima and the Band 6 peak T⋆ = 11.68 **by the same number**, add-one **p = 0.001 and 0.010**."

If both are exceeded by 0 of 1655, both add-one p-values are 1/1656 = 6×10⁻⁴. p = 0.010 implies
~16 exceedances. Either the counts differ (state them) or the p-values do not.

**C15 — MAJOR. Appendix B: "113 of the 403 (86 per cent)" is neither 86 per cent nor consistent with
the 19 exceptions.**
> App. B: "Every Class A window lies in a band the grid samples; **113 of the 403 (86 per cent)**
> lie inside it on all three axes at once. **The 19 that do not** are extrapolations, 18 of them in
> integration count alone and 1 in channel width."

113/403 = 28 per cent, and 113 + 19 = 132 ≠ 403. The self-consistent reading is 384 of 403
(95 per cent) with 19 extrapolations. The following sentence ("read as measured for the 86 per
cent") inherits whichever number is right.

**C16 — MAJOR. "the 20 fine windows with any ≥5σ stellar crossing" — there are 71.**
> App. F (l.3696): "excluding the **20** fine windows with any ≥5σ stellar crossing restores
> uniformity (p = 0.39)"

`\NCrossWin = 20` is stale; CSV gives **71** Class A windows with a crossing (of 75 total). The
same stale count appears twice more: §5.3.7 "would exclude **19 of 20 crossings**" and §G.5 "the
same query at the **20 crossing frequencies** returns a transition within 60 km s⁻¹ for 19 of
them". The survey has 75 crossings.

**C17 — MAJOR. The masked-crossing ledger disagrees with itself by a factor three.**
> §5.3.7: "**17 of the 75 crossings** fall inside a tube, **9** of them are the stage-1 outliers
> already dispositioned as CO …, and the remaining **8** do not exceed their own control ensembles"
> App. D: "of the 75 windows with an on-star crossing, 13 also beat their control ring and **three
> of those** are accounted for by the mask. **Two further** crossing windows fall inside the mask
> without beating their ring … **The other 16** are ordinary noise crossings"

9 + 8 = 17 versus 3 + 2 = 5, on the same 75 crossings. Appendix D's "other 16" does not reconcile
with either (17 − 5 = 12; 75 − 17 = 58).

**C18 — MAJOR. The mask is quoted as costing 4.1 per cent of the union in six places and 0.75 per
cent in one.**
> §5.3.7 (l.2452): "a full Splatalogue selection would mask 75.1 per cent of the union **against
> 0.75 per cent here**"
> §4.2, §5.3.7, §5.5, Table 18, conclusions: the mask costs **4.1 per cent** of the union
> (118.13 → 113.31 GHz, Table 18 "All" row: 4.811 GHz masked).

`\MaskOwnPctUnion = 0.75` must be a different quantity (a narrower tolerance?). As written the
comparison is not like for like and contradicts Table 18.

**C19 — MAJOR. The per-class mask costs cannot add up to the survey mask cost.**
> §5.3.7 (l.2494): "**0.45 GHz** of the 47.7 GHz Class A union (0.9 per cent) against **0.23 GHz**
> of 90.5 GHz in Class B (0.3 per cent)"

Every masked interval in the 118.1 GHz union lies in a Class A window, a Class B window, or both,
so the union's masked total cannot exceed 0.45 + 0.23 = 0.68 GHz — against the **4.811 GHz** of
Table 18 (which is internally perfect: the per-band masked column sums to 4.811, and every
"Left" and "Lost %" entry checks out). A factor 7 is unaccounted for. The dependent claim "the
fine-channel experiment therefore pays three times the fractional price" rests on these two numbers.

**C20 — MAJOR. §G.3.1 reports the pre-sweep flagged set and contradicts §5.3.2 on what is adopted.**
> §G.3.1 (l.3941): "Under the adopted screen **the flagged set is the released one, 4 windows**,
> with 0 added and 0 lost … **The number of unattributed stage-1 outliers is one** for every repair
> and every debit between zero and 0.61σ"
> §G.3.1 also: "**We adopt detrending** … The stellar debit m(0) **is the one free choice**"
> §5.3.2: "**The stellar debit m(0) is no longer needed and is not used in the primary analysis** …
> We therefore adopt the radius-corrected statistic as the primary one"

The released flagged set is **13** windows with **4** unattributed. Table 23 ("Flagged, whole
survey: 5 / 4") carries the same pre-sweep counts. And the two sections adopt different repairs.

**C21 — MAJOR. §F.1's rank-first accounting does not close, and quotes an impossible probability.**
> "The survey expectation is 3.23 and **16 are observed**; the execution-block clustered permutation
> returns **P(≥16) = 2.2 × 10⁻¹**, and the excess is astrophysical, celestial line emission sitting
> at the stellar position **in 3 of the 16** (Table 11) and **leaving 2 against 3.23 expected**."

16 − 3 = 13, not 2. Table 11 attributes **9** of the flagged windows to CO, not 3. And a Poisson
(or clustered) probability of observing ≥16 when 3.23 are expected cannot be 0.22 — the macro
used (`\ClustPfive = 2.2e-1`) is by its name a P(≥5). Note the count 16 itself is supported
(Table 20: 9 + 7 rank-first), so only the attribution arithmetic and the p-value are wrong.

**C22 — MAJOR. Stage-1 outliers in the ACA stratum: 1 or 4?**
> §F (l.3562): "Of the stage-1 outliers **only HD 48370 Band 6 is ACA**."
> §F next paragraph: "The 12 m stratum holds **9 of the 13** stage-1 outliers, **the one lost**
> being HD 48370's foreground CO"
> Table 20: stage-1 outliers — 12 m: **9**; ACA 7 m: **4**.

9 + 4 = 13, so four stage-1 windows are ACA, not one, and dropping the ACA stratum loses four
(including, by Table 11's list, unattributed events) rather than one attributed line. The
conclusion drawn — "no survey-level statement changes" — depends on which is true.

**C23 — MAJOR. Table 20's caption arithmetic.**
> "Expected rank-first counts are N_win/(512+1) … the measured tail rate is a factor 1.4 higher,
> **which brings the 12 m stratum's 9 observed within one of expectation**."

1.17 × 1.4 = 1.6. Nine observed is not "within one" of 1.6; it is a factor 5.5 above it. (The
sentence would be true of 2 observed, which is what this stratum held in the previous release.)

**C24 — MAJOR. "one unattributed crossing among 416" after excluding 15 windows from 1655.**
> §F: "Excluding the **15** β Pictoris windows leaves **one unattributed crossing among 416**,
> against **3.13** expected (P(≥1) = 96 per cent)."

1655 − 15 = 1640, and the survey has 4 unattributed events. 416/513 = 0.81, not 3.13; 3.13
corresponds to ~1605 windows. `\NNonBP = 416` and `\ExpNonBP = 3.13` are mutually inconsistent
as well as inconsistent with the survey.

---

## 2. Table entries that disagree with the catalogue they are said to summarise

**C25 — MAJOR. Table 5's Class A P_eff row is inconsistent with the catalogue and with the paper's
own P₉₀ = 1.2 P_eff relation.**
Table 5 (l.~655–660) gives, for Class A: `P90 = 1.2 Peff` **6.3×10¹³–1.1×10¹⁷ (median 2.4×10¹⁵)**
and `Peff = 2.29 Ptrig` **5.1×10¹³–1.6×10¹⁷ (median 2.1×10¹⁵)**.

* CSV `eirp_p90_W` (Class A): 6.27×10¹³ – 1.12×10¹⁷, median 2.37×10¹⁵ — **row 1 is right**.
* CSV `eirp_eff_total_W` (Class A): 5.10×10¹³ – **9.14×10¹⁶**, median **1.93×10¹⁵** — row 2's
  maximum and median are **not** the catalogue's; they are 2.29 × Ptrig, which is only correct
  where `c_response_smear` = 2.29 (the column runs 1.33–3.98, as Fig. 10's caption itself says).
* Consistency test on Table 5's own numbers: 1.2 × 1.6×10¹⁷ = 1.9×10¹⁷ ≠ 1.1×10¹⁷, and
  1.2 × 2.1×10¹⁵ = 2.6×10¹⁵ ≠ 2.4×10¹⁵. The catalogue ratio is a constant 1.2289, so the
  relation must hold exactly on min, median and max — it does not.

The Class B row (3.7×10¹³–6.4×10¹⁷, median 1.4×10¹⁵) *does* match the catalogue. Only Class A
is affected.

**C26 — MAJOR. "178 of the 1655 windows come from 3 systems (10.8 per cent)" — the catalogue says 285 (17.2 per cent).**
l.473 (`\ConcThreeWin = 178`, `\ConcThreePct = 10.8`) and §6.3 "three systems carry 10.8 per cent of
the searched windows". CSV, top three by `system_id`: Proxima Cen 100, BD05 1668 100, HD 33793 85
= **285 windows = 17.2 per cent** (identical if the 1616 de-duplicated datasets are used). The
statement is used in the discussion as evidence about sample concentration, so the error runs the
wrong way for the paper's own argument.

**C27 — MAJOR. "41 per cent are M dwarfs" is hard-typed and contradicts the table it cites.**
> §6.3: "Among the stars with a Gaia temperature, **41 per cent** are M dwarfs against 69 per cent
> of the reference census (Table 16)"

Table 16 and Table 4 give M = **21** of **57** classified = **36.8 per cent** (Table 16 even prints
"21 (36.8 %)"). 69 per cent for the census is right (5908/8594). Note this is one of the few
percentages in the paper not driven by a macro.

**C28 — MINOR (but a direct contradiction). Temperatures available for 55 or 57 stars?**
> §3 (l.481): "The spectral-class proxy is `teff_gspphot`, available for **55 of 94** sample stars"
> Table 16: "Temperatures are available for **57 of the 94**"; Fig. 2: "searched here (**57**
> classified)"; Table 4's N_searched column sums to **57**.

`\NTeffStars = 55` against a table built on 57.

**C29 — MAJOR. Table 3's "Stars" column holds systems for the science sample.**
`tab_partitions_v385.tex`: "Science sample | 404 | 1655 | **87** | …". The science sample is
**94 stars in 87 systems** (abstract, §3, §4.1, Table 5, CSV). The hold-out row (36) and the
out-of-sample row (22) are presumably star counts, so the column mixes units. Rename the column or
give 94.

**C30 — MAJOR. "446 windows" is not 1655 − 9, and the release only carries η_smear for 455 windows.**
> §4.2 (l.1199): "Intra-integration smearing is negligible for **446** windows: at most 1.10
> channels, median 0.001. **9** windows have η_smear < 0.99"
> App. A: "The frequency excursion … is at most 1.10 channels **across the 1655 windows** …
> **The remaining 446** agree with their nominal thresholds to better than 1 per cent."

1655 − 9 = 1646. CSV: `eta_smear` is populated for **455** rows only (446 + 9), and empty for
1200 rows — so the claim "across the 1655 windows" is also unsupported by the release. Either
populate the column or say "of the 455 windows for which the term is evaluated". (The nine
exceptions listed in Appendix A match the CSV exactly, including the five 15.3-kHz Band 6 windows.)

**C31 — MAJOR. "the 12 ε Eri Band 6 windows … select the same four windows".**
> §4.3 (l.1260): "Beyond it are the **12** ε Eri Band 6 windows at 1.0–3.5×, which is also past the
> first sidelobe transition … the two criteria are independent and **select the same four windows.
> We withhold them**"

Twelve windows, then "the same four windows", then "them". Table 5's withheld count is 12
(`\NWithheld = 12`), so "four" is the stale number.

**C32 — MAJOR. Figure 13 prints p-values that contradict its caption and the text.**
`figures/control_diagnostics.pdf` panel (b) prints "**fine p<0.001, coarse p=0.004**", and panel
(a) prints **p<0.01 for B6 and for B7**. The caption says "The ensemble tracks the on-star
statistic in every band and both channelisation classes. **The one departure is the drift-search
class (p = 0.015)**", and the body (§F) says the fine class fails "**at p = 0.015** (n = 403)" and
implies the coarse class is uniform. Three different values for the fine class (0.015 vs <0.001)
and a coarse-class departure (0.004) that the text denies exists.

**C33 — MINOR→MAJOR. §5.1's Barnard's Star / Wolf 359 numbers do not match the catalogue.**
> l.1649: "The nominal EIRP₅σ trigger thresholds are 6.2–6.9 × 10¹³ W for Barnard's Star **over
> four windows** and 7.8–9.1 × 10¹³ W for Wolf 359"

CSV: Barnard's Star has **12** Band 6 windows spanning **6.2–9.3 × 10¹³ W**; Wolf 359 has **12**
Band 6 windows spanning **7.3 × 10¹³ – 1.1 × 10¹⁴ W**. The quoted ranges are those of the four
deepest windows each. Since this subsection claims the first mm/submm limits for these stars, the
numbers should be the released ones.

**C34 — MINOR. Table 5's "On-source time per window … median 2087 s" is not a per-window median.**
CSV median `on_source_s` = **2812 s** (Class A 2389 s, Class B 2964 s, per-EB 2843 s). 2087 s is
the median of the **per-star/band** medians (`\OnsrcMedian`; I reproduce 2086.6 s that way). The
range 21–5274 s is correct. Either relabel the row or use the per-window median.

**C35 — MAJOR. Table 12 is a pre-sweep table: its caption, its column count and its sample labels
all conflict with §5.3.**
> Table 12 caption: "(b) **the three** unattributed single-epoch outliers, **one from the frozen
> survey and two from the calibration sample**" — the table then prints **four** columns
> (CP−72 2713, 61 Vir, HD 14055, HD 23484) and its own header line reads "The **four** unattributed
> single-epoch outliers", with 61 Vir / HD 14055 / HD 23484 labelled sample "**calib.**"

But Tables 10 and 11 present those same three events (identical T⋆ = 6.16, 6.03, 5.30 and identical
ring maxima) as **science-sample** stage-1 outliers of the completed sweep, and the CSV carries
them as survey rows. A reader cannot tell whether these three events are in the headline 13 or in
the calibration sample; the paper needs them in exactly one place.

Directly coupled to this: §5.3.1 says the three "**Re-searched at its own tuning in further blocks
of the same star**, each falls back into the body of its own control distribution: 4.83 with 119
controls above the star, 5.51 with 5, and 4.99 with 21" — i.e. repeat observations exist and were
searched — while Table 10 records "repeat blocks: **none**" for all three and §5.3 says "the other
3 sit in the **only block that covers their frequency, so no persistence test exists for them**".

---

## 3. Abstract and conclusions: support in the body

**C36 — MAJOR. "none recurs" is asserted for four events of which three have no recurrence test.**
> Abstract: "The remaining 4 have no identification, against 3.2 expected by chance, and **none recurs**."
> §4.6 step 10: "**None of the 4 recurs** in a second epoch of the same target"
> Conclusions 2: "**none recurs in a second epoch**"
> against §5.3: "only one has a repeat observation … the other 3 sit in the only block that covers
> their frequency, **so no persistence test exists for them**", and Table 10 ("repeat blocks: none").

"None recurs" should be "the one event with a second epoch does not recur; the other three admit
no recurrence test" — which is also what the conclusion about confirmation needs. (If §5.3.1's
re-searches are the missing tests, then C35 must be fixed and they must be reported here.)

**C37 — MAJOR. §6.4 says the visibility test was applied to one window and that the visibilities
were not retained.**
> §6.4: "**Applied to the one unattributed window** (§5.3) the visibility fit was decisive; applied
> to every window it would … **Doing so needs the visibilities retained, which this survey did not
> do**, and it is the first change we would make."

§5.3 recalibrated four blocks from the raw archive and applied the test to all four (Table 9,
Fig. 7). The recommendation is still valid, but as written it contradicts the results section.

**C38 — MINOR. Abstract's "8 observations" vs §4.4/§5.3.4 "four execution blocks"** — see C13.

**C39 — OK (checked, no issue). Abstract's "recovered nine times in ten above 2.4×10¹⁵ W at the median window and
6.3×10¹³ W at the deepest, with a window-to-window scatter of ×0.48–×1.35"** — all verified against
the CSV and Table 5. No issue; recorded here because I checked it.

**C40 — OK (checked, no issue). Abstract's "the sample is 94 catalogue stars in 87 systems"** is right and is
contradicted only by Table 3 (C29).

---

## 4. Cross-references that compile but do not point where intended

**C41 — MAJOR. Two labels on one table make Table 5 point twice at the same table.**
l.1423–1424: `\label{tab:dwell}` and `\label{tab:classcomp}` are both attached to Table 7. Table 5's
completeness row (l.665) therefore renders "**Table 7 (amplitude); Table 7 (dwell)**". The
amplitude-completeness results live in Appendix B / **Table 15** (`tab:driftstrata`), which is
presumably the intended target of `tab:classcomp`. This is exactly the failure mode where a
reference resolves and is still wrong.

**C42 — MINOR. Table 2's caption claims exclusivity it does not have.**
> Table 2: "**Every term and every power scale in this paper is defined here and nowhere else**"

Table 1 (the glossary, one page earlier) defines P_trig, P_eff, P₅₀/P₉₀, crossing, stage-1,
hold-out, drift and add-one rank as well. Two glossaries of the same quantities is a structural
choice, but the caption's claim is false as printed.

**C43 — MINOR. §5.3.3 is a signpost containing no content** ("… are all calibration rather than
result, and are collected in Appendix F"). Not an error, but the section number is referenced from
§4.2 and §5.3 as if it held the calibration.

**C44 — MINOR. "the four stage-1 windows".** §F.1 and §G.1 both speak of "the four stage-1 windows"
(meaning those with retained control spectra) while the survey has 13 stage-1 windows and §G.3.2
says "the 4 stage-1 windows of the released catalogue **for which the full control vectors were
retained**" — the correct, qualified form. Use it in all three places.

---

## 5. Captions vs content

**C45 — MINOR. Table 7's caption describes an entry the table does not contain.**
> "**The 0 of 500 coarse-window entry** is a property of the test, not of the pipeline"

Table 7(a)'s drift column reads "none" for both Class B rows; "0 of 500" appears only in §4.5 and
Appendix B. Either print the entry or reword the caption.

**C46 — MINOR. Table 7 note a: "transfer to the other 403 Class A windows".** There are 403 in
total, one of which is the calibration configuration; "the other" should be 402.

**C47 — MINOR. Fig. 3's caption counts three denominators and lists four.**
> "The **three** denominators the text keeps apart are the catalogued population, the 168-entry
> ALMA-covered work list, the ~115 stars a public field genuinely contains, **and the 94 searched**."

Also: "Every count is read from the generated macros, so **the figure, the list and the released
catalogue cannot disagree**" — the figure and list do agree with the CSV, but as a general claim
about the paper it is refuted by C2, C3, C25, C26 and C34.

**C48 — MINOR. Fig. 1's caption titles itself on the wrong quantity.**
> "Fig. 1 — **Literature context of the 5σ trigger thresholds**, in total power (§2). (a) EIRP
> against distance. Blue: this survey, plotted as **P₉₀**…"

The survey points are P₉₀, as the ordinate says ("EIRP for 90 per cent recovery"); only the
literature points are 5σ triggers. Related: 25 of the 94 plotted points are Class B, for which the
paper states that no measured completeness curve exists ("completeness-calibrated exclusion holds
only in Class A", §6.2; Table 5 defines P₉₀ for Class A only). Plotting P₉₀ for Class B stars needs
justifying or the panel should mark them differently. The caption also omits the legend's third
entry ("flagged window").

**C49 — MINOR. Table 5's caption: "Every count quoted in this paper reconciles with it."** Not true
as printed (C2 is in the table itself; C25, C26, C34 are quoted elsewhere).

**C50 — MINOR. Table 11's caption says the unattributed pairs are "consistent with the 3.2 expected
by chance (p = 0.40)"** while Table 8 says the text uses 3.5 and §G.3.3 predicts 4.7 (C10).

---

## 6. Smaller numerical and unit slips

**C51 — MINOR. Exposure unit conversion.** §5.3.7: "Total exposure is **6.8 × 10⁶ s GHz, or 393
star-hour-GHz**". I reproduce 6.84 × 10⁶ s GHz from the CSV (Σ on_source × bandwidth) — but that is
**1.9 × 10³ hour GHz**, not 393. The word "or" asserts a unit conversion which is wrong by ×4.8.
If "star-hour-GHz" de-duplicates something (per star? per union?), define it.

**C52 — MINOR. "|a_los| = 3.6–3.9 m s⁻²" (§4.2) vs "3.60–4.00 m s⁻²" (§4.5, §5.5, Fig. 12) vs
"3.6–4.0" (§4.2, Table 5).** 12.0–13.3 Hz s⁻¹ GHz⁻¹ × 0.2998 = 3.60–3.99; the CSV's `a_max_m_s2`
takes exactly two values, 3.598 and 3.999. Use one rounding.

**C53 — MINOR. Trial drift count 2–1944 (§4.2, §5.3.4) vs CSV maximum 1945.**

**C54 — MINOR. "3533 channels" (§5.3.4) vs "3,534 channels" (same subsection, `\BpRecNChan`).**

**C55 — MINOR. "across nine years" (§5.3.4, twice) vs "over 8.4 yr from 2013-10-06 to 2022-03-03"**
(same subsection).

**C56 — MINOR. β Pic crossing offsets: "within 3.6 km s⁻¹ of the stellar systemic" (§5.3.7) vs
"All three lie within 0.46 km s⁻¹ of systemic" (§5.3.4) and Table 21 (−0.39, −0.29, −0.46).**

**C57 — MINOR. "All twelve Band 8 windows here belong to η Crv, HD 48370 and HD 61005" (§G.3).**
Table 5, Table 17 and the CSV all give **24** Band 8 windows (3 systems, 6 blocks). The 12 is the
Band 9+10 count (§G.6, correctly).

**C58 — MINOR. "the 0 Band 9 and 10 windows, absent from the metadata snapshot, take ALMA's default"
(App. A).** Arithmetically consistent (1509 + 146 + 0 = 1655) but reads as a claim about an empty
set, and sits one appendix away from "The **12** Band 9/10 windows toward AU Mic and HD 61005".

**C59 — MINOR. "17 transitions of 11 species" vs "the 9 frozen species" (both §5.3.7),** with a
species list that names nine entries, one of which ("the CO isotopologues") is plural.

**C60 — MINOR. Appendix D: "5,114 of 235 carriers"** — a count of transitions described with the
unit of carriers; the sentence as printed has no consistent reading.

**C61 — MINOR. §6.2: "the remaining 97.5 GHz (Bands 4–8) lies wholly outside it".** The union runs
to 873.1 GHz and includes Bands 9 and 10 (4 + 8 windows, 20.7 GHz of union in Table 17/18); the
parenthesis should read Bands 4–10.

**C62 — MINOR. Table 19's decomposition does not multiply out.** The caption offers 3.0 and 1.9 as
"**the two multiplicative parts of that factor**", the factor being 1.5 (55 observed / 37.8
expected). 3.0 × 1.9 = 5.7. (5.7 is the right factor for the *total* 229 cells against 37.8 —
i.e. the decomposition applies to a different numerator than the one printed above it.)

**C63 — MINOR. §6.1: "Read on the trigger, 1 systems of 87 reach the numerical EIRP of the Arecibo
planetary radar and 4 reach twice it".** Working on the deepest Class B window per system, the CSV
gives **2** systems at ≤2.0 × 10¹³ W (G 272-61A at 1.62 × 10¹³, Proxima Cen at 1.99 × 10¹³) and 4 at
≤4.0 × 10¹³ W. The P_eff counts (0 and 1) reproduce exactly. Check whether Proxima is being excluded
by a slightly different Arecibo value. Also, the stated denominator "87 systems" is right for Class
B but the Class A statements in the same paragraph are over 65 systems.

**C64 — MINOR. §6.4: "analysing them would make a multi-epoch survey of 54 stars".** 54 systems
**already** have more than one block (§6.2, Fig. 6b); the number the extension buys is 70
("70 in all … 80 per cent"). §3 gives a third figure for the same idea ("116 sets … supplying …
**69 of the 94** catalogue entries"), and §G.4 a fourth ("**54 stars** hold further public blocks
this survey did not take").

**C65 — MINOR. §4.3: "Every spectral window … capped at 8 per target to bound compute cost; the cap
bound one target/band, 61 Vir Band 7".** The CSV has up to **100** windows for one star/band
(Proxima Cen B6) and 20 for 61 Vir B7 (5 blocks). §3 states a different cap ("at most **25 blocks**
per target"). If the cap is on blocks per target/band, say so; as written it is contradicted by the
release.

**C66 — MINOR. §5.3.2's pseudo-star result is reported as a null at p = 0.01.**
> "Out of sample the pseudo-stars are displaced as far as the real ones, median 0.443 against 0.429
> (p = 0.003); **within the survey they are not (0.463, p = 0.01)**."

p = 0.01 is not a null result. Either the sign of the comparison or the wording is wrong.

**C67 — MINOR. Calibration-sample denominators.** 1322 (§5.3.1, Table 12), 1326 (§G.3.3, "all 1326
calibration windows"), 599 ("calibration windows carrying no attributed line", also Fig. 14), 578
("the remaining 578 windows" / "at 578 null windows"), 1614 ("all 1614 windows", "404 blocks and
1614 windows"), 1616 (distinct datasets), 1655 (survey). At least three of these are undefined at
their point of use.

**C68 — MINOR. §G.3.3: "Propagated over the survey's 1655 windows, the pseudo-star rate predicts 4.7
unattributed stage-1 outliers … against 3.23 predicted under exchangeability and one observed."**
Four are observed (C8). The same "and has one" appears in §5.3.6.

**C69 — MINOR. §G.3.3: "Counts are those at this build date (2026 September 13, 07:44 UTC)"** — the
manuscript is dated 2026 September 20 and Table 12 is headed "as searched at 2026 September 17".

**C70 — MINOR. §5.3.2 / HD 207129's disposition is stated two ways in three sentences.** It "gains
the flag", its "crossing lies −150 km s⁻¹ from CO(2→1) in the stellar frame, **the same disposition
the paper reaches for the other disc hosts**" (i.e. CO) — yet −150 km s⁻¹ is outside the paper's own
±50 km s⁻¹ attribution rule, and the following sentence's arithmetic ("**8** attributed … and **2**
unattributed") only closes if HD 207129 is counted as **unattributed**.

**C71 — MINOR. Data Availability: "re-derives **26** of the paper's headline numbers".** Running the
shipped `reproduce_from_catalogue_v385.py` gives "**21 pass, 0 FAIL, 5 skipped** (macro absent —
retired or renamed)". Only 21 are actually re-derived; the claim should be 21, or the five retired
checks restored. Note that none of the quantities in C2, C3, C25, C26, C30 or C34 is among the 21,
which is why those errors survived the build gate.

**C72 — MINOR. Data Availability: "the disposition verbatim from Table 11".** The released
`disposition` column is empty in **1645 of 1655** rows, including all three rows Table 11
dispositions as "unattributed" (61 Vir, HD 14055, HD 23484). Only 10 rows carry a string.

**C73 — MINOR. Data Availability: "reproduces all 65 products byte for byte"** (`\NRegenProducts`
= 65) while the release notes accompanying this build report 76 regenerated products. Low
confidence — the definitions may differ — but the two should be reconciled before submission.

---

## 7. Categories in which I found nothing wrong

Stated explicitly, as requested.

* **Block accounting.** 656 → 484 → 404 + 77 + 3, with 177 unprocessed repeats: closes exactly,
  in §3, §4.6, Fig. 3, Table 2 and §6.2. 77/484 = 15.9 % ✓.
* **Window accounting.** 1725 extracted − 45 duplicates − 13 defective − 12 withheld = 1655 ✓;
  403 + 1252 = 1655 ✓; 1252/1655 = 76 % ✓; 1655 rows / 1616 distinct datasets ✓ (CSV).
* **Band histogram.** 112/4/4/1072/427/24/4/8 = 1655, and every entry matches the CSV ✓.
  Table 17's EB column (27/1/1/265/102/6/1/1 = 404) and system column (8/1/1/59/36/3/1/1) match
  the CSV exactly, as do all eight median EIRP values ✓.
* **Table 18** is internally perfect: masked column sums to 4.811 GHz = the "All" row; every
  "Left" = Union − Masked; every "Lost %" checks; 4.811/118.13 = 4.1 % ✓.
* **Table 15** (4032 trials): every axis's trial counts sum to 4032 ✓; the sub-channel rows sum
  to 400 ✓; P₅₀/P₉₀ by drift third match the text ✓.
* **Table 7(b)**: 1944 + 1944 = 3888 ✓.
* **η_drift bookkeeping:** 403 − 13 + 38 = 428 ✓ against the CSV's 428 windows with η_drift ≥ 1,
  13 Class A below unity, 38 Class B above it, max 1.351 ✓.
* **Appendix A's nine smearing windows** reproduce the CSV exactly, star by star, including the
  five 15.3-kHz Band 6 windows and the ×4.6 worst-case compounding ✓.
* **P₉₀ per window and per system**: 6.3×10¹³ / 2.4×10¹⁵ / 1.1×10¹⁷ and 6.3×10¹³ / 1.3×10¹⁵ /
  2.0×10¹⁶ all reproduce from the CSV ✓, as does Fig. 6's "20 systems within a decade of the
  deepest" and "33 of 87 … 62 per cent" ✓.
* **Selection percentages**: 85/94 = 90 %, 21/5908 = 0.4 %, 54/87 = 62 %, 70/87 = 80 %,
  (1072+427)/1655 = 91 %, 1054/1655 = 64 %, 13.3/118.1 = 11.2 %, 178→10.8 % (internally),
  0.46/50 = 0.9 %, 9/403 = 2.2 % — all check ✓.
* **Fig. 2, Fig. 4, Fig. 5, Fig. 7, Fig. 9, Fig. 10, Fig. 11, Fig. 12, Fig. 14**: text extracted
  from each PDF agrees with its caption (counts, legends, annotations, the ×2.81 trigger factor,
  the 9 red-ringed smearing windows, the 25/69 Class B/A split, 2835 GHz = 24.0 × 118.1) ✓.
  The only figure whose printed content contradicts its caption is Fig. 13 (C32).
* **Cross-references**: all resolve; the only conceptual mis-target I found is C41 (duplicate label).
* **Commit/date chain** in §5.3.1 (statistic 09-09, criteria 09-11, hold-out rule 09-14 = "5 days
  after the statistic", first reserved block 09-17 = "3 days after that") is self-consistent ✓.

---

## 8. What I would ask for before round 2

1. A single authoritative statement of **which statistic is primary** (C7) and one **chance
   expectation** carried through the abstract, §4.6, §5.3, §6 and the conclusions (C10).
2. Resolution of the **CP−72 2713 visibility contradiction** (C5) — this one can change a
   disposition.
3. A pass over the **stale macros** whose values predate the completed sweep: `NPolEB`,
   `NPolBoth`, `NEbBothHands` (104), `NCrossWin` (20), `NNonBP` (416), `ExpNonBP` (3.13),
   `RmBFlag`/`RmBNew`, `ConcThreeWin`/`ConcThreePct`, and the hard-typed 5.9 kHz s⁻¹, 41 per
   cent, "four windows", "four execution blocks", "seven windows against four".
4. Extension of `reproduce_from_catalogue_v385.py` to assert the quantities that failed here:
   the crossing class split, the on-source median, the Class A P_eff range, the window
   concentration, and P₉₀ = 1.2289 × P_eff on min/median/max (C71).
