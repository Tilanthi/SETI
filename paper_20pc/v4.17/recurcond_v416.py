#!/usr/bin/env python3
r"""recurcond_v416.py -- what the recurrence test actually permits, and the
two attributed crossings that do not come back.

Round 550.  Writes `survey_numbers_round550.tex` only.

WHY THIS EXISTS.  The recurrence criterion is read at ONE cell: one channel
of the repeat window, at the drift carried from the discovery epoch.  Every
exclusion the paper quotes is therefore conditional on the carrier having
stayed inside that cell, and the width of the cell is a measured number the
paper never printed.  This generator prints it, per crossing, as a frequency
and as the equivalent change in line-of-sight velocity, and compares it with
the velocity excursion a transmitter in orbit would show over the same
baseline.  It also prints:

* the FOUR recovery probabilities of the four crossings where the criterion
  has little power, individually.  The text quoted one value -- the minimum
  over the four -- beside all four names, which reads as the same number four
  times, and it is not: at the discovery amplitude they are 0.41, 0.51, 0.77
  and 0.85;

* the measured saturation of sigma_excl.  The exclusion significance
  (T_pers - T_rep)/sqrt(1 + (T_pers/T_star)^2) tends to T_star as T_pers
  grows, so where the repeat coverage is deep the quantity restates the
  discovery significance and carries no information about the repeat.  That
  is why the fraction of the discovery amplitude still excluded at the
  trigger, (T_rep + 5)/T_pers, is the quantity the tables lead with;

* the stellar-frame recurrence reading for the two line-attributed crossings
  that are not recovered, HR 1010 and ALMA J153702653-33192492, with the
  noise each window's own on-source time supports.

★★★★ ONE DEFECT FIXED HERE, AND IT IS THE REASON ONE OF THOSE TWO LOOKED
LIKE A CONTRADICTION.  T_pers for a line-attributed crossing is formed as
T_star x (sigma of the discovery window) / (sigma of the deepest repeat).
HR 1010's discovery window exists twice on this host: the delivered
extraction integrated 60.48 s of the track and the re-extraction integrated
2842.56 s of it, and the two differ in noise by a factor of 7.1.  The
crossing statistic T_star = 5.41 is the re-extracted one -- the delivered
extraction gives 3.77, below the trigger -- while the window noise was taken
from the delivered row, because that row is reached first.  The product was
T_pers = 60.1 for a crossing whose own window supports 8.4, and a 2.1-sigma
non-recovery was published as a 5.0-sigma one.  The adopted noise is checked
against the seven sibling blocks of the same star at the same on-source
time, which is an external check and not a preference: 11.50 mJy sits inside
their 7.38-11.65 mJy and 81.89 mJy does not.

ASSERTIONS (each driven; `--drive N` perturbs and the check must fail)
    Q1  the displacement the exclusion permits is half a channel of the
        repeat window, in the star's frame, and it is narrower than the
        interval searched about the cell by the printed factor
    Q2  the four low-power recovery probabilities are four DISTINCT numbers,
        so no single value may be printed beside all four names
    Q3  sigma_excl saturates: where T_pers exceeds T_star by a factor the
        data supply, sigma_excl agrees with T_star to within 5 per cent, so
        it is not a statement about the repeat
    Q4  the noise adopted for a twice-extracted discovery window is the one
        its own on-source time supports, tested against the sibling blocks
        of the same star, and the rejected value fails that test
    Q5  the positive control is READ from the ledger: the recovered,
        not-recovered and uncovered attributed crossings partition the
        attributed rows, and at least one attributed crossing is not
        recovered, so the stage can return no
    Q6  every frequency this round prints is the stellar-frame one, equal to
        the ledger's own f_stellar to the printed precision

Usage: recurcond_v416.py [--drive N]
"""
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round550.tex')
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE

C_KMS = 299792.458
TRIG = 5.0
GM_SUN = 1.32712440018e20       # m^3 s^-2, IAU 2015 nominal
AU_M = 1.495978707e11           # m, IAU 2012 definition
A_AU = GM_SUN / AU_M ** 2       # 5.93e-3 m s^-2, a transmitter at 1 au
SAT_TOL = 0.05                  # Q3: 5 per cent


def out(name):
    b, e = os.path.splitext(name)
    return os.path.join(HERE, b + SFX + e)


