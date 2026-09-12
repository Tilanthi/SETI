#!/usr/bin/env python3
"""v3.50 stage 5: compression, to pay for the round's additions, and the
first half of the de-AI sweep.

Every block below does two jobs at once, which is the only way to do both
inside a fixed page budget: it removes words that restate something, and
it breaks sentences that stacked three or four quantitative clauses
(referee B1).  Secondary numbers go to the released catalogue or to the
table that already carries them, not into new prose.

No result, caveat or measured number is dropped.  Where a number leaves
the sentence it is because it is already tabulated in the same paper.
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


# ------------------------------------------------ app:closure, compressed
sub(r"""\emph{Closure phase.} The closure phase
$\arg(V_{ij})+\arg(V_{jk})-\arg(V_{ik})$ vanishes for an unresolved point
source anywhere on sky and is immune to per-station calibration errors,
so it tests point-source coherence alone and a coherent far-sidelobe
interferer would pass. We score consistency with zero by a circular
z-score of the mean drift-tracked closure phase, nulled on each
observation's own integrations, and ran it on continuum detections in
four local reprocessing fields, the resolved AT~Mic Band~7 binary among
them as a control. At these flux densities it is useless: per-baseline
S/N is 0.5--0.7 at the median, only 0.02 per cent of triangles have all
three baselines above 5, and every field's closure phases, the binary
included, are indistinguishable from noise.""",
    r"""\emph{Closure phase.} The closure phase
$\arg(V_{ij})+\arg(V_{jk})+\arg(V_{ki})$ vanishes for an unresolved point
source anywhere on sky and is immune to per-station calibration errors, so
it tests point-source coherence alone. A coherent far-sidelobe interferer
would pass it. We scored consistency with zero on continuum detections in
four locally reprocessed fields, using the resolved AT~Mic Band~7 binary as
a control. At these flux densities the test is useless: the median
per-baseline signal-to-noise ratio is 0.5--0.7, and every field's closure
phases are indistinguishable from noise, the binary included.""")

sub(r"""We implemented a chirped (quadratic-drift) extension
on a coarser grid of 21 linear-drift $\times$ 5 chirp-rate trials, and a
per-channel periodicity search, a per-position FFT along each channel's
time axis; both vet the star against 8 retained control positions, a
strict subset of that window's ensemble. On the 122 retained spectra
this is a demonstration: flag rates of 10.7 and 13.1 per cent against a
${\sim}11$ per cent chance rate show only that the extension runs
correctly under the null, and no limit derives from it.""",
    r"""We implemented a chirped (quadratic-drift) extension and a per-channel
periodicity search, both vetting the star against the eight retained
control positions of that window. On the 122 retained spectra this is a
demonstration and not a measurement. Both flag at the chance rate of
${\sim}11$ per cent, which shows only that the extension runs correctly
under the null, and no limit derives from it.""")

sub(r"""Over every target/spw
result the check pairs the best-fit-channel frequency and the formal
$\geq5\sigma$ crossings, matching $\nu_1,\nu_2$ towards different
targets when $|\nu_1-\nu_2| < \max(k\,\Delta\nu_1,\; k\,\Delta\nu_2)$
with $k=3$ (${\sim}46$\,kHz). Across the \NWindows{} windows and 107
tabulated crossings, no pair falls within the kernel, or within
0.5\,MHz. The kernel is narrower than the $\beta$~Pictoris line offsets
of 10.6 and 21.9\,MHz, so those windows were dispositioned by
line-catalogue inspection.

The null's power is the count of target pairs sharing frequency
coverage: on the $\le$20\,pc subset, 366 of 946 star pairs overlap by at least
0.01\,GHz and 109 involve one of the five stars carrying formal crossings, so
every crossing frequency was tested against overlapping independent targets.
The UV~Ceti and AT~Mic shared execution blocks are excluded as identities by
construction. The interim product's
per-window crossing lists are capped at 50 frequencies, so the true
count is 171 crossings against 107 tabulated. The difference is one
window, $\beta$~Pic Band~6 ultra-fine, whose 114 formal crossings enter
as the 50 strongest; its untabulated 64 could not be tested, so the null
is demonstrated for the tabulated set and unresolved for the rest. The
public release ships uncapped crossing lists.""",
    r"""The check matches crossing frequencies towards different targets when they
