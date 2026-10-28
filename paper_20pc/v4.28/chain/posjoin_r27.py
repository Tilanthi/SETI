"""posjoin_r27.py -- ONE positional join from a catalogue row to the product
records that share its window.  Round 27, register row 56 (r27-pick).

WHY THIS EXISTS.  Five generators (chance_v414, stats_v413, r21_lines,
screen_r23, statunit_v426) each carried a private `_pick(cands, row, ...)`
that chose, among the records sharing a catalogue row's window, the one whose
NAME matched the row's, and -- when no name matched -- fell back to the only
candidate, or to the one with the nearest control maximum.  The repair
records (`fieldfix_v409.json`) name their star in a different format from the
catalogue (`'tau Cet [B6]'` against `'tau Cet'`), so 149 of 149 repair joins
went through the fallback.  148 landed on the right star by luck of there
being only one; the 149th did not: HD 139084 (V343 Nor A, 38.72 pc) in
`A002_Xcd8029_Xb6b0` took the record of HD 139084 B (39.31 pc), 10.3 arcsec
away, and four catalogue rows of A carried B's control vector.  That is the
16th position-blind join this project has found; every one of the previous 15
was fixed the same way, and so is this one: KEY ON POSITION, AND NEVER FALL
BACK TO A NAME.

THE TWO KINDS OF RECORD.
  * a repair record (`fieldfix_v409.json`) carries the position the
    re-extraction used (`ra_used`, `dec_used`) and its parallax distance:
    it is joined on SKY POSITION within `TOL_ARCSEC`, with the distance
    required to agree as a second, independent coordinate.
  * an export row (`corrected_export_v399.json`) carries no sky position at
    all, only its parallax distance: it is joined on DISTANCE within
    `TOL_PC`, and where two export rows of one star share a window (45 such
    windows) on its own published control maximum to 1e-3 -- the same
    content key `chance_v414.py` has always validated the join with.
  No name is read anywhere in this module.

THE CATALOGUE ROW'S OWN POSITION comes from `pbcat_v408.json` (the product's
own `t1_ra`/`t1_dec`, keyed on the catalogue's OWN name and block -- an index
into the catalogue, not a join across products), else from the same star's
entry in another window of the same block (one position per star per block,
asserted to 0.01 arcsec), else from `r27inputs/catpos_r27.json` (the three
eps Eri blocks that joined the census after v4.08, read from each block's
extraction log).  A row with no position anywhere may still join an export
row (distance), but a repair candidate for it is a LookupError.

FAILING LOUDLY.  `pick_rep` and `pick_exp` raise `LookupError` when no
candidate matches and when more than one does.  A row correctly receives
nothing (None) only when every record in its window is either at the
position of ANOTHER catalogued star sharing that window (a multiple of which
one component was re-extracted -- the case the pending Xfb16 and Xed74
records will be the first to exercise) or DECLARED in `UNCATALOGUED` to
belong to a star with no catalogue row.  There is exactly one such star,
HD 139084 B, which the census carries only through `repaired_v409.csv` and
the crossing ledger (the D21 restoration).  A record that matches no
catalogued star and is not declared stops the build.

THE SHARED-RECORD ASSERTION.  `audit(joins, label)` checks, independently of
the picking code, that (P1) every joined record lies at its row's position
(repair: sky and distance; export: distance) and (P2) no single record is
joined to catalogue rows of two different stars -- i.e. two components of
one system never share one repair record.  `posjoin_selftest_r27.py` drives
both clauses on deliberately broken copies.
"""
import collections
import json
import math
import os

#: MEASURED MARGINS (v4.27 catalogue + the r27 fieldtrunc bundle, 153 repair
#: joins, 1,662 export joins; `pick/code/margins.py`):
#:   same star, repair vs catalogue position: max 0.0023 arcsec
#:   closest DISTINCT catalogue stars sharing a window: 0.361 arcsec
#:     (2MASS J05241914-1601153 551040 / 717696, X4871), then 1.418 (LP
#:     476-207), 1.561 (TWA 3A), 1.962 (AT Mic); HD 139084 A/B are 10.30
#:   same star, distance: max 2.3e-5 relative (repair), 4.8e-5 pc (export)
#:   closest distinct stars sharing a window, distance: 0.0323 pc (TX/WW PsA)
TOL_ARCSEC = 0.1
TOL_PC = 1.0e-3
#: relative distance agreement demanded of a repair record already matched
#: on sky -- a second, independent coordinate (HD 139084 A/B: 1.5 per cent).
TOL_REL_DIST = 1.0e-3

