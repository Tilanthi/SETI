#!/usr/bin/env python3
"""v3.51 stage 1: the restructure, and the cuts that pay for the round.

Both referees ask for the same thing: keep the operative detection pipeline
in the main text and move everything that derives no limit out of it.  This
stage does only that, plus the cuts named in the brief.  No new claim is
made here and no caveat is weakened; the material moved is material the
appendices already carry in full.

  S1-1  Sec. 4.4: the four exploratory diagnostics (closure phase, chirped
        drift, per-channel periodicity, cross-target occupancy) collapse to
        one pointer.  The RFI defences stay in the main text, because RFI
        vetting IS an operative gate in the chain, but are compressed.
  S1-2  Appendix C is renamed to the heading the referees name, and gains
        the one-line statement of what it is for.
  S1-3  Sec. 5.4 ancillary results: compressed, no result dropped.
  S1-4  Sec. 6.4 future work: compressed, all six items kept.
  S1-5  The haystack axis-by-axis paragraph: compressed.
  S1-6  Sec. 5.3 CP-72 2713: the supporting-detail paragraphs compressed
        (the operative argument, the flux comparison, is untouched).
  S1-7  Sec. 2 background: compressed.
  S1-8  Figure widths reduced.  Float geometry, not prose, is what closes
        the last page (measured in v3.50).
"""
import importlib.util
import re
import sys

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------ S1-1
sub(r"""\emph{Closure-phase vetting} (Appendix~\ref{app:closure}). This one-sided
point-source test needs multiple independent baselines, so single-dish and
beamformed surveys cannot perform it. It is implemented and
simulation-validated, and at this survey's flux densities it has
\emph{no discriminating power}: per-baseline S/N never exceeds 5.1 in
the positive-control fields, so no flagged window could have failed it
whatever its nature. It is a proof-of-principle diagnostic and never an operative filter, and no
window is described as having ``survived'' it.

\emph{Extended and cross-target screens}
(Appendices~\ref{app:extended} and \ref{app:freqoccupancy}). Satellite constellations grew across the 2013--2025 archival
baseline. No known ordinary downlink
allocation maps into the searched frequencies, but that excludes neither
harmonics, intermodulation products nor unconventional emitters, and no
exclusion claim rests on allocation alone. The primary defences are the
control ensemble and the time-domain tests. A satellite enters star and
control extractions alike within an integration, the channel-width
mismatch and the drift-stacked statistic dilute transient passes, and a
pass confined to one block and one target would evade the cross-target
occupancy check by construction. A near-field emitter need not share a
celestial source's far-field interferometric response, one reason a
dedicated per-integration RFI screen and visibility-domain checks
belong in any successor analysis. A chirped (quadratic-drift) extension, a per-channel
periodicity search and a cross-target recurrence match at the same sky
frequency all ran as demonstrations only. All
three behave as the null predicts, none produces a candidate and no limit
derives from them; Appendix~\ref{app:extended} gives the rates, the pair
counts and one bookkeeping caveat.""",
    r"""\emph{Interference rejection}, which is an operative gate. Satellite
constellations grew across the 2013--2025 archival baseline, and although no
ordinary downlink allocation maps into the searched frequencies, an allocation
table excludes neither harmonics nor intermodulation products nor
unconventional emitters, so no exclusion claim here rests on one. The defences
that do the work are the control ensemble and the time domain. A satellite
enters the star and the control extractions alike within an integration; the
mismatch between its bandwidth and ours, together with the drift-stacked sum
over the track, dilutes a transient pass; and a second epoch at the same
tuning tests whether anything reproduces. What none of that reaches is a
near-field emitter, whose interferometric response need not resemble a
celestial source's at all, which is one reason a per-integration RFI screen
and a visibility-domain check belong in any successor analysis.

@@PARA@@\emph{Exploratory diagnostics}, which are not part of candidate
selection and are collected in Appendix~\ref{app:closure} under that heading.
Four were run. Closure phase is implemented and simulation-validated, but at
these flux densities it has \emph{no} discriminating power, per-baseline
signal-to-noise never exceeding 5.1 even in the positive-control fields, so no
flagged window could have failed it whatever its nature and none is described
as having survived it. A chirped quadratic-drift extension, a per-channel
periodicity search and a cross-target match of recurring sky frequencies
behave as the null predicts, produce no candidate, and derive no limit.""")

