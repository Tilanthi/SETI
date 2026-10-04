# Response to the second-round referee report

Manuscript: *A Search for Time-Variable and Frequency-Drifting Narrowband Technosignatures toward
ALMA-Observed Stars within 40 pc of the Sun: Survey Design and First Results*
White & Dey — revision v3.29

---

## Note to the editor: the second report is for a different paper

Two reports were forwarded. The first is unmistakably on this manuscript and we address it in full
below. **The second is not about this paper at all.** It reviews a manuscript of ~18 pages
concerning the \(L_{\rm IR}\)–\(L'_{\rm HCN(3-2)}\) relation in Galactic clumps, with a slope of
1.22 ± 0.07, a W49A data point, a 107-source sample in a "Table A1", and citations to
"Grozdanova et al., in preparation".

Our manuscript is 38 pages, has 14 figures, contains no Table A1, no W49A, no Galactic clumps, no
\(L_{\rm IR}\)–\(L'_{\rm HCN}\) relation, and no reference to Grozdanova et al. Our only mention of
HCN is as one of eight molecular species in a line-exclusion mask. We have therefore not attempted
to act on that report, since doing so would mean inventing content. We would be grateful if the
correct report could be forwarded, and we are happy to respond to it promptly.

---

# Referee 1 — point by point

We accept this report essentially in full. It identified one substantive physical error in our
presentation, one class of bookkeeping failure that was worse than we had appreciated, and a
framing problem with our headline result that we agree needed fixing. The revision is structural,
not cosmetic.

## The four conditions the referee set for acceptance

**(a) A complete single-version numerical audit.**
Done, and done in a way that prevents recurrence rather than patching symptoms. Every survey
quantity is now emitted as a LaTeX macro by a generated file, `survey_numbers.tex`, produced by
`make_numbers.py` from `survey_stats.json`. The manuscript no longer contains typed digits for any
of these quantities; it contains `\NWindows`, `\NStars`, `\NSystems`, `\NCandidates`, `\OccMeasured`
and so on. A number therefore cannot disagree with itself between sections, and refreshing the data
export updates the abstract, body, tables and captions in one step.

This is exactly the referee's "generated from that table rather than typed manually", and it
addresses the root cause: the manual effort of keeping numbers consistent scaled with the number of
places each number appeared, so every revision reintroduced errors. That coupling is now broken.

Every specific error the referee listed was real. All are corrected:

| Referee's finding | Was | Now |
|---|---|---|
| Conclusions revert to three candidates incl. AU Mic | "Of the three candidates … one, towards AU Mic" | four spatially significant windows, three CO (incl. HD 48370), one CP−72 2713, **zero candidates** |
| Conclusions base probability statements on the obsolete AU Mic result | present | removed |
| 42 vs 79 independent systems | both | `\NSystems` = 79 throughout |
| 46 processed stars | present | `\NStars` = 85 |
| 104/208 called "≈41 %" | 41 % | `\PctPlanned` = 50 % |
| local-population fraction given as both ~7 % and ~1 % | both | ~1 %, consistent with the 40 pc Gaia reference census (168/17,566) |
| "extend to 30, 40 and 50 pc once the 20 pc sample is complete" | present | "extending it beyond 40 pc" |
| Table 2 vs glossary give different definitions of "candidate" (zero vs three) | both | single definition, zero candidates, in both places |

**(b) Correction of the Figure 1 / narrowband spectral-power interpretation.**
The referee is right, and this was the most important scientific correction in the round. We have
**withdrawn the W Hz⁻¹ panel entirely** rather than relabelling it, because we could not construct
a caption that would reliably prevent the misreading.

The text now states the reasoning explicitly: EIRP\(_{5\sigma}/\Delta\nu_{\rm ch}\) is a
channel-averaged equivalent spectral luminosity, correct for emission that *fills* the channel and
not for an unresolved carrier. Our own worked example is used to make the contradiction visible —
the deepest window reaches \(1.6\times10^{13}\) W in a 15.625 MHz channel, and a 1 Hz carrier there
still needs the whole \(1.6\times10^{13}\) W, so its intrinsic spectral power is of order
\(10^{13}\) W Hz⁻¹, not the \(10^{6}\) W Hz⁻¹ that division returns. Presenting the latter beside
Hz-scale backends flattered ALMA by six orders of magnitude against precisely the signal class we
are searching for. Figure 1 is now a single-column, total-power comparison only, at each
instrument's native resolution.

While rebuilding it we found that **the `eirp_context.pdf` shipped in v3.28 was not the figure its
caption described** — the file on disk was an EIRP histogram, while the caption described the
scatter comparison. That is now fixed too, and the literature values were re-verified against the
published papers in the process; one was wrong, and is corrected below.

**(c) A more defensible treatment of the 6.5 % occurrence statement.**
We have demoted it, reframed it and quantified what it is conditional on.

- The **principal result is now the non-detection and the threshold range**, as the referee
  recommends. The abstract says so in those terms.
- The occurrence number is presented as a *secondary, deliberately conditional* calculation, and we
  no longer call it a prevalence. It is an **effective conditional occurrence bound given occupancy
  of each target's own observed frequencies**, defined on the **79 systems processed in this
  release** — not the 168-star ALMA-covered census, and not the 40 pc stellar population.
- The duty-cycle degradation now travels with it everywhere it appears: 6.5 % at *D* = 1, 13 % at
  *D* = 0.5, 65 % at *D* = 0.1.
- Most importantly, we now **measure how much the conditioning is doing**, instead of asking the
  reader to supply their own prior. Adopting the simplest transparent choice, a uniform \(p(\nu)\)
  across ALMA's tuning range, and evaluating \(F_i=\int_{\Delta\nu_i}p(\nu)\,d\nu\) honestly rather
  than setting it to one: the per-system fine-channel union has a median of 1.73 GHz, so \(F_i\)
  falls to a mean of \(4.5\times10^{-3}\) (Bands 3–8) or \(2.2\times10^{-3}\) (Bands 3–10), and
  \(\sum_i C_i\) is 0.27 and 0.13. **The bound becomes vacuous** — one would need \(f\approx3.8\) or
  7.8 transmitters per system before this survey expected a single detection. Under any
  frequency prior spread over ALMA's tuning range, this release constrains nothing, and the entire
  content of the quoted numbers is what the conditioning supplies. We say that in the text.

**(d) A fully traceable injection/recovery dataset.**
We cannot meet this in the present paper, and we say so plainly rather than implying otherwise. The
retained products preserve the campaign's pooled recovery fractions but not its trial-level records,
so the denominators are reconstructed from the campaign design. The referee is right that this is
inadequate provenance for a headline result, which is one reason the occurrence bound is now
secondary and is labelled a **pilot, configuration-limited** estimate.

We have taken the second option the referee offers, and in addition:
- the new completeness figure states on its face that the drifting rows share one pooled
  measurement rather than carrying independent per-cell measurements, and is drawn as discrete
  cells rather than an interpolated surface so it cannot imply data we do not have;
- trial-level logging — identifier, dataset, amplitude, frequency phase, drift, morphology,
  recovered flag — is committed for the next release, along with configurations spanning band,
  channel width, integration time and primary-beam position.

One consistency check is worth recording: the reconstructed denominator *n* = 24 is corroborated
by the reported percentages themselves, which are exactly *k*/24 to rounding (4, 10, 14, 18, 20 of
24 give 16.7, 41.7, 58.3, 75.0, 83.3 %). That is reassuring but it is not a log, and we do not
present it as one.

## Remaining points

**3. Narrow the definition of the search in title, abstract and conclusions.**
Agreed and applied. The title already carried "time-variable and frequency-drifting"; that
terminology is now used consistently, and the abstract states in its opening that a phase-steady
beacon lies outside the class this pipeline can constrain. We have audited for unqualified
statements of the form "EIRP thresholds bound any transmitter present above them" and qualified
them by morphology.

**5. Reformulate the occurrence interpretation.** Covered under (c). We took the referee's second
option — avoid "prevalence", call it an effective conditional occurrence bound — and then went
further by evaluating the first option numerically to show what the conditioning is worth.

**6. Restrict the population claim to the processed sample.**
Applied. The denominator is the 79 independent systems of this release. We have also stopped
calling our own sample a "volume-limited census": it is an **archive-defined 40 pc sample**, the
intersection of a volume-limited catalogue with a strongly selected archive, and the abstract now
says so in those words. The term "volume-limited" survives only where it correctly describes the
Gaia reference census.

**7. Stronger validation of the control-ring framework.**
We have run the null experiment the referee asked for, using the controls themselves as
pseudo-stars. For every window, each of the 512 control positions was ranked against the other 511
by exactly the statistic and add-one rule applied to the star, and the ranks pooled over the
release. The result: **213,504 pseudo-star ranks, uniform to the resolution the ensemble can
express** (mean 0.5010 against 0.5; the KS *D* = 1/512 is the discreteness floor of a 512-point rank
statistic, *p* = 0.39), and uniform within every receiver band and at both channelisations.
Comparing the 417 real stellar ranks against that pooled distribution as two samples gives
*p* = 0.31 — the stellar position behaves like one more position in its own ring. This is now in the
main text as the null calibration the argument needs, measured rather than assumed.

We have also reconciled the description the referee found confusing. The **operative criterion, the
symmetric single-position statistic, is applied to all 417 windows** and always was; what is limited
to seven locally reprocessed windows is a *richer variant* that additionally maximises over a source
region at each control, which does require raw-visibility reprocessing. The old text called that
variant "the designed principal test", which invited exactly the reading the referee gave it.

The one departure we found, the fine-channel stratum at *p* = 0.018, is retained and reported rather
than pooled away; it is driven by the four flagged windows, i.e. by real astrophysical signal in the
windows where narrow lines are detectable. We say that, and we also say that fine-window rank
probabilities should therefore be treated as slightly optimistic. The stratifications on control
radial position and primary-beam gain remain impossible from the retained products, and we say that
too rather than substituting something else.

**8. Simplify the candidate nomenclature and history.**
Applied. AU Mic no longer appears anywhere as part of the final candidate sample; the final
presentation contains only the four windows the frozen pipeline produced. A concise subsection
retains the methodological lesson — an initial asymmetric statistic was identified as biased, and
what replaced it — with the detailed forensics in an appendix.

**9. Strengthen the molecular-line vetting language.**
Applied, in the referee's own terms. The text now distinguishes "not within the eight-line automated
mask" from "no plausible known astronomical transition", states that the eight-species list is a
contamination cut and not a complete catalogue, and reports that the one unattributed window was
separately re-queried against a wider catalogue (nearest entry H¹³CN(4→3) at −195 km s⁻¹). The
defensible reading is stated as "no plausible known transition identified", explicitly a statement
about the catalogues consulted rather than a proof that none exists.

**10. The drift-limit equation.**
Checked. The source is `c\dot\nu/\nu`, which is correct; the referee's reading almost certainly came
from the inline dot accent extracting as `c ˙ν/ν`. Since the point is central to the selection
function and evidently easy to misread inline, we have promoted it to a displayed equation,
\(a_{\rm los}=c\,\dot\nu/\nu\), and — as the referee suggests — added the frequency-independent form
alongside: 12–13 Hz s⁻¹ GHz⁻¹ is \(\dot\nu/\nu=(1.2\text{–}1.3)\times10^{-8}\) s⁻¹, i.e.
\(|a_{\rm los}| = 3.6\text{–}3.9\) m s⁻², independent of observing frequency. That also resolves an
inconsistency of our own, between the 3.6 m s⁻² ceiling quoted in one place and 3.9 m s⁻² in
another: they are the two ends of the same range.

**11. Moderate the novelty claims.**
Applied. The claims are now explicitly scoped: to our knowledge each is new *in an ALMA archival
technosignature survey*, with no wider priority claim, since several have counterparts in the
centimetre-wave literature and we have not done the exhaustive search a general claim would need.
Closure phase is presented as a demonstrated future diagnostic with no discriminating power at
present sensitivity, and we no longer describe any window as having "survived" it.

**12. Compression and restructuring.**
The paper is 38 pages, unchanged, despite the additions above — the space came from compressing
repetition and developmental narrative, not from removing analyses. Developmental history, obsolete
statistics and extended QC diagnostics now sit in the online-only appendices.

**Headline result.** We have adopted the referee's formulation as the paper's primary claim, close
to their wording: a reproducible ALMA archival pipeline has searched 417 spectral windows toward 85
stars / 79 independent systems over a highly non-uniform effective frequency union, finding no
credible time-variable or sufficiently frequency-drifting narrowband signal, at nominal
native-channel EIRP thresholds of \(1.6\times10^{13}\)–\(2.8\times10^{17}\) W. The occurrence bound
follows as a secondary, conditional interpretation.

**Figures.** The coverage waterfall has been moved to follow the sample description, where the
referee wanted it — it now appears on page 5 and does the work of making the conditional nature of
any population statement obvious before the reader reaches the statistics. The injection figure has
been brought into the main article, and the requested compact completeness surface (recovery against
amplitude and drift fraction) has been added, drawn honestly as discrete cells.

---

## Things we found ourselves, in the course of this revision

- **`eirp_context.pdf` did not match its caption in v3.28** — the file on disk was a histogram, the
  caption described a scatter plot. Rebuilt.
- **A literature value was wrong.** Our comparison figure plotted Margot et al. (2023) at
  \(1.0\times10^{13}\) W within 100 pc; the published value is \(1.35\times10^{13}\) W. Corrected.
- **"Only targets within ~3 pc reach below the Arecibo-like EIRP" was misleading**: the two stars
  concerned are the two resolved components of G 272-61, i.e. **one bound system**. Reworded.
- **An unexplained number in our own prose.** The injection campaign is described as using a
  "49-trial drift grid", but 5 amplitudes × 5 drift fractions = 25 design cells and
  1200/6/5 = 40 trials per amplitude; neither is 49, and no retained product explains it. We have
  flagged it rather than harmonising it silently, and it will be resolved with the trial-level
  logging committed above.

## Still outstanding, for the authors

Unchanged from the previous round and still open: the VBRL affiliation and competing-interest
wording; an arXiv identifier for White (2026); and the submission tag plus Zenodo DOI — the
repository still carries no tags at all.
