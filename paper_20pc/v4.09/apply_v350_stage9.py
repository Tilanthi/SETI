#!/usr/bin/env python3
"""v3.50 stage 9: the last main-text tightening, which is where page count
actually responds.

Measured during this cycle and worth recording: cutting appendix prose did
not move the page count at all (47,540 -> 46,951 characters, total
unchanged at 29.49 pages), because the appendix region is float-quantised
and the freed space is absorbed.  Main-text cuts propagate.  Everything
below is therefore main text, and every one of them removes a second
statement rather than a finding.
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


# ---------------------------------------------- the ensemble-level tests
sub(r"""For the stronger question, exchangeability of the ensemble itself, we
ranked each of a window's \NCtrl{} controls against the other
\NCtrl-1 by the statistic and add-one rule used for the star, pooled over the
survey. The \NPseudo{} pseudo-star ranks are uniform to the resolution the
ensemble can express ($p=\PseudoKSp$) in every band and at both
channelisations; the mean of \PseudoMean{} is the construction value
under the add-one rule and carries no information.
That test compares a control against the other \NCtrl-1 plus add-one, a
different geometry from star-against-ring, so it cannot by itself detect
a centre-versus-annulus asymmetry. \textbf{The test that can is the
two-sample comparison of the \NWindows{} real stellar ranks against the
pooled pseudo-ranks, $p=\StarPseudoP$: the stellar position behaves like
one more position in its own annulus}, their median \emph{statistics}
agreeing at \SymMedStar{} against \SymMedCtrl{} ($D=\SymKSd$). The
radial test is the second: the Spearman correlation of control statistic
against reconstructed radius has median \RingRhoNull{} over the
\RingRhoNullN{} crossing-free windows, with 5th and 95th percentiles
\RingRhoNullLo{} and \RingRhoNullHi, so any systematic radial
suppression of the controls is bounded below \RingRhoBoundPct{} per cent
in the mean. Both are null, which supplies the bound the one-sidedness argument
above lacks.""",
    r"""Two tests address the stronger question, exchangeability of the ensemble
itself. Ranking each control against the other \NCtrl-1 by the statistic
and add-one rule used for the star gives \NPseudo{} pseudo-star ranks,
uniform to the resolution the ensemble can express ($p=\PseudoKSp$) in
every band and at both channelisations. That geometry differs from
star-against-ring, so it cannot by itself detect a centre-versus-annulus
asymmetry. \textbf{The test that can is the two-sample comparison of the
\NWindows{} real stellar ranks against the pooled pseudo-ranks,
$p=\StarPseudoP$: the stellar position behaves like one more position in
its own annulus.} The second test is radial. The Spearman correlation of
control statistic against reconstructed radius has median \RingRhoNull{}
over the \RingRhoNullN{} crossing-free windows, bounding any systematic
radial suppression of the controls below \RingRhoBoundPct{} per cent in the
mean. Both are null, which supplies the bound the one-sidedness argument
above lacks.""")

sub(r"""That fits the astrophysical line features identified below, with no misbehaving
ensemble, but the departure is genuine, so fine-window rank
probabilities are slightly optimistic. It is also localised, since excluding
the 20 fine windows with any $\geq5\sigma$ stellar crossing restores uniformity
($p=\KsFineNoCross$, $n=98$). Per-control noise records and gain are two stratifications the frozen
products cannot support, so the empirical rank distributions bound the
net effect: expected flags \PsFlagMu{} against a rank-only budget of
\ExpFlags, with no excess in any stratum. The windows nearest the beam
edge are not silently affected either: the largest retained offset,
\PbMaxStar{} at $\PbMaxRoverTheta\,\theta_{\rm PB}$, sits inside the
annulus's own radial span, and the four $\epsilon$\,Eri Band~6 windows
are withheld outright (\S\ref{sec:frames}). Controls at equal
holography-model gain would remove the sky-brightness term.""",
    r"""That fits the astrophysical line features identified below, with no
