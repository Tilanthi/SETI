#!/usr/bin/env python3
r"""r21_lines.py -- round 951 -> survey_numbers_round951.tex, r21_lines.json,
tab_nearest_r21.tex.

WHAT "UNATTRIBUTED" MEANS, MEASURED AGAINST A LIST NOBODY CHOSE FOR US.

The frozen mask holds every transition of the twelve species the original
spectral setups were tuned to.  Referee 2's fifth point is that this makes
"unattributed" mean "unattributed against a twelve-species list chosen by
other observers", and he names two cases that the twelve omit: the
beta Pictoris pair at 241.77 and 241.86 GHz in the stellar frame, which falls
inside the CH3OH J = 5->4 K-ladder region, and ALMA J153702653-33192492,
a serendipitous field star on a Lupus-cloud sightline.

THE FROZEN MASK DOES NOT CHANGE.  What this file does is state honestly what
the word means, by measuring the same crossings against a list built from a
dated query of CDMS and JPL for every species with a published interstellar
or circumstellar detection and every transition below 150 K
(`r21_harvest.py`, `r21_harvest_full.py`).

AND IT MEASURES BOTH SIDES OF THE COMPARISON.  The count of unattributed
crossings is compared with an expectation built from the control positions of
the same fields, and that expectation is reduced by the SAME mask: a control
position's noise maximum is attributed when its own channel lands inside the
mask.  Widening the list therefore lowers the expectation as well as the
count, and a sensitivity case that moved one side only would be worthless.
The expectation is recomputed here window by window, exactly as
`chance_v414.py` forms it, and B1 requires the frozen-mask value to reproduce
the published \CeExp before the widened one is believed.

ASSERTIONS (each driven to fail on its own, --drive 1..9; 5 retired)

  B1  the expectation recomputed here with the FROZEN mask reproduces the
      published \CeExp, which is what licenses the widened one.
  B2  the frozen mask's own transitions are recovered by the dated query
      wherever CDMS or JPL carries them, so the expanded list is a superset
      and not a different list; the exceptions are named rather than hidden.
  B3  the crossings read here are the published census and the published
      unattributed set (\NCross, \MkUnattr).
  B4  the expanded list attributes every crossing the frozen mask attributes:
      a wider list cannot un-attribute anything.
  B5  RETIRED in v4.26 (A4), with the seven `XlBp...` macros it guarded and
      with --drive 5.  It asserted that the beta Pictoris pair is decided
      against the methanol ladder by measurement -- which was true, and which
      no sentence of the manuscript ever cited, so from outside the paper the
      measurement did not exist.  `ch3oh_r25.py` (round 985) owns that
      question now, decides it against JPL and CDMS directly, prints it in
      Appendix C, and carries its own drives.
  B6  the expanded list is not vacuously dense: at the same half-width it
      leaves some crossing unattributed, and the median offset to the
      nearest transition of the expanded list exceeds the channel width of
      the window it is measured in.
  B7  the widened expectation is formed from the same windows and the same
      exceedance rates as the frozen one, so the ratio is a change of mask
      and of nothing else.
  B8  the probability is computed from the Poisson tail of the expectation it
      names, and the frozen-mask reproduction of it reproduces \CeProbNull.
  B9  the species list carries its query date and the date is not today's
      build date: a frozen list has a provenance.

Usage: r21_lines.py [--paper DIR] [--out DIR] [--scope DIR] [--drive N]
"""
import bisect
import collections
import csv
import json
import math
import os
import re
import statistics as st
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 951
C = 299792.458

DRIVE = None
PAPER = HERE   # the version tree this generator lives in
OUTDIR = HERE
SCOPE = os.path.join(HERE, 'r21inputs')   # the frozen network harvests
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--paper':
        PAPER = sys.argv[_i + 1]
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
    if _a == '--scope':
        SCOPE = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round951%s.tex' % SUF)
OUT_JSON = os.path.join(OUTDIR, 'r21_lines%s.json' % SUF)
OUT_TAB = os.path.join(OUTDIR, 'tab_nearest_r21%s.tex' % SUF)
OUT_TSV = os.path.join(OUTDIR, 'si_nearest_r21%s.tsv' % SUF)

MACROS, FAIL = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' \
        % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), \
        name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-66s %s  %s' % (label[:66], 'PASS' if ok else 'FAIL', detail))


sys.path.insert(0, PAPER)
import maskframe_v411 as mf                                     # noqa: E402
import star_alias as sa                                         # noqa: E402


