#!/usr/bin/env python3
r"""misc_r35.py -- round 3540: limits and sets (round-35 Referee 2 items M5, M1, m1, m2, m6, m7).

Reads only products already in the tree (the released catalogue through adopted_e90, the recombined-field record,
the per-window generation record, the deposit's system table inputs, the ledger, the recurrence columns, the chance
record, the injection-response record and the macro layer) and writes numbers/survey_numbers_round3540.tex and
misc_r35.json.  NOTHING IS TYPED except the two declared constants below (the 90 per cent completeness level the
limits are defined at, and the +-50 km/s tube of the frozen mask, read from appm_v405.py's own source).

  E1-E6 (M5) THE DEEPEST LIMIT.  The system with the deepest Class A limit over the summaries' systems is
     epsilon Eridani's census window; this file finds it from the data (never by name) and asserts:
     E1 it is the printed headline (\EirpNinetySysLoA) and the window Table F1 prints for the star (\BmEpsCenEb);
     E2 its star offsets, from the field-recombined record's own per-pointing geometry, are inside the offset at which
        the documented Gaussian and the blocked-aperture response part by the tolerance that sets the response floor
        (beam_r17's MODEL_TOL, solved here for the window's OWN dish exactly as beam_r17 solves it), and the binding
        floor solved here is beam_r17's (so it is one beam model, not a second);
     E3 the limit product omits no annual parallax: its generation record is the final extractor (E3) and the
        recombined record stores the star at its APPARENT position -- so the "up to N per cent" parallax bound of
        App. A applies to the star's OTHER blocks, whose limits are not its best, and their count is printed;
     E4 the system's decorrelation basis is 'none' (no phase-rms record and no matched block), it is the only system
        of the summaries with none, and the deposited system row says the same;
     E5 the extension's withheld eps Eri windows are withheld by the star-band rule and by nothing else: the response
        floor removes none of them (epsx_v423.json) and every one lies inside the beam-model agreement radius;
     E6 the deepest window lies further off axis than any injected carrier, so its response rests on the beam model
        (E2) and not on an injection -- printed as a fact.
  B1-B2 (M1) the best-window frequency range over the summaries' systems (lower edge of the lowest, upper edge of the
     highest, and the centres), the lower-edge pair being round 103's \BenchTunedFreqLo/Hi; the number of carriers at
     their limit a 90 per cent completeness misses, 0.1 x \NSysALimSum, rounded, with its word.
  S1-S4 (m1) the sets: the unattributed crossings that the clustering test (quality_r19) and the recurrence test
     (census_v412 / recur_v411) are run over are the census's \CeObs PLUS the archival tail's \CeNTailCross, by
     membership (chance_v414.json observed_rows / observed_tail against ledger.json); the per-window catalogue's
     crossing rows (appm_v405) split into the census crossings and the rows the census supersedes; and the tube
     occupancy is recomputed over the census crossings alone (same frozen mask, same null, own seed).
  K1-K3 (m2) the channel-response decomposition: the injection kernel's centre/boundary/phase-mean shares are the
     analytic 0.25/0.5/0.25 values, the response factor is 1/phase mean, the printed product is the printed class
     factor, and the measured correlator response (\HanWorst on a boundary) is a different quantity whose ratio to
     the kernel is printed beside the injected rho_1.
  C1 (m6) the +-\BudComb calibration interval is the quadrature of the flux-scale specification (\BudFlux), the
     distance/visibility term (\BudDistVis) and the injection sampling term, to the printed precision.
  W1-W2 (m7) every system whose best window switched under the crossing-level reading (\XwSwitchNames): the window
     the tabulated limit now refers to, its frequency and channel width, and the crossing window's limit beside it.

    python3 misc_r35.py [--drive N]     N = 1..14: each perturbs one input in memory, prints FAILED and exits 1
                                        without writing a production path
"""
import collections
import csv
import json
import math
import os
import statistics as st
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import adopted_e90 as ae            # noqa: E402
import census_rule                  # noqa: E402
import pbgate_v408 as pbg           # noqa: E402
import posflag_r31 as pf            # noqa: E402
import recombfold_r30 as rc         # noqa: E402
import star_alias                   # noqa: E402

