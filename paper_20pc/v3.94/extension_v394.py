#!/usr/bin/env python3
"""v3.94: the prospective epoch extension.

WHAT THIS IS, AND WHY IT IS NOT MERGED INTO THE SCIENCE SAMPLE

The 123 execution blocks searched here are public, in scope, and were
never part of the frozen survey: `make_worklist.py` had been built against
the v3.43-era archive map (102 member OUS, 448 progenitors) and could not
see them, so the v3.81 map (152 OUS, 656 progenitors) exposed them for the
first time. They were searched with the frozen pipeline AFTER the
detection statistic and the molecular-line mask were fixed.

That ordering is the whole value of this sample, and merging it into the
science sample would destroy it: the paper's statistics rest on a
denominator and a candidate list that were fixed before the data were
looked at. So the frozen sample stays exactly as published, and this is
reported as a prospective extension with its own null.

WHAT IT BUYS

Every block is repeat coverage of a star and tuning already searched, so
it adds no star, no system and no frequency. It adds EPOCHS, which is the
axis on which the survey was weakest: 27 of 82 systems had a single
searched epoch and therefore admitted no confirmation at all.

THREE THINGS ARE MEASURED

 1. Coverage: blocks, windows, stars, systems, volume, and the change in
    the number of systems that now have more than one searched epoch.
 2. The null on unseen data: the add-one rank distribution, its KS
    distance from uniform, the threshold-crossing rate and the stage-1
    count against the expectation the paper's own calibration predicts.
 3. The positive control: whether the beta Pictoris disc CO is recovered
    in epochs the survey had never searched.
"""
import collections
import csv
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = json.load(open(os.path.join(HERE, 'export_extension.json')))
CAT = list(csv.DictReader(open(os.path.join(HERE,
                                            'per_target_results_v3.94.csv'))))
OUT = os.path.join(HERE, 'survey_numbers_round50.tex')
TRIG = 5.0


