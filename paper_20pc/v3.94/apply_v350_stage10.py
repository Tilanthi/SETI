#!/usr/bin/env python3
"""v3.50 stage 10: the final 0.3 page, and the last of the de-AI sweep.

Four main-text passages restate something the paper now says better
elsewhere: the introduction's roadmap (Figure 2 is the roadmap), the
introduction's tuning caveat (the abstract and section 5.4 both carry it),
the channel-dilution derivation (Appendix A owns it), and the systematic
budget's single 90-word sentence, which is broken into three.
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


sub(r"""No ancillary analysis carries a technosignature disposition, the continuum
screen alone feeding an argument in the primary lane
(\S\ref{sec:statistic}, \S\ref{sec:ancillary}). One worked case runs through
the paper, a crossing towards $\beta$~Pictoris, the largest
star-versus-control contrast here, attributed to the disc's known
circumstellar CO across two transitions and three epochs
(\S\ref{sec:technosearch}). Per-target results are in Appendix~\ref{app:table}, and dispositions,
false-alarm accounting and injection completeness consolidate in
Tables~\ref{tab:searchspace} and~\ref{tab:flagged} with
Appendices~\ref{app:falsealarm} and~\ref{app:inject}.

The symmetric detection statistic and the
$\pm\MaskVWidth$\,km\,s$^{-1}$ molecular-line mask were both defined,
and the statistic once revised, on these data (\S\ref{sec:aumic}).
The rank probabilities and false-alarm figures are therefore
descriptive of this dataset, not an independent validation of the
pipeline's false-positive rate, and this is restated where it bears on a
number.""",
    r"""No ancillary analysis carries a technosignature disposition. One worked
case runs through the paper, a crossing towards $\beta$~Pictoris, which is
the largest star-versus-control contrast here and is attributed to the
disc's known circumstellar CO across two transitions and three epochs
(\S\ref{sec:technosearch}). Figure~\ref{fig:funnel} is the roadmap: it
gives the selection from catalogue to searched sample on the left, and the
decision chain from window to disposition on the right.

The statistic and the molecular-line mask were both defined on these data,
and the statistic once revised (\S\ref{sec:aumic}), so the rank
probabilities and false-alarm figures describe this dataset and do not
independently validate the pipeline's false-positive rate. An out-of-sample
check on windows searched after both were frozen is in
\S\ref{sec:heldout}.""")

# ---------------------------------------- the 90-word systematic budget
sub(r"""Their systematic budget is the ALMA absolute flux scale (5--10 per cent,
band- and epoch-dependent), residual atmospheric phase after water-vapour
correction and phase referencing (a coherent point-source loss
$\exp(-\sigma_\phi^{2}/2)$, typically 5--20 per cent at 230--345\,GHz, common
to the star and the annulus within the isoplanatic patch and so no threat to
exchangeability), the primary-beam model at the stellar
offset, the instrumental spectral response (the boxed rule below; median
$\times\HanFacMed$) and visibility calibration. Each
multiplies $S_{\rm min}$ and hence EIRP$_{5\sigma}$ directly; \emph{Gaia}
distance errors are negligible here.""",
    r"""Five terms enter their systematic budget. They are the ALMA absolute flux
scale, 5--10 per cent and band- and epoch-dependent; residual atmospheric
phase after water-vapour correction and phase referencing; the
primary-beam model at the stellar offset; the instrumental spectral
response, median $\times\HanFacMed$ by the boxed rule below; and
visibility calibration. Each multiplies $S_{\rm min}$, and hence
EIRP$_{5\sigma}$, directly, while \emph{Gaia} distance errors are
negligible here. The atmospheric term is a coherent point-source loss
$\exp(-\sigma_\phi^{2}/2)$, typically 5--20 per cent at 230--345\,GHz. It
is common to the star and the annulus within the isoplanatic patch, so it
is no threat to exchangeability.""")

# ---------------------------------------- channel dilution, owned by App A
sub(r"""The native channel width is also the linewidth convention for every EIRP
threshold, the commonest confusion when technosignature limits are
compared across surveys. Channel dilution spreads a sub-channel carrier's total line flux across
the channel, so the minimum detectable total power is
$4\pi d^{2}S_{\min}\Delta\nu_{\rm ch}$, independent of the transmitter's
own width below the channel (Appendix~\ref{app:conventions}).
EIRP$_{5\sigma}$ is thus the minimum \emph{total} power of a channel-confined
carrier, never a spectral power density. Dividing by
$\Delta\nu_{\rm ch}$ gives the minimum spectral power for wider
transmitters, so a $10^{15}$\,W threshold at 15.625-MHz channelisation
is $6.4\times10^{7}$\,W\,Hz$^{-1}$. The 1-Hz and 3-Hz
limits of Hz-resolution surveys are total powers in the same sense, each
the best case of its own channelisation, which makes the axes of
Fig.~\ref{fig:context} commensurable. Channelisation is the dominant price the
archive exacts, and we do not project an Hz-resolution sensitivity from it,
because a radiometer-equation scaling $P_{\min}\propto\sqrt{\Delta\nu}$ across
six orders of magnitude in spectral resolution would be a thought experiment
not an achievable ALMA sensitivity.""",
    r"""The native channel width is also the linewidth convention for every EIRP
