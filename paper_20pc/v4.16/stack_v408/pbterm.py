#!/usr/bin/env python3
"""PRIMARY-BEAM ATTENUATION FOR THE MULTI-EPOCH STACK (D29 item 1).

The stored `*_srcspec.npz` spectra are in APPARENT flux: the visibilities are
never primary-beam corrected, so a source at the star appears at A x its true
flux, where A is the primary-beam response at the star's offset from the phase
centre.  The drift search corrects for this exactly once, in S_min; the D15/D17
stack did not correct for it at all, so every stacked limit for an off-axis star
was optimistic by 1/A.

What this module fixes, and how:

  * the offset is recomputed from the extraction's OWN geometry, stored in the
    product (`phase_ra`, `phase_dec`, `t1_ra`, `t1_dec`), by EXACT haversine.
    The pipeline's own `hypot(l_star, m_star)` small-angle value is checked
    against it but not trusted (it is wrong by 0.003" at 8").
  * the response is the CASA/ALMA BLOCKED-AIRY pattern (12 m: D_eff 10.7 m,
    blockage 0.75 m; 7 m: 6.25/0.75), which reproduces ALMA's quoted
    FWHM ~= 1.13 lam/D (measured 1.15 here).  The pipeline's Gaussian at
    1.22 lam/D is 6 per cent too wide; see PB_OFFSET_AUDIT.md section 3.
  * the dish is derived from the product's own `pb_arcsec` (= 1.22 lam/D) and
    must round to 12 m or 7 m, else this raises.

Where the correction is applied, and why there:

  A source at the star gives apparent flux A_e * S in epoch e.  Dividing each
  epoch's spectrum by A_e and weighting by 1/(sigma_e/A_e)^2 = A_e^2/sigma_e^2
  is exactly the matched filter for a source at the star:
      sum_e (x_e/A_e) * A_e^2/sigma_e^2  =  sum_e x_e A_e / sigma_e^2 .
  So the division is not cosmetic: it also REWEIGHTS the epochs, downweighting
  epochs in which the star was badly attenuated.  Where A is the same in every
  epoch of a group the weights are unchanged and A cancels out of every gain
  ratio identically; where A differs between epochs the gains legitimately move.

  The SAME scalar A_e is applied to the star row and to all eight control rows,
  so star and controls carry identical processing (D15 item 3).  The control
  positions' own, much larger, offsets are deliberately NOT used: the ring is
  centred on the star and reaches 0.78 x FWHM, no flux read there means
  anything (PB_OFFSET_AUDIT.md section 2), and using them would give the nine
  positions nine different epoch weightings.

A is a scalar evaluated at the window's median frequency, matching the drift
search.  `spread` reports A(f_lo)/A(f_hi) so the intra-window gradient that
this ignores is measured rather than assumed.

MODEL='none' reproduces the pre-fix stack exactly and exists so the fix can be
driven in both directions.
"""
import math
import numpy as np
from scipy.special import j1

AS = math.pi / 180.0 / 3600.0
C_M_S = 299792458.0
MODEL = 'casa'                  # 'casa' | 'gauss' | 'none'
DISHES = (12.0, 7.0)
DISH_TOL = 0.12                 # m, on 1.22 lam/D back-solved from pb_arcsec
BLOCKED = {12.0: (10.7, 0.75), 7.0: (6.25, 0.75)}


def sep_arcsec(ra0, dec0, ra1, dec1):
    """Exact angular separation, radians in, arcsec out (haversine)."""
    s = (math.sin((dec1 - dec0) / 2) ** 2
         + math.cos(dec0) * math.cos(dec1) * math.sin((ra1 - ra0) / 2) ** 2)
    return 2.0 * math.asin(min(1.0, math.sqrt(s))) / AS


def gauss(theta, fwhm):
    return math.exp(-4.0 * math.log(2.0) * (theta / fwhm) ** 2)


def airy_blocked(theta, lam, dish):
    """CASA/ALMA blocked-aperture Airy power pattern."""
    de, blk = BLOCKED[dish]
    eps = blk / de
    x = math.pi * de * theta * AS / lam
    if x < 1e-9:
        return 1.0
    v = (2 * j1(x) / x - eps * eps * 2 * j1(eps * x) / (eps * x)) / (1 - eps * eps)
    return float(v * v)


