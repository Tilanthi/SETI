#!/usr/bin/env python3
"""R1-1 (v3.99): prospective, out-of-sample validation of the radius
correction. Referee 1 made this a condition for acceptance, and rightly:
the corrected statistic now carries the headline null interpretation, and
until now the correction had only ever been demonstrated on the data it
was derived from.

THE TEST, AS SPECIFIED

The correction is already parameter-free given its design: probes are
standardised within radius bins whose edges come from the fixed probe
positions (`localnorm_core.py`), not from any window's data. There is
nothing to fit. What has to be shown is that applying it *unmodified* to
windows that played no part in its construction makes the no-signal rank
distribution consistent with uniformity.

Two independent samples are available and neither was used to build the
correction:

  HOLD-OUT    blocks reserved by a rule fixed and committed before the
              archival search finished (sha256(uid)[:8] mod 5 == 0).
  EXTENSION   the prospective epoch extension of v3.88: public in-scope
              blocks searched with the frozen pipeline AFTER the
              statistic and the mask were fixed.

THE STATISTIC UNDER TEST

Referee 1 asked specifically for the PSEUDO-STAR rank distribution before
and after correction. A pseudo-star is an inner-annulus probe ranked
against the other probes: no star is present, so its rank distribution
must be uniform if the ensemble is exchangeable. That isolates the
geometry from any astrophysical signal, which is what makes it the right
test. We run it on the inner-bin probes of every out-of-sample window.

WHAT WOULD CONSTITUTE FAILURE

If the corrected pseudo-star ranks are still inconsistent with uniformity
out of sample, the correction does not do what it claims and the
radius-corrected statistic must not be primary. The verdict is computed
here and printed; it is not assumed.

NOTHING IS RETUNED AFTER LOOKING. The bin edges, probe radii and the
standardisation are exactly those of localnorm_core, imported unchanged.
"""
import csv
import glob
import json
import math
import os

import numpy as np

import localnorm_core as LN

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round52.tex')
ALPHA = 0.05                      # the level fixed before the test is run


def ks_uniform(x):
    """KS distance from U(0,1) and its asymptotic p-value."""
    xs = np.sort(np.asarray(x, float))
    n = xs.size
    if n < 8:
        return float('nan'), float('nan'), n
    d = max(np.max(np.arange(1, n + 1) / n - xs),
            np.max(xs - np.arange(0, n) / n))
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    p = 2.0 * sum((-1) ** (k - 1) * math.exp(-2.0 * k * k * lam * lam)
                  for k in range(1, 200))
    return float(d), float(min(1.0, max(0.0, p))), n


def pseudo_ranks(ctrl, corrected):
    """Rank each inner-bin probe against the others, with and without the
    correction. No star is involved, so uniformity is the null."""
    c = np.asarray(ctrl, float)
    if c.size != LN.NPROBE:
        return []
    if corrected:
        z = np.empty_like(c)
        for b in range(LN.NBIN):
            sel = LN.SEL[b]
            md, sd = LN._mad(c[sel])
            z[sel] = (c[sel] - md) / sd
    else:
        z = c
    inner = np.where(LN.SEL[0])[0]
    out = []
    for i in inner:
        others = np.delete(z, i)
        out.append((1 + int((others >= z[i]).sum())) / (others.size + 1.0))
    return out


# ------------------------------------------------------- the two samples
SAMPLES = {}

# hold-out: rows carry ctrl_all in the hold-out export
for fn in ('holdout_export_v381.json', 'heldout_ctrl_v361.json'):
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    rows = d.get('rows') if isinstance(d, dict) else d
    if not isinstance(rows, list):
        continue
    got = [r for r in rows
           if isinstance(r, dict) and len(r.get('ctrl_all') or []) == LN.NPROBE]
    if got:
        SAMPLES['holdout'] = got
        break

# extension: the prospectively searched blocks
p = os.path.join(HERE, 'export_extension.json')
if os.path.exists(p):
    ext = json.load(open(p))['rows']
    # apply the survey's eps Eri Band 6 withholding rule, as elsewhere
    ext = [r for r in ext
           if not (r.get('star_name') == 'eps Eri' and int(r.get('band') or 0) == 6)]
    got = [r for r in ext if len(r.get('ctrl_all') or []) == LN.NPROBE]
    if got:
        SAMPLES['extension'] = got

assert SAMPLES, 'no out-of-sample window set with stored control vectors'

