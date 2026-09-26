#!/usr/bin/env python3
"""R2-M3: an honest before/after test of the ACA control-geometry repair.

A referee caught a real error. The manuscript compared an ACA stellar-rank
KS statistic "before" against one "after", but after the correction was
folded into the export BOTH numbers were being computed from corrected
data. The "before" value therefore already satisfied the success criterion
and the comparison demonstrated nothing.

This generator computes the comparison properly, from the two exports:

    frozen_export_v3.81_survey.json   the original geometry   ("before")
    corrected_export_v399.json        the repaired geometry   ("after")

It also reports the diagnostic the referee identifies as the one actually
sensitive to the defect -- the excess of the innermost control bin over the
outer annulus, per array -- with bootstrap intervals, and it states the
minimum shift in median rank the KS test can resolve at these sample sizes,
so a null result cannot be mistaken for evidence of repair.

Writes survey_numbers_round66.tex.
"""
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round66.tex')
SEED = 20260924
NBOOT = 2000
NBIN = 8
ANN_LO, ANN_HI, NPROBE = 0.14, 0.78, 512

ARCH = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))
EBS = ARCH['ebs']


# v4.01 (R2-M2, row 11): the KS ran on the RAW export -- 1,725 rows, 1,071 of
# them ACA -- while the rest of the paper reports 1,655 windows, 1,054 ACA.
# The extra rows are the ones the catalogue drops as duplicated, noise-
# defective, or withheld (eps Eri B6), so "the ACA stratum is now consistent
# with uniformity" was being asserted on a population the paper does not
# otherwise use, and 601 + 1,071 = 1,672 is neither 1,655 nor 1,725.  Both
# exports are now cut to the released catalogue, which also keeps the
# before/after comparison on identical windows.
import collections                                            # noqa: E402
import csv                                                    # noqa: E402


def _key(eb, a, b):
    # a descending spw has flo > fhi in the export while the catalogue always
    # writes the lower edge first, so the key must be order-free
    return (eb, round(min(a, b), 4), round(max(a, b), 4))


CATN = collections.Counter()
with open(os.path.join(HERE, 'per_target_results_v3.99.csv')) as _fh:
    for _r in csv.DictReader(_fh):
        CATN[_key(_r['eb'], float(_r['flo_GHz']), float(_r['fhi_GHz']))] += 1
NCAT = sum(CATN.values())


def load(path):
    """Export rows cut to the released catalogue's population.

    The catalogue can hold more than one row per (EB, window) -- the same
    window towards two stars of one field -- so the cut is by multiplicity,
    not by set membership: at most as many export rows per key as the
    catalogue has.  Windows the catalogue drops therefore drop out here too.
    """
    rows = json.load(open(os.path.join(HERE, path)))['rows']
    left = collections.Counter(CATN)
    keep = []
    for r in rows:
        k = _key(r['eb'], r['flo'], r['fhi'])
        if left.get(k, 0) > 0:
            left[k] -= 1
            keep.append(r)
    return keep


def arr_of(eb):
    a = EBS.get(eb, {}).get('array')
    return 'ACA' if a == '7m' else ('12m' if a == '12m' else None)


def rank(r):
    n = r.get('n_ctrl') or len(r.get('ctrl_all') or [])
    if not n:
        return None
    ge = r.get('n_ge_star')
    if ge is None:
        ca = r.get('ctrl_all') or []
        ge = sum(1 for x in ca if x >= r['star_snr'])
    return (ge + 1.0) / (n + 1.0)


