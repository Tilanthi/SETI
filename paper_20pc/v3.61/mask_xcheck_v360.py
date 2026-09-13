#!/usr/bin/env python3
"""Splatalogue harvest over the v3.60 searched islands (Bands 3--10).

Identical selection to the v3.51/v3.52 harvest (`/workspace/SETI/v352_F/
mask_xcheck.py`); the only change is the island list, which is recomputed from
the released v3.60 catalogue and now runs to 873.1 GHz because the Band 9 and
Band 10 windows have been folded in.  Read-only apart from its own output.

Writes `mask_xcheck_lines.json` in this folder (the path `v352_calc.py` looks
for first) and prints a comparison against the 33-island v3.51 harvest.
"""
import csv, json, os, re, collections, sys
import astropy.units as u
from astroquery.splatalogue import Splatalogue

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOGUE = os.path.join(HERE, 'per_target_results_v3.61.csv')
OLD = '/workspace/SETI/v352_F/mask_xcheck_lines.json'

EU_MAX = 150.0     # K -- cold/warm circumstellar gas
LOGA_MIN = -5.0    # log10 A_ij [s^-1] -- strong rotational transitions

rows = list(csv.DictReader(open(CATALOGUE)))
iv = sorted((min(float(r['flo_GHz']), float(r['fhi_GHz'])),
             max(float(r['flo_GHz']), float(r['fhi_GHz']))) for r in rows)
isl = []
for a, b in iv:
    if isl and a <= isl[-1][1]:
        isl[-1][1] = max(isl[-1][1], b)
    else:
        isl.append([a, b])
print('catalogue rows %d | islands %d | union %.3f GHz'
      % (len(rows), len(isl), sum(b - a for a, b in isl)), flush=True)


def _num(v):
    m = re.search(r'-?\d+\.?\d*', str(v).replace('<span', ' '))
    return float(m.group()) if m else float('nan')


out = []
for a, b in isl:
    for attempt in range(4):
        try:
            t = Splatalogue.query_lines(a * u.GHz, b * u.GHz,
                                        only_astronomically_observed=True)
            break
        except Exception as e:
            print('   retry %d %.3f-%.3f %s' % (attempt, a, b, e), flush=True)
            t = None
    if t is None:
        print('QUERYFAIL', a, b, flush=True)
        sys.exit(1)
    n = 0
    for r in t:
        try:
            eu = float(str(r['upper_state_energy_K']))
        except Exception:
            eu = float('nan')
        try:
            aij = float(r['aij'])
        except Exception:
            aij = float('nan')
        f = _num(r['orderedFreq'])
        if not (a - 1e-3 <= f <= b + 1e-3):
            f2 = _num(r['orderedfreq'])
            f = f2 / 1000.0 if f2 > 1000 else f2
        if f > 1000:
            f = f / 1000.0
        if eu == eu and eu > EU_MAX:
            continue
        if aij == aij and aij < LOGA_MIN:
            continue
        out.append(dict(f=f, name=str(r['name']).strip(),
                        chem=str(r['chemical_name']).strip(),
                        qn=str(r['resolved_QNs']).strip(), eu=eu, aij=aij,
                        ll=str(r['linelist']).strip()))
        n += 1
    print('  %9.3f-%9.3f  rows %4d  kept %4d' % (a, b, len(t), n), flush=True)

json.dump(dict(islands=isl, eu_max=EU_MAX, loga_min=LOGA_MIN, lines=out),
          open(os.path.join(HERE, 'mask_xcheck_lines.json'), 'w'), indent=1)
_strip = lambda s: re.sub(r'<[^>]+>', '', s).replace('&#150;', '-').strip()
print('total kept %d | distinct carriers %d'
      % (len(out), len({_strip(x['name']) for x in out})))

# --- comparison against the v3.51 harvest over the 33 common islands --------
if os.path.exists(OLD):
    O = json.load(open(OLD))
    oi = {tuple(x) for x in O['islands']}
    ni = {tuple(x) for x in isl}
    print('islands: common %d, new %d, dropped %d'
          % (len(oi & ni), len(ni - oi), len(oi - ni)))
    inold = lambda f: any(a <= f <= b for a, b in O['islands'])
    same_region = [x for x in out if inold(x['f'])]
    print('over the 33 v3.51 islands: v3.51 kept %d, this harvest keeps %d'
          % (len(O['lines']), len(same_region)))
    print('new islands contribute %d transitions, %d carriers'
          % (len(out) - len(same_region),
             len({_strip(x['name']) for x in out if not inold(x['f'])})))
    c = collections.Counter(_strip(x['name']) for x in out if not inold(x['f']))
    for k, v in c.most_common(25):
        print('   %5d  %s' % (v, k))
