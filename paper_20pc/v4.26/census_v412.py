#!/usr/bin/env python3
r"""Round 205: ONE OWNER FOR THE CROSSING CENSUS.

Every section, table, figure and the abstract read the census from here.  No
section carries its own count.  That rule exists because three of this paper's
own products disagreed about how many Class A crossings are unattributed, and
the disagreement reached a referee, who made it the second of two main
complaints.

What this generator publishes
-----------------------------
1.  The census itself, read from `ledger.json`: the crossing total, the
    attributed/unattributed split, the number outranking every control
    position, and the number recurring.  Each is asserted against the two
    other generators that already publish it (`blockq_v412.py`'s round 175
    and `numbers_v410.py`'s round 103), so three names for one quantity can
    no longer carry three values.

2.  The DISPOSITION SPLIT of the unattributed crossings, which
    `ledger_v410.py` printed to standard output and published as no macro at
    all: data-quality flagged / tested and absent again / spectrum not
    retained.  The conclusions and the abstract turn on which of the two
    numbers in "N tested" is meant -- `\RcNTested` is the number TESTED and
    is not the number tested AND absent again -- so both are published, each
    named for what it counts, and their sum is asserted.

3.  THE RECONCILIATION of the released catalogue's Class A unattributed count
    against the adopted ledger's.  This is the item that must be a sentence
    in the paper rather than a substitution.  Three numbers, not two:

      36  Class A crossings the released catalogue's own `disposition_computed`
          column calls unattributed;
      35  those of them whose window carries an independent-cell count, which
          is the population the chance expectation is summed over -- so the
          pairing of 35 against that expectation is right, and the one
          crossing excluded is named;
      32  the adopted ledger's Class A unattributed crossings.

    and the step from 35 to 32 is 35 - 4 - 2 + 3, measured and named here:

      -4  fall below the trigger at the repaired statistic and leave the
          ledger entirely;
      -2  become attributed because the rebuilt mask holds transitions the
          superseded hand-kept list did not;
      +3  are HD 14055, and they are the whole of the residue: one released
          crossing that the 35 never counted because its window carries no
          independent-cell count, and two from the archival tail that the
          released catalogue does not carry at all.

    ★ The three crossings behind the difference are therefore all one star.
    That is worth saying in the paper, because it is a statement about which
    product is incomplete and where, not a disagreement about physics.

Inputs, all read and none remembered: `ledger.json`, the released catalogue
`per_target_results_v3.99.csv`, and the macro layer for the counts the other
generators publish.  Nothing here is typed except the names of the two frozen
catalogue columns it reads.
"""
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 205
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
# ★ The PRODUCTION name is a literal, and only the drive branch is built by
#   format.  `macrosyn`'s SOURCE clause looks for the filename as a literal
#   string in some .py, so a name assembled with '%s' makes it report that no
#   generator can rebuild a file that is typeset -- which is the opposite of
#   the truth and exactly the alarm that clause exists to raise.
OUT_TEX = os.path.join(HERE, 'survey_numbers_round205.tex' if DRIVE is None
                       else 'survey_numbers_round205_drive%d.tex' % DRIVE)
OUT_JSON = os.path.join(HERE, 'census_v412%s.json' % SUF)

OUT = []
fail = []


def m(n, v):
    OUT.append(r'\newcommand{\%s}{%s}' % (n, v))


def ck(name, cond, detail=''):
    print('  %-70s %s' % (name[:70], 'PASS' if cond else 'FAIL  ' + str(detail)))
    if not cond:
        fail.append(name)


def texval(name):
    """The value the macro layer publishes, in \\input order so that a later
    \\renewcommand wins -- which is how round 103 supersedes an earlier
    round.  Reading the files in sorted order instead puts round 38 after
    round 103 and gives last run's value."""
    main = [f for f in glob.glob(os.path.join(HERE, 'technosignatures_*.tex'))]
    order = []
    if len(main) == 1:
        for ln in open(main[0], errors='ignore'):
            mm = re.match(r'\s*\\input\{(survey_numbers[A-Za-z0-9_]*)\}', ln)
            if mm:
                order.append(mm.group(1) + '.tex')
    val = None
    for fn in order:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        for ln in open(p, errors='ignore'):
            for nm, vv in re.findall(
                    r'\\(?:providecommand|renewcommand|newcommand)'
                    r'\{?\\([A-Za-z]+)\}?\{([^{}]*)\}', ln):
                if nm == name and vv.strip():
                    val = vv.strip()
    return val


