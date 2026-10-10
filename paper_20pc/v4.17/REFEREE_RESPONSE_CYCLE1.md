# Response to the three referee reports on v3.42

Manuscript: *An ALMA Archival Search for Spectral Technosignatures toward Stars
within 40 pc*, White & Dey. Revision **v3.43**.
Reports: `v3.43_referee1_radio.md`, `v3.43_referee2_radiostars.md`,
`v3.43_referee3_general.md`.

We thank all three referees. Three of their findings were factual errors in the
manuscript against our own released catalogue, and one (R1-M1) was a
misdescription of the detection statistic that three separate arguments rested
on. All are corrected, and every replacement number is generated rather than
typed: a new script `v343_calc.py` emits `survey_numbers_round13.tex`
(129 macros) from `per_target_results_v3.43.csv`, `pipeline_peakfreq_v342.json`,
`archive_meta_v343.json`, `linecat_v343.json`, `v342_local_null.json` and
`localnull_code/ctrlmax.json`, and is wired into `make_all.sh`.

**Status: 29 pages (unchanged). Main text 20.98 (was 21.03), back matter 0.92,
appendices 6.76 (was 6.70), bibliography 0.33, total 28.99 (was 28.96). 0 LaTeX errors, 0 undefined references or citations,
0 multiply-defined labels, 0 overfull boxes, 0 underfull boxes, 0 Type 3 fonts,
0 em-dashes. Verified to build from an empty directory with the 27-item arXiv
set.**

**Note on appendix lettering.** Appendices C and D (demonstrated diagnostics;
cross-target occupancy) are merged into one "Ancillary screens" appendix, so
every appendix from D onward shifts back one letter relative to v3.42. Where
this letter cites an appendix by letter it uses **the v3.42 lettering the
referees saw**; the manuscript's own cross-references are all `\ref`-based and
resolve correctly. The new mapping is: A conventions, B injection-recovery,
C ancillary screens, D per-target results, E line mask, F AU Mic, G continuum
lane, H false-alarm accounting, I excluded entries, J conditional transmitter
fraction.

---

## Referee 1 (observational radio/mm interferometry)

### M1. Equation (2) and §4.1 do not describe the statistic the pipeline computes

**Accepted in full, and settled from the release itself rather than taken on
trust.** `v342_local_null.json` states the statistic as "max over channels and
drift trials of the inverse-variance-weighted, de-drifted stack at the stellar
position", reimplemented "using ... `*_search.npz` for the **all-probe** robust
noise map sigma[t,c]", and its `method/validation` block records that the
reimplementation reproduces the published `star_peak_snr` **bit for bit**
(absolute difference exactly 0.0 in float32) for all four flagged windows. The
released `localnull_code/local_null.py` implements exactly that: `Z = I/sigma`,
`u = 1/sigma`, `X = Z*u`, `num = sum_t X_t(shifted)`, `den = sum_t invvar`,
`snr = num/sqrt(den)`.

Changes:

- **Eq. (2) rewritten** as the inverse-variance-weighted de-drifted stack, with
  the note that it reduces to amplitude-over-scale only for a sigma independent
  of integration and channel.
- **sigma redefined**: 1.4826 x MAD taken *across the control positions* at
  each integration and each channel, shared by star and controls; global in
  position, local in frequency and in time.
- **The across-position median is stated not to be subtracted** from the
  numerator, so T is an absolute stacked S/N carrying a cross-position noise
  scale, and that is given as the reason a beam-filling line drives star and
  ring up together.
- **Table 3 steps 4, 6 and 7 corrected** (block median with W = 65; robust
  noise map sigma(t,nu) across the 512 controls; an inverse-variance-weighted
  stack).
- **(b)** The "global in frequency, so it can misstate the local noise"
  paragraph described a defect the pipeline does not have. It now says what is
  true: because sigma is built from the annulus, no variance belonging to the
  stellar position alone enters it. The four measured local-to-global ratios
  are retained and reinterpreted as a test of the scale's frequency dependence.
- **(c)** The breakdown-point argument is rewritten to count positions, not
  channels: for a compact feature at the star none of the 512 controls carry
  it and the 50 per cent breakdown holds; for beam-filling emission all of them
  do, which is the HD 48370 case.

### M2. Nothing measures excess variance specific to the stellar position

