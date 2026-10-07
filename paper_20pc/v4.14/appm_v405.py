#!/usr/bin/env python3
"""Round 91 (v4.05): Appendix M's clustering test, measured and replaced.

Referee 2, item 9, asks for the distribution of the crossings' offsets from
the tuned line and objects that a p = 0.01 clustering result cannot be
described as "no clustering".  The referee is right, and the shipped test
(the 1 MHz bin-multiplicity statistic) turns out to be broken three ways:

 A. it is not counting the crossings.  `f_cross_GHz` is populated for
    \\AppMNPeaks{} of the 1,655 catalogue windows and is every window's own
    peak-SNR frequency, of which \\AppMNCoarsePeaks{} are coarse 15.625 MHz
    continuum windows whose "peak" is a noise maximum.  The survey has
    \\AppMNCross{} crossings, \\AppMNCrossF{} with a released frequency.

 B. its null draws frequencies CONTINUOUSLY inside each window, while a peak
    can land only on one of that window's own ALMA channels -- and two
    windows of identical tuning share an IDENTICAL grid.  Against the
    windows' own grids the expected maximum multiplicity is \\AppMNullGrid{}
    and the observed \\AppMMaxMult{} is entirely typical (p = \\AppMPGrid).
    The published p = 0.0095 is manufactured by a null that did not know
    ALMA has a channel grid.  The honest repair makes the evidence WEAKER,
    not stronger, and it is reported that way.

 C. a 1 MHz multiplicity statistic has no power against clustering wider
    than about one channel, which is the structure the referee asks about.
    That is measured here rather than asserted: the power curve is computed
    for both statistics on the SAME simulated data.

The replacement is a scan statistic over a \\AppMLadderLo--\\AppMLadderHi\\,MHz
ladder, calibrated on the same grid null.  Applied to the released crossing
frequencies it DOES find clustering (p = \\AppMScanP) -- located at CO(2-1),
and removed by the line mask.  The same statement without any choice of band:
\\AppMTubeObs{} of the \\AppMNCrossF{} crossings lie inside the survey's own
+-50 km/s tube against \\AppMTubeNull{} expected from the same windows' grids.

Everything here is computed from the frozen release in this directory
(`per_target_results_v3.99.csv`) and from the 15-transition search list
parsed out of `v342_calc.py`.  Nothing outside the version directory is read.

-> survey_numbers_round91.tex, appm_v405.json,
   figures/appm_power.pdf, figures/appm_power.png
"""
import collections
import csv
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round91.tex')
JSONOUT = os.path.join(HERE, 'appm_v405.json')
FIGDIR = os.path.join(HERE, 'figures')
CAT = os.path.join(HERE, 'per_target_results_v3.99.csv')

# Every draw in this generator comes from this one stream, consumed in a fixed
# order, so the products are byte-identical run to run (the build's
# clean-regeneration gate deletes them, re-runs and compares sha256).
SEED = 20260926
RNG = np.random.default_rng(SEED)

NMC = 4000            # draws for the 1 MHz statistic's nulls
NMC_SCAN = 4000       # draws for the scan statistic's nulls
NPOW = 600            # trials per power point (+-2 per cent at 50 per cent)
BIN_MHZ = 1.0
LADDER = [1.0, 3.0, 10.0, 30.0, 100.0, 300.0]          # MHz
MASK_HALF = 50.0                                        # km/s, the frozen tube
C_KMS = 299792.458

# The frozen list the SEARCH ran: 15 transitions, rounded to 1 MHz.  Parsed out
# of the generator that owns it, so the two cannot drift apart; parsing is
# safer than importing, which would rebuild the catalogue this script reads.
_src = open(os.path.join(HERE, 'v342_calc.py')).read()
_i = _src.index('CAT_OLD = {')
_j = _src.index('}', _i)
CAT_OLD = eval(_src[_i + len('CAT_OLD = '):_j + 1])            # noqa: S307
assert len(CAT_OLD) == 15, len(CAT_OLD)

# The released catalogue carries the SEARCH CODE's key spelling for formaldehyde
# ('H2CO') while the mask list is keyed 'H2CO(3-2)'.  Normalise once, here.
SPELL = {'H2CO': 'H2CO(3-2)'}

