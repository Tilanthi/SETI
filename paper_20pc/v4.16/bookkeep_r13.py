#!/usr/bin/env python3
r"""round 340 -> survey_numbers_round340.tex: THE BOOKKEEPING THAT THREE
APPENDICES STATED THREE DIFFERENT WAYS.

Five quantities in this paper were published under one name apiece while
being computed over different sets, which is the defect this file closes.
Each is recomputed here from the released catalogue, the hold-out export and
the frozen calibration record, and each is published with the set it belongs
to named in its own macro.

  1. THE SPATIAL RANK'S FIRST-PLACE COUNT.  The paper prints 14 against 3.2
     in one appendix and 12 + 0 against 0.78 + 2.43 in another.  Both are
     right and neither says what it is conditioned on: 14 is the number of
     windows whose star outranks all 512 probes, and 12 is the number that
     ALSO reaches the trigger.  The two windows between them are
     coarse-channel and sit below it.  Asserted to close.

  2. THE HOLD-OUT'S RANK DISPLACEMENT AGAINST THE SURVEY'S.  The published
     comparison pools windows, so its two intervals do not overlap and the
     paper concluded that the displacement is a property of the reserved
     blocks.  That conclusion cannot stand for a hash-random subsample, and
     it does not survive the measurement: the hold-out's 315 windows are
     concentrated on a handful of stars, and compared star by star over the
     27 stars in both samples the difference is +0.035 with an interval that
     spans zero.  Once each star carries equal weight the two intervals
     overlap.  The pooled difference is a weighting effect, not a tuning.

  3. THE EXTERNAL CALIBRATION SAMPLE.  Its 326 blocks are 263 primary-census
     and 63 hold-out blocks, with none outside either; the block ledger's
     footnote said the opposite.  Its crossing counts were carried over from
     the harvest that built it rather than from the adopted extraction, and
     on the adopted extraction they are smaller: 5 crossings outrank all
     their controls, 4 of them beta Pictoris carbon monoxide and 1
     unattributed, and none of them is in a hold-out block -- which is what
     the hold-out search itself reports.

  4. THE WINDOW-LEVEL DATA-QUALITY FLAG against the execution-block quality
     criterion.  Two criteria wore one name.  The flag is a property of a
     window (`dqflag.py`): the median of its own 512-probe control ensemble
     above twice the survey median of that quantity.  It fires on 5 windows
     in 2 blocks toward 2 stars.  The block criterion is built from it and
     fails 1 block.  Both counts are published here with the predicate that
     produces them named.

  5. THE WITHHELD EPSILON ERIDANI BAND 6 WINDOWS.  Four of the twelve need
     no beam correction at all.  They are measured, they carry no crossing,
     and their thresholds are published here, so that the nearest star in
     this part of the sample is not left with no limit for the sake of a
     tidy exclusion rule.

Also: the integration-time coverage behind the intra-integration smearing
statement, and the Gaia DR3 identity of the one target carried under an ALMA
source designation.

Usage:  bookkeep_r13.py [--drive N]      N in 1..10, each breaks one assertion
"""
import collections
import csv
import json
import math
import os
import re
import sys

import numpy as np

import star_alias as sa

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 340
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SUF = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = 'survey_numbers_round340%s.tex' % SUF
OUT_PATH = os.path.join(HERE, OUT)

CAT_NAME = 'per_target_results_v3.99.csv'
NPROBE = 512
TRIG = 5.0
MASK_HALF_KMS = 50.0
BOOT = 20000
SEED = 20261007

M, FAIL = [], []


def m(k, v):
    M.append('\\newcommand{\\%s}{%s}' % (k, v))


def ck(name, cond, detail=''):
    print('  %-74s %s' % (name[:74], 'OK' if cond else 'FAIL ' + str(detail)))
    if not cond:
        FAIL.append(name.split()[0])


def texval(macro):
    """Read a published macro back out of the macro layer, so that nothing
    here can disagree with a number the paper already prints."""
    pat = re.compile(r'(?:new|renew|provide)command\{\\%s\}\{([^}]*)\}'
                     % macro)
    for fn in sorted(os.listdir(HERE)):
        if not fn.startswith('survey_numbers') or not fn.endswith('.tex'):
            continue
        mm = pat.search(open(os.path.join(HERE, fn)).read())
        if mm:
            return mm.group(1)
    raise KeyError(macro)


