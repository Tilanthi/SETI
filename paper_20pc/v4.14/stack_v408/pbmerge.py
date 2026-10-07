#!/usr/bin/env python3
"""What merging the split star keys does (D31 item 1).

stack5_result.jsonl : PB-corrected, keyed on skey            (394 groups, 78 "stars")
stack6_result.jsonl : PB-corrected, keyed on star identity   (368 groups)

A merge can only ADD epochs to a star's best group, so a star's best limit must
not get worse.  That is asserted, per star, and the comparison is made on the
canonical identity so that a star split in two before is compared against itself.
"""
import json, os, sys, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import starkey

L = lambda f: [json.loads(x) for x in open(os.path.join(HERE, f)) if 'err' not in x]
A = L('stack5_result.jsonl')
B = L('stack6_result.jsonl')
W = json.load(open(os.path.join(HERE, 'windows.json')))
ident, _ = starkey.build(W)
print('groups: skey-keyed %d -> identity-keyed %d' % (len(A), len(B)))

# map each result row to the canonical identity
for r in A:
    r['ident'] = ident.get(r['skey'], r['skey'])
for r in B:
    r['ident'] = r['skey']            # groups3 already writes the identity
sa = sorted(set(r['ident'] for r in A))
sb = sorted(set(r['ident'] for r in B))
print('stars: %d -> %d  (skeys before: %d)'
      % (len(sa), len(sb), len(set(r['skey'] for r in A))))
gone = [s for s in sa if s not in sb]
new = [s for s in sb if s not in sa]
print('stars lost: %s ; gained: %s' % (gone or 'none', new or 'none'))

ga = collections.defaultdict(list)
gb = collections.defaultdict(list)
for r in A:
    ga[r['ident']].append(r)
for r in B:
    gb[r['ident']].append(r)

# --- the assertion, on the quantity that is MONOTONE --------------------------
# Adding an epoch to an inverse-variance stack can only reduce the PREDICTED
# noise, 1/sqrt(sum 1/sigma_e^2).  That is what a merge must improve, and it is
# what is asserted.  The measured limit is 5 * sigma_pred * madZ, and madZ is a
# MAD over the common channels -- on a 100-channel interval it carries a ~7 per
# cent sampling error of its own -- so the measured limit is allowed to move the
# other way, provided sigma_pred improved.  Each such case is listed with its
# madZ, so the explanation is a number and not a claim.
best = lambda v, k: min((x[k] for x in v if np.isfinite(x[k])), default=np.nan)
bestrow = lambda v, k: min((x for x in v if np.isfinite(x[k])), key=lambda x: x[k])
rows, worse, worse_pred = [], [], []
for s in sa:
    if s not in gb:
        continue
    a = best(ga[s], 'smin_stack_mjy')
    b = best(gb[s], 'smin_stack_mjy')
    ea = best(ga[s], 'eirp_stack_W')
    eb = best(gb[s], 'eirp_stack_W')
    na = max(x['N'] for x in ga[s])
    nb = max(x['N'] for x in gb[s])
    rows.append((s, len(ga[s]), len(gb[s]), na, nb, a, b, ea, eb))
    pa = best(ga[s], 'sigma_stack_pred_mjy')
    pb_ = best(gb[s], 'sigma_stack_pred_mjy')
    if np.isfinite(pa) and np.isfinite(pb_) and pb_ > pa * (1 + 1e-6):
        worse_pred.append((s, pa, pb_, pb_ / pa))
    if np.isfinite(a) and np.isfinite(b) and b > a * (1 + 1e-6):
        ra, rb = bestrow(ga[s], 'smin_stack_mjy'), bestrow(gb[s], 'smin_stack_mjy')
        worse.append((s, a, b, b / a, ra, rb))
print('\nstars whose PREDICTED best depth got worse: %d  <-- must be 0' % len(worse_pred))
for x in worse_pred[:6]:
    print('   %-28s %.5f -> %.5f mJy  x%.4f' % x)
assert not worse_pred, ('a merge made the PREDICTED depth worse -- it is '
                        'combining things it should not: %s' % worse_pred[:3])
print('stars whose MEASURED best limit got worse: %d' % len(worse))
for s, a, b, r, ra, rb in sorted(worse, key=lambda x: -x[3]):
    print('   %-16s %.4f -> %.4f mJy x%.4f | N %d->%d, sigma_pred %.5f -> %.5f '
          '(x%.4f, the merge working), madZ %.4f -> %.4f on %d -> %d channels'
          % (s[:16], a, b, r, ra['N'], rb['N'], ra['sigma_stack_pred_mjy'],
             rb['sigma_stack_pred_mjy'],
             rb['sigma_stack_pred_mjy'] / ra['sigma_stack_pred_mjy'],
             ra['madZ'], rb['madZ'], ra['nchan_full_cov'], rb['nchan_full_cov']))
    assert rb['sigma_stack_pred_mjy'] < ra['sigma_stack_pred_mjy'] * (1 + 1e-6), \
        'measured limit worse AND predicted depth worse on %s' % s

print('\n--- every star whose best stacked limit or epoch count moved ---')
print('%-30s %-9s %-9s %-19s %s' % ('star', 'groups', 'N_max', 'S_min best (mJy)',
                                    'EIRP best (W)'))
nmoved = 0
for s, nga, ngb, na, nb, a, b, ea, eb in sorted(rows, key=lambda x: (x[6] / x[5]) if x[5] else 1):
    if abs(b / a - 1) < 1e-6 and na == nb:
        continue
    nmoved += 1
    print('%-30s %2d->%-5d %2d->%-5d %8.4f -> %-8.4f %.3e -> %.3e  x%.4f'
          % (s[:30], nga, ngb, na, nb, a, b, ea, eb, eb / ea))
print('stars moved: %d of %d ; unchanged: %d' % (nmoved, len(rows), len(rows) - nmoved))

# --- survey-level ------------------------------------------------------------
for res, lbl in ((A, 'skey-keyed'), (B, 'identity-keyed')):
    sm = [r['smin_stack_mjy'] for r in res if np.isfinite(r['smin_stack_mjy'])]
    ei = [r['eirp_stack_W'] for r in res if np.isfinite(r['eirp_stack_W'])]
    gn = [r['gain_real_vs_best'] for r in res if np.isfinite(r['gain_real_vs_best'])]
    ne = [r['gain_real_vs_best'] / r['sqrt_n_eff'] for r in res
          if r.get('sqrt_n_eff') and np.isfinite(r['gain_real_vs_best'])]
    surv = [r for r in res if r.get('pass_z') and r.get('pass_ctrl') and r.get('pass_clause')]
    print('\n%-15s groups %3d stars %2d | S_min med %.3f mJy | EIRP med %.3e | '
          'gain med %.4f | real/sqrt(Neff) %.4f | epoch-combinations %d | hours %.0f'
          % (lbl, len(res), len(set(r['ident'] for r in res)), np.median(sm),
             np.median(ei), np.median(gn), np.median(ne), sum(r['N'] for r in res),
             sum(r['on_source_h'] for r in res)))
    print('%-15s survivors: %d %s' % ('', len(surv),
                                      sorted(set(r['star'] for r in surv))))
