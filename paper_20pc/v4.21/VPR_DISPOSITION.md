# Virtual peer review — dispositions

Five rounds, each report written by an independent reviewer pass and then
verified by me against the released catalogue before any edit. Reviewer
claims that turned out to be wrong are recorded as such, not silently
dropped.

## Round 1 — internal consistency and arithmetic

Report: `VPR_ROUND1.md`. 34 MAJOR + 37 MINOR raised. I verified each
against `per_target_results_v3.85.csv` and the macro set before acting.

### Real, and fixed

| ID | What was wrong | Fix |
|---|---|---|
| **C1** | Polarisation census covered **104 of 404** blocks and was typeset as "all of them" | `polstates_v385.py` re-queries all 404 via obscore `asdm_uid` (200 resolve; `obs_id` returns nothing, which is how the old query had been silently narrow). **198 of 200 deliver both hands, 2 do not** — 8 Class B windows toward $\tau$ Ceti. Old macros retired at source. |
| **C2** | "75 crossings (all Class A)" | 71 A + 4 B, from derived macros |
| **C3** | Drift ceilings "1.1–5.9 kHz s⁻¹" | 1.1–10.5, derived; the Band 9/10 windows had moved the maximum |
| **C4** | Table 10's caption said the visibility test had **not** been run | it had; caption corrected |
| **C5** | CP−72 2713 reported at **2.3σ** (Table 9) and **5.5σ** (App. G.5) from the same 405,860 visibilities | Both are right and they are different estimators. `visdilute_v385.py` quantifies it: the uniform single-channel test loses a drifting carrier by up to ×4.8, the tracks sweep 4–23 channels, and the observed ratio ×2.4 is what a 13-channel track predicts. **The paper now says plainly that for this event the visibility domain supports a point source at the star, and its disposition rests on the repeat block.** Abstract, §4.6 and conclusions all corrected. |
| **C6** | Table 22's caption claimed "every window the region-maximum statistic flags" | it flags 66 windows in 41 pairs; caption now says what the table is |
| **C7** | §5.3.2 adopted the radius-corrected statistic "as the primary one" (10/8/2) against 13/9/4 everywhere else | **Adoption withdrawn.** It was built after the candidate list, and it moves the survey median *away* from 0.5. It is now stated as the robustness check it is. |
| **C12** | "median add-one rank **improves** from 0.445 to 0.432" | 0.5 is exchangeable, so that is *away* from it. Rewritten to say so. |
| **C13/C55** | β Pic "four execution blocks", "nine years", "three epochs" | 8 blocks, 8.4 yr, derived |
| **C14** | one control count carrying two different add-one p-values | 0 of 1655 (p = 0.001) and 16 of 1655 (p = 0.010) |
| **C15** | "113 of the 403 (86 per cent)" | 113/132 = 86 % of the windows whose configuration is known; 28 % of all 403. Both now given with their denominators. |
| **C16** | "excluding the 20 fine windows with a crossing restores uniformity (p = 0.39)" | **False on this sample.** `ksrank_v385.py`: removing all 71 leaves D = 0.103, p = 0.002. The old p came from a 431-window freeze. The correction makes the paper's caution stronger. |
| **C25** | Table 5's Class A $P_{\rm eff}$ row disagreed with the catalogue | row is now the per-window product $P_{\rm trig}C_{\rm resp}C_{\rm smear}$ for both classes, and its label says so |
| **C26** | "three systems carry 10.8 per cent" — the three were hard-coded as β Pic, AU Mic, TRAPPIST-1, the top three at v3.31 | top three are now BD+05 1668, Proxima Cen and HD 33793, carrying 285 windows = 17.2 % |
| **C27** | "41 per cent are M dwarfs" hand-typed against the table's 36.8 | macros from the table's own numbers |
| **C30** | smearing "negligible for 446 windows" with no denominator | 446 of the 455 that carry a value |
| **C32** | Fig. 13's caption claimed one departure at p = 0.015 | both classes depart; recomputed values in the caption |
| **C34** | on-source median was not the per-window median | 2812 s, derived |
| **C36** | "none recurs" asserted for four events, three of which admit no recurrence test | stated correctly |
| **C46** | "the other 403 fine-channel windows" | "the rest of the 403" |
| **C51** | "6.8×10⁶ s GHz, or 393 star-hour-GHz" | 1,900; the conversion was out by ×4.8 |
| **C57** | "all twelve Band 8 windows" | 24, toward three stars |

### Reviewer was wrong (verified, not assumed)

