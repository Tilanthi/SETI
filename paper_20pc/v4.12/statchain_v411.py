#!/usr/bin/env python3
r"""round 130 -> survey_numbers_round130.tex: THE ON-STAR NOISE RATIO, THE
DIRECTION OF THE SPATIAL RANK, AND THE DATA-QUALITY DISPOSITION.

Three things the manuscript asserts, or ought to assert, and could not
support with a number.

(1) THE ON-STAR NOISE RATIO.  Equation 1 divides every position by one noise
    scale, the median absolute deviation across the control positions, shared
    by the star and all of them.  If the noise at the stellar position is not
    that scale -- because a bright source there carries multiplicative
    calibration residuals of its own -- then the stellar statistic is
    inflated by the ratio of the two, and nothing in the search would show
    it.  The ratio is measurable from the released control vectors without
    re-extracting anything:

        r = T_star / median(T_control)

    in each window.  The star and each control are divided by the SAME scale
    and maximised over the SAME channel x drift grid, so under equal noise
    the 513 statistics are exchangeable, r has median one over many windows,
    and a noise excess k at the star multiplies r by exactly k (the maximum
    of a scaled field is the scaled maximum).  r is therefore the ratio the
    referee asks for, read through the statistic that the ratio would
    corrupt.

    Reported on the windows with no threshold crossing -- the ones where
    nothing but noise is present -- and SEPARATELY on the windows that carry
    one, which is what keeps the estimator from being a check that cannot
    fail: if r could not rise, 1.00 on the quiet windows would mean nothing.
    It rises to 1.24 where a crossing sits.

    And against field brightness, because that is what a multiplicative
    error scales with: by fifths of the window's own control-ring maximum,
    and separately for the windows whose ring is set by resolved emission
    rather than by noise (the top stratum of the frozen sensitivity record,
    so the bin edge is the paper's own and not chosen here).

(2) THE DIRECTION OF THE RANK.  The manuscript quotes a median rank of 0.405
    without ever saying which way is which, so a reader cannot tell whether
    the star sits high or low.  The convention is settled from the RELEASE
    ITSELF: the catalogue's own `p_rank_addone` reaches its minimum,
    1/(N+1), exactly on the windows whose `n_ctrl_ge_star` is zero.  A LOW
    rank therefore means a HIGH star.  A displacement to 0.405 is the star
    sitting systematically high, and that is the direction that INFLATES
    star-first outcomes rather than suppressing them -- the opposite of what
    one paragraph of the false-alarm appendix said.  The star-first rate is
    measured here against the exchangeable rate so the sign is a number.

(3) THE DATA-QUALITY DISPOSITION.  Referee 2 asks for a disposition set by a
    rule fixed in advance, and suggests one.  THE RULE, WRITTEN DOWN BEFORE
    IT WAS APPLIED (see STAT_REPORT.md section 4, and this docstring):

        a window is flagged when the MEDIAN of its own control ensemble
        exceeds twice the survey median of that quantity.

    The median, not the maximum: one bright control is a source in the field,
    half the field above the trigger is not a null at all.  Nothing else is
    tuned, no star is named in the rule, and the threshold is the survey's
    own median times two.  The flag changes no disposition; it records that
    the spatial screen has no null to work against in that window, whether
    the cause is a defective execution block or a resolved disc.

Reads only released products: `corrected_export_v399.json` (the control
vectors), `per_target_results_v3.99.csv` (classes, crossings, the released
rank column), `r9inputs/sens_r9b.json` (the ring strata), `ledger_v403.csv`
(the flagged star's own crossings).  Nothing is typed except the rule's
factor of two and the ring-stratum edge is read, not chosen.

Eight assertions, each naming the input that would make it fail, and eight
drives.  `--drive 0` means "no perturbation, but do not write a path
production reads".

    python3 statchain_v411.py [--drive N]
"""
import collections
import csv
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

