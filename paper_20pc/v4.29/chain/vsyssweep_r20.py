#!/usr/bin/env python3
r"""Round 930: every adopted systemic velocity against every barycentric
correction of the blocks its star was observed in.

WHY THIS FILE EXISTS

    Appendix D.5 records that one star's systemic velocity, +4.55 km/s,
    is the barycentric correction at its epoch, +4.5161 km/s, and calls the
    agreement a coincidence.  Agreement to 0.03 km/s between a catalogued
    radial velocity and an epoch-dependent projection of the Earth's motion
    is also exactly what a field populated from the wrong variable looks
    like, and the appendix cited no source for the velocity.  Two things
    close that: the catalogue and the value are named in the text, and the
    comparison is made for EVERY star and EVERY block rather than for the
    one row where it happened to be noticed.

WHAT IS SWEPT

    Every star that carries an adopted systemic velocity in the frame chain
    (`maskframe_v411.vsys`), against

      * the barycentric term of every window of every execution block in
        which that star was observed, as the released catalogue lists them
        (`maskframe_v411.vbary`), and
      * the barycentric term of the discovery block and of every repeat
        block of the recurrence inventory, which the catalogue does not
        hold, read from the inventory's own `v_corr_kms`.

    The companion of the one close pair is observed in its primary's block
    and is counted under the primary's name in the per-window census, so its
    windows are resolved through the primary's catalogue rows and its own
    systemic velocity.

WHAT THE SWEEP FINDS (and the assertions that make it a measurement)

    W1  the sweep is not vacuous: it compares more than a thousand
        (star, block, window) triples, every star it compares carries a
        velocity from a declared source, and every star with an adopted
        velocity is compared in at least one block
    W2  exactly one agreement within 0.1 km/s exists in the whole survey,
        it is the row the appendix names, and the next closest separation
        anywhere is larger than that tolerance
    W3  the agreement is a coincidence and not a copied field: the two
        values differ by more than the catalogued uncertainty of the
        velocity, the block's own windows carry more than one barycentric
        value while the systemic velocity is one number, and the two come
        from different frozen inputs
    W4  nothing rests on it: carried through the same frame chain, the
        primary's independently catalogued velocity leaves the crossing
        inside the same line mask, so the disposition is the same under
        either value

Usage: vsyssweep_r20.py [--drive N]   (drives 1-4, one per assertion)
"""
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ v4.23: ROUND 20'S FALLBACK PATTERN.  A bare absolute pin into
# another version directory broke the build in round 20 when that
# directory was deleted, and `cleanregen.py` cannot see a
# cross-version dependency because the predecessor is always there
# while it runs.  `verpin.py` now gates every such pin.
PAPER = os.environ.get(
    'V420',
    HERE if os.path.exists(os.path.join(HERE, 'maskframe_v411.py'))
    else '/workspace/SETI/paper_20pc/v4.20')
sys.path.insert(0, PAPER)
import maskframe_v411 as mf                                  # noqa: E402

# ★ ROUND RENUMBERED 910 -> 930 BY THE INTEGRATOR: `r20-confirm` holds
# 910-914 (ROUND_CLAIMS_R20.md, 07:55) and `confirm_r20.py` is in the tree
# on 910; `linerecur_r20.py` is on 920.  Three generators claimed 910 in
# three queue files this round -- the same collision round 19 had at 840.
ROUND = 930
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SUF = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUTJ = os.path.join(HERE, 'vsyssweep_r20%s.json' % SUF)

TOL = 0.1                       # km/s, the tolerance the sweep reports at
C_KMS = mf.C_KMS

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-58s %s  %s' % (name[:58], 'PASS' if cond else 'FAIL', detail))


# ------------------------------------------------------------------ inputs
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'), encoding='utf-8')))
REC = json.load(open(os.path.join(PAPER, 'r10inputs', 'recur_v411.json'),
                     encoding='utf-8'))['crossings']
LED = json.load(open(os.path.join(PAPER, 'ledger.json'),
                     encoding='utf-8'))['rows']
SIM = json.load(open(os.path.join(HERE, 'r20inputs', 'simbad_rv_r20.json'),
                     encoding='utf-8'))
RV = {r[0]: dict(v=r[1], err=r[2], bib=r[3], qual=r[5]) for r in SIM['rows']}

