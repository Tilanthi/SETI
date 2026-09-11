#!/usr/bin/env python3
r"""v3.43 generator: control-ring geometry, repaired line mask, sensitivity
reporting, and the machine-readable catalogue.

Sources (all local to this folder, so the release builds from itself)
--------------------------------------------------------------------
  frozen_export_v3.31.json     the rounds 5-9 freeze, UNCHANGED
  pipeline_peakfreq_v342.json  per-window crossing (peak) frequency, channel,
                               drift and integration count, harvested from the
                               pipeline's own *_result.json products.  Adds no
                               new measurement: every star_peak_snr in it
                               reproduces the frozen export's own value.
  ebmeta_v342.json             sky position and epoch of the four flagged
                               windows' execution blocks, from the retained
                               *_srcspec.npz products, for the frame chain.

What this round exists to do (referee round 12)
-----------------------------------------------
A. Control-ring geometry (referee A2, B-M3).  The geometry was never in the
   frozen products, only in the code.  It is deterministic, so it is
   reconstructed here exactly rather than described:

     seti_extract_generic.py::probe_positions(pb_arcsec, seed=20260825)

   builds the offsets, and the caller adds them to the STAR's own direction
   cosines (lam = l_star + dl), so the construction is concentric with the
   star.  512 control positions are drawn uniform in area between 0.14 and
   0.78 theta_PB and uniform in azimuth from a fixed seed; theta_PB is
   1.22 lambda / 12 m at the window's own median frequency.  Two independent
   checks that this reconstruction is the layout that actually ran:

     (1) the inner check-ring it produces has n_src = 135 positions, which is
         the n_src the manuscript's retired region-max statistic maximised
         over;
     (2) in the two windows filled by extended CO emission, the released
         control statistics fall with the reconstructed radius (Spearman rho
         with p ~ 1e-33 and 1e-12), which a wrong position-to-index mapping
         could not produce.

B. Line mask, repaired and re-applied retrospectively (referee A3, B minor).
   Full-precision rest frequencies, [C I] and H30alpha added, and a separate
   LSR-frame test for Galactic foreground beside the stellar-frame test.

C. Sensitivity reporting (referee A8, A10, B-M2, B-M6): Class A and Class B
   distributions separately, native resolution beside every EIRP, and the
   Hanning-corrected threshold carried alongside the nominal one.

Rules honoured: numbers only via generated macros; macro names letter-only.
"""
import json, math, csv, collections, statistics as st
import numpy as np

C_KMS = 299792.458
C_MS = 299792458.0
DISH = 12.0
ARCSEC = math.pi / (180.0 * 3600.0)

# ---------------------------------------------------------------- prologue --
# identical to survey_stats_round10.py, so GOOD is the same 431 windows
SRC = 'frozen_export_v3.31.json'
D = json.load(open(SRC))
ROWS = D['rows']


def band_of(r):
    if r['band'] is not None:
        return r['band']
    f = 0.5 * (r['flo'] + r['fhi'])
    for lo, hi, b in [(84, 116, 3), (125, 163, 4), (163, 211, 5),
                      (211, 275, 6), (275, 373, 7), (385, 500, 8)]:
        if lo <= f < hi:
            return b


for r in ROWS:
    r['band_x'] = band_of(r)
    r['res_x'] = 'fine' if r['chanw'] < 5e6 else 'coarse'
    r['qa'] = r['rms'] * math.sqrt(r['onsrc'] * r['chanw'])
    r['cmax'] = max(r['ctrl_all']) if r['ctrl_all'] else r['ctrl_max']

_k = lambda r: (r['star_name'], r['eb'], round(min(r['flo'], r['fhi']), 6),
                round(max(r['flo'], r['fhi']), 6), r['chanw'])
_b = {}
for r in ROWS:
    if _k(r) not in _b or (_b[_k(r)]['line'] is None and r['line'] is not None):
        _b[_k(r)] = r
_u = list(_b.values())
_qm = st.median(r['qa'] for r in _u)
GOOD = [r for r in _u
        if r['qa'] >= _qm / 100.0
        and not (r['star_name'] == 'eps Eri' and r['band_x'] == 6)]
assert len(GOOD) == 431, len(GOOD)

PAIRS = [('2MASS J05241914-1601153 551040', '2MASS J05241914-1601153 717696'),
         ('NAME AT Mic AB  Gaia DR3 6792436799475128960', 'V AT Mic B'),
         ('G 272-61A', 'G 272-61B'), ('GJ 2006A', 'GJ 2006B'),
         ('LP 476-207 384128', 'LP 476-207 783296'),
         ('V star TX PsA', 'V star WW PsA'),
         ('HD 139084B 805632', 'HD 139084B 921024')]
_sysof = {}
for a, b in PAIRS:
    _sysof[a] = a
    _sysof[b] = a
