#!/usr/bin/env python3
"""v3.51 stage 6: the last of the compression.

Same rule as stage 5: duplication and narration go, evidence and caveats
stay.  The coarse-noise defect keeps every one of its four arguments (gap
size, direction, mechanism, no coverage cost); the CP-72 2713 catalogue
argument keeps its numbers.

  S6-1  The coarse-noise defect, compressed.
  S6-2  The duplicate-row paragraph, compressed.
  S6-3  CP-72 2713: the catalogue-transition paragraph, compressed.
  S6-4  Sec. 3's census-fraction paragraph, compressed.
  S6-5  Sec. 5's opening roadmap, compressed.
  S6-6  Sec. 6.3 subsamples, compressed.
  S6-7  The line-exclusion section, compressed.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------ S6-1
sub(r"""The retained population is itself broad, so the exclusion does not rest on its
narrowness; $q$ runs over a factor ${\sim}290$ of the sample median, mostly the
band dependence the same relation predicts through SEFD. It rests on the size of
the gap, the six sitting a factor $1.5\times10^{3}$ below the lowest retained
window across an empty 3.2 decades, so that any threshold between
$1.5\times10^{1}$ and $2.2\times10^{4}$ in absolute $q$ units selects the same
six. It rests also on direction: $\sigma$ is estimated from the control probes
and applied to every position of a window alike, so a window-level deflation can
only over-state sensitivity, never manufacture a star-exceeds-ring window. All
six have on-source times of 12 to 48\,s, and no integration-time cut is applied
anywhere.

The six share a signature rather than an origin in the observing programme: all
are \DefectArrays{} array, \NDefectBandSix{} in Band~6 and \NDefectBandSeven{} in
Band~7, all at \DefectChanwMHz\,MHz, in \NDefectEBs{} execution blocks across
\NDefectProjects{} projects, and every one has a normally behaved finer-channelised window covering the same
frequencies in the same block (Appendix~\ref{app:provenance}). That is the
signature of a channel-averaged auxiliary window riding on a
frequency-division science baseband, and the archive metadata identify the
mechanism without any re-extraction. Those windows carry a constant WEIGHT
column, so they never received the science baseband's calibration, and the
deflation is common mode in the data and in the weights alike. Common-mode
deflation leaves the signal-to-noise ratio the search actually uses untouched,
which is why the defect can only misstate a threshold and can never
manufacture a flag, and why it has no reach beyond the six windows. Excluding
them costs no frequency coverage, because their finer-channelised siblings
cover the same frequencies in the same blocks. Modelling $q$ for every retained window from its
own band, array and antenna count leaves those residuals unimodal with the six
\SefdResidDefGapDex\,dex below the lowest retained window and nothing between,
so no continuum of smaller deflations hides under the cut.""",
    r"""The exclusion does not rest on the retained population being narrow, since
$q$ runs over a factor ${\sim}290$ of the sample median, mostly the band
dependence the same relation predicts through SEFD. It rests on the size of
the gap and on the direction of the error. The six sit a factor
$1.5\times10^{3}$ below the lowest retained window across an empty 3.2
decades, so any threshold between $1.5\times10^{1}$ and $2.2\times10^{4}$ in
absolute $q$ selects the same six, and modelling $q$ for every retained window
from its own band, array and antenna count leaves the residuals unimodal with
the six \SefdResidDefGapDex\,dex below the lowest retained window and nothing
between. Direction settles the rest: $\sigma$ is estimated from the control
probes and applied to every position of a window alike, so a window-level
deflation can only over-state sensitivity and can never manufacture a
star-exceeds-ring window.

