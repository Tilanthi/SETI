# Response to Referee Reports — Round 4 (v3.33 → v3.34)

**Manuscript:** An ALMA Archival Search for Spectral Technosignatures toward
Stars within 40 pc: Methodology and First Survey Release
**New version:** `technosignatures_20pc_v3.34.tex` / `.pdf` (38 pages — identical
to v3.33's page count, per the length constraint; every addition was offset by
equal or greater trims).
**Build state:** pdflatex ×2, 0 errors, 0 undefined references, 38 pages,
0 Type 3 fonts, no text or rule beyond the type block (programmatic page scan,
all 38 pages), appendices lettered A–R with all in-text references resolving to
letters, **zero overfull hboxes** (better than v3.33 — see R2 minor on box
styling: the two long-standing "baseline" overfull warnings were this same
defect, now fixed at source).

Where the referees offered options, our choice is stated. Where an item asks
for computation on visibility-level data, we state plainly what was and was not
possible in this revision cycle (no cluster access; the frozen export stores
per-window statistics, not visibilities) and what the text now says instead.

---

## Referee 1 (Major revision)

### R1-1 — Reframe as an interim survey release
**Done.** The abstract, §1, §7 (Discussion) and the Conclusions now carry the
developmental-release framing at first mention, not only in §5.5: 107 of 208
planned target/bands (51 per cent), sensitivity-ranked subset, thresholds that
"apply to the 88 processed stars and will not fill in symmetrically" as the
remaining, farther, differently band-distributed datasets arrive. The
statistic-and-mask circularity caveat is front-loaded into the abstract and
Conclusions (also R2-1 below).

### R1-2 — "Narrowband" needs tighter qualification
**Done, including retitle.** The title now reads "Spectral Technosignatures"
(v3.33's title used "Narrowband"); a sentence at the start of §4 states
verbatim the referee's point: "narrowband" describes the assumed intrinsic
signal morphology, not the spectral resolving power of the observations, and in
most windows an intrinsically Hz-wide carrier would be unresolved inside a
15.625-MHz channel. Coarse windows are stated to measure amplitude but not
drift rate (313 of 431 windows).

### R1-3 — Terminology for what is actually detected
**Done.** Adopted "unresolved spectral-carrier search at native ALMA
resolution" for the experiment, with "narrowband" reserved for the assumed
transmitter morphology (same edit as R1-2).

### R1-4 — Injection/recovery needs cleaner quantitative presentation
**Done.** The transfer error now has an analytic anchor where one exists:
coherently averaging N_int on-source integrations suppresses noise as
√N_int, so the amplitude anchor can shift by at most √(5274/21) ≈ 16 between
the shortest and longest windows, and the calibration configuration (1506 s
on source) sits a factor 1.2 in √t_on from the median fine window (2177 s).
Channel-count and primary-beam-offset terms admit no such bound and are said
to need new injections — honestly demarcated, not claimed.

### R1-5 — Completeness too weak for 6.2% as headline
**Done (option: demote).** 6.2% is demoted everywhere in prose to "an
illustrative conditional in-band transmitter fraction above EIRP 10^16 W,
approximately 6 per cent" — tables keep the computed 6.2. The subsection is
retitled "Conditional transmitter-fraction limits"; the abstract's conditional
clause now precedes the number (also R2-5).

### R1-6 — Occurrence calculation conditional
**Done.** The "What is and is not being inferred" passage now states the
quantity is "an effective survey detection fraction under heterogeneous
frequency support", defined on the 82 processed systems, not a prevalence.

### R1-7 — Frequency hypothesis differs per star
**Done.** Per-system frequency sets F_i are stated as part of the conditioning
(the reading-rule box and the effective-detection-fraction clause).

### R1-8 — Retrospective development of the statistic
**Done.** The retrospective-validation status is stated in the abstract, §5.5,
Discussion and Conclusions; Table 4 (validation history) remains the single
tabulation of pre-freeze changes; the main text describes the final pipeline
and defers narrative history to the validation appendix (also R1-19).

### R1-9 — ±50 km/s mask is post hoc
**Done (option 2: retrospective designation + pre-registration).** The mask's
application to this release is now labelled retrospective in §5.1, and the
same ±50 km/s stellar-frame definition is pre-registered, unchanged, for all
remaining planned datasets: "the confirmatory sample tests a frozen rule, not
a tuned one." (Option 1 — deriving the mask from a literature velocity
distribution — would be a new analysis masquerading as a justification for a
rule already applied; we chose the honest pre-registration route.)

