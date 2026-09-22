# Response to the third-round referee reports

Manuscript: *An ALMA Archival Search for Narrowband Technosignatures toward Stars
within 40 pc* (retitled; previously *A Search for Time-Variable and Frequency-Drifting
Narrowband Technosignatures toward ALMA-Observed Stars within 40 pc of the Sun:
Survey Design and First Results*)
White & Dey — revision v3.33

Both reports recommended major revision. We have acted on every item, declining two
suggestions with reasons (Referee 2's B4 split, and Referee 2 A1's specific replacement
title, where we adopted a third title that we argue is the accurate one). The revised
manuscript compiles at **38 pages, the same count as the previous version**: the roughly
two pages of new material this revision required (two figures, the completeness matrix,
the validation-changes table, the transmitter-model subsection, the quantitative
multi-release guard, expanded glossary and comparison columns) are offset by removing
three tables to the machine-readable release with their content folded into prose,
replacing a page break with a rule, and a full pass of compression described at the end
of this letter.

---

# Referee 1 — point by point

## The four conditions set for acceptance

| # | Condition | Status |
|---|---|---|
| 1 | Single definitive algorithm description; every copy identical | Done — Table 1 is now a 12-step data path "so the statistic can be reimplemented without the appendices"; §4.1 and the appendices carry the same operator. The temporal-median description is gone from all seven sites that carried it. |
| 2 | Resolve the coarse-channel completeness contradiction; regenerate affected tables/figures/abstract | Done — new completeness matrix (the referee's requested table, in the exact class × morphology form); the contradiction's root cause (the drift-matching clause of the frozen recovery criterion) is stated once, in the validation-changes table. |
| 3 | Symmetric statistic demonstrably applied to all 431 windows | Done — the SP statistic is operative over all 431 windows; a compact audit (the crossing funnel, one row per window with a ≥5σ crossing, plus the glossary row) makes the count auditable; the "designated replacement" sentence that implied otherwise is deleted. |
| 4 | Strengthen or demote the 6.2% occurrence limit | Done — demoted (the referee's Option B). It is now labelled an illustrative conditional constraint at every appearance, including the abstract; the direct observational result (zero candidates across 431 windows, EIRP thresholds 1.6×10¹³–2.8×10¹⁷ W) is the headline. |

## 1. Mutually incompatible descriptions of the signal-processing operation

The referee is right that this was the most serious defect, and the diagnosis is the one
we arrived at on reconstructing the pipeline from the frozen source: **the baseline step
is a per-integration running median along the frequency axis; there is no temporal median
at any stage.** The revised text states this once, definitively, and every other
description was regenerated from it:

* Table 1 (the algorithm table) now lists, in order: calibrated measurement set →
  proper-motion-propagated position → spectral extraction at native channelisation →
  *per-integration baseline removal: running median along frequency* → stack along each
  trial linear drift rate → robust per-position noise scale σ (MAD) → T(x) from Eq. 1 →
  repeat at 512 control positions → threshold T★ ≥ 5 (a hit) → rank test → molecular-line
  mask → vetting. This answers the referee's pseudocode request step by step, including
  the exact combination (inverse-variance-weighted sum over integrations) and the exact
  noise scale (σ = 1.4826 × MAD over the window).
* §4.1 now opens the statistic definition with the same operator in prose, with the
  explicit aside "there is no temporal median at any stage".
* The appendix withdrawal paragraph explains *why* the earlier claim arose (the frozen
  campaign's recovery criterion conflated drift attribution with detection) without
  narrating the drafting history (see Referee 2 B1).
* The statement that the operator "by construction cannot remove a feature confined to
  one or two channels" now sits next to the definition, so the transfer-function
  consequence the referee was concerned about is visible immediately.
* The operator is applied **before** de-drifting (per-integration, Table 1 steps 4→5),
  stated by the table's ordering and confirmed in prose.

On the kernel width: the operator's axis, scope and position in the data path are now
fully specified, and the numeric width is a fixed constant of the frozen pipeline,
retrievable by any reader from the tagged source release. We have not printed the numeric
value in this revision — we did not have access to the frozen pipeline host while
revising and preferred pointing to the code over risking a mis-transcribed constant —
and we accept the referee's implicit point: the number belongs in the text, and we will
insert it at proof stage, verified against the tagged source.

## 2. Coarse-channel completeness simultaneously measured and unmeasured

The referee's two-questions diagnosis is exactly right, and we have adopted it verbatim.
The new table (which replaces the earlier contradictory framing) is the referee's
suggested matrix in its exact form — window class (fine/coarse) × morphology
(stationary/drifting/intermittent), with separate columns for **detection completeness
measured?** and **drift recovery measured?**, and the applicable window counts (118/313).
What it records:

* **Coarse windows: amplitude/detection measured, drift not discriminable.** The dwell
  campaign recovers 83–100% of injected carriers across dwell fractions 1.0→0.1, and an
  end-to-end injection through the released pipeline returns T★ = 20.5, 65.3, 217.7 at
  1, 3 and 10× the per-integration noise — amplitude sensitivity is real and measured.
  Every in-grid drift is sub-channel over a coarse track, so the recovered drift is
  arbitrary and no drift-rate claim is made for the coarse majority. The paper now says
  precisely this, in the referee's own terms ("amplitude sensitivity to unresolved
  carriers, but no drift discrimination").
* **Fine windows: drifting class measured** (17/42/58/75/83% at 4/5/6/8/10σ),
  **stationary through-pipeline recovery unmeasured** — the one unmeasured cell, marked
  as such in the matrix and owned in the text (the 1200-trial campaign failed static
  carriers under a criterion that mixes amplitude and drift matching; no end-to-end
  zero-drift injection has been run on a fine window).
* The earlier "0/500 static carriers suppressed" statement is corrected everywhere it
  appeared: the zero was an artefact of the criterion's drift clause on degenerate
  coarse grids, not of the pipeline, and the end-to-end check demonstrates the pipeline
  does not suppress persistent carriers.

## 3. The 6.2% occurrence limit presented too prominently

We chose **Option B**, and went slightly further than the referee asked: the population
calculation is now introduced as *"an illustrative conditional occurrence limit under the
measured fine-window recovery model"* — the referee's own suggested label — at every
appearance, including the abstract and conclusions. "This paper's result" phrasing is
removed from the occurrence table and its figure. The primary result restated in the
abstract and conclusions is the direct one the referee recommended: no credible
technosignature in 431 searched windows; nominal EIRP thresholds spanning
1.6×10¹³–2.8×10¹⁷ W. We also replaced the abstract's naive duty-cycle numbers with the
duty-aware values that the duty table actually supports (see the numerical corrections
below), so the abstract's quantitative claims are all direct-measurement claims.

We did not attempt Option A (an enlarged multi-configuration injection campaign): it is
the right next-release item, but running it properly means new cluster processing across
bands, durations and primary-beam offsets, which we could not execute within this
revision. The completeness matrix marks every transfer-based cell as such, so the
calibration basis is visible rather than implied.

## 4. Two statistical pipelines / were all 431 windows reprocessed?

Stated unequivocally, and the inconsistent sentences are gone:

* The **single-position (SP) statistic is the operative criterion over all 431 windows**:
  the frozen products carry T★ and all 512 control statistics per window, and the
  published star-exceeds-ring rate (5/431 = 1.2%) is computed from them.
* The **region-max variant (SR)** survives only as a validation check on the seven
  windows locally reprocessed from raw data, and the text now says so in one sentence,
  with a glossary row defining both terms.
* The Appendix sentence describing the symmetric statistic as "the designated replacement
  … as the remaining sets are re-run" — the sentence that contradicted the conclusion —
  is **deleted**.
* The referee's audit request is met by the crossing funnel table (one row per window
  with a ≥5σ crossing: T★, ring max, exceedance flag) plus the trials table; the
  figure the referee flagged now has its caption and content consistent.

## 5. "5σ" terminology

Adopted. The trigger is now introduced as a nominal local amplitude trigger with an
explicit symbol (T_trig = 5), "hit" is reserved for a channel crossing that trigger, and
"candidate"/"significant" appear only at the control-calibrated stage. The nomenclature
table defines both senses explicitly.

## 6. Rank resolution of 512 controls

We agree, and we did what is possible without new cluster processing:

* The rank floor (1/513) and the expected 0.84 top-ranked windows per survey are stated
  at first introduction of the rate, so no per-window claim is over-read.
* For **CP−72 2713 specifically — the referee's named case (T★ = 5.81 vs ring max
  5.68) — we added the requested figure**: the complete empirical control distribution
  (512 controls) with the star statistic marked inside it, so the margin is seen rather
  than asserted. This is more informative than the two numbers alone, as the referee
  said.
* We did **not** enlarge the control ring to 10⁴–10⁵ positions in this revision: that
  requires re-extracting control spectra from the frozen per-window products on the
  processing cluster, which we could not run here. The paper states this as the standing
  recommendation for any window that would change a disposition, and the CP−72
  promote/retire criteria (Referee 2 C6) now bound what such a computation would have to
  show.

## 7. Molecular-line masking as excluded space

Done as requested. At the mask's first introduction the text now states that the mask is
an astrophysical-confusion veto that **removes those channels from the technosignature
search volume** — excluded space, not nondetections — with the "water hole" point made in
one sentence (a transmitter has no reason to avoid, and might deliberately choose,
conspicuous transition frequencies). Both bandwidths are reported: 93.1 GHz gross
searched, ≈87 GHz effective technosignature search bandwidth, with the latter the default
in the searched-parameter-space discussion.

## 8. What "narrowband" means at 15.625 MHz channels

Adopted verbatim: "unresolved narrowband carriers at the native ALMA channel resolution"
is now the standing phrase, including in the abstract; the velocity-width arithmetic
(≈20 km s⁻¹ per coarse channel at 230 GHz) appears where the distinction is introduced,
and the retitle (Referee 2 A1) carries the plainer claim. Figure 1's seven-order-of-
magnitude channel-width comparison remains central and its caption now describes only the
retained panel.

## 9. Stokes I and polarisation geometry

Softened, per the referee's safer alternative. The construction is now stated (Stokes I
formed from the two parallel-hand cross-correlations), and the claim reads that the
limits are Stokes-I limits and **no polarisation-discrimination search was performed**,
with one sentence noting that a fully polarised carrier is still detected in the
parallel hands but that polarisation-independent sensitivity claims would need all four
Stokes parameters. The stronger "independent of polarisation geometry" sentence is gone.

