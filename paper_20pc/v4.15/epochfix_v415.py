#!/usr/bin/env python3
r"""epochfix_v415.py -- the block epochs, measured; and the four ledger rows
that dispose of crossings on a quantity belonging to a different set.

Round 421.  Writes `survey_numbers_round421.tex` and `epochfix_v415.json`.

★★★★ WHY THIS EXISTS.  Every statement in this paper about *when* two blocks
were taken reads one file, `epochs_v386.json`, and that file is wrong for most
of the survey.  The archive does not index every execution block by its own
identifier, so the blocks it does not carry were resolved through their member
observing unit set -- and the value returned is the EARLIEST block in that
unit, not this one.  Two blocks of one scheduling block therefore receive the
same timestamp and are separated by exactly zero.

The defect is measured here, not asserted: of the blocks for which a
measurement set survives and can be read directly, most disagree with the
stored stamp, by up to most of a year.  Three consequences follow, and all
three are published numbers.

 1. The ledger's repeat interval for three crossings is printed as 0.0 d.
    Two different blocks cannot be simultaneous, and the barycentric term
    these three carry differs by 12 km/s, which a day cannot produce.
 2. The epoch-separation split -- how many systems have a second block more
    than a day from the first -- classifies a system "all within one day"
    whenever its blocks share a stamp.  Seven of the ten systems so
    classified are demonstrably not.
 3. The confirmable bandwidth is built from the same comparison and is
    therefore understated.

TWO INDEPENDENT WITNESSES, AND NEITHER IS THE STORED STAMP.

  * the measurement sets.  The recurrence and hold-out campaigns read each
    block's own start time out of the data, and those are used wherever they
    exist.
  * ★★★ THE BARYCENTRIC TERM.  Each block carries its own observatory-to-
    barycentre projection, which moves through 60 km/s over a year and by at
    most a fraction of a km/s within a day.  Two blocks whose terms differ by
    more than that cannot have been taken within a day of each other -- a
    one-sided test that can prove separation and never proves simultaneity.
    The threshold is CALIBRATED, not chosen: over every pair of blocks for
    which both measurement sets survive, the largest difference seen among
    pairs genuinely within one day is reported, and the threshold is set well
    above it.  The test then fires on hundreds of those pairs and gives not
    one false separation.

Usage: epochfix_v415.py [--drive N]
"""
import collections
import csv
import glob
import itertools
import json
import math
import os
import re
import sys

import epochs_r14 as _ep   # the ONE determination of a block's epoch

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 421
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round421%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'epochfix_v415%s.json' % SFX)

SEP = 1.0                      # the paper's own definition of an independent
                               # epoch, in days
BARY_TOL = 1.5                 # km/s; calibrated below, never chosen
CKMS = 299792.458
TRIG = 5.0

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-70s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


# ------------------------------------------------------------------ inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
STORED = json.load(open(os.path.join(HERE, 'epochs_v386.json')))
MJD, SRC = STORED['mjd'], STORED['source']
BARY = json.load(open(os.path.join(HERE, 'r8inputs',
                                   'bary_v405.json')))['v_bary_kms']
LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
RCOL = json.load(open(os.path.join(HERE, 'recurcols_v411.json')))
REC = json.load(open(os.path.join(HERE, 'r10inputs',
                                  'recur_v411.json')))['crossings']
HREC = json.load(open(os.path.join(HERE, 'r11inputs', 'events',
                                   'recur_holdout.json')))['crossings']
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']

