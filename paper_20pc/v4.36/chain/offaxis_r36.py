#!/usr/bin/env python3
r"""offaxis_r36.py -- round 3620.  ROUND 36, R2-4: THE POINTING TERM, THE WINDOWS BEYOND THE INJECTED
OFFSETS, AND THE DEEPEST LIMIT THAT RESTS ON INJECTED CONFIGURATIONS.

(1) THE POINTING UNCERTAINTY.  Every limit divides by the primary-beam response A at the star's offset
theta (the documented Gaussian, FWHM = 1.13 lambda/D: sens_r11's pb_atten_fwhm_r11.csv, the beam the
limits use, beam_r17).  A pointing error delta moves A by d ln A = (d ln A/d theta) delta, with

    A = exp(-4 ln 2 theta^2 / FWHM^2),   |d ln A / d theta| = 8 ln 2 theta / FWHM^2 ,

so the limit is uncertain by the fraction 8 ln2 theta sigma_p / FWHM^2, sigma_p being ALMA's pointing
accuracy.  The ALMA Cycle 13 Technical Handbook (Cortes et al. 2026, \citep{ALMAHandbook}) gives it in
Sec. 10.3.3 and App. A.1: "Absolute pointing <= 2.0 arcsec all-sky.  Offset pointing <= 0.6 arcsec within
a 2 degree radius on the sky" -- one specification for every band (pointing is done in Band 6 and the
band offsets are calibrated, App. A).  The 0.6 arcsec offset value is ADOPTED (every block points on a
calibrator near its target); the 2.0 arcsec all-sky value is published beside it as the bound.  It is an
UNCERTAINTY and is NOT applied: the limit stays where it is.  Frozen inputs: POINTING below, with its
source; nothing else is typed.

(2) THE MARK.  A window lies BEYOND THE INJECTED OFFSETS where its star is further from the pointing
centre than any injected carrier (pbaudit_v408's injection units, the same record \PbInjOffMax is read
from) AND its response is below A_CUT = 0.4 (the register's threshold, a choice and not a measurement).
A system is marked where its BEST window is.  The pilcrow is taken (extrapolated limits, persys_r17 P12),
so the mark is a NEW one, a diamond (\OffMark); persys_r17 prints it (P14) from `beyond()` here.

(3) THE DEEPEST LIMIT THAT RESTS ON INJECTED CONFIGURATIONS: the deepest adopted limit among the
\NSysALimSum bounded-position systems whose best window is neither extrapolated (extrap_r33, the pilcrow)
nor beyond the injected offsets (the diamond).  No new injection (option b).

    python3 offaxis_r36.py              # -> numbers/survey_numbers_round3620.tex, offaxis_r36.json
    python3 offaxis_r36.py --drive N    # N = 1..6: prints FAILED: O<N>, writes nothing, exits 1

  O1 the pointing slope is the derivative of the response the limits use: on every window the analytic
     8 ln2 theta / FWHM^2 equals a finite difference of ln A(theta) from the csv's own A to 1e-3, and
     A itself is exp(-4 ln2 theta^2/FWHM^2) to 1e-4 (drive 1)
  O2 the uncertainty is zero exactly at the pointing centre, grows with theta/FWHM, the 2.0 arcsec value
     is the 0.6 one times 2.0/0.6, and the summaries are the set's own (median <= max) (drive 2)
  O3 the furthest injected offset is the record \PbInjOffMax is printed from, and every injected Class A
     window of the catalogue lies at or inside it (drive 3)
  O4 the marked windows are exactly those beyond that offset with A < A_CUT; every one is a transferred
     window (none was injected into), and the marked systems are those whose best window is marked (drive 4)
  O5 the deepest injected-configuration limit is the minimum over the bounded systems that are neither
     pilcrow nor diamond, no deeper than the deepest limit overall, and it is NOT a marked system (drive 5)
  O6 epsilon Eridani's best window is marked (the referee's case), and its limit is \EirpNinetySysLoA
     (drive 6)
MUST FOLLOW numbers_v410.py (round 103), sens_r11.py (pb_atten_fwhm_r11.csv), pbaudit_v408.py and
extrap_r33's inputs; MUST PRECEDE persys_r17.py's final pass? NO -- persys_r17 imports beyond() only,
which reads frozen inputs; the macros here precede macrosource.py.
"""
import csv
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

ROUND = 3620
A_CUT = 0.4
#: ALMA Cycle 13 Technical Handbook (Cortes et al. 2026, ALMA Doc. 13.3 v1.0, \citep{ALMAHandbook}),
#: Sec. 10.3.3 and App. A.1 -- frozen with its source; band-independent.
POINTING = dict(offset_arcsec=0.6, absolute_arcsec=2.0,
                source='ALMA Cycle 13 Technical Handbook (Cortes et al. 2026), Sec. 10.3.3 and App. A.1',
                bands='all (pointing in Band 6; band offsets calibrated, App. A)')
