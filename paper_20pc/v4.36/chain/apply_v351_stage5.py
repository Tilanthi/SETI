#!/usr/bin/env python3
"""v3.51 stage 5: the second round of main-text compression, which funds the
additions of stage 6.

Every cut here removes duplication or detail that the appendices already
carry.  No caveat is dropped and no number disappears: where a sentence goes,
its content is either retained in compressed form or is verbatim in an
appendix already cross-referenced from the same paragraph.

  S5-1  Control-geometry reconstruction: the two confirming checks kept, the
        narration around them dropped.
  S5-2  The off-centre control paragraph, compressed.
  S5-3  The rank-floor paragraph, compressed.
  S5-4  The annulus-variance paragraph, compressed now that the measurement
        of \\S\\ref{sec:rsigma} carries the argument.
  S5-5  The drift-rate range, compressed; every ceiling and caveat kept.
  S5-6  The primary-beam paragraph in Sec. 4.2, compressed.
  S5-7  The dwell campaign's two-distinction paragraph and the derived-quantity
        paragraph, compressed.
  S5-8  Sec. 3's five-criterion tree and composition paragraph, compressed.
  S5-9  Sec. 4.1's opening, compressed.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------ S5-1
sub(r"""The frozen products carry none of that geometry, so it is reconstructed from
the code. Two checks confirm the layout that ran. The inner check-ring it
generates has the \RingNSrc{} positions the retired region-max statistic
maximised over. And where extended CO fills the beam, the control statistics
fall with reconstructed radius, at Spearman $\rho=\RingRhoCO$ in the HD~48370
Band~6 window. A wrong position-to-index mapping could not produce either.""",
    r"""The frozen products carry none of that geometry, so it is reconstructed
from the code, and two checks confirm the layout that ran: the inner
check-ring it generates has the \RingNSrc{} positions the retired region-max
statistic maximised over, and where extended CO fills the beam the control
statistics fall with reconstructed radius, at Spearman $\rho=\RingRhoCO$ in
the HD~48370 Band~6 window. Neither would survive a wrong
position-to-index mapping.""")

# ------------------------------------------------------------------ S5-2
sub(r"""Placing controls off-centre costs sensitivity. A star
near the pointing centre sits at primary-beam response ${\approx}1$,
while the annulus samples \RingGainIn{} at $\RingInFrac\,\theta_{\rm
PB}$ falling to \RingGainOut{} at $\RingOutFrac\,\theta_{\rm PB}$,
area-weighted mean \RingGainMean{} (lower on ALMA's actual
$\RingPbCoef\,\lambda/D$ beam). Star and controls are therefore not exchangeable in flux
density, while they remain exchangeable in the signal-to-noise ratio the
statistic actually ranks, because $T(\mathbf{x})$ in Eq.~\ref{eq:tstar} is
formed on uncorrected amplitudes against one noise scale shared by every
position. Extended sky brightness does not cancel.
Smooth emission lives on short baselines, whose phases barely change
under a phase rotation of a few arcsec, so its extracted amplitude is
nearly position-independent inside the beam, and star and annulus rise
\emph{together}, as they do for HD~48370. Emission whose centroid is offset
from the star instead raises particular controls above it, as in the same
star's $^{13}$CO window, whose ring maximum of \HdThirteenRingMax{}
at \HdThirteenOffset\,arcsec stands against \HdThirteenStar{} at the
star (\S\ref{sec:technosearch}). Two asymmetries remain, in opposite
directions. A suppressed control can only make a star-exceeds-ring
outcome more likely under the null, while a multiplicative calibration
error scales with the continuum flux at the extracted position and so
favours the star, where that flux is not zero. The second is bounded
below, and the bound is given with the noise estimator above.""",
    r"""Placing controls off-centre costs sensitivity. A star near the pointing