def F(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


ALL = [r for r in EXT['rows'] if r.get('star_snr') is not None]
# Apply the survey's own withholding rule: eps Eri Band 6 sits at ~0.7
# primary-beam FWHM, where the Gaussian beam form used for the correction
# is not valid (survey_stats.py:40). Every eps Eri block in this campaign
# is Band 6, so all of them are withheld, exactly as in the frozen sample.
WITHHELD = [r for r in ALL
            if r['star_name'] == 'eps Eri' and int(r.get('band') or 0) == 6]
ROWS = [r for r in ALL if r not in WITHHELD]
assert ROWS, 'no extension rows'
assert not [r for r in ROWS if r['star_name'] == 'eps Eri'], \
    'eps Eri must be fully withheld'

# ------------------------------------------------- 1. coverage
blocks = sorted({r['eb'] for r in ROWS})
stars = sorted({r['star_name'] for r in ROWS})
fine = [r for r in ROWS if str(r.get('res', '')).startswith('fine')]
coarse = [r for r in ROWS if not str(r.get('res', '')).startswith('fine')]


def union(iv):
    iv = sorted((min(a, b), max(a, b)) for a, b in iv)
    tot, clo, chi = 0.0, None, None
    for lo, hi in iv:
        if clo is None:
            clo, chi = lo, hi
        elif lo <= chi:
            chi = max(chi, hi)
        else:
            tot += chi - clo
            clo, chi = lo, hi
    if clo is not None:
        tot += chi - clo
    return tot


uni = union([(r['flo'], r['fhi']) for r in ROWS
             if r.get('flo') and r.get('fhi')])
uniA = union([(r['flo'], r['fhi']) for r in fine
              if r.get('flo') and r.get('fhi')])

# map the extension's star names onto the catalogue's systems, so the
# epoch improvement is counted on the paper's own system definition
name2sys = {}
for r in CAT:
    name2sys.setdefault(r['star_name'], r['system_id'])
# the extension uses base names; match on a normalised key
def norm(s):
    return ''.join(ch for ch in s.lower() if ch.isalnum())


bykey = {}
for r in CAT:
    bykey.setdefault(norm(r['star_name']), r['system_id'])
    # also index the leading token set, e.g. "HD 53143 Gaia DR3 ..." -> "hd53143"
    bykey.setdefault(norm(r['star_name'].split('Gaia')[0]), r['system_id'])

ext_sys = {}
unmatched = []
for s in stars:
    k = norm(s)
    sysid = bykey.get(k) or bykey.get(norm(s.replace('*', '').strip()))
    if sysid is None:
        # last resort: prefix match
        cand = [v for kk, v in bykey.items() if kk and (kk.startswith(k) or k.startswith(kk))]
        sysid = cand[0] if cand else None
    if sysid is None:
        unmatched.append(s)
    else:
        ext_sys[s] = sysid

# epochs per system, before and after
before = collections.defaultdict(set)
for r in CAT:
    before[r['system_id']].add(r['eb'])
after = {k: set(v) for k, v in before.items()}
for r in ROWS:
    sysid = ext_sys.get(r['star_name'])
    if sysid:
        after.setdefault(sysid, set()).add(r['eb'])
one_before = {k for k, v in before.items() if len(v) == 1}
one_after = {k for k, v in after.items() if len(v) == 1}
multi_before = sum(1 for v in before.values() if len(v) > 1)
multi_after = sum(1 for v in after.values() if len(v) > 1)
gained = sorted(one_before - one_after)

# ------------------------------------------------- 2. the null on unseen data
def addone(r):
    c = r.get('ctrl_all') or []
    if not c or r.get('star_snr') is None:
        return None
    n = sum(1 for x in c if x >= r['star_snr'])
    return (n + 1.0) / (len(c) + 1.0)


ranks = [addone(r) for r in ROWS]
ranks = [x for x in ranks if x is not None]
rs = np.sort(np.asarray(ranks))
n = rs.size
D = max(np.max(np.arange(1, n + 1) / n - rs), np.max(rs - np.arange(0, n) / n))
lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * D
p = 2.0 * sum((-1) ** (k - 1) * math.exp(-2.0 * k * k * lam * lam)
              for k in range(1, 100))
p = min(1.0, max(0.0, p))

cross = [r for r in ROWS if (r.get('_n_hits') or 0) > 0]
rank1 = [r for r in ROWS if r.get('n_ge_star') == 0]
stage1 = [r for r in ROWS if (r.get('_n_hits') or 0) > 0 and r.get('n_ge_star') == 0]

# the expectation the paper's own calibration gives for this many windows:
# rank-first requires the star to beat 512 controls, and a stage-1 event
# also requires the trigger, so only windows whose control maximum reaches
# the trigger can produce one (the v3.87 conditioning).
elig = [r for r in ROWS if (r.get('ctrl_all') and max(r['ctrl_all']) >= TRIG)]
TAIL = 1.4
exp_rank1 = TAIL * len(ROWS) / 513.0
exp_stage1 = TAIL * len(elig) / 513.0

# ------------------------------------------------- 3. the positive control
bp = [r for r in stage1 if 'bet Pic' in r['star_name']]
bp.sort(key=lambda r: -(r['star_snr'] or 0))

res = dict(
    n_blocks=len(blocks), n_windows=len(ROWS), n_stars=len(stars),
    n_systems=len(set(ext_sys.values())), n_fine=len(fine), n_coarse=len(coarse),
    union_GHz=uni, unionA_GHz=uniA,
    unmatched_stars=unmatched,
    systems_one_epoch_before=len(one_before),
    systems_one_epoch_after=len(one_after),
    systems_multi_before=multi_before, systems_multi_after=multi_after,
    systems_gained_second_epoch=gained,
    rank_median=float(np.median(rs)), rank_ks_D=float(D), rank_ks_p=float(p),
    n_ranked=int(n),
    n_cross=len(cross), n_rank1=len(rank1), n_stage1=len(stage1),
    n_eligible=len(elig),
    exp_rank1=exp_rank1, exp_stage1=exp_stage1,
    bpic=[dict(eb=r['eb'], T=r['star_snr'], ctrl=r['ctrl_max'],
               f=r.get('_star_peak_freq'), line=r.get('line'),
               off=r.get('line_off')) for r in bp],
    snapshot=EXT['snapshot'],
)
json.dump(res, open(os.path.join(HERE, 'extension_v394.json'), 'w'),
          indent=1, default=str)

L = ['%% GENERATED by extension_v394.py -- do not hand-edit.\n']


def m(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


def sci(v):
    e = int(math.floor(math.log10(abs(v))))
    return '%.1f\\times10^{%d}' % (v / 10.0 ** e, e)


m('ExtBlocks', '%d' % len(blocks))
m('ExtWindows', '%d' % len(ROWS))
m('ExtStars', '%d' % len(stars))
m('ExtSystems', '%d' % len(set(ext_sys.values())))
m('ExtFine', '%d' % len(fine))
m('ExtCoarse', '%d' % len(coarse))
m('ExtUnion', '%.1f' % uni)
m('ExtUnionA', '%.1f' % uniA)
m('ExtSysOneBefore', '%d' % len(one_before))
m('ExtSysOneAfter', '%d' % len(one_after))
m('ExtSysMultiBefore', '%d' % multi_before)
m('ExtSysMultiAfter', '%d' % multi_after)
m('ExtSysGained', '%d' % len(gained))
m('ExtRankMed', '%.3f' % np.median(rs))
m('ExtRankKsD', '%.3f' % D)
m('ExtRankKsP', ('%.2f' % p) if p >= 0.01 else '<0.01')
m('ExtNRanked', '%d' % n)
m('ExtNCross', '%d' % len(cross))
m('ExtCrossPct', '%.2f' % (100.0 * len(cross) / len(ROWS)))
m('ExtNRankOne', '%d' % len(rank1))
m('ExtExpRankOne', '%.1f' % exp_rank1)
m('ExtNStageOne', '%d' % len(stage1))
m('ExtExpStageOne', '%.2f' % exp_stage1)
m('ExtNEligible', '%d' % len(elig))
m('ExtNBpic', '%d' % len(bp))
if bp:
    m('ExtBpicTHi', '%.2f' % bp[0]['star_snr'])
    m('ExtBpicTLo', '%.2f' % bp[-1]['star_snr'])
    m('ExtBpicCtrlHi', '%.2f' % max(r['ctrl_max'] for r in bp))
    m('ExtBpicFreqLo', '%.4f' % min(r['_star_peak_freq'] for r in bp
                                    if r.get('_star_peak_freq')))
    m('ExtBpicFreqHi', '%.4f' % max(r['_star_peak_freq'] for r in bp
                                    if r.get('_star_peak_freq')))
    m('ExtBpicOffLo', '%.1f' % min(abs(r['line_off']) for r in bp
                                   if r.get('line_off') is not None))
    m('ExtBpicOffHi', '%.1f' % max(abs(r['line_off']) for r in bp
                                   if r.get('line_off') is not None))
m('ExtSnapshot', EXT['snapshot'].replace('T', ' ').replace('Z', ' UTC'))
m('ExtWithheldWin', '%d' % len(WITHHELD))
m('ExtWithheldBlocks', '%d' % len({r['eb'] for r in WITHHELD}))
m('ExtNUnattrib', '%d' % (len(stage1) - len(bp)))
open(OUT, 'w').writelines(L)

# ---- the table, generated so it cannot drift from the macros
T = [r'\begin{tabular}{@{}lrr@{}}', r'\toprule',
     r' & frozen sample & extension \\', r'\midrule']
frozen_blocks = len({r['eb'] for r in CAT})
frozen_win = len(CAT)
frozen_stars = len({r['star_name'] for r in CAT})
frozen_sys = len({r['system_id'] for r in CAT})
frozen_A = sum(1 for r in CAT if r['search_class'] == 'A')
# every frozen number by the SAME definition used on the extension
fz_cross = sum(1 for r in CAT if r['crossing'] == 'True')
fz_rank1 = sum(1 for r in CAT if (r['n_ctrl_ge_star'] or '').strip() == '0')
fz_stage1 = sum(1 for r in CAT if r['stage1_flag'] == 'True')
fz_line = sum(1 for r in CAT if r['stage1_flag'] == 'True'
              and abs(F(r['line_offset_kms']) or 9e9) <= 50.0)
fz_unatt = fz_stage1 - fz_line
fz_rank = [None]
_ar = []
for r in CAT:
    v = F(r['p_rank_addone'])
    if v is not None:
        _ar.append(v)
fz_rankmed = float(np.median(_ar)) if _ar else float('nan')
T += [r'execution blocks & %d & %d \\' % (frozen_blocks, len(blocks)),
      r'windows & %d & %d \\' % (frozen_win, len(ROWS)),
      r'\quad Class~A & %d & %d \\' % (frozen_A, len(fine)),
      r'stars & %d & %d \\' % (frozen_stars, len(stars)),
      r'systems & %d & %d \\' % (frozen_sys, len(set(ext_sys.values()))),
      r'\midrule',
      r'threshold crossings & %d & %d \\' % (fz_cross, len(cross)),
      r'rank-first windows & %d & %d \\' % (fz_rank1, len(rank1)),
      r'stage-1 events & %d & %d \\' % (fz_stage1, len(stage1)),
      r'\quad attributed to CO & %d & %d \\' % (fz_line, len(bp)),
      r'\quad unattributed & \textbf{%d} & \textbf{%d} \\'
      % (fz_unatt, len(stage1) - len(bp)),
      r'\midrule',
      r'median add-one rank & %.3f & %.3f \\' % (fz_rankmed, float(np.median(rs))),
      r'\bottomrule', r'\end{tabular}']
# these must agree with what the paper already publishes
import re as _re
def _pub(name):
    for fn in sorted(os.listdir(HERE)):
        if fn.startswith('survey_numbers_round') and fn.endswith('.tex'):
            mm = _re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name,
                            open(os.path.join(HERE, fn)).read())
            if mm:
                return mm.group(1)
    return None
for _nm, _v in (('NHits', fz_cross), ('NStageOneWin', fz_stage1),
                ('NStageOneLine', fz_line), ('NStageOneUnattrib', fz_unatt)):
    _p = _pub(_nm)
    if _p is not None:
        assert int(_p) == _v, ('%s: paper says %s, catalogue gives %d'
                               % (_nm, _p, _v))
        print('  cross-check %-20s paper %-5s == catalogue %d' % (_nm, _p, _v))
open(os.path.join(HERE, 'tab_extension_v394.tex'), 'w').write('\n'.join(T) + '\n')

print('%s: %d macros; tab_extension_v394.tex written'
      % (os.path.basename(OUT), len(L) - 1))
print('PROSPECTIVE EXTENSION, snapshot %s' % EXT['snapshot'])
print('  withheld by the survey rule (eps Eri B6): %d windows in %d blocks'
      % (len(WITHHELD), len({r['eb'] for r in WITHHELD})))
print('  %d blocks, %d windows (%d fine / %d coarse), %d stars, %d systems'
      % (len(blocks), len(ROWS), len(fine), len(coarse), len(stars),
         len(set(ext_sys.values()))))
if unmatched:
    print('  WARNING unmatched star names: %s' % unmatched)
print('  unique frequency %.1f GHz (%.1f GHz fine)' % (uni, uniA))
print('  systems with one searched epoch: %d -> %d  (%d gained a second)'
      % (len(one_before), len(one_after), len(gained)))
print('  systems with more than one epoch: %d -> %d' % (multi_before, multi_after))
print('  NULL on unseen data: median add-one rank %.3f over %d windows, '
      'KS D = %.3f p = %.3g' % (np.median(rs), n, D, p))
print('  threshold crossings %d (%.2f per cent), rank-first %d (expect %.1f), '
      'stage-1 %d (expect %.2f over %d eligible windows)'
      % (len(cross), 100.0 * len(cross) / len(ROWS), len(rank1), exp_rank1,
         len(stage1), exp_stage1, len(elig)))
print('  POSITIVE CONTROL: %d stage-1 events are beta Pic CO' % len(bp))
for r in bp:
    print('     T*=%.2f ctrl=%.2f  %.4f GHz  %s %+.1f MHz  %s'
          % (r['star_snr'], r['ctrl_max'], r.get('_star_peak_freq') or 0,
             r.get('line'), r.get('line_off') or 0, r['eb']))
print('  unattributed stage-1 events in the extension: %d'
      % (len(stage1) - len(bp)))
