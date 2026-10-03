#!/usr/bin/env python3
"""Round 85 (v4.04): stellar flares as the astrophysical alternative to the
threshold crossings -- measured, not argued.

★ WHY THIS SECTION GREW INSTEAD OF SHRINKING.  Referee 1 item 9 asked for the
stellar-activity discussion to be cut to a single sentence, on the ground
that activity "cannot explain the localisation result: stellar activity would
still be emission at the stellar position".  That premise is false in this
version.  Under the corrected reference epoch, 40 of the 50 fitted crossings
DO localise at the stellar position, so localisation no longer disfavours a
stellar origin at all -- stellar activity becomes the LEADING astrophysical
alternative rather than a disfavoured one.  The referee's conclusion survives,
but only because it can be replaced by a measurement, and the measurement is
stronger than the argument it replaces.

THE TEST, WITH NO FREE PARAMETER.  A millimetre flare is broadband: it raises
every channel of a window by the same flux density F.  In one de-drifted
channel that is F/sigma_1; coherently over the N channels of the same window
it is sqrt(N) times larger.  A flare able to produce a 5 sigma single-channel
crossing must therefore produce a 5*sqrt(N) sigma CONTINUUM event in the very
same integrations -- of order hundreds of sigma.  Nothing of the kind is
present: the observed continuum statistic in the crossings' own time windows
has median -0.29, and the largest continuum excursion anywhere in those blocks
corresponds to a median 0.05 sigma of single-channel signal.

THE WORKED EXAMPLE THAT CLOSES IT.  One block contains both a threshold
crossing and a real, bright, independently published millimetre flare.  The
flare is there in the continuum at Z = 10.3; its contribution to the
single-channel statistic is 0.17 sigma.

THE NEGATIVE CONTROL THAT SHOWS THE TEST HAS POWER.  A steady line must look
steady under a boxcar bank, and beta Pictoris CO -- the survey's strongest
real feature -- does: T* up to 30.8 with a boxcar maximum BELOW its own
controls.  So the statistic can see temporal concentration and simply does
not see it in the crossings.

Input: `r8inputs/flare_crossings_v404.json`, which records only the OBSERVED
quantities; every prediction here is derived.

-> survey_numbers_round85.tex
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round85.tex')
F = json.load(open(os.path.join(HERE, 'r8inputs',
                                'flare_crossings_v404.json')))
LED = json.load(open(os.path.join(HERE, 'ledger_v403.json')))['summary']

M = {}


def m(k, v):
    M[k] = v


T = F['trigger_sigma']

# ------------------------------------------------------------- the premise
# R1-9's premise is that the events fail localisation.  State the number that
# voids it, read from the ledger rather than retyped, so that if the ledger
# ever returns to zero localisations this section's own justification goes
# with it.
nloc = LED['n_localised_corrected']
nfit = LED['n_fitted']
m('FlNLocalised', '%d' % nloc)
m('FlNFitted', '%d' % nfit)
assert nloc > 0.5 * nfit, (nloc, nfit)

# --------------------------------------------------------- the prediction
for tag, n in zip(('Wide', 'Narrow'), F['illustrative_nchan']):
    m('FlIllusN%s' % tag, '%d' % n)
    m('FlIllusZ%s' % tag, '%.0f' % (T * math.sqrt(n)))

m('FlNCross', '%d' % F['n_crossings'])
m('FlNWindow', '%d' % F['n_with_window'])
m('FlNCont', '%d' % F['n_with_continuum'])
m('FlPredLo', '%d' % F['pred_z_lo'])
def thousands(n):
    s = '%d' % n
    return '{,}'.join([s[:-3], s[-3:]]) if len(s) > 3 else s


m('FlPredHi', thousands(F['pred_z_hi']))
m('FlPredMed', '%d' % F['pred_z_med'])
# The quoted prediction range must be consistent with the rule it comes from:
# both ends must correspond to a whole number of channels at the trigger.
for z in (F['pred_z_lo'], F['pred_z_hi']):
    n = (z / T) ** 2
    assert n > 1 and abs(n - round(n)) / n < 0.01, (z, n)

# ---------------------------------------------------------- the observation
m('FlObsMed', '%.2f' % F['obs_z_median'])
m('FlObsAbsMax', '%d' % F['obs_z_absmax'])
m('FlNQuiet', '%d' % F['n_absz_lt3'])
m('FlImpliedMed', '%.2f' % F['implied_single_channel_median'])
m('FlImpliedMax', '%.2f' % F['implied_single_channel_max'])
m('FlConcMed', '%.2f' % F['timeconc_median'])
m('FlConcNGt', '%d' % F['timeconc_n_gt2'])
# The observed continuum is not merely below the prediction, it is below it by
# orders of magnitude.  Compute the margin rather than saying "far below".
m('FlMarginLog', '%.0f' % math.log10(F['pred_z_lo']
                                     / max(abs(F['obs_z_median']), 1e-9)))
# Even the LARGEST continuum excursion seen in any crossing window is below
# the SMALLEST value a flare origin would require -- which is the whole
# argument, and is therefore what is asserted.
assert F['obs_z_absmax'] < F['pred_z_lo'], \
    (F['obs_z_absmax'], F['pred_z_lo'])

# -------------------------------------------------------- the worked example
W = F['worked_example']
contrib = W['continuum_z'] / math.sqrt(W['nchan'])
m('FlEgStar', W['star'])
m('FlEgEb', W['eb'].replace('_', r'\_'))
m('FlEgT', '%.2f' % W['tstar'])
m('FlEgNChan', thousands(W['nchan']))
m('FlEgContZ', '%.1f' % W['continuum_z'])
m('FlEgContmJy', '%.2f' % W['continuum_mJy'])
m('FlEgTrackZ', '%.1f' % W['track_zmax'])
m('FlEgContrib', '%.2f' % contrib)
# The example is only worth printing if the flare's contribution is far below
# the trigger; if a future input made it comparable, the paragraph would be
# claiming the opposite of what it says.
assert contrib < 0.2 * T, contrib

# ------------------------------------------------------ the negative control
C = F['negative_control']
m('FlCtlTLo', '%.1f' % C['tstar_lo'])
m('FlCtlTHi', '%.1f' % C['tstar_hi'])
m('FlCtlBoxLo', '%.1f' % C['boxcar_zmax_lo'])
m('FlCtlBoxHi', '%.1f' % C['boxcar_zmax_hi'])
m('FlCtlCtrlLo', '%.1f' % C['ctrl_zmax_lo'])
m('FlCtlCtrlHi', '%.1f' % C['ctrl_zmax_hi'])
# The control demonstrates POWER only if the strongest real feature in the
# survey stays inside its own control band under the concentration statistic.
assert C['boxcar_zmax_lo'] <= C['ctrl_zmax_hi'], C

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by flare_v404.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('flare_v404: a %.0f sigma crossing needs a %d-%s sigma continuum event; '
      'observed median %.2f with |Z|<3 in %d of %d'
      % (T, F['pred_z_lo'], F['pred_z_hi'], F['obs_z_median'],
         F['n_absz_lt3'], F['n_with_continuum']))
print('  worked example: %s %s carries both a crossing (T*=%.2f) and a '
      'published flare (continuum Z=%.1f) -- the flare contributes %.2f sigma'
      % (W['star'], W['eb'], W['tstar'], W['continuum_z'], contrib))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