sysn = lambda n: _sysof.get(n, n)
NSYS = len({sysn(r['star_name']) for r in GOOD})
assert NSYS == 81, NSYS

MAC = []
M = lambda name, val: MAC.append('\\newcommand{\\%s}{%s}' % (name, val))

# ------------------------------------------------- A. control-ring geometry --
RING_SEED = 20260825
RING_IN, RING_OUT = 0.14, 0.78        # fractions of theta_PB
RING_CHECK = 0.06                     # inner point-source check ring
N_PROBE = 512


def theta_pb(freq_hz):
    """FWHM of one 12 m ALMA dish, arcsec: the pipeline's own Eq. theta_PB =
    1.22 lambda / D.  Verified against the pb_arcsec recorded in the retained
    *_srcspec.npz products (agreement to the printed precision)."""
    return math.degrees(1.22 * (C_MS / freq_hz) / DISH) * 3600.0


def probe_layout(pb_arcsec, seed=RING_SEED):
    """Exact reconstruction of probe_positions(): inner check ring plus the
    512-position control annulus, uniform in area and azimuth."""
    rng = np.random.default_rng(seed)
    n_src = 1
    rmax = RING_CHECK * pb_arcsec
    step = rmax / 7.0
    for r in np.arange(step, rmax + 1e-9, step):
        n_src += max(6, min(24, int(round(2 * np.pi * r / step))))
    lo, hi = RING_IN * pb_arcsec, RING_OUT * pb_arcsec
    rr = np.sqrt(rng.uniform(lo ** 2, hi ** 2, N_PROBE))
    th = rng.uniform(0, 2 * np.pi, N_PROBE)
    return n_src, rr, th


def pb_gain(r, pb):
    """Gaussian primary-beam response at radius r for FWHM pb."""
    return math.exp(-4.0 * math.log(2.0) * (r / pb) ** 2)


for r in GOOD:
    fmid = 0.5 * (r['flo'] + r['fhi']) * 1e9
    r['theta_pb'] = theta_pb(fmid)
    r['r_in'] = RING_IN * r['theta_pb']
    r['r_out'] = RING_OUT * r['theta_pb']

NSRC, _rr0, _th0 = probe_layout(GOOD[0]['theta_pb'])
assert NSRC == 135, NSRC        # check (1): matches the retired statistic's n_src

GAIN_IN = pb_gain(RING_IN, 1.0)
GAIN_OUT = pb_gain(RING_OUT, 1.0)
# area-weighted mean response over the annulus, which is what the 512 draws
# sample: <G> = int_rin^rout G(r) 2 r dr / (rout^2 - rin^2)
_x = np.linspace(RING_IN, RING_OUT, 20001)
GAIN_MEAN = float(np.trapezoid(np.exp(-4 * np.log(2) * _x ** 2) * 2 * _x, _x)
                  / (RING_OUT ** 2 - RING_IN ** 2))

M('RingSeed', '%d' % RING_SEED)
M('RingNProbe', '%d' % N_PROBE)
M('RingNSrc', '%d' % NSRC)
M('RingInFrac', '%.2f' % RING_IN)
M('RingOutFrac', '%.2f' % RING_OUT)
M('RingCheckFrac', '%.2f' % RING_CHECK)
M('RingGainIn', '%.2f' % GAIN_IN)
M('RingGainOut', '%.2f' % GAIN_OUT)
M('RingGainMean', '%.2f' % GAIN_MEAN)
# The annulus is defined in units of the pipeline's own theta_PB = 1.22 lambda/D.
# ALMA's actual 12 m primary-beam FWHM is nearer 1.13 lambda/D, so the physical
# response at a given annulus radius is lower than the definition implies.
PBTRUE = 1.13 / 1.22
M('RingGainInTrue', '%.2f' % pb_gain(RING_IN / PBTRUE, 1.0))
M('RingGainOutTrue', '%.2f' % pb_gain(RING_OUT / PBTRUE, 1.0))
M('RingPbCoef', '%.2f' % 1.13)
M('RingPbCoefCode', '%.2f' % 1.22)
M('RingThetaMin', '%.1f' % min(r['theta_pb'] for r in GOOD))
M('RingThetaMax', '%.1f' % max(r['theta_pb'] for r in GOOD))
M('RingRinMin', '%.1f' % min(r['r_in'] for r in GOOD))
M('RingRinMax', '%.1f' % max(r['r_in'] for r in GOOD))
M('RingRoutMin', '%.1f' % min(r['r_out'] for r in GOOD))
M('RingRoutMax', '%.1f' % max(r['r_out'] for r in GOOD))

