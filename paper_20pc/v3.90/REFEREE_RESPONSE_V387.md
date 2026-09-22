# Response to the two referee reports — v3.90

Both reports were worked recommendation by recommendation, each finished
before the next was started, as instructed. All 26 recommendations are
implemented. Nothing was declined.

Every number quoted below is read back from the built PDF or printed by the
generator named, not from a draft.

---

## Referee 1 — major

### R1-1 One compact table of every false-alarm expectation, and one primary expectation

Done, and it turned out to be the most consequential item in either report.

New `falsealarm_v390.py` builds `tab_falsealarm_v390.tex`
(Table~\ref{tab:falsealarm}, §5.3) with all seven expectations in one
place and a new **`predicts`** column. Writing that column exposed the
real problem: **six of the seven expectations predict the number of
windows in which a no-signal position would rank first, which is not the
observed quantity.** A stage-1 event requires two conditions — rank-first
*and* the trigger — and every figure the paper had quoted imposed only the
first. Comparing 4 observed events against 3.2–4.7 "expected" was a
category error in our favour and against us by turns, and it is what
generated the "modest excess" language the referee objects to in R1-4.

### R1-4 Empirical P(≥4) under the calibrated null, with clustering

Done, and it resolves the tension.

New `stageonenull_v390.py` computes the correctly-conditioned null: for
each window, the probability that a no-signal position both ranks first
and reaches the trigger, which is `1/(N_ctrl+1)` **if that window's
control maximum reaches the trigger and zero otherwise**, block-resampled
over 20,000 draws with the measured ×1.4 tail factor.

    stage-1 null over 1614 windows (394 Class A), trigger 5
      windows where a no-signal position can reach the trigger: 460 (29 per cent), 391 Class A
      observed unattributed stage-1 events: 4
      Class A, exchangeable   mean 0.75  95% 0-3  P(>=4) = 0.0066
      Class A, x1.4 tail      mean 1.07  95% 0-4  P(>=4) = 0.0251

So the honest statement is **4 observed against 1.07 expected,
P(≥4) = 0.025**, and the abstract, §5.3 and the conclusions now say
exactly that in place of "a modest population excess".

**A second result falls out of the same calculation, and it dissolves the
reference-class argument the paper had been having with itself.** Only 460
of 1614 windows can reach the trigger from noise at all, and **391 of
those 460 are Class A**. That is why every stage-1 event in the survey is
Class A, and it means the choice between the all-window and the Class A
denominator — which the manuscript had treated as an open interpretive
question — is largely forced by the data. §5.3 says so.

### R1-2 Visibility localisation into the formal candidate definition

Done, in the referee's order. §4.2's definition is now:

1. threshold crossing,
2. spatial-control prioritisation,
3. **visibility-domain localisation**,
4. astrophysical-line identification,
5. independent recurrence,

with the first two labelled explicitly as *computational candidate
generation* and (iii) as *the first physical test of association with the
star*. The spatial statistic is described that way consistently. The
funnel figure (`make_fig_funnel.py`) and `stagetable_v386.py` were checked
against the new order and already agreed; the §4.6 summary was updated.

### R1-3 P90_sel as the single headline sensitivity

Done. Table 1's power block is now an ordered hierarchy —
P_trig → C_resp, C_smear → P_eff → P_50, P_90 → **P_90^sel** — with the
last flagged as the headline and the first four as intermediates. The
"how to read every limit" paragraph was rewritten to match, and the boxed
rule in §5.5 now says four quantities, not three.

Three defects were found doing it:

* The glossary carried **duplicate definitions** of P_trig, P_eff and
  P_90, and two of "stage-1", with the P_eff row still saying "Quote this
  one" while the caption said P_90^sel. Deleted.
* The Mason et al. (2024) comparison was quoted on P_90. Recomputed on
  P_90^sel in `v381_calc.py`: **×459** (median per-system
  P_90^sel = 1.5×10¹⁵ W) rather than ×595, with the weaker
  number given beside it because Mason's published figure is a threshold,
  so the P_90^sel ratio is the conservative comparison.
