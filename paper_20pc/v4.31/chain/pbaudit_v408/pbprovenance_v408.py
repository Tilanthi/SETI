#!/usr/bin/env python3
"""ITEM 2 of D31: the provenance gap, disclosed and not reconciled.

Four released windows of HD 285968 `A002_Xd98580_X3bf6` carry a published rms that
no surviving product reproduces.  This emits the row-by-row numbers, in a form
v4.08 can quote, and CHECKS that the gap is exactly the one `DROPPED_EXTRACTIONS.md`
already declared -- two independent routes to the same four rows.

Nothing is adjusted.  In particular the two new primary-beam columns are NOT
affected: `pb_atten` comes from the pre-repair product that DOES survive at that
position, the attenuation is 0.99996 there, and `smin == 5 rms / A` still holds to
3e-6, so the gap is in the PROVENANCE of `rms_mJy` and `star_snr`, not in A.
"""
import json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pbgate_v408 as G

GAP_EB = 'A002_Xd98580_X3bf6'
GAP_STAR = 'HD 285968'
DECLARED = os.path.join(HERE, '..', 'dropped', 'exclusions_v406.json')

prods = json.load(open(os.path.join(HERE, '..', 'dropped', 'inv_products.json')))['recs']
pidx = collections.defaultdict(list)
for p in prods:
    pidx[p['eb']].append(p)
rows = G.load(0)

out = []
for c, e, g in rows:
    if c['eb'] != GAP_EB:
        continue
    lo = float(c['flo_GHz'])
    cand = [p for p in pidx[c['eb']]
            if abs(min(p['freq_lo_GHz'], p['freq_hi_GHz']) - lo) < 0.002]
    assert cand, 'no surviving product at all for %s %.3f' % (c['eb'], lo)
    p = min(cand, key=lambda x: abs(x['rms_combined_mJy'] - float(c['rms_mJy'])))
    r, rp = float(c['rms_mJy']), p['rms_combined_mJy']
    a, s = float(c['pb_atten']), float(c['smin_mJy'])
    out.append(dict(star=c['star_name'], eb=c['eb'], flo_GHz=round(lo, 4),
                    chanw_Hz=float(c['chanw_Hz']),
                    rms_published_mJy=round(r, 5), rms_surviving_product_mJy=round(rp, 5),
                    rms_discrepancy_pct=round(100 * (r - rp) / rp, 3),
                    pb_atten=a, smin_published_mJy=round(s, 5),
                    smin_from_5rms_over_A=round(5 * r / a, 5),
                    smin_residual=abs(5 * r / a - s) / s,
                    star_snr_published=float(c['star_snr']),
                    crossing=c['crossing'],
                    source='acafull_v399.json (ACA control-annulus repair, v3.99)',
                    surviving_product='pre-repair extraction at the same position',
                    reason='the repaired product was removed in the disk cleanups; '
                           'the frozen repair snapshot is now the only record'))
assert len(out) == 4, len(out)
d = max(abs(x['rms_discrepancy_pct']) for x in out)
res = max(x['smin_residual'] for x in out)
print('%s %s: %d released windows, published rms exceeds the surviving product by '
      '%.2f-%.2f %% (worst %.2f %%)'
      % (GAP_STAR, GAP_EB, len(out),
         min(abs(x['rms_discrepancy_pct']) for x in out), d, d))
print('the new pb columns are UNAFFECTED: A = %.6f-%.6f and smin == 5 rms / A to %.1e'
      % (min(x['pb_atten'] for x in out), max(x['pb_atten'] for x in out), res))
assert res < 2e-4, res
print('crossings among them: %s' % [x['flo_GHz'] for x in out if x['crossing'] == 'True'])

# --- is this the gap DROPPED_EXTRACTIONS.md already declared? ---------------
dec = json.load(open(DECLARED))['provenance_gaps']
# matched with a 2 MHz tolerance, not on a rounded key -- the declared list
# rounds 212.0465 down where this rounds it up, the same half-way case that cost
# six windows in pbcat_v408.py
mine = sorted(x['flo_GHz'] for x in out)
theirs = sorted(b for a, b, _ in dec if a == GAP_EB)
same = len(mine) == len(theirs) and all(abs(x - y) < 0.002 for x, y in zip(mine, theirs))
print('declared provenance gaps for this block: %d ; found here: %d ; same windows '
      'to 2 MHz: %s' % (len(theirs), len(mine), same))
assert same, (mine, theirs)
print('total declared provenance gaps in the release: %d (14 = 4 here + 10 windows '
      'with no product on disk at all)' % len(dec))
assert len(dec) == 14, len(dec)

json.dump(out, open(os.path.join(HERE, 'provenance_gap_v408.json'), 'w'), indent=1)
print('\n%-9s %-9s %-10s %-7s %-9s %s'
      % ('flo GHz', 'rms pub', 'rms prod', 'delta', 'T*', 'chanw'))
for x in out:
    print('%9.3f %9.5f %10.5f %6.2f%% %9.4f %.4g kHz'
          % (x['flo_GHz'], x['rms_published_mJy'], x['rms_surviving_product_mJy'],
             x['rms_discrepancy_pct'], x['star_snr_published'], x['chanw_Hz'] / 1e3))
print('wrote provenance_gap_v408.json')
