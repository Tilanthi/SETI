import json, numpy as np
from astroquery.gaia import Gaia
import warnings; warnings.filterwarnings('ignore')

stars = json.load(open('stars_deduped.json'))
need = [s for s in stars if (s['teff'] is None or not np.isfinite(s['teff'])) and s['gaia_source_id'] and s['gaia_source_id'] > 0]
ids = sorted(set(int(s['gaia_source_id']) for s in need))
print(f"{len(ids)} unique Gaia IDs still needing a spectral-type proxy")

bprp_map = {}
CHUNK = 500
for i in range(0, len(ids), CHUNK):
    chunk = ids[i:i+CHUNK]
    idlist = ','.join(str(x) for x in chunk)
    q = f"SELECT source_id, bp_rp FROM gaiadr3.gaia_source WHERE source_id IN ({idlist})"
    job = Gaia.launch_job_async(q)
    r = job.get_results()
    for row in r:
        if row['bp_rp'] is not None and np.isfinite(row['bp_rp']):
            bprp_map[int(row['source_id'])] = float(row['bp_rp'])
    print(f"  chunk {i}: {len(r)} rows")

# Rough BP-RP -> Teff proxy (Pecaut & Mamajek 2013 main-sequence table, coarse bins)
def bprp_to_teff(bprp):
    bins = [(-0.1,0.2,9000),(0.2,0.4,7500),(0.4,0.65,6300),(0.65,0.85,5700),
            (0.85,1.2,5000),(1.2,1.6,4300),(1.6,2.0,3800),(2.0,2.6,3400),(2.6,4.0,3000)]
    for lo,hi,teff in bins:
        if lo <= bprp < hi:
            return teff
    return np.nan

filled = 0
for s in stars:
    if (s['teff'] is None or not np.isfinite(s['teff'])) and s['gaia_source_id'] in bprp_map:
        s['teff'] = bprp_to_teff(bprp_map[s['gaia_source_id']])
        s['teff_is_proxy'] = True
        filled += 1
    else:
        s.setdefault('teff_is_proxy', False)
print(f"filled via BP-RP proxy: {filled}")
still_missing = sum(1 for s in stars if s['teff'] is None or not np.isfinite(s['teff']))
print(f"still missing teff after both passes: {still_missing}/{len(stars)}")
json.dump(stars, open('stars_deduped.json', 'w'))
