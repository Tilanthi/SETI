#!/usr/bin/env python3
r"""Round 270: WHICH BLOCKS THE DEEPEST LIMIT IS BUILT FROM, WHAT A VELOCITY
TOLERANCE MEANS, AND ON WHOSE CONVENTION THE FIGURE OF MERIT IS QUOTED.

Six things in one place, because each is a case of the same thing: a number
printed without the convention that gives it meaning.

1. THE DEEPEST LIMIT IN THE PAPER IS NOT COMPUTED OVER THE PRIMARY CENSUS.
   Section 3 says the primary census is the set every limit is computed over;
   the Proxima stack combines 66 execution blocks, and only 25 of them are
   census blocks.  Keyed on the execution block, the other 41 are 33 blocks
   of the archival extension -- searched with the frozen pipeline after the
   statistic and the line mask were fixed -- and 8 blocks of the
   pre-registered hold-out.  All 66 were OBSERVED inside the census blocks'
   own date range, so "observed after the census was frozen" cannot be right
   whichever way one reads it; what separates them is when they were
   searched.  A3 asserts that, so the wrong word cannot come back.

   ★ The census-only limit is computed, and it is the one the paper now
   quotes first.  It is not a model: inverse-variance combination of the
   PUBLISHED per-window noise of all 66 blocks reproduces the stack's own
   predicted noise for each of Proxima's four spectral windows to a few per
   cent (A2), so restricting the same sum to the 25 census blocks is the
   stack's own arithmetic with 41 terms removed.  The limit is shallower by
   \SzProxDeepen, which is what the archive beyond the census buys.

   ★ The three sets are separated on the EXECUTION BLOCK, never on a name,
   and every one of the 66 must own exactly one published noise record (A1).
   A name join here would be this project's commonest defect: Proxima's
   hold-out products are deposited under a Gaia directory name and its
   census rows under "Proxima Cen", and a filter on the name finds 5 of the
   8 hold-out blocks and silently loses 3.

2. A STACKING GAIN THAT DOES NOT REPRODUCE FROM sqrt(N_eff) ALONE.  The
   section quotes HD 161868 as 13 epochs for a gain of 1.15 with N_eff 1.7,
   and sqrt(1.7) = 1.29.  The missing term is the measured noise of the
   stacked spectrum: realised gain == sqrt(N_eff) / madZ identically, and
   this stack's madZ is 1.12.  A5 asserts the identity to the last printed
   digit of the published gain.  And the "+-7 per cent" the section claims
   elsewhere is a robust scatter, not a range: nine stacks in ten lie
   between \SzNoiseLo and \SzNoiseHi, so the range is published and A6
   requires it to bracket this stack.

3. A VELOCITY TOLERANCE WITH NO CONVENTION.  "The +-30 km/s reflex swing
   spans 47 channels" mixes the two: 30 km/s is 47 channels of 488 kHz, so
   the +-30 km/s swing spans twice that.  Every excursion is therefore
   emitted peak to peak as well as in amplitude, and gate P4 extends round
   140's tolerance/width pairing to the CONVENTION: a velocity tolerance may
   not be printed in a sentence that does not say whether it is an amplitude
   or a peak-to-peak span.

4. A FIGURE OF MERIT ON TWO CONVENTIONS.  The CWTFM was computed with this
   paper's EIRP_90 and compared with programmes that quote a bare detection
   threshold -- the same mismatch Figure 1(a) was rebuilt to avoid.  Both are
   now computed from the released catalogue, and A8 reproduces the published
   EIRP_90 pair exactly, so the two conventions are one calculation.

5. "277x FURTHER THAN THE NEAREST" IS THE NEAREST CLASS A STAR.  The ratio
   is measured against the nearest star of the carrier search, 3.65 pc; the
   sample's nearest star is Proxima at 1.30 pc, which is 776x.  A9 asserts
   the two differ, so the label cannot be dropped again.

6. "SEVEN ORDERS OF MAGNITUDE" IS NOT THIS SURVEY'S CHANNELISATION.  The
   catalogue's own widths span \SzChanDexSurvey orders; seven is the span
   that opens once the few-hertz channels of centimetre-band carrier
   searches are set beside them, which is what Figure 1(b) annotates.

Reads the released catalogue, the extension and hold-out exports, the stack
products, `adopted_e90.py` and the published macro layer.  Nothing is typed:
every count is len(set) and every ratio is recomputed.

    python3 stackfix_v413.py [--drive N]        N = 0..12

--drive 0 writes no production path and perturbs nothing; 1..12 break one
assertion each.  Run after stack_v408.py, stacktol_v411.py, cover_v412.py,
occurrence_v399.py and masoncmp_v401.py: all five are read back out of the
macro layer, so a disagreement is reported against the file that published it.
"""
import collections
import csv
import datetime
import glob
import json
import math
import os
import re
import statistics as st
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'stack_v408')
ROUND = 270

