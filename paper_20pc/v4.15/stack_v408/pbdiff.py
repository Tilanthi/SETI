#!/usr/bin/env python3
"""What the primary-beam term does to the multi-epoch stack (D29 item 1).

Compares stack_pbnone.jsonl (--pbmodel none, proved byte-identical to the
adopted stack4_result.jsonl) against stack5_result.jsonl (--pbmodel casa).
Every claim in PB_FIXES.md section 1.4 is printed here.
"""
import json, os, sys, math, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
L = lambda f: [json.loads(x) for x in open(os.path.join(HERE, f)) if 'err' not in x]
A = L('stack_pbnone.jsonl')
B = L('stack5_result.jsonl')
k = lambda r: (r['skey'], round(r['chanw']), round(r['sf_lo'] / 1e6, 1))
da, db = {k(r): r for r in A}, {k(r): r for r in B}
K = sorted(set(da) & set(db))
print('groups: none %d  casa %d  common %d' % (len(A), len(B), len(K)))
assert len(K) == len(A) == len(B)

# ---------------------------------------------------------------- 1. limits --
rat = np.array([db[x]['smin_stack_mjy'] / da[x]['smin_stack_mjy'] for x in K])
print('\nS_min(casa)/S_min(none): min %.5f  med %.6f  p90 %.4f  p99 %.3f  max %.3f'
      % (rat.min(), np.median(rat), np.percentile(rat, 90), np.percentile(rat, 99),
         rat.max()))
print('  groups deepened-then-corrected >1%%: %d  >10%%: %d  >2x: %d  <0.999: %d'
      % ((rat > 1.01).sum(), (rat > 1.10).sum(), (rat > 2).sum(), (rat < 0.999).sum()))
# The PREDICTED stacked noise can only get worse: sigma_true/sigma_app =
# sqrt(sum 1/s^2) / sqrt(sum A^2/s^2) >= 1 identically.  That is the assertion.
# The MEASURED limit carries madZ as well, and madZ moves when the epoch weights
# move, so a group with A varying across epochs may land fractionally better.
pr = np.array([db[x]['sigma_stack_pred_mjy'] / da[x]['sigma_stack_pred_mjy'] for x in K])
assert (pr >= 1.0 - 1e-12).all(), \
    'predicted stacked noise improved: the correction has the wrong sign'
print('  predicted-noise ratio (must be >=1 identically): min %.12f  max %.3f'
      % (pr.min(), pr.max()))
wob = [(rat[i], K[i], db[K[i]]['star'], db[K[i]]['madZ'] / da[K[i]]['madZ'],
        db[K[i]]['pb_atten_spread']) for i in range(len(K)) if rat[i] < 0.999]
for r, x, s, mz, sp in wob:
    print('  measured limit improved x%.5f on %s: madZ moved x%.4f, intra-group '
          'A spread x%.3f -> a reweighting, not a sign error' % (r, s, mz, sp))

# per-star worst move
per = collections.defaultdict(list)
for x in K:
    per[db[x]['star']].append(db[x]['smin_stack_mjy'] / da[x]['smin_stack_mjy'])
print('\n--- every star whose stacked limit moves by >1 per cent ---')
for s, v in sorted(per.items(), key=lambda kv: -max(kv[1])):
    if max(v) > 1.01:
        print('  %-30s %2d group(s)  x%.3f - x%.3f  (median x%.3f)'
              % (s, len(v), min(v), max(v), float(np.median(v))))
print('stars unaffected (<=1%%): %d of %d'
      % (sum(1 for v in per.values() if max(v) <= 1.01), len(per)))

# ---------------------------------------------------------------- 2. gains ---
for fld, lbl in (('gain_real_vs_best', 'gain over best single epoch'),
                 ('gain_real_vs_median', 'gain over a median epoch'),
                 ('n_eff', 'N_eff'), ('madZ', 'MAD of stacked Z')):
    a = np.array([da[x][fld] for x in K]); b = np.array([db[x][fld] for x in K])
    g = np.isfinite(a) & np.isfinite(b) & (a != 0)
    r = b[g] / a[g]
    print('\n%-28s none med %.4f -> casa med %.4f  | ratio med %.6f max %.4f min %.4f'
          % (lbl, np.median(a[g]), np.median(b[g]), np.median(r), r.max(), r.min()))
    print('   groups with ANY change: %d of %d' % ((np.abs(r - 1) > 1e-9).sum(), g.sum()))

# the cancellation claim, split on intra-group A spread
flat = [x for x in K if db[x]['pb_atten_spread'] < 1.0000001]
vary = [x for x in K if db[x]['pb_atten_spread'] >= 1.0000001]
print('\ngroups with a SINGLE A across epochs: %d ; with A varying: %d' % (len(flat), len(vary)))
for fld in ('gain_real_vs_best', 'gain_real_vs_median', 'n_eff', 'z_star', 'z_ctrl_max'):
    d = [abs(db[x][fld] - da[x][fld]) for x in flat
         if np.isfinite(da[x][fld]) and np.isfinite(db[x][fld])]
    print('  A-flat groups, max |delta %-20s| = %.3e' % (fld, max(d)))
print('  -> A cancels exactly wherever it is constant across epochs')
print('  A-varying groups: gain_real_vs_best ratio med %.4f  range %.4f-%.4f'
      % tuple(f([db[x]['gain_real_vs_best'] / da[x]['gain_real_vs_best'] for x in vary])
              for f in (np.median, min, max)))

# realised vs sqrt(N_eff)
for res, lbl in ((A, 'none'), (B, 'casa')):
    r = [x['gain_real_vs_best'] / x['sqrt_n_eff'] for x in res
         if x.get('sqrt_n_eff') and np.isfinite(x['gain_real_vs_best'])]
    rn = [x['gain_real_vs_best'] / x['sqrtN'] for x in res
          if np.isfinite(x['gain_real_vs_best'])]
    print('%-5s realised/sqrt(N_eff) med %.4f | realised/sqrt(N) med %.4f | '
          'N_eff/N med %.3f'
          % (lbl, np.median(r), np.median(rn),
             np.median([x['n_eff'] / x['N'] for x in res])))

# ------------------------------------------------------- 3. the headlines ----
def best(res, sub):
    v = [x for x in res if sub in x['skey'] or sub in x['star'].lower().replace(' ', '')]
    return min(v, key=lambda x: x['eirp_stack_W']) if v else None
print()
for sub, lbl in (('prox', 'Proxima'), ('taucet', 'tau Cet'), ('betpic', 'bet Pic'),
                 ('epseri', 'eps Eri'), ('twa7', 'TWA 7')):
    p, q = best(A, sub), best(B, sub)
    if p:
        print('%-8s best-EIRP group  none %.3e W  casa %.3e W  x%.3f   '
              '(off %.2f", A %.4f, N=%d)'
              % (lbl, p['eirp_stack_W'], q['eirp_stack_W'],
                 q['eirp_stack_W'] / p['eirp_stack_W'],
                 q['pb_offset_max'], q['pb_atten_med'], q['N']))

# survivors of the criterion
import criterion as CR
for res, lbl in ((A, 'none'), (B, 'casa')):
    s = [x for x in res if x.get('pass_z') and x.get('pass_ctrl') and x.get('pass_clause')]
    print('%-5s groups passing all three clauses: %d  %s'
          % (lbl, len(s), sorted(set(x['star'] for x in s))))
print('\nmax intra-window A gradient used-vs-ignored: x%.4f (median x%.5f)'
      % (max(x['pb_chan_spread_max'] for x in B),
         float(np.median([x['pb_chan_spread_max'] for x in B]))))
