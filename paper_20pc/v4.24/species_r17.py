#!/usr/bin/env python3
r"""species_r17.py -- is the line mask's species list set by the original
observers' science goals, and how near a catalogued line does a crossing sit?
Both measured, neither asserted.  Round 790.

Writes `survey_numbers_round790.tex`.

WHY THIS EXISTS.  Appendix~\ref{app:linemask} carried two sentences that
nothing in the build measured.  The first says the mask holds every transition
of "the \FrNSpec{} species these spectral setups cover"; the second, closing
the appendix, says that "at these frequencies almost anything lies within
+-\MaskHalfKms km/s of something in such a list".  Neither is a bookkeeping
detail.  If the spectral setups are tuned to these twelve species then the
mask is defined by OTHER PEOPLE'S science goals, which is a real limitation of
an archival search and says where the mask is blind; and if almost every
crossing sits near some catalogued transition of some carrier, that is the
reason the mask's output is a label and not a verdict.

MEASUREMENT 1, THE TUNING, and it is two questions rather than one.
  (1) does a Class A window CONTAIN at least one masked transition?
  (2) is the window CENTRE within \MaskHalfKms km/s of one?
(1) is weak by construction: the median Class A window is ~1.7 GHz wide, which
is ~2150 km/s at 240 GHz, so a window can contain a transition by accident.
(2) is the discriminating test, because a window placed BECAUSE of a line is
centred on it.
  WHY IT CANNOT PASS VACUOUSLY.  Both questions are asked again of the same
windows displaced bodily in frequency by +1, -2, +3 and +7 GHz.  A displaced
window has the same width, the same count and the same band and differs only
in not having been tuned by anybody.  If the observed and displaced numbers
agreed, the windows would not be tuned to these species and the appendix's
sentence would be wrong.  S3 is that comparison and it is driven to fail.

MEASUREMENT 2, THE DENSITY OF THE FULL CATALOGUE at the crossings.  The
stellar-frame frequency of every crossing, from `maskframe_v411.json`, against
the whole cross-check line list `mask_xcheck_lines.json` -- \MaskDbTrans
transitions of \MaskDbCarriers carriers, the same record round 20 uses for the
counterfactual mask, so the appendix's two statements about that list rest on
one record and not on two.

The tuning measurement is `r17-refs`' (`referee_r17/refs/species_tuning.py`);
this is the same computation wired into the build, reading the same two inputs
the mask and the catalogue are built from, so the numbers the appendix prints
cannot drift from the catalogue they describe.

CHECKS (rule 9: each is driven to fail on its own)

    S1  the transition list read here IS the published mask: the number of
        transitions equals \FrNTrans.  Drive 1 drops one transition.
    S2  the window population read here IS the published Class A census: the
        number of fine-resolution windows equals \NWinA.  Drive 2 drops one
        window.
    S3  the tuning test is not vacuous: the observed fraction of windows
        centred within \MaskHalfKms km/s of a masked transition exceeds the
        largest control fraction by at least a factor of two.  Drive 3
        replaces the displacements with zero, which makes every control the
        observed case.
    S4  the containment question is the weaker of the two and is published as
        such: the observed-to-worst-control ratio for "contains a transition"
        is smaller than the ratio for "centred on one".  Drive 4 gives the
        CONTROLS zero bandwidth, which is a control differing from the
        observed windows in width as well as in placement: containment then
        looks like the discriminating test, and S4 refuses it.
    ★ Drive 3 fires S3 AND S4, and that is stated rather than hidden: a zero
      displacement makes every control the observed case, so both ratios
      become exactly one and S4's strict inequality fails with S3.
    S5  the cross-check list read here IS the published one: its length
        equals \MaskDbTrans.  Drive 5 drops one line.
    S6  the crossings read here ARE the published census: their number equals
        \NCross.  Drive 6 drops one crossing.

Usage: species_r17.py [--drive N], N in 1..6.  A driven run writes
`survey_numbers_round790_driveN.tex` and never the production path: the
suffix follows the FLAG, not the perturbation.
"""
import bisect
import csv
import glob
import json
import os
import re
import sys

