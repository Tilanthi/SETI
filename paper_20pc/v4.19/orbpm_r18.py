#!/usr/bin/env python3
r"""round 810 -> survey_numbers_round810.tex, orbpm_r18.json

ORBITAL MOTION IN THE EXTRACTION POSITION.

The extraction propagates each star's Gaia DR3 position to the observation
epoch with its DR3 proper motion.  For a single star that is exact to the
annual parallax, which is treated elsewhere.  For a component of a bound pair
it is not: the DR3 five-parameter solution absorbs the component's position
and its instantaneous velocity at the DR3 reference epoch, and nothing else,
so what is left over is the CURVATURE of the orbit,

    D(t) = | r(t) - r(t_0) - \dot r(t_0) (t - t_0) |,      t_0 = 2016.0,

evaluated for the searched component's barycentric orbit.  That is the
quantity computed here, for every searched component of a multiple and every
block that covers it, and compared with that block's own synthesised beam
through the same normalised dirty beam the omitted parallax already uses.

THREE ROUTES, AND EACH ROW SAYS WHICH IT TOOK.

  A  a published visual orbit (Sixth Catalog of Orbits of Visual Binary
     Stars) exists for the pair the star belongs to.  D(t) is then computed
     from the orbit: a measurement, not a bound.  The searched component's
     share of the relative orbit is f = M_other / M_total; where the masses
     are not published f = 1 is used, which is the ceiling.
  B  a companion is located -- resolved by Gaia DR3 or measured in the
     Washington Double Star catalogue -- but no orbit is published.  The
     PROJECTED separation is a lower bound on the true separation, so
     GM/rho^2 is an upper bound on the orbital acceleration and
     D <= 2 pi^2 M_other dt^2 / (rho^2 d^3) is an upper bound on the
     displacement.  The same separation puts a floor under the period, and
     the quadratic form is only used where dt is a small fraction of it.
  C  the Gaia DR3 astrometry is disturbed -- a non-single-star solution, a
     multiple-peak detection, an elevated RUWE -- but no companion is
     located.  No orbit can be bounded from an indicator, and this file does
     not pretend otherwise: the row is flagged, and the worst displacement
     any orbit consistent with the non-detection could produce is reported
     beside it.

THE METHOD IS CHECKED AGAINST THE SURVEY'S OWN SIRIUS MEASUREMENT.  Three
blocks hold Sirius A's continuum at 26-46 sigma, and its centroid lies
3.10-3.75 arcsec from the position a linear propagation of the Hipparcos-2
solution predicts.  The orbit of Bond et al. (2017), with their masses,
predicts 3.67 arcsec in a direction 7-13 degrees from the three measured
ones -- inside the measured centroid scatter.  Nothing in that comparison is
fitted.  A second, independent check: the same orbit predicts Sirius B's
orbital velocity at 2016.0 to be 298 mas/yr, and the difference between the
DR3 proper motion of B and the long-term motion of the system is 320 mas/yr.

    python3 orbpm_r18.py [--out DIR] [--drive N]

--drive 1..9 breaks one assertion each; --drive 0 perturbs nothing but does
not write a path production reads.
"""
import bisect
import collections
import csv
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: in the tree the generator and the paper are the same directory
PAPER = HERE
sys.path.insert(0, PAPER)
from star_alias import canon, PAIRS                               # noqa: E402

ROUND = 810
DRIVE = None
OUTDIR = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round810%s.tex' % SUF)
OUTJS = os.path.join(OUTDIR, 'orbpm_r18%s.json' % SUF)

GAIA_EPOCH = 2016.0                 # gaiadr3.gaia_source ref_epoch
GAIA_BASELINE_YR = 34.0 / 12.0      # DR3 astrometric baseline
HIP_EPOCH = 1991.25                 # Hipparcos-2 reference epoch
HG_INTERVAL_YR = GAIA_EPOCH - HIP_EPOCH
EXPLAIN_ARCSEC = 20.0               # see the flag clause in section 5
FOURPI2 = 4.0 * math.pi ** 2        # GM_sun in AU^3 yr^-2
# The separation below which this sample shows Gaia DR3 does NOT list both
# components.  Measured from the sample itself, not assumed.
MACROS, FAILS = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' % name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAILS.append(label)


# ========================================================== 0. frozen inputs
H = json.load(open(os.path.join(HERE, 'r18inputs', 'pm', 'orbharvest_r18.json')))
STAR = H['stars']
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
PXJ = json.load(open(os.path.join(PAPER, 'r8inputs', 'parallax_loss_v404.json')))
PXB = {b['eb']: b for b in PXJ['blocks']}
FAMILY = PXJ['family']
WIDE = json.load(open(os.path.join(HERE, 'r18inputs', 'pm', 'orbwide_r18.json')))
R_SEARCH = WIDE['radius_arcsec']
PMAJ = json.load(open(os.path.join(HERE, 'r18inputs', 'pm', 'orbpma_r18.json')))['pma']
EPFIX = json.load(open(os.path.join(
    PAPER, 'epochfix_v415.json')))['measured_epochs']
AMETA = json.load(open(os.path.join(
    PAPER, 'archive_meta_v381.json')))['ebs']
SIRF = json.load(open(os.path.join(
    PAPER, 'r17inputs', 'siriusfield_r17.json')))

# Pecaut & Mamajek's main-sequence sequence, for the mass that enters the
# route-B ceiling and the route-A mass ratio.  A main-sequence relation
# OVERSTATES the mass of a pre-main-sequence star of the same luminosity, and
# every term it feeds is an upper bound, so the error is in the safe sense.
EEM = []
for _ln in open(os.path.join(HERE, 'r18inputs', 'pm', 'eem_mamajek.txt')):
    _p = _ln.split()
    if _ln.startswith('#') or len(_p) < 31:
        continue
    try:
        EEM.append((float(_p[13]), float(_p[30])))
    except ValueError:
        pass
EEM.sort()
assert len(EEM) >= 60, len(EEM)
assert EEM[0][0] < 0 and EEM[-1][0] > 17, (EEM[0], EEM[-1])


def mass_of(MG):
    """Main-sequence mass from the absolute G magnitude, interpolated."""
    if MG <= EEM[0][0]:
        return EEM[0][1]
    if MG >= EEM[-1][0]:
        return EEM[-1][1]
    j = bisect.bisect_left([e[0] for e in EEM], MG)
    (x0, y0), (x1, y1) = EEM[j - 1], EEM[j]
    return y0 + (y1 - y0) * (MG - x0) / (x1 - x0)


# ======================================================= 1. the block epochs
# Two measured sources, then interpolation on the execution-block identifier,
# which the archive assigns in time order.  The interpolation is used only
# where it is bracketed tightly, and the bracket is carried and asserted.
_KNOWN = {}
for _e, _v in EPFIX.items():
    _KNOWN[_e] = float(_v[0])
for _e, _v in AMETA.items():
    if _v.get('t_min') and _e not in _KNOWN:
        _KNOWN[_e] = min(float(x) for x in _v['t_min'])
_HX = sorted({(int(e.split('_')[1][1:], 16), t) for e, t in _KNOWN.items()})
_HXK = [p[0] for p in _HX]


def mjd_to_yr(mjd):
    return 2000.0 + (mjd - 51544.5) / 365.25


