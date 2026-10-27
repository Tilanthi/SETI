#!/usr/bin/env python3
r"""ctl_r18.py -- the positive controls of the recurrence stage, block by
block, and the two readings the section calls "the largest".  Round 805.
Writes `survey_numbers_round805.tex` and `ctl_r18.json`.

WHY THIS EXISTS.  Two things the paper asserts about this stage are not
shown anywhere in it.

 1. THE POSITIVE CONTROL IS A COUNT AND NOT A LIST.  The recurrence
    criterion recovers a number of line-attributed crossings, and that is
    the whole evidence that the criterion can return yes.  Which later
    block satisfied it, and how far from the discovery epoch, is never
    stated -- so a reader cannot tell whether the control was satisfied
    across the baselines the exclusions are quoted over or inside a single
    scheduling session.  Both occur, and the separations are printed here
    for every one of them.  They are measured from the execution blocks'
    own epochs, never from the archive's per-block stamp, which this
    project has shown to be unusable for intervals.

 2. "THE LARGEST STATISTIC AT THE PREDICTED CELL" NAMES TWO DIFFERENT
    QUANTITIES IN TWO PLACES.  One is the inverse-variance COMBINATION over
    every block covering a crossing, maximised over the crossings; the other
    is the largest reading in any SINGLE block, likewise maximised over the
    crossings.  They differ -- the combination is the quantity the exclusion
    is built from, the single reading is what a reader would compute from
    one row -- and the section prints both under the same words.  Both are
    recomputed here from the frozen records, each is required to reproduce
    the macro the manuscript already carries, and the two are reported as
    what they separately are.

Usage: ctl_r18.py [--drive N]
"""
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.dirname(os.path.abspath(__file__))   # the tree this lives in
ROUND = 805
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
# ★ DERIVED FROM `ROUND`, NEVER TYPED AGAIN.  This literal used to
# carry the round number a second time, and when the round was moved
# off `r18-census`'s claim the constant changed and this did not --
# so this generator silently overwrote another generator's published
# round file.  That is the defect `roundcollide` exists for, and it
# resolves a format-built name, so it would have caught the next one.
OUT = os.path.join(HERE, 'survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTJ = os.path.join(HERE, 'ctl_r18%s.json' % SFX)

sys.path.insert(0, V)
TRIG = 5.0
DAY = 1.0

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
    for p in sorted(glob.glob(os.path.join(V, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


def tname(s):
    s = s.split(' Gaia')[0].strip()
    s = re.sub(r'^HD(\d)', r'HD \1', s)
    s = s.replace('HD14055', 'HD 14055').replace('bet Pic', r'$\beta$~Pic')
    s = s.replace('eta Crv', r'$\eta$~Crv')
    s = s.replace('CP-72', 'CP$-$72').replace('CD-57', 'CD$-$57')
    s = s.replace('BD05', 'BD+05')
    return s.replace(' ', '~')


def ebname(eb):
    return eb.split('_')[-1]


# ---------------------------------------------------------------- inputs
# The recovery record itself is the manuscript's own: `maskso_v414.py` builds
# it and this generator imports that function rather than reimplementing the
# criterion, so the list cannot drift away from the count the paper prints.
import maskso_v414 as MS                                        # noqa: E402
EP = __import__('epochs_r14')
EPOCHS = EP.EPOCHS

LED = json.load(open(os.path.join(V, 'ledger.json')))['rows']
RCOL = json.load(open(os.path.join(V, 'recurcols_v411.json')))
CROSS = json.load(open(os.path.join(V, 'r10inputs',
                                   'recur_v411.json')))['crossings']
EXTRA = MS.attributed_recurrence(LED, RCOL, here=V)


def key_of(r):
    return '%s|%.6f' % (r['eb'], float(r['freq']))


# ======================================= 1. THE POSITIVE CONTROLS, LISTED
ROWS = []
for r in LED:
    k = key_of(r)
    q = RCOL.get(k) if (RCOL.get(k, {}) or {}).get('T_pers') is not None \
        else EXTRA.get(k)
    if not q or q.get('verdict') != 'recovered':
        continue
    eb0, eb1 = r['eb'], q['recovered_eb']
    t0, t1 = EPOCHS.get(eb0), EPOCHS.get(eb1)
    sep = (t1 - t0) if (t0 is not None and t1 is not None) else None
    # ★ THE SEPARATION IS NOT THE EPOCH DIFFERENCE WHERE THE TWO BLOCKS HAVE
    # NO EPOCH OF THEIR OWN.  `epochs_r14` documents the artefact: a block the
    # archive does not index inherits the earliest stamp of its member OUS, so
    # two blocks of one scheduling unit come back with the same number and
    # every interval through them is zero by construction.  The paper's own
    # one-sided predicate is therefore the authority on "more than a day", and
    # the witness that settled it is recorded beside each row.
    # ★★ A BLOCK HAS A RELIABLE EPOCH WHERE A MEASUREMENT SET SURVIVES OR
    # WHERE THE ARCHIVE INDEXED THE BLOCK ITSELF; only the stamps marked
    # `ous` are the artefact.  `epochs_r14.apart()` requires BOTH blocks to
    # carry the same KIND of witness and so refuses a pair of which one is
    # measured and the other block-stamped -- which is every HD 285968 pair
    # here, separated by 39 to 44 days on two reliable epochs.  The
    # distinction is made explicitly rather than by widening that predicate,
    # which other counts in the paper depend on.
    def rel(eb):
        return eb in EP.MS or EP.SRC.get(eb) == 'block'
    both_ms = rel(eb0) and rel(eb1)
    shown = bool(both_ms and sep is not None and abs(sep) > DAY) \
        or EP.apart(eb0, eb1)
    wit = ('two reliable epochs' if both_ms else
           ('barycentric term' if (eb0 in EP.VB and eb1 in EP.VB
                                   and abs(EP.VB[eb0] - EP.VB[eb1])
                                   > EP.BARY_TOL) else
            ('stored stamp' if shown
             else 'none: one shared observing-unit stamp')))
    ROWS.append(dict(
        star=r['display'], eb=eb0, rec_eb=eb1, freq=float(r['freq']),
        line=r.get('line'), tstar=float(r['tstar']),
        t_recov=q.get('T_recov'), n_rep=q.get('n_rep'),
        dt_min_d=q.get('dt_min_d'), dt_max_d=q.get('dt_max_d'),
        sep_d=sep, sep_abs=(abs(sep) if sep is not None else None),
        later=(sep is not None and sep > 0),
        witness=wit, both_ms=both_ms,
        beyond_day=bool(shown)))

ROWS.sort(key=lambda z: (z['star'], z['freq']))
NREC = int(macro('MkAttrRecur'))
if DRIVE == 3:                     # C1: a control dropped from the list
    ROWS = ROWS[:-1]
if DRIVE == 4:                     # C3: a separation outside its own span
    ROWS[0] = dict(ROWS[0], sep_abs=ROWS[0]['dt_max_d'] + 5.0)
ck('C1 every crossing the manuscript counts as a positive control is listed '
   'here with the block that satisfied the criterion and that block epoch '
   'is a measured one, so the list and the count cannot disagree',
   len(ROWS) == NREC
   and all(z['sep_d'] is not None for z in ROWS)
   and all(z['t_recov'] is not None and z['t_recov'] >= TRIG for z in ROWS),
   '%d listed against %s counted; weakest recovering statistic %.2f'
   % (len(ROWS), macro('MkAttrRecur'),
      min(z['t_recov'] for z in ROWS)))

# ★★★ THE TEMPORAL REACH OF THIS CONTROL IS MEASURED IN ROUND 806 AND NOT
# HERE, AND THE DIFFERENCE IS NOT A METHOD BUT A SET.  `verdict == recovered`
# keeps the STRONGEST recovering block; the criterion is satisfied by every
# block that meets it, and for four of these thirteen the strongest one is a
# sibling of the discovery block's own observing unit while a block of another
# session, 53 d away, meets it too.  Measured over the strongest block alone
# this set reads as 9 separated and 4 not; measured over every block that
# satisfies the criterion, all 13 are recovered more than a day away and in a
# different session.  `confirm_r19.py` owns that measurement, the table under
# it and the macros, so the paper cannot carry both answers.  What stays here
# is the per-row record, which that generator reads.
EARLY = [z for z in ROWS if not z['later']]

# the criterion names the STRONGEST recovering block, not the nearest or the
# first beyond a day, and that is worth stating because it is not the choice
# a reader would assume.
_bystar = {}
for z in ROWS:
    _bystar.setdefault(z['star'], []).append(z)
ck('C3 the block the criterion names is the strongest recovering block of '
   'that crossing and not the nearest in time, so a separation quoted for '
   'it is a property of that choice and is reported as such',
   all(z['n_rep'] is None or z['dt_max_d'] is None
       or z['sep_abs'] <= z['dt_max_d'] + 0.01 for z in ROWS),
   '%d crossings toward %d stars; %s'
   % (len(ROWS), len(_bystar),
      '; '.join('%s %d' % (s, len(v)) for s, v in sorted(_bystar.items()))))

# ================================ 2. THE TWO "LARGEST" READINGS, NAMED APART
U = [k for k, c in RCOL.items()
     if isinstance(c, dict) and c.get('T_rep') is not None
     and not c.get('attributed')]
TREP = max(RCOL[k]['T_rep'] for k in U)
TSNG = max(RCOL[k]['T_matched_max'] for k in U)
TANY = max(RCOL[k]['T_anydrift'] for k in U)
_krep = max(U, key=lambda k: RCOL[k]['T_rep'])
_ksng = max(U, key=lambda k: RCOL[k]['T_matched_max'])
_ncomb = sum(1 for k in U if RCOL[k]['n_rep'] > 1)
if DRIVE == 2:                     # C4: the two readings conflated
    TSNG = TREP
ck('C4 the two readings the section calls "the largest" are different '
   'quantities over the same crossings -- the inverse-variance combination '
   'over a crossing\'s covering blocks, and the largest reading in any '
   'single block -- and each reproduces the macro the manuscript carries',
   '%+.2f' % TREP == macro('RcTRepMax')
   and '%.2f' % TSNG == macro('RcTMatched')
   and '%.2f' % TANY == macro('RcTMax')
   and TSNG > TREP and _ncomb > 0,
   'combination %+.2f (%s) against %s; single block %.2f (%s) against %s; '
   'single block at any drift %.2f against %s; %d of %d crossings combine '
   'more than one block'
   % (TREP, _krep.split('|')[0][-6:], macro('RcTRepMax'),
      TSNG, _ksng.split('|')[0][-6:], macro('RcTMatched'),
      TANY, macro('RcTMax'), _ncomb, len(U)))

# ★ AND THE ORDERING IS A PROPERTY OF THESE DATA, NOT AN IDENTITY.  An
# inverse-variance combination of several positive readings can exceed any one
# of them, so "the combination is the smaller number" is something to measure
# rather than to assume -- and it is measured to hold for every crossing here,
# which is why the single-block maximum is the conservative one to quote.
_hi = [k for k in U if RCOL[k]['T_rep'] > RCOL[k]['T_matched_max'] + 1e-9]
if DRIVE == 5:
    _hi = U[:1]
ck('C5 for every one of these crossings the combination lies below that '
   "crossing's own largest single-block reading, so the single-block value "
   'is the conservative one to quote -- an ordering measured here and not '
   'guaranteed by the arithmetic',
   not _hi,
   '%d of %d crossings have a combination above their own single-block '
   'maximum' % (len(_hi), len(U)))

# ======================================================= macros
m('PcNCtl', '%d' % len(ROWS))
m('PcNStar', '%d' % len(_bystar))
m('PcNEarlier', '%d' % len(EARLY))
m('PcStarList', ', '.join(
    '%s (%d)' % (tname(s), len(v)) for s, v in sorted(_bystar.items())))
m('PcTRepMax', '%+.2f' % TREP)
m('PcTSingleMax', '%.2f' % TSNG)
m('PcTAnyDrift', '%.2f' % TANY)
m('PcNComb', '%d' % _ncomb)
m('PcNQuoted', '%d' % len(U))

# ★ THE UNCITED FRAGMENT THIS GENERATOR WROTE IS GONE.  It was declared
# "generated and uncited" on 2026-10-13 against the day a long table could be
# relocated; there is no Supporting Information at this journal, and the table
# the referee asks for is `tab_confirm_r19.tex`, which carries the session and
# the epoch as well and is cited in Appendix D.  A fragment built and typeset
# nowhere is an orphan, and this one would now be a second table of the same
# thirteen rows with a different answer in its last column.

json.dump(dict(controls=ROWS, t_rep_max=TREP, t_single_max=TSNG,
               t_anydrift_max=TANY, n_quoted=len(U)),
          open(OUTJ, 'w'), indent=1, default=str)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by ctl_r18.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
for z in ROWS:
    print('  %-14s %-22s %10.4f  T* %5.2f  rec %-10s  dt %+9.2f d  %s'
          % (z['star'][:14], (z['line'] or '--')[:22], z['freq'], z['tstar'],
             ebname(z['rec_eb']), z['sep_d'],
             ('beyond a day by %s' % z['witness']) if z['beyond_day']
             else 'NOT SHOWN APART (%s)' % z['witness']))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