misbehaving ensemble, but the departure is genuine, so fine-window rank
probabilities are slightly optimistic. It is also localised: excluding the
20 fine windows with any $\geq5\sigma$ stellar crossing restores uniformity
($p=\KsFineNoCross$). Per-control noise records and gain are two
stratifications the frozen products cannot support, so the empirical rank
distributions bound the net effect, at \PsFlagMu{} expected flags against a
rank-only budget of \ExpFlags. The windows nearest the beam edge are not
silently affected either, the largest retained offset sitting inside the
annulus's own radial span.""")

sub(r"""Two limits attach to these numbers. The retained products
keep full dynamic spectra for \LNNRetained{} of the \LNNFirstStage{}
control positions, so position-to-position heterogeneity rests on
\LNNRetained{} draws; that is what breaks the HD~48370 null, a limit the
retained products impose on the method and one that retaining more control
spectra would remove. Parametric extrapolation of a null tail
is not used for any number quoted here: for $\beta$~Pictoris Band~3 the
natural fits disagree by \LNTailDex{} orders of magnitude and one
implies a bounded tail and returns exactly zero.""",
    r"""Two limits attach to these numbers. The retained products keep full
dynamic spectra for only \LNNRetained{} of the \LNNFirstStage{} control
positions, so position-to-position heterogeneity rests on \LNNRetained{}
draws, and that is what breaks the HD~48370 null. Retaining more control
spectra would remove the limit. No number quoted here uses parametric
extrapolation of a null tail; for $\beta$~Pictoris Band~3 the natural fits
disagree by \LNTailDex{} orders of magnitude.""")

# ------------------------------------------------------- section 5.3 open
sub(r"""All \NStarBands{}
star/band datasets yielded at least one carrier-lane result
(process-level failures, \S\ref{sec:exclusions}, uncounted), spanning
\NWindows{} spectral-window measurements after the catalogue audit
removed \NDup{} duplicate rows (Appendix~\ref{app:table});
B6/\BandWinSix{} and B7/\BandWinSeven{} dominate (per-band breakdown in
Table~\ref{tab:perband}). EIRP$_{5\sigma}$ trigger thresholds span
$\EirpMin$--$\EirpMax$\,W, median $\EirpMedian$\,W
(Figures~\ref{fig:waterfall}, \ref{fig:context}); the deepest thresholds are
reached toward the nearest systems ($1.6\times10^{13}$\,W for the UV~Ceti pair
at 2.7\,pc), though depth also tracks integration time and channelisation, and
the shallowest is $\eta$~Corvi. Against the
benchmarks of \S\ref{sec:benchmarks}, only that pair's two resolved
components reach below the Arecibo-like planetary-radar EIRP,
\CaseDetCoarseNow{} system of \NSystems.""",
    r"""All \NStarBands{} star/band datasets yielded at least one carrier-lane
result, spanning \NWindows{} spectral-window measurements after the
catalogue audit removed \NDup{} duplicate rows. Bands~6 and~7 dominate, with
\BandWinSix{} and \BandWinSeven{} windows (Table~\ref{tab:perband}).
Nominal EIRP$_{5\sigma}$ trigger thresholds span $\EirpMin$--$\EirpMax$\,W
at a median of $\EirpMedian$\,W (Figs.~\ref{fig:waterfall} and
\ref{fig:context}). The deepest are reached toward the nearest systems,
$1.6\times10^{13}$\,W for the UV~Ceti pair at 2.7\,pc, though depth also
tracks integration time and channelisation. Only that pair reaches below
the Arecibo-like planetary-radar EIRP of \S\ref{sec:benchmarks}.""")

# ------------------------------------------------------- future work
sub(r"""\emph{Use the visibilities.} The largest unused advantage is the
interferometric phase itself: whether a spectral feature carries the
signature of a celestial point source at a known position. For each
surviving candidate one would compare competing likelihoods,
$H_{\star}$, a source at the propagated stellar position,
$V_{ij}=A(t,\nu)\,e^{-2\pi i(u_{ij}l_\star+v_{ij}m_\star)}$; $H_{\rm
sky}$, a source elsewhere; $H_{\rm common}$, correlated or common-mode
interference; and $H_{\rm noise}$, thermal and calibration residual, and
evaluate $\Lambda=\mathcal L(V|H_\star)/\mathcal L(V|H_{\rm
noise}{+}H_{\rm common})$. That is strictly more powerful than ranking a peak
against a control ensemble, and would demote the ensemble to a calibration
layer.""",
    r"""\emph{Use the visibilities.} The largest unused advantage is the
interferometric phase itself, which says whether a spectral feature carries
the signature of a celestial point source at a known position. For each
surviving candidate one would compare the likelihoods of a source at the
propagated stellar position, a source elsewhere, common-mode interference
and thermal noise, and evaluate their ratio. That is strictly more powerful
than ranking a peak against a control ensemble, and it would demote the
ensemble to a calibration layer.""")

