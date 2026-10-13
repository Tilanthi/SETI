#!/usr/bin/env python3
"""v3.51 stage 2: the statistical narrative reduced to the operative chain.

Referee D8 and referee C1 both ask for the same reduction: the main text
should carry the pipeline that decides a disposition, and nothing else.  The
survey-level false-alarm calibration is a validation of that pipeline, not a
gate in it, so what stays in the main text is what it measured and what it
licenses; the component-by-component construction moves to
Appendix~\ref{app:falsealarm}, which is where the worked derivation referee
C2 asks for now lives.  Nothing is deleted: every number below survives in
one place or the other, and no caveat is softened in the move.

  S2-1  The five-component false-alarm block becomes one compact statement
        of the measurement and its meaning.
  S2-2  The exchangeability battery is compressed to its results, with the
        construction of each test left to the appendix.
  S2-3  The appendix receives the construction it now has to carry.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------ S2-1
sub(r"""Each window-level test compares the peak signal-to-noise ratio at the
star's position with the same statistic at \NCtrl{} controls. The drift grid and thousands of channels apply identically to both, so
the per-window trials factor is absorbed empirically. The statistic is
symmetric, one propagated stellar position against one position per control.
Every number here derives from that frozen statistic; the retired
asymmetric variant is development history
(Appendix~\ref{app:exclusions}). The
false-alarm probability has five components, in the order the procedure
applies them.

\emph{(i) The empirical spatial rank probability.} The per-window
significance quantity is an empirical spatial rank probability under the
control-position null, and no Gaussian-tail $p$-value; what the control
ensemble delivers is an empirical null distribution conditional on approximate
spatial exchangeability, and not a direct measurement of a local false-alarm
probability. Under exchangeability one designated position of \RankFloor{} ranks first with
probability exactly $1/\RankFloor$, whether the noise is Gaussian or
heavy-tailed, so heavy tails cannot explain an excess. The survey expectation
is \ExpFlags{} windows and \SbrN{} are observed, $P=\SbrPobs$ under an
independent-Poisson approximation. That excess is astrophysical. Genuine
celestial line emission sits at the stellar position in \SbrAstro{} of the
\SbrN{} rank-first windows (Table~\ref{tab:flagged}), so those are not draws
from the noise null, and removing them leaves \SbrResid{} against \ExpFlags{}
expected.

\emph{(ii) The $\geq5\sigma$ amplitude requirement and (iii) the line
mask.} Only \NHits{} of \NWindows{} windows contain any $\geq5\sigma$
crossing at the stellar position. The ensemble calibrates the rank and the
trial count follows from it, because a window's channel$\times$drift grid holds
up to \CellsWinMax{} cells (Appendix~\ref{app:falsealarm}), far more than
\NCtrl{} controls can resolve, so the control maximum absorbs whatever
effective trial count the noise carries. The velocity-space mask
(Appendix~\ref{app:linemask}) then removes known molecular emission from every
crossing before it can count as unattributed. It is an analysis choice, never
lowers the noise-null budget, and carries no disposition alone, the three CO
attributions being kinematic (Table~\ref{tab:flagged}).

\emph{(iv) The family-level pseudo-target Monte Carlo.} Each trial draws
one control per window uniformly from its annulus as the pseudo-star and
passes it through the operative gates, $T\geq5\sigma$ then the velocity mask.
This prespecified procedure carries threshold, mask and ring geometry together
on real data and expects \PsFlagMu{} flagged pseudo-target windows
(\PsFlagPzero{} per cent of trials flag none); (i) and the Bonferroni scale
agree.

\emph{(v) The control-ensemble floor, and the second-stage local null.}
Authentication falls to localisation, recurrence and astrophysical
attribution (\S\ref{sec:statistic}), and we pre-commit that no crossing will
be advanced as a candidate on rank statistics alone. That floor belongs to
the first stage, and a second-stage local null carries the four flagged
windows past it. For each we take a retained control position and standardise its residual by
the pipeline's per-integration noise map. Every integration is then shifted
independently and at random in channel, and the identical search is re-run
with the same noise map, weights, drift grid and channel count. A rigid shift
preserves each integration's spectral autocorrelation, and the maximum runs
over the same grid, so each null realisation carries the same trials factor as
the measurement at the star. Independence across integrations leaves nothing
coherent along a drift track, which makes each realisation signal-free by
construction. Between $\LNDrawsMin$ and $\LNDrawsMax$ realisations per window
resolve probabilities well below $1/\RankFloor$. The statistic was reimplemented
from the pipeline source and reproduced all four published $T_\star$
values bit for bit before any null was drawn.