**Accepted as a stated limitation; the measurement asked for cannot be made
from the release.** §4.1 now states the gap explicitly, together with R2-M5's
bandpass-residual scaling and its numerical requirement (an artefact of
CP-72 2713's 12.2 mJy feature needs epsilon x S_cont = 12.2 mJy, so a
per-cent-level bandpass residual would need a jansky-level stellar continuum).
The star-versus-control residual-variance ratio and the scramble null on the
star's own residual are **deferred**: the release retains full dynamic spectra
for the star and only 8 of 512 controls per flagged window, which is too few to
calibrate a variance ratio, and the paper now says so rather than implying the
test was run.

### M3. The one-sided residual asymmetry needs a bound, not only a sign

**Accepted.** The Spearman radial test is promoted out of its parenthesis and
given its distribution: median 0.009 over the 304 crossing-free windows, 5th
and 95th percentiles -0.08 and 0.11 (new macros `\RingRhoNullLo/Hi`,
`\RingRhoBoundPct`). The two-sample comparison of the 431 real stellar ranks
against the pooled pseudo-ranks is promoted to the headline of the
exchangeability passage and set in bold, with the explicit statement that this
is the test that *can* detect a centre-versus-annulus asymmetry and the
pseudo-star test is not.

### M4. The beam-filling mechanism is stated backwards

