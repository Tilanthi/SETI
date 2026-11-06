#!/usr/bin/env python3
"""r27 stackfix -- PROVENANCE HARVEST of every product in the stack's frozen inventory (read-only over the products).
For each `*_srcspec.npz` in inventory.json: the geometry record the extractor wrote (pb_arcsec, and dish_m /
ann_syn_factor / bmax_m / syn_arcsec when the repaired extractor wrote it), the stellar position (t1_ra, t1_dec),
parallax, chanw, the median frequency, a sha256 of every array the stack reads (I_star, I_control_sample, W, freqs,
times) and of the file, and the sibling result.json's published quantities (rms_combined_mJy, star_peak_snr,
primary_beam_fwhm_arcsec, on_source_s, n_control_ge_star, sha of ctrl_all rounded to 1e-4), plus mtime and size.
No directory name and no mtime is used by the selection; they are recorded so the report can show what the old
inventory keyed on.   Usage: harvest.py inventory.json out.json [nproc]"""
import json, sys, os, hashlib, datetime
from multiprocessing import Pool
import numpy as np
ARR = ('I_star', 'I_control_sample', 'W', 'freqs', 'times')
GEO = ('pb_arcsec', 'dish_m', 'ann_syn_factor', 'bmax_m', 'syn_arcsec', 't1_ra', 't1_dec', 'parallax', 'chanw',
       'l_star', 'm_star', 'phase_ra', 'phase_dec')
def sha(b): return hashlib.sha256(b).hexdigest()
def one(p):
    r = dict(path=p)
    try:
        st = os.stat(p); r['mtime'] = datetime.datetime.utcfromtimestamp(st.st_mtime).isoformat()[:19]; r['size'] = st.st_size
        with open(p, 'rb') as fh: r['sha_file'] = sha(fh.read())
        d = np.load(p, allow_pickle=True)
        for k in GEO:
            if k in d.files: r[k] = float(d[k])
        for k in ('star_name', 'pos_convention'):
            if k in d.files: r[k] = str(d[k])
        r['sha'] = {k: sha(np.ascontiguousarray(d[k]).tobytes()) for k in ARR if k in d.files}
        f = d['freqs']; r['fmed'] = float(np.median(f)); r['f_lo'] = float(np.min(f)); r['f_hi'] = float(np.max(f))
        r['nchan'] = int(f.size); r['nint'] = int(d['times'].size)
        q = p.replace('_srcspec.npz', '_result.json')
        if os.path.exists(q):
            j = json.load(open(q))
            r['res'] = dict(rms=j.get('rms_combined_mJy'), snr=j.get('star_peak_snr'), pb=j.get('primary_beam_fwhm_arcsec'),
                            onsrc=j.get('on_source_s'), nge=j.get('n_control_ge_star'), eb=j.get('eb'),
                            flo=j.get('freq_lo_GHz'), fhi=j.get('freq_hi_GHz'),
                            ctrl_sha=sha(json.dumps([round(x, 4) for x in j.get('ctrl_all') or []]).encode()))
    except Exception as e:
        r['err'] = '%s: %s' % (type(e).__name__, str(e)[:200])
    return r
if __name__ == '__main__':
    inv = [x['path'] for x in json.load(open(sys.argv[1]))]
    with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 48) as pool:
        rows = pool.map(one, inv, chunksize=4)
    json.dump(dict(source=os.path.abspath(sys.argv[1]), n=len(rows), rows=rows), open(sys.argv[2], 'w'))
    print('harvested %d products, %d errors' % (len(rows), sum('err' in r for r in rows)))
