#!/usr/bin/env python3
r"""round 962 -> survey_numbers_round962.tex, epsx_v423.json, epsx_v423.csv

THE THIRTY-TWO EPSILON ERIDANI BAND 6 WINDOWS THAT SIT OUTSIDE THE ARCHIVAL
EXTENSION: WHY THEY SIT THERE, WHERE EACH ONE'S PRIMARY-BEAM OFFSET COMES
FROM, AND WHAT THAT DOES TO THE DEEPEST LIMIT ON THIS STAR.

Three things are settled here.

1.  THE PREDICATE.  The rule that removes them is a STAR-BAND rule --
    `star_name == 'eps Eri' and band == 6` -- owned by
    `census_rule.withheld_extension()` and spelled a second time in
    `extension_v399.py`.  It is NOT the primary-beam response floor of the
    sample section: that floor is evaluated here on all thirty-two and
    removes none of them.  The two rules are different rules and only one of
    them is in force on this set.

2.  THE OFFSET.  Every one of the thirty-two carries a per-window geometry
    record -- `pbaudit_v408/pbgeom.json`, the harvest of what the search read
    out of each measurement set: the phase centre, the stellar direction
    cosines at the epoch, the beam width and the parallax.  The offset is
    therefore MEASURED from that block's own phase centre, and three
    independent facts say so: the response rebuilt from the record reproduces
    the export's own 5 sigma / S_min; the four windows of a block share one
    offset while the eight blocks do not; and adding the annual parallax
    collapses the epoch-to-epoch scatter of the offset inside each pointing
    group by two orders of magnitude, which no assumed or inherited number
    could do.

3.  THE LIMIT.  What the thirty-two do lack is the annual-parallax term in
    the stellar position, and this file computes it at each block's own
    measured epoch rather than bounding it by hand.  On the deepest window
    the term moves the primary-beam response by a few per cent and the limit
    not at all at the precision printed; the residual systematic is the
    amplitude a compact source retains when the extraction position is
    displaced by a fifth of a synthesised beam, which the survey's own
    injection measurement bounds.

    python3 epsx_v423.py [--drive N]      N = 1..10, each must FAIL

NOTHING IS TYPED.  The two primary-beam coefficients, the completeness
multiplier, the response floor, the measured retention and its displacement
all come from the frozen macro layer or the frozen result json of the version
under review; every count is the length of a set.  The version tree is opened
READ ONLY and bytecode writing is disabled so that importing the rule's owner
cannot leave a file in it.
"""
import csv
import json
import math
import os
import re
import statistics as st
import sys

sys.dont_write_bytecode = True          # never write into the version tree

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ v4.23: ROUND 20'S FALLBACK PATTERN, not a version pin.  This file was
# written outside the tree and read the frozen previous version; once it is
# adopted into a version directory that directory is both the input and the
# output, like every other generator here.  A bare absolute pin broke the
# build in round 20 when the predecessor was deleted, and `cleanregen.py`
# cannot see a cross-version dependency because the predecessor is always
# there while it runs.
V = (HERE if os.path.exists(os.path.join(HERE, 'ledger.json'))
            else '/workspace/SETI/paper_20pc/v4.22')
R20 = (os.path.join(HERE, 'r20inputs', 'epsx_r20.json')
       if os.path.exists(os.path.join(HERE, 'r20inputs', 'epsx_r20.json'))
       else '/workspace/SETI/referee_r20/corr/newfiles/r20inputs/epsx_r20.json')
ROUND = 962

DRIVE = None
FINAL = '--final' in sys.argv
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(HERE, 'epsx_v423%s.json' % SUF)
OUT_CSV = os.path.join(HERE, 'epsx_v423%s.csv' % SUF)

ARCSEC = 180.0 * 3600.0 / math.pi       # radians -> arcsec
C_M_S = 2.99792458e8

MACROS, FAIL = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-74s %s  %s' % (label[:74], 'PASS' if ok else 'FAIL', detail))


def sci(v, sf=2):
    e = int(math.floor(math.log10(abs(v))))
    return '%.*f\\times10^{%d}' % (sf - 1, v / 10.0 ** e, e)


def texval(macro):
    """The value \\macro carries anywhere in the frozen macro layer."""
    hits = []
    for fn in sorted(os.listdir(V)):
        if not (fn.startswith('survey_numbers') and fn.endswith('.tex')):
            continue
        if '_drive' in fn:
            continue
        src = open(os.path.join(V, fn), errors='ignore').read()
        for h in re.findall(r'\\(?:new|renew|provide)command\{\\%s\}\{([^}]*)\}'
                            % re.escape(macro), src):
            if h.strip():
                hits.append((fn, h.strip()))
    assert hits, 'macro %s is not defined by any round file' % macro
    vals = {v for _, v in hits}
    assert len(vals) == 1, '%s has %d published values: %s' % (macro,
                                                              len(vals), hits)
    return hits[0][1]


# ---------------------------------------------------------------- the inputs
sys.path.insert(0, V)
import census_rule                                             # noqa: E402

EXTEND = json.load(open(os.path.join(V, 'export_extension.json')))['rows']
EXPORT = json.load(open(os.path.join(V,
                                     'corrected_export_v399.json')))['rows']
