# v4.04 — the round-8 referee response

Built 2026-09-26 from `v4.03/` by `cp -a`. Binding decisions:
[`referee_r8/DECISIONS_R8.md`](../../referee_r8/DECISIONS_R8.md) D1–D13 and
[`referee_r7/DECISIONS_R7.md`](../../referee_r7/DECISIONS_R7.md) A1–A6.
Reports verbatim in
[`referee_r8/REPORTS_RAW.md`](../../referee_r8/REPORTS_RAW.md).

★ **Glenn's standing directive is in force: page length is deferred.** No
science was deleted to save space. Deletions that are *corrections* happened.
Length is measured below and was not optimised: **main text 14.98 → 16.62 pp,
total 43 → 46 pp.** Both referees' ≤15-page cap on the main text is therefore
**no longer met**, deliberately.

---

## 1. What this version changes about what the paper claims

Four statements are corrected, two of them reversing a conclusion.

1. ★★★ **Appendix J.3's arithmetic was wrong and its conclusion was wrong in
   the opposite direction.** It read "line emission accounts for
   `\SbrAstro` = 3 of the `\SbrN` = 14, which leaves `\SbrResid` = 2 against
   `\ExpFlags` = 3.23 expected — far too many for chance". 14 − 3 ≠ 2, and 2
   is *fewer* than 3.23, not "far too many". `\SbrAstro` and `\SbrResid` were
   hand-typed literals in `make_numbers.py` from an older extraction.
   Recomputed from the released catalogue (`fa_v404.py`): 12 of the 14
   rank-first windows reach the trigger, **10 carry an identified CO
   attribution**, and the residual is **4 against 3.23 expected,
   P(≥4) = 0.40 — entirely consistent with chance.** *The rank-first excess is
   explained by astrophysics and is not, by itself, evidence that the rank is
   non-exchangeable.* The claim that it is not exchangeable stands, on the
   out-of-sample rank displacement, which is independent of the crossings, and
   the appendix now cites that instead.
2. ★★★ **The line mask is evaluated TOPOCENTRICALLY, not in the stellar
   frame.** Proved, not asserted: `maskframe_v404.py` re-derives all **1400**
   released `line_offset_MHz` and all **1400** `line_offset_kms` values from
   each crossing's observed sky frequency against the frozen 15-transition
   list, worst residual **0.001 MHz**, and none reproduces barycentrically or
   in the stellar frame. Two passages said otherwise. It is a documentation
   defect, not a correctness one — no attribution changes between frames at
   ±50 km s⁻¹ — and it is corrected rather than carried.
3. ★★ **The α CMa B limit is WITHDRAWN.** The pipeline propagates Sirius B
   with the *system* proper motion only and ignores the 50.13-yr visual orbit,
   so the search ran **3.1–3.6″ (3–5 synthesised beams)** from where Sirius B
   actually was. `fields_v404.py` asserts that **0** threshold crossings
   depend on the star before the withdrawal is printed. (Sirius A does lie
   inside the control annulus, in 10 of 15 windows, which is how this was
   found — the referee's actual question turned out to be the smaller
   problem.)
4. ★★ **AU Mic is removed from Table 21 and from Appendix F.** It was listed
   as a "line-attributed window" at +378.8 km s⁻¹ — far outside the mask —
   and **no AU Mic attribution exists in the results.** The `Fouque2018`
   reference went with it.

## 2. The four terms, and the one formulation of the rank's status

- **R1-2.** `tab:vocab` is new, immediately at the head of §4.6: *threshold
  crossing* (56), *screened event* (12), *localised event* (40), *confirmed
  candidate* (0). Every count in the manuscript is a count of one of those
  four objects and is stated with its unit. `tab:interpret` stays but its
  caption is corrected — it said "four levels" over five rows — and it is now
  explicitly about the *statistics*, where `tab:vocab` is about the *objects
  counted*. `\LgNScreen` came back out of retirement to supply the screened
  count from the ledger rather than from the older stage-1 generator.
  ★ Counts were checked against the ledger, not propagated: **16** attributed
  at ±50 km s⁻¹ over crossings, **10** over stage-1 windows, and both are
  labelled with their denominator everywhere.
