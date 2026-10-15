# BUILD NOTES — v3.86

Two referee reports, 29 numbered and lettered points, worked one at a time
in the order given. Ledger: `CHECKLIST_V386.md`. Every point is closed.

## Gates

| gate | value |
|---|---|
| pages | 43 (main 25.4 / back 0.8 / appendices 16.6 / bib 0.3) |
| LaTeX errors | 0 |
| undefined references / citations | 0 |
| multiply-defined labels | 0 |
| overfull boxes | 0 |
| Type 3 fonts | 0 |
| underfull boxes | 27 (the narrow two-column measure) |
| macros defined / unused | 1065 / 0 |
| abstract | 1903 characters (arXiv limit 1920) |
| clean regeneration | **83/83 byte-identical** |
| number audit | 49 pass, 0 fail |
| catalogue self-sufficiency | 0 fail |
| arXiv set | 72 items |

## The three changes that alter what the paper claims

**The headline sensitivity is now the sensitivity of the search, not of its
trigger** (R1-1). A signal does not become a stage-1 event by crossing
5σ; it must also outrank all 512 spatial controls, whose Class A median is
5.79σ. The abstract, Table 5, the boxed reading rule, §6.1, the
conclusions and the principal sensitivity figure now lead with
$P_{90}^{\rm sel}$ — $8.7\times10^{13}$–$1.4\times10^{17}$ W per window,
median $2.8\times10^{15}$, and per system $8.7\times10^{13}$–$4.4\times10^{16}$
with a median of $1.5\times10^{15}$. $P_{90}$ stays, relabelled as the
matched-filter completeness. Figure 6 now plots both curves, and the gap
between them is the point.

**Class A is the primary statistical reference population** (R1-2, R2-1).
Every stage-1 outlier is Class A, so conditioning on the class that can
produce them is the fair comparison. The abstract and conclusions now lead
with 1.1 (0.5–1.4) expected against 4 observed, describe it as a modest
population excess rather than evidence for any individual event, and the
all-window figure is a secondary diagnostic in an appendix table. The
paper also now traces the consequence the referee asked about: a tail
large enough to absorb the excess would make the quoted completeness
optimistic by about the same factor, so the two cannot be traded
independently.

**The recurrence test is shorter than "23 repeat observations" suggests**
(R1-8). Dating every one of the 404 searched blocks — 200 from the
archive's execution-block index, 204 from their member observing unit —
gives separations of 0–2 d between the four unattributed events and their
repeats. So what the non-recurrence excludes is a transmitter persistent
over **hours to days**, and nothing here bounds one with a duty cycle
measured in months. That is a weakening of a claim the paper had been
making more strongly, and it is now stated in the abstract, the summary,
the candidate table and the conclusions.

## Also done

- **R1-3** §4.2 now introduces the spatial rank as an empirically
  calibrated screen and states that $1/513$ is a resolution and not a
  false-alarm probability *before* developing it, with the Bonferroni
  comparison as an equation (also R2-m2). Three later restatements removed.
- **R1-4** the visibility test is stage 2 of the pipeline, and one new
  table carries all 13 stage-1 events through every stage — screen,
  localisation, attribution, recurrence — so a reader can see in one place
  why each was rejected. Figure 3 and the step summary follow the same
  eleven-step chain.
- **R1-5** the null claim now always reads "no persistent, independently
  confirmed narrowband spectral technosignature within the frequency,
  drift-rate, duty-cycle and sensitivity domain searched", and is never
  shortened.
- **R1-6** the Class A union, 47.7 GHz, is the primary experiment's
  bandwidth in the abstract and Table 5; Class B adds 70.4 GHz of archival
  coverage; the 118.1/113.3 GHz figures are the total.
- **R1-7** the per-system unique Class A bandwidth: median 1.84 GHz,
  10th–90th 1.73–6.17, range 0.11–19.08, which is 3.9 per cent of the
  survey's own union — the quantitative reason no occurrence rate follows.
- **R1-9** the title counts **82 stellar systems**; the abstract gives the
  90 catalogue entries in the same sentence.
- **R1-10** main text reduced **19.3 per cent**, from 29.9 to 25.4 pages,
  by moving the hold-out validation, the radial-gradient derivation, the
  line-exclusion cost, the CP−72 worked example, the β Pictoris recurrence
  derivation and five audit floats into the appendices. Tables 1 and 2 are
  merged into one glossary.
- **R1-11** Figure 1 is explicitly parameter-space context; the caveat is
  the first thing the caption says; "competitive EIRP" is gone.
- **R1-12** §7 opens with the narrow organising conclusion and the
  demographics follow it.
- **R1 textual** stage-1 event vs candidate; Class A union and system count
  in the abstract; "0 independently confirmed candidates"; the expectation's
  uncertainty beside it; the mask as unsearched space in the conclusions;
  the frequency-range comparison named (∼10 GHz, the Breakthrough Listen
  and haystack boundary, so about two orders of magnitude); and β Pictoris
  qualified as an *astrophysical* positive control, with the injection
  campaign named as the one that tests artificial-carrier recovery.
- **R2-2** Author contributions, Funding and Competing interests sections
  added. Each carries a `%% AUTHORS:` marker; the competing-interests
  wording is written to be accurate **only if** VBRL Holdings had no role,
  and `AUTHOR_ACTIONS.md` says so in terms.
- **R2-3** §5's bookkeeping moved to the parallel appendix sections and the
  narrative shortened.
- **R2-4** one abstract sentence: the threshold is an injection-calibrated
  trigger power, not a statistical significance.
- **R2-m1** the illustrative $\sqrt{\Delta\nu}$ rescaling is now given as a
  number — ÷418 to a 2.79 Hz channel, ${\sim}6.8\times10^{12}$ W — and
  flagged as not achievable.
- **R2-m3** the transfer bracket restated in the conclusions.
- **R2-m4** a worked example of the combination for one window, showing the
  one-sided terms applied to the upper end only.
- **R2-m5** preprint entries marked consistently.

## Bugs found while doing it

- **A fourth consecutive forward dependency**, caught only by the clean
  regeneration: `make_fig_funnel.py` came to read `NStageLocalised`, which
  `stagetable_v386.py` emits later in `make_all.sh`. Reordered.
- **`EirpEffMedian` was emitted by two generators** from two different
  definitions of $P_{\rm eff}$. The v3.51 one is retired.
- **The per-system macro trio silently changed meaning** when the
  sensitivity figure switched to the selection power: `med` became the
  selection median while `PNinetySys*` still claimed to be the trigger
  completeness. Split into two families, and the two independent
  derivations of the selection median now cross-assert.

## Author actions

Four submission blockers remain, all the authors': the Zenodo DOI, the
submission git tag, the White (2026) identifier, and confirmation of the
three new disclosure statements. See `AUTHOR_ACTIONS.md`.
