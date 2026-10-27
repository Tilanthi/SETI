#!/usr/bin/env python3
r"""Recurrence plan, version 2: the product selection is GATED, not preferred.

Version 1 of this plan chose, among several copies of the same window, the one
that sorted first.  That was wrong, and the way we found out is worth writing
down: **489 of the 2729 retained windows exist in more than one directory on
this host, and 372 of those pairs disagree about the window's own statistic.**
`<star>_B7/products/` and `<star>_B7_EB_<tag>/products/` hold two extractions
of one execution block with the same integration count and different peaks, and
it is the per-block `_EB_` copy that the released catalogue carries.  Choosing
by sort order silently moved four crossings' statistics by 2-4 per cent.

So the discovery window of a crossing is not *preferred*, it is *identified*:
the product whose own published peak reproduces the T* the paper prints for that
crossing.  The field-truncation re-extraction is checked against its own
record in `fieldfix_v409.json`, the released windows against the deposited
catalogue.  Exactly one product must match, and a crossing for which none does
is reported as unresolved rather than measured.

Repeat windows carry no per-crossing published statistic, so they are selected
the same way against the catalogue row for their own (block, channel width,
span), and where the block is outside the released catalogue -- the follow-up
and archival-extension epochs -- every copy must agree to 1e-6 or the window is
dropped and named.

Usage: r10_plan2.py <index.json> <crossings.json> <catalogue.csv>
                    <fieldfix.json> <worklist_all.json> <out.json>
"""
import csv
import json
import math
import re
import sys
from collections import defaultdict

POS_TOL = 2.0
FAMILY_TOL = 2.0
TREL = 1e-3


def famname(tdir):
    return re.sub(r'_EB_[^_]+$', '', tdir or '')


def sep_arcsec(a, b):
    ra1, d1 = math.radians(a[0]), math.radians(a[1])
    ra2, d2 = math.radians(b[0]), math.radians(b[1])
    c = (math.sin(d1) * math.sin(d2)
         + math.cos(d1) * math.cos(d2) * math.cos(ra1 - ra2))
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * 3600.0


def close(a, b, rel=TREL):
    return a is not None and b is not None and abs(a - b) <= rel * max(abs(b), 1.0)


