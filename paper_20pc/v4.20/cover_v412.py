#!/usr/bin/env python3
r"""cover_v412.py -- round 185.  Three things the paper says in more than one
way, each reduced to one measured definition.

WHY THIS EXISTS.

1. THE FREQUENCY COVERAGE HAS BEEN QUOTED AS THREE DIFFERENT QUANTITIES UNDER
   ONE WORD.  The abstract and Section 3 say 47.7 GHz, which is a UNION: the
   measure of the set of sky frequencies observed at least once.  The
   recurrence subsection says "181.5 GHz of fine-channel coverage", with 79.7
   and 17.8 GHz as subsets of it.  181.5 is neither the union (47.7) nor the
   summed window bandwidth (588.0): it is the per-system union SUMMED OVER
   SYSTEMS, so a frequency observed toward six systems is counted six times.
   A reader cannot tell any of the three apart from the word "coverage", and
   two of them have been differenced against each other.

   This generator publishes exactly TWO definitions and measures both for
   each class:

       union bandwidth          the measure of the set of sky frequencies
                                covered at least once.  Counts a frequency
                                once however often it was observed.
       summed window bandwidth  the sum of the individual windows' widths.
                                Counts integrated search effort, and exceeds
                                the union by the mean number of visits.

   Anything else -- the per-system sum above, or a count of systems at a
   frequency -- is a third quantity and must be named in full where it is
   used, never called "coverage".

2. CONFIRMATION COVERAGE.  Searching a frequency and being able to CONFIRM a
   persistent carrier at it are different extents, and only the first has
   been quoted.  C_conf(nu) is the number of Class A systems for which two
   independent execution blocks separated by more than a day (or a year)
   both cover nu, so a persistent carrier found once could have been tested
   at a second epoch.  Its support, as a union bandwidth, is the parameter
   space over which this experiment could have confirmed anything at all --
   and it is half the searched union.

3. THE PROXIMA STACK'S TWO BOOKKEEPING PUZZLES.  The stack combines 66
   execution blocks where the primary census holds 25 for that star; and its
   realised gain, 3.19, exceeds sqrt(N_eff) = 2.80 although the combination
   is also said to be ideal to about one per cent.  Both are measured here.
   The second is NOT a mixed completeness convention -- `stacktol_v411.py`
   already pins the single-epoch and stacked limits to one injection
   calibration, and asserts it -- it is the noise REALISATION: the measured
   median-absolute-deviation noise of that stacked spectrum came out 0.880 of
   the inverse-variance prediction over 126 common channels, and
   2.805 x 1/0.880 = 3.187 exactly.  On a like-for-like basis -- propagated
   noise against propagated noise, which is the quantity sqrt(N_eff)
   predicts -- the gain is 2.80.

   ALSO FOUND HERE, AND NOT IN EITHER REPORT: 11 of the 69 stacked stars are
   not primary-census stars at all.  They come from the external and
   out-of-sample block sets.  The sentence that calls them "the surveyed
   stars" is therefore counting over a set the rest of the paper does not use.

4. THE BENCHMARK'S BEAM.  The 12 m / 1 MW / 230 GHz example quotes a
   directive gain and an EIRP but never says how narrow the beam is, which
   is the one thing that makes the EIRP large.  Omega = 4 pi / G is read off
   the gain the paper already publishes, so there is no second convention.

Usage:  cover_v412.py [--drive N]      (N = 1..9, one assertion each)

--drive 0 means "no perturbation, but do not write a path production reads":
the suffix follows the FLAG, not the perturbation.
"""
import collections
import csv
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 185
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
SEP_DAY = 1.0            # the paper's own definition of an independent epoch
SEP_YR = 365.25
C_MS = 2.998e8           # the same c numbers_v410.py uses for the benchmark

M, fail = [], []


def m(k, v):
    assert k.isalpha(), k    # a LaTeX macro name may contain letters only
    M.append('\\newcommand{\\%s}{%s}' % (k, v))


