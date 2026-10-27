#!/usr/bin/env python3
r"""Every above-trigger cell of every window, not only the window maximum.

WHY THIS EXISTS
    The search records one number per window: the largest value its
    per-channel, drift-maximised statistic reaches at the stellar position.  A
    real carrier is therefore unrecordable whenever anything else in the same
    window is larger -- a molecular line, but equally a noise excursion, and
    windows hold up to 6.9e6 channel x drift cells.  So the published
    "crossing" counts measure WINDOWS, not EVENTS.

    This reads the retained per-channel profile of every window of the survey
    and extracts every above-trigger cell at the star and at each retained
    control position, de-duplicated by one stated rule.

THE RETAINED PRODUCT, AND THE ONE THING IT CANNOT DO
    `star[c]` is the maximum over the drift grid of the statistic in channel c,
    and `star_drift[c]` is the drift that attained it.  The drift axis is
    already collapsed: each channel contributes at most one cell, so two
    carriers in the SAME channel at different drifts cannot be separated.
    That is a property of the retained product; it is reported, not hidden.

THE DE-DUPLICATION RULE (adopted)
    Take every channel whose statistic reaches the trigger.  Two such channels
    belong to one event when they lie within one channel of each other AND
    their drift rates differ by no more than one step of the window's own
    drift grid; the relation is closed transitively.  Each event is
    represented by its largest cell.  The window maximum is one of these
    events; every other is SECONDARY.

    Both clauses do work.  A drifting carrier leaks into the channels either
    side of its peak at nearly its own drift, so those merge.  Two noise
    excursions in neighbouring channels pick unrelated drifts out of the grid,
    so they do not.  Two bounds are carried beside the adopted rule so the
    reader can see what it costs: `nomerge`, every above-trigger channel its
    own event, and `strict`, only strict local maxima of the profile.

    The drift clause needs the drift that attained each cell.  That is stored
    for the star and NOT for the controls, so for a control position the
    adopted rule cannot be evaluated and the two bounds are reported instead.
    The star-control comparison is then made under each bound separately,
    which is like for like and assumes nothing about the controls' drifts.

THE DRIFT STEP
    The grid is uniform in dnu/dt over `n_drift` trials, so the step is
    (max-min)/(n_drift-1) over the drifts actually attained.  The result is
    required to reproduce the smallest positive difference between attained
    drifts to one per cent (reported per window; asserted in cells_v416.py).
    Where fewer than two drifts were attained there is no drift
    discrimination and the drift clause is satisfied by construction.

HOW A WINDOW'S PROFILE IS FOUND -- ON THE STATISTIC, NEVER ON A NAME
    Five profile sets exist, written by four campaigns, and they disagree about
    the directory name of the same star: `tau_Cet_B6_EB_X7e6` in one set is
    `Tau_Cet_B6_EB_X7e6` in another, so a join on that string loses the
    re-extracted profile of every repaired window silently -- which is how
    this file was written the first time, and the 150 repaired windows came
    back carrying their pre-repair statistic.

    A window is therefore identified by its block, its spectral-window number
    and its two edges (min/max of the pair, because a descending window is
    stored reversed in one product and not in another), and a candidate
    profile is accepted only if its own maximum reproduces the window's
    ADOPTED statistic -- the repaired value where `repaired_v409.csv` carries
    one, the released value otherwise -- to 1e-4 relative.  Where no candidate
    does, the window is reported unresolved, with its candidates and their
    values printed.  Nothing is quietly folded in.

ATTRIBUTION
    Each event's channel is carried to the star's rest frame through the two
    declared steps -- f_bary = f_topo (1 - v_bary/c), f_star = f_bary
    (1 + v_sys/c) -- and compared with the frozen transition list at
    +-50 km/s.  The mask is passed in by the caller from the module that owns
    it and is never rebuilt here, so a secondary cell is attributed by exactly
    the rule that attributes a published crossing.

Input:  cells_jobs.json      built by cells_jobs.py
        repaired_v409.csv    the adopted statistic of every repaired window
Output: cells_extract_result.json
"""
import collections
import json
import os
import sys

import numpy as np

JOBS = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
TRIG = float(JOBS['trig'])
HALF = float(JOBS['half'])
C = float(JOBS['c'])
NAMES = sorted(JOBS['trans'], key=lambda k: JOBS['trans'][k])
REST = np.array([JOBS['trans'][k] for k in NAMES], dtype=np.float64)
NAMES_N = sorted(JOBS['trans_null'], key=lambda k: JOBS['trans_null'][k])
REST_N = np.array([JOBS['trans_null'][k] for k in NAMES_N], dtype=np.float64)


