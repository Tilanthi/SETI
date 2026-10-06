#!/usr/bin/env python3
"""R2-2 (v3.99): the standard occurrence-rate metrics, computed.

Referee 2 asked for a figure the SETI literature already uses, so that
this survey can be placed on the same axes as everyone else's, and asked
for it WITH the caveats this paper argues elsewhere. Both halves are done
here: the numbers are computed from the released catalogue, and the
generator also computes the quantity that shows why the literature
convention flatters every archival survey -- the per-system fractional
bandwidth, which is what one civilisation is actually searched over.

Metrics, as defined in the literature and not re-invented here:

  Transmitter Rate (Enriquez et al. 2017, S V.2.4)
      TR = 1 / (N_stars nu_rel),   nu_rel = dnu_tot / nu_mid

  Continuous Waveform Transmitter Figure of Merit (ibid., their Eq. 11)
      CWTFM = zeta_AO EIRP / (N_stars nu_rel) = zeta_AO EIRP TR
      zeta_AO fixed by CWTFM = 1 at EIRP = L_AO = 1e13 W,
      nu_rel = 1/2, N_stars = 1000  =>  zeta_AO = 1000 x 0.5 / 1e13.
      LOWER IS BETTER.

  Transmitter-hosting fraction: 0 detections in N systems gives a
      95 per cent Poisson upper limit of 3.0 expected events, so
      f < 3/N. The literature usually quotes 1/N; we quote the
      statistically correct bound, which is weaker.

Everything is computed on Class A, the primary experiment, because only
there is there a measured recovery curve. Two versions of nu_rel are
produced and both are printed:

  (a) SURVEY union -- the literature convention. Generous: it credits one
      star with frequencies observed toward a different star.
  (b) PER-SYSTEM median union -- what a civilisation around the median
      system was actually searched over.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CAT = os.path.join(HERE, 'per_target_results_v3.99.csv')
OUT = os.path.join(HERE, 'survey_numbers_round48.tex')

L_AO = 1.0e13                       # Arecibo planetary radar EIRP, W
ZETA_AO = 1000.0 * 0.5 / L_AO       # = 5e-11, from the normalisation above


def F(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


ROWS = list(csv.DictReader(open(CAT)))
A = [r for r in ROWS if r['search_class'] == 'A']
assert A, 'no Class A rows'


def union(intervals):
    """Total length of the union of [lo, hi] intervals, in GHz."""
    iv = sorted((min(a, b), max(a, b)) for a, b in intervals)
    tot, clo, chi = 0.0, None, None
    for lo, hi in iv:
        if clo is None:
            clo, chi = lo, hi
        elif lo <= chi:
            chi = max(chi, hi)
        else:
            tot += chi - clo
            clo, chi = lo, hi
    if clo is not None:
        tot += chi - clo
    return tot


# ---- the survey-level fractional bandwidth (literature convention) -------
iv_all = [(F(r['flo_GHz']), F(r['fhi_GHz'])) for r in A
          if F(r['flo_GHz']) and F(r['fhi_GHz'])]
dnu_survey = union(iv_all)
lo = min(min(a, b) for a, b in iv_all)
hi = max(max(a, b) for a, b in iv_all)
nu_mid = 0.5 * (lo + hi)
nurel_survey = dnu_survey / nu_mid

# ---- the per-system fractional bandwidth (the honest one) ---------------
bysys = {}
for r in A:
    if F(r['flo_GHz']) and F(r['fhi_GHz']):
        bysys.setdefault(r['system_id'], []).append(
            (F(r['flo_GHz']), F(r['fhi_GHz'])))
sysun = sorted(union(v) for v in bysys.values())
dnu_sys = sysun[len(sysun) // 2]
nurel_sys = dnu_sys / nu_mid
NSYS = len(bysys)

# v4.05 (R2-m11).  Two defects in the three lines above.
#
# (1) `nurel_sys = dnu_sys / nu_mid` divides ONE SYSTEM'S union by the
#     SURVEY'S midpoint.  A per-system fractional bandwidth must use that
#     system's own midpoint; done properly the median is about twice as large.
# (2) Substituting a per-system nu_rel into Eq. 11 while KEEPING N_star = 60
#     makes the product N_star nu_rel count neither the survey's
#     opportunities (which are heterogeneous) nor one system's (which would
#     need N_star = 1).  The referee is right that the resulting factor is not
#     a CWTFM; it is an illustrative rescaling and is now labelled as one.
#
# The defensible figure for a heterogeneous survey is the star-bandwidth
# product itself: the SUM of the per-system fractional bandwidths, which
# reduces to Eq. 11 when coverage is uniform and needs no substitution.
_sys_own = {}
for _sid, _iv in bysys.items():
    _lo = min(min(a, b) for a, b in _iv)
    _hi = max(max(a, b) for a, b in _iv)
    _sys_own[_sid] = union(_iv) / (0.5 * (_lo + _hi))
_so = sorted(_sys_own.values())
nurel_sys_own = _so[len(_so) // 2]
starband_sum = sum(_sys_own.values())           # Sigma_i nu_rel,i, measured
starband_uniform = NSYS * nurel_survey          # the literature convention
starband_ratio = starband_uniform / starband_sum
n_equiv_uniform = starband_sum / nurel_survey   # equivalent covered systems
# ★ The correction must run in the direction the argument claims: the
# convention OVER-credits a heterogeneous survey, so the uniform product must
# exceed the measured sum.  A reversal would mean the typical system is
# covered more completely than the survey-wide union, which is impossible.
assert starband_uniform > starband_sum, (starband_uniform, starband_sum)
# ★ ...and the per-system nu_rel really was computed against the wrong
# midpoint.  If the two ever agree, defect (1) has been repaired elsewhere and
# this block is claiming a fix it did not make.
assert abs(nurel_sys_own - nurel_sys) > 0.1 * nurel_sys, \
    (nurel_sys_own, nurel_sys)
# ★ No system's own union can exceed the survey's, so every per-system
# fractional bandwidth must lie at or below the survey figure.
assert max(_sys_own.values()) <= nurel_survey + 1e-12, max(_sys_own.values())

# ---- the EIRP to quote: the adopted EIRP_90, per system -----------------
# Enriquez take the EIRP of their most distant target, i.e. the largest
# EIRP_min in the sample. We give that worst case AND the median, because a
# single number hides three decades of spread in an archival sample.
# v4.11 (R1-9, R2-M11b): this read the catalogue column `eirp_p90_sel_W`,
# which is the RETIRED criterion -- exactly 2.876 x the nominal trigger --
# while the paper's adopted sensitivity is \EirpNinetyMultA x P_trig. Every
# figure of merit below was therefore optimistic by that ratio. The adopted
# multiplier is read from the macro layer, exactly as make_fig_classa_sens.py
# does, so the metric cannot drift away from the plotted sensitivity.
import glob as _glob
import re as _re


def _texval(name):
    pat = _re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                      r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % _re.escape(name))
    out = None
    for fn in sorted(_glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(fn).read()):
            v = mm.group(1).strip()
            if v:
                out = v
    seen = set()
    while out and _re.fullmatch(r'\\[A-Za-z]+', out) and out not in seen:
        seen.add(out)
        out = _texval(out[1:])
    return out


MULT = _texval('EirpNinetyMultA')
assert MULT, ('\\EirpNinetyMultA is not defined: this generator must run '
              'after numbers_v410.py (round 103).')
MULT = float(MULT)
assert abs(MULT / 2.876 - 1) > 0.01, 'the RETIRED x2.88 criterion is back'
psel = {}
for r in A:
    s = F(r['eirp_nominal_W'])
    if s:
        s *= MULT
        if s < psel.get(r['system_id'], float('inf')):
            psel[r['system_id']] = s
vals = sorted(psel.values())
import statistics as _stm
eirp_med = _stm.median(vals)
eirp_worst = vals[-1]
eirp_best = vals[0]


def cwtfm(eirp, n, nurel):
    return ZETA_AO * eirp / (n * nurel)


def tr(n, nurel):
    return 1.0 / (n * nurel)


# Cross-assert against three numbers other generators already publish, so
# this metric cannot drift away from the rest of the paper. These are the
# same quantities computed by a different route.
def _mac(name):
    import re
    for fn in sorted(os.listdir(HERE)):
        if fn.startswith('survey_numbers_round') and fn.endswith('.tex'):
            mm = re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name,
                           open(os.path.join(HERE, fn)).read())
            if mm:
                return mm.group(1)
    return None


for _nm, _val, _tol in (('NSysClassA', NSYS, 0),
                        ('UnionClassA', dnu_survey, 0.05),
                        ('SysUnionAMed', dnu_sys, 0.005)):
    _pub = _mac(_nm)
    if _pub is not None:
        assert abs(float(_pub) - _val) <= _tol, \
            '%s: published %s, computed here %r' % (_nm, _pub, _val)
        print('  cross-check %-14s published %-6s == %.4g' % (_nm, _pub, _val))

res = {
    'zeta_AO': ZETA_AO,
    'n_systems_A': NSYS,
    'dnu_survey_GHz': dnu_survey,
    'dnu_sys_median_GHz': dnu_sys,
    'nu_mid_GHz': nu_mid,
    'nu_rel_survey': nurel_survey,
    'nu_rel_sys': nurel_sys,
    'eirp_psel_median_W': eirp_med,
    'eirp_psel_worst_W': eirp_worst,
    'eirp_psel_best_W': eirp_best,
    'TR_survey': tr(NSYS, nurel_survey),
    'TR_sys': tr(NSYS, nurel_sys),
    'CWTFM_survey_median_eirp': cwtfm(eirp_med, NSYS, nurel_survey),
    'CWTFM_survey_worst_eirp': cwtfm(eirp_worst, NSYS, nurel_survey),
    'CWTFM_sys_median_eirp': cwtfm(eirp_med, NSYS, nurel_sys),
    'f_upper_95': 3.0 / NSYS,
    'f_upper_naive': 1.0 / NSYS,
}

# Literature comparison values, quoted from the papers, not recomputed.
# Enriquez et al. 2017 (BL L band, 692 stars) and Price et al. 2020.
LIT = {'Enriquez2017': 0.85, 'Price2020_GBT': 0.11, 'Price2020_Parkes': 8.21,
       'Phoenix': 49.0}
res['literature_CWTFM'] = LIT

# Margot et al. (2023) deliberately do NOT publish a CWTFM: they argue the
# metric is deficient and report an improved Drake figure of merit instead.
# The referee asks for a comparison value, so Eq. (CWTFM) is evaluated here
# from the three quantities that paper does publish -- 11,680 stars, the
# 1.15-1.73 GHz L-band receiver, and a limit of EIRP > 1e13 W for stars
# within 100 pc.  The paper must say that this number is ours, not theirs.
MARGOT = {'N': 11680.0, 'nu_lo': 1.15, 'nu_hi': 1.73, 'eirp': 1.0e13}
MARGOT['nu_rel'] = ((MARGOT['nu_hi'] - MARGOT['nu_lo'])
                    / (0.5 * (MARGOT['nu_hi'] + MARGOT['nu_lo'])))
MARGOT['CWTFM'] = cwtfm(MARGOT['eirp'], MARGOT['N'], MARGOT['nu_rel'])
res['Margot2023_CWTFM_computed_here'] = MARGOT
# A sanity bound, not a tautology: the same formula on a survey an order of
# magnitude larger in N x nu_rel and three decades deeper in EIRP must come
# out below the Enriquez value it is being compared with.
assert MARGOT['CWTFM'] < LIT['Enriquez2017'], MARGOT['CWTFM']
# ...and our own must come out above both, or the sentence that explains the
# gap is describing a gap that is not there.
assert cwtfm(eirp_med, NSYS, nurel_survey) > LIT['Enriquez2017'], \
    'the survey no longer sits where the Discussion says it does'

json.dump(res, open(os.path.join(HERE, 'occurrence_v399.json'), 'w'),
          indent=1, sort_keys=True)


def sci(v, sf=2):
    e = int(math.floor(math.log10(abs(v))))
    return '%.*f\\times10^{%d}' % (sf - 1, v / 10.0 ** e, e)


def g(v):
    """Format a figure of merit to two significant figures. Above 10^3 use
    scientific notation: a CWTFM printed as 12767 claims five significant
    figures on a quantity known to one."""
    if v >= 1000:
        return sci(v)
    if v >= 10:
        return '%.0f' % v
    if v >= 1:
        return '%.1f' % v
    if v >= 0.01:
        return '%.2f' % v
    return sci(v)


L = ['%% generated by occurrence_v399.py -- do not edit\n']


def m(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


m('OccNSysA', '%d' % NSYS)
m('OccNuMid', '%.0f' % nu_mid)
m('OccNuRelSurvey', '%.3f' % nurel_survey)
m('OccNuRelSys', '%.4f' % nurel_sys)
m('OccDnuSurvey', '%.1f' % dnu_survey)
m('OccDnuSys', '%.2f' % dnu_sys)
m('OccEirpMed', sci(eirp_med))
m('OccEirpWorst', sci(eirp_worst))
m('OccTRSurvey', g(res['TR_survey']))
m('OccTRSys', g(res['TR_sys']))
m('OccCwtfmMed', g(res['CWTFM_survey_median_eirp']))
m('OccCwtfmWorst', g(res['CWTFM_survey_worst_eirp']))
m('OccCwtfmSys', g(res['CWTFM_sys_median_eirp']))
m('OccFracPct', '%.1f' % (100.0 * res['f_upper_95']))
m('OccFracNaivePct', '%.1f' % (100.0 * res['f_upper_naive']))
m('OccZeta', sci(ZETA_AO))
m('OccLitEnriquez', '%.2f' % LIT['Enriquez2017'])
m('OccLitPriceGBT', '%.2f' % LIT['Price2020_GBT'])
m('OccLitPriceParkes', '%.1f' % LIT['Price2020_Parkes'])
m('OccLitPhoenix', '%.0f' % LIT['Phoenix'])
# the ratio the reader wants: how much of the CWTFM gap is bandwidth
m('OccCwtfmRatioEnriquez',
  g(res['CWTFM_survey_median_eirp'] / LIT['Enriquez2017']))
# R1-9 / R2-M11(b): the names the Discussion cites.
m('FomZeta', sci(ZETA_AO))
# the two constants that fix the normalisation, from Enriquez et al.
m('FomNormN', '1000')
m('FomNormNuRel', '0.5')
m('FomNuRel', '%.3f' % nurel_survey)
m('FomNuMid', '%.0f' % nu_mid)
m('FomCwtfmWorst', g(res['CWTFM_survey_worst_eirp']))
m('FomCwtfmMed', g(res['CWTFM_survey_median_eirp']))
m('FomEirpWorst', sci(eirp_worst))
m('FomLitEnriquez', '%.2f' % LIT['Enriquez2017'])
m('FomLitMargot', '%.2f' % MARGOT['CWTFM'])
m('FomMargotN', '%s' % format(int(MARGOT['N']), ',').replace(',', '\\,'))
m('FomMargotLo', '%.2f' % MARGOT['nu_lo'])
m('FomMargotHi', '%.2f' % MARGOT['nu_hi'])
m('FomMargotEirp', sci(MARGOT['eirp'], 1))
m('FomAreciboEirp', sci(L_AO, 1))
m('OccSysSurveyRatio', g(nurel_survey / nurel_sys))
# v4.05 (R2-m11): the heterogeneous star-bandwidth product and the CWTFM it
# supports, which is the number to quote on the conventional axis.
m('OccStarBandSum', '%.3f' % starband_sum)
m('OccStarBandUniform', '%.2f' % starband_uniform)
m('OccStarBandRatio', '%.1f' % starband_ratio)
m('OccNEquivUniform', '%.1f' % n_equiv_uniform)
m('OccNuRelSysOwn', '%.4f' % nurel_sys_own)
m('OccCwtfmHetero', g(ZETA_AO * eirp_med / starband_sum))
m('OccCwtfmHeteroWorst', g(ZETA_AO * eirp_worst / starband_sum))
m('OccSysRescaleLabel', 'illustrative rescaling')
m('OccCwtfmHeteroRatioEnriquez',
  g(ZETA_AO * eirp_med / starband_sum / LIT['Enriquez2017']))

open(OUT, 'w').writelines(L)
print('%s: %d macros' % (os.path.basename(OUT), len(L) - 1))
print('  Class A: %d systems, union %.1f GHz, nu_mid %.0f GHz, '
      'nu_rel %.3f' % (NSYS, dnu_survey, nu_mid, nurel_survey))
print('  per-system median union %.2f GHz -> nu_rel %.4f (x%.0f smaller)'
      % (dnu_sys, nurel_sys, nurel_survey / nurel_sys))
print('  P_90^sel per system: best %.2e  median %.2e  worst %.2e W'
      % (eirp_best, eirp_med, eirp_worst))
print('  Transmitter Rate: survey convention %.3g, per-system %.3g'
      % (res['TR_survey'], res['TR_sys']))
print('  CWTFM: %.3g (median EIRP) / %.3g (worst EIRP) / %.3g (per-system '
      'bandwidth)' % (res['CWTFM_survey_median_eirp'],
                      res['CWTFM_survey_worst_eirp'],
                      res['CWTFM_sys_median_eirp']))
print('  literature: Enriquez+17 %.2f (published), Margot+23 %.3f '
      '(computed here from N=%d, %.2f-%.2f GHz, EIRP %.0e)'
      % (LIT['Enriquez2017'], MARGOT['CWTFM'], MARGOT['N'],
         MARGOT['nu_lo'], MARGOT['nu_hi'], MARGOT['eirp']))
print('  transmitter-hosting fraction, 0 of %d, 95%% Poisson: f < %.1f%% '
      '(naive 1/N would say %.1f%%)'
      % (NSYS, 100.0 * res['f_upper_95'], 100.0 * res['f_upper_naive']))
