#!/usr/bin/env python3
r"""holdout_v412.py -- the reserved hold-out searched as a search, the
beyond-40 pc control reported, and the question of whether the external
calibration sample overlaps the primary census answered.

Round 191.  Writes `survey_numbers_round191.tex` and `tab_holdout_v412.tex`.

WHY THIS EXISTS.  Three sets of execution blocks in this paper were searched
with the frozen pipeline and then reported only as instrument calibration.
They hold data on sample stars, and a transmitter in them would matter
whatever role they were reserved for.

  * **The hold-out.**  77 blocks held back by a rule fixed before the search
    finished.  The paper reported one clause about it -- the number of
    crossings whose star outranks its controls -- and nothing about what the
    crossings themselves were.  There are eight, and this generator gives
    each one's attribution in its own star's rest frame and its recurrence
    disposition, measured on the same code path and with the same statistic
    as the primary census.
  * **The beyond-40 pc control.**  47 blocks toward stars outside the
    sample, listed in the block ledger as "the external null" with no result
    anywhere in the paper.  There are eight crossings there too.
  * **The external calibration sample.**  326 blocks used to calibrate the
    spatial rank, and described as a second out-of-sample set.

★★★ IT IS NOT OUT OF SAMPLE.  Every one of its 326 blocks is either a
primary-census block (263) or a reserved hold-out block (63); not one lies
outside both.  The claim that the positive control recovered beta Pictoris
carbon monoxide "on data it had never seen" is therefore false, and so is
the block ledger's footnote that the set reaches stars outside the work
list.  Five of beta Pictoris' eleven census blocks are in it.  The
arithmetic closes exactly: the harvest holds 1326 windows in 327 blocks, of
which one block and its four windows are excluded, leaving the published
1322/326.  This is asserted, with the one excluded block named.

WHAT THE HOLD-OUT MEASUREMENT IS.  `r11inputs/events/holdout_cross_r11.py`
(deposited) identifies each exported hold-out window in the retained-product
index on (block, channel width, lower window edge) and accepts the match
only if the product's own published peak reproduces the exported statistic;
all sixteen crossings of the two sets resolved, none guessed.  The crossing
frequency is then the product's own peak frequency, not an inversion of the
released velocity offset -- which recovers a frequency outside its own
window for four of the sixteen.  `r10_recur_all.py`, the generator that
produced the published census exclusions, then ran unchanged on the result,
with two systemic velocities added from a dated SIMBAD query because the
paper's own resolver covers only stars with a census crossing; five of the
seven stars are in both and the two agree to the printed digit.

Usage: holdout_v412.py [--drive N]
"""
import csv
import json
import math
import os
import re
import sys

import maskframe_v411 as mf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round191.tex')
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
EV = os.path.join(HERE, 'r11inputs', 'events')
TRIG = 5.0


def out(name):
    b, e = os.path.splitext(name)
    return os.path.join(HERE, b + SFX + e)


M, fail = [], []


def m(k, v):
    M.append((k, v))