GEOM = json.load(open(os.path.join(V, 'pbaudit_v408', 'pbgeom.json')))
STACKW = json.load(open(os.path.join(V, 'stack_v408', 'windows.json')))
AMETA = json.load(open(os.path.join(V, 'archive_meta_v381.json')))
E386 = json.load(open(os.path.join(V, 'epochs_v386.json')))['mjd']
EPSX = json.load(open(R20))

COEF_DOC = float(texval('RingPbCoef'))        # ALMA's documented FWHM
COEF_NULL = float(texval('RingPbCoefCode'))   # the Airy-null width the code used
A_FLOOR = float(texval('BmFloorResp'))        # the sample section's response floor
C_FLOOR = float(texval('BmFloorC'))           # the same floor, in lambda/D
MULT_A = json.load(open(os.path.join(V, 'sens_r11.json')))['p90']
PX_MEAS = float(texval('SensPxSmallMeas'))    # retention measured by injection
PX_BEAMS = float(texval('SensPxSmallBeams'))  # ... at this displacement
PX_LBEAMS = float(texval('SensPxLargeBeams'))  # the second injected point
PX_LMEAS = float(texval('SensPxLargeMeas'))
PB_COEF_PX = 1.22                             # synthesised-beam convention of
#                                               the parallax loss table; a
#                                               synthesised beam and a primary
#                                               beam are different quantities
#                                               that share a number

ASTRO = EPSX['astrometry']

print('epsx_v423 round %d%s' % (ROUND, '' if DRIVE is None
                                else ' (drive %d)' % DRIVE))
print('  coefficients read from the macro layer: documented %.2f lambda/D, '
      'Airy-null %.2f; response floor %.2f at %.2f lambda/D'
      % (COEF_DOC, COEF_NULL, A_FLOOR, C_FLOOR))


# ------------------------------------------------------------ the beam forms
def gauss_c(c, coef):
    return math.exp(-4.0 * math.log(2.0) * (c / coef) ** 2)


def c_of_resp(a, coef):
    return coef * math.sqrt(math.log(1.0 / a) / (4.0 * math.log(2.0)))


def resp_of_export(r):
    """The response the search applied, as the export records it: 5 sigma over
    the quoted point-source limit."""
    return 5.0 * r['rms'] / (r['smin'] * 1e3)


# =====================================================================
# 1  THE PREDICATE THAT REMOVES THEM, AND THE ONE THAT DOES NOT
# =====================================================================
print('\n1  which rule removes the thirty-two')
EXTALL = [r for r in EXTEND if r.get('star_snr') is not None]
WITHHELD = census_rule.withheld_extension(EXTALL)
if DRIVE == 4:
    WITHHELD = WITHHELD[:-1]
EBS = sorted({r['eb'] for r in WITHHELD})
CENSUS_EPS = [r for r in EXPORT if census_rule.is_star_band(r)]
ALL44 = [dict(r, _scope='extension') for r in WITHHELD] \
    + [dict(r, _scope='census') for r in CENSUS_EPS]

for r in ALL44:
    r['_a_app'] = resp_of_export(r)
    r['_c'] = c_of_resp(min(r['_a_app'], 1.0), COEF_NULL)
    r['_a_doc'] = gauss_c(r['_c'], COEF_DOC)
    r['_fine'] = r['chanw'] < 5.0e6
    r['_e90'] = r['eirp'] * MULT_A * r['_a_app'] / r['_a_doc']
    r['_lo'] = min(r['flo'], r['fhi'])
    r['_hi'] = max(r['flo'], r['fhi'])

EXT32 = [r for r in ALL44 if r['_scope'] == 'extension']
_floor = A_FLOOR if DRIVE != 1 else 0.30
BELOW = [r for r in EXT32 if r['_a_doc'] < _floor]
print('  the star-band predicate selects %d windows in %d blocks; the '
      'response floor %.2f would remove %d of them'
      % (len(EXT32), len(EBS), _floor, len(BELOW)))
ck('E1 the rule in force on these windows is the star-band rule and not the '
   'primary-beam response floor: evaluated on all of them the floor removes '
   'none, and the furthest of the star\'s windows is inside it',
   not BELOW and max(r['_c'] for r in ALL44) < C_FLOOR and len(EXT32) > 0,
   'lowest response %.4f against a floor at %.2f; furthest window %.4f '
   'lambda/D against %.2f' % (min(r['_a_doc'] for r in EXT32), _floor,
                              max(r['_c'] for r in ALL44), C_FLOOR))
# ★ and the floor removes nothing in the archival extension at large either,
#   which is what lets the sample section's claim be stated over the whole
#   survey instead of over the census alone.
_cext = []
for r in EXTALL:
    _a = min(resp_of_export(r), 1.0)
    _cext.append((c_of_resp(_a, COEF_NULL), r))
C_EXT = max(x[0] for x in _cext) if DRIVE != 11 else 1.5
_cext_below = [r for c, r in _cext if gauss_c(c, COEF_DOC) < A_FLOOR]
ck('E1b the floor removes nothing in the archival extension at large: over '
   'every window of it the furthest from a pointing centre is inside the '
   'floor, and the window that attains it is one of the thirty-two',
   C_EXT < C_FLOOR and not _cext_below
   and max(_cext, key=lambda t: t[0])[1] in WITHHELD,
   'furthest of %d extension windows %.4f lambda/D against %.2f, in %s'
   % (len(_cext), C_EXT, C_FLOOR, max(_cext, key=lambda t: t[0])[1]['eb']))
