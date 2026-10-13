"""Freeze the bright-star gap into one record the paper's generator reads.

Inputs, all produced in this directory by live queries and kept beside it:
  hip2_plx25.ecsv        Hipparcos-2 (van Leeuwen 2007) stars with plx > 25 mas
  vizier_gdr3_plx20.ecsv Gaia DR3 sources with plx > 20 mas
  hip_no_dr3.ecsv        the unmatched subset (produced here, recomputed)
  bright257.json         the ALMA ObsCore probe of every unmatched star
  ebcost257.json         execution blocks and raw volumes of the covered ones
  names_r17.json         SIMBAD main identifiers and spectral types

Output: brightgap_r17.json -- counts by magnitude, the covered stars with their
window, block and volume content, and the Sirius geometry.
"""
import collections
import json
import warnings

warnings.filterwarnings('ignore')
import numpy as np
from astropy.table import Table
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

PLX_MIN = 25.0        # the survey's own parallax floor, mas
PLX_FRAC = 0.20       # the survey's own fractional-precision cut
MATCH_TOL = 3.0       # arcsec, Hipparcos propagated to J2016 against Gaia DR3
CLASS_A_MAX_HZ = 2.0e6  # fine/coarse boundary on the CHANNEL SEPARATION
# The ALMA archive's frequency_support quotes an EFFECTIVE resolution, not a
# channel separation.  Measured against this survey's own 252 fine-channel
# execution blocks, the ratio is exactly 2 for un-averaged spectra and 1.156
# for online channel-averaged ones, and no other value occurs.
ARCH_RES_RATIOS = (2.0, 1.156)
LADDER = [15258.789 * 2 ** k for k in range(12)] + [31.25e6, 62.5e6]

# ----------------------------------------------------------------- the volume
H = Table.read('hip2_plx25.ecsv')
H = H[(np.array(H['e_Plx']) / np.array(H['Plx'])) <= PLX_FRAC]
assert np.all(np.array(H['Plx']) > PLX_MIN)
G = Table.read('vizier_gdr3_plx20.ecsv')

ch = SkyCoord(np.array(H['RArad']) * u.deg, np.array(H['DErad']) * u.deg,
              pm_ra_cosdec=np.array(H['pmRA']) * u.mas / u.yr,
              pm_dec=np.array(H['pmDE']) * u.mas / u.yr,
              distance=(1000.0 / np.array(H['Plx'])) * u.pc,
              obstime=Time(1991.25, format='jyear')).apply_space_motion(
                  new_obstime=Time(2016.0, format='jyear'))
cg = SkyCoord(np.array(G['RA_ICRS']) * u.deg, np.array(G['DE_ICRS']) * u.deg)
_, sep, _ = ch.match_to_catalog_sky(cg)
missing = np.where(sep.arcsec > MATCH_TOL)[0]

hp_all = np.array(H['Hpmag'])
hp_mis = hp_all[missing]
BINS = [(-2, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 10), (10, 20)]
bincount = [dict(lo=lo, hi=hi,
                 n_volume=int(((hp_all >= lo) & (hp_all < hi)).sum()),
                 n_missing=int(((hp_mis >= lo) & (hp_mis < hi)).sum()))
            for lo, hi in BINS]
assert sum(b['n_volume'] for b in bincount) == len(H)
assert sum(b['n_missing'] for b in bincount) == len(missing)

# the faint floor: everything from fourth magnitude down, pooled
_faint = [b for b in bincount if b['lo'] >= 4]
faint_pct = round(100.0 * sum(b['n_missing'] for b in _faint)
                  / sum(b['n_volume'] for b in _faint), 1)

# the colour of what the catalogue requirement removes.  Table 2 splits A from
# F at BP-RP 0.36; the Hipparcos table carries B-V, where the same boundary is
# about 0.30, so this is the count of stars at least as blue as an A star.
BV_A = 0.30
bv_all = np.array(H['B-V'], dtype=float)
bv_mis = bv_all[missing]
colour = dict(bv_cut=BV_A,
              n_early_volume=int((bv_all < BV_A).sum()),
              n_early_missing=int((bv_mis < BV_A).sum()))
colour['early_pct'] = round(100.0 * colour['n_early_missing']
                            / colour['n_early_volume'], 1)
colour['other_pct'] = round(100.0 * (len(missing) - colour['n_early_missing'])
                            / (len(H) - colour['n_early_volume']), 1)
assert np.all(np.isfinite(bv_all)), 'a star with no colour would bias the ratio'

# ----------------------------------------------- the archive probe, per star
def chan_sep(arch_hz):
    """Recover the channel separation from the archive's effective resolution."""
    best, berr = None, 1e99
    for ratio in ARCH_RES_RATIOS:
        v = arch_hz / ratio
        err = min(abs(v / L - 1.0) for L in LADDER)
        if err < berr:
            best, berr = v, err
    assert berr < 0.02, (arch_hz, best, berr)
    return best


probe = json.load(open('bright257.json'))
cost = json.load(open('ebcost257.json'))
names = json.load(open('names_r17.json'))

hits = collections.defaultdict(list)
for r in probe:
    if r['inside_fov'] and r['pb_pass']:
        hits[str(r['hip'])].append(r)

# the survey's own searched execution blocks, read from the released catalogue
import csv
SEARCHED = {row['eb'] for row in
            csv.DictReader(open('../../paper_20pc/v4.18/per_target_results_v3.99.csv'))}

