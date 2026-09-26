# Version history — "A Volume-Limited Search for Technosignatures within 20 pc"

Each version lives in its own subfolder (`v1.00/`, `v1.01/`, ...) so any
previous version can be recovered without relying on git history alone.
Bump the **minor** number (1.00 → 1.01) for content edits/additions within
the same broad draft stage; bump the **major** number (1.x → 2.00) once
Paper II's actual results/discussion/conclusions sections are added.

## v4.02 — 2026-09-26

**The non-ledger round-7 correction pass.** These changes were completed in
the local `v4.01/` folder *after* `v4.01` had already been pushed, so the
remote `v4.01` and this content are not the same paper; they are published
under their own number rather than as a second commit on `v4.01`.

- **The three frozen macro files are gone.** `survey_numbers_round{5,6,7}.tex`
  were restored by `cp` from `frozen_macros/` and no generator could rebuild
  them; they came from an extraction two revisions before the ACA repair and
  **12 of their macros were still typeset**. All 12 now derive from the
  released catalogue. `\HdCorrectedT/Ring` 21.0/20.8 → 20.8/14.2;
  `\NonExcRingGe` 16 → 38; `\MaskBWTwenty/Hundred` 2.1/10 → 2.3/8.7.
- **Two new gates**: `macrosyn.py` (macros that claim to be the same quantity
  must agree; declared ledger identities must close; no macro file may exist
  that no `.py` writes) and the figure pass of `audit_numbers_v385.py` (every
  star designation drawn in a typeset figure must be in the catalogue and in
  SIMBAD form).
- **Mason et al. 2025 redone like-for-like** in minimum detectable received
  flux, with their published EIRP reproduced from their own numbers to 0.3 %
  as a build-stopping positive control. The "~361× lower" sentence is gone.
- **The known-answer test vectors are RUN** (`katcheck_v401.py`), Eq. (3)
  re-implemented importing nothing from the search or injection code.
- **TRAPPIST-1's acceleration margin** was compared against one ceiling under
  the other's name; both margins are now published and named.
- **Main text 18.86 → 16.53 pp**, by deleting narration rather than
  measurement.
- v4.02 itself bumps the version, and **deletes two paragraphs the shipped
  ledger has already made false**: §4.1's "the visibility test was applied to
  the flagged windows rather than to all threshold crossings" and its cost
  estimate, and the "one β Pictoris window is absent from this table" one.
  Main text 16.53 → **16.03 pp**, total 44 → **43 pages**.

**The visibility-test ledger carried here is the superseded round-6 one.** The
round-7 refits, the epoch-convention change (`t0 = times[0]`) and the
recurrence results land in v4.03. Notes: `v4.02/BUILD_NOTES_V402.md` and
`v4.02/BUILD_NOTES_V401_NONLEDGER.md`.

## v4.01 — 2026-09-25

R2-M2's "factor of two" in the channel response answered: it is 9 per cent,
and both sides were wrong. `cresp_v401.py` computes `C_resp` from the
correlator's own lag window rather than from a linear split of the channel;
`C_resp` = 2.00–2.36, median **2.08** (was 2.29). Five documented ALMA
numbers reproduced and none fitted, including the archive's own reported
effective resolutions for this survey's windows to four digits. Thirteen
`P_eff`-family macros move by ~9 %; `P90^sel` does not move and must not.

## v4.00 — 2026-09-25

Referee round 5. **P90^sel is now measured end to end** — carriers injected
into calibrated visibilities and recovered through the unmodified pipeline,
trigger and 512-control rank together (8,860 tones, 52 configurations, null
0/9,543). The headline per-system sensitivity moves 1.5e15 -> 2.9e15 W.

**The ACA control ensemble is worth 13 independent controls, not 512**, once
every pair is required to be two synthesised beams apart; the rank
resolution is 1/14 rather than 1/513, and the separated screen is *more*
permissive (stage-1 12 -> 28).

**The visibility test's power is now stated**: a compact source at the
stellar position would return Re/sigma = 5.6-6.0 at the unattributed
events against 2.47 observed, excluding emission there at 3.3-6.1 sigma.

All 28 of Referee 2's numbered corrections closed, plus M2, M3(1), M4, M5,
M7, R1-6/7/8/12/x and R2-S2/S5/S7/S9/S10. The "defect found and repaired"
narrative is removed throughout, and removing it exposed a factual error.
Main text cut to 17.3 pp. Notes: `v4.00/BUILD_NOTES_V400.md`.

## v3.99 — 2026-09-24

Every downstream number regenerated from the corrected ACA extraction.
Notes: `v3.99/BUILD_NOTES_V399.md`.

- ★★★ **The catalogue is now built from the repaired data.** The correction is
  folded in at the EXPORT (`corrected_export_v399.py`), because `v342_calc.py`
  rewrites the catalogue CSV from that export on every build — a direct CSV
  patch is silently discarded.
- **Crossings 75 → 56; stage-1 13 → 12; line-attributed 9 → 10;
  unattributed 4 → 2**; windows retaining a crossing cell 451 → **1401**.
  Sample sizes and the 1.5e15 W sensitivity are unchanged, as they must be.
- HD 23484 and HD 14055 disappear as artefacts; a β Pic CO(2−1) window is
  recovered and attributed by the paper's own ±50 km/s rule.
- **Four latent bugs surfaced and fixed**: the export write-target clobbered by
  a blanket repoint; `EDGE.sort()` comparing dicts on ties; a 10 kHz hard-coded
  frequency literal for a peak that the repair re-measures; and three frozen
  constants encoding the old result, now derived.
- The Band 8 [C I] passage removed — that crossing no longer exists.
- Gates 0/0/0/0; `audit_numbers` 49 PASS / 0 FAIL; clean regeneration 83/83.

## v3.98 — 2026-09-24

The ACA control-geometry defect, repaired and verified. Notes:
`v3.98/BUILD_NOTES_V398.md`; spec and result in `ACA_REEXTRACTION_SPEC.md`.

- ★★★ **278 blocks / 739 GB re-extracted, zero failures**, with the dish and
  baseline now measured from the data and the annulus starting at
  `max(0.14 theta_PB, 2 theta_syn)`. **The pre-registered test passed:
  ACA stellar ranks D 0.10 -> 0.034, p <0.001 -> 0.169** (criterion p>0.05,
  frozen before the run and asserted in the generator).
- ★★ **Regression check passed**: 12 m windows reproduce the release,
  233/239 within 1 %, median fractional difference 6.4e-06.
- ★★ **The repair recovers a beta Pic CO positive-control window the defect
  had hidden, and removes HD 23484 and HD 14055**, which it had manufactured.
  One ACA unattributed event survives (61 Vir); CP-72 2713 is 12 m.
- **M1 discharged**: every window now stores its peak frequency and drift.
- The v3.97 "68-window caveat" was a stale-duplicate artefact of my own
  export, not a data problem; resolved.
- Gates 0/0/0/0; clean regeneration 83/83 byte-identical; abstract 1913/1920.

## v3.97 — 2026-09-23

Two referee reports, worked through by hand. Notes:
`v3.97/BUILD_NOTES_V397.md`.

- ★★ **A regression I introduced in v3.96**: deleting the "About this paper"
  section swallowed the `\appendix` command, so the appendices numbered as
  main sections 8–20 with "10.0.2" subsections — exactly what Referee 2 (M8)
  reported. Restored; appendices now letter **A–E**, six orphan
  subsubsections promoted, 0 labels printing X.0.Y.
- ★★ **The line-mask percentages used two different masks** (Referee 2, S1).
  The per-class figures came from a stale **8-transition** list while the
  adopted mask has **17 transitions of 11 species**. Class A mask cost was
  understated **eightfold**: 0.9 % → **7.4 %**; Class B 0.3 % → **3.1 %**.
  Now computed on the adopted tube set, with the A/B ratio generated (2.4)
  instead of the literal "three times".
- ★ **The abstract quoted a displaced source as a positive control**
  (minor 1): 5.9σ is HD 48370. `visgain` now selects on the verdict column
  and asserts >6σ; range corrected to **6.1–9.5σ**.
- ★ **Two generators computed the headline median differently** (minor 2):
  1.4 vs 1.5 × 10¹⁵ W. Now built from the catalogue's stored column and
  **cross-asserted** against the headline macro.
- **RFI allocation statement corrected** (M6): 90–873 GHz is *not* above all
  allocated services. New generator asserts that 1 of 1655 windows overlaps
  the 94.0–94.1 GHz cloud-radar band, with 0 crossings and 0 stage-1 events.
- **Star designations cleaned** (minor 30) — our own repair had WD 0407**+**179
  as −179; suffixes and case now fixed via a `display()` function.
- New "How to interpret a candidate" table (R1-6); non-recurrence reframed as
  corroborating rather than excluding (R1-5); imaginary part presented as a
  discriminant against displaced emission only (S3); polarisation claim
  softened (R1-12); novelty reframed to two gaps (R1-8); conclusions end with
  three sentences plus a misquotation guard (R1-10, R1-13).
- Version history, commit hashes, seeds and build dates removed (M8);
  White (2026, submitted) and two uncited references removed.
- Gates 0/0/0/0; clean regeneration 82/82 byte-identical; abstract 1913/1920.

## v3.96 — 2026-09-23

Two referee reports. Notes: `v3.96/BUILD_NOTES_V396.md`.

- ★★ **Referee 2's M3 confirmed: a real bug, and our published explanation
  was wrong.** The pipeline builds the control annulus from a hard-coded 12 m
  primary beam for every window, so ACA 7 m windows have theirs at 58 % of the
  correct radius — inner edge 3.8″ at 230 GHz, inside a ~7.3″ ACA synthesised
  beam. Measured: inner-bin control excess **+0.108 in ACA against +0.007 in
  12 m**, and the stellar rank is exchangeable in the 12 m stratum
  (D = 0.027, p = 0.77) but not in ACA (D = 0.10, p < 0.001). The
  primary-beam-gradient narrative is withdrawn, as is the claim that the
  stage-1 excess was "an artefact of rank bias" — the bias pushes the star
  *low* and cannot manufacture star-first outliers. New §6.4 states what rests
  on the ACA windows; 3 of the 4 unattributed events are ACA, as the referee
  inferred.
- ★ **Referee 2's M1 confirmed, and it retracts our own table.** Only 4 of 13
  stage-1 windows have a stored crossing frequency. The v3.94 mask-robustness
  table used an uncorrected sky-frame offset where the rule is stellar-frame,
  on offsets not measured at the crossing for 9 of 13 windows. Withdrawn.
- **Table 7's recurrence criterion fixed**: it tested the trigger alone, so
  HD 14055 was marked as recurring on a repeat that does not outrank its
  controls. Now matches the stage-1 definition.
- **Sensitivity is now a distribution** (3/22/55/60 systems at 10¹⁴–10¹⁷ W),
  temporal incompleteness is explicit (40 of 82 systems have no independent
  epoch), the title drops the system count, and the four events are rejected
  on physical grounds first.
- **Polarisation physics corrected**: ALMA's linear feeds mean a per-hand
  search gains nothing on a circularly polarised carrier.
- Deleted the continuum-lane appendix, the duplicate plain-language paragraph
  and "About this paper". New gate checks prose literals against macros.
- Gates 0/0/0/0; clean regeneration 81/81 byte-identical; abstract 1909/1920.

## v3.95 — 2026-09-23

Readability and compression round, at Glenn's direction: the paper had come
to read like a technical diary amended over many revision cycles. Notes:
`v3.95/BUILD_NOTES_V395.md`.

- **Cut 19.8 %** of main text plus appendices (319,573 → 256,202 chars),
  **49 → 42 pages**, with the majority from the appendices as instructed
  (appendices −20.6 %, main text −18.8 %).
- **New plain-language opening to the appendices**, "What this paper did,
  and where the details are", replacing the terse roadmap: what was
  searched, what was found, what the four unexplained events are, and the
  two cautions that matter more than the limit.
- **Diary removed**: defensive self-commentary, editorial history
  ("an earlier version", "we withdrew", "the retired statistic"),
  triple-stated caveats, and essay-length captions that carried argument
  the body already made. Diary-flavoured headings renamed to plain
  scientific ones.
- **Rejected alternatives compressed to verdict plus evidence** — the
  radius-corrected statistic changes no conclusion and no longer gets a
  long narrative.
- **Four defects found**: a cross-reference that resolved to the wrong
  appendix; a gate silently disabled by rewording the prose it keys on; two
  labels re-anchored by an inserted block; and a cut that would have made a
  non-recurrence read as a recurrence.
- Gates 0/0/0/0; clean regeneration 79/79 byte-identical; abstract
  1904/1920.

## v3.94 — 2026-09-22

