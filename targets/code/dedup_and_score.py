import json, numpy as np
from collections import defaultdict

raw = json.load(open('all_candidates_raw.json'))
for r in raw:
    for k, v in r.items():
        if v is None:
            r[k] = np.nan

# ---------------------------------------------------------- dedup key
# Prefer Gaia source_id as the identity key; fall back to a rounded
# position key (0.5 arcsec) for the handful of exoplanet hosts we could not
# resolve to Gaia.
def key(r):
    if r['gaia_source_id'] and r['gaia_source_id'] > 0:
        return ('gaia', int(r['gaia_source_id']))
    return ('pos', round(r['ra']*7200), round(r['dec']*7200))  # ~0.5"

groups = defaultdict(list)
for r in raw:
    groups[key(r)].append(r)
print(f"{len(raw)} raw rows -> {len(groups)} unique stars")

stars = []
for k, rows in groups.items():
    best = min(rows, key=lambda r: (r['alma_specres_hz'] if np.isfinite(r['alma_specres_hz']) else 1e12))
    total_texp = np.nansum([r['alma_texp_s'] for r in rows])
    n_mous = len(set(r['alma_mous'] for r in rows))
    bands = sorted(set(b for r in rows for b in str(r['alma_band']).replace(' ','').split(',') if b))
    is_exo = any(r['is_exo_host'] for r in rows)
    is_disk = any(r['is_disk_host'] for r in rows)
    n_planets = max((r['n_planets'] for r in rows), default=0)
    min_rade = np.nanmin([r['min_planet_rade'] for r in rows]) if any(np.isfinite(r['min_planet_rade']) for r in rows) else np.nan
    kw = '; '.join(sorted(set(str(r['alma_science_kw']) for r in rows)))
    dist_candidates = [r['dist_pc'] for r in rows if np.isfinite(r['dist_pc']) and r['dist_pc'] > 0]
    dist_pc = np.nanmedian(dist_candidates) if dist_candidates else np.nan
    gmag_candidates = [r['gmag'] for r in rows if np.isfinite(r['gmag'])]
    gmag = np.nanmin(gmag_candidates) if gmag_candidates else np.nan   # brightest reported value
    teff_candidates = [r['teff'] for r in rows if np.isfinite(r['teff'])]
    teff = np.nanmedian(teff_candidates) if teff_candidates else np.nan
    pmra_candidates = [r['pmra'] for r in rows if np.isfinite(r['pmra'])]
    pmdec_candidates = [r['pmdec'] for r in rows if np.isfinite(r['pmdec'])]
    pmra = pmra_candidates[0] if pmra_candidates else np.nan
    pmdec = pmdec_candidates[0] if pmdec_candidates else np.nan
    pmra_err_candidates = [r['pmra_err'] for r in rows if np.isfinite(r['pmra_err'])]
    pmdec_err_candidates = [r['pmdec_err'] for r in rows if np.isfinite(r['pmdec_err'])]
    pmra_err = pmra_err_candidates[0] if pmra_err_candidates else np.nan
    pmdec_err = pmdec_err_candidates[0] if pmdec_err_candidates else np.nan
    name = sorted(rows, key=lambda r: len(r['name']))[0]['name']
    stars.append(dict(
        name=name, ra=rows[0]['ra'], dec=rows[0]['dec'],
        gaia_source_id=rows[0]['gaia_source_id'],
        dist_pc=dist_pc, gmag=gmag, teff=teff,
        pmra=pmra, pmdec=pmdec, pmra_err=pmra_err, pmdec_err=pmdec_err,
        pm_total_masyr=float(np.hypot(pmra, pmdec)) if np.isfinite(pmra) and np.isfinite(pmdec) else np.nan,
        is_exo_host=is_exo, n_planets=n_planets, min_planet_rade=min_rade,
        is_disk_host=is_disk,
        alma_n_mous=n_mous, alma_total_texp_h=total_texp/3600.0,
        alma_bands=','.join(bands), alma_best_specres_Hz=best['alma_specres_hz'],
        alma_best_target=best['alma_target'], alma_science_keywords=kw,
        alma_best_mous=best['alma_mous'],
    ))

print(f"unique stars: {len(stars)}")
n_no_pm = sum(1 for s in stars if not (np.isfinite(s['pmra']) and np.isfinite(s['pmdec'])))
print(f"stars WITHOUT a measured proper motion: {n_no_pm} (will be excluded from the ranked list)")
n_no_dist = sum(1 for s in stars if not np.isfinite(s['dist_pc']))
print(f"stars without a usable distance: {n_no_dist}")

json.dump(stars, open('stars_deduped.json','w'))