def epoch_of(eb):
    """(decimal year, bracket half-width in years, provenance)."""
    if eb in _KNOWN:
        return mjd_to_yr(_KNOWN[eb]), 0.0, 'measured'
    h = int(eb.split('_')[1][1:], 16)
    j = bisect.bisect_left(_HXK, h)
    lo, hi = _HX[max(0, j - 1)], _HX[min(len(_HX) - 1, j)]
    if hi[0] == lo[0]:
        return mjd_to_yr(lo[1]), 0.0, 'interpolated'
    if DRIVE == 6:                     # an unbracketed interpolation must fail
        lo, hi = _HX[0], _HX[-1]
    t = lo[1] + (hi[1] - lo[1]) * (h - lo[0]) / (hi[0] - lo[0])
    return (mjd_to_yr(t), abs(mjd_to_yr(hi[1]) - mjd_to_yr(lo[1])) / 2.0,
            'interpolated')


# ============================================== 2. the beam response, reused
def retained(beams, fam):
    """The normalised dirty beam at a displacement, from the same measured
    library the omitted parallax is corrected with.  Outside the library's
    abscissa the answer is not a number but a refusal: beyond ~0.65 of a beam
    the displacement puts the phase wrong on the longest baselines and a
    scalar correction is not legitimate."""
    F = FAMILY[fam]
    x, y = F['x'], F['med']
    if DRIVE == 1:                     # a different beam model must show
        y = [min(1.0, v * 1.05) for v in y]
    if beams <= x[0]:
        return 1.0 - (1.0 - y[0]) * beams / x[0], True
    if beams > x[-1]:
        return y[-1], False
    j = bisect.bisect_left(x, beams)
    return y[j - 1] + (y[j] - y[j - 1]) * (beams - x[j - 1]) / (
        x[j] - x[j - 1]), True


# ============================================================ 3. the orbits
def _f(s):
    try:
        return float(s.strip())
    except ValueError:
        return None


ORB6, ORB6_SKIP = [], 0
for ln in H['orb6_raw'].split('\n'):
    if len(ln) < 230 or not re.match(r'^\d{6}', ln):
        continue
    o = dict(wds=ln[19:29].strip(), dd=ln[30:37].strip(),
             comp=ln[37:44].strip() or 'AB',
             P=_f(ln[81:92]), Pu=ln[92:93], a=_f(ln[105:114]), au=ln[114:115],
             i=_f(ln[125:133]), Om=_f(ln[143:151]),
             T=_f(ln[162:174]), Tu=ln[174:175],
             e=_f(ln[187:195]), w=_f(ln[205:213]),
             grade=ln[233:234].strip(), ref=ln[237:245].strip())
    if None in (o['P'], o['a'], o['i'], o['Om'], o['T'], o['e'], o['w']):
        ORB6_SKIP += 1
        continue
    # units -> years and arcsec
    o['P'] = {'y': 1.0, 'd': 1 / 365.25, 'c': 100.0, 'h': 1 / 8766.0}.get(
        o['Pu'], None) and o['P'] * {'y': 1.0, 'd': 1 / 365.25, 'c': 100.0,
                                     'h': 1 / 8766.0}[o['Pu']] \
        if o['Pu'] in ('y', 'd', 'c', 'h') else None
    o['a'] = {'a': 1.0, 'm': 1e-3, 'M': 60.0}.get(o['au'], None) and \
        o['a'] * {'a': 1.0, 'm': 1e-3, 'M': 60.0}[o['au']] \
        if o['au'] in ('a', 'm', 'M') else None
    if o['Tu'] == 'y':
        pass
    elif o['Tu'] == 'd':                       # modified Julian day
        o['T'] = mjd_to_yr(o['T'] if o['T'] < 1e5 else o['T'] - 2400000.5)
    elif o['Tu'] == 'c':
        o['T'] = o['T'] * 100.0
    else:
        o['T'] = None
    if None in (o['P'], o['a'], o['T']):
        ORB6_SKIP += 1
        continue
    ORB6.append(o)
ORB6_BY = collections.defaultdict(list)
for o in ORB6:
    ORB6_BY[o['wds']].append(o)


def kepler(M, e):
    M = math.fmod(M, 2 * math.pi)
    E = M if e < 0.8 else math.pi
    for _ in range(300):
        d = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= d
        if abs(d) < 1e-14:
            break
    return E


def relpos(o, t):
    """(north, east) of the secondary relative to the primary, arcsec."""
    a, i = o['a'], math.radians(o['i'])
    Om, w, e = math.radians(o['Om']), math.radians(o['w']), o['e']
    ci, cO, sO, cw, sw = (math.cos(i), math.cos(Om), math.sin(Om),
                          math.cos(w), math.sin(w))
    A = a * (cw * cO - sw * sO * ci)
    B = a * (cw * sO + sw * cO * ci)
    F = -a * (sw * cO + cw * sO * ci)
    G = -a * (sw * sO - cw * cO * ci)
    E = kepler(2 * math.pi * (t - o['T']) / o['P'], e)
    X, Y = math.cos(E) - e, math.sqrt(1 - e * e) * math.sin(E)
    return A * X + F * Y, B * X + G * Y


def curvature(o, t, t0=GAIA_EPOCH, h=1e-3):
    """|r(t) - r(t0) - rdot(t0)(t-t0)| of the RELATIVE orbit, arcsec, and
    its two components."""
    n0, e0 = relpos(o, t0)
    n1, e1 = relpos(o, t0 + h)
    nm, em = relpos(o, t0 - h)
    vn, ve = (n1 - nm) / (2 * h), (e1 - em) / (2 * h)
    n, e = relpos(o, t)
    return (n - n0 - vn * (t - t0), e - e0 - ve * (t - t0))


# ============== 4. the multiplicity census, from our own catalogue outwards
CENSUS_STARS = sorted({canon(r['star_name']) for r in CAT})
EBS = collections.defaultdict(set)
WIN = collections.defaultdict(list)
for r in CAT:
    EBS[canon(r['star_name'])].add(r['eb'])
    WIN[canon(r['star_name'])].append(r)

# ★ One searched component is NOT in the released per-window catalogue: the
#   companion in V343 Nor, whose four re-extracted windows are deposited
#   separately and which carries an attributed crossing.  It is read out of
#   that deposit rather than named here, and its astrometry is taken from the
#   Gaia DR3 source the primary's own neighbour list holds, so no coordinate
#   is typed.
REPAIRED = list(csv.DictReader(open(os.path.join(PAPER, 'repaired_v409.csv'))))
_BYSID = {str(STAR[s]['gaia']['source_id']): s for s in CENSUS_STARS}
_NRM = {re.sub(r'[^a-z0-9]', '', s.lower()): s for s in CENSUS_STARS}


def repaired_star(name):
    """A repaired row's star, resolved to the census by identifier."""
    n = canon(name.split(' [')[0])
    if n in CENSUS_STARS:
        return n
    mm = re.match(r'^GaiaDR3[_ ](\d+)$', n)
    if mm and mm.group(1) in _BYSID:
        return _BYSID[mm.group(1)]
    k = re.sub(r'[^a-z0-9]', '', n.lower())
    if k in _NRM:
        return _NRM[k]
    return n


_RSTARS = {repaired_star(r['star']) for r in REPAIRED}
EXTRA = sorted(_RSTARS - set(CENSUS_STARS))
assert len(EXTRA) == 1, EXTRA
XSTAR = EXTRA[0]
XPARENT = [s for s in CENSUS_STARS
           if canon(s) == canon(XSTAR.rstrip('B').strip())]
assert len(XPARENT) == 1, (XSTAR, XPARENT)
_xc = [n for n in WIDE['stars'][XPARENT[0]]
       if n['source_id'] != STAR[XPARENT[0]]['gaia']['source_id']
       and n['parallax'] and abs(n['parallax']
                                 - STAR[XPARENT[0]]['gaia']['parallax']) < 1.0]
