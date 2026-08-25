from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
import json, numpy as np, warnings, time
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')
Simbad.TIMEOUT = 15

ranked = json.load(open('ranked_all.json'))
need = [(i, s) for i, s in enumerate(ranked[:100]) if s['name'].startswith('Gaia DR3')]
print(f"{len(need)} of top-100 need SIMBAD name resolution")

def resolve(item):
    i, s = item
    try:
        c = SkyCoord(s['ra']*u.deg, s['dec']*u.deg)
        r = Simbad.query_region(c, radius=3*u.arcsec)
        if r is None or len(r) == 0:
            return i, None
        return i, str(r[0]['MAIN_ID'])
    except Exception:
        return i, None

t0=time.time(); resolved = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(resolve, item): item for item in need}
    for f in as_completed(futs):
        i, name = f.result()
        if name:
            ranked[i]['simbad_name'] = name
            resolved += 1
        else:
            ranked[i]['simbad_name'] = None
print(f"resolved {resolved}/{len(need)} in {time.time()-t0:.0f}s")
json.dump(ranked, open('ranked_all.json', 'w'), indent=1)
