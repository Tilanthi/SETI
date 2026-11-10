#!/usr/bin/env python3
"""harvest_jx_r35.py -- (cluster, read-only) freeze, for the crossings of
ALMA J153702653-33192492 and the HD 48370 CO crossing, the search's own
source-region grid (the statistic at the star and at the 134 positions within
0.06 theta_PB of it, at the crossing's channel), the star's offset from the
phase centre and the synthesised beam (srcspec).  Read from the census products (the
re-flag tree targets_D, whose star statistic reproduces the ledger's T* at
the published cell -- asserted).  Writes r35inputs/jx_srcgrid_r35.json.

    python3 harvest_jx_r35.py LEDGER_JSON OUT_JSON ROOT [ROOT ...]
"""
import glob, hashlib, json, os, re, sys
import numpy as np

LED, OUT, ROOTS = sys.argv[1], sys.argv[2], sys.argv[3:]
WANT = ('ALMA J153702653-33192492', 'HD 48370')
rows = [r for r in json.load(open(LED))['rows']
        if any(r['star'].startswith(w) for w in WANT)]
assert len(rows) == 6, len(rows)


def sha(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()


def grid_xy(names):
    """(dl, dm) arcsec of each source-region position, from its name: the
    extractor's probe_positions() puts src_r{r}_{k} at angle 2 pi k / n_r."""
    per = {}
    for nm in names:
        m = re.match(r'src_r([0-9.]+)_(\d+)$', nm)
        if m:
            per.setdefault(m.group(1), []).append(int(m.group(2)))
    xy = []
    for nm in names:
        if nm == 'star':
            xy.append((0.0, 0.0)); continue
        m = re.match(r'src_r([0-9.]+)_(\d+)$', nm)
        r, k = float(m.group(1)), int(m.group(2))
        n = max(per[m.group(1)]) + 1
        th = 2 * np.pi * k / n
        xy.append((r * np.cos(th), r * np.sin(th)))
    return xy


out = []
for r in rows:
    f, T, eb = float(r['freq']), float(r['tstar']), r['eb']
    hit = None
    for root in ROOTS:
        for fn in sorted(glob.glob('%s/*/products/%s_spw*_search.npz' % (root, eb))):
            d = np.load(fn)
            fr = d['freqs'] / 1e9 if d['freqs'].max() > 1e3 else d['freqs']
            if not (fr.min() <= f <= fr.max()):
                continue
            j = int(np.argmin(abs(fr - f)))
            bs = d['best_src']
            lo = max(0, j - 2)
            jj = lo + int(np.argmax(bs[0, lo:j + 3]))
            if abs(float(bs[0, jj]) - T) < 1e-3:
                hit = (root, fn, d, jj, fr)
                break
        if hit:
            break
    assert hit, 'no census product reproduces T* %.4f for %s %.4f' % (T, eb, f)
    root, fn, d, jj, fr = hit
    sp = fn.replace('_search.npz', '_srcspec.npz')
    s = np.load(sp)
    names = [str(x) for x in d['names']]
    xy = grid_xy(names)
    drift = float(d['best_drift'][0, jj])
    out.append(dict(
        star=r['star'], eb=eb, freq=f, tstar=T, attributed=bool(r['attributed']),
        product=fn.split('/products/')[0].split('/')[-1] + '/' + fn.split('/')[-1],
        product_root=root, sha256_search=sha(fn), sha256_srcspec=sha(sp),
        chan=jj, chan_freq_GHz=float(fr[jj]), drift_Hz_s=drift,
        l_star_arcsec=float(s['l_star']) * 206264.806, m_star_arcsec=float(s['m_star']) * 206264.806,
        syn_arcsec=float(s['syn_arcsec']), pb_arcsec=float(s['pb_arcsec']),
        bmax_m=float(s['bmax_m']), chanw_Hz=float(s['chanw']),
        grid=[dict(name=nm, dl=round(x, 4), dm=round(y, 4), T=round(float(d['best_src'][k, jj]), 4))
              for k, (nm, (x, y)) in enumerate(zip(names, xy))],
        ))
json.dump(dict(harvester='harvest_jx_r35.py', ledger=os.path.basename(LED), roots=ROOTS, rows=out),
          open(OUT, 'w'), indent=0)
print('wrote %s: %d crossings' % (OUT, len(out)))
for o in out:
    g = o['grid']; k = max(range(len(g)), key=lambda i: g[i]['T'])
    print(o['star'][:12], o['eb'], o['freq'], o['tstar'], o['product'], 'peak', g[k]['name'], g[k]['T'],
          'l,m %.3f %.3f syn %.2f drift %.1f' % (o['l_star_arcsec'], o['m_star_arcsec'], o['syn_arcsec'], o['drift_Hz_s']))
