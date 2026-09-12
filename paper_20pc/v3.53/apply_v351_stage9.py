#!/usr/bin/env python3
"""v3.51 stage 9: the last compression, and one figure restored.

Referee C8 asks for Figure~\\ref{fig:waterfall} to be enlarged.  Stage 8's
float sweep had shrunk it, which is the opposite of what was asked, so it is
restored to its v3.50 size here and the enlargement is declined in the
response letter with the page budget as the reason.  The space that buys is
found in prose that repeats an appendix.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------- the dwell check
sub(r"""An end-to-end check confirms this through the unmodified pipeline. Injecting a zero-drift, always-on tone into the
calibrated visibilities of a coarse Band~7 window at 1, 3 and 10 times
the per-integration rms and running the released extraction and search
returns $T_\star = 20.5$, $65.3$ and $217.7$, each recovered within one channel of the
injection and flagged as a detection. For 639
integrations the ideal coherent gain is $\sqrt{639}=25$, so a carrier at
the per-integration noise level should reach ${\sim}25\sigma$: the
measured 20.5 is that, less weighting and flagging losses.""",
    r"""An end-to-end check confirms this through the unmodified pipeline.
Injecting a zero-drift, always-on tone into the calibrated visibilities of a
coarse Band~7 window at 1, 3 and 10 times the per-integration rms returns
$T_\star = 20.5$, $65.3$ and $217.7$, each recovered within one channel of the
injection. The ideal coherent gain over its 639 integrations is
$\sqrt{639}=25$, and the measured 20.5 is that value less weighting and
flagging losses.""")

# ------------------------------------------------------- eps Eri / Sirius B
sub(r"""$\epsilon$\,Eri Band~6 lies beyond the first sidelobe transition, where the
correction reaches $\EpsEriPbLo$--$\EpsEriPbHi\times$ and the Gaussian form
fails, so we \emph{withhold} those \EpsEriNWin{} windows. They enter no number
here and are not in the released catalogue. Under the same nominal rule they
would have covered $\EpsEriEirpLo$--$\EpsEriEirpHi$\,W at \EpsEriDistPc\,pc,
which at the lower end is among the deepest thresholds in the survey; that is
exactly why we decline to quote them on a beam model we cannot defend. Everything retained sits inside
$\PbMaxRoverTheta\,\theta_{\rm PB}$, where the correction stays a bounded
systematic within a valid beam model. Excluding Sirius~B would change neither endpoint of the quoted EIRP range
nor any conclusion, and would move the median by one significant figure,
$\EirpMedWithSirius\to\EirpMedNoSirius\times10^{15}$\,W.
The correction uses the same $\theta_{\rm PB}=\RingPbCoefCode\,\lambda/D$ as
the annulus geometry, the Airy first-null coefficient rather than ALMA's
FWHM of ${\approx}\RingPbCoef\,\lambda/D$, so off-axis thresholds are
optimistic by up to ${\sim}10$ per cent at the largest retained offset,
which is $\PbMaxRoverFwhm$ of a true FWHM.""",
    r"""$\epsilon$\,Eri Band~6 lies beyond the first sidelobe transition, where the
correction reaches $\EpsEriPbLo$--$\EpsEriPbHi\times$ and the Gaussian form
fails, so we \emph{withhold} those \EpsEriNWin{} windows; they enter no number
here and are not in the released catalogue. Under the same nominal rule they
would have covered $\EpsEriEirpLo$--$\EpsEriEirpHi$\,W at \EpsEriDistPc\,pc,
which at the lower end is among the deepest thresholds in the survey, and that
is exactly why we decline to quote them on a beam model we cannot defend.
Everything retained sits inside $\PbMaxRoverTheta\,\theta_{\rm PB}$, where the
correction stays a bounded systematic. The correction uses the same
$\theta_{\rm PB}=\RingPbCoefCode\,\lambda/D$ as the annulus geometry, which is
the Airy first-null coefficient and not ALMA's FWHM of
${\approx}\RingPbCoef\,\lambda/D$, so off-axis thresholds are optimistic by up
to ${\sim}10$ per cent at the largest retained offset.""")

# ------------------------------------------------------- CP-72 recurrence
sub(r"""One qualification travels with this result. The two
blocks are a single night's pair, \CpRecDate, beginning \CpRecUTone{} and
\CpRecUTtwo\,UT, a \CpRecGapMin-minute gap that puts the second measurement
\CpRecStartSepH\,h after the first. That makes the test strong
against the class the scramble null below cannot reach, because a correlator
spur, a fixed-channel bandpass residual or a birdie is at its most
reproducible two hours later in the same configuration and tuning, and none
reproduced. It also constrains persistence across two hours alone, leaving the
duty cycles of Appendix~\ref{app:population} untouched. AU~Mic's two epochs
(\S\ref{sec:aumic}) are ten weeks apart, a different test.""",
    r"""One qualification travels with this result. The two blocks are a single
