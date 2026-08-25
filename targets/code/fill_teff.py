import json, numpy as np
from astroquery.gaia import Gaia
import warnings; warnings.filterwarnings('ignore')

stars = json.load(open('stars_deduped.json'))
need = [s for s in stars if (s['teff'] is None or not np.isfinite(s['teff'])) and s['gaia_source_id'] and s['gaia_source_id'] > 0]
ids = sorted(set(int(s['gaia_source_id']) for s in need))
print(f"{len(need)} stars need teff, {len(ids)} unique Gaia IDs")

teff_map = {}
CHUNK = 500
for i in range(0, len(ids), CHUNK):
    chunk = ids[i:i+CHUNK]
    idlist = ','.join(str(x) for x in chunk)
    q = f"""SELECT source_id, teff_gspphot, radius_gspphot
            FROM gaiadr3.astrophysical_parameters
            WHERE source_id IN ({idlist})"""
    job = Gaia.launch_job_async(q)
    r = job.get_results()
    for row in r:
        if np.isfinite(row['teff_gspphot']):
            teff_map[int(row['source_id'])] = float(row['teff_gspphot'])
    print(f"  chunk {i}-{i+len(chunk)}: {len(r)} rows returned")

filled = 0
for s in stars:
    if (s['teff'] is None or not np.isfinite(s['teff'])) and s['gaia_source_id'] in teff_map:
        s['teff'] = teff_map[s['gaia_source_id']]
        filled += 1
print(f"filled teff for {filled} stars")
still_missing = sum(1 for s in stars if s['teff'] is None or not np.isfinite(s['teff']))
print(f"still missing teff: {still_missing}/{len(stars)}")
json.dump(stars, open('stars_deduped.json', 'w'))