centre sits at primary-beam response ${\approx}1$ while the annulus samples
\RingGainIn{} at $\RingInFrac\,\theta_{\rm PB}$ falling to \RingGainOut{} at
$\RingOutFrac\,\theta_{\rm PB}$, area-weighted mean \RingGainMean. Star and
controls are therefore not exchangeable in flux density, and they remain
exchangeable in the signal-to-noise ratio the statistic actually ranks,
because $T(\mathbf{x})$ is formed on uncorrected amplitudes against one shared
noise scale. Extended sky brightness does not cancel: smooth emission lives on
short baselines whose phases barely change under a rotation of a few arcsec,
so star and annulus rise \emph{together}, as they do for HD~48370, while
emission offset from the star raises particular controls above it, as in the
same star's $^{13}$CO window (ring maximum \HdThirteenRingMax{} at
\HdThirteenOffset\,arcsec against \HdThirteenStar{} at the star). Two
asymmetries remain and they run in opposite directions: a suppressed control
can only make a star-exceeds-ring outcome more likely under the null, whereas
a multiplicative calibration error scales with the continuum flux at the
extracted position and so favours the star, where that flux is not zero.""")

# ------------------------------------------------------------------ S5-3
sub(r"""Ranking $T_\star$ against \NCtrl{} values fixes the smallest per-window
$p$-value the design can express at $1/\RankFloor=\RankFloorVal$, while a
survey-wide Bonferroni scale over \NWindows{} windows is $\BonferroniThresh$,
smaller by a factor of \BonfRankRatio. \textbf{No single event in this design
can therefore reach survey-wide significance.} The \NCtrl-control design is a
candidate-generation screen and never a significance test. A stage-1 flag
selects a feature for examination and establishes none. The
annulus estimates the local false-alarm rate; it cannot authenticate an
individual event (component~v, \S\ref{sec:technosearch}). The vocabulary for
search output nests strictly (Table~\ref{tab:nomenclature}), and
Table~\ref{tab:algorithm} allows the statistic to be reimplemented from the
main text alone.""",
    r"""Ranking $T_\star$ against \NCtrl{} values fixes the smallest per-window
$p$-value the design can express at $1/\RankFloor=\RankFloorVal$, while the
survey-wide Bonferroni scale over \NWindows{} windows is
$\BonferroniThresh=\BonfAlpha/\BonfNWin$, smaller by a factor of
\BonfRankRatio{} (Appendix~\ref{app:falsealarm}). \textbf{No single event in
this design can therefore reach survey-wide significance.} The
\NCtrl-control comparison is a candidate-generation screen and never a
significance test: a stage-1 spatial outlier selects a window for examination
and establishes nothing about it. Table~\ref{tab:nomenclature} fixes the
vocabulary and Table~\ref{tab:algorithm} allows the statistic to be
reimplemented from the main text alone.""")

# ------------------------------------------------------------------ S5-4
sub(r"""Because $\sigma$ is built from the annulus, it carries no variance that
belongs to the stellar position alone: residual continuum after baseline
removal, deconvolution or self-calibration residuals, and
position-correlated calibration error all concentrate at or near the
phase centre, where the pointed science target sits. The continuum lane
detects 17 of 57 target/bands (Appendix~\ref{app:continuum}), so these
stars are not all blank there. A multiplicative spectral calibration
error carries the same asymmetry and in the unfavourable direction: a
residual bandpass ripple of fractional amplitude $\epsilon$ leaves a
channel-confined artefact of order $\epsilon\,S_{\rm cont}$ at the
extracted position and essentially nothing on the annulus, where the
continuum flux is negligible. The requirement is severe where it matters,
and \S\ref{sec:technosearch} works it through for the one window where it
was tested. The release does not carry
per-target continuum flux densities, so that argument scales from typical
fluxes and bounds no individual window. The sharper test is a direct comparison of the star's own residual variance
against the controls', which the \RsigNCtrl{} retained control spectra per
window support for the broadband scale and not for a channel-confined
artefact; \S\ref{sec:rsigma} makes it and reports both what it settles and
what it leaves open. A second measurement, of the scale's frequency
dependence, comes from the same products. Re-extracting the four flagged
windows'
per-integration spectra and recomputing the scale
within a band around the feature and
excluding the feature itself, gives local-to-global ratios of 0.97
(CP$-$72~2713), 1.29 (HD~48370), 0.93 ($\beta$~Pic~B3) and 1.02
($\beta$~Pic~B6). The global scale is accurate to a few per cent except
towards HD~48370, where the local value sits 29 per cent higher because
that field is filled with CO; rescaling both the statistic and its
ensemble by the local value leaves it flagged ($T_\star=\HdCorrectedT$
against a corrected ring maximum of \HdCorrectedRing), the disposition
already assigned to it. For CP$-$72~2713 the local scale is slightly \emph{lower}, so its excess is if anything
understated and no disposition moves. The retained products keep no
drift-stacked cube, so this tests only the noise scale, and a per-crossing local scale inside the search is an open item
(\S\ref{sec:futurework}). The same estimator runs at the star and at all
\NCtrl{} control positions, so a badly misstated $\sigma$ would displace
the control distribution, and the pseudo-star ranks are uniform in every
band and at both channelisations (\S\ref{sec:technosearch}). The one
departing stratum is the fine-channel one, and that departure is the
four flagged windows themselves.""",
    r"""Because $\sigma$ is built from the annulus, it carries no variance that
