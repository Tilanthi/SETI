# Response to the second-round reports, v3.43 -> v3.44

White & Dey, *An ALMA Archival Search for Spectral Technosignatures toward
Stars within 40 pc*, for arXiv and the Open Journal of Astrophysics.

Reports answered: `v3.44_referee1_radio.md`, `v3.44_referee2_radiostars.md`,
`v3.44_referee3_general.md`, together with the priority findings in
`CYCLE2_PRIORITY_ARCHIVE_FINDINGS.md`.

**A note on how this letter is written.** Referee 3 checked the previous
letter's claims by counting, and found several of them overstated. This one
therefore says, for each point, **what was verified and how**, and marks
separately anything asserted but not independently checked. The measurements
at the end are from scripts in the release folder, not estimates.

---

## 1. Summary of the state

| gate | v3.43 (in) | v3.44 (out) |
|---|---|---|
| pages | 29 | **29** |
| main text / back matter / appendices / bibliography | 20.98 / 0.92 / 6.76 / 0.33 | **20.74 / 0.96 / 6.94 / 0.31** |
| total content | 28.99 pp | **28.95 pp** |
| LaTeX errors | 0 | **0** |
| undefined references or citations | 0 | **0** |
| multiply-defined labels | 0 | **0** |
| overfull / underfull boxes | 0 / 0 | **0 / 0** |
| Type 3 fonts | 0 | **0** |
| em-dashes in the source | 0 | **0** |
| unused generated macros | 31 of 129 round-13; 167 of 603 overall | **0 of 541** |
| arXiv set builds from an empty directory | 27 items | **26 items, 29 pages, 0 missing files** |
| figures with no generator in the folder | 2 | **0** |

The main text is **0.24 pages shorter** than it arrived and the page count is
unchanged, so the paper did not grow. It does not reach the author's 20.0
main-text target; §6 below says why, and what it would cost.

---

## 2. The blocking item: the archive audit now reaches the reader

All three referees raised this independently and it is the one thing that
stopped an accept. We agree with every part of it.

**Verified first.** Before editing anything, we recomputed the audit from
`archive_meta_v343.json` and the catalogue: the 102 searched member OUSs hold
**448** public execution blocks, of which **102** were searched (22.8 per cent)
and **346** were not; **75** of the 102 hold at least one unsearched block;
those supply **304** of the 431 windows (70.5 per cent) and **62** of the 88
stars; **62** stars have more public blocks available than were searched, up to
**34** available against at most **3** searched; and per system, **18** of 81
have a single available block against **63** with two or more. Every one of
those numbers reproduced. Referee 1 says six member OUSs hold ten or more
progenitor blocks; we count **seven** (11, 12, 23, 24, 25, 26, 34). Six hold
eleven or more.

**(a) §3 now carries the scope statement.** A new paragraph states that
archive-completeness holds *in targets and tunings, and not in epochs or
integration time*, gives all of the numbers above from
`\NMous`, `\NProgenitorEB`, `\PctEbSearched`, `\NUnsearchedEB`, `\NMousMulti`,
`\NWinMultiEB`, `\PctWinMultiEB`, `\NStarMultiEB`, `\MaxProgEBStar` and
`\MaxSearchedEBStar`, and names both causes: the per-target download budget
that caps blocks at three, and spectral-window de-duplication by identifier
across the blocks of one set. The abstract's first use of
"ALMA-archive-complete" now reads "complete in targets and tunings, though not
in epochs (§3)".

**(b) §6.2's claim is withdrawn.** It said "every held execution block in scope
was searched, so no EB-level selection lies behind the 102", followed by the
September 9 count of 107 on-star blocks. Both are gone. It now says that an
EB-level selection *does* lie behind the searched blocks, gives the datalink
count of 448 against 102, notes that the obscore service does not expose raw
progenitors (which is why the earlier audit could not see the selection), and
points at §3 for the cause and §6.3 for what searching them would buy.

