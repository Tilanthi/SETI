#!/usr/bin/env python3
r"""r21_harvest.py -- the expanded line catalogue: a dated Splatalogue query of
CDMS and JPL for every species with a published interstellar or circumstellar
detection and an upper-state energy below 150 K.

WHY.  Referee 2's fifth point: the frozen mask holds every transition of the
twelve species the original spectral setups were tuned to, so "unattributed"
means "unattributed against a twelve-species list chosen by other observers".
The referee names two specific cases -- the beta Pictoris pair at 241.77 and
241.86 GHz in the stellar frame, which falls in the CH3OH J = 5->4 K-ladder
region the mask omits, and ALMA J153702653-33192492, a Lupus-cloud sightline
where a much wider chemistry is expected.  This file builds the wider list and
NOTHING ELSE: the frozen primary mask does not change, and the attribution it
would give is reported as a sensitivity case by `r21_lines.py`.

HOW THE REFEREE'S TWO CONDITIONS ARE IMPLEMENTED, and the asymmetry is
deliberate.

  * "a published interstellar or circumstellar detection" is a property of a
    SPECIES, so it is read at the species level: Splatalogue's own
    astronomically-observed flag, taken over every transition of the species
    that falls inside one of the survey's own searched frequency islands.  A
    species counts as detected if any one of its transitions is flagged.
  * "E_u < 150 K" is a property of a TRANSITION and is applied transition by
    transition, server-side, against the CDMS and JPL catalogues, which are
    the two the referee names and the two that carry upper-state energies.
    (The observed-line flag sits mostly on Lovas rows, which carry no E_u at
    all -- so a query asking for both conditions at once returns almost
    nothing.  That is the reason for the two-stage query, not a filter choice
    of ours.)

OUTPUT `r21_lines_harvest.json`: the species set, the transition list, and the
UTC date of the query, which is the provenance the referee asks for.  Nothing
in the paper build makes a network call; this file is run by hand and its
output is frozen, exactly as `mask_xcheck_v360.py` was.

Usage: r21_harvest.py [--paper DIR] [--out DIR]
"""
import csv
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r21_splat import (EU_MAX, clean, freq_ghz, molecule, num,  # noqa: E402
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

PAD_GHZ = 0.30            # +-0.3 GHz about each crossing: +-370 km/s at 240 GHz
C_KMS = 299792.458

# The query date is read from the clock, never typed.
QDATE = subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ']).decode(
).strip()








# ------------------------------------------------------------------ inputs
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
ISL = union([(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in CAT])
print('catalogue %d rows -> %d searched islands, %.3f GHz union'
      % (len(CAT), len(ISL), sum(b - a for a, b in ISL)), flush=True)

# the frequencies the nearest-transition columns are measured at: every
# crossing of the census in both frames, and every hold-out crossing
FR = []
LSR = json.load(open(os.path.join(PAPER, 'masklsr_v520.json')))['rows']
for r in LSR:
    FR += [r['f_lsr']]
MF = json.load(open(os.path.join(PAPER, 'maskframe_v411.json')))['rows']
for r in MF:
    FR += [r['f_stellar'], r['f_bary'], r['f_topo']]
HO = json.load(open(os.path.join(
    PAPER, 'r11inputs/events/cross_holdout.json')))
for r in HO:
    FR += [r['freq_GHz'] * (1.0 + 400.0 / C_KMS),
           r['freq_GHz'] * (1.0 - 400.0 / C_KMS)]
NEI = union([(f - PAD_GHZ, f + PAD_GHZ) for f in sorted(FR)])
print('%d frequencies -> %d neighbourhoods, %.3f GHz'
      % (len(FR), len(NEI), sum(b - a for a, b in NEI)), flush=True)

# ============================================================ stage 1: species
# Every species with an astronomically observed transition inside the searched
# islands.  This is the detection criterion, and it is read at species level.
SPEC = {}
for k, (a, b) in enumerate(ISL):
    t = query(a, b, only_astronomically_observed=True)
    n = 0
    for r in t:
        mol = molecule(r['name'])
        if not mol or 'UNIDENT' in clean(r['chemical_name']).upper():
            continue
        s = SPEC.setdefault(mol, dict(mol=mol, chem=clean(r['chemical_name']),
                                      n_obs=0, lists=[]))
        s['n_obs'] += 1
        if str(r['linelist']) not in s['lists']:
            s['lists'].append(str(r['linelist']))
        n += 1
    print('  island %2d/%d %9.3f-%9.3f  rows %5d  observed-species rows %4d'
          '  cumulative species %d'
          % (k + 1, len(ISL), a, b, len(t), n, len(SPEC)), flush=True)
print('\nstage 1: %d species carry a published detection inside the searched '
      'islands' % len(SPEC), flush=True)

# ====================================================== stage 2: transitions
# Every CDMS or JPL transition with E_u < 150 K in the neighbourhood of a
# crossing, kept where its molecule is one of stage 1's.
LINES, DROP = [], 0
for k, (a, b) in enumerate(NEI):
    t = query(a, b, line_lists=['CDMS', 'JPL'], energy_max=EU_MAX,
              energy_type='eu_k')
    n = 0
    for r in t:
        mol = molecule(r['name'])
        if mol not in SPEC:
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
        LINES.append(dict(f=f, mol=mol, chem=clean(r['chemical_name']),
                          qn=clean(r['resolved_QNs']), eu=eu,
                          aij=num(r['aij']), ll=str(r['linelist'])))
        n += 1
    print('  nbhd %2d/%d %9.3f-%9.3f  rows %5d  kept %4d  (total %d)'
          % (k + 1, len(NEI), a, b, len(t), n, len(LINES)), flush=True)

LINES.sort(key=lambda z: z['f'])
json.dump(dict(query_date=QDATE, eu_max=EU_MAX, pad_GHz=PAD_GHZ,
               islands=ISL, neighbourhoods=NEI,
               n_species=len(SPEC), species=SPEC,
               n_lines=len(LINES), n_dropped=DROP, lines=LINES),
          open(os.path.join(OUTDIR, 'r21_lines_harvest.json'), 'w'),
          indent=1, sort_keys=True)
print('\nqueried %s' % QDATE)
print('%d species, %d transitions kept, %d rows dropped'
      % (len(SPEC), len(LINES), DROP))
print('wrote r21_lines_harvest.json')
