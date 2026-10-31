#!/usr/bin/env python3
r"""Round 985: the two unattributed crossings of beta Pictoris against the
methanol 5_K->4_K ladder, decided by measurement and printed.

WHY THIS FILE EXISTS

    Both crossings lie inside the dense CH3OH 5_K->4_K complex, each about
    7 MHz above a component, and the two velocity offsets agree with each
    other -- which is the configuration a real line identification produces.
    `r21_lines.py` has measured the two offsets since round 951 and emitted
    them as macros, but no section referenced any of them, so the nearest
    strong transition the paper printed for this pair was the nearest MASKED
    one, 3,765 to 3,870 km/s away, which reads as though the pair were far
    from any line.  It is not.  This file prints the coincidence and the
    four measurements that decide it, so that a reader meets both.

    THE DECISION IS NOT AN ARGUMENT ABOUT PLAUSIBILITY.  It rests on the one
    window that holds both crossings and covers the whole ladder in both
    blocks:

      (1)  the brightest member of the complex, 5_0->4_0 A+, is predicted
           above the trigger AND above the window maximum at every
           excitation temperature -- so it would have been the window
           maximum, and the window maximum is the crossing itself;
      (2)  the weaker of the two claimed members cannot reach the strength
           it is observed with, at any excitation temperature, relative to
           the stronger;
      (3)  each crossing is a drifting track, tens of grid steps from the
           zero drift a transition at rest in the stellar frame requires,
           and it sweeps more channels inside its own block than the
           coincidence is wide;
      (4)  neither recurs in the block that covers the same frequency one
           day later, where a persistent line would be recovered.

    The ratio bounds are optically thin LTE with the partition function
    cancelling, and they are quoted as bounds over temperature rather than
    at a chosen temperature, so no excitation model is adopted.  They are
    also conservative in optical depth: as lines saturate every ratio tends
    to unity, so (1) only strengthens.

SOURCE
    `r25inputs/ch3oh_5k4k.json` -- every entry of the JPL and CDMS
    laboratory catalogues between 241.6 and 242.0 GHz, no filter, with the
    URL and md5 of each catalogue file and the date it was read.  The two
    catalogues agree on both component frequencies to 0.1 kHz; the mask of
    this paper is unchanged and holds no methanol.

ASSERTIONS (each driven to fail on its own, --drive 1..7; C1 twice, on its
membership clause and on its one-window clause)

  C1  the pair is DERIVED: it is the unattributed crossings of the star in
      the ledger, both in one window, and that window covers the ladder in
      both blocks of the pair.
  C2  the two catalogues agree on the nearest component of each crossing,
      so the identification is not an artefact of one catalogue.
  C3  the brightest member of the ladder is predicted above both the trigger
      and the published window maximum at every temperature of the scan, and
      the published window maximum is the crossing itself.
  C4  the observed ratio of the two claimed members exceeds the LTE ceiling
      on that ratio over the same scan.
  C5  the fitted drifts are many grid steps from zero and the in-block
      excursion exceeds the coincidence width.
  C6  the printed chance probability is computed, not asserted, and the
      agreement of the two offsets is the quantity it is the probability of.

Usage: ch3oh_r25.py [--paper DIR] [--out DIR] [--drive N]  (drives 1..8)
-> survey_numbers_round985.tex, ch3oh_r25.json
"""
import argparse
import csv
import json
import math
import os
import random
import re
import sys

CKMS = 299792.458
HK_K_PER_GHZ = 4.799243e-2
TSCAN = (3, 2000)                 # the temperature scan the bounds are over
STAR = 'bet Pic'
MACROS, FAIL, D = [], [], {}


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-62s %s  %s' % (label[:62], 'PASS' if ok else 'FAIL', detail))


