#!/usr/bin/env python3
r"""num_r22.py -- round 971.  FOUR OF REFEREE 2's NUMERICAL ITEMS, EACH
MEASURED FROM THE RECORD THAT OWNS IT.

 1. R2-11, THE 279 m / 279 BLOCKS COINCIDENCE.  The median longest baseline
    of the blocks with no phase record is recomputed, and the reason the two
    sets differ is measured: it is not a longer baseline per block but a
    different ARRAY MIX.  The distribution is bimodal and the median falls in
    the gap between its modes, so the median is replaced by the mix and the
    within-array medians -- which also takes the 279 off the page beside the
    279 blocks.  The baselines themselves are cross-checked against the
    archive's own angular resolutions, since the measurement sets are gone.

 2. R2-12(a), THE MEDIAN CONTROL STATISTIC, 2.75 AGAINST 2.74.  Two
    generators publish the same quantity over two different populations:
    `fields_v404.py` over the 1476 rows of the corrected export that carry a
    `ctrl_med` field, `dqflag.py` over every window whose 512-position
    ensemble is stored and joins to exactly one catalogue row.  The second is
    the owner of the data-quality predicate, so it is the one value.

 3. R2-12(b), THE PREDICTED-CELL OFFSET.  Sec. 5.6's 0.05 is a VELOCITY in
    km/s -- the registration residual against the line centroid -- and Table
    D2's Delta c column is in CHANNELS.  Both medians are computed here so
    that each is stated once, in its own unit, with the identity that ties
    them: the median |Delta c| is 0.06 of a channel and 0.04 km/s.

 4. R2-9, THE 3.9 PER CENT.  Found.  The published value is the v3.99 ACA
    control-geometry re-extraction and the "surviving product" is the v3.81
    pre-repair extraction of the same window; both are deposited in this
    tree, and each reproduces its own side of the comparison exactly.  The
    discrepancy is the measured effect of a repair the paper describes, not
    an irreproducibility, and the caption must say which is which.

Read-only on the paper tree.  Usage: num_r22.py [--drive N]
★ ROUND RENUMBERED 96x -> 97x BY THE INTEGRATOR (v4.23).  `r22-edge` and
`r22-num` both claimed macro rounds 960-962 in their own queue files in the
same wave -- the race AGENT_RULES warns about and this project's fourth
double claim.  Edge keeps 960-962 (`edge_v423.py`, `proxb_v423.py`,
`epsx_v423.py`); this generator moved to 971.  `roundcollide.py` resolves the
round from the module-level constant below, so the renumber is that line and
the manuscript's \input.
"""
import collections
import csv
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ v4.23: ROUND 20'S FALLBACK PATTERN, not a version pin.  This file was
# written outside the tree and read the frozen previous version; once it is
# adopted into a version directory that directory is both the input and the
# output, like every other generator here.  A bare absolute pin broke the
# build in round 20 when the predecessor was deleted, and `cleanregen.py`
# cannot see a cross-version dependency because the predecessor is always
# there while it runs.
PAPER = (HERE if os.path.exists(os.path.join(HERE, 'ledger.json'))
                else '/workspace/SETI/paper_20pc/v4.22')
ROUND = 971
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
SFX = '' if DRIVE is None else '_drive%d' % DRIVE
TRIG = 5.0
C_KMS = 299792.458

MACROS, FAIL = [], []


def m(k, v):
    assert not any(x.startswith('\\newcommand{\\%s}' % k) for x in MACROS), k
    MACROS.append('\\newcommand{\\%s}{%s}' % (k, v))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label)
    print('  %-68s %s  %s' % (label[:68], 'PASS' if ok else 'FAIL', detail))


def texval(name):
    import re
    import glob
    pat = re.compile(r'\\(?:new|renew)command\{\\%s\}\{([^}]*)\}' % name)
    for f in sorted(glob.glob(os.path.join(PAPER, 'survey_numbers*.tex'))):
        for ln in open(f):
            mm = pat.search(ln)
            if mm:
                return mm.group(1)
    raise KeyError(name)


CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))

# =====================================================================
# 1.  R2-11: THE BLOCKS WITH NO PHASE RECORD ARE A DIFFERENT ARRAY MIX
# =====================================================================
print('\n1  the blocks with no phase-stability record')
GEOM = json.load(open(os.path.join(PAPER, 'r11inputs',
                                   'window_geometry_r11.json')))['windows']