**Accepted.** Replaced with the referee's interferometric statement: smooth
emission lives on short baselines whose phases barely change under a phase
rotation of a few arcsec, so star and annulus rise together (HD 48370), while
offset-centroid emission raises particular controls above the star (the same
star's 13CO window, ring maximum 20.4 at 9.2 arcsec against 4.6 at the star).
Both asymmetries are now stated with their directions, including the
multiplicative-calibration one, which favours the star.

### M5. The baseline filter is not a running median, and W can be printed

**Accepted; Appendix A's claim is withdrawn.** The filter is described
everywhere as a contiguous block median with linear interpolation between block
centres, `nb = max(2, n // 65)`. W is printed: 65 channels wherever a window
keeps more than 130 usable channels (65 to 74 in practice over the fine class)
and n/2 otherwise (30 to 59 over the coarse class), with ceilings of about
32 MHz at the fine class's modal 488 kHz and about 0.9 GHz at the coarse
class's 15.62 MHz. All generated from `pipeline_peakfreq_v342.json`'s own
trimmed channel counts, matched to the catalogue on (EB, window edges); the
match is exact for all 431 rows.

### M6. The smearing census is wrong: nine windows, not three

**Confirmed exactly and corrected in both places.** `\NSmearLo` = 9;
`\NSmearWorst` = 5 at eta_smear 0.574 to 0.606, all 15.3 kHz Band 6 windows and
so among the most drift-capable in the survey, carrying threshold multipliers
1.65 to 1.74; two of the nine are stage-1 flags. The hand-typed triple in
Appendix A is replaced by a generated list (`\SmearList`), and a generated
table fragment `tab_smear.tex` ships with the release. "Every other window
agrees to better than 1 per cent" now reads "the remaining 422". The
sinc(pi Delta/2) form is justified in one clause as the conservative choice
against the min(1, 1/Delta) occupancy reading (0.64 against 1.0 at Delta = 1).

### M7. The primary-beam statements are contradicted by the catalogue

**Confirmed, with one of the referee's numbers not reproduced.** From
smin/(5 rms) over the 431 retained rows: median 1.00004, 90th percentile 1.018
(the paper's 1.012 does not reproduce), **41 rows above 2 per cent** and 31
above 10 per cent across 6 stars, largest **j1256-1257 Band 7 at 1.81**, which
is 0.46 theta_PB or 0.50 of a true FWHM and is now named in the manuscript for
the first time. Sirius B spans **3.6 to 18.6 per cent**; the referee's 4.6 per
cent lower bound does not reproduce from the released catalogue, and we say
3.6 to 18.6 rather than the manuscript's former 3.6 to 16. Selection criterion
(ii) now states the rule the code enforces (extraction aborts beyond
2 theta_PB, largest retained offset 0.46 theta_PB) instead of "one FWHM", and
no longer attaches epsilon Eri's offset to Sirius B's correction. The
1.22 lambda/D versus 1.13 lambda/D disclosure now covers the *correction*, not
only the annulus, with the resulting up-to-10-per-cent optimism stated.

### M8. Two beta Pictoris empirical-significance claims are contradicted

**Confirmed and corrected, on the operative symmetric statistic.** The retired
region-max values 20.3 and 12.8 and the add-one p < 0.0044 are gone. The
Band 3 peak is T* = 14.65 and the Band 6 peak T* = 11.68; five of the 431
per-window control maxima match or exceed each, giving add-one p = 0.014 on a
denominator of 432, stated explicitly. The claim that beta Pic's own CO-filled
ring maximum of 15.2 is "the largest here" is corrected: it is the fifth
largest, and HD 48370's CO(2-1) ring at 26.83 and 13CO ring at 20.37 are quoted
in the same sentence, which is also where the paper already quoted 20.4 three
paragraphs later.

### M9. The trials accounting is internally inconsistent

**Accepted; stated once, in cells.** A window holds 177 to 6,866,208
channel x drift cells (median 468); the survey holds 4.60e7. A one-sided
Gaussian 5 sigma tail predicts 13.2 chance **cells**. The frozen products carry
the observation in the same units: **229 on-star cells reach 5 sigma, in 20
windows**, of which 174 belong to the four stage-1 flags (three of them CO).
The remaining 55 cells over 16 windows stand against 13.2 expected, a factor
4.2 that channel adjacency accounts for at a mean run of three to four cells.
The "1.1e5 effective trials per window" claim in §5.3 and the
"8.5e4 to 1.1e5 effectively independent cells" in Appendix L are both
withdrawn: the referee is right that they cannot both be true, and neither is
needed once the comparison is made in one set of units.

### M10. The local null has no power against fixed-channel instrumental artefacts

**Accepted; stated in instrumental terms in the CP-72 2713 subsection.** The
scramble shifts every integration independently in channel, so it destroys
anything coherent across integrations and with it any frequency-stationary
feature: a correlator spur, a fixed-channel bandpass residual, a birdie. A
small local-null p disfavours thermal noise and nothing else, and is not
evidence against an instrumental origin. The manuscript now adds that this
window's other two instrumental discriminants are also absent (the occupancy
check is blind to a feature confined to one block and one target; a single
searched execution block leaves no recurrence test).

Both supporting requests are met and reproduced here from
`localnull_code/ctrlmax.json`: a **Gumbel** fit to the same 512 control maxima
gives p = 4.4e-3, a factor 3.6 above the GEV value and still above Bonferroni,
so the two nulls' close agreement is partly fortuitous while the conclusion is
not; and the same window's **ring** maximum has local-null p = 3.0e-3, only 1.9
times the star's, which is now in the text as the most honest one-number
summary of this feature.

### M11. The Hanning factor is applied blanket across two correlator modes

**Accepted, and now evidenced rather than assumed.** `archive_meta_v343.json`,
shipped in this release folder, carries the archive's reported effective
spectral resolution per spectral window. Its ratio to the measurement set's own
channel separation is **exactly 2.00 in 403 of the 431 windows, including 309
of the 313 coarse TDM windows**, which is ALMA's default online Hanning
smoothing; the other 28 report a smaller ratio, the signature of online channel
averaging, where the peak-channel loss is smaller. The blanket factor is
therefore correct for the great majority of both classes. Appendix A's "the
per-window smoothing state sits in archive metadata not yet harvested" is
withdrawn. We still do not rescale.

### M12. Document the edge handling that actually ran

**Accepted.** The window's recorded width shows the standard 4 per cent edge
trim already applied, so channel 35 lies about 92 MHz inside the true baseband
edge rather than at it. The manuscript also states that the block-median
baseline places its first interpolation node near channel 65, so the crossing
sits within a few channels of that node, which is where a block median is least
well behaved. The per-window record of whether the trim was fixed or adaptively
extended is not in the release; we state the arithmetic we can support and
leave the rest unclaimed.

### Minor points

1. **Table 9's nu column.** Defined in the caption as the window *centre*, with
   the note that it differs from the crossing frequency by up to 0.85 GHz and
   that Table 7 carries nu_cross. The label inside `v342_local_null.json` is a
   frozen product and is left as it is, with the definition now in the paper.
2. **§5.2 noise-screen units.** The admissible threshold range is now stated in
   absolute q units, with the six defective windows at 11.6 to 14.7 and the
   lowest retained at 2.2e4.
3. **Root cause of the coarse-noise defect.** **Deferred**: the theoretical rms
   (`rms_theory_per_int_mJy`) is in the per-window `*_result.json` files, which
   are not in the release folder. We have added the referee's other point,
   which the release does support: all six have on-source times of 12 to 48 s
   and were removed by the noise screen, not by an integration-time cut.
4. **Drift ceiling not uniform.** Corrected and macro-sourced: the ceiling is
   12.0 to 13.3 Hz/s/GHz, line-of-sight |a| = 3.60 to 4.00 m/s^2, the generic
   value everywhere except the 12 windows where a known planet's own bound
   raises it. The scope box and §3.4 now carry the range.
5. **§3.3 window-cap arithmetic.** The "53 of the 107" claim does not
   reconcile and the release does not carry the configured-window count needed
   to repair it, so the claim is **withdrawn** rather than guessed at; the
   verifiable content (the cap bound 61 Vir Band 7; three targets are
   represented by their deepest single window) is retained.
6. **Criterion (ii) as enforced.** Corrected, see M7.
7. **Catalogue columns.** **Deferred**: adding the star's offset and
   primary-beam gain, the peak channel index, W and the per-integration and
   theoretical rms to the released CSV requires regenerating it against
   products that are not in this folder. Noted for the author.
8. **rms_mJy vs smin_mJy.** The ratio is 5 x PB, now stated where the
   primary-beam correction is defined.
9. **The pseudo-rank mean.** Labelled as the construction value on a 512-point
   grid under the add-one rule, carrying no information; the KS result carries
   the argument.
10. **"the medians coincide".** Now says which quantity: the median
    *statistics*, not ranks.
11. **Fig. 2 legibility.** The figure is reduced to 0.80 textwidth for length,
    and its label fonts are enlarged by the same factor in the generator, so
    the rendered label size is unchanged. Its top-panel title, which overflowed
    the axes at the larger font, is shortened.
12. **`\SminMax` = 1.30 Jy.** Not yet parenthesised; **deferred** to the author
    with the rest of the Table 4 notes.
13. **Author-side items.** Left in place as TODO markers, per the standing
    rules: the Data Availability tag, White (2026)'s arXiv identifier, the VBRL
    affiliation and CRediT.

---

## Referee 2 (radio stars / circumstellar astrophysics)

### M1. The CP-72 2713 catalogue check was run at the superseded frequency

**Confirmed, and the disposition is re-argued on the physics.** The
-195 km/s H13CN(4-3) number is a relic of the superseded 345.1152 GHz window
centre and is **deleted**. Re-querying at the corrected 344.269746 GHz, keeping
only transitions flagged as observed in space and pushing each through this
paper's own frame chain (which reproduces the published CO(3-2) offsets of
-1323.2 and -1300 km/s), returns **three** catalogued transitions inside the
+/-50 km/s tube in both the stellar and the LSR frame: the unidentified Lovas
entry U-344288.4 at +7 (+7) km/s, SO 8(8)-7(7) at -12 (-13) km/s, and
34SO2 10(4,6)-10(3,7) at +45 (+44) km/s. The manuscript says so, and states
explicitly that **SO is absent from the 17-transition, 11-species mask** and
that the feature would have been masked had SO been in it.

