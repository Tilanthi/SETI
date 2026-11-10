#!/usr/bin/env python3
r"""tobs_r34.py -- round 3400.  ROUND 34, R2-1: A WINDOW THAT HOLDS AN UNATTRIBUTED
CROSSING HAS NO UPPER LIMIT AT THE TRIGGER.

EIRP_90 is the power at which nine injected carriers in ten reach the trigger
T = 5 at the stellar position.  In a window that already holds an unattributed
cell at T_obs >= 5, a carrier that only reached T = 5 would not have been told
apart from what is there, so the limit of that window is the power at which
nine carriers in ten reach T >= T_obs.  This file measures that power for every
such window from the EXISTING injection trials, and nothing else:

  * no window that holds an unattributed crossing was itself injected (the
    round-9, round-11 and r29 records carry none of them; AU Mic X319 failed at
    the split in the round-11 campaign), so no window has its own ladder at the
    new threshold;
  * the Class A completeness factor every transferred window carries is the
    POOLED curve of the injected windows (sens_r11.py, the 49 windows, the
    r29 re-injections of the recombined mosaics substituted).  Every injected
    tone stores the statistic it reached at the star (`snr`), and its trigger
    flag is exactly snr >= 5 (T1 asserts it on every tone), so the pooled curve
    at threshold T_obs is the same measurement read at another level: the
    fraction of tones with snr >= T_obs at each injected power, and the
    ninety-per-cent point interpolated exactly as sens_r11._cross does;
  * the window's factor is k(T_obs) / k(5), applied to its completeness
    multiplier in adopted_e90._Rule.mult -- the one definition every
    generator reads -- so the window's deposited p90_mult_adopted and every
    limit, median, count, figure and table built on it carry it.  The linear
    rescaling of the class curve (x T_obs/5) is computed beside it as the
    check: the two agree to within a few per cent on every window (T4), the
    measured one being the smaller at the largest T_obs because the trigger
    statistic carries a noise term that does not scale with the carrier.

THE WINDOWS (frozen in r34inputs/20261108/tobs_crossings_r34.json, checked
against their owners on every build by --summary, T2):
  * the census's unattributed Class A crossings: chance_v414.json
    `observed_rows` (eb, frequency, T at the star) -- \CeObs of them, each the
    largest cell of its window;
  * the unattributed SECONDARY cells (cells_v416.json `secondary`, in_mask
    False) in windows whose own largest cell is attributed: there the largest
    cell outside the mask is the secondary, and that is the window's T_obs.
    Where the largest cell is itself unattributed the window is already listed
    at the larger value;
  * the archival-tail crossings (chance_v414.json `observed_tail`) are in no
    released window and carry no limit; they are counted, not applied.

Two passes, because the census is formed far down the build and the limits far
up it:
  python3 tobs_r34.py                # EARLY (before strata_v411/sens_r11): tobs_r34.json from the frozen list
  python3 tobs_r34.py --summary      # LATE (after chance_v414, cells_v416, numbers_v410, persys_r17):
                                     #   T1-T7, -> numbers/survey_numbers_round3400.tex
  python3 tobs_r34.py --summary --drive N   # N = 1..7: prints FAILED: T<N>, writes nothing, exits 1
  python3 tobs_r34.py --freeze       # (one-off) write the frozen list from chance_v414.json + cells_v416.json

Assertions (all driven):
  T1 every injected tone's trigger flag is snr >= 5, and the pooled curve at
     threshold 5 reproduces sens_r11.json's p90 bit for bit (drive 1)
  T2 the frozen list is the census's: chance_v414 observed_rows and tail,
     cells_v416 unattributed secondaries in attributed-primary windows; the
     primaries number \CeObs (drive 2)
  T3 every listed crossing lies in exactly one released Class A window (tail:
     none), a primary's T_obs is that window's star_snr, and no window is
     listed twice (drive 3)
  T4 every factor is >= 1 and non-decreasing in T_obs, and agrees with the
     linear rescaling T_obs/5 to within LIN_TOL (drive 4)
  T5 adopted_e90 applies exactly these factors: per_window / the record's
     factor-free value is the factor on the listed windows and 1 on every
     other, and the deposited p90_mult_adopted carries it (drive 5)
  T6 a system's limit moves exactly when its best window at the trigger holds
     an unattributed crossing; every move is shallower; and the median, the
     deepest limit and the count at 1e15 W over the bounded systems are
     round 103's (drive 6)
  T7 the printed names, counts and the headline clause are the sets above
     (drive 7)
"""
import collections
import csv
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import adopted_e90 as ae          # noqa: E402

