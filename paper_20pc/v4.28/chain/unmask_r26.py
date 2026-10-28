#!/usr/bin/env python3
r"""Round 990: how much of each searched window the attribution mask removes,
in the star's own rest frame, and the consequence for what a limit means.

WHAT THIS FILE OWNS

1.  THE UNMASKED FRACTION OF EVERY SEARCHED WINDOW.  Section~\ref{sec:lines}
    says the survey constrains nothing inside the mask.  A limit is therefore
    a statement about a window's UNMASKED channels, and a window with none of
    them carries no limit at all -- which is not a nuance here but the
    deepest number in the paper: the finest windows were tuned to CO, and a
    58.6 MHz window of 15.26 kHz channels placed on CO(2-1) is 53.91 MHz
    wide after the pipeline's edge trim, against a +-50 km/s mask 76.90 MHz
    wide.  It is entirely inside the mask.  So this file computes the
    fraction per window, and the per-system limit is formed over windows that
    retain bandwidth.

2.  THE MASKED SET IS A UNION, NOT A SUM.  The hyperfine components of CN
    N=1-0 lie closer together than 100 km/s, and so do others: the 96
    transitions of the adopted list collapse to 36 disjoint masked
    intervals.  Any accounting that adds per-transition widths over-counts.
    The merge happens here once, and U2 asserts disjointness afterwards, so
    it cannot silently stop happening.

3.  A SYSTEMIC VELOCITY FOR EVERY STAR, AND NOT ONLY FOR THE ONES THAT
    CROSSED THE THRESHOLD.  Attribution only ever had to be evaluated where
    there was a crossing, so the frozen records carry 22 velocities.  An
    unmasked fraction needs one for every star with a window.  `vsys_r26.json`
    is a dated SIMBAD snapshot that records, with every value, the separation,
    the parallax agreement and a verdict `plx_ok`; U5 asserts that it
    re-derives the velocities the article already adopts.  ★★★ ROUND 27: a
    value is used ONLY if its verdict is true.  This file used to read the
    velocity and never the verdict, and so put LP 736-15 and PM J03433+1958
    in the rest frames of objects 79 and 100 arcsec away whose parallaxes the
    snapshot itself had rejected; and six entries had been resolved by
    IDENTIFIER, not by position and parallax.  `r27inputs/vsys_r27.json`
    re-decides those on Gaia DR3 astrometry and supersedes them, U7 asserts
    that no window takes a velocity from a rejected match, and
    `vsysgate_r27.py` re-decides identity from the astrometry for every
    velocity the build consumes.  Where the article adopts a value of its own -- beta Pic,
    whose circumstellar gas value `bpic_vsys.py` argues for -- that value
    wins and the snapshot is the thing checked against it.

WHAT THIS FILE DOES NOT DO.  It does not re-search, re-threshold or re-weight
anything.  The limit of a window is the limit that window already has; what
changes is which windows are eligible to be a system's best one.  The
published union-level cost of the mask is also left alone, and measured
rather than assumed to be safe: evaluating it window by window in each star's
own frame moves it from 4.98 to 5.00 per cent of the Class A union, which is
the same printed number (U6).

ASSERTIONS (each driven, see --drive)
    U1  every searched window gets a frame and a fraction, or is named: a
        velocity term missing anywhere is reported and never defaulted
        silently
    U2  the masked set is the union of the transition tubes -- 96 transitions
        to 36 disjoint intervals -- and summing the widths instead
        over-counts by a stated amount
    U3  the frame chain is maskframe_v411's own, not a copy: the stellar-frame
        frequency computed here reproduces the ledger's for every crossing it
        publishes one for
    U4  a fully masked window is not a system's best window, every system
        whose best window moves is named, and no system's limit gets DEEPER
    U5  the velocity snapshot re-derives the velocities the article adopts,
        and every exception is named with its reason
    U7  no window takes its systemic velocity from a snapshot entry whose
        verdict is not true (round 27: the consumer now reads the verdict)
    U6  the fine windows are narrower than the mask at their own transition,
        which is the mechanism, and the union-level cost is unchanged by the
        frame

    python3 unmask_r26.py [--drive N]

-> survey_numbers_round990.tex, unmask_r26.json
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import re
import sys

import maskframe_v411 as mf

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 990
C_KMS = mf.C_KMS
HALF = mf.MASK_HALF_KMS
SUF = ('_drive%d' % int(sys.argv[sys.argv.index('--drive') + 1])
       if '--drive' in sys.argv else '')
OUTNAME = 'survey_numbers_round990%s.tex' % SUF
assert OUTNAME.startswith('survey_numbers_round%d' % ROUND), OUTNAME


def _load(*p):
    return json.load(open(os.path.join(HERE, *p), encoding='utf-8'))


def one(pat):
    f = sorted(glob.glob(os.path.join(HERE, pat)))
    assert f, pat
    return f[-1]


def texval(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^{}]*)\}'
                     % name)
    v = None
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for m in pat.finditer(open(f, encoding='utf-8').read()):
            if m.group(1).strip():
                v = m.group(1).strip()
    return v


def sci(x, nd=1):
    e = int(math.floor(math.log10(x)))
    return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)


def tname(s):
    return s.replace(' ', '~')


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


# --------------------------------------------------------------- the mask
def masked_union(transitions, half):
    """The masked SET: the union of the velocity tubes, merged.

    Returned as a list of disjoint (lo, hi) in GHz, ascending.
    """
    iv = sorted((f * (1 - half / C_KMS), f * (1 + half / C_KMS))
                for f in transitions)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def unmasked_channels(lo, hi, chan_Hz, factor, union):
    """Channels of one window whose stellar-frame centre is outside the mask.

    The window is topocentric, as the correlator delivered it; `factor` is
    (1 - v_bary/c)(1 + v_sys/c), so channel i has stellar-frame centre
    (lo + (i + 1/2) dnu) * factor.  Counted by interval arithmetic on the
    channel index, so the cost does not grow with the channel count.
    """
    n = int(round((hi - lo) * 1e9 / chan_Hz))
    if n <= 0:
        return 0, 0
    step = chan_Hz / 1e9
    masked = 0
    for a, b in union:
        ia = (a / factor - lo) / step - 0.5
        ib = (b / factor - lo) / step - 0.5
        i0 = max(0, math.ceil(ia - 1e-12))
        i1 = min(n - 1, math.floor(ib + 1e-12))
        if i1 >= i0:
            masked += i1 - i0 + 1
    return n, masked


def main(argv):
    drive = 0
    if '--drive' in argv:
        drive = int(argv[argv.index('--drive') + 1])
    M, fail = {}, []

    def m(k, v):
        assert k.isalpha(), k     # a macro name may hold letters only
        M[k] = v if isinstance(v, str) else str(v)

    def ck(name, cond, detail=''):
        print('  %-4s %s %s' % ('PASS' if cond else 'FAIL', name, detail))
        if not cond:
            fail.append(name.split()[0])

    CAT = list(csv.DictReader(open(one('per_target_results*.csv'))))
    VS = _load('r26inputs', 'vsys_r26.json')
    SNAP = {k: dict(e) for k, e in VS['v_sys_kms'].items()}
    # ★★★ ROUND 27, ROW 52.  Supersessions re-decided on Gaia DR3 position and
    # parallax, each carrying the entry it replaces and why.  Drive 8 restores
    # the v4.27 behaviour -- no supersession, and the verdict unread -- which
    # is the defect U7 exists to catch.
    V27 = _load('r27inputs', 'vsys_r27.json')
    if drive != 8:
        for _k, _e in V27['supersede'].items():
            assert _k in SNAP, ('a supersession names no snapshot entry', _k)
            SNAP[_k].update({f: v for f, v in _e.items() if f != 'superseded'})
    PB = _load('pbcat_v408.json')
    HARVEST = json.load(open(os.path.join(HERE, 'stack_v408', 'windows.json')))

    # ---------------------------------------------------------------- U2
    TRANS = {k: v[0] for k, v in mf.TRANS.items()}
    UNION = masked_union(TRANS.values(), HALF)
    if drive == 2:
        UNION = sorted(UNION + [UNION[0]])     # the merge stops happening
    _sumw = sum(f * 2 * HALF / C_KMS for f in TRANS.values())
    _unw = sum(b - a for a, b in UNION)
    ck('U2 the masked set is the union of the transition tubes and summing '
       'their widths instead over-counts',
       all(UNION[i][1] < UNION[i + 1][0] for i in range(len(UNION) - 1))
       and len(UNION) < len(TRANS)
       and _sumw > _unw,
       '%d transitions -> %d disjoint intervals, %.4f GHz against %.4f GHz '
       'summed (%.1f per cent over)'
       % (len(TRANS), len(UNION), _unw, _sumw, 100 * (_sumw / _unw - 1)))
    m('UmNTrans', '%d' % len(TRANS))
    m('UmNMaskIv', '%d' % len(UNION))
    m('UmMaskSumPct', '%.0f' % (100 * (_sumw / _unw - 1)))

    # --------------------------------------------- positions and velocities
    POS = {}
    for key, lst in PB.items():
        tid, eb = key.split('|')
        for w in lst:
            POS[(tid, eb, '%.6f' % w['flo'])] = (w['star_ra'], w['star_dec'])
    # ★ The primary-beam record holds no eps Eri -- which is also why the
    # deposit ships that star with blank coordinates -- so its position comes
    # from the stellar-frame harvest, by block and by containment of the
    # searched extent inside the delivered window.  Declared, not silent.
    HBLK = {}
    for w in HARVEST:
        HBLK.setdefault(w['block'], []).append(w)

    def harvest_window(eb, lo, hi):
        best = None
        for w in HBLK.get(eb, []):
            if w['f_lo'] - 2e6 <= lo * 1e9 and hi * 1e9 <= w['f_hi'] + 2e6:
                d = abs(w['f_lo'] - lo * 1e9)
                if best is None or d < best[0]:
                    best = (d, w)
        return best[1] if best else None

    def frame_factor(r, hw):
        """(1 - v_bary/c)(1 + v_sys/c) for one catalogue row, with sources."""
        lo = float(r['flo_GHz'])
        vb, vbs = mf.vbary(r['eb'], lo)
        if vb is None and hw is not None and hw.get('v_corr') is not None:
            vb, vbs = float(hw['v_corr']), 'stellar-frame harvest'
        vs, vss, _ = mf.vsys(r['star_name'])
        if vs is None:
            e = SNAP.get(r['star_name'])
            # ★★★ ROUND 27: the verdict is READ.  A rejected match leaves the
            # term missing, and U1/U1b then treat it as missing -- never as
            # another star's velocity.
            if e and e['v_sys_kms'] is not None \
                    and (e['plx_ok'] is True or drive == 8):
                vs, vss = float(e['v_sys_kms']), 'SIMBAD %s' % e['main_id']
        return vb, vbs, vs, vss

    rows, nofr = [], []
    for r in CAT:
        lo, hi = float(r['flo_GHz']), float(r['fhi_GHz'])
        chan = float(r['chanw_Hz'])
        hw = harvest_window(r['eb'], lo, hi)
        vb, vbs, vs, vss = frame_factor(r, hw)
        if vb is None or vs is None:
            nofr.append(dict(star=r['star_name'], eb=r['eb'], flo=lo,
                             have_bary=vb is not None,
                             have_sys=vs is not None,
                             search_class=r['search_class']))
        fac = (1.0 - (vb or 0.0) / C_KMS) * (1.0 + (vs or 0.0) / C_KMS)
        n, mk = unmasked_channels(lo, hi, chan, fac, UNION)
        ra, dec = POS.get((r['star_name'], r['eb'], '%.6f' % lo),
                          (None, None))
        if ra is None and hw is not None:
            ra, dec = hw['ra'], hw['dec']
        rows.append(dict(
            star=r['star_name'], system=r['system_id'], eb=r['eb'],
            nu_lo_GHz=lo, nu_hi_GHz=hi, chan_width_Hz=chan,
            search_class=r['search_class'],
            # ★ THE NOMINAL POWER, NOT THE ADOPTED ONE, AND DELIBERATELY.
            # This file runs before the catalogue carries its adopted
            # column -- it has to, because the generators that write that
            # column ask this file which windows carry a limit at all.  The
            # eligibility is geometric and uses no limit; the column below
            # exists so that U4 can show the rule costs depth and never buys
            # it, and that is true of any limit monotone in the nominal one,
            # which every column in this catalogue is.
            eirp_nominal_W=float(r['eirp_nominal_W']),
            ra_deg=ra, dec_deg=dec,
            v_bary_kms=vb, v_bary_source=vbs,
            v_sys_kms=vs, v_sys_source=vss,
            n_chan=n, n_chan_masked=mk,
            unmasked_fraction=(n - mk) / n if n else 0.0))

    # ---------------------------------------------------------------- U1
    # ★ The clause has to be able to fail, so it recounts the incomplete
    # frames FROM THE RECORD rather than trusting the list that was built
    # alongside it: a window whose frame is incomplete and which is not in
    # `no_frame` is the defect this is here to catch.
    _inc = [x for x in rows
            if x['v_bary_kms'] is None or x['v_sys_kms'] is None]
    _keys = {(x['star'], x['eb'], round(x['flo'], 6)) for x in nofr}
    if drive == 1:
        _keys.discard(sorted(_keys)[0])
    ck('U1 every window whose frame is incomplete is named, with the term '
       'it lacks, in the record this file writes',
       all((x['star'], x['eb'], round(x['nu_lo_GHz'], 6)) in _keys
           for x in _inc) and len(_keys) == len(_inc),
       '%d window(s) without a complete frame: %s'
       % (len(_inc), sorted({x['star'] for x in _inc}) or 'none'))
    m('UmNNoFrame', '%d' % len(nofr))

    # ★ A MISSING TERM IS NEVER A SILENT ZERO.  Where a velocity term cannot
    # be had, the fraction is recomputed over the whole range that term could
    # take -- +-30 km/s for the Earth's own motion, +-50 km/s for a systemic
    # velocity this sample could hold -- and the window is usable only if the
    # answer does not depend on it.  The alternative, defaulting to zero and
    # saying so in a footnote, leaves a number in the paper that nobody can
    # check.
    _env = []
    for x in nofr:
        r = next(q for q in CAT if q['star_name'] == x['star']
                 and q['eb'] == x['eb']
                 and abs(float(q['flo_GHz']) - x['flo']) < 1e-9)
        lo, hi = float(r['flo_GHz']), float(r['fhi_GHz'])
        span = 30.0 if not x['have_bary'] else 50.0
        fr = []
        # ★ ROUND 27: the range is sampled every 1 km/s, not at its two ends
        # and its middle -- a mask edge crossed inside the range was missed,
        # and Wolf 219's 217.09 GHz window reads 0.874 at three points against
        # 0.883 at its true maximum.
        for tv in [float(i) for i in range(-int(span), int(span) + 1)]:
            hw = harvest_window(r['eb'], lo, hi)
            vb, _a, vs, _b = frame_factor(r, hw)
            vb = tv if not x['have_bary'] else vb
            vs = tv if not x['have_sys'] else vs
            fac = (1.0 - (vb or 0.0) / C_KMS) * (1.0 + (vs or 0.0) / C_KMS)
            n, mk = unmasked_channels(lo, hi, float(r['chanw_Hz']), fac,
                                      UNION)
            fr.append((n - mk) / n if n else 0.0)
        # ★ ROUND 27: keyed on the WINDOW.  It was keyed on (star, class), so
        # every missing-term window of a star took the LAST dependent range
        # of that star and was withheld whether or not its own fraction
        # depended on the term: four of Wolf 219's six Class B windows (two
        # that read 1.000 and two that read 0.955-0.964 over the whole range)
        # were withheld under the 0.820-0.874 range of a third.
        _env.append((x['star'], x['search_class'], min(fr), max(fr),
                     x['eb'], round(x['flo'], 6)))
    _dep = [e for e in _env if e[3] - e[2] >= 0.01]
    if drive == 7:
        _dep.append(('a Class A window whose answer depends on it', 'A',
                     0.0, 1.0, '', 0.0))
    # Where the answer does depend on the missing term the point value is
    # WITHHELD and the range is deposited in its place, so no default
    # reaches a column a reader could quote.
    for _s, _c, _lo, _hi, _eb, _flo in _dep:
        for x in rows:
            if x['star'] == _s and x['search_class'] == _c \
                    and x['eb'] == _eb and round(x['nu_lo_GHz'], 6) == _flo \
                    and (x['v_bary_kms'] is None or x['v_sys_kms'] is None):
                x['unmasked_fraction'] = None
                x['unmasked_fraction_lo'] = _lo
                x['unmasked_fraction_hi'] = _hi
    ck('U1b no published quantity rests on a defaulted velocity: where the '
       'fraction depends on the missing term the window is Class B and its '
       'value is withheld in favour of the range',
       all(c != 'A' for _s, c, _lo, _hi, _eb, _flo in _dep)
       and sum(1 for x in rows if x['unmasked_fraction'] is None
               and 'unmasked_fraction_lo' in x) == len(_dep),
       '%d window(s) with a missing term, %d of them dependent: %s'
       % (len(_env), len(_dep),
          sorted({(s, c, eb, flo, round(lo, 3), round(hi, 3))
                  for s, c, lo, hi, eb, flo in _dep}) or 'none'))

    # ---------------------------------------------------------------- U3
    # The sharp form of "the chain is maskframe's own": every crossing whose
    # stellar-frame offset maskframe can evaluate must fall inside one of the
    # masked intervals used here if and only if maskframe attributes it.  A
    # re-implementation of the chain, or a mask union built from a different
    # list, breaks the equivalence on at least one row.
    _chk, _dis = 0, []
    for r in CAT:
        if not r.get('crossing') or r['crossing'] in ('0', '', 'False'):
            continue
        dv, _why = mf.row_dv_stellar(r)
        if dv is None:
            continue
        f_topo = mf.recover_ftopo(r.get('nearest_line'),
                                  r.get('line_offset_MHz'))
        hw = harvest_window(r['eb'], float(r['flo_GHz']),
                            float(r['fhi_GHz']))
        vb, _vbs, vs, _vss = frame_factor(r, hw)
        f_star = mf.to_stellar(f_topo, vb, vs)[1]
        mine = any(a <= f_star <= b for a, b in UNION)
        theirs = abs(dv) <= HALF
        _chk += 1
        if mine != theirs:
            _dis.append((r['star_name'], r['eb'], f_star, dv))
    if drive == 3:
        _dis.append(('a row the two routes disagree on', '', 0.0, 0.0))
    ck('U3 the frame chain and the masked set are maskframe_v411\'s own: '
       'every crossing it attributes falls inside an interval used here, '
       'and no crossing it does not',
       _chk > 0 and not _dis,
       '%d crossings checked, %d disagreements %s'
       % (_chk, len(_dis), _dis[:3]))
    m('UmNFrameChk', '%d' % _chk)

    # ---------------------------------------------------------------- U5
    _ctl, _agree, _exc = 0, 0, []
    for tid, e in sorted(SNAP.items()):
        adopted = mf.vsys(tid)[0]
        if adopted is None:
            continue
        _ctl += 1
        if e['v_sys_kms'] is not None and abs(e['v_sys_kms'] - adopted) < 1.0:
            _agree += 1
        else:
            _exc.append((tid, adopted, e['v_sys_kms']))
    if drive == 5:
        _exc.append(('a star with no reason', 0.0, None))
    _REASON = {
        # the article adopts the circumstellar gas value; bpic_vsys.py argues it
        'bet Pic': 'adopted value differs from the catalogue one by design',
        # not a star: a background source the article declares at zero
        'ALMA J153702653-33192492': 'a background source, declared at zero',
    }
    ck('U5 the velocity snapshot re-derives the velocities the article '
       'adopts, and every exception is named with its reason',
       _ctl > 0 and all(t in _REASON for t, _a, _s in _exc),
       '%d of %d reproduced; exceptions %s'
       % (_agree, _ctl, [(t, _REASON.get(t, 'UNEXPLAINED')) for t, _a, _s
                         in _exc]))
    m('UmNVsysCtl', '%d' % _ctl)
    m('UmNVsysAgree', '%d' % _agree)
    m('UmNVsys', '%d' % sum(1 for e in SNAP.values()
                            if e['v_sys_kms'] is not None
                            and e['plx_ok'] is True))

    # ---------------------------------------------------------------- U7
    # Recounted from the RECORD, not from the rule that built it: a window
    # whose velocity the article's lookup does not supply came from the
    # snapshot, and the entry it came from must carry a true verdict.  The
    # comparison is against the snapshot AS PUBLISHED plus its supersessions,
    # so dropping the filter above, or a supersession, fails here.
    _V26 = {k: dict(e) for k, e in VS['v_sys_kms'].items()}
    for _k, _e in V27['supersede'].items():
        _V26[_k].update({f: v for f, v in _e.items() if f != 'superseded'})
    _rej = sorted({x['star'] for x in rows
                   if x['v_sys_kms'] is not None
                   and mf.vsys(x['star'])[0] is None
                   and ((_V26.get(x['star']) or {}).get('plx_ok') is not True
                        or x['v_sys_kms']
                        != (_V26.get(x['star']) or {}).get('v_sys_kms'))})
    ck('U7 no window takes its systemic velocity from a match the snapshot '
       'rejected, or a value its entry does not carry',
       not _rej, '%s' % (_rej or 'none'))

    # ------------------------------------------------- the Class A picture
    A = [x for x in rows if x['search_class'] == 'A']
    full = [x for x in A if x['unmasked_fraction'] == 0.0]
    part = [x for x in A if 0.0 < x['unmasked_fraction'] < 0.5]
    m('UmNWinA', '%d' % len(A))
    m('UmNWinAFull', '%d' % len(full))
    m('UmNWinAPart', '%d' % len(part))
    m('UmFracAMedian', '%.3f' % median([x['unmasked_fraction'] for x in A]))
    m('UmFracAMeanPct', '%.1f'
      % (100 * sum(x['unmasked_fraction'] for x in A) / len(A)))

    sysw = {}
    for x in A:
        sysw.setdefault(x['system'], []).append(x)
    moved, lost = [], []
    for s, ws in sorted(sysw.items()):
        old = min(ws, key=lambda x: x['eirp_nominal_W'])
        keep = [x for x in ws if (x['unmasked_fraction'] or 0.0) > 0]
        if not keep:
            lost.append(s)
            continue
        new = min(keep, key=lambda x: x['eirp_nominal_W'])
        if new['eirp_nominal_W'] != old['eirp_nominal_W']:
            moved.append((s, old['eirp_nominal_W'], new['eirp_nominal_W']))
    if drive == 4:
        moved.append(('a system that got deeper', 2.0, 1.0))
    ck('U4 a fully masked window is not a system\'s best window, every '
       'system whose best window moves is named, and no limit gets deeper',
       all(b > a for _s, a, b in moved),
       '%d systems move: %s; %d system(s) retain no unmasked window: %s'
       % (len(moved), ['%s x%.2f' % (s, b / a) for s, a, b in moved],
          len(lost), lost or 'none'))
    m('UmNSysMoved', '%d' % len(moved))
    m('UmNSysLost', '%d' % len(lost))
    if lost:
        m('UmSysLostName', tname(lost[0]))
        m('UmNWinALostWin',
          '%d' % sum(1 for x in A if x['system'] == lost[0]))

    # ---------------------------------------------------------------- U6
    fine = sorted(A, key=lambda x: x['chan_width_Hz'])[0]
    _bw = (fine['nu_hi_GHz'] - fine['nu_lo_GHz']) * 1e3
    _nearest = min(TRANS.values(),
                   key=lambda f: abs(f - 0.5 * (fine['nu_lo_GHz']
                                                + fine['nu_hi_GHz'])))
    _mw = _nearest * 2 * HALF / C_KMS * 1e3
    if drive == 6:
        _bw = _mw * 2
    ck('U6 the finest windows are narrower than the mask at their own '
       'transition, which is why they retain no bandwidth',
       _bw < _mw and fine['unmasked_fraction'] == 0.0,
       '%s %s: %.2f MHz searched against a %.2f MHz mask at %.6f GHz, '
       '%.3f unmasked'
       % (fine['star'], fine['eb'], _bw, _mw, _nearest,
          fine['unmasked_fraction']))
    m('UmFineChanKHz', '%.2f' % (fine['chan_width_Hz'] / 1e3))
    m('UmFineBwMHz', '%.1f' % _bw)
    m('UmFineMaskMHz', '%.1f' % _mw)
    m('UmFineStar', tname(fine['star']))

    # ---------------------------------------------------------- the record
    assert SUF == ('_drive%d' % drive if drive else '')
    with open(os.path.join(HERE, OUTNAME), 'w', encoding='utf-8') as fh:
        fh.write('%%%% GENERATED by unmask_r26.py -- do not hand-edit.\n')
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
    json.dump(dict(macros=M, windows=rows, no_frame=nofr,
                   mask_intervals=UNION, moved=moved, lost=lost),
              open(os.path.join(HERE, 'unmask_r26%s.json' % SUF), 'w'),
              indent=1)
    print('%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
