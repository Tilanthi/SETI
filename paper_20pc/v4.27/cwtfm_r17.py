#!/usr/bin/env python3
r"""round 721 -> survey_numbers_round721.tex, cwtfm_r17.json

THE FIGURE OF MERIT, WITH THE BANDWIDTH EACH STAR WAS ACTUALLY SEARCHED OVER.

The continuous-waveform transmitter figure of merit is
zeta EIRP / (N_star nu_rel), and that denominator is the star-bandwidth
product: the number of stars times the fractional bandwidth searched toward
each.  Writing it as a product of a star count and ONE fractional bandwidth
is exact only when every star was searched over the same band, which is true
of a single-receiver survey and is not true of an archive.  Here the union of
all the spectral windows is 48 GHz while the median system was covered over
under 2 GHz, so the product credits every system with frequencies observed
toward a different one.

The quantity the metric needs is therefore the SUM of the per-system
fractional bandwidths, each formed with that system's own midpoint:

    Sigma_i dnu_i / nu_i,

which reduces to N_star nu_rel exactly when the coverage is uniform -- that
reduction is checked here, on a synthetic uniform survey of the same stars, so
that the comparison with published values stays like for like.  The literature
values need no restatement under it, because the programmes being compared are
single-band.

Inputs: the released catalogue (per-system Class A coverage), `adopted_e90.py`
(the published per-window EIRP_90), and `occurrence_v399.json` for the Arecibo
normalisation, the literature values and the threshold rescaling, all of which
have one owner each.  NOTHING IS TYPED.

    python3 cwtfm_r17.py [--out DIR] [--drive N]       N in 1..8
"""
import csv
import re as _re
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 721

DRIVE = None
OUTDIR = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(OUTDIR, 'cwtfm_r17%s.json' % SUF)

MACROS, FAIL = [], []


def m(name, val):
    assert name.isalpha(), name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-70s %s  %s' % (label[:70], 'PASS' if ok else 'FAIL', detail))


def g(v):
    """Two significant figures; scientific above a thousand, because a figure
    of merit printed as 123675 claims five figures on a quantity known to
    one."""
    if v >= 1000:
        e = int(math.floor(math.log10(v)))
        return '%.1f\\times10^{%d}' % (v / 10.0 ** e, e)
    if v >= 10:
        return '%.0f' % v
    if v >= 1:
        return '%.1f' % v
    return '%.2f' % v


sys.path.insert(0, HERE)
import adopted_e90 as ae                                      # noqa: E402

CAT = ae.catalogue(HERE)
OCC = json.load(open(os.path.join(HERE, 'occurrence_v399.json')))
ZETA = float(OCC['zeta_AO'])
LIT_PUB = float(OCC['literature_CWTFM']['Enriquez2017'])
LIT_FIVE = float(OCC['literature_CWTFM_at_five_sigma']['Enriquez2017'])
MARGOT = float(OCC['Margot2023_CWTFM_computed_here']['CWTFM'])
MARGOT_FIVE = float(OCC['Margot2023_CWTFM_computed_here']['CWTFM_five'])
# ★ THE FIGURE OF MERIT IS A SENSITIVITY, SO IT IS FORMED OVER THE WINDOWS
# THAT CARRY ONE.  A window every channel of which lies inside the
# attribution mask constrains nothing (Sec. \ref{sec:lines}): it supplies
# neither a limit nor bandwidth a carrier could have been reported in.  Both
# terms of the product are therefore taken over the eligible windows, which
# also keeps this file's W4 comparable with the headline it checks against.
# ★ Declared residual: the bandwidth term still counts the masked channels
# inside a window that is only PARTLY masked, about six per cent of the
# Class A total.  That is a separate correction and is not made here.
A = [r for r in CAT if r['search_class'] == 'A'
     and ae.limit_eligible(r, HERE)]
E90 = ae.per_window(CAT, HERE)

print('cwtfm_r17 round %d%s' % (ROUND, '' if DRIVE is None
                                else ' (drive %d)' % DRIVE))


def union(iv):
    out = 0.0
    lo = hi = None
    for a, b in sorted((min(x, y), max(x, y)) for x, y in iv):
        if lo is None:
            lo, hi = a, b
        elif a <= hi:
            hi = max(hi, b)
        else:
            out += hi - lo
            lo, hi = a, b
    return out + (hi - lo if lo is not None else 0.0)


