#!/usr/bin/env python3
r"""Round 850: THE RESERVED HOLD-OUT SPLIT AT SESSION LEVEL, AND WHAT SURVIVES
ON THE BLOCKS THAT SHARE NO SESSION WITH THE CENSUS.

WHY THIS EXISTS
    The hold-out rule hashes the EXECUTION BLOCK, and ALMA's identifier carries
    the observing session above the block, so two executions of one session can
    fall on opposite sides of the split.  \BkSessHoBlocks of the \NEbHeldOut
    reserved blocks share a session with a searched one.  The paper reports
    that and then draws out-of-sample conclusions from the whole reserved set
    anyway: the rank displacement, the confirmation of the step to the star,
    and the dispositions of the reserved trigger events.  Independence is what
    those three rest on.

    Everything the hold-out licenses is therefore re-measured here on the
    blocks that share NO session with the census, beside the full set, by the
    same code.

WHAT IT FINDS, AND IT RUNS AGAINST US
    The rank displacement survives: HsIndRankMed on the session-independent
    blocks against the HoRankMed of the whole reserved set.

    The out-of-sample confirmation of the step DOES NOT.  Every one of the
    reserved set's trigger events lies in a block that shares a session with
    the census, so on the session-independent blocks there are HsIndObs events
    against HsIndExp expected -- a subset with no events in it, which cannot
    agree with a step and cannot disagree with one either; the Poisson
    probability of seeing none at the control rate is HsIndPNone, so the
    subset is uninformative rather than discrepant.  The agreement the paper
    reports is carried entirely by the HsShareBlocks blocks that share a
    session, where the ratio is HsShareRatio.

    Table 7's dispositions are in the same position: HsIndDispo of its rows
    come from a session-independent block.

THE SESSION KEY
    `eb.rsplit('_', 1)[0]`, the same key `bookkeep_r13.py` uses, which is the
    execution block's identifier with its own trailing component removed.  H1
    requires the two subsets to partition the reserved blocks and requires the
    sharing count to reproduce the published \BkSessHoBlocks, so the key here
    cannot drift from the key there.

WHY THE FULL-SAMPLE VALUES ARE RECOMPUTED TOO
    A subset number is only comparable with a published number if the same
    code produced both.  H2 recomputes the published rank median, fine-window
    trigger count, expectation and ratio, and fails if any of them disagrees
    with the macro layer -- so the subset figures below are the published
    quantities restricted, and not a second definition of them.

ASSERTIONS (each driven; `--drive N`)
    H1  the session split partitions the reserved blocks and reproduces the
        published sharing count                                   (drive 1)
    H2  the full-sample values reproduce the published macros      (drive 2)
    H3  the trigger-level comparison decomposes over the two subsets, and
        both subsets are non-empty in windows                      (drive 3)
    H4  every sentence that calls the reserved hold-out unseen or out of
        sample carries the session-sharing qualification           (drive 4)

Inputs, all read: `holdout_export_v381.json`, `per_target_results_v3.99.csv`,
`tab_holdout_v412.tex`, the manuscript section files, and the macro layer for
the counts other generators own.

    python3 holdsess_r19.py [--drive N]
"""
import collections
import csv
import glob
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
#: the version directory is this file's own once the integrator has copied it
#: in; while it is being written it is the sandbox beside it
PAPER = (HERE if glob.glob(os.path.join(HERE, 'technosignatures_*.tex'))
         else os.path.join(HERE, 'sandbox'))

ROUND = 850
TRIG = 5.0
NPROBE = 512
NBOOT = 20000
SEED = 850
COV_LOQ, COV_HIQ = 2.5, 97.5
COV_PCT = COV_HIQ - COV_LOQ

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])

#: the production name is a literal and only the drive branch is built by
#: format, so `roundcollide` can resolve the claim on round 850
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round850.tex' if DRIVE is None
                       else 'numbers/survey_numbers_round850_drive%d.tex' % DRIVE)
OUT_JSON = os.path.join(HERE, 'holdsess_r19%s.json'
                        % ('' if DRIVE is None else '_drive%d' % DRIVE))

OUT = []
fail = []