night's pair, \CpRecDate, the second beginning \CpRecStartSepH\,h after the
first. That makes the test strong against the class the scramble null cannot
reach, since a correlator spur, a fixed-channel bandpass residual or a birdie
is at its most reproducible two hours later in the same configuration and
tuning, and none reproduced; and it makes the test weak against intermittency,
because it constrains persistence across two hours alone and leaves the duty
cycles of Appendix~\ref{app:population} untouched.""")

sub(r"""A non-recurrence is only meaningful if the same machinery can recover a
repeat when one exists. We therefore applied it to emission we already believe in.
Blocks of one observing unit are not independent epochs, and the
de-duplication of \S\ref{sec:sample} took one block per unit. The unit behind the Band~3 flag holds
\BpUnitThreeAvail{} blocks and all \BpUnitThreeDone{} are now searched
unmodified, an exhaustive control. The CO($1\rightarrow0$)
feature is present in every one, at $T_\star=\BpRecThreeTList$, with
\BpRecThreeHitsList{} channels above threshold and the control maximum below
the star throughout (largest \BpThreeRingMax{} against a smallest
$T_\star$ of \BpThreeTmin). Those executions share one
scheduling block within \BpThreeSessionH\,h and are one epoch
repeated.""",
    r"""A non-recurrence is only meaningful if the same machinery can recover a
repeat when one exists, so we applied it to emission we already believe in.
The unit behind the Band~3 flag holds \BpUnitThreeAvail{} blocks and all
\BpUnitThreeDone{} are now searched unmodified, an exhaustive control. The
CO($1\rightarrow0$) feature is present in every one, at
$T_\star=\BpRecThreeTList$, with \BpRecThreeHitsList{} channels above
threshold and the control maximum below the star throughout. Those executions
share one scheduling block within \BpThreeSessionH\,h, so they are one epoch
repeated.""")

# ------------------------------------------------------- detectability (ii),(iii)
sub(r"""\emph{(ii) A continuously drifting
carrier} in a fine 488-kHz channel is the only morphology with a measured
end-to-end recovery curve (Appendix~\ref{app:inject}). A drifting transmitter
above ${\sim}8\times10^{13}$\,W is recovered in \RecTwice{} per cent of trials
with its drift inside the searched ceiling, and \CaseDetFineNow{} systems
reach that depth in Class~A.

\emph{(iii) An intermittent carrier, on for a
quarter of the track,} above ${\sim}2\times10^{14}$\,W is detected toward
\CaseDetDwellNow{} mid-distance systems such as HD~10647 at 17.4\,pc. Recovery
falls rapidly at smaller dwell fractions (Table~\ref{tab:dwell}), and below
$f_{\rm dwell}\sim0.1$ only the nearest windows carry information.""",
    r"""\emph{(ii) A continuously drifting carrier} in a fine 488-kHz channel is the
only morphology with a measured end-to-end recovery curve
(Appendix~\ref{app:inject}): above ${\sim}8\times10^{13}$\,W nominal it is
recovered in \RecTwice{} per cent of trials with its drift inside the searched
ceiling, and \CaseDetFineNow{} systems reach that depth in Class~A.