# ------------------------------------------------------------------ S1-2
sub(r"""\section{Ancillary screens with no operative role here}
\label{app:closure}""",
    r"""\section{Exploratory diagnostics not used for candidate selection}
\label{app:closure}

@@PARA@@Nothing in this appendix gates a disposition or derives a limit. Each
screen was run because the data allow it, each is reported whatever it
returned, and the operative chain of \S\ref{sec:technosearch} would read the
same if none had been run.""")

# ------------------------------------------------------------------ S1-3
sub(r"""Two ancillary results are reported in full below; the third ships with
the data.

\emph{Integration-time audit} (machine-readable release). Two of the 58
star--execution-block groups over-count their on-source time against the
archive's own exposure accounting, AT~Mic by a factor 1.43 and
CD$-$38~10980 by 7 per cent, the rest being conservative. No EIRP
threshold depends on integration time, so nothing moves and the
exposure-weighted coverage is at worst optimistic by under 1 per cent
(Appendix~\ref{app:falsealarm}).

\emph{Continuum search} (Appendix~\ref{app:contsearch}). An exploratory by-product over the 57 target/bands processed far enough
for a usable measurement: seventeen $\geq5\sigma$ detections and forty
non-detections reaching 0.036--3.6\,mJy (median 0.52\,mJy). Every
detection is astrophysically unsurprising, the auroral emitter
LSR~J1835$+$3259 meriting deeper follow-up. No technosignature
disposition rests on it.

\emph{Serendipitous molecular-line catalogue} (machine-readable release;
it has no appendix here). The line-exclusion step identifies every
$\geq5\sigma$ outlier channel as a by-product; across the subset scanned,
twelve outlier groups are single- or few-channel features with no
\emph{masked} transition within 300\,MHz and six are plausibly real, all
reported openly. That proximity is measured against the
\MaskNTransNew-transition mask of \S\ref{sec:linecost}, which is what the line-exclusion step compares to, and never against the wider
catalogues. \S\ref{sec:technosearch} shows those lie within 60\,km\,s$^{-1}$ of
\NCrossWithCat{} of the \NCrossQueried{} crossing frequencies.""",
    r"""Three by-products of the search are reported for completeness. None of
them carries a technosignature disposition.

@@PARA@@\emph{Integration-time audit} (machine-readable release). Two of the
58 star--execution-block groups over-count their on-source time against the
archive's own exposure accounting, AT~Mic by a factor 1.43 and CD$-$38~10980
by 7 per cent, the rest being conservative. No EIRP threshold depends on
integration time, so the exposure-weighted coverage is at worst optimistic by
under 1 per cent (Appendix~\ref{app:falsealarm}).

@@PARA@@\emph{Continuum search} (Appendix~\ref{app:contsearch}). Over the 57
target/bands processed far enough for a usable measurement, seventeen
$\geq5\sigma$ detections and forty non-detections reaching 0.036--3.6\,mJy
(median 0.52\,mJy). Every detection is astrophysically unsurprising, the
auroral emitter LSR~J1835$+$3259 meriting deeper follow-up.

@@PARA@@\emph{Serendipitous molecular-line catalogue} (machine-readable
release). The line-exclusion step identifies every $\geq5\sigma$ outlier
channel as a by-product; across the subset scanned, twelve outlier groups are
single- or few-channel features with no \emph{masked} transition within
300\,MHz and six are plausibly real, all reported openly. Proximity there is
measured against the \MaskNTransNew-transition mask of \S\ref{sec:linecost},
never against the wider catalogues.""")

