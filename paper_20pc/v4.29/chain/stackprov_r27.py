#!/usr/bin/env python3
r"""stackprov_r27.py -- THE STACK'S INVENTORY SELECTS EACH WINDOW'S PRODUCT BY PROVENANCE.
Round 27 (EXTENSION_DECISION.md, Ruling 25's condition result): the 17th wrong-object / name-key join.

WHAT WAS WRONG.  The stellar-frame stack's inventory (`stack_v408/inventory.json`, 3,134 retained
products) holds more than one product for some windows: a pre-repair extraction (the 12 m control
annulus written into a 7 m block) and its repaired re-extraction, in two directories under two star
names; backup copies; and re-extractions of 12 m blocks.  Two name-keyed rules chose between them:
  * `groups.py` `dedupe()` kept, per (star-NAME key, block, spw), the copy under `/targets/` with the
    SHORTEST PATH -- so `HD14055_B7/` beat `HD14055_B7_EB_X2085/`, the pre-repair product beat its
    repaired twin, purely on the length of a directory name;
  * twins under DIFFERENT star names (`GaiaDR3_5853...` vs `Proxima_Cen_B6_EB_...`) both survived the
    dedupe, and `groups3.py` then took, per block, the window with most integrations -- a tie between
    twins, broken by list order, i.e. by sorted path, i.e. by name.  Worse, a twin left behind in the
    pool could seed a SECOND group, so one observation entered two stacks.
The census-only Proxima stack read 7 pre-repair products of 25 this way (r27-extension, 19:51 UTC).

WHAT THIS DOES.  A window is identified by its CONTENT COORDINATES -- execution block, channel-grid edges
(to 1 kHz) and the star's sky position (to `TOL_ARCSEC`, the tolerance of `posjoin_r27`) -- never by a
directory or a star name.  Among the products holding one window the winner is decided by PROVENANCE, in
this order, and the rule that decided it is recorded:
  R1 RING GEOMETRY   the product's primary beam (pb_arcsec) is 1.22 lambda/D of its block's OWN array dish
                     (archive record), and any dish it records (dish_m) is that dish.  A product whose
                     control annulus was drawn for another dish is pre-repair and is rejected.
  R2 EXTRACTOR       among those, a product written by the repaired extractor (it records its geometry:
                     dish_m, ann_syn_factor) is preferred to one that does not.
  R3 RECORD          among those, the product whose own result reproduces the PUBLISHED row of its window
                     (census: `acafull_v399.json` for the repaired compact-array fold, else the catalogue;
                     hold-out, extension, beyond-40 pc control: the pre-repair exports the stack was built
                     against) -- rms to 1e-6 relative and peak statistic to 1e-4.
  R4 CONTENT         if more than one is still left and every array the stack reads (I_star,
                     I_control_sample, W, freqs, times) and the primary beam are byte-identical, the copies
                     are one measurement and the choice cannot reach any number; the winner is the copy in
                     the search's own product tree (`recur_r7/` holds copies made from it by the recurrence
                     tooling), then the smallest file hash -- neither a name nor a time.
  R5 DECLARATION     otherwise the window MUST be declared in `r27inputs/stackfix/stackdecl_r27.json`
                     (identity -> winner, with a reason).  An undeclared tie raises `TieError` and stops
                     the build.  So does a declaration naming a product that is not a candidate, and a
                     declaration that is not used (a stale declaration is a silent future winner).
A CENSUS window whose block has a known array and no ring-correct product raises `PreRepairError`.  A
hold-out / extension / control window with only pre-repair products in the inventory is KEPT and labelled
`prerepair_only`: Ruling 25 leaves the archive-wide stack on those products for this version.

GATE MODE (`--check`, run by make_all): re-derives the selection from the frozen harvest and asserts that
the stack's frozen `windows.json` and `groups3.json` read exactly the winners (P1-P8).  `--drive N`
perturbs a COPY in memory and must fail; `--selftest` runs drives 0-7 and exits 0 only if drive 0 passes
and every other drive fails.  Neither mode writes anything.
  drive 1  a second directory holding one window (same block, edges, position, geometry), different content,
           no declaration                                     -> P1 (TieError)
  drive 2  a declaration that decides nothing                  -> P1 (DeclError)
  drive 3  a census compact-array window's repaired product removed -> P1 (PreRepairError)
  drive 4  the old name-keyed choice: a pre-repair twin back in the windows -> P2
  drive 5  one observation entered in two groups               -> P4
  drive 6  a census winner that is not the product its published row identifies -> P6
  drive 7  a group list not rebuilt after the selection         -> P10
  drive 8  one window framed by its directory-name key again    -> P9, P12

ROW 61 (v4.29): THE FRAME BY IDENTITY, NOT BY NAME (the 18th wrong-object / name-key join).  `groups.py` looked
each window's systemic velocity up by its search-time star-NAME key, so a star searched under a `GaiaDR3_...`
directory lost its v_sys there while its named windows kept it (bet Pic `X75bfbf_Xace`: 16.8 km/s, ~26 fine
channels).  The velocity is now attached by IDENTITY, decided on numbers as `vsysgate_r27.py` decides it: a
window takes the velocity of the stack's velocity table (`starrv_v399.json`, unchanged) whose star's Gaia DR3
astrometry (`r27inputs/vsys_r27.json`), propagated by its own proper motion to the block's epoch, lies within
`R_SELF` of the window's position AND whose parallax agrees with the window's to `PLX_TOL` (starkey's
tolerance, which separates two components of one system by a factor of five).  Two matches stop the build.
The arithmetic is groups.py's own (dv = v_sys - v_corr, or -v_corr without one; sf = f / (1 - dv/c)), and P11
proves it by reproducing every deposited frame from the NAME lookup exactly; P12 then requires every frozen
window to carry the identity frame, and no window to lose a velocity the name lookup gave it.

Inputs (tree): r27inputs/stackfix/namekey/windows.json (the deposited, name-keyed windows: the frames),
r27inputs/stackfix/prov_harvest_r27.json.gz (cluster harvest of every inventory product,
`harvest.py`), r27inputs/stackfix/ext_arrays_r27.json, r27inputs/stackfix/stackdecl_r27.json,
archive_meta_v381.json, r27inputs/holdout/holdfix_r27.json, acafull_v399.json,
per_target_results_v3.99.csv, holdout_export_v381_prerepair.json, export_extension_prerepair.json,
outofsample_v381.json, stack_v408/{windows,groups3,badweight}.json; row 61: starrv_v399.json,
r27inputs/vsys_r27.json.
"""
import csv
import gzip
import json
import math
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
TOL_ARCSEC = 0.1          # posjoin_r27.TOL_ARCSEC: the position tolerance every join in the tree uses
PB_REL = 0.01             # 1.22 lambda / D to 1 per cent (the two dishes differ by 71 per cent)
PB_FACTOR = 1.22
DISH = {'7m': 7.0, '12m': 12.0}
C = 299792458.0
RAD2AS = 206264.80624709636
ARRAYS = ('I_star', 'I_control_sample', 'W', 'freqs', 'times')
C_KMS = 299792.458        # frame.py's constant, as groups.py used it
R_SELF = 2.0              # arcsec, vsysgate_r27.R_SELF: same object after the target's own proper motion
PLX_TOL = 1e-3            # starkey.PLX_TOL: same star (<= 3e-4) vs two components of one system (>= 1.5e-3)
SEARCH_TREE = '/data/SETI/targets/'      # the search's product tree; everything else in the inventory is a copy


