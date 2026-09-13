#!/usr/bin/env python3
r"""v3.62 generated numbers.

 (1) The repaired spatial null, rerun over the whole survey (referee 1's
     principal requirement), from `radius_matched_v362.json`.
 (2) The natural false-positive rate a disc-selected archive carries
     (referee 2, major 4).
 (3) What the molecular-line mask would have cost in candidates, not only in
     bandwidth (referee 2, major 5).
 (4) The searched-domain summary in one place (referee 1, point 8).

Reads only this folder; writes `survey_numbers_round28.tex`.
"""
import csv, collections, json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = []


def M(name, val):
    OUT.append(r'\newcommand{\%s}{%s}' % (name, val))


def texval(macro):
    import glob
    for fn in sorted(glob.glob('survey_numbers*.tex')):
        m = re.search(r'\\newcommand\{\\%s\}\{(.*?)\}\s*$' % macro, open(fn).read(), re.M)
        if m:
            return m.group(1)
    raise SystemExit('%s not found' % macro)


ROWS = list(csv.DictReader(open('per_target_results_v3.62.csv')))
RM = json.load(open('radius_matched_v362.json'))
NWIN = len(ROWS)

# =====================================================================
# (1) The repaired null, rerun
# =====================================================================
M('RmInnerN', '%d' % RM['inner_n'])
M('RmInnerU', '%.2f' % RM['inner_u'])
M('RmAFlag', '%d' % len(RM['a_flagged']))
M('RmANew', '%d' % sum(1 for r in RM['a_flagged'] if not r['released']))
M('RmAExpected', '%.1f' % RM['a_expected'])
M('RmBFlag', '%d' % len(RM['b_flagged']))
M('RmBNew', '%d' % sum(1 for r in RM['b_flagged'] if not r['released']))
M('RmBLost', '%d' % sum(1 for r in RM['released'] if not r['b_flag']))
M('RmDebitCons', '%.2f' % RM['m_star'])
M('RmProfIn', '%+.2f' % RM['profile'][0])
M('RmProfMin', '%+.2f' % min(RM['profile']))
M('RmProfOut', '%+.2f' % RM['profile'][-1])
for tag, key in (('HO', 'heldout'), ('Sv', 'survey')):
    d = RM[key]
    M('Rm%sRawMed' % tag, '%.3f' % d['raw_median'])
    M('Rm%sDetMed' % tag, '%.3f' % d['det_median'])
    M('Rm%sRawD' % tag, '%.3f' % d['raw_D'])
    M('Rm%sDetD' % tag, '%.3f' % d['det_D'])


def pfmt(p):
    if p >= 0.01:
        return '%.2f' % p
    if p >= 1e-3:
        return '%.3f' % p
    e = int(math.floor(math.log10(p)))
    return r'%.0f\times10^{%d}' % (p / 10 ** e, e)


M('RmHORawP', pfmt(RM['heldout']['raw_p']))
M('RmHODetP', pfmt(RM['heldout']['det_p']))
M('RmSvRawP', pfmt(RM['survey']['raw_p']))
M('RmSvDetP', pfmt(RM['survey']['det_p']))

# the debit that centres the held-out rank distribution, and the largest debit
# each released window survives; both are in `radius_matched_v362.json`
M('RmDebitCal', '%.2f' % RM['debit_calibrated'])
SURV = {(r['star'], r['band']): r for r in RM['released']}
for key, mac in ((('bet Pic', '3'), 'RmSurvBpThree'), (('bet Pic', '6'), 'RmSurvBpSix'),
                 (('HD 48370', '6'), 'RmSurvHd'), (('CP-72 2713', '7'), 'RmSurvCp')):
    M(mac, '%.2f' % SURV[key]['survives'])
M('RmSurvMinName', min(RM['released'], key=lambda r: r['survives'])['star'])
M('RmNoNew', 'none' if not any(r for r in RM['b_flagged'] if not r['released']) else '?')

# =====================================================================
# (2) The natural false-positive rate of a disc-selected archive
# =====================================================================
S1 = [r for r in ROWS if r['stage1_flag'] == 'True']
CO1 = [r for r in S1 if 'CO' in r['disposition']]
sys_co = {r['system_id'] for r in CO1}
ndisc_sys = int(texval('NDebrisKwSys'))
ndisc_star = int(texval('NDebrisKwStars'))
M('DiscFpWin', '%d' % len(CO1))
M('DiscFpSys', '%d' % len(sys_co))
M('DiscFpOfFlags', '%d' % len(S1))
M('DiscFpRateSys', '%.0f' % (100.0 * len(sys_co) / ndisc_sys))
M('DiscFpOneIn', '%d' % round(ndisc_sys / float(len(sys_co))))
M('DiscFpRateWin', '%.1f' % (100.0 * len(CO1) / NWIN))
M('DiscFpPerClassA', '%.1f' % (100.0 * len(CO1) /
                               sum(1 for r in ROWS if r['search_class'] == 'A')))