- **R1-1.** `\rankstatus` is a `\DeclareRobustCommand` in the preamble holding
  the referee's own formulation verbatim, used in **§4.6, in Results, and
  twice in the appendices**. The contradicting sentence is gone: Appendix A
  said star and controls "remain exchangeable in signal-to-noise ratio", and
  now says that forming the statistic on uncorrected amplitudes removes that
  one asymmetry but does not establish exchangeability, *and that earlier
  versions of this paper wrongly said it did*. A table caption calling the
  ensemble a "calibrated screen" now calls it a prioritisation screen. The
  radial/noise geometry is named as the empirical source and the
  parameter-free correction is stated not to restore a validated null.

## 3. R2-1: which extraction change removed HD 14055 and HD 23484

`counts_v404.py` (round 82) joins the **pre-repair** frozen export to the
**post-repair** corrected one on (execution block, window edges), and the
answer is a result rather than a correction:

| star | window | pre-repair T⋆ / ring | repaired T⋆ / ring | controls above |
|---|---|--:|--:|--:|
| 61 Vir | B7 344.872 GHz | 6.16 / 5.88 | **5.96 / 5.65** | 0 |
| HD 14055 | B7 330.387 GHz | 6.03 / 5.96 | 5.57 / 5.99 | **9** |
| HD 23484 | B6 229.610 GHz | 5.30 / 5.25 | 5.52 / 5.55 | **1** |

The change is the **ACA control-annulus repair**: **1131 windows in 278
blocks** re-extracted on the correct 7 m primary beam, which moves each control
outward to its intended radius. ★ And because σ is the median absolute
deviation *across* the control positions, moving the controls moves the
**star's** own statistic too. The repair is **unbiased** — median change
−0.08 at the star, −0.00 at the ring — but not small: the typical move is
**0.32 at the ring and 0.19 at the star**, which is enough to decide a rank in
a window where star and ring sat within a tenth of each other, as all three of
these did. HD 14055 and HD 23484 fall behind their own rings and stop being
stage-1 events; 61 Vir survives at exactly the 5.96 / 5.65 the results table
quotes. The generator asserts that the **ring** moves more than the star,
because the geometry acts on the ring and the star follows only through the
shared noise scale; a reversal would falsify the mechanism the text describes.

★★ **The referee's `\CampUnOneT` = 6.16 was not a stale literal but a
pre-repair record**, and the consequence is larger than the number: the
external calibration sample was scored on **2026-09-17**, before the repair,
so **its measured tail rate is a pre-repair tail rate.** Because the repair
*removes* outliers, that rate is an upper bound on the post-repair one, and
the appendix now says so and uses it only in that direction. Table 28(b) is
rebuilt as the before/after table above, generated from the two exports.

★ **The clustered and Poisson tail probabilities are identical because they
agree**, not because one was copied: at this mean the block-clustered
convolution and the Poisson tail coincide to three significant figures and
`v352_calc.py` asserts it. The text now states that.

## 4. New gate: every integer in running prose (`intsweep.py`)

The referee asked for "an assertion covering every integer quoted in running
text, not only the 41 headline numbers". `prosenum_v399.py` is deliberately
narrow — a handful of phrase patterns — which is exactly why the stale
13/4 version survived it.

`intsweep.py` enumerates **every** integer literal in the manuscript's running
prose (comments, math, tabular bodies, `\texttt` identifiers, structural
arguments and the bibliography removed; captions **kept**) and requires each
distinct value to be registered in `intsweep_registry.json` as either

- `"macro": "<Name>"` — and the gate asserts the macro's **current** value
  still equals the literal, or
- `"literal": "<why>"` — a year, a band number, a star name, an ITU
  allocation edge, a design constant, with the reason recorded.

**79 distinct integers, 79 registered, 0 problems.** The useful finding is
that none of them silently duplicates a survey count — the prose already uses
macros — with one exception the gate caught on its first run: *"The 112 Band 3
windows searched here"* was a catalogue quantity written as a literal. It is
now `\NWinBandThree`, generated.

★ All three failure modes were demonstrated: an unregistered integer, a macro
that moved, and a macro that no generator defines.

## 5. Two systematics that must be stated together (D11, D6, D7)