def ks_uniform(u):
    u = sorted(x for x in u if x is not None)
    n = len(u)
    if n < 5:
        return None, None, None
    D = max(max((i + 1) / n - x, x - i / n) for i, x in enumerate(u))
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * D
    p = 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam)
                for k in range(1, 101))
    return D, max(0.0, min(1.0, p)), u[n // 2]


def med(v):
    v = sorted(v)
    return v[len(v) // 2] if v else float('nan')


# fractional probe radii, reproduced from the pipeline's fixed seed
def probe_u():
    import numpy as np
    rng = np.random.default_rng(20260825)
    return np.sqrt(rng.uniform(ANN_LO ** 2, ANN_HI ** 2, NPROBE))


U = probe_u()
edges = [ANN_LO + (ANN_HI - ANN_LO) * k / NBIN for k in range(NBIN + 1)]
binof = [min(NBIN - 1, max(0, next(b for b in range(NBIN - 1, -1, -1)
                                   if u >= edges[b]))) for u in U]


def inner_excess(rows, want):
    """Median standardised control level in the innermost annulus bin minus
    the outer half, for one array. This is the quantity the defect acts on."""
    prof = [[] for _ in range(NBIN)]
    for r in rows:
        if arr_of(r['eb']) != want:
            continue
        ca = r.get('ctrl_all') or []
        if len(ca) != NPROBE:
            continue
        m = med(ca)
        ad = med([abs(x - m) for x in ca]) or 1.0
        for k in range(NPROBE):
            prof[binof[k]].append((ca[k] - m) / (1.4826 * ad))
    if not prof[0]:
        return None, None, None
    inner = med(prof[0])
    outer = med([x for b in range(NBIN // 2, NBIN) for x in prof[b]])
    rnd = random.Random(SEED)
    boots = []
    for _ in range(NBOOT):
        s0 = [prof[0][rnd.randrange(len(prof[0]))] for _ in range(200)]
        pool = [x for b in range(NBIN // 2, NBIN) for x in prof[b]]
        s1 = [pool[rnd.randrange(len(pool))] for _ in range(200)]
        boots.append(med(s0) - med(s1))
    boots.sort()
    return (inner - outer, boots[int(0.025 * NBOOT)], boots[int(0.975 * NBOOT)])


def ks_power(n, alpha=0.05):
    """Smallest shift in median rank a KS test of n samples can reject at
    alpha, for a uniform-vs-shifted-uniform alternative. Reported so a pass
    is not read as proof of repair."""
    crit = 1.358 / math.sqrt(n)          # two-sided 5 per cent KS critical D
    return crit


RES = {}
for tag, path in (('Before', 'frozen_export_v3.81_survey.json'),
                  ('After', 'corrected_export_v399.json')):
    rows = load(path)
    for arr in ('ACA', '12m'):
        sel = [r for r in rows if arr_of(r['eb']) == arr and r.get('ctrl_all')]
        D, p, m_ = ks_uniform([rank(r) for r in sel])
        exc, lo, hi = inner_excess(rows, arr)
        RES[(tag, arr)] = dict(n=len(sel), D=D, p=p, med=m_, exc=exc,
                               lo=lo, hi=hi)

b, a = RES[('Before', 'ACA')], RES[('After', 'ACA')]
assert b['exc'] is not None and a['exc'] is not None, 'no control profile built'

L = ['%% GENERATED by acaverify_v399.py -- do not hand-edit.\n']


def M(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


for tag in ('Before', 'After'):
    for arr, short in (('ACA', 'Aca'), ('12m', 'Twm')):
        r = RES[(tag, arr)]
        M('Ver%s%sD' % (short, tag), '%.3f' % r['D'])
        M('Ver%s%sP' % (short, tag),
          ('<0.001' if r['p'] < 0.001 else '%.2f' % r['p']))
        M('Ver%s%sMed' % (short, tag), '%.3f' % r['med'])
        M('Ver%s%sN' % (short, tag), '%d' % r['n'])
        if r['exc'] is not None:
            M('Ver%s%sExc' % (short, tag), '%+.3f' % r['exc'])
            M('Ver%s%sExcLo' % (short, tag), '%+.3f' % r['lo'])
            M('Ver%s%sExcHi' % (short, tag), '%+.3f' % r['hi'])
M('VerKsPowerAca', '%.3f' % ks_power(a['n']))
# the population actually tested, against the released catalogue, so the text
# can state the shortfall instead of quoting a larger number from the export
_ntest = RES[('After', 'ACA')]['n'] + RES[('After', '12m')]['n']
M('VerNTested', '%s' % format(_ntest, ',').replace(',', r'\,'))
M('VerNUnmatched', '%d' % (NCAT - _ntest))
assert NCAT - _ntest < 0.01 * NCAT, \
    'too many catalogue windows have no export row: %d' % (NCAT - _ntest)
open(OUT, 'w').writelines(L)

print('ACA repair, before -> after:')
for arr in ('ACA', '12m'):
    x, y = RES[('Before', arr)], RES[('After', arr)]
    print('  %-4s KS   D %.3f (p %.3f) -> D %.3f (p %.3f)   median %.3f -> %.3f'
          % (arr, x['D'], x['p'], y['D'], y['p'], x['med'], y['med']))
    if x['exc'] is not None:
        print('       inner-bin excess %+.3f [%+.3f, %+.3f] -> %+.3f [%+.3f, %+.3f]'
              % (x['exc'], x['lo'], x['hi'], y['exc'], y['lo'], y['hi']))
print('  KS can resolve D >= %.3f at 5 per cent with n=%d'
      % (ks_power(a['n']), a['n']))
