# Response to referees A and B on v3.45

Prepared with v3.46. Every claim below that says "verified" was checked against
the retained pipeline products, the frozen release, the processing log or the
released repository during this cycle, and the check is named. Where we could
not verify something, we say so instead of asserting it.

Two results arrived after both reports were written and are folded in: an
archive-metadata audit of every processing failure, and a set of further
archival execution blocks searched with the unmodified pipeline.

---

## A. Things we found wrong in our own manuscript while answering you

Stated first, because they matter more than the replies.

1. **The recurrence paragraph named the wrong window.** A first draft of the new
   positive-control paragraph said that both β Pic windows attributed to
   circumstellar CO had been re-searched. The Band 6 window actually re-searched
   is 230.528134 GHz in MOUS `uid://A002/X5a9a13/X58b`, which crosses threshold
   but is **not** a stage-1 outlier; the Band 6 row of Table 5 is 230.516128 GHz
   in `uid://A001/X133d/Xbb5` at T\* = 11.68, and the archive holds no second
   block of it. The text contradicted our own table. Both windows are now named
   and distinguished.
2. **A frequency agreement was computed against a rounded printed value.** The
   β Pic Band 3 agreement was quoted as 0.13 MHz (0.34 km/s), obtained by
   differencing against the table's rounded 115.2605 GHz instead of the
   full-precision product column. The products give 0.27 MHz. The comparison is
   now made properly, and reported after removing each block's own tuning.
3. **The Conclusions still asserted a classification the Results had already
   withdrawn** ("retired as a noise excursion"). Corrected, per A12.

---

## Referee A

**A2, A3, A15 — selection accounting.** Accepted; it was an error. Table 4's
first row said "Census stars within 40 pc = 168", which is the number with
qualifying ALMA coverage, not the reference census. The chain is now stated in
full: **17,566 Gaia DR3 stars within 40 pc → 168 with qualifying public archival
coverage → 88 searched to completion here → 81 independent systems.**

*Verified, and it improves the paper.* An audit of every processing failure
re-derived the pointing of each candidate unit from obscore. **53 of the 168
never had the star in any beam in any band.** All 54 distinct never-pointed
stars were matched to census entries by designation; exactly one of them,
Wolf 28, also reaches the searched 88 through a different band. The honest
denominator for the searched fraction is therefore **88 of about 115**, not
88 of 168, and the paper now says so.

**A new selection-function figure (A15)** we have not added, for length; the
selection function is tabulated in Table 8 against the reference census and the
searched-fraction-versus-distance information is in its distance panel.

**A4 — the 93.1 GHz union.** Accepted and applied wherever the figure appears.
*Verified:* summing window bandwidth over the 431 retained windows gives
**717 GHz** against a 93.1 GHz union, which is your number and the paper's own
factor of 7.7.

**A5 — Class A / Class B.** Accepted; your sentence is used, and the split is in
the abstract.

**A6 — the Hanning response.** Accepted and foregrounded, with nominal and
sub-channel thresholds reported together and the abstract carrying the factor.

**A7 — "5σ".** Accepted; "nominal 5σ trigger power" is used consistently and the
trigger/completeness distinction is stated in the boxed rule.

**A8, A9 — more injections.** *Declined for this version, and we say why rather
than implying it was done.* The dwell campaign already spans 12 windows,
11 targets and three bands for the non-drifting class. Extending the
drifting-class campaign across bands, channelisations, array types and
off-axis positions is a substantial piece of work that would not change a null
result, and it is listed first in further work with the stratification you
propose. The completeness claim is restricted throughout to "the completeness
measured for the reference Class A configuration", with the 0.5–2× transfer
bracket carried into the abstract.

**A10 — exchangeability.** Accepted. The control ensemble is described as an
empirical null distribution conditional on approximate spatial exchangeability,
never as a direct local false-alarm probability, and the list of known
violations is kept.

**A11 — the rank floor.** Accepted. "Stage-1 statistical flag" is renamed
**stage-1 spatial outlier** throughout, the impossibility of survey-wide
significance from the first-stage test alone is stated prominently, and the
evidentiary bar beyond it is given. *Verified:* 1/513 = 1.95×10⁻³ against a
Bonferroni scale of 0.05/431 = 1.16×10⁻⁴; a 5σ-equivalent single-window rank
resolution would need **3.5×10⁶** control positions (your "about 3×10⁶").

