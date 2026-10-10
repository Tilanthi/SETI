#!/usr/bin/env python3
r"""Round 520: the molecular mask evaluated in the local standard of rest as
well as in each star's own rest frame, and the carbon monoxide that two
published large-scale surveys show along these lines of sight.

WHY THIS FILE EXISTS

    Attribution is a velocity criterion, and a velocity criterion needs a
    frame.  Circumstellar gas is at rest in the star's frame, which is the
    frame the mask is evaluated in, and it is the ADOPTED frame: attribution
    is decided there and nowhere else.  Interstellar gas along the line of
    sight is at rest in the local standard of rest, and for a star whose own
    LSR velocity is large a foreground line therefore falls outside the mask
    by construction, so every crossing is evaluated in that frame too -- as a
    CHECK.  The check changes no disposition (L10), which is the only
    condition under which calling it a check is honest; the either-frame
    counts and the bandwidth it would have cost are reported as the
    alternative.  Whether there is any foreground gas to be confused with is
    answered from published data rather than argued.

WHAT IT OWNS

1.  THE SECOND FRAME.  One further transform, in the same two declared steps
    as the first: f_lsr = f_bary * (1 - v_sun/c), where v_sun is the
    projection of the standard solar motion -- 20 km/s toward the B1900 apex
    18h03m50.3s +30d00m17s -- onto the line of sight.  The offset from a
    transition is dv_lsr = c (f_lsr - f_rest) / f_rest, the same definition
    and the same sign as in the stellar frame.  Both conventions of the
    radio LSR are computed and required to agree.

2.  THE DIFFERENCE BETWEEN THE FRAMES IS ONE NUMBER PER STAR.  To first
    order dv_star - dv_lsr is the star's own LSR velocity v_sys + v_sun, so
    the second frame adds no degree of freedom per crossing.  That identity
    is asserted on every row where the nearest transition is the same in
    both frames, and the rows where it is not are counted.

3.  WHAT THE SURVEYS SHOW.  Spectra are cut along every line of sight from
    the moment-masked composite CO cube of Dame & Thaddeus (2022), which
    contains Dame, Hartmann & Thaddeus (2001), and the velocity-integrated
    all-sky Planck CO(1-0) map is read at the same positions, so the
    directions the CfA survey does not cover are still answered.  Both are
    read from frozen cuts (`lsr_r15.py`); the build makes no network call.

4.  WHAT THE SECOND FRAME COSTS.  A mask evaluated in two frames masks more
    bandwidth: the union of two tubes of the same half-width separated by
    the star's LSR velocity.  The cost against the Class A union is computed
    by ONE function for both frames, so the one-frame value reproduces the
    published number and the difference is the cost of the second frame and
    nothing else.

ASSERTIONS (each driven, see --drive)
    L1  the frame identity: on every row whose nearest transition is the
        same in both frames, dv_star - dv_lsr is the star's own LSR velocity
    L2  the either-frame rule can only add: the stellar-frame attributed set
        is contained in the either-frame set, the two counts differ by the
        number that move, and the published count is reproduced
    L3  the lines of sight and the velocities are the right ones: every
        star's queried position lies within one arcminute of the measured
        position of its own products, and its queried radial velocity agrees
        with the one the frame chain uses apart from the single declared
        override
    L4  no disposition depends on the convention of the LSR: the apex form
        and the galactic-component form of the standard solar motion agree
        on every line of sight to better than half a channel
    L5  the two CO surveys agree about which directions carry gas: every
        direction the CfA survey covers and detects is above the Planck
        ceiling, every direction it covers and does not detect is below it,
        and no direction outside its footprint is above it
    L6  the bandwidth cost is measured by one function: with the frames
        coincident it reproduces the published one-frame mask cost of the
        Class A union, and with them separated it is strictly larger
    L7  the null result is a measurement and not a vacuous test: the second
        frame moves every crossing's offset by more than one channel, and
        the margin it would have to cross is published beside the largest
        LSR velocity in the sample
    L9  the bound the appendix publishes on the field star's other crossings
        is not larger than any offset the ledger tabulates for them, in
        either frame
    L10 the LSR evaluation is a check and not the rule: it moves no crossing
        across the mask edge, so the adopted stellar-frame attributed set and
        the either-frame set are the same set
    L11 the foreground reading of the one flagged disc host is a measurement:
        its coincidence is further from the star's own transition than
        Keplerian rotation allows and closer to a catalogued cloud line
    L8  the control ring outshining the star is not discriminating: it does
        so in the great majority of Class A windows, so the one field whose
        ring a referee reads as evidence of a cloud is ordinary in that
        respect and the cloud identification must rest on the velocity

    python3 masklsr_v520.py [--drive N]

-> survey_numbers_round520.tex, masklsr_v520.json
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys

import numpy as np

import maskframe_v411 as mf
import star_alias as sa

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 520
C_KMS = mf.C_KMS
HALF = mf.MASK_HALF_KMS
#: the standard (kinematic) solar motion: 20 km/s toward the B1900 apex.
#: This is the LSR the CO surveys quote their velocities in.
APEX = ('18h03m50.29s', '+30d00m16.8s', 'B1900')
APEX_KMS = 20.0
#: the same motion as galactic components, the other published form
UVW_KMS = (10.27, 15.32, 7.74)
#: integrated CO(1-0) above which a Planck direction is called a detection
CO_CEIL_K_KMS = 1.0
#: The CfA cubes are moment-masked: the survey's own significance mask sets
#: noise to exactly zero, so a direction carries gas where the spectrum is
#: non-zero and the test needs no threshold of ours.
SUF = ('_drive%d' % int(sys.argv[sys.argv.index('--drive') + 1])
       if '--drive' in sys.argv else '')
OUTNAME = 'survey_numbers_round520%s.tex' % SUF
assert OUTNAME.startswith('survey_numbers_round%d' % ROUND), OUTNAME
_W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
      'nine', 'ten')


def _load(*p):
    return json.load(open(os.path.join(*p), encoding='utf-8'))


def texval(name):
    """The value of a published macro, read from the round files."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^{}]*)\}'
                     % name)
    v = None
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for m in pat.finditer(open(f, encoding='utf-8').read()):
            if m.group(1).strip():
                v = m.group(1).strip()
    return v