# --------------------------------------------------------------- the ledger
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
SUM, ROWS = LED['summary'], LED['rows']
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))

N_CROSS = SUM['n_crossings']
N_ATTR = SUM['n_attributed']
N_UNATTR = SUM['n_unattributed']
N_RANK = SUM['n_rank_flagged_unattributed']

# ------------------------------------------------- the search class of a row
# ★ A crossing's search class is a property of the WINDOW it falls in, so it
#   is resolved by position in frequency inside that block's windows and never
#   by a name.  The two archival-tail crossings fall in windows the released
#   catalogue does not carry; they are fine-channel carrier-search windows by
#   construction, which is declared here and asserted against the published
#   Class A total rather than assumed.
def window_class(eb, freq):
    cs = set()
    for r in CAT:
        if r['eb'] != eb:
            continue
        lo, hi = float(r['flo_GHz']), float(r['fhi_GHz'])
        if min(lo, hi) - 1e-6 <= freq <= max(lo, hi) + 1e-6:
            cs.add(r['search_class'])
    if len(cs) == 1:
        return cs.pop(), 'window'
    if not cs:
        return 'A', 'tail'          # not in the release; declared, asserted below
    return '?', 'ambiguous'


for r in ROWS:
    r['_cls'], r['_cls_src'] = window_class(r['eb'], r['freq'])

XA = [r for r in ROWS if r['_cls'] == 'A']
XB = [r for r in ROWS if r['_cls'] == 'B']
UN_A = [r for r in XA if not r['attributed']]
UN_B = [r for r in XB if not r['attributed']]
TAIL = [r for r in ROWS if r['_cls_src'] == 'tail']

# ------------------------------------------- the disposition of each row
# The ledger's own typeset disposition column is the authority, because that
# is what a reader counts.  Re-deriving it here would be a second
# implementation of a split the ledger owns; instead the three sets are formed
# on the SAME two fields the ledger branches on and the result is asserted
# against the ledger's own totals.
RECURC = {}
_rc = os.path.join(HERE, 'recurcols_v411.json')
if os.path.exists(_rc):
    RECURC = json.load(open(_rc))


def rec_of(r):
    return RECURC.get('%s|%.6f' % (r['eb'], r['freq'])) or {}


UN = [r for r in ROWS if not r['attributed']]
TESTED = [r for r in UN if rec_of(r) and rec_of(r).get('note') is None]
NOSPEC = [r for r in UN if r not in TESTED]
FLAGGED = [r for r in TESTED if r['dq']]
NORECUR = [r for r in TESTED if not r['dq']]
N_RECUR = sum(1 for r in TESTED
              if (rec_of(r).get('T_anydrift') or 0.0) >= 5.0)

if DRIVE == 1:
    NORECUR = NORECUR[:-1]          # the split stops summing
if DRIVE == 2:
    N_RECUR = 1                     # a crossing recurs after all

# ------------------------------------------------- the 35 / 36 / 32 chain
RELA = [r for r in CAT if r['crossing'] == 'True' and r['search_class'] == 'A']
REL_UNATTR = [r for r in RELA
              if r['disposition_computed'].strip() == 'unattributed']
REL_COV = [r for r in REL_UNATTR if r['n_ind_cells'] != '']
REL_NOCELL = [r for r in REL_UNATTR if r['n_ind_cells'] == '']


def key(eb, f):
    return (eb, round(float(f), 4))


LEDKEY = {key(r['eb'], r['freq']): r for r in ROWS}
COVKEY = {key(r['eb'], r['f_cross_GHz']): r for r in REL_COV}

FELL = [r for k, r in sorted(COVKEY.items()) if k not in LEDKEY]
NOWATTR = [(k, r, LEDKEY[k]) for k, r in sorted(COVKEY.items())
           if k in LEDKEY and LEDKEY[k]['attributed']]
ARRIVED = [r for k, r in sorted(LEDKEY.items())
           if not r['attributed'] and r['_cls'] == 'A' and k not in COVKEY]

if DRIVE == 3:
    ARRIVED = ARRIVED[:-1]          # the reconciliation stops closing