# ------------------------------------------------------------------ S1-4
sub(r"""\emph{Search the blocks already held.} \NUnsearchedEB{} of the
\NProgenitorEB{} public execution blocks in scope were never downloaded
(\S\ref{sec:sample}), and one has since settled this survey's only
unattributed flag (\S\ref{sec:technosearch}). Searching the rest costs no
telescope time and would make a multi-epoch survey of \NStarMoreEB{} stars.
The worked case sets the expectation, its two blocks being repeat executions
of one scheduling block on one night, so such a pair often supplies a baseline
of hours; the distribution of separations is one archive query.""",
    r"""\emph{Search the blocks already held.} \NUnsearchedEB{} of the
\NProgenitorEB{} public execution blocks in scope were never downloaded
(\S\ref{sec:sample}), and searching them costs no telescope time. The
campaign of \S\ref{sec:heldout} has begun that work and continues; completing
it would make a multi-epoch survey of \NStarMoreEB{} stars. One caution
carries over from the worked case, whose two blocks are repeat executions of
a single scheduling block on one night: a second block is often a baseline of
hours rather than of years, and which it is can be settled with one archive
query before any download.""")

sub(r"""\emph{Use the visibilities.} The largest unused advantage is the
interferometric phase itself, which says whether a spectral feature carries
the signature of a celestial point source at a known position. For each
surviving candidate one would compare the likelihoods of a source at the
propagated stellar position, a source elsewhere, common-mode interference and
thermal noise, and evaluate their ratio. That is strictly more powerful than
ranking a peak against a control ensemble, and it would demote the ensemble to
a calibration layer.""",
    r"""\emph{Use the visibilities.} The largest unused advantage is the
interferometric phase itself, which says whether a spectral feature has the
signature of a celestial point source at a known position. Comparing the
likelihoods of a source at the propagated stellar position, a source
elsewhere, common-mode interference and thermal noise is strictly more
powerful than ranking a peak against a control ensemble, and it would demote
the ensemble to a calibration layer.""")

sub(r"""\emph{Retain more control spectra.} The two-stage scheme of
\S\ref{sec:technosearch}, \NCtrl{} controls routinely and a local null
for any window that passes, fails wherever that null cannot be
validated, because full dynamic spectra survive for only \LNNRetained{}
control positions. Retaining all of them, at modest storage cost, would
make the second stage usable in structured fields too.""",
    r"""\emph{Retain more control spectra.} Full dynamic spectra survive for only
\LNNRetained{} of the \NCtrl{} control positions, which is what breaks the
second-stage null in a structured field and what limits the variance test of
\S\ref{sec:rsigma}. Retaining all of them costs storage and nothing else.""")

sub(r"""\emph{A boundary on drift linearity.} The search assumes linear drift over a track. Curvature matters when $\tfrac{1}{2}\ddot\nu T^{2}$
exceeds half a native channel, reached only by the shortest-period
orbits: $P\lesssim1.6$\,d for a typical Class~A window (230\,GHz,
488\,kHz, $T\approx2000$\,s), about an hour for Class~B.
TRAPPIST-1\,b, at $1.51$\,d, sits just inside the boundary and is also
the case that reaches the drift ceiling; elsewhere the constant-drift model
is adequate, and the chirp-search extension
(Appendix~\ref{app:extended}) covers the remainder.""",
    r"""\emph{A boundary on drift linearity.} The search assumes linear drift over
a track, and curvature matters once $\tfrac{1}{2}\ddot\nu T^{2}$ exceeds half
a native channel, which only the shortest-period orbits reach:
$P\lesssim1.6$\,d for a typical Class~A window (230\,GHz, 488\,kHz,
$T\approx2000$\,s). TRAPPIST-1\,b at $1.51$\,d sits just inside that boundary
and is also the case that reaches the drift ceiling.""")