* Figure 1 plots the trigger-level P_90, not P_90^sel. Rather than change
  the figure we **named the quantity on the axis** and added to the caption
  that P_90^sel is ×1.16 higher, "so the panel as drawn flatters this
  survey".

### R1-5 Table for the four unattributed events

Done. `tab_unattributed_v383.tex` gains five columns — epoch (UT),
N_rep, Δt range, the depth of the deepest repeat **with its shortfall
against the event**, and the recurrence verdict — replacing the single
crammed cell.

Building it found that **the deepest repeat anywhere in the set reaches
T★ = 5.42, which crosses the trigger.** It does not outrank its own
controls and so does not reproduce a stage-1 event, which is what "none
recurs" means in this paper, but the bare claim was closer to the line
than the manuscript admitted. The cell now reads `no` with a footnote
stating the crossing, and the caption states it too.

### R1-6 One completeness formulation

Done. "Work-list complete but epoch-incomplete" is now the paper's only
formulation for the sample, stated as a paired phrase in the Introduction,
in §3 and in the glossary. The Introduction's "a sample complete with
respect to the public archive" — the exact reading the referee warns
against — is gone.

### R1-7 Class A and Class B as two experiments in the conclusions

Done. Conclusion 3 is split into *Class A, the primary experiment*,
*Class B, the secondary experiment* and *Common to both*, with no combined
sensitivity or completeness figure. Class B's limits are given
(3.7×10¹³–6.4×10¹⁷ W, median 1.4×10¹⁵ W) with the statement that they hold
for any dwell fraction and discriminate no drift, so they are not
comparable window for window with Class A. Conclusion 1 now says the
47.7 + 70.4 GHz union is "a coverage total and not a sensitivity".

### R1-8 Move the methodological defence out of the Introduction

Done. The two-disclosure paragraph (pre-registration detail, repository
timestamps, the 135-position region-max experiment) is replaced by two
sentences of forward pointers to §4.2, §5.3.2 and Appendix G.4, where all
of it already existed in full. Net −643 characters from the Introduction.

## Referee 1 — secondary

* **R1-s1** §6 opens with a new paragraph putting the disc selection
  (90 per cent) and the M-dwarf deficit (21 of 5,908 catalogued
  M dwarfs within 40 pc) before any inference,
  and saying the section's quantities describe these stars and not the
  40 pc population.
* **R1-s2** Figure 1's panels now carry their own titles:
  "(a) parameter-space location; vertical sensitivities not directly
  comparable" and "(b) native spectral resolution, directly comparable".
  Verified by extracting the text back out of `eirp_context.pdf` rather
  than by eye.
* **R1-s3** Every aggregate frequency-union statement now points at
  Fig. 4 — the search-space table and its caption, the mask paragraph,
  the exclusion box and the conclusions — with the warning that the union
  is not continuous coverage of its endpoints.
* **R1-s4** Masked frequency space is "excluded from the experiment"
  throughout; "vetoed" now appears only in the two places that explicitly
  contrast the two, and the candidate stages are called stages.
* **R1-s5** The one-sided atmospheric-decorrelation bias (+5 to +20 per
  cent) now travels with the headline number in the §5.5 boxed rule, in the
  §5.5 statement of the sensitivity, and in the conclusions, each time with
  "read as an upper bound on reach, not a central estimate".

---

## Referee 2 — major

### R2-1 Radius-correction promoted to the headline

Done. The abstract gives both counts side by side with their chance
expectations, and states at first mention why the uncorrected count is
primary (the correction postdates the candidate list). §5.3 and the
conclusions do the same.

### R2-2 A standard occurrence-rate metric

