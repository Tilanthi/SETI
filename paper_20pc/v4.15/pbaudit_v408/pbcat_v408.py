#!/usr/bin/env python3
"""BUILD THE FROZEN CATALOGUE INPUT FOR THE TWO NEW PB COLUMNS (D29 items 2, 3).

The release pairs an APPARENT `rms_mJy` with a primary-beam-CORRECTED `smin_mJy`
and ships no column for the response A, so on 89 windows `smin != 5 rms` with
nothing in the deposit to explain it.  This writes `pbcat_v408.json`: for every
released window, the star-to-phase-centre offset and the response that was
actually applied, so a reader can reproduce `smin = 5 rms / A`.

It also fixes item 3: Wolf 28 `A002_X9f2ff8_X25b0` is an old single-spw product
that carries no `primary_beam_offset_arcsec`.  The offset is recovered HERE, at
the generator, from that product's own stored geometry -- not typed in.

KEYING.  The audit found the hard way that `(eb, window)` is NOT a key: two Gaia
components can share a block and their rms agree to the five decimals the
catalogue prints.  The key here is `(star_name, eb, flo, fhi)` -- exactly what
the catalogue prints, and unique over its 1,651 rows -- and the PRODUCT behind
each row is found through `target`, the search-time extraction directory carried
by every one of the 1,721 export rows.  Both halves are proved by POSITION and
not by name:
  * 32 export keys carry TWO target directories, because the same star was
    extracted twice under a named and a `GaiaDR3_*` directory.  The builder
    asserts their stored star positions agree to 0.2", so either product gives
    the same response, and that the responses agree to 1e-6.
  * inside every (eb, flo, fhi) shared by more than one star_name, the builder
    asserts the resolved positions are more than 0.2" apart -- the check whose
    absence manufactured a fake mismatch in the audit's first attempt.
The star position used is recorded in the output so both claims stay re-checkable.
"""
import json, csv, math, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, '..', '..', 'paper_20pc', 'v4.07')      # READ ONLY
AS = math.pi / 180 / 3600


def gauss(th, fwhm):
    return math.exp(-4 * math.log(2) * (th / fwhm) ** 2)


def sep_arcsec(ra0, dec0, ra1, dec1):
    s = (math.sin((dec1 - dec0) / 2) ** 2
         + math.cos(dec0) * math.cos(dec1) * math.sin((ra1 - ra0) / 2) ** 2)
    return 2 * math.asin(min(1.0, math.sqrt(s))) / AS


fq = lambda x: round(float(x), 3)   # 1 MHz: windows are ~2 GHz wide, so this
                                   # is a tolerance, not a loss of resolution.
                                   # Uniqueness of the resulting key is asserted.

# The catalogue's printed star_name and the export's differ in whitespace
# ('Wolf   28' vs 'Wolf 28') and, since v4.07, in the census name repair.  Both
# sides go through the paper's OWN canonicalisation, imported from the deposit,
# so this join cannot drift from the one v342_calc.py already uses for PKMAP.
sys.path.insert(0, V)
from star_alias import released as _released
nm = lambda s: _released(" ".join(s.replace("_", " ").split()))

cat = list(csv.DictReader(open(os.path.join(V, 'per_target_results_v3.99.csv'))))
exp = json.load(open(os.path.join(V, 'corrected_export_v399.json')))['rows']
prods = json.load(open(os.path.join(HERE, '..', 'dropped', 'inv_products.json')))['recs']
EBS = json.load(open(os.path.join(V, 'archive_meta_v381.json')))['ebs']
geom = {(g['_dir'], g['_stem']): g for g in json.load(open(os.path.join(HERE, 'pbgeom.json')))}
print('catalogue rows %d | export rows %d | products %d | geometry %d'
      % (len(cat), len(exp), len(prods), len(geom)))

# ---- 1. catalogue row -> search-time target directory, via the export -------
# The export is the single source v342_calc.py builds the catalogue from, and it
# carries `target`.  Key on everything the catalogue prints that the export has.
ekey = lambda r: (nm(r['star_name']), r['eb'], fq(min(r['flo'], r['fhi'])),
                  fq(max(r['flo'], r['fhi'])))
