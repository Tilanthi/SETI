from astroquery.gaia import Gaia
from astropy.table import Table, vstack
import astropy.units as u
from astropy.coordinates import SkyCoord
import numpy as np, warnings, time
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

t = Table.read('alma_disk_tagged.ecsv', format='ascii.ecsv')
names = np.array([str(x) for x in t['target_name']])
uniq_names, first_idx = np.unique(names, return_index=True)
up = t[first_idx]
print(f"{len(up)} unique disk-host target positions to resolve")

COLS = ['source_id','ra','dec','parallax','parallax_error','pmra','pmra_error',
        'pmdec','pmdec_error','phot_g_mean_mag','bp_rp']

def resolve_one(i):
    row = up[i]
    c = SkyCoord(float(row['s_ra'])*u.deg, float(row['s_dec'])*u.deg)
    try:
        j = Gaia.cone_search(c, radius=5*u.arcsec)
        r = j.get_results()
    except Exception as e:
        return None
    if len(r) == 0:
        return None
    # prefer nearest match with a measured parallax; fall back to brightest
    r = r[np.isfinite(r['parallax'])]
    if len(r) == 0:
        return None
    r.sort('phot_g_mean_mag')
    best = r[0]
    out = {c_: best[c_] for c_ in COLS}
    out['tname'] = row['target_name']
    out['alma_ra'] = row['s_ra']; out['alma_dec'] = row['s_dec']
    return out

results = []
t0 = time.time()
with ThreadPoolExecutor(max_workers=12) as ex:
    futs = {ex.submit(resolve_one, i): i for i in range(len(up))}
    done = 0
    for f in as_completed(futs):
        res = f.result()
        if res is not None:
            results.append(res)
        done += 1
        if done % 100 == 0:
            print(f"  {done}/{len(up)} ({time.time()-t0:.0f}s)", flush=True)

print(f"{len(results)}/{len(up)} resolved to a Gaia source in {time.time()-t0:.0f}s")
out_t = Table(rows=[[r[c] for c in COLS+['tname','alma_ra','alma_dec']] for r in results],
              names=COLS+['tname','alma_ra','alma_dec'])
out_t.write('disk_hosts_gaia_resolved.ecsv', format='ascii.ecsv', overwrite=True)