@@PARA@@The six share a signature rather than a programme: all are
\DefectArrays{} array, \NDefectBandSix{} in Band~6 and \NDefectBandSeven{} in
Band~7, all at \DefectChanwMHz\,MHz, in \NDefectEBs{} execution blocks across
\NDefectProjects{} projects, and every one has a normally behaved
finer-channelised window covering the same frequencies in the same block
(Appendix~\ref{app:provenance}). That is a channel-averaged auxiliary window
riding on a frequency-division science baseband, identified from archive
metadata without re-extraction: those windows carry a constant WEIGHT column,
so they never received the science baseband's calibration, and the deflation
is common mode in the data and in the weights alike. Common-mode deflation
leaves the signal-to-noise ratio the search uses untouched, which is why the
defect can misstate a threshold and cannot manufacture a flag, and why
excluding the six costs no frequency coverage at all.""")

# ------------------------------------------------------------------ S6-2
sub(r"""\NDup{} of the \NExtracted{} extracted rows are duplicate catalogue
entries for one physical window, the same (star, execution block,
frequency range, channel width) key appearing twice in the archive query,
either as repeated archive products or as alternative calibrations of one
execution block, so one row per key is the right statistical unit. The retention rule is deterministic and
quantity-independent, the key's first-listed row in the archive query's
own identifier order, so it consults no measured value and cannot prefer
a crossing or a deeper threshold. Repeats need not agree; two reductions of the
same $\tau$~Ceti Band~6 window differ by 44 per cent in threshold, which
exceeds the flux-scale systematic of \S\ref{sec:frames} and is the most direct
empirical bound here on threshold reproducibility. The two HR~1010
Band~6 rows straddle $5\sigma$ at 5.10 and 4.95, so the crossing count is
rule-dependent at the level of one window. The four flagged windows are not,
no discarded row being both a crossing and star-exceeds-ring
(Appendix~\ref{app:exclusions}).""",
    r"""\NDup{} of the \NExtracted{} extracted rows are duplicate catalogue entries
for one physical window, the same (star, execution block, frequency range,
channel width) key appearing twice in the archive query, so one row per key is
the right statistical unit. The retention rule is deterministic and
quantity-independent, the key's first-listed row in the query's own identifier
order, so it consults no measured value and cannot prefer a crossing or a
deeper threshold. Repeats need not agree: two reductions of the same
$\tau$~Ceti Band~6 window differ by 44 per cent in threshold, which exceeds
the flux-scale systematic of \S\ref{sec:frames} and is the most direct
empirical bound here on threshold reproducibility, and the two HR~1010 Band~6
rows straddle $5\sigma$ at 5.10 and 4.95, so the crossing count is
rule-dependent at the level of one window. The four flagged windows are not,
no discarded row being both a crossing and a stage-1 spatial outlier
(Appendix~\ref{app:exclusions}).""")

# ------------------------------------------------------------------ S6-3
sub(r"""Frequency disposes of the catalogue entries. A catalogued transition is
stationary in the observed frame to well within a channel over two hours, and
at zero drift the first-epoch statistic here is only $\CpRecZeroSig\sigma$, so
none can produce this feature. Re-querying the wider catalogues at the
corrected \CpCatFreq\,GHz returns \NCpTube{} entries in the
$\pm50$\,km\,s$^{-1}$ tube. One of them, SO($8_{8}$--$7_{7}$) at
\CpSoFreq\,GHz, is absent from the mask of \S\ref{sec:linecost} and would have
masked the feature had it been present. Such proximity carries no
discriminating power at these frequencies: the same query at each of the
\NCrossQueried{} crossing frequencies returns a catalogued transition within
60\,km\,s$^{-1}$ for \NCrossWithCat{} of them. Width does not contradict the
reading either, the feature occupying one \CpTwoChanwkHz\,kHz channel against
the ${\sim}\CoAssumedDVkms$\,km\,s$^{-1}$ of a belt at \BeltRadiusAu\,au.""",
    r"""Frequency disposes of the catalogue entries. A catalogued transition is