#: repair records of stars that have NO catalogue row, by `pos_key`.
UNCATALOGUED = {
    'Hd_139084B_805632_B7_EB_Xb6b0|39.3076|234.736101|-57.705776':
        'HD 139084 B (V343 Nor B, M5Ve, Gaia DR3 ...805632), 10.3 arcsec '
        'from the catalogued primary: restored at v4.09 (D21) through '
        'repaired_v409.csv and the crossing ledger, never as a catalogue row',
}


def sep_arcsec(ra1, de1, ra2, de2):
    """Great-circle separation by the haversine formula (stable at 1e-3")."""
    p1, p2 = math.radians(de1), math.radians(de2)
    dra = math.radians(ra2 - ra1)
    h = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dra / 2) ** 2)
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(h)))) * 3600.0


def _edges(a, b):
    a, b = float(a), float(b)
    return round(min(a, b), 5), round(max(a, b), 5)


class _Pos:
    def __init__(self, tree):
        self.win, self.blk = {}, collections.defaultdict(list)
        self.bywin = collections.defaultdict(list)
        cat = json.load(open(os.path.join(tree, 'pbcat_v408.json')))
        for key, ents in cat.items():
            name, eb = key.rsplit('|', 1)
            for e in ents:
                if e.get('star_ra') is None or e.get('star_dec') is None:
                    continue
                p = (float(e['star_ra']), float(e['star_dec']))
                self.win[(name, eb) + _edges(e['flo'], e['fhi'])] = p
                self.blk[(name, eb)].append(p)
                self.bywin[(eb,) + _edges(e['flo'], e['fhi'])].append(p)
        sup = os.path.join(tree, 'r27inputs', 'catpos_r27.json')
        if os.path.exists(sup):
            for e in json.load(open(sup))['rows']:
                p = (float(e['star_ra']), float(e['star_dec']))
                k = (e['star_name'], e['eb']) + _edges(e['flo_GHz'],
                                                       e['fhi_GHz'])
                assert k not in self.win, ('catpos_r27 duplicates pbcat', k)
                self.win[k] = p
                self.blk[(e['star_name'], e['eb'])].append(p)
                self.bywin[(e['eb'],) + _edges(e['flo_GHz'],
                                               e['fhi_GHz'])].append(p)
        for k, ps in self.blk.items():
            for p in ps[1:]:
                assert sep_arcsec(*ps[0], *p) < 0.01, (
                    'one star, one block, two positions', k, ps[0], p)

    def of(self, row):
        k = (row['star_name'], row['eb'])
        p = self.win.get(k + _edges(row['flo_GHz'], row['fhi_GHz']))
        if p is None and self.blk.get(k):
            p = self.blk[k][0]
        return p


_POS = {}


def _pos(tree):
    if tree not in _POS:
        _POS[tree] = _Pos(tree)
    return _POS[tree]


def row_pos(row, tree):
    return _pos(tree).of(row)


def _rep_at(rec, pos, row):
    if pos is None:
        return False
    if sep_arcsec(pos[0], pos[1], float(rec['ra_used']),
                  float(rec['dec_used'])) > TOL_ARCSEC:
        return False
    d0 = float(row['dist_pc'])
    return abs(float(rec['dist_pc']) - d0) <= TOL_REL_DIST * d0


def _exp_at(rec, row):
    return abs(float(rec['dist_pc']) - float(row['dist_pc'])) <= TOL_PC


def _where(row):
    return '%s %s %s-%s GHz' % (row.get('star_name'), row.get('eb'),
                                row.get('flo_GHz'), row.get('fhi_GHz'))