def m(name, val):
    assert name.isalpha(), 'a macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-68s %s  %s' % (label[:68], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """The value the macro layer publishes, in \\input order so a later
    \\renewcommand wins."""
    main = glob.glob(os.path.join(PAPER, 'technosignatures_*.tex'))
    order = []
    if len(main) == 1:
        for ln in open(main[0], errors='ignore'):
            mm = re.match(r'\s*\\input\{(?:numbers/)?(survey_numbers[A-Za-z0-9_]*)\}', ln)
            if mm:
                order.append(mm.group(1) + '.tex')
    val = None
    for fn in order:
        p = os.path.join(PAPER, 'numbers', fn)
        if not os.path.exists(p):
            continue
        for ln in open(p, errors='ignore'):
            for nm, vv in re.findall(
                    r'\\(?:providecommand|renewcommand|newcommand)'
                    r'\{?\\([A-Za-z]+)\}?\{([^{}]*)\}', ln):
                if nm == name and vv.strip():
                    val = vv.strip()
    assert val is not None, 'no generator publishes \\%s' % name
    return val


# =====================================================================
# inputs
# =====================================================================
HOL = json.load(open(os.path.join(PAPER, 'holdout_export_v381.json')))['rows']
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))

ROWS = [r for r in HOL if r.get('ctrl_all') and r.get('star_snr') is not None]


def session(eb):
    """The observing session an execution block belongs to: ALMA's block
    identifier with its own trailing component removed.  The same key
    `bookkeep_r13.py` uses, and H1 requires the two to agree."""
    if DRIVE == 1:
        return eb                       # the block passed off as the session
    return eb.rsplit('_', 1)[0]


CEN_SESS = {session(r['eb']) for r in CAT}
HO_EB = {r['eb'] for r in ROWS}
SHARE_EB = {e for e in HO_EB if session(e) in CEN_SESS}
IND_EB = HO_EB - SHARE_EB
SHARED_SESS = CEN_SESS & {session(e) for e in HO_EB}


def indep(r):
    return r['eb'] in IND_EB


ALL_R = ROWS
IND_R = [r for r in ROWS if indep(r)]
SHARE_R = [r for r in ROWS if not indep(r)]
if DRIVE == 3:
    IND_R = []                          # one subset empties


# =====================================================================
# (1) the rank displacement
# =====================================================================
def ranks(rows):
    """The add-one rank of the star against its own window's control probes,
    over the rows that retain a complete control vector."""
    out = []
    for r in rows:
        c = np.asarray(r['ctrl_all'], float)
        if c.size != NPROBE or not np.all(np.isfinite(c)):
            continue
        out.append(_rank(c, r['star_snr']))
    return np.array(sorted(out))


def _rank(c, star):
    """The add-one rank.  Drive 2 drops the add-one and raises the trigger,
    which is the family of small redefinitions that make a subset figure
    incomparable with the published one -- H2 exists to catch exactly that."""
    if DRIVE == 2:
        return float((c >= star).sum()) / c.size
    return (1 + int((c >= star).sum())) / (c.size + 1.0)


def _trig():
    return TRIG + 0.1 if DRIVE == 2 else TRIG


RNG = np.random.default_rng(SEED)


def rank_med(rows):
    """The median rank and its block-clustered interval, because blocks share
    weather, calibration and correlator setup."""
    byb = collections.defaultdict(list)
    for r in rows:
        c = np.asarray(r['ctrl_all'], float)
        if c.size != NPROBE or not np.all(np.isfinite(c)):
            continue
        byb[r['eb']].append(_rank(c, r['star_snr']))
    if not byb:
        return None, None, None, 0
    keys = list(byb)
    meds = []
    for _ in range(2000):
        pick = RNG.integers(0, len(keys), len(keys))
        meds.append(np.median([x for i in pick for x in byb[keys[i]]]))
    lo, hi = np.percentile(meds, [COV_LOQ, COV_HIQ])
    return (float(np.median([x for v in byb.values() for x in v])),
            float(lo), float(hi), sum(len(v) for v in byb.values()))


R_ALL = rank_med(ALL_R)
R_IND = rank_med(IND_R)
R_SHARE = rank_med(SHARE_R)


# =====================================================================
# (2) the trigger-level ratio -- the quantity the step is checked against
# =====================================================================
def ho_rate(rows):
    """Observed stellar trigger events and the number the same windows' own
    control positions predict.  `stats_v413.py`'s definition."""
    obs = [r for r in rows if float(r['star_snr']) >= _trig()]
    exp = sum(sum(1 for x in r['ctrl_all'] if x >= _trig())
              / float(len(r['ctrl_all'])) for r in rows)
    return len(obs), exp, obs


def fine(rows):
    return [r for r in rows if r['res'].startswith('fine')]


def coarse(rows):
    return [r for r in rows if not r['res'].startswith('fine')]


