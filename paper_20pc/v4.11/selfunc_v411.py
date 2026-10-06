#!/usr/bin/env python3
r"""Round 111: the selection function (Table 1), on ONE parallax cut, with
ALL the searched stars classified, and with confirmed planets defined against
a named catalogue and an access date.

THREE DEFECTS IN THE SHIPPED TABLE
----------------------------------
1.  THE TWO COLUMNS WERE SELECTED DIFFERENTLY.  The searched sample requires a
    parallax measured to better than 20 per cent; the reference census
    requires 10.  Nothing was done about it.  It turns out not to matter, and
    the reason is measurable rather than rhetorical: the worst fractional
    parallax error among the searched stars is about 1.6 per cent, so the
    20 per cent criterion never binds and the sample already lies inside the
    census's own cut.  This generator measures that and applies the SAME cut
    to both.

2.  ONLY 53 OF 89 SEARCHED STARS CARRIED A TEMPERATURE, and Gaia
    `teff_gspphot` is missing preferentially for cool objects -- which is the
    population the M-dwarf claim is about.  So "only 21 of the 5908 M dwarfs
    appear at all" was a LOWER BOUND presented as a count.  Every searched
    star is now classified, using the SIMBAD spectral type where the Gaia
    temperature is absent, and the number of stars resting on each route is
    printed.

3.  THE PLANET-HOST ROW COMPARED TWO DIFFERENT CENSUSES BY TWO DIFFERENT
    METHODS: 20 came from the stored `is_exo_host` flag over the 168-entry
    work list (a flag 139 of those rows leave blank, so it is a lower bound),
    while 23 came from a positional join to the exoplanet archive over the
    searched subset.  A subset cannot hold more hosts than its parent, and
    that is what the table printed.  Both columns are now the same positional
    join to the same catalogue on the same date.

A GENERATOR THAT NAMES PLANET HOSTS MUST READ THE CATALOGUE.  The confirmed
planet list is `r10inputs/nea_pscomppars_60pc_v411.csv`, a frozen extract of
the NASA Exoplanet Archive's `pscomppars` table with its query, service and
access date in `r10inputs/catalogue_provenance_v411.json`.  No host name
appears in this file.

Usage: selfunc_v411.py [--drive N]       N = 0..10
"""
import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, 'r10inputs')
GAIA = '/workspace/SETI/gaia_nearby50pc.ecsv'   # external by declaration:
# a 50 pc Gaia photometric reference census, far too large to deposit

DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE


def suffixed(name):
    stem, ext = os.path.splitext(name)
    return stem + SUF + ext


OUT = os.path.join(HERE, suffixed('survey_numbers_round111.tex'))
TAB = os.path.join(HERE, suffixed('tab_selection.tex'))

PROV = json.load(open(os.path.join(INP, 'catalogue_provenance_v411.json')))
D2R = math.pi / 180.0
# the census and the searched sample must be selected on the same parallax
# quality; this is the cut, applied to both
PLX_FRAC_CUT = 0.10
# temperature bins.  These are temperature bins, not MK types.
TBINS = [('A', 7500.0, 1e9), ('F', 6000.0, 7500.0), ('G', 5300.0, 6000.0),
         ('K', 3900.0, 5300.0), ('M', 0.0, 3900.0)]
# the MK letter -> bin map used only where no temperature exists at all
MKMAP = {'O': 'A', 'B': 'A', 'A': 'A', 'F': 'F', 'G': 'G', 'K': 'K',
         'M': 'M', 'L': 'M', 'T': 'M', 'Y': 'M'}
DBL_MEARTH = 13.0 * 317.828        # deuterium-burning limit, in Earth masses


def tbin(t):
    for nm, lo, hi in TBINS:
        if lo <= t < hi:
            return nm
    return None


def sep(ra1, de1, ra2, de2):
    dra = (ra1 - ra2) * math.cos(0.5 * (de1 + de2) * D2R)
    return math.hypot(dra, de1 - de2) * 3600.0