**A12 — CP−72 2713.** Accepted, and you were right. The event fails the
pre-defined recurrence criterion and is retired as a candidate; the available
data cannot distinguish a statistical or instrumental excursion from a
non-repeating or intermittent event. Applied in the Results, the Conclusions and
the abstract.

**A13 — molecular masking.** Accepted as a reframing, without re-running the
survey: the detection stage is blind to astrophysical identity, the ±50 km/s
mask is classification plus robustness check, and masked channels are described
as searched but intrinsically ambiguous, since a deliberate transmitter could
sit on a transition.

**A14 — "there is nothing there".** Deleted. Replaced by the statement that no
signal satisfying the survey's statistical, spatial, recurrence and
astrophysical-vetting criteria was identified, with the list of what could still
be present retained.

**A16 — the M fraction.** The temperature panel reports the classified
population and the 36 stars without a Gaia temperature are stated rather than
normalised away.

**A17, A13 minor — Figure 1.** The caption now states that lower EIRP on this
figure does not imply greater sensitivity to a hertz-wide carrier, the two
panels are explicitly inseparable, and the native channel width is carried in
panel (b).

**A18 — Arecibo.** The 12 m, 1 MW, 230 GHz benchmark is the foregrounded
comparison; Arecibo remains only as a familiar power scale and is explicitly not
offered as a transmitter model at these frequencies.

**A19 — why linear drift.** The curvature boundary (P ≲ 1.6 d for a typical
Class A window) is in the main text rather than future work.

**A20 — visibility-domain localisation.** *Declined, with reasons.* It needs
visibility data that the frozen release does not contain. It is stated as the
highest-priority item of further work, with the four windows you name.

**Presentation and vocabulary.** The appendix carrying the development history
is now headed *Analysis audit trail*, and the main text opens the validation
section by saying that what follows is the final analysis and pointing there.
The nomenclature table has been shrunk. Two parts of this we have **not**
completed and will not claim: the statistic-revision narrative is still in the
main text rather than moved wholesale into that appendix, partly because
referee B asks for its audit table to be prominent; and the vocabulary
replacement is unfinished, with "lane" still in use.

---

## Referee B

**B1 — the statistic-revision timeline.** Accepted in full, and the answer is
the one you invited. *Verified against the released repository through the
GitHub API:* the AU Mic flag is first committed **2026-08-31T11:55:04Z**
(`8e00f90e8f8c`), stated in that version's abstract and in its machine-readable
aggregate, which we confirmed by fetching the file; the symmetric statistic
becomes operative **2026-09-09T16:14:07Z** (`0c465f2661bd`). **The redesign
postdates the flag by nine days.** The paper now says so plainly and rests the
case on the algebra, which owes nothing to these data. *On promoting the audit
table:* Table 7 is already in the main text, inside the statistic-revision
subsection, and has been since v3.45; no move was needed. An independent blind
re-derivation we have not done.

**B2 — the resolution floor.** Accepted; see A11.

**B3 — one configuration transferred.** Accepted as a restriction of the claim
and a declined request, as for A8: the wording is now "the completeness measured
for the reference Class A configuration", and the 0.5–2× bracket is in the
abstract beside the completeness-corrected figures.

**B4 — the coarse-noise defect.** This is now answered with measurements rather
than a gap argument. *Verified here:* all six windows are 12 m, three in Band 6
and three in Band 7, all at 15.6 MHz, spread over **five execution blocks in
four projects**, so they share an array and a correlator mode but not a
proposal. Every one of them has a finer-channelised window **in the same
execution block covering the same frequencies** that behaves normally, with q
larger by 2.9×10³ to 6.3×10³, which is the signature of an auxiliary window
riding on a science baseband. The position question is settled from the pipeline
source: σ is an `(n_int, n_chan)` array estimated from the control probes and
applied to every position alike, so the deflation is a property of the window.
And the correlation you ask for: predicting q for every retained window from its
band, array and antenna count, the **431 retained residuals are unimodal**, with
98.4 per cent inside half a decade of the median, an interquantile spread of a
factor 2.3, and no empty interval wider than 0.04 dex inside the distribution;
the six excluded windows sit **3.0 dex below the lowest retained one** with
nothing between. There is no continuum of smaller deflations under the cut.

