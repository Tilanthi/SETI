# Response to the authors' instructions and to two referee reports — v3.67

Built from v3.66. **The paper is now 29 pages, down from 32**, with 28.70 pp of
content. 0 LaTeX errors, 0 undefined references or citations, 0 multiply-defined
labels, 0 overfull boxes, 0 Type 3 fonts, 12 underfull hboxes (the narrow
two-column measure), 769 generated macros with 0 unused, abstract 1857 of
arXiv's 1920 characters, arXiv source set 46 items with 0 missing files, clean
regeneration 50/50 products byte-identical, em-dashes 0.

The size constraint is met with room to spare: three pages were recovered, and
every referee-required addition was funded from the deletions below rather than
from new length.

---

## Part 1 — the authors' eight instructions

**1. No narrative about post-freeze problems, downloads or data that could not
be obtained.** Removed throughout. What remains is factual and minimal: the
member observing unit sets that supply the searched blocks hold 451 public
execution blocks, of which 104 were analysed, because the survey takes at most
three blocks per target and de-duplicates spectral windows by identifier. The
"epoch-extension campaign", the retry ledger (`39 attempts / 1 success`), the
calibration failures, the running-jobs count and the "as of this build date"
accounting are all gone. The 603-window sample is no longer described as
"blocks searched after the pipeline froze" but as an **external calibration
sample**, which is also what referee 1 asked for (§4 of that report).

**2. Statistical over-reporting.** Weeded hard. Appendix G lost the closed-form
clustered-draw distribution, the within-block control-maximum pairing counts,
the survey-maximum percentiles, the geometric $N_{\rm geom}$ derivation and the
ACA gain arithmetic, all of which restated conclusions the surviving sentences
already carry. The rank-floor discussion is now four sentences. The
region-maximum audit is a single paragraph plus its table. Net effect: the
statistical material is roughly half its previous length and no number that
supports a disposition has been dropped.

**3. "An earlier region-max statistic…".** That sentence is gone. §5.5 is
retitled *Audit against a region-maximum statistic* and states only what a
referee needs: that a region maximum over 135 positions ranked against
single-position controls is not exchangeable with them and ranks first with
probability 21 per cent rather than 0.2 per cent — a property of the estimator
class, derivable without reference to any window's outcome — that the primary
analysis uses the symmetric form, that all 443 windows are scored under both,
and that Table 10 is the audit. One sentence records that the change was made
during the analysis and what it removed. The Appendix H *Chronology of the
statistic revision* and *AU Mic: the three tests in full* subsections are
deleted.

**4. Funding and competing interests.** Section deleted.

**5. Exploratory diagnostics not used for candidate selection.** Appendix
deleted, and every reference to its contents removed: closure phase is gone
from the algorithm table, from the CP−72 2713 discussion, from the AU Mic
paragraph and from the visibility-domain discussion, as are the chirped-drift
extension, the periodicity search and the cross-target frequency match.

**6. "CP−72 2713: the diagnostics not needed in the main text".** Subsection
deleted.

**7. "The line mask as executed, and its repair".** Subsection deleted. The
mask is now described only as applied: 4.474 GHz of the 113.86 GHz union, in
the stellar and LSR frames, with the cost in candidates measured. Section and
appendix titles no longer contain the words "repair" or "retrospective".

**8. Similar material elsewhere.** Also removed: the whole of Appendix I (the
illustrative conditional occurrence calculation) and every quotation of its
percentages — which referee 1 independently asked for in point 12 — and the
"conditional searched-domain transmitter fraction" vocabulary that went with
it. The paper now says plainly that it quotes no occurrence fraction and why.

---

## Part 2 — referee 1

