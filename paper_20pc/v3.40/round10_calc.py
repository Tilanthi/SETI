#!/usr/bin/env python3
r"""Round-10 macro computation (v3.40).

Sources
-------
  frozen_export_v3.31.json        the rounds 5-9 freeze, UNCHANGED
  dwell_campaign_trials_v3.32.csv the 3,888 trial-level injection records
  survey_stats_round10.json       written by survey_stats_round10.py, which is
                                  the v3.32 statistics engine pointed at the
                                  SAME frozen export and extended with (a) a
                                  measured two-class completeness curve and
                                  (b) a coarse-inclusive occurrence limit.

Rules honoured: numbers only via generated macros; macro names letter-only.

Why this round exists
---------------------
Through v3.39 the paper stated that completeness was measured on ONE
fine-channel configuration and transferred to every other window by
assumption, and that the coarse class had no completeness curve at all.
That was true of the v3.28 campaign.  It is NOT true of the dwell campaign
released with v3.32, which this round finally reads at trial level.

The dwell campaign injected carriers into 12 real windows (11 targets,
Bands 3, 6 and 7, both resolution classes) whose integration counts span
n_int = 21 to 1314, a factor of 63.  Because the de-drift step is an
inverse-variance-weighted SUM over integrations, a carrier of amplitude
`amp_sigma` per integration present for a dwell fraction `dwell`
accumulates to

    a = amp_sigma * dwell * sqrt(n_int)

in units of the per-integration noise: `a` is the stacked significance, and
the 5-sigma trigger acts on it directly.  Binning the trials in `a`
therefore unifies the amplitude and dwell axes AND puts all 12 windows on
one axis, which makes configuration-independence a measurable claim rather
than an assumption.  It is measured here two ways:

  1. the amplitude at 50 per cent recovery, window by window, in the six
     windows where the campaign's amplitude grid straddles the threshold;
  2. the pooled curve per class, which is flat-bottomed below a=3 and
     saturated above a=8 in both classes.

The six remaining windows cannot measure a 50 per cent point because their
weakest injection is already above the trigger; they recover 100 per cent
of every injection, which is consistent but carries no information about
the curve's position.  Both facts are reported.

Referee items served: the standing "single configuration / unbounded
transfer error / no coarse curve" caveat (abstract, S4.4, S6.2,
Appendix I), and the restriction of the occurrence limit to the
fine-calibrated subset.
"""
import csv, json, math, statistics as st, collections

TR = list(csv.DictReader(open('dwell_campaign_trials_v3.32.csv')))
for r in TR:
    r['a'] = float(r['amp_sigma']) * float(r['dwell']) * math.sqrt(int(r['n_int']))
    r['det'] = r['detected'].lower() == 'true'

winkey = lambda r: (r['klass'], r['band'], r['target'], r['window'])
wins = sorted({winkey(r) for r in TR})