ROUND = 3400
FROZEN = os.path.join(HERE, 'r34inputs', '20261108', 'tobs_crossings_r34.json')
OUT_JSON = os.path.join(HERE, 'tobs_r34.json')
TRIG = 5.0
# T4's agreement between the measured factor and the linear rescaling of the class curve: a tolerance on a
# model comparison, the only chosen number in this file (observed largest difference ~2.3 per cent)
LIN_TOL = 0.05
POSCTRL_AMP = 20.0            # sens_r11.POSCTRL_AMP: a diagnostic rung, not a measurement point
SUMMARY = '--summary' in sys.argv
FREEZE = '--freeze' in sys.argv
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex'
                       % (ROUND, '' if DRIVE is None else '_drive%d' % DRIVE))
OUT, FAIL = [], []


def m(k, v):
    assert k.isalpha() and k not in {x.split('}')[0][13:] for x in OUT}, k
    OUT.append('\\newcommand{\\%s}{%s}' % (k, v))


def ck(label, ok, detail=''):
    print('  %-74s %s  %s' % (label[:74], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


def lo_hi(r):
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    return min(a, b), max(a, b)


# ------------------------------------------------------------------ the injected tones, as sens_r11 pools them
def pooled_tones():
    """{tag: [tone]} exactly as sens_r11.py builds TONE_BY_TAG (round-9 fine units, round-11 extension,
    the recombined round-11 windows replaced by their r29 re-injection, model hann3_399000)."""
    tones = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_tones_r9.json')))
    units = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_units_r9.json')))
    new = json.load(open(os.path.join(HERE, 'r11inputs', 'm3a_r11.json')))
    old_tags = {u['tag'] for u in units if u['cls'] == 'fine'}
    new_tags = sorted(u['tag'] for u in new['units'])
    tb = collections.defaultdict(list)
    for t in tones:
        if not t['outside'] and t['tag'] in old_tags:
            tb[t['tag']].append(dict(amp=t['amp'], trig=bool(t['trig']), snr=float(t['snr'])))
    for t in new['tones']:
        if not t['outside']:
            tb[t['tag']].append(dict(amp=t['amp'], trig=bool(t['trig']), snr=float(t['snr'])))
    ffx = {f['eb'] for f in json.load(open(os.path.join(HERE, 'r8inputs', 'v409', 'fieldfix_v409.json')))}
    mos = sorted(g for g in new_tags if g.rsplit('_spw', 1)[0] in ffx)
    for u in json.load(open(os.path.join(HERE, 'r30inputs', '20261104', 'inject_r29_units.json')))['units']:
        g = u.get('published_tag')
        if u.get('field_injected') and g in mos:
            tb[g] = [dict(amp=t[0], trig=bool(t[4]), snr=float(t[5]))
                     for t in u['models']['hann3_399000']['tones'] if not t[6]]
    return dict(tb)


def _cross(amps, fr, want=0.9):
    """sens_r11._cross, verbatim: where a recovery curve first reaches `want`, linearly interpolated."""
    prev = None
    for a, f in zip(amps, fr):
        if f is None:
            continue
        if f >= want:
            if prev is None:
                return a
            pa, pf = prev
            return pa + (want - pf) * (a - pa) / (f - pf) if f > pf else a
        prev = (a, f)
    return None


TB = pooled_tones()
TAGS = sorted(TB)
AMPS = sorted({t['amp'] for g in TAGS for t in TB[g] if t['amp'] != POSCTRL_AMP})
_BYAMP = {a: [t for g in TAGS for t in TB[g] if t['amp'] == a] for a in AMPS}


def k_at(thr, flag=False):
    """The pooled ninety-per-cent point (in units of the nominal trigger power) at threshold `thr`
    on the stored statistic; flag=True reads the stored trigger flag instead (sens_r11's own curve)."""
    fr = [sum((t['trig'] if flag else t['snr'] >= thr) for t in tt) / len(tt) for a, tt in
          ((a, _BYAMP[a]) for a in AMPS)]
    return _cross(AMPS, fr)


K5 = k_at(TRIG)


# ------------------------------------------------------------------ the frozen crossing list
def census_list():
    """The list as the census owners hold it now (chance_v414.json, cells_v416.json)."""
    ch = json.load(open(os.path.join(HERE, 'chance_v414.json')))
    ce = json.load(open(os.path.join(HERE, 'cells_v416.json')))
    out = [dict(role='primary', eb=o['eb'], freq_GHz=round(float(o['freq']), 7), t_obs=round(float(o['tstar']), 4))
           for o in ch['observed_rows']]
    for s in ce['secondary']:
        if s['in_mask']:
            continue
        # every unattributed secondary is listed; where its window's largest cell is itself an
        # unattributed primary, windows() takes the primary (the larger statistic)
        out.append(dict(role='secondary', eb=s['eb'], freq_GHz=round(float(s['f_topo']), 7),
                        t_obs=round(float(s['T']), 4), window_max=round(float(s['window_max']), 4),
                        star=s['star']))
    for t in ch['observed_tail']:
        out.append(dict(role='tail', eb=t[1], freq_GHz=round(float(t[2]), 7), t_obs=None))
    return dict(n_primary=len(ch['observed_rows']), rows=out)


def windows(cat, lst):
    """{smear_key: (row, t_obs, role)} for the listed crossings; the tail maps to no window."""
    A = [r for r in cat if r['search_class'] == 'A']
    hits, nohit, multi = {}, [], []
    for c in lst['rows']:
        f = c['freq_GHz']
        hh = [r for r in A if r['eb'] == c['eb'] and lo_hi(r)[0] - 1e-6 <= f <= lo_hi(r)[1] + 1e-6]
        if c['role'] == 'tail':
            if hh:
                multi.append(('tail in a released window', c))
            continue
        if len(hh) != 1:
            (nohit if not hh else multi).append((len(hh), c))
            continue
        r = hh[0]
        k = ae.smear_key(r)
        hits.setdefault(k, []).append((r, c['t_obs'], c['role']))
    # a window's T_obs is its largest unattributed cell: a primary beats any secondary in it
    out = {}
    for k, v in hits.items():
        pri = [x for x in v if x[2] == 'primary']
        out[k] = max(pri or v, key=lambda x: x[1])
    return out, hits, nohit, multi


def record(cat, lst):
    W, _h, nohit, multi = windows(cat, lst)
    assert not nohit and not multi, ('crossings that do not map to one released Class A window', nohit, multi)
    rec = {}
    for k, (r, t, role) in sorted(W.items()):
        kt = k_at(t)
        assert kt is not None and t >= TRIG, (k, t)
        rec[k] = dict(star=r['star_name'], system_id=r['system_id'], eb=r['eb'], t_obs=t, role=role,
                      k_trig=K5, k_tobs=kt, factor=kt / K5, linear=t / TRIG)
    return rec


CAT = ae.catalogue(HERE)

if FREEZE:
    lst = census_list()
    os.makedirs(os.path.dirname(FROZEN), exist_ok=True)
    lst.update(generated_by='tobs_r34.py --freeze', sources=['chance_v414.json observed_rows/observed_tail',
                                                              'cells_v416.json secondary (in_mask False)'])
    json.dump(lst, open(FROZEN, 'w'), indent=1, sort_keys=True)
    print('tobs_r34 --freeze: %d rows -> %s' % (len(lst['rows']), FROZEN))
    raise SystemExit(0)

LST = json.load(open(FROZEN))
REC = record(CAT, LST)

if not SUMMARY:
    # EARLY pass: the record adopted_e90 reads.  Hard assertions only; the driven clauses are --summary's.
    assert all(v['factor'] >= 1.0 for v in REC.values())
    json.dump(dict(generated_by='tobs_r34.py', round=ROUND, k_trig=K5, n_tags=len(TAGS), amps=AMPS,
                   basis='pooled Class A injection trials re-read at threshold T_obs (no listed window was injected)',
                   windows=REC), open(OUT_JSON, 'w'), indent=1, sort_keys=True)
    print('tobs_r34: %d windows, factors %.4f..%.4f -> tobs_r34.json'
          % (len(REC), min(v['factor'] for v in REC.values()), max(v['factor'] for v in REC.values())))
    raise SystemExit(0)

# ================================================================== --summary: the driven clauses
import posflag_r31 as pf          # noqa: E402
import star_alias                 # noqa: E402

print('tobs_r34 --summary')
# ---- T1
SENS = json.load(open(os.path.join(HERE, 'sens_r11.json')))
_k5 = K5 if DRIVE != 1 else k_at(4.9)
_badflag = sum(1 for g in TAGS for t in TB[g] if t['trig'] != (t['snr'] >= TRIG))
ck('T1 every injected tone triggers exactly where its stored statistic is >= 5, and the pooled curve at 5 '
   'is sens_r11\'s p90 bit for bit',
   _badflag == 0 and _k5 == SENS['p90'] and k_at(TRIG, flag=True) == SENS['p90'] and len(TAGS) == SENS['n_injected'],
   '%d tones disagree; k(5) %.12g vs sens_r11 %.12g; %d windows (%d)'
   % (_badflag, _k5, SENS['p90'], len(TAGS), SENS['n_injected']))

# ---- T2
NOW = census_list()
_fz = sorted((c['role'], c['eb'], c['freq_GHz'], c['t_obs']) for c in LST['rows'])
_nw = sorted((c['role'], c['eb'], c['freq_GHz'], c['t_obs']) for c in NOW['rows'])
if DRIVE == 2:
    _fz = _fz[1:]
_ceobs = int(ae._texval('CeObs', HERE))
_npri = sum(1 for c in _fz if c[0] == 'primary')
ck('T2 the frozen list is the census the owners hold now, and its primaries number \\CeObs',
   _fz == _nw and _npri == _ceobs == NOW['n_primary'],
   '%d frozen vs %d now (%d differ); %d primaries, \\CeObs %d'
   % (len(_fz), len(_nw), len(set(_fz) ^ set(_nw)), _npri, _ceobs))

# ---- T3
W, HITS, NOHIT, MULTI = windows(CAT, LST)
_pri_ok = all(abs(float(r['star_snr']) - t) < 5e-4 for k, (r, t, role) in W.items() if role == 'primary')
_dup = [k for k, v in HITS.items() if sum(1 for x in v if x[2] == 'primary') > 1]
_ntail = sum(1 for c in LST['rows'] if c['role'] == 'tail')
if DRIVE == 3:
    _dup = ['drive']
ck('T3 each crossing lies in one released Class A window (the tail in none); a primary\'s T_obs is its '
   'window\'s star_snr; no window holds two primaries',
   not NOHIT and not MULTI and _pri_ok and not _dup and len(W) == len(REC),
   '%d windows (%d primary, %d secondary-only), %d tail crossings in no released window; dup %s'
   % (len(W), sum(1 for v in W.values() if v[2] == 'primary'), sum(1 for v in W.values() if v[2] != 'primary'),
      _ntail, _dup))

# ---- T4
_fac = sorted((v['t_obs'], v['factor'], v['linear']) for v in REC.values())
if DRIVE == 4:
    _fac[0] = (_fac[0][0], 0.99, _fac[0][2])
_mono = all(b[1] >= a[1] - 1e-15 for a, b in zip(_fac, _fac[1:]))
_lindev = max(abs(f / lin - 1.0) for _t, f, lin in _fac)
ck('T4 every factor is >= 1, non-decreasing in T_obs, and within %.0f per cent of the linear rescaling '
   'T_obs/5' % (100 * LIN_TOL),
   all(f >= 1.0 for _t, f, lin in _fac) and _mono and _lindev <= LIN_TOL,
   'T_obs %.3f..%.3f: factor %.4f..%.4f, linear %.4f..%.4f'
   % (_fac[0][0], _fac[-1][0], min(x[1] for x in _fac), max(x[1] for x in _fac),
      min(x[2] for x in _fac), max(x[2] for x in _fac)) + '; largest difference %.2f per cent' % (100 * _lindev))

# ---- T5 adopted_e90 applies them, and the deposit carries them
E = ae.per_window(CAT, HERE)
RULE = ae._Rule(HERE)
_fx = {id(r): REC[ae.smear_key(r)]['factor'] if ae.smear_key(r) in REC else 1.0 for r in CAT}
if DRIVE == 5:
    _fx[id(CAT[0])] = 1.5
_napp = sum(1 for r in CAT if ae.smear_key(r) in RULE.tobs)
_mult_bad = [r for r in CAT if abs(ae.mult_of(r, HERE) /
                                    (RULE.m_a if r['search_class'] == 'A' else ae.multiplier_b(HERE))
                                    / RULE.resp['%s%d' % (r['search_class'], int(r['n_chan_avg']))]
                                    / _fx[id(r)] - 1.0) > 1e-12]
# Class A only: a Class B row's deposited factor is the unrounded campaign value and mult_of's default is the
# macro layer's two-decimal one (senscal_r23b X3 pins that difference); no Class B window carries a T_obs factor
_dep_bad = [r for r in CAT if r['search_class'] == 'A'
            and abs(float(r['p90_mult_adopted']) / ae.mult_of(r, HERE) - 1.0) > 1e-9]
ck('T5 adopted_e90 applies exactly these factors, and the deposited p90_mult_adopted carries them',
   _napp == len(REC) and not _mult_bad and not _dep_bad,
   '%d of %d applied; %d rows off the factor; %d deposited rows stale'
   % (_napp, len(REC), len(_mult_bad), len(_dep_bad)))

# ---- T6 the systems
E0 = {k: v / _fx_v for k, v, _fx_v in ((id(r), E[id(r)], (REC[ae.smear_key(r)]['factor']
                                                           if ae.smear_key(r) in REC else 1.0)) for r in CAT)}
B1, _l1 = ae.best_by_system(CAT, E)
B0, _l0 = ae.best_by_system(CAT, E0)
MOVED = sorted(s for s in B1 if abs(B1[s][1] / B0[s][1] - 1.0) > 1e-12)
AT_CROSS = sorted(s for s in B0 if ae.smear_key(B0[s][0]) in REC)
if DRIVE == 6:
    MOVED = MOVED[1:]
P1 = sorted(v for s, (r, v) in B1.items() if not pf.is_cond(s))
P0 = sorted(v for s, (r, v) in B0.items() if not pf.is_cond(s))


def sci(x, nd=1):
    e = int(math.floor(math.log10(x)))
    return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)


_n15 = sum(1 for v in P1 if v <= 1e15)
_hl = (sci(st.median(P1)) == ae._texval('EirpNinetySysMedA', HERE)
       and sci(P1[0]) == ae._texval('EirpNinetySysLoA', HERE)
       and _n15 == int(ae._texval('NSysEfifteen', HERE)) and len(P1) == int(ae._texval('NSysALimSum', HERE)))
ck('T6 a limit moves exactly where the best window at the trigger holds an unattributed crossing, always '
   'shallower; the summaries are round 103\'s',
   MOVED == AT_CROSS and all(B1[s][1] > B0[s][1] for s in MOVED) and _hl,
   'moved %s; at a crossing %s; median %.4g -> %.4g, count %d -> %d'
   % ([star_alias.designation(s, tex=False) for s in MOVED], len(AT_CROSS), st.median(P0), st.median(P1),
      sum(1 for v in P0 if v <= 1e15), _n15))

# ---- the macros
WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']


def word(n):
    return WORDS[n] if n < len(WORDS) else '%d' % n


def names(ss):
    nn = [star_alias.designation(s).replace(' ', '~') for s in ss]
    return nn[0] if len(nn) == 1 else ', '.join(nn[:-1]) + ' and ' + nn[-1]


MOVED_S = sorted(MOVED, key=lambda s: B1[s][1])
SUMSYS = [s for s in MOVED_S if not pf.is_cond(s)]
SWITCH = [s for s in MOVED_S if B1[s][0] is not B0[s][0]]
_shift = {s: B1[s][1] / B0[s][1] - 1.0 for s in MOVED_S}
_smax = max(MOVED_S, key=lambda s: _shift[s]) if MOVED_S else None
_med0, _med1 = st.median(P0), st.median(P1)
_n150 = sum(1 for v in P0 if v <= 1e15)
if sci(_med0) == sci(_med1) and _n150 == _n15:
    clause = r'leaves the median system limit and the count of systems at $10^{15}$\,W unchanged'
else:
    clause = (r'moves the median system limit from $%s$ to $%s$\,W and the count at $10^{15}$\,W from %d to %d'
              % (sci(_med0), sci(_med1), _n150, _n15))
if DRIVE == 7:
    SUMSYS = MOVED_S
_nwin = len(REC)
_nsec = sum(1 for v in REC.values() if v['role'] != 'primary')
m('XwNWin', '%d' % _nwin)
m('XwNWinSec', '%d' % _nsec)
m('XwNWinSecWord', word(_nsec))
m('XwTobsLo', '%.2f' % min(v['t_obs'] for v in REC.values()))
m('XwTobsHi', '%.2f' % max(v['t_obs'] for v in REC.values()))
m('XwFacMaxPct', '%.0f' % (100 * (max(v['factor'] for v in REC.values()) - 1.0)))
m('XwLinDevPct', '%.0f' % math.ceil(100 * _lindev))
m('XwNSys', '%d' % len(MOVED_S))
m('XwNSysWord', word(len(MOVED_S)))
m('XwSysNames', names(MOVED_S) if MOVED_S else 'none')
m('XwNSysSum', '%d' % len(SUMSYS))
m('XwNSysSumWord', word(len(SUMSYS)))
m('XwShiftMaxPct', ('%.0f' % (100 * _shift[_smax])) if _smax else '--')
m('XwShiftMaxName', star_alias.designation(_smax).replace(' ', '~') if _smax else 'none')
_smaxs = max(SUMSYS, key=lambda s: _shift[s]) if SUMSYS else None
m('XwShiftMaxSumPct', ('%.0f' % (100 * _shift[_smaxs])) if _smaxs else '--')
m('XwShiftMaxSumName', star_alias.designation(_smaxs).replace(' ', '~') if _smaxs else 'none')
m('XwSwitchNames', names(SWITCH) if SWITCH else 'none')
m('XwNSwitch', '%d' % len(SWITCH))
m('XwHeadlineClause', clause)
m('XwMark', r'$^{\|}$')
ck('T7 the printed names and counts are the sets: the summaries\' movers exclude the position-conditional '
   'systems, and a switched system is one whose best window changes',
   SUMSYS == [s for s in MOVED_S if not pf.is_cond(s)] and len(SWITCH) == sum(
       1 for s in MOVED_S if ae.smear_key(B1[s][0]) != ae.smear_key(B0[s][0]))
   and ('unchanged' in clause) == (sci(_med0) == sci(_med1) and _n150 == _n15),
   'movers %d (%d in the summaries), switched %s' % (len(MOVED_S), len(SUMSYS), SWITCH))

if FAIL:
    print('\nFAILED: %s' % '; '.join(FAIL))
    raise SystemExit(1)
if DRIVE is not None:
    print('drive %d did not fire' % DRIVE)
    raise SystemExit(0)
hdr = ['%% GENERATED by tobs_r34.py --summary (round %d) -- do not hand-edit.' % ROUND,
       '% R2-1: the limits of the windows that hold an unattributed crossing, at the crossing\'s own statistic.']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
json.dump(dict(generated_by='tobs_r34.py --summary', round=ROUND, moved={
    s: dict(before=B0[s][1], after=B1[s][1], eb_before=B0[s][0]['eb'], eb_after=B1[s][0]['eb'],
            position_conditional=pf.is_cond(s)) for s in MOVED_S},
    median_before=_med0, median_after=_med1, n1e15_before=_n150, n1e15_after=_n15),
    open(os.path.join(HERE, 'tobs_r34_summary.json'), 'w'), indent=1, sort_keys=True)
print('tobs_r34 --summary: %d macros -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
