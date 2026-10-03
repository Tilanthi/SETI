#!/usr/bin/env python3
"""R2-M3(1): the control ensemble redrawn so that no two controls, and no
control and the star, lie within 2 synthesised beams of each other.

The screen ranks the stellar statistic against 512 control positions drawn
uniformly in an annulus. Those 512 are not 512 independent measurements:
the annulus is only so large, and many of the draws land within one
synthesised beam of a neighbour, so they share the same noise. Quoting a
rank resolution of 1/513 therefore claims more than the field contains.
The referee asks what the ensemble is worth once that is enforced, and for
the rank resolution to be quoted as 1/(N_ctrl+1) with the N_ctrl that
survives.

Nothing needs re-extracting. The draw is deterministic --- the extractor
takes `default_rng(seed)`, then

    rr = sqrt(uniform(ann_lo^2, ann_hi^2, 512));  th = uniform(0, 2pi, 512)

in that order --- and the catalogue stores the seed and both annulus radii
per window, so the positions are recoverable exactly. The per-control
statistics are in the frozen export. The synthesised beam is the archive's
own recorded value for the block, not one of ours.

The selection is greedy in the order the positions were drawn, which is
fixed before any statistic is seen; it is therefore independent of the
data and cannot be tuned. Greedy selection gives a valid separated set,
not the largest possible one, so every N_ctrl here is a lower bound on
what a maximal packing would give --- which is the conservative direction.

Writes survey_numbers_round73.tex and tab_ctrlsep_v400.tex.
"""
import collections
import csv
import json
import math
import os
import statistics as st

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.99.csv'))))
EXPORT = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']
OUT = os.path.join(HERE, 'survey_numbers_round73.tex')
TAB = os.path.join(HERE, 'tab_ctrlsep_v400.tex')

SEP_BEAMS = 2.0          # the referee's constraint, in synthesised beams