def ROOT_RANK(path):
    return 0 if path.startswith(SEARCH_TREE) else 1


class TieError(Exception):
    pass


class PreRepairError(Exception):
    pass


class DeclError(Exception):
    pass


def jload(path):
    if path.endswith('.gz'):
        with gzip.open(path, 'rt') as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def blockid(path):
    m = re.search(r'(A002_X[0-9a-zA-Z]+_X[0-9a-zA-Z]+)', path)
    return m.group(1) if m else None


def sep_arcsec(a, b):
    ra1, de1, ra2, de2 = (math.radians(x) for x in (a[0], a[1], b[0], b[1]))
    s = math.sin((de2 - de1) / 2) ** 2 + math.cos(de1) * math.cos(de2) * math.sin((ra2 - ra1) / 2) ** 2
    return 2 * math.asin(min(1.0, math.sqrt(s))) * RAD2AS


# ------------------------------------------------------------------ the records the rules read
def array_record(tree):
    """block -> (dish name, route).  Archive first; then the extension's obscore harvest; then the
    hold-out / control re-extraction's own list of compact-array blocks."""
    out = {}
    for eb, v in jload(os.path.join(tree, 'archive_meta_v381.json'))['ebs'].items():
        if v.get('array') in DISH:
            out[eb] = (v['array'], 'archive_meta_v381')
    for eb, v in jload(os.path.join(tree, 'r27inputs', 'stackfix', 'ext_arrays_r27.json')).items():
        a = v['array']
        a = '12m' if a not in DISH and '12' in a else a      # "{'12','PM'}": 12 m + total power
        out.setdefault(eb, (a, 'ext_arrays_r27 (obscore)'))
    hf = jload(os.path.join(tree, 'r27inputs', 'holdout', 'holdfix_r27.json'))
    aca = set()
    for k, v in hf['aca_blocks'].items():
        aca |= set(v)
    for eb in aca:
        out.setdefault(eb, ('7m', 'holdfix_r27 aca_blocks'))
    for f in ('holdout_export_v381_prerepair.json', 'outofsample_v381.json'):
        for r in jload(os.path.join(tree, f))['rows']:
            if r['eb'] not in aca:
                out.setdefault(r['eb'], ('12m', 'holdfix_r27 complement (every compact-array block re-extracted)'))
    return out


