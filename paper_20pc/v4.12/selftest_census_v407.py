#!/usr/bin/env python3
r"""GATE (v4.07): drive every census / catalogue tripwire in BOTH directions.

A check that cannot fail is not a check.  Seven instances of that family have
been found in this project in two days, one of them inside a brand-new
assertion.  So nothing below is declared to pass: each case says which way it
is driven and what the expected outcome is, and a case that expects FAIL and
gets PASS is itself a failure.

Three groups:

  A.  `census_dupcheck_v407.py`, in process, on the shipped census and
      catalogue and on mutations of them.  The PRE-REPAIR state is not
      reconstructed by hand: the two files as released at v4.06 are shipped in
      `census_fixtures/`, so the failing direction runs on the data that was
      actually published.

  B.  `censusfix_v407.apply()` on the frozen survey export, which is the row
      set the build hands it.  ★ The important case is that the attribution is
      COMPUTED: swap the two distances and the module must keep the OTHER star
      and then trip its declaration cross-check.  Without that pair of cases
      "the retained row is the one the EIRP was computed for" is a claim, not a
      check.

  C.  source perturbations of the two generator-level assertions added in this
      cycle (the n_int join pin in `v342_calc.py` and the star-blind overwrite
      guard in `corrected_export_v399.py`), run in a subprocess with writes
      redirected by a shim on `builtins.open`, so no released product can be
      touched.  A symlink farm would not do: `open(path, 'w')` follows a
      symlink and would truncate the real product.
"""
import contextlib
import copy
import csv
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

import census_dupcheck_v407 as D                      # noqa: E402
import censusfix_v407 as F                            # noqa: E402

FIX_CEN = os.path.join(HERE, 'ranked_master40pc.csv')
FIX_CAT = os.path.join(HERE, 'per_target_results_v3.99.csv')
PRE_CEN = os.path.join(HERE, 'census_fixtures',
                       'ranked_master40pc_prerepair_v406.csv')
PRE_CAT = os.path.join(HERE, 'census_fixtures',
                       'catalogue_prerepair_v406_hd139084.csv')
EXPORT = os.path.join(HERE, 'corrected_export_v399.json')
TMP = tempfile.mkdtemp(prefix='selftest_census_v407_')
RES = []


def run(name, expect, fn):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            fn()
        got, msg = 'PASS', ''
    except AssertionError as e:
        got, msg = 'FAIL', str(e).split('.')[0][:66]
    ok = got == expect
    RES.append((ok, name))
    print('%-4s %-62s expect %-4s got %-4s %s'
          % ('ok' if ok else 'BAD', name, expect, got, msg))


