#!/usr/bin/env python3
r"""r1_r22.py -- round 972.  REFEREE 1's THREE VERIFICATIONS, AUDITED RATHER
THAN REPEATED.

R1-1  Does any statement describe all 405 Class A windows as drift-RESOLVING,
      when 391 satisfy the physical criterion and 14 do not?
R1-2  (1) Is the reported calibration uncertainty population-average or
      individual-window?  (2) Do the individual limits use a common
      transferred factor?  (3) Does any individual-system uncertainty present
      the pooled interval as an individual-window confidence interval?
R1-3  (1) Is every limit marked nominal where decorrelation is excluded?
      (2)(3) Do the best-window limits -- particularly those whose block
      exposes no phase record -- carry the same empirical support as the
      measured ones?  (5) Does any population-level conclusion treat the
      missing corrections as randomly distributed?

Round 21's `calib_REPORT.md` settled the neighbouring items R1-5 and R1-6.
This generator AUDITS that work rather than repeating it: every claim it
relies on is recomputed here from the tree's own records, and the one piece
of round 21 that never reached the manuscript is measured again from scratch.

Read-only on the paper tree.  Usage: r1_r22.py [--drive N]
★ ROUND RENUMBERED 96x -> 97x BY THE INTEGRATOR (v4.23).  `r22-edge` and
`r22-num` both claimed macro rounds 960-962 in their own queue files in the
same wave -- the race AGENT_RULES warns about and this project's fourth
double claim.  Edge keeps 960-962 (`edge_v423.py`, `proxb_v423.py`,
`epsx_v423.py`); this generator moved to 972.  `roundcollide.py` resolves the
round from the module-level constant below, so the renumber is that line and
the manuscript's \input.
"""
import collections
import glob
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ v4.23: ROUND 20'S FALLBACK PATTERN, not a version pin.  This file was
# written outside the tree and read the frozen previous version; once it is
# adopted into a version directory that directory is both the input and the
# output, like every other generator here.  A bare absolute pin broke the
# build in round 20 when the predecessor was deleted, and `cleanregen.py`
# cannot see a cross-version dependency because the predecessor is always
# there while it runs.
PAPER = (HERE if os.path.exists(os.path.join(HERE, 'ledger.json'))
                else '/workspace/SETI/paper_20pc/v4.22')
ROUND = 972
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
SFX = '' if DRIVE is None else '_drive%d' % DRIVE

MACROS, FAIL = [], []


def m(k, v):
    assert not any(x.startswith('\\newcommand{\\%s}' % k) for x in MACROS), k
    MACROS.append('\\newcommand{\\%s}{%s}' % (k, v))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label)
    print('  %-66s %s  %s' % (label[:66], 'PASS' if ok else 'FAIL', detail))


_TEX = {}
for _f in sorted(glob.glob(os.path.join(PAPER, 'survey_numbers*.tex'))):
    for _ln in open(_f):
        _mm = re.search(r'\\(?:new|renew)command\{\\([A-Za-z]+)\}\{(.*)\}\s*$',
                        _ln)
        if _mm:
            _TEX[_mm.group(1)] = _mm.group(2)


def texval(n):
    return _TEX[n]


sys.path.insert(0, PAPER)
import adopted_e90 as ae                                   # noqa: E402
import decor_r13                                           # noqa: E402

ROWS = ae.catalogue(PAPER)
E90 = ae.per_window(ROWS, PAPER)
CLSA = [r for r in ROWS if r['search_class'] == 'A']
# ★ A system's best window is its best ELIGIBLE window: one every channel of
# which lies inside the attribution mask constrains nothing (Sec.
# \ref{sec:lines}) and cannot be the window a limit is read from.  The rule
# lives in `adopted_e90`, so every generator that forms a per-system limit
# applies the same one.
BEST = {}
for r in CLSA:
    if not ae.limit_eligible(r, PAPER):
        continue
    s = r['system_id']
    if s not in BEST or E90[id(r)] < E90[id(BEST[s])]:
        BEST[s] = r

# =====================================================================
# 1.  R1-1 -- THE 405 AND THE 391
# =====================================================================
print('\n1  R1-1: where the 405 is named, is the 391 named with it')
NA = int(texval('NWinA'))
NOK = int(texval('EdrNWinA'))
NLO = int(texval('EtaDriftALo'))
if DRIVE == 1:                      # A1: a partition that does not close
    NLO += 1