DECOR = json.load(open(os.path.join(PAPER, 'r13inputs',
                                    'decor_r13.json')))['blocks']
AMETA = json.load(open(os.path.join(PAPER, 'archive_meta_v381.json')))['ebs']
GB = collections.defaultdict(list)
for w in GEOM:
    GB[w['eb']].append(w)
EBS = sorted({r['eb'] for r in CAT})


def bmax(eb):
    v = [w['bmax'] for w in GB.get(eb, ()) if w.get('bmax')]
    return max(v) if v else None


def bsrc(eb):
    b = bmax(eb)
    return sorted({w['bmax_src'] for w in GB.get(eb, ())
                   if w.get('bmax') == b})[0] if b else None


def array(eb):
    """The array, from the antenna counts the archive metadata reads out of
    the ASDM -- never from the stored beam width, which is 1.22 lambda/12 m
    for every window the search stored."""
    a = AMETA.get(eb, {}).get('array')
    if a in ('7m', '12m'):
        return a
    d = max((w['dish_m'] for w in GB.get(eb, ()) if w.get('dish_m')),
            default=None)
    return None if d is None else ('7m' if d < 10 else '12m')


MEAS = [e for e in EBS if e in DECOR]
UNM = [e for e in EBS if e not in DECOR]
BL_M = sorted(bmax(e) for e in MEAS if bmax(e))
BL_U = sorted(bmax(e) for e in UNM if bmax(e))
if DRIVE == 1:                     # B1: a set with no baseline difference
    BL_U = BL_M
ck('B1 the published median longest baseline of the unrecorded blocks is '
   'reproduced, so the coincidence with the block count is a coincidence '
   'and not a substitution',
   '%.0f' % st.median(BL_U) == texval('RpDecBlUn')
   and '%.0f' % st.median(BL_M) == texval('RpDecBlMeas')
   and len(MEAS) == int(texval('SensDecorNBlk'))
   and len(UNM) == int(texval('RpDecNUn')),
   '%.1f m over %d of %d unrecorded against a published %s; %.1f m over %d '
   'recorded against %s'
   % (st.median(BL_U), len(BL_U), len(UNM), texval('RpDecBlUn'),
      st.median(BL_M), len(BL_M), texval('RpDecBlMeas')))
# ★ THE MEDIAN DESCRIBES NO BLOCK IN THE SET.  Measure that rather than
# assert it: the two modes are the two arrays, and the median sits between.
BY = {}
for tag, ebs in (('meas', MEAS), ('unm', UNM)):
    for a in ('7m', '12m'):
        v = sorted(bmax(e) for e in ebs if bmax(e) and array(e) == a)
        BY[(tag, a)] = v
# ★ THE MEDIAN IS A MIX STATISTIC, NOT A BASELINE.  The set is bimodal --
# an ACA mode and a 12 m mode nearly an order of magnitude apart -- so the
# median lands wherever the 50th centile of the MIX falls.  Measure how
# unstable that is: how few blocks have to change array before the published
# median moves from one mode to the other.
_u7 = sorted(BY[('unm', '7m')])
_u12 = sorted(BY[('unm', '12m')])
MODE_LO, MODE_HI = st.median(_u7), st.median(_u12)
GAP_LO, GAP_HI = max(_u7), min(_u12)
NSWING = 0
for k in range(0, len(_u12) + 1):
    # k of the 12 m blocks reclassified: the same n, a different mix
    cand = sorted(_u7 + [MODE_LO] * k + _u12[k:])
    if st.median(cand) < GAP_HI:
        NSWING = k
        break
if DRIVE == 2:                     # B2: a unimodal distribution
    GAP_HI, NSWING = GAP_LO * 1.05, len(_u12)
ck('B2 the set is bimodal and the published median is a property of the mix '
   'rather than of any block: it sits a few blocks from the other mode, and '
   'a swing of that few moves it by a factor of several',
   GAP_HI / GAP_LO > 3.0 and NSWING <= 8
   and st.median(BL_U) / GAP_LO > 3.0,
   'modes at %.0f m (n=%d) and %.0f m (n=%d), nothing between %.0f and '
   '%.0f m; %d blocks of mix move the median from %.0f m to below %.0f m'
   % (MODE_LO, len(_u7), MODE_HI, len(_u12), GAP_LO, GAP_HI, NSWING,
      st.median(BL_U), GAP_HI))
