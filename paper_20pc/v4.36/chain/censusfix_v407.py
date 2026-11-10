#!/usr/bin/env python3
r"""Fold the round-8 CENSUS NAME-COLLISION repair into the survey export.

Round 8, `referee_r8/CENSUS_DUPLICATES.md`, corrected by direct inspection of
the two extractions on the processing host (2026-09-27, recorded in
`BUILD_NOTES_V407.md`).

WHAT THE DEFECT IS
------------------
`build_ranked_master40pc.py`'s `best_display_name()` returns the ALMA *field*
name for a disc host.  The field `HD_139084B` contains **two** catalogued stars
10.32" apart, so both inherited the name `HD 139084B`, and the digit
disambiguator then dressed the pair up as two Gaia solutions of one star.
`canon_names_v381.py` canonicalises search results to census stars **by name**,
so one product set was attached to both entries.

IT IS NOT A DUPLICATION; IT IS A MISATTRIBUTION.  Both stars were extracted
separately on the host, at their own positions (primary-beam offsets 5.092" and
5.208"), and the two extractions give different statistics in all four windows.
The four released rows carry the **...921024** numbers -- i.e. the measurement
of the PRIMARY, `HD 139084` (= V343 Nor A, K0V; SIMBAD proper motion
-54.602,-92.786 and parallax 25.829 both reproduce) -- written out twice, once
under each name.  The secondary's own extraction (`...805632`, HD 139084B,
M5Ve) never entered the catalogue at all.

So the repair is NOT "delete one row and rescale the other's EIRP by 1.0308".
Rescaling would have manufactured a limit for the M5V secondary out of the K0V
primary's data.  The repair is:

  * rename the census entry `...921024` to `HD 139084` (done at the census
    generator; this module ASSERTS the census it is handed carries the repair,
    so it cannot silently come undone);
  * keep the four rows ONCE, under the star the data say was measured, which
    this module DETERMINES rather than declares: the retained name is the one
    whose `dist_pc` reproduces the distance implied by the row's own EIRP;
  * drop the other name's copy, and record it in the audit sidecar together
    with the fact that that star's own extraction exists and is NOT in this
    release;
  * check the EIRP <-> distance identity on EVERY remaining row, so a row that
    carries another star's EIRP can never ship again.

WHY IT LIVES HERE
-----------------
Same reasoning as `fieldfix_v404.py`, and the same lesson from v3.99:
`v342_calc.py` rebuilds the released catalogue from the export on every build,
so a patch applied to the catalogue CSV is silently discarded; and
`apply_holdout_v381.py` *writes* the frozen export, so the repair cannot live
upstream of it either.  Applying it inside the stage that already builds the
export means not one of the seventeen read sites changes.

Row provenance is extended, not replaced: a retained row keeps whatever
`corrected_export_v399.py` and `fieldfix_v404.py` gave it and gains the
`census_repaired` flag.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CENSUS = os.path.join(HERE, 'ranked_master40pc.csv')
AUDIT = os.path.join(HERE, 'censusfix_v407_audit.json')

#: EIRP = 4 pi d^2 S_min dnu.  With d in pc, S_min in Jy and dnu in Hz the
#: constant is 4 pi (1 pc in m)^2 x 1e-26, computed here rather than fitted:
#: a constant obtained by regression on the rows it then tests would make C3 a
#: check that cannot fail.  The measured median is asserted against it below.
PC_M = 3.0856775814913673e16
K_EIRP = 4.0 * math.pi * PC_M ** 2 * 1e-26
EIRP_TOL = 5e-3          # the identity holds to 4e-16 on 1,721 of 1,725 rows
K_TOL = 1e-3             # first-principles constant vs the export's median

#: Census name repairs, from the resolved identities in
#: `build_ranked_master40pc.py:FIELD_NAME_COLLISIONS`.  Keyed on the export's
#: own spelling (the canonicaliser writes " 921024" where the census writes
#: "[921024]").
RENAME = {
    'HD 139084B 921024': 'HD 139084',
    # the suffix existed only to separate the two; with the collision resolved
    # at its source the secondary carries its own name, exactly as the repaired
    # census spells it.  Leaving the suffix on would advertise a
    # disambiguation of something that is no longer ambiguous.
    'HD 139084B 805632': 'HD 139084B',
}

#: Field-name collisions whose members were emitted as ONE extraction under
#: TWO names.  The value is documentation and a cross-check on the computed
#: attribution -- never its source.
ONE_EXTRACTION = {
    frozenset(('HD 139084', 'HD 139084B')): {
        'expect_measured': 'HD 139084',
        'why': 'the A component (Gaia ...921024, pb offset 5.208") is the '
               'extraction the released rows carry; the B component '
               '(...805632, 5.092") was extracted separately on the host and '
               'is not in this release',
    },
}


def _windowkey(r):
    lo, hi = sorted((float(r['flo']), float(r['fhi'])))
    return (r['eb'], round(lo, 6), round(hi, 6), r['chanw'])


def _implied_distance(r):
    """The distance the row's own EIRP was computed at, in pc."""
    return math.sqrt(r['eirp'] / (K_EIRP * r['smin'] * r['chanw']))