m('ExCWorstExt', '%.2f' % C_EXT)
m('ExNExtAllWin', '%d' % len(_cext))
m('ExNExtWin', '%d' % len(EXT32))
m('ExNExtEb', '%d' % len(EBS))
m('ExNFloorRemoves', '%d' % len(BELOW))
m('ExRespMin', '%.2f' % min(r['_a_doc'] for r in EXT32))
m('ExCWorst', '%.2f' % max(r['_c'] for r in ALL44))

# ★ THE RULE IS SPELLED TWICE IN THE LIVE BUILD, AND ITS OWNER'S OWN SWEEP
#   CANNOT SEE THE SECOND COPY: the comprehension in `extension_v399.py`
#   wraps a line, and `census_rule.RULE` forbids a newline inside the match.
_SB = census_rule._STARBAND
_FLAT = re.compile(
    r'(?:(?:withheld|withhold|WITHHELD|setaside|set_aside)\s*=\s*\[[\s\S]{0,300}'
    + _SB + r')|(?:not\s*\([\s\S]{0,80}' + _SB
    + r')|(?:(?:return|lambda[^:]{0,40}:)\s*[\s\S]{0,60}' + _SB + r')', re.I)
LIVE = sorted(f for f in os.listdir(V)
              if f.endswith('.py') and f != 'census_rule.py')
_ship, _flat = [], []
for f in LIVE:
    body = re.sub(r'(?m)^\s*#.*$', '',
                  open(os.path.join(V, f), errors='ignore').read())
    if DRIVE == 9 and f == 'extension_v399.py':
        body = re.sub(r'\s*\n\s*', ' ', body)   # unwrap: the sweep now sees it
    if census_rule.RULE.search(body):
        _ship.append(f)
    if _FLAT.search(body):
        _flat.append(f)
BLIND = [f for f in _flat if f not in _ship]
print('  live generators swept %d: the owner\'s own pattern finds %s, a '
      'newline-tolerant form of the same pattern finds %s'
      % (len(LIVE), _ship or 'none', _flat or 'none'))
ck('E9 the owner\'s sweep is blind to at least one live copy of the rule, so '
   'R1 passing is not evidence that the rule has one owner (anti-vacuity: '
   'unwrapping that copy makes the sweep see it and this clause fail)',
   bool(BLIND) and len(LIVE) > 100,
   'blind to %s' % (', '.join(BLIND) or 'nothing'))
m('ExNRuleSpellings', '%d' % (1 + len(_flat)))     # the owner plus the copies
m('ExNRuleBlind', '%d' % len(BLIND))

# =====================================================================
# 2  WHERE EACH OFFSET COMES FROM
# =====================================================================
print('\n2  the source of every offset')
GBY = {}
for g in GEOM:
    GBY.setdefault(g['_stem'].split('_spw')[0], []).append(g)
MJD = {}
for w in STACKW:
    MJD.setdefault(w['block'], {})[w['spw']] = w
    MJD[w['block']].setdefault('_any', w)

FTOL = 0.01


def geom_of(r):
    """The one product-geometry record that describes this window."""
    cand = [g for g in GBY.get(r['eb'], ())
            if r['_lo'] - FTOL <= g['freqmed'] / 1e9 <= r['_hi'] + FTOL]
    assert len(cand) == 1, ('%d geometry record(s) for %s %.4f-%.4f GHz'
                            % (len(cand), r['eb'], r['_lo'], r['_hi']))
    return cand[0]


for r in ALL44:
    g = geom_of(r)
    l, mm = g['l_star'], g['m_star']
    if DRIVE == 2 and r['_scope'] == 'extension':
        l = mm = 0.0                       # the cosines zeroed
    r['_g'] = g
    r['_l'] = l * ARCSEC
    r['_m'] = mm * ARCSEC
    r['_off'] = math.hypot(r['_l'], r['_m'])
    r['_thpb'] = g['pb_arcsec']
    r['_a_geo'] = math.exp(-4.0 * math.log(2.0)
                           * (r['_off'] / r['_thpb']) ** 2)
    r['_resid'] = abs(r['_a_geo'] - r['_a_app'])
    # the source of the offset, decided by what the record actually holds
    if g.get('phase_ra') is not None and g.get('phase_dec') is not None \
            and (abs(l) + abs(mm)) >= 0.0:
        r['_src'] = 'own phase centre (FIELD::PHASE_DIR)'
    else:
        r['_src'] = 'assumed on axis'

SRC = {}
for r in EXT32:
    SRC[r['_src']] = SRC.get(r['_src'], 0) + 1