## 10. "No astrophysical selection of its own"

Replaced everywhere with the referee's precise form: *no technosignature-driven or
astrophysical target selection was imposed after conditioning on public ALMA coverage.*
The distance and spectral-type biases of the archive-conditioned sample (F/G
overrepresented, M dwarfs underrepresented) are stated at the sample's introduction, not
only in the discussion.

## 11. Development history out of the narrative

Done, in the referee's suggested form: a single table ("Validation changes made before
the frozen analysis": original issue → effect → correction → final data affected) now
carries every correction story exactly once — the W Hz⁻¹ withdrawal, the source-region
statistic, the temporal-median claim, the coarse-window injection failure, the
duplicated-row defects, the provisional/final product distinction. The main text
describes only the final methodology; the withdrawn-claim narration that was distributed
across the abstract, §4.4/4.5 and the Figure 1 caption is excised (this is the same
operation Referee 2 requested as B1, and it is done once for both).

## 12. Three products, three tiers

Adopted. The Results section and the scope table now structure everything into the three
tiers — primary search / conditional population constraint / exploratory ancillary — with
the validation status and "in headline limits?" columns making the separation auditable.
The ancillary screens are introduced as tier-3 with one-line main-text pointers.

## 13. Continuum analysis moved to an appendix

Done: the continuum anomaly screen now lives almost entirely in the online appendix,
with a single main-text paragraph stating what it is and that its one outlier is
astrophysically dispositioned and affects no headline limit.