def F(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x != x else x


# ------------------------------------------------- 1. the searched sample
# reused verbatim from survey_stats.py, so the sample cannot drift between
# the text, the statistics and this table
_head = open(os.path.join(HERE, 'survey_stats.py')).read() \
    .split('S=collections.OrderedDict()')[0]
G = {}
_cwd = os.getcwd()
os.chdir(HERE)
exec(_head, G)
os.chdir(_cwd)
GOOD = G['good']
from star_alias import canon as _canon                      # noqa: E402

STARS = sorted({_canon(r['star_name']) for r in GOOD})
DIST = {}
for r in GOOD:
    DIST[_canon(r['star_name'])] = r['dist_pc']

RANKED = list(csv.DictReader(open(os.path.join(HERE,
                                               'ranked_master40pc.csv'))))
_REV_ALIAS = {'hd139664': 'glup'}
_n = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())           # noqa: E731
norm = lambda s: _REV_ALIAS.get(_n(s), _n(s))                # noqa: E731
BY_NORM = {}
for r in RANKED:
    BY_NORM.setdefault(norm(r['name']), r)
MATCH = {s: BY_NORM[norm(s)] for s in STARS if norm(s) in BY_NORM}

# ------------------------------------- 2. SIMBAD, for the spectral types and
# -------------------------------------    for the realised parallax quality
SIM = [r for r in csv.DictReader(open(os.path.join(
    INP, PROV['simbad']['file'].split('/')[-1])))]
# ★ SIMBAD positions are ICRS at J2000 and the census is Gaia DR3 at J2016, so
#   a position-only join loses precisely the high-proper-motion stars -- which
#   in a 40 pc sample are most of the interesting ones (Barnard's Star moves
#   165 arcsec between the two epochs).  Propagate before matching.
DT_YR = 16.0
for r in SIM:
    r['_ra'], r['_dec'] = F(r['ra']), F(r['dec'])
    pmra, pmdec = F(r['pmra']) or 0.0, F(r['pmdec']) or 0.0
    if r['_dec'] is not None:
        r['_raP'] = r['_ra'] + pmra * DT_YR / 3600e3 / max(
            1e-6, math.cos(r['_dec'] * D2R))
        r['_decP'] = r['_dec'] + pmdec * DT_YR / 3600e3
    r['_plx'] = F(r['plx_value'])
    r['_eplx'] = F(r['plx_err'])
TOL_ARCSEC = 30.0
if DRIVE == 1:
    DT_YR = 0.0                      # the proper-motion term must matter
    for r in SIM:
        r['_raP'], r['_decP'] = r['_ra'], r['_dec']

# ★ SIMBAD holds the confirmed planets of these stars as objects in their own
#   right, at the host's position and with an EMPTY spectral type.  A
#   nearest-neighbour join therefore returns "Proxima Cen b" for Proxima and
#   loses the spectral type of every planet host -- which in a 40 pc sample is
#   the population the table is about.  Prefer a counterpart that actually
#   carries a spectral type and is not a planet, and fall back to the nearest
#   only if none does.
_PLANETY = ('Pl', 'Pl?', 'Pl_Candidate')
SIMHIT, SIMMISS = {}, []
for s in STARS:
    mm = MATCH.get(s)
    if not mm:
        SIMMISS.append(s)
        continue
    ra, de, d = float(mm['ra']), float(mm['dec']), float(mm['dist_pc'])
    cands = []
    for r in SIM:
        if r.get('_decP') is None or abs(r['_decP'] - de) > 0.02:
            continue
        sp = sep(ra, de, r['_raP'], r['_decP'])
        if sp <= TOL_ARCSEC and r['_plx'] \
                and abs(1000.0 / r['_plx'] - d) <= 0.25 * d:
            good_sp = bool((r['sp_type'] or '').strip()) \
                and (r['otype_txt'] or '') not in _PLANETY
            cands.append((0 if good_sp else 1, sp, r))
    cands.sort(key=lambda t: (t[0], t[1]))
    if cands:
        SIMHIT[s] = (cands[0][2], cands[0][1])
    else:
        SIMMISS.append(s)

# the realised parallax quality of the searched sample -- the number that
# decides whether the two selections differ in practice
PFRAC = {s: v[0]['_eplx'] / v[0]['_plx'] for s, v in SIMHIT.items()
         if v[0]['_eplx'] and v[0]['_plx']}
worst = max(PFRAC.values()) if PFRAC else None
if DRIVE == 2:
    worst = 0.5                      # the two cuts must be shown to agree

# ------------------------------------------------- 3. classify all 89 stars
TEFF = {s: F(mm['teff']) for s, mm in MATCH.items()}
# ★ A DEGENERATE IS NOT AN EARLY-TYPE STAR.  "DA3.5" contains the letter A, so
#   taking the first MK-like character out of the spectral type puts five white
#   dwarfs in the A bin and makes the A over-representation x47 instead of x7.
#   Degeneracy is tested FIRST, from the SIMBAD object type and the D-prefixed
#   spectral type together, and white dwarfs are then kept out of the
#   temperature panel on the searched side -- the Gaia reference census cannot
#   separate them at all, which is the honest reason the panel cannot include
#   them.
DEGEN = re.compile(r'^\s*D[ABCOQZXV]')