LN2 = math.log(2.0)

_PB = {}


def _pbtab(paper=HERE):
    if paper not in _PB:
        t = {}
        for r in csv.DictReader(open(os.path.join(paper, 'pb_atten_fwhm_r11.csv'))):
            t[(r['star_name'], r['eb'], '%.6f' % float(r['flo_GHz']))] = r
        _PB[paper] = t
    return _PB[paper]


def pb_row(row, paper=HERE):
    """(theta arcsec, FWHM arcsec of the documented beam, A) for one released catalogue row."""
    p = _pbtab(paper)[(row['star_name'], row['eb'], '%.6f' % float(row['flo_GHz']))]
    return float(p['pb_offset_arcsec']), float(p['theta_pb_fwhm_arcsec']), float(p['pb_atten_fwhm'])


def slope(row, paper=HERE):
    """|d ln A / d theta| in 1/arcsec at the star's offset."""
    th, fw, _a = pb_row(row, paper)
    return 8.0 * LN2 * th / fw ** 2


def pointing_frac(row, sigma=POINTING['offset_arcsec'], paper=HERE):
    """The fractional uncertainty of the limit from a pointing error sigma (arcsec)."""
    return slope(row, paper) * sigma


def inj_off_max(paper=HERE):
    """The furthest offset (arcsec) at which a carrier was injected: the maximum over the released catalogue's
    injected Class A windows (p90_basis = injected, the windows the class factor is measured on).

    ★ NOT pbaudit_v408's p90_pb.json (\\PbInjOffMax, 4.98"): that record holds the 40 injection units of the
    v4.08 campaign; the injected set has since grown to 49 windows, and ALMA J1537's block X73b0 was injected at
    5.74".  O3 requires this value to be at least the older record's."""
    best = 0.0
    for r in csv.DictReader(open(os.path.join(paper, 'per_target_results_v3.99.csv'))):
        if r['search_class'] == 'A' and r.get('p90_basis') == 'injected':
            best = max(best, pb_row(r, paper)[0])
    assert best > 0.0, 'no injected Class A window in the catalogue'
    return best


def beyond(row, paper=HERE, _off=None):
    """True where the star lies beyond every injected offset AND the response is below A_CUT."""
    th, _fw, a = pb_row(row, paper)
    return th > (inj_off_max(paper) if _off is None else _off) and a < A_CUT