- **C11** "median 0.405 outside its own interval 0.42–0.46" — the interval
  is 0.341–0.458 and contains it.
- **C41** duplicate `tab:dwell`/`tab:classcomp` labels — each occurs once.
- **C63** "0 systems reach Arecibo but 1 reaches twice it" is not a
  contradiction: reaching *twice* the Arecibo EIRP is a weaker requirement
  on the survey's threshold, so 0 ≤ 1 is the expected ordering.
- **C69** an appendix build date in the text — there is none.
- **C24** "among 416" — no such string.
- **C71** `NReproChecks` = 21 — a mid-build artefact; the completed build
  gives 26, now 36.

### Durable fix

Every quantity above is now re-derived from the released catalogue by
`reproduce_from_catalogue_v385.py`, which runs inside `make_all.sh` and
**fails the build** if any of them stops matching: 36 checks, 0 failures.
That is the defence against the whole class of error round 1 found — a
number frozen at an earlier sample size and typeset as though current.

## Round 2 — scientific validity of the inference

Report: `VPR_ROUND2.md`. 18 MAJOR + 6 MINOR + 15 overclaiming items + 8 missing
controls. Verified each against the released products first.

### Real, and fixed

| ID | What was wrong | Fix |
|---|---|---|
| **S1** | "the other three have no second epoch, so no recurrence test exists for them" — **false**. `_repeat_blocks()` required a crossing frequency the release stores only sometimes, so it returned `[]` for events with 3, 16 and 3 same-tuning repeat blocks | matched on the window instead. **All four unattributed events have repeats, 23 blocks in all, and none recurs**: largest $T_\star$ anywhere in them 5.42, 0 above their own controls, 0 stage-1. The paper had been understating its own strongest evidence. |
| **S2** | `blockboot_v385.py` compared against a hard-coded `obs = 2`, the radius-corrected count, while the paper reports 4 | read from the catalogue; P(≥2)=0.87 → P(≥4)=0.64 |
| **S3/S10** | one chance expectation (3.2) quoted from a denominator of all 1655 windows while every stage-1 flag is Class A | **both reference classes now reported**: 4.4 (all windows, P=0.64) and 1.1 (Class A, P=0.022). The paper now says plainly that on the narrow class the four unattributed events are a ~2σ excess, and does not choose the reference class that removes the tension. |
| **S4** | the "block-resampled null" was degenerate: its per-window rate estimator had expectation exactly $1/512$ in every window, so it carried no window-to-window information — the code comment claimed it avoided precisely that | rebuilt. The rate is now the exchangeable rate times the measured tail factor, and the paper states that only the block clustering is resampled, not the rate. |
| **S5** | the tail factor 1.4 is propagated although out of sample it is 1.22 with a 95 % interval 0.61–1.87 | the Class A p-value is now quoted across that interval, 0.001–0.058, and called not sharply determined |
| **S6** | $P_{90}$ presented as the power at which the survey would have *flagged* a carrier; it is the trigger completeness, and promotion also needs the star to beat a ring whose Class A median is 5.79σ | new $P_{90,\rm promote}$: $8.7\times10^{13}$–$1.4\times10^{17}$ W, median $2.8\times10^{15}$, ×1.16 the median $P_{90}$. Abstract now says "triggers the search" and names the promotion factor. |
| **S7** | the budget omitted atmospheric decorrelation, which the method section declares and which is a **one-sided bias**: injected tones are added coherently and suffer none | +5/+20 % added as a one-sided term, and the text says every quoted $P_{90}$ is optimistic by it |
| **S8** | "No analysis choice in this paper postdates the reservation" — false | the three choices that can manufacture a candidate predate it; the four diagnostics that postdate it are now named, with the reason none of them can promote a window |
| **S9** | Table 12 labelled three survey events as calibration-sample, and an argument rested on it; `holdout_assignment_v381.json` marks all four `survey` | labels corrected, the argument withdrawn, and the point re-based on the repeat blocks of S1 |
| **S12** | the ×0.48–1.35 spread called "not an error" | it *is* a transfer uncertainty for the 375 Class A windows the campaign never injected into, and is now the largest term in the budget by a factor of several |
| **S13** | "∼1250× deeper than Mason et al." hand-typed, unreproducible, on the trigger not $P_{90}$, and **smaller than the $d^2$ ratio** | derived: 595 on $P_{90}$, against a $d^2$ ratio of 6563 — so in received flux this survey is the shallower. Both now given. |
| **S14** | the duty-cycle selection function is measured on zero-drift injections and applied to the drifting primary experiment | stated, with the unmeasured cell named |
| **S15** | recurrence coverage quoted as 54/87 systems, pooling both classes | the primary experiment's own figure, 41 of 65 Class A systems, added |
| **S18** | Table 11's $\Delta v$ is topocentric while the disposition rule is applied in the stellar frame (β Pic: −28 tabulated, −0.39 in the stellar frame) | caption says which frame each is, and points at the stellar-frame table |
| **S19** | the mask-width robustness check is one-sided — widening only | stated as one-sided, and the attributions re-based on stellar-frame velocity agreement, published detections and recurrence rather than on the half-width |
| **S20/O13** | β Pictoris offered as the positive control for a search whose target is a drifting narrowband carrier, which β Pic CO is not | split: the injection campaign controls the morphology, β Pic controls localisation and recurrence |
| **O5/S16** | HD 14055's 3.2σ imaginary part read as proof of displacement | withdrawn to "at this significance the uniform test does not localise the excess" |
| **O6/S17** | the 5.5σ CP−72 fit read as corroboration | it is on the cell the image-plane maximum had already selected: morphology, not significance |
| **O15/S11** | two β Pic ranks called $p$-values in a reference set the paper shows is not exchangeable | relabelled as ranks; the attribution does not need them |