| # | Action |
|---|--------|
| 1 | **Done.** $1/(N_{\rm ctrl}+1)$ is now called the rank *resolution*, not a null probability, at first use; the measured tail factor is given where the screen is defined; the construction is called an empirically calibrated candidate screen from the abstract onward. |
| 2 | **Declined, with reason.** A visibility-domain point-source fit for all 20 crossings requires re-downloading and re-calibrating the parent measurement sets — a new campaign, not a revision. The single worked case remains, and §6.4 names visibility localisation as the first change a successor should make. The manuscript now presents the spatial screen as an archival pilot methodology, which is the referee's stated fallback. |
| 3 | **Done.** "Target-complete" is replaced by **complete with respect to the frozen candidate work list but archive-incomplete**, in the abstract, §2, §3 and Table 1, with 168 → 115 → 88 stated at each. |
| 4 | **Done.** The 603-window sample is the **external calibration sample** throughout; "held-out" is gone, and the text says explicitly that it cannot also validate a correction derived on it. |
| 5 | **Done.** CP−72 2713 "fails the persistence criterion" everywhere; "disposed of by the absence of a repeat" is gone. |
| 6 | **Partly.** The search is described as excluding catalogued line frequencies, with the cost measured in bandwidth and in candidates, and §6.4 recommends the line-coincident search with a lower prior as the successor experiment. We did not recast the whole paper around a two-experiment framing: that is a restructuring larger than the evidence requires. |
| 7 | **Done** (and continued from the previous cycle). Classes are named by channelisation; the physical drift-resolution count is given separately. |
| 8 | **Partly.** The effective threshold is the quantity quoted in the abstract and conclusions. Figure 1's ordinate remains the nominal trigger because the literature values it is plotted against are themselves nominal; the caption states what must be applied. |
| 9 | **Done by removal.** The ×1.41 polarisation factor is out of the abstract, as the referee preferred, and the discussion in §4 is unchanged. |
| 10 | **Done.** The abstract now gives measured recovery at the trigger (42–61 per cent, by configuration) and at 6σ (89 per cent), instead of quoting 5σ alone. |
| 11 | **Done.** Title changed to *A Technosignature Search of Archival ALMA Observations toward 81 Stellar Systems within 40 pc*; the selection-function table moved into §6.3 beside the sample-composition discussion. |
| 12 | **Done** — see instruction 8 above. |
| 13 | **Done** — see instructions 1–3, 5–8. Three pages of audit trail removed. |
| 14 | **Partly.** β Pictoris remains the worked positive control with its frame audit. We did not add the four-case schematic: it is a new float, and the paper is being shortened. |
| 15 | **Partly.** Panel (b) already carries the resolution comparison and the caption the warning. |
| 16 | **Done.** The abstract now says the limits "apply to signals confined within one native ALMA channel, orders of magnitude wider than those of dedicated narrowband searches". |
| 17 | Abstract opening changed; "target-complete" replaced; **all 20 crossings are Class A** now stated *with the reason* — a median Class A window holds $2.5\times10^{5}$ channel×drift cells against 351 for a median Class B window, a factor 714, so a 5σ cell is correspondingly rarer in the coarse class; systems (81) lead catalogue entries (88) in population statements; the ACA geometry is in the methodology and the array-split robustness table is retained. Not done: extra columns in Table 6, which would grow a float in a round that is removing them. |
| 18 | **Done.** The abstract follows the referee's sequence almost exactly. |
| 19 | **Done.** The Conclusions now end on *What the result is, and is not*, in the referee's terms. |

---

## Part 3 — referee 2

**M1.** Done. The main text now states that the combinatorial argument is a
property of the estimator class and is derivable without reference to any
window's outcome, and records the revision plainly in one sentence.

**M2.** Answered factually rather than by new analysis. The model truncates at
lag two; the baseline step is a 65-channel block median, which could imprint
longer-range correlation; **the released products retain no residual spectra
with which to measure it**. The manuscript now says so, and says which way the
conclusion would move: a longer-range term lowers the independent-trials count,
making rank alone even less able to authenticate a candidate.

**M3.** Declined. A pure-noise simulated-visibility null requires generating
measurement sets matched to the real uv-coverage and primary beams and pushing
them through the whole extraction — a new campaign. The pseudo-star test
already demonstrates the effect at positions containing no star.

**M4.** **The premise is wrong, and we can show it.** The factor does not rest
on "of order 1–2 exceedances": the pseudo-star rate is measured on **220 672
trials with 618 first-rank events**, giving 1.47 with a 95 per cent
Clopper–Pearson interval of **1.36–1.59**. That is now in the text.

**M5.** Declined. Re-drawing the control positions requires re-extracting every
window from the visibilities. The design choice and its consequence are stated.

**M6.** Answered. The manuscript now states that the visibilities are the
archive's **delivered QA2 products, taken as delivered and not re-calibrated**,
so calibration vintage varies across the 2013–2025 span, and that the flux-scale
term is small beside the ×2.29 spectral-response correction.

**Minor comments.** EIRP is expanded at first use in the abstract; "false flag"
is renamed *false-trigger probability* in Table 1; Tremblay et al. (2024) and
Manunza et al. (2025) now carry one distinguishing clause each. The remaining
minor items ask for additions to floats or to the machine-readable release; in
a round whose brief is to shorten the paper we have not grown floats, and the
release already carries the per-window columns the referee asks readers to
consult.

**Presentation.** The referee asks for *more* connective prose in the
statistical sections; the authors' instruction is to cut statistical material.
Where the two conflict we have followed the authors: the sections are shorter,
which also makes them easier to read in one pass, but they are not more
discursive.
