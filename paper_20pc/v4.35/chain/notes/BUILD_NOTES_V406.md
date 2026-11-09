# v4.06 build notes — the trigger-uniformity reframing, the multi-epoch stack, the C_resp key, and D14

**Built 2026-09-27 from v4.05 (`5bde124e9d8a`).** 52 pp, **main text 19.69 pp**
(appendix starts p. 21). The 15-page cap remains **deliberately broken**, per Glenn's
standing directive that page length is deferred until the science is settled: length was
**measured and not optimised**.

| gate | result |
|---|---|
| pdflatex | **0 errors, 0 undefined refs/cites, 0 multiply defined, 0 overfull, 66 underfull** |
| Type 3 fonts | 0 |
| `roundcollide` | **89 / 89**, 0 problems |
| `macrosyn` | 0 problems (9 declared open divergences unchanged) |
| `consistency_v399` | 0 problems |
| `prosenum_v399` | 0 literals disagreeing with a macro |
| `macroleak` | 0 problems |
| `intsweep` | **81 integers in running prose, 81 registered, 0 stale, 0 problems** |
| `audit_numbers_v385` | **49 PASS / 0 FAIL**, 10 warn, 7 skip |
| `reproduce_from_catalogue_v385` | **22 pass / 0 FAIL** |
| `selftest_v403` | 26 checks, 20 demonstrated failing |
| `selftest_v404` | 46 / 46 demonstrated failing |
| `selftest_v405` | 60 / 60 demonstrated failing |
| **`selftest_v406` (new)** | **65 / 65 demonstrated failing, 0 not demonstrated** |
| `cleanregen` | **134 / 134 byte-identical** |
| arXiv abstract | 1884 rendered chars, 302 words (limit 1920, headroom 36) |

New generators: `trigunif_v406.py` (round 95, 116 macros), `stack_v406.py` (round 96, 80),
`crespkey_v406.py` (round 97, 32), `hzlist_v406.py` (round 98, 9), `p90r7_v406.py`
(round 99, 18), plus the shared `numfmt_v406.py` and the gate `selftest_v406.py`.

---

## 1. ★★★ D16 — a flat 5σ is not a uniform criterion, and it explains the crossings

New §5.2.x `sec:trigunif`, and the reframing is given the prominence D16 asks for: it is in
the **abstract**, in the **Results**, and in the **Conclusions**.

