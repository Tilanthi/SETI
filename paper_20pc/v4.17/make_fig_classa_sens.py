#!/usr/bin/env python3
r"""Class A sensitivity and temporal coverage, the two things a reader
needs in order to judge what the primary experiment could have found.

Referee 1 asks for the cumulative number of independent systems against
P_90, on the ground that a deepest and a median EIRP do not describe a
survey whose thresholds span two decades. Referee 1 also asks for the
distribution of independent epochs per system, because recurrence is part
of the paper's own definition of a confirmed technosignature and most
systems cannot supply it.

Both are properties of the released catalogue, so both are drawn from it.

Panel (a): cumulative independent systems whose best Class A window has
           P_90 at or below the abscissa.
Panel (b): how many systems have 1, 2, 3, 4 or more independent execution
           blocks, and the time baseline those blocks span.

Writes figures/classa_sensitivity.pdf and the macros the text quotes.
"""
import csv, glob, json, math, os, re, collections

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(os.path.abspath(__file__)))
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'font.family': 'serif', 'font.serif': ['DejaVu Serif'],
                     'mathtext.fontset': 'dejavuserif'})

CAT = 'per_target_results_v3.99.csv'
ROWS = list(csv.DictReader(open(CAT)))


def texval(name):
    """LAST literal definition of \\name, across new/renew/providecommand.

    v4.10: the old reader matched \\newcommand only and returned the FIRST
    file's value.  Both are wrong here.  \\BudTotalLo is written
    \\providecommand{..}{}\\renewcommand{..}{39} and was invisible to it
    (texval returned None, so the band could never be drawn from the budget
    the caption cites), and round103 renames the retired sensitivity family
    with \\renewcommand, so a first-match reader returns the superseded value.
    Definitions whose body is another macro are skipped, so an alias never
    masks a number.
    """
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % re.escape(name))
    out = None
    for f in sorted(glob.glob('survey_numbers*.tex')):
        for m in pat.finditer(open(f).read()):
            v = m.group(1).strip()
            if v:
                out = v
    # round103 retires a superseded name by ALIASING it to its replacement, so
    # the last definition of \BudTotalLo is the single token \EirpNinetyPctLo.
    # Follow the alias rather than reporting "not defined": an alias is the
    # manuscript saying where the number now lives.
    seen = set()
    while out and re.fullmatch(r'\\[A-Za-z]+', out) and out not in seen:
        seen.add(out)
        out = texval(out[1:])
    return out


def F(x):
    return None if x in ('', None) else float(x)


# v4.00 (R2-M2, R1-4): both curves are now the END-TO-END measurement.
# The superseded factor came from a campaign that injected into retained
# spectra after the baseline step; it is kept nowhere. Both ratios multiply
# the NOMINAL trigger, because a measured end-to-end ratio already carries
# the spectral response -- multiplying eirp_eff_total_W, which is
# P_trig C_resp C_smear, would count that response twice.
import json as _json
_m3a = {x['stratum']: x for x in
        _json.load(open('m3a_result_v400.json'))['strata']}
P90FAC = _m3a['fine (<1 MHz)']['P90_over_trigger']          # through the gate
TRIGFAC = None
_lad = _m3a['fine (<1 MHz)']['ladder']
for _j in range(1, len(_lad)):
    _a, _b = _lad[_j - 1], _lad[_j]
    if _a['frac_trig_only'] < 0.9 <= _b['frac_trig_only']:
        _w = (0.9 - _a['frac_trig_only']) / (_b['frac_trig_only'] - _a['frac_trig_only'])
        TRIGFAC = _a['amp_over_trig'] + _w * (_b['amp_over_trig'] - _a['amp_over_trig'])
        break
assert TRIGFAC and P90FAC > TRIGFAC, (
    'the gate cannot make a carrier easier to recover: trigger %.2f, '
    'through the gate %.2f' % (TRIGFAC or -1, P90FAC))