ck('A1 the two subsets of the carrier search close on its own size, so the '
   'distinction is a partition and not a second population',
   NOK + NLO == NA and NOK == int(texval('EtaDriftAOk'))
   and NA == len(CLSA),
   '%d + %d == %d, and the catalogue holds %d Class A windows'
   % (NOK, NLO, NA, len(CLSA)))
# ★ A PROSE CLAUSE, AND DELIBERATELY SO.  The defect R1-1 reports is not a
# wrong number: every number is right.  It is that the two numbers do not
# appear together where the experiment is introduced, so a reader meets the
# 405 as the drift-resolving set.  The invariant pinned here is therefore
# "wherever the carrier search is INTRODUCED, both counts appear" -- an
# invariant, not today's value of either.
#: ★★ THE ABSTRACT LEAVES THIS LIST ON THE SAME REFEREE'S LATER INSTRUCTION
#: (R1 S3 of the final round: the abstract "does not need the exact number of
#: drift-resolving windows").  The invariant is unchanged where the search is
#: introduced in full -- Sec. 3, Sec. 4 and the conclusions -- and the
#: abstract is held by the opposite implication below: it may not quote the
#: drift-resolving count as if it were the size of the search.
INTRO = ('05_results.tex', '07_conclusions.tex', '03_sample.tex')
seen = {}
for f in INTRO:
    t = open(os.path.join(PAPER, 'sections', f)).read()
    seen[f] = ('\\NWinA' in t, '\\EdrNWinA' in t or '\\EtaDriftAOk' in t)
if DRIVE == 2:               # A2: a section that names the size and not the
    #                          drift-resolving subset.  ★ THE DRIVE WAS
    #                          WRITTEN IN THE OTHER DIRECTION, because the
    #                          clause was expected to fail at baseline; with
    #                          the abstract clause landed it passes, so a
    #                          drive that makes every section satisfy it
    #                          demonstrates nothing.  It now removes the
    #                          mention, which is the perturbation the clause
    #                          exists to catch.
    seen = {f: (True, False) for f in seen}
# ★ WRITTEN AS THE GATE THE BUILD SHOULD CARRY and not as a description of
# today's text.  The clause R1-1(3) asks for costs four words, and the
# abstract measures 235 words against the 250-word ceiling `abswords.py`
# enforces as a referee requirement, so there is room for it and it is in:
# `\EdrNWinA{} of them drift-resolving`.  ►► THE PASS THAT TAKES THE
# ABSTRACT TO 200 WORDS MUST KEEP A CLAUSE CITING `\EdrNWinA` OR THIS CLAUSE
# FAILS THE BUILD -- which is the point of it.
_bad = [f for f, (a, b) in seen.items() if a and not b]
_abs_t = open(os.path.join(PAPER, 'sections', 'abstract.tex')).read()
if DRIVE == 14:
    #: the subset quoted in the abstract in place of the size.
    _abs_t = _abs_t.replace('\\NWinA{', '\\EdrNWinA{')
#: the abstract may give the size alone, or both; never the subset alone.
if ('\\EdrNWinA' in _abs_t or '\\EtaDriftAOk' in _abs_t) \
        and '\\NWinA{' not in _abs_t:
    _bad.append('abstract.tex (subset without the size)')
ck('A2 every section that introduces the carrier search by its size also '
   'states how many of those windows resolve a drift',
   not _bad, 'missing in: %s (checked in %s)'
   % (', '.join(_bad) or 'none', ', '.join(INTRO)))
m('NgNWinADrift', '%d' % NOK)
m('NgNWinANoDrift', '%d' % NLO)