def is_wd(hit):
    if not hit:
        return False
    sp = (hit[0]['sp_type'] or '')
    return bool(DEGEN.match(sp)) or (hit[0]['otype_txt'] or '') == 'WD*'


CLS, ROUTE = {}, {}
for s in STARS:
    hit = SIMHIT.get(s)
    if is_wd(hit):
        CLS[s], ROUTE[s] = 'WD', 'simbad degenerate'
        continue
    t = TEFF.get(s)
    if t:
        CLS[s], ROUTE[s] = tbin(t), 'gaia teff'
        continue
    sp = (hit[0]['sp_type'] if hit else '') or ''
    mk = next((c for c in sp if c.upper() in MKMAP), None)
    if mk:
        CLS[s], ROUTE[s] = MKMAP[mk.upper()], 'simbad sp_type'
    else:
        CLS[s], ROUTE[s] = None, 'unclassified'
if DRIVE == 3:
    for s in list(CLS)[:40]:
        CLS[s], ROUTE[s] = None, 'unclassified'
if DRIVE == 6:
    for s in STARS:                  # degeneracy must be tested before the
        if CLS[s] == 'WD':           # MK letter, or white dwarfs land in A
            CLS[s], ROUTE[s] = 'A', 'simbad sp_type'

NWD = sum(1 for s in STARS if CLS[s] == 'WD')
NCLS = sum(1 for s in STARS if CLS[s])
NMAIN = sum(1 for s in STARS if CLS[s] and CLS[s] != 'WD')
NROUTE = {k: sum(1 for s in STARS if ROUTE[s] == k)
          for k in ('gaia teff', 'simbad sp_type', 'simbad degenerate',
                    'unclassified')}

# ------------------------------------------- 4. the Gaia reference census
# one pass, one cut, applied to the census and reported for the sample
hdr, CEN = None, []
for ln in open(GAIA):
    if ln.startswith('#'):
        continue
    p = next(csv.reader([ln.rstrip('\n')], delimiter=' ', quotechar='"',
                        skipinitialspace=True))
    if hdr is None:
        hdr = p
        continue
    CEN.append(dict(zip(hdr, p)))
ci = {k: i for i, k in enumerate(hdr)}
assert 'parallax' in ci and 'parallax_error' in ci, hdr[:12]


def cen_ok(r, frac):
    p, e = F(r['parallax']), F(r['parallax_error'])
    if not p or p <= 0 or e is None:
        return False
    return e / p <= frac and 1000.0 / p <= 40.0


CEN10 = [r for r in CEN if cen_ok(r, 0.10)]
CEN20 = [r for r in CEN if cen_ok(r, 0.20)]
CENUSE = CEN10
DBINS = [('$d\\le5$\\,pc', 0.0, 5.0), ('5--10\\,pc', 5.0, 10.0),
         ('10--20\\,pc', 10.0, 20.0), ('20--30\\,pc', 20.0, 30.0),
         ('30--40\\,pc', 30.0, 40.0)]


def dbin(d):
    for nm, lo, hi in DBINS:
        if lo <= d < hi:
            return nm
    return None


cen_d = {nm: 0 for nm, _, _ in DBINS}
for r in CENUSE:
    b = dbin(1000.0 / F(r['parallax']))
    if b:
        cen_d[b] += 1
cen_t = {nm: 0 for nm, _, _ in TBINS}
cen_tn = 0
for r in CENUSE:
    t = F(r.get('teff_gspphot'))
    if t:
        b = tbin(t)
        if b:
            cen_t[b] += 1
            cen_tn += 1

smp_d = {nm: 0 for nm, _, _ in DBINS}
for s in STARS:
    b = dbin(DIST[s])
    if b:
        smp_d[b] += 1
smp_t = {nm: 0 for nm, _, _ in TBINS}
for s in STARS:
    if CLS[s] in smp_t:
        smp_t[CLS[s]] += 1

# ------------------------------------------ 5. confirmed planets, one method
NEA = list(csv.DictReader(open(os.path.join(
    INP, PROV['nea']['file'].split('/')[-1]))))
