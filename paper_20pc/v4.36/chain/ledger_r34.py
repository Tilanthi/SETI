#!/usr/bin/env python3
r"""ledger_r34.py -- round 3440: the ledger and the checks of Referee 2's items 9, 10, 12, 15, 16 and 17 (v4.34).

Reads only products already in the tree, writes numbers/survey_numbers_round3440.tex, tab_recalrecon_r34.tex and
ledger_r34.json (zdeposit.py deposits catalogues/recalibration_reconciled.csv and
candidates/above_all_controls.csv from it).

  Q1 (item 10) ONE breakdown of the blocks the two recalibration statements count: Sec. 3's "of the N blocks that set
     a quoted limit or hold a crossing" (r29inputs/reflag/reflag_decl_r29.json, core tier; reflagdecl_r29.py) and the
     Data Availability's "of the M blocks that hold a crossing, set a best limit or come close to the threshold"
     (r33inputs/20261107/extract_status_r33.json; xgen_r31.py), together with every block that holds a crossing or a
     system's best limit NOW (ledger.json, sens_r28_systems.csv), which neither frozen record has to contain.
     Rows: holds a crossing / sets a system's best limit / sets another quoted limit / other.  Columns: recalibrated on
     ALMA's flags with every window on the final extractor / recalibrated, some window on an older extractor /
     delivered calibration, final extractor / delivered calibration, older extractor (windows_version.json).
     Asserted: both records' margins are the printed ones (\RflNEbCoreAll, \RflNEbCore, \RflNEbNot, \RflNNotLim,
     \RflNNotCross, \XgNBlkPlan, \XgNBlkReDone, \XgNBlkNotRe) and every re-extracted block is recalibrated on the
     final extractor, every block not re-extracted keeps the delivered calibration.
  Q2 (item 9) count_accounting: every parent row is the sum it names, or is marked "not a sum" (sumrule_r34).
  Q3 (item 12) beta Pic: the stellar-frame velocities of the CO crossings, their number = \BpicPanelNCo, their
     largest |dv| = \BpicDvCoHi; the scatter is the SAMPLE STANDARD DEVIATION (ddof = 1), and the full range.
  Q4 (item 15) the "spatial stage" = the crossings whose stellar statistic exceeds every control position of their
     window (catalogue stage1_flag; n_ctrl_ge_star = 0): its size = \DiscFpOfFlags, its CO members = \DiscFpWin, and
     its one other member is the field leader \EvAStar.
  Q5 (item 15) HD 14055's setups: every census block has the same windows, fine ones holding CO / 13CO J=3-2 and
     coarse continuum ones, and every HD 14055 crossing of the ledger lies in a fine window.
  Q6 (item 16) the sigma of Eq. A1, located in the deposited search code (r30inputs/20261104/pipeline.tar): the
     per-integration, per-channel MAD over the control positions and its inverse-variance combination; each
     pattern must occur exactly once.
  Q7 (item 17) 61 Vir: Table 5's drift row is the observatory-frame fit and its star-frame row the pair test's value
     (pairs_v415.json), and the field leader is the later member of the Table 4 pair.

    python3 ledger_r34.py [--drive N]      N = 1..9: each perturbs one input in memory, prints FAILED and exits 1
                                           without writing a production path
"""
import collections
import csv
import json
import math
import os
import re
import statistics as st
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import star_alias                     # noqa: E402
import sumrule_r34                    # noqa: E402

ROUND = 3440
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
SFX = '' if DRIVE is None else '_drive%d' % DRIVE
J = lambda p: json.load(open(os.path.join(HERE, p)))  # noqa: E731
OUT, FAIL = {}, []
WORD = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve')
word = lambda k: WORD[k] if k < len(WORD) else '%d' % k  # noqa: E731


def m(k, v):
    assert k.isalpha() and k not in OUT, k
    OUT[k] = v