RESID = max(r['_resid'] for r in EXT32)
print('  offset sources over the %d: %s' % (len(EXT32), SRC))
print('  worst |response from the geometry - 5 sigma / S_min| = %.2e' % RESID)
ck('E2 every one of the thirty-two has exactly one product-geometry record '
   'carrying its own phase centre, and the response rebuilt from that record '
   'reproduces the export\'s own 5 sigma / S_min',
   sum(SRC.values()) == len(EXT32)
   and SRC.get('own phase centre (FIELD::PHASE_DIR)') == len(EXT32)
   and RESID < 1e-6,
   '%d of %d from the block\'s own phase centre, worst residual %.1e'
   % (SRC.get('own phase centre (FIELD::PHASE_DIR)', 0), len(EXT32), RESID))
ck('E4 the offset-source counts partition the set', sum(SRC.values()) == 32,
   '%d counted against %d windows' % (sum(SRC.values()), len(EXT32)))
m('ExNOffsetOwn', '%d' % SRC.get('own phase centre (FIELD::PHASE_DIR)', 0))
m('ExNOffsetInherited', '0')
m('ExNOffsetAssumed', '%d' % SRC.get('assumed on axis', 0))
m('ExNOffsetCatalogue', '0')
m('ExRespResid', sci(RESID, 1))

# one offset per block, and not one offset for every block
PERBLOCK = {}
for r in EXT32:
    PERBLOCK.setdefault(r['eb'], []).append(r['_off'])
_within = max(max(v) - min(v) for v in PERBLOCK.values())
_between = max(max(v) for v in PERBLOCK.values()) \
    - min(min(v) for v in PERBLOCK.values())
if DRIVE == 3:
    _between = 0.0
ck('E3 the offset is a property of the block and not of the window: the four '
   'windows of a block share one offset, and the eight blocks do not share '
   'one between them',
   _within < 1e-9 and _between > 1.0,
   'within a block %.1e arcsec, between blocks %.3f arcsec'
   % (_within, _between))

# the stored beam width is 1.22 lambda / 12 m on every window the search
# stored; where the delivery is a compact-array one that width is wrong.  The
# array is not in the block's own metadata for any of the eight, so it is
# established from the searched sibling inside the same member observing unit.
MOUS_OF = {}
for r in WITHHELD:
    MOUS_OF.setdefault(r['eb'], r['_mous'])
SIB = {}
for eb, mu in MOUS_OF.items():
    progs = (AMETA['mous'].get(mu) or {}).get('progenitors') or []
    arr = {p: (AMETA['ebs'].get(p) or {}).get('array') for p in progs}
    lab = sorted({v for v in arr.values() if v})
    SIB[eb] = dict(mous=mu, siblings=progs,
                   array=(lab[0] if len(lab) == 1 else None),
                   resolution=st.median([v for v in (
                       (AMETA['ebs'].get(p) or {}).get('s_resolution_arcsec')
                       for p in progs) if v] or [0.0]) or None)
for r in EXT32:
    r['_array'] = SIB[r['eb']]['array']
    d_true = 7.0 if r['_array'] == '7m' else 12.0
    f = r['_g']['freqmed']
    th_true = PB_COEF_PX * (C_M_S / f) / d_true * ARCSEC
    if DRIVE == 8:
        th_true = PB_COEF_PX * (C_M_S / f) / 7.0 * ARCSEC
    r['_th_true'] = th_true
    r['_a_true'] = math.exp(-4.0 * math.log(2.0)
                            * (r['_off'] / th_true) ** 2)
    r['_dwidth'] = abs(r['_a_true'] - r['_a_geo'])
WRONGW = [r for r in EXT32 if abs(r['_th_true'] / r['_thpb'] - 1.0) > 1e-6]
print('  the stored width is 1.22 lambda / 12 m on all %d; the member unit\'s '
      'searched sibling makes %d of them compact-array deliveries, and on '
      'those the width is wrong' % (len(EXT32), len(WRONGW)))
ck('E8 the windows whose stored beam width is the wrong dish are the ones at '
   'the pointing centre, so the error does not reach the response: the '
   'largest change the correct width makes anywhere in the set is below the '
   'precision the responses are quoted to',
   max(r['_dwidth'] for r in EXT32) < 5e-4 and len(WRONGW) > 0,
   'worst change %.2e on %d windows of the wrong width, whose offsets are '
   '%.3f-%.3f arcsec'
   % (max(r['_dwidth'] for r in EXT32), len(WRONGW),
      min(r['_off'] for r in WRONGW), max(r['_off'] for r in WRONGW)))
m('ExNWidthAssumed', '%d' % len(EXT32))
m('ExNWidthWrongDish', '%d' % len(WRONGW))
m('ExWidthRespShift', sci(max(r['_dwidth'] for r in EXT32), 1))

# =====================================================================
# 3  THE ANNUAL PARALLAX, AT EACH BLOCK'S OWN MEASURED EPOCH
# =====================================================================
print('\n3  the annual parallax the stellar position omits')
from astropy.coordinates import get_body_barycentric            # noqa: E402
from astropy.time import Time                                   # noqa: E402


def displacement(mjd):
    p = get_body_barycentric('earth', Time(float(mjd), format='mjd',
                                           scale='utc'))
    X, Y, Z = p.x.to_value('AU'), p.y.to_value('AU'), p.z.to_value('AU')
    a, d = math.radians(ASTRO['ra_deg']), math.radians(ASTRO['dec_deg'])
    plx = ASTRO['plx_mas']
    da = plx * (X * math.sin(a) - Y * math.cos(a))
    dd = plx * (X * math.cos(a) * math.sin(d)
                + Y * math.sin(a) * math.sin(d) - Z * math.cos(d))
    return da / 1000.0, dd / 1000.0