# ★★★★ ROUND 14 INTEGRATION: THE WITNESSES AND THE PREDICATE NOW LIVE IN
# `epochs_r14.py`, WHICH FOUR GENERATORS IMPORT.  This file measured the defect
# and built the correction, and then `epochsplit_v399.py`, `cover_v412.py`,
# `recur_v411.py`, `maskso_v414.py` and the confirmation-coverage figure each
# still classified separations out of the broken file -- so the fix had to be
# made in six places and agree in six places.  One module owns it; this file
# keeps the measurement of the defect, because the paper states it.
MS = _ep.MS
VB = _ep.VB
_spread = _ep.VB_SPREAD
SHARED = _ep.SHARED
_cmp, _wrong = _ep.CMP, _ep.WRONG
_within, _tp, _fp = _ep.WITHIN, _ep.NTRUE, _ep.NFALSE
apart = _ep.apart
ck('E1 no execution block is read out of a measurement set with two '
   'different start times', not _ep.MS_MULTI,
   '%d blocks read' % len(MS))
ck('E2 the barycentric term is a property of the block and not of the '
   'window', _spread < 0.05,
   'largest spread across one block\'s windows %.4f km/s' % _spread)

# ---------------------------------------------------- the defect, measured
_src_cnt = collections.Counter((META.get(e) or {}).get('meta_src')
                               for e in MJD)
m('ZdNOwnRow', '%d' % _src_cnt['asdm_uid'])
m('ZdNOusRow', '%d' % _src_cnt['member_ous'])
m('ZdNBlockStored', '%d' % len(MJD))
m('ZdNStamp', '%d' % _ep.NSTAMP)
m('ZdNShared', '%d' % len(SHARED))
m('ZdNChecked', '%d' % len(_cmp))
m('ZdNWrong', '%d' % len(_wrong))
m('ZdWorstD', '%.0f' % _ep.WORST_D)
ck('E3 the stored block epochs disagree with the measurement sets wherever '
   'both exist, so the stored file cannot be used for an interval',
   len(_wrong) > 0.5 * len(_cmp) if DRIVE != 3 else False,
   '%d of %d checked blocks disagree, the worst by %.0f d; %d of %d blocks '
   'share a stamp with another block'
   % (len(_wrong), len(_cmp), _ep.WORST_D, len(SHARED), len(MJD)))
m('ZdBaryTol', '%.1f' % BARY_TOL)
m('ZdBaryWithinMax', '%.2f' % _ep.WITHIN_MAX)
m('ZdBaryNTrue', '%d' % _tp)
m('ZdBaryNFalse', '%d' % _fp)
m('ZdBaryNPair', '%d' % _ep.NPAIR)
ck('E4 the barycentric witness separates blocks and never falsely separates '
   'two taken within a day',
   _fp == 0 and _tp > 100 and _ep.WITHIN_MAX < 0.5 * BARY_TOL
   if DRIVE != 4 else False,
   '%d pairs separated correctly, %d falsely; the largest difference among '
   'pairs genuinely within a day is %.2f km/s against a threshold of %.1f'
   % (_tp, _fp, _ep.WITHIN_MAX, BARY_TOL))


# ------------------------------- the epoch-separation split, recomputed
BYSYSA = collections.defaultdict(set)
for r in CAT:
    if r['resolution_class'] == 'fine':
        BYSYSA[r['system_id']].add(r['eb'])
pub = collections.Counter()
cor = collections.Counter()
MOVED = []
for sid, ebs in BYSYSA.items():
    ts = sorted(MJD[e] for e in ebs if e in MJD)
    if len(ts) < 2:
        p = 'one'
    elif max(ts[i + 1] - ts[i] for i in range(len(ts) - 1)) < SEP:
        p = 'sameday'
    else:
        p = 'indep'
    if len(ebs) < 2:
        c = 'one'
    elif any(apart(a, b) for a, b in itertools.combinations(sorted(ebs), 2)):
        c = 'indep'
    else:
        c = 'sameday'
    pub[p] += 1
    cor[c] += 1
    if p != c:
        MOVED.append((sid, p, c, len(ebs),
                      max(abs(VB[a] - VB[b])
                          for a, b in itertools.combinations(
                              [e for e in ebs if e in VB], 2))))
