# v4.09 build notes — the repaired extraction becomes the search statistic, referee 2's 345.5 GHz cluster dissolves, η Crv gains a recurrence test, and the block ledger closes permanently

**Built 2026-10-04 from v4.08 (`8f31704edd01`, notes amended `cfd03e103dcf`).** This is the
final version of referee round 8. Its science inputs are
`referee_r8/V409_INPUTS.md` (828 lines, 15 verdicts) and `DECISIONS_R8.md` **D34–D36**;
everything adopted here was measured by that worker on products this container no longer
holds, and every one of those records is frozen into `r8inputs/v409/` and shipped.

**60 pp, main text 22.07 pp** (appendix starts p. 24). The 15-page cap remains
**deliberately broken** under Glenn's standing directive (D24): length is measured and not
optimised until the science is settled. The main text grew 21.98 → 22.07 pp on one
result-bearing subsection (§5.2.5) and two main-text tables.

| gate | result |
|---|---|
| pages | **60**; main text **22.07 pp**; appendices 36.72; back matter 0.21; bib 0.34 |
| pdflatex | **0 errors, 0 undefined refs/cites, 0 multiply defined, 0 overfull**, 83 underfull |
| Type 3 fonts | 0 |
| `roundcollide` | **92 / 92**, 0 problems |
| `xrefcheck` | 141 labels, 0 misplaced, 21 defined-but-unreferenced (was 23) |
| `macrosyn` | 0 problems (9 declared open divergences unchanged) |
| `consistency_v399` | 0 problems |
| `prosenum_v399` | 0 literals disagreeing with a macro |
| `macroleak` | 0 problems — **plus a new clause, see §7** |
| `intsweep` | **83 integers in running prose, 83 registered, 0 stale** |
| `audit_numbers_v385` | **49 PASS / 0 FAIL**, 10 warn, 7 skip |
| `reproduce_from_catalogue_v385` | **22 pass / 0 FAIL**, 19 skipped |
| `census_dupcheck_v407` | C1/C2/C3 all pass |
| `pbgate_v408` | drive 0 PASS; drives 1–8 each fire |
| `selftest_v403` | 26 checks, 20 demonstrated failing, 6 structural |
| `selftest_v404` | 46 / 46 | 
| `selftest_v405` | 60 / 60 |
| `selftest_v406` | 65 / 65 |
| `selftest_census_v407` | 29 / 29 as specified |
| `selftest_v408` | **60 / 60** (57 + 3 added here) |
| **`selftest_v409`** | **48 / 48 demonstrated**, 0 not demonstrated |
| `cleanregen` | **144 / 144 byte-identical** |
| arXiv abstract | 1884 rendered chars, 302 words (limit 1920) — abstract untouched |

**The six assertions this round's decision record required to survive the build, all
confirmed in the shipped generators:**

```
V1   VnWinA + VnWinB == VnWindows                     417 + 1270 == 1687
V2   the crossing delta closes on VnNHits             56 - 4 + 1 + 1 + 2 == 56, 8 rows
F2   the block fates sum to FateScope                 144+18+11+1+3 == 177
V6   ClustShippedFixedSkyP < ClustFixedSkyP           3.6e-4 < 0.019
V7   the edge excess is emitted only with its one-window share and a held-out half
V7c  ... and the manuscript CITES them beside the ratio, so retire_macros cannot strip them
V12  no test writes a path production reads (every drive emits *_driveN.*)
```

New in this version: `v409_calc.py` (round 102), `blockfate_v409.py` (round 69, supersedes
`blockfate_v400.py`), `p90_budget_v409.py` (round 38, supersedes `p90_budget_v385.py`),
`selftest_v409.py`, the frozen input directory `r8inputs/v409/`, the deposited
`visfit_r7v409_result.json` and `repaired_v409.csv`, and the table fragments
`tab_crossdelta_v409.tex`, `tab_clust_v409.tex`, `tab_tail_v409.tex`,
`tab_p90budget_v409.tex`. Changed: `epoch_v403.py`, `p90r7_v406.py`,
`make_tables_v328.py`, `etadrift_v405.py`, `macroleak.py`, `roundcollide.py`,
`cleanregen.py`, `selftest_v408.py`, `make_all.sh`, `intsweep_registry.json` and the
manuscript. Retired to `retired/`: `blockfate_v400.py`, `p90_budget_v385.py`.

---

## 1. ★★★★ The repaired $T_\star$ is the search statistic, and the crossing list changes while its count does not

