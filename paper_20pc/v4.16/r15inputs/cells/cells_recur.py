#!/usr/bin/env python3
r"""The recurrence test, run on every secondary cell the cell-level search
leaves unattributed.

THE TEST IS THE PAPER'S OWN, APPLIED TO A NEW EVENT
    A cell's stellar rest frequency is carried to every other execution block
    of the same star whose spectral coverage includes it, and the statistic is
    read at the channel that frequency lands on in that block, after that
    block's own barycentric term and the star's systemic velocity.  The
    criterion is that it reach the trigger again.

THE JOIN IS ON POSITION, NEVER ON A NAME
    Two components of a multiple share a star name in some products and not in
    others, and this project has lost rows to that thirteen times.  Each
    window's extraction position is read from its own `*_srcspec.npz`
    (`t1_ra`, `t1_dec`) and windows are grouped at 2 arcsec, which is the
    tolerance the published recurrence runner uses.  The number of groups is
    reported and asserted against the number of distinct names, so a
    disagreement between the two keys is visible rather than silent.

THE VALUE READ IS DRIFT-MAXIMISED, WHICH CAN ONLY WEAKEN AN EXCLUSION
    The retained profile holds, per channel, the maximum over the drift grid.
    Reading it at the predicted channel therefore gives the largest value any
    drift attains there, which is at or above the value at the single
    transported drift the test specifies.  An exclusion computed from it is
    conservative: the matched-drift value can only be lower.

THE PERSISTENCE EXPECTATION
    Both windows publish a five-sigma flux limit, so a carrier that kept its
    discovery flux would reach

        T_pers = T_disc * smin_disc / smin_rep

    in the repeat window, and the fraction of that amplitude the repeat
    excludes is (T_rep + 5) / T_pers -- the quantity the paper reports, read
    the same way for a secondary cell as for a window maximum.  Where the
    repeat is deeper than the discovery T_pers exceeds the trigger and the
    test has power; where it is shallower it does not, and that is stated per
    epoch rather than averaged away.

Usage: cells_recur.py cells_jobs.json cells_extract_result.json out.json
"""
import collections
import json
import math
import os
import re
import sys

import numpy as np

JOBS = json.load(open(sys.argv[1]))
EXT = json.load(open(sys.argv[2]))
OUT = sys.argv[3]
# 'pos'   : one star = one extraction position within POS_TOL
# 'union' : one star = position OR name, closed transitively.  Proper motion
#           splits a nearby star's own epochs across positions (Proxima moves
#           3.9 arcsec a year), and an alias splits one star across names, so
#           the two keys disagree in both directions and the honest thing is
#           to run the test under each.  The union can only ADD covering
#           blocks, so it is the one that could find a recurrence the tight
#           key misses; the tight key is the one whose epoch COUNT is quoted.
JOIN = sys.argv[4] if len(sys.argv) > 4 else 'pos'
C = float(JOBS['c'])
TRIG = float(JOBS['trig'])
POS_TOL_ARCSEC = 2.0

BYKEY = {w['key']: w for w in JOBS['windows']}
JBY = BYKEY
EXTBY = {w['key']: w for w in EXT['windows']}

# ------------------------------------------------------------------ position
pos = {}
for w in JOBS['windows']:
    p = w['stem'] + '_srcspec.npz'
    if not os.path.exists(p):
        continue
    try:
        z = np.load(p, mmap_mode=None)
        pos[w['key']] = (float(z['t1_ra']), float(z['t1_dec']))
    except Exception:
        pass

groups, gid = [], {}
for k, (ra, dec) in pos.items():
    hit = None
    for i, (gra, gdec, _n) in enumerate(groups):
        d = math.hypot((ra - gra) * math.cos(math.radians(dec)), dec - gdec)
        if d * 3600.0 <= POS_TOL_ARCSEC:
            hit = i
            break
    if hit is None:
        groups.append([ra, dec, 1])
        hit = len(groups) - 1
    gid[k] = hit

if JOIN == 'union':
    parent = {k: k for k in gid}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    bypos = collections.defaultdict(list)
    byname = collections.defaultdict(list)
    for k in gid:
        bypos[gid[k]].append(k)
        byname[BYKEY[k]['star']].append(k)
    for grp in list(bypos.values()) + list(byname.values()):
        for k in grp[1:]:
            union(grp[0], k)
    gid = {k: find(k) for k in gid}
    print('union join: %d groups' % len(set(gid.values())))

names = {w['star'] for w in JOBS['windows']}
print('positions read for %d of %d windows; %d position groups at %.1f arcsec '
      'against %d distinct names'
      % (len(pos), len(JOBS['windows']), len(groups), POS_TOL_ARCSEC,
         len(names)))
namesof = collections.defaultdict(set)
for k, g in gid.items():
    namesof[g].add(BYKEY[k]['star'])
split = {n: sorted({g for k, g in gid.items() if BYKEY[k]['star'] == n})
         for n in names}
for n, gs in split.items():
    if len(gs) > 1:
        print('  ONE NAME, %d POSITIONS: %-28s %s' % (len(gs), n, gs))
for g, ns in namesof.items():
    if len(ns) > 1:
        print('  ONE POSITION, %d NAMES: %s' % (len(ns), sorted(ns)))

# --------------------------------------------------------- the events to test
SEC = []
for w in EXT['windows']:
    if w['cls'] != 'A':
        continue
    for e in w['events']:
        if e['is_window_max']:
            continue
        if e['in_mask'] and e['in_mask_null']:
            continue                      # attributed
        SEC.append((w, e))
SEC.sort(key=lambda x: -x[1]['T'])
print('%d unattributed secondary cells to test' % len(SEC))

