#!/usr/bin/env python3
"""PRIMARY-BEAM GATE (D29 item 5) -- the audit's tripwire, adopted.

No released window may be published with an uncomputed, zero-by-assumption or
unverifiable star-to-phase-centre offset, and the published S_min must carry the
primary-beam response exactly once.

WHAT CHANGED FROM `pbcheck_v408.py`
-----------------------------------
* It reads the CATALOGUE'S OWN two new columns (`pb_offset_arcsec`, `pb_atten`),
  so from v4.08 the gate checks what ships rather than a snapshot of the
  products.  It therefore also runs unchanged for a referee.
* ★ It is keyed on the POSITION, not on `(eb, window)` and not on rms.  The
  audit's own author found that `(eb, window)` is not a key -- G 272-61A/B and
  LP 476-207's two Gaia components share a block and their rms agree to the five
  decimals the catalogue prints, which silently swapped their attenuations and
  manufactured a fake 0.11 per cent `smin` mismatch.  Here each row carries the
  star position its product stored (`pbcat_v408.json`, built by a
  position-resolved join), and the product is found by matching that position to
  0.05" inside the window.  No name comparison happens anywhere in this file.
* C7 is added: the failure mode that produced the fake mismatch is itself now a
  clause -- two stars in one window may not resolve to the same position, and two
  catalogue rows may not resolve to the same product.

HONESTY OF EACH CLAUSE (which rows it can and cannot fail on)
------------------------------------------------------------
* 10 windows have no product on disk at all; their A is back-solved from the
  release's own `5 rms / smin`, flagged `pb_source='inverted'`, and C2/C3/C4 are
  SKIPPED on them -- running C4 there would be a check that cannot fail.
* 1 window (Wolf 28) has its offset recovered from its product's geometry, so on
  that row C2 and C3 are tautological by construction.  Counted and printed
  separately rather than folded into the pass count.
* The remaining 1,640 rows carry an offset the search stored and an A the search
  applied, so C2, C3 and C4 are independent there.

Six clauses, each demonstrated firing (--drive 1..6), plus C7 (--drive 7), and
all passing at drive 0.
"""
import json, csv, math, os, sys, collections
from scipy.special import j1

HERE = os.path.dirname(os.path.abspath(__file__))
# v4.08: inside the deposit.  The catalogue is the one that ships, the frozen
# provenance record and the product geometry live in pbaudit_v408/, and nothing
# is read from outside this directory -- so a referee can run this file.
P = lambda n: os.path.join(HERE, n)
Q = lambda n: os.path.join(HERE, 'pbaudit_v408', n)
AS = math.pi / 180 / 3600
C = 299792458.0
# No published limit may move by more than this if the beam model is changed from
# the pipeline Gaussian to CASA's blocked Airy.  The audit's 1.08, from a measured
# maximum of 1.0745, is kept -- and the maximum is now PRINTED at every run rather
# than trusted.  ★ Getting it right depends on resolving the right EXTRACTION: an
# earlier version of this gate resolved the product by position alone, paired
# ALMA J1537's 7 m attenuation with its superseded 12 m geometry, and reported a
# spurious x1.083.  Position picks the star; rms picks the extraction.
MODEL_TOL = 1.08
A_TOL = 1e-5              # published A is printed to 6 dp and the offset to 4 dp;
                          # measured worst reconstruction residual is 3.7e-6
RMS_TOL = 0.02            # relative; separates extractions (~1%) while still
                          # flagging a published rms no product reproduces
POS_TOL = 0.05            # arcsec, product <-> declared position
SEP_MIN = 0.2             # arcsec, two stars in one window

# every released window whose response is below 0.9 must be declared HERE,
# by POSITION (ra, dec of the star as the search propagated it) and eb
PB_LOW_RESPONSE = {
    ('A002_Xd9398d_X37e8', 194.007, -12.957),    # LP 736-15,   8.13", 4 windows
    ('A002_Xd9398d_X322a', 194.007, -12.957),    # LP 736-15,   8.13", 4 windows
    ('A002_Xb825df_X2265', 160.625, -33.671),    # TWA 7,       5.87", 4 windows
    ('A002_Xb77b17_X3940', 160.625, -33.671),    # TWA 7,       5.87", 4 windows
    ('A002_Xd9d7c7_Xb3d2', 234.262, -33.325),    # ALMA J1537,  5.72", 4 windows
    ('A002_Xd9d7c7_Xbb64', 234.262, -33.325),    # ALMA J1537,  5.72", 4 windows
    ('A002_Xcd8029_Xb6b0', 234.739, -57.708),    # HD 139084,   5.21", 4 windows
    ('A002_Xd0fb35_X90dc', 101.286, -16.722),    # alf CMa B,   7.43", 4 windows
    ('A002_Xcc626d_X579', 101.286, -16.722),     # alf CMa B,   7.98", 2 windows
}