# per-band annulus table, at the band's own median searched frequency
BANDROWS = []
for b in sorted({r['band_x'] for r in GOOD}):
    sel = [r for r in GOOD if r['band_x'] == b]
    fmed = st.median(0.5 * (r['flo'] + r['fhi']) for r in sel)
    pb = theta_pb(fmed * 1e9)
    BANDROWS.append((b, fmed, pb, RING_IN * pb, RING_OUT * pb, len(sel)))
with open('tab_ring.tex', 'w') as f:
    f.write('%% GENERATED by v342_calc.py -- do not hand-edit.\n'
            '\\begin{tabular}{@{}crrrrr@{}}\n\\toprule\n'
            'Band & $\\nu_{\\rm med}$ (GHz) & $\\theta_{\\rm PB}$ ($^{\\prime\\prime}$) '
            '& $r_{\\rm in}$ ($^{\\prime\\prime}$) & $r_{\\rm out}$ '
            '($^{\\prime\\prime}$) & windows \\\\\n\\midrule\n')
    f.write(' \\\\\n'.join('%d & %.0f & %.1f & %.1f & %.1f & %d'
                           % (b, fm, pb, ri, ro, n)
                           for b, fm, pb, ri, ro, n in BANDROWS))
    f.write(' \\\\\n\\bottomrule\n\\end{tabular}\n')

# check (2): does the released control-statistic ordering follow the
# reconstructed radii where an extended source fills the beam?
try:
    from scipy.stats import spearmanr
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False

RHO = {}
if _HAVE_SCIPY:
    for tag, star, flo_ in (('CO', 'HD 48370', 230.5004), ('CI', 'HD 48370', 218.56)):
        for r in GOOD:
            if r['star_name'] == star and abs(min(r['flo'], r['fhi']) - flo_) < 0.01:
                _, rr, th = probe_layout(r['theta_pb'])
                rho, p = spearmanr(rr, np.array(r['ctrl_all']))
                RHO[tag] = (rho, p, r)
    # null control: windows with no crossing anywhere should show no trend
    _null = []
    for r in GOOD:
        if r['star_snr'] < 4.0 and r['cmax'] < 5.0:
            _, rr, th = probe_layout(r['theta_pb'])
            _null.append(spearmanr(rr, np.array(r['ctrl_all']))[0])
    RHO['null'] = (float(np.median(_null)), len(_null), None)
    RHO['null_pct'] = (float(np.percentile(_null, 5)),
                       float(np.percentile(_null, 95)))

if 'CO' in RHO:
    M('RingRhoCO', '%.2f' % RHO['CO'][0])
    M('RingRhoCOexp', '%d' % round(math.log10(max(RHO['CO'][1], 1e-300))))
    M('RingRhoNull', '%.3f' % RHO['null'][0])
    M('RingRhoNullN', '%d' % RHO['null'][1])
    _lo, _hi = RHO['null_pct']
    M('RingRhoNullLo', '%.2f' % _lo)
    M('RingRhoNullHi', '%.2f' % _hi)
    # A Spearman rho of magnitude |rho| over N_probe draws corresponds, for a
    # monotone linear trend across the annulus, to a mean control deficit of
    # about |rho| times the ensemble's own dispersion; the 95th percentile
    # bounds it.
    M('RingRhoBoundPct', '%.0f' % (100 * max(abs(_lo), abs(_hi))))

# the HD 48370 13CO peak's angular offset from the star (referee B minor):
# the control carrying that window's ring maximum, located in the
# reconstructed layout.
if 'CI' in RHO:
    r13 = RHO['CI'][2]
    _, rr13, th13 = probe_layout(r13['theta_pb'])
    c13 = np.array(r13['ctrl_all'])
    i13 = int(np.argmax(c13))
    top10 = np.argsort(c13)[::-1][:10]
    M('HdThirteenOffset', '%.1f' % rr13[i13])
    M('HdThirteenOffsetPB', '%.2f' % (rr13[i13] / r13['theta_pb']))
    M('HdThirteenTopLo', '%.1f' % rr13[top10].min())
    M('HdThirteenTopHi', '%.1f' % rr13[top10].max())
    M('HdThirteenRingMed', '%.1f' % float(np.median(rr13)))
    M('HdThirteenRingMax', '%.1f' % c13[i13])
    M('HdThirteenStar', '%.1f' % r13['star_snr'])

