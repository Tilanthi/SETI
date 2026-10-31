#!/usr/bin/env python3
r"""anchor_r18.py -- where along the drifting track the predicted cell is
pinned, and what the exclusions do when that anchor is swept.  Round 804.
Writes `survey_numbers_round804.tex` and `anchor_r18.json`.

WHY THIS EXISTS.  A drifting crossing occupies a track tens of channels
long, not one frequency, and the repeat reading is taken at one cell at one
drift.  The reading therefore depends on the instant within each observation
at which the de-drifted track is pinned to the predicted cell -- start,
midpoint or end -- and the paper never says which.  A different anchor tests
a different carrier.

THE CONVENTION, READ OUT OF THE CODE AND THEN OUT OF THE DATA.  Both the
search statistic and the repeat reading stack the dynamic spectrum along
shifts computed from `t - t.min()`, so the track is pinned at the FIRST
integration of its own observation: the frequency a reading refers to is the
carrier's frequency at the start of that block, and the discovery frequency
means the same thing in its own block.  That is checked here against the
shift vectors the figure data retain -- the first shift is zero and the whole
vector is the rounded drift times the elapsed time -- rather than taken from
the source.

WHAT THE SWEEP IS, EXACTLY.  Changing the anchor by a time dt shifts the
whole track by the drift times dt, so reading at one cell under a different
anchor is identically reading at a DIFFERENT channel under this one.  The
anchor family is therefore the channel interval the track spans, and
sweeping it is a channel sweep at the carried drift.  Two families are
measured:

  * `block`:     pin at a common fraction u of the way through each repeat
                 observation, u = 0 (start, the convention), 0.5 and 1
                 (end), and at every integer channel between;
  * `discovery`: the wider set the referee names, every channel the
                 DISCOVERY track spans, either side of the cell.

HOW FAR IT CAN REACH AT ALL, FOR EVERY CROSSING AND NOT ONLY THE TWO WHOSE
SPECTRA SURVIVE.  The track length is the fitted drift times the dwell, and
every crossing and every repeat block carries both, so the width of the
anchor family is measurable survey-wide even where the spectra are not
retained.  It is then compared with the distance to the NEAREST above-trigger
cell in any covering window, which the widened-window search already
measured: if the family is narrower than that distance, no choice of anchor
anywhere in the survey can turn a non-recovery into a recovery.

Usage: anchor_r18.py [--drive N]
"""
import glob
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.dirname(os.path.abspath(__file__))   # the tree this lives in
ROUND = 804
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
# ★ DERIVED FROM `ROUND`, NEVER TYPED AGAIN.  This literal used to
# carry the round number a second time, and when the round was moved
# off `r18-census`'s claim the constant changed and this did not --
# so this generator silently overwrote another generator's published
# round file.  That is the defect `roundcollide` exists for, and it
# resolves a format-built name, so it would have caught the next one.
OUT = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTJ = os.path.join(HERE, 'anchor_r18%s.json' % SFX)