m('ZdNSysA', '%d' % len(BYSYSA))
m('ZdPubOne', '%d' % pub['one'])
m('ZdPubSameDay', '%d' % pub['sameday'])
m('ZdPubNoConf', '%d' % (pub['one'] + pub['sameday']))
m('ZdPubIndep', '%d' % pub['indep'])
m('ZdCorOne', '%d' % cor['one'])
m('ZdCorSameDay', '%d' % cor['sameday'])
m('ZdCorNoConf', '%d' % (cor['one'] + cor['sameday']))
m('ZdCorIndep', '%d' % cor['indep'])
m('ZdNMoved', '%d' % len(MOVED))
m('ZdMovedList', ', '.join(sorted(
    s.split(' Gaia')[0].replace(' ', '~') for s, _, _, _, _ in MOVED)))
# ★★ E5 IS REPOINTED AT ROUND 14 AND IT IS NOW THE SINGLE-VALUEDNESS CHECK.
# It used to require the STORED-STAMP split to equal round 410's macros, which
# was the right check while round 410 still published the stored-stamp figure.
# Round 410 now classifies on the measured epochs through the same module this
# file does, so what has content is that the two determinations AGREE and that
# the stored-stamp pair -- the defect -- is strictly different from both.  A
# bare "they agree" would pass if both were computed the same wrong way, which
# is why the second clause is here.  Driven at --drive 5.
ck('E5 the measured split and round 410 agree exactly, and the stored-stamp '
   'split differs from both -- one quantity, one value, and the defect still '
   'visible',
   (cor['one'] == int(macro('ScSysOneBlock'))
    and cor['sameday'] == int(macro('ScSysSameDay'))
    and cor['one'] + cor['sameday'] == int(macro('ScSysNoConf'))
    and (pub['one'], pub['sameday']) != (cor['one'], cor['sameday']))
   if DRIVE != 5 else False,
   'measured %d + %d = %d, round 410 %s + %s = %s; the stored stamps give '
   '%d + %d = %d'
   % (cor['one'], cor['sameday'], cor['one'] + cor['sameday'],
      macro('ScSysOneBlock'), macro('ScSysSameDay'), macro('ScSysNoConf'),
      pub['one'], pub['sameday'], pub['one'] + pub['sameday']))
ck('E6 correcting the epochs moves systems only out of the same-day class '
   'and never into it, because the witness is one-sided',
   all(p == 'sameday' and c == 'indep' for _, p, c, _, _ in MOVED)
   if DRIVE != 6 else False,
   '%d systems move: %s'
   % (len(MOVED), '; '.join('%s %.1f km/s' % (s.split(' Gaia')[0], d)
                            for s, _, _, _, d in MOVED)))

# ---------------- the confirmable system count, on the corrected comparison
CLA = [r for r in CAT if r['search_class'] == 'A']
BYSYSCLA = collections.defaultdict(list)
for r in CLA:
    BYSYSCLA[r['system_id']].append(r)


def confirmable(rows):
    iv = [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
           max(float(r['flo_GHz']), float(r['fhi_GHz'])), r['eb'])
          for r in rows]
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        es = sorted({e for a, b, e in iv if a <= mid <= b})
        if any(apart(a, b) for a, b in itertools.combinations(es, 2)):
            return True
    return False


_nc = sum(1 for _s, rows in BYSYSCLA.items() if confirmable(rows))
m('ZdConfSysPub', macro('RcConfSysDay'))
m('ZdConfSysCor', '%d' % _nc)
# ★ E7 at round 14: recur_v411.py now measures the same comparison through
# the same module, so this is no longer "can only add" -- the two must be the
# same number.  The published count moved 30 -> 37 with the epoch fix.
ck('E7 the confirmable system count agrees with the one the recurrence '
   'section publishes, both measured on the same epochs',
   _nc == int(macro('RcConfSysDay')) if DRIVE != 7 else False,
   '%d against the published %s' % (_nc, macro('RcConfSysDay')))