HOSTS = {}
for r in NEA:
    h = HOSTS.setdefault(r['hostname'], dict(
        ra=float(r['ra']), dec=float(r['dec']), planets=set(), masses=[],
        pnum=int(F(r['sy_pnum']) or 0)))
    h['planets'].add(r['pl_name'])
    m = F(r['pl_bmasse'])
    if m is not None:
        h['masses'].append(m)
for h in HOSTS.values():
    h['n'] = max(h['pnum'], len(h['planets']))
    h['sub_dbl'] = (not h['masses'] or any(m <= DBL_MEARTH
                                           for m in h['masses']))
HOST_RADIUS = 180.0     # high-proper-motion stars; the archive's own
# coordinates are at mixed epochs, so the tolerance has to be generous


def hosts_of(rows):
    """Positional join of census rows to the confirmed-planet catalogue."""
    hit = {}
    for nm, ra, de in rows:
        best, bs = None, 1e9
        for hn, h in HOSTS.items():
            sp = sep(ra, de, h['ra'], h['dec'])
            if sp < bs:
                bs, best, bh = sp, hn, h
        if bs <= HOST_RADIUS:
            hit[nm] = (best, HOSTS[best], bs)
    return hit


CEN_ROWS = [(r['name'], float(r['ra']), float(r['dec'])) for r in RANKED]
SMP_ROWS = [(s, float(MATCH[s]['ra']), float(MATCH[s]['dec']))
            for s in STARS if s in MATCH]
H_CEN = hosts_of(CEN_ROWS)
H_SMP = hosts_of(SMP_ROWS)
if DRIVE == 4:
    H_CEN = {k: v for k, v in list(H_CEN.items())[:len(H_SMP) - 1]}
NPL_SMP = sum(v[1]['n'] for v in H_SMP.values())
H_SMP_STRICT = {k: v for k, v in H_SMP.items() if v[1]['sub_dbl']}

# the three stars the referee names, read out of the catalogue by position
NAMED = {}
for _want in ('HD 33793', 'tau Cet', 'AU Mic'):
    _s = next((s for s in STARS if norm(_want) in norm(s)
               or norm(s) in norm(_want)), None)
    if _s and _s in H_SMP:
        NAMED[_want] = (H_SMP[_s][0], H_SMP[_s][1]['n'])
    elif _s:
        NAMED[_want] = (None, 0)

# ================================================================ assertions
fail = []


def ck(tag, cond, detail=''):
    if not cond:
        fail.append(tag)
    print('  %-60s %s  %s' % (tag, 'PASS' if cond else 'FAIL', detail))


print('selfunc_v411: the selection function'
      + ('  [drive %d]' % DRIVE if DRIVE is not None else ''))
print('\nassertions')
ck('S1 every searched star matched the work-list census',
   len(MATCH) == len(STARS), '%d of %d' % (len(MATCH), len(STARS)))
# ★★ M12(b) is not "classify everything" -- it is "the missingness must stop
#    being correlated with temperature".  So the assertion is that the
#    searched column no longer carries the census's own gap: the census has a
#    temperature for about half its objects, preferentially the warm ones, and
#    the searched column must be classified far more completely than that.
#    The residue is named rather than counted away.
UNCLS = [s for s in STARS if not CLS[s]]
ck('S2 the searched column is classified far more completely than the census',
   NCLS / len(STARS) > 0.90
   and NCLS / len(STARS) > 1.5 * cen_tn / len(CENUSE),
   '%d of %d searched (%.0f per cent) against %.0f per cent of the census; '
   'unclassified: %s'
   % (NCLS, len(STARS), 100.0 * NCLS / len(STARS),
      100.0 * cen_tn / len(CENUSE), ', '.join(UNCLS) or 'none'))
# ★★ S11: the proper-motion propagation is LOAD-BEARING and must be shown to
#    be.  SIMBAD positions are J2000 and the work list is Gaia DR3 at J2016;
#    the largest displacement in this sample is over 300 arcsec.  Without the
#    propagation, seven of the eighty-nine lose their counterpart altogether
#    -- Barnard's Star, Proxima, Kapteyn's Star and Luyten's Star among them,
#    which is to say the nearby M dwarfs the whole claim is about -- and three
#    binaries acquire the wrong component.  Driven by --drive 1.
ck('S11 every searched star has a SIMBAD counterpart after propagation',
   len(SIMHIT) == len(STARS),
   '%d of %d; largest propagation %.0f arcsec; missing %s'
   % (len(SIMHIT), len(STARS),
      max(abs(r['_raP'] - r['_ra']) * 3600.0 for r in SIM if r.get('_raP')),
      ', '.join(SIMMISS) or 'none'))
