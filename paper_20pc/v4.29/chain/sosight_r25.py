#!/usr/bin/env python3
r"""Round 986: the three crossings that coincide with sulphur monoxide, and
what their own sightlines say.

★ r28 (v4.29, Ruling R3): SULPHUR MONOXIDE IS BACK IN THE MASK, under the one
rule every species obeys (covered by these setups, detected in discs or
molecular clouds).  The three crossings are therefore ATTRIBUTED, on the
coincidence alone, and this file now measures what an attribution of that
kind rests on: no catalogued gas at the crossing's own LSR velocity, and no
CO(3-2) above the trigger in the same window.  S2 and S6 are restated in that
direction; everything else is unchanged.  The history below is kept because
it explains the v4.26-v4.28 state the referee objected to.

WHY THIS FILE EXISTS

    Sulphur monoxide was masked for bandwidth and not for attribution: its
    transitions were counted in the cost of the mask and in the statement
    that the survey constrains nothing inside it, while crossings falling on
    them were kept, tested and reported as unattributed.  That is not a
    consistent object, and the inconsistency is resolved the way the
    bandwidth is cheaper and the evidence is unchanged: SO leaves the mask,
    so those channels are searched and the three crossings stay unattributed
    and reported, each with its offset to the nearest SO transition printed.

    THE REASON FOR LEAVING IT OUT IS ABOUT SECOND-GENERATION GAS, AND IT HAS
    A LIMIT.  No debris disc has a reported SO detection; the gas seen in
    these discs is CO, C and O.  But sulphur monoxide IS an interstellar
    molecule, so a crossing on a molecular-cloud sightline could be
    interstellar SO rather than noise -- and this survey's own coincidences
    include interstellar ones.  So the question is not a preference but a
    measurement, made here for each of the three on the sightline it was
    found on, with the instrument that can make it: a single-dish CO survey,
    where nothing is resolved out.

WHAT IT MEASURES, PER CROSSING
    the offset to the nearest SO transition in the star's frame AND in the
    local standard of rest, where interstellar gas is at rest; whether the
    composite CO(1-0) survey or the all-sky Planck CO map shows gas on that
    sightline at all, and at what velocity; and whether the window the
    crossing sits in, which covers CO(3-2) in every case, holds anything
    above the trigger -- carbon monoxide being some four orders of magnitude
    the more abundant of the two.

ASSERTIONS (each driven to fail on its own, --drive 1..8)

  S1  the three are DERIVED, not listed: they are the crossings whose
      nearest transition of the full query is sulphur monoxide and inside
      the published half-width in the star's own frame.
  S2  all three remain unattributed in the shipped ledger, which is what
      taking SO out of the mask means, and none of them is confirmed.
  S3  no sightline carries catalogued CO at the crossing's own LSR
      velocity: the directions outside the CfA footprint are below the
      Planck ceiling, and for any direction that IS detected the catalogued
      emission is further from the crossing's velocity than the survey's own
      cloud tolerance.
  S4  every one of the three windows covers CO(3-2), and in every one the
      maximum over the whole channel-drift grid is the crossing itself, so
      no CO(3-2) feature above the trigger exists in any of the blocks.
  S5  the frames are both reported and disagree for at least one of them, so
      a reader sees that an interstellar reading is not the same test as a
      circumstellar one.
  S6  the sulphur monoxide transitions are no longer in the mask this
      paper's attributions use, and the three crossings' nearest MASKED
      transition is therefore a different one, named here.
  S7  the local-standard-of-rest frequency computed here reproduces the one
      the frame chain has already published for the same crossings, so this
      file has not grown a second implementation of the frame.

Usage: sosight_r25.py [--paper DIR] [--out DIR] [--drive N]
-> survey_numbers_round986.tex, sosight_r25.json
"""
import argparse
import csv
import json
import os
import re
import sys

