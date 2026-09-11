# Referee response — round 6 (v3.36)

Paper: "An ALMA Archival Search for Spectral Technosignatures toward Stars
within 40 pc: Methodology and First Survey Release"

Both reports addressed below, item by item. Standing constraint honoured
throughout: **the paper did not grow** — v3.36 compiles to the same 38 pages
as v3.35 (0 errors, 0 overfull boxes), with every addition offset by trims of
repetitive or non-essential text and by retiring redundant floats (see
"Length discipline" at the end). All new survey numbers are generated macros
(`survey_numbers_round6.tex`, computed by `round6_calc.py` from the same
frozen export as every previous round); none is hand-typed.

Where a referee offered options, our choice is marked **Decision**.

---

## Referee 1

**R1-1 (P_trig vs P_x must be central; abstract wording; Figs 1 and 9 axis
labels).** Done. The boxed rule "How to read every limit in this paper"
(§4.1) now defines the two named quantities — trigger power P_trig =
EIRP_5σ and completeness P_x — and states explicitly that P_50 = 1.10
P_trig and P_90 > 2 P_trig only for the calibration configuration's
drifting class, with every other configuration marked "not determined"
rather than left implicit. The abstract carries the requested form
(nominal trigger-power range; "these are not completeness limits"; the
measured 42 per cent recovery at 5σ for the fine-channel drifting class
immediately after). Figures 1 and 9 were regenerated with the y-axis
label "EIRP_5σ trigger threshold (W) / (nominal, not a completeness
limit)" on the axis itself, not only in the caption.

**R1-2 (occurrence analysis demoted to illustrative framework).** Done.
§6.2 is retitled as an illustrative population-inference framework; the
abstract's single sentence states that completeness is calibrated for
only a subset of fine-channel configurations and population limits are
illustrative rather than survey-grade. The Conclusions quote the bracket
with its conditioning attached, never a bare limit. The "prior spread ⇒
constraint disappears" point is now quantitative in §6.2: under a uniform
transmitter-frequency prior the per-system F_i average 4.5e-3 (Bands 3–8)
and sum_i C_i = 0.27, so the product likelihood excludes nothing — stated
as the reason the conditioning supplies the entire content of the numbers.

**R1-3 (false-alarm framework; MC pseudo-target validation).** The three
complications are now separated explicitly: (i) the 1/513 rank floor vs
the 1.2e-4 family-wise threshold (the floor is a resolution, not a
significance; a single window cannot reach survey-wide significance —
said at the flagging site and in the trials box); (ii) the fine-stratum
uniformity failure (p=0.015) is stated as a failure of demonstrated
exchangeability for that stratum and traced to the four astrophysical
crossings themselves; (iii) rank resolution (512 positions) vs effective
independent spatial trials (N_eff ≈ 30–43) are distinguished in the
trials box and Table 2. **Decision:** we implemented the recommended
Monte Carlo pseudo-target validation on the frozen products: each trial
draws one control per window uniformly from its ring as the pseudo-star
and passes it through the operative gates (T ≥ 5σ, then the velocity
mask). The expected count of pseudo-target windows flagged by the full
procedure is 0.20 (82 per cent of trials flag none), lying below the
rank-only budget of 0.84 because every added gate only removes; on the
384 windows of stars outside the development set the same procedure
expects 0.17 and the control ranks remain uniform (KS p = 0.73) — the
empirical survey-level false-positive calibration the referee asked
for, replacing the approximate Poisson argument (§5.2).

**R1-4 (CP−72 2713 as unresolved follow-up target).** Done. Terminology
changed throughout to "unclassified; statistically non-significant at
survey level". The full treatment now sits in Results (§5.4): margin
0.13 at the rank floor, the star's own other-window control maxima
(5.16–5.85) showing its rings reach 5.81 routinely, the wider-catalogue
re-query (closest entry H13CN 4−3 at −195 km/s), pinned promote/retire
criteria (promote: recurrence at an independent epoch, or p < 1.2e-4
requiring ~10^4 controls; retire: clean second epoch or catalogued
identification), and why enlargement needs visibility-level
re-extraction the frozen products do not carry. The requested properties
table is Table "Observational properties of the CP−72 2713 Band 7
crossing, as needed to plan or re-observe it" (frequency 345.1152 GHz,
date, bandwidth, implied EIRP 8.26e14 W nominal / 9.60e14 W at the
re-observation sensitivity, drift, on-source time, distance 36.7 pc).