def texnum(macro):
    return float(texval(macro).replace('\\,', '').replace(',', ''))


CAT = list(csv.DictReader(open(os.path.join(HERE, CAT_NAME))))
HOLD = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
CCAL = json.load(open(os.path.join(HERE, 'ctrl_calib_v372.json')))
EXPORT = json.load(open(os.path.join(HERE,
                                     'corrected_export_v399.json')))['rows']
ALMAID = json.load(open(os.path.join(HERE, 'r13inputs', 'almaid_r13.json')))

print('bookkeep_r13 round %d%s' % (ROUND, '' if not DRIVE
                                   else ' (drive %d)' % DRIVE))


def tex_star(name):
    """The paper's own display form, with the internal space tied so a star
    name cannot break across a line."""
    return sa.designation(name).replace(' ', '~')


def attributed(row):
    v = row['line_offset_kms']
    return v not in ('', None) and abs(float(v)) <= MASK_HALF_KMS


# =====================================================================
# 1. THE FIRST-PLACE COUNT, WITH AND WITHOUT THE TRIGGER CONDITION
# =====================================================================
FIRST = [r for r in CAT if int(r['n_ctrl_ge_star']) == 0]
FIRST_TRIG = [r for r in FIRST if float(r['star_snr']) >= TRIG]
BELOW = [r for r in FIRST if float(r['star_snr']) < TRIG]

n_fine = sum(1 for r in FIRST_TRIG if r['search_class'] == 'A')
n_coarse = len(FIRST_TRIG) - n_fine

print('\n1. first place')
print('   %d windows outrank all %d probes; %d of them reach the trigger '
      '(%d fine, %d coarse); %d do not'
      % (len(FIRST), NPROBE, len(FIRST_TRIG), n_fine, n_coarse, len(BELOW)))
for r in BELOW:
    print('     below trigger: %-30s %s T*=%.2f class %s'
          % (r['star_name'][:30], r['eb'], float(r['star_snr']),
             r['search_class']))

_tot = len(FIRST) if DRIVE != 1 else len(FIRST) + 1
ck('B1 the two published first-place counts differ by exactly the windows '
   'below the trigger, and the published fine and coarse counts are the '
   'conditioned ones',
   len(FIRST_TRIG) + len(BELOW) == _tot
   and n_fine == int(texnum('NStageOneFine'))
   and n_coarse == int(texnum('NStageOneCoarse'))
   and len(FIRST) == int(texnum('NsrFirstObs')),
   '%d + %d against %d; fine %d/%s coarse %d/%s; all %d/%s'
   % (len(FIRST_TRIG), len(BELOW), _tot, n_fine, texval('NStageOneFine'),
      n_coarse, texval('NStageOneCoarse'), len(FIRST),
      texval('NsrFirstObs')))

m('BkFirstBelow', '%d' % len(BELOW))
m('BkFirstBelowTLo', '%.2f' % min(float(r['star_snr']) for r in BELOW))
m('BkFirstBelowTHi', '%.2f' % max(float(r['star_snr']) for r in BELOW))

# =====================================================================
# 2. THE HOLD-OUT'S RANK DISPLACEMENT, STAR BY STAR
# =====================================================================
rng = np.random.default_rng(SEED)
sv = collections.defaultdict(list)
for r in CAT:
    sv[r['star_name']].append(float(r['p_rank_addone']))
ho = collections.defaultdict(list)
for r in HOLD:
    c = r.get('ctrl_all')
    if not c or r.get('star_snr') is None:
        continue
    c = np.asarray(c, float)
    if c.size != NPROBE or not np.all(np.isfinite(c)):
        continue
    ho[r['star_name']].append(
        (1 + int((c >= r['star_snr']).sum())) / float(NPROBE + 1))

ho_all = np.concatenate([np.asarray(v) for v in ho.values()])
sv_all = np.concatenate([np.asarray(v) for v in sv.values()])
POOLED = float(np.median(ho_all) - np.median(sv_all))

common = sorted(set(sv) & set(ho))
d = np.array([np.median(ho[s]) - np.median(sv[s]) for s in common])
PAIRED = float(np.median(d))
_b = np.array([np.median(d[rng.integers(0, len(d), len(d))])
               for _ in range(BOOT)])
