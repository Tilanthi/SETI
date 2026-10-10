#!/usr/bin/env python3
r"""Round 540.  THE INTRA-INTEGRATION SMEARING CORRECTION, APPLIED.

★★★ WHY THIS FILE EXISTS.  The injection campaign deposits each artificial
carrier at ONE frequency per integration, so it carries the channel response
and the drift BETWEEN integrations but not the sweep WITHIN one.  A real
drifting carrier loses amplitude to that sweep, so the campaign measures the
recovery of a signal slightly easier to find than the one being searched for.
Until this round the loss was computed and then declared, on the grounds that
the released catalogue has no column for it.  That is backwards: an unmodelled
reduction in recovery efficiency is a CORRECTION TO APPLY, not an uncertainty
to declare, and it is a different kind of thing from the uncertainty on a
calibration factor -- the two must not be combined.  So it is applied here,
window by window, and the deposit is regenerated to carry it.

★ THE DRIFT THAT SETS THE CORRECTION IS THE ONE RELEVANT TO THE QUOTED LIMIT,
AND IT IS MEASURED, NOT ASSUMED.  EIRP_90 is a NINETY PER CENT point over
carriers injected at a drift drawn from each window's own grid.  The power
needed to recover a carrier scales as 1/eta_smear, so the power at which nine
in ten come back is set by the NINETIETH PERCENTILE of 1/eta over that drift
distribution -- that is, by eta at the ninetieth percentile of |drift|.  That
percentile is read off the campaign's own tone records (every in-band injected
tone, each with its own drift rate and its own window's drift ceiling) instead
of being assumed uniform; the uniform draw the campaign plan specifies would
give exactly 0.900, and the measured value is asserted to agree with it.

Three conventions exist and all three are reported, so that the one adopted is
visible as a choice: the drift CEILING (the worst case, which is what earlier
rounds quoted), the ninetieth percentile (adopted), and the mean over the grid.

★ WHERE A WINDOW'S INTEGRATION LENGTH IS NOT RECORDED THE TERM IS BOUNDED AND
SAID TO BE.  The release carries an integration count for 451 windows; the
campaign's own exposure scan recovers 595 more on a join that is validated
where the two overlap; the remaining windows are bounded at the longest
integration delivered anywhere in the campaign.  Nothing is imputed: a bounded
window gets the bound, which can only make its limit worse, and the deposit
says which of the two it is.

★★ AND THE ANALYTIC ROUTE IS CHECKED AGAINST THE CAMPAIGN ITSELF.  For each of
the 49 directly injected windows the measured recovery ladder is re-scored with
every tone's amplitude de-rated by that tone's OWN eta, and the ninety per cent
point re-read.  That is a measurement of the same quantity through the same
pipeline, and it is compared window by window with the analytic factor.

Output: survey_numbers_round540.tex, smear_r15.json, and the regenerated
deposit (see `--deposit`).

    python3 smear_r15.py                 # macros + json, no deposit written
    python3 smear_r15.py --deposit       # also rewrite the released catalogue
    python3 smear_r15.py --drive N       # perturbation N; see DRIVES below

DRIVES (each must make a named assertion fail, and each has been shown to):
    1  the measured drift percentile is forced to the ceiling   -> Q1
    2  a tone is given a drift above its window's ceiling       -> Q2
    3  the integration-length bound is shrunk below the longest
       measured integration, so the bound bounds nothing        -> Q3
    4  the measured/bounded/absent groups are not a partition   -> Q4
    5  the correction is applied in the optimistic direction    -> Q5
    6  the injected-window join is made many-to-one             -> Q6
    7  an estimated window is labelled as a measured one        -> Q7
    8  the analytic factor is divorced from the re-scored one    -> Q8
    9  the corrected count at 1e15 W is left at the uncorrected
       value, i.e. the correction is computed and not applied   -> Q9
   10  the window-to-window dispersion is narrowed inside the
       calibration interval, so the two could be interchanged   -> Q10
   11  a window is deposited with no smearing factor, so the
       deposit cannot close on the published limit               -> Q11
   12  the regeneration moves a column it has no business in     -> Q12
   13  the Class B factor used here parts from the one the macro
       layer publishes                                          -> Q13
"""
import collections
import csv
import json
import math
import os
import statistics as st
import sys

ROUND = 540
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DRIVE = 0
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
DEPOSIT = '--deposit' in sys.argv

# ★ D36: the suffix follows the FLAG, not the perturbation, so a driven run
# can never write a path production reads.
SUF = '' if '--drive' not in sys.argv else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round540%s.tex' % SUF)
OUTJSON = os.path.join(HERE, 'smear_r15%s.json' % SUF)
CAT_NAME = 'per_target_results_v3.99.csv'
DEPOSIT_OUT = os.path.join(HERE, CAT_NAME if not SUF
                           else CAT_NAME.replace('.csv', SUF + '.csv'))

FAIL = []