def _phi(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def med(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def macro(name):
    """One macro's value out of the frozen layer, by name.  A generator that
    prints a number another generator owns must READ it, or the two drift."""
    import glob
    import re as _re
    pat = _re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                      r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('macro %s not found' % name)
    return v


def tname(s):
    """The ledger's own DISPLAY name with non-breaking spaces, and an ASCII
    hyphen promoted to a maths minus only where the display field does not
    already carry one: rewriting a hyphen inside maths turns `CP$-$72` into
    `CP$--$72`, and leaving one alone sets a minus sign as a hyphen."""
    if '$' not in s:
        s = s.replace('-', '$-$')
    return s.replace(' ', '~')


M, fail = [], []


def m(k, v):
    assert k.isalpha(), k           # a macro name may hold letters only
    assert k not in [a for a, _ in M], k
    M.append((k, v))


def ck(name, cond, detail=''):
    if not cond:
        fail.append(name)
    print('  %-62s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


# ------------------------------------------------------------------ inputs
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
ROWS = LED['rows']
R = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
CROSS = R['crossings']
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'), encoding='utf-8')))
REP = list(csv.DictReader(open(os.path.join(
    HERE, 'repaired_v409.csv'), encoding='utf-8')))
BARY = json.load(open(os.path.join(
    HERE, 'r8inputs', 'bary_v405.json')))['v_bary_kms']
import epochs_r14 as _ep          # the ONE determination of a block's epoch
MJD = _ep.EPOCHS

# The stellar-frame frequency of every crossing, keyed the way the ledger
# keys itself -- block and frequency, never a star name.
FSTELLAR = {(r['eb'], round(float(r['freq']), 4)): r['frame']['f_stellar']
            for r in ROWS}
ATTRIB = {(r['eb'], round(float(r['freq']), 4)): bool(r['attributed'])
          for r in ROWS}
SCREEN = {(r['eb'], round(float(r['freq']), 4)) for r in ROWS
          if r.get('screen') and not r['attributed']}
DISPLAY = {(r['eb'], round(float(r['freq']), 4)): r['display'] for r in ROWS}
DQ = {(r['eb'], round(float(r['freq']), 4)) for r in ROWS if r.get('dq')}
BYEB = {}
for r in CAT:
    BYEB.setdefault(r['eb'], []).append(r)
BYSYS = {}
for r in CAT:
    BYSYS.setdefault(r['system_id'], []).append(r)


def lkey(c):
    return (c['eb'], round(float(c['freq_GHz']), 4))


# ============================================================= 1. the cell
# Every quoted exclusion is read at one channel of the repeat window at one
# drift, so the displacement it tolerates is half that channel.  Expressed as
# a change in line-of-sight velocity it is the number a reader needs in order
# to know what the exclusion is an exclusion of.
UNITS = []
for cid, c in CROSS.items():
    if c['status'] != 'ok':
        continue
    bl = [b for b in c.get('blocks', []) if not b.get('bad_weight_product')]
    if not bl:
        continue
    k = lkey(c)
    if k not in FSTELLAR or ATTRIB[k] or k in DQ:
        continue                       # the 33 quoted exclusions, no others
    fs = FSTELLAR[k]
    near = min(bl, key=lambda b: abs(b['sep_from_discovery_h']))
    dt_near = abs(near['sep_from_discovery_h']) * 3600.0
    dt_far = max(abs(b['sep_from_discovery_h']) for b in bl) * 3600.0
    half = 2.0 if DRIVE == 1 else 0.5   # Q1: a whole channel, not a half
    S = c['discovery']['amp_mJy']
    sd = c['discovery']['sig_mJy']
    w = [1.0 / b['sig_mJy'] ** 2 for b in bl]
    sb = 1.0 / math.sqrt(sum(w))
    ab = sum(b['amp_mJy'] * q for b, q in zip(bl, w)) / sum(w)
    t_pers, t_rep = S / sb, ab / sb
    # ★★ THE NEAREST BLOCK ALONE, which is the reading that assumes only the
    # two observations.  The combination above assumes the carrier returned
    # to the same channel at the start of every covering block, so the
    # survival argument at 1 au has to be attached to the single-block
    # reading and the baseline the combination spans has to be quoted beside
    # it.  Both are built here, per crossing, from that block's own noise.
    near_pers = S / near['sig_mJy']
    near_rep = near['T_matched']
    UNITS.append(dict(
        star=DISPLAY[k], screen=k in SCREEN, fs=fs, chanw=near['chanw_Hz'],
        dv=half * near['chanw_Hz'] / (fs * 1e9) * C_KMS,
        dv_far=half * max(b['chanw_Hz'] for b in bl) / (fs * 1e9) * C_KMS,
        dt_near=dt_near, dt_far=dt_far, n_rep=len(bl),
        near_deepest=(near['sig_mJy']
                      == min(b['sig_mJy'] for b in bl)),
        near_pers=near_pers, near_rep=near_rep,
        near_f5=(near_rep + TRIG) / near_pers,
        orb_near=A_AU * dt_near / 1000.0, orb_far=A_AU * dt_far / 1000.0,
        t_pers=t_pers, t_rep=t_rep, t_star=c['discovery']['T_matched'],
        f5=(t_rep + TRIG) / t_pers,
        excl=(S - ab) / math.sqrt(sd * sd + sb * sb),
        p_conf=_phi(t_pers - TRIG),
        amp=S, amp_err=sd,
        rms_win=next((float(r['rms_mJy']) for r in BYEB.get(c['eb'], [])
                      if min(float(r['flo_GHz']), float(r['fhi_GHz']))
                      <= c['freq_GHz']
                      <= max(float(r['flo_GHz']), float(r['fhi_GHz']))), None),
        p_trig=_phi(t_pers * TRIG / c['discovery']['T_matched'] - TRIG)))
UNITS.sort(key=lambda u: (u['star'], u['fs']))
# ★ Q2's third clause guards the one join that could silently invalidate the
# trigger-amplitude power: the discovery statistic and the persistence
# statistic must come from the SAME crossing.  Drive 10 takes T_star from
# the neighbouring row, which is what a star-keyed join does here, and the
# inequality p_trig <= p_conf then fails.
if DRIVE == 10:
    _shift = [u['t_star'] for u in UNITS[1:]] + [UNITS[0]['t_star']]
    for u, ts in zip(UNITS, _shift):
        u['p_trig'] = _phi(u['t_pers'] * TRIG / ts - TRIG)
NU = len(UNITS)

A_GRID = float(macro('WdAGrid'))        # the drift grid's own ceiling
SEARCH_HALF = float(macro('WdHalfKms'))  # the interval searched about the cell
DVS = [u['dv'] for u in UNITS]
m('RqNUnit', '%d' % NU)
m('RqDvLo', '%.2f' % min(DVS))
m('RqDvMed', '%.2f' % med(DVS))
m('RqDvHi', '%.2f' % max(DVS))
m('RqOrbAu', '%.1f' % (A_AU * 1e3))     # mm s^-2 at 1 au
# ★ The two crossings whose stellar statistic leads their own control field
# are READ out of the ledger's own rank flag, never named here, and each
# carries its own permitted displacement.  They are the rows Table 5 and
# Fig. 6 print, so the caption can state the interval the test covers.
# ★ The pair is ordered by DISCOVERY STATISTIC, which is the order round 120
# uses for the same two crossings, so `A` here and `Sx` there are the same
# event.  Ordering by frequency would agree today and silently stop agreeing.
# ★ The two tags are `Sx` and `Cp`, the names round 120 already uses for the
# same two crossings, and NOT `A`/`B`: `twinmacro.py` strips a trailing A or B
# as a class suffix, so \RqDvA and \RqDvB would be read as one quantity
# carrying two values -- which, for the Class A and Class B experiments, is
# exactly what it is meant to catch.
SCR = sorted([u for u in UNITS if u['screen']], key=lambda u: -u['t_star'])
for tag, u in zip(('Sx', 'Cp'), SCR):
    m('RqDisp%s' % tag, '%.3f' % u['dv'])
    m('RqFreq%s' % tag, '%.4f' % u['fs'])
    m('RqOrb%s' % tag, '%.3f' % u['orb_near'])
    m('RqGrid%s' % tag, '%.0f' % (A_GRID * u['dt_near'] / 1e3))
    # ★★ The single-block reading and the baseline the combination spans.
    # The 1 au displacement that the paper attaches to these two exclusions
    # belongs to the NEAREST block's interval, which is hours; the combined
    # reading spans days, over which the same orbit moves the carrier by
    # `RqOrbFar<tag>` and far outside the half-channel the reading covers.
    m('RqNearTPers%s' % tag, '%.2f' % u['near_pers'])
    m('RqNearTRep%s' % tag, '%+.2f' % u['near_rep'])
    m('RqNearFrac%s' % tag, '%.2f' % u['near_f5'])
    m('RqSpanD%s' % tag, '%.0f' % (u['dt_far'] / 86400.0))
    m('RqOrbFar%s' % tag, '%.2f' % u['orb_far'])
    m('RqNRep%s' % tag, '%d' % u['n_rep'])
    m('RqPowerTrig%s' % tag, '%.2f' % u['p_trig'])
    # ★★ TWO ESTIMATORS OF ONE FLUX, AND HOW FAR APART THEY ARE.  The fitted
    # amplitude with its own error is what Table 5 prints; the statistic
    # times the window's published noise is a second estimator of the same
    # quantity, carries no error, and is what the line-mask appendix quotes.
    # The difference is printed in units of the fitted error so that an
    # argument resting on it can be read for what it is worth.
    m('RqAmpSigma%s' % tag, '%.2f' % (abs(u['t_star'] * u['rms_win']
                                          - u['amp']) / u['amp_err']))

# ★★★★ Q9 -- THE CHECK THAT STOPS THE SURVIVAL ARGUMENT BEING ATTACHED TO THE
# WRONG READING.  For each of the two rank-leading crossings the nearest
# single block must give a WEAKER limit than the combination over every
# covering block, and the orbital displacement at 1 au must be inside the
# permitted half-channel over the nearest interval and OUTSIDE it over the
# longest baseline.  If that second clause ever fails, the combined reading
# would survive an orbit of that period and the restriction is unnecessary;
# if the first fails, the combination is not buying anything and the two
# readings should not be printed apart.
_scr_weaker = all(u['near_f5'] >= u['f5'] - 1e-9 for u in SCR)
_scr_near_in = all(u['orb_near'] < u['dv'] for u in SCR)
_scr_far_out = all(u['orb_far'] > u['dv_far'] for u in SCR)
# ★★ AND THE SECOND EVENT'S SINGLE-BLOCK READING IS THE ONE ANOTHER ROUND
# ALREADY PUBLISHES, because for that crossing the nearest covering block is
# also the deepest.  Two generators computing one quantity must agree to the
# digits they print, or the paper carries it twice at two values.
_cp = SCR[1]
_cp_agrees = (_cp['near_deepest']
              and '%.1f' % _cp['near_pers'] == macro('EvBDeepTPers')
              and '%+.2f' % _cp['near_rep'] == macro('EvBDeepTObs'))
if DRIVE == 9:                           # Q9: the combination read as single
    _scr_weaker = all(u['f5'] >= u['near_f5'] - 1e-9 for u in SCR)
if DRIVE == 13:                          # Q9: the two rounds drift apart
    _cp_agrees = '%.3f' % _cp['near_pers'] == macro('EvBDeepTPers')
ck('Q9 for both rank-leading crossings the nearest single block is a weaker '
   'limit than the combination, an orbit at 1 au stays inside the permitted '
   'half-channel over the nearest interval, the same orbit leaves it over '
   'the longest baseline, and the second event\'s nearest block is also its '
   'deepest and reads what round 190 publishes for it',
   _scr_weaker and _scr_near_in and _scr_far_out and _cp_agrees,
   '; '.join('%s nearest %.2f S over %.2f h (orbit %.3f of %.3f km/s) '
             'against combined %.2f S over %.1f d (orbit %.2f km/s)'
             % (u['star'], u['near_f5'], u['dt_near'] / 3600.0,
                u['orb_near'], u['dv'], u['f5'], u['dt_far'] / 86400.0,
                u['orb_far']) for u in SCR))
# How many exclusions survive an orbiting transmitter at all: at 1 au the
# line-of-sight velocity moves by a_au x dt, and the exclusion holds only
# while that is inside the cell.
_in_near = [u for u in UNITS if u['orb_near'] < u['dv']]
_in_far = [u for u in UNITS if u['orb_far'] < u['dv_far']]
_in_grid = [u for u in UNITS if A_GRID * u['dt_near'] / 1e3 < u['dv']]
m('RqNOrbNear', '%d' % len(_in_near))
m('RqNOrbFar', '%d' % len(_in_far))
m('RqNOrbGrid', '%d' % len(_in_grid))
m('RqOrbGridWord', 'none' if not _in_grid else '%d' % len(_in_grid))

if DRIVE == 2:                           # Q1: a cell wider than the search
    SEARCH_HALF = 0.5 * med(DVS)
ck('Q1 the exclusion is read at one cell, so the displacement it permits is '
   'half a channel in the star frame; the interval searched about that cell '
   'is wider; and the two rank-leading crossings are read from the ledger',
   all(abs(u['dv'] - 0.5 * u['chanw'] / (u['fs'] * 1e9) * C_KMS) < 1e-9
       for u in UNITS) and SEARCH_HALF > max(DVS) and len(SCR) == 2,
   '%d units, permitted %.2f-%.2f km/s, searched +/-%.0f km/s; %d '
   'rank-leading: %s'
   % (NU, min(DVS), max(DVS), SEARCH_HALF, len(SCR),
      [(u['star'], round(u['fs'], 4)) for u in SCR]))

# ================================= 2. the recovery chance, at the trigger
# ★★★★ THE POWER IS EVALUATED AT THE TRIGGER AMPLITUDE AND NOT AT THE
# DISCOVERY AMPLITUDE.  A discovery amplitude is selected as the largest of
# between a hundred and a few million cells at a statistic of about five, so
# it is biased high (Appendix B.2); the faintest carrier consistent with the
# crossing having been found at all is 5S/T_star, and the recovery chance
# there is Phi(5 T_pers/T_star - 5).  That is the number the paper quotes,
# the crossings below the declared level are UNTESTED rather than excluded,
# and both probabilities stay in Table 5 so a reader can see the difference
# selection makes.
POWER = float(macro('RcPowerLevel')) / 100.0
LOW = sorted([u for u in UNITS if u['p_trig'] < POWER],
             key=lambda u: u['p_trig'])
if DRIVE == 3:                           # Q2: one value for every crossing
    LOW = [dict(u, p_conf=LOW[0]['p_conf'], p_trig=LOW[0]['p_trig'])
           for u in LOW]
# ★ The LOW count and its smallest member are \RcNPowerLoTrig and
# \RcPowerMinTrig in round 120; only the list and the complementary count
# are emitted here, and the complement is required to close on \RcNExcl so
# the two rounds cannot drift apart.
_parts = ['%s at %.2f\\,GHz (%.2f)'
          % (tname(u['star']), u['fs'], u['p_trig']) for u in LOW]
m('RqLowList', ' and '.join([', '.join(_parts[:-1]), _parts[-1]])
  if len(_parts) > 1 else _parts[0])
m('RqNPowerHi', '%d' % (NU - len(LOW)))
_nlo = int(macro('RcNPowerLoTrig'))
ck('Q2 the recovery chances below the declared level are distinct numbers, '
   'so no single value may be printed beside all of their names; the count '
   'below and the count above partition the quoted exclusions; and every '
   'chance at the trigger amplitude is at most the chance at the discovery '
   'amplitude, which is what makes the trigger reading the conservative one',
   len({round(u['p_trig'], 2) for u in LOW}) == len(LOW)
   and len(LOW) == _nlo and (NU - len(LOW)) + _nlo == NU
   and all(u['p_trig'] <= u['p_conf'] + 1e-12 for u in UNITS),
   '%d below %.0f per cent at the trigger amplitude against %d above; '
   'round 120 says %d below; at the trigger %s'
   % (len(LOW), 100.0 * POWER, NU - len(LOW), _nlo,
      ['%.2f' % u['p_trig'] for u in LOW]))

# ================================================ 3. sigma_excl saturates
# sigma_excl = (T_pers - T_rep)/sqrt(1 + (T_pers/T_star)^2) -> T_star as
# T_pers grows, so on deep repeat coverage it reports the discovery
# significance and nothing about the repeat.
DEEP = [u for u in UNITS if u['t_pers'] > 10.0 * u['t_star']]
_ratio = [u['excl'] / u['t_star'] for u in DEEP]
if DRIVE == 4:                           # Q4 of the old kind: no saturation
    DEEP = [dict(u, excl=0.3 * u['t_star']) for u in DEEP]
    _ratio = [u['excl'] / u['t_star'] for u in DEEP]
m('RqSatN', '%d' % len(DEEP))
m('RqSatRatioLo', '%.2f' % min(_ratio))
m('RqSatRatioHi', '%.2f' % max(_ratio))
_top = max(UNITS, key=lambda u: u['excl'])
m('RqSatStar', tname(_top['star']))
m('RqSatExcl', '%.2f' % _top['excl'])
m('RqSatTStar', '%.2f' % _top['t_star'])
# The excluded amplitude fraction itself is \RcFracMin, \RcFracMed and
# \RcFracMax in round 120 and is not repeated here.
_f5 = [u['f5'] for u in UNITS]
ck('Q3 sigma_excl saturates at the discovery significance on deep repeat '
   'coverage, so it is not a statement about the repeat, while the excluded '
   'amplitude fraction this round agrees with round 120 to the digit printed',
   bool(DEEP) and all(abs(r - 1.0) <= SAT_TOL for r in _ratio)
   and '%.2f' % med(_f5) == macro('RcFracMed')
   and '%.3f' % min(_f5) == macro('RcFracMin')
   and '%.2f' % max(_f5) == macro('RcFracMax'),
   '%d units with T_pers > 10 T_star; sigma_excl/T_star %.3f-%.3f; '
   'largest exclusion %.2f against its own T_star %.3f; f5 %.3f/%.2f/%.2f '
   'against round 120 %s/%s/%s'
   % (len(DEEP), min(_ratio), max(_ratio), _top['excl'], _top['t_star'],
      min(_f5), med(_f5), max(_f5), macro('RcFracMin'), macro('RcFracMed'),
      macro('RcFracMax')))

# ======================================== 4. the two attributed crossings
def own_window(row):
    """The window a crossing sits in, and the noise its own on-source time
    supports.  A window extracted twice on this host appears in both the
    delivered catalogue and the re-extraction, and the two disagree; the row
    whose integration time matches the statistic the ledger carries is the
    one the exclusion must use.  Keyed on block and frequency."""
    cands = []
    for r in BYEB.get(row['eb'], []):
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if lo <= row['freq'] <= hi:
            cands.append(('delivered', float(r['rms_mJy']),
                          float(r['on_source_s']), r['system_id']))
    for r in REP:
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if r['eb'] == row['eb'] and lo <= row['freq'] <= hi:
            cands.append(('re-extracted', float(r['rms_mJy_repaired']),
                          float(r['on_source_s_repaired']), None))
    if not cands:
        return None
    sysid = next((c[3] for c in cands if c[3]), None)
    pick = cands[-1] if row.get('tstar_source') == 'repaired' else cands[0]
    if DRIVE == 5:                       # Q4: the noise of a shorter track
        pick = cands[0]
    return dict(rms=pick[1], ons=pick[2], src=pick[0], sysid=sysid,
                alt=[c for c in cands if c is not pick])


def repeats(row, sysid):
    """Class A windows of other blocks toward the same system covering the
    crossing's stellar-frame frequency, each transported to its own block's
    barycentric term."""
    outl = []
    if sysid is None:
        return outl
    fs, vs = row['frame']['f_stellar'], row['frame']['v_sys']
    for r in BYSYS.get(sysid, []):
        if r['eb'] == row['eb'] or r['search_class'] != 'A':
            continue
        vb = BARY.get('%s|%.6f' % (r['eb'], round(float(r['flo_GHz']), 6)))
        here = fs / (1.0 + vs / C_KMS) / (1.0 - (vb or 0.0) / C_KMS)
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        cw = float(r['chanw_Hz']) / 1e9
        if lo - 0.5 * cw <= here <= hi + 0.5 * cw:
            outl.append(r)
    return outl


PAIR = {}
for row in ROWS:
    if not row['attributed'] or not row.get('line_coincident'):
        continue
    ow = own_window(row)
    if ow is None:
        continue
    reps = repeats(row, ow['sysid'])
    if not reps:
        continue
    best = min(reps, key=lambda r: float(r['rms_mJy']))
    t_pers = float(row['tstar']) * ow['rms'] / float(best['rms_mJy'])
    t_rep = float(best['star_snr'])
    denom = math.sqrt(1.0 + (t_pers / float(row['tstar'])) ** 2)
    t0 = MJD.get(row['eb'])
    dts = sorted(abs(MJD[r['eb']] - t0) for r in reps
                 if t0 is not None and r['eb'] in MJD)
    PAIR[row['eb']] = dict(
        row=row, ow=ow, n=len(reps), t_pers=t_pers, t_rep=t_rep,
        excl=(t_pers - t_rep) / denom, best=best,
        span=dts[-1] if dts else None,
        star_lo=min(float(r['star_snr']) for r in reps),
        star_hi=max(float(r['star_snr']) for r in reps),
        ctrl_lo=min(float(r['ctrl_max_snr']) for r in reps),
        ctrl_hi=max(float(r['ctrl_max_snr']) for r in reps),
        nge_hi=max(int(r['n_ctrl_ge_star']) for r in reps),
        rms_lo=min(float(r['rms_mJy']) for r in reps),
        rms_hi=max(float(r['rms_mJy']) for r in reps),
        ons_lo=min(float(r['on_source_s']) for r in reps),
        ons_hi=max(float(r['on_source_s']) for r in reps))

HR = [p for p in PAIR.values() if p['row']['star'].startswith('HR 1010')][0]
AJ = [p for p in PAIR.values()
      if p['row']['star'].startswith('ALMA J1537')][0]
for tag, p in (('Hr', HR), ('Aj', AJ)):
    r = p['row']
    # ★ The frame is NAMED and not assumed.  One of these two is a
    # background source with no measured systemic velocity, so the frequency
    # printed for it is the barycentric one and must not be called a stellar
    # rest frequency.  The word is read out of the frame record.
    m('Rq%sFrame' % tag,
      'barycentric' if p['row']['frame']['v_sys'] == 0.0
      and 'background' in p['row']['frame']['v_sys_src'] else 'stellar-frame')
    m('Rq%sStar' % tag, tname(r['display']))
    m('Rq%sFreq' % tag, '%.4f' % r['frame']['f_stellar'])
    # ★ An ASCII hyphen typesets as a hyphen and not as a minus sign, and
    # this value is set in running text rather than in maths mode.
    m('Rq%sDv' % tag, ('%+.1f' % r['dv_stellar']).replace('-', '$-$'))
    m('Rq%sTStar' % tag, '%.2f' % float(r['tstar']))
    m('Rq%sTPers' % tag, '%.1f' % p['t_pers'])
    m('Rq%sTRep' % tag, '%.1f' % p['t_rep'])
    m('Rq%sExcl' % tag, '%.1f' % p['excl'])
    m('Rq%sNRep' % tag, '%d' % p['n'])
    m('Rq%sRmsLo' % tag, '%.1f' % p['rms_lo'])
    m('Rq%sRmsHi' % tag, '%.1f' % p['rms_hi'])
    m('Rq%sRms' % tag, '%.1f' % p['ow']['rms'])
    m('Rq%sOnsMin' % tag, '%.0f' % (p['ow']['ons'] / 60.0))
    m('Rq%sSpanD' % tag, '%.0f' % (p['span'] or 0.0))
m('RqAjStarLo', '%.1f' % AJ['star_lo'])
m('RqAjStarHi', '%.1f' % AJ['star_hi'])
m('RqAjCtrlLo', '%.1f' % AJ['ctrl_lo'])
m('RqAjCtrlHi', '%.1f' % AJ['ctrl_hi'])
m('RqAjNgeHi', '%d' % AJ['nge_hi'])
m('RqAjCtrlDisc', '%.1f' %
  float([r for r in BYEB[AJ['row']['eb']]
         if min(float(r['flo_GHz']), float(r['fhi_GHz']))
         <= AJ['row']['freq']
         <= max(float(r['flo_GHz']), float(r['fhi_GHz']))][0]['ctrl_max_snr'])
  )

# ★ Q4 -- the check that matters.  The window noise adopted for a twice
# extracted discovery window must be the one its own on-source time
# supports, and the sibling blocks of the same star at the same integration
# time are the external test of it.  The rejected value must FAIL that test,
# or the choice is a preference and not a measurement.
_hr_alt = [a[1] for a in HR['ow']['alt']]
ck('Q4 the noise adopted for the twice-extracted discovery window lies '
   'inside the range its sibling blocks give at the same on-source time, '
   'and the rejected value lies outside it',
   HR['rms_lo'] <= HR['ow']['rms'] <= HR['rms_hi']
   and all(not (HR['rms_lo'] <= a <= HR['rms_hi']) for a in _hr_alt),
   'adopted %.2f mJy over %.0f s (%s); siblings %.2f-%.2f mJy over '
   '%.0f-%.0f s; rejected %s'
   % (HR['ow']['rms'], HR['ow']['ons'], HR['ow']['src'], HR['rms_lo'],
      HR['rms_hi'], HR['ons_lo'], HR['ons_hi'],
      ['%.2f' % a for a in _hr_alt]))

# ======================================= 5. the positive control, read out
import maskso_v414 as _mk
RECUR = _mk.attributed_recurrence(
    ROWS, json.load(open(os.path.join(HERE, 'recurcols_v411.json'))))
ATT = [r for r in ROWS if r['attributed']]
_rec = [r for r in ATT if RECUR.get(_mk.key_of(r), {}).get(
    'verdict') == 'recovered']
_abs = [r for r in ATT if RECUR.get(_mk.key_of(r), {}).get(
    'verdict') == 'absent']
_unt = [r for r in ATT if RECUR.get(_mk.key_of(r), {}).get(
    'verdict') == 'untested']
if DRIVE == 6:                           # Q5: a stage that cannot say no
    _rec = _rec + _abs
    _abs = []
# ★ Nothing is emitted here.  The counts are \MkAttr, \MkAttrRecur,
# \MkAttrExcl and \MkAttrUntest in round 330, and the paper must cite those
# so that a crossing moving between attributed and unattributed moves every
# number with it.  What this round adds is the CHECK that they close.
# ★★★ WHICH KIND OF REAL EMISSION EACH RECOVERY IS.  A recurring circumstellar
# line and a recurring foreground cloud line are both correct positives for
# this stage, and the control is stronger for saying which is which.  The
# classification is NOT made here and NOT typed: it is read out of round 520's
# own product, `masklsr_v520.json`, and joined on the block and the crossing
# frequency -- never on a star name, which is this project's commonest join
# defect.  If that file is absent the build must stop rather than silently
# call every recovery circumstellar.
_clpath = os.path.join(HERE, 'masklsr_v520.json')
if not os.path.exists(_clpath):
    raise SystemExit('masklsr_v520.json is absent: round 520 must be '
                     'generated before this round can split the positive '
                     'control into foreground and circumstellar')
CLOUD = {(c['eb'], round(float(c['freq']), 4))
         for c in json.load(open(_clpath))['cloud_matches']}
if DRIVE == 8:                           # Q7: the foreground set goes missing
    CLOUD = set()


def _ck(r):
    return (r['eb'], round(float(r['freq']), 4))


_rec_cloud = [r for r in _rec if _ck(r) in CLOUD]
_rec_disc = [r for r in _rec if _ck(r) not in CLOUD]
m('RqNRecurCloud', '%d' % len(_rec_cloud))
m('RqNRecurDisc', '%d' % len(_rec_disc))
m('RqRecurCloudStars',
  ' and '.join(sorted({tname(r['display']) for r in _rec_cloud})))
m('RqRecurDiscStars',
  ' and '.join(sorted({tname(r['display']) for r in _rec_disc})))
# ★ The two attributed crossings that are NOT recovered split the same way,
# and the velocity match is what carries each attribution.
m('RqAjCloud', 'yes' if _ck(AJ['row']) in CLOUD else 'no')
m('RqHrCloud', 'yes' if _ck(HR['row']) in CLOUD else 'no')
ck('Q7 the origin of every recovered line is read from round 520 and joined '
   'on block and frequency; the two origins partition the recoveries and '
   'both are represented, so the control cannot be made of one kind only',
   len(_rec_cloud) + len(_rec_disc) == len(_rec)
   and len(_rec_cloud) > 0 and len(_rec_disc) > 0
   and len(CLOUD) == int(macro('LsNCloud')),
   '%d foreground + %d circumstellar of %d recovered; round 520 lists %s '
   'interstellar coincidences and %d were read'
   % (len(_rec_cloud), len(_rec_disc), len(_rec), macro('LsNCloud'),
      len(CLOUD)))

ck('Q5 the positive control is read from the ledger: recovered, absent and '
   'uncovered partition the attributed crossings; at least one attributed '
   'crossing is not recovered, so the stage can return no; and the counts '
   'agree with round 330',
   len(_rec) + len(_abs) + len(_unt) == len(ATT) and len(_abs) > 0
   and '%d' % len(ATT) == macro('MkAttr')
   and '%d' % len(_rec) == macro('MkAttrRecur')
   and '%d' % len(_abs) == macro('MkAttrExcl')
   and '%d' % len(_unt) == macro('MkAttrUntest'),
   '%d recovered + %d absent + %d uncovered against %d attributed; round '
   '330 says %s/%s/%s of %s'
   % (len(_rec), len(_abs), len(_unt), len(ATT), macro('MkAttrRecur'),
      macro('MkAttrExcl'), macro('MkAttrUntest'), macro('MkAttr')))

# ============ 5b. WHERE THE GAS IS, WHICH IS THE WHOLE OF THE MECHANISM
# ★★★★ ONE MECHANISM, AND IT IS MEASURED RATHER THAN ASSERTED.  Two
# foreground sightlines behave oppositely at the phase centre, and "gas
# spread across the field is not recovered as a point source" cannot explain
# both: the gas toward HD 285968 recurs at the star in every covering block,
# and the crossing toward ALMA J1537 was found at the phase centre in the
# block that produced it.  What separates them is not the uv coverage -- the
# covering blocks of both share one array and their synthesised beams agree
# to a few per cent -- but WHERE THE EMISSION LIES relative to the phase
# centre, and the control ring measures that directly in the same map.  So
# the qualitative claim is replaced by the ring statistic and the number of
# control positions that exceed the phase centre, per block.
_META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']


def _beams(ebs):
    v = [_META[e]['s_resolution_arcsec'] for e in ebs if e in _META]
    a = sorted({_META[e]['array'] for e in ebs if e in _META})
    return (min(v), max(v), a) if v else (None, None, a)


def _field(rows):
    """The ring maximum, the phase-centre statistic and the number of control
    positions above it, over a set of catalogue rows."""
    return dict(
        star_lo=min(float(r['star_snr']) for r in rows),
        star_hi=max(float(r['star_snr']) for r in rows),
        ring_lo=min(float(r['ctrl_max_snr']) for r in rows),
        ring_hi=max(float(r['ctrl_max_snr']) for r in rows),
        nge_lo=min(int(r['n_ctrl_ge_star']) for r in rows),
        nge_hi=max(int(r['n_ctrl_ge_star']) for r in rows),
        nctrl=sorted({int(r['n_ctrl']) for r in rows}),
        ebs=[r['eb'] for r in rows])


# the covering windows of the two not-recovered attributed crossings
_aj_disc = [r for r in BYEB[AJ['row']['eb']]
            if min(float(r['flo_GHz']), float(r['fhi_GHz']))
            <= AJ['row']['freq']
            <= max(float(r['flo_GHz']), float(r['fhi_GHz']))]
_aj_rep = _field(AJ['best'] and repeats(AJ['row'], AJ['ow']['sysid']))
_aj_all = _field(_aj_disc + repeats(AJ['row'], AJ['ow']['sysid']))
m('RqAjNgeLo', '%d' % _aj_rep['nge_lo'])
m('RqAjNgeDisc', '%d' % int(_aj_disc[0]['n_ctrl_ge_star']))
_b = _beams(_aj_all['ebs'])
m('RqAjBeamLo', '%.1f' % _b[0])
m('RqAjBeamHi', '%.1f' % _b[1])
m('RqAjArray', ' and '.join(x.replace('m', '\\,m') for x in _b[2]))

# the covering windows of the recovered foreground line, which is the
# positive control nearest the trigger
_cl_rows = []
for r in _rec_cloud:
    ow = own_window(r)
    _cl_rows += [q for q in BYEB[r['eb']]
                 if min(float(q['flo_GHz']), float(q['fhi_GHz'])) <= r['freq']
                 <= max(float(q['flo_GHz']), float(q['fhi_GHz']))]
    _cl_rows += repeats(r, ow['sysid'] if ow else None)
_cl_rows = list({(q['eb'], q['flo_GHz']): q for q in _cl_rows}.values())
# ★ A drive that empties the foreground set must make Q10 FAIL, not make this
# generator crash: an exception is not a verdict, and a drive that cannot
# report is a drive that cannot be shown to fire.
_cl = _field(_cl_rows) if _cl_rows else dict(
    star_lo=0.0, star_hi=0.0, ring_lo=0.0, ring_hi=0.0, nge_lo=0, nge_hi=0,
    nctrl=[], ebs=[])
m('RqCtlNBlock', '%d' % len({q['eb'] for q in _cl_rows}))
m('RqCtlStarLo', '%.1f' % _cl['star_lo'])
m('RqCtlStarHi', '%.1f' % _cl['star_hi'])
m('RqCtlRingLo', '%.1f' % _cl['ring_lo'])
m('RqCtlRingHi', '%.1f' % _cl['ring_hi'])
m('RqCtlNgeLo', '%d' % _cl['nge_lo'])
m('RqCtlNgeHi', '%d' % _cl['nge_hi'])
_bc = _beams(sorted({q['eb'] for q in _cl_rows}))
_spread = (max(_b[1] / _b[0], _bc[1] / _bc[0]) - 1.0
           if _bc[0] else float('inf'))
if DRIVE == 11:                          # Q10: the ring stops leading
    _aj_rep['ring_lo'] = 0.5 * _aj_rep['star_lo']
if not _cl_rows:
    _aj_rep['ring_lo'] = -1.0        # Q10 must be able to say no
ck('Q10 the two foreground sightlines are separated by WHERE the emission '
   'lies and not by the uv coverage: the ring leads the phase centre in '
   'every block covering the crossing that is not recovered and trails it '
   'nowhere, the recovered line leads its own ring in no block, and the '
   'covering blocks of both share one array with beams agreeing to better '
   'than a tenth',
   _aj_rep['ring_lo'] > _aj_rep['star_hi']
   and _cl['ring_lo'] > _cl['star_hi']
   and _aj_rep['nge_lo'] > _cl['nge_hi'] / 2.0
   and len(set(_b[2]) | set(_bc[2])) == 1 and _spread < 0.1,
   'not recovered: ring %.1f-%.1f against %.1f-%.1f at the phase centre, '
   '%d-%d of %s controls above it; recovered: ring %.1f-%.1f against '
   '%.1f-%.1f, %d-%d above; arrays %s, beams %.2f-%.2f and %.2f-%.2f '
   'arcsec (spread %.1f per cent)'
   % (_aj_rep['ring_lo'], _aj_rep['ring_hi'], _aj_rep['star_lo'],
      _aj_rep['star_hi'], _aj_rep['nge_lo'], _aj_rep['nge_hi'],
      _aj_rep['nctrl'], _cl['ring_lo'], _cl['ring_hi'], _cl['star_lo'],
      _cl['star_hi'], _cl['nge_lo'], _cl['nge_hi'],
      sorted(set(_b[2]) | set(_bc[2])), _b[0], _b[1],
      _bc[0] if _bc[0] else -1.0, _bc[1] if _bc[1] else -1.0,
      100.0 * _spread if _spread != float('inf') else -1.0))

# ★★ THE POSITIVE CONTROL NEAREST THE TRIGGER IS ONE SIGHTLINE, AND SAYING SO
# IS A LIMITATION OF THE CONTROL RATHER THAN A DETAIL.  Of the attributed
# crossings carried through the recurrence stage, the two with the lowest
# discovery statistic are exactly the two that are not recovered; every
# recovery sits at \MkAttrRecurTLo or above.
_abs_t = sorted(float(r['tstar']) for r in _abs)
_rec_t = sorted(float(r['tstar']) for r in _rec)
_cloud_t = sorted(float(r['tstar']) for r in _rec_cloud)
_disc_t = sorted(float(r['tstar']) for r in _rec_disc)
m('RqNearTrigN', '%d' % len(_abs))
m('RqNearTrigT', '%.2f' % (max(_abs_t) if _abs_t else 0.0))
m('RqRecurDiscTLo', '%.1f' % (min(_disc_t) if _disc_t else 0.0))
if DRIVE == 12:                          # Q11: a recovery below them
    _rec_t = [0.5 * _abs_t[0]] + _rec_t
ck('Q11 the attributed crossings nearest the trigger are exactly the ones '
   'that are not recovered, and every recovery between the trigger and the '
   'faintest circumstellar one is foreground gas, so the positive control '
   'near the trigger rests on that one sightline',
   bool(_abs_t) and bool(_rec_t) and bool(_cloud_t) and bool(_disc_t)
   and max(_abs_t) < min(_rec_t) and max(_cloud_t) < min(_disc_t),
   'not recovered at T* %s; recovered from %s up over %d crossings; '
   'foreground %s, circumstellar %s'
   % (['%.2f' % t for t in _abs_t],
      ('%.3f' % min(_rec_t)) if _rec_t else 'none', len(_rec_t),
      ('%.2f-%.2f' % (min(_cloud_t), max(_cloud_t))) if _cloud_t else 'none',
      ('%.2f-%.2f' % (min(_disc_t), max(_disc_t))) if _disc_t else 'none'))

# ===================================================== 6. the frame, named
_printed = [('RqHrFreq', HR['row']), ('RqAjFreq', AJ['row'])]
_bad = []
for name, row in _printed:
    want = float(dict(M)[name])
    have = row['frame']['f_topo'] if DRIVE == 7 \
        else row['frame']['f_stellar']
    if abs(want - round(have, 4)) > 5e-5:
        _bad.append((name, want, have))
if DRIVE == 7:
    _bad = [(n, float(dict(M)[n]), row['frame']['f_topo'])
            for n, row in _printed
            if abs(float(dict(M)[n]) - round(row['frame']['f_topo'], 4))
            > 5e-5]
ck('Q6 every frequency this round prints is the stellar-frame one, equal to '
   "the ledger's own f_stellar to the printed precision",
   not _bad, 'mismatches: %s' % _bad)

# ---------------------------------------------------------------- emission
with open(out(OUT), 'w', encoding='utf-8') as fh:
    fh.write('%% GENERATED by recurcond_v416.py -- do not hand-edit.\n')
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
print('permitted displacement %.2f-%.2f km/s (median %.2f) against '
      '+/-%.0f km/s searched' % (min(DVS), max(DVS), med(DVS), SEARCH_HALF))
print('an orbit at 1 au keeps %d of %d inside the cell at the nearest '
      'epoch, %d over the longest baseline, %d at the grid ceiling'
      % (len(_in_near), NU, len(_in_far), len(_in_grid)))
print('HR 1010: T_pers %.1f (was 60.1 on the delivered noise), T_rep <= '
      '%.1f, %.1f sigma' % (HR['t_pers'], HR['t_rep'], HR['excl']))
print('ALMA J1537: T_pers %.1f, T_rep <= %.1f, %.1f sigma; star %.1f-%.1f '
      'against a control ring %.1f-%.1f in every covering block'
      % (AJ['t_pers'], AJ['t_rep'], AJ['excl'], AJ['star_lo'], AJ['star_hi'],
         AJ['ctrl_lo'], AJ['ctrl_hi']))
sys.exit(1 if fail else 0)