## 14. "What transmitter would this survey detect?"

Added as a subsection with exactly the referee's three cases — a continuously emitting
monochromatic beacon, a drifting carrier from an orbiting transmitter, and an
intermittent carrier at 10% duty cycle — each traced through a representative coarse and
fine observation with the measured recovery numbers, so the completeness matrix can be
read as physics rather than bookkeeping.

## 15. Two-dimensional sensitivity representation

Added: a new figure of frequency versus nominal EIRP threshold for all 431 windows, with
channel class encoded (fine as open circles, coarse as grey points), the Arecibo-like
planetary-radar line for scale, and band boundaries marked. The caption states the
drift-discrimination asymmetry between the classes, so the figure carries the search's
actual shape rather than a single collapsed threshold.

## 16. Cosmic Haystack kept qualitative

Agreed and unchanged in kind: the axis-by-axis comparison stands, no marginal fractions
are multiplied, and one sentence records that a joint sensitivity volume is the only
defensible way to quote a haystack fraction — which this release does not attempt.

## The numerical/textual inconsistencies

* **Duty-cycle limits (12.3%/62% vs 10.8%/48%).** The naive and duty-aware numbers were
  indeed mixed. All four sites (abstract, conclusions, duty discussion, table) now carry
  the duty-aware values — 10.8% at D = 0.5 and 48% at D = 0.1 — via generated macros, so
  the abstract cannot disagree with the table again.