CKMS = 299792.458
TRIG = 5.0
EV = os.path.join(V, 'r11inputs', 'events')

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-70s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(V, 'numbers/survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


def tname(s):
    s = s.split(' Gaia')[0].strip()
    s = re.sub(r'^HD(\d)', r'HD \1', s)
    s = s.replace('HD14055', 'HD 14055').replace('bet Pic', r'$\beta$~Pic')
    s = s.replace('CP-72', 'CP$-$72').replace('CD-57', 'CD$-$57')
    return s.replace(' ', '~')


META = json.load(open(os.path.join(EV, 'figdata_meta.json')))
REC = json.load(open(os.path.join(V, 'r10inputs',
                                  'recur_v411.json')))['crossings']
RCOL = json.load(open(os.path.join(V, 'recurcols_v411.json')))
LED = json.load(open(os.path.join(V, 'ledger.json')))['rows']
LDQ = {(r['eb'], round(float(r['freq']), 6)) for r in LED if r.get('dq')}


def blocks(c):
    return [b for b in c.get('blocks', []) if not b.get('bad_weight_product')]


# ============================================ 1. THE ANCHOR, SURVEY-WIDE
# The family's width is the track length: |drift| x dwell, in channels and
# as a velocity.  Measured for every reading the recurrence test took, from
# each block's own drift, dwell and channel width.
SPAN, ROWS = [], []
for cid, c in sorted(REC.items()):
    if c['status'] != 'ok':
        continue
    d = c.get('discovery') or {}
    bl = blocks(c)
    if not bl or not d.get('drift_Hz_s'):
        continue
    k = '%s|%.6f' % (c['eb'], float(c['freq_GHz']))
    rc = RCOL.get(k) or {}
    f0 = float(c['freq_GHz']) * 1e9
    dwell = d['t_end_mjdsec'] - d['t_start_mjdsec']
    dch = abs(d['drift_Hz_s']) * dwell / float(d['chanw_Hz'])
    dkms = CKMS * abs(d['drift_Hz_s']) * dwell / f0
    per = []
    for b in bl:
        dw = b['t_end_mjdsec'] - b['t_start_mjdsec']
        per.append(dict(eb=b['eb'],
                        chan=abs(b['drift_Hz_s']) * dw / float(b['chanw_Hz']),
                        kms=CKMS * abs(b['drift_Hz_s']) * dw / f0,
                        sep_h=b['sep_from_discovery_h']))
    row = dict(cid=cid, star=c['star'], eb=c['eb'], freq=float(c['freq_GHz']),
               attributed=bool(c['attributed']),
               withheld=(c['eb'], round(float(c['freq_GHz']), 6)) in LDQ,
               disc_chan=dch, disc_kms=dkms, blocks=per,
               max_chan=max([dch] + [p['chan'] for p in per]),
               max_kms=max([dkms] + [p['kms'] for p in per]),
               n_rep=rc.get('n_rep'), f5=rc.get('f5'), T_rep=rc.get('T_rep'),
               T_pers=rc.get('T_pers'))
    ROWS.append(row)
    SPAN.append(row['max_kms'])

NEAR = float(macro('WdNearKms'))
SPANMAX = max(SPAN)
if DRIVE == 1:                     # A1: a family wider than the gap to the
    SPANMAX *= 12.0                # nearest above-trigger cell
ck('A1 the whole anchor family is narrower than the distance to the nearest '
   'above-trigger cell in any covering window, so no choice of anchor '
   'anywhere in the survey can turn a non-recovery into a recovery',
   SPANMAX < NEAR and len(ROWS) >= int(macro('RcNExcl')),
   'widest family %.1f km/s (median %.1f) over %d crossings and %d readings, '
   'against %.0f km/s to the nearest exceedance'
   % (SPANMAX, sorted(SPAN)[len(SPAN) // 2], len(ROWS),
      sum(len(r['blocks']) for r in ROWS), NEAR))

# ============================ 2. THE CONVENTION, CHECKED AGAINST THE DATA
CONV = []
for cid, mt in sorted(META.items()):
    z = np.load(os.path.join(EV, 'figdata_%s.npz' % cid))
    sh = np.asarray(z['shifts'])
    dt = np.asarray(z['dt'])
    fr = np.asarray(z['freqs'])
    cw = float(z['chanw'])
    sign = 1.0 if fr[-1] >= fr[0] else -1.0
    pred = np.rint(sign * float(mt['drift']) * dt / cw).astype(np.int64)
    CONV.append(dict(cid=cid, zero=int(sh[0]), end=int(sh[-1]),
                     exact=bool(np.array_equal(sh, pred)),
                     dt0=float(dt[0]), sign=sign))
_z = all(q['zero'] == 0 for q in CONV)
if DRIVE == 2:                     # A2: the track pinned somewhere else
    _z = False
ck('A2 the de-drifted track is pinned at the FIRST integration of its own '
   'observation: the first shift is zero, the shift vector is the rounded '
   'drift times the elapsed time throughout, and the track runs away from '
   'the cell from there',
   _z and all(q['exact'] for q in CONV) and all(q['dt0'] == 0.0 for q in CONV)
   and all(q['end'] != 0 for q in CONV),
   '; '.join('%s shifts %d to %d channels' % (q['cid'], q['zero'], q['end'])
             for q in CONV))

# ======================= 3. THE SWEEP, MEASURED WHERE THE SPECTRA SURVIVE
SW = []
for cid, mt in sorted(META.items()):
    z = np.load(os.path.join(EV, 'figdata_%s.npz' % cid))
    rT = np.asarray(z['r_T'], dtype=float)
    rA = np.asarray(z['r_amp'], dtype=float)
    rS = np.asarray(z['r_sig'], dtype=float)
    half = int(z['half'])
    fr = np.asarray(z['freqs'])
    cw = float(z['chanw'])
    sign = 1.0 if fr[-1] >= fr[0] else -1.0
    f0 = float(mt['freq_GHz']) * 1e9
    c = REC[cid]
    bl = blocks(c)
    k = '%s|%.6f' % (c['eb'], float(c['freq_GHz']))
    rc = RCOL[k]
    assert len(bl) == rT.shape[0], (cid, len(bl), rT.shape)
    # the end shift of each repeat block's own track, which is what "pin at
    # the end rather than the start" moves the cell by
    ends = []
    for b in bl:
        dw = b['t_end_mjdsec'] - b['t_start_mjdsec']
        ends.append(int(np.rint(sign * b['drift_Hz_s'] * dw
                                / float(b['chanw_Hz']))))

    def comb(dcols):
        """Inverse-variance combination over the blocks, each read at its own
        channel offset.  Returns (T_rep, n used)."""
        num = den = 0.0
        n = 0
        for j, dd in enumerate(dcols):
            i = half + dd
            if not (0 <= i < rT.shape[1]):
                continue
            a, s = rA[j, i], rS[j, i]
            if not (np.isfinite(a) and np.isfinite(s)) or s <= 0:
                continue
            w = 1.0 / s ** 2
            num += a * w
            den += w
            n += 1
        if den <= 0:
            return None, 0
        return (num / den) / (1.0 / math.sqrt(den)), n

    t0, n0 = comb([0] * len(bl))
    # the published combination is over the same blocks and the same cell
    rel = abs(t0 - rc['T_rep']) / max(abs(rc['T_rep']), 0.05)
    # family 1: a common fraction through each repeat observation
    frac = {}
    for u in (0.0, 0.5, 1.0):
        frac[u] = comb([-int(np.rint(u * e)) for e in ends])[0]
    # the same, every integer channel of each block's own track
    inblock = []
    umax = max(abs(e) for e in ends) or 1
    for q in range(umax + 1):
        u = q / float(umax)
        v, _ = comb([-int(np.rint(u * e)) for e in ends])
        if v is not None:
            inblock.append((u, v))
    # family 2: every channel the discovery track spans, either side
    L = int(np.rint(abs(float(mt['drift']))
                    * (mt['on_source_s'] if False else
                       (mt['t_end_mjd'] - mt['t_start_mjd']) * 86400.0) / cw))
    disc = []
    for dd in range(-min(L, half), min(L, half) + 1):
        v, n = comb([dd] * len(bl))
        if v is not None:
            disc.append((dd, v))
    single = np.nanmax(rT[:, max(0, half - L):half + L + 1])
    tp = rc['T_pers']
    f5_0 = (t0 + TRIG) / tp
    best = max(q[1] for q in disc + inblock)
    SW.append(dict(
        cid=cid, star=c['star'], display=mt['display'], n_rep=len(bl),
        L_disc=L, half=half, ends=ends,
        T_rep_pub=rc['T_rep'], T_rep_zero=t0, rel=rel,
        T_start=frac[0.0], T_mid=frac[0.5], T_end=frac[1.0],
        T_best_block=max(q[1] for q in inblock),
        T_best_disc=max(q[1] for q in disc),
        T_best=best, T_single_max=float(single),
        f5_pub=rc['f5'], f5_zero=f5_0, f5_best=(best + TRIG) / tp,
        df5=(best - t0) / tp, T_pers=tp,
        kms_per_chan=CKMS * cw / f0,
        span_kms=CKMS * L * cw / f0))

_rel = max(q['rel'] for q in SW)
if DRIVE == 3:                     # A3: a combination that is not the
    _rel = 1.0                     # published one
ck('A3 the combination rebuilt from the retained spectra reproduces the '
   'published reading at the published cell, for every block of both '
   'crossings, so the sweep below moves the anchor and nothing else',
   _rel < 0.02 and len(SW) == 2
   and all(q['n_rep'] == RCOL['%s|%.6f'
                              % (REC[q['cid']]['eb'],
                                 float(REC[q['cid']]['freq_GHz']))]['n_rep']
           for q in SW),
   '; '.join('%s %d blocks, T_rep %+.3f against %+.2f published'
             % (q['cid'], q['n_rep'], q['T_rep_zero'], q['T_rep_pub'])
             for q in SW))

WORST = max(SW, key=lambda q: q['df5'])
if DRIVE == 4:                     # A4: a sweep that reaches the trigger
    SW[0]['T_best'] = 6.0
ck('A4 no anchor in either family reaches the trigger, in the combination '
   'or in any single block, so no disposition depends on the anchor even '
   'where the depth of an exclusion does',
   all(q['T_best'] < TRIG and q['T_single_max'] < TRIG for q in SW),
   '; '.join('%s T_rep %+.2f -> %+.2f (start %+.2f, mid %+.2f, end %+.2f), '
             'single block to %+.2f, exclusion %.2f -> %.2f of S'
             % (q['cid'], q['T_rep_zero'], q['T_best'], q['T_start'],
                q['T_mid'], q['T_end'], q['T_single_max'], q['f5_zero'],
                q['f5_best']) for q in SW))

# ★★★★ THE DEPTH DOES MOVE, AND THE CROSSING IT MOVES MOST IS ALREADY
# REPORTED AS UNTESTED.  Maximising over the anchor family is maximising over
# tens of cells, so the reading it returns is positive on average whatever is
# there -- the same objection the paper already makes to the drift-maximised
# reading -- and the honest use of it is as a bound.  Taken that way the
# anchor sweep costs CP-72 2713 its exclusion entirely: nothing below the
# discovery amplitude is ruled out.  That crossing is one of the seven the
# published drift-maximised reading already reports as ruling out nothing,
# and the assertion is that every crossing the sweep makes vacuous is in
# that published set -- if one were not, a disposition would have to move.
VAC = set(json.load(open(os.path.join(V, 'traj_v418.json')))['vacuous'])
_newvac = sorted(q['cid'] for q in SW if q['f5_best'] >= 1.0)
if DRIVE == 6:                     # A6: a crossing the published set misses
    _newvac = _newvac + ['U02']
# ★ r28 (v4.29, Ruling R3): with sulphur monoxide in the mask one of the two
# swept crossings (CP-72 2713, SO 8_8-7_7) is attributed and carries no quoted
# exclusion, so it is not in the published vacuous set either.  The clause
# keeps its non-vacuity (the sweep still empties a crossing) and requires
# every emptied crossing to be reported vacuous OR to carry no exclusion.
_LUN6 = {(r['eb'], round(float(r['freq']), 6)) for r in LED
         if not r['attributed']}
_noexcl = {q['cid'] for q in SW
           if (REC[q['cid']]['eb'], round(float(REC[q['cid']]['freq_GHz']), 6))
           not in _LUN6}
ck('A6 every crossing whose exclusion the anchor sweep empties is already '
   'one of the crossings the published wider reading reports as ruling out '
   'nothing, or carries no quoted exclusion at all, so the sweep changes the '
   'depth of an exclusion and never a disposition',
   set(_newvac) <= (VAC | _noexcl) and bool(_newvac)
   and all(q['f5_best'] <= 1.0 or q['cid'] in (VAC | _noexcl) for q in SW),
   'emptied by the sweep %s against the %d already reported vacuous %s'
   % (_newvac, len(VAC), sorted(VAC)))

# the two families must not be confused: the discovery-track family is the
# wider one and must be at least as generous as the within-block one.
if DRIVE == 5:                     # A5: the narrower family quoted as the
    SW[0]['T_best_disc'] = SW[0]['T_best_block'] - 1.0   # wider one
ck('A5 the discovery-track family is the wider of the two and its maximum '
   'is therefore the one quoted, and the start of the observation -- the '
   'convention in force -- is not the most favourable anchor, so the '
   'quoted exclusions are not the best case of the sweep',
   all(q['T_best_disc'] >= q['T_best_block'] - 1e-9 for q in SW)
   and any(q['T_best'] > q['T_start'] for q in SW),
   '; '.join('%s discovery %+.2f against within-block %+.2f, start %+.2f'
             % (q['cid'], q['T_best_disc'], q['T_best_block'], q['T_start'])
             for q in SW))

# ★★★★ AND THE MEASUREMENT ALREADY EXISTS IN THE PAPER UNDER ANOTHER NAME.
# Appendix C reports the largest value anywhere within +-\WdBandKms km/s of a
# predicted channel AT THE CARRIED DRIFT, which is a scan across frequency at
# one drift -- and that is identically the anchor family, because moving the
# anchor along the track moves the cell in frequency and nothing else.  The
# single-block maximum of the sweep must therefore reproduce \WdBandMax
# exactly, and the retained band must be wide enough to contain the family it
# is being asked to cover.
_bandkms = float(macro('WdBandKms'))
_bandmax = float(macro('WdBandMax'))
_famkms = max(q['span_kms'] for q in SW)
if DRIVE == 7:                     # A7: a sweep that is not that scan
    _bandmax += 0.4
ck('A7 the sweep is the scan across frequency at the carried drift that the '
   'appendix already reports: the largest single-block value it finds '
   'reproduces that figure, and the retained band is wider than the anchor '
   'family of either crossing',
   abs(max(q['T_single_max'] for q in SW) - _bandmax) < 0.01
   and _famkms < _bandkms,
   'sweep %.2f against the published %.2f; family +-%.1f km/s inside the '
   'retained +-%.0f' % (max(q['T_single_max'] for q in SW), _bandmax,
                        _famkms, _bandkms))

# ======================================================= macros
m('AnPinWord', 'the first integration of each observation')
m('AnSpanMaxKms', '%.1f' % SPANMAX)
m('AnSpanMedKms', '%.1f' % sorted(SPAN)[len(SPAN) // 2])
m('AnSpanMaxChan', '%.0f' % max(r['max_chan'] for r in ROWS))
m('AnNCross', '%d' % len(ROWS))
m('AnNRead', '%d' % sum(len(r['blocks']) for r in ROWS))
m('AnNearKms', '%.0f' % NEAR)
m('AnNMeas', '%d' % len(SW))
m('AnMeasStars', ' and '.join(tname(q['star']) for q in SW))
m('AnTBest', '%+.2f' % max(q['T_best'] for q in SW))
m('AnTSingle', '%+.2f' % max(q['T_single_max'] for q in SW))
m('AnFracMove', '%.2f' % max(q['df5'] for q in SW))
m('AnFracFrom', '%.2f' % WORST['f5_zero'])
m('AnFracTo', '%.2f' % WORST['f5_best'])
m('AnWorstStar', tname(WORST['star']))
m('AnChanSpan', '%d' % max(q['L_disc'] for q in SW))
m('AnTrig', '%.0f' % TRIG)
m('AnNVac', '%d' % len([q for q in SW if q['f5_best'] >= 1.0]))
m('AnVacStar', tname([q for q in SW if q['f5_best'] >= 1.0][0]['star'])
  if any(q['f5_best'] >= 1.0 for q in SW) else '--')
m('AnOtherStar', tname([q for q in SW if q['f5_best'] < 1.0][0]['star'])
  if any(q['f5_best'] < 1.0 for q in SW) else '--')
m('AnOtherFrom', '%.2f' % min(q['f5_zero'] for q in SW
                              if q['f5_best'] < 1.0))
m('AnOtherTo', '%.2f' % min(q['f5_best'] for q in SW if q['f5_best'] < 1.0))
m('AnNWideVac', macro('ZtNWideVac'))
m('AnBandKms', macro('WdBandKms'))
m('AnBandMax', macro('WdBandMax'))

json.dump(dict(convention=CONV, survey=ROWS, swept=SW,
               span_max_kms=SPANMAX, near_kms=NEAR),
          open(OUTJ, 'w'), indent=1, default=str)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by anchor_r18.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