def dish_from_pb(pb_arcsec, lam):
    """The pipeline stores pb_arcsec = 1.22 lam/D.  Recover D; it must be 12 or 7."""
    d = 1.22 * lam / (pb_arcsec * AS)
    for cand in DISHES:
        if abs(d - cand) <= DISH_TOL:
            return cand, d
    raise ValueError('pb_arcsec %.3f" at lam %.5f mm implies D = %.3f m, '
                     'neither 12 nor 7' % (pb_arcsec, lam * 1e3, d))


def geometry(d, model=None):
    """Primary-beam geometry and response for one *_srcspec.npz (already loaded).

    Returns dict(offset_arcsec, pb_fwhm_arcsec, dish_m, freq_med_Hz,
                 A, A_gauss, A_casa, spread, offset_lm_arcsec, model).
    """
    model = MODEL if model is None else model
    need = ('phase_ra', 'phase_dec', 't1_ra', 't1_dec', 'pb_arcsec', 'freqs')
    miss = [k for k in need if k not in d.files]
    if miss:
        raise KeyError('product carries no primary-beam geometry: missing %s' % miss)
    f = np.asarray(d['freqs'], float)
    fmed = float(np.median(f))
    lam = C_M_S / fmed
    pb = float(d['pb_arcsec'])
    dish, draw = dish_from_pb(pb, lam)
    off = sep_arcsec(float(d['phase_ra']), float(d['phase_dec']),
                     math.radians(float(d['t1_ra'])), math.radians(float(d['t1_dec'])))
    off_lm = math.hypot(float(d['l_star']), float(d['m_star'])) / AS \
        if 'l_star' in d.files else float('nan')
    a_g = gauss(off, pb)
    a_c = airy_blocked(off, lam, dish)
    A = {'casa': a_c, 'gauss': a_g, 'none': 1.0}[model]
    # intra-window gradient that a scalar A ignores: A at the band edges
    lo, hi = float(f.min()), float(f.max())
    if model == 'none':
        spread = 1.0
    elif model == 'gauss':
        spread = gauss(off, pb * fmed / lo) / max(gauss(off, pb * fmed / hi), 1e-300)
    else:
        spread = airy_blocked(off, C_M_S / lo, dish) \
            / max(airy_blocked(off, C_M_S / hi, dish), 1e-300)
    return dict(offset_arcsec=off, offset_lm_arcsec=off_lm, pb_fwhm_arcsec=pb,
                dish_m=dish, dish_raw_m=draw, freq_med_Hz=fmed,
                A=A, A_gauss=a_g, A_casa=a_c, spread=spread, model=model)


if __name__ == '__main__':
    # self-checks, driven in both directions
    lam = C_M_S / 230.538e9
    for dish in (12.0, 7.0):
        pb = 1.22 * lam / (dish * AS)
        lo, hi = 0.0, 90.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if airy_blocked(mid, lam, dish) > 0.5:
                lo = mid
            else:
                hi = mid
        fw = 2 * lo
        print('%2.0f m @230.538 GHz: blocked-Airy FWHM %.3f" = %.4f lam/D ; '
              'pipeline 1.22 lam/D = %.3f"' % (dish, fw, fw * AS * dish / lam, pb))
        assert 1.10 < fw * AS * dish / lam < 1.20
        assert abs(dish_from_pb(pb, lam)[0] - dish) < 1e-9
    try:
        dish_from_pb(1.22 * lam / (9.0 * AS), lam)
        raise SystemExit('FAIL: dish_from_pb accepted a 9 m dish')
    except ValueError:
        print('dish_from_pb rejects a 9 m dish: ok')
    assert abs(gauss(0.0, 18.0) - 1.0) < 1e-15 and abs(airy_blocked(0.0, lam, 12.0) - 1.0) < 1e-15
    # exact vs small angle
    print('haversine at 8": %.6f"' % sep_arcsec(0.0, 0.0, 8 * AS, 0.0))
    print('A(5.21",B7 18.2") gauss %.4f  airy %.4f' % (
        gauss(5.21, 18.2), airy_blocked(5.21, C_M_S / 347.9e9, 12.0)))
    print('pbterm selftests ok')