F12_U = len(BY[('unm', '12m')]) / float(len(BL_U))
F12_M = len(BY[('meas', '12m')]) / float(len(BL_M))
if DRIVE == 3:                     # B3: the same mix in both sets
    F12_U = F12_M
ck('B3 the real difference is the share of 12 m blocks, and within each '
   'array the two sets are not distinguishable',
   F12_U > 1.5 * F12_M
   and abs(st.median(BY[('unm', '7m')]) - st.median(BY[('meas', '7m')])) < 5
   and abs(st.median(BY[('unm', '12m')])
           / st.median(BY[('meas', '12m')]) - 1.0) < 0.15,
   '12 m share %.0f per cent against %.0f; 7 m medians %.0f/%.0f m; 12 m '
   'medians %.0f/%.0f m'
   % (100 * F12_U, 100 * F12_M, st.median(BY[('unm', '7m')]),
      st.median(BY[('meas', '7m')]), st.median(BY[('unm', '12m')]),
      st.median(BY[('meas', '12m')])))
# ★ THE BASELINES THEMSELVES, CROSS-CHECKED.  The measurement sets are gone,
# so the only independent witness is the archive's own quoted angular
# resolution.  54 of the unrecorded blocks' baselines were DERIVED from it as
# 1.22 lambda / theta; calibrate that constant on the 12 m blocks whose
# baselines come from their own data instead.
K = collections.defaultdict(list)
for e in EBS:
    b, s, a = bmax(e), bsrc(e), array(e)
    res = AMETA.get(e, {}).get('s_resolution_arcsec')
    if not (b and res and a):
        continue
    f = st.median([w['fmed_GHz'] for w in GB[e] if w.get('fmed_GHz')])
    K[(a, s)].append(res / 206265.0 * b / (C_KMS * 1e-6 / f))
K_LOG = st.median(K[('12m', 'log')])
K_OBS = st.median(K[('12m', 'obscore')])
if DRIVE == 4:                     # B4: a conversion the data do not support
    K_LOG = 2.0 * K_OBS
ck('B4 and the archive-derived baselines use a conversion the blocks '
   'measured from their own data confirm, so the long-baseline set is not '
   'an artefact of the fallback',
   abs(K_LOG / K_OBS - 1.0) < 0.10,
   'k = %.3f over %d measured against %.3f assumed on %d derived'
   % (K_LOG, len(K[('12m', 'log')]), K_OBS, len(K[('12m', 'obscore')])))
NO_BL = [e for e in UNM if not bmax(e)]
m('NbDecNUnBl', '%d' % len(BL_U))
m('NbDecNUnNoBl', '%d' % len(NO_BL))
m('NbDecPctTwelveUn', '%.0f' % (100 * F12_U))
m('NbDecPctTwelveMeas', '%.0f' % (100 * F12_M))
m('NbDecBlSevenUn', '%.0f' % st.median(BY[('unm', '7m')]))
m('NbDecBlSevenMeas', '%.0f' % st.median(BY[('meas', '7m')]))
m('NbDecBlTwelveUn', '%.0f' % st.median(BY[('unm', '12m')]))
m('NbDecBlTwelveMeas', '%.0f' % st.median(BY[('meas', '12m')]))
m('NbDecNTwelveUn', '%d' % len(BY[('unm', '12m')]))
m('NbDecNTwelveMeas', '%d' % len(BY[('meas', '12m')]))
m('NbDecSwing', '%d' % NSWING)
m('NbDecGapLo', '%.0f' % GAP_LO)
m('NbDecGapHi', '%.0f' % GAP_HI)

# =====================================================================
# 2.  R2-12(a): ONE MEDIAN CONTROL STATISTIC
# =====================================================================
print('\n2  the median of a window\'s own control ensemble')
sys.path.insert(0, PAPER)
import dqflag                                             # noqa: E402
DQ = dqflag._load(PAPER)
EXP = json.load(open(os.path.join(PAPER, 'corrected_export_v399.json')))
CM = [float(x['ctrl_med']) for x in EXP['rows']
      if x.get('ctrl_med') is not None]
OWN = DQ['survey_median']
FIELDS = st.median(CM)
if DRIVE == 5:                     # B5: two populations that do agree
    FIELDS = OWN
