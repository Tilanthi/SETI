#!/usr/bin/env python3
r"""v3.80: the stage-1 outlier taxonomy on the completed archival sweep.

The released catalogue held 443 windows and four stage-1 spatial outliers,
and the manuscript could name each of them in prose. The completed sweep
holds 1956 windows and thirteen, so the prose has to become arithmetic or it
will be wrong the next time a block lands.

What the enlarged sample actually shows, and it is the cleanest result of
the round: separate the outliers that sit on a molecular transition in the
star's own frame from those that do not, and the unattributed remainder is
what chance predicts. Eight of the thirteen are one object -- beta Pictoris,
in five Band 3 and three Band 6 windows, every one within a few km/s of
systemic on CO -- which is a single astrophysical source seen repeatedly,
not eight independent events.

Everything here is computed from the released catalogue, so the taxonomy
and the table cannot disagree.

Writes survey_numbers_round30.tex and tab_flagged_v380.tex.
"""
import csv, json, math, collections

ROWS = list(csv.DictReader(open('per_target_results_v3.81.csv')))
K = json.load(open('catalogue_constants.json'))
S = json.load(open('survey_stats.json'))
OUT = 'survey_numbers_round30.tex'
TAB = 'tab_flagged_v380.tex'
N = len(ROWS)
assert N == K['n_windows'], (N, K['n_windows'])

M = []


def m(name, val):
    M.append('\\newcommand{\\%s}{%s}' % (name, val))


def F(x):
    return None if x in ('', None) else float(x)



def _ck(n):
    """Census-name key: strip Gaia designations, SIMBAD prefixes and
    punctuation, the same normalisation canon_names_v380.py uses."""
    import re
    n = re.sub(r'\bGaia\s*DR3\s*\d+\b', '', n, flags=re.I)
    n = re.sub(r'^(NAME|V\*|V star|\*)\s+', '', n.strip(), flags=re.I)
    return re.sub(r'[^A-Za-z0-9]+', '', n).lower()


def tidy(s):
    s = ' '.join(s.split())
    for cut in ('  Gaia DR3', ' Gaia DR3'):
        if cut in s:
            s = s.split(cut)[0]
    return s.replace('CP-72', 'CP$-$72').replace('bet Pic', r'$\beta$~Pic')


# --------------------------------------------------------------- taxonomy
# The survey's own molecular tube, +-50 km/s about the transition in the
# stellar frame (v342_calc.py). A stage-1 outlier inside it is attributable
# to the star's own or foreground gas; outside it, nothing in this survey
# explains it.
TUBE_KMS = 50.0
FL = [r for r in ROWS if r['stage1_flag'] == 'True']
assert len(FL) == K['n_flagged'], (len(FL), K['n_flagged'])

attributed = [r for r in FL if abs(F(r['line_offset_kms']) or 9e9) <= TUBE_KMS]
unattributed = [r for r in FL if r not in attributed]

m('NStageOneWin', '%d' % len(FL))
m('NStageOneSys', '%d' % len({r['system_id'] for r in FL}))
m('NStageOneStars', '%d' % len({r['star_name'] for r in FL}))
m('NStageOnePairs', '%d' % len({(r['star_name'], r['band']) for r in FL}))
m('NStageOneLine', '%d' % len(attributed))
m('NStageOneUnattrib', '%d' % len(unattributed))
m('NStageOneUnattribSys', '%d' % len({r['system_id'] for r in unattributed}))

bp = [r for r in FL if r['star_name'].startswith('bet Pic')]
m('NStageOneBpic', '%d' % len(bp))
m('NStageOneBpicThree', '%d' % sum(1 for r in bp if r['band'] == '3'))
m('NStageOneBpicSix', '%d' % sum(1 for r in bp if r['band'] == '6'))
m('NStageOneNonBpic', '%d' % (len(FL) - len(bp)))
m('BpicDvLo', '%.0f' % min(F(r['line_offset_kms']) for r in bp))
m('BpicDvHi', '%.0f' % max(F(r['line_offset_kms']) for r in bp))
m('BpicTsymMax', '%.1f' % max(F(r['star_snr']) for r in bp))
m('BpicTsymMin', '%.1f' % min(F(r['star_snr']) for r in bp))
m('NStageOneBpicEb', '%d' % len({r['eb'] for r in bp}))

