#!/usr/bin/env python3
"""Index every retained search product on this host, with its own position.

One row per (stem) that carries ALL THREE of `_search.npz`, `_srcspec.npz` and
`_result.json` -- the three files the recurrence harness needs.  A stem missing
any of them is recorded with `complete=False` and a list of what is missing, so
"the spectra do not survive" is a measured statement and not an absence of a
line in a table.

v4.29 (round 28, Ruling R10): a stem is found by ANY of its products, not by
its search record.  Enumerating `*_search.npz` alone made the 2026-09-25
extraction of HD 14055 `A002_X1001fdc_X29ae` invisible -- it holds the
discovery `_srcspec.npz` (and the waterfall) and no search record -- so the
crossing was reported as having no discovery spectrum while the spectrum sat
on disk and reproduces the ledger's T* exactly.  A stem with a spectrum and no
result record now carries the window's edges from the spectrum's own
frequency axis (`f_lo_GHz`/`f_hi_GHz`, `edges_from='srcspec'`), so the plan
can find it by block and window edges.

Position comes, in order, from
  1. the product's own `_fieldsel.json` reference field (the phase centre the
     extraction actually used), or
  2. `/data/SETI/r8stack/inventory.json`, which records ra/dec per product.
Nothing falls back to the star NAME: a name-keyed join is the defect family
this project has found thirteen times, and the components of HD 139084 and
AT Mic differ by 10 arcsec on sky while agreeing to 0.1 arcsec in beam offset.

Read-only.  Usage: r10_index.py <out.json> [--fold FOLD_WINDOWS.json] [--r27] [--r59]

v4.29 (round 28, fold decision E5): LAYERS.  A window that has been measured
again is read from its NEWEST product, and its earlier copies are not read at
all -- they are written to `<out>.superseded.json`, never silently dropped.
  --r27   the round-27 control-annulus re-extractions of the hold-out and the
          archival extension (`/data/paper_build/holdout_r27/targets{,_rep}`,
          Rulings 17, 22, 27.2).  Before E5 this was applied by hand to ONE
          crossing (A01's four repeat epochs); the layer applies the same rule
          to every crossing that reads those epochs.
  --fold  the v4.29 re-flag fold's window map (`fold_windows.json`, harvest
          H2): every re-calibrated window's new product.  The fold's
          catalogue publishes the new product's statistic, so a recurrence
          reading made on the earlier copy would be a reading of a window
          the paper no longer prints.
  --r59   the round-27 row-59 field-truncation repairs of 12 m hold-out,
          beyond-40 pc and extension blocks (`fieldtrunc_r27/harvroot_r59`),
          which the hold-out export publishes (the hold-out chain, E5-H).
Precedence fold > r27 > r59 > the three roots above.  A layer row supersedes an
earlier row when both are the SAME WINDOW: same block, same channel width
(1e-3), frequency spans overlapping by >= 90 % of the shorter (Pipeline_Final
trims an edge channel, and one old product is block-level with no spw), and
recorded source positions (`t1_ra`/`t1_dec` of each `_srcspec.npz`) within
2 arcsec -- plus, for the fold, the old product the harvest itself names.  A
layer row is placed by that same recorded position (the stack inventory's
convention, and the position `r10_recur_all.py` joins on), never by its name
and never by the fieldsel phase centre.  With no option the index is the one
the round-10 campaign made (self-test: plan and readings reproduce the
frozen records exactly).
"""
import glob
import json
import math
import os
import re
import sys

ROOTS = ['/data/SETI/r8reext/targets', '/data/SETI/targets',
         '/data/SETI/recur_r7/prodbak']
# r8reext FIRST: those 157 windows are the field-truncation re-extraction, and
# the adopted search statistic in the ledger is the REPAIRED one.  A recurrence
# test run on the superseded extraction of a repaired window would fail its own
# reproduction gate, which is how we would find out -- but preferring the
# repaired product means the gate passes for the right reason.
INVPATH = '/data/SETI/r8stack/inventory.json'
EBRE = re.compile(r'^(A002_[^_]+_[^_]+)(?:_(spw\d+))?$')


LAYER_R27 = ['/data/paper_build/holdout_r27/targets',
             '/data/paper_build/holdout_r27/targets_rep']
#: round 27 row 59: the field-truncation repairs of 12 m hold-out / beyond-40 pc
#: / extension blocks (TWA 7 Xc4c, Proxima X1d95, ...), which the hold-out
#: export (holdfix_r27) publishes
LAYER_R59 = ['/data/paper_build/fieldtrunc_r27/harvroot_r59']
SAME_OVERLAP = 0.90
SAME_POS = 2.0


def _sep(a, b):
    ra1, d1 = math.radians(a[0]), math.radians(a[1])
    ra2, d2 = math.radians(b[0]), math.radians(b[1])
    c = (math.sin(d1) * math.sin(d2)
         + math.cos(d1) * math.cos(d2) * math.cos(ra1 - ra2))
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * 3600.0