# ★★★★ v4.26, Ruling 7.  B5 WAS FAILING ON THE PUSHED v4.25, AND THE DEFECT
# WAS IN THE CHECK, NOT ON THE PAGE.  It read the row-field median out of
# `\BdSurvCtrlMed` -- but `fields_v404.py` re-pointed that name at the
# OWNER's value when it decided (correctly, in its own comment) that "the
# owner of the predicate is the one to publish the number", and kept the
# row-field median beside it as `\BdSurvCtrlMedRows`.  B5 was never
# re-pointed with it, so it compared 2.7535 with a macro that now carries
# 2.7431 and reported a wrong digit where there is none: Sec. 5.3's sentence
# is about "a window's own control ensemble ... across the survey", which is
# the 1,663-window stored ensemble, and 2.74 is that population's median.
# ★ Measured both ways before changing anything: 2.7535 over the 1,476 rows
# carrying `ctrl_med`, 2.7431 over the 1,663 windows with a stored ensemble.
# What the check should pin -- and now does -- is that EACH population's
# value is published under its own name, that the two names are not the same
# number, and that the macro the prose cites is the owner's.
_PROSE5 = open(os.path.join(PAPER, 'sections', '05_results.tex')).read()
ck('B5 the two published values are the same quantity over two different '
   'populations, the difference is the population and not the arithmetic, '
   'each is published under its own name, and the one the results section '
   'cites is the owner of the data-quality predicate',
   '%.2f' % FIELDS == texval('BdSurvCtrlMedRows')
   and '%.2f' % OWN == texval('BdSurvCtrlMed')
   and '%.2f' % OWN == texval('DqSurvMed')
   and len(CM) != len(DQ['ringmed'])
   and '\\BdSurvCtrlMed{}' in _PROSE5
   and '\\BdSurvCtrlMedRows' not in _PROSE5,
   '%.4f over %d rows carrying ctrl_med (published %s) against %.4f over '
   '%d windows with a stored ensemble (published %s, and %s as the survey '
   'median of the quality rule); the results section cites %s'
   % (FIELDS, len(CM), texval('BdSurvCtrlMedRows'), OWN, len(DQ['ringmed']),
      texval('BdSurvCtrlMed'), texval('DqSurvMed'),
      'the owner' if '\\BdSurvCtrlMed{}' in _PROSE5 else 'the row field'))
_nwin = int(texval('NWindows').replace('\\,', '').replace(',', ''))
if DRIVE == 6:                     # B6: an owner that covers less
    _nwin = len(DQ['ringmed']) + 1
ck('B6 and the value to keep is the one the quality rule itself uses, which '
   'is also the one measured over every window of the census',
   len(DQ['ringmed']) == _nwin and len(CM) < _nwin,
   '%d windows in the owner against %d in the census and %d carrying '
   'ctrl_med' % (len(DQ['ringmed']), _nwin, len(CM)))
m('NbCtrlMedOne', '%.2f' % OWN)
m('NbCtrlMedN', '%d' % len(DQ['ringmed']))
m('NbCtrlMedDropped', '%d' % (_nwin - len(CM)))

# =====================================================================
# 3.  R2-12(b): THE PREDICTED-CELL OFFSET, IN ITS TWO UNITS
# =====================================================================
print('\n3  the predicted-cell offset')
LR = json.load(open(os.path.join(PAPER, 'linerecur_r20.json')))
CTL = [v for v in LR['table_d2'].values() if v['verdict'] == 'recovered']
DC = [v['dchan'] for v in CTL if v['dchan'] is not None]
DK = [v['dkms'] for v in CTL if v['dchan'] is not None]
DC_TR = [v['dchan'] for v in CTL
         if v['dchan'] is not None and v['T_rep'] is not None
         and v['T_rep'] >= TRIG]
SIGNED = st.median(DC)
ABSMED = st.median([abs(x) for x in DC])
KMSMED = st.median([abs(x) for x in DK])
if DRIVE == 11:                    # B8: a column in the wrong unit
    KMSMED = ABSMED
if DRIVE == 7:                     # B7: a signed median that is not zero
    SIGNED = 0.5