PAIR_LO, PAIR_HI = (float(x) for x in np.percentile(_b, [2.5, 97.5]))


def star_balanced(byst):
    v = np.array([np.median(x) for x in byst.values()])
    bb = np.array([np.median(v[rng.integers(0, len(v), len(v))])
                   for _ in range(BOOT)])
    return float(np.median(v)), tuple(float(x) for x in
                                      np.percentile(bb, [2.5, 97.5]))


HO_BAL, (HO_BAL_LO, HO_BAL_HI) = star_balanced(ho)
SV_BAL, (SV_BAL_LO, SV_BAL_HI) = star_balanced(sv)
_sz = sorted((len(v) for v in ho.values()), reverse=True)
TOP5 = sum(_sz[:5])
TOP5_PCT = 100.0 * TOP5 / len(ho_all)

print('\n2. the rank displacement')
print('   pooled: hold-out %.3f over %d windows, survey %.3f over %d, '
      'difference %+.3f' % (np.median(ho_all), len(ho_all),
                            np.median(sv_all), len(sv_all), POOLED))
print('   paired over the %d stars in both: %+.3f (95%% %+.3f to %+.3f)'
      % (len(common), PAIRED, PAIR_LO, PAIR_HI))
print('   star-balanced: hold-out %.3f (%.3f-%.3f) against survey %.3f '
      '(%.3f-%.3f)' % (HO_BAL, HO_BAL_LO, HO_BAL_HI, SV_BAL, SV_BAL_LO,
                       SV_BAL_HI))
print('   the hold-out\'s five largest stars carry %d of its %d windows '
      '(%.0f per cent)' % (TOP5, len(ho_all), TOP5_PCT))

_lo, _hi = (PAIR_LO, PAIR_HI) if DRIVE != 2 else (0.02, 0.09)
ck('B2 the star-by-star difference in rank spans zero, so the pooled '
   'displacement is not reproduced star by star',
   _lo < 0.0 < _hi, 'paired %+.3f, 95 per cent %+.3f to %+.3f'
   % (PAIRED, _lo, _hi))

_hb = HO_BAL_HI if DRIVE != 3 else SV_BAL_LO - 0.01
ck('B3 and once each star carries equal weight the two intervals overlap, '
   'which the pooled ones do not',
   _hb >= SV_BAL_LO and texnum('HoRankMedHi') < texnum('SurvBootLo'),
   'star-balanced hold-out to %.3f against survey from %.3f; pooled %s-%s '
   'against %s-%s' % (_hb, SV_BAL_LO, texval('HoRankMedLo'),
                      texval('HoRankMedHi'), texval('SurvBootLo'),
                      texval('SurvBootHi')))

m('BkRankPooledDiff', '%.3f' % abs(POOLED))
m('BkRankPairedStars', '%d' % len(common))
m('BkRankPaired', '%+.3f' % PAIRED)
m('BkRankPairedLo', '%+.2f' % PAIR_LO)
m('BkRankPairedHi', '%+.2f' % PAIR_HI)
m('BkRankBalHo', '%.2f' % HO_BAL)
m('BkRankBalHoLo', '%.2f' % HO_BAL_LO)
m('BkRankBalHoHi', '%.2f' % HO_BAL_HI)
m('BkRankBalSurv', '%.2f' % SV_BAL)
m('BkRankBalSurvLo', '%.2f' % SV_BAL_LO)
m('BkRankBalSurvHi', '%.2f' % SV_BAL_HI)
m('BkRankTopFiveWin', '%d' % TOP5)
m('BkRankTopFivePct', '%.0f' % TOP5_PCT)

# the set the "99 of 149 blocks" sign test actually belongs to: the archival
# extension campaign, not the pre-registered hold-out.
EXT_REC = json.load(open(os.path.join(HERE, 'heldout_v352.json')))
_ew = [w for w in EXT_REC['windows']
       if not w.get('detection') and not w.get('stage1')]
EXT_STARS = len({w['star'] for w in _ew})
EXT_BLOCKS = len({w['eb'] for w in _ew})
EXT_MED = float(np.median([w['p_star_empirical'] for w in _ew]))
EXT_BELOW = sum(1 for b in {w['eb'] for w in _ew}
                if np.mean([w['p_star_empirical'] for w in _ew
                            if w['eb'] == b]) < 0.5)