**R1-5 (mask is post-hoc for this release).** Done. Table 5's caption and
§5.4/App J now state the developmental/confirmatory split in exactly the
referee's terms: the ±50 km/s width was fixed after inspecting the β Pic
crossings it must exclude, so its application to the four flagged
windows is a developmental disposition, while the now-frozen rule is the
confirmatory criterion for the remaining datasets. The ±20/±30/±50/±100
km/s insensitivity result is in the main text (§5.4), with the statement
that CP−72 2713 remains the sole unattributed exceedance under every
plausible width; the Discussion and Conclusions both name the mask as a
post-hoc adjustment.

**R1-6 (two formal survey classes).** Done. Class A (drift-sensitive
spectral search; 118 fine-channel windows) and Class B (unresolved
excess-power search; 313 coarse windows) are defined formally in §4 and
carried through: results are given per class first and combined only
where appropriate; Figures 1 and 9 mark the classes visually (filled =
Class A, open = Class B, with legend entries stating "completeness
calibrated" vs "completeness not calibrated"); Figure 10's framing and
the Conclusions use the class language; the exposure table separates the
fine/coarse bandwidth unions (23 vs 77 per cent).

**R1-7 (coarse-window end-to-end completeness).** **Decision:** a new
injection campaign across representative coarse configurations cannot be
run before publication (no reprocessing capacity in this release cycle;
the campaign products are frozen), so we took the referee's alternative:
the occurrence-rate calculation is presented as excluding the coarse
sample — completeness is calibrated for the fine-channel drifting class
only, Class B is labelled "completeness not calibrated" on the figures,
and the abstract makes the fine-only calibration explicit. The planned
campaign is listed as future work with the configurations specified.

**R1-8 (low-noise defect windows).** The defect forensics are now a
dedicated appendix (Q) with a per-window table carrying the requested
properties (antennas, baselines, channel width, effective integration,
weights, visibility units before/after calibration, flagged fraction,
theoretical vs measured rms). Root cause: the anomalous normalisation
enters at the per-window weights step; the table shows where measured
rms departs from theoretical. §5.3 adds the explicit statement of
whether the defect could recur undetected below the empty-gap threshold
(it cannot silently: the gap between the six windows and the retained
population is >3 decades, so any recurrence lands in an empty region
flagged by the same screen).

**R1-9 (census terminology).** Done: "archive-conditioned 40-pc census"
and "ALMA-covered 40-pc sample" throughout; "census of the local stellar
population" never appears without the qualifier attached.

**R1-10 (development/confirmation split as a design feature).** Done: a
boxed statement at the end of the Introduction states the split in the
referee's own terms (the present datasets are the development sample on
which statistic and mask were established; the remainder constitute the
held-out confirmatory sample under frozen rules).

**R1-11 (drift ceiling as physical selection function).** Done. The
ceiling is presented as "the adopted drift-rate search domain" (not
"plausible drift rates"), with the new figure relating 12–13 Hz/s/GHz to
line-of-sight acceleration vs orbital period for host masses 0.09–1.8
Msun; TRAPPIST-1 b/c/d are placed against the boundary (0.31 / 2.14 /
1.07 m/s²), and the text states that artificial emitters need not lie
inside the planetary manifold.

**R1-12 (Arecibo benchmark qualification).** Done on the figure itself:
the regenerated Figures 1 and 9 carry the in-plot label "Arecibo-like
radar: power-scale benchmark", with the caption retaining "a
technological power scale, not a model".