Each null has first to reproduce the distribution of the
\LNNFirstStage{} real control maxima, genuine draws of the same
statistic at exchangeable positions. The criteria were fixed before inspection: \LNValidLo{} to \LNValidHi{}
per cent of real controls above the null's 99th percentile, under 1 per
cent above its maximum. Three windows pass. HD~48370 Band~6 fails badly: \LNHDnAbove{} of its
\LNNFirstStage{} real controls, \LNHDPctAbove{} per cent, exceed the
maximum of $\LNDrawsMax$ null draws, and those controls sit at median
\LNHDRealMed{} against the null's \LNHDNullMed. The cause is physical,
the field carrying extended emission and its imaging residuals, coherent
across integrations, which the scramble destroys by design. A
scrambled-noise probability there would be manufactured significance, so
we quote none for that window.

The two $\beta$~Pictoris windows act as positive controls: no draw
reaches $T_\star$ in either, giving $p<\LNpBpicThree$ in Band~3 and
$p<\LNpBpicSix$ in Band~6, which is what a working statistic should return
where a genuine localised astrophysical signal is present, here on
independently known CO. For CP$-$72~2713 the null resolves the value itself,
\LNnExceedCP{} of $\LNDrawsMax$ draws equalling or
exceeding $T_\star$, and an extreme-value fit to that window's
\LNNFirstStage{} control maxima agrees with it to a factor
\LNCPAgreeFac, a \LNNBootGEV-fold bootstrap putting the chance of the
true value falling below the Bonferroni scale at \LNCPBootPct{} per
cent; the values, and what they do and do not license, are with that
window below. The same fit places HD~48370 at $p=\LNpHDgev$
($\LNpHDgevLo$ to $\LNpHDgevHi$), unremarkable and consistent with the
CO attribution.

Two limits attach to these numbers. The retained products keep full dynamic
spectra for only \LNNRetained{} of the \LNNFirstStage{} control positions, so
position-to-position heterogeneity rests on \LNNRetained{} draws, and that is
what breaks the HD~48370 null. Retaining more control spectra would remove the
limit. No number quoted here uses parametric extrapolation of a null tail; for
$\beta$~Pictoris Band~3 the natural fits disagree by \LNTailDex{} orders of
magnitude.""",
    r"""Each window-level test compares the peak signal-to-noise ratio at the
star's position with the same statistic at \NCtrl{} controls, and because the
drift grid and the thousands of channels apply identically to both, the
per-window trials factor is absorbed empirically rather than modelled. Under
exchangeability one designated position of \RankFloor{} ranks first with
probability exactly $1/\RankFloor$, whatever the shape of the noise
distribution, so a heavy tail cannot by itself produce an excess of rank-first
windows. The survey expectation is \ExpFlags{} such windows and \SbrN{} are
observed, $P=\SbrPobs$ under an independent-Poisson approximation, and that
excess is astrophysical rather than statistical: genuine celestial line
emission sits at the stellar position in \SbrAstro{} of the \SbrN{}
(Table~\ref{tab:flagged}), which leaves \SbrResid{} against \ExpFlags{}
expected. Two further calibrations agree with that reading. Only \NHits{} of
the \NWindows{} windows contain any $\geq5\sigma$ crossing at the stellar
position at all; and a prespecified Monte~Carlo that promotes one control per
window to pseudo-star and runs it through the operative gates, the $5\sigma$
threshold and the velocity mask, expects \PsFlagMu{} flagged pseudo-target
windows, in agreement with the rank budget and with the Bonferroni scale. The
whole construction, the trials arithmetic behind it and the residual excess it
leaves are worked through in Appendix~\ref{app:falsealarm}.