assert len(_xc) == 1, (XSTAR, _xc)
# ★ The companion must NOT inherit the primary's SIMBAD hierarchy: the
#   primary's WDS identifier names the primary's own inner pair, and letting
#   it through here would attach that inner orbit to the wrong star.  The
#   companion's record carries no identifier, so it takes the separation
#   route on the pair Gaia itself resolves.
STAR[XSTAR] = dict(gaia=_xc[0], neighbours=[], nss={},
                   simbad=(STAR[XPARENT[0]]['simbad'] if DRIVE == 8 else {}),
                   worklist=dict(ra=_xc[0]['ra'], dec=_xc[0]['dec'],
                                 pmra=_xc[0]['pmra'], pmdec=_xc[0]['pmdec'],
                                 dist_pc=1000.0 / _xc[0]['parallax'],
                                 gaia_source_id=str(_xc[0]['source_id']),
                                 name=XSTAR))
# separations in the wide harvest are measured from the PRIMARY, so they are
# recomputed from the companion's own position before they are used
WIDE['stars'][XSTAR] = []
for _n in WIDE['stars'][XPARENT[0]]:
    _m = dict(_n)
    _m['sep_arcsec'] = math.hypot(
        (_n['ra'] - _xc[0]['ra']) * math.cos(math.radians(_xc[0]['dec'])) * 3600,
        (_n['dec'] - _xc[0]['dec']) * 3600)
    WIDE['stars'][XSTAR].append(_m)
for r in REPAIRED:
    if repaired_star(r['star']) == XSTAR:
        EBS[XSTAR].add(r['eb'])
        WIN[XSTAR].append(dict(eb=r['eb'], eirp_p90_adopted_W=''))
CENSUS_STARS.append(XSTAR)
CENSUS_STARS.sort()
PAIRED = set()
for a, b in PAIRS:
    PAIRED.add(canon(a))
    PAIRED.add(canon(b))

WDSROW = collections.defaultdict(list)
for r in H['wds']:
    WDSROW[r['WDS']].append(r)


def wds_ids(s):
    out = []
    for i in (STAR[s]['simbad'].get('ids') or []):
        mm = re.match(r'^WDS\s+J(\d{5}[+-]\d{4})(\S*)$', i.strip())
        if mm:
            out.append((mm.group(1), mm.group(2)))
    return out


def letters(tag):
    """The capital component letters a WDS/ORB6 component tag names."""
    return {c for c in tag if c.isupper()}


PARTNER = {}
for a, b in PAIRS:
    if canon(a) in CENSUS_STARS and canon(b) in CENSUS_STARS:
        PARTNER[canon(a)] = canon(b)
        PARTNER[canon(b)] = canon(a)

MULT = {}
for s in CENSUS_STARS:
    v = STAR[s]
    g = v['gaia']
    plx = g['parallax']
    d_pc = 1000.0 / plx
    MG = g['phot_g_mean_mag'] + 5 - 5 * math.log10(d_pc)
    m1 = mass_of(MG)
    # (a) a Gaia DR3 source inside 400 arcsec sharing the parallax and the
    #     proper motion.  Its separation is measured, not catalogued.
    comp = []
    for n in WIDE['stars'][s]:
        if n['source_id'] == g['source_id'] or not n['parallax']:
            continue
        if abs(n['parallax'] - plx) > 0.1 * plx + 3 * (
                (n['parallax_error'] or 0) + (g['parallax_error'] or 0)):
            continue
        dpm = math.hypot((n['pmra'] or 0) - (g['pmra'] or 0),
                         (n['pmdec'] or 0) - (g['pmdec'] or 0))
        if dpm < 0.25 * math.hypot(g['pmra'] or 0, g['pmdec'] or 0) + 5:
            comp.append(n)
    # (a2) the catalogue's own bound pairs.  Two components of one system can
    #      be separated enough in proper motion to FAIL a common-motion test
    #      precisely when the orbit is fast, which is the case this file is
    #      about, so our own pair list overrides the test rather than being
    #      checked by it.
    if s in PARTNER:
        pid = STAR[PARTNER[s]]['gaia']['source_id']
        if pid not in {c['source_id'] for c in comp}:
            hit = [n for n in WIDE['stars'][s] if n['source_id'] == pid]
            assert hit, ('the catalogue declares %s and %s a bound pair and '
                         'the partner is not within %.0f arcsec'
                         % (s, PARTNER[s], R_SEARCH))
            comp += hit
    # (b) the Washington Double Star catalogue, but only where Gaia DR3
    #     cannot list the companion: blended inside about two arcsec, or a
    #     primary too bright for DR3 astrometry.  A faint wide WDS entry is
    #     a line-of-sight candidate and is not evidence of a bound pair.
    wrows = []
    for wid, tag in wds_ids(s):
        mine = letters(tag) or {'A'}
        for r in WDSROW.get(wid, []):
            c = r['Comp'] or 'AB'
            rho = max(float(r['sep2'] or 0), float(r['sep1'] or 0))
            # 999.9 is the catalogue's "separation not measured" sentinel and
            # 0.0 means below its own precision; neither is a measurement.
            if not (letters(c) & mine) or rho <= 0.05 or rho >= 900.0:
                continue
            orbit = any(letters(o['comp']) & letters(c)
                        for o in ORB6_BY.get(wid, []))
            # A pair seen once, or last seen before this century, is a
            # candidate and not a measurement.  Sirius's own catalogue holds
            # four such entries around the companion, one of them from 1975.
            if (r['Nobs'] or 0) < 3 or (r['Obs2'] or 0) < 2000:
                continue
            if rho <= 2.0 or orbit:
                wrows.append((wid, c, rho, orbit))
    # (c) the astrometric indicators
    astro = dict(ruwe=g.get('ruwe'), aen=g.get('astrometric_excess_noise'),
                 aen_sig=g.get('astrometric_excess_noise_sig'),
                 nss=g.get('non_single_star'),
                 multipeak=g.get('ipd_frac_multi_peak'),
                 nss_orbit=len(v['nss'].get('nss_two_body_orbit') or []),
                 nss_accel=len(v['nss'].get('nss_acceleration_astro') or []))
    # (c) the Hipparcos-Gaia proper-motion anomaly, where the star has a
    #     Hipparcos epoch at all
    pr = PMAJ.get(s)
    pma = pma_err = pma_snr = None
    if pr and pr.get('PMaRAH2EG3b') is not None:
        pma = math.hypot(pr['PMaRAH2EG3b'], pr['PMaDEH2EG3b'])
        pma_err = math.hypot(pr.get('e_PMaRAH2EG3b') or 0.0,
                             pr.get('e_PMaDEH2EG3b') or 0.0)
        pma_snr = pr.get('snrPMaH2EG3b')
    disturbed = bool((g.get('ruwe') or 0) > 1.4 or astro['nss'] or
                     (g.get('ipd_frac_multi_peak') or 0) >= 10 or
                     astro['nss_orbit'] or astro['nss_accel'] or
                     (pma_snr or 0) >= 3.0)
    MULT[s] = dict(d_pc=d_pc, MG=MG, m1=m1, gaia_comp=comp, wds=wrows,
                   astro=astro, disturbed=disturbed,
                   pma=pma, pma_err=pma_err, pma_snr=pma_snr,
                   in_census_pair=s in PAIRED,
                   gmag=g['phot_g_mean_mag'],
                   source_id=g['source_id'])

# A star is a component of a multiple if any of the three says so.
MULTIPLE = [s for s in CENSUS_STARS
            if MULT[s]['gaia_comp'] or MULT[s]['wds']
            or MULT[s]['in_census_pair'] or MULT[s]['disturbed']]
