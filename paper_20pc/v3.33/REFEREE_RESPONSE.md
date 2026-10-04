# Response to the referees

Manuscript: *A Search for Time-Variable and Frequency-Drifting Narrowband Technosignatures toward
ALMA-Observed Stars within 40 pc of the Sun: Survey Design and First Results*
White & Dey — revision v3.28

We thank both referees. The two reports agree on the central problem — the manuscript reported a
40 pc sample in its title and a ≤20 pc sample in its results — and we have fixed that first, because
almost everything else followed from it. **The whole paper is now the 40 pc dataset.** Every survey
number has been recomputed from a single frozen export by one script,
`survey_stats.py`, which is released with the paper; the figures are generated from that same export
by `make_figures_v328.py`. Text, tables and figures can no longer drift apart.

Recomputing at 40 pc changed the science, and we flag that prominently:

* the sample is **85 stars / 79 independent systems / 104 star-band datasets / 417 windows**;
* the search now flags **four** windows, not three. Two are the known β Pic CO lines; one is
  **HD 48370**, whose CO(2−1) emission is independently reported by Cataldi et al. (2023) and
  attributed there to foreground cloud contamination — an external corroboration of the pipeline
  we did not have before; and one is **CP−72 2713**, a new marginal crossing;
* **AU Mic is no longer flagged at all**, which changes how §5.5 reads (see R2/2 below);
* the occurrence limits are stronger, and their hierarchy has been inverted so that the
  completeness-aware number leads.

A note on two requests we could not fully meet, stated plainly rather than glossed: we cannot
re-run the observatory pipeline from this environment, so the holography-beam recomputation
(R1/22) has been resolved by **withholding** the affected data rather than by recomputing it, and
the integration-time audit (R1 essential list) still covers the subset on which it was executed,
which is now said at the point of use. Both are marked below.

---

# Referee 1

**1–3. Nominal thresholds must not read as 95 % detection limits; replace "sensitivity limit"
with "nominal detection threshold".**
Done throughout. The term *nominal detection threshold* is now standard, is defined once in the
boxed reading rule in §4, and is entered in a new nomenclature table (Table 3) together with
*completeness*. The abstract states the measured recovery (42 %) immediately after the thresholds.
Figure captions carrying EIRP values now say so in the caption itself rather than relying on the
reader having absorbed §4.

**4. Expand the completeness experiment, or downgrade the frequency-integrated occurrence
constraint.**
We take the second option, explicitly. The occurrence constraint is now defined on the **56 systems
that have injection-calibrated fine-channel coverage**, and the paper says in terms that the
coarse-channel-only systems contribute nothing because their searched class has no measured
recovery. Extending the campaign across band, channel width, integration time, antenna count,
baseline distribution, rms, primary-beam position and drift-grid density is now the fourth item in
a new §6.3, *Priorities for the next release*, with the axes named as the referee lists them.

**5. Hierarchy of the 6.9 %, ~16 %, 45 % numbers.**
Restructured exactly as recommended, and the numbers themselves have changed with the rescope. The
completeness-aware result now leads, in the abstract and in §6.1: **f₉₅ < 6.5 % at EIRP ≥ 10¹⁶ W
(56 injection-calibrated systems)**, with 3.8 % (unit recovery) and 9.0 % (uniform 42 %) given
afterwards and labelled *bracketing calculations*. A new sentence, "Which number is the result",
states that the measured form is the observational result because it is the only one in which
recovery was measured rather than assumed. Table 12 marks the measured column *(result)* in the
header.

**6. F_i = 1 is a conditioning statement and should be said so.**
Added, close to the referee's own wording, as a lead-in to the evaluation:
"We do not infer the prevalence of transmitters over ALMA's frequency range: we infer the
prevalence conditional on the transmitter's frequency lying inside the particular set of archival
spectral windows available for each system, and on it emitting throughout the archival epochs
observed. A reader who wants an unconditional prevalence must multiply by their own priors on
transmitter frequency and duty cycle, and those priors, not our data, will dominate the answer."
The requested frequency-coverage figure is the new Figure 5 (next point).