**(c) §5.4 and Appendix J say *searched*, not *observed*.** §5.4 now reads
"Each star was *searched* in one to three execution blocks", with the count of
stars holding further public blocks. In Appendix J, $n_i$ is now introduced as
"a system *searched* in $n_i$ independent execution blocks", followed by the
archived multiplicity (63 systems with two or more blocks against 18 with one,
up to 34 available), and the statement that the bound is what the searched
epochs support. No number in the duty ladder is recomputed; only the label
changes, as referee 1 said.

**(d) CP−72 2713 no longer says a recurrence test is unavailable.** The
sentence "with a single searched execution block at this frequency no
recurrence test is available", and the telescope-time recommendation built on
it, are replaced. The subsection now names the member OUS
`uid://A001/X2d20/X2e25`, the unsearched block `uid___A002_Xff0235_X502d` at
49.5 GB against 49.3 GB for the searched one, states that it lies at the same
tuning and therefore covers 344.27 GHz, records that the per-target download
budget declined it, and rewrites the promote criterion to say that **that
archived block is the immediate test and no new telescope time is required**.
We have not claimed any result from it: the separate search job's outcome is
not in this revision, and the manuscript says only that the test exists and is
public. Referee 2's point that the asymmetric treatment of AU Mic was
conspicuous is taken; AU Mic's second epoch and CP−72 2713's are now described
in the same terms.

**(e) The unsearched blocks are now a ranked recommendation.** §6.3's list
gains a first item, *Search the blocks already held*: 346 of 448 blocks, no
telescope time, the tunings already searched, a multi-epoch survey for 62
stars, and the CP−72 2713 recurrence test among them.

---

## 3. Errors of fact and argument

**R1-N3, Appendix H's explanation of the 5σ cell excess.** The referee is
right: for marginally standard-normal cells E[number above 5σ] = *Np*
regardless of correlation, so channel adjacency cannot account for a factor
4.2 in the count. The paragraph is replaced with the referee's decomposition,
every number of which we reproduced from the catalogue and
`pipeline_peakfreq_v342.json`:

* summing $1-(1-2.87\times10^{-7})^{n_{\rm cells}}$ over the 431 windows
  predicts **10.9** windows with at least one on-star crossing against **16**
  observed excluding the four flags, a factor **1.5** at Poisson
  **p = 0.09**;
* within a crossing window the iid expectation is **1.2** cells against
  **3.4** observed, a factor **2.8**, and *that* is channel adjacency;
* 1.5 × 2.8 recovers the 4.2 already printed;
* the trials budget is almost entirely fine-class, **4.58e7** of 4.60e7 cells,
  so 10.9 chance crossings are expected among the 118 Class A windows against
  **0.03** among the 313 Class B ones, which is why all 20 crossings are fine
  windows. The paper previously reported that as a stratum departure without
  connecting it to the arithmetic.

The empirical calibration the referee asked for is now in, and it is a
positive result the paper was not claiming: the same arithmetic on each
window's 512 controls predicts **134** of 431 windows carrying a control above
5σ and **125** do, agreeing to **7 per cent**; and the observed per-window
control maxima track the iid-Gaussian prediction at a median ratio of
**0.995** (5th–95th percentile 0.91–1.12), separately in both classes, fine
5.77 against 5.71 and coarse 4.41 against 4.47. One note on reproducing this:
the convention that gives 0.995 is the **median** of the maximum of *N* iid
standard normals, $\Phi^{-1}(0.5^{1/N})$; $\Phi^{-1}(1-1/N)$ gives 1.009. The
residual window-level factor 1.5 at the star against 0.93 at the controls is
stated as the closest measurement of position-specific excess at the phase
centre the release affords, marginal, and dominated by CO(2→1) toward disc
hosts.

**R1-N4, the baseline node.** Confirmed, and the referee's numbers are right.
With the pipeline's own `nb = max(2, n // 65)` on this window's 3534 channels,
nb = 54, the block width is 65.4 channels and the first node is a block
*centre* at channel **32.7**, so the crossing at channel 35 sits **2.3**
channels beyond it, not 30 channels from a node at 65. The text now says so,
adds that the baseline is held flat at the first block median below that node
and that channel 35 is just past the transition, and keeps the referee's point
that the corrected numbers sharpen the caveat.