New main-text subsection **§5.2.5 `\label{sec:repairedstat}`** (Appendix **M** carries its detail) and
**Table 7** (`tab_crossdelta_v409.tex`, generated).

- **157 windows in 39 blocks** re-extracted with the corrected field selection; on-source
  **40.05 → 111.74 h** over them (median ×2.130), noise ×0.692, **146 joined** to a
  catalogue row **on the window interval**.
- Published, crossing by crossing: **4 fall below the trigger** (τ Cet `Xba460f_X7e6`
  5.1980 → 4.9064, η Crv `X75bfbf_X1430` 5.0126 → 4.9026, HR 1010 `Xc6a3db_X7b5b`
  5.0542 → 4.4791 and `Xc66ce1_X1345` 5.5820 → 4.5773), **1 appears** (HR 1010
  `Xc6fa08_X1053` 3.7673 → **5.4097**, as its noise falls 81.89 → 11.50 mJy), **1 is
  restored** (HD 139084 B, 4.1526 primary → **5.7635** companion), and **2 arrive with the
  tail** (HD 14055, 5.0061 and 5.4477). **56 − 4 + 1 + 1 + 2 = 56, a different 56** — said
  explicitly, and asserted.
- **Every one of the 8 rows fails the frozen rank screen** (controls ≥ star of 512: 237,
  68, 270, 74, 1, 47, 49, 3), recomputed from each product's own control vector rather
  than read off a flag. Both additions inside the sample are line-attributed in the
  stellar frame; the two from the tail are unattributed and are excluded as persistent
  carriers. **No disposition reverses.**
- ★★ **The legitimacy paragraph is three measurements, not an assurance.** The repair was
  decided and recorded in writing on **2026 September 27** before any re-extracted product
  existed (D1/D2); the trigger, the baseline window and the drift grid are unchanged, and
  only the input field selection moved; it was applied **uniformly** to all 157 windows;
  and it is **unbiased in the median** (median signed ΔT⋆ **+0.072**), **a no-op where
  nothing was lost** (median |ΔT⋆| **0.057** on the 5 windows that recovered no on-source
  time), and **not a no-op on the crossings** (they move 0.110–1.642). All three are
  asserted, each driven in both directions.
  ★ **`V409_INPUTS` and D35/D36 all quote "median |ΔT⋆| = +0.071"**, which cannot be a
  median of absolute values because it carries a sign: **+0.072 is the median *signed*
  shift and 0.353 is the median *absolute* shift**. Both are now printed, and the
  difference is stated in the appendix, because they are different claims.

## 2. ★★★ Referee 2's 345.48–345.64 GHz cluster was substantially an artefact of our own pipeline

New **Table 8** (`tab_clust_v409.tex`), three populations and one code.

- **3 of the group's 6 members are among the 4 that fall**, and **2 of those 3 are
  HR 1010**, one of the two most severely field-truncated stars in the survey.
- On the repaired population — **97 CO(3–2)-tuned fine windows, 34 stars, 11 crossings**,
  22 windows repointed at the repaired product and resolved **on sky position** — the
  referee's own fixed band gives **p = 0.019** against 3.6×10⁻⁴ as shipped, the
  position-free scan **0.82**, the position-and-width-free scan **0.78**, and in the
  stellar frame **0.33 / 0.89 / 0.88**.
- ★★ **This is a better answer than either hypothesis that was on the table.** The referee
  proposed a baseline artefact and injection disproved that mechanism; the real cause was a
  search run on a fraction of the in-beam time, at a fixed threshold, on the two
  worst-affected stars.
- ★ `\ClustShippedFixedSkyP < \ClustFixedSkyP` is asserted, so the post-hoc band can never
  be printed as the result. The shipped and released-product columns are printed **only**
  beside the corrected one.

## 3. ★★★★ η Crv's crossing now has a recurrence test: excluded at 11.57σ

New **Appendix M.3 `\label{app:etacrvrecur}`**, cross-linked from §5.2.3.

- Exactly **2** of the 48 η Crv windows with products cover the event's frequency and
  drift. The other is `A002_X11e10bc_X12662` — **the surviving sibling in the same member
  OUS as the uncalibratable block of §6** — and it is **2.19× deeper** (σ 0.00183 against
  0.00400).
- The survey's own estimator, re-run at a **single** drift and at the
  **stellar-frame-matched** channel, returns $T_\star=-0.618$ there against a control
  maximum of +1.10, where a persistent carrier of the discovery flux would have given
  **10.95**. **Excluded at 11.57σ**, with **N_eff = 4.79** equivalent discovery epochs
  from one block.