### R1-10 — Control-ring exchangeability validation
**Partially done; one part declined with reasons.** §4.1 now gives the ring
geometry in full: single ring centred on the target, 512 positions evenly
spaced in azimuth (0.70° apart), radius well inside the primary beam and many
synthesised beams from the target; effective independent count N_eff ≈ 30–43
from symmetric reprocessing. The primary-beam term is now bounded
analytically: an off-axis control's extracted amplitude is attenuated by
G(r) = exp[−2.77 (r/θ_PB)²] while the visibility-domain thermal noise carries
no such factor, so control statistics are suppressed relative to the star —
a one-sided bias that can only inflate star-exceeds-ring events under the
null, the conservative direction for every "consistent with chance"
disposition in this release. What we could NOT add: per-control holography
gains (the frozen export stores 512 control statistics per window, not
positions or gains; visibility-level re-extraction was not possible in this
cycle). That measurement remains flagged in the text as a required item for
the completed survey.

### R1-11 — 512-control p-value floor
**Done.** §4.1 now states the floor explicitly (p ≥ 1/513): the ring
calibrates the false-alarm rate but cannot authenticate an individual
candidate; a window at the floor passes to the enlarged local-null protocol
of §7 (10^4–10^5 evaluations) — a two-stage design, stated as such.

### R1-12 — CP−72 2713 deserves a stronger test now
**Declined with reasons; dispositions strengthened textually.** The requested
enlargement needs new control positions, which requires visibility-level
re-extraction — not possible in this revision cycle (no cluster access; the
frozen products do not carry visibilities). The paper now says exactly this
and names the faster arbiter already scheduled: the re-observation at
345.1152 GHz, which needs no reprocessing. Table 20's new disposition column
(see R2 tables) labels this window "marginal — held pending the scheduled
re-observation", and the promote/retire criteria are unchanged.

### R1-13 — CO detections as positive control
**Done.** New subsubsection "Astrophysical positive controls" (β Pic): what is
recovered is quantified — frequencies to the frame chain's stated tolerance;
velocities agreeing within 0.9 km/s across three epochs and both transitions;
localisation at the stellar position. Not quantified: flux against calibrated
imaging (Matra et al. 2017), stated as such. "A known line remains the more
convincing end-to-end control precisely because nothing about it was tuned."

### R1-14 — Noise failures must be resolved
**Done to the limit of the retained products.** §5.3 now grounds the QC cut
physically (radiometer relation σ√(t_on Δν_ch) ≈ SEFD/√N_bl; a window >100×
below the sample median cannot be a real measurement) and characterises the
failure mode: reproducible, confined to coarse-channel windows, to be named in
the completed survey's pipeline release — but unable to touch a retained
window, whose σ√(t Δν) sits within the normal range.

### R1-15 — Median/100 threshold as primary criterion
**Done.** The median/100 cut is now presented as a physical-screening
criterion with the radiometric grounding above, not an arbitrary percentile;
the text states what it would and would not pass.

### R1-16 — Caution vs centimetre-wave surveys
**Done.** §6.1 now states the comparison is a power-scale comparison between
an unresolved continuous carrier and an Arecibo-like planetary radar whose
bandwidth, modulation and beaming would differ from the model signal — not a
simulated-radar equivalence.

### R1-17 — "Arecibo-equivalent power" wording
**Done.** Same edit family: "an unresolved, continuous carrier whose *total*
EIRP matches an Arecibo-like planetary radar is recovered toward the nearest
systems at 15.625-MHz channel resolution — a power-scale comparison, not a
simulated radar."

### R1-18 — Duty-cycle terminology
**Done.** D_epoch (epoch duty cycle, Bernoulli over n_i execution blocks) is
now defined against f_dwell (intra-track dwell fraction, the injection
campaign parameter); Table 12's column head and caption use D_epoch, and the
duty paragraph states the distinction explicitly.