- **`exposure_v404.py` (round 83).** The field-truncation defect discarded
  **19.1 h** of in-beam on-source time out of ~30 h available across **42
  blocks / 171 windows / 18 stars**, 6.8 per cent of the survey, with a median
  flux penalty of **1.73×** (3.0× in EIRP) and a worst case of 2.83×. In the
  opposite direction, `n_int × median(Δt)` over-counts: **486 of 1938**
  released windows fall by more than 1 per cent under the exact computation
  and **0** rise, taking the total from **279.0 → 260.5 h** (the aggregation
  that reproduces the published 280.3 h) and 272.2 → 259.3 h on the other,
  i.e. **−12.9 to −18.5 h**. ★★ *The survey's exposure is right by accident,
  to within +0.6 to +6.2 h.* Both signs are in the same paragraph, and the
  generator **asserts** that they are of opposite sign and comparable size, so
  a future input that broke the cancellation would stop the build rather than
  print a reassuring number. The whole of D1's ledger is reproduced from the
  frozen audit product plus the released catalogue — 19.1 h, 171 windows,
  18 stars and the 280.3 h total all fall out exactly.
- **`parallax_v404.py` (round 84).** The extractor phase-rotates to each
  star's *barycentric* direction, so the annual parallax is omitted. Measured
  over 1654 windows: loss **0.13 %** median, **2.98 %** at p90, **32.4 %** at
  p99, **51.5 %** worst, **76** windows above 10 per cent. **Stated, not
  applied**: correcting it moves the median per-system P90 from 2.91 to
  2.93 × 10¹⁵ W (**+0.69 %**) and leaves the count of systems reaching 10¹⁵ W
  unchanged at 14, because a long-baseline block is never a system's best
  window. ★★ Two things about the *direction* are explicit: the sign is
  **optimistic**, every limit being too deep by 1/(1−loss) in its own window;
  and **the completeness campaign is blind to the term**, because its tones
  are deposited at the same assumed position the estimator evaluates at —
  *the third instance in this project of a validation being insensitive to the
  error it exists to catch.*
- **D7, `sec:absscale`.** The one available external check: our extractor
  returns 98–99 per cent of Burton (2024)'s Ross 154 flare amplitudes (ACA,
  0.04–0.05 beams of displacement) and **81–82 per cent** of
  MacGregor et al. (2020)'s AU Mic ones (12 m, 0.245 beams) — the pattern a
  positional error predicts and no other candidate does. ★ **The honest
  qualification is printed**: over the **17 real 12 m configurations** whose
  dirty beam was measured the prediction is **0.89 (0.86–0.93)** against
  0.81–0.82 observed, so parallax accounts for about **58 per cent** of the
  deficit, leaving **7–8 per cent**. The wording is therefore *"bounds any
  further systematic in our absolute flux scale at roughly the 10 per cent
  level"* and **not** "no room for a second term". The generator asserts
  `0 < residual < 0.10` and `0.4 < fraction < 0.9`, so neither the softened
  claim nor the identification can outlive the measurement.
  Glenn's AU Mic letter is cited for the star (`White2026`); **nothing is said
  about its own flux scale.**

## 6. R1-9, inverted: stellar flares excluded by measurement

Referee 1 asked for the stellar-activity discussion to be cut to one sentence
on the ground that the events fail localisation. **That premise is void** —
40 of the 50 fitted crossings localise — so on the referee's own logic
activity becomes the *leading* astrophysical alternative. The discussion is
replaced by `flare_v404.py` (round 85) and the measurement is stronger than
the argument it replaces:

- a flare able to produce a 5σ single-channel crossing must produce a
  **5√N σ** continuum event in the same integrations: **320σ** in a
  4096-channel window, **57σ** in a 128-channel one, and **49–4717** over the
  48 crossings with a recoverable continuum measurement;
- observed continuum Z has **median −0.29** with |Z| < 3 in **45 of 48**, and
  the largest excursion anywhere in those blocks implies at most **0.05σ**
  (median) of single-channel signal;
- ★ one block carries **both** a threshold crossing (T⋆ = 5.27) and the
  published 2015 AU Mic flare. The flare is there in the continuum at
  Z = 10.3; its contribution to the single-channel statistic is
  **0.17σ** (= 10.3/√3840);
- the negative control shows the test has power: β Pic CO at T⋆ up to 30.8 has
  a boxcar maximum of 3.2–4.4 against 3.8–4.2 at its own controls, because a
  steady line is steady.

The generator reads the localisation count out of `ledger_v403.json` and
asserts it exceeds half the fitted crossings, so if the ledger ever returns to
zero localisations this section's own justification goes with it.

## 7. R2-7: the ledgers close

`ledgers_v404.py` (round 87):

- **136 processed = 115 reported + 8 withheld + 13 processed after the
  2026-09-22 export snapshot.** The 13 were not missing; two frozen records
  were cut on different days and the residue was never printed. Asserted as an
  identity.