def rewrite(src, mutate, tag='x'):
    R = list(csv.DictReader(open(src)))
    R = mutate(R)
    p = os.path.join(TMP, 'mut_%s.csv' % tag)
    with open(p, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    return p


def _with_k(k, fn):
    old = D.K_EIRP
    D.K_EIRP = k
    try:
        return fn()
    finally:
        D.K_EIRP = old


def _with_rename(new, fn):
    old = F.RENAME
    F.RENAME = new
    try:
        return fn()
    finally:
        F.RENAME = old


# ---------------------------------------------------------------------------
# A.  the three checks, on real released data and on mutations
# ---------------------------------------------------------------------------
run('C1 released (pre-repair) census, declaration EMPTY', 'FAIL',
    lambda: D.census_check(PRE_CEN, declared={}, verbose=False))
run('C1 released (pre-repair) census, collision declared', 'PASS',
    lambda: D.census_check(PRE_CEN, verbose=False))
run('C1 repaired census, declaration EMPTY (fixed at source)', 'PASS',
    lambda: D.census_check(FIX_CEN, declared={}, verbose=False))
run('C1 repaired census with the field name re-injected', 'FAIL',
    lambda: D.census_check(rewrite(FIX_CEN, lambda R: [
        dict(r, name='HD 139084B [%s]' % str(r['gaia_source_id'])[-6:])
        if str(r['gaia_source_id']) in ('5882581895219921024',
                                        '5882581895192805632') else r
        for r in R], 'c1a'), declared={}, verbose=False))
run('C1 declaration present but one Gaia id stale', 'FAIL',
    lambda: D.census_check(PRE_CEN, declared={'HD 139084B': {
        '5882581895192805632': 'x', '9999999999999999999': 'y'}},
        verbose=False))
run('C1 a NEW undeclared wide collision, two unrelated stars', 'FAIL',
    lambda: D.census_check(rewrite(FIX_CEN, lambda R: [
        dict(r, name='Proxima Cen') if r['name'] in ('Proxima Cen', 'HIP 490')
        else r for r in R], 'c1b'), verbose=False))

run('C2+C3 released (pre-repair) catalogue rows', 'FAIL',
    lambda: D.catalogue_check(PRE_CAT, verbose=False))
run('C2+C3 repaired catalogue (the shipped release)', 'PASS',
    lambda: D.catalogue_check(FIX_CAT, verbose=False))
run('C2 repaired + an UNRELATED window duplicated under a 2nd name', 'FAIL',
    lambda: D.catalogue_check(rewrite(FIX_CAT, lambda R: R + [
        dict(next(r for r in R if r['star_name'] == 'Proxima Cen'),
             star_name='Proxima Cen [alias]')], 'c2a'), verbose=False))
run('C3 repaired + one arbitrary dist_pc moved 1 per cent', 'FAIL',
    lambda: D.catalogue_check(rewrite(FIX_CAT, lambda R: [
        dict(r, dist_pc='%.6f' % (float(r['dist_pc']) * 1.01))
        if i == 700 else r for i, r in enumerate(R)], 'c3a'), verbose=False))
run('C3 repaired + the retained rows relabelled with the companion\'s '
    'distance (dedup alone is not enough)', 'FAIL',
    lambda: D.catalogue_check(rewrite(FIX_CAT, lambda R: [
        dict(r, dist_pc='39.3076') if r['star_name'] == 'HD 139084' else r
        for r in R], 'c3b'), verbose=False))
run('C3 setup: the first-principles constant must reproduce as the median',
    'PASS', lambda: D.catalogue_check(FIX_CAT, verbose=False))
run('C3 setup FAILS if the constant is wrong by 1 per cent', 'FAIL',
    lambda: _with_k(D.K_EIRP * 1.01,
                    lambda: D.catalogue_check(FIX_CAT, verbose=False)))


def genuine_fields_survive():
    R = list(csv.DictReader(open(FIX_CAT)))
    g = {}
    for r in R:
        g.setdefault((r['eb'], r['flo_GHz'], r['chanw_Hz']), set()).add(
            r['star_name'])
    groups = {frozenset(v) for v in g.values() if len(v) > 1}
    assert len(groups) == 8, (
        'the eight genuine multi-star fields must survive the repair; got %d: '
        '%s' % (len(groups), sorted(map(sorted, groups))))
    assert not any('HD 139084' in s for s in groups), \
        'the repaired field still carries two stars in one window'


run('the 8 genuine multi-star fields survive (no over-merging)', 'PASS',
    genuine_fields_survive)


def chance_is_not_proof():
    lam, obs = D.chance_rate(FIX_CAT, trials=800, seed=7, verbose=False)
    assert 0.02 < lam < 0.5, 'permutation null %.3f outside expectation' % lam
    assert obs == 0, 'the repaired catalogue still has %d collision(s)' % obs
    lam2, obs2 = D.chance_rate(PRE_CAT, trials=200, seed=7, verbose=False)
    assert obs2 == 4, 'the pre-repair rows no longer show 4 collisions'


run('C0 lambda ~ 0.1, so ONE (eb,star_snr) collision proves nothing', 'PASS',
    chance_is_not_proof)
run('the C1 declaration and the export rename agree', 'PASS',
    D.declaration_agrees)
run('...and disagree if RENAME drops a member', 'FAIL',
    lambda: _with_rename({'HD 139084B 921024': 'HD 139084'},
                         D.declaration_agrees))


# ---------------------------------------------------------------------------
# B.  censusfix_v407.apply() on the row set the build hands it
# ---------------------------------------------------------------------------
def prefix_rows():
    """The row set `corrected_export_v399.py` hands censusfix: the ACA
    re-extraction has already been folded in, which is what CREATED the
    one-extraction-two-names state, so the frozen export will not do -- there
    the two stars are still distinct and correct.  Reconstruct it from the
    shipped export by cloning each retained row back under the name it was
    also emitted as, and check the reconstruction against the rows that were
    actually published at v4.06."""
    rows = copy.deepcopy(json.load(open(EXPORT))['rows'])
    aud = json.load(open(os.path.join(HERE, 'censusfix_v407_audit.json')))
    back = {v: k for k, v in F.RENAME.items()}
    pub = {}
    for r in csv.DictReader(open(PRE_CAT)):
        pub[(r['star_name'], round(float(r['flo_GHz']), 4))] = r
    out = []
    for r in rows:
        if r.pop('census_repaired', None) is None:
            out.append(r)
            continue
        for d in aud['dropped_rows']:
            if d['eb'] != r['eb'] or abs(d['flo'] - r['flo']) > 1e-6:
                continue
            twin = copy.deepcopy(r)
            twin['star_name'] = back.get(d['star_name'],
                                         d['star_name'])
            twin['dist_pc'] = d['dist_pc']
            twin['target'] = (back.get(d['star_name'], d['star_name'])
                              .replace(' ', '_') + '_B7')
            out.append(twin)
        r['star_name'] = back[r['star_name']]
        out.append(r)
    # the reconstruction must reproduce what v4.06 published, row for row
    n = 0
    for r in out:
        k = (r['star_name'], round(min(r['flo'], r['fhi']), 4))
        if k in pub:
            assert abs(float(pub[k]['star_snr']) - r['star_snr']) < 5e-4, k
            assert abs(float(pub[k]['eirp_nominal_W']) / r['eirp'] - 1) < 1e-5, k
            assert abs(float(pub[k]['dist_pc']) - r['dist_pc']) < 1e-3, k
            n += 1
    assert n == 8, ('the reconstructed pre-repair state matches %d of the 8 '
                    'rows v4.06 published' % n)
    return out


AUD = os.path.join(TMP, 'audit.json')


def fix(rows=None, census=FIX_CEN, mutate=None, expect_keep='HD 139084',
        one_extraction=None):
    rows = prefix_rows() if rows is None else rows
    if mutate:
        mutate(rows)
    old = F.ONE_EXTRACTION
    if one_extraction is not None:
        F.ONE_EXTRACTION = one_extraction
    try:
        n_ren, n_drop = F.apply(rows, census=census, audit=AUD, verbose=False)
    finally:
        F.ONE_EXTRACTION = old
    assert n_drop == 4, 'expected 4 dropped rows, got %d' % n_drop
    kept = [r for r in rows if r['star_name'] in ('HD 139084', 'HD 139084B')]
    assert len(kept) == 4, 'expected 4 retained rows, got %d' % len(kept)
    assert {r['star_name'] for r in kept} == {expect_keep}, (
        'retained rows are labelled %s, expected %s'
        % (sorted({r['star_name'] for r in kept}), expect_keep))


run('censusfix on the reconstructed pre-repair rows: 8 renamed, 4 dropped, primary kept',
    'PASS', fix)
run('censusfix with the PRE-REPAIR census (name repair undone at source)',
    'FAIL', lambda: fix(census=PRE_CEN))


def swap_distances(rows):
    """Make the shared EIRP imply the COMPANION's distance instead -- the SAME
    value on both rows, as a single extraction must, so that the only thing
    that moves is which star the measurement belongs to."""
    f = (39.307605808821975 / 38.71618767167229) ** 2
    for r in rows:
        if r['star_name'] in ('HD 139084B 805632', 'HD 139084B 921024'):
            r['eirp'] *= f


def one_extraction_expecting(name):
    return {frozenset(('HD 139084', 'HD 139084B')):
            {'expect_measured': name, 'why': 'selftest'}}


run('★ censusfix attribution is COMPUTED: swap which distance the EIRP '
    'implies and the declaration must trip', 'FAIL',
    lambda: fix(mutate=swap_distances))
run('★ ...and with the declaration changed to match, the OTHER star is kept',
    'PASS', lambda: fix(mutate=swap_distances, expect_keep='HD 139084B',
                        one_extraction=one_extraction_expecting(
                            'HD 139084B')))
run('censusfix: an undeclared one-extraction-two-names group', 'FAIL',
    lambda: fix(one_extraction={}))


def break_k(rows):
    for r in rows:
        if r.get('eirp'):
            r['eirp'] *= 2.0


run('censusfix: the first-principles EIRP constant is not fitted', 'FAIL',
    lambda: fix(mutate=break_k))


def clone_unrelated(rows):
    """One extraction under two names in a window that has nothing to do with
    HD 139084 -- the check must not be hard-wired to this star."""
    victim = next(r for r in rows if r['star_name'] == 'Proxima Cen')
    twin = dict(victim)
    twin['star_name'] = 'Proxima Cen [alias]'
    rows.append(twin)


run('censusfix: an unrelated window duplicated under a 2nd name', 'FAIL',
    lambda: fix(mutate=clone_unrelated))


def offset_one_distance(rows):
    for r in rows:
        if r['star_name'] == 'Proxima Cen':
            r['dist_pc'] *= 1.02
            break


run('censusfix: a row whose EIRP was computed at another distance', 'FAIL',
    lambda: fix(mutate=offset_one_distance))

# ---------------------------------------------------------------------------
# C.  the generator-level assertions, perturbed in source
# ---------------------------------------------------------------------------
SHIM = """
import builtins as _b, os as _o
_ro = _b.open
_TMP = %r


def _wo(file, mode='r', *a, **k):
    if isinstance(file, (str, bytes)) and any(c in mode for c in 'wax+'):
        file = _o.path.join(_TMP, _o.path.basename(
            file.decode() if isinstance(file, bytes) else file))
    return _ro(file, mode, *a, **k)


_b.open = _wo
"""

CASES = [
    # the (star, window) join into the peak-frequency snapshot.  Reinstate the
    # un-canonicalised key -- the code as it stood before v4.07 -- and the pin
    # must fire: this is the silent blank-column failure the repair caused in
    # its first build, and the direction the literal actually moved.
    ('v342_calc.py',
     "    return _canon(' '.join(s.replace('_', ' ').split()))",
     "    return ' '.join(s.replace('_', ' ').split())"),
    # ...and the pin must be a pin, not a bound: lower it and it must fire too
    ('v342_calc.py', '_NO_NINT_PINNED = 1200', '_NO_NINT_PINNED = 1199'),
    # the star-blind overwrite guard: undeclare the one known case
    ('corrected_export_v399.py', "    ('A002_Xcd8029_Xb6b0', 'HD 139084B 921024'):",
     "    ('A002_Xcd8029_Xb6b0', 'NOT THIS STAR'):"),
    # the embedded census in the export must receive the rename
    ('corrected_export_v399.py', 'assert n_cen == len(censusfix_v407.RENAME), (',
     'assert n_cen != len(censusfix_v407.RENAME), ('),
]

for fn, old, new in CASES:
    src = open(os.path.join(HERE, fn)).read()
    name = 'source: %s  %s' % (fn, old.strip()[:40])
    if old not in src:
        print('BAD  %-62s MISSING' % name)
        RES.append((False, name))
        continue
    p = src.replace(old, new, 1)
    p = p.replace("HERE = os.path.dirname(os.path.abspath(__file__))",
                  "HERE = %r" % HERE)
    p = ("import sys\nsys.path.insert(0, %r)\n" % HERE) + SHIM % (TMP,) + p
    tmp = os.path.join(TMP, '_pert_' + fn)
    open(tmp, 'w').write(p)
    r = subprocess.run([sys.executable, tmp], capture_output=True, text=True,
                       cwd=HERE)
    os.remove(tmp)
    ok = r.returncode != 0 and 'AssertionError' in r.stderr
    RES.append((ok, name))
    why = ('exited 0' if r.returncode == 0
           else (r.stderr.strip().splitlines() or ['?'])[-1][:60])
    print('%-4s %-62s expect FAIL got %-4s %s'
          % ('ok' if ok else 'BAD', name, 'FAIL' if ok else 'PASS',
             '' if ok else why))

import shutil                                          # noqa: E402
shutil.rmtree(TMP, ignore_errors=True)
nok = sum(1 for ok, _ in RES if ok)
print('\nselftest_census_v407: %d/%d cases behaved as specified' % (nok,
                                                                    len(RES)))
if nok != len(RES):
    raise SystemExit(1)
