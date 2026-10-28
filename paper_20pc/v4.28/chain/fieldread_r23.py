#!/usr/bin/env python3
r"""Round 311: WHICH FIELD THE STATISTIC IS READ OVER, AND WHAT THE OTHER
READING WOULD HAVE GIVEN.

Equation 1 divides the stellar amplitude by the MAD over the control
positions, so $T_\star$ is a property of the annulus as much as of the cell:
read the same visibilities over a narrower field and the same crossing can
fall on the other side of the trigger.  Both sides of the chance comparison
are read over the whole primary beam, each block on its own antenna geometry;
this generator rebuilds both sides over the narrower first field as well, so
that the dependence is reported as a measurement rather than asserted to be
small.  It also publishes which geometry the compact-array catalogue rows
were extracted on, because that is the same question asked of the deposit.

It does not recompute the chance expectation itself: it runs the chance
generator twice, once in each reading, through its `--field` option, which
writes only `*_field<name>.*` and never a production path.  F1 requires the
adopted run to reproduce the published macros, which is what makes the narrow
run a measurement of the field and not of anything else.

Six assertions, six drives.  `--drive 0` means "no perturbation, but do not
write a path production reads"; every drive writes `*_driveN.*` only.

    python3 fieldread_r23.py [--drive N]
"""
import collections
import csv
import json
import math
import os
import re
import subprocess
import sys

import manuscript as mscript
import star_alias as sa

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 311
TRIG = 5.0
GEN = 'chance_v414.py'

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])

OUT_TEX = os.path.join(HERE, 'survey_numbers_round311.tex' if DRIVE is None
                       else 'survey_numbers_round311_drive%d.tex' % DRIVE)
OUT_JSON = os.path.join(HERE, 'fieldread_r23%s.json'
                        % ('' if DRIVE is None else '_drive%d' % DRIVE))

OUT = []
fail = []


def m(name, val):
    assert name.isalpha(), 'a macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label[:70], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def published(name, fn='survey_numbers_round310.tex'):
    """The value another generator has published, read from its own file."""
    for ln in open(os.path.join(HERE, fn), errors='ignore'):
        mm = re.match(r'\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$', ln)
        if mm and mm.group(1) == name:
            return mm.group(2)
    raise AssertionError('not published: %s' % name)


