#!/usr/bin/env python3
r"""r21_harvest_full.py -- the same expanded list as `r21_harvest.py`, over the
WHOLE of the survey's searched frequency, not only the neighbourhoods of the
crossings.

WHY BOTH.  The nearest-transition columns need the list near a crossing; the
sensitivity case needs it everywhere, because the chance expectation the
observed count is compared with is reduced by the SAME mask: a control
position's noise maximum is attributed when its own channel falls inside the
mask, so widening the mask lowers the expectation as well as the count.  A
sensitivity case that widened one side only would be worthless.

The species set is read from `r21_lines_harvest.json` -- one detection
criterion, queried once -- and only the transitions are queried again, in
0.5 GHz chunks across the islands.  Stores f, molecule, E_u and A_ij; the
quantum numbers live in the neighbourhood file, which is what names a line.

Usage: r21_harvest_full.py [--paper DIR] [--out DIR]
"""
import csv
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r21_splat import (EU_MAX, freq_ghz, molecule, num,  # noqa: E402
                       query, union)

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ v4.23: ROUND 20'S FALLBACK PATTERN.  A bare absolute pin into
# another version directory broke the build in round 20 when that
# directory was deleted, and `cleanregen.py` cannot see a
# cross-version dependency because the predecessor is always there
# while it runs.  `verpin.py` now gates every such pin.
PAPER = (HERE if os.path.exists(os.path.join(HERE, 'ledger.json'))
         else '/workspace/SETI/paper_20pc/v4.21')
OUTDIR = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--paper':
        PAPER = sys.argv[_i + 1]
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]

CHUNK = 0.5
QDATE = subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ']).decode(
).strip()

SPEC = json.load(open(os.path.join(OUTDIR, 'r21_lines_harvest.json')))
SPECIES = set(SPEC['species'])
print('%d species from the dated detection query of %s'
      % (len(SPECIES), SPEC['query_date']), flush=True)

CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
ISL = union([(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in CAT])

SEG = []
for a, b in ISL:
    x = a
    while x < b - 1e-9:
        SEG.append((x, min(x + CHUNK, b)))
        x += CHUNK
print('%d islands -> %d chunks of at most %.1f GHz, %.3f GHz total'
      % (len(ISL), len(SEG), CHUNK, sum(b - a for a, b in SEG)), flush=True)

LINES, DROP = [], 0
for k, (a, b) in enumerate(SEG):
    t = query(a, b, line_lists=['CDMS', 'JPL'], energy_max=EU_MAX,
              energy_type='eu_k')
    n = 0
    for r in t:
        mol = molecule(r['name'])
        if mol not in SPECIES:
            DROP += 1
            continue
        f = freq_ghz(r)
        if not (a - 1e-3 <= f <= b + 1e-3):
            DROP += 1
            continue
        eu = num(r['upper_state_energy_K'])
        if eu == eu and eu > EU_MAX:
            DROP += 1
            continue
        LINES.append([round(f, 7), mol, round(eu, 2) if eu == eu else None,
                      round(num(r['aij']), 3)])
        n += 1
    if k % 20 == 0 or k == len(SEG) - 1:
        print('  chunk %3d/%d %9.3f-%9.3f  rows %5d kept %4d (total %d)'
              % (k + 1, len(SEG), a, b, len(t), n, len(LINES)), flush=True)

LINES.sort(key=lambda z: z[0])
json.dump(dict(query_date=QDATE, eu_max=EU_MAX, chunk_GHz=CHUNK,
               species_query_date=SPEC['query_date'],
               n_species=len(SPECIES), islands=ISL,
               cols=['f_GHz', 'molecule', 'eu_K', 'log_aij'],
               n_lines=len(LINES), n_dropped=DROP, lines=LINES),
          open(os.path.join(OUTDIR, 'r21_lines_full.json'), 'w'))
print('\nqueried %s: %d transitions over the searched islands, %d rows dropped'
      % (QDATE, len(LINES), DROP))
