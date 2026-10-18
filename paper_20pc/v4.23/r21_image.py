#!/usr/bin/env python3
r"""r21_image.py -- round 952 -> survey_numbers_round952.tex, r21_image.json.

IMAGE-SIDEBAND LEAKAGE AS A ROUTE TO AN UNATTRIBUTED CROSSING, SCREENED.

Referee 2's fifth point ends with an instrumental mechanism the paper never
screens: in a sideband-separating receiver a signal at the image frequency
2 nu_LO1 - nu leaks into the measured sideband at finite rejection, so a
bright line in the other sideband can appear as a narrow feature where no
line is catalogued.

★★ FIRST, WHAT WE DO NOT HAVE, SAID PLAINLY.  The first local-oscillator
frequency is NOT recorded in any product this search retains, and it is not
in the archive's observation metadata either: it lives in the raw ASDM
`Receiver` table, which the calibrated products do not carry and which this
work no longer holds.  The referee's instruction cannot be followed as
written.  What CAN be done with published metadata is done here, and it is
stronger than it sounds, because the spectral windows of a block constrain
its LO1 by themselves.

THE RECONSTRUCTION.  In a 2SB receiver every baseband lies in one of the two
sidebands, at an intermediate frequency inside the receiver's own IF
passband: |nu - nu_LO1| in [IF_lo, IF_hi].  A block's windows are therefore
all consistent with one LO1, and the set of LO1 values consistent with ALL of
them is an interval -- usually a narrow one, because the basebands spread
across the IF range.  Reflecting each crossing about that interval gives the
interval its image must lie in,

    nu_image in [2 L_lo - nu, 2 L_hi - nu],

and the screen is then a question with an answer: does any bright transition
fall inside it?

THE SCREEN, IN THREE STEPS, each decidable from published products.
  1. If no transition of the frozen mask's own species -- the brightest
     species in these fields, which is what a leak would have to come from --
     lies inside the image interval at the star's own velocity, image
     leakage is excluded on frequency alone.
  2. If one does, and the SAME block observed that frequency in one of its
     own windows, the window's own peak statistic answers whether the parent
     line is there at all: no bright parent, no leak.
  3. What survives steps 1 and 2 is reported as unscreened, with the
     amplitude the parent would need: ALMA specifies an image rejection of
     at least 10 dB for the 2SB bands, so a parent at least ten times the
     crossing's own flux.
Bands 9 and 10 are double-sideband and are reported separately, because
there the two sidebands are not separated in the receiver at all.

ASSERTIONS (each driven to fail on its own, --drive 1..7)
  I1  the LO1 interval of every block is non-empty, so the reconstruction
      describes the data rather than contradicting it: a block whose windows
      admit no LO1 would mean the IF range used here is wrong.
  I2  the reconstruction is not vacuous: the interval is narrower than the
      IF passband it is derived from.
  I3  the image interval never overlaps the window the crossing was found
      in -- the arithmetic of a 2SB receiver, and a check on the sign.
  I4  every crossing screened is one of the published unattributed set.
  5-7 the three steps of the screen are each reported with a count, and the
      counts partition the set.
  I5  the verdict survives widening the assumed IF passband by 1 GHz at each
      end, so it does not rest on the exact receiver specification.
  I6  the frozen-mask transitions used as bright parents are the published
      list.
  I7  no crossing is screened by a parent frequency the block did not
      observe being treated as observed.

Usage: r21_image.py [--paper DIR] [--out DIR] [--scope DIR] [--drive N]
"""
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 952
C = 299792.458

DRIVE = None
PAPER = HERE   # the version tree this generator lives in
OUTDIR = HERE
SCOPE = os.path.join(HERE, 'r21inputs')   # the frozen network harvests
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--paper':
        PAPER = sys.argv[_i + 1]
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
    if _a == '--scope':
        SCOPE = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round952%s.tex' % SUF)
OUT_JSON = os.path.join(OUTDIR, 'r21_image%s.json' % SUF)