print('   the block sign test\'s own sample: %d windows, %d blocks, %d '
      'stars, median rank %.3f, %d blocks below one half'
      % (len(_ew), EXT_BLOCKS, EXT_STARS, EXT_MED, EXT_BELOW))
_eb = EXT_BLOCKS if DRIVE != 4 else int(texnum('HoBlocks'))
ck('B4 the published block sign test and 0.440 median are NOT the reserved '
   'hold-out\'s: they reproduce on the extension campaign, whose block count '
   'differs from the hold-out\'s',
   _eb == int(texnum('HOBlockN')) and _eb != int(texnum('HoBlocks'))
   and EXT_BELOW == int(texnum('HOBlockBelow'))
   and abs(EXT_MED - texnum('HOBootMed')) < 5e-4,
   '%d blocks against the published %s and the hold-out\'s %s; %d below '
   'against %s; median %.3f against %s'
   % (_eb, texval('HOBlockN'), texval('HoBlocks'), EXT_BELOW,
      texval('HOBlockBelow'), EXT_MED, texval('HOBootMed')))
m('BkExtRankStars', '%d' % EXT_STARS)
m('BkExtRankWin', '%d' % len(_ew))

# =====================================================================
# 3. THE EXTERNAL CALIBRATION SAMPLE, ON THE ADOPTED EXTRACTION
# =====================================================================
_EBPAT = re.compile(r'(A002_X[0-9a-f]+_X[0-9a-f]+)_spw')


def eb_of(key):
    mm = _EBPAT.match(key)
    return mm.group(1) if mm else None


CAL_ALL = {eb_of(k) for k in CCAL}
CENS_EB = {r['eb'] for r in CAT}
HOLD_EB = {r['eb'] for r in HOLD}
OUTSIDE = sorted(b for b in CAL_ALL if b not in CENS_EB and b not in HOLD_EB)
CAL = CAL_ALL - set(OUTSIDE)

cal_cat = [r for r in CAT if r['eb'] in CAL]
cal_hold = [r for r in HOLD if r['eb'] in CAL and r.get('ctrl_all')
            and r.get('star_snr') is not None]
cx = [r for r in cal_cat if float(r['star_snr']) >= TRIG]
cf = [r for r in cx if int(r['n_ctrl_ge_star']) == 0]
hx = [r for r in cal_hold if float(r['star_snr']) >= TRIG]
hf = [r for r in hx if max(r['ctrl_all']) < float(r['star_snr'])]
cf_att = [r for r in cf if attributed(r)]
cf_un = [r for r in cf if not attributed(r)]
CAL_WIN = len(cal_cat) + len(cal_hold)
CAL_EXP = CAL_WIN * texnum('PseudoFirstHO')

print('\n3. the external calibration sample')
print('   %d blocks: %d census + %d hold-out, %d outside both (%s)'
      % (len(CAL), len(CAL & CENS_EB), len(CAL & HOLD_EB), len(OUTSIDE),
         ', '.join(OUTSIDE) or 'none'))
print('   %d windows, %d crossings, %d outranking every control: %d '
      'attributed, %d unattributed; hold-out side %d'
      % (CAL_WIN, len(cx) + len(hx), len(cf) + len(hf), len(cf_att),
         len(cf_un), len(hf)))
for r in cf:
    print('     %-18s %-22s T*=%6.2f ctrl=%5.2f %s'
          % (r['star_name'][:18], r['eb'], float(r['star_snr']),
             float(r['ctrl_max_snr']),
             r['nearest_line'] if attributed(r) else 'unattributed'))

_nout = len(OUTSIDE) if DRIVE != 5 else 3
ck('B5 exactly one block of the harvest lies outside the census and the '
   'hold-out, and removing it leaves the published sample entirely inside '
   'them, so it is not external to the survey',
   _nout == 1 and len(CAL) == int(texnum('CalNBlock'))
   and len(CAL & CENS_EB) == int(texnum('CalNCensus'))
   and len(CAL & HOLD_EB) == int(texnum('CalNHoldout'))
   and len(CAL & CENS_EB) + len(CAL & HOLD_EB) == len(CAL),
   '%d outside; %d blocks = %d census (%s) + %d hold-out (%s)'
   % (_nout, len(CAL), len(CAL & CENS_EB), texval('CalNCensus'),
      len(CAL & HOLD_EB), texval('CalNHoldout')))

