#!/usr/bin/env python3
r"""GATE (round 27, row 52): no window takes a systemic velocity from a match
the snapshot rejected, or from an object that is not the star.

WHY THIS EXISTS.  `r26inputs/vsys_r26.json` records, for every target, the
SIMBAD object its velocity came from, the separation, the parallax agreement
and a verdict `plx_ok`.  `unmask_r26.py` read the velocity and never the
verdict, so LP 736-15 and PM J03433+1958 were placed in the rest frames of
UCAC2 27300936 (79 arcsec away, parallax 1.4 mas against 47.3) and
UCAC4 550-007537 (100 arcsec away, 0.3 mas against 48.2) -- objects the same
file had rejected.  The fifteenth star-blind or wrong-object join in this
project.  A flag the consumer does not read is not a check, so this gate does
not rely on the generator reading it either: it re-reads what the build
CONSUMED and re-decides identity from the astrometry.

THE INVARIANT (no star, value or count from today is pinned):
  for every searched window whose systemic velocity came from the snapshot --
  i.e. the article's own lookup (`maskframe_v411.vsys`) has none and the
  window carries one --
    V1  the entry it came from (vsys_r26 with r27 supersessions applied) has
        plx_ok true, and plx_ok agrees with its own plx_match against the
        tolerance the snapshot's provenance states;
    V2  the velocity object is the target, decided on numbers: the same Gaia
        DR3 source, or within R_SELF of the target's position propagated to
        J2000 by the target's own proper motion.  Otherwise it is a different
        object and passes only if DECLARED a companion AND co-distant (the
        snapshot's parallax tolerance), within SEP_AU_MAX projected and within
        DVT_MAX in tangential velocity -- an undeclared or distant object fails
        however its flag reads;
    V3  the value in the window is the entry's value;
  and, so that a new target cannot arrive unverified,
    V4  every snapshot entry carrying a velocity has an astrometric record,
        and that record's target parallax agrees with the adopted distance.

Writes nothing.  Exit status 1 on any failure.

    python3 vsysgate_r27.py [TREE]        (default: the directory of this file)
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

R_SELF = 2.0          # arcsec: same object, after the target's own motion
SEP_AU_MAX = 1000.0   # a declared companion must be bound-pair close
DVT_MAX = 15.0        # km/s: tangential-velocity difference of a bound pair
K = 4.740470446       # km/s per (mas/yr / mas)


def sep_arcsec(a1, d1, a2, d2):
    a1, d1, a2, d2 = map(math.radians, (a1, d1, a2, d2))
    c = (math.sin(d1) * math.sin(d2)
         + math.cos(d1) * math.cos(d2) * math.cos(a1 - a2))
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * 3600.0


def main(tree):
    tree = os.path.abspath(tree)
    fail = []

    def ck(name, ok, detail):
        print('  %-4s %s %s' % ('PASS' if ok else 'FAIL', name, detail))
        if not ok:
            fail.append(name.split()[0])

    v26 = json.load(open(os.path.join(tree, 'r26inputs', 'vsys_r26.json')))
    p27 = os.path.join(tree, 'r27inputs', 'vsys_r27.json')
    if not os.path.exists(p27):
        ck('V0 the astrometric verification record exists', False, p27)
        return 1
    v27 = json.load(open(p27))
    m = re.search(r'within\s+(\d+)\s+per\s+cent', v26['_provenance'])
    assert m, 'the snapshot provenance no longer states its parallax tolerance'
    tol = int(m.group(1)) / 100.0

    snap = {k: dict(e) for k, e in v26['v_sys_kms'].items()}
    for k, e in v27['supersede'].items():
        assert k in snap, ('a supersession names no snapshot entry', k)
        snap[k].update({f: v for f, v in e.items() if f != 'superseded'})
    ast, comp = v27['astrometry'], v27['companions']

    # the article's own lookup, imported read-only from the tree under test
    sys.path.insert(0, tree)
    sys.dont_write_bytecode = True
    import maskframe_v411 as mf                                # noqa: E402

    rec = json.load(open(os.path.join(tree, 'unmask_r26.json')))
    used = {}
    for w in rec['windows']:
        if mf.vsys(w['star'])[0] is None and w['v_sys_kms'] is not None:
            used.setdefault(w['star'], set()).add(w['v_sys_kms'])
    ck('V0 the gate measures a non-empty set',
       len(used) > 0, '%d targets take a velocity from the snapshot' % len(used))

    v1, v2, v3 = [], [], []
    kinds = {}
    for k in sorted(used):
        e = snap.get(k)
        if e is None:
            v3.append((k, 'no snapshot entry at all'))
            continue
        pm = e.get('plx_match')
        if not (e.get('plx_ok') is True and pm is not None and pm <= tol):
            v1.append((k, e.get('main_id'), e.get('plx_ok'), pm))
        if used[k] != {e.get('v_sys_kms')}:
            v3.append((k, sorted(used[k]), e.get('v_sys_kms')))
        a = ast.get(k)
        if a is None or a.get('target') is None:
            v2.append((k, 'no astrometric record'))
            continue
        t = a['target']
        o = a.get('vel_object_r27', a.get('vel_object')) \
            if k in v27['supersede'] else a.get('vel_object')
        if o is None:
            v2.append((k, 'velocity carried but no velocity object recorded'))
            continue
        if o.get('gaia_dr3') and o['gaia_dr3'] == t['gaia_dr3']:
            kinds[k] = 'self (same Gaia DR3 source)'
            continue
        if o.get('ra_2000') is None:
            v2.append((k, 'velocity object has neither a Gaia id nor a position'))
            continue
        cosd = math.cos(math.radians(t['dec_2016']))
        ra0 = t['ra_2016'] - t['pmra'] / 3.6e6 * 16.0 / cosd
        de0 = t['dec_2016'] - t['pmdec'] / 3.6e6 * 16.0
        s = sep_arcsec(ra0, de0, o['ra_2000'], o['dec_2000'])
        if s <= R_SELF:
            kinds[k] = 'self (%.2f arcsec at J2000)' % s
            continue
        au = s * 1000.0 / t['parallax']
        dplx = (abs(o['parallax'] - t['parallax']) / t['parallax']
                if o.get('parallax') else None)
        dvt = (K * math.hypot(o['pmra'] - t['pmra'], o['pmdec'] - t['pmdec'])
               / t['parallax'] if o.get('pmra') is not None else None)
        ok = (k in comp and dplx is not None and dplx <= tol
              and au <= SEP_AU_MAX and dvt is not None and dvt <= DVT_MAX)
        if ok:
            kinds[k] = 'declared companion (%.1f arcsec, %.0f au, dplx %.3f, dvt %.1f km/s)' % (s, au, dplx, dvt)
        else:
            v2.append((k, o.get('simbad_main_id'), round(s, 1), round(au),
                       None if dplx is None else round(dplx, 3),
                       None if dvt is None else round(dvt, 1),
                       'declared' if k in comp else 'undeclared'))

    ck('V1 no window takes a velocity from a match the snapshot rejected '
       '(plx_ok, and plx_match within %.0f per cent)' % (100 * tol),
       not v1, '%d of %d consumed entries fail: %s' % (len(v1), len(used), v1))
    ck('V2 every consumed velocity belongs to the star, or to a DECLARED '
       'co-distant bound companion (<= %.0f au, <= %.0f km/s)' % (SEP_AU_MAX, DVT_MAX),
       not v2, '%d fail: %s; %d self, %d declared companions'
       % (len(v2), v2, sum(1 for x in kinds.values() if x.startswith('self')),
          sum(1 for x in kinds.values() if x.startswith('declared'))))
    ck('V3 the value each window carries is its entry\'s value',
       not v3, '%d mismatch(es): %s' % (len(v3), v3))

    v4 = []
    for k, e in snap.items():
        if e.get('v_sys_kms') is None:
            continue
        a = ast.get(k)
        if a is None or a.get('target') is None:
            v4.append((k, 'no record'))
            continue
        p0 = 1000.0 / e['dist_pc']
        if abs(a['target']['parallax'] - p0) / p0 > tol:
            v4.append((k, 'target parallax %.2f against adopted %.2f'
                       % (a['target']['parallax'], p0)))
    ck('V4 every snapshot velocity has an astrometric record whose target '
       'parallax is the adopted distance',
       not v4, '%d of %d fail: %s' % (len(v4), sum(1 for e in snap.values()
                                                  if e.get('v_sys_kms') is not None), v4))
    print('  info declared companions and how each was decided: %s'
          % {k: kinds.get(k, 'not consumed by any window') for k in sorted(comp)})
    print('vsysgate_r27: %d clause(s) failed %s' % (len(fail), fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else os.path.dirname(os.path.abspath(__file__))))