# =====================================================================
# (1) the two readings, each rebuilt on BOTH sides by the chance generator
# =====================================================================
def run(field):
    """One reading, computed by the chance generator itself.  A drive run
    passes `--drive 0` so that it writes a drive path and not the one this
    generator's production run reads.  The target is removed first and its
    absence is fatal: a stale file read back as this run's answer is the one
    way a sub-run can lie."""
    args = [sys.executable, os.path.join(HERE, GEN), '--field', field]
    sfx = '_field%s' % field
    if DRIVE is not None:
        args += ['--drive', '0']
        sfx = '_drive0' + sfx
    target = os.path.join(HERE, 'chance_v414%s.json' % sfx)
    if os.path.exists(target):
        os.remove(target)
    p = subprocess.run(args, cwd=HERE, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    assert os.path.exists(target), (
        '%s did not write %s (rc %d)\n%s'
        % (GEN, os.path.basename(target), p.returncode,
           p.stdout.decode()[-2000:]))
    return json.load(open(target))


ADO = run('adopted')
NAR = run('narrow')
if DRIVE == 1:
    NAR = ADO                       # the two readings stop differing

N_AD, E_AD = ADO['observed'], ADO['e_chance']
P_AD = ADO['p_at_least_observed_control_only']
N_NA, E_NA = NAR['observed'], NAR['e_chance']
P_NA = NAR['p_at_least_observed_control_only']
#: ★★ RULING 30: each reading's Monte Carlo standard error, from the chance
#: generator's own resampling (it prints the adopted reading itself)
SE_AD = ADO['p_at_least_observed_control_only_se']
SE_NA = NAR['p_at_least_observed_control_only_se']
MC_REPORT = {}


def mc_dp(name, p, se, dp):
    want = dp
    while dp > 0 and not se < 0.25 * 10.0 ** (-dp):
        dp -= 1
    assert se < 0.25 * 10.0 ** (-dp), ('Ruling 30: %s cannot be printed even '
                                       'to %d places (se %.2g)' % (name, dp, se))
    MC_REPORT[name] = dict(p=p, se=se, dp_requested=want, dp_printed=dp,
                           printed='%.*f' % (dp, p))
    return dp

# =====================================================================
# (2) the deposit's own record: which geometry each catalogue row used
# =====================================================================
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXP = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
ACA = json.load(open(os.path.join(HERE, 'acareext_v399.json')))
ACA = ACA['windows'] if isinstance(ACA, dict) else ACA
MET = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']
LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']


def wkey(eb, a, b):
    a, b = float(a), float(b)
    if DRIVE == 2:
        return (eb, round(a, 3), round(b, 3))      # the stored order again
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


def skey(s):
    return re.sub(r'\s+', '', s or '').lower()


BY = collections.defaultdict(list)
for r in EXP:
    BY[wkey(r['eb'], r['flo'], r['fhi'])].append(r)
AW = collections.defaultdict(list)
for r in ACA:
    AW[wkey(r['eb'], r['flo'], r['fhi'])].append(r)


import posjoin_r27 as PJ                                        # noqa: E402

_JOINS = []


def pick(cands, row, kind):
    """The export row of this catalogue row's star, by parallax distance and
    the row's own control maximum, never by name (r27 row 56,
    `posjoin_r27.py`).  Raises unless exactly one star's row is there."""
    assert kind == 'exp'
    q = PJ.pick_exp(cands, row)
    if q is not None:
        _JOINS.append((kind, row, q))
    return q


#: the compact-array rows, by the block's own antenna record and never by a
#: name: `archive_meta_v381.json` carries the array of every block, and
#: `acareext_v399.json` carries the dish the extraction actually used.
ACAROW = [i for i, r in enumerate(CAT)
          if MET.get(r['eb'], {}).get('array') == '7m']
_hot = max(ACAROW, key=lambda i: float(CAT[i]['star_snr']))
OWN, OTHER = [], []
for i in ACAROW:
    k = wkey(CAT[i]['eb'], CAT[i]['flo_GHz'], CAT[i]['fhi_GHz'])
    p = pick(BY[k], CAT[i], 'exp') if BY[k] else None
    prov = (p or {}).get('provenance')
    if DRIVE == 3 and i == _hot:
        #: a row that DOES hold a crossing loses its own geometry
        prov = 'frozen'
    (OWN if prov == 'corrected-geometry' else OTHER).append(i)
# P1/P2: every record at its row's position, and no record shared by two stars.
PJ.audit(_JOINS, 'fieldread_r23', HERE)
OTHER_T = max([float(CAT[i]['star_snr']) for i in OTHER] or [0.0])
#: the recorded dish of every row said to carry the corrected geometry
DISH = set()
for i in OWN:
    for w in AW.get(wkey(CAT[i]['eb'], CAT[i]['flo_GHz'], CAT[i]['fhi_GHz']), []):
        DISH.add(round(float(w['dish']), 1))

# =====================================================================
# (3) the six rows where the deposited flag is the narrower reading
# =====================================================================
WS = collections.defaultdict(list)
for i, r in enumerate(CAT):
    lo, hi = float(r['flo_GHz']), float(r['fhi_GHz'])
    WS[r['eb']].append((min(lo, hi), max(lo, hi), i))


def window_of(eb, f):
    h = [i for lo, hi, i in WS.get(eb, []) if lo - 1e-6 <= f <= hi + 1e-6]
    return h[0] if h else None


LEDWIN = {window_of(r['eb'], r['freq']) for r in LED}
LEDWIN.discard(None)
FLAG_UP, FLAG_DOWN = [], []
for i, r in enumerate(CAT):
    if r['search_class'] != 'A':
        continue
    flag = (r['crossing'] == 'True')
    held = i in LEDWIN
    if flag and not held:
        FLAG_DOWN.append(i)         # the catalogue flags it, the ledger does not
    elif held and not flag:
        FLAG_UP.append(i)           # the ledger holds it, the catalogue does not
if DRIVE == 4:
    FLAG_UP = []                    # the disagreement runs one way only
NFLAG = len(FLAG_UP) + len(FLAG_DOWN)

# =====================================================================
# macros
# =====================================================================
m('FrNarrowObs', '%d' % N_NA)
m('FrNarrowExp', '%.1f' % E_NA)
m('FrNarrowProb', '%.*f' % (mc_dp('FrNarrowProb', P_NA, SE_NA, 3), P_NA))
#: ★★ AND THE BOUND, IN THE OTHER READING.  The chance generator inverts its
#: own resampling in whichever field it is read over, so the largest added
#: population the comparison could not have rejected comes back beside the
#: count and the expectation rather than from a second calculation.  It is
#: published so that each reading can be quoted with its own bound instead of
#: one reading's bound standing for both.
m('FrNarrowAddLim', '%d' % NAR['added_population_limit'])
m('FrNFlag', '%d' % NFLAG)

#: ★★★★ A2: TWO READINGS WERE TESTED AND NEITHER WAS NOMINATED FIRST.  The
#: paper reports both, so the smaller of the two probabilities is a minimum
#: over two tests and is corrected for them.  Bonferroni is the correction
#: PRINTED, because it is the one a reader can redo from the two
#: probabilities the paper already quotes; Sidak is computed beside it and F7
#: requires the two to agree at the printed precision, so the statement does
#: not depend on which form is used and only one number enters the paper.
#: ★ THE MULTIPLIER IS DERIVED FROM THE READINGS THIS GENERATOR PUBLISHES, so
#: a third reading changes the correction instead of leaving it at two.
READINGS = [('adopted', P_AD), ('narrow', P_NA)]
N_READ = len(READINGS)
P_MIN = min(p for _n, p in READINGS)
P_TWO = min(1.0, N_READ * P_MIN)
P_TWO_SIDAK = 1.0 - (1.0 - P_MIN) ** N_READ
#: the precision the number is PRINTED at, so that "the two forms agree" is
#: asserted in the units the paper quotes and never in machine precision --
#: `abs(round(a, 3) - round(b, 3)) <= 0.001` FAILS on these very inputs,
#: because 0.054 - 0.053 is 1.0000000000000009e-3 in binary floating point.
#: ★ Ruling 30: the printed precision is the one the two-trial value's own
#: Monte Carlo error supports (N_READ times the smaller reading's error).
_SE_MIN = SE_AD if P_AD <= P_NA else SE_NA
P_PREC = mc_dp('FrTwoTrialP', P_TWO, N_READ * _SE_MIN, 3)


def _ulp(x):
    return int(round(x * 10.0 ** P_PREC))


m('FrNRead', '%d' % N_READ)
#: ★ THE COUNT AS ENGLISH, because the sentence that carries it sits beside
#: three other spelled-out counts and a digit there reads as a typesetting
#: slip.  Generated from the same list the correction is computed over, so a
#: third reading changes the word with the multiplier instead of leaving a
#: stale one in the prose.
_WORDS = ('no', 'one', 'two', 'three', 'four', 'five', 'six')
assert N_READ < len(_WORDS), N_READ
m('FrNReadWord', _WORDS[N_READ])
m('FrTwoTrialP', '%.*f' % (P_PREC, P_TWO))


#: ★ The risen rows are named from the LEDGER and the fallen ones from the
#: catalogue, because only the ledger resolves the component: one catalogue
#: row carries a companion's crossing under the primary's name.
def _namelist(idxs, from_ledger):
    out = []
    for i in idxs:
        #: the ledger row is found by WINDOW -- block and frequency span --
        #: and never by block alone: a block may hold more than one crossing
        r = (next((q for q in LED if window_of(q['eb'], q['freq']) == i), None)
             if from_ledger else None)
        out.append(r['display'] if r else
                   sa.designation(CAT[i]['star_name']).replace(' ', '~'))
    c = collections.Counter(out)
    seen, parts = set(), []
    for n in out:
        if n in seen:
            continue
        seen.add(n)
        parts.append(n if c[n] == 1 else
                     '%s (%s)' % (n, {2: 'twice', 3: 'three times'}[c[n]]))
    return (', '.join(parts[:-1]) + ' and ' + parts[-1]) if len(parts) > 1 \
        else parts[0]


m('FrUpStars', _namelist(FLAG_UP, True))
m('FrDownStars', _namelist(FLAG_DOWN, False))
m('FrNAcaRow', format(len(ACAROW), ',').replace(',', '\\,'))
m('FrNAcaOwn', format(len(OWN), ',').replace(',', '\\,'))
m('FrNAcaOther', '%d' % len(OTHER))
m('FrAcaMaxT', '%.1f' % OTHER_T)
if DRIVE == 5:
    OUT[:] = [x for x in OUT if 'FrAcaMaxT' not in x]   # the bound goes

# =====================================================================
# assertions
# =====================================================================
ck('F1 THE ADOPTED READING REPRODUCES THE PUBLISHED COMPARISON, so the other '
   'run measures the field and nothing else: the generator is the same one, '
   'run twice, and only the annulus it reads over differs',
   N_AD == int(published('CeObs'))
   and abs(E_AD - float(published('CeExp'))) < 0.05
   and abs(P_AD - float(published('CeProbNull'))) < 0.005,
   'adopted %d against the published %s, expectation %.2f against %s, '
   'P %.3f against %s' % (N_AD, published('CeObs'), E_AD, published('CeExp'),
                          P_AD, published('CeProbNull')))

ck('F2 THE OTHER READING MOVES BOTH SIDES AND IS THEREFORE LIKE FOR LIKE: '
   'the expectation and the count are both rebuilt on the narrower field, '
   'the window set is the same one, and the two readings differ',
   NAR['n_win_A_reference'] == ADO['n_win_A_reference']
   and E_NA != E_AD and N_NA != N_AD
   and NAR['e_trigger_released'] != ADO['e_trigger_released'],
   'narrow %d against %.2f over %d windows; adopted %d against %.2f over %d'
   % (N_NA, E_NA, NAR['n_win_A_reference'], N_AD, E_AD,
      ADO['n_win_A_reference']))

ck('F3 EVERY COMPACT-ARRAY ROW IS ACCOUNTED FOR AND THE EXCEPTIONS HOLD NO '
   'crossing: the rows are selected by the block\'s own antenna record, the '
   'ones carrying the corrected geometry record the 7 m dish and no other, '
   'and the largest statistic among the rest is below the trigger',
   len(OWN) + len(OTHER) == len(ACAROW)
   and len(ACAROW) == int(published('PbNAcaRow',
                                    'survey_numbers_round101.tex')
                          .replace('\\,', ''))
   and DISH == {7.0} and len(OTHER) > 0 and OTHER_T < TRIG,
   '%d rows, %d on their own geometry, %d not, recorded dish %s, largest '
   'statistic among them %.4f against a trigger of %g'
   % (len(ACAROW), len(OWN), len(OTHER), sorted(DISH), OTHER_T, TRIG))

ck('F4 THE DEPOSITED FLAGS DISAGREE WITH THE LEDGER IN BOTH DIRECTIONS, '
   'which is what makes them a different reading rather than a loss: a '
   'narrower field both raises and lowers the statistic, and the count of '
   'rows affected is the one the appendix prints',
   len(FLAG_UP) > 0 and len(FLAG_DOWN) > 0
   and NFLAG == len(FLAG_UP) + len(FLAG_DOWN)
   and all(CAT[i]['search_class'] == 'A' for i in FLAG_UP + FLAG_DOWN),
   '%d rows: %d the ledger holds and the catalogue does not, %d the other '
   'way' % (NFLAG, len(FLAG_UP), len(FLAG_DOWN)))

ck('F5 THE EXCEPTIONS ARE BOUNDED IN PRINT AND NOT MERELY COUNTED: a '
   'statement that some rows were extracted on another geometry is worth '
   'nothing without the largest statistic among them',
   any('FrAcaMaxT' in x for x in OUT)
   and any('FrNAcaOther' in x for x in OUT),
   '%d macros' % len(OUT))

_PR = re.sub(r'\s+', ' ', mscript.flat())
if DRIVE == 8:
    _PR = _PR.replace('\\CeAlphaPct', 'XX')     # the level leaves the prose
_TWOSENT = [s for s in re.split(r'(?<=[.;:])\s', _PR) if '\\FrTwoTrialP' in s]
_LVL = float(published('CeAlphaPct')) / 100.0
if DRIVE == 7:
    N_READ = 1                       # the correction silently drops a trial
    P_TWO = min(1.0, N_READ * P_MIN)
ck('F7 THE CORRECTION IS FOR THE READINGS THE PAPER REPORTS, AND THE NUMBER '
   'IS NEVER PRINTED WITHOUT THE LEVEL IT IS TESTED AGAINST: the printed '
   'probability is the smaller raw probability multiplied by the number of '
   'readings this generator publishes a probability for, it is never smaller '
   'than that raw probability nor larger than one, the two standard '
   'corrections agree to within one unit in the last printed place and on '
   'the verdict against the level, and every sentence quoting it also quotes '
   'the level',
   N_READ == len(READINGS)
   and abs(P_TWO - min(1.0, N_READ * P_MIN)) < 1e-12
   and P_MIN <= P_TWO <= 1.0
   and abs(_ulp(P_TWO) - _ulp(P_TWO_SIDAK)) <= 1
   and ((P_TWO > _LVL) == (P_TWO_SIDAK > _LVL))
   and len(_TWOSENT) > 0
   and all('\\CeAlphaPct' in s for s in _TWOSENT),
   '%d readings, smaller raw probability %.6f, corrected %.6f (Sidak '
   '%.6f), printed %.3f; %d sentences quote it, %d of them with the level'
   % (N_READ, P_MIN, P_TWO, P_TWO_SIDAK, P_TWO,
      len(_TWOSENT), sum('\\CeAlphaPct' in s for s in _TWOSENT)))


#: ★★★★ F6: THE BOUND IS A PROPERTY OF THE READING, SO IT IS REBUILT IN BOTH.
#: Two things make it a measurement rather than a quotation.  The adopted run
#: must return the bound the paper already publishes -- same generator, same
#: inversion, only the annulus differing -- and both bounds must agree with
#: the closed form, the inversion of a one-sided Poisson test at the same
#: level, which is the arithmetic a reader can redo with a calculator and the
#: one check of this paper's bound that needs none of its machinery.
#: ★ The ORDERING is asserted against the counts that imply it rather than
#: assumed: a reading with the larger excess must admit the larger added
#: population, and if it ever did not, that is the finding.
def _pois_cdf(k, lam):
    s, t = 0.0, math.exp(-lam)
    for i in range(k + 1):
        s, t = s + t, t * lam / (i + 1)
    return s


def _pois_lim(n, e, alpha):
    """The largest added population leaving a count as low as n credible."""
    lo, hi = 0.0, 400.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if _pois_cdf(n, e + mid) >= alpha else (lo, mid)
    return lo


ALPHA = (100.0 - float(ADO['coverage_pct'])) / 100.0
B_AD, B_NA = ADO['added_population_limit'], NAR['added_population_limit']
if DRIVE == 6:
    B_NA = B_AD                 # the bound stops following the reading
P_LIM_AD, P_LIM_NA = _pois_lim(N_AD, E_AD, ALPHA), _pois_lim(N_NA, E_NA, ALPHA)
ck('F6 EACH READING CARRIES ITS OWN BOUND, the adopted one reproducing the '
   'published value and both agreeing with the closed-form Poisson inversion '
   'at the same level to within one crossing, and the larger excess admits '
   'the larger added population',
   B_AD == int(published('CeAddLim'))
   and abs(B_AD - P_LIM_AD) <= 1.0 and abs(B_NA - P_LIM_NA) <= 1.0
   and (B_NA > B_AD) == (N_NA - E_NA > N_AD - E_AD),
   'adopted %d against the published %s and %.2f in closed form; narrow %d '
   'against %.2f in closed form; excesses %+.2f and %+.2f at the %.0f per '
   'cent level' % (B_AD, published('CeAddLim'), P_LIM_AD, B_NA, P_LIM_NA,
                   N_AD - E_AD, N_NA - E_NA, 100.0 * (1.0 - ALPHA)))

# =====================================================================
# write
# =====================================================================
if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    if DRIVE is None:
        raise SystemExit(1)

hdr = ['%% GENERATED by fieldread_r23.py (round %d) -- do not hand-edit.' % ROUND,
       '%% The field the statistic is read over: the adopted reading over the',
       '%% whole primary beam, the same comparison rebuilt on both sides over',
       '%% the narrower first field, and the geometry each compact-array row',
       '%% was extracted on.']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
json.dump(dict(round=ROUND, drive=DRIVE,
               adopted=dict(observed=N_AD, expectation=E_AD, p=P_AD),
               narrow=dict(observed=N_NA, expectation=E_NA, p=P_NA,
                           bound=NAR.get('added_population_limit')),
               n_aca_row=len(ACAROW), n_aca_own_geometry=len(OWN),
               n_aca_other_geometry=len(OTHER),
               aca_other_rows=[dict(eb=CAT[i]['eb'], star=CAT[i]['star_name'],
                                    cls=CAT[i]['search_class'],
                                    tstar=float(CAT[i]['star_snr']))
                               for i in OTHER],
               aca_other_max_tstar=OTHER_T,
               recorded_dish=sorted(DISH),
               flags_ledger_only=[CAT[i]['eb'] for i in FLAG_UP],
               flags_catalogue_only=[CAT[i]['eb'] for i in FLAG_DOWN]),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('\nfieldread_r23: round %d%s' % (ROUND, '' if DRIVE is None
                                       else '  (drive %d)' % DRIVE))
print('  adopted  %d observed against %.2f expected, P = %.3f'
      % (N_AD, E_AD, P_AD))
print('  narrow   %d observed against %.2f expected, P = %.3f'
      % (N_NA, E_NA, P_NA))
print('  %d compact-array rows, %d on their own geometry, %d not (largest '
      'statistic %.4f)' % (len(ACAROW), len(OWN), len(OTHER), OTHER_T))
print('wrote %s (%d macros) and %s'
      % (os.path.basename(OUT_TEX), len(OUT), os.path.basename(OUT_JSON)))
print('Ruling 30 (Monte Carlo digits): %s' % json.dumps(MC_REPORT, sort_keys=True))