_nhf = len(hf) if DRIVE != 6 else 1
ck('B6 no hold-out crossing in the calibration sample outranks its '
   'controls, which is what the hold-out search reports, and the '
   'first-place crossings split into the attributed and the one that is not',
   _nhf == 0 and len(cf_att) + len(cf_un) == len(cf) and len(cf_un) == 1
   and all(r['star_name'] == 'bet Pic' for r in cf_att),
   '%d hold-out, %d attributed + %d unattributed = %d'
   % (_nhf, len(cf_att), len(cf_un), len(cf)))

m('BkCalWin', '%d' % CAL_WIN)
m('BkCalWinCensus', '%d' % len(cal_cat))
m('BkCalWinHold', '%d' % len(cal_hold))
m('BkCalNCross', '%d' % (len(cx) + len(hx)))
m('BkCalNFirst', '%d' % (len(cf) + len(hf)))
m('BkCalNFirstBpic', '%d' % len(cf_att))
m('BkCalNFirstUnattr', '%d' % len(cf_un))
m('BkCalNFirstHold', '%d' % len(hf))
m('BkCalUnattrStar', tex_star(cf_un[0]['star_name']))
m('BkCalUnattrGHz', '%.4f' % float(cf_un[0]['f_cross_GHz']))
m('BkCalExpFirst', '%.1f' % CAL_EXP)

# =====================================================================
# 4. THE WINDOW FLAG AGAINST THE BLOCK CRITERION
# =====================================================================
import dqflag                                             # noqa: E402

FL = dqflag.flagged_keys(HERE)
FL_EB = dqflag.flagged_ebs(HERE)
flag_rows = [r for r in CAT if dqflag.is_flagged_row(r, HERE)]
flag_cross = [r for r in flag_rows if float(r['star_snr']) >= TRIG]
FLAG_STARS = sorted({r['star_name'] for r in flag_rows})
bq_eb = texval('BqFailBlock').replace('\\_', '_')
flag_other = [r for r in flag_cross if r['eb'] != bq_eb]

print('\n4. the window flag against the block criterion')
print('   ring median above %.1f (twice the survey median %.2f) flags %d '
      'windows in %d blocks toward %d stars: %s'
      % (dqflag.threshold(HERE), dqflag.survey_median(HERE), len(FL),
         len(FL_EB), len(FLAG_STARS), ', '.join(FLAG_STARS)))
print('   %d of the flagged windows carry a crossing; %d of those are '
      'outside the one block the block criterion fails'
      % (len(flag_cross), len(flag_other)))

_nst = len(FLAG_STARS) if DRIVE != 7 else 1
ck('B7 the window flag and the block criterion are not the same test: the '
   'flag reaches a star and a block the block criterion does not fail, and '
   'it spans attributed and unattributed crossings',
   _nst > int(texnum('BqNFail')) and len(FL_EB) > int(texnum('BqNFail'))
   and len(flag_other) > 0 and len(flag_cross) == len(flag_rows)
   and 0 < sum(1 for r in flag_cross if attributed(r)) < len(flag_cross),
   '%d stars and %d blocks flagged against %s block failing; %d flagged '
   'crossings elsewhere; %d of %d attributed'
   % (_nst, len(FL_EB), texval('BqNFail'), len(flag_other),
      sum(1 for r in flag_cross if attributed(r)), len(flag_cross)))

m('BkFlagNBlock', '%d' % len(FL_EB))
m('BkFlagNCross', '%d' % len(flag_cross))
m('BkFlagNCrossOther', '%d' % len(flag_other))
m('BkFlagOtherStar', tex_star(flag_other[0]['star_name']))

# =====================================================================
# 5. THE FOUR ON-AXIS EPSILON ERIDANI WINDOWS
# =====================================================================
EPS = [r for r in EXPORT if r['star_name'] == 'eps Eri' and r['band'] == 6]


def corr_of(r):
    return r['smin'] * 1e3 / (5.0 * r['rms'])