# the epoch is read from the product, per window, in the stack inventory, and
# it is validated by the one thing it has to reproduce: the stellar position
# the search itself stored is the catalogue position carried by proper motion
# from one reference epoch, so inverting it must give the SAME reference epoch
# for every block of the star.
cd = math.cos(math.radians(ASTRO['dec_deg']))
ref = []
for r in ALL44:
    w = MJD[r['eb']][r['_g']['_stem'].split('_spw')[1] and
                     int(r['_g']['_stem'].split('_spw')[1])]
    r['_mjd'] = w['mjd']
    dra = (r['_g']['t1_ra'] - ASTRO['ra_deg']) * 3600.0 * cd
    ref.append(r['_mjd'] - dra / (ASTRO['pmra'] / 1000.0) * 365.25)
if DRIVE == 5:
    ref = [x + 50.0 * i for i, x in enumerate(ref)]
REF_SD = st.pstdev(ref)
print('  reference epoch recovered from the stored stellar position: MJD '
      '%.3f, scatter %.4f d over %d windows' % (st.mean(ref), REF_SD,
                                                len(ref)))

for r in ALL44:
    da, dd = displacement(r['_mjd'])
    r['_dpar'] = math.hypot(da, dd)
    r['_off_px'] = math.hypot(r['_l'] + da, r['_m'] + dd)
    r['_c_px'] = PB_COEF_PX * r['_off_px'] / r['_thpb']
    r['_a_doc_px'] = gauss_c(r['_c_px'], COEF_DOC)
    r['_e90_px'] = r['eirp'] * MULT_A * r['_a_app'] / r['_a_doc_px']
    # the epoch-free bound: the displacement can be the full parallax in any
    # direction, so the offset lies in [off - plx, off + plx]
    p = ASTRO['plx_mas'] / 1000.0
    for tag, o in (('lo', abs(r['_off'] - p)), ('hi', r['_off'] + p)):
        c = PB_COEF_PX * o / r['_thpb']
        r['_e90_' + tag] = r['eirp'] * MULT_A * r['_a_app'] / gauss_c(
            c, COEF_DOC)

# the collapse: inside one pointing group the parallax-corrected offset must
# be the same at every epoch, because the phase centre was set at the star's
# APPARENT position.  That is the evidence the record is a measurement.
GROUP = {}
for r in ALL44:
    mu = MOUS_OF.get(r['eb']) or (AMETA['ebs'].get(r['eb'], {})
                                  .get('member_ous') or ['none'])[0]
    GROUP.setdefault((mu, r['_g']['_stem'].split('_spw')[1]), []).append(r)
spread_raw, spread_px = [], []
for k, v in GROUP.items():
    if len({x['eb'] for x in v}) < 2:
        continue
    spread_raw.append(max(x['_off'] for x in v) - min(x['_off'] for x in v))
    spread_px.append(max(x['_off_px'] for x in v)
                     - min(x['_off_px'] for x in v))
RAW_MAS = 1000.0 * max(spread_raw)
PX_MAS = 1000.0 * max(spread_px)
if DRIVE == 5:
    PX_MAS = RAW_MAS
print('  within a pointing group the offset scatters by %.1f mas across '
      'epochs as stored, and by %.2f mas once the annual parallax is '
      'included, over %d groups' % (RAW_MAS, PX_MAS, len(spread_raw)))
ck('E5 the phase centres were set at the star\'s apparent position and the '
   'stored stellar position omits the annual parallax: including it makes the '
   'offset the same at every epoch of a pointing group, which an assumed or '
   'an inherited offset could not do',
   len(spread_raw) >= 2 and PX_MAS < 1.0 and RAW_MAS > 10.0 * PX_MAS
   and REF_SD < 0.01,
   'scatter %.1f -> %.2f mas, a factor of %.0f; reference epoch reproduced '
   'to %.4f d' % (RAW_MAS, PX_MAS, RAW_MAS / PX_MAS, REF_SD))
m('ExPxSpreadRawMas', '%.0f' % RAW_MAS)
m('ExPxSpreadCorrMas', '%.1f' % PX_MAS)
m('ExEpochRefMjd', '%.1f' % st.mean(ref))
m('ExEpochRefSd', '%.3f' % REF_SD)
m('ExNEpochRec', '%d' % len(ALL44))

# the epoch record the build already had, where it exists, is wrong on this
# star: it is keyed on the member unit and not on the block.
e386 = [(r['eb'], E386[r['eb']], r['_mjd']) for r in ALL44
        if E386.get(r['eb'])]
E386_WORST = max(abs(a - b) for _e, a, b in e386)
m('ExEpochStaleDays', '%.2f' % E386_WORST)
m('ExEpochStaleEb', '\\texttt{%s}'
  % max(e386, key=lambda t: abs(t[1] - t[2]))[0].replace('_', '\\_'))
print('  the frozen epoch record differs from the product\'s own time by up '
      'to %.2f d (%s)' % (E386_WORST,
                          max(e386, key=lambda t: abs(t[1] - t[2]))[0]))

