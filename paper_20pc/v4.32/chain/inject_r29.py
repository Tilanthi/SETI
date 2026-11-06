#!/usr/bin/env python3
r"""inject_r29.py -- the completeness factor of EACH WINDOW'S OWN CHANNEL RESPONSE, measured.

THE DEFECT.  The campaign that sets the class factors (`campaign_m3a_v399.py` + `inject_vis_v399.py`, pinned in
`strata_v411.py`) deposited every carrier as a linear split between two channels convolved with the 0.25/0.5/0.25
kernel ON THE DELIVERED GRID.  That is ALMA's response only approximately for a window without online spectral
averaging (N = 1) and not at all for the 115 Class A windows delivered with averaging (114 at N = 2, one at N = 4):
online averaging delivers the mean of N Hann-windowed raw channels, which keeps far more of a carrier in the peak
channel.  `sens_r28.py` estimated the averaged factor from a share-ratio model (1.83 P_trig at N = 2 against 3.03)
and it was stated, not applied, because no carrier had been injected through the averaged response.

THE MEASUREMENT (r29-inject; frozen in r30inputs/20261104/inject_r29_units.json).  27 Class A and 9 Class B
windows in 21 blocks (every averaging mode present: Class A N = 1, 2, 4; Class B N = 1, 2; bands 3-10; 122 kHz to
31 MHz channels; 7 m and 12 m; two recombined mosaics injected in every pointing), each re-calibrated with the v4.29
re-flag patch and recovered through the unchanged extractor and search with the published campaign's ladder,
criterion and scorer.  Each window carries three injection models on one split and one uninjected pass:
  hann3_399000  the published deposition and the published seeds -- the REPRODUCTION;
  exact_399000  the window's own response R_N (inject_vis_r29.py), the SAME tones -- paired with hann3;
  exact_429000  the own response, an independent tone draw.
The factor a window's own response needs is the published class factor times the PAIRED ratio of the pooled
ninety-per-cent points, exact/hann3, of the windows of its class and averaging mode:
    F(class, N) = F_published(class) * rho(class, N),  rho = P90_exact / P90_hann3 on identical tones.
The published level (49 Class A windows; the coarse Class B campaign) is kept and only the response term is
measured here, on identical carriers, so the transfer to the uninjected windows is the published one and the
response correction is a measurement rather than a model.  The direct pooled exact-response point over both tone
draws is reported beside it as the cross-check.

Emits  inject_r29.json                 (read by adopted_e90.py: rho by class and N, with the record behind it)
       response_trials_r30.json        (the trial export, REPRO.md Sec. 6 schema, for the deposit's own program;
                                        NOT inject_trials_r30.json, which is sens_r11.py's class-level export)
       numbers/survey_numbers_round3010.tex
Usage: inject_r29.py [--drive N]   (drives write *_driveN.*, never production)
  --drive 1  one unit's positive control broken                     -> J1 must fail
  --drive 2  one reproduction window's triggers below 4 x S_trig lost -> J2 must fail
  --drive 3  one exact_399000 tone moved to another channel         -> J3 must fail
  --drive 4  rho(A, 2) forced above 1                               -> J4 must fail
  --drive 5  a Class A averaging mode with no measured ratio        -> J5 must fail
  --drive 6  the injector self-test record says "not bit-identical" -> J6 must fail
"""
import argparse
import collections
import csv
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--drive', type=int, default=0)
A = ap.parse_args()
DRIVE = A.drive
SUF = '_drive%d' % DRIVE if DRIVE else ''
REC = os.path.join(HERE, 'r30inputs', '20261104', 'inject_r29_units.json')
AMPS = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0]
POSCTRL = 20.0
fails = []


def ck(label, cond, detail=''):
    print('  %-74s %s' % (label, 'OK' if cond else 'FAIL ' + str(detail)))
    if not cond:
        fails.append(label)


def cross(amps, fr, want=0.9):
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


def p90(tl):
    fr = []
    for a in AMPS:
        tt = [t for t in tl if t[0] == a]
        fr.append(sum(t[4] for t in tt) / len(tt) if tt else None)
    return cross(AMPS, fr)


D = json.load(open(REC))
U = D['units']
if DRIVE == 1:
    U[0]['models']['hann3_399000']['posctrl'] = [0, 16]
if DRIVE == 2:
    # the first single-pointing reproduction window loses every trigger below 4 x S_trig: its point moves to >= 4
    for u in U:
        if u.get('published_tag') and not u.get('field_injected'):
            for t in u['models']['hann3_399000']['tones']:
                if t[0] < 4.0:
                    t[4] = False
            break