* **Coarse completeness measured/unmeasured.** Resolved by the completeness matrix (item 2).
* **Static-carrier recovery.** Resolved (item 2): the 0/500 was a criterion artefact;
  measured dwell recovery and the end-to-end result are the operative statements.
* **Median operation.** Resolved (item 1).
* **Symmetric reprocessing.** Resolved (item 4).

## Minor and editorial comments

* The defensive/audit-trail phrases the referee quoted are removed or neutralised; the
  two boxed callouts are retained as deliberate devices (see Referee 2 B3).
* "Census" now reads "ALMA-coverage census" wherever a casual reader could mistake the
  168 stars for a volume-complete stellar census (glossary included).
* Star / target / catalogue entry / system as statistical units is defined at first use
  in §2 and in the glossary, with the 88 → 82 reduction stated there, not only later.
* "Processed nearest-first" is reworded to say the processing order used distance as the
  ordering variable while EIRP sensitivity also depends on channel width and rms —
  "approximately in anticipated sensitivity order".
* Spectrum/dynamic-spectrum panels for the exceedance windows and CO-velocity overlays
  for β Pic and HD 48370: we could not generate these in this revision — they require
  re-extraction from retained per-integration spectra on the processing cluster. The
  funnel table, the new CP−72 control-distribution figure and the local noise-scale
  measurements (ratios 0.97/1.29/0.93/1.02 for the four exceedances) carry the
  equivalent information in tabular form; the panels remain the right addition when the
  cluster products are next refreshed.
* The permanent-DOI point is met by the existing commitment: the Zenodo deposit is
  minted at acceptance, and the Data Availability statement names the tagged,
  frozen snapshot as the identifier of record.

## The suggested restructuring

The revised paper follows the referee's skeleton in substance — one definitive methods
section; validation (controls + injection/recovery) as its own section; results ordered
by tier; the population constraint explicitly secondary; continuum, closure phase, chirp,
line catalogue, audit and forensics in appendices. We did not renumber the sections into
the referee's exact 1–8 form, but a reader following that outline will find each item in
one place and in that order.

---

# Referee 2 — point by point

## A1. Title oversells the validated product — retitled

Agreed, and retitle chosen. The new title is:

> **An ALMA Archival Search for Narrowband Technosignatures toward Stars within 40 pc**

We did not adopt the referee's example ("…Search for *Drifting* Narrowband
Technosignatures…") because it would undersell what is measured: amplitude sensitivity
to unresolved carriers is measured on **both** channel classes (dwell recovery 83–100%
on coarse windows, end-to-end T★ = 20.5–217.7), and the search stacks over drift trials
on all 431 windows. "Narrowband" with the "at native ALMA channel resolution" qualifier
(Referee 1 item 8) claims exactly what is validated — an unresolved-carrier amplitude
search — without claiming the time-variable morphology recovery that is not measured.
The abstract's first caveat sentence states the drift-discrimination asymmetry directly
(A2). The previous title's twin claims ("time-variable and frequency-drifting") are
gone.

## A2. Coarse-channel drift non-discrimination prominent