### R1-19 — Shorten methodological history
**Done in structure.** The main text describes the final pipeline; pre-freeze
narrative is concentrated in the validation appendix and Table 4, with one
pointer from §4. Residual mentions are one clause each (e.g. the withdrawn
per-unit-bandwidth convention, logged with the other validation changes).

### R1-20 — Introduction: state the question sharply
**Done.** §1 now leads with the explicit question — how strongly can existing
ALMA observations constrain unresolved artificial spectral emission from
nearby stellar systems? — followed by the five objectives in the referee's
own structure (define sample → search → empirical false-positive distribution
→ injection sensitivity → conditional constraints). The M-dwarf
over/under-representation sentence and the TRAPPIST-1-like inner-orbit point
are included (also R2-8).

### R1 abstract
**Done.** Cut by a factor of two; the first sentence states this is a
technosignature search amongst the closest star systems in the ALMA archive;
the conditional clause precedes the ~6 per cent number.

### R1 figures
Figs 1, 3, 4, 5, 9, 11, 12 reduced 30%. Fig 9 says "nominal trigger
threshold" at every occurrence; Fig 11's curve is labelled "conditional model
limit — illustrative, not a prevalence bound"; Fig 2 distinguishes
fine/coarse windows; Fig 4 is labelled as the dwell experiment, not threshold
completeness. Fig 7 retained.

### R1 minors
- Terminology: glossary (Table 2) definitions used throughout; the six
  denominators (168/88/82/107/102/431) appear with their nouns.
- "5σ limit" sweep: no remaining instances; "nominal 5σ trigger threshold"
  convention holds everywhere (verified by text search).
- "Upper limit" reserved for confidence statements (reading-rule box, §6.2).
- Significant figures: 6.2 → ~6 in all prose (tables keep the computed value);
  the duty-scenario values (10.8, 48) are scenario brackets, not precision
  claims, and keep one decimal as labels.
- Title: single exact title adopted (see R1-2); running heads match.

### R1's four acceptance conditions
1. Developmental/51%-release framing — done (R1-1).
2. Native-channel excess vs Hz-scale narrowband clarified — done (R1-2/3).
3. 6.2% demoted to illustrative conditional — done (R1-5).
4. Control-ring validation strengthened; CP−72 with larger ensemble —
   first part done analytically (R1-10); the larger ensemble declined with
   stated reasons (R1-12) and the window is dispositioned "marginal, pending
   re-observation" in Table 20.

---

## Referee 2 (Minor-to-moderate revision)

### R2-1 — Circularity caveat front-loaded
**Done.** Abstract + Conclusions now carry it at first mention (with R1-1).

### R2-2 — Single-configuration completeness transfer
**Done to the analytic limit.** The √N_int bound and the calibration window's
position within the on-source span are now stated (R1-4); the unbounded terms
are named and confined to future injections. New macros
(\IntGainSpan, \FineOnsrcMedian, \CalibOnsrc, \CalibGainRatio) are generated
from the frozen export via make_numbers.py, like every other survey number.

### R2-3 — CP−72 2713 now
**Declined with reasons** (R1-12): visibility-level re-extraction not possible
this cycle; the scheduled 345.1152 GHz re-observation is the faster arbiter;
disposition column now labels the window unambiguously.

### R2-4 — 51%-complete publication framing
**Done.** More prominent: abstract, §1, Discussion (with R1-1). The §7 note on
how to treat later candidates for already-included stars: this release's
frozen products supersede; discrepancies resolve in their favour; updates by
erratum against the named snapshot.

### R2-5 — Abstract caveat ordering
**Done.** Conditioning clause precedes the number (referee's suggested
inversion adopted).

### R2-6 — Epoch independence / periodic transmitters
**Done.** The duty paragraph now uses the epoch-spacing data: blocks span
2013 October–2025 June; 18 of 82 systems are multi-epoch (13×2, 5×3);
rotation- or orbit-tied beacons enter at effectively random phase and average
into the Bernoulli model; a schedule correlated with the sampling could read
as intermittent or be missed entirely; with ≤3 epochs there is no power to
detect periodicity itself, and the ladder is a phase-averaged bound.

### R2-7 — Satellite-constellation RFI
**Done.** New §4.4 paragraph: constellation downlinks near 10–40 and 37–75 GHz
lie below every band searched (Band 3, the lowest, starts at 84 GHz); the
transient-pass case is addressed (per-integration extraction, drift-stack
smearing quantified); a dedicated per-integration RFI screen is named for the
next release.