ROUND = 3540
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
J = lambda p: json.load(open(os.path.join(HERE, p)))  # noqa: E731
T = lambda k: ae._texval(k, HERE)                    # noqa: E731
OUT, FAIL, INFO = {}, [], {}
WORD = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve')
word = lambda k: WORD[k] if k < len(WORD) else '%d' % k  # noqa: E731
COMPLETENESS = 0.90        # the level EIRP_90 is defined at (declared: the definition of the limit)
MODEL_TOL = 0.10           # beam_r17's tolerance; asserted equal to the printed \BmFloorTolPct below


def m(k, v):
    assert k.isalpha() and k not in OUT, k
    OUT[k] = v


def ck(label, ok, detail=''):
    print('  %-4s %s  %s' % (label.split()[0], 'PASS' if ok else 'FAIL', label[len(label.split()[0]):][:110]))
    if detail:
        print('         ' + str(detail))
    if not ok:
        FAIL.append(label.split()[0])


def sci(x, nd=1):
    e = int(math.floor(math.log10(x)))
    return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)


def tt(eb):
    return r'\texttt{%s}' % eb.replace('_', r'\_')


def lohi(r):
    return (min(float(r['flo_GHz']), float(r['fhi_GHz'])), max(float(r['flo_GHz']), float(r['fhi_GHz'])))


print('misc_r35: round %d%s' % (ROUND, '' if DRIVE is None else '  (drive %d)' % DRIVE))
CAT = ae.catalogue(HERE)
E = ae.per_window(CAT, HERE)
COEF_DOC = float(T('RingPbCoef'))
COEF_NULL = float(T('RingPbCoefCode'))
assert abs(100 * MODEL_TOL - float(T('BmFloorTolPct'))) < 1e-9, T('BmFloorTolPct')

# ------------------------------------------------------------------ the summaries' systems and their best windows
BEST = {}
for r in CAT:
    if r['search_class'] != 'A' or not ae.limit_eligible(r, HERE) or pf.is_cond(r['system_id']):
        continue
    s = r['system_id']
    if s not in BEST or E[id(r)] < E[id(BEST[s])]:
        BEST[s] = r
NSYS = len(BEST)
assert NSYS == int(T('NSysALimSum')), (NSYS, T('NSysALimSum'))
DEEP_S = min(BEST, key=lambda s: E[id(BEST[s])])
DEEP = BEST[DEEP_S]
SECOND_S = sorted(BEST, key=lambda s: E[id(BEST[s])])[1]

# ================================================================== M5
print('\nM5  the deepest limit')
_deep_e = E[id(DEEP)]
if DRIVE == 1:
    _deep_e *= 1.2
ck('E1 the deepest system limit over the summaries is the printed headline and is the window Table F1 prints for '
   'that star', sci(_deep_e) == T('EirpNinetySysLoA') and tt(DEEP['eb']) == T('BmEpsCenEb')
   and sci(_deep_e) == T('BmEpsCenEirp'),
   '%s %s %.4f GHz: %s against \\EirpNinetySysLoA %s, \\BmEpsCenEb %s'
   % (DEEP_S, DEEP['eb'], sum(lohi(DEEP)) / 2, sci(_deep_e), T('EirpNinetySysLoA'), T('BmEpsCenEb')))


def gauss_c(c, coef):
    return math.exp(-4.0 * math.log(2.0) * (c / coef) ** 2)


def airy_c(c, dish):
    lam = 1.0e-3
    return pbg.airy_casa(c * lam / dish / (math.pi / 180 / 3600), lam, dish)


def dev_at(c, dish):
    return abs(gauss_c(c, COEF_DOC) / airy_c(c, dish) - 1.0)


def floor_c(dish):
    """beam_r17.floor_c, verbatim in method: the outer-branch bisection for the 10 per cent parting radius."""
    lo, hi = 0.70, 1.30
    assert dev_at(lo, dish) < MODEL_TOL < dev_at(hi, dish), dish
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if dev_at(mid, dish) < MODEL_TOL:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


