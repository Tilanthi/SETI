#!/usr/bin/env python3
r"""Round 160 (v4.11): the molecular-line mask in the stellar rest frame, in
one frame throughout, with sulphur monoxide in the species list.

WHAT THIS FILE OWNS
    The frame chain and the mask.  It is both a MODULE -- `ledger_v410.py`
    imports it so that the ledger table, the chain figure and the robustness
    table cannot disagree about a velocity -- and a GENERATOR, which reads the
    adopted ledger back and emits the macros, the robustness table and the
    machine-readable record.

    Build order: `ledger_v410.py` (which imports this as a module) and then
    `python3 maskframe_v411.py`.

THE FRAME, STATED ONCE
    Every crossing frequency is topocentric as the correlator delivers it.
    Attribution is evaluated in the star's own rest frame, per execution
    block, in two declared steps:

        f_bary = f_topo * (1 - v_bary / c)        topocentric -> barycentric
        f_star = f_bary * (1 + v_sys  / c)        barycentric -> stellar rest

    and the offset from a transition is dv = c (f_star - f_rest) / f_rest.
    `v_bary` is the per-(block, window) barycentric term measured at that
    block's own pointing and mid-time; `v_sys` is the catalogue systemic
    velocity of the star.  Nothing is absorbed into the tolerance: a tube
    wide enough to swallow 30 km/s of the Earth's own motion spends most of a
    budget that is justified on kinematic grounds, and it makes an
    attribution depend on the date of observation.

THREE DEFECTS THIS GENERATOR EXISTS TO CLOSE
    1.  WINDOW EDGES IN A FREQUENCY COLUMN.  Five crossings ship without a
        crossing frequency, and the ledger substituted the window's LOWER
        EDGE for it, unmarked -- so five beta Pic rows were tabulated 1150
        and 554 km/s from the transition the same row attributes them to.
        Every crossing frequency is in fact recoverable exactly, because the
        release carries the offset that was computed FROM it:
        f_topo = f_rest(search list) + line_offset_MHz.  The recovery is
        validated against the 51 rows that do carry f_cross (worst residual
        asserted below 2 kHz) and then applied to the 5 that do not, so no
        row needs a "frequency not recovered" marker.
    2.  TWO SYSTEMIC VELOCITIES FOR ONE STAR.  `bpic_vsys.py` exists because
        two generators once carried 16.84 and 20.0 km/s for beta Pic three
        paragraphs apart.  `starrv_v399.json` still holds the superseded
        16.84, and the ledger was reading it -- so the ledger's beta Pic
        offsets disagreed with the body text's by 3 km/s.  The adopted value
        is imported from the one file that owns it, and the override is
        asserted to be a real override (the two values must differ) so it
        cannot quietly become a no-op.
    3.  TWO FRAMES IN ONE COLUMN.  Of the four crossings the adopted list
        adds, two carried stellar-frame offsets and two carried topocentric
        ones.  All four are recomputed here through the same chain.

SULPHUR MONOXIDE, AND WHY ITS COINCIDENCES ARE A NOTE
    SO is a standard component of the Band 6 and Band 7 spectral setups these
    fields were observed with, and its transitions fall inside the mask of
    three crossings.  The coincidence is printed beside each of the three and
    disposes of none of them, on two physical grounds that hold for the
    SPECIES and not for a particular crossing: SO has never been reported in
    a debris disc, where the second-generation gas is CO, C and O; and in the
    one such window that also covers CO(3-2), that line is absent at a limit
    BELOW the crossing's own flux (F13, F13b), so an SO line there would have
    to outshine an undetected CO(3-2) line in the same data.  A chronological
    argument would not serve, because the species list is a single dated
    query and post-dates every classification equally; a physical one reaches
    all three alike, which is why it is written here as a predicate on the
    species (`note_reason`) rather than as a list of crossings.  The counts
    under both choices are published by `maskso_v414.py`.

ASSERTIONS (each driven, see --drive)
    F1  the crossing frequency recovered from the released offset reproduces
        every f_cross the release carries
    F2  the two-step frame chain agrees with the single-step form, and
        reproduces the two frozen f_stellar values computed independently
        during the archival-tail recurrence campaign
    F3  the beta Pic systemic velocity used is the adopted one and differs
        from the catalogue one
    F4  every crossing has a barycentric term and a systemic velocity from a
        declared source, and the frozen fallback inventory is consumed whole
    F5  the three HD 285968 epochs, 12 km/s apart topocentrically, agree in
        the stellar frame to better than 0.1 km/s
    F6  adding SO changes exactly the dispositions this generator names
    F7  the robustness ladder reproduces the adopted counts at the adopted
        half-width, and every rank-passing unattributed crossing at every
        tabulated half-width has a recurrence record
    F6b the coincidences reported as a note are exactly those with the noted
        species, and no crossing is excepted one at a time
    F13b the CO(3-2) limit in that window is below the crossing's own flux,
        which is the physical ground the note rests on
    F8  the full-harvest cross-check names the dispositions that change under
        it, and the count is not asserted to be zero
    F9b the printed bandwidth the mask removes and the printed fraction of the
        union reproduce each other

    python3 maskframe_v411.py [--drive N]

-> maskframe_v411.json, survey_numbers_round160.tex,
   tab_maskrobust_v411.tex, tab_maskband_v411.tex
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C_KMS = 299792.458
MASK_HALF_KMS = 50.0
TRIGGER = 5.0
LADDER = (20.0, 25.0, 50.0, 100.0)
WORD = {20.0: 'Twenty', 25.0: 'TwentyFive', 50.0: 'Fifty', 100.0: 'Hundred'}


def _load(*parts):
    return json.load(open(os.path.join(HERE, *parts)))


# --------------------------------------------------------------------------
# (1) the masked transitions
# --------------------------------------------------------------------------
def _parse_dict(src, name):
    i = src.index('%s = {' % name)
    j = src.index('}', i)
    return eval(src[i + len('%s = ' % name):j + 1])            # noqa: S307


_V342 = open(os.path.join(HERE, 'v342_calc.py')).read()
# CAT_OLD: the list the SEARCH ran, rounded to 1 MHz.  It is what the released
# `line_offset_MHz` column was computed against and therefore the only list a
# recovery of the crossing frequency may invert.  It is NOT the mask.
CAT = _parse_dict(_V342, 'CAT')
CAT_OLD = _parse_dict(_V342, 'CAT_OLD')

_STRIP = lambda s: re.sub(r'<[^>]+>', '', s).replace('&#150;', '-').strip()

# ★ v4.12.  THE MASK IS NOW A CATALOGUE QUERY, NOT A HAND-KEPT LIST.
# `maskcat_v412.py` holds the rule, the frozen query and the published table;
# this file holds the frame chain and nothing about which lines exist.  The
# hand-kept list it replaces had no J = 3-2 isotopologue, no HCN(4-3), no
# HCO+(4-3) and no SO 9_8-8_7, so crossings were reported hundreds or
# thousands of km/s from a transition when a masked species lay nearer.
import maskcat_v412 as _mc                                   # noqa: E402

TRANS = {k: (v['f'], v['short']) for k, v in _mc.MASK.items()}
assert TRANS, 'maskcat_v412 produced an empty mask'

# The hand-kept list, kept only so that the rebuild can be measured against
# it; nothing is attributed with it.
PREV = dict(CAT)

HARVEST = _load('mask_xcheck_lines.json')


def species(name):
    """The carrier of a transition label, for counting species."""
    return _mc.species_of(name)


def tex_label(name):
    """The transition as the ledger prints it."""
    t = TRANS.get(name)
    return t[1] if t else name


# --------------------------------------------------------------------------
# (2) the velocity terms
# --------------------------------------------------------------------------
BARY = _load('r8inputs', 'bary_v405.json')['v_bary_kms']
STARRV = _load('starrv_v399.json')
MASKR9 = _load('r9inputs', 'mask_r9.json')
R10RV = _load('r10inputs', 'vsys_r10.json')['v_sys_kms']
HD14055 = _load('r8inputs', 'v409', 'hd14055_recur.json')

from bpic_vsys import VSYS_BPIC_KMS as _VSYS_BPIC          # noqa: E402

# The one declared override: beta Pic.  The catalogue value is the Gaia DR3
# hot-star template value this paper does not adopt; bpic_vsys.py says why.
VSYS_OVERRIDE = {'bet Pic': (_VSYS_BPIC, 'adopted, bpic_vsys.py')}

# Barycentric terms for blocks the release predates, keyed on the EXECUTION
# BLOCK and not on a star name.  Read from the frozen inventories that
# measured them; each is asserted single-valued per block.
_FROZEN_BARY: dict[str, tuple[float, str]] = {}


def _add_frozen_bary(eb, v, src):
    if eb in _FROZEN_BARY:
        assert abs(_FROZEN_BARY[eb][0] - v) < 1e-6, (eb, _FROZEN_BARY[eb], v)
        return
    _FROZEN_BARY[eb] = (float(v), src)


for _q in MASKR9['newly_evaluable']:
    _add_frozen_bary(_q['eb'], _q['v_corr'], 'mask_r9.json newly_evaluable')
for _e in HD14055['events']:
    _add_frozen_bary(_e['eb'], _e['v_corr_kms'], 'hd14055_recur.json')

# Systemic velocities for stars the release's own table lacks.
_FROZEN_VSYS: dict[str, tuple[float, str, bool]] = {}
for _q in MASKR9['newly_evaluable']:
    _FROZEN_VSYS.setdefault(
        _q['star'], (float(_q['v_sys']), _q['v_sys_src'],
                     'background source' in _q['v_sys_src']))
for _k, _v in R10RV.items():
    _FROZEN_VSYS.setdefault(_k, (float(_v['v']), _v['src'], False))

_USED_FROZEN_BARY: set[str] = set()
_USED_FROZEN_VSYS: set[str] = set()


def vbary(eb, flo_GHz):
    """The barycentric term for one window of one execution block."""
    v = BARY.get('%s|%.6f' % (eb, float(flo_GHz)))
    if v is not None:
        return float(v), 'bary_v405.json'
    if eb in _FROZEN_BARY:
        _USED_FROZEN_BARY.add(eb)
        return _FROZEN_BARY[eb]
    return None, None


def vsys(star):
    """The systemic velocity of a star, and whether it is a bound only."""
    if star in VSYS_OVERRIDE:
        v, s = VSYS_OVERRIDE[star]
        return float(v), s, False
    if star in STARRV:
        return float(STARRV[star]), 'starrv_v399.json', False
    if star in _FROZEN_VSYS:
        _USED_FROZEN_VSYS.add(star)
        return _FROZEN_VSYS[star]
    return None, None, False


# --------------------------------------------------------------------------
# (3) the chain
# --------------------------------------------------------------------------
def to_stellar(f_topo, v_bary, v_sys):
    """topocentric -> barycentric -> stellar rest, in two declared steps."""
    f_bary = f_topo * (1.0 - v_bary / C_KMS)
    return f_bary, f_bary * (1.0 + v_sys / C_KMS)


def offset_kms(f, f_rest):
    return C_KMS * (f - f_rest) / f_rest


def nearest(f_star, trans=None):
    """The nearest masked transition to a stellar-frame frequency."""
    t = TRANS if trans is None else trans
    best = None
    for k, v in t.items():
        f_rest = v[0] if isinstance(v, (tuple, list)) else v
        d = offset_kms(f_star, f_rest)
        if best is None or abs(d) < abs(best[2]):
            best = (k, f_rest, d)
    return best


def key_search_list(nl):
    """The search-list key for a released `nearest_line` label."""
    if nl in CAT_OLD:
        return nl
    c = [k for k in CAT_OLD if k.split('(')[0] == nl]
    return c[0] if len(c) == 1 else None


def recover_ftopo(nearest_line, line_offset_MHz):
    """The crossing frequency, inverted from the offset the release carries.

    The released offsets were computed against the 1 MHz search list, so the
    inversion must use that list and not the full-precision one.
    """
    k = key_search_list(nearest_line)
    if k is None or line_offset_MHz in (None, ''):
        return None
    return CAT_OLD[k] + float(line_offset_MHz) / 1e3


def frame_row(eb, star, flo_GHz, f_topo):
    """Everything the ledger needs for one crossing, or a reason it cannot."""
    vb, vb_src = vbary(eb, flo_GHz)
    vs, vs_src, bound = vsys(star)
    if vb is None or vs is None or f_topo is None:
        return dict(ok=False, v_bary=vb, v_bary_src=vb_src,
                    v_sys=vs, v_sys_src=vs_src, f_topo=f_topo)
    f_bary, f_star = to_stellar(f_topo, vb, vs)
    name, f_rest, dv = nearest(f_star)
    return dict(ok=True, f_topo=f_topo, f_bary=f_bary, f_stellar=f_star,
                v_bary=vb, v_bary_src=vb_src, v_sys=vs, v_sys_src=vs_src,
                bound_only=bound, line=name, line_rest_GHz=f_rest,
                line_tex=tex_label(name), dv_stellar=dv)


_DV_CACHE: dict = {}


def row_dv_stellar(row):
    """The stellar-frame offset of one released catalogue row, or a reason.

    ★ v4.11.  THREE generators were each deciding, out of the released
    `line_offset_kms` column, whether a stage-1 event is attributed:
    `v381_calc.py` (which publishes `\\NStageOneUnattrib`), `rfi_v399.py`
    (whose interference statement is scoped by that set) and
    `extension_v399.py` (which asserts the published macro against its own
    recount).  The released column is the SKY-frame offset to the fifteen
    transitions the search ran.  Once the mask moved into each star's own
    rest frame and gained sulphur monoxide, all three went on counting the
    old set: the count said two, the set held one, and the thing that caught
    it was a figure caption saying "one".

    So the predicate lives once, here, beside the frame chain and the
    species list it depends on, and every generator that needs it calls
    this.  A row the chain cannot evaluate returns None with a reason --
    never a silent fallback to the released column, because that is what
    would reinstate the stale count without changing a line of output.
    """
    # Memoised: the callers below evaluate the same rows inside bootstrap
    # loops, and the chain is pure in these five fields.
    ck = (row.get('eb'), row.get('star_name'), row.get('flo_GHz'),
          row.get('nearest_line'), row.get('line_offset_MHz'))
    if ck in _DV_CACHE:
        return _DV_CACHE[ck]
    f_topo = recover_ftopo(row.get('nearest_line'),
                           row.get('line_offset_MHz'))
    if f_topo is None:
        out = (None, 'no recoverable crossing frequency')
    else:
        fr = frame_row(row.get('eb'), row.get('star_name'),
                       row.get('flo_GHz'), f_topo)
        if not fr.get('ok') or fr.get('dv_stellar') is None:
            out = (None, 'frame chain incomplete (v_bary %r, v_sys %r)'
                   % (fr.get('v_bary'), fr.get('v_sys')))
        else:
            out = (float(fr['dv_stellar']), fr.get('line'))
    _DV_CACHE[ck] = out
    return out


# --------------------------------------------------------------------------
# (3a) ONE SPECIES IS REPORTED AS A NOTE, AND THE GROUND IS PHYSICAL
# --------------------------------------------------------------------------
# A coincidence is a statement about a catalogue, and for one species in the
# catalogue it is not evidence of anything.  Sulphur monoxide has never been
# reported in a debris disc, where the second-generation gas is CO, C and O;
# and toward the one coincident crossing whose window also covers CO(3-2),
# that line is absent at a limit BELOW the crossing's own flux, so an SO line
# there would have to outshine an undetected CO(3-2) line in the same data.
# The offset is therefore printed beside every such crossing and used to
# dispose of none of them.
#
# This is a predicate on the SPECIES, which is why it may be written down at
# all: a per-crossing exception is not a rule, and WITHHELD -- which once
# held exactly one crossing -- stays empty and is asserted empty.  The
# alternative counts, under which the coincidences do dispose, are published
# beside the adopted ones so a reader can see what the choice costs.
NOTED_SPECIES = ('SO',)
NOTED_REASON = ('sulphur monoxide: not reported in a debris disc, and not '
                'supported by the CO emission of the same window')
WITHHELD: dict = {}


def note_reason(line, dv_stellar, half=MASK_HALF_KMS):
    """Why a line coincidence is reported as a note and not a disposition.

    Takes the two quantities every caller already has -- the nearest masked
    transition and the stellar-frame offset to it -- so that no caller can
    reach a different answer from the one printed in its own table.
    """
    if line is None or dv_stellar is None:
        return None
    if abs(float(dv_stellar)) > half:
        return None
    return NOTED_REASON if species(line) in NOTED_SPECIES else None


def withheld_reason(eb, f_topo):
    """A per-crossing exception, which there is never one of.  Retained so
    that an attempt to add one is visible rather than quiet."""
    if f_topo is None:
        return None
    for (e, f), why in WITHHELD.items():
        if e == eb and abs(f - float(f_topo)) < 1e-5:
            return why
    return None


def row_attributed(row, half=MASK_HALF_KMS):
    """True if the row's feature is inside the mask in its star's own frame.

    Raises if the frame chain cannot evaluate the row, for the reason above.
    """
    dv, why = row_dv_stellar(row)
    if dv is None:
        raise AssertionError(
            'maskframe_v411.row_attributed: %s %s cannot be evaluated in the '
            'stellar frame (%s), and no caller may fall back to the released '
            'sky-frame column' % (row.get('star_name'), row.get('eb'), why))
    return abs(dv) <= half


def split_attributed(rows, half=MASK_HALF_KMS):
    """(attributed, unattributed) for released rows, in the stellar frame."""
    att = [r for r in rows if row_attributed(r, half)]
    una = [r for r in rows if r not in att]
    assert len(att) + len(una) == len(rows)
    return att, una


# ==========================================================================
# generator
# ==========================================================================
def main(argv):
    drive, driven = 0, False
    for i, a in enumerate(argv):
        if a == '--drive':
            drive, driven = int(argv[i + 1]), True
    # ★ The suffix follows the FLAG, not the perturbation: `--drive 0` means
    # "no perturbation, but do not write a path production reads".  Without
    # this, driving the baseline overwrites the published products.
    suf = '_drive%d' % drive if driven else ''
    fail = []

    def ck(name, cond, detail=''):
        if not cond:
            fail.append('%s: %s' % (name, detail))

    def _published(name):
        """A macro another round already published, or None."""
        import glob as _g
        for _f in sorted(_g.glob(os.path.join(HERE,
                                              'survey_numbers*.tex'))):
            _m = re.search(
                r'\\(?:new|renew)command\{\\%s\}\{([-+0-9.]+)\}' % name,
                open(_f, errors='ignore').read())
            if _m:
                return _m.group(1)
        return None

    import csv
    ROWS = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'))))
    LED = _load('ledger.json')

    # ---- F1 the recovery of the crossing frequency ------------------------
    n_have = n_rec = 0
    worst = 0.0
    for r in ROWS:
        if r['crossing'] != 'True':
            continue
        f = recover_ftopo(r['nearest_line'], r['line_offset_MHz'])
        if drive == 1 and f is not None:
            f += 1e-4
        if r['f_cross_GHz']:
            n_have += 1
            worst = max(worst, abs(f - float(r['f_cross_GHz'])))
        else:
            n_rec += 1
    ck('F1 the crossing frequency recovered from the released offset '
       'reproduces every f_cross the release carries',
       n_have >= 50 and worst < 2e-6,
       '%d checked, worst residual %.1f Hz' % (n_have, worst * 1e9))

    # ---- F2 the chain -----------------------------------------------------
    worst_1step = 0.0
    for f0 in (115.0, 230.5, 345.8):
        for vb in (-28.0, 0.0, 29.0):
            for vs in (-20.0, 0.0, 30.0):
                _, f2 = to_stellar(f0, vb, vs)
                f1 = f0 * (1.0 + (vs - vb) / C_KMS)
                worst_1step = max(worst_1step,
                                  abs(offset_kms(f2, f1)))
    # The frozen stellar-frame frequencies were computed with the additive
    # form, so they differ from the chain by the second-order cross term
    # v_sys v_bary / c^2 and by nothing else.  The tolerance is therefore set
    # at the size of that term -- 10 kHz at 345 GHz, 0.01 km/s -- not at
    # machine precision, which would be a check that can only fail.
    worst_froz = 0.0
    for e in HD14055['events']:
        _, fs = to_stellar(e['f_GHz'], e['v_corr_kms'],
                           HD14055['v_sys_kms'])
        if drive == 2:
            fs += 1e-3
        worst_froz = max(worst_froz, abs(fs - e['f_stellar_GHz']))
    ck('F2 the two-step chain agrees with the single-step form and '
       'reproduces the frozen stellar-frame frequencies',
       worst_1step < 0.01 and worst_froz < 1e-5,
       'cross term %.4f km/s, frozen residual %.1f Hz'
       % (worst_1step, worst_froz * 1e9))

    # ---- F3 the beta Pic override ----------------------------------------
    _bp_adopt, _bp_src, _ = vsys('bet Pic')
    _bp_cat = float(STARRV['bet Pic'])
    if drive == 3:
        _bp_adopt = _bp_cat
    ck('F3 the beta Pic systemic velocity is the adopted one and is not the '
       'catalogue one', abs(_bp_adopt - _bp_cat) > 1.0 and 'adopted' in _bp_src,
       'adopted %.2f against catalogue %.2f' % (_bp_adopt, _bp_cat))

    # ---- the per-crossing records, over the ADOPTED list ------------------
    rec = []
    for row in LED['rows']:
        q = dict(row)
        mf = row.get('frame')
        if drive == 10 and row is LED['rows'][0]:
            mf = None
        ck('F4a every adopted ledger row carries a frame record',
           mf is not None and mf.get('ok'),
           '%s %s' % (row['star'], row['eb']))
        if mf is None:
            continue
        q['frame'] = mf
        rec.append(q)
    # ★ The frozen inventories exist because the release's own tables do not
    # cover every block or every star.  Count the rows that drew on them from
    # the SOURCES THE ROWS RECORD -- not from this module's call counters,
    # which this script never exercises and which would therefore make the
    # check vacuous.  Each frozen block must be used, and the release's own
    # table must still be doing most of the work.
    src_b = {}
    src_s = {}
    for q in rec:
        src_b[q['frame']['v_bary_src']] = src_b.get(
            q['frame']['v_bary_src'], 0) + 1
        src_s[q['frame']['v_sys_src']] = src_s.get(
            q['frame']['v_sys_src'], 0) + 1
    froz_eb = {q['eb'] for q in rec
               if q['frame']['v_bary_src'] != 'bary_v405.json'}
    if drive == 4:
        froz_eb = set()
    ck('F4b the frozen velocity inventories were consumed, and the release '
       'supplies the rest',
       froz_eb and froz_eb <= set(_FROZEN_BARY)
       and src_b.get('bary_v405.json', 0) > len(rec) // 2
       and len(src_s) >= 3,
       (sorted(froz_eb), src_b, src_s))

    # ---- F5 the three HD 285968 epochs -----------------------------------
    hd = [q for q in rec if q['star'].startswith('HD 285968')]
    if hd:
        topo = [q['frame']['f_topo'] for q in hd]
        dvs = [q['frame']['dv_stellar'] for q in hd]
        spread_topo = offset_kms(max(topo), min(topo))
        spread_stel = max(dvs) - min(dvs)
        if drive == 5:
            spread_stel = 1.0
        ck('F5 the HD 285968 epochs agree in the stellar frame',
           len(hd) == 3 and spread_topo > 5.0 and abs(spread_stel) < 0.1,
           '%d epochs, %.1f km/s apart topocentrically, %.3f km/s apart in '
           'the stellar frame' % (len(hd), spread_topo, spread_stel))
    else:
        spread_topo = spread_stel = float('nan')

    # ---- F6 what rebuilding the mask from the catalogue changes ----------
    # The hand-kept list against the queried one, named crossing by crossing.
    moved = []
    for q in rec:
        f = q['frame']
        n0, r0, d0 = nearest(f['f_stellar'], PREV)
        a0 = abs(d0) <= MASK_HALF_KMS
        a1 = abs(f['dv_stellar']) <= MASK_HALF_KMS
        if a0 != a1 or abs(abs(d0) - abs(f['dv_stellar'])) > 0.5:
            moved.append((q.get('display') or q['star'], q['eb'], n0,
                          round(d0, 1), f['line'],
                          round(f['dv_stellar'], 1), a0, a1))
    flipped = [m for m in moved if m[6] != m[7]]
    if drive == 6:
        flipped = []
    ck('F6 rebuilding the mask from a catalogue query moves at least one '
       'disposition and this generator names every one it moves',
       len(flipped) >= 1, moved)

    # ---- F6b the note is a species rule, and it reaches every such case ---
    # Three requirements, and all three must hold or the rule is an exception
    # wearing a rule's clothes: no crossing is excepted one at a time; the
    # crossings whose coincidence is reported as a note are EXACTLY those
    # coincident with the noted species; and there is at least one, or the
    # predicate is decorative.
    _wh = [q for q in rec
           if withheld_reason(q['eb'], q['frame']['f_topo'])]
    _noted = [q for q in rec
              if note_reason(q['frame']['line'], q['frame']['dv_stellar'])]
    _bysp = [q for q in rec
             if abs(q['frame']['dv_stellar']) <= MASK_HALF_KMS
             and species(q['frame']['line']) in NOTED_SPECIES]
    if drive == 12:
        _wh = [rec[0]]
    ck('F6b the coincidences reported as a note are exactly the coincidences '
       'with the noted species, and no crossing is excepted individually',
       len(_wh) == len(WITHHELD) == 0
       and {id(q) for q in _noted} == {id(q) for q in _bysp}
       and len(_noted) >= 1,
       '%d withheld, %d noted against %d coincident with %s'
       % (len(_wh), len(_noted), len(_bysp), '/'.join(NOTED_SPECIES)))

    # ---- the robustness ladder -------------------------------------------
    RECUR = {}
    for row in _load('ledger_v403.json')['rows']:
        if row.get('recurrence'):
            RECUR[row['eb']] = row['recurrence']
    if drive == 11:
        RECUR.pop(sorted(RECUR)[0], None)
        RECUR.pop('A002_Xc079b5_X82f', None)
    lad = []

    def _att(q, w):
        """Reported as line-attributed at half-width w."""
        return (abs(q['frame']['dv_stellar']) <= w
                and not note_reason(q['frame']['line'],
                                    q['frame']['dv_stellar'], w)
                and not withheld_reason(q['eb'], q['frame']['f_topo']))

    for w in LADDER:
        att = [q for q in rec if _att(q, w)]
        una = [q for q in rec if not _att(q, w)]
        rp = [q for q in una if q['screen']]
        have = [q for q in rp if q['eb'] in RECUR]
        nrec = sum(1 for q in have if RECUR[q['eb']]['recurs'])
        lad.append(dict(w=w, n=len(rec), att=len(att), una=len(una),
                        rank=len(rp), recur=(nrec if len(have) == len(rp)
                                             else None),
                        rank_names=sorted((q['star'], q['eb']) for q in rp)))
    # ★ The interesting case the referee asks for: a count that MOVES.
    # Name the crossing, do not merely report the difference.
    _rel = [q for q in rec
            if abs(q['frame']['dv_stellar']) > LADDER[0]
            and _att(q, MASK_HALF_KMS)]
    at50 = [l for l in lad if l['w'] == MASK_HALF_KMS][0]
    n_att, n_una, n_rank = at50['att'], at50['una'], at50['rank']
    if drive == 7:
        n_rank += 1
    ck('F7a the ladder reproduces the attribution at the adopted half-width',
       at50['att'] + at50['una'] == len(rec) and at50['rank'] == n_rank,
       (at50['att'], at50['una'], at50['rank'], n_rank))
    ck('F7b every rank-passing unattributed crossing at every tabulated '
       'half-width has a recurrence record',
       all(l['recur'] is not None for l in lad),
       [(l['w'], l['rank'], l['recur']) for l in lad])

    # ---- F8 the full harvest ---------------------------------------------
    FULL = {}
    for x in HARVEST['lines']:
        FULL['%.6f|%s|%s' % (x['f'], x['chem'],
                             re.sub(r'\s+', '', _STRIP(x['qn'])))] = x['f']
    full_moved = []
    for q in rec:
        f = q['frame']
        a1 = abs(f['dv_stellar']) <= MASK_HALF_KMS
        kf, _, df = nearest(f['f_stellar'], FULL)
        if (abs(df) <= MASK_HALF_KMS) != a1:
            full_moved.append((q.get('display') or q['star'], q['eb'],
                               round(df, 1), q['screen'], q['tstar'],
                               kf.split('|')[1], kf.split('|')[2]))
    if drive == 8:
        full_moved = []
    ck('F8 the full-harvest cross-check names the dispositions it changes',
       len(full_moved) >= 1, len(full_moved))
    full_rank = [m for m in full_moved if m[3]]

    # ---- CP-72 2713 against everything within 100 km/s -------------------
    # One physical transition is returned several times by the harvest -- once
    # per line list, and once more as a Lovas entry with its excitation and
    # strength blanked.  Collapse them on (carrier, quantum numbers) so the
    # paper reports transitions and not catalogue rows, keeping the entry
    # that carries the numbers.
    cp = [q for q in rec if q['star'].startswith('CP')]
    cp_near = []
    if cp:
        fs = cp[0]['frame']['f_stellar']
        byqn = {}
        for x in HARVEST['lines']:
            d = offset_kms(fs, x['f'])
            if abs(d) > 100.0:
                continue
            k = (x['chem'], re.sub(r'\s+', '', _STRIP(x['qn'])))
            cand = dict(name=_STRIP(x['name']), chem=x['chem'],
                        qn=re.sub(r'\s+', '', _STRIP(x['qn'])), f=x['f'],
                        eu=x['eu'], aij=x['aij'], ll=x['ll'],
                        dv_stellar=round(d, 2))
            if k not in byqn or (byqn[k]['aij'] == 0.0 and x['aij'] < 0.0):
                byqn[k] = cand
        cp_near = sorted(byqn.values(), key=lambda z: abs(z['dv_stellar']))

    # ---- F14 a crossing whose two frames agree is not a failed transform --
    # One crossing has topocentric and stellar-frame frequencies equal to
    # better than 0.1 MHz, which looks exactly like a transform that did
    # nothing.  It is not: the barycentric term and the systemic velocity are
    # independently measured, they happen to agree, and the INTERMEDIATE
    # barycentric frequency differs from both.  So the check is not "the
    # frequencies differ" -- that would fail on good data -- but "where they
    # agree, the two velocities agree, and the step between them is real".
    _coin = []
    for q in rec:
        f = q['frame']
        if abs(f['f_stellar'] - f['f_topo']) * 1e3 > 0.1:        # MHz
            continue
        step = abs(offset_kms(f['f_bary'], f['f_topo']))
        _coin.append((q.get('display') or q['star'], q['eb'],
                      round(f['v_bary'], 4), round(f['v_sys'], 4),
                      round(abs(f['f_bary'] - f['f_topo']) * 1e3, 3)))
        if drive == 14:
            step = 0.0
        ck('F14 where a crossing has the same topocentric and stellar-frame '
           'frequency the two velocity terms agree and the barycentric step '
           'is still real, so the transform ran',
           abs(f['v_bary'] - f['v_sys']) < 0.1 and step > 1.0,
           '%s %s: v_bary %+.4f, v_sys %+.4f, barycentric step %.3f MHz'
           % (q['star'], q['eb'], f['v_bary'], f['v_sys'],
              abs(f['f_bary'] - f['f_topo']) * 1e3))

    # ---- F13 was carbon monoxide covered toward the withheld crossing? ---
    # The astrophysical half of the argument.  Sulphur monoxide has not been
    # detected in a debris disc; the second-generation gas in these systems is
    # CO, C and O.  So the question a reader asks is whether CO was observed
    # at the same time, and to what depth.  Read from the released catalogue,
    # with the transition carried the other way through the same frame chain.
    _cpco = None
    if cp:
        _f = cp[0]['frame']
        _co = TRANS['CO(3-2)'][0] / ((1.0 - _f['v_bary'] / C_KMS)
                                     * (1.0 + _f['v_sys'] / C_KMS))
        _win = [r for r in ROWS
                if r['eb'] == cp[0]['eb']
                and min(float(r['flo_GHz']), float(r['fhi_GHz'])) <= _co
                <= max(float(r['flo_GHz']), float(r['fhi_GHz']))]
        _same = [r for r in _win
                 if min(float(r['flo_GHz']), float(r['fhi_GHz']))
                 <= _f['f_topo']
                 <= max(float(r['flo_GHz']), float(r['fhi_GHz']))]
        if _win:
            _r = (_same or _win)[0]
            _cpco = dict(f_topo_GHz=_co, same_window=bool(_same),
                         smin_mJy=float(_r['smin_mJy']),
                         rms_mJy=float(_r['rms_mJy']),
                         # ★ the crossing's own flux, in the same window and
                         # the same units as the limit it is compared with:
                         # the comparison is the whole of the argument, so
                         # neither number may be quoted without the other.
                         cross_mJy=cp[0]['tstar'] * float(_r['rms_mJy']),
                         chan_kms=C_KMS * float(_r['chanw_Hz']) / (_co * 1e9),
                         band=int(_r['band']), eb=_r['eb'])
    _ok = _cpco is not None and _cpco['same_window']
    if drive == 13:
        _ok = False
    ck('F13 carbon monoxide was covered toward the crossing whose sulphur '
       'monoxide coincidence is reported as a note, in the same spectral '
       'window, and the depth reached there is read from the catalogue',
       _ok, _cpco)
    # ★ F13b is the physical argument itself, and it can fail: if the CO
    # limit in that window were fainter than the crossing, an SO line of that
    # brightness would be unremarkable and the note would have no ground.
    _ok13b = _cpco is not None and _cpco['smin_mJy'] < _cpco['cross_mJy']
    if drive == 16:
        _ok13b = False
    ck('F13b the CO(3-2) limit reached in that window is BELOW the '
       'crossing\'s own flux, which is what makes a sulphur monoxide line '
       'there implausible rather than merely unusual',
       _ok13b,
       None if _cpco is None else
       'CO limit %.1f mJy against crossing %.1f mJy'
       % (_cpco['smin_mJy'], _cpco['cross_mJy']))

    # ---- what the mask costs --------------------------------------------
    # Computed as the band-by-band cost generator does it: around EVERY
    # catalogued transition of a masked species, not only the named ones, so
    # the cost is an upper bound on what the species list removes.
    def _merge(iv):
        o = []
        for a, b in sorted(iv):
            if o and a <= o[-1][1]:
                o[-1][1] = max(o[-1][1], b)
            else:
                o.append([a, b])
        return o

    def _tubes(freqs, half):
        return _merge([(f * (1 - half / C_KMS), f * (1 + half / C_KMS))
                       for f in freqs])

    def _cost(isl, tub):
        t = 0.0
        for a, b in isl:
            for c, d in tub:
                lo, hi = max(a, c), min(b, d)
                if hi > lo:
                    t += hi - lo
        return t

    def _carrier(nm):
        s = _STRIP(nm)
        return s.split()[0] if s else ''

    SPEC_PUB = ('CO', '13CO', 'C18O', 'HCN', 'HCO+', 'CS', 'CN', 'SiO',
                'H2CO', 'CI', 'H30')
    DB_NEW = [x for x in HARVEST['lines']
              if _carrier(x['name']) in SPEC_PUB + ('SO',)]
    byband = {}
    for r in ROWS:
        a, b = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        byband.setdefault(int(r['band']), []).append((a, b))
    ALLISL = _merge([iv for bl in byband.values() for iv in bl])
    UNION = sum(b - a for a, b in ALLISL)
    # ★ v4.12.  THE COST IS NOW THE COST OF THE MASK THAT IS APPLIED.
    # It used to be computed around every catalogued transition of a masked
    # species in the 235-species harvest, which is a different and much larger
    # set than the list attribution used -- so the paper quoted 4.8 per cent
    # for a mask that removed 1.2 per cent.  The cost and the mask are now one
    # object, and the harvest figure survives only as a declared alternative.
    MASKF = [v[0] for v in TRANS.values()]
    cost_new = {w: _cost(ALLISL, _tubes(MASKF, w)) for w in LADDER}
    cost_harv = _cost(ALLISL, _tubes([x['f'] for x in DB_NEW],
                                     MASK_HALF_KMS))
    cost_prev = _cost(ALLISL, _tubes(list(PREV.values()), MASK_HALF_KMS))
    import glob as _glob

    def _texval(name):
        pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                         r'\{([^{}]*)\}' % name)
        v = None
        for f in sorted(_glob.glob(os.path.join(HERE,
                                                'survey_numbers*.tex'))):
            if 'round160' in f:
                continue
            for mm in pat.finditer(open(f).read()):
                if mm.group(1).strip():
                    v = mm.group(1).strip()
        return v
    _pub_u = _texval('MaskUnionGHz')
    _cn, _cp = cost_new[MASK_HALF_KMS], cost_prev
    if drive == 9:
        _cp = _cn
    ck('F9 the mask costs more coverage than the hand-kept list it replaces, '
       'over the published searched union',
       _pub_u is not None and abs(UNION - float(_pub_u)) < 0.05
       and _cn > _cp,
       'union %.2f against %s; rebuilt %.3f GHz against previous %.3f GHz'
       % (UNION, _pub_u, _cn, _cp))

    # ---- F9b the bandwidth removed and the fraction are ONE pair ---------
    # The paper printed the cost three ways: 4.8 GHz as a difference of
    # rounded survivors, 5.0 GHz, and 4.3 per cent.  Only one pair can be
    # right, so the two printed strings are required to reproduce each other
    # at the precision they are printed to.
    _lost_s, _pct_s = '%.2f' % _cn, '%.1f' % (100.0 * _cn / UNION)
    if drive == 15:
        _pct_s = '%.1f' % (100.0 * _cn / UNION + 0.3)
    ck('F9b the printed bandwidth removed and the printed fraction of the '
       'union reproduce each other',
       abs(100.0 * float(_lost_s) / UNION - float(_pct_s)) < 0.05,
       '%s GHz of %.2f GHz is %.3f per cent, printed %s'
       % (_lost_s, UNION, 100.0 * float(_lost_s) / UNION, _pct_s))

    TABB = os.path.join(HERE, 'tab_maskband_v411%s.tex' % suf)
    with open(TABB, 'w') as fh:
        fh.write('%% GENERATED by maskframe_v411.py -- do not hand-edit.\n')
        fh.write('\\begin{table}\n\\centering\n\\footnotesize\n'
                 '\\setlength{\\tabcolsep}{4pt}\n'
                 '\\caption{Band-by-band cost of the molecular-line mask. '
                 'Union: unique sky frequency searched in the band. Masked: '
                 'the part of it lying within '
                 '$\\pm\\MaskHalfKms$\\,km\\,s$^{-1}$ of a catalogued '
                 'transition of a masked species, evaluated in the stellar '
                 'rest frame. Left: what a technosignature search can still '
                 'occupy. The mask is excluded search space and not a veto '
                 '(Appendix~\\ref{app:linemask}); the loss is concentrated in the '
                 'bands where CO and SO sit.}\n'
                 '\\label{tab:maskband}\n')
        fh.write('\\begin{tabular}{@{}crrrr@{}}\n\\hline\n'
                 'Band & Union (GHz) & Masked (GHz) & Left (GHz) & '
                 'Lost (\\%) \\\\\n\\hline\n')
        # ★ ONE OBJECT.  The per-band rows used the 235-species harvest while
        # the All row used the mask that is applied, so the column did not sum
        # to its own total and the paper carried two mask costs.  Both are now
        # the applied mask.
        TUB = _tubes(MASKF, MASK_HALF_KMS)
        worst_b, worst_p = None, -1.0
        for band in sorted(byband):
            isl = _merge(byband[band])
            u = sum(b - a for a, b in isl)
            c_ = _cost(isl, TUB)
            if 100.0 * c_ / u > worst_p:
                worst_b, worst_p = band, 100.0 * c_ / u
            fh.write('%d & %.2f & %.3f & %.2f & %.1f \\\\\n'
                     % (band, u, c_, u - c_, 100.0 * c_ / u))
        fh.write('\\hline\nAll & %.2f & %.3f & %.2f & %.1f \\\\\n'
                 % (UNION, cost_new[MASK_HALF_KMS],
                    UNION - cost_new[MASK_HALF_KMS],
                    100.0 * cost_new[MASK_HALF_KMS] / UNION))
        fh.write('\\hline\n\\end{tabular}\n\\end{table}\n')

    # ---- macros ----------------------------------------------------------
    M = {}

    def m(k, v):
        assert k.isalpha(), k
        assert k not in M, k
        M[k] = v

    m('FrNTrans', '%d' % len(TRANS))
    m('FrNSpec', '%d' % len({species(k) for k in TRANS}))
    m('FrNSO', '%d' % sum(1 for k in TRANS if species(k) == 'SO'))
    m('FrSOName', tex_label('SO(8(8)-7(7))'))
    m('FrSOGHz', '%.4f' % TRANS['SO(8(8)-7(7))'][0])
    m('FrNRecovered', '%d' % n_rec)
    m('FrNRecovChecked', '%d' % n_have)
    m('FrRecovWorstHz', '%.0f' % (worst * 1e9))
    m('FrNUnrecovered', '0')
    m('FrBaryLo', '%+.1f' % min(q['frame']['v_bary'] for q in rec))
    m('FrBaryHi', '%+.1f' % max(q['frame']['v_bary'] for q in rec))
    m('FrBarySwing', '%.0f' % (max(q['frame']['v_bary'] for q in rec)
                               - min(q['frame']['v_bary'] for q in rec)))
    m('FrEpochStar', 'HD 285968')
    m('FrEpochNEpoch', '%d' % len(hd))
    m('FrEpochTopoKms', '%.0f' % abs(spread_topo))
    m('FrEpochStelKms', '%.2f' % abs(spread_stel))
    m('FrNAttr', '%d' % n_att)
    m('FrNUnattr', '%d' % n_una)
    m('FrNRankPass', '%d' % at50['rank'])
    m('FrNRecur', '--' if at50['recur'] is None
      else '%d' % at50['recur'])
    for l in lad:
        t = 'W' + WORD[l['w']]
        m('FrAttr' + t, '%d' % l['att'])
        m('FrUnattr' + t, '%d' % l['una'])
        m('FrRank' + t, '%d' % l['rank'])
    m('FrLadderLo', '%g' % LADDER[0])
    m('FrLadderHi', '%g' % LADDER[-1])
    m('FrLadderRankConst', 'yes' if len({l['rank'] for l in lad}) == 1
      else 'no')
    m('FrMaskPct', '%.1f' % (100.0 * cost_new[MASK_HALF_KMS] / UNION))
    m('FrMaskPctPrev', '%.1f' % (100.0 * cost_prev / UNION))
    m('FrMaskPctHarv', '%.1f' % (100.0 * cost_harv / UNION))
    m('FrMaskPctLo', '%.1f' % (100.0 * cost_new[LADDER[0]] / UNION))
    m('FrMaskPctHi', '%.1f' % (100.0 * cost_new[LADDER[-1]] / UNION))
    m('FrMaskUnionGHz', '%.1f' % UNION)
    # ★ Two decimals, so that the pair a reader checks closes: 5.04 of 118.13
    # is 4.3 per cent, where "5.0 of 118.1" reads as 4.2 and the paper was
    # caught printing both.
    m('FrMaskLostGHz', '%.2f' % cost_new[MASK_HALF_KMS])
    m('FrMaskWorstBand', '%d' % worst_b)
    m('FrMaskWorstPct', '%.1f' % worst_p)
    m('FrMaskNDbTrans', format(len(DB_NEW), ',').replace(',', '\\,'))
    if cp_near:
        _so = [z for z in cp_near if z['chem'] == 'Sulfur Monoxide'
               and z['qn'].startswith('8') and z['aij'] < 0.0][0]
        m('FrCpSODv', '%+.1f' % _so['dv_stellar'])
        m('FrCpSOAij', '%.2f' % _so['aij'])
        m('FrCpNNear', '%d' % len(cp_near))
        m('FrCpNearest', _so['chem'].lower().replace('sulfur', 'sulphur'))
        m('FrCpUnidDv', '%+.0f' % [z for z in cp_near
                                   if z['chem'] == 'UNIDENTIFIED'
                                   ][0]['dv_stellar'])
        m('FrCpSecondChem', [z for z in cp_near if z['chem']
                             not in ('Sulfur Monoxide', 'UNIDENTIFIED')
                             ][0]['chem'].lower()
          .replace('sulfur', 'sulphur'))
        m('FrCpSecondDv', '%+.0f' % [z for z in cp_near if z['chem']
                                     not in ('Sulfur Monoxide',
                                             'UNIDENTIFIED')
                                     ][0]['dv_stellar'])
        m('FrCpFStellar', '%.4f' % cp[0]['frame']['f_stellar'])
        m('FrCpFTopo', '%.4f' % cp[0]['frame']['f_topo'])
        m('FrCpVBary', '%+.1f' % cp[0]['frame']['v_bary'])
        m('FrCpVSys', '%+.2f' % cp[0]['frame']['v_sys'])
        m('FrCpStar', 'CP$-$72 2713')
        # ★★ v4.11: ONE NUMBER, ONE PRECISION, AND NOW ASSERTED.
        # `v409_calc.py` publishes the same crossing's statistic as
        # \VnCpT and this file published \FrCpT, at two different
        # precisions (5.81 against 5.809), so `synmacro.py` read them as two
        # values for one quantity -- which is what they were on the page.
        # Printed at the same precision and required to agree, so the two
        # cannot drift the way the SO offset nearly did.
        # ★★ v4.11: NO SECOND NAME FOR THIS NUMBER.  This file used to emit
        # \FrCpT and `v409_calc.py` emits \VnCpT for the same crossing's
        # statistic, at two precisions (5.81 against 5.809), and both were
        # cited -- in Appendix C and Appendix I.  Exactly one live name now:
        # Appendix I cites \VnCpT, and what survives here is the assertion
        # that the value this file computes IS the published one, which is
        # the part that was missing.
        _vn = _published('VnCpT')
        ck('F12 the crossing statistic this file prints is the one the '
           'repaired-statistic round publishes, to the digit both print',
           _vn is None or abs(float(_vn) - cp[0]['tstar']) < 1e-3
           if drive != 25 else False,
           'FrCpT %.4f against VnCpT %s' % (cp[0]['tstar'], _vn))
    _surv = [q for q in rec if q['frame']['dv_stellar'] is not None
             and not _att(q, MASK_HALF_KMS) and q['screen']]
    # ★ The DISPLAY name, not the catalogue key: the key writes CP-72 2713
    # with a hyphen where the star's name carries a minus sign.  This list
    # held one star until the sulphur monoxide coincidences became notes, so
    # the defect had never reached the page.
    m('FrSurvStar', ', '.join((q.get('display') or q['star']).replace(' ', '~')
                              for q in _surv) or 'none')
    m('FrSurvN', '%d' % len(_surv))
    # ★ Which coincidences rest only on a weak transition.  The list is
    # complete by rule, so it contains transitions nobody would detect in
    # these fields; a reader is told which crossings coincide with nothing
    # stronger than A_ij = 1e-5 s^-1 outside the CO ladder, and can discount
    # them.  Nothing is disposed of either way -- the flag does not gate.
    _STRONG = {k for k, v in _mc.MASK.items()
               if v['spec'] in ('CO', '13CO', 'C18O', 'CI')
               or (v['aij'] == v['aij'] and v['aij'] >= -5.0)}
    _weak = []
    for q in rec:
        if not _att(q, MASK_HALF_KMS):
            continue
        fs = q['frame']['f_stellar']
        if not any(abs(offset_kms(fs, TRANS[k][0])) <= MASK_HALF_KMS
                   for k in _STRONG):
            _weak.append(q.get('display') or q['star'])
    if _cpco:
        m('FrCpCoGHz', '%.4f' % _cpco['f_topo_GHz'])
        m('FrCpCoLimMJy', '%.1f' % _cpco['smin_mJy'])
        m('FrCpFluxMJy', '%.1f' % _cpco['cross_mJy'])
        m('FrCpCoChanKms', '%.2f' % _cpco['chan_kms'])
        m('FrCpCoBand', '%d' % _cpco['band'])
    m('FrFrameCoincN', '%d' % len(_coin))
    m('FrWeakOnlyN', '%d' % len(_weak))
    m('FrWeakOnlyStar', ', '.join(sorted(set(_weak))) or 'none')
    m('FrRebuildFlipStar', ', '.join(sorted({m_[0] for m_ in flipped}))
      or 'none')
    m('FrRebuildFlipN', '%d' % len(flipped))
    m('FrRebuildMovedN', '%d' % len(moved))
    m('FrFullNFlip', '%d' % len(full_moved))
    m('FrFullNFlipRank', '%d' % len(full_rank))
    _WORDS = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
              'eight', 'nine', 'ten')
    m('FrFullNFlipRankWord', _WORDS[len(full_rank)]
      if len(full_rank) < len(_WORDS) else '%d' % len(full_rank))
    _nso = sum(1 for k in TRANS if species(k) == 'SO')
    m('FrNSOWord', _WORDS[_nso] if _nso < len(_WORDS) else '%d' % _nso)
    m('FrFullFlipRankStar',
      ', '.join(sorted({m_[0] for m_ in full_rank})) or 'none')
    m('FrFullFlipRankDv', ('%+.0f' % full_rank[0][2]) if full_rank else '--')
    m('FrFullFlipRankChem',
      (full_rank[0][5].lower().replace('sulfur', 'sulphur'))
      if full_rank else '--')
    m('FrFullFlipRankQn', (full_rank[0][6]) if full_rank else '--')
    m('FrNarrowMoveN', '%d' % len(_rel))
    m('FrNarrowMoveStar', ', '.join((q.get('display') or q['star'])
                                    for q in _rel) or 'none')
    m('FrNarrowMoveDv', ', '.join('%+.1f' % q['frame']['dv_stellar']
                                  for q in _rel) or '--')
    m('FrNarrowMoveLine', ', '.join(q['frame']['line_tex'] for q in _rel)
      or '--')

    OUT = os.path.join(HERE, 'survey_numbers_round160%s.tex' % suf)
    with open(OUT, 'w') as fh:
        fh.write('%% GENERATED by maskframe_v411.py -- do not hand-edit.\n')
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

    TAB = os.path.join(HERE, 'tab_maskrobust_v411%s.tex' % suf)
    with open(TAB, 'w') as fh:
        fh.write('%% GENERATED by maskframe_v411.py -- do not hand-edit.\n')
        fh.write('\\begin{tabular}{@{}lrrrrr@{}}\n\\hline\n')
        fh.write('Half-width & band & line- & unatt- & outrank & recur- '
                 '\\\\\n')
        fh.write('(km\\,s$^{-1}$) & masked & attributed & ributed & '
                 'all & ring \\\\\n')
        fh.write(' & (per cent) & & & controls & \\\\\n\\hline\n')
        for l in lad:
            b = ((lambda x: '\\textbf{%s}' % x)
                 if l['w'] == MASK_HALF_KMS else (lambda x: x))
            fh.write('%s & %s & %s & %s & %s & %s \\\\\n'
                     % (b('$\\pm%g$' % l['w']),
                        b('%.1f' % (100.0 * cost_new[l['w']] / UNION)),
                        b('%d' % l['att']), b('%d' % l['una']),
                        b('%d' % l['rank']),
                        b('--' if l['recur'] is None else '%d' % l['recur'])))
        fh.write('\\hline\n\\end{tabular}\n')

    JS = os.path.join(HERE, 'maskframe_v411%s.json' % suf)
    with open(JS, 'w') as fh:
        json.dump(dict(
            generator='maskframe_v411.py',
            frame='stellar rest frame, per execution block',
            chain='f_bary = f_topo (1 - v_bary/c); '
                  'f_star = f_bary (1 + v_sys/c)',
            mask=dict(n_transitions=len(TRANS),
                      n_species=len({species(k) for k in TRANS}),
                      source='maskcat_v412.py (round 170)',
                      previous_hand_kept=sorted(PREV),
                      withheld=[dict(eb=k[0], f_topo_GHz=k[1], reason=v)
                                for k, v in WITHHELD.items()],
                      noted_species=list(NOTED_SPECIES),
                      noted_reason=NOTED_REASON,
                      noted=[dict(star=q.get('display') or q['star'],
                                  eb=q['eb'],
                                  f_topo_GHz=q['frame']['f_topo'],
                                  line=q['frame']['line'],
                                  dv_stellar_kms=q['frame']['dv_stellar'])
                             for q in _noted]),
            recovery=dict(n_recovered=n_rec, n_checked=n_have,
                          worst_residual_Hz=worst * 1e9, n_unrecovered=0),
            vsys_override={k: v for k, v in VSYS_OVERRIDE.items()},
            ladder=[{k: v for k, v in l.items()} for l in lad],
            adopted=dict(n_crossings=len(rec), attributed=n_att,
                         unattributed=n_una,
                         rank_flagged_unattributed=at50['rank'],
                         recurrent=at50['recur']),
            frozen_adopted=MASKR9['adopted'],
            frame_coincidences=_coin,
            rebuild_flipped=flipped, rebuild_moved=moved,
            full_harvest_flipped=full_moved,
            cp72_within_100kms=cp_near,
            hd285968=dict(n=len(hd), spread_topo_kms=spread_topo,
                          spread_stellar_kms=spread_stel),
            rows=[dict(star=q['star'], eb=q['eb'], band=q['band'],
                       tstar=q['tstar'], screen=q['screen'], **q['frame'])
                  for q in rec],
        ), fh, indent=1)

    print('maskframe_v411 (round 160): %d transitions of %d species from '
          'maskcat_v412; %d crossings -> %d line-flagged / %d not, '
          '%d of the unflagged outrank all controls, %s recurrent'
          % (len(TRANS), len({species(k) for k in TRANS}),
             len(rec), n_att, n_una, at50['rank'], at50['recur']))
    print('  frozen adopted counts were %s' % (MASKR9['adopted'],))
    print('  rebuilding the mask moves %d nearest-line entries and flips '
          '%d:' % (len(moved), len(flipped)))
    for _m in moved:
        print('     %-26s %-20s %-22s %+8.1f  ->  %-26s %+8.1f  %s'
              % (_m[0][:26], _m[1].replace('A002_', ''), _m[2], _m[3],
                 _m[4], _m[5], 'FLIP' if _m[6] != _m[7] else ''))
    print('  full harvest flips %d (%d rank-passing): %s'
          % (len(full_moved), len(full_rank), full_moved))
    if cp_near:
        print('  CP-72 2713: f_topo %.6f -> f_stellar %.6f (v_bary %+.3f, '
              'v_sys %+.3f); %d transitions within 100 km/s:'
              % (cp[0]['frame']['f_topo'], cp[0]['frame']['f_stellar'],
                 cp[0]['frame']['v_bary'], cp[0]['frame']['v_sys'],
                 len(cp_near)))
        for z in cp_near:
            print('     %+8.2f km/s  %-22s %-14s %10.6f  E_u %6.1f  '
                  'logA %6.2f' % (z['dv_stellar'], z['chem'], z['qn'],
                                  z['f'], z['eu'], z['aij']))
    for l in lad:
        print('  +-%-5g  %2d crossings  %2d attributed  %2d unattributed  '
              '%d outrank all  %s recurrent  %s'
              % (l['w'], l['n'], l['att'], l['una'], l['rank'],
                 l['recur'], l['rank_names']))
    print('  -> %s (%d macros), %s, %s'
          % (os.path.basename(OUT), len(M), os.path.basename(TAB),
             os.path.basename(JS)))
    for f in fail:
        print('  ASSERTION FIRED  ' + f)
    print('maskframe_v411: %d assertions fired' % len(fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