- **20 versus 17 uncalibrated** are different denominators — 20 over all 177
  in-scope blocks the work list missed, 17 over the 41 of those still
  unsearched — and the containment is asserted.
- **"79 per cent" is not "42 of 82".** Three figures now carry their criterion:
  55 systems (67 %) have >1 *searched* block, 65 (79 %) have >1 *archived*
  block, and 42 (51 %) have searched epochs >1 d apart. Only 76 per cent of
  multi-block systems clear the one-day bar, so extending the search to every
  archived block projects to about **50 systems, 61 per cent** — close to the
  referee's own 63 per cent, reached honestly.
- ★ The prose said "recurrence over years can be tested for fewer than a
  third of the sample" beside 51 per cent. The year criterion is a *different*
  one (23 of 82, **28 per cent**) and both are now stated.
- **The two out-of-sample sets are defined once and distinguished.** The
  hold-out is 77 blocks / 315 windows / 36 stars by hash and sits inside §3's
  block ledger. The external calibration sample is 326 blocks / 1322 windows /
  56 stars, assembled in processing order, **not** a subset of the 656
  in-scope blocks, and must not be added to the 484 processed — which is
  exactly the impossibility the referee spotted. "Pre-registered" was already
  gone (0 occurrences); "reserved by a committed rule" is used throughout.

## 8. BD+05 1668, diagnosed

`fields_v404.py`. **All 4 crossings are in one ACA execution block**,
`A002_Xc7fa6f_X28a8`, of the 25 this star contributes; the 24 sibling
executions of the same field reach **T⋆ = 4.26** and produce no crossing.
In the defective block **512 of 512** control positions exceed T = 5 (median
10.9, max 19.5) against a survey median control of **2.75** over 1480 windows.
The single-integration noise is exactly as predicted (0.1609 vs 0.1611 Jy) but
the residual does not integrate down: jackknife 0.030 Jy against 0.0048 Jy
thermal (×6.3), a flat binned-mean curve, statistic scatter 4.15 instead of 1.
Line emission (off-frequency controls to |Re/σ| = 97.9), a common mode
(channel-to-channel correlation 0.007), a field source (flat in position angle
and radius; absent from 24 siblings) and a signal at the star (star outranked
by 172–448 of 512 in three windows; |Im/σ| tens) each fail separately. Two of
the four sit **8 channels** from a band edge at the identical fractional
position **0.928** in basebands exactly **2.000 GHz** apart — a fixed
intermediate frequency.

★★ **The quality criterion the survey lacked is the MEDIAN of the control
ensemble, not its maximum** (survey median 2.75, p99 4.76; this block 11.20
against 2.60–2.75 for its siblings). It is reported as **diagnostic and
deliberately not adopted as an exclusion**, because a cut strict enough to
remove this block would also remove the HD 48370 CO positive control.

**GJ 273 b** is added to the habitable-zone M-dwarf list, which becomes six
(Astudillo-Defru et al. 2017) — BD+05 1668 *is* GJ 273, so naming it in the
BD+05 paragraph while omitting it there would have been incoherent.

## 9. The rest of the small corrections

- **Title → 60 systems, 114–873 GHz.** `\SurvFreqLoA`/`\SurvFreqHiA` are
  generated from the Class A rows, with an assertion that the Class A span is
  strictly narrower at the low end than the survey span — which is the whole
  reason the title changes.
- **The mask list.** The search ran **15** transitions of 10 species rounded to
  1 MHz; the paper's mask is **17**, adding [C I](1–0) and H30α at v3.46.
  Neither is near a crossing and no nearest-transition assignment changes, so
  it is a documentation matter — stated because one number was being used for
  two objects.
- ★ **A live generator bug fixed at the generator.** The search writes the
  *species* `H2CO` where the mask keys on the *transition* `H2CO(3-2)`, so
  `nl in CAT_OLD` failed and **20 released rows carried an offset in MHz with
  a blank km s⁻¹ column.** Normalised on the unique transition of the species,
  with an assertion that every MHz offset now yields a velocity —
  demonstrated failing.
- **R1-6.** "Primary experiment: Class A drifting spectral-carrier search" and
  "secondary experiment: Class B unresolved spectral-excess search" are named
  where the classes are defined and at the head of Results, with the
  convention stated explicitly: 1655 appears only where it describes the
  archive processed, never as the extent of the carrier experiment, never
  without "403 Class A" beside it.
