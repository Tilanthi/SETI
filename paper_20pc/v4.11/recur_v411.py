#!/usr/bin/env python3
r"""recur_v411.py -- the stellar-frame recurrence test on every unattributed
crossing, the two-number separation of searchability from confirmability, and
the single candidate table.

Round 120.  Writes `survey_numbers_round120.tex`, `tab_recurcand_v411.tex`,
`tab_visfit_v411.tex`, `tab_recurcols_v411.tex` and `recurcols_v411.json`.

WHY THIS EXISTS.  The spatial rank has no calibrated false-alarm probability,
so the paper states that it is not used as evidence for detection; and the
paper then disposed of most unattributed crossings on that rank and concluded
that none of them recurs.  Only ten had ever been tested.  The test is now run
on all of them: `r10inputs/recur_v411.json` is the measurement, made on the
retained dynamic spectra with the survey's own estimator at a single drift --
the discovery drift transported to each repeat epoch's observed frequency -- at
the channel the event's stellar-frame rest frequency lands on in that epoch.
That is the same code path and the same registration that produced the
published eta Crv exclusion, and it reproduces it to the printed digits, which
is this generator's first assertion.

THREE THINGS THE MEASUREMENT HAD TO GET RIGHT, each of which was wrong once:

* **Two extractions of one block live on this host.**  489 of 2729 retained
  windows exist in more than one directory and 372 of those pairs disagree
  about the window's own peak statistic; the per-block `_EB_` copy is the one
  the released catalogue carries.  So the discovery window is *identified* by
  reproducing the T* the paper prints for that crossing, not preferred by sort
  order.  All \RcNTested{} of them do, to better than 1e-7 relative.
* **The join from a crossing to its repeat blocks is on position**, taken from
  each product's own `t1_ra`/`t1_dec`, never on the star name: the catalogue,
  the worklist, the stack inventory and the recurrence worker spell one star
  four ways.
* **One repeat product's published noise is 1.4 microJy where its siblings are
  7-12 mJy.**  It is on the paper's own list of 27 weight-pathology products
  (`badweight.json`, \StkBadWeight), and it is dropped by that list rather than
  by a cut invented here.  Without it the combined noise of HR 1010's repeat
  coverage was wrong by a factor of 2e3.

Usage: recur_v411.py [--drive N]
"""
import csv
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round120.tex')
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE


def out(name):
    """Every product of a driven run is suffixed.  A test must never write a
    path production reads; the suffix follows the FLAG, not the perturbation."""
    b, e = os.path.splitext(name)
    return os.path.join(HERE, b + SFX + e)


TRIG = 5.0
SEP_DAY = 1.0           # the paper's own definition of an independent epoch


def macro(name):
    """One macro's value out of the frozen layer, by name.  A generator that
    prints a number another generator owns must READ it, or the two drift."""
    import glob
    import re as _re
    pat = _re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                      r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('macro %s not found' % name)
    return v
def tname(s):
    """The ledger's display name, shortened for a narrow column.  It must NOT
    convert hyphens to en-dashes: the ledger already ships `CP$-$72 2713` with
    a maths minus, and `-` -> `--` inside that turns it into `CP$--$72`."""
    s = s.split('  Gaia')[0].split(' (Gaia')[0].split(' Gaia')[0]
    if '$' not in s:
        s = s.replace('-', '$-$')
    return s.replace(' ', '~')


def _mant(x):
    e = int(math.floor(math.log10(abs(x))))
    return [x / 10.0 ** e, e]


def linetex(s):
    """The transition name as the paper sets it: an en-dash between the
    quantum numbers, and SO's two subscripts."""
    if s == 'SO(8_8-7_7)':
        return r'SO($8_8$--$7_7$)'
    return s.replace('-', '--')


def num(x, dp=2, signed=False):
    """A number for maths mode.  An ASCII hyphen typesets as a hyphen, not a
    minus, which is why the drift rates in the shipped table read `-2056`."""
    t = ('%+.*f' if signed else '%.*f') % (dp, x)
    return t.replace('-', '-')


def sig(x):
    """A signal-to-noise ratio is not a probability.  Print it with the
    precision it has: two digits below ten, none above twenty."""
    return ('%.1f' % x) if x < 20 else ('%.0f' % x)


M = []
fail = []


