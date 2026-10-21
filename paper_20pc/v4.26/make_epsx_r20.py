#!/usr/bin/env python3
r"""The annual-parallax displacement on epsilon Eridani's own blocks.

★ NOT PART OF THE BUILD, by the same convention as `make_abary_v417.py`: it
requires astropy, so it is run once and its product frozen in
`r20inputs/epsx_r20.json`, which `beam_r17.py` reads.

WHY IT IS NEEDED.  Every window of the census has its annual-parallax
retention divided out of its limit except thirteen, and twelve of those are
epsilon Eridani's -- the nearest Class A star, the largest parallax in the
sample, and one of the ten deepest limits.  The host harvest that measured
the displacement for the other 404 blocks never covered these three: the band
was restored to the census later, from a different route, and
`window_geometry_r11.json` holds 1655 of the catalogue's 1663 rows and misses
exactly those twelve.  So the displacement is computed here from the Gaia DR3
astrometry the sample selection itself used, and the retention is NOT
modelled: the paper's own injection measurement at 0.25 of a synthesised beam
bounds it, because this displacement is smaller than that.

THE COMPUTATION, AND THE EVIDENCE THAT IT IS THE SAME ONE.  The apparent
position differs from the barycentric one by

    Delta(alpha*) = plx (X sin a - Y cos a)
    Delta(delta)  = plx (X cos a sin d + Y sin a sin d - Z cos d)

with (X, Y, Z) the Earth's barycentric position in au at the block's epoch.
Run over the 588 harvested windows whose star has a coordinate in the frozen
SIMBAD harvest, this reproduces the harvest's own recorded displacement to a
median 4e-5 in relative terms and 0.9 per cent at worst -- on a 14 mas
displacement, where the recorded value is rounded.  That agreement is the
only evidence that this is the harvest's computation and not a second one, so
it is written into the product and asserted in the build.

    python3 make_epsx_r20.py            # writes r20inputs/epsx_r20.json
"""
import csv
import json
import math
import os
import statistics as st
import sys

from astropy.coordinates import get_body_barycentric
from astropy.time import Time

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, 'r20inputs')
OUT = os.path.join(OUTDIR, 'epsx_r20.json')

#: the star this file is about, and the SIMBAD identifier it is keyed on in
#: the frozen parallax harvest the sample selection used
STAR = 'eps Eri'
SIMBAD_ID = '* eps Eri'


def displacement(ra_deg, dec_deg, plx_mas, mjd):
    """|apparent - barycentric| position in arcsec, and its two components."""
    p = get_body_barycentric('earth', Time(float(mjd), format='mjd',
                                           scale='utc'))
    X, Y, Z = p.x.to_value('AU'), p.y.to_value('AU'), p.z.to_value('AU')
    a, d = math.radians(ra_deg), math.radians(dec_deg)
    da = plx_mas * (X * math.sin(a) - Y * math.cos(a))
    dd = plx_mas * (X * math.cos(a) * math.sin(d)
                    + Y * math.sin(a) * math.sin(d) - Z * math.cos(d))
    return math.hypot(da, dd) / 1000.0, da / 1000.0, dd / 1000.0


def _norm(n):
    return ' '.join(str(n).replace('*', ' ').replace('V star', ' ')
                    .replace('NAME', ' ').split()).lower()


def main():
    cat = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'))))
    sim = list(csv.DictReader(open(os.path.join(
        HERE, 'r10inputs', 'simbad_plx23_v411.csv'))))
    geom = json.load(open(os.path.join(
        HERE, 'r11inputs', 'window_geometry_r11.json')))['windows']
    mjd = json.load(open(os.path.join(HERE, 'epochs_v386.json')))
    coord = {}
    for r in sim:
        coord.setdefault(_norm(r['main_id']), r)

    # --- 1. the validation, which is the only reason to believe the rest
    dev, n_nocoord = [], 0
    for w in geom:
        c = coord.get(_norm(w['star']))
        if not c or 'dpar' not in w:
            n_nocoord += 1
            continue
        got, _, _ = displacement(float(c['ra']), float(c['dec']),
                                 w['plx_mas'], w['mjd'])
        dev.append(abs(got / w['dpar'] - 1.0))
    dev.sort()
    assert len(dev) > 400 and dev[-1] < 0.01, (len(dev), dev[-1:])

    # --- 2. eps Eri's own blocks
    me = coord[_norm(SIMBAD_ID)]
    rows = [r for r in cat if r['system_id'] == STAR]
    ebs = sorted({r['eb'] for r in rows})
    blocks = {}
    for eb in ebs:
        m = mjd['mjd'][eb]
        tot, da, dd = displacement(float(me['ra']), float(me['dec']),
                                   float(me['plx_value']), m)
        blocks[eb] = dict(mjd=m, mjd_src=mjd.get('source', 'epochs_v386'),
                          dpar_arcsec=tot, dalpha_arcsec=da,
                          ddelta_arcsec=dd,
                          n_windows=sum(1 for r in rows if r['eb'] == eb))
    out = dict(
        generated_by=os.path.basename(__file__),
        star=STAR,
        astrometry=dict(
            source='SIMBAD/Gaia DR3 via r10inputs/simbad_plx23_v411.csv, the '
                   'frozen harvest the sample selection itself used',
            simbad_id=me['main_id'], ra_deg=float(me['ra']),
            dec_deg=float(me['dec']), plx_mas=float(me['plx_value']),
            plx_err_mas=float(me['plx_err']), pmra=float(me['pmra']),
            pmdec=float(me['pmdec'])),
        ephemeris='astropy get_body_barycentric(earth), ICRS cartesian au',
        validation=dict(
            n_windows=len(dev), n_without_coordinate=n_nocoord,
            rel_median=st.median(dev), rel_p90=dev[int(0.9 * len(dev))],
            rel_worst=dev[-1]),
        blocks=blocks)
    os.makedirs(OUTDIR, exist_ok=True)
    json.dump(out, open(OUT, 'w'), indent=1, sort_keys=True)
    print('make_epsx_r20: %s' % OUT)
    print('  validation over %d harvested windows: median %.2g, 90th %.2g, '
          'worst %.2g' % (len(dev), st.median(dev),
                          dev[int(0.9 * len(dev))], dev[-1]))
    for eb, b in sorted(blocks.items()):
        print('  %-20s mjd %.4f  %2d windows  displacement %.4f arcsec '
              '(%.1f per cent of the parallax)'
              % (eb, b['mjd'], b['n_windows'], b['dpar_arcsec'],
                 100 * b['dpar_arcsec'] * 1000 / float(me['plx_value'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
