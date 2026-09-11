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

# ============================================================================
# Round-11 (v3.41) additions: referee-driven macros.  Everything below is
# derived from the SAME frozen export; nothing is hand-typed.
# ============================================================================
import math as _m
_d = json.load(open('frozen_export_v3.31.json'))
_rows = _d['rows']
def _band(r):
    if r['band'] is not None: return r['band']
    f = 0.5*(r['flo']+r['fhi'])
    for lo,hi,b in [(84,116,3),(125,163,4),(163,211,5),(211,275,6),(275,373,7),(385,500,8)]:
        if lo<=f<hi: return b
for r in _rows:
    r['band_x']=_band(r); r['res_x']='fine' if r['chanw']<5e6 else 'coarse'
    r['qa']=r['rms']*_m.sqrt(r['onsrc']*r['chanw'])
    r['cmax']=max(r['ctrl_all']) if r['ctrl_all'] else r['ctrl_max']
_k=lambda r:(r['star_name'],r['eb'],round(min(r['flo'],r['fhi']),6),
             round(max(r['flo'],r['fhi']),6),r['chanw'])
_b={}
for r in _rows:
    if _k(r) not in _b or (_b[_k(r)]['line'] is None and r['line'] is not None): _b[_k(r)]=r
_u=list(_b.values()); _qm=st.median(r['qa'] for r in _u)
_kept=[r for r in _u if r['qa']>=_qm/100.0]
GOOD=[r for r in _kept if not (r['star_name']=='eps Eri' and r['band_x']==6)]
assert len(GOOD)==431, len(GOOD)

N2 = []
def M2(name, val): N2.append('\\newcommand{\\%s}{%s}' % (name, val))

# --- exposure: gross searched bandwidth (was hand-typed 700.8) --------------
GROSS = sum(abs(r['fhi']-r['flo']) for r in GOOD)
M2('GrossBwGHz', '%.1f' % GROSS)

# --- Gaussian-expected chance crossings over the whole trial grid -----------
CELLS = sum(int(abs(r['fhi']-r['flo'])*1e9/r['chanw'])*r['ndrift'] for r in GOOD)
P5 = 0.5*_m.erfc(5.0/_m.sqrt(2.0))
M2('GaussCross', '%.1f' % (CELLS*P5))

# --- Poisson tail of the flag budget: P(>=4 | expected) --------------------
MU = S['expected_flags']
_pk = [_m.exp(-MU)*MU**k/_m.factorial(k) for k in range(4)]
M2('PgeFourPct', '%.1f' % (100.0*(1.0-sum(_pk))))

# --- the one unattributed crossing against the non-beta-Pic window count ----
NBP = sum(1 for r in GOOD if r['star_name'] != 'bet Pic')
EXP_NBP = NBP/(S['n_ctrl']+1.0)
M2('ExpNonBP', '%.2f' % EXP_NBP)
M2('PgeOneNonBPPct', '%.0f' % (100.0*(1.0-_m.exp(-EXP_NBP))))

# --- flagged-window peak flux densities (T* x per-channel rms, mJy) ---------
FLAG = {(r['star_name'], r['band_x']): r
        for r in GOOD if r['star_snr'] >= 5.0 and r['star_snr'] > r['cmax']}
assert len(FLAG) == 4, sorted(FLAG)
def _pk_mjy(star, band): 
    r = FLAG[(star, band)]; return r['star_snr']*r['rms']
M2('FluxBpicThree', '%.0f' % _pk_mjy('bet Pic', 3))
M2('FluxBpicSix',   '%.0f' % _pk_mjy('bet Pic', 6))
M2('FluxHdFour',    '%.2f' % (_pk_mjy('HD 48370', 6)/1e3))      # Jy
M2('FluxCpSeven',   '%.0f' % _pk_mjy('CP-72 2713', 7))
M2('FluxRatioBpic', '%.1f' % (_pk_mjy('bet Pic', 6)/_pk_mjy('bet Pic', 3)))

# --- the frozen mask's rest frequencies are stored rounded to 1 MHz ---------
# Recovered without using any number printed in the manuscript: a crossing
# lies on the window's channel grid, so snapping (laboratory rest + released
# offset) to that grid and subtracting the offset returns the catalogue entry
# the pipeline actually used.
LAB = {'CO(1-0)': 115.271202, 'CO(2-1)': 230.538000, 'CO(3-2)': 345.795990,
       'CO(4-3)': 461.040768, '13CO(2-1)': 220.398684, 'C18O(2-1)': 219.560354,
       'CS(5-4)': 244.935556, 'SiO(5-4)': 217.104980}
_cat = collections.defaultdict(list)
for r in GOOD:
    L = r['line']
    if L in LAB and r['line_off'] is not None and r['chanw'] < 1e6:
        lo = min(r['flo'], r['fhi']); cw = r['chanw']/1e9
        f = LAB[L] + r['line_off']*1e-3
        _cat[L].append(lo + round((f-lo)/cw)*cw - r['line_off']*1e-3)
CATCO = st.median(_cat['CO(1-0)'])                      # 115.271000
M2('MaskRestRoundMHz', '1')
M2('CatCOoneGHz', '%.6f' % CATCO)
M2('LabCOoneGHz', '%.6f' % LAB['CO(1-0)'])
M2('CatCOerrMHz', '%.3f' % (1e3*(LAB['CO(1-0)'] - CATCO)))
M2('CatCOerrKms', '%.2f' % (299792.458*(LAB['CO(1-0)']-CATCO)/LAB['CO(1-0)']))
M2('CatWorstKms', '%.1f' % (299792.458*5e-4/LAB['CO(1-0)']))   # +-0.5 MHz at 115 GHz