res = []
for w, e in SEC:
    j = BYKEY[w['key']]
    g = gid.get(w['key'])
    vs = w['v_sys']
    fstar = e['f_star']
    cov, tested = [], 0
    for k2, j2 in BYKEY.items():
        if j2['eb'] == w['eb']:
            continue
        if g is None or gid.get(k2) != g:
            continue
        w2 = EXTBY.get(k2)
        if w2 is None:
            continue                      # no profile carrying the adopted stat
        ftopo = fstar / (1.0 + vs / C) / (1.0 - w2['v_bary'] / C)
        lo, hi = min(w2['lo'], w2['hi']), max(w2['lo'], w2['hi'])
        if not (lo <= ftopo <= hi):
            continue
        tested += 1
        cov.append(dict(key=k2, eb=j2['eb'], cls=j2['cls'],
                        f_topo_pred=ftopo,
                        smin_mJy=j2['smin_mJy'], nint=w2['nint'],
                        chanw=w2['chanw'], v_bary=w2['v_bary'],
                        win_peak=w2['star_peak']))
    res.append(dict(key=w['key'], eb=w['eb'], star=w['star'], group=g,
                    T=e['T'], drift=e['drift'], f_topo=e['f_topo'],
                    f_star=fstar, line=e['line'], dv=e['dv'],
                    in_mask=e['in_mask'], win_max=w['star_peak'],
                    smin_mJy=j['smin_mJy'], chanw=w['chanw'],
                    n_covering=tested, covering=cov))

# ------------------------------------------------- read the predicted channel
cache = {}


def profile_of(key):
    if key not in cache:
        p = JBY[key]['profile']
        z = np.load(p)
        cache[key] = (np.asarray(z['freqs'], float) / 1e9,
                      np.asarray(z['star'], float),
                      np.asarray(z['star_drift'], float))
    return cache[key]


for r in res:
    for c in r['covering']:
        f, st, dr = profile_of(c['key'])
        i = int(np.argmin(np.abs(f - c['f_topo_pred'])))
        c['chan'] = i
        c['T_at_cell'] = float(st[i])
        c['T_three_chan'] = float(st[max(0, i - 1):i + 2].max())
        c['drift_at_cell'] = float(dr[i])
        c['chan_offset'] = float((f[i] - c['f_topo_pred']) * 1e9 / c['chanw'])
        if c['smin_mJy'] and r['smin_mJy']:
            c['T_pers'] = r['T'] * r['smin_mJy'] / c['smin_mJy']
            c['excluded_fraction'] = (c['T_three_chan'] + TRIG) / c['T_pers']
            sd = r['smin_mJy'] / 5.0
            sr = c['smin_mJy'] / 5.0
            c['excl_sigma'] = (r['T'] * sd - c['T_three_chan'] * sr) \
                / math.hypot(sd, sr)
        c['recurs'] = bool(c['T_three_chan'] >= TRIG)
        c['status'] = 'ok'

    ok = [c for c in r['covering'] if c.get('status') == 'ok']
    r['n_read'] = len(ok)
    r['n_recurring'] = sum(1 for c in ok if c['recurs'])
    r['T_rep_max'] = max((c['T_three_chan'] for c in ok), default=None)
    pw = [c for c in ok if c.get('T_pers') and c['T_pers'] >= TRIG]
    r['n_with_power'] = len(pw)
    r['best_excluded_fraction'] = min((c['excluded_fraction'] for c in pw),
                                      default=None)
    # inverse-variance stack of the repeats, in flux
    if ok and r['smin_mJy']:
        wts = np.array([(5.0 / c['smin_mJy']) ** 2 for c in ok
                        if c['smin_mJy']])
        fl = np.array([c['T_three_chan'] * c['smin_mJy'] / 5.0 for c in ok
                       if c['smin_mJy']])
        if wts.size:
            r['stack_flux_mJy'] = float((fl * wts).sum() / wts.sum())
            r['stack_err_mJy'] = float(1.0 / math.sqrt(wts.sum()))
            r['disc_flux_mJy'] = r['T'] * r['smin_mJy'] / 5.0
            r['disc_err_mJy'] = r['smin_mJy'] / 5.0
            r['stack_excl_sigma'] = (r['disc_flux_mJy'] - r['stack_flux_mJy']) \
                / math.hypot(r['disc_err_mJy'], r['stack_err_mJy'])
            r['n_eff'] = float(wts.sum() / (25.0 / r['smin_mJy'] ** 2))

json.dump(dict(meta=dict(n_position_groups=len(groups), n_names=len(names),
                         n_positions_read=len(pos), pos_tol=POS_TOL_ARCSEC,
                         n_secondary=len(SEC)), rows=res),
          open(OUT, 'w'), indent=1)

print()
print('%-30s %7s %7s %6s %6s %8s %8s %s'
      % ('cell', 'T', 'cover', 'read', 'recur', 'Trep', 'power', 'excl frac'))
nrec = 0
for r in res:
    nrec += r['n_recurring'] > 0
    print('%-30s %7.3f %7d %6d %6d %8s %8d %s'
          % ((r['star'][:16] + ' ' + ('%.4f' % r['f_topo']))[:30], r['T'],
             r['n_covering'], r['n_read'], r['n_recurring'],
             ('%.3f' % r['T_rep_max']) if r['T_rep_max'] is not None else '-',
             r['n_with_power'],
             ('%.3f' % r['best_excluded_fraction'])
             if r['best_excluded_fraction'] is not None else '-'))
print()
print('%d of %d unattributed secondary cells recur in any covering block'
      % (nrec, len(res)))
print('%d have no covering block at all' % sum(1 for r in res
                                               if r['n_read'] == 0))