def ck(label, ok, detail=''):
    print('  %-78s %s  %s' % (label[:78], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


def tv(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{(.*)\}\s*$' % name, re.M)
    vals = []
    for f in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if f.startswith('survey_numbers') and f.endswith('.tex') and '_drive' not in f \
                and 'round%d' % ROUND not in f:
            vals += [v for v in pat.findall(open(os.path.join(HERE, 'numbers', f), errors='ignore').read()) if v]
    assert len(set(vals)) == 1, ('macro %s defined %d times: %s' % (name, len(vals), vals[:3]))
    return vals[0]


def and_list(xs):
    xs = list(xs)
    return 'none' if not xs else xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def tname(n):
    return star_alias.designation(re.sub(r'^(?:NAME|V\s*star|V\*|\*\*|\*)\s+', '', n.strip())).replace(' ', '~')


print('ledger_r34: round %d%s' % (ROUND, '' if DRIVE is None else '  (drive %d)' % DRIVE))

# ====================================================================== Q1 the reconciled recalibration breakdown
DEC = J('r29inputs/reflag/reflag_decl_r29.json')['blocks']
DECB = {b['eb']: b for b in DEC}
CORE = [b for b in DEC if b['tier'] == '1-core']
XS = J('r33inputs/20261107/extract_status_r33.json')['blocks']
PLAN = {b['eb']: b for b in XS}
WV = J('r31inputs/20261105/windows_version.json')
WVB = collections.defaultdict(list)
for w in WV:
    WVB[w['eb']].append(w)
LED = J('ledger.json')['rows']
SYS = list(csv.DictReader(open(os.path.join(HERE, 'sens_r28_systems.csv'))))
CROSS = collections.defaultdict(list)
for r in LED:
    CROSS[r['eb']].append(r)
BEST = collections.defaultdict(list)
for r in SYS:
    BEST[r['best_eb']].append(r)
if DRIVE == 1:                       # a recalibrated core block read as keeping the delivered calibration
    _b0 = next(b for b in CORE if b['fate'] == 'recalibrated' and b['eb'] not in PLAN)
    DECB[_b0['eb']] = dict(_b0, fate='infeasible_estimated')
if DRIVE == 2:                       # a block not re-extracted read as on the final extractor
    _e0 = next(e for e, b in PLAN.items() if b['status'] != 're-extracted')
    WVB[_e0] = [dict(w, gen_stat='E3', gen_limit='E3') for w in WVB[_e0]]
CORE_EB = {b['eb'] for b in CORE}
U = sorted(CORE_EB | set(PLAN) | set(CROSS) | set(BEST))


def recal(e):
    return DECB.get(e, {}).get('fate') == 'recalibrated' or PLAN.get(e, {}).get('status') == 're-extracted'


def final(e):
    ws = WVB.get(e, [])
    return bool(ws) and all(w['gen_stat'] == 'E3' and w['gen_limit'] == 'E3' for w in ws)


COLS = [('rf', 'recalibrated on ALMA\\textquoteright s flags, every window on the final extractor'),
        ('ro', 'recalibrated, some window on an older extractor'),
        ('df', 'delivered calibration, final extractor'),
        ('do', 'delivered calibration, older extractor')]
ROWS = [('x', 'holds a crossing'), ('b', 'sets a system\\textquoteright s best limit'),
        ('l', 'sets another quoted limit'), ('o', 'none of these now')]


def col(e):
    return ('r' if recal(e) else 'd') + ('f' if final(e) else 'o')


def role(e):
    if e in CROSS:
        return 'x'
    if e in BEST:
        return 'b'
    if e in CORE_EB and DECB[e]['carries_limit']:
        return 'l'
    return 'o'


GRID = collections.Counter((role(e), col(e)) for e in U)
core_rec = sum(1 for e in CORE_EB if recal(e))
core_not = [e for e in CORE_EB if not recal(e)]
ck('Q1a the 178-block statement: the core record, its recalibrated and not-recalibrated margins and their '
   'limit/crossing split are the printed ones',
   len(CORE_EB) == int(tv('RflNEbCoreAll')) and core_rec == int(tv('RflNEbCore'))
   and len(core_not) == int(tv('RflNEbNot'))
   and sum(1 for e in core_not if DECB[e]['carries_limit']) == int(tv('RflNNotLim'))
   and sum(1 for e in core_not if DECB[e]['carries_crossing']) == int(tv('RflNNotCross')),
   '%d core: %d recalibrated, %d not (%d limit, %d crossing, at the record\'s v4.29 roles)'
   % (len(CORE_EB), core_rec, len(core_not), sum(1 for e in core_not if DECB[e]['carries_limit']),
      sum(1 for e in core_not if DECB[e]['carries_crossing'])))
p_done = [e for e, b in PLAN.items() if b['status'] == 're-extracted']
p_not = [e for e, b in PLAN.items() if b['status'] != 're-extracted']
ck('Q1b the 52-block statement: its re-extracted blocks are recalibrated on the final extractor, the others keep '
   'the delivered calibration and an older extractor, and the margins are the printed ones',
   len(PLAN) == int(tv('XgNBlkPlan')) and len(p_done) == int(tv('XgNBlkReDone'))
   and len(p_not) == int(tv('XgNBlkNotRe'))
   and all(col(e) == 'rf' for e in p_done) and all(col(e) == 'do' for e in p_not),
   '%d planned: %d re-extracted (%s), %d not (%s)'
   % (len(PLAN), len(p_done), dict(collections.Counter(col(e) for e in p_done)), len(p_not),
      dict(collections.Counter(col(e) for e in p_not))))
_nx = len(CROSS)
ck('Q1c every block that holds a crossing or a best limit now is in the breakdown, once',
   set(CROSS) <= set(U) and set(BEST) <= set(U) and sum(GRID.values()) == len(U),
   '%d blocks: %d crossing, %d best-limit; %d outside both records'
   % (len(U), _nx, len(set(BEST) - set(CROSS)), len(set(U) - CORE_EB - set(PLAN))))


def sysname_best(e):
    return [tname(r['designation']) for r in BEST[e]]


NOTRE = []
for e in sorted(p_not):
    nm = sorted({tname(w['star']) for w in WVB.get(e, [])})
    NOTRE.append(dict(eb=e, role=role(e), stars=nm,
                      systems_best=sysname_best(e) if e in BEST else [],
                      crossing_stars=sorted({tname(r['star']) for r in CROSS.get(e, [])}),
                      reason=PLAN[e]['reason_class'], in_core_record=e in CORE_EB))
_nr = collections.Counter(d['role'] for d in NOTRE)
_px = sorted({s for d in NOTRE if d['role'] == 'x' for s in d['crossing_stars']})
_pb = []
for d in NOTRE:
    if d['role'] == 'b':
        for s in d['systems_best']:
            if s not in _pb:
                _pb.append(s)
_bits = []
if _nr['x']:
    _bits.append('%s %s a crossing (toward %s)' % (word(_nr['x']), 'holds' if _nr['x'] == 1 else 'hold',
                                                 and_list(_px)))
if _nr['b']:
    # r34 phase 3: a block can set the best limit of more than one system (one serves PM J03433+1958 and WD 0407+179),
    # so the clause counts the systems as well as the blocks
    _bits.append('%s %s the best %s of %s %s (%s)' % (word(_nr['b']), 'sets' if _nr['b'] == 1 else 'set',
                                    'limit' if len(_pb) == 1 else 'limits', word(len(_pb)),
                                    'system' if len(_pb) == 1 else 'systems', and_list(_pb)))
_rest = len(NOTRE) - _nr['x'] - _nr['b']
_cl = and_list(_bits) if _bits else 'none holds a crossing or a best limit'
if _bits and _rest:
    _cl += ', and the other %s %s neither' % (word(_rest), 'holds' if _rest == 1 else 'hold')
m('LrNotReClause', 'Of these %s, %s' % (word(len(NOTRE)), _cl))
m('LrNotReNCross', '%d' % _nr['x'])
m('LrNotReNBest', '%d' % _nr['b'])
m('LrNotReNNeither', '%d' % _rest)
m('LrRecNBlk', '%d' % len(U))
m('LrRecNOutside', '%d' % len(set(U) - CORE_EB - set(PLAN)))
m('LrRecNCrossBlk', '%d' % _nx)
m('LrRecNBestBlk', '%d' % len(set(BEST) - set(CROSS)))
m('LrRecNCrossNotRec', '%d' % sum(GRID[('x', c)] for c in ('df', 'do')))
m('LrRecNBestNotRec', '%d' % sum(GRID[('b', c)] for c in ('df', 'do')))
m('LrRecNOldExtr', '%d' % sum(v for (r_, c), v in GRID.items() if c[1] == 'o'))

# the table: rows x columns, the row and column totals, then the two records as "of which" rows
_T = ['%% GENERATED by ledger_r34.py (round %d) -- do not hand-edit.' % ROUND,
      '\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{0.34\\linewidth}@{~}rrrr@{~}r@{}}', '\\hline',   # r34: one column; the labels wrap
      ' & \\multicolumn{2}{c}{Recalibrated$^{a}$} & \\multicolumn{2}{c}{Delivered calibration} & \\\\',
      'Block & final & older & final & older & All \\\\',
      ' & \\multicolumn{4}{c}{extractor$^{b}$} & \\\\', '\\hline']


def trow(lab, cnt):
    return '%s & %s \\\\' % (lab, ' & '.join('%d' % cnt.get(c, 0) for c, _ in COLS) + ' & %d' % sum(cnt.values()))


for rk, lab in ROWS:
    _T.append(trow(lab[0].upper() + lab[1:], {c: GRID[(rk, c)] for c, _ in COLS}))
_T.append('\\hline')
_T.append(trow('All', collections.Counter(col(e) for e in U)))
_T.append('\\quad of which counted at the recalibration$^{c}$' + ' & '
          + ' & '.join('%d' % sum(1 for e in CORE_EB if col(e) == c) for c, _ in COLS)
          + ' & %d \\\\' % len(CORE_EB))
_T.append('\\quad of which planned for reprocessing$^{d}$ & '
          + ' & '.join('%d' % sum(1 for e in PLAN if col(e) == c) for c, _ in COLS)
          + ' & %d \\\\' % len(PLAN))
_T += ['\\hline', '\\end{tabular}']
ck('Q1d the table closes: rows and columns sum to the population, and the two record rows to their margins',
   sum(GRID.values()) == len(U) and sum(1 for e in CORE_EB if col(e)[0] == 'r') == core_rec
   and sum(1 for e in PLAN if col(e) == 'rf') == len(p_done),
   '%d blocks in %d cells' % (len(U), len(GRID)))

# ====================================================================== Q2 count_accounting summation rule
_body = [ln for ln in open(os.path.join(HERE, 'si_counts.txt')) if not ln.startswith('#')]
CNT = list(csv.DictReader(_body, delimiter='\t'))
if DRIVE == 3:                       # a parent that no longer equals the rows its note names
    CNT = [dict(r, value=str(int(r['value']) + 1)) if r['row'] == '1' else r for r in CNT]
_ann, _sfail = sumrule_r34.annotate(CNT)
ck('Q2 count_accounting: every parent is the sum of the rows it names (or of a partition of its sub-rows), '
   'or is marked not a sum',
   not _sfail, '%d rows, %d with a rule; %s' % (len(CNT), sum(1 for v in _ann.values() if v[1]),
                                                 '; '.join(_sfail) or 'all close'))

# ====================================================================== Q3 beta Pic, the CO velocities
BP = [r for r in LED if r['star'] in ('bet Pic', 'beta Pic') and r['attributed'] and r['line']
      and re.match(r'^CO\(', r['line'])]
if DRIVE == 4:
    BP = BP[:-1]
DV = [float(r['dv_stellar']) for r in BP]
ck('Q3 beta Pic: the CO crossings are the figure\'s (\\BpicPanelNCo) and their largest offset is \\BpicDvCoHi',
   len(BP) == int(tv('BpicPanelNCo')) and '%.1f' % max(abs(v) for v in DV) == tv('BpicDvCoHi')
   and len({r['eb'] for r in BP}) == len(BP),
   '%d crossings in %d blocks, dv %.3f..%.3f km/s, s.d. %.3f' % (len(BP), len({r['eb'] for r in BP}),
                                                               min(DV), max(DV), st.stdev(DV)))
m('LrBpNVel', '%d' % len(DV))
m('LrBpDvSd', '%.1f' % st.stdev(DV))
m('LrBpDvRange', '%.1f' % (max(DV) - min(DV)))
m('LrBpDvMin', '%+.1f' % min(DV))
m('LrBpDvMax', '%+.1f' % max(DV))
m('LrBpDvMean', '%+.1f' % st.mean(DV))

# ====================================================================== Q4 the "spatial stage"
CAT = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.99.csv'))))
STG = [r for r in CAT if r['stage1_flag'] == 'True']
if DRIVE == 5:
    STG = STG[1:]
_rule = [r for r in CAT if r['crossing'] == 'True' and r['n_ctrl_ge_star'] == '0']
_co = [r for r in STG if 'CO' in r['disposition']]
_oth = [r for r in STG if 'CO' not in r['disposition']]
ck('Q4 the spatial stage is the crossings above every control position of their window: \\DiscFpOfFlags '
   'windows, \\DiscFpWin of them CO, the other the field leader \\EvAStar',
   [id(r) for r in STG] == [id(r) for r in _rule] and len(STG) == int(tv('DiscFpOfFlags'))
   and len(_co) == int(tv('DiscFpWin')) and len(_oth) == 1
   and _oth[0]['star_name'] == tv('EvAStar') and _oth[0]['disposition'] == 'unattributed',
   '%d windows (rule %d), %d CO, other %s' % (len(STG), len(_rule), len(_co),
                                              [(r['star_name'], r['disposition']) for r in _oth]))
m('LrStageN', '%d' % len(STG))
m('LrStageNCo', '%d' % len(_co))
m('LrStageCoStars', and_list(sorted({tname(r['star_name']) for r in _co})))
m('LrStageFile', 'candidates/above\\_all\\_controls.csv')
STAGEROWS = [dict(star=star_alias.designation(r['star_name'], tex=False), eb=r['eb'], band=r['band'],
                  nu_lo_GHz='%.6f' % min(float(r['flo_GHz']), float(r['fhi_GHz'])),
                  nu_hi_GHz='%.6f' % max(float(r['flo_GHz']), float(r['fhi_GHz'])),
                  search_class=r['search_class'], T_star='%.4f' % float(r['star_snr']),
                  T_ctrl_max='%.4f' % float(r['ctrl_max_snr']), n_ctrl=r['n_ctrl'],
                  disposition=r['disposition']) for r in STG]

# ====================================================================== Q5 HD 14055's setups
HD = [r for r in CAT if r['star_name'].replace(' ', '') == 'HD14055']
_hdb = collections.defaultdict(list)
for r in HD:
    _hdb[r['eb']].append(r)
MASKT = J('maskcat_v412.json')['transitions']
_fine = [r for r in HD if r['search_class'] == 'A']
_coarse = [r for r in HD if r['search_class'] == 'B']
_per = collections.Counter((sum(1 for r in v if r['search_class'] == 'A'),
                            sum(1 for r in v if r['search_class'] == 'B')) for v in _hdb.values())


def lines_in(r):
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    return {re.sub(r'\(J=.*', '', k) for k, v in MASKT.items() if lo <= v['f'] <= hi}


_hx = [r for r in LED if r['star'].replace(' ', '') == 'HD14055']
_hw = [w for w in WV if re.sub(r'\s|\*|\[.*\]', '', w['star']) == 'HD14055']
_wins = []
for x in _hx:
    _wins += [w for w in _hw if w['eb'] == x['eb'] and w['flo'] <= float(x['freq']) <= w['fhi']]
if DRIVE == 6:
    _wins = _wins + [dict(_wins[0], cls='B')]
_lines = sorted({re.sub(r'\(J=.*', '', k) for w in _wins for k, v in MASKT.items()
                 if w['flo'] <= v['f'] <= w['fhi'] and re.match(r'^(13)?CO\(', k)})
ck('Q5 HD 14055: every census block carries two fine and two coarse windows, and every crossing (census and '
   'tail) lies in a fine window, which holds a CO or 13CO line',
   len(_per) == 1 and _wins and all(w['cls'] == 'A' for w in _wins) and len(_wins) == len(_hx)
   and all(any(re.match(r'^(13)?CO\(3-2\)', re.sub(r'\(J=.*', '(3-2)', k))
               for k, v in MASKT.items() if w['flo'] <= v['f'] <= w['fhi']) for w in _wins),
   '%d census blocks, per block %s fine/coarse; %d crossings in %d windows of class %s; lines there %s'
   % (len(_hdb), list(_per)[0] if len(_per) == 1 else dict(_per), len(_hx), len(_wins),
      sorted({w['cls'] for w in _wins}), _lines))
_pf, _pc = list(_per)[0] if len(_per) == 1 else (0, 0)
m('LrHdNBlk', '%d' % len(_hdb))
m('LrHdNFine', word(_pf))
m('LrHdNCoarse', word(_pc))
m('LrHdFineChanKHz', '%.0f' % (min(float(r['chanw_Hz']) for r in _fine) / 1e3))
m('LrHdCoarseChanMHz', '%.1f' % (min(float(r['chanw_Hz']) for r in _coarse) / 1e6))
_tex = {'CO(3-2)': 'CO($3$--$2$)', '13CO(3-2)': '$^{13}$CO($3$--$2$)', '13CO': '$^{13}$CO($3$--$2$)'}
m('LrHdFineLines', and_list(sorted({_tex.get(x, x) for x in _lines}, key=lambda t: ('13' in t, t))))
m('LrHdNCross', '%d' % len(_hx))

# ====================================================================== Q6 the sigma of Eq. A1, in the deposited code
_TAR = os.path.join(HERE, 'r30inputs', '20261104', 'pipeline.tar')
with tarfile.open(_TAR) as tf:
    _src = tf.extractfile('search/seti_drift_search_generic.py').read().decode()
_SL = _src.split('\n')
PAT = dict(mad=r'^\s*mad = np\.nanmedian\(np\.abs\(I\[:, probe, :\] - med\[:, None, :\]\), axis=1\)',
           sigma=r'^\s*sigma = \(1\.4826 \* mad\)',
           comb=r'^\s*sig_comb = float\(np\.nanmedian\(1\.0 / np\.sqrt\(np\.nansum\(invvar, axis=0\)\)\)\)',
           smin=r'^\s*S_min_measured = SNR_THRESH \* sig_comb')
if DRIVE == 7:
    PAT['comb'] = r'^\s*sig_comb = np\.std\('
LN = {k: [i + 1 for i, s in enumerate(_SL) if re.search(p, s)] for k, p in PAT.items()}
ck('Q6 the sigma of Eq. A1 is located once each in the deposited search code (MAD over the control positions, '
   'per integration and channel; inverse-variance combination; S_min = 5 sigma)',
   all(len(v) == 1 for v in LN.values()) and LN['mad'][0] < LN['sigma'][0] < LN['comb'][0] < LN['smin'][0],
   ', '.join('%s line %s' % (k, v) for k, v in LN.items()))
m('LrSigFile', 'code/\\allowbreak pipeline/\\allowbreak search/\\allowbreak seti\\_drift\\_search\\_generic.py')   # breakable (latexlog: 18.6 pt overfull)
m('LrSigLineMad', '%d' % LN['mad'][0] if LN['mad'] else '?')
m('LrSigLineSig', '%d' % LN['sigma'][0] if LN['sigma'] else '?')
m('LrSigLineComb', '%d' % LN['comb'][0] if LN['comb'] else '?')
m('LrSigLineSmin', '%d' % LN['smin'][0] if LN['smin'] else '?')

# ====================================================================== Q7 61 Vir: the frames and the field leader
PJ = J('pairs_v415.json')['pairs']
FL = [r for r in STG if r['disposition'] == 'unattributed']
_fl_eb = FL[0]['eb'] if len(FL) == 1 else None
_pp = [p for p in PJ if p['star'] == tv('EvAStar') and _fl_eb in (p['eblo'], p['ebhi'])]
if DRIVE == 8:
    _fl_eb = _pp[0]['eblo'] if _pp else None
_T5 = open(os.path.join(HERE, 'tab_recurcand_v411.tex')).read()
_obs = re.search(r'^Drift rate, observatory frame \(Hz\\,s\$\^\{-1\}\$\) & \$([+-]\d+)\$', _T5, re.M)
_stf = re.search(r"^\\quad in the star\\textquoteright s frame & \$([+-]\d+)\$", _T5, re.M)
_hi = (_pp[0]['ebhi'] == _fl_eb) if _pp else None
_dt, _ds = ((_pp[0]['dhitopo'], _pp[0]['dhi']) if _hi else (_pp[0]['dlotopo'], _pp[0]['dlo'])) if _pp else (None, None)
ck('Q7 61 Vir: the field leader is one member of the Table 4 pair, and Table 5 prints its observatory-frame drift '
   'and its star-frame drift as the pair test computes them',
   len(_pp) == 1 and _obs and _stf and int(_obs.group(1)) == round(_dt) and int(_stf.group(1)) == round(_ds),
   'pair %s; Table 5 %s / %s against %s / %s'
   % ([(p['eblo'], p['ebhi']) for p in _pp], _obs and _obs.group(1), _stf and _stf.group(1),
      _dt if _dt is None else round(_dt), _ds if _ds is None else round(_ds)))
m('LrFlBlock', 'X' + _fl_eb.rsplit('_X', 1)[1] if _fl_eb else '?')
m('LrFlMember', ('second' if _hi else 'first') if _pp else '?')
m('LrFlDriftObs', '%+.0f' % _dt if _dt is not None else '?')
m('LrFlDriftStar', '%+.0f' % _ds if _ds is not None else '?')
m('LrFlFrameTerm', '%+.0f' % (_ds - _dt) if _dt is not None else '?')

# ====================================================================== write
if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
if DRIVE is not None:
    print('ledger_r34: drive %d passed every check -- it did NOT fire' % DRIVE)
    sys.exit(0)
with open(os.path.join(HERE, 'numbers/survey_numbers_round%d.tex' % ROUND), 'w') as fh:
    fh.write('%% GENERATED by ledger_r34.py (round %d) -- do not hand-edit.\n' % ROUND)
    for k in sorted(OUT):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, OUT[k]))
_notes = ('\\par\\smallskip{\\footnotesize\\raggedright $^{a}$With ALMA\\textquoteright s final flags. '
          '$^{b}$The final extractor or an older one made the products of every window of the block. '
          '$^{c}$The blocks that set a quoted limit or held a crossing when the recalibration was planned. '
          '$^{d}$The blocks that held a crossing, set a best limit or came close to the threshold when their '
          'reprocessing with the final extractor was planned. A block appears in a row by what it holds now, crossing first. '
          'The table is \\texttt{catalogues/\\allowbreak recalibration\\_reconciled.csv} in the data archive.\\par}')
open(os.path.join(HERE, 'tab_recalrecon_r34.tex'), 'w').write('\n'.join(_T) + '\n' + _notes + '\n')
json.dump(dict(generated_by='ledger_r34.py', round=ROUND,
               blocks=[dict(eb=e, role=dict(ROWS)[role(e)].replace('\\textquoteright ', "'"), calibration=('recalibrated' if col(e)[0] == 'r'
                                                                         else 'delivered'),
                            extractor=('final' if col(e)[1] == 'f' else 'older'),
                            in_calibration_record=int(e in CORE_EB), in_reextraction_plan=int(e in PLAN),
                            reextracted=('' if e not in PLAN else int(PLAN[e]['status'] == 're-extracted')),
                            stars=';'.join(sorted({star_alias.designation(w['star'], tex=False)
                                                   for w in WVB.get(e, [])})))
                       for e in U],
               not_reextracted=NOTRE, above_all_controls=STAGEROWS,
               sigma_code=dict(file='code/pipeline/search/seti_drift_search_generic.py', lines=LN),
               bpic_dv_kms=sorted(DV)),
          open(os.path.join(HERE, 'ledger_r34.json'), 'w'), indent=1)
print('ledger_r34: %d macros, tab_recalrecon_r34.tex, ledger_r34.json' % len(OUT))