# -------------------------------------------------- B. the repaired mask ----
# Full-precision rest frequencies, JPL/CDMS (Pickett et al. 1998; Mueller et
# al. 2005).  The frozen mask stored these rounded to 1 MHz, and carried
# neither [C I] nor a hydrogen recombination line.
CAT = {
    'CO(1-0)':    115.2712018, 'CO(2-1)':   230.5380000, 'CO(3-2)': 345.7959899,
    'CO(4-3)':    461.0407682, 'CO(6-5)':   691.4730763,
    '13CO(2-1)':  220.3986842, 'C18O(2-1)': 219.5603541,
    'HCN(1-0)':    88.6316022, 'HCN(3-2)':  265.8864340,
    'HCO+(1-0)':   89.1885260, 'HCO+(3-2)': 267.5576259,
    'CS(5-4)':    244.9355565, 'CN(1-0)':   113.4909702,
    'SiO(5-4)':   217.1049800, 'H2CO(3-2)': 218.2221920,
    '[CI](1-0)':  492.1606510,                    # new in v3.43
    'H30a':       231.9009280,                    # new in v3.43
}
CAT_OLD = {'CO(1-0)': 115.271, 'CO(2-1)': 230.538, 'CO(3-2)': 345.796,
           'CO(4-3)': 461.041, 'CO(6-5)': 691.473, '13CO(2-1)': 220.399,
           'C18O(2-1)': 219.560, 'HCN(1-0)': 88.632, 'HCN(3-2)': 265.886,
           'HCO+(1-0)': 89.189, 'HCO+(3-2)': 267.558, 'CS(5-4)': 244.936,
           'CN(1-0)': 113.491, 'SiO(5-4)': 217.105, 'H2CO(3-2)': 218.222}
NSPEC_OLD = len({k.split('(')[0] for k in CAT_OLD})
NSPEC_NEW = len({k.split('(')[0].split('3')[0] if k == 'H30a' else k.split('(')[0]
                 for k in CAT})
M('MaskNTransOld', '%d' % len(CAT_OLD))
M('MaskNTransNew', '%d' % len(CAT))
M('MaskNSpecOld', '%d' % NSPEC_OLD)
M('MaskNSpecNew', '%d' % NSPEC_NEW)
M('MaskCIGHz', '%.6f' % CAT['[CI](1-0)'])
M('MaskHthirtyGHz', '%.6f' % CAT['H30a'])
M('MaskVWidth', '50')
# worst rounding error the old mask carried, in km/s
_worst = max(abs(CAT[k] - CAT_OLD[k]) / CAT[k] * C_KMS for k in CAT_OLD)
M('MaskRoundWorstKms', '%.2f' % _worst)

# crossing (peak) frequency per window, from the pipeline's own products
PK = json.load(open('pipeline_peakfreq_v342.json'))


def _norm(s):
    return ' '.join(s.replace('_', ' ').split())

# the pipeline's target directories predate the "gamma Lupi" name-lookup
# correction of the paper's item (iv), so one star is filed under its
# historical identifier there and under the resolved one in the export.
ALIAS = {'g Lup': 'HD 139664'}


PKMAP = {}
for p in PK:
    if p['flo'] is None:
        continue
    star = _norm(p['tgt'].rsplit('_B', 1)[0])
    star = ALIAS.get(star, star)
    PKMAP[(star, p['eb'], round(min(p['flo'], p['fhi']), 4),
           round(max(p['flo'], p['fhi']), 4), round(p['cw'], 1))] = p
_nmatch = 0
for r in GOOD:
    key = (_norm(r['star_name']), r['eb'], round(min(r['flo'], r['fhi']), 4),
           round(max(r['flo'], r['fhi']), 4), round(r['chanw'], 1))
    p = PKMAP.get(key)
    r['f_cross'] = p['pk'] if p else None
    r['n_int'] = p['nint'] if p else None
    if p is not None:
        assert abs(p['snr'] - r['star_snr']) < 0.02, (r['star_name'], p['snr'], r['star_snr'])
        _nmatch += 1
M('PeakFreqMatched', '%d' % _nmatch)

CROSS = [r for r in GOOD if r['star_snr'] >= 5.0]
FLAG = [r for r in CROSS if r['star_snr'] > r['cmax']]
assert len(FLAG) == 4, len(FLAG)


def nearest(fghz, cat):
    """(name, offset in MHz, offset in km/s) of the nearest catalogue entry."""
    best = min(cat.items(), key=lambda kv: abs(fghz - kv[1]))
    dnu = (fghz - best[1]) * 1e3
    return best[0], dnu, C_KMS * (fghz - best[1]) / best[1]


# frame chain for the four flagged windows, from the retained EB metadata
EBM = json.load(open('ebmeta_v342.json'))
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time
import astropy.units as au

ALMA = EarthLocation.of_site('alma') if False else EarthLocation.from_geodetic(
    lon=-67.7538 * au.deg, lat=-23.0292 * au.deg, height=5074 * au.m)