# D36: a test must never write to a path production reads.  The suffix
# follows the FLAG, not the perturbation.
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

C_KMS = 299792.458
CO21_HZ = 230.5380000e9             # the reference line, as in stack_v408.py

# --------------------------------------------------------------- macro layer
_VALS = {}
for _f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
    if '_drive' in os.path.basename(_f):
        continue
    # The value may itself contain braces -- `1.3\times10^{4}` is the common
    # shape -- so `[^}]*` truncates it at the first closing brace and every
    # exponent silently loses its digits.  One balanced level is enough for
    # every macro in this tree and is asserted on by A8.
    for _n, _v in re.findall(
            r'\\(?:new|renew|provide)command\*?\{\\([A-Za-z]+)\}'
            r'\{((?:[^{}]|\{[^{}]*\})*)\}',
            open(_f, encoding='utf8', errors='ignore').read()):
        if _v.strip():
            _VALS[_n] = _v.strip()


def texval(name):
    if name not in _VALS:
        raise SystemExit('stackfix_v413: macro \\%s is not published' % name)
    return _VALS[name]


def texnum(name):
    return float(re.sub(r'[^0-9.eE+-]', '', texval(name)
                        .replace(r'\times10^{', 'e')
                        .replace(r'\times 10^{', 'e')))


def texround(name):
    """(value, half a unit in the macro's own last printed place).  A
    published figure of merit is rounded to two significant figures, so
    "reproduces it" means inside its own rounding and not inside a
    percentage of my choosing."""
    t = texval(name).replace(' ', '')
    mm = re.match(r'([-\d.]+)\\times10\^\{(-?\d+)\}$', t)
    if not mm:
        return float(t), 0.0
    mant, ex = mm.group(1), int(mm.group(2))
    dp = len(mant.split('.')[1]) if '.' in mant else 0
    return float(mant) * 10.0 ** ex, 0.5 * 10.0 ** (ex - dp)


def sci(x, nd=2):
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (nd - 1, x / 10.0 ** e, e)


def iso(mjd):
    return (datetime.date(1858, 11, 17)
            + datetime.timedelta(days=mjd)).isoformat()


# ------------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXT = json.load(open(os.path.join(HERE, 'export_extension.json')))['rows']
HOLD = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
WIN = {w['path']: w for w in json.load(open(os.path.join(DATA,
                                                         'windows.json')))}
GRP = json.load(open(os.path.join(DATA, 'groups3.json')))
RES = [json.loads(_l) for _l in open(os.path.join(DATA, 'stack6_result.jsonl'))
       if 'err' not in _l]

fail = []


def ck(name, ok, detail=''):
    print('  %-4s %s\n       %s' % ('PASS' if ok else 'FAIL', name, detail))
    if not ok:
        fail.append(name.split()[0])


# ======================================================================
# 1.  THE DEEPEST STACKED LIMIT: WHICH BLOCKS, AND THE CENSUS-ONLY VALUE
# ======================================================================
DEEP = min(RES, key=lambda r: r['eirp_stack_W'])
STAR = DEEP['skey']

# One published noise record per (execution block, spectral window), from the
# three deposits that between them cover every searched block.  The window is
# keyed on min/max of its own edge pair: the extension and hold-out exports
# carry descending windows with flo > fhi.
NOISE = collections.defaultdict(list)
for r in CAT:
    if r['star_name'] == STAR:
        a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
        NOISE[r['eb']].append(('census', min(a, b), max(a, b),
                               float(r['rms_mJy'])))