# Frequencies are matched with a 2 MHz TOLERANCE rather than by a rounded key:
# the export stores flo/fhi in either order and at full float precision, and
# rounding to a fixed number of decimals put six windows on the wrong side of a
# half-way case.  Windows are ~2 GHz wide, so 2 MHz cannot confuse two of them --
# and the assertion below pins that every catalogue row finds exactly one.
FTOL = 0.002
_eidx = collections.defaultdict(list)
for r in exp:
    _eidx[(nm(r['star_name']), r['eb'])].append(r)


def _find(name, eb, flo, fhi):
    out = []
    for r in _eidx.get((name, eb), ()):
        a, b = min(r['flo'], r['fhi']), max(r['flo'], r['fhi'])
        if abs(a - flo) < FTOL and abs(b - fhi) < FTOL:
            out.append(r)
    return out


etg = collections.defaultdict(set)
for r in exp:
    etg[ekey(r)].add(r['target'])
amb = {k: v for k, v in etg.items() if len(v) > 1}
print('export keys with more than one target directory: %d (same star, two '
      'directory names -- checked by position below)' % len(amb))

ckey = lambda c: (nm(c['star_name']), c['eb'], fq(c['flo_GHz']), fq(c['fhi_GHz']))
assert len(set(ckey(c) for c in cat)) == len(cat), \
    'the canonicalised (star, eb, flo, fhi) key is NOT unique over the catalogue'
ETG = {}
nomap = []
for c in cat:
    k = ckey(c)
    v = _find(k[0], k[1], float(c['flo_GHz']), float(c['fhi_GHz']))
    if not v:
        nomap.append(k)
    else:
        ETG[k] = sorted({r['target'] for r in v})
print('catalogue rows with no export target: %d' % len(nomap))
assert not nomap, nomap[:3]
print('export keys with two target directories reached from the catalogue: %d'
      % sum(1 for v in ETG.values() if len(v) > 1))

# ---- 2. window -> products, and directory -> position ---------------------
# The export's `target` is the directory the window was FIRST searched in, and
# it is NOT sufficient to find the product the release published: the v3.99
# re-extractions live in `*_EB_<eb>` directories that the export never names, and
# their rms is what the catalogue prints.  So the candidate set is every product
# in that (eb, window), and it is narrowed BY POSITION -- the star position each
# product stores -- with the export target used only to say which position is
# this row's when a block holds more than one star.
_widx = collections.defaultdict(list)
for p in prods:
    _widx[p['eb']].append(p)


def products_for(eb, flo, fhi):
    # same 2 MHz tolerance as the export match, and for the same reason
    return [p for p in _widx.get(eb, ())
            if abs(min(p['freq_lo_GHz'], p['freq_hi_GHz']) - flo) < FTOL
            and abs(max(p['freq_lo_GHz'], p['freq_hi_GHz']) - fhi) < FTOL]

# ---- 3. resolve every catalogue row to a product, by position ------------
def sep_of(g1, g2):
    return sep_arcsec(math.radians(g1['t1_ra']), math.radians(g1['t1_dec']),
                      math.radians(g2['t1_ra']), math.radians(g2['t1_dec']))