C_KMS = 299792.458
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round790.tex')
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
SHIFTS = (1.0, -2.0, 3.0, 7.0)

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    M.append((k, v))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-62s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """One published value, read out of the macro layer.  Never a copy."""
    pat = re.compile(r'\\(?:new|renew)command\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.search(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


def ival(name):
    """A published integer, with the thousands separator the macro carries."""
    return int(macro(name).replace('\\,', '').replace(',', ''))


# ------------------------------------------------------------------ inputs
# The attribution tolerance is the appendix's own, read from the macro layer:
# this file must not acquire a second half-width of its own.
CEN_KMS = float(macro('MaskHalfKms'))
TRANS = json.load(open(os.path.join(HERE, 'maskcat_v412.json')))['transitions']
LINES = sorted(v['f'] for v in TRANS.values())
ROWS = [r for r in csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv')))
    if r['resolution_class'] == 'fine']
XDB = json.load(open(os.path.join(HERE, 'mask_xcheck_lines.json')))['lines']
XF = sorted(x['f'] for x in XDB)
CROSS = json.load(open(os.path.join(HERE, 'maskframe_v411.json')))['rows']
assert LINES and ROWS and XF and CROSS, 'read nothing: the inputs moved'
if DRIVE == 1:
    LINES = LINES[1:]
if DRIVE == 2:
    ROWS = ROWS[1:]
if DRIVE == 5:
    XF = XF[1:]
if DRIVE == 6:
    CROSS = CROSS[1:]


def nearest(fl, f):
    """Velocity to the nearest entry of a sorted frequency list, km/s."""
    i = bisect.bisect_left(fl, f)
    cand = [fl[j] for j in (i - 1, i) if 0 <= j < len(fl)]
    return min(abs(f - c) for c in cand) / f * C_KMS


def measure(shift, width=True):
    """(contains a transition, centred within CEN_KMS) over the windows,
    displaced bodily by `shift` GHz.  `width=False` asks the containment
    question of a window of zero bandwidth, which is drive 4's mis-specified
    control: a control may differ from the observed windows in placement and
    in nothing else."""
    inside, near, dvs = 0, 0, []
    for r in ROWS:
        lo, hi = sorted((float(r['flo_GHz']) + shift,
                         float(r['fhi_GHz']) + shift))
        fc = 0.5 * (lo + hi)
        if not width:
            lo = hi = fc
        dv = nearest(LINES, fc)
        dvs.append(dv)
        inside += 1 if any(lo <= x <= hi for x in LINES) else 0
        near += 1 if dv < CEN_KMS else 0
    n = len(ROWS)
    dvs.sort()
    return dict(n=n, inside=inside, near=near,
                f_in=inside / n, f_near=near / n, med=dvs[n // 2])


OBS = measure(0.0)
CTRL = [measure(s) for s in (SHIFTS if DRIVE != 3 else (0.0,) * len(SHIFTS))]
W = sorted(abs(float(r['fhi_GHz']) - float(r['flo_GHz'])) for r in ROWS)
# every crossing's distance to the nearest transition of any carrier
XDV = sorted(nearest(XF, c['f_stellar']) for c in CROSS)

# --------------------------------------------------------------- the macros
m('TnWinPct', '%.0f' % round(100 * OBS['f_in']))
m('TnCenPct', '%.0f' % round(100 * OBS['f_near']))
m('TnCtrlCenLo', '%.0f' % round(100 * min(c['f_near'] for c in CTRL)))
m('TnCtrlCenHi', '%.0f' % round(100 * max(c['f_near'] for c in CTRL)))
m('TnShiftLoGHz', '%.0f' % min(abs(s) for s in SHIFTS))
m('TnShiftHiGHz', '%.0f' % max(abs(s) for s in SHIFTS))
m('TnNNearDb', '%d' % sum(1 for v in XDV if v < CEN_KMS))
m('TnMedDbKms', '%.1f' % XDV[len(XDV) // 2])

# --------------------------------------------------------------- the checks
print('species_r17: %d transitions, %d Class A windows, median width '
      '%.3f GHz; %d cross-check lines, %d crossings'
      % (len(LINES), len(ROWS), W[len(W) // 2], len(XF), len(CROSS)))
print('  as observed      contains %3d/%d = %4.1f%%   centred within '
      '%.0f km/s %4.1f%%   median %7.1f km/s'
      % (OBS['inside'], OBS['n'], 100 * OBS['f_in'], CEN_KMS,
         100 * OBS['f_near'], OBS['med']))
for s, c in zip((SHIFTS if DRIVE != 3 else (0.0,) * len(SHIFTS)), CTRL):
    print('  control %+5.0f GHz contains %3d/%d = %4.1f%%   centred within '
          '%.0f km/s %4.1f%%   median %7.1f km/s'
          % (s, c['inside'], c['n'], 100 * c['f_in'], CEN_KMS,
             100 * c['f_near'], c['med']))
print('  crossings within %.0f km/s of any catalogued transition: %d of %d, '
      'median %.1f km/s, largest %.1f'
      % (CEN_KMS, sum(1 for v in XDV if v < CEN_KMS), len(XDV),
         XDV[len(XDV) // 2], XDV[-1]))

ck('S1 the transition list read here is the published mask',
   len(LINES) == ival('FrNTrans'),
   '%d against \\FrNTrans %s' % (len(LINES), macro('FrNTrans')))
ck('S2 the windows read here are the published Class A census',
   len(ROWS) == ival('NWinA'),
   '%d against \\NWinA %s' % (len(ROWS), macro('NWinA')))
_wn = max(c['f_near'] for c in CTRL)
ck('S3 the centring test is not vacuous: the observed fraction beats '
   'every control twofold',
   OBS['f_near'] >= 2.0 * _wn,
   'observed %.3f against a worst control %.3f, ratio %.1f'
   % (OBS['f_near'], _wn, OBS['f_near'] / _wn if _wn else float('inf')))
_ctrl4 = (CTRL if DRIVE != 4
          else [measure(s, width=False) for s in SHIFTS])


def _ratio(obs, ctrl, key):
    """Observed over the worst control, and a control that cannot happen at
    all gives an infinite ratio rather than an exception."""
    w = max(c[key] for c in ctrl)
    return obs[key] / w if w else float('inf')


_r_in = _ratio(OBS, _ctrl4, 'f_in')
_r_near = _ratio(OBS, _ctrl4, 'f_near')
ck('S4 containment is the weaker question and is published as the weaker '
   'one', _r_in < _r_near,
   'containment ratio %.2f against centring ratio %.2f' % (_r_in, _r_near))
ck('S5 the cross-check line list read here is the published one',
   len(XF) == ival('MaskDbTrans'),
   '%d against \\MaskDbTrans %s' % (len(XF), macro('MaskDbTrans')))
ck('S6 the crossings read here are the published census',
   len(CROSS) == ival('NCross'),
   '%d against \\NCross %s' % (len(CROSS), macro('NCross')))

# --------------------------------------------------------------------- emit
with open(os.path.join(HERE, 'survey_numbers_round790%s.tex' % SFX), 'w') as f:
    f.write('%% GENERATED by species_r17.py -- do not hand-edit.\n')
    for k, v in M:
        f.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('%d macros, %d assertion(s) failed %s' % (len(M), len(FAIL), FAIL))
if FAIL and DRIVE == 0:
    raise SystemExit('assertions failed: %s' % FAIL)