MASKREPORT = []
for r in FLAG:
    key = '%s|%s' % (r['star_name'], r['eb'])
    meta = EBM[key]
    sc = SkyCoord(ra=meta['ra'] * au.deg, dec=meta['dec'] * au.deg)
    t = Time(meta['tmid'] / 86400.0, format='mjd', scale='utc')
    # topocentric -> barycentric: subtract the observer's velocity toward the
    # source (radio convention, first order)
    vbary = sc.radial_velocity_correction(kind='barycentric',
                                          obstime=t, location=ALMA).to(au.km / au.s).value
    # barycentric -> LSR (kinematic, standard solar motion 20 km/s toward
    # 18h00m, +30 deg B1900 = Sun's apex)
    apex = SkyCoord(ra='18h03m50.29s', dec='+30d00m16.8s', frame='icrs')
    vlsr_corr = 20.0 * (math.sin(sc.dec.rad) * math.sin(apex.dec.rad)
                        + math.cos(sc.dec.rad) * math.cos(apex.dec.rad)
                        * math.cos(sc.ra.rad - apex.ra.rad))
    vsys = meta['vsys']
    f = r['f_cross']
    name_new, dnu_new, dv_topo = nearest(f, CAT)
    name_old, dnu_old, dv_old = nearest(f, CAT_OLD)
    # velocity of the emitting frame relative to the transition's rest frame
    dv_bary = dv_topo - vbary
    dv_stellar = (dv_bary + vsys) if vsys is not None else None
    # v_LSR = v_bary + P, where P is the projection of the standard solar
    # motion on the line of sight.  These dv are frequency offsets expressed
    # in velocity units, i.e. the negative of the Doppler velocity (the
    # manuscript's own convention), so the projection enters with a minus.
    dv_lsr = dv_bary - vlsr_corr
    MASKREPORT.append(dict(star=r['star_name'], band=r['band_x'], f=f,
                           new=name_new, dnu_new=dnu_new, dv_topo=dv_topo,
                           old=name_old, dv_old=dv_old,
                           vbary=vbary, vsys=vsys, vlsr=vlsr_corr,
                           dv_stellar=dv_stellar, dv_lsr=dv_lsr,
                           masked_stellar=(abs(dv_stellar) <= 50.0
                                           if dv_stellar is not None
                                           else abs(dv_bary) <= 150.0),
                           masked_lsr=abs(dv_lsr) <= 50.0))

# every crossing window against the repaired catalogue, topocentric
NEWCOINC = []
for r in CROSS:
    if r['f_cross'] is None:
        continue
    nn, dn, dv = nearest(r['f_cross'], CAT)
    no, do, dvo = nearest(r['f_cross'], CAT_OLD)
    if nn != no.replace('H2CO', 'H2CO'):
        NEWCOINC.append((r['star_name'], r['band_x'], r['f_cross'], no, dvo, nn, dv))
M('MaskNewCoinc', '%d' % len(NEWCOINC))
# the Band 8 [C I] crossing, the one entry whose nearest transition moves
if NEWCOINC:
    _b8 = NEWCOINC[0]
    M('CIcrossStar', _b8[0].replace(' ', '~'))
    M('CIcrossGHz', '%.6f' % _b8[2])
    M('CIcrossKms', '%.0f' % _b8[6])
    M('CIcrossOldKms', '%.0f' % _b8[4])

# how much extra unique sky frequency the two new transitions exclude
def _union(ivs):
    iv = sorted(ivs); out = []
    for lo, hi in iv:
        if out and lo <= out[-1][1]:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out
def _sub(base, cut):
    out = []
    for lo, hi in base:
        seg = [(lo, hi)]
        for a, b in cut:
            nxt = []
            for x, y in seg:
                if b <= x or a >= y:
                    nxt.append((x, y)); continue
                if a > x: nxt.append((x, min(a, y)))
                if b < y: nxt.append((max(b, x), y))
            seg = nxt
        out += seg
    return [(a, b) for a, b in out if b > a]
_base = _union([(min(r['flo'], r['fhi']), max(r['flo'], r['fhi'])) for r in GOOD])
_h = lambda f: f * 50.0 / C_KMS
_cut_old = [(f - _h(f), f + _h(f)) for f in CAT_OLD.values()]
_cut_new = [(f - _h(f), f + _h(f)) for f in CAT.values()]
_lost_old = sum(b - a for a, b in _base) - sum(b - a for a, b in _sub(_base, _cut_old))
_lost_new = sum(b - a for a, b in _base) - sum(b - a for a, b in _sub(_base, _cut_new))
M('MaskLostOldGHz', '%.2f' % _lost_old)
M('MaskLostNewGHz', '%.2f' % _lost_new)
M('MaskExtraGHz', '%.2f' % (_lost_new - _lost_old))
M('MaskExtraPct', '%.1f' % (100.0 * (_lost_new - _lost_old) / sum(b - a for a, b in _base)))
M('NCrossFreq', '%d' % sum(1 for r in CROSS if r['f_cross'] is not None))

