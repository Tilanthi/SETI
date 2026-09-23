#!/usr/bin/env python3
"""v3.95: the radius-corrected statistic becomes the PRIMARY analysis.

Both referees required this. The reasoning, which the manuscript now
states explicitly, is that the radial displacement of the stellar rank is
not a post-hoc rationalisation but a characterised instrumental effect
with a known mechanism: images are primary-beam corrected, so the true
noise rises with distance from the pointing centre, while the search
divides every position by one global scale. The control probes therefore
sit at systematically different effective noise from the star, which is at
the phase centre. Correctness takes priority over the order of discovery.

What this generator produces:

 1. The primary candidate list under the radius-corrected statistic, and
    the frozen-statistic list beside it as a documented robustness
    comparison.
 2. The correctly conditioned null for the CORRECTED statistic. A stage-1
    event needs the position both to outrank every radius-standardised
    probe and to reach the trigger, so only windows whose control maximum
    reaches the trigger can produce one. Block-resampled, with the
    pseudo-star tail factor and -- new in v3.95, at referee 2's request --
    its measured 1.2-1.9 uncertainty folded into the interval rather than
    left as a separate caveat.
 3. Tail probabilities rounded to ONE significant figure, since the count
    is 2 and the rate normalisation is uncertain by up to a factor 1.6.
"""
import collections
import csv
import json
import math
import os

import numpy as np

import localnorm_core as LN

HERE = os.path.dirname(os.path.abspath(__file__))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.95.csv'))))
OUT = os.path.join(HERE, 'survey_numbers_round51.tex')
TRIG = 5.0
TUBE_KMS = 50.0
NBOOT = 20000
RNG = np.random.default_rng(20260922)

# the pseudo-star tail factor and its measured range (Appendix G.10.3)
TAIL, TAIL_LO, TAIL_HI = 1.4, 1.2, 1.9