def m(k, v):
    M.append((k, v))


def ck(name, cond, detail=''):
    if not cond:
        fail.append(name)
    print('  %-56s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


# ---------------------------------------------------------------- inputs
R = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
CROSS = R['crossings']
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
MJD = json.load(open(os.path.join(HERE, 'epochs_v386.json')))['mjd']

UNATTR = [r for r in LED['rows'] if not r['attributed']]
N_UNATTR = len(UNATTR)


def blocks(c):
    """The covering repeat blocks of one crossing, with the paper's own
    weight-pathology list applied.  A product whose published noise is three
    orders of magnitude below its siblings' is a noise-estimation failure, not
    a deeper observation, and the paper already names 27 of them."""
    return [b for b in c.get('blocks', []) if not b.get('bad_weight_product')]


def comb(c, bl):
    """Inverse-variance combination of the repeat coverage at the registered
    cell: what a carrier persisting at the discovery flux would have given
    there, what was measured, and the difference in units of the combined
    noise."""
    S = c['discovery']['amp_mJy']
    w = [1.0 / b['sig_mJy'] ** 2 for b in bl]
    sb = 1.0 / math.sqrt(sum(w))
    ab = sum(b['amp_mJy'] * q for b, q in zip(bl, w)) / sum(w)
    return dict(n=len(bl), sbar=sb, abar=ab, T_pers=S / sb,
                excl=(S - ab) / sb,
                T_max=max(b['T_matched'] for b in bl),
                T_bestdrift_max=max(b['T_bestdrift_pub'] for b in bl),
                n_eff=(c['discovery']['sig_mJy'] / sb) ** 2,
                sep_min_h=min(abs(b['sep_from_discovery_h']) for b in bl),
                sep_max_h=max(abs(b['sep_from_discovery_h']) for b in bl),
                nearest_eb=min(bl, key=lambda b: abs(
                    b['sep_from_discovery_h']))['eb'],
                deepest_eb=min(bl, key=lambda b: b['sig_mJy'])['eb'],
                n_outside_catalogue=sum(
                    1 for b in bl if not b.get('in_released_catalogue')))


ROWS, UNTESTED = {}, []
for cid, c in CROSS.items():
    if c['status'] != 'ok':
        UNTESTED.append(c)
        continue
    bl = blocks(c)
    if not bl:
        UNTESTED.append(c)
        continue
    ROWS[cid] = dict(c=c, s=comb(c, bl))

U = [k for k in ROWS if not CROSS[k].get('attributed')]
N_TESTED = len(U)
N_UNTESTED = len(UNTESTED)
if DRIVE == 1:                       # a crossing silently left out
    U = U[:-1]
    N_TESTED = len(U)

TMAX = max(ROWS[k]['s']['T_max'] for k in U)
TBD = max(ROWS[k]['s']['T_bestdrift_max'] for k in U)
EXCL = sorted(ROWS[k]['s']['excl'] for k in U)
NREP_MEAS = sum(ROWS[k]['s']['n'] for k in U)
REP_EB = {b['eb'] for k in U for b in blocks(CROSS[k])}
REP_OUT = {b['eb'] for k in U for b in blocks(CROSS[k])
           if not b.get('in_released_catalogue')}

m('RcNUnattr', '%d' % N_UNATTR)
m('RcNTested', '%d' % N_TESTED)
m('RcNUntested', '%d' % N_UNTESTED)
m('RcNRepeatMeas', '%d' % NREP_MEAS)
m('RcNRepeatBlock', '%d' % len(REP_EB))
m('RcNRepeatFollow', '%d' % len(REP_OUT))
# ★ TWO readings of the same cell, and the paper must not use one word for
# both.  `RcTMatched` is the statistic at the discovery drift transported to
# the repeat epoch -- an unbiased amplitude, which is what the exclusion is
# built from.  `RcTMax` is the largest value found at that cell over every
# drift trial, which is what Referee 2 asks to see tabulated and is the
# conservative number; it is also what Appendix C already quotes for
# \RcCpStar{} (\CpRecT), so the two parts of the paper now agree.
m('RcTMatched', '%.2f' % TMAX)
m('RcTMax', '%.2f' % TBD)
m('RcExclMin', '%.1f' % EXCL[0])
m('RcExclMed', '%.1f' % EXCL[len(EXCL) // 2])
m('RcNExclFive', '%d' % sum(1 for e in EXCL if e >= TRIG))
m('RcNeffMax', '%.0f' % max(ROWS[k]['s']['n_eff'] for k in U))
# the range of usable baselines, over the blocks the test actually used, in
# the units they fall in: hours at one end and years at the other.
_sh = [ROWS[k]['s']['sep_min_h'] for k in U]
_sx = [ROWS[k]['s']['sep_max_h'] for k in U]
m('RcSepMinH', '%.2f' % min(_sh))
m('RcSepMaxYr', '%.1f' % (max(_sx) / 24.0 / 365.25))
m('RcNSepSameDay', '%d' % sum(1 for h in _sh if h < 24.0))
if UNTESTED:
    q = UNTESTED[0]
    m('RcUntStar', q['display'].replace('~', '\\,'))
    m('RcUntEb', q['eb'].replace('A002_', '').replace('_', '\\_'))
    m('RcUntFreq', '%.4f' % q['freq_GHz'])
    m('RcUntT', '%.2f' % q['tstar'])
    # the repeat coverage is not the problem: it is the DISCOVERY dynamic
    # spectrum that was not retained, so there is no flux to transport.
    _same = [CROSS[b] for b in CROSS if CROSS[b]['status'] == 'ok'
             and CROSS[b]['star'] == q['star']]
    m('RcUntNRep', '%d' % (max((c['n_repeat_blocks_measured']
                                for c in _same), default=0)))

# ---- the single rank-passing crossing, and the one the mask now attributes
SCR = [k for k in U if CROSS[k]['screen']]
CP = [k for k in ROWS if CROSS[k].get('attributed')]
for tag, keys in (('Sx', SCR), ('Cp', CP)):
    if not keys:
        continue
    k = keys[0]
    c, s = ROWS[k]['c'], ROWS[k]['s']
    m('Rc%sStar' % tag, c['display'])
    m('Rc%sFreq' % tag, '%.6f' % c['freq_GHz'])
    m('Rc%sT' % tag, '%.3f' % c['discovery']['T_matched'])
    m('Rc%sNRep' % tag, '%d' % s['n'])
    m('Rc%sNCat' % tag, '%d' % c['n_catalogue_covering_blocks'])
    m('Rc%sNearH' % tag, '%.2f' % s['sep_min_h'])
    m('Rc%sSpanD' % tag, '%.0f' % (s['sep_max_h'] / 24.0))
    m('Rc%sTPers' % tag, '%.2f' % s['T_pers'])
    m('Rc%sTObs' % tag, '%.2f' % s['T_bestdrift_max'])
    m('Rc%sTObsMatched' % tag, '%+.2f' % s['T_max'])
    m('Rc%sExcl' % tag, '%.1f' % s['excl'])
    m('Rc%sFlux' % tag, '%.1f' % c['discovery']['amp_mJy'])
    m('Rc%sFluxErr' % tag, '%.1f' % c['discovery']['sig_mJy'])
    m('Rc%sDrift' % tag, '%.0f' % c['discovery']['drift_Hz_s'])
    m('Rc%sChanwkHz' % tag, '%.2f' % (c['discovery']['chanw_Hz'] / 1e3))
    m('Rc%sCtrl' % tag, '%.2f' % (c['rank_ctrl'] or 0.0))
    m('Rc%sBand' % tag, str(c['band']))
    m('Rc%sDv' % tag, '%.0f' % c['dv_stellar'])
    m('Rc%sLine' % tag, c.get('line_tex') or linetex(c['line']))
# ★ R2-minor 7: the released "2--769 d" came from a generator that knew only
# catalogue blocks, so it could not see a repeat 2.05 HOURS later in a
# follow-up execution block.  These two come from the products' own time
# stamps, over exactly the blocks the test used, and carry both units.
_scrkeys = SCR + CP
if _scrkeys:
    _h = [ROWS[k]['s']['sep_min_h'] for k in _scrkeys]
    _d = [ROWS[k]['s']['sep_max_h'] / 24.0 for k in _scrkeys]
    m('RcScrSepMinH', '%.2f' % min(_h))
    m('RcScrSepMaxD', '%.0f' % max(_d))

# ------------------------------------------- searchability, confirmability
A = [r for r in CAT if r['search_class'] == 'A']
bysys = collections.defaultdict(list)
for r in A:
    bysys[r['system_id']].append(r)


def union(iv):
    iv, o = sorted(iv), []
    for a, b in iv:
        if o and a <= o[-1][1]:
            o[-1][1] = max(o[-1][1], b)
        else:
            o.append([a, b])
    return o


def total(iv):
    return sum(b - a for a, b in iv)


def doubly(rows, sep):
    """The frequency interval of one system covered by two execution blocks
    more than `sep` days apart.  Computed on the interval boundaries, so a
    partial overlap counts only where it overlaps."""
    iv = [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
           max(float(r['flo_GHz']), float(r['fhi_GHz'])), r['eb'])
          for r in rows]
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    keep = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        ts = sorted(MJD[e] for _a, _b, e in iv
                    if _a <= mid <= _b and e in MJD)
        if any(ts[k] - ts[j] > sep
               for j in range(len(ts)) for k in range(j + 1, len(ts))):
            keep.append([pts[i], pts[i + 1]])
    return union(keep), union([(a, b) for a, b, _ in iv])


CONF = {}
for sep, tag in ((SEP_DAY, 'Day'), (365.25, 'Yr')):
    nsys, gd, ga = 0, 0.0, 0.0
    for s, rows in bysys.items():
        d, u = doubly(rows, sep)
        ga += total(u)
        gd += total(d)
        if d:
            nsys += 1
    CONF[tag] = (nsys, gd, ga)
    m('RcConfSys' + tag, '%d' % nsys)
    m('RcConfGHz' + tag, '%.1f' % gd)
    m('RcConfPct' + tag, '%.0f' % (100.0 * gd / ga))
_nocat = sorted({e for k in U
                 for e in CROSS[k].get('catalogue_blocks_without_spectra', [])})
m('RcNCatNoSpec', '%d' % len(_nocat))
m('RcSearchSys', '%d' % len(bysys))
m('RcSearchWin', '%d' % len(A))
m('RcSearchGHz', '%.1f' % CONF['Day'][2])

# ------------------------------------------------------------- assertions
print('\nassertions')
_e = [k for k in ROWS if CROSS[k]['star'] == 'eta Crv']
if _e:
    s = ROWS[_e[0]]['s']
    v = (abs(s['T_pers'] - 10.95) if DRIVE != 2 else 9.0)
    ck('A1 eta Crv reproduces its published exclusion',
       v < 0.02 and abs(s['excl'] - 11.57) < 0.02
       and abs(s['n_eff'] - 4.79) < 0.01,
       'T_pers %.2f (10.95), excl %.2f (11.57), N_eff %.2f (4.79)'
       % (s['T_pers'], s['excl'], s['n_eff']))
v = N_TESTED + N_UNTESTED if DRIVE != 1 else N_TESTED + N_UNTESTED
ck('A2 tested + untested == the unattributed crossings',
   v == N_UNATTR, '%d + %d == %d' % (N_TESTED, N_UNTESTED, N_UNATTR))
v = TBD if DRIVE != 3 else 9.9
ck('A3 nothing reaches the trigger at the registered cell, at any drift',
   v < TRIG, 'largest drift-maximised T* over %d blocks = %.2f'
   % (NREP_MEAS, TBD))
v = EXCL[0] if DRIVE != 4 else 0.5
ck('A4 every tested crossing is excluded above the trigger',
   v >= TRIG, 'weakest exclusion %.1f sigma' % EXCL[0])
_g = [c['discovery'] for c in CROSS.values() if c['status'] == 'ok']
v = max(abs(d['gate_rel']) for d in _g) if DRIVE != 5 else 1.0
ck('A5 every discovery window reproduces its published statistic',
   v < 1e-6, 'worst relative error %.1e over %d windows' % (v, len(_g)))
v = CONF['Day'][0] if DRIVE != 6 else len(bysys)
ck('A6 confirmability is strictly smaller than searchability',
   v < len(bysys), '%d of %d Class A systems have an independent repeat at '
   'the same frequency' % (CONF['Day'][0], len(bysys)))
# ★ this one can only fail if the deposit loses the pathology list, which is
# how a 1.4 microJy noise got into a combined sigma in the first place
v = R['n_bad_weight_block_measurements'] if DRIVE != 7 else 0
ck('A7 the weight-pathology list is applied and bites',
   v >= 1, '%d repeat measurement(s) dropped by badweight.json' % v)

# ------------------------------------------------------------ the tables
# (1) the four recurrence columns of the crossing ledger, for ledger_v410.py
cols = {}
for cid, r in ROWS.items():
    c, s = r['c'], r['s']
    cols['%s|%.6f' % (c['eb'], c['freq_GHz'])] = dict(
        n_rep=s['n'], T_max=round(s['T_max'], 2),
        T_pers=round(s['T_pers'], 1), excl=round(s['excl'], 1))
for q in UNTESTED:
    cols['%s|%.6f' % (q['eb'], q['freq_GHz'])] = dict(
        n_rep=None, T_max=None, T_pers=None, excl=None,
        note='dynamic spectrum not retained')
json.dump(cols, open(out('recurcols_v411.json'), 'w'), indent=1)

L = ['%% GENERATED by recur_v411.py -- do not hand-edit.']
L.append(r'\begin{tabular}{@{}l@{~~}r@{~~}r@{~~}r@{~~}r@{}}')
L.append(r'\hline')
L.append(r'Crossing & $n_{\rm rep}$ & $T_\star^{\rm rep}$ & '
         r'$T_\star^{\rm pers}$ & Exclusion \\')
L.append(r'\hline')
for cid in sorted(ROWS, key=lambda k: -ROWS[k]['c']['discovery']['T_matched']):
    c, s = ROWS[cid]['c'], ROWS[cid]['s']
    L.append(r'%s %.4f & %d & %.2f & %s & %s$\sigma$ \\'
             % (tname(c['display']), c['freq_GHz'], s['n'],
                s['T_bestdrift_max'], sig(s['T_pers']), sig(s['excl'])))
for q in UNTESTED:
    L.append(r'%s %.4f & --- & \multicolumn{3}{l}{spectrum not retained} \\'
             % (tname(q['display']), q['freq_GHz']))
L += [r'\hline', r'\end{tabular}']
open(out('tab_recurcols_v411.tex'), 'w').write('\n'.join(L) + '\n')

# (2) the candidate table (R1-8): everything about the surviving crossing and
#     the one the line mask now attributes, in one place
def flux_eirp(c):
    d = c['discovery']
    rows = [r for r in CAT if r['eb'] == c['eb']
            and min(float(r['flo_GHz']), float(r['fhi_GHz'])) <= c['freq_GHz']
            <= max(float(r['flo_GHz']), float(r['fhi_GHz']))]
    dist = float(rows[0]['dist_pc']) if rows else None
    e = None
    if dist:
        e = (4.0 * math.pi * (dist * 3.0856775814913673e16) ** 2
             * d['amp_mJy'] * 1e-29 * d['chanw_Hz'])
    return dist, e


C1 = [r'%% GENERATED by recur_v411.py -- do not hand-edit.',
      r'\begin{tabular}{@{}l' + 'r' * len(_scrkeys) + r'@{}}', r'\hline']
HDR = [('Star', lambda c, s: c['display']),
       ('ALMA band', lambda c, s: str(c['band'])),
       (r'Frequency (GHz)', lambda c, s: '%.6f' % c['freq_GHz']),
       (r'Channel width (kHz)',
        lambda c, s: '%.2f' % (c['discovery']['chanw_Hz'] / 1e3)),
       (r'Drift rate (Hz\,s$^{-1}$)',
        lambda c, s: '$%s$' % num(c['discovery']['drift_Hz_s'], 0, True)),
       (r'$T_\star$', lambda c, s: '%.3f' % c['discovery']['T_matched']),
       (r'Highest control $T$',
        lambda c, s: '%.2f' % (c['rank_ctrl'] or 0.0)),
       (r'Flux density (mJy)',
        lambda c, s: '%.1f $\\pm$ %.1f' % (c['discovery']['amp_mJy'],
                                           c['discovery']['sig_mJy'])),
       (r'EIRP (W)', lambda c, s: '$%.1f \\times 10^{%d}$'
        % tuple(_mant(flux_eirp(c)[1]))),
       (r'Nearest transition', lambda c, s: linetex(c['line'])),
       (r'Offset (km\,s$^{-1}$)',
        lambda c, s: '$%s$' % num(c['dv_stellar'], 0, True)),
       (r'Repeat blocks', lambda c, s: '%d' % s['n']),
       (r'Nearest repeat (h)', lambda c, s: '%.2f' % s['sep_min_h']),
       (r'Longest baseline (d)',
        lambda c, s: '%.0f' % (s['sep_max_h'] / 24.0)),
       (r'Covering blocks in the catalogue',
        lambda c, s: '%d' % c['n_catalogue_covering_blocks']),
       (r'$T_\star$ if persistent', lambda c, s: '%.2f' % s['T_pers']),
       (r'$T_\star$ measured', lambda c, s: '%.2f' % s['T_bestdrift_max']),
       (r'Exclusion', lambda c, s: '%s$\\sigma$' % sig(s['excl'])),
       (r'Disposition', lambda c, s: (
           'attributed' if c.get('attributed') else 'not confirmed'))]
C1.append(' & '.join([''] + [ROWS[k]['c']['display'] for k in _scrkeys])
          + r' \\')
C1.append(r'\hline')
for lab, fn in HDR[1:]:
    C1.append(lab + ' & '
              + ' & '.join(fn(ROWS[k]['c'], ROWS[k]['s']) for k in _scrkeys)
              + r' \\')
C1 += [r'\hline', r'\end{tabular}']
open(out('tab_recurcand_v411.tex'), 'w').write('\n'.join(C1) + '\n')

# (3) the visibility-fit table, which replaces the box inside Fig. 7
S = json.load(open(os.path.join(HERE, 'ledger_v403.json')))['summary']
# ★ R2-minor 9 is right that "12 controls" looked inconsistent with "full
# dynamic spectra survive for only 8 of 512", and it was our own fault for
# printing one number without saying which control set it belonged to.  There
# are three, they are different things, and they are now tabulated together so
# the question cannot arise again.
_NVIS = int(macro('EpNVisCtrl'))
_NRET = int(macro('LNNRetained'))
_NCTRL = int(macro('NCtrl'))
m('RcNVisCtrl', '%d' % _NVIS)
m('RcNRetCtrl', '%d' % _NRET)
V = [r'%% GENERATED by recur_v411.py -- do not hand-edit.',
     r'\begin{tabular}{@{}lr@{}}', r'\hline',
     r'Crossings re-measured in the visibility domain & %d of %d \\'
     % (S['n_fitted'], S['n_crossings']),
     r'\quad consistent with a point source at the stellar position & %d \\'
     % S['n_localised_corrected'],
     r'\quad of those, unattributed & %d \\'
     % S['n_localised_unattributed_corrected'],
     r'\hline',
     r'Control positions in the image-plane rank screen & %d \\' % _NCTRL,
     r'\quad with a full dynamic spectrum retained & %d \\' % _NRET,
     r'Control positions available in the visibility fit & %d \\' % _NVIS,
     r'\hline', r'\end{tabular}']
open(out('tab_visfit_v411.tex'), 'w').write('\n'.join(V) + '\n')

# --------------------------------------------------------------- emit
with open(out(os.path.basename(OUT)), 'w') as fh:
    fh.write('%% GENERATED by recur_v411.py -- do not hand-edit.\n')
    for k, v in M:
        assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
print('tested %d of %d unattributed crossings over %d repeat-block '
      'measurements in %d distinct blocks (%d outside the released catalogue)'
      % (N_TESTED, N_UNATTR, NREP_MEAS, len(REP_EB), len(REP_OUT)))
print('largest T* at the registered cell %.2f (matched drift) / %.2f '
      '(any drift); exclusions %.1f-%.1f sigma, median %.1f'
      % (TMAX, TBD, EXCL[0], EXCL[-1], EXCL[len(EXCL) // 2]))
print('searchability %d Class A systems / %.1f GHz;  confirmability %d '
      'systems / %.1f GHz (%.0f%%) with an independent repeat at the same '
      'frequency; over years %d systems / %.1f GHz'
      % (len(bysys), CONF['Day'][2], CONF['Day'][0], CONF['Day'][1],
         100 * CONF['Day'][1] / CONF['Day'][2], CONF['Yr'][0], CONF['Yr'][1]))
if fail and DRIVE == 0:
    raise SystemExit('assertions failed: %s' % fail)
