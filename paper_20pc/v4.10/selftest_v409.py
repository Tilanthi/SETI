#!/usr/bin/env python3
r"""GATE (v4.09): drive every assertion added in this cycle, one at a time,
and require THE NAMED CHECK -- and no other -- to be the one that fires.

A check that cannot fail is not a check.  This project has now shipped
FOURTEEN defects of one family, and v4.09 added a fifteenth variant of the
complement: TWO assertions that could only ever fail on good data.  So the
discipline here is three-sided.

  * every assertion has a `--drive N` that makes it fire;
  * where it has two directions, BOTH are driven (V3a/V3b/V3c on the repair's
    no-op claim; V8a/V8b on the fixed key; V9/V9b on the declared epochs);
  * and the drive must fire the NAMED check and nothing else, so a drive that
    breaks the generator in some other way does not count as a demonstration.

★★★★ AND THE FOURTEENTH DEFECT'S OWN LESSON IS ENFORCED MECHANICALLY HERE.
D36's fourteenth instance was not a key collision at all: the repair's own
test harness WROTE THE PRODUCTION POPULATION FILE on every run, drives
included, so a deliberately mis-keyed population was left on disk and the
next stage consumed it.  A crossing then appeared twice and a scan ladder read
5 instead of 4.  Standing rule, and now a test: *a test must never write to
the path production reads.*  Every v4.09 generator suffixes all of its outputs
with `_driveN` when driven, and `V12`/`W0` below assert that the drives leave
the production products byte-identical.

Usage: selftest_v409.py
"""
import glob
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (generator, drive, {tags that must fire}, what the drive reinstates)
DRIVES = [
    # ================= v409_calc.py: the census and the crossing delta =====
    ('v409_calc.py', 1, {'V2', 'V3b'},
     'join the harvest to the catalogue on flo alone -- the defect that '
     'silently loses every reversed-spectral-axis window (80 of 157)'),
    ('v409_calc.py', 2, {'V1'},
     'add a Class B window: the class split must stop summing to the extent'),
    ('v409_calc.py', 3, {'V2'},
     'break the crossing arithmetic: 56 - 4 + 1 + 1 + 2 must close on 56'),
    # ★ BOTH DIRECTIONS of the no-op claim, which is the whole legitimacy
    #   argument for adopting the repaired statistic
    ('v409_calc.py', 4, {'V3a'},
     'demand a median signed shift so small the test could not fire'),
    ('v409_calc.py', 5, {'V3a'},
     '... and the other way: demand one so large that "unbiased" is '
     'unwritable'),
    ('v409_calc.py', 6, {'V3b'},
     'require the no-time-recovered windows to MOVE, which would mean the '
     'repair is a re-tuning and not a repair'),
    ('v409_calc.py', 7, {'V3c'},
     '... and the converse: require the crossings NOT to move, which would '
     'make the delta table vacuous'),
    ('v409_calc.py', 8, {'V4'},
     'force one delta row to pass the rank screen -- the one circumstance in '
     'which a crossing here could be a candidate'),
    ('v409_calc.py', 9, {'V5a'},
     'require the two additions to be UNattributed: if they were, the '
     'unattributed population would grow'),
    ('v409_calc.py', 10, {'V5b'},
     '... and the converse: require the two tail crossings to be '
     'line-attributed, which would remove the need for a recurrence test'),
    ('v409_calc.py', 11, {'V6'},
     "transpose the clustering p-values so the referee's post-hoc fixed band "
     'is printed as the result'),
    ('v409_calc.py', 12, {'V6b'},
     'require a corrected clustering statistic to be significant'),
    ('v409_calc.py', 13, {'V7'},
     'drop the held-out half from the emitted set: D5 forbids citing the '
     'near-edge excess without it'),
    ('v409_calc.py', 14, {'V7b'},
     'require the excess to survive removing its one dominating window'),
    ('v409_calc.py', 15, {'V8a'},
     'require the fixed position key to WEAKEN the star/control contrast'),
    ('v409_calc.py', 16, {'V9'},
     'quote the all-30-epoch exclusion instead of the conservative '
     'informative-epoch one'),
    ('v409_calc.py', 17, {'V14'},
     'let the duplicated transition list drift from v342_calc.py'),
    ('v409_calc.py', 19, {'V15'},
     'break the visibility-fit coverage identity: fitted plus outstanding '
     'must equal the released crossing count, which is how the "52 of 56" '
     'in the science-input note was caught disagreeing with the ledger'),
    # ★ round 9: V7c is no longer conditional on the manuscript happening to
    #   quote the ratio.  Drive 20 removes the citation itself and V7c must
    #   fire, so the limitation cannot be deleted from the prose in silence --
    #   which is exactly what happened when the appendix that quoted it went.
    ('v409_calc.py', 20, {'V7c'},
     'delete the near-edge ratio from the manuscript altogether: the old V7c '
     'went vacuous on exactly this and left a stated limitation protected by '
     'nothing'),
    ('v409_calc.py', 18, {'V7c'},
     "stop the manuscript referencing the edge excess's guards, so "
     'retire_macros would strip them and D5\'s condition would be '
     'unenforceable at the use site'),
    # ================= blockfate_v409.py: the ledger ========================
    ('blockfate_v409.py', 1, {'F3', 'F4', 'F5'},
     'leave the one unnamed block in `never_started`: the category must not '
     'be able to survive'),
    ('blockfate_v409.py', 2, {'F2', 'F2b'},
     'add a block: the fates must stop summing to the 177 in scope'),
    ('blockfate_v409.py', 3, {'F5'},
     "tighten the one remaining infeasible block's size agreement to zero"),
    ('blockfate_v409.py', 4, {'F6'},
     'claim three falsified disk_infeasible labels where two are measured'),
    ('blockfate_v409.py', 5, {'F7'},
     "require the searched volume to rise by something other than the "
     "transitions' own sizes"),
    ('blockfate_v409.py', 6, {'F8'},
     'allow a negative fate count'),
    # ================= p90_budget_v409.py: Table 11 =========================
    ('p90_budget_v409.py', 1, {'B3'},
     'put the typed PLX_WORST = 0.0248 back: a claim about the sample that '
     'nothing compares to the sample'),
    # ★ round 9: the old drive 2 became a NO-OP when B4 reversed (transfer
    #   and campaign are one quantity, so assigning one to the other
    #   perturbs nothing).  It now reinstates the real defect -- the same
    #   quantity carried twice under two row names -- which B4 catches on
    #   the values AND B7 catches on the row count.  Both are the gate
    #   working, so both are expected.
    ('p90_budget_v409.py', 2, {'B4', 'B7'},
     'conflate the window-to-window transfer row with the campaign row '
     'again -- they were literally the same two numbers'),
    ('p90_budget_v409.py', 3, {'B5'},
     'relabel the decorrelation bracket as measured when no measurement of '
     'it exists'),
    ('p90_budget_v409.py', 4, {'B9'},
     'choose the dominant term from a set including two terms that are not '
     'in the quadrature sum -- which is what the paper printed'),
    ('p90_budget_v409.py', 5, {'B7'},
     'change the row count away from the pinned 9'),
    ('p90_budget_v409.py', 6, {'B6'},
     'break the quadrature identity of the Combined row'),
    ('p90_budget_v409.py', 7, {'B7b'},
     'break `tested + transferred == NWinA`, the pin that caught the stale '
     'typed 403'),
    ('p90_budget_v409.py', 8, {'B8'},
     "print R1-5's withdrawn x0.48-1.35 bracket instead of the measured one"),
    ('p90_budget_v409.py', 9, {'B10'},
     'require a macro the manuscript does not reference: this is the exact '
     'mechanism by which retire_macros.py removed the transfer row from '
     'Table 11 for four versions'),
    # ★ round 9: B10 was AMENDED, because its original requirement outlived
    #   the row it protected -- B4's reversal merged the transfer row into the
    #   campaign row, and `BudTransLo/Hi` then held the COMBINED interval
    #   under a TRANSFER label.  B10b is the new half: one quantity, one name.
    ('p90_budget_v409.py', 10, {'B10b'},
     'put the combined interval back under a transfer-labelled macro name, '
     'which is how the same number came to have four names and how a reader '
     'could meet it under a label that said something else'),
]