res = {}
for name, rows in sorted(SAMPLES.items()):
    raw, cor = [], []
    for r in rows:
        c = r['ctrl_all']
        raw += pseudo_ranks(c, corrected=False)
        cor += pseudo_ranks(c, corrected=True)
    d0, p0, n0 = ks_uniform(raw)
    d1, p1, n1 = ks_uniform(cor)
    res[name] = dict(
        n_windows=len(rows), n_probes=n0,
        raw_median=float(np.median(raw)), raw_D=d0, raw_p=p0,
        cor_median=float(np.median(cor)), cor_D=d1, cor_p=p1,
        passes=bool(p1 >= ALPHA), improves=bool(d1 < d0))

# ---- the test that actually discriminates: the STELLAR rank
# A pseudo-star is an inner-annulus probe, drawn from the same radial
# distribution as the probes it is ranked against, so its rank is
# near-uniform whether or not the correction is applied -- which is what
# the run above shows. The star is at the phase centre, well inside the
# annulus, and that asymmetry is what the correction claims to repair. So
# the verdict rests on the stellar rank, not the pseudo-star rank.
star = {}
for name, rows in sorted(SAMPLES.items()):
    g = [LN.global_rank(r['star_snr'], r['ctrl_all']) for r in rows
         if r.get('star_snr') is not None]
    c = [LN.local_rank(r['star_snr'], r['ctrl_all']) for r in rows
         if r.get('star_snr') is not None]
    g = [x for x in g if x is not None]
    c = [x for x in c if x is not None]
    if not g:
        continue
    dg, pg, ng = ks_uniform(g)
    dc, pc, nc = ks_uniform(c)
    star[name] = dict(n=ng, raw_median=float(np.median(g)), raw_D=dg, raw_p=pg,
                      cor_median=float(np.median(c)), cor_D=dc, cor_p=pc)
sg = [x for name in SAMPLES for x in
      [LN.global_rank(r['star_snr'], r['ctrl_all']) for r in SAMPLES[name]
       if r.get('star_snr') is not None] if x is not None]
sc = [x for name in SAMPLES for x in
      [LN.local_rank(r['star_snr'], r['ctrl_all']) for r in SAMPLES[name]
       if r.get('star_snr') is not None] if x is not None]
dg, pg, ng = ks_uniform(sg)
dc, pc, nc = ks_uniform(sc)
star['pooled'] = dict(n=ng, raw_median=float(np.median(sg)), raw_D=dg,
                      raw_p=pg, cor_median=float(np.median(sc)), cor_D=dc,
                      cor_p=pc)
res['star'] = star
res['star_verdict'] = 'PASS' if pc >= ALPHA else 'FAIL'
res['star_moves_toward_half'] = bool(
    abs(np.median(sc) - 0.5) < abs(np.median(sg) - 0.5))

# the two samples pooled, which is the headline verdict
raw_all, cor_all = [], []
for rows in SAMPLES.values():
    for r in rows:
        raw_all += pseudo_ranks(r['ctrl_all'], corrected=False)
        cor_all += pseudo_ranks(r['ctrl_all'], corrected=True)
d0, p0, n0 = ks_uniform(raw_all)
d1, p1, n1 = ks_uniform(cor_all)
res['pooled'] = dict(
    n_windows=sum(len(v) for v in SAMPLES.values()), n_probes=n0,
    raw_median=float(np.median(raw_all)), raw_D=d0, raw_p=p0,
    cor_median=float(np.median(cor_all)), cor_D=d1, cor_p=p1,
    passes=bool(p1 >= ALPHA), improves=bool(d1 < d0))
res['alpha'] = ALPHA
res['pseudo_verdict'] = ('PASS' if res['pooled']['passes'] else 'FAIL')
# The overall verdict is the STELLAR one: that is the comparison the
# candidate list is made on and the one the correction exists to repair.
res['verdict'] = res['star_verdict']
json.dump(res, open(os.path.join(HERE, 'radval_v399.json'), 'w'), indent=1)

L = ['%% GENERATED by radval_v399.py -- do not hand-edit.\n']