# --------------------------------------------- is the remainder chance?
# Under exchangeability a window is rank-first among its NCTRL controls with
# probability 1/(NCTRL+1), so the expected number of stage-1 outliers over
# the catalogue follows directly. This is the comparison the paper has
# always made; on 1956 windows it can be made against the UNATTRIBUTED
# count, which is the one chance is supposed to explain.
NCTRL = K['n_ctrl']
EXP = N / float(NCTRL + 1)
m('ExpStageOneAll', '%.1f' % EXP)
m('ExpStageOneRankFloor', '1/%d' % (NCTRL + 1))


def pois_ge(k, mu):
    """P(X >= k) for a Poisson mean mu."""
    return 1.0 - sum(math.exp(-mu) * mu ** i / math.factorial(i)
                     for i in range(k))


m('PStageOneUnattrib', '%.2f' % pois_ge(len(unattributed), EXP))
m('PStageOneAll', '%.1e' % pois_ge(len(FL), EXP))
m('StageOneUnattribRatio', '%.1f' % (len(unattributed) / EXP))

# Counting beta Pic once, as one astrophysical source rather than eight
# independent events, is the comparison a reader will want.
_eff = len(FL) - len(bp) + (1 if bp else 0)
m('NStageOneSources', '%d' % _eff)

# ------------------------------------------------------- per-flag details
by = collections.defaultdict(list)
for r in FL:
    by[(r['star_name'], r['band'])].append(r)
m('NStageOnePairsTab', '%d' % len(by))

rows = []
for (star, band), rs in sorted(
        by.items(), key=lambda kv: -max(F(r['star_snr']) for r in kv[1])):
    deep = max(rs, key=lambda r: F(r['star_snr']))
    dv = F(deep['line_offset_kms'])
    inside = abs(dv) <= TUBE_KMS
    rows.append((tidy(star), band, len(rs), deep, dv, inside))

with open(TAB, 'w') as fh:
    fh.write('% generated by v380_calc.py -- do not edit\n')
    fh.write('\\begin{tabular}{@{}llrrrrrl@{}}\n\\toprule\n')
    fh.write('Star & B & $N_{\\rm win}$ & $\\nu$ (GHz) & $T_\\star$ & '
             'ctrl & $\\Delta v$ & disposition \\\\\n\\midrule\n')
    for star, band, n, deep, dv, inside in rows:
        fh.write('%s & %s & %d & %.4f & %.2f & %.2f & %s & %s \\\\\n'
                 % (star, band, n, F(deep['f_cross_GHz']) or 0.0,
                    F(deep['star_snr']), F(deep['ctrl_max_snr']),
                    ('$%+.0f$' % dv) if dv is not None else '--',
                    deep['disposition'] or
                    ('%s in frame' % deep['nearest_line'] if inside
                     else 'unattributed')))
    fh.write('\\bottomrule\n\\end{tabular}\n')

# --------------------------------------------- where the outliers sit
# Every stage-1 outlier of the completed sweep is fine-channel. That is not
# a selection: the coarse class holds three quarters of the windows and
# predicts the larger share of chance outliers, and produces none. Narrow
# circumstellar lines are diluted by a 15.6-31.25 MHz channel, so the class
# that can resolve them is the class that finds them -- and the same logic
# says a genuine narrowband technosignature would also appear here first.
_fine = [r for r in ROWS if r['resolution_class'] == 'fine']
_coarse = [r for r in ROWS if r['resolution_class'] == 'coarse']
_ff = [r for r in _fine if r['stage1_flag'] == 'True']
_cf = [r for r in _coarse if r['stage1_flag'] == 'True']
m('NStageOneFine', '%d' % len(_ff))
m('NStageOneCoarse', '%d' % len(_cf))
m('ExpStageOneFine', '%.2f' % (len(_fine) / float(NCTRL + 1)))
m('ExpStageOneCoarse', '%.2f' % (len(_coarse) / float(NCTRL + 1)))
m('PStageOneCoarseNone', '%.2f' % math.exp(-len(_coarse) / float(NCTRL + 1)))

