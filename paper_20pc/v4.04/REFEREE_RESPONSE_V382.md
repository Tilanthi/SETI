# Response to the two referee reports

We are grateful to both referees. The reports converged on three things —
an internal numerical inconsistency, statistical-reporting hygiene, and
density — and all three are addressed. Every number below is generated from
the frozen analysis and checked by an automated audit that now runs inside
the build.

Section and table numbers refer to the revised manuscript.

---

## Referee 1

**1. Numerical consistency audit (required).** Both inconsistencies were
real and both are fixed at source, not in the text.

*0.405 against 0.44.* These were two different samples printed under one
name. `0.44` was the median rank of the processing-order calibration set;
`0.405` is the median rank of the pre-registered hold-out. The paper's
calibration now rests entirely on the hold-out, so the hold-out value is
used everywhere and the other macro is gone.

*75 against 77 reserved blocks.* The manuscript inferred the count by
differencing two populations that were never the same — the metadata's
"searched" list against the catalogue's blocks — which gave 75 where the
assignment itself says 77. The count is now read from the assignment.

An automated audit, `audit_numbers_v382.py`, runs inside `make_all.sh` and
fails the build on any disagreement. It covers the referee's list in full:
reserved blocks and windows, hold-out median rank, KS statistic and
probability, pseudo-star tail factor, crossings, stage-1 outliers,
attributed and unattributed counts, and the block accounting. **56 checks
pass, 0 fail.**

**2. The four unattributed events (required).** New
Table~\ref{tab:unattributed} gives one row each: star, execution block,
band, frequency, drift ceiling, $T_\star$, largest control statistic,
$P_{\rm eff}$, and whether a repeat block exists. Only CP$-$72~2713 has
one; the other three sit in the only block covering their frequency, so no
persistence test exists for them, and none has been tested in the
visibility domain. §5 now says so directly.

On the origin of the 3.2: it assumes **ideal exchangeability**. We now say
that, and give the alternative — folding in the tail excess measured on the
hold-out ($\times1.2$) raises the expectation to 3.9 and the probability to
0.47. The conclusion is unchanged either way, and the second is the fairer
comparison.

**3. CP$-$72 2713 quantified (required).** New Table~\ref{tab:cprepeat}
puts both blocks side by side: separation, on-source time, channel rms,
channelisation, primary-beam FWHM, test frequency and drift, the drift
track's sweep, measured flux in each, $T_\star$ in each, the largest
control statistic in each, and the $T_\star$ a persistent source at the
first block's flux would have produced. The qualification the referee asks
us to keep is kept and is stated in the caption: intermittent emission is
not excluded.

**4. Two experiments, separated.** The abstract now opens with
"(1) a drifting spectral-carrier search in 403 fine-resolution windows" and
"(2) a channel-confined excess-power search in 1252 coarse-resolution
windows … which has no useful drift discrimination", and says they should
not be pooled. Per-class figures were already given for EIRP, completeness
and the mask; the mask is now also reported per class (point 8).

**5. Figure 1 ordinate.** Relabelled "EIRP at the native-channel detection
threshold (W) — NOT sensitivity to a 1 Hz transmitter", verified by
extracting the text back out of the figure PDF.

**6. A schematic of the response correction.** New Fig.~\ref{fig:hanning}:
the same unresolved carrier at a channel centre, a quarter-channel off and
on a boundary, with the smoothed channel values each produces (50, 44, 38
per cent in the peak channel), and the resulting penalty from $\times2.00$
to $\times2.67$ with the survey median $\times2.29$ marked.

**7. $P_{90}$ promoted.** The abstract now leads with the 90 per cent
recovery power, and Table~\ref{tab:searchspace} lists $P_{90}$ above
$P_{\rm eff}$ above $P_{\rm trig}$, in that order, with $P_{90}$ in bold.

**8. The molecular mask.** We now state plainly that **no constraint of any
kind is placed on artificial emission inside the masked regions, at any
signal strength**, and that every limit is conditional on the exclusion.
The cost is given per class: 0.9 per cent of the Class A union against 0.3
per cent of Class B. Class A pays three times the fractional price, because
its coverage sits in the line-tuned windows a molecular mask is built to
remove.

**9. Control geometry as a methodological conclusion.** §5.3 now states it
as one: *spatial control positions are a sound way to prioritise candidates
in targeted interferometric archival data and an unsound way to establish
significance in them*, with the reason (the fields are not blank sky and
the response varies across the annulus) and the remedy (a visibility-domain
point-source test). We agree this is a result and not an embarrassment.

**10. Population modesty.** The conclusions now say the result "constrains
this ALMA-observed subset of nearby systems over the frequencies, epochs
and powers actually sampled, and carries no demographic weight for the
nearby stellar population as a whole". No occurrence fraction is quoted.