ARR_STARS = sorted({r['display'].replace('~', ' ') for r in ARRIVED})


def starname(r):
    return r.get('display', r.get('star_name', '?')).replace('~', ' ')


# ------------------------------------------------------------- what was found
print('census_v412: round %d' % ROUND)
print('  census: %d crossings = %d attributed + %d unattributed; %d outrank '
      'all controls; %d recur' % (N_CROSS, N_ATTR, N_UNATTR, N_RANK, N_RECUR))
print('  by class: Class A %d (%d attributed, %d unattributed), Class B %d '
      '(%d, %d); %d from the archival tail'
      % (len(XA), len(XA) - len(UN_A), len(UN_A), len(XB),
         len(XB) - len(UN_B), len(UN_B), len(TAIL)))
print('  dispositions of the %d unattributed: %d data-quality flagged, %d '
      'tested and absent again, %d spectrum not retained  (tested = %d)'
      % (N_UNATTR, len(FLAGGED), len(NORECUR), len(NOSPEC), len(TESTED)))
print('  reconciliation: released column %d, of which %d carry an '
      'independent-cell count' % (len(REL_UNATTR), len(REL_COV)))
print('      - %d fell below the trigger at the repaired statistic: %s'
      % (len(FELL), ', '.join('%s %s' % (starname(r), r['eb'].split('_', 1)[1])
                              for r in FELL)))
print('      - %d attributed by the rebuilt mask: %s'
      % (len(NOWATTR), ', '.join('%s %s at %+.1f km/s from %s'
                                 % (starname(c), lr['eb'].split('_', 1)[1],
                                    lr['dv_stellar'], lr['line'])
                                 for _k, c, lr in NOWATTR)))
print('      + %d arrived, all %s: %s'
      % (len(ARRIVED), ' / '.join(ARR_STARS),
         ', '.join('%s at %.4f GHz (%s)'
                   % (r['eb'].split('_', 1)[1], r['freq'],
                      'no independent-cell count in the release'
                      if key(r['eb'], r['freq'])
                      in {key(x['eb'], x['f_cross_GHz']) for x in REL_NOCELL}
                      else 'archival tail, not in the release')
                   for r in ARRIVED)))
print('      %d - %d - %d + %d = %d' % (len(REL_COV), len(FELL), len(NOWATTR),
                                        len(ARRIVED), len(UN_A)))

# ------------------------------------------------------------- assertions
print('\nassertions')
ck('N1 the census closes: attributed + unattributed == crossings',
   N_ATTR + N_UNATTR == N_CROSS,
   '%d + %d == %d' % (N_ATTR, N_UNATTR, N_CROSS))
ck('N2 the class split closes both ways, and every row has a class',
   len(XA) + len(XB) == N_CROSS and len(UN_A) + len(UN_B) == N_UNATTR
   and not [r for r in ROWS if r['_cls'] == '?'],
   '%d A + %d B == %d; %d + %d == %d'
   % (len(XA), len(XB), N_CROSS, len(UN_A), len(UN_B), N_UNATTR))
ck('N3 THE DISPOSITION SPLIT SUMS TO THE UNATTRIBUTED TOTAL, and the number '
   'TESTED is not the number tested and absent again',
   len(FLAGGED) + len(NORECUR) + len(NOSPEC) == N_UNATTR
   and len(FLAGGED) + len(NORECUR) == len(TESTED)
   and len(NORECUR) < len(TESTED),
   '%d flagged + %d absent again + %d no spectrum == %d; tested %d'
   % (len(FLAGGED), len(NORECUR), len(NOSPEC), N_UNATTR, len(TESTED)))
ck('N4 no crossing recurs, which is the result the conclusions state',
   N_RECUR == 0, '%d of %d tested reach the trigger again'
   % (N_RECUR, len(TESTED)))
ck('N5 THE RECONCILIATION CLOSES: the covered released count, less those '
   'that fell, less those the rebuilt mask attributes, plus those that '
   'arrived, is the ledger count',
   len(REL_COV) - len(FELL) - len(NOWATTR) + len(ARRIVED) == len(UN_A),
   '%d - %d - %d + %d != %d' % (len(REL_COV), len(FELL), len(NOWATTR),
                                len(ARRIVED), len(UN_A)))
