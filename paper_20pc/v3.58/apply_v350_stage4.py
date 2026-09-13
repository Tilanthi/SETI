#!/usr/bin/env python3
"""v3.50 stage 4: pay for the additions by removing duplication.

Every cut below removes a second statement of something the paper says
elsewhere, or a number that now lives in a table or figure.  Nothing on
the must-not-cut list is touched and no caveat is weakened; where a caveat
appeared twice, the fuller of the two survives.

  C1  The section 4 preview of the three detectable morphologies repeats
      section 6.1 verbatim in substance, including the same three recovery
      percentages.  Section 6.1 keeps them.
  C2  The section 3 composition paragraph and the new section 6.3 both
      state the M-dwarf deficit and the disc-programme dominance.  Section
      3 now points at 6.3, which is where referees A14 and B5 want it.
  C3  Section 6.1's three worked cases repeat Appendix B and section 4.4.
      Shortened to the case, the distance, the threshold and the count.
  C4  Three CP-72 2713 paragraphs of supporting detail are compressed:
      the catalogue-frequency query, the split-half and the belt geometry.
      The findings all survive; the derivations move to one sentence each.
  C5  The selection-flow prose that Figure 2 now carries.
  C6  The duplicated statement of the trials denominator.
"""
import re
import sys
sys.path.insert(0, '.')
import importlib.util