# ------------------------------------------------------------------ S1-5
sub(r"""The survey sits against \citet{Wright2018}'s haystack axis by axis. On
frequency (10\,MHz--115\,GHz) only Band~3 falls inside,
\UnionBandThree{} of 115\,GHz, \UnionBandThreeFrac{} of the axis, where Hz-resolution surveys go finer;
the remaining \UnionBandsFourEight\,GHz (Bands~4--8,
\UnionHiLoGHz--\UnionHiHiGHz\,GHz) lies wholly outside and is new territory. On transmitted bandwidth (0--20\,MHz) a native-channel search probes a
fraction set by channel width (mean 0.63). On sensitivity the
median threshold of Table~\ref{tab:searchspace} detects a
$10^{13}$\,W transmitter only within ${\sim}0.9$\,pc. Against the sole prior
ALMA-archival search \citep[][28 bycatch targets at $\geq$1.01\,kpc,
deepest EIRP$_{\rm min}$ $6.91\times10^{17}$\,W]{Mason2024}, the
\NSystems{} systems here, \NSysInTwentyNow{} inside 20\,pc, reach median
per-target thresholds ${\sim}\MasonRatio\times$ deeper. These fractions
are not combined into one coverage: the axes are strongly coupled,
distance and sensitivity above all, so a product of marginals would
misstate the overlap by orders of magnitude.""",
    r"""The survey sits against \citet{Wright2018}'s haystack axis by axis. On
frequency only Band~3 falls inside that axis's 10\,MHz--115\,GHz span,
\UnionBandThree{} of 115\,GHz, and the remaining \UnionBandsFourEight\,GHz
(Bands~4--8) lies wholly outside it and is new territory. On transmitted
bandwidth a native-channel search probes a fraction set by channel width. On
sensitivity the median threshold detects a $10^{13}$\,W transmitter only
within ${\sim}0.9$\,pc. Against the sole prior ALMA-archival search
\citep[][28 bycatch targets at $\geq$1.01\,kpc]{Mason2024}, the \NSystems{}
systems here reach median per-target thresholds ${\sim}\MasonRatio\times$
deeper. We do not combine these fractions into one coverage number, because
the axes are strongly coupled and a product of marginals would misstate the
overlap by orders of magnitude.""")

# ------------------------------------------------------------------ S1-6
sub(r"""Evidence that framed the flag survives as supporting detail. The feature
is at \FobsCpSeven\,GHz, not the window centre \CpTwoFreqGHz\,GHz quoted in
earlier versions, and channel \EdgeChanMin{} of \CpNChan{} makes
it the most edge-proximate crossing in the survey, \EdgeFracMin{} of the way
into its own window, though edge proximity is common across the survey,
\NPeakOuterThree{} of \NPeakRows{} recorded peak channels falling in the outer
3 per cent of their own. $T_\star$ exceeds the ring maximum by \CpTwoMargin, the smallest margin
\NCtrl{} controls can express, so the margin records a resolution floor alone.""",
    r"""Two details frame the event without bearing on its disposition. It sits in
channel \EdgeChanMin{} of \CpNChan, the most edge-proximate crossing in the
survey, although edge proximity is common here, \NPeakOuterThree{} of
\NPeakRows{} recorded peak channels falling in the outer 3 per cent of their
window. And $T_\star$ exceeds the ring maximum by \CpTwoMargin, which is the
smallest margin \NCtrl{} controls can express, so that margin records a
resolution floor and not a measured contrast.""")

sub(r"""Three further checks find nothing. The star's debris belt, resolved by
\citet{Moor2020} at \BeltRadiusAu\,au, lies six beams from the flagged
window's extraction, so the disc is not the feature. A split-half of the
retained integrations gives $T_\star=\CpSplitLo$ and \CpSplitHi{} against
\CpSplitExp{} expected for a persistent source, so both halves carry it and an
event confined to either one is excluded. The per-integration continuum of
$\CpContMjy\pm\CpContErrMjy$\,mJy would need $\epsilon\approx\CpBandpassEps$
to drive the multiplicative bandpass route of \S\ref{sec:statistic}.""",
    r"""Three further checks find nothing. The star's debris belt, resolved by
\citet{Moor2020} at \BeltRadiusAu\,au, lies six beams from the extraction, so
the disc is not the feature; a split-half of the retained integrations gives
$T_\star=\CpSplitLo$ and \CpSplitHi{} against \CpSplitExp{} expected for a
persistent source, so both halves carry it; and the per-integration continuum
of $\CpContMjy\pm\CpContErrMjy$\,mJy would need
$\epsilon\approx\CpBandpassEps$ to drive the multiplicative bandpass route of
\S\ref{sec:statistic}.""")