def apply(rows, census=CENSUS, audit=AUDIT, verbose=True):
    """Repair `rows` in place.  Returns (n_renamed, n_dropped)."""
    # ---- 0. the census must already carry the repair ----------------------
    names = {r['name'] for r in csv.DictReader(open(census))}
    for old, new in RENAME.items():
        assert new in names, (
            'the census at %s does not contain the repaired name %r; the '
            'name collision was resolved in build_ranked_master40pc.py and '
            'that repair has come undone (or the wrong census is being read)'
            % (census, new))
    _stale = sorted(n for n in names if ' [' in n and n.split(' [')[0]
                    in {v for v in RENAME.values()} | {'HD 139084B'})
    assert not _stale, (
        'the census still disambiguates a declared field-name collision by '
        'Gaia digits: %s' % _stale)

    # ---- 1. the constant, checked against the export itself ---------------
    kk = [r['eirp'] / (r['dist_pc'] ** 2 * r['smin'] * r['chanw'])
          for r in rows if r.get('eirp') and r.get('smin') and r.get('chanw')
          and r.get('dist_pc')]
    kk.sort()
    kmed = kk[len(kk) // 2]
    assert abs(kmed / K_EIRP - 1) < K_TOL, (
        'the export median EIRP/(d^2 S dnu) is %.6e, %.2f per cent from the '
        'first-principles 4 pi pc^2 1e-26 = %.6e; C3 would then be measuring '
        'the rows against themselves'
        % (kmed, 100 * (kmed / K_EIRP - 1), K_EIRP))

    # ---- 2. rename ---------------------------------------------------------
    n_ren = 0
    for r in rows:
        new = RENAME.get(r['star_name'])
        if new:
            r['star_name'] = new
            r['census_repaired'] = 'renamed'
            n_ren += 1
    assert n_ren, ('no row carries any of the names to be renamed (%s); the '
                   'export naming has moved' % sorted(RENAME))

    # ---- 3. one extraction, two names -------------------------------------
    win = {}
    for r in rows:
        win.setdefault(_windowkey(r), []).append(r)
    IGNORE = {'star_name', 'dist_pc', 'target', 'census_repaired'}
    dropped, groups = [], []
    for k, v in sorted(win.items()):
        if len(v) < 2:
            continue
        # the signature runs over the UNION of the group's keys, so a row that
        # merely carries an extra key cannot slip past as "not identical"
        cols = sorted({c for r in v for c in r} - IGNORE)
        sig = {}
        for r in v:
            s = tuple(repr(r.get(c)) for c in cols)
            sig.setdefault(s, []).append(r)
        for rs in sig.values():
            if len(rs) < 2:
                continue
            nm = frozenset(r['star_name'] for r in rs)
            dec = ONE_EXTRACTION.get(nm)
            assert dec is not None, (
                'window %s carries %d rows that agree in EVERY column except '
                'star_name/dist_pc/target, under names %s.  One extraction '
                'may not be emitted under two star names; if these really are '
                'two measurements, they cannot be identical to the last bit '
                'of all %d control draws.'
                % (k[0], len(rs), sorted(nm), len(rs[0].get('ctrl_all') or [])))
            # WHICH star was measured is computed, not declared: the EIRP was
            # evaluated at the extraction's own distance.
            di = _implied_distance(rs[0])
            cand = [r for r in rs
                    if abs(r['dist_pc'] / di - 1) < 0.5 * EIRP_TOL]
            assert len(cand) == 1, (
                'the EIRP of window %s %.4f GHz implies d = %.4f pc, which '
                'matches %d of the %d candidate distances %s -- the measured '
                'star cannot be identified, so nothing may be dropped'
                % (k[0], k[1], di, len(cand), len(rs),
                   [round(r['dist_pc'], 4) for r in rs]))
            keep = cand[0]
            assert keep['star_name'] == dec['expect_measured'], (
                'the row set of window %s %.4f GHz was measured at %.4f pc, '
                'i.e. %r, but the declaration expects %r.  Correct the '
                'declaration only with evidence from the extraction itself.'
                % (k[0], k[1], di, keep['star_name'], dec['expect_measured']))
            keep['census_repaired'] = '+'.join(
                filter(None, (keep.get('census_repaired'), 'retained')))
            for r in rs:
                if r is keep:
                    continue
                dropped.append(dict(
                    star_name=r['star_name'], eb=r['eb'],
                    flo=r['flo'], chanw=r['chanw'],
                    dist_pc=r['dist_pc'], star_snr=r['star_snr'],
                    eirp=r['eirp'],
                    reason='one extraction emitted under two names; measured '
                           'star is %s (EIRP implies d = %.4f pc)'
                           % (keep['star_name'], di)))
                r['_drop'] = True
            groups.append(dict(eb=k[0], flo=k[1], chanw=k[3],
                               names=sorted(nm), kept=keep['star_name'],
                               implied_distance_pc=di, why=dec['why']))
    before = len(rows)
    rows[:] = [r for r in rows if not r.pop('_drop', False)]
    n_drop = before - len(rows)
    assert n_drop == len(dropped)

    # ---- 4. no row may print a distance its EIRP was not computed at -------
    bad = []
    for r in rows:
        if not (r.get('eirp') and r.get('smin') and r.get('chanw')
                and r.get('dist_pc')):
            continue
        di = _implied_distance(r)
        if abs(di / r['dist_pc'] - 1) > EIRP_TOL:
            bad.append((r['star_name'], r['eb'], round(r['flo'], 4),
                        round(r['dist_pc'], 4), round(di, 4)))
    assert not bad, (
        '%d row(s) carry an EIRP computed at a distance that is not the '
        'dist_pc printed beside them (star, eb, flo, dist_pc, implied): %s'
        % (len(bad), bad[:6]))

    rec = dict(renamed=n_ren, dropped=n_drop, rows_out=len(rows),
               k_first_principles=K_EIRP, k_export_median=kmed,
               groups=groups, dropped_rows=dropped,
               note='the dropped rows are NOT a second measurement: they are '
                    'the retained extraction written out under a second '
                    'census name.  The star they were labelled with has an '
                    'extraction of its own on the processing host which is '
                    'not in this release; see BUILD_NOTES_V407.md.')
    json.dump(rec, open(audit, 'w'), indent=1)
    if verbose:
        print('censusfix_v407: %d renamed, %d dropped, %d rows out; '
              'K measured/theory = %.8f'
              % (n_ren, n_drop, len(rows), kmed / K_EIRP))
        for g in groups:
            print('  %s %.4f GHz: %s -> kept %s (EIRP implies %.4f pc)'
                  % (g['eb'], g['flo'], '/'.join(g['names']), g['kept'],
                     g['implied_distance_pc']))
    return n_ren, n_drop


def repair_census_list(census_rows):
    """Apply the same rename to an export's EMBEDDED census list, whose
    entries spell the suffix `[921024]`."""
    n = 0
    for c in census_rows or []:
        base = str(c.get('name', ''))
        for old, new in RENAME.items():
            stem, _, sid = old.rpartition(' ')
            if base == '%s [%s]' % (stem, sid):
                c['name'] = new
                n += 1
    return n


if __name__ == '__main__':
    raise SystemExit('censusfix_v407 is applied by corrected_export_v399.py, '
                     'which owns the export file; running it alone would '
                     'write nothing.')