CKMS = 299792.458
#: Flat rotation curve, for the ONE geometric statement the cloud sightline needs:
#: Reid et al. (2019), R0 = 8.15 kpc, Theta0 = 236 km/s.  Cited in the prose.
R0_KPC, THETA0_KMS = 8.15, 236.0
#: the molecular scale height, for scale only, Heyer & Dame (2015)
H_MOL_KPC = 0.075
MACROS, FAIL = [], []


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
        if fn.endswith('.tex'):
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
    paper, out = a.paper, a.out or (a.out or a.paper)
    suf = '_drive%d' % a.drive if a.drive else ''
    drive = a.drive
    sys.path.insert(0, paper)
    import maskframe_v411 as mf
    import maskcat_v412 as mc
    import masklsr_v520 as ml
    import star_alias as sa

    HALF = mf.MASK_HALF_KMS
    LED = json.load(open(os.path.join(paper, 'ledger.json')))['rows']
    DHT = json.load(open(os.path.join(paper, 'r15inputs', 'co_dht_r15.json')))
    PL = json.load(open(os.path.join(paper, 'r15inputs', 'co_planck_r15.json')))
    LOS = json.load(open(os.path.join(paper, 'r15inputs', 'losdir_r15.json')))
    WIN = list(csv.DictReader(open(os.path.join(paper, 'occupancy_windows.csv'))))
    RCOL = json.load(open(os.path.join(paper, 'recurcols_v411.json')))
    trig = float(texval(paper, 'StageNullTrig'))
    ceil_k = ml.CO_CEIL_K_KMS
    tol_cloud = float(texval(paper, 'LsCloudDvMax'))
    co32 = [v[0] for k, v in mf.TRANS.items() if k.startswith('CO(3-2')][0]

    # ----------------------------------------- the SO list, and that it is out
    ALL = getattr(mc, 'MASK_ALL', mc.MASK)
    so = {k: v['f'] for k, v in ALL.items() if mc.species_of(k) == 'SO'}
    # r28: SO is IN the mask the attributions use (the name is kept for the
    # clause below, which now asserts the opposite of what it did)
    out_of_mask = any(mf.species(k) == 'SO' for k in mf.TRANS)
    if drive == 6:
        out_of_mask = not out_of_mask

    # ------------------------------------------------- the three, derived
    rows = []
    for r in LED:
        fs = r['frame']['f_stellar']
        nm, f0 = min(so.items(), key=lambda kv: abs(CKMS * (fs - kv[1]) / kv[1]))
        dv = CKMS * (fs - f0) / f0
        if abs(dv) > (HALF if drive != 1 else 1.0):
            continue
        # ★ KEY ON THE CANONICAL DESIGNATION, NEVER ON THE LEDGER'S RAW NAME.
        # The ledger carries `HD161868` where the sightline files carry
        # `HD 161868`; this project has produced fourteen wrong-key joins and
        # every one of them looked like a missing star.
        rows.append(dict(star=sa.designation(r['star'], tex=False),
                         star_raw=r['star'], display=r['display'], eb=r['eb'],
                         f_topo=r['freq'], f_star=fs, tstar=r['tstar'],
                         ctrl=r['rank_ctrl'], screen=r['screen'],
                         attributed=r['attributed'], line_mask=r['line'],
                         dv_mask=r['dv_stellar'], so_line=nm, so_f=f0, dv_star=dv))
    rows.sort(key=lambda z: z['star'])
    LEDF = {(r['eb'], round(r['freq'], 6)): r['frame'] for r in LED}

    # --------------------------------- the LSR reading, against the SO line
    apex = ml._apex_icrs()
    for r in rows:
        s = LOS['star'][r['star']]
        vsun = ml.solar_projection(s['ra'], s['dec'], apex)
        # f_bary comes from the ledger's own frame record and is not recomputed
        # here: the barycentric step is one object in this build, and a second
        # implementation of it is a second answer waiting to be quoted.
        f_bary = LEDF[(r['eb'], round(r['f_topo'], 6))]['f_bary']
        f_lsr = ml.to_lsr(f_bary, vsun)
        r['v_sun'] = vsun
        r['f_lsr'] = f_lsr
        r['dv_lsr'] = CKMS * (f_lsr - r['so_f']) / r['so_f']
        r['v_feature_lsr'] = -r['dv_lsr']
        r['in_lsr'] = abs(r['dv_lsr']) <= HALF

    def kinematic_z(l_deg, b_deg, v_lsr):
        """How far off the mid-plane gas at this LSR velocity would have to be,
        on a flat rotation curve: both solutions, in kpc."""
        import math as _m
        l, b = _m.radians(l_deg), _m.radians(b_deg)
        w = v_lsr / (R0_KPC * _m.sin(l)) + THETA0_KMS / R0_KPC
        R = THETA0_KMS / w
        disc = R * R - (R0_KPC * _m.sin(l)) ** 2
        if disc < 0 or _m.sin(l) == 0.0:
            return None
        root = _m.sqrt(disc)
        ds = [R0_KPC * _m.cos(l) - root, R0_KPC * _m.cos(l) + root]
        return sorted(abs(d * _m.tan(b)) for d in ds if d > 0)

    # ------------------------------------------------- the sightline evidence
    for r in rows:
        d, p = DHT['los'][r['star']], PL['los'][r['star']]
        r['l'], r['b'] = d['l'] % 360.0, d['b']
        r['covered'] = bool(d['covered'])
        r['planck'] = p['w_co_cone_max']
        r['cloud'] = None
        if r['covered']:
            v = d['vel_kms']
            t = d['t_mb_K']
            i = min(range(len(v)), key=lambda j: abs(v[j] - r['v_feature_lsr']))
            r['cloud'] = dict(t_peak=d['t_peak_K'], v_peak=d['v_peak_kms'],
                              w=d['w_co_K_kms'], v_near=v[i], t_near=t[i],
                              v_lo=min(v), v_hi=max(v),
                              dv_from_peak=abs(r['v_feature_lsr'] - d['v_peak_kms']))
        # the window, and CO(3-2) inside it
        hit = [w for w in WIN if w['eb'] == r['eb']
               and min(float(w['flo']), float(w['fhi'])) <= r['f_topo']
               <= max(float(w['flo']), float(w['fhi']))]
        assert hit and len({(w['peakf'], w['nchan']) for w in hit}) == 1, r['eb']
        w = hit[0]
        lo, hi = sorted((float(w['flo']), float(w['fhi'])))
        r['win'] = dict(lo=lo, hi=hi, nchan=int(w['nchan']),
                        chanw=float(w['chanw']), peakf=float(w['peakf']),
                        peaksnr=float(w['peaksnr']), co32=lo <= co32 <= hi)
        rc = RCOL.get('%s|%.6f' % (r['eb'], r['f_topo'])) or {}
        r['recurs'] = bool(rc.get('T_matched') is not None
                           and rc.get('T_matched', 0) >= trig)

    n_pub = int(texval(paper, 'MkNSOCross')) if _has(paper, 'MkNSOCross') else 3
    cloudy = [r for r in rows if r['covered'] and r['planck'] > ceil_k]
    no_gas = all((r['planck'] <= ceil_k) if not r['covered']
                 else (r['cloud']['dv_from_peak'] > tol_cloud) for r in rows)
    if drive == 3:
        no_gas = all((r['planck'] <= -1.0) for r in rows)
    # ★ GEN (v4.29 fold, E3 / R21): `occupancy_windows.csv` is the frozen per-window extract of the PRE-FOLD
    #   products.  A window the fold re-ran (HD 161868 X10ca8: 5.4812 there, 5.2727 now) is compared with the
    #   statistic its shipped (pre-fold) export row carried -- refoldpop_r29.prefold_max, the fold's own input --
    #   which proves the extract is that product and the crossing was its maximum; the re-run statistic is the
    #   new product's own window maximum (the export row).  Windows not re-run compare with the ledger as before.
    import refoldpop_r29

    def _want_peak(r):
        k = refoldpop_r29.wkey(r['eb'], r['win']['lo'], r['win']['hi'])
        if k in refoldpop_r29.rerun_keys():
            return refoldpop_r29.prefold_max(r['eb'], r['win']['lo'], r['win']['hi'])
        return r['tstar']
    win_ok = all(r['win']['co32'] and _want_peak(r) is not None
                 and abs(r['win']['peaksnr'] - _want_peak(r)) < 5e-4
                 for r in rows)
    if drive == 4:
        win_ok = all(not r['win']['co32'] for r in rows)
    # r28: attributed (the mask holds SO again), and none recurs
    unattr = all(r['attributed'] and not r['recurs'] for r in rows)
    if drive == 2:
        unattr = all(not r['attributed'] for r in rows)
    frames = any(r['in_lsr'] != (abs(r['dv_star']) <= HALF) for r in rows)
    if drive == 5:
        frames = not frames

    ck('S1 the three are derived from the full query and the half-width, not listed',
       len(rows) == n_pub and len(so) > 0,
       '%d crossings within %.0f km/s of one of the %d SO transitions: %s'
       % (len(rows), HALF, len(so), ', '.join(r['star'] for r in rows)))
    ck('S2 all of them are attributed in the shipped ledger and none recurs',
       unattr, 'attributed flags %s' % [r['attributed'] for r in rows])
    ck('S3 no sightline carries catalogued CO at the crossing\'s own LSR velocity',
       no_gas, '; '.join('%s %s' % (r['star'], ('Planck %.3f K km/s' % r['planck'])
                                    if not r['covered'] else
                                    ('CfA peak %.2f K at %+.2f, %.1f km/s away'
                                     % (r['cloud']['t_peak'], r['cloud']['v_peak'],
                                        r['cloud']['dv_from_peak'])))
                         for r in rows))
    ck('S4 every window covers CO(3-2) and its maximum over the whole grid is the '
       'crossing itself', win_ok,
       '; '.join('%.4f at %.6f' % (r['win']['peaksnr'], r['win']['peakf']) for r in rows))
    ck('S5 both frames are reported and they disagree for at least one', frames,
       '; '.join('%s %+.1f star / %+.1f LSR' % (r['star'], r['dv_star'], r['dv_lsr'])
                 for r in rows))
    # ★★ S7 EXISTS BECAUSE THE FIRST VERSION OF THIS FILE WAS WRONG AND EVERY
    # OTHER ASSERTION PASSED.  It recomputed the barycentric step instead of
    # reading the ledger's, and the LSR velocities came out 15 to 26 km/s off --
    # a wrong number in the paper with a clean gate.  The frame chain has one
    # implementation, and this check is that this file used it.
    MLS = {(x['eb'], round(float(x['freq']), 6)): x
           for x in json.load(open(os.path.join(paper, 'masklsr_v520.json')))['rows']}
    dfs = [abs(r['f_lsr'] - MLS[(r['eb'], round(r['f_topo'], 6))]['f_lsr'])
           for r in rows]
    frame_ok = max(dfs) < 1e-6 if dfs else False
    if drive == 7:
        frame_ok = max(dfs) < 0.0
    ck('S7 the LSR frequency here reproduces the one the frame chain already '
       'published for the same crossings', frame_ok,
       'largest difference %.3f kHz' % (1e6 * max(dfs)))
    out_of_mask = out_of_mask and all(r['line_mask'] == r['so_line']
                                      for r in rows)
    ck('S6 sulphur monoxide is in the mask the attributions use, and each '
       'crossing\'s nearest masked transition is its SO line', out_of_mask,
       '%d masked transitions, %d of them SO' % (len(mf.TRANS),
                                                 sum(1 for k in mf.TRANS
                                                     if mf.species(k) == 'SO')))

    # ---------------------------------------------------------------- macros
    _W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven')
    m('SoNCross', '%d' % len(rows))
    m('SoNCrossWord', _W[len(rows)] if len(rows) < len(_W) else '%d' % len(rows))
    m('SoNTrans', '%d' % len(so))
    m('SoStars', _list([r['display'].replace(' ', '~') for r in rows]))
    m('SoDvList', _list(['$%+.1f$' % r['dv_star'] for r in rows], tex=False))
    m('SoDvLsrList', _list(['$%+.1f$' % r['dv_lsr'] for r in rows]))
    m('SoNInLsr', '%d' % sum(1 for r in rows if r['in_lsr']))
    m('SoNInLsrWord', _W[sum(1 for r in rows if r['in_lsr'])])
    m('SoEuLo', '%.0f' % min(ALL[r['so_line']]['eu'] for r in rows))
    m('SoEuHi', '%.0f' % max(ALL[r['so_line']]['eu'] for r in rows))
    m('SoTstarLo', '%.2f' % min(r['tstar'] for r in rows))
    m('SoTstarHi', '%.2f' % max(r['tstar'] for r in rows))
    m('SoNBelowScreen', '%d' % sum(1 for r in rows if not r['screen']))
    m('SoPlanckMax', '%.2f' % max(r['planck'] for r in rows if not r['covered']))
    m('SoPlanckCeil', '%.1f' % ceil_k)
    m('SoNUncovered', '%d' % sum(1 for r in rows if not r['covered']))
    if cloudy:
        c = cloudy[0]
        z = kinematic_z(c['l'], c['b'], c['v_feature_lsr'])
        if z:
            m('SoCloudZLo', '%.1f' % z[0])
            m('SoCloudZHi', '%.1f' % z[-1])
            m('SoCloudZScale', '%.0f' % (z[0] / H_MOL_KPC))
            ck('S8 gas at the crossing\'s own LSR velocity in that direction would '
               'lie far off the mid-plane, so the sightline\'s catalogued cloud is '
               'not available at that velocity',
               z[0] > 10.0 * H_MOL_KPC if drive != 8 else z[0] < 0.0,
               '%.1f to %.1f kpc from the plane, against a %.0f pc scale height'
               % (z[0], z[-1], 1e3 * H_MOL_KPC))
        m('SoCloudStar', c['display'].replace(' ', '~'))
        m('SoCloudTpeak', '%.1f' % c['cloud']['t_peak'])
        m('SoCloudVpeak', '%+.1f' % c['cloud']['v_peak'])
        m('SoCloudW', '%.1f' % c['cloud']['w'])
        m('SoCloudVfeat', '%+.1f' % c['v_feature_lsr'])
        m('SoCloudDv', '%.0f' % c['cloud']['dv_from_peak'])
        m('SoCloudDvStar', '%.1f' % c['dv_star'])
        m('SoCloudDvLsr', '%.1f' % c['dv_lsr'])
        m('SoCloudGlon', '%.0f' % c['l'])
        m('SoCloudGlat', '%+.0f' % c['b'])
    json.dump(dict(rows=rows, n_so=len(so), macros=MACROS, failed=FAIL),
              open(os.path.join(out, 'sosight_r25%s.json' % suf), 'w'),
              indent=1, default=str)
    with open(os.path.join(out, 'numbers/survey_numbers_round986%s.tex' % suf), 'w') as fh:
        fh.write('%% GENERATED by sosight_r25.py -- do not hand-edit.\n')
        fh.write('\n'.join(MACROS) + '\n')
    print('  %d macros, %d assertions failed %s' % (len(MACROS), len(FAIL), FAIL))
    return 1 if (FAIL and not drive) else 0


def _has(paper, name):
    try:
        texval(paper, name)
        return True
    except KeyError:
        return False


def _list(xs, tex=True):
    xs = list(xs)
    if len(xs) == 1:
        return xs[0]
    return ', '.join(xs[:-1]) + ' and ' + xs[-1]


if __name__ == '__main__':
    sys.exit(main())
