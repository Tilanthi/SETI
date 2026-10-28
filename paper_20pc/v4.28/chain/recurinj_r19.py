#!/usr/bin/env python3
r"""recurinj_r19.py -- the recurrence reading measured on injected carriers,
for the two crossings whose spectra survive, and the register of what cannot
be measured.

Round 750.  Writes `survey_numbers_round750.tex` and `recurinj_r19.json`.

WHY THIS EXISTS.  Every recurrence exclusion in this paper carries a recovery
probability that is CALCULATED, not measured:

    p = Phi(5 T_pers / T_star - 5),      T_pers = S / sigmabar,

with S the discovery amplitude at statistic T_star and sigmabar the
inverse-variance combination of the covering repeat blocks' noise at the
predicted cell.  That expression contains both noise levels and the
combination over blocks, and it contains nothing else: not the error in the
fitted drift, not the sub-channel position of the predicted cell, and not any
maximum over drift trials.  The reading it describes can be driven with real
noise and synthetic carriers, and this generator does that wherever the
products to do it with still exist.

WHAT EXISTS.  The extracted per-window products of this survey are gone.  Two
remain, `r11inputs/events/figdata_A01.npz` and `figdata_U02.npz`, retained for
the event figure: for the two crossings that lead their own control fields
they hold the discovery block's per-integration baselined spectrum, its
per-integration noise and its de-drift shifts, and every covering repeat
block's de-drifted amplitude and noise per channel about the predicted cell.
Those two crossings are the pair whose recovery probabilities the paper quotes
individually, so the measurement lands exactly where the numbers are printed.
For the other crossings carrying an exclusion there is nothing to inject into,
and that count is published here rather than left to be inferred.

THE CAMPAIGN.  A carrier at the trigger amplitude 5S/T_star -- the faintest
one that could have produced the crossing at all -- is injected at the
predicted cell of every covering repeat block through the instrument's own
channel response, the readings are combined inverse-variance exactly as the
exclusion combines them, and the fraction reaching the trigger is counted over
NREAL realisations.  Three modes:

  centred  the carrier in the middle of the predicted channel, which is the
           model's own assumption: this must reproduce Phi, and if it does
           not then the harness is wrong rather than the model;
  phase    the sub-channel position of the discovery and of the prediction
           drawn independently, which is what a frame transform that moves
           the cell by up to a hundred channels delivers;
  noise    the same reading with no carrier at all, which must confirm
           nothing.

The noise of each realisation is the real reading of another channel of the
same block, taken in units of that channel's own noise so that the weights
stay the ones the published exclusion uses.  A handful of band-edge cells of
the deepest block are built from fewer integrations and carry five times its
noise; drawing their weight as well would measure the edges of the retained
band and not the test.

AND THE DE-DRIFT, which no model term covers.  In the one block per crossing
whose per-integration spectrum survives, a carrier is laid down integration by
integration at its own drift and read back at the drift carried from the fit,
with the error in that drift drawn from half a step of the window's own grid.
The grid steps by half a channel across the dwell by construction, so this
should cost almost nothing inside one block -- and the measurement says how
much almost nothing is.

The channel response is the one the paper already measured for its sensitivity
budget: a tone at fractional offset f puts 1-f of its power in its channel and
f in the next, and the online Hanning smoothing convolves the channel axis
with (1/4,1/2,1/4).  Its prediction is checked against the retained response
trials here before it is used for anything.

Usage: recurinj_r19.py [--drive N]
"""
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 750
NREAL = 1000
SEED = 20261014
TRIG = 5.0
FW_TARGET = 0.01          # declared only for the register below, not used here
HAN = np.array([0.25, 0.5, 0.25])
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round750%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'recurinj_r19%s.json' % SFX)
EV = os.path.join(HERE, 'r11inputs', 'events')

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-60s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    import glob
    import re
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


