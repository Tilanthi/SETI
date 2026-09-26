#!/usr/bin/env python3
"""R2-M5: does the drift-following visibility fit have the power to see a
compact source at the stellar position?  And what does it therefore say?

A null result from a test of unknown power says nothing, and the referee is
right to ask for the power to be demonstrated rather than asserted.  The
demonstration is parameter-free.  The image-plane statistic is a
signal-to-noise ratio at the star, so an event with statistic T_star in a
window whose trigger flux is S_min = 5 sigma corresponds to a flux
S = T_star x S_min / 5; the visibility fit reports its own flux uncertainty
sigma_re in the same units; so a COMPACT SOURCE AT THE STELLAR POSITION of
that flux would return Re/sigma = S / sigma_re.  Nothing is fitted.

★★★ v4.03: THIS GENERATOR'S CONCLUSION IS REVERSED, AND THAT IS THE POINT.

Until v4.02 it read `vistest_v385.json`, the original fit file, in which the
carrier's channel was evaluated at t0 = median(TIME) rather than at the
search's own first retained integration.  On that file the unattributed
events returned at most Re/sigma = 2.47 against an expectation near 6, and
the paper concluded -- in its abstract -- that emission at the stellar
position was "excluded at 3.3-6.1 sigma".

The injection campaign has since shown that the median-time convention
recovers essentially none of an unresolved carrier once its track spans more
than a few channels (epoch_v403.py).  Re-fitted at the correct epoch, the
rank-flagged unattributed crossing towards 61 Vir returns Re/sigma = 5.3,
which is what a compact source at the star producing its trigger would give.
The exclusion is withdrawn.  It was an artefact of the estimator, and this
generator now publishes the numbers that say so rather than the numbers that
were an artefact.

The macros it emits are therefore about POWER only.  No macro here states an
exclusion, and `\VpZMin`, `\VpZMax`, `\VpPWorst` and `\VpUnattSnrMax` are
deliberately NOT redefined: any surviving use of them must fail the
undefined-macro gate rather than print a withdrawn number.

Reads ledger_v403.json (which epoch is adopted for each crossing, and the
Re/sigma there) and visfit_r7_result.json (sigma_re in flux units).  MUST
follow ledger_v403.py.

Writes survey_numbers_round74.tex and tab_vispower_v400.tex.
"""
import csv
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round74.tex')
TAB = os.path.join(HERE, 'tab_vispower_v400.tex')

LED = json.load(open(os.path.join(HERE, 'ledger_v403.json')))
FITS = json.load(open(os.path.join(HERE, 'visfit_r7_result.json')))['fits']
CAT = list(csv.DictReader(open(os.path.join(HERE,
                                            'per_target_results_v3.99.csv'))))


def sig_re(rec):
    """The flux uncertainty of the adopted-epoch fit.  Prefer the evaluation
    at the extraction's own first retained integration, fall back to the one
    at times[0], and only then to the committed fit -- the same order of
    preference the ledger uses for the verdict, so the uncertainty and the
    ratio always come from the same fit."""
    ep = rec.get('epoch') or {}
    for node in (ep.get('exact'), ep.get('first'), rec):
        if isinstance(node, dict) and isinstance(node.get('star'), dict) \
                and node['star'].get('sig_re'):
            return float(node['star']['sig_re'])
    return None


# window key -> trigger flux, from the released catalogue
SMIN = {}
for r in CAT:
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    if r['smin_mJy']:
        SMIN[(r['eb'], round(lo, 3), round(hi, 3))] = float(r['smin_mJy']) / 1e3

BY_EB = {}
for k, v in FITS.items():
    if v.get('status') == 'ok':
        BY_EB.setdefault(v['event']['eb'], []).append(v)