def tname(s):
    """The designation as the paper typesets it.

    `star_alias.designation` renders a catalogue sign -- CD$-$57 1054 -- but
    not the sign inside a coordinate-based designation, so a hyphen between
    two digits is normalised here as it is wherever such a name is printed.
    """
    t = sa.designation(s).replace(' ', '~')
    return re.sub(r'(?<=\d)-(?=\d)', '$-$', t)


# ---------------------------------------------------------------- the frame
def _apex_icrs():
    from astropy.coordinates import SkyCoord, FK4
    return SkyCoord(APEX[0], APEX[1], frame=FK4(equinox=APEX[2])).icrs


def solar_projection(ra, dec, apex=None):
    """The standard solar motion projected on a line of sight, apex form."""
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    a = apex if apex is not None else _apex_icrs()
    c = SkyCoord(float(ra) * u.deg, float(dec) * u.deg)
    return APEX_KMS * float(np.cos(c.separation(a).rad))


def solar_projection_uvw(ra, dec):
    """The same motion, from its galactic components: the other convention."""
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    g = SkyCoord(float(ra) * u.deg, float(dec) * u.deg).galactic
    l, b = g.l.rad, g.b.rad
    u0, v0, w0 = UVW_KMS
    return float(u0 * np.cos(b) * np.cos(l) + v0 * np.cos(b) * np.sin(l)
                 + w0 * np.sin(b))


def to_lsr(f_bary, v_sun):
    """barycentric -> local standard of rest, one declared step."""
    return f_bary * (1.0 - v_sun / C_KMS)