LOCATED = [s for s in MULTIPLE if MULT[s]['gaia_comp'] or MULT[s]['wds']]

# ---- the orbit, where one is published for the pair this star belongs to
# ★ THE IDENTITY TEST THAT HAS TO COME FIRST.  SIMBAD resolves a component's
#   designation to the SYSTEM for several of these pairs, so a record reached
#   by name can belong to the other component.  Where the record carries a
#   Gaia DR3 identifier it is compared with the star's own, and an INNER-pair
#   orbit -- one whose component tag names sub-components, like Aa,Ab -- is
#   accepted only where that comparison succeeds.  Two records in this sample
#   do name the wrong component, and the test finds them.
def simbad_gaia(s):
    """True, False or None: whether SIMBAD's record for this star carries
    this star's own Gaia DR3 source identifier."""
    g = [i for i in (STAR[s]['simbad'].get('ids') or [])
         if i.strip().startswith('Gaia DR3')]
    if not g:
        return None
    return any(str(MULT[s]['source_id']) in i for i in g)


SIMBAD_WRONG = sorted(s for s in CENSUS_STARS if simbad_gaia(s) is False)
for s in MULTIPLE:
    mine = set()
    for wid, tag in wds_ids(s):
        mine |= (letters(tag) or {'A'})
    orbs, refused = [], []
    for wid, _t in wds_ids(s):
        for o in ORB6_BY.get(wid, []):
            if not (letters(o['comp']) & mine):
                continue
            inner = any(c.islower() for c in o['comp'])
            if (simbad_gaia(s) is False) or (inner and simbad_gaia(s) is not True):
                refused.append(o)
                continue
            orbs.append(o)
    MULT[s]['orbits'] = orbs
    MULT[s]['orbits_refused'] = refused

# ---- the mass fraction f = M_other / M_total, where both masses are had
BOND = dict(MA=2.063, MB=1.018, ref='Bond et al. (2017)')
for s in MULTIPLE:
    u = MULT[s]
    f, fsrc = 1.0, 'ceiling'
    if s == 'alf CMa B':
        f = BOND['MA'] / (BOND['MA'] + BOND['MB'])
        fsrc = 'Bond2017'
    elif u['gaia_comp']:
        c = min(u['gaia_comp'], key=lambda n: n['sep_arcsec'])
        m2 = mass_of((c['phot_g_mean_mag'] or 20) + 5 - 5 * math.log10(u['d_pc']))
        f, fsrc = m2 / (u['m1'] + m2), 'gaiaphot'
        u['m2'] = m2
    u['f'], u['f_src'] = f, fsrc

if DRIVE == 1:                      # the mass fraction must matter
    for s in MULTIPLE:
        MULT[s]['f'] = 1.0

# ================================================== 5. the per-block answer
def bound_B(u, sep, sep_src, m2ceil, dt):
    """The ceiling a projected separation puts on the displacement.

    The true separation is at least the projected one, so GM/rho^2 is at
    least as large as the true orbital acceleration and D <= a dt^2 / 2.
    The same separation puts a floor under the period; beyond a quarter of
    that the quadratic expansion is not a bound any more, and the component
    is held instead by the only thing that always holds it, which is its own
    orbit: it cannot travel further than the orbit is wide.
    """
    s_au = sep * u['d_pc']
    Pmin = math.sqrt(s_au ** 3 / (u['m1'] + m2ceil))
    extent = 2.0 * sep
    curv = 2 * math.pi ** 2 * m2ceil * dt ** 2 / (sep ** 2 * u['d_pc'] ** 3)
    if DRIVE == 7:                     # the quarter-period guard must bite
        return curv, Pmin, 'driven: unguarded acceleration ceiling'
    if abs(dt) > 0.25 * Pmin or curv > extent:
        return extent, Pmin, ('orbit-extent ceiling, twice rho=%.3f" (%s)'
                              % (sep, sep_src))
    return curv, Pmin, ('acceleration ceiling at rho=%.3f" (%s), '
                        'M2<=%.2f Msun, P>=%.1f yr'
                        % (sep, sep_src, m2ceil, Pmin))


ROWS = []
for s in MULTIPLE:
    u = MULT[s]
    # ★ the CLOSEST located companion, whichever catalogue found it: the
    #   acceleration goes as 1/rho^2, so a wide Gaia pair must not be allowed
    #   to stand in for a close one the double-star catalogue has measured.
    _cands = [(n['sep_arcsec'], 'GaiaDR3') for n in u['gaia_comp']] \
        + [(w[2], 'WDS') for w in u['wds']]
    sep, sep_src = min(_cands) if _cands else (None, None)
    assert sep is None or sep > 0, (s, sep)
    u['sep'] = sep
    u['sep_src'] = sep_src
    m2ceil = u.get('m2') or u['m1']        # unseen companion <= the primary
    for eb in sorted(EBS[s]):
        if eb not in PXB:
            continue
        t, ehw, eprov = epoch_of(eb)
        dt = 0.0 if DRIVE == 5 else t - GAIA_EPOCH
        syn, fam = PXB[eb]['syn'], PXB[eb]['fam']
        # ★ EVERY ROUTE THE STAR HAS DATA FOR IS EVALUATED, AND THE LARGEST
        #   ANSWER IS THE ONE REPORTED.  A star with a wide companion and a
        #   disturbed solution would otherwise be handed the reassuring
        #   number: the wide pair curves the track by nothing, and the thing
        #   that is actually pulling the astrometry is the one not described.
        cand, Pmin = [], None
        for o in u['orbits']:
            dn, de = curvature(o, t)
            cand.append((u['f'] * math.hypot(dn, de), 'A',
                         '%s P=%.4gyr a=%.4g" grade %s'
                         % (o['ref'], o['P'], o['a'], o['grade']), o['P']))
            # A hierarchical system has more than one orbit.  Where a
            # companion is located whose separation the published orbit does
            # not describe, its own ceiling is added rather than ignored.
            if sep is not None and not (o['a'] / 3 < sep < o['a'] * 3):
                b = bound_B(u, sep, sep_src, m2ceil, dt)
                cand[-1] = (cand[-1][0] + b[0], 'A',
                            cand[-1][2] + ' + ' + b[2], cand[-1][3])
        if sep is not None and not u['orbits']:
            b = bound_B(u, sep, sep_src, m2ceil, dt)
            cand.append((b[0], 'B', b[2], b[1]))
        if u['pma'] is not None:
            # The Hipparcos-Gaia proper-motion anomaly is the difference
            # between the DR3 proper motion and the long-term mean motion.
            # With a constant acceleration across that interval it is
            # a*DT/2, so a = 2*PMa/DT and D = PMa*dt^2/DT.  The anomaly is
            # taken at its measured value plus two standard errors.
            pma = u['pma'] + 2 * u['pma_err']
            cand.append((pma * 1e-3 * dt ** 2 / HG_INTERVAL_YR, 'C',
                         'PMa %.3f+2x%.3f mas/yr over %.2f yr '
                         '(Kervella et al. 2022)'
                         % (u['pma'], u['pma_err'], HG_INTERVAL_YR), None))
        if cand:
            D, route, note, Pmin = max(cand)
        else:
            D, route = None, 'D'
            note = ('no companion located, no Hipparcos epoch, RUWE %.2f: '
                    'flagged, not quantified' % (u['astro']['ruwe'] or 0))
        beams = None if D is None else D / syn
        ret, ok = (None, False) if D is None else retained(beams, fam)
        # ★ a residual indication no route covers: the Gaia solution is
        #   disturbed, no proper-motion anomaly exists, and the only located
        #   companion is one Gaia resolves and so cannot be disturbing it.
        # A companion Gaia itself lists is a sufficient explanation for a
        # disturbed solution out to the scale on which Gaia's own windowing
        # and deblending degrade, taken here as 20 arcsec; beyond that, an
        # elevated RUWE is saying something the located pair does not.
        explained = any(math.hypot(*relpos(o, GAIA_EPOCH)) <= EXPLAIN_ARCSEC
                        for o in u['orbits']) or (sep is not None
                                                  and sep <= EXPLAIN_ARCSEC)
        unq = bool(u['disturbed'] and u['pma'] is None and not explained)
        ROWS.append(dict(star=s, eb=eb, t=t, epoch_hw=ehw, epoch_src=eprov,
                         dt=dt, route=route, D=D, syn=syn, fam=fam,
                         beams=beams, retained=ret, correctable=ok,
                         unquantified=unq,
                         sep=sep, sep_src=sep_src, f=u['f'], f_src=u['f_src'],
                         Pmin=Pmin, note=note,
                         nwin=sum(1 for r in WIN[s] if r['eb'] == eb)))