# ---- 1. per-window 50 per cent recovery amplitude ---------------------------
def a_fifty(sel, block=24):
    """Amplitude at which recovery crosses 0.5, by linear interpolation on
    sliding blocks of `block` trials ordered in a.  None when the campaign's
    weakest injection is already recovered (no crossing inside the grid)."""
    s = sorted(sel, key=lambda r: r['a'])
    pts = []
    for i in range(0, len(s) - block + 1, block // 2):
        ch = s[i:i + block]
        pts.append((st.median(r['a'] for r in ch),
                    sum(r['det'] for r in ch) / len(ch)))
    for (a1, p1), (a2, p2) in zip(pts, pts[1:]):
        if p1 < 0.5 <= p2:
            return a1 + (0.5 - p1) / (p2 - p1) * (a2 - a1)
    return None

meas, sat = [], []
perwin = []
for w in wins:
    sel = [r for r in TR if winkey(r) == w]
    v = a_fifty(sel)
    amin = min(r['a'] for r in sel)
    perwin.append({'klass': w[0], 'band': int(w[1]), 'target': w[2],
                   'n_int': int(sel[0]['n_int']), 'a_fifty': v, 'a_min': amin,
                   'rec_all': sum(r['det'] for r in sel) / len(sel)})
    (meas if v is not None else sat).append((w, v, amin))

nint = [p['n_int'] for p in perwin]
fifty = [p['a_fifty'] for p in perwin if p['a_fifty'] is not None]
satmin = min(p['a_min'] for p in perwin if p['a_fifty'] is None)
satrec = min(p['rec_all'] for p in perwin if p['a_fifty'] is None)

# ---- 2. pooled two-class curve ----------------------------------------------
EDGES = [(0, 3), (3, 4), (4, 5), (5, 6), (6, 8), (8, 12), (12, None)]
curve = {}
for cls in ('coarse', 'fine'):
    sel = [r for r in TR if r['klass'] == cls]
    row = []
    for lo, hi in EDGES:
        s = [r for r in sel if lo <= r['a'] and (hi is None or r['a'] < hi)]
        row.append((len(s), (sum(r['det'] for r in s) / len(s)) if s else None))
    curve[cls] = row

# ---- 3. occurrence, coarse-inclusive ----------------------------------------
S = json.load(open('survey_stats_round10.json'))
O16 = S['occurrence']['1e+16']
O15 = S['occurrence']['1e+15']
O17 = S['occurrence']['1e+17']

# Guard: this round must NOT move any published number.  These three are the
# v3.39 values; if the freeze or the engine ever drifts, fail loudly.
for got, want, what in ((100 * O16['measured'], 6.2, 'OccMeasured'),
                        (O16['n_sys_fine'], 59, 'NOccSystems'),
                        (100 * O16['unit'], 3.6, 'OccUnit'),
                        (100 * O16['uniform'], 8.6, 'OccUniform'),
                        (100 * O16['measured_D05'], 10.8, 'DutyHalf')):
    if abs(got - want) > 0.05:
        raise SystemExit(f'FREEZE DRIFT: {what} recomputed as {got:.2f}, '
                         f'published {want} -- refusing to write macros')

M = [
    ('CompWin',        '%d' % len(wins)),
    ('CompTgt',        '%d' % len({w[2] for w in wins})),
    ('CompBands',      ', '.join(sorted({w[1] for w in wins}))
                       .replace(', 7', ' and~7')),
    ('CompNintLo',     '%d' % min(nint)),
    ('CompNintHi',     '%s' % format(max(nint), ',').replace(',', chr(92) + ',')),
    ('CompNintFactor', '%d' % round(max(nint) / min(nint))),
    ('CompFiftyN',     '%d' % len(fifty)),
    ('CompFiftyLo',    '%.1f' % min(fifty)),
    ('CompFiftyHi',    '%.1f' % max(fifty)),
    ('CompFiftyMed',   '%.1f' % st.median(fifty)),
    ('CompSatN',       '%d' % len(sat)),
    ('CompSatMin',     '%.1f' % satmin),
    ('CompSatRec',     '%d' % round(100 * satrec)),
    ('OccAll',         '%.1f' % (100 * O16['all'])),
    ('NOccAll',        '%d'   % O16['n_sys_all']),
    ('OccAllDhalf',    '%.1f' % (100 * O16['all_D05'])),
    ('OccAllDtenth',   '%.0f' % (100 * O16['all_D01'])),
    ('OccAllFifteen',  '%.1f' % (100 * O15['all'])),
    ('NOccAllFifteen', '%d'   % O15['n_sys_all']),
    ('OccAllSeventeen','%.1f' % (100 * O17['all'])),
    ('NOccAllSeventeen','%d'  % O17['n_sys_all']),
]
with open('survey_numbers_round10.tex', 'w') as f:
    f.write('%% GENERATED by round10_calc.py -- do not hand-edit.\n')
    for k, v in M:
        f.write('\\newcommand{\\%s}{%s}\n' % (k, v))

# ---- 4. generated table body: the measured two-class completeness curve -----
def cell(n, p):
    return '--' if p is None else ('%d\\%% (%d)' % (round(100 * p), n))
lab = ['$<3$', '3--4', '4--5', '5--6', '6--8', '8--12', '$>12$']
# The WHOLE table environment is generated, and \input at top level in the
# manuscript.  \input'ing only the rows from inside a tabular breaks booktabs
# ("Misplaced \noalign" at \bottomrule), whichever way the final row is
# terminated -- verified both ways.
body = ' \\\\\n'.join('%s & %s & %s' % (L, cell(*curve['coarse'][i]),
                                        cell(*curve['fine'][i]))
                      for i, L in enumerate(lab))
# Emitted as panel (b) of the existing dwell table, not as a float of its
# own: same campaign, same message, one caption and one float between them.
with open('tab_compcurve.tex', 'w') as f:
    f.write(r"""%% GENERATED by round10_calc.py -- do not hand-edit.
\smallskip
\emph{(b) completeness at the trigger, against stacked amplitude $a$
(Eq.~\ref{eq:stacked}), pooled over the \CompWin{} injected windows;
trial counts in parentheses.}\\[2pt]
\label{tab:compcurve}
\begin{tabular}{@{}lrr@{}}
\toprule
stacked $a$ & Class B (coarse) & Class A (fine) \\
\midrule
""" + body + r""" \\
\bottomrule
\end{tabular}
""")

json.dump({'per_window': perwin, 'curve': curve,
           'occurrence_all': {'1e15': O15, '1e16': O16, '1e17': O17}},
          open('round10_stats.json', 'w'), indent=1)

print('per-window 50%% recovery amplitude (stacked S/N):')
for p in sorted(perwin, key=lambda p: (p['klass'], p['n_int'])):
    v = '  --  ' if p['a_fifty'] is None else '%6.2f' % p['a_fifty']
    print('  %-6s B%-2d n_int=%5d  a50=%s  a_min=%5.2f  rec=%3.0f%%'
          % (p['klass'], p['band'], p['n_int'], v, p['a_min'], 100 * p['rec_all']))
print('\nmeasurable a50: n=%d  %.2f-%.2f  median %.2f'
      % (len(fifty), min(fifty), max(fifty), st.median(fifty)))
print('saturated windows: n=%d, weakest injection a=%.2f, recovery %.0f%%'
      % (len(sat), satmin, 100 * satrec))
print('\npooled curve (coarse | fine):')
for i, L in enumerate(lab):
    print('  a %-6s  %-12s %-12s' % (L.replace('$', ''),
                                     cell(*curve['coarse'][i]),
                                     cell(*curve['fine'][i])))
print('\noccurrence at 1e16 W: coarse-inclusive %.1f%% over %d systems '
      '(fine-only %.1f%% over %d)'
      % (100 * O16['all'], O16['n_sys_all'], 100 * O16['measured'], O16['n_sys_fine']))
print('macros -> survey_numbers_round10.tex ; table -> tab_completeness_round10.tex')