Done, computed, not asserted. New `occurrence_v390.py` implements the
Enriquez et al. (2017) definitions exactly, with ζ_AO = 5.0×10⁻¹¹ from
their normalisation:

    Class A: 60 systems, union 47.7 GHz about nu_mid 494 GHz, nu_rel 0.097
    Transmitter Rate 0.17
    CWTFM 1.3e4 at the median per-system P_90^sel (3.8e5 worst case)
    literature: Enriquez+17 0.85, Price+20 GBT 0.11, Parkes 8.2, Phoenix 49
    transmitter-hosting fraction, 0 of 60, 95% Poisson: f < 5.0%

The paper now states plainly that **this survey is some four orders of
magnitude worse than cm-wave SETI on the standard continuous-carrier
metric**, and why that is the correct conclusion. Two caveats are given
with it: the transmitter-hosting bound uses the 95 per cent Poisson limit
(5.0 per cent) rather than the 1/N convention (1.7 per cent, optimistic);
and ν_rel is a survey-level quantity, so recomputing on the median
system's own 1.84 GHz of coverage gives ν_rel = 0.0037 and CWTFM = 3.3×10⁵.
Both are quoted. The generator cross-asserts its inputs against
`NSysClassA`, `UnionClassA` and `SysUnionAMed` as other generators publish
them.

### R2-3 RFI vetting statement

Done, as a new §5.3.1 with three measurements, not an assertion. New
`rfi_v390.py`:

* **Sky-frequency recurrence across unrelated targets.** 86 windows toward
  6–39 other stars in 276 other blocks cover the four events' frequencies;
  **0** carry a crossing in the same channel. Only 1 of the 4 events has a
  released crossing frequency, so the test runs on one and the paper says
  so rather than implying four.
* **Clustering in sky frequency.** Over all 451 released crossing
  frequencies, binned at 1 MHz, the largest multiplicity is **2** against
  1.9 for a null that randomises each crossing within its own window,
  p = 0.90. No interference line.
* **Fixed intermediate frequency.** Crossings' fractional positions within
  their windows have median 0.50 and are uniform to D = 0.023, p = 0.97
  over 451 crossings, so no signal-chain artefact at fixed IF.

The physical argument is stated beside them (89–873 GHz is above every
allocated terrestrial service; 5000 m site; a near-field source does not
fringe-track), and the section ends by saying this is not a substitute for
an ON/OFF cadence.

### R2-4 Drop σ notation for the trigger

Done. T★ and T_trig = 5 are defined in the glossary, with the statement
that σ is reserved for genuine noise scales. 45 of the 46 occurrences of
"5σ" were converted: `EIRP_5σ` → `EIRP_trig` (7), threshold statements →
`T_trig`, and quoted statistic values → `T★ = x`. The one remaining is
"each programme's own 5σ threshold" in the Figure 1 caption, which is the
literature's notation and correctly theirs.

## Referee 2 — minor and technical

* **R2-m1** The conclusions now separate the **±8 per cent calibration budget**
  (flux scale of one window) from the **×0.48–1.35 transfer bracket** (window-to-window spread of the injection-measured
  completeness), name the second as dominant, and no longer state the
  bracket twice.
* **R2-m2 / R2-t1** No placeholder identifier anywhere. The White (2026)
  sentence is rewritten to be self-contained — "submitted, and not yet
  available to the reader… Nothing in the present paper rests on it" — and
  the bibliography entry drops "(identifier to be supplied)".
* **R2-m3** Each worked example closes with a boxed one-line verdict
  giving statistic, ring maximum, line offset, visibility result and
  disposition. Writing CP−72's found that its `|Re/σ|` was printed as a
  negative absolute value; and HD 48370's found that **the printed margin
  did not equal the difference of the printed values** (27.10 − 26.83 =
  0.27, printed 0.28, because the margin was computed unrounded). The
  generator now computes it from the rounded values so the arithmetic on
  the page closes.
* **R2-m4** The six follow-ups in §6.4 are explicitly ranked (1)–(6) with
  a stated criterion and a bracketed statement of what each buys. This
  fixed a self-contradiction: the visibility recommendation said "it is
  the first change we would make" while appearing second.
