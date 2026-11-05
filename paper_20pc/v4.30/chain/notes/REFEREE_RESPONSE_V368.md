# Response to two referee reports, plus three internal review rounds — v3.68

Built from v3.67. **29 pages, unchanged** (28.98 pp content). 0 LaTeX errors,
0 undefined references or citations, 0 multiply-defined labels, 0 overfull
boxes, 0 Type 3 fonts, 12 underfull hboxes, 778 macros with 0 unused, abstract
1874 of 1920 characters, arXiv set 46 items, clean regeneration 50/50
byte-identical, em-dashes 0.

All work was done in this one directory; there are no intermediate versions.

---

## The three revisions referee 1 called necessary for acceptance

**(1) The EIRP conversion.** The referee is right that $S_{\min}\Delta\nu$ is an
integrated power only if the channel's effective noise bandwidth equals its
separation, which for a smoothed correlator it does not. §4 now says so
explicitly and states that this is exactly what $C_{\rm response}$ corrects,
and that the correction is **calibrated, not assumed**: injecting unresolved
tones of known amplitude into real visibilities and recovering them through the
unmodified pipeline returns ×2.02–2.69, median ×2.31, against the analytic
×2.29 — the medians agree to one per cent, and the quoted range is
window-to-window variation in the correlator response, not an error on the
estimator. EIRPs are quoted to two significant figures, the precision the flux
scale supports.

**(2) The false-alarm factor's uncertainty.** The referee's objection was
correct and, on checking, understated. The v3.67 text quoted a Clopper–Pearson
interval of 1.36–1.59 computed on 220,672 "trials" — but that number is a count
of pooled rank values from an earlier analysis, **not** the pseudo-star trial
count. The pseudo-star test uses the 16 inner probes of each calibration
window, so the true trial count is 9,648, and the interval is an order of
magnitude wider. `tailboot_v368.py` recomputes the test from the stored control
vectors and bootstraps it as the referee asked:

| estimator | 95 per cent interval on the factor |
|---|---|
| naive binomial (Clopper–Pearson) | 1.1 – 2.3 |
| bootstrap resampling whole windows | 1.1 – 2.2 |
| bootstrap resampling whole execution blocks (150) | 1.1 – 2.1 |

Clustering barely widens it, because the 30 first-rank events are spread across
windows rather than concentrated. The paper now says the factor lies between
about 1 and 2 rather than quoting it to two figures, and that no disposition
changes anywhere in that range. **This correction was found because the referee
asked; the published interval was wrong.**

**(3) CP−72 2713 recast.** "Fails the persistence criterion" is gone from the
abstract, §5 and the conclusions. The event is now an *unconfirmed single-epoch
event, with persistent emission of the same strength excluded on a 2.05-h
baseline*, and the text states plainly that persistence is the survey's
operational criterion and not a physical requirement on a transmitter: an
intermittent emitter is not excluded by two executions two hours apart. Figure 2
no longer terminates in "0 candidates" but in **0 persistent candidates; 3
identified astrophysical; 1 unexplained, non-repeating**, which is the
three-way disposition the referee asked for.

## Referee 1, remaining points

Gross versus unmasked bandwidth is now systematic: **113.9 GHz gross frequency
coverage, 109.4 GHz effective unmasked search space**, in the abstract, §4, the
scope box and the conclusions. The Conclusions open literally ("We searched a
defined subset of public ALMA observations covering…") and are cut to four
paragraphs. The molecular-line species criterion is now stated in the main text
with its consequence — a full Splatalogue selection would mask 75 per cent of
the union against 3.9 per cent here, so "coincident with a known molecular
line" is a statement about a catalogue, not a binary property — together with
the argument that no masked crossing exceeds its own controls, so no plausible
species list changes a disposition. The six coarse-noise windows are stated to
be excluded from the sensitivity accounting **only**. `p_rank,min` is described
in Table 1 strictly as rank resolution. The M-dwarf and F/G halves of the
sample-bias sentence are separated, as the referee's logic requires.

Declined, with reasons: the visibility-domain rerun of the four stage-1
outliers needs the parent measurement sets re-downloaded and re-calibrated, a
campaign rather than a revision; the compact CP−72 table and the extra columns
in Table 6 would grow floats in a paper under a strict page cap, and the
quantities are in the released catalogue.

## Referee 2

M1 is answered with a number (21 of 5,908 temperature-classified M dwarfs
within 40 pc carry a searched window) and a one-clause version in the abstract.
M2(b) is now a listed caveat in the *Scope of the constraints* box: the radial
correction is derived on the calibration sample and is therefore **not
validated out of sample**. M3(b) is one sentence in the Conclusions: the
zero-candidate result is unchanged under either form of the statistic. M6 is
answered: $N_{\rm eff}\simeq30$–43 is an analytic beam-geometry estimate, not a
measured correlation length, and it is the worst case. M7 is done — every
run-in header in §5, §6 and the appendices is now a numbered subsection. M9 is
done: the title reads *…toward 88 Stars in 81 Systems within 40 pc*. m2 gives
the noise estimator as a formula; m4 now reads "searched only once before the
present work".

M5 is declined: an illustrative occurrence figure is exactly what the authors
and referee 1 asked to have removed, and re-introducing it would undo that.

## What the three internal review rounds caught

**Round 1 — three errors in material added earlier in this same round.** The
M-dwarf fraction paired a numerator restricted to temperature-classified
searched stars with a census denominator, implying a completeness it does not
have; the EIRP paragraph claimed the estimator recovers injected power "to ~10
per cent" when the medians agree to one per cent and the ±range is physical
spread; and the paper carried two tail factors (1.4 released, 1.6 recomputed)
with no reconciliation. All three fixed.

**Round 2 — the figure had not followed the text.** Figure 2 still ended in "0
candidates" after the disposition vocabulary had changed. Cross-references and
table numbering were re-audited after four floats moved sections; all resolve.

**Round 3 — an unverifiable assertion, withdrawn.** The new sentence on the six
coarse-noise windows claimed "none is a crossing", which cannot be checked from
the release because those windows are not in it. Replaced with what the physics
does support: the deflation is common mode, so the signal-to-noise statistics
and ranks remain valid and were carried through candidate generation on that
basis.

**Round 3 also caught a build-ordering defect**: `v363_calc.py` now reads the
M-dwarf row out of `tab_selection.tex`, which `make_all.sh` generated *after*
it. The working directory built fine because the file was already present; a
clean regeneration failed outright. `make_tables_v328.py` now runs before
`v363_calc.py`, with the dependency written into the script. This is the second
ordering bug of exactly this shape in two rounds, and only the
clean-regeneration test finds them.