A_OBS, A_EXP, A_HITS = ho_rate(fine(ALL_R))
I_OBS, I_EXP, I_HITS = ho_rate(fine(IND_R)) if fine(IND_R) else (0, 0.0, [])
S_OBS, S_EXP, S_HITS = ho_rate(fine(SHARE_R))
AC_OBS, AC_EXP, _ = ho_rate(coarse(ALL_R))
A_RATIO = A_OBS / A_EXP if A_EXP else None
I_RATIO = I_OBS / I_EXP if I_EXP else None
S_RATIO = S_OBS / S_EXP if S_EXP else None
#: a subset holding no event neither agrees with a step nor disagrees with one.
#: What can be said is how likely that emptiness is at the control rate, and
#: at the control rate TIMES the step, so the reader can see that the subset is
#: uninformative rather than discrepant.
STEP = float(texval('CeStep'))
P_NONE = math.exp(-I_EXP) if I_EXP else None
P_NONE_STEP = math.exp(-I_EXP * STEP) if I_EXP else None


# =====================================================================
# (3) Table 7's dispositions
# =====================================================================
#: Read from the printed table, so that what is qualified is what a reader
#: sees, and keyed on the block identifier the table prints.
TABLE = open(os.path.join(PAPER, 'tab_holdout_v412.tex')).read()
TAB_EB = re.findall(r'&\s*(X[0-9a-f]+\\_X[0-9a-f]+)\s*&', TABLE)
TAB_EB = ['A002_' + e.replace('\\_', '_') for e in TAB_EB]
TAB_IND = [e for e in TAB_EB if e in IND_EB]
TAB_SHARE = [e for e in TAB_EB if e in SHARE_EB]

# =====================================================================
# what was found
# =====================================================================
print('holdsess_r19: round %d%s' % (ROUND, '' if DRIVE is None
                                    else '  (drive %d)' % DRIVE))
print('  the split: %d reserved blocks, %d sharing a session with the census '
      'across %d sessions, %d sharing none (%.0f per cent shared)'
      % (len(HO_EB), len(SHARE_EB), len(SHARED_SESS), len(IND_EB),
         100.0 * len(SHARE_EB) / len(HO_EB)))
for nm, sub, rk, o, e, ra in (
        ('all reserved', ALL_R, R_ALL, A_OBS, A_EXP, A_RATIO),
        ('session-independent', IND_R, R_IND, I_OBS, I_EXP, I_RATIO),
        ('session-sharing', SHARE_R, R_SHARE, S_OBS, S_EXP, S_RATIO)):
    print('  %-20s %3d windows (%d fine, %d coarse) in %2d blocks toward %2d '
          'stars; rank median %s (%s-%s); trigger %d observed against %.2f '
          'predicted, ratio %s'
          % (nm, len(sub), len(fine(sub)), len(coarse(sub)),
             len({r['eb'] for r in sub}), len({r['star_name'] for r in sub}),
             'n/a' if rk[0] is None else '%.3f' % rk[0],
             'n/a' if rk[1] is None else '%.3f' % rk[1],
             'n/a' if rk[2] is None else '%.3f' % rk[2],
             o, e, 'n/a' if ra is None else '%.3f' % ra))
print('  the session-independent subset holds no trigger event: the chance of '
      'that at the control rate is %s, and %s at the control rate times the '
      'step %s -- uninformative, not discrepant'
      % ('n/a' if P_NONE is None else '%.3f' % P_NONE,
         'n/a' if P_NONE_STEP is None else '%.3f' % P_NONE_STEP,
         '%.3f' % STEP))
print('  Table 7: %d rows, %d from a session-independent block, %d from a '
      'session-sharing one' % (len(TAB_EB), len(TAB_IND), len(TAB_SHARE)))

# =====================================================================
# (4) the prose qualification
# =====================================================================
#: ★ A VALUE GATE AND A PROSE GATE ARE DIFFERENT GATES.  Measuring the subsets
#: does not put them on the page.
#:
#: ★★ AND IT IS KEYED ON THE MACROS, NOT ON ENGLISH.  The first form of this
#: check looked for the words "never seen" and "out of sample".  Both
#: sentences were then rewritten without those words -- which is a legitimate
#: edit and leaves the check guarding nothing at all: a gate that a rewording
#: can satisfy is a gate that cannot fail.  What the requirement is actually
#: about is the three quantities the reserved blocks CALIBRATE: the rank
#: displacement, the trigger-level ratio the step is checked against, and the
#: expectation behind it.  So every paragraph that quotes one of those must
#: also carry the session-sharing qualification, in whatever words.
_CALMAC = re.compile(r'\\(?:HoRankMed|StHoObs|StHoRatio|StHoNFine'
                     r'|StHoExpFine)\b')