**7. Frequency × target coverage diagram.**
Added as **Figure 5**, built exactly as specified: frequency on the horizontal axis, one row per
independent system ordered by distance, each searched window a horizontal segment, colour encoding
the EIRP threshold, with a panel above counting systems per gigahertz. It answers the referee's
question directly: the 92.4 GHz union is **34 disjoint islands of median width 1.8 GHz**, clustered
near 230 and 345 GHz, with summed window bandwidth **7.6× the union** — repeated narrow islands, not
broad coverage. It replaces the old two-panel frequency-coverage figure, and the occurrence
section now points at it when stating what the limits are conditioned on.

**8. Do not describe the sample as population-representative.**
Corrected. The phrase is now "a bycatch census of the **ALMA-observed subset** of the local stellar
population within a fixed volume, which is not the same thing as a census of that population."

**9. Show the exchangeability tests quantitatively in the main text.**
Moved from the appendix into §5.4 with a new figure (Figure 8, `control_diagnostics.pdf`) and a
quantitative paragraph: median per-window control maximum by band (4.46, 4.59, 4.42, 4.52, 4.63,
4.69 in B3–B8), by resolution class, and against achieved rms and on-source time, plus a KS test of
the per-window rank of the star among its own controls against U(0,1).
**We report a real departure rather than smoothing it:** the fine-channel stratum fails that test at
p = 0.018 and contains four windows whose on-star peak beats its own control maximum against 0.22
expected. Those four are precisely the four flagged windows, so the excess is astrophysical signal
concentrated where narrow lines are detectable — but it is a genuine stratum-level departure and
readers are told to treat fine-window rank probabilities as slightly optimistic.
Two of the referee's requested panels — stratification on control radial position and on
primary-beam gain — **cannot be made**: the retained products store no per-control position or beam
gain. We say so in the text and in the caption rather than substituting something else silently.

**10. Distinguish the rank resolution from the false-positive probability.**
Both quantities are now separate entries in the nomenclature table — `p_rank,min = 1/(N_ctrl+1)`
described as the *rank resolution* of the ensemble, and `P(false flag)` as the survey false-positive
probability after thresholding, correlation and non-Gaussianity — and the prose that previously
slipped between them has been corrected, including in the new CP−72 2713 disposition, where p =
1/513 is described as "the smallest value 512 controls can express and not a measurement of
significance".

**11. Re-run the symmetric statistic on every window.**
This one rested on an ambiguity in our own writing, and we have fixed the writing. The **operative
criterion — the symmetric single-position statistic — is applied to all 417 windows**, and always
was; the frozen products support it. What was limited to seven windows is a *richer* variant that
additionally applies the region maximisation at the controls as well, which does require raw-
visibility reprocessing. The old text called that variant "the designed principal test", which
invited exactly the referee's reading. It is now described as a validation of the operative
criterion, and §5.4 states plainly that the criterion behind every number in the paper is applied
uniformly to the whole sample.

**12. More controls for candidate significance.**
Adopted as a stated plan, with the referee's two-stage structure: 512 controls routinely, then
10⁴–10⁵ local null evaluations for any window that passes. It appears twice — as the third item of
§6.3, and as part of the pre-committed promotion rule in §5.4 (see R2/5).

**13. Separate "vetoed search space" from "false positives".**
Reworded as requested: "a signal coincident with a molecular line is not thereby *false*, it is
**excluded from the technosignature search domain** because the astrophysical prior there is
overwhelming and this pipeline cannot separate the two." The point that masked frequencies are not
searched at all, so the survey makes no statement about deliberately line-adjacent transmitters, is
now also item (v) of the new limitations box.