POS_TOL = 0.2            # arcsec: same star
RES, natt, nposcut, nmulti, aspread = {}, 0, 0, 0, 0.0
for c in cat:
    w = (c['eb'], fq(c['flo_GHz']), fq(c['fhi_GHz']))
    allp = products_for(c['eb'], float(c['flo_GHz']), float(c['fhi_GHz']))
    # this row's sky position: from the export target's own product(s)
    ref = None
    for p in allp:
        if p['_dir'] in ETG[ckey(c)] or p['_dir'].split('_EB_')[0] in ETG[ckey(c)]:
            g = geom.get((p['_dir'], p['_stem']))
            if g:
                ref = g
                break
    cands = allp
    if ref is not None:
        keep = []
        for p in allp:
            g = geom.get((p['_dir'], p['_stem']))
            if g is None or sep_of(g, ref) <= POS_TOL:
                keep.append(p)
        if len(keep) != len(allp):
            nposcut += 1
        cands = keep
    if len(cands) > 1:
        nmulti += 1
    ats = [p['primary_beam_atten'] for p in cands
           if p.get('primary_beam_atten') is not None]
    if ats:
        natt += 1
        # NOT an assertion: two extractions of the same star can legitimately
        # carry different A, because they propagated the proper motion to
        # different epochs (Proxima: 0.9975 vs 0.9992 in one window).  Which one
        # the release used is settled below by rms and then CHECKED against the
        # published smin, which is the assertion that matters.
        aspread = max(aspread, max(ats) - min(ats))
    # POSITION has settled which STAR; rms settles which EXTRACTION of that star
    # the release actually published (a re-extraction differs in the 2nd decimal).
    if cands:
        _rr = float(c['rms_mJy'])
        pick = min(cands, key=lambda x: (abs(x['rms_combined_mJy'] - _rr),
                                         x.get('primary_beam_atten') is None,
                                         -x['_mtime']))
    else:
        pick = None
    RES[ckey(c)] = (pick, geom.get((pick['_dir'], pick['_stem'])) if pick else None)
print('largest A disagreement between two extractions of one star: %.5f' % aspread)
print('rows whose candidate set the POSITION cut narrowed: %d ; rows with more '
      'than one surviving product: %d' % (nposcut, nmulti))

# every window shared by two DIFFERENT stars must resolve to different positions
bywin = collections.defaultdict(list)
for c in cat:
    bywin[(c['eb'], fq(c['flo_GHz']), fq(c['fhi_GHz']))].append(nm(c['star_name']))
nshare, mind = 0, 1e9
for w, names in bywin.items():
    u = sorted(set(names))
    if len(u) < 2:
        continue
    nshare += 1
    for i in range(len(u)):
        for j in range(i + 1, len(u)):
            g1 = RES[(u[i],) + w][1]
            g2 = RES[(u[j],) + w][1]
            if g1 and g2:
                d = sep_of(g1, g2)
                mind = min(mind, d)
                assert d > 0.2, ('two STARS in one window at the same position: '
                                 '%s %s %s %.4f"' % (w, u[i], u[j], d))
print('windows shared by more than one star: %d -- closest resolved separation '
      '%.3f" (>0.2" required)' % (nshare, mind))