BYSTAR = collections.defaultdict(list)
for r in ROWS:
    BYSTAR[r['star']].append(r)

def tex(n):
    """The designation as the paper prints it."""
    return (n.replace('alf CMa B', r'Sirius~B')
            .replace('gam Vir', r'$\gamma$~Virginis')
            .replace('eta Crv', r'$\eta$~Corvi')
            .replace('eta Cru', r'$\eta$~Crucis')
            .replace('bet Pic', r'$\beta$~Pictoris')
            .replace('tau Cet', r'$\tau$~Ceti')
            .replace('gam Lep', r'$\gamma$~Leporis')
            .replace('NAME ', '').replace('V star ', '')
            .replace('HD14055', 'HD 14055').replace('HD161868', 'HD 161868')
            .split(' Gaia DR3')[0].split(' [')[0])


# ============================================================ 6. the checks
print('\n--- the Sirius validation, which nothing here fits')
fA = BOND['MB'] / (BOND['MA'] + BOND['MB'])
SIR = [o for o in ORB6_BY['06451-1643'] if o['comp'] == 'AB']
ck('exactly one published Sirius AB orbit', len(SIR) == 1, str(len(SIR)))
sir = SIR[0]
A = SIRF['component_A']
pred, meas = [], []
for b in SIRF['blocks']:
    y, mo, dd = (int(x) for x in b['date_obs'].split('-'))
    t = y + (mo - 0.5) / 12.0 + (dd - 15) / 365.25
    n0, e0 = relpos(sir, A['epoch'])
    n, e = relpos(sir, t)
    _fa = fA
    if DRIVE == 4:                     # the mass ratio must matter
        _fa = 1.0
    if DRIVE == 3:                     # the sense of the barycentre must too
        _fa = -fA
    dn, de = -_fa * (n - n0), -_fa * (e - e0)
    ara = A['ra'] + A['pmra'] / 3.6e6 * (t - A['epoch']) / math.cos(
        math.radians(A['dec']))
    ade = A['dec'] + A['pmdec'] / 3.6e6 * (t - A['epoch'])
    mdn = (b['cen_dec'] - ade) * 3600
    mde = (b['cen_ra'] - ara) * 3600 * math.cos(math.radians(b['cen_dec']))
    pa_p = math.degrees(math.atan2(de, dn)) % 360
    pa_m = math.degrees(math.atan2(mde, mdn)) % 360
    pred.append((math.hypot(dn, de), pa_p))
    meas.append((math.hypot(mdn, mde), pa_m))
    print('    %s  predicted %.3f" at %.1f deg   measured %.3f" at %.1f deg'
          % (b['date_obs'], pred[-1][0], pa_p, meas[-1][0], pa_m))
PRED_SEP = statistics.mean(p[0] for p in pred)
MEAS_LO, MEAS_HI = min(x[0] for x in meas), max(x[0] for x in meas)
PA_RES = max(abs((p[1] - q[1] + 180) % 360 - 180) for p, q in zip(pred, meas))
ck('S1 the orbit predicts the measured Sirius A displacement',
   MEAS_LO <= PRED_SEP <= MEAS_HI,
   'predicted %.3f, measured %.3f-%.3f' % (PRED_SEP, MEAS_LO, MEAS_HI))
SCAT_DEG = math.degrees(SIRF['centroid_scatter_arcsec'] / PRED_SEP)
# The comparison that matters is of two vectors, not of two angles: the
# block-to-block scatter of the measured centroid is itself 0.78 arcsec.
def _mean_vec(v):
    return (statistics.mean(x[0] * math.cos(math.radians(x[1])) for x in v),
            statistics.mean(x[0] * math.sin(math.radians(x[1])) for x in v))


_pv, _mv = _mean_vec(pred), _mean_vec(meas)
VEC_RES = math.hypot(_pv[0] - _mv[0], _pv[1] - _mv[1])
MEAS_MEAN = math.hypot(*_mv)
ck('S2 and in the measured direction, inside the centroid scatter',
   VEC_RES < SIRF['centroid_scatter_arcsec'],
   'mean measured %.3f arcsec at %.1f deg, mean predicted %.3f at %.1f, '
   'vector residual %.3f against a block-to-block centroid scatter of %.3f'
   % (MEAS_MEAN, math.degrees(math.atan2(_mv[1], _mv[0])) % 360,
      math.hypot(*_pv), math.degrees(math.atan2(_pv[1], _pv[0])) % 360,
      VEC_RES, SIRF['centroid_scatter_arcsec']))
# the orbital velocity of B at 2016 against DR3 minus the long-term motion
h = 1e-3
n1, e1 = relpos(sir, GAIA_EPOCH + h)
nm, em = relpos(sir, GAIA_EPOCH - h)
fB = BOND['MA'] / (BOND['MA'] + BOND['MB'])
vmod = 1000 * fB * math.hypot((n1 - nm) / (2 * h), (e1 - em) / (2 * h))
if DRIVE == 2:
    vmod *= 2.0
gB = STAR['alf CMa B']['gaia']
vobs = math.hypot(gB['pmra'] - A['pmra'], gB['pmdec'] - A['pmdec'])
ck('S3 B\'s DR3 proper motion carries the orbital velocity the orbit predicts',
   abs(vmod / vobs - 1) < 0.15, 'model %.0f, observed %.0f mas/yr' % (vmod, vobs))

print('\n--- the measurement')
ck('M1 every census star resolves to one Gaia DR3 solution at epoch 2016',
   all(STAR[s]['gaia'] for s in CENSUS_STARS) and
   all(abs(STAR[s]['gaia'].get('ref_epoch', GAIA_EPOCH) - GAIA_EPOCH) < 1e-6
       for s in CENSUS_STARS))
_wl = max(math.hypot((STAR[s]['worklist']['ra'] - STAR[s]['gaia']['ra'])
                     * math.cos(math.radians(STAR[s]['gaia']['dec'])) * 3600,
                     (STAR[s]['worklist']['dec'] - STAR[s]['gaia']['dec']) * 3600)
          for s in CENSUS_STARS)
ck('M2 the work list IS that solution, so the propagation is the one modelled',
   _wl < 0.5, 'worst %.3f arcsec' % _wl)
_iw = [r['epoch_hw'] for r in ROWS if r['epoch_src'] == 'interpolated']
_ii = [r['t'] for r in ROWS if r['epoch_src'] == 'interpolated']
_known_yr = [mjd_to_yr(v) for v in _KNOWN.values()]
ck('M3 every interpolated block epoch is bracketed inside a tenth of a year '
   'and inside the measured span',
   (not _iw or max(_iw) < 0.1)
   and (not _ii or (min(_known_yr) <= min(_ii) and max(_ii) <= max(_known_yr))),
   '%d interpolated, worst bracket %.3f yr, range %.2f-%.2f inside %.2f-%.2f'
   % (len(_iw), max(_iw) if _iw else 0,
      min(_ii) if _ii else 0, max(_ii) if _ii else 0,
      min(_known_yr), max(_known_yr)))
