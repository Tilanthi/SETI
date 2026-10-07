#!/usr/bin/env python3
"""v3.50 stage 8: the last 0.5 page, from the two appendices whose own
text says they are illustrative.

Appendix J is an explicitly illustrative framework and Appendix B's
opening restates the transfer caveat that now has its own table.  Neither
loses a result.  The long selection-function caption gives back to
Table~10's own columns what it was repeating in prose.
"""
import re
import sys
sys.path.insert(0, '.')
import importlib.util

spec = importlib.util.spec_from_file_location('fuzzysub', '.fuzzysub.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------ app:inject
sub(r"""To test whether a $5\sigma$ threshold behaves as idealised Gaussian
noise predicts, we inject synthetic tones of known amplitude into real
visibilities, through the extraction code's own mechanism and as far
upstream of the statistic as retained products allow, and measure what
the unmodified pipeline returns. Three results inherit its
single-configuration limitation: the drifting-class recovery of
Appendix~\ref{app:population}, the machinery and boundary-placement
amplitude factors of \S\ref{sec:ancillary}, and the coarse-window dwell
reading of \S\ref{sec:dwell}.

Six configurations span three bands and both classes: three
coarse Band~7 spws of AT~Mic, one coarse spw each in Bands~3 and~6 of
AU~Mic, and AU~Mic's 488-kHz flagband window with its 49-trial drift
grid. Each receives a complex tone at the star position, at amplitudes
$4$--$10\times$ the statistic's own noise, drift fractions
$f_{\rm drift}=0$, $0.25$, $0.5$, $0.75$, $1.0$ of the ceiling, on- and
half-grid rates, and channel-centred and boundary placements:
200 trials per configuration, \NTrials{} in all, under a frozen
criterion ($T\geq5$, peak channel within 3 of the injection, peak drift
within one grid step).""",
    r"""To test whether a $5\sigma$ threshold behaves as idealised Gaussian noise
predicts, we inject synthetic tones of known amplitude into real
visibilities and measure what the unmodified pipeline returns. The
injection uses the extraction code's own mechanism, as far upstream of the
statistic as the retained products allow.

Six configurations span three bands and both classes: three coarse Band~7
spectral windows of AT~Mic, one coarse window each in Bands~3 and~6 of
AU~Mic, and AU~Mic's 488-kHz flagband window with its 49-trial drift grid.
Each receives a complex tone at the star position at amplitudes
$4$--$10\times$ the statistic's own noise. The grid covers drift fractions
$f_{\rm drift}=0$ to $1.0$ of the ceiling, on- and half-grid rates, and
channel-centred and boundary placements, 200 trials per configuration and
\NTrials{} in all. The recovery criterion was frozen in advance: $T\geq5$,
peak channel within 3 of the injection, peak drift within one grid step.""")

sub(r"""The coarse-window variant recovered 0 of 500 injections at every
amplitude from $4\sigma$ to $10\sigma$ under that criterion. The recovery
criterion produced that artefact and the pipeline suppresses nothing, which
makes it the one withdrawn result here: the drift-matching clause cannot be satisfied
on coarse windows, where every in-grid drift is sub-channel over the
track, so the reported peak drift is arbitrary. Scored on detection
alone the same windows recover essentially everything, and an end-to-end
injection through the released pipeline
returns $T_\star$ of 20.5, 65.3 and 217.7 at 1, 3 and 10 times the
per-integration noise, against an ideal coherent gain of
$\sqrt{639}=25$. Class~B limits therefore bound carriers of any dwell
fraction, with the completeness of \S\ref{sec:dwell}; what those windows
lack is drift discrimination. The fine window fails the same criterion
the same way, and that cell is unmeasured, since carriers with
$f_{\rm drift}\leq0.25$ dwell ${\geq}40$ per cent of the track per
channel and fail it, while those with $f_{\rm drift}\geq0.5$ survive as the
searched class.""",
    r"""The coarse-window variant recovered 0 of 500 injections at every amplitude
from $4\sigma$ to $10\sigma$ under that criterion. The criterion produced
that artefact and the pipeline suppresses nothing, which makes it the one
withdrawn result here. The drift-matching clause cannot be satisfied on
coarse windows, where every in-grid drift is sub-channel over the track, so
the reported peak drift is arbitrary. Scored on detection alone the same
windows recover essentially everything: an end-to-end injection through the
released pipeline returns $T_\star$ of 20.5, 65.3 and 217.7 at 1, 3 and 10
times the per-integration noise, against an ideal coherent gain of
$\sqrt{639}=25$. Class~B limits therefore bound carriers of any dwell
fraction, with the completeness of \S\ref{sec:dwell}, and what those
windows lack is drift discrimination. The fine window fails the same
criterion the same way, so the near-static cell there is unmeasured.""")

# --------------------------------------------------------- app:population
sub(r"""No number here appears among the headline quantities of
Table~\ref{tab:searchspace}; the appendix is kept for the framework. A zero
detection constrains a fraction of systems only through a per-system
probability, factorised as""",
    r"""No number here appears among the headline quantities of the paper, and the
appendix is kept for the framework alone. \textbf{The fraction below is
conditional on the searched frequencies, epochs and morphology, and quoting
it outside that conditioning would misstate it by orders of magnitude.} A
zero detection constrains a fraction of systems only through a per-system
probability, factorised as""")

sub(r"""Everything below sets $F_i=D_i=1$ \emph{by conditioning, not by
measurement}. At EIRP
$\geq10^{16}$\,W the measured form gives
$f_{95}\approx\OccMeasuredRound$ per cent over the \NOccSystems{}
systems carrying a Class~A window, with idealised brackets \OccUnit{}
and \OccUniform{} per cent. Folding in the dwell-measured Class~B curve,
so each window carries the completeness measured for the morphology it
searches, extends the calculation to \NOccAll{} systems and moves the
number to \OccAll{} per cent. Table~\ref{tab:occurrence} carries the ladder in
EIRP and in epoch activity.

How far this travels is bounded three ways. The Class~A recovery curve is
measured on one configuration (AU~Mic, 488-kHz Band~6) and applied to all
\NWinA{} Class~A windows; the $^{+\RecThreshHi}_{-\RecThreshLo}$
percentage-point binomial interval is sampling noise within that one run and
does not bound the transfer error, whereas scaling the curve by
0.5--2$\times$ moves the number from \OccMeasured{} to
\OccBracketLo--\OccBracketHi{} per cent, which is the honest width. The $C_i$
are not independent: windows group into \NEB{} execution blocks with an
intraclass correlation of \IccRank, whose design effect moves
\OccMeasuredRound{} to \EffFIccPct{} per cent, an order below the transfer
term. Under any transmitter-frequency prior spread across ALMA's tuning range
the bound vanishes, the per-system Class~A union being 1.73\,GHz in the median
against ${\sim}75$\,GHz.""",
    r"""Everything below sets $F_i=D_i=1$ \emph{by conditioning, not by
measurement}. At EIRP $\geq10^{16}$\,W the measured form gives
$f_{95}\approx\OccMeasuredRound$ per cent over the \NOccSystems{} systems
carrying a Class~A window. Folding in the dwell-measured Class~B curve
extends the calculation to \NOccAll{} systems and moves the number to
\OccAll{} per cent. Table~\ref{tab:occurrence} carries the ladder in EIRP
and in epoch activity.

How far this travels is bounded three ways. The Class~A recovery curve is
measured on one configuration and applied to all \NWinA{} Class~A windows
(Table~\ref{tab:configdist}); scaling it by 0.5--2$\times$ moves the number
to \OccBracketLo--\OccBracketHi{} per cent, which is the honest width. The
$C_i$ are not independent, windows grouping into \NEB{} execution blocks
with an intraclass correlation of \IccRank, but that design effect is an
order below the transfer term. And under any transmitter-frequency prior
spread across ALMA's tuning range the bound vanishes, the per-system
Class~A union being 1.73\,GHz in the median against ${\sim}75$\,GHz.""")

fz.apply('technosignatures_20pc_v3.50.tex', E)

# ------------------------------------------------ tab:selfunc caption, at
# the generator so a clean regeneration reproduces it
P = 'make_tables_v328.py'
s = open(P, encoding='utf-8').read()
OLD = (r"Temperatures are available for 52 of the 88 stars "
       r"(all 88 matched to the 168-entry ALMA-covered census, 58 by exact "
       r"name; 52 of those matches carry a temperature), so the temperature "
       r"panel is normalised within each column over classified objects "
       r"only, with $T_{\rm eff}$ a proxy for spectral class. ")
NEW = (r"Temperatures are available for 52 of the 88 stars, so the "
       r"temperature panel is normalised within each column over classified "
       r"objects only, with $T_{\rm eff}$ a proxy for spectral class. ")
assert s.count(OLD) == 1, s.count(OLD)
open(P, 'w', encoding='utf-8').write(s.replace(OLD, NEW))
print('tab:selfunc caption trimmed at the generator')