* **R2-m5** A compact ordered step list is given where Fig. 3 is
  introduced in §3, with every surviving count, so the reader meets the
  pipeline before the results. The step count is now read from the
  figure's own list (`funnel_steps.tex`): **the caption said "ten steps"
  while the figure drew eleven and §4.6 said eleven.**
* **R2-t2** A dedicated cross-reference pass, now a gate
  (`xrefcheck.py`). It found and we fixed: `sec:vistest` **anchored on a
  table**, not a section, because its label sat after a float — it printed
  the right number by luck and hyperlinked to the wrong place; `app:table`
  the same; `sec:benchmarks` sharing an anchor with `sec:frames`, so a
  reader sent to §4.3 for the Arecibo benchmark arrived at the velocity
  frames. It also found `tab:chance`, an **unreferenced table that is a
  strict subset of the new R1-1 table**, which is deleted.
* **R2-t3** All 26 glossary rows now carry the section or appendix where
  the term is defined or first used. Previously 8 did.
* **R2-t4** One appendix heading style: the three starred subsubsections
  in G.10 are numbered and labelled, two run-in headings are broken, and
  G.10 is retitled. It had been called "Validation material moved from the
  main text", which is wrong — it is the detail layer for §5.3.2, §5.3.3
  and §5.3.5, it carries 104 generated macros that appear nowhere else,
  and **it was never referenced**, so no reader could find it. Each of the
  three main-text summaries now points at its own appendix subsection.
* **R2-t5** Figure 1's caption bolds exactly one sentence, the warning
  about panel (a); the lead-in is now emphasised instead.

---

## Two process defects found this cycle, both now gated

**1. A silent round-file overwrite.** `occurrence_v390.py`, added for
R2-2, wrote `survey_numbers_round47.tex` — which `stageonenull_v390.py`
already owns. The build reported 0 errors and 0 undefined control
sequences, because the destroyed macros were still in the `.aux` from the
previous run. Nothing in `gate.sh` could see it. New `roundcollide.py`
(now in `gate.sh`) asserts that no two generators write the same round
file, that every round file the manuscript inputs has exactly one writer,
and that none is orphaned. It knows about `frozen_macros/` for the rounds
whose generators are retired.

**2. `retire_macros.py` did not know that generators read macros.**
Three v3.90 generators look their inputs up by name in the round files.
Retirement commented out 13 of them as "unreferenced", and **four rows of
the new false-alarm table silently became `--`**. Caught by re-running the
generator after retirement, not by any gate. `retire_macros.py` now scans
the `.py` files for `V('Name')`-style readers and protects what it finds:
16 macros this round.

Both are the same failure as v3.61's stale literal and v3.62's
frozen-input arithmetic: a value that one stage produces and another
consumes, with nothing asserting the link. The assertions are the defence.

---

## Release state

    pages 45 (main 27.6 / back 0.8 / appendices 16.3 / bib 0.3)
    errors 0 | undefined refs/cites 0 | multiply defined 0
    overfull 0 | Type 3 fonts 0 | underfull 32 (the narrow measure)
    abstract 1917 rendered characters of arXiv's 1920 (headroom 3)
    macros 1107 defined, 0 unused (16 read by generators, protected)
    clean regeneration 88/88 byte-identical, including 14/14 figures
    arXiv set 86 items, built clean from an empty directory
    roundcollide 45/45, 0 problems | xrefcheck 0 misplaced labels
    em-dashes 67 (v3.86: 66) | antithesis 184 (v3.86: 175)

## Still open for the authors

Unchanged from v3.86 and listed verbatim in `AUTHOR_ACTIONS.md`: the
Zenodo DOI, the submission git tag, the White (2026) identifier if it
becomes available, the ALMA project codes, the funding statement, and the
VBRL affiliation with its competing-interest wording.