The disposition now rests on excitation: SO 8(8)-7(7) has E_u = 87 K and the
34SO2 transition 89 K, both needing warm dense gas (n(H2) >~ 1e6 cm^-3), and a
~24 Myr debris belt at 37 pc with CO(3-2) undetected *in this very window* and
CO(2-1) undetected in Band 6 cannot produce SO or SO2 without CO. The rule we
actually use is now stated: a full catalogue query at the *crossing* frequency,
filtered to species detected in space, followed by an excitation argument; the
11-species mask is a contamination screen and not a disposition tool.

The referee's fifth request is met and goes further than they asked: the same
query run at each of the 20 crossing frequencies returns at least one
catalogued transition within 60 km/s for **19 of the 20**, median 3. Bare
catalogue proximity therefore has no discriminating power at these frequencies,
and the manuscript says that the earlier reliance on it was misplaced.
One consequence: Appendix F's "no tube in any frame excludes it" is corrected
to "no tube *of this mask*", with a pointer to the physical argument.

### M2. The second execution block is in the archive

**Confirmed and deferred by instruction.** `archive_meta_v343.json` records
that member OUS uid://A001/X2d20/X2e25 has two raw ASDM progenitors and that
one was searched. A separate job is handling the search of the second block;
this revision does not pre-empt its result. What the manuscript now carries is
the audited scope of the issue, which is larger than one block: the 102
searched member OUSs hold 448 public execution blocks between them, 75 hold
more than one, and 304 of the 431 windows (71 per cent) covering 62 of the 88
stars sit in an OUS with at least one further unsearched block. The survey is
archive-complete in targets and tunings, not in epochs or integration time.

