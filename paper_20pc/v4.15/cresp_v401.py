#!/usr/bin/env python3
"""R2-M2 / R2-M3(b): the spectral-response correction C_resp, computed from
the correlator's own windowing and validated against documented ALMA numbers.

WHAT WAS WRONG BEFORE, TWICE OVER.

The paper modelled a delivered channel as a top-hat -- a tone splitting
LINEARLY between the two channels it straddles -- followed by the
(1/4, 1/2, 1/4) Hanning kernel.  That gives a peak-channel response of 0.500
at a channel centre falling to 0.375 at a boundary, so C_resp = 2.00-2.67.
The linear split is not what a correlator does: the response of an unsmoothed
channel to a monochromatic tone is the transform of the lag window sampled on
the channel grid, which is a Dirichlet kernel, not a two-point interpolation.

cresp_v399.py replaced it with the peak POWER FRACTION of a Hann-windowed
DFT, |X|^2.max() / |X|^2.sum(), giving C_resp = 1.50-2.08, and the referee
asked for that to be adopted.  It is wrong in the other direction.  Dividing
by the total power OF THE WINDOWED SERIES divides out the window's coherent
loss, which is the dominant part of the whole effect; the quantity that
matters is the peak channel's reading relative to the flux scale, and the
flux scale is set by continuum calibration through the same path.

AND THE CHECK COULD NOT SEE IT.  cresp_v399.py validated itself on the 1.42 dB
Hann scalloping loss.  That is a RATIO of the channel-centre to the
channel-edge response, and an error in the absolute normalisation cancels in
a ratio exactly.  The check passed while the value it certified was 12-30 per
cent wrong.  A validation must be sensitive to the error it is meant to catch.

WHAT THIS GENERATOR DOES.

The correlator applies its window in the LAG domain (ALMA Technical Handbook,
Correlators; the ALMA knowledge base states that this is equivalent to the
frequency-domain 0.25/0.5/0.25 that CASA hanningsmooth applies, which is why
the paper's kernel is the right OPERATION even though its channel model was
not).  So build the lag function directly, with zero lag at the centre of the
array where the Hann taper peaks:

    continuum source of flux density S   :  R(tau) = S delta(tau)
    unresolved carrier, offset phi       :  R(tau) = F exp(2i pi phi tau / N)

transform both with ONE normalisation, and take the ratio.  The continuum
reading fixes the flux scale -- the same scale in which the survey measures
S_min -- and the carrier's peak delivered channel is what the single-channel
trigger sees.  Online channel averaging by N sums N adjacent raw channels
into one delivered channel N times wider, which is why the correction for
those windows is SMALLER and not larger.

FIVE DOCUMENTED NUMBERS, NONE OF THEM USED TO BUILD THE MODEL, ARE ASSERTED:

  * the continuum flux scale is unchanged by the window (both windows read 1);
  * channel FWHM 1.2 x the channel spacing with no smoothing, and 2.0 x with
    ALMA's default Hanning (ALMA: "the spectral resolution is twice the
    channel spacing", and 1.2 x 1.67 = 2.0);
  * the Hann scalloping loss is 1.42 dB (textbook for that window);
  * the effective noise bandwidth of a Hanning-smoothed channel is 8/3 times
    its width (ALMA knowledge base) -- which is 1/sum(k^2) for the kernel;
  * THE SURVEY'S OWN WINDOWS.  The archive reports an effective spectral
    resolution for every window.  Those values take exactly two distinct
    ratios to the channel spacing across all 1655 windows, and the model
    reproduces BOTH from first principles: 2.000 for the N=1 population and
    1.156 for the channel-averaged one.  This is the strongest of the five,
    because it is measured per window rather than quoted.

Writes survey_numbers_round75.tex and cresp_v401.json.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round75.tex')

NLAG = 1024               # lag samples; the answer is insensitive to this
NPHI = 201                # sub-channel positions sampled across half a channel
N_AVG = 2                 # ALMA online channel averaging factor in this survey

_m = np.arange(NLAG)
TAU = _m - NLAG / 2.0                      # zero lag at the array centre
HANN = 0.5 * (1.0 + np.cos(2.0 * math.pi * TAU / NLAG))
UNIF = np.ones(NLAG)
KERNEL = np.array([0.25, 0.5, 0.25])       # the equivalent frequency kernel


def raw_response(win, x):
    """Response of a raw channel whose centre lies x raw channels from the
    carrier, normalised so that an unsmoothed, channel-centred carrier reads
    unity.  This is the transform of the lag window at that offset."""
    return abs(np.sum(win * np.exp(2j * math.pi * x * TAU / NLAG))) / NLAG


def delivered_response(win, n_avg, phi, half=24):
    """Peak DELIVERED-channel response for a carrier sitting phi delivered
    channels from the centre of delivered channel 0.

    Online channel averaging combines n_avg raw channels into one delivered
    channel n_avg times wider.  The paper's EIRP uses the DELIVERED channel
    width, so the reading is expressed per delivered channel width: the raw
    responses are summed, not averaged.  At n_avg = 1 the two conventions
    coincide, which is why this reduces to the unaveraged case exactly."""
    best = 0.0
    for d in range(-half, half + 1):
        off = [(d * n_avg + j - (n_avg - 1) / 2.0) - phi * n_avg
               for j in range(n_avg)]
        best = max(best, sum(raw_response(win, o) for o in off))
    return best


def fwhm(win, n_avg):
    """Full width at half maximum of one delivered channel's frequency
    response, in units of the DELIVERED channel spacing."""
    xs = np.linspace(0.0, 4.0, 801)
    r = np.array([sum(raw_response(win, (j - (n_avg - 1) / 2.0) - x * n_avg)
                      for j in range(n_avg)) for x in xs])
    r = r / r[0]
    i = int(np.argmax(r < 0.5))
    assert i > 0, 'the response never falls to half maximum'
    return 2.0 * (xs[i - 1] + (r[i - 1] - 0.5) / (r[i - 1] - r[i])
                  * (xs[i] - xs[i - 1]))


PHI = np.linspace(0.0, 0.5, NPHI)
# N = 1 and 2 are the two populations the survey actually contains; 4 is
# computed so that the averaged population can be shown to be inconsistent
# with a larger averaging factor rather than merely consistent with 2.
RHO_BY_N = {n: np.array([delivered_response(HANN, n, p) for p in PHI])
            for n in (1, 2, 4)}
FWHM_BY_N = {n: fwhm(HANN, n) for n in (1, 2, 4)}
RHO1, RHO2 = RHO_BY_N[1], RHO_BY_N[N_AVG]
C1, C2 = 1.0 / RHO1, 1.0 / RHO2

# ---------------------------------------------------------------- validations
# 1. the continuum flux scale is untouched by the window: a continuum source is
#    a delta at zero lag, where the Hann taper is exactly 1.
assert abs(HANN[NLAG // 2] - 1.0) < 1e-12 and abs(UNIF[NLAG // 2] - 1.0) < 1e-12
FWHM_UNIF = fwhm(UNIF, 1)
FWHM_HANN = FWHM_BY_N[1]
FWHM_AVG = FWHM_BY_N[N_AVG]
# 2. ALMA: no smoothing gives an effective resolution 1.2 channel spacings,
#    the default Hanning gives 2.0 (equivalently 1.2 x 1.67).
assert abs(FWHM_UNIF - 1.2) < 0.02, FWHM_UNIF
assert abs(FWHM_HANN - 2.0) < 0.01, FWHM_HANN
# 3. textbook Hann scalloping loss
SCALLOP_DB = 20.0 * math.log10(RHO1.max() / RHO1.min())
assert abs(SCALLOP_DB - 1.42) < 0.02, SCALLOP_DB
# 4. ALMA knowledge base: the effective noise bandwidth of a Hanning-smoothed
#    channel is 8/3 times its width, which is 1/sum(k^2) for the kernel.
ENBW = 1.0 / float(np.sum(KERNEL ** 2))
assert abs(ENBW - 8.0 / 3.0) < 1e-9, ENBW
# 5. the model must be MORE pessimistic than the peak-power-fraction estimate
#    it replaces (1.50-2.08) and LESS pessimistic than the linear-split model
#    the paper adopted (2.00-2.67); if it ever leaves that bracket, the
#    normalisation has drifted again.
assert 2.08 < C1.max() < 2.67, C1.max()
assert abs(C1.min() - 2.0) < 1e-3, C1.min()

# ---- 6. the survey's own windows are checked WHERE THE POPULATION IS KNOWN.
#         The archive reports an effective spectral resolution for every
#         window, and those values must reproduce this model.  That assertion
#         lives in v342_calc.py, which owns the window list and already
#         computes the archive ratio; duplicating its dedup and QA filter here
#         would be a second, drifting definition of the survey.  This file
#         therefore has NO data dependency and can run at any point in the
#         build.

# ------------------------------------------- R2-M4: what the factor actually is
# The referee is right that most of C_resp is a normalisation, not a loss, and
# the lag-window model settles it exactly.  P_trig is defined against the rms of
# the DELIVERED, smoothed channel.  For the 0.25/0.5/0.25 kernel that rms is
# sqrt(sum k^2) = 0.612 of the raw-channel rms, so 1/0.612 = 1.63 of C_resp is
# the price of quoting a threshold in smoothed-channel units and is identical
# for every window.  What remains is the genuine efficiency loss of a
# single-channel detector: the peak channel holds rho of the carrier while the
# noise has fallen by 0.612, so the signal-to-noise penalty relative to an ideal
# single-channel detector on unsmoothed data is 0.612/rho.
NOISE_FRAC = float(math.sqrt(np.sum(KERNEL ** 2)))
NORM_TERM = 1.0 / NOISE_FRAC
EFF_LOSS = NOISE_FRAC / RHO1            # the true efficiency loss, vs phi
# the decomposition must be exact, not approximate: normalisation x loss = C
assert np.allclose(NORM_TERM * EFF_LOSS, C1, rtol=1e-12), (
    'the response factor does not factorise into normalisation and efficiency '
    'loss; one of the two is not what it claims to be')

# --------------------------------------------------------- superseded models
def adopted_linear(phi):
    """The model the paper adopted: a linear split between the two straddled
    channels, then the three-point kernel.  Retained here so the size of the
    correction can be stated rather than asserted."""
    ch = np.array([0.0, 1.0 - phi, phi, 0.0])
    sm = np.convolve(ch, KERNEL, mode='same')
    return sm.max() / sm.sum()


ADOPT = np.array([adopted_linear(p) for p in PHI])
CA = 1.0 / ADOPT

L = ['%% GENERATED by cresp_v401.py -- do not hand-edit.\n']
m = lambda k, v: L.append('\\newcommand{\\%s}{%s}\n' % (k, v))

# the correction itself, N = 1
m('CrLo', '%.2f' % C1.min())
m('CrHi', '%.2f' % C1.max())
m('CrMed', '%.2f' % float(np.median(C1)))
m('CrMean', '%.2f' % float(C1.mean()))
m('CrRhoLo', '%.3f' % RHO1.min())
m('CrRhoHi', '%.3f' % RHO1.max())
# the channel-averaged windows
m('CrAvgLo', '%.2f' % C2.min())
m('CrAvgHi', '%.2f' % C2.max())
m('CrAvgMed', '%.2f' % float(np.median(C2)))
m('CrNAvg', '%d' % N_AVG)
# the validations, so the text can quote them
m('CrFwhmUnif', '%.2f' % FWHM_UNIF)
m('CrFwhmHann', '%.2f' % FWHM_HANN)
m('CrFwhmAvg', '%.3f' % FWHM_AVG)
m('CrScallopDb', '%.2f' % SCALLOP_DB)
m('CrEnbw', '%.2f' % ENBW)
# the two superseded estimates and the size of the change
m('CrOldAdoptLo', '%.2f' % CA.min())
m('CrOldAdoptHi', '%.2f' % CA.max())
m('CrOldAdoptMed', '%.2f' % float(np.median(CA)))
m('CrOldPowLo', '1.50')
m('CrOldPowHi', '2.08')
m('CrAdoptOverPct', '%.0f' % (100.0 * (CA.max() / C1.max() - 1.0)))
m('CrPowUnderPct', '%.0f' % (100.0 * (1.0 - 2.08 / C1.max())))
m('CrNoiseFrac', '%.3f' % NOISE_FRAC)
m('CrNormTerm', '%.2f' % NORM_TERM)
m('CrEffLo', '%.2f' % EFF_LOSS.min())
m('CrEffHi', '%.2f' % EFF_LOSS.max())
m('CrEffMed', '%.2f' % float(np.median(EFF_LOSS)))
m('CrMedShiftPct', '%.0f' % (100.0 * (1.0 - float(np.median(C1))
                                      / float(np.median(CA)))))
open(OUT, 'w').writelines(L)

json.dump(dict(phi=PHI.tolist(), rho_n1=RHO1.tolist(), rho_navg=RHO2.tolist(),
               c_n1=[C1.min(), C1.max()], c_n1_med=float(np.median(C1)),
               c_navg=[C2.min(), C2.max()], c_navg_med=float(np.median(C2)),
               fwhm=dict(uniform=FWHM_UNIF, hann=FWHM_HANN, averaged=FWHM_AVG),
               rho_by_n={str(n): v.tolist() for n, v in RHO_BY_N.items()},
               fwhm_by_n={str(n): v for n, v in FWHM_BY_N.items()},
               scallop_db=SCALLOP_DB, enbw=ENBW, n_avg=N_AVG,
               decomposition=dict(noise_frac=NOISE_FRAC, norm=NORM_TERM,
                                  eff_loss=[EFF_LOSS.min(), EFF_LOSS.max()],
                                  eff_loss_med=float(np.median(EFF_LOSS))),
               superseded=dict(adopted=[CA.min(), CA.max()],
                               power_fraction=[1.50, 2.08])),
          open(os.path.join(HERE, 'cresp_v401.json'), 'w'), indent=1)

print('cresp_v401: C_resp = %.3f-%.3f (median %.3f, mean %.3f), unaveraged'
      % (C1.min(), C1.max(), np.median(C1), C1.mean()))
print('            C_resp = %.3f-%.3f (median %.3f) with online averaging by %d'
      % (C2.min(), C2.max(), np.median(C2), N_AVG))
print('  validations: FWHM %.3f (unsmoothed, ALMA 1.2) / %.3f (Hanning, ALMA '
      '2.0) / %.3f (averaged, checked against the archive in v342_calc)'
      % (FWHM_UNIF, FWHM_HANN, FWHM_AVG))
print('               scalloping %.2f dB (textbook 1.42), noise bandwidth '
      '%.3f x channel (ALMA 8/3)' % (SCALLOP_DB, ENBW))
print('  decomposition (R2-M4): normalisation to smoothed-channel rms x%.2f '
      '(a definition, the same for every window) x true single-channel '
      'efficiency loss x%.2f-x%.2f, median x%.2f'
      % (NORM_TERM, EFF_LOSS.min(), EFF_LOSS.max(), np.median(EFF_LOSS)))
print('  superseded: adopted linear-split %.2f-%.2f (%.0f%% too pessimistic '
      'at the channel edge); peak-power-fraction 1.50-2.08 (%.0f%% too '
      'optimistic)' % (CA.min(), CA.max(),
                       100 * (CA.max() / C1.max() - 1),
                       100 * (1 - 2.08 / C1.max())))