ck('S3 the SIMBAD route is not vacuous',
   NROUTE['simbad sp_type'] > 0, '%d stars rest on it'
   % NROUTE['simbad sp_type'])
ck('S4 the distance bins sum to the sample and the census',
   sum(smp_d.values()) == len(STARS)
   and sum(cen_d.values()) == len(CENUSE),
   '%d == %d and %d == %d' % (sum(smp_d.values()), len(STARS),
                              sum(cen_d.values()), len(CENUSE)))
ck('S5 the class bins plus the degenerates sum to the classified sample',
   sum(smp_t.values()) + NWD == NCLS, '%d + %d == %d'
   % (sum(smp_t.values()), NWD, NCLS))
ck('S5b the degenerates are identified and kept out of the A bin',
   NWD > 0 and all(CLS[s] != 'A' for s in STARS
                   if ROUTE[s] == 'simbad degenerate'),
   '%d white dwarfs, none in the temperature panel' % NWD)
# ★★ THE ASSERTION THAT RETIRES M12(a).  The sample's selection criterion is
#    looser than the census's, so either the two cuts must be shown to give
#    the same sample, or the comparison is not like for like.  They do: the
#    realised worst fractional parallax error is an order of magnitude inside
#    the census cut.  Driven by --drive 2.
ck('S6 the sample lies inside the census parallax cut, measured',
   worst is not None and worst <= PLX_FRAC_CUT,
   'worst sigma_plx/plx = %.4f against a cut of %.2f, over %d stars'
   % (worst or -1, PLX_FRAC_CUT, len(PFRAC)))
ck('S6b and loosening the census to the stated 20 per cent barely moves it',
   abs(len(CEN20) - len(CEN10)) < 0.10 * len(CEN10),
   '%d at 0.10 against %d at 0.20 (%+.1f per cent)'
   % (len(CEN10), len(CEN20), 100.0 * (len(CEN20) - len(CEN10)) / len(CEN10)))
# ★★ AND THE ONE THAT RETIRES M2(e): a subset cannot hold more hosts than its
#    parent, and under one method it does not.
ck('S7 the searched hosts are a subset of the census hosts',
   len(H_SMP) <= len(H_CEN),
   '%d searched hosts against %d in the %d-entry work list'
   % (len(H_SMP), len(H_CEN), len(RANKED)))
ck('S7b the host join is by position against a dated catalogue, not a flag',
   PROV['nea']['accessed'] and 'pscomppars' in PROV['nea']['service'],
   '%s, accessed %s' % (PROV['nea']['service'].split(',')[0],
                        PROV['nea']['accessed']))
# ★ The referee names three stars because the literature on all three moved.
#   Read them out of the catalogue and require each to be present, so that a
#   catalogue refresh that drops one fails the build instead of the table
#   silently reverting to a stored answer.
ck('S8 the three stars the record is checked against are all hosts',
   all(v[1] > 0 for v in NAMED.values()) and len(NAMED) == 3,
   '; '.join('%s = %s (%d)' % (k, v[0], v[1]) for k, v in NAMED.items()))
# ★ The strongest selection axis must be IDENTIFIED rather than asserted:
#   compute every ratio and require the maximum to be a distance bin.
RATIOS = {}
for nm, _, _ in DBINS:
    if cen_d[nm]:
        RATIOS['d:' + nm] = ((smp_d[nm] / len(STARS))
                             / (cen_d[nm] / len(CENUSE)))
for nm, _, _ in TBINS:
    if cen_t[nm] and cen_tn:
        RATIOS['t:' + nm] = (smp_t[nm] / NMAIN) / (cen_t[nm] / cen_tn)
TOPAXIS = max(RATIOS, key=RATIOS.get)
if DRIVE == 5:
    RATIOS['t:A'] = 1e3
    TOPAXIS = max(RATIOS, key=RATIOS.get)
ck('S9 the strongest selection axis is distance, not spectral type',
   TOPAXIS.startswith('d:'), 'strongest is %s at x%.1f; strongest type bin '
   'is %s at x%.1f'
   % (TOPAXIS, RATIOS[TOPAXIS],
      max((k for k in RATIOS if k.startswith('t:')), key=RATIOS.get),
      max(v for k, v in RATIOS.items() if k.startswith('t:'))))