BYSTAR = {}
for _r in CAT:
    BYSTAR.setdefault(_r['star_name'], []).append(_r)

# ---------------------------------------------------------------- the stars
# Every star the frame chain can give a systemic velocity for.  The ledger's
# own star strings are included so that a star carrying a crossing under a
# second designation is swept too, resolved to the catalogue rows it has.
NAMES = set(BYSTAR)
for _q in LED:
    NAMES.add(_q['star'])

STARS = {}
for nm in sorted(NAMES):
    v, src, bound = mf.vsys(nm)
    if v is None or bound:
        continue                       # no adopted velocity, nothing to sweep
    rows = BYSTAR.get(nm)
    if rows is None:
        # a ledger designation whose windows are catalogued under another
        # name: resolve on the blocks its own crossings were found in
        ebs = {q['eb'] for q in LED if q['star'] == nm}
        rows = [r for r in CAT if r['eb'] in ebs]
    if not rows:
        continue
    STARS[nm] = dict(v_sys=float(v), src=src, rows=rows)

# ------------------------------------------------------- the two comparisons
PAIRS = []                              # (star, eb, label, v_sys, v_bary)
for nm, s in sorted(STARS.items()):
    for r in s['rows']:
        vb, vbsrc = mf.vbary(r['eb'], r['flo_GHz'])
        if vb is None:
            continue
        PAIRS.append(dict(star=nm, eb=r['eb'], win=float(r['flo_GHz']),
                          v_sys=s['v_sys'], v_bary=float(vb),
                          v_sys_src=s['src'], v_bary_src=vbsrc,
                          route='catalogue window'))
LEDKEY = {(q['eb'], round(q['freq'], 4)): q for q in LED}
STALE = []
for cid, c in sorted(REC.items()):
    _v, _src, _bound = mf.vsys(c['star'])
    if _bound:
        continue                       # a bound, not an adopted velocity
    # ★★ THE ADOPTED VELOCITY, NOT THE INVENTORY'S.  The frozen recurrence
    #    inventory carries a systemic velocity of its own, and for some
    #    crossings it is not the adopted one: a zero where the harness had no
    #    value to hand, and one superseded value.  It cannot move the
    #    predicted cell -- the reading is a DIFFERENCE of two barycentric
    #    terms and the systemic velocity cancels out of it to first order --
    #    and W5 measures what is left.  But it must not enter this sweep as
    #    though it were the adopted number.
    _led = LEDKEY.get((c['eb'], round(float(c['freq_GHz']), 4)))
    vs = (_led['frame']['v_sys'] if _led else None)
    if vs is None:
        vs = _v if _v is not None else c.get('v_sys_kms')
    if vs is None:
        continue
    _inv = c.get('v_sys_kms')
    if _inv is not None and abs(_inv - vs) > 1e-6:
        STALE.append((cid, c['star'], _inv, vs, c))
    blocks = [('discovery', c['eb'], c.get('discovery') or {})]
    blocks += [('repeat', b.get('eb'), b) for b in (c.get('blocks') or [])]
    for kind, eb, b in blocks:
        vb = b.get('v_corr_kms')
        if vb is None or eb is None:
            continue
        PAIRS.append(dict(star=c['star'], eb=eb, win=None,
                          v_sys=float(vs), v_bary=float(vb),
                          v_sys_src='recurrence inventory',
                          v_bary_src='recur_v411.json',
                          route='%s block of %s' % (kind, cid)))

if DRIVE == 1:                          # W1: a sweep over almost nothing
    PAIRS = PAIRS[:20]
for p in PAIRS:
    p['d'] = abs(p['v_sys'] - p['v_bary'])
if DRIVE == 2:                          # W2: a second agreement, elsewhere
    PAIRS[0]['d'] = 0.004

HITS = sorted([p for p in PAIRS if p['d'] <= TOL], key=lambda p: p['d'])
REST = sorted([p for p in PAIRS if p['d'] > TOL], key=lambda p: p['d'])


def skey(name):
    """One key per STAR, so that a designation written two ways is not two
    stars.  The companion keeps its own key: the suffix is part of the
    designation and the two components are 10 arcsec apart."""
    return name.replace(' ', '').split('GaiaDR3')[0].lower()