def main():
    idxp, crp, catp, ffp, wlp, outp = sys.argv[1:7]
    IDX = [r for r in json.load(open(idxp)) if r['complete']]
    CROSS = json.load(open(crp))
    CAT = list(csv.DictReader(open(catp)))
    FF = json.load(open(ffp))
    WL = json.load(open(wlp))
    released_ebs = {w['eb'] for w in WL}

    byeb = defaultdict(list)
    for r in IDX:
        byeb[r['eb']].append(r)
    fam = defaultdict(list)
    for r in IDX:
        if r.get('ra_deg') is not None:
            fam[famname(r['tdir'])].append(r)
    borrowed, unplaced = 0, []
    for r in IDX:
        if r.get('ra_deg') is not None:
            continue
        sibs = fam.get(famname(r['tdir']), [])
        if not sibs:
            unplaced.append(r['stem'])
            continue
        p0 = (sibs[0]['ra_deg'], sibs[0]['dec_deg'])
        spread = max(sep_arcsec(p0, (s['ra_deg'], s['dec_deg'])) for s in sibs)
        if spread > FAMILY_TOL:
            unplaced.append(r['stem'])
            continue
        r['ra_deg'], r['dec_deg'] = p0
        r['pos_source'] = 'family:%s(spread %.3f arcsec)' % (
            famname(r['tdir']), spread)
        borrowed += 1

    catk = {}
    for c in CAT:
        lo = min(float(c['flo_GHz']), float(c['fhi_GHz']))
        catk[(c['eb'], round(float(c['chanw_Hz']), 1), round(lo, 5))] = c
    ffk = {}
    for q in FF:
        lo = min(q['flo'], q['fhi'])
        ffk[(q['eb'], round(float(q['chanw']), 1), round(lo, 5))] = q

    def wkey(r):
        return (r['eb'], round(float(r['chanw_Hz']), 1), round(r['f_lo_GHz'], 5))

    def identify(cands, target):
        return [r for r in cands if close(r['star_peak_snr'], target)]

    copies = defaultdict(list)
    for r in IDX:
        copies[(r['eb'], r['spw'])].append(r)

    def pick_repeat(eb, spw):
        cs = copies[(eb, spw)]
        rex = [r for r in cs if r['root'].startswith('/data/SETI/r8reext')]
        if rex:
            q = ffk.get(wkey(rex[0]))
            m = identify(rex, q['star_snr']) if q else rex
            if m:
                return m[0], 'repaired' + ('' if q else '(no repair record)')
        rest = [r for r in cs if not r['root'].startswith('/data/SETI/r8reext')]
        if not rest:
            return None, 'no_non_repaired_copy'
        c = catk.get(wkey(rest[0]))
        if c is not None:
            m = identify(rest, float(c['star_snr']))
            if len(m) >= 1:
                return m[0], 'catalogue'
            return None, 'no_copy_reproduces_catalogue'
        pk = {round(r['star_peak_snr'], 6) for r in rest}
        if len(pk) == 1:
            return rest[0], 'outside_catalogue_copies_agree'
        return None, 'outside_catalogue_copies_disagree'

    plan = []
    rep = dict(n_products=len(IDX), borrowed_positions=borrowed,
               unplaced=unplaced,
               n_windows_multiple_copies=sum(1 for v in copies.values()
                                             if len(v) > 1),
               n_windows_copies_disagree=sum(
                   1 for v in copies.values()
                   if len({round(r['star_peak_snr'], 6) for r in v}) > 1))
    for c in CROSS:
        f = c['freq_GHz']
        rec = dict(c, discovery=None, repeats=[])
        if not f:
            rec['status'] = 'no_crossing_frequency_recorded'
            plan.append(rec)
            continue
        own = [r for r in byeb.get(c['eb'], [])
               if r['f_lo_GHz'] <= f <= r['f_hi_GHz']]
        if not own:
            rec['status'] = 'discovery_products_do_not_survive'
            rec['diagnostic'] = dict(
                n_windows_of_block_retained=len(byeb.get(c['eb'], [])),
                spans=[[r['spw'], r['f_lo_GHz'], r['f_hi_GHz']]
                       for r in byeb.get(c['eb'], [])])
            plan.append(rec)
            continue
        hit, route = [], None
        for r in own:
            q = ffk.get(wkey(r))
            if r['root'].startswith('/data/SETI/r8reext') and q \
                    and close(r['star_peak_snr'], q['star_snr']):
                hit, route = [r], 'repaired'
        if not hit:
            m = identify(own, c['tstar'])
            if m:
                hit, route = m, 'published_tstar'
        if not hit:
            cands = []
            for r in own:
                cc = catk.get(wkey(r))
                if cc is not None and close(r['star_peak_snr'],
                                            float(cc['star_snr'])):
                    cands.append(r)
            if cands:
                hit, route = cands, 'catalogue_row_not_window_peak'
        if not hit:
            rec['status'] = 'discovery_product_unidentified'
            rec['diagnostic'] = dict(
                published_tstar=c['tstar'],
                copies=[[r['stem'], r['star_peak_snr'], r['chanw_Hz']]
                        for r in own])
            plan.append(rec)
            continue
        d = min(hit, key=lambda r: r['chanw_Hz'])
        pos = (d['ra_deg'], d['dec_deg'])
        rec['discovery'] = dict(
            stem=d['stem'], spw=d['spw'], root=d['root'], tdir=d['tdir'],
            route=route, n_copies=len(copies[(d['eb'], d['spw'])]),
            chanw_Hz=d['chanw_Hz'], n_chan=d['n_chan'], n_int=d['n_int'],
            on_source_s=d['on_source_s'], band=d['band'],
            rms_combined_mJy=d['rms_combined_mJy'],
            star_peak_snr=d['star_peak_snr'],
            star_peak_freq_GHz=d['star_peak_freq_GHz'],
            star_peak_drift_Hz_s=d['star_peak_drift_Hz_s'],
            n_drift_trials=d['n_drift_trials'],
            ra_deg=pos[0], dec_deg=pos[1], pos_source=d['pos_source'],
            repaired=d['root'].startswith('/data/SETI/r8reext'),
            tstar_ledger=c['tstar'],
            is_window_peak=bool(
                d['star_peak_freq_GHz'] is not None
                and abs(d['star_peak_freq_GHz'] - f) * 1e9
                < 1.5 * d['chanw_Hz']))
        cand = defaultdict(list)
        for r in IDX:
            if r['eb'] == c['eb'] or r.get('ra_deg') is None:
                continue
            if not (r['f_lo_GHz'] <= f <= r['f_hi_GHz']):
                continue
            if sep_arcsec(pos, (r['ra_deg'], r['dec_deg'])) > POS_TOL:
                continue
            cand[(r['eb'], r['spw'])].append(r)
        chosen, dropped = {}, []
        for (eb2, spw2) in sorted(cand):
            w, route2 = pick_repeat(eb2, spw2)
            if w is None:
                dropped.append([eb2, spw2, route2])
                continue
            o = chosen.get(eb2)
            if o is None or w['chanw_Hz'] < o[0]['chanw_Hz']:
                chosen[eb2] = (w, route2)
        for eb2, (w, route2) in sorted(chosen.items()):
            rec['repeats'].append(dict(
                eb=eb2, stem=w['stem'], spw=w['spw'], root=w['root'],
                tdir=w['tdir'], route=route2, chanw_Hz=w['chanw_Hz'],
                n_int=w['n_int'], on_source_s=w['on_source_s'],
                rms_combined_mJy=w['rms_combined_mJy'],
                in_released_catalogue=eb2 in released_ebs,
                sep_arcsec=round(sep_arcsec(pos,
                                            (w['ra_deg'], w['dec_deg'])), 4)))
        rec['repeats_dropped'] = dropped
        catcov = set()
        for cc in CAT:
            if cc['eb'] == c['eb']:
                continue
            lo = min(float(cc['flo_GHz']), float(cc['fhi_GHz']))
            hi = max(float(cc['flo_GHz']), float(cc['fhi_GHz']))
            if lo <= f <= hi and cc['star_name'] == c['star']:
                catcov.add(cc['eb'])
        rec['n_catalogue_covering_blocks'] = len(catcov)
        rec['catalogue_blocks_without_spectra'] = sorted(
            catcov - set(chosen) - {c['eb']})
        rec['status'] = 'ok' if rec['repeats'] else 'no_repeat_coverage'
        plan.append(rec)
    json.dump(dict(report=rep, plan=plan), open(outp, 'w'), indent=1)
    from collections import Counter
    print(json.dumps(rep, indent=1))
    print('status:', Counter(p['status'] for p in plan))
    print('discovery route:', Counter(
        (p['discovery'] or {}).get('route') for p in plan))
    for p in plan:
        d = p['discovery'] or {}
        print('%-4s %-26s %-22s %13s %-34s nrep=%-3d cat=%-3s route=%-26s '
              'pk=%-5s T_prod=%-9s T_led=%s'
              % (p['cid'], p['star'][:26], p['eb'], p['freq_GHz'],
                 p['status'], len(p['repeats']),
                 p.get('n_catalogue_covering_blocks'), d.get('route'),
                 d.get('is_window_peak'),
                 ('%.4f' % d['star_peak_snr']) if d.get('star_peak_snr')
                 is not None else '-', p['tstar']))


if __name__ == '__main__':
    main()