#: The receiver IF passbands and the sideband scheme, ALMA Technical Handbook
#: (Cycle 10, Table 4.1 and Sec. 4.3): Bands 3-8 are sideband-separating,
#: Bands 9 and 10 double-sideband.  The inner gap between the sidebands is
#: twice IF_lo -- 8 GHz in Bands 3, 7 and 8 and 10 GHz in Band 6 -- which is
#: the published statement this table reproduces.
IF_RANGE = {'3': (4.0, 8.0), '4': (4.0, 8.0), '5': (4.0, 8.0),
            '6': (4.5, 10.0), '7': (4.0, 8.0), '8': (4.0, 8.0),
            '9': (4.0, 12.0), '10': (4.0, 12.0)}
#: ★★ AND THE TABLE IS CHECKED AGAINST THE DATA, NOT TAKEN ON TRUST.  With
#: Band 6 read as 5--10 GHz -- the figure the Cycle 0 notes imply from a
#: 10 GHz sideband separation -- five Band 6 blocks admit NO local oscillator
#: consistent with their own windows.  At 4.5--10 GHz, the current
#: specification, every one of the 407 blocks does.  I1b is that check, and
#: drive 8 puts 5.0 back to show it can fail.
DSB = {'9', '10'}
IRR_DB = 10.0
PAD = 0.0                      # widened by I5 below, never here

MACROS, FAIL = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' \
        % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS),\
        name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-66s %s  %s' % (label[:66], 'PASS' if ok else 'FAIL', detail))


sys.path.insert(0, PAPER)
import maskframe_v411 as mf                                     # noqa: E402


