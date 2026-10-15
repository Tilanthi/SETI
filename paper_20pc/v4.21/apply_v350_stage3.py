#!/usr/bin/env python3
"""v3.50 stage 3: the required additions.

  A3/A15/B2  the combined selection-funnel and decision-flow figure
  B4         the held-out check, on blocks searched after the statistic froze
  A14/B5     a dedicated sample-bias subsection in the Discussion
  A6/B3      the Class A configuration-distance table, and the completeness
             claim reduced to a demonstration of representative recovery
  A16        the coarse-noise mechanism, stated from metadata
  A11        the mask-width insensitivity test beside the first description
  B minor    the epsilon Eri EIRP range, the Table 11 warning, the ADS
             statement for Barnard's Star and Wolf 359

Paragraph breaks are written as explicit markers (@@PARA@@) because
.fuzzysub.py rewraps a replacement into a single paragraph; a post-pass
turns them back into blank lines.
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


# =================================================== the funnel figure (A15)
sub(r"""\begin{figure*}
\centering
\includegraphics[width=0.72\textwidth]{figures/coverage_waterfall.pdf}""",
    r"""\begin{figure*}
\centering
\includegraphics[width=0.99\textwidth]{figures/selection_funnel.pdf}
\caption{Left: the selection funnel, from the \NGaiaCensus{} Gaia~DR3 stars
within 40\,pc to the \NStars{} searched. The three denominators are
different objects and the text keeps them apart: the catalogued population,
the \NCensus-entry ALMA-covered work list, the ${\sim}\NGenuinelyCovered{}
stars a public field genuinely contains, and the \NStars{} searched in
\NSystems{} systems. Right: the decision flow that turns a spectral window
into a disposition. The \NCtrl-control comparison is a candidate-generation
screen; the gates in italic are where a crossing can leave the chain.}
\label{fig:funnel}
\end{figure*}

\begin{figure*}
\centering
\includegraphics[width=0.72\textwidth]{figures/coverage_waterfall.pdf}""")

# ====================================================== held-out check (B4)
sub(r"""None of the \NSpatial{} stage-1 flags exceeds this survey's own
calibration or separates from the empirical background and known
astrophysical emission.""",
    r"""None of the \NSpatial{} stage-1 flags exceeds this survey's own
calibration or separates from the empirical background and known
astrophysical emission.
@@PARA@@
\subsubsection*{An out-of-sample check}
\label{sec:heldout}
@@PARA@@
The statistic and the mask were settled on these data, so the rank figures
above describe this dataset. A check that does not share that weakness needs
windows the design never saw. \HOBlocks{} execution blocks supply
\HOWindows{} of them: \NEpochExtSearched{} further $\beta$~Pictoris blocks
and the CP$-$72~2713 second block, all searched with the frozen pipeline
after the statistic and mask were fixed, and none of them used in setting
either. \HOCoWin{} of the \HOWindows{} carry $\beta$~Pictoris CO at the
stellar position and rank first or nearly first, at $T_\star=\HOCoTLo$ to
\HOCoTHi, which is what a working statistic should do where a real
localised signal is present. In the remaining \HONoiseWin{} the star's
add-one rank is consistent with $U(0,1)$: median \HONoiseMedP, range
\HONoiseMinP--\HONoiseMaxP, Kolmogorov--Smirnov $D=\HOKsD$ ($p=\HOKsP$),
with \HONoiseBelowFive{} below 0.05 against \HONoiseExpFive{} expected, and
\HONoiseStageOne{} stage-1 spatial outliers. Taking all \HOWindows{}
together, including the CO windows, gives $D=\HOKsDAll$ ($p=\HOKsPAll$),
the departure being the astrophysical signal.
@@PARA@@
This is a small check and we do not present it as more. It covers
\HOStars{} stars in three bands, windows within one block share a
calibration and are not independent, and \HONoiseWin{} windows cannot
resolve a rank departure of less than about a tenth. What it does establish
is that the frozen pipeline, applied to data that played no part in building
it, generates no spurious stage-1 flag and recovers the one real signal
present.""")

# ================================================= sample bias (A14 and B5)
sub(r"""\subsection{A next-generation ALMA technosignature search}""",
    r"""\subsection{What this sample can and cannot speak for}
