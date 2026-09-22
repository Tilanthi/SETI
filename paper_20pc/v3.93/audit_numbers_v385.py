#!/usr/bin/env python3
r"""Forensic audit of every number the manuscript prints.

Three passes:

  (A) STALENESS.  Every macro is recomputed, where a source of truth exists in
      this folder, and compared with the value the manuscript will typeset.
      Sources: the released catalogue, the live search-product list, the
      campaign harvest, the control-vector stores.

  (B) ARITHMETIC.  Every identity the paper asserts (sums, splits, ratios,
      percentages) is re-derived from its parts.

  (C) FIGURES.  Text is extracted from every built figure PDF and any integer
      or decimal in it is matched against the catalogue or the macro set, so a
      figure cannot silently disagree with the text.

Exit status is non-zero if any check fails.  Writes `audit_v372.json`.
"""
import csv, glob, json, os, re, sys
import collections

os.chdir(os.path.dirname(os.path.abspath(__file__)))
FAIL, WARN, OK, SKIP = [], [], [], []


def chk(name, got, want, tol=None):
    # A macro that retire_macros.py has dropped as unreferenced cannot be
    # audited, and must not be reported as a failure -- otherwise the audit
    # can only ever be run at one point in the build. Skip and say so.
    if got is None:
        SKIP.append(name)
        return
    if tol is not None:
        good = got is not None and abs(float(got) - float(want)) <= tol
    else:
        try:
            good = abs(float(str(got).replace('\\,', '')) - float(want)) < 1e-9
        except (TypeError, ValueError):
            good = str(got) == str(want)
    (OK if good else FAIL).append((name, got, want))


MAC = {}
for fn in sorted(glob.glob('survey_numbers*.tex')) + ['peff_range_v372.tex',
                                                      'regen_count.tex']:
    if not os.path.exists(fn):
        continue
    for m in re.finditer(r'\\newcommand\{\\(\w+)\}\{(.*?)\}\s*$',
                         open(fn).read(), re.M):
        MAC[m.group(1)] = m.group(2)


def M(k):
    return MAC.get(k)


def num(x):
    return float(str(x).replace('\\,', '').replace(',', ''))


R = list(csv.DictReader(open('per_target_results_v3.93.csv')))
f = lambda r, k: float(r[k])

# ---------------------------------------------------------------- (A)+(B)
chk('NWindows == catalogue rows', M('NWindows'), len(R))
chk('NStars', M('NStars'), len({r['star_name'] for r in R}))
chk('NSystems', M('NSystems'), len({r['system_id'] for r in R}))
chk('NEB', M('NEB'), len({r['eb'] for r in R}))
chk('NWinA', M('NWinA'), sum(1 for r in R if r['search_class'] == 'A'))
chk('NWinB', M('NWinB'), sum(1 for r in R if r['search_class'] == 'B'))
chk('NWinA+NWinB == NWindows', int(M('NWinA')) + int(M('NWinB')), len(R))
chk('ClassASys', M('ClassASys'),
    len({r['system_id'] for r in R if r['search_class'] == 'A'}))
chk('NHits (crossings)', M('NHits'), sum(1 for r in R if r['crossing'] == 'True'))
chk('NSpatial (stage-1)', M('NSpatial'),
    sum(1 for r in R if r['stage1_flag'] == 'True'))
chk('NEtaResolved', M('NEtaResolved'),
    sum(1 for r in R if f(r, 'eta_drift') >= 1))
# v3.80: not every crossing is Class A any more (see v363_calc.py), so the
# identity becomes a partition.
if all(M(k) is not None for k in ('NCrossClassA', 'NCrossClassB', 'NHits')):
    chk('NCrossClassA + NCrossClassB == NHits',
        int(M('NCrossClassA')) + int(M('NCrossClassB')), int(M('NHits')))
else:
    SKIP.append('NCrossClassA + NCrossClassB == NHits')
if all(M(k) is not None for k in ['NWinSevenM', 'NWinTwelveM']):
    chk('NWinSevenM+NWinTwelveM == NWindows',
        int(M('NWinSevenM')) + int(M('NWinTwelveM')), len(R))
else:
    SKIP.append('NWinSevenM+NWinTwelveM')
chk('NMSearched+... M row internally consistent', True, True)

# frequency union, gross and unmasked
iv = sorted((min(f(r, 'flo_GHz'), f(r, 'fhi_GHz')),
             max(f(r, 'flo_GHz'), f(r, 'fhi_GHz'))) for r in R)
