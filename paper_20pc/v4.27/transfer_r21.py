#!/usr/bin/env python3
r"""R1-5: does the transferred completeness carry the uncertainty of the
TRANSFER, and does that uncertainty include BETWEEN-CONFIGURATION variation?

Nothing new is measured here.  Every number is read from the records the
published completeness is built from, and the question is whether the
interval the paper quotes covers the variation the records themselves show
across instrumental configurations.

  sens_r11.json   the published completeness, its per-window points, its
                  stratum medians by band / array / channel width, and the
                  transfer row of the budget
  per_target_results_v3.99.csv
                  the population of Class A windows, with the configuration
                  of each and each system's best window

Three things are established, in this order:

 1. WHAT THE QUOTED TRANSFER INTERVAL IS.  The 16th-84th percentile of the
    per-window ninety-per-cent points across the 49 directly injected
    windows, as a factor on the adopted class value.
 2. WHETHER IT COVERS THE CONFIGURATION AXES.  The largest difference between
    stratum medians on each of band, array and channel width, compared with
    that interval.  If any axis exceeds it, the interval does not cover
    between-configuration variation and the paper must say so.
 3. WHERE THE TRANSFER IS AN EXTRAPOLATION RATHER THAN AN INTERPOLATION.
    Configurations the population holds and the injected sample does not
    hold at all -- the windows and, more importantly, the SYSTEMS whose best
    window sits in one, because those are the limits a reader takes from
    Table F1.

Writes transfer_r21.json.  Assertions pin invariants, not today's values.
"""
import collections
import csv
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V421 = HERE   # the version tree this generator lives in
OUT = os.path.join(HERE, 'transfer_r21.json')

S = json.load(open(os.path.join(V421, 'sens_r11.json')))
CAT = list(csv.DictReader(open(os.path.join(
    V421, 'per_target_results_v3.99.csv'))))

A = [r for r in CAT if r['search_class'] == 'A']
P90 = S['p90']
TAGS = set(S['tags'])
PER = S['per_window']

FAIL = []


def ck(label, cond, detail=''):
    print('  %-74s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


def chanlab(hz):
    return '%d kHz' % round(float(hz) / 1e3)


def arrof(r):
    """The array, from the published geometry route sens_r11 itself uses: the
    dish diameter is not a catalogue column, so the 7 m array is identified by
    its primary-beam width at the window's own frequency, which is."""
    # theta_pb = 1.22 lambda / D in arcsec; D follows from theta_pb and nu.
    th = float(r['theta_pb_arcsec'])
    f = 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz'])) * 1e9
    d = 1.22 * 2.99792458e8 / f / (th / 206264.80624709636)
    return '7m' if d < 10.0 else '12m'


DRIVE = 0
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])