- ★ **The stellar-frame match moves the cell by −80.2 channels**, so a sky-frame test would
  have looked in the wrong place. The paper's existing 11.2σ was a **maximum over the
  repeat's own drift grid** and is now labelled as such, with the unbiased value beside it.
- ★★ **An assertion that could only ever fail on good data is recorded as such.** `S4` in
  the source work first asserted `N_eff < N`; N_eff is $\sum(\sigma_{\rm disc}/\sigma_i)^2$
  and **exceeds** N whenever the other epochs are deeper, which is this case. The deposit
  asserts the identity (closure to 1 part in 10⁶) and *reports* the direction. **A check
  that can only fail when the data are good is as useless as one that cannot fail.**
- ★ η Crv now has **one** threshold crossing, not two: `X75bfbf_X1430` fell.

## 4. ★★★★ The block ledger closes permanently, and the remaining gap is not ours

`blockfate_v409.py` supersedes `blockfate_v400.py`. The ledger is now **the v4.08 state plus
a named transition per block**, so the difference is auditable block by block.

| fate | v4.08 | **v4.09** |
|---|--:|--:|
| searched | 136 / 1.4 TB | **144 / 1.7 TB** |
| no calibration in the archive | 17 / 170 GB | **18 / 237 GB** |
| legacy calibration failure | 11 | **11** |
| disk-infeasible | 4 / 158 GB | **1 / 29.7 GB** |
| reachable, not attempted | 9 / 449 GB | **3 / 168 GB** |
| `never_started` | 1 / 67 GB (**unnamed**) | **0 — the category is gone** |

- ★★★★ The unnamed block is **`A002_X11e10bc_X23333`** — η Crv, Band 7, 67.2 GB, member OUS
  `uid://A001/X362b/Xc1d`. It was in the deposit's own sources all along: the upstream
  infeasibility list holds **four** names and the ledger copied **three**.
  **ALMA shipped 67.24 GB of raw ASDM it never pipeline-calibrated**: the delivery for that
  OUS offers **3** execution blocks, **2** carry a calibration application record and both
  are already in the survey (one of them is §3's covering epoch and the other is η Crv's own
  crossing block), and this one carries none. Its fate is
  `excluded_no_calibration_available`. ★★ **The gap is in the ALMA delivery, not in our
  effort, and no future run can close it** — a stronger and permanent statement than "not
  attempted". The screen that excluded it is **validated, not trusted**: against 361
  already-calibrated blocks as a control it resolved 0 and failed 10.
- ★★ **Two of the three published `disk_infeasible` labels are falsified by measurement**:
  `A002_X1171dca_X606b` and `A002_Xb2b000_X7667` both ran calibrate → select → extract →
  search, 4/4 windows clean. The sweep gated on ASDM volume and the working set is not a
  function of it (×2.3 to ×10.0 over 25–74 GB blocks). The remaining blocks are infeasible
  **by measurement**, each needing > 246 GB of working space.
- The ledger's own arithmetic is asserted twice over: the v4.08 prior sums to 177, the
  v4.09 state sums to 177, the five printed categories sum to 177, and the searched volume
  rises by exactly the transitions' own sizes.

## 5. Both withdrawals survive on the fixed key, and the aggregate rates strengthen

New **Appendix M.7 `\label{app:fixedkey}`**.

- **The ×2.39 near-edge excess stays withdrawn.** On the position key the pooled ratio is
  **×2.464** (p = 6.6×10⁻¹⁴), but **59 per cent of the near-edge exceedances come from one
  window** (HD 48370 `A002_Xc26103_X155a`, a bright resolved CO(2–1) line near the band
  edge). Remove it → **×1.020, p = 0.473**; apply the survey's own mask → **×0.981,
  p = 0.565**. ★ **D5's standing condition is met**: on a pre-declared seed the half
  *without* that window gives **×1.181, p = 0.24** over 190 windows while the half *with*
  it carries the whole effect (×3.924, p = 5×10⁻²⁰). The generator refuses to emit the
  pooled ratio without the share and a held-out half, **and asserts that the manuscript
  cites them beside it** — because emitting a macro is not enough when
  `retire_macros.py` strips what the manuscript does not reference.
- **The z = 3.5 occupancy excess stays withdrawn on its own grounds, and its immunity is
  demonstrated rather than assumed**: 35 of the 35 colliding basenames live in more than
  one product directory, and the occupancy extract is assembled per directory.
