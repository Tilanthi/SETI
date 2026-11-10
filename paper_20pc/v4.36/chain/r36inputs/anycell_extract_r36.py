#!/usr/bin/env python3
"""r36 (N3, R2-3): freeze, from the RETAINED per-channel profiles the cells extract already read
(r15inputs/cells/cells_extract_result.json -> profile_path; read-only), every above-trigger EVENT
(a maximal run of adjacent channels at or above the trigger, represented by its largest channel -- the
cells extract's adopted rule) at the stellar position and at each retained control position whose window
maximum reaches the trigger, for every Class A census window.  Frequencies only: the attribution and the
atmospheric screen are applied by the generator (anycell_r36.py) with the production modules, so a change
of mask moves the result.  Run once, on the cluster, from a chain/ directory:

    python3 anycell_extract_r36.py r15inputs/cells/cells_extract_result.json r36inputs/anycell_r36.json
"""
import hashlib, json, sys
import numpy as np
TRIG = 5.0
CELLS = json.load(open(sys.argv[1]))['windows']


def runs(T):
    a = np.flatnonzero(T >= TRIG)
    if not a.size:
        return []
    g = [[int(a[0])]]
    for c in a[1:]:
        c = int(c)
        (g[-1].append(c) if c - g[-1][-1] <= 1 else g.append([c]))
    return [int(x[int(np.argmax(T[x]))]) for x in g]


out = []
for w in CELLS:
    if w['cls'] != 'A' or w['stratum'] == 'archival_tail':
        continue
    p = w['profile_path']
    z = np.load(p)
    fr = np.asarray(z['freqs'], float) / 1e9
    star = np.asarray(z['star'], float)
    ctrl = np.asarray(z['ctrl'], float)
    ev = lambda T: [[c, round(float(T[c]), 6), float(fr[c])] for c in runs(T)]   # noqa: E731
    cr = []
    for k in range(ctrl.shape[0]):
        row = ctrl[k]
        ick = int(np.argmax(row))
        cr.append(dict(win_max=round(float(row[ick]), 6), max_chan=ick, f_max=float(fr[ick]),
                       events=ev(row) if row[ick] >= TRIG else []))
    out.append(dict(key=w['key'], eb=w['eb'], star=w['star'], lo=w['lo'], hi=w['hi'], v_bary=w['v_bary'],
                    v_sys=w['v_sys'], nch=int(star.size), star_peak_chan=int(np.argmax(star)),
                    star_peak=round(float(star.max()), 6), star_events=ev(star), ctrl=cr,
                    profile=w['profile'], profile_sha256=hashlib.sha256(open(p, 'rb').read()).hexdigest()))
json.dump(dict(produced_by='anycell_extract_r36.py', source='r15inputs/cells/cells_extract_result.json',
               trigger=TRIG, rule='an event is a maximal run of adjacent channels >= trigger, at its largest channel',
               windows=out), open(sys.argv[2], 'w'), indent=0)
print('%d windows, %d star events, %d control exceedances'
      % (len(out), sum(len(w['star_events']) for w in out),
         sum(1 for w in out for c in w['ctrl'] if c['events'])))