### M3. No time-domain test on a flare star at the flux level flares reach

**Deferred, and flagged as such.** The per-integration light curve of the
crossing channel, the flare-like-transient test and the comparison against the
continuum light curve all need the retained dynamic spectra, which are not in
this release folder. The manuscript continues to state plainly that these tests
were not run.

### M4. The two marginal flags are the two crossings nearest a band edge

**Confirmed from the shipped catalogue and recorded.** CP-72 2713 sits 0.010 of
the way into its window and HD 48370 Band 6 0.024, the two most edge-proximate
of the 20 crossings, while the two beta Pic crossings sit at the dead centre of
theirs. Were the four flags drawn at random from the 20 crossings, the two most
edge-proximate would both be flags 3.2 per cent of the time. The manuscript
states the coincidence, bounds it two ways (the 4 per cent trim already
applied, so channel 35 is ~92 MHz inside the baseband edge; and the
block-median node position), and says plainly that at a band edge the concern
is structure rather than scale, so the 0.97 local-scale ratio addresses the
wrong systematic. The bandpass and phase-calibrator spectra that would settle
it are **not in the release**; QA2 per-channel flagging fractions likewise.

### M5. Exchangeability is not exact for continuum-detected stars

**Accepted.** §4.1 now carries the asymmetry, its scaling
(epsilon x S_cont at the star, essentially nothing on the annulus), the
statement that it is one-sided in the *unfavourable* direction and therefore
not covered by the existing primary-beam argument, and the numerical
requirement for CP-72 2713. The per-window continuum flux density at the
stellar position is **not carried by the release**, so we give the scaling and
the requirement and say explicitly that this is not a per-window bound.

### M6. The synthesised beam and array configuration appear nowhere

**Confirmed, and worse than "several rows".** From the obscore harvest in
`archive_meta_v343.json`: **38 of the 102 execution blocks and 141 of the 431
windows (33 per cent) are ACA 7 m**, while theta_PB is 1.22 lambda/12 m
throughout. Synthesised beams span 0.10 to 5.7 arcsec (median 0.84), and 133 of
the 431 windows have an inner annulus radius below the synthesised beam. The
effective independent spatial trials N_eff = pi(r_out^2 - r_in^2)/(1.133
theta_beam^2) span 36 to 1.4e5 with median 995 (ACA median 51), so the blanket
30 to 43 quoted in the text is the compact/ACA case only. Recomputing the
annulus geometry per array is **out of scope for a manuscript-only revision**
and is recorded as a stated limitation with these numbers attached. One
correction to the referee: of the four stage-1 flags only **one** (HD 48370
Band 6) is ACA; beta Pic Band 3, beta Pic Band 6 and CP-72 2713 Band 7 are all
12 m.

### M7 to M10

**M7** (variability as a survey-level confounder): the continuum anomaly
screen's lack of an intrinsic-variability term is already stated in Appendix H
and is retained verbatim; the survey-level treatment is **deferred**.
**M8** (astrophysical alternatives enumerated): partly met, through the SO /
34SO2 / U-line enumeration and the excitation argument above.
**M9** (a CO limit for CP-72 2713): **deferred**, the release does not carry
the per-window CO flux limit at the stellar position; the non-detection is
stated without a number, as before.
**M10** (beta Pic specifics): the velocity chain, both transitions and three
epochs are retained in full, per both R1's and R3's "must not be cut" lists.

---

## Referee 3 (general observational astrophysicist)

### 1. Put the result where a reader can find it