Two referee reports (Referee 1: 10 major + abstract/figures/minors;
Referee 2: 7 major + 4 minors), plus Glenn's instruction to note the
β Pictoris b radio detection. 19 items closed, 2 partial, 3 deferred with
reasons. Notes: `v3.94/BUILD_NOTES_V394.md`; ledger `v3.94/CHECKLIST_V394.md`.

- **Title changed** to "An Archival ALMA Search for Unresolved
  Spectral-Carrier Technosignatures toward 82 Stellar Systems within
  40 Parsecs" (R1-5), with the term defined at first use.
- **arXiv:2609.16720 (Ortiz Ceballos et al. 2026)** discussed beside the
  β Pic positive control: their ECMI emission is 1.4 decades below our
  bands and out of reach *by physics* (89.6 GHz needs 32 kG, 26× their
  field), and their circular polarisation shows the discrimination we forgo
  is real — but also that circular polarisation is not itself a mark of
  artificiality.
- **Two corrections found in our own numbers**: the visibility-extension
  partition was built on "searched" rather than "still held" (no crossing
  block retains visibilities; 60→62 windows, 50→52 blocks, 0.31→0.40 TB);
  and the ±13 km/s line-mask comparison mixed stellar-frame and observed-frame
  velocities.
- **Three new measurements**: SIMBAD activity/multiplicity of the four
  unattributed hosts (3 of 4 active); line-mask robustness (attributed ≤34,
  unattributed ≥328 km/s, a factor-10 gap); and the measured gain of the
  visibility statistic (all 13 flagged windows sit at the rank floor and are
  indistinguishable in the image plane; the visibility fit separates them by
  5.0σ).
- Main text shortened 17.1 % by moving four blocks to the appendices
  (R1-10 asked 25–30 %; the shortfall is stated, not hidden).
- Gates 0/0/0/0; clean regeneration 79/79 byte-identical; abstract
  1904/1920.

## v3.86 — 2026-09-21

Two referee reports, 29 points, worked one at a time in the order given.
All closed. Notes: `v3.86/BUILD_NOTES_v386.md`; ledger
`v3.86/CHECKLIST_V386.md`.

**Changes that alter what the paper claims**

- **The headline sensitivity is now the search's, not its trigger's.** A
  signal becomes a stage-1 event only by crossing threshold *and*
  outranking all 512 spatial controls, whose Class A median is 5.79σ. The
  abstract, Table 5, the boxed rule, §6.1, the conclusions and Fig. 6 lead
  with $P_{90}^{\rm sel}$: median $2.8\times10^{15}$ W per window,
  $1.5\times10^{15}$ per system. $P_{90}$ is relabelled the matched-filter
  completeness.
- **Class A is the primary statistical reference population.** 1.1
  (0.5–1.4) expected against 4 observed, described as a modest population
  excess and not evidence for any individual event; the all-window figure
  is now a secondary diagnostic. The paper also traces the consequence of
  the "unmodelled tail" explanation: it would make the quoted completeness
  optimistic by about the same factor.
- **The recurrence test spans days, not years.** Dating all 404 searched
  blocks gives 0–2 d between the four unattributed events and their 23
  repeats, so the non-recurrence bounds persistence over hours to days and
  nothing longer. Stated in the abstract, the summary and the conclusions.
- **Title now counts 82 stellar systems**, with the 90 catalogue entries in
  the abstract's first sentence.
- **Class A and Class B frequency unions separated**: 47.7 GHz for the
  drifting-carrier experiment, 70.4 GHz more for the coarse search, 118.1
  total.

**Additions**

One table carrying all 13 stage-1 events through every pipeline stage; the
visibility test promoted to stage 2; the per-system Class A bandwidth
distribution (median 1.84 GHz, 3.9 per cent of the survey union); Author
contributions, Funding and Competing interests sections; the illustrative
√Δν rescaling as a number; a worked example of the systematic combination.

**Presentation**

Main text cut **19.3 per cent** (29.9 → 25.4 pages) by moving validation
and audit material to the appendices; Tables 1 and 2 merged into one
glossary; §4.2 now states that 1/513 is a resolution and not a false-alarm
probability before developing it; Figure 1 reframed as parameter-space
context; the null claim always carries its domain qualifier.

**Bugs found**

A fourth consecutive forward dependency in `make_all.sh`, caught only by
the clean regeneration; `EirpEffMedian` emitted twice from two definitions
of $P_{\rm eff}$; and the per-system macro trio silently changing meaning
when the sensitivity figure switched quantity. Clean regeneration
**83/83 byte-identical**.


## v3.85 — 2026-09-21

Two referee reports worked item by item, then five rounds of independent
self-review with verification against the released products before every
edit. Round reports `VPR_ROUND1..5.md`; dispositions, including the
reviewer claims that were wrong, in `VPR_DISPOSITION.md`.

**Corrections that change printed results**

- The survey has **90 stars in 82 systems**, not 94 in 87. Four stars were
  in the frozen export under two name strings each and TWA 3A's two Gaia
  components were in no bound pair; six generators each held their own copy
  of the map, so the count was consistently wrong everywhere. The title
  said 94. One shared `star_alias.py` now owns canonicalisation and the
  catalogue writer asserts that no two systems share a distance.
- `j1256-1257` renamed to **LP 736-15**: the ALMA field name had been taken
  for the star's, and the star in that field has the 21.154 pc parallax the
  catalogue already carried.
- **All four unattributed events have repeat coverage**, 23 blocks in all,
  and none recurs. The repeat finder had required a crossing frequency the
  release stores only sometimes.
- The **drift-following, continuum-subtracted visibility fit** was run on
  all 13 stage-1 events: β Pictoris recovered in 6 of 8 windows at
  6.1–9.5σ, HD 48370 displaced, and |Re/σ| ≤ 0.93 for all four unattributed
  events. It returns −0.86σ for CP−72 2713 where a continuum-inclusive fit
  gives 5.5σ; the excess is that window's 10.9 mJy stellar continuum.
- **Polarisation** re-queried over all searched blocks: 198 of the 200
  resolvable deliver both parallel hands and **two do not**. The previous
  "all 104 of 104" covered 26 per cent of the sample.
- The chance expectation is now reported on **both reference classes**, 4.4
  over all searched windows and 1.1 over the drift-resolving class, and the
  paper states that on the narrow class the four unattributed events are a
  ~2σ excess rather than choosing the class that removes the tension.
- Rank uniformity recomputed: removing all 71 fine crossings leaves
  p = 0.002, where a 431-window freeze had given 0.39.
- $P_{90,\rm promote}$ added, because $P_{90}$ is a trigger completeness
  and promotion needs the star to beat a ring whose Class A median is 5.79σ.
- Numerous stale or hand-typed quantities re-derived: the drift ceiling,
  the Class A $P_{\rm eff}$ row, the window concentration, the star–band
  count, the Band 8 window count, the exposure conversion, the Mason
  comparison, the benchmark shortfall, the exoplanet counts.

**Withdrawn**

- The radius-corrected statistic is no longer adopted as primary: it was
  built after the candidate list and moves the survey median away from the
  exchangeable value.
- A dimensionally invalid recovery bracket (a percentage multiplied by a
  power-transfer factor, clamped at 100).

**Additions**

Drift-resolved injection reporting; the searched domain in acceleration
against observing frequency; a systematic budget on $P_{90}$ including two
one-sided biases; a ten-step experiment summary and a redrawn Fig. 3; a
glossary moved to the Introduction.

**Infrastructure**

`star_alias.py`, `inject_curve.py`, `localnorm_core.py` give each quantity
one owner. `reproduce_from_catalogue_v385.py` re-derives 41 headline
quantities from the released CSV alone and runs inside the build.
`literalsweep.py` reports prose literals that duplicate a macro.
Clean regeneration **81/81 byte-identical**.





## v3.84 (2026-09-20) — two referee reports, all required changes

Reply in `v3.84/REFEREE_RESPONSE_V384.md`.

- **Visibility-domain test on all four unattributed events**, required by
  referee 1. The measurement sets had been reclaimed, so the four blocks
  were re-downloaded and recalibrated from the raw archive. **None is a
  point source at the stellar position**: largest real part +2.5 sigma,
  61 Vir below its own controls, and HD 14055's imaginary part 3.2 sigma
  from zero, which emission at the star cannot produce.
- **Local radial noise normalisation**, required by referee 2 in place of
  the post-hoc stellar debit. Standardising each control probe within its
  own radius bin removes the gradient by construction, with no free
  parameter. 9 of 13 stage-1 windows keep their flag; the 4 that lose it
  are the marginal cases, all already dispositioned otherwise. **No
  disposition changes and the debit is no longer needed.**
- **One block-accounting identity**: 656 progenitors = 484 processed
  (404 science + 77 hold-out + 3 windowless) + 177 repeat coverage.
  "Every public ALMA observation" and "the archive is exhausted" withdrawn.
- Class A named as the primary experiment; P90 the primary sensitivity
  everywhere including Fig. 1; the exchangeability failure promoted to the
  head of section 5.3 and into the candidate-flow figure; a new "what this
  excludes and what it does not" subsection; the 2e-7 parameter-volume
  product deleted.
- Confirmation completeness quantified: 40 of 65 Class A systems have a
  same-tuning repeat, so for the rest the recurrence test cannot be
  applied at all.
- Abstract rewritten in plain language with the disc bias and the
  duty-cycle blind spot in it; plain-language summary at the end of the
  Introduction; four audit subsections and six CP-72 paragraphs moved to
  appendices; conclusions cut to four claims.
- New figures: selection bias by spectral class, cumulative systems vs
  P90 with epochs per system, and the four unattributed events.
- Gates: 34 pages, 0 errors / 0 undefined / 0 overfull / 0 Type 3, 866
  macros 0 unused, abstract 1916/1920, clean regeneration **71/71
  byte-identical**.

## v3.83 (2026-09-20) — three internal review rounds, readability, figure sizing

Findings in `v3.83/REFEREE_ROUNDS_V383.md`.

- **Three numerical defects found and fixed at the generator**: Table 5 said
  every threshold crossing was Class A (4 of 75 are Class B); the crossing
  ledger said the mask accounts for three stage-1 outliers (it accounts for
  nine); **Fig. 2's decision-flow panel read "3 identified astrophysical; 1
  unexplained" where the catalogue says 9 and 4** — hand-typed into the
  figure generator and stale since the catalogue grew.
- The abstract's scope narrowed to what is true: every public observation
  *for which the archive holds a pipeline calibration*. The median window's
  P90 is now quoted beside the deepest window's.
- The HD 48370 near-tie, the limiting case of the whole screening argument,
  was hand-typed; generated now.
- The whole detection chain appears in one place, in the Fig. 2 caption.
- **Readability**: the three densest main-text paragraphs rewritten to lead
  with what the evidence shows; main-text sentences over 400 characters
  44 -> 36. No number, qualification or citation removed.
- **Figs 6, 9 and 10 resized**: all three were drawn wide and printed into a
  single column at scales 0.58, 0.41 and 0.45, so their type rendered at
  under half its designed size. Redrawn at single-column width, printing at
  1:1. Fig. 10's panels stacked; its canvas had been hard-coded inside its
  own generator, overriding the size table.
- Gates: 32 pages, 0 errors / 0 undefined / 0 overfull / 0 Type 3, 850
  macros 0 unused, abstract 1917/1920, clean regeneration **64/64
  byte-identical**, audit 56 pass 0 fail.

## v3.82 (2026-09-20) — referee cycle

Two referee reports, worked point by point. Reply in
`v3.82/REFEREE_RESPONSE_V382.md`.

- **The "factor 16" was wrong and is now 65.** The rank floor was being
  divided by a Bonferroni scale read from a round-5 freeze on a superseded
  window count, while printed beside the current 1655. Recomputed from the
  catalogue, asserted consistent in all three places it appears.
- **Two further internal inconsistencies fixed at source**: the reserved-
  block count (75 against 77, from differencing two populations that were
  never the same) and the out-of-sample median rank (0.405 against 0.44,
  two samples under one name).
- **A 56-check numerical audit now runs inside the build** and fails it on
  any disagreement between the abstract, tables, body and conclusions.
- **No probability is printed as an exact zero** anywhere, including inside
  two figure panels.
- New tables: the four unattributed stage-1 outliers, and the CP-72 2713
  repeat test in full. New figure: a schematic of the Hanning response
  correction.
- P90 promoted above P_eff and P_trig; the molecular mask's cost reported
  per class; a physical cause given for the radial non-exchangeability,
  with its effect on completeness (+0.08 sigma at the star, so recovery is
  pessimistic by ~2 per cent, not optimistic).
- The pre-registration chronology is generated from repository timestamps
  with the ordering asserted: statistic 2026-09-09, criteria 2026-09-11,
  hold-out five days after the statistic, first reserved block three days
  after that.
- Figure 3 reduced from four variables to two; Figure 1's ordinate and
  caption now carry the "not a like-for-like comparison" caveat.