# ======================================================= minor 10, the row
# The three crossings whose repeat interval is printed as zero.
# A row whose interval is printed as zero is one the recurrence campaign
# never covered -- so the ledger fills it from the stored stamps -- whose own
# block shares a stamp with another block of the same system.  The condition
# is the mechanism, not the printed value, so this does not read the table it
# diagnoses.
SYSOF = {}
for r in CAT:
    SYSOF.setdefault(r['eb'], r['system_id'])
EBSOF = collections.defaultdict(set)
for r in CAT:
    EBSOF[r['system_id']].add(r['eb'])
Z = []
for r in LED:
    if (RCOL.get('%s|%.6f' % (r['eb'], r['freq'])) or {}).get('T_pers'):
        continue
    if not r.get('line_coincident'):
        continue
    sid = SYSOF.get(r['eb'])
    if not sid or r['eb'] not in MJD:
        continue
    sib = [e for e in EBSOF[sid] if e != r['eb'] and e in MJD]
    if sib and all(MJD[e] == MJD[r['eb']] for e in sib):
        Z.append(r)
ZSTAR = sorted({r['star'] for r in Z})
ZEB = sorted({r['eb'] for r in Z})
# their own epochs, from a measurement set where one survives and from the
# block's own archive stamp where the archive does index it directly
EPOCH = {}
for e in ZEB:
    if e in MS:
        EPOCH[e] = (MS[e], 'measurement set')
    else:
        # the archive indexes this block directly where it returns a start
        # time of its own; the blocks it does not index carry none at all and
        # inherited this one through the observing unit set.
        t = [float(x) for x in (META.get(e) or {}).get('t_min') or []]
        if t and (META.get(e) or {}).get('meta_src') == 'asdm_uid':
            EPOCH[e] = (min(t), 'archive, indexed by block')
_known = sorted(v[0] for v in EPOCH.values())
_dts = sorted(abs(a - b) for a, b in itertools.combinations(_known, 2))
# ★ Every block toward that star whose own measurement set survives, census
# and hold-out together: the span the epochs certify without the archive.
_zsid = SYSOF.get(ZEB[0])
_zms = sorted(MS[e] for e in EBSOF.get(_zsid, ()) if e in MS)
m('ZdZeroNMs', '%d' % len(_zms))
m('ZdZeroSpanD', '%.1f' % (_zms[-1] - _zms[0]) if len(_zms) > 1 else '--')
m('ZdZeroNRow', '%d' % len(Z))
m('ZdZeroStar', ZSTAR[0].replace(' ', '~'))
m('ZdZeroNBlock', '%d' % len(ZEB))
m('ZdZeroNEpoch', '%d' % len(EPOCH))
m('ZdZeroDtMin', '%.1f' % _dts[0])
m('ZdZeroDtMax', '%.1f' % _dts[-1])
_zvb = [abs(VB[a] - VB[b]) for a, b in itertools.combinations(ZEB, 2)
        if a in VB and b in VB]
m('ZdZeroDvBary', '%.0f' % max(_zvb))
ck('E8 the crossings whose interval is printed as zero are in blocks that '
   'are provably days apart',
   len(Z) > 0 and _dts[0] > SEP and len(set(ZSTAR)) == 1
   if DRIVE != 8 else False,
   '%d rows, all %s, %d blocks sharing one stamp; measured intervals '
   '%.1f-%.1f d within the trio and %.1f d over the %d blocks toward that '
   'star whose measurement sets survive'
   % (len(Z), ZSTAR[0], len(ZEB), _dts[0], _dts[-1],
      _zms[-1] - _zms[0], len(_zms)))

# =============================================== minor 12, three readings
# The hold-out crossing that IS present again carries three readings of one
# cell.  The ledger's own column for the census rows of the same star carries
# a FOURTH quantity under the same name: the largest stellar statistic among
# the covering blocks' own crossings, which is not a repeat measurement at
# all.  Both are demonstrated here.
H = [v for v in HREC.values() if v['star'] == ZSTAR[0]]
HB = max((b for v in H for b in v['blocks']),
         key=lambda b: b['T_bestdrift_pub'])