EPS_ON = [r for r in EPS if corr_of(r) <= 1.01]
EPS_FINE = [r for r in EPS_ON if r['chanw'] < 1e6]
EPS_COARSE = [r for r in EPS_ON if r['chanw'] >= 1e6]
EPS_EB = sorted({r['eb'] for r in EPS_ON})
EPS_T = max(r['star_snr'] for r in EPS_ON)
EPS_H = sum(r['onsrc'] for r in EPS_ON) / 3600.0


def sci(x):
    e = int(math.floor(math.log10(x)))
    return '%.1f\\times10^{%d}' % (x / 10.0 ** e, e)


print('\n5. the on-axis epsilon Eri windows')
print('   %d of %d need no beam correction, all in %s, %.2f window-hours; '
      '%d fine and %d coarse; largest statistic %.2f against a trigger of '
      '%.0f' % (len(EPS_ON), len(EPS), ', '.join(EPS_EB), EPS_H,
                len(EPS_FINE), len(EPS_COARSE), EPS_T, TRIG))
for r in sorted(EPS_ON, key=lambda x: x['eirp']):
    print('     %9.1f kHz  EIRP %.2e W  T*=%.2f' % (r['chanw'] / 1e3,
                                                    r['eirp'], r['star_snr']))

_t = EPS_T if DRIVE != 8 else TRIG + 1
_con = max(corr_of(r) for r in EPS_ON)
_coff = min(corr_of(r) for r in EPS if corr_of(r) > 1.01)
ck('B8 the on-axis windows need no correction and none reaches the trigger, '
   'the split from the off-axis ones is not marginal, and the count is the '
   'published one',
   _con < 1.0005 and _coff > 1.5 and _t < TRIG
   and len(EPS_ON) == int(texnum('EpsEriNOnAxis'))
   and len(EPS_FINE) + len(EPS_COARSE) == len(EPS_ON) and len(EPS_FINE) > 0,
   'on axis to %.4f against off axis from %.2f, largest statistic %.2f, '
   '%d on axis against %s'
   % (_con, _coff, _t, len(EPS_ON), texval('EpsEriNOnAxis')))

m('BkEpsOnBlock', EPS_EB[0].replace('A002_', '').replace('_', r'\_'))
m('BkEpsOnHours', '%.2f' % EPS_H)
m('BkEpsOnNFine', '%d' % len(EPS_FINE))
m('BkEpsOnNCoarse', '%d' % len(EPS_COARSE))
m('BkEpsOnChanFineKHz', '%.0f' % (EPS_FINE[0]['chanw'] / 1e3))
m('BkEpsOnChanCoarseMHz', '%.1f' % (EPS_COARSE[0]['chanw'] / 1e6))
m('BkEpsOnEirpFine', sci(min(r['eirp'] for r in EPS_FINE)))
m('BkEpsOnEirpCoarseLo', sci(min(r['eirp'] for r in EPS_COARSE)))
m('BkEpsOnEirpCoarseHi', sci(max(r['eirp'] for r in EPS_COARSE)))
m('BkEpsOnTMax', '%.1f' % EPS_T)

# =====================================================================
# 6. THE INTEGRATION-TIME COVERAGE BEHIND THE SMEARING STATEMENT
# =====================================================================
HAVE = [r for r in CAT if r['eta_smear'] not in ('', 'None')]
MISS = [r for r in CAT if r['eta_smear'] in ('', 'None')]
TINT = sorted(float(r['on_source_s']) / float(r['n_int']) for r in HAVE
              if r['n_int'] not in ('', 'None') and float(r['n_int']) > 0)


def ratio(r):
    return float(r['drift_max_Hz_s']) / float(r['chanw_Hz'])


RH = sorted(ratio(r) for r in HAVE)
RM = sorted(ratio(r) for r in MISS)
print('\n6. the smearing coverage')
print('   %d windows carry an integration count and %d do not; integration '
      'time %.1f-%.1f s where it is known'
      % (len(HAVE), len(MISS), TINT[0], TINT[-1]))
print('   drift ceiling over channel width, per second: known %.2e-%.2e, '
      'unknown %.2e-%.2e' % (RH[0], RH[-1], RM[0], RM[-1]))
m('BkSmearNUnver', '%d' % len(MISS))
m('BkSmearIntLo', '%.1f' % TINT[0])
m('BkSmearIntHi', '%.0f' % TINT[-1])

