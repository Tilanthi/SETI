#!/usr/bin/env python3
"""
Ranking algorithm for ALMA-archive technosignature follow-up targets.

Combines three candidate-discovery pathways, all requiring confirmed public
ALMA calibrated (MOUS-level) archival coverage:
  1. Nearby stars (<50 pc, Gaia DR3) whose position falls inside the primary
     beam of an ALMA pointing.
  2. Confirmed exoplanet host stars (NASA Exoplanet Archive) similarly
     matched to ALMA coverage.
  3. Known circumstellar-disk hosts, identified directly from ALMA's own
     science_keyword/scientific_category metadata (these ARE the ALMA
     target, not a positional match), extending beyond the 50 pc cut to
     capture well-known but more distant disk systems (e.g. TW Hya, HR 8799).

HARD GATE: a star without a measured Gaia proper motion is excluded from
the ranked list. This was specifically requested: without a measured proper
motion, the star's position at the ALMA observation epoch (often years to a
decade+ after the Gaia reference epoch) cannot be reliably computed, and a
fast-moving nearby star can be offset by a significant fraction of an
arcsecond to several arcseconds -- exactly the effect that had to be
corrected for TRAPPIST-1 itself (0.22" offset) in the original search.

Score = 0.30*dist + 0.10*bright + 0.20*startype + 0.15*disk + 0.15*exo
        + 0.05*pm_quality + 0.05*alma_dataquality
(weights sum to 1.0; documented per-component below)
"""
import json
import numpy as np

stars = json.load(open('/workspace/SETI/stars_deduped.json'))
print(f"Loaded {len(stars)} unique candidate stars with confirmed ALMA coverage")

# ------------------------------------------------------------ PM hard gate
before = len(stars)
stars = [s for s in stars if s['pmra'] is not None and s['pmdec'] is not None
         and np.isfinite(s['pmra']) and np.isfinite(s['pmdec'])]
print(f"Proper-motion gate: {before} -> {len(stars)} (excluded {before-len(stars)} "
      f"without a measured Gaia proper motion)")

dist = np.array([s['dist_pc'] for s in stars], dtype=float)
gmag = np.array([s['gmag'] for s in stars], dtype=float)
teff = np.array([s['teff'] if s['teff'] is not None else np.nan for s in stars], dtype=float)
pmra = np.array([s['pmra'] for s in stars], dtype=float)
pmdec = np.array([s['pmdec'] for s in stars], dtype=float)
pmra_err = np.array([s['pmra_err'] if s['pmra_err'] is not None else np.nan for s in stars], dtype=float)
pmdec_err = np.array([s['pmdec_err'] if s['pmdec_err'] is not None else np.nan for s in stars], dtype=float)
is_disk = np.array([bool(s['is_disk_host']) for s in stars])
is_exo = np.array([bool(s['is_exo_host']) for s in stars])
n_planets = np.array([s['n_planets'] for s in stars], dtype=float)
min_rade = np.array([s['min_planet_rade'] if s['min_planet_rade'] is not None else np.nan for s in stars])
specres = np.array([s['alma_best_specres_Hz'] if s['alma_best_specres_Hz'] is not None else np.nan for s in stars])
texp_h = np.array([s['alma_total_texp_h'] for s in stars], dtype=float)
n_mous = np.array([s['alma_n_mous'] for s in stars], dtype=float)

# handle missing distances/mags with a neutral (worst-quartile) fallback so
# they don't crash ranking, but are not spuriously favoured
dist_fill = np.nanpercentile(dist, 75)
dist = np.where(np.isfinite(dist) & (dist > 0), dist, dist_fill)
gmag_fill = np.nanpercentile(gmag, 75)
gmag = np.where(np.isfinite(gmag), gmag, gmag_fill)


def minmax(x, invert=False):
    x = np.asarray(x, dtype=float)
    lo, hi = np.nanmin(x), np.nanmax(x)
    if hi <= lo:
        return np.zeros_like(x)
    s = (x - lo) / (hi - lo)
    return 1 - s if invert else s


# 1. Distance: closer is better. This is the score most directly tied to
#    achievable sensitivity (EIRP_min ~ d^2 for fixed flux sensitivity), so
#    we rank on log10(distance) to keep the whole 1.3-50 pc range usefully
#    spread rather than let the very nearest star swamp everything at d^2.
score_dist = minmax(np.log10(dist), invert=True)

# 2. Brightness: brighter (lower Gmag) is better -- easier to pin down
#    astrometry/ephemeris and a marker of the nearest, best-characterised
#    systems.
score_bright = minmax(gmag, invert=True)

# 3. Stellar type desirability: M dwarfs (potential cool/compact planetary
#    systems, per TRAPPIST-1) and G-type Sun-like stars (classic "Earth-like
#    star" habitable-zone hosts) both score highly; K dwarfs (long-lived,
#    increasingly favoured SETI targets) score partial credit; hot
#    early-type stars score low (short main-sequence lifetime, poor
#    habitability case).
def startype_score(t):
    if not np.isfinite(t):
        return 0.3          # unknown type: neutral-low, not penalised to zero
    if t < 3900:
        return 1.0          # M dwarf
    if 5200 <= t <= 6000:
        return 1.0          # G-type, Sun-like
    if 3900 <= t < 5200:
        return 0.7          # K dwarf
    if 6000 < t <= 7500:
        return 0.3          # F-type, shorter-lived
    return 0.1               # A/B/O or white dwarf/evolved, deprioritised
score_startype = np.array([startype_score(t) for t in teff])
is_mdwarf = teff < 3900
is_sunlike = (teff >= 5200) & (teff <= 6000)