threshold, which is the commonest confusion when technosignature limits are
compared across surveys. Channel dilution spreads a sub-channel carrier's
total line flux across the channel, so the minimum detectable total power
is $4\pi d^{2}S_{\min}\Delta\nu_{\rm ch}$, independent of the
transmitter's own width below the channel (Appendix~\ref{app:conventions}).
EIRP$_{5\sigma}$ is therefore the minimum \emph{total} power of a
channel-confined carrier and never a spectral power density. The 1-Hz and
3-Hz limits of Hz-resolution surveys are total powers in the same sense,
each the best case of its own channelisation, which is what makes the axes
of Fig.~\ref{fig:context} commensurable. Channelisation is the dominant
price the archive exacts. We do not project an Hz-resolution sensitivity
from it, because scaling by $P_{\min}\propto\sqrt{\Delta\nu}$ across six
orders of magnitude in spectral resolution would be a thought experiment
and not an achievable ALMA sensitivity.""")

# ------------------------------------------------- CP-72, one more pass
sub(r"""That same member observing unit set, \texttt{\CpMous}, holds a second public
execution block at this tuning, \texttt{\CpEbUnsearched}, which the
de-duplication of \S\ref{sec:sample} declined. We have since calibrated and
searched it with the unmodified pipeline. It matches the first epoch in
tuning, channel width (\CpRecChanwkHz\,kHz), channel count (\CpNChan),
integrations (\CpRecNInt) and on-source time, and the two frequency axes are
registered to \CpRecOffkHz\,kHz, \CpRecOffChan{} of a channel, so the feature
falls in the same channel, \CpRecChan. Only the drift grid differs, one trial
coarser, which puts the first epoch's fitted rate \CpRecNodeChan{} channel
from the nearest node. The second block is also the deeper, combined rms
\CpRecRmsTwo\,mJy against \CpRecRmsOne, so a persistent emitter at the first
epoch's flux would have appeared there at $T_\star=\CpRecExpT$, above both the
$5\sigma$ trigger and that window's largest control, \CpRecCtrlMax. That
margin is narrow, so a second \emph{flag} was never assured; what the
retirement rests on is the flux comparison below, which carries no trials
factor.""",
    r"""That same member observing unit set holds a second public execution block
at this tuning, \texttt{\CpEbUnsearched}, which the de-duplication of
\S\ref{sec:sample} declined. We have since calibrated and searched it with
the unmodified pipeline. It matches the first epoch in tuning, channel
width, channel count, integration count and on-source time, and the two
frequency axes are registered to \CpRecOffChan{} of a channel, so the
feature falls in the same channel. Only the drift grid differs, by one
trial. The second block is also the deeper, at a combined rms of
\CpRecRmsTwo\,mJy against \CpRecRmsOne, so a persistent emitter at the
first epoch's flux would have appeared there at $T_\star=\CpRecExpT$. That
is above both the $5\sigma$ trigger and that window's largest control,
\CpRecCtrlMax, but the margin is narrow, so a second \emph{flag} was never
assured. What the retirement rests on is the flux comparison below, which
carries no trials factor.""")

fz.apply(TEX, E)

s = open(TEX, encoding='utf-8').read()
s = re.sub(r'\s*@@PARA@@\s*', '\n\n', s)
open(TEX, 'w', encoding='utf-8').write(s)
