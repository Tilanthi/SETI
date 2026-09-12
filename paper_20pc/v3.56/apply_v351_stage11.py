#!/usr/bin/env python3
"""v3.51 stage 11: the final compression, to hold 29 pages.

Only duplication goes.  Each anchor below states something an appendix
already states in full, and each cross-reference is left in place.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


sub(r"""\emph{Injection-recovery validation} (Appendix~\ref{app:inject}). Synthetic
tones of known amplitude were injected into real visibilities and recovered
with the unmodified pipeline, \NTrials{} trials across six window
configurations, three bands and both resolution classes. Two properties of the
pipeline matter for reading the result. The baseline step is a per-integration
block median along \emph{frequency} (Table~\ref{tab:algorithm}, step~4), which
by construction cannot remove a feature confined to one or two channels. The
de-drift step is an inverse-variance-weighted sum over integrations, which
accumulates a persistent carrier coherently. Appendix~\ref{app:inject} gives
the measured recovery curve, and the completeness it supports is stated once,
in the boxed rule of \S\ref{sec:method}. Tables here stay in nominal
EIRP$_{5\sigma}$.

One validation-history item is told in full in
Appendix~\ref{app:inject}. The campaign's original report of 0 of 500
coarse-window recoveries was an artefact of its recovery \emph{criterion} and
never of the search pipeline. The corrected criterion has not been re-derived
by an independent implementation, and that cross-check is an open item
(\S\ref{sec:futurework}). The independent evidence is the dwell campaign of
\S\ref{sec:dwell}, which measures persistent near-static carriers as
\emph{recovered} and so reverses the artefact's reading.

The primary statistic
has no automated injection test on every pipeline change. Three quantified
checks bound undetected pipeline faults instead: the machinery-only lane,
whose amplitude fidelity of $-9$/$+14$ per cent is the bound that caught the
artefact above; the AU~Mic re-analyses under three treatments, whose
recomputation agrees with the released products; and the pseudo-star rank
uniformity over \NPseudo{} pooled ranks ($p=\PseudoKSp$), which any defect of
the statistic itself would displace.""",
    r"""\emph{Injection-recovery validation} (Appendix~\ref{app:inject}). Synthetic
tones of known amplitude were injected into real visibilities and recovered
with the unmodified pipeline, \NTrials{} trials across six window
configurations, three bands and both resolution classes. Two properties of the
pipeline matter for reading the result. The baseline step is a per-integration
block median along \emph{frequency} (Table~\ref{tab:algorithm}, step~4), which
by construction cannot remove a feature confined to one or two channels, and
the de-drift step is an inverse-variance-weighted sum over integrations, which
accumulates a persistent carrier coherently. One history item goes with the
curve: the campaign's original report of 0 of 500 coarse-window recoveries was
an artefact of its recovery \emph{criterion} and never of the search pipeline,
the dwell campaign of \S\ref{sec:dwell} measuring those same persistent
carriers as \emph{recovered}. The corrected criterion has not been re-derived
by an independent implementation, which is an open item
(\S\ref{sec:futurework}).

@@PARA@@The primary statistic has no automated injection test on every
pipeline change, so three quantified checks bound undetected pipeline faults
instead: the machinery-only lane, whose amplitude fidelity of $-9$/$+14$ per
cent is the bound that caught the artefact above; the AU~Mic re-analyses under
three treatments, whose recomputation agrees with the released products; and
the pseudo-star rank uniformity over \NPseudo{} pooled ranks
($p=\PseudoKSp$), which any defect of the statistic itself would displace.""")

sub(r"""Every spectral window of an observation enters the spectral-carrier search,
capped at 8 per target to bound compute cost. The cap bound
one target/band, 61~Vir Band~7 (four of eight windows searched), whose
frequency-space selection function is tabulated; three further targets
($\tau$~Cet, Kapteyn's Star, Van~Maanen's Star) are represented by their
deepest single window and are marked in the released catalogue. Each
searched window yields its own EIRP$_{5\sigma}$ row, and
Figure~\ref{fig:context} plots only the deepest per star. When a crossing is checked against the masked species the operative
discriminant is velocity coincidence: circumstellar emission sits at
rest offset by the gas's kinematics, while a technosignature may appear
at any frequency and drift rate. The searches as executed used a
narrower one-channel-width implementation, which agrees with the
velocity-space form on every disposition here (\S\ref{sec:linecost}).""",
    r"""Every spectral window of an observation enters the spectral-carrier search,
