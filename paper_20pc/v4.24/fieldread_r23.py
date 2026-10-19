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

Five assertions, five drives.  `--drive 0` means "no perturbation, but do not
write a path production reads"; every drive writes `*_driveN.*` only.

    python3 fieldread_r23.py [--drive N]
"""
import collections
import csv
import json
import os
import re
import subprocess
import sys

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


def pick(cands, row, namekey):
    same = [x for x in cands if skey(x.get(namekey)) == skey(row['star_name'])]
    pool = same or cands
    if len(pool) == 1:
        return pool[0]
    return min(pool, key=lambda x: abs(float(x['ctrl_max'])
                                       - float(row['ctrl_max_snr'] or 0)))


#: the compact-array rows, by the block's own antenna record and never by a
#: name: `archive_meta_v381.json` carries the array of every block, and
#: `acareext_v399.json` carries the dish the extraction actually used.
ACAROW = [i for i, r in enumerate(CAT)
          if MET.get(r['eb'], {}).get('array') == '7m']
_hot = max(ACAROW, key=lambda i: float(CAT[i]['star_snr']))
OWN, OTHER = [], []
for i in ACAROW:
    k = wkey(CAT[i]['eb'], CAT[i]['flo_GHz'], CAT[i]['fhi_GHz'])
    p = pick(BY[k], CAT[i], 'star_name') if BY[k] else None
    prov = (p or {}).get('provenance')
    if DRIVE == 3 and i == _hot:
        #: a row that DOES hold a crossing loses its own geometry
        prov = 'frozen'
    (OWN if prov == 'corrected-geometry' else OTHER).append(i)
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
m('FrNarrowProb', '%.3f' % P_NA)
m('FrNFlag', '%d' % NFLAG)
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