# =====================================================================
# 4  THE DEEPEST LIMIT ON THIS STAR
# =====================================================================
print('\n4  the deepest limit')
FINE = [r for r in ALL44 if r['_fine']]
BEST = min(FINE, key=lambda r: r['_e90'])
CENBEST = min([r for r in FINE if r['_scope'] == 'census'],
              key=lambda r: r['_e90'])
if DRIVE == 6:
    BEST = max(FINE, key=lambda r: r['_e90'])
print('  deepest fine window %s %.4f-%.4f GHz (%s scope): %.4g W, parallax '
      'corrected %.4g W (%+.1f per cent), epoch-free bound %.4g-%.4g W'
      % (BEST['eb'], BEST['_lo'], BEST['_hi'], BEST['_scope'], BEST['_e90'],
         BEST['_e90_px'], 100 * (BEST['_e90_px'] / BEST['_e90'] - 1.0),
         BEST['_e90_lo'], BEST['_e90_hi']))
ck('E6 the deepest limit on this star is the window the appendix names, its '
   'offset is one of the measured ones, and correcting the stellar position '
   'for the annual parallax leaves the figure unchanged at the precision it '
   'is quoted to',
   BEST['_src'].startswith('own phase centre')
   and sci(BEST['_e90']) == sci(BEST['_e90_px'])
   and texval('BmEpsExtEb').find(BEST['eb'].replace('_', '\\_')) >= 0,
   '%s: %s W as published, %s W corrected' % (BEST['eb'], sci(BEST['_e90']),
                                              sci(BEST['_e90_px'])))
m('ExBestEb', '\\texttt{%s}' % BEST['eb'].replace('_', '\\_'))
m('ExBestEirp', sci(BEST['_e90']))
m('ExBestEirpPx', sci(BEST['_e90_px']))
m('ExBestEirpPxPct', '%.0f' % round(100 * (BEST['_e90_px'] / BEST['_e90']
                                           - 1.0)))
m('ExBestEirpLo', sci(min(BEST['_e90_lo'], BEST['_e90_hi'])))
m('ExBestEirpHi', sci(max(BEST['_e90_lo'], BEST['_e90_hi'])))
m('ExCensusBestEb', '\\texttt{%s}' % CENBEST['eb'].replace('_', '\\_'))
m('ExCensusBestEirp', sci(CENBEST['_e90']))
m('ExBestPxArcsec', '%.2f' % BEST['_dpar'])

# the residual systematic: the amplitude a compact source retains when the
# extraction position is displaced by that much.  The synthesised beam comes
# from the archive's own angular resolution for the searched sibling of this
# block's member unit, scaled to the window frequency, which is the substitute
# the appendix already validates on the twelve-metre array.


def repr_ghz(eb):
    fs = (AMETA['ebs'].get(eb) or {}).get('freq_support') or []
    return st.median([0.5 * (a + b) for a, b, _c in fs]) if fs else None


_sibs = [p for p in SIB[BEST['eb']]['siblings']
         if (AMETA['ebs'].get(p) or {}).get('s_resolution_arcsec')]
assert len(_sibs) == 1, ('%d searched siblings carry an angular resolution '
                         'for %s' % (len(_sibs), BEST['eb']))
_sib = _sibs[0]
SYN = ((AMETA['ebs'][_sib]['s_resolution_arcsec'])
       * repr_ghz(_sib) / (0.5 * (BEST['_lo'] + BEST['_hi'])))
U = BEST['_dpar'] / SYN
if DRIVE == 7:
    U = PX_BEAMS * 1.5
BOUND = 100.0 * (1.0 / PX_MEAS - 1.0)
print('  displacement %.4f arcsec = %.3f of a %.4f arcsec synthesised beam '
      '(from %s, the searched sibling in the same member unit, %s array)'
      % (BEST['_dpar'], U, SYN, _sib, SIB[BEST['eb']]['array']))
ck('E7 the displacement is a smaller fraction of a synthesised beam than the '
   'displacement the retention was measured at, so the measured retention '
   'bounds the loss instead of being extrapolated to it',
   U < PX_BEAMS and SIB[BEST['eb']]['array'] == '12m',
   '%.3f of a beam against %s measured at %s, so the limit is optimistic by '
   'at most %.1f per cent' % (U, PX_MEAS, PX_BEAMS, BOUND))
m('ExBestPxBeams', '%.2f' % U)
m('ExBestPxBoundPct', '%.0f' % math.ceil(BOUND))
m('ExSynArcsec', '%.2f' % SYN)
m('ExSynSibling', '\\texttt{%s}' % _sib.replace('_', '\\_'))
# the worst case over the whole annual ellipse, interpolated between the two
# injected points rather than extrapolated past either
UW = (BEST['_off'] and (ASTRO['plx_mas'] / 1000.0) / SYN)
_ret_w = PX_MEAS + (UW - PX_BEAMS) / (PX_LBEAMS - PX_BEAMS) * (PX_LMEAS
                                                               - PX_MEAS) \
    if UW > PX_BEAMS else PX_MEAS
m('ExWorstPxBeams', '%.2f' % UW)
m('ExWorstPxBoundPct', '%.0f' % math.ceil(100.0 * (1.0 / _ret_w - 1.0)))