def ck(name, cond, detail=''):
    if not cond:
        fail.append(name)
    print('  %-62s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro_opt(name):
    """The value if the layer defines it, else None.  Used where the point of
    the check is that a macro is NOT published any more."""
    try:
        return macro(name)
    except SystemExit:
        return None


def macro(name):
    """One macro's value out of the frozen layer, by name.  LAST definition
    wins: the retirement rounds alias superseded names, so a first-match
    reader returns the stale value."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('cover_v412: macro %s not found' % name)
    return v


def sci(x, sf=2):
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sf - 1, x / 10.0 ** e, e)


def union(iv):
    """Merged disjoint intervals of a list of (lo, hi) pairs.  min/max on the
    pair, because a descending spectral window writes its edges reversed."""
    out = []
    for a, b in sorted((min(x, y), max(x, y)) for x, y in iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def total(iv):
    return sum(b - a for a, b in iv)


# ---------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
import epochs_r14 as _ep    # the ONE determination of a block's epoch
MJD = _ep.EPOCHS            # measured where one survives, stored elsewhere
STACK = [json.loads(l) for l in
         open(os.path.join(HERE, 'stack_v408', 'stack6_result.jsonl'))]

CLA = [r for r in CAT if r['search_class'] == 'A']
CLB = [r for r in CAT if r['search_class'] == 'B']
assert len(CLA) + len(CLB) == len(CAT), 'a window is in neither class'


def edges(rows):
    return [(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in rows]


def summed(rows):
    return sum(abs(float(r['fhi_GHz']) - float(r['flo_GHz'])) for r in rows)


# =================================================== 1. the two definitions
U_A, U_B, U_ALL = (total(union(edges(s))) for s in (CLA, CLB, CAT))
S_A, S_B, S_ALL = (summed(s) for s in (CLA, CLB, CAT))
LO_A = min(min(a, b) for a, b in edges(CLA))
HI_A = max(max(a, b) for a, b in edges(CLA))
LO_B = min(min(a, b) for a, b in edges(CLB))
HI_B = max(max(a, b) for a, b in edges(CLB))

# ============================================ 2. the confirmation coverage
BYSYS = collections.defaultdict(list)
for r in CLA:
    BYSYS[r['system_id']].append(r)


def confirmable(rows, sep):
    """The frequency intervals of ONE system covered by two execution blocks
    more than `sep` days apart.  Evaluated on the interval boundaries, so a
    partial overlap counts only over the part that overlaps.  Same
    construction as the recurrence generator, which is why the system counts
    below are asserted against its published macros rather than re-derived."""
    iv = [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
           max(float(r['flo_GHz']), float(r['fhi_GHz'])), r['eb'])
          for r in rows]
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    keep = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        # ★★★ ROUND 14: measured separations, through epochs_r14.  See the
        # same substitution in recur_v411.py, whose counts C5 asserts against.
        if _ep.separated([e for a, b, e in iv if a <= mid <= b], sep):
            keep.append([pts[i], pts[i + 1]])
    return union(keep)


CONF = {}
for sep, tag in ((SEP_DAY, 'Day'), (SEP_YR, 'Yr')):
    pooled, nsys, persys = [], 0, 0.0
    for s, rows in BYSYS.items():
        d = confirmable(rows, sep)
        pooled += [tuple(x) for x in d]
        persys += total(d)
        if d:
            nsys += 1
    CONF[tag] = dict(iv=union(pooled), ghz=total(union(pooled)),
                     nsys=nsys, persys=persys)

# C_conf(nu) itself.  Computed on the interval boundaries rather than on a
# grid: the Class A union is 47.7 GHz spread over 759, so any grid coarse
# enough to be cheap loses islands, and a check bounded by a gridded island
# count is a check that cannot fail.
def cconf_profile(sep):
    """(frequency, number of systems) for the confirmable support, as a list
    of (lo, hi, n) runs -- exact, not gridded, so no island can be lost."""
    per = {}
    for s, rows in BYSYS.items():
        per[s] = confirmable(rows, sep)
    pts = sorted({x for iv in per.values() for a, b in iv for x in (a, b)})
    runs = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        n = sum(1 for iv in per.values()
                if any(a <= mid <= b for a, b in iv))
        if n:
            runs.append((pts[i], pts[i + 1], n))
    return runs


RUNS_D = cconf_profile(SEP_DAY)
NMAX_D = max(n for _, _, n in RUNS_D)
NUMAX_D = [0.5 * (a + b) for a, b, n in RUNS_D if n == NMAX_D][0]

# ======================================================== 3. the stack
PXCAT = [r for r in CAT if r['star_name'] == 'Proxima Cen']
PX_EB_CENSUS = {r['eb'] for r in PXCAT}
PXG = min((r for r in STACK if r['skey'] == 'Proxima Cen'),
          key=lambda x: x['eirp_stack_W'])
GROUPS = [g for g in json.load(open(os.path.join(
    HERE, 'stack_v408', 'groups3.json'))) if g['skey'] == 'Proxima Cen']
PXGRP = max(GROUPS, key=lambda g: g['n_block'])
PX_EB_STACK = {re.search(r'(A002_X[0-9a-f]+_X[0-9a-f]+)_spw', p).group(1)
               for p in PXGRP['paths']}
PX_EB_EXT = PX_EB_STACK - PX_EB_CENSUS

SQ_NEFF = math.sqrt(PXG['n_eff'])
# madZ is the measured noise scale of the stacked spectrum in units of the
# inverse-variance prediction.  The realised gain is sqrt(N_eff)/madZ.
NOISE_REAL = 1.0 / PXG['madZ']

# which of the stacked stars are primary-census stars
def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


SYSOF = {norm(r['star_name']): r['system_id'] for r in CAT}
SKEYS = sorted({r['skey'] for r in STACK})
IN_CENSUS = [s for s in SKEYS if norm(s) in SYSOF]
OUT_CENSUS = [s for s in SKEYS if norm(s) not in SYSOF]
STK_SYS = {SYSOF[norm(s)] for s in IN_CENSUS}

# ======================================================== 4. the beam
B_D = float(macro('BenchDiam'))
B_NU = float(macro('BenchFreqGHz')) * 1e9
B_ETA = float(macro('BenchEta'))
GAIN = B_ETA * (math.pi * B_D * B_NU / C_MS) ** 2
OMEGA = 4.0 * math.pi / GAIN                       # sr
BEAM_ARCSEC = math.degrees(math.sqrt(4.0 * OMEGA / math.pi)) * 3600.0
SKYFRAC = OMEGA / (4.0 * math.pi)

# ---------------------------------------------------------------- checks
print('assertions')
_v = U_A if DRIVE != 1 else U_A + 1.0
ck('C1 the Class A and whole-survey union bandwidths are the published ones',
   abs(_v - float(macro('DnuA'))) < 0.05
   and abs(U_ALL - float(macro('DnuAB'))) < 0.05,
   'A %.3f (%s), A+B %.3f (%s) GHz'
   % (U_A, macro('DnuA'), U_ALL, macro('DnuAB')))

_v = S_ALL if DRIVE != 2 else S_ALL * 2
ck('C2 summed window bandwidth over union reproduces the published ratio',
   abs(_v / U_ALL - float(macro('GrossOverUnion'))) < 0.05,
   'summed %.1f / union %.1f = %.2f (%s)'
   % (S_ALL, U_ALL, S_ALL / U_ALL, macro('GrossOverUnion')))

# The title's range must be the span of BOTH classes.  It is the Class B
# windows that reach lower than any Class A one, which is exactly why the
# title's lower edge disagrees with the abstract's -- so the Class B edge has
# to be stated.  Driving this the wrong way asserts the Class A edge sets it.
_v = LO_B if DRIVE != 3 else LO_A
# ★ 2026-10-07: THIS READ `\SurvFreqHi` AND THE UPPER EDGE IT CHECKS IS A
# CLASS A ONE.  That was harmless while the title printed the union span;
# once the title moved to the Class A range (R2-13) `\SurvFreqHi` lost its
# last use site, `retire_macros.py` would have deleted it at the end of the
# build, and this line would then have done `int(None)` on the next clean
# regeneration -- a generator brought down by the retirement of a macro it
# reads, which is the fourth time that shape has bitten this build.  The
# durable fix is to compare the Class A edge against the Class A macro.
ck('C3 the title span is both classes, and its lower edge is Class B',
   round(_v) == int(macro('SurvFreqLo'))
   and round(HI_A) == int(macro('SurvFreqHiA')) and LO_B < LO_A,
   'B %.3f-%.3f, A %.3f-%.3f, published low %s, Class A high %s'
   % (LO_B, HI_B, LO_A, HI_A, macro('SurvFreqLo'), macro('SurvFreqHiA')))

_v = CONF['Day']['ghz'] if DRIVE != 4 else U_A + 1.0
ck('C4 confirmation coverage is a strict subset of the searched union',
   CONF['Yr']['ghz'] < _v < U_A,
   '>1 yr %.3f < >1 d %.3f < searched %.3f GHz'
   % (CONF['Yr']['ghz'], CONF['Day']['ghz'], U_A))

_v = CONF['Day']['nsys'] if DRIVE != 5 else CONF['Day']['nsys'] + 1
ck('C5 the confirmable system counts are the recurrence section\'s own',
   _v == int(macro('RcConfSysDay'))
   and CONF['Yr']['nsys'] == int(macro('RcConfSysYr'))
   and len(BYSYS) == int(macro('NSysClassA'))
   and len(CLA) == int(macro('NWinA')),
   '%d of %d systems >1 d, %d >1 yr; %d Class A windows'
   % (CONF['Day']['nsys'], len(BYSYS), CONF['Yr']['nsys'], len(CLA)))

# The 181.5/79.7/17.8 family is the quantity the recurrence subsection has
# been calling coverage: the PER-SYSTEM union summed over systems, so a
# frequency covered toward six systems counts six times.  It is neither of
# the two defined quantities -- the referee guessed summed window bandwidth,
# which is 588.0 GHz for Class A -- and it must not be published under the
# word "coverage" at all.  So the check is twofold: it is a third quantity,
# and no bandwidth macro in the layer carries its value any longer.
_leftover = [n for n in ('RcConfGHzDay', 'RcConfGHzYr', 'RcConfPctDay',
                         'RcSearchGHz') if macro_opt(n) is not None]
if DRIVE == 6:
    _leftover = ['RcConfGHzDay']
ck('C6 the per-system sum is a third quantity and is no longer published as '
   'a bandwidth',
   abs(CONF['Day']['persys'] - CONF['Day']['ghz']) > 1.0
   and abs(CONF['Day']['persys'] - S_A) > 1.0 and not _leftover,
   'per-system %.2f vs union %.2f vs summed window %.1f GHz; still '
   'published: %s' % (CONF['Day']['persys'], CONF['Day']['ghz'], S_A,
                      _leftover or 'none'))

_v = OMEGA * GAIN if DRIVE != 7 else 1.0
ck('C7 the beam solid angle is read off the published gain, not a second '
   'convention',
   abs(_v - 4.0 * math.pi) < 1e-9
   and abs(GAIN / float(macro('BenchGain').replace(r'\times10^{', 'e')
                        .rstrip('}')) - 1.0) < 0.02,
   'G %.4g (%s), Omega %.3g sr, 1 part in %.3g of the sky'
   % (GAIN, macro('BenchGain'), OMEGA, 1.0 / SKYFRAC))

_v = len(PX_EB_STACK) if DRIVE != 8 else len(PX_EB_CENSUS)
ck('C8 Proxima\'s stack is the census blocks plus the extension blocks, and '
   'the census part is the number the systems table prints',
   _v == len(PX_EB_CENSUS) + len(PX_EB_EXT)
   and len(PX_EB_CENSUS & PX_EB_STACK) == len(PX_EB_CENSUS)
   and len(PX_EB_STACK) == PXG['N'] == int(macro('StkProxN')),
   '%d census + %d extension = %d stacked (StkProxN %s)'
   % (len(PX_EB_CENSUS), len(PX_EB_EXT), len(PX_EB_STACK),
      macro('StkProxN')))

_v = SQ_NEFF * NOISE_REAL if DRIVE != 9 else SQ_NEFF
ck('C9 the gain above sqrt(N_eff) is the noise realisation and nothing else',
   abs(_v - PXG['gain_real_vs_best']) < 1e-6
   and abs(PXG['gain_real_vs_best']
           - float(macro('StkProxGain'))) < 0.005,
   'sqrt(N_eff) %.4f x 1/madZ %.4f = %.4f (published %s)'
   % (SQ_NEFF, NOISE_REAL, SQ_NEFF * NOISE_REAL, macro('StkProxGain')))

_v = len(SKEYS) if DRIVE != 10 else len(IN_CENSUS)
ck('C10 the stacked stars are not all census stars, and the census ones are '
   'fewer systems than stars',
   _v == len(IN_CENSUS) + len(OUT_CENSUS) == int(macro('StkNStar'))
   and len(OUT_CENSUS) > 0 and len(STK_SYS) <= len(IN_CENSUS),
   '%d stacked = %d census stars (%d systems) + %d outside the census'
   % (len(SKEYS), len(IN_CENSUS), len(STK_SYS), len(OUT_CENSUS)))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('cover_v412: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ---------------------------------------------------------------- macros
# -- the two definitions
m('CvUnionA', '%.1f' % U_A)
m('CvUnionB', '%.1f' % U_B)
m('CvSumA', '%.0f' % S_A)
m('CvSumB', '%.0f' % S_B)
m('CvSumAll', '%.0f' % S_ALL)
m('CvVisitsA', '%.1f' % (S_A / U_A))
m('CvFreqLoB', '%.1f' % LO_B)
m('CvFreqHiB', '%.1f' % HI_B)
# -- confirmation coverage
m('CvConfGHzDay', '%.1f' % CONF['Day']['ghz'])
m('CvConfGHzYr', '%.1f' % CONF['Yr']['ghz'])
m('CvConfPctDay', '%.0f' % (100.0 * CONF['Day']['ghz'] / U_A))
m('CvConfPctYr', '%.0f' % (100.0 * CONF['Yr']['ghz'] / U_A))
m('CvConfNMaxDay', '%d' % NMAX_D)
m('CvConfNuMaxDay', '%.0f' % NUMAX_D)
# -- the benchmark beam
m('BmOmegaSr', sci(OMEGA))
m('BmArcsec', '%.0f' % BEAM_ARCSEC)
m('BmSkyFrac', sci(SKYFRAC))
# -- the stack reconciliation
m('SxProxEbCensus', '%d' % len(PX_EB_CENSUS))
m('SxProxEbExt', '%d' % len(PX_EB_EXT))
m('SxProxSqrtNeff', '%.2f' % SQ_NEFF)
m('SxProxNoiseReal', '%.2f' % NOISE_REAL)
m('SxProxNChan', '%d' % PXG['nchan_common'])
m('SxStkStarCensus', '%d' % len(IN_CENSUS))
m('SxStkSysCensus', '%d' % len(STK_SYS))
m('SxStkStarOutside', '%d' % len(OUT_CENSUS))

# ★ Queue entry 57 (integrator): the PRODUCTION name must be a literal.
#   `macrosyn`'s SOURCE clause searches the .py files for the filename as a
#   literal string, so a name built with '%s' made it report
#   `survey_numbers_round185.tex is typeset but no .py in this folder names
#   it, so nothing can rebuild it` -- a false alarm on the one clause that
#   exists to catch a frozen macro file nothing can regenerate.  Only the
#   drive branch is formatted.
OUT = os.path.join(HERE, 'survey_numbers_round185.tex' if SUF == ''
                   else 'survey_numbers_round185%s.tex' % SUF)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by cover_v412.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    fh.write('\n'.join(sorted(M)) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(OUT), len(M)))

# the measurement, for the report and for the figure's own cross-check
json.dump(dict(union=dict(A=U_A, B=U_B, all=U_ALL),
               summed=dict(A=S_A, B=S_B, all=S_ALL),
               span=dict(A=[LO_A, HI_A], B=[LO_B, HI_B]),
               conf={k: dict(ghz=v['ghz'], nsys=v['nsys'],
                             persys=v['persys'], iv=v['iv'])
                     for k, v in CONF.items()},
               cconf_day=RUNS_D,
               prox=dict(eb_census=sorted(PX_EB_CENSUS),
                         eb_ext=sorted(PX_EB_EXT),
                         sqrt_neff=SQ_NEFF, noise_real=NOISE_REAL,
                         gain=PXG['gain_real_vs_best'],
                         nchan=PXG['nchan_common']),
               stacked=dict(census=IN_CENSUS, outside=OUT_CENSUS,
                            systems=sorted(STK_SYS)),
               beam=dict(gain=GAIN, omega_sr=OMEGA, arcsec=BEAM_ARCSEC,
                         skyfrac=SKYFRAC)),
          open(os.path.join(HERE, 'cover_v412%s.json' % SUF), 'w'), indent=1)
print('wrote cover_v412%s.json' % SUF)