# The census repeat column for these rows is filled by the ledger's own rule
# for a crossing that IS present again: the largest stellar statistic among
# the covering blocks' own crossings.  That is reproduced here from the rows
# themselves -- which is the point: it is a property of the OTHER rows and
# not a reading of the repeat.
_tstars = sorted((float(r['tstar']) for r in Z), reverse=True)
_treps = sorted((max(float(o['tstar']) for o in Z if o is not r)
                 for r in Z), reverse=True)
m('ZdHoTRep', macro('HoRecTRep'))
m('ZdHoNRep', macro('HoRecNRep'))
m('ZdHoTAnyDrift', macro('HoRecTAnyDrift'))
m('ZdHoDeepEb', HB['eb'].replace('A002_', '').replace('_', r'\_'))
m('ZdCensusTRepMax', '%.2f' % _treps[0])
m('ZdCensusTStarMax', '%.3f' % _tstars[0])
m('ZdCensusTStarSnd', '%.3f' % _tstars[1])
ck('E9 the census repeat column for these rows carries the largest stellar '
   'statistic of the OTHER rows, not a reading of the repeat',
   abs(_treps[0] - _tstars[0]) < 0.01 and abs(_treps[-1] - _tstars[1]) < 0.01
   if DRIVE != 9 else False,
   'repeat column %s against the rows\' own statistics %s'
   % ([round(x, 2) for x in _treps], [round(x, 3) for x in _tstars]))
ck('E10 the two hold-out readings the referee calls contradictory are a '
   'combination over blocks and a maximum over one block, so neither '
   'contains the other',
   abs(float(macro('HoRecTAnyDrift')) - HB['T_bestdrift_pub']) < 0.01
   and int(macro('HoRecNRep')) > 1 if DRIVE != 10 else False,
   'combination over %s blocks gives %s; the largest single block, %s, '
   'reaches %.2f at its own best drift'
   % (macro('HoRecNRep'), macro('HoRecTRep'), HB['eb'],
      HB['T_bestdrift_pub']))

# ================================================= minor 13, CP-72 2713
A01 = REC['A01']
_bl = A01['blocks']
_near = min(_bl, key=lambda b: abs(b['sep_from_discovery_h']))
_deep = min(_bl, key=lambda b: b['rms_combined_mJy'])
_away = [b for b in _bl if abs(b['sep_from_discovery_h']) > 24.0]
_q = RCOL['%s|%.6f' % (A01['eb'], A01['freq_GHz'])]
m('ZdCpStar', 'CP$-$72~2713')
m('ZdCpNRep', '%d' % len(_bl))
m('ZdCpNAway', '%d' % len(_away))
m('ZdCpNearH', '%.2f' % abs(_near['sep_from_discovery_h']))
m('ZdCpSpanD', '%.0f' % (max(abs(b['sep_from_discovery_h'])
                             for b in _bl) / 24.0))
m('ZdCpTRepComb', '%+.2f' % _q['T_rep'])
m('ZdCpTRepDeep', '%+.2f' % _deep['T_matched'])
m('ZdCpTPersComb', '%.2f' % _q['T_pers'])
m('ZdCpDeepH', '%.2f' % abs(_deep['sep_from_discovery_h']))
ck('E11 CP-72 2713 is not a within-night test: most of its covering blocks '
   'are more than a day away',
   len(_away) > len(_bl) / 2.0 if DRIVE != 11 else False,
   '%d of %d covering blocks are more than a day away, the nearest is '
   '%.2f h and the longest baseline %.0f d'
   % (len(_away), len(_bl), abs(_near['sep_from_discovery_h']),
      max(abs(b['sep_from_discovery_h']) for b in _bl) / 24.0))