# =====================================================================
# 2.  R1-2 -- WHAT THE QUOTED UNCERTAINTY IS, AND WHAT THE LIMITS USE
# =====================================================================
print('\n2  R1-2: the calibration uncertainty and the transfer')
SENS = json.load(open(os.path.join(PAPER, 'sens_r11.json')))
MULT_A = float(SENS['headline']['mult_a'])
# (2) ONE FACTOR, TRANSFERRED.  Every Class A window's limit is the SAME
# class multiplier on its own nominal trigger power, divided by its own three
# measured retentions.  Recomputed here without using `adopted_e90`'s own
# arithmetic for the ratio: the ratio of the adopted value to the nominal one
# must take only as many distinct values as there are retention combinations,
# and its minimum over the class must be the multiplier itself.
RAT = [E90[id(r)] / float(r['eirp_nominal_W']) for r in CLSA]
_rmin = min(RAT)
if DRIVE == 3:                      # A3: a per-window calibration factor
    _rmin = MULT_A * 0.5
ck('A3 every individual Class A limit carries the SAME class factor -- the '
   'retentions are the only thing that differs between windows, and they '
   'can only raise a limit',
   _rmin >= MULT_A * (1 - 1e-9) and _rmin < MULT_A * 1.001,
   'smallest adopted/nominal ratio %.6f against the class factor %.6f, '
   'largest %.3f over %d windows' % (_rmin, MULT_A, max(RAT), len(RAT)))
# (1) THE QUOTED INTERVAL IS A POPULATION QUANTITY.  x0.89-x1.11 is the
# calibration of the class factor; the per-window dispersion is x0.80-x1.58,
# which is wider, and the paper must quote the second against an individual
# window.  Both read from the campaign record, not from the prose.
FAC_LO, FAC_HI = float(texval('SensFacLo')), float(texval('SensFacHi'))
DSP_LO, DSP_HI = float(texval('SmcDispLo')), float(texval('SmcDispHi'))
IND_LO, IND_HI = float(texval('SensIndivLo')), float(texval('SensIndivHi'))
if DRIVE == 4:                      # A4: the two intervals swapped
    FAC_LO, FAC_HI = DSP_LO, DSP_HI
ck('A4 the published calibration interval is narrower than the measured '
   'window-to-window dispersion, so the two are different quantities and '
   'the narrower one cannot be an individual window\'s error',
   (FAC_HI - FAC_LO) < (DSP_HI - DSP_LO)
   and abs(DSP_LO - IND_LO / MULT_A) < 0.005
   and abs(DSP_HI - IND_HI / MULT_A) < 0.005,
   'calibration x%.2f-%.2f against dispersion x%.2f-%.2f, the latter being '
   'the 49 windows\' own range %.2f-%.2f over the adopted %.2f'
   % (FAC_LO, FAC_HI, DSP_LO, DSP_HI, IND_LO, IND_HI, MULT_A))
# (5) THE DISPERSION IS MEASURED, NOT ADDED.  It is the range of the 49
# injected windows' own ninety-per-cent points and nothing else.
PW = SENS['per_window']
_pts = sorted(float(v['trig']) for v in PW.values())
if DRIVE == 5:                      # A5: an uncertainty with no measurement
    _pts = [x * 1.2 for x in _pts]
ck('A5 and that dispersion is the 49 measured points themselves, so no '
   'uncertainty has been invented to carry the transfer',
   abs(_pts[0] - IND_LO) < 0.011 and abs(_pts[-1] - IND_HI) < 0.011
   and len(_pts) == int(texval('SensNInj')),
   '%d measured points spanning %.2f-%.2f P_trig against the published '
   '%.2f-%.2f' % (len(_pts), _pts[0], _pts[-1], IND_LO, IND_HI))
