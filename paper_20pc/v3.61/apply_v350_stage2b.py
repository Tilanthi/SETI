#!/usr/bin/env python3
"""v3.50 stage 2b: shorten the beta Pic and HD 48370 dispositions to one
concise paragraph each plus the existing table (referee A12).

What leaves the main text goes to Appendix app:provenance (stage 2c), not
to the bin: the velocity-frame audit, the flux-ratio and excitation
argument, the stellar-flare suppression argument and the [C I] tuning
check are all kept, and the appendix is built to receive them.  What is
actually deleted is duplication: the same velocity concordance was stated
three times across the two paragraphs and the frame-audit table caption.

The debris-disc prior paragraph moves to the Discussion, where referees
A14 and B5 want a dedicated sample-bias paragraph, instead of sitting
inside the beta Pic disposition.
"""
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


# ---------------------------------------------------------------- beta Pic
sub(r"""Two of the four flagged windows are towards $\beta$~Pictoris, a debris
disc with resolved CO emission \citep{Matra2017,Dent2014}: one in Band~3
and one in Band~6 (Table~\ref{tab:flagged}), each offset from its CO rest
frequency by more than the automated one-channel check allowed, which is why
that check missed both. Through the frame chain (Table~\ref{tab:bpicaudit}) the
offsets are one kinematic component, \StelBpicThree{} and
\StelBpicSix\,km\,s$^{-1}$ from stellar systemic, in the
two lowest CO rotational transitions of a system with detected
circumstellar CO. The unflagged Class~\BpRecSixClass{} window at
\FobsBpicSixB\,GHz, a third epoch six years earlier, independently shows CO at
\StelBpicCoarse\,km\,s$^{-1}$: all three epochs and
both transitions lie within \BpicMaxAbsStel\,km\,s$^{-1}$ of systemic, deep
inside the $\pm\MaskVWidth$\,km\,s$^{-1}$ mask. The stage-1 Band~6 window carries \NCrossBpicSix{}
formal $\geq5\sigma$ crossings where a channel-confined carrier admits
one; the retained products do not record whether those channels are
contiguous, so the count sets a floor of \BpWidthSixKms\,km\,s$^{-1}$ on the
feature's extent without measuring it
(Appendix~\ref{app:extended} for the tabulation cap). Peak flux densities of \FluxBpicThree{} and \FluxBpicSix\,mJy per
channel, ratio \FluxRatioBpic, are the right order for this belt's
spatially integrated CO. They are per-beam peaks, the synthesised beams being
\BeamBpicThree{} and \BeamBpicSixFlag\,arcsec on emission resolved in both, and
\citet{Matra2017} find the gas subthermally excited ($T_{\rm exc}=12\pm4$\,K),
so beam dilution and excitation both depress the ratio below optically thin
LTE; and since both channels are far
narrower than the line, the peak per channel is comparable across the two
despite their differing widths.

We attribute both crossings to this kinematically offset CO. Within the frozen
release the validation rests on the velocity chain of
Table~\ref{tab:bpicaudit}, which recovers the whole check list untuned:
frequencies to the frame chain's stated tolerance, velocity concordance across
epochs and transitions, localisation against the control ensemble, and drift
class zero to within the grid.

Attributing the pair to CO does not diminish it. Measured on the operative symmetric
statistic and against the survey background, the Band~3 peak
$T_\star=\BpicBThreeTsym$ is matched or exceeded by
\NCtrlGeBpicBThree{} of the \NWindows{} per-window control maxima
(add-one $p=\BpicBThreeAddOne$ on a denominator of \BpicAddOneDen) and
the Band~6 peak $T_\star=\BpicBSixTsym$ by the same \NCtrlGeBpicBSix{}
(add-one $p=\BpicBSixAddOne$). Those \NCtrlGeBpicBThree{} include this star's own
CO-filled Band~6 ensemble at \BpicCoRingMax, the
\BpicCoRingRank th largest control maximum in the survey.
The alternative needs a transmitter coincidentally placed at matched
offsets from two CO transitions in the same star. Every flagged window,
and the crossing the statistic revision removed, belongs to one
population: $\beta$~Pic, AU~Mic and CP$-$72~2713 are $\beta$~Pictoris
moving-group members with debris discs, and HD~48370 is a disc host
behind a molecular cloud. The searched sample is a debris-disc archive in the
archive's own terms: \NDiskCatStars{} of the \NStars{} stars were observed
under proposals categorised \emph{Disks and planet formation} and
\NDebrisKwStars{} carry the \emph{Debris disks} science keyword
(\NDebrisKwSys{} of \NSystems{} systems). That is the worst case for astrophysical
false positives at millimetre wavelengths, so the flags concentrate where the
foreground is richest.

The same population raises the stellar-emission question directly, and
the search suppresses it twice. Gyrosynchrotron and free-free emission
from chromospheres and coronae are broadband, while the block-median
baseline of \S\ref{sec:statistic} removes everything broader than its
\MedWin-channel passband, ${\sim}32$\,MHz at the fine class, a
fractional bandwidth of ${\sim}10^{-4}$; \citet{MacGregor2020}'s AU~Mic
flares are coherent across the full 8\,GHz. Flares are also
time-confined, so the inverse-variance stack over all integrations
dilutes them. What survives is the multiplicative route of
\S\ref{sec:statistic}, a flare continuum times a spectral calibration
residual, bounded there and measured for CP$-$72~2713 below. The search
is blind to the time axis by construction, and the retained dynamic
spectra are the only handle on it.""",
    r"""Two of the four flagged windows are towards $\beta$~Pictoris, a debris disc
with resolved CO emission \citep{Matra2017,Dent2014}: one in Band~3 and one
in Band~6 (Table~\ref{tab:flagged}). Both sit at the same place in velocity.
Carried through the frame chain, the Band~3 crossing lies \StelBpicThree{}
and the Band~6 crossing \StelBpicSix\,km\,s$^{-1}$ from the stellar systemic
velocity, in the two lowest CO rotational transitions of a star with mapped
circumstellar CO, and a third, unflagged window six years earlier shows the
same component at \StelBpicCoarse\,km\,s$^{-1}$. All three lie within
\BpicMaxAbsStel\,km\,s$^{-1}$ of systemic. Both windows fell outside the
executed one-channel line check, which is why it missed them, and both lie
deep inside the $\pm\MaskVWidth$\,km\,s$^{-1}$ velocity exclusion region
that replaced it. We attribute both crossings to this kinematically offset
CO. The full frame audit, the flux ratio and the excitation argument are in
Appendix~\ref{app:provenance}, with the per-window numbers in
Table~\ref{tab:bpicaudit}.

Attributing the pair to CO does not diminish it. Against the survey
background the Band~3 peak $T_\star=\BpicBThreeTsym$ is matched or exceeded
by \NCtrlGeBpicBThree{} of the \NWindows{} per-window control maxima and the
Band~6 peak $T_\star=\BpicBSixTsym$ by the same number, add-one
$p=\BpicBThreeAddOne$ and $\BpicBSixAddOne$. The alternative reading needs a
transmitter placed by coincidence at matched offsets from two CO transitions
in one star. The flags also concentrate where the astrophysical foreground
is richest: $\beta$~Pic, AU~Mic and CP$-$72~2713 are all $\beta$~Pictoris
moving-group members with debris discs, and HD~48370 is a disc host behind a
molecular cloud (\S\ref{sec:bias}).""")