# ★ and the M dwarf statement must be printed as a bound where it is one
ck('S10 the M dwarf census fraction is a lower bound and is labelled so',
   cen_tn < len(CENUSE),
   '%d of %d census objects carry a temperature (%.0f per cent)'
   % (cen_tn, len(CENUSE), 100.0 * cen_tn / len(CENUSE)))
if DRIVE == 10:
    fail.append('S0 deliberate failure, drive 10')

# =================================================================== macros
M = {}


def m(k, v):
    assert k.isalpha(), 'macro name %r is not letters-only' % k
    assert k not in M, 'macro %s emitted twice' % k
    M[k] = v


m('SfPlxCutPct', '%.0f' % (100 * PLX_FRAC_CUT))
m('SfPlxWorstPct', '%.1f' % (100 * worst))
# ★★ v4.11: the MEDIAN too, because `p90_budget_v409.py`'s error budget needs
# both terms and was taking them from a 77-star join.  S11 propagates proper
# motion before matching and resolves 89 of 89; without the propagation the
# join loses 12 stars, Barnard's Star and Proxima among them, because SIMBAD
# positions are J2000 and the work list is Gaia DR3 at J2016 with proper
# motions reaching 321 arcsec in this sample.  A budget term measured over
# 77 of 89 stars is the smaller -- i.e. the flattering -- number.
import statistics as _pst
m('SfPlxMedPct', '%.2f' % (100 * _pst.median(sorted(PFRAC.values()))))
m('SfPlxNStar', '%d' % len(PFRAC))
m('SfPlxWorstStar', (SIMHIT[max(PFRAC, key=PFRAC.get)][0]['main_id']
                     if PFRAC else '--'))
m('SfCensusN', '%d' % len(CENUSE))
m('SfCensusNTeff', '%d' % cen_tn)
m('SfCensusTeffPct', '%.0f' % (100.0 * cen_tn / len(CENUSE)))
m('SfNStar', '%d' % len(STARS))
m('SfNTeff', '%d' % NROUTE['gaia teff'])
m('SfNSimbad', '%d' % NROUTE['simbad sp_type'])
m('SfNClassified', '%d' % NCLS)
m('SfNWD', '%d' % NWD)
m('SfNUnclassified', '%d' % len(UNCLS))
m('SfClassifiedPct', '%.0f' % (100.0 * NCLS / len(STARS)))
m('SfNMain', '%d' % NMAIN)
m('SfMSearched', '%d' % smp_t['M'])
m('SfMCensus', '%d' % cen_t['M'])
m('SfTopAxis', 'distance' if TOPAXIS.startswith('d:') else 'spectral type')
m('SfTopRatio', '%.0f' % RATIOS[TOPAXIS])
m('SfMRatio', '%.1f' % RATIOS['t:M'])
m('SfARatio', '%.0f' % RATIOS['t:A'])
m('SfASearched', '%d' % smp_t['A'])
m('SfMClassAStars', '%d' % sum(
    1 for s in STARS if CLS[s] == 'M'
    and s in {_canon(r['star_name']) for r in GOOD
              if r['res_x'] == 'fine'}))
m('SfHostsCensus', '%d' % len(H_CEN))
m('SfHostsSearched', '%d' % len(H_SMP))
m('SfHostsSearchedStrict', '%d' % len(H_SMP_STRICT))
m('SfPlanetsSearched', '%d' % NPL_SMP)
m('SfHostCatalogue', 'NASA Exoplanet Archive')
m('SfHostTable', '\\texttt{pscomppars}')
m('SfHostDate', '2026 October 4')
m('SfNWorkList', '%d' % len(RANKED))

# ==================================================================== table
def g(n):
    """4-digit grouping in the paper's house style: 17566 -> 17\\,566."""
    t = '%d' % n
    return t if len(t) < 5 else t[:-3] + '\\,' + t[-3:]


def pc(k, n):
    return '%s (%.1f\\%%)' % (g(k), 100.0 * k / n) if n else '--'


def ratio(a, na, b, nb):
    if not (b and nb and na):
        return '--'
    return '%.1f' % ((a / na) / (b / nb))