for tag, src in (('extension', EXT), ('holdout', HOLD)):
    for r in src:
        if r['star_name'] == STAR:
            a, b = r['flo'], r['fhi']
            NOISE[r['eb']].append((tag, min(a, b), max(a, b), r['rms']))

# The stacked groups of this star, each matched to the group record that
# supplied its paths.  The group key is the star, the epoch count and the
# stellar-frame window; the result record is trimmed, so the nearest window
# centre is the join and the count of matched epochs is asserted below.
GROUPS = [g for g in GRP if g['skey'] == STAR]


def blocks_of(res):
    g = min((x for x in GROUPS if x['n_win'] == res['N']),
            key=lambda x: abs(x['sf_common_lo'] - res['sf_lo']))
    return [WIN[p]['block'] for p in g['paths']], g


def noise_of(res, blks):
    """The published noise of each of a group's blocks, in that group's own
    window.  Returns {eb: (provenance, rms)} and must be complete."""
    mid = 0.5 * (res['sf_lo'] + res['sf_hi']) / 1e9
    out, amb = {}, []
    for b in blks:
        hit = [x for x in NOISE.get(b, []) if abs(0.5 * (x[1] + x[2]) - mid)
               < 1.2]
        if len(hit) != 1:
            amb.append((b, len(hit)))
        else:
            out[b] = (hit[0][0], hit[0][3])
    return out, amb


DBLK, DGRP = blocks_of(DEEP)
DN, DAMB = noise_of(DEEP, DBLK)
PROV = collections.Counter(v[0] for v in DN.values())
N_CEN = PROV['census']
N_EXT = PROV['extension']
N_HOLD = PROV['holdout']

# The inverse-variance identity, checked on every one of this star's groups
# before it is used on a subset of one of them.
IVAR = []
for res in RES:
    if res['skey'] != STAR:
        continue
    blks, _g = blocks_of(res)
    nn, _amb = noise_of(res, blks)
    if _amb or len(nn) != res['N']:
        continue
    s_all = sum(v[1] ** -2.0 for v in nn.values()) ** -0.5
    IVAR.append((res, nn, s_all / res['sigma_stack_pred_mjy']))
IVAR_WORST = max(abs(x[2] - 1.0) for x in IVAR)

S_ALL = sum(v[1] ** -2.0 for v in DN.values()) ** -0.5
S_CEN = sum(v[1] ** -2.0 for v in DN.values()
            if v[0] == 'census') ** -0.5
DEEPEN = S_CEN / S_ALL
E_FULL = texnum('StkProxEirpCal')
E_CEN = E_FULL * DEEPEN

# Observation dates, so "observed after the census was frozen" can be tested
# rather than repeated.  ★ The range to test against is the WHOLE census's,
# not this star's: freezing the census is one survey-wide act, and a block
# observed before the last census observation cannot have been observed after
# it.  Tested against the star's own blocks first, this clause failed on one
# block observed later the same day as the star's last census block -- a true
# statement about that star and the wrong question.
MJD = {}
for p in DGRP['paths']:
    MJD[WIN[p]['block']] = WIN[p]['mjd']
CEN_ALL = [w['mjd'] for w in WIN.values()
           if w['block'] in {r['eb'] for r in CAT}]
CEN_MJD = [MJD[b] for b, v in DN.items() if v[0] == 'census']
OTH_MJD = [MJD[b] for b, v in DN.items() if v[0] != 'census']
OUTSIDE = [b for b, v in DN.items() if v[0] != 'census'
           and not (min(CEN_ALL) <= MJD[b] <= max(CEN_ALL))]

# ★ The name join this must not be: how many hold-out blocks a filter on the
#   star's catalogue name would find, against how many there are.
BY_NAME = {w['block'] for w in WIN.values() if STAR.lower()
           in w['star'].lower()}
HOLD_BY_NAME = len([b for b, v in DN.items()
                    if v[0] == 'holdout' and b in BY_NAME])