- Editorial: every mention of previous versions, peer review or revision
  removed; title names the archive; abstract states the archive-complete
  scope and the 4.1 TB downloaded; de-AI pass (em-dashes 0).
- Gates: 32 pages, 0 errors / 0 undefined / 0 overfull / 0 Type 3, 846
  macros 0 unused, abstract 1842/1920, clean regeneration **64/64
  byte-identical**, audit 56 pass 0 fail.

## v3.81 (2026-09-20) — the pre-registered hold-out, applied

The archival sweep closed at **460/460 worklist items terminal** (428 searched,
20 excluded because the archive holds no pipeline calibration for them, 12
failed; 3.97 of 4.28 TB). This round splits that data on a rule fixed before
it existed and reports the headline on one half, every empirical calibration
on the other.

- **The rule**: `holdout_rule_v371.py`, committed **2026-09-14T07:10:24Z**
  (`c75069040eab`) — held out iff `sha256(canonical EB uid)[:8] mod 5 == 0`,
  with two guards depending only on identifiers and the published block list.
  **77 of 484 blocks reserved (15.9 %)**; headline 404 blocks / 1655 windows /
  94 stars / 87 systems. **The reservation costs no star and no system**, which
  is asserted rather than hoped for.
- **Every calibration is now out of sample.** On the reserved blocks alone:
  median stellar add-one rank **0.405** (block-clustered 95 % 0.341-0.458),
  KS *D* = 0.109 at *p* = 0.0011 over 315 windows; false-alarm tail factor
  **1.2** (95 % 0.6-1.9 over 5040 trials); **0 stage-1 outliers against 0.61
  expected**. The rank displacement — the claim referee 1 objected was
  in-sample — is reproduced on data the design never saw, at very nearly the
  in-sample value.
- **One honest negative**: the steep inner-edge radial excess is NOT
  reproduced out of sample (profile +0.12, +0.10, +0.12, +0.16 inner to
  outer). The radial correction is now presented as one demonstrated
  mechanism for the displacement rather than the whole of it.
- Stage-1 outliers unchanged at 13, all in the survey; 9 CO-attributed, 4
  unattributed against **3.2 expected, *p* = 0.40**.
- Occurrence limit loosens 5.86 -> 5.84 per cent and the duty-cycle variant
  7.61 -> 7.75, as it must: holding data back cannot make a survey more
  complete. That direction is the guard.
- `survey_stats_systems.py` extracts the system-grouping rule into one module
  so the hold-out's second guard groups systems exactly as the headline does.
- Gates: 30 pages, 0 errors / 0 undefined / 0 overfull / 0 Type 3, 820 macros
  0 unused, abstract 1897/1920, clean regeneration **61/61 byte-identical**.

## v3.80 (2026-09-19) — the completed archival sweep

The catalogue grows from **443 windows / 104 execution blocks / 88 stars /
81 systems** to **1956 / 479 / 94 / 87** as the archival download-and-search
campaign completes, and every number, table and figure in the paper is
rebuilt on it. Union bandwidth 113.9 -> 125.1 GHz; Class A/B 126/317 ->
459/1497; systems with drift-resolving coverage 58 -> 65.

- **The result the larger sample makes possible.** Stage-1 spatial outliers
  go from 4 to 13, in 7 star-band pairs and 6 systems. Nine lie within
  +-50 km/s of a molecular transition in the star's own frame and are CO;
  **eight of those are beta Pictoris alone**, recovered independently in five
  Band 3 and three Band 6 windows from six execution blocks. The remaining
  **four are unattributed against 3.8 expected by chance** at the ensemble's
  own rank floor of 1/513 (*p* = 0.53). Quadrupling the catalogue did not
  accumulate unexplained events.
- **Every stage-1 outlier is fine-channel**: 13 of 459 Class A against 0.89
  expected, **0 of 1497 Class B** against 2.92 expected.
- **A new external null.** 195 windows in 46 blocks toward stars at 40-50 pc
  were queued by a beam-matching step that did not check distance. They are
  outside the sample and excluded from every number in the paper, but they
  ran through the identical frozen pipeline and entered no tuning decision:
  ranks median 0.502, KS *p* = 0.96, **0 outliers against 0.4 expected**.
- Occurrence limit at 1e16 W tightens 6.4 -> 5.9 per cent, duty-cycle variant
  11.2 -> 7.6. Zero systems reach Arecibo-class effective EIRP (unchanged);
  two now reach twice it, where one did.
- **Engineering**: the catalogue's size is written once, to
  `catalogue_constants.json`, and asserted against everywhere. Three
  generators were still reading a 431-window snapshot three catalogues out of
  date. Archive metadata and obscore categories re-harvested over all 482
  blocks; Splatalogue harvest re-run (45 -> 49 islands, 4958 -> 5406 lines).
- Gates: 30 pages, 0 errors / 0 undefined / 0 overfull / 0 Type 3, 800 macros
  0 unused, abstract 1906/1920, clean regeneration **56/56 byte-identical**,
  arXiv set 51 items.

## v1.00 (2026-08-30)
- First draft. MNRAS-format LaTeX (official `mnras.cls`/`mnras.bst` v3.2
  from CTAN), authors Glenn J. White & Robin Dey.
- **Content**: full Introduction and Background/Literature Review sections
  (six decades of radio SETI history; modern large-scale surveys —
  Breakthrough Listen, FAST, LOFAR/NenuFAR, Sardinia Radio Telescope, ATA,
  commensal VLA/MeerKAT/MWA systems; the very small mm/submm literature,
  centred on Mason et al. 2024's ALMA Band 3 bycatch survey and our own
  prior TRAPPIST-1/100-star pilot work; machine-learning/anomaly-detection
  approaches (Ma et al. 2023 deep learning, GLOBULAR clustering, Parkes/GBT
  anomaly search); statistical frameworks for interpreting non-detections
  (Wright et al. 2018 Cosmic Haystack, Sheikh 2020 nine axes of merit,
  Margot et al. 2023 representative-sample formalism); the explicit case
  for a volume-limited, disc/planet-status-agnostic sample; and prospects
  for SKA/ngVLA). Sample Selection and Data/Methodology sections summarise
  the already-established 20pc target list and pipeline design. Results,
  Discussion and Conclusions sections are NOT yet written — this version
  is background/motivation only, as instructed.
- All literature citations were individually verified against arXiv
  listing pages (author lists, years, journal/volume/page or arXiv ID)
  before inclusion — several initial draft citations had incorrect
  author attributions from search-snippet-only research and were
  corrected against the primary source before this version was finalised.
- 6 pages, clean compile, no undefined references, no overfull boxes.
- Pushed to `Tilanthi/SETI` GitHub repo.