The Conclusions now open with one declarative sentence with no subordinate
clause: the public ALMA archive already holds a technosignature search of 88
stars within 40 pc over 93.1 GHz of unique sky frequency between 89.6 and
495.1 GHz, sensitive to channel-confined carriers above roughly 1e13 to 1e17 W
EIRP, and there is nothing in it. The "In plain terms" paragraph is kept where
it is and protected.

### 2. Two non-results occupy more space than the result

The CP-72 2713 subsection is rewritten and compressed while absorbing three
referee-requested additions, and the prose duplicates of Table 7 are deleted in
favour of a pointer to it. The AU Mic chronology and Table 9 are untouched, per
your own "must not be cut" list.

### 3. "Flagged windows" means two different things

**Accepted.** `\NSbr` and its relatives are renamed `\NRankFirst`,
`\RateRankFirst`, `\NRankFirstOld`, `\RateRankFirstOld`, and the quantity is
called a **rank-first window** throughout. Appendix J now states both pairs
with their gate in one sentence: counted *without* the 5 sigma amplitude gate,
65/431 become 5/431; counted *with* it, which is the stage-1 flag of the main
text, 7 become 4 (new macro `\NSpatialOld`). Appendix I's conflation is gone
with the paragraph removed under minor point 7.

### 4. Numbers that do not reconcile with the generated tables

All four corrected and macro-sourced:

- "66.6 GHz" -> `\UnionBandsFourEight` = **72.5 GHz**, recomputed as the
  interval union over Bands 4 to 8; the range "125-495 GHz" becomes the
  generated 142-495 GHz.
- Fig. 2's "7.6x" -> `\GrossOverUnion` = **7.7**, = 716.7/93.1, which is also
  the figure's own annotation.
- The beta Pic add-one denominator: replaced entirely by the symmetric-statistic
  calculation of R1-M8, which prints its denominator (432) explicitly.
- "Eighteen exoplanet hosts" -> `\NExoHosts`.
- `\EffBandGHz` is **retired** from both `make_numbers.py` (87) and
  `round9_calc.py` (renewed to 88.2); its three uses now take
  `\SearchedUnionGHz`, the single source.

### 5. Arecibo

**Accepted.** The Conclusions clause now reads "toward 1 of the 81 systems",
and the §5.3 benchmark sentence carries the same count. The two figure captions
label the position of a reference line and are left; the 230 GHz
frequency-matched benchmark remains the primary comparison.

### 6. The headline sensitivity is quoted bare

**Accepted.** The abstract now quotes the Hanning-corrected medians
(`\EirpHanMedA`, `\EirpHanMedB`) in the same clause as the nominal ranges.

### 7. W is not printed

See R1-M5. Printed, in channels and in frequency, for both classes.

### 8. Bespoke vocabulary

The standardised excess **zeta is deleted** (it decided nothing). The SP/SR
initialisms are written out and dropped. Table 1 is trimmed from 15 rows to 7:
crosswalk, QA2, ALMA-archive-complete, control ring, f_dwell and p_epoch are
removed and left to their definitions at first use.

### 9 and 12. Residual hedging and the length plan

We agree with your diagnosis that the remaining page is in duplicated content
rather than in sentences. Cuts taken, all repeats, never a first statement: the
archive-complete restatements in §1, §5.3 and §6.2; the rank-floor and
local-null restatements in §5.3; §5.3(iv)'s "Worked through" recap; the "three
levels stay distinct" restatement; §5.3(v)'s first two sentences; the
pseudo-star two-caveat paragraph and its N_eff restatement; the symmetric
region-max sub-subsection; §5.2's four-way argument reduced to two plus
direction; the polarisation paragraph; §5.5's integration-time audit; the
Conclusions' restatement of the future-work list; §6.3 merged into §6.4 as one
ranked list; Appendix I's withdrawn-statistic stratification; Appendix H's
detection list; and the CP-72 and beta Pic prose duplicates of their own tables.