# ★★★ THE ONE THING ROUND 21 MEASURED THAT NEVER REACHED THE MANUSCRIPT,
# RE-MEASURED HERE FROM THE CAMPAIGN RECORD: configurations the population
# holds and the campaign never injected into.  This is R1-2's own concern --
# "each system's best window may not be representative of the injected
# subset" -- in its sharpest form.
# ★★★★ r27 ROW 1.  THE SET WAS DEFINED AT BLOCK LEVEL AND ON TWO AXES.
# `SENS['ring']` is keyed by tag, so stripping the spw gave the 50 Class A
# windows of the 35 blocks that carry an injection, not the 49 that were
# injected -- a check that could not see the divergence it exists to catch.
# The set is now the deposit's own per-window flag, which `sens_r18.py` X2
# ties one-to-one to the campaign record.  And R1 1.1 asks for five axes,
# not two: band, channel width, array AND ITS CONFIGURATION, integration
# time and block duration.  Block duration is kept although it puts no
# window out on its own, because the referee names it and a reader must see
# that it was tested.  THE NOISE IS DELIBERATELY NOT AN AXIS: what is
# transferred is a multiple of the window's OWN trigger power, so the noise
# level cancels out of it (clause A3 below asserts exactly that), and the
# four quietest windows are 1.4x beyond one end of a range spanning 215x.
INJ_ROWS = [r for r in CLSA if r['p90_basis'] == 'injected']
_ARCH = json.load(open(os.path.join(PAPER, 'archive_meta_v381.json')))['ebs']
_arr = lambda r: _ARCH[r['eb']]['array']
_res = lambda r: float(_ARCH[r['eb']]['s_resolution_arcsec'])
_BDUR = collections.defaultdict(float)
for _r in ROWS:
    _BDUR[_r['eb']] = max(_BDUR[_r['eb']], float(_r['on_source_s']))
B_INJ = {r['band'] for r in INJ_ROWS}
C_INJ = {round(float(r['chanw_Hz'])) for r in INJ_ROWS}
A_INJ = {_arr(r) for r in INJ_ROWS}
_rng = lambda f: (min(f(r) for r in INJ_ROWS), max(f(r) for r in INJ_ROWS))
T_INJ = _rng(lambda r: float(r['on_source_s']))
D_INJ = _rng(lambda r: _BDUR[r['eb']])
# the synthesised beam is only comparable within an array, so its support is
R_INJ = {a: (min(_res(r) for r in INJ_ROWS if _arr(r) == a),
             max(_res(r) for r in INJ_ROWS if _arr(r) == a))
         for a in A_INJ}


def _outside(r):
    """the axes on which this window leaves the injected range"""
    o = []
    if r['band'] not in B_INJ:
        o.append('band')
    if round(float(r['chanw_Hz'])) not in C_INJ:
        o.append('channel width')
    if _arr(r) not in A_INJ:
        o.append('array')
    elif not R_INJ[_arr(r)][0] <= _res(r) <= R_INJ[_arr(r)][1]:
        o.append('configuration')
    if not T_INJ[0] <= float(r['on_source_s']) <= T_INJ[1]:
        o.append('integration time')
    if not D_INJ[0] <= _BDUR[r['eb']] <= D_INJ[1]:
        o.append('block duration')
    return o


EXTRAP = [r for r in CLSA if r not in INJ_ROWS and _outside(r)]
INTERP = [r for r in CLSA if r not in INJ_ROWS and not _outside(r)]
EX_SYS = [s for s, r in BEST.items() if r in EXTRAP]
if DRIVE == 6:                      # A6: a campaign covering every setting
    EXTRAP, EX_SYS = [], []
ck('A6 some configurations of the population hold no injected window at '
   'all, and some systems take their headline limit from one, so for those '
   'the transfer crosses a configuration boundary',
   len(EXTRAP) > 0 and len(EX_SYS) > 0,
   '%d of %d Class A windows in %d such configurations; %d systems, the '
   'deepest being %s at %.2e W'
   % (len(EXTRAP), len(CLSA),
      len({(r['band'], round(float(r['chanw_Hz']))) for r in EXTRAP}),
      len(EX_SYS),
      min(EX_SYS, key=lambda s: E90[id(BEST[s])]) if EX_SYS else '-',
      min(E90[id(BEST[s])] for s in EX_SYS) if EX_SYS else -1))
_deep = min(BEST, key=lambda s: E90[id(BEST[s])])
# ★★★★ THIS CLAUSE USED TO ASSERT THE OPPOSITE, AND IT WAS RIGHT TO AT THE
# TIME.  The deepest limit in the survey was a 15.26 kHz window, a
# channelisation the injection campaign never covered, so its completeness
# was carried across a configuration boundary and the paper said so.  That
# window lies entirely inside the attribution mask and no longer supplies a
# limit; the deepest limit now comes from a band and channelisation the
# campaign did cover, so the support is better and the sentence that said
# otherwise has gone.  What is asserted is the fact either way -- which
# configuration the deepest limit is in, and whether an injected window
# shares it -- so the clause still fails if the answer changes again.
_deep_extrap = _deep in EX_SYS
_deep_cfg = (BEST[_deep]['band'], round(float(BEST[_deep]['chanw_Hz'])))
_deep_inj = sum(1 for r in INJ_ROWS
                if (r['band'], round(float(r['chanw_Hz']))) == _deep_cfg)