@@PARA@@Ranking against \NCtrl{} controls cannot resolve a probability below
$1/\RankFloor$, so a second-stage local null was built to carry the four
stage-1 windows past that floor. It scrambles each integration independently
in channel and re-runs the identical search with the same noise map, weights
and drift grid, which destroys anything coherent along a drift track while
preserving each integration's own spectral autocorrelation and trials factor;
the construction, its validation criteria and its failure mode are in
Appendix~\ref{app:provenance}. Three of the four windows pass validation. The
two $\beta$~Pictoris windows behave as positive controls, no draw of
$\LNDrawsMax$ reaching $T_\star$ in either ($p<\LNpBpicThree$ and
$p<\LNpBpicSix$), which is what a working statistic should return where a
genuine localised signal is present. For CP$-$72~2713 the null resolves the
value itself, \LNnExceedCP{} draws of $\LNDrawsMax$ equalling or exceeding
$T_\star$, and an extreme-value fit to that window's own control maxima agrees
to a factor \LNCPAgreeFac; both are used with that window below. HD~48370
Band~6 fails validation outright, \LNHDPctAbove{} per cent of its real
controls exceeding the maximum of $\LNDrawsMax$ null draws, because the field
carries extended emission and imaging residuals that are coherent across
integrations and that the scramble destroys by design, so we quote no
scrambled-noise probability there. That failure is a direct consequence of
retaining full dynamic spectra for only \LNNRetained{} of the \LNNFirstStage{}
control positions, and no number quoted here rests on a parametric
extrapolation of a null tail.""")

# ------------------------------------------------------------------ S2-2
sub(r"""Exchangeability is the central assumption of the statistic: the
rank expectation holds only if the star and its \NCtrl{} controls are
exchangeable under the null, which spatially varying noise,
sidelobes, correlated pixels or phase-centre-localised calibration
residuals could spoil. For a debris-disc archive the dominant violation is
none of those but resolved astrophysical emission filling the annulus, measured
here in HD~48370's CO ring and in $\beta$~Pictoris' recurring Band~6 window,
where the ring outshines the star by $\BpRecSixRingRatio\times$. It suppresses
a star-exceeds-ring outcome and never manufactures one, so it costs sensitivity
alone. The primary-beam term is settled by construction
(\S\ref{sec:statistic}): the statistic is formed on \emph{uncorrected}
amplitudes, whose thermal noise is position-independent across the field, and
$\sigma(t,\nu)$ is one scale shared by the star and every control. The \RankFloor{} positions are therefore \emph{approximately} exchangeable
under a \emph{restricted} noise-only null, and the primary beam enters only in
converting to flux. Both qualifiers carry weight. The argument covers thermal
noise and the beam, and it does not cover residual calibration or continuum
systematics, which can occur preferentially at the phase centre. That matters
here because the star is usually the original science target: every searched
star but Wolf~219 is the pointed target of at least one block
(\S\ref{sec:sample}). The rest we measure by stratum
(Fig.~\ref{fig:ctrldiag}). Median per-window control maxima are flat across bands, running 4.42 to 4.69
from Band~3 to Band~8. A Kolmogorov--Smirnov test of the star's rank among its
controls against $U(0,1)$ is consistent in every band
($p=\KsBandLo{}$--$\KsBandHi$) and in the coarse stratum ($p=\KsCoarse$).
Fine-channel windows sit higher, control maximum \CtrlMedFine{} against
\CtrlMedCoarse, as their far larger channel$\times$drift trial count predicts.
The test is conditional on the window, so that is no violation.

Two tests address the stronger question, exchangeability of the ensemble
itself. Ranking each control against the other \NCtrl-1 by the statistic and
add-one rule used for the star gives \NPseudo{} pseudo-star ranks, uniform to
the resolution the ensemble can express ($p=\PseudoKSp$) in every band and at
both channelisations. That geometry differs from star-against-ring, so it
cannot by itself detect a centre-versus-annulus asymmetry. \textbf{The test
that can is the two-sample comparison of the \NWindows{} real stellar ranks
against the pooled pseudo-ranks, $p=\StarPseudoP$: the stellar position
behaves like one more position in its own annulus.} The second test is radial.
The Spearman correlation of control statistic against reconstructed radius has
median \RingRhoNull{} over the \RingRhoNullN{} crossing-free windows, bounding
any systematic radial suppression of the controls below \RingRhoBoundPct{} per
cent in the mean. Both are null, which supplies the bound the one-sidedness
argument above lacks.