belongs to the stellar position alone, and residual continuum after baseline
removal, self-calibration residuals and position-correlated calibration error
all concentrate at or near the phase centre, where the pointed science target
sits. These stars are not all blank there, the continuum lane detecting 17 of
57 target/bands (Appendix~\ref{app:continuum}). A multiplicative spectral
calibration error carries the same asymmetry in the unfavourable direction,
since a residual bandpass ripple of fractional amplitude $\epsilon$ leaves a
channel-confined artefact of order $\epsilon\,S_{\rm cont}$ at the extracted
position and essentially nothing on the annulus. The direct test of the
premise is \S\ref{sec:rsigma}, which compares the star's own residual variance
with the controls' in the four flagged windows and finds them equal to better
than a per cent, and two indirect ones agree with it. Recomputing the scale
locally, within a band around each feature and excluding the feature itself,
gives local-to-global ratios of 0.97 (CP$-$72~2713), 1.29 (HD~48370), 0.93
($\beta$~Pic~B3) and 1.02 ($\beta$~Pic~B6): the global scale is accurate to a
few per cent except towards HD~48370, where the field is filled with CO and
rescaling both the statistic and its ensemble leaves the window flagged
($T_\star=\HdCorrectedT$ against \HdCorrectedRing), which is the disposition
it already has. And because the same estimator runs at the star and at every
control, a badly misstated $\sigma$ would displace the control distribution,
which the uniform pseudo-star ranks exclude. None of this reaches a
per-crossing local scale inside the search, which remains an open item
(\S\ref{sec:futurework}).""")

# ------------------------------------------------------------------ S5-5
sub(r"""so the ceiling is quoted in cross-band-comparable form
$\dot\nu/\nu$: 12--13\,Hz\,s$^{-1}$\,GHz$^{-1}$ is
$\dot\nu/\nu = (1.2$--$1.3)\times10^{-8}$\,s$^{-1}$, i.e.\
$|a_{\rm los}| = 3.6$--$3.9$\,m\,s$^{-2}$ (Eq.~\ref{eq:drift}),
independent of observing
frequency. That is the acceleration at ${\sim}0.04$\,au around a
solar-type star. Earth-motion contributions
($\lesssim0.13$\,Hz\,s$^{-1}$\,GHz$^{-1}$) lie two orders of magnitude
below, subsumed by the grid. The grid itself is uniform in $\dot\nu$,
spanning the searched range in $n_{\rm drift}$ steps (2--1944 across
windows, recorded per window in the released file), so the
worst-case mismatch, a carrier midway between trial rates, leaves a
residual drift that traverses at most \DriftGridFineHalf{} of one
native channel over the longest fine-class track
(\DriftGridCoarseHalf{} over the coarse class), and the
stacked-amplitude loss is bounded by that sub-channel smearing alone,
an order below the recovery slope measured between $5\sigma$ and
$10\sigma$. The injection campaign injected on grid
points; continuous randomisation between them belongs with the
stratified campaign of \S\ref{sec:futurework}.
Very short-period systems lie at the edge of the searched drift range. An
artificial emitter need not be tied to a known planet at all, since a
free-flying platform, rotating structure or deliberately chirped carrier can
accelerate as it chooses, and such emitters fall outside the constraints
reported here without being excluded by them.
These are \emph{apparent} topocentric drift rates, including deliberate
transmitted chirp and acceleration-induced drift, which the survey does
not distinguish, so the constraints concern linear apparent drift within
the searched range only. For circular orbits the ceiling covers a
transmitter co-orbiting an Earth analogue by three orders of magnitude
and Proxima~b comfortably, while TRAPPIST-1\,b
($a_{\rm los}=\OrbAccTrapb$\,m\,s$^{-2}$) sits at it and c
($\OrbAccTrapc$\,m\,s$^{-2}$) reaches it only at modest eccentricity.
Eccentricity raises the periastron value by up to
$(1{+}e)/(1{-}e)^{2}$, $1.9\times$ at $e=0.2$, so borderline cases move
outside the searched domain at modest eccentricity
(Fig.~\ref{fig:accel}).""",
    r"""so the ceiling is quoted in cross-band-comparable form $\dot\nu/\nu$:
12--13\,Hz\,s$^{-1}$\,GHz$^{-1}$ is $(1.2$--$1.3)\times10^{-8}$\,s$^{-1}$,
that is $|a_{\rm los}| = 3.6$--$3.9$\,m\,s$^{-2}$ independent of observing
frequency, the acceleration at ${\sim}0.04$\,au around a solar-type star.
Earth-motion contributions lie two orders of magnitude below and are subsumed
by the grid. The grid is uniform in $\dot\nu$ over $n_{\rm drift}$ steps
(2--1944 across windows, recorded per window), so a carrier midway between
trial rates leaves a residual drift traversing at most \DriftGridFineHalf{} of
a native channel over the longest fine-class track, and the resulting
amplitude loss is an order below the recovery slope measured between
$5\sigma$ and $10\sigma$. Two limits of the model matter more. The rates
searched are \emph{apparent} topocentric ones, so the survey does not separate
a deliberately chirped carrier from an accelerating platform and constrains
only linear apparent drift inside the ceiling; and an emitter need not be tied
to a known planet at all, a free-flying platform or rotating structure
accelerating as it chooses and falling outside these constraints without being
excluded by them. For circular orbits the ceiling covers a transmitter
co-orbiting an Earth analogue by three orders of magnitude and Proxima~b
comfortably, while TRAPPIST-1\,b ($a_{\rm los}=\OrbAccTrapb$\,m\,s$^{-2}$)
sits at it and c ($\OrbAccTrapc$\,m\,s$^{-2}$) reaches it at modest
eccentricity, which raises the periastron value by up to
$(1{+}e)/(1{-}e)^{2}$ (Fig.~\ref{fig:accel}).""")

# ------------------------------------------------------------------ S5-6
sub(r"""Both carrier-lane thresholds and continuum fluxes are corrected for
ALMA's primary-beam response at the star's offset from the phase centre,
negligibly for most targets (median factor \PbMedian, 90th percentile
\PbPninety), but \NPbAboveTwoPct{} of the \NWindows{} retained windows exceed
2 per cent and \NPbAboveTenPct{} exceed 10 per cent, across
\NPbTierStars{} catalogue entries (five designations: the two
HD~139084B rows share one). The largest retained correction is \PbMaxStar{} Band~\PbMaxBand{} at
$\PbMax\times$, which sits at $\PbMaxRoverTheta\,\theta_{\rm PB}$. Sirius~B
spans \PbSirLoPct--\PbSirHiPct{} per cent over its \NSirWin{} windows. The boundary
between a retained bounded correction and a withheld window is whether the
Gaussian beam form is defensible at the offset in question, and the offset by
itself does not decide it.""",
    r"""Both carrier-lane thresholds and continuum fluxes are corrected for ALMA's
primary-beam response at the star's offset from the phase centre, negligibly
for most targets (median factor \PbMedian, 90th percentile \PbPninety), though
\NPbAboveTwoPct{} of the \NWindows{} retained windows exceed 2 per cent and
\NPbAboveTenPct{} exceed 10 per cent. The largest retained correction is
\PbMaxStar{} Band~\PbMaxBand{} at $\PbMax\times$, at
$\PbMaxRoverTheta\,\theta_{\rm PB}$. What decides between a retained bounded
correction and a withheld window is whether the Gaussian beam form is
defensible at the offset in question, and the offset by itself does not decide
it.""")

# ------------------------------------------------------------------ S5-7
sub(r"""Two distinctions apply. The dwell campaign injects into retained
per-integration spectra, after the baseline step, while the end-to-end check
injects into visibilities, before it. And one cell is measured only in part,
the through-pipeline recovery of near-static carriers on Class~A windows. The
earlier claim that the pipeline suppresses persistent carriers is withdrawn.""",
    r"""Two distinctions apply. The dwell campaign injects into retained
