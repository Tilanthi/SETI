#!/usr/bin/env python3
r"""v3.61 generated numbers: the referee cycle that asks the paper to finish
the arguments its appendices had half-made.

Sections
--------
 (1) Radial calibration of the spatial null (referee 1 major 1 and 2; referee 2
     M2), from `radial_null_v361.json`, which re-ranks the star against
     radius-matched controls and against pseudo-stars carrying no star at all.
 (2) The empirical false-alarm rate propagated into the survey's own
     expectation (referee 2 M2).
 (3) Both statistics side by side over the WHOLE survey rather than the seven
     windows that changed class (referee 2 M1).
 (4) Band-by-band molecular-mask accounting (referee 1 major 4), which also
     retires a stale global figure.
 (5) The Class A injection grid: which of the 126 windows are interpolated and
     which extrapolated (referee 2 M7).
 (6) Drift-resolved coverage counted in SYSTEMS, not windows (referee 2 M3).
 (7) Cross-target frequency-occupancy: the expected number of chance
     coincidences the check had never quoted (referee 2 M6).
 (8) Polarisation: what the archive does and does not carry (referee 2 M4).
 (9) The transmitter-gain benchmark as an equation (referee 2 minor 3).

Reads only this folder.  Writes `survey_numbers_round27.tex` and
`tab_maskband.tex`.
"""
import csv, collections, itertools, json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = []


def M(name, val):
    OUT.append(r'\newcommand{\%s}{%s}' % (name, val))


def texval(fn, macro):
    m = re.search(r'\\newcommand\{\\%s\}\{(.*?)\}\s*$' % macro,
                  open(fn).read(), re.M)
    if not m:
        raise SystemExit('%s not found in %s' % (macro, fn))
    return m.group(1)


ROWS = list(csv.DictReader(open('per_target_results_v3.61.csv')))
EXP = json.load(open('frozen_export_v3.60.json'))['rows']
RAD = json.load(open('radial_null_v361.json'))
NWIN = len(ROWS)
NCTRL = 512

# =====================================================================
# (1) The spatial null is radius-dependent, and that is measurable
# =====================================================================
M('RadRIn', '%.2f' % RAD['r_in'])
M('RadROut', '%.2f' % RAD['r_out'])
M('RadUStarMed', '%.4f' % RAD['ustar']['u_median'])
M('RadInsideN', '%d' % RAD['ustar']['inside']['n'])
M('RadOutsideN', '%d' % RAD['ustar']['outside']['n'])
M('RadInsideMed', '%.3f' % RAD['ustar']['inside']['median'])
M('RadOutsideMed', '%.3f' % RAD['ustar']['outside']['median'])
M('RadNWin', '%d' % RAD['n_windows'])

# the radial profile of the control level itself, in units of each window's
# own robust noise scale
zf = RAD['profile']['z']
uf = RAD['profile']['u']
M('RadProfIn', '%+.2f' % zf[0])
M('RadProfMin', '%+.2f' % min(zf))
M('RadProfOut', '%+.2f' % zf[-1])
M('RadProfUIn', '%.2f' % uf[0])
M('RadProfUMin', '%.2f' % uf[zf.index(min(zf))])
M('RadProfUOut', '%.2f' % uf[-1])
zh = RAD['heldout']['profile']['z']
M('RadProfInHO', '%+.2f' % zh[0])
M('RadProfMinHO', '%+.2f' % min(zh))
M('RadProfOutHO', '%+.2f' % zh[-1])

# star rank against all 512 controls, and against the radius-matched inner set
def pfmt(p):
    """A p-value as the manuscript prints them."""
    if p >= 0.01:
        return '%.2f' % p
    if p >= 1e-3:
        return '%.3f' % p
    e = int(math.floor(math.log10(p)))
    return r'%.0f\times10^{%d}' % (p / 10 ** e, e)


M('RadInnerN', '%d' % RAD['inner_n'])
M('RadInnerUHi', '%.2f' % RAD['inner_u_max'])
for tag, d in (('All', RAD['rank_all']), ('In', RAD['rank_inner'])):
    M('RadRank%sMed' % tag, '%.3f' % d['median'])
    M('RadRank%sD' % tag, '%.3f' % d['D'])
    M('RadRank%sP' % tag, pfmt(d['p']))
for tag, d in (('All', RAD['heldout']['rank_all']),
               ('In', RAD['heldout']['rank_inner'])):
    M('HORadRank%sMed' % tag, '%.3f' % d['median'])
    M('HORadRank%sD' % tag, '%.3f' % d['D'])
    M('HORadRank%sP' % tag, pfmt(d['p']))