# source mutations, for assertions whose failure mode is structural rather
# than numeric
MUTATE = [
    # ★★ the HD 139084 repoint keyed on the primary-beam offset is the 13th
    #    instance of the family: the two components differ by 0.13 arcsec in
    #    offset and 10.32 arcsec on the sky, so a 0.2 arcsec tolerance CANNOT
    #    separate them.  Reinstate the tolerance and V13 must fire.
    ('v409_calc.py',
     "   abs(PB_COMP - PB_PRIM) < 0.2 and len(COMP) == 4,",
     "   abs(PB_COMP - PB_PRIM) > 0.2 and len(COMP) == 4,", 'V13'),
    # the N_eff identity, which replaced an assertion that could only ever
    # fail on good data (`N_eff < N`)
    ('v409_calc.py',
     "   abs(neff_id - EC['n_eff']) < 1e-6 * max(1.0, EC['n_eff']),",
     "   abs(neff_id - EC['n_eff']) < 0.0,", 'V10b'),
    # eta Crv must have exactly two covering epochs; if it had one there is
    # no recurrence test and the paper may not claim one
    ('v409_calc.py',
     "   EC['n_covering'] == 2 and EC_OTH['sig'] < EC_DISC['sig'],",
     "   EC['n_covering'] == 3 and EC_OTH['sig'] < EC_DISC['sig'],", 'V10'),
    # Class B must be untouched to the last digit, because every one of the
    # 35 collisions is a fine spw3 window
    ('v409_calc.py',
     "   abs(AG['fixed_key']['B']['ratio'] - AG['basename_key']['B']['ratio']) < 1e-12,",
     "   abs(AG['fixed_key']['B']['ratio'] - AG['basename_key']['B']['ratio']) < 0.0,",
     'V8b'),
    # the 21 ACA-sensitivity epochs must be declared and not counted
    ('v409_calc.py',
     "   all(e['frac_invvar_from_shallow'] < 0.05 for e in EV.values()),",
     "   all(e['frac_invvar_from_shallow'] < 0.005 for e in EV.values()),",
     'V9b'),
    # the computed part of the tail hours must reproduce
    ('v409_calc.py',
     "   abs(H_TAIL_HD - 9.334) < 0.01 and H_TAIL_DECL > 0,",
     "   abs(H_TAIL_HD - 9.334) < 1e-9 and H_TAIL_DECL > 0,", 'V11'),
    # the delivery record itself: two of three siblings carry calibration
    ('blockfate_v409.py',
     "   and set(DEL['delivery']['calapply']) == set(NS['searched_siblings']),",
     "   and set(DEL['delivery']['calapply']) != set(NS['searched_siblings']),",
     'F4b'),
    ('blockfate_v409.py',
     "   '361' in DEL['check_validation'] and 'resolved 0' in DEL['check_validation'],",
     "   '362' in DEL['check_validation'] and 'resolved 0' in DEL['check_validation'],",
     'F9'),
    ('p90_budget_v409.py',
     "   shipped_val('Absolute flux scale') == '$\\\\pm%.0f$' % (100 * E_FLUX),",
     "   shipped_val('Absolute flux scale') != '$\\\\pm%.0f$' % (100 * E_FLUX),",
     'B1'),
    ('p90_budget_v409.py',
     "   shipped_val('Distance') == _v,",
     "   shipped_val('Distance') != _v,", 'B2'),
]

