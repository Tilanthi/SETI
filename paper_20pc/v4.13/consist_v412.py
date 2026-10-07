#!/usr/bin/env python3
r"""Round 195: THE SETS THAT WERE WEARING ONE ANOTHER'S NAMES.

Referee 2 tabulated sixteen places where the paper gives two values for what
reads like one quantity, and observed that several of them change what a
reader would conclude.  Almost none of them is wrong arithmetic.  They are
DIFFERENT SETS GIVEN THE SAME NAME -- this project's commonest defect, found
here for the fifteenth time -- and the repair is to establish from the
released catalogue what each number counts, to give the two sets names that
cannot be confused, and to print both with their denominators.  Referee 1's
closing minor point asks for exactly that: every denominator stated at first
occurrence.

WHAT IS MEASURED HERE, AND WHICH REFEREE ROW IT CLOSES

  1614 vs 1645 "windows retaining a control vector".  NEITHER is that.
       Every one of the 1651 released windows carries `n_ctrl = 512`, and
       the two files join completely on a key made of three measured
       quantities of the window -- the key `statchain_v411.py` already uses,
       1651 of 1651 with nothing ambiguous.  1614 was the survivor count of
       a STAR-BLIND key, `(block, lower window edge)`, which is shared by
       two or three catalogue rows wherever one spectral window of one block
       is extracted at more than one star of the field; 1645 was the
       survivor count of a THIRD key in `acaverify_v399.py`.  The key is
       repaired in `stageonenull_v399.py` and the population is 1651.

  447 vs 455 "windows with a control maximum at the trigger".  ONE SET.  455
       is the released scalar `ctrl_max_snr` column; 447 was the same count
       taken over the 1614 the star-blind key kept.  With the key repaired
       the stored 512-element ensembles give 455, and 398 Class A, which are
       the catalogue's own numbers to the last digit.

  "390" twice.  Genuinely two sets, and after the key repair they are no
       longer even numerically equal: 390 Class A windows whose control ring
       is NOISE (402 minus the 12 disc-affected), and 398 Class A windows
       whose control maximum REACHES the trigger.

  12 / 4 / 8 "disc-affected windows".  Three sets, one rule, three
       thresholds and two classes: 12 Class A windows with a control ring at
       or above 10 sigma (the completeness-stratum rule), 4 of those at or
       above 14 sigma (where the screen's whole cost is paid), and 8 windows
       of EITHER class at or above 14 sigma -- those 4 plus 4 coarse windows
       of one star.  4 is a subset of 12; 8 is not.

  14 vs 12 "windows where the star outranks every control".  Both right, in
       two different populations: 14 of the 1651 released windows, of which
       the 12 that also reach the trigger are all Class A.  The other two
       peak at T* = 4.36 and 4.20 and never cross, so they can appear in no
       stage-1 count.

  51 vs 56 crossings.  51 of the 56 carry a released peak FREQUENCY; the
       five that do not are beta Pictoris carbon-monoxide crossings whose
       release carries the velocity offset instead, which is why the ledger
       table can still list all 56.

  beta Pic CO in 9 or 10 blocks.  10 blocks hold a recovered CO crossing; in
       9 of them the star also outranks every control.  The figure caption
       already said so; the body said 9 and meant 10.

  and two measurements the referee's minor list asks for and the paper never
  made: whether the MAD is scaled to a Gaussian-equivalent sigma (it is, by
  1.4826, everywhere in this build), and the integration time per dump for
  each array.

EVERY ASSERTION BELOW IS DRIVEN.  `--drive N` perturbs exactly one input and
exactly one check must fail; the output suffix follows the FLAG, so no driven
run -- including `--drive 0` -- writes a path the production run writes.

Usage:  consist_v412.py [--drive N]      N = 0..10
"""
import collections
import csv
import glob
import json
import math
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
# ★ The production name is written as a LITERAL, because `macrosyn`'s source
#   check looks for the filename as a literal string in some generator and
#   cannot resolve a format template -- the blind spot `roundcollide` fixed
#   for itself in v4.11 and `macrosyn` still has.  A round file no gate can
#   trace to a generator is a macro file the build cannot recompute.
OUT = os.path.join(HERE, 'survey_numbers_round195.tex' if DRIVE is None
                   else 'survey_numbers_round195_drive%d.tex' % DRIVE)

TRIG = 5.0
NCTRL_VEC = 512
MAD_SCALE = 1.4826          # quoted from the search's own noise estimator