# ------------------------------------------------ (a) Class A sensitivity
# R1-1: the survey's sensitivity is the power that passes the COMPLETE
# automated selection -- trigger AND the window's own control-ring gate --
# so that is what this figure leads with. P_90, the trigger completeness,
# is plotted beside it because the gap between them is itself the point.
# v4.10 (figures): the PLOTTED sensitivity is the adopted one,
# EIRP_90 = \EirpNinetyMultA x P_trig, computed here from the multiplier the
# injection campaign measured and the window's own nominal trigger power.
# The catalogue column eirp_p90_sel_W is NOT read: it carries the RETIRED
# criterion, exactly 2.876 x the nominal trigger in Class A, and the paper
# now quotes one sensitivity only.  eirp_p90_W is still read, but only for
# the PNinetySys* macros the reproducer checks; it is not drawn.
_m = texval('EirpNinetyMultA')
assert _m, ('\\EirpNinetyMultA is not defined yet: make_fig_classa_sens.py '
            'MUST run after numbers_v410.py (round 103), which is where the '
            'adopted multiplier and \\EirpNinetySys*A live.  In make_all.sh it '
            'currently runs four lines earlier.')
# The PLOTTED multiplier is the macro, not the campaign record: the adopted
# value is the control-maximum-stratified one (4.42 at round 103), which is
# NOT the campaign's own pooled 90 per cent point (5.70).  P90FAC is kept only
# for the gate-vs-trigger assertion above.  The invariant enforced here is
# that the plotted value is not the RETIRED x2.88.
P90FAC = float(_m)
assert abs(P90FAC / 2.88 - 1) > 0.01, (
    'this figure would plot the RETIRED x2.88 sensitivity')

import adopted_e90 as _ae
_E90 = _ae.per_window(ROWS, os.path.dirname(os.path.abspath(__file__)))
best, bestsel = {}, {}
for r in ROWS:
    if r['resolution_class'] != 'fine':
        continue
    e = F(r['eirp_p90_W'])
    # ★★ v4.11: WAS `P90FAC * eirp_nominal_W`, the BLANKET multiplier, which
    # is the completeness of no window.  The adopted per-window EIRP_90 is
    # stratified on the window's own control maximum and then corrected for
    # the omitted annual parallax; this panel's own assertion against
    # \EirpNinetySysMedA caught the difference and stopped the build.
    # `adopted_e90.py` owns the formation.
    sel = _E90[id(r)]
    if e is None or sel is None:
        continue
    s = r['system_id']
    if s not in best or e < best[s]:
        best[s] = e
    if s not in bestsel or sel < bestsel[s]:
        bestsel[s] = sel
p90 = np.array(sorted(best.values()))
psel = np.array(sorted(bestsel.values()))
cum = np.arange(1, p90.size + 1)
cumsel = np.arange(1, psel.size + 1)

# ------------------------------------------------ (b) epochs per system
ebs = collections.defaultdict(set)
for r in ROWS:
    ebs[r['system_id']].add(r['eb'])
nep = collections.Counter(min(len(v), 5) for v in ebs.values())

# ★★★★ PANEL (b) IS NOW DRAWN ON SAME-FREQUENCY COVERAGE, WHICH IS WHAT
#      "confirmation completeness" MEANS.  It used to group systems by the
#      longest separation between ANY two of their execution blocks, and a
#      second block at a frequency the first did not cover confirms nothing:
#      the panel therefore drew 39 systems as confirmable and 21 as not,
#      beside a text and a ledger that give 37 and 23.  A panel titled
#      "confirmation completeness" is read before its caption, so the picture
#      is the thing that had to change rather than the words beneath it.
#
#      The construction is the one in cover_v412.py, which publishes
#      \RcConfSysDay and \RcConfSysYr: a system is confirmable above a
#      separation if some frequency interval of it is covered by two blocks
#      demonstrably more than that many days apart.  It is reproduced here
#      rather than imported, and the assertions below require it to return
#      exactly the published counts, so the two cannot drift apart.
import epochs_r14 as _epr


def _ivA(rows):
    return [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
             max(float(r['flo_GHz']), float(r['fhi_GHz'])), r['eb'])
            for r in rows]


def _confirmable(rows, sep):
    """True where two blocks more than `sep` days apart cover one frequency."""
    iv = _ivA(rows)
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        if _epr.separated([e for a, b, e in iv if a <= mid <= b], sep):
            return True
    return False