- **R1-12.** The Conclusions now end on the exclusion statement with the
  archive-selection caveat, in the referee's own form.
- **R1-m3.** "Unresolved spectral carrier" replaces "narrowband" except in
  comparisons with conventional SETI.
- **R1-m4.** The polarisation caveat is consolidated into the main
  limitations; §4's methodology passage now points there instead of repeating
  it.
- **R2-m3.** Figure 1's legend and inset say **Mason+25**.
- **R2-m4.** The frequency-scaled Arecibo-equivalent (~2 × 10¹⁷ W at 230 GHz)
  is named as the physically appropriate comparison, and benchmark statements
  quoted in P_eff or P_trig are labelled instrument-level with the
  ×5.7 (×3.7–5.9) completeness factor stated beside them.
- **CP−72 2713**: its stellar-frame offset from SO 8₈–7₇ is −12.3 km s⁻¹ and
  the 1323 km s⁻¹ reference is labelled as the offset to the nearest *masked*
  transition. (Folded in at v4.03; unchanged here.)
- Appendix A's plain-language summary carried the stale "Thirteen windows …
  the remaining four" **and** the withdrawn claim that neither unattributed
  event is a compact source at the stellar position. Both are corrected.
- Appendix J's unit-less counts ("the four dispositioned windows", "the four
  stage-1 windows", "three of the four") now name their unit and read from
  macros.

## 10. Gates

| gate | result |
|---|---|
| pdflatex errors | **0** |
| undefined references / citations | **0** |
| multiply-defined labels | **0** |
| Overfull boxes | **0** |
| Type-3 fonts | **0** |
| `roundcollide.py` | **79 round files, 79 inputs, 0 problems** |
| `macrosyn.py` | **0 problems** (11 groups, 6 relations, 85 macro files, 9 deferred) |
| `consistency_v399.py` | **0 problems** |
| `prosenum_v399.py` | **0 literals disagreeing with a macro** |
| `macroleak.py` | **0 problems** |
| **`intsweep.py`** (new) | **79 integers, 79 registered, 0 problems** |
| `audit_numbers_v385.py` | **49 PASS / 0 FAIL** (10 WARN, 7 SKIP) |
| `reproduce_from_catalogue_v385.py` | **22 pass / 0 FAIL**, 19 skipped |
| `selftest_v403.py` | 26 checks, **20 demonstrated failing, 0 undemonstrated** |
| **`selftest_v404.py`** (new) | **46 cases, 46 demonstrated failing, 0 NOT demonstrated** |
| `xrefcheck.py` | 121 labels, 0 misplaced |
| **`cleanregen.py`** | **116/116 byte-identical** |

**Page split:** 46 pages — main text **16.62 pp**, back matter 1.07,
appendices 27.76, bibliography 0.28. By the `\label`-anchored count: appendix
starts p. 18, so **main 17 pp / appendix 29 pp**.

**Abstract:** 1743 rendered characters, 276 words (arXiv limit 1920).

Underfull boxes 58, unchanged in kind. Not a gate.

★ `selftest_v404.py` runs each perturbed generator with `cwd` at the version
directory — so every read resolves — and redirects every **write** into a
scratch directory via a shim on `builtins.open`. Copying the directory per
case would have been 135 MB × 46, and a symlink farm would have *truncated the
real products*, because `open(path, 'w')` follows a symlink. The released
catalogue's checksum was verified unchanged after the run.

## 11. NOT IN THIS VERSION

- ★ **The round-7 P90 campaign.** Every $P_{90}$ macro is untouched, as
  instructed. R1-4 (one Class A selection-function figure), R1-5
  (measured vs transferred completeness with counts and transfer interval),
  R2-3 (the localisation test's power by injection; Re/σ against injected
  amplitude and against T⋆) and R2-5 (one injection model, the ladder extended
  to ≥50× the trigger, one Class A multiplier, Table 11 rebuilt, the combined
  systematic including ×0.48–1.35) **all wait on it**. The
  `\SelTransFine*`/`\StratTransferNine*` divergence remains a `macrosyn`
  DEFERRED entry.
- **R1-11 and R2-10's 25-page target.** Deferred by Glenn's directive. Main
  text grew by 1.6 pp in this cycle.
