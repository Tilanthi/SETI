from astroquery.gaia import Gaia
import warnings; warnings.filterwarnings('ignore')

# Nearby stars within 50 pc (parallax > 20 mas), reasonably bright (G<16 for
# usable SNR at ALMA-relevant follow-up), with basic astrophysical params
# (effective temperature for M-dwarf classification) where available.
q = """
SELECT g.source_id, g.ra, g.dec, g.parallax, g.parallax_error, g.pmra, g.pmdec,
       g.phot_g_mean_mag, g.bp_rp, g.radial_velocity,
       ap.teff_gspphot, ap.radius_gspphot
FROM gaiadr3.gaia_source AS g
LEFT OUTER JOIN gaiadr3.astrophysical_parameters AS ap
  ON g.source_id = ap.source_id
WHERE g.parallax > 20 AND g.parallax_over_error > 5
  AND g.phot_g_mean_mag < 16
"""
print("launching job (async, may take a while for full 50pc sample)...")
job = Gaia.launch_job_async(q)
r = job.get_results()
print(len(r), "nearby Gaia sources")
r.write('/workspace/SETI/gaia_nearby50pc.ecsv', format='ascii.ecsv', overwrite=True)