**R1-13 (EIRP channel-width derivation).** Done: §4.1/App C derive it in
three lines (δν_tx << Δν_ch ⇒ channel dilution S_ν,ch = F_line/Δν_ch ⇒
EIRP = 4πd² S_ν,ch Δν_ch), with the worked UV Ceti example and an
explicit warning against comparing with 1-Hz or 3-Hz SETI limits; §4.1
now forward-references the worked example.

**R1-14 (standard multidimensional exposure).** Done: new exposure table
(by channelisation class): systems, frequency unions (fine/coarse/all:
29.4 / 83 / 93 GHz), Σ t Δν = 393 s·GHz, star-hours 60, median on-source
35 min, C(ν) covered-bin median/peak star-hours.

**R1-15 (length; abstract; figures; data availability).** See "Length
discipline" below for what was cut. The abstract was restructured in the
previous round to the four-content form (searched / sensitivity / found
/ meaning) and retains 88 stars, 431 windows, 118 vs 313. **Decision on
the Fig 1 second panel:** we kept a single panel — the channel-width
caveat is now carried by the in-figure footer (the ~10^6 rescaling
factor statement), symbol size, and the axis label, rather than a second
(P, Δν) panel; the two-panel variant could not be accommodated at fixed
page count without retiring the per-star information the figure exists
to show. Fig 2 was already early (§3). Fig 6's anomalous stratum is
discussed at the figure. Fig 7 now carries the expected-maximum
distribution: the bootstrap of the ring-maximum distribution gives a
median maximum of 4.56 (90th pct 5.85) against the flagged 5.81–5.97
features. Fig 11 carries "illustrative conditional" inside the plotting
area (axis label) and the product-likelihood model in the footer. Data
availability: `make paper` single-command regeneration is stated; the
Zenodo DOI and the exact commit hash are flagged as author actions at
submission (TODO comments in the source).

**R1 minimum-acceptance list:** all five items addressed (segregation of
completeness by class, R1-7 decision; occurrence demoted, R1-2;
512-position rank meaning clarified + MC calibration, R1-3; CP−72
unresolved-but-non-significant, R1-4; developmental/confirmatory split,
R1-5/R1-10; defect windows characterised, R1-8; shortened, R1-15).

---

## Referee 2

**R2-1 (circularity quantified + held-out check + abstract statement).**
Three parts. (a) The pseudo-target Monte Carlo of R1-3 quantifies the
effect on the false-alarm side: the full frozen procedure expects 0.20
flagged pseudo-target windows (0.17 on the 384 windows of stars outside
the development set, where control ranks remain uniform, KS p = 0.73)
— the in-sample tuning does not inflate the empirical flag count above
the rank-only budget, and the 4–19 per cent Wilson bracket on P(F≥3) is
presented as the sensitivity of the accounting to the frozen choices,
read against this measured expectation. (b) The held-out check that
re-derives false-alarm behaviour on data not used in the statistic's
development is the outside-the-development-set split above (the
statistic was developed on the release; those 384 windows use the
frozen rules only). (c) The abstract and §1 now state that the
false-alarm calibration of this release is retrospective developmental
validation, with the remaining survey sample as the first independent
confirmatory dataset. Visibility-level reprocessing for a fully
independent field set (blank-sky calibrators) is declined with reasons
(see R2-7).

**R2-2 (methods-paper framing).** **Decision:** keep the current framing
—"Methodology and First Survey Release" in the title—with the referee's
alternative absorbed: §1 and the Conclusions now state up front all
three provisos ((i) completeness measured on one configuration,
(ii) false-alarm calibration retrospective, (iii) half the intended
census), so no reader needs §4.6/§5 to discover them.

**R2-3 (completeness transfer; abstract number).** **Decision:** no new
injection configurations can be measured in this cycle (frozen
campaign products; no reprocessing capacity — declined with reasons), so
the abstract presents the occurrence-limit as a bracketed range with no
central value and the word "illustrative" attached; the single
central ~6 per cent figure no longer appears anywhere as a standalone
quotable number. §6.2 states the transfer is an assumption with
unbounded error.