### In progress

**M1** — the drift-following, continuum-subtracted fit on all thirteen events,
which the reviewer made a condition of acceptance, is running on the
processing host (`visfit_all_v385.py`; 6 of 13 done at the time of writing).

## Round 3 — method description, reproducibility and presentation

Report: `VPR_ROUND3.md`. 27 MAJOR + 38 MINOR.

### The two that mattered most

| ID | What was wrong | Fix |
|---|---|---|
| **P15** | **Four stars were in the release twice**, under two name strings each — SIMBAD's name route and its position route disagree on punctuation, and two entries carry a leading `* `. So the survey counted **94 stars and 87 systems where it has 90 and 83**, and the error reached the *title*. Three generators each carried their own copy of the pair map and none knew about the aliases, so the count was consistently wrong everywhere and therefore invisible. | new shared `star_alias.py`; `survey_stats.py`, `v342_calc.py`, `v352_calc.py`, `make_figures_v328.py` and `make_tables_v328.py` all use it. **The title is now `\NStars{} Stars within 40 Parsecs` and reads 90.** A second bug surfaced on the way: `v342_calc.py` defined `ALIAS` twice, the later one shadowing the merge map, so `sysn` silently stopped merging halfway through the file. The defence is an identity, not vigilance: **no two systems may share a distance**, asserted in the catalogue writer. |
| **P16** | the reviewer reported a quasar in the star sample (`j1256-1257`, 8 windows at 21.15 pc) | **Half right.** The ALMA field of that calibrator-style target contains **LP 736-15**, a nearby M dwarf whose Gaia parallax of 47.27 mas is exactly the 21.154 pc the catalogue carries — verified by a SIMBAD cone search on the field centre returned by the archive. So it is real science under the wrong name, not contamination. Renamed to LP 736-15. |

### Also fixed

- **P22** — seven floats were never cross-referenced, including Fig. 7 (round 2's
  requested test) and Fig. 6. All now cited from the text that needs them.
- **P23** — five full-width figures printed below their design size, worst being
  Fig. 14 at scale 0.65 with 3–5 pt type. All now print at 1.00–1.01.
- **P33–P36, P45** — the five densest passages restructured: the 131-word
  catalogue column sentence into four labelled groups, the seven limitations and
  the five-step candidate definition and the five-term budget into lists, and
  the 82-word response-factor sentence into three.

### Condition of acceptance M1 — done, and it changed an answer

The drift-following, continuum-subtracted fit was run on all thirteen stage-1
events from the recalibrated blocks (`visfit_all_v385.py`, ~5 h on the host).

- **The estimator works**: β Pictoris recovered at the stellar position in
  7 windows at 5.9–9.5σ, HD 48370 at 5.9σ with a 2.7σ imaginary part — still
  displaced, as its foreground identification predicts. One β Pic window is
  unreachable because its drift track is wider than the continuum reference
  leaves, and that is reported as a limitation rather than as a null.
- **All four unattributed events show nothing**: largest $|{\rm Re}/\sigma|$
  = 0.93, none consistent with a source at the star, and no control position or
  frequency anywhere in the thirteen above 2.14σ.