def ck(name, cond, detail=''):
    print('  %-74s %s  %s' % (name[:74], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(name)


LINES = ['%% GENERATED by smear_r15.py (round %d) -- do not hand-edit.\n'
         % ROUND]


def m(name, val):
    # ★ 15th defect class: a LaTeX macro name may contain letters only.
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    LINES.append('\\newcommand{\\%s}{%s}\n' % (name, val))


def texval(name):
    """A generated macro's value, following the manuscript's \\input order."""
    import re
    import glob
    main = [f for f in sorted(os.listdir(HERE))
            if f.startswith('technosignatures_') and f.endswith('.tex')]
    order = []
    if len(main) == 1:
        order = [x + '.tex' for x in re.findall(
            r'\\input\{(survey_numbers[A-Za-z0-9_]*)\}',
            open(os.path.join(HERE, main[0]), errors='ignore').read())]
    have = {os.path.basename(p) for p in
            glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))}
    files = [f for f in order if f in have] + sorted(have - set(order))
    pat = re.compile(r'\\(?:new|renew)command\{\\%s\}\{([^{}]*)\}' % name)
    out = None
    for f in files:
        for mm in pat.finditer(open(os.path.join(HERE, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                out = mm.group(1).strip()
    assert out is not None, 'macro \\%s is not generated anywhere' % name
    return out


def texnum(name):
    return float(texval(name).replace('\\,', '').replace(',', ''))


def texnum_opt(name):
    """The macro's value if the macro layer defines it yet, else None.

    ★ NOT a silent skip.  Two of the identities below are against macros a
    LATER generator writes -- \\CsNDumpWin is round 195 and \\NSysEfifteen is
    round 103, and this file has to run before both, because round 103 reads
    the deposit column this file writes.  On a tree that already carries the
    macro files the comparison is made; on a clean regeneration it cannot be,
    and the check that owns it then is `ledger_r14.py` (round 450), which runs
    after both and asserts the same identities.  Which path was taken is
    printed and recorded in the json, so an absent macro is visible rather
    than absorbed."""
    try:
        return float(texval(name).replace('\\,', '').replace(',', ''))
    except AssertionError:
        return None


def sci(x, sf=2):
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sf - 1, x / 10.0 ** e, e)


def sinc(x):
    return math.sin(x) / x if x else 1.0


print('smear_r15 round %d%s' % (ROUND, '' if not DRIVE
                                else ' (drive %d)' % DRIVE))

# ------------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(HERE, CAT_NAME))))
SCAN = json.load(open(os.path.join(HERE, 'r8inputs',
                                   'd3_scan_v404.json')))['rows']
UNITS = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_units_r9.json')))
TONES = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_tones_r9.json')))
NEW = json.load(open(os.path.join(HERE, 'r11inputs', 'm3a_r11.json')))
SENS = json.load(open(os.path.join(HERE, 'sens_r11.json')))

import adopted_e90 as ae                                     # noqa: E402
import star_alias as sa                                      # noqa: E402

# =====================================================================
# 1. EACH WINDOW'S OWN INTEGRATION LENGTH: measured, or bounded and said so
# =====================================================================
# The scan is keyed on (block, spectral window); the catalogue has no
# spectral-window column, so the join key is the block together with the
# window's own published on-source time, which the scan records as `pub`.
# `old` is the catalogue's own estimator -- n_int x median(dt) -- so where
# both sources carry a window they must agree exactly, and that equality is
# the test of the join.
SCAN_IX = collections.defaultdict(list)
for _s in SCAN:
    if _s['pub'] is not None and _s['nint']:
        SCAN_IX[(_s['eb'], round(_s['pub'], 3))].append(_s)

AGREE = []
for r in CAT:
    hit = SCAN_IX.get((r['eb'], round(float(r['on_source_s']), 3)))
    if r['n_int'] not in ('', 'None'):
        r['_dt'] = float(r['on_source_s']) / float(r['n_int'])
        r['_src'] = 'release'
        if hit:
            AGREE.append(abs(hit[0]['old'] / hit[0]['nint'] / r['_dt'] - 1.0))
    elif hit:
        r['_dt'] = hit[0]['old'] / hit[0]['nint']
        r['_src'] = 'scan'
    else:
        r['_dt'] = None
        r['_src'] = 'bound'

DT_CEIL = max([s['old'] / s['nint'] for s in SCAN if s['nint']]
              + [r['_dt'] for r in CAT if r['_dt'] is not None])
if DRIVE == 3:
    DT_CEIL = 0.5

# =====================================================================
# 2. THE DRIFT THAT SETS THE QUOTED LIMIT, MEASURED FROM THE CAMPAIGN
# =====================================================================
# The campaign's tone records carry each injected carrier's own drift rate.
# Expressed as a fraction of its window's drift ceiling, the distribution is
# the one EIRP_90 was measured over; its ninetieth percentile is the drift at
# which the ninetieth-percentile power is needed, and therefore the drift
# relevant to the quoted limit.
OLD_FINE = [u for u in UNITS if u['cls'] == 'fine']
NEW_FINE = list(NEW['units'])

# ---- the injected-window join, on frequency and channel width, never a name
_TONEWIN = collections.defaultdict(set)
for t in TONES:
    # window-edge keys use min/max of the pair: a descending spectral window
    # writes them reversed
    _TONEWIN[t['tag']].add((round(min(t['fsl'], t['fsh']), 6),
                            round(t['cw'], 1)))
CAT_IX = collections.defaultdict(list)
for r in CAT:
    _lo = min(float(r['flo_GHz']), float(r['fhi_GHz']))
    CAT_IX[(r['eb'], round(_lo, 6),
            round(float(r['chanw_Hz']), 1))].append(r)

INJ = {}                       # tag -> catalogue row
_unres = []
for u in OLD_FINE:
    g = _TONEWIN.get(u['tag'], set())
    if len(g) != 1:
        _unres.append((u['tag'], 'tone window ambiguous', len(g)))
        continue
    lo, cw = next(iter(g))
    c = CAT_IX.get((u['eb'], lo, cw), [])
    if len(c) == 1:
        INJ[u['tag']] = c[0]
    else:
        _unres.append((u['tag'], 'catalogue candidates', len(c)))
for u in NEW_FINE:
    c = CAT_IX.get((u['eb'], round(u['cat_flo_GHz'], 6),
                    round(u['chanw_Hz'], 1)), [])
    if len(c) == 1:
        INJ[u['tag']] = c[0]
        # the round-11 half of the campaign carries two of the released
        # row's own values, so the join is checked and not merely made
        assert abs(float(c[0]['on_source_s']) - u['cat_on_source_s']) < 0.01
        assert abs(float(c[0]['ctrl_max_snr']) - u['cat_ctrl_max_snr']) < 0.02
    else:
        _unres.append((u['tag'], 'catalogue candidates', len(c)))

if DRIVE == 6:
    INJ[OLD_FINE[0]['tag']] = INJ[OLD_FINE[1]['tag']]

_ids = [id(v) for v in INJ.values()]
ck('Q6 every directly injected window resolves to exactly one released row, '
   'and no two injected windows resolve to the same row',
   len(INJ) == len(OLD_FINE) + len(NEW_FINE) and not _unres
   and len(set(_ids)) == len(_ids)
   and len(INJ) == SENS['n_injected'],
   '%d of %d joined, %d distinct rows, record says %d; unresolved %s'
   % (len(INJ), len(OLD_FINE) + len(NEW_FINE), len(set(_ids)),
      SENS['n_injected'], _unres))

for r in CAT:
    r['_inj'] = False
for _row in INJ.values():
    _row['_inj'] = True
if DRIVE == 7:
    [r for r in CAT if not r['_inj']][0]['_inj'] = True

# ---- the drift distribution the campaign realised
DRFRAC = []
_overs = 0
for t, src in [(t, 'old') for t in TONES] + \
              [(t, 'new') for t in NEW['tones']]:
    if t['outside']:
        continue
    row = INJ.get(t['tag'])
    if row is None:
        continue
    dm = float(row['drift_max_Hz_s'])
    f = abs(t['dr']) / dm
    if DRIVE == 2 and not DRFRAC:
        f = 1.4
    if f > 1.0 + 1e-6:
        _overs += 1
    DRFRAC.append(f)
DRFRAC.sort()
N_TONE = len(DRFRAC)
Q90 = DRFRAC[int(0.90 * N_TONE)]
QMEAN = sum(DRFRAC) / N_TONE
if DRIVE == 1:
    Q90 = 1.0

ck('Q2 no injected carrier drifted faster than its own window\'s searched '
   'ceiling, which is what makes the fraction a fraction',
   _overs == 0, '%d of %d tones above the ceiling' % (_overs, N_TONE))

# the campaign plan draws the drift uniformly over the window's own grid, for
# which the ninetieth percentile of |drift| is exactly 0.900 and the mean
# 0.500; the realised draw is required to agree, so a plan not followed is
# visible rather than absorbed
ck('Q1 the drift percentile that sets a ninety per cent point is measured '
   'from the campaign\'s own tones and agrees with the uniform draw the '
   'campaign plan specifies',
   abs(Q90 - 0.900) < 0.03 and abs(QMEAN - 0.500) < 0.03,
   'measured ninetieth percentile %.4f against 0.900, mean %.4f against '
   '0.500, over %d tones' % (Q90, QMEAN, N_TONE))

# =====================================================================
# 3. eta_smear PER WINDOW, ON THREE CONVENTIONS, THE MIDDLE ONE ADOPTED
# =====================================================================
NONE = []
for r in CAT:
    if DRIVE == 4 and r is CAT[0]:
        r['drift_max_Hz_s'] = ''
    if r['drift_max_Hz_s'] in ('', 'None') or r['chanw_Hz'] in ('', 'None'):
        r['_src'] = 'none'
        NONE.append(r)
        continue
    if r['_dt'] is None:
        r['_dt'] = DT_CEIL
    dmax = float(r['drift_max_Hz_s'])
    cw = float(r['chanw_Hz'])
    for key, q in (('ceil', 1.0), ('p90', Q90), ('mean', QMEAN)):
        r['_eta_' + key] = sinc(math.pi * q * dmax * r['_dt'] / cw / 2.0)
    r['_eta'] = r['_eta_p90']
    r['_delta'] = Q90 * dmax * r['_dt'] / cw

MEAS = [r for r in CAT if r['_src'] in ('release', 'scan')]
BOUND = [r for r in CAT if r['_src'] == 'bound']
if DRIVE == 4:
    pass                               # NONE is already occupied
N_FROM_SCAN = sum(1 for r in MEAS if r['_src'] == 'scan')
N_FROM_REL = sum(1 for r in MEAS if r['_src'] == 'release')

_dumpwin = texnum_opt('CsNDumpWin')
ck('Q4 every released window is measured or bounded with nothing in '
   'between, the three groups partition the catalogue, and the measured '
   'group contains the subset the release itself carries',
   len(MEAS) + len(BOUND) + len(NONE) == int(texnum('NWindows'))
   and not NONE and N_FROM_SCAN > 0 and N_FROM_REL > 0
   and (_dumpwin is None or N_FROM_REL == int(_dumpwin)),
   '%d measured (%d release + %d scan) + %d bounded + %d neither = %d '
   'against %s; release subset against %s'
   % (len(MEAS), N_FROM_REL, N_FROM_SCAN, len(BOUND),
      len(NONE), len(MEAS) + len(BOUND) + len(NONE), texval('NWindows'),
      ('\\CsNDumpWin %d' % _dumpwin) if _dumpwin is not None
      else 'NOT YET IN THE MACRO LAYER (clean tree): ledger_r14 round 450 '
           'asserts it'))

_worst_agree = max(AGREE) if AGREE else 1.0
ck('Q3 the bound is conclusive: the ceiling is at least the longest '
   'integration measured anywhere, the join behind the measured group is '
   'exact where both sources carry a window, and no bounded window loses '
   'one per cent',
   DT_CEIL >= max(r['_dt'] for r in MEAS) - 1e-9
   and len(AGREE) > 100 and _worst_agree < 1e-5
   and min(r['_eta'] for r in BOUND) >= 0.99,
   'ceiling %.3f s against longest measured %.3f s; %d overlapping windows '
   'agree to %.2g; worst bounded eta %.5f'
   % (DT_CEIL, max(r['_dt'] for r in MEAS), len(AGREE), _worst_agree,
      min(r['_eta'] for r in BOUND)))

# ★ A window for which the factor cannot be formed at all -- no drift ceiling
# or no channel width -- cannot be corrected and must not be quietly left
# uncorrected, so the run stops here rather than carrying it forward.
if FAIL:
    print('\nsmear_r15: %d FAILURE(S) before the correction could be formed'
          % len(FAIL))
    for f in FAIL:
        print('  - %s' % f)
    sys.exit(1)

# =====================================================================
# 4. THE ANALYTIC FACTOR, CHECKED AGAINST THE CAMPAIGN'S OWN LADDERS
# =====================================================================
# For each injected window: re-score its own recovery ladder with every tone's
# amplitude de-rated by that tone's own eta, and read the ninety per cent
# point again.  The ratio to the undrated point is a MEASURED penalty for that
# window, to be compared with the analytic 1/eta.
AMPS = SENS['amps']
TONE_BY_TAG = collections.defaultdict(list)
for t in TONES:
    if not t['outside'] and t['tag'] in INJ:
        TONE_BY_TAG[t['tag']].append(t)
for t in NEW['tones']:
    if not t['outside'] and t['tag'] in INJ:
        TONE_BY_TAG[t['tag']].append(t)


def _frac_curve(tag):
    """recovery fraction at each ladder amplitude, from the tone records"""
    out = []
    for a in AMPS:
        tt = [t for t in TONE_BY_TAG[tag] if t['amp'] == a]
        out.append(sum(bool(t['trig']) for t in tt) / len(tt) if tt else None)
    return out


def _interp(xs, ys, x):
    """the measured curve as a function of amplitude, clamped at both ends"""
    pts = [(a, f) for a, f in zip(xs, ys) if f is not None]
    if x <= pts[0][0]:
        return pts[0][1] * x / pts[0][0]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for j in range(1, len(pts)):
        if pts[j][0] >= x:
            (a0, f0), (a1, f1) = pts[j - 1], pts[j]
            return f0 + (f1 - f0) * (x - a0) / (a1 - a0)
    return pts[-1][1]


def _cross(f, lo, hi, want=0.9):
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if f(mid) < want:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


VAL = []
for tag, row in INJ.items():
    fr = _frac_curve(tag)
    pts = [(a, f) for a, f in zip(AMPS, fr) if f is not None]
    if not pts or pts[-1][1] < 0.9:
        continue
    dt, cw = row['_dt'], float(row['chanw_Hz'])
    etas = [sinc(math.pi * abs(t['dr']) * dt / cw / 2.0)
            for t in TONE_BY_TAG[tag]]
    p90_plain = _cross(lambda p: _interp(AMPS, fr, p), 0.01, 200.0)
    p90_smear = _cross(
        lambda p: sum(_interp(AMPS, fr, p * e) for e in etas) / len(etas),
        0.01, 200.0)
    VAL.append(dict(tag=tag, star=row['star_name'],
                    measured=p90_smear / p90_plain,
                    analytic=1.0 / row['_eta'],
                    eta=row['_eta'], src=row['_src']))

# ★ THE TWO ROUTES DO NOT AGREE EXACTLY, AND THE DIRECTION IS THE POINT.
# The analytic factor is taken at the ninetieth-percentile drift; the
# re-scored one convolves the whole drift distribution with that window's own
# recovery curve, which is steep, so the analytic factor is an UPPER BOUND on
# the penalty.  It is on the conservative side in all 49 windows, by at most
# eight per cent on the two most affected.  So the assertion is one-sided --
# the analytic factor may never be the smaller of the two, because that would
# make the applied correction optimistic -- together with a ceiling on how
# far it overshoots.  An equality here would be a check that can only ever
# fail on good data, which this project has shipped twice.
_dev = [v['analytic'] - v['measured'] for v in VAL]
_opt = [v for v in VAL if v['analytic'] < v['measured'] - 1e-9]
if DRIVE == 8:
    _opt = VAL[:1]
ck('Q8 the analytic per-window factor is never smaller than the penalty '
   'measured by re-scoring that window\'s own ladder with every tone '
   'de-rated by its own smearing loss, and overshoots it by at most a tenth',
   len(VAL) > 40 and not _opt and max(_dev) < 0.10,
   '%d windows re-scored, analytic larger in %d, worst overshoot %.4f, '
   'optimistic in %d' % (len(VAL), sum(1 for d in _dev if d > 0),
                         max(_dev) if _dev else -1, len(_opt)))

# =====================================================================
# 5. FOLD IT IN
# =====================================================================
PXA = json.load(open(os.path.join(HERE, 'pxapply_v411.json')))
# ★ CIRCULAR DEPENDENCY, BROKEN THE WAY sens_r11.py BROKE THE SAME ONE.  The
# Class B factor is published as \EirpNinetyMultB by round 103, and round 103
# reads the deposit column this file writes.  So the factor is taken from the
# campaign record that MEASURED it, and the macro layer is consulted only as a
# cross-check where it is already defined.
MULT_B = SENS['class_b']['p90']
if DRIVE == 13:
    MULT_B = MULT_B * 1.5
_layer_b = texnum_opt('EirpNinetyMultB')
ck('Q13 the Class B factor used here is the one the macro layer publishes, '
   'where the layer defines it at all',
   _layer_b is None or abs(_layer_b / MULT_B - 1.0) < 0.01,
   'measured %.4f against layer %s'
   % (MULT_B, '%.4f' % _layer_b if _layer_b is not None
      else 'not yet written'))

# ★ The arithmetic lives in `adopted_e90.py` and the measurement lives here:
# the eta map this file computed is handed to the one definition of the
# paper's headline sensitivity rather than copied into a second one.  That
# also removes the ordering trap -- this generator does not have to deposit
# its own record before it can use it.
ETA = {ae.smear_key(r): r['_eta'] for r in CAT}
assert len(ETA) == len(CAT), (
    'two released windows share one block-and-lower-edge key, so the '
    'smearing factor cannot be joined to the deposit by position: %d keys '
    'for %d rows' % (len(ETA), len(CAT)))
E_PLAIN = ae.per_window(CAT, HERE, mult_b=MULT_B, _smear=False)
E_CORR = ae.per_window(CAT, HERE, mult_b=MULT_B, smear=ETA)

_ratio = [E_CORR[id(r)] / E_PLAIN[id(r)] for r in CAT]
if DRIVE == 5:
    _ratio = [1.0 / x for x in _ratio]
ck('Q5 the correction only ever makes a limit worse, never better: a lost '
   'efficiency cannot deepen a limit',
   min(_ratio) >= 1.0 - 1e-12,
   'smallest ratio %.6f, largest %.4f' % (min(_ratio), max(_ratio)))


def _best_by_system(E, cls='A'):
    best = {}
    for r in CAT:
        if r['search_class'] != cls:
            continue
        v = E[id(r)]
        s = r['system_id']
        if s not in best or v < best[s][0]:
            best[s] = (v, r)
    return best


WIN_PLAIN = sorted(E_PLAIN[id(r)] for r in CAT if r['search_class'] == 'A')
WIN_CORR = sorted(E_CORR[id(r)] for r in CAT if r['search_class'] == 'A')
BP, BC = _best_by_system(E_PLAIN), _best_by_system(E_CORR)
SYS_PLAIN = sorted(v for v, _ in BP.values())
SYS_CORR = sorted(v for v, _ in BC.values())
NE_PLAIN = sum(1 for v in SYS_PLAIN if v <= 1e15)
NE_CORR = sum(1 for v in SYS_CORR if v <= 1e15)
if DRIVE == 9:
    NE_CORR = NE_PLAIN

print('\n   per-window median Class A  %s -> %s W'
      % (sci(st.median(WIN_PLAIN)), sci(st.median(WIN_CORR))))
print('   per-system median Class A  %.4e -> %.4e W  (printed %s -> %s)'
      % (st.median(SYS_PLAIN), st.median(SYS_CORR),
         sci(st.median(SYS_PLAIN)), sci(st.median(SYS_CORR))))
print('   systems reaching 1e15 W    %d -> %d' % (NE_PLAIN, NE_CORR))

_lost = [s for s in BP if BP[s][0] <= 1e15 < BC[s][0]]
LOSTSTARS = sorted(sa.designation(BP[s][1]['star_name']).replace(' ', '~')
                   for s in _lost)
print('   systems that fall out: %s' % (', '.join(LOSTSTARS) or 'none'))

# ★ The published count is compared with this one by `ledger_r14.py`'s L11,
# which runs after round 103 writes it; this clause states the thing this file
# can state on its own -- that the correction MOVES the count, and moves it the
# only way a lost efficiency can.
_pubn = texnum_opt('NSysEfifteen')
ck('Q9 the correction changes the count of systems reaching 1e15 W, and '
   'reduces it, so it is applied and not merely computed',
   NE_CORR < NE_PLAIN and (_pubn is None or int(_pubn) in (NE_CORR, NE_PLAIN)),
   'corrected %d, uncorrected %d, macro layer %s'
   % (NE_CORR, NE_PLAIN,
      '%d' % _pubn if _pubn is not None else 'not yet written'))

# =====================================================================
# 6. MEASURED COMPLETENESS AND ESTIMATED COMPLETENESS, KEPT APART
# =====================================================================
# Each system's headline limit is its best window.  That window either was
# injected into -- in which case its completeness is measured -- or it was
# not, in which case the completeness is the class average transferred to it
# and the right statement of its uncertainty is the observed dispersion
# between injected windows, not the sampling error of the pooled mean.
DISP_LO = SENS['transfer']['full_lo']
DISP_HI = SENS['transfer']['full_hi']
IND_LO = SENS['individual']['lo']
IND_HI = SENS['individual']['hi']
BOOT_PCT = 100.0 * max(SENS['p90'] / SENS['p90_boot']['lo'] - 1.0,
                       SENS['p90_boot']['hi'] / SENS['p90'] - 1.0)

N_INJ_WIN = sum(1 for r in CAT if r['_inj'])
N_A = sum(1 for r in CAT if r['search_class'] == 'A')
SYS_MEAS = sorted(s for s in BC if BC[s][1]['_inj'])
SYS_EST = sorted(s for s in BC if not BC[s][1]['_inj'])
# the injected windows that are some system's best window
print('\n   injected windows %d of %d Class A; systems whose headline '
      'window is injected %d of %d'
      % (N_INJ_WIN, N_A, len(SYS_MEAS), len(BC)))

ck('Q7 the measured set is exactly the injected set: every window the '
   'campaign record names and no other, and the systems whose headline '
   'limit is measured are a proper subset of the systems searched',
   N_INJ_WIN == SENS['n_injected'] and 0 < len(SYS_MEAS) < len(BC)
   and len(SYS_MEAS) + len(SYS_EST) == len(BC),
   '%d injected windows against the record\'s %d; %d of %d systems measured'
   % (N_INJ_WIN, SENS['n_injected'], len(SYS_MEAS), len(BC)))

# ★ WHERE THE TRANSFER DISPERSION COMES FROM, measured because it bears on
# whether the campaign's unit should have been the block or the window: over
# the blocks that hold more than one injected window, each window's own ninety
# per cent point sits within a tenth of its block's mean, against the
# x0.80-x1.58 spread about the pooled value.  So the dispersion an estimated
# limit carries is almost all BETWEEN blocks, which is what the block-level
# draw was chosen for.  Reported, not asserted: it changes no published
# number, because no system's best window shares a block with an injected one.
_bt = collections.defaultdict(list)
for _t in SENS['tags']:
    _bt[_t.rsplit('_spw', 1)[0]].append(SENS['per_window'][_t]['trig'])
_wb = []
for _k, _v in _bt.items():
    if len(_v) > 1:
        _mu = sum(_v) / len(_v)
        _wb += [x / _mu for x in _v]
_wb.sort()
WITHIN = dict(lo=_wb[0], hi=_wb[-1], n_window=len(_wb),
              n_block=sum(1 for v in _bt.values() if len(v) > 1))
print('   within-block spread of the measured factor about its own block '
      'mean: x%.2f-x%.2f over %d windows in %d blocks, against the pooled '
      'x%.2f-x%.2f'
      % (WITHIN['lo'], WITHIN['hi'], WITHIN['n_window'], WITHIN['n_block'],
         DISP_LO, DISP_HI))

# ★ the dispersion is wider than the calibration interval quoted beside it,
#   which is the referees' point and is asserted rather than asserted of
CAL_LO = SENS['budget']['factor_lo']
CAL_HI = SENS['budget']['factor_hi']
if DRIVE == 10:
    DISP_LO, DISP_HI = CAL_LO * 1.01, CAL_HI * 0.99
ck('Q10 the observed window-to-window dispersion is wider than the '
   'uncertainty on the pooled calibration, so the two may not be '
   'interchanged',
   DISP_LO < CAL_LO and DISP_HI > CAL_HI,
   'dispersion x%.3f-x%.3f against calibration x%.3f-x%.3f'
   % (DISP_LO, DISP_HI, CAL_LO, CAL_HI))

# =====================================================================
# 7. MACROS
# =====================================================================
_facA = sorted(E_CORR[id(r)] / E_PLAIN[id(r)]
               for r in CAT if r['search_class'] == 'A')
_fac_all = sorted(_ratio)
_nabove = sum(1 for x in _facA if x > 1.01)
_lowstars = []
for r in sorted((r for r in CAT if E_CORR[id(r)] / E_PLAIN[id(r)] > 1.01),
                key=lambda r: r['_eta']):
    s = sa.designation(r['star_name']).replace(' ', '~')
    if s not in _lowstars:
        _lowstars.append(s)

def thou(n):
    return '{:,}'.format(int(n)).replace(',', '\\,')


m('SmcQninePct', '%.0f' % (100.0 * Q90))
m('SmcNTone', thou(N_TONE))
# ★ window counts are printed plainly in this paper (\NWindows is 1651,
# \NWinB is 1249); trial counts carry a thin space (\ScRsNTrial, 4\,000).
m('SmcNMeas', '%d' % len(MEAS))
m('SmcNBound', '%d' % len(BOUND))
m('SmcDtCeil', '%.1f' % DT_CEIL)
m('SmcBoundEta', '%.3f' % min(r['_eta'] for r in BOUND))
m('SmcFacWorst', '%.2f' % _facA[-1])
m('SmcFacCeilWorst', '%.2f' % (1.0 / min(r['_eta_ceil'] for r in CAT)))
m('SmcNAbove', '%d' % _nabove)
# ★ The star COUNT is emitted here beside the star LIST, not borrowed from
# round 450's \SmNLowStar.  That macro counts stars on the drift-ceiling
# convention and over the measured windows only; this one counts the stars in
# the list printed next to it, on the convention actually applied.  Two
# generators' definitions standing in one sentence is how this project has
# printed "116 against 112" before.
m('SmcNAboveStar', '%d' % len(_lowstars))
m('SmcAboveStars', ', '.join(_lowstars[:-1]) + ' and ' + _lowstars[-1])
m('SmcWinLoWas', sci(WIN_PLAIN[0]))
m('SmcMedWinA', sci(st.median(WIN_CORR)))
m('SmcMedSysA', sci(st.median(SYS_CORR)))
m('SmcMedSysShiftPct', '%.1f'
  % (100.0 * (st.median(SYS_CORR) / st.median(SYS_PLAIN) - 1.0)))
m('SmcSysEfifteen', '%d' % NE_CORR)
m('SmcSysEfifteenWas', '%d' % NE_PLAIN)
m('SmcLostStars', ' and '.join(LOSTSTARS) if LOSTSTARS else 'none')
m('SmcNLost', '%d' % len(LOSTSTARS))
m('SmcValNWin', '%d' % len(VAL))
m('SmcValWorstPct', '%.0f' % (100.0 * max(_dev)))
m('SmcNInjWin', '%d' % N_INJ_WIN)
m('SmcNEstWin', '%d' % (N_A - N_INJ_WIN))
m('SmcNMeasSys', '%d' % len(SYS_MEAS))
m('SmcNEstSys', '%d' % len(SYS_EST))
m('SmcDispLo', '%.2f' % DISP_LO)
m('SmcDispHi', '%.2f' % DISP_HI)
m('SmcIndLo', '%.2f' % IND_LO)
m('SmcIndHi', '%.2f' % IND_HI)
m('SmcBootPct', '%.0f' % BOOT_PCT)

# =====================================================================
# 8. THE REGENERATED DEPOSIT
# =====================================================================
# ★★ WHAT THE DEPOSIT COULD NOT DO, AND NOW CAN.  The released catalogue's
# `eirp_p90_W` column is the TRIGGER RATIO of the twenty-one-window campaign
# applied to each window's nominal trigger power -- a well-defined quantity,
# asserted as such elsewhere in the build, but NOT the limit this paper
# quotes: it carries neither the phase-centre retention, nor the factor
# re-measured over forty-nine windows, nor the smearing loss, and it sits a
# median FACTOR OF 1.19 away from the published limit on every one of its
# rows.  Neither were the ingredients all there, so no reader could close the
# gap: the parallax retention was held per execution block in a file outside
# the deposit.  The regeneration is therefore ADDITIVE -- six new columns that
# make the published limit reproducible from the deposited file alone, and a
# closure assertion on the deposited values themselves, which is this
# project's own convention for a derived column.  Nothing existing is
# overwritten: `eta_smear` keeps its published meaning (the factor formed
# from the RELEASE's own integration count, blank where the release has none)
# because a dozen generators state honest things about exactly that column,
# and the complete factor is deposited beside it under its own name.
RENAME = {}
NEWCOLS = ['p90_mult_adopted', 'eta_px_retained', 'eta_smear_adopted',
           'eta_smear_basis', 'p90_basis',
           'eirp_p90_adopted_W', 'eirp_p90_adopted_lo_W',
           'eirp_p90_adopted_hi_W']
def deposit_rows():
    src = list(csv.DictReader(open(os.path.join(HERE, CAT_NAME))))
    assert len(src) == len(CAT)
    cols = list(csv.reader(open(os.path.join(HERE, CAT_NAME))))[0]
    # ★ IDEMPOTENT.  The generator must be able to run on its own output and
    # reproduce it byte for byte -- the build's clean-regeneration gate
    # requires exactly that -- so its OWN columns are dropped and rebuilt
    # while every column it did not write is carried through untouched.  A
    # new column whose name collides with one this file does not own is a
    # defect and stops the run rather than overwriting a published value.
    out_cols = [c for c in cols if c not in NEWCOLS] + list(NEWCOLS)
    assert len(set(out_cols)) == len(out_cols), out_cols
    rows = []
    for s, r in zip(src, CAT):
        assert s['eb'] == r['eb'] and s['flo_GHz'] == r['flo_GHz'] \
            and s['star_name'] == r['star_name']
        d = dict(s)
        e = E_CORR[id(r)]
        d['p90_mult_adopted'] = '%.10g' % (SENS['p90']
                                          if r['search_class'] == 'A'
                                          else MULT_B)
        d['eta_px_retained'] = '%.10g' % PXA['retained_fraction_by_eb'].get(
            r['eb'], 1.0)
        d['eta_smear_adopted'] = '%.10g' % r['_eta']
        d['eta_smear_basis'] = ('bounded' if r['_src'] == 'bound'
                                else 'measured')
        if DRIVE == 11:
            d['eta_smear_adopted'] = ''
        d['eirp_p90_adopted_W'] = '%.10g' % e
        # ★ THE INTERVAL BESIDE A LIMIT IS NOT THE SAME KIND OF THING FOR AN
        # INJECTED WINDOW AS FOR A TRANSFERRED ONE.  An injected window's
        # completeness was measured, so its interval is its own measurement;
        # a transferred one's was not, so its interval is the OBSERVED spread
        # between injected windows -- never the sampling error of the pooled
        # mean, which describes no window at all.
        if r['_inj']:
            lo, hi = IND_LO / SENS['p90'], IND_HI / SENS['p90']
            d['p90_basis'] = 'injected'
        else:
            lo, hi = DISP_LO, DISP_HI
            d['p90_basis'] = 'transferred'
        d['eirp_p90_adopted_lo_W'] = '%.10g' % (e * lo)
        d['eirp_p90_adopted_hi_W'] = '%.10g' % (e * hi)
        if DRIVE == 12 and not rows:
            d['star_snr'] = '0.0'
        rows.append(d)
    return out_cols, rows


OUTCOLS, DROWS = deposit_rows()
_nmeas_dep = sum(1 for d in DROWS if d['eta_smear_basis'] == 'measured')
_ninj_dep = sum(1 for d in DROWS if d['p90_basis'] == 'injected')
# ★ THE CLOSURE, ON THE DEPOSITED STRINGS AND NOT ON THE VALUES IN MEMORY.
# A reader with nothing but the file must be able to form the published limit
# from it, so the identity is checked at the printed precision of the
# deposited columns.  This is what the deposit could not do before.
# ★ The tolerance is set by the printed precision of the three factors this
# file deposits -- ten significant figures each -- and NOT by the released
# nominal power's seven, because the same deposited string appears on both
# sides of the identity and cancels.  A tolerance orders of magnitude looser
# than the achieved residual would be a check that cannot fail.
_CLOSE_TOL = 1e-8
_close = []
for d in DROWS:
    want = (float(d['eirp_nominal_W']) * float(d['p90_mult_adopted'])
            / float(d['eta_px_retained']) / float(d['eta_smear_adopted'] or 1))
    _close.append(abs(want / float(d['eirp_p90_adopted_W']) - 1.0))
ck('Q11 the deposit now closes on the published limit from its own columns: '
   'nominal trigger power times the adopted completeness factor, divided by '
   'the phase-centre retention and by the smearing retention, reproduces the '
   'deposited EIRP_90 on every row, with the basis of each per-window term '
   'named beside it',
   len(DROWS) == len(CAT) and all(d['eta_smear_adopted'] for d in DROWS)
   and _nmeas_dep == len(MEAS) and _ninj_dep == N_INJ_WIN
   and max(_close) < _CLOSE_TOL,
   '%d rows, %d measured, %d injected, %d columns, worst closure %.2g'
   % (len(DROWS), _nmeas_dep, _ninj_dep, len(OUTCOLS), max(_close)))

# and nothing existing moved: every column of the file this run read is
# reproduced unchanged, value for value
_moved = set()
for s, d in zip(list(csv.DictReader(open(os.path.join(HERE, CAT_NAME)))),
                DROWS):
    for k, v in s.items():
        if k not in NEWCOLS and d[k] != v:
            _moved.add(k)
ck('Q12 the regeneration is additive: every column the released catalogue '
   'already published is reproduced value for value, so no statement made '
   'about the deposit elsewhere in this paper can have moved under it',
   not _moved, sorted(_moved))

if DEPOSIT:
    with open(DEPOSIT_OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=OUTCOLS)
        w.writeheader()
        for d in DROWS:
            w.writerow(d)
    print('\n   deposit written: %s (%d rows, %d columns)'
          % (os.path.basename(DEPOSIT_OUT), len(DROWS), len(OUTCOLS)))

# =====================================================================
json.dump(dict(
    generated_by='smear_r15.py', round=ROUND, drive=DRIVE,
    q90=Q90, q_mean=QMEAN, n_tone=N_TONE,
    dt_ceiling_s=DT_CEIL, n_measured=len(MEAS), n_bounded=len(BOUND),
    n_from_release=N_FROM_REL, n_from_scan=N_FROM_SCAN,
    join_overlap=len(AGREE), join_worst=_worst_agree,
    eta_key='adopted_e90.smear_key: eb|lower edge|channel width|star label',
    eta=dict((ae.smear_key(r),
              dict(eta=r['_eta'], eta_ceil=r['_eta_ceil'],
                   eta_mean=r['_eta_mean'], dt=r['_dt'], basis=r['_src'],
                   injected=r['_inj']))
             for r in CAT),
    validation=VAL, val_worst=max(_dev),
    headline=dict(win_med=st.median(WIN_CORR), sys_med=st.median(SYS_CORR),
                  sys_lo=SYS_CORR[0], sys_hi=SYS_CORR[-1],
                  n_sys=len(SYS_CORR), n_sys_1e15=NE_CORR,
                  win_med_nosmear=st.median(WIN_PLAIN),
                  sys_med_nosmear=st.median(SYS_PLAIN),
                  n_sys_1e15_nosmear=NE_PLAIN),
    measured_systems=len(SYS_MEAS), estimated_systems=len(SYS_EST),
    within_block=WITHIN,
    n_injected_windows=N_INJ_WIN,
    dispersion=[DISP_LO, DISP_HI], calibration=[CAL_LO, CAL_HI],
    failures=FAIL), open(OUTJSON, 'w'), indent=1)

if FAIL:
    print('\nsmear_r15: %d FAILURE(S)' % len(FAIL))
    for f in FAIL:
        print('  - %s' % f)
    sys.exit(1)
open(OUT, 'w').writelines(LINES)
print('\nsmear_r15: %d macros -> %s' % (len(LINES) - 1, os.path.basename(OUT)))