def F(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def attributed(r):
    v = F(r['line_offset_kms'])
    return v is not None and abs(v) <= TUBE_KMS


# ---------------------------------------------------------- the two lists
frozen = [r for r in CAT if r['stage1_flag'] == 'True']
corr = [r for r in CAT if r['stage1_flag_local'] == 'True']
fz_un = [r for r in frozen if not attributed(r)]
co_un = [r for r in corr if not attributed(r)]
lost = [r for r in frozen if r['stage1_flag_local'] != 'True']
gained = [r for r in corr if r['stage1_flag'] != 'True']

# ------------------------------------------- the null for the CORRECTED statistic
# Load the stored control vectors. The corrected statistic standardises
# each probe within its own radius bin, so a no-signal position reproduces
# a stage-1 event only if it is the maximum of the standardised ensemble
# AND reaches the trigger.
EXP = None
for fn in ('frozen_export_v3.81.json', 'frozen_export_v3.80.json'):
    p = os.path.join(HERE, fn)
    if os.path.exists(p):
        EXP = json.load(open(p))['rows']
        break
assert EXP is not None, 'no frozen export with control vectors'

KEY = {(r['eb'], round(min(F(r['flo_GHz']), F(r['fhi_GHz'])), 4)) for r in CAT}
byblock = collections.defaultdict(list)
seen = set()
nwin = 0
nelig = 0
for r in EXP:
    c = r.get('ctrl_all') or []
    if len(c) != LN.NPROBE:
        continue
    k = (r['eb'], round(min(r['flo'], r['fhi']), 4))
    if k in seen or k not in KEY:
        continue
    seen.add(k)
    nwin += 1
    ca = np.asarray(c, float)
    # standardise the probes exactly as local_rank does
    z = np.empty_like(ca)
    for b in range(LN.NBIN):
        s = LN.SEL[b]
        md, sd = LN._mad(ca[s])
        z[s] = (ca[s] - md) / sd
    # A no-signal position at the star's place draws from the innermost
    # bin's distribution. It reproduces a stage-1 event only if it tops
    # the standardised ensemble and the window can reach the trigger at
    # all, i.e. its raw control maximum does.
    eligible = ca.max() >= TRIG
    if eligible:
        nelig += 1
    pw = (1.0 / (z.size + 1.0)) if eligible else 0.0
    byblock[r['eb']].append(pw)

blocks = sorted(byblock)
assert blocks, 'no blocks with control vectors'


def draw(tail):
    tot = 0
    for _ in range(len(blocks)):
        b = blocks[RNG.integers(len(blocks))]
        ps = np.asarray(byblock[b], float) * tail
        tot += int(RNG.random(ps.size).__lt__(ps).sum())
    return tot


def tail_stats(tail):
    d = np.asarray([draw(tail) for _ in range(NBOOT)])
    return d


obs = len(co_un)
d_mid = tail_stats(TAIL)
d_lo = tail_stats(TAIL_LO)
d_hi = tail_stats(TAIL_HI)


def onesig(x):
    """One significant figure, as referee 2 requires."""
    if x <= 0:
        return '0'
    e = int(math.floor(math.log10(x)))
    v = round(x, -e)
    return ('%.*f' % (max(0, -e), v)) if e < 0 else '%d' % int(v)


p_mid = float((d_mid >= obs).mean())
p_lo = float((d_hi >= obs).mean())      # larger tail factor -> larger p
p_hi = float((d_lo >= obs).mean())      # smaller tail factor -> smaller p
mean_mid = float(d_mid.mean())

# the same, for the frozen statistic, as the robustness comparison
fz_obs = len(fz_un)
byblock_fz = collections.defaultdict(list)
seen = set()
for r in EXP:
    c = r.get('ctrl_all') or []
    if len(c) != LN.NPROBE:
        continue
    k = (r['eb'], round(min(r['flo'], r['fhi']), 4))
    if k in seen or k not in KEY:
        continue
    seen.add(k)
    ca = np.asarray(c, float)
    byblock_fz[r['eb']].append((1.0 / (ca.size + 1.0)) if ca.max() >= TRIG else 0.0)


def draw_fz(tail):
    tot = 0
    for _ in range(len(blocks)):
        b = blocks[RNG.integers(len(blocks))]
        ps = np.asarray(byblock_fz[b], float) * tail
        tot += int(RNG.random(ps.size).__lt__(ps).sum())
    return tot


d_fz = np.asarray([draw_fz(TAIL) for _ in range(NBOOT)])
p_fz = float((d_fz >= fz_obs).mean())

res = dict(
    n_frozen=len(frozen), n_corrected=len(corr),
    n_frozen_unattrib=fz_obs, n_corrected_unattrib=obs,
    n_lost=len(lost), n_gained=len(gained),
    lost=[(r['star_name'], r['band']) for r in lost],
    gained=[(r['star_name'], r['band']) for r in gained],
    n_windows=nwin, n_eligible=nelig,
    mean=mean_mid, p=p_mid, p_lo=p_lo, p_hi=p_hi,
    tail=TAIL, tail_lo=TAIL_LO, tail_hi=TAIL_HI,
    frozen_p=p_fz, frozen_mean=float(d_fz.mean()),
    q95=[int(np.percentile(d_mid, 2.5)), int(np.percentile(d_mid, 97.5))],
)
json.dump(res, open(os.path.join(HERE, 'primary_v395.json'), 'w'), indent=1)

L = ['%% GENERATED by primary_v395.py -- do not hand-edit.\n']


def m(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


assert len(corr) == (len(corr) - obs) + obs, 'identity'
# The conclusions once printed the FROZEN attributed count (9) beside the
# corrected totals, so 9 + 2 = 11 did not equal 10. Assert the identity the
# prose depends on, in both directions.
assert (len(corr) - obs) + obs == len(corr), 'corrected counts must close'
assert (len(frozen) - fz_obs) + fz_obs == len(frozen), 'frozen counts must close'
m('PriNStageOne', '%d' % len(corr))
m('PriNUnattrib', '%d' % obs)
m('PriNAttrib', '%d' % (len(corr) - obs))
m('PriNLost', '%d' % len(lost))
m('PriNGained', '%d' % len(gained))
m('PriMean', '%.1f' % mean_mid)
m('PriP', onesig(p_mid))
m('PriPLo', onesig(min(p_lo, p_hi)))
m('PriPHi', onesig(max(p_lo, p_hi)))
m('PriNWin', '%d' % nwin)
m('PriNElig', '%d' % nelig)
m('PriTail', '%.1f' % TAIL)
m('PriTailLo', '%.1f' % TAIL_LO)
m('PriTailHi', '%.1f' % TAIL_HI)
m('PriQLo', '%d' % res['q95'][0])
m('PriQHi', '%d' % res['q95'][1])
# the frozen statistic, as the robustness comparison
m('RobNStageOne', '%d' % len(frozen))
m('RobNUnattrib', '%d' % fz_obs)
m('RobP', onesig(p_fz))
m('RobMean', '%.1f' % float(d_fz.mean()))
open(OUT, 'w').writelines(L)

print('%s: %d macros' % (os.path.basename(OUT), len(L) - 1))
print('PRIMARY = radius-corrected statistic')
print('  stage-1 events      : %d  (%d attributed, %d unattributed)'
      % (len(corr), len(corr) - obs, obs))
print('  vs frozen statistic : %d  (%d attributed, %d unattributed)'
      % (len(frozen), len(frozen) - fz_obs, fz_obs))
print('  changes             : %d lost, %d gained' % (len(lost), len(gained)))
for r in lost:
    print('     lost   %-30s %s' % (r['star_name'][:30], r['band']))
for r in gained:
    print('     gained %-30s %s' % (r['star_name'][:30], r['band']))
print()
print('  NULL for the corrected statistic, over %d windows (%d trigger-eligible)'
      % (nwin, nelig))
print('     expected %.2f, 95%% interval %d-%d' % (mean_mid, *res['q95']))
print('     observed %d  ->  P(>=%d) = %s  (range %s-%s over the tail '
      'factor %.1f-%.1f)'
      % (obs, obs, onesig(p_mid), onesig(min(p_lo, p_hi)),
         onesig(max(p_lo, p_hi)), TAIL_LO, TAIL_HI))
print('  ROBUSTNESS, frozen statistic: observed %d, expected %.2f, P = %s'
      % (fz_obs, float(d_fz.mean()), onesig(p_fz)))
