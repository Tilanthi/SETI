# v3.46 — independent verification of the brief's new numbers

**Author:** `astra-pa` (second, concurrent v3.46 run). **Date:** 2026-09-12 06:45 UTC.

I was asked to verify the brief's new results against the retained products before
writing them. I did. **Three of them do not reproduce.** A concurrent run is editing
`/workspace/SETI/paper_20pc/v3.46/technosignatures_20pc_v3.46.tex` and has already
generated `survey_numbers_bprec.tex` and `survey_numbers_pointing.tex` carrying the
brief's figures; the corrections below should be applied there.

Everything below is read out of the unmodified pipeline's own result files on the
processing host (read-only, `nice -n 19`), or recomputed from the frozen release.
Provenance files, all in the v3.46 folder:
`bpic_epochs_v346.json`, `epoch_extension_v346.json`, `driver_summary_v346.json`,
`untried_eb_audit_v346.json`; generator `v346_calc.py` -> `survey_numbers_round15.tex`.

---

## 1. WRONG: the beta Pic B3 frequency agreement is 0.27 MHz, not 0.13 MHz

The brief (and `survey_numbers_bprec.tex`, `\BpRecThreeDv{0.34}`) says the B3 pair
agrees to **0.13 MHz = 0.34 km/s**. The products say otherwise.

| | epoch 1 (published) | second block | difference |
|---|---|---|---|
| EB | `A002_Xf5d76d_X32f1` | `A002_Xf5d76d_Xcc5` | |
| `star_peak_freq_GHz` | 115.26064369 | 115.26037213 | **0.2716 MHz** |
| in velocity at 115.26 GHz | | | **0.71 km/s** |
| in channels (244.14 kHz) | | | **1.11** |

`0.13 MHz = 0.34 km/s` is internally consistent, so it is a real quantity of
something, but it is not the separation between the two peak frequencies in the
released products. The defensible statement is: **the two epochs' peak frequencies
agree to 1.1 channels (0.27 MHz, 0.71 km/s).**

The B6 pair does reproduce exactly: 230.52813436 vs 230.52718495 GHz =
**0.949 MHz = 1.23 km/s = 3.9 channels** (brief: 0.95 MHz, 1.3 km/s).

**A second, load-bearing correction.** The brief calls the B3 second block a "new
epoch". It is **0.94 days EARLIER** than the published one (2022-03-02T23:20:42Z
against 2022-03-03T21:49:25Z). Describe them as two independent execution blocks,
not as a later epoch. The B6 pair is +25.13 d (2013-10-06 and 2013-10-31).