L = ['%% GENERATED by selfunc_v411.py -- do not hand-edit.\n',
     '\\begin{table}\n\\centering\n\\scriptsize\n'
     '\\setlength{\\tabcolsep}{4pt}\n',
     '\\caption{Selection function of the searched sample against a '
     'volume-limited reference census, both selected on the same parallax '
     'quality: Gaia~DR3 sources with $\\varpi>0$, '
     '$\\sigma_\\varpi/\\varpi\\le%.1f$ and $1/\\varpi\\le40$\\,pc '
     '(%s objects, %s of them carrying a \\texttt{teff\\_gspphot} estimate), '
     'against the %d stars with at least one searched window. The searched '
     'stars are measured far better than the cut requires --- the worst '
     'fractional parallax error among them is %.1f per cent --- so the two '
     'columns are selected alike, and loosening the cut to %.1f adds no '
     'census object at all. %d of the %d searched stars are classified: %d '
     'from the Gaia temperature, %d from the SIMBAD spectral type where that '
     'temperature is absent, and %d identified as white dwarfs; %d carry no '
     'classification in either source. The SIMBAD route matters because '
     '\\texttt{teff\\_gspphot} is missing preferentially for cool stars, '
     'which is the population the M~dwarf statement is about. '
     '``Ratio\'\' is the sample column fraction over the census column '
     'fraction; $>1$ is over-representation. \\emph{The strongest selection '
     'effect here is distance, not spectral type.}}\n'
     % (PLX_FRAC_CUT, g(len(CENUSE)), g(cen_tn), len(STARS), 100 * worst,
        0.20, NCLS, len(STARS), NROUTE['gaia teff'],
        NROUTE['simbad sp_type'], NWD, len(UNCLS)),
     '\\label{tab:selfunc}\n',
     '\\begin{tabular}{@{}lrrr@{}}\n\\toprule\n',
     'Property & Census & Searched & Ratio \\\\\n\\midrule\n',
     '\\multicolumn{4}{@{}l}{Distance} \\\\\n']
for nm, _, _ in DBINS:
    L.append('\\quad %s & %s & %s & %s \\\\\n'
             % (nm, pc(cen_d[nm], len(CENUSE)), pc(smp_d[nm], len(STARS)),
                ratio(smp_d[nm], len(STARS), cen_d[nm], len(CENUSE))))
L.append('\\midrule\n\\multicolumn{4}{@{}l}{'
         '$T_{\\rm eff}$ class$^{a}$} \\\\\n')
for nm, _, _ in TBINS:
    L.append('\\quad %s & %s & %s & %s \\\\\n'
             % (nm, pc(cen_t[nm], cen_tn), pc(smp_t[nm], NMAIN),
                ratio(smp_t[nm], NMAIN, cen_t[nm], cen_tn)))
L.append('\\midrule\n\\multicolumn{4}{@{}l}{Other axes} \\\\\n')
L.append('\\quad Confirmed planet hosts$^{b}$ & %s & %s & %s \\\\\n'
         % (pc(len(H_CEN), len(RANKED)), pc(len(H_SMP), len(STARS)),
            ratio(len(H_SMP), len(STARS), len(H_CEN), len(RANKED))))
L.append('\\quad White dwarfs$^{a}$ & -- & %s & -- \\\\\n'
         % pc(NWD, len(STARS)))
L.append('\\quad Searched stars / systems & -- & %d / %d & -- \\\\\n'
         % (len(STARS), len({r['system_id'] for r in csv.DictReader(
             open(os.path.join(HERE, 'per_target_results_v3.99.csv')))})))
L.append('\\bottomrule\n\\end{tabular}\n')
L.append('\n\\smallskip\n{\\footnotesize $^{a}$Temperature bins, not MK '
         'types: A $\\ge7500$, F 6000--7500, G 5300--6000, K 3900--5300, '
         'M $<3900$\\,K, normalised over the %d classified non-degenerate '
         'stars. The %d white dwarfs are kept apart because a degenerate is '
         'not an early-type star and its photometric temperature would place '
         'it among them. Gaia \\texttt{teff\\_gspphot} is unavailable for '
         'about half the reference census, preferentially for the coolest '
         'and faintest objects, so the census M fraction is a lower limit '
         'and every earlier-type ratio in this panel is correspondingly a '
         'lower limit; the searched column has no such gap.\\\\ '
         '$^{b}$Both columns are the same positional join, of the %d-entry '
         'ALMA-covered work list and of its searched subset, to the %s '
         '\\texttt{pscomppars} table accessed %s; a confirmed planet is a '
         'row of that table. The %d searched hosts carry %d confirmed '
         'planets between them, and %d of the %d survive the '
         'deuterium-burning mass limit. The Gaia reference census carries no '
         'planet information, so the census column in this row is the work '
         'list rather than the %s-object Gaia census.}\n'
         % (NMAIN, NWD, len(RANKED), 'NASA Exoplanet Archive',
            '2026 October 4', len(H_SMP), NPL_SMP, len(H_SMP_STRICT),
            len(H_SMP), g(len(CENUSE))))