def hav(a0, d0, a1, d1):
    """exact angular separation, arcsec; radians in"""
    s = (math.sin((d1 - d0) / 2) ** 2
         + math.cos(d0) * math.cos(d1) * math.sin((a1 - a0) / 2) ** 2)
    return 2 * math.asin(min(1.0, math.sqrt(s))) / AS


def gauss(th, fwhm):
    return math.exp(-4 * math.log(2) * (th / fwhm) ** 2)


def airy_casa(th, lam, dish):
    de, b = (10.7, 0.75) if dish > 9.5 else (6.25, 0.75)
    eps = b / de
    x = math.pi * de * th * AS / lam
    if x < 1e-9:
        return 1.0
    v = (2 * j1(x) / x - eps * eps * 2 * j1(eps * x) / (eps * x)) / (1 - eps * eps)
    return v * v


MODELMAX = [0.0]
RECOV = [None]
NEAR = []          # rows whose published rms differs from the best product by
                   # more than 1e-4 but less than RMS_TOL -- reported, not fatal


def load(drive=0, cat_path=None):
    # drive 8 is not a perturbation but a REGRESSION: run the gate against the
    # catalogue as v4.07 shipped it, with no pb columns.  C1 must then fire on
    # every row -- that is the proof that item 2 is what makes drive 0 pass.
    cat = list(csv.DictReader(open(cat_path or P('per_target_results_v3.99.csv'))))
    if drive == 8:
        # ★ drive 8 is not a perturbation but a REGRESSION: the catalogue as
        # v4.07 shipped it, i.e. this one with the two new columns removed.
        # Deriving it rather than freezing a second 800 kB copy keeps the test
        # honest -- a stale fixture would stop tracking the catalogue -- and
        # the equivalence was verified once against v4.07 itself: of 60
        # columns, 0 cells differ (BUILD_NOTES_V408, section 1).  C1 must then
        # fire on EVERY row.
        cat = [{k: v for k, v in c.items()
                if k not in ('pb_offset_arcsec', 'pb_atten')} for c in cat]
    pbc = json.load(open(P('pbcat_v408.json')))
    prods = json.load(open(Q('inv_products.json')))['recs']
    geom = {(g['_dir'], g['_stem']): g for g in json.load(open(Q('pbgeom.json')))}
    FTOL = 0.002
    widx = collections.defaultdict(list)
    for p in prods:
        widx[p['eb']].append(p)
    rows = []
    del NEAR[:]
    for c in cat:
        lo = min(float(c['flo_GHz']), float(c['fhi_GHz']))
        hi = max(float(c['flo_GHz']), float(c['fhi_GHz']))
        # the frozen record: provenance and the position the search used
        ent = None
        for e in pbc.values():
            pass
        for k, v in pbc.items():
            if not k.endswith('|' + c['eb']):
                continue
            for e in v:
                if abs(e['flo'] - lo) < FTOL and abs(e['fhi'] - hi) < FTOL:
                    # on drive 8 the catalogue has no pb_atten to match against
                    if not c.get('pb_atten') \
                            or abs(e['pb_atten'] - float(c['pb_atten'])) < 2e-6:
                        ent = e
                        break
            if ent:
                break
        # The product, found BY POSITION inside this window and then by rms.
        # Position says WHICH STAR; rms says which EXTRACTION of that star the
        # release published.  rms is independent of A, so C2/C3/C4 stay honest;
        # choosing on A instead would make C3 a check that cannot fail.
        g = None
        if ent and ent['star_ra'] is not None:
            cands = []
            for p in widx.get(c['eb'], ()):
                if abs(min(p['freq_lo_GHz'], p['freq_hi_GHz']) - lo) >= FTOL \
                        or abs(max(p['freq_lo_GHz'], p['freq_hi_GHz']) - hi) >= FTOL:
                    continue
                gg = geom.get((p['_dir'], p['_stem']))
                if gg is None:
                    continue
                if hav(math.radians(gg['t1_ra']), math.radians(gg['t1_dec']),
                       math.radians(ent['star_ra']), math.radians(ent['star_dec'])) <= POS_TOL:
                    cands.append((p, gg))
            if cands:
                rr = float(c['rms_mJy'])
                p, g = min(cands, key=lambda x: abs(x[0]['rms_combined_mJy'] - rr))
                if abs(p['rms_combined_mJy'] - rr) > RMS_TOL * rr:
                    g = ('norms', p['rms_combined_mJy'], rr)
                elif abs(p['rms_combined_mJy'] - rr) > 1e-4 * rr:
                    NEAR.append((abs(p['rms_combined_mJy'] - rr) / rr,
                                 c['star_name'], c['eb']))
        rows.append([c, ent, g])
    # ---------------------------------------------------------------- drives --
    if drive == 1:
        rows[7][0]['pb_offset_arcsec'] = ''
        rows[7][0]['pb_atten'] = ''
    if drive == 2:
        g = dict(rows[7][2])
        g['phase_ra'] = g['phase_ra'] + 6.3 * AS / math.cos(g['phase_dec'])
        rows[7][2] = g
    if drive == 3:
        for c, e, g in rows:
            if e and e['pb_source'] != 'inverted' and float(c['pb_atten']) < 0.9:
                c['pb_atten'] = '1.000000'
                break
    if drive == 4:
        for c, e, g in rows:
            if e and e['pb_source'] != 'inverted' and float(c['pb_atten']) < 0.9:
                c['smin_mJy'] = '%.5f' % (5 * float(c['rms_mJy']))
                break
    if drive == 6:
        for r in rows:
            if isinstance(r[2], dict):
                r[2] = dict(r[2], pb_arcsec=r[2]['pb_arcsec'] * 1.13 / 1.22)
                break
    if drive == 7:
        # give two DIFFERENT stars in one window the same declared position
        byw = collections.defaultdict(list)
        for r in rows:
            byw[(r[0]['eb'], round(float(r[0]['flo_GHz']), 3))].append(r)
        for w, v in byw.items():
            pos = {(round(x[1]['star_ra'], 6), round(x[1]['star_dec'], 6))
                   for x in v if x[1] and x[1]['star_ra'] is not None}
            if len(pos) > 1:
                ref = v[0][1]
                for x in v[1:]:
                    if x[1] and x[1]['star_ra'] is not None \
                            and (x[1]['star_ra'], x[1]['star_dec']) != (ref['star_ra'],
                                                                       ref['star_dec']):
                        x[1] = dict(x[1], star_ra=ref['star_ra'], star_dec=ref['star_dec'])
                        break
                break
    return rows


