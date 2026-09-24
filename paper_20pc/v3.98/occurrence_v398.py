#!/usr/bin/env python3
"""R2-2 (v3.98): the standard occurrence-rate metrics, computed.

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
CAT = os.path.join(HERE, 'per_target_results_v3.98.csv')
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

# ---- the EIRP to quote: the headline P_90^sel, per system --------------
# Enriquez quote the EIRP of their most distant target, i.e. the survey's
# worst case. We give the worst case AND the median, because a single
# number hides two decades of spread in an archival sample.
psel = {}
for r in A:
    v, c = F(r['eirp_p90_W']), F(r['ctrl_max_snr'])
    if v and c:
        s = v * c / 5.0
        if s < psel.get(r['system_id'], float('inf')):
            psel[r['system_id']] = s
vals = sorted(psel.values())
eirp_med = vals[len(vals) // 2]
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

json.dump(res, open(os.path.join(HERE, 'occurrence_v398.json'), 'w'),
          indent=1, sort_keys=True)


def sci(v):
    e = int(math.floor(math.log10(abs(v))))
    return '%.1f\\times10^{%d}' % (v / 10.0 ** e, e)


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


L = ['%% generated by occurrence_v398.py -- do not edit\n']


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
m('OccSysSurveyRatio', g(nurel_survey / nurel_sys))

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
print('  literature: Enriquez+17 %.2f, Price+20 GBT %.2f / Parkes %.2f, '
      'Phoenix %.0f' % (LIT['Enriquez2017'], LIT['Price2020_GBT'],
                        LIT['Price2020_Parkes'], LIT['Phoenix']))
print('  transmitter-hosting fraction, 0 of %d, 95%% Poisson: f < %.1f%% '
      '(naive 1/N would say %.1f%%)'
      % (NSYS, 100.0 * res['f_upper_95'], 100.0 * res['f_upper_naive']))
