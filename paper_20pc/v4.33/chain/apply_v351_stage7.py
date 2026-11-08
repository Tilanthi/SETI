#!/usr/bin/env python3
"""v3.51 stage 7: the additions the referees asked for.

  S7-1  A new subsection, ``Statistical units and independence'' (referee
        D9), defining every unit and saying which one enters which
        population-level probability.  The overlapping definitions in
        Sec. 3 are removed in the same edit, so this is nearly free.
  S7-2  The false-alarm arithmetic worked through in the appendix
        (referee C2): the correlation-corrected trial count derived rather
        than asserted, the residual excess decomposed and tested, and the
        factor of 16 shown and connected to N_eff.
  S7-3  CP-72 2713's chronology (referee C4a) and what a positive
        recurrence would have had to look like (C4b).
  S7-4  The polarisation census (referee C5).
  S7-5  The molecular mask reframed as our choice, not ALMA's limit
        (referee D5), in the discussion and the conclusions.
  S7-6  One explicit warning sentence against misquoting the conditional
        searched-domain transmitter fraction (referee C6).
  S7-7  Which configuration axes dominate the mismatch (referee C, minor).
  S7-8  A summary sentence at the head of the AU Mic appendix, the
        ``wholly unsearched'' qualification, and the ``stared at the
        nearest stars'' phrasing (referees C and D, minor).
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------ S7-1
sub(r"""Throughout, a \emph{star} is one catalogue entry and a \emph{system}
the set of entries bound to it; a \emph{target/band} dataset is one
star in one ALMA band; an \emph{execution block} (EB) one archival
observation; and a \emph{window}
is one spectral window of one execution block. This gives \NCensus{} unique target stars, processed nearest-first.""",
    r"""Units are defined in \S\ref{sec:units}. This gives \NCensus{} unique
target stars, processed nearest-first.""")

sub(r"""\subsection{The search statistic, and the words used for its output}
\label{sec:statistic}""",
    r"""\subsection{Statistical units and independence}
\label{sec:units}

@@PARA@@Six units appear below and they are not interchangeable, so we fix
them here and say which one carries which probability. A \emph{catalogue
entry} is one star as SIMBAD designates it, \NStars{} of them searched; a
\emph{physical system} is the set of entries gravitationally bound together,
\NSystems{} of them, seven designation-linked pairs accounting for the
difference. A \emph{target/band} dataset is one entry in one ALMA band,
\NStarBands{} in all. An \emph{execution block} is one archival observation,
\NEB{} searched, and it is the unit that shares weather, calibration and
correlator setup. A \emph{spectral window} is one window of one execution
block: \NWindows{} catalogue rows, which reduce to \NDistinctDatasets{}
distinct (execution block, window) datasets once repeated archive products are
collapsed. An \emph{independent frequency trial} is neither of those: within a
window the channel$\times$drift grid is oversampled on both axes, so its
\CellsWinMin--\CellsWinMax{} cells carry about a factor \FaOverDerived{} fewer
independent trials than cells (Appendix~\ref{app:falsealarm}). An
\emph{independent epoch} is a separate execution block at the same tuning, and
blocks of one scheduling block executed on one night are not independent
epochs in any useful sense.

@@PARA@@Which unit enters a population-level statement therefore depends on
the statement. Per-window rank probabilities are conditional on the window and
use no denominator at all. The survey-level flag expectation uses \NWindows{}
windows, which is conservative because the \NDistinctDatasets{} distinct
datasets are the smaller number and because windows within a block are
correlated; \textbf{\NWindows{} windows are not \NWindows{} independent
trials}, and no probability here should be read as though they were. Anything
about how common transmitters are must use \NSystems{} systems, never
\NStars{} entries and never \NWindows{} windows. Anything about persistence
uses epochs, of which most stars here have one.