def _revisited(rows):
    """True where two blocks cover one frequency at all, separated or not."""
    iv = _ivA(rows)
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    return any(len({e for a, b, e in iv if a <= 0.5 * (pts[i] + pts[i + 1])
                    <= b}) > 1 for i in range(len(pts) - 1))


BYSYS_A = collections.defaultdict(list)
for r in ROWS:
    if r['resolution_class'] == 'fine':
        BYSYS_A[r['system_id']].append(r)
_C1 = {s for s, rr in BYSYS_A.items() if _confirmable(rr, 1.0)}
_C30 = {s for s, rr in BYSYS_A.items() if _confirmable(rr, 30.0)}
_C365 = {s for s, rr in BYSYS_A.items() if _confirmable(rr, 365.0)}
assert _C365 <= _C30 <= _C1, (
    'the confirmable sets are not nested, so the bars would double-count: '
    '%d / %d / %d' % (len(_C1), len(_C30), len(_C365)))
_LEFT = set(BYSYS_A) - _C1
_ONE = {s for s in _LEFT if len({r['eb'] for r in BYSYS_A[s]}) < 2}
_NOFREQ = {s for s in _LEFT - _ONE if not _revisited(BYSYS_A[s])}
_SAMEDAY = _LEFT - _ONE - _NOFREQ

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3),
                         gridspec_kw=dict(wspace=0.30))

ax = axes[0]
# v4.10: the band is the COMBINED interval of the budget table, which is what
# the caption says it is.  It previously used \StratTransferNineLo/Hi
# (x0.48--1.35), the window-to-window transfer bracket measured through the
# RETIRED rank gate -- a result withdrawn at v4.08, where the same quantity on
# the published criterion is x0.94--1.09 and is one of the smallest terms, not
# the dominant one.  A figure must not keep drawing a withdrawn number.
BUD_LO, BUD_HI = float(texval('BudTotalLo')), float(texval('BudTotalHi'))
ax.fill_betweenx(cumsel, psel * (1.0 - BUD_LO / 100.0),
                 psel * (1.0 + BUD_HI / 100.0),
                 step='post', color='#3a6ea5', alpha=0.16, lw=0,
                 label=(r'calibration interval, $-%.0f$ to $+%.0f$ per cent'
                        % (BUD_LO, BUD_HI)))
# ★★★★ THE LEGEND NAMED A CONVENTION THE PAPER NO LONGER USES, AND IT WAS
# NOT WHAT THE PANEL PLOTTED.  It read "EIRP_90, stratified: 3.45 P_trig
# where the ring is noise, > 20 P_trig where it is not" -- the two-stratum
# rank-charged convention retired in the v4.12 cycle -- while the curve has
# been `adopted_e90.per_window`, i.e. ONE factor for the class divided by
# each window's own annual-parallax retention, ever since.  A figure whose
# legend plots a retired convention and whose text quotes the adopted one
# makes a reader doubt both; and because the legend was built from macros of
# the retired family (\StrMultNoise, \StrPosCtrl) rather than from the curve,
# nothing could see the mismatch.
#
# The legend is now built from the SAME object the curve is built from, and
# the two assertions below make it impossible for them to drift apart again:
# the multiplier named in the legend must be the adopted one, and the plotted
# curve must reproduce the per-system median and the count of systems at
# 10^15 W that the text prints.
_ADOPT = float(texval('EirpNinetyMultA'))
assert abs(_ADOPT - P90FAC) < 1e-9, (_ADOPT, P90FAC)
_LEGEND = (r'$\mathrm{EIRP}_{90}=%.2f\,P_{\rm trig}$, per-window '
           r'parallax retention' % _ADOPT)
# The legend must name the adopted factor and no value of the retired
# two-stratum family, whichever of them is still defined in the macro layer.
for _retired in ('StrMultNoise', 'StrPosCtrl', 'EirpNinetyMultRank'):
    _v = texval(_retired)
    if _v:
        try:
            _f = float(_v)
        except ValueError:
            continue
        assert ('%.2f' % _f) not in _LEGEND, (
            'the legend of panel (a) names the retired %s = %s where the '
            'curve is drawn on the adopted %.2f' % (_retired, _v, _ADOPT))