if DRIVE == 3:
    U[0]['models']['exact_399000']['tones'][0][1] += 1

# tone rows are [amp, chan_inj, subchan, drift, trig, snr, outside]; a tone outside the searched band is not a trial
# (m3a_tones.py's rule, which built the published per-tone record), and the positive control is not a ladder rung
TONES = {u['tag']: {k: [t for t in v['tones'] if t[0] != POSCTRL and not t[6]] for k, v in u['models'].items()}
         for u in U}
print('inject_r29: %d units, %d blocks' % (len(U), len({u['eb'] for u in U})))

# J1 every unit's positive control, every model, recovers >= 14 of 16 (the published inclusion: sens_r11 keeps the
#    two r9 units at 14/16)
bad = [(u['tag'], k, v['posctrl']) for u in U for k, v in u['models'].items()
       if v['posctrl'][1] == 0 or v['posctrl'][0] / v['posctrl'][1] < 0.875]
ck('J1 every unit recovers its 20x positive control under every model', not bad, bad)

# J2 THE REPRODUCTION.  hann3 at the published seeds, on the re-calibrated (v4.29 re-flag) product of a window the
#    published campaign injected, gives that window's published point to within the tone noise of one window
#    (r27-reflag INJECT: flags move a point inside its own tone bootstrap; 0.10 is the widest 68 % half-width of
#    the published per-window bootstrap); pooled over those windows the two curves cross 0.9 within 3 %.
PUB = D['published']
# ★ a window whose search recombines several pointings is NOT a reproduction case: the published injector phase-rotated
#   every row to the REFERENCE pointing's direction cosines, so in every other pointing its carrier was placed at the
#   wrong position at full amplitude and decorrelated; this campaign injects every pointing at the star (its own
#   direction cosines and primary-beam response).  Those windows are reported separately (J2b), not reproduced.
rep = [u for u in U if u.get('published_tag') and not u.get('field_injected')]
MOSAIC_PUB = [(u['tag'], p90(TONES[u['tag']]['hann3_399000']), PUB[u['published_tag']]['p90'])
              for u in U if u.get('published_tag') and u.get('field_injected')]
devs = []
for u in rep:
    mine = p90(TONES[u['tag']]['hann3_399000'])
    pub = PUB[u['published_tag']]['p90']
    devs.append((u['tag'], mine, pub, abs(mine / pub - 1.0)))
worst = max(devs, key=lambda x: x[3]) if devs else None
pool_mine = p90([t for u in rep for t in TONES[u['tag']]['hann3_399000']])
pool_pub = cross(AMPS, [sum(PUB[u['published_tag']]['rungs'][str(a)][0] for u in rep)
                        / sum(PUB[u['published_tag']]['rungs'][str(a)][1] for u in rep) for a in AMPS])
ck('J2 the published deposition at the published seeds reproduces the published points',
   devs and worst[3] <= 0.10 and abs(pool_mine / pool_pub - 1) <= 0.03,
   'worst %s %.3f vs %.3f; pooled %.4f vs %.4f' % (worst[0], worst[1], worst[2], pool_mine, pool_pub)
   if devs else 'no reproduction window')
N_IDENT = sum(1 for u in rep if u.get('rungs_identical'))
# J2b the published point of a recombined window, against the same deposition injected in every pointing: reported,
#     and required to differ in the direction a mis-placed carrier must (the published point is the HIGHER)
for t, mine, pub in MOSAIC_PUB:
    print('  J2b mosaic %s: published (reference pointing only) %.3f, every pointing at the star %.3f' % (t, pub, mine))
# (equal where the extra FIELD rows are the same pointing, whose direction cosines the reference's equal)
ck('J2b in a recombined window the published point is never the deeper one (its carrier missed any offset pointing)',
   all(pub >= mine - 1e-9 for _, mine, pub in MOSAIC_PUB) and any(pub > mine for _, mine, pub in MOSAIC_PUB),
   MOSAIC_PUB)

# J7 THE PUBLISHED CLASS FACTOR, WITH THE RE-RUN WINDOWS' TONES SUBSTITUTED.  The published pooled point is formed
#    over the 49 injected windows (sens_r11.py: round-9 fine units + round-11 units, tones not outside the band, the
#    positive control excluded).  Replacing each re-run single-pointing window's published tones by this campaign's
#    hann3 tones -- the same carriers through the v4.29 re-calibrated data -- must leave the pooled point inside its
#    published bootstrap interval (the r27-reflag spot check did this for 6 windows: 3.0287 -> 3.0283).
_U9 = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_units_r9.json')))
_T9 = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_tones_r9.json')))
_N11 = json.load(open(os.path.join(HERE, 'r11inputs', 'm3a_r11.json')))
_SENS = json.load(open(os.path.join(HERE, 'sens_r11.json'))) if os.path.exists(
    os.path.join(HERE, 'sens_r11.json')) else None