@@PARA@@\subsection{The search statistic, and the words used for its output}
\label{sec:statistic}""")

# ------------------------------------------------------------------ S7-2
sub(r"""The control ensembles calibrate this empirically, no Gaussian
assumption surviving. The same arithmetic on each window's \NCtrl{}
controls predicts \NCtrlWinExp{} of the \NWindows{} windows carrying at
least one control above $5\sigma$; \NCtrlWinObs{} do, agreeing to
\CtrlWinAgreePct{} per cent. The observed per-window
control maxima track the iid-Gaussian prediction for
$\NCtrl\times n_{\rm cells}$ trials at a median ratio of
\CtrlMaxRatioMed{} (5th--95th percentile
\CtrlMaxRatioLo--\CtrlMaxRatioHi), separately in both classes: fine
median observed control maxima \CtrlMedFine{} against an expected maximum
\FaPredFine, coarse \CtrlMedCoarse{} against \FaPredCoarse. That agreement is partly bookkeeping:
$n_{\rm cells}$ counts grid cells, not independent trials, and both axes are
oversampled, in frequency by the Hanning correlation
($\rho_1=\HanRhoOneFrac$, Appendix~\ref{app:conventions}) and in drift by a
grid whose adjacent trials differ by about half a channel over the track.
Dividing the trial count by a combined factor of \FaOverCount{} lowers the
predictions to \FaPredFineCorr{} and \FaPredCoarseCorr, leaving a
$+\FaExcessFine$ and $+\FaExcessCoarse$ per cent excess at the controls in the
two classes independently. Mild non-Gaussianity of that size is exactly why
the operative statement is the empirical rank and not the Gaussian budget. The
residual window-level factor \CrossWinRatio{} at the star against
\CtrlWinRatio{} at the controls is the closest measurement of
position-specific excess at the phase centre the release affords. It is
marginal, and the crossing list is dominated by CO($2{\to}1$) at
230.5\,GHz toward disc hosts, the expected astrophysical reading. The
operative false-alarm statement remains the rank against the control
ensemble.""",
    r"""The control ensembles calibrate this empirically, no Gaussian assumption
surviving. The same arithmetic on each window's \NCtrl{} controls predicts
\NCtrlWinExp{} of the \NWindows{} windows carrying at least one control above
$5\sigma$; \NCtrlWinObs{} do, agreeing to \CtrlWinAgreePct{} per cent. The
observed per-window control maxima track the iid-Gaussian prediction for
$\NCtrl\times n_{\rm cells}$ trials at a median ratio of \CtrlMaxRatioMed{}
(5th--95th percentile \CtrlMaxRatioLo--\CtrlMaxRatioHi), separately in both
classes: fine median observed control maxima \CtrlMedFine{} against an
expected maximum \FaPredFine, coarse \CtrlMedCoarse{} against \FaPredCoarse.

@@PARA@@That agreement is partly bookkeeping, because $n_{\rm cells}$ counts
grid cells and not independent trials, and it is worth doing the arithmetic
rather than asserting a correction. On the frequency axis ALMA's online
Hanning smoothing correlates neighbouring channels at
$\rho_1=\HanRhoOneFrac$ and $\rho_2=\HanRhoTwo$
(Appendix~\ref{app:conventions}), so the variance of a sum over $n$ channels
exceeds $n$ by $1+2\rho_1+2\rho_2=\FaFreqOver$ and that many grid channels
carry one channel's worth of independent information. On the drift axis the
grid is deliberately oversampled at two steps per channel of traverse over the
track, so adjacent trials share nearly all their integrations and count
\FaDriftOver{} for one. The axes are independent of each other, so the
combined over-count is $\FaFreqOver\times\FaDriftOver=\FaOverDerived$.
Dividing $n_{\rm cells}$ by it lowers the predicted maxima from \FaPredFine{}
to \FaPredFineCorr{} in the fine class and from \FaPredCoarse{} to
\FaPredCoarseCorr{} in the coarse one, against \CtrlMedFine{} and
\CtrlMedCoarse{} observed: a residual $+\FaExcessFine$ and
$+\FaExcessCoarse$ per cent, in the two classes independently. Mild
non-Gaussianity of that size is exactly why the operative statement is the
empirical rank and not the Gaussian budget.

@@PARA@@The same correction disposes of most of the on-star cell excess. Of
the factor \CellsRestOverExpect{} above, the part contributed within a
crossing window is \CellsPerCrossObs{} cells observed against
\CellsPerCrossExp{} expected under independence, a factor
\CellsPerCrossRatio, which is what an over-count of \FaFreqOver{} on the
frequency axis predicts: one real threshold excursion is counted about three
times. What that leaves is the window-level factor, \NHitWindowsRest{} windows
carrying at least one unattributed on-star crossing against \ExpCrossWin{}
expected, a factor \CrossWinRatio{} whose one-sided Poisson probability is
\CrossWinPoisson. Once the four dispositioned windows are set aside, then, the
residual excess is consistent with chance at that level and is not
significant. It is also not zero, it runs one way, and the same sign appears
at the controls, so we report it as an open systematic rather than as settled:
the honest reading is that the crossing list is dominated by CO($2{\to}1$) at
230.5\,GHz toward disc hosts and that a residual excess of on-star chance
crossings at the tens-of-per-cent level cannot be excluded. The operative
false-alarm statement remains the rank against the control ensemble.