def published(tree):
    """eb -> list of published rows (flo, fhi, rms, snr, set) of the windows the stack was built against."""
    pub = collections.defaultdict(list)
    for a in jload(os.path.join(tree, 'acafull_v399.json')):
        pub[a['eb']].append(dict(lo=min(a['flo'], a['fhi']), hi=max(a['flo'], a['fhi']), rms=a['rms'],
                                 snr=a['star_snr'], set='census', src='acafull_v399'))
    aca_eb = set(pub)
    census = set(aca_eb)
    with open(os.path.join(tree, 'per_target_results_v3.99.csv')) as fh:
        for r in csv.DictReader(fh):
            census.add(r['eb'])
            if r['eb'] in aca_eb:
                continue
            lo, hi = float(r['flo_GHz']), float(r['fhi_GHz'])
            # the catalogue prints rms to 1e-5 mJy and the peak statistic to 1e-4: compare at that precision
            pub[r['eb']].append(dict(lo=min(lo, hi), hi=max(lo, hi), rms=float(r['rms_mJy']),
                                     snr=float(r['star_snr']), set='census', src='per_target_results_v3.99',
                                     rms_abs=0.51e-5, snr_abs=0.51e-4))
    for f, s in (('holdout_export_v381_prerepair.json', 'holdout'), ('export_extension_prerepair.json', 'extension'),
                 ('outofsample_v381.json', 'oos')):
        for r in jload(os.path.join(tree, f))['rows']:
            pub[r['eb']].append(dict(lo=min(r['flo'], r['fhi']), hi=max(r['flo'], r['fhi']), rms=r['rms'],
                                     snr=r['star_snr'], set=s, src=f))
    return pub, census


def matches_record(c, rows):
    r = c.get('res') or {}
    if r.get('rms') is None or r.get('flo') is None:
        return False
    lo, hi = min(r['flo'], r['fhi']), max(r['flo'], r['fhi'])
    for p in rows:
        if abs(p['lo'] - lo) < 1e-3 and abs(p['hi'] - hi) < 1e-3 \
                and abs(p['rms'] - r['rms']) <= p.get('rms_abs', 1e-6 * abs(p['rms'])) \
                and abs(p['snr'] - r['snr']) <= p.get('snr_abs', 1e-4):
            return True
    return False


# ------------------------------------------------------------------ identities
def identities(rows):
    """[(key, [candidates])]: key = (block, f_lo kHz, f_hi kHz, ra, dec of the cluster's first member)."""
    byw = collections.defaultdict(list)
    for c in rows:
        byw[(blockid(c['path']), int(round(c['f_lo'] / 1e3)), int(round(c['f_hi'] / 1e3)))].append(c)
    out = []
    for k in sorted(byw):
        clusters = []
        for c in sorted(byw[k], key=lambda x: x['sha_file']):          # order-free: content hash
            pos = (c['t1_ra'], c['t1_dec'])
            hit = [cl for cl in clusters if sep_arcsec(cl[0], pos) <= TOL_ARCSEC]
            if len(hit) > 1:
                raise TieError('window %s: a product within %.2f" of two position clusters' % (k, TOL_ARCSEC))
            if hit:
                hit[0][1].append(c)
            else:
                clusters.append((pos, [c]))
        for pos, cs in clusters:
            for a in cs:
                for b in cs:
                    assert sep_arcsec((a['t1_ra'], a['t1_dec']), (b['t1_ra'], b['t1_dec'])) <= TOL_ARCSEC
            out.append((k + (round(pos[0], 6), round(pos[1], 6)), cs))
    return out


def ident_str(key):
    return '%s|%d|%d|%.6f|%.6f' % key