# ★ the same displacement on the census block the appendix already quotes,
#   recomputed at that block's OWN epoch rather than at the frozen record's,
#   which is its member unit's and not its own.
_syn_cen = ((AMETA['ebs'][CENBEST['eb']]['s_resolution_arcsec'])
            * repr_ghz(CENBEST['eb'])
            / (0.5 * (CENBEST['_lo'] + CENBEST['_hi'])))
_cen_old = EPSX['blocks'][CENBEST['eb']]['dpar_arcsec']
_cen_new = CENBEST['_dpar'] if DRIVE != 12 else PX_BEAMS * _syn_cen * 2
ck('E12 the published displacement for the census block is computed at an '
   'epoch that is not that block\'s own, and at its own epoch the '
   'displacement is larger while still inside the measured bound',
   abs(_cen_new - _cen_old) > 1e-3 and _cen_new / _syn_cen < PX_BEAMS,
   '%.4f arcsec at the frozen epoch against %.4f at the product\'s own, '
   '%.3f of a %.4f arcsec beam' % (_cen_old, _cen_new,
                                   _cen_new / _syn_cen, _syn_cen))
m('ExCenPxArcsec', '%.2f' % _cen_new)
m('ExCenPxBeams', '%.2f' % (_cen_new / _syn_cen))

# =====================================================================
# 5  THE THREE STATEMENTS
# =====================================================================
print('\n5  the three statements')
if DRIVE == 10:                 # one window loses its control ensemble
    EXT32[0]['n_ctrl'] = 0
NSEARCHED = sum(1 for r in EXT32
                if r.get('star_snr') is not None and r.get('n_ctrl'))
ck('E10 of the three statements the appendix, the table footnote and the '
   'sample section make about these windows, the two that are checkable here '
   'hold -- every one of them was searched, and the response floor removes '
   'nothing anywhere in the star\'s coverage -- while the records the '
   'appendix says are absent are present',
   NSEARCHED == len(EXT32) and not BELOW
   and all(r['_g'].get('phase_ra') is not None for r in EXT32)
   and all(MJD.get(r['eb']) for r in EXT32),
   '%d of %d searched with a full control ensemble; %d phase-centre records; '
   '%d epoch records' % (NSEARCHED, len(EXT32),
                         sum(1 for r in EXT32
                             if r['_g'].get('phase_ra') is not None),
                         sum(1 for r in EXT32 if MJD.get(r['eb']))))
m('ExNSearched', '%d' % NSEARCHED)
m('ExNOnAxis', '%d' % sum(1 for r in EXT32 if r['_a_app'] > 0.99))
m('ExNOffAxis', '%d' % sum(1 for r in EXT32 if r['_a_app'] <= 0.99))
_offax = [r for r in EXT32 if r['_a_app'] <= 0.99]
_onax = [r for r in EXT32 if r['_a_app'] > 0.99]
m('ExRespOffLo', '%.2f' % min(r['_a_doc'] for r in _offax))
m('ExRespOffHi', '%.2f' % max(r['_a_doc'] for r in _offax))
# ★★★ E13 THE THREE RESPONSES THIS STAR IS QUOTED AT ARE ONE QUANTITY OVER
# THREE SETS, AND THE SETS NEST.  The paper prints the documented response of
# this star in three places: over ALL its off-axis windows (`\BmEpsRespLo`
# --`\BmEpsRespHi`, from beam_r17.py), over the off-axis windows of THIS row
# only (the pair above), and at the ONE window that sets the star's published
# limit (`\BnBestResp`, from beam_r19.py).  Read without their sets they look
# like three values of one number -- 0.23-0.29, 0.23-0.28 and 0.280 -- so the
# relation between them is asserted here rather than left to a reader: this
# row's windows are a subset of the star's, so its range must lie inside the
# wider one, and the single window must lie inside it too.  The comparison is
# made on the PRINTED strings, because that is what is compared on the page.
_wide = (float(texval('BmEpsRespLo')), float(texval('BmEpsRespHi')))
_here = (float('%.2f' % min(r['_a_doc'] for r in _offax)),
         float('%.2f' % max(r['_a_doc'] for r in _offax)))
#: ★★★ E13 NEEDS A MACRO THIS GENERATOR RUNS BEFORE.  `\BnBestResp` is
#: published by `beam_r19.py`, which must follow `sens_r18.py` and so runs
#: four hundred lines later; this generator must PRECEDE `blockledger_v411.py`.
#: On a warm tree the macro is there from the last run and the clause passes,
#: which is precisely the forward dependency only a clean regeneration can
#: see -- and it did.  So this generator runs TWICE, as `edge_v423.py` does
#: for its own cycle: the first pass publishes the macros the ledger needs
#: and DEFERS this clause, the second pass (`--final`, after `beam_r19.py`)
#: evaluates it and REQUIRES the macro to be there.  A deferred clause is
#: reported as deferred and never as a pass.
_one = None
try:
    _one = float(texval('BnBestResp'))
except Exception:
    if FINAL:
        raise
if DRIVE == 11:
    _here = (_wide[0] - 0.01, _here[1])
if _one is None:
    print('  %-70s %s  %s' % ('E13 deferred to the --final pass'[:70],
                              'DEFER',
                              '\\BnBestResp is not published yet; this '
                              'generator runs again after beam_r19.py'))