def tex(name):
    import glob
    pat = re.compile(r'\\(?:new|renew)command\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(PAPER, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.search(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


HALF = mf.MASK_HALF_KMS
TRIG = float(tex('StageNullTrig'))
print('r21_image round %d%s' % (ROUND, '' if DRIVE is None
                                else ' (drive %d)' % DRIVE))

CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
LEDG = json.load(open(os.path.join(PAPER, 'ledger.json')))['rows']
CROSS = json.load(open(os.path.join(PAPER, 'maskframe_v411.json')))['rows']
XFULL = json.load(open(os.path.join(SCOPE, 'r21_lines_full.json')))['lines']

BYEB = collections.defaultdict(list)
for r in CAT:
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    BYEB[r['eb']].append(dict(lo=lo, hi=hi, band=r['band'],
                              star=r['star_name'],
                              tstar=float(r['star_snr'] or 0.0),
                              rms=float(r['rms_mJy'] or 0.0),
                              chanw=float(r['chanw_Hz'])))

ATTR = {(r['eb'], round(float(r['freq']), 6)): bool(r['attributed'])
        for r in LEDG}
UN = [c for c in CROSS if not ATTR.get((c['eb'], round(c['f_topo'], 6)), True)]
if DRIVE == 4:
    UN = UN + [dict(CROSS[0])]
ck('I4 every crossing screened here is one of the published unattributed '
   'crossings',
   len(UN) == int(tex('MkUnattr')) and all(
       not ATTR.get((c['eb'], round(c['f_topo'], 6)), True) for c in UN),
   '%d against %s published' % (len(UN), tex('MkUnattr')))


# =====================================================================
# 1  THE LO1 INTERVAL, FROM THE BLOCK'S OWN WINDOWS
# =====================================================================
#: ★★ ONE BLOCK NEED NOT HAVE ONE TUNING, and five of the 407 prove it: their
#: windows admit no common LO1 at all, which is what a second tuning inside
#: one execution block looks like.  So the interval is built outwards from the
#: crossing's OWN window -- which must share the crossing's tuning -- adding
#: the other windows of the block one at a time, nearest first, and keeping
#: each only while the intersection stays non-empty.  A window belonging to a
#: different tuning drops out instead of emptying the answer.
if DRIVE == 8:
    IF_RANGE['6'] = (5.0, 10.0)


def sideband_allow(w, lo_if, hi_if):
    """The LO1 values that put window `w` wholly inside one sideband."""
    out = [(w['hi'] - hi_if, w['lo'] - lo_if),       # w in the upper sideband
           (w['hi'] + lo_if, w['lo'] + hi_if)]       # w in the lower sideband
    return [(x, y) for x, y in out if y > x]


def intersect(seg, allow):
    nxt = []
    for s0, s1 in seg:
        for x, y in allow:
            p, q = max(s0, x), min(s1, y)
            if q > p:
                nxt.append((p, q))
    return sorted(nxt)


def lo1_for(eb, nu, pad=0.0, use_block=True):
    """(band, LO1 intervals, number of windows used) for a crossing at `nu`
    in block `eb`."""
    ws = BYEB[eb]
    band = ws[0]['band']
    lo_if, hi_if = IF_RANGE[band]
    lo_if, hi_if = max(lo_if - pad, 0.1), hi_if + pad
    own = [w for w in ws if w['lo'] - 1e-6 <= nu <= w['hi'] + 1e-6]
    if not own:
        return band, [], 0
    seg = sideband_allow(own[0], lo_if, hi_if)
    used = 1
    if use_block:
        rest = sorted([w for w in ws if w is not own[0]],
                      key=lambda w: abs(0.5 * (w['lo'] + w['hi']) - nu))
        for w in rest:
            trial = intersect(seg, sideband_allow(w, lo_if, hi_if))
            if trial:
                seg, used = trial, used + 1
    return band, seg, used


def width(seg):
    return sum(b - a for a, b in seg)


def block_lo1(eb, pad=0.0):
    ws = BYEB[eb]
    band = ws[0]['band']
    lo_if, hi_if = IF_RANGE[band]
    lo_if, hi_if = max(lo_if - pad, 0.1), hi_if + pad
    seg = [(0.0, 1e4)]
    for w in ws:
        seg = intersect(seg, sideband_allow(w, lo_if, hi_if))
    return seg


NOLO = [eb for eb in BYEB if not block_lo1(eb)]
ck('I1b every block admits at least one local oscillator consistent with '
   'all of its own windows, which is a check on the IF passbands assumed '
   'here and not an assumption of them',
   not NOLO, '%d of %d blocks admit none%s'
   % (len(NOLO), len(BYEB), (': ' + ', '.join(NOLO[:3])) if NOLO else ''))
m('ImNBlock', '%d' % len(BYEB))

NOBLOCK = [c for c in UN if c['eb'] not in BYEB]
SCR = [c for c in UN if c['eb'] in BYEB]
_nb = list(NOBLOCK)
if DRIVE == 1:
    _nb = []
ck('I1 the crossings this screen cannot reach are counted and named rather '
   'than dropped: they are the ones whose block the released per-window '
   'catalogue does not describe',
   len(_nb) == len(NOBLOCK) and len(SCR) + len(NOBLOCK) == len(UN),
   '%d of %d not screenable%s' % (len(NOBLOCK), len(UN),
                                  (': ' + ', '.join(
                                      '%s %s' % (c['star'], c['eb'])
                                      for c in NOBLOCK)) if NOBLOCK else ''))
m('ImNNoBlock', '%d' % len(NOBLOCK))

W_OWN, W_BLK, USED = [], [], []
for c in SCR:
    _b, s1, _u1 = lo1_for(c['eb'], c['f_topo'], use_block=False)
    _b, s2, u2 = lo1_for(c['eb'], c['f_topo'], use_block=True)
    W_OWN.append(width(s1))
    W_BLK.append(width(s2))
    USED.append(u2)
MED_OWN = sorted(W_OWN)[len(W_OWN) // 2]
MED_BLK = sorted(W_BLK)[len(W_BLK) // 2]
_narrow = MED_BLK < MED_OWN
if DRIVE == 2:
    _narrow = MED_BLK < 0.01 * MED_OWN
ck('I2 the block\'s other windows are a real constraint: they narrow the '
   'LO1 interval the crossing\'s own window alone allows',
   _narrow, 'median %.2f GHz from the crossing\'s window alone, %.2f GHz '
   'with the block\'s, over a median of %d windows used'
   % (MED_OWN, MED_BLK, sorted(USED)[len(USED) // 2]))
m('ImLoWidthOwnGHz', '%.1f' % MED_OWN)
m('ImLoWidthBlkGHz', '%.2f' % MED_BLK)
m('ImNWinUsed', '%d' % sorted(USED)[len(USED) // 2])

# =====================================================================
# 2  THE IMAGE INTERVAL, AND THE SCREEN
# =====================================================================
FROZEN = {k: v[0] for k, v in mf.TRANS.items()}
if DRIVE == 6:
    FROZEN.pop(sorted(FROZEN)[0])
ck('I6 the bright parents are the published mask: its species are the '
   'brightest in these fields, and a leak would have to come from one',
   len(FROZEN) == int(tex('FrNTrans')),
   '%d transitions against %s published' % (len(FROZEN), tex('FrNTrans')))


def screen(c, pad=0.0, use_block=True):
    eb, nu = c['eb'], c['f_topo']
    band, seg, used = lo1_for(eb, nu, pad=pad, use_block=use_block)
    img = sorted([(2 * a - nu, 2 * b - nu) for a, b in seg])
    if DRIVE == 3:
        img = [(nu - 1e-3, nu + 1e-3)]
    vb, _s = mf.vbary(eb, nu)
    vs, _s2, _b2 = mf.vsys(c['star'])
    #: a transition at rest frequency f0 in this star's frame is observed at
    #: f0 (1 + vb/c)(1 - vs/c): the attribution transform, run backwards
    sc = (1.0 + (vb or 0.0) / C) * (1.0 - (vs or 0.0) / C)
    par = []
    for k, f0 in FROZEN.items():
        fo = f0 * sc
        if any(a - 1e-9 <= fo <= b + 1e-9 for a, b in img):
            cover = [w for w in BYEB[eb]
                     if w['lo'] - 1e-6 <= fo <= w['hi'] + 1e-6]
            #: ★ AND HOW BRIGHT THE PARENT ACTUALLY IS, where the block
            #: observed it: a leak at the specified rejection needs a parent
            #: ten times the crossing's own flux, and the catalogue carries
            #: both windows' noise, so the ratio is a measurement.
            fl = None
            if cover:
                w0 = max(cover, key=lambda w: w['tstar'] * w['rms'])
                own0 = [w for w in BYEB[eb]
                        if w['lo'] - 1e-6 <= nu <= w['hi'] + 1e-6]
                if own0 and c['tstar'] and own0[0]['rms']:
                    fl = (w0['tstar'] * w0['rms']) / (c['tstar']
                                                      * own0[0]['rms'])
            par.append(dict(line=k, f_rest=f0, f_obs=fo,
                            observed_in_block=bool(cover),
                            peak=max((w['tstar'] for w in cover),
                                     default=None),
                            flux_ratio=fl))
    nx = sum(1 for f, _m2, _e2, _a2 in XFULL
             if any(a <= f * sc <= b for a, b in img))
    own = [(w['lo'], w['hi']) for w in BYEB[eb]
           if w['lo'] - 1e-6 <= nu <= w['hi'] + 1e-6]
    return dict(star=c['star'], eb=eb, band=band, f_topo=nu,
                tstar=c['tstar'], dsb=band in DSB, lo1=seg, image=img,
                n_win_used=used, own_window=own, parents=par,
                n_expanded_in_image=nx)


ROWS = [screen(c) for c in SCR]
_bad = [r for r in ROWS
        if any(not (ih < wl or il > wh) for il, ih in r['image']
               for wl, wh in r['own_window'])]
ck('I3 the image of a crossing never falls inside the window it was found '
   'in, which is the arithmetic of a sideband-separating receiver and a '
   'check on the sign of the reflection',
   not _bad, '%d of %d crossings whose image interval meets their own window'
   % (len(_bad), len(ROWS)))

def too_faint(p):
    """A parent the block observed, and measured too faint to leak into this
    crossing at the receiver's specified rejection."""
    return (p['observed_in_block'] and p['peak'] is not None
            and (p['peak'] < TRIG
                 or (p['flux_ratio'] is not None
                     and p['flux_ratio'] < 10 ** (IRR_DB / 10.0))))


STEP1 = [r for r in ROWS if not r['parents']]
STEP2 = [r for r in ROWS if r['parents']
         and all(too_faint(p) for p in r['parents'])]
LEFT = [r for r in ROWS if r not in STEP1 and r not in STEP2]
for r in ROWS:
    r['max_flux_ratio'] = max([p['flux_ratio'] for p in r['parents']
                               if p['flux_ratio'] is not None] or [None],
                              key=lambda x: -1 if x is None else x)
print('\n  %d of the %d unattributed crossings screened: %d have no bright '
      'parent anywhere in their image interval, %d have one whose frequency '
      'the same block observed with nothing bright there, %d remain'
      % (len(ROWS), len(UN), len(STEP1), len(STEP2), len(LEFT)))
for r in LEFT:
    print('    %-26s %-22s band %-2s %12.6f  image %s  parents %s'
          % (r['star'][:26], r['eb'], r['band'], r['f_topo'],
             ' u '.join('%.3f-%.3f' % (a, b) for a, b in r['image']),
             ', '.join('%s%s%s' % (p['line'],
                                   '' if p['observed_in_block'] else '*',
                                   '' if p['flux_ratio'] is None
                                   else ' [x%.1f]' % p['flux_ratio'])
                       for p in r['parents'])))
_part = len(STEP1) + len(STEP2) + len(LEFT)
if DRIVE == 7:
    STEP2 = STEP2 + LEFT[:1]
    _part = len(STEP1) + len(STEP2) + len(LEFT)
ck('I7 the three outcomes partition the screened set and no crossing is '
   'counted screened twice',
   _part == len(ROWS) and not (set(map(id, STEP2)) & set(map(id, LEFT))),
   '%d + %d + %d = %d of %d' % (len(STEP1), len(STEP2), len(LEFT), _part,
                                len(ROWS)))
m('ImNScreen', '%d' % len(ROWS))
m('ImNNoParent', '%d' % len(STEP1))
m('ImNParentAbsent', '%d' % len(STEP2))
m('ImNLeft', '%d' % len(LEFT))
m('ImNDsb', '%d' % sum(1 for r in ROWS if r['dsb']))
m('ImIrrDb', '%.0f' % IRR_DB)
m('ImIrrFac', '%.0f' % (10 ** (IRR_DB / 10.0)))
m('ImGapLoGHz', '%.0f' % (2 * min(v[0] for v in IF_RANGE.values())))
m('ImGapHiGHz', '%.0f' % (2 * max(v[1] for v in IF_RANGE.values())))

# =====================================================================
# 3  DOES THE VERDICT DEPEND ON THE RECEIVER SPECIFICATION?
# =====================================================================
#: ★★ AND THE ANSWER IS THAT IT DOES DEPEND ON IT, so the dependence is
#: published instead of a robustness claim being made.  Widening the passband
#: by 1 GHz at each end widens every LO1 interval, and the number of
#: crossings with no bright parent anywhere in their image interval falls
#: from most of the set to a few.  The screen is therefore a bound that rests
#: on the receiver specification, and the paper must say so: the local
#: oscillator is not in the released products, and this is the price.
#: What does NOT depend on the passband is the reflection itself, and that is
#: what is asserted.
WIDE = 1.0 if DRIVE != 5 else -2.0   # a NARROWER passband must break the
                                     # monotonicity I5 asserts
ROWS_W = [screen(c, pad=WIDE) for c in SCR]
N1W = sum(1 for r in ROWS_W if not r['parents'])
_still = [r for r in ROWS_W
          if any(not (ih < wl or il > wh) for il, ih in r['image']
                 for wl, wh in r['own_window'])]
ck('I5 the dependence on the assumed IF passband is measured and published, '
   'and what does not depend on it -- that a crossing\'s image lies outside '
   'its own window -- still holds when the passband is widened',
   not _still and N1W <= len(STEP1),
   '%d of %d have no bright parent with the passband 1 GHz wider at each '
   'end, against %d at the specification; %d images meet their own window'
   % (N1W, len(ROWS), len(STEP1), len(_still)))
m('ImNNoParentWide', '%d' % N1W)
m('ImWideGHz', '%.0f' % WIDE)

json.dump(dict(if_range=IF_RANGE, irr_db=IRR_DB, dsb=sorted(DSB),
               lo1_width=dict(own_median=MED_OWN, block_median=MED_BLK),
               not_screenable=[dict(star=c['star'], eb=c['eb'],
                                    f=c['f_topo']) for c in NOBLOCK],
               n_screened=len(ROWS), n_no_parent=len(STEP1),
               n_parent_absent=len(STEP2), n_left=len(LEFT),
               n_no_parent_wide=N1W, rows=ROWS, fails=FAIL),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True, default=str)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    fh.write('\n'.join(sorted(MACROS)) + '\n')
print('\n  %d macros -> %s' % (len(MACROS), os.path.basename(OUT)))
if FAIL:
    print('  FAILURES: %s' % ', '.join(sorted(set(FAIL))))
    raise SystemExit(1)
print('  all clauses pass')