# What the shipped Appendix M reports.  This generator must reproduce it before
# it is allowed to criticise it; see the falsifier assertions below.
SHIPPED = dict(max_multiplicity=4, null_mean=2.44, p=0.0095)

M = {}


def m(k, v):
    M[k] = v


def F(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def lohi(r):
    """Window edges, low first: a descending spw writes fhi < flo."""
    return (min(F(r['flo_GHz']), F(r['fhi_GHz'])),
            max(F(r['flo_GHz']), F(r['fhi_GHz'])))


def grid(r):
    """The window's own channel grid, in GHz."""
    lo, hi = lohi(r)
    cw = F(r['chanw_Hz']) / 1e9
    n = int(round((hi - lo) / cw)) + 1
    return lo + cw * np.arange(n)


def maxmult(f):
    """The shipped statistic: largest multiplicity in a 1 MHz bin."""
    b = collections.Counter(int(round(x * 1000.0 / BIN_MHZ)) for x in f)
    return max(b.values()), b


def scanmax(f, widths=LADDER):
    """The replacement: max count in any half-open band of any listed width."""
    f = np.sort(np.asarray(f, float)) * 1000.0                 # MHz
    n = f.size
    best = 0
    for w in widths:
        c = np.searchsorted(f, f + w, side='left') - np.arange(n)
        best = max(best, int(c.max()))
    return best


def scanband(f, widths=LADDER):
    """The maximal band itself: (width_MHz, lo_GHz, hi_GHz, count)."""
    fs = np.sort(np.asarray(f, float)) * 1000.0
    n = fs.size
    best = (0, None, None, 0)
    for w in widths:
        c = np.searchsorted(fs, fs + w, side='left') - np.arange(n)
        i = int(c.argmax())
        if int(c[i]) > best[3]:
            best = (w, fs[i] / 1000.0, (fs[i] + w) / 1000.0, int(c[i]))
    return best


def dv_nearest(f):
    """Offset in km/s from the nearest transition in the frozen mask."""
    k = min(CAT_OLD, key=lambda q: abs(C_KMS * (f - CAT_OLD[q]) / CAT_OLD[q]))
    return C_KMS * (f - CAT_OLD[k]) / CAT_OLD[k]


# --------------------------------------------------------------- the data ---
ROWS = list(csv.DictReader(open(CAT)))
HAVE = [r for r in ROWS if F(r['f_cross_GHz']) and lohi(r)[1] > lohi(r)[0]]
CROSS = [r for r in ROWS if r['crossing'] == 'True']
CROSSF = [r for r in CROSS if F(r['f_cross_GHz'])]
for r in CROSSF:
    nl = SPELL.get(r['nearest_line'], r['nearest_line'])
    f = F(r['f_cross_GHz'])
    r['_line'] = nl
    r['_dv'] = C_KMS * (f - CAT_OLD[nl]) / CAT_OLD[nl]
    r['_attr'] = abs(r['_dv']) <= MASK_HALF
UNATTR = [r for r in CROSSF if not r['_attr']]
FINE = [r for r in CROSSF if F(r['chanw_Hz']) < 1e6]
FINE_UN = [r for r in FINE if not r['_attr']]

out = dict(seed=SEED, n_mc=NMC, n_mc_scan=NMC_SCAN, n_power_trials=NPOW,
           ladder_MHz=LADDER, mask_half_kms=MASK_HALF,
           counts=dict(n_rows=len(ROWS), n_with_fcross=len(HAVE),
                       n_crossings=len(CROSS),
                       n_crossings_with_fcross=len(CROSSF),
                       n_coarse_with_fcross=sum(1 for r in HAVE
                                                if F(r['chanw_Hz']) >= 5e6),
                       n_crossings_attributed=len(CROSSF) - len(UNATTR),
                       n_crossings_unattributed=len(UNATTR),
                       n_fine_crossings=len(FINE)))

# ★ Defect B rests entirely on the claim that a peak can land only on one of
# its window's own channels.  That is a property of the released catalogue, so
# measure it: the worst deviation of any released peak frequency from its own
# grid, in channels.  Breaking this assert would mean the grid null is not the
# right null and the whole of Section B (and the power curve, which is
# calibrated on that null) would have to be withdrawn.
_gres = []
for r in HAVE:
    lo, _hi = lohi(r)
    k = (F(r['f_cross_GHz']) - lo) / (F(r['chanw_Hz']) / 1e9)
    _gres.append(abs(k - round(k)))
GRID_WORST = float(max(_gres))
assert GRID_WORST < 0.1, GRID_WORST          # 1 kHz rounding of f_cross_GHz

# ----------------------------------------------- A + B: the 1 MHz statistic --
f_all = [F(r['f_cross_GHz']) for r in HAVE]
obs_mm, bins = maxmult(f_all)
G_all = [grid(r) for r in HAVE]
LH_all = [lohi(r) for r in HAVE]
mm_c = np.array([maxmult([RNG.uniform(lo, hi) for lo, hi in LH_all])[0]
                 for _ in range(NMC)])
mm_g = np.array([maxmult([g[RNG.integers(0, g.size)] for g in G_all])[0]
                 for _ in range(NMC)])
p_c = float(((mm_c >= obs_mm).sum() + 1) / (NMC + 1))
p_g = float(((mm_g >= obs_mm).sum() + 1) / (NMC + 1))

# ★★★ THE FALSIFIER, fixed before this generator was written: it must
# reproduce the SHIPPED test -- observed multiplicity 4, continuous-null mean
# 2.44 +- 0.15, p = 0.0095 -- before it is entitled to criticise it.  If any of
# these three fires, this generator is not computing the published statistic
# and nothing below it stands; the appendix must revert to the shipped text
# until the discrepancy is understood.
assert obs_mm == SHIPPED['max_multiplicity'], obs_mm
assert abs(mm_c.mean() - SHIPPED['null_mean']) < 0.15, mm_c.mean()
assert abs(p_c - SHIPPED['p']) < 0.006, p_c

out['one_mhz'] = dict(
    n=len(f_all), observed=obs_mm,
    null_continuous=dict(mean=float(mm_c.mean()), p=p_c),
    null_grid=dict(mean=float(mm_g.mean()), p=p_g),
    grid_worst_channel_fraction=GRID_WORST,
    falsifier='PASS: the continuous null reproduces the shipped 2.44 / 0.0095',
    crowded_bins=[dict(bin_MHz=k, n=n, members=[
        dict(star=r['star_name'], eb=r['eb'], f=F(r['f_cross_GHz']),
             chanw_kHz=F(r['chanw_Hz']) / 1e3, crossing=r['crossing'])
        for r in HAVE
        if int(round(F(r['f_cross_GHz']) * 1000.0)) == k])
        for k, n in sorted(bins.items(), key=lambda t: -t[1])[:4]])

# ★ The four crowded bins name the mechanism themselves: every member should be
# a coarse window sharing a standard tuning, and none of them a crossing.  If a
# crossing ever appears here the "not one of them is a crossing" sentence in
# the appendix is false and must be rewritten.
assert not any(mem['crossing'] == 'True'
               for b in out['one_mhz']['crowded_bins']
               for mem in b['members']), 'a crossing is in a crowded bin'

# ---------------------------------------------- the scan statistic, on data --
SETS = (('all_window_peaks', HAVE), ('crossings', CROSSF),
        ('crossings_unattributed', UNATTR), ('crossings_fine', FINE),
        ('crossings_fine_unattributed', FINE_UN))
out['scan'] = {}
for tag, sub in SETS:
    f = [F(r['f_cross_GHz']) for r in sub]
    obs = scanmax(f)
    w, blo, bhi, cnt = scanband(f)
    G = [grid(r) for r in sub]
    null = np.array([scanmax([g[RNG.integers(0, g.size)] for g in G])
                     for _ in range(NMC_SCAN)])
    members = sorted(
        [dict(star=r['star_name'], eb=r['eb'], f=F(r['f_cross_GHz']),
              dv=round(r['_dv'], 1) if '_dv' in r else None,
              line=r.get('_line', SPELL.get(r['nearest_line'],
                                            r['nearest_line'])),
              attributed=r.get('_attr'))
         for r in sub if blo - 1e-9 <= F(r['f_cross_GHz']) < bhi + 1e-9],
        key=lambda d: d['f'])
    out['scan'][tag] = dict(
        n=len(f), observed=obs,
        null_mean=float(null.mean()), null_p95=float(np.percentile(null, 95)),
        p=float(((null >= obs).sum() + 1) / (NMC_SCAN + 1)),
        crit95=int(np.percentile(null, 95)),
        max_band=dict(width_MHz=w, lo_GHz=blo, hi_GHz=bhi, count=cnt),
        members=members,
        n_members_attributed=sum(1 for mem in members if mem['attributed']))

# ------------------------------------------------------- the POWER CURVE ----
# The decision rule is fixed FIRST, from the grid null: reject when the
# statistic exceeds the null's 95th percentile.  Then inject a cluster of k
# events of width W into a grid-null draw of the crossing windows and measure
# the rejection rate.  BOTH statistics are run on the SAME simulated data, so
# the comparison cannot favour either by construction.
Gc = [grid(r) for r in CROSSF]
null_scan = np.array([scanmax([g[RNG.integers(0, g.size)] for g in Gc])
                      for _ in range(NMC_SCAN)])
null_mm = np.array([maxmult([g[RNG.integers(0, g.size)] for g in Gc])[0]
                    for _ in range(NMC_SCAN)])
crit_scan = float(np.percentile(null_scan, 95))
crit_mm = float(np.percentile(null_mm, 95))
F_CENTRE = 345.478                         # the band the referee points at
WIDTHS = [1.0, 10.0, 30.0, 100.0, 156.0, 300.0]
# The width the paper quotes the power curve at.  Named rather than repeated,
# because the prose has to agree with the column the curve was measured in.
WIDE_MHZ = 156.0
assert WIDE_MHZ in WIDTHS, WIDE_MHZ
KS = [0, 2, 4, 6, 8, 12, 18, 24]
power = {'crit_scan': crit_scan, 'crit_one_mhz': crit_mm,
         'widths_MHz': WIDTHS, 'k': KS, 'scan': {}, 'one_mhz': {}}
for W in WIDTHS:
    ps, pm = [], []
    for k in KS:
        hs = hm = 0
        for _ in range(NPOW):
            f = np.array([g[RNG.integers(0, g.size)] for g in Gc])
            if k:
                idx = RNG.choice(f.size, size=min(k, f.size), replace=False)
                f[idx] = F_CENTRE + RNG.uniform(0, W / 1000.0, size=idx.size)
            hs += scanmax(f) > crit_scan
            hm += maxmult(f)[0] > crit_mm
        ps.append(hs / NPOW)
        pm.append(hm / NPOW)
    power['scan']['%g' % W] = ps
    power['one_mhz']['%g' % W] = pm
out['power'] = power

# ★★★ THE CONCLUSION, MACHINE-CHECKED.  The appendix's claim is that the scan
# statistic has power against the structure the referee asks about (a cluster
# ~156 MHz wide) where the 1 MHz statistic has none.  Assert the ordering at
# twelve injected events -- a quarter of the crossing population -- rather than
# typing it.  If this fires, the replacement is not an improvement at that
# scale and the appendix's recommendation is wrong.
_i12 = KS.index(12)
assert power['scan']['156'][_i12] > power['one_mhz']['156'][_i12], (
    power['scan']['156'][_i12], power['one_mhz']['156'][_i12])
# ★ And the honest other half of the same claim: against a cluster EXACTLY one
# bin wide the old statistic beats the new one.  It is a channel-coincidence
# detector, not a useless one, and the appendix says so.  If this fires, that
# sentence must go.
_i6 = KS.index(6)
assert power['one_mhz']['1'][_i6] > power['scan']['1'][_i6], (
    power['one_mhz']['1'][_i6], power['scan']['1'][_i6])
# ★ Both statistics must be conservative in size (integer-valued statistics cut
# at a discrete atom), otherwise the rejection rates are not lower bounds on
# power at a true 5 per cent level and the caption's claim is wrong.
assert max(power['scan']['%g' % W][0] for W in WIDTHS) <= 0.05, 'scan oversized'
assert max(power['one_mhz']['%g' % W][0] for W in WIDTHS) <= 0.05, 'old oversized'

# ---------------- the same statement with no scan and no choice of band ------
# How many crossings lie inside the survey's own +-50 km/s tube, against a null
# drawn from the same windows' channel grids?  This is the referee's figure
# reduced to one number.
obs_in = sum(1 for r in CROSSF if abs(dv_nearest(F(r['f_cross_GHz'])))
             <= MASK_HALF)
nin = np.array([sum(1 for g in Gc
                    if abs(dv_nearest(g[RNG.integers(0, g.size)])) <= MASK_HALF)
                for _ in range(NMC_SCAN)])
out['tube_occupancy'] = dict(
    n=len(CROSSF), observed=obs_in, null_mean=float(nin.mean()),
    null_sd=float(nin.std()),
    p=float(((nin >= obs_in).sum() + 1) / (NMC_SCAN + 1)))
# ★ The tube statement and the scan statement must agree in direction: both are
# one-sided excesses of crossings on the masked transitions.  If the tube
# occupancy ever falls at or below its null the prose "the crossing population
# is significantly concentrated on the masked transitions" is false.
assert obs_in > out['tube_occupancy']['null_mean'], obs_in

# ------------------------------------------------------------------ macros --
sc, su = out['scan']['crossings'], out['scan']['crossings_unattributed']
mb = sc['max_band']
m('AppMNPeaks', '%d' % out['counts']['n_with_fcross'])
m('AppMNCross', '%d' % out['counts']['n_crossings'])
m('AppMNCrossF', '%d' % out['counts']['n_crossings_with_fcross'])
m('AppMNCoarsePeaks', '%d' % out['counts']['n_coarse_with_fcross'])
m('AppMMaxMult', '%d' % out['one_mhz']['observed'])
m('AppMNullCont', '%.2f' % out['one_mhz']['null_continuous']['mean'])
m('AppMPCont', '%.4f' % out['one_mhz']['null_continuous']['p'])
m('AppMNullGrid', '%.2f' % out['one_mhz']['null_grid']['mean'])
m('AppMPGrid', '%.4f' % out['one_mhz']['null_grid']['p'])
m('AppMScanObs', '%d' % sc['observed'])
m('AppMScanNull', '%.2f' % sc['null_mean'])
m('AppMScanP', '%.4f' % sc['p'])
# ★ THE PRINTED INTERVAL MUST CONTAIN ITS OWN MEMBERS.  The scan band runs
# 230.422618-230.722618 GHz and holds 12 crossings; rounded to kHz for print
# the lower edge became 230.423, which is ABOVE the lowest member, so the
# appendix stated an interval excluding one of the crossings it counted in it.
# Round OUTWARD -- floor the lower edge, ceil the upper -- and then require
# the printed numbers to bracket every member.  Reverting either rounding to
# `%.3f` makes this assertion fail on the shipped data, which is how it was
# checked.
_BAND_LO = math.floor(mb['lo_GHz'] * 1e3) / 1e3
_BAND_HI = math.ceil(mb['hi_GHz'] * 1e3) / 1e3
assert all(_BAND_LO <= mem['f'] <= _BAND_HI for mem in sc['members']), (
    'the printed band %.3f-%.3f GHz excludes a member it counts: %s'
    % (_BAND_LO, _BAND_HI,
       [mem['f'] for mem in sc['members']
        if not _BAND_LO <= mem['f'] <= _BAND_HI]))
# and the count must be the SET, not a separately carried integer
assert mb['count'] == len(sc['members']), (mb['count'], len(sc['members']))
m('AppMBandLo', '%.3f' % _BAND_LO)
m('AppMBandHi', '%.3f' % _BAND_HI)
m('AppMBandWidth', '%g' % mb['width_MHz'])
m('AppMBandN', '%d' % len(sc['members']))
m('AppMBandNAttr', '%d' % sc['n_members_attributed'])
m('AppMUnattrN', '%d' % su['n'])
m('AppMUnattrObs', '%d' % su['observed'])
m('AppMUnattrNull', '%.2f' % su['null_mean'])
m('AppMUnattrP', '%.3f' % su['p'])
# The cluster width the power curve is quoted at, so the prose cannot name a
# width the curve was not measured at.  156 MHz is the span of the structure
# referee 2 asks about.
m('AppMWideMHz', '%g' % WIDE_MHZ)
m('AppMPowerOldWideK', '%d' % 24)
m('AppMPowerOldWide', '%.1f' % (100 * power['one_mhz']['156'][KS.index(24)]))
m('AppMPowerNewWide', '%.1f' % (100 * power['scan']['156'][KS.index(12)]))
m('AppMPowerNewSix', '%.1f' % (100 * power['scan']['156'][KS.index(6)]))
m('AppMPowerOldNarrow', '%.1f' % (100 * power['one_mhz']['1'][KS.index(6)]))
m('AppMLadderLo', '%g' % LADDER[0])
m('AppMLadderHi', '%g' % LADDER[-1])
m('AppMTubeObs', '%d' % out['tube_occupancy']['observed'])
m('AppMTubeNull', '%.1f' % out['tube_occupancy']['null_mean'])
m('AppMTubeP', '%.4f' % out['tube_occupancy']['p'])
out['macros'] = dict(M)


# ------------------------------------------------------------------ figure --
def figure():
    """Three panels.  (b) is the figure R2-9 explicitly asks for: each
    crossing's velocity offset from the nearest masked transition, against a
    MATCHED null drawn from the same windows' own channel grids."""
    import matplotlib
    matplotlib.use('Agg')
    # Type-3 fonts are a gate in this build (arXiv rejects them and they do not
    # subset cleanly); 42 is TrueType.  Every other figure generator here does
    # the same, and the gate caught this one missing it.
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42
    import matplotlib.pyplot as plt

    fa = np.array([F(r['f_cross_GHz']) for r in CROSSF])
    dv = np.array([dv_nearest(x) for x in fa])
    attr = np.abs(dv) <= MASK_HALF

    p = out['power']
    ks = p['k']
    fig, ax = plt.subplots(1, 3, figsize=(12.6, 3.7))

    # ---- (a) the power curve ------------------------------------------
    a = ax[0]
    cols = plt.cm.viridis(np.linspace(0.05, 0.85, len(p['widths_MHz'])))
    for c, W in zip(cols, p['widths_MHz']):
        a.plot(ks, p['scan']['%g' % W], '-o', ms=3.2, color=c,
               label='%g MHz' % W)
        a.plot(ks, p['one_mhz']['%g' % W], '--', lw=1.0, color=c, alpha=0.8)
    a.axhline(0.05, color='0.5', lw=0.8, ls=':')
    a.set_xlabel('injected events in the cluster')
    a.set_ylabel('rejection rate, 95th-percentile cut')
    a.set_ylim(-0.03, 1.03)
    a.set_title('(a) power: scan statistic (solid)\nvs the 1 MHz bin count '
                '(dashed)', fontsize=9)
    a.legend(fontsize=7, ncol=2, title='cluster width', title_fontsize=7,
             loc='center left', frameon=False)

    # ---- (b) offset from the nearest masked transition, vs a matched null --
    b = ax[1]
    G = [grid(r) for r in CROSSF]
    NB = 400                      # null realisations of the whole population
    nulldv = np.concatenate([[dv_nearest(g[RNG.integers(0, g.size)])
                              for g in G] for _ in range(NB)])
    edges = np.linspace(-400, 400, 41)
    ho, _ = np.histogram(dv, bins=edges)
    hn, _ = np.histogram(nulldv, bins=edges)
    hn = hn / float(NB)
    b.bar(0.5 * (edges[1:] + edges[:-1]), hn, width=np.diff(edges),
          color='0.82', label='matched null (same windows,\ntheir own channel '
                              'grids)')
    b.step(0.5 * (edges[1:] + edges[:-1]), ho, where='mid', color='#2c3e50',
           lw=1.4, label='observed crossings')
    b.axvspan(-MASK_HALF, MASK_HALF, color='#c0392b', alpha=0.13, zorder=0)
    b.set_xlabel(r'$\Delta v$ from the nearest masked transition '
                 r'(km s$^{-1}$, topocentric)')
    b.set_ylabel('crossings per bin')
    b.set_title('(b) offset from the nearest masked transition;\n%d of %d '
                r'inside $\pm50$ km s$^{-1}$ (null %.1f)'
                % (int(attr.sum()), len(CROSSF),
                   float((np.abs(nulldv) <= MASK_HALF).sum()) / NB),
                fontsize=9)
    b.legend(fontsize=7, frameon=False)

    # ---- (c) the scan, zoomed on the maximal band ----------------------
    c = ax[2]
    mb_ = out['scan']['crossings']['max_band']
    c.axvspan(mb_['lo_GHz'], mb_['hi_GHz'], color='0.86', zorder=0,
              label='maximal band (%g MHz)' % mb_['width_MHz'])
    sel = (fa > mb_['lo_GHz'] - 0.35) & (fa < mb_['hi_GHz'] + 0.35)
    c.plot(fa[sel & attr], np.full((sel & attr).sum(), 1.0), '|', ms=16,
           color='#c0392b', label='line-attributed')
    c.plot(fa[sel & ~attr], np.full((sel & ~attr).sum(), 0.72), '|', ms=16,
           color='#2c3e50', label='unattributed')
    c.axvline(CAT_OLD['CO(2-1)'], color='#c0392b', lw=0.8, ls=':')
    c.text(CAT_OLD['CO(2-1)'], 1.16, ' CO(2--1)', color='#c0392b', fontsize=7,
           ha='left')
    c.set_ylim(0.45, 1.65)
    c.set_yticks([])
    c.set_xlabel('sky frequency (GHz)')
    c.set_title('(c) the maximal band %.3f--%.3f GHz:\n%d crossings, %d of '
                'them CO(2--1)'
                % (mb_['lo_GHz'], mb_['hi_GHz'], mb_['count'],
                   out['scan']['crossings']['n_members_attributed']),
                fontsize=9)
    c.legend(fontsize=7, frameon=False, loc='upper left', ncol=1)
    c.text(0.98, 0.04, 'scan $p=%.4f$;  unattributed only $p=%.3f$'
           % (out['scan']['crossings']['p'],
              out['scan']['crossings_unattributed']['p']),
           transform=c.transAxes, fontsize=8, va='bottom', ha='right')

    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIGDIR, 'appm_power.' + ext), dpi=150)
    plt.close(fig)