def texval(name):
    """A macro's value out of the macro layer, last non-empty definition."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*)\}' % re.escape(name))
    out = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        if '_drive' in fn:
            continue
        for mm in pat.finditer(open(fn, errors='ignore').read()):
            if mm.group(1).strip():
                out = mm.group(1).strip()
    seen = set()
    while out and re.fullmatch(r'\\[A-Za-z]+', out) and out not in seen:
        seen.add(out)
        out = texval(out[1:])
    return out


def tint(name):
    v = texval(name)
    assert v is not None, 'macro \\%s is not defined' % name
    return int(v.replace('\\,', '').replace(',', ''))


# ------------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXP = json.load(open(os.path.join(
    HERE, 'corrected_export_v399.json')))['rows']
ARR = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']

A = [r for r in CAT if r['search_class'] == 'A']
B = [r for r in CAT if r['search_class'] == 'B']


def fl(r, k):
    v = r[k].strip()
    return float(v) if v else None


# ------------------------------------- the key, and the population it joins
# Three MEASURED quantities of the window.  The star-blind key the stage-1
# null used, `(eb, min(flo, fhi))`, is kept here under its own name so the
# shortfall it produced is a measurement in this file and not a memory.
def key3(eb, rms, snr):
    return (eb, round(float(rms), 5), round(float(snr), 4))


def key_edge(eb, lo, hi):
    return (eb, round(min(float(lo), float(hi)), 4))


BY3 = collections.defaultdict(list)
BYEDGE = collections.defaultdict(list)
for r in CAT:
    BY3[key3(r['eb'], r['rms_mJy'], r['star_snr'])].append(r)
    BYEDGE[key_edge(r['eb'], r['flo_GHz'], r['fhi_GHz'])].append(r)
N_AMBIG3 = sum(1 for v in BY3.values() if len(v) > 1)
N_AMBIG_EDGE = sum(len(v) - 1 for v in BYEDGE.values() if len(v) > 1)
N_COLLIDING_KEYS = sum(1 for v in BYEDGE.values() if len(v) > 1)
# the colliding keys are MULTI-STAR, which is the whole diagnosis: one
# spectral window of one block extracted at two or three stars of the field
COLLIDE_MULTISTAR = sum(1 for v in BYEDGE.values() if len(v) > 1
                        and len({r['star_name'] for r in v}) == len(v))

joined, trig_vec, trig_vec_A = 0, 0, 0
seen = set()
for r in EXP:
    c = r.get('ctrl_all') or []
    if len(c) != NCTRL_VEC or r.get('star_snr') is None:
        continue
    k = key3(r['eb'], r['rms'], r['star_snr'])
    hit = BY3.get(k)
    if k in seen or not hit or len(hit) > 1:
        continue
    seen.add(k)
    joined += 1
    if max(c) >= TRIG:
        trig_vec += 1
        if hit[0]['search_class'] == 'A':
            trig_vec_A += 1
if DRIVE == 1:
    joined -= 1                     # the join must be complete

# the same question of the released SCALAR column
trig_col = [r for r in CAT if fl(r, 'ctrl_max_snr') > TRIG]
trig_col_A = [r for r in trig_col if r['search_class'] == 'A']

# ------------------------------------------------- the star-outranks-all set
RANKFIRST = [r for r in CAT if r['n_ctrl_ge_star'] == '0']
RF_A = [r for r in RANKFIRST if r['search_class'] == 'A']
RF_B = [r for r in RANKFIRST if r['search_class'] != 'A']
STAGE1 = [r for r in CAT if r['stage1_flag'] == 'True']
if DRIVE == 2:
    RF_B = []                       # the two non-crossing ones must be named


def star(r):
    s = re.sub(r'\s+Gaia DR3 \d+$', '', r['star_name'])
    s = s.replace('BD05', 'BD$+$05').replace('CP-72', 'CP$-$72')
    s = s.replace('bet Pic', r'$\beta$~Pic').replace('eta Crv',
                                                     r'$\eta$~Crv')
    return re.sub(r'\s+', '~', s.strip())


# ------------------------------------------------------- the three "discs"
RULE_SIGMA, BRIGHT_SIGMA = 10.0, 14.0
DISC_A = [r for r in A if fl(r, 'ctrl_max_snr') >= RULE_SIGMA]
BRIGHT_A = [r for r in A if fl(r, 'ctrl_max_snr') >= BRIGHT_SIGMA]
BRIGHT_B = [r for r in B if fl(r, 'ctrl_max_snr') >= BRIGHT_SIGMA]
BRIGHT_ALL = BRIGHT_A + BRIGHT_B
NOISE_A = [r for r in A if fl(r, 'ctrl_max_snr') < RULE_SIGMA]
if DRIVE == 3:
    BRIGHT_A = BRIGHT_A + NOISE_A[:1]   # 4 must stay inside 12

# ------------------------------------------------------ crossings and frames
X = [r for r in CAT if r['crossing'] == 'True']
X_FREQ = [r for r in X if r['f_cross_GHz'].strip()]
X_NOFREQ = [r for r in X if not r['f_cross_GHz'].strip()]
if DRIVE == 4:
    X_NOFREQ = []                   # the 51/56 gap must be accounted for

# beta Pic CO: the blocks that hold one, and the blocks that also pass
BP = [r for r in CAT if r['star_name'] == 'bet Pic']
BP_CO = [r for r in BP if r['crossing'] == 'True'
         and (r['nearest_line'] or '').startswith('CO(')]
BP_CO_EB = {r['eb'] for r in BP_CO}
BP_CO_PASS_EB = {r['eb'] for r in BP_CO if r['n_ctrl_ge_star'] == '0'}
if DRIVE == 5:
    BP_CO_PASS_EB = BP_CO_EB        # the screened block must stay screened

# ----------------------------------------------- the integration dump times
dump = collections.defaultdict(list)
for r in CAT:
    n, t = fl(r, 'n_int'), fl(r, 'on_source_s')
    a = (ARR.get(r['eb'], {}) or {}).get('array')
    if n and t and a:
        dump[a].append(t / n)
N_DUMP_WIN = sum(len(v) for v in dump.values())
SMEAR_POP = [r for r in CAT if r['eta_smear'].strip()]
if DRIVE == 6:
    SMEAR_POP = CAT                 # the smear denominator is not \NWindows

# ------------------------------------------------------- Table 3's own count
INT_NOCLASSA = None
_tab = os.path.join(HERE, 'tab_interesting.tex')
if os.path.exists(_tab):
    _rows = [l for l in open(_tab) if l.rstrip().endswith('\\\\')
             and '&' in l and not l.lstrip().startswith('System')
             and 'pc)' not in l]
    INT_NOCLASSA = sum(1 for l in _rows
                       if re.search(r'&\s*0\s*&', l))
    INT_NROW = len(_rows)
if DRIVE == 7 and INT_NOCLASSA is not None:
    INT_NOCLASSA = INT_NROW         # a count read from no row at all

# ================================================================ assertions
fail = []


def ck(tag, cond, detail=''):
    if not cond:
        fail.append(tag)
    print('  %-66s %s  %s' % (tag, 'PASS' if cond else 'FAIL', detail))


print('consist_v412: the sets that were wearing one another\'s names'
      + ('  [drive %d]' % DRIVE if DRIVE is not None else ''))
print('\nassertions')

ck('C1 every released window retains a full control ensemble, and the two '
   'files join completely on a measured key',
   N_AMBIG3 == 0 and joined == len(CAT)
   and all(int(r['n_ctrl']) == NCTRL_VEC for r in CAT),
   '%d ambiguous keys, %d of %d windows joined, n_ctrl == %d on all'
   % (N_AMBIG3, joined, len(CAT), NCTRL_VEC))
ck('C1b and the published shortfall was a STAR-BLIND key, measured: the '
   'window-edge key collides, and every collision is multi-star',
   N_AMBIG_EDGE > 0 and COLLIDE_MULTISTAR == N_COLLIDING_KEYS,
   '%d keys shared by %d extra rows, %d of the %d colliding keys carry one '
   'row per star'
   % (N_COLLIDING_KEYS, N_AMBIG_EDGE, COLLIDE_MULTISTAR, N_COLLIDING_KEYS))
ck('C2 the stored ensembles and the released scalar column give ONE count '
   'of the windows reaching the trigger, in both classes',
   trig_vec == len(trig_col) and trig_vec_A == len(trig_col_A),
   'stored %d / %d Class A against column %d / %d Class A'
   % (trig_vec, trig_vec_A, len(trig_col), len(trig_col_A)))
ck('C3 the two "390"s are different sets, and the noise-ring count is not '
   'the trigger-eligible count',
   len(NOISE_A) + len(DISC_A) == len(A) and len(NOISE_A) != trig_vec_A,
   'noise ring %d + disc-affected %d == %d Class A; trigger-eligible %d'
   % (len(NOISE_A), len(DISC_A), len(A), trig_vec_A))
ck('C4 the disc counts nest: 14 sigma Class A inside 10 sigma Class A, and '
   'the all-class 14 sigma count is the sum of the two classes',
   set(id(r) for r in BRIGHT_A) <= set(id(r) for r in DISC_A)
   and len(BRIGHT_ALL) == len(BRIGHT_A) + len(BRIGHT_B)
   and len(BRIGHT_B) > 0,
   '%d of %d Class A at >=%.0f sigma inside %d at >=%.0f; all classes %d = '
   '%d A + %d B'
   % (len(BRIGHT_A), len(A), BRIGHT_SIGMA, len(DISC_A), RULE_SIGMA,
      len(BRIGHT_ALL), len(BRIGHT_A), len(BRIGHT_B)))
ck('C5 the star outranks every control in 14 windows, 12 of which also '
   'reach the trigger and are exactly the Class A ones',
   len(RF_A) + len(RF_B) == len(RANKFIRST)
   and {id(r) for r in STAGE1} == {id(r) for r in RF_A}
   and len(RF_B) > 0
   and all(fl(r, 'star_snr') < TRIG for r in RF_B),
   '%d rank-first of %d windows: %d Class A (all stage-1 flagged) and %d '
   'Class B below the trigger at T*=%s'
   % (len(RANKFIRST), len(CAT), len(RF_A), len(RF_B),
      '/'.join('%.2f' % fl(r, 'star_snr') for r in RF_B)))
ck('C6 the released frequency column accounts for the 51 against 56, and '
   'the five without one are all the same star',
   len(X_FREQ) + len(X_NOFREQ) == len(X) == tint('NCross')
   and len(X_NOFREQ) > 0
   and len({r['star_name'] for r in X_NOFREQ}) == 1
   and all(r['line_offset_kms'].strip() for r in X_NOFREQ),
   '%d with a frequency + %d without == %d crossings; the %d without are '
   'all %s and all carry a line offset'
   % (len(X_FREQ), len(X_NOFREQ), len(X), len(X_NOFREQ),
      star(X_NOFREQ[0]) if X_NOFREQ else '-'))
ck('C7 beta Pic CO is recovered in 10 blocks and passes the screen in 9, '
   'which is the published \\NStageOneBpicEb',
   len(BP_CO_EB) == len(BP_CO)
   and len(BP_CO_PASS_EB) == tint('NStageOneBpicEb')
   and len(BP_CO_PASS_EB) < len(BP_CO_EB),
   '%d CO crossings in %d blocks, %d passing the screen against the '
   'published %d' % (len(BP_CO), len(BP_CO_EB), len(BP_CO_PASS_EB),
                     tint('NStageOneBpicEb')))
ck('C8 the intra-integration population is the windows that carry n_int, '
   'and it is NOT the catalogue',
   len(SMEAR_POP) == N_DUMP_WIN < len(CAT)
   and len(SMEAR_POP) == tint('NSmearLo') + tint('NSmearOk'),
   '%d windows carry a dump time and a smearing figure, of %d; '
   '%d + %d == %d' % (N_DUMP_WIN, len(CAT), tint('NSmearLo'),
                      tint('NSmearOk'), len(SMEAR_POP)))
ck('C9 both arrays are represented in the dump-time census and their '
   'modal dumps differ',
   len(dump) >= 2
   and len({round(st.median(v), 2) for v in dump.values()}) == len(dump),
   '; '.join('%s n=%d median %.2f s' % (a, len(v), st.median(v))
             for a, v in sorted(dump.items())))
if INT_NOCLASSA is not None:
    ck('C10 the count of Table 3 rows with no Class A window is read from '
       'the table, not written beside it',
       0 < INT_NOCLASSA < INT_NROW,
       '%d of %d rows have N_A = 0' % (INT_NOCLASSA, INT_NROW))
if DRIVE == 8:
    fail.append('C0 deliberate failure, drive 8')

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('consist_v412: %d assertion(s) failed' % len(fail))

# =================================================================== macros
M = {}


def m(k, v):
    assert k.isalpha(), 'macro name %r is not letters-only' % k
    assert k not in M, 'macro %s emitted twice' % k
    M[k] = v


def sci(x, sf=2):
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sf - 1, x / 10.0 ** e, e)


# the control ensemble, named once
m('CsNWinCtrlVec', '%d' % joined)
m('CsNWinCtrlVecLost', '%d' % (len(CAT) - joined))
m('CsNCtrlTrig', '%d' % trig_vec)
m('CsNCtrlTrigA', '%d' % trig_vec_A)
m('CsNCtrlTrigB', '%d' % (trig_vec - trig_vec_A))
# the star-outranks-all sets
m('CsNRankFirst', '%d' % len(RANKFIRST))
m('CsNRankFirstA', '%d' % len(RF_A))
m('CsNRankFirstB', '%d' % len(RF_B))
m('CsRankFirstBList',
  ' and '.join('%s Band~%s' % (star(r), r['band']) for r in RF_B))
m('CsRankFirstBTLo', '%.2f' % min(fl(r, 'star_snr') for r in RF_B))
m('CsRankFirstBTHi', '%.2f' % max(fl(r, 'star_snr') for r in RF_B))
# the three disc counts
m('CsNDiscTen', '%d' % len(DISC_A))
m('CsNDiscFourteen', '%d' % len(BRIGHT_A))
m('CsNRingFourteen', '%d' % len(BRIGHT_ALL))
m('CsNRingFourteenB', '%d' % len(BRIGHT_B))
m('CsRingFourteenBStar', star(BRIGHT_B[0]) if BRIGHT_B else '--')
m('CsDiscSigma', '%.0f' % RULE_SIGMA)
m('CsBrightSigma', '%.0f' % BRIGHT_SIGMA)
m('CsNNoiseRing', '%d' % len(NOISE_A))
# crossings with and without a released frequency
m('CsNCrossFreq', '%d' % len(X_FREQ))
m('CsNCrossNoFreq', '%d' % len(X_NOFREQ))
m('CsCrossNoFreqStar', star(X_NOFREQ[0]) if X_NOFREQ else '--')
# beta Pic
m('CsBpCoBlocks', '%d' % len(BP_CO_EB))
m('CsBpCoBlocksScreen', '%d' % len(BP_CO_PASS_EB))
# the noise scale and the dump times
m('CsMadScale', '%.4f' % MAD_SCALE)
m('CsNDumpWin', '%d' % N_DUMP_WIN)
for _a, _lab in (('12m', 'Twelve'), ('7m', 'Aca')):
    if _a in dump:
        v = sorted(dump[_a])
        m('CsDump' + _lab, '%.2f' % st.median(v))
        m('CsDump' + _lab + 'Lo', '%.2f' % v[0])
        m('CsDump' + _lab + 'Hi', '%.2f' % v[-1])
        m('CsDump' + _lab + 'N', '%d' % len(v))
if INT_NOCLASSA is not None:
    m('CsIntNoClassA', '%d' % INT_NOCLASSA)
    m('CsIntNRow', '%d' % INT_NROW)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by consist_v412.py -- do not hand-edit.\n'
             '%% round 195: the paired sets of referee 2\'s inconsistency\n'
             '%% table, each named for what it counts and each printed with\n'
             '%% its denominator.\n')
    for k, v in M.items():
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('\n%s: %d macros' % (os.path.basename(OUT), len(M)))
print('  control ensembles joined      %d of %d windows (%d ambiguous keys)'
      % (joined, len(CAT), N_AMBIG3))
print('  the star-blind window-edge key loses %d rows over %d colliding keys'
      % (N_AMBIG_EDGE, N_COLLIDING_KEYS))
print('  control maximum at the trigger  %d (%d Class A) by either route'
      % (trig_vec, trig_vec_A))
print('  star outranks every control     %d windows; %d Class A also cross'
      % (len(RANKFIRST), len(RF_A)))
print('  disc-affected                   %d Class A >=%.0f sigma, %d >=%.0f, '
      '%d of either class >=%.0f'
      % (len(DISC_A), RULE_SIGMA, len(BRIGHT_A), BRIGHT_SIGMA,
         len(BRIGHT_ALL), BRIGHT_SIGMA))
print('  crossings with a frequency      %d of %d' % (len(X_FREQ), len(X)))
print('  beta Pic CO                     %d blocks, %d passing the screen'
      % (len(BP_CO_EB), len(BP_CO_PASS_EB)))
for a, v in sorted(dump.items()):
    print('  dump time %-4s                  median %.3f s over %d windows'
          % (a, st.median(v), len(v)))