# ------------------------------------------------- the star-bandwidth product
BY = {}
for r in A:
    BY.setdefault(r['system_id'], []).append((float(r['flo_GHz']),
                                              float(r['fhi_GHz'])))
NU_REL = {}
for sid, iv in BY.items():
    lo = min(min(a, b) for a, b in iv)
    hi = max(max(a, b) for a, b in iv)
    NU_REL[sid] = union(iv) / (0.5 * (lo + hi))
NSYS = len(BY)
SIGMA = sum(NU_REL.values())

# the literature convention on the same stars: the whole union over the whole
# survey's midpoint, credited to every system
IV_ALL = [(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in A]
DNU = union(IV_ALL)
NU_MID = 0.5 * (min(min(a, b) for a, b in IV_ALL)
                + max(max(a, b) for a, b in IV_ALL))
UNIFORM = NSYS * DNU / NU_MID
print('  %d systems: summed fractional bandwidth %.4f against %.3f on the '
      'uniform convention, a factor %.1f' % (NSYS, SIGMA, UNIFORM,
                                             UNIFORM / SIGMA))

# ★ W1 THE REDUCTION, WHICH IS WHAT KEEPS THE COMPARISON LIKE FOR LIKE.  On a
# survey in which every star is searched over the same band -- which is what
# the programmes compared against are -- the sum IS the product, identically.
# Built by giving every system the survey's own union, so the clause is a
# property of the expression and not of this sample.
UNI_SIG = sum(DNU / NU_MID for _ in BY)
if DRIVE == 1:
    UNI_SIG *= 1.05
ck('W1 the summed fractional bandwidth reduces to the star count times one '
   'fractional bandwidth when every star is searched over the same band, so '
   'a single-band programme needs no restatement under it',
   abs(UNI_SIG / UNIFORM - 1.0) < 1e-12,
   '%.6f against %.6f' % (UNI_SIG, UNIFORM))
# ★ W2 AND THE DIRECTION.  An archive covers the typical star over less than
# the union, so the convention must OVER-credit it; a reversal would mean the
# typical system was covered more completely than the survey as a whole.
_sig = SIGMA if DRIVE != 2 else UNIFORM * 2
ck('W2 the conventional denominator exceeds the measured one, so the figure '
   'of merit it gives is the more favourable of the two',
   _sig < UNIFORM and max(NU_REL.values()) <= DNU / NU_MID + 1e-12,
   '%.4f against %.3f' % (_sig, UNIFORM))
# ★ W3 and the sum is over the systems the carrier search covers and not over
# windows, which is the error that makes it a star-bandwidth product at all.
_n = NSYS if DRIVE != 3 else NSYS + 1
ck('W3 the sum runs over the systems of the carrier experiment that carry '
   'a limit, one term each, and the systems the mask leaves nothing of are '
   'accounted for rather than missing',
   _n == int(ae._texval('NSysALim', HERE))
   and _n + int(ae._texval('NSysALost', HERE))
   == int(ae._texval('NSysClassA', HERE))
   and len(NU_REL) == NSYS,
   '%d terms against a published %s, with %s system(s) carrying no limit '
   'out of %s covered'
   % (_n, ae._texval('NSysALim', HERE), ae._texval('NSysALost', HERE),
      ae._texval('NSysClassA', HERE)))

# ★★★★ WHAT A READER CAN FORM FROM THE PER-SYSTEM TABLE, which is the only
# place the per-system coverage appears.  That table gives each system's
# BEST-WINDOW frequency beside its merged coverage, while this sum divides by
# the midpoint of the coverage SPAN, so a reader who takes the two printed
# columns gets a different -- and slightly larger -- number with no way to
# tell which is meant.  Both are computed here, the convention is named in the
# text, and the adopted one must be the smaller: a figure of merit may not
# improve on a choice of denominator.  Driven at 8.
NU_BEST = {}
for r in A:
    _s = NU_BEST.get(r['system_id'])
    _e = E90[id(r)]
    if _s is None or _e < _s[0]:
        NU_BEST[r['system_id']] = (_e, 0.5 * (float(r['flo_GHz'])
                                              + float(r['fhi_GHz'])))
SIGMA_BEST = sum(union(BY[s]) / NU_BEST[s][1] for s in BY)
if DRIVE == 8:
    SIGMA_BEST = SIGMA * 0.5         # the adopted sum no longer the smaller
ck('W3b the sum a reader forms from the per-system table, on each system '
   'own best-window frequency, is the larger of the two, so the convention '
   'named in the text is the conservative one',
   SIGMA < SIGMA_BEST and set(NU_BEST) == set(BY),
   '%.4f adopted against %.4f on the printed frequencies, over %d systems'
   % (SIGMA, SIGMA_BEST, len(NU_BEST)))

# ------------------------------------------------------------- the two EIRPs
# The bare threshold power, which is what other programmes quote, and the
# recovery completeness this paper adopts.  Per system, the best window.
def bysys(f):
    d = {}
    for r in A:
        v = f(r)
        d[r['system_id']] = min(d.get(r['system_id'], float('inf')), v)
    return sorted(d.values())


BARE = bysys(lambda r: float(r['eirp_nominal_W']))
ADOPT = bysys(lambda r: E90[id(r)])
_pub, _tol = None, None
_px = ae._texval('EirpNinetySysMedA', HERE)

_mm = _re.match(r'([\d.]+)\\times10\^\{(\d+)\}', _px.replace(' ', ''))
_pub = float(_mm.group(1)) * 10.0 ** int(_mm.group(2))
_tol = 0.5 * 10.0 ** (int(_mm.group(2)) - 1)
_med = st.median(ADOPT) if DRIVE != 4 else _pub * 2
ck('W4 the figure of merit is built on the sensitivity the paper prints, so '
   'a reader can reproduce it from the published numbers',
   abs(_med - _pub) <= _tol,
   '%.4g W against a published %s W' % (_med, _px))


def cwtfm(eirp, denom):
    return ZETA * eirp / denom


VALS = dict(
    bare_worst=cwtfm(BARE[-1], SIGMA), bare_med=cwtfm(st.median(BARE), SIGMA),
    adopt_worst=cwtfm(ADOPT[-1], SIGMA),
    adopt_med=cwtfm(st.median(ADOPT), SIGMA),
    bare_worst_uniform=cwtfm(BARE[-1], UNIFORM),
    bare_med_uniform=cwtfm(st.median(BARE), UNIFORM),
    adopt_med_uniform=cwtfm(st.median(ADOPT), UNIFORM))
for k in sorted(VALS):
    print('  %-20s %.4g' % (k, VALS[k]))

# ★ W5 THE SIZE AND THE SIGN OF THE CHANGE, STATED MECHANICALLY.  Measuring
# the denominator rather than assuming it uniform makes every figure of merit
# here WORSE, by the same factor in all of them, and that factor is the
# bandwidth ratio and nothing else.  A correction quoted without its direction
# is how a less favourable number gets reported as a refinement.
_fac = sorted(VALS['adopt_med'] / VALS['adopt_med_uniform'] for _ in (0,))[0]
_fac2 = VALS['bare_med'] / VALS['bare_med_uniform']
if DRIVE == 5:
    _fac = 1.0 / _fac
ck('W5 the measured denominator makes every figure of merit here less '
   'favourable, by exactly the bandwidth ratio and by the same factor in '
   'each',
   _fac > 1.0 and abs(_fac / (UNIFORM / SIGMA) - 1.0) < 1e-9
   and abs(_fac2 / _fac - 1.0) < 1e-9,
   'x%.2f on both the threshold and the completeness convention' % _fac)
# ★ W6 WHERE THIS SURVEY SITS.  The sentence the Discussion carries explains a
# gap, so the gap has to be there: ours above the comparison programmes, and
# the ratio to the rescaled value larger than to the published one, because
# the rescale makes them deeper and ours does not move.
#
# ★★★ AND BOTH SIDES OF THE RATIO ARE THE SAME KIND OF NUMBER.  The metric is
# linear in the power it is formed on, so a ratio of two figures of merit says
# something about haystack and depth only if both are formed at a threshold of
# the same kind.  Every published value compared here is a BARE threshold,
# while this survey's EIRP_90 is a COMPLETENESS -- measured here and not
# established on the same basis elsewhere, which is why Section 2 compares
# nominal thresholds and draws the bare value as the filled symbol.  Forming
# the ratio on EIRP_90 divided a completeness by a threshold and inflated the
# gap by the completeness factor, which is not a difference between the
# experiments.  The numerator is therefore the BARE median, and the two ratios
# differ only in the threshold the denominator is quoted at.
_r_pub = VALS['bare_med'] / LIT_PUB
_r_five = VALS['bare_med'] / LIT_FIVE
if DRIVE == 6:
    _r_five = _r_pub / 2
ck('W6 this survey still sits far above the centimetre-band programmes on a '
   'ratio of two bare thresholds, and further above them once theirs is put '
   'on the common footing',
   VALS['bare_med'] > LIT_PUB and _r_five > _r_pub and MARGOT < LIT_PUB,
   'x%.3g published, x%.3g rescaled' % (_r_pub, _r_five))
_mix = VALS['adopt_med'] / VALS['bare_med']
if DRIVE == 9:
    _r_five = VALS['adopt_med'] / LIT_FIVE
ck('W6b neither published ratio mixes a completeness with a threshold: both '
   'are formed on the bare median, which is the completeness value divided '
   'by the completeness factor this survey measures',
   abs(_r_pub * _mix / (VALS['adopt_med'] / LIT_PUB) - 1.0) < 1e-9
   and abs(_r_five - VALS['bare_med'] / LIT_FIVE) < 1e-9 * _r_five,
   'completeness factor x%.2f; published ratio x%.3g bare against x%.3g on '
   'EIRP90' % (_mix, _r_pub, VALS['adopt_med'] / LIT_PUB))
# ★ W7 AND THE SENTENCE THAT ATTRIBUTED THE WHOLE GAP TO THE STAR-BANDWIDTH
# PRODUCT IS MEASURED RATHER THAN REPEATED.  The metric is a ratio of two
# ratios, so the gap splits exactly into a haystack term and a depth term:
#
#   log(ours/theirs) = log(Sigma_theirs/Sigma_ours) + log(E_ours/E_theirs)
#
# and the two have to be compared before either can be called dominant.  The
# comparison programme's own star count and band come from the literature
# record that Table 1 and Figure 1 are both drawn from, and its threshold
# power is taken from its own published figure of merit rather than from a
# second quoted number, so the decomposition is self-consistent by
# construction and the identity below is a real one.
import make_fig_context_v410 as _ctx                          # noqa: E402
_lab = _ctx.LIT['enriquez2017']['label']
_nlit = float(_re.search(r'([\d\s]+) stars', _lab).group(1).replace(' ', ''))
_flo, _fhi = _ctx.LIT['enriquez2017']['freq_GHz']
_nurel_lit = (_fhi - _flo) / (0.5 * (_fhi + _flo))
SIG_LIT = _nlit * _nurel_lit
E_LIT = LIT_PUB * SIG_LIT / ZETA
# ★ the comparison threshold on the common footing of five, which is the one
#   the decomposed ratio is formed against: the figure of merit is linear in
#   the power, so rescaling it rescales the threshold behind it by the same
#   factor.
E_LIT_FIVE = LIT_FIVE * SIG_LIT / ZETA
_share = math.log10(_r_five)
_band_dex = math.log10(SIG_LIT / SIGMA)
_eirp_dex = math.log10(st.median(BARE) / E_LIT_FIVE)
if DRIVE == 7:
    _eirp_dex = _share
print('  the gap is %.3f decades: %.3f of haystack and %.3f of depth '
      '(%.0f stars x %.3f against %.3f; %.3g against %.3g W)'
      % (_share, _band_dex, _eirp_dex, _nlit, _nurel_lit, SIGMA,
         st.median(BARE), E_LIT_FIVE))
ck('W7 the gap splits exactly into a haystack term and a depth term, and '
   'neither of them is the whole of it, so it cannot be attributed to the '
   'star-bandwidth product alone',
   abs(_band_dex + _eirp_dex - _share) < 1e-9
   and 0.2 < _band_dex / _share < 0.8,
   '%.3f + %.3f = %.3f decades' % (_band_dex, _eirp_dex,
                                   _band_dex + _eirp_dex))
# ★★★ W7b AND IT IS THE PRINTED FIGURES A READER ADDS, NOT THESE ONES.  An
# exact identity between three floats is not what reaches the page: the page
# carries two rounded decade counts beside a rounded ratio, and a reader who
# adds them has to land on the ratio.  At one decimal place these terms print
# as 2.8 and 2.6 against a ratio of 2.2e5 = 10^5.34, so the printed sum is
# 10^5.4 -- out by a quarter, on arithmetic the sentence invites.  That is the
# defect the paper is being corrected for, one convention further up; a gate
# on the floats alone cannot see it.  So the decade counts print at the
# precision where they close, and this clause holds them there: it reads the
# EMITTED STRINGS, so widening `_DEX` back to '%.1f' fails the build instead
# of shipping a sum that does not add up.
_DEX = '%.2f'


def _printed(txt):
    """The float a reader reads off `g()`'s 'a.b\\times10^{c}' form."""
    _m = _re.match(r'([\d.]+)\\times10\^\{(-?\d+)\}$', txt)
    return float(_m.group(1)) * 10.0 ** int(_m.group(2)) if _m else float(txt)


_pb, _pe = float(_DEX % _band_dex), float(_DEX % _eirp_dex)
_pr = _printed(g(_r_five))
if DRIVE == 11:
    _DEX = '%.1f'
    _pb, _pe = float(_DEX % _band_dex), float(_DEX % _eirp_dex)
_closure = 10.0 ** (_pb + _pe) / _pr
ck('W7b the decade counts AS PRINTED sum to the ratio AS PRINTED, so the '
   'arithmetic the sentence invites closes to better than five per cent',
   abs(_closure - 1.0) < 0.05,
   'printed %s + %s decades = x%.3g against a printed ratio of x%.3g '
   '(%+.1f per cent)' % (_DEX % _band_dex, _DEX % _eirp_dex,
                         10.0 ** (_pb + _pe), _pr, 100.0 * (_closure - 1.0)))

m('CwNSys', '%d' % NSYS)
m('CwSigma', '%.2f' % SIGMA)
m('CwSigmaBest', '%.2f' % SIGMA_BEST)
m('CwUniform', '%.1f' % UNIFORM)
m('CwRatio', '%.1f' % (UNIFORM / SIGMA))
# ★ NOT PUBLISHED HERE: the median per-system coverage.  The Discussion
# already prints it as \SysUnionAMed, and this file's own median of the
# same distribution differs in the last figure because one takes the upper
# of the two middle values and the other averages them.  Two medians of one
# distribution under two names is the defect this round is correcting
# elsewhere; the existing macro is cited instead.
m('CwBareWorst', g(VALS['bare_worst']))
m('CwBareMed', g(VALS['bare_med']))
m('CwAdoptWorst', g(VALS['adopt_worst']))
m('CwAdoptMed', g(VALS['adopt_med']))
m('CwLitEnriquez', '%.2f' % LIT_PUB)
m('CwLitEnriquezFive', '%.2f' % LIT_FIVE)
m('CwLitMargot', '%.2f' % MARGOT)
m('CwLitMargotFive', '%.3f' % MARGOT_FIVE)
m('CwRatioEnriquez', g(_r_pub))
m('CwRatioEnriquezFive', g(_r_five))
m('CwTransRate', '%.1f' % (1.0 / SIGMA))
m('CwBandDex', _DEX % _band_dex)
m('CwEirpDex', _DEX % _eirp_dex)

print('\nassertions failed: %d %s' % (len(FAIL), FAIL))
if FAIL and DRIVE is None:
    raise SystemExit('cwtfm_r17: %d assertion(s) failed: %s' % (len(FAIL), FAIL))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    fh.write('\n'.join(sorted(MACROS)) + '\n')
json.dump(dict(generated_by=os.path.basename(__file__), round=ROUND,
               drive=DRIVE, n_systems=NSYS, sigma_nu_rel=SIGMA,
               uniform_product=UNIFORM, ratio=UNIFORM / SIGMA,
               union_GHz=DNU, nu_mid_GHz=NU_MID,
               eirp_bare=dict(median=st.median(BARE), worst=BARE[-1]),
               eirp_adopted=dict(median=st.median(ADOPT), worst=ADOPT[-1]),
               cwtfm=VALS, literature=dict(enriquez=LIT_PUB,
                                           enriquez_five=LIT_FIVE,
                                           margot=MARGOT,
                                           margot_five=MARGOT_FIVE),
               gap_dex=dict(total=_share, bandwidth=_band_dex,
                            depth=_eirp_dex),
               failures=FAIL),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('\n%d macros -> %s' % (len(MACROS), os.path.basename(OUT)))
