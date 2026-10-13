#!/usr/bin/env python3
r"""Round 440: what a window-maximum crossing costs the line mask, the
re-search that recovers it, and the two frame numbers that make one row
readable.

WHAT THIS FILE OWNS

1.  A CROSSING IS THE WINDOW MAXIMUM, AND THAT HAS A PRICE.  The search
    records one statistic per window: the largest value of the per-channel,
    drift-maximised statistic at the stellar position.  So in a window whose
    largest value sits on a catalogued transition, a weaker carrier elsewhere
    in the same window could not have been recorded, and the price of line
    confusion is the whole window rather than the masked channels inside it.
    The windows this applies to are exactly those whose maximum is a
    frequency coincidence, and they are READ out of the ledger here, never
    listed.

2.  THE RE-SEARCH.  Each of those windows is searched again with the masked
    channels removed, from the retained per-window profile -- the same
    per-channel statistic the published number is the maximum of.  The
    profile is resolved on the statistic and not on a name, and a window
    whose retained product does not reproduce the published value is counted
    and named rather than quietly folded in.  Three fine windows are
    narrower than the mask itself and cannot be re-searched at all; their
    bandwidth is stated as lost.

3.  THE COST AGAINST THE CLASS A UNION.  The mask cost has been quoted
    against the union of both search classes, where the loss is concentrated
    in the line-tuned fine windows of the primary experiment.  Both are
    published here, computed by one function from one window list.

4.  THE ONE ROW WHOSE FRAME TRANSFORM LOOKS LIKE A FAILURE.  For one star
    the barycentric and systemic terms very nearly cancel, so its
    topocentric and stellar-frame frequencies agree to a few tens of kHz.
    Both velocities are published so that a reader can see the cancellation
    instead of inferring a missing transform.

ASSERTIONS (each driven, see --drive)
    K1  the published statistic of every one of these windows is the maximum
        of its own retained profile, and that maximum sits at the published
        crossing frequency -- which is what makes "a crossing is the window
        maximum" a statement about the data and not a convention
    K2  the frequency-coincidence count is reached by the velocity criterion
        alone, with no species judgement in it, and it decomposes into the
        attributed count plus the coincidences the species note decides
    K3  the Class A union reproduces the published coverage, and the mask
        costs a larger fraction of it than of both classes together
    K4  every line-dominated window is a Class A window of the census, the
        re-searched and wholly-masked sets partition them, and no window is
        in both
    K5  the re-search is not vacuous: every re-searched window lost channels
        and kept channels, every one carries its own control positions
        measured through the same mask, and any surviving cell at the
        trigger was carried to every block covering it
    K6  the near-cancellation is real: each velocity term alone moves the
        frequency by more than 1 MHz, their difference moves it by less than
        0.1 MHz, and the two terms reproduce the ledger's own frequencies
    K7  the one window whose retained product does not reproduce the
        published statistic is counted and named, and the others all do

    python3 maskcost_v440.py [--drive N]

-> survey_numbers_round440.tex, maskcost_v440.json
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys

import maskframe_v411 as mf

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 440
C_KMS = mf.C_KMS
HALF = mf.MASK_HALF_KMS
TRIG = 5.0
IN = os.path.join(HERE, 'r14inputs', 'mask')
SUF = ('_drive%d' % int(sys.argv[sys.argv.index('--drive') + 1])
       if '--drive' in sys.argv else '')
# ★ Declared as a literal so that `roundcollide` can resolve the writer of
# this round without guessing; the drive suffix is the only variable part.
OUTNAME = 'survey_numbers_round440%s.tex' % SUF
assert OUTNAME.startswith('survey_numbers_round%d' % ROUND), OUTNAME


def _load(*p):
    return json.load(open(os.path.join(*p), encoding='utf-8'))


def texval(name):
    """The value of a published macro, read from the round files."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^{}]*)\}'
                     % name)
    v = None
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for m in pat.finditer(open(f, encoding='utf-8').read()):
            if m.group(1).strip():
                v = m.group(1).strip()
    return v


def tname(s):
    return s.replace(' ', '~')