print('the deepest stacked limit: %s, %d blocks in the stellar-frame window '
      '%.3f-%.3f GHz' % (STAR, DEEP['N'], DEEP['sf_lo'] / 1e9,
                         DEEP['sf_hi'] / 1e9))
print('  provenance, keyed on execution block: %d census + %d extension + '
      '%d hold-out' % (N_CEN, N_EXT, N_HOLD))
print('  observed: census %s..%s, the rest %s..%s'
      % (iso(min(CEN_MJD)), iso(max(CEN_MJD)), iso(min(OTH_MJD)),
         iso(max(OTH_MJD))))
print('  inverse-variance noise: all %.5f mJy, census-only %.5f mJy = x%.4f'
      % (S_ALL, S_CEN, DEEPEN))
print('  EIRP_90: full stack %.4g W, census-only %.4g W' % (E_FULL, E_CEN))

# ======================================================================
# 2.  THE GAIN THAT NEEDS ITS NOISE TERM
# ======================================================================
WORST = min((r for r in RES if r['N'] >= 8),
            key=lambda r: r['gain_real_vs_best'])
W_SQ = WORST['sqrt_n_eff']
W_MZ = WORST['madZ']
INV = np.array([1.0 / r['madZ'] for r in RES])
N_LO, N_HI = float(np.percentile(INV, 5)), float(np.percentile(INV, 95))
SCAT = texnum('StkMadZScatterPct') / 100.0

print('\nthe stack the section names as the counter-example: %s, %d epochs'
      % (WORST['star'], WORST['N']))
print('  N_eff %.4f -> sqrt %.4f ; measured noise %.4f x prediction ; '
      'gain %.4f' % (WORST['n_eff'], W_SQ, W_MZ, WORST['gain_real_vs_best']))
print('  1/madZ over %d groups: median %.4f, 5-95 per cent %.3f-%.3f, '
      'robust scatter %.0f per cent'
      % (len(RES), float(np.median(INV)), N_LO, N_HI, 100 * SCAT))

# ======================================================================
# 3.  THE REFLEX EXCURSION, IN BOTH CONVENTIONS
# ======================================================================
A_MAX = max(float(r['chanw_Hz']) for r in CAT if r['search_class'] == 'A')
B_MIN = min(float(r['chanw_Hz']) for r in CAT if r['search_class'] == 'B')
_fine = [r['chanw'] for r in RES if r['chanw'] <= A_MAX]
_coarse = [r['chanw'] for r in RES if r['chanw'] >= B_MIN]
CH_FINE = float(max(set(_fine), key=_fine.count))
CH_COARSE = float(max(set(_coarse), key=_coarse.count))
AMP_KMS = texnum('StkReflexAmpKms')             # the published amplitude
PP_KMS = 2.0 * AMP_KMS
PP_FINE = PP_KMS / C_KMS * CO21_HZ / CH_FINE
PP_COARSE = PP_KMS / C_KMS * CO21_HZ / CH_COARSE
AMP_FINE = PP_FINE / 2.0

print('\nthe reflex excursion of a short-period giant')
print('  amplitude %.0f km/s = %.2f channels of %.3f kHz; peak to peak '
      '%.0f km/s = %.2f channels' % (AMP_KMS, AMP_FINE, CH_FINE / 1e3,
                                     PP_KMS, PP_FINE))
print('  peak to peak in %.3f MHz channels: %.2f' % (CH_COARSE / 1e6,
                                                     PP_COARSE))

# ======================================================================
# 4.  THE FIGURE OF MERIT, ON BOTH CONVENTIONS
# ======================================================================
sys.path.insert(0, HERE)
import adopted_e90 as _ae                                   # noqa: E402

A = [r for r in CAT if r['search_class'] == 'A']
E90 = _ae.per_window(CAT, HERE)


def union(iv):
    iv = sorted((min(a, b), max(a, b)) for a, b in iv)
    tot, clo, chi = 0.0, iv[0][0], iv[0][1]
    for a, b in iv[1:]:
        if a > chi:
            tot += chi - clo
            clo, chi = a, b
        else:
            chi = max(chi, b)
    return tot + chi - clo