stationary in the observed frame to well within a channel over two hours,
while at zero drift the first-epoch statistic is only $\CpRecZeroSig\sigma$,
so none can produce this feature. Re-querying the wider catalogues at the
corrected \CpCatFreq\,GHz does return \NCpTube{} entries in the
$\pm50$\,km\,s$^{-1}$ tube, one of which would have masked the feature had it
been in the mask of \S\ref{sec:linecost}, but such proximity carries no
discriminating power here: the same query at each of the \NCrossQueried{}
crossing frequencies returns a catalogued transition within 60\,km\,s$^{-1}$
for \NCrossWithCat{} of them.""")

# ------------------------------------------------------------------ S6-4
sub(r"""The \NCensus{} stars are complete against, and conditional only on, the
40-parsec reference catalogue intersected with the public-archive snapshot of
2026 September~8. Against that Gaia~DR3 catalogue of \NGaiaCensus{} stars they
are $\lesssim$1 per cent, and fewer once \S\ref{sec:exclusions} removes those
never in fact observed (Fig.~\ref{fig:funnel}). The two parallax cuts are not
interchangeable, the sample's binding condition being
$\sigma_\varpi/\varpi<\PlxAdqlPct$ per cent against the census's 10 per cent,
so the ratio compares two differently selected populations. The realised
sample is far better than its condition, reaching \PlxWorstPct{} per cent at
worst and exceeding 1 per cent in only \NPlxOverEight{} entries. The census is
incomplete at both ends, so the fraction shows only that coverage is small.""",
    r"""The \NCensus{} stars are complete against, and conditional only on, the
40-parsec reference catalogue intersected with the public-archive snapshot of
2026 September~8. Against that Gaia~DR3 catalogue of \NGaiaCensus{} stars they
are $\lesssim$1 per cent, and fewer once \S\ref{sec:exclusions} removes those
never in fact observed (Fig.~\ref{fig:funnel}). The two parallax cuts are not
interchangeable, the sample's binding condition being
$\sigma_\varpi/\varpi<\PlxAdqlPct$ per cent against the census's 10 per cent,
and the realised sample is better than its condition, reaching
\PlxWorstPct{} per cent at worst. Because the census is incomplete at both
ends, the fraction shows only that coverage is small.""")

# ------------------------------------------------------------------ S6-5
sub(r"""The search, its non-detection and the per-window thresholds come first
(\S\ref{sec:exclusions}, \S\ref{sec:technosearch}), then the four flagged
windows and their dispositions (\S\ref{sec:aumic}), and last the ancillary
by-products, which gate nothing in the primary lane
(\S\ref{sec:ancillaryresults}). The non-detection is stated under two
late-stage corrections, and both made the reported picture more conservative.
The mid-analysis statistic revision (\S\ref{sec:aumic},
Table~\ref{tab:bothstats}) only ever removed flags (seven windows before, four
after, none in which the star dominated its own controls), and withdrawing the
coarse-window 0-of-500 recovery artefact (\S\ref{sec:ancillary}) restored the
recovery of persistent near-static carriers rather than removing a claim.""",
    r"""The search, its non-detection and the per-window thresholds come first
(\S\ref{sec:exclusions}, \S\ref{sec:technosearch}), then the four stage-1
spatial outliers and their dispositions (\S\ref{sec:aumic}), and last the
by-products, which gate nothing (\S\ref{sec:ancillaryresults}). Two late
corrections stand behind the non-detection and both made the picture more
conservative: the mid-analysis statistic revision only ever removed outliers,
seven windows before and four after (\S\ref{sec:aumic},
Table~\ref{tab:bothstats}), and withdrawing the coarse-window 0-of-500
recovery artefact restored a recovery rather than removing a claim.""")

# ------------------------------------------------------------------ S6-6
sub(r"""Useful subsamples still fall out of archival selection without
compromising the archive-target-complete framing, subject to the
unresolved-pair caveat of \S\ref{sec:sample}. \NExoHosts{} of the \NStars{}
processed stars (\NExoPlanets{} known planets) are confirmed exoplanet hosts,
among them Proxima~Centauri, $\tau$~Ceti, $\epsilon$~Eridani, $\beta$~Pictoris
and the seven-planet TRAPPIST-1 system; HN~Lib and LHS~1140, each with a
habitable-zone planet, now carry an ALMA technosignature non-detection. Four
searched stars are white dwarfs \citep{GentileFusillo2021}: Sirius~B,
Van~Maanen's Star, Wolf~219 and CD$-$38~10980, all continuum non-detections
and among the few mm/submm SETI constraints for white dwarfs
\citep{PollutedWD2026}.""",
    r"""Useful subsamples still fall out of archival selection. \NExoHosts{} of the