# pseudo-stars: positions with no star in them, ranked the same way
M('RadPseudoNProbe', '%d' % RAD['pseudo']['n_probes'])
M('RadPseudoULo', '%.2f' % RAD['pseudo']['u_lo'])
M('RadPseudoUHi', '%.2f' % RAD['pseudo']['u_hi'])
M('RadPseudoMed', '%.3f' % RAD['pseudo']['median_one'])
M('RadPseudoP', '%.2f' % RAD['pseudo']['p_one'])
M('HOPseudoMed', '%.3f' % RAD['heldout']['pseudo']['median_one'])
M('HOPseudoD', '%.3f' % RAD['heldout']['pseudo']['D_one'])
M('HOPseudoP', '%.3f' % RAD['heldout']['pseudo']['p_one'])

# =====================================================================
# (2) The tail, which is what the candidate screen actually uses
# =====================================================================
p_exch = 1.0 / (NCTRL + 1)
p_frozen = RAD['pseudo']['first_frac']
p_ho = RAD['heldout']['pseudo']['first_frac']
M('PseudoFirstFrozen', '%.4f' % p_frozen)
M('PseudoFirstHO', '%.4f' % p_ho)
M('PseudoFirstExch', '%.4f' % p_exch)
M('PseudoFirstRatio', '%.1f' % (p_ho / p_exch))
M('PseudoExpFlags', '%.1f' % (NWIN * p_ho))
M('PseudoPgeOne', '%.0f' % (100 * (1 - math.exp(-NWIN * p_ho))))
# the same statement as a per-window false-alarm probability
M('PseudoFAPct', '%.2f' % (100 * p_ho))
M('ExchFAPct', '%.2f' % (100 * p_exch))

# the control percentile of the survey's own unattributed outlier, so that
# tab:heldout can put it beside the campaign's on the same definition
import numpy as _np
_cp = [r for r in EXP if r['star_name'] and r['star_name'].startswith('CP-72')
       and r['ctrl_all'] and r['star_snr'] and r['star_snr'] > 5]
assert len(_cp) == 1, [r['star_name'] for r in _cp]
M('CpCtrlNinetyNine', '%.2f' % _np.percentile(_np.asarray(_cp[0]['ctrl_all'], float), 99))

# =====================================================================
# (3) Both statistics, over the whole survey
# =====================================================================
# The catalogue itself now carries both statistics for every window
# (v342_calc.py), so this reads them back rather than re-deriving them: one
# source, and the released file is what a reader can check.
n_src = 135                       # positions in the superseded region maximum
reg = [r for r in ROWS if r['star_snr_regionmax']]
assert len(reg) == NWIN, (len(reg), NWIN)
reg_cross = sum(1 for r in reg if float(r['star_snr_regionmax']) >= 5)
reg_flag = sum(1 for r in reg if r['stage1_flag_regionmax'] == 'True')
sym_cross = sum(1 for r in ROWS if r['crossing'] == 'True')
sym_flag = sum(1 for r in ROWS if r['stage1_flag'] == 'True')
floor = n_src / float(n_src + NCTRL)
M('StatRegCross', '%d' % reg_cross)
M('StatRegFlag', '%d' % reg_flag)
M('StatSymCross', '%d' % sym_cross)
M('StatSymFlag', '%d' % sym_flag)
M('StatRegFlagPct', '%.0f' % (100.0 * reg_flag / reg_cross))
M('StatRegFloorPct', '%.0f' % (100.0 * floor))
M('StatRegFlagRatio', '%.0f' % (reg_flag / float(sym_flag)))
M('StatNsrc', '%d' % n_src)

# =====================================================================
# (4) Band-by-band cost of the molecular-line mask
# =====================================================================
C_KMS = 299792.458
HALF = float(texval('survey_numbers.tex', 'MaskVWidth')) \
    if re.search(r'\\MaskVWidth\}', open('survey_numbers.tex').read()) else 50.0
MASK = {'CO(1-0)': 115.2712018, 'CO(2-1)': 230.5380000, 'CO(3-2)': 345.7959899,
        'CO(4-3)': 461.0407682, 'CO(6-5)': 691.4730763, '13CO(2-1)': 220.3986842,
        'C18O(2-1)': 219.5603541, 'HCN(1-0)': 88.6316022, 'HCN(3-2)': 265.8864340,
        'HCO+(1-0)': 89.1885260, 'HCO+(3-2)': 267.5576259, 'CS(5-4)': 244.9355565,
        'CN(1-0)': 113.4909702, 'SiO(5-4)': 217.1049800, 'H2CO(3-2)': 218.2221920,
        '[CI](1-0)': 492.1606510, 'H30a': 231.9009280}