**R2-N2, the CO argument.** Accepted in full; this was the second most
consequential item. Verified against Moór et al. (2020) and the shipped
products: the belt's peak radius of 140 au is **3.8 arcsec** at 36.72 pc; the
flagged Band 7 window is 47 × 12 m with a **0.61 arcsec** beam, so a stellar
extraction is six beams from the belt; the belt lies inside that window's
control annulus, which spans **94–522 au**; and the belt-appropriate window is
the Band 6 CO(2→1) one, 9 × 7 m with a **5.71 arcsec** (210 au) beam that holds
the whole belt. The limits reproduce the referee's arithmetic exactly from the
shipped `rms_mJy`, at 3σ matched-width over an assumed 4 km/s double-peaked
width and optically thin LTE: **CO(2→1) < 84 mJy km/s**, **M_CO < 1.6×10^19 kg
at 20 K and 2.4×10^19 kg at 50 K** (2.7–4.0 × 10^-6 M_Earth), and
**CO(3→2) < 8.2 mJy km/s** at the stellar position alone. All of this is now
in the text, with the assumptions named, and with the ring statement the
referee asked for: belt CO(3→2) would raise individual controls as HD 48370's
13CO ring does at 26.8, and no control in that window reaches beyond 5.68. The
filter clause is in too: 65 channels at 488 kHz is 32 MHz, 28 km/s at Band 7,
so a belt line sits inside the flat region and the non-detection is not a
filter artefact. The Galactic coordinates are now quoted (l = 315.9,
b = −42.0) instead of "far from the Galactic plane".

**R2-N1, the excitation argument.** Correct, and corrected. `linecat_v343.json`
gives U-344288.4 `eu: 0.0`, `chem: UNIDENTIFIED`, `linelist: Lovas`. The text
now says excitation disposes of the **two identified** entries, and that the
third has no carrier and no upper-state energy to violate. **What we could not
do:** recover the U-line's provenance. Splatalogue is not reachable from the
machine this revision was prepared on and the shipped query product carries no
source field, so the referee's preferred repair, naming the astronomical
spectrum the entry was reported toward, is not available to us. We took the
fallback the referee offered and say plainly that the shipped product carries
no provenance for it.

Rather than leave the nearest entry undisposed, we added the argument the
referee's own M8 asked for, which disposes of all three and of a background
emitter besides: the feature occupies **one 488 kHz channel, 0.42 km/s**,
whereas a Keplerian belt at 140 au around a ~0.6 M_sun star spans ~4 km/s
(about ten channels), a hydrogen recombination line would be broader still, and
an extragalactic CO line would span ≳50 km/s.

**R3-E, the single-source rule.** `\UnionBandThree` = 20.6 and a new generated
`\UnionBandThreeFrac` = 0.18 replace the two hand-typed digits in §6.2;
`\EdgeChanMin` = 35 replaces the hand-typed "channel 35"; Data Availability
names `per_target_results_v3.44.csv`, which is byte-identical to the v3.42 and
v3.43 files and is the one the release now ships. The full sweep is §5 below.
**Not closed:** "17 of 57 target/bands", "forty ancillary continuum
measurements" and "median 0.52 mJy" remain hand-typed. There is no continuum
product in the release folder to generate them from, so we could not source
them and say so rather than leaving the impression that we did.

**R3-B, the one-sentence result.** Taken verbatim: the Conclusions now open
"...raising a 5σ trigger at powers of roughly 10^13 to 10^17 W EIRP, and there
is nothing there", which no longer contradicts the boxed rule.

**R3-F, N_eff.** §4.1 now says 30–43 is the compact-configuration case and
gives the archive-derived median of 995 with a pointer to Appendix H, so a
reader meeting the number in the methods learns immediately that it is a floor.