ck('N5b and the released column itself exceeds the covered subset by exactly '
   'the crossings whose window carries no independent-cell count',
   len(REL_UNATTR) - len(REL_COV) == len(REL_NOCELL) and len(REL_NOCELL) >= 1,
   '%d - %d against %d' % (len(REL_UNATTR), len(REL_COV), len(REL_NOCELL)))
ck('N6 EVERY ARRIVAL IS ONE STAR -- the residue is a statement about which '
   'product is incomplete, not about physics',
   len(ARR_STARS) == 1 and len(ARRIVED) >= 2, ARR_STARS)
ck('N7 the terms that fell and the terms the mask attributed are disjoint, '
   'so no crossing is counted in two of them',
   not ({key(r['eb'], r['f_cross_GHz']) for r in FELL}
        & {k for k, _c, _l in NOWATTR}),
   'overlap')
ck('N8 the mask can only move a crossing TOWARDS attribution: every one of '
   'the attributed-by-rebuild lies inside the mask half-width',
   all(abs(lr['dv_stellar']) <= SUM['mask_half_kms'] + 1e-9
       for _k, _c, lr in NOWATTR),
   [(starname(c), round(lr['dv_stellar'], 1)) for _k, c, lr in NOWATTR])
ck('N9 the archival-tail crossings really are outside the release, which is '
   'the declared reason their class is not read from a window',
   all(not [r for r in CAT if r['eb'] == t['eb']] for t in TAIL)
   or not TAIL, [t['eb'] for t in TAIL])

# ★ The three OTHER generators that publish a census count must agree with
#   this one.  This is the clause the round exists for: nothing compared them.
for nm, val, lbl in (('NCross', N_CROSS, 'crossings'),
                     ('NAttributed', N_ATTR, 'attributed'),
                     ('NUnattributed', N_UNATTR, 'unattributed'),
                     ('NUnattrRankFlagged', N_RANK, 'outranking all controls'),
                     ('ChnXrossA', len(XA), 'Class A crossings'),
                     ('ChnXrossB', len(XB), 'Class B crossings'),
                     ('ChnUnattrA', len(UN_A), 'Class A unattributed'),
                     ('ChnUnattrB', len(UN_B), 'Class B unattributed')):
    pub = texval(nm)
    if DRIVE == 4 and nm == 'ChnUnattrA':
        pub = str(len(UN_A) + 1)
    ck('N10 \\%s agrees with the census (%s)' % (nm, lbl),
       pub is not None and pub.strip() == str(val),
       'layer %s against census %d' % (pub, val))

# ★★ N10b -- RULING: "N tested" IS THREE NUMBERS AND NOT ONE.  This clause
# used to compare `\RcNTested` with the rows carrying a recurrence record,
# and it fired the moment HD 14055 became testable: the criterion (T >= 5 at
# the predicted cell) needs only a frequency and a drift grid, while an
# EXCLUSION needs a discovery amplitude, and that crossing has no retained
# discovery spectrum.  Reverting the count would have restored the
# contradiction referee 1 raised.  So the published triple is checked
# instead, and it is required to SUM: every unattributed crossing is tested;
# of those, one is tested against the criterion alone and four have their
# exclusion withheld with the execution block that fails the quality
# criterion; the rest carry a quoted exclusion.
_TRIPLE = (('RcNTested', N_UNATTR, 'every unattributed crossing is tested'),
           ('RcNExclPoss', len(TESTED), 'an exclusion is possible'),
           ('RcNNoSpec', len(NOSPEC), 'the criterion alone'),
           ('RcNWithheld', len(FLAGGED), 'exclusion withheld'),
           ('RcNExcl', len(NORECUR), 'a quoted exclusion'))
_got = {}
for nm, val, lbl in _TRIPLE:
    pub = texval(nm)
    _got[nm] = None if pub is None else pub.strip()
    ck('N10b \\%s agrees with the census (%s)' % (nm, lbl),
       _got[nm] is not None and _got[nm] == str(val),
       'layer %s against census %d' % (pub, val))
_iv = lambda k: int(_got[k]) if (_got.get(k) or '').isdigit() else -1
if DRIVE == 11:
    _got['RcNWithheld'] = '0'