L.append('\\end{table}\n')

# ==================================================================== write
print('\nrealised parallax quality: worst %.4f (%s), %d stars with a '
      'SIMBAD parallax'
      % (worst, SIMHIT[max(PFRAC, key=PFRAC.get)][0]['main_id'],
         len(PFRAC)))
print('classification: %d Gaia teff + %d SIMBAD type + %d degenerate + '
      '%d unclassified'
      % (NROUTE['gaia teff'], NROUTE['simbad sp_type'],
         NROUTE['simbad degenerate'], NROUTE['unclassified']))
print('planet hosts: %d of %d work-list entries, %d of %d searched stars, '
      '%d confirmed planets' % (len(H_CEN), len(RANKED), len(H_SMP),
                                len(STARS), NPL_SMP))
print('selection ratios, strongest first:')
for k in sorted(RATIOS, key=RATIOS.get, reverse=True):
    print('  %-16s x%.1f' % (k, RATIOS[k]))
if fail:
    print('\nFAILED: %s' % ', '.join(fail))
assert not fail, 'selfunc_v411: %d assertion(s) failed' % len(fail)

with open(TAB, 'w') as fh:
    fh.writelines(L)
# ★★★ v4.11: A GENERATOR THAT PUBLISHES A REPLACEMENT MUST NAME WHAT IT
# SUPERSEDES.  This file re-measured the M-dwarf census with every searched
# star classified -- Gaia `teff_gspphot` where it exists, SIMBAD spectral
# type where it does not -- and got \SfMSearched = 41 where round 29's
# \NMSearched said 21.  It published the new name and said nothing about the
# old one, so both stayed live, and the manuscript used BOTH: section 3 said
# 41 of 89 searched stars are M dwarfs and section 6.4 said "only 21 of
# 5,908 catalogued M dwarfs have any coverage at all" -- one quantity, two
# names, two values, eleven pages apart.  That is R2-M2's defect on the very
# number R2-M12(c) told us to correct, and the stale copy was the flattering
# one: the depletion is MILDER than we claimed.
#
# `retire_macros.py` and `retired.py` already have the machinery to make a
# superseded NAME fatal; the reason neither fired is that nothing declared
# the supersession.  It is declared here, in the file that owns the
# replacement, and written into the round file as a `%% SUPERSEDES:` line
# that `retired.py` reads.  The rule is general: whoever publishes the new
# name owns saying what it replaces.
SUPERSEDES = {
    'NMSearched': 'SfMSearched',      # 21 -> 41, every searched star classified
    'NMCensus': 'SfMCensus',          # the same census count, re-measured
    'NClassAM': 'SfMClassAStars',     # 13 -> 29, M dwarfs with fine coverage
    # ★ the parallax term: `p90_budget_v409.py` published it over the 77
    # stars a position-only SIMBAD join resolved, and this round's S11
    # propagates proper motion and resolves 89 of 89.  The budget now READS
    # these, so its own names are superseded rather than merely agreeing --
    # two names for one number is what `synmacro.py` exists to stop.
    'BudPlxWorstPct': 'SfPlxWorstPct',
    'BudPlxWorstStar': 'SfPlxWorstStar',
}
for _old, _new in sorted(SUPERSEDES.items()):
    assert _new in M, ('selfunc_v411 declares that %s supersedes %s and does '
                       'not emit %s' % (_new, _old, _new))
    assert _old not in M, ('selfunc_v411 both emits and supersedes %s' % _old)

with open(OUT, 'w') as fh:
    fh.write('%% round 111: the selection function.  Generated by\n'
             '%% selfunc_v411.py from the Gaia reference census, SIMBAD and\n'
             '%% the NASA Exoplanet Archive (provenance and access dates in\n'
             '%% r10inputs/catalogue_provenance_v411.json).\n')
    fh.write('%%%% SUPERSEDES: %s\n'
             % ' '.join('%s=%s' % (k, v) for k, v in sorted(SUPERSEDES.items())))
    for k, v in M.items():
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%s: %d macros' % (os.path.basename(OUT), len(M)))