Done: the abstract carries the caveat in its own sentence ("on the coarse-channel
majority … any in-grid drift is sub-channel over a track, so the search recovers the
carrier's amplitude but carries no information on its drift rate"), and the introduction
now has the sentence for readers from single-dish SETI: at channel widths far below any
Doppler-drift concern, drift discrimination is free; at ALMA's native mm-wave
channelisation it is not, and that asymmetry defines what this survey can and cannot say
about the coarse majority.

## A3. The 42% transfer error unquantified — carried beside the number

Done: every quotation of the 42(+16/−14)% recovery figure — abstract, completeness
matrix, occurrence discussion — now carries in the same sentence (or table cell) that the
curve is measured on one fine-channel configuration, transferred to all 118 fine
windows, and that the transfer error is **not contained in the quoted binomial
interval**. Broadening the campaign across bands/durations/beam offsets is named as the
first next-release item, not folded into a caveat dump.

## A4. Trial-level records not retained

This is the one item we could not execute: re-running the campaign with trial-level
logging requires the processing cluster, which was not available during this revision.
What we did instead, honestly: the paper states plainly that trial-level records were
not retained and that the released campaign is therefore not independently re-analysable
at the trial level; the completeness matrix marks every transfer-based cell; and the
next-release queue names trial-level logging as its first change. We accept the referee's
standard and do not claim the current numbers meet it — the matrix and the abstract say
what the numbers are and are not.

## A5. Occurrence conditioning next to the number

Done: wherever f₉₅ appears as a result — abstract, table, conclusions — the conditioning
is in the same sentence: continuous emission (D = 1), the measured fine-window recovery
model transferred from one configuration, and the frequencies this dataset happened to
observe. The "vanishes entirely under a broader frequency prior" statement is likewise
beside the number, not in a later section.

## A6. Quantitative multi-release false-discovery control

Done, provisionally as the referee allowed: the multi-release paragraph now commits to a
concrete rule — each release's unattributed flags reported against the **cumulative**
expected count (Poisson tail on the running total across the planned ~2000-window
series, whose null expectation ≈ 4 rank-first windows in total is computed in the text),
with series-level false-discovery control by Benjamini–Hochberg on per-window rank
probabilities, acknowledging the 1/513 rank floor limits its resolution. The rule is
labelled provisional and will be fixed with power simulations before the second release.

## A7. Closure phase contributes no discriminating power

Clarified everywhere the test is introduced: it is validated infrastructure with **no
discriminating power at this release's flux densities** (per-baseline S/N never exceeds
5.1), and no flagged-window disposition rests on it. The abstract-adjacent framing no
longer implies it contributed to the vetting.

## B1. Revision-history narration removed

