#!/usr/bin/env python3
"""Stage 2.  Two things the first stage leaves open.

(a) THE CONTROL COMPARISON.  For each re-searched window, how high the
    window's own retained control positions reach outside the mask.  A cell
    at the trigger outside the mask means nothing until it is known how often
    a control position in the same field does the same.

(b) THE SURVIVING CELL.  Any window whose unmasked maximum reaches the
    trigger is carried to the other blocks of the same star: its
    stellar-frame frequency is transported to each covering block's own
    barycentric term and the statistic read at the matched channel.  That is
    the paper's own recurrence test, run on the new cell.

Output: mask_second_result.json
"""
import glob
import json
import os
import sys

import numpy as np

R8 = '/data/SETI/r8'
PROF = [os.path.join(R8, d) for d in
        ('prof_v409r', 'profall_v409', 'prof_v409', 'profall', 'prof')]
PROF.append('/data/SETI/r14mask')
JOBS = json.load(open(sys.argv[1]))
FIRST = json.load(open(sys.argv[2]))
OUT = sys.argv[3]
HALF, C, TRANS = JOBS['half'], JOBS['c'], JOBS['trans']
TRIG = 5.0
WORK = json.load(open(os.path.join(R8, 'worklist_all_v409.json')))
BARY = json.load(open(os.path.join(R8, 'bary.json')))


def profiles_for(eb):
    out = []
    for d in PROF:
        out += sorted(glob.glob(os.path.join(d, '*%s_spw*_r8prof.npz' % eb)))
    return out


# ---------------------------------------------------------------- (a)
ctrl_rows = []
for r in FIRST:
    if r['status'] not in ('ok',):
        continue
    p = None
    for d in PROF:
        q = os.path.join(d, r['profile'])
        if os.path.exists(q):
            p = q
            break
    z = np.load(p)
    star = np.asarray(z['star'], dtype=np.float64)
    ctrl = np.asarray(z['ctrl'], dtype=np.float64)
    freqs = np.asarray(z['freqs'], dtype=np.float64) / 1e9
    fs = freqs * (1.0 - r['v_bary'] / C) * (1.0 + r['v_sys'] / C)
    masked = np.zeros(star.size, dtype=bool)
    for frest in TRANS.values():
        masked |= np.abs(C * (fs - frest) / frest) <= HALF
    keep = ~masked
    cm = ctrl[:, keep].max(axis=1)
    ctrl_rows.append(dict(display=r['display'], eb=r['eb'],
                          T_resid=r['T_resid'], n_ctrl=int(cm.size),
                          ctrl_resid=[float(x) for x in cm],
                          n_ctrl_trig=int((cm >= TRIG).sum()),
                          ctrl_max=float(cm.max())))

n_win = len(ctrl_rows)
n_star_trig = sum(1 for r in ctrl_rows if r['T_resid'] >= TRIG)
n_ctrl_tot = sum(r['n_ctrl'] for r in ctrl_rows)
n_ctrl_trig = sum(r['n_ctrl_trig'] for r in ctrl_rows)
n_win_ctrl_trig = sum(1 for r in ctrl_rows if r['n_ctrl_trig'] > 0)

# ---------------------------------------------------------------- (b)
survivors = [r for r in FIRST if r.get('second_crossing')]
recur = []
for s in survivors:
    fstar = s['f_resid_stellar']
    star_name = s['star']
    wins = [w for w in WORK if w['star'] == star_name
            and w['cls'] == 'A' and w['eb'] != s['eb']]
    tested = []
    for w in wins:
        vb = BARY.get('%s|%.6f' % (w['eb'], round(min(w['lo'], w['hi']), 6)))
        if vb is None:
            vb = BARY.get('%s|%.6f' % (w['eb'], round(w['lo'], 6)))
        if vb is None:
            tested.append(dict(eb=w['eb'], lo=w['lo'], hi=w['hi'],
                               status='no_barycentric_term'))
            continue
        # the frequency this cell would sit at in that block, topocentric
        ftopo = fstar / (1.0 + s['v_sys'] / C) / (1.0 - float(vb) / C)
        lo, hi = min(w['lo'], w['hi']), max(w['lo'], w['hi'])
        if not (lo <= ftopo <= hi):
            continue
        got = None
        for p in profiles_for(w['eb']):
            z = np.load(p)
            f = np.asarray(z['freqs'], dtype=np.float64) / 1e9
            if not (f.min() <= ftopo <= f.max()):
                continue
            star = np.asarray(z['star'], dtype=np.float64)
            i = int(np.argmin(np.abs(f - ftopo)))
            w0 = max(0, i - 1)
            w1 = min(star.size, i + 2)
            got = dict(eb=w['eb'], profile=os.path.basename(p),
                       f_topo_pred=ftopo, chan=i,
                       T_at_cell=float(star[i]),
                       T_in_window_of_three=float(star[w0:w1].max()),
                       T_window_peak=float(star.max()),
                       chanw_Hz=float(z['chanw']), v_bary=float(vb))
            break
        tested.append(got or dict(eb=w['eb'], status='no_profile',
                                  f_topo_pred=ftopo))
    recur.append(dict(display=s['display'], eb=s['eb'],
                      T_resid=s['T_resid'],
                      f_resid_topo=s['f_resid_topo'],
                      f_resid_stellar=fstar,
                      resid_drift=s['resid_drift'],
                      resid_dv=s['resid_dv'],
                      n_covering=sum(1 for t in tested
                                     if t.get('T_at_cell') is not None),
                      covering=tested))

json.dump(dict(control=dict(n_window=n_win, n_star_at_trigger=n_star_trig,
                            n_ctrl_positions=n_ctrl_tot,
                            n_ctrl_at_trigger=n_ctrl_trig,
                            n_window_with_ctrl_at_trigger=n_win_ctrl_trig,
                            rows=ctrl_rows),
               survivors=recur), open(OUT, 'w'), indent=1)

print('control: %d of %d windows reach the trigger outside the mask at the '
      'star; %d of %d control positions do, in %d of the %d windows'
      % (n_star_trig, n_win, n_ctrl_trig, n_ctrl_tot, n_win_ctrl_trig, n_win))
for r in recur:
    print('%s %s  T_resid=%.3f at %.6f GHz (stellar %.6f), drift %+.1f Hz/s'
          % (r['display'], r['eb'], r['T_resid'], r['f_resid_topo'],
             r['f_resid_stellar'], r['resid_drift']))
    for t in r['covering']:
        if t.get('T_at_cell') is None:
            print('    %-24s %s' % (t['eb'], t.get('status')))
        else:
            print('    %-24s predicted %.6f GHz  T=%.3f (3-chan %.3f), '
                  'window peak %.3f' % (t['eb'], t['f_topo_pred'],
                                        t['T_at_cell'],
                                        t['T_in_window_of_three'],
                                        t['T_window_peak']))