def run(drive=0, cat_path=None, quiet=False):
    rows = load(drive, cat_path)
    declared = set(PB_LOW_RESPONSE)
    if drive == 5:
        declared.discard(('A002_Xd9398d_X37e8', 194.007, -12.957))
    fail = collections.defaultdict(list)
    MODELMAX[0] = 0.0
    seen_low, skip, taut = set(), 0, 0
    posmap = collections.defaultdict(set)
    prodmap = collections.defaultdict(list)
    for c, e, g in rows:
        tag = '%s|%s|%.4f' % (c['star_name'], c['eb'], float(c['flo_GHz']))
        # ---- C1: an offset and a response must be PUBLISHED --------------
        if not c.get('pb_offset_arcsec') or not c.get('pb_atten'):
            if drive == 8:
                fail['C1 published window with no offset or no response'].append(tag)
                continue
            fail['C1 published window with no offset or no response'].append(tag)
            continue
        off, at = float(c['pb_offset_arcsec']), float(c['pb_atten'])
        if e is None:
            fail['C1b no provenance record for a published response'].append(tag)
            continue
        if e['pb_source'] == 'inverted':
            skip += 1
            continue                      # A derived from smin: C2-C4 vacuous
        if e['pb_source'] == 'recovered':
            taut += 1
            RECOV[0] = '%s  off=%.3f" A=%.5f' % (tag, off, at)
        if g is None:
            fail['C1c product has a response but no independent geometry'].append(tag)
            continue
        if isinstance(g, tuple):
            fail['C1d no product at that position reproduces the published rms'].append(
                '%s product %.5f vs published %.5f' % (tag, g[1], g[2]))
            continue
        # ---- C2: reproduce the offset from the product's OWN geometry -----
        ind = hav(g['phase_ra'], g['phase_dec'],
                  math.radians(g['t1_ra']), math.radians(g['t1_dec']))
        if abs(ind - off) > max(0.01, 1e-3 * off):
            fail['C2 published offset != independent recomputation'].append(
                '%s published %.3f" vs %.3f"' % (tag, off, ind))
        # ---- C3: the response must BE the model at that offset ------------
        fw = g['pb_arcsec']
        if abs(at - gauss(off, fw)) > A_TOL:
            fail['C3 response is not the model evaluated at the published offset'].append(
                '%s A=%.6f vs %.6f' % (tag, at, gauss(off, fw)))
        lam = C / g['freqmed']
        D = 1.22 * lam / (fw * AS)
        if min(abs(D - 12.0), abs(D - 7.0)) > 0.12:
            fail['C3b pb FWHM is not 1.22 lam/D for a 12 m or 7 m dish'].append(
                '%s D=%.2f m' % (tag, D))
        # ---- C4: S_min must carry the response exactly ONCE ---------------
        pred = 5 * float(c['rms_mJy']) / at
        if abs(pred - float(c['smin_mJy'])) / float(c['smin_mJy']) > 2e-4:
            fail['C4 smin != 5 rms / A (response missing or applied twice)'].append(
                '%s smin=%s pred=%.5f' % (tag, c['smin_mJy'], pred))
        # ---- C5: every low-response window must be declared, BY POSITION --
        if at < 0.9:
            key = (c['eb'], round(g['t1_ra'], 3), round(g['t1_dec'], 3))
            seen_low.add(key)
            if key not in declared:
                fail['C5 undeclared low-response window'].append('%s A=%.3f' % (tag, at))
        # ---- C6: beam-model sensitivity ----------------------------------
        r = at / airy_casa(off, lam, 12.0 if D > 9.5 else 7.0)
        MODELMAX[0] = max(MODELMAX[0], r, 1 / r)
        if r > MODEL_TOL or r < 1 / MODEL_TOL:
            fail['C6 beam-model sensitivity exceeds tolerance'].append('%s x%.3f' % (tag, r))
        # ---- C7: the position must be a key ------------------------------
        w = (c['eb'], round(float(c['flo_GHz']), 3))
        posmap[w].add((round(e['star_ra'], 6), round(e['star_dec'], 6), c['star_name']))
        prodmap[(g['_dir'], g['_stem'])].append(tag)
    for w, s in posmap.items():
        pts = sorted(s)
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                d = hav(math.radians(pts[i][0]), math.radians(pts[i][1]),
                        math.radians(pts[j][0]), math.radians(pts[j][1]))
                if d <= SEP_MIN:
                    fail['C7 two stars in one window at the same position'].append(
                        '%s %s / %s %.4f"' % (w[0], pts[i][2], pts[j][2], d))
    for k, v in prodmap.items():
        if len(set(v)) > 1:
            fail['C7b one product claimed by two catalogue rows'].append(
                '%s <- %s' % (k[1], ', '.join(sorted(set(v))[:2])))
    for d in declared - seen_low:
        fail['C5b declared low-response window not present at A<0.9'].append(str(d))
    if not quiet:
        print('drive=%d  windows %d (%d skipped: A inverted from smin; '
              '%d tautological: offset recovered)  ->  %s'
              % (drive, len(rows), skip, taut, 'PASS' if not fail else 'FAIL'))
        if NEAR:
            w = max(NEAR)
            print('   note: %d rows whose published rms no product reproduces to '
                  '1e-4 (worst %.2f%%, %s %s)'
                  % (len(NEAR), 100 * w[0], w[1], w[2]))
        print('   measured worst beam-model sensitivity A_pipe/A_casa: x%.4f '
              '(tolerance %.2f)' % (MODELMAX[0], MODEL_TOL))
        if drive == 0:
            print('   the ONE row whose offset had to be recovered: %s'
                  % (RECOV[0] or 'none'))
        for k, v in sorted(fail.items()):
            print('   %-62s %4d  e.g. %s' % (k, len(v), v[0][:72]))
    return fail


if __name__ == '__main__':
    drives = [int(x) for x in sys.argv[1:]] or [0, 1, 2, 3, 4, 5, 6, 7, 8]
    bad = 0
    for d in drives:
        f = run(d)
        if d == 0 and f:
            bad = 1
        if d != 0 and not f:
            bad = 1
            print('   *** DRIVE %d DID NOT FIRE ***' % d)
    print('\ngate %s' % ('FAILED' if bad else 'OK'))
    sys.exit(bad)