assert ('%.2f' % _ADOPT) in _LEGEND, _LEGEND
ax.step(psel, cumsel, where='post', color='#3a6ea5', lw=1.6,
        label=_LEGEND)
# v4.10: the trigger-only curve is gone.  EIRP_90 is the only sensitivity the
# paper quotes, the two curves lay within 0.2 per cent of each other on the
# retired scale, and the caption describes one curve and one band.
ax.set_xscale('log')
ax.set_xlabel(r'$\mathrm{EIRP}_{90}$ (W)', fontsize=7.6)
ax.set_ylabel('independent systems with\nClass A coverage at or below', fontsize=7.6)
ax.tick_params(labelsize=6.8)
med = float(np.median(psel))
ax.axvline(med, color='#b03030', ls=':', lw=0.9)
ax.text(med * 1.18, cumsel[-1] * 0.10,
        'median\n%s W' % ('%.1f' % (med / 1e15) + r'$\times10^{15}$'),
        fontsize=6.2, color='#b03030')
ax.set_title('(a) Class A sensitivity, %d systems' % psel.size,
             fontsize=7.6, pad=3)
ax.legend(fontsize=5.8, frameon=False, loc='upper left',
          handlelength=1.6, handletextpad=0.5, borderpad=0.2)
ax.grid(color='0.9', lw=0.4)

ax = axes[1]
# R1-7 (v3.99): confirmation power, not block count. Classes come from
# epochsplit_v399.py, which defines an independent epoch as a separation
# of more than one day.
# ★★★★ ROUND 14: PANEL (b) PLOTTED THE WRONG POPULATION FOR THREE VERSIONS.
# It read the ALL-SURVEY split -- 82 systems -- and drew it beside a panel (a)
# titled "Class A sensitivity, 60 systems", with a red annotation reading
# "40 systems".  Both referees quoted "40 of the 60 Class A systems" back at
# us, because that is what this figure said.  The bars are now the Class A
# restriction of the same rule, on MEASURED epochs, and the identity below --
# whose ABSENCE is what let one figure count two populations -- requires them
# to sum to the number of points panel (a) plots.
LAB = ['one block only', 'no frequency covered twice',
       'repeats within one day', 'days apart', 'months apart', 'over a year']
VAL = [len(_ONE), len(_NOFREQ), len(_SAMEDAY),
       len(_C1 - _C30), len(_C30 - _C365), len(_C365)]
assert sum(VAL) == psel.size, (
    'panel (b) counts %d systems where panel (a) plots %d' % (sum(VAL),
                                                              psel.size))
# ★★ AND THE THREE BARS RIGHT OF THE LINE MUST BE THE PUBLISHED CONFIRMATION
#    COUNTS.  This is the clause whose absence let the panel draw the
#    any-frequency split under this title: the bars agreed with a generator,
#    just not with the one the text quotes.
for _got, _name in ((sum(VAL[3:]), 'RcConfSysDay'), (VAL[5], 'RcConfSysYr'),
                    (sum(VAL[:3]), 'RcNoRepSys')):
    _want = texval(_name)
    assert _want and _got == int(_want), (
        'panel (b) draws %d systems where \\%s is %s' % (_got, _name, _want))
# Horizontal bars: six categories carry sentences, not two-word stubs, and
# the reader sees at a glance which side of the line a system falls.
COL = ['0.72', '0.72', '0.72', '#8fb3d9', '#5b86b5', '#3a6ea5']
_y = range(len(VAL))
ax.barh(_y, VAL, color=COL, edgecolor='0.3', linewidth=0.4, height=0.70)
ax.set_yticks(list(_y))
ax.set_yticklabels(LAB, fontsize=6.2)
ax.invert_yaxis()
ax.set_xlabel('number of systems', fontsize=7.6)
ax.tick_params(labelsize=6.8)
for i2, v in enumerate(VAL):
    ax.text(v + 0.4, i2, str(v), va='center', fontsize=6.4)
