#!/usr/bin/env python3
r"""round 105 -> survey_numbers_round105.tex: WHAT THE SPATIAL SCREEN COSTS.

Why this exists.  The paper concedes to referee 2 that the completeness must
charge for the 512-position spatial screen, and the adopted multiplier does.
The quantitative counterpart was missing: nowhere in the manuscript did a
reader learn whether charging for the screen was a large correction or a small
one, and nowhere was the paper's own claim that *the screen measures
compactness and not authenticity* supported by a number.  Grepping the built
PDF text for the cost found nothing.

Everything here is READ from the frozen record the adopted sensitivity itself
is read from, `r9inputs/sens_r9b.json`, so the cost and the multiplier cannot
come from two different analyses -- which is the defect this tree has met
sixteen times.  Nothing is typed:

    \ScrTrigOnlyA   the trigger-only 90 per cent point, x P_trig
    \ScrCostA       the screen's cost, adopted / trigger-only
    \ScrCostNoise   the cost in a NOISE-DOMINATED window: the median over all
                    Class A windows of max(1, C/5), where C is the window's
                    own published control maximum.  In a window whose ring
                    peaks at C sigma the screen is equivalent to raising the
                    5 sigma trigger to C, so this is the cost when the ring is
                    noise and nothing else.
    \ScrNBright     Class A windows whose control ring is at or above
                    \ScrBrightSig sigma -- where the screen is set by resolved
                    emission at the control positions rather than by the noise
    \ScrBrightSig   that stratum's lower edge, read from the strata
    \ScrBrightLo    the lowest and highest control maxima among those windows
    \ScrBrightHi
    \ScrNWinA       the Class A window count those four are out of
    \ScrBrightStars the stars carrying them, formatted

Six assertions, each naming the input that would make it fail, and five
drives.  Run after numbers_v410.py: C0 there pins the same frozen p90 this
reads, so a disagreement is caught at its source rather than here.

    python3 screencost_v410.py [--drive N]

--drive 1..7 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads" (D36's rule: the
suffix follows the FLAG, not the perturbation).
"""
import csv
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

SENSB = json.load(open(os.path.join(HERE, 'r9inputs', 'sens_r9b.json')))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))

OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-62s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """Read a macro back out of the macro layer, last definition wins."""
    # ★ `(?:provide|re|new)command` does NOT match `\renewcommand`: the
    #   alternation takes `re`, and what follows is `newcommand`, not
    #   `command`.  Round 103's retirements are ALL `\renewcommand`, so a
    #   reader of the macro layer written that way sees none of the adopted
    #   values and silently falls back to whatever came before them.
    pat = re.compile(r'\\(?:provide|renew|new)command\{?\\%s\}?\{([^}]*)\}'
                     % name)
    got = None
    for f in sorted(os.listdir(HERE)):
        if not (f.startswith('survey_numbers') and f.endswith('.tex')):
            continue
        for mm in pat.finditer(open(os.path.join(HERE, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                got = mm.group(1).strip()
    return got


# ---------------------------------------------------------------- the numbers
AN = SENSB['analytic']
ST = SENSB['stratified']
TRIG_ONLY = AN['trigger_only_p90']
ADOPTED = ST['p90']
COST = ADOPTED / TRIG_ONLY
COST_NOISE = AN['screen_cost_med']
BINS = ST['bins']
BRIGHT_EDGE = BINS[-2]                      # the top stratum's lower edge
BLIND = AN['blind_windows']

cls_a = [r for r in CAT if r['search_class'] == 'A' and r.get('ctrl_max_snr')]
ctrl = [float(r['ctrl_max_snr']) for r in cls_a]
N_WIN_A = len(cls_a)
bright = sorted(x for x in ctrl if x >= BRIGHT_EDGE)
# the per-window cost when the ring is noise: raising 5 sigma to C sigma
recomputed_noise = statistics.median(max(1.0, x / 5.0) for x in ctrl)

stars = []
for b in BLIND:
    s = b['star']
    s = {'bet Pic': r'$\beta$~Pictoris'}.get(s, s.replace(' ', '~'))
    if s not in stars:
        stars.append(s)

# ------------------------------------------------------------- the assertions
print('\nscreen cost, from the same frozen record as the multiplier')
print('  trigger-only %.4f -> adopted %.4f, i.e. the screen costs x%.3f'
      % (TRIG_ONLY, ADOPTED, COST))
print('  noise-dominated cost, median max(1, C/5) over %d Class A windows: '
      'recorded %.5f, recomputed %.5f' % (N_WIN_A, COST_NOISE,
                                          recomputed_noise))
print('  control ring >= %.0f sigma: %d window(s) %s'
      % (BRIGHT_EDGE, len(bright), ['%.1f' % x for x in bright]))

print('\nassertions')
# ★ Each drive perturbs the ONE quantity its assertion tests, at the point of
#   use.  An earlier version perturbed the inputs instead, and two of the five
#   then tripped two assertions at once while a third perturbed a value that
#   had already been consumed and tripped none -- a drive that cannot perturb
#   is a check that cannot fail, which is the family this tree has met
#   sixteen times.
ck('S1 the screen cannot make a carrier easier to find',
   (COST if DRIVE != 1 else 1.0) > 1.0, 'x%.3f' % COST)
ck('S2 the noise-dominated cost is the SMALLER one -- which IS the finding: '
   'the referee\'s premise that the screen costs about two is wrong',
   COST_NOISE < (COST if DRIVE != 2 else COST_NOISE * 0.99),
   'x%.3f in noise against x%.3f overall' % (COST_NOISE, COST))
ck('S3 the recorded noise-dominated cost reproduces from the CATALOGUE\'S '
   'own ctrl_max_snr column, so a reader can rederive it',
   abs(recomputed_noise - COST_NOISE) < (5e-4 if DRIVE != 3 else -1),
   'recomputed %.5f against a recorded %.5f'
   % (recomputed_noise, COST_NOISE))
ck('S4 the bright-field windows are the top stratum, counted two ways',
   len(bright) == len(BLIND) == (AN['n_ge14'] if DRIVE != 4 else 0)
   == ST['n_cat'][-1],
   'catalogue %d, declared %d, recorded %d, stratum %d'
   % (len(bright), len(BLIND), AN['n_ge14'], ST['n_cat'][-1]))
ck('S5 the bright stratum is well above the trigger, so "resolved emission" '
   'is not a restatement of "5 sigma"',
   (BRIGHT_EDGE if DRIVE != 5 else 5.0) >= 10.0, '%.1f sigma' % BRIGHT_EDGE)
ck('S6 every bright window is named, so none is averaged away',
   len(stars if DRIVE != 6 else stars[:1]) >= 3
   and len(BLIND) >= len(stars),
   '%d star(s) over %d window(s): %s' % (len(stars), len(BLIND), stars))

# the multiplier this cost is a ratio TO must be the one the paper prints
_mult = texval('EirpNinetyMultA')
ck('S7 the adopted multiplier in the macro layer is the one this cost is '
   'computed against',
   _mult is not None and abs(float(_mult) - ADOPTED) < (0.005 if DRIVE != 7
                                                         else -1),
   'macro layer %s against frozen %.4f' % (_mult, ADOPTED))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('screencost_v410: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ------------------------------------------------------------------ the macros
m('ScrTrigOnlyA', '%.2f' % TRIG_ONLY)
m('ScrCostA', '%.2f' % COST)
m('ScrCostNoise', '%.2f' % COST_NOISE)
m('ScrNBright', '%d' % len(bright))
m('ScrNWinA', '%d' % N_WIN_A)
m('ScrBrightSig', '%.0f' % BRIGHT_EDGE)
m('ScrBrightLo', '%.1f' % bright[0])
m('ScrBrightHi', '%.1f' % bright[-1])
m('ScrBrightStars', ', '.join(stars[:-1]) + ' and ' + stars[-1]
  if len(stars) > 1 else stars[0])

path = os.path.join(HERE, 'survey_numbers_round105%s.tex' % SUF)
with open(path, 'w') as fh:
    fh.write('%% GENERATED by screencost_v410.py -- do not hand-edit.\n')
    fh.write('\n'.join(sorted(OUT)) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(path), len(OUT)))