- ★★ **It withdraws the paper's most awkward loose end.** An earlier
  single-block fit had reported a 5.5σ point source at CP−72 2713; this fit
  returns **−0.86σ** with an imaginary part of +0.02σ. That window's stellar
  continuum is 10.9 mJy at 5.8σ — almost exactly the 10.4 mJy the earlier fit
  attributed to a narrowband excess. The later fit removes a continuum per
  integration along the track, was implemented independently, and reproduces
  β Pictoris where the earlier one was never tested. Adopted; the 5.5σ point
  source is withdrawn in both the appendix and the conclusions.

Two engineering notes worth keeping: the first 13-event run silently returned
**6** results because the dict was keyed on star name and eight events are
β Pic (now keyed on `star|eb`, with `len(results) == len(inputs)` asserted);
and taking the continuum median over every channel in the slice built an
11.9 GB array for the 15.3 kHz windows, so it now uses a fixed set of
reference offsets either side of the guard band.

## Round 4 — audit of the fixes

Report: `VPR_ROUND4.md`. 27 MAJOR + 19 MINOR, and its structural finding was
right: nearly every remaining defect is **a quantity that exists twice**.

Verified and fixed: **Q1** (Fig. 1 plotted 94 stars against a caption saying
90 — `make_fig_context_v342.py` keyed on the raw name), **Q2** (the same in
`completeness_sensitivity.pdf`), **Q3** (`NStarBands` 117 → 113), **Q4**
(Table 3's "Stars" column carried the system count), **Q5** (two name
matchers gave 51 and 53 teff stars; the table's is now the only one), **Q6**
(six copies of the pair map, now one), **Q7** (TWA 3A was in no bound pair
and counted as two systems — but the reviewer's claim that three declared
pairs are one star twice is **wrong**: each member has its own Gaia
parallax), **Q9** (a superseded drift range), **Q10** ("seven against four"
is 13 against 66), **Q11**, **Q12/Q13** (the chance table mislabelled the
naive Poisson and two denominators were swapped), **Q14**, **Q15** (my own
error: HD 48370 was counted as a β Pic recovery, making "7 windows at
5.9–9.5σ" of "6 at 6.1–9.5"), **Q16** (one repeat statistic computed two
ways, 5.51 vs 5.42), **Q17**, **Q20** (a recovery percentage multiplied by a
power-transfer factor, with a `min(100, ·)` clamp hiding it — withdrawn),
**Q21**, **Q22**, **Q23**, **Q24**, **Q25** (`NReproChecks` depended on when
it ran, so it failed the clean-regeneration test), **Q26**, **Q27**
(pointing entered a symmetric quadrature sum as a one-sided maximum — the
same error S7 had just fixed for decorrelation, in the same table).

Durable fix: `literalsweep.py`, which reports every prose literal equal to a
generated macro. It is a report and not a gate, because "5σ" and "two
transitions" are literals on purpose.

## Round 5 — final look

Report: `VPR_ROUND5.md`. 25 must-fix items, verdict "not submittable today".

Fixed: **R1** (the abstract paired two *different* estimators, 3.2 from ideal
exchangeability against 1.1 from the block-resampled null — the matched pair
is 4.4/1.1, and every headline use now says which), **R2** (an appendix
frozen at the four-flagged-window era, now scoped to the 447 windows it
covers with a pointer to the full-sample result), **R3**, **R4**
(`BenchEffRatio` derived from the superseded uniform-factor $P_{\rm eff}$),
**R5** (a median printed outside its own interval, because the median came
from the 315-window hold-out and the interval from the 578-window campaign
set — both now printed with their own sample), **R6** (one symbol for two
estimators of the CP−72 repeat), **R9**, **R10** (`$p =< 0.01$` rendered in
five places: a macro body beginning `<` after a typed `=`), **R13**, **R14**,
**R17**, **R18**, **R22** (**nine sentences that read as replies to a
referee** — Glenn asked specifically that the paper read as a natural
first-time paper, and they are gone), **R23** (Sheikh et al. 2025 is AJ 169,
118 not 108; Manunza et al. observed at 6 and 18 GHz, C and K band, not L/C;
the reference list is now alphabetised — 22 of 45 entries moved), **R24**
(the ALMA partner is NSTC, not MOST), **R25** (the three submission
blockers are now the whole of `AUTHOR_ACTIONS.md`).

Not fixed, deliberately: the remaining MINOR items are cosmetic or turn on
judgement the authors should exercise. They are listed in `VPR_ROUND5.md`.
