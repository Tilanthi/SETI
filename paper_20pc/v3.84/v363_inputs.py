#!/usr/bin/env python3
r"""Deterministic frozen inputs for v3.72.  No network.

Writes `trappist_phase_v363.json` and `itu5340_v363.json`.

`ssobody_cp72_v363.json` is NOT rebuilt here: it is a network harvest (IMCCE
SkyBoT) and is shipped frozen, with its own positive control recorded inside
the file.  Re-running it needs `astroquery.imcce`.
"""
import csv, json, os
import numpy as np

os.chdir(os.path.dirname(os.path.abspath(__file__)))
C = 2.99792458e8

# --------------------------------------------------------------- TRAPPIST-1 b
# Referee 2, minor 8.  The manuscript says TRAPPIST-1 b "sits at" the drift
# ceiling, quoting the maximum of |a_los| over orbital phase and inclination.
# A reader can take that to mean the planet is generically unsearchable.  For a
# circular orbit |a_los| = (GM/r^2) |sin i| |cos theta|, so the fraction of
# orbital phase above a ceiling a_c is (2/pi) arccos(a_c / (a_max sin i)).
AMAX = 4.00                       # m s^-2, the value the manuscript quotes
out = {}
for tag, ceil in (('lo', 12.0), ('hi', 13.3)):     # Hz s^-1 GHz^-1
    ac = ceil * C / 1e9
    f_edge = (2 / np.pi) * np.arccos(min(1.0, ac / AMAX)) if AMAX > ac else 0.0
    i = np.linspace(1e-6, np.pi / 2, 200001)
    s = np.sin(i)
    x = ac / (AMAX * s)
    f = np.where(x < 1, (2 / np.pi) * np.arccos(np.clip(x, -1, 1)), 0.0)
    out[tag] = dict(ceil_hzsghz=ceil, a_ceil=float(ac), f_edge=float(f_edge),
                    f_iso=float(np.trapezoid(f * s, i) / np.trapezoid(s, i)),
                    frac_inclinations=float(np.trapezoid((x < 1) * s, i)
                                            / np.trapezoid(s, i)))
json.dump(out, open('trappist_phase_v363.json', 'w'), indent=1)

# ------------------------------------------------------------------ ITU 5.340
# Referee 2, minor 11.  The manuscript rested the "no operational allocation"
# argument on a single FCC filing by one operator.  ITU Radio Regulations
# No. 5.340 prohibits ALL emissions in the bands below, whoever the operator
# is, which is the robust form of the same argument.
RR5340 = [(86, 92), (100, 102), (109.5, 111.8), (114.25, 116), (148.5, 151.5),
          (164, 167), (182, 185), (190, 191.8), (200, 209), (226, 231.5),
          (250, 252)]
R = list(csv.DictReader(open('per_target_results_v3.84.csv')))
iv = sorted((min(float(r['flo_GHz']), float(r['fhi_GHz'])),
             max(float(r['flo_GHz']), float(r['fhi_GHz']))) for r in R)
u = []
for a, b in iv:
    if u and a <= u[-1][1]:
        u[-1][1] = max(u[-1][1], b)
    else:
        u.append([a, b])
tot = sum(b - a for a, b in u)
per, ov = [], 0.0
for a, b in RR5340:
    s = sum(max(0.0, min(b, y) - max(a, x)) for x, y in u)
    if s > 0:
        per.append((a, b, s))
    ov += s
hi = sum(max(0.0, b - max(a, 275.0)) for a, b in u)
json.dump({'union_GHz': tot, 'n_islands': len(u), 'rr5340_overlap_GHz': ov,
           'rr5340_pct': 100 * ov / tot, 'per_band': per,
           'above275_GHz': hi, 'above275_pct': 100 * hi / tot},
          open('itu5340_v363.json', 'w'), indent=1)
print('v363 inputs: TRAPPIST phase + ITU 5.340 (%.1f GHz, %.1f %%)'
      % (ov, 100 * ov / tot))
