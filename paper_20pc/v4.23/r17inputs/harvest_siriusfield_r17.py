"""Freeze what this survey's own products already say about the Sirius field.

Reads only products the campaign wrote: the three continuum maps the pipeline
made for `* alf CMa B` and its own continuum summaries.  Measures, for each
block: the delivered phase centre (FITS CRVAL, which equals FIELD::PHASE_DIR),
the catalogue position of each component propagated to the observation epoch,
and the position of the continuum source by a two-dimensional Gaussian fit.

Output: siriusfield_r17.json
"""
import json
import warnings

warnings.filterwarnings('ignore')
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy.table import Table
import astropy.units as u
from scipy.optimize import curve_fit

# component A: Hipparcos-2 (van Leeuwen 2007), the astrometry Gaia DR3 lacks
H = Table.read('hip2_plx25.ecsv')
_r = [x for x in H if int(x['HIP']) == 32349][0]
A = dict(src='Hipparcos-2 HIP 32349', epoch=1991.25, ra=float(_r['RArad']),
         dec=float(_r['DErad']), pmra=float(_r['pmRA']), pmdec=float(_r['pmDE']),
         plx=float(_r['Plx']), eplx=float(_r['e_Plx']))
# component B: the astrometry this survey used, from its own re-extraction plan
B = dict(src='Gaia DR3 2947050466531873024', epoch=2016.0,
         ra=101.28662547305618, dec=-16.72093250564587,
         pmra=-461.571, pmdec=-914.52, plx=374.4896)
BLOCKS = [(3, 'A002_Xc99ad7_X348'), (4, 'A002_Xcc626d_X579'),
          (5, 'A002_Xd0fb35_X90dc')]


def prop(d, obs):
    return SkyCoord(d['ra'] * u.deg, d['dec'] * u.deg,
                    distance=(1000.0 / d['plx']) * u.pc,
                    pm_ra_cosdec=d['pmra'] * u.mas / u.yr,
                    pm_dec=d['pmdec'] * u.mas / u.yr,
                    obstime=Time(d['epoch'], format='jyear')
                    ).apply_space_motion(new_obstime=obs)


def g2(xy, a, x0, y0, sx, sy, b):
    x, y = xy
    return (a * np.exp(-0.5 * (((x - x0) / sx) ** 2
                               + ((y - y0) / sy) ** 2)) + b).ravel()


rows = []
for band, eb in BLOCKS:
    hdu = fits.open('sirius/alf_CMa_B_B%d_continuum.fits' % band)[0]
    hd = hdu.header
    # The field names the PRIMARY in every block -- `Sirius_A` in one and
    # `Sirius` in the other two -- and names the companion in none of them.
    _obj = str(hd['OBJECT']).strip()
    assert _obj.startswith('Sirius') and not _obj.endswith('B'), _obj
    d = np.squeeze(hdu.data)
    w = WCS(hd).celestial
    obs = Time(hd['DATE-OBS'])
    j0, i0 = np.unravel_index(np.nanargmax(d), d.shape)
    R = 8
    sub = d[j0 - R:j0 + R + 1, i0 - R:i0 + R + 1]
    yy, xx = np.mgrid[j0 - R:j0 + R + 1, i0 - R:i0 + R + 1]
    p, _ = curve_fit(g2, (xx, yy), sub.ravel(),
                     p0=[sub.max(), i0, j0, 2.0, 2.0, 0.0])
    cen = w.pixel_to_world(p[1], p[2])
    rms = float(np.nanstd(d[np.abs(d) < 5 * np.nanstd(d)]))
    pc = SkyCoord(hd['CRVAL1'] * u.deg, hd['CRVAL2'] * u.deg)
    cA, cB = prop(A, obs), prop(B, obs)
    rows.append(dict(
        band=band, eb=eb, date_obs=hd['DATE-OBS'][:10], field=_obj,
        bmaj_arcsec=float(hd['BMAJ'] * 3600), bmin_arcsec=float(hd['BMIN'] * 3600),
        peak_mJy=float(p[0] * 1e3), rms_mJy=float(rms * 1e3),
        snr=float(p[0] / rms),
        cen_ra=float(cen.ra.deg), cen_dec=float(cen.dec.deg),
        phase_ra=float(hd['CRVAL1']), phase_dec=float(hd['CRVAL2']),
        catA_to_phase_arcsec=float(cA.separation(pc).arcsec),
        catB_to_phase_arcsec=float(cB.separation(pc).arcsec),
        cen_to_catA_arcsec=float(cen.separation(cA).arcsec),
        cen_to_catB_arcsec=float(cen.separation(cB).arcsec),
        cen_to_phase_arcsec=float(cen.separation(pc).arcsec)))

freq = {3: 100.0, 4: 150.0, 5: 200.0}
alpha = float(np.polyfit([np.log(freq[r['band']]) for r in rows],
                         [np.log(r['peak_mJy']) for r in rows], 1)[0])
cs = [SkyCoord(r['cen_ra'] * u.deg, r['cen_dec'] * u.deg) for r in rows]
scatter = max(cs[i].separation(cs[j]).arcsec
              for i in range(3) for j in range(i + 1, 3))
rec = dict(component_A=A, component_B=B, blocks=rows, alpha=alpha,
           centroid_scatter_arcsec=scatter,
           n_block=len(rows),
           snr_lo=min(r['snr'] for r in rows), snr_hi=max(r['snr'] for r in rows),
           catA_phase_hi=max(r['catA_to_phase_arcsec'] for r in rows),
           catB_phase_lo=min(r['catB_to_phase_arcsec'] for r in rows),
           catB_phase_hi=max(r['catB_to_phase_arcsec'] for r in rows),
           cen_catA_lo=min(r['cen_to_catA_arcsec'] for r in rows),
           cen_catA_hi=max(r['cen_to_catA_arcsec'] for r in rows),
           ab_sep_lo=min(r['cen_to_catB_arcsec'] for r in rows),
           ab_sep_hi=max(r['cen_to_catB_arcsec'] for r in rows),
           beam_lo=min(r['bmin_arcsec'] for r in rows),
           beam_hi=max(r['bmaj_arcsec'] for r in rows))
json.dump(rec, open('siriusfield_r17.json', 'w'), indent=1)
for r in rows:
    print('B%d %-20s %s  peak %6.3f mJy  SNR %5.1f  beam %.2f"x%.2f"  '
          'catA->phase %.3f"  cen->catA %.3f"  cen->catB %.3f"'
          % (r['band'], r['eb'], r['date_obs'], r['peak_mJy'], r['snr'],
             r['bmaj_arcsec'], r['bmin_arcsec'], r['catA_to_phase_arcsec'],
             r['cen_to_catA_arcsec'], r['cen_to_catB_arcsec']))
print('alpha = %.2f   centroid scatter %.3f"   A-B separation %.2f-%.2f"'
      % (alpha, scatter, rec['ab_sep_lo'], rec['ab_sep_hi']))