KEYS = {}
for p in PAIRS:
    KEYS.setdefault(skey(p['star']), set()).add(round(p['v_sys'], 6))
NSTAR, NBLOCK = len(KEYS), len({p['eb'] for p in PAIRS})

print('vsyssweep_r20: %d stars with an adopted systemic velocity, %d blocks, '
      '%d comparisons' % (NSTAR, NBLOCK, len(PAIRS)))
for p in HITS:
    print('  AGREES  %-14s %-22s v_sys %+8.4f  v_bary %+9.4f  %.4f km/s  %s'
          % (p['star'], p['eb'], p['v_sys'], p['v_bary'], p['d'], p['route']))
print('  next    %-14s %-22s %.4f km/s'
      % (REST[0]['star'], REST[0]['eb'], REST[0]['d']))

# ------------------------------------------------------------ the named row
# The appendix's row, read from the ledger rather than named here: the
# crossing whose topocentric and stellar-frame frequencies agree most closely.
CANC = sorted([q for q in LED
               if abs(q['freq_stellar'] - q['freq']) * 1e3 < 0.1],
              key=lambda q: abs(q['freq_stellar'] - q['freq']))[0]
CSTAR = CANC['star']
CRV = RV.get(CSTAR.replace(' B', 'B').replace('  ', ' '))
assert CRV is not None, 'no frozen radial velocity for %r' % CSTAR
PRIM = RV['HD 139084']

# the barycentric terms of that block's own windows: a copied field would be
# one number, and these are not
CWIN = sorted({round(mf.vbary(CANC['eb'], r['flo_GHz'])[0], 6)
               for r in CAT if r['eb'] == CANC['eb']
               and mf.vbary(CANC['eb'], r['flo_GHz'])[0] is not None})
DIFF = abs(CANC['frame']['v_sys'] - CANC['frame']['v_bary'])
if DRIVE == 3:                          # W3: the field really was copied
    DIFF = 0.0

# W4: the same crossing through the same chain on the primary's velocity
_fb, _fs = mf.to_stellar(CANC['frame']['f_topo'], CANC['frame']['v_bary'],
                         PRIM['v'])
_name, _frest, _dv_prim = mf.nearest(_fs)
MASK = float(mf.HALF_KMS) if hasattr(mf, 'HALF_KMS') else 50.0
if DRIVE == 4:                          # W4: a disposition that does move
    _dv_prim = 10.0 * MASK

m('VsNStar', '%d' % NSTAR)
m('VsNBlock', '%d' % NBLOCK)
m('VsNComp', '%d' % len(PAIRS))
m('VsTolKms', '%.1f' % TOL)
m('VsNAgree', '%d' % len({(p['star'], p['eb']) for p in HITS}))
m('VsAgreeStar', mf.tname(CANC['display']) if hasattr(mf, 'tname')
  else CANC['display'])
m('VsAgreeKms', '%.4f' % DIFF)
m('VsNextKms', '%.2f' % REST[0]['d'])
m('VsRvErr', '%.2f' % CRV['err'])
m('VsRvRatio', '%.1f' % (DIFF / CRV['err']))
m('VsRvQual', CRV['qual'])
m('VsPrimV', '%+.2f' % PRIM['v'])
m('VsPrimErr', '%.2f' % PRIM['err'])
m('VsPrimDv', '%+.1f' % _dv_prim)
m('VsNWinVBary', '%d' % len(CWIN))

# ----- W5: what the inventory's own stale systemic velocities could do -----
# The predicted cell is f_event (1 - (v_sys - v_here)/c) / (1 - (v_sys -
# v_disc)/c).  The systemic velocity appears in both factors and cancels to
# first order; what survives is of order v_sys x v_bary / c^2.  Measured over
# every repeat block of every crossing whose inventory value is not the
# adopted one.
STALE_HZ, STALE_CH = 0.0, 0.0
for cid, star, inv, adopt, c in STALE:
    f = float(c['freq_GHz']) * 1e9
    vd = float((c.get('discovery') or {}).get('v_corr_kms') or 0.0)
    for b in (c.get('blocks') or []):
        vh = float(b.get('v_corr_kms') or 0.0)

        def _fh(vsv, _f=f, _vd=vd, _vh=vh):
            return _f * (1.0 - (vsv - _vh) / C_KMS) \
                / (1.0 - (vsv - _vd) / C_KMS)
        d = abs(_fh(inv) - _fh(adopt))
        STALE_HZ = max(STALE_HZ, d)
        STALE_CH = max(STALE_CH, d / float(b.get('chanw_Hz') or 488281.25))