**14. Expand the molecular species list, or query a comprehensive database for every crossing.**
We take the second, preferred option for the case where it matters. The eight-species mask is now
described as a contamination cut rather than a completeness claim, and the one flagged window with
no attribution, CP−72 2713, was re-queried against a wider catalogue of common mm/submm
transitions: the nearest is H¹³CN(4→3) at **−195 km s⁻¹**, still far outside any circumstellar
tolerance. That result is in the text.

**15. Physical presentation of the drift ceiling.**
`drift_acceleration.pdf` has been rebuilt as the figure the referee describes: maximum
line-of-sight acceleration versus orbital semi-major axis, one curve per host mass 0.1, 0.5, 1.0
and 2.0 M⊙, the adopted ceiling |a| = 3.60 m s⁻² drawn as a horizontal line with the unsearched
region shaded, and TRAPPIST-1 b and Proxima Cen b marked. The ceiling was measured from the export
rather than asserted (median 12.00 Hz s⁻¹ GHz⁻¹). It shows immediately that a 1 M⊙ host excludes
a < 0.041 au (P < 3.0 d).

**16. Constant linear drift is only first order; quantify where it fails.**
Added, using the referee's own criterion. Curvature matters when ½ν̈T² exceeds half a native
channel, which for a circular orbit of period P becomes P ≲ 2π(ν/c) a_max T² / Δν_ch — about
**1.6 d** for a typical fine-channel window and about an hour for a coarse one. TRAPPIST-1 b, at
1.51 d, sits just inside that boundary and is also the case that exceeds the drift ceiling. This is
in §6.3, i.e. in the limitations discussion rather than in an appendix.

**17. Move duty cycle next to the headline occurrence result.**
Done at three levels. The abstract now ends with the duty-cycle dependence. Table 13 gives f₉₅ at
D = 1, 0.5, 0.1 and 0.01 for both the thresholded and the measured forms. And a new **Figure 12**
plots the occurrence limit against EIRP with four curves — measured and unit recovery, each at
D = 1 and D = 0.5 — with the region where no bound exists shaded. The text states that since an
intermittent transmitter is at least as plausible a priori as a continuous one, the D = 1 numbers
should never be quoted without this dependence attached.

**18. Standardise terminology; the 1 Hz extrapolation.**
Terminology standardised as the referee sets it out. On the extrapolation we take the **removal**
option: the projection of what ALMA "would reach at 1 Hz" has been deleted, along with its figure,
and replaced by an explicit statement that a √Δν scaling across six orders of magnitude in spectral
resolution is a thought experiment rather than an achievable sensitivity, and that quoting it
invites the misreading the paper is trying to avoid.

**19. Caution on the Arecibo comparison.**
The benchmark is retained as a power scale only. The claim that targets "reach Arecibo levels" has
been removed, and the EIRP figure caption now carries the qualification directly: "it is an S-band
radar, and a device radiating the same EIRP at 100–300 GHz would be a different engineering system
entirely, so this is not a statement that the survey reaches Earth-technology detectability."

**20–21. A QA figure for heterogeneous calibration, and statistical justification of the 100×
noise-defect cut.**
Both addressed by the new **Figure 7** (`noise_qa.pdf`): σ√(t_on Δν_ch) for every extracted window,
by band, with the sample median, the median/100 threshold and the six excluded windows marked. The
figure makes the referee's point better than the prose did — the six defective windows sit **3.2
decades** below the lowest retained window with a completely empty gap between, so *any* threshold
between 1.5 × 10¹ and 2.2 × 10⁴ selects exactly the same six. The criterion is demonstrably not
fine-tuned.

**22. Primary-beam correction: use the best available beam model before publication.**
We cannot run the holography recomputation from the analysis environment used for this revision, so
we have taken the referee's underlying point — that provisional values should not be published — and
resolved it by **withholding the data instead**. The four ε Eri Band 6 windows, which sit at ~0.7
primary-beam FWHM where the Gaussian beam form is not valid (correction 2.9–3.4×), are withheld
from the release and are excluded from every number in the paper; this is now recorded alongside the
noise-defect exclusion. Sirius B is retained, because its correction is ≤ 16 % and is a bounded
systematic rather than an invalid model, and it is described that way rather than as "provisional".