def main():
    import adopted_e90 as ae
    import extrap_r33
    import posflag_r31 as pf
    import star_alias as sa

    DRIVE = None
    if '--drive' in sys.argv:
        DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
    OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex'
                           % (ROUND, '' if DRIVE is None else '_drive%d' % DRIVE))
    OUT_JSON = os.path.join(HERE, 'offaxis_r36%s.json' % ('' if DRIVE is None else '_drive%d' % DRIVE))
    OUT, FAIL = [], []

    def m(k, v):
        assert k.isalpha() and not any(x.startswith('\\newcommand{\\%s}' % k) for x in OUT), k
        OUT.append('\\newcommand{\\%s}{%s}' % (k, v))

    def ck(label, ok, detail=''):
        print('  %-74s %s  %s' % (label[:74], 'PASS' if ok else 'FAIL', detail))
        if not ok:
            FAIL.append(label.split()[0])

    def tv(name):
        v = ae._texval(name, HERE)
        assert v is not None, 'macro \\%s is not in the layer' % name
        return v

    def sci(x, nd=1):
        e = int(math.floor(math.log10(x)))
        return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)

    C = extrap_r33.classify(HERE)
    R, E = C['rows'], C['e90']
    A = [r for r in R if r['search_class'] == 'A']
    B = [r for r in R if r['search_class'] == 'B']

    # ---- O1 the slope is the derivative of the response the limits use
    _bad1 = 0
    for r in R:
        th, fw, a = pb_row(r)
        a_mod = math.exp(-4.0 * LN2 * th ** 2 / fw ** 2)
        h = 1e-3 * fw
        fd = abs(math.log(math.exp(-4 * LN2 * (th + h) ** 2 / fw ** 2))
                 - math.log(math.exp(-4 * LN2 * max(th - h, 0.0) ** 2 / fw ** 2))) / (th + h - max(th - h, 0.0))
        sl = slope(r) if DRIVE != 1 else 4.0 * LN2 * th / fw ** 2
        if abs(a_mod - a) > 1e-4 or (th > 2 * h and abs(sl / fd - 1.0) > 1e-3):
            _bad1 += 1
    ck('O1 the pointing slope is d ln A/d theta of the response the limits use (csv A = the Gaussian, analytic = '
       'finite difference)', _bad1 == 0, '%d of %d windows disagree' % (_bad1, len(R)))

    # ---- O2 the uncertainty: zero at the centre, monotone in theta/FWHM, the bound scales
    s0, s1 = POINTING['offset_arcsec'], POINTING['absolute_arcsec']
    U = {id(r): pointing_frac(r, s0) for r in R}
    U2 = {id(r): pointing_frac(r, s1) for r in R}
    if DRIVE == 2:
        U2 = {k: v * 2.0 for k, v in U.items()}
    _mono = all(U[id(r)] >= 0.0 and abs(U[id(r)] - 8 * LN2 * s0 * pb_row(r)[0] / pb_row(r)[1] ** 2) <= 1e-12
                for r in R)
    _zero = all((U[id(r)] == 0.0) == (pb_row(r)[0] == 0.0) for r in R)
    _scale = all(abs(U2[id(r)] - U[id(r)] * s1 / s0) <= 1e-12 + 1e-9 * U2[id(r)] for r in R)
    uA = sorted(U[id(r)] for r in A)
    uB = sorted(U[id(r)] for r in B)
    ck('O2 zero exactly at the pointing centre, the 2.0" bound is the 0.6" value x 2.0/0.6, median <= max',
       _zero and _scale and _mono and st.median(uA) <= uA[-1] and st.median(uB) <= uB[-1],
       'Class A median %.3f %%, max %.2f %%; Class B median %.3f %%, max %.2f %%'
       % (100 * st.median(uA), 100 * uA[-1], 100 * st.median(uB), 100 * uB[-1]))

    # ---- O3 the furthest injected offset (r36: the catalogue's injected set; at least pbaudit_v408's older record)
    OFF = inj_off_max()
    _old = max(u['off'] for u in json.load(open(os.path.join(HERE, 'pbaudit_v408', 'p90_pb.json')))['rows'])
    inj = [r for r in A if r['p90_basis'] == 'injected']
    _injoff = max(pb_row(r)[0] for r in inj)
    _off_used = OFF if DRIVE != 3 else _injoff * 0.5
    ck('O3 the furthest injected offset is the maximum over the catalogue\'s injected Class A windows, every one lies '
       'inside it, and it is at least the v4.08 record\'s (\\PbInjOffMax)',
       abs(_off_used - _injoff) < 1e-9 and _off_used >= _old - 1e-9 and len(inj) == int(tv('SensNInj')),
       '%d injected windows reach %.4f arcsec (%s); the 40-unit v4.08 record %.4f (printed \\PbInjOffMax %s)'
       % (len(inj), _injoff, [r['star_name'] for r in inj if abs(pb_row(r)[0] - _injoff) < 1e-9][:1], _old,
          tv('PbInjOffMax')))

    # ---- O4 the marked windows and systems
    MW = [r for r in A if beyond(r, _off=_off_used)]
    _want = [r for r in A if pb_row(r)[0] > OFF and pb_row(r)[2] < A_CUT]
    BEST = C['best']
    POP = {s: r for s, r in BEST.items() if not pf.is_cond(s)}
    MS = sorted(s for s, r in BEST.items() if beyond(r, _off=_off_used))
    if DRIVE == 4:
        MS = MS[1:]
    MSP = [s for s in MS if s in POP]
    ck('O4 marked windows = beyond the furthest injected offset with A < %.1f; all transferred; marked systems = '
       'those whose best window is marked' % A_CUT,
       [id(r) for r in MW] == [id(r) for r in _want] and all(r['p90_basis'] != 'injected' for r in MW)
       and MS == sorted(s for s, r in BEST.items() if beyond(r)) and len(MW) > 0,
       '%d windows toward %d systems; marked systems %s'
       % (len(MW), len({r['system_id'] for r in MW}), [sa.designation(s, tex=False) for s in MS]))

    # ---- O5 the deepest limit resting on injected configurations
    EX = set(C['ex_sys'])
    cand = sorted((E[id(r)], s) for s, r in POP.items() if s not in EX and s not in MS)
    if DRIVE == 5:
        cand = sorted((E[id(r)], s) for s, r in POP.items())
    allv = sorted(E[id(r)] for r in POP.values())
    deep_v, deep_s = cand[0]
    ck('O5 the deepest injected-configuration limit: minimum over the bounded systems neither pilcrow nor diamond, '
       'no deeper than the deepest overall, and not a marked system',
       deep_s not in MS and deep_s not in EX and deep_v >= allv[0] and len(POP) == int(tv('NSysALimSum')),
       '%s %.4e W (deepest overall %.4e W); %d candidates of %d'
       % (sa.designation(deep_s, tex=False), deep_v, allv[0], len(cand), len(POP)))

    # ---- O6 epsilon Eridani is marked and is the deepest limit
    _eps = [s for s in POP if sa.designation(s, tex=False).replace('epsilon', 'eps').startswith('eps Eri')]
    _epsm = bool(_eps) and _eps[0] in MS and DRIVE != 6
    ck('O6 epsilon Eridani\'s best window is marked, and its limit is \\EirpNinetySysLoA',
       _epsm and sci(E[id(POP[_eps[0]])]) == tv('EirpNinetySysLoA'),
       '%s: %s' % (_eps, sci(E[id(POP[_eps[0]])]) if _eps else '-'))

    # the summaries for Table 3 and the appendix: over every Class A window, over the systems' best windows
    uS = sorted(U[id(r)] for r in POP.values())
    _epsr = POP[_eps[0]] if _eps else None
    words = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
    m('PtSigmaOff', '%.1f' % s0)
    m('PtSigmaAbs', '%.1f' % s1)
    def pct_small(x):
        # a per cent at one significant figure below 1 per cent (a median of 0.02 must not print as 0.0)
        x = 100.0 * x
        return '%.0f' % x if x >= 1.0 else ('%.1g' % x if x > 0 else '0')
    m('PtUncMedPct', pct_small(st.median(uA)))
    m('PtUncMaxPct', '%.0f' % (100 * uA[-1]))
    m('PtUncMaxAbsPct', '%.0f' % (100 * U2[id(max(A, key=lambda r: U2[id(r)]))]))
    m('PtUncSysMedPct', pct_small(st.median(uS)))
    m('PtUncBMedPct', pct_small(st.median(uB)))
    m('PtUncBMaxPct', '%.0f' % (100 * uB[-1]))
    m('PtUncDeepPct', '%.0f' % (100 * U[id(_epsr)]) if _epsr is not None else '--')
    m('PtUncDeepAbsPct', '%.0f' % (100 * U2[id(_epsr)]) if _epsr is not None else '--')
    m('PtNWinTenth', '%d' % sum(1 for x in uA if x > 0.10))
    m('OffAcut', '%.1f' % A_CUT)
    m('OffInjMaxArcsec', '%.2f' % OFF)
    m('OffMark', r'\ensuremath{^{\diamond}}')
    m('OffNWin', '%d' % len(MW))
    m('OffNSys', '%d' % len(MSP))
    m('OffNSysWord', words[len(MSP)] if len(MSP) < len(words) else '%d' % len(MSP))
    _nm = [sa.designation(s).replace(' ', '~') for s in sorted(MSP, key=lambda s: E[id(POP[s])])]
    m('OffNames', ', '.join(_nm[:-1]) + ' and ' + _nm[-1] if len(_nm) > 1 else (_nm[0] if _nm else 'none'))
    m('OffAMin', '%.2f' % min(pb_row(r)[2] for r in MW))
    m('PtDeepInjEirp', sci(deep_v))
    m('PtDeepInjStar', sa.designation(deep_s))
    m('PtDeepInjBasis', 'injected' if POP[deep_s]['p90_basis'] == 'injected' else 'transferred')

    if FAIL:
        print('\nFAILED: %s' % '; '.join(FAIL))
        raise SystemExit(1)
    if DRIVE is not None:
        print('drive %d did not fire' % DRIVE)
        raise SystemExit(0)
    json.dump(dict(generated_by='offaxis_r36.py', round=ROUND, pointing=POINTING, a_cut=A_CUT,
                   inj_off_max_arcsec=OFF, marked_systems=MS,
                   deepest_injected_config=dict(system=deep_s, eirp90_W=deep_v),
                   windows=[dict(star=r['star_name'], eb=r['eb'], nu_lo_GHz=min(float(r['flo_GHz']), float(r['fhi_GHz'])),
                                 cls=r['search_class'], theta_arcsec=pb_row(r)[0], fwhm_arcsec=pb_row(r)[1],
                                 response=pb_row(r)[2], dlnA_dtheta_per_arcsec=slope(r),
                                 pointing_frac_offset=U[id(r)], pointing_frac_absolute=U2[id(r)],
                                 beyond_injected=bool(r['search_class'] == 'A' and beyond(r)))
                            for r in R]),
              open(OUT_JSON, 'w'), indent=0, sort_keys=True)
    hdr = ['%% GENERATED by offaxis_r36.py (round %d) -- do not hand-edit.' % ROUND,
           '% R2-4: the pointing uncertainty (ALMA Cycle 13 Technical Handbook 10.3.3/A.1), the windows beyond the'
           ' injected offsets, the deepest limit resting on injected configurations.']
    open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
    print('offaxis_r36: %d macros -> %s' % (len(OUT), os.path.basename(OUT_TEX)))


if __name__ == '__main__':
    main()
