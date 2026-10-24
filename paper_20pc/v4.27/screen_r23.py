#!/usr/bin/env python3
r"""screen_r23.py -- round 980 -> survey_numbers_round980.tex, screen_r23.json.

THREE MEASUREMENTS, ONE GENERATOR.  Owned by r23-screen; nothing here is typed.

(1) THE TELLURIC SCREEN AT A FIXED RADIUS OF TWO SYSTEM-TEMPERATURE CHANNELS.
    Appendix B states that no crossing lies within 25 MHz of a catalogued
    atmospheric transition, against the 31.25 MHz resolution at which the
    system temperature is measured.  ★★ THAT 25 IS NOT A RADIUS.  It is
    `'%.0f' % off.min()` in `calib_r15.py`: the smallest topocentric offset
    any crossing actually has, rounded.  The sentence is therefore true by
    construction for any data set whatever, and it is smaller than the
    quantity it claims to exclude, because an interpolated-Tsys residual
    occupies at least one Tsys channel.  Here the radius is fixed FIRST, at
    two Tsys channels read from the frozen specification, and the count is
    then measured.  Both numbers are published: how many crossings lie inside
    it, and the full list within 300 MHz with its topocentric offset, because
    the paper quotes crossing frequencies in the stellar frame and a telluric
    coincidence lives in the topocentric one.

(2) THE IMAGE SIDEBAND, OVER WINDOWS AND NOT OVER CROSSINGS.  Appendix E
    screens the unattributed crossings for image leakage and then dismisses
    the resolved lines with one clause -- that the spectral baseline removes
    them.  It does not: the baseline is a per-integration median along
    frequency, which removes a channel-independent level and nothing else,
    and the survey's own positive control is a CO line resolved across tens
    of channels at a statistic far above the trigger.  So the clause is
    replaced by a measurement over every Class A window: reflect the window
    about the interval its own block's windows allow for the first local
    oscillator, ask whether the image band so obtained covers a CO
    isotopologue transition at the star's velocity or at rest in the local
    standard of rest, and -- where it does -- ask whether a crossing lies at
    the image position.

(3) THE RESPONSE OF THE SEARCH FILTER TO A FEATURE N CHANNELS WIDE, measured
    on the statistic as Eq. 1 defines it rather than asserted.  The referee
    offers sqrt(N); the filter gives N, and the two differ because sqrt(N) is
    the penalty an optimally matched filter pays for spreading a fixed power
    over N channels while N is the penalty THIS filter pays, which reads one
    channel per integration.  Measured, reported, and the smaller of the two
    is not written into the paper.

INPUTS -- all read, none typed.
  per_target_results_v3.99.csv        the released per-window catalogue
  maskframe_v411.json                 the 56 census crossings, f_topo + frame
  r11inputs/events/cross_holdout.json the 8 hold-out crossings
  ledger.json                         the adopted attribution flag
  r15inputs/calib/jpl_c0*.cat         the JPL catalogue (O3, H2O, O2)
  r15inputs/calib/calspec_r15.json    Tsys resolution, atmosphere temperature
  r15inputs/losdir_r15.json           sky position and radial velocity per star
  r15inputs/cells/cells_extract_result.json   control maxima, with channels
  maskframe_v411 (module)             the frame chain and the frozen mask
  calib_r15 (module)                  the telluric line selection

ASSERTIONS (each driven to fail on its own, --drive 1..15)
  S1  the telluric radius is the frozen specification's own Tsys resolution
      times two, and is LARGER than the offset the paper currently quotes.
  S2  the line list reproduces the two strong water lines the search range
      contains at the frequencies the catalogue gives, and the selection is
      not vacuous (it omits catalogued transitions).
  S3  the crossing set read here is the published census plus the published
      hold-out, and every census crossing carries a topocentric frequency.
  S4  the HD 69830 case is decided on the frame chain's own numbers: its
      stellar-frame frequency is reproduced from its topocentric one with the
      block's own barycentric term and the star's catalogued velocity.
  S5  the offsets are topocentric: computing them in the stellar frame moves
      the HD 69830 offset by more than the radius, which is why the paper's
      stellar-frame quoting hides the coincidence.
  S6  the count inside the radius partitions into attributed and unattributed
      and the unattributed ones are named.
  S7  the control side is screened on the same radius and the same frame, and
      the rebuilt channel axis reproduces every stored in-mask flag -- the
      channel-reversal guard, without which this is a reversal defect.
  S8  every Class A window admits a local oscillator consistent with its own
      block's windows, and the image band never overlaps the window itself.
  S9  the image screen is not vacuous: some Class A window's image band does
      cover a CO isotopologue transition.
  S10 the window image screen keys on position: a crossing is matched to an
      image position by frequency inside the same window, never by a name.
  S11 the N-channel response of Eq. 1 scales as N and not as sqrt(N), with
      the measured exponent published.
  S12 the sqrt(N) alternative is demonstrated to be the matched-filter
      exponent on the same data, so the two are distinguished by measurement.
  S13 every unattributed crossing at an image position is named and held to
      the same leakage standard as the frequency screen: its parent's own
      frequency was observed in the same block and is too faint there for a
      leak at the specified rejection to account for the crossing.

Usage: screen_r23.py [--paper DIR] [--out DIR] [--drive N] [--selftest]
"""
import bisect
import collections
import csv
import importlib.util
import json
import math
import os
import re
import sys

import numpy as np

ROUND = 980
C = 299792.458

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = HERE
OUTDIR = HERE
DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--paper':
        PAPER = sys.argv[_i + 1]
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
#: ★ D36: a drive writes its own path.  The suffix follows the FLAG, not the
#: perturbation, so `--drive 0` is "no perturbation and no production path".
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(OUTDIR, 'screen_r23%s.json' % SUF)

sys.path.insert(0, PAPER)
import maskframe_v411 as mf                                     # noqa: E402
import star_alias as sa                                         # noqa: E402


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name,
                                                  os.path.join(PAPER, path))
    m_ = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m_)
    return m_


c15 = _mod('c15_r23', 'calib_r15.py')

MACROS, FAIL = [], []
R = {}


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may hold letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), \
        name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-62s %s  %s' % (label[:62], 'PASS' if ok else 'FAIL', detail))