_qb = [r for r in ROWS if r['route'] == 'B' and r['Pmin']
       and abs(r['dt']) > 0.25 * r['Pmin']
       and not r['note'].startswith('orbit-extent')]
_qa = [r for r in ROWS if r['route'] == 'A' and r['Pmin']
       and abs(r['dt']) > 0.25 * r['Pmin']]
ck('M4 no route-B ceiling is quoted over a quarter of its own minimum period',
   not _qb,
   '%d route-B offenders; %d route-A rows exceed it legitimately, the orbit '
   'being integrated rather than expanded' % (len(_qb), len(_qa)))
ck('M5 the beam response is the one the omitted parallax already uses',
   abs(retained(0.6661454989247715, '12m')[0] - 0.4852870225697653) < 1e-9)
QUANT = [r for r in ROWS if r['D'] is not None]
_nc = [r for r in QUANT if not r['correctable']]
ck('M6 rows beyond the library are refused rather than extrapolated',
   all(r['beams'] > FAMILY[r['fam']]['x'][-1] for r in _nc),
   '%d refused' % len(_nc))
# Where a star has both an orbit and a proper-motion anomaly the two must
# agree in order of magnitude, or one of them is wrong.
_both = []
for s in BYSTAR:
    u = MULT[s]
    if u['orbits'] and u['pma'] and (u['pma_snr'] or 0) >= 3:
        w = max(BYSTAR[s], key=lambda r: abs(r['dt']))
        dc = (u['pma'] + 2 * u['pma_err']) * 1e-3 * w['dt'] ** 2 / HG_INTERVAL_YR
        _both.append((s, w['D'], dc, w['Pmin']))
ck('M7 orbit and proper-motion anomaly agree where both exist',
   all(P < HG_INTERVAL_YR or (b > 0 and 0.1 < a / b < 10)
       for s, a, b, P in _both),
   '; '.join('%s A=%.4f C=%.4f P=%.0fyr' % x for x in _both))
_rd = [r for r in ROWS if r['unquantified']]
ck('M8 every flagged row is flagged because there is nothing to measure',
   all(MULT[r['star']]['pma'] is None and MULT[r['star']]['disturbed']
       for r in _rd),
   '%d rows, %d stars: %s' % (len(_rd), len({r['star'] for r in _rd}),
                              sorted(tex(x) for x in {r['star'] for r in _rd})))

# the one number the paper leans on: does anything move?
WORST = max(QUANT, key=lambda r: r['beams'])
WORST_A = max([r for r in ROWS if r['route'] == 'A'], key=lambda r: r['beams'])
SIRROWS = BYSTAR['alf CMa B']
SIR_WORST = max(SIRROWS, key=lambda r: r['beams'])

# ============== 7. what it does to the limits, exactly as parallax does
from star_alias import sysname                                    # noqa: E402

RET = {(r['star'], r['eb']): r for r in QUANT}
LIM = {}
for r in QUANT:
    for w in WIN[r['star']]:
        if w['eb'] != r['eb']:
            continue
        base = float(w['eirp_p90_adopted_W'] or 0) or None
        if base:
            LIM.setdefault(r['star'], []).append(
                (base, base / r['retained'], r['route'], r['beams']))
MOVED = [(s, b, c, rt, bm) for s, v in LIM.items() for b, c, rt, bm in v
         if c / b - 1 > 0.01]
PERSYS = {}
for s, v in LIM.items():
    PERSYS[s] = (min(b for b, c, rt, bm in v), min(c for b, c, rt, bm in v))
SYSMOVE = {s: p[1] / p[0] - 1 for s, p in PERSYS.items() if p[1] / p[0] - 1 > 0.01}

# the survey's own headline: the median system limit, before and after
SYSBASE, SYSCORR = collections.defaultdict(list), collections.defaultdict(list)
for w in CAT:
    base = float(w['eirp_p90_adopted_W'] or 0)
    if not base:
        continue
    sy = sysname(w['star_name'])
    SYSBASE[sy].append(base)
    rr = RET.get((canon(w['star_name']), w['eb']))
    SYSCORR[sy].append(base / rr['retained'] if rr else base)
MED_BASE = statistics.median(min(v) for v in SYSBASE.values())
MED_CORR = statistics.median(min(v) for v in SYSCORR.values())
N_SYS = len(SYSBASE)

# a crossing cannot be created by an attenuation; say which crossings sit on
# a tested star and how far the worst of them is displaced
XR = [w for w in CAT if str(w['crossing']).strip().lower() in ('true', '1')]
XR_HIT = [(canon(w['star_name']), w['eb'],
           RET[(canon(w['star_name']), w['eb'])]['beams'])
          for w in XR if (canon(w['star_name']), w['eb']) in RET]
XR_FLAG = [(canon(w['star_name']), w['eb']) for w in XR
           if (canon(w['star_name']), w['eb']) not in RET
           and canon(w['star_name']) in BYSTAR]

print('\n--- the headline')
print('median system limit %.4g -> %.4g W over %d systems (%+.3f per cent)'
      % (MED_BASE, MED_CORR, N_SYS, 100 * (MED_CORR / MED_BASE - 1)))
print('crossings on a tested star: %d of %d, worst %.4f beams; '
      'unquantified: %d' % (len(XR_HIT), len(XR),
                            max([x[2] for x in XR_HIT] or [0]), len(XR_FLAG)))

print('\n--- per star')
hdr = '%-44s %-4s %5s %5s %8s %7s %8s %6s %5s'
print(hdr % ('star', 'rte', 'nblk', 'nwin', 'sep"', '|dt|max', 'D"max',
             'beams', 'ret'))


def _key(x):
    b = [r['beams'] for r in BYSTAR[x] if r['beams'] is not None]
    return (0 if b else -1, -max(b) if b else 0)


for s in sorted(BYSTAR, key=_key):
    rs = BYSTAR[s]
    w = max(rs, key=lambda r: (-1 if r['beams'] is None else r['beams']))
    print(hdr % (s, w['route'], len(rs), sum(r['nwin'] for r in rs),
                 '%.3f' % w['sep'] if w['sep'] else '--',
                 '%.2f' % max(abs(r['dt']) for r in rs),
                 '--' if w['D'] is None else '%.5f' % w['D'],
                 '--' if w['beams'] is None else '%.3f' % w['beams'],
                 '--' if w['retained'] is None else '%.3f' % w['retained']))

print('\nworst overall  : %s %s route %s %.3f beams, retained %.3f'
      % (WORST['star'], WORST['eb'], WORST['route'], WORST['beams'],
         WORST['retained']))
print('worst measured : %s route A %.3f beams, retained %.3f'
      % (WORST_A['star'], WORST_A['beams'], WORST_A['retained']))
print('Sirius B worst : %.4f arcsec = %.3f beams, retained %.3f'
      % (SIR_WORST['D'], SIR_WORST['beams'], SIR_WORST['retained']))
print('windows whose limit moves by >1 per cent: %d of %d'
      % (len(MOVED), sum(len(WIN[s]) for s in BYSTAR)))
print('systems whose best window moves by >1 per cent: %s' % SYSMOVE)