- **The aggregate exceedance rates are re-derived on 1,641 re-profiled windows and the
  fixed key *strengthens* the contrast**: Class A star-to-control **7.794 → 8.099**, all
  windows **6.400 → 6.596** (+3.07 per cent), control exceedances **645 → 627**.
  ★ **Class B is identical to the last digit** (1.418 either way), because every one of the
  35 collisions is a fine `spw3` window — itself a check that the repair touched only what
  it should.
- **The collisions and the stack's merged star identities agree**: the merge keeps every
  colliding pair separate, every testable group exceeds its own parallax tolerance, 6 of 8
  are pinned pairs, and none of the 23 merged identities contains two stars that share a
  colliding basename. **The analysis key was wrong and the stack was right.**

## 6. The archival tail, the follow-up stratum, and the survey's extent

New **Appendix M.4 `\label{app:tail}`** and **Table 33**.

- **8 of 12 reachable tail blocks searched, +32 windows, +22.69 h.** Two hold a threshold
  crossing, both HD 14055 Band 7, and both are carried through the frozen chain in order:
  unattributed in the stellar frame (−1165.6 and −317.1 km s⁻¹ from CO(3–2)); **both fail
  the 512-control rank screen** (49 and 3 above the star); and a persistent carrier is
  excluded at **11.75σ** and **12.70σ** over 31 covering epochs.
  ★ **The quoted exclusions are the conservative, informative-epoch ones**: 21 of the 30
  other epochs are ACA-sensitivity products carrying 3.0 and 2.8 per cent of the inverse
  variance, and alone they reach 1.9 and 2.2σ. On all 30 the figures would be 11.98 and
  13.02σ. `V409_INPUTS`'s own macro file emitted the all-30 pair under the names its prose
  used for the informative pair; both are now computed, named apart, and the generator
  asserts that the smaller is the one printed.
- **A separately labelled follow-up stratum**, 10 blocks / 40 windows / 35.33 h, kept out
  of the census because those blocks were fetched *because* they cover a crossing
  frequency. 2 of the 9 informative epochs are census windows and 7 are follow-up, so the
  exclusions are quoted as follow-up evidence with their stratum named.