stars = []
for hip, rr in hits.items():
    ebs = cost[hip]
    nA = nB = 0
    for m, lst in collections.defaultdict(
            list, {k: [x for x in rr if x['mous'] == k]
                   for k in {x['mous'] for x in rr}}).items():
        n_eb = sum(1 for e, v in ebs.items() if v['mous'] == m) or 1
        for (lo, hi, w) in {(x['flo_ghz'], x['fhi_ghz'], x['chanw_hz']) for x in lst}:
            if chan_sep(w) <= CLASS_A_MAX_HZ:
                nA += n_eb
            else:
                nB += n_eb
    stars.append(dict(
        hip=int(hip), name=names[hip]['name'], sp_type=names[hip]['sp_type'],
        v_mag=names[hip]['v'], hp_mag=rr[0]['hp'],
        plx_hip=float(H['Plx'][np.array(H['HIP']) == int(hip)][0]),
        dist_pc=round(1000.0 / float(H['Plx'][np.array(H['HIP']) == int(hip)][0]), 2),
        n_mous=len({x['mous'] for x in rr}), n_eb=len(ebs),
        n_win_a=nA, n_win_b=nB,
        raw_gb=round(sum(v['size_gb'] for v in ebs.values()), 1),
        bands=sorted({x['band'] for x in rr}),
        projects=sorted({x['proj'] for x in rr}),
        eb_already_searched=sorted(e for e in ebs if e in SEARCHED),
        sep_min_arcsec=round(min(x['sep_arcsec'] for x in rr), 2),
        sep_max_arcsec=round(max(x['sep_arcsec'] for x in rr), 2),
        pb_min=round(min(x['pb_resp'] for x in rr), 3)))
stars.sort(key=lambda s: s['v_mag'])

# ------------------------------------------- the Sirius geometry, from our own
# primary-beam catalogue: where the search put Sirius B in the same blocks
pbcat = json.load(open('../../paper_20pc/v4.18/pbcat_v408.json'))
sir_b = [w for k, v in pbcat.items() if k.startswith('alf CMa B|') for w in v]
sirius = dict(
    n_eb=len([s for s in stars if s['hip'] == 32349][0]['eb_already_searched']),
    a_sep_min=[s for s in stars if s['hip'] == 32349][0]['sep_min_arcsec'],
    a_sep_max=[s for s in stars if s['hip'] == 32349][0]['sep_max_arcsec'],
    b_off_min=round(min(w['pb_offset_arcsec'] for w in sir_b), 2),
    b_off_max=round(max(w['pb_offset_arcsec'] for w in sir_b), 2),
    b_pb_min=round(min(w['pb_atten'] for w in sir_b), 3),
    b_pb_max=round(max(w['pb_atten'] for w in sir_b), 3),
    b_n_win=len(sir_b))

# ------------------------------------------------------------------- totals
all_eb = {}
for hip in hits:
    for e, v in cost[hip].items():
        all_eb[e] = v['size_gb']
rec = dict(
    plx_min_mas=PLX_MIN, plx_frac=PLX_FRAC, match_tol_arcsec=MATCH_TOL,
    n_volume=int(len(H)), n_missing=int(len(missing)), bins=bincount,
    faint_pct=faint_pct, colour=colour,
    n_covered=len(stars), stars=stars, sirius=sirius,
    tot_eb=len(all_eb), tot_raw_gb=round(sum(all_eb.values()), 1),
    tot_win_a=sum(s['n_win_a'] for s in stars),
    tot_win_b=sum(s['n_win_b'] for s in stars),
    n_a_type=sum(1 for s in stars if s['sp_type'].strip().upper().startswith('A')),
    n_class_a_star=sum(1 for s in stars if s['n_win_a'] > 0),
    eb_already_searched=sorted(e for e in all_eb if e in SEARCHED))
json.dump(rec, open('brightgap_r17.json', 'w'), indent=1)

print('volume %d   no DR3 parallax %d   with ALMA coverage %d'
      % (rec['n_volume'], rec['n_missing'], rec['n_covered']))
for b in bincount:
    print('  Hp %5.0f-%-5.0f  %5d in volume  %4d missing  %.3f'
          % (b['lo'], b['hi'], b['n_volume'], b['n_missing'],
             b['n_missing'] / b['n_volume']))
for s in stars:
    print('  %-12s %-9s V=%5.2f %6.2f pc  winA=%3d winB=%3d  EB=%2d %7.1f GB  '
          'bands %s  already searched %d'
          % (s['name'], s['sp_type'], s['v_mag'], s['dist_pc'], s['n_win_a'],
             s['n_win_b'], s['n_eb'], s['raw_gb'], s['bands'],
             len(s['eb_already_searched'])))
print('TOTAL  EB=%d  raw=%.1f GB  Class A windows=%d  Class B windows=%d  '
      'A-type stars=%d  stars with fine channels=%d'
      % (rec['tot_eb'], rec['tot_raw_gb'], rec['tot_win_a'], rec['tot_win_b'],
         rec['n_a_type'], rec['n_class_a_star']))
print('sirius:', json.dumps(sirius))
print('faint floor from fourth magnitude down: %.1f per cent' % faint_pct)
print('colour: %d of %d stars bluer than B-V %.2f are missing (%.1f per cent), '
      'against %.1f per cent of the rest'
      % (colour['n_early_missing'], colour['n_early_volume'], colour['bv_cut'],
         colour['early_pct'], colour['other_pct']))