def F(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def key(eb, band, flo, fhi):
    # min/max, not as-written: a descending spectral window has flo > fhi in
    # the export while the catalogue always writes the lower edge first, so
    # keying on the raw pair silently loses half the windows.
    a, b = float(flo), float(fhi)
    return (eb, str(band), round(min(a, b), 4), round(max(a, b), 4))


CTRL = {}
for e in EXPORT:
    if e.get('ctrl_all'):
        CTRL[key(e['eb'], e['band'], e['flo'], e['fhi'])] = e['ctrl_all']


def positions(r_in, r_out, seed, n=512):
    """Reproduce the extractor's control draw exactly."""
    rng = np.random.default_rng(int(seed))
    rr = np.sqrt(rng.uniform(r_in ** 2, r_out ** 2, n))
    th = rng.uniform(0, 2 * np.pi, n)
    return rr * np.cos(th), rr * np.sin(th)


def separated(l, m, sep):
    """Greedy maximal-ish subset with all pairwise separations >= sep, in
    draw order. The star is at the origin and is enforced too."""
    keep = []
    kl, km = [], []
    for i in range(l.size):
        if math.hypot(l[i], m[i]) < sep:          # too close to the star
            continue
        ok = True
        for a, b in zip(kl, km):
            if (l[i] - a) ** 2 + (m[i] - b) ** 2 < sep * sep:
                ok = False
                break
        if ok:
            keep.append(i)
            kl.append(l[i])
            km.append(m[i])
    return keep


rec = []
for r in ROWS:
    ca = CTRL.get(key(r['eb'], r['band'], r['flo_GHz'], r['fhi_GHz']))
    syn = META.get(r['eb'], {}).get('s_resolution_arcsec')
    r_in, r_out, seed = F(r['r_in_arcsec']), F(r['r_out_arcsec']), r['ring_seed']
    star = F(r['star_snr'])
    if not (ca and syn and r_in and r_out and star is not None):
        continue
    l, m = positions(r_in, r_out, seed, len(ca))
    keep = separated(l, m, SEP_BEAMS * float(syn))
    if not keep:
        continue
    vals = [float(ca[i]) for i in keep]
    n_ge = sum(1 for v in vals if v >= star)
    rec.append(dict(
        eb=r['eb'], cls=('A' if r['resolution_class'] == 'fine' else 'B'),
        arr=('7m' if float(syn) > 2.0 else '12m'),
        n_sep=len(keep), n_full=len(ca), syn=float(syn),
        star=star, cmax_sep=max(vals),
        rank_sep=(1 + n_ge) / (len(keep) + 1),
        flag_full=(r['stage1_flag'] == 'True'),
        flag_sep=(star >= 5.0 and n_ge == 0),
        crossing=(r['crossing'] == 'True')))

assert rec, 'no window could be redrawn'
n_sep = [x['n_sep'] for x in rec]
byarr = collections.defaultdict(list)
for x in rec:
    byarr[x['arr']].append(x['n_sep'])

flag_full = [x for x in rec if x['flag_full']]
flag_sep = [x for x in rec if x['flag_sep']]
lost = [x for x in flag_full if not x['flag_sep']]
gained = [x for x in flag_sep if not x['flag_full']]
ranks = [x['rank_sep'] for x in rec]

# Exchangeability on the reduced ensemble. A continuous Kolmogorov--Smirnov
# test is NOT the right instrument here: with a median of a dozen
# independent ACA controls the add-one rank takes only a dozen values, and
# comparing that to a continuous uniform manufactures D ~ 1/(2 N_ctrl)
# from the quantisation alone. The rank is therefore dithered within its
# own cell before the test, which is the standard randomised-p device and
# is exact under the null.
_rng = np.random.default_rng(20260924)
_dith = [min(max(x['rank_sep'] - _rng.uniform(0, 1.0 / (x['n_sep'] + 1)),
                 1e-9), 1 - 1e-9) for x in rec]
try:
    from scipy import stats as _sps
    D, p = _sps.kstest(_dith, 'uniform')
    Draw = _sps.kstest(ranks, 'uniform')[0]
except Exception:
    rs = sorted(_dith)
    n = len(rs)
    D = max(max((i + 1) / n - v, v - i / n) for i, v in enumerate(rs))
    p = float('nan')
    Draw = float('nan')

L = ['%% GENERATED by ctrlsep_v400.py -- do not hand-edit.\n']


def mc(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


mc('SepBeams', '%.0f' % SEP_BEAMS)
mc('SepNWin', '%d' % len(rec))
mc('SepNMed', '%d' % round(st.median(n_sep)))
mc('SepNLo', '%d' % min(n_sep))
mc('SepNHi', '%d' % max(n_sep))
mc('SepFloorMed', '%.3f' % (1.0 / (round(st.median(n_sep)) + 1)))
mc('SepFloorRatio', '%.0f' % ((1.0 / (round(st.median(n_sep)) + 1)) / (1.0 / 513)))
for a in ('7m', '12m'):
    if byarr[a]:
        tag = 'Seven' if a == '7m' else 'Twelve'
        mc('SepN%sMed' % tag, '%d' % round(st.median(byarr[a])))
        mc('SepFloor%s' % tag, '%.3f' % (1.0 / (round(st.median(byarr[a])) + 1)))
        mc('SepN%sWin' % tag, '%d' % len(byarr[a]))
mc('SepNFlagFull', '%d' % len(flag_full))
mc('SepNFlagSep', '%d' % len(flag_sep))
mc('SepNLost', '%d' % len(lost))
mc('SepNGained', '%d' % len(gained))
mc('SepRankMed', '%.3f' % st.median(ranks))
mc('SepKsD', '%.3f' % D)
mc('SepKsDRaw', '%.3f' % Draw)
mc('SepKsP', ('<0.001' if p == p and p < 0.001 else
              ('=%.2f' % p if p == p else 'n/a')))

with open(TAB, 'w') as fh:
    fh.write('%% GENERATED by ctrlsep_v400.py -- do not hand-edit.\n')
    fh.write('\\begin{tabular}{@{}lrrr@{}}\n\\toprule\n')
    fh.write('Array & Windows & Independent controls & Rank resolution \\\\\n')
    fh.write(' & & (median, of 512) & $1/(N_{\\rm ctrl}+1)$ \\\\\n\\midrule\n')
    for a, lab in (('12m', '12\\,m'), ('7m', 'ACA 7\\,m')):
        if byarr[a]:
            med = round(st.median(byarr[a]))
            fh.write('%s & %d & %d & %.3f \\\\\n'
                     % (lab, len(byarr[a]), med, 1.0 / (med + 1)))
    fh.write('\\midrule\n')
    med = round(st.median(n_sep))
    fh.write('All & %d & %d & %.3f \\\\\n' % (len(rec), med, 1.0 / (med + 1)))
    fh.write('\\bottomrule\n\\end{tabular}\n')

open(OUT, 'w').writelines(L)
print('ctrlsep_v400: %d windows redrawn at >=%.0f theta_syn separation'
      % (len(rec), SEP_BEAMS))
for a in ('12m', '7m'):
    if byarr[a]:
        print('  %-4s %4d windows, independent controls median %3d '
              '(range %d-%d), rank resolution 1/%d'
              % (a, len(byarr[a]), round(st.median(byarr[a])),
                 min(byarr[a]), max(byarr[a]), round(st.median(byarr[a])) + 1))
print('  stage-1 under the full ensemble %d, under the separated ensemble %d '
      '(%d lost, %d gained)' % (len(flag_full), len(flag_sep), len(lost), len(gained)))
print('  separated-ensemble rank: median %.3f, dithered D=%.3f p=%s '
      '(undithered D=%.3f, inflated by quantisation)'
      % (st.median(ranks), D, p, Draw))