BJ = J('beam_r17.json')
FC = {d: floor_c(d) for d in (7.0, 12.0)}
_bind = min(FC.values())
REC = rc.lookup_row(DEEP)
assert REC is not None, 'the deepest window is no longer a field-recombined row: re-derive E2 on its single offset'
DISH = float(REC['dish_m'])
FGHZ = REC['freqmed_hz'] / 1e9
LDA = 2.99792458e8 / REC['freqmed_hz'] / DISH * 206264.80624709636        # lambda/D, arcsec
FWHM = COEF_DOC * LDA
OFFS = sorted(f['offset_arcsec'] for f in REC['fields'])
CS = [o / LDA for o in OFFS]
_cmax = CS[-1] if DRIVE != 2 else 1.2 * FC[DISH]
_devmax = max(dev_at(c, DISH) for c in CS)
ck('E2 every pointing of the deepest window puts the star inside the radius where the documented Gaussian and the '
   'blocked-aperture response part by the floor tolerance, on the window\'s own dish, and that radius is solved by '
   'beam_r17\'s method (its binding value reproduces beam_r17.json)',
   _cmax < FC[DISH] and _devmax < MODEL_TOL and abs(_bind - BJ['floor']['c']) < 1e-9
   and abs(REC['pb_offset_arcsec'] - float(DEEP['pb_offset_arcsec'])) < 1e-3,
   '%d pointings at %.2f-%.2f arcsec = %.3f-%.3f lambda/D = %.3f-%.3f FWHM (FWHM %.2f arcsec at %.2f GHz, %g m); '
   'radius %.3f lambda/D on %g m (binding %.4f vs beam_r17 %.4f); worst agreement %.1f per cent'
   % (len(OFFS), OFFS[0], OFFS[-1], CS[0], CS[-1], OFFS[0] / FWHM, OFFS[-1] / FWHM, FWHM, FGHZ, DISH,
      FC[DISH], DISH, _bind, BJ['floor']['c'], 100 * _devmax))
m('EdDeepStar', star_alias.designation(DEEP_S).replace(' ', '~'))
m('EdDeepEb', tt(DEEP['eb']))
m('EdDeepGHz', '%.2f' % (sum(lohi(DEEP)) / 2))
m('EdDeepChanKHz', '%.0f' % (float(DEEP['chanw_Hz']) / 1e3))
m('EdDeepDish', '%.0f' % DISH)
m('EdDeepNPoint', '%d' % len(OFFS))
m('EdDeepOffLo', '%.1f' % OFFS[0])
m('EdDeepOffHi', '%.1f' % OFFS[-1])
m('EdDeepFwhm', '%.1f' % FWHM)
m('EdDeepFwhmFracLo', '%.2f' % (OFFS[0] / FWHM))
m('EdDeepFwhmFracHi', '%.2f' % (OFFS[-1] / FWHM))
m('EdDeepCLo', '%.2f' % CS[0])
m('EdDeepCHi', '%.2f' % CS[-1])
m('EdDeepAgreePct', '%.0f' % math.ceil(100 * _devmax))
m('EdFloorCOwn', '%.2f' % FC[DISH])
m('EdDeepResp', '%.2f' % gauss_c(REC['pb_offset_arcsec'] / LDA, COEF_DOC))
INFO['deep'] = dict(system=DEEP_S, eb=DEEP['eb'], eirp=_deep_e, ghz=FGHZ, dish=DISH, offsets=OFFS, c=CS,
                    fwhm_arcsec=FWHM, floor_c_own=FC[DISH], floor_c_binding=_bind, worst_dev=_devmax,
                    second_system=SECOND_S, second_eirp=E[id(BEST[SECOND_S])])
# the next-deepest system, printed so that a reader (and the integrator) can see what would take the headline
m('EdNextStar', star_alias.designation(SECOND_S).replace(' ', '~'))
m('EdNextEirp', sci(E[id(BEST[SECOND_S])]))

# E3 parallax
WV = J(os.path.join('r31inputs', '20261105', 'windows_version.json'))
_wv = [w for w in WV if w['set'] == 'census' and w['eb'] == DEEP['eb']
       and abs(min(w['flo'], w['fhi']) - lohi(DEEP)[0]) < 1e-4]
assert len(_wv) == 1, _wv
_gen = _wv[0]['gen_limit'] if DRIVE != 3 else 'E1'
_conv = REC['pos_convention']
_epsw = [w for w in WV if w['set'] == 'census' and w['star'] == DEEP['star_name']]
_omit = [w for w in _epsw if w['gen_limit'] != 'E3']
_omit_eb = sorted({w['eb'] for w in _omit})
_omit_best = min(E[id(r)] for r in CAT if r['star_name'] == DEEP['star_name'] and r['eb'] in _omit_eb
                 and r['search_class'] == 'A')