def tex(name):
    import glob
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^{}]*)\}\s*$'
                     % name)
    hit = None
    for p in sorted(glob.glob(os.path.join(PAPER, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.search(line.strip())
            if mm and mm.group(1) != '':
                hit = mm.group(1)
    if hit is None:
        raise KeyError(name)
    return hit


print('screen_r23 round %d%s' % (ROUND, '' if DRIVE is None
                                 else ' (drive %d)' % DRIVE))

# =====================================================================
# inputs
# =====================================================================
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
IA = [i for i, r in enumerate(CAT) if r['search_class'] == 'A']
MFR = json.load(open(os.path.join(PAPER, 'maskframe_v411.json')))['rows']
HOL = json.load(open(os.path.join(PAPER, 'r11inputs', 'events',
                                  'cross_holdout.json')))
LEDG = json.load(open(os.path.join(PAPER, 'ledger.json')))['rows']
SPEC = json.load(open(os.path.join(PAPER, 'r15inputs', 'calib',
                                   'calspec_r15.json')))
LOS = json.load(open(os.path.join(PAPER, 'r15inputs', 'losdir_r15.json')))
CELLS = json.load(open(os.path.join(
    PAPER, 'r15inputs', 'cells', 'cells_extract_result.json')))['windows']
#: ★ THE COUNT AND THE EXPECTATION ARE NOT MINE TO PUBLISH.  `chance_v414.py`
#: owns the unattributed count and the chance expectation and applies this
#: same screen itself, on the mask that actually attributes; what this
#: generator does is rebuild the screen independently, from the catalogue and
#: the ledger, and require the two to agree BEFORE and AFTER it -- which is a
#: check that can fail, where printing a second copy of the same number under
#: a second macro name is only a way of disagreeing with oneself in public.
CHANCE = json.load(open(os.path.join(PAPER, 'chance_v414.json')))['telluric']

TRIG = float(tex('StageNullTrig'))
HALF = mf.MASK_HALF_KMS

# =====================================================================
# (1a) THE RADIUS, FIXED BEFORE ANYTHING IS COUNTED
# =====================================================================
TSYS_RES = float(SPEC['tsys_resolution_MHz'])
N_TSYS_CHAN = 2
RAD = N_TSYS_CHAN * TSYS_RES
if DRIVE == 1:
    RAD = float(tex('TlOffMin'))        # the published offset back as a radius
PUB = float(tex('TlOffMin'))
ck('S1 the radius is two Tsys channels of the frozen specification and is '
   'larger than the offset the paper quotes as its screen',
   abs(RAD - N_TSYS_CHAN * TSYS_RES) < 1e-9 and RAD > PUB,
   '%.2f MHz against %.0f MHz published, Tsys resolution %.2f MHz'
   % (RAD, PUB, TSYS_RES))
#: ★ NO MACRO IS EMITTED FOR THE SYSTEM-TEMPERATURE RESOLUTION.  `calib_r15`
#: already publishes it as `\CdSpecTsysRes` from this same record, and two
#: macros for one quantity, differing only in how many digits they keep, is a
#: `twinmacro` failure waiting to happen.  The relation between that number
#: and this radius is asserted above, in S1, instead of being printed twice.
#: ★ A HARD `assert` HERE BROKE DRIVE 1 and I nearly left it in: drive 1 is
#: supposed to put the published offset back as the radius and let S1 report
#: that, and an assert on the same relation crashed the run before S1 could
#: print, so the drive matrix showed nothing at all rather than a failure.
#: The check belongs where it can FAIL AND BE SEEN, not where it can abort.
m('ScRadMHz', '%.1f' % RAD)
m('ScNTsysChan', '%d' % N_TSYS_CHAN)

# =====================================================================
# (1b) THE TELLURIC LINE LIST, from calib_r15's own selection
# =====================================================================
T_ATM = float(SPEC['t_atmosphere_K'])
FLO = min(min(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in CAT)
FHI = max(max(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in CAT)
ALLT, SEL = c15.telluric_lines(T_ATM, FLO, FHI)
if DRIVE == 2:
    SEL = [x for x in SEL if x[1] != 'H2O']        # the water lines dropped
TARR = np.array(sorted(x[0] for x in SEL))
TSPEC = {x[0]: x[1] for x in SEL}
#: the two strong water lines the search range holds, named by the catalogue
WAT = sorted(x[0] for x in SEL if x[1] == 'H2O' and x[2] > -6.0
             and 300e3 < x[0] < 350e3)
ck('S2 the selection reproduces the strong water lines in the searched '
   'range and is not vacuous -- it omits catalogued transitions',
   len(WAT) >= 2 and len(SEL) < len(ALLT),
   '%d selected of %d catalogued; strong water at %s GHz'
   % (len(SEL), len(ALLT), ', '.join('%.6f' % (w / 1e3) for w in WAT[:2])))
m('ScNTlLine', '%d' % len(SEL))
by = collections.Counter(x[1] for x in SEL)
m('ScNTlWater', '%d' % by['H2O'])
m('ScNTlOxygen', '%d' % by['O2'])
m('ScNTlOzone', '%d' % by['O3'])


def nearest_tl(f_ghz):
    """(line MHz, signed offset MHz) of the nearest selected transition."""
    x = f_ghz * 1e3
    i = bisect.bisect_left(TARR.tolist(), x)
    cand = [TARR[j] for j in (i - 1, i, i + 1) if 0 <= j < TARR.size]
    best = min(cand, key=lambda a: abs(x - a))
    return float(best), float(x - best)


# =====================================================================
# (1c) THE CROSSINGS, topocentric, with the adopted attribution
# =====================================================================
ATTR = {(r['eb'], round(float(r['freq']), 6)): bool(r['attributed'])
        for r in LEDG}
WINSPAN = collections.defaultdict(list)
for i, r in enumerate(CAT):
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    WINSPAN[r['eb']].append((min(a, b), max(a, b), i))


def window_of(eb, f):
    """The released window a frequency falls in -- BY POSITION, never a name."""
    hit = [i for lo, hi, i in WINSPAN.get(eb, []) if lo - 1e-6 <= f <= hi + 1e-6]
    return hit[0] if hit else None


X = []
for r in MFR:
    X.append(dict(sample='census', star=r['star'], display=r.get('display')
                  or r['star'], eb=r['eb'], f=float(r['f_topo']),
                  f_star=float(r['f_stellar']), tstar=float(r['tstar']),
                  v_bary=r['v_bary'], v_sys=r['v_sys'],
                  attr=ATTR.get((r['eb'], round(float(r['f_topo']), 6)),
                                abs(r['dv_stellar']) <= HALF)))
for r in HOL:
    X.append(dict(sample='holdout', star=r['star'], display=r['star'],
                  eb=r['eb'], f=float(r['freq_GHz']), f_star=None,
                  tstar=float(r['tstar']), v_bary=None, v_sys=None,
                  attr=bool(r['line'] is not None and abs(r['dv_sky']) <= HALF)))
if DRIVE == 3:
    X = X[:-1]
ck('S3 the crossing set is the published census plus the published hold-out, '
   'each with a topocentric frequency',
   sum(1 for x in X if x['sample'] == 'census') == int(tex('NCross'))
   and len(X) == int(tex('TlNCross'))
   and all(x['f'] > 0 for x in X),
   '%d census + %d hold-out = %d against %s published'
   % (sum(1 for x in X if x['sample'] == 'census'),
      sum(1 for x in X if x['sample'] == 'holdout'), len(X), tex('TlNCross')))

for x in X:
    x['tl'], x['doff'] = nearest_tl(x['f'])
    x['win'] = window_of(x['eb'], x['f'])
    x['cls'] = CAT[x['win']]['search_class'] if x['win'] is not None else None

# =====================================================================
# (1d) HD 69830, THE NAMED CASE -- decided on the frame chain's own numbers
# =====================================================================
#: ★ The case is selected by POSITION, not by a name: it is the crossing whose
#: topocentric frequency lies closest to a catalogued atmospheric transition.
#: ★ `mf.vbary` keys on the window's LOW EDGE, not on an arbitrary frequency
#: inside it, so the window has to be found first.  (`r21_image.py` calls it
#: with the crossing frequency and silently takes the zero fallback -- see the
#: report; harmless there because its intervals are GHz wide, wrong anyway.)
NEAR = min(X, key=lambda x: abs(x['doff']))
vb, _sb = mf.vbary(NEAR['eb'], float(CAT[NEAR['win']]['flo_GHz']))
vs, _ss, _bs = mf.vsys(NEAR['star'])
F_STAR_RECON = NEAR['f'] * (1.0 - vb / C) * (1.0 + vs / C)
if DRIVE == 4:
    F_STAR_RECON = NEAR['f']            # the frame chain dropped
ck('S4 the named case is reproduced through the frame chain: its published '
   'stellar-frame frequency follows from its topocentric one',
   abs(F_STAR_RECON - NEAR['f_star']) < 1e-6,
   '%s %s: topo %.7f, stellar %.8f reconstructed %.8f (v_bary %+.4f, '
   'v_sys %+.3f km/s)' % (NEAR['star'], NEAR['eb'], NEAR['f'],
                          NEAR['f_star'], F_STAR_RECON, vb, vs))

#: ★★ AND WHY THE PAPER COULD NOT SEE IT.  Quoted in the stellar frame the
#: same crossing sits a long way from the same line; the coincidence is a
#: topocentric one, because the atmosphere is in the observatory's frame.
_, D_STAR = nearest_tl(NEAR['f_star'])
_cw = float(CAT[NEAR['win']]['chanw_Hz']) / 1e6
if DRIVE == 5:
    #: the frame treated as a detail: the screen evaluated on the frequency
    #: the paper prints instead of the one the atmosphere sees.
    D_STAR = NEAR['doff']
ck('S5 the screen is evaluated topocentrically, and the frame is not a '
   'detail: the stellar-frame offset of the named case differs from the '
   'topocentric one by many channels',
   abs(D_STAR - NEAR['doff']) > 10.0 * _cw,
   'topocentric %+.2f MHz, stellar frame %+.2f MHz, channel %.3f MHz, '
   'radius %.1f MHz' % (NEAR['doff'], D_STAR, _cw, RAD))
m('ScNearStar', NEAR['display'].replace(' ', '~'))
m('ScNearFTopo', '%.4f' % NEAR['f'])
m('ScNearFStar', '%.4f' % NEAR['f_star'])
m('ScNearLine', '%.4f' % (NEAR['tl'] / 1e3))
m('ScNearSpecies', {'H2O': 'H$_2$O', 'O2': 'O$_2$',
                    'O3': 'O$_3$'}[TSPEC[NEAR['tl']]])
m('ScNearOffMHz', '%.1f' % abs(NEAR['doff']))
m('ScNearOffKms', '%.1f' % (abs(NEAR['doff']) / (NEAR['f'] * 1e3) * C))
m('ScNearOffStarMHz', '%.0f' % abs(D_STAR))
m('ScNearVbary', '%+.2f' % vb)
m('ScNearVsys', '%+.2f' % vs)
m('ScNearTstar', '%.2f' % NEAR['tstar'])

# =====================================================================
# (1e) THE COUNT INSIDE THE RADIUS, and the 300 MHz table
# =====================================================================
INR = [x for x in X if abs(x['doff']) <= RAD]
INR_UN = [x for x in INR if not x['attr']]
WIDE = sorted([x for x in X if abs(x['doff']) <= 300.0],
              key=lambda y: abs(y['doff']))
print('     inside %.1f MHz: %d of %d, %d unattributed: %s'
      % (RAD, len(INR), len(X), len(INR_UN),
         ', '.join('%s %s' % (x['display'], x['eb']) for x in INR_UN)
         or 'none'))
#: ★★★ HOW SHARP THE SCREEN IS WHERE IT FIRES, restored in v4.24 from the
#: first-wave measurement that the second patch set dropped.  A radius of two
#: Tsys channels is a large fraction of a narrow window, so a crossing inside
#: it is not necessarily singled out among its own window's channels: HD
#: 69830's window is TUNED ON the water line, and 95 per cent of its own
#: channels lie within the same radius of the same transition.  So
#: "telluric-coincident" here is not a statement that singles this crossing
#: out among its neighbours -- it is a statement that THIS WINDOW CANNOT
#: SEPARATE THE TWO, and removal is the conservative reading of that.  The
#: share is therefore computed and published beside the removal, and it is
#: also why the same radius must come off the control side: in that window
#: every control channel is inside it too.
for _x in INR:
    _w = CAT[_x['win']]
    _lo, _hi = sorted((float(_w['flo_GHz']), float(_w['fhi_GHz'])))
    _n = max(int(round((_hi - _lo) * 1e9 / float(_w['chanw_Hz']))), 1)
    _x['winshare'] = float(np.mean([abs(nearest_tl(float(_f))[1]) <= RAD
                                    for _f in np.linspace(_lo, _hi, _n)]))
_shared = all('winshare' in _x and 0.0 < _x['winshare'] <= 1.0 for _x in INR)
if DRIVE == 14:
    _shared = False
ck('S6b no crossing is screened out without the share of its own window the '
   'radius covers being measured and published beside it',
   _shared and len(INR) > 0,
   '; '.join('%s %.2f of its window' % (_x['display'], _x['winshare'])
             for _x in INR))
if INR:
    m('ScNearWinShare', '%.2f' % INR[0]['winshare'])
    m('ScNearWinPct', '%.0f' % (100.0 * INR[0]['winshare']))
R['near_window_share'] = [dict(star=_x['display'], eb=_x['eb'],
                               share=_x['winshare']) for _x in INR]
m('ScNInRad', '%d' % len(INR))
m('ScNInRadUn', '%d' % len(INR_UN))
m('ScNWide', '%d' % len(WIDE))
m('ScNWideUn', '%d' % sum(1 for x in WIDE if not x['attr']))
m('ScWideMHz', '%d' % 300)

#: the unattributed primary-census count, before and after this screen.  The
#: published 32 is the unattributed ledger rows that lie in a RELEASED Class A
#: window and carry no quality flag, which is how `chance_v414.py` forms it.
def _dq(x):
    for r in LEDG:
        if r['eb'] == x['eb'] and abs(float(r['freq']) - x['f']) < 1e-6:
            return bool(r.get('dq'))
    return False


PRIM = [x for x in X if x['sample'] == 'census' and not x['attr']
        and x['win'] is not None and x['cls'] == 'A' and not _dq(x)]
if DRIVE == 6:
    #: the attribution condition dropped: the reconstruction then no longer
    #: reproduces the published count, which is the whole point of it.
    #: ★ the search-class condition is NOT the one driven here, because
    #: dropping it changes nothing -- the two crossings it excludes are the two
    #: whose blocks are absent from the released catalogue, so `win is None`
    #: already removes them.  A drive on a redundant condition is not a drive.
    PRIM = [x for x in X if x['sample'] == 'census'
            and x['win'] is not None and x['cls'] == 'A' and not _dq(x)]
PRIM_AFTER = [x for x in PRIM if abs(x['doff']) > RAD]
#: ★★ S6 REPLACED.  The assertion here was that the crossings inside the
#: radius partition into attributed and unattributed ones -- which is true of
#: any list by the definition of "unattributed", and so was a check that could
#: not fail.  What has to hold, and can fail, is that this count of the
#: unattributed primary census is reconstructed from the ledger and the
#: released catalogue INDEPENDENTLY and comes out equal to the published one,
#: and that the screen then removes from it exactly the unattributed crossings
#: that lie inside the radius and nothing else.
_REMOVED = [x for x in PRIM if abs(x['doff']) <= RAD]
#: ★ and the quality-flag join is shown to RESOLVE, keyed on block and
#: frequency: without this the `not _dq(x)` condition could be inert and the
#: agreement above would be reached by a route the paper does not describe.
_NDQ_LEDG = sum(1 for r in LEDG if r.get('dq'))
_NDQ_SEEN = sum(1 for x in X if x['sample'] == 'census' and _dq(x))
ck('S6 the unattributed primary census is reconstructed here and equals the '
   'published count, the quality-flag join resolves, and the screen removes '
   'exactly the crossings named inside the radius',
   len(PRIM) == int(CHANCE['observed_before'])
   and len(PRIM_AFTER) == int(CHANCE['observed_after'])
   and int(CHANCE['observed_after']) == int(tex('CeObs'))
   and abs(RAD - float(CHANCE['radius_MHz'])) < 1e-9
   and _NDQ_LEDG > 0 and _NDQ_SEEN == _NDQ_LEDG
   and len(PRIM) - len(PRIM_AFTER) == len(_REMOVED)
   and all(not x['attr'] and abs(x['doff']) <= RAD for x in _REMOVED)
   and {(x['eb'], round(x['f'], 6)) for x in _REMOVED}
   <= {(x['eb'], round(x['f'], 6)) for x in INR_UN},
   'reconstructed %d before and %d after, against %s and %s in the owning '
   'generator (published \\CeObs %s); %d quality-flagged rows joined '
   'of %d in the ledger, %d removed: %s'
   % (len(PRIM), len(PRIM_AFTER), CHANCE['observed_before'],
      CHANCE['observed_after'], tex('CeObs'), _NDQ_SEEN, _NDQ_LEDG,
      len(_REMOVED),
      ', '.join('%s %s %.4f GHz' % (x['display'], x['eb'], x['f'])
                for x in _REMOVED) or 'none'))
R['observed'] = dict(before=len(PRIM), after=len(PRIM_AFTER),
                     published=int(tex('CeObs')),
                     owner=dict(CHANCE),
                     removed=[dict(star=x['display'], eb=x['eb'], f=x['f'],
                                   line=x['tl'] / 1e3,
                                   species=TSPEC[x['tl']], d_MHz=x['doff'],
                                   tstar=x['tstar'])
                              for x in PRIM if abs(x['doff']) <= RAD])
R['wide'] = [dict(sample=x['sample'], star=x['display'], eb=x['eb'],
                  f_topo=x['f'], f_star=x['f_star'], line=x['tl'] / 1e3,
                  species=TSPEC[x['tl']], d_MHz=x['doff'],
                  d_kms=x['doff'] / (x['f'] * 1e3) * C,
                  attributed=x['attr'], tstar=x['tstar'],
                  search_class=x['cls']) for x in WIDE]

# =====================================================================
# (1f) THE CONTROL SIDE, ON THE SAME RADIUS AND THE SAME FRAME
# =====================================================================
#: ★★ A SCREEN APPLIED TO ONE SIDE OF THE COMPARISON IS WORTHLESS.  Removing a
#: crossing for a telluric coincidence lowers the observed count, and the
#: expectation it is compared with is a sum of CONTROL exceedance rates in the
#: same windows -- whose maxima land on the same topocentric channels.  So the
#: same radius is applied to the control exceedances, and the share it takes
#: is what the expectation must be multiplied by.
#:
#: THE HAZARD: a channel index means nothing without the direction of the
#: window's frequency axis.  The direction is taken from the catalogue row's
#: own flo/fhi ORDER and then VALIDATED against the stored in-mask flags,
#: which are computed in the STELLAR frame -- so reproducing them validates
#: the axis and the frame chain at once.  The telluric screen itself is
#: topocentric and uses the same grid before that transform.
def _wkey(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


CATKEY = collections.defaultdict(list)
for i in IA:
    CATKEY[_wkey(CAT[i]['eb'], CAT[i]['flo_GHz'], CAT[i]['fhi_GHz'])].append(i)
#: ★★★★ v4.26 (A3, option (a)).  THIS MUST BE THE WHOLE QUERY, NOT THE MASK,
#: and the distinction did not exist until SO left the mask.  The stored
#: `max_in_mask` flags on every control exceedance were written under the
#: released list of all the species the query returns, so validating a
#: rebuild against them with the SMALLER list reports a disagreement on every
#: exceedance whose channel lands on a transition of the species the mask now
#: leaves out -- 108 of them here, which is what this clause fired on.  The
#: validation's job is to prove the channel axis is rebuilt correctly, so it
#: has to be run against the list the flags were made with; the mask proper
#: is used where attribution is decided, which is not here.  `chance_v414.py`
#: A11 is the same clause and takes `TRANS_ALL` for the same reason.
REST_FULL = np.array(sorted(v[0] for v in mf.TRANS_ALL.values()))
#: ...and the ATTRIBUTION mask, which is the smaller list.  The validation
#: above uses the query because that is what the stored flags were made with;
#: everything that DECIDES anything -- here, which control exceedances the
#: mask removes before the telluric screen is applied -- uses the mask.  They
#: were one object until A3, and nothing distinguished them because nothing
#: had to.
REST_MASK = np.array(sorted(v[0] for v in mf.TRANS.values()))
assert len(REST_MASK) < len(REST_FULL)

#: ★★ THE AXIS DIRECTION COMES FROM THE EXPORT ROW THE STATISTIC WAS TAKEN
#: FROM, not from the catalogue row.  Taking it from the catalogue leaves 20
#: windows whose rebuilt mask disagrees with the stored flags -- which is the
#: channel-reversal defect this validation exists to catch, and it caught my
#: first attempt.  The join is `chance_v414.py`'s: window identified by block
#: and edges as min/max of the pair, the component picked by name where the
#: products agree and by the published control maximum where they do not.
EXPR = json.load(open(os.path.join(
    PAPER, 'corrected_export_v399.json')))['rows']
FFX = json.load(open(os.path.join(
    PAPER, 'r8inputs', 'v409', 'fieldfix_v409.json')))


def _skey(x):
    return re.sub(r'\s+', '', x or '').lower()


def _pick(cands, row, namekey):
    same = [x for x in cands if _skey(x.get(namekey)) == _skey(row['star_name'])]
    pool = same or cands
    if len(pool) == 1:
        return pool[0]
    return min(pool, key=lambda x: abs(float(x['ctrl_max'])
                                       - float(row['ctrl_max_snr'] or 0)))


_BY, _FF = collections.defaultdict(list), collections.defaultdict(list)
for _r in EXPR:
    _BY[_wkey(_r['eb'], _r['flo'], _r['fhi'])].append(_r)
for _r in FFX:
    _FF[_wkey(_r['eb'], _r['flo'], _r['fhi'])].append(_r)
SRC = {}
for i, r in enumerate(CAT):
    k = _wkey(r['eb'], r['flo_GHz'], r['fhi_GHz'])
    q = _pick(_FF[k], r, 'star') if _FF.get(k) else None
    if q is None or not (q.get('ctrl_all') or []):
        q = _pick(_BY[k], r, 'star_name') if _BY.get(k) else None
    if q is not None:
        SRC[i] = q


def _inmask(fs, rest=None):
    ins = np.zeros(fs.size, bool)
    for fr in (REST_FULL if rest is None else rest):
        ins |= (fs >= fr * (1.0 - HALF / C)) & (fs <= fr * (1.0 + HALF / C))
    return ins


N_EXC = N_EXC_MASK = N_EXC_TL = N_EXC_TL_ONLY = N_EXC_QUERY = 0
VALBAD, NJOIN = [], 0
for w in CELLS:
    if w['cls'] != 'A' or w['stratum'] == 'archival_tail':
        continue
    idx = CATKEY.get(_wkey(w['eb'], w['lo'], w['hi']), [])
    same = [j for j in idx if sa.canon(CAT[j]['star_name']) == sa.canon(w['star'])]
    cand = same or idx
    if len(cand) > 1:
        cand = [min(cand, key=lambda j: abs(float(CAT[j]['star_snr'] or 0.0)
                                            - w['adopted']))]
    if len(cand) != 1:
        continue
    j = cand[0]
    src = SRC.get(j)
    if src is None:
        continue
    g = np.linspace(w['lo'], w['hi'], w['nch'])
    if float(src['flo']) > float(src['fhi']):
        g = g[::-1]
    if DRIVE == 7:
        g = g[::-1]                                  # the axis read backwards
    fs = g * (1.0 - w['v_bary'] / C) * (1.0 + w['v_sys'] / C)
    im = _inmask(fs)                      # the query, for the validation
    im_mask = _inmask(fs, REST_MASK)      # the attribution mask, for the count
    if abs(float(im.mean()) - w['masked_share']) > 1e-9:
        VALBAD.append((w['key'], 'grid share'))
    exc = [c for c in w['ctrl'] if c['win_max'] >= TRIG]
    for c in exc:
        if bool(im[c['max_chan']]) != c['max_in_mask']:
            VALBAD.append((w['key'], 'channel %d' % c['max_chan']))
    tlin = np.array([abs(nearest_tl(float(f))[1]) <= RAD for f in g])
    for c in exc:
        N_EXC += 1
        a_, b_ = bool(im_mask[c['max_chan']]), bool(tlin[c['max_chan']])
        N_EXC_MASK += a_
        N_EXC_QUERY += bool(im[c['max_chan']])
        N_EXC_TL += b_
        N_EXC_TL_ONLY += (b_ and not a_)
    NJOIN += 1
ck('S7 the control side is screened on the same radius in the same frame, '
   'the rebuilt channel axis reproduces every stored in-mask flag when it is '
   'rebuilt from the list those flags were made with, and the attribution '
   'mask is the strictly smaller list the count below uses',
   not VALBAD and N_EXC > 0 and N_EXC_MASK <= N_EXC_QUERY
   and len(REST_MASK) < len(REST_FULL),
   '%d windows joined, %d control exceedances, %d in the attribution mask '
   '(%d in the whole query, which is what the stored flags were made with), '
   '%d inside the telluric radius (%d of them not already masked); '
   '%d validation failures' % (NJOIN, N_EXC, N_EXC_MASK, N_EXC_QUERY,
                               N_EXC_TL, N_EXC_TL_ONLY, len(VALBAD)))
m('ScNCtrlExc', '%d' % N_EXC)
m('ScNCtrlTl', '%d' % N_EXC_TL)
m('ScNCtrlTlOnly', '%d' % N_EXC_TL_ONLY)
#: the factor the expectation must be multiplied by: the share of the control
#: exceedances that SURVIVE the molecular mask and then also the telluric one,
#: relative to the share that survives the molecular mask alone
SURV_M = N_EXC - N_EXC_MASK
SURV_MT = N_EXC - N_EXC_MASK - N_EXC_TL_ONLY
FAC = SURV_MT / float(SURV_M) if SURV_M else float('nan')
E_PUB = float(CHANCE['e_chance_before'])
R['control'] = dict(n_windows=NJOIN, n_exc=N_EXC, n_mask=N_EXC_MASK,
                    n_query=N_EXC_QUERY,
                    n_telluric=N_EXC_TL, n_telluric_only=N_EXC_TL_ONLY,
                    factor=FAC, e_published=E_PUB, e_after=E_PUB * FAC)

# =====================================================================
# (2) THE IMAGE SIDEBAND, OVER EVERY CLASS A WINDOW
# =====================================================================
IF_RANGE = {'3': (4.0, 8.0), '4': (4.0, 8.0), '5': (4.0, 8.0),
            '6': (4.5, 10.0), '7': (4.0, 8.0), '8': (4.0, 8.0),
            '9': (4.0, 12.0), '10': (4.0, 12.0)}
DSB = {'9', '10'}
BYEB = collections.defaultdict(list)
for i, r in enumerate(CAT):
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    BYEB[r['eb']].append(dict(i=i, lo=lo, hi=hi, band=r['band'],
                              star=r['star_name'],
                              chanw=float(r['chanw_Hz']),
                              cls=r['search_class']))


def _allow(w, lo_if, hi_if):
    out = [(w['hi'] - hi_if, w['lo'] - lo_if),
           (w['hi'] + lo_if, w['lo'] + hi_if)]
    return [(a, b) for a, b in out if b > a]


def _isect(seg, allow):
    nxt = []
    for s0, s1 in seg:
        for a, b in allow:
            p, q = max(s0, a), min(s1, b)
            if q > p:
                nxt.append((p, q))
    return sorted(nxt)


def lo1_for_window(w):
    """The LO1 interval, built outwards from this window and then narrowed by
    the block's others, nearest first -- a window on a second tuning inside
    the same block drops out instead of emptying the answer."""
    ws = BYEB[w['eb']] if 'eb' in w else None
    lo_if, hi_if = IF_RANGE[w['band']]
    seg, used = _allow(w, lo_if, hi_if), 1
    rest = sorted([x for x in ws if x['i'] != w['i']],
                  key=lambda x: abs(0.5 * (x['lo'] + x['hi'])
                                    - 0.5 * (w['lo'] + w['hi'])))
    for x in rest:
        trial = _isect(seg, _allow(x, lo_if, hi_if))
        if trial:
            seg, used = trial, used + 1
    return seg, used


#: THE PARENTS: the CO isotopologues of the frozen mask and nothing else, which
#: is what the referee's instruction names and what these fields actually hold.
CO_RE = re.compile(r'^(?:12C|13C|C17|C18|C)(?:O)\(')
CO = {k: v[0] for k, v in mf.TRANS.items() if CO_RE.match(k)}
if DRIVE == 9:
    CO = {}
#: the sightline: a transition at rest in the local standard of rest.  The
#: solar motion is projected on each star's own position, from the frozen
#: SIMBAD harvest, and the star's own velocity comes from the same file.
POS = {sa.designation(k, tex=False): v for k, v in LOS['star'].items()}


#: ★ The solar motion is the one the paper's own LSR generator uses, READ from
#: that file rather than retyped, so the two cannot disagree about a frame.
_src = open(os.path.join(PAPER, 'masklsr_v520.py')).read()
_mm = re.search(r'UVW_KMS\s*=\s*\(([^)]*)\)', _src)
UVW = tuple(float(t) for t in _mm.group(1).split(','))


def _gal(ra, dec):
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    g = SkyCoord(float(ra) * u.deg, float(dec) * u.deg).galactic
    return g.l.rad, g.b.rad


def v_sun_for(ra, dec):
    u0, v0, w0 = UVW
    la, be = _gal(ra, dec)
    return (u0 * math.cos(be) * math.cos(la) + v0 * math.cos(be) * math.sin(la)
            + w0 * math.sin(be))


IMG_ROWS = []
NOPOS, NOLO, OVER, NOBARY = [], [], [], []
for i in IA:
    r = CAT[i]
    w = [x for x in BYEB[r['eb']] if x['i'] == i][0]
    w = dict(w, eb=r['eb'])
    band = r['band']
    if band in DSB:
        IMG_ROWS.append(dict(i=i, eb=r['eb'], star=r['star_name'], band=band,
                             dsb=True, covered=False, hit=False))
        continue
    seg, used = lo1_for_window(w)
    if not seg:
        NOLO.append((r['eb'], i))
        IMG_ROWS.append(dict(i=i, eb=r['eb'], star=r['star_name'], band=band,
                             dsb=False, covered=False, hit=False, nolo=True))
        continue
    key = sa.designation(r['star_name'], tex=False)
    p = POS.get(key)
    vb_, _s = mf.vbary(r['eb'], float(r['flo_GHz']))
    nobary = vb_ is None
    vb_ = 0.0 if nobary else vb_
    if nobary:
        NOBARY.append(i)
    if p is None:
        NOPOS.append((r['star_name'], i))
        vsys_, vsun_ = None, None
    else:
        vsys_ = p.get('rv_kms')
        vsun_ = v_sun_for(p['ra'], p['dec'])
    #: the image band of the WHOLE window: reflect its edges about the LO1
    #: interval.  (2L - hi, 2L - lo) for L in each segment.
    img = sorted([(2 * a - w['hi'], 2 * b - w['lo']) for a, b in seg])
    if DRIVE == 8:
        img = [(w['lo'], w['hi'])]
    if any(not (ih < wl or il > wh) for il, ih in img
           for wl, wh in [(w['lo'], w['hi'])]):
        OVER.append(i)
    par = []
    for k, f0 in CO.items():
        for frame, vv in (('star', vsys_), ('lsr', vsun_)):
            if vv is None:
                continue
            #: topocentric frequency of a transition at rest in that frame
            if frame == 'star':
                fo = f0 / ((1.0 - vb_ / C) * (1.0 + vv / C))
            else:
                fo = f0 / ((1.0 - vb_ / C) * (1.0 - vv / C))
            seg_pos = []
            for a, b in seg:
                p0, p1 = 2 * a - fo, 2 * b - fo
                p0, p1 = min(p0, p1), max(p0, p1)
                q0, q1 = max(p0, w['lo']), min(p1, w['hi'])
                if q1 >= q0:
                    seg_pos.append((q0, q1))
            if seg_pos:
                par.append(dict(line=k, f_rest=f0, f_topo=fo, frame=frame,
                                pos=seg_pos))
    #: and does a crossing lie at the image position?  Matched BY FREQUENCY
    #: inside this same window -- never by a name.
    xin = [x for x in X if x['win'] == i]
    #: ★★ THE COUNTERFACTUAL KEY, carried so that the position key can be
    #: shown to DISCRIMINATE.  A name-keyed implementation would offer every
    #: crossing of the same star, in any window of any block, to this window's
    #: image interval; thirteen joins in this project have been keyed that way.
    xin_name = [x for x in X
                if sa.canon(x['star']) == sa.canon(r['star_name'])]
    hit, hit_name = [], []
    tol = max(w['chanw'] / 1e9, 0.0)
    for pp in par:
        for x in (xin_name if DRIVE == 10 else xin):
            if any(a - tol <= x['f'] <= b + tol for a, b in pp['pos']):
                hit.append(dict(star=x['display'], eb=x['eb'], f=x['f'],
                                win=x['win'], line=pp['line'],
                                frame=pp['frame'],
                                attributed=x['attr'], tstar=x['tstar']))
        for x in xin_name:
            if any(a - tol <= x['f'] <= b + tol for a, b in pp['pos']):
                hit_name.append((x['eb'], round(x['f'], 6)))
    #: ★★ AND HOW MUCH OF THE WINDOW THE IMAGE POSITION ACTUALLY IS.  The
    #: local oscillator is bounded, not known, so an image position is an
    #: interval; where that interval covers most of the window, a crossing
    #: inside it is no evidence at all.  The union share is therefore measured
    #: and the hits are compared with what the share alone predicts.
    segs = sorted([(max(a - tol, w['lo']), min(b + tol, w['hi']))
                   for pp in par for a, b in pp['pos']])
    un, cur = [], None
    for a, b in segs:
        if cur and a <= cur[1]:
            cur = (cur[0], max(cur[1], b))
        else:
            if cur:
                un.append(cur)
            cur = (a, b)
    if cur:
        un.append(cur)
    share = sum(b - a for a, b in un) / (w['hi'] - w['lo'])
    IMG_ROWS.append(dict(i=i, eb=r['eb'], star=r['star_name'], band=band,
                         dsb=False, lo1=seg, n_win_used=used, image=img,
                         covered=bool(par), parents=par, hit=bool(hit),
                         hits=hit, hits_name=hit_name, i_win=i,
                         n_cross_in_window=len(xin),
                         share=share, lo1_width=sum(b - a for a, b in seg),
                         win_width=w['hi'] - w['lo']))

NCOV = sum(1 for r_ in IMG_ROWS if r_.get('covered'))
NHIT = sum(1 for r_ in IMG_ROWS if r_.get('hit'))
NDSB = sum(1 for r_ in IMG_ROWS if r_.get('dsb'))
ck('S8 every Class A window admits a local oscillator consistent with its '
   'own block and its image band never overlaps itself',
   not NOLO and not OVER,
   '%d windows with no admissible LO1, %d whose image band meets themselves; '
   '%d double-sideband windows reported separately' % (len(NOLO), len(OVER),
                                                       NDSB))
ck('S9 the image screen is not vacuous: some Class A window\'s image band '
   'does cover a CO isotopologue transition',
   NCOV > 0, '%d of %d Class A windows covered, %d hold a crossing at the '
   'image position' % (NCOV, len(IA), NHIT))
#: ★★ S10 REPLACED.  The assertion here was that every matched crossing
#: carries the same block identifier as the window it matched -- true by
#: construction, because the candidate list was already selected on that
#: identifier, so it was a check that could not fail.  What can fail, and is
#: the defect this project has produced thirteen times, is the join KEY: so
#: the position key is required to hold exactly (every match lies in the
#: window it was matched against) AND the name key is evaluated in parallel
#: and required to give MORE matches, which demonstrates that the choice of
#: key is doing work rather than being a comment.
_pos_ok = all(h['win'] == r_['i_win']
              for r_ in IMG_ROWS for h in r_.get('hits', []))
_NPOS = sum(len(r_.get('hits', [])) for r_ in IMG_ROWS)
_NNAME = sum(len(r_.get('hits_name', [])) for r_ in IMG_ROWS)
ck('S10 a crossing is matched to an image position by frequency inside the '
   'window it was matched against, and the name key is shown to be looser',
   _pos_ok and _NNAME > _NPOS,
   '%d matches on the position key, %s inside the window they were matched '
   'against; the same intervals on a star-name key take %d'
   % (_NPOS, 'all' if _pos_ok else 'NOT all', _NNAME))
#: the chance expectation: each crossing in a covered window, weighted by the
#: share of its own window the image positions occupy
_cov = [r_ for r_ in IMG_ROWS if r_.get('covered')]
E_IMG = sum(r_['share'] * r_['n_cross_in_window'] for r_ in _cov)
SH_MED = float(np.median([r_['share'] for r_ in _cov])) if _cov else float('nan')
LO1_MED = float(np.median([r_['lo1_width'] for r_ in _cov])) if _cov else 0.0
N_X_COV = sum(r_['n_cross_in_window'] for r_ in _cov)
_narrow = [r_ for r_ in _cov if r_['share'] < 0.5]
N_HIT_NARROW = sum(1 for r_ in _narrow if r_['hit'])
ck('S9b the screen is reported with the localisation it actually has: the '
   'image position is an interval, and the hits are compared with what that '
   'interval\'s share of the window predicts on its own',
   E_IMG > 0 and SH_MED == SH_MED,
   '%d crossings in covered windows, image positions occupy a median %.2f of '
   'the window (LO1 bounded to a median %.2f GHz), so %.1f hits are expected '
   'and %d are observed; %d of the %d windows localise to under half the '
   'window and %d of those hold a hit'
   % (N_X_COV, SH_MED, LO1_MED, E_IMG, NHIT, len(_narrow), len(_cov),
      N_HIT_NARROW))
m('ScImShareMed', '%.2f' % SH_MED)
m('ScImLoWidth', '%.2f' % LO1_MED)
m('ScImNCross', '%d' % N_X_COV)
m('ScImExp', '%.1f' % E_IMG)
m('ScImNHitUn', '%d' % len({(h['eb'], round(h['f'], 6))
                            for r_ in IMG_ROWS for h in r_.get('hits', [])
                            if not h['attributed']}))
m('ScImNWin', '%d' % len(IA))
m('ScImNCov', '%d' % NCOV)
m('ScImNWinHit', '%d' % NHIT)
#: ★ the number of WINDOWS holding a hit and the number of CROSSINGS at an
#: image position are not the same quantity, so they are emitted apart on
#: purpose: a window can hold more than one crossing inside its image interval.
m('ScImNHitCross', '%d' % len({(h['eb'], round(h['f'], 6))
                               for r_ in IMG_ROWS for h in r_.get('hits', [])}))
m('ScImNDsb', '%d' % NDSB)
m('ScImNCo', '%d' % len(CO))
m('ScImNoPos', '%d' % len({n for n, _ in NOPOS}))
m('ScImNWinNoPos', '%d' % len(NOPOS))
m('ScImNWinNoBary', '%d' % len(NOBARY))
R['image'] = dict(n_window=len(IA), n_covered=NCOV, n_hit=NHIT, n_dsb=NDSB,
                  n_cross_in_covered=N_X_COV, share_med=SH_MED,
                  lo1_width_med=LO1_MED, expected=E_IMG,
                  n_narrow=len(_narrow), n_hit_narrow=N_HIT_NARROW,
                  n_co=len(CO), no_pos=sorted({n for n, _ in NOPOS}),
                  n_win_no_pos=len(NOPOS),
                  hits=[h for r_ in IMG_ROWS for h in r_.get('hits', [])],
                  covered=[dict(eb=r_['eb'], star=r_['star'],
                                lines=sorted({p['line'] for p in r_['parents']}),
                                frames=sorted({p['frame'] for p in r_['parents']}))
                           for r_ in IMG_ROWS if r_.get('covered')])

# ---------------------------------------------------------------------
# (2b) THE UNATTRIBUTED CROSSINGS AT AN IMAGE POSITION, NAMED AND TESTED
# ---------------------------------------------------------------------
#: ★★★★ A CROSSING THAT COINCIDES WITH A CATALOGUED LINE IN THE SIGNAL BAND
#: IS ATTRIBUTED, so leaving a crossing at the IMAGE of one unattributed and
#: unnamed is an inconsistency unless the image case is held to a stated
#: standard.  The standard already in print is the one the frequency screen
#: above uses: a leak at the specified image rejection needs a parent `IRR_FAC`
#: times the crossing's own amplitude, so the parent is looked for AT ITS OWN
#: FREQUENCY in the SAME BLOCK and measured there.  Two quantities are emitted
#: per crossing and neither is typed: how close the bounded oscillator can
#: place the crossing's image to the transition, and how bright the parent
#: actually is where the block observed it.
#: ★ the rejection is the specification figure the frequency screen already
#: publishes, READ OUT OF THAT GENERATOR'S SOURCE and not retyped here, so the
#: two screens cannot disagree about it.  Its source and not its product: that
#: generator runs after this one, and a product read back would be the
#: PREVIOUS build's answer.
_isrc = open(os.path.join(PAPER, 'r21_image.py')).read()
_im = re.search(r'^IRR_DB\s*=\s*([0-9.]+)\s*$', _isrc, re.M)
assert _im, 'r21_image.py no longer declares IRR_DB, which this reads'
IRR_DB = float(_im.group(1))
IRR_FAC = 10.0 ** (IRR_DB / 10.0)
#: the window's own amplitude scale, from the deposited catalogue: the
#: statistic at the star times the window's noise, which is the quantity the
#: published screen already ratios (`r21_image.py`).
_AMP = {}
for _i, _r in enumerate(CAT):
    try:
        _AMP[_i] = (float(_r['star_snr']) * float(_r['rms_mJy']),
                    float(_r['star_snr']))
    except (TypeError, ValueError):
        _AMP[_i] = None


def _main_line(name):
    """A transition's main line, not one of its hyperfine components."""
    return ',' not in name


IMG_UN = []
for r_ in IMG_ROWS:
    _w = None
    for h in r_.get('hits', []):
        if h['attributed']:
            continue
        if _w is None:
            _w = [x for x in BYEB[r_['eb']] if x['i'] == r_['i_win']][0]
        tol = max(_w['chanw'] / 1e9, 0.0)
        #: the parent of record is the main line, and the bound on the offset
        #: is taken over every frame in which it matched, so the number holds
        #: in either frame rather than in the kinder one.
        off, par = 0.0, None
        for pp in r_['parents']:
            if not _main_line(pp['line']):
                continue
            if not any(a - tol <= h['f'] <= b + tol for a, b in pp['pos']):
                continue
            for a, b in r_['lo1']:
                for o in (2 * a - h['f'] - pp['f_topo'],
                          2 * b - h['f'] - pp['f_topo']):
                    if abs(o) * 1e3 > off:
                        off = abs(o) * 1e3
            par = pp if par is None else par
        if par is None:
            continue
        #: THE PARENT AT ITS OWN FREQUENCY, IN THIS BLOCK.  A window of the
        #: same block covering the transition is the measurement; the largest
        #: amplitude in it bounds anything that could have leaked.
        _cov = [x for x in BYEB[r_['eb']]
                if x['lo'] - 1e-6 <= par['f_topo'] <= x['hi'] + 1e-6]
        _best, _bt = None, None
        for x in _cov:
            v = _AMP.get(x['i'])
            if v and (_best is None or v[0] > _best):
                _best, _bt = v[0], v[1]
        _mine = _AMP.get(r_['i_win'])
        IMG_UN.append(dict(star=sa.designation(r_['star'], tex=True),
                           eb=r_['eb'], f=h['f'], tstar=h['tstar'],
                           line=par['line'], line_tex=mf.tex_label(par['line']),
                           f_rest=par['f_rest'], f_topo=par['f_topo'],
                           off_bound_MHz=off,
                           parent_observed=bool(_cov),
                           parent_amp=_best, parent_tstar=_bt,
                           own_amp=(_mine or [None])[0],
                           ratio=(None if not (_best and _mine)
                                  else _best / _mine[0])))
#: one row per crossing, in a frequency order the catalogue fixes
IMG_UN = sorted({(d['eb'], round(d['f'], 6)): d for d in IMG_UN}.values(),
                key=lambda d: (d['f'], d['eb']))
if DRIVE == 15:
    #: the parent is allowed to be as bright as a leak would need
    IMG_UN = [dict(d, ratio=(d['ratio'] or 0.0) + IRR_FAC) for d in IMG_UN]
ck('S13 EVERY UNATTRIBUTED CROSSING AT AN IMAGE POSITION IS NAMED AND HELD '
   'TO THE SAME LEAKAGE STANDARD AS THE FREQUENCY SCREEN: its parent\'s own '
   'frequency was observed in the same block, and the largest amplitude '
   'there is too small for a leak at the specified rejection to reach it',
   len(IMG_UN) == len({(h['eb'], round(h['f'], 6))
                       for r_ in IMG_ROWS for h in r_.get('hits', [])
                       if not h['attributed']})
   and len(IMG_UN) > 0
   and all(d['parent_observed'] and d['ratio'] is not None
           and d['ratio'] < IRR_FAC and d['parent_tstar'] < TRIG
           for d in IMG_UN),
   '; '.join('%s %.4f GHz, image within %.0f MHz of %s, parent %.2f of the '
             'crossing (T* %.2f) against the %.0f a leak needs'
             % (d['star'], d['f'], d['off_bound_MHz'], d['line'],
                d['ratio'] if d['ratio'] is not None else float('nan'),
                d['parent_tstar'] if d['parent_tstar'] is not None
                else float('nan'), IRR_FAC)
             for d in IMG_UN))
for _n, _d in zip('AB', IMG_UN):
    m('ScImUnStar%s' % _n, _d['star'].replace(' ', '~'))
    m('ScImUnCross%s' % _n, '%.4f' % _d['f'])
    m('ScImUnLine%s' % _n, _d['line_tex'])
    m('ScImUnOff%s' % _n, format(int(round(_d['off_bound_MHz'])),
                                 ',').replace(',', '\\,'))
    m('ScImUnRatio%s' % _n, '%.2f' % _d['ratio'])
m('ScImUnParMaxT', '%.2f' % max(d['parent_tstar'] for d in IMG_UN))
R['image_unattributed'] = IMG_UN
R['image_irr_db'] = IRR_DB

# =====================================================================
# (3) THE FILTER'S RESPONSE TO A FEATURE N CHANNELS WIDE
# =====================================================================
#: WHAT IS MEASURED.  Not the statistic, but the quantity the paper's limits
#: ARE: the total flux a feature must carry to be recovered nine times in ten,
#: as a function of how many channels it is spread over.  That is the paper's
#: own EIRP_90 definition applied to a broad feature instead of a carrier, and
#: it is the number "optimistic by a factor X" refers to.
#:
#: Eq. 1 is implemented exactly as written, with sigma constant: each
#: integration's spectrum is shifted to follow a trial drift and the shifted
#: spectra are added, inverse-variance weighted, then divided by the noise of
#: that stack.  Because the stack is LINEAR, the noise realisation and the
#: signal template can be stacked once each and combined at any amplitude, so
#: a recovery curve costs one set of realisations.
#:
#: ★ A FIRST VERSION OF THIS MEASUREMENT GAVE -0.62 AND WAS WRONG.  It read
#: the maximum of the grid, which for a weak broad feature is the NOISE
#: maximum: the quantity saturates and the exponent it returns is an artefact
#: of 4096 cells of noise, not a property of the filter.  The recovery
#: amplitude does not saturate.
#:
#: This is a property of the ESTIMATOR, so it is measured on Gaussian noise
#: and claims nothing about the data; what it decides is which of two
#: analytic factors -- N or sqrt(N) -- the paper should state.
rng = np.random.default_rng(20261018)
NT, NCH, NTRIAL = 32, 1024, 80
NS = [1, 2, 4, 8, 16, 32, 64]
DRIFTS = np.arange(-2, 3)
SIG = 1.0
PDET = 0.9


def _shift(t):
    return np.rint(DRIFTS[:, None] * (t / (NT - 1.0))).astype(int)


def _stack(cube):
    """the drift x channel grid of Eq. 1 for one realisation, sigma constant"""
    out = np.zeros((DRIFTS.size, NCH))
    for k, d in enumerate(DRIFTS):
        acc = np.zeros(NCH)
        for t in range(NT):
            acc += np.roll(cube[t], -int(round(d * t / (NT - 1.0))))
        out[k] = acc / (SIG * math.sqrt(NT))
    return out


def a_ninety(n, matched):
    """the TOTAL flux recovered nine times in ten, for a feature n channels
    wide, with the single-channel filter or with the filter matched to it."""
    c0 = NCH // 2
    ind = np.zeros((NT, NCH))
    ind[:, c0:c0 + n] = 1.0 / (n * NT)
    tmpl = _stack(ind)
    noise = [_stack(rng.normal(0.0, SIG, size=(NT, NCH)))
             for _ in range(NTRIAL)]
    if matched:
        ker = np.ones(n) / math.sqrt(n)
        tmpl = np.array([np.convolve(row, ker, 'same') for row in tmpl])
        noise = [np.array([np.convolve(row, ker, 'same') for row in g])
                 for g in noise]
    span = (c0 - 1, c0 + n)

    def frac(a):
        ok = 0
        for g in noise:
            grid = g + a * tmpl
            if grid.max() >= TRIG:
                ch = int(np.unravel_index(int(grid.argmax()), grid.shape)[1])
                ok += span[0] <= ch <= span[1]
        return ok / float(NTRIAL)

    lo, hi = 1.0, 1.0
    while frac(hi) < PDET and hi < 1e7:
        lo, hi = hi, hi * 2.0
    for _ in range(26):
        mid = 0.5 * (lo + hi)
        if frac(mid) < PDET:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


#: and the paper's own widest resolved line, read from the macro that states
#: it, so the factor quoted in the appendix is the factor at that width
NWIDE = int(tex('RgResFwhmChMax'))
A1 = np.array([a_ninety(n, False) for n in NS])
A2 = np.array([a_ninety(n, True) for n in NS])
AW1, AW2 = a_ninety(NWIDE, False), a_ninety(NWIDE, True)
lx = np.log(np.array(NS, float))
p1 = float(np.polyfit(lx, np.log(A1), 1)[0])
p2 = float(np.polyfit(lx, np.log(A2), 1)[0])
if DRIVE == 11:
    p1 = 0.5
if DRIVE == 12:
    p2 = 1.0
#: ★ THE ASSERTION PINS THE INVARIANT AND NOT TODAY'S NUMBER.  What has to
#: hold is that the single-channel filter's penalty is far closer to N than to
#: sqrt(N); the exponent itself is published and is 0.79-0.82 across
#: realisations, integration counts, channel counts and drift grids.  The
#: measured value falls short of 1 for a reason that belongs to the search and
#: not to the model: a feature n channels wide offers n independent
#: single-channel trials at the same per-channel amplitude, so the maximum of
#: the grid is reached a little sooner than the per-channel response alone
#: would say.
ck('S11 the single-channel filter of Eq. 1 needs of order N times the flux, '
   'and nothing like sqrt(N) times, to reach the same recovery on a feature '
   'N channels wide',
   p1 >= 0.70 and p1 - 0.5 > 0.2,
   'measured exponent %+.3f over N = %d..%d (N gives 1, sqrt(N) gives 0.5); '
   'ratio at N = %d is %.1f, at N = %d it is %.1f'
   % (p1, min(NS), max(NS), max(NS), A1[-1] / A1[0], NWIDE, AW1 / A1[0]))
ck('S12 and sqrt(N) is what a filter matched to the feature would need, on '
   'the same realisations, so the two factors are told apart by measurement',
   abs(p2 - 0.5) < 0.12,
   'measured exponent %+.3f, ratio at N = %d is %.1f'
   % (p2, max(NS), A2[-1] / A2[0]))
#: ★★ AND THE SIMULATION IS CHECKED AGAINST THE ARITHMETIC IT IS REPLACING.
#: For a one-channel feature Eq. 1 reduces to a closed form: the stacked
#: statistic is a/(sigma*sqrt(NT)), so the flux that reaches the trigger is
#: TRIG*sigma*sqrt(NT) exactly, and the measured recovery amplitude must sit a
#: little above it -- the excess being the price of asking for nine recoveries
#: in ten against the maximum of a grid, not a single threshold crossing.
#: Without this the whole curve could be wrong by a constant and the exponent
#: would still look right.
A_ANA = TRIG * SIG * math.sqrt(NT)
_r_ana = A1[0] / A_ANA
if DRIVE == 13:
    _r_ana *= 3.0
ck('S11b the one-channel case reproduces the closed form of Eq. 1, so the '
   'curve is anchored and not only its slope',
   1.0 <= _r_ana <= 1.4,
   'measured %.2f against %.2f analytic, ratio %.3f' % (A1[0], A_ANA, _r_ana))
m('ScNBroadExp', '%.2f' % p1)
m('ScNBroadExpMatched', '%.2f' % p2)
m('ScNBroadMax', '%d' % max(NS))
m('ScNBroadRatioMax', '%.1f' % (A1[-1] / A1[0]))
m('ScNBroadChan', '%d' % NWIDE)
m('ScNBroadRatio', '%.0f' % (AW1 / A1[0]))
m('ScNBroadRatioMatched', '%.1f' % (AW2 / A2[0]))
R['filter'] = dict(n=NS, a90_single=A1.tolist(), a90_matched=A2.tolist(),
                   exp_single=p1, exp_matched=p2, n_int=NT, n_chan=NCH,
                   n_trial=NTRIAL, p_det=PDET, trigger=TRIG, n_wide=NWIDE,
                   a90_wide_single=AW1, a90_wide_matched=AW2)

# =====================================================================
# output
# =====================================================================
R['generator'] = os.path.basename(__file__)
R['round'] = ROUND
R['drive'] = DRIVE
R['radius_MHz'] = RAD
with open(OUT, 'w') as fh:
    fh.write('%%%% GENERATED by %s (round %d) -- do not hand-edit.\n'
             % (os.path.basename(__file__), ROUND))
    for s in sorted(MACROS):
        fh.write(s + '\n')
json.dump(R, open(OUT_JSON, 'w'), indent=1, sort_keys=True, default=str)
print('\n  %d macros -> %s' % (len(MACROS), os.path.basename(OUT)))
print('  FAILED: %s' % (', '.join(FAIL) if FAIL else 'none'))
raise SystemExit(1 if FAIL else 0)