ck('N10c and the three parts of "tested" SUM to it: a quoted exclusion, an '
   'exclusion withheld with the failing block, and the criterion alone',
   _iv('RcNExcl') + _iv('RcNWithheld') + _iv('RcNNoSpec')
   == _iv('RcNTested') == N_UNATTR
   and _iv('RcNExcl') + _iv('RcNWithheld') == _iv('RcNExclPoss'),
   '%s quoted + %s withheld + %s criterion-only = %s tested of %d '
   'unattributed; %s carry an exclusion at all'
   % (_got.get('RcNExcl'), _got.get('RcNWithheld'), _got.get('RcNNoSpec'),
      _got.get('RcNTested'), N_UNATTR, _got.get('RcNExclPoss')))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('census_v412: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ------------------------------------------------------------------ macros
m('CnCross', '%d' % N_CROSS)
m('CnAttr', '%d' % N_ATTR)
m('CnUnattr', '%d' % N_UNATTR)
m('CnRank', '%d' % N_RANK)
m('CnRecur', '%d' % N_RECUR)
m('CnRecurWord', 'none' if N_RECUR == 0 else '%d' % N_RECUR)
# the disposition split -- the four macros that existed only on stdout
m('CnNTested', '%d' % len(TESTED))
m('CnNFlagged', '%d' % len(FLAGGED))
m('CnNNoRecur', '%d' % len(NORECUR))
m('CnNNoSpec', '%d' % len(NOSPEC))
m('CnNFlaggedWord', {0: 'no', 1: 'one', 2: 'two', 3: 'three',
                     4: 'four', 5: 'five'}.get(len(FLAGGED),
                                               '%d' % len(FLAGGED)))
m('CnNNoSpecWord', {0: 'no', 1: 'one', 2: 'two', 3: 'three'}.get(
    len(NOSPEC), '%d' % len(NOSPEC)))
# the reconciliation
m('CnRelUnattrA', '%d' % len(REL_UNATTR))
m('CnRelCovA', '%d' % len(REL_COV))
m('CnNFell', '%d' % len(FELL))
m('CnNMaskAttr', '%d' % len(NOWATTR))
m('CnNArrived', '%d' % len(ARRIVED))
m('CnArrivedStar', ARR_STARS[0] if ARR_STARS else '--')
m('CnArrivedStarTex', (ARRIVED[0]['display'] if ARRIVED else '--'))
m('CnNArrivedNoCell', '%d' % len(REL_NOCELL))
m('CnNArrivedTail', '%d' % (len(ARRIVED) - len(REL_NOCELL)))
m('CnArrivedWord', {2: 'two', 3: 'three', 4: 'four'}.get(
    len(ARRIVED), '%d' % len(ARRIVED)))
m('CnNTail', '%d' % len(TAIL))

json.dump(dict(round=ROUND, drive=DRIVE,
               census=dict(crossings=N_CROSS, attributed=N_ATTR,
                           unattributed=N_UNATTR, rank_flagged=N_RANK,
                           recurring=N_RECUR),
               by_class=dict(A=len(XA), B=len(XB),
                             A_unattr=len(UN_A), B_unattr=len(UN_B)),
               dispositions=dict(tested=len(TESTED), flagged=len(FLAGGED),
                                 no_recurrence=len(NORECUR),
                                 no_spectrum=len(NOSPEC)),
               reconciliation=dict(
                   released_column=len(REL_UNATTR),
                   released_covered=len(REL_COV),
                   fell=[(starname(r), r['eb'], float(r['f_cross_GHz']))
                         for r in FELL],
                   attributed_by_rebuilt_mask=[
                       (starname(c), lr['eb'], lr['freq'],
                        lr['line'], lr['dv_stellar'])
                       for _k, c, lr in NOWATTR],
                   arrived=[(starname(r), r['eb'], r['freq'], r['_cls_src'])
                            for r in ARRIVED],
                   ledger=len(UN_A))),
          open(OUT_JSON, 'w'), indent=1)

with open(OUT_TEX, 'w') as fh:
    fh.write('%% GENERATED by census_v412.py (round %d) -- do not '
             'hand-edit.\n' % ROUND)
    fh.write('%% The crossing census has ONE owner.  No section may carry its '
             'own count.\n')
    fh.write('\n'.join(OUT) + '\n')
print('\n%d macros -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