**What is published per window, in the catalogue** (`scale_route_a`, `scale_route_b`,
`n_search_cells`, `n_ind_cells`, `trigger_1pct_window`, `trigger_1pct_survey`): the realised
scale of each window's own null by **two independent estimators**, the number of searched
(channel, drift) cells, the fitted number of **independent** cells, and the statistic the
window would have to reach for a 1 per cent false alarm in itself and over the catalogue.
`\NCatCols` 53 → **60** (the sixth new column is D18's `n_chan_avg`).

**Every published number reproduces from the frozen measurement**: cells per window
**112 → 6.87×10⁶** (4.8 decades, median 354), $N_{\rm ind}/N_{\rm cells}$ = 0.808; a
per-window 1 % needs **4.00** (3.52–15.86; A 5.38, B 3.94), survey-wide 1 % needs **5.53**
(4.97–22.19; A 6.61); **30 of 51** crossings below their own per-window requirement, **40 of
51** below the survey-wide one; η Crv `X122b6ff_X1041e` at $T_\star$ = 5.0059, 6.71×10⁴
cells, $s_w$ = 1.008, **needs 5.157 / 6.420 — below both**.

★★★ **The expectation, and why this strengthens the null result.** Summed window by window:
**27.4 expected with an ideal unit null, 37.6 with the measured scale, against 51 observed**.
Class A by three independent routes: **33.5 / 36.5 / 41.1 against 50 observed**, spread 1.23.
The paper now says so plainly, and says that it removes the need for any artefact hypothesis
to explain the crossing population — while leaving the negative result intact, because the
rank screen and recurrence are both *relative to the same window* and carry no dependence on
$N_{\rm ind}$ or $s_w$.

★ **The bracket is 27–41, not 27–42.** D16's summary rounded 41.1 up. The generator publishes
the measured bracket and this note records the disagreement rather than reconciling it.

★★ **Three join defects handled rather than absorbed.**
- The join covers **1641 of 1655** windows; 14 ship **blank, not zero** — a consumer that read
  a blank as zero would get zero cells and infinite protection. The build asserts the gap is
  under 5 per cent, so this cannot become the fifth silent instance of that family.
- **71 windows carry more than one extraction**, and `s_A`/`s_B` agree between repeats to a few
  per cent while `N_ind` (a Monte-Carlo fit) can differ by **×1.8**. The median over repeats is
  published, because "the first record in the file" would make a released column depend on
  file order.
- ★ **Two windows cannot be told apart by the join key at all** — two Proxima Cen TDM rows
  whose peak statistics agree to 10⁻³ — and that is a *different* ambiguity from re-extraction.
  It is counted (`\TuNCatAmbig` = 2) and asserted small rather than resolved by picking one.

**The measured nulls, stated as nulls** (new App. L.1 `app:sensnull`): morphology-for-threshold
**×1.16, i.e. 16 per cent worse** (false-alarm log-slope −3.84/σ, so a veto needs 62/85/98 per
cent to buy 5/10/20 per cent in flux and the two discriminants deliver 13.3 per cent; Hanning
already correlates channels at ρ = 2/3), **with its falsifier** — the same cuts reject
20-channel lines 111/111 and 10 %-duty transients 107/107 while keeping 95.8 per cent of
carriers, so the null is a property of the false-alarm population and not of a broken cut.
Grid-quantisation recovery **0.997 ± 0.003** against the trigger and **0.992** against the rank
screen, and — the sentence that matters — the campaigns draw drift and sub-channel offset
**continuously**, so the loss is **already inside the measured $P^{\rm sel}_{90}$** and
**must not be corrected for twice**. The top-hit deduplication artefact is **absent and of the
opposite sign**. The one unbooked gain is stated and **not applied**: a 3-channel matched
filter, **×1.08 fixed / ×1.17 offset-matched**, ×0.972 (a *loss*) at a channel boundary, and
for the **n = 1 population only**.

---

## 2. ★★★ D17 — the stellar-frame multi-epoch stacked search, as a subsection

New §5.3 `sec:stack`, about one page, with a matching paragraph in the abstract and the
conclusions. 394 groups, **78 stars, 2,277 epoch-windows, 1,454 h**. Registration validated on
real lines first (HD 285968 19.26 ch topocentric → **0.798 ch**, rms 0.351 ch = 0.223 km/s;
β Pic CO(2−1) agreeing to **0.087 km/s** across a **×16** change of channel width). The gain is
**√N_eff**: realised/√N_eff = **0.991**, realised/√N = 0.79, median N_eff/N = **0.67**, and
HD 161868 stacks **12 epochs for a gain of 0.94** because its N_eff is 1.1. Limits deepen
**×1.39** median (×2.32 p90, ×4.45 max), **×1.21 carrier-equivalent**. **Proxima Centauri:
63 blocks, 84 h, 6.3 yr, 5.15×10¹² W.** Two survivors, both β Pic CO, agreeing to 0.14 km/s
across two bands — the positive control passing — and **zero unattributed**.

★★ **The reflex restriction is in the same paragraph, and the arithmetic is now right.** A
488 kHz channel is **0.635 km/s** at CO(2−1), so ±30 km/s of reflex motion is 23.1 MHz =
**47 channels**. The v4.05-era note said "47,000"; the generator now **computes** the figure and
**asserts it is tens of channels, not tens of thousands** — the check the note lacked.

★★ **Three literals in the adopted generator are now computed, and one of them changed the
claim.** `StkBadWeight` (27) and `StkNUnattributed` (0) were typed; both are derived, the
second by running the survey's own ±50 km/s mask over every survivor. And the persistence
list's star keys were typed: **three of the nine were misspelt**, so the first run of that
block silently tested six stars while claiming nine. The generator now asserts every named
star is present.

★★★ **And correcting that changed the statement, in the paper's favour.** The honest result is
**not** "all nine stack below threshold": eight do, at **Z = 3.26–4.43** with **0 of 9**
exceeding their own controls and **0 of 9** passing the full criterion. **HD 285968 reaches
Z = 12.89** on the same frame-locked foreground CO line used as the registration standard —
and is rejected because **its own control ensemble reaches 14.19**, i.e. the emission is
extended, which is what a foreground cloud does and a transmitter does not. That is a stronger
and truer sentence than the bare null. ► D15's report gave the range as 0.92–3.71 over a
different selection; the disagreement is recorded, not reconciled.

★ The drift tolerance is now quoted **per span**: 1.5×10⁻¹ Hz s⁻¹ over the **median** 38 d
inter-epoch span, 2.0×10⁻³ over the longest (2857 d). A single number here was a per-stack
quantity masquerading as a survey one.

---

## 3. ★★ D18 — the C_resp key, and the covariance as a sixth validation

**Patched at the consumer, `v342_calc.py`**, exactly as `CRESP_KEYING.md` specified: the key is
the **nearest modelled effective resolution** among n = 1, 2, 4 instead of `abs(fs_ratio - 2.0)
>= 0.05`. **Exactly one row of 1655 changed**: 51 Eri `A002_Xb95160_X3e24` at 1953.1 kHz,
$C_{\rm resp}$ **1.3334 → 1.0573**, EIRP_eff **1.459 → 1.157 ×10¹⁵ W** = **×1.261 = 1.01 dB
overstated, in the conservative direction**. **0 crossings affected**; the published
$C_{\rm resp}$ macros do not move; the system counts at 10¹⁵ W do not move on either power
scale. The split is now **n=1: 1509, n=2: 145, n=4: 1**, and the averaging factor is published
as a catalogue column (`n_chan_avg`) so a reader can check which response a window received.

★★ **The gate that could not fail is fixed, and the fix is demonstrated in both directions.**
The "two dominant ratios" assertion allows 1 per cent of windows to be anything (1/1655 =
0.06 per cent) and `han_avg` was **binary — a flag with too few states is a check that cannot
fail**. Two new assertions: every window's archive ratio must match *some* modelled factor
within 3 per cent, and the factor keyed must be the *nearest* one. `selftest_v406` case 1
**reinstates the shipped binary flag and requires the assertion to fire**.

★ **The channel covariance is added as a sixth, independent validation of the response model,
and the only one of the six that can see the averaging factor** (App. F). Predicted delivered
lag-1 **0.667 / 0.300 / 0.115** for n = 1 / 2 / 4, recomputed here from the Hann kernel and not
imported from `cresp_v401.py`, a factor **5.8** apart; measured on control positions of 18
catalogue windows, **0.628–0.674 / 0.267–0.302 / 0.105**, and **18 of 18 confirm their own
key, 0 disagree**. Channel width alone would not serve: **244.1 and 488.3 kHz each appear in
both classes**. D16's own wording is corrected where the matched-filter gain is quoted — the
pooled 0.645 lag-1 sits on the n = 1 branch, so the ×1.08/×1.17 gain is an **n = 1 gain**,
91 per cent of the catalogue.

---

## 4. ★★★ D14 — $P^{\rm sel}_{90}$ through trigger → localisation, and the chance expectation RE-DERIVED

`sel_curve.py` rewired: the headline multiplier is the round-7 campaign's **trigger →
localisation** point, with the M3a **rank-gated** value kept beside it as `SEL_RANK` and
labelled superseded everywhere it appears. Class A **5.70 → 2.88 × P_trig**
(central interval 2.84–2.91) against **2.87** for the trigger alone — *localisation costs
0.2 per cent, which is the finding stated as a number*. Class B 4.62, all 3.85.

★★ **The comparison is protected against the obvious mistake.** The two values come from
**different campaigns**, so dividing M3a's 5.70 by round 7's 2.88 could manufacture a gain out
of two unrelated measurements. `sel_curve.py` therefore takes TRIG and SEL from the **same**
campaign and asserts the two campaigns' **trigger-only** points agree to 10 per cent
(2.87 vs 2.99 → 4 per cent) before the factor 1.98 may be quoted. Driven in both directions by
`selftest_v406` case 56.

**What moved, all of it through the macros, none by hand — 18 macros in 5 round files:**

| macro | v4.05 | v4.06 |
|---|---|---|
| `\PromoteMedA` (per-window $P^{\rm sel}_{90}$, A) | 5.3×10¹⁵ | **2.7×10¹⁵** |
| `\PromoteSysMedA` = `\SdMed` (per-system median) | 2.9×10¹⁵ | **1.5×10¹⁵** |
| `\PromoteLoA` / `\PromoteHiA` | 1.3×10¹⁴ / 3.9×10¹⁷ | **6.4×10¹³ / 2.0×10¹⁷** |
| `\PromoteSysLoA` / `\PromoteSysHiA` | 1.3×10¹⁴ / 6.9×10¹⁶ | **6.4×10¹³ / 3.5×10¹⁶** |
| **`\SdNFifteen`** (systems reaching 10¹⁵ W) | **14** | **25** |
| `\OccEirpMed`, `\OccCwtfmMed`, `\OccCwtfmWorst` | 2.9×10¹⁵, 2.5×10⁴, 5.9×10⁵ | **1.5×10¹⁵, 1.3×10⁴, 3.0×10⁵** |
| `\OccCwtfmHetero` / `...Worst` | 2.3×10⁵ / 5.5×10⁶ | **1.2×10⁵ / 2.8×10⁶** |
| `\MasonMedPsel`, `\FluxSelMatchMed`, `\FluxSelMedRatio` | 2.9×10¹⁵, 4.0×10⁻²², 8 | **1.5×10¹⁵, 2.0×10⁻²², 4** |
| `\SqrtScalePsel` | 7.7×10¹² | **7.4×10¹²** |
| `\NCatCols` | 53 | **60** |
| new | — | `\SelRatioRank` = 5.70, `\SelRankGain` = 1.98 |

★★★ **The chance expectation is RE-DERIVED, not re-labelled, and the result is the strongest
single number in this version.** `\ClustStageMean` = 0.89 is conditioned on trigger **and
rank**; the rank clause is a one-in-513 filter, so dropping it cannot be a change of wording.
On the chain the paper now states — **trigger → localisation → attribution** — each factor
measured: **36.5** Class A windows expected to trigger by chance (D16, from the catalogue's own
published columns), the fit localises **0.985** of events at $T_\star\approx5$ (0.977 through
all three clauses, so the factor is the same either way, and the two are asserted to agree),
and the frozen mask occupies 4 per cent of the searched band. **34.5 expected unattributed
Class A crossings against 35 observed.** That is a factor **39** larger than 0.89 and it
accounts for the observed population outright. `\ClustStageMean` is retained, correctly
labelled, for stage-1 events only — which are *defined* by the rank screen.

► **The campaign was at 40 of 42 usable units (of 56 planned) when this version was cut.** The
sibling `p90-r7-finish-and-analyse` had reached 51/56 done at 01:30 UTC and had not
re-published its analysis; the published artefact's own gates (campaign validity, null
0.089 % against a 1 % pre-committed ceiling, positive control 0.995 against a 0.95 floor) all
hold, and `\RsevNUnitScored` = 40 is printed in the paper. **To refresh: re-run
`referee_r8/p90_r7/finalise.sh`, copy `p90_r7_analysis.json` and `selfunc_classA.json` into
`v4.06/r8inputs/`, and re-run `make_all.sh`.** Nothing else has to change.