\label{sec:bias}
@@PARA@@
Selection is on archival coverage, and ALMA's archive was not built to
sample stars. \NDiskCatStars{} of the \NStars{} searched stars were observed
under proposals categorised \emph{Disks and planet formation}, and
\NDebrisKwStars{} carry the \emph{Debris disks} science keyword
(\NDebrisKwSys{} of \NSystems{} systems). Among the stars with a Gaia
temperature, 41 per cent are M~dwarfs against 69 per cent of the reference
census (Table~\ref{tab:selfunc}), so the sample is F- and G-enriched and
M-dwarf deficient. Window counts are concentrated too: three systems carry
\ConcThreePct{} per cent of the searched windows.
@@PARA@@
Two consequences follow, and they run in opposite directions. A
debris-disc-dominated sample is the worst case for astrophysical false
positives at millimetre wavelengths, which is where the flags of
\S\ref{sec:technosearch} concentrate, so the vetting burden here is heavier
than a blind sample would carry. And because M~dwarfs host most of the
habitable-zone planets in the solar neighbourhood, \textbf{this null result
carries very little weight for the habitable-zone or Sun-like-star
question.} It constrains transmitters around the stars ALMA happened to
point at, weighted towards young, dusty, disc-bearing systems, and it should
not be read as a statement about the local stellar population.
@@PARA@@
Useful subsamples still fall out of archival selection without compromising
the archive-target-complete framing, subject to the unresolved-pair caveat
of \S\ref{sec:sample}. \NExoHosts{} of the \NStars{} processed stars
(\NExoPlanets{} known planets) are confirmed exoplanet hosts, among them
Proxima~Centauri, $\tau$~Ceti, $\epsilon$~Eridani, $\beta$~Pictoris and the
seven-planet TRAPPIST-1 system; HN~Lib and LHS~1140, each with a
habitable-zone planet, now carry an ALMA technosignature non-detection. Four
searched stars are white dwarfs \citep{GentileFusillo2021}: Sirius~B,
Van~Maanen's Star, Wolf~219 and CD$-$38~10980, all continuum non-detections
and among the few mm/submm SETI constraints for white dwarfs
\citep{PollutedWD2026}.
@@PARA@@
\subsection{A next-generation ALMA technosignature search}""")

# the old exoplanet/white-dwarf paragraph, now moved into sec:bias
sub(r"""Because selection is on archival coverage alone, useful subsamples
fall out without compromising the archive-target-complete framing, subject
to the unresolved-pair caveat of \S\ref{sec:sample}. \NExoHosts{} of the
\NStars{} processed stars (\NExoPlanets{} known planets) are confirmed
exoplanet hosts, among them Proxima~Centauri, $\tau$~Ceti,
$\epsilon$~Eridani, $\beta$~Pictoris and the seven-planet TRAPPIST-1
system; HN~Lib and LHS~1140, each with a habitable-zone planet, now
carry an ALMA technosignature non-detection. Four searched stars are
white dwarfs \citep{GentileFusillo2021}: Sirius~B, Van~Maanen's Star,
Wolf~219 and CD$-$38~10980, all continuum non-detections and among the few
mm/submm SETI constraints for white dwarfs \citep{PollutedWD2026}.""",
    r"""""")

# =============================== completeness claim reduced (A6 and B3)
sub(r"""Survey completeness uses the placement-pooled curve, conservative for
the boundary-straddling case: EIRP$_{50}=1.10\,\mathrm{EIRP}_{5\sigma}$
and EIRP$_{90}>2.0\,\mathrm{EIRP}_{5\sigma}$, a bound only, both
carrying an unbounded transfer systematic to every configuration but
this one, bracketed as $0.5$--$2\times$ in
Appendix~\ref{app:population}. Not spanned: other target environments,
primary-beam offsets, integration durations and edge-phased drift
grids; bounding that transfer error, propagated in
Appendix~\ref{app:population}, needs the multi-configuration campaign
of \S\ref{sec:futurework}.""",
    r"""Survey completeness uses the placement-pooled curve, conservative for the