# ===================================================== 8. the last checks
_n0 = [r for r in QUANT if abs(r['dt']) > 5 and r['D'] > 0]
ck('M9 the archive really does reach years from the Gaia reference epoch',
   len(_n0) > 0 and max(abs(r['dt']) for r in ROWS) > 5,
   'worst |t - 2016| = %.2f yr, %d rows beyond five years'
   % (max(abs(r['dt']) for r in ROWS), len(_n0)))
# M10 is the check the companion's own identity defect would have failed:
# an orbit may only be attached to a star whose own data are consistent with
# the separation that orbit predicts.
#
# ★★★ AND THE TWO DESIGNATIONS IT NAMES WERE SWEPT, 2026-10-13 (integration).
# SIMBAD's name route returns the WRONG COMPONENT for both of them: resolving
# `2MASS J05241914-1601153 551040` gives `Gaia DR3 2983928735054717696`, which
# is the OTHER worklist entry's own source, and `V star TX PsA` gives
# `Gaia DR3 6603693881832177792`, which is WW PsA.  In both cases the
# catalogue's own `gaia_source_id` is the authority and this check refuses the
# name route, so nothing here is affected.
# ★ The question that remained was whether anything ELSE in the build resolves
# either designation by name, and the answer is NO, measured: the only
# generator in `make_all.sh` that touches a name service at all is
# `hosts_v399.py`, which reads a FROZEN harvest (`--requery` refreshes it by
# hand) and whose frozen file mentions neither designation; `lsr_r15.py` and
# `harvest_sptype_r18.py` are fetchers and are not in `make_all.sh`.  So the
# two wrong resolutions reach no published number by any route.  If a
# generator is ever added that resolves a star by name, it must key on
# `gaia_source_id` as this file does.
_mis = [s for s in BYSTAR if MULT[s]['orbits']
        and (simbad_gaia(s) is False
             or (any(c.islower() for o in MULT[s]['orbits']
                     for c in o['comp']) and simbad_gaia(s) is not True))]
_testable = [s for s in CENSUS_STARS if simbad_gaia(s) is not None]
_refused = sum(len(MULT[s].get('orbits_refused') or []) for s in MULTIPLE)
ck('M10 no star takes an inner-pair orbit it is not itself identified with',
   not _mis and _refused == 0 and len(_testable) > 0.5 * len(CENSUS_STARS),
   'offenders %s; %d of %d stars carry a Gaia identifier in SIMBAD, and %d '
   'of those name the WRONG component (%s); %d orbits refused on this test'
   % (_mis, len(_testable), len(CENSUS_STARS), len(SIMBAD_WRONG),
      ', '.join(SIMBAD_WRONG), _refused))
# M11 justifies the search radius by computing what a companion at it could
# do to the nearest star in the sample.
# star by star, with that star's own distance, its own epochs and its own
# smallest beam, against a companion mass above anything in the sample
M_CEIL = 3.0
_edge = []
for s in CENSUS_STARS:
    rs = [r for r in ROWS if r['star'] == s] or None
    ebs = [e for e in EBS[s] if e in PXB]
    if not ebs:
        continue
    dt = max(abs(epoch_of(e)[0] - GAIA_EPOCH) for e in ebs)
    syn = min(PXB[e]['syn'] for e in ebs)
    d = MULT[s]['d_pc']
    _rs = 6.0 if DRIVE == 9 else R_SEARCH
    _edge.append((2 * math.pi ** 2 * M_CEIL * dt ** 2
                  / (_rs ** 2 * d ** 3) / syn, s))
_ew = max(_edge)
ck('M11 a companion just outside the search radius could not matter',
   _ew[0] < 2e-3,
   'worst %s at %.1e of its own smallest beam, for %.1f Msun at %.0f arcsec'
   % (_ew[1], _ew[0], M_CEIL, 6.0 if DRIVE == 9 else R_SEARCH))

# M12 is the check that catches a unit error in the orbit catalogue, which
# is the silent failure this file is most exposed to: a semi-major axis read
# in milliarcseconds as arcseconds, or a period in days as years, changes the
# dynamical mass by orders of magnitude and nothing else would notice.
# ★ The photometric comparison is a main-sequence relation and says nothing
#   about a white dwarf, so it is not applied to one; and an orbit that
#   contributes less than a hundredth of a beam anywhere need not be
#   credible, only harmless.  Both exemptions are reported, not silent.
_dyn, _bad = [], []
for s in sorted(BYSTAR):
    u = MULT[s]
    wd = (STAR[s]['simbad'].get('basic') or [{}])[0].get('otype') == 'WD*'
    for o in u['orbits']:
        a_au = o['a'] * u['d_pc']
        if DRIVE == 10:
            a_au *= 1000.0
        mtot = a_au ** 3 / o['P'] ** 2
        mphot = u['m1'] + (u.get('m2') or u['m1'])
        wmax = max([r['beams'] for r in BYSTAR[s] if r['beams'] is not None]
                   or [0])
        _dyn.append((tex(s), o['ref'], mtot, mphot, wmax, wd))
        if wmax <= 0.01:
            continue
        if not (0.02 < mtot < 12.0):
            _bad.append((tex(s), o['ref'], mtot, 'implausible'))
        elif not wd and not (1 / 8.0 < mtot / mphot < 8.0):
            _bad.append((tex(s), o['ref'], mtot, 'disagrees with photometry'))
ck('M12 every orbit that matters gives a credible dynamical mass',
   not _bad,
   '%s | all: %s' % (_bad or 'none',
                     '; '.join('%s %s %.2f vs %.2f (%.3f beams%s)' % x
                               for x in _dyn)))

# ============================================================= 9. the macros
N_ORBIT = len([s for s in BYSTAR if MULT[s]['orbits']])
N_LOCATED = len([s for s in BYSTAR if MULT[s]['sep'] is not None])
N_COMPONENT = len([s for s in BYSTAR
                   if MULT[s]['orbits'] or MULT[s]['sep'] is not None])
N_INDONLY = len(BYSTAR) - N_COMPONENT
N_PMA = len([s for s in BYSTAR if MULT[s]['pma'] is not None])
FLAGSTARS = sorted({r['star'] for r in ROWS if r['unquantified']})
N_FLAG = len(FLAGSTARS)
FLAGWIN = sum(r['nwin'] for r in ROWS if r['unquantified'])


m('OmNStar', '%d' % len(CENSUS_STARS))
m('OmNTested', '%d' % len(BYSTAR))
m('OmNComponent', '%d' % N_COMPONENT)
m('OmNOrbit', '%d' % N_ORBIT)
m('OmNLocated', '%d' % N_LOCATED)
m('OmNIndOnly', '%d' % N_INDONLY)
m('OmNPma', '%d' % N_PMA)
m('OmNFlag', '%d' % N_FLAG)
m('OmFlagStars', ', '.join(tex(x) for x in FLAGSTARS[:-1])
  + ' and ' + tex(FLAGSTARS[-1]) if len(FLAGSTARS) > 1
  else tex(FLAGSTARS[0]))