ck('E3 the deepest limit omits no annual parallax (final extractor, star at its apparent position); the star\'s '
   'windows whose limit products predate that extractor are in other blocks and none of them sets its best limit',
   _gen == 'E3' and _conv.startswith('apparent') and DEEP['eb'] not in _omit_eb and _omit
   and _omit_best > _deep_e and len(_epsw) == int(T('BmEpsNCensus')),
   'gen_limit %s, %s; %d of %d census windows on older products in %s, deepest of them %.3g W'
   % (_gen, _conv, len(_omit), len(_epsw), _omit_eb, _omit_best))
m('EdPxNOmitWin', '%d' % len(_omit))
m('EdPxNOmitEb', '%d' % len(_omit_eb))
m('EdPxOmitBest', sci(_omit_best))
# and the bound those older windows carry: each block's own annual-parallax displacement (r20inputs/epsx_r20.json,
# the record beam_r17 B17/B18 validate) in synthesised beams from the archive's own resolution scaled to the window
# (beam_r17 B16's substitute, validated on 12 m; on the compact array it is not, so the beam there is taken 1.5x
# SMALLER, the conservative direction), and the retention interpolated between the two injected points exactly as
# epsx_v423 does (never extrapolated past the larger one).
EPSX = J(os.path.join('r20inputs', 'epsx_r20.json'))
AMETA = J('archive_meta_v381.json')['ebs']
_pb, _pm = float(T('SensPxSmallBeams')), float(T('SensPxSmallMeas'))
_lb, _lm = float(T('SensPxLargeBeams')), float(T('SensPxLargeMeas'))
_bounds = {}
for eb in _omit_eb:
    am = AMETA[eb]
    f0 = st.median([0.5 * (a + b) for a, b, _c in am['freq_support']])
    fw = st.median([0.5 * sum(lohi(r)) for r in CAT if r['eb'] == eb and r['star_name'] == DEEP['star_name']])
    syn = am['s_resolution_arcsec'] * f0 / fw / (1.0 if am['array'] == '12m' else 1.5)
    u = EPSX['blocks'][eb]['dpar_arcsec'] / syn
    assert u < _lb, (eb, u, _lb)              # inside the injected range, or the bound is an extrapolation
    ret = _pm if u <= _pb else _pm + (u - _pb) / (_lb - _pb) * (_lm - _pm)
    _bounds[eb] = dict(array=am['array'], dpar=EPSX['blocks'][eb]['dpar_arcsec'], syn=syn, beams=u,
                       bound_pct=100.0 * (1.0 / ret - 1.0))
_bmax = max(v['bound_pct'] for v in _bounds.values())
print('         parallax bound on the older blocks: %s' % {k: '%.3f beams, %.1f%%' % (v['beams'], v['bound_pct'])
                                                          for k, v in _bounds.items()})
m('EdPxOmitBoundPct', '%.0f' % math.ceil(_bmax))
m('EdPxOmitBeamsHi', '%.2f' % max(v['beams'] for v in _bounds.values()))
INFO['parallax_bounds'] = _bounds
INFO['parallax'] = dict(gen_limit=_gen, pos_convention=_conv, omit_eb=_omit_eb, n_omit=len(_omit))

# E4 decorrelation
SYS = list(csv.DictReader(open(os.path.join(HERE, 'sens_r28_systems.csv'))))
_none = [r for r in SYS if r['decor_basis'] == 'none' and not pf.is_cond(r['system'])]
if DRIVE == 4:
    _none = _none + [SYS[1]]
ck('E4 the deepest system carries no decorrelation estimate (basis none) and is the only system of the summaries '
   'that has none', len(_none) == 1 and _none[0]['system'] == DEEP_S and _none[0]['best_eb'] == DEEP['eb'],
   [(r['system'], r['best_eb'], r['decor_basis']) for r in _none])
m('EdDecorNNone', '%d' % len(_none))
m('EdDecorNNoneWord', word(len(_none)))

# E5 the extension's withheld windows
EX = J('epsx_v423.json')
EXT = [r for r in J('export_extension.json')['rows'] if r.get('star_snr') is not None]
_wh = census_rule.withheld_extension(EXT)
_exc = []
for r in EX['rows']:
    _ld = 2.99792458e8 / (0.5 * (r['_lo'] + r['_hi']) * 1e9) / float(r['dish_m']) * 206264.80624709636
    _exc.append((r['_off'] / _ld, float(r['dish_m'])))