# 4. Disk host: binary bonus (debris or protoplanetary disk = confirmed
#    ongoing/completed planet formation, and the best-characterised ALMA
#    data in the archive).
score_disk = is_disk.astype(float)

# 5. Exoplanet host: scaled by number of confirmed planets (diminishing
#    returns) with an extra bonus if any known planet is Earth-sized
#    (R < 2 R_earth, i.e. plausibly rocky).
score_exo = np.where(is_exo, np.minimum(1.0, 0.4 + 0.15 * n_planets), 0.0)
earthlike_bonus = np.where(is_exo & np.isfinite(min_rade) & (min_rade < 2.0), 0.2, 0.0)
score_exo = np.minimum(1.0, score_exo + earthlike_bonus)

# 6. Proper-motion quality: how reliably the ALMA-epoch position can be
#    astrometrically corrected. Total PM signal-to-noise ratio, capped.
pm_tot = np.hypot(pmra, pmdec)
pm_err = np.hypot(np.nan_to_num(pmra_err, nan=0), np.nan_to_num(pmdec_err, nan=0))
with np.errstate(divide='ignore', invalid='ignore'):
    pm_snr = np.where(pm_err > 0, pm_tot / pm_err, 100.0)  # no reported error -> assume fine (Gaia default)
score_pmq = minmax(np.clip(pm_snr, 0, 200))

# 7. ALMA data quality: fine spectral resolution strongly preferred (a
#    genuinely narrowband search needs it -- coarse channels, as found for
#    Bands 3/6 on TRAPPIST-1, degrade EIRP_min by orders of magnitude and
#    make the drift search largely moot); more total integration time and
#    more independent visits (epochs) both help.
specres_fill = np.nanpercentile(specres, 75)
specres_f = np.where(np.isfinite(specres) & (specres > 0), specres, specres_fill)
score_specres = minmax(np.log10(specres_f), invert=True)
score_texp = minmax(np.log1p(texp_h))
score_nmous = minmax(np.log1p(n_mous))
score_dataq = 0.6 * score_specres + 0.25 * score_texp + 0.15 * score_nmous

W = dict(dist=0.30, bright=0.10, startype=0.20, disk=0.15, exo=0.15, pmq=0.05, dataq=0.05)
total = (W['dist'] * score_dist + W['bright'] * score_bright +
         W['startype'] * score_startype + W['disk'] * score_disk +
         W['exo'] * score_exo + W['pmq'] * score_pmq + W['dataq'] * score_dataq)

for i, s in enumerate(stars):
    s.update(
        score_dist=float(score_dist[i]), score_bright=float(score_bright[i]),
        score_startype=float(score_startype[i]), score_disk=float(score_disk[i]),
        score_exo=float(score_exo[i]), score_pmq=float(score_pmq[i]),
        score_dataq=float(score_dataq[i]), score_total=float(total[i]),
        is_mdwarf=bool(is_mdwarf[i]), is_sunlike=bool(is_sunlike[i]),
        pm_total_masyr=float(pm_tot[i]), pm_snr=float(pm_snr[i]),
    )

ranked = sorted(stars, key=lambda s: -s['score_total'])
json.dump(ranked, open('/workspace/SETI/ranked_all.json', 'w'), indent=1)

top100 = ranked[:100]
json.dump(top100, open('/workspace/SETI/ranked_top100.json', 'w'), indent=1)

# -------------------------------------------------------------- CSV output
import csv
cols = ['rank', 'name', 'ra', 'dec', 'dist_pc', 'gmag', 'teff', 'is_mdwarf',
        'is_sunlike', 'is_disk_host', 'is_exo_host', 'n_planets',
        'min_planet_rade', 'pmra', 'pmdec', 'pm_total_masyr', 'pm_snr',
        'alma_bands', 'alma_best_specres_Hz', 'alma_total_texp_h',
        'alma_n_mous', 'alma_best_target', 'score_total', 'score_dist',
        'score_bright', 'score_startype', 'score_disk', 'score_exo',
        'score_pmq', 'score_dataq']
with open('/workspace/SETI/ranked_top100.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(cols)
    for i, s in enumerate(top100):
        w.writerow([i + 1] + [s.get(c) for c in cols[1:]])

print(f"\nTop 15 targets:")
print(f"{'#':>3} {'Name':<32}{'dist(pc)':>9}{'Gmag':>7}{'Teff':>7} {'M':>2}{'Sun':>4}"
      f"{'Disk':>5}{'Exo':>4} {'Score':>7}")
for i, s in enumerate(top100[:15]):
    print(f"{i+1:>3} {s['name']:<32}{s['dist_pc']:>9.2f}{s['gmag']:>7.2f}"
          f"{(s['teff'] or 0):>7.0f} {'Y' if s['is_mdwarf'] else '':>2}"
          f"{'Y' if s['is_sunlike'] else '':>4}{'Y' if s['is_disk_host'] else '':>5}"
          f"{'Y' if s['is_exo_host'] else '':>4} {s['score_total']:>7.3f}")

print(f"\nSaved: ranked_top100.csv, ranked_top100.json, ranked_all.json ({len(ranked)} total)")
print(f"Category counts in top 100: M dwarfs = {sum(s['is_mdwarf'] for s in top100)}, "
      f"Sun-like = {sum(s['is_sunlike'] for s in top100)}, "
      f"Disk hosts = {sum(s['is_disk_host'] for s in top100)}, "
      f"Exoplanet hosts = {sum(s['is_exo_host'] for s in top100)}")