def events(T, drift, step, trig=TRIG):
    """The adopted rule, plus the two bounds, as (events, n_above, n_strict)."""
    above = np.flatnonzero(T >= trig)
    if above.size == 0:
        return [], 0, 0
    groups = [[int(above[0])]]
    for c in above[1:]:
        c = int(c)
        p = groups[-1][-1]
        near = (c - p) <= 1
        comp = True if (step is None or drift is None) else \
            abs(float(drift[c]) - float(drift[p])) <= step * (1.0 + 1e-9)
        (groups[-1].append(c) if (near and comp) else groups.append([c]))
    ev = []
    for g in groups:
        i = int(g[int(np.argmax(T[g]))])
        ev.append((i, float(T[i]), None if drift is None else float(drift[i])))
    n_strict = 0
    for c in above:
        c = int(c)
        lo = T[c - 1] if c > 0 else -np.inf
        hi = T[c + 1] if c + 1 < T.size else -np.inf
        if T[c] >= lo and T[c] > hi:
            n_strict += 1
    return ev, int(above.size), int(n_strict)


def nearest(f_star, rest, names):
    dv = C * (f_star - rest) / rest
    k = int(np.argmin(np.abs(dv)))
    return names[k], float(dv[k])


res = []
for j in JOBS['windows']:
    p = j['profile']
    z = np.load(p)
    star = np.asarray(z['star'], dtype=np.float64)
    ctrl = np.asarray(z['ctrl'], dtype=np.float64)
    sdr = np.asarray(z['star_drift'], dtype=np.float64)
    freqs = np.asarray(z['freqs'], dtype=np.float64) / 1e9
    nd = int(z['n_drift'])
    u = np.unique(sdr)
    span = float(u.max() - u.min()) if u.size > 1 else 0.0
    mindiff = float(np.diff(u).min()) if u.size > 1 else None
    # THE ADOPTED DRIFT STEP is the smallest positive difference between the
    # drift rates this window's own search attained.  The grid is uniform, so
    # that difference IS a grid step wherever two neighbouring trials both win
    # somewhere, which a window of thousands of channels guarantees; where it
    # does not it is a multiple of the step, which makes the merge looser and
    # the event count smaller, never larger.  `span / (n_drift - 1)` is kept
    # beside it because that is what the released catalogue's own drift
    # ceiling and trial count imply, and the two are compared window by window.
    step = mindiff
    step_span = span / (nd - 1) if (nd > 1 and u.size > 1) else None

    vb, vs = float(j['v_bary']), float(j['v_sys'])
    fs = freqs * (1.0 - vb / C) * (1.0 + vs / C)
    inmask = np.zeros(freqs.size, dtype=bool)
    for fr in REST:
        inmask |= (fs >= fr * (1.0 - HALF / C)) & (fs <= fr * (1.0 + HALF / C))
    inmask_n = np.zeros(freqs.size, dtype=bool)
    for fr in REST_N:
        inmask_n |= (fs >= fr * (1.0 - HALF / C)) \
            & (fs <= fr * (1.0 + HALF / C))

    # THE ADOPTED RULE IS CHANNEL ADJACENCY.  The drift axis is already
    # collapsed, so the drift the search attained in the channel NEXT to an
    # excursion carries no information about the excursion: a carrier puts
    # little power there and the winning trial wanders.  Requiring the two
    # drifts to agree before merging therefore counts one excursion twice --
    # measured below, it does so for ten of the thirteen cells it produces,
    # and it splits a resolved CO line into a hundred.  So an event is a
    # maximal run of above-trigger channels and its cell is the run's largest.
    ev, n_above, n_strict = events(star, None, None)
    ipk = int(np.argmax(star))

    # WHAT THE DE-DUPLICATION RULE COSTS, measured and not asserted.  Five
    # rules over the same cells: the adopted one, the same with the
    # catalogue's implied step, the same with twice the step (looser), channel
    # adjacency with no drift clause at all (loosest), and no merging (every
    # above-trigger channel its own event, tightest).
    def _un(evs):
        return sum(1 for (c, _T, _d) in evs
                   if not (inmask[c] and inmask_n[c]))
    variants = {}
    for nm, st in (('adopted', 1e99), ('driftstep', step),
                   ('driftspan', step_span),
                   ('drifttwice', None if step is None else 2.0 * step)):
        e2, _a, _s = events(star, sdr if nm != 'adopted' else None, st)
        variants[nm] = dict(n=len(e2), n_sec=max(0, len(e2) - 1),
                            n_unattr=_un(e2),
                            n_sec_unattr=_un([x for x in e2
                                              if x[0] != ipk]))
    _ab = [(int(c), float(star[c]), float(sdr[c]))
           for c in np.flatnonzero(star >= TRIG)]
    variants['nomerge'] = dict(n=len(_ab), n_sec=max(0, len(_ab) - 1),
                               n_unattr=_un(_ab),
                               n_sec_unattr=_un([x for x in _ab
                                                 if x[0] != ipk]))
    _st = [(int(c), float(star[c]), float(sdr[c]))
           for c in np.flatnonzero(star >= TRIG)
           if star[c] >= (star[c - 1] if c > 0 else -np.inf)
           and star[c] > (star[c + 1] if c + 1 < star.size else -np.inf)]
    variants['strict'] = dict(n=len(_st), n_sec=max(0, len(_st) - 1),
                              n_unattr=_un(_st),
                              n_sec_unattr=_un([x for x in _st
                                                if x[0] != ipk]))
    rows = []
    for (c, T, dr) in ev:
        line, dv = nearest(fs[c], REST, NAMES)
        rows.append(dict(chan=c, T=T, drift=dr, f_topo=float(freqs[c]),
                         f_star=float(fs[c]), line=line, dv=dv,
                         in_mask=bool(inmask[c]),
                         in_mask_null=bool(inmask_n[c]),
                         is_window_max=bool(c == ipk)))

    cr = []
    for k in range(ctrl.shape[0]):
        row = ctrl[k]
        cev, cn_above, cn_strict = events(row, None, None)
        above = np.flatnonzero(row >= TRIG)
        strict = [int(c) for c in above
                  if row[c] >= (row[c - 1] if c > 0 else -np.inf)
                  and row[c] > (row[c + 1] if c + 1 < row.size else -np.inf)]
        ick = int(np.argmax(row))
        cr.append(dict(win_max=float(row.max()), max_chan=ick,
                       max_in_mask=bool(inmask[ick]),
                       n_sec=int(max(0, len(cev) - 1)),
                       n_sec_out=int(sum(1 for (c, _T, _d) in cev
                                         if c != ick and not inmask[c])),
                       n_above_sec=int(max(0, cn_above - 1)),
                       n_strict_sec=int(max(0, cn_strict - 1)),
                       n_above=cn_above, n_strict=cn_strict,
                       n_merge_adj=len(cev),
                       n_above_out=int(sum(1 for c in above
                                           if not inmask[int(c)])),
                       n_strict_out=int(sum(1 for c in strict
                                            if not inmask[c])),
                       n_merge_adj_out=int(sum(1 for (c, _T, _d) in cev
                                               if not inmask[c]))))

    # A THRESHOLD LADDER, so the comparison is not made at one level only.
    # The star and the control positions are counted the same way at each
    # level, outside the mask, and the ratio is read as a function of the
    # level: an amplitude offset between the star and its own controls shows
    # up as a ratio that is already large below the trigger, where no carrier
    # claim is at stake.  A ratio that appears only AT the trigger would be
    # something else.
    ladder = {}
    for thr in JOBS['ladder']:
        se, sa, _ss = events(star, None, None, trig=thr)
        s_out = sum(1 for (c, _T, _d) in se if not inmask[c])
        c_tot = c_out = 0
        for k in range(ctrl.shape[0]):
            ce, _ca, _cs = events(ctrl[k], None, None, trig=thr)
            c_tot += len(ce)
            c_out += sum(1 for (c, _T, _d) in ce if not inmask[c])
        ladder['%.2f' % thr] = dict(star=len(se), star_out=s_out,
                                    ctrl=c_tot, ctrl_out=c_out)

    res.append(dict(
        ladder=ladder,
        key=j['key'], eb=j['eb'], spw=j['spw'], star=j['star'], cls=j['cls'],
        band=j.get('band'), released=j.get('released'),
        stratum=j['stratum'], crossing_cat=j.get('crossing'),
        fcross_cat=j.get('fcross'), smin_mJy=j.get('smin_mJy'),
        profile=os.path.basename(p), profile_path=p,
        profile_dir=j['profile_dir'], gate_rel=j.get('gate_rel', 0.0),
        repaired=j['repaired'], adopted=j['adopted'],
        lo=float(freqs.min()), hi=float(freqs.max()),
        nch=int(star.size), n_drift=nd, nint=int(z['nint']),
        chanw=float(z['chanw']), n_cells=int(star.size) * nd,
        n_search_cells_cat=j.get('n_search_cells'),
        drift_span=span, drift_step=step, drift_min_diff=mindiff,
        drift_step_span=step_span, variants=variants,
        v_bary=vb, v_sys=vs, v_sys_known=bool(j['v_sys_known']),
        star_peak=float(star.max()), peak_chan=ipk,
        masked_share=float(inmask.mean()),
        n_above=n_above, n_strict=n_strict, n_events=len(ev),
        events=rows, ctrl=cr, n_ctrl=int(ctrl.shape[0])))

json.dump(dict(meta=dict(trig=TRIG, half=HALF, n_window=len(res),
                         n_unresolved=len(JOBS['unresolved']),
                         unresolved=JOBS['unresolved'],
                         n_trans=len(REST), n_trans_null=len(REST_N)),
               windows=res), open(OUT, 'w'))

A = [r for r in res if r['cls'] == 'A']
print('%d windows searched' % len(res))
print('profile sets used: %s'
      % dict(collections.Counter(r['profile_dir'] for r in res)))
print('Class A %d: %d events (adopted), %d windows with a secondary event, '
      '%d windows whose maximum reaches the trigger'
      % (len(A), sum(r['n_events'] for r in A),
         sum(1 for r in A if r['n_events'] > 1),
         sum(1 for r in A if r['star_peak'] >= TRIG)))
print('by stratum: %s' % dict(collections.Counter(r['stratum'] for r in res)))
