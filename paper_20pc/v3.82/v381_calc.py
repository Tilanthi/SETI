#!/usr/bin/env python3
r"""v3.80: the stage-1 outlier taxonomy on the completed archival sweep.

The released catalogue held 443 windows and four stage-1 spatial outliers,
and the manuscript could name each of them in prose. The completed sweep
holds 1956 windows and thirteen, so the prose has to become arithmetic or it
will be wrong the next time a block lands.

What the enlarged sample actually shows, and it is the cleanest result of
the round: separate the outliers that sit on a molecular transition in the
star's own frame from those that do not, and the unattributed remainder is
what chance predicts. Eight of the thirteen are one object -- beta Pictoris,
in five Band 3 and three Band 6 windows, every one within a few km/s of
systemic on CO -- which is a single astrophysical source seen repeatedly,
not eight independent events.

Everything here is computed from the released catalogue, so the taxonomy
and the table cannot disagree.

Writes survey_numbers_round30.tex and tab_flagged_v380.tex.
"""
import csv, json, math, collections

ROWS = list(csv.DictReader(open('per_target_results_v3.82.csv')))
K = json.load(open('catalogue_constants.json'))
S = json.load(open('survey_stats.json'))
OUT = 'survey_numbers_round30.tex'
TAB = 'tab_flagged_v380.tex'
N = len(ROWS)
assert N == K['n_windows'], (N, K['n_windows'])

M = []


def m(name, val):
    M.append('\\newcommand{\\%s}{%s}' % (name, val))


def F(x):
    return None if x in ('', None) else float(x)



def _ck(n):
    """Census-name key: strip Gaia designations, SIMBAD prefixes and
    punctuation, the same normalisation canon_names_v380.py uses."""
    import re
    n = re.sub(r'\bGaia\s*DR3\s*\d+\b', '', n, flags=re.I)
    n = re.sub(r'^(NAME|V\*|V star|\*)\s+', '', n.strip(), flags=re.I)
    return re.sub(r'[^A-Za-z0-9]+', '', n).lower()



def _texval(name):
    import glob as _g, re as _re
    for _f in sorted(_g.glob('survey_numbers*.tex')):
        _m = _re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name,
                        open(_f).read())
        if _m:
            return _m.group(1)
    return None


def _ebtag(eb):
    """Last two segments of the execution-block uid, which identify it."""
    return '\\_'.join(eb.split('_')[1:])


def _sci(x, sf=2):
    """Two significant figures in LaTeX scientific form."""
    if x is None:
        return '--'
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sf - 1, x / 10.0 ** e, e)


def tidy(s):
    s = ' '.join(s.split())
    for cut in ('  Gaia DR3', ' Gaia DR3'):
        if cut in s:
            s = s.split(cut)[0]
    return s.replace('CP-72', 'CP$-$72').replace('bet Pic', r'$\beta$~Pic')


# --------------------------------------------------------------- taxonomy
# The survey's own molecular tube, +-50 km/s about the transition in the
# stellar frame (v342_calc.py). A stage-1 outlier inside it is attributable
# to the star's own or foreground gas; outside it, nothing in this survey
# explains it.
TUBE_KMS = 50.0
FL = [r for r in ROWS if r['stage1_flag'] == 'True']
assert len(FL) == K['n_flagged'], (len(FL), K['n_flagged'])

attributed = [r for r in FL if abs(F(r['line_offset_kms']) or 9e9) <= TUBE_KMS]
unattributed = [r for r in FL if r not in attributed]

m('NStageOneWin', '%d' % len(FL))
m('NStageOneSys', '%d' % len({r['system_id'] for r in FL}))
m('NStageOneStars', '%d' % len({r['star_name'] for r in FL}))
m('NStageOnePairs', '%d' % len({(r['star_name'], r['band']) for r in FL}))
m('NStageOneLine', '%d' % len(attributed))
m('NStageOneUnattrib', '%d' % len(unattributed))
m('NStageOneUnattribSys', '%d' % len({r['system_id'] for r in unattributed}))