if DRIVE == 7:                      # A7: the deepest limit extrapolated again
    _deep_extrap, _deep_inj = True, 0
ck('A7 the deepest limit in the survey is supported by injections in its '
   'own configuration, so it is not one of the extrapolated ones, and the '
   'count of injected windows that share its configuration says so',
   (not _deep_extrap) and _deep_inj > 0,
   'deepest system %s at %.2e W, band %s, %.0f kHz channels; %d injected '
   'window(s) in that configuration; extrapolated %s'
   % (_deep, E90[id(BEST[_deep])], BEST[_deep]['band'],
      float(BEST[_deep]['chanw_Hz']) / 1e3, _deep_inj, _deep_extrap))
m('NgDeepNInjCfg', '%d' % _deep_inj)


def tname(s):
    #: the house rendering, the same substitutions `confirm_r19.py::tname`
    #: makes, so two tables cannot spell one star two ways
    t = BEST[s]['star_name'].split(' Gaia')[0].strip()
    t = re.sub(r'^HD(\d)', r'HD \1', t)
    t = re.sub(r'^HIP(\d)', r'HIP \1', t)
    t = t.replace('bet Pic', r'$\beta$~Pic').replace('eta Crv', r'$\eta$~Crv')
    t = t.replace('CP-72', 'CP$-$72').replace('CD-57', 'CD$-$57')
    return t.replace(' ', '~')


m('NgNExtrapWin', '%d' % len(EXTRAP))
m('NgNInterpWin', '%d' % len(INTERP))
m('NgNExtrapSys', '%d' % len(EX_SYS))
_exn = sorted(tname(s) for s in EX_SYS)
m('NgExtrapSys', (', '.join(_exn[:-1]) + ' and ' + _exn[-1]) if len(_exn) > 1
  else (_exn[0] if _exn else 'none'))
m('NgNMeasSysChk', '%d' % sum(1 for s, r in BEST.items() if r in INJ_ROWS))

# ---- S3: THE CARDINAL AND THE NOUN IT GOVERNS, GENERATED TOGETHER
# ★★★ `\NgNExtrapSys` IS 1 IN THIS BUILD AND BOTH PROSE SITES WERE WRITTEN
# FOR A PLURAL, so the shipped page read "1 systems take their best window
# from one" in S4.1 and "for the 1 systems whose best window lies in a band
# ..." in Appendix P.  Nothing could see it: the macro is right, the value is
# right, the sentence parses.  This is `prose_v412`'s P8/P8b family -- a
# generated cardinal that governs a noun needs the same treatment as one
# that opens a sentence -- so the noun and the whole agreeing sub-clause are
# generated from the count here, next to the count, and A13 below holds them
# together.  Written as English for any value, including none.
_NX = len(EX_SYS)
NG_NOUN = 'system' if _NX == 1 else 'systems'
NG_TAKE_SG = (r'\NgNExtrapSys{} system takes its headline limit from one of them')
NG_TAKE_PL = (r'\NgNExtrapSys{} systems take their headline limit from one of them')
NG_TAKE_NONE = (r'no system takes its best window from one')
NG_TAKE = ({0: NG_TAKE_NONE}.get(_NX)
           or (NG_TAKE_SG if _NX == 1 else NG_TAKE_PL))
# ★ The prose half of the same defect: a typed noun beside the macro is the
# same error one edit later, so the sites are required to cite the generated
# noun rather than to spell one.
NG_SITES = ('05_results.tex', 'app_P_persys.tex')
_ngtxt = {f: open(os.path.join(PAPER, 'sections', f)).read() for f in NG_SITES}
if DRIVE == 12:                     # A13: the noun written for the other size
    NG_NOUN = 'systems' if _NX == 1 else 'system'
    NG_TAKE = NG_TAKE_PL if NG_TAKE is NG_TAKE_SG else NG_TAKE_SG