#: the one number this generator chooses, and it is the referee's own
#: suggestion: "control-ensemble median T above twice the survey median"
DQ_FACTOR = 2.0

EXPORT = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
SENSB = json.load(open(os.path.join(HERE, 'r9inputs', 'sens_r9b.json')))
LEDGER = list(csv.DictReader(open(os.path.join(HERE, 'ledger_v403.csv'))))

OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-66s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """Read a macro back out of the macro layer, last definition wins."""
    pat = re.compile(r'\\(?:provide|renew|new)command\{?\\%s\}?\{([^}]*)\}'
                     % name)
    got = None
    for f in sorted(os.listdir(HERE)):
        if not (f.startswith('survey_numbers') and f.endswith('.tex')):
            continue
        if f.endswith('%s.tex' % SUF) and SUF:
            continue
        for mm in pat.finditer(open(os.path.join(HERE, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                got = mm.group(1).strip()
    return got


# --------------------------------------------------------------- the join
# ★ The obvious key, (execution block, window start frequency), SILENTLY DROPS
#   HALF THE SURVEY: the catalogue's `flo_GHz` is the trimmed window start and
#   the export's `flo` is the delivered one, so only 809 of 1641 keys meet and
#   a crossing flag read through that key would have been wrong on most rows.
#   The key below is three measured quantities of the window itself and it
#   closes exactly: 1651 catalogue rows, 1651 matched, 0 ambiguous, and the
#   crossing count is asserted against the published \NCross.
def key(eb, rms, snr):
    return (eb, round(float(rms), 5), round(float(snr), 4))


CATBY = {}
for r in CAT:
    CATBY.setdefault(key(r['eb'], r['rms_mJy'], r['star_snr']), []).append(r)
CAT_AMBIG = sum(1 for v in CATBY.values() if len(v) > 1)

NCTRL_VEC = 512
rows, seen, UNJOINED = [], set(), 0
for r in EXPORT['rows']:
    c, s = r.get('ctrl_all'), r.get('star_snr')
    if not c or s is None:
        continue
    c = np.asarray(c, float)
    if c.size != NCTRL_VEC or not np.all(np.isfinite(c)):
        continue
    k = key(r['eb'], r['rms'], s)
    cr = CATBY.get(k)
    if not cr or len(cr) > 1:
        UNJOINED += 1
        continue
    if k in seen:                      # the export carries repeated rows
        continue
    seen.add(k)
    cr = cr[0]
    off = cr['line_offset_kms']
    rows.append(dict(star=r['star_name'], k=k, ratio=float(s) / float(
        np.median(c)), ring=float(np.max(c)), ringmed=float(np.median(c)),
        cross=cr['crossing'] == 'True',
        attr=(cr['crossing'] == 'True' and off not in (None, '')
              and abs(float(off)) <= float(texval('MaskHalfKms') or 50)),
        cls=cr['search_class'], nge=int((c >= float(s)).sum())))

RAT = np.array([x['ratio'] for x in rows])
RING = np.array([x['ring'] for x in rows])
HASX = np.array([x['cross'] for x in rows])
NWIN = len(rows)

quiet = RAT[~HASX]
loud = RAT[HASX]
MED_Q = float(np.median(quiet))
MED_X = float(np.median(loud))

# star-clustered bootstrap: windows of one star share weather, calibration
# and correlator setup, so whole stars are resampled, not windows.
byst = collections.defaultdict(list)
for x in rows:
    if not x['cross']:
        byst[x['star']].append(x['ratio'])
ks = list(byst)
rng = np.random.default_rng(20261004)
boot = np.array([np.median(np.concatenate(
    [byst[ks[i]] for i in rng.integers(0, len(ks), len(ks))]))
    for _ in range(4000)])
LO, HI = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

# brightness: fifths of the ring maximum, on the quiet windows
rq, gq = RAT[~HASX], RING[~HASX]
edges = np.quantile(gq, np.linspace(0, 1, 6))
FIFTH_LO = float(np.median(rq[gq <= edges[1]]))
FIFTH_HI = float(np.median(rq[gq >= edges[4]]))

BRIGHT_EDGE = SENSB['stratified']['bins'][-2]
bm = RING >= BRIGHT_EDGE
BRIGHT_N = int(bm.sum())
BRIGHT_MED = float(np.median(RAT[bm]))

# ---------------------------------------------------- the rank's direction
rk = [(float(r['p_rank_addone']), int(r['n_ctrl_ge_star']), int(r['n_ctrl']))
      for r in CAT if r['p_rank_addone'] and r['n_ctrl_ge_star'] != '']
FLOOR = min(p for p, n, nc in rk)
FLOOR_N = [n for p, n, nc in rk if abs(p - FLOOR) < 1e-9]
STARFIRST = int((np.array([x['nge'] for x in rows]) == 0).sum())
EXCH = NWIN / float(NCTRL_VEC + 1)

# ------------------------------------------------- the data-quality flag
ringmed = np.array([x['ringmed'] for x in rows])
SURVMED = float(np.median(ringmed))
DQ_THRESH = DQ_FACTOR * SURVMED
flagged = [x for x in rows if x['ringmed'] > DQ_THRESH]
# ★★ v4.11: ONE OWNER OF THIS PREDICATE.  `ledger_v410.py` needs the same
# answer, to give Table 6's flagged rows their disposition instead of
# disposing of them on the spatial rank -- the sentence R2-M5 objects to.  A
# second implementation of one rule is this project's commonest defect (six
# instances of the attribution split alone in this cycle), so the rule lives
# in `dqflag.py`, the ledger imports it, and the counts published HERE are
# asserted against it.  If the two ever part, one of the two tables is wrong
# about which windows failed.
import dqflag as _dq
_dqkeys = _dq.flagged_keys(HERE)
_mykeys = {x['k'] for x in flagged}
ck('N7b the data-quality rule published here is the one the crossing ledger '
   'dispositions Table 6 with, window for window',
   (_mykeys == _dqkeys if DRIVE != 10 else False)
   and abs(SURVMED - _dq.survey_median(HERE)) < 1e-9
   and abs(DQ_FACTOR - _dq.DQ_FACTOR) < 1e-12,
   '%d flagged here, %d in dqflag; only here %s; only there %s'
   % (len(_mykeys), len(_dqkeys), sorted(_mykeys - _dqkeys)[:3],
      sorted(_dqkeys - _mykeys)[:3]))
DQ_STARS = []
for x in flagged:
    s = x['star']
    s = re.sub(r'\s+Gaia DR3 \d+$', '', s).replace('BD05', 'BD$+$05')
    s = re.sub(r'\s+', '~', s.strip())
    if s not in DQ_STARS:
        DQ_STARS.append(s)
DQ_NCROSS = sum(1 for x in flagged if x['cross'])

# the flagged star's own crossings, from the ledger, named by reading it
lg = [r for r in LEDGER if r['eb'] in {x['k'][0] for x in flagged}]
BD_EB = collections.Counter(r['eb'] for r in lg).most_common(1)[0][0] if lg \
    else 'none'
BD_ROWS = [r for r in LEDGER if r['eb'] == BD_EB]
BD_T = sorted(float(r['T_star']) for r in BD_ROWS)
# intermediate-frequency coincidence: the channel index of each crossing in
# its own window, from the catalogue's own window edges
chan = []
for r in CAT:
    if r['eb'] != BD_EB or not r['f_cross_GHz']:
        continue
    lo, cw = float(r['flo_GHz']), float(r['chanw_Hz']) / 1e9
    chan.append(int(round((float(r['f_cross_GHz']) - lo) / cw)))
IF_MULT = collections.Counter(chan).most_common(1)[0] if chan else (0, 0)
BD_RINGMED = sorted(x['ringmed'] for x in flagged
                    if x['k'][0] == BD_EB)

# ★ Is the feature a terrestrial carrier at a fixed SKY frequency, as the
#   appendix used to assert?  Measured, not assumed: for each of the block's
#   crossing frequencies, every other window in the survey that covers it,
#   and whether any carries a crossing in the same channel.  The appendix's
#   old claim -- "appears in the same coarse channel toward unrelated stars"
#   -- is false on this measurement.
BD_COVER, BD_STARS, BD_SAME = [], [], 0
for fc in sorted(set(float(r['f_cross_GHz']) for r in CAT
                     if r['eb'] == BD_EB and r['f_cross_GHz'])):
    cov = [r for r in CAT if r['eb'] != BD_EB
           and float(r['flo_GHz']) <= fc <= float(r['fhi_GHz'])]
    BD_COVER.append(len(cov))
    BD_STARS.append(len({r['star_name'] for r in cov}))
    BD_SAME += sum(1 for r in cov if r['crossing'] == 'True'
                   and r['f_cross_GHz']
                   and abs(float(r['f_cross_GHz']) - fc)
                   <= float(r['chanw_Hz']) / 1e9)

# ------------------------------- the IF-position population (R2 minor 11)
# ★★ v4.12: THIS PAIR WAS A COUNT OF ONE SET AND A COUNT OF ANOTHER, JOINED
# BY "OF WHICH".  The appendix reads "run over every window for which the
# catalogue releases a peak frequency --- \IfPopNWin{} of them, of which
# only \IfPopNCross{} carry a threshold crossing".  "of which" refers to
# those 1397 windows -- but \IfPopNCross counted EVERY crossing in the
# catalogue, and five crossings (all beta Pic: four Band 3, one Band 6)
# carry no released frequency column at all, so they are not in the
# population the test runs over.  Inside it the number is 51.  N8 below
# required \IfPopNCross == \NCross, which is to say the check enforced the
# error; it now requires the strict subset, and both counts are published so
# the sentence can state them apart.
IF_NWIN = sum(1 for r in CAT if r['f_cross_GHz'].strip())
IF_NCROSS = sum(1 for r in CAT
                if r['crossing'] == 'True' and r['f_cross_GHz'].strip())
IF_NCROSS_ALL = sum(1 for r in CAT if r['crossing'] == 'True')
IF_NCROSS_NOFREQ = IF_NCROSS_ALL - IF_NCROSS
IF_NOFREQ_STARS = sorted({r['star_name'] for r in CAT
                          if r['crossing'] == 'True'
                          and not r['f_cross_GHz'].strip()})

# ------------------------------------------------------------- assertions
print('\non-star noise ratio  r = T_star / median(T_control)')
print('  %d windows with a full %d-position control vector' % (NWIN, NCTRL_VEC))
print('  quiet windows (no crossing): n=%d median %.4f, star-clustered 95%% '
      '%.4f-%.4f' % (len(quiet), MED_Q, LO, HI))
print('  crossing windows:            n=%d median %.4f' % (len(loud), MED_X))
print('  faintest fifth of rings %.4f, brightest fifth %.4f' % (FIFTH_LO,
                                                                FIFTH_HI))
print('  rings >= %.0f sigma (resolved emission): n=%d median %.4f'
      % (BRIGHT_EDGE, BRIGHT_N, BRIGHT_MED))
print('rank direction: floor %.6f on %d windows, all with n_ctrl_ge_star=%s'
      % (FLOOR, len(FLOOR_N), set(FLOOR_N)))
print('  star first in %d of %d windows against %.1f if exchangeable (x%.2f)'
      % (STARFIRST, NWIN, EXCH, STARFIRST / EXCH))
print('data-quality flag: survey median ring median %.4f, threshold %.4f'
      % (SURVMED, DQ_THRESH))
print('  %d windows, %d stars: %s' % (len(flagged), len(DQ_STARS), DQ_STARS))
print('  worst block %s: ring medians %s, T_star %s'
      % (BD_EB, ['%.2f' % v for v in BD_RINGMED], ['%.2f' % v for v in BD_T]))
print('  its crossings by channel index: %s, commonest %s' % (chan, IF_MULT))

print('\nassertions')
ck('N1 the join closes on the published survey: one control vector per '
   'catalogue row, every crossing found, and \\NCtrl is the vector length',
   NWIN == int(texval('NWindows') or -1) and CAT_AMBIG == 0
   and int(HASX.sum()) == int(texval('NCross') or -1)
   and (NCTRL_VEC if DRIVE != 1 else 511) == int(texval('NCtrl') or 0),
   '%d windows of a declared %s, %d crossings of a declared %s, '
   '\\NCtrl %s, %d export rows unjoined'
   % (NWIN, texval('NWindows'), int(HASX.sum()), texval('NCross'),
      texval('NCtrl'), UNJOINED))
ck('N2 the ratio is consistent with unity on the quiet windows -- which is '
   'the finding, and the ruling that the search is not re-run',
   LO <= (1.0 if DRIVE != 2 else 1.5) <= HI,
   'median %.4f, 95%% %.4f-%.4f' % (MED_Q, LO, HI))
ck('N3 the estimator CAN see an excess at the star, so N2 is not a check '
   'that cannot fail',
   (MED_X if DRIVE != 3 else MED_Q) > HI + 0.05,
   'crossing windows %.4f against %.4f' % (MED_X, MED_Q))
ck('N4 the ratio does not climb with field brightness',
   abs((FIFTH_HI if DRIVE != 4 else 1.4) - FIFTH_LO) < 0.02
   and abs((BRIGHT_MED if DRIVE != 4 else 2.0) - MED_Q) < 0.15,
   'fifths %.4f vs %.4f, resolved-ring stratum %.4f'
   % (FIFTH_LO, FIFTH_HI, BRIGHT_MED))
ck('N5 a LOW rank means a HIGH star: the released rank reaches its floor '
   'exactly where no control beats the star',
   FLOOR_N == [0] * len(FLOOR_N) and len(FLOOR_N) > 0
   and abs(FLOOR - 1.0 / (NCTRL_VEC + 1)) < (1e-5 if DRIVE != 5 else -1),
   'floor %.6f = 1/(%d+1) on %d windows' % (FLOOR, NCTRL_VEC, len(FLOOR_N)))
ck('N6 the displacement therefore INFLATES star-first outcomes: the '
   'measured rate exceeds the exchangeable one',
   (STARFIRST if DRIVE != 6 else 0) > EXCH,
   '%d against %.1f expected' % (STARFIRST, EXCH))
ck('N7 the rule flags the defective block in full, stays rare, is not a '
   'relabelling of "crossing", and cuts across attribution',
   len(BD_RINGMED) == len(BD_ROWS)
   and len(flagged) / float(NWIN) < (0.01 if DRIVE != 7 else 0.0)
   and DQ_NCROSS < int(HASX.sum())
   and any(x['attr'] for x in flagged) and any(
       x['cross'] and not x['attr'] for x in flagged),
   '%d of %d windows flagged, %d of %d crossings, %d attributed'
   % (len(flagged), NWIN, DQ_NCROSS, int(HASX.sum()),
      sum(1 for x in flagged if x['attr'])))
ck('N9 the flagged block is NOT a carrier at a fixed sky frequency: its '
   'frequencies are covered toward many other stars and none crosses',
   min(BD_COVER) > 50 and min(BD_STARS) > 5
   and (BD_SAME if DRIVE != 9 else 1) == 0,
   '%d-%d other windows toward %d-%d other stars, %d with a crossing in '
   'the same channel' % (min(BD_COVER), max(BD_COVER), min(BD_STARS),
                         max(BD_STARS), BD_SAME))
_ifn = IF_NCROSS_ALL if DRIVE == 11 else IF_NCROSS
ck('N8 the fractional-position test runs over WINDOWS, and the crossing '
   'count inside it is a strict subset of the catalogue\'s',
   IF_NWIN > _ifn and IF_NWIN == int(texval('RfiNFrac') or -1)
   and _ifn < IF_NCROSS_ALL and IF_NCROSS_NOFREQ > 0
   and (IF_NCROSS_ALL if DRIVE != 8 else 0) == int(texval('NCross') or -1),
   '%d windows carry a released peak frequency, %d of them a crossing, '
   'against %d crossings in the catalogue; the %d without a released '
   'frequency are all %s'
   % (IF_NWIN, _ifn, IF_NCROSS_ALL, IF_NCROSS_NOFREQ,
      ', '.join(IF_NOFREQ_STARS)))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('statchain_v411: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ---------------------------------------------------------------- macros
m('NsrNWin', '%d' % len(quiet))
m('NsrMed', '%.3f' % MED_Q)
m('NsrLo', '%.3f' % LO)
m('NsrHi', '%.3f' % HI)
m('NsrCrossMed', '%.2f' % MED_X)
m('NsrCrossN', '%d' % len(loud))
m('NsrFifthLo', '%.3f' % FIFTH_LO)
m('NsrFifthHi', '%.3f' % FIFTH_HI)
m('NsrBrightSig', '%.0f' % BRIGHT_EDGE)
m('NsrBrightN', '%d' % BRIGHT_N)
m('NsrBrightMed', '%.2f' % BRIGHT_MED)
m('NsrRankFloor', '%d' % (NCTRL_VEC + 1))
m('NsrFirstObs', '%d' % STARFIRST)
m('NsrFirstExp', '%.1f' % EXCH)
m('NsrFirstRatio', '%.1f' % (STARFIRST / EXCH))
m('DqFactor', 'twice')
m('DqSurvMed', '%.2f' % SURVMED)
m('DqThresh', '%.1f' % DQ_THRESH)
m('DqNWin', '%d' % len(flagged))
m('DqNStar', '%d' % len(DQ_STARS))
m('DqStars', ', '.join(DQ_STARS[:-1]) + ' and ' + DQ_STARS[-1]
  if len(DQ_STARS) > 1 else DQ_STARS[0])
m('DqNCross', '%d' % DQ_NCROSS)
m('DqBlock', BD_EB.replace('_', r'\_'))
m('DqBlockRingLo', '%.1f' % BD_RINGMED[0])
m('DqBlockRingHi', '%.1f' % BD_RINGMED[-1])
m('DqBlockNCross', '%d' % len(BD_ROWS))
m('DqBlockTLo', '%.1f' % BD_T[0])
m('DqBlockTHi', '%.1f' % BD_T[-1])
m('DqBlockIfMult', '%d' % IF_MULT[1])
m('DqBlockIfChan', '%d' % IF_MULT[0])
m('DqOtherWinLo', '%d' % min(BD_COVER))
m('DqOtherWinHi', '%d' % max(BD_COVER))
m('DqOtherStarLo', '%d' % min(BD_STARS))
m('DqOtherStarHi', '%d' % max(BD_STARS))
m('DqOtherSame', '%d' % BD_SAME)
m('IfPopNWin', '%d' % IF_NWIN)
m('IfPopNCross', '%d' % IF_NCROSS)
m('IfPopNCrossAll', '%d' % IF_NCROSS_ALL)
m('IfPopNCrossNoFreq', '%d' % IF_NCROSS_NOFREQ)

path = os.path.join(HERE, 'survey_numbers_round130%s.tex' % SUF)
with open(path, 'w') as fh:
    fh.write('%% GENERATED by statchain_v411.py -- do not hand-edit.\n')
    fh.write('%% round 130: the on-star noise ratio, the rank direction and\n')
    fh.write('%% the data-quality disposition.\n')
    fh.write('\n'.join(OUT) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(path), len(OUT)))