m('OmNWin', '%d' % sum(r['nwin'] for r in ROWS))
m('OmNWinFlag', '%d' % FLAGWIN)
m('OmRadius', '%d' % int(R_SEARCH))
m('OmWorstStar', tex(WORST['star']))
m('OmWorstArcsec', '%.2f' % WORST['D'])
m('OmWorstBeams', '%.2f' % WORST['beams'])
m('OmWorstRetPct', '%.0f' % (100 * WORST['retained']))
m('OmWorstLossPct', '%.0f' % (100 * (1 / WORST['retained'] - 1)))
m('OmMeasStar', tex(WORST_A['star']))
m('OmMeasArcsec', '%.2f' % WORST_A['D'])
m('OmMeasBeams', '%.2f' % WORST_A['beams'])
m('OmMeasRetPct', '%.0f' % (100 * WORST_A['retained']))
m('OmSirArcsec', '%.2f' % SIR_WORST['D'])
m('OmSirBeams', '%.2f' % SIR_WORST['beams'])
m('OmSirLossPct', '%.0f' % (100 * (1 / SIR_WORST['retained'] - 1)))
m('OmSirPredArcsec', '%.2f' % PRED_SEP)
m('OmSirMeasLo', '%.2f' % MEAS_LO)
m('OmSirMeasHi', '%.2f' % MEAS_HI)
m('OmSirScatter', '%.2f' % SIRF['centroid_scatter_arcsec'])
m('OmSirVecRes', '%.2f' % VEC_RES)
m('OmSirVModel', '%.0f' % vmod)
m('OmSirVObs', '%.0f' % vobs)
m('OmSirOrbRef', 'BdH2017')
_sdyn = [d for d in _dyn if d[0] == 'Sirius~B'][0]
m('OmSirDynMass', '%.2f' % _sdyn[2])
m('OmSirPubMass', '%.2f' % (BOND['MA'] + BOND['MB']))
m('OmMedSysBase', '%.3g' % MED_BASE)
m('OmMedSysCorr', '%.3g' % MED_CORR)
m('OmMedSysShiftPct', '%.2f' % (100 * (MED_CORR / MED_BASE - 1)))
_tenth = sorted({r['star'] for r in QUANT if r['beams'] >= 0.1})
m('OmNTenth', '%d' % len(_tenth))
m('OmTenthStars', ', '.join(tex(x) for x in _tenth[:-1]) + ' and '
  + tex(_tenth[-1]) if len(_tenth) > 1 else tex(_tenth[0]))
m('OmNFlagComponent', '%d' % len([s for s in BYSTAR
                                  if (MULT[s]['orbits'] or MULT[s]['sep'])
                                  and not any(r['unquantified']
                                              for r in BYSTAR[s])]))
m('OmNSysMoved', '%d' % len(SYSMOVE))
m('OmSysMovedStars', ' and '.join(tex(x) for x in sorted(SYSMOVE)))
m('OmSysMovedMaxPct', '%.0f' % (100 * max(SYSMOVE.values())) if SYSMOVE else '0')
m('OmNCross', '%d' % len(XR))
m('OmNCrossTested', '%d' % len(XR_HIT))
m('OmCrossWorstBeams', '%.3f' % max([x[2] for x in XR_HIT] or [0]))
m('OmNCrossFlag', '%d' % len(XR_FLAG))
m('OmHGInterval', '%.2f' % HG_INTERVAL_YR)
# the span of the whole searched archive, not only of the tested stars, so
# that this number cannot disagree with the one the rest of the paper uses
_allt = [mjd_to_yr(_KNOWN[e]) for e in {r['eb'] for r in CAT}
         if e in PXB and e in _KNOWN]
m('OmEpochLo', '%d' % int(min(_allt)))
m('OmEpochHi', '%d' % int(max(_allt)))

with open(OUT, 'w') as fh:
    fh.write('%% orbpm_r18.py (round %d) -- orbital motion in the extraction\n'
             '%% position.  Generated; do not edit.\n' % ROUND)
    fh.write('\n'.join(MACROS) + '\n')
print('\nwrote %s, %d macros' % (OUT, len(MACROS)))

# the per-star flag, keyed on the designation the released catalogue uses,
# so that a table generator joins on an identifier and not on a rendering
FLAGCSV = os.path.join(OUTDIR, 'orbflags_r18%s.csv' % SUF)
from star_alias import released                                   # noqa: E402
with open(FLAGCSV, 'w', newline='') as fh:
    wr = csv.writer(fh)
    wr.writerow(['star_name', 'released', 'flag', 'route', 'companion_arcsec',
                 'companion_source', 'max_displacement_arcsec', 'max_beams',
                 'retained', 'note'])
    for st in sorted(BYSTAR):
        rs = [r for r in BYSTAR[st] if r['beams'] is not None]
        w = max(rs, key=lambda r: r['beams']) if rs else BYSTAR[st][0]
        unq = any(r['unquantified'] for r in BYSTAR[st])
        flag = ('unquantified' if unq else
                'component' if MULT[st]['sep'] is not None
                or MULT[st]['orbits'] else 'indicated')
        wr.writerow([st, released(st), flag, w['route'],
                     '' if MULT[st]['sep'] is None else '%.3f' % MULT[st]['sep'],
                     MULT[st]['sep_src'] or '',
                     '' if w['D'] is None else '%.5f' % w['D'],
                     '' if w['beams'] is None else '%.4f' % w['beams'],
                     '' if w['retained'] is None else '%.4f' % w['retained'],
                     w['note']])
print('wrote', FLAGCSV)

# ★★★★ M13: THE FROZEN COPY `make_tables_v328.py` READS MUST BE WHAT THIS
# GENERATOR COMPUTES.  `tab_perstar.tex` is generated 450 lines earlier in
# `make_all.sh` than this file can run -- it needs the catalogue's
# `eirp_p90_adopted_W`, which `smear_r15.py --deposit` writes long after the
# tables -- so the table reads `r18inputs/pm/orbflags_r18.csv` as a frozen
# input.  A frozen input nothing compares with the live measurement is a copy
# that drifts: this clause is the comparison, and it fails the build rather
# than letting the daggers in a published table describe an older
# computation.  It is checked on the FLAG COLUMN, which is all the table uses.
_FROZEN = os.path.join(PAPER, 'r18inputs', 'pm', 'orbflags_r18.csv')
if os.path.isfile(_FROZEN):
    _live = {r['star_name']: r['flag']
             for r in csv.DictReader(open(FLAGCSV))}
    if DRIVE == 13:
        _live[sorted(_live)[0]] = 'indicated'
    _froz = {r['star_name']: r['flag']
             for r in csv.DictReader(open(_FROZEN))}
    _bad = sorted(k for k in set(_live) | set(_froz)
                  if _live.get(k) != _froz.get(k))
    ck('M13 the frozen per-star flag file the table generator reads is what '
       'this generator computes',
       not _bad,
       'frozen %d rows, live %d rows, %d disagree%s'
       % (len(_froz), len(_live), len(_bad),
          '' if not _bad else ': ' + ', '.join('%s %r/%r'
                                               % (k, _froz.get(k),
                                                  _live.get(k))
                                               for k in _bad[:4])))
else:
    ck('M13 the frozen per-star flag file the table generator reads is what '
       'this generator computes', False,
       'the frozen file %r does not exist, so the table is joining against '
       'nothing' % _FROZEN)

json.dump(dict(_doc=__doc__, rows=ROWS,
               stars={s: {k: v for k, v in MULT[s].items()
                          if k not in ('gaia_comp', 'wds')}
                      for s in MULTIPLE},
               sirius=dict(pred=pred, meas=meas, pred_sep=PRED_SEP,
                           meas_lo=MEAS_LO, meas_hi=MEAS_HI,
                           pa_residual_deg=PA_RES, scatter_deg=SCAT_DEG,
                           vec_residual=VEC_RES, v_model=vmod, v_obs=vobs),
               headline=dict(med_base=MED_BASE, med_corr=MED_CORR,
                             n_sys=N_SYS),
               crossings=dict(n=len(XR), on_tested=XR_HIT, flagged=XR_FLAG),
               moved=MOVED, sysmove=SYSMOVE, macros=MACROS, fails=FAILS),
          open(OUTJS, 'w'), indent=1, default=str)
print('wrote', OUTJS)
if FAILS:
    print('FAILED:', FAILS)
    sys.exit(1)