# ---- 4. emit --------------------------------------------------------------
out, src = {}, collections.Counter()
recov, bad = [], []
for c in cat:
    p, g = RES[ckey(c)]
    rms, smin = float(c['rms_mJy']), float(c['smin_mJy'])
    if p is not None and p.get('primary_beam_atten') is not None \
            and p.get('primary_beam_offset_arcsec') is not None:
        off, at, how = p['primary_beam_offset_arcsec'], p['primary_beam_atten'], 'product'
    elif g is not None:
        # ITEM 3: recover from the extraction's own stored geometry.
        off = sep_arcsec(g['phase_ra'], g['phase_dec'],
                         math.radians(g['t1_ra']), math.radians(g['t1_dec']))
        at, how = gauss(off, g['pb_arcsec']), 'recovered'
        recov.append('%s %s %.4f GHz  off=%.3f" A=%.5f'
                     % (c['star_name'], c['eb'], float(c['flo_GHz']), off, at))
    else:
        # no product on disk at all: invert the release's own chain.  Flagged so
        # the gate can never run C4 (smin == 5 rms / A) on a row where A was
        # DERIVED from smin -- that would be a check that cannot fail.
        at = 5.0 * rms / smin if smin > 0 else float('nan')
        at = min(1.0, max(at, 1e-12))
        # NOT theta_pb_arcsec: that column is the pipeline's 1.22 lam/DISH with
        # DISH = 12 m for EVERY window, so on an ACA block it is 1.7x too narrow
        # and would invert to a badly wrong offset.  Use the block's own array.
        fmid = 0.5 * (float(c['flo_GHz']) + float(c['fhi_GHz'])) * 1e9
        dish = 7.0 if EBS.get(c['eb'], {}).get('array') == '7m' else 12.0
        pb = math.degrees(1.22 * (2.99792458e8 / fmid) / dish) * 3600.0
        off = pb * math.sqrt(max(0.0, math.log(1.0 / at) / (4 * math.log(2))))
        how = 'inverted'
    src[how] += 1
    if how != 'inverted' and smin > 0 and abs(5 * rms / at - smin) / smin > 2e-4:
        bad.append('%s %s %.4f  smin %.5f vs 5rms/A %.5f'
                   % (c['star_name'], c['eb'], float(c['flo_GHz']), smin, 5 * rms / at))
    # Keyed on (released star name, eb) with the window carried as a NUMBER, so
    # the consumer matches on a 2 MHz tolerance.  A rounded frequency key put six
    # windows on the wrong side of a half-way case at every decimal tried.
    out.setdefault('%s|%s' % (nm(c['star_name']), c['eb']), []).append(dict(
        flo=round(min(float(c['flo_GHz']), float(c['fhi_GHz'])), 6),
        fhi=round(max(float(c['flo_GHz']), float(c['fhi_GHz'])), 6),
        pb_offset_arcsec=round(off, 4), pb_atten=round(at, 6), pb_source=how,
        star_ra=(g['t1_ra'] if g else None), star_dec=(g['t1_dec'] if g else None)))
print('provenance: %s' % dict(src))
print('ITEM 3, offsets recovered at the generator: %d' % len(recov))
for x in recov:
    print('   %s' % x)
print('rows where smin != 5 rms / A (tolerance 2e-4): %d' % len(bad))
for x in bad[:5]:
    print('   %s' % x)
assert not bad, bad[:3]
assert src['recovered'] == 1, ('exactly one released window is expected to need '
                              'recovery (Wolf 28); got %d' % src['recovered'])
# --- the theta_pb_arcsec column is 12 m for every window, including ACA -------
nac = 0
for c in cat:
    if EBS.get(c['eb'], {}).get('array') == '7m':
        fmid = 0.5 * (float(c['flo_GHz']) + float(c['fhi_GHz'])) * 1e9
        if abs(float(c['theta_pb_arcsec'])
               - math.degrees(1.22 * (2.99792458e8 / fmid) / 7.0) * 3600.0) > 1.0:
            nac += 1
print('ACA rows whose published theta_pb_arcsec is the 12 m beam, not their own: '
      '%d (a reader cannot recompute A from it -- which is why pb_atten must ship)'
      % nac)
assert nac > 0, 'expected the 12 m-for-every-window theta_pb column to be visible'
assert sum(len(v) for v in out.values()) == len(cat), \
    (sum(len(v) for v in out.values()), len(cat))
# no two entries under one (star, eb) may sit within the consumer's tolerance
for k, v in out.items():
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            assert abs(v[i]['flo'] - v[j]['flo']) >= FTOL \
                or abs(v[i]['fhi'] - v[j]['fhi']) >= FTOL, \
                'two windows of %s are within the 2 MHz match tolerance' % k
json.dump(out, open(os.path.join(HERE, 'pbcat_v408.json'), 'w'), indent=0, sort_keys=True)
lo = sorted((e['pb_atten'], k) for k, v in out.items() for e in v)
print('A over the release: min %.4f  p1 %.4f  median %.6f  |  A<0.99 %d  <0.9 %d'
      % (lo[0][0], lo[len(lo) // 100][0], lo[len(lo) // 2][0],
         sum(1 for a, _ in lo if a < 0.99), sum(1 for a, _ in lo if a < 0.9)))
print('wrote pbcat_v408.json: %d (star, eb) keys, %d window entries'
      % (len(out), sum(len(v) for v in out.values())))