# ------------------------------------------------------------------ S1-7
sub(r"""Radio searches, from \citet{CocconiMorrison1959} and
\citet{Drake1960} through the programmes reviewed by
\citet{Tarter2001} and Project Phoenix \citep{Backus2002}, divide into
wide-field commensal and targeted surveys
\citep{Zhang2020,Czech2021,Morrison2023,FAST3IATLAS2025,LOFARdualsite2023,SRT2025,Tremblay2024},
with machine-learning interference rejection now central
\citep{Ma2023,Choza2024,GLOBULAR2025,AnomalyParkesGBT2025,BRaTs2026}, a
capability our classical threshold search lacks. Essentially all of it
lies below ${\sim}10$\,GHz, and the mm/submm regime above has been
searched once, with ALMA \citep{Mason2024}. Physical reasons favour going higher: interstellar scattering and
dispersion fall steeply with frequency, a given aperture delivers a
tighter beam per watt of EIRP, and directional communication, radar and
beamed power are already engineered coherent mm-wave
emission. Atmospheric transmission, receiver noise, photons per watt per
hertz, and pointing and phase stability raise the cost of such a search
without forbidding it.""",
    r"""Radio searches, from \citet{CocconiMorrison1959} and \citet{Drake1960}
through the programmes reviewed by \citet{Tarter2001} and Project Phoenix
\citep{Backus2002}, divide into wide-field commensal and targeted surveys
\citep{Zhang2020,Czech2021,Morrison2023,FAST3IATLAS2025,LOFARdualsite2023,SRT2025,Tremblay2024},
with machine-learning interference rejection now central
\citep{Ma2023,Choza2024,GLOBULAR2025,AnomalyParkesGBT2025,BRaTs2026}, a
capability our classical threshold search lacks. Essentially all of that work
lies below ${\sim}10$\,GHz, and the millimetre regime above it has been
searched once, with ALMA \citep{Mason2024}. There are physical reasons to go
higher, since interstellar scattering and dispersion fall steeply with
frequency, a given aperture delivers a tighter beam per watt of EIRP, and
directional communication, radar and beamed power are already engineered as
coherent mm-wave emission. Atmospheric transmission, receiver noise, photons
per watt per hertz, and pointing and phase stability raise the cost of such a
search without forbidding it.""")

fz.apply(TEX, E)

# ------------------------------------------------------------------ S1-8
# Float geometry.  Measured in v3.50: prose cuts stop propagating once a
# region is float-packed, and figure size is what moves the page count then.
src = open(TEX, encoding='utf-8').read()
GEOM = [
    ('includegraphics[width=0.99\\textwidth]{figures/selection_funnel.pdf}',
     'includegraphics[width=0.94\\textwidth]{figures/selection_funnel.pdf}'),
    ('includegraphics[width=0.72\\textwidth]{figures/coverage_waterfall.pdf}',
     'includegraphics[width=0.66\\textwidth]{figures/coverage_waterfall.pdf}'),
    ('includegraphics[width=0.94\\columnwidth]{figures/eirp_context.pdf}',
     'includegraphics[width=0.90\\columnwidth]{figures/eirp_context.pdf}'),
    ('includegraphics[width=0.90\\columnwidth]{figures/control_diagnostics.pdf}',
     'includegraphics[width=0.84\\columnwidth]{figures/control_diagnostics.pdf}'),
]
for a, b in GEOM:
    if src.count(a) != 1:
        raise SystemExit('figure anchor not unique: %s' % a)
    src = src.replace(a, b)
open(TEX, 'w', encoding='utf-8').write(src)
print('figure widths: %d reduced' % len(GEOM))