# =====================================================================
# 6b. WHAT BECAME OF THE BLOCKS CALIBRATED AND SEARCHED AFTER THE FREEZE
# =====================================================================
EXT_SEARCHED = int(texnum('LdgExtSearched'))
EXT_REPORTED = int(texnum('LdgExtEB'))
EXT_PARTS = [int(texnum(k)) for k in ('LdgExtNoWindow', 'LdgExtWithheld',
                                      'LdgExtTail')]
NOT_REPORTED = EXT_SEARCHED - EXT_REPORTED
print('\n6b. of %d blocks calibrated and searched, %d are reported and %d '
      'are not (%s)' % (EXT_SEARCHED, EXT_REPORTED, NOT_REPORTED,
                        ' + '.join(str(x) for x in EXT_PARTS)))
_nr = NOT_REPORTED if DRIVE != 10 else NOT_REPORTED + 1
ck('B10 the blocks calibrated and searched but not reported are exactly the '
   'three ledger rows that enter nothing',
   _nr == sum(EXT_PARTS) and EXT_REPORTED + _nr == EXT_SEARCHED,
   '%d against %s = %d' % (_nr, ' + '.join(str(x) for x in EXT_PARTS),
                           sum(EXT_PARTS)))
m('BkExtNotReported', '%d' % NOT_REPORTED)

# =====================================================================
# 7. THE ONE TARGET WITH NO CATALOGUE NAME
# =====================================================================
G = ALMAID['gaia']
ALMA_ROWS = [r for r in CAT
             if r['star_name'] == ALMAID['alma_designation']]
D_GAIA = 1000.0 / G['parallax']
D_CAT = float(ALMA_ROWS[0]['dist_pc']) if DRIVE != 9 else 12.0
print('\n7. %s = Gaia DR3 %d (%s), parallax %.4f +- %.4f mas -> %.4f pc '
      'against the catalogue\'s %.4f; %d windows, %d crossings'
      % (ALMAID['alma_designation'], G['source_id'], ALMAID['sp_type'],
         G['parallax'], G['parallax_error'], D_GAIA, D_CAT, len(ALMA_ROWS),
         sum(1 for r in ALMA_ROWS if float(r['star_snr']) >= TRIG)))
ck('B9 the Gaia identification reproduces the distance the catalogue '
   'already uses for this target, and the parallax is inside the '
   'selection\'s own quality cut',
   abs(D_GAIA - D_CAT) < 1e-3
   and 100.0 * G['parallax_error'] / G['parallax'] < texnum('PlxAdqlPct')
   and G['parallax'] >= 25.0,
   '%.4f against %.4f pc; %.3f per cent against %s'
   % (D_GAIA, D_CAT, 100.0 * G['parallax_error'] / G['parallax'],
      texval('PlxAdqlPct')))
# ★ The designation itself carries digits, so it is emitted rather than
# typed: `intsweep` reads running prose and would otherwise see 33192492 as
# an unregistered integer, which is exactly the check working as intended.
m('BkAlmaName', ALMAID['alma_designation'].replace('-', '$-$'))
m('BkAlmaGaia', '%d' % G['source_id'])
m('BkAlmaSpType', ALMAID['sp_type'])
m('BkAlmaDistPc', '%.1f' % D_GAIA)
m('BkAlmaNCross', '%d' % sum(1 for r in ALMA_ROWS
                             if float(r['star_snr']) >= TRIG))

# =====================================================================
print('\nassertions failed: %d %s' % (len(FAIL), FAIL))
if FAIL and DRIVE == 0:
    raise SystemExit('bookkeep_r13: %d assertion(s) failed: %s'
                     % (len(FAIL), FAIL))

HDR = ['%% GENERATED by bookkeep_r13.py -- do not hand-edit.',
       '%% round ' + str(ROUND) + ': the first-place count with and without '
       'the trigger,',
       '%% the rank displacement compared star by star, the external '
       'calibration',
       '%% sample on the adopted extraction, the window-level data-quality '
       'flag,',
       '%% the four on-axis epsilon Eri windows, and the one target with no',
       '%% catalogue name.']
with open(OUT_PATH, 'w') as fh:
    fh.write('\n'.join(HDR + sorted(M)) + '\n')
print('wrote %s: %d macros' % (OUT, len(M)))