_iv = [(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in A]
_lo = min(min(a, b) for a, b in _iv)
_hi = max(max(a, b) for a, b in _iv)
NUREL = union(_iv) / (0.5 * (_lo + _hi))
NSYS = len({r['system_id'] for r in A})
ZETA_AO = 1000.0 * 0.5 / 1e13       # Enriquez et al.'s normalisation


def per_system(which):
    d = {}
    for r in A:
        v = E90[id(r)] if which == 'e90' else float(r['eirp_nominal_W'])
        if v and v < d.get(r['system_id'], float('inf')):
            d[r['system_id']] = v
    return sorted(d.values())


def cwtfm(e):
    return ZETA_AO * e / (NSYS * NUREL)


BARE = per_system('bare')
ADOPT = per_system('e90')
CW_BARE_MED, CW_BARE_HI = cwtfm(st.median(BARE)), cwtfm(BARE[-1])
CW_AD_MED, CW_AD_HI = cwtfm(st.median(ADOPT)), cwtfm(ADOPT[-1])

print('\nthe figure of merit, %d systems at nu_rel %.4f' % (NSYS, NUREL))
print('  bare 5-sigma threshold (the comparison programmes\' convention): '
      'median %.3g, worst %.3g' % (CW_BARE_MED, CW_BARE_HI))
print('  this paper\'s EIRP_90:                                        '
      'median %.3g, worst %.3g (published %s, %s)'
      % (CW_AD_MED, CW_AD_HI, texval('FomCwtfmMed'),
         texval('FomCwtfmWorst')))

# ======================================================================
# 5.  WHOSE "NEAREST", AND 6.  WHOSE "SEVEN ORDERS"
# ======================================================================
D_A = sorted(float(r['dist_pc']) for r in A)
D_ALL = sorted(float(r['dist_pc']) for r in CAT)
MAS_PC = texnum('MasonNearKpc') * 1e3
R_NEAR_A = MAS_PC / D_A[0]
R_NEAR_ALL = MAS_PC / D_ALL[0]
NEAR_A = sorted({r['star_name'] for r in A
                 if abs(float(r['dist_pc']) - D_A[0]) < 1e-6})
NEAR_ALL = sorted({r['star_name'] for r in CAT
                   if abs(float(r['dist_pc']) - D_ALL[0]) < 1e-6})

CW = sorted({float(r['chanw_Hz']) for r in CAT})
DEX_SURVEY = math.log10(CW[-1] / CW[0])
# The channelisation of the comparison programmes, read from the figure
# generator's own literature table rather than remembered.
_fig = open(os.path.join(HERE, 'make_fig_context_v410.py'),
            errors='ignore').read()
LIT_HZ = sorted(float(x) for x in re.findall(r'chan_Hz=([0-9.]+)', _fig))
DEX_ALL = math.log10(max(CW[-1], LIT_HZ[-1]) / min(CW[0], LIT_HZ[0]))

print('\n"the nearest": Class A %s at %.3f pc = x%.0f; the sample %s at '
      '%.3f pc = x%.0f' % (', '.join(NEAR_A), D_A[0], R_NEAR_A,
                           ', '.join(NEAR_ALL), D_ALL[0], R_NEAR_ALL))
print('channel widths: %.3f kHz to %.3f MHz = %.2f dex here; with the '
      '%.2f Hz channels of the comparison searches, %.2f dex'
      % (CW[0] / 1e3, CW[-1] / 1e6, DEX_SURVEY, LIT_HZ[0], DEX_ALL))

# ======================================================================
# P4.  A TOLERANCE MUST NAME ITS CONVENTION AS WELL AS ITS WIDTH
# ======================================================================
# Round 140 requires a velocity or drift tolerance to be printed beside the
# channel width it came from.  That stopped a tolerance standing beside the
# wrong width; it cannot stop an amplitude being printed as a span.  So each
# velocity quantity declares its convention, and the sentence must say it.
CONV = {'StkTolFineKms': 'pp',
        'StkProxTolKms': 'pp',
        'SzReflexPPChanFine': 'pp',
        'SzReflexPPChanCoarse': 'pp',
        'StkReflexAmpKms': 'pm'}
TOKEN = {'pp': re.compile(r'peak to peak'),
         'pm': re.compile(r'\\pm')}
MINE = '05b_stack.tex'
# Files I do not own whose tolerance sentence is queued for its owner.  Each
# must STILL lack its convention: once the queued text lands the entry is
# stale and has to go, which is the second half of this clause.
# ★ 2026-10-07: EMPTY, and that is the point.  Conclusion 6 now names the
# convention ("\StkProxTolKms km/s peak to peak") and quotes the census-only
# limit first, so the entry became STALE -- which this gate's own second
# clause reports and which is the signal to delete it.  A PENDING list that
# is never emptied is a whitelist.
PENDING = {}
SENT = re.compile(r'(?<!\\)\.(?:\s|$)')


def unconventional(path):
    txt = '\n'.join(l for l in open(path, errors='ignore').read().splitlines()
                    if not l.lstrip().startswith('%'))
    out = []
    for s in SENT.split(txt):
        for mac, conv in CONV.items():
            if re.search(r'\\%s(?![A-Za-z])' % mac, s) \
                    and not TOKEN[conv].search(s):
                out.append(mac)
    return sorted(set(out))


SECDIR = os.path.join(HERE, 'sections')
STATE = {f: unconventional(os.path.join(SECDIR, f))
         for f in sorted(os.listdir(SECDIR)) if f.endswith('.tex')}
if DRIVE == 11:
    STATE[MINE] = ['SzReflexPPChanFine']
if DRIVE == 12:
    # Re-arm the `stale` clause against a file that already says its
    # convention: a queue entry left behind after the text it asked for has
    # landed is exactly what that clause exists to catch, and it must fire.
    PENDING = dict(PENDING, **{MINE: 'StkTolFineKms'})
    STATE[MINE] = []


def _find_queue():
    if os.environ.get('R12_QUEUE'):
        return os.environ['R12_QUEUE']
    d, tried = HERE, []
    for _ in range(6):
        d = os.path.dirname(d)
        c = os.path.join(d, 'referee_r12', 'queue', 'QUEUE_stack.md')
        tried.append(c)
        if os.path.exists(c):
            return c
    return tried


QPATH = _find_queue()
if isinstance(QPATH, list):
    QTXT, QWHERE = '', 'NOT FOUND, looked in %s' % QPATH
else:
    QTXT, QWHERE = open(QPATH, errors='ignore').read(), QPATH
LOOSE = sorted(f for f, u in STATE.items() if u and f not in PENDING)
STALE = sorted(f for f in PENDING if not STATE.get(f))
UNQUEUED = sorted(f for f in PENDING
                  if f not in QTXT or PENDING[f] not in QTXT)

# ============================================================ assertions
print('\nassertions')

_v = (N_CEN, N_EXT, N_HOLD) if DRIVE != 1 else (N_CEN, N_EXT + 1, N_HOLD)
ck('A1 the blocks of the deepest stacked limit are split on the execution '
   'block, not on a name: census, extension and hold-out partition the '
   'published total, every block owns exactly one published noise record, '
   'and a name filter would have lost some of them',
   not DAMB and len(DN) == DEEP['N'] == int(texnum('StkProxN'))
   and sum(_v) == DEEP['N']
   and _v[0] == int(texnum('SxProxEbCensus'))
   and _v[1] + _v[2] == int(texnum('SxProxEbExt'))
   and HOLD_BY_NAME < N_HOLD,
   '%d + %d + %d = %d blocks against \\StkProxN %s; census %s, '
   'non-census %s; ambiguous %s; a name filter finds %d of %d hold-out'
   % (_v[0], _v[1], _v[2], sum(_v), texval('StkProxN'),
      texval('SxProxEbCensus'), texval('SxProxEbExt'), DAMB or 'none',
      HOLD_BY_NAME, N_HOLD))

_v = IVAR_WORST if DRIVE != 2 else 1.0
ck('A2 the census-only noise is the stack\'s own arithmetic, not a model of '
   'mine: inverse-variance combination of the published per-window noise '
   'reproduces the stack\'s predicted noise in every one of this star\'s '
   'stacked windows',
   len(IVAR) >= 4 and _v < 0.05,
   'worst departure %.2f per cent over %d groups (%s)'
   % (100 * IVAR_WORST, len(IVAR),
      ', '.join('%.3f' % x[2] for x in IVAR)))

_v = OUTSIDE if DRIVE != 3 else ['forced']
ck('A3 every non-census block was OBSERVED inside the census blocks\' own '
   'date range, so the section may not say they were observed after the '
   'census was frozen',
   not _v and len(OTH_MJD) == N_EXT + N_HOLD,
   'the census spans %s..%s and contains all %d non-census blocks (%s..%s, '
   'this star\'s census blocks %s..%s); outside %s'
   % (iso(min(CEN_ALL)), iso(max(CEN_ALL)), len(OTH_MJD), iso(min(OTH_MJD)),
      iso(max(OTH_MJD)), iso(min(CEN_MJD)), iso(max(CEN_MJD)), _v or 'none'))

_v = DEEPEN if DRIVE != 4 else 1.0
ck('A4 the census-only limit is shallower than the full stack by more than '
   'the precision it is printed to, and the two round-trip through the '
   'published deepening factor',
   _v > 1.005 and abs(E_CEN / _v - E_FULL) < 1e-6 * E_FULL,
   'census-only %.4g W = x%.4f the full stack %.4g W' % (E_CEN, DEEPEN,
                                                         E_FULL))

_v = W_SQ / W_MZ if DRIVE != 5 else W_SQ
ck('A5 the realised gain of that stack is sqrt(N_eff) divided by the '
   'measured noise of the stacked spectrum, to the last digit the section '
   'prints',
   abs(_v - texnum('StkWorstGain')) < 0.005
   and abs(WORST['gain_real_vs_best'] - W_SQ / W_MZ) < 1e-9
   and WORST['star'] == texval('StkWorstStar'),
   'sqrt(N_eff) %.4f / noise %.4f = %.4f against \\StkWorstGain %s for %s'
   % (W_SQ, W_MZ, W_SQ / W_MZ, texval('StkWorstGain'), WORST['star']))

_v = (N_LO, N_HI) if DRIVE != 6 else (0.999, 1.001)
ck('A6 the published 5-95 per cent range of the noise term brackets that '
   'stack, and is genuinely wider than the single robust scatter the '
   'section used to quote on its own',
   _v[0] <= W_MZ <= _v[1] and (_v[1] - _v[0]) > 2 * SCAT
   and _v[0] < 1.0 < _v[1],
   'range %.3f-%.3f contains %.4f; width %.3f against 2x%.2f'
   % (_v[0], _v[1], W_MZ, _v[1] - _v[0], SCAT))

_v = PP_FINE if DRIVE != 7 else AMP_FINE
ck('A7 the peak-to-peak excursion is exactly twice the amplitude in both '
   'channelisations, and the fine figure is more than ten times the coarse '
   'one, which is why neither may stand for the other',
   abs(_v / AMP_FINE - 2.0) < 1e-9
   and abs(PP_COARSE / (PP_KMS / C_KMS * CO21_HZ / CH_COARSE / 2.0) - 2.0)
   < 1e-9 and PP_FINE / PP_COARSE > 10.0,
   'amplitude %.3f ch, peak to peak %.3f ch (fine); %.3f ch (coarse); '
   'ratio %.1f' % (AMP_FINE, _v, PP_COARSE, PP_FINE / PP_COARSE))

_FM, _FW = texround('FomCwtfmMed'), texround('FomCwtfmWorst')
_v = CW_BARE_MED if DRIVE != 8 else CW_AD_MED
ck('A8 the two conventions are one calculation: the EIRP_90 branch '
   'reproduces the published figures of merit, and the bare-threshold '
   'branch -- the convention the comparison programmes use -- is the '
   'smaller of the two',
   abs(CW_AD_MED - _FM[0]) <= _FM[1]
   and abs(CW_AD_HI - _FW[0]) <= _FW[1]
   and _v < CW_AD_MED,
   'EIRP_90 %.4g / %.4g against published %s / %s (rounding %.3g / %.3g); '
   'bare %.4g / %.4g'
   % (CW_AD_MED, CW_AD_HI, texval('FomCwtfmMed'), texval('FomCwtfmWorst'),
      _FM[1], _FW[1], CW_BARE_MED, CW_BARE_HI))

_v = D_A[0] if DRIVE != 9 else D_ALL[0]
ck('A9 the published distance ratio is measured against the nearest star of '
   'the CARRIER search, and the sample contains a nearer star that is not '
   'in it, so the label cannot be dropped',
   abs(MAS_PC / _v - texnum('MasonDistRatioNear')) < 1.0
   and D_ALL[0] < D_A[0] and NEAR_A != NEAR_ALL,
   'nearest Class A %s %.3f pc -> x%.0f (published %s); nearest of all %s '
   '%.3f pc -> x%.0f' % (', '.join(NEAR_A), D_A[0], MAS_PC / D_A[0],
                         texval('MasonDistRatioNear'), ', '.join(NEAR_ALL),
                         D_ALL[0], R_NEAR_ALL))

_v = DEX_SURVEY if DRIVE != 10 else DEX_ALL
ck('A10 "about seven orders of magnitude" is the span that opens only once '
   'the comparison searches\' channels are set beside ours: this survey\'s '
   'own widths span about three, and the difference is more than three '
   'orders',
   _v < 4.0 and DEX_ALL > 6.5 and (DEX_ALL - _v) > 3.0
   and len(LIT_HZ) >= 3,
   'here %.2f dex (%.1f kHz to %.1f MHz), with the literature %.2f dex '
   '(finest %.2f Hz)' % (DEX_SURVEY, CW[0] / 1e3, CW[-1] / 1e6, DEX_ALL,
                         LIT_HZ[0]))

ck('P4 no velocity tolerance or excursion is printed in a sentence that '
   'does not say whether it is an amplitude or a peak-to-peak span; the '
   'file queued for its owner still lacks it and is still queued',
   not LOOSE and not STALE and not UNQUEUED,
   'without a convention %s | stale pending %s | pending but not queued %s '
   '| queue %s' % (LOOSE, STALE, UNQUEUED, QWHERE))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('stackfix_v413: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ------------------------------------------------------------------ macros
OUTM = []


def m(name, val):
    assert name.isalpha(), name      # a macro name may contain letters only
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUTM), \
        name
    OUTM.append('\\newcommand{\\%s}{%s}' % (name, val))


m('SzProxEbSearched', '%d' % N_EXT)
m('SzProxEbHold', '%d' % N_HOLD)
m('SzProxEirpCensus', sci(E_CEN))
m('SzProxDeepen', '%.2f' % DEEPEN)
m('SzWorstSqrtNeff', '%.2f' % W_SQ)
m('SzWorstNoise', '%.2f' % W_MZ)
m('SzNoiseLo', '%.2f' % N_LO)
m('SzNoiseHi', '%.2f' % N_HI)
m('SzReflexPPChanFine', '%.0f' % PP_FINE)
m('SzReflexPPChanCoarse', '%.1f' % PP_COARSE)
m('SzCwtfmBareMed', sci(CW_BARE_MED))
m('SzCwtfmBareWorst', sci(CW_BARE_HI))
m('SzMasonDistRatioAll', '%.0f' % R_NEAR_ALL)
m('SzChanDexSurvey', '%.1f' % DEX_SURVEY)
m('SzChanDexAll', '%.0f' % DEX_ALL)
m('SzChanFinestKHz', '%.1f' % (CW[0] / 1e3))
m('SzChanWidestMHz', '%.2f' % (CW[-1] / 1e6))
m('SzChanLitHz', '%.1f' % LIT_HZ[0])

OUT = os.path.join(HERE, 'survey_numbers_round270%s.tex' % SUF)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by stackfix_v413.py (round %d) -- do not '
             'hand-edit.\n' % ROUND)
    fh.write('\n'.join(sorted(OUTM)) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(OUT), len(OUTM)))