# the wider definition the text quotes: every catalogued transition of the
# masked species, from the harvest, not only the 17 named lines
DB = json.load(open('mask_xcheck_lines.json'))
SPECIES = ('CO', '13CO', 'C18O', 'HCN', 'HCO+', 'CS', 'CN', 'SiO', 'H2CO',
           'CI', 'H30')
_strip = lambda s: re.sub(r'<[^>]+>', '', s).replace('&#150;', '-').strip()


def species_of(name):
    n = _strip(name).split()[0] if _strip(name) else ''
    return n


DBF = [x for x in DB['lines'] if species_of(x['name']) in SPECIES]


def merge(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def tubes_of(freqs):
    return merge([(f * (1 - HALF / C_KMS), f * (1 + HALF / C_KMS)) for f in freqs])


def cost(islands, tubes):
    tot = 0.0
    for a, b in islands:
        for c, d in tubes:
            lo, hi = max(a, c), min(b, d)
            if hi > lo:
                tot += hi - lo
    return tot


TUBES_OWN = tubes_of(MASK.values())
TUBES_DB = tubes_of(x['f'] for x in DBF)
byband = collections.defaultdict(list)
for r in ROWS:
    a, b = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    byband[int(r['band'])].append((a, b))
L = ['% Generated by v361_calc.py -- do not edit by hand.',
     r'\begin{table}', r'\centering', r'\footnotesize',
     r'\setlength{\tabcolsep}{4pt}',
     (r'\caption{Band-by-band cost of the molecular-line exclusion. '
      r'Union: unique sky frequency searched in the band. '
      r'Masked: the part of it inside a $\pm\MaskVWidth$\,km\,s$^{-1}$ '
      r'stellar-frame tube around a catalogued transition of one of the '
      r'masked species. Left: what a technosignature search can still '
      r'occupy. The mask is excluded search space and not a veto '
      r'(\S\ref{sec:linecost}); the loss is concentrated in Band~6, where '
      r'CO\,$2\to1$ sits.}'),
     r'\label{tab:maskband}',
     r'\begin{tabular}{@{}crrrr@{}}', r'\hline',
     r'Band & Union (GHz) & Masked (GHz) & Left (GHz) & Lost (\%) \\', r'\hline']
tot_u = tot_m = 0.0
for band in sorted(byband):
    isl = merge(byband[band])
    u = sum(b - a for a, b in isl)
    m = cost(isl, TUBES_DB)
    L.append('%d & %.2f & %.3f & %.2f & %.1f \\\\' % (band, u, m, u - m, 100 * m / u))
ALL = merge([iv for band in byband for iv in byband[band]])
U = sum(b - a for a, b in ALL)
MDB = cost(ALL, TUBES_DB)
MOWN = cost(ALL, TUBES_OWN)
L += [r'\hline',
      'All & %.2f & %.3f & %.2f & %.1f \\\\' % (U, MDB, U - MDB, 100 * MDB / U),
      r'\hline', r'\end{tabular}', r'\end{table}']
open('tab_maskband.tex', 'w').write('\n'.join(L) + '\n')
M('MaskUnionGHz', '%.1f' % U)
M('MaskLostGHz', '%.2f' % MDB)
M('MaskLeftGHz', '%.1f' % (U - MDB))
M('MaskLostPct', '%.1f' % (100 * MDB / U))
M('MaskOwnLostGHz', '%.2f' % MOWN)
M('MaskWorstBand', '%d' % max(byband, key=lambda b: cost(merge(byband[b]), TUBES_DB) /
                              sum(y - x for x, y in merge(byband[b]))))
_wb = max(byband, key=lambda b: cost(merge(byband[b]), TUBES_DB) /
          sum(y - x for x, y in merge(byband[b])))
M('MaskWorstPct', '%.1f' % (100 * cost(merge(byband[_wb]), TUBES_DB) /
                            sum(y - x for x, y in merge(byband[_wb]))))
M('MaskNDbTrans', '%s' % format(len(DBF), ',').replace(',', r'\,'))
# the macros round9_calc.py used to carry as literals, now measured on the
# released catalogue with the definition tab:maskband states
GROSS = sum(abs(float(r['fhi_GHz']) - float(r['flo_GHz'])) for r in ROWS)
gross_lost = 0.0
for r in ROWS:
    a, b = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    gross_lost += cost([(a, b)], TUBES_DB)
M('SearchedUnionGHz', '%.1f' % (U - MDB))
M('MaskUnionLostGHz', '%.2f' % MDB)
M('MaskUnionPct', '%.1f' % (100.0 * MDB / U))
M('MaskGrossLostGHz', '%.1f' % gross_lost)
M('MaskGrossPct', '%.1f' % (100.0 * gross_lost / GROSS))

# =====================================================================
# (5) The Class A injection grid: interpolation or extrapolation?
# =====================================================================
TR = list(csv.DictReader(open('stratified_inject_trials_v3.58.csv')))
cfg = {(int(t['band']), float(t['chanw_Hz']), int(t['n_int']), t['array'])
       for t in TR}
gb = {c[0] for c in cfg}
gcw = [c[1] for c in cfg]
gni = [c[2] for c in cfg]
A = [r for r in ROWS if r['search_class'] == 'A']
inside = [r for r in A if int(r['band']) in gb
          and min(gcw) <= float(r['chanw_Hz']) <= max(gcw)
          and min(gni) <= int(r['n_int']) <= max(gni)]
out_ni = [r for r in A if not (min(gni) <= int(r['n_int']) <= max(gni))]
out_cw = [r for r in A if not (min(gcw) <= float(r['chanw_Hz']) <= max(gcw))]
M('GridConfigs', '%d' % len(cfg))
M('GridBands', ', '.join(str(b) for b in sorted(gb)[:-1]) + ' and ' + str(sorted(gb)[-1]))
M('GridChanLo', '%.1f' % (min(gcw) / 1e3))
M('GridChanHi', '%.0f' % (max(gcw) / 1e3))
M('GridNintLo', '%d' % min(gni))
M('GridNintHi', '%d' % max(gni))
M('GridInside', '%d' % len(inside))
M('GridOutside', '%d' % (len(A) - len(inside)))
M('GridOutNint', '%d' % len(out_ni))
M('GridOutChan', '%d' % len(out_cw))
M('GridInsidePct', '%.0f' % (100.0 * len(inside) / len(A)))

# =====================================================================
# (6) Drift-resolved coverage counted in systems
# =====================================================================
sysA = {r['system_id'] for r in A}
sysAll = {r['system_id'] for r in ROWS}
starA = {r['star_name'] for r in A}
M('ClassASys', '%d' % len(sysA))
M('ClassASysPct', '%.0f' % (100.0 * len(sysA) / len(sysAll)))
M('ClassAStars', '%d' % len(starA))
M('ClassBPct', '%.0f' % (100.0 * sum(1 for r in ROWS if r['search_class'] == 'B') / NWIN))

# =====================================================================
# (7) Cross-target frequency occupancy: what would chance have given?
# =====================================================================
HIT = json.load(open('hitfreqs_v361.json'))
k4 = lambda e, a, b: (e, round(min(a, b), 4), round(max(a, b), 4))
CATK = collections.defaultdict(list)
for r in ROWS:
    CATK[k4(r['eb'], float(r['flo_GHz']), float(r['fhi_GHz']))].append(r)
groups = []
for eb, a, b, fl in HIT:
    c = CATK.get(k4(eb, a, b))
    if not c:
        continue
    r = c[0]
    cw = float(r['chanw_Hz']) / 1e9
    fs = sorted(fl)
    cur = [fs[0]]
    for f in fs[1:]:
        if f - cur[-1] <= 3 * cw:
            cur.append(f)
        else:
            groups.append((r['system_id'], min(a, b), max(a, b), sum(cur) / len(cur)))
            cur = [f]
    groups.append((r['system_id'], min(a, b), max(a, b), sum(cur) / len(cur)))
KER = 46e-6                      # GHz, the three-channel kernel of the check
E = 0.0
npair = 0
for i, j in itertools.combinations(range(len(groups)), 2):
    x, y = groups[i], groups[j]
    if x[0] == y[0]:
        continue
    lo, hi = max(x[1], y[1]), min(x[2], y[2])
    if hi <= lo:
        continue
    npair += 1
    E += min(1.0, 2 * KER / (hi - lo))
M('OccGroups', '%d' % len(groups))
M('OccSystems', '%d' % len({g[0] for g in groups}))
M('OccPairs', '%d' % npair)
M('OccExpChance', '%.2f' % E)
M('OccPgeOne', '%.0f' % (100 * (1 - math.exp(-E))))
M('OccBoundPct', '%.0f' % (100.0 * 3.0 / npair))   # Poisson 95% rule of three

# =====================================================================
# (8) Polarisation: what the archive carries
# =====================================================================
POL = json.load(open('polstates_v351.json'))
both = sum(1 for v in POL.values() if 'XX' in v[0] and 'YY' in v[0])
cross = sum(1 for v in POL.values() if 'XY' in v[0] or 'YX' in v[0])
# \NPolEB and \NPolBoth are v351_calc.py's; only the cross-hand count and the
# per-hand sensitivity factor are new here
assert len(POL) == both, 'a block is missing a parallel hand'
M('PolCross', '%d' % cross)
M('PolGain', '%.2f' % math.sqrt(2.0))

# =====================================================================
# (8a) R_sigma on unflagged windows (referee 2, minor 4)
# =====================================================================
RS = json.load(open('rsigma_sample_v361.json'))
_r = sorted(x['R_sigma'] for x in RS)
import statistics as _st
M('RsigSampN', '%d' % len(_r))
M('RsigSampMed', '%.3f' % _st.median(_r))
M('RsigSampLo', '%.3f' % _r[0])
M('RsigSampHi', '%.3f' % _r[-1])
M('RsigSampWithin', '%d' % sum(1 for x in _r if abs(x - 1) < 0.05))
M('RsigSampPct', '%.0f' % (100.0 * max(abs(x - 1) for x in _r)))

# =====================================================================
# (8b) Which planets are inside the drift-linearity boundary (referee 2 m7)
# =====================================================================
PL = json.load(open('planet_periods_v361.json'))
PL.sort(key=lambda r: r['pl_orbper'])
BOUND = 1.6                      # days, the curvature boundary quoted in S6.4
insideb = [r for r in PL if r['pl_orbper'] <= BOUND]
M('PlanetPerN', '%d' % len(PL))
M('PlanetPerHosts', '%d' % len({r['hostname'] for r in PL}))
M('PlanetInsideN', '%d' % len(insideb))
M('PlanetInsideName', insideb[0]['pl_name'].replace('-', '--') if insideb else 'none')
M('PlanetInsideP', '%.2f' % insideb[0]['pl_orbper'] if insideb else '--')
M('PlanetNextP', '%.2f' % PL[len(insideb)]['pl_orbper'])
M('PlanetNextName', PL[len(insideb)]['pl_name'].replace('-', '--'))
_other = [r for r in PL if r['hostname'] != insideb[0]['hostname']]
M('PlanetOtherP', '%.2f' % _other[0]['pl_orbper'])
M('PlanetOtherName', _other[0]['pl_name'])

# =====================================================================
# (9) The transmitter benchmark, as an equation
# =====================================================================
D_M, P_TX, F_BENCH = 12.0, 1.0e6, 230.0e9
lam = 299792458.0 / F_BENCH
gain = 4 * math.pi * (math.pi * (D_M / 2) ** 2) / lam ** 2
M('BenchDiam', '%.0f' % D_M)
M('BenchGainSci', r'%.1f\times10^{%d}' % (gain / 10 ** int(math.floor(math.log10(gain))),
                                          int(math.floor(math.log10(gain)))))
_e = P_TX * gain
M('BenchEirpSci', r'%.1f\times10^{%d}' % (_e / 10 ** int(math.floor(math.log10(_e))),
                                          int(math.floor(math.log10(_e)))))

# ---------------------------------------------------------------------
_names = [re.match(r'\\newcommand\{\\([A-Za-z]+)\}', s).group(1) for s in OUT]
assert len(set(_names)) == len(_names), 'duplicate macro in this round'
EARLIER = ['survey_numbers.tex'] + ['survey_numbers_round%d.tex' % n for n in range(5, 27)]
for fn in EARLIER:
    if not os.path.exists(fn):
        continue
    txt = open(fn).read()
    for n in _names:
        if re.search(r'\\newcommand\{\\%s\}' % n, txt):
            raise SystemExit('%s already defined in %s' % (n, fn))
open('survey_numbers_round27.tex', 'w').write(
    '%% GENERATED by v361_calc.py -- do not hand-edit.\n' + '\n'.join(OUT) + '\n')
print('\n'.join(OUT))
print('%d macros' % len(OUT))