# --- flagged-window offsets referred to the LABORATORY rest frequencies -----
C = 299792.458
def _fcat(line):
    return st.median(_cat[line]) if _cat[line] else LAB[line]
def _cross(r, line):
    """Crossing frequency = the pipeline's own arithmetic inverted:
    released offset is measured from the frozen catalogue entry."""
    return _fcat(line) + r['line_off']*1e-3
def _row(star, band, line):
    r = FLAG[(star, band)]
    fx = _cross(r, line)
    dnu = (fx - LAB[line])*1e3                                   # MHz, lab-referred
    return fx, dnu, C*dnu*1e-3/LAB[line]
for tag, star, band, line in (('BpicThree','bet Pic',3,'CO(1-0)'),
                              ('BpicSix','bet Pic',6,'CO(2-1)'),
                              ('HdFour','HD 48370',6,'CO(2-1)'),
                              ('CpSeven','CP-72 2713',7,'CO(3-2)')):
    fx, dnu, dv = _row(star, band, line)
    M2('Fobs'+tag, '%.6f' % fx)
    M2('Dnu'+tag, '%.2f' % dnu)
    M2('Dv'+tag, '%.1f' % dv)
    M2('Fcen'+tag, '%.4f' % (0.5*(FLAG[(star, band)]['flo']+FLAG[(star, band)]['fhi'])))

# --- the beta Pic frame chain, recomputed from the lab-referred offset ------
# stellar-frame offset = topocentric - barycentric correction + v_sys
BARY = {'BpicThree': -7.90, 'BpicSix': -8.15, 'BpicCoarse': +7.63}
VSYS_BPIC = 16.84
_f3, _d3, _v3 = _row('bet Pic', 3, 'CO(1-0)')
_f6, _d6, _v6 = _row('bet Pic', 6, 'CO(2-1)')
_stel3 = _v3 - BARY['BpicThree'] + VSYS_BPIC
_stel6 = _v6 - BARY['BpicSix'] + VSYS_BPIC
_flag6 = FLAG[('bet Pic', 6)]
_coarse = [r for r in GOOD if r['star_name']=='bet Pic' and r['band_x']==6
           and r is not _flag6 and r['line']=='CO(2-1)'
           and r['line_off'] is not None and abs(r['line_off'])<50]
_rc = min(_coarse, key=lambda r: abs(r['line_off']))
_fc = _cross(_rc, 'CO(2-1)')
_dnc = (_fc - LAB['CO(2-1)'])*1e3
_vc = C*_dnc*1e-3/LAB['CO(2-1)']
_stelc = _vc - BARY['BpicCoarse'] + VSYS_BPIC
M2('DnuBpicCoarse', '%.2f' % _dnc); M2('DvBpicCoarse', '%.2f' % _vc)
M2('StelBpicThree', '%.2f' % _stel3)
M2('StelBpicSix', '%.2f' % _stel6)
M2('StelBpicCoarse', '%.2f' % _stelc)
M2('BpicSpreadKms', '%.1f' % (max(_stel3,_stel6,_stelc)-min(_stel3,_stel6,_stelc)))
M2('BpicPairSepKms', '%.2f' % abs(_stel3-_stel6))

with open('survey_numbers_round11.tex', 'w') as f:
    f.write('%% GENERATED by round10_calc.py (v3.41 block) -- do not hand-edit.\n')
    f.write('\n'.join(N2) + '\n')

# --- generated occurrence table (was hand-typed in rows 3 and 5) ------------
def _pc(x): return 'unconstrained' if x is None else '%.1f\\%%' % (100.0*x)
_P = [('$3\\times10^{13}$','3e+13'), ('$10^{14}$','1e+14'), ('$10^{15}$','1e+15'),
      ('$10^{16}$','1e+16'), ('$10^{17}$','1e+17')]
_rowsA = ' \\\\\n'.join(
    '%s & %d & %s & %d & %s' % (lab, S['occurrence'][k]['n_sys'],
        _pc(S['occurrence'][k]['unit']), S['occurrence'][k]['n_sys_fine'],
        _pc(S['occurrence'][k]['measured'])) for lab, k in _P)
_O = S['occurrence']['1e+16']
_rowsB = ' \\\\\n'.join('%s & %s & %s' % (lab, _pc(_O[u]), _pc(_O[mm])) for lab, u, mm in
    (('1 (continuous)','unit','measured'), ('0.5','unit_D05','measured_D05'),
     ('0.1','unit_D01','measured_D01'), ('0.01','unit_D001','measured_D001')))
with open('tab_occurrence.tex','w') as f:
    f.write('%% GENERATED by round10_calc.py -- do not hand-edit.\n'
            '\\emph{(a)}\\\\[2pt]\n\\begin{tabular}{@{}lrrrr@{}}\n\\toprule\n'
            '$P$ (W) & \\multicolumn{2}{c}{thresholded (unit $C$)} &\n'
            '\\multicolumn{2}{c}{measured $C$} \\\\\n'
            ' & $n$ & $f_{95}$ & $n$ & $f_{95}$ \\\\\n\\midrule\n'
            + _rowsA + ' \\\\\n\\bottomrule\n\\end{tabular}\n\n\\smallskip\n'
            '\\emph{(b)}\\\\[2pt]\n\\begin{tabular}{@{}lrr@{}}\n\\toprule\n'
            'Epoch activity $p_{\\rm epoch}$ & $f_{95}$ thresholded & $f_{95}$ measured \\\\\n'
            '\\midrule\n' + _rowsB + ' \\\\\n\\bottomrule\n\\end{tabular}\n')
print('\nv3.41 block -> survey_numbers_round11.tex, tab_occurrence.tex')
for x in N2: print('  ', x)