capped at 8 per target to bound compute cost; the cap bound one target/band,
61~Vir Band~7, and three further targets are represented by their deepest
single window and marked in the released catalogue. Each searched window
yields its own EIRP$_{5\sigma}$ row, and Figure~\ref{fig:context} plots only
the deepest per star. When a crossing is checked against the masked species
the operative discriminant is velocity coincidence, since circumstellar
emission sits at rest offset by the gas's kinematics while a technosignature
may appear at any frequency and drift rate.""")

sub(r"""All \NStarBands{} star/band datasets yielded at least one carrier-lane result,
spanning \NWindows{} spectral-window measurements after the catalogue audit
removed \NDup{} duplicate rows. Bands~6 and~7 dominate, with \BandWinSix{} and
\BandWinSeven{} windows (Table~\ref{tab:perband}). Nominal EIRP$_{5\sigma}$
trigger thresholds span $\EirpMin$--$\EirpMax$\,W at a median of
$\EirpMedian$\,W (Figs.~\ref{fig:waterfall} and \ref{fig:context}). The
deepest are reached toward the nearest systems, $1.6\times10^{13}$\,W for the
UV~Ceti pair at 2.7\,pc, though depth also tracks integration time and
channelisation. Only that pair reaches below the Arecibo-like planetary-radar
EIRP of \S\ref{sec:benchmarks}.""",
    r"""All \NStarBands{} star/band datasets yielded at least one carrier-lane
result, spanning \NWindows{} spectral-window measurements after the catalogue
audit removed \NDup{} duplicate rows, and Bands~6 and~7 dominate with
\BandWinSix{} and \BandWinSeven{} windows (Table~\ref{tab:perband}). Nominal
trigger thresholds span $\EirpMin$--$\EirpMax$\,W at a median of
$\EirpMedian$\,W (Figs.~\ref{fig:waterfall} and \ref{fig:context}), the
deepest being reached toward the nearest systems, $1.6\times10^{13}$\,W for
the UV~Ceti pair at 2.7\,pc, though depth also tracks integration time and
channelisation.""")

sub(r"""\caption{The survey as searched, and the paper's
headline numbers in one place. Every count quoted in this paper reconciles with it; subset numbers are
identified where used. The two completeness experiments measure different quantities and are
kept in separate tables. The conditional
searched-domain transmitter fraction is a methodological demonstration
(Appendix~\ref{app:population}) and is deliberately absent.}""",
    r"""\caption{The survey as searched, and the paper's headline numbers in one
place. Every count quoted in this paper reconciles with it. The two
completeness experiments measure different quantities and are kept in separate
tables, and the conditional searched-domain transmitter fraction is a
methodological demonstration (Appendix~\ref{app:population}) and is
deliberately absent.}""")

sub(r"""\caption{The four windows containing a stage-1 spatial outlier, with
the evidence dispositioning each. $T_\star$ is the search statistic at
the stellar position (Eq.~\ref{eq:tstar}) and `ring max' the largest of
that window's \NCtrl{} control statistics. $\nu_{\rm cross}$ is the crossing channel, which differs from the window centre
by up to 0.85\,GHz here, and $S_{\rm peak}=T_\star\sigma$ is the peak flux
density in one native channel. $\Delta\nu$ and $\Delta v$ are the topocentric offset of that channel from the
nearest \emph{laboratory} rest frequency of the masked species, so a positive
value means the observed frequency exceeds the rest frequency. The repaired
mask of \S\ref{sec:linecost} changes no row. The HD~48370 row is the limiting
case, a near-tie of rank dispositioned by velocity coincidence with
independently published emission.}""",
    r"""\caption{The four stage-1 spatial outliers, with the evidence dispositioning
each. $T_\star$ is the search statistic at the stellar position
(Eq.~\ref{eq:tstar}) and `ring max' the largest of that window's \NCtrl{}
control statistics; $\nu_{\rm cross}$ is the crossing channel, which differs
from the window centre by up to 0.85\,GHz here, and
$S_{\rm peak}=T_\star\sigma$ is the peak flux density in one native channel.
$\Delta\nu$ and $\Delta v$ give the topocentric offset of that channel from
the nearest \emph{laboratory} rest frequency of the masked species. The
repaired mask of \S\ref{sec:linecost} changes no row, and the HD~48370 row is
the limiting case, a near-tie of rank dispositioned by velocity coincidence
with independently published emission.}""")

fz.apply(TEX, E)
