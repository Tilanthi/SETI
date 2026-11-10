# Response to three referee reports on v3.40 — revision v3.41

White & Dey, *An ALMA Archival Search for Spectral Technosignatures toward
Stars within 40 pc: Methodology and First Survey Release*

We thank all three referees. The reports are unusually specific and several of
them are numerically checkable against the data we released; we checked every
such claim against `frozen_export_v3.31.json`, `survey_stats_round10.json` and
`per_target_results_v3.32.csv` before acting, and we say below what we verified,
what we could not verify, and what we found that no referee raised.

**A standing convention in this letter.** Where a referee is right, we say so
and give the verification. Where we could not check a claim with the products in
hand, we say *"not verified"* and either state the limitation in the paper or
decline the change — we have not asserted a single fix we did not test. Three
referee recommendations we declined outright, and they are listed in §5.

**Summary of the revision.** 39 pages → **36**. Five verified production defects
fixed. One withdrawn verification (the Hanning check), one corrected population
description, one newly diagnosed catalogue defect, and one newly diagnosed
system-count defect — all three found during this round and all three disclosed
in the paper rather than silently repaired. Three duplicate figures deleted, two appendices deleted, two merged (17
appendices → 14). Build gates in §6.

---

## 1. The five defects the editor had already verified

### A1 — duplicated Background paragraph and orphaned citation pile (R1-m1/m2, R2-m1/m2, R3-M1)

**Verified and fixed.** The ~90-word block spliced after "divide into wide-field
commensal surveys and targeted programmes" has been deleted; §2 now reads
"…divide into wide-field commensal surveys and targeted programmes
`\citep{Zhang2020,…}`; machine-learning RFI rejection is now central…", i.e. the
citation pile is re-attached to the sentence it belongs to and the later,
correct occurrence of the passage is kept. §2 was then re-read as a whole and
compressed (R1 §4.1 item 2).

### A2 — hand-typed `402` where the generator says `416` (R1-M8, R3-M6a)

**Verified and fixed via macro.** 431 − 15 β Pic windows = 416 = `\NNonBP`; we
confirmed `416` directly from the frozen export. Both the main text and Appendix
N now use `\NNonBP`, and the associated expectation and Poisson tail are also
macro-sourced: `\ExpNonBP` = 416/513 = **0.81** (was 0.78, which corresponds to
402) and `P(≥1)` = **56 %** (was 54 %). Referee 1's arithmetic is exactly right.

Two further hand-typed numbers in the same accounting were wrong and are now
generated:

* `P(≥4 | 0.84)` was printed as **0.9 %**, which is P(*exactly* 4). We recompute
  P(exactly 4) = 0.896 %, P(≥4) = **1.07 %**. The text now carries
  `\PgeFourPct` = 1.1. R1-M8 is correct.
* "Gaussian-expected chance crossings **11.4**" in Table `tab:trials` and
  Appendix N. 4.597×10⁷ cells × 2.867×10⁻⁷ = **13.18**. Both places now use
  `\GaussCross`. R1-M8 is correct.

### A3 — gross bandwidth 700.8 GHz vs 716.7 GHz (R1-M8)

**Verified and fixed at the generator.** Summing |f_hi − f_lo| over the 431
retained windows gives **716.654 GHz**. The literal `GROSS_BW = 700.8` in
`round9_calc.py` has been replaced by a sum over the same frozen rows used for
everything else, and a new macro `\GrossBwGHz` (emitted by `round10_calc.py`) is
used in both the prose and Table `tab:exposure`. As Referee 1 notes, this also
moves `\MaskGrossPct` from 3.2 % to **3.1 %** (22.20/716.65 = 3.098 %), which is
now computed rather than typed.

### A4 — the β Pic B3 CO(1→0) offset

This is the one place where we depart from the editor's instruction, and we want
to be explicit about why, because the instruction was to "take the export value
as authoritative" and the evidence says the export value is the one that is
wrong.

**What we found.** The released `line_off` column gives −10.3563 MHz; Table 7
printed −10.36; the §5.3 text and Table 21 printed −10.56. Referee 2's
hypothesis — that the pipeline's line catalogue does not carry the laboratory
CO(1→0) rest frequency — is **verified, and we can now quantify it**.