\NStars{} processed stars (\NExoPlanets{} known planets) are confirmed
exoplanet hosts, among them Proxima~Centauri, $\tau$~Ceti,
$\epsilon$~Eridani, $\beta$~Pictoris and the seven-planet TRAPPIST-1 system,
while HN~Lib and LHS~1140, each with a habitable-zone planet, now carry an
ALMA technosignature non-detection. Four searched stars are white dwarfs
\citep{GentileFusillo2021}, all continuum non-detections and among the few
mm/submm SETI constraints for that class \citep{PollutedWD2026}.""")

# ------------------------------------------------------------------ S6-7
sub(r"""The mask as executed carried four defects, all repaired here and all described
in Appendix~\ref{app:provenance}: rounded rest frequencies, no atomic carbon,
no hydrogen recombination line, and application in the stellar frame alone.
The repaired catalogue holds \MaskNTransNew{} transitions of \MaskNSpecNew{}
species at full JPL/CDMS precision \citep{Pickett1998,CDMS2005} and is applied
in the LSR frame as well as the stellar frame. Re-running the survey was not
affordable, so it is re-applied to the frozen crossing list as a post-hoc
filter. \textbf{No disposition changes.} The masking cost uses one definition: every JPL catalogued transition of
the \MaskNSpecOld{} frozen species (276), displaced by each system's radial velocity,
$\pm50$\,km\,s$^{-1}$ stellar-frame half-width, intersected with each
window and merged. It costs \MaskUnionPct{} per cent of the unique-frequency
union (Table~\ref{tab:searchspace}, Fig.~\ref{fig:waterfall}) and
\MaskGrossPct{} per cent of the window-summed gross bandwidth, the per-window
usable fraction having median 0.960 (10th percentile
0.790). CN and CO dominate the loss, and the per-species, per-band breakdown
ships in the released veto-mask export. Total exposure is
$\ExposureSGHz$\,s\,GHz, or \ExpoTotalSHG{} star-hour-GHz, with
\ExpoTopPct{} per cent of it in the five best-populated 2-GHz bins,
which any frequency-prior calculation must weight
(Appendix~\ref{app:table}). The mask governs dispositions and leaves the noise-derived thresholds alone,
so the quoted EIRP$_{5\sigma}$ values are unchanged; no signal was found
outside the excluded velocity regions in any window.""",
    r"""The mask as executed carried four defects, all repaired here and all
described in Appendix~\ref{app:provenance}: rounded rest frequencies, no
atomic carbon, no hydrogen recombination line, and application in the stellar
frame alone. The repaired catalogue holds \MaskNTransNew{} transitions of
\MaskNSpecNew{} species at full JPL/CDMS precision
\citep{Pickett1998,CDMS2005} and is applied in the LSR frame as well as the
stellar frame. Re-running the survey was not affordable, so it is re-applied
to the frozen crossing list as a post-hoc filter. \textbf{No disposition
changes.} The cost of masking is measured on one definition, every JPL
catalogued transition of the \MaskNSpecOld{} frozen species displaced by each
system's radial velocity, given a $\pm50$\,km\,s$^{-1}$ stellar-frame
half-width, intersected with each window and merged: \MaskUnionPct{} per cent
of the unique-frequency union and \MaskGrossPct{} per cent of the
window-summed gross bandwidth, with CN and CO dominating the loss. Total
exposure is $\ExposureSGHz$\,s\,GHz, or \ExpoTotalSHG{} star-hour-GHz, with
\ExpoTopPct{} per cent of it in the five best-populated 2-GHz bins, which any
frequency-prior calculation must weight (Appendix~\ref{app:table}). The mask
governs dispositions and leaves the noise-derived thresholds alone.""")

fz.apply(TEX, E)