ck('B7 the offset column is centred on zero and its typical size is a '
   'fraction of a channel, while its largest entry is tens of channels, so '
   'the median and the maximum are both needed',
   abs(SIGNED) < 0.05 and ABSMED < 0.10 and max(abs(x) for x in DC) > 10,
   'signed median %+.3f, absolute median %.3f, largest %.2f channels over '
   '%d readings' % (SIGNED, ABSMED, max(abs(x) for x in DC), len(DC)))
ck('B8 and the same column in velocity agrees with the registration '
   'residual the text quotes, so the two numbers are one measurement in two '
   'units and not a contradiction',
   abs(KMSMED - float(texval('RgCenMedKms'))) < 0.02
   and '%.2f' % KMSMED == texval('RgOffMedKms'),
   'median |offset| %.4f km/s against a published %s in the table and %s '
   'as the residual' % (KMSMED, texval('RgOffMedKms'),
                        texval('RgCenMedKms')))
# a signed median that rounds to zero must print as zero, not as -0.00
m('NbDcSigned', '%.2f' % (SIGNED if abs(round(SIGNED, 2)) > 0 else 0.0))
m('NbDcAbs', '%.2f' % ABSMED)
m('NbDcAbsKms', '%.2f' % KMSMED)
m('NbDcN', '%d' % len(DC))
m('NbDcNTrig', '%d' % len(DC_TR))
m('NbDcAbsTrig', '%.2f' % st.median([abs(x) for x in DC_TR]))

# =====================================================================
# 4.  R2-9: WHERE THE 3.9 PER CENT COMES FROM
# =====================================================================
print('\n4  the 3.9 per cent')
GAP = json.load(open(os.path.join(
    PAPER, 'pbaudit_v408', 'provenance_gap_v408.json')))
PRE = json.load(open(os.path.join(
    PAPER, 'frozen_export_v3.81_survey.json')))['rows']
REP = json.load(open(os.path.join(PAPER, 'acafull_v399.json')))
CATBY = {}
for r in CAT:
    CATBY[(r['eb'], round(float(r['rms_mJy']), 5))] = r
PAIRS = []
for g in GAP:
    pre = [r for r in PRE if r['eb'] == g['eb']
           and abs(r['rms'] - g['rms_surviving_product_mJy']) < 1e-4]
    rep = [r for r in REP if r['eb'] == g['eb']
           and abs(r['rms'] - g['rms_published_mJy']) < 1e-4]
    assert len(pre) >= 1 and len(rep) == 1, (g['flo_GHz'], len(pre), len(rep))
    cat = CATBY.get((g['eb'], round(g['rms_published_mJy'], 5)))
    PAIRS.append(dict(flo=g['flo_GHz'], pre=pre[0], rep=rep[0], gap=g,
                      cat=cat, crossing=str(g['crossing']).lower() == 'true'))
_dev_pub = max(abs(p['rep']['star_snr'] - float(p['cat']['star_snr']))
               for p in PAIRS)
_dev_pre = max(abs(p['pre']['star_snr'] - p['gap']['star_snr_published'])
               for p in PAIRS)
if DRIVE == 8:                     # B9: a published value with no record
    _dev_pub = 1.0
ck('B9 every published value of the four is reproduced by the repair record '
   'the catalogue was built from, to the precision the catalogue prints',
   _dev_pub < 5e-5,
   'worst difference %.1e over %d rows against the deposited repair record'
   % (_dev_pub, len(PAIRS)))
_pre_match = max(abs(p['pre']['rms'] - p['gap']['rms_surviving_product_mJy'])
                 for p in PAIRS)
if DRIVE == 9:                     # B10: a surviving product off both records
    _pre_match = 1.0
ck('B10 and the value the audit found on disk is the PRE-REPAIR extraction, '
   'which is itself deposited, so both sides of the comparison are on '
   'record and the difference is the repair',
   _pre_match < 1e-4 and _dev_pre > 0.01,
   'the pre-repair export reproduces the surviving product to %.1e and '
   'differs from the published value by up to %.4f' % (_pre_match, _dev_pre))
X = [p for p in PAIRS if p['crossing']]
assert len(X) == 1, len(X)
x = X[0]
PCT = 100 * abs(x['pre']['star_snr'] - x['gap']['star_snr_published']) \
    / x['gap']['star_snr_published']
RMS_PCT = 100 * (x['gap']['rms_published_mJy']
                 / x['gap']['rms_surviving_product_mJy'] - 1.0)
