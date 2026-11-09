#!/usr/bin/env python3
r"""extrap_r33 -- which Class A windows, and which systems' best windows, lie
outside the configurations the injection campaign covered.

WHY IT IS A MODULE.  The rule was written inside `r1_r22.py` (round 972,
R1-2 of round 22), which publishes \NgNExtrapWin, \NgNInterpWin and
\NgNExtrapSys from it.  Round 32 (R1-5) asks for three more uses of the same
set: the systems are named and marked in Table F1 (`persys_r17.py`, which runs
BEFORE r1_r22 in make_all.sh and so cannot read its json), the summaries over
systems are printed over the interpolated-only sample beside the full one
(`rankcharge_r33.py`), and the window-to-window dispersion is said to apply
to the interpolated transfers only.  Three copies of one rule is how a table
and a sentence end up describing two different sets, so the rule lives here,
once, and r1_r22's A14 requires its own (unchanged) computation to give the
same set.  Nothing here is typed: the injected set is the deposit's own
`p90_basis` column, the axes are r1_r22's, and the best window is the
adopted one (`adopted_e90`, eligible windows only).

THE RULE (r1_r22, r27 row 1).  A transferred Class A window is EXTRAPOLATED
when it leaves the injected range on at least one of: band, channel width,
array, configuration (synthesised beam within the array), integration time,
block duration.  Otherwise it is INTERPOLATED.  A system is extrapolated when
its best eligible window is.

  python3 extrap_r33.py     # prints the sets
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import adopted_e90 as ae      # noqa: E402


def classify(paper=HERE, rows=None, e90=None):
    """Return a dict: rows, e90, inj (list of injected Class A rows), extrap,
    interp (transferred rows outside / inside the injected range), best
    (system_id -> its best eligible Class A row), ex_sys (sorted system ids
    whose best window is extrapolated), outside (id(row) -> list of axes)."""
    R = rows if rows is not None else ae.catalogue(paper)
    E = e90 if e90 is not None else ae.per_window(R, paper)
    A = [r for r in R if r['search_class'] == 'A']
    best = {}
    for r in A:
        if not ae.limit_eligible(r, paper):
            continue
        s = r['system_id']
        if s not in best or E[id(r)] < E[id(best[s])]:
            best[s] = r
    inj = [r for r in A if r['p90_basis'] == 'injected']
    arch = json.load(open(os.path.join(paper, 'archive_meta_v381.json')))['ebs']

    def _arr(r):
        return arch[r['eb']]['array']

    def _res(r):
        return float(arch[r['eb']]['s_resolution_arcsec'])

    bdur = collections.defaultdict(float)
    for r in R:
        bdur[r['eb']] = max(bdur[r['eb']], float(r['on_source_s']))
    b_inj = {r['band'] for r in inj}
    c_inj = {round(float(r['chanw_Hz'])) for r in inj}
    a_inj = {_arr(r) for r in inj}

    def _rng(f):
        return (min(f(r) for r in inj), max(f(r) for r in inj))

    t_inj = _rng(lambda r: float(r['on_source_s']))
    d_inj = _rng(lambda r: bdur[r['eb']])
    r_inj = {a: (min(_res(r) for r in inj if _arr(r) == a),
                 max(_res(r) for r in inj if _arr(r) == a)) for a in a_inj}

    def outside(r):
        o = []
        if r['band'] not in b_inj:
            o.append('band')
        if round(float(r['chanw_Hz'])) not in c_inj:
            o.append('channel width')
        if _arr(r) not in a_inj:
            o.append('array')
        elif not r_inj[_arr(r)][0] <= _res(r) <= r_inj[_arr(r)][1]:
            o.append('configuration')
        if not t_inj[0] <= float(r['on_source_s']) <= t_inj[1]:
            o.append('integration time')
        if not d_inj[0] <= bdur[r['eb']] <= d_inj[1]:
            o.append('block duration')
        return o

    injid = {id(r) for r in inj}
    out = {id(r): outside(r) for r in A if id(r) not in injid}
    extrap = [r for r in A if id(r) not in injid and out[id(r)]]
    interp = [r for r in A if id(r) not in injid and not out[id(r)]]
    exid = {id(r) for r in extrap}
    ex_sys = sorted(s for s, r in best.items() if id(r) in exid)
    return dict(rows=R, e90=E, inj=inj, extrap=extrap, interp=interp,
                best=best, ex_sys=ex_sys, outside=out)


def extrap_systems(paper=HERE):
    return set(classify(paper)['ex_sys'])


if __name__ == '__main__':
    c = classify()
    print('extrap_r33: %d injected, %d interpolated, %d extrapolated Class A '
          'windows; %d systems take their best window from an extrapolated one:'
          % (len(c['inj']), len(c['interp']), len(c['extrap']),
             len(c['ex_sys'])))
    for s in c['ex_sys']:
        r = c['best'][s]
        print('  %-28s %s %.3f-%.3f GHz %.0f kHz  %.3e W  outside on: %s'
              % (s, r['eb'], float(r['flo_GHz']), float(r['fhi_GHz']),
                 float(r['chanw_Hz']) / 1e3, c['e90'][id(r)],
                 ', '.join(c['outside'][id(r)])))