PRODUCTS = ['survey_numbers_round102.tex', 'survey_numbers_round69.tex',
            'survey_numbers_round38.tex', 'tab_crossdelta_v409.tex',
            'tab_clust_v409.tex', 'tab_tail_v409.tex',
            'tab_p90budget_v409.tex', 'repaired_v409.csv',
            'p90budget_v409.json']
LINE = re.compile(r'^\s{2}(\w+)\s.*?\s(PASS|FAIL)\s', re.M)


def digests():
    d = {}
    for p in PRODUCTS:
        f = os.path.join(HERE, p)
        if os.path.exists(f):
            d[p] = hashlib.sha256(open(f, 'rb').read()).hexdigest()
    return d


def fired(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    hits = {t for t, v in LINE.findall(r.stdout) if v == 'FAIL'}
    # ★★ ROUND 9.  This read the exit status FIRST, so any drive whose
    #    assertion makes the generator REFUSE was recorded as CRASHED rather
    #    than as demonstrated -- and `p90_budget_v409.py` raises SystemExit
    #    for a `ROUTED` condition BY DESIGN (B10/B10b are conditions on a
    #    prose file, so they stop the build without being product failures).
    #    So B10 could never be demonstrated through this harness at all: the
    #    one check in the budget whose whole purpose is to survive
    #    `retire_macros` was the one check this gate could not drive.  Read
    #    the generator's own assertion report first; a non-zero exit with NO
    #    named assertion is still a crash, which is what the distinction is
    #    for.
    if hits:
        return hits, None
    if r.returncode != 0:
        return None, r.stderr.strip().splitlines()[-1:] or ['?']
    return hits, None


ok = bad = 0

# ---- W0: the undriven run must pass every assertion ----------------------
# NOTE the ordering: the digests are taken AFTER the baseline runs, not
# before.  make_all.sh ends with retire_macros.py, which strips unreferenced
# macros from the round files, so a snapshot taken first would show a
# difference caused by the legitimate regeneration rather than by a drive.
for gen in ('v409_calc.py', 'blockfate_v409.py', 'p90_budget_v409.py'):
    # `--drive 0` means "no perturbation, but write to *_drive0.*".  The
    # baseline check must not itself land on a production path -- that would
    # be D36's fourteenth defect reappearing inside the gate that exists to
    # prevent it, which is what the first version of this file did.
    f, err = fired([sys.executable, gen, '--drive', '0'])
    if err is not None or f:
        print('  BASELINE FAILS  %-22s %s' % (gen, err or sorted(f)))
        bad += 1
    else:
        ok += 1
before = digests()

# ---- the drives ----------------------------------------------------------
for gen, n, want, why in DRIVES:
    f, err = fired([sys.executable, gen, '--drive', str(n)])
    if err is not None:
        print('  CRASHED           %-22s drive %-2d %s' % (gen, n, err))
        bad += 1
    elif f == want:
        ok += 1
    else:
        print('  NOT DEMONSTRATED  %-22s drive %-2d wanted %s got %s  (%s)'
              % (gen, n, sorted(want), sorted(f), why[:50]))
        bad += 1

# ---- the source mutations -----------------------------------------------
import tempfile
TMP = tempfile.mkdtemp(prefix='selftest_v409_')
for gen, old, new, want in MUTATE:
    src = open(os.path.join(HERE, gen)).read()
    if old not in src:
        print('  MISSING           %-22s %s' % (gen, old[:60]))
        bad += 1
        continue
    pert = src.replace(old, new, 1)
    pert = pert.replace("HERE = os.path.dirname(os.path.abspath(__file__))",
                        "HERE = %r" % HERE)
    # every write goes to the scratch directory: the mutation must not be
    # able to land a product either
    # v4.10: the perturbed copy runs from TMP, so sys.path[0] is TMP and
    # `import manuscript` (the split-manuscript view the generators now read)
    # would raise ModuleNotFoundError -- which looks exactly like a check that
    # failed to fire.  Put the build directory on the path.
    pert = ("import os as _o\n_o.makedirs(%r, exist_ok=True)\n" % TMP
            + "import sys as _sy\n_sy.path.insert(0, %r)\n" % HERE) + pert
    pert = pert.replace("def out(name):",
                        "def out(name):\n    import os as _oo\n"
                        "    return _oo.path.join(%r, _oo.path.basename(name))"
                        % TMP)
    # every write is redirected: the mutation must not be able to land a
    # product either.  `suffixed()` is the one place all three generators
    # build an output path, so redirecting it covers all of them.
    pert = pert.replace("def suffixed(name):",
                        "def suffixed(name):\n    import os as _oo\n"
                        "    return _oo.path.join(%r, _oo.path.basename(name))"
                        % TMP)
    pert = pert.replace("open(os.path.join(HERE, suffixed(", "open(os.path.join('', suffixed(")
    pert = pert.replace("open(os.path.join(HERE, 'p90budget_v409' + SUF + '.json'), 'w')",
                        "open(os.path.join(%r, 'x.json'), 'w')" % TMP)
    tmp = os.path.join(TMP, '_pert_' + gen)
    open(tmp, 'w').write(pert)
    r = subprocess.run([sys.executable, tmp], capture_output=True, text=True,
                       cwd=HERE)
    got = {t for t, v in LINE.findall(r.stdout) if v == 'FAIL'}
    os.remove(tmp)
    if got == {want}:
        ok += 1
    else:
        print('  NOT DEMONSTRATED  %-22s mutate wanted %s got %s  rc=%d %s'
              % (gen, want, sorted(got), r.returncode,
                 (r.stderr.strip().splitlines() or [''])[-1][:60]))
        bad += 1

import shutil
shutil.rmtree(TMP, ignore_errors=True)

# ---- V12 / the standing rule: no drive may touch a production product ----
after = digests()
moved = [p for p in before if before[p] != after.get(p)]
stray = sorted(os.path.basename(p)
               for p in glob.glob(os.path.join(HERE, '*_drive*')))
if moved:
    print('  A DRIVE WROTE A PRODUCTION PRODUCT: %s' % moved)
    bad += 1
else:
    ok += 1
for p in stray:
    os.remove(os.path.join(HERE, p))
print('  (%d drive outputs written to *_driveN.* and removed; '
      '%d production products byte-identical)' % (len(stray), len(before)))

print('selftest_v409: %d cases, %d demonstrated, %d NOT demonstrated'
      % (3 + len(DRIVES) + len(MUTATE) + 1, ok, bad))
if bad:
    raise SystemExit(1)