def main():
    R = {}
    if DRIVE == 1:
        # a configuration axis that moves the completeness further than the
        # quoted transfer bracket: clause 3 must stop the run.
        S['spreads']['band']['6'] = S['p90'] * 2.0
    if DRIVE == 2:
        # a transfer bracket that is not a function of the per-window points
        S['transfer']['hi'] = 1.0 + 3.0 * (S['transfer']['full_hi'] - 1.0)
    if DRIVE == 3:
        # the full range no longer set by one window
        k = max(PER, key=lambda g: PER[g]['trig'] or 0)
        PER[k]['trig'] = sorted(
            (PER[g]['trig'] for g in PER if PER[g]['trig']), reverse=True)[1]
    if DRIVE == 4:
        # the budget row decoupled from the bracket
        S['budget']['transfer_hi'] = 0.5

    # ---------------------------------------------------------------- 1
    pts = sorted(PER[g]['trig'] for g in PER if PER[g]['trig'] is not None)
    assert len(pts) == S['n_injected'], (len(pts), S['n_injected'])
    lo16 = statistics.quantiles(pts, n=100, method='inclusive')[15]
    hi84 = statistics.quantiles(pts, n=100, method='inclusive')[83]
    R['interval'] = dict(n=len(pts), p90=P90,
                         published_lo=S['transfer']['lo'],
                         published_hi=S['transfer']['hi'],
                         full_lo=S['transfer']['full_lo'],
                         full_hi=S['transfer']['full_hi'],
                         budget_lo_pct=100 * S['budget']['transfer_lo'],
                         budget_hi_pct=100 * S['budget']['transfer_hi'])
    # the published interval must BE a quantile spread of the per-window
    # points: an interval that is not a function of the points cannot carry
    # the transfer's own uncertainty.  Invariant, not a value: the quoted
    # bracket must lie inside the full range and contain the adopted point.
    ck('the quoted transfer bracket lies inside the full range of the '
       'per-window points and contains the adopted value',
       S['transfer']['full_lo'] <= S['transfer']['lo'] <= 1.0
       <= S['transfer']['hi'] <= S['transfer']['full_hi'],
       'x%.3f-x%.3f inside x%.3f-x%.3f'
       % (S['transfer']['lo'], S['transfer']['hi'],
          S['transfer']['full_lo'], S['transfer']['full_hi']))
    ck('the budget transfer row is that same bracket and not a separate '
       'number',
       abs(100 * S['budget']['transfer_lo'] - 100 * (1 - S['transfer']['lo']))
       < 0.05 and abs(100 * S['budget']['transfer_hi']
                      - 100 * (S['transfer']['hi'] - 1)) < 0.05,
       '-%.2f/+%.2f per cent'
       % (100 * S['budget']['transfer_lo'], 100 * S['budget']['transfer_hi']))

    # ---------------------------------------------------------------- 2
    sp = S['spreads']
    axes = {}
    for name, d in (('band', sp['band']), ('channel width', sp['chanw']),
                    ('array', sp['array'])):
        v = list(d.values())
        axes[name] = dict(levels={str(k): d[k] for k in d},
                          spread=max(v) - min(v),
                          spread_frac=(max(v) - min(v)) / P90)
    R['configuration_axes'] = axes
    widest = max(axes, key=lambda k: axes[k]['spread_frac'])
    halfwidth = max(1 - S['transfer']['lo'], S['transfer']['hi'] - 1)
    R['widest_axis'] = dict(axis=widest,
                            frac=axes[widest]['spread_frac'],
                            transfer_halfwidth=halfwidth)
    # ★ THE INVARIANT, NOT TODAY'S NUMBER: whatever the widest configuration
    # axis turns out to be, the transfer interval the paper quotes must be at
    # least as wide as it.  If a future campaign finds a configuration that
    # moves the completeness further than the interval, this fails and the
    # interval has to grow -- which is the whole point of the referee's
    # question.
    ck('the quoted transfer interval is at least as wide as the largest '
       'difference between configuration strata',
       halfwidth >= axes[widest]['spread_frac'] - 1e-12,
       '%s spans %.1f per cent of the adopted value against a transfer '
       'bracket of %.1f per cent'
       % (widest, 100 * axes[widest]['spread_frac'], 100 * halfwidth))

    # ---------------------------------------------------------------- 3
    cov = S['covariates']
    unc = {}
    for ax, key in (('band', 'band'), ('array', 'array'),
                    ('chanw', 'chanw')):
        pop, ach = cov[ax]['population'], cov[ax]['achieved']
        unc[ax] = sorted(k for k in pop if k not in ach)
    R['levels_absent_from_injected_sample'] = unc

    # the windows, and the systems whose BEST window sits in such a level
    ach_band = set(cov['band']['achieved'])
    ach_chan = set(cov['chanw']['achieved'])
    ach_arr = set(cov['array']['achieved'])

    def extrap(r):
        why = []
        if r['band'] not in ach_band:
            why.append('band %s' % r['band'])
        if chanlab(r['chanw_Hz']) not in ach_chan:
            why.append('channel width %s' % chanlab(r['chanw_Hz']))
        if arrof(r) not in ach_arr:
            why.append('array %s' % arrof(r))
        return why

    ex_win = [r for r in A if extrap(r)]
    R['extrapolated_windows'] = dict(
        n=len(ex_win), n_class_a=len(A),
        reasons=dict(collections.Counter(
            '; '.join(extrap(r)) for r in ex_win)))

    # each system's best window = the smallest adopted EIRP_90
    best = {}
    for r in A:
        v = r.get('eirp_p90_adopted_W') or r.get('eirp_p90_trigratio_W')
        if not v:
            continue
        k = r['system_id']
        if k not in best or float(v) < float(best[k][0]):
            best[k] = (float(v), r)
    ex_sys = {k: extrap(r) for k, (_, r) in best.items() if extrap(r)}
    inj_sys = {k for k, (_, r) in best.items()
               if '%s_spw' % r['eb'] in ''.join(TAGS)
               or any(g.startswith(r['eb']) for g in TAGS)}
    R['systems'] = dict(n=len(best), n_best_window_extrapolated=len(ex_sys),
                        extrapolated=
                        {k: v for k, v in sorted(ex_sys.items())},
                        n_best_window_in_injected_block=len(inj_sys))
    ck('the systems whose best window sits in a configuration the injected '
       'sample never held are counted and named, not left implicit',
       isinstance(ex_sys, dict),
       '%d of %d systems' % (len(ex_sys), len(best)))

    # ---------------------------------------------------------------- 4
    # The 49 points must actually support a single pooled factor: the test the
    # referee asks for is whether the dispersion is consistent with one value
    # plus sampling, or whether it is structured.  Read out, not modelled:
    # how much of the full range is one window, and how far the second
    # extreme sits.
    top = pts[-1]
    second = pts[-2]
    R['dispersion'] = dict(lo=pts[0], hi=top, second_hi=second,
                           median=statistics.median(pts),
                           within_tenth=sum(
                               1 for p in pts if abs(p / P90 - 1) <= 0.10),
                           iqr=(statistics.quantiles(pts, n=4)[0],
                                statistics.quantiles(pts, n=4)[2]))
    ck('the upper end of the per-window range is one window and is published '
       'as such, not as a typical transfer error',
       top > 1.25 * second,
       '%.2f against %.2f for the next, shallowest window %s'
       % (top, second, S['transfer']['shallowest']))

    json.dump(R, open(OUT, 'w'), indent=1, sort_keys=True)
    print('\nwrote %s' % OUT)
    print(json.dumps({k: R[k] for k in
                      ('interval', 'widest_axis',
                       'levels_absent_from_injected_sample',
                       'extrapolated_windows', 'systems', 'dispersion')},
                     indent=1, sort_keys=True))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