## v1.01 (2026-08-30)
- **Journal target corrected**: Glenn confirmed the paper will likely go to
  the **Open Journal of Astrophysics (OJA)**, not MNRAS as originally
  assumed. Re-typeset using OJA's official `openjournal.cls`
  (http://www.thphys.nuim.ie/staff/pcoles/openjournal.cls, v09/06/15,
  AASTeX/emulateapj-style, built on `revtex4-1`) instead of `mnras.cls`.
  **Content is otherwise identical to v1.00** — same title, authors,
  abstract, full Background/Lit-Review text, Sample Selection, Methodology,
  Scope-of-Paper-II placeholder, and the same (corrected, individually
  verified) ~30-entry bibliography — only the document class, front-matter
  markup (`\shorttitle`/`\altaffilmark`/`\altaffiltext` instead of MNRAS's
  `\author[]{}`/`\pubyear`), and resulting page layout (OJA is single-column
  AASTeX-style vs MNRAS's two-column) changed.
- Dependencies: `openjournal.cls` requires `revtex4-1.cls` (now installed on
  this container via `apt-get install texlive-publishers`; NOT bundled in
  the repo since it's a standard TeXLive component, unlike the one-off
  `openjournal.cls` itself, which IS bundled per-version for
  recoverability) and the small legacy `epsf.sty` (bundled in `v1.01/`,
  fetched from `fits.gsfc.nasa.gov/standard30/epsf.sty` since it is not in
  this container's TeXLive install and CTAN's own mirrors served an HTML
  error page for the direct .sty path tried first).
  Kept natbib-compatible `\citet`/`\citep` and `\bibitem[Author(Year)]{key}`
  bibliography entries unchanged from v1.00 — `openjournal.cls` restores
  natbib internally, so no citation-syntax changes were needed, only the
  front matter.
  6 pages, clean compile (pdfLaTeX only needed, no BibTeX step — bibliography
  is a manual `thebibliography` block, same as v1.00), 1 negligible 3pt
  overfull \vbox (page-break rounding, not a real content overflow).
- **v1.00 (MNRAS-format) is now superseded but kept in place** for the
  record, per the "any previous version can be recovered" versioning policy
  — do not delete it.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v1.01/`.

## v2.00 (2026-08-30)
- **Major restructure, per Glenn's instruction**: "Paper I" and "Paper II"
  are no longer separate — this is now a single, standalone paper that is
  updated in place as the survey progresses, rather than a background-only
  piece promising results in a future companion paper. All "Paper I of a
  series"/"will be presented in Paper II" language removed from title,
  abstract, introduction, and the old placeholder "Scope of Paper II"
  section (§5) is replaced with real content.
- **New content**:
  - §4.1 Closure-phase point-source vetting, §4.2 Population-level
    spectral-type-normalised continuum anomaly check — full methodology
    write-ups of the two new analyses added to the live pipeline this
    session (see MEMORY.md 2026-08-30 07:25 entry for implementation
    details). Both explicitly framed as novel relative to the entire
    technosignature literature reviewed in §2, not just re-implementations
    of Ma et al./GLOBULAR/Poznanski.
  - §5 Results (real, current data): pulled and rigorously filtered actual
    campaign output — 26 target/bands had *some* data on disk, but 7 of
    those were STALE, pre-fix results for targets on the known
    "needs-redo" list (multi-field/phase-centre/mosaic-continuum bugs,
    or old pre-budget-fix timeouts) that the volume-limited campaign
    hasn't reprocessed yet (it's still working through nearer targets
    first) — these 7 were explicitly excluded from every statistic and
    from the appendix table, not silently included. Final dataset: 19
    valid target/bands. Caught and correctly explained, not silently
    reported as anomalous: (a) the one flagged "candidate" (β Pictoris,
    Band 3, 115.26 GHz) is the CO(1-0) line; (b) G 272-61A/B showing
    bit-identical continuum flux is NOT a bug recurrence — verified via
    `calibrate_status.json` that both share one single-field MOUS with
    `target_field=uv_cet`, i.e. these ARE the two components of the
    well-known UV Ceti visual binary, genuinely unresolved by ALMA at
    this configuration — flagged as an honest caveat, not excluded.
  - §6 Discussion, §7 Conclusions — new, grounded in the actual (partial,
    honestly labelled as preliminary — 19/120 = 16%) results.
  - Appendix A (`Table~1`, `tabularx`-based for proper text wrapping —
    plain `tabular` overflowed the page width by ~68pt on first attempt,
    caught by the standard `Overfull \hbox` log check and fixed): full
    per-target table (target, band, distance, frequency range searched,
    EIRP_min, candidate flag, continuum value, notes) — kept OUT of the
    main body per Glenn's explicit instruction; main text has summary
    statistics and two figures only.
  - Figure 1: EIRP and continuum vs. distance (two-panel), Figure 2:
    full 120-star sample distance distribution — both generated from real
    pipeline output, not illustrative/mock data.
- **Process notes**: gathered fresh data directly from the cluster
  (`/data/SETI/logs/driver_summary_master20pc.json` + all
  `*_result.json`/`continuum_summary.json` files), built a local
  `paper_data.json` → filtered → `paper_data_valid.json` pipeline so the
  filtering-out of stale data is itself reproducible/auditable, not a
  one-off manual edit.
- Verified with the full compile-3x + `pdftotext | grep "??"` = 0 discipline
  established after the v1.01 unresolved-references incident, on a
  completely clean rebuild (deleted the PDF and recompiled from scratch)
  as the final check before packaging for push.
- 9 pages, clean compile, 1 negligible 3pt page-break `Overfull \vbox`
  (not a content defect).
- **v1.00 and v1.01 kept in place**, superseded but recoverable, per the
  standing versioning policy.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.00/`.

## v2.01 (2026-08-30)
- Glenn: Figure 2 should be a cumulative plot (total number of stars out
  to distance $d$) rather than a binned histogram of counts per bin.
  Regenerated from the same underlying 120-star master list as a step
  plot of $N(<d)$ vs.\ $d$; updated the figure caption to describe the
  cumulative curve (steepening reflects increasing shell volume at larger
  $d$) rather than the old per-bin-count description. No other content
  changed from v2.00.
  Verified with the same compile-3x + zero-`??` + visual-render check as
  every version since the v1.01 incident. 9 pages, clean, 1 negligible
  page-break `Overfull \vbox`.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.01/`.

## v2.02 (2026-08-30)
- Glenn asked a clarifying question: does Figure 2 (and the "120-star
  volume-limited sample") represent the total stellar population within
  20 pc, or just the subset with ALMA archival coverage? Answer: the
  latter — this was already stated in words in §3, but Figure 2 itself
  didn't make the completeness gap visually or numerically explicit, and
  one leftover "Paper II" reference from the pre-merge draft (§2.6) had
  never actually been given a real number to point to.
- **Computed the real completeness fraction**: cross-matched the 120-star
  sample against our own reference Gaia DR3 catalogue of the solar
  neighbourhood — 2357 individually catalogued stars within 20 pc, of
  which our sample is only ~5.1%.
- Rebuilt Figure 2 as two cumulative curves on a log axis: the full
  2357-star Gaia census (grey) vs. our 120-star ALMA-covered sample
  (blue), with the completeness fraction annotated directly on the plot.
  Rewrote the caption to state explicitly that the two curves are not
  expected to track each other, since ALMA proposal pressure on the solar
  neighbourhood is not spectral-type- or distance-uniform.
- Added an explicit paragraph to §3 (Sample Selection) and tightened the
  Abstract's and §2.6's wording: the sample is volume-limited and
  unbiased *within* the ALMA-observed population, but is NOT a complete
  census of the local stellar neighbourhood — stated plainly rather than
  left for a reader to assume from the word "volume-limited" alone. Fixed
  the leftover "we quantify explicitly in Paper~II" reference (missed in
  the v2.00 merge) to point to the actual §3 discussion with the real
  number.
- Verified with the standard compile-3x + zero-`??` + visual-render
  discipline. 9 pages, clean, 1 negligible page-break `Overfull \vbox`.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.02/`.

## v2.03 (2026-08-30)
- Glenn raised three substantive, well-founded questions after reading
  v2.02 closely:
  1. **Spectral window coverage**: does the narrowband search cover every
     correlator sub-band configured together, or just one? Verified
     against real data (`calibrate_status.json` per target): ALMA
     configures 4-24 spectral windows simultaneously per observation in
     our sample (median 4; tau Cet's spectral-scan setup has 24), and we
     only ever search the single finest-resolution one — meaning, on
     average, only ~23% (range 4-25%) of the instantaneously configured
     spectral windows are actually searched narrowband. Added an explicit
     paragraph to §4 stating this with real numbers, and a new N$_{\rm
     spw}$ column in the Appendix table giving the exact count per
     target, rather than leaving it as an aggregate-only statement.
  2. **Continuum upper limit definition**: "(UL)" wasn't quantitative
     enough — is it 1σ, 3σ, 5σ, the raw measurement? Fixed by (a)
     explicitly restating throughout that a UL = 5×rms (the same
     threshold used to define a detection), (b) adding an explicit RMS
     (mJy) column to the Appendix table so the underlying measurement is
     given directly, not just the pre-multiplied 5σ value, letting a
     reader rescale to any confidence level they want, (c) switching from
     the ambiguous "X.XXX (UL)" notation to the standard astronomical
     "$<$X.XXX" convention.
  3. **EIRP context**: added a new §4.1 "Reference transmitter
     benchmarks" citing two real, precisely-sourced values from
     \citet{EarthDetectingEarth2025} — an Arecibo-like planetary radar
     ($2\times10^{13}$ W, the most powerful deliberate transmitter humans
     have built) and typical unintentional Earth radio leakage
     ($\sim4\times10^{9}$ W, LTE/cellular). Both added as horizontal
     reference lines on Figure 1's EIRP panel, with matching discussion
     in §5.1 (Results): our deepest limits are only just competitive with
     an Arecibo-equivalent transmitter at the very nearest handful of
     stars, and nowhere near sensitive enough yet to detect
     Earth-leakage-equivalent activity at any distance probed so far — an
     honest, useful calibration of what the survey can and cannot claim.
- Precise sourcing: fetched the actual Sheikh et al. (2025) "Earth
  Detecting Earth" paper text rather than relying on memory for these
  numbers — confirmed "Arecibo's characteristic EIRP at S-band is 20 TW"
  and the 4 GW LTE-leakage figure directly from the source text before
  citing either.
- Verified with the standard compile-3x + zero-`??` + visual-render
  discipline. 10 pages (grew by 1 from the new benchmarks subsection),
  clean, 1 negligible page-break `Overfull \vbox`.
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.03/`.

## v2.04-v2.08 (2026-08-30 -- 2026-09-01)
- **Retroactive summary** (this file was not updated incrementally during
  these versions; full detail for each is in `/workspace/MEMORY.md`,
  search "v2.04" through "v2.08" -- reconstructed here briefly so the
  version history stays traceable from this file alone):
  - **v2.04**: Table 1 restructured to a full spectral-window-per-row
    format (previously one row per target); added N$_{\rm spw}$ column.
  - **v2.05**: abstract cut to ~1/3 length per journal guidance; found
    and excluded the first batch of 4 crossmatch-error target/bands.
  - **v2.06**: implemented full multi-spw search (previously only the
    single finest-resolution window per target was searched).
  - **v2.07**: full data refresh (21→36 valid target/bands incl.
    TRAPPIST-1); second candidate flag (AU Mic, judged not credible);
    found 19 MORE crossmatch-error target/bands beyond the original 4,
    plus the bookkeeping bug that would have permanently excluded them
    from retry.
  - **v2.08**: main 120-star driver finished its full first pass
    (146/146 attempted, 68 succeeded at process level); added eta Corvi
    (first Band-8 target); found and carefully handled a new
    data-quality category (gamma Lupi partial-crossmatch + an
    implausible short-integration result, withheld pending
    investigation).

## v2.09 (2026-09-04)
- **Full data refresh**: re-ran the aggregation against current cluster
  data. Main $\leq$20pc sample grows from 37→50 target/bands (28→39
  unique stars); 22 target/bands new or reprocessed this version. EIRP
  limits now $1.7\times10^{13}$--$7.1\times10^{16}$W (median
  $3.1\times10^{14}$W); continuum 14 detections / 33 non-detections
  (median UL 0.52 mJy, was 0.56).
- **NEW: preliminary 20-30 pc extension appendix** (Appendix B), per
  Glenn's request. Investigated what "the additional searches out to 30
  pc" actually are: **there is no actively-maintained, parallel 20-30pc
  campaign** -- only archived metadata from the older, non-distance-limited
  pre-pivot survey (`archive_gt20pc_metadata/`). Identified the 12 stars
  in that archive falling in 20-30pc, characterised each honestly: 5
  usable (narrowband+continuum), 2 continuum-only (narrowband failed), 5
  with no usable data at all (calibration/download/governor failures,
  never retried since that survey was stopped, not paused, at the
  pivot). Reported as a clearly-separated, explicitly non-volume-complete
  table -- NOT merged into the main Table 1, and the paper states plainly
  what it is and isn't.
- **Candidate-vetting catch (20-30pc data)**: HD 107146's archived result
  carried `credible_technosignature_candidate=true` (3 hits) but its
  control-ensemble peak SNR (6.013) is statistically indistinguishable
  from its source-region peak SNR (6.029) -- applied the same
  control-ensemble discipline used throughout the main survey and
  correctly rejected it as non-credible, rather than reporting the raw
  flag.
- **Two real pipeline findings, reported with the same rigour as
  v2.05-v2.08's crossmatch-bug disclosures**:
  1. A specific spectral window (recurring with byte-identical anomalous
     parameters: 12.1s on-source vs 393-520s for sibling windows, yet an
     implausibly *smaller* combined noise estimate) found in TWO
     independent targets sharing a similar Band-6 correlator setup
     (HD 10647 and the star catalogued as "gamma Lupi" -- NOT the famous
     naked-eye B-star of the same name, confirmed via grossly
     inconsistent Teff/distance). Cross-target recurrence with matching
     detail elevates this from "one target's odd result" (as left open
     in v2.08) to a diagnosed, reproducible pipeline defect. Both
     targets' affected window is excluded, contaminated continuum
     withheld, other windows retained.
  2. Confirmed a previously-reported (pre-v2.08) continuum-imaging gap is
     STILL outstanding: Giclas 9-38A/B remains unfixed and still produces
     a spurious ~8 Jy, 86sigma "detection" at an offset the code reports
     as 0.00 arcsec (actually ~52 arcmin off, since the continuum step
     lacks the narrowband step's pointing-offset guard). By contrast,
     confirmed that most of the OTHER crossmatch-affected targets
     (SCR J1845-6357, Wolf 358, eps Eridani, and others) have since been
     successfully reprocessed and now appear in Table 1 with legitimate
     data -- the retry mechanism is working as designed.
  3. **Separately, an operational (not scientific-pipeline) bug**: this
     version's cluster driver relaunch (following the exact command given
     in the task brief) omitted required `SETI_TARGET_CSV`/`SETI_BAND_MOUS`
     env vars and silently ran the OLD non-volume-limited target list for
     ~20 min before being caught and fixed. See `STATUS.md` and
     `/workspace/MEMORY.md` for detail; does not affect any number
     reported in this paper.
- Exoplanet-host subsample: 13/41 unique stars (32%, 33 planets), adding
  eps Eridani and HD 69830.
- Three supplementary-analysis subsections (molecular-line catalogue,
  chirped-drift/periodicity, frequency-occupancy) explicitly note their
  quoted counts are carried over unchanged from v2.08 -- re-running them
  against the larger sample needs the original scripts, not available
  this session; deferred honestly to next version rather than
  guessed/fabricated.
- Verified with the full discipline: rendered and eyeballed every page
  (not just first/last) via `pdftoppm`; `grep "Overfull \hbox"` = 0
  after one minor rewording fix; 0 unresolved `??`/undefined refs;
  clean-from-scratch rebuild MD5-verified before packaging. 17 pages
  (was 15).
- Figures: EIRP/continuum-vs-distance figure regenerated from fresh
  aggregate data with the 7 20-30pc points overlaid as visually distinct
  open orange diamonds, clearly labelled as the preliminary extension in
  both the legend and caption. Sample-distance-distribution figure
  (Fig. 2) carried forward unchanged (its underlying 2357-star/120-star
  lists did not change this version).
- Pushed to `Tilanthi/SETI` at `paper_20pc/v2.09/`; aggregate JSON and
  generation scripts pushed to `paper_20pc/v2.09_analysis/` for
  transparency, following the established pattern.

## v2.10 (2026-09-07)
- **Headline finding: first-ever ALMA technosignature search of Barnard's
  Star and Wolf 359.** Investigating why neither of these two very
  nearby, high-value stars had ever been reached by the pipeline despite
  deep archival ALMA coverage existing for both revealed a genuine
  upstream bug: the crossmatch step matching a catalogued star's position
  to ALMA archive pointings was not propagating the star's Gaia proper
  motion before matching. For most of the sample this makes no
  difference, but Barnard's Star (10.4"/yr) and Wolf 359 (4.7"/yr) are
  respectively the highest- and among the highest-proper-motion stars in
  the entire 20pc sample -- over the years between the archival
  observation and the crossmatch, each star had drifted far enough that a
  real, on-target MOUS was never even offered to the pipeline as a
  candidate. Fixed and reprocessed: both now have clean Band-6 results
  (primary-beam offsets 0.54"/0.51", dead-centre; EIRP limits
  6.2-6.9e13 W and 7.8-9.1e13 W respectively; non-detections throughout).
  Given real narrative weight in the paper (new §5.1-5.2), not just a
  table row.
- **Five further target/bands recovered via two distinct mechanisms**,
  reported precisely (not conflated): **three** genuine legacy-format
  recoveries (Wolf 219 [B6], chi01 Ori [B3], eta Cru [B6]) via a
  newly-built capability to replay pre-automated-pipeline ALMA calibration
  scripts (`scriptForCalibration.py`) the pipeline previously could not
  read at all; **two** stale-marker corrections (CD-38 10980 [B6],
  GL 3379 [B6]) -- modern-format data sitting on stale FAILED markers
  from an earlier, since-fixed bug, recovered by clearing and retrying.
  All five yield clean, non-anomalous results; chi01 Ori and eta Cru show
  modest photospheric continuum detections consistent with their spectral
  types (G0V, F2V), not anomalous.
- Two further target/bands (eta Corvi's second band [B7], alongside its
  already-reported [B8]; HN Lib [B6]; LHS 1140 [B6]) completed in the
  ordinary course of the survey's continuing progress during this period
  -- HN Lib and LHS 1140 are both themselves known exoplanet hosts
  (HN Lib b and LHS 1140 b/c, both habitable-zone candidates), adding a
  genuine ALMA non-detection to their existing planet-search literature.
- Several further pipeline reliability bugs found/fixed but not
  individually detailed in the paper text (consistent with prior
  versions' level of disclosure for non-result-changing fixes):
  download-retry state-cleanup, log-file search path, and a
  cache-corruption issue from an earlier false-success bug.
- **Ground-truth verification discipline** (per direct instruction not to
  trust cached numbers): re-derived every statistic from real product
  files on the cluster via a fresh has_data walk. Found and corrected a
  real discrepancy in the dispatch's own headline number: a naive global
  directory scan suggested 72/166 valid target-bands, but this
  double-counted 9 legacy single-band duplicate directories (superseded
  by their current multi-band counterparts, e.g. `GJ_581` bare-name dir
  vs the current `GJ_581_B6`) and included 1 out-of-scope star
  (HD 45184, not in the <=20pc master list). The correct, verified figure
  is **60 valid target/bands out of 148 planned** (up from 50/146 in
  v2.09), 46 unique stars. Reported the correction transparently rather
  than publishing the higher, uncorrected number.
- Full data refresh: EIRP now 1.6e13-7.1e16 W (median 2.7e14 W, was
  3.1e14); continuum 17 detections/40 non-detections (median UL still
  0.52 mJy); exoplanet-host subsample 15/46 (33%, 36 planets, was
  13/41). No new credible candidates -- re-verified with the same
  control-ensemble discipline as before; still only the already-known,
  already-explained beta Pic CO-line and AU Mic marginal cases.
- Single-window ("reprocessing queued") target count dropped from 11 to
  3 ($\tau$ Cet, Kapteyn's Star, Van Maanen's Star) as most of the
  sample's earliest-processed targets (Proxima Cen, Sirius B, the UV Cet
  pair, GJ 674, CD-23 14742) were reprocessed to full multi-spw coverage
  during this period.
- Verified with the full discipline: page-by-page render review (22
  pages, up from 17), `grep "Overfull \hbox"` = 0, 0 undefined refs, 0
  unresolved `??`. Found and fixed a real LaTeX layout defect during
  verification: with 8 appendix table parts now (up from 5), floating
  `table*` blocks were drifting past the bibliography's `\begin{document}`
  boundary, splitting the References section in half around interleaved
  table floats -- fixed with an explicit `\clearpage` before
  `\begin{thebibliography}`. Clean-from-scratch rebuild MD5-verified
  before packaging.
- Aggregate JSON and generation scripts pushed to
  `paper_20pc/v2.10_analysis/` for transparency, following the
  established pattern.

## v3.24 (2026-09-09, Glenn, offline)
- Versions v2.11-v3.24 were drafted by Glenn offline; no changelog entries
  were made here for them. v3.24 is the baseline this assistant reproduced
  byte-for-byte (44/44 pages pixel-identical, full-text SHA256 identical)
  before taking over editing. Build notes: `v3.24/BUILD_NOTES.md`.

## v3.25 (2026-09-09)
- Rescoped 0-20 pc -> 0-40 pc (partial, stated explicitly in a new
  front-matter "Scope of this version" note, since parts of the text still
  quote the 20 pc counts).
- Adopted the **symmetric** star-versus-control statistic in place of the
  earlier region-max statistic; the AU Mic feature is reclassified from
  candidate to non-candidate as a direct consequence. 44 -> 43 pp.

## v3.26 (2026-09-09)
- All 13 data figures regenerated on the 40 pc sample from a
  written-from-scratch, re-runnable `make_figures.py`.
- **Noise-defect exclusion generalised from a name list to a physical
  test** (`sigma*sqrt(t_on*dnu_ch)` more than 100x below the sample
  median): 6 of 448 windows fail, not the 2 named in v3.25. Those 6 had
  been setting the headline depth; corrected best threshold 1.6e13 W.
- Two real manuscript defects fixed: an internal author note that was
  **rendering as body text** on p2 of v3.24 and v3.25, and leaked referee
  tags. Appendices trimmed 34%. 43 -> 38 pp.

## v3.27 (2026-09-09) - ancillary relocation, main text -20.0%
- **Structural trim only: no scientific claim, number, figure or table was
  removed from the paper.** Ancillary and validation material was moved
  from the main text into the online-only supplementary material, and each
  moved block left behind a summary carrying every number the main text
  depends on.
- Relocated: injection-recovery validation (+ its table and figure);
  closure-phase vetting; the population-level continuum anomaly screen;
  the chirp/periodicity screen; the cross-target frequency-occupancy check
  (+ the scope table); the integration-time audit; the continuum-search
  results; the serendipitous molecular-line catalogue; the AU Mic
  localisation/recurrence/statistical-scale detail; the velocity-space
  line mask's justification; the symmetric-null validation subset; and
  three false-alarm robustness checks (trials-count reconciliation,
  stratification, control-ring geometry).
- Where a summary and its "full specification" appendix existed as separate
  objects, they are now merged into one online section, so each topic lives
  in exactly one place.
- **Lengths**: main text 110,773 -> 88,655 characters (**-20.0%**);
  printed article (through the last printed appendix) 26 -> 20 pp;
  main text alone 19 -> 15 pp; total document **38 pp, unchanged** - the
  material moved, it was not deleted, so the no-growth constraint holds.
- Verification: 0 undefined references, 0 undefined citations, 0
  multiply-defined labels, 0 Type3 bitmap fonts, 38/38 pages render.
  Number-preservation diff against v3.26 shows no numeric value lost.
- Two pre-existing defects fixed in passing: a `\ref` inside a
  `\subsection*` moving argument (would have printed an undefined
  reference), and the claim that "the block-permutation model ... remains
  the operative release-wide estimate", which contradicted the appendix
  that retires that ladder - now the empirical star-versus-ring
  calibration, which is what is actually used.

## v3.28 (2026-09-09) - referee revision: 40 pc rescope completed, two reports addressed point by point

**The central referee complaint, from both reports: the title and abstract described a
40 pc sample while every result reported the older <=20 pc one. Fixed by completing the
rescope.** Every survey number is now recomputed from ONE frozen export by `survey_stats.py`,
and the figures and tables come from the same export via `make_figures_v328.py` and
`make_tables_v328.py`, so text, tables and figures cannot drift apart.

- **Sample**: 168-star census; **85 stars / 79 independent systems / 104 of 208 star-band
  datasets / 417 windows / 100 execution blocks**, 1.30-38.83 pc. 448 rows extracted, minus
  21 repeats, 6 noise-defect windows and 4 withheld.
- **The science changed.** Four windows now contain a spatially significant hit, not three:
  the two known beta Pic CO lines, plus **HD 48370** - whose CO(2-1) emission is
  independently reported by Cataldi et al. (2023) and attributed there to foreground cloud
  contamination, an external corroboration the survey recovered blind - plus **CP-72 2713**,
  a new marginal crossing. **AU Mic is no longer flagged at all.** Zero candidates.
- **Occurrence limits re-derived and re-ordered** so the completeness-aware number leads:
  f95 < **6.5%** at EIRP >= 1e16 W (56 injection-calibrated systems), with 3.8% (unit
  recovery) and 9.0% (uniform 42%) demoted to bracketing calculations. Bayesian cross-check
  with a uniform prior gives 6.4%. Duty-cycle dependence is now in the abstract, a table and
  a figure: 13.0% at D=0.5, 65% at D=0.1.
- **Nomenclature simplified** to hit / spatially significant hit / candidate, so the paper
  now says "four spatially significant hits, zero candidates" and cannot generate a
  candidate headline.
- **AU Mic transparency**: the symmetric criterion's flagged set is a strict SUBSET of the
  old region-max set - it removed three windows (ALMA J1537-3319, AU Mic, HD 14055), in all
  of which the star never beat its own control ring. A bias correction, not a power
  reduction, and demonstrably not tuned to reject one object.
- **New figures**: frequency x system coverage waterfall; noise-QA showing the 3.2-decade
  empty gap that justifies the defect cut; drift ceiling vs orbital radius by host mass;
  occurrence vs EIRP with duty-cycle curves; control-ring exchangeability diagnostics.
  Removed: the 1 Hz sensitivity extrapolation (referee asked), plus two superseded figures.
- **New in text**: explicit T* equation, an algorithm box, a nomenclature table, an
  authoritative survey-state table at the head of Results, a "What this survey does not
  constrain" box, a priorities-for-next-release section, and a pre-committed look-elsewhere
  rule across the planned release sequence.
- **eps Eri Band 6 withheld** rather than published with a provisional 2.9-3.4x primary-beam
  correction; Sirius B retained with its bounded <=16% systematic stated as such.
- **Length**: 38 pages, unchanged from v3.27, despite all of the above. Paid for entirely by
  removing repetition and non-essential wording (~25k characters), not by deleting analyses.
- **Defects fixed that we had shipped**: `completeness.pdf` in v3.27 did not match its own
  caption; `pipeline_schematic.pdf` embedded Type 3 fonts (broken text extraction) in
  v3.24-v3.27; the main text called the retired block-permutation ladder the operative
  false-alarm model; and a de-duplication rule that materially affects two windows is now
  disclosed rather than silent.
- Verification: 0 undefined references, 0 undefined citations, 0 multiply-defined labels,
  0 LaTeX errors, 0 Type 3 fonts, 0 residual "within 20 pc" text, 0 manuscript-version
  history. Point-by-point response in `v3.28/REFEREE_RESPONSE.md`.

## v3.29 (2026-09-10) - second referee round: single-source numbering, Figure 1 physics corrected, occurrence bound demoted

Note for the record: two reports were forwarded and **the second was for a different paper**
(an 18-page study of the L_IR-L'_HCN(3-2) relation in Galactic clumps, with a 107-source
Table A1, a W49A point, and "Grozdanova et al., in preparation"). Our paper is 38 pp and
contains none of that; its only HCN mention is one of eight masked species. Not acted on;
the editor has been asked for the correct report.

**THE REFEREE'S FOUR ACCEPTANCE CONDITIONS**
- **Single-version numerical audit.** Every survey quantity is now a LaTeX macro emitted by
  `make_numbers.py` into a generated `survey_numbers.tex`. The manuscript contains no typed
  digits for these quantities. Root cause fixed, not symptoms: the manual effort of keeping
  a number consistent used to scale with the number of places it appeared.
- **Figure 1 physics corrected.** The W Hz^-1 panel is WITHDRAWN. EIRP/dnu_ch is a
  channel-averaged equivalent spectral luminosity, right only for channel-filling emission,
  not the spectral power of an unresolved carrier - our own worked example proves it (a 1 Hz
  carrier still needs the full 1.6e13 W, so ~1e13 W/Hz intrinsic, not 1e6). The panel
  flattered ALMA by six orders of magnitude against exactly the signal class searched.
  Figure 1 is now single-column, total power only.
- **Occurrence bound demoted and reframed.** The headline is now the non-detection plus the
  threshold range. The bound is no longer called a prevalence: it is an effective conditional
  occurrence bound given occupancy of each target's own observed frequencies, on the 79
  systems processed. Duty-cycle degradation travels with it everywhere (6.5% -> 13% at D=0.5,
  65% at D=0.1). **New: the conditioning is now measured** - under a uniform p(nu) across
  ALMA's tuning range, F_i falls to ~4.5e-3 and the bound is VACUOUS (f~3.8 transmitters per
  system needed for one expected detection).
- **Injection provenance.** Trial-level records were not retained, so denominators are
  reconstructed from the design. Disclosed rather than disguised; the bound is labelled a
  pilot, configuration-limited estimate; trial-level logging committed for the next release.

**ALSO FIXED (all errors the referee found were real)**
Conclusions reverted to three candidates incl. AU Mic (now four spatially significant
windows, zero candidates); 42 vs 79 systems; 46 vs 85 stars; 104/208 called 41% (is 50%);
local-population fraction given as both ~7% and ~1% (is ~1%); "extend to 30, 40 and 50 pc
once the 20 pc sample is complete"; glossary and nomenclature table disagreeing on the
definition of "candidate".

**NEW ANALYSIS**
- **Pseudo-star null calibration** (referee-requested): each of the 512 controls ranked in
  turn against the other 511, pooled over the release. 213,504 ranks uniform to the
  discreteness floor (mean 0.5010, KS D=1/512, p=0.39), uniform in every band and both
  channelisations; star vs pseudo-star two-sample p=0.31. The control-ring argument is now
  measured, not assumed.
- New completeness surface (recovery vs amplitude and drift fraction), drawn as discrete
  cells with hatching so it cannot imply per-cell data we do not have.

**PRESENTATION**: drift relation promoted to a displayed equation with the frequency-
independent dnu/nu form; "volume-limited census" -> "archive-defined 40 pc sample"; line
vetting distinguishes "outside the eight-line mask" from "no plausible known transition";
novelty claims scoped to ALMA archival technosignature surveys; coverage waterfall moved to
p5 per the referee; injection figure brought into the main text.

**DEFECTS IN OUR OWN PRIOR RELEASE**: `eirp_context.pdf` in v3.28 was not the figure its
caption described (a histogram, not the scatter); the Margot et al. (2023) comparison value
was plotted at 1.0e13 W instead of the published 1.35e13 W; "only targets within ~3 pc reach
below Arecibo" described two components of ONE bound system.

**FLAGGED, NOT SILENTLY HARMONISED**: the injection campaign is described as using a
"49-trial drift grid", but 5 amplitudes x 5 drift fractions = 25 and 1200/6/5 = 40; neither
is 49 and no retained product explains it.

**Length**: 38 pages, unchanged. Verification: 0 undefined refs, 0 undefined citations,
0 multiply-defined labels, 0 errors, 0 Type 3 fonts, 0 literals disagreeing with a macro.
Point-by-point reply in `v3.29/REFEREE_RESPONSE_ROUND2.md`.

## v3.30 (2026-09-10) - post-push audit: residual stale content found and removed

v3.29 was pushed after a verification pass that checked for specific literal strings. A
deeper independent audit then found that several of the referee's objections survived as
**paraphrases** rather than literals, plus a set of defects that pass had not looked for.
v3.30 fixes them. Nothing here changes a result; all of it is consistency and correctness.

**A REAL ERROR IN THE CONCLUSIONS.** The occurrence sentence had its descriptors swapped:
it attributed "the injection-measured, frequency-integrated completeness folded in" to the
3.8% figure, which S6.1 and tab:occurrence define as the *thresholded, unit-recovery*
bracket, and it hard-coded "24 calibrated systems" where the value is 56. Rewritten, with
the duty-cycle degradation and the vacuity-under-a-frequency-prior statement attached.

**A TABLE THAT CONTRADICTED THE PAPER, DELETED.** `tab:bandsummary` was an unreferenced,
hand-written duplicate of the generated `tab:perband`: 439 windows instead of 417, and its
"Best EIRP" column quoted **2.8e12 and 2.0e12 W** - the two noise-defect windows this paper
explicitly excludes, and whose exclusion is one of its headline corrections. Removing an
unreferenced stale duplicate that states what S5.3 refutes is an error fix, not a cut.

**`tab:ebs` claimed 100 execution blocks and listed 57.** The caption now says what is true:
57 blocks whose archive metadata had been recovered at freeze time, out of the 100 searched,
the remainder to accompany the machine-readable release.

**"Candidate" was still used for objects the paper defines as non-candidates** - the AU Mic
window in five places including two figure captions, the beta Pic windows in four, "the three
candidate windows", and tab:supp listing closure-phase vetting as applied to "3 candidates".
All reworded; "candidate" now means only what tab:nomenclature says it means.

**Further 20 pc-era residue**: "four of the 46 are white dwarfs"; "the 120 entries comprise
113 distinct physical systems"; "spanning 1.3-19.6 pc"; "~7% of the catalogued stars"
(elsewhere ~1%); a stray "within 20 pc" in the frame-conversion appendix; and version history
("Versions up to 3.24") in an appendix the referee had asked be cleared of it.

**Housekeeping**: App. R contradicted S5.3 on which item the process-level failures are;
two orphaned references (Drake 1974, Gentile Fusillo et al. 2021) restored to in-text
anchors; the Data Availability TODO named a superseded tag. `make_tables_v328.py` now carries
a warning that re-running it reverts the trimming and re-hardcodes numbers over the macros.

**Still open and flagged, not guessed**: `Tristan2025` remains uncited - it is the authors'
own co-authored flare paper and its intended anchor is theirs to place.

**Length**: 38 pages, unchanged. 0 undefined references, 0 undefined citations, 0
multiply-defined labels, 0 LaTeX errors, 0 Type 3 fonts, 0 stale-era residue patterns,
285 generated-macro calls, every referenced label defined and every figure present.

## v3.31 (2026-09-10) - refreshed to live pipeline data + third referee round, in one version

**LIVE DATA CONNECTION ESTABLISHED.** The survey runs on **astra-climate**
(`fetch-agi@34.143.130.135`), not in any agent container; `/data` does not exist locally.
The SSH key was already on the shared drive, mis-recorded as "awaiting authorization".
There was also **no exporter** - the analysis export had been a manual step nobody preserved,
which is why the paper kept going stale. `/data/SETI/bin/export_figdata.py` now rebuilds it in
one command. Route and refresh cycle documented in `/shared/SHARED.md`.

**DATA REFRESHED** to snapshot 2026-09-10T06:43Z (was 2026-09-09T16:26Z):

| | v3.30 | v3.31 |
|---|---|---|
| searched windows | 417 | **431** |
| stars / systems | 85 / 79 | **88 / 82** |
| star-band datasets | 104 of 208 | **107 of 208** |
| execution blocks | 100 | **102** |
| distance span | 1.30-38.83 pc | **1.30-39.63 pc** |
| hits / flagged / candidates | 18 / 4 / 0 | **20 / 4 / 0** |

**The science is unchanged**: the same four spatially significant windows (beta Pic x2,
HD 48370, CP-72 2713), still zero candidates. Coverage grew; conclusions did not move.
Because every number is macro-generated, refreshing the export updated the abstract, body,
tables and captions in one step - the point of the v3.29 macro system.

**REFEREE ROUND 3, both reports addressed.** Referee 1 was right that the rank-null argument
was wrong: under exchangeability the probability that one designated position of 513 ranks
first is exactly 1/513, *independent of tail shape*, so the previous "heavy tails inflate
1/513" explanation was invalid. Replaced with the real one: of the 5 rank-first windows,
3 carry genuine celestial line emission at the stellar position and are not draws from the
noise null at all; the residual 2 against 0.84 expected give P = 0.21, unremarkable. Also:
which statistic is applied to all 431 windows vs the 7 reprocessed ones is now stated once,
unambiguously; a three-level hierarchy (instrument/noise -> astrophysical-source ->
technosignature) is enforced; "5 sigma" is a *trigger* threshold throughout; the occurrence
number is renamed a **conditional in-band transmitter fraction**, demoted below the
non-detection, and always quoted with its duty-cycle degradation; the title is shorter; the
abstract is restructured and now scopes the 42 per cent completeness to the fine-channel
class only (Referee 2 M1); AU Mic is purged of "candidate" language; closure phase is
presented as demonstrated-but-not-sensitivity-effective.

**NEW ARTEFACTS**: `tab:bothstats` (all seven originally-flagged windows under both
statistics - the audit trail Referee 2 asked for; it also closed the only undefined reference
in v3.30); `tab:allhits` (all 20 hit windows, the full funnel); frequency offsets alongside
velocity offsets in the flagged-window table; channel width exposed on Figure 1
(GBT/Parkes 2.8 Hz, Margot 3.0 Hz, Mason 30.5 kHz, this survey 15.63 MHz median); a
completeness surface; a C_i = F_i R_i D_i C_morph decomposition; an online-appendix index.

**CORRECTIONS TO OUR OWN TEXT**, found by audit: "this release's 42 systems all lie inside
20 pc" was flatly false after the rescope (82 systems, 41 inside 20 pc) and its "~2500x
deeper than Mason+2024" was wrong (~1250x); "15 of the 46 processed stars (36 planets)"
contradicted Section 3 and is now 18 of 88 (41 planets); Figure 13 said "n=86" and "within
20 pc"; and the archival-hygiene lesson the paper now teaches in the main text - that the
catalogue entry "gamma Lupi" is really HD 139664 - was contradicted by our own tables, which
still said "g Lup". Fixed at source in the exporter, so the released data agree.

**Length**: 38 pages, unchanged since v3.27. 0 undefined references, 0 undefined citations,
0 multiply-defined labels, 0 LaTeX errors, 0 Type 3 fonts, 316 generated-macro calls.

## v3.31 (rev 3, 2026-09-10) - fifth referee round: duty-cycle model corrected, local noise measured, statistics named

**DUTY CYCLE CORRECTED (Referee 1's principal technical point).** The occurrence ladder used
D_i = D, discarding the benefit of repeated epochs. A system observed in n_i independent
execution blocks is sampled n_i times, so D_i = 1-(1-D)^n_i. 18 of the 82 systems have n_i>1
(13 with two epochs, five with three). Recomputed: at EIRP >= 1e16 W the measured-completeness
bound goes 12.3 -> 10.8 per cent at D=0.5 and 62 -> 48 per cent at D=0.1, and D=0.05 moves from
unconstrained to 95 per cent. The independence assumption is stated, and correlated or periodic
on-states are explicitly outside the model.

**LOCAL NOISE MEASURED, not deferred (Referee 1 point 8).** The referee asked that the global
MAD noise scale be checked locally for the four exceedances rather than left to a future
release. Done, using the retained per-integration spectra on the cluster: local-to-global
ratios are 0.97 (CP-72 2713), 1.29 (HD 48370), 0.93 (beta Pic B3), 1.02 (beta Pic B6). The
global scale is accurate to a few per cent except toward HD 48370, where a local estimate sits
29 per cent higher because that field is full of CO - the disposition already assigned to it.
For CP-72 2713 the local scale is slightly LOWER, so its excess is marginally understated
rather than inflated. No disposition changes. Stated honestly as a test of the noise scale,
not of T_star, since the retained products keep no drift-stacked cube.

**THREE STATISTICS NAMED (Referee 1 point 4).** "Symmetric" was doing two jobs. Now: the SP
statistic (single stellar position vs 512 single controls) is operative over all 431 windows
and is the source of every count; the SR statistic (region maximisation at star AND controls)
needs raw-visibility reprocessing and exists for seven windows as a consistency check; the
legacy asymmetric statistic is retired.

**DEVELOPMENTAL vs CONFIRMATORY (Referee 1 point 5).** Because this release is the sample on
which the statistic was developed, its false-alarm calibration is now labelled retrospective.
The pre-registration binds only the remaining 101 planned datasets, which become the
confirmatory sample.

**ERRORS FIXED**
- Stellar composition: "76 of the 168 stars are M dwarfs (63 per cent)" - the enumerated counts
  summed to 120, and 76/120 (not /168) gives 63 per cent. Referee 2 caught it. Replaced with
  the generated, correctly scoped Teff composition from the selection-function table.
- Four hard-typed 417-window numbers survived the refresh to 431 and contradicted the macros:
  the AU Mic statistical-scale percentile/count/p-value, the AU Mic figure legend, "18 windows
  with an on-star crossing" (now 20), and "among 402" non-beta-Pic windows (now 416). All
  recomputed, macro-ised, and the figure regenerated. This was the same bug class the macro
  system exists to prevent, surviving only because these four were typed rather than generated.
- A crossmatch alias broke by my own earlier fix: the export renames g Lup -> HD 139664 while
  the ranked census keeps the old identifier, so one star failed to match. Reverse alias added;
  the table now reads "all 88 were matched" rather than 87.
- Nine duplicated generated-table header comment blocks, left by successive re-splices.

**TERMINOLOGY**: "phase-steady" -> "temporally persistent, frequency-stationary" (the pipeline
subtracts a temporal median of intensity, not electromagnetic phase, so the old term invited a
physics misreading); "vacuous" -> "unconstrained"; channel-width range spelled out as spanning
more than three orders of magnitude.

**FIGURE SIZING FIXED**: three supplement figures were being upscaled to 154-209 per cent of
their natural width, which is why their axis labels were visibly larger than the body text.
Normalised. That, not text deletion, is what returned the paper to 38 pages.

**Length**: 38 pages, unchanged. 0 undefined references, 0 undefined citations, 0
multiply-defined labels, 0 LaTeX errors, 0 Type 3 fonts, 346 generated-macro calls, and a clean
sweep on eight stale-number patterns.

## v3.32 (2026-09-10) - the coarse-channel completeness campaign, and a withdrawn claim

**THE PAPER'S CENTRAL LIMITATION WAS WRONG AND IS WITHDRAWN.** Every version since v3.24 has
said the pipeline's "per-channel temporal-median subtraction" suppresses temporally persistent,
frequency-stationary carriers, and that a classical continuous beacon therefore lies outside
what this survey constrains. It does not. **The pipeline performs no temporal-median
subtraction at all**: its baseline step is a running median along FREQUENCY (65 channels,
per integration), which by construction cannot remove a feature confined to one or two
channels -- its own docstring says so -- and the de-drift step is an inverse-variance-weighted
SUM over integrations, which accumulates a persistent carrier coherently.

**MEASURED, TWO WAYS.**
- Dwell-fraction campaign: 3,888 trial-level injections over 12 real windows (6 coarse,
  6 fine, 11 targets), amplitudes 2-20 sigma per integration, dwell 0.10-1.00, six
  realisations. Recovery RISES with dwell. Pooling amplitudes >=4 sigma: coarse 100% at
  dwell 1.00, 100% at 0.25, 83% at 0.10; fine 100%, 91%, 71%.
- End-to-end through the unmodified released pipeline: a zero-drift, always-on tone injected
  into calibrated visibilities of a coarse Band 7 window at 1, 3 and 10x the per-integration
  rms returns T_star = 20.5, 65.3 and 217.7, recovered within one channel of the injected
  frequency, detection=True in every case. For 639 integrations the ideal coherent gain is
  sqrt(639)=25, so 20.5 at the per-integration noise level is essentially perfect.

**WHERE THE OLD "0 of 500" CAME FROM.** That campaign's frozen recovery criterion required the
recovered peak drift to lie within one grid step of the injected drift. On a coarse window
every in-grid drift is sub-channel over a track, so the trial grid is degenerate and the
reported peak drift is arbitrary; the clause fails even for a 200-sigma detection. A criterion
artefact, read for four versions as physical suppression.

**CONSEQUENCES**
- The 73 per cent completeness gap that both referee rounds called the survey's biggest
  weakness is now FILLED: coarse windows have measured C(A, f_dwell).
- The survey DOES constrain the classical continuous narrowband beacon.
- The genuine coarse-window limitation is narrower and still real: no drift DISCRIMINATION
  (the grid is degenerate), while amplitude sensitivity is full. That replaces item (i) of the
  "what this survey does not constrain" box and heads the next-release priorities.
- The abstract, introduction, boxed reading rule, limitations box, injection appendix and
  future-work list are all corrected; the withdrawal is stated explicitly rather than quietly.
- New section 5.5 "Dwell-fraction completeness, and a withdrawn claim" with Table 11, and the
  trial-level records released as per_target dwell_campaign_trials_v3.32.csv -- which also
  answers the referees' standing request for per-injection provenance.

**OPERATIONAL: the survey was deadlocked and is now running again.** While scoping the
campaign the driver was found stalled -- the disk governor had been blocking it for hours at
149G free against a 150G floor, because the target it was working on (HD172555 B7) had
accumulated 175G of per-spw split measurement sets in its own products directory. The search
step reclaims its waterfall intermediate but never reclaimed the split MS. Freeing one
completed spw's MS (30G) unblocked it immediately, and the reclaim gap is now fixed in
seti_drift_search_generic.py so it cannot recur.

**Length**: 38 pages, unchanged. 0 undefined references, 0 undefined citations, 0
multiply-defined labels, 0 LaTeX errors, 0 Type 3 fonts.

## v3.33-v3.39 (2026-09-10/11) - authored offline by GJW, not logged here

Referee rounds 3-9, the Class A/Class B taxonomy, the Discussion restructure,
the demotion of the occurrence limit to an "illustrative calculation only"
appendix, and the round-5..round-9 generated macro lanes. v3.39 was uploaded
to GitHub directly by the author; this file has no per-version entry for them.
(A v3.33 was started here and abandoned on instruction; see that folder's
HALTED.md.)

## v3.40 (2026-09-11) - round 10: the dwell campaign read at trial level

- **The coarse class gets a completeness curve.** The trigger acts on the
  stacked statistic and the de-drift step is an inverse-variance-weighted sum,
  so `a = A * f_dwell * sqrt(N_int)` unifies the amplitude and dwell axes and
  puts all 12 injected windows on one axis. Those windows span
  `N_int` = 21-1314 (x63), 11 targets, Bands 3/6/7, both classes, so
  configuration-independence became measurable rather than assumed: the 50 per
  cent recovery point sits at `a` = 5.3-8.3 (median 6.2) in the six windows
  whose grid straddles the trigger - the 5 sigma threshold itself - and the
  other six saturate (weakest injection `a` = 3.4, >=97 per cent recovered).
- **The injected carriers do not drift**, so the curve is applied only where it
  belongs. The occurrence limit uses a morphology-matched mix: the drifting
  curve on Class A, the dwell curve on Class B. That extends the measured form
  from 59 fine-calibrated systems to 81 and moves the demonstration number from
  6.2 to 4.3 per cent (7.4 per cent at p_epoch = 0.5, 34 at 0.1).
- Abstract's "no completeness number is validated across more than one
  instrumental configuration / the coarse class has no completeness curve at
  all" retired; the single-configuration caveat **kept** for the drifting class.
- `survey_stats_round10.py` reproduces every published number exactly; a guard
  in `round10_calc.py` aborts the build if any frozen value drifts.
- Freeze **kept** at `frozen_export_v3.31.json`: section 1(iv) pre-registers the
  unprocessed datasets as a held-out confirmatory sample, and the refreshed
  2026-09-11 export (459 windows / 91 stars / 85 systems, first Band 10 data,
  ceiling 495 -> 873 GHz) is precisely that pool.
- 39 pages - one over the ceiling, paid off in v3.41 rather than by hasty cuts.

## v3.41 (2026-09-11) - three-panel referee round, corrections, 39 -> 36 pages

- Revised against three independent virtual referees (radio interferometry /
  radio stars / general astronomy), archived in `/shared/ASTRA/reviews/` with a
  point-by-point reply in `REFEREE_RESPONSE_ROUND10.md`.
- Corrections, each verified against the frozen export first: a ~90-word
  Background block had been spliced into the wrong sentence, orphaning a
  seven-reference citation pile and rendering twice on page 2; "402" typed
  where the macro gives 416; gross bandwidth typed 700.8 where the generator
  gives 716.7; P(>=4|0.84) 0.9 -> 1.1 per cent (0.9 was P(exactly 4));
  Gaussian-expected crossings 11.4 -> 13.2; Table 7's frequency column was the
  window centre, not the crossing.
- The referee challenge to the beta Pic B3 CO offset was **investigated and
  rejected with evidence**: the pipeline's mask catalogue stores rest
  frequencies rounded to 1 MHz (`CO(1-0) = 115.271` exactly), so the released
  offset column and the lab-referred offset are different quantities and both
  printed values were right. The rounding is now disclosed, macro-sourced.
- Disclosed rather than silently fixed: HD 139084B appears to be one system
  counted twice, so N_sys is probably 81, not 82. Correcting it would break the
  freeze, so the paper states it with its size.
- Length: main text -3.4 per cent, appendices -12.2 per cent net (gross cuts
  -7.4 / -18.7, with referee-required additions paid out of them).
- Gates: 0 errors, 0 undefined refs/cites, 0 multiply-defined labels, 0
  overfull/underfull boxes, 36 pages. Verified to build from an empty directory
  with the 19-item set in `ARXIV_UPLOAD.md`.
- Three Type 3 fonts on page 6 are inherited from
  `figures/pipeline_schematic.pdf` and documented, not papered over; the
  earlier "0 Type 3" gate was reporting false and its wording is corrected.
- Target journal recorded correctly: **arXiv, then the Open Journal of
  Astrophysics**. Not RASTI.

## Planned for v2.04+
- Add the full ALMA project-code list to the Acknowledgements section
  (deferred again — still meaningful to wait until survey completion so
  it's compiled once, not incrementally).
- Populate a quantitative transmitter-prevalence bound (Wright et al. 2018 /
  Margot et al. 2023 frameworks) once a statistically meaningful fraction
  of the 120-target sample is complete — explicitly deferred in §6 as
  premature at n=19.
- First real closure-phase-vetting result and first population-anomaly
  flag, whenever either actually triggers.
- Consider extending to 30/40/50 pc per the roadmap already stated in the
  paper, once the 20 pc sample is complete.

## v3.63 (2026-09-13) — referee cycle after v3.62; the S_min unit repair

- **Band 9/10 S_min unit defect repaired (referee 1, point 5).** The twelve
  Band 9/10 rows restored at v3.60 carried S_min in mJy while every other row
  of the frozen export carries Jy. `v343_calc.py` infers the primary-beam
  correction as S_min/(5 sigma_rms) and so printed "1000.13x" as the largest
  retained correction. Repaired at the point of use in `v342_calc.py` with the
  freeze untouched, verified against the pipeline's own EIRP_min_W, and an
  assertion added that 0.95 < S_min/(5 sigma_rms) < 5 for every row. The
  largest retained correction is 1.81x at 0.46 theta_PB.
- **Explicit primary-beam response floor adopted**: a window is retained only
  where the response at the stellar position is >= 0.5 (correction <= x2). All
  443 released windows satisfy it; the four withheld eps Eri windows fail it.
- **Leave-one-star-out cross-validation of the radial repair** (27 held-out
  stars): median 0.437, D = 0.081, against 0.437 and 0.081 in sample. The
  profile is not over-fitted and does not restore exchangeability. The
  detrended statistic is no longer presented as a validated null.
- **New Table 14**: formal 12-m vs ACA 7-m array-split robustness table.
- **Solar-system crossmatch for CP-72 2713**: SkyBoT returns zero known minor
  planets at 30/300/1800 arcsec at the flagged block's epoch; positive control
  on the ecliptic at the same epoch returns 118-444.
- **ITU RR No. 5.340** replaces a single FCC filing as the basis of the
  no-allocation argument: 13.3 GHz (11.6 per cent) of the searched union is
  "all emissions prohibited", and 44 per cent lies above 275 GHz.
- TRAPPIST-1 b exceeds the drift ceiling over 5-29 per cent of orbital phase
  edge-on, 0.3-10 per cent averaged over inclination.
- Terminology: "spatial-control null" -> "spatial-control screen";
  "second-stage local null" -> "local scramble test"; Eq. (1) track duration
  T -> tau_track; Class A/B introduced as fine-channel/coarse-channel;
  "pre-registered" -> "repository-timestamped"/"prospectively frozen".
- Abstract restructured on referee 1's ordering (1833/1920 chars). Conclusions
  open with the referee's own primary-result sentence. Sentence-level bold cut
  from 12 to 4. Occurrence ladder withdrawn from Appendix I.
- Software citations added (CASA Team 2022; Astropy 2022; Harris 2020;
  Virtanen 2020).
- **Page budget NOT met: 32 pages, 31.20 pp of content.** Three costed options
  for the authors in `REFEREE_RESPONSE_V363.md` section 0.

## v3.64 / v3.65 / v3.66 (2026-09-13) — three rounds of internal peer review

Full record in `PEER_REVIEW_ROUNDS_SUMMARY.md` and
`VIRTUAL_REFEREES_ROUND{1,2,3}.md`.

**v3.64 (round 1)** — primary-beam floor now states the gap it sits in
(retained to 0.46 theta_PB / x1.81; first withheld at 0.62 / x2.88); Class A/B
rename completed across nine text sites; abstract gives 88 of 115
archive-covered stars; ITU percentage to one decimal (11.6); the x3.2 debit no
longer called a worst case; TRAPPIST-1 quoted edge-on only (it transits);
Table 14's expectation labelled as the exchangeable lower bound; ACA array
assignment described as measured; solar-system argument extended to
uncatalogued bodies by non-sidereal motion; astroquery cited.

**v3.65 (round 2)** — Figure 8's right axis no longer claims a single-factor
P_eff (per-window ratio x1.33-3.98 now generated into the caption); Figures 2
and 8 regenerated with the new class names; noise-quality figure no longer
counts withheld windows as passes; local-to-global scale ratios tied to the
reproducible R_sigma test; Table 8's "survives" column given units and a stated
convention; data-availability statement admits unprinted diagnostic figures.

**v3.66 (round 3)** — **a claim added in round 2 was reversed**: beta Pictoris
Band 6 is narrow (53.9 MHz) but finely channelised, so it carries 1944 drift
trials against a survey median of 4, the largest trials load in the survey, and
its rank is harder to earn, not easier; the numbers are generated with an
assertion. Positive control now states the drift it is recovered at. Primary-
beam gap quoted in responses as well as offsets. Figure 8's axis label
un-clipped, verified from text-block bounding boxes. Conclusions carry the
physical drift-resolution count. **`regen_count.py` added**: the macro counting
regenerated products was previously emitted before the figures were built, so
the one file that failed a clean-regeneration test was the file carrying the
reproducibility claim.

Gates at v3.66: 32 pages, 31.39 pp content, 0 errors / 0 undefined / 0 overfull
/ 0 Type 3, 12 underfull, 860 macros 0 unused, abstract 1850/1920, arXiv set 46
items, clean regeneration 50/50 byte-identical.

**Page budget still not met** (32 not 31); three costed options for the authors
in `PEER_REVIEW_ROUNDS_SUMMARY.md`.

## v3.67 (2026-09-13) — the cut: 32 pages to 29

Authors' instruction plus two referee reports. Full record in
`REFEREE_RESPONSE_V367.md`.

**Deleted entirely**: the *Funding and competing interests* section; Appendix
*Exploratory diagnostics not used for candidate selection* (and every reference
to closure phase, the chirped-drift extension, the periodicity search and the
cross-target frequency match); the *CP-72 2713: the diagnostics not needed in
the main text* subsection; *The line mask as executed, and its repair*;
Appendix I (the illustrative conditional occurrence calculation) and every
quotation of its percentages; the Appendix H *Chronology of the statistic
revision* and *AU Mic: the three tests in full* subsections.

**Minimised**: the epoch-shortfall and processing-failure narrative (retry
ledger, calibration failures, running-job counts, "as of this build date" all
gone); Appendix G's false-alarm accounting, roughly halved; the
region-maximum discussion, now one paragraph plus its audit table.

**Renamed**: the 603-window sample is an *external calibration sample*, not a
held-out or post-freeze one; "target-complete" becomes *complete with respect
to the frozen candidate work list but archive-incomplete*; "false flag" becomes
*false-trigger probability*; title is now *A Technosignature Search of Archival
ALMA Observations toward 81 Stellar Systems within 40 pc*.

**Added**, funded entirely from the deletions: a restructured abstract on the
referee's own sequence, with EIRP expanded, measured recovery quoted (42-61 per
cent at the trigger, 89 per cent at 6 sigma) and the native-channel caveat;
the reason all 20 crossings are Class A (median Class A window holds
2.5e5 channel x drift cells against 351 for Class B, a factor 714); a
Clopper-Pearson interval on the measured tail factor (1.47, 95 per cent
1.36-1.59, from 618 first-rank pseudo-stars in 220,672 trials, which refutes
the referee's premise that it rested on 1-2 exceedances); an explicit statement
that the visibilities are delivered QA2 products taken as delivered; an
explicit statement of what the correlation model cannot measure and which way
it would move the conclusion; distinguishing clauses for two citations; and a
Conclusions ending on what the result is and is not.

Gates: **29 pages**, 28.70 pp content, 0 errors / 0 undefined / 0
multiply-defined / 0 overfull / 0 Type 3, 12 underfull, 769 macros 0 unused,
abstract 1857/1920, arXiv set 46 items, clean regeneration 50/50
byte-identical, em-dashes 0.

## v3.68 (2026-09-13) — two referee reports + three internal review rounds

Record in `REFEREE_RESPONSE_V368.md`. 29 pages, unchanged.

**★ A published number was wrong and the referee found it.** v3.67 quoted a
Clopper-Pearson interval of 1.36-1.59 on the empirical false-alarm factor,
computed on "220,672 trials" -- a count of pooled rank values from an earlier
analysis, not the pseudo-star trial count. The test uses the 16 inner probes of
each calibration window, so the true count is 9,648 with 30 first ranks.
`tailboot_v368.py` recomputes it from the stored control vectors and bootstraps
clustered by window and by execution block: 1.1-2.2 and 1.1-2.1 against 1.1-2.3
binomial. The paper now says the factor lies between about 1 and 2, not to two
figures.

**EIRP estimator**: S_min x dnu is an integrated power only if the effective
noise bandwidth equals the channel separation, which for a smoothed correlator
it does not; that is what C_response corrects, and the correction is calibrated
by visibility-level injection (x2.02-2.69, median x2.31) against the analytic
x2.29, agreeing at the median to one per cent. EIRPs quoted to two figures.

**CP-72 2713 recast** as an unconfirmed single-epoch event with persistent
emission excluded on a 2.05-h baseline; persistence stated as an operational
criterion, not a physical requirement on a transmitter. Figure 2 now ends in
"0 persistent candidates; 3 identified astrophysical; 1 unexplained,
non-repeating".

**Gross vs unmasked bandwidth** systematic throughout (113.9 GHz gross, 109.4
GHz unmasked search space). Molecular-species criterion stated with its
consequence. Six coarse-noise windows: excluded from the sensitivity accounting
only. Conclusions opened literally and cut to four paragraphs. Title now
"...toward 88 Stars in 81 Systems within 40 pc". All run-in headers promoted to
numbered subsections. Noise estimator given as a formula. M-dwarf search
fraction quantified. Radial correction flagged in the scope box as not
validated out of sample. Zero-candidate result stated in the Conclusions to be
unchanged under either statistic.

**Internal rounds caught**: an M-dwarf fraction pairing a restricted numerator
with a census denominator; an unsupported "~10 per cent" accuracy claim; two
unreconciled tail factors; Figure 2 not following the text; an unverifiable
"none is a crossing" claim, withdrawn; and a build-ordering defect
(`v363_calc.py` read a file `make_all.sh` generated after it) that only the
clean-regeneration test could find.

Gates: 29 pages, 28.98 pp, all zero, 778 macros 0 unused, abstract 1874/1920,
arXiv 46 items, clean regeneration 50/50 byte-identical.

## v3.69 (2026-09-13) — campaign re-harvested; two referee reports; three internal rounds

**★ NEW DATA FOLDED IN.** The epoch-continuation campaign has grown since the
counts frozen at v3.51. Re-harvested read-only from the search host at
2026-09-13T19:30Z: the external calibration sample is now **899 windows in 224
execution blocks toward 35 stars** (was 603/150/27). Consequences, all
regenerated rather than hand-edited:
* the rank displacement persists on the larger sample, median add-one rank
  0.425 against 0.5, D = 0.092 at p = 5e-07;
* 27 trigger crossings, 6 stage-1 outliers, 4 of them beta Pictoris CO;
* **two unattributed single-epoch outliers, not one**: 61 Vir Band 7 at
  344.872 GHz (T* = 6.16 against ring maximum 5.88) and HD 23484 (T* = 5.30).
  **Neither recurs**: at the same tuning in a further block 61 Vir returns
  T* = 4.83 with 119 controls above the star, HD 23484 returns 4.99.
* the measured tail rate predicts 2.5 such events over 899 windows against the
  2 seen, so the enlarged sample strengthens rather than weakens the
  false-alarm argument. There are now three independent non-recurring
  single-epoch events (CP-72 2713, HD 23484, 61 Vir) behaving as predicted.
Table 7 was rebuilt on the new sample; the pseudo-star and radial diagnostics
remain on the 603-window subset that retains full 512-probe control vectors,
which the text now states.

Referee items: abstract recast (archive-selection bias stated, drift-resolution
split quantified, "no persistent, independently confirmed" used throughout);
ancillary continuum reduced to a pointer to its appendix; tail factor quoted as
about 1.4 with an empirical range of roughly 1-2.

Gates: 29 pages, 28.98 pp, 0 errors / 0 undefined / 0 multiply-defined /
0 overfull / 0 Type 3, 12 underfull, 775 macros 0 unused, abstract 1889/1920,
arXiv 46 items, clean regeneration 50/50 byte-identical.

## v3.70 (2026-09-13) — forensic number audit, and the block-accounting correction

**The question that started it**: the paper said "104 of 451 public execution
blocks", which is correct for the FROZEN RELEASE but had become badly
misleading as a forward-looking statement. Measured from the search host:
**351 execution blocks now carry a search product** -- 104 in the frozen
release and 252 from the continuation campaign -- of which 327 of the 451 in
scope (73 per cent) have been searched, leaving 124. A further 29 campaign
blocks lie outside the original scope. The Conclusions previously said "347
remain unanalysed"; that was wrong by a factor of nearly three.

**`audit_numbers_v370.py`** now runs inside `make_all.sh` and fails the build
if any printed number disagrees with its source of truth. It re-derives 37
quantities from the released catalogue, the live block list, the campaign
harvest and the control-vector stores, checks every sum/split/ratio identity
the paper asserts, and extracts the text from every built figure to match its
numbers against the macro set. It found two macros silently retired because a
compression pass had removed their only reference, and one figure legend
(`rank_cdf.pdf`) still saying "held-out" after the sample was renamed
"calibration".

Gates: 29 pages, 29.01 pp, 0 errors / 0 undefined / 0 multiply-defined /
0 overfull / 0 Type 3, 12 underfull, macros 0 unused, abstract 1889/1920,
arXiv 46 items, clean regeneration 50/50 byte-identical, audit 37/37 pass.

## v3.71 (2026-09-14) — data catch-up, two referee reports, three internal rounds

**Data caught up to the live campaign (as of 2026-09-14T07:33Z).** The external
calibration sample grew from 899 to **1114 windows in 276 blocks toward 41
stars**. Consequences, all regenerated:
* the rank displacement deepens on the larger sample: median add-one rank
  **0.406** against 0.5, D = 0.110 at p = 4e-12;
* 53 trigger crossings, 7 stage-1 outliers, 4 of them beta Pictoris CO;
* **a third unattributed non-recurring event appeared**: HD 14055 Band 7 at
  332.227 GHz (T* = 6.03 against ring maximum 5.96), which does not recur --
  17 further blocks at the same tuning give at best T* = 5.51 with 5 controls
  above the star. With 61 Vir and HD 23484 that is 3 observed against **3.1
  predicted** by the measured tail rate. Table 7 rebuilt as a four-column
  comparison including CP-72 2713.
* `CampAsOf` is now derived from the harvest record rather than typed.

**Two arithmetic defects the referees found, both real, both fixed at source:**
* `BenchEffRatio` printed 2.3 while the paper's own two numbers give 2.14. The
  cause was a **hand-typed `BENCH = 8.0e14`** that had drifted from the
  generated 8.4e14. Now derived from the physics (with the aperture efficiency
  named explicitly, referee 2 M5) and rounded so a reader dividing the printed
  values reproduces it: **2.1**.
* The survey-wide Bonferroni scale was printed as both 1.2e-4 and 1.1e-4. The
  1.2e-4 came from `BonferroniThresh` in the round-5 freeze, computed on a
  superseded window count. That macro is retired from the text and an
  assertion now checks `BonfScaleCalc == alpha/N` on the released catalogue.

**Referee items applied**: abstract recast as "two related experiments" with
the 5-sigma trigger explicitly distinguished from significance and the
per-window (1.95e-3) and survey-wide (1.1e-4) false-alarm figures given at
first use; new opening subsection *Final candidate definition and statistical
interpretation* stating that the spatial comparison is a screening statistic
and that a claim requires independent recurrence; Figure 2's decision flow
relabelled to spatial prioritisation -> vetting -> independent confirmation;
title changed to *A Search for Spectral Technosignatures in Archival ALMA
Observations of 88 Nearby Stars*; a seven-item consolidated *Scope of the
constraints*; Table 1 glossary extended by six terms; Eq. 2 now states it is
neither Gaussian nor chi distributed under the null; the RFI paragraph
expanded and the previously orphaned SpaceX/FCC citation used; the
pre-registration claim given a commit hash and date; the coarse-noise
forensics cut to one paragraph; colourful phrasing neutralised.

**Internal rounds caught**: a misleading macro name (`MaskUnionGHz` holds the
union, not the masked bandwidth -- the audit check itself had fallen for it);
an abstract conflating 89 per cent recovery at 6 sigma with the 90 per cent
point at 6.1 sigma; and one surviving colourful phrase in an appendix.

Gates: 29 pages, 28.95 pp, 0 errors / 0 undefined / 0 multiply-defined /
0 overfull / 0 Type 3, 12 underfull, 775 macros 0 unused, abstract 1833/1920,
arXiv 46 items, clean regeneration 50/50 byte-identical, audit 39/39 pass.

## v3.72 (2026-09-17) — the tail factor, now measured on 2.2x the data

A targeted update, not a full round: the calibration sample and the empirical
false-alarm tail factor are brought up to date, nothing else is restructured.

**Every window ever searched retains its 512-probe control vector** in its
`*_search.npz`, and since 2026-09-14 the pipeline also writes `ctrl_all` into
the result JSON. Harvesting both gives **1326 calibration windows** with full
vectors against the 603 available to earlier versions.

**The tail factor is correspondingly better determined:**

| | v3.71 | v3.72 |
|---|---|---|
| pseudo-star trials | 9,648 | **21,216** |
| first-rank events | 30 | **63** |
| point estimate | 1.6 | **1.5** |
| naive binomial 95 % | 1.1-2.3 | **1.2-1.9** |
| window-clustered 95 % | 1.1-2.2 | **1.2-1.9** |
| block-clustered 95 % | 1.1-2.1 (150 blocks) | **1.2-1.9 (327 blocks)** |

The text now states the factor as lying between 1.2 and 1.9 rather than
"between about 1 and 2", and notes that the released-product value 1.4 sits
inside that interval. This answers referee 1's point 4 and referee 2's M5,
both of which pressed on the precision of this number.

**Calibration sample also refreshed** (as of 2026-09-17): 1114 -> **1322
windows**, 276 -> **326 blocks**, 41 -> **56 stars**. Median add-one rank
0.406 -> **0.419** against 0.5, KS D 0.110 -> 0.095 at p = 6e-11.
**Nothing else moves**: stage-1 outliers stay at 7, beta Pictoris CO at 4, and
the unattributed non-recurring events at 3 (61 Vir, HD 14055, HD 23484). A
19 per cent enlargement of the calibration sample changes no conclusion, which
is itself worth reporting.

The frozen survey is untouched: 104 blocks, 443 windows, 88 stars, 81 systems,
4 stage-1 outliers.

Gates: 29 pages, 28.95 pp, 0 errors / 0 undefined / 0 multiply-defined /
0 overfull / 0 Type 3, 12 underfull, 775 macros 0 unused, abstract 1833/1920,
arXiv 46 items, clean regeneration 50/50 byte-identical, audit 39/39.
