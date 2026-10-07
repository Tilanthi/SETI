#!/usr/bin/env python3
r"""round 175 -> survey_numbers_round175.tex: THE EXECUTION-BLOCK QUALITY
CRITERION, THE CLASS DECOMPOSITION OF THE CROSSINGS, AND THE CHANCE
EXPECTATION WITH ITS MEASURED TAIL FACTOR.

Three things, all of them asked for, all of them cheap.

(1) THE BLOCK-QUALITY CRITERION (R1-6).  Four crossings arise in one ACA block
    whose whole control ensemble sits far above the trigger.  The manuscript
    recognises the condition and then keeps the block, which is a condition
    and not a criterion.  So the condition becomes a rule, the rule is written
    down in /workspace/SETI/referee_r11/BLOCKQ_CRITERION.md BEFORE it is
    applied, and it is then applied to every block of the primary census:

        the statistic is the MEDIAN of a window's 512-position control
        ensemble, m_w -- the paper's own diagnostic, and the median rather
        than the maximum, because a ring with one bright position holds a
        source while a ring whose typical position is bright is no null at
        all;

        m_w is a maximum over the window's own channel x drift grid, so its
        null level rises with the cell count, which differs by orders of
        magnitude between the two search classes.  It is therefore scaled by
        the median of m_w over the windows of its OWN class,
        q_w = m_w / median(m of that class), so that one threshold means one
        thing in both classes;

        the BLOCK statistic is Q_b = median(q_w over the block's windows),
        median again and for the same reason;

        and a block FAILS when Q_b > 2.  The factor is not chosen here: it is
        the factor already carried by this manuscript's published window-level
        data-quality flag (`dqflag.DQ_FACTOR`, macro \DqFactor, "twice the
        survey median"), which was itself fixed before it was applied.  This
        generator promotes that published rule from the window to the block
        and changes nothing else, so there is no new tuned number in it.

    The raw, unscaled variant is computed alongside and published, so that a
    reader can see the normalisation does not decide the answer.

    Then the complete Class A results WITH and WITHOUT the failing blocks.
    ★ The interesting part is that the two are identical, and the reason is
    measured here rather than asserted: the failing block holds no Class A
    window at all, so no Class A statistic in the paper has ever contained it.

(2) THE CLASS DECOMPOSITION OF THE CROSSINGS (R2-M4.2).  The referee reads the
    text as implying 35 Class A and 2 Class B unattributed crossings.  Both
    halves are wrong, and the truth is more useful to us: the four Class B
    crossings are unattributed, and they are the entire Class B crossing
    population of the survey, and all four come from the one block the
    criterion of (1) rejects.  The class of a crossing is resolved by
    containment in the block's own released windows, and for the two
    epoch-extension crossings whose blocks are not in the released catalogue,
    from the extension's own per-window records.  Nothing is typed.

(3) THE CHANCE EXPECTATION WITH ITS TAIL FACTOR (R2-M4.1).  The headline
    expectation is built on exceedance rates at the control positions, and the
    hold-out measures that the star and the controls are not exchangeable, at
    a tail factor of \HoTailFactor with interval \HoTailLo-\HoTailHi.  The
    factor is applied to the headline here and the result published as ONE
    range.  The uncertainty is larger than the difference between the
    expectation and the observation, which is the referee's point and the
    reason the words "agreement to one" leave the paper.

Reads only released products and the published macro layer:
`corrected_export_v399.json` (the control vectors), `per_target_results_v3.99.csv`
(classes and window edges), `ledger.json` (the dispositions),
`r8inputs/v409/hd14055_results.json` (the extension windows), `dqflag.py` (the
published window-level rule) and the survey_numbers macro layer.

Ten assertions, each naming what would make it fail, and ten drives.
`--drive 0` means "no perturbation, but do not write a path production reads".

    python3 blockq_v412.py [--drive N]
"""
import collections
import csv
import json
import os
import re
import sys

import numpy as np

import dqflag

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 175

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

OUT_NAME = 'survey_numbers_round175%s.tex' % SUF
OUT_PATH = os.path.join(HERE, OUT_NAME)

#: the rule's factor, taken from the published window-level flag and not
#: chosen here.  A second number would be a second rule.
BQ_FACTOR = dqflag.DQ_FACTOR
NCTRL_VEC = dqflag.NCTRL_VEC

OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-72s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """Read a macro out of the published macro layer; last definition wins."""
    pat = re.compile(r'\\(?:provide|renew|new)command\{?\\%s\}?\{([^}]*)\}'
                     % name)
    got = None
    for f in sorted(os.listdir(HERE)):
        if not (f.startswith('survey_numbers') and f.endswith('.tex')):
            continue
        if SUF and f.endswith('%s.tex' % SUF):
            continue
        if f == 'survey_numbers_round%d.tex' % ROUND:
            continue                     # never read our own previous output
        for mm in pat.finditer(open(os.path.join(HERE, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                got = mm.group(1).strip()
    return got


# --------------------------------------------------------------- the inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXPORT = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))
LEDGER = json.load(open(os.path.join(HERE, 'ledger.json')))
EXT = json.load(open(os.path.join(
    HERE, 'r8inputs', 'v409', 'hd14055_results.json')))
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']

CLS = {}          # window key -> search class
for r in CAT:
    CLS[dqflag.key(r['eb'], r['rms_mJy'], r['star_snr'])] = r['search_class']

RINGMED = dqflag._load(HERE)['ringmed']      # window key -> median control T
assert len(RINGMED) == len(CLS), (len(RINGMED), len(CLS))

# the full control vectors of the worst block, for the condition the referee
# names: that the whole ensemble exceeds the trigger
TRIG = float(texval('StageNullTrig') or 5)

# ------------------------------------------- the statistic and the criterion
CLASS_MED = {}
for c in sorted(set(CLS.values())):
    CLASS_MED[c] = float(np.median([v for k, v in RINGMED.items()
                                    if CLS[k] == c]))
Q = {k: v / CLASS_MED[CLS[k]] for k, v in RINGMED.items()}

BY_BLOCK = collections.defaultdict(list)
BY_BLOCK_RAW = collections.defaultdict(list)
for k, v in Q.items():
    BY_BLOCK[k[0]].append(v)
    BY_BLOCK_RAW[k[0]].append(RINGMED[k])
QB = {e: float(np.median(v)) for e, v in BY_BLOCK.items()}
SURV_RAW = float(np.median(list(RINGMED.values())))
QB_RAW = {e: float(np.median(v)) / SURV_RAW for e, v in BY_BLOCK_RAW.items()}

FACTOR = BQ_FACTOR if DRIVE not in (4, 14) else (0.0 if DRIVE == 4 else 1e9)
FAILED = {e for e, q in QB.items() if q > FACTOR}
FAILED_RAW = {e for e, q in QB_RAW.items() if q > BQ_FACTOR}

QB_SORTED = sorted(QB.items(), key=lambda kv: -kv[1])
Q_MED_BLOCK = float(np.median(list(QB.values())))

# ------------------------------------- the class of every ledger crossing
BYEB = collections.defaultdict(list)
for r in CAT:
    BYEB[r['eb']].append(r)


def crossing_class(row):
    """The search class of the window a crossing sits in.

    Containment in the block's own released window edges, min/max of the pair
    because a descending spectral window writes them reversed.  Blocks absent
    from the released catalogue -- the epoch-extension blocks -- are resolved
    from the extension's own per-window records, by the same containment and
    its own recorded resolution class.  Never from the star name.
    """
    cand = set()
    for r in BYEB.get(row['eb'], ()):
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if lo <= row['freq'] <= hi:
            cand.add(r['search_class'])
    if len(cand) == 1:
        return cand.pop(), 'catalogue'
    if not cand:
        for x in EXT:
            if x['eb'] != row['eb']:
                continue
            lo, hi = sorted((float(x['flo']), float(x['fhi'])))
            if lo <= row['freq'] <= hi:
                return ('A' if x['rc'].startswith('fine') else 'B'), 'extension'
    return '?', 'unresolved'


XR = LEDGER['rows']
for _r in XR:
    _r['cls'], _r['cls_src'] = crossing_class(_r)
N_UNRESOLVED = sum(1 for r in XR if r['cls'] == '?')
N_EXT = sum(1 for r in XR if r['cls_src'] == 'extension')

XA = [r for r in XR if r['cls'] == 'A']
XB = [r for r in XR if r['cls'] == 'B']
ATTR_A = [r for r in XA if r['attributed']]
ATTR_B = [r for r in XB if r['attributed']]
UN_A = [r for r in XA if not r['attributed']]
UN_B = [r for r in XB if not r['attributed']]
RANK_A = [r for r in UN_A if r.get('screen')]

# ----------------------------------- Class A, with and without the failures
def census(keep):
    """(windows, crossings, attributed, unattributed, rank-passing) over the
    Class A windows of the blocks in `keep`."""
    win = [k for k in CLS if CLS[k] == 'A' and k[0] in keep]
    xs = [r for r in XA if r['eb'] in keep or r['cls_src'] == 'extension']
    return (len(win), len(xs), sum(1 for r in xs if r['attributed']),
            sum(1 for r in xs if not r['attributed']),
            sum(1 for r in xs if not r['attributed'] and r.get('screen')))


ALL_EB = set(e for e in BY_BLOCK)
KEEP = ALL_EB - FAILED
WITH = census(ALL_EB)
WITHOUT = census(KEEP)

SURV_WIN_WITH = len(CLS)
SURV_WIN_WITHOUT = sum(1 for k in CLS if k[0] not in FAILED)
SURV_X_WITH = len(XR)
SURV_X_WITHOUT = sum(1 for r in XR
                     if r['eb'] not in FAILED or r['cls_src'] == 'extension')
XB_LOST = sum(1 for r in XB if r['eb'] in FAILED)

# ------------------------------------ the failing block, described by reading
WORST = QB_SORTED[0][0]
NEXT_Q = QB_SORTED[1][1]
WORST_WIN = [k for k in CLS if k[0] == WORST]
WORST_X = [r for r in XR if r['eb'] == WORST]
WORST_CTRL = []
_seen = set()
for r in EXPORT['rows']:
    if r['eb'] != WORST or not r.get('ctrl_all') or r.get('star_snr') is None:
        continue
    k = dqflag.key(r['eb'], r['rms'], r['star_snr'])
    if k in _seen or k not in RINGMED:
        continue
    _seen.add(k)
    WORST_CTRL.append(np.asarray(r['ctrl_all'], float))
CTRL_MIN = float(min(c.min() for c in WORST_CTRL))
CTRL_FRAC = float(np.mean([(c >= TRIG).mean() for c in WORST_CTRL]))
WORST_STAR_BELOW = sum(1 for c, r in zip(WORST_CTRL, sorted(
    (x for x in EXPORT['rows'] if x['eb'] == WORST and x.get('ctrl_all')),
    key=lambda x: x['star_snr']))
    if float(r['star_snr']) < np.median(c))
WORST_ARRAY = META.get(WORST, {}).get('array', 'unknown')
WORST_NANT = META.get(WORST, {}).get('n_ant', 0)


def disp(s):
    s = re.sub(r'\s+Gaia DR3 \d+$', '', s).replace('BD05', 'BD$+$05')
    return re.sub(r'\s+', '~', s.strip())


WORST_STARS = []
for r in CAT:
    if r['eb'] == WORST and disp(r['star_name']) not in WORST_STARS:
        WORST_STARS.append(disp(r['star_name']))

# ------------------------- the reserved hold-out, as a branch of its own
# ★ R2 asks for the hold-out reported rather than summarised as one
#   rank-conditioned number, and Fig. 8 must carry it as a separate branch.
#   Counted here from the hold-out's own released export, through the same
#   trigger the primary census uses.  The attribution split is NOT computed
#   here: the mask is evaluated in the stellar frame and this export carries
#   only topocentric offsets, so publishing a split from it would be wrong.
HO = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
HO_X = [r for r in HO if r.get('star_snr') is not None
        and float(r['star_snr']) >= TRIG]
HO_FIRST = [r for r in HO_X if int(r.get('n_ge_star', 1)) == 0]

# ------------------------------------ the chance expectation and its factor
E_HEAD = float(texval('RsevChanceExp'))
TF = float(texval('HoTailFactor'))
TF_LO = float(texval('HoTailLo'))
TF_HI = float(texval('HoTailHi'))
E_MID, E_LO, E_HI = E_HEAD * TF, E_HEAD * TF_LO, E_HEAD * TF_HI
OBS_RELEASED = int(texval('RsevChanceObsAUnattr'))

# ------------------------------------------------------------- what was found
print('block-quality criterion:  Q_b = median over the block of '
      'm_w / median(m of its class);  FAIL when Q_b > %.1f' % BQ_FACTOR)
print('  class medians of the window statistic: %s'
      % {c: round(v, 3) for c, v in CLASS_MED.items()})
print('  %d blocks, median Q_b %.3f; failing %d: %s'
      % (len(QB), Q_MED_BLOCK, len(FAILED), sorted(FAILED)))
print('  worst %s Q_b %.3f (%s, %d antennas, %d windows, %d crossings), '
      'next worst %.3f' % (WORST, QB[WORST], WORST_ARRAY, WORST_NANT,
                           len(WORST_WIN), len(WORST_X), NEXT_Q))
print('  its control ensembles: smallest of all %d positions %.2f, '
      'fraction above the trigger %.3f' % (NCTRL_VEC, CTRL_MIN, CTRL_FRAC))
print('  raw (unscaled) variant fails %d: %s' % (len(FAILED_RAW),
                                                 sorted(FAILED_RAW)))
print('Class A   with the failing blocks: %s' % (WITH,))
print('Class A without the failing blocks: %s' % (WITHOUT,))
print('survey windows %d -> %d, crossings %d -> %d, Class B crossings lost %d'
      % (SURV_WIN_WITH, SURV_WIN_WITHOUT, SURV_X_WITH, SURV_X_WITHOUT,
         XB_LOST))
print('class decomposition: A %d (%d attr, %d unattr, %d outrank all ctrl), '
      'B %d (%d attr, %d unattr); %d resolved from the extension records, '
      '%d unresolved' % (len(XA), len(ATTR_A), len(UN_A), len(RANK_A),
                         len(XB), len(ATTR_B), len(UN_B), N_EXT, N_UNRESOLVED))
print('chance expectation %.1f x tail factor %.1f (%.1f-%.1f) = %.0f '
      '(%.0f-%.0f) against %d observed (ledger) / %d (released column)'
      % (E_HEAD, TF, TF_LO, TF_HI, E_MID, E_LO, E_HI, len(UN_A),
         OBS_RELEASED))

# ------------------------------------------------------------- assertions
print('\nassertions')
ck('B1 every primary-census block is judged: one control ensemble per '
   'released window, and the block count is the published one',
   len(RINGMED) == int(texval('NWindows') or -1)
   and len(QB) == int(texval('NEB') or -1)
   and (len(QB) if DRIVE != 1 else 0) == len({r['eb'] for r in CAT}),
   '%d windows of a declared %s, %d blocks of a declared %s'
   % (len(RINGMED), texval('NWindows'), len(QB), texval('NEB')))
ck('B2 the class scaling does what it is for: the median window of each '
   'class sits at q = 1, so one threshold means one thing in both',
   all(abs(float(np.median([v for k, v in Q.items() if CLS[k] == c])) - 1.0)
       < (1e-9 if DRIVE != 2 else -1) for c in CLASS_MED)
   and abs(CLASS_MED['A'] / CLASS_MED['B'] - 1.0) > 0.3,
   'class medians %s, ratio %.2f'
   % ({c: round(v, 3) for c, v in CLASS_MED.items()},
      CLASS_MED['A'] / CLASS_MED['B']))
ck('B3 the rule fails something, does not fail everything, and separates '
   'the block it fails from the rest of the survey by a clear margin',
   0 < len(FAILED) < 0.02 * len(QB)
   and (NEXT_Q if DRIVE != 3 else 9.9) < BQ_FACTOR
   and QB[WORST] > 2 * BQ_FACTOR,
   '%d of %d blocks fail, worst %.2f, next worst %.2f, threshold %.1f'
   % (len(FAILED), len(QB), QB[WORST], NEXT_Q, BQ_FACTOR))
ck('B4 the rule is a function of its factor and not a stored list: at a '
   'factor of zero every block fails and at 1e9 none does',
   len({e for e, q in QB.items() if q > 0.0}) == len(QB)
   and len({e for e, q in QB.items() if q > 1e9}) == 0
   and (len(FAILED) == 1 if DRIVE not in (4, 14)
        else len(FAILED) in (0, len(QB))),
   'at the declared factor %d fail; this run used %.3g' % (len(FAILED),
                                                           FACTOR))
ck('B5 the normalisation does not decide the answer: the raw, unscaled '
   'variant of the rule fails the same blocks',
   (FAILED_RAW if DRIVE != 5 else set()) == {e for e, q in QB.items()
                                             if q > BQ_FACTOR},
   'scaled %s, raw %s' % (sorted({e for e, q in QB.items()
                                  if q > BQ_FACTOR}), sorted(FAILED_RAW)))
ck('B6 THE RESULT: no Class A window lies in a failing block, so the '
   'complete Class A census is identical with and without them',
   (WITH if DRIVE != 6 else (0, 0, 0, 0, 0)) == WITHOUT
   and WITH[0] == int(texval('NWinA') or -1),
   'with %s, without %s, declared NWinA %s' % (WITH, WITHOUT,
                                               texval('NWinA')))
ck('B7 the class decomposition closes on the published crossing totals, in '
   'both directions, and nothing is left unclassified',
   len(XA) + len(XB) == int(texval('NCross') or -1)
   and len(ATTR_A) + len(ATTR_B) + len(UN_A) + len(UN_B)
   == int(texval('NCross') or -1)
   and len(XA) == int(texval('NHitsA') or -1)
   and len(XB) == int(texval('NHitsB') or -1)
   and (N_UNRESOLVED if DRIVE != 7 else 1) == 0,
   'A %d (declared %s), B %d (declared %s), attr %d+%d, unattr %d+%d, '
   'total declared %s, unresolved %d'
   % (len(XA), texval('NHitsA'), len(XB), texval('NHitsB'), len(ATTR_A),
      len(ATTR_B), len(UN_A), len(UN_B), texval('NCross'), N_UNRESOLVED))
ck('B8 the condition the criterion is for is present in the block it '
   'fails: every one of its control positions exceeds the trigger',
   (CTRL_FRAC if DRIVE != 8 else 0.5) == 1.0 and CTRL_MIN > TRIG
   and len(WORST_CTRL) == len(WORST_WIN),
   'smallest of %d x %d positions %.2f against a trigger of %.0f'
   % (len(WORST_CTRL), NCTRL_VEC, CTRL_MIN, TRIG))
ck('B9 the block rule is stricter than the published window flag and not a '
   'relabelling of it: it fails a subset of the flagged blocks, and it '
   'does NOT fail the block whose single flagged window is a resolved disc',
   FAILED <= dqflag.flagged_ebs(HERE)
   and (len(FAILED) if DRIVE != 9 else len(dqflag.flagged_ebs(HERE)))
   < len(dqflag.flagged_ebs(HERE)),
   'block rule fails %s; the window flag reaches %s'
   % (sorted(FAILED), sorted(dqflag.flagged_ebs(HERE))))
ck('B11 the hold-out is counted from its own export, over the published '
   'number of reserved windows, and none of its crossings outranks all its '
   'controls -- which is what the published rank-conditioned count says',
   len(HO) == int(texval('HoWin') or -1)
   and (len(HO_FIRST) if DRIVE != 11 else 1) == int(texval('HoStageOne') or -1)
   and 0 < len(HO_X) < 0.1 * len(HO),
   '%d reserved windows of a declared %s, %d crossings, %d star-first '
   'against a declared %s' % (len(HO), texval('HoWin'), len(HO_X),
                              len(HO_FIRST), texval('HoStageOne')))
ck('B10 the tail-corrected expectation is a range that contains the point '
   'estimate and the observed count, and is wider than their difference',
   E_LO < E_MID < E_HI and E_LO <= len(UN_A) <= E_HI
   and (E_HI - E_LO if DRIVE != 10 else 0.0) > abs(E_MID - len(UN_A)),
   '%.1f (%.1f-%.1f) against %d observed; width %.1f against a difference '
   'of %.1f' % (E_MID, E_LO, E_HI, len(UN_A), E_HI - E_LO,
                abs(E_MID - len(UN_A))))

# ★★ Reported, not asserted, because the macro layer is written by another
#    generator and may legitimately be mid-flight while the mask is rebuilt:
#    the attribution split published as \NAttributed / \NUnattributed must
#    agree with the ledger this generator reads.  If it does not, the macro
#    layer is stale and the integrator must re-run the ledger's own macro
#    generator BEFORE this one.  The crossing totals are asserted above, so a
#    stale split cannot pass unnoticed into the class decomposition.
_declA, _declU = texval('NAttributed'), texval('NUnattributed')
if (_declA, _declU) != ('%d' % (len(ATTR_A) + len(ATTR_B)),
                        '%d' % (len(UN_A) + len(UN_B))):
    print('\n  STALE MACRO LAYER  \\NAttributed=%s / \\NUnattributed=%s '
          'against the ledger\'s %d / %d.\n'
          '        Re-run the ledger macro generator, then this one.  The '
          'counts published here are the LEDGER\'s.'
          % (_declA, _declU, len(ATTR_A) + len(ATTR_B),
             len(UN_A) + len(UN_B)))

# ★ Reported, not asserted, because the fix is not this generator's: the
#   released catalogue's own disposition column and the live ledger disagree
#   about how many Class A crossings are unattributed.  The ledger is the
#   paper's authority, so the ledger count is what is published here.
if len(UN_A) != OBS_RELEASED:
    print('\n  NOTE  the released catalogue column gives %d unattributed '
          'Class A crossings and the ledger gives %d.  The ledger is the\n'
          '        paper\'s authority (stellar-frame mask, repaired T*), so '
          '\\ChnUnattrA is the ledger count and \\RsevChanceObsAUnattr\n'
          '        must be retired from the prose.  Queued for the '
          'integrator.' % (OBS_RELEASED, len(UN_A)))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('blockq_v412: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ---------------------------------------------------------------- macros
m('BqFactor', 'twice')
m('BqNBlocks', '%d' % len(QB))
m('BqQMed', '%.2f' % Q_MED_BLOCK)
m('BqNFail', '%d' % len(FAILED))
m('BqFailBlock', WORST.replace('_', r'\_'))
m('BqFailStar', WORST_STARS[0])
m('BqFailArray', 'ACA' if WORST_ARRAY == '7m' else WORST_ARRAY)
m('BqFailNAnt', '%d' % WORST_NANT)
m('BqFailQ', '%.1f' % QB[WORST])
m('BqNextQ', '%.2f' % NEXT_Q)
m('BqFailNWin', '%d' % len(WORST_WIN))
m('BqFailNCross', '%d' % len(WORST_X))
m('BqFailCtrlMin', '%.1f' % CTRL_MIN)
m('BqRawNFail', '%d' % len(FAILED_RAW))
m('BqWinA', '%d' % WITH[0])
m('BqWinACut', '%d' % WITHOUT[0])
m('BqXrossA', '%d' % WITH[1])
m('BqXrossACut', '%d' % WITHOUT[1])
m('BqUnattrA', '%d' % WITH[3])
m('BqUnattrACut', '%d' % WITHOUT[3])
m('BqRankA', '%d' % WITH[4])
m('BqRankACut', '%d' % WITHOUT[4])
m('BqSurvWin', '%d' % SURV_WIN_WITH)
m('BqSurvWinCut', '%d' % SURV_WIN_WITHOUT)
m('BqSurvXross', '%d' % SURV_X_WITH)
m('BqSurvXrossCut', '%d' % SURV_X_WITHOUT)
m('BqXrossBLost', '%d' % XB_LOST)
m('ChnXrossA', '%d' % len(XA))
m('ChnXrossB', '%d' % len(XB))
m('ChnAttrA', '%d' % len(ATTR_A))
m('ChnAttrB', '%d' % len(ATTR_B))
m('ChnUnattrA', '%d' % len(UN_A))
m('ChnUnattrB', '%d' % len(UN_B))
m('ChnRankA', '%d' % len(RANK_A))
m('ChnHoWin', '%d' % len(HO))
m('ChnHoCross', '%d' % len(HO_X))
m('ChnHoFirst', '%d' % len(HO_FIRST))
m('ChnChanceMid', '%.0f' % E_MID)
m('ChnChanceLo', '%.0f' % E_LO)
m('ChnChanceHi', '%.0f' % E_HI)

#: ★ '%%' inside a %-formatted string is a LITERAL '%', which silently turned
#: the second comment line into a one-character LaTeX comment.  Concatenate.
HDR = ['%% GENERATED by blockq_v412.py -- do not hand-edit.',
       '%% round ' + str(ROUND) + ': the execution-block quality criterion, '
       'the class',
       '%% decomposition of the crossings, and the chance expectation with',
       '%% its measured tail factor.']
with open(OUT_PATH, 'w') as fh:
    fh.write('\n'.join(HDR + sorted(OUT)) + '\n')
print('\nwrote %s: %d macros' % (OUT_NAME, len(OUT)))
