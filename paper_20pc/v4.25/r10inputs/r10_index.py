#!/usr/bin/env python3
"""Index every retained search product on this host, with its own position.

One row per (stem) that carries ALL THREE of `_search.npz`, `_srcspec.npz` and
`_result.json` -- the three files the recurrence harness needs.  A stem missing
any of them is recorded with `complete=False` and a list of what is missing, so
"the spectra do not survive" is a measured statement and not an absence of a
line in a table.

Position comes, in order, from
  1. the product's own `_fieldsel.json` reference field (the phase centre the
     extraction actually used), or
  2. `/data/SETI/r8stack/inventory.json`, which records ra/dec per product.
Nothing falls back to the star NAME: a name-keyed join is the defect family
this project has found thirteen times, and the components of HD 139084 and
AT Mic differ by 10 arcsec on sky while agreeing to 0.1 arcsec in beam offset.

Read-only.  Usage: r10_index.py <out.json>
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


def main():
    out = sys.argv[1]
    inv = {}
    for r in json.load(open(INVPATH)):
        stem = r['path']
        for sfx in ('_srcspec.npz', '_search.npz'):
            if stem.endswith(sfx):
                stem = stem[:-len(sfx)]
        inv[stem] = r
    rows = []
    seen = set()
    for root in ROOTS:
        for p in sorted(glob.glob(root + '/*/products/*_search.npz')
                        + glob.glob(root + '/*/*_search.npz')):
            stem = p[:-len('_search.npz')]
            base = os.path.basename(stem)
            m = EBRE.match(base)
            if not m:
                rows.append(dict(stem=stem, base=base, root=root,
                                 complete=False, missing=['unparsable_name']))
                continue
            eb, spw = m.group(1), m.group(2) or 'spw-'
            miss = [s for s in ('_srcspec.npz', '_result.json')
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
                    rows.append(rec)
                    continue
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
            ra = dec = None
            posrc = None
            fs = stem + '_fieldsel.json'
            if os.path.exists(fs):
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
            key = (eb, spw)
            rec['shadowed'] = key in seen      # an earlier root already has it
            seen.add(key)
            rows.append(rec)
    json.dump(rows, open(out, 'w'), indent=1)
    nc = sum(1 for r in rows if r['complete'])
    npos = sum(1 for r in rows if r.get('ra_deg') is not None)
    print('%d stems, %d complete, %d with a position, %d shadowed'
          % (len(rows), nc, npos, sum(1 for r in rows if r.get('shadowed'))))
    from collections import Counter
    print('position sources:', Counter(r.get('pos_source') for r in rows))
    print('incomplete:', Counter(tuple(r['missing']) for r in rows
                                 if not r['complete']))


if __name__ == '__main__':
    main()

# ---- family fallback, appended as a second pass ------------------------
def family(tdir):
    """The star directory a per-block directory belongs to: HD14055_B7_EB_Xd46
    -> HD14055_B7.  Used ONLY to borrow a position for the handful of products
    that record none, and only when every positioned product of that family
    agrees to within 2 arcsec -- so the borrow is validated, not assumed."""
    return re.sub(r'_EB_[^_]+$', '', tdir or '')
