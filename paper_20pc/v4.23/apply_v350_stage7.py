#!/usr/bin/env python3
"""v3.50 stage 7: the last of the page debt, taken out of captions and
reference prose that repeats the body.

Captions are prose.  Three of them re-derive, in the caption, a
convention the section above already states; that text goes back to the
section that owns it and the caption keeps what a reader needs to read the
columns.  The frame-audit table drops to \\footnotesize with the rest of
the non-evidence tables.
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


# --------------------------------------------------- tab:flagged caption
sub(r"""$\Delta\nu$ and $\Delta v$ are the offset
of that channel from the nearest \emph{laboratory} rest frequency of the
masked species, topocentric, as $c\,\Delta\nu/\nu_{\rm rest}$ and so
positive when the observed frequency exceeds the rest frequency; the
$\pm\MaskVWidth$\,km\,s$^{-1}$ mask applies in the stellar frame after
the conversion chain of Appendix~\ref{app:conventions}, and the repaired
mask of \S\ref{sec:linecost} changes no row. The frozen mask stored rest
frequencies rounded to \MaskRestRoundMHz\,MHz, so the released offset
column reads \CatCOerrMHz\,MHz (\CatCOerrKms\,km\,s$^{-1}$) smaller than
the values here for CO($1{\to}0$). The HD~48370 row is the limiting case, a near-tie of rank
dispositioned by velocity coincidence with independently published
emission (\S\ref{sec:technosearch}).}""",
    r"""$\Delta\nu$ and $\Delta v$ are the topocentric offset of that channel from
the nearest \emph{laboratory} rest frequency of the masked species, so a
positive value means the observed frequency exceeds the rest frequency.
The repaired mask of \S\ref{sec:linecost} changes no row. The HD~48370 row
is the limiting case, a near-tie of rank dispositioned by velocity
coincidence with independently published emission.}""")

# ------------------------------------------------- tab:bpicaudit caption
sub(r"""\centering
\small
\caption{Line-attribution audit of the three line-attributed windows
(first three rows) and the Class~A $\beta$~Pictoris Band~6 window at
230.528134\,GHz, which carries no stage-1 flag yet shows the same CO
component, through the frame chain of \S\ref{sec:frames}. Topocentric
offsets are observed
minus catalogued rest frequency as $c\,\Delta\nu/\nu_{\rm rest}$ (CO $J{=}1{\to}0$
\LabCOoneGHz\,GHz, CO $J{=}2{\to}1$ 230.538000\,GHz,
\citealt{Pickett1998}; the frozen mask's own entries, rounded to
\MaskRestRoundMHz\,MHz, are not used here), so a negative offset means
the observed frequency lies below rest; the barycentric correction
is the Earth-ephemeris term at the execution-block mid-time (block uids
in the machine-readable release). The AU~Mic systemic velocity is
catalogued (SIMBAD, \emph{Gaia}~DR2, \citealt{Fouque2018}). For
$\beta$~Pictoris we adopt the
$v_{\rm sys}=\VsysBpic\pm\VsysBpicErr$\,km\,s$^{-1}$ used by
\citet{Matra2017} rather than the \emph{Gaia}~DR3 catalogue value of
$+16.84$\,km\,s$^{-1}$ \citep{GaiaDR3}: the star is A6V with
$v\sin i\simeq130$\,km\,s$^{-1}$, inside the hot-star template regime
in which DR3 radial velocities carry a known systematic
\citep{Blomme2023}.}""",
    r"""\centering
\footnotesize
\caption{Line-attribution audit through the frame chain of
\S\ref{sec:frames}: the three line-attributed windows, and the Class~A
$\beta$~Pictoris Band~6 window that carries no stage-1 flag yet shows the
same CO component. Topocentric offsets are observed minus catalogued
laboratory rest frequency \citep{Pickett1998}, so a negative offset means
the observed frequency lies below rest. The barycentric correction is the
Earth-ephemeris term at the execution-block mid-time. The AU~Mic systemic
velocity is catalogued \citep{Fouque2018}. For $\beta$~Pictoris we adopt
$v_{\rm sys}=\VsysBpic\pm\VsysBpicErr$\,km\,s$^{-1}$ \citep{Matra2017}
rather than the \emph{Gaia}~DR3 value of $+16.84$\,km\,s$^{-1}$
\citep{GaiaDR3}, because the star is an A6V rotator inside the hot-star
template regime in which DR3 radial velocities carry a known systematic
\citep{Blomme2023}.}""")

# ----------------------------------------------- app:conventions, tightened
sub(r"""\emph{Channel widths, and the instrumental response.} These come from
the measurement sets' own spectral window tables (CHAN\_WIDTH). Earlier
versions read a missing ``EFFECTIVE\_BANDWIDTH'' column as evidence of
no online spectral averaging; MS~v2 defines no such column, so the check
is withdrawn, and with it the claim that the quoted channelisations are
noise bandwidths.

ALMA applies online Hanning smoothing by default, so the spectral
response is ${\sim}2$ channels wide and neighbouring channels are correlated.""",
    r"""\emph{Channel widths, and the instrumental response.} These come from the
measurement sets' own spectral window tables (CHAN\_WIDTH). Earlier
versions read a missing ``EFFECTIVE\_BANDWIDTH'' column as evidence of no
online spectral averaging; MS~v2 defines no such column, so that check is
withdrawn, and with it the claim that the quoted channelisations are noise
bandwidths.