ax.axhline(2.5, color='#b03030', ls='--', lw=0.9)
ax.text(max(VAL) * 1.12, 1.5,
        'above the line: no confirmation\npossible at any power, %d systems'
        % sum(VAL[:3]), ha='right', va='center', fontsize=5.6,
        color='#b03030')
ax.set_title('(b) confirmation power, same-frequency epochs',
             fontsize=7.6, pad=3)
ax.set_xlim(0, max(VAL) * 1.16)
ax.grid(axis='x', color='0.9', lw=0.4)

fig.savefig('figures/classa_sensitivity.pdf', bbox_inches='tight',
            pad_inches=0.02)

# ------------------------------------------------------------ macros
M = []
def m(k, v):
    M.append('\\newcommand{\\%s}{%s}' % (k, v))


def sci(x, sf=2):
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sf - 1, x / 10.0 ** e, e)


m('ClassASysPlot', '%d' % p90.size)
# Per SYSTEM: the best Class A window of each system.
# The figure's `med` is the SELECTION median; the PNinetySys* trio must
# stay the trigger completeness, or a caption and a macro that share a
# name stop meaning the same thing.
m('PNinetySysMedA', sci(float(np.median(p90))))
m('PNinetySysBestA', sci(float(p90.min())))
m('PNinetySysWorstA', sci(float(p90.max())))
# v4.10: the PselSys* trio is NOT emitted any more.  It was the retired
# criterion under a third name, nothing referenced it, and the assertion it
# carried compared it with \PromoteSysMedA -- another member of the same
# retired family -- so two superseded numbers agreeing proved nothing.  The
# plotted curve is instead required to reproduce the three macros the
# manuscript actually prints.


def _macro_W(name):
    v = texval(name)
    assert v, 'the plotted sensitivity has no macro to check against: %s' % name
    a, b = v.split('\\times10^{')
    return float(a) * 10 ** float(b.rstrip('}'))


for _got, _name in ((float(np.median(psel)), 'EirpNinetySysMedA'),
                    (float(psel.min()), 'EirpNinetySysLoA'),
                    (float(psel.max()), 'EirpNinetySysHiA')):
    # tolerance is half a unit in the macro's last printed digit (two
    # significant figures), not an arbitrary 6 per cent.
    assert abs(_got / _macro_W(_name) - 1) < 0.05, (
        'panel (a) plots %g where \\%s is %g'
        % (_got, _name, _macro_W(_name)))

# ★★ AND THE COUNT THE TEXT PRINTS MUST BE READABLE OFF THIS CURVE.  The
# median and the range were already pinned; the number of systems reaching
# 10^15 W was not, and it is the one figure of the panel a reader checks by
# eye against the axis.  Under a convention other than the adopted one it
# moves, so this is the clause that would have caught a stratified curve
# beneath an unstratified legend.
_NE15 = int((psel <= 1e15).sum())
_claim = texval('NSysEfifteen')
assert _claim and _NE15 == int(_claim), (
    'panel (a) has %d systems at or below 1e15 W where \\NSysEfifteen is %s'
    % (_NE15, _claim))

m('ClassASysDecade', '%d' % int((p90 <= p90.min() * 10).sum()))
m('NSysOneEB', '%d' % nep.get(1, 0))
m('NSysTwoEB', '%d' % nep.get(2, 0))
m('NSysMultiEBNow', '%d' % sum(v for k, v in nep.items() if k >= 2))
m('PctSysMultiEB', '%.0f' % (100.0 * sum(v for k, v in nep.items() if k >= 2)
                             / sum(nep.values())))
open('survey_numbers_round32.tex', 'w').write(
    '% generated by make_fig_classa_sens.py -- do not edit\n'
    + '\n'.join(M) + '\n')
print('Class A systems %d | P90 best %.2g median %.2g worst %.2g'
      % (p90.size, p90.min(), med, p90.max()))
print('epochs per system: %s | multi-epoch %d of %d (%.0f per cent)'
      % (dict(sorted(nep.items())), sum(v for k, v in nep.items() if k >= 2),
         sum(nep.values()),
         100.0 * sum(v for k, v in nep.items() if k >= 2) / sum(nep.values())))