Outcome: **main text 20.98 pages** (target 20), **appendices 6.76** (target 7),
total 29 pages, 28.99 measured against the 28.96 we started at. The main text is inside the 21.03 it started at and below 21 for the first
time, while absorbing about 1,400 words of referee-requested new material. We did not reach 20.0. The float ledger in `BUILD_NOTES.md` is
unchanged in its conclusion: below about 20.9 the binding constraint is float
placement, not prose, and the remaining page can only be bought by deleting
`fig:context`, `fig:cp72ctrl` or `fig:sens2d`, which we were instructed not to
do and which you also protect. We did take your Fig. 1 point in spirit on other floats: `fig:waterfall` is
reduced from 0.90 to 0.72 textwidth, `fig:noiseqa` from 0.64 to 0.56
columnwidth, `fig:completeness` from 0.88 to 0.78 and `fig:accel` from 0.72 to
0.62, in every case with that figure's label fonts enlarged by the same factor
in the generator so rendered legibility is unchanged (R1 m11's condition). **Fig. 1 panel (b) is left as it is**: at
`width=\columnwidth` the figure's height scales with its aspect ratio, so
narrowing panel (b) makes the figure *taller* on the page unless its height is
cut too, and the recoverable saving is about 20 pt rather than the 130 pt
estimated.

### 10. Prose

19 "X, not Y" antitheses converted to plain declaratives; 5 decorative italic
paragraph lead-ins deleted, including the three question-shaped ones you named,
with the parallel-list labels kept; 5 numeral-openers varied; §1 and §2 no
longer both open "Six decades". Em-dashes remain at zero.

### 11. The Introduction claims novelty for inoperative analyses

**Accepted.** The §1 claim is reduced to the three contributions the paper
defends (archive-complete selection, the control annulus with its local
false-alarm calibration, and the quantified search domain); the four further
diagnostics are named once as demonstrations that gate nothing, with the
continuum screen identified as the only one entering a disposition.

### Minor points

1. **115 vs 50 GHz.** Reconciled: both now derive from Wright et al.'s
   haystack frequency axis, whose upper limit is ~115 GHz.
2. **UV Ceti / G 272-61.** Standardised on "the UV Ceti pair".
3. **Scope item (iii).** "unconstrained" -> "only weakly constraining".
4. **Appendix F's stale "six".** Corrected: the crossing ledger is now stated
   once (20 crossing windows, 4 beat their ring, 3 of those accounted for by
   the mask, 2 further crossing windows inside the mask without beating their
   ring), and the rest cross-reference it.
5. **Fig. 1 panel (b).** See the length note above: left as it is, with the
   reason given.
6. **Fig. 2's cross-reference.** Fixed: the caption now points at
   Appendix K, where the in-band transmitter fractions live.
7. **Appendix I's withdrawn-statistic paragraph.** Compressed to one clause
   that labels itself a consistency check on a superseded quantity.
8. **Appendix I's best sentence.** Promoted to §5.3, where the flags are
   dispositioned.
9. **"control ring" vs "annulus".** The Table 1 row is gone with the trim;
   "ring maximum" is kept as the column name, with the annulus construction
   described in §4.1.
10. **"Per cent" vs "%".** **Not harmonised** in this pass; an OJAp house-style
    question for the author.
11 and 12. **Author-side items**, left flagged.
13. **HD 48370 Band 8's 5.05 sigma crossing.** The sentence now says
    explicitly that it is *not* one of the four stage-1 flags, because its own
    ring exceeds it.
14. **Table 5's punchline row.** **Not changed**; an author's typographic call.

---

## Deferred, with the reason

| Item | Why |
|---|---|
| R1-M2 star-vs-control residual variance; scramble null on the star's own residual | Release keeps 8 of 512 control spectra per flagged window |
| R1-m3 empirical-vs-theoretical rms for the six defective windows | `rms_theory_per_int_mJy` lives in `*_result.json`, not in this folder |
| R1-m7 four new catalogue columns | Requires regenerating the CSV against products not in this folder |
| R2-M2 the second CP-72 execution block | Handled by a separate job; not pre-empted here |
| R2-M3 time-domain tests on CP-72 2713 | Needs the retained dynamic spectra |
| R2-M4 QA2 edge-flagging fractions; calibrator spectra | Not in the release |
| R2-M5 per-window continuum flux at the stellar position | Not in the release; scaling argument given instead |
| R2-M6 recomputing theta_PB and the annulus per array | Requires re-running the extraction; recorded as a stated limitation with the measured numbers |
| R2-M9 a CO limit for CP-72 2713 | Not in the release |
| R3 minor 6, 10, 14 and the author TODOs | Cross-reference, house style and author calls |