if DRIVE == 5:                          # W5: a shift that would matter
    STALE_CH = 0.75
m('VsNStale', '%d' % len(STALE))
m('VsStaleKHz', '%.1f' % (STALE_HZ / 1e3))
m('VsStaleChan', '%.5f' % STALE_CH)

# ------------------------------------------------------------- assertions
ck('W1 the sweep is not vacuous: every star with an adopted systemic '
   'velocity is compared against every block it was observed in, and each '
   'velocity carries a declared source',
   len(PAIRS) > 1000 and NSTAR > 20 and NBLOCK > 100
   and set(map(skey, STARS)) <= set(KEYS)
   and all(len(v) == 1 for v in KEYS.values())
   and all(mf.vsys(nm)[1] for nm in STARS),
   '%d comparisons, %d stars, %d blocks; %d designations, each one velocity'
   % (len(PAIRS), NSTAR, NBLOCK, len({p['star'] for p in PAIRS})))
ck('W2 exactly one agreement within the tolerance exists in the whole '
   'survey, it is the row the appendix names, and the next closest '
   'separation anywhere is outside the tolerance',
   len({(p['star'], p['eb']) for p in HITS}) == 1
   and {p['star'] for p in HITS} == {CSTAR}
   and REST[0]['d'] > TOL,
   'one star, %d windows of one block; next closest %.3f km/s (%s)'
   % (len(HITS), REST[0]['d'], REST[0]['star']))
ck('W3 the agreement is a coincidence and not a copied field: the two '
   'differ by more than the catalogued uncertainty, and the block carries '
   'several barycentric values against one systemic velocity',
   0.0 < DIFF <= TOL and DIFF > CRV['err'] and len(CWIN) > 1
   and CANC['frame']['v_sys'] == CRV['v'],
   '%.4f km/s apart, %.1f times the %.2f km/s catalogue error; %d distinct '
   'barycentric terms in that block; source %s'
   % (DIFF, DIFF / CRV['err'], CRV['err'], len(CWIN), CRV['bib']))
ck('W4 the disposition does not rest on the value: the primary\'s '
   'independently catalogued velocity leaves the crossing inside the same '
   'mask',
   abs(_dv_prim) < MASK and abs(CANC['dv_stellar']) < MASK
   and _name == CANC['frame']['line'],
   '%+.1f km/s on the primary\'s %+.2f km/s against %+.1f on the adopted '
   'value, mask +/-%.0f, same transition %s'
   % (_dv_prim, PRIM['v'], CANC['dv_stellar'], MASK, _name))

ck('W5 the frozen recurrence inventory carries a systemic velocity of its '
   'own, it is not the adopted one everywhere, and it cannot move the '
   'predicted cell: the quantity cancels out of a two-epoch reading',
   STALE_CH < 0.01 and STALE_HZ > 0.0,
   '%d crossings differ, worst %.1f kHz = %.5f of a channel'
   % (len(STALE), STALE_HZ / 1e3, STALE_CH))

# ------------------------------------------------------------------ output
with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('%%%% GENERATED by vsyssweep_r20.py (round %d) -- '
             'do not hand-edit.\n' % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
json.dump(dict(n_star=NSTAR, n_block=NBLOCK, n_comparison=len(PAIRS),
               tolerance_kms=TOL, agreements=HITS, next_closest=REST[0],
               named_row=dict(star=CSTAR, eb=CANC['eb'],
                              v_sys=CANC['frame']['v_sys'],
                              v_bary=CANC['frame']['v_bary'],
                              rv=CRV, primary=PRIM,
                              dv_adopted=CANC['dv_stellar'],
                              dv_on_primary=_dv_prim),
               macros=dict(M), failed=FAIL),
          open(OUTJ, 'w', encoding='utf-8'), indent=1)
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
if FAIL:
    print('FAILED: %s' % ', '.join(f[:40] for f in FAIL))
    sys.exit(1)