One stratum departs, and we report it separately. The fine-channel
windows fail the same $U(0,1)$ test at $p=\KsFine$ ($n=\NFine$): four
contain an on-star peak above their own control maximum, against 0.22
expected, precisely the four flagged windows of Table~\ref{tab:flagged}.
That fits the astrophysical line features identified below, with no
misbehaving ensemble, but the departure is genuine, so fine-window rank
probabilities are slightly optimistic. It is also localised: excluding the 20
fine windows with any $\geq5\sigma$ stellar crossing restores uniformity
($p=\KsFineNoCross$). Per-control noise records and gain are two
stratifications the frozen products cannot support, so the empirical rank
distributions bound the net effect, at \PsFlagMu{} expected flags against a
rank-only budget of \ExpFlags. The windows nearest the beam edge are not
silently affected either, the largest retained offset sitting inside the
annulus's own radial span.""",
    r"""Exchangeability is the central assumption of the statistic, and it can
fail through spatially varying noise, sidelobes, correlated pixels or
calibration residuals localised at the phase centre. For a debris-disc archive
the dominant violation is none of those but resolved astrophysical emission
filling the annulus, seen here in HD~48370's CO ring and in $\beta$~Pictoris'
recurring Band~6 window, where the ring outshines the star by
$\BpRecSixRingRatio\times$; that suppresses a star-exceeds-ring outcome
instead of manufacturing one, so it costs sensitivity and nothing else. The
primary beam is settled by construction, since the statistic is formed on
\emph{uncorrected} amplitudes whose thermal noise does not depend on position
and $\sigma(t,\nu)$ is one scale shared by the star and every control
(\S\ref{sec:statistic}), so the \RankFloor{} positions are
\emph{approximately} exchangeable under a \emph{restricted} noise-only null.
Both qualifiers carry weight, because that argument covers the thermal noise
and the beam and does not cover residual calibration or continuum systematics,
which can occur preferentially where the pointed science target sits.

@@PARA@@Four measurements bound what is left, and all four are null. Ranking
each control against the other \NCtrl-1 by the rule used for the star gives
\NPseudo{} pseudo-star ranks, uniform to the resolution the ensemble can
express ($p=\PseudoKSp$) in every band and at both channelisations; that
geometry cannot by itself detect a centre-versus-annulus asymmetry, so the
test that can is the two-sample comparison of the \NWindows{} real stellar
ranks against the pooled pseudo-ranks, and it returns $p=\StarPseudoP$.
\textbf{On that comparison the stellar position behaves like one more position
in its own annulus.} The Spearman correlation of control statistic against
reconstructed radius has median \RingRhoNull{} over the \RingRhoNullN{}
crossing-free windows, bounding any systematic radial suppression of the
controls below \RingRhoBoundPct{} per cent in the mean. And the star's own
residual variance is measured directly against the controls' in
\S\ref{sec:rsigma}.

@@PARA@@One stratum departs, and we report it separately. The fine-channel
windows fail the $U(0,1)$ rank test at $p=\KsFine$ ($n=\NFine$), because four
of them contain an on-star peak above their own control maximum against 0.22
expected, and those four are precisely the flagged windows of
Table~\ref{tab:flagged}. That is the astrophysical line emission identified
below rather than a misbehaving ensemble, but the departure is genuine, so
fine-window rank probabilities here are slightly optimistic; excluding the
\NCrossWin{} fine windows with any $\geq5\sigma$ stellar crossing restores
uniformity ($p=\KsFineNoCross$). Two stratifications the frozen products
cannot support, per-control noise records and gain, are bounded only through
these empirical rank distributions. Figure~\ref{fig:ctrldiag} shows the
by-stratum behaviour: median per-window control maxima are flat across bands
and the fine class sits higher than the coarse, \CtrlMedFine{} against
\CtrlMedCoarse, as its far larger channel$\times$drift trial count predicts.""")

fz.apply(TEX, E)
