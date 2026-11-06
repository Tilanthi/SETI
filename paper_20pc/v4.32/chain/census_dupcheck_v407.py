#!/usr/bin/env python3
r"""Census / catalogue name-collision tripwires.  GATE -- run by make_all.sh.

Round 8, v4.07.  Three checks, each ALWAYS strict: there is no lenient mode,
because a check that can be switched off is a check that cannot fail.  What
differs between a failing and a passing run is the DATA (and, for C1, the
declared resolution), never the strictness.

  C1  CENSUS.     A display-name collision may only be disambiguated by Gaia
                  source id if the colliding solutions are plausibly the SAME
                  STAR.  Two Gaia sources 10" apart that share a name share an
                  ALMA *field* name, not a stellar identity.  Every collision
                  group must span less than SEP_TOL_ARCSEC, or be declared in
                  FIELD_NAME_COLLISIONS with each member's externally resolved
                  identity.

  C2  CATALOGUE.  One extraction may not be emitted under two star names.
                  Within a physical window (eb, flo_GHz, chanw_Hz), no two rows
                  may agree in EVERY column except star_name/dist_pc.

  C3  CATALOGUE.  Every row's eirp_nominal_W must be consistent with the
                  dist_pc printed beside it, EIRP = 4 pi d^2 S_min dnu with the
                  constant computed from first principles, NOT fitted to the
                  rows it then tests.  A row that inherited another star's EIRP
                  -- or another star's distance -- fails here even if C2 is
                  silenced, which is the point: C2 and C3 are independent
                  routes to the same defect.

  C0  Not a check but a calibration: how often SHOULD (eb, star_snr) collide by
      chance?  A permutation null says lambda ~ 0.1 over the released
      catalogue, so a SINGLE such collision is a 1-in-10 event and proves
      nothing.  The evidence for the defect is full-row identity, not the
      coincidence.

Raises AssertionError (never sys.exit) so selftest_census_v407.py can catch
each failure and prove it fires.

Usage:  census_dupcheck_v407.py [census.csv catalogue.csv]
"""
import csv
import math
import os
import random
import statistics
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CENSUS = os.path.join(HERE, 'ranked_master40pc.csv')
CATALOGUE = os.path.join(HERE, 'per_target_results_v3.99.csv')

SEP_TOL_ARCSEC = 3.0
EIRP_TOL_FRAC = 5e-3
PC_M = 3.0856775814913673e16
#: EIRP[W] = K d[pc]^2 S[mJy] dnu[Hz], S in mJy here because that is the
#: catalogue's column.  Computed, not regressed.
K_EIRP = 4.0 * math.pi * PC_M ** 2 * 1e-29

#: Name collisions that are NOT two identities of one star.  Each entry must
#: name every member and say which physical star it is, resolved from an
#: external catalogue -- a shared ALMA target_name is not evidence.  An empty
#: dict is the pre-audit state of the code, and the pre-repair census fails
#: against it, which is how this check is shown to be able to fail.
#: The same declaration exists in build_ranked_master40pc.py, which writes the
#: census and lives outside the version directory; the two are cross-checked
#: against censusfix_v407.RENAME below.
FIELD_NAME_COLLISIONS = {
    'HD 139084B': {
        '5882581895192805632': 'HD 139084B  (M5Ve companion; SIMBAD pm '
                               '-50.334,-100.036, plx 25.4404 -> 39.31 pc)',
        '5882581895219921024': 'HD 139084  (= V343 Nor A, K0V SB*; SIMBAD pm '
                               '-54.602,-92.786, plx 25.829 -> 38.72 pc) '
                               '-- MISNAMED "HD 139084B" before v4.07',
    },
}


def _sep(a, b):
    dra = ((float(a['ra']) - float(b['ra']))
           * math.cos(math.radians(0.5 * (float(a['dec']) + float(b['dec']))))
           * 3600.0)
    return math.hypot(dra, (float(a['dec']) - float(b['dec'])) * 3600.0)


def census_check(path=CENSUS, declared=None, verbose=True):
    declared = FIELD_NAME_COLLISIONS if declared is None else declared
    C = list(csv.DictReader(open(path)))
    groups = defaultdict(list)
    for r in C:
        groups[r['name'].split(' [')[0]].append(r)
    bad, ok = [], []
    for base, v in sorted(groups.items()):
        if len(v) < 2:
            continue
        sep = max(_sep(v[i], v[j]) for i in range(len(v))
                  for j in range(i + 1, len(v)))
        e = (base, len(v), round(sep, 2))
        if sep > SEP_TOL_ARCSEC:
            ids = {str(r['gaia_source_id']) for r in v}
            if base in declared and set(declared[base]) == ids:
                ok.append(e + ('declared field-name collision',))
            else:
                bad.append(e)
        else:
            ok.append(e + ('same star, two Gaia solutions',))
    if verbose:
        print('C1 census %s: %d entries, %d collision group(s)'
              % (os.path.basename(path), len(C), len(ok) + len(bad)))
        for e in ok + [b + ('UNDECLARED',) for b in bad]:
            print('   %-32s n=%d maxsep=%6.2f"  %s' % e)
    assert not bad, (
        'C1 FAIL: %d display-name collision group(s) span more than %.1f" and '
        'are not declared in FIELD_NAME_COLLISIONS: %s.  A shared name over '
        'that separation is an ALMA FIELD name, so at least one member is '
        'misnamed; appending Gaia digits hides the misnomer behind a '
        'plausible-looking pair.' % (len(bad), SEP_TOL_ARCSEC, bad))
    return ok