# ------------------------------------------------------------------ the selection
def select(harvest, arrays, pub, census, decl):
    """Returns (decisions, used_declarations).  Raises TieError / PreRepairError / DeclError."""
    rows = [r for r in harvest['rows'] if 'err' not in r]
    if len(rows) != len(harvest['rows']):
        raise TieError('%d inventory products could not be read' % (len(harvest['rows']) - len(rows)))
    dec_by = {d['identity']: d for d in decl['declarations']}
    used = set()
    out = []
    errs = []                     # every problem is collected, then the first kind raised with all of them
    for key, cs in identities(rows):
        eb = key[0]
        arr, aroute = arrays.get(eb, (None, 'unrecorded'))
        dish = DISH.get(arr)
        d = dict(identity=ident_str(key), block=eb, array=arr, array_route=aroute,
                 set='census' if eb in census else (pub[eb][0]['set'] if pub.get(eb) else 'unrecorded'),
                 n_cand=len(cs), cands=[c['path'] for c in cs])
        if dish:
            exp = PB_FACTOR * C / cs[0]['fmed'] / dish * RAD2AS
            ring = [c for c in cs if abs(c['pb_arcsec'] - exp) <= PB_REL * exp
                    and ('dish_m' not in c or abs(c['dish_m'] - dish) < 1e-6)]
            d['pb_expected'] = exp
        else:
            ring = [c for c in cs if 'dish_m' in c]
        kept, rule = (ring, 'R1') if ring else (list(cs), None)
        if not ring:
            dd = dec_by.get(d['identity'])
            if dish and d['set'] == 'census' and not (dd and dd.get('kind') == 'prerepair'):
                errs.append((PreRepairError, 'census window %s (%s block) has no product on its own dish\'s '
                                                 'ring: %s' % (d['identity'], arr, d['cands'])))
            if dd and dd.get('kind') == 'prerepair':
                used.add(d['identity'])
                if not (dish and d['set'] == 'census' and len(cs) == 1 and dd['winner'] == cs[0]['path']):
                    errs.append((DeclError, 'pre-repair declaration for %s does not describe a census window with '
                                            'one off-ring product %s' % (d['identity'], d['cands'])))
                d['status'] = 'prerepair_declared'
            else:
                d['status'] = 'prerepair_only' if dish else 'array_unrecorded'
        else:
            d['status'] = 'ring_ok'
        if len(kept) > 1:
            ext = [c for c in kept if 'dish_m' in c]
            if ext and len(ext) < len(kept):
                kept, rule = ext, 'R2'
        if len(kept) > 1:
            rec = [c for c in kept if matches_record(c, pub.get(eb, []))]
            if rec and len(rec) < len(kept):
                kept, rule = rec, 'R3'
        if len(kept) > 1:
            sig = {(tuple(c['sha'].get(a) for a in ARRAYS), round(c['pb_arcsec'], 9)) for c in kept}
            if len(sig) == 1:
                # one measurement: the search's own product tree holds the original, `recur_r7` holds copies
                # of it made by the recurrence tooling; then the smallest file hash (neither a name nor a time)
                kept, rule = [min(kept, key=lambda c: (ROOT_RANK(c['path']), c['sha_file']))], 'R4'
        if len(kept) > 1:
            dd = dec_by.get(d['identity'])
            if dd is not None and dd.get('kind') != 'winner':
                dd = None
            if dd is None:
                errs.append((TieError, 'window %s: %d products and no provenance rule separates them, and no '
                                       'declared winner: %s' % (d['identity'], len(kept),
                                                                sorted(c['path'] for c in kept))))
                kept, rule = kept[:1], 'UNRESOLVED'
            else:
                win = [c for c in kept if c['path'] == dd['winner']]
                if len(win) != 1:
                    errs.append((DeclError, 'declaration for %s names %s, which is not one of the tied '
                                            'candidates %s' % (d['identity'], dd['winner'],
                                                               sorted(c['path'] for c in kept))))
                    win = kept[:1]
                kept, rule = win, 'R5'
                used.add(d['identity'])
        if len(cs) == 1:
            rule = 'single'
        elif rule is None:
            rule = 'R1'
        d['winner'] = kept[0]['path']
        d['rule'] = rule
        d['winner_matches_record'] = matches_record(kept[0], pub.get(eb, []))
        out.append(d)
    stale = set(dec_by) - used
    if stale:
        errs.append((DeclError, '%d declaration(s) decide nothing (stale): %s' % (len(stale), sorted(stale))))
    if errs:
        for _, m in errs:
            print('  stackprov_r27: ' + m, file=sys.stderr)
        raise errs[0][0]('%d problem(s); first: %s' % (len(errs), errs[0][1]))
    return out, used


def load_all(tree):
    H = jload(os.path.join(tree, 'r27inputs', 'stackfix', 'prov_harvest_r27.json.gz'))
    A = array_record(tree)
    P, CEN = published(tree)
    D = jload(os.path.join(tree, 'r27inputs', 'stackfix', 'stackdecl_r27.json'))
    return H, A, P, CEN, D


