#!/usr/bin/env python3
"""ITEM 4: is the measured P90^sel biased because the injections are unattenuated?

The campaign cannot be re-run, so the consequence is quantified instead.  Two
things have to be established, and both are checked here on the 40 scored units
of the round-7 campaign (geometry read off each unit's own baseline record,
`p90_pb.json`):

  1. the UNITS the ladder is expressed in.  `campaign_p90_r7.py` L577 sets
     `s_trig = base['S_min_measured_Jy']` and `inject_vis_v401.py` adds
     `amp_Jy = f * s_trig` to the visibilities with no primary-beam factor.  If
     `S_min_measured_Jy` is the APPARENT 5 sigma (5 x rms_combined) then the
     ladder and the search threshold are in the same units and A cancels out of
     the ratio identically; if it were the CORRECTED S_min then the injected
     signal would be 1/A too bright and the measured P90/P_trig would be
     optimistic by that factor.

  2. the size of A over the configurations that were actually injected, so the
     worst case can be stated even if (1) were read the wrong way round.
"""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'p90_pb.json')))['rows']
print('scored units with geometry: %d' % len(R))

# ---- 1. the units of the ladder -------------------------------------------
e1 = [r for r in R if abs(r['strig'] - r['smin_app']) > 1e-15]
e2 = [r for r in R if abs(5 * r['rms'] * 1e-3 - r['smin_app']) / r['smin_app'] > 1e-5]
e3 = [r for r in R if abs(5 * r['rms'] * 1e-3 / r['A'] - r['smin_corr']) / r['smin_corr'] > 1e-5]
print('S_trig != S_min_measured                         : %d of %d' % (len(e1), len(R)))
print('S_min_measured != 5 x rms_combined  (APPARENT)   : %d of %d' % (len(e2), len(R)))
print('S_min_Jy       != 5 x rms / A       (CORRECTED)  : %d of %d' % (len(e3), len(R)))
assert not e1 and not e2 and not e3
# drive it the other way: if the ladder were in corrected units the two would
# differ, and on the 4 off-axis units they demonstrably do
d = [r for r in R if abs(r['smin_corr'] - r['smin_app']) / r['smin_app'] > 1e-3]
print('units where APPARENT and CORRECTED S_min differ by >0.1%%: %d '
      '(so the distinction is testable, not vacuous)' % len(d))
assert d, 'no unit distinguishes the two conventions -- the check is vacuous'
print('   e.g. %s  off=%.3f" A=%.4f  apparent %.6f Jy vs corrected %.6f Jy'
      % (d[0]['star'], d[0]['off'], d[0]['A'], d[0]['smin_app'], d[0]['smin_corr']))

# ---- 2. A over the injected configurations --------------------------------
A = sorted(r['A'] for r in R)
O = sorted(r['off'] for r in R)
print('\noffset over injected units: min %.4f" median %.4f" max %.4f"'
      % (O[0], O[len(O) // 2], O[-1]))
print('A                          : min %.6f  median %.6f  max %.6f'
      % (A[0], A[len(A) // 2], A[-1]))
for t in (0.999, 0.99, 0.95, 0.9):
    print('   A < %-5s : %d units' % (t, sum(1 for a in A if a < t)))
print('worst 1/A among injected units: %.4f ; median 1/A: %.6f'
      % (1 / A[0], 1 / A[len(A) // 2]))
print('\nunits with A < 0.999:')
for r in sorted(R, key=lambda x: x['A']):
    if r['A'] < 0.999:
        print('   %-24s class %s  %-9s off=%.4f"  A=%.6f  1/A=%.4f'
              % (r['star'][:24], r['cls'], r['array'], r['off'], r['A'], 1 / r['A']))

# ---- 3. what the release contains that the campaign never sampled ---------
pbc = json.load(open(os.path.join(HERE, 'pbcat_v408.json')))
rel = sorted(e['pb_atten'] for v in pbc.values() for e in v)
omax = max(r['off'] for r in R)
nbeyond = sum(1 for v in pbc.values() for e in v if e['pb_offset_arcsec'] > omax)
print('\nreleased windows at a larger offset than ANY injected unit (%.2f"): %d '
      'of %d' % (omax, nbeyond, len(rel)))
print('released A: min %.4f ; injected A: min %.4f -- the completeness curve is '
      'INTERPOLATED, not measured, below A = %.4f' % (rel[0], A[0], A[0]))
print('\nVERDICT: the ladder is in apparent flux and so is the 5 sigma threshold, '
      'so A cancels\nout of P90/P_trig identically -- the measured P90^sel is '
      'UNBIASED, exactly, not\napproximately.  Even on the wrong reading the bias '
      'would be <=%.1f%% and only on\n%d of %d units.  What remains true is that '
      'the campaign can never FALSIFY the\nbeam model, and that it never sampled '
      'the %d released windows beyond %.2f".'
      % (100 * (1 / A[0] - 1), sum(1 for a in A if a < 0.999), len(A), nbeyond, omax))
