import numpy as np
from astropy.table import Table, vstack
from astropy.coordinates import SkyCoord
import astropy.units as u

ALMA = Table.read('alma_mous_dedup.ecsv', format='ascii.ecsv')
ALMA_ALL = Table.read('alma_public_science_raw.ecsv', format='ascii.ecsv')  # for per-target aggregation

# ---------------------------------------------------------------- source 1:
# nearby Gaia stars (<50 pc) with confirmed ALMA archival coverage
gaia = Table.read('gaia_nearby50pc.ecsv', format='ascii.ecsv')
gaia['dist_pc'] = 1000.0 / gaia['parallax']
gmatch = Table.read('gaia_alma_matches.ecsv', format='ascii.ecsv')
cand1 = []
for row in gmatch:
    g = gaia[row['star_idx']]
    a = ALMA[row['alma_idx']]
    cand1.append(dict(
        name=f"Gaia DR3 {g['source_id']}", source='nearby_gaia',
        ra=float(g['ra']), dec=float(g['dec']),
        gaia_source_id=int(g['source_id']),
        dist_pc=float(g['dist_pc']), dist_err_pc=np.nan,
        gmag=float(g['phot_g_mean_mag']), teff=float(g['teff_gspphot']) if g['teff_gspphot'] is not np.ma.masked else np.nan,
        pmra=float(g['pmra']), pmdec=float(g['pmdec']),
        pmra_err=float(g['parallax_error']), pmdec_err=np.nan,  # placeholder, filled properly below if avail
        is_exo_host=False, n_planets=0, min_planet_rade=np.nan,
        is_disk_host=False,
        alma_mous=str(a['member_ous_uid']), alma_target=str(a['target_name']),
        alma_band=str(a['band_list']), alma_specres_hz=float(a['spectral_resolution']) if a['spectral_resolution'] is not np.ma.masked else np.nan,
        alma_texp_s=float(a['t_exptime']), alma_science_kw=str(a['science_keyword']),
        alma_sep_arcsec=float(row['sep_arcsec']),
    ))
print(f"source 1 (nearby Gaia + ALMA): {len(cand1)} raw rows")

# ---------------------------------------------------------------- source 2:
# exoplanet-host stars with confirmed ALMA archival coverage
exo_hosts = Table.read('exo_hosts_unique.ecsv', format='ascii.ecsv')
exo_pm = Table.read('exo_hosts_gaia_pm.ecsv', format='ascii.ecsv')
exo_pm_map = {int(r['host_idx']): r for r in exo_pm}
ematch = Table.read('exo_alma_matches.ecsv', format='ascii.ecsv')
cand2 = []
for row in ematch:
    h = exo_hosts[row['host_idx']]
    a = ALMA[row['alma_idx']]
    pm = exo_pm_map.get(int(row['host_idx']))
    cand2.append(dict(
        name=str(h['hostname']), source='exoplanet_host',
        ra=float(h['ra']), dec=float(h['dec']),
        gaia_source_id=int(pm['source_id']) if pm is not None else -1,
        dist_pc=float(h['sy_dist']) if h['sy_dist'] is not None else np.nan,
        dist_err_pc=np.nan,
        gmag=float(pm['phot_g_mean_mag']) if pm is not None else (float(h['sy_vmag']) if h['sy_vmag'] is not None else np.nan),
        teff=float(h['st_teff']) if h['st_teff'] is not None else np.nan,
        pmra=float(pm['pmra']) if pm is not None else np.nan,
        pmdec=float(pm['pmdec']) if pm is not None else np.nan,
        pmra_err=float(pm['pmra_error']) if pm is not None else np.nan,
        pmdec_err=float(pm['pmdec_error']) if pm is not None else np.nan,
        is_exo_host=True, n_planets=int(h['n_planets_confirmed']),
        min_planet_rade=float(h['min_planet_rade']) if h['min_planet_rade'] is not None else np.nan,
        is_disk_host=False,
        alma_mous=str(a['member_ous_uid']), alma_target=str(a['target_name']),
        alma_band=str(a['band_list']), alma_specres_hz=float(a['spectral_resolution']) if a['spectral_resolution'] is not np.ma.masked else np.nan,
        alma_texp_s=float(a['t_exptime']), alma_science_kw=str(a['science_keyword']),
        alma_sep_arcsec=float(row['sep_arcsec']),
    ))
print(f"source 2 (exoplanet hosts + ALMA): {len(cand2)} raw rows")

# ---------------------------------------------------------------- source 3:
# disk-tagged ALMA targets resolved to Gaia stars (own position = ALMA target)
disk = Table.read('disk_hosts_gaia_resolved.ecsv', format='ascii.ecsv')
disk_meta = Table.read('alma_disk_tagged.ecsv', format='ascii.ecsv')
cand3 = []
for row in disk:
    dist_pc = 1000.0/float(row['parallax']) if row['parallax'] > 0 else np.nan
    # attach ALL matching ALMA disk MOUS entries for this target name
    sub = disk_meta[np.array([str(x) for x in disk_meta['target_name']]) == str(row['tname'])]
    for a in sub:
        cand3.append(dict(
            name=f"Gaia DR3 {row['source_id']} ({row['tname']})", source='disk_host',
            ra=float(row['ra']), dec=float(row['dec']),
            gaia_source_id=int(row['source_id']),
            dist_pc=dist_pc, dist_err_pc=np.nan,
            gmag=float(row['phot_g_mean_mag']), teff=np.nan,
            pmra=float(row['pmra']), pmdec=float(row['pmdec']),
            pmra_err=float(row['pmra_error']), pmdec_err=float(row['pmdec_error']),
            is_exo_host=False, n_planets=0, min_planet_rade=np.nan,
            is_disk_host=True,
            alma_mous=str(a['member_ous_uid']), alma_target=str(a['target_name']),
            alma_band=str(a['band_list']), alma_specres_hz=float(a['spectral_resolution']) if a['spectral_resolution'] is not np.ma.masked else np.nan,
            alma_texp_s=float(a['t_exptime']), alma_science_kw=str(a['science_keyword']),
            alma_sep_arcsec=0.0,
        ))
print(f"source 3 (disk hosts + ALMA): {len(cand3)} raw rows")

allcand = cand1 + cand2 + cand3
print(f"\nTotal raw candidate-MOUS rows before dedup: {len(allcand)}")

import json
json.dump(allcand, open('all_candidates_raw.json','w'), default=lambda o: None if (isinstance(o,float) and np.isnan(o)) else o)
print("saved all_candidates_raw.json")