figure()

with open(JSONOUT, 'w') as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write('\n')

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by appm_v405.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('appm_v405 (round 91): 1 MHz statistic on %d per-window peaks -- '
      'observed %d' % (len(f_all), obs_mm))
print('  continuous null %.2f, p=%.4f (shipped %.2f / %.4f: FALSIFIER PASSES)'
      % (mm_c.mean(), p_c, SHIPPED['null_mean'], SHIPPED['p']))
print('  CHANNEL-GRID null %.2f, p=%.4f -- the observed %d is typical; peaks '
      'sit on their own grids to %.3f channel'
      % (mm_g.mean(), p_g, obs_mm, GRID_WORST))
for tag, _ in SETS:
    d = out['scan'][tag]
    print('  scan %-28s n=%4d obs %3d null %6.2f p=%.4f  band %.3f-%.3f GHz'
          % (tag, d['n'], d['observed'], d['null_mean'], d['p'],
             d['max_band']['lo_GHz'], d['max_band']['hi_GHz']))
print('  maximal band holds %d crossings, %d of them within %g km/s of CO(2-1)'
      % (mb['count'], sc['n_members_attributed'], MASK_HALF))
print('  power over 156 MHz, scan   : %s'
      % ' '.join('k=%d:%.2f' % t for t in zip(KS, power['scan']['156'])))
print('  power over 156 MHz, 1 MHz  : %s'
      % ' '.join('k=%d:%.2f' % t for t in zip(KS, power['one_mhz']['156'])))
print('  power over   1 MHz, 1 MHz  : %s'
      % ' '.join('k=%d:%.2f' % t for t in zip(KS, power['one_mhz']['1'])))
print('  tube occupancy: %d of %d inside +-%g km/s, null %.2f+-%.2f, p=%.4f'
      % (out['tube_occupancy']['observed'], out['tube_occupancy']['n'],
         MASK_HALF, out['tube_occupancy']['null_mean'],
         out['tube_occupancy']['null_sd'], out['tube_occupancy']['p']))
print('  -> %s (%d macros), %s, figures/appm_power.pdf+png'
      % (os.path.basename(OUT), len(M), os.path.basename(JSONOUT)))