---

## 5. The v4.05 residue, each closed at its generator

- ★ **`build_ranked_master40pc.py` no longer emits a blank `is_exo_host`** (fifth instance of
  that family). It writes `True`/`False` explicitly for the 48 rows it creates, **asserts none
  is blank**, and — for the 96 inherited from the ≤20 pc census, which are not its to fix —
  **pins the count at 96 and fails if it grows**, writing
  `ranked_master40pc_flagaudit.json`. Verified in a sandbox: the census changes in **exactly
  43 rows and only in `is_exo_host` (blank → `False`) and `n_planets` (blank → `0`)**; every
  other field is byte-identical, and no paper number moves.
- ★ **§6.5's habitable-zone list is generated** (`hzlist_v406.py`). The literature *membership*
  stays a declared table with its citations — no catalogue can decide habitable-zone
  membership — but the **count, the word "Six", the "searched" claim, the contested count and
  the formatted list** are computed, and every named star must resolve to a star in the
  released catalogue. ★★ **That assertion fired immediately**: the paper's "GJ 273" is
  `BD05 1668` in the catalogue. And it found something the typed sentence hid — **two of the
  six do carry crossings** (GJ 273 ×4, LHS 1140 ×1, in 2 blocks), so the passage now names
  them instead of implying a clean set.
