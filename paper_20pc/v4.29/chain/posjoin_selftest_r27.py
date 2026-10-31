"""posjoin_selftest_r27.py -- drives posjoin_r27's picks and its shared-record
assertion on deliberately BROKEN COPIES of the inputs, in both directions.
Reads only; writes nothing anywhere (every perturbation is an in-memory deep
copy).  Exit status 0 only if every drive ends in its expected verdict.

usage: python3 posjoin_selftest_r27.py [<tree>] [<fieldfix json>]
"""
import collections
import copy
import csv
import json
import os
import re
import sys

TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
    os.path.abspath(__file__))
sys.path.insert(0, TREE)
import posjoin_r27 as PJ                                         # noqa: E402

FFXP = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    TREE, 'r8inputs', 'v409', 'fieldfix_v409.json')
CAT = list(csv.DictReader(open(os.path.join(TREE,
                                            'per_target_results_v3.99.csv'))))
EXP = json.load(open(os.path.join(TREE, 'corrected_export_v399.json')))['rows']
FFX = json.load(open(FFXP))


def wkey(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


def skey(s):
    return re.sub(r'\s+', '', s or '').lower()


def shipped_pick(cands, row, namekey):
    """v4.27's `_pick`, verbatim in behaviour: name, else the only candidate,
    else the nearest control maximum."""
    same = [x for x in cands if skey(x.get(namekey)) == skey(row['star_name'])]
    pool = same or cands
    if len(pool) == 1:
        return pool[0]
    return min(pool, key=lambda x: abs(float(x['ctrl_max'])
                                       - float(row['ctrl_max_snr'] or 0)))


def joins(ffx, exp, picker):
    by, ff = collections.defaultdict(list), collections.defaultdict(list)
    for r in exp:
        by[wkey(r['eb'], r['flo'], r['fhi'])].append(r)
    for r in ffx:
        ff[wkey(r['eb'], r['flo'], r['fhi'])].append(r)
    out = []
    for r in CAT:
        k = wkey(r['eb'], r['flo_GHz'], r['fhi_GHz'])
        if by.get(k):
            out.append(('exp', r, picker('exp', by[k], r)))
        if ff.get(k):
            out.append(('rep', r, picker('rep', ff[k], r)))
    return out


def new_picker(kind, c, r):
    return PJ.pick_rep(c, r, TREE) if kind == 'rep' else PJ.pick_exp(c, r)


def old_picker(kind, c, r):
    return shipped_pick(c, r, 'star' if kind == 'rep' else 'star_name')


RES = []


def drive(name, expect, fn):
    """expect: 'pass', 'P1', 'P2', 'P1+P2' (audit clauses that must fire --
    and no other), or 'LookupError'."""
    try:
        fn()
        got = 'pass'
    except AssertionError as e:
        s = str(e)
        got = '+'.join(c for c in ('P1', 'P2') if '\n  %s ' % c in s)
        msg = s.splitlines()[0]
    except LookupError as e:
        got, msg = 'LookupError', str(e)
    ok = got == expect
    RES.append(ok)
    print('%-4s %-62s expect %-11s got %-11s' % ('ok' if ok else 'FAIL',
                                                 name[:62], expect, got))
    if got != 'pass':
        print('       ' + msg[:150])


def rows_of(eb, star=None):
    return [r for r in CAT if r['eb'] == eb and
            (star is None or r['star_name'] == star)]


# ---- D0  the patched join on the real inputs: passes
drive('D0 positional join, real inputs', 'pass',
      lambda: PJ.audit(joins(FFX, EXP, new_picker), 'D0', TREE))

# ---- D1  the SHIPPED join on the real inputs: P1 on HD 139084 A x4
drive('D1 shipped name-fallback join, real inputs (the defect)', 'P1',
      lambda: PJ.audit(joins(FFX, EXP, old_picker), 'D1', TREE))

# ---- a deliberately broken copy: ONE repair record in a two-component
#      window (GJ 2006 A/B, Xfb16 -- a block the r27 fieldtrunc stage 3
#      will repair), positioned on GJ 2006A.
_A = rows_of('A002_Xcdb7b8_Xfb16', 'GJ 2006A')[0]
_pa = PJ.row_pos(_A, TREE)
_rec = copy.deepcopy(FFX[0])
_rec.update(eb=_A['eb'], flo=float(_A['flo_GHz']), fhi=float(_A['fhi_GHz']),
            ra_used=_pa[0], dec_used=_pa[1], dist_pc=float(_A['dist_pc']),
            star='GJ 2006A [B7]', ctrl_max=float(_A['ctrl_max_snr']),
            pos_key='DRIVE|GJ2006A')
#: ★ r27 merge: the field-truncation fold (row 55, FT1) has since REPAIRED
#: Xfb16 for real -- one record for each of GJ 2006 A and B -- so the
#: broken copy first removes the block's real records, then adds the single
#: synthetic one; otherwise the fixture is no longer the defect it models.
FFX_GJ = [r for r in FFX if r['eb'] != _A['eb']] + [_rec]
drive('D2 shipped join, one record in a 2-star window: shared', 'P1+P2',
      lambda: PJ.audit(joins(FFX_GJ, EXP, old_picker), 'D2', TREE))
drive('D3 positional join, same broken copy: A gets it, B nothing', 'pass',
      lambda: PJ.audit(joins(FFX_GJ, EXP, new_picker), 'D3', TREE))

# ---- P2 independent of P1: tolerances widened past the closest distinct
#      pair (2MASS J0524-1601 551040/717696, 0.361", 0.66 % in distance), one
#      record placed on 551040 -> under the POSITIONAL picker both rows
#      accept it, P1 is satisfied for both, and only P2 can see it.
_c = rows_of('A002_Xcf749a_X4871', '2MASS J05241914-1601153 551040')[0]
_pc = PJ.row_pos(_c, TREE)
_rec2 = copy.deepcopy(FFX[0])
_rec2.update(eb=_c['eb'], flo=float(_c['flo_GHz']), fhi=float(_c['fhi_GHz']),
             ra_used=_pc[0], dec_used=_pc[1], dist_pc=float(_c['dist_pc']),
             ctrl_max=float(_c['ctrl_max_snr']), pos_key='DRIVE|J0524')


def _d4():
    t = (PJ.TOL_ARCSEC, PJ.TOL_REL_DIST)
    PJ.TOL_ARCSEC, PJ.TOL_REL_DIST = 1.0, 1.0e-2
    try:
        PJ.audit(joins(FFX + [_rec2], EXP, new_picker), 'D4', TREE)
    finally:
        PJ.TOL_ARCSEC, PJ.TOL_REL_DIST = t


drive('D4 tolerance broken past the closest pair: P2 alone fires', 'P2', _d4)

# ---- export side: G 272-61B's own export rows removed from its window
_gb = 'G 272-61B'
EXP_G = [r for r in EXP if not (r['eb'] == 'A002_X877e41_X14c1'
                                and r['star_name'] == _gb)]
drive('D5 shipped join, B\'s export rows deleted: takes A\'s', 'P1+P2',
      lambda: PJ.audit(joins(FFX, EXP_G, old_picker), 'D5', TREE))
drive('D6 positional join, same copy: fails loudly', 'LookupError',
      lambda: joins(FFX, EXP_G, new_picker))

# ---- the declaration is load-bearing: undeclare HD 139084 B
def _d7():
    saved = dict(PJ.UNCATALOGUED)
    PJ.UNCATALOGUED.clear()
    try:
        joins(FFX, EXP, new_picker)
    finally:
        PJ.UNCATALOGUED.update(saved)


drive('D7 HD 139084 B undeclared: positional join fails loudly',
      'LookupError', _d7)

# ---- two records at one position: ambiguity is an error, not a choice
_dup = [r for r in FFX if r['eb'] == 'A002_X9707f1_Xa89'][0]
_dup2 = copy.deepcopy(_dup)
_dup2['ctrl_max'] = float(_dup['ctrl_max']) + 1.0
drive('D8 two repair records at one star\'s position', 'LookupError',
      lambda: joins(FFX + [_dup2], EXP, new_picker))

# ---- a catalogue row with no position cannot take a repair record
def _d9():
    saved = PJ._POS.pop(TREE, None)
    p = PJ._pos(TREE)
    k = [k for k in p.win if k[1] == 'A002_X9707f1_Xa89']
    for kk in k:
        p.win.pop(kk)
    p.blk.pop(k[0][:2], None)
    try:
        joins(FFX, EXP, new_picker)
    finally:
        PJ._POS.pop(TREE, None)
        if saved is not None:
            PJ._POS[TREE] = saved


drive('D9 row position deleted, repair candidate present', 'LookupError', _d9)

n_ok = sum(RES)
print('%d of %d drives end in their expected verdict' % (n_ok, len(RES)))
sys.exit(0 if n_ok == len(RES) else 1)
