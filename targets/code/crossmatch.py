import json, numpy as np
from astropy.table import Table, vstack, unique
from astropy.coordinates import SkyCoord
import astropy.units as u

# ---------------------------------------------------------------- load ALMA
alma = Table.read('alma_mous_dedup.ecsv', format='ascii.ecsv')
alma_c = SkyCoord(alma['s_ra'], alma['s_dec'])
print(f"ALMA: {len(alma)} unique calibrated MOUS pointings")

# ---------------------------------------------------- load exoplanet hosts
exo = json.load(open('exo_hosts_raw.json'))
exo_t = Table(rows=[[r.get(k) for k in
             ('hostname','ra','dec','sy_dist','st_spectype','st_teff','st_rad',
              'st_mass','sy_vmag','sy_kmag','sy_gaiamag','sy_pnum','pl_name',
              'pl_rade','pl_bmasse','pl_orbsmax','pl_eqt')] for r in exo],
    names=('hostname','ra','dec','sy_dist','st_spectype','st_teff','st_rad',
           'st_mass','sy_vmag','sy_kmag','sy_gaiamag','sy_pnum','pl_name',
           'pl_rade','pl_bmasse','pl_orbsmax','pl_eqt'))
# collapse to one row per host star (keep most-Earth-like planet's params too)
exo_t = exo_t[~exo_t['ra'].mask if hasattr(exo_t['ra'],'mask') else np.ones(len(exo_t),bool)]
print(f"Exoplanet Archive: {len(exo_t)} planet rows -> ", end='')
hosts = {}
for row in exo_t:
    h = row['hostname']
    if h is None or row['ra'] is None:
        continue
    if h not in hosts:
        hosts[h] = dict(row=row, n_planets=0, min_rade=99, has_hz_candidate=False)
    hosts[h]['n_planets'] += 1
    if row['pl_rade'] is not None and row['pl_rade'] < hosts[h]['min_rade']:
        hosts[h]['min_rade'] = row['pl_rade']
exo_hosts = Table(rows=[list(v['row']) + [v['n_planets'], v['min_rade']] for v in hosts.values()],
                   names=exo_t.colnames + ['n_planets_confirmed', 'min_planet_rade'])
print(f"{len(exo_hosts)} unique host stars")
exo_hosts.write('exo_hosts_unique.ecsv', format='ascii.ecsv', overwrite=True)

# --------------------------------------------------------- load Gaia nearby
gaia = Table.read('gaia_nearby50pc.ecsv', format='ascii.ecsv')
gaia['dist_pc'] = 1000.0 / gaia['parallax']
print(f"Gaia nearby: {len(gaia)} stars within 50pc, G<16")

# ------------------------------------------------------------- crossmatch
def xmatch(cat_coord, n_cat, max_sep=5*u.arcmin):
    ia, ib, sep2d, _ = alma_c.search_around_sky(cat_coord, max_sep)
    # astropy's index-return order for SkyCoord.search_around_sky has proven
    # inconsistent with the documented convention in practice; verify
    # empirically which returned array indexes which catalogue rather than
    # trust either the docs or a fixed assumption.
    n_alma = len(alma_c)
    ia_fits_alma = (ia.max() < n_alma) if len(ia) else True
    ia_fits_cat  = (ia.max() < n_cat)  if len(ia) else True
    ib_fits_alma = (ib.max() < n_alma) if len(ib) else True
    ib_fits_cat  = (ib.max() < n_cat)  if len(ib) else True
    if ia_fits_alma and ib_fits_cat and not (ia_fits_cat and not ia_fits_alma):
        idx_alma, idx_cat = ia, ib
    elif ib_fits_alma and ia_fits_cat:
        idx_alma, idx_cat = ib, ia
    else:
        raise RuntimeError(f'cannot disambiguate index order: n_alma={n_alma} '
                            f'n_cat={n_cat} ia.max={ia.max() if len(ia) else None} '
                            f'ib.max={ib.max() if len(ib) else None}')
    print(f'  [xmatch] resolved index order: idx_alma from '
          f'{"1st" if idx_alma is ia else "2nd"} return value')
    return idx_cat, idx_alma, sep2d

print("\ncrossmatching exoplanet hosts against ALMA pointings...")
exo_c = SkyCoord(exo_hosts['ra']*u.deg, exo_hosts['dec']*u.deg)
i_cat, i_alma, sep = xmatch(exo_c, len(exo_hosts))
# keep only matches within the ACTUAL per-pointing FoV/2
fov_arcsec = alma['s_fov'][i_alma] * 3600.0
keep = sep.arcsec <= (fov_arcsec / 2.0)
print(f"  {keep.sum()} raw matches within actual FoV (of {len(i_cat)} candidates in 5' box)")
exo_matches = Table()
exo_matches['host_idx'] = i_cat[keep]
exo_matches['alma_idx'] = i_alma[keep]
exo_matches['sep_arcsec'] = sep.arcsec[keep]
exo_matches.write('exo_alma_matches.ecsv', format='ascii.ecsv', overwrite=True)
print(f"  unique host stars with ALMA data: {len(set(exo_matches['host_idx']))}")

print("\ncrossmatching nearby Gaia stars against ALMA pointings...")
gaia_c = SkyCoord(gaia['ra'], gaia['dec'])
i_cat, i_alma, sep = xmatch(gaia_c, len(gaia))
fov_arcsec = alma['s_fov'][i_alma] * 3600.0
keep = sep.arcsec <= (fov_arcsec / 2.0)
print(f"  {keep.sum()} raw matches within actual FoV (of {len(i_cat)} candidates in 5' box)")
gaia_matches = Table()
gaia_matches['star_idx'] = i_cat[keep]
gaia_matches['alma_idx'] = i_alma[keep]
gaia_matches['sep_arcsec'] = sep.arcsec[keep]
gaia_matches.write('gaia_alma_matches.ecsv', format='ascii.ecsv', overwrite=True)
print(f"  unique nearby stars with ALMA data: {len(set(gaia_matches['star_idx']))}")