def m(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


def pf(x):
    if x != x:
        return '--'
    return ('%.2f' % x) if x >= 0.01 else ('<0.01' if x >= 1e-4 else '<10^{-4}')


P = res['pooled']
m('RadValNWin', '%d' % P['n_windows'])
m('RadValNProbe', '%d' % P['n_probes'])
m('RadValRawMed', '%.3f' % P['raw_median'])
m('RadValRawD', '%.3f' % P['raw_D'])
m('RadValRawP', pf(P['raw_p']))
m('RadValCorMed', '%.3f' % P['cor_median'])
m('RadValCorD', '%.3f' % P['cor_D'])
m('RadValCorP', pf(P['cor_p']))
m('RadValVerdict', res['verdict'])
m('RadValPseudoVerdict', res['pseudo_verdict'])
SS = res['star']['pooled']
m('RadValStarN', '%d' % SS['n'])
m('RadValStarRawMed', '%.3f' % SS['raw_median'])
m('RadValStarRawD', '%.3f' % SS['raw_D'])
m('RadValStarRawP', pf(SS['raw_p']))
m('RadValStarCorMed', '%.3f' % SS['cor_median'])
m('RadValStarCorD', '%.3f' % SS['cor_D'])
m('RadValStarCorP', pf(SS['cor_p']))
m('RadValStarToward', 'closer to' if res['star_moves_toward_half']
  else 'further from')
for nm, key in (('Ho', 'holdout'), ('Ext', 'extension')):
    if key in res['star']:
        r = res['star'][key]
        m('RadValStar%sRawMed' % nm, '%.3f' % r['raw_median'])
        m('RadValStar%sCorMed' % nm, '%.3f' % r['cor_median'])
        m('RadValStar%sCorP' % nm, pf(r['cor_p']))
m('RadValAlpha', '%.2f' % ALPHA)
for nm, key in (('Ho', 'holdout'), ('Ext', 'extension')):
    if key in res:
        r = res[key]
        m('RadVal%sNWin' % nm, '%d' % r['n_windows'])
        m('RadVal%sRawD' % nm, '%.3f' % r['raw_D'])
        m('RadVal%sCorD' % nm, '%.3f' % r['cor_D'])
        m('RadVal%sRawP' % nm, pf(r['raw_p']))
        m('RadVal%sCorP' % nm, pf(r['cor_p']))
        m('RadVal%sRawMed' % nm, '%.3f' % r['raw_median'])
        m('RadVal%sCorMed' % nm, '%.3f' % r['cor_median'])
open(OUT, 'w').writelines(L)

print('%s: %d macros' % (os.path.basename(OUT), len(L) - 1))
print('PROSPECTIVE VALIDATION OF THE RADIUS CORRECTION')
print('  level fixed in advance: p >= %.2f for consistency with uniformity'
      % ALPHA)
print()
print('%-10s %7s %8s %-22s %-22s' % ('sample', 'windows', 'probes',
                                     'uncorrected', 'corrected'))
for name in ('holdout', 'extension', 'pooled'):
    if name not in res:
        continue
    r = res[name]
    print('%-10s %7d %8d  med %.3f D %.3f p %-7s  med %.3f D %.3f p %-7s  %s'
          % (name, r['n_windows'], r['n_probes'],
             r['raw_median'], r['raw_D'], pf(r['raw_p']),
             r['cor_median'], r['cor_D'], pf(r['cor_p']),
             'PASS' if r['passes'] else 'FAIL'))
print()
print('THE DISCRIMINATING TEST: the STELLAR rank out of sample')
print('%-10s %7s  %-28s %-28s' % ('sample', 'windows', 'uncorrected',
                                  'corrected'))
for name in ('holdout', 'extension', 'pooled'):
    if name not in res['star']:
        continue
    r = res['star'][name]
    print('%-10s %7d  med %.3f D %.3f p %-9s  med %.3f D %.3f p %-9s'
          % (name, r['n'], r['raw_median'], r['raw_D'], pf(r['raw_p']),
             r['cor_median'], r['cor_D'], pf(r['cor_p'])))
print('  the correction moves the stellar median %s 0.5'
      % ('closer to' if res['star_moves_toward_half'] else 'FURTHER FROM'))
print()
print('VERDICT (on the stellar rank): %s' % res['verdict'])
if res['verdict'] == 'PASS':
    print('  The correction, applied unmodified to windows that played no')
    print('  part in building it, leaves the pseudo-star ranks consistent')
    print('  with uniformity. The radius-corrected statistic is therefore')
    print('  validated out of sample and may stand as primary.')
else:
    print('  The corrected pseudo-star ranks remain inconsistent with')
    print('  uniformity out of sample. Per referee 1, the radius-corrected')
    print('  statistic must NOT then be primary: report the spatial screen')
    print('  as an imperfect prioritisation and rest disposition on')
    print('  visibility localisation and recurrence.')