# --------------------------------------------------------------- HD 48370
sub(r"""The third, towards HD~48370 in Band~6, is the largest excess here in
absolute and the smallest in relative terms: $T_\star=27.10$ against a
control-ring maximum of 26.83, the star exceeding its ring by one per
cent of the statistic. Star and ring rising together is what emission filling the
primary beam looks like. The window sits $-34.2$\,km\,s$^{-1}$
topocentric from CO($J{=}2{\to}1$). The attribution is independently
published: \citet{Cataldi2023} report prominent CO($2{\to}1$) and
$^{13}$CO($2{\to}1$) emission towards HD~48370 at $v_{\rm
bary}\approx41$\,km\,s$^{-1}$, well separated from its
$23.6$\,km\,s$^{-1}$ systemic velocity and noted by them as potential
foreground cloud contamination; our frame chain returns
$v_{\rm bary}=+41.2$\,km\,s$^{-1}$, so we recover it and confirm it
kinematically. Two further checks close the alternative. The same authors
report the HD~48370 disc undetected in both CO and carbon, which excludes the
circumstellar alternative to their sensitivity; and the sight line runs through the outer
Galaxy at $l=214.55^{\circ}$, $b=-3.19^{\circ}$, where a flat rotation curve
($R_{0}=\RzeroKpc$\,kpc, $\Theta_{0}=\ThetaZeroKms$\,km\,s$^{-1}$) reaches the
$+\VlsrHdLsr$\,km\,s$^{-1}$ our own LSR chain measures at a kinematic distance
of \KinDistKpc\,kpc, which nothing local could produce.
The peak is $\FluxHdFour$\,Jy
in one 122-kHz channel with the ring at the same level. The $^{13}$CO($2{\to}1$) window of the same execution block has a
control maximum of \HdThirteenRingMax{} against only \HdThirteenStar{}
at the star, so there is bright $^{13}$CO in the field but not at the
star, as extended foreground emission predicts. The reconstructed annulus
geometry puts that peak \HdThirteenOffset\,arcsec from the star, which against
the window's \HdBeamArcsec-arcsec synthesised beam is
\HdCoOffsetBeams{} beams: the emission is resolved away from the star and
clustered off-centre, with the per-control radii in the released catalogue. The Band~8 tuning says the same thing by omission: all twelve Band~8 windows here belong to
$\eta$~Crv, HD~48370 and HD~61005 and are [C\,\textsc{i}]
$^{3}P_{1}$--$^{3}P_{0}$ (\MaskCIGHz\,GHz) tunings, and HD~48370's
carries a $5.05\sigma$ on-star crossing against a ring maximum of 6.23,
which is not one of the four stage-1 flags because its own ring exceeds
it.
Its crossing channel sits \CIcrossKms\,km\,s$^{-1}$ from
[C\,\textsc{i}], so it is not [C\,\textsc{i}] emission from the disc, the cloud
or the star; its own ring dispositions it as an ordinary noise crossing.
What the window does show is no line at the star in this disc's carbon tuning,
which is what \citet{Cataldi2023} report. The rank statistic identifies nothing here, a
stated limitation of the spatial test.""",
    r"""The third flag, towards HD~48370 in Band~6, is the largest excess here in
absolute terms and the smallest in relative ones, $T_\star=27.10$ against a
control-ring maximum of 26.83. Star and ring rising together is what
emission filling the primary beam looks like. The velocities agree
immediately: \citet{Cataldi2023} report prominent CO($2{\to}1$) towards
HD~48370 at $v_{\rm bary}\approx41$\,km\,s$^{-1}$ and flag it as possible
foreground cloud contamination, and our own frame chain returns
$v_{\rm bary}=+41.2$\,km\,s$^{-1}$ for this crossing, so we recover their
line and confirm it kinematically. Three checks close the circumstellar
alternative. The same authors report the disc itself undetected in CO and in
carbon. The sight line runs through the outer Galaxy, where a flat rotation
curve reaches the measured velocity only at a kinematic distance of
\KinDistKpc\,kpc, which nothing local could produce. And the block's
$^{13}$CO($2{\to}1$) window has a control maximum of \HdThirteenRingMax{}
against \HdThirteenStar{} at the star, so the field carries bright
$^{13}$CO that the star does not, resolved \HdCoOffsetBeams{} synthesised
beams away. Appendix~\ref{app:provenance} gives the Band~8 [C\,\textsc{i}]
tuning check, which says the same thing by omission. The rank statistic
identifies nothing here, a stated limitation of the spatial test.""")

fz.apply(TEX, E)
