#!/usr/bin/env python3
r"""pairs_v415.py -- the cross-block pair test: can two threshold crossings
within the wide recurrence window be one carrier on one trajectory?

Round 420.  Writes `survey_numbers_round420.tex`, `tab_pairs_v415.tex` and
`pairs_v415.json`.

WHY THIS EXISTS.  The confirmation criterion as the paper states it is met at
the predicted stellar-frame channel OR anywhere within the widened window at
any drift, in another block.  Read literally that is satisfied by the
exceedances the widened window holds, and those exceedances were set aside
because they are themselves crossings the ledger lists -- which is circular,
because a carrier that recurred would appear in the repeat block as a
crossing.  The population count (28 found against 28 predicted) is a
statement about the set and not about any pair.  So the per-pair question has
to be asked, and it is asked here.

THE QUESTION.  Two crossings toward one star, in two blocks, separated by
Delta_nu in the star's own frame and Delta_t in time, each with its own
independently fitted drift nudot_1 and nudot_2.  Is there one trajectory
nu(t) with nu(0), nu(Delta_t) and both drifts as measured?

TWO ANSWERS, AND THE SECOND IS THE ONE THAT MATTERS.

 1. CONSTANT LINE-OF-SIGHT ACCELERATION.  nudot is then linear in t and the
    offset is fixed with no freedom at all:

        Delta_nu = (nudot_1 + nudot_2) * Delta_t / 2

    which a reader can evaluate from three columns of the table.  The
    residual is quoted two ways: in MHz, and as the error the two fitted
    drifts would both have to carry to absorb it.  That second form is what
    makes the test self-calibrating, because a drift wrong by that much
    smears the carrier across many channels of its own dwell and the
    crossing could not have been detected at all.

 2. ANY BOUNDED TRAJECTORY.  Relax to every nu(t) whose drift stays inside
    the grid the window was searched over and whose curvature is bounded.
    The reachable set of Delta_nu is computed exactly -- the extreme profile
    is the pointwise envelope of the three constraints -- and the smallest
    curvature that reaches the observed offset is found by bisection.  That
    curvature is reported as the time in which the line-of-sight acceleration
    would have to cross the whole range the search covers, and compared with
    the quarter period of the fastest orbit that same acceleration ceiling
    allows.  Where the required reversal is faster, the pair is excluded;
    where it is slower, THE TEST HAS NO POWER AND THE PAPER MUST SAY SO.

THE JOIN IS ON POSITION.  Two spellings of HD 14055 occur in the ledger and
the archival-tail crossings carry no catalogue row at all, so pairing on the
star name would both merge and split the wrong rows.  Pairs are formed on the
discovery products' own `t1_ra`/`t1_dec` and the name is carried only for
printing; the number of distinct positions is asserted against the number of
distinct systems the ledger names, with the two spellings counted once.

R2-2 IS ANSWERED HERE TOO.  The published exclusions combine one predicted
channel over every covering block by inverse variance, which assumes the
carrier returns to that channel at the start of each of them.  The same
quantity is therefore computed from the NEAREST SINGLE repeat block, which
assumes nothing beyond the two observations, and both are published so a
reader can see what the combination buys.

Usage: pairs_v415.py [--drive N]
"""
import csv
import itertools
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 420
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round420%s.tex' % SFX)
OUTT = os.path.join(HERE, 'tab_pairs_v415%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'pairs_v415%s.json' % SFX)

CKMS = 299792.458
C = CKMS * 1e3
GMSUN = 1.32712440018e20
MSUN_MAX = 2.0                 # the bound the widened window is built on
TRIG = 5.0
POS_TOL = 2.0                  # arcsec; one ALMA beam is larger than this

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-66s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def tname(s):
    """The star as the paper sets it."""
    s = s.split(' Gaia')[0].strip()
    s = s.replace('HD14055', 'HD 14055').replace('bet Pic', r'$\beta$ Pic')
    s = s.replace('eta Crv', r'$\eta$ Crv').replace('BD05', 'BD+05')
    return s.replace(' ', '~').replace('-', '$-$')


# ---------------------------------------------------------------- inputs
LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
REC = json.load(open(os.path.join(HERE, 'r10inputs',
                                  'recur_v411.json')))['crossings']
RCOL = json.load(open(os.path.join(HERE, 'recurcols_v411.json')))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
# ★★★ THE DRIFTS ARE FITTED TOPOCENTRICALLY AND THE OFFSET IS STELLAR-FRAME,
# so the extrapolation below has to be done in one frame.  A topocentric
# drift carries the observatory's own line-of-sight acceleration, which here
# is dominated by the Earth's rotation: it oscillates with a period of a day
# rather than accumulating, so carrying it linearly across days adds a term
# that is not there.  `a_bary` is the frozen input that removes it, measured
# per block at that block's own pointing and mid-time and validated against
# the survey's own frozen v_bary (see `make_abary_v417.py`).
ABARY = json.load(open(os.path.join(HERE, 'r16inputs',
                                    'abary_v417.json')))['blocks']

WINOF = {}
for _r in CAT:
    WINOF.setdefault(_r['eb'], []).append(_r)


def window(eb, f):
    for r in WINOF.get(eb, []):
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if lo <= f <= hi:
            return r
    return None


LK = {(r['eb'], round(float(r['freq']), 6)): r for r in LED}

# ★★ THE CONTROL.  The one set of crossings in this survey that IS present
# again is a molecular line, and a test that cannot return "one trajectory"
# for it is not a test.  Those rows carry no recurrence record of their own --
# they are attributed, so the recurrence campaign never covered them -- so
# their drift comes from the frozen per-crossing fits and their epoch from the
# measurement sets read by the hold-out campaign.  Block epochs are taken
# ONLY from a measurement set: the archive's own per-block stamp is unusable
# for intervals, as the ledger-error generator demonstrates.
L403 = {}
for _r in json.load(open(os.path.join(HERE, 'ledger_v403.json')))['rows']:
    if _r.get('freq') is not None:
        L403[(_r['eb'], round(float(_r['freq']), 6))] = _r
MSTIME = {}
for _src in (os.path.join(HERE, 'r10inputs', 'recur_v411.json'),
             os.path.join(HERE, 'r11inputs', 'events', 'recur_holdout.json')):
    for _v in json.load(open(_src))['crossings'].values():
        for _b in [(_v.get('discovery') or {})] + list(_v.get('blocks') or []):
            if _b.get('t_start_mjdsec'):
                MSTIME.setdefault(_v['eb'] if _b is (_v.get('discovery') or {})
                                  else _b['eb'], set()).add(
                                      round(_b['t_start_mjdsec'], 3))
ck('P0 no execution block is read with two different start times',
   all(len(v) == 1 for v in MSTIME.values()),
   '%d blocks, %d with more than one' % (len(MSTIME),
                                         sum(1 for v in MSTIME.values()
                                             if len(v) > 1)))
MSTIME = {k: min(v) for k, v in MSTIME.items()}

# ------------------------------------------- the crossings the test runs on
ROWS, NODRIFT = [], []
for cid, v in sorted(REC.items()):
    d = v.get('discovery') or {}
    lk = LK[(v['eb'], round(float(v['freq_GHz']), 6))]
    if not d.get('drift_Hz_s') or not d.get('t_start_mjdsec'):
        NODRIFT.append((cid, v['star'], v['status']))
        continue
    w = window(v['eb'], float(v['freq_GHz']))
    dwell = d['t_end_mjdsec'] - d['t_start_mjdsec']
    chanw = float(w['chanw_Hz']) if w else float(d['chanw_Hz'])
    # ★ The drift resolution is the grid the window was actually searched on.
    # Where the catalogue carries the grid it is used; the two tail windows
    # are not in the catalogue, and for them the grid step follows from the
    # rule the catalogue's own grids obey -- one half channel across the
    # dwell -- which is checked below against every window that has both.
    if w and w['n_drift_trials']:
        step = 2.0 * float(w['drift_max_Hz_s']) / (int(w['n_drift_trials']) - 1)
        dmax = float(w['drift_max_Hz_s'])
        src = 'catalogue grid'
    else:
        step = chanw / (2.0 * dwell)
        dmax = AG_PLACEHOLDER = None
        src = 'half a channel across the dwell'
    ROWS.append(dict(
        cid=cid, star=v['star'], eb=v['eb'], ra=d['ra'], dec=d['dec'],
        ftopo=float(v['freq_GHz']), fstar=lk['frame']['f_stellar'],
        drift=d['drift_Hz_s'], t0=d['t_start_mjdsec'], dwell=dwell,
        tstar=float(v['tstar']), attr=bool(lk['attributed']),
        chanw=chanw, step=step, dmax=dmax, step_src=src,
        vsys=float(lk['frame']['v_sys']), ntrial=(
            int(w['n_drift_trials']) if w and w['n_drift_trials'] else None),
        sysid=(w['system_id'] if w else None)))

# the attributed crossings that can carry the same test: a fitted drift from
# the frozen records and an epoch from a measurement set.
RECK = {(v['eb'], round(float(v['freq_GHz']), 6)) for v in REC.values()}
NCTRLROW = 0
for r in LED:
    k = (r['eb'], round(float(r['freq']), 6))
    if k in RECK:
        continue
    l4 = L403.get(k)
    if not l4 or l4.get('drift_Hz_s') is None or l4.get('t_span_s') is None:
        continue
    if r['eb'] not in MSTIME:
        continue
    w = window(r['eb'], float(r['freq']))
    if not w or not w['n_drift_trials']:
        continue
    ROWS.append(dict(
        cid='C%02d' % (NCTRLROW + 1), star=r['star'], eb=r['eb'],
        ra=None, dec=None, sysid=w['system_id'],
        ftopo=float(r['freq']), fstar=r['frame']['f_stellar'],
        drift=l4['drift_Hz_s'], t0=MSTIME[r['eb']], dwell=l4['t_span_s'],
        tstar=float(r['tstar']), attr=True, chanw=float(w['chanw_Hz']),
        step=2.0 * float(w['drift_max_Hz_s'])
        / (int(w['n_drift_trials']) - 1),
        dmax=float(w['drift_max_Hz_s']), step_src='catalogue grid',
        vsys=float(r['frame']['v_sys']), ntrial=int(w['n_drift_trials']),
        starkey=r['star']))
    NCTRLROW += 1

# the acceleration ceiling is one number for the whole survey
AGRID = sorted({round(float(r['a_max_m_s2']), 3) for r in CAT
                if r['a_max_m_s2']})
AG = AGRID[0]
for r in ROWS:
    if r['dmax'] is None:
        r['dmax'] = AG * r['ftopo'] * 1e9 / C

# ----------------------------------------- the drifts, in the star's frame
# nu_star = nu_topo (1 + v_sys/c)(1 - v_bary/c), so
#   nudot_star = nudot_topo (1 + v_sys/c)(1 - v_bary/c)
#                - nu_topo (1 + v_sys/c) a_bary / c.
# The second term is the observatory's own line-of-sight acceleration.  It is
# at most a few tens of Hz s^-1 here against fitted drifts of hundreds to
# thousands, but it is diurnal: it does not accumulate over days, and the
# extrapolation below runs over days.  Keyed on the execution block.
_missing = sorted({r['eb'] for r in ROWS if r['eb'] not in ABARY})
for r in ROWS:
    ab = ABARY.get(r['eb'])
    r['drift_topo'] = r['drift']
    if ab is None:
        r['drift_star'] = r['drift']
        r['frame_term'] = None
        continue
    kk = (1.0 + r['vsys'] / CKMS) * (1.0 - ab['v_bary_kms'] / CKMS)
    term = (r['ftopo'] * 1e9 * (1.0 + r['vsys'] / CKMS)
            * ab['a_bary_m_s2'] / C)
    if DRIVE == 6:                     # P6: the frame term left out
        kk, term = 1.0, 0.0
    r['drift_star'] = r['drift'] * kk - term
    r['frame_term'] = r['drift_star'] - r['drift']
# ★★★ THE PHYSICAL BOUND THAT MAKES THE FROZEN INPUT CHECKABLE.  The
# observatory's line-of-sight acceleration toward any target cannot exceed
# the equatorial rotation term at ALMA's latitude plus the Earth's orbital
# acceleration.  A wrong site, a wrong ephemeris or a factor of a thousand in
# the units all break this bound, and nothing else in the build would see it.
A_OBS_MAX = (7.292115e-5 ** 2 * 6378137.0 * math.cos(math.radians(23.0229))
             + GMSUN / 1.495978707e11 ** 2)
_ab = [ABARY[r['eb']]['a_bary_m_s2'] for r in ROWS]
ck('P6a the frame term is available for every block the test uses, is the '
   "observatory's own acceleration times nu/c, and that acceleration lies "
   "inside the Earth's rotation at ALMA's latitude plus its orbital "
   'acceleration -- which is the only external bound on this frozen input',
   not _missing and all(r['frame_term'] is not None for r in ROWS)
   and max(abs(a) for a in _ab) <= 1.02 * A_OBS_MAX
   and all(abs(r['frame_term']
               + r['ftopo'] * 1e9 * (1.0 + r['vsys'] / CKMS)
               * ABARY[r['eb']]['a_bary_m_s2'] / C)
           <= 3e-4 * abs(r['drift_topo']) + 1e-9 for r in ROWS)
   and any(abs(r['frame_term']) > 1.0 for r in ROWS),
   '%d blocks without a frame term %s; a_bary %.4f to %.4f m/s2 against a '
   'bound of %.4f; correction %.1f to %.1f Hz/s'
   % (len(_missing), _missing[:3], min(_ab), max(_ab), A_OBS_MAX,
      min(r['frame_term'] for r in ROWS),
      max(r['frame_term'] for r in ROWS)))
for r in ROWS:
    r['drift'] = r['drift_star']

# the Nyquist rule the fallback rests on, measured where both exist
_rat = [(2.0 * float(window(r['eb'], r['ftopo'])['drift_max_Hz_s'])
         / (int(window(r['eb'], r['ftopo'])['n_drift_trials']) - 1))
        / (r['chanw'] / (2.0 * r['dwell']))
        for r in ROWS if r['step_src'] == 'catalogue grid']
_fine = [x for x, r in zip(_rat, [r for r in ROWS
                                  if r['step_src'] == 'catalogue grid'])
         if r['chanw'] < 2e6]
ck('P1 the searched drift grid steps by half a channel across the dwell, so '
   'the two windows outside the catalogue can be given the same resolution',
   abs(sum(_fine) / len(_fine) - 1.0) < (0.05 if DRIVE != 1 else 0.0001),
   'mean ratio %.4f over %d fine windows (%d coarse windows excluded, '
   'ratio to %.2f)' % (sum(_fine) / len(_fine), len(_fine),
                       len(_rat) - len(_fine), max(_rat)))

# ------------------------------------------------------- the identity join
# A crossing is paired with another by POSITION, never by star name: the
# ledger spells one star two ways and the archival-tail crossings carry no
# catalogue row at all, so a name key would both split and merge the wrong
# rows.  The attributed control rows have no measured position of their own,
# so they are placed by the catalogue's system identifier -- and the two keys
# are required to agree, which is what makes the fallback safe.
def sep_arcsec(a, b):
    return 3600.0 * math.hypot((a['ra'] - b['ra'])
                               * math.cos(math.radians(a['dec'])),
                               a['dec'] - b['dec'])


POS = [r for r in ROWS if r['ra'] is not None]
GROUP = []
for r in POS:
    for g in GROUP:
        if sep_arcsec(r, g[0]) <= POS_TOL:
            g.append(r)
            break
    else:
        GROUP.append([r])
SYSOF = {}
for i, g in enumerate(GROUP):
    for r in g:
        if r['sysid']:
            SYSOF.setdefault(r['sysid'], set()).add(i)
ck('P2a no catalogue system identifier spans two measured positions, and no '
   'measured position carries two identifiers',
   all(len(v) == 1 for v in SYSOF.values())
   and all(len({r['sysid'] for r in g if r['sysid']}) <= 1 for g in GROUP)
   if DRIVE != 2 else False,
   '%d positions, %d identifiers, %d identifiers spanning more than one'
   % (len(GROUP), len(SYSOF), sum(1 for v in SYSOF.values() if len(v) > 1)))
for r in ROWS:
    if r['ra'] is not None:
        r['key'] = next(i for i, g in enumerate(GROUP) if r in g)
    else:
        q = SYSOF.get(r['sysid'])
        if q:
            r['key'] = next(iter(q))
        else:
            GROUP.append([r])
            SYSOF[r['sysid']] = {len(GROUP) - 1}
            r['key'] = len(GROUP) - 1
_names = {r['star'].split(' Gaia')[0].replace(' ', '').lower() for r in ROWS}
ck('P2b the join gives one group per star once the spellings are removed, '
   'and the two spellings of one star land in one group',
   len(GROUP) == len(_names),
   '%d groups against %d distinct names (%d raw spellings)'
   % (len(GROUP), len(_names), len({r['star'] for r in ROWS})))

# ================================================================ the test
def macro(name):
    """One macro's value out of the frozen layer, by name."""
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


# The widened window is not redefined here: it is the one the recurrence
# generator measured and the one the figure prints.
HALF_KMS = float(macro('WdHalfKms'))

VORB = (GMSUN * MSUN_MAX * AG) ** 0.25
PORB = 2.0 * math.pi * math.sqrt(GMSUN * MSUN_MAX / AG) / VORB
TAU_ORB = 0.25 * PORB              # the fastest acceleration reversal allowed


def reach(d1, d2, dt, dmax, J, n=4000):
    """The largest and smallest frequency offset a trajectory can produce
    with nudot(0)=d1, nudot(dt)=d2, |nudot|<=dmax and |nuddot|<=J.  The
    extreme drift profile is the pointwise envelope of the three
    constraints, which is itself feasible, so this is exact."""
    if abs(d2 - d1) > J * dt:
        return None
    hi = lo = 0.0
    h = dt / n
    for i in range(n + 1):
        t = i * h
        w = 0.5 if i in (0, n) else 1.0
        hi += w * min(d1 + J * t, dmax, d2 + J * (dt - t)) * h
        lo += w * max(d1 - J * t, -dmax, d2 - J * (dt - t)) * h
    return lo, hi


def min_curvature(d1, d2, dt, df, dmax):
    """The smallest |nuddot| for which one bounded trajectory joins the
    pair.  None if no curvature does, which happens when the offset needs a
    mean drift outside the grid the windows were searched over."""
    top = 1e3
    r = reach(d1, d2, dt, dmax, top)
    if r is None or not r[0] - 1.0 <= df <= r[1] + 1.0:
        return None
    lo, hi = 1e-9, top
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        r = reach(d1, d2, dt, dmax, mid)
        if r is not None and r[0] - 1.0 <= df <= r[1] + 1.0:
            hi = mid
        else:
            lo = mid
    return hi


def build_pairs(dkey):
    """Every pair, under one choice of frame for the fitted drifts.  The test
    is run twice and the verdicts are required to agree, so that the frame
    correction is shown to change nothing rather than assumed to."""
    out = []
    for a, b in itertools.combinations(ROWS, 2):
        out += _one_pair(a, b, dkey)
    out.sort(key=lambda p: p['dt'])
    return out


def _one_pair(a, b, dkey='drift'):
    if a['eb'] == b['eb'] or a['key'] != b['key']:
        return []
    nu = 0.5 * (a['fstar'] + b['fstar'])
    dv = CKMS * (b['fstar'] - a['fstar']) / nu
    if abs(dv) > HALF_KMS:
        return []
    lo, hi = (a, b) if a['t0'] < b['t0'] else (b, a)
    dt = hi['t0'] - lo['t0']
    df = (hi['fstar'] - lo['fstar']) * 1e9
    # (1) ONE TRAJECTORY AT CONSTANT LINE-OF-SIGHT ACCELERATION.  The drift is
    # then linear in time and the offset has no freedom at all.
    dlo, dhi = lo[dkey], hi[dkey]
    pred = 0.5 * (dlo + dhi) * dt
    res = df - pred
    # The prediction's own uncertainty is the resolution of the drift grid the
    # two windows were searched on, which is where the fitted drifts come from.
    sig = 0.5 * dt * math.hypot(lo['step'], hi['step'])
    # ★ The test has power only while that uncertainty is smaller than the
    # window the criterion searches.  Over long baselines the drift resolution
    # alone spans gigahertz and a pair cannot be separated at all.
    halfhz = HALF_KMS / CKMS * nu * 1e9
    power = sig < halfhz
    # The error both fitted drifts would have to carry to absorb the residual,
    # and what a drift wrong by that much would have done to the crossing that
    # measured it.
    derr = abs(res) / dt
    smear = max(derr * lo['dwell'] / lo['chanw'], derr * hi['dwell']
                / hi['chanw'])
    # (2) ANY BOUNDED TRAJECTORY.  The smallest curvature that joins the pair,
    # expressed as the time its line-of-sight acceleration would need to cross
    # the whole range the search covers.
    dmax = min(lo['dmax'], hi['dmax'])
    J = min_curvature(dlo, dhi, dt, df, dmax)
    if J is None:
        tau = ratio = None
        verdict = 'needs a drift outside the searched range'
    else:
        tau = 2.0 * AG / (C * J / (nu * 1e9))
        ratio = TAU_ORB / tau
        verdict = ('excluded' if tau < TAU_ORB else 'not separable')
    if power and abs(res) <= 3.0 * sig:
        verdict = 'one trajectory'
    return [dict(
        star=lo['star'], attr=bool(lo['attr'] or hi['attr']),
        cidlo=lo['cid'], cidhi=hi['cid'], eblo=lo['eb'], ebhi=hi['eb'],
        nu=nu, dv=dv, dt=dt, dlo=dlo, dhi=dhi,
        dlotopo=lo['drift_topo'], dhitopo=hi['drift_topo'],
        steplo=lo['step'], stephi=hi['step'],
        dmaxlo=lo['dmax'], dmaxhi=hi['dmax'],
        ntriallo=lo['ntrial'], ntrialhi=hi['ntrial'],
        fstarlo=lo['fstar'], fstarhi=hi['fstar'], meanreq=df / dt, pred=pred,
        res=res, sig=sig, nsig=abs(res) / sig, power=power, derr=derr,
        smear=smear, J=J, tau=tau, ratio=ratio, dmax=dmax,
        tlo=lo['tstar'], thi=hi['tstar'], verdict=verdict)]


PAIRS = build_pairs('drift_star')
PTOPO = build_pairs('drift_topo')

# ★★★★ P6b -- THE FRAME CORRECTION MUST BE SHOWN TO CHANGE NOTHING.  Doing
# the extrapolation in the star's frame is correct whatever the answer, but
# the paper is entitled to say the verdicts are unaffected only if that has
# been measured.  Pairs are matched on their two crossing identifiers, never
# on a star name, and the residual shift is reported.
_vt = {(p['cidlo'], p['cidhi']): p for p in PTOPO}
_diff = [k for k, p in ((((p['cidlo'], p['cidhi'])), p) for p in PAIRS)
         if _vt[k]['verdict'] != p['verdict'] or _vt[k]['power'] != p['power']]
_sh = [(abs(p['res'] - _vt[(p['cidlo'], p['cidhi'])]['res']) / p['sig'], p)
       for p in PAIRS]
_shift = max(abs(p['res'] - _vt[(p['cidlo'], p['cidhi'])]['res']) / 1e6
             for p in PAIRS)
_ctl = [p for p in PAIRS if p['attr']]
_ctlt = [_vt[(p['cidlo'], p['cidhi'])] for p in _ctl]
ck('P6b converting the fitted drifts to the star frame before extrapolating '
   'changes no verdict and no power flag, moves every pair by less than its '
   'own resolution, and brings the one pair that IS a single emitter closer '
   'to the prediction rather than further from it',
   not _diff and len(PAIRS) == len(PTOPO)
   and max(q for q, _ in _sh) < 1.0
   and all(abs(a['res']) < abs(b['res']) for a, b in zip(_ctl, _ctlt))
   if DRIVE != 7 else False,
   '%d of %d pairs change verdict; largest shift %.2f MHz and at most %.2f '
   'of a pair\'s own resolution; the control pair moves from %.1f to %.1f '
   'MHz, %.2f to %.2f sigma'
   % (len(_diff), len(PAIRS), _shift, max(q for q, _ in _sh),
      _ctlt[0]['res'] / 1e6, _ctl[0]['res'] / 1e6, _ctlt[0]['nsig'],
      _ctl[0]['nsig']))

UN = [p for p in PAIRS if not p['attr']]
CTL = [p for p in PAIRS if p['attr']]
POWER = [p for p in UN if p['power']]
CONS = [p for p in UN if p['verdict'] == 'one trajectory']
EXCL = [p for p in UN if p['verdict'] in ('excluded',
                                          'needs a drift outside the '
                                          'searched range')]
OPEN = [p for p in UN if p['verdict'] == 'not separable']

# ★★★★ THE ONE RESULT THAT WOULD CHANGE THE PAPER'S CONCLUSION.  A pair the
# constant-acceleration test accepts where it has power is a pair the paper
# may not set aside, and this assertion exists so that outcome can never pass
# in silence.  It is driven, and the drive makes it fire.
ck('P3 no pair of unattributed crossings is consistent with one carrier on '
   'one trajectory where the test has power',
   not CONS if DRIVE != 3 else False,
   '%d of %d pairs have power; %d excluded outright, %d not separable, '
   '%d consistent' % (len(POWER), len(UN), len(EXCL), len(OPEN), len(CONS)))

# ★★★ AND THE TEST MUST BE ABLE TO SAY YES.  The one set of crossings in this
# survey that IS present again is a carbon monoxide line seen in three blocks,
# and the test returns one trajectory for it.  Without this the whole section
# would be a check that cannot fail.
ck('P5 the test returns one trajectory for the crossings that do recur',
   bool(CTL) and all(p['verdict'] == 'one trajectory' for p in CTL)
   if DRIVE != 5 else False,
   '%d control pair(s): %s' % (len(CTL),
                               '; '.join('%s %.2f d at %.1f sigma -> %s'
                                         % (p['star'], p['dt'] / 86400.0,
                                            p['nsig'], p['verdict'])
                                         for p in CTL)))

m('TjNPair', '%d' % len(UN))
m('TjNStarPair', '%d' % len({p['star'].split(' Gaia')[0] for p in UN}))
m('TjNPower', '%d' % len(POWER))
m('TjNExcl', '%d' % len(EXCL))
m('TjNOpen', '%d' % len(OPEN))
m('TjNCons', '%d' % len(CONS))
m('TjSigMin', '%.1f' % min(p['nsig'] for p in POWER))
m('TjHalfKms', '%.0f' % HALF_KMS)
m('TjTauOrbH', '%.0f' % (TAU_ORB / 3600.0))
m('TjPorbD', '%.1f' % (PORB / 86400.0))
m('TjAGrid', '%.1f' % AG)
m('TjVorbKms', '%.0f' % (VORB / 1e3))
m('TjNoDrift', '%d' % len(NODRIFT))
m('TjNTested', '%d' % len([r for r in ROWS if not r['attr']]))
m('TjDtPowerMaxD', '%.0f' % (max(p['dt'] for p in POWER) / 86400.0))
m('TjDtOpenMinD', '%.0f' % (min(p['dt'] for p in OPEN) / 86400.0))
# ★★★★ THE TWO ANSWERS PARTITION THE PAIRS DIFFERENTLY AND THE PAPER MUST NOT
# PRINT ONE COUNT FROM EACH AS IF THEY WERE COMPLEMENTARY.  The
# constant-acceleration comparison RESOLVES the interval for \TjNPower of the
# \TjNPair pairs and all of those fail it; the bounded-trajectory criterion,
# which is the weaker demand and therefore the one a verdict rests on,
# partitions all \TjNPair into \TjNExcl excluded and \TjNOpen not separable.
# A pair can be resolved by the first and not separable by the second, and
# the mildest resolved failure is exactly such a pair.  Both counts are
# emitted, their sums are asserted, and the two of the excluded that are
# excluded on the reversal timescale are named apart from the one that needs
# a drift the search never covered.
_etau = [p for p in EXCL if p['tau'] is not None]
_egrid = [p for p in EXCL if p['tau'] is None]
m('TjNExclTau', '%d' % len(_etau))
m('TjNExclGrid', '%d' % len(_egrid))
m('TjRatioLo', '%.1f' % min(p['ratio'] for p in _etau))
m('TjRatioHi', '%.1f' % max(p['ratio'] for p in _etau))
m('TjNPowerOpen', '%d' % len([p for p in POWER
                              if p['verdict'] == 'not separable']))
if DRIVE == 8:                           # P7: the two partitions conflated
    _etau = _etau + _egrid
ck('P7 the two criteria partition the pairs separately and both partitions '
   'close on the same total, so no count from one may be subtracted from a '
   'count from the other',
   len(EXCL) + len(OPEN) + len(CONS) == len(UN)
   and len(_etau) + len(_egrid) == len(EXCL)
   and len(POWER) <= len(UN),
   '%d excluded (%d on the reversal timescale, %d needing a drift outside '
   'the grid) + %d not separable + %d consistent == %d pairs; the '
   'constant-acceleration comparison resolves %d of them, of which %d are '
   'not separable under a bounded trajectory'
   % (len(EXCL), len(_etau), len(_egrid), len(OPEN), len(CONS), len(UN),
      len(POWER), len([p for p in POWER
                       if p['verdict'] == 'not separable'])))

# ---- the pair the referee starts from, and the two others they name
def named(star, k=0):
    q = [p for p in UN if p['star'].split(' Gaia')[0].replace(' ', '')
         == star.replace(' ', '')]
    q.sort(key=lambda p: abs(p['dv']))
    return q[k] if len(q) > k else None


BP = named('bet Pic')
assert BP is not None and abs(BP['dt'] / 3600.0 - 24.4) < 0.1, BP
m('TjBpDvKms', '%.0f' % abs(BP['dv']))
m('TjBpOffMHz', '%.0f' % abs((BP['fstarhi'] - BP['fstarlo']) * 1e3))
m('TjBpDtH', '%.1f' % (BP['dt'] / 3600.0))
m('TjBpDriftLo', '%+.0f' % BP['dlo'])
m('TjBpDriftHi', '%+.0f' % BP['dhi'])
m('TjBpMeanReq', '%+.0f' % BP['meanreq'])
m('TjBpCeil', '%.0f' % BP['dmax'])
m('TjBpPredMHz', '%+.0f' % (BP['pred'] / 1e6))
m('TjBpResMHz', '%.0f' % abs(BP['res'] / 1e6))
m('TjBpResKms', '%.0f' % abs(CKMS * BP['res'] / (BP['nu'] * 1e9)))
m('TjBpNSig', '%.0f' % BP['nsig'])
m('TjBpSmearCh', '%.0f' % BP['smear'])
m('TjBpDerr', '%.0f' % BP['derr'])
m('TjBpTauH', '%.1f' % (BP['tau'] / 3600.0))
m('TjBpRatio', '%.1f' % BP['ratio'])
m('TjBpNuLo', '%.4f' % BP['fstarlo'])
m('TjBpNuHi', '%.4f' % BP['fstarhi'])
# ★★★★ THE PAIR MUST BE JUDGED BY THE SAME CRITERION AS THE OTHERS.  Its mean
# required drift corresponds to a line-of-sight acceleration INSIDE the grid's
# own ceiling, so "both drifts are negative and the carrier would have had to
# rise" disposes of nothing on its own: under constant acceleration it fails
# at \TjBpNSig sigma like the other resolved pairs, and under a bounded
# trajectory it is excluded because the reversal it needs is \TjBpRatio times
# faster than the acceleration ceiling allows.  That is the narrowest margin
# of any exclusion here and the paper says so.
m('TjBpAccelReq', '%.2f' % abs(C * BP['meanreq'] / (BP['nu'] * 1e9)))

# ---------------- the grid, and why a fitted drift can lie outside it
# ★★★ A FITTED DRIFT IS NOT A GRID POINT.  The search steps uniformly to
# +/-`drift_max` for the window, and the peak is then refined inside one step,
# so a fitted value can fall beyond the outermost trial; and the printed
# drifts are STELLAR-FRAME while the ceiling is a bound on the topocentric
# drift the grid was built in.  Both effects are measured here on the largest
# drift the table prints, so the caption can say whether the grid extends
# past the ceiling.  It does not.
_big = max((p for p in PAIRS), key=lambda p: max(abs(p['dlotopo']),
                                                 abs(p['dhitopo'])))
_bl = (_big if abs(_big['dlotopo']) > abs(_big['dhitopo']) else None)
_dtopo, _dstar, _dmax_w, _ntr = (
    (_big['dlotopo'], _big['dlo'], _big['dmaxlo'], _big['ntriallo']) if _bl
    else (_big['dhitopo'], _big['dhi'], _big['dmaxhi'], _big['ntrialhi']))
_nu_big = (_big['fstarlo'] if _bl else _big['fstarhi'])
_step_big = 2.0 * _dmax_w / (_ntr - 1)
m('TjGridEdgeHzS', '%.0f' % _dmax_w)
m('TjGridStepHzS', '%.0f' % _step_big)
m('TjGridOverStep', '%.2f' % ((abs(_dtopo) - _dmax_w) / _step_big))
m('TjGridEdgeNHz', '%.2f' % (_dmax_w / _nu_big))
m('TjDriftMaxNHz', '%.2f' % (abs(_dstar) / _nu_big))
m('TjFrameMaxHzS', '%.0f' % max(abs(r['frame_term']) for r in ROWS))
if DRIVE == 9:                           # P8: the grid read past its ceiling
    _dmax_w = 1.5 * _dmax_w
ck('P8 the searched drift grid stops at the acceleration ceiling, and the '
   'largest drift the table prints exceeds it only through the sub-step '
   'refinement of a fitted value and the conversion to the star frame',
   _dmax_w / _nu_big <= float(macro('DriftCeilLo')) + 0.01
   and abs(_dtopo) > _dmax_w
   and abs(_dtopo) - _dmax_w < _step_big
   and abs(_dstar) / _nu_big > float(macro('DriftCeilLo')),
   'grid edge %.1f Hz/s = %.3f nHz against a declared ceiling of %s; fitted '
   '%.1f Hz/s, %.2f of a %.1f Hz/s step beyond it; in the star frame %.1f '
   'Hz/s = %.3f nHz'
   % (_dmax_w, _dmax_w / _nu_big, macro('DriftCeilLo'), abs(_dtopo),
      (abs(_dtopo) - _dmax_w) / _step_big, _step_big, abs(_dstar),
      abs(_dstar) / _nu_big))

HD = named('HD14055')
m('TjHdDvKms', '%.0f' % abs(HD['dv']))
m('TjHdDtD', '%.1f' % (HD['dt'] / 86400.0))
m('TjHdResMHz', '%.0f' % abs(HD['res'] / 1e6))
m('TjHdNSig', '%.0f' % HD['nsig'])
m('TjHdSmearCh', '%.0f' % HD['smear'])
m('TjHdTauH', '%.0f' % (HD['tau'] / 3600.0))

AJ = named('ALMA J153702653-33192492')
m('TjAjDvKms', '%.0f' % abs(AJ['dv']))
m('TjAjDtD', '%.0f' % (AJ['dt'] / 86400.0))
m('TjAjNSig', '%.1f' % AJ['nsig'])
m('TjAjTauD', '%.0f' % (AJ['tau'] / 86400.0))

CP = CTL[0]
m('TjCtlStar', tname(CP['star']))
m('TjCtlLine', 'CO($2$--$1$)')
m('TjCtlDtD', '%.1f' % (CP['dt'] / 86400.0))
m('TjCtlOffKHz', '%.0f' % abs((CP['fstarhi'] - CP['fstarlo']) * 1e6))
m('TjCtlDriftLo', '%+.0f' % CP['dlo'])
m('TjCtlDriftHi', '%+.0f' % CP['dhi'])
m('TjCtlNSig', '%.1f' % CP['nsig'])
m('TjCtlSmearCh', '%.2f' % CP['smear'])

# ======================================================= R2-2, one channel
# What the inverse-variance combination over every covering block buys over
# the nearest single one.  The nearest block assumes only that the carrier
# was there at both epochs; the combination assumes it returned to the same
# stellar-frame channel at the start of every block.
# ★★★★ THE SET IS THE QUOTED EXCLUSIONS AND NOT EVERY CROSSING WITH REPEAT
# COVERAGE.  Four crossings come from the one execution block the quality
# criterion rejects, and their exclusions are WITHHELD: the ledger prints no
# value for them, so a median taken over them is a median of numbers the
# paper does not publish -- and because all four have the deepest repeat
# coverage in the survey it was also the flattering median.  The flag is read
# from the ledger, keyed on block and frequency.
DQKEY = {(r['eb'], round(float(r['freq']), 6)) for r in LED if r.get('dq')}
NEAR, NEARDQ = [], []
for cid, v in sorted(REC.items()):
    d = v.get('discovery') or {}
    k = '%s|%.6f' % (v['eb'], float(v['freq_GHz']))
    rc = RCOL.get(k) or {}
    bl = [b for b in (v.get('blocks') or []) if not b.get('bad_weight_product')]
    if not bl or rc.get('T_pers') is None or not d.get('amp_mJy'):
        continue
    b = min(bl, key=lambda z: abs(z['sep_from_discovery_h']))
    tp = d['amp_mJy'] / b['sig_mJy']
    tr = b['T_matched']
    rec = dict(
        cid=cid, star=v['star'], n_rep=rc['n_rep'],
        span_d=rc['dt_max_d'], near_h=abs(b['sep_from_discovery_h']),
        f5_comb=rc['f5'], f5_near=(tr + TRIG) / tp,
        excl_comb=rc['excl'],
        excl_near=(tp - tr) / math.sqrt(1.0 + (tp / float(v['tstar'])) ** 2),
        tpers_comb=rc['T_pers'], tpers_near=tp,
        withheld=(v['eb'], round(float(v['freq_GHz']), 6)) in DQKEY)
    (NEARDQ if rec['withheld'] and DRIVE != 10 else NEAR).append(rec)
NEAR.sort(key=lambda z: z['f5_comb'])
# ★ The case R2-2 names: the crossing whose exclusion rests on the most
# blocks over the longest span, which is where the periodic-reset assumption
# does the most work.  Read as the maximum, never chosen by hand.
DEEP = max(NEAR, key=lambda z: (z['n_rep'], z['span_d']))
m('TjCombNCross', '%d' % len(NEAR))
m('TjDeepStar', tname(DEEP['star']))
m('TjDeepNRep', '%d' % DEEP['n_rep'])
m('TjDeepSpanD', '%.0f' % DEEP['span_d'])
m('TjDeepNearH', '%.0f' % DEEP['near_h'])
m('TjDeepFracComb', '%.2f' % DEEP['f5_comb'])
m('TjDeepFracNear', '%.2f' % DEEP['f5_near'])
m('TjDeepExclComb', '%.1f' % DEEP['excl_comb'])
m('TjDeepExclNear', '%.1f' % DEEP['excl_near'])
m('TjDeepGain', '%.0f' % (DEEP['f5_near'] / DEEP['f5_comb']))
_fn = sorted(z['f5_near'] for z in NEAR)
_fc = sorted(z['f5_comb'] for z in NEAR)
m('TjFracNearMed', '%.2f' % _fn[len(_fn) // 2])
m('TjFracCombMed', '%.2f' % _fc[len(_fc) // 2])
m('TjNNearWeak', '%d' % sum(1 for z in NEAR if z['f5_near'] >= 1.0))
m('TjNWithheld', '%d' % len(NEARDQ))
# ★ P9: the set these medians run over is the set the paper publishes values
# for, and it closes on round 120's own counts both ways.
if DRIVE == 11:
    _fc = _fc + [0.0]
ck('P9 the two medians run over the quoted exclusions only, the withheld '
   'rows are counted apart, the two sets close on round 120, and the '
   'combined median agrees with the one round 120 publishes',
   len(NEAR) == int(macro('RcNExcl'))
   and len(NEARDQ) == int(macro('RcNWithheld'))
   and len(NEAR) + len(NEARDQ) == int(macro('RcNExclPoss'))
   and '%.2f' % _fc[len(_fc) // 2] == macro('RcFracMed'),
   '%d quoted + %d withheld == %d against round 120 %s + %s == %s; combined '
   'median %.3f against %s; the withheld rows would have moved it to %.3f'
   % (len(NEAR), len(NEARDQ), len(NEAR) + len(NEARDQ), macro('RcNExcl'),
      macro('RcNWithheld'), macro('RcNExclPoss'), _fc[len(_fc) // 2],
      macro('RcFracMed'),
      sorted([z['f5_comb'] for z in NEAR + NEARDQ])[
          (len(NEAR) + len(NEARDQ)) // 2]))
m('TjChanKHz', '%.0f' % (min(r['chanw'] for r in ROWS
                             if r['chanw'] > 4e5) / 1e3))
m('TjChanKms', '%.1f' % (CKMS * min(r['chanw'] for r in ROWS
                                    if r['chanw'] > 4e5) * 1e-9
                         / max(r['fstar'] for r in ROWS)))
# ★ Where only one block covers the crossing the combination IS the nearest
# block, so the two agree to the rounding of the published column; the claim
# is about the crossings whose exclusion combines more than one.
_MULTI = [z for z in NEAR if z['n_rep'] > 1]
ck('P4 the nearest single repeat block is a weaker limit than the '
   'combination over every covering block, for every crossing whose '
   'exclusion combines more than one',
   all(z['f5_near'] > z['f5_comb'] for z in _MULTI)
   and all(abs(z['f5_near'] - z['f5_comb']) < 0.01
           for z in NEAR if z['n_rep'] == 1)
   if DRIVE != 4 else False,
   'median %.2f S against %.2f S over %d crossings; %d of %d are not '
   'constrained at all by their nearest block alone; %d crossings have one '
   'covering block and the two agree'
   % (_fn[len(_fn) // 2], _fc[len(_fc) // 2], len(_MULTI),
      sum(1 for z in NEAR if z['f5_near'] >= 1.0), len(NEAR),
      len(NEAR) - len(_MULTI)))
m('TjNNearOne', '%d' % (len(NEAR) - len(_MULTI)))

# ================================================================== table
def _fmt(x, f='%.4f'):
    return f % x


# ★★★ TWO COLUMNS INSTEAD OF AN ITALIC.  The old table marked the pairs the
# comparison cannot resolve by setting their residual in italics, which is a
# typographic distinction that does not survive into a plain-text or an XML
# rendering of the table -- and the number it marked was meaningless there in
# any case.  So the residual is printed only where the comparison resolves
# the interval, and the verdict each pair actually receives gets a column of
# its own, in words.
VERD = {'excluded': 'no', 'not separable': 'open', 'one trajectory': 'yes',
        'needs a drift outside the searched range': 'no'}
with open(OUTT, 'w') as fh:
    fh.write('%% GENERATED by pairs_v415.py -- do not hand-edit.\n')
    fh.write('\\begin{tabular}{@{}l@{~}l@{\\,}r@{\\,}r@{\\,}r@{\\,}r'
             '@{\\,}r@{~}l@{}}\n')
    fh.write('\\hline\nStar & blocks & $\\Delta t$ & '
             '$\\dot\\nu_1$ & $\\dot\\nu_2$ & $\\Delta\\nu$ & '
             'miss & one \\\\\n')
    fh.write(' & & (d) & \\multicolumn{2}{c}{(Hz\\,s$^{-1}$)} & (MHz) & '
             '($\\sigma$) & carrier? \\\\\n\\hline\n')
    last = None
    for p in sorted(PAIRS, key=lambda z: (z['attr'], z['star'], z['dt'])):
        if p['attr'] and last is not None and 'HD~285968' != last:
            fh.write('\\hline\n')
            last = None
        nm = tname(p['star'].split(' Gaia')[0])
        if 'ALMA' in nm:
            nm = 'J1537$-$3319'
        shown = '' if nm == last else nm
        last = nm
        off = (p['fstarhi'] - p['fstarlo']) * 1e3
        fh.write('%s & %s/%s & %s & $%+.0f$ & $%+.0f$ & %s & %s & %s \\\\\n'
                 % (shown,
                    p['eblo'].split('_')[-1], p['ebhi'].split('_')[-1],
                    ('%.2f' % (p['dt'] / 86400.0)) if p['dt'] < 86400 * 10
                    else '%.0f' % (p['dt'] / 86400.0),
                    p['dlo'], p['dhi'],
                    ('$%+.1f$' % off) if abs(off) >= 0.05
                    else '$%+.3f$' % off,
                    (('%.1f' if p['nsig'] < 10 else '%.0f') % p['nsig'])
                    if p['power'] else '---',
                    VERD[p['verdict']]))
        if p['attr']:
            break
    fh.write('\\hline\n\\end{tabular}\n')

json.dump(dict(pairs=PAIRS, near=NEAR, nodrift=NODRIFT,
               tau_orb_s=TAU_ORB, porb_s=PORB, a_grid=AG,
               half_kms=HALF_KMS), open(OUTJ, 'w'), indent=1, default=str)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by pairs_v415.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
print('%d pairs -> %s' % (len(PAIRS), os.path.basename(OUTT)))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