@@PARA@@Where the factor of \BonfRankRatio{} comes from is worth stating
explicitly, since it fixes what a single window can ever mean here. The rank
floor is $1/(N_{\rm ctrl}+1)=1/\RankFloor=\RankFloorVal$; the survey-wide
Bonferroni scale is $\BonfAlpha/\BonfNWin=\BonfScaleCalc$; their ratio is
\BonfRankRatio. The annulus cannot close that gap, and correlation widens it:
with $N_{\rm eff}\simeq30$--$43$ independent spatial trials the ensemble's real
rank resolution is \RankEffLo--\RankEffHi{} rather than \RankFloorVal, so the
gap to the Bonferroni scale is a factor \BonfGapEffLo{} to \BonfGapEffHi.
Drawing more control positions would not help either, since the primary beam
bounds the annulus. This is the design's central limitation, and it is why
authentication is left to recurrence and astrophysical attribution.""")

# ------------------------------------------------------------------ S7-3
sub(r"""The redesign postdates the AU~Mic flag by \StatGapDays{} days
and we do not claim otherwise; Appendix~\ref{app:provenance} gives the
chronology with its commit hashes, the algebraic argument that owes nothing to
these data, and the three tests AU~Mic fails.""",
    r"""The redesign postdates the AU~Mic flag by \StatGapDays{} days and we do
not claim otherwise; Appendix~\ref{app:provenance} gives the chronology with
its commit hashes, the algebraic argument that owes nothing to these data, and
the three tests AU~Mic fails. A reader will ask the same question of the other
window that survived, and there the order is the other way round.
CP$-$72~2713 first appears as a flagged window in the very commit that adopts
the symmetric statistic (\StatSymHash, \StatSymDate), so the revision precedes
that flag rather than following it; and because the region maximum for that
window already lay on the star, both statistics return the same $T_\star$
(Table~\ref{tab:bothstats}), so no version of the analysis could have created
it.""")

sub(r"""That is above both the $5\sigma$
trigger and that window's largest control, \CpRecCtrlMax, but the margin is
narrow, so a second \emph{flag} was never assured. What the retirement rests
on is the flux comparison below, which carries no trials factor.""",
    r"""That is above both the $5\sigma$ trigger and that window's largest control,
\CpRecCtrlMax, so the pre-registered criterion had a definite prospective
form: a positive recurrence meant a crossing at the first epoch's channel
\emph{and} drift rate reaching $T\geq5$ in the second block and exceeding all
\NCtrl{} of its controls. The margin between \CpRecExpT{} and \CpRecCtrlMax{}
is narrow, so a second \emph{stage-1 outlier} was never assured even for a
persistent emitter. What the retirement rests on is therefore the flux
comparison below, which carries no trials factor.""")

# ------------------------------------------------------------------ S7-4
sub(r"""The retained
products do not record per-correlation flagging, so we cannot say what
fraction of datasets kept both hands unflagged through QA2; one that lost a
hand would be $\sqrt{2}$ less sensitive than its threshold implies, with
nothing here to catch it.""",
    r"""The archive delivers both parallel hands for all \NPolBoth{} of the
\NPolEB{} searched execution blocks, so the discrimination described next is
available from the existing data and needs no new observation. What the
retained products do not record is per-correlation flagging inside QA2, so we
cannot say what fraction kept both hands unflagged all the way through; one
that lost a hand would be $\sqrt{2}$ less sensitive than its threshold
implies, with nothing here to catch it.""")

# ------------------------------------------------------------------ S7-5
sub(r"""This survey is blind by construction to a transmitter parked
there in the stellar frame, a false-positive control purchased with
\MaskGrossPct{} per cent of gross bandwidth and one physically motivated
class of signal.""",
    r"""This survey is blind by construction to a transmitter parked there in the