sub(r"""\emph{Extend the injection campaign and the polarisation axis.} The
completeness curve should be measured per band, channel width,
integration time, antenna count and primary-beam position, and pushed
past $10\sigma$ until it asymptotes. The design is a stratified grid
over those axes, injections at randomised drift rates and channel phases,
morphologies extended to sinusoidal acceleration tracks from
representative sample orbits, trial-level logging from the first run,
and an independent re-implementation cross-check. The
polarisation axis buys discrimination against weakly polarised
astrophysical backgrounds at no sensitivity cost.""",
    r"""\emph{Extend the injection campaign and the polarisation axis.} The
completeness curve should be measured on a stratified grid over band,
channel width, integration time, antenna count and primary-beam position,
which are the axes Table~\ref{tab:configdist} shows the present
single-configuration measurement does not span, and pushed past $10\sigma$
until it asymptotes. The polarisation axis buys discrimination against
weakly polarised astrophysical backgrounds at no sensitivity cost.""")

# --------------------------------------------------- sample selection
sub(r"""The \NCensus{} stars are complete against, and conditional only
on, the 40-parsec reference catalogue intersected with the
public-archive snapshot of 2026 September~8. Against that Gaia~DR3
solar-neighbourhood catalogue (17\,566 stars within 40\,pc) they are
$\lesssim$1 per cent, and fewer once \S\ref{sec:exclusions} removes those
never in fact observed. The two parallax cuts are not interchangeable. The
sample's binding condition is $\sigma_\varpi/\varpi<\PlxAdqlPct$ per cent and
the reference census's is $\le$10 per cent (Table~\ref{tab:selfunc}), so the
ratio compares two differently selected populations. The realised sample is
far better than its condition, $\sigma_\varpi/\varpi$ reaching
\PlxWorstPct{} per cent at worst and exceeding 1 per cent in only
\NPlxOverEight{} entries. The census is also incomplete at both ends,
and the fraction shows only that coverage is small.
Table~\ref{tab:selfunc} leaves the selection function inspectable; age and
disc-hosting flags are documented qualitatively, being unevenly available.""",
    r"""The \NCensus{} stars are complete against, and conditional only on, the
40-parsec reference catalogue intersected with the public-archive snapshot
of 2026 September~8. Against that Gaia~DR3 catalogue of \NGaiaCensus{}
stars they are $\lesssim$1 per cent, and fewer once \S\ref{sec:exclusions}
removes those never in fact observed (Fig.~\ref{fig:funnel}). The two
parallax cuts are not interchangeable, the sample's binding condition being
$\sigma_\varpi/\varpi<\PlxAdqlPct$ per cent against the census's 10 per
cent, so the ratio compares two differently selected populations. The
realised sample is far better than its condition, reaching \PlxWorstPct{}
per cent at worst and exceeding 1 per cent in only \NPlxOverEight{}
entries. The census is incomplete at both ends, so the fraction shows only
that coverage is small.""")

fz.apply(TEX, E)

s = open(TEX, encoding='utf-8').read()
s = re.sub(r'\s*@@PARA@@\s*', '\n\n', s)
# a paragraph break lost to an earlier rewrap
s = s.replace('criterion, and the two are never interchanged. \\subsubsection*{Astrophysical\nend-to-end validation: $\\beta$~Pictoris CO}',
              'criterion, and the two are never interchanged.\n\n'
              '\\subsubsection*{Astrophysical end-to-end validation: $\\beta$~Pictoris CO}')
open(TEX, 'w', encoding='utf-8').write(s)