_cw = max(c for c, d in _exc)
_nfloor = EX['predicate']['floor_removes'] if DRIVE != 5 else 1
ck('E5 the extension\'s eps Eri windows are withheld by the star-band rule alone: the response floor removes none, '
   'every one lies inside the beam-model agreement radius of its own dish, and none reaches the trigger',
   len(_wh) == int(T('ExNExtWin')) == int(T('BmEpsNExt')) == len(EX['rows']) and _nfloor == 0
   and int(T('ExNFloorRemoves')) == 0 and all(c < FC[d] and dev_at(c, d) < MODEL_TOL for c, d in _exc)
   and max(r['star_snr'] for r in EX['rows']) < 5.0,
   '%d withheld (\\ExNExtWin %s, \\BmEpsNExt %s); floor removes %d; worst offset %.3f lambda/D, worst agreement '
   '%.1f per cent; T max %.2f' % (len(_wh), T('ExNExtWin'), T('BmEpsNExt'), _nfloor, _cw,
                                  100 * max(dev_at(c, d) for c, d in _exc), max(r['star_snr'] for r in EX['rows'])))
m('EdExtAgreePct', '%.0f' % math.ceil(100 * max(dev_at(c, d) for c, d in _exc)))
m('EdExtNEb', '%d' % len({r['eb'] for r in _wh}))
# (the window count is \\ExNExtWin = \\BmEpsNExt, asserted equal above; the offset \\ExCWorstExt; not re-emitted)

# E6 beyond the injection reach
_inj = float(T('PbInjOffMax'))
ck('E6 the deepest window lies further off axis than any injected carrier, so its response is the beam model\'s',
   OFFS[0] > _inj if DRIVE != 6 else False, '%.2f arcsec against a furthest injection at %.2f' % (OFFS[0], _inj))

# ================================================================== M1
print('\nM1  the best-window frequency range and the carriers a 90 per cent completeness misses')
_lo = sorted(lohi(r)[0] for r in BEST.values())
_hi = sorted(lohi(r)[1] for r in BEST.values())
_ce = sorted(sum(lohi(r)) / 2 for r in BEST.values())
if DRIVE == 7:
    _lo = _lo[1:]
ck('B1 the lower edges of the summaries\' best windows span round 103\'s \\BenchTunedFreqLo--\\BenchTunedFreqHi',
   '%.0f' % _lo[0] == T('BenchTunedFreqLo') and '%.0f' % _lo[-1] == T('BenchTunedFreqHi') and len(_lo) == NSYS,
   'lower edges %.2f-%.2f, centres %.2f-%.2f, upper edges %.2f-%.2f over %d systems'
   % (_lo[0], _lo[-1], _ce[0], _ce[-1], _hi[0], _hi[-1], NSYS))
m('NtBestNuLo', '%.0f' % math.floor(_lo[0]))
m('NtBestNuHi', '%.0f' % math.ceil(_hi[-1]))
m('NtBestNuCenLo', '%.0f' % _ce[0])
m('NtBestNuCenHi', '%.0f' % _ce[-1])
_miss = (1.0 - COMPLETENESS) * NSYS
_missr = int(math.floor(_miss + 0.5))
if DRIVE == 8:
    _missr += 1
ck('B2 the carriers at their limit a 90 per cent completeness misses: (1 - 0.90) x the summaries\' systems, '
   'rounded half up, and the word is the number', abs(_missr - _miss) <= 0.5 and WORD[_missr] == word(_missr),
   '%.1f -> %d (%s) of %d' % (_miss, _missr, word(_missr), NSYS))
m('NtMissAtLim', '%d' % _missr)
m('NtMissAtLimWord', word(_missr))
m('NtMissAtLimExact', '%.1f' % _miss)
INFO['m1'] = dict(lo_edges=[_lo[0], _lo[-1]], hi_edges=[_hi[0], _hi[-1]], centres=[_ce[0], _ce[-1]],
                  miss=_miss)

# ================================================================== m1 sets
print('\nm1  the sets')
LED = J('ledger.json')['rows']
CH = J('chance_v414.json')


def lkey(eb, f):
    return (eb, round(float(f), 3))