def pick_rep(cands, row, tree):
    """The repair record at this catalogue row's sky position, or None when
    every record in the window is DECLARED to be another, uncatalogued star.
    Anything else raises."""
    if not cands:
        return None
    pos = row_pos(row, tree)
    if pos is None:
        raise LookupError('posjoin: a repair record shares the window of %s, '
                          'which has no catalogued position' % _where(row))
    m = [c for c in cands if _rep_at(c, pos, row)]
    if len(m) == 1:
        return m[0]
    if len(m) > 1:
        raise LookupError('posjoin: %d repair records at the position of %s'
                          % (len(m), _where(row)))
    # A record not at this row's position is legitimate only if it is at the
    # position of ANOTHER catalogued star sharing the window (a multiple
    # where one component was re-extracted) or is declared uncatalogued.
    others = _pos(tree).bywin.get((row['eb'],) + _edges(row['flo_GHz'],
                                                        row['fhi_GHz']), [])
    stray = [c.get('pos_key') for c in cands
             if c.get('pos_key') not in UNCATALOGUED
             and not any(sep_arcsec(o[0], o[1], float(c['ra_used']),
                                    float(c['dec_used'])) <= TOL_ARCSEC
                         for o in others)]
    if stray:
        raise LookupError('posjoin: no repair record at the position of %s; '
                          'the window holds undeclared %s'
                          % (_where(row), stray))
    return None


def pick_exp(cands, row):
    """The export row of this catalogue row's star (by parallax distance),
    disambiguated by the row's own published control maximum.  Raises unless
    exactly one record -- or several byte-identical ones -- remain."""
    if not cands:
        return None
    m = [c for c in cands if _exp_at(c, row)]
    if len(m) > 1 and (row.get('ctrl_max_snr') or '') != '':
        cm = float(row['ctrl_max_snr'])
        m = [c for c in m if abs(float(c['ctrl_max']) - cm) <= 1e-3]
    # Two extractions of ONE star in one window (45 windows: e.g. AU Mic
    # X26ec, a frozen-geometry and a position-routed extraction agreeing to
    # float32).  They are one star only if they carry the SAME Gaia distance
    # to the last bit; then the nearest published control maximum chooses,
    # exactly as the shipped join did, so no same-star choice changes here.
    if len(m) > 1 and len({float(c['dist_pc']) for c in m}) == 1:
        cm = float(row.get('ctrl_max_snr') or 0)
        m = [min(m, key=lambda x: abs(float(x['ctrl_max']) - cm))]
    if len(m) != 1:
        raise LookupError('posjoin: %d export rows at the distance of %s'
                          % (len(m), _where(row)))
    return m[0]


def audit(joins, label, tree):
    """`joins` = iterable of (kind, row, record), kind 'rep' or 'exp'.
    P1: every record lies at its row's position.  P2: no record is joined to
    two different stars (two components of one system never share a
    record).  Independent of pick_*: it re-derives ownership from the
    record's own coordinates.  Raises AssertionError naming every failure;
    returns (n_joins, n_records) for the caller to print."""
    bad, owners = [], collections.defaultdict(set)
    n = 0
    for kind, row, rec in joins:
        if rec is None:
            continue
        n += 1
        pos = row_pos(row, tree)
        ok = _rep_at(rec, pos, row) if kind == 'rep' else _exp_at(rec, row)
        if not ok:
            bad.append('P1 %s record %s joined to %s, which is not at its '
                       'position' % (kind, rec.get('pos_key') or
                                     rec.get('target'), _where(row)))
        ident = (row['star_name'],
                 None if pos is None else (round(pos[0], 4),
                                           round(pos[1], 4)),
                 round(float(row['dist_pc']), 3))
        owners[(kind, id(rec))].add(ident)
    for (kind, _), ids in owners.items():
        if len(ids) > 1:
            bad.append('P2 one %s record shared by %d stars: %s'
                       % (kind, len(ids), sorted(ids, key=str)))
    if bad:
        raise AssertionError('posjoin audit [%s]: %d failure(s)\n  %s'
                             % (label, len(bad), '\n  '.join(bad)))
    return n, len(owners)