**The barycentric argument only applies to the B6 pair.** Computed here with astropy
for the ALMA site and beta Pic: the barycentric velocity difference is **-2.196 km/s**
between the two B6 dates (the brief's 2.2 km/s, confirmed independently), and the
observed shift is in the same sense. But between the two B3 dates it is only
**0.08 km/s**, so it explains nothing there; the B3 agreement is a
channel-quantisation statement, and should be written as one.

## 2. WRONG: "the same resolved width (24 and 28 channels above threshold)"

24 and 28 are the **second** blocks' `n_hits_above_threshold`. The published epochs
give **17** (B3) and **32** (B6). Both pairs are resolved, many channels wide, which
is the point; but the two numbers are not a matched pair and must not be presented as
one. Both blocks in both pairs carry `detection = true`.

Integrated line flux, which is the stronger recurrence statement and is matched:

| pair | epoch 1 | second block | difference |
|---|---|---|---|
| B3 CO(1-0) | 68 +- 6 mJy MHz | 77 +- 9 | **+0.8 sigma** |
| B6 CO(2-1) | 984 +- 88 | 911 +- 69 | **-0.7 sigma** |

The B6 pair is an exact configuration match (244.14 kHz, 3770 channels), as the brief
says. The B3 pair is also 244.14 kHz / 3534 channels.

**One more accuracy point on the control pair.** Of the four stage-1 windows, the one
that recurs is **beta Pic B3** (115.260644 GHz). The **beta Pic B6 stage-1 window is
at 230.516128 GHz (`A002_Xd9668b_X3a90`, T\* = 11.68) and has no second block
searched**. The B6 recurrence reported here belongs to the *other* beta Pic Band 6
window, 230.528134 GHz in MOUS `uid://A002/X5a9a13/X58b`, which is a crossing but
**not** one of the four stage-1 outliers. Writing "the two beta Pic flags recur"
would be false.

## 3. WRONG: the retry programme is not "0 successes in 38 attempts"

From `/data/SETI/logs/driver_summary_master20pc.json` (md5 `e795df50...`, mtime
2026-09-12T04:46:54Z, the same snapshot the audit used): re-attempts of previously
failed target-bands run from 2026-09-11T11:38:50Z to 2026-09-12T04:46:54Z.

**39 attempts, 1 success, 38 failures.** The success is **AU Mic [B9]**, rc = 0,
7786.6 s, finished 2026-09-11T19:51:47Z. The summary now stands at 140 ok / 68 failed
of 208 attempted, against 139/69 before the retry pass, which is the same one
recovery seen from the other side.

"0 successes in 38 attempts" is what you get by counting the 38 failures as the
attempts. AU Mic Band 9 is outside the paper's Bands 3-8 and outside the frozen
release, so it changes no count in the paper, but the sentence must not say zero.

## 4. Check: the pointing separations

`survey_numbers_pointing.tex` carries `\SepMedianDeg{1.4}` and `\SepMaxArc{8\,777}`.
Recomputed from `untried_eb_audit.json`, taking the nearest field centre over all
candidate member OUS of each failed target-band (one number per target-band, n = 60):

* minimum **250"**, maximum **8205"**, median **5603" = 1.6 deg**.
* Taking instead one number per candidate MOUS (n = 71) gives median **5699" = 1.6 deg**,
  which is the figure in the audit document.

Neither route gives 1.4 deg or 8777". Whoever owns `pointing_calc.py` should re-derive.
Both routes agree on the two facts the paper needs: nothing between 5.8" and 250",
and a median near 1.6 degrees.

## 5. Confirmed, and worth using: the selection chain closes exactly

The brief asks for 17,566 -> 168 -> 88 -> 81. It reconciles completely, and the audit
adds a term that improves the paper:

    17,566  Gaia DR3 stars within 40 pc (sigma_parallax/parallax <= 10 per cent)
       168  admitted as having qualifying public ALMA coverage at the snapshot
        88  searched to completion in the frozen release, in 81 systems

Of the 80 not searched here, **53 are stars ALMA never observed**: their entire
claim to coverage is an `s_fov` reported for an ephemeris or solar delivery. All 54
distinct not-pointed stars are entries of the 168 (verified by designation match);
exactly one of them, Wolf 28, is also in the searched 88 through a different band.
The remaining 28 are genuinely pointed at and sit outside this frozen release.
53 + 28 + 87 = 168, with one searched star (HD 139664) carrying a designation not in
the 168-entry list.

So the honest denominator for "how much of the covered sample did we search" is
**88 of about 115**, not 88 of 168.

## 6. Confirmed: the three-block cap caused nothing

Independently recomputed from the audit JSON: 14 of the 68 failed target-bands have
untried blocks carrying calibration products, and in **0** of them did the tried
blocks lack them. The hypothesis returns 0 of 68.

## 7. New, and it answers referee B4 quantitatively

Referee B asks for retained-window sigma against an SEFD-based prediction, with the
residuals shown to be well behaved. Computed here for all 431 retained windows, using
`q = sigma sqrt(t_on dnu_ch)` against `SEFD_band / sqrt(N_bl)` with the antenna count
and array of each execution block from `archive_meta_v343.json`:

* residuals unimodal, median 0.76 dex, 16-84 per cent **0.59 to 0.95** (a factor 2.3),
  **98.4 per cent within half a decade of the median**, largest empty interval inside
  the body of the distribution **0.04 dex**;
* full retained range 0.39 to 1.73 dex;
* the six defective windows sit at **-3.05 to -2.66 dex**, i.e. **3.0 dex below the
  lowest retained window**, with nothing in between.

So the gap-based exclusion is not an artefact of the cut: there is no continuum of
smaller deflations among the retained sample.

And the metadata referee B4 asks for: the six defective windows are **all 12 m**
(none ACA), all at **15.6 MHz** channel width, spread over **5 execution blocks in 4
projects**, so they share a correlator mode and an array but not a proposal.

## 8. Confirmed: the statistic-revision chronology, with hashes

Resolved against `Tilanthi/SETI` through the GitHub API:

| commit | committed (UTC) | what |
|---|---|---|
| `157f92c08d` | 2026-09-09T15:45:28Z | `v3.24/figures/aumic_control_maxima.pdf` |
| `aff669e29d` | 2026-09-09T15:45:30Z | the same figure as PNG |
| `0c465f2661` | 2026-09-09T16:14:07Z | v3.25, "adopt the symmetric ..." |
| `bfe7d277f1` | 2026-09-09T17:02:17Z | v3.26, same series |

The v3.24 manuscript (`9e4fd72751`, 2026-09-09T15:39:59Z) still carries AU Mic as one
of three candidates. The v3.25 manuscript states "The AU~Mic crossing of earlier
versions fails the symmetric test and is no longer counted."

**So the redesign demonstrably postdates the flag**, by about half an hour of
committed record. Referee B is right, and the paper should say so plainly rather than
implying the reverse; the algebraic argument then has to carry the weight, which is
exactly what referee B invites.

## 9. Not verified, stated as such

* I did not attempt to reproduce the 0.13 MHz figure from any other quantity, so I
  cannot say what it is a measurement of.
* `survey_numbers_bprec.tex`'s `\BpRecChanThree`/`\BpRecChanSix` I have matched to
  `n_hits_above_threshold` in the second blocks; if they were meant as something else,
  the generator should say so.
* The 8.1 GB Cycle 0 question for G29-38 (V\* ZZ Psc) is still unsettled, and
  LP 722-21 was still calibrating on the host at 06:37 UTC. Nothing about either
  belongs in the paper yet.

---

## 10. Addendum: referee claims checked against the manuscript and the products

**Referee B6's 1.07 m s$^{-2}$ is TRAPPIST-1 d, not TRAPPIST-1 b.** The paper's own
macros give 1.07 (d), 2.14 (c) and **4.00** (b) m s$^{-2}$, against a searched ceiling
of 3.6-4.0 m s$^{-2}$. So TRAPPIST-1 b sits exactly *at* the ceiling, which is a
sharper statement than the referee's and is already in the Discussion ("only
TRAPPIST-1 b reaches the drift ceiling"; "TRAPPIST-1 b, at 1.51 d, sits just inside
the [curvature] boundary and is also the case exceeding the drift ceiling"). The
abstract caveat the referee asks for is worth adding; the referee's number is not.

**Referee A4's 717 GHz is right.** Recomputed from the frozen export, the summed
window bandwidth over the 431 retained windows is **717 GHz** against a 93.1 GHz
union, i.e. the paper's own `\GrossOverUnion` of 7.7.

**Referee A3's Table 4 error is real.** `tab:searchspace` row 1 reads
"Census stars within 40\,pc & `\NCensus`" with `\NCensus` = 168, while `tab:selfunc`
uses 17,566 for the reference census. Both referee readings of the row are available
to a reader, and the percentages differ by a factor of 100.

**Referee A11 / B2's arithmetic is right.** 1/513 = 1.95e-3; Bonferroni at
0.05/431 = 1.16e-4, the paper's 1.2e-4. For a 5 sigma-equivalent single-window rank
resolution the control ensemble needs 1/2.87e-7 = **3.5e6** positions (the referee's
"about 3e6"), which is the number I would print.

**Referee B5's polarisation point is already in the manuscript in full**, including
the sqrt(2) worst case and the statement that the retained products cannot say which
datasets lost a hand. What is new is the request to put it in the abstract.

**Referee B1's "promote the audit table" may already be satisfied.** `tab:bothstats`,
the both-statistics audit of all seven originally flagged windows, is in the main text
(inside \S "Changing the detection statistic, and the AU Mic crossing"), not in an
appendix. Worth saying so in the response rather than moving anything.

---

## 11. NEW since the brief was written: the beta Pic B3 flag now has THREE blocks

A third execution block of the same member observing unit, `A002_Xf5d76d_Xe19`,
finished on the host at **2026-09-12T06:35:04Z**, after the brief was issued. Read out
of its own `result.json`:

| block | T\* | peak (GHz) | channels above threshold | ring max | detection |
|---|---|---|---|---|---|
| `A002_Xf5d76d_X32f1` (published) | 14.65 | 115.260644 | 17 | 7.27 | yes |
| `A002_Xf5d76d_Xcc5` | 17.29 | 115.260372 | 24 | 5.52 | yes |
| `A002_Xf5d76d_Xe19` | **27.68** | 115.260345 | 24 | 6.48 | yes |

All three are detections, all three have zero of 512 controls at or above the star,
and the three peak frequencies span **0.30 MHz = 1.2 channels** in total. The third
block is also the deepest (combined rms 2.65 mJy against 3.70 and 4.68).

This is a considerably stronger positive control than the two-block version in the
brief: the CO feature repeats in three independent blocks at a fixed frequency, while
CP-72 2713's feature is absent in its second block at the matched frequency and drift.
A fourth block, `A002_Xf5d76d_Xeb8`, was calibrating at 06:35Z.

`bpic_epochs_v346.json` in the v3.46 folder now carries all five blocks (three B3, two
B6) with provenance, and `v346_calc.py` emits `\BpRecThreeTList{14.65, 17.29, 27.68}`,
`\BpRecThreeSpreadMHz{0.30}`, `\BpRecThreeSpreadChan{1.2}`,
`\BpRecThreeHitsList{17, 24, 24}` and `\BpRecThreeNBlocks{3}`.

**Consequence for \S sample:** the manuscript sentence "One unsearched block has since
been searched, as the second-epoch test" is now **four** (CP-72 2713's, two beta Pic
B3 and one beta Pic B6), out of the 346 unsearched blocks. That sentence needs
updating whichever run owns the file.