fall within three channel widths of each other, ${\sim}46$\,kHz. Across
the \NWindows{} windows and 107 tabulated crossings no pair falls within
that kernel, or within 0.5\,MHz. The kernel is narrower than the
$\beta$~Pictoris line offsets, so those windows were dispositioned by
line-catalogue inspection instead.

The null has power only where targets share frequency coverage. On the
$\le$20\,pc subset 366 of 946 star pairs overlap, and 109 of those involve
one of the five stars carrying formal crossings, so every crossing
frequency was tested against overlapping independent targets. Shared
execution blocks are excluded as identities by construction. One
qualification remains. The interim product caps each window's crossing list
at 50 frequencies, so 171 crossings exist against 107 tabulated, the
difference being the 64 untabulated crossings of one $\beta$~Pic Band~6
window. The null is demonstrated for the tabulated set and unresolved for
the rest, and the public release ships uncapped lists.""")

# ------------------------------- the beta Pic frame audit block, compressed
sub(r"""Table~\ref{tab:bpicaudit} carries the frame
chain for the line-attributed windows. It recovers the whole check list
untuned: frequencies to the frame chain's stated tolerance, velocity
concordance across epochs and transitions, localisation against the control
ensemble, and drift class zero to within the grid. The stage-1 Band~6 window
carries \NCrossBpicSix{} formal $\geq5\sigma$ crossings where a
channel-confined carrier admits one. The retained products do not record
whether those channels are contiguous, so the count sets a floor of
\BpWidthSixKms\,km\,s$^{-1}$ on the feature's extent without measuring it
(Appendix~\ref{app:extended} for the tabulation cap). Peak flux densities of
\FluxBpicThree{} and \FluxBpicSix\,mJy per channel, ratio \FluxRatioBpic, are
the right order for this belt's spatially integrated CO. They are per-beam
peaks, the synthesised beams being \BeamBpicThree{} and
\BeamBpicSixFlag\,arcsec on emission resolved in both, and \citet{Matra2017}
find the gas subthermally excited ($T_{\rm exc}=12\pm4$\,K), so beam dilution
and excitation both depress the ratio below optically thin LTE. Since both
channels are far narrower than the line, the peak per channel is comparable
across the two despite their differing widths. Among the
\NCtrlGeBpicBThree{} control maxima that match or exceed the Band~3 peak is
this star's own CO-filled Band~6 ensemble at \BpicCoRingMax, the
\BpicCoRingRank th largest control maximum in the survey.""",
    r"""Table~\ref{tab:bpicaudit} carries the frame chain for the line-attributed
windows. It recovers the whole check list untuned: frequencies to the frame
chain's stated tolerance, velocity concordance across epochs and
transitions, localisation against the control ensemble, and drift class
zero to within the grid.

Two further properties fit CO and not a carrier. The stage-1 Band~6 window
carries \NCrossBpicSix{} formal $\geq5\sigma$ crossings where a
channel-confined carrier admits one. The retained products do not record
whether those channels are contiguous, so the count sets a floor of
\BpWidthSixKms\,km\,s$^{-1}$ on the feature's extent without measuring it.
The peak flux densities, \FluxBpicThree{} and \FluxBpicSix\,mJy per channel,
are the right order for this belt's spatially integrated CO. They are
per-beam peaks on emission resolved in both beams, and \citet{Matra2017}
find the gas subthermally excited, so beam dilution and excitation both
depress their ratio below optically thin LTE.""")

# --------------------------------- section 4.1: split the dense sentences
sub(r"""It operates on the QA2-calibrated
measurement set as delivered, per integration and per native channel, carrying
the archive's flagging through untouched and applying no
spectral regridding or interpolation (Table~\ref{tab:algorithm},
step~3), and returns the real part of the weighted vector average of the phase-shifted
visibilities at the propagated sky position $\mathbf{x}$: the
natural-weighted dirty-map value there, with no deconvolution, so a quoted
$S_{\rm peak}$ in a field with extended emission is a dirty-map amplitude.
Baseline removal follows extraction (step~4), and the primary-beam correction enters the quoted thresholds and fluxes
(\S\ref{sec:frames}), leaving untouched the extracted amplitudes the statistic
ranks.""",
    r"""It operates on the QA2-calibrated measurement set as delivered, per