def ck(name, cond, detail=''):
    if not cond:
        fail.append(name)
    print('  %-56s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def tname(s):
    """The star as the paper sets it.  The exported spellings run words
    together and carry a Gaia designation; neither belongs in a table."""
    s = re.split(r'\s+Gaia\b', s)[0].strip()
    s = re.sub(r'^HD(\d)', r'HD \1', s)
    return s.replace(' ', '~').replace('-', '$-$') if '$' not in s \
        else s.replace(' ', '~')


# ------------------------------------------------------------------ inputs
HOLD = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
OOS = json.load(open(os.path.join(HERE, 'outofsample_v381.json')))['rows']
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
CCAL = json.load(open(os.path.join(HERE, 'ctrl_calib_v372.json')))
CAMP = json.load(open(os.path.join(HERE, 'campaign_v372.json')))
XH = json.load(open(os.path.join(EV, 'cross_holdout.json')))
XO = json.load(open(os.path.join(EV, 'cross_oos.json')))
REC = json.load(open(os.path.join(EV, 'recur_holdout.json')))['crossings']
VSYS = json.load(open(os.path.join(EV, 'vsys_holdout_v412.json')))
EXTRA = json.load(open(os.path.join(EV, 'vcorr_extra_v412.json')))

# ===================================================== (1) the two set sizes
for tag, R in (('Ho', HOLD), ('Oos', OOS)):
    m(tag + 'NBlock', '%d' % len({r['eb'] for r in R}))
    m(tag + 'NWin', '%d' % len(R))
    m(tag + 'NStar', '%d' % len({r['star_name'] for r in R}))
    m(tag + 'Hours', '%.0f' % (sum(r['onsrc'] for r in R) / 3600.0))
    m(tag + 'NFine', '%d' % sum(1 for r in R if r['res'].startswith('fine')))

# ================================= (2) the hold-out crossings, fully disposed
C = 299792.458
ROWS = []
for c in XH:
    rec = REC.get(c['cid'], {})
    d = rec.get('discovery') or {}
    vc = d.get('v_corr_kms')
    if vc is None:
        vc = EXTRA[c['cid']]['v_corr_kms']
    vs = VSYS[c['star']]
    _fb, fstar = mf.to_stellar(c['freq_GHz'], vc, vs)
    line, _frest, dv = mf.nearest(fstar)
    bl = [b for b in rec.get('blocks', [])
          if not b.get('bad_weight_product')]
    r = dict(c, f_star=fstar, line_star=line, dv_star=dv,
             attributed=abs(dv) <= mf.MASK_HALF_KMS,
             v_sys=vs, v_corr=vc, n_rep=len(bl))
    if bl:
        S = d['amp_mJy']
        w = [1.0 / b['sig_mJy'] ** 2 for b in bl]
        sb = 1.0 / math.sqrt(sum(w))
        ab = sum(b['amp_mJy'] * q for b, q in zip(bl, w)) / sum(w)
        # ★★ ONE DEFINITION FOR THE CENSUS AND FOR THE HOLD-OUT.  `T_rep` is
        # the inverse-variance combination of the repeat readings -- the
        # number T_pers is compared against -- and not the largest of them:
        # the mean of a maximum over n blocks is not zero, which is why a
        # column of maxima read as a systematic positive offset.  The
        # exclusion carries the discovery amplitude's own noise, so it cannot
        # exceed the strength of the discovery it is built from, and `f5` is
        # the fraction of that amplitude still ruled out at the trigger.
        sd = d['sig_mJy']
        r.update(T_pers=S / sb, T_rep=ab / sb,
                 excl=(S - ab) / math.sqrt(sd * sd + sb * sb),
                 excl_conditional=(S - ab) / sb,
                 f5=(ab / sb + TRIG) / (S / sb),
                 T_matched=max(b['T_matched'] for b in bl),
                 T_anydrift=max(b['T_bestdrift_pub'] for b in bl),
                 dt_min=min(abs(b['sep_from_discovery_h']) for b in bl) / 24.0,
                 dt_max=max(abs(b['sep_from_discovery_h']) for b in bl) / 24.0)
    ROWS.append(r)

ROWS.sort(key=lambda z: -z['tstar'])
HATT = [r for r in ROWS if r['attributed']]
HUN = [r for r in ROWS if not r['attributed']]
HTEST = [r for r in ROWS if r['n_rep']]
# ★ "recurs" is the same predicate the census uses: the drift-maximised
# statistic at the predicted stellar-frame cell reaches the trigger.
HREC = [r for r in HTEST if r['T_anydrift'] >= TRIG]
m('HoNCross', '%d' % len(ROWS))
m('HoNAttr', '%d' % len(HATT))
m('HoNUnattr', '%d' % len(HUN))
m('HoNScreen', '%d' % sum(1 for r in ROWS if r['screen']))
m('HoNCtrlMin', '%d' % min(r['n_ge_star'] for r in ROWS))
m('HoNTested', '%d' % len(HTEST))
m('HoNNoRep', '%d' % sum(1 for r in ROWS if not r['n_rep']))
m('HoNRecur', '%d' % len(HREC))
m('HoTMax', '%.2f' % max(r['tstar'] for r in ROWS))
_nr = [r for r in HTEST if r not in HREC]
m('HoExclMin', '%.1f' % min(r['excl'] for r in _nr))
m('HoExclMax', '%.1f' % max(r['excl'] for r in _nr))
m('HoFracMed', '%.2f' % sorted(r['f5'] for r in _nr)[len(_nr) // 2])
m('HoFracMax', '%.2f' % max(r['f5'] for r in _nr))
if HREC:
    q = HREC[0]
    m('HoRecStar', tname(q['star']))
    m('HoRecT', '%.2f' % q['tstar'])
    m('HoRecLine', mf.tex_label(q['line_star']))
    m('HoRecDv', '%+.0f' % q['dv_star'])
    # ★★★ THERE ARE THREE READINGS OF THIS ONE CELL, AND THE MACRO NAMES MUST
    # SAY WHICH IS WHICH.  `HoRecTRep` carried the DRIFT-MAXIMISED value under
    # a name the hold-out table uses for a different column; the prose then
    # said the matched-drift value "is the value Table 5 prints", and the
    # table prints neither of them -- it prints the inverse-variance
    # combination.  Named apart:
    #   T_rep       the combination over the repeat blocks at the matched
    #               drift.  This IS the table's column and the quantity the
    #               exclusion is formed from.
    #   T_matched   the largest single block at the matched drift.
    #   T_anydrift  the largest over every drift trial -- a maximum over
    #               about 120 of them, so positive on average whatever is
    #               there, and the predicate the recurrence test uses.
    m('HoRecTRep', '%+.2f' % q['T_rep'])
    m('HoRecTMatchedMax', '%+.2f' % q['T_matched'])
    m('HoRecTAnyDrift', '%.2f' % q['T_anydrift'])
    m('HoRecNRep', '%d' % q['n_rep'])
if HUN:
    m('HoUnTMax', '%.2f' % max(r['tstar'] for r in HUN))

# ================================= (3) the beyond-40 pc control, in the sky
# frame: these are background sources and the paper's resolver holds no
# systemic velocity for any of them, which is itself the reason the set can
# only ever be a null and never a limit.  Said, not hidden.
OATT = [c for c in XO if abs(c['dv_sky']) <= mf.MASK_HALF_KMS]
m('OosNCross', '%d' % len(XO))
m('OosNAttrSky', '%d' % len(OATT))
m('OosNScreen', '%d' % sum(1 for c in XO if c['screen']))
m('OosNCtrlMin', '%d' % min(c['n_ge_star'] for c in XO))
m('OosTMax', '%.1f' % max(c['tstar'] for c in XO))
m('OosNVsys', '%d' % sum(1 for c in XO if mf.vsys(c['star'])[0] is not None))

# ============================ (4) does the calibration sample overlap?  Yes.
def _eb(k):
    mm = re.match(r'(A002_X[0-9a-f]+_X[0-9a-f]+)_spw', k)
    return mm.group(1) if mm else None


CAL_WIN = sorted(CCAL)
CAL_EB_ALL = {_eb(k) for k in CAL_WIN}
CENS_EB = {r['eb'] for r in CAT}
HOLD_EB = {r['eb'] for r in HOLD}
OOS_EB = {r['eb'] for r in OOS}
_outside = sorted(CAL_EB_ALL - CENS_EB - HOLD_EB - OOS_EB)
# the published sample is the harvest minus the blocks outside both sets:
# 327 - 1 == 326 and 1326 - 4 == 1322, which is how the exclusion is
# identified rather than assumed.
CAL_EB = CAL_EB_ALL - set(_outside)
m('CalNBlockHarvest', '%d' % len(CAL_EB_ALL))
m('CalNWinHarvest', '%d' % len(CAL_WIN))
m('CalNBlock', '%d' % len(CAL_EB))
m('CalNCensus', '%d' % len(CAL_EB & CENS_EB))
m('CalNHoldout', '%d' % len(CAL_EB & HOLD_EB))
m('CalNOutside', '%d' % len(CAL_EB - CENS_EB - HOLD_EB))
m('CalPctCensus', '%.0f' % (100.0 * len(CAL_EB & CENS_EB) / len(CAL_EB)))
_bp = {r['eb'] for r in CAT if r['star_name'] == 'bet Pic'}
m('CalNBpicCensus', '%d' % len(_bp))
m('CalNBpicShared', '%d' % len(_bp & CAL_EB))
m('HoNCensusShared', '%d' % len(HOLD_EB & CENS_EB))

# ------------------------------------------------------------- assertions
print('\nassertions')
v = len(CAL_EB - CENS_EB - HOLD_EB) if DRIVE != 1 else 1
ck('H1 every block of the external calibration sample is a primary-census '
   'or a hold-out block', v == 0,
   '%d of %d outside both (%d census + %d hold-out)'
   % (v, len(CAL_EB), len(CAL_EB & CENS_EB), len(CAL_EB & HOLD_EB)))
# ★ and the identification of the excluded block is not assumed: the two
# published counts must come back exactly.
v = (len(CAL_EB_ALL) - len(_outside) == CAMP['n_blocks']
     and len(CAL_WIN) - sum(1 for k in CAL_WIN if _eb(k) in set(_outside))
     == CAMP['n_windows']) if DRIVE != 2 else False
ck('H2 the harvest minus the blocks outside both sets reproduces the '
   'published sample exactly', v,
   '%d-%d==%d blocks, %d-%d==%d windows, excluded %s'
   % (len(CAL_EB_ALL), len(_outside), CAMP['n_blocks'], len(CAL_WIN),
      sum(1 for k in CAL_WIN if _eb(k) in set(_outside)),
      CAMP['n_windows'], _outside))
v = len(_bp & CAL_EB) if DRIVE != 3 else 0
ck('H3 the positive control was calibrated on census blocks, so "data it '
   'had never seen" cannot be said of it', v > 0,
   '%d of beta Pic\'s %d census blocks are in the calibration sample'
   % (v, len(_bp)))
# ★ the hold-out, by contrast, IS disjoint from the census, which is what
# makes the rank displacement an out-of-sample measurement.
v = len(HOLD_EB & CENS_EB) if DRIVE != 4 else 1
ck('H4 the reserved hold-out shares no execution block with the primary '
   'census', v == 0, '%d shared' % v)
v = min(r['n_ge_star'] for r in ROWS) if DRIVE != 5 else 0
ck('H5 no hold-out crossing outranks its own control positions', v > 0,
   'fewest controls above the star %d of %d' % (v, ROWS[0]['n_ctrl']))
# ★ THIS ONE IS THE POINT OF THE SUBSECTION, AND IT CAN FAIL EITHER WAY.
# The hold-out's one recurring crossing must be a line-attributed one: a
# recurring crossing that no transition explains is a detection, and the
# paper would have to say so.
_badrec = [r for r in HREC if not r['attributed']]
if DRIVE == 6:
    _badrec = [HUN[0]]
ck('H6 every hold-out crossing that recurs is one the mask attributes',
   not _badrec, 'recurring: %s; unattributed among them: %s'
   % ([(r['star'], round(r['T_anydrift'], 2)) for r in HREC],
      [r['star'] for r in _badrec]))
v = max(abs(d['gate_rel']) for d in
        [REC[k]['discovery'] for k in REC
         if REC[k].get('discovery', {}).get('gate_rel') is not None])
if DRIVE == 7:
    v = 1.0
ck('H7 every measured hold-out window reproduces its published statistic',
   v < 1e-6, 'worst relative error %.1e' % v)
# ★ the two systemic velocities that had to be fetched must not disagree
# with the paper's own resolver where both hold a value
_cmp = [(k, VSYS[k], mf.vsys(k)[0]) for k in VSYS
        if mf.vsys(k)[0] is not None]
v = max(abs(a - b) for _k, a, b in _cmp) if DRIVE != 8 else 9.0
ck('H8 the fetched systemic velocities agree with the resolver where both '
   'have one', v < 1e-3,
   '%d of %d stars in both, worst difference %.4f km/s'
   % (len(_cmp), len(VSYS), v))

# ----------------------------------------------------------------- table
T = ['%% GENERATED by holdout_v412.py -- do not hand-edit.',
     r'\begin{tabular}{@{}l@{~}l@{~}r@{~}r@{~}l@{~}r@{~~}r@{~}r@{~}r@{~}l@{}}',
     r'\hline',
     r'Star & block & $\nu_{\rm topo}$ (GHz) & $T_\star$ & line & '
     r'$\Delta v_\star$ & $n_{\rm rep}$ & $T_{\rm pers}$ & $T_{\rm rep}$ & '
     r'disposition \\', r'\hline']
for r in ROWS:
    if r['n_rep']:
        tp, tr = '%.1f' % r['T_pers'], '%+.2f' % r['T_rep']
        dis = ('present again' if r['T_anydrift'] >= TRIG
               else 'does not recur')
    else:
        tp = tr = '---'
        dis = 'no repeat coverage'
    T.append(r'%s & %s & %.4f & %.3f & %s & %+.1f & %s & %s & %s & '
             r'%s; %s \\'
             % (tname(r['star']),
                r['eb'].replace('A002_', '').replace('_', r'\_'),
                r['freq_GHz'], r['tstar'], mf.tex_label(r['line_star']),
                r['dv_star'], r['n_rep'] or '---', tp, tr,
                'attributed' if r['attributed'] else 'unattributed', dis))
T += [r'\hline', r'\end{tabular}']
open(out('tab_holdout_v412.tex'), 'w').write('\n'.join(T) + '\n')

# ★★ THE PROSE SAYS "WHICH IS THE VALUE TABLE 5 PRINTS", SO THAT MUST BE
# CHECKED AGAINST THE TABLE AND NOT AGAINST A VARIABLE.  The macro and the
# cell are compared as the strings they are typeset as; a reformatting of
# either one fails this.  Driven at 9.
if HREC:
    _mm = dict(M)
    _cell = '%+.2f' % HREC[0]['T_rep']
    _row = [t for t in T if t.startswith(tname(HREC[0]['star']) + ' &')
            and ('%.4f' % HREC[0]['freq_GHz']) in t]
    _mac = _mm['HoRecTRep'] if DRIVE != 9 else '%.2f' % HREC[0]['T_anydrift']
    ck('H9 the recurrence value the section attributes to the hold-out table '
       'is the one the table prints',
       len(_row) == 1 and _cell in _row[0] and _mac == _cell,
       'macro %s, table cell %s' % (_mac, _cell))

with open(out(os.path.basename(OUT)), 'w') as fh:
    fh.write('%% GENERATED by holdout_v412.py -- do not hand-edit.\n')
    for k, v in M:
        assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
print('hold-out: %d blocks / %d windows / %d crossings -- %d attributed, '
      '%d unattributed; %d tested for recurrence, %d present again, %d with '
      'no repeat coverage'
      % (len({r['eb'] for r in HOLD}), len(HOLD), len(ROWS), len(HATT),
         len(HUN), len(HTEST), len(HREC),
         sum(1 for r in ROWS if not r['n_rep'])))
print('beyond 40 pc: %d blocks / %d windows / %d crossings -- %d within '
      '%g km/s of a masked transition in the sky frame, %d outranking their '
      'controls, %d with a systemic velocity'
      % (len({r['eb'] for r in OOS}), len(OOS), len(XO), len(OATT),
         mf.MASK_HALF_KMS, sum(1 for c in XO if c['screen']),
         sum(1 for c in XO if mf.vsys(c['star'])[0] is not None)))
print('external calibration sample: %d blocks = %d primary census + %d '
      'hold-out + %d outside'
      % (len(CAL_EB), len(CAL_EB & CENS_EB), len(CAL_EB & HOLD_EB),
         len(CAL_EB - CENS_EB - HOLD_EB)))
if fail and DRIVE == 0:
    raise SystemExit('assertions failed: %s' % fail)