---

## 12. What is actually in the manuscript right now (checked 06:50 UTC)

The concurrent run has already written the recurrence passage. Two of my points bite,
one does not, and I withdraw it.

**WITHDRAWN.** "Both remain resolved, with 24 and 28 channels above threshold" is
correct as written: it refers to the re-searched blocks, and 24 and 28 are their
values. My earlier note read it as a claim about both epochs. It is not.

**STANDS, and it is now printed:** "at a frequency agreeing to `\BpRecThreeDv` km/s"
prints **0.34**. The products give **0.71** km/s (0.27 MHz, 1.1 channels).

**STANDS, and it is the more serious of the two:** the passage opens "The two
$\beta$~Pic windows attributed to circumstellar CO were re-searched in independent
archival blocks." The Band 6 window that was re-searched is **230.528 GHz in MOUS
`uid://A002/X5a9a13/X58b`, T\* = 10.16**. The Band 6 window in `tab:flagged` is
**230.516 GHz in MOUS `uid://A001/X133d/Xbb5`, T\* = 11.68**, and no second block of
it has been searched. So the sentence identifies the wrong window, and the paper now
contradicts its own Table 5: the text says "9.95 against 10.16 in the first epoch"
while the table gives 11.68 for the flagged Band 6 window. A referee who checks the
two against each other will find it.

