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

Input: `r8inputs/flare_crossings_v404.json` for the OBSERVED quantities and
`per_target_results_v3.99.csv` for each crossing window's channel count;
every prediction here is derived from the latter.  The input file's own
`pred_z_*` fields are no longer read: they were predictions recorded in a
file whose provenance line says it records observations only, and they were
formed over searched cells rather than channels.

-> survey_numbers_round85.tex
"""
import csv
import json
import math
import os


# ★★ A HYPHEN IS NOT A MINUS SIGN, and a macro value is typeset verbatim.
# In text mode `-0.29` sets U+002D: short, raised, visibly not a minus.  The
# journal does no copy-editing.  `\ensuremath{-}` is correct in text and in
# maths, so a macro already used inside `$...$` is unchanged and a bare one
# starts printing a minus.  Applied at the EMIT step only: every in-process
# read of M stays numeric, no use site changes, and no value moves -- only
# the glyph.  `minuscheck.py` in `gate.sh` fails the build on a regression.


def _minus(v):
    """A leading hyphen is a minus sign."""
    s = str(v)
    return '\\ensuremath{-}' + s[1:] if s[:1] == '-' else s


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

# ★★★★ N IS A CHANNEL COUNT.  A flare raises every CHANNEL of a window by the
# same flux density, so the coherent gain over one de-drifted channel is
# sqrt(N_chan); the drift trials re-read those same channels and add nothing.
# The frozen input carried 49--4717, and 5*sqrt(N) = 4717 needs N = 890,004 --
# no ALMA window holds that, and the largest here holds 3,769.  That N is a
# SEARCHED CELL count (beta Pic's A002_Xd9668b_Xa9df carries 901,170 cells ->
# 4,746), and the low end's N = 96 is a drift-trial count.  Both ends came off
# the wrong axis, so both are recomputed here from the catalogue's own
# bandwidth and channel width, which is also the only form in which the
# prediction is reproducible from a released product.
#: ★ AND THE CHECK THIS REPLACES COULD NOT FAIL.  It asked that (z/5)^2 be
#: within one per cent of a whole number; at n ~ 890,000 the worst case is
#: 5.6e-7, so the assertion was vacuous at exactly the end that was wrong.
#: The replacement asserts MEMBERSHIP in the measured set of channel counts,
#: which fails when fed anything but a channel count.
_XCAT = [q for q in csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))) if q['crossing'] == 'True']
NCHAN = []
for _q in _XCAT:
    _n = float(_q['bandwidth_Hz']) / float(_q['chanw_Hz'])
    assert abs(_n - round(_n)) < 1e-3, (_q['eb'], _n)
    NCHAN.append(int(round(_n)))
assert NCHAN, 'no crossing window carries a channel count'
PRED = sorted(T * math.sqrt(n) for n in NCHAN)
m('FlNChanLo', '%d' % min(NCHAN))
m('FlNChanWin', '%d' % len(NCHAN))
m('FlPredLo', '%d' % round(PRED[0]))
def thousands(n):
    # ★ THIN SPACE, NOT A COMMA.  The paper's majority convention for a
    # number of five digits or more is a thin space (17 566, 11 680, 10 332,
    # 20 000); `{,}` here was one of only two commas left in the text.
    s = '%d' % n
    return r'\,'.join([s[:-3], s[-3:]]) if len(s) > 3 else s


m('FlPredHi', thousands(round(PRED[-1])))
m('FlNChanHi', thousands(max(NCHAN)))
m('FlPredMed', '%d' % round(PRED[len(PRED) // 2]))
# Both ends must be the prediction for a window that exists in this survey,
# which a cell count or a trial count is not.
for z in (PRED[0], PRED[-1]):
    assert round((z / T) ** 2) in NCHAN, (z, (z / T) ** 2)
assert T * math.sqrt(max(NCHAN)) < F['pred_z_hi'] / 2.0, (
    'the frozen input\'s predicted high end is not reachable from any '
    'channel count in the survey: %s needs N = %.0f against at most %d'
    % (F['pred_z_hi'], (F['pred_z_hi'] / T) ** 2, max(NCHAN)))

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
m('FlMarginLog', '%.0f' % math.log10(PRED[0]
                                     / max(abs(F['obs_z_median']), 1e-9)))
# Even the LARGEST continuum excursion seen in any crossing window is below
# the SMALLEST value a flare origin would require -- which is the whole
# argument, and is therefore what is asserted.  ★ ON THE RECOMPUTED FLOOR,
# NOT THE FROZEN ONE: the corrected low end is HIGHER (the narrowest window
# holds more channels than the drift-trial count the old figure came from),
# so the argument has more margin and not less.
assert F['obs_z_absmax'] < PRED[0], (F['obs_z_absmax'], PRED[0])

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
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, _minus(M[k])))

print('flare_v404: a %.0f sigma crossing needs a %.0f-%.0f sigma continuum '
      'event over N = %d-%d channels; observed median %.2f with |Z|<3 in '
      '%d of %d'
      % (T, PRED[0], PRED[-1], min(NCHAN), max(NCHAN), F['obs_z_median'],
         F['n_absz_lt3'], F['n_with_continuum']))
print('  worked example: %s %s carries both a crossing (T*=%.2f) and a '
      'published flare (continuum Z=%.1f) -- the flare contributes %.2f sigma'
      % (W['star'], W['eb'], W['tstar'], W['continuum_z'], contrib))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