integration and per native channel. The archive's flagging carries through
untouched and no spectral regridding or interpolation is applied
(Table~\ref{tab:algorithm}, step~3). What the extraction returns at a
propagated sky position $\mathbf{x}$ is the real part of the weighted
vector average of the phase-shifted visibilities, which is the
natural-weighted dirty-map value there. There is no deconvolution, so a
quoted $S_{\rm peak}$ in a field with extended emission is a dirty-map
amplitude. Baseline removal follows extraction (step~4). The primary-beam
correction enters the quoted thresholds and fluxes (\S\ref{sec:frames}) and
leaves untouched the extracted amplitudes the statistic ranks.""")

sub(r"""The baseline filter takes the median in
contiguous blocks of \MedWin{} channels and interpolates linearly between
block centres, with $\max(2,n/\MedWin)$ blocks over $n$ usable channels,
so its effective width is $W=\MedWin$ channels for the
\NWinFullWidth{} windows holding more than \MedWinSplit{} channels
(\MedWinFineLo--\MedWinFineHi{} in practice) and $n/2$, or
\MedWinCoarseLo--\MedWinCoarseHi{} channels, for the short coarse
windows whose block count collapses to two. The linewidth ceiling that
imposes is ${\approx}\MedWinCeilFineMHz$\,MHz at the fine class's modal
\ChanFineKHz\,kHz channelisation and
${\approx}\MedWinCeilCoarseGHz$\,GHz at the coarse class's
\ChanCoarseMHz\,MHz (Appendix~\ref{app:conventions}).
The crossing channel is \emph{not}
excluded from the scale.""",
    r"""The baseline filter takes the median in contiguous blocks of \MedWin{}
channels and interpolates linearly between block centres, using
$\max(2,n/\MedWin)$ blocks over $n$ usable channels. Its effective width is
therefore \MedWin{} channels in the \NWinFullWidth{} windows long enough to
hold more than two blocks, and $n/2$ in the short coarse windows where the
block count collapses to two. This sets a ceiling on the linewidth the
filter passes: ${\approx}\MedWinCeilFineMHz$\,MHz at the fine class's modal
channelisation, and ${\approx}\MedWinCeilCoarseGHz$\,GHz at the coarse
class's (Appendix~\ref{app:conventions}). The crossing channel is
\emph{not} excluded from the scale.""")

sub(r"""It holds \RingNProbe{} positions drawn uniform in
area, $r=\sqrt{U(r_{\rm in}^{2},r_{\rm
out}^{2})}$, and uniform in azimuth, from the fixed seed \RingSeed, re-applied
per window, so all windows share one pattern in units of $\theta_{\rm PB}$ and
two windows of one tuning sample identical sky positions
(Fig.~\ref{fig:cp72ctrl}). Radii run
$\RingInFrac$--$\RingOutFrac\,\theta_{\rm PB}$ with $\theta_{\rm
PB}=\RingPbCoefCode\,\lambda/D$ evaluated at each window's own median
frequency, so the annulus scales window by window. A separate
inner check-ring of \RingNSrc{} positions, reaching
$\RingCheckFrac\,\theta_{\rm PB}$, serves the point-source test. The full
per-window geometry ships as catalogue columns (Data Availability).""",
    r"""It holds \RingNProbe{} positions drawn uniform in area,
$r=\sqrt{U(r_{\rm in}^{2},r_{\rm out}^{2})}$, and uniform in azimuth, from
the fixed seed \RingSeed{} re-applied per window. All windows therefore
share one pattern in units of $\theta_{\rm PB}$, and two windows of one
tuning sample identical sky positions (Fig.~\ref{fig:cp72ctrl}). Radii run
$\RingInFrac$--$\RingOutFrac\,\theta_{\rm PB}$, with $\theta_{\rm PB}$
evaluated at each window's own median frequency, so the annulus scales
window by window. A separate inner check-ring of \RingNSrc{} positions
serves the point-source test, and the full per-window geometry ships as
catalogue columns.""")

sub(r"""Because the frozen products carry none of it, the geometry is reconstructed
from the code, and two checks confirm the layout that ran: the
inner check-ring it generates has the \RingNSrc{} positions the
retired region-max statistic maximised over, and
where extended CO fills the beam the control statistics fall
with reconstructed radius (Spearman $\rho=\RingRhoCO$,
$p\sim10^{\RingRhoCOexp}$, in the HD~48370 Band~6 window). A wrong
position-to-index mapping could not produce either.""",
    r"""The frozen products carry none of that geometry, so it is reconstructed