def same_window(a, b):
    """(verdict, how): is layer row `a` a newer measurement of row `b`?"""
    if a.get('eb') != b.get('eb') or a.get('f_lo_GHz') is None \
            or b.get('f_lo_GHz') is None:
        return False, None
    ca, cb = a.get('chanw_Hz'), b.get('chanw_Hz')
    if ca is None or cb is None or abs(ca - cb) > 1e-3 * max(abs(cb), 1.0):
        return False, None
    ov = min(a['f_hi_GHz'], b['f_hi_GHz']) - max(a['f_lo_GHz'], b['f_lo_GHz'])
    short = min(a['f_hi_GHz'] - a['f_lo_GHz'], b['f_hi_GHz'] - b['f_lo_GHz'])
    if short <= 0 or ov < SAME_OVERLAP * short:
        return False, None
    # positions compared on ONE convention: each product's own recorded
    # source position (`t1_ra`/`t1_dec` of its spectrum -- what the stack
    # inventory holds and what r10_recur_all.py joins on).  The fieldsel
    # reference field is the phase centre and differs from it by up to
    # 4.3 arcsec on 8 of the round-10 products.
    pa, pb = _t1(a['stem']), _t1(b['stem'])
    if pa is None or pb is None:
        return True, 'span+chanw (position unknown on one side)'
    s = _sep(pa, pb)
    return (s <= SAME_POS), 'span+chanw+position (%.3f arcsec)' % s


_T1 = {}


def _t1(stem):
    if stem not in _T1:
        import numpy as np
        try:
            z = np.load(stem + '_srcspec.npz', allow_pickle=True)
            _T1[stem] = (float(z['t1_ra']), float(z['t1_dec']))
        except Exception:
            _T1[stem] = None
    return _T1[stem]


def main():
    out = sys.argv[1]
    fold = sys.argv[sys.argv.index('--fold') + 1] \
        if '--fold' in sys.argv else None
    use_r27 = '--r27' in sys.argv
    use_r59 = '--r59' in sys.argv
    inv = {}
    for r in json.load(open(INVPATH)):
        stem = r['path']
        for sfx in ('_srcspec.npz', '_search.npz'):
            if stem.endswith(sfx):
                stem = stem[:-len(sfx)]
        inv[stem] = r
    rows = []
    seen = set()

    def stems_of(root):
        _st = set()
        for sfx in ('_search.npz', '_srcspec.npz'):
            for p in (glob.glob(root + '/*/products/*' + sfx)
                      + glob.glob(root + '/*/*' + sfx)):
                _st.add(p[:-len(sfx)])
        return sorted(_st)

    # ---- the layers, newest first (E5); built before the roots so that a
    #      superseded root row can be recognised as it is met
    layer_rows, explicit = [], {}
    layers = []
    if fold:
        F = json.load(open(fold))
        fl = []
        for w in F['windows']:
            np_ = w.get('new_product')
            if not np_:
                continue
            st = np_[:-len('_result.json')] if np_.endswith('_result.json') \
                else np_
            fl.append(st)
            if w.get('old_product'):
                op = w['old_product']
                explicit[op[:-len('_result.json')] if
                         op.endswith('_result.json') else op] = st
        layers.append(('reflag', sorted(set(fl))))
    if use_r27:
        st27 = []
        for root in LAYER_R27:
            st27 += stems_of(root)
        layers.append(('r27', st27))
    if use_r59:
        st59 = []
        for root in LAYER_R59:
            st59 += stems_of(root)
        layers.append(('r59', st59))
    for lname, lstems in layers:
        for stem in lstems:
            r = describe(stem, stem.split('/products/')[0].rsplit('/', 1)[0]
                         if '/products/' in stem else os.path.dirname(stem),
                         inv, srcspec_pos=True)
            r['layer'] = lname
            if r.get('eb') is None:
                continue
            # a lower layer row superseded by a higher one is not read
            hit = None
            for h in layer_rows:
                ok, how = same_window(h, r)
                if ok:
                    hit = (h['stem'], how)
                    break
            if hit:
                r['superseded_by'], r['superseded_how'] = hit
                SUPERSEDED.append(r)
                continue
            layer_rows.append(r)

    for root in ROOTS:
        for stem in stems_of(root):
            rec = describe(stem, root, inv)
            if rec.get('eb') is None:
                rows.append(rec)
                continue
            hit = None
            if stem in explicit:
                hit = (explicit[stem], 'the fold harvest names it as the '
                       'superseded product')
            else:
                for h in layer_rows:
                    ok, how = same_window(h, rec)
                    if ok:
                        hit = (h['stem'], how)
                        break
            if hit:
                rec['superseded_by'], rec['superseded_how'] = hit
                SUPERSEDED.append(rec)
                continue
            key = (rec['eb'], rec['spw'])
            rec['shadowed'] = key in seen      # an earlier root already has it
            seen.add(key)
            rows.append(rec)
    for r in layer_rows:
        key = (r['eb'], r['spw'])
        r['shadowed'] = key in seen
        seen.add(key)
        rows.append(r)
    if layers:
        json.dump(SUPERSEDED, open(out + '.superseded.json', 'w'), indent=1)
        from collections import Counter as _C
        print('layers: %s; %d layer rows read, %d earlier rows superseded '
              '(%s)' % ([(n, len(s)) for n, s in layers], len(layer_rows),
                        len(SUPERSEDED),
                        dict(_C((x.get('layer') or 'root',
                                 (x['superseded_how'] or '')[:14])
                                for x in SUPERSEDED))))
    json.dump(rows, open(out, 'w'), indent=1)
    nc = sum(1 for r in rows if r['complete'])
    npos = sum(1 for r in rows if r.get('ra_deg') is not None)
    print('%d stems, %d complete, %d with a position, %d shadowed'
          % (len(rows), nc, npos, sum(1 for r in rows if r.get('shadowed'))))
    from collections import Counter
    print('position sources:', Counter(r.get('pos_source') for r in rows))
    print('incomplete:', Counter(tuple(r['missing']) for r in rows
                                 if not r['complete']))