_SESSMAC = re.compile(r'\\(?:BkSessHoBlocks|HsIndBlocks|HsSharePct'
                      r'|HsIndRankMed|HsIndObs|HsShareRatio)\b')
UNQUAL = []
for p in sorted(glob.glob(os.path.join(PAPER, 'sections', '*.tex'))):
    body = re.sub(r'(?m)^\s*%%.*$', '', open(p, errors='ignore').read())
    for para in re.split(r'\n\s*\n', body):
        q = ' '.join(para.split())
        if DRIVE == 4:
            q = _SESSMAC.sub('', q)     # the qualification is edited out
        if _CALMAC.search(q) and not _SESSMAC.search(q):
            UNQUAL.append((os.path.basename(p), q[:150]))
print('  prose: %d paragraph(s) quote what the reserved blocks calibrate '
      'without the session-sharing qualification' % len(UNQUAL))
for f, s in UNQUAL:
    print('     %-24s %s' % (f, s))

# =====================================================================
# assertions
# =====================================================================
print('\nassertions')
ck('H1 THE SESSION SPLIT PARTITIONS THE RESERVED BLOCKS AND REPRODUCES THE '
   'PUBLISHED SHARING COUNT, so the session key here cannot drift from the '
   'one that measured it',
   len(SHARE_EB) + len(IND_EB) == len(HO_EB)
   and len(HO_EB) == int(texval('NEbHeldOut')) == int(texval('HoBlocks'))
   and len(SHARE_EB) == int(texval('BkSessHoBlocks'))
   and len(SHARED_SESS) == int(texval('BkSessShared'))
   and 0 < len(IND_EB) < len(HO_EB)
   and abs(COV_PCT - float(texval('CeCovPct'))) < 1e-9,
   '%d + %d = %d against the published %s; %d shared sessions against %s; '
   'coverage %.0f against the published %s'
   % (len(SHARE_EB), len(IND_EB), len(HO_EB), texval('NEbHeldOut'),
      len(SHARED_SESS), texval('BkSessShared'), COV_PCT,
      texval('CeCovPct')))

ck('H2 THE FULL-SAMPLE VALUES REPRODUCE THE PUBLISHED MACROS, so every subset '
   'figure below is a published quantity restricted and not a second '
   'definition of it',
   abs(R_ALL[0] - float(texval('HoRankMed'))) < 5e-4
   and R_ALL[3] == int(texval('HoWin'))
   and A_OBS == int(texval('StHoObs'))
   and abs(A_EXP - float(texval('StHoExpFine'))) < 0.05
   and abs(A_RATIO - float(texval('StHoRatio'))) < 5e-3
   and len(fine(ALL_R)) == int(texval('StHoNFine'))
   and len(coarse(ALL_R)) == int(texval('StHoNCoarse')),
   'rank median %.3f against %s on %d of %s windows; trigger %d against %s, '
   'expectation %.2f against %s, ratio %.3f against %s; %d fine / %d coarse '
   'against %s / %s'
   % (R_ALL[0], texval('HoRankMed'), R_ALL[3], texval('HoWin'), A_OBS,
      texval('StHoObs'), A_EXP, texval('StHoExpFine'), A_RATIO,
      texval('StHoRatio'), len(fine(ALL_R)), len(coarse(ALL_R)),
      texval('StHoNFine'), texval('StHoNCoarse')))

ck('H3 THE TRIGGER-LEVEL COMPARISON DECOMPOSES OVER THE TWO SUBSETS and both '
   'hold windows, so a subset that carries no event is seen to carry none '
   'rather than being absent from the accounting',
   I_OBS + S_OBS == A_OBS
   and abs((I_EXP + S_EXP) - A_EXP) < 1e-9
   and len(IND_R) > 0 and len(SHARE_R) > 0
   and len(fine(IND_R)) > 0
   and len(TAB_IND) + len(TAB_SHARE) == len(TAB_EB) == A_OBS,
   '%d + %d = %d events, %.3f + %.3f = %.3f expected; %d and %d windows; '
   'Table 7 %d + %d = %d rows'
   % (I_OBS, S_OBS, A_OBS, I_EXP, S_EXP, A_EXP, len(IND_R), len(SHARE_R),
      len(TAB_IND), len(TAB_SHARE), len(TAB_EB)))