if DRIVE == 13:                     # A13: a typed plural beside the cardinal
    _ngtxt['05_results.tex'] += '\n\\NgNExtrapSys{} systems take their best\n'
_typed = sorted(f for f, t in _ngtxt.items()
                if re.search(r'\\NgNExtrapSys\{\}\s+(system|systems)\b',
                             re.sub(r'\s+', ' ', t)))
ck('A13 the noun the extrapolated-system count governs is generated from '
   'that count and never typed beside it, so the sentence is English at any '
   'value of the count',
   NG_NOUN == ('system' if _NX == 1 else 'systems')
   and (NG_TAKE is NG_TAKE_SG) == (_NX == 1)
   and (NG_TAKE is NG_TAKE_NONE) == (_NX == 0)
   and ('their headline limit' in NG_TAKE) == (_NX > 1)
   and not _typed,
   '%d -> %r / %s; typed noun beside the macro in: %s'
   % (_NX, NG_NOUN,
      'none' if NG_TAKE is NG_TAKE_NONE
      else 'singular' if NG_TAKE is NG_TAKE_SG else 'plural',
      ', '.join(_typed) or 'nowhere'))
m('NgExtrapSysNoun', NG_NOUN)
m('NgExtrapTakeClause', NG_TAKE)

# =====================================================================
# 3.  R1-3 -- NOMINAL LIMITS AND THE BLOCKS WITH NO PHASE RECORD
# =====================================================================
print('\n3  R1-3: the decorrelation behind each system\'s own best window')
M = decor_r13.Matcher(PAPER)
BASIS, DEC = {}, {}
for s, r in BEST.items():
    d, b, _hi = M.correction(r)
    BASIS[s], DEC[s] = b, d
CNT = collections.Counter(BASIS.values())
ORDER = sorted(BEST, key=lambda s: E90[id(BEST[s])])
NDEEP = 10
DEEP = ORDER[:NDEEP]
n_meas_deep = sum(1 for s in DEEP if BASIS[s] == 'measured')
if DRIVE == 8:                      # A8: every best window measured
    CNT = collections.Counter({'measured': len(BEST)})
    n_meas_deep = NDEEP
ck('A8 a majority of the systems take their headline limit from a block '
   'whose delivery exposes no phase record, so for them the decorrelation '
   'column is imputed and not measured',
   CNT['matched'] > CNT['measured'],
   'measured %d, imputed %d, none %d of %d systems'
   % (CNT['measured'], CNT['matched'], CNT['none'], len(BEST)))
ck('A9 and the deepest limits are no better supported than the rest: of the '
   'ten deepest, fewer than half carry a measured correction',
   n_meas_deep <= NDEEP // 2,
   '%d of the %d deepest measured, %d imputed, %d with no estimate'
   % (n_meas_deep, NDEEP,
      sum(1 for s in DEEP if BASIS[s] == 'matched'),
      sum(1 for s in DEEP if BASIS[s] == 'none')))
# the medians, by basis, so that a pooled median is never quoted as if the
# whole of it were measured
MED = {b: st.median([DEC[s] for s in BEST if BASIS[s] == b])
       for b in ('measured', 'matched')}
POOL = st.median([DEC[s] for s in BEST if DEC[s] is not None])
if DRIVE == 9:                      # A10: a pooled median outside both
    POOL = 9.0
ck('A10 the pooled per-system median the text quotes lies between the two, '
   'so it is a mixture and must be labelled one',
   min(MED.values()) <= POOL <= max(MED.values())
   and abs(100 * POOL - float(texval('NmDecSysMedPct'))) < 0.6,
   'measured %.1f per cent, imputed %.1f, pooled %.1f against a published %s'
   % (100 * MED['measured'], 100 * MED['matched'], 100 * POOL,
      texval('NmDecSysMedPct')))
# the table's own marking, checked against this count rather than assumed
TAB = open(os.path.join(PAPER, 'tab_persys_r17.tex')).read()
NSTAR = TAB.count('$^{*}$')
NDAG = TAB.count('$^{\\dagger}$')
if DRIVE == 10:                     # A11: a table that marks nothing
    NSTAR = 0