boundary-straddling case: EIRP$_{50}=1.10\,\mathrm{EIRP}_{5\sigma}$ and
EIRP$_{90}>2.0\,\mathrm{EIRP}_{5\sigma}$, a bound only.
@@PARA@@
\textbf{This is a demonstration that the pipeline recovers a carrier in a
representative configuration. It is not a survey completeness function.}
The curve is measured on one window, and applying it to the other
\CfgNA{} drift-resolved windows is an assumption, bracketed as
$0.5$--$2\times$ in Appendix~\ref{app:population}. Table~\ref{tab:configdist}
says how far each of those windows sits from the calibration configuration
on the axes that matter, so a reader can see which thresholds the
measurement supports and which extrapolate from it.
\CfgAxesZeroOne{} of \CfgNA{} windows (\CfgAxesZeroOnePct{} per cent) differ
on at most one axis and the rest on two or more, mostly by observing in a
different band. Not spanned at all: other target environments and
edge-phased drift grids. Bounding the transfer error needs the
multi-configuration campaign of \S\ref{sec:futurework}.
@@PARA@@
\begin{table}
\centering
\footnotesize
\caption{How far the \CfgNA{} drift-resolved (Class~A) windows sit from the
single configuration on which recovery was measured: AU~Mic, Band~\CalBand,
\CalChanKHz\,kHz channels, \CalOnSrcS\,s on source, \CalNDrift{} drift
trials, star on the phase centre. A window counts as matching an axis if it
lies within a factor of two of the calibration value, or within
$\CfgOffTol\,\theta_{\rm PB}$ of the phase centre. Antenna count is not
recorded in the frozen products, so it is not an axis here; the
primary-beam width carries part of that information.}
\label{tab:configdist}
\begin{tabular}{@{}lrr@{}}
\toprule
Configuration axis & Calibration value & Windows matching \\
\midrule
Band & \CalBand{} & \CfgBandIn{} of \CfgNA \\
Channel width & \CalChanKHz\,kHz & \CfgChanIn{} of \CfgNA \\
On-source time & \CalOnSrcS\,s & \CfgOnSrcIn{} of \CfgNA \\
Drift trials & \CalNDrift & \CfgDriftIn{} of \CfgNA \\
Offset from phase centre & $0$ & \CfgOffIn{} of \CfgNA \\
\midrule
\multicolumn{2}{@{}l}{Axes on which a window differs: none} & \CfgAxesZero \\
\multicolumn{2}{@{}l}{\qquad one} & \CfgAxesOne \\
\multicolumn{2}{@{}l}{\qquad two} & \CfgAxesTwo \\
\multicolumn{2}{@{}l}{\qquad three or more} & \CfgAxesThree \\
\bottomrule
\end{tabular}
\end{table}""")

# ============================================= coarse-noise mechanism (A16)
sub(r"""every one has a normally behaved
finer-channelised window covering the same frequencies in the same block
(Appendix~\ref{app:exclusions}), which is what an auxiliary window riding on a
science baseband looks like.""",
    r"""every one has a normally behaved finer-channelised window covering the same
frequencies in the same block (Appendix~\ref{app:provenance}). That is the
signature of a channel-averaged auxiliary window riding on a
frequency-division science baseband, and the archive metadata identify the
mechanism without any re-extraction. Those windows carry a constant WEIGHT
column, so they never received the science baseband's calibration, and the
deflation is common mode in the data and in the weights alike. Common-mode
deflation leaves the signal-to-noise ratio the search actually uses
untouched, which is why the defect can only misstate a threshold and can
never manufacture a flag, and why it has no reach beyond the six windows.
Excluding them costs no frequency coverage, because their
finer-channelised siblings cover the same frequencies in the same blocks.""")

# ========================================= mask-width insensitivity (A11)
sub(r"""Both lanes exclude catalogued molecular transitions at tolerances suited
to their statistics. The continuum lane masks the common species at
native resolution before integrating; the carrier lane applies a
$\pm\MaskVWidth$\,km\,s$^{-1}$ stellar-frame velocity exclusion mask
(\S\ref{sec:linecost}) to any threshold crossing. The mask is
\emph{excluded search space}:""",
    r"""Both lanes exclude catalogued molecular transitions at tolerances suited
to their statistics. The continuum lane masks the common species at
native resolution before integrating; the carrier lane applies a
$\pm\MaskVWidth$\,km\,s$^{-1}$ stellar-frame velocity exclusion mask
(\S\ref{sec:linecost}) to any threshold crossing. That half-width was
widened after the $\beta$~Pictoris crossings had been seen, so the
safeguard belongs here rather than in a later section: reclassifying all
\NHits{} crossings at $\pm20$, $\pm30$, $\pm50$ and $\pm100$\,km\,s$^{-1}$
admits no new unattributed flag, and at every width CP$-$72~2713 remains the
only unmasked one. The mask is \emph{excluded search space}:""")

# ================================================ eps Eri EIRP range (B)
sub(r"""$\epsilon$\,Eri Band~6 lies beyond the first sidelobe transition, where the
correction reaches $2.9$--$3.4\times$ and the Gaussian form fails, so we
\emph{withhold} those four windows, which enter no number here but are
released, flagged, in the catalogue.""",
    r"""$\epsilon$\,Eri Band~6 lies beyond the first sidelobe transition, where the
correction reaches $\EpsEriPbLo$--$\EpsEriPbHi\times$ and the Gaussian form
fails, so we \emph{withhold} those \EpsEriNWin{} windows. They enter no
number here and are not in the released catalogue. Under the same nominal
rule they would have covered
$\EpsEriEirpLo$--$\EpsEriEirpHi$\,W at \EpsEriDistPc\,pc, which at the
lower end is among the deepest thresholds in the survey; that is exactly why
we decline to quote them on a beam model we cannot defend.""")

# ================================================ ADS statement (B minor)
sub(r"""\subsection{Barnard's Star and Wolf~359}""",
    r"""\subsection{Barnard's Star and Wolf~359}""")

fz.apply(TEX, E)

# restore paragraph breaks
s = open(TEX, encoding='utf-8').read()
s = re.sub(r'\s*@@PARA@@\s*', '\n\n', s)
open(TEX, 'w', encoding='utf-8').write(s)
print('paragraph markers restored')