**11. Figure 3 simplified.** The panel carried four variables on 87 rows.
It now carries two: position in frequency, and which of the two experiments
covered it. The EIRP colour scale is gone (that is Fig. 1's subject), and
the marginal panel — systems covering each gigahertz — is given real
vertical space.

**12. Defensive prose (required).** Table 1 is now labelled as the single
place where every term and power scale is defined, and carries
$P_{\rm trig}$, $P_{\rm eff}$ and $P_{90}$ explicitly. The restatements in
§4.2 and the conclusions are cut.

**13. "Persistent, independently confirmed".** Enforced throughout,
including the survey table row and the discussion.

**14. Terminology.** $1/513$ is now called the *resolution* of the rank
statistic, never a false-alarm probability, and the text says the
attainable rate is measured because the controls are only approximately
exchangeable.

**15. The principal result, simply.** The Conclusions now open with it:
the archive can be turned into a reproducible mm/submm technosignature
experiment, and what limits it is not ALMA's raw sensitivity but coarse and
heterogeneous spectral resolution, molecular-line confusion, sparse
temporal coverage, and the behaviour of spatial controls in fields chosen
because something interesting is in them.

---

## Referee 2

**1. The factor 16.** The referee's diagnosis is exactly right. The ratio
was computed against a Bonferroni scale read from a frozen round-5 macro
file derived from a superseded window count. Recomputed from the current
catalogue it is **65**, and it now appears as 65 in all three places. The
scale, the window count and the ratio are asserted to be one calculation.

**2. Exact $p=0.00$.** A formatter is now shared across the generators:
anything that rounds to zero at the printed precision is reported as a
bound. Two figure panels carried the same fault and are fixed too. A sweep
confirms no generated probability prints as an exact zero.

**3. Radial non-exchangeability.** (a) We now commit to a cause in the
first sentence of §5.3.2: images are primary-beam corrected, so the true
noise rises outward, while the search divides every position by one scale
with no radial dependence. Outer positions are divided by too small a
scale and stand high; the star, inside the annulus, is divided by too large
a scale and stands low — which is the observed sign. Extended emission on
short baselines adds to it. (b) The completeness side is now addressed
explicitly: extrapolating the out-of-sample radial profile to the stellar
radius gives $+0.08\sigma$, so the scale applied at the star is too large
and the quoted recovery is **pessimistic** by of order 2 per cent of the
threshold, not optimistic. Small, safe in direction, and not zero.

**4. Pre-registration chronology.** Now given in one place and generated
from the repository timestamps, with an assertion that the order holds: the
detection statistic was fixed on 2026-09-09, the candidate criteria on
2026-09-11, the hold-out rule five days after the statistic, and the first
reserved block was searched three days after that. No analysis choice in
the paper postdates the reservation.

**5. The Class B 0/500 result.** Moved into the main text at §4.5, with the
explanation: the recovery criterion required the recovered drift to match
the injected drift, which a coarse window cannot satisfy by construction,
so the test measured its own inapplicability. Scored on detection alone the
same windows reach $T_\star = 20.5$, 65.3 and 217.7 at one, three and ten
times the per-integration noise.

**6. Haystack fraction.** Added, labelled as an illustration and nothing
else, with each axis separate: $5.4\times10^{-3}$ of the catalogued stars
within 40 pc, 0.39 of the 0.3–300 GHz band, 56 hours of cumulative staring
across 87 systems. The product, ${\sim}2\times10^{-7}$, is given with the
explicit warning that the axes are not independent and it is not a bound.

**7. Figure 1 caption caveat.** Added, in bold: **this is not a
like-for-like sensitivity comparison**, because each programme's $5\sigma$
is its own threshold statistic, evaluated over a different channel width
and corresponding to a different completeness.

**8. Density.** Two self-audit tables moved to the appendix; the
five-criterion decision tree is now an enumerated list; the longest
sentences in the main text are broken into statements. No claim or number
was dropped.

**9–10. Terminology reminders and Table 5.** The load-bearing terms are
re-stated briefly where the results and calibration sections first lean on
them. Table~\ref{tab:searchspace} now sits at the end of the sample
section, before the methods, where a reader meets the denominators first.

**11. Title.** Changed to "A Search for Spectral Technosignatures in the
Public ALMA Archive: 94 Stars within 40 Parsecs".

**Minor items.** The precision asymmetry is explained in a footnote to the
survey table (relative checks to a per cent; the absolute flux scale rests
on ALMA's delivered calibration, several per cent). The polarisation scope
now says why the per-hand search was not run. The $\gamma$ Lupi
reclassification is flagged in the main sample description. Figure 9's type
is enlarged, its strata labelled on the panel, and its clipped title moved
into the caption.

---

## Build state

32 pages; 0 errors, 0 undefined references, 0 multiply-defined, 0 overfull
boxes, 0 Type 3 fonts; 846 macros with none unused; abstract 1842 of
arXiv's 1920 characters; clean regeneration **64/64 byte-identical**
including every figure; numerical audit **56 pass, 0 fail**.