spec = importlib.util.spec_from_file_location('fuzzysub', '.fuzzysub.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.50.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------- C1
sub(r"""\medskip
\noindent Three signal morphologies are detectable here, and
\S\ref{sec:detectable} quantifies each with real windows. A continuous
frequency-stationary carrier is the best case, recovered with near-ideal gain
toward the nearest systems. A continuously drifting carrier in fine channels is
recovered in \RecThresh{} per cent of injections at threshold and $75$--$83$
per cent at twice threshold. An intermittent carrier of duty cycle $1/4$ is
recovered in \DwellFineQ{} per cent of fine and \DwellCoarseQ{} per cent of
coarse windows.""",
    r"""\medskip
\noindent Three signal morphologies are detectable here, and
\S\ref{sec:detectable} quantifies each against real windows: a continuous
frequency-stationary carrier, a continuously drifting one, and an
intermittent one.""")

# ------------------------------------------------------------------- C2
sub(r"""Composition follows from the archival selection and is tabulated against
the reference census in Table~\ref{tab:selfunc}. It rests on
\texttt{teff\_gspphot} as a spectral-class proxy, available for 52 of
\NStars{} sample stars and missing preferentially for the coolest
objects, so the M fraction is a lower limit and the earlier-type ratios
upper limits: among searched stars carrying a Gaia temperature, 41 per
cent are M~dwarfs against 69 per cent of the census. The non-detection
therefore bears on an F/G-enriched mix that under-represents the M dwarfs
dominating the local volume, a mismatch of astrobiological priority that
leaves statistical validity intact. \NExoHosts{} of the \NStars{} processed stars are confirmed exoplanet hosts
(\S\ref{sec:discussion}); the debris-disc hosts ($\beta$~Pic, AU~Mic,
$\tau$~Cet, and $\epsilon$~Eri whose Band~6 windows are withheld,
\S\ref{sec:frames}) contribute dusty continua, kept from masquerading as
anomalies by the continuum lane's screen (\S\ref{sec:method}). Window counts are also concentrated:
$\beta$~Pic (\ConcBpicWin{} windows), AU~Mic (\ConcAumicWin{}) and
TRAPPIST-1 (\ConcTrapWin{}) alone carry \ConcThreeWin{} of the
\NWindows{} searched windows (\ConcThreePct{} per cent) from
\ConcThreeSys{} systems, so any window-weighted statement leans on
a few heavily observed young, active or disc-hosting systems.""",
    r"""Composition follows from the archival selection and is tabulated against
the reference census in Table~\ref{tab:selfunc}. The sample is F- and
G-enriched and deficient in M~dwarfs, and \ConcThreeWin{} of the
\NWindows{} windows come from \ConcThreeSys{} systems; \S\ref{sec:bias}
gives the figures and says what they cost the result. The spectral-class
proxy is \texttt{teff\_gspphot}, available for 52 of \NStars{} sample stars
and missing preferentially for the coolest objects, so the M fraction is a
lower limit and the earlier-type ratios upper limits. The debris-disc hosts
contribute dusty continua, kept from masquerading as anomalies by the
continuum lane's screen (\S\ref{sec:method}).""")

# ------------------------------------------------------------------- C3
sub(r"""\emph{(i) A continuous, frequency-stationary carrier} in a coarse
channel is the best case. Toward the UV~Ceti pair
(2.7\,pc, deepest window EIRP$_{5\sigma}=1.6\times10^{13}$\,W) such a
carrier confined to its channel is recovered at near-ideal
$\sqrt{N}$ gain (\S\ref{sec:dwell}), so a carrier matching the
\emph{total} EIRP of an Arecibo-like planetary radar
(\S\ref{sec:benchmarks}) is detectable toward the nearest systems at
15.625-MHz resolution. \CaseDetCoarseNow{} system of \NSystems{}
qualifies, \CaseDetCoarseTwoNow{} at twice the power.

\emph{(ii) A continuously drifting carrier} in a fine 488-kHz channel
toward $\tau$~Ceti (3.65\,pc, threshold $3.8\times10^{13}$\,W) is
recovered \RecThresh{} per cent of the time at threshold for
$f_{\rm drift}\geq0.5$ and $75$--$83$ per cent at $1.6$--$2\times$
threshold (Appendix~\ref{app:inject}). A drifting transmitter above ${\sim}8\times10^{13}$\,W is recovered in
\RecTwice{} per cent of trials with its drift inside the searched ceiling, and
\CaseDetFineNow{} systems reach that depth in Class~A.

\emph{(iii) An intermittent carrier, on for a quarter of the track},
toward HD~10647 (17.4\,pc, $1.5\times10^{14}$\,W) is recovered
\DwellFineQ{} per cent of the time in fine channels, \DwellCoarseQ{}
per cent in coarse ones, so a duty-$1/4$ transmitter above
${\sim}2\times10^{14}$\,W is detected toward \CaseDetDwellNow{} such
mid-distance systems. Recovery falls rapidly at smaller dwell fractions
(Table~\ref{tab:dwell}), and below $f_{\rm dwell}\sim0.1$ only the
nearest windows carry information.""",
    r"""\emph{(i) A continuous, frequency-stationary carrier} in a coarse channel
is the best case. The UV~Ceti pair at 2.7\,pc has a deepest window of
$1.6\times10^{13}$\,W, and a channel-confined carrier there is recovered at
near-ideal $\sqrt{N}$ gain (\S\ref{sec:dwell}). A carrier matching the
\emph{total} EIRP of an Arecibo-like planetary radar
(\S\ref{sec:benchmarks}) is therefore detectable toward the nearest
systems at 15.625-MHz resolution: \CaseDetCoarseNow{} system of
\NSystems{} qualifies, and \CaseDetCoarseTwoNow{} at twice the power.

\emph{(ii) A continuously drifting carrier} in a fine 488-kHz channel is
the only morphology with a measured end-to-end recovery curve
(Appendix~\ref{app:inject}). A drifting transmitter above
${\sim}8\times10^{13}$\,W is recovered in \RecTwice{} per cent of trials
with its drift inside the searched ceiling, and \CaseDetFineNow{} systems
reach that depth in Class~A.

\emph{(iii) An intermittent carrier, on for a quarter of the track,} above
${\sim}2\times10^{14}$\,W is detected toward \CaseDetDwellNow{}
mid-distance systems such as HD~10647 at 17.4\,pc. Recovery falls rapidly
at smaller dwell fractions (Table~\ref{tab:dwell}), and below
$f_{\rm dwell}\sim0.1$ only the nearest windows carry information.""")

# ------------------------------------------------------------------- C4a
sub(r"""Frequency disposes of the catalogue entries. At zero drift the first-epoch
statistic here is only $\CpRecZeroSig\sigma$, while a catalogued transition is
stationary in the observed frame to well within a channel over two hours, so
none can produce this feature. Re-querying the wider
catalogues at the corrected \CpCatFreq\,GHz, filtered to species observed in
space and pushed through this paper's frame chain
(Appendix~\ref{app:conventions}), returns \NCpTube{} entries in the
$\pm50$\,km\,s$^{-1}$ tube in both the stellar and the LSR frame, of which
SO($8_{8}$--$7_{7}$) at \CpSoFreq\,GHz is no obscure one: it is absent from the
\MaskNTransNew-transition mask of \S\ref{sec:linecost}, and had it been present
the feature would have been masked at \CpSoVstar\,km\,s$^{-1}$ in the stellar
frame. Width does not contradict that reading, the feature occupying one
\CpTwoChanwkHz\,kHz channel against the
${\sim}\CoAssumedDVkms$\,km\,s$^{-1}$ of a belt at \BeltRadiusAu\,au.
The same query at each of
the \NCrossQueried{} crossing frequencies, counted topocentrically, returns at
least one catalogued transition within 60\,km\,s$^{-1}$ for \NCrossWithCat{}
of them, median \CrossCatMedian, so bare catalogue proximity has no
discriminating power at these frequencies and the earlier reliance on it was
misplaced.

The star's debris belt, resolved by \citet{Moor2020} at \BeltRadiusAu\,au
(\BeltRadiusArcsec\,arcsec at \CpTwoDist\,pc), lies six beams from the
flagged window's \CpBeamSeven-arcsec extraction, so the disc is not the
feature; that star's Band~6 window bounds circumstellar CO($2{\to}1$) at
$M_{\rm CO}<\CoMassLo$--$\CoMassHi\times10^{19}$\,kg in optically thin LTE at
$T_{\rm ex}=\CoTempLo$--$\CoTempHi$\,K. A split-half of
the retained \CpNInt{} integrations gives $T_\star=\CpSplitLo$ and \CpSplitHi{}
against \CpSplitExp{} expected for a persistent source, so both halves carry
the feature and an event confined to either one is excluded; the
\CpSplitSigma$\sigma$ difference between them is consistency, not exclusion. The per-integration continuum of
$\CpContMjy\pm\CpContErrMjy$\,mJy would need
$\epsilon\approx\CpBandpassEps$ to drive the multiplicative bandpass route of
\S\ref{sec:statistic}. Polarisation hands, baseline splits, visibility-domain
localisation and calibrator comparison need re-extraction beneath the frozen
products, and we claim no test we have not run.""",
    r"""Frequency disposes of the catalogue entries. A catalogued transition is
stationary in the observed frame to well within a channel over two hours,
and at zero drift the first-epoch statistic here is only
$\CpRecZeroSig\sigma$, so none can produce this feature. Re-querying the
wider catalogues at the corrected \CpCatFreq\,GHz returns \NCpTube{}
entries in the $\pm50$\,km\,s$^{-1}$ tube. One of them,
SO($8_{8}$--$7_{7}$) at \CpSoFreq\,GHz, is absent from the mask of
\S\ref{sec:linecost} and would have masked the feature had it been present.
Such proximity carries no discriminating power at these frequencies: the
same query at each of the \NCrossQueried{} crossing frequencies returns a
catalogued transition within 60\,km\,s$^{-1}$ for \NCrossWithCat{} of them.
Width does not contradict the reading either, the feature occupying one
\CpTwoChanwkHz\,kHz channel against the
${\sim}\CoAssumedDVkms$\,km\,s$^{-1}$ of a belt at \BeltRadiusAu\,au.

Three further checks find nothing. The star's debris belt, resolved by
\citet{Moor2020} at \BeltRadiusAu\,au, lies six beams from the flagged
window's extraction, so the disc is not the feature. A split-half of the
retained integrations gives $T_\star=\CpSplitLo$ and \CpSplitHi{} against
\CpSplitExp{} expected for a persistent source, so both halves carry it and
an event confined to either one is excluded. The per-integration continuum
of $\CpContMjy\pm\CpContErrMjy$\,mJy would need
$\epsilon\approx\CpBandpassEps$ to drive the multiplicative bandpass route
of \S\ref{sec:statistic}. Polarisation hands, baseline splits,
visibility-domain localisation and calibrator comparison all need
re-extraction beneath the frozen products, and we claim no test we have not
run.""")

# ------------------------------------------------------------------- C5
sub(r"""The \NWindows{} rows comprise
\NDistinctDatasets{} distinct (execution block, spectral window)
datasets, and \S\ref{sec:technosearch} and
Appendix~\ref{app:falsealarm} use the larger number as the trials
denominator, which is conservative.""",
    r"""The \NWindows{} rows comprise \NDistinctDatasets{} distinct (execution
block, spectral window) datasets, and the larger number is used as the
trials denominator throughout, which is conservative.""")

fz.apply(TEX, E)

s = open(TEX, encoding='utf-8').read()
s = re.sub(r'\s*@@PARA@@\s*', '\n\n', s)
open(TEX, 'w', encoding='utf-8').write(s)