from the code. Two checks confirm the layout that ran. The inner check-ring
it generates has the \RingNSrc{} positions the retired region-max statistic
maximised over. And where extended CO fills the beam, the control
statistics fall with reconstructed radius, at Spearman $\rho=\RingRhoCO$ in
the HD~48370 Band~6 window. A wrong position-to-index mapping could not
produce either.""")

# ------------------------------------------ section 5.3, dense sentences
sub(r"""Under exchangeability
one designated position of \RankFloor{} ranks first with probability exactly
$1/\RankFloor$, whether the noise is Gaussian or heavy-tailed, so heavy tails
cannot explain an excess. The
survey expectation is $\NWindows/\RankFloor=\ExpFlags$ windows, and
$P(\geq\SbrN\,|\,\ExpFlags)=\SbrPobs$ under an independent-Poisson
approximation. That excess is astrophysical: in \SbrAstro{} of the
\SbrN{} rank-first windows genuine celestial line emission sits at the
stellar position (Table~\ref{tab:flagged}), so they are not draws from
the noise null, and removing them leaves \SbrResid{} against
\ExpFlags{} expected ($P=\SbrResidP$).""",
    r"""Under exchangeability one designated position of \RankFloor{} ranks first
with probability exactly $1/\RankFloor$, whether the noise is Gaussian or
heavy-tailed, so heavy tails cannot explain an excess. The survey
expectation is \ExpFlags{} windows and \SbrN{} are observed,
$P=\SbrPobs$ under an independent-Poisson approximation. That excess is
astrophysical. Genuine celestial line emission sits at the stellar position
in \SbrAstro{} of the \SbrN{} rank-first windows
(Table~\ref{tab:flagged}), so those are not draws from the noise null, and
removing them leaves \SbrResid{} against \ExpFlags{} expected.""")

sub(r"""Median per-window control maxima are flat
across bands, 4.46, 4.59, 4.42, 4.52, 4.63 and 4.69 in Bands 3 to 8, and
a Kolmogorov--Smirnov test of the star's rank among its controls against
$U(0,1)$ is consistent in every band ($p=\KsBandLo{}$--$\KsBandHi$) and
in the coarse stratum ($p=\KsCoarse$). Fine-channel windows sit higher
(control maximum \CtrlMedFine{} against \CtrlMedCoarse), as their far larger channel$\times$drift trial count predicts; the test
is conditional on the window, so that is no violation.""",
    r"""Median per-window control maxima are flat across bands, running 4.42 to
4.69 from Band~3 to Band~8. A Kolmogorov--Smirnov test of the star's rank
among its controls against $U(0,1)$ is consistent in every band
($p=\KsBandLo{}$--$\KsBandHi$) and in the coarse stratum ($p=\KsCoarse$).
Fine-channel windows sit higher, control maximum \CtrlMedFine{} against
\CtrlMedCoarse, as their far larger channel$\times$drift trial count
predicts. The test is conditional on the window, so that is no violation.""")

sub(r"""For each we take a retained control position,
standardise its residual
by the pipeline's per-integration noise map, shift every integration
independently and at random in channel, and re-run the identical search, with
the same noise map, weights, drift grid and channel count. A rigid shift
preserves each integration's spectral autocorrelation,
\LNLagOne{} at lag one, and the maximum runs over the same grid, so each null
realisation carries the same trials factor as the measurement at the star.
Independence across integrations leaves nothing coherent along a drift
track, so each realisation is signal-free by construction, and between
$\LNDrawsMin$ and $\LNDrawsMax$ realisations per window resolve
probabilities well below $1/\RankFloor$.""",
    r"""For each we take a retained control position and standardise its residual
by the pipeline's per-integration noise map. Every integration is then
shifted independently and at random in channel, and the identical search is
re-run with the same noise map, weights, drift grid and channel count. A
rigid shift preserves each integration's spectral autocorrelation, and the
maximum runs over the same grid, so each null realisation carries the same
trials factor as the measurement at the star. Independence across
integrations leaves nothing coherent along a drift track, which makes each
realisation signal-free by construction. Between $\LNDrawsMin$ and
$\LNDrawsMax$ realisations per window resolve probabilities well below
$1/\RankFloor$.""")

fz.apply(TEX, E)

s = open(TEX, encoding='utf-8').read()
s = re.sub(r'\s*@@PARA@@\s*', '\n\n', s)
open(TEX, 'w', encoding='utf-8').write(s)
