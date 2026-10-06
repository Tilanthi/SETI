#!/usr/bin/env python3
r"""Referee 1, point 4: the survey-completeness map N*(nu, EIRP).

Bandwidth alone exaggerates the search volume.  The Class A union is
\DnuA GHz, but different frequencies were searched toward different numbers
of stars and to EIRP limits spanning three and a half decades, so "47.7 GHz"
describes the window function and not the experiment.

This figure answers the question the referee actually poses: at a given sky
frequency and a given transmitter power, how many INDEPENDENT systems would
have yielded a recovery at 90 per cent completeness?  A system counts at
(nu, E) if it has at least one Class A window whose frequency limits contain
nu and whose EIRP_90 is at or below E.

  EIRP_90(window) = \EirpNinetyMultA x P_trig(window)

the adopted, injection-measured sensitivity -- the same quantity plotted in
the Class A sensitivity figure.  The catalogue column `eirp_p90_sel_W` is NOT
read: it carries the retired 2.88 x P_trig criterion.

The figure replaces the repeated prose warnings that the union is a set of
disconnected intervals.  It makes that point once, and it makes the stronger
point as well: the covered frequency SHRINKS as the power falls, from the
full union when power is unlimited to \CovUnionAtRef GHz at \CovEirpRefTex W.

Writes figures/completeness_map.pdf and survey_numbers_round135.tex.
"""
import csv
import glob
import math
import os
import re

import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 8, 'axes.labelsize': 7.6,
    'xtick.labelsize': 6.8, 'ytick.labelsize': 6.8, 'legend.fontsize': 6.0,
})
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

CAT = 'per_target_results_v3.99.csv'
OUT = 'survey_numbers_round135.tex'
EIRP_REF = 1.0e15          # the round power the paper already quotes