**R2-4 (73 per cent no drift discrimination; abstract + Fig 1).** Done:
the abstract states the fraction of searched bandwidth with drift
discrimination (23 per cent fine / 77 per cent coarse), and Figure 1 now
visually separates the two populations (filled Class A vs open Class B
points, legend in the figure).

**R2-5 (channel-width annotation on Fig 1).** Done on the figure itself:
the regenerated Figure 1 footer states the channel-width convention and
the ~10^6 flattering factor a naive 1-Hz rescaling would introduce; the
axis label names the trigger threshold. **Decision:** the second
"rescaled to 1 Hz" panel was not added — the footer statement carries
the warning without presenting a non-physical rescaled dataset at fixed
page count.

**R2-6 (demographics caveat in Conclusions).** Done: one unambiguous
sentence in the Conclusions — the transmitter-fraction bound applies
only to the archivally observed, F/G-enriched subsample searched here
(3.1–3.4× over-representation; M dwarfs under-represented) and cannot be
extrapolated to the 40-pc population.

**R2-7 (independent validation of the symmetric statistic).** What does
not share the 512-control structure: (i) the pseudo-target Monte Carlo
(re-controls re-drawn per trial, R1-3); (ii) the AU Mic three-treatment
re-analyses (recalibrated visibilities, independent epoch — Table 6);
(iii) the machinery-only injection lane. **Decision:** applying the
frozen statistic to blank-sky calibrator fields requires
visibility-level re-extraction that the frozen release products do not
carry and that cannot be run in this cycle; it is pre-registered as the
first item of the confirmatory sample. Declined with reasons, not
silently dropped.

**R2-8 (vocabulary crosswalk).** Done: Table 2's nomenclature gains a
crosswalk row — "control-ring exceedance" ≈ the "hit"/"event" of
Enriquez 2017 / Margot 2023; SP statistic ≈ S/N with an empirical
false-alarm probability via the control ring — with a sentence at first
use in §4.

**R2-9 (consolidated trials chain).** Done: a boxed worked example in
the "How to read" style walks one continuous chain — raw channel×drift
cells (4.60e7) → channel-correlation correction (ρ_lag1 = 0.989–0.991 ⇒
8.5e4–1.1e5 effective cells) → 512-position control-ring rank (floor
1/513, N_eff 30–43) → family-wise 1.2e-4 Bonferroni threshold over 431
windows → the separate 4–19 per cent Wilson bracket on P(F≥3). Table 12
rows now duplicated by the box were removed.

**R2-10 (second-author affiliation).** Author input: a TODO comment
marks where the institutional-context sentence is to be added (VBRL
Holdings Inc. description, capacity of the work); not resolved by us.

**R2-11 (duty-cycle conflation).** Done: Table 2 formalises the two
symbols — f_dwell (intra-track occupancy of one continuous observation)
and p_epoch (probability of activity at a years-separated epoch) — and
the bare phrase "duty cycle" no longer appears unqualified anywhere in
text or figures; Figure 11 was regenerated with p_epoch in the legend,
the product-likelihood formula ∏(1 − f p_epoch C_i) = 0.05, and the
footer, which additionally distinguishes p_epoch from the intra-track
dwell fraction in words.

**R2-12 (prose style).** A further editorial pass was made over the
abstract and §4–§6 in this round (on top of the previous round's
abstract halving): long compound sentences split, parenthetical caveats
promoted to sentences, terms tied to their Table 2 definitions at first
use per section.

**R2-13 (appendix roadmap).** Done: the scope table (analyses ×
validation status × role in headline limits) is referenced in §1 and
again at the head of §4, naming which appendices carry load-bearing
claims.

**R2-14 (self-citation).** Author input: TODO comment; the White 2026
citation stays marked provisional until the companion is published or
posted with a fixed identifier.