# =====================================================================
# (3) What the mask would have cost in candidates
# =====================================================================
CROSS = [r for r in ROWS if r['crossing'] == 'True']
INMASK = [r for r in CROSS if r['line_offset_kms']
          and abs(float(r['line_offset_kms'])) <= float(texval('MaskVWidth'))]
INMASK_S1 = [r for r in INMASK if r['stage1_flag'] == 'True']
M('MaskCrossIn', '%d' % len(INMASK))
M('MaskCrossOut', '%d' % (len(CROSS) - len(INMASK)))
M('MaskCrossInStageOne', '%d' % len(INMASK_S1))
M('MaskCrossInNoFlag', '%d' % (len(INMASK) - len(INMASK_S1)))

# =====================================================================
# (4) The searched domain, in one statement
# =====================================================================
A = [r for r in ROWS if r['search_class'] == 'A']
B = [r for r in ROWS if r['search_class'] == 'B']


def rng(rows, col, scale=1.0, fmt='%.1f'):
    v = [float(r[col]) * scale for r in rows if r[col] not in ('', 'nan')]
    return fmt % min(v), fmt % max(v)


for tag, rows in (('A', A), ('B', B)):
    lo, hi = rng(rows, 'a_max_m_s2', 1.0, '%.1f')
    M('Dom%sAccelLo' % tag, lo)
    M('Dom%sAccelHi' % tag, hi)
    lo, hi = rng(rows, 'chanw_Hz', 1e-6, '%.2f')
    M('Dom%sChanLo' % tag, lo)
    M('Dom%sChanHi' % tag, hi)
    f = [min(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in rows]
    g = [max(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in rows]
    M('Dom%sFreqLo' % tag, '%.1f' % min(f))
    M('Dom%sFreqHi' % tag, '%.1f' % max(g))
    iv = sorted(zip(f, g))
    mg = []
    for a, b in iv:
        if mg and a <= mg[-1][1]:
            mg[-1][1] = max(mg[-1][1], b)
        else:
            mg.append([a, b])
    M('Dom%sUnion' % tag, '%.1f' % sum(b - a for a, b in mg))
    M('Dom%sIslands' % tag, '%d' % len(mg))

# =====================================================================
# (5) The combined response + smearing threshold (referee 1, point 5)
# =====================================================================
tot = [float(r['eirp_eff_total_W']) / float(r['eirp_nominal_W']) for r in ROWS
       if r.get('eirp_eff_total_W')]
if tot:
    M('EffTotalLo', '%.2f' % min(tot))
    M('EffTotalHi', '%.2f' % max(tot))
    M('EffTotalMed', '%.2f' % sorted(tot)[len(tot) // 2])
    _big = sum(1 for x in tot if x >= 4.0)
    M('EffTotalNBig', '%d' % _big)
    _e = [float(r['eirp_eff_total_W']) for r in ROWS if r.get('eirp_eff_total_W')]

    def sci(x):
        e = int(math.floor(math.log10(x)))
        return r'%.1f\times10^{%d}' % (x / 10 ** e, e)
    M('EffTotalMinW', sci(min(_e)))
    M('EffTotalMaxW', sci(max(_e)))

# ---------------------------------------------------------------------
_names = [re.match(r'\\newcommand\{\\([A-Za-z]+)\}', s).group(1) for s in OUT]
assert len(set(_names)) == len(_names), 'duplicate macro in this round'
import glob as _g
for fn in sorted(_g.glob('survey_numbers*.tex')):
    if fn.endswith('round28.tex'):
        continue
    txt = open(fn).read()
    for n in _names:
        if re.search(r'\\newcommand\{\\%s\}' % n, txt):
            raise SystemExit('%s already defined in %s' % (n, fn))
open('survey_numbers_round28.tex', 'w').write(
    '%% GENERATED by v362_calc.py -- do not hand-edit.\n' + '\n'.join(OUT) + '\n')
print('\n'.join(OUT))
print('%d macros' % len(OUT))