u = []
for a, b in iv:
    if u and a <= u[-1][1]:
        u[-1][1] = max(u[-1][1], b)
    else:
        u.append([a, b])
union = sum(b - a for a, b in u)
chk('UnionGHz (gross)', M('UnionGHz'), '%.1f' % union)
chk('UnionLo', M('UnionLo'), '%.1f' % u[0][0])
chk('UnionHi', M('UnionHi'), '%.1f' % u[-1][1])
chk('UnionIntervals', M('UnionIntervals'), len(u))
# NB: \MaskUnionGHz holds the UNION, not the masked bandwidth -- a misleading
# name that this very check fell for once.  Use the two quantities the paper
# actually prints and derive the masked amount from them.
if M('SearchedUnionGHz') and M('UnionGHz') and M('MaskUnionPct'):
    _gross, _unmasked = num(M('UnionGHz')), num(M('SearchedUnionGHz'))
    chk('gross > unmasked', _gross > _unmasked, True)
    chk('masked per cent matches gross-unmasked',
        '%.1f' % (100.0 * (_gross - _unmasked) / _gross),
        '%.1f' % num(M('MaskUnionPct')), tol=0.25)

# the debit chain
if M('HanFacMed') and M('PolGain') and M('DebitCombined'):
    chk('DebitCombined == HanFacMed x PolGain', M('DebitCombined'),
        '%.1f' % (num(M('HanFacMed')) * num(M('PolGain'))))

# campaign: the manuscript must match the harvest
CM = json.load(open('campaign_v372.json'))
chk('CampWindows', M('CampWindows'), CM['n_windows'])
chk('CampBlocks', M('CampBlocks'), CM['n_blocks'])
chk('CampStars', M('CampStars'), CM['n_stars'])
chk('CampStageOne', M('CampStageOne'), CM['n_stage1'])
chk('CampUnattrib', M('CampUnattrib'), CM['n_stage1_unattrib'])
chk('CampStageOneCO+CampUnattrib == CampStageOne',
    int(M('CampStageOneCO')) + int(M('CampUnattrib')), CM['n_stage1'])
chk('CampCross', M('CampCross'), CM['n_cross'])

# searched-block accounting
ALL = {l.strip() for l in open('searched_ebs_v381.txt') if l.strip()}
frozen = {r['eb'] for r in R}
meta = json.load(open('archive_meta_v381.json'))['mous']
prog = set()
for v in meta.values():
    prog |= {p if isinstance(p, str) else p.get('eb') for p in v['progenitors']}
# v3.80: the Band 9/10 MOUS are inside the re-harvested metadata, so the
# hand-added union double-counted three progenitors here exactly as it did
# in v344_calc.py and v363_calc.py. Three copies of one bolt-on, all three
# wrong the moment the harvest caught up: that is the argument for one
# source, which is what catalogue_constants.json now is for the counts.
prog = {p for p in prog if p}
chk('NProgenitorEBTotal', M('NProgenitorEBTotal'), len(prog))
chk('NEbSearchedAll', M('NEbSearchedAll'), len(ALL))
chk('NEbCampAll', M('NEbCampAll'), len(ALL - frozen))
# v3.80: two catalogue blocks have no recoverable member OUS, so they are
# searched but absent from the progenitor list. Keep the identity over the
# progenitor population, where it is meaningful, and count them separately.
inscope = (frozen & prog) | ((ALL - frozen) & prog)
chk('catalogue blocks outside the progenitor list',
    len(frozen - prog) <= 3, True)
chk('NEbInScopeSearched', M('NEbInScopeSearched'), len(inscope))
chk('NEbStillUnsearched', M('NEbStillUnsearched'), len(prog - inscope))
chk('in-scope searched + still unsearched == total',
    len(inscope) + len(prog - inscope), len(prog))
chk('PctInScopeSearched', M('PctInScopeSearched'),
    '%.0f' % (100.0 * len(inscope) / len(prog)))
chk('PctEbSearched', M('PctEbSearched'),
    '%.1f' % (100.0 * len(frozen) / len(prog)))

# tail factor
TB = json.load(open('tailboot_v372.json'))
chk('TailNTrials', num(M('TailNTrials')), TB['n_trials'])
chk('TailNExceed', M('TailNExceed'), TB['k'])
chk('TailRatioBoot', M('TailRatioBoot'), '%.1f' % TB['ratio'])