bp = [r for r in FL if r['star_name'].startswith('bet Pic')]
m('NStageOneBpic', '%d' % len(bp))
m('NStageOneBpicThree', '%d' % sum(1 for r in bp if r['band'] == '3'))
m('NStageOneBpicSix', '%d' % sum(1 for r in bp if r['band'] == '6'))
m('NStageOneNonBpic', '%d' % (len(FL) - len(bp)))
m('BpicDvLo', '%.0f' % min(F(r['line_offset_kms']) for r in bp))
m('BpicDvHi', '%.0f' % max(F(r['line_offset_kms']) for r in bp))
m('BpicTsymMax', '%.1f' % max(F(r['star_snr']) for r in bp))
m('BpicTsymMin', '%.1f' % min(F(r['star_snr']) for r in bp))
m('NStageOneBpicEb', '%d' % len({r['eb'] for r in bp}))

# --------------------------------------------- is the remainder chance?
# Under exchangeability a window is rank-first among its NCTRL controls with
# probability 1/(NCTRL+1), so the expected number of stage-1 outliers over
# the catalogue follows directly. This is the comparison the paper has
# always made; on 1956 windows it can be made against the UNATTRIBUTED
# count, which is the one chance is supposed to explain.
NCTRL = K['n_ctrl']
EXP = N / float(NCTRL + 1)
m('ExpStageOneAll', '%.1f' % EXP)
m('ExpStageOneRankFloor', '1/%d' % (NCTRL + 1))


def pois_ge(k, mu):
    """P(X >= k) for a Poisson mean mu."""
    return 1.0 - sum(math.exp(-mu) * mu ** i / math.factorial(i)
                     for i in range(k))


m('PStageOneUnattrib', '%.2f' % pois_ge(len(unattributed), EXP))
m('PStageOneAll', '%.1e' % pois_ge(len(FL), EXP))
m('StageOneUnattribRatio', '%.1f' % (len(unattributed) / EXP))

# Counting beta Pic once, as one astrophysical source rather than eight
# independent events, is the comparison a reader will want.
_eff = len(FL) - len(bp) + (1 if bp else 0)
m('NStageOneSources', '%d' % _eff)

# ------------------------------------------------------- per-flag details
by = collections.defaultdict(list)
for r in FL:
    by[(r['star_name'], r['band'])].append(r)
m('NStageOnePairsTab', '%d' % len(by))

rows = []
for (star, band), rs in sorted(
        by.items(), key=lambda kv: -max(F(r['star_snr']) for r in kv[1])):
    deep = max(rs, key=lambda r: F(r['star_snr']))
    dv = F(deep['line_offset_kms'])
    inside = abs(dv) <= TUBE_KMS
    rows.append((tidy(star), band, len(rs), deep, dv, inside))

with open(TAB, 'w') as fh:
    fh.write('% generated by v380_calc.py -- do not edit\n')
    fh.write('\\begin{tabular}{@{}llrrrrrl@{}}\n\\toprule\n')
    fh.write('Star & B & $N_{\\rm win}$ & $\\nu$ (GHz) & $T_\\star$ & '
             'ctrl & $\\Delta v$ & disposition \\\\\n\\midrule\n')
    for star, band, n, deep, dv, inside in rows:
        fh.write('%s & %s & %d & %.4f & %.2f & %.2f & %s & %s \\\\\n'
                 % (star, band, n, F(deep['f_cross_GHz']) or 0.0,
                    F(deep['star_snr']), F(deep['ctrl_max_snr']),
                    ('$%+.0f$' % dv) if dv is not None else '--',
                    deep['disposition'] or
                    ('%s in frame' % deep['nearest_line'] if inside
                     else 'unattributed')))
    fh.write('\\bottomrule\n\\end{tabular}\n')

# ------------------------------- an illustrative haystack fraction
# Wright et al. (2018) frame a search as a fraction of a multidimensional
# parameter volume. We decline to turn the non-detection into an
# occurrence rate, but an order-of-magnitude statement of how much of that
# volume this survey touched is useful and costs nothing, provided each
# axis is given separately: the product treats the axes as independent,
# which they are not, and is quoted only as an order of magnitude.
_HAY = dict(nu_lo=0.3, nu_hi=300.0)          # GHz, the Wright et al. band
_nstars = len({r['star_name'] for r in ROWS})
_ncensus = 17566                             # Gaia DR3 stars within 40 pc
_union = float(_texval('UnionGHz'))
_tsum = sum(F(r['on_source_s']) for r in ROWS)
_bysys = collections.defaultdict(float)
for r in ROWS:
    _bysys[r['system_id']] = max(_bysys[r['system_id']], F(r['on_source_s']))
