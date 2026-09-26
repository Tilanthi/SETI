#!/usr/bin/env python3
"""The principal candidate ledger: every threshold crossing, and what the
visibility-domain localisation test says about it.

Referee 1 items 1, 2 and 3 and Referee 2 item M1 both require the same thing:
the drift-following, continuum-subtracted visibility fit must be applied to
EVERY threshold crossing rather than only to the windows that passed the
512-control rank, and the outcome must be reported in one table. The rank is
demoted to a released diagnostic column.

THE CRITERION WAS COMMITTED BEFORE THE FITS WERE RUN. It is reproduced from
referee_r6/LOCALISATION_CRITERION.md, written at 2026-09-25T06:59:24Z and
committed before the campaign started at 07:05. A crossing is localised at the
stellar position when all three of

    Re/sigma >= 4 at the star,
    |Im/sigma| < 3,
    Re/sigma strictly above the maximum over the 8 annulus control positions
        and the 4 off-event control frequencies of the same fit,

hold. A crossing that fails any of them is not localised. A crossing that
cannot be fitted is UNTESTABLE and is never silently counted as either. The
thresholds below are literals for exactly that reason: they must not be
recomputed from the data they are applied to.

Inputs, all frozen:
  per_target_results_v3.99.csv   the 56 crossings, with T*, control maximum,
                                 rank-screen flag, line attribution, disposition
  visfit_all_v385.json           the 13 fits made in the original round
  visfit_r6_result.json          the 31 fits of the round-6 campaign

Writes tab_ledger_v401.tex and survey_numbers_round76.tex.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the committed criterion.  Do not derive these from the data. --------
RE_MIN = 4.0
IM_MAX = 3.0
# The survey's frozen line mask, the same +-50 km/s half-width used throughout
# (v342_calc.py).  It is applied HERE because a crossing is attributed only if
# its nearest transition lies inside the mask.
MASK_KMS = 50.0
CRITERION_COMMIT = 'edfcc0d3d7db'
CRITERION_TIME = '2026-09-25T06:59:24Z'

from star_alias import designation as _display  # noqa: E402

CAT = list(csv.DictReader(open(os.path.join(HERE,
                                            'per_target_results_v3.99.csv'))))
CROSS = [r for r in CAT if r['crossing'].strip().lower() in ('true', '1')]


def wkey(eb, a, b):
    """Window key.  ALWAYS min/max of the two edges: a descending spectral
    window is delivered with flo > fhi, and keying on the raw pair silently
    lost half the windows when this join was first written."""
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


BYKEY = {}
for r in CROSS:
    k = wkey(r['eb'], r['flo_GHz'], r['fhi_GHz'])
    BYKEY.setdefault(k, []).append(r)

# ---- the fits ------------------------------------------------------------
FITS = {}
for src, tag in (('visfit_all_v385.json', 'round 1'),
                 ('visfit_r6_result.json', 'round 6')):
    d = json.load(open(os.path.join(HERE, src)))
    recs = d['fits'] if 'fits' in d else d
    for rec in recs.values():
        if rec.get('status') != 'ok':
            continue
        ev = rec['event']
        k = wkey(ev['eb'], ev['flo_GHz'], ev['fhi_GHz'])
        rec['_round'] = tag
        # a window may be fitted in both rounds; the later one supersedes, and
        # the count below records that it happened rather than hiding it
        FITS.setdefault(k, []).append(rec)

_dup = sum(1 for v in FITS.values() if len(v) > 1)
FIT = {k: v[-1] for k, v in FITS.items()}

_orphan = [k for k in FIT if k not in BYKEY]
assert not _orphan, (
    'these fits match no threshold crossing in the catalogue, so the join is '
    'wrong or the fit was run on a window the survey does not contain: %s'
    % _orphan[:4])


def ctrl_max(rec):
    """Maximum Re/sigma over the 12 controls of this fit: 8 annulus positions
    and 4 off-event frequencies.  They are stored as pos_controls and
    freq_controls; an earlier read of this file looked for a key named
    ctrl_snr_re_max, found nothing, and briefly concluded the control stage had
    not run at all."""
    vals = []
    for key in ('pos_controls', 'freq_controls'):
        for c in rec.get(key) or []:
            if c.get('snr_re') is not None:
                vals.append(float(c['snr_re']))
    for key in ('ctrl_pos_max', 'ctrl_freq_max'):
        if rec.get(key) is not None:
            vals.append(float(rec[key]))
    return max(vals) if vals else None


ROWS = []
for r in CROSS:
    k = wkey(r['eb'], r['flo_GHz'], r['fhi_GHz'])
    rec = FIT.get(k)
    row = dict(star=_display(r['star_name']), band=r['band'], eb=r['eb'],
               freq=(float(r['f_cross_GHz']) if r['f_cross_GHz'] else None),
               chanw=float(r['chanw_Hz']), tstar=float(r['star_snr']),
               ctrl=float(r['ctrl_max_snr']) if r['ctrl_max_snr'] else None,
               screen=r['stage1_flag'].strip().lower() in ('true', '1'),
               line=r['nearest_line'] or '', dispo=r['disposition'] or '',
               loff=(float(r['line_offset_kms'])
                     if r['line_offset_kms'] else None))
    # ATTRIBUTION IS THE MASK, NOT THE PRESENCE OF A NEAREST TRANSITION.
    # `nearest_line` is populated for every one of the 56 crossings -- it is
    # the closest catalogued transition at any velocity, and HD 69830's is
    # -20,255 km/s away. Testing `if r['line']` therefore made the count of
    # unattributed localised crossings identically zero BY CONSTRUCTION: a
    # check that cannot fail is not a check. Apply the frozen mask.
    row['attributed'] = (row['loff'] is not None
                         and abs(row['loff']) <= MASK_KMS)
    if rec is None:
        row.update(fitted=False, re=None, im=None, cmax=None,
                   localised=None, rnd=None)
    else:
        st = rec['star']
        cm = ctrl_max(rec)
        re_s, im_s = float(st['snr_re']), float(st['snr_im'])
        row.update(fitted=True, re=re_s, im=im_s, cmax=cm, rnd=rec['_round'],
                   localised=bool(re_s >= RE_MIN and abs(im_s) < IM_MAX
                                  and (cm is None or re_s > cm)))
    ROWS.append(row)

N_CROSS = len(ROWS)
FITTED = [r for r in ROWS if r['fitted']]
UNTEST = [r for r in ROWS if not r['fitted']]
LOCAL = [r for r in FITTED if r['localised']]
# a localised crossing that the line mask attributes is an astrophysical
# source, correctly identified; one that it does not is a candidate
LOCAL_ATTR = [r for r in LOCAL if r['attributed']]
LOCAL_UNATTR = [r for r in LOCAL if not r['attributed']]
# the mask must be capable of rejecting: if every crossing in the survey were
# inside it, the attribution step would be carrying no information at all
assert any(not r['attributed'] for r in ROWS), (
    'every crossing is inside the line mask, so attribution is vacuous')
SCREEN = [r for r in ROWS if r['screen']]
# the point of the whole exercise: crossings the rank screen REJECTED but the
# physical test accepted, and the reverse
MISSED = [r for r in LOCAL if not r['screen']]
SCREENED_NOT_LOCAL = [r for r in SCREEN if r['fitted'] and not r['localised']]

assert len(FITTED) + len(UNTEST) == N_CROSS
assert N_CROSS == 56, N_CROSS

# ------------------------------------------------------------------ table
def fmt(x, n=2):
    return '--' if x is None else ('%.*f' % (n, x))


ROWS.sort(key=lambda r: (-(r['re'] if r['re'] is not None else -99),
                         r['star']))
L = [r'% GENERATED by ledger_v401.py -- do not hand-edit.',
     r'\begin{tabular}{@{}l@{~}c@{~}r@{~}r@{~}r@{~}r@{~}r@{~}l@{~}l@{}}',
     r'\hline',
     r'Star & B & $\nu$ (GHz) & $T_\star$ & Re/$\sigma$ & Im/$\sigma$ & '
     r'ctrl & Line & Disposition \\', r'\hline']
for r in ROWS:
    if r['fitted']:
        re_, im_, cm = fmt(r['re']), fmt(r['im']), fmt(r['cmax'])
        if r['localised']:
            re_ = r'\textbf{%s}' % re_
    else:
        re_ = im_ = cm = r'\emph{n.f.}'
    L.append('%s & %s & %s & %s & %s & %s & %s & %s & %s \\\\'
             % (r['star'], r['band'],
                fmt(r['freq'], 4), fmt(r['tstar']), re_, im_, cm,
                ((r['line'] or '--') if r['attributed'] else '--').replace('_', r'\_'),
                (r['dispo'] or 'not localised')))
L += [r'\hline', r'\end{tabular}']
open(os.path.join(HERE, 'tab_ledger_v401.tex'), 'w').write('\n'.join(L) + '\n')

# ----------------------------------------------------------------- macros
M = []
m = lambda k, v: M.append('\\newcommand{\\%s}{%s}' % (k, v))
m('LgNCross', '%d' % N_CROSS)
m('LgNFit', '%d' % len(FITTED))
m('LgNUntest', '%d' % len(UNTEST))
m('LgFitPct', '%.0f' % (100.0 * len(FITTED) / N_CROSS))
m('LgNLocal', '%d' % len(LOCAL))
m('LgNLocalAttr', '%d' % len(LOCAL_ATTR))
m('LgNLocalUnattr', '%d' % len(LOCAL_UNATTR))
m('LgNScreen', '%d' % len(SCREEN))
m('LgNMissed', '%d' % len(MISSED))
m('LgNScreenNotLocal', '%d' % len(SCREENED_NOT_LOCAL))
m('LgReMin', '%.0f' % RE_MIN)
m('LgImMax', '%.0f' % IM_MAX)
m('LgCommit', r'\texttt{%s}' % CRITERION_COMMIT)
m('LgNDup', '%d' % _dup)
_re = sorted(r['re'] for r in FITTED if r['re'] is not None)
m('LgReMaxAll', '%.2f' % _re[-1])
_nl = sorted(r['re'] for r in FITTED if not r['localised']
             and r['re'] is not None)
m('LgReMaxNotLocal', '%.2f' % _nl[-1])
OUT = os.path.join(HERE, 'survey_numbers_round76.tex')
open(OUT, 'w').write('\n'.join(M) + '\n')

print('ledger: %d crossings, %d fitted (%.0f%%), %d untestable'
      % (N_CROSS, len(FITTED), 100.0 * len(FITTED) / N_CROSS, len(UNTEST)))
print('        localised %d (%d line-attributed, %d unattributed)'
      % (len(LOCAL), len(LOCAL_ATTR), len(LOCAL_UNATTR)))
print('        rank screen passed %d; localised but screen-rejected %d; '
      'screen-passed but not localised %d'
      % (len(SCREEN), len(MISSED), len(SCREENED_NOT_LOCAL)))
print('        largest Re/sigma among non-localised crossings: %.2f' % _nl[-1])