# --------------------------------------------------- C. Hanning correction --
# ALMA's default online Hanning response leaves a fraction of a sub-channel
# tone's power in the peak channel that depends on where in the channel the
# tone sits.  Hanning weights (0.25, 0.5, 0.25) applied to a delta at
# sub-channel position u in [-0.5, 0.5] give peak-channel fractions between
# the channel-centred and the boundary-straddling cases.
def hanning_peak_fraction(u):
    """Peak-channel power fraction for a delta-function tone at sub-channel
    offset u (channels) under the 0.25/0.5/0.25 Hanning kernel."""
    w = {-1: 0.25, 0: 0.5, 1: 0.25}
    # the unsmoothed tone falls in channel 0 with weight 1 - |u| and in the
    # neighbour with |u| (linear channel response), then Hanning mixes them
    a0, a1 = 1.0 - abs(u), abs(u)
    s = int(math.copysign(1, u)) if u != 0 else 1
    pk = w[0] * a0 + w[-s] * a1
    nb = w[s] * a0 + w[0] * a1
    return max(pk, nb)


_us = np.linspace(-0.5, 0.5, 4001)
_fr = np.array([hanning_peak_fraction(u) for u in _us])
HAN_BEST, HAN_WORST, HAN_MED = _fr.max(), _fr.min(), float(np.median(_fr))
M('HanBest', '%.2f' % HAN_BEST)
M('HanWorst', '%.2f' % HAN_WORST)
M('HanMed', '%.2f' % HAN_MED)
M('HanFacBest', '%.2f' % (1.0 / HAN_BEST))
M('HanFacWorst', '%.1f' % (1.0 / HAN_WORST))
M('HanFacMed', '%.2f' % (1.0 / HAN_MED))
for r in GOOD:
    r['eirp_han_c'] = r['eirp'] / HAN_BEST     # channel-centred tone
    r['eirp_han_w'] = r['eirp'] / HAN_WORST    # boundary-straddling tone

# ---------------------------------- D. Class A / Class B sensitivity, split --
def sci(x, sf=2):
    e = int(math.floor(math.log10(abs(float(x)))))
    m = float(x) / 10 ** e
    return r'%.*f\times10^{%d}' % (sf - 1, m, e)


for tag, cls in (('A', 'fine'), ('B', 'coarse')):
    sel = [r for r in GOOD if r['res_x'] == cls]
    e = sorted(r['eirp'] for r in sel)
    ch = sorted(r['chanw'] for r in sel)
    M('EirpMin' + tag, sci(e[0]))
    M('EirpMax' + tag, sci(e[-1]))
    M('EirpMed' + tag, sci(st.median(e)))
    M('EirpHanMed' + tag, sci(st.median(e) / HAN_WORST))
    M('ChanLo' + tag, ('%.1f' % (ch[0] / 1e3)) if cls == 'fine' else ('%.3f' % (ch[0] / 1e6)))
    M('ChanHi' + tag, ('%.0f' % (ch[-1] / 1e3)) if cls == 'fine' else ('%.2f' % (ch[-1] / 1e6)))
    M('NWin' + tag, '%d' % len(sel))
    M('ChanMed' + tag, ('%.0f' % (st.median(ch) / 1e3)) if cls == 'fine'
      else ('%.3f' % (st.median(ch) / 1e6)))
M('PctCoarse', '%.0f' % (100.0 * sum(1 for r in GOOD if r['res_x'] == 'coarse') / len(GOOD)))
M('AsymExpectPct', '%.1f' % (100.0 * NSRC / (NSRC + N_PROBE)))
M('PctFine', '%.0f' % (100.0 * sum(1 for r in GOOD if r['res_x'] == 'fine') / len(GOOD)))

# eta_drift / eta_smear / a_max per window (referee A11), for the catalogue
for r in GOOD:
    fmid = 0.5 * (r['flo'] + r['fhi']) * 1e9
    r['eta_drift'] = r['drift_max'] * r['onsrc'] / r['chanw']
    r['a_max'] = C_MS * r['drift_max'] / fmid
    tint = r['onsrc'] / r['n_int'] if r['n_int'] else None
    if tint:
        dl = r['drift_max'] * tint / r['chanw']
        r['eta_smear'] = (math.sin(math.pi * dl / 2) / (math.pi * dl / 2)) if dl > 0 else 1.0
    else:
        r['eta_smear'] = None
_ea = sorted(r['eta_drift'] for r in GOOD if r['res_x'] == 'fine')
_eb2 = sorted(r['eta_drift'] for r in GOOD if r['res_x'] == 'coarse')
M('EtaAltOneNow', '%d' % sum(1 for x in _ea if x < 1.0))
M('EtaBgeOneNow', '%d' % sum(1 for x in _eb2 if x >= 1.0))
M('AmaxMin', '%.1f' % min(r['a_max'] for r in GOOD))
M('AmaxMax', '%.1f' % max(r['a_max'] for r in GOOD))