def texval(name):
    """LAST literal definition of \\name across new/renew/providecommand,
    following an alias whose body is a single macro.  Same reader as
    make_fig_classa_sens.py, for the same reason: round103 retires superseded
    names by aliasing them, so a first-match reader returns the wrong value."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % re.escape(name))
    out = None
    for f in sorted(glob.glob('survey_numbers*.tex')):
        for m in pat.finditer(open(f).read()):
            v = m.group(1).strip()
            if v:
                out = v
    seen = set()
    while out and re.fullmatch(r'\\[A-Za-z]+', out) and out not in seen:
        seen.add(out)
        out = texval(out[1:])
    return out


MULT = texval('EirpNinetyMultA')
assert MULT, ('\\EirpNinetyMultA is not defined: this figure must run after '
              'numbers_v410.py (round 103), which measures the adopted '
              'multiplier.')
MULT = float(MULT)
assert abs(MULT / 2.88 - 1) > 0.01, 'this figure would use the RETIRED x2.88'

ROWS = [r for r in csv.DictReader(open(CAT)) if r['search_class'] == 'A']
WIN = []
for r in ROWS:
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    # a descending spectral window writes its limits reversed; key on the pair
    WIN.append((min(a, b), max(a, b), MULT * float(r['eirp_nominal_W']),
                r['system_id']))
assert WIN, 'no Class A windows'
SYS = sorted({s for _, _, _, s in WIN})

# ---------------------------------------------------------------- the grid
# 20 MHz in frequency: the narrowest Class A island is 107 MHz wide, so every
# island is resolved by at least five cells.  Three decades of EIRP at 40
# cells per decade.
DNU = 0.02
NU_LO = DNU * math.floor(min(w[0] for w in WIN) / DNU) - 2.0
NU_HI = DNU * math.ceil(max(w[1] for w in WIN) / DNU) + 2.0
NU = np.arange(NU_LO, NU_HI + DNU, DNU)
E_LO = 10 ** math.floor(math.log10(min(w[2] for w in WIN)))
E_HI = 10 ** math.ceil(math.log10(max(w[2] for w in WIN)))
EDG = np.logspace(math.log10(E_LO), math.log10(E_HI),
                  int(round(40 * math.log10(E_HI / E_LO))) + 1)
ECEN = np.sqrt(EDG[:-1] * EDG[1:])

# For each (system, frequency cell) the DEEPEST window covering it.  Then
# N*(nu, E) = number of systems whose best limit there is at or below E.
BEST = np.full((len(SYS), NU.size), np.inf)
SIDX = {s: i for i, s in enumerate(SYS)}
for lo, hi, e, s in WIN:
    i0, i1 = int(np.searchsorted(NU, lo)), int(np.searchsorted(NU, hi))
    row = BEST[SIDX[s], i0:i1]
    np.minimum(row, e, out=row)
NSTAR = np.zeros((ECEN.size, NU.size), dtype=np.int16)
for j, e in enumerate(ECEN):
    NSTAR[j] = (BEST <= e).sum(axis=0)

# ---------------------------------------------------------------- the checks
# (1) A completeness map cannot LOSE a system when more power is allowed.
assert np.all(np.diff(NSTAR, axis=0) >= 0), \
    'N* falls with increasing EIRP somewhere in the map'
# (2) No frequency can reach more systems than the experiment has.
assert NSTAR.max() <= len(SYS), (NSTAR.max(), len(SYS))
# (3) The frequency extent of the map at unlimited power must reproduce the
#     published Class A union.  This is the figure's tie to the rest of the
#     paper: if the catalogue or the macro moves, the build stops.
def _merge(iv):
    out = []
    for lo, hi in sorted(iv):
        if out and lo <= out[-1][1]:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out


MERGED = _merge([(w[0], w[1]) for w in WIN])
union_exact = sum(hi - lo for lo, hi in MERGED)
union_full = DNU * float((NSTAR[-1] > 0).sum())
ISLANDS = int(np.diff(np.concatenate(([0], (NSTAR[-1] > 0).view(np.int8),
                                      [0]))).clip(min=0).sum())
_pub = float(texval('DnuA'))
assert abs(union_exact - _pub) <= 0.05, \
    ('the catalogue union is %.2f GHz where \\DnuA says %.2f'
     % (union_exact, _pub))
# The frequency cell must be fine enough that no island is lost or merged
# into its neighbour.  Bounding the union error by DNU x (gridded island
# count) alone would be a check that cannot fail: coarsening the grid shrinks
# the count and widens the tolerance at the same time.  The island count is
# therefore compared with the catalogue's own merge AND with the published
# macro, and the union error is bounded by the EXACT count.
assert ISLANDS == len(MERGED), \
    ('the %.0f MHz grid resolves %d islands where the catalogue has %d'
     % (1e3 * DNU, ISLANDS, len(MERGED)))
_pubi = int(texval('DomAIslands'))
assert len(MERGED) == _pubi, (len(MERGED), _pubi)
assert abs(union_full - union_exact) <= DNU * len(MERGED), \
    ('gridding moved the union by %.3f GHz over %d islands'
     % (union_full - union_exact, len(MERGED)))
_pubn = int(texval('NSysClassA'))
assert len(SYS) == _pubn, (len(SYS), _pubn)
_pubw = int(texval('NWinA'))
assert len(WIN) == _pubw, (len(WIN), _pubw)

# ---------------------------------------------------------------- numbers
jref = int(np.searchsorted(ECEN, EIRP_REF))
nref = NSTAR[jref]
union_ref = DNU * float((nref > 0).sum())
nsys_ref = len({s for _, _, e, s in WIN if e <= EIRP_REF})
nmax_ref = int(nref.max())
numax_ref = float(NU[int(np.argmax(nref))])
nmax_full = int(NSTAR[-1].max())
numax_full = float(NU[int(np.argmax(NSTAR[-1]))])
e_best = min(w[2] for w in WIN)
# The fraction of the headline bandwidth that survives at the reference power.
frac_ref = 100.0 * union_ref / union_exact
# Half the systems: the power at which the map first reaches N*/2 anywhere.
half = len(SYS) / 2.0
jhalf = int(np.argmax(NSTAR.max(axis=1) >= half))

# ---------------------------------------------------------------- figure
# One panel per populated ALMA band, with panel widths in proportion to the
# frequency range that band actually contributes.  A single linear axis from
# 114 to 873 GHz renders every island as a hairline -- the Class A union is
# 47.7 GHz spread over 759, so 94 per cent of such a figure is empty and the
# structure inside each band is invisible.  That is the fault this figure
# exists to fix, so it must not be reproduced here.  Narrow bands are given a
# floor width so that Bands 3 and 8 survive at column width; the floor changes
# how wide a panel is drawn, never what is drawn inside it.
LEV = [1, 2, 3, 5, 8, 12, 18, 26, 40]
cmap = plt.get_cmap('YlGnBu', len(LEV) - 1)
norm = BoundaryNorm(LEV, cmap.N)

BANDS = sorted({r['band'] for r in ROWS}, key=int)
BSPAN = {}
for b in BANDS:
    f = [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
          max(float(r['flo_GHz']), float(r['fhi_GHz'])))
         for r in ROWS if r['band'] == b]
    lo, hi = min(a for a, _ in f), max(c for _, c in f)
    pad = max(0.04 * (hi - lo), 0.05)
    BSPAN[b] = (lo - pad, hi + pad)
FLOOR = 5.0
WID = [max(BSPAN[b][1] - BSPAN[b][0], FLOOR) for b in BANDS]

W, H = 245.0, 132.0
fig = plt.figure(figsize=(W / 72.0, H / 72.0))
gs = fig.add_gridspec(1, len(BANDS), width_ratios=WID, wspace=0.18,
                      left=0.145, right=0.845, bottom=0.195, top=0.885)
axes = []
for k, b in enumerate(BANDS):
    ax = fig.add_subplot(gs[0, k])
    lo, hi = BSPAN[b]
    sel = (NU >= lo - DNU) & (NU <= hi + DNU)
    i0, i1 = int(np.argmax(sel)), int(NU.size - np.argmax(sel[::-1]))
    sub = np.ma.masked_where(NSTAR[:, i0:i1] < 1, NSTAR[:, i0:i1])
    pm = ax.pcolormesh(np.append(NU[i0:i1], NU[i1 - 1] + DNU), EDG, sub,
                       cmap=cmap, norm=norm, shading='flat', rasterized=True)
    ax.set_yscale('log')
    ax.set_xlim(lo, hi)
    ax.set_ylim(E_LO, E_HI)
    ax.set_facecolor('0.955')
    ax.axhline(EIRP_REF, color='#b03030', ls='--', lw=0.8, zorder=5)
    ax.set_title('Band %s' % b, fontsize=6.6, pad=2.5)
    ax.tick_params(labelsize=6.0, length=2, pad=1.5)
    if (hi - lo) > 12:
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(
            nbins=2, prune='both', integer=True, steps=[1, 2, 5, 10]))
    else:
        ax.set_xticks([round(0.5 * (lo + hi))])
    ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%d'))
    if k:
        ax.set_yticklabels([])
    else:
        ax.set_ylabel('EIRP (W)')
    axes.append(ax)

fig.text(0.495, 0.015, 'sky frequency (GHz)', ha='center', fontsize=7.6)
axes[-1].text(0.96, EIRP_REF * 1.3, r'$10^{15}$ W',
              transform=axes[-1].get_yaxis_transform(), ha='right',
              va='bottom', fontsize=5.8, color='#b03030')

cax = fig.add_axes([0.868, 0.195, 0.030, 0.690])
cb = fig.colorbar(pm, cax=cax, ticks=LEV[:-1], spacing='uniform')
cb.ax.set_yticklabels([str(v) for v in LEV[:-1]])
cb.ax.tick_params(labelsize=6.2, length=2)
cb.set_label('independent systems reaching this depth', fontsize=6.4,
             labelpad=2)
cb.outline.set_linewidth(0.5)

fig.savefig('figures/completeness_map.pdf')
plt.close(fig)

# ---------------------------------------------------------------- macros
M = []


def m(k, v):
    M.append('\\newcommand{\\%s}{%s}' % (k, v))


def sci(x, sf=2):
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sf - 1, x / 10.0 ** e, e)


m('CovEirpRefTex', sci(EIRP_REF, 1))
m('CovUnionAtRef', '%.1f' % union_ref)
m('CovUnionFull', '%.1f' % union_exact)
m('CovNIslands', '%d' % ISLANDS)
m('CovFracAtRef', '%.0f' % frac_ref)
m('CovNSysAtRef', '%d' % nsys_ref)
m('CovNMaxAtRef', '%d' % nmax_ref)
m('CovNuMaxAtRef', '%.0f' % numax_ref)
m('CovNMaxFull', '%d' % nmax_full)
m('CovNuMaxFull', '%.0f' % numax_full)
m('CovEirpBest', sci(e_best))
m('CovEirpHalf', sci(float(ECEN[jhalf])))
m('CovNHalf', '%d' % int(math.ceil(half)))
open(OUT, 'w').write('%% GENERATED by make_fig_completeness_map.py -- '
                     'do not hand-edit.\n' + '\n'.join(M) + '\n')

print('completeness_map.pdf: %d Class A windows, %d systems, %.2f GHz '
      'union in %d islands (gridded %.2f)'
      % (len(WIN), len(SYS), union_exact, ISLANDS, union_full))
print('  at %.0e W: %.2f GHz covered (%.0f per cent of the union), %d systems '
      'reached, best frequency %d GHz with %d systems'
      % (EIRP_REF, union_ref, frac_ref, nsys_ref, numax_ref, nmax_ref))
print('  unlimited power: best frequency %d GHz with %d of %d systems'
      % (numax_full, nmax_full, len(SYS)))
print('  deepest single window %.3g W; half the systems (%d) first reached '
      'at %.3g W' % (e_best, math.ceil(half), ECEN[jhalf]))
print('macros -> %s (%d)' % (OUT, len(M)))