Done in full: the abstract sentence ("Earlier versions of this paper asserted the
opposite… it is withdrawn") is deleted; §4.4/4.5 now state the corrected result on its
own merits; the Figure 1 caption describes only the retained panel; the statistic-history
material is consolidated into the validation-changes table (one row per issue, including
the star-beats-ring replacement). Two boxed callouts that the referee exempted ("How to
read every limit in this paper", "What this survey does not constrain") are retained.

## B2. Jargon

Reduced, and the glossary expanded: standard field vocabulary is used wherever it
suffices (hit, candidate, false-alarm probability, off-source reference positions);
"Schelling point" is gone; the coinages that survive (control ring, SP/SR statistic,
funnel) are defined at first use and in the glossary, which now also carries rows for
the SP/SR distinction, star-exceeds-ring, and QA2.

## B3. Prose style

Copy-edited toward conventional expository prose; the aphoristic register survives only
in the two boxed callouts the referee singled out as effective. The specific phrases
quoted ("That reading was wrong…", etc.) are reworded as plain statements of the
corrected result.

## B4. Split into results + methods papers — declined, with reasons

We considered this carefully and declined. The validation appendices are load-bearing
for exactly the claims both referees asked us to make auditable — the completeness
matrix, the false-alarm accounting, the trials table, the audit trail. Splitting them
into a companion paper would make the results paper's central statements (measured
completeness, empirical false-alarm rate) unevalatable without a second document under
separate review, and the cross-referencing burden would grow, not shrink. Instead we did
what Referee 1's items 12–13 suggest and the referee's own Table 16 comment points at:
a three-tier scope table that marks each analysis's validation status and whether it
enters headline limits, ancillary material relocated to appendices with one-paragraph
main-text pointers, and the revision-history consolidation of B1. If the editor prefers
a split we will of course comply, but we ask that the three-tier structure be considered
the alternative.

## B5. Why publish at 51% completion

Stated up front in the introduction: the release is a frozen partial survey — 107 of 208
planned star/band datasets — because a frozen pipeline with a fully documented selection
function and a reproducible null is the citable methodological unit; deferring to 100%
would leave the archive-growing selection function undefined at publication time. The
51% figure and the frozen-release philosophy now appear together in §1.

## C. Specific/minor comments

1. **EIRP defined at first abstract use; QA2 expanded** at its first §2 appearance
   ("the observatory pipeline's calibrated, quality-scored data products") and given a
   glossary row.
2. **Abstract revision sentence removed** (B1).
3. **Figure 1 caption** describes only the retained panel (B1).
4. **Notation fixed**: the inequality and significant-figure convention for the
   occurrence limit ("f < 6.2 per cent") is applied uniformly across text, table, boxed
   rule and abstract, all via generated macros.
5. **Table 15 EIRP column added**: Breakthrough Listen (deepest per-target EIRP
   2×10¹² W GBT, 9×10¹² W Parkes), Margot et al. (1.35×10¹³ W within 100 pc;
   5.08×10¹⁶ W within 6135 pc), alongside Enriquez et al. — the quantitative comparison
   is now in one place.
6. **CP−72 2713 promote/retire criteria stated next to the disposition**: promote only
   on recurrence at the same frequency in an independent epoch; retire on a clean second
   epoch or on identification with a catalogued or local astrophysical feature; absent
   either, the window stays in the look-elsewhere ledger of subsequent releases rather
   than silently re-entering the trials budget. This is now explicit, with the enlarged
   control-ring computation named as the discriminating measurement for any future
   marginal case.
7. **Competing interests** rewritten plainly: standard boilerplate plus one plain
   sentence on what the relevant affiliation actually is, replacing the elaborate
   negations.
8. **Spot-checks**: we are grateful for the independent verification of the UV Ceti
   worked example and the Poisson tail; every survey number in the manuscript is
   generated (no typed digits), which is the systematic guard against the silent
   transcription error the referee warns about, and the tables the referee names are
   regenerated from the same macro file.
9. **Zenodo DOI**: the statement is honest that minting occurs at acceptance; the
   GitHub tag named in Data Availability is the frozen snapshot of record in the
   meantime.
10. **mm/submm neglect paragraph added** to §1: receiver and back-end cost, the absence
    of commensal narrowband back-ends at ALMA (channelisation set by continuum and line
    science drivers), and the resulting mismatch between mm-wave observing as practised
    and narrow-carrier SETI as classically formulated — the paper's motivating gap, now
    stated as such.
11. **Promissory forward-references reduced**: the dozen-plus "will be committed /
    next release / completed survey" instances were each either deleted, converted to a
    present-tense statement of what the current products do contain, or concentrated in
    the single next-release subsection. The remaining ones are exactly those naming work
    that genuinely cannot be done on retained products (enlarged control ring,
    trial-level logging, per-crossing local scales), each with its reason stated.

---

# What we could not do in this revision, and where that is carried

For transparency to both referees, three requested computations require the processing
cluster that hosts the frozen pipeline and retained per-window products, and could not
be run during this revision. Each is carried honestly in the text rather than papered
over:

1. **Enlarged control rings (10⁴–10⁵ nulls) for CP−72 2713 and the other exceedance
   windows** (Referee 1 item 6). The paper now shows the complete 512-control empirical
   distribution for CP−72 2713 and states the promote/retire criteria; the enlarged-ring
   computation is named as the discriminating follow-up.
2. **Spectrum/dynamic-spectrum panels and CO-velocity overlays** (Referee 1 minors).
   Equivalent tabular information (funnel rows, local noise-scale ratios) is provided;
   the panels await the next cluster refresh of the retained per-integration spectra.
3. **Injection campaign re-run with trial-level logging** (Referee 2 A4) and the
   **fine-window zero-drift end-to-end test** (Referee 1 item 2's one unmeasured cell).
   Both are stated as exactly that — unmeasured — in the completeness matrix, the
   abstract and the next-release queue.

# Page budget (the 38-page constraint)

The previous version was 38 pages; so is this one. Additions this revision: the
completeness matrix, the validation-changes table, the CP−72 control-distribution
figure, the 2D sensitivity figure, the transmitter-model subsection, the quantitative
multi-release guard, the mm/submm-neglect paragraph, glossary rows, and the Table 15
EIRP column (≈2.2 pages). Offsets: the 57-row execution-block table, the 10-row
frequency-overlap table and the integration-time audit table were removed to the
machine-readable release with their essential content folded into prose (≈1.7 pages); a
page break before the online-only supplement became a rule (~0.5 page); one unused and
two over-long bibliography entries were cut and two multi-author entries shortened to
"et al."; four figures were reduced in width; and a full compression pass removed
roughly 150 lines of prose the referees had flagged as repetitive, promissory or
peripheral (the remaining revision-history narration, duplicate statements of the γ Lupi
misidentification, an audit sentence explaining an anomaly visible only in a table no
longer printed, and similar). Every number remains generated from the frozen export; no
figure was deleted.

# Verification

v3.33 compiles clean: 0 errors, 0 undefined references or citations, 0 multiply-defined
labels, no Type 3 fonts (the two figures regenerated for this revision are embedded as
TrueType), 38 pages, every figure file present, every citation matched to a bibitem.