AMP_PCT = 100 * ((x['pre']['star_snr'] * x['pre']['rms'])
                 / (x['gap']['star_snr_published']
                    * x['gap']['rms_published_mJy']) - 1.0)
if DRIVE == 10:                    # B11: a difference that is all noise
    AMP_PCT = 0.0
ck('B11 the difference decomposes into the window noise and the recovered '
   'amplitude, and it is the amplitude that dominates, so it is not a '
   'rescaling of one quantity',
   abs(PCT - float(texval('LrSuppPct'))) < 0.05 and abs(AMP_PCT) > RMS_PCT,
   '%.2f per cent in the statistic = %.2f per cent in the noise and %.2f '
   'per cent in the amplitude' % (PCT, RMS_PCT, AMP_PCT))
CTRL_PRE, CTRL_PUB = x['pre']['ctrl_max'], float(x['cat']['ctrl_max_snr'])
if DRIVE == 12:                    # B12: a repair that left the ring alone
    CTRL_PRE = CTRL_PUB
ck('B12 and the repair moved this window\'s control ensemble, which is what '
   'it was for: no control position sits on the star\'s own synthesised '
   'lobe after it',
   CTRL_PRE > CTRL_PUB,
   'largest control %.3f before against %.3f published' % (CTRL_PRE, CTRL_PUB))
_am = AMETA.get(x['gap']['eb'], {})
if DRIVE == 15:                    # B15: a 12 m block, where the geometry
    _am = dict(array='12m', n_ant_7m=0, n_ant_12m=43)
ck('B15 and the window belongs to the compact array, which is where a '
   'control annulus placed on the nominal 12 m geometry is misplaced, so '
   'the two extractions differ for a reason the method section already '
   'states',
   _am.get('array') == '7m' and (_am.get('n_ant_7m') or 0) > 0
   and (_am.get('n_ant_12m') or 0) == 0,
   '%s, %d x 7 m and %d x 12 m antennas'
   % (_am.get('array'), _am.get('n_ant_7m') or 0, _am.get('n_ant_12m') or 0))
m('NbProvArray', _am.get('array', '?'))
m('NbProvN', '%d' % len(PAIRS))
m('NbProvPct', '%.1f' % PCT)
m('NbProvRmsPct', '%.2f' % RMS_PCT)
m('NbProvAmpPct', '%.1f' % AMP_PCT)
m('NbProvPre', '%.4f' % x['pre']['star_snr'])
m('NbProvPub', '%.4f' % x['gap']['star_snr_published'])
m('NbProvCtrlPre', '%.2f' % CTRL_PRE)
m('NbProvCtrlPub', '%.2f' % CTRL_PUB)
m('NbProvPctWorst', '%.1f' % max(
    100 * abs(p['pre']['star_snr'] - p['gap']['star_snr_published'])
    / p['gap']['star_snr_published'] for p in PAIRS))

# =====================================================================
# 5.  R2-10: WHAT THE 25 d MEASURES, AND WHY TABLE D2's SHORTEST IS 39 d
# =====================================================================
print('\n5  the closest two sessions')
EPJ = json.load(open(os.path.join(PAPER, 'epochs_v386.json')))
LED = json.load(open(os.path.join(PAPER, 'ledger.json')))['rows']
BP = [r for r in LED if 'Pic' in r['display'] and r['line'].startswith('CO')]


def _sess(eb):
    return eb.split('_')[1]


_tr = collections.defaultdict(set)
for r in BP:
    _tr[r['line']].add(_sess(r['eb']))
_mjd = collections.defaultdict(list)
for r in BP:
    if EPJ['source'].get(r['eb']) == 'block':
        _mjd[_sess(r['eb'])].append(float(EPJ['mjd'][r['eb']]))
_T = {k: min(v) for k, v in _mjd.items()}
_pairs = []
for tr, ss in sorted(_tr.items()):
    t = sorted((_T[x], x) for x in ss if x in _T)
    _pairs += [(b[0] - a[0], tr, a[1], b[1]) for a, b in zip(t, t[1:])]
_pairs.sort()
GAPMIN = _pairs[0]
if DRIVE == 13:                    # B13: a pair inside one session
    GAPMIN = (0.5,) + GAPMIN[1:]