_old = {u['tag'] for u in _U9 if u['cls'] == 'fine'}
POOL = collections.defaultdict(list)
for t in _T9:
    if not t['outside'] and t['tag'] in _old:
        POOL[t['tag']].append([t['amp'], 0, 0, 0, bool(t['trig']), 0, False])
for t in _N11['tones']:
    if not t['outside']:
        POOL[t['tag']].append([t['amp'], 0, 0, 0, bool(t['trig']), 0, False])
F_POOL = p90([t for g in POOL for t in POOL[g] if t[0] != POSCTRL])
_sub = {u['published_tag']: TONES[u['tag']]['hann3_399000'] for u in rep if u['published_tag'] in POOL}
POOL2 = {g: (_sub[g] if g in _sub else v) for g, v in POOL.items()}
F_SUB = p90([t for g in POOL2 for t in POOL2[g] if t[0] != POSCTRL])
_lo, _hi = ((_SENS['p90_boot']['lo'], _SENS['p90_boot']['hi']) if _SENS else (F_POOL * 0.98, F_POOL * 1.02))
ck('J7 the published class factor is reproduced from the published tones, and with the %d re-run windows\' '
   'tones substituted it stays inside its published interval' % len(_sub),
   abs(F_POOL / D['published_factor_A'] - 1) < 1e-9 and _lo <= F_SUB <= _hi,
   'published tones %.4f (record %.4f); substituted %.4f; interval %.3f-%.3f'
   % (F_POOL, D['published_factor_A'], F_SUB, _lo, _hi))
print('  J7 pooled class factor: published tones %.4f, %d windows re-run substituted %.4f' % (F_POOL, len(_sub), F_SUB))

# J3 PAIRING: the exact_399000 tones are the hann3 tones (channel, sub-channel phase, drift), tone for tone
unpaired = []
for u in U:
    h = [(t[0], t[1], round(t[2], 9), round(t[3], 6)) for t in TONES[u['tag']]['hann3_399000']]
    e = [(t[0], t[1], round(t[2], 9), round(t[3], 6)) for t in TONES[u['tag']]['exact_399000']]
    if sorted(h) != sorted(e):
        unpaired.append(u['tag'])
ck('J3 the paired model carries identical carriers (only the response differs)', not unpaired, unpaired)

# ---- the ratios, by class and averaging mode, with a bootstrap over windows (the sample unit)
GROUPS = collections.defaultdict(list)
for u in U:
    GROUPS[(u['cls'], int(u['navg']))].append(u['tag'])