# ------------------------------------- E. system-denominator recomputations --
BYSYS = collections.defaultdict(list)
for r in GOOD:
    BYSYS[sysn(r['star_name'])].append(r)
_deep = {s: min(r['eirp'] for r in rs) for s, rs in BYSYS.items()}
_deepf = {s: min([r['eirp'] for r in rs if r['res_x'] == 'fine'] or [float('inf')])
          for s, rs in BYSYS.items()}
# The three worked detectability cases of the Discussion, recomputed with the
# definition stated in the text: the number of systems whose deepest threshold,
# in the class that case is about, lies at or below the case power.  The lost
# round-6 generator's published values (1, 2, 8, 24) are reproduced exactly, so
# the definition is recovered rather than replaced; none of them moves when
# HD 139084B stops being counted twice.
_deepc = {s: min([r['eirp'] for r in rs if r['res_x'] == 'coarse'] or [float('inf')])
          for s, rs in BYSYS.items()}
_CASEI, _CASEII, _CASEIII = 1.62e13, 8.0e13, 2.0e14
M('CaseDetCoarseNow', '%d' % sum(1 for v in _deepc.values() if v <= _CASEI))
M('CaseDetCoarseTwoNow', '%d' % sum(1 for v in _deepc.values() if v <= 2 * _CASEI))
M('CaseDetFineNow', '%d' % sum(1 for v in _deepf.values() if v <= _CASEII))
M('CaseDetDwellNow', '%d' % sum(1 for v in _deep.values() if v <= _CASEIII))
assert (sum(1 for v in _deepc.values() if v <= _CASEI),
        sum(1 for v in _deepc.values() if v <= 2 * _CASEI),
        sum(1 for v in _deepf.values() if v <= _CASEII),
        sum(1 for v in _deep.values() if v <= _CASEIII)) == (1, 2, 8, 24)
M('NSysInTwentyNow', '%d' % len({sysn(r['star_name']) for r in GOOD if r['dist_pc'] <= 20.0}))
M('NStarBelowAreciboNow', '%d' % sum(1 for v in _deep.values() if v < 2e13))

# --------------------------------------------- F. machine-readable catalogue --
DISPOSITION = {
    ('bet Pic', 3): 'circumstellar CO',
    ('bet Pic', 6): 'circumstellar CO',
    ('HD 48370', 6): 'foreground CO',
    ('CP-72 2713', 7): 'unclassified; not significant at the survey level',
}
FLAGKEY = {(r['star_name'], r['band_x']) for r in FLAG}
COLS = ['star_name', 'system_id', 'band', 'eb', 'dist_pc', 'flo_GHz', 'fhi_GHz',
        'chanw_Hz', 'bandwidth_Hz', 'on_source_s', 'n_int', 'rms_mJy', 'smin_mJy',
        'eirp_nominal_W', 'eirp_hanning_centred_W', 'eirp_hanning_worst_W',
        'drift_max_Hz_s', 'a_max_m_s2',
        'n_drift_trials', 'eta_drift', 'eta_smear', 'resolution_class',
        'search_class', 'star_snr', 'ctrl_max_snr', 'n_ctrl', 'n_ctrl_ge_star',
        'p_rank_addone', 'f_cross_GHz', 'nearest_line', 'line_offset_MHz',
        'line_offset_kms', 'ring_centre', 'theta_pb_arcsec', 'r_in_arcsec',
        'r_out_arcsec', 'n_control', 'ring_seed', 'crossing', 'stage1_flag',
        'disposition']