- ★ **`eq:cwtfmhet`** is now `\ref`'d in the prose that discusses it.
- ★ **The occupancy extract's resolution class is derived, not read.** Nine rows carry an empty
  class and five say `medium (1–5 MHz)`, against a binary fine/coarse assumption everywhere
  downstream — so a consumer testing `startswith('fine')` filed a 488.3 kHz τ Cet window and a
  488.3 kHz HD 285968 window as *not fine*. The class is now derived from `chanw`, **asserted
  to agree with the stored label wherever one exists** (0 mismatches), and the derivation is
  required to move something: **7 rows are relabelled fine, 719 → 726**. The screen's
  conclusion does not move (p = 0.15, z = 1.1 unchanged).
- ★ **`'%.2f' % 0.145` → `numfmt_v406.py`.** The private half-up rounder in `freqocc_v405.py`
  is now shared, and it is **driven in both directions**: `printf` is demonstrated wrong on
  4 of 5 cases the survey can actually produce (58/400, 1/8, 7/40, 29/200) and demonstrated
  *right* on the one that is not a tie, so the module cannot be a no-op.

---

## 6. Findings about the checks themselves

- ★★ **`roundcollide` could be defeated by a variable name.** It recognised only
  `OUT|OUTFILE|OUTPATH` on the assignment line, so `p90r7_v406.py`'s `TEX = ...` produced
  **"NO WRITER for a file a generator plainly writes"**. Both ends fixed: the generator renamed
  to house style, **and** the pattern widened, because the next one will pick another name. The
  gate now **raises** instead of `sys.exit(1)`, so `selftest_v406` can drive its own detection
  logic (case 64).