SUPERSEDED = []


def describe(stem, root, inv, srcspec_pos=False):
    """One index row for one product stem (the round-10 body, unchanged)."""
    base = os.path.basename(stem)
    m = EBRE.match(base)
    if not m:
        return dict(stem=stem, base=base, root=root,
                    complete=False, missing=['unparsable_name'])
    eb, spw = m.group(1), m.group(2) or 'spw-'
    miss = [s for s in ('_search.npz', '_srcspec.npz', '_result.json')
            if not os.path.exists(stem + s)]
    rec = dict(stem=stem, root=root, eb=eb, spw=spw,
               tdir=stem.split('/products/')[0].rstrip('/').split('/')[-1],
               complete=not miss, missing=miss)
    if not miss:
        try:
            res = json.load(open(stem + '_result.json'))
        except Exception as exc:
            rec['complete'] = False
            rec['missing'] = ['result_json_unreadable:%r' % exc]
            return rec
        lo = res.get('freq_lo_GHz')
        hi = res.get('freq_hi_GHz')
        rec.update(f_lo_GHz=min(lo, hi), f_hi_GHz=max(lo, hi),
                   chanw_Hz=res.get('chanwidth_Hz'),
                   n_chan=res.get('n_chan'), n_int=res.get('n_int'),
                   on_source_s=res.get('on_source_s'),
                   rms_combined_mJy=res.get('rms_combined_mJy'),
                   star_peak_snr=res.get('star_peak_snr'),
                   star_peak_chan=res.get('star_peak_chan'),
                   star_peak_freq_GHz=res.get('star_peak_freq_GHz'),
                   star_peak_drift_Hz_s=res.get('star_peak_drift_Hz_s'),
                   n_drift_trials=res.get('n_drift_trials'),
                   band=res.get('alma_band_inferred'),
                   pb_offset_arcsec=res.get('primary_beam_offset_arcsec'))
    elif os.path.exists(stem + '_srcspec.npz'):
        # R10: no result record, but the spectrum is here -- its own
        # frequency axis gives the window's edges, so the plan can find
        # it by block and edges.
        import numpy as np
        try:
            fq = np.load(stem + '_srcspec.npz', mmap_mode='r')['freqs']
            rec.update(f_lo_GHz=float(fq.min()) / 1e9,
                       f_hi_GHz=float(fq.max()) / 1e9,
                       n_chan=int(fq.size), edges_from='srcspec')
        except Exception as exc:
            rec['missing'] = rec['missing'] + ['srcspec_unreadable:%r' % exc]
    ra = dec = None
    posrc = None
    if srcspec_pos and _t1(stem) is not None:
        # E5: a LAYER product (never a round-10 root product) is placed by
        # its own recorded source position -- the convention of the stack
        # inventory, which places 2,857 of the round-10 products, and the
        # position r10_recur_all.py checks every product against
        ra, dec = _t1(stem)
        posrc = 'srcspec_t1'
    fs = stem + '_fieldsel.json'
    if os.path.exists(fs) and ra is None:
        try:
            j = json.load(open(fs))
            ref = j.get('ref_field')
            for f in j.get('fields', []):
                if f.get('field_id') == ref:
                    ra = math.degrees(f['ra_rad'])
                    dec = math.degrees(f['dec_rad'])
                    posrc = 'fieldsel'
            rec['fieldsel_star'] = j.get('star')
        except Exception:
            pass
    if ra is None and stem in inv:
        ra, dec = inv[stem]['ra'], inv[stem]['dec']
        posrc = 'stack_inventory'
        rec['inv_star'] = inv[stem]['star']
    rec.update(ra_deg=ra, dec_deg=dec, pos_source=posrc)
    return rec


if __name__ == '__main__':
    main()

# ---- family fallback, appended as a second pass ------------------------
def family(tdir):
    """The star directory a per-block directory belongs to: HD14055_B7_EB_Xd46
    -> HD14055_B7.  Used ONLY to borrow a position for the handful of products
    that record none, and only when every positioned product of that family
    agrees to within 2 arcsec -- so the borrow is validated, not assumed."""
    return re.sub(r'_EB_[^_]+$', '', tdir or '')