with open('per_target_results_v3.43.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(COLS)
    for r in sorted(GOOD, key=lambda r: (r['dist_pc'], r['star_name'], r['band_x'],
                                         min(r['flo'], r['fhi']))):
        key = (r['star_name'], r['band_x'])
        nl, off, offk = r['line'], r['line_off'], None
        if off is not None and nl in CAT_OLD:
            offk = C_KMS * (off * 1e-3) / CAT_OLD[nl]
        w.writerow([
            r['star_name'], sysn(r['star_name']), r['band_x'], r['eb'],
            '%.4f' % r['dist_pc'], '%.6f' % min(r['flo'], r['fhi']),
            '%.6f' % max(r['flo'], r['fhi']), '%.4f' % r['chanw'],
            '%.1f' % (abs(r['fhi'] - r['flo']) * 1e9), '%.2f' % r['onsrc'],
            r['n_int'] if r['n_int'] else '',
            '%.5f' % r['rms'],
            '%.5f' % (r['smin'] * 1e3), '%.6e' % r['eirp'],
            '%.6e' % r['eirp_han_c'], '%.6e' % r['eirp_han_w'],
            '%.4f' % r['drift_max'], '%.3f' % r['a_max'], r['ndrift'],
            '%.4g' % r['eta_drift'],
            ('%.4f' % r['eta_smear']) if r['eta_smear'] is not None else '',
            r['res_x'], 'A' if r['res_x'] == 'fine' else 'B',
            '%.4f' % r['star_snr'], '%.4f' % r['cmax'], r['n_ctrl'],
            r['n_ge_star'] if r['n_ge_star'] is not None else
            sum(1 for c in r['ctrl_all'] if c >= r['star_snr']),
            '%.6f' % ((1 + sum(1 for c in r['ctrl_all'] if c >= r['star_snr']))
                      / (len(r['ctrl_all']) + 1)),
            ('%.6f' % r['f_cross']) if r['f_cross'] else '',
            nl or '', ('%.4f' % off) if off is not None else '',
            ('%.3f' % offk) if offk is not None else '',
            'star', '%.3f' % r['theta_pb'], '%.3f' % r['r_in'], '%.3f' % r['r_out'],
            N_PROBE, RING_SEED,
            'True' if r['star_snr'] >= 5.0 else 'False',
            'True' if key in FLAGKEY and r['star_snr'] >= 5.0 and r['star_snr'] > r['cmax'] else 'False',
            (DISPOSITION.get(key, '')
             if (r['star_snr'] >= 5.0 and r['star_snr'] > r['cmax']) else ''),
        ])
M('NCatRows', '%d' % len(GOOD))
M('NCatCols', '%d' % len(COLS))

# ----------------------------------------------------------------- output ---
with open('survey_numbers_round12.tex', 'w') as f:
    f.write('%% GENERATED by v342_calc.py -- do not hand-edit.\n')
    f.write('\n'.join(MAC) + '\n')

json.dump({'mask_report': MASKREPORT, 'new_coincidences': NEWCOINC,
           'band_ring': BANDROWS,
           'rho': {k: (v[0], v[1]) for k, v in RHO.items()}},
          open('v342_stats.json', 'w'), indent=1, default=str)

print('control ring: seed %d, %d probes, annulus %.2f-%.2f theta_PB, n_src=%d'
      % (RING_SEED, N_PROBE, RING_IN, RING_OUT, NSRC))
print('  theta_PB %.1f-%.1f", r_in %.1f-%.1f", r_out %.1f-%.1f"'
      % (min(r['theta_pb'] for r in GOOD), max(r['theta_pb'] for r in GOOD),
         min(r['r_in'] for r in GOOD), max(r['r_in'] for r in GOOD),
         min(r['r_out'] for r in GOOD), max(r['r_out'] for r in GOOD)))
print('  PB response %.2f (in) to %.2f (out), area-weighted mean %.2f'
      % (GAIN_IN, GAIN_OUT, GAIN_MEAN))
for b, fm, pb, ri, ro, n in BANDROWS:
    print('   B%d  nu=%7.1f  theta=%5.1f  r=%5.1f-%5.1f  (%d windows)' % (b, fm, pb, ri, ro, n))
if RHO:
    print('  ordering check: rho(radius, ctrl) = %.2f (p=%.1e) in the CO-filled '
          'window; median rho = %.3f over %d quiet windows'
          % (RHO['CO'][0], RHO['CO'][1], RHO['null'][0], RHO['null'][1]))
print('\nrepaired mask: %d transitions of %d species (was %d of %d); worst rounding %.2f km/s'
      % (len(CAT), NSPEC_NEW, len(CAT_OLD), NSPEC_OLD, _worst))
print('retrospective re-application to the four flagged windows:')
for m in MASKREPORT:
    print('  %-12s B%d  f=%.6f  nearest(new)=%-10s dnu=%+9.2f MHz  '
          'v_topo=%+8.1f  v_stellar=%+8.1f [%s]  v_LSR=%+8.1f [%s]'
          % (m['star'], m['band'], m['f'], m['new'], m['dnu_new'], m['dv_topo'],
             (m['dv_stellar'] if m['dv_stellar'] is not None else float('nan')),
             'MASKED' if m['masked_stellar'] else 'not masked',
             m['dv_lsr'], 'MASKED' if m['masked_lsr'] else 'not masked'))
print('\ncrossings whose nearest transition changes under the repaired catalogue: %d'
      % len(NEWCOINC))
for x in NEWCOINC:
    print('   %-22s B%d %.6f  %s (%+.0f km/s) -> %s (%+.0f km/s)'
          % (x[0], x[1], x[2], x[3], x[4], x[5], x[6]))
print('\nHanning peak-channel fraction: best %.2f, median %.2f, worst %.2f '
      '(threshold optimistic by x%.2f to x%.1f)'
      % (HAN_BEST, HAN_MED, HAN_WORST, 1 / HAN_BEST, 1 / HAN_WORST))
print('catalogue -> per_target_results_v3.43.csv (%d rows, %d columns)'
      % (len(GOOD), len(COLS)))
print('macros -> survey_numbers_round12.tex (%d)' % len(MAC))
