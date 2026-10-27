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

Each window's EIRP_90 is taken from `adopted_e90.py`, the single owner of
the published per-window sensitivity: the class completeness factor, the
omitted annual parallax, the intra-integration smearing retention and the
primary-beam response, all four applied.  ★ IT USED TO BE THE BLANKET
MULTIPLIER TIMES THE NOMINAL TRIGGER POWER, which is the same quantity minus
the three per-window terms, and that is why this figure reached 25 systems at
10^15 W where Section 5 reached 24: one system's best window loses enough to
the smearing term to cross the line, and a figure and a sentence disagreed
about a headline count.  One number now serves both, and the clause below
asserts it against the macro the text prints.

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

import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import figfloor_r17 as ff        # the type floor, the scale and the float
ff.pin_epoch()                   # before any savefig, or the wall clock is stamped

# ★ FS_REQUIRED is what this figure is HELD to and is never perturbed;
#   FS_FLOOR is what it is DRAWN at.  Keeping them apart is the whole point:
#   a drive that lowered both would move the check and the thing it checks
#   together, and a check that shares its input with its subject is circular.
#   Drives 65-69 break one clause each; see the foot of the file.
_DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) \
    if '--drive' in sys.argv else 0
FS_REQUIRED = 6.5
FS_FLOOR = FS_REQUIRED if _DRIVE != 66 else 5.8   # 66: the sizes it shipped at
FS_TICK = FS_FLOOR
FS_TITLE = FS_FLOOR + 0.3
FS_AXLAB = 7.6

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 8, 'axes.labelsize': FS_AXLAB,
    'xtick.labelsize': FS_TICK, 'ytick.labelsize': FS_TICK,
    'legend.fontsize': FS_FLOOR,
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
    for f in sorted([_mgp for _mgp in glob.glob('survey_numbers*.tex') if '_drive' not in _mgp]):
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

import adopted_e90 as _ae
_ALL = list(csv.DictReader(open(CAT)))
_E90 = _ae.per_window(_ALL, os.path.dirname(os.path.abspath(CAT)) or '.')
# ★ THE MAP IS A MAP OF LIMITS, so it is drawn over the windows that carry
# one: a window every channel of which lies inside the attribution mask
# constrains nothing (Sec. \ref{sec:lines}).  Drawing it over all of them
# put the map and Section 5 on two different sensitivities, which is what
# the clause at the foot of this file refuses.
_CDIR = os.path.dirname(os.path.abspath(CAT)) or '.'
ROWS = [r for r in _ALL
        if r['search_class'] == 'A' and _ae.limit_eligible(r, _CDIR)]
WIN = []
for r in ROWS:
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    # a descending spectral window writes its limits reversed; key on the pair
    WIN.append((min(a, b), max(a, b), _E90[id(r)], r['system_id']))
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
# ★ TWO COUNTS, KEPT APART.  \NSysClassA is how many systems the
# fine-channel search COVERS and \NSysALim how many of them a limit can be
# drawn for; this map draws limits, so it is the second.  The same for the
# windows: \NWinA counts the windows searched and \NSysALost names the
# systems the mask leaves nothing of.
_pubn = int(texval('NSysALim'))
assert len(SYS) == _pubn, (len(SYS), _pubn)
_pubw = int(texval('NWinA')) - int(texval('UmNWinAFull'))
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

# ★ The canvas IS the column: the saved width is the figsize, there is no tight
#   bbox, so the float's scale is 1 by construction and the sizes set here are
#   the sizes a reader sees.  The height grew with the type, 132 -> 146 pt.
W, H = ff.COL_PT, 146.0
if _DRIVE in (65, 67):           # 65: artwork too wide for the float it is given
    W = ff.TEXT_PT               # 67: and drawn as a two-column figure*
fig = plt.figure(figsize=(W / 72.0, H / 72.0))
gs = fig.add_gridspec(1, len(BANDS), width_ratios=WID, wspace=0.30 if _DRIVE != 70 else 0.03,
                      left=0.155, right=0.822, bottom=0.215, top=0.875)
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
    ax.set_title('Band %s' % b, fontsize=FS_TITLE, pad=5.0)
    ax.tick_params(labelsize=FS_TICK, length=2, pad=1.5)
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