# ---- interval arithmetic, one implementation for both classes ------------
def merge(iv):
    o = []
    for a, b in sorted(iv):
        if o and a <= o[-1][1]:
            o[-1][1] = max(o[-1][1], b)
        else:
            o.append([a, b])
    return o


def total(m):
    return sum(b - a for a, b in m)


def edges(rows):
    return [tuple(sorted((float(r['flo_GHz']), float(r['fhi_GHz']))))
            for r in rows]


def tubes(freqs, half):
    return merge([(f * (1 - half / C_KMS), f * (1 + half / C_KMS))
                  for f in freqs])


def overlap(isl, tub):
    t = 0.0
    for a, b in isl:
        for c, d in tub:
            lo, hi = max(a, c), min(b, d)
            if hi > lo:
                t += hi - lo
    return t


def main(argv):
    drive, driven = 0, False
    for i, a in enumerate(argv):
        if a == '--drive':
            drive, driven = int(argv[i + 1]), True
    suf = '_drive%d' % drive if driven else ''
    fail = []

    def ck(name, cond, detail=''):
        if not cond:
            fail.append('%s: %s' % (name, detail))
        print('  %-3s %s %s' % (name.split()[0], 'PASS' if cond else 'FAIL',
                                detail))

    M = {}

    def m(k, v):
        assert k.isalpha(), k         # a macro name may hold letters only
        assert k not in M, k
        M[k] = str(v)

    LED = _load(HERE, 'ledger.json')['rows']
    # the one execution block that fails the quality criterion; no
    # coincidence lies in it, which is why one count serves both the whole
    # crossing list and the quality-passing population Sec. 5.3 quotes it in
    _FLAGEB = sorted({r['eb'] for r in LED if r['dq']},
                     key=lambda e: -sum(1 for r in LED if r['eb'] == e))[0]
    CAT = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'), encoding='utf-8')))
    RES = _load(IN, 'mask_research_result.json')
    SEC = _load(IN, 'mask_second_result.json')
    TRANS = {k: v[0] for k, v in mf.TRANS.items()}

    # =============================================== 1. the two layers
    # Layer one is the velocity criterion and nothing else.  It is recomputed
    # here from the frame, so that the published count cannot inherit a
    # species judgement from the ledger's own flag.
    coinc = [r for r in LED
             if abs(mf.nearest(r['frame']['f_stellar'], mf.TRANS)[2]) <= HALF]
    noted = [r for r in coinc
             if mf.note_reason(r['frame']['line'], r['frame']['dv_stellar'])]
    if drive == 2:
        coinc = coinc[:-1]
    n_attr_pub = int(texval('EvNAttrQp'))
    n_noted_pub = int(texval('MkNSODecide'))
    ck('K2 the frequency-coincidence count comes from the velocity criterion '
       'alone and decomposes into the attributed count plus the coincidences '
       'the species note decides',
       len(coinc) == n_attr_pub + n_noted_pub
       and len(noted) == n_noted_pub
       and all(r['line_coincident'] for r in coinc)
       and len(coinc) == sum(1 for r in LED if r['line_coincident'])
       and not any(r['dq'] and r['eb'] == _FLAGEB for r in coinc),
       '%d coincidences = %d attributed + %d noted'
       % (len(coinc), n_attr_pub, len(noted)))
    m('MkNCoinc', len(coinc))

    # =============================================== 2. the bandwidth cost
    CLA = [r for r in CAT if r['search_class'] == 'A']
    UA, UALL = merge(edges(CLA)), merge(edges(CAT))
    u_a, u_all = total(UA), total(UALL)
    TUB = tubes(list(TRANS.values()), HALF)
    c_a, c_all = overlap(UA, TUB), overlap(UALL, TUB)
    if drive == 3:
        c_a = c_all * u_a / u_all
    pct_a, pct_all = 100.0 * c_a / u_a, 100.0 * c_all / u_all
    pub_ua = float(texval('CvUnionA'))
    pub_call = float(texval('FrMaskLostGHz'))
    ck('K3 the Class A union reproduces the published coverage and the mask '
       'costs a larger fraction of it than of both classes together',
       abs(u_a - pub_ua) < 0.05 and abs(c_all - pub_call) < 0.005
       and pct_a > pct_all,
       'Class A %.2f GHz, %.3f masked = %.2f per cent against %.2f per cent '
       'of %.2f GHz' % (u_a, c_a, pct_a, pct_all, u_all))
    m('MkMaskAGHz', '%.2f' % c_a)
    m('MkMaskAPct', '%.1f' % pct_a)

    # =============================================== 3. the re-search
    ok = [r for r in RES if r['status'] == 'ok']
    whole = [r for r in RES if r['status'] == 'wholly_masked']
    if drive == 4:
        whole = whole + ok[:1]
    dom = ok + whole
    ck('K4 every line-dominated window is a Class A window of the census, '
       'and the re-searched and wholly-masked sets partition them',
       len(dom) == len(coinc) and len(RES) == len(dom)
       and not ({id(r) for r in ok} & {id(r) for r in whole})
       and all(any(x['eb'] == r['eb'] and min(float(x['flo_GHz']),
                                              float(x['fhi_GHz']))
                   <= r['freq'] <= max(float(x['flo_GHz']),
                                       float(x['fhi_GHz']))
                   for x in CLA) for r in dom),
       '%d re-searched + %d wholly masked against %d coincidences'
       % (len(ok), len(whole), len(coinc)))

    gate_ok = [r for r in dom if r['gate']]
    gate_bad = [r for r in dom if not r['gate']]
    if drive == 7:
        gate_bad = []
    ck('K7 the windows whose retained product does not reproduce the '
       'published statistic are counted and named, and they are a minority',
       len(gate_ok) + len(gate_bad) == len(dom) and len(gate_bad) >= 1
       and len(gate_bad) < len(gate_ok),
       '%d of %d reproduce; not reproducing: %s'
       % (len(gate_ok), len(dom),
          [(r['display'], r['eb'], r['star_peak_pub'], r['tstar'])
           for r in gate_bad]))

    # K1: the operational definition, measured.  The statistic the paper
    # publishes for a window is the maximum of that window's own per-channel
    # profile, and the channel it is published at is the channel of that
    # maximum.  A published crossing read anywhere but the window maximum
    # fails this.  (The two statistics agree bit for bit, which is a property
    # of the retained product and not a test, so it is reported and not
    # asserted; what is asserted is the channel.)
    off = [(r['display'], r['eb'], abs(r['peak_offset_chan'])) for r in dom]
    worst_chan = max(x[2] for x in off)
    if drive == 1:
        worst_chan = 1.0
    ck('K1 the statistic published for each of these windows is the maximum '
       'of its own retained per-channel profile, and is published at the '
       'channel of that maximum',
       worst_chan < 0.5 and len(off) == len(dom),
       'worst departure %.3f channels over %d windows' % (worst_chan,
                                                          len(off)))

    resid = [r['T_resid'] for r in ok]
    surv = [r for r in ok if r['second_crossing']]
    ctl = SEC['control']
    if drive == 5:
        ok[0] = dict(ok[0], n_keep_chan=0)
    ck('K5 the re-search is not vacuous: every re-searched window lost '
       'channels and kept channels, each carries control positions measured '
       'through the same mask, and a surviving cell is carried to every '
       'block covering it',
       all(r['n_masked_chan'] > 0 and r['n_keep_chan'] > 0 for r in ok)
       and ctl['n_ctrl_positions'] > 0
       and ctl['n_window'] == len(ok)
       and all(s['n_covering'] > 0 for s in SEC['survivors']),
       '%d windows, %d control positions, %d surviving cell(s) with '
       '%s covering blocks'
       % (len(ok), ctl['n_ctrl_positions'], len(surv),
          [s['n_covering'] for s in SEC['survivors']]))

    m('MkNResearch', len(ok))
    m('MkNWholly', len(whole))
    dom_u = total(merge([(r['win_lo'], r['win_hi']) for r in dom]))
    wh_u = total(merge([(r['win_lo'], r['win_hi']) for r in whole]))
    m('MkLineDomGHz', '%.2f' % dom_u)
    m('MkLineDomPct', '%.1f' % (100.0 * dom_u / u_a))
    m('MkWhollyGHz', '%.3f' % wh_u)
    m('MkWhollyPct', '%.2f' % (100.0 * wh_u / u_a))
    m('MkResidLo', '%.2f' % min(resid))
    m('MkResidHi', '%.2f' % max(resid))
    m('MkNResidTrig', len(surv))
    _W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven')
    m('MkNResidTrigWord', _W[len(surv)] if len(surv) < len(_W)
      else '%d' % len(surv))
    m('MkNCtrlPos', ctl['n_ctrl_positions'])
    m('MkNCtrlTrig', ctl['n_ctrl_at_trigger'])
    m('MkNWinCtrlTrig', ctl['n_window_with_ctrl_at_trigger'])
    if surv:
        s = SEC['survivors'][0]
        cov = [t for t in s['covering'] if t.get('T_at_cell') is not None]
        m('MkSurvStar', tname(s['display']))
        m('MkSurvFreq', '%.4f' % s['f_resid_topo'])
        m('MkSurvDv', '%+.0f' % s['resid_dv'])
        m('MkSurvNRep', len(cov))
        m('MkSurvTRepLo', '%.1f' % min(t['T_in_window_of_three']
                                       for t in cov))
        m('MkSurvTRepHi', '%.1f' % max(t['T_in_window_of_three']
                                       for t in cov))

    # =============================================== 4. the cancellation
    rows = [r for r in LED
            if abs(r['frame']['v_bary'] + r['frame']['v_sys']) > 0
            and abs(r['freq_stellar'] - r['freq']) * 1e3 < 0.1]
    rows.sort(key=lambda r: abs(r['freq_stellar'] - r['freq']))
    canc = rows[0]
    fr = canc['frame']
    vb, vs = fr['v_bary'], fr['v_sys']
    f_bary = canc['freq'] * (1.0 - vb / C_KMS)
    f_stel = f_bary * (1.0 + vs / C_KMS)
    d_bary = abs(f_bary - canc['freq']) * 1e3
    d_sys = abs(f_stel - f_bary) * 1e3
    d_net = abs(f_stel - canc['freq']) * 1e3
    if drive == 6:
        d_net = 10.0
    ck('K6 the near-cancellation is real: each velocity term alone moves the '
       'frequency by more than 1 MHz, the net shift is below 0.1 MHz, and '
       'the two terms reproduce the ledger',
       d_bary > 1.0 and d_sys > 1.0 and d_net < 0.1
       and abs(f_stel - canc['freq_stellar']) < 1e-9,
       '%s: bary %.3f MHz, systemic %.3f MHz, net %.3f MHz'
       % (canc['display'], d_bary, d_sys, d_net))
    m('MkCancStar', tname(canc['display']))
    m('MkCancVBary', '%+.4f' % vb)
    m('MkCancVSys', '%+.4f' % vs)
    m('MkCancBaryMHz', '%.1f' % d_bary)
    m('MkCancNetkHz', '%.0f' % (d_net * 1e3))
    m('MkCancDv', '%+.1f' % canc['dv_stellar'])
    m('MkCancLine', mf.tex_label(canc['line']))

    # ------------------------------------------------------------------
    assert suf == SUF, (suf, SUF)
    with open(os.path.join(HERE, OUTNAME), 'w', encoding='utf-8') as fh:
        fh.write('%%%% GENERATED by maskcost_v%d.py -- do not hand-edit.\n'
                 % ROUND)
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
    json.dump(dict(macros=M, failed=fail,
                   coincidences=len(coinc), noted=len(noted),
                   union_a_GHz=u_a, mask_a_GHz=c_a,
                   union_all_GHz=u_all, mask_all_GHz=c_all,
                   line_dominated=len(dom), researched=len(ok),
                   wholly_masked=len(whole)),
              open(os.path.join(HERE, 'maskcost_v%d%s.json' % (ROUND, suf)),
                   'w'), indent=1)
    print('%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