_obs = {lkey(r['eb'], r['freq']) for r in CH['observed_rows']}
_tail = {lkey(t[1], t[2]) for t in CH['observed_tail']}
_un = [r for r in LED if not r['attributed']]
_unk = {lkey(r['eb'], r['freq']) for r in _un}
_qp = [r for r in _un if not r['dq']]
_tail_ck = set(sorted(_tail)[1:]) if DRIVE == 9 else _tail     # the drive perturbs the check, not the set
ck('S1 the unattributed crossings the clustering and recurrence tests run over are the census\'s unattributed '
   'crossings and the archival tail\'s, by membership, and the printed counts are those sets',
   _unk == _obs | _tail_ck and not (_obs & _tail_ck) and len(_obs) == int(T('CeObs')) and len(_tail_ck) == int(T('CeNTailCross'))
   and len(_qp) == int(T('QcNQP')) == int(T('MkUnattr')) == len(_un),
   '%d unattributed = %d census + %d tail; QcNQP %s MkUnattr %s' % (len(_un), len(_obs), len(_tail), T('QcNQP'),
                                                                  T('MkUnattr')))
RCC = J('recurcols_v411.json')
_tested = [r for r in _un if (RCC.get('%s|%.6f' % (r['eb'], r['freq'])) or {}).get('note') is None
           and RCC.get('%s|%.6f' % (r['eb'], r['freq']))]
_tc = [r for r in _tested if lkey(r['eb'], r['freq']) in _obs]
ck('S2 the recurrence test\'s read population is census_v412\'s \\RcNExclPoss, drawn from that same set',
   len(_tested) == int(T('RcNExclPoss')) and len(_un) - len(_tested) == int(T('RcNNoSep')) + int(T('RcNNoRepeat')),
   '%d read (%d census, %d tail); %d not tested' % (len(_tested), len(_tc), len(_tested) - len(_tc),
                                                   len(_un) - len(_tested)))
m('NtSetUnName', 'census and archival tail')
m('NtSetUnNotTested', '%d' % (len(_un) - len(_tested)))
m('NtSetUnNotTestedWord', word(len(_un) - len(_tested)))
m('NtSetUnReadCen', '%d' % len(_tc))

# the per-window catalogue's crossing rows against the census
LEDC = [r for r in LED if lkey(r['eb'], r['freq']) not in _tail]
assert len(LEDC) == int(T('CsNCross')), (len(LEDC), T('CsNCross'))


def win_of(eb, f):
    for r in CAT:
        if r['eb'] == eb and lohi(r)[0] - 1e-6 <= f <= lohi(r)[1] + 1e-6:
            return r
    return None


_lw = {id(win_of(r['eb'], r['freq'])) for r in LEDC if win_of(r['eb'], r['freq']) is not None}
XC = [r for r in CAT if r['crossing'] == 'True']
XCF = [r for r in XC if r['f_cross_GHz'] not in ('', None)]
_catonly = [r for r in XCF if id(r) not in _lw]
_both = [r for r in XCF if id(r) in _lw]
ck('S3 the per-window catalogue\'s crossing rows with a released peak (\\AppMNCrossF) are census crossings plus '
   'rows the census supersedes, and no census crossing is missing from them except where its window is not a '
   'catalogue crossing row', len(XCF) == int(T('AppMNCrossF')) and len(_both) + len(_catonly) == len(XCF)
   and (len(_catonly) > 0 if DRIVE != 10 else False),
   '%d = %d census + %d superseded (%s)' % (len(XCF), len(_both), len(_catonly),
                                            sorted({r['star_name'] for r in _catonly})))
m('NtCatXNCen', '%d' % len(_both))
m('NtCatXNSup', '%d' % len(_catonly))
m('NtCatXNSupStars', '%d' % len({r['system_id'] for r in _catonly}))
m('NtCenXNotCat', '%d' % (len(LEDC) - len(_both)))

# the tube occupancy over the census crossings alone, appm_v405's method (frozen mask, own-grid null)
_src = open(os.path.join(HERE, 'v342_calc.py')).read()
_i = _src.index('CAT_OLD = {')
CAT_OLD = eval(_src[_i + len('CAT_OLD = '):_src.index('}', _i) + 1])        # noqa: S307
_asrc = open(os.path.join(HERE, 'appm_v405.py')).read()
MASK_HALF = float(_asrc.split('MASK_HALF = ')[1].split()[0])
NMC_T = int(_asrc.split('NMC_SCAN = ')[1].split()[0])
C_KMS = 299792.458


def dvn(f):
    k = min(CAT_OLD, key=lambda q: abs(C_KMS * (f - CAT_OLD[q]) / CAT_OLD[q]))
    return C_KMS * (f - CAT_OLD[k]) / CAT_OLD[k]