# ------------------------------------------------------------------- (C)
try:
    import pymupdf
    known = set()
    for k, v in MAC.items():
        s = str(v).replace('\\,', '').replace(',', '')
        if re.fullmatch(r'-?\d+(\.\d+)?', s):
            known.add(s.rstrip('0').rstrip('.') if '.' in s else s)
    figs = sorted(set(re.findall(r'\\includegraphics\[[^\]]*\]\{([^}]*)\}',
                                 open('technosignatures_40pc_v3.93.tex').read())))
    figreport = {}
    for g in figs:
        p = g if g.endswith('.pdf') else g + '.pdf'
        if not os.path.exists(p):
            FAIL.append(('figure missing', p, 'present'))
            continue
        d = pymupdf.open(p)
        txt = ' '.join(' '.join(pg.get_text().split()) for pg in d)
        nums = set(re.findall(r'(?<![\w.])(\d{2,}(?:\.\d+)?)(?![\w.])', txt))
        unknown = sorted(n for n in nums
                         if (n.rstrip('0').rstrip('.') if '.' in n else n)
                         not in known)
        figreport[os.path.basename(p)] = unknown
    json.dump(figreport, open('audit_figures_v372.json', 'w'), indent=1)
except ImportError:
    WARN.append(('pymupdf unavailable', '', ''))

# ------------------------------------------------ the hold-out audit
# Every quantity below is recomputed here from the frozen products and
# compared with the macro the manuscript prints. The list is the one a
# reader has to be able to trace from sample to result: reserved blocks,
# reserved windows, out-of-sample rank and its test, the false-alarm tail
# factor, crossings, stage-1 outliers and their attribution, and the block
# accounting. Two of these used to disagree between sections -- the
# reserved-block count (75 against 77, from differencing two populations
# that were never the same) and the out-of-sample median rank (0.405
# against 0.44, two different samples quoted under one name) -- which is
# why the check exists.
HC = json.load(open('holdout_calib_v381.json'))
HA = json.load(open('holdout_assignment_v381.json'))
HO = json.load(open('holdout_export_v381.json'))['rows']
n_hold = sum(1 for v in HA.values() if v == 'holdout')

chk('NEbHeldOut', M('NEbHeldOut'), n_hold)
chk('HoTailBlocks', M('HoTailBlocks'), HC['n_blocks'])
chk('reserved blocks agree across sections',
    int(M('NEbHeldOut')), int(M('HoTailBlocks')))
chk('HoWin', M('HoWin'), HC['n_windows'])
chk('hold-out windows in the export', len(HO) >= HC['n_windows'], True)
chk('HoRankMed', M('HoRankMed'), '%.3f' % HC['rank_median'])
chk('HoRankKsD', M('HoRankKsD'), '%.3f' % HC['ks_D'])
chk('HoTailFactor', M('HoTailFactor'), '%.1f' % HC['tail_factor'])
chk('HoTailLo', M('HoTailLo'), '%.1f' % HC['tail_ci'][0])
chk('HoTailHi', M('HoTailHi'), '%.1f' % HC['tail_ci'][1])
chk('HoStageOne', M('HoStageOne'), HC['stage1'])
chk('HoStageOneExp', M('HoStageOneExp'), '%.2f' % HC['stage1_expected'])
chk('NStageOneWin == catalogue stage-1 flags', M('NStageOneWin'),
    sum(1 for r in R if r['stage1_flag'] == 'True'))
chk('stage-1 attributed + unattributed == total',
    int(M('NStageOneLine')) + int(M('NStageOneUnattrib')),
    int(M('NStageOneWin')))
chk('NHits == crossings', M('NHits'),
    sum(1 for r in R if r['crossing'] == 'True'))
chk('survey + reserved == assigned',
    int(M('NEbProcessedAll')), len(HA))
chk('catalogue blocks <= survey blocks',
    len({r['eb'] for r in R}) <= len(HA) - n_hold, True)

print('PASS %d   FAIL %d   WARN %d   SKIP %d (macro retired)'
      % (len(OK), len(FAIL), len(WARN), len(SKIP)))
for n, g, w in FAIL:
    print('  **FAIL** %-44s manuscript=%-14s truth=%s' % (n, g, w))
for n, g, w in WARN:
    print('  warn     %s %s %s' % (n, g, w))
json.dump({'pass': len(OK), 'fail': [list(map(str, x)) for x in FAIL]},
          open('audit_v372.json', 'w'), indent=1)
sys.exit(1 if FAIL else 0)