A crossing lies on its window's channel grid. Snapping (laboratory rest
frequency + released offset) to that grid and subtracting the offset therefore
returns the catalogue entry the pipeline actually used, without reference to any
number printed in the manuscript. Over the fine (<1 MHz) windows this gives:

| transition | implied catalogue value (GHz) | laboratory (GHz) | difference |
|---|---|---|---|
| CO(1−0) | 115.271000 | 115.271202 | **−0.202 MHz** (−0.53 km s⁻¹) |
| CO(2−1) | 230.538000 | 230.538000 | 0.000 |
| CO(3−2) | 345.796000 | 345.795990 | +0.010 MHz |
| CO(4−3) | 461.041000 | 461.040768 | +0.232 MHz |
| SiO(5−4) | 217.105000 | 217.104980 | +0.020 MHz |
| ¹³CO(2−1) | 220.398680 | 220.398684 | −0.004 MHz |

The pattern is unambiguous: **the frozen mask stores rest frequencies rounded to
1 MHz**. That is a new finding, not raised by any referee in this form, and it is
worth up to ±1.3 km s⁻¹ at 115 GHz.

The crossing frequency itself is not in doubt: 115.260644 GHz lands on the
window's channel grid to within 0.0013 of a channel (0.3 kHz), whereas
115.271202 − 10.3563 MHz = 115.260846 GHz lands at 0.83 of a channel. So
115.260644 GHz is the measured channel and the *laboratory-referred* offset is
115.260644 − 115.271202 = **−10.558 MHz = −27.46 km s⁻¹**, giving a
stellar-frame offset of **−2.72 km s⁻¹**.

**Consequence for Referee 2's M2.** R2 computed −2.20 km s⁻¹ and a widened
concordance of ~1.4 km s⁻¹. That follows from taking the released offset as
laboratory-referred, which it is not. On the laboratory scale the three epochs
are −2.72, −3.45 and −3.62 km s⁻¹, spread **0.9 km s⁻¹**, and the two
transitions are **0.73 km s⁻¹** apart. The concordance therefore does *not*
weaken. We would have said so plainly if it had; the arithmetic is now in
`round10_calc.py` and the numbers reach the page only through macros
(`\DnuBpicThree`, `\DvBpicThree`, `\StelBpicThree`, `\StelBpicSix`,
`\StelBpicCoarse`, `\BpicSpreadKms`, `\BpicPairSepKms`), all of which reproduce
the previously printed Table 21 entries exactly.

**What changed in the paper.** Table 7 and Table 21 are now macro-sourced and
both use the laboratory rest frequencies; Table 7's caption states the rest
frequency, the Doppler convention (radio) and the 1-MHz catalogue rounding
explicitly, and says that the released offset column is 0.202 MHz smaller for
CO(1→0) as a result. The mask appendix lists the rounding as a known defect of
the frozen mask.