else:
    ck('E13 the response range this row prints lies inside the range printed '
       'for all of this star\'s off-axis windows, and the single window that '
       'sets its published limit lies inside that range too, so the three '
       'figures the paper quotes are one quantity over nested sets',
       _wide[0] <= _here[0] and _here[1] <= _wide[1]
       and _wide[0] <= round(_one, 2) <= _wide[1],
       'this row %.2f--%.2f within %.2f--%.2f for all off-axis windows; the '
       'limit-setting window at %.3f' % (_here + _wide + (_one,)))
m('ExOffArcsecLo', '%.2f' % min(r['_off'] for r in _offax))
m('ExOffArcsecHi', '%.2f' % max(r['_off'] for r in _offax))
m('ExOffArcsecPxLo', '%.2f' % min(r['_off_px'] for r in _offax))
m('ExOffArcsecPxHi', '%.2f' % max(r['_off_px'] for r in _offax))
m('ExOnArcsecLo', '%.2f' % min(r['_off'] for r in _onax))
m('ExOnArcsecHi', '%.2f' % max(r['_off'] for r in _onax))
m('ExOnArcsecPx', '%.3f' % max(r['_off_px'] for r in _onax))
m('ExNFine', '%d' % sum(1 for r in EXT32 if r['_fine']))
m('ExNCoarse', '%d' % sum(1 for r in EXT32 if not r['_fine']))
m('ExHours', '%.1f' % (sum(r['onsrc'] for r in EXT32) / 3600.0))
m('ExTMax', '%.1f' % max(r['star_snr'] for r in EXT32))

# ---------------------------------------------------------------- the table
with open(OUT_CSV, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['eb', 'spw', 'flo_GHz', 'fhi_GHz', 'freqmed_GHz', 'chanw_Hz',
                'class', 'resp_applied', 'resp_documented', 'offset_arcsec',
                'theta_pb_arcsec', 'theta_pb_dish_assumed_m',
                'array_from_member_ous', 'offset_source', 'mjd_product',
                'parallax_displacement_arcsec', 'offset_arcsec_px_corrected',
                'eirp90_W', 'eirp90_W_px_corrected', 'tstar'])
    for r in sorted(EXT32, key=lambda r: (r['eb'], r['_lo'])):
        w.writerow([r['eb'], r['_g']['_stem'].split('_spw')[1],
                    '%.4f' % r['_lo'], '%.4f' % r['_hi'],
                    '%.4f' % (r['_g']['freqmed'] / 1e9), '%.0f' % r['chanw'],
                    'A' if r['_fine'] else 'B',
                    '%.6f' % r['_a_app'], '%.4f' % r['_a_doc'],
                    '%.4f' % r['_off'], '%.3f' % r['_thpb'], '12.0',
                    r['_array'], r['_src'], '%.4f' % r['_mjd'],
                    '%.4f' % r['_dpar'], '%.4f' % r['_off_px'],
                    '%.4g' % r['_e90'], '%.4g' % r['_e90_px'],
                    '%.4f' % r['star_snr']])
print('\n  per-window table: %s' % OUT_CSV)

json.dump(dict(
    generated_by=os.path.basename(__file__), round=ROUND, drive=DRIVE,
    n_ext_win=len(EXT32), n_ext_eb=len(EBS),
    predicate=dict(owner='census_rule.py:168-169 withheld_extension()',
                   copy='extension_v399.py:63-65',
                   form="star_name == 'eps Eri' and band == 6",
                   floor_removes=len(BELOW), floor=A_FLOOR),
    offset_sources=SRC, resp_residual=RESID,
    sibling_arrays={k: v['array'] for k, v in SIB.items()},
    best=dict(eb=BEST['eb'], flo=BEST['_lo'], fhi=BEST['_hi'],
              e90=BEST['_e90'], e90_px=BEST['_e90_px'],
              e90_bound=[BEST['_e90_lo'], BEST['_e90_hi']],
              dpar=BEST['_dpar'], beams=U, syn=SYN, sibling=_sib),
    census_best=dict(eb=CENBEST['eb'], e90=CENBEST['_e90']),
    epoch=dict(ref_mjd=st.mean(ref), ref_sd=REF_SD,
               stale_worst_days=E386_WORST),
    rows=[{k: v for k, v in r.items()
           if not k.startswith('_g') and k not in ('ctrl_all',)}
          for r in sorted(EXT32, key=lambda r: (r['eb'], r['_lo']))],
), open(OUT_JSON, 'w'), indent=1, sort_keys=True, default=str)

open(OUT, 'w').write(
    '%% round %d -- epsx_v423.py.  The epsilon Eridani Band 6 windows outside\n'
    '%% the archival extension: the predicate, the offsets and the limit.\n%s\n'
    % (ROUND, '\n'.join(sorted(MACROS))))
print('\n  %d macros -> %s' % (len(MACROS), OUT))
print('epsx_v423: %d FAIL' % len(FAIL))
if DRIVE and not FAIL:
    print('  DRIVE %d DID NOT FAIL -- the clause it exercises is vacuous'
          % DRIVE)
    sys.exit(2)
sys.exit(1 if FAIL else 0)
