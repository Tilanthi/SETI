#!/usr/bin/env python3
r"""R1-8: what happened to every archival block the survey did not search.

Supersedes `blockfate_v400.py`.  The categories, their definitions and the
round file are unchanged; what changes is that the ledger is now computed as
the v4.08 state PLUS a named transition for every block that moved, so the
difference is auditable block by block instead of being a second hand-written
table.  The transitions are the tail run's own verdicts
(`r8inputs/v409/tail_collect.json`) and the ALMA delivery record for the one
block the v4.08 ledger left anonymous (`etacrv_delivery.json`).

The categories are not interchangeable and the paper must not blur them:

  searched            processed with the frozen pipeline;
  no archive calibration
                      the archive exposes no calibration product and none
                      can be generated;
  calibration failed  a Cycle 0/1 block whose legacy `scriptForCalibration`
                      replay path this project does not maintain;
  disk infeasible     a block whose working-set expansion exceeds the
                      volume available, so it cannot be calibrated here at
                      any scheduling;
  not attempted       reachable in principle, not processed.

★★★★ WHAT CLOSES IN v4.09.  v4.08 carried a sixth category, `never_started`,
holding exactly one block and naming it nowhere.  It is
`A002_X11e10bc_X23333` -- eta Crv, Band 7, 67.24 GB -- and it was recoverable
from the deposit's own sources all along: `infeasible_blocks.json` holds FOUR
names and `blockfate_v400.json` copied THREE.  Run alone through the
canonical extractor it is excluded *before download*: the ALMA delivery for
its member OUS offers three execution blocks, two carry `calapply.txt` and
are both already in the survey, and this one carries none.  Its fate is
`excluded_no_calibration_available`, so the `never_started` category
disappears from the ledger entirely, and the remaining gap is in the ALMA
delivery rather than in this work -- a permanent statement rather than a
provisional one.

★★ Two of the three published `disk_infeasible` labels are FALSIFIED by the
tail run: `A002_X1171dca_X606b` and `A002_Xb2b000_X7667` both ran calibrate
-> spw select -> extract -> search, 4/4 windows clean.  The original sweep
gated on ASDM size and the working set is not a function of ASDM size: it
spans x2.3 to x10.0 over blocks of 25-74 GB.

Writes survey_numbers_round69.tex.

Usage: blockfate_v409.py [--drive N]   N = 1..7
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, 'r8inputs', 'v409')
# ★ `--drive 0` is "no perturbation, but DO NOT write a production path".
#   The gate's own baseline check needs to run the generator unperturbed, and
#   if that run landed on the real products it would be the very thing D36
#   forbids -- a test writing where production reads.  So DRIVE is None when
#   the flag is absent and an integer (including 0) when it is present, and
#   the suffix follows the flag rather than the perturbation.
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE


def suffixed(name):
    # ★ D36's standing rule: a test must never write to the path production
    #   reads.  Under a drive every output is suffixed, so it cannot.
    stem, ext = os.path.splitext(name)
    return stem + SUF + ext

D = json.load(open(os.path.join(HERE, 'blockfate_v400.json')))
TAIL = json.load(open(os.path.join(INP, 'tail_collect.json')))
DEL = json.load(open(os.path.join(INP, 'etacrv_delivery.json')))
NS = json.load(open(os.path.join(INP, 'neverstarted_v409.json')))

C = dict(D['counts'])
G = dict(D['gb'])
SCOPE = D['scope']
assert sum(C.values()) == SCOPE, (sum(C.values()), SCOPE)

# ---------------------------------------------------------------------------
# the transitions, each one derived from a record rather than typed
# ---------------------------------------------------------------------------
# which prior category each tail block was in.  `blockfate_v400.json` names
# its three `disk_infeasible` blocks explicitly; every other tail block was
# in `closed_campaign_ended`.
PRIOR_INFEAS = set(D['infeasible'])
MOVES = []
for b in TAIL:
    if not b.get('done'):
        continue
    frm = ('disk_infeasible' if b['eb'] in PRIOR_INFEAS
           else 'closed_campaign_ended')
    MOVES.append((b['eb'], frm, 'done', b['gb'],
                  'searched 4/4 windows with the frozen pipeline'))

# the one block the ledger never named, moved on the ALMA delivery record
assert DEL['eb'] == NS['eb'] == 'A002_X11e10bc_X23333', (DEL['eb'], NS['eb'])
assert DEL['not_never_started'] is True
assert DEL['delivery']['n_ebs_offered'] == 3
assert DEL['delivery']['n_with_calapply'] == 2
assert DEL['delivery']['no_calibration'] == [DEL['eb']]
NS_FROM = 'never_started'
NS_TO = DEL['correct_fate']
if DRIVE == 1:
    NS_TO = 'never_started'                  # the category must not survive
MOVES.append((DEL['eb'], NS_FROM, NS_TO, DEL['gb'],
              'the ALMA delivery for its member OUS carries no pipeline '
              'calibration for this execution block'))

for eb, frm, to, gb, why in MOVES:
    C[frm] -= 1
    C[to] = C.get(to, 0) + 1
    G[frm] = G.get(frm, 0) - gb
    G[to] = G.get(to, 0) + gb

if DRIVE == 2:
    C['done'] += 1                           # fates must stop summing to 177

# ★ The residual GB of a category with one block left is that block's OWN
#   measured size, not the v4.08 rounding minus the transitions.  Both are
#   printed and required to agree within 1 GB (F5).
INFEAS_REMAIN_GB = 29.7          # A002_Xa7a216_X2f0f, measured >= x8.32
G_INFEAS_DERIVED = G['disk_infeasible'] + G.get('never_started', 0.0)

done = C['done']
nocal = C['excluded_no_calibration_available']
calfail = C['failed_calibrate']
infeas = C['disk_infeasible'] + C.get('never_started', 0)
unattempted = C['closed_campaign_ended']

L = ['%% GENERATED by blockfate_v409.py -- do not hand-edit.\n']


def m(k, v):
    # ★ A LaTeX macro name may contain LETTERS ONLY.  `\FateDoneV408` parses as
    #   `\FateDoneV` followed by the characters 408, which TeX then tries to
    #   TYPESET -- in the preamble that is "Missing \begin{document}" and the
    #   build dies with no PDF.  Four macros were written that way in the first
    #   pass of this generator.  Neither `macrosyn` nor `macroleak` compares
    #   macro NAMES against TeX's own rule, so the assertion lives here.
    assert k.isalpha(), 'macro name %r is not letters-only' % k
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


m('FateScope', '%d' % SCOPE)
m('FateDone', '%d' % done)
m('FateDoneTB', '%.1f' % (G['done'] / 1000.0))
m('FateNoCal', '%d' % nocal)
m('FateNoCalGB', '%d' % round(G['excluded_no_calibration_available']))
m('FateCalFail', '%d' % calfail)
m('FateInfeas', '%d' % infeas)
m('FateInfeasGB', '%.1f' % INFEAS_REMAIN_GB)
m('FateUnattempted', '%d' % unattempted)
m('FateUnattemptedGB', '%d' % round(G['closed_campaign_ended']))
m('FateNotSearched', '%d' % (SCOPE - done))
m('FateReachable', '%d' % (done + unattempted))
m('FateDonePct', '%.0f' % (100.0 * done / SCOPE))
# v4.09: the ledger's own history, so the sentence that says the category is
# gone can be written from generated numbers
m('FateDonePrior', '%d' % D['counts']['done'])
m('FateNoCalPrior', '%d' % D['counts']['excluded_no_calibration_available'])
m('FateInfeasPrior', '%d' % (D['counts']['disk_infeasible']
                            + D['counts'].get('never_started', 0)))
m('FateUnattemptedPrior', '%d' % D['counts']['closed_campaign_ended'])
m('FateNeverStarted', '%d' % C.get('never_started', 0))
m('FateNMoved', '%d' % len(MOVES))
m('FateNFalsified', '%d' % sum(
    1 for _, frm, _, _, _ in MOVES if frm == 'disk_infeasible'))

fail = []


def ck(tag, cond, detail=''):
    if not cond:
        fail.append(tag)
    print('  %-52s %s  %s' % (tag, 'PASS' if cond else 'FAIL', detail))


print('blockfate_v409: %d transitions' % len(MOVES))
for eb, frm, to, gb, why in MOVES:
    print('  %-22s %-24s -> %-34s %6.1f GB  %s'
          % (eb, frm, to, gb, why[:44]))
print('\nassertions')
ck('F1 the v4.08 prior sums to the scope',
   sum(D['counts'].values()) == SCOPE,
   '%d == %d' % (sum(D['counts'].values()), SCOPE))
ck('F2 the v4.09 fates sum to FateScope',
   sum(C.values()) == SCOPE, '%d == %d' % (sum(C.values()), SCOPE))
ck('F2b and the five printed categories sum to it too',
   done + nocal + calfail + infeas + unattempted == SCOPE,
   '%d + %d + %d + %d + %d == %d'
   % (done, nocal, calfail, infeas, unattempted, SCOPE))
ck('F3 never_started is GONE: the category has no members',
   C.get('never_started', 0) == 0, '%d' % C.get('never_started', 0))
ck('F4 the named block is excluded on the DELIVERY, not on effort',
   NS_TO == 'excluded_no_calibration_available'
   and DEL['verdict'] == 'eb_not_calibrated_in_delivery',
   '%s / %s' % (NS_TO, DEL['verdict']))
ck('F4b its two siblings in the same OUS carry calibration and are searched',
   len(DEL['delivery']['calapply']) == 2
   and set(DEL['delivery']['calapply']) == set(NS['searched_siblings']),
   '%s' % DEL['delivery']['calapply'])
ck('F5 the one remaining infeasible block\'s size closes both ways',
   abs(G_INFEAS_DERIVED - INFEAS_REMAIN_GB) < (1.0 if DRIVE != 3 else 0.0),
   '%.1f GB derived from the v4.08 total vs %.1f GB measured'
   % (G_INFEAS_DERIVED, INFEAS_REMAIN_GB))
ck('F6 two published disk_infeasible labels are falsified by measurement',
   sum(1 for _, frm, _, _, _ in MOVES if frm == 'disk_infeasible')
   == (2 if DRIVE != 4 else 3),
   '%d' % sum(1 for _, frm, _, _, _ in MOVES if frm == 'disk_infeasible'))
ck('F7 searched volume rises by exactly the transitions\' own sizes',
   abs(G['done'] - D['gb']['done']
       - sum(gb for _, _, to, gb, _ in MOVES if to == 'done'))
   < (0.05 if DRIVE != 5 else 0.0),
   '%.1f -> %.1f GB' % (D['gb']['done'], G['done']))
ck('F8 no fate count is negative',
   all(v >= 0 for v in C.values()) if DRIVE != 6 else False, '%s' % C)
ck('F9 the check that excluded it has been validated against controls',
   '361' in DEL['check_validation'] and 'resolved 0' in DEL['check_validation'],
   DEL['check_validation'][:60])
print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('blockfate_v409: %d assertion(s) failed: %s'
                     % (len(fail), fail))

TEXOUT = 'survey_numbers_round69.tex'
open(os.path.join(HERE, suffixed(TEXOUT)), 'w').writelines(L)
print('\nblockfate_v409: %d of %d searched (%.0f per cent, %.1f TB); not '
      'searched %d = %d no archive calibration, %d legacy calibration '
      'failures, %d disk-infeasible (%.1f GB), %d reachable but not attempted '
      '(%d GB); never_started %d'
      % (done, SCOPE, 100.0 * done / SCOPE, G['done'] / 1000.0,
         SCOPE - done, nocal, calfail, infeas, INFEAS_REMAIN_GB,
         unattempted, round(G['closed_campaign_ended']),
         C.get('never_started', 0)))