# ------------------------------------------- the out-of-sample null set
# 195 windows of the sweep lie beyond 40 pc: they are Option A blocks whose
# ALMA target is not a census member. They were searched by the same frozen
# pipeline, they entered no tuning decision and they are outside the sample
# the paper reports, which makes them a genuinely external null.
OS = json.load(open('outofsample_v381.json'))['rows']
m('NOutSample', '%d' % len(OS))
m('NOutSampleEb', '%d' % len({r['eb'] for r in OS}))
m('NOutSampleStars', '%d' % len({r['star_name'] for r in OS}))
m('OutSampleDistLo', '%.1f' % min(r['dist_pc'] for r in OS))
m('OutSampleDistHi', '%.1f' % max(r['dist_pc'] for r in OS))
_osf = [r for r in OS
        if r['star_snr'] is not None and r['ctrl_all']
        and r['star_snr'] >= 5.0 and r['star_snr'] > max(r['ctrl_all'])]
m('NOutSampleFlag', '%d' % len(_osf))
m('ExpOutSampleFlag', '%.1f' % (len(OS) / float(NCTRL + 1)))
# the add-one rank of the star among its own controls, which is U(0,1)
# under exchangeability
_rk = sorted((1 + sum(1 for c in r['ctrl_all'] if c >= r['star_snr']))
             / (len(r['ctrl_all']) + 1.0)
             for r in OS if r['ctrl_all'] and r['star_snr'] is not None)
if _rk:
    m('OutSampleRankMed', '%.3f' % _rk[len(_rk) // 2])
    _d = max(max((i + 1) / len(_rk) - x, x - i / len(_rk))
             for i, x in enumerate(_rk))
    m('OutSampleKsD', '%.2f' % _d)
    _lam = _d * math.sqrt(len(_rk))
    m('OutSampleKsP', '%.2f' % min(1.0, 2 * math.exp(-2 * _lam * _lam)))

# ------------------------------------------------- spectral-class proxy
# The manuscript carried a hand-typed "52 of NStars" for the number of
# searched stars with a Gaia teff_gspphot. It was measured when the sample
# held 88 stars; the sample now holds 94 and the count is 55. A literal
# beside a macro is exactly the pairing that goes stale unnoticed, so it is
# generated here from the same census the selection table uses.
import re as _re
_cen = {}
for _c in csv.DictReader(open('ranked_master40pc.csv')):
    _cen.setdefault(_ck(_c['name']), _c)
_stars = sorted({r['star_name'] for r in ROWS})
_withteff = sum(1 for _s in _stars if (_cen.get(_ck(_s)) or {}).get('teff'))
m('NTeffStars', '%d' % _withteff)
m('NCensusMatched', '%d' % sum(1 for _s in _stars if _ck(_s) in _cen))

# ----------------------------------------------------- growth of the survey
# What the completed sweep added, stated once so the text can quote it.
OLD = json.load(open('frozen_export_v3.60.json'))
m('NWinReleased', '%d' % 443)
m('NEbReleased', '%d' % 104)
m('NSysReleased', '%d' % 81)
m('NWinGrowth', '%.1f' % (N / 443.0))
m('NEbGrowth', '%.1f' % (K['n_eb'] / 104.0))

with open(OUT, 'w') as fh:
    fh.write('% generated by v380_calc.py -- do not edit\n')
    fh.write('\n'.join(M) + '\n')
print('%s: %d macros' % (OUT, len(M)))
print('stage-1: %d windows, %d star-band pairs, %d systems; '
      'line-attributed %d, unattributed %d (expected %.1f, p=%.2f)'
      % (len(FL), len(by), len({r['system_id'] for r in FL}),
         len(attributed), len(unattributed), EXP,
         pois_ge(len(unattributed), EXP)))
print('out-of-sample: %d windows, %d blocks, %d flagged (expected %.1f)'
      % (len(OS), len({r['eb'] for r in OS}), len(_osf), len(OS) / 513.0))