**23. State where in the reduction chain the statistic is formed; add an algorithm box.**
Added as **Table 2**, in the referee's numbered form, in a new §4.4. The text states explicitly that
the statistic is formed on extracted spectra, not on images or visibilities, and that steps 1–8 are
executed identically at the stellar position and at all 512 controls.

**24. Give the search statistic an explicit mathematical definition.**
Added as Eq. 1: T(x) = max over drift and frequency of S(x,ν,ν̇)/σ(x), with σ specified — a single
robust scale per position and window, 1.4826 × the median absolute deviation of that position's
median-subtracted spectrum over all channels, local in position, global in frequency, and not a
Gaussian fit. T★ ≡ T(x★) is now used consistently.

**25. Quantify N_eff for the correlated controls.**
Retained and made explicit that N_eff ≃ 30–43 is measured from the symmetric reprocessing runs, with
a statement of what it does and does not change: it does not affect the rank test, which is
conditional on the realised ensemble, but it does mean "512 controls" must not be read as 512
independent noise realisations.

**26. Simplify candidate nomenclature.**
Adopted, in the referee's three-tier form: **hit** → **spatially significant hit** → **candidate**,
defined in Table 3 and used consistently. The consequence is exactly what the referee anticipated:
the paper now says "four windows contain a spatially significant hit; none survives vetting, so this
release reports **zero candidates**", which cannot generate a headline about candidates being found.

**27. The continuum analysis dilutes the paper.**
Partially adopted. The continuum anomaly screen, continuum photometry and line catalogue were moved
to online-only supplementary material in the previous version and remain there; the main text
carries a short paragraph each. We have not removed them from the paper, on the lead author's
instruction, but the main text now states explicitly that the continuum lane is exploratory, that
its counts refer to a subset of the sample, and that no disposition in the paper rests on it.

**28. Closure phase has no discriminating power; present it as proof of principle.**
Adopted in full, and in the main text where the vetting cascade is introduced, not only in the
appendix: "at this survey's flux densities it has **no discriminating power** … no flagged window
could have failed the test whatever its true nature. We therefore report it as a proof-of-principle
diagnostic for future, deeper releases and not as an operative filter here, **and we do not describe
any window as having 'survived' it**."

**29. Compress the AU Mic discussion.** / **R2/2 asks for it to be expanded and made more
transparent.**
These pull in opposite directions and we have tried to satisfy both: the section is **shorter** than
before, and simultaneously more rigorous. See R2/2 below for the substance.

**30. Remove manuscript-version history from the scientific narrative.**
Done. The "Scope of this version" section is deleted, the version slug that printed on page 1 is
gone, and phrases of the form "earlier versions used…" are replaced by the construction the referee
suggests: "An initial implementation … Tests showed this to be biased because … We therefore
adopt …". Version history now lives only in the repository changelog and the Data Availability
statement.

**31. Title and running headers.**
Fixed; the running header now reads "An ALMA Archival Technosignature Search within 40 pc" and the
20 pc/40 pc distinction has disappeared from the paper, since there is now one dataset.

**32. The abstract is too dense.**
Rewritten to the referee's four components, roughly 25 % shorter, opening with the method and the
sample and carrying one plain declarative sentence — "We find no evidence for a technosignature in
any of the data searched" — before any processing statistics. The explanation of the earlier
asymmetric statistic is gone from the abstract entirely.

**33. Sharpen the unique scientific question.**
The framing the referee proposes — *what constraints on powerful high-frequency narrowband
transmitters already exist implicitly in the ALMA archive?* — is now the organising question, with
the novelty stated as turning archival interferometric data into a reproducible experiment with
controlled false-positive and completeness statistics.

**34. Do not overstate "firsts".**
Audited; "to our knowledge" is now attached consistently, and the occurrence numbers are described
as "to our knowledge, the first ALMA-side numbers of their kind" rather than as bare firsts.