**B5 — polarisation.** Accepted; the worst case is quantified in the abstract.
The manuscript already stated that the retained products cannot say which
datasets kept both hands through QA2, and that statement is kept.

**B6 — TRAPPIST-1 b.** Accepted as an abstract caveat. One correction: the
1.07 m s⁻² you quote is **TRAPPIST-1 d**. TRAPPIST-1 b is 4.00 m s⁻², against a
searched ceiling of 3.6–4.0 m s⁻², so it sits exactly at the ceiling rather than
near it, which is the sharper form of your point.

**B7 — abstract structure.** Restructured along the lines you propose, inside
the 1920-character arXiv limit (currently 1907).

**B8 — prose.** Accepted, and measured rather than asserted. The antithesis
family ("X, not Y" / "and not" / "rather than") falls from 57 occurrences to
23; em-dashes remain at zero; QA2, SEFD, MOUS and TDM are expanded at first use;
the terse aphoristic constructions in the statistic and results sections have
been expanded and the aphoristic paragraph closers removed.

**B9 — independent validation.** *Declined, with reasons*, as for A20: applying
the frozen pipeline to pointings outside the sample, or holding out 10 per cent
of windows from mask design, both need products the release does not carry. Both
are stated as high-priority further work with your design.

**B10 — a citable anchor for the CP−72 2713 criterion.** *Verified:* the paired
promote/retire wording, including "retire on a clean second epoch", is committed
**2026-09-11T11:33:40Z** (`119a68a6ab50`), and the second-epoch search began
2026-09-11T20:19:23Z, so the criterion predates the search by nine hours. We
note the honest limit of that: the programme-wide promotion criterion is
*contemporaneous* with the CP−72 2713 flag, entering the record in the same
commit, so what is established is criterion-before-search, not criterion-before-flag.

**Minor items.** QA2, SEFD, MOUS and TDM expanded at first use; σ stated to come
from control positions only, cross-referenced from Eq. 2; "coherent" clarified as
drift-track phase across integrations of an intensity series, not visibility
phase; the order-of-magnitude bandpass argument replaced by ALMA's quoted
bandpass accuracy; the 462/448/431/396 bookkeeping summarised in one main-text
sentence; KS p-values added to Figure 3; Figure 6 notes that Class B has no
drift-completeness curve; the significant-figures convention made consistent.
The VBRL affiliation wording and the White (2026) identifier are author actions
and remain marked in the source.

---

## New results the referees did not see

**1. Most "failures" are stars ALMA never observed.** Of 68 failed target/bands,
**60** have the star between 250″ and 8205″ from the nearest pointing (median
1.6°) and **8** have it inside the beam, with nothing in between. The 60 observe
the Sun, planets, moons and comets; ALMA's archive reports a field of view up to
63° of half-width for such deliveries, and the candidate crossmatch trusted it.
Proper motion cannot rescue them: the fastest mover in the set runs at
5.12″ yr⁻¹, so the smallest gap would take about 49 years to close. These are
catalogue-construction artefacts, not processing failures.

*Also settled, and reported as a negative result:* the hypothesis that the
per-target three-block limit caused failures by selecting blocks without
calibration products returns **0 of 68**. Fourteen failures have untried blocks
carrying such products, and in none of them did the blocks actually tried lack
them.

**2. The β Pic CO features recur: a matched positive control.** The observing
unit behind the Band 3 outlier holds further public blocks that the download
budget declined; two have since been searched unmodified. The CO(1→0) feature is
present in all three blocks at T\* = 14.65, 17.29 and 27.68, with 17, 24 and 24
channels above threshold and no control of the 512 above the star in any block.
A second Band 6 CO(2→1) window behaves the same way across two blocks. After
removing each block's own tuning the Band 3 peaks agree to exactly one channel
and the Band 6 peaks to three; in the barycentric frame the CO peaks of the four
blocks with a recorded epoch lie within 0.7 km s⁻¹ of β Pic's systemic velocity
across two transitions and nine years. Set against CP−72 2713, which does not
reappear at its own frequency and drift in a deeper block of the same tuning,
this converts the CP−72 null from a possible blind spot into a measurement.

**3. The retry programme.** Re-running the failed target/bands on the current
code produced **38 further failures in 39 attempts**; the single recovery lies
outside Bands 3–8 and outside this release. No claim of recoverable failures
survives in the paper.
