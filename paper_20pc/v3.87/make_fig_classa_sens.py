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

CAT = 'per_target_results_v3.87.csv'
ROWS = list(csv.DictReader(open(CAT)))


def texval(name):
    for f in sorted(glob.glob('survey_numbers*.tex')):
        m = re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name, open(f).read())
        if m:
            return m.group(1)
    return None


def F(x):
    return None if x in ('', None) else float(x)


from inject_curve import P90_OVER_TRIG as P90FAC  # unrounded; the macro is %.1f

# ------------------------------------------------ (a) Class A sensitivity
# R1-1: the survey's sensitivity is the power that passes the COMPLETE
# automated selection -- trigger AND the window's own control-ring gate --
# so that is what this figure leads with. P_90, the trigger completeness,
# is plotted beside it because the gap between them is itself the point.
best, bestsel = {}, {}
for r in ROWS:
    if r['resolution_class'] != 'fine':
        continue
    e, c = F(r['eirp_eff_total_W']), F(r['ctrl_max_snr'])
    if e is None:
        continue
    s = r['system_id']
    if s not in best or e < best[s]:
        best[s] = e
    if c:
        sel = e * P90FAC * c / 5.0
        if s not in bestsel or sel < bestsel[s]:
            bestsel[s] = sel
p90 = np.array(sorted(v * P90FAC for v in best.values()))
psel = np.array(sorted(bestsel.values()))
cum = np.arange(1, p90.size + 1)
cumsel = np.arange(1, psel.size + 1)

# ------------------------------------------------ (b) epochs per system
ebs = collections.defaultdict(set)
for r in ROWS:
    ebs[r['system_id']].add(r['eb'])
nep = collections.Counter(min(len(v), 5) for v in ebs.values())

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3),
                         gridspec_kw=dict(wspace=0.30))

ax = axes[0]
ax.step(psel, cumsel, where='post', color='#3a6ea5', lw=1.6,
        label=r'$P_{90}^{\rm sel}$: passes the complete selection')
ax.step(p90, cum, where='post', color='0.55', lw=1.1, ls='--',
        label=r'$P_{90}$: reaches the trigger only')
ax.set_xscale('log')
ax.set_xlabel('EIRP for 90 per cent recovery (W)', fontsize=7.6)
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
ks = [1, 2, 3, 4, 5]
vals = [nep.get(k, 0) for k in ks]
ax.bar(range(len(ks)), vals, color='#3a6ea5', edgecolor='0.3', linewidth=0.4,
       width=0.72)
ax.set_xticks(range(len(ks)))
ax.set_xticklabels(['1', '2', '3', '4', r'$\geq5$'], fontsize=6.8)
ax.set_xlabel('independent execution blocks per system', fontsize=7.6)
ax.set_ylabel('number of systems', fontsize=7.6)
ax.tick_params(labelsize=6.8)
for i, v in enumerate(vals):
    if v:
        ax.text(i, v + 0.6, str(v), ha='center', fontsize=6.4)
ax.set_title('(b) how often a repeat exists at all', fontsize=7.6, pad=3)
ax.grid(axis='y', color='0.9', lw=0.4)

for a in axes:
    for sp in ('top', 'right'):
        a.spines[sp].set_visible(False)
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
m('PselSysMedA', sci(float(np.median(psel))))
m('PselSysBestA', sci(float(psel.min())))
m('PselSysWorstA', sci(float(psel.max())))
# v381_calc.py derives the same quantity from the catalogue as
# PromoteSys*; assert the two agree rather than ship both unchecked.
_other = texval('PromoteSysMedA')
if _other:
    _o = float(_other.split('\\times10^{')[0]) * 10 ** float(
        _other.split('\\times10^{')[1].rstrip('}'))
    assert abs(float(np.median(psel)) / _o - 1) < 0.06, (
        'PselSysMedA %g disagrees with PromoteSysMedA %g'
        % (float(np.median(psel)), _o))

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