**R2-15 (Fig 1 / Fig 5 legibility).** Figure 1 was regenerated with a
re-laid-out constrained-layout geometry (wider left margin, larger
annotation and footer text at reflowed line lengths); the in-panel
legend now separates the two classes. **Decision:** the two-panel split
was not taken (see R1-15). Figure 5 (noise-quality control) was not
regenerated: its inset annotation keeps its size, and its load-bearing
caveat is carried by the axis label and caption; resizing the figure
could not be accommodated at fixed page count.

**R2 minors.** (1) "demo." spelled out in the abstract. (2) §1's
infinitesimal-fraction claim now carries the concrete number
(6e-18 of the Wright et al. 2018 haystack). (3) "bycatch" is defined at
first use in the abstract. (4) The Table-5-style scope summary is
referenced from §1. (5) §4.4's plain sentence added ("persistent,
near-static carriers are recovered, not suppressed, at the rates the
dwell experiment measures"). (6) §5.3 states the recurrence question
explicitly (see R1-8). (7) HD 48370: the caption and text state the
Cataldi et al. (2023) coincidence is with their quoted barycentric
velocity after our own frame-chain correction, and the near-tie of rank
(27.10 vs 26.83) is foregrounded in the caption as the limiting case.
(8) §6.1's three transmitter classes now carry detection denominators
(of the 88 stars: 1, 2, 8 and 24 would host a detectable transmitter of
the four benchmark classes). (9) Eq. 3–4: the independence assumption
among F_i, R_i, D_i, C_morph is now stated explicitly, with a sentence
on the bias direction if frequency occupancy and epoch activity are
correlated (a continuous narrowband broadcaster violates independence
toward over-optimistic limits). (10) §4.1 forward-references the
App C worked example. (11) Discussion/Conclusions state the ±50 km/s
mask is a post-hoc adjustment (with R1-5). (12) References: in-press
entries updated where final forms exist; White 2026 remains provisional
(author TODO). (13) GitHub + Zenodo DOI consistency stated in Data
Availability. (14) The Margot et al. (2023) methodology comparison is
handled in prose in §6.2 (shared: product-likelihood form over
transmitter fraction; different: uniform per-target frequency coverage
vs conditioning on each target's own archival frequency support and the
transferred single-configuration recovery) — **Decision:** prose rather
than a table, at fixed page count.

---

## Length discipline (page count unchanged at 38)

Additions this round (boxed split statement, trials box, pseudo-target
Monte Carlo paragraph, CP−72 properties table, defect-forensics appendix
and table, exposure table, crosswalk row, expected-maximum distribution,
Class A/B machinery, figure regenerations) were offset by:

1. **Retired redundant floats** — four tables that restated
   machine-readable or figure-carried content: the prior-surveys table
   (17 rows; §2 prose + Fig 1 carry its function, and it was referenced
   nowhere), the full 20-row crossing funnel (the four flagged windows
   are in Table 5, the statistic revision audit in Table 7, and every
   crossing is in the released per-target file), the one-line-per-star
   summary table (88 rows; superseded by the released
   per_target_results CSV, named in §5.1, with Fig 9 and the per-band
   table carrying the paper-level view), and the cumulative N(<d) sample
   figure (one sentence of message; Table 17 carries the selection
   function quantitatively).
2. **Table-row deduplication** where this round's new tables subsumed
   old rows (search-space vs exposure table; trials table vs the
   trials box).
3. **Prose trims** of narrative recitals that restated tables or
   appendices (§2, §3, §4.1–§4.4, §5.1–§5.7, §7, App C/H), and caption
   tightening.

Two of the retired tables were already unreferenced in v3.35 (MNRAS
requires every float referenced); the remaining floats were audited and
all are now referenced exactly once or more. Appendix lettering closes
at Q.

## Build gates

pdflatex ×2: 0 errors, 0 undefined references/citations, 38 pages,
0 overfull boxes; fonts Type 1/Type 0 only; no drawing extends past the
text block beyond the pre-existing v3.35 top-float geometry; every
figure regenerated this round (1, 9, 11) passes the word-clipping scan
(0 clipped words), and the regeneration repaired pre-existing edge
clipping in the shipped Figure 11 footer.