- **R2-10's appendix lettering.** The deletions of the radius-corrected and
  detrended statistics and of Table 24 are corrections and were **not** done
  here — they interact with Appendix C and K, which R2-6 is also rewriting.
- **R2-6.** The catalogue column recording each window's control-annulus
  geometry, and the reconciliation of N_eff ≃ 30–43 against medians 229 (12 m)
  and 13 (ACA).
- **R1-7's mask-width ladder as a generated table.** The measured values exist
  (sky frame 11/10/3/2/2, stellar 3/2/2/2/2 at ±13/20/30/50/100 km s⁻¹) and
  are **not** wired in.
- **R1-8.** Single-epoch detectability and confirmation completeness as two
  explicitly different quantities.
- **Appendix M's clustering test**, which round 8 finds broken three ways
  (grid-respecting null gives p = 1.0000; the right test finds p = 0.0025
  that is entirely the survey's own CO attributions).
- **The 51st visibility fit.** β Pic `Xd9668b_X3a90` landed on the host after
  `visfit_r7_result.json` was cut, and the CP−72 2713 refit is still in
  flight. The ledger's fit input is a **glob**, so both are a re-run and not an
  edit; the paper says 50 fitted / 6 untested.
- **The closure-phase RFI record.** `rfi_ledger_r7.json` exists and is not
  wired into a generator.
- **`visfit_v385_calc.py` and `visgain_v399.py`** are still not retired; five
  `macrosyn` DEFERRED entries name them.
- **R2-m12.** The Zenodo DOI is an author action (Glenn's account).
- **R2-m2.** "Delete statements that all Class A windows are drift-resolving,
  and state how many have η_drift < 1" — not done. §J.3 still contains
  *"every stage-1 flagged window in the survey is drift-resolving"*, which is
  true as written but sits beside the class claim the referee objects to.

## 12. Noticed, out of scope, not changed

- ★ **`\NExoHostsTab` = 19 and `\NExoPlanetsTab` = 42 are understated.**
  `build_ranked_master40pc.py` leaves `is_exo_host` blank for 139 of 168
  census entries and `make_tables_v328.py` counts blanks as non-hosts, so the
  true figures are ≥22 hosts and ≥49 planets. This is the *fourth* instance of
  the hard-coded-prose bug family in this project. Only the §6.5 M-dwarf
  count was corrected here (five → six), because BD+05 1668 forced it.
- ★ **`\HostNMult` = 1 is wrong.** 61 Vir's SIMBAD principal otype is `PM*`
  with 0 parents and 0 siblings; the `**` is inherited from WDS component-A
  rows. `hosts_v399.py:57` tests the aggregated `otypes` bag and should test
  `basic.otype` + `h_link`. Not fixed: it needs a SIMBAD re-query.
- `tab_visibility_v38*.tex` still writes `HD14055` rather than the SIMBAD
  form; `audit_numbers` warns twice.
- Eight figures are built and never `\includegraphics`'d.
- `sec:acalimit` is still a label with no reference, and 22 labels are defined
  but never referenced (a report, not a gate).
- The version folder still carries `.aux`/`.log`/`.out`/`.pdf` from v3.87–v3.90
  and superseded `apply_v3xx_stage*.py`. The deposit is larger than the paper.
- **Disk**: `/workspace` sat at 99 per cent full (3.3 GB free) throughout this
  build. `cleanregen.py` needs no copy, so it ran, but the volume is shared and
  a larger campaign would not fit.

## 13. Frozen round-8 inputs

`r8inputs/` is new and holds the four frozen measurement products this version
reads, each with a `_provenance` string:

| file | what it is |
|---|---|
| `trunc_aff_ebs_v404.json` | the 42 field-truncated blocks with their in-beam field counts |
| `d3_scan_v404.json` | both on-source estimators applied to every surviving product's `times` array |
| `parallax_loss_v404.json` | per-window parallax displacement and dirty-beam loss, the 19-configuration beam library, and the headline recomputed both ways |
| `flare_crossings_v404.json` | the crossings' continuum measurements — **observed quantities only**; every prediction is derived by `flare_v404.py` |
| `fields_v404.json` | the BD+05 1668 block diagnostics and the Sirius B orbit geometry |

Where a number could be recomputed from the released catalogue it is, and the
frozen value is not used: the 19.1 h, the 171 windows, the 18 stars, the
280.3 h total, the 486 moved windows, the BD+05 crossing confinement and the
sibling maximum all fall out of the catalogue and the audit product together.