**35. One authoritative survey table at the start of Results.**
Added as **Table 4**, at the head of §5, in the referee's format and with the caption stating that
every count in the paper reconciles with it and that any number referring to a subset says so at the
point of use.

**36. Distinguish stars from independent systems.**
Enforced. Observational results are quoted per star or per star/band; occurrence statistics use
**79 independent systems** as the denominator throughout, with the six bound pairs that share a
pointing collapsed. The rule and the pair list are stated where the denominator is introduced.

**37. Survey-selection flow diagram.**
`selection.pdf` rebuilt with the referee's ten stages, from the 168-star census through ALMA
coverage, processing, star-band datasets, extracted windows, QA, hits, spatially significant hits
and line-mask survivors to zero credible technosignatures. The counts are cross-checked against
`survey_stats.json` at generation time and the script aborts if they disagree.

**38. One correlation-aware null model.**
The exchangeable-rate model is now the single primary survey-level model, presented with the
execution-block correlation stated as its known limitation; the historical four-model bookkeeping
ladder is retired to an appendix that records only what replaced it. We also corrected a genuine
internal inconsistency the referee's point exposed: the main text had described "the
block-permutation model" as the operative estimate while the appendix retired that ladder. It now
names what is actually used.

**39. Bayesian upper bound as a cross-check.**
Computed and reported: with a uniform prior on f, p(f|data) ∝ Π(1 − f C_i) gives a 95 % credible
upper bound of **6.4 %** against the frequentist **6.5 %** for the same completeness model —
agreement to better than the last quoted digit, so nothing turns on the frequentist construction.

**40. Confidence intervals on the recovery fractions.**
Added. `completeness.pdf` now carries binomial 68 % and 95 % Wilson intervals on every point, and
the threshold-level recovery is quoted as **42⁺¹⁶₋₁₄ %** in the abstract and wherever it is used.
The denominator is stated on the figure (n = 24 per amplitude for the fine drifting class, which is
the unique value consistent with the campaign design and with all five reported percentages).

**41. Extend injection amplitudes beyond 10σ.**
Accepted as a stated deficiency and a committed action: the paper says EIRP₉₀ has **not** been
located, that the quoted EIRP₉₀ > 2 EIRP₅σ is a bound rather than a measurement, and §6.3 commits to
pushing the campaign to 15, 20 and 30σ until the curve asymptotes, noting the referee's point that
failure to approach unity would itself identify a further selection effect.

**42. The sub-channel placement dependence deserves mitigation, not averaging.**
The channel-phase dependence is retained as a resolved result rather than only folded into a pooled
curve, and the mitigations the referee lists — half-channel-offset regridding, overlapping
channelisation, passband-aware interpolation, searching multiple frequency offsets — are named in
§6.3 as low-cost sensitivity gains.

**43. Preserve phase-steady emitters — the largest scientific opportunity.**
Accepted as the referee frames it, and promoted to the **first** item of §6.3 and to item (i) of the
new limitations box. The text states that this is not a completeness correction but a whole signal
class the pipeline cannot see, and that an interferometer does not need median subtraction to reject
terrestrial interference — sky localisation, baseline-dependent phase, delay and fringe-rate
signatures and multi-block consistency can do it without touching the time dependence. The abstract
now says in its third sentence that a stable beacon is outside the class this pipeline can
constrain.

**44. Exploit the interferometry more aggressively.**
Added as the second item of §6.3, with the visibility model written out and the likelihood-ratio
comparison between a celestial point source at the star, a common-mode terrestrial interferer and
image-plane noise identified as the distinctive methodological opportunity of ALMA SETI.

**45–46. Make the data release operative at submission; provide one machine-readable master table.**
The per-window master table ships with this revision as `per_target_results_v3.28.csv`, one row per
searched window, and `survey_stats.py` regenerates every survey number in the paper from the frozen
export. We flag one item for the editor: **the repository carries no tags at all**, although the
Data Availability section refers to a tagged snapshot; the authors need to cut that tag and mint the
Zenodo DOI before acceptance, which we agree should precede publication rather than follow it.