ck('E12 the two values quoted for its repeat statistic are a combination '
   'over every covering block and a reading in the single deepest one',
   abs(_deep['T_matched'] - float(macro('EvBDeepTObs'))) < 0.01
   and abs(_q['T_rep'] - float(macro('EvBDeepTObs'))) > 0.1
   if DRIVE != 12 else False,
   'combination %+.2f over %d blocks; deepest block alone %+.2f, and the '
   'figure caption prints %s' % (_q['T_rep'], len(_bl), _deep['T_matched'],
                                macro('EvBDeepTObs')))

# ======================================= minor 14, the four denominators
D = [('ZdDenTested', 'the unattributed crossings, all tested',
      int(macro('RcNTested'))),
     ('ZdDenAmp', 'those retaining a discovery amplitude',
      int(macro('RcNExclPoss'))),
     ('ZdDenQuoted', 'those carrying a quoted exclusion',
      int(macro('RcNExcl'))),
     ('ZdDenCovered', 'those a window of another block also covers',
      int(macro('WdNOrbTot')))]
# ★ These are NOT re-published: the four counts were never wrong, they were
# unnamed, and a second macro carrying the same value is how this project
# acquires two numbers for one quantity.  The prose names the sets apart and
# goes on citing the existing macros; what is added here is the assertion
# that they are nested, which is what nobody had checked.
m('ZdDenNoAmp', '%d' % (D[0][2] - D[1][2]))
ck('E13 the four counts Sec. 5.6 quotes are nested sets and are named apart '
   'in the prose', [v for _, _, v in D] == sorted(
       (v for _, _, v in D), reverse=True) if DRIVE != 13 else False,
   ' > '.join('%d (%s)' % (v, lab) for _, lab, v in D))

# ★ THE DEPOSIT ANY OTHER GENERATOR NEEDS: a measured epoch per block, from a
# measurement set where one survives and from the archive only where the
# archive indexes that block directly; plus every block's own barycentric
# term, so a separation can be established where no epoch survives at all.
MEASURED = {}
for e in sorted(set(MJD) | set(MS)):
    if e in MS:
        MEASURED[e] = [MS[e], 'measurement set']
    else:
        # ★ The archive's own record says which blocks it indexed directly:
        # `meta_src == 'asdm_uid'` is this block's own row, and
        # `'member_ous'` is the whole observing unit's, which is the defect.
        _t = [float(x) for x in (META.get(e) or {}).get('t_min') or []]
        if _t and (META.get(e) or {}).get('meta_src') == 'asdm_uid':
            MEASURED[e] = [min(_t), 'archive, indexed by block']
_dark = sorted(e for e in MJD if e not in MEASURED and e not in VB)
m('ZdNMeasured', '%d' % len(MEASURED))
m('ZdNDark', '%d' % len(_dark))
# ★ Two blocks have neither, and they are named rather than quietly left to
# the stored stamp.  A quantity that cannot be measured is declared.
ck('E14 all but a named few blocks have a measured epoch or a barycentric '
   'term, so a comparison need not fall back on the stored stamp',
   len(_dark) <= 2 if DRIVE != 14 else False,
   '%d blocks with a measured epoch, %d with a barycentric term, %d with '
   'neither: %s' % (len(MEASURED), sum(1 for e in MJD if e in VB),
                    len(_dark), ', '.join(_dark) or 'none'))

json.dump(dict(measured_epochs=MEASURED, v_bary_kms=VB,
               bary_tol_kms=BARY_TOL, sep_days=SEP,
               moved=MOVED, shared=len(SHARED), wrong=len(_wrong),
               checked=len(_cmp), zero_epochs=EPOCH,
               pub=dict(pub), cor=dict(cor), conf_cor=_nc),
          open(OUTJ, 'w'), indent=1, default=str)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by epochfix_v415.py (round %d) -- do not '
             'hand-edit.\n' % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
if FAIL:
    print('FAILED: %s' % '; '.join(FAIL))
    sys.exit(1)