The honest version is available and is no weaker: the Band 3 stage-1 outlier recurs in
two further blocks, and a second $\beta$~Pic Band 6 CO crossing, not itself a stage-1
outlier, also recurs. Suggested wording in `DRAFT_TEXT_astra-pa.md`, section A.

---

## 13. Reconciliation with the parallel evidence run, and one correction to me

`/shared/ASTRA/reviews/v3.46_evidence_bpic.md` reached the same three verdicts
independently (0.27 MHz not 0.13; the recurring B6 window is not a stage-1 outlier; the
"24 and 28" attribution), which is the cross-check both of us should want. It also
**corrects me on the barycentric argument**, and it is right.

I wrote that the B6 residual is "in the same sense as, and of comparable size to" the
2.2 km/s barycentric difference. That inference is not valid. ALMA Doppler-sets the
spectral window per date, so the barycentric term is already in the tuning: predicted
shift 1.6843 MHz, measured difference in the window tuning 1.6818 MHz, agreeing to
2.5 kHz. Corrected for the tuning the two B6 drift-search peaks differ by exactly three
channels and the two line-profile peaks by exactly one, and the B3 peaks by exactly one.

The statement that should be printed instead is frame-free and much stronger: converted
to the barycentric frame the CO peaks of four independent blocks, two bands, two
transitions, nine years apart, all land within 0.8 km/s of beta Pic's systemic velocity.

`DRAFT_TEXT_astra-pa.md` section A has been rewritten accordingly. Also noted from
`v3.46_MANDATORY_CORRECTIONS.md`: the 0.13 MHz figure came from differencing against the
table's **rounded** 115.2605 GHz rather than the full-precision export column, which is
the same failure mode as the earlier CO rest-frequency episode.

My SEFD work and `/shared/ASTRA/reviews/evidence_task2_noise.md` also agree
independently where they overlap: unimodal retained residuals and an empty gap of
**3.0 dex** (mine) against **3.09 dex** (theirs) between the retained sample and the six
defective windows, computed with different normalisations. Their pack goes further and
identifies the mechanism (auxiliary TDM windows on an uncalibrated amplitude scale), so
theirs is the one to cite in the manuscript; mine stands as an independent check of the
gap and of the unimodality.