def catalogue_check(path=CATALOGUE, verbose=True):
    R = list(csv.DictReader(open(path)))
    IGNORE = {'star_name', 'dist_pc'}
    cols = [c for c in R[0] if c not in IGNORE]
    win = defaultdict(list)
    for r in R:
        win[(r['eb'], r['flo_GHz'], r['chanw_Hz'])].append(r)
    twins = []
    for k, v in win.items():
        if len(v) < 2:
            continue
        sig = defaultdict(list)
        for r in v:
            sig[tuple(r[c] for c in cols)].append(r['star_name'])
        for names in sig.values():
            if len(names) > 1:
                twins.append((k[0], float(k[1]), sorted(set(names))))
    if verbose:
        print('C2 catalogue %s: %d rows, %d physical windows, %d '
              'one-extraction-two-names group(s)'
              % (os.path.basename(path), len(R), len(win), len(twins)))
        for t in sorted(twins)[:8]:
            print('   %s  flo=%.4f  %s' % t)

    def kk(r):
        return (float(r['eirp_nominal_W'])
                / (float(r['dist_pc']) ** 2 * float(r['smin_mJy'])
                   * float(r['chanw_Hz'])))
    v = [kk(r) for r in R if float(r['smin_mJy']) > 0]
    # the first-principles constant is the reference; the sample median is only
    # a cross-check on it, and a large sample must reproduce it.
    med = statistics.median(v)
    if len(R) >= 100:
        assert abs(med / K_EIRP - 1) < 1e-3, (
            'C3 SETUP FAIL: the catalogue median EIRP/(d^2 S dnu) is %.6e, '
            '%.3f per cent from the first-principles 4 pi pc^2 1e-29 = %.6e'
            % (med, 100 * (med / K_EIRP - 1), K_EIRP))
    off = [(r['star_name'], round(float(r['flo_GHz']), 3),
            round(math.sqrt(float(r['eirp_nominal_W'])
                            / (K_EIRP * float(r['smin_mJy'])
                               * float(r['chanw_Hz']))), 4),
            round(float(r['dist_pc']), 4))
           for r in R if float(r['smin_mJy']) > 0
           and abs(kk(r) / K_EIRP - 1) > EIRP_TOL_FRAC]
    if verbose:
        print('C3 EIRP/distance identity: K=%.6e (theory) %.6e (median), '
              '%d of %d rows inconsistent' % (K_EIRP, med, len(off), len(R)))
        for o in off[:6]:
            print('   %-22s flo=%8.3f  EIRP implies d=%.4f, dist_pc=%.4f '
                  '(EIRP scale x%.4f)' % (o + ((o[3] / o[2]) ** 2,)))
    assert not twins, (
        'C2 FAIL: %d catalogue row group(s) are one extraction emitted under '
        'two star names (every column identical except star_name/dist_pc): %s'
        % (len(twins), sorted(twins)[:4]))
    assert not off, (
        'C3 FAIL: %d row(s) carry an eirp_nominal_W computed at a different '
        'distance from the dist_pc printed beside them (star, flo, implied d, '
        'dist_pc): %s' % (len(off), off[:4]))
    return len(R), len(win)


def chance_rate(path=CATALOGUE, trials=2000, seed=1, verbose=True):
    """How often SHOULD (eb, star_snr) collide?  Permutation null."""
    R = list(csv.DictReader(open(path)))
    eb = [r['eb'] for r in R]
    snr = [r['star_snr'] for r in R]
    pairs = sum(c * (c - 1) // 2 for c in Counter(eb).values())
    rng = random.Random(seed)
    tot = 0
    for _ in range(trials):
        s = snr[:]
        rng.shuffle(s)
        tot += sum(x - 1 for x in Counter(zip(eb, s)).values() if x > 1)
    lam = tot / trials
    obs = sum(x - 1 for x in Counter(zip(eb, snr)).values() if x > 1)
    if verbose:
        print('C0 (eb,star_snr): %d within-block row pairs, snr at 4 dp; '
              'expected chance collisions %.3f -> P(>=1)=%.1f%%; observed %d'
              % (pairs, lam, 100 * (1 - math.exp(-lam)), obs))
    return lam, obs


def declaration_agrees():
    """The C1 declaration here and the rename applied to the export must
    describe the same repair, or one of them has been edited alone."""
    import censusfix_v407 as F
    want = {ident.split('(')[0].strip().rstrip('- ').strip()
            for mem in FIELD_NAME_COLLISIONS.values() for ident in mem.values()}
    got = set(F.RENAME.values())
    assert want == got, (
        'C1 declares the resolved identities %s but censusfix_v407.RENAME '
        'produces %s; the declaration and the repair have diverged'
        % (sorted(want), sorted(got)))
    return sorted(want)


if __name__ == '__main__':
    cen = sys.argv[1] if len(sys.argv) > 2 else CENSUS
    cat = sys.argv[2] if len(sys.argv) > 2 else CATALOGUE
    print('declared identities agree with the export repair:',
          declaration_agrees())
    chance_rate(cat)
    census_check(cen)
    catalogue_check(cat)
    print('C1/C2/C3 ALL PASS')