**A further error in the same table, which no referee caught.** Table 7's `ν
(GHz)` column was the **spectral-window centre**, not the crossing frequency.
For β Pic the two coincide to ~0.1 MHz by accident; for HD 48370 they differ by
219 MHz and for CP−72 2713 by **845 MHz**. We verified this by code reading:
`round9_calc.py` computes `\CpTwoFreqGHz` as `0.5*(flo+fhi)`, so the
"345.1152 GHz" quoted for the CP−72 2713 feature throughout the paper — and used
by Referee 2 in M3 — is the window centre. The crossing is at **344.2697 GHz**.
Table 7 now carries ν_cross, labelled as such, with the window centre named as a
different quantity in the caption.

**Doppler convention (R2-m20, R2-M2).** Also verified: the printed −1326 km s⁻¹
for CP−72 2713 is c·Δν/ν_window-centre, which is neither the radio nor the
relativistic convention. Radio convention against the laboratory CO(3−2) rest
frequency gives **−1323.2 km s⁻¹**. The paper now states the convention once
and uses `\DvCpSeven`.

### A5 — Type 3 fonts and the gate that reported "0"

**Verified.** The released PDF contains **3 Type 3 fonts, all on page 6**:
`EVICAO+DejaVuSans-Bold`, `GCWXDV+DejaVuSans-Oblique`, `BMQQDV+DejaVuSans`, all
inherited from `figures/pipeline_schematic.pdf`, which was not produced with
`pdf.fonttype=42`. They are present in v3.39's and v3.40's released PDFs too.
The generator for that schematic is not in the version folder, so it cannot be
regenerated here; `gs -dNoOutputFonts` was **not** applied. `BUILD_NOTES.md` now
records this as a known inherited defect, states the corrected gate (fonts are
enumerated per page from the PDF with `f[2] == 'Type3'`, which catches glyphs
inherited from included figures — the old gate did not), and records that the
schematic carries ~12 hand-typed survey numbers that violate the single-source
rule and will all be wrong if the freeze is ever swapped.

---

## 2. Referee 1 (interferometry)

**M1 — Hanning smoothing.** *Partly verified; acted on.* We verified the two
things we could check without the measurement sets: (a) the words "Hanning",
"spectral response" and "window function" did not appear anywhere in v3.40;
(b) the Appendix C verification tested for a column named
`EFFECTIVE_BANDWIDTH`, which is **not** a column of the MS v2 SPECTRAL_WINDOW
subtable — the required columns are `CHAN_WIDTH`, `EFFECTIVE_BW` and
`RESOLUTION` (casacore note 229). A null result from a non-existent column name
is not evidence of unsmoothed data. We have **withdrawn that verification in
print**, and added an explicit paragraph stating that ALMA's default online
Hanning smoothing leaves only ~50 % of a channel-centred narrow carrier's power
in the peak channel, so every EIRP₅σ here is optimistic by up to a factor ~2;
that the injections deposit an unsmoothed delta-in-channel tone and therefore
share the bias, which the end-to-end √N check cannot see; and that part of
ρ_lag1 = 0.989–0.991 is instrumental, with the decomposition unmeasured. The
factor is now also in the abstract, in the main-text systematic budget alongside
the 5–10 % flux-scale term, and in the boxed reading rule.

*Not done:* we did **not** rescale the thresholds and did **not** re-run an
injection with the tone convolved by the measured response. Both need the
per-window archive metadata we have not harvested; doing either now would mean
asserting a per-window smoothing state we have not established. Stated as the
first item of the next release.

**M2 — the spectral extraction operator is never defined.** *Verified* (it is
not in v3.40) and **not fixed.** The estimator's visibility-domain weighting is
a property of the released code and is not recoverable from the frozen
per-window products; we will not write down an equation we cannot check against
the implementation. This is an author action before submission and we have
flagged it as such rather than papering over it.

**M3 — control-ring geometry.** *Verified and acted on.* §4.1 ("a single ring
centred on the target") and §5.3 ("shares the star's radius from the phase
centre exactly") are indeed mutually exclusive unless the star sits at the phase
centre, and we confirmed by search that **the ring radius appears nowhere in the
manuscript**. We could not determine from the frozen products which construction
the code implements, and we have not guessed. §4.1 now states plainly that the
radius is a code constant not carried in the frozen products, that the products
do not record which centre the ring uses, and that both are printed with the
next release. §5.3's "identically zero for a circularly symmetric beam" is now
explicitly conditional on the phase-centre construction, with the star-centred
alternative stated as first order in r★/θ_PB — sub-percent at the median 0.1″
offset, tens of per cent at Sirius B's radius. The one-sided, conservative sign
argument holds under either construction and is retained.

**M4 — multiplicative (bandpass) errors.** *Not verified; not fixed.* The
mechanism Referee 1 describes is real and the control ring is indeed blind to
it. Testing it needs the continuum flux at the stellar position, the brightest
in-field source and its sidelobe level, and the bandpass solution S/N — none of
which is in the frozen release. We have not added a claim we cannot support. We
note that the HD 48370 evidence we *did* add (a 0.82 Jy peak with the ring at
the same level; bright ¹³CO in the field but not on the star) argues against a
multiplicative origin there, and that CP−72 2713 remains the case where this
alternative is live and unexcluded.

**M5 — the stage at which σ is evaluated; local-vs-global on all 20 crossing
windows.** *Verified* that only 20 windows contain an on-star crossing
(recomputed: 20). *Not fixed.* The retained products keep the per-window noise
scale but not the per-channel spectra, so the local recomputation exists only
for the four flagged windows, which is already stated. The ambiguity about which
spectrum the MAD is taken on is real and we have not resolved it, for the same
reason as M2.

**M6 — the fine-channel near-static cell: three contradictory statements.**
*Verified by reading, and resolved.* The three statements did contradict each
other. We have adopted the reading the evidence supports: the cell is
**unmeasured, not lost**. The Fig. 4 caption now says the zero returns are a
failure of the same frozen drift-matching criterion that produced — and was
withdrawn for — the coarse 0-of-500 artefact, that no end-to-end zero-drift
injection has been run on a fine window, and that the completeness quotes apply
to the drifting class only. Appendix D says the same thing in the same words.
We did **not** run the fine-window zero-drift injection Referee 1 asks for; it
needs measurement sets not retained locally.

**M7 — the coarse-noise defect.** *Partly acted on.* We have not identified the
mechanism and have not reprocessed a defective window. We have, however, stopped
asserting the containment argument as though it were established: the paper now
says explicitly that whether the defect is window-level rather than
position-level is exactly what is not known while the mechanism is unknown, and
names the check that would settle it (do the 512 control σ values in a defective
window show the same deflation as the stellar one?) as needing per-position
noise records the frozen products do not carry. The load-bearing one-directional
bound is unchanged and is now clearly separated from the parts that are not
established.

**M8 — printed numbers that do not reproduce.** *Every item verified.* Table 9
(`tab:occurrence`) is now generated in full by `round10_calc.py` from the same
frozen rows, both panels, all five rows. Recomputed values:

| row | printed in v3.40 | recomputed | referee's value |
|---|---|---|---|
| 10¹⁵ thresholded | 57, 5.1 % | **59, 5.0 %** | 59, 4.95 % ✓ |
| 10¹⁵ measured | 45, 10.1 % | **47, 9.5 %** | 47, 9.54 % ✓ |
| 10¹⁷ thresholded | 82, 3.7 % | **82, 3.6 %** | 82, 3.59 % ✓ |
| 10¹⁷ measured | 57, 6.2 % | **60, 5.9 %** | 60, 5.87 % ✓ |

Referee 1's diagnosis that the printed 6.2 % is the 10¹⁶ *measured* value copied
down one row is confirmed. The 3×10¹³ and 10¹⁴ rows were correct. Panel (b) was
also correct (29.0 % at p_epoch = 0.1 reproduces exactly) but is now generated
too. Gross bandwidth, `MaskGrossPct`, 11.4 → 13.2, 0.9 % → 1.1 %, 402 → 416 and
0.78 → 0.81 are all covered in §1 above.

*Not fixed:* `make_numbers.py` still cannot be run as shipped (`duty_v331.json`
absent) and `survey_stats.py` still reads an absolute path. We confirm both.
They are release-packaging items, not manuscript items, and are recorded in
BUILD_NOTES.

**M9 — correlated controls and non-exchangeable geometry.** *Acted on in
print, not in analysis.* Both caveats are now stated where the 220 672
pseudo-ranks are quoted: that the star sits at the centre of a ring whose
members are correlated with their azimuthal neighbours, so the joint
distribution is not permutation-invariant; that the pseudo-star construction is
a different geometry again and cannot detect a centre-versus-ring asymmetry;
that the pooled KS p-value treats non-independent ranks (N_eff ≃ 30–43) and is
therefore optimistic; that the relevant check is the two-sample comparison of
the 431 real stellar ranks against the pooled pseudo-ranks (p = 0.38), now
presented as the primary evidence; and that in terms of independent spatial
trials the achievable resolution is nearer a few × 10⁻² than 1/513. We did
**not** run the block bootstrap — the per-window control statistics are retained
in the public release, not in the frozen products we build from.

**M10 — claims that outrun their evidence.** All four verified and fixed.
(a) The abstract now says the unresolved-excess completeness is measured on
**six coarse configurations**, not twelve. (b) §6.1 case (i) — see R2-M8 below;
the benchmark sentence now names the evidence. (c) The coverage fraction now
distinguishes the 168 sample entries (~1 %) from the 88 stars actually searched
(**~0.5 %**), in §2 and §3. (d) F/G ratios corrected to **×3.7 and ×3.1** from
Table 16, and the M-dwarf ratio to the table's single value **×0.6**, in the
abstract, §3 and Appendix Q.

**M11 — the two tables disagree on the β Pic offset.** See A4. Referee 1's
reading that the two tables use crossing frequencies differing by ~0.2 MHz is
correct, and the cause is the mask catalogue's 1-MHz rounding, not a
transcription error. One definition (laboratory rest frequencies, radio
convention) is now used in both tables.

**M12 — sample-definition inconsistencies.**
(a) *Verified and fixed:* both parallax cuts are now stated together
(σ_ϖ/ϖ ≤ 0.8 % for the sample, ≤ 10 % for the census) with the explicit note
that the ratio compares two differently selected populations.
(b) *Not fixed:* the criterion (ii) wording ("largest accepted offset ~0.7
FWHMs, Sirius B") versus the footnote's 3.6–16 % correction. We could not
resolve this from the frozen products, which carry no per-window primary-beam
radius, and have not guessed at a replacement number.
(c) *Verified:* "1 star in 44, 1 EB in 57" are 20-pc release numbers. Not
restated on the current sample, because the bycatch determination for the 88-star
sample is not in the frozen products. Flagged for the authors.
(d) **"Seven designation-linked component pairs" — Referee 1 says this should be
six. We checked, and the text is right and the code is wrong.** See §4 below.
(e) *Verified:* on-source times run from 20.7 s, so "the shortest retained are
1.0 and 1.5 min" is wrong. Not yet repaired in §3; flagged.

**Minor points.** m1/m2 fixed (A1). m3 *verified*: the median S_min is
**6.71 mJy**, not 7.3; the text now uses `\SminMedian` and the downstream
φ ≈ 1.0 × 10⁻²¹ W m⁻², with the 0.9 pc reach unchanged (we recomputed it:
0.89 pc). m4 *verified* — W is genuinely never given; the appendix now says
explicitly that W is not carried in the frozen products and ships with the
release, rather than leaving the reader to notice. m6, m7 (the "release" unit on
a per-window quantity — fixed to "window"), m14 (Table 15 said "6
configurations / 3 stars" while only AT Mic and AU Mic are enumerated; changed
to 2 stars to match the enumeration, and flagged) all verified and fixed. m17:
Fig. 9 (`eirp_vs_distance`) has been **deleted** and merged into Fig. 1(a) per
R3-minor-6; Fig. 12 (`aumic_control_maxima`, 0.29 columnwidth) **deleted** per
R3-minor-4. m19: `BLMeerKAT2026` and `BLoverview` were indeed uncited and have
been removed from the bibliography. m5, m8, m9, m10, m11, m12, m13, m15, m16,
m18, m20 not addressed — see §5.

---

## 3. Referee 2 (radio/mm stellar astrophysics)

**M1 — show the spectra.** *Partly acted on.* We did not add the spectra figure:
the channel-level products of those execution blocks are not in the frozen
release and re-extracting them is a visibility-level operation we have declined
for CP−72 2713 on pre-registration grounds. But Referee 2 is right that the flux
densities are immediate, and **we verified all four of them exactly**:

| window | T★ × rms | peak |
|---|---|---|
| β Pic B3 | 14.65 × 3.696 mJy | **54 mJy** per 244-kHz channel |
| β Pic B6 | 11.68 × 6.660 mJy | **78 mJy** per 15.3-kHz channel |
| HD 48370 B6 | 27.10 × 30.303 mJy | **0.82 Jy** per 122-kHz channel |
| CP−72 2713 B7 | 5.81 × 2.097 mJy | **12 mJy** per 488-kHz channel |

Table 7 now carries an S_peak column (macro-sourced), and the β Pic text quotes
the 2−1/1−0 flux-density ratio **1.4** against the optically thin LTE
expectation of ≈4, with the resolved-out-flux and different-weighting caveats
attached. The HD 48370 flux is used in the disposition as Referee 2 suggests.
Crossing multiplicity: Appendix G's 114 formal crossings in the β Pic B6
ultra-fine window is now promoted into the disposition — but we state only the
*count*, because **the released products do not record whether those channels
are contiguous**, so we cannot convert it into a line width in km s⁻¹ as
Referee 2 does. That distinction is stated in the text.

**M2 — the β Pic frame chain.** See A4. Referee 2's diagnosis of a catalogue
rest-frequency problem is **confirmed and quantified** (1-MHz rounding
throughout the mask, −0.202 MHz for CO(1−0)), but the arithmetic runs the other
way: the laboratory-referred numbers are −10.56 MHz / −27.46 km s⁻¹ /
−2.72 km s⁻¹, and the 0.9 km s⁻¹ concordance stands. The released offset column
is the quantity that needs correcting, and we say so in Table 7's caption.
The relativistic-vs-radio point is verified and the convention is now stated.

**M3 — CP−72 2713's astrophysical context.** *Verified and added.* The star is
now introduced as a K7/M0 member of the ~24 Myr β Pic moving group with a cold
dust-rich debris disc detected in ALMA 1.33-mm continuum (Moór et al. 2020, AJ
159, 288 — citation checked), with the explicit statement that the prior for an
astrophysical explanation there is *higher*, not lower, than at a random sample
member. We also verified and now report Referee 2's point 2 from our own
products: the flagged Band 7 window covers CO(3−2) at the stellar velocity and
the Band 6 fine window covers CO(2−1), and neither crosses threshold — **a
non-detection of circumstellar CO in the CP−72 2713 belt**, reported as such.
*Not done:* the per-integration time series at the crossing frequency (no
retained per-integration products at that frequency), and the full
Splatalogue/CDMS/JPL query over the whole 344.25–345.98 GHz window in both
frames. The existing wider-catalogue query (nearest entry H¹³CN(4−3) at
−195 km s⁻¹) is retained with its honest label, "a statement about the
catalogues consulted, not a proof that none exists".

**M4 — the flagged population is the young disc-bearing subset.** *Verified and
added.* β Pic, AU Mic and CP−72 2713 are all β Pic moving-group members with
debris discs and HD 48370 is a disc host behind a molecular cloud; the rate
argument in Appendix N is, as Referee 2 says, the wrong test. Appendix N now
states that the flags are concentrated in the systems with the richest
astrophysical foreground, that the searched sample is to a good approximation
the ALMA debris-disc and young-moving-group archive, and that this is the worst
case for astrophysical false positives at mm wavelengths. The reading rule for
f₉₅ now says "a sample dominated by young, dusty, magnetically active stars, not
nearby F/G stars in general". *Not done:* adding disc/age/gas columns to
Table 16 — that needs a literature compilation for 88 stars that we cannot
audit here.

**M5 — the mask is stellar-frame only.** *Partly verified.* The physical
argument is correct and is now stated as gap (iii) of a new "four gaps in the
frozen mask" paragraph. **We could not verify the specific example:** Kapteyn's
Star and Van Maanen's Star are **not in the 431-window searched set** — we
checked the full star list. If they appear at the cited line it is in a
different context. We have not added an LSR-frame tube, because the mask is
pre-registered and frozen; we pre-register it instead for the confirmatory
sample.

**M6 — [C I] and the tuned-line rule.** *Verified in detail and stated.* All 12
Band 8 windows belong to η Crv, HD 48370 and HD 61005; each of the three has a
fine window covering 492.16065 GHz; Table `tab:maskband`'s Band 8 column is
**0.00 GHz for all eight species**; and the nearest-transition column reports
CO(4−3), 30 GHz away, for all twelve. HD 48370's 491.657–492.578 GHz window does
carry an on-star crossing at **T★ = 5.05 with ring max 6.23**, exactly as
Referee 2 says. Foreground [C I] is now given as an independent corroboration of
the HD 48370 disposition. The H₂CO nine-vs-eight species discrepancy is verified
and stated. The tuned-line masking rule is adopted as the pre-registered
criterion for the confirmatory sample.

**M7 — stellar variability.** *Partly acted on.* We added the point that costs
nothing and is verifiable: Appendix K's error model
σ²_tot = σ²_map + (f_cal S)² + σ²_model has **no intrinsic-variability term**,
which makes the screen uninformative for precisely the active M dwarfs a
radio-stellar reader cares about — now stated, with the variability term named
as a next-release item. τ Ceti is no longer described as young and active (see
m5) and the two incomplete lists are repaired (m6). *Not done:* the flare
paragraph in §5.3 and the tabulation of the seventeen continuum detections with
fluxes and epochs — both are additions we could not pay for within the length
mandate.

**M8 — the Arecibo benchmark is an S-band number.** *Verified and fixed.* The
ν² gain scaling is stated explicitly, together with a **frequency-matched
benchmark**: a 12-m aperture radiating 1 MW at 230 GHz, EIRP ≈ 8×10¹⁴ W, within
a factor of two of this release's median threshold of 1.4×10¹⁵ W. The
4×10⁹ W mobile-leakage benchmark, quoted once and never used, has been dropped.

**M9 — the T_eff proxy.** *Verified and stated.* §3 now says the composition
rests on `teff_gspphot`, available for 52 of 88 sample stars and 49 % of the
census and missing preferentially for the coolest objects, so the M fraction is
a lower limit and the earlier-type ratios are upper limits. The two parallax
cuts are stated together (R1-M12a), and the abstract's ×0.6–0.7 is now the
table's ×0.6. *Not done:* re-deriving the composition from MK types or GCNS.

**M10 — the retained noise population is mis-described.** *Verified, and the
description is corrected in print.* Recomputing q = σ√(t_on Δν_ch) over all 431
retained windows: the range is **0.33× to 95.8×** the sample median — a factor
of ~290, not ~12 — with a clear Band 8 secondary mode (band median 55.7×;
η Crv and HD 48370 Band 8 windows at 64–96×) and a factor-52 spread inside
Band 6 alone. Every number Referee 2 gives is reproduced. §5.2 now carries an
explicit correction paragraph saying what we previously said and what is true,
notes that the band dependence is predicted by SEFD and that per-band
normalisation would make this a physical comparison rather than an outlier cut,
and keeps the exclusion — which never depended on the population being narrow —
with its one-directional bound intact.

**M11 — three cheap strengthenings of HD 48370.** *Two of three verified and
added.* (2) We confirm from the frozen export that the ¹³CO(2−1) window
(218.560–220.400 GHz) of the same execution block A002_Xc26103_X155a has a
control-ring maximum of **20.4σ** against only **4.6σ** at the star — bright
¹³CO in the field but not on the star. This is now in the paper as internal
corroboration. (3) The 0.82 Jy peak is added. (1) We did **not** re-derive the
barycentric velocity through our own frame chain; the frozen products do not
carry the HD 48370 block's ephemeris term, and the dependence on
Cataldi et al.'s frame convention is retained as a stated limitation.

**M12 — background line emitters.** *Not acted on.* We agree the class is
missing and we have not added it, because the strongest counter-argument
(narrowness) is exactly the measurement we cannot make — see M1. Listed in §5.

**Minor points.** m3 *verified and fixed*: `Matra2017` pointed at ApJ 842, 9
(Fomalhaut); the β Pic CO paper is **MNRAS 464, 1415**, now corrected, with
Dent et al. (2014, Science 343, 1490) added. m4 *verified and fixed*:
`Hallinan2007` (ApJ 663, L25) is the TVLM 513 paper; LSR J1835+3259's aurorae
are **Hallinan et al. 2015, Nature 523, 568**, now cited. m5 *verified and
fixed*: τ Ceti is no longer called a young active system. m6 *verified and
fixed*: both lists now match their counts. m7 *fixed*: the glossary entry that
defined "star-exceeds-ring" as the stage-1 flag with count 5/431 has been
deleted along with the other six entries duplicated in Table 1 (R1-m19), which
removes the conflation; the main text's distinction between 5 rank-first windows
and 4 stage-1 flags stands, and we confirm both counts from the export.
m8, m9, m12 *verified and now disclosed in the Data Availability section* — see
§4. m14 *verified*: the CP−72 2713 execution block does carry 2993.76 s for its
fine windows and 4009.82 s for its coarse ones; we could not determine the cause
and have not asserted one. m13, m10, m11, m15, m16, m18, m19 not addressed —
see §5.

---

## 4. Three things we found that no referee raised

**(i) The system count double-counts one star.** Referee 1 (M12d) says the text's
"seven designation-linked component pairs" should be six; Referee 2 (m9) says
HD 139084B appears twice in the released file. Putting the two together and
checking the export, **the text is right and the de-duplication list is
incomplete**. `HD 139084B 805632` and `HD 139084B 921024` have different system
identifiers and different distances (39.31 and 38.72 pc) but the *same* execution
block, the *same* four spectral windows and the *same* on-source times, and they
follow exactly the naming pattern of the two pairs that *are* in the
de-duplication list (`2MASS J05241914-1601153 551040/717696`,
`LP 476-207 384128/783296`). There are seven such pairs, not six, so
**N_sys = 82 counts one system twice and the correct independent-system total is
most likely 81**. We have not re-run the analysis — that would break the freeze
and trip the drift guard — but the Data Availability section now states the
defect, its size (every per-system quantity optimistic by ≲1.5 %, inside the
quoted brackets), and that the frozen analysis is not re-run for it. This needs
an author decision before submission.

**(ii) Two build gates were reporting false.** The Type 3 gate (A5) reported "0"
while 3 existed. Separately, v3.40's BUILD_NOTES claimed "0 underfull hboxes";
the v3.40 build in fact emits **10**, all from unjustified text in fixed-width
`p{}` table columns. Both gates are corrected in BUILD_NOTES, and the underfull
boxes are now actually zero (the `p{}` columns are `\raggedright`).

**(iii) Two mask-loss computations in the codebase disagree by a factor ~7.**
`survey_stats_round10.py` computes `mask_loss_GHz` = 0.64 GHz over 15
transitions; the generated Table `tab:maskband`, which is the in-paper
authority, gives 4.96 GHz over 276 transitions of eight species, and
`round9_calc.py` renews `\EffBandGHz` from the latter. We did not reconcile
them — we cannot check the mask definition against the pipeline from here — but
a paper with a single-source-of-truth policy should not carry two. Flagged for
the authors.

---

## 5. Recommendations we declined, and why

1. **R3-M3, split §5.3 into two subsections.** Declined. We compressed §5.3 by
   ~6 kB instead (false-alarm components ii and the trials-chain box removed,
   primary-beam analysis condensed, line-exclusion block halved). A structural
   split would have relabelled every cross-reference in the paper for no change
   in length, and the length mandate had priority this round.
2. **R3-M8, expand §5.1.** Declined on length. The abstract now leads with the
   result and names the Barnard's Star / Wolf 359 firsts, which was the part of
   this we could afford. §6.1 is protected and untouched.
3. **R2-M1(1), the spectra figure; R2-M12, background emitters; R1-M6's fine
   zero-drift injection; R1-M7's reprocessing; R1-M9's block bootstrap;
   R2-M5's LSR tube; R2-M7(3)'s continuum table.** All declined for the same
   reason: each needs data outside the frozen release, and we would rather leave
   an honest gap than assert an untested result.
4. **R3-M5, one label per concept; R3-M4's target of ≤40 ", not X"
   constructions; the full caption cap; R3's 17→11 appendix plan.** Partly done
   (17 → 14 appendices; the longest seven captions cut; several corrective
   constructions rewritten) but not completed. The remaining terminology
   unification is a copy-edit pass we did not attempt mid-revision.
5. **R3-M7/M9, R1-m18, R2-m17 — the author TODOs, the VBRL affiliation, the git
   tag, the arXiv ID, the CRediT split, the incomplete EB metadata table, the
   product version string.** Deliberately **not resolved**: these are author
   input. All seven markers are still in the source, at lines 38 (VBRL
   affiliation), 187 and 198 (White 2026 EB overlap, and its exception clause),
   2577 (competing interests), 2580 (arXiv ID for White 2026), 2585 (CRediT
   roles) and 2596 (submission git tag). The Data Availability statement still
   rests on a tag that does not exist; we have not pretended otherwise.

---

## 6. Build and verification

* `pdflatex` ×3. **36 pages** (v3.40: 39; standing ceiling 38).
* **0 errors**, **0 undefined references or citations**, **0 multiply-defined
  labels**, **0 underfull hboxes**.
* **1 overfull `\vbox`, 1.57 pt (0.55 mm), in the output routine.** This is a
  page-fitting warning, not an overfull hbox; nothing is set into the margin.
  The as-received v3.40 source had none, so it is a regression introduced by
  this round's repagination, and we could not clear it by local adjustment.
  Reported rather than suppressed.
* **3 Type 3 fonts, page 6 only**, all DejaVu glyphs inherited from
  `figures/pipeline_schematic.pdf` — pre-existing in v3.39 and v3.40, generator
  not in the version folder, `gs -dNoOutputFonts` tested and not applied.
* The v3.31 freeze is unchanged (431 windows / 88 stars / 82 systems), the
  drift guard in `round10_calc.py` is unchanged and passes, and
  `survey_stats_round10.py` still reproduces every published value.
* Trim accounting is in `BUILD_NOTES.md`. The page target is met; the character
  targets are not, and we say so there rather than rounding them into
  compliance.