stellar frame, a false-positive control purchased with \MaskGrossPct{} per
cent of gross bandwidth and one physically motivated class of signal. The
distinction matters and is easily lost: a carrier deliberately placed on
CO($2{\to}1$) is not undetectable by ALMA, it is unsearched here because this
analysis vetoes that frequency, and the channels themselves are retained in
the release for anyone who will bring independent spatial or time-domain
discrimination to them.""")

sub(r"""\emph{What was found.} Nothing. Four windows raised a
stage-1 spatial screening flag,""",
    r"""\emph{What was found.} Nothing, in the domain searched. The
$\pm\MaskVWidth$\,km\,s$^{-1}$ molecular-line mask is part of that
qualification: it removes \MaskGrossPct{} per cent of gross bandwidth around
transitions whose rest frequencies are exactly the channels a communicator
might choose, and those channels are unsearched by our choice rather than
inaccessible to ALMA. Four windows raised a stage-1 spatial screening flag,""")

# ------------------------------------------------------------------ S7-6
sub(r"""We call it the
\emph{conditional searched-domain transmitter fraction} throughout, and its
framework, demonstration and sensitivity analysis sit in
Appendix~\ref{app:population} as an \emph{illustrative calculation only},
among no headline quantity.""",
    r"""We call it the \emph{conditional searched-domain transmitter fraction}
throughout, and its framework, demonstration and sensitivity analysis sit in
Appendix~\ref{app:population} as an \emph{illustrative calculation only},
among no headline quantity. \textbf{It is not an occurrence rate and should
not be quoted as one.} It is conditional on this survey's frequencies, epochs,
duty cycles and morphology class, on a sample selected by ALMA's own
proposal history, and on a transmitter-frequency prior confined to the
searched islands; under any prior spanning ALMA's tuning range it vanishes.""")

# ------------------------------------------------------------------ S7-7
sub(r"""\CfgAxesZeroOne{} of \CfgNA{} windows
(\CfgAxesZeroOnePct{} per cent) differ on at most one axis and the rest on two
or more, mostly by observing in a different band. Not spanned at all: other
target environments and edge-phased drift grids.""",
    r"""\CfgAxesZeroOne{} of \CfgNA{} windows (\CfgAxesZeroOnePct{} per cent)
differ on at most one axis and the rest on two or more, the largest single
group being the \CfgAxesTwo{} that differ on two. Two axes account for almost
all of the mismatch, band (\CfgBandOut{} windows) and drift-trial count
(\CfgDriftOut), against \CfgChanOut{} for channel width, \CfgOnSrcOut{} for
integration time and \CfgOffOut{} for beam offset. That is the useful reading
for the transfer bracket: what is least well established is the transfer
across band and across drift-grid size, not across integration time or
position in the beam. Not spanned at all are other target environments and
edge-phased drift grids.""")

# ------------------------------------------------------------------ S7-8
sub(r"""Six decades of radio searches cover many thousands of stars yet sample only
\HaystackFrac{} of the haystack of transmitter frequency,
bandwidth, power and duty cycle \citep{Wright2018}. Three gaps persist. The
millimetre and submillimetre regime is essentially unsearched, and everything
above that axis's ${\sim}115$\,GHz upper limit wholly so.""",
    r"""Six decades of radio searches cover many thousands of stars yet sample only
\HaystackFrac{} of the haystack of transmitter frequency, bandwidth, power and
duty cycle \citep{Wright2018}. Three gaps persist. The millimetre and
submillimetre regime is very sparsely searched, and everything above that
axis's ${\sim}115$\,GHz upper limit more sparsely still.""")

sub(r"""In plain terms, ALMA has stared at \NStars{} of the nearest stars as a
by-product of other science, across parts of the millimetre band no
technosignature search had examined.""",
    r"""In plain terms, ALMA has observed \NStars{} nearby stars as a by-product of
other science, across parts of the millimetre band no technosignature search
had examined.""")

sub(r"""\subsection*{AU~Mic: the three tests in full}""",
    r"""\subsection*{AU~Mic: the three tests in full}

@@PARA@@All three converge on the same conclusion: the AU~Mic crossing is not
a candidate under the symmetric statistic, it would not have been one on the
original data either, and nothing about the reclassification required data
that did not already exist when the window was first flagged.""")

fz.apply(TEX, E)