rng = random.Random(3010)
RES = {}
for (cls, n), tags in sorted(GROUPS.items()):
    def pool(ts, key):
        # a big unit (a 12 m mosaic) carries only the paired pair of models
        return [t for g in ts for t in TONES[g].get(key, [])]
    h, e1 = p90(pool(tags, 'hann3_399000')), p90(pool(tags, 'exact_399000'))
    ed = p90(pool(tags, 'exact_399000') + pool(tags, 'exact_429000'))
    br, bd = [], []
    for _ in range(4000):
        s = [tags[rng.randrange(len(tags))] for _ in tags]
        a, b = p90(pool(s, 'hann3_399000')), p90(pool(s, 'exact_399000'))
        if a and b:
            br.append(b / a)
        c = p90(pool(s, 'exact_399000') + pool(s, 'exact_429000'))
        if c:
            bd.append(c)
    br.sort()
    bd.sort()
    q = (lambda v, p: v[int(p * (len(v) - 1))])
    # a PAIRED TONE bootstrap too (carriers matched by rung and injected channel, which the seed fixes): for a mode
    # sampled by one or two windows a bootstrap over windows has no spread to show, and the tone noise is the
    # honest interval there
    pairs = collections.defaultdict(list)
    for g in tags:
        hk = {(t[0], t[1]): t for t in TONES[g]['hann3_399000']}
        for t in TONES[g]['exact_399000']:
            if (t[0], t[1]) in hk:
                pairs[t[0]].append((hk[(t[0], t[1])], t))
    bt = []
    for _ in range(2000):
        hs, es = [], []
        for a, lst in pairs.items():
            for _k in range(len(lst)):
                x = lst[rng.randrange(len(lst))]
                hs.append(x[0])
                es.append(x[1])
        a_, b_ = p90(hs), p90(es)
        if a_ and b_:
            bt.append(b_ / a_)
    bt.sort()
    per = {g: dict(hann3=p90(TONES[g]['hann3_399000']), exact=p90(TONES[g]['exact_399000']),
                   exact2=p90(TONES[g]['exact_429000']) if 'exact_429000' in TONES[g] else None)
           for g in tags}
    RES[(cls, n)] = dict(n_windows=len(tags), tags=tags, p90_hann3=h, p90_exact_paired=e1, p90_exact_direct=ed,
                         rho=e1 / h, rho_lo=q(br, 0.16) if len(tags) >= 3 else q(bt, 0.16),
                         rho_hi=q(br, 0.84) if len(tags) >= 3 else q(bt, 0.84), rho_lo95=q(br, 0.025),
                         rho_hi95=q(br, 0.975), rho_tone_ci68=[q(bt, 0.16), q(bt, 0.84)],
                         rho_window_ci68=[q(br, 0.16), q(br, 0.84)],
                         interval_basis='windows' if len(tags) >= 3 else 'paired tones', direct_lo=q(bd, 0.16), direct_hi=q(bd, 0.84),
                         n_tones=len(pool(tags, 'hann3_399000')) + len(pool(tags, 'exact_399000'))
                         + len(pool(tags, 'exact_429000')), per_window=per)
    print('  %s N=%d: %2d windows  hann3 %.3f  exact %.3f  rho %.3f [%.3f, %.3f] (tones [%.3f, %.3f])  direct exact %.3f'
          % (cls, n, len(tags), h, e1, e1 / h, RES[(cls, n)]['rho_lo'], RES[(cls, n)]['rho_hi'], q(bt, 0.16),
             q(bt, 0.84), ed))
if DRIVE == 4:
    RES[('A', 2)]['rho'] = 1.05

# J4 PHYSICS: averaging can only concentrate a carrier in the peak channel, so the averaged modes need LESS power
#    than the native one (rho(A,2) < rho(A,1)); and no ratio exceeds the native one's reading by more than its noise
r1, r2 = RES[('A', 1)]['rho'], RES[('A', 2)]['rho']
ck('J4 the averaged response needs less power than the native one, and neither more than the deposited kernel',
   r2 < r1 and r2 < 1.0 and RES[('A', 1)]['rho_lo'] <= 1.0,
   'rho(A,1) %.3f, rho(A,2) %.3f' % (r1, r2))

# J5 every averaging mode of every Class A and Class B window in the catalogue has a measured ratio
CAT = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.99.csv'))))
modes = collections.Counter((r['search_class'], int(r['n_chan_avg'])) for r in CAT)
if DRIVE == 5:
    modes[('A', 8)] = 1
missing = sorted(k for k in modes if k not in RES)
ck('J5 every averaging mode in the catalogue has a measured response ratio', not missing,
   'unmeasured: %s (%s windows)' % (missing, [modes[k] for k in missing]))

# J6 the injector's own self-test: the published deposition is reproduced bit for bit, and the own response is
#    the one the archive's resolution ratios certify (cresp_v401)
st = D['injector_selftest']
if DRIVE == 6:
    st[sorted(st)[0]]['T1_bit_identical'] = False
ck('J6 the injector reproduces the published deposition bit for bit and deposits R_N exactly',
   bool(st) and all(x['T1_bit_identical'] and x['T3_other_seed_differs'] and x['T2_pass'] for x in st.values()),
   {k: (x['T1_bit_identical'], x['T3_other_seed_differs'], x['T2_pass']) for k, x in st.items()})

# ---- the record adopted_e90.py reads, and the macros
F_A = D['published_factor_A']
F_B = D['published_factor_B']
out = dict(generated_by='inject_r29.py', round=3010, record=os.path.relpath(REC, HERE),
           rule='F(class,N) = F_published(class) * rho(class,N), rho = paired exact/hann3 P90 ratio',
           published_factor={'A': F_A, 'B': F_B},
           rho={'%s%d' % k: v['rho'] for k, v in RES.items()},
           rho_ci68={'%s%d' % k: [v['rho_lo'], v['rho_hi']] for k, v in RES.items()},
           factor={'%s%d' % k: (F_A if k[0] == 'A' else F_B) * v['rho'] for k, v in RES.items()},
           groups={'%s%d' % k: {kk: vv for kk, vv in v.items()} for k, v in RES.items()},
           mosaic_published=[dict(tag=t, hann3_every_pointing=a, published=b) for t, a, b in MOSAIC_PUB],
           reproduction=dict(windows=[dict(tag=t, hann3=a, published=b) for t, a, b, _ in devs],
                             pooled_hann3=pool_mine, pooled_published=pool_pub, n_rung_identical=N_IDENT),
           catalogue_modes={'%s%d' % k: v for k, v in modes.items()},
           class_factor_substituted=dict(published_tones=F_POOL, substituted=F_SUB, n_windows=len(_sub)))