_tstar = sum(_bysys.values())
# time axis: cumulative staring time per system against one year each
_ftime = _tstar / (len(_bysys) * 365.25 * 86400.0)
_fstar = _nstars / float(_ncensus)
_fnu = _union / (_HAY['nu_hi'] - _HAY['nu_lo'])
m('HayFracStar', _sci(_fstar))
m('HayFracNu', '%.2f' % _fnu)
m('HayFracTime', _sci(_ftime, 1))
m('HayFracProd', _sci(_fstar * _fnu * _ftime, 1))
m('HayNuLo', '%g' % _HAY['nu_lo'])
m('HayNuHi', '%g' % _HAY['nu_hi'])
m('HayStareHours', '%.0f' % (_tstar / 3600.0))

# ------------------------------------------ the pre-registration order
# A hold-out is only worth having if nothing about the analysis was
# decided after it was fixed. The repository timestamps settle that:
# the detection statistic and the candidate criteria are committed before
# the hold-out rule, and the hold-out rule before any reserved block was
# searched. Generated so the ordering cannot be asserted without being
# checked.
_ORDER = json.load(open('prereg_order_v382.json'))
_d = [(k, _ORDER[k]['date']) for k in ('statistic', 'criteria', 'holdout',
                                       'first_reserved_block_searched')]
for (k1, d1), (k2, d2) in zip(_d, _d[1:]):
    assert d1 <= d2, ('pre-registration order violated', k1, d1, k2, d2)
m('StatFreezeDate', _ORDER['statistic']['date'])
m('StatFreezeHash', _ORDER['statistic']['commit'])
m('HoLeadDays', '%d' % _ORDER['holdout']['days_after_statistic'])
m('HoLeadBlockDays', '%d' % _ORDER['holdout']['days_before_first_reserved'])

# --------------------------------------- the molecular mask, per class
# The aggregate reduction of the frequency union hides the fact that the
# two experiments pay different prices: a coarse channel spans many times
# the +-50 km/s tube, so masking a transition in Class B removes a whole
# 15.6-31.25 MHz window's worth of coverage rather than a sliver.
MASK_KMS = 50.0
_LAB = {'CO(1-0)': 115.271202, 'CO(2-1)': 230.538000, 'CO(3-2)': 345.795990,
        'CO(4-3)': 461.040768, '13CO(2-1)': 220.398684,
        'C18O(2-1)': 219.560354, 'CS(5-4)': 244.935556,
        'SiO(5-4)': 217.104980}