**R2-N5, the third "ancillary result in full".** There is no appendix for the
serendipitous line catalogue and the `\ref` pointed at the continuum lane. §5.5
now advertises two results in full and says the third ships with the data, and
the pointer is gone. On the 300 MHz claim: the by-product is generated by the
line-exclusion step, which compares against the 17-transition mask, so the text
now says "no *masked* transition within 300 MHz", names the mask as the list
the claim was made against, and points at the 19-of-20 catalogue finding so the
reader is not left to assume otherwise. We did not re-run the scan.

**R1-N6, Figure 2.** Three defects, all repaired in `make_figures_v328.py` and
verified by reading the built page at 200 dpi and the figure's own text layer:
the legend's `$<$5\,MHz` passed a literal backslash to matplotlib and now reads
"($<5$ MHz channels)"; the 81 row labels collided at 0.72\textwidth, and every
row now keeps its label with alternate rows set on a secondary right-hand axis,
which doubles the space each label has without enlarging the figure or dropping
any system; and the row labels are set as the text sets the same objects
(α CMa B, β Pic, χ¹ Ori, γ Lep, Barnard's Star).

---

## 4. Everything else, point by point

**Referee 1.** N5, the scramble null on the star's own residual: **run, and it
is in.** The value is p = 2.0×10⁻³ against 1.6×10⁻³ on a control, printed side
by side in §5.3. See the disclosure in §5 below about where that number comes
from. N7, ACA geometry: both consequences are in Appendix H and both were
recomputed here. The ACA annuli span 0.08–0.46 of the *true* primary beam at a
median area-weighted gain of **0.75** against **0.47** for the 12 m windows, so
exchangeability in flux is better there; and of the 41 windows with a
primary-beam correction above 2 per cent, **36 are 12 m and 5 are 7 m**, with
all four at the ×1.81 maximum 12 m, so the applied correction is overstated
only for the five ACA rows, where the 1.71× dish-diameter ratio makes a ×1.05
correction really ×1.017. m1, W = 65–74 against 65–73: **not changed**, because
we could not settle it from the folder. The generator computes W = n/nb from
the pipeline's own trimmed channel count and prints the rounded range; the
referee's 65–73 comes from a channel count that differs from the pipeline's by
one in some windows. Flagged rather than silently altered. m2: "across 6 stars"
now reads "across 6 catalogue entries (five designations: the two HD 139084B
rows share one)". m3: §3 now states that the 431 rows are **396** distinct
(execution block, spectral window) datasets and points forward to where 431 is
used as the trials denominator, noting that the larger number is conservative.
We did not check whether a co-observed star falls inside a neighbour's control
annulus; that needs the per-probe positions, which the release does not carry.
m4: the compounded worst case is now a parenthesis in Appendix A, **×4.6**.
m5, em-dashes: noted and obeyed, see §5.

**Referee 2.** M3, the time axis: the claim that time splits need re-extraction
was **false for time** and is corrected. The split-half is now reported
(T★ = 3.08 and 5.12 against 4.11 expected, a 1.4σ difference, so a flare is
excluded), and the sentence now defers only polarisation, baselines, the
visibility domain and the calibrator comparison. M4 residual: the survey-wide
edge-proximity distribution is published, 32 of 490 recorded peak channels in
the outer 3 per cent. M6 residual: the HD 48370 13CO offsets are now given in
beams, 1.7 and 1.3–2.0 for the ten strongest against that window's 5.55 arcsec
beam, with the text saying "resolved away from the star by a beam or two and
not by tens". M8 residual: the width argument above covers the extragalactic
emitter and the recombination line. N4, stellar emission as a survey-level
confounder: four sentences at the head of the disposition discussion, saying
that the block-median baseline removes anything broader than ~32 MHz (a
fractional bandwidth of ~10⁻⁴) while MacGregor et al. (2020)'s AU Mic flares
are coherent across 8 GHz, that flares are also time-confined and so suppressed
twice, that what survives is the multiplicative route already bounded in §4.1,
and that the search is blind to the time axis by construction. The CP−72 2713
subsection then measures it: per-integration continuum at the star
0.07 ± 0.06 mJy (3σ < 0.17 mJy) against AU Mic's 6.1 and 16.8 mJy flares, so
that route needs ε ≈ 70. M7's §1/§5.5 contradiction is resolved in §5.5's
favour: no ancillary analysis carries a technosignature disposition, and §1 now
says the continuum screen feeds an argument in the primary lane rather than
entering a disposition. Minors 1 (the abstract says 0.50 per cent, the searched
sample, not ~1 per cent, which belongs to the census; the same correction in
the Conclusions), 2 ("at most ×3.7, ×3.1" and "at least ×0.6"), 3 (the sign
convention in both captions is now "as c Δν/ν_rest, positive when the observed
frequency exceeds the rest frequency") and 8 (Appendix E now says *masked*
transition) are done. **Not done:** M10's three β Pic specifics, minor 4
(Table 9's hand-typed values), minor 5 (χ¹ Ori variability, the LSR J1835+3259
flux in the main text), minor 6 (Band 8 [C I] limits) and minor 7 (promoting
the tuned-line rule out of Appendix E). Minor 6 is computable from the shipped
catalogue and we agree it is worth having; it did not fit the page budget this
round, and we would rather say so than claim it.