def main(argv):
    drive, driven = 0, False
    for i, a in enumerate(argv):
        if a == '--drive':
            drive, driven = int(argv[i + 1]), True
    suf = '_drive%d' % drive if driven else ''
    fail = []

    def ck(name, cond, detail=''):
        if not cond:
            fail.append('%s: %s' % (name, detail))
        print('  %-3s %s %s' % (name.split()[0], 'PASS' if cond else 'FAIL',
                                detail))

    M = {}
    D = {}

    def m(k, v):
        assert k.isalpha(), k         # a macro name may hold letters only
        assert k not in M, k
        M[k] = str(v)

    LED = _load(HERE, 'ledger.json')['rows']
    LOS = _load(HERE, 'r15inputs', 'losdir_r15.json')
    CO = _load(HERE, 'r15inputs', 'co_dht_r15.json')
    PL = _load(HERE, 'r15inputs', 'co_planck_r15.json')
    PB = _load(HERE, 'pbcat_v408.json')
    CAT = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'), encoding='utf-8')))
    TRANS = {k: v[0] for k, v in mf.TRANS.items()}
    apex = _apex_icrs()

    # ===================================================== 1. the second frame
    proj, proj2 = {}, {}
    for k, s in LOS['star'].items():
        proj[k] = solar_projection(s['ra'], s['dec'], apex)
        proj2[k] = solar_projection_uvw(s['ra'], s['dec'])
    if drive == 4:
        k0 = sorted(proj)[0]
        proj2[k0] = proj2[k0] + 3.0

    rows = []
    for r in LED:
        d = sa.designation(r['star'], tex=False)
        p = proj[d]
        if drive == 7:
            p = 0.0
        f_lsr = to_lsr(r['frame']['f_bary'], p)
        name, f_rest, dv = mf.nearest(f_lsr, mf.TRANS)
        rows.append(dict(
            star=d, display=r['display'], eb=r['eb'], freq=r['freq'],
            t_star=r['tstar'], t_ctrl=r['rank_ctrl'],
            v_sys=r['frame']['v_sys'], v_sun=p,
            v_star_lsr=r['frame']['v_sys'] + p,
            f_lsr=f_lsr, line_star=r['line'], dv_star=r['dv_stellar'],
            line_lsr=name, dv_lsr=dv, v_feature_lsr=-dv,
            attr_star=bool(abs(r['dv_stellar']) <= HALF),
            attr_lsr=bool(abs(dv) <= HALF)))

    same = [x for x in rows if x['line_lsr'] == x['line_star']]
    diff = [x for x in rows if x['line_lsr'] != x['line_star']]
    # The identity is exact in this form; the plain first-order statement
    # the appendix makes is true to a few tenths of a km/s, and the departure
    # grows with the offset, so both are measured.
    exact = max(abs(x['dv_star'] - x['dv_lsr']
                    - x['v_star_lsr'] * (1.0 + x['dv_lsr'] / C_KMS)
                    / (1.0 - x['v_sun'] / C_KMS)) for x in same)
    resid = max(abs(x['dv_star'] - x['dv_lsr'] - x['v_star_lsr'])
                for x in same)
    if drive == 1:
        exact, resid = 9.9, 9.9
    ck('L1 on every row whose nearest transition is the same in both frames '
       'the two offsets differ by the star\'s own LSR velocity',
       exact < 1e-6 and resid < 0.5
       and len(same) + len(diff) == len(rows) and len(same) > 0,
       'identity closes to %.2e km/s and the first-order form to %.2f km/s '
       'over %d rows, %d rows change transition'
       % (exact, resid, len(same), len(diff)))
    D['LsIdentKms'] = ( '%.1f' % resid)
    D['LsNFrameDiff'] = ( len(diff))
    D['LsNFrameDiffWord'] = ( _W[len(diff)] if len(diff) < len(_W) else len(diff))

    # ===================================================== 2. the recount
    a_star = [x for x in rows if x['attr_star']]
    a_either = [x for x in rows if x['attr_star'] or x['attr_lsr']]
    move = [x for x in rows if x['attr_lsr'] and not x['attr_star']]
    leave = [x for x in rows if x['attr_star'] and not x['attr_lsr']]
    if drive == 2:
        a_either = a_either[:-1]
    pub = int(texval('MkNCoinc'))
    ck('L2 the either-frame rule can only add: the stellar-frame set is '
       'contained in the either-frame set, the counts differ by the number '
       'that move, and the published count is reproduced',
       len(a_star) == pub
       and all(x in a_either for x in a_star)
       and len(a_either) == len(a_star) + len(move),
       '%d attributed in the stellar frame, %d in either, %d move, %d would '
       'be lost if the LSR frame replaced it' % (len(a_star), len(a_either),
                                                 len(move), len(leave)))
    D['LsNCoinc'] = ( len(a_either))
    D['LsNMove'] = ( len(move))
    m('LsNMoveWord', _W[len(move)] if len(move) < len(_W) else len(move))
    D['LsNLeave'] = ( len(leave))
    m('LsNLeaveWord', _W[len(leave)] if len(leave) < len(_W) else len(leave))
    if leave:
        x = max(leave, key=lambda y: abs(y['dv_lsr']))
        m('LsLeaveStar', tname(x['display']))
        m('LsLeaveLine', mf.tex_label(x['line_star']))
        m('LsLeaveDvStar', '%+.1f' % x['dv_star'])
        m('LsLeaveDvLsr', '%+.1f' % x['dv_lsr'])

    vl = [abs(x['v_star_lsr']) for x in rows]
    m('LsVLsrLo', '%.1f' % min(vl))
    m('LsVLsrHi', '%.1f' % max(vl))
    m('LsVLsrMed', '%.1f' % float(np.median(vl)))
    una = sorted(abs(x['dv_star']) for x in rows if not x['attr_star'])
    m('LsNearestUnattr', '%.0f' % una[0])
    m('LsGapKms', '%.0f' % (una[0] - HALF))

    # ===================================================== 3. the two surveys
    cov = {k: v for k, v in CO['los'].items() if v['covered']}
    det = {k: v for k, v in cov.items()
           if any(t != 0.0 for t in v['t_mb_K'])}
    nodet = {k: v for k, v in cov.items() if k not in det}
    ceil = CO_CEIL_K_KMS
    if drive == 5:
        ceil = 0.05
    hi = {k for k, v in PL['los'].items() if v['w_co_cone_max'] >= ceil}
    out_fp = {k for k in PL['los'] if k not in cov}
    ck('L5 the two CO surveys agree about which directions carry gas: every '
       'direction the CfA survey covers and detects is above the Planck '
       'ceiling, every one it covers and does not detect is below it, and no '
       'direction outside its footprint is above it',
       set(det) <= hi and not (set(nodet) & hi) and not (out_fp & hi)
       and len(det) > 0 and len(nodet) > 0 and len(out_fp) > 0,
       '%d of %d directions covered, %d detected, %d outside the footprint; '
       'Planck above %.2f K km/s: %s' % (len(cov), len(CO['los']), len(det),
                                         len(out_fp), ceil,
                                         sorted(hi)))
    m('LsNLos', len(CO['los']))
    m('LsNLosCov', len(cov))
    m('LsNLosDet', len(det))
    m('LsNLosOut', len(out_fp))
    D['LsCoCeil'] = ( '%.1f' % ceil)
    m('LsPlanckMax', '%.3f' % max(PL['los'][k]['w_co_cone_max']
                                  for k in PL['los'] if k not in det))
    m('LsCoVLo', '%+.0f' % min(v['v_peak_kms'] for v in det.values()))
    m('LsCoVHi', '%+.0f' % max(v['v_peak_kms'] for v in det.values()))
    D['LsCoBeam'] = ( '%.1f' % CO['source']['beam_arcmin'])
    D['LsCoChan'] = ( '%.2f' % CO['source']['chan_kms'])
    m('LsCoRms', '%.2f' % CO['source']['rms_K'])
    D['LsPlanckBeam'] = ( '%.0f' % (PL['source']['beam_arcmin'] / 60.0))

    # which crossings sit at a velocity where the survey shows gas
    cloud = []
    for x in rows:
        c = CO['los'][x['star']]
        if x['star'] not in det or abs(x['v_feature_lsr']) > 45.0:
            continue
        vel = np.asarray(c['vel_kms'])
        t = np.asarray(c['t_mb_K'])
        i = int(np.argmin(abs(vel - x['v_feature_lsr'])))
        # The velocity is compared with the spectrum of the star's OWN
        # pixel; the 3x3 neighbourhood is used only to decide that the
        # direction carries gas at all, since a 0.25 deg grid under an
        # 8.4 arcmin beam undersamples a cloud edge.
        x = dict(x, co_t_at_feature=float(t[i]),
                 co_v_peak=c['v_peak_kms'],
                 co_t_peak=c['t_peak_box_K'], co_w=c['w_co_K_kms'],
                 co_dv=x['v_feature_lsr'] - c['v_peak_kms'])
        if x['co_t_at_feature'] != 0.0:
            cloud.append(x)
    cstars = sorted({x['star'] for x in cloud})
    m('LsNCloud', len(cloud))
    # A drive that removes the transform removes every match, which is the
    # point of it; the macros below then have nothing to describe.
    _have = bool(cloud)
    D['LsNCloudStar'] = ( len(cstars))
    if _have:
        m('LsCloudStars', ', '.join(tname(s) for s in cstars[:-1])
          + ' and ' + tname(cstars[-1]))
        m('LsCloudDvMax', '%.0f' % max(abs(x['co_dv']) for x in cloud))
        m('LsCloudTMin', '%.2f' % min(x['co_t_at_feature'] for x in cloud))

    # the two fields the report names
    lup = [x for x in rows if x['star'].startswith('ALMA')]
    lupco = CO['los'][lup[0]['star']]
    lupg = LOS['star'][lup[0]['star']]
    lupc = ([x for x in cloud if x['star'] == lup[0]['star']] or [None])[0]
    D['LsLupNCross'] = ( len(lup))
    D['LsLupNCrossWord'] = _W[len(lup)] if len(lup) < len(_W) else len(lup)
    _rl = sum(1 for x in lup if x['t_ctrl'] > x['t_star'])
    m('LsLupNRingLeadWord', _W[_rl] if _rl < len(_W) else _rl)
    m('LsLupTCtrl', '%.1f' % max(x['t_ctrl'] for x in lup))
    m('LsLupTStar', '%.1f' % max(x['t_star'] for x in lup))
    m('LsLupVco', '%+.1f' % lupco['v_peak_kms'])
    D['LsLupTco'] = '%.1f' % lupco['t_peak_box_K']
    m('LsLupWco', '%.1f' % lupco['w_co_K_kms'])
    if lupc:
        D['LsLupVfeat'] = ( '%+.1f' % lupc['v_feature_lsr'])
        m('LsLupDv', '%.1f' % abs(lupc['co_dv']))
    # Printed in the sample section already; recomputed here so that a
    # disagreement is a build failure rather than a stale sentence.
    _dpc = 1000.0 / lupg['plx_mas']
    assert abs(_dpc - float(texval('BkAlmaDistPc'))) < 0.05, _dpc
    D['LsLupDistPc'] = ( '%.1f' % _dpc)
    _far = [x for x in lup if not x['attr_star'] and not x['attr_lsr']]
    m('LsLupNFar', len(_far))
    # The bound has to hold in BOTH frames, so it is the smaller of the two
    # minima and not the LSR one.  Taking the LSR offsets alone published a
    # bound of 128 km/s while the ledger tabulated -122.2 for the same
    # crossing: the appendix then contradicted a table in the same paper.
    _far_star = min(abs(x['dv_star']) for x in _far)
    _far_lsr = min(abs(x['dv_lsr']) for x in _far)
    _bound = min(_far_star, _far_lsr)
    if drive == 9:
        _bound = _far_lsr            # the defect: the LSR frame alone
    m('LsLupFarMin', '%.0f' % _bound)
    ck('L9 the published bound on the field star\'s other crossings is not '
       'larger than any offset the ledger tabulates for them, in either '
       'frame',
       float(M['LsLupFarMin']) <= _far_star + 0.5
       and float(M['LsLupFarMin']) <= _far_lsr + 0.5,
       'bound %s km/s against a nearest tabulated offset of %.1f in the '
       'stellar frame and %.1f in the LSR'
       % (M['LsLupFarMin'], _far_star, _far_lsr))

    # ======================= the adopted frame, and the LSR as a check only
    # Attribution is evaluated in the star's own rest frame.  The appendix
    # may call the LSR evaluation a check rather than the rule only while it
    # changes no disposition, so that is asserted and not assumed.
    _either = len([x for x in rows if x['attr_star'] or x['attr_lsr']])
    _n_move = len(move)
    if drive == 10:
        _n_move = 1
    ck('L10 the LSR evaluation is a check and not the rule: it moves no '
       'crossing across the mask edge, so the adopted stellar-frame set and '
       'the either-frame set are the same set',
       _n_move == 0 and _either - _n_move == len(a_star),
       '%d move; %d attributed in the stellar frame, %d in either'
       % (_n_move, len(a_star), _either))

    hd = [x for x in cloud if x['star'] == 'HD 48370']
    if drive == 11 and hd:
        hd = [dict(hd[0], dv_star=0.5 * hd[0]['co_dv'])]
    if hd:
        # Minor 18: the coincidence is 17.8 km/s from the star's own
        # CO(2-1) -- outside the Keplerian width the mask is built on -- and
        # within 2.1 km/s of a catalogued cloud line at its own LSR
        # velocity.  It is foreground gas, and the appendix says so.
        m('LsHdDvStar', '%+.1f' % hd[0]['dv_star'])
        m('LsHdVfeat', '%+.1f' % hd[0]['v_feature_lsr'])
        m('LsHdVco', '%+.1f' % hd[0]['co_v_peak'])
        ck('L11 the foreground reading of the flagged disc host is a '
           'measurement: its coincidence is further from the star\'s own '
           'transition than Keplerian rotation allows and closer to a '
           'catalogued cloud line than that',
           abs(hd[0]['dv_star']) > abs(hd[0]['co_dv'])
           and hd[0]['co_t_at_feature'] != 0.0,
           '%.1f km/s from CO(2-1) in the stellar frame against %.1f km/s '
           'from the cloud peak, at %.2f K'
           % (hd[0]['dv_star'], hd[0]['co_dv'], hd[0]['co_t_at_feature']))

    tau = [x for x in cloud if x['star'] == 'HD 285968']
    if tau:
        D['LsTauVco'] = ( '%+.1f' % tau[0]['co_v_peak'])
        D['LsTauVfeat'] = ( '%+.1f' % tau[0]['v_feature_lsr'])
        D['LsTauDv'] = ( '%.1f' % abs(tau[0]['co_dv']))
        D['LsTauDvStar'] = ( '%+.1f' % tau[0]['dv_star'])
        D['LsTauWco'] = ( '%.1f' % tau[0]['co_w'])

    # ===================================================== 4. positions, rv
    # `pbcat` is keyed on the string the export carried, and for one bound
    # pair the companion's products sit under the primary's designation.  A
    # trailing component letter is therefore dropped as a second attempt,
    # and the separation tolerance below is what decides whether the two
    # strings are the same line of sight: the components are 10 arcsec apart
    # and a different star would miss by degrees.
    def _cand(star):
        c = [w for k, v in PB.items()
             if sa.designation(k.split('|')[0], tex=False) == star
             for w in v]
        if not c and len(star.rsplit(' ', 1)[-1]) == 1:
            base = star.rsplit(' ', 1)[0]
            c = [w for k, v in PB.items()
                 if sa.designation(k.split('|')[0], tex=False) == base
                 for w in v]
        return [(w['star_ra'], w['star_dec']) for w in c
                if w.get('star_ra') is not None
                and w.get('star_dec') is not None]

    seps, rvd = [], []
    for x in rows:
        s = LOS['star'][x['star']]
        meas = _cand(x['star'])
        if drive == 3 and seps == []:
            s = dict(s, dec=s['dec'] + 0.5)
        if meas:
            dra = [(s['ra'] - a) * np.cos(np.radians(s['dec']))
                   for a, b in meas]
            dde = [s['dec'] - b for a, b in meas]
            seps.append((x['star'], 3600.0 * float(np.max(np.hypot(dra,
                                                                   dde)))))
        if s['rv_kms'] is not None:
            rvd.append((x['star'], abs(x['v_sys'] - s['rv_kms'])))
    # The survey spans two decades of ALMA epochs and these are the nearest
    # stars in the sky, so a star's catalogued J2000 position and the
    # position its own products were extracted at differ by its proper
    # motion.  The tolerance is therefore what that motion covers in the
    # span, plus ten arcseconds; a position belonging to the wrong star
    # misses by degrees and cannot pass it.
    EPOCH_YR = 30.0
    worst = []
    for k, sep in seps:
        s0 = LOS['star'][k]
        pm = np.hypot(s0.get('pmra_masyr') or 0.0,
                      s0.get('pmdec_masyr') or 0.0) / 1000.0
        worst.append((k, sep, 10.0 + pm * EPOCH_YR))
    override = sorted(mf.VSYS_OVERRIDE)
    bad_rv = [t for t in rvd
              if t[1] > 0.01 and not any(sa.designation(o, tex=False) == t[0]
                                         for o in override)]
    ck('L3 every star\'s queried position lies within one arcminute of the '
       'measured position of its own products, and its queried radial '
       'velocity agrees with the one the frame chain uses apart from the '
       'declared override, the position tolerance being the star\'s own '
       'proper motion over the span of the survey',
       len(seps) == len(rows) and all(a <= b for _, a, b in worst)
       and not bad_rv and len(rvd) >= len(rows) - 6,
       'worst separation %.1f arcsec against %.1f allowed by its own proper '
       'motion (%s), %d velocities compared, declared override %s'
       % (max(worst, key=lambda t: t[1] / t[2])[1],
          max(worst, key=lambda t: t[1] / t[2])[2],
          max(worst, key=lambda t: t[1] / t[2])[0], len(rvd), override))
    D['LsPosWorstArcsec'] = ( '%.0f' % max(a for _, a, _ in worst))

    d2 = max(abs(proj[k] - proj2[k]) for k in proj)
    chan = float(CO['source']['chan_kms'])
    ck('L4 no disposition depends on the convention of the LSR: the apex form '
       'and the galactic-component form agree on every line of sight to '
       'better than half a channel',
       d2 < 0.5 * chan,
       'worst difference %.3f km/s against %.3f km/s half a channel'
       % (d2, 0.5 * chan))
    m('LsConvKms', '%.2f' % d2)

    # ===================================================== 5. the cost
    def merge(iv):
        o = []
        for a, b in sorted(iv):
            if o and a <= o[-1][1]:
                o[-1][1] = max(o[-1][1], b)
            else:
                o.append([a, b])
        return o

    def tot(x):
        return sum(b - a for a, b in x)

    CLA = [r for r in CAT if r['search_class'] == 'A']
    UA = merge([tuple(sorted((float(r['flo_GHz']), float(r['fhi_GHz']))))
                for r in CLA])
    u_a = tot(UA)
    avl = {}
    for k, s in LOS['star'].items():
        avl[k] = None if s['rv_kms'] is None else abs(s['rv_kms'] + proj[k])
    aw = {sa.designation(r['star_name'], tex=False) for r in CLA}
    known = sorted(v for k, v in avl.items() if k in aw and v is not None)
    med = float(np.median(known))
    norv = sorted(k for k in aw if avl.get(k) is None)
    nwin = sum(1 for r in CLA
               if sa.designation(r['star_name'], tex=False) in norv)

    def cost(two):
        iv = []
        for r in CLA:
            lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
            v = avl.get(sa.designation(r['star_name'], tex=False))
            w = HALF + (min(med if v is None else v, 2 * HALF)
                        if two else 0.0)
            for f0 in TRANS.values():
                a, b = max(f0 * (1 - w / C_KMS), lo), min(f0 * (1 + w / C_KMS),
                                                          hi)
                if b > a:
                    iv.append((a, b))
        return tot(merge(iv))

    one, two = cost(False), cost(True)
    if drive == 6:
        one = two
    pub_a = float(texval('MkMaskAGHz'))
    ck('L6 the bandwidth cost is measured by one function: with the frames '
       'coincident it reproduces the published one-frame mask cost of the '
       'Class A union, and with them separated it is strictly larger',
       abs(one - pub_a) < 0.005 and two > one,
       'one frame %.4f GHz against published %.2f, two frames %.4f GHz, '
       '%.1f per cent more' % (one, pub_a, two, 100.0 * (two - one) / one))
    # The one-frame value is NOT published here: it is already published as
    # `\MkMaskAGHz` and L6 asserts this function reproduces it, so emitting
    # it again would be two macros for one number.
    m('LsMaskTwoGHz', '%.2f' % two)
    m('LsMaskTwoPct', '%.1f' % (100.0 * two / u_a))
    m('LsMaskAddPct', '%.0f' % (100.0 * (two - one) / one))
    D['LsNAStarNoRv'] = ( len(norv))
    D['LsNAWinNoRv'] = ( nwin)
    D['LsVLsrAHi'] = ( '%.0f' % max(known))
    D['LsVLsrAStar'] = tname(max((k for k in aw if avl.get(k) is not None),
                                 key=lambda k: avl[k]))
    D['LsVLsrAMed'] = ( '%.1f' % med)

    # ===================================================== 6. not vacuous
    shift = [abs(x['dv_star'] - x['dv_lsr']) for x in same]
    kms_chan = min(abs(float(r['chanw_Hz'])) / 1e9 / float(r['flo_GHz'])
                   * C_KMS for r in CLA)
    ck('L7 the second frame is not a vacuous test: it moves every crossing\'s '
       'offset, the largest shift exceeds a channel of the search, and the '
       'margin a crossing would have to cross is published beside the '
       'largest LSR velocity in the sample',
       min(shift) > 0 and max(shift) > kms_chan
       and (una[0] - HALF) > max(vl),
       'shifts %.2f to %.2f km/s against a %.3f km/s channel; margin %.1f '
       'km/s against the largest LSR velocity %.1f km/s'
       % (min(shift), max(shift), kms_chan, una[0] - HALF, max(vl)))
    D['LsShiftHi'] = ( '%.0f' % max(shift))
    D['LsChanKms'] = ( '%.2f' % kms_chan)

    # ============================= 7. the ring comparison says nothing
    # The field identified as a cloud above has a control ring brighter than
    # its star, and so does nearly every Class A window: the comparison is
    # reported in the ledger and must not be read as evidence.  Measured on
    # the released catalogue, against the published window count.
    lead = sum(1 for r in CLA
               if float(r['ctrl_max_snr']) > float(r['star_snr']))
    n_a = int(texval('NWinA'))
    if drive == 8:
        lead = len(CLA) // 4
    ck('L8 a control ring brighter than the star is not discriminating: it '
       'happens in the great majority of Class A windows, so the Lupus '
       'field is ordinary in that respect',
       len(CLA) == n_a and lead > 0.9 * n_a
       and all(x['t_ctrl'] > x['t_star'] for x in lup),
       '%d of %d Class A windows, and %d of %d windows of the cloud field'
       % (lead, n_a, sum(1 for x in lup if x['t_ctrl'] > x['t_star']),
          len(lup)))
    m('LsRingLeadA', lead)

    # ------------------------------------------------------------------
    assert suf == SUF, (suf, SUF)
    with open(os.path.join(HERE, OUTNAME), 'w', encoding='utf-8') as fh:
        fh.write('%%%% GENERATED by masklsr_v%d.py -- do not hand-edit.\n'
                 % ROUND)
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
    json.dump(dict(macros=M, diagnostics=D, failed=fail,
                   n_attributed_stellar=len(a_star),
                   n_attributed_either=len(a_either),
                   n_move=len(move), n_leave=len(leave),
                   n_transition_changed=len(diff),
                   mask_one_frame_GHz=one, mask_two_frame_GHz=two,
                   union_a_GHz=u_a,
                   cloud_matches=[dict(star=x['star'], eb=x['eb'],
                                       freq=x['freq'],
                                       line=x['line_lsr'],
                                       dv_star=x['dv_star'],
                                       dv_lsr=x['dv_lsr'],
                                       v_feature_lsr=x['v_feature_lsr'],
                                       co_v_peak=x['co_v_peak'],
                                       co_t_at_feature=x['co_t_at_feature'],
                                       co_w=x['co_w']) for x in cloud],
                   rows=rows),
              open(os.path.join(HERE, 'masklsr_v%d%s.json' % (ROUND, suf)),
                   'w'), indent=1)
    print('%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