# ------------------------------------------------------------------ windows from the winners
INV_FIELDS = ('path', 'star', 'ra', 'dec', 'plx', 'chanw', 'nchan', 'nint', 'f_lo', 'f_hi', 't_min', 't_max', 'dt_med')


def name_key(star):
    """groups.py's `key()` verbatim: the search-time star-name key under which the deposited stack computed a
    window's frame (its systemic velocity is looked up by this key).  Used ONLY to reproduce, for the winning
    product, the frame groups.py itself would have computed for it -- never to choose a product."""
    s = re.sub(r'\s*\[B\d+\]\s*$', '', star or '').strip()
    s = re.sub(r'^\*\s*', '', s)
    s = re.sub(r'\s*\(Gaia DR3 \d+\)\s*$', '', s)
    s = re.sub(r'\s*Gaia DR3 \d+\s*$', '', s)
    return re.sub(r'[^a-z0-9+-]', '', s.strip().lower())


FRAME = ('skey', 'star_n', 'band', 'block', 'mjd', 'v_corr', 'v_sys', 'dv', 'sf_lo', 'sf_hi', 'has_vsys')


def rebuild_windows(decisions, windows_old, inventory):
    """The stack's windows from the winners, as groups.py would have written them had its dedupe chosen the
    winner: the inventory fields are the winner's own, and the FRAME fields are the ones groups.py computed for
    the winner's own star-name key in that block (the old row of the same identity under that key; the two
    agree by construction because groups.py computes the frame per (name key, block)).  So this is the
    deposited computation with a different selection, and nothing else.  Returns (windows, report)."""
    inv = {r['path']: r for r in inventory}
    wold = {w['path']: w for w in windows_old}
    out, rep = [], collections.Counter()
    for d in decisions:
        have = [wold[p] for p in d['cands'] if p in wold]
        if not have:
            raise TieError('window %s: no row of the deposited windows for any of its products' % d['identity'])
        k = name_key(inv[d['winner']]['star'])
        frame = [w for w in have if w['skey'] == k and w['block'] == d['block']] \
            or [w for w in have if w['skey'] == k]
        if any(w['block'] != d['block'] for w in have):
            # groups.py's blockid() falls back to the FILE NAME for a product written without an spw in its name,
            # so the same observation entered the stack as two "blocks" (sqrt-N gain from one block counted twice)
            rep['old rows whose block field was a file name, not the execution block'] += \
                sum(1 for w in have if w['block'] != d['block'])
        if not frame:
            raise TieError('window %s: the winner\'s name key %r has no frame in the deposited windows' %
                           (d['identity'], k))
        if len({json.dumps([w[f] for f in FRAME]) for w in frame}) != 1:
            raise TieError('window %s: two frames under one name key' % d['identity'])
        if len({json.dumps([w[f] for f in FRAME if f not in ('skey', 'star_n')]) for w in have}) > 1:
            rep['identities whose rows under different name keys carry different frames'] += 1
        base = dict(frame[0])
        base['block'] = d['block']
        for f in INV_FIELDS:
            base[f] = inv[d['winner']][f]
        m = re.search(r'_spw(\d+)_srcspec', d['winner'])
        base['spw'] = int(m.group(1)) if m else -1
        if base['spw'] == -1 and frame[0]['path'] == d['winner']:
            base['spw'] = frame[0]['spw']
        rep['kept' if any(w['path'] == d['winner'] for w in have) else 'swapped to the provenance winner'] += 1
        rep['old rows collapsed'] += len(have) - 1
        out.append(base)
    order = {w['path']: i for i, w in enumerate(windows_old)}
    first = {d['winner']: min(order[p] for p in d['cands'] if p in order) for d in decisions}
    out.sort(key=lambda w: first[w['path']])
    return out, rep


# ------------------------------------------------------------------ row 61: the frame by identity
def velocity_refs(tree):
    """The stack's velocity table with each star's Gaia DR3 astrometry (row 52's verified record)."""
    rv = jload(os.path.join(tree, 'starrv_v399.json'))
    ast = jload(os.path.join(tree, 'r27inputs', 'vsys_r27.json'))['astrometry']
    refs = []
    for n, v in sorted(rv.items()):
        if n not in ast:
            raise TieError('velocity table star %r has no astrometric record' % n)
        t = ast[n]['target']
        refs.append(dict(name=n, key=name_key(n), v=float(v), ra=t['ra_2016'], dec=t['dec_2016'],
                         pmra=t['pmra'], pmdec=t['pmdec'], plx=t['parallax']))
    return refs