ck('A11 and Table F1 marks exactly those systems, so the reader can see '
   'which limits rest on an imputed correction',
   NSTAR == CNT['matched'] and NDAG == int(texval('SmcNMeasSys')),
   '%d starred rows against %d imputed; %d daggered against %s injected'
   % (NSTAR, CNT['matched'], NDAG, texval('SmcNMeasSys')))
m('NgNDecMeasSys', '%d' % CNT['measured'])
m('NgNDecImpSys', '%d' % CNT['matched'])
m('NgNDecNoneSys', '%d' % CNT['none'])
m('NgDecMeasMedPct', '%.0f' % (100 * MED['measured']))
m('NgDecImpMedPct', '%.0f' % (100 * MED['matched']))
m('NgNDeep', '%d' % NDEEP)
m('NgNDeepMeas', '%d' % n_meas_deep)
m('NgNDeepImp', '%d' % sum(1 for s in DEEP if BASIS[s] == 'matched'))

# ---- R2-8's two star counts, by the class of the star's own deepest window
_bystar = {}
for r in ROWS:
    k = r['star_name']
    if k not in _bystar or E90[id(r)] < E90[id(_bystar[k])]:
        _bystar[k] = r
NBONLY = sum(1 for r in _bystar.values() if r['search_class'] == 'B')
NAONLY = sum(1 for r in _bystar.values() if r['search_class'] == 'A')
_cover = collections.defaultdict(bool)
for r in ROWS:
    _cover[r['star_name']] |= r['search_class'] == 'A'
if DRIVE == 11:                     # A12: a star plotted in the wrong class
    NBONLY += 1
ck('A12 the class of a star\'s own deepest window is the class of its '
   'coverage for every star, so one symbol per star can carry both',
   NBONLY == sum(1 for k, v in _cover.items() if not v)
   and NAONLY == sum(1 for k, v in _cover.items() if v)
   and NBONLY + NAONLY == int(texval('NStars')),
   '%d stars carrier-searched and %d coarse-only, of %s'
   % (NAONLY, NBONLY, texval('NStars')))
m('NgNStarA', '%d' % NAONLY)
m('NgNDecBOnly', '%d' % NBONLY)

out = dict(drive=DRIVE,
           r1_1=dict(n_a=NA, n_drift=NOK, n_nodrift=NLO,
                     sections_missing=_bad),
           r1_2=dict(mult_a=MULT_A, ratio_min=min(RAT), ratio_max=max(RAT),
                     calib=[FAC_LO, FAC_HI], dispersion=[DSP_LO, DSP_HI],
                     n_extrap_win=len(EXTRAP),
                     extrap_systems=[tname(s) for s in EX_SYS],  # house rendering
                     deepest_system=tname(_deep)),
           r1_3=dict(basis=dict(CNT), med_measured=MED['measured'],
                     med_imputed=MED['matched'], med_pooled=POOL,
                     deepest_basis=[(tname(s), BASIS[s]) for s in DEEP],
                     n_star=NSTAR, n_dagger=NDAG),
           macros={x.split('{')[1].strip('}\\'): x.split('{')[-1].rstrip('}\n')
                   for x in MACROS})
json.dump(out, open(os.path.join(HERE, 'r1_r22%s.json' % SFX), 'w'),
          indent=1, sort_keys=True, default=str)
if DRIVE is None:
    with open(os.path.join(HERE, 'survey_numbers_round%d.tex' % ROUND),
              'w') as fh:
        fh.write('%% GENERATED by r1_r22.py (round %d) -- do not hand-edit.\n' % ROUND)
        fh.write('\n'.join(sorted(MACROS)) + '\n')
print('\nassertions failed: %d %s' % (len(FAIL), FAIL))
# ★★★★ v4.26, Ruling 7.  THIS SUITE USED TO COLLECT ITS FAILURES AND THEN
# EXIT 0, AND `make_all.sh` RAN IT WITH STDOUT TO /dev/null.  Three suites in
# this build were written that way -- `num_r22.py`, `r1_r22.py` and
# `recurinj_r19.py` -- so three sets of checks written to answer referee items
# could not fail the build, and one of them (num_r22's B5) had been failing on
# the shipped paper for two versions with a wrong digit on the page.  A gate
# that cannot fail is not a gate; it is a comment that takes CPU.
if FAIL:
    raise SystemExit(1)