@@PARA@@\emph{(iii) An intermittent carrier, on for a quarter of the track,}
above ${\sim}2\times10^{14}$\,W is detected toward \CaseDetDwellNow{}
mid-distance systems. Recovery falls rapidly at smaller dwell fractions
(Table~\ref{tab:dwell}), and below $f_{\rm dwell}\sim0.1$ only the nearest
windows carry information.""")

# ------------------------------------------------------- data availability
sub(r"""The machine-readable catalogue,
\texttt{per\_target\_results\_v3.51.csv}, carries \NCatRows{} rows, one per searched window, in \NCatCols{}
columns. Each row gives star name and machine-readable
\texttt{system\_id} (the independent stellar system that is the
statistical unit, seven bound pairs sharing one identifier), distance,
ALMA band and execution block, searched frequency range, native channel
width, on-source time and integration count, per-channel rms, the
nominal EIRP$_{5\sigma}$ threshold with both Hanning-corrected values
(\S\ref{sec:method}), the drift ceiling as a rate and as an
acceleration, the trial drift count, $\eta_{\rm drift}$, $\eta_{\rm
smear}$, resolution and search class, stellar and control peak
statistics with the count of controls at or above the star and the
add-one rank probability, the crossing frequency, the nearest catalogued
transition with its offset in MHz and km\,s$^{-1}$, the full control
geometry (ring centre, $\theta_{\rm PB}$, $r_{\rm in}$, $r_{\rm out}$,
control count, seed) and the disposition, verbatim from
Table~\ref{tab:flagged} and so carrying the CP$-$72~2713 retirement. The
re-searched $\beta$~Pictoris blocks of \S\ref{sec:technosearch} lie outside
this frozen release; their per-block $T_\star$, control maximum, control count,
channel width and epoch ship in the accompanying epoch-extension record.
Four defects disclosed in earlier versions are repaired: HD~139084B is no
longer counted as two systems, so \NSystems{} is the independent-system total;
the empty \texttt{n\_ant} column is removed, per-window antenna counts being
recoverable only from the raw measurement sets; the disposition strings match
Table~\ref{tab:flagged}; and the directory-name sanitisation that stripped the
sign from four designations is undone, so \texttt{star\_name} now reads
LSR~J1835$+$3259, PM~J03433$+$1958, WD~0407$-$179 and BD$+$05~1668.""",
    r"""The machine-readable catalogue,
\texttt{per\_target\_results\_v3.51.csv}, carries \NCatRows{} rows, one per
searched window, in \NCatCols{} columns. Each row gives star name and
machine-readable \texttt{system\_id} (the independent stellar system that is
the statistical unit, seven bound pairs sharing one identifier), distance,
ALMA band and execution block, searched frequency range, native channel width,
on-source time and integration count, per-channel rms, the nominal
EIRP$_{5\sigma}$ trigger with both response-corrected values
(\S\ref{sec:method}), the drift ceiling as a rate and as an acceleration, the
trial drift count, $\eta_{\rm drift}$, $\eta_{\rm smear}$, resolution and
search class, stellar and control peak statistics with the count of controls
at or above the star and the add-one rank probability, the crossing frequency,
the nearest catalogued transition with its offset, the full control geometry
(ring centre, $\theta_{\rm PB}$, $r_{\rm in}$, $r_{\rm out}$, control count,
seed) and the disposition, verbatim from Table~\ref{tab:flagged}. The blocks
searched by the epoch-extension campaign of \S\ref{sec:heldout} lie outside
this frozen release, and their per-block statistics ship in the accompanying
epoch-extension record.""")

fz.apply(TEX, E)

# ----------------------------------------------------- restore Fig. 3 size
src = open(TEX, encoding='utf-8').read()
a = 'width=0.60\\textwidth]{figures/coverage_waterfall'
b = 'width=0.72\\textwidth]{figures/coverage_waterfall'
assert src.count(a) == 1
open(TEX, 'w', encoding='utf-8').write(src.replace(a, b))
print('Fig. 3 restored to 0.72 textwidth (referee C8)')