ev = []
for row in LED['rows']:
    if not row['fitted'] or row['adopted'] is None:
        continue
    key = (row['eb'], round(min(row['flo'], row['fhi']), 3),
           round(max(row['flo'], row['fhi']), 3))
    smin = SMIN.get(key)
    if smin is None:
        continue
    # the fit record for this crossing: matched on block AND frequency,
    # because three blocks carry more than one crossing on the same star and
    # a block-only key silently discarded one of each (REFIT_R7 S1).
    cand = BY_EB.get(row['eb'], [])
    rec = None
    if len(cand) == 1:
        rec = cand[0]
    elif row['freq'] is not None:
        rec = min(cand, key=lambda c: abs(c['event']['freq_GHz'] - row['freq']),
                  default=None)
    s = sig_re(rec) if rec else None
    if not s:
        continue
    flux = row['tstar'] * smin / 5.0
    ev.append(dict(display=row['display'], band=row['band'],
                   tstar=row['tstar'], attributed=row['attributed'],
                   screen=row['screen'], chain=row['chain'],
                   obs=row['adopted']['re'], im=row['adopted']['im'],
                   expect=flux / s))

assert ev, 'no crossing has both a trigger flux and an adopted-epoch fit'
UN = [x for x in ev if not x['attributed']]
UNS = [x for x in UN if x['screen']]
assert UNS, ('no unattributed rank-flagged crossing has a fit; the paragraph '
             'this feeds names them individually')

# ★ The check that stops the withdrawn claim being reinstated by accident.
# The old text said the largest Re/sigma at an unattributed event was far
# below the expectation for a real source.  Assert the OPPOSITE of the
# condition that sentence needed, so that if a future refit ever restores it
# the build fails and the wording is revisited deliberately rather than the
# number quietly changing under prose that no longer matches it.
_best = max(UNS, key=lambda x: x['obs'])
assert _best['obs'] > 0.5 * _best['expect'], (
    'the largest Re/sigma among rank-flagged unattributed crossings has '
    'fallen far below what a compact source at the star would give; the '
    'v4.03 text says the visibility fit does NOT exclude these crossings '
    'and would have to be rewritten')

L = ['%% GENERATED by vispower_v400.py -- do not hand-edit.\n']


def m(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


m('VpNEvent', '%d' % len(ev))
m('VpNUnatt', '%d' % len(UN))
m('VpNUnattScr', '%d' % len(UNS))
m('VpExpectLo', '%.1f' % min(x['expect'] for x in UNS))
m('VpExpectHi', '%.1f' % max(x['expect'] for x in UNS))
m('VpExpectMed', '%.1f' % st.median(x['expect'] for x in ev))
m('VpScrObsMax', '%.1f' % _best['obs'])
m('VpScrObsStar', _best['display'])
m('VpScrRatio', '%.2f' % (_best['obs'] / _best['expect']))

with open(TAB, 'w') as fh:
    fh.write('%% GENERATED by vispower_v400.py -- do not hand-edit.\n')
    fh.write('\\begin{tabular}{@{}llrrrrl@{}}\n\\toprule\n')
    fh.write('Star & B & $T_\\star$ & Re$/\\sigma$ & Im$/\\sigma$ & '
             'expected & chain \\\\\n\\midrule\n')
    for x in sorted(ev, key=lambda y: -y['tstar']):
        fh.write('%s & %s & %.2f & $%+.2f$ & $%+.2f$ & %.1f & %s \\\\\n'
                 % (x['display'], x['band'], x['tstar'], x['obs'], x['im'],
                    x['expect'], x['chain']))
    fh.write('\\bottomrule\n\\end{tabular}\n')

open(OUT, 'w').writelines(L)
print('vispower_v400: %d fitted crossings, %d unattributed, %d of those '
      'rank-flagged' % (len(ev), len(UN), len(UNS)))
print('  a compact source at the star producing the trigger would return '
      'Re/sigma = %.1f-%.1f at the rank-flagged unattributed crossings; '
      'the largest observed is %.1f (%s), %.2f of expectation'
      % (min(x['expect'] for x in UNS), max(x['expect'] for x in UNS),
         _best['obs'], _best['display'], _best['obs'] / _best['expect']))