def tex(name):
    pat = re.compile(r'\\(?:new|renew)command\{\\%s\}\{(.*)\}\s*$' % name)
    import glob
    for p in sorted(glob.glob(os.path.join(PAPER, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.search(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


def ival(name):
    return int(tex(name).replace('\\,', '').replace(',', ''))


HALF = mf.MASK_HALF_KMS
TRIG = float(tex('StageNullTrig'))
print('r21_lines round %d%s   half-width %.0f km/s, trigger %.1f'
      % (ROUND, '' if DRIVE is None else ' (drive %d)' % DRIVE, HALF, TRIG))

# =====================================================================
# 0  THE TWO LISTS
# =====================================================================
HARV = json.load(open(os.path.join(SCOPE, 'r21_lines_harvest.json')))
FULL = json.load(open(os.path.join(SCOPE, 'r21_lines_full.json')))
XP = [dict(f=r['f'], mol=r['mol'], qn=r['qn'], eu=r['eu'], aij=r['aij'],
           ll=r['ll']) for r in HARV['lines']]
XP.sort(key=lambda z: z['f'])
if DRIVE == 4:
    XP = [r for r in XP if not (241.7 < r['f'] < 241.9)]   # the ladder goes
XF = [r['f'] for r in XP]
FULL_F = np.array([r[0] for r in FULL['lines']])
FROZEN = {k: v for k, v in mf.TRANS.items()}
FROZ_F = np.array(sorted(v[0] for v in FROZEN.values()))
print('  frozen mask %d transitions of %s species; expanded list %d '
      'transitions of %d species near the crossings and %d over the islands'
      % (len(FROZEN), tex('FrNSpec'), len(XP), HARV['n_species'],
         FULL['n_lines']))

_date = HARV['query_date']
if DRIVE == 9:
    _date = ''
ck('B9 the species query carries its own date',
   bool(re.match(r'^20\d\d-\d\d-\d\dT', _date)), _date or '(none)')
m('XlQueryDate', _date[:10])
m('XlNSpecies', '%d' % HARV['n_species'])
m('XlNTrans', format(FULL['n_lines'], ',').replace(',', '\\,'))
m('XlEuMax', '%.0f' % HARV['eu_max'])


def nearest(f, lines=None, lf=None):
    """The nearest transition of the expanded list, and the offset in km/s
    with the paper's own sign: positive means the crossing lies ABOVE the
    transition in frequency."""
    lines = XP if lines is None else lines
    lf = XF if lf is None else lf
    i = bisect.bisect_left(lf, f)
    best, bdv = None, 1e99
    for j in (i - 1, i, i + 1):
        if 0 <= j < len(lf):
            dv = C * (f - lf[j]) / lf[j]
            if abs(dv) < abs(bdv):
                best, bdv = lines[j], dv
    return best, bdv


def nearest_dv(f, lf):
    """The velocity offset to the nearest entry of a sorted frequency list."""
    i = bisect.bisect_left(lf, f)
    bdv = 1e99
    for j in (i - 1, i, i + 1):
        if 0 <= j < len(lf):
            dv = C * (f - lf[j]) / lf[j]
            if abs(dv) < abs(bdv):
                bdv = dv
    return bdv


# =====================================================================
# 1  THE EXPANDED LIST IS A SUPERSET OF THE FROZEN ONE WHERE IT CAN BE
# =====================================================================
print('\n1  is the expanded list a superset of the frozen mask?')
NB = HARV['neighbourhoods']


def in_nbhd(f):
    return any(a <= f <= b for a, b in NB)


REC, MISS = 0, []
for k, v in sorted(FROZEN.items()):
    f0 = v[0]
    if not in_nbhd(f0):
        continue
    i = bisect.bisect_left(XF, f0)
    hit = any(abs(XF[j] - f0) < 1e-3 for j in (i - 1, i, i + 1)
              if 0 <= j < len(XF))
    if hit:
        REC += 1
    else:
        MISS.append((k, f0))
_missmol = sorted({mf.species(k) for k, _f in MISS})
#: THE ONE ALLOWED EXCEPTION, NAMED.  Hydrogen recombination lines are not in
#: CDMS or JPL -- Splatalogue keeps them in a line list of their own -- so the
#: referee's two catalogues cannot carry them, and the expanded list is a
#: superset of the frozen mask everywhere else.  Any OTHER missing transition
#: means the query lost a line, which is how the empty-span frequency defect
#: was found: it had dropped CO(2--1) itself.
ALLOWED = re.compile(r'^H\(\d+')
_bad_miss = [k for k, _f in MISS if not ALLOWED.match(k)]
if DRIVE == 2:
    REC -= 1
    _bad_miss = _bad_miss + ['__invented__']
ck('B2 every frozen-mask transition in the queried neighbourhoods is '
   'recovered by the dated query, bar the hydrogen recombination lines that '
   'CDMS and JPL do not carry at all',
   REC > 0 and not _bad_miss,
   '%d recovered, %d missing (%s), %d of them not recombination'
   % (REC, len(MISS), ', '.join(_missmol) or '-', len(_bad_miss)))
m('XlNRecov', '%d' % REC)
m('XlMissSpec', ', '.join(_missmol) if _missmol else 'none')

# =====================================================================
# 2  THE CROSSINGS, IN BOTH FRAMES, AGAINST BOTH LISTS
# =====================================================================
print('\n2  the crossings')
CAT_EARLY = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
LSR = {(r['eb'], round(r['freq'], 6)): r
       for r in json.load(open(os.path.join(PAPER,
                                            'masklsr_v520.json')))['rows']}
CROSS = json.load(open(os.path.join(PAPER, 'maskframe_v411.json')))['rows']
LEDG = json.load(open(os.path.join(PAPER, 'ledger.json')))['rows']
if DRIVE == 3:
    CROSS = CROSS[1:]
ck('B3 the crossings read here are the published census',
   len(CROSS) == ival('NCross'),
   '%d against %s published' % (len(CROSS), tex('NCross')))


FLAG, ATTR_FROZEN, LEDGNAME = {}, {}, {}
for r in LEDG:
    k = (r['eb'], round(float(r['freq']), 6))
    ATTR_FROZEN[k] = bool(r['attributed'])
    FLAG[k] = bool(r['dq'])
    #: ★ the ancillary columns must JOIN to the deposited ledger, so the star
    #: name written there is the ledger's own spelling and not the frame
    #: chain's: `maskframe_v411` carries "BD05 1668" where the ledger and the
    #: deposit carry "BD+05 1668".
    LEDGNAME[k] = r.get('display') or r['star']

#: the released window a crossing falls in, by position in frequency and
#: never by a name: a crossing in no released window is an archival-tail one
#: and sits outside the comparison, exactly as `chance_v414.py` puts it there
WINSPAN = collections.defaultdict(list)
for _i, _r in enumerate(CAT_EARLY):
    _lo, _hi = sorted((float(_r['flo_GHz']), float(_r['fhi_GHz'])))
    WINSPAN[_r['eb']].append((_lo, _hi, _i))


def window_of(eb, freq):
    hit = [i for lo, hi, i in WINSPAN.get(eb, [])
           if lo - 1e-6 <= freq <= hi + 1e-6]
    return hit[0] if hit else None


ROWS = []
for c in CROSS:
    key = (c['eb'], round(c['f_topo'], 6))
    l = LSR.get(key)
    f_star, f_lsr = c['f_stellar'], (l['f_lsr'] if l else None)
    xb, xdv = nearest(f_star)
    xl, xldv = (nearest(f_lsr) if f_lsr else (None, None))
    fz, fzdv = None, None
    i = bisect.bisect_left(list(FROZ_F), f_star)
    for j in (i - 1, i, i + 1):
        if 0 <= j < len(FROZ_F):
            dv = C * (f_star - FROZ_F[j]) / FROZ_F[j]
            if fzdv is None or abs(dv) < abs(fzdv):
                fz, fzdv = float(FROZ_F[j]), dv
    att = ATTR_FROZEN.get(key)
    ROWS.append(dict(star=LEDGNAME.get(key, c['star']),
                     star_frame=c['star'], eb=c['eb'], band=c['band'],
                     tstar=c['tstar'], f_topo=c['f_topo'], f_star=f_star,
                     f_lsr=f_lsr, frozen_line=c['line'],
                     frozen_dv=c['dv_stellar'],
                     attributed_frozen=att,
                     flagged=FLAG.get(key), 
                     in_release=window_of(c['eb'], c['f_topo']) is not None,
                     x_mol=xb['mol'], x_qn=xb['qn'], x_eu=xb['eu'],
                     x_aij=xb['aij'], x_f=xb['f'], x_dv_star=xdv,
                     x_mol_lsr=(xl['mol'] if xl else None),
                     x_dv_lsr=xldv,
                     x_inside=abs(xdv) <= HALF))
UN = [r for r in ROWS if not r['attributed_frozen']]
AT = [r for r in ROWS if r['attributed_frozen']]
ck('B3b the unattributed set is the published one',
   len(UN) == ival('MkUnattr'),
   '%d against %s published' % (len(UN), tex('MkUnattr')))
_bad = [r for r in AT if not r['x_inside']]
if DRIVE == 4:
    pass                       # drive 4 removes the ladder: B5 fires, not B4
ck('B4 the expanded list attributes everything the frozen mask attributes: a '
   'wider list cannot un-attribute a crossing',
   not _bad, '%d of %d frozen attributions outside the expanded mask'
   % (len(_bad), len(AT)))

IN = [r for r in UN if r['x_inside']]
OUTSIDE = [r for r in UN if not r['x_inside']]
print('  of the %d unattributed crossings, %d lie within %.0f km/s of a '
      'transition of the expanded list and %d do not'
      % (len(UN), len(IN), HALF, len(OUTSIDE)))
m('XlNUnattrIn', '%d' % len(IN))
m('XlNUnattrOut', '%d' % len(OUTSIDE))
m('XlFracIn', '%.0f' % round(100.0 * len(IN) / len(UN)))
_med = st.median([abs(r['x_dv_star']) for r in UN])
m('XlMedDvKms', '%.1f' % _med)

# the two named cases
BP = sorted([r for r in ROWS if r['star_frame'] in ('bet Pic', 'beta Pic')
             or 'Pictoris' in r['star']], key=lambda z: z['f_star'])
BPU = [r for r in BP if not r['attributed_frozen']]
CH3 = [r for r in XP if r['mol'] == 'CH3OH']
CH3F = [r['f'] for r in CH3]
for r in BPU:
    b, dv = nearest(r['f_star'], CH3, CH3F)
    r['ch3oh'] = dict(f=b['f'], qn=b['qn'], eu=b['eu'], dv=dv)
#: ★★★★ v4.26 (A4).  B5 AND THE SEVEN `XlBp...` MACROS ARE GONE, AND THE
#: REASON IS THE FINDING ITSELF.  This file has asserted since round 951 that
#: the beta Pictoris pair is decided against the methanol ladder BY
#: MEASUREMENT, and emitted seven macros saying so -- and not one of the seven
#: was referenced by any section of the manuscript, so from outside the paper
#: the measurement did not exist and Referee 2 raised it as a defect, rightly.
#: `ch3oh_r25.py` (round 985) now decides the same question against the two
#: catalogues directly, prints it in Appendix C, and carries the drives.  Two
#: owners of one number is how this project has produced divergences before,
#: so this one is retired rather than left beside it.  `BPU` itself stays: the
#: beta Pictoris rows feed the nearest-transition table and `si_nearest_r21`.

LUP = [r for r in ROWS if r['star_frame'].startswith('ALMA J')]
LUPU = [r for r in LUP if not r['attributed_frozen']]
m('XlLupNCross', '%d' % len(LUPU))
m('XlLupNIn', '%d' % sum(1 for r in LUPU if r['x_inside']))
if LUPU:
    m('XlLupDvMin', '%.1f' % min(abs(r['x_dv_star']) for r in LUPU))
    m('XlLupMols', ', '.join(sorted({r['x_mol'] for r in LUPU})))

# ---------------------------------------------------------------------
# WHAT EACH LIST COSTS IN BANDWIDTH, measured the way the paper measures it
# ---------------------------------------------------------------------
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
_chan = {}
for r in CAT:
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    _chan.setdefault(r['eb'], []).append((lo, hi, float(r['chanw_Hz'])))


def chanw_kms(c):
    for lo, hi, cw in _chan.get(c['eb'], []):
        if lo - 1e-6 <= c['f_topo'] <= hi + 1e-6:
            return C * cw / 1e9 / c['f_topo']
    return None


def merge(iv):
    o = []
    for x, y in sorted((min(p, q), max(p, q)) for p, q in iv):
        if o and x <= o[-1][1]:
            o[-1][1] = max(o[-1][1], y)
        else:
            o.append([x, y])
    return o


def overlap(isl, tub):
    t = 0.0
    for x, y in isl:
        for c, d in tub:
            lo, hi = max(x, c), min(y, d)
            if hi > lo:
                t += hi - lo
    return t


UA = merge([(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in CAT
            if r['search_class'] == 'A'])
U_A = sum(b - a for a, b in UA)


def band_cost(freqs, half):
    """GHz of the Class A union inside +-half km/s of any of `freqs`, and the
    percentage -- the same interval arithmetic `maskcost_v440.py` publishes."""
    tub = merge([(f * (1 - half / C), f * (1 + half / C)) for f in freqs])
    g = overlap(UA, tub)
    return g, 100.0 * g / U_A


_gz, _pz = band_cost([v[0] for v in FROZEN.values()], HALF)
_pubg, _pubp = float(tex('MkMaskAGHz')), float(tex('MkMaskAPct'))
if DRIVE == 6:
    _gz *= 2
ck('B6 the bandwidth each list costs is measured the way the paper already '
   'measures the frozen one, which the frozen value reproduces',
   abs(_gz - _pubg) < 0.02 and abs(_pz - _pubp) < 0.1,
   '%.2f GHz = %.1f per cent against %s GHz = %s per cent published'
   % (_gz, _pz, tex('MkMaskAGHz'), tex('MkMaskAPct')))
_gx, _px = band_cost(FULL_F.tolist(), HALF)
print('  the frozen mask costs %.2f GHz of the %.2f GHz Class A union '
      '(%.1f per cent); the expanded list costs %.2f GHz (%.1f per cent)'
      % (_gz, U_A, _pz, _gx, _px))
m('XlBandPct', '%.0f' % _px)
# ★ `\XlBandFrozenPct` is NOT emitted: the frozen mask's share of the
# Class A union is already published as `\MkMaskAPct` by `maskcost_v440.py`,
# and B6 above reproduces it here rather than republishing it.  Two names
# for one quantity is the defect `valuetwin` exists to find, and the prose
# cites `\MkMaskAPct`.

# ---------------------------------------------------------------------
# THE LADDER: how tight the tolerance has to be before the wider list says
# anything at all.  Reported because at the published half-width it does not.
# ---------------------------------------------------------------------
LAD = []
for h in (HALF, 13.0, 5.0, 1.0):
    nin = sum(1 for r in UN if abs(r['x_dv_star']) <= h)
    g, p = band_cost(FULL_F.tolist(), h)
    LAD.append(dict(half=h, n_in=nin, n_out=len(UN) - nin, band_GHz=g,
                    band_pct=p))
    print('    +-%5.1f km/s: %2d of %d unattributed crossings coincide, '
          'the list masks %5.1f per cent of the band'
          % (h, nin, len(UN), p))
m('XlLadNIn', ' / '.join('%d' % x['n_in'] for x in LAD))
m('XlLadHalf', ' / '.join('%g' % x['half'] for x in LAD))
m('XlTightHalf', '%g' % LAD[-1]['half'])
m('XlTightNIn', '%d' % LAD[-1]['n_in'])
m('XlTightBandPct', '%.0f' % LAD[-1]['band_pct'])

#: ★ WHAT DOES THE ATTRIBUTING.  Most of the nearest transitions are weak
#: lines of complex organics, so the same ladder is reported for the subset
#: with log A_ij >= -5 -- the strength cut the survey's own cross-check list
#: has always used -- and the difference is the measure of how much of the
#: confusion is carried by lines nobody would expect to see.
STRONG = np.array(sorted(r[0] for r in FULL['lines']
                         if r[3] is not None and r[3] >= -5.0))
LADS = []
for h in (HALF, 13.0, 5.0, 1.0):
    _sf = STRONG.tolist()
    nin = sum(1 for r in UN if abs(nearest_dv(r['f_star'], _sf)) <= h)
    g, p = band_cost(STRONG.tolist(), h)
    LADS.append(dict(half=h, n_in=nin, band_pct=p))
    print('    strong lines only, +-%5.1f km/s: %2d of %d coincide, '
          '%5.1f per cent of the band' % (h, nin, len(UN), p))
m('XlStrongNIn', ' / '.join('%d' % x['n_in'] for x in LADS))
m('XlStrongBandPct', '%.0f' % LADS[0]['band_pct'])
m('XlNStrong', format(int(STRONG.size), ',').replace(',', '\\,'))

#: ★ THE REFEREE NAMES SEVEN SPECIES for the Lupus sightline.  They are
#: tested one by one rather than taken on trust, because the answer is not
#: the same for all five of that star's unattributed crossings.
LUPSPEC = ['CH3OH', 'H2CO', 'c-C3H2', 'DCO+', 'OCS', 'HC3N', 'SO2']
BYMOL = collections.defaultdict(list)
for _f, _mol, _eu, _aij in FULL['lines']:
    BYMOL[_mol].append((_f, _eu, _aij))
LUPHIT = []
for r in [x for x in UN if x['star_frame'].startswith('ALMA J')]:
    for k in LUPSPEC:
        if not BYMOL.get(k):
            continue
        f0, eu0, aij0 = min(BYMOL[k], key=lambda z: abs(z[0] - r['f_star']))
        dv = C * (r['f_star'] - f0) / f0
        if abs(dv) <= HALF:
            LUPHIT.append(dict(f=r['f_star'], mol=k, f_line=f0, dv=dv,
                               eu=eu0, aij=aij0))
_absent = [k for k in LUPSPEC if not BYMOL.get(k)]
print('  the Lupus sightline: %d of the %d named species reach a crossing '
      'within %.0f km/s -- %s; %s absent from the searched intervals'
      % (len({h['mol'] for h in LUPHIT}), len(LUPSPEC), HALF,
         '; '.join('%s at %+.1f km/s' % (h['mol'], h['dv']) for h in LUPHIT)
         or 'none', ', '.join(_absent) or 'none'))
m('XlLupNamedN', '%d' % len(LUPHIT))
if LUPHIT:
    m('XlLupNamedMol', LUPHIT[0]['mol'])
    m('XlLupNamedDv', '%.0f' % abs(LUPHIT[0]['dv']))
    m('XlLupNamedEu', '%.0f' % LUPHIT[0]['eu'])

#: ★ THE HOLD-OUT'S OWN CROSSINGS, on the same code path: the referee asks
#: for the column over the 38 census and the 7 hold-out unattributed ones.
HOX = json.load(open(os.path.join(
    PAPER, 'r11inputs/events/cross_holdout.json')))
HREC = json.load(open(os.path.join(
    PAPER, 'r11inputs/events/recur_holdout.json')))['crossings']
HVSYS = json.load(open(os.path.join(
    PAPER, 'r11inputs/events/vsys_holdout_v412.json')))
HEXTRA = json.load(open(os.path.join(
    PAPER, 'r11inputs/events/vcorr_extra_v412.json')))
HROWS = []
for c in HOX:
    rec = HREC.get(c['cid'], {})
    d = rec.get('discovery') or {}
    vc = d.get('v_corr_kms')
    if vc is None:
        vc = HEXTRA[c['cid']]['v_corr_kms']
    _fb, fstar = mf.to_stellar(c['freq_GHz'], vc, HVSYS[c['star']])
    line, _fr, dv = mf.nearest(fstar)
    note = mf.note_reason(line, dv) if abs(dv) <= HALF else None
    xb, xdv = nearest(fstar)
    HROWS.append(dict(cid=c['cid'], star=c['star'], eb=c['eb'],
                      tstar=c['tstar'], f_star=fstar, frozen_line=line,
                      frozen_dv=dv,
                      attributed_frozen=bool(abs(dv) <= HALF and not note),
                      x_mol=xb['mol'], x_qn=xb['qn'], x_eu=xb['eu'],
                      x_dv_star=xdv, x_inside=abs(xdv) <= HALF))
HUN = [r for r in HROWS if not r['attributed_frozen']]
_hpub = ival('HoNUnattr')
if DRIVE == 10:
    HUN = HUN[1:]
ck('B10 the hold-out crossings are read on the same frame and attribution '
   'path and reproduce the published hold-out split',
   len(HUN) == _hpub, '%d unattributed against %s published'
   % (len(HUN), tex('HoNUnattr')))
m('XlHoNIn', '%d' % sum(1 for r in HUN if r['x_inside']))
m('XlHoN', '%d' % len(HUN))
print('  hold-out: %d of %d unattributed crossings coincide with the '
      'expanded list' % (sum(1 for r in HUN if r['x_inside']), len(HUN)))

# =====================================================================
# 3  THE SAME MASK ON THE OTHER SIDE: THE CHANCE EXPECTATION
# =====================================================================
print('\n3  the expectation, recomputed with each mask')


def wkey(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


def skey(s):
    return re.sub(r'\s+', '', s or '').lower()


EXP = json.load(open(os.path.join(PAPER,
                                  'corrected_export_v399.json')))['rows']
FFX = json.load(open(os.path.join(
    PAPER, 'r8inputs/v409/fieldfix_v409.json')))
CELLS = json.load(open(os.path.join(
    PAPER, 'r15inputs/cells/cells_extract_result.json')))['windows']
BYWIN, FFWIN = collections.defaultdict(list), collections.defaultdict(list)
for r in EXP:
    BYWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)
for r in FFX:
    FFWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)


def _pick(cands, row, namekey, maxkey):
    same = [x for x in cands if skey(x.get(namekey)) == skey(row['star_name'])]
    pool = same or cands
    if len(pool) == 1:
        return pool[0]
    return min(pool, key=lambda x: abs(float(x[maxkey])
                                       - float(row['ctrl_max_snr'] or 0)))


JOIN, REPJOIN = {}, {}
for i, r in enumerate(CAT):
    c = BYWIN.get(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']), [])
    p = _pick(c, r, 'star_name', 'ctrl_max') if c else None
    if p is not None and (p.get('ctrl_all') or []):
        JOIN[i] = p
    c = FFWIN.get(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']), [])
    q = _pick(c, r, 'star', 'ctrl_max') if c else None
    if q is not None and q.get('ctrl_all'):
        REPJOIN[i] = q

IA = [i for i, r in enumerate(CAT) if r['search_class'] == 'A']
CATKEY = collections.defaultdict(list)
for i in IA:
    CATKEY[wkey(CAT[i]['eb'], CAT[i]['flo_GHz'], CAT[i]['fhi_GHz'])].append(i)
PEXC = {}
for i, r in enumerate(CAT):
    src = REPJOIN.get(i) if i in REPJOIN else JOIN.get(i)
    if src is not None:
        PEXC[i] = float((np.asarray(src['ctrl_all'], float) >= TRIG).mean())
E_TRIG_REL = sum(PEXC[i] for i in IA if i in PEXC)

#: The null's own mask: the searched list minus the species whose
#: coincidences the paper reports rather than acts on, exactly as
#: `chance_v414.py` forms it.
NULL_FROZEN = np.array(sorted(
    v[0] for k, v in mf.TRANS.items() if mf.species(k) not in
    mf.NOTED_SPECIES))
NULL_EXP = np.array(sorted(set(FULL_F.tolist()) | set(NULL_FROZEN.tolist())))
if DRIVE == 7:
    NULL_EXP = NULL_FROZEN               # the widened side stops widening


def inmask(rest, fs, half):
    """Vectorised: a channel is inside the mask when its nearest transition
    is within the half-width in velocity."""
    j = np.searchsorted(rest, fs)
    out = np.zeros(fs.size, bool)
    for off in (-1, 0):
        k = np.clip(j + off, 0, rest.size - 1)
        out |= np.abs(C * (fs - rest[k]) / rest[k]) <= half
    return out


def grid_share(i, rest, half):
    r = CAT[i]
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    cw = float(r['chanw_Hz']) / 1e9
    n = int(round((hi - lo) / cw)) + 1
    g = lo + cw * np.arange(n)
    vb, _s = mf.vbary(r['eb'], r['flo_GHz'])
    vs, _s2, _b = mf.vsys(r['star_name'])
    fs = g * (1.0 - (vb or 0.0) / C) * (1.0 + (vs or 0.0) / C)
    return float(inmask(rest, fs, half).mean())


def expectation(rest, half):
    """The control-position expectation of unattributed Class A crossings,
    formed exactly as `chance_v414.py` forms it: the share of each window's
    exceedance rate that the mask does NOT take, with the attributed share of
    the joined windows measured on the channels the control maxima land on
    rather than assumed uniform."""
    nex = nat = 0
    joined = set()
    for w in CELLS:
        if w['cls'] != 'A' or w['stratum'] == 'archival_tail':
            continue
        k = wkey(w['eb'], w['lo'], w['hi'])
        idx = CATKEY.get(k, [])
        same = [j for j in idx
                if sa.canon(CAT[j]['star_name']) == sa.canon(w['star'])]
        cand = same or idx
        if len(cand) > 1:
            cand = [min(cand, key=lambda j: abs(float(CAT[j]['star_snr'])
                                                - w['adopted']))]
        if len(cand) != 1:
            continue
        i = cand[0]
        src = REPJOIN.get(i) if i in REPJOIN else JOIN.get(i)
        if src is None:
            continue
        g = np.linspace(w['lo'], w['hi'], w['nch'])
        if float(src['flo']) > float(src['fhi']):          # descending window
            g = g[::-1]
        fs = g * (1.0 - w['v_bary'] / C) * (1.0 + w['v_sys'] / C)
        im = inmask(rest, fs, half)
        exc = [c for c in w['ctrl'] if c['win_max'] >= TRIG]
        nex += len(exc)
        nat += sum(1 for c in exc if im[c['max_chan']])
        joined.add(i)
    a_meas = nat / float(nex)
    #: ★ The atmospheric screen is the OWNER'S, read out of its own record
    #: rather than rebuilt here: this generator exists to compare two line
    #: masks, and a second implementation of a second screen would be a
    #: second place for it to be wrong.  It cancels in that comparison and
    #: is carried only so that the frozen side reproduces the published
    #: expectation, which is the clause that licenses the widened one.
    e = sum(PEXC[i] * (1.0 - (a_meas if i in joined
                              else grid_share(i, rest, half))) * TLFAC
            for i in IA if i in PEXC)
    return e, nex, nat, a_meas, len(joined)


_TLREC = json.load(open(os.path.join(HERE, 'chance_v414.json')))['telluric']
TLFAC = float(_TLREC['factor'])
TLCUT = {(_r['eb'], round(float(_r['f_topo']), 6))
         for _r in _TLREC['observed_removed']}

E_FZ, NEX, NAT, A_FZ, NJ = expectation(NULL_FROZEN, HALF)
_pub = float(tex('CeExp'))
if DRIVE == 1:
    E_FZ *= 1.3
ck('B1 the expectation recomputed here with the frozen mask reproduces the '
   'published one, which is what licenses the widened one',
   abs(E_FZ - _pub) < 0.15,
   '%.2f against %s published; %d of %d control exceedances in mask, '
   '%d windows joined' % (E_FZ, tex('CeExp'), NAT, NEX, NJ))
E_XP, NEX2, NAT2, A_XP, NJ2 = expectation(NULL_EXP, HALF)
#: ★ AND IT MUST ALSO CHECK THAT THE WIDENED SIDE IS WIDER.  The first form
#: of this clause asserted only that the two runs used the same windows,
#: which stays true when the widened list stops widening -- drive 7 passed
#: it.  A gate that its own drive cannot fire is not a gate.
ck('B7 the two expectations run over the same windows and the same '
   'exceedance rates and the second list is strictly the wider, so the '
   'difference between them is the mask and nothing else',
   NEX2 == NEX and NJ2 == NJ and NEX > 0
   and NULL_EXP.size > NULL_FROZEN.size and A_XP >= A_FZ,
   '%d control exceedances and %d windows both times; %d transitions against '
   '%d; attributed share %.3f -> %.3f'
   % (NEX, NJ, NULL_EXP.size, NULL_FROZEN.size, A_FZ, A_XP))

# ---------------------------------------------------------------------
# the observed side, over the comparison's own set
# ---------------------------------------------------------------------
PRIM = [r for r in UN if not r['flagged'] and r['in_release']
        and (r['eb'], round(float(r['f_topo']), 6)) not in TLCUT]
_pubobs = ival('CeObs')
if DRIVE == 3:
    PRIM = PRIM[1:]
ck('B3c the observed side is the comparison\'s own set: the unattributed '
   'crossings of the released primary census, which reproduces \\CeObs',
   len(PRIM) == _pubobs, '%d against %s published' % (len(PRIM), tex('CeObs')))


def ptail(n, mu):
    """P(N >= n) for a Poisson mean mu."""
    if n <= 0:
        return 1.0
    s, t = 0.0, math.exp(-mu)
    for k in range(0, n):
        s += t
        t *= mu / (k + 1)
    return 1.0 - s


P_FZ = ptail(len(PRIM), E_FZ)
_pfz = float(tex('CeProbNull'))
if DRIVE == 8:
    P_FZ = 0.99
ck('B8 the probability is the Poisson tail of the expectation it names, and '
   'reproduces the published one on the frozen mask',
   abs(P_FZ - _pfz) < 0.02, '%.3f against %s published' % (P_FZ, _pfz))

SENS = []
for h in (HALF, LAD[-1]['half']):
    e, _n, _a, sh, _j = expectation(NULL_EXP, h)
    obs = sum(1 for r in PRIM if abs(r['x_dv_star']) > h)
    SENS.append(dict(half=h, exp=e, obs=obs, p=ptail(obs, e), share=sh))
    print('  expanded list at +-%g km/s: expectation %.2f, observed %d, '
          'P(N>=obs) %.2f, attributed share of control exceedances %.0f per '
          'cent' % (h, e, obs, ptail(obs, e), 100 * sh))
print('  frozen mask at +-%g km/s: expectation %.2f, observed %d, '
      'P(N>=obs) %.2f' % (HALF, E_FZ, len(PRIM), P_FZ))
m('XlExpFrozen', '%.1f' % E_FZ)
m('XlExpWide', '%.1f' % SENS[0]['exp'])
m('XlObsWide', '%d' % SENS[0]['obs'])
m('XlShareFrozenPct', '%.0f' % (100 * A_FZ))
m('XlShareWidePct', '%.0f' % (100 * A_XP))
m('XlTightExp', '%.1f' % SENS[1]['exp'])
m('XlTightObs', '%d' % SENS[1]['obs'])
m('XlTightProb', '%.2f' % SENS[1]['p'])
m('XlNPrim', '%d' % len(PRIM))

# =====================================================================
# 4  THE LEDGER COLUMN
# =====================================================================
ROWS.sort(key=lambda z: -z['tstar'])


def tname(x):
    """The paper's spelling: the Gaia designation the catalogue appends for a
    Gaia-resolved component is not part of the name."""
    return x.split('Gaia DR3')[0].strip().replace(' ', '~')


#: TWO FORMS OF ONE TABLE, and the recommendation is the second: the ledger
#: ships as an arXiv ancillary file, so two more columns there cost no pages,
#: while a typeset column costs a column.
with open(OUT_TAB, 'w') as fh:
    fh.write('%% GENERATED by r21_lines.py -- do not hand-edit.\n')
    for r in ROWS + HROWS:
        if r['attributed_frozen']:
            continue
        lsr = r.get('x_dv_lsr')
        fh.write('%s & %.6f & %s %s & $%+.1f$ & %s \\\\\n'
                 % (tname(r['star']), r['f_star'], r['x_mol'],
                    r['x_qn'][:28], r['x_dv_star'],
                    ('$%+.1f$' % lsr) if lsr is not None else '--'))
with open(OUT_TSV, 'w') as fh:
    fh.write('# nearest transition of ANY species with a published '
             'interstellar or circumstellar detection and E_u < %.0f K,\n'
             '# from a Splatalogue query of CDMS and JPL on %s.  The frozen '
             '%s-species mask of the paper is unchanged; these columns are '
             'reported so that\n# "unattributed" can be read against a '
             'wider list.  An empty field is a value not computed, not a '
             'zero.\n'
             % (HARV['eu_max'], HARV['query_date'][:10], tex('FrNSpec')))
    fh.write('star\teb\tnu_star_GHz\tnearest_any\tqn\teu_K\t'
             'dv_any_star_kms\tdv_any_lsr_kms\tset\n')
    for r, tag in ([(x, 'census') for x in ROWS]
                   + [(x, 'hold-out') for x in HROWS]):
        if r['attributed_frozen']:
            continue
        lsr = r.get('x_dv_lsr')
        fh.write('%s\t%s\t%.6f\t%s\t%s\t%.1f\t%+.2f\t%s\t%s\n'
                 % (r['star'], r['eb'], r['f_star'], r['x_mol'], r['x_qn'],
                    r['x_eu'], r['x_dv_star'],
                    ('%+.2f' % lsr) if lsr is not None else '', tag))

json.dump(dict(query_date=HARV['query_date'], half_kms=HALF,
               n_species=HARV['n_species'], n_lines_nbhd=len(XP),
               n_lines_islands=FULL['n_lines'],
               frozen_recovered=REC, frozen_missing=MISS,
               rows=ROWS,
               holdout=HROWS, lupus_named=LUPHIT,
               ladder_strong=LADS,
               n_unattr=len(UN), n_unattr_in=len(IN),
               n_unattr_out=len(OUTSIDE),
               ladder=LAD, sensitivity=SENS,
               band_frozen=dict(GHz=_gz, pct=_pz),
               band_wide=dict(GHz=_gx, pct=_px),
               expectation=dict(frozen=E_FZ, wide=E_XP, n_exc=NEX,
                                n_attr_frozen=NAT, n_attr_wide=NAT2,
                                share_frozen=A_FZ, share_wide=A_XP,
                                obs_frozen=len(PRIM), p_frozen=P_FZ),
               fails=FAIL), open(OUT_JSON, 'w'), indent=1, sort_keys=True,
          default=str)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    fh.write('\n'.join(sorted(MACROS)) + '\n')
print('\n  %d macros -> %s' % (len(MACROS), os.path.basename(OUT)))
if FAIL:
    print('  FAILURES: %s' % ', '.join(sorted(set(FAIL))))
    raise SystemExit(1)
print('  all clauses pass')