ALMA applies online Hanning smoothing by default, so the spectral response
is ${\sim}2$ channels wide and neighbouring channels are correlated.""")

sub(r"""\emph{Linewidth convention.} The statistic is the single-channel
flux density after drift correction, so the quoted EIRP$_{5\sigma}$
applies to any transmitter narrower than the native channel, flat in the
assumed linewidth, with two sub-channel qualifications. Flatness is exact only for a centred tone, a boundary-straddling one
splitting its power between two channels at worst by a factor of two;
and the channel-to-channel transition follows the correlator's passband
shape, which the frozen products do not retain, so flatness is a
channel-centred idealisation good to tens of per cent. Thresholds therefore carry a
sub-channel-position systematic of that size, a randomly placed tone
keeping a mean 0.75 of its power in the stronger channel, and EIRP
values are quoted to two significant figures.""",
    r"""\emph{Linewidth convention.} The statistic is the single-channel flux
density after drift correction, so the quoted EIRP$_{5\sigma}$ applies to
any transmitter narrower than the native channel and is flat in the assumed
linewidth. Two sub-channel qualifications attach. Flatness is exact only
for a centred tone, a boundary-straddling one splitting its power between
two channels at worst by a factor of two. And the channel-to-channel
transition follows the correlator's passband shape, which the frozen
products do not retain. Thresholds therefore carry a sub-channel-position
systematic of tens of per cent, and EIRP values are quoted to two
significant figures.""")

sub(r"""The \NSmearLo{} windows with
$\eta_{\rm smear}<0.99$, generated from the released catalogue as star,
band, ($\eta_{\rm smear}$, threshold multiplier): \SmearList. The
remaining \NSmearOk{} agree with their nominal thresholds to better than
1 per cent (compounding the worst smearing penalty with the worst
Hanning factor gives $\times\CompoundWorst$ on the nominal threshold for
those five windows; no released column carries the product). The $\mathrm{sinc}(\pi\Delta/2)$ form is the transform of a
tone swept uniformly across $\Delta$ channels within one integration,
evaluated at the peak channel, and is the conservative reading: a pure
occupancy argument would retain $\min(1,1/\Delta)$, giving 1.0 rather
than 0.64 at $\Delta=1$.""",
    r"""The \NSmearLo{} windows with $\eta_{\rm smear}<0.99$, as star, band,
($\eta_{\rm smear}$, threshold multiplier), are \SmearList. The remaining
\NSmearOk{} agree with their nominal thresholds to better than 1 per cent.
Compounding the worst smearing penalty with the worst Hanning factor gives
$\times\CompoundWorst$ on the nominal threshold for those five windows, and
no released column carries that product. The $\mathrm{sinc}(\pi\Delta/2)$
form is the conservative reading: a pure occupancy argument would retain
$\min(1,1/\Delta)$, giving 1.0 rather than 0.64 at $\Delta=1$.""")

# ------------------------------------------------ app:falsealarm, tightened
sub(r"""The remaining \CellsObsRest{} cells, over
\NHitWindowsRest{} windows, stand against the \CellExpect{} expected, a
factor \CellsRestOverExpect{} that is the product of two, only the
second of them correlation. Correlation cannot move the expected
\emph{number} above $5\sigma$, which is $Np$ whatever the correlation;
it moves the clumping. Summing
$1-(1-2.87\times10^{-7})^{n_{\rm cells}}$ over the \NWindows{} windows
predicts \ExpCrossWin{} windows carrying at least one on-star crossing
against the \NHitWindowsRest{} observed, a factor \CrossWinRatio{} at
Poisson $p=\CrossWinPoisson$; within a crossing window the iid
expectation is \CellsPerCrossExp{} cells against \CellsPerCrossObs{}
observed, a factor \CellsPerCrossRatio, and that one is channel
adjacency. The two multiply to \CellsRestOverExpect. The budget is also almost entirely fine-class:
\CellsFineSci{} of the \CellsTotal{} cells, so \ExpCrossWinFine{} chance
crossings are expected among the \NWinA{} Class~A windows against
\ExpCrossWinCoarse{} among the \NWinB{} Class~B ones, which is why all
\NCrossWin{} crossings are fine windows.""",
    r"""The remaining \CellsObsRest{} cells, over \NHitWindowsRest{} windows, stand
against the \CellExpect{} expected. That factor of
\CellsRestOverExpect{} is a product of two, and only the second is
correlation. Correlation cannot move the expected \emph{number} above
$5\sigma$, which is $Np$ whatever the correlation; it moves the clumping.
Summing the per-window crossing probability predicts \ExpCrossWin{} windows
carrying at least one on-star crossing against \NHitWindowsRest{} observed,
a factor \CrossWinRatio. Within a crossing window the independent
expectation is \CellsPerCrossExp{} cells against \CellsPerCrossObs{}
observed, a factor \CellsPerCrossRatio, and that one is channel adjacency.
The budget is also almost entirely fine-class, which is why all
\NCrossWin{} crossing windows are fine ones.""")

fz.apply(TEX, E)

s = open(TEX, encoding='utf-8').read()
s = re.sub(r'\s*@@PARA@@\s*', '\n\n', s)
open(TEX, 'w', encoding='utf-8').write(s)