**47. A "What this survey does not constrain" box.**
Added verbatim in spirit, as a ruled box immediately before the Conclusions, with seven numbered
items covering phase-steady carriers, frequencies outside the searched windows, epochs outside the
archival coverage, drift rates above the ceiling, the molecular mask, emission broader than one
channel, and the completeness-dependent threshold.

**48. Recast the Conclusions.**
Shortened and reorganised around the seven findings the referee lists, in that order, ending on the
conditional and still-weak nature of the occurrence constraint and on the pipeline change that would
enlarge the searched signal space.

---

# Referee 2

**Major 1. Scope inconsistency between title, abstract and results.**
Fixed by completing the rescope, which is option (a). The results section, every table and every
figure now report the 40 pc dataset: 168-star census, 85 stars searched, 79 independent systems,
104 star-band datasets, 417 windows, 1.30–38.83 pc. The "SCOPE OF THIS VERSION" changelog section is
deleted. Nothing in the paper now mixes the two volumes; where a subsidiary analysis (continuum
lane, injection campaign, integration audit) covers a subset, that is stated in the sentence that
reports it.

**Major 2. The AU Mic reclassification and the timing of the criterion change.**
This is the point we have worked hardest on, and the rescope has changed the situation in a way that
helps: **under the 40 pc recomputation AU Mic is not among the flagged windows at all**, and the
section is now framed as a methodological result rather than a defence of one object. The referee
asked for three things.

*(i) State the sequence explicitly.* Done, in the opening of §5.5, in the impersonal form Referee 1
asked for: an initial implementation used a region-maximum statistic, a crossing towards AU Mic was
identified under it, and we then set out the evidence — because "a criterion revised after
inspecting the object it must judge is a criterion a reader is entitled to distrust".

*(ii) Demonstrate the new criterion does not suppress real signals.* We can now do this
quantitatively rather than by assertion, and it is the strongest single addition to the paper.
Across the 417 windows, **the set flagged by the symmetric criterion is a strict subset of the set
flagged by the region-max criterion**: seven windows were flagged before, four are flagged now, and
the three that dropped out — towards ALMA J1537−3319, AU Mic and HD 14055 — have in common that
**the stellar position itself never exceeded its own control ring** (star statistics 5.09, 5.22, 5.22
against ring maxima 5.63, 5.85, 5.74). The symmetric criterion removed no window in which the star
dominated its controls, which is the only configuration a localised transmitter can produce. It is a
bias correction, not a power reduction, and it did not single out AU Mic: it removed three windows
of the same class, of which AU Mic is one.
The defect is also demonstrable without reference to any target: under an exchangeable null the
maximum of n_src = 135 positions beats the maximum of 512 single positions with probability 20.9 %,
and the measured region-max rate over the release is 15.3 %, against 0.19 % for a symmetric test.

*(iii) Promote it out of an appendix.* It is a signposted main-text subsection, §5.5, retitled
"Changing the detection statistic, and the AU Mic crossing".

**Major 3. Representativeness of the completeness calibration.**
Both remedies the referee offers are now in place. The occurrence limit is restricted to the 56
systems that actually have injection-calibrated coverage; uncertainties are propagated, with
recovery quoted as 42⁺¹⁶₋₁₄ % (binomial); and the scope limitation is stated in the abstract and in
the main text rather than only in the appendix. Broadening the campaign to one configuration per
band, including Bands 4, 5 and 8, is committed in §6.3.

**Major 4. Closure-phase vetting has no discriminating power.**
Agreed and adopted; see Referee 1/28. The word "survived" has been removed in this context
throughout, and the zero-power statement now appears where the vetting cascade is first introduced.