def phi_n(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


# ---------------------------------------------------------------- response
def chan_profile(f):
    raw = np.zeros(5)
    raw[2] = 1.0 - f
    raw[3] = f
    return np.convolve(raw, HAN, mode='same')


def resp(f):
    """The fraction of a channel-centred carrier's peak amplitude recovered by
    reading the nearest channel, at fractional offset f."""
    if DRIVE == 1:                   # J1: a response curve that is not the one
        return 1.0 - 1.5 * f         #     the trials measure
    return chan_profile(f).max() / chan_profile(0.0).max()


TR = list(csv.DictReader(open(os.path.join(
    HERE, 'hanning_response_trials_v3.58.csv'))))
BYPHI = {}
for _r in TR:
    BYPHI.setdefault(float(_r['phi']), []).append(float(_r['peak_smoothed']))
_ref = float(np.median(BYPHI[0.0]))
_dev = max(abs(float(np.median(v)) / _ref - resp(p)) for p, v in BYPHI.items())
ck('J1 the channel response used here is the one the %d retained response '
   'trials measure' % len(TR), _dev < 0.02,
   'largest deviation %.4f over fractional offsets %s'
   % (_dev, ', '.join('%.3f' % p for p in sorted(BYPHI))))

# ---------------------------------------------------------------- inputs
REC = json.load(open(os.path.join(HERE, 'r10inputs',
                                  'recur_v411.json')))['crossings']
META = json.load(open(os.path.join(EV, 'figdata_meta.json')))
LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
WINOF = {}
for _r in CAT:
    WINOF.setdefault(_r['eb'], []).append(_r)
LFS = {(r['eb'], round(float(r['freq']), 6)): r for r in LED}


def grid_step(eb, f, dwell, chanw):
    for r in WINOF.get(eb, []):
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if lo <= f <= hi and r['n_drift_trials']:
            return (2.0 * float(r['drift_max_Hz_s'])
                    / (int(r['n_drift_trials']) - 1))
    return chanw / (2.0 * dwell)


def blocks(c):
    return [b for b in (c.get('blocks') or [])
            if not b.get('bad_weight_product')]


# The pair is READ from the ledger's own rank flag and ordered by discovery
# statistic -- the order rounds 550 and 700 use for the same two crossings --
# so a measurement can never be attached to the wrong event.
PAIR = []
for cid in sorted(META):
    c = REC[cid]
    lr = LFS[(c['eb'], round(float(c['freq_GHz']), 6))]
    PAIR.append((float(c['tstar']), cid, bool(lr['screen']),
                 float(lr['frame']['f_stellar'])))
PAIR.sort(key=lambda x: -x[0])
if DRIVE == 2:                       # J2: the pair taken in the other order
    PAIR = PAIR[::-1]
ck('J2 the crossings measured are the ledger\'s own rank-leading pair, in the '
   'order the rest of the paper prints them',
   len(PAIR) == 2 and all(p[2] for p in PAIR)
   and ['%.4f' % p[3] for p in PAIR] == [macro('RqFreqSx'),
                                         macro('RqFreqCp')],
   '%s at %s against %s'
   % ([p[1] for p in PAIR], ['%.4f' % p[3] for p in PAIR],
      [macro('RqFreqSx'), macro('RqFreqCp')]))

RES = {}
for tag, (_ts, cid, _scr, _fs) in zip(('Sx', 'Cp'), PAIR):
    c = REC[cid]
    z = np.load(os.path.join(EV, 'figdata_%s.npz' % cid))
    half = int(z['half'])
    chanw = float(z['chanw'])
    bl = blocks(c)
    mrep = META[cid]['repeats']
    if DRIVE == 6:                   # J3: a retained row quietly dropped
        mrep = mrep[:-1]
    ck('J3 %s: the retained repeat rows are the frozen record\'s own blocks, '
       'keyed on the execution block' % cid,
       [r['eb'] for r in mrep] == [b['eb'] for b in bl]
       and len(bl) == int(macro('RqNRep%s' % tag)),
       '%d retained, %d in the record, %s published'
       % (len(mrep), len(bl), macro('RqNRep%s' % tag)))

    S = float(c['discovery']['amp_mJy'])
    tstar = float(c['discovery']['T_matched'])
    if DRIVE == 7:                   # J4: a model that is not the published one
        tstar *= 1.1
    scell = [float(b['sig_mJy']) for b in bl]
    sbar = 1.0 / math.sqrt(sum(1.0 / s ** 2 for s in scell))
    tpers = S / sbar
    tpers_trig = tpers * TRIG / tstar
    model = phi_n(tpers_trig - TRIG)
    A_trig = S * TRIG / tstar
    ck('J4 %s: the modelled recovery probability reproduced here is the one '
       'the paper prints for this crossing' % cid,
       '%.2f' % model == macro('RqPowerTrig%s' % tag),
       'computed %.4f against published %s'
       % (model, macro('RqPowerTrig%s' % tag)))

    ramp = np.asarray(z['r_amp'], dtype=float)
    rsig = np.asarray(z['r_sig'], dtype=float)
    ok = np.ones(ramp.shape[1], dtype=bool)
    for i in range(ramp.shape[0]):
        ok &= np.isfinite(ramp[i]) & np.isfinite(rsig[i]) & (rsig[i] > 0)
    ok[max(0, half - 2):half + 3] = False
    cells = np.flatnonzero(ok)
    rng = np.random.default_rng(SEED + sum(ord(x) for x in cid))

    def campaign(mode):
        hit, tv = 0, []
        for _ in range(NREAL):
            cs = rng.choice(cells, size=ramp.shape[0], replace=True)
            if mode == 'centred':
                fd, fr = 0.0, np.zeros(ramp.shape[0])
            else:
                fd = rng.uniform(0.0, 0.5)
                fr = rng.uniform(0.0, 0.5, size=ramp.shape[0])
            s = np.array(scell)
            a = np.array([ramp[i, cs[i]] / rsig[i, cs[i]] * s[i]
                          for i in range(ramp.shape[0])])
            if mode != 'noise':
                a = a + A_trig * np.array([resp(x) for x in fr]) / resp(fd)
            if mode == 'noise' and DRIVE == 5:   # J6: a carrier left in the
                a = a + A_trig                   #     carrier-free run
            iv = 1.0 / s ** 2
            sb = 1.0 / math.sqrt(iv.sum())
            t = float((a * iv).sum() / iv.sum()) / sb
            tv.append(t)
            hit += int(t >= TRIG)
        return hit / float(NREAL), np.array(tv)

    out = dict(cid=cid, tag=tag, star=META[cid]['display'], f_stellar=_fs,
               n_rep=len(bl), T_star=tstar, T_pers=tpers,
               tpers_trig=tpers_trig, model=model, A_trig_mJy=A_trig,
               sbar_mJy=sbar, n_real=NREAL, n_cells=int(len(cells)))
    # the local null of the band the noise is drawn from, which the model
    # has no entry for either: measured here and reported, because it is the
    # reason the centred mode can sit a little above Phi
    _iv = 1.0 / np.array(scell) ** 2
    _tb = np.array([float((ramp[:, cc] / rsig[:, cc] * np.array(scell)
                           * _iv).sum() / _iv.sum())
                    / (1.0 / math.sqrt(_iv.sum())) for cc in cells])
    out['null_mean'] = float(_tb.mean())
    out['null_sd'] = float(_tb.std(ddof=1))
    for mode in ('centred', 'phase', 'noise'):
        p, tv = campaign(mode)
        if mode == 'phase' and DRIVE == 4:   # J5: a measurement that misses
            p = min(1.0, p + 0.25)
        out['p_' + mode] = p
        out['e_' + mode] = math.sqrt(max(p * (1.0 - p), 1e-12) / NREAL)
        out['tmed_' + mode] = float(np.median(tv))

    # ------------------------------------------------- the de-drift itself
    dyn = np.asarray(z['dyn'], dtype=float)
    sig_t = np.asarray(z['sig_t'], dtype=float)
    dt = np.asarray(z['dt'], dtype=float)
    d_fit = float(META[cid]['drift'])
    sign = 1.0 if float(z['freqs'][-1]) >= float(z['freqs'][0]) else -1.0
    dwell = float(dt.max() - dt.min())
    step = grid_step(c['eb'], float(c['freq_GHz']), dwell, chanw)
    if DRIVE == 3:                   # J7: a grid a hundred times coarser
        step *= 100.0
    good = np.isfinite(sig_t) & (sig_t > 0) & np.isfinite(dyn).all(axis=1)
    iv_t = np.where(good, 1.0 / np.where(sig_t > 0, sig_t, 1.0) ** 2, 0.0)

    def read(cube, k, drift):
        sh = np.rint(sign * drift * dt / chanw).astype(int)
        num = den = 0.0
        for t in range(cube.shape[0]):
            j = k + int(sh[t]) + half
            if good[t] and 0 <= j < cube.shape[1]:
                num += cube[t, j] * iv_t[t]
                den += iv_t[t]
        return None if den <= 0 else (num / den) * math.sqrt(den)

    def lay(k, drift, f0):
        o = np.zeros_like(dyn)
        for t in range(dyn.shape[0]):
            x = k + sign * drift * dt[t] / chanw + f0
            j0 = int(math.floor(x))
            prof = chan_profile(x - j0) / chan_profile(0.0).max()
            for q in range(-2, 3):
                j = j0 + q + half
                if 0 <= j < dyn.shape[1]:
                    o[t, j] += prof[2 + q]
        return o

    amp = TRIG / read(lay(0, d_fit, 0.0), 0, d_fit)
    rng2 = np.random.default_rng(SEED + 7)
    kmax = half - 1 - int(abs(np.rint(sign * d_fit * dt / chanw)).max())
    ks = [k for k in range(-kmax, kmax + 1) if abs(k) > 2]
    tv0, tv1 = [], []
    for _ in range(NREAL):
        k = int(rng2.choice(ks))
        f0 = rng2.uniform(0.0, 1.0)
        tv0.append(read(dyn + amp * lay(k, d_fit, f0), k, d_fit))
        dd = rng2.uniform(-0.5 * step, 0.5 * step)
        tv1.append(read(dyn + amp * lay(k, d_fit + dd, f0), k, d_fit))
    t0 = float(np.median([x for x in tv0 if x is not None]))
    t1 = float(np.median([x for x in tv1 if x is not None]))
    out.update(step_Hz_s=step, dwell_s=dwell, d_true_med=t0, d_err_med=t1,
               d_ratio=t1 / t0)
    RES[tag] = out

    print('\n%s %s  %d repeat blocks  T*=%.3f  T_pers=%.3f  trigger-amplitude '
          'T=%.3f' % (cid, out['star'], len(bl), tstar, tpers, tpers_trig))
    print('   modelled                %.3f' % model)
    print('   carrier centred         %.3f +- %.3f' % (out['p_centred'],
                                                       out['e_centred']))
    print('   sub-channel phase       %.3f +- %.3f' % (out['p_phase'],
                                                       out['e_phase']))
    print('   no carrier              %.4f' % out['p_noise'])
    print('   the band\'s own null     %+.3f +- %.3f over %d cells'
          % (out['null_mean'], out['null_sd'], len(cells)))
    print('   de-drift: half a step of %.1f Hz/s over a %.0f s dwell takes '
          'T %.2f to %.2f (%.3f)' % (step, dwell, t0, t1, t1 / t0))

# ---------------------------------------------------------------- verdicts
DEV = max(abs(r['p_' + k] - r['model']) / max(r['e_' + k], 1.0 / NREAL)
          for r in RES.values() for k in ('centred', 'phase'))
ck('J5 the measured recovery agrees with the model it tests, for both '
   'crossings and with the carrier centred or at a random sub-channel '
   'position', DEV < 3.5,
   'largest departure %.2f binomial errors; %s'
   % (DEV, '; '.join('%s %.3f+-%.3f and %.3f+-%.3f against %.3f'
                     % (r['star'], r['p_centred'], r['e_centred'],
                        r['p_phase'], r['e_phase'], r['model'])
                     for r in RES.values())))
NFALSE = sum(int(round(r['p_noise'] * NREAL)) for r in RES.values())
ck('J6 the same reading confirms nothing when the carrier is removed',
   NFALSE == 0,
   '%d of %d carrier-free readings reach the trigger'
   % (NFALSE, 2 * NREAL))
RATIO = min(r['d_ratio'] for r in RES.values())
ck('J7 half a step of error in the carried drift costs little inside one '
   'block, which is what a grid stepping by half a channel across the dwell '
   'is for', RATIO > 0.97,
   'the statistic keeps %.3f of its value at worst, over grids of %s Hz/s'
   % (RATIO, ', '.join('%.1f' % r['step_Hz_s'] for r in RES.values())))
# ★ THE REGISTER OF WHAT CANNOT BE MEASURED, and it must be able to fail: the
# retained products are listed from the directory, never remembered, so that a
# product restored to the tree enlarges the campaign instead of being silently
# left out of it.
HAVE = sorted(f[8:-4] for f in os.listdir(EV)
              if f.startswith('figdata_') and f.endswith('.npz'))
if DRIVE == 8:                       # J8: a product nobody measured
    HAVE = HAVE + ['Z99']
LUN = {(r['eb'], round(float(r['freq']), 6)) for r in LED
       if not r['attributed'] and not r.get('dq')}
NOINJ = int(macro('RcNExcl')) - len(RES)
ck('J8 every retained per-integration product is measured here, and the '
   'crossings with nothing to inject into are the rest of those carrying an '
   'exclusion',
   HAVE == sorted(r['cid'] for r in RES.values())
   and all((REC[r['cid']]['eb'],
            round(float(REC[r['cid']]['freq_GHz']), 6)) in LUN
           for r in RES.values())
   and NOINJ > 0,
   'retained %s; measured %s; %d of %s carry an exclusion with nothing to '
   'inject into' % (HAVE, sorted(r['cid'] for r in RES.values()), NOINJ,
                    macro('RcNExcl')))

m('RjNMeas', '%d' % len(RES))
m('RjNReal', '%d' % NREAL)
m('RjNoInject', '%d' % NOINJ)
m('RjNFalse', '%d' % NFALSE)
m('RjDevSig', '%.1f' % DEV)
m('RjDriftKeep', '%.3f' % RATIO)
m('RjDriftPct', '%.1f' % (100.0 * (1.0 - RATIO)))
for tag, r in RES.items():
    m('RjMeas' + tag, '%.2f' % r['p_phase'])
    m('RjErr' + tag, '%.2f' % max(r['e_phase'], 0.005))
    m('RjCentred' + tag, '%.2f' % r['p_centred'])

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by recurinj_r19.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
json.dump(dict(rows=RES, n_real=NREAL, seed=SEED, dev_sigma=DEV,
               n_false=NFALSE, n_no_inject=NOINJ, drive=DRIVE),
          open(OUTJ, 'w'), indent=1, default=str)
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
if FAIL:
    print('FAILED: %s' % '; '.join(FAIL))
else:
    print('all checks pass')
# ★★★★ v4.26, Ruling 7.  THIS SUITE USED TO COLLECT ITS FAILURES AND THEN
# EXIT 0, AND `make_all.sh` RAN IT WITH STDOUT TO /dev/null.  Three suites in
# this build were written that way -- `num_r22.py`, `r1_r22.py` and
# `recurinj_r19.py` -- so three sets of checks written to answer referee items
# could not fail the build, and one of them (num_r22's B5) had been failing on
# the shipped paper for two versions with a wrong digit on the page.  A gate
# that cannot fail is not a gate; it is a comment that takes CPU.
if FAIL:
    raise SystemExit(1)