def _union(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _len(iv):
    return sum(b - a for a, b in iv)


def _mask_cost(rows):
    isl = _union([(min(F(r['flo_GHz']), F(r['fhi_GHz'])),
                   max(F(r['flo_GHz']), F(r['fhi_GHz']))) for r in rows])
    tubes = _union([(f * (1 - MASK_KMS / 299792.458),
                     f * (1 + MASK_KMS / 299792.458)) for f in _LAB.values()])
    lost = 0.0
    for a, b in isl:
        for c, d in tubes:
            lost += max(0.0, min(b, d) - max(a, c))
    return _len(isl), lost


for tag, cls in (('A', 'fine'), ('B', 'coarse')):
    _g = [r for r in ROWS if r['resolution_class'] == cls]
    _u, _l = _mask_cost(_g)
    m('MaskUnion' + tag, '%.1f' % _u)
    m('MaskLost' + tag, '%.2f' % _l)
    m('MaskPct' + tag, '%.1f' % (100.0 * _l / _u if _u else 0.0))

# ------------------------------- the CP-72 2713 repeat test, quantified
# A reader should be able to tell "not detected again" from "a persistent
# signal of the original strength would have been recovered", and that
# needs both blocks' parameters side by side rather than scattered through
# a paragraph. Generated from the catalogue, so the table and the text
# cannot drift apart.
_CPF, _CPR = 'A002_Xff0235_X4a6d', 'A002_Xff0235_X502d'
_cp = {r['eb']: r for r in ROWS
       if r['eb'] in (_CPF, _CPR) and F(r['chanw_Hz']) < 1e6}
if len(_cp) == 2:
    _a, _b = _cp[_CPF], _cp[_CPR]
    _rows = [
        ('Execution block', r'\texttt{%s}' % _ebtag(_CPF),
         r'\texttt{%s}' % _ebtag(_CPR)),
        ('Start-to-start separation (h)', r'\multicolumn{2}{c}{\CpRecStartSepH}', None),
        ('On-source time (s)', '%.0f' % F(_a['on_source_s']),
         '%.0f' % F(_b['on_source_s'])),
        ('Channel width (kHz)', '%.2f' % (F(_a['chanw_Hz']) / 1e3),
         '%.2f' % (F(_b['chanw_Hz']) / 1e3)),
        ('Channel rms (mJy)', r'\CpRecRmsOne', r'\CpRecRmsTwo'),
        (r'Primary-beam FWHM (arcsec)', '%.1f' % F(_a['theta_pb_arcsec']),
         '%.1f' % F(_b['theta_pb_arcsec'])),
        ('Frequency axes registered to', r'\multicolumn{2}{c}{\CpRecOffChan{} channel}', None),
        ('Test frequency (GHz)', r'\multicolumn{2}{c}{%.4f}' % F(_a['f_cross_GHz']), None),
        (r'Test drift (kHz\,s$^{-1}$)', r'\multicolumn{2}{c}{\CpRecDriftkHzs}', None),
        ('Drift track sweeps (channels)', r'\multicolumn{2}{c}{\CpRecSweepChan}', None),
        ('Flux at that cell (mJy)',
         r'$\CpRecFluxOne\pm\CpRecErrOne$', r'$\CpRecFluxTwo\pm\CpRecErrTwo$'),
        (r'$T_\star$ in this window', '%.2f' % F(_a['star_snr']),
         '%.2f' % F(_b['star_snr'])),
        ('Largest control statistic', '%.2f' % F(_a['ctrl_max_snr']),
         '%.2f' % F(_b['ctrl_max_snr'])),
        (r'$T_\star$ expected if persistent', '--', r'\CpRecExpT'),
        ('Pair inconsistent at', r'\multicolumn{2}{c}{\CpRecExclPair$\sigma$}', None),
        ('First flux taken as exact', r'\multicolumn{2}{c}{\CpRecExclCond$\sigma$}', None),
    ]
    with open('tab_cprepeat_v382.tex', 'w') as fh:
        fh.write('% generated by v381_calc.py -- do not edit\n')
        fh.write('\\begin{tabular}{@{}lrr@{}}\n\\toprule\n')
        fh.write(' & first block & repeat block \\\\\n\\midrule\n')
        for lab, x, y in _rows:
            fh.write('%s & %s \\\\\n' % (lab, x if y is None else '%s & %s' % (x, y)))
        fh.write('\\bottomrule\n\\end{tabular}\n')
    m('CpOnSrcOne', '%.0f' % F(_a['on_source_s']))
    m('CpOnSrcTwo', '%.0f' % F(_b['on_source_s']))
    m('CpChanKHzTab', '%.2f' % (F(_a['chanw_Hz']) / 1e3))
    m('CpTstarTwo', '%.2f' % F(_b['star_snr']))

# --------------------------------- the unattributed outliers, one table
# The four unattributed stage-1 outliers are not homogeneous and should not
# read as though they were: only one has a repeat observation. One row each,
# generated from the catalogue.
_unatt = sorted(unattributed, key=lambda r: -F(r['star_snr']))
# Repeat coverage: a second execution block of the same star at a tuning
# that contains this window's crossing frequency.
_byname = collections.defaultdict(list)
for r in ROWS:
    _byname[r['star_name']].append(r)


def _repeat_blocks(r):
    f = F(r['f_cross_GHz'])
    if f is None:
        return []
    out = []
    for q in _byname[r['star_name']]:
        if q['eb'] == r['eb']:
            continue
        lo, hi = sorted((F(q['flo_GHz']), F(q['fhi_GHz'])))
        if lo <= f <= hi:
            out.append(q)
    return out


with open('tab_unattributed_v382.tex', 'w') as fh:
    fh.write('% generated by v381_calc.py -- do not edit\n')
    fh.write('\\begin{tabular}{@{}llcrrrrrl@{}}\n\\toprule\n')
    fh.write('Star & EB & B & $\\nu$ (GHz) & $|\\dot\\nu|_{\\rm max}$ & '
             '$T_\\star$ & ctrl & $P_{\\rm eff}$ (W) & repeat blocks \\\\\n')
    fh.write(' & & & & (Hz\\,s$^{-1}$) & & & & \\\\\n\\midrule\n')
    for r in _unatt:
        rep = _repeat_blocks(r)
        if rep:
            best = max(rep, key=lambda q: F(q['star_snr']))
            rp = '%d; $T_\\star=%.2f$' % (len(rep), F(best['star_snr']))
        else:
            rp = 'none'
        # The crossing frequency is released only where the pipeline stored
        # a peak; elsewhere give the window and mark it, rather than
        # printing a zero or inventing a value.
        fc = F(r['f_cross_GHz'])
        nu = ('%.4f' % fc) if fc else ('%.2f--%.2f$^{a}$'
                                       % (min(F(r['flo_GHz']), F(r['fhi_GHz'])),
                                          max(F(r['flo_GHz']), F(r['fhi_GHz']))))
        fh.write('%s & \\texttt{%s} & %s & %s & %.0f & %.2f & %.2f & $%s$ & %s \\\\\n'
                 % (tidy(r['star_name']), _ebtag(r['eb']), r['band'], nu,
                    abs(F(r['drift_max_Hz_s']) or 0.0),
                    F(r['star_snr']), F(r['ctrl_max_snr']),
                    _sci(F(r['eirp_eff_total_W'])), rp))
    fh.write('\\bottomrule\n\\end{tabular}\n')
m('NUnattNoCrossFreq',
  '%d' % sum(1 for r in _unatt if not F(r['f_cross_GHz'])))
m('NUnattRepeat', '%d' % sum(1 for r in _unatt if _repeat_blocks(r)))
m('NUnattNoRepeat', '%d' % sum(1 for r in _unatt if not _repeat_blocks(r)))

# What the expectation of unattributed outliers assumes. Two versions: the
# ideal-exchangeability rate the paper has always quoted, and the same rate
# multiplied by the tail excess measured out of sample. Saying which is
# which is the whole point -- the second is the honest comparison.
_TAIL = json.load(open('holdout_calib_v381.json'))['tail_factor']
m('ExpStageOneTail', '%.1f' % (EXP * _TAIL))
m('TailUsedForExp', '%.1f' % _TAIL)
m('PStageOneUnattribTail',
  '%.2f' % pois_ge(len(unattributed), EXP * _TAIL))

# --------------------------------------------- where the outliers sit
# Every stage-1 outlier of the completed sweep is fine-channel. That is not
# a selection: the coarse class holds three quarters of the windows and
# predicts the larger share of chance outliers, and produces none. Narrow
# circumstellar lines are diluted by a 15.6-31.25 MHz channel, so the class
# that can resolve them is the class that finds them -- and the same logic
# says a genuine narrowband technosignature would also appear here first.
_fine = [r for r in ROWS if r['resolution_class'] == 'fine']
_coarse = [r for r in ROWS if r['resolution_class'] == 'coarse']
_ff = [r for r in _fine if r['stage1_flag'] == 'True']
_cf = [r for r in _coarse if r['stage1_flag'] == 'True']
m('NStageOneFine', '%d' % len(_ff))
m('NStageOneCoarse', '%d' % len(_cf))
m('ExpStageOneFine', '%.2f' % (len(_fine) / float(NCTRL + 1)))
m('ExpStageOneCoarse', '%.2f' % (len(_coarse) / float(NCTRL + 1)))
m('PStageOneCoarseNone', '%.2f' % math.exp(-len(_coarse) / float(NCTRL + 1)))

# ------------------------------------------- the out-of-sample null set
# 195 windows of the sweep lie beyond 40 pc: they are Option A blocks whose
# ALMA target is not a census member. They were searched by the same frozen
# pipeline, they entered no tuning decision and they are outside the sample
# the paper reports, which makes them a genuinely external null.
OS = json.load(open('outofsample_v381.json'))['rows']
m('NOutSample', '%d' % len(OS))
m('NOutSampleEb', '%d' % len({r['eb'] for r in OS}))
m('NOutSampleStars', '%d' % len({r['star_name'] for r in OS}))
m('OutSampleDistLo', '%.1f' % min(r['dist_pc'] for r in OS))
m('OutSampleDistHi', '%.1f' % max(r['dist_pc'] for r in OS))
_osf = [r for r in OS
        if r['star_snr'] is not None and r['ctrl_all']
        and r['star_snr'] >= 5.0 and r['star_snr'] > max(r['ctrl_all'])]
m('NOutSampleFlag', '%d' % len(_osf))
m('ExpOutSampleFlag', '%.1f' % (len(OS) / float(NCTRL + 1)))
# the add-one rank of the star among its own controls, which is U(0,1)
# under exchangeability
_rk = sorted((1 + sum(1 for c in r['ctrl_all'] if c >= r['star_snr']))
             / (len(r['ctrl_all']) + 1.0)
             for r in OS if r['ctrl_all'] and r['star_snr'] is not None)
if _rk:
    m('OutSampleRankMed', '%.3f' % _rk[len(_rk) // 2])
    _d = max(max((i + 1) / len(_rk) - x, x - i / len(_rk))
             for i, x in enumerate(_rk))
    m('OutSampleKsD', '%.2f' % _d)
    _lam = _d * math.sqrt(len(_rk))
    m('OutSampleKsP', '%.2f' % min(1.0, 2 * math.exp(-2 * _lam * _lam)))

# ------------------------------------------------- spectral-class proxy
# The manuscript carried a hand-typed "52 of NStars" for the number of
# searched stars with a Gaia teff_gspphot. It was measured when the sample
# held 88 stars; the sample now holds 94 and the count is 55. A literal
# beside a macro is exactly the pairing that goes stale unnoticed, so it is
# generated here from the same census the selection table uses.
import re as _re
_cen = {}
for _c in csv.DictReader(open('ranked_master40pc.csv')):
    _cen.setdefault(_ck(_c['name']), _c)
_stars = sorted({r['star_name'] for r in ROWS})
_withteff = sum(1 for _s in _stars if (_cen.get(_ck(_s)) or {}).get('teff'))
m('NTeffStars', '%d' % _withteff)
m('NCensusMatched', '%d' % sum(1 for _s in _stars if _ck(_s) in _cen))

# ------------------------------------------- the 90 per cent recovery power
# The number a reader actually wants is "what transmitter power would we
# detect nine times in ten", not "at what power does our internal statistic
# cross 5". The injection campaign measures the latter as a multiple of the
# trigger: recovery reaches 90 per cent at StratPNinety sigma. Threshold
# flux, and so EIRP, is linear in that multiple, so the 90 per cent power
# is the effective threshold scaled by StratPNinety/5. Derived here rather
# than typed, and from the macros the injection generator already emits.


_p90sig = float(_texval('StratPNinety'))
_eff = _texval('EirpEffDeepest')
_effval = float(_eff.split(r'\times10^{')[0]) * 10 ** float(
    _eff.split(r'\times10^{')[1].rstrip('}'))
m('EirpNinetyDeepest', _sci(_effval * _p90sig / 5.0))
m('PNinetyOverTrig', '%.1f' % (_p90sig / 5.0))

# --------------------------------------------------- the data volume
# The size of the archival download is a fact a reader wants and no other
# number in the paper carries: raw ASDM volume actually transferred from the
# ALMA archive, calibrated and searched. Taken from the campaign ledger
# rather than estimated, and stated to the nearest tenth of a terabyte,
# which is the precision the per-block sizes support.
_CAMP = json.load(open('campaign_volume_v382.json'))
m('TotalDataTB', '%.1f' % _CAMP['tb_downloaded'])
m('TotalDataBlocks', '%d' % _CAMP['blocks_downloaded'])
m('TotalDataSearchedTB', '%.1f' % _CAMP['tb_searched'])
m('NEbExcluded', '%d' % _CAMP['blocks_never_downloaded'])

# ----------------------------------------------------- growth of the survey
# What the completed sweep added, stated once so the text can quote it.
OLD = json.load(open('frozen_export_v3.60.json'))
m('NWinReleased', '%d' % 443)
m('NEbReleased', '%d' % 104)
m('NSysReleased', '%d' % 81)
m('NWinGrowth', '%.1f' % (N / 443.0))
m('NEbGrowth', '%.1f' % (K['n_eb'] / 104.0))

with open(OUT, 'w') as fh:
    fh.write('% generated by v380_calc.py -- do not edit\n')
    fh.write('\n'.join(M) + '\n')
print('%s: %d macros' % (OUT, len(M)))
print('stage-1: %d windows, %d star-band pairs, %d systems; '
      'line-attributed %d, unattributed %d (expected %.1f, p=%.2f)'
      % (len(FL), len(by), len({r['system_id'] for r in FL}),
         len(attributed), len(unattributed), EXP,
         pois_ge(len(unattributed), EXP)))
print('out-of-sample: %d windows, %d blocks, %d flagged (expected %.1f)'
      % (len(OS), len({r['eb'] for r in OS}), len(_osf), len(OS) / 513.0))