**Major 5. Look-elsewhere effect across the planned sequence of releases.**
Addressed with a pre-committed global rule rather than an acknowledgement. The text now states that
each release of N windows contributes ~N/513 chance flags, so a programme reaching the full
~2000-window census expects ~4, and that reporting one unattributed marginal crossing per release is
the expected outcome rather than an accumulating anomaly. We then pre-commit: **no crossing will be
advanced as a candidate on rank statistics alone at any point in this programme**; promotion
requires recurrence at an independent epoch, or a control ensemble enlarged for that window until
the rank probability can resolve a survey-wide significance (≳10⁴ positions for a Bonferroni
threshold over the completed census).

**Major 6. The occurrence limits presuppose continuous emission; foreground it.**
Done, including the requested one-sentence caveat in the abstract itself: "All limits assume
continuous emission: at duty cycle 0.5 the primary bound weakens to 13 per cent, and by 0.1 it is
65 per cent and effectively vacuous." See also Referee 1/17 for the new figure and table.

**Major 7. Readability and bespoke terminology.**
(i) The abstract has been rewritten as described. (ii) The version-scope statements are deleted and
the glossary and process material sit in the online-only supplement. (iii) The manuscript has had a
dedicated de-densification pass: nested parentheticals unpacked, repeated caveats replaced by
cross-references to a single statement, and the paper trimmed back to its previous page count even
after the substantial additions above.

**Major 8. Internal inconsistency in star counts in §3.**
Fixed at the root: the "120 stars" residue is gone and §3 now uses 168 census stars and 85 searched
stars consistently, as does the selection-function table. This was, as the referee diagnosed, a
symptom of Major 1 and disappeared with the rescope.

## Minor points

1. **Table 5 overflowing the margin.** The survey-state table has been rebuilt from scratch as the
   new Table 4 and verified against the typeset output; no overfull box is reported for it.
2. **Competing interests.** Rewritten to state the implication, not only the fact: VBRL has no
   financial or intellectual stake in ALMA archival SETI work, provided no funding, and had no role
   in the study, and on that basis the authors declare no competing interest. *Flagged for the
   authors to confirm before submission.*
3. **Self-citation of an unreviewed companion paper.** We agree an identifier is required. The
   authors must supply the arXiv number for White (2026); this is marked in the source and flagged
   to the editor.
4. **Drift-ceiling caveat surfaced earlier.** It is now in §4, in the abstract-adjacent limitations
   box, and in §6.3 with the quantitative orbital boundary, not only in the appendix.
5. **A plain declarative sentence near the top of the abstract.** Added as the second sentence.
6. **Figure 1 caption.** The panel (a)/(b) distinction — spectral power versus total power, and why
   the like-for-like comparison is panel (a) — is now stated in the caption itself.
7. **Reminder of the candidate vocabulary at the start of §5.4.** Superseded by the nomenclature
   table (Table 3) and the simplified three-tier naming, which is referenced at that point.
8. **Polarisation.** Raised from a passing mention to a named priority in §6.3, on the referee's
   grounds that a polarised carrier is a physically motivated discriminator against weakly polarised
   astrophysical backgrounds.
9. **Reference disambiguation.** Sheikh et al. 2025a/b and Czech et al. 2021/2026 checked for
   unambiguous in-text keying.
10. **Hyphenation and units.** A single style pass across the manuscript and appendices.

---

## Changes we made that neither referee asked for

* **A new astrophysical attribution.** The rescope produced a flagged window towards HD 48370 whose
  CO(2−1) emission turns out to be independently reported by Cataldi et al. (2023) and attributed
  there to foreground cloud contamination. We had not previously cited that work; the pipeline
  recovered the feature blind.
* **A limitation of the spatial test, found while dispositioning that window.** HD 48370 beats its
  control ring by 1 % of the statistic (27.10 against 26.83), which is what beam-filling emission
  looks like. The paper now states that the star-versus-control test discriminates only weakly
  against emission that fills the primary beam.
* **Two defects in our own previous release, fixed.** The figure shipped as `completeness.pdf` in
  v3.27 did not match its caption; and the pipeline schematic embedded Type 3 bitmap fonts, which
  breaks text extraction from the PDF. Both are corrected.