def _sep(a1, d1, a2, d2):
    a1, d1, a2, d2 = map(math.radians, (a1, d1, a2, d2))
    c = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(a1 - a2)
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * 3600.0


def identity_match(w, refs):
    """The velocity-table stars this window IS, on numbers: position at the block's epoch and parallax."""
    dt = (w['mjd'] - 57388.5) / 365.25          # years from J2016.0 (Gaia DR3 epoch, MJD 57388.5)
    out = []
    for r in refs:
        ra = r['ra'] + r['pmra'] / 3.6e6 * dt / math.cos(math.radians(r['dec']))
        de = r['dec'] + r['pmdec'] / 3.6e6 * dt
        if (_sep(w['ra'], w['dec'], ra, de) <= R_SELF
                and abs(w['plx'] - r['plx']) <= PLX_TOL * r['plx']):
            out.append(r)
    return out


def reframe(W, refs, by='identity'):
    """groups.py's frame arithmetic with the velocity attached by identity (or, to prove the arithmetic, by
    the old name key).  Returns (windows, report)."""
    byname = {r['key']: r['v'] for r in refs}
    out, rep = [], collections.Counter()
    for w in W:
        if by == 'name':
            v = byname.get(w['skey'])
        else:
            m = identity_match(w, refs)
            if len(m) > 1:
                raise TieError('window %s matches two velocity-table stars: %s' % (w['path'], [r['name'] for r in m]))
            v = m[0]['v'] if m else None
            vn = byname.get(w['skey'])
            if vn is not None and v != vn:
                raise TieError('window %s: identity gives %r, its name key %r' % (w['path'], v, vn))
            rep['framed by identity, name key had none' if (v is not None and vn is None)
                else ('with v_sys' if v is not None else 'without v_sys')] += 1
        dv = (v - w['v_corr']) if v is not None else (0.0 - w['v_corr'])
        f = 1.0 / (1.0 - dv / C_KMS)
        out.append(dict(w, v_sys=v, dv=dv, sf_lo=w['f_lo'] * f, sf_hi=w['f_hi'] * f, has_vsys=v is not None))
    return out, rep


def reframed_paths(W, refs):
    """The windows that carry a velocity only because it is now attached by identity (their directory-name key has
    none in the table) -- frozen as stack_v408/frame_r61.json so stack_v408.py, which reads only its own directory,
    can tell a frame change from a merge effect when it compares stacks across the change."""
    byname = {r['key'] for r in refs}
    return sorted(w['path'] for w in W if w['has_vsys'] and w['skey'] not in byname)


FRAME61_DOC = ('row 61 (v4.29): the stack windows whose systemic velocity is attached by stellar identity and which '
               'had none under their directory-name key; written by stackprov_r27.py, checked by its P13')