**Referee 3.** A, B, E and F are in §3 above. C, the antithesis: **13
conversions this round, and we give the honest count** in §6. D: we have not
reduced any figure width further, per the referee's warning, and the page this
round was bought from floats the referees themselves priced. Minor 1: the
honesty paragraph is moved to the end of §1, after the contributions, where the
referee asked for it, and it stays in §1. Minor 2: the first of the two σ
statements is deleted, the second develops it. Minor 3: the generator no longer
emits a spaced double hyphen inside Fig. 1. Minor 5: **both missing generators
are written**, see §5. Minor 6: `tab_smear.tex` and the annulus-geometry
fragment are now named in Data Availability as released products. Minor 7: one
of the two UV Ceti statements is gone. Minor 8: Appendix D's prose is folded.
Minor 9: the `\end{table}` followed by running text was in `tab:ring`, which
this round deletes, so it is gone. Minor 10: see the hand-typed continuum
numbers above. Minor 11: the author items are left in place and flagged again.

---

## 5. Disclosures

**Numbers we did not derive in this revision.** Four measurements on the
CP−72 2713 dynamic spectrum close referee 1's M2 and N5 and referee 2's M3 and
N4: the star's residual variance at 1.006 times the control median, the local
null on the star's own residual at p = 2.0×10⁻³, the split-half statistics, and
the per-integration continuum. The `*_srcspec.npz` products they are computed
from are **not in the release folder**, so this revision could not re-derive
them; they are carried from the cycle-1 verification run and are recorded, with
that provenance stated in the file, as a frozen input `cp72_checks_v344.json`
that the generator reads, rather than hand-typed into the manuscript. Data
Availability now lists the retained dynamic spectra as products held on the
processing host.

**Unused-macro sweep.** `macrosweep.py` on the incoming manuscript reproduced
referee 3's count exactly: **31 of the 129 round-13 macros unused**, and 167 of
603 across all ten generated files. Twenty-three of the 31 are now used in the
text; 14 round-13 spares are retired at source in `v343_calc.py`; and a new
last step in `make_all.sh`, `retire_macros.py`, removes from the generated
files every `\newcommand` that no `.tex` in the folder references, recording
what it removed in a comment in each file and refusing to touch a referenced
one. The generators still compute the quantities. **The sweep now reports 541
macros defined and 0 unused**, and the built PDF's text layer is byte-identical
before and after the retirement, so nothing a reader sees moved.

**Figure generators.** `make_fig_missing_v344.py` is new and rebuilds
`cp72_control_distribution.pdf` from `localnull_code/ctrlmax.json` and the
catalogue, and `sensitivity_2d.pdf` from the catalogue, at the shipped canvas
sizes. Both reproduce the figures they replace: the histogram's 32 bars and its
two marked values, and all 431 points with the same class split, markers,
colours, band markers and labels. Every figure in the upload set now has a
script behind it.