GR, FC_ = [], []
for r in LEDC:
    w = win_of(r['eb'], r['freq'])
    lo, hi = lohi(w)
    cw = float(w['chanw_Hz']) / 1e9
    GR.append(lo + cw * np.arange(int(round((hi - lo) / cw)) + 1))
    FC_.append(float(r['freq']))
_tobs = sum(1 for f in FC_ if abs(dvn(f)) <= MASK_HALF)
RNG = np.random.default_rng(20261109)
_nin = np.array([sum(1 for g in GR if abs(dvn(g[RNG.integers(0, g.size)])) <= MASK_HALF) for _ in range(NMC_T)])
_tp = float(((_nin >= _tobs).sum() + 1) / (NMC_T + 1))
_tnull = float(_nin.mean())
# the catalogue figure reproduced by the same code on the catalogue's rows is the check that this is appm's test
_cobs = sum(1 for r in XCF if abs(dvn(float(r['f_cross_GHz']))) <= MASK_HALF)
if DRIVE == 11:
    _cobs += 1
ck('S4 the tube count, recomputed by appm_v405\'s method, reproduces \\AppMTubeObs on the catalogue rows, and over '
   'the census crossings alone is printed with its own null and p',
   _cobs == int(T('AppMTubeObs')) and _tobs <= _cobs + len(LEDC) and _tnull > 0,
   'catalogue %d (\\AppMTubeObs %s); census %d of %d against %.2f expected, p %.4g'
   % (_cobs, T('AppMTubeObs'), _tobs, len(LEDC), _tnull, _tp))
m('NtTubeCenObs', '%d' % _tobs)
m('NtTubeCenNull', '%.1f' % _tnull)
_ne = int(round(_tp * (NMC_T + 1))) - 1
if _ne == 0:
    _b = 1.0 / (NMC_T + 1)
    _e = int(math.floor(math.log10(_b)))
    m('NtTubeCenP', '$<%d\\times10^{%d}$' % (int(math.ceil(_b / 10.0 ** _e - 1e-12)), _e))
else:
    m('NtTubeCenP', '%.2g' % _tp)
INFO['tube_census'] = dict(n=len(LEDC), observed=_tobs, null_mean=_tnull, p=_tp, n_mc=NMC_T, seed=20261109,
                           catalogue_superseded=[(r['star_name'], r['eb'], r['f_cross_GHz']) for r in _catonly])

# ================================================================== m2
print('\nm2  the channel-response decomposition')
SR = J('strata_v411.json')['response']
_k = (0.25, 0.5, 0.25)
_kc, _ke = _k[1], _k[1] * 0.5 + _k[0] * 0.5          # carrier centred; carrier split equally over two channels
_km = 0.5 * (_kc + _ke)                              # linear in phase, so the phase mean is the midpoint
_rf = float(T('RpRespFac'))
_mg = float(T('RpMarginNinety'))
_ma = float(T('EirpNinetyMultA'))
_dep = SR['deposited_phase_mean'] if DRIVE != 12 else 0.42
ck('K1 the injection kernel leaves 0.5 / 0.375 / 0.4375 (centre / boundary / phase mean) in the peak channel, '
   'which the injections deposited; the response factor is its inverse and the printed product is the class factor',
   abs(SR['deposited_centre'] - _kc) < 1e-12 and abs(SR['deposited_edge'] - _ke) < 1e-12 and abs(_dep - _km) < 1e-4
   and abs(_rf - 1.0 / _dep) < 0.5 * 10 ** -(len(T('RpRespFac').split('.')[1]))
   and abs(round(_rf * _mg, 2) - _ma) < 1e-9,
   'kernel %.3f/%.3f/%.4f, deposited %.3f/%.3f/%.4f; %s x %s = %.4f against %s'
   % (_kc, _ke, _km, SR['deposited_centre'], SR['deposited_edge'], _dep, T('RpRespFac'), T('RpMarginNinety'),
      _rf * _mg, T('EirpNinetyMultA')))
ck('K2 the measured correlator response (\\HanBest, \\HanWorst) is the exact one, not the kernel, and it holds more '
   'of the carrier on a boundary than the kernel does',
   abs(float(T('HanWorst')) - SR['exact_edge']) < 0.005 and SR['exact_edge'] > _ke
   and abs(float(T('InjRespMean')) - SR['exact_phase_mean']) < 1e-4,
   'exact %.4f boundary, %.4f mean; kernel %.3f, %.4f' % (SR['exact_edge'], SR['exact_phase_mean'], _ke, _km))