# ------------------------------------------------------------------ gate
def check(tree, drive=0):
    M = []

    def ck(name, cond, detail=''):
        M.append((name, bool(cond)))
        print('  %-78s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))

    H, A, P, CEN, D = load_all(tree)
    W = jload(os.path.join(tree, 'stack_v408', 'windows.json'))
    G = jload(os.path.join(tree, 'stack_v408', 'groups3.json'))
    BW = jload(os.path.join(tree, 'stack_v408', 'badweight.json'))
    if drive == 1:     # a second directory holding one window, same geometry, different content, undeclared
        c = json.loads(json.dumps(next(r for r in H['rows'] if 'dish_m' not in r and r.get('res')
                                       and blockid(r['path']) in A and A[blockid(r['path'])][0] == '12m')))
        c['path'] = c['path'].replace('/targets/', '/targets/DRIVE1_COPY_')
        c['sha_file'] = '0' * 64
        c['sha']['I_star'] = 'f' * 64
        H['rows'].append(c)
    if drive == 2:     # a stale declaration
        D = dict(D, declarations=D['declarations'] + [dict(identity='A002_Xdrive_X2|1|2|0.000000|0.000000',
                                                            winner='/nowhere', reason='drive 2')])
    if drive == 3:     # a census compact-array window whose ring-correct product is removed
        pairs = [cs for _, cs in identities(H['rows']) if blockid(cs[0]['path']) in CEN
                 and A.get(blockid(cs[0]['path']), (None,))[0] == '7m' and len(cs) == 2
                 and sum('dish_m' in c for c in cs) == 1]
        gone = next(c['path'] for c in pairs[0] if 'dish_m' in c)
        H = dict(H, rows=[r for r in H['rows'] if r['path'] != gone])
    try:
        dec, used = select(H, A, P, CEN, D)
        err = None
    except (TieError, PreRepairError, DeclError) as e:
        dec, used, err = None, set(), '%s: %s' % (type(e).__name__, str(e)[:300])
    ck('P1 every window of the inventory has exactly one product chosen by a provenance rule or a declared '
       'winner (an undeclared tie, a stale declaration or a census window off its own ring stops the build)',
       err is None, err or '%d windows' % len(dec))
    if err:
        return M
    win = {d['winner'] for d in dec}
    wp = [w['path'] for w in W]
    if drive == 4:     # the old name-keyed choice: a pre-repair twin back in the windows
        bad = next(d for d in dec if d['rule'] in ('R1', 'R2') and d['n_cand'] > 1)
        wp = [next(p for p in bad['cands'] if p != bad['winner']) if p == bad['winner'] else p for p in wp]
    ck('P2 the stack\'s windows read only provenance winners', set(wp) <= win,
       '%d of %d windows are not winners' % (len(set(wp) - win), len(wp)))
    loser_ids = {p: d['identity'] for d in dec for p in d['cands']}
    ids = collections.Counter(loser_ids[p] for p in wp if p in loser_ids)
    ck('P3 no window identity appears twice in the stack\'s windows (one observation, one product)',
       max(ids.values()) == 1, 'max %d' % max(ids.values()))
    gp = [p for g in G for p in g['paths']]
    if drive == 5:     # one observation in two groups
        gp = gp + [G[0]['paths'][0]]
    gid = collections.Counter((loser_ids[p], round(g['sf_common_lo'] / 1e6, 3)) for g in G for p in g['paths'])
    ck('P4 every group path is a winner, and no identity enters two groups', set(gp) <= win and len(gp) ==
       len(set(gp)) and len({loser_ids[p] for p in gp}) == len(gp),
       '%d group-paths, %d distinct, %d identities' % (len(gp), len(set(gp)), len({loser_ids[p] for p in gp})))
    cen_bad = [d for d in dec if d['set'] == 'census' and d['status'] not in ('ring_ok', 'prerepair_declared')
               and d['array'] in DISH]
    ndecl = sum(1 for d in dec if d['status'] == 'prerepair_declared')
    ck('P5 every census window the stack can read is on its own dish\'s ring, except the declared ones whose '
       'repaired product does not exist', not cen_bad, '%d off-ring undeclared, %d declared' % (len(cen_bad), ndecl))
    hb = {r['path']: r for r in H['rows']}
    cen_multi = [d for d in dec if d['set'] == 'census' and d['n_cand'] > 1]
    cen_rec = [d for d in cen_multi if not d['winner_matches_record']
               and any(matches_record(hb[p], P.get(d['block'], [])) for p in d['cands'])]
    if drive == 6:     # a census winner swapped for a sibling while the record identifies the other product
        cen_rec = cen_rec + [cen_multi[0]]
    unver = [d['identity'] for d in cen_multi if not any(matches_record(hb[p], P.get(d['block'], []))
                                                         for p in d['cands'])]
    ck('P6 where a census window has more than one product and the published row identifies one of them, the '
       'winner is that one', not cen_rec, '%d not; %d of %d windows where no product carries a matching result '
       '(%s)' % (len(cen_rec), len(unver), len(cen_multi), ', '.join(u.split('|')[0] for u in unver) or '-'))
    bw_ok = all(p in win for p in BW)
    ck('P7 every excluded (bad-weight) product is named by its winner, so the exclusion still applies',
       bw_ok, '%d of %d' % (sum(p in win for p in BW), len(BW)))
    NK = jload(os.path.join(tree, 'r27inputs', 'stackfix', 'namekey', 'windows.json'))
    INV = jload(os.path.join(tree, 'stack_v408', 'inventory.json'))
    REFS = velocity_refs(tree)
    if drive == 8:     # one window framed by its directory-name key again (the 18th join back)
        _i = next(i for i, w in enumerate(W) if w['has_vsys'] and name_key(w['star']) not in
                  {r['key'] for r in REFS})
        _w = W[_i]
        _dv = 0.0 - _w['v_corr']
        _f = 1.0 / (1.0 - _dv / C_KMS)
        W = W[:_i] + [dict(_w, v_sys=None, dv=_dv, sf_lo=_w['f_lo'] * _f, sf_hi=_w['f_hi'] * _f,
                           has_vsys=False)] + W[_i + 1:]
    try:
        W1, _ = rebuild_windows(dec, NK, INV)
        W1n, _ = reframe(W1, REFS, by='name')
        p11 = W1n == W1
        W2, rep61 = reframe(W1, REFS, by='identity')
        same = W2 == W
    except TieError as e:
        p11 = same = False
        rep61 = {'error': str(e)[:200]}
    ck('P11 groups.py\'s frame arithmetic, re-done here from the NAME lookup, reproduces every deposited frame '
       'exactly (so the identity frame below differs from it only in which velocity is attached)', p11,
       '%d windows' % len(W))
    ck('P9 the frozen windows are exactly the deposited windows with each identity\'s product replaced by its '
       'winner, framed by STELLAR IDENTITY (row 61); nothing else differs', same, '%d windows' % len(W))
    _idv = [w for w in W if w['has_vsys']]
    _ok12 = all(len(identity_match(w, REFS)) == 1 and identity_match(w, REFS)[0]['v'] == w['v_sys'] for w in _idv) \
        and not any(identity_match(w, REFS) for w in W if not w['has_vsys'])
    ck('P12 every frozen window carries the velocity of the star it IS (position at its epoch + parallax), and '
       'none lacks one its identity has', _ok12, dict(rep61))
    _f61 = jload(os.path.join(tree, 'stack_v408', 'frame_r61.json'))
    _rp = reframed_paths(W, REFS)
    ck('P13 stack_v408/frame_r61.json lists exactly the windows framed by identity whose name key had no velocity',
       _f61 == dict(_doc=FRAME61_DOC, paths=_rp), '%d windows' % len(_rp))
    sys.path.insert(0, os.path.join(tree, 'stack_v408'))
    import groups3
    import starkey
    ident, _ = starkey.build(W)
    G2 = groups3.build(W, ident)
    if drive == 7:     # a group list not rebuilt after the selection changed
        G2 = G2[:-1]
    ck('P10 the frozen groups are exactly groups3.build() on those windows', json.loads(json.dumps(G2)) == G,
       '%d groups' % len(G))
    pre = collections.Counter(d['set'] for d in dec if d['status'] == 'prerepair_only')
    ck('P8 the windows left on pre-repair products are hold-out / extension / control windows only '
       '(Ruling 25), and are counted', set(pre) <= {'holdout', 'extension', 'oos'}, dict(pre))
    return M


def main():
    tree = sys.argv[sys.argv.index('--tree') + 1] if '--tree' in sys.argv else HERE
    if '--check' in sys.argv:
        drive = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else 0
        print('stackprov_r27 --check (drive %d)' % drive)
        M = check(tree, drive)
        nf = sum(1 for _, ok in M if not ok)
        print('stackprov_r27: %d FAIL' % nf)
        sys.exit(1 if nf else 0)
    if '--selftest' in sys.argv:        # every drive must FAIL, and drive 0 must pass; writes nothing
        bad = []
        for drv in range(0, 9):
            print('--- drive %d' % drv)
            nf = sum(1 for _, ok in check(tree, drv) if not ok)
            if (drv == 0) != (nf == 0):
                bad.append(drv)
        print('stackprov_r27 selftest: %s' % ('ALL DRIVES BEHAVE (0 passes, 1-8 fail)' if not bad
                                              else 'MISBEHAVING DRIVES %s' % bad))
        sys.exit(1 if bad else 0)
    if '--select' in sys.argv:          # build mode (cluster): decisions + windows from the old windows
        out = sys.argv[sys.argv.index('--select') + 1]
        H, A, P, CEN, D = load_all(tree)
        dec, used = select(H, A, P, CEN, D)
        W = jload(os.path.join(tree, 'r27inputs', 'stackfix', 'namekey', 'windows.json'))
        INV = jload(os.path.join(tree, 'stack_v408', 'inventory.json'))
        W1, rep = rebuild_windows(dec, W, INV)
        W2, rep61 = reframe(W1, velocity_refs(tree), by='identity')     # row 61
        print('row 61 frames: %s' % dict(rep61))
        os.makedirs(out, exist_ok=True)
        json.dump(dec, open(os.path.join(out, 'stackprov_decisions.json'), 'w'), indent=0)
        json.dump(W2, open(os.path.join(out, 'windows.json'), 'w'))
        json.dump(dict(_doc=FRAME61_DOC, paths=reframed_paths(W2, velocity_refs(tree))),
                  open(os.path.join(out, 'frame_r61.json'), 'w'), indent=0)
        print('decisions %d  rules %s  status %s' % (len(dec), dict(collections.Counter(d['rule'] for d in dec)),
                                                    dict(collections.Counter(d['status'] for d in dec))))
        print('windows %d -> %d  %s' % (len(W), len(W2), dict(rep)))


if __name__ == '__main__':
    main()