fig.text(0.495, 0.028, 'sky frequency (GHz)', ha='center',
         fontsize=FS_AXLAB if _DRIVE != 69 else 26.0)
axes[-1].text(0.96, EIRP_REF * 1.35, r'$10^{15}$ W',
              transform=axes[-1].get_yaxis_transform(), ha='right',
              va='bottom', fontsize=FS_FLOOR, color='#b03030')

cax = fig.add_axes([0.845, 0.215, 0.030, 0.660])
cb = fig.colorbar(pm, cax=cax, ticks=LEV[:-1], spacing='uniform')
cb.ax.set_yticklabels([str(v) for v in LEV[:-1]])
cb.ax.tick_params(labelsize=FS_TICK, length=2)
# ★ Two lines, not one.  At the floor this legend is longer than the bar it
#   labels, and a single line would be clipped off the top of the canvas --
#   which is what the FIT clause below exists to refuse.
cb.set_label('independent systems\nreaching this depth', fontsize=FS_FLOOR,
             labelpad=2, linespacing=1.15)
cb.outline.set_linewidth(0.5)

# ======================================================================================
# ★★ IS IT BIG ENOUGH TO READ?  Five clauses, each driven to fail on its own:
#   --drive 65  the canvas is drawn at the full text width while the float still
#               gives it one column: every label prints at half size and nothing
#               else in the build can see it.  SCALE fires.
#   --drive 66  the sizes this figure shipped at are restored.  FLOOR fires, and
#               on the written PDF, not on the numbers set above.
#   --drive 67  emitted as a two-column figure* and declared as one while the
#               manuscript places it in a figure.  FLOAT fires.
#   --drive 68  SOURCE_DATE_EPOCH cleared before the save -- how a generator run
#               by hand writes a file the build cannot reproduce.  EPOCH fires.
#   --drive 69  the abscissa label is set at 26 pt and runs off a canvas that
#               does not grow to fit it.  FIT fires; nothing else could see it.
# ======================================================================================
# ★ TWO CLEARANCES, because they are two different questions.  Abscissa
#   labels in ADJACENT panels must stand apart -- 240 beside 320 reads
#   "240320" without ever intersecting -- while everything else need only not
#   collide.
#   --drive 70  the panels are pushed together until 240 and 320 touch across
#               the Band 6 / Band 7 boundary.  CLASH fires on the clearance
#               clause: the two never intersect, they merely read as "240320".
ff.no_overlap([t for a in axes for t in a.get_xticklabels()], fig, clear=2.5)
ff.no_overlap([t for a in axes for t in
               a.get_xticklabels() + a.get_yticklabels()]
              + [a.title for a in axes] + list(cb.ax.get_yticklabels()),
              fig, clear=0.0)

if _DRIVE == 68:
    os.environ.pop('SOURCE_DATE_EPOCH', None)
FOUT = 'figures/completeness_map%s.pdf' % ('_drive%d' % _DRIVE if _DRIVE else '')
fig.savefig(FOUT)
plt.close(fig)
ff.check(FOUT, HERE, 'figures/completeness_map.pdf', floor=FS_REQUIRED,
         expect_env='figure*' if _DRIVE == 67 else 'figure')

# ★ D36, and a drive that silently passes is worse than no drive: every drive
#   number above is expected to have failed a clause by now, so reaching this
#   line with one set is itself a failure -- and it also guarantees a drive can
#   never write a path production reads.
assert not _DRIVE, ('--drive %d reached the end of the generator: the clause '
                    'it was written to break did not fire' % _DRIVE)

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
# ★ THE COUNT THIS FIGURE REACHES AT THE REFERENCE POWER IS THE COUNT THE
# TEXT PRINTS.  Both are "systems whose best Class A window reaches 10^15 W",
# and for five rounds they were computed from two different sensitivities and
# differed by one.  A figure that contradicts the sentence beside it on a
# headline count is worse than either number alone, so the agreement is
# asserted rather than hoped for.
_pub15 = texval('NSysEfifteen')
assert _pub15 and int(_pub15) == nsys_ref, (
    'the map reaches %d systems at %.0e W where \\NSysEfifteen says %s; the '
    'figure and the text are built on different sensitivities'
    % (nsys_ref, EIRP_REF, _pub15))
print('  cross-check \\NSysEfifteen = %s == %d from the map' % (_pub15, nsys_ref))
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