**Em-dashes.** Zero in the source. The built PDF's text layer contains
**seven**, one per figure caption, and they are `openjournal.cls`'s own
"Fig. n.—" separator. The count fell from eight only because one figure was
deleted. Both referees who raised this asked that they not be "fixed"; they
have not been, and BUILD_NOTES records why for the next pass.

**Two defects fixed in passing.** The bibliography filed Dent et al. (2014)
after Matrà et al. (2017) and Pickett et al. (1998) after Vidal et al. (2026);
both are now in place.

---

## 6. Length, measured honestly

Referee 3 found last round's compression claims overstated, so this round's are
measured with one script (`worddiff.py`) run on both sides, and reported
whichever way they fall.

**Word-level diff of the source, `.tex` to `.tex`:**

| region | old | new | deleted | inserted | **net** |
|---|---:|---:|---:|---:|---:|
| main text | 18,169 | 18,519 | 1,037 | 1,387 | **+350** |
| appendices | 5,251 | 5,486 | 249 | 484 | **+235** |
| whole | 23,420 | 24,005 | 1,286 | 1,871 | **+585** |

**Rendered-text diff of the built PDFs:** 26,198 tokens to 26,668; 4,239
deleted, 4,709 inserted, **net +470**.

So the paper gained about 500 words. We are not going to describe that as
compression. The page count held at 29, and the main text fell 20.98 to
**20.74**, because the room was bought from **floats the referees priced
themselves**: `fig:noiseqa` (222 pt, referee 1's item 1, whose two numbers the
referee verified without the plot) and `tab:ring` (127 pt, item 2, whose
per-window content is six columns of the released catalogue) are deleted and
ship with the data. Table 1 lost the two rows whose terms are defined at first
use. Everything else on the referees' lists that we took is prose: the Hanning
restatements in §4 and the Conclusions, the §6.2 transfer restatement, four
rank-floor restatements, §5.2's duplicate-row closing sentences, §6.2's
bandwidth and sensitivity clauses, §6.3's "strengths and mirrors" preamble,
§4.2's re-derivation of the channel-dilution algebra, §4.1's first σ statement,
three components of §5.3's false-alarm calibration, Appendix D's prose, 13
antithesis conversions, and tightening in Appendices A, C, H, I and J.

**Not taken: referee 1's item 3, merging the two boxed rules (~120 pt).** Both
boxes are on referee 2's must-not-cut list in full, they sit in different
sections doing different jobs, and the page budget did not require a structural
edit of protected text. Reported rather than done.

**The 20.0 target is not reached, at 20.74.** Referee 3's own plan reached
about 20.2 and said so; ours reached 20.74 while absorbing about 500 words of
new referee-requested evidence. The remaining three quarters of a page is the
CP−72 2713 apparatus, and referee 3 is right that the way to it is to search
the second execution block: if the feature does not recur, the subsection, its
table and `fig:cp72ctrl` collapse together. That search is running separately
and its result is not in this revision.

---

## 7. What we could not verify

* The Lovas U-line's provenance (referee 2, N1). Splatalogue is unreachable
  from here and the shipped product carries no source field.
* W = 65–73 against the printed 65–74 (referee 1, m1). The two channel counts
  differ; we left the generated value and flagged it.
* Whether any co-observed star falls inside a neighbour's control annulus
  (referee 1, m3). The release does not carry per-probe positions.
* The four CP−72 2713 dynamic-spectrum measurements, which are carried from the
  cycle-1 log rather than re-derived; see §5.
* The hand-typed continuum-lane counts (referee 3, minor 10). No continuum
  product ships in the folder.

## 8. Author items, unchanged and flagged again

The Data Availability TODO still instructs tagging `submitted-v3.32` against a
later catalogue, now `per_target_results_v3.44.csv`; the VBRL affiliation
wording; the arXiv identifier and status of White (2026); and the repository
tag and Zenodo DOI. None is resolved here.