per-integration spectra, after the baseline step, while the end-to-end check
injects into visibilities before it; and one cell, the through-pipeline
recovery of near-static carriers on Class~A windows, is measured only in
part.""")

sub(r"""The injected carriers do not
drift, so what is measured across \CompWin{} configurations is the
persistent and partial-dwell, non-drifting class. On Class~B windows
that is the searched class, which therefore carries a survey-threshold
completeness curve. On Class~A windows the searched
class is the drifting carrier, whose curve is still the single
calibration configuration of Appendix~\ref{app:inject}; the fine column
of Table~\ref{tab:compcurve} constrains the near-static cell at the
search stage only and bounds nothing about the transfer error. The quantity $a$
is a derived combination, justified by the form of the statistic and by the
collapse of \CompWin{} configurations onto one curve; it is not measured
independently at every $(A,f_{\rm dwell})$ pair.""",
    r"""The injected carriers do not drift, so what is measured across \CompWin{}
configurations is the persistent and partial-dwell non-drifting class. On
Class~B windows that is the searched class, which therefore carries a
survey-threshold completeness curve; on Class~A windows the searched class is
the drifting carrier, whose curve is still the single calibration
configuration of Appendix~\ref{app:inject}, so the fine column of
Table~\ref{tab:compcurve} bounds nothing about the transfer error. The
quantity $a$ is a derived combination, justified by the form of the statistic
and by the collapse of \CompWin{} configurations onto one curve rather than
measured independently at every $(A,f_{\rm dwell})$ pair.""")

# ------------------------------------------------------------------ S5-8
sub(r"""``Usable public ALMA coverage'' is a five-criterion decision tree,
frozen absent an erratum: (i) at least one public
execution block (EB) whose visibilities have passed ALMA's second-stage
quality assurance (QA2) and cover the star's
epoch-propagated position in the primary beam, with no minimum
integration, sensitivity, antenna count, mosaic-tile count or array
configuration beyond QA2; (ii) that position inside the field's primary beam, the extraction
aborting beyond $2\,\theta_{\rm PB}$ (largest retained offset
$\PbMaxRoverTheta\,\theta_{\rm PB}$, \PbMaxStar, so nothing approaches
the bound; largest retained primary-beam correction $\PbMax\times$,
\S\ref{sec:frames}); (iii) each spectral window admitted
individually, on QA2 vetting alone; (iv) no
programme-category restriction, science, calibration and observatory
projects entering on identical terms; (v) a fixed archive snapshot
date (2026 September~8). No star
or window was excluded by an unlisted criterion, none for short
integration (the shortest retained are 1.0 and 1.5\,min).""",
    r"""``Usable public ALMA coverage'' is a five-criterion decision tree, frozen
absent an erratum: (i) at least one public execution block (EB) whose
visibilities have passed ALMA's second-stage quality assurance (QA2) and cover
the star's epoch-propagated position, with no minimum integration,
sensitivity, antenna count, mosaic-tile count or array configuration beyond
QA2; (ii) that position inside the field's primary beam, the extraction
aborting beyond $2\,\theta_{\rm PB}$ and the largest retained offset being
$\PbMaxRoverTheta\,\theta_{\rm PB}$, so nothing approaches the bound;
(iii) each spectral window admitted individually, on QA2 vetting alone;
(iv) no programme-category restriction, science, calibration and observatory
projects entering on identical terms; and (v) a fixed archive snapshot date
(2026 September~8). No star or window was excluded by an unlisted criterion,
and none for short integration.""")

# ------------------------------------------------------------------ S5-9
sub(r"""The design is one shared archive-ingestion stage feeding two
independent search lanes over the 40\,pc archive-target-complete sample;
Table~\ref{tab:algorithm} gives the data path of the primary lane in
order. For each target we mine, within a bounded budget, all calibrated
(or locally recalibrated) archival execution blocks
covering the star's Gaia-propagated position. Their visibilities feed (i) the
\emph{primary} lane, a Doppler-drift-corrected
spectral-carrier search following \citet{Mason2024} and
\citet{Enriquez2017}, which converts each non-detection into an equivalent
isotropic radiated power limit""",
    r"""The design is one shared archive-ingestion stage feeding two independent
search lanes, and Table~\ref{tab:algorithm} gives the data path of the primary
lane in order. For each target we mine, within a bounded budget, the
calibrated archival execution blocks covering the star's Gaia-propagated
position. Their visibilities feed (i) the \emph{primary} lane, a
Doppler-drift-corrected spectral-carrier search following \citet{Mason2024}
and \citet{Enriquez2017}, which converts each non-detection into an equivalent
isotropic radiated power limit""")

fz.apply(TEX, E)