ck('H4 EVERY PARAGRAPH THAT QUOTES WHAT THE RESERVED BLOCKS CALIBRATE '
   'CARRIES THE SESSION-SHARING QUALIFICATION',
   not UNQUAL, '%d unqualified: %s'
   % (len(UNQUAL), '; '.join(f for f, _ in UNQUAL) or 'none'))

# =====================================================================
# macros
# =====================================================================
m('HsIndBlocks', '%d' % len(IND_EB))
m('HsShareBlocks', '%d' % len(SHARE_EB))
m('HsShareSess', '%d' % len(SHARED_SESS))
m('HsSharePct', '%.0f' % (100.0 * len(SHARE_EB) / len(HO_EB)))
m('HsIndWin', '%d' % len(IND_R))
m('HsIndFine', '%d' % len(fine(IND_R)))
m('HsIndCoarse', '%d' % len(coarse(IND_R)))
m('HsIndStars', '%d' % len({r['star_name'] for r in IND_R}))
m('HsIndRankMed', '%.3f' % R_IND[0])
m('HsIndRankLo', '%.3f' % R_IND[1])
m('HsIndRankHi', '%.3f' % R_IND[2])
m('HsShareRankMed', '%.3f' % R_SHARE[0])
m('HsIndObs', '%d' % I_OBS)
m('HsIndObsWord', ['no', 'one', 'two', 'three', 'four'][min(4, I_OBS)])
# ★★ THE WORD ABOVE IS A DETERMINER AND NEEDS A NOUN AFTER IT.  At I_OBS = 0
# it prints "no", and one of the two sentences that use it had no noun, so it
# typeset as "the 28 reserved blocks that share none hold no between them" --
# grammatical nonsense that no gate can see, and it reads that way at the
# only value this quantity takes.  The noun is emitted here so that both
# sentences are English at every value and not only at this one.
m('HsIndObsNoun', 'event' if I_OBS == 1 else 'events')
m('HsIndExp', '%.1f' % I_EXP)
m('HsIndPNone', '%.2f' % P_NONE)
m('HsShareObs', '%d' % S_OBS)
m('HsShareExp', '%.1f' % S_EXP)
m('HsShareRatio', '%.2f' % S_RATIO)
m('HsIndDispo', '%d' % len(TAB_IND))
m('HsIndDispoWord', ['none', 'one', 'two', 'three', 'four'][min(4, len(TAB_IND))])
#: the coverage is ONE quantity and is published ONCE, by `chance_v414.py`
#: as \CeCovPct; H1 asserts that this file's own coverage is the same
#: number, so the two cannot drift apart.  `valuetwin.py` found the
#: second name within an hour of its being written.

# =====================================================================
# write
# =====================================================================
if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    if DRIVE is None:
        raise SystemExit(1)

hdr = ['%% GENERATED by holdsess_r19.py (round %d) -- do not hand-edit.' % ROUND,
       '%% The reserved hold-out split at SESSION level: the rank',
       '%% displacement, the trigger-level ratio the step is checked',
       '%% against, and Table 7\'s dispositions, re-measured on the reserved',
       '%% blocks that share no observing session with the census.']
with open(OUT_TEX, 'w') as fh:
    fh.write('\n'.join(hdr + sorted(OUT)) + '\n')
json.dump(dict(round=ROUND, drive=DRIVE, seed=SEED, coverage_pct=COV_PCT,
               n_reserved_blocks=len(HO_EB),
               n_session_sharing_blocks=len(SHARE_EB),
               n_session_independent_blocks=len(IND_EB),
               n_shared_sessions=len(SHARED_SESS),
               session_independent_blocks=sorted(IND_EB),
               rank_all=R_ALL, rank_independent=R_IND, rank_sharing=R_SHARE,
               trigger_all=[A_OBS, A_EXP, A_RATIO],
               trigger_independent=[I_OBS, I_EXP, I_RATIO],
               trigger_sharing=[S_OBS, S_EXP, S_RATIO],
               coarse_all=[AC_OBS, AC_EXP],
               p_none_independent=P_NONE,
               p_none_independent_with_step=P_NONE_STEP,
               step_used=STEP,
               table_blocks=TAB_EB, table_independent=TAB_IND,
               table_sharing=TAB_SHARE,
               prose_unqualified=UNQUAL),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('\nwrote %s (%d macros) and %s'
      % (os.path.basename(OUT_TEX), len(OUT), os.path.basename(OUT_JSON)))