- **The extent, printed as a four-step sequence**: 1,655/90 wrong content → **1,651/89**
  honest interim → 1,655/90/57 companion restored → 1,655/90/**54** repaired statistic →
  **1,687 windows (417 Class A + 1,270 Class B) / 90 stars / 82 systems / 56 crossings /
  1,185.49 h**.
- ►►► **DELIBERATE DIVERGENCE FROM THE ADOPTION LIST, and the only one.** The adoption list
  asks for the census of 1,687 windows. **The deposited catalogue remains the 1,651-row
  release**, because the per-window content of the 32 tail windows and of the restored
  companion does not exist in this deposit — the products are on a host volume — and
  `\NWindows` is the denominator of some forty statistics computed on those 1,651 rows.
  Inventing rows would have made all of them false. So the v4.09 extent is emitted under
  its own `\Vn...` namespace, printed as the sequence, and the paper says in both the
  results and the Data Availability statement which count is which. The repaired statistic
  is deposited for every re-extracted window as **`repaired_v409.csv`** so a reader can
  recompute the delta from the release rather than take the table on trust.
  ★ One quantity cannot be re-derived here and says so: of the tail's 22.69 h, **9.33 h is
  recomputed in the deposit** from the twelve HD 14055 tail windows' own records and
  **13.35 h is carried as a declared input** with its provenance named. `V409_INPUTS`
  carried the whole 22.687 as a typed literal commented "measured".

## 7. Table 11, and the residue from v4.08's notes

`p90_budget_v409.py` supersedes `p90_budget_v385.py` — **9 content rows, 10 assertions,
9 drives.**

- ★★ **The standing note was wrong**: Table 11 was never "6 of 7 rows hand-written"; the
  predecessor generated the whole table. What was actually wrong is narrower and worse.
- **`PLX_WORST = 0.0248`, commented "the largest fractional parallax error in the sample",
  was a typed claim about the sample that nothing compared to the sample.** Measured from
  Gaia DR3 parallaxes for **77 of 89** catalogue stars it is **1.65 per cent** — the
  literal was **×1.51 too large** — and the worst-constrained star is **γ Tri = HD 14055**,
  the star that carries this version's two new crossings. `BudDistWorst` 5.0 → 3.3 per cent.
- **The window-to-window transfer row that referee 1's point 5 is about reaches the table
  for the first time**: `BudTransLo/Hi` were computed and then dropped by
  `retire_macros.py` as unreferenced in four consecutive versions. It prints **−6/+9 per
  cent** from the **13 of 402** directly injected Class A windows, with
  `13 + 389 == \NWinA` asserted. ★★★ **And the mechanism is now closed, not just the
  instance**: `B10` requires the manuscript to *reference* those macros, so a row computed
  and then stripped fails the build.
- **The transfer and campaign rows were literally the same two numbers** (`T_LO, T_HI =
  MC_LO, MC_HI`); they are separate now, −6/+9 against −36/+4, and asserted to differ.
- **The decorrelation bracket has no source anywhere in this project** and is declared an
  external assumption in the table and in the emitted JSON, with a drive that relabels it
  as measured and must fire.
- ★★ **`\BudDominant` was chosen as the largest of four terms, two of which are not in the
  quadrature sum the sentence attributes it to**, so the paper printed "the independent
  terms combine to ±9 per cent dominated by **the injection statistics**" — a term that is
  not one of them. It is now the largest of exactly the three rows above the Combined
  line, and prints **the absolute flux scale**.
- **`etadrift_v405.py`'s docstring** no longer says 403.
- ★★ **`make_tables_v328.py`'s `n_starbands` mismatch is diagnosed and now asserts.** It
  printed `tables=116 vs survey_stats=112 MISMATCH` and exited zero for four versions. The
  cause is the alias-key family again: `survey_stats.py` has keyed on the **canonical**
  star name since v3.85 and this generator used the **raw** one, so four (star, band) pairs
  that are one star under two labels were counted twice. Keyed canonically the two agree,
  **the agreement is asserted** for every row of the cross-check, and the raw-name count is
  kept beside the canonical one so the size of the alias effect is visible rather than
  merely absent.

## 8. ★★★ Three assertions fired during this build and all three were right to

These were not obstacles; they are the gates doing the job they were written for.

1. **`epoch_v403.py`**: *"exactly one of the two rank-flagged unattributed crossings is
   expected to be fitted and one outstanding; that is what §5.2.3 says."* Folding in the
   CP−72 2713 fit made **both** fitted, and the build stopped. §5.2.3 is rewritten: **both
   are now fitted, both localise, and neither is promoted by it** — for the reason §5.2.2
   gives — and both are disposed of by recurrence. The assertion is now the mirror
   (`all fitted`) and is driven in `selftest_v408` case 59.
2. **`p90r7_v406.py`**: `assert len(_s1) == 1` on the rank-flagged unattributed localised
   crossing in the campaign's own $T_\star$ bin. Same cause. The pin is now **2**, the one
   the referee's question concerns is selected by **which of the two carries a deposited
   percentile** rather than by name, and §5.2.2 names both (61 Vir at +5.26, percentile 23;
   CP−72 2713 at +5.10). Driven in both directions, cases 57 and 58.
3. **`p90r7_v406.py`'s macro-count pin** (`== 112`) fired on the three macros that change
   added. Bumped to 115 and the drive updated. **That pin exists because the failure mode
   this project keeps producing is a macro that is *absent*, and an absent macro is neither
   empty nor NaN.**

★ A fourth: **the first pass of `blockfate_v409.py` wrote four macros named
`\FateDoneV408` and friends.** A LaTeX macro name may contain **letters only**, so
`\FateDoneV408` defines `\FateDoneV` and asks TeX to *typeset* "408"; in the preamble that
is `Missing \begin{document}` and **no PDF at all**. Neither `macrosyn` (which compares
values) nor the generators' own empty/NaN gate can see it, because the macro *is* defined —
just not the one anybody meant. Fixed at the three generators with an `isalpha()`
assertion, and **`macroleak.py` has a new clause** that scans every macro file for a
non-letter macro name; it is demonstrated firing.

## 9. ★★ D36's standing rule is enforced mechanically, including against this round's own gate

D36's fourteenth defect of the key family was not a key collision: *a driver that writes the
canonical output is a booby trap.* Every v4.09 generator takes `--drive N`, and **under a
drive every output filename is suffixed `_driveN`**, so a test cannot land on a path
production reads. `selftest_v409.py` asserts it, by hashing all nine production products
before and after 48 driven runs.

★ **And the first version of that gate violated the rule itself.** Its baseline check ran
each generator unperturbed — which wrote the real products, and was caught by `cleanregen`
reporting three round files differing. `--drive 0` now means *"no perturbation, but do not
write a production path"*, so the suffix follows the flag rather than the perturbation.
★ `roundcollide.py` needed widening a second time, exactly as its own note predicted: the
round file now reaches `os.path.splitext(...)` rather than an `open(..., 'w')`, so the gate
could not see the writer. It recognises that shape too, instead of waiting for a third
variable name.

## 10. Every number in the new material is read from a frozen record

The round's inputs are in `r8inputs/v409/` (20 files, 2.5 MB): the harvest
(`reext_results.json`), the per-window post-repair record with each product's own 512-point
control vector (`fieldfix_v409.json`), the matched recurrence fits
(`hd14055_recur.json`, `v409_recur_etacrv.json`), the clustering recomputation
(`scan_v409.json`), the fixed-key re-runs (`v409_aggrates.json`,
`v409_edge_recheck.json`, `v409_allpop.json`, `v409_collision_xcheck.json`), the tail
(`tail_collect.json`), the named block and its ALMA delivery record
(`neverstarted_v409.json`, `etacrv_delivery.json`), the follow-up stratum, the live SIMBAD
parallaxes, and the shipped Table 11 for row-by-row comparison. The CP−72 2713 fit is
deposited as `visfit_r7v409_result.json`, under the name `ledger_v403.py`'s input glob
expects, so folding it in was a re-run and not an edit.

★ **Typed values found and replaced while wiring this in**: the CP−72 fit's five numbers
(all present in its own record), the risen crossing's two rms values, the tail's hours
(part-measured, part declared), the visibility-fit coverage (`52 of 56` in the source note
against the ledger's own **51 of 56** — the ledger is what ships, and `V15` now asserts
`fitted + outstanding == crossings`), and the line offset of the risen crossing, which the
source note gave as "−28 km/s" where **−28.1 is its offset in MHz and −32.1 km/s is the
velocity**. A typed status string would have shipped a unit error into a table.

---

## 11. Not in this version

| item | why | where it goes |
|---|---|---|
| the point-by-point referee letter for round 8 | the science settled only in this version; the letter should be written against what ships | next |
| the length pass | **deferred by standing instruction (D24)**; measured, not optimised | — |
| the 3 remaining unattempted blocks (`X107e0e5_X252b`, `X10756f7_X3067`, `Xa8666f_X16de`) | each needs > 246 GB of free working space against a ~275 GB ceiling on this volume; `Xa8666f_X16de` is additionally gate-bound and cannot open at all | not reachable here |
| the 1 infeasible block (`Xa7a216_X2f0f`) | measured at **≥ ×8.32** expansion on a 29.7 GB ASDM | not reachable here |
| extending the deposited catalogue to the 1,687-window extent | the per-window content of the 32 tail windows and of the restored companion is not in this deposit; see §6 | when the products are deposited |
| R2-6, R2-10's lettering, R1-8, the closure-phase RFI record, retiring `visfit_v385_calc.py` | unchanged from v4.06–v4.08 | later |

## 12. Out of scope but noticed

1. ★★ **`tab:specclass` resolves UNRESOLVED in `xrefcheck`**, and `eq:gain` and
   `eq:visphase` likewise. Pre-existing since before v4.07 and not diagnosed in this pass.
2. **8 figures are built and never `\includegraphics`'d** (`audit_numbers` warns), and
   `canon_names_v381.py` still reads the deleted `v3.72/` and cannot run. Pre-existing.
3. ★ **`tab_visibility_v384.tex` and `_v385.tex` carry `HD14055` where SIMBAD says
   `HD 14055`** (`audit_numbers` warns). Cosmetic, but it is the star this version talks
   about most, and the two tables are superseded by the ledger in any case.
4. ★★ **The 9 declared `macrosyn` open divergences are unchanged**, five of them owned by
   "retire `visfit_v385_calc.py`; repoint `visgain_v399.py` at the ledger". That retirement
   is now the oldest open item in the build and it has been deferred four times.
5. ★ **`v409_calc.py` keeps its own copy of the 17-transition mask**, because
   `v342_calc.py` is a 1,300-line generator with side effects. `V14` asserts the two agree
   on every transition, so the copy cannot drift — but one list in one place would be
   better.
6. ★★ **`reext_results.json`'s own summary carries `checks_pass: false`.** That is the two
   guard checks of §1 firing — the exposure repair on three windows and a 0.16 per cent
   noise rise on one — both diagnosed and both explained in Appendix M.1. It is recorded
   here because a frozen input that ships with a false flag should not be discovered by a
   reader without an explanation beside it.