def texval(paper, name):
    pat = re.compile(r'newcommand\{\\%s\}\{(.*?)\}\s*$' % name)
    for fn in sorted(([_e for _e in os.listdir(paper) if _e != 'numbers'] + [os.path.join('numbers', _e) for _e in (os.listdir(os.path.join(paper, 'numbers')) if os.path.isdir(os.path.join(paper, 'numbers')) else [])]), key=os.path.basename):
        if not fn.endswith('.tex'):
            continue
        for ln in open(os.path.join(paper, fn), encoding='utf-8'):
            if '\\%s}' % name in ln:
                g = pat.search(ln.strip())
                if g:
                    return g.group(1)
    raise KeyError(name)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--paper', default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument('--out', default=None)
    ap.add_argument('--drive', type=int, default=0)
    a = ap.parse_args(argv)
    paper = a.paper
    out = a.out or paper
    suf = '_drive%d' % a.drive if a.drive else ''
    drive = a.drive

    CAT = json.load(open(os.path.join(paper, 'r25inputs', 'ch3oh_5k4k.json')))
    LED = json.load(open(os.path.join(paper, 'ledger.json')))['rows']
    RCOL = json.load(open(os.path.join(paper, 'recurcols_v411.json')))
    TRAJ = {r['cid']: r for r in json.load(open(os.path.join(paper, 'traj_v418.json')))['rows']}
    WIN = list(csv.DictReader(open(os.path.join(paper, 'occupancy_windows.csv'))))
    trig = float(texval(paper, 'StageNullTrig'))

    # ------------------------------------------------- 1. the pair, derived
    pair = sorted([r for r in LED if r['star'] == STAR and not r['attributed']],
                  key=lambda z: z['freq'])
    attr = [r for r in LED if r['star'] == STAR and r['attributed']]
    if drive == 1:                      # the pair stops being the ledger's own
        pair = pair[:1]

    def window(eb, f):
        hit = [w for w in WIN if w['eb'] == eb
               and min(float(w['flo']), float(w['fhi'])) <= f
               <= max(float(w['flo']), float(w['fhi']))]
        assert hit, (eb, f)
        assert len({(w['peakf'], w['nchan']) for w in hit}) == 1, (eb, f)
        w = hit[0]
        lo, hi = sorted((float(w['flo']), float(w['fhi'])))
        return dict(lo=lo, hi=hi, nchan=int(w['nchan']), chanw=float(w['chanw']),
                    peakf=float(w['peakf']), peaksnr=float(w['peaksnr']))

    rows = []
    for r in pair:
        w = window(r['eb'], r['freq'])
        fac = r['freq_stellar'] / r['freq']
        rows.append(dict(eb=r['eb'], f_topo=r['freq'], f_star=r['freq_stellar'],
                         tstar=r['tstar'], ctrl=r['rank_ctrl'], screen=r['screen'],
                         fac=fac, w=w, lo_star=w['lo'] * fac, hi_star=w['hi'] * fac))
    # One window, read in the stellar frame: the blocks are Doppler-tracked, so
    # their topocentric edges differ by design and only the covered band is the
    # same object.  The test is mutual coverage plus an identical channel grid.
    one_window = (len({(r['w']['nchan'], r['w']['chanw']) for r in rows}) == 1
                  and all(r['lo_star'] <= q['f_star'] <= r['hi_star']
                          for r in rows for q in rows))
    if drive == 7:                      # the two crossings stop sharing a window
        one_window = one_window and rows[0]['hi_star'] < rows[0]['lo_star']

    # -------------------------------------------- 2. the catalogue, unfiltered
    def near(fs, which):
        c = CAT['rows'][which]
        x = min(c, key=lambda z: abs(z['f_MHz'] - fs * 1e3))
        off = fs * 1e3 - x['f_MHz']
        return x, off, CKMS * off / x['f_MHz']

    for r in rows:
        for which in ('JPL', 'CDMS'):
            x, off, dv = near(r['f_star'], which)
            r[which] = dict(f=x['f_MHz'], off=off, dv=dv, qn=x['qn'],
                            elo=x['elo_cm1'] * 1.4387770, lgint=x['lgint'])
        r['elo'] = r['JPL']['elo']
        r['eu'] = r['elo'] + HK_K_PER_GHZ * r['JPL']['f'] / 1e3
    agree = all(abs(r['JPL']['f'] - r['CDMS']['f']) < 1e-3 for r in rows)
    if drive == 2:
        agree = any(abs(r['JPL']['f'] - r['CDMS']['f']) > 1e9 for r in rows)

    # ---------------------------------------------------- 3. the ladder in LTE
    jpl = CAT['rows']['JPL']

    def eu_of(x):
        return x['elo_cm1'] * 1.4387770 + HK_K_PER_GHZ * x['f_MHz'] / 1e3

    def pop(x, T):
        el = x['elo_cm1'] * 1.4387770
        return math.exp(-el / T) - math.exp(-eu_of(x) / T)

    def ratio(x, y, T):
        return 10 ** (x['lgint'] - y['lgint']) * (pop(x, T) / pop(y, T)) \
            * (pop(y, 300.0) / pop(x, 300.0))

    strong = rows[0]                 # the brighter claimed member
    weak = rows[-1]                  # [-1] and not [1]: a drive may shorten the
    #                                  list, and a drive must fail its assertion
    #                                  rather than raise
    jp_strong = [x for x in jpl if abs(x['f_MHz'] - strong['JPL']['f']) < 1e-6][0]
    jp_weak = [x for x in jpl if abs(x['f_MHz'] - weak['JPL']['f']) < 1e-6][0]
    dv = strong['JPL']['dv']
    # every ladder member whose line at that velocity lands inside the window
    inwin = [x for x in jpl
             if rows[0]['lo_star'] <= x['f_MHz'] / 1e3 * (1 + dv / CKMS) <= rows[0]['hi_star']]
    best, bestr = None, 0.0
    for x in inwin:
        if abs(x['f_MHz'] - jp_strong['f_MHz']) < 1e-6:
            continue
        rr = min(ratio(x, jp_strong, T) for T in range(*TSCAN))
        if rr > bestr:
            best, bestr = x, rr
    pred = bestr * strong['tstar']
    if drive == 3:
        pred = 0.5 * trig
    rmax = max(ratio(jp_weak, jp_strong, T) for T in range(*TSCAN))
    robs = weak['tstar'] / strong['tstar']
    if drive == 4:
        rmax = 2.0 * robs

    # ------------------------------------------------------- 4. the drifts
    tj = {}
    for r in rows:
        hit = [v for v in TRAJ.values()
               if v['star'] == STAR and abs(v['freq'] - r['f_topo']) < 1e-6]
        assert len(hit) == 1, r['f_topo']
        t = hit[0]
        steps = t['drift'] / t['step']
        exc = t['drift'] * t['dwell']                     # Hz
        tj[r['eb']] = dict(drift=t['drift'], step=t['step'], dwell=t['dwell'],
                           steps=steps, exc_MHz=exc / 1e6,
                           exc_chan=exc / t['chanw'],
                           exc_kms=CKMS * exc / (r['f_topo'] * 1e9))
        r['tj'] = tj[r['eb']]
    # WHAT THE DRIFT MEANS HERE.  A transition at rest in the stellar frame is
    # recovered at zero drift, which the grid contains.  These two are tens of
    # grid steps away, and over the block each track crosses many channels, so a
    # line would have been de-drifted out of its own channel rather than into it.
    drifty = all(v['steps'] > 10.0 for v in tj.values()) and \
        all(v['exc_chan'] > 2.0 for v in tj.values())
    if drive == 5:
        drifty = all(v['steps'] > 1e6 for v in tj.values())

    # --------------------------------------------------- 5. the repeat epoch
    for r in rows:
        rc = RCOL['%s|%.6f' % (r['eb'], r['f_topo'])]
        r['rc'] = rc

    # ----------------------------------------------------- 6. chance, measured
    half = float(texval(paper, 'MaskHalfKms'))
    comps = sorted(x['f_MHz'] / 1e3 for x in jpl)
    tol = abs(rows[0]['JPL']['dv'] - rows[-1]['JPL']['dv'])
    maxoff = max(abs(r['JPL']['dv']) for r in rows)
    rng = random.Random(985)
    N, hit = 200000, 0
    lo, hi = rows[0]['lo_star'], rows[0]['hi_star']
    for _ in range(N):
        d1 = d2 = None
        for _k in (0, 1):
            f = rng.uniform(lo, hi)
            x = min(comps, key=lambda z: abs(z - f))
            d = CKMS * (f - x) / x
            d1, d2 = (d, d1) if d1 is None else (d1, d)
        if max(abs(d1), abs(d2)) <= maxoff and d1 > 0 and d2 > 0 and abs(d1 - d2) <= tol:
            hit += 1
    pchance = hit / N
    chance_ok = 0.0 < pchance < 0.5 and tol > 0.0 and maxoff <= half
    if drive == 6:
        chance_ok = pchance < 0.0

    # ---------------------------------------------- the label, not typed
    def qlabel(qn):
        """TeX label for a CH3OH rotational transition from the catalogue's own
        quantum-number field, with the parse checked by round trip."""
        f = qn.replace('+', ' + ').replace('-', ' - ').split()
        t = re.findall(r'(\d+)\s*([+-]?)\s*(\d+)\s*([+-]?)\s*(\d+)', qn)
        g = re.match(r'\s*(\d+)\s*([+-]?)\s*(\d+)\s*([+-]?)\s*(\d+)'
                     r'\s+(\d+)\s*([+-]?)\s*(\d+)\s*([+-]?)\s*(\d+)', qn)
        assert g, qn
        ju, su, ku, yu, vu, jl, sl, kl, yl, vl = g.groups()
        assert vu == vl == '0', qn
        sym = {'+': r'\,A$^{+}$', '-': r'\,A$^{-}$', '': r'\,E'}[yu]
        lab = '$%s_{%s%s}{\\to}%s_{%s%s}$%s' % (ju, su, ku, jl, sl, kl, sym)
        back = (int(ju), (su or '+') + ku, int(jl), (sl or '+') + kl)
        assert back[0] - back[2] == 1, qn
        return lab, back

    # ------------------------------------------------------------ assertions
    ck('C1 the pair is the ledger\'s own unattributed pair for the star, both '
       'crossings in one window, and that window covers the ladder in both blocks',
       len(pair) == 2 and one_window and len(attr) >= 1
       and all(r['lo_star'] <= best['f_MHz'] / 1e3 * (1 + dv / CKMS) <= r['hi_star']
               for r in rows),
       '%d unattributed, window %.6f-%.6f GHz in the stellar frame'
       % (len(pair), rows[0]['lo_star'], rows[0]['hi_star']))
    ck('C2 the two laboratory catalogues agree on the nearest component of each',
       agree, '; '.join('%.4f vs %.4f MHz' % (r['JPL']['f'], r['CDMS']['f']) for r in rows))
    ck('C3 the brightest covered member is predicted above the trigger and above '
       'the published window maximum at every temperature of the scan',
       pred > trig and pred > max(r['w']['peaksnr'] for r in rows)
       and all(abs(r['w']['peaksnr'] - r['tstar']) < 5e-4 for r in rows),
       '%s predicted >= %.2f against trigger %.1f and window maxima %s'
       % (best['qn'].strip(), pred, trig,
          ', '.join('%.4f' % r['w']['peaksnr'] for r in rows)))
    ck('C4 the observed ratio of the two claimed members exceeds the LTE ceiling',
       robs > rmax, 'observed %.4f against a ceiling of %.4f over %d-%d K, x%.2f'
       % (robs, rmax, TSCAN[0], TSCAN[1] - 1, robs / rmax))
    ck('C5 each crossing is a drifting track, many grid steps from zero, sweeping '
       'many channels inside its own block',
       drifty, '; '.join('%.0f steps, %.2f MHz = %.1f channels'
                         % (r['tj']['steps'], r['tj']['exc_MHz'], r['tj']['exc_chan'])
                         for r in rows))
    ck('C6 the chance probability of the agreement is computed here and the '
       'agreement is the quantity it is the probability of',
       chance_ok, 'P = %.4f over %d trials for |dv1-dv2| <= %.3f km/s'
       % (pchance, N, tol))

    # ---------------------------------------------------------------- macros
    m('ZmNCross', '%d' % len(rows))
    m('ZmOffLoMHz', '%.1f' % min(r['JPL']['off'] for r in rows))
    m('ZmOffHiMHz', '%.1f' % max(r['JPL']['off'] for r in rows))
    m('ZmDvLo', '%.1f' % min(r['JPL']['dv'] for r in rows))
    m('ZmDvHi', '%.1f' % max(r['JPL']['dv'] for r in rows))
    m('ZmDvAgree', '%.2f' % tol)
    m('ZmEuLo', '%.0f' % min(r['eu'] for r in rows))
    m('ZmEuHi', '%.0f' % max(r['eu'] for r in rows))
    m('ZmChancePct', '%.1f' % (100.0 * pchance))
    m('ZmBandLo', '%.3f' % rows[0]['lo_star'])
    m('ZmBandHi', '%.3f' % rows[0]['hi_star'])
    m('ZmBright', qlabel(best['qn'])[0])
    m('ZmBrightMHz', '%.3f' % best['f_MHz'])
    m('ZmCompLo', qlabel(rows[0]['JPL']['qn'])[0])
    m('ZmCompHi', qlabel(rows[-1]['JPL']['qn'])[0])
    m('ZmCompLoMHz', '%.3f' % rows[0]['JPL']['f'])
    m('ZmCompHiMHz', '%.3f' % rows[-1]['JPL']['f'])
    m('ZmPredAplus', '%.1f' % pred)
    m('ZmTstarLo', '%.2f' % min(r['tstar'] for r in rows))
    m('ZmTstarHi', '%.2f' % max(r['tstar'] for r in rows))
    m('ZmRatioMax', '%.2f' % rmax)
    m('ZmRatioObs', '%.2f' % robs)
    m('ZmGapH', '%.1f' % (24.0 * max(r['rc']['dt_max_d'] for r in rows)))
    # =================================================================
    # R-09 (A13): PER CROSSING, IN THE ORDER THE PARAGRAPH INTRODUCES
    # THEM -- NOT AS SORTED LOW/HIGH RANGES
    # =================================================================
    # ★★★★ THIS IS THE DEFECT, NOT A TIDY-UP.  Six quantities were emitted as
    # `...Lo`/`...Hi` -- a SORTED pair -- while the prose set them out as two
    # PARALLEL per-crossing lists ("are \ZmStepsOne and \ZmStepsTwo steps
    # ... crossing \ZmSweepOne and \ZmSweepTwo channels ... recovered at
    # \ZmPersOne and \ZmPersTwo ... reaches only \ZmAnyOne and \ZmAnyTwo").
    # Sorting is not order-preserving across quantities, so **three of the six
    # lists ran in the opposite direction to the other three**: 5.7 sigma, 71
    # grid steps and 35.7 channels were attributed to the wrong crossing of
    # the two.  Nothing could see it, because every individual number was
    # right and `macrosyn` compares values.
    #
    # The order is the paragraph's own -- ascending stellar-frame offset from
    # the ladder component, which is `rows` as built -- and C7 ASSERTS that it
    # is the same order as \ZmOffLoMHz/\ZmOffHiMHz and \ZmDvLo/\ZmDvHi,
    # the two pairs the prose introduces first and the only two whose sorted
    # form happens to agree with it.  That assertion is what would have caught
    # the reversal.
    #
    # ★ Independent of every macro name: the sweep ratio equals the drift
    # ratio, 35.675/15.203 = 2.3466 against 1625.47/692.38 = 2.3477, so 35.7
    # channels and 71 steps belong to the 6.7 MHz crossing.  C8 asserts that
    # too, because it is the check that does not depend on my reading the
    # paragraph correctly.
    _one, _two = rows[0], rows[1]
    if drive == 8:
        _one, _two = _two, _one          # drive 8: the historic reversal, re-planted
    m('ZmBlockOne', _one['eb'].replace('A002_', '').replace('_', '\\_'))
    m('ZmBlockTwo', _two['eb'].replace('A002_', '').replace('_', '\\_'))
    m('ZmPersOne', '%.1f' % _one['rc']['T_pers'])
    m('ZmPersTwo', '%.1f' % _two['rc']['T_pers'])
    m('ZmAnyOne', '%.2f' % _one['rc']['T_anydrift'])
    m('ZmAnyTwo', '%.2f' % _two['rc']['T_anydrift'])
    m('ZmStepsOne', '%.0f' % _one['tj']['steps'])
    m('ZmStepsTwo', '%.0f' % _two['tj']['steps'])
    m('ZmSweepOne', '%.1f' % _one['tj']['exc_chan'])
    m('ZmSweepTwo', '%.1f' % _two['tj']['exc_chan'])
    ck('C7 the per-crossing One/Two macros run in the SAME crossing order as '
       'the offset and velocity pairs the paragraph introduces first, so no '
       'quantity is attributed to the wrong member of the pair',
       (_one['JPL']['off'] < _two['JPL']['off']
        and _one['JPL']['dv'] < _two['JPL']['dv']),
       'One off %.3f dv %.3f (%s); Two off %.3f dv %.3f (%s)'
       % (_one['JPL']['off'], _one['JPL']['dv'], _one['eb'],
          _two['JPL']['off'], _two['JPL']['dv'], _two['eb']))
    _sr = _one['tj']['exc_chan'] / _two['tj']['exc_chan']
    _dr = abs(_one['tj']['drift'] / _two['tj']['drift'])
    ck('C8 the sweep ratio equals the drift ratio, which fixes which crossing '
       'owns which sweep and which step count WITHOUT reading a macro name',
       abs(_sr - _dr) < 0.01 * _dr,
       'sweep %.4f/%.4f = %.4f against drift %.1f/%.1f = %.4f'
       % (_one['tj']['exc_chan'], _two['tj']['exc_chan'], _sr,
          _one['tj']['drift'], _two['tj']['drift'], _dr))
    ck('C9 the two crossings are in DIFFERENT blocks, \\ZmGapH apart -- which '
       'is the fact A13 turns on and which makes "neither is present 24.4 h '
       'later" false for the second, whose covering block is 24.4 h EARLIER',
       _one['eb'] != _two['eb'],
       '%s and %s, %.1f h apart'
       % (_one['eb'], _two['eb'],
          24.0 * max(r['rc']['dt_max_d'] for r in rows)))
    #: ZmPersLo/Hi, ZmStepsLo/Hi, ZmSweepLo/Hi and ZmAnyLo/Hi are NO LONGER
    #: EMITTED.  They are cited nowhere after R-08, and leaving them would
    #: leave the misleading form available to the next person to write this
    #: paragraph -- which is exactly how it got written the first time.
    m('ZmCoReg', '%.2f' % max(abs(r['dv_stellar']) for r in attr))
    m('ZmCoNBlock', '%d' % len(attr))
    m('ZmQueryDate', CAT['fetched_utc'][:10])

    # ----------------------------------------------------------------- output
    tex = os.path.join(out, 'numbers/survey_numbers_round985%s.tex' % suf)
    with open(tex, 'w') as fh:
        fh.write('%% GENERATED by ch3oh_r25.py -- do not hand-edit.\n')
        fh.write('\n'.join(MACROS) + '\n')
    json.dump(dict(rows=[{k: v for k, v in r.items() if k != 'w'} for r in rows],
                   pred=pred, rmax=rmax, robs=robs, pchance=pchance, tol=tol,
                   brightest=best, inwin=len(inwin), macros=MACROS, failed=FAIL),
              open(os.path.join(out, 'ch3oh_r25%s.json' % suf), 'w'),
              indent=1, default=str)
    print('  %d macros, %d assertions failed %s' % (len(MACROS), len(FAIL), FAIL))
    return 1 if (FAIL and not drive) else 0


if __name__ == '__main__':
    sys.exit(main())