if not DRIVE:
    json.dump(out, open(os.path.join(HERE, 'inject_r29.json'), 'w'), indent=1, sort_keys=True)
    # ★ the TRIAL EXPORT in REPRO.md Sec. 6's schema (Ruling R13(d)): every trial of every window and model, in
    #   the order the pooled curves consume them, so the deposit's own program can rebuild every ratio here.
    #   trials = [amp, trig, rank, rec, snr, sub, dr, cw, tspan] (tspan is not recorded per tone: 0, as in round 11)
    _ex = []
    for u in U:
        for k in sorted(u['models']):
            _ex.append(dict(tag=u['tag'], model=k, search_class=u['cls'], n_chan_avg=int(u['navg']),
                            published_tag=u.get('published_tag'), field_injected=bool(u.get('field_injected')),
                            trials=[[t[0], bool(t[4]), bool(t[8]) if len(t) > 8 else None,
                                     bool(t[7]) if len(t) > 7 else None, t[5], t[2], t[3], u['chanw_Hz'], 0.0]
                                    for t in u['models'][k]['tones'] if not t[6]]))
    json.dump(dict(schema='REPRO.md Sec. 6: per window tag, trials[amp,trig,rank,rec,snr,sub,dr,cw,tspan]; here one '
                          'entry per (window, model)',
                   generated_by='inject_r29.py', want=0.9, positive_control_amp=POSCTRL, boot_seed=3010, boot_n=4000,
                   boot_quantiles=[0.16, 0.84], spread_percentiles=None, instrumental=None,
                   reference='rho(class, N) = pooled P90 of model exact_399000 / pooled P90 of model hann3_399000 over '
                             'the windows of that class and online-averaging mode (identical carriers); the factor of a '
                             'window is the class level (sens_r11) times rho; the positive control is not a rung',
                   rho=out['rho'], amps=AMPS, windows=_ex),
              open(os.path.join(HERE, 'response_trials_r30.json'), 'w'), separators=(',', ':'))

W = ['One', 'Two', 'Three', 'Four']
mac = {
    'IjNWin': '%d' % len(U), 'IjNBlk': '%d' % len({u['eb'] for u in U}),
    'IjNWinA': '%d' % sum(1 for u in U if u['cls'] == 'A'),
    'IjNWinB': '%d' % sum(1 for u in U if u['cls'] == 'B'),
    'IjNTone': '{:,}'.format(sum(v['n_tones'] for v in RES.values())),
    'IjNRepro': '%d' % len(rep),
    'IjReproWorstPct': '%.0f' % (100 * worst[3]) if devs else '0',
    'IjNMosaic': '%d' % sum(1 for u in U if u.get('field_injected')),
    'IjNMosaicPub': '%d' % len(MOSAIC_PUB),
    'IjNSub': '%d' % len(_sub),
}
for (cls, n), v in RES.items():
    tag = ('B' if cls == 'B' else '') + 'N' + W[n - 1] if n <= 4 else str(n)
    mac['IjRatio' + tag] = '%.2f' % v['rho']
    mac['IjRatio%sLo' % tag] = '%.2f' % v['rho_lo']
    mac['IjRatio%sHi' % tag] = '%.2f' % v['rho_hi']
    # (the factor itself, class level x this ratio, is printed by sens_r11.py, which owns the class level)
    mac['IjNWin' + tag] = '%d' % v['n_windows']
    mac['IjDirect' + tag] = '%.2f' % v['p90_exact_direct']
for k in mac:
    assert k.isalpha(), k
with open(os.path.join(HERE, 'numbers/survey_numbers_round3010%s.tex' % SUF), 'w') as fh:
    fh.write('%% GENERATED by inject_r29.py -- do not hand-edit.\n')
    for k, v in sorted(mac.items()):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
for f in fails:
    print('FAIL', f)
print('inject_r29: %s%s' % ('FAIL' if fails else 'PASS', ' [drive %d]' % DRIVE if DRIVE else ''))
sys.exit(3 if fails else 0)