ck('B13 the closest two sessions to recover one transition are the two the '
   'text quotes, they are a day apart or more, and the pair is a pair of '
   'SESSIONS rather than of blocks',
   '%.0f' % GAPMIN[0] == texval('CsBpCoSepMinD') and GAPMIN[0] > 1.0,
   '%.2f d between sessions %s and %s on %s, against a published %s'
   % (GAPMIN[0], GAPMIN[2], GAPMIN[3], GAPMIN[1],
      texval('CsBpCoSepMinD')))
_blk = {}
for r in BP:
    _blk.setdefault(_sess(r['eb']), []).append(r['eb'])
D2EB = {v['eb'] for v in LR['table_d2'].values()} | {
    v['recovering_eb'] for v in LR['table_d2'].values() if v['recovering_eb']}
_in = [e for s in (GAPMIN[2], GAPMIN[3]) for e in _blk[s]]
if DRIVE == 14:                    # B14: a pair the table does not hold
    D2EB = set()
ck('B14 and both of those blocks are already in the recurrence table, so '
   'the table does not contradict the sentence -- it pairs each crossing '
   'with the block whose reading it quotes, which is a different pairing',
   all(e in D2EB for e in _in),
   'blocks %s; the table pairs them at %s d instead'
   % (', '.join(sorted(set(_in))),
      ', '.join(sorted({'%d' % abs(round(_T[GAPMIN[3]] - _T[GAPMIN[2]]))}))))
m('NbSessGapD', '%.0f' % GAPMIN[0])
m('NbSessLine', GAPMIN[1].replace('-', '--'))
m('NbSessEbOne', sorted(set(_blk[GAPMIN[2]]))[0].replace('_', r'\_'))
m('NbSessEbTwo', sorted(set(_blk[GAPMIN[3]]))[0].replace('_', r'\_'))

out = dict(drive=DRIVE,
           decor=dict(n_unrecorded=len(UNM), n_with_baseline=len(BL_U),
                      med_unrecorded=st.median(BL_U),
                      med_recorded=st.median(BL_M),
                      by_array={'%s_%s' % k: dict(n=len(v),
                                                  med=st.median(v) if v
                                                  else None)
                                for k, v in BY.items()},
                      k_log=K_LOG, k_obscore=K_OBS,
                      gap=[GAP_LO, GAP_HI], swing=NSWING),
           ctrl_med=dict(owner=OWN, fields=FIELDS, n_owner=len(DQ['ringmed']),
                         n_fields=len(CM)),
           dc=dict(signed=SIGNED, absolute=ABSMED, kms=KMSMED, n=len(DC),
                   n_trigger=len(DC_TR)),
           session=dict(gap_d=GAPMIN[0], line=GAPMIN[1],
                        sessions=[GAPMIN[2], GAPMIN[3]],
                        blocks=sorted(set(_in))),
           provenance=dict(pct=PCT, rms_pct=RMS_PCT, amp_pct=AMP_PCT,
                           pre=x['pre']['star_snr'],
                           published=x['gap']['star_snr_published'],
                           ctrl_pre=CTRL_PRE, ctrl_published=CTRL_PUB),
           macros={y.split('{')[1].strip('}\\'): y.split('{')[-1].rstrip('}\n')
                   for y in MACROS})
json.dump(out, open(os.path.join(HERE, 'num_r22%s.json' % SFX), 'w'),
          indent=1, sort_keys=True)
if DRIVE is None:
    with open(os.path.join(HERE, 'survey_numbers_round%d.tex' % ROUND),
              'w') as fh:
        fh.write('%% GENERATED by num_r22.py (round %d) -- do not hand-edit.\n' % ROUND)
        fh.write('\n'.join(sorted(MACROS)) + '\n')
print('\nassertions failed: %d %s' % (len(FAIL), FAIL))
# ★★★★ v4.26, Ruling 7.  THIS SUITE USED TO COLLECT ITS FAILURES AND THEN
# EXIT 0, AND `make_all.sh` RAN IT WITH STDOUT TO /dev/null.  Three suites in
# this build were written that way -- `num_r22.py`, `r1_r22.py` and
# `recurinj_r19.py` -- so three sets of checks written to answer referee items
# could not fail the build, and one of them (num_r22's B5) had been failing on
# the shipped paper for two versions with a wrong digit on the page.  A gate
# that cannot fail is not a gate; it is a comment that takes CPU.
if FAIL:
    raise SystemExit(1)

