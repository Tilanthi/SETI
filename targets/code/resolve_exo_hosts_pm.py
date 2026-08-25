from astroquery.gaia import Gaia
from astropy.table import Table
import astropy.units as u
from astropy.coordinates import SkyCoord
import numpy as np, warnings, time
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

exo_hosts = Table.read('exo_hosts_unique.ecsv', format='ascii.ecsv')
matches = Table.read('exo_alma_matches.ecsv', format='ascii.ecsv')
host_idx = sorted(set(matches['host_idx']))
print(f"{len(host_idx)} matched exoplanet-host stars to resolve PM for")

COLS = ['source_id','ra','dec','parallax','parallax_error','pmra','pmra_error',
        'pmdec','pmdec_error','phot_g_mean_mag','bp_rp']

def resolve_one(i):
    row = exo_hosts[i]
    c = SkyCoord(float(row['ra'])*u.deg, float(row['dec'])*u.deg)
    try:
        j = Gaia.cone_search(c, radius=5*u.arcsec)
        r = j.get_results()
    except Exception:
        return None
    if len(r) == 0:
        return None
    r = r[np.isfinite(r['parallax'])]
    if len(r) == 0:
        return None
    r.sort('phot_g_mean_mag')
    best = r[0]
    out = {c_: best[c_] for c_ in COLS}
    out['host_idx'] = i
    out['hostname'] = row['hostname']
    return out

results = []
t0 = time.time()
with ThreadPoolExecutor(max_workers=12) as ex:
    futs = {ex.submit(resolve_one, i): i for i in host_idx}
    for f in as_completed(futs):
        res = f.result()
        if res is not None:
            results.append(res)
print(f"{len(results)}/{len(host_idx)} resolved in {time.time()-t0:.0f}s")
out_t = Table(rows=[[r[c] for c in COLS+['host_idx','hostname']] for r in results],
              names=COLS+['host_idx','hostname'])
out_t.write('exo_hosts_gaia_pm.ecsv', format='ascii.ecsv', overwrite=True)