### R2-8 — Sample composition vs astrobiological relevance
**Done.** §3 states the F/G over-representation and M-dwarf
under-representation and its consequence for scoping the limit; Fig 16's
drift-ceiling point (TRAPPIST-1 b-like orbits at the ceiling) is cited in the
same sentence.

### R2-9 — White (2026) cross-paper bookkeeping
**Done as far as author input allows.** The clarifying sentence is in
("Where a star is treated in both, the numbers to cite are this release's
frozen products; any discrepancy resolves in their favour."). The citation's
final status (arXiv id / acceptance) is flagged as author input — the
manuscript carries a marked TODO for the authors; we have not resolved it
ourselves.

### R2 tables and figures
- **Table 5 overflow:** fixed with line wraps in the first-column labels; all
  wide tables (5, 18, 21, 23, 24) audited by the programmatic page scan.
- **Table 20 disposition column:** added ("Disp.": fg CO / cs CO / marginal /
  chance, keyed in the caption; cross-referenced to Table 7 and §5.4–5.5).
- **Figure 11 annotation:** the thresholded C≡1 square from Table 11 is
  marked on the curve with an explicit caption pointer (verified present).
- **1.0% ALMA-covered census fraction:** echoed in §3 (verified present).

### R2 minors
- **Box styling consistency:** the §6.2 "Reading rule" box now uses the
  identical rule-delimited construct as the §4 box. Fixing this surfaced a
  real defect: the closing rules of all four such boxes were being appended
  to the running paragraph's last line and rendered past the page edge
  (clipped at the paper boundary — the two long-standing "benign baseline"
  overfull warnings). All four now end their paragraph before the closing
  rule; the rules render exactly 51–562 pt on every page, and the build has
  **zero** overfull hboxes.
- **Arecibo + Earth-leakage restated in a figure note:** Fig 9's caption now
  carries both benchmarks (2×10^13 W radar line; ~4×10^9 W leakage below
  every threshold shown).
- **Table 9 peak drift:** caption now explains the ~10–20 per cent spread —
  each treatment recomputes the drift-stack maximum over a differently
  weighted cube, so the maximum settles on an adjacent part of the drift
  grid; the spread measures the drift-location uncertainty of a ≤2.5σ
  per-channel feature, not physical drift evolution.
- **Czech references:** initials unified (D.~J. in both); same author, two
  works, correctly differentiated.
- **MOUS / QA2 at first use:** parentheticals present at first use in §4
  (verified); MOUS appears only in the glossary.
- **Arithmetic consistency:** every survey number is a generated macro from
  the frozen export (make_numbers.py → survey_numbers.tex); the new transfer
  macros follow the same chain. Final pass verified the cross-quoted values
  (431/513 = 0.84; P(≥5|0.84) = 1.7×10^-3; 20 crossings / 4 exceedances in
  Table 20 vs Table 6/Fig 12).
- **Sentence register:** the longest sentences (Conclusions opener; the
  exchangeability "Two stratifications" sentence) are split; a light pass was
  made over §5.4's densest passages.

---

## Items we did not do, and why (consolidated)

1. **Enlarged CP−72 control ensemble / trial-level logging / new injection
   configurations / per-control primary-beam gains / per-integration RFI
   screen** — all require visibility-level re-extraction or new compute on
   the pipeline cluster, neither available in this revision cycle. Each is
   named in the text as a required item for the completed survey, with the
   scheduled re-observation as the faster arbiter for CP−72.
2. **Literature-derived mask width (R1-9 option 1)** — chose pre-registration
   instead (reasons at R1-9).
3. **White (2026) citation status** — author input; flagged in the source.

## Length accounting

Additions (disposition column + caption key, box conversions, transfer-bound
and duty/epoch/satellite/M-dwarf passages, Fig 9 note, Table 9 sentence) were
offset by: the halved abstract, the §5.5 γ Lupi compression, the
methodological-history consolidation (R1-19), the reframe-and-trim of the
dispositions subsection, the split-and-tightened Conclusions opener, and the
30% figure reductions. Final: 38 pages, identical to v3.33.