m('NtKerEdge', '%.3f' % _ke)
m('NtKerToExact', '%.2f' % (_dep / SR['exact_phase_mean']))

# ================================================================== m6
print('\nm6  the calibration interval')
S11 = J('sens_r11.json')
_bf, _bd, _bc = float(T('BudFlux')), float(T('BudDistVis')), float(T('BudComb'))
_q2 = math.hypot(_bf, _bd)
ck('C1 the +-\\BudComb calibration interval is wider than the flux-scale specification alone (\\BudFlux) and is the '
   'quadrature of it with the distance/visibility term and a sampling term of at most a few per cent',
   (_bc if DRIVE != 13 else _bf) > _bf and _q2 <= _bc + 0.5 and math.sqrt(max(0.0, (_bc + 0.5) ** 2 - _q2 ** 2)) < 6,
   'sqrt(%.1f^2 + %.1f^2) = %.2f; printed %.0f; implied sampling term <= %.1f'
   % (_bf, _bd, _q2, _bc, math.sqrt(max(0.0, (_bc + 0.5) ** 2 - _q2 ** 2))))

# ================================================================== m7
print('\nm7  the switched best windows')
TS = J('tobs_r34.json')['windows']
_sw = [s for s in BEST if star_alias.designation(s).replace(' ', '~') in T('XwSwitchNames').split(', ')
       or star_alias.designation(s).replace(' ', '~') == T('XwSwitchNames')]
_cl = []
for s in _sw:
    b = BEST[s]
    xr = [r for r in CAT if r['system_id'] == s and r['search_class'] == 'A' and ae.limit_eligible(r, HERE)
          and '%s|%s|%s|%s' % (r['eb'], r['flo_GHz'], r['chanw_Hz'], r['star_name']) in TS]
    x = min(xr, key=lambda r: E[id(r)])
    fac = TS['%s|%s|%s|%s' % (x['eb'], x['flo_GHz'], x['chanw_Hz'], x['star_name'])]
    _cl.append((s, b, x, fac))
if DRIVE == 14:
    _cl = [(s, x, x, f) for s, b, x, f in _cl]
ck('W1 every switched system\'s tabulated limit refers to a window other than the one holding its crossing, the two '
   'print alike or not as the data say, and the crossing window was the best one before the reading',
   _cl and len(_cl) == int(T('XwNSwitch')) and all(b is not x and E[id(b)] < E[id(x)] for s, b, x, f in _cl),
   [(s, b['eb'], x['eb'], '%.4g' % E[id(b)], '%.4g' % E[id(x)]) for s, b, x, f in _cl])
if len(_cl) == 1:
    s, b, x, f = _cl[0]
    _fac = float(f.get('factor', 1.0)) if isinstance(f, dict) else 1.0
    m('NtSwBestEb', tt(b['eb']))
    m('NtSwBestGHz', '%.2f' % (sum(lohi(b)) / 2))
    m('NtSwBestLoGHz', '%.2f' % lohi(b)[0])
    m('NtSwBestHiGHz', '%.2f' % lohi(b)[1])
    m('NtSwBestChanKHz', '%.0f' % (float(b['chanw_Hz']) / 1e3))
    m('NtSwBestEirp', sci(E[id(b)]))
    m('NtSwCrossEb', tt(x['eb']))
    m('NtSwCrossGHz', '%.2f' % (sum(lohi(x)) / 2))
    m('NtSwCrossEirp', sci(E[id(x)]))
    m('NtSwCrossEirpTrig', sci(E[id(x)] / _fac))
    INFO['switch'] = dict(system=s, best=b['eb'], cross=x['eb'], best_e=E[id(b)], cross_e=E[id(x)], factor=_fac)

# ------------------------------------------------------------------ output
if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
if DRIVE is not None:
    print('misc_r35: drive %d passed every check -- it did NOT fire' % DRIVE)
    sys.exit(0)
with open(os.path.join(HERE, 'numbers/survey_numbers_round%d.tex' % ROUND), 'w') as fh:
    fh.write('%% GENERATED by misc_r35.py (round %d) -- do not hand-edit.\n' % ROUND)
    for k in sorted(OUT):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, OUT[k]))
json.dump(dict(generated_by='misc_r35.py', round=ROUND, **INFO), open(os.path.join(HERE, 'misc_r35.json'), 'w'),
          indent=1, sort_keys=True, default=str)
print('misc_r35: %d macros' % len(OUT))