- ★ **My own first draft of the persistence-list block was the sixth instance of the
  cannot-fail family this cycle** — it silently selected six of nine stars. The assertion that
  catches it is case 39.
- **`selftest_v406`: 65 cases, 65 demonstrated failing.** Every assertion added anywhere in
  this cycle is driven, including the two that fire on *shipped* v4.05 behaviour (the binary
  `han_avg` key; the typed `StkNUnattributed`).

---

## 7. Noticed, out of scope, not changed

- **`canon_names_v381.py` is broken**: it reads
  `/workspace/SETI/paper_20pc/v3.72/frozen_export_v3.60.json`, and v3.72 was deleted. It is
  **not** in `make_all.sh`, so nothing fails, but it cannot be run. Either repoint it at a
  frozen input inside the version folder or retire it.
- **`make_fig_sample.py` is an orphan**: it writes
  `figures/sample_distance_distribution.pdf`, which no `\includegraphics` uses and which
  `make_all.sh` never invokes. Running it by hand created a file `cleanregen` then reported as
  NOT REBUILT — a true report about a real orphan. Eight such dead figures are warned about by
  `audit_numbers`. Either wire them in or delete them from the deposit.
- ★★ **The census contains what look like two rows for one physical window.**
  `HD 139084B [921024]` and `HD 139084B [805632]` are two Gaia source ids ~1–3″ apart that the
  archive names identically; **8 catalogue rows share `(eb, star_snr)` exactly** between them.
  The disambiguation is deliberate and documented in `build_ranked_master40pc.py`, but a reader
  of the catalogue sees the same measurement twice under two names, and the exoplanet-host and
  system counts should be checked against it.
- **`\CampUnOneT` remains a pre-repair record** (flagged at v4.04 and v4.05, still true).
- **`tab_visibility_v384/v385.tex` still write `HD14055`**; `audit_numbers` warns twice.
- **22 labels defined and never referenced**, now including `app:sensnull` and `sec:stack`
  (both are cross-referenced *from* the new prose but are themselves section anchors);
  `eq:gain`, `eq:visphase` and `tab:specclass` are UNRESOLVED in the `.aux`.
- **Disk**: `/workspace` sat at 99 per cent (2.5–2.9 GB free) throughout. v4.06 is ~160 MB.
  Nothing was deleted this cycle; a campaign of any size still would not fit.

## 8. Not in this version

- **R2-6** (the geometry column, the $N_{\rm eff}$ reconciliation).
- **R2-10's** Table 24 deletions and appendix re-lettering.
- **R1-8.**
- **The 51st visibility fit** — the ledger input is a glob, so this is a re-run and not an edit.
- **The closure-phase RFI record** (`rfi_ledger_r7.json` exists and is still not wired).
- **`\CampUnOneT` re-measured after the ACA control-annulus repair.**
- **Retiring `visfit_v385_calc.py` and repointing `visgain_v399.py`** at `ledger_v403` — the
  five `macrosyn` divergences that owner covers are still open and still declared.
- **The matched filter is deliberately not applied** (D16), because it changes the search
  statistic and therefore the crossing list and the frozen catalogue.
- **The trigger is deliberately left at 5σ** (D16); Eq. `eq:tunif` plus the per-window
  $s_w$ and $N_{\rm ind}$ columns are published so a reader can impose any α they like.
- **Page length** — measured at 19.69 pp of main text against both referees' 15-page cap, and
  not optimised, per Glenn's standing instruction. Deleting the two new subsections would
  recover roughly 2 pp when that becomes the priority.
- **The last 2 of 42 usable P90 units** (see §4).
