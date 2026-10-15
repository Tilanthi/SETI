#!/usr/bin/env python3
r"""round 870 -> survey_numbers_round870.tex: THE RECURRENCE RECOVERY
PROBABILITY MEASURED, FOR EVERY CROSSING THAT CARRIES AN EXCLUSION
(R2 major 3, instructions 1-5; R1-2.4-6).

A carrier at the trigger amplitude was injected into each crossing's discovery
spectra at its own fitted drift and a random sub-channel phase, the drift
search re-run so that the recurrence stage carried a FITTED rather than a true
drift, and the matching carrier injected into every covering repeat block at
the cell a persistent carrier would occupy.  The frozen recurrence path was
then run unmodified and the recovery fraction counted.

★ WHAT THIS GENERATOR TAKES FROM THE CAMPAIGN AND WHAT IT COMPUTES ITSELF.
It reads the campaign's **per-realisation records** -- one JSON line per
realisation, carrying the per-block amplitudes and noises the frozen path
measured -- and recomputes the recovery fraction, its binomial interval, the
reading loss, the drift walk and every published number from them.  It takes
**no summary number** from the campaign, and the MODEL it compares against is
this paper's own: `traj_v418.json`'s $\Phi(5T_{\rm pers}/T_\star-5)$, the
expression Sec. 5.6 and Appendix B print.  The record is trusted for the
amplitudes themselves and for the sha256 of the frozen path, which every line
carries and which C1 requires to be one value.

★★ ONE INPUT IS CORRUPT AND IS FILTERED HERE.  `recur_v411.json` combines
`all_other` over EVERY repeat block, including the ones `badweight_v411.json`
flags: HR 1010's block `A002_Xc6b674_X28f5` carries sig = 0.0014 mJy against
7-12 in its siblings, so that crossing's stored `T_if_persistent` is 27,705 --
a number no reading can produce.  Every combination here drops the flagged
blocks, and C10 refuses any crossing whose retained statistic still exceeds
the trigger by more than a declared factor.

Inputs (all tree-local):
  r19inputs/hostinj_r19.jsonl.gz   the campaign's 15,850 realisation records
  traj_v418.json                   the model, per crossing (round 700)
  r10inputs/recur_v411.json        the blocks, their weights flag, the epochs
  recurinj_r19.json                round 750's independent measurement
  cresp_v401.json                  the correlator's own channel response

15 clauses (C1-C15), drives 1-16, each demonstrated to fail its own
clause:
  python3 hostinj_r19.py --drive N
★ C13-C15 and drives 14-16 are round 19's: the frame of every frequency this
  generator prints, the subset relation the main text asserts between the
  vacuous and the untested sets, and the tabulation R2-3.4 asked for.
★ D36: a drive writes `*_driveN.*` only and never a path production reads.
"""
import gzip
import json
import re
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 870
DRIVE = 0
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
SFX = '_drive%d' % DRIVE if '--drive' in sys.argv else ''
OUT = os.path.join(HERE, 'survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTJ = os.path.join(HERE, 'hostinj_r19%s.json' % SFX)

TRIG = 5.0                 # the trigger, as everywhere in this paper
POWER = 0.90               # the level the recovery probabilities quote
NMIN = 200                 # the realisations per crossing the campaign was asked for
CORRUPT = 100.0            # a persistence statistic this many times the trigger
#                            is not a reading, it is a weight fault
LONGREP = 2.0              # a repeat block this many times longer than the
#                            discovery block carries the drift grid out of step
ETA = 'U37'                # the crossing the structural effect bites

L, PROB = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' % name
    L.append('\\newcommand{\\%s}{%s}\n' % (name, val))


def ck(desc, cond, detail):
    print(('PASS  ' if cond else 'FAIL  ') + desc + '  [' + detail + ']')
    if not cond:
        PROB.append(desc)


def tname(display):
    """House style for a star name in running text: no breakable space
    inside a designation, and a real minus rather than a hyphen before a
    digit -- which `minuscheck` reads off the typeset page."""
    out = re.sub(r'(?<!\$)-(?!\$)', '$-$', display)
    return out.replace(' ', '~')


def phi(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def wilson(k, n, z=1.0):
    """The binomial interval, recomputed here."""
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


# ======================================================= the paper's own inputs
REC = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
CROSSINGS = REC['crossings']

# ★★★★ EVERY FREQUENCY THIS GENERATOR PRINTS IS THE ONE IN THE STAR'S OWN
# FRAME, because Sec. 5.5 declares that convention for itself AND for Sec.
# 5.6, and the list below is set in Sec. 5.6.  `freq_GHz` in the measurement
# record is the DELIVERED frequency: `recur_v411.py` uses that field as the
# LOOKUP KEY for the transported one, which is what proves which frame it is
# in.  Printed raw it gave the same crossing two frequencies 23 MHz apart in
# one paragraph -- beta Pic at 241.75 six lines after 241.77 -- and called
# one crossing 344.27 GHz where Sec. 5.5, Fig. 7 and Table 6 call it
# 344.2965.  The ledger is the one place the transported frequency is
# computed, so it is read from there and joined on BLOCK AND FREQUENCY,
# never on a star name.  C13 reads the frequencies back out of the string
# that is typeset.
LEDR = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
FSTELLAR = {(r['eb'], round(float(r['freq']), 4)):
            float(r['frame']['f_stellar']) for r in LEDR}
FTOPO = {(r['eb'], round(float(r['freq']), 4)):
         float(r['frame']['f_topo']) for r in LEDR}


def fkey(c):
    return (c['eb'], round(float(c['freq_GHz']), 4))


def fstellar(c, topo=False):
    return (FTOPO if topo else FSTELLAR)[fkey(c)]

BADW = set()
for cid, c in CROSSINGS.items():
    for b in c.get('blocks', []):
        if b.get('bad_weight_product'):
            BADW.add((cid, b['eb']))
if DRIVE == 10:                 # C10: the corrupt block left in the combination
    BADW = set()

TRAJ = {r['cid']: r for r in
        json.load(open(os.path.join(HERE, 'traj_v418.json')))['rows']}
THRMATCH = float(json.load(
    open(os.path.join(HERE, 'traj_v418.json')))['trial_thr'])


def combined(r):
    """Inverse-variance combination over the covering repeat blocks, dropping
    any block the weights flag -- the statistic the exclusions are built
    from."""
    bs = [b for b in r['blocks'] if (r['cid'], b['eb']) not in BADW]
    if not bs:
        return float('nan'), 0
    w = [1.0 / b['sig_mJy'] ** 2 for b in bs]
    sb = 1.0 / math.sqrt(sum(w))
    ab = sum(b['amp_mJy'] * x for b, x in zip(bs, w)) / sum(w)
    return ab / sb, len(bs)


def bestdrift(r):
    """The pipeline's own maximum over the repeat block's drift trials, on the
    same retained blocks.  Reported as a CHECK and never as the statistic."""
    bs = [b for b in r['blocks'] if (r['cid'], b['eb']) not in BADW]
    return max((b['T_bestdrift'] for b in bs), default=float('nan'))


# ======================================================= the frozen record
RAWF = os.path.join(HERE, 'r19inputs', 'hostinj_r19.jsonl.gz')
RAW = []
with gzip.open(RAWF, 'rt') as fh:
    for ln in fh:
        ln = ln.strip()
        if ln:
            RAW.append(json.loads(ln))
OK = [r for r in RAW if r.get('ok')]
BAD = [r for r in RAW if not r.get('ok')]
SHA = sorted({r['frozen_sha'] for r in RAW})
if DRIVE == 3:                  # C1: the frozen path changed mid-campaign
    SHA = sorted(SHA + ['deadbeefdeadbeef'])
MODE = 'cell'                   # independent noise: the defensible interval
ROWS = {}
for r in OK:
    if r['mode'] == MODE:
        ROWS.setdefault(r['cid'], []).append(r)

# ======================================================= the measurement
MEAS = {}
for cid, rs in sorted(ROWS.items()):
    tc = [combined(r)[0] for r in rs]
    tb = [bestdrift(r) for r in rs]
    k = sum(1 for t in tc if t >= TRIG)
    p, lo, hi = wilson(k, len(rs))
    km = sum(1 for t in tc if t >= THRMATCH)
    model = phi(TRIG * float(TRAJ[cid]['tpers']) / float(TRAJ[cid]['tstar'])
                - TRIG)
    model_m = phi(TRIG * float(TRAJ[cid]['tpers']) / float(TRAJ[cid]['tstar'])
                  - THRMATCH)
    MEAS[cid] = dict(cid=cid, star=CROSSINGS[cid]['display'], n=len(rs), k=k,
                     p=p, lo=lo, hi=hi, model=model, dev=model - p,
                     p_match=km / len(rs), model_match=model_m,
                     p_best=sum(1 for t in tb if t >= TRIG) / len(rs),
                     t_med=statistics.median(tc),
                     n_blocks=statistics.median(combined(r)[1] for r in rs))
if DRIVE == 8:                  # C3: a count that is not the fraction's own
    _c = sorted(MEAS)[0]
    MEAS[_c]['k'] += 1
if DRIVE == 9:                  # C5: an exclusion measured deeper than modelled
    _c = min(MEAS, key=lambda c: MEAS[c]['model'])
    MEAS[_c]['p'] = min(MEAS[_c]['model'] + 0.25, 0.85)
    MEAS[_c]['k'] = round(MEAS[_c]['p'] * MEAS[_c]['n'])
    MEAS[_c]['lo'], MEAS[_c]['hi'] = MEAS[_c]['p'] - 0.01, 1.0
    MEAS[_c]['dev'] = MEAS[_c]['model'] - MEAS[_c]['p']
if DRIVE == 5:                  # C6: a second crossing moved across the level
    for _c in sorted(MEAS):
        if _c != ETA and MEAS[_c]['model'] >= POWER:
            MEAS[_c]['p'] = 0.5 * POWER
            MEAS[_c]['k'] = round(MEAS[_c]['p'] * MEAS[_c]['n'])
            MEAS[_c]['lo'], MEAS[_c]['hi'] = 0.0, 1.0
            MEAS[_c]['dev'] = MEAS[_c]['model'] - MEAS[_c]['p']
            break

DEV = sorted(v['dev'] for v in MEAS.values())
DEV_MED = statistics.median(DEV)
if DRIVE == 4:                  # C4: a model pessimistic in the median
    DEV_MED = -abs(DEV_MED)
DEV_MAX = max(DEV)
DEV_MAX_OTHER = max(v['dev'] for c, v in MEAS.items() if c != ETA)
DEV_WORST_OTHER = max(((v['dev'], v['star']) for c, v in MEAS.items()
                       if c != ETA))
LO_MEAS = {c for c, v in MEAS.items() if v['p'] < POWER}
LO_MODEL = {c for c, v in MEAS.items() if v['model'] < POWER}
N_TRIAL_MEAS = sum(1 for v in MEAS.values() if v['p_match'] >= POWER)
N_TRIAL_MODEL = sum(1 for v in MEAS.values() if v['model_match'] >= POWER)

CRESP = json.load(open(os.path.join(HERE, 'cresp_v401.json')))
SCALLOP = 1.0 - 10.0 ** (-float(CRESP['scallop_db']) / 20.0)
OUTMAX = 0.10                   # the share of block readings allowed outside it

# ======================================================= the mechanism
# The implied per-block reading efficiency: the amplitude the frozen path
# recovers in a repeat block over the flux injected into it, against the same
# ratio in the discovery block the carrier was normalised on.  Both measured.
GAIN, WALKB = {}, {}
for cid, rs in sorted(ROWS.items()):
    _step = statistics.median(r['drift_step_Hz_s'] for r in rs)
    for b in CROSSINGS[cid].get('blocks', []):
        if (cid, b['eb']) in BADW:
            continue
        WALKB[(cid, b['eb'])] = (
            _step * (float(b['t_end_mjdsec']) - float(b['t_start_mjdsec']))
            / float(b['chanw_Hz']))
for cid, rs in sorted(ROWS.items()):
    gd = statistics.median(r['gain'] for r in rs)
    per = {}
    for r in rs:
        inj = r['amp_Jy'] * 1000.0
        for b in r['blocks']:
            if (cid, b['eb']) in BADW:
                continue
            per.setdefault(b['eb'], []).append(b['amp_mJy'] / inj)
    for eb, v in per.items():
        GAIN[(cid, eb)] = statistics.median(v) / gd
# ★ THE RESPONSE TERM IS SEPARABLE FROM THE WALK TERM AND ONLY ONE OF THEM IS
# BOUNDED BY THE INSTRUMENT.  Where one step of the drift grid stays inside
# half a channel across the repeat block, the only thing between the injected
# carrier and the reading is where in the channel it lands, and that is the
# correlator's own scalloping loss.  Where the grid walks further -- C11's
# term -- the loss is structural and much larger, and saying so is the point.
STEADY = {k: v for k, v in GAIN.items() if WALKB.get(k, 9.9) <= 0.5}
RATIO = sorted(STEADY.values())
LOSS_MED = 1.0 - statistics.median(RATIO)
LOSS_MAX = 1.0 - min(RATIO)
OUTSIDE = sum(1 for r in RATIO if 1.0 - r > SCALLOP) / len(RATIO)
if DRIVE == 6:                  # C7: a response term outside the instrument's bound
    OUTSIDE = 0.5


# ======================= the structural term: how far the grid walks ==========
# One step of the drift grid is sized to the DISCOVERY block.  Carried into a
# repeat block of a different length it walks a different number of channels,
# and where the repeat is much the longer the fitted drift no longer lands on
# the predicted cell.  Both durations are the paper's own.
WALK = {}
for cid, rs in sorted(ROWS.items()):
    c = CROSSINGS[cid]
    d = c['discovery']
    tdisc = float(d['t_end_mjdsec']) - float(d['t_start_mjdsec'])
    step = statistics.median(r['drift_step_Hz_s'] for r in rs)
    chw = float(d['chanw_Hz'])
    reps = [b for b in c['blocks'] if (cid, b['eb']) not in BADW]
    trep = max((float(b['t_end_mjdsec']) - float(b['t_start_mjdsec'])
                for b in reps), default=0.0)
    ok = [abs(r['disc_drift_fit_Hz_s'] - r['drift_true_Hz_s'])
          <= 0.5 * r['drift_step_Hz_s'] for r in rs]
    WALK[cid] = dict(ratio=trep / tdisc if tdisc else 0.0,
                     walk_disc=step * tdisc / chw,
                     walk_rep=step * trep / chw,
                     frac_ok=sum(ok) / len(ok))
if DRIVE == 11:                 # C11: eta Crv's repeat no longer the long one
    WALK[ETA]['ratio'] = 1.0

# the pipeline's own maximum on the REAL repeat, from the paper's own record
ETA_REAL = float(CROSSINGS[ETA]['all_other']['T_bestdrift_max'])
if DRIVE == 12:                 # C12: the alternative statistic returns
    ETA_REAL = TRIG + 1.0

# ======================================================= what stays modelled
def macro(name):
    """A value from the published macro layer of this directory."""
    import glob
    import re
    pat = re.compile(r'\\(?:provide|renew|new)command\{?\\(%s)\}?\{([^}]*)\}'
                     % name)
    val = None
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(f, errors='ignore').read()):
            if mm.group(2).strip():
                val = mm.group(2).strip()
    assert val is not None, 'no macro \\%s in the macro layer' % name
    return val


# ★ C9 REQUIRES THE PARTITION TO CLOSE AND NOT THAT ANYTHING BE LEFT OVER.
# Written the other way round -- "some crossings must remain model-dependent"
# -- it would be a clause that can only FAIL on good data.
NQ = int(macro('RcNExcl'))
N_MODEL = NQ - len(MEAS)

# ======================================================= the other harness
RJ = json.load(open(os.path.join(HERE, 'recurinj_r19.json')))['rows']
CROSS, CROSS_SIG = {}, {}
for tag, r in RJ.items():
    if r['cid'] in MEAS:
        v = MEAS[r['cid']]
        CROSS[r['cid']] = (float(r['p_phase']), v['p'])
        CROSS_SIG[r['cid']] = math.sqrt(max(float(r['e_phase']), 0.005) ** 2
                                        + (0.5 * (v['hi'] - v['lo'])) ** 2)
if DRIVE == 7:                  # C8: two harnesses that disagree
    _c = sorted(CROSS)[0]
    CROSS[_c] = (CROSS[_c][0], CROSS[_c][1] - 0.25)
CROSS_DEV = max(abs(a - b) for a, b in CROSS.values()) if CROSS else 0.0

# the persistence statistic of every crossing, over the RETAINED blocks
TPERS = {}
for cid, c in CROSSINGS.items():
    bs = [b for b in c.get('blocks', []) if (cid, b['eb']) not in BADW]
    if not bs:
        continue
    w = [1.0 / b['sig_mJy'] ** 2 for b in bs]
    sb = 1.0 / math.sqrt(sum(w))
    ab = sum(b['amp_mJy'] * x for b, x in zip(bs, w)) / sum(w)
    TPERS[cid] = abs(ab) / sb
WORST = max(TPERS.items(), key=lambda z: z[1])
STORED = max((abs(float(c['all_other']['T_if_persistent'])), cid)
             for cid, c in CROSSINGS.items() if c.get('all_other'))

# ======================================================= clauses
_nreal = min(v['n'] for v in MEAS.values())
if DRIVE == 2:                  # C2: a crossing short of the stated minimum
    _nreal = NMIN - 1
_nbad = len(BAD) if DRIVE != 1 else 1
ck('C1 the campaign ran ONE frozen recurrence path, unmodified, and every '
   'realisation records its sha256: a path that changed mid-campaign would '
   'make the measurement a measurement of nothing',
   len(SHA) == 1 and len(SHA[0]) >= 16,
   'sha256[:16] %s over %d realisation records' % (', '.join(SHA), len(RAW)))
ck('C2 no realisation failed, and every crossing carries at least the %d '
   'realisations the campaign was asked for' % NMIN,
   _nbad == 0 and _nreal >= NMIN,
   '%d failed of %d; fewest realisations on one crossing %d'
   % (_nbad, len(RAW), _nreal))
ck('C3 the recovery fraction is recomputed here from the per-block '
   'amplitudes by the same inverse-variance combination the exclusions use, '
   'and its binomial interval brackets it',
   all(v['lo'] <= v['p'] <= v['hi'] and v['k'] == round(v['p'] * v['n'])
       for v in MEAS.values()),
   '%d crossings, %d realisations; median recovery %.3f'
   % (len(MEAS), sum(v['n'] for v in MEAS.values()),
      statistics.median(v['p'] for v in MEAS.values())))
ck('C4 the model is optimistic in the median rather than pessimistic, so '
   'the exclusions this paper quotes are the WEAKER of the two readings',
   DEV_MED > 0.0,
   'model - measured: median %+.3f, largest %+.3f (%s), smallest %+.3f'
   % (DEV_MED, DEV_MAX, MEAS[max(MEAS, key=lambda c: MEAS[c]['dev'])]['star'],
      DEV[0]))
ck('C5 no crossing measures deeper than the model it is quoted at: the '
   'model lies at or above the lower end of every measured interval, so no '
   'exclusion in this paper is weaker than the measurement allows',
   all(v['model'] >= v['lo'] - 1e-9 for v in MEAS.values()),
   'tightest margin %+.3f at %s (model %.3f against a measured lower bound '
   'of %.3f)'
   % tuple(min(((v['model'] - v['lo'], v['star'], v['model'], v['lo'])
                for v in MEAS.values()))[i] for i in (0, 1, 2, 3)))
ck('C6 the measurement moves EXACTLY ONE crossing across %d per cent '
   'recovery and it is %s: a count the paper prints moves, and it moves for '
   'one named reason rather than across the board'
   % (100 * POWER, CROSSINGS[ETA]['display']),
   LO_MEAS - LO_MODEL == {ETA} and LO_MODEL - LO_MEAS == set(),
   'below %.2f: %d modelled, %d measured; moved %s'
   % (POWER, len(LO_MODEL), len(LO_MEAS),
      sorted(MEAS[c]['star'] for c in LO_MEAS ^ LO_MODEL) or 'nothing'))
ck('C7 where the drift grid stays inside half a channel across the repeat '
   'block the shortfall is the instrument\'s own: the median loss is well '
   'inside the correlator\'s scalloping bound and all but a declared %.0f '
   'per cent of block readings are inside it' % (100 * OUTMAX),
   LOSS_MED < SCALLOP and OUTSIDE <= OUTMAX,
   'median loss %.1f per cent over %d steady block roles of %d, %.1f per '
   'cent of them outside the response bound of %.1f per cent (%.4f dB); '
   'worst steady role %.1f per cent'
   % (100 * LOSS_MED, len(STEADY), len(GAIN), 100 * OUTSIDE, 100 * SCALLOP,
      float(CRESP['scallop_db']), 100 * LOSS_MAX))
ck('C8 two independently built harnesses agree on the crossings they share, '
   'within twice their own combined uncertainty, so neither is publishing '
   'its own defect: %s'
   % ', '.join(sorted(MEAS[c]['star'] for c in CROSS)),
   bool(CROSS) and all(abs(a - b) <= 2.0 * CROSS_SIG[c]
                       for c, (a, b) in CROSS.items()),
   'largest disagreement %.3f over %d shared crossing(s): %s'
   % (CROSS_DEV, len(CROSS),
      ', '.join('%s %.3f vs %.3f' % (MEAS[c]['star'], a, b)
                for c, (a, b) in sorted(CROSS.items()))))
ck('C9 every crossing that carries an exclusion is measured here or declared '
   'model-dependent, and the two sets partition the %d of them' % NQ,
   (len(MEAS) + N_MODEL == NQ if DRIVE != 13 else False)
   and 0 < len(MEAS) <= NQ and N_MODEL >= 0,
   '%d measured, %d model-dependent, %d carrying an exclusion%s'
   % (len(MEAS), N_MODEL, NQ,
      '' if N_MODEL else ' -- none left model-dependent'))
ck('C10 no crossing is combined over a block the weights flag, and no '
   'retained persistence statistic exceeds the trigger by more than x%g: a '
   'stored %.0f is a weight fault and not a reading, and any generator '
   'reading it straight out of the record would publish it' % (CORRUPT,
                                                               STORED[0]),
   WORST[1] <= TRIG * CORRUPT and len(BADW) > 0
   and STORED[0] > TRIG * CORRUPT,
   'largest retained %.2f (%s) against a stored maximum of %.0f (%s); '
   '%d flagged block(s) dropped'
   % (WORST[1], CROSSINGS[WORST[0]]['display'], STORED[0],
      CROSSINGS[STORED[1]]['display'], len(BADW)))
ck('C11 the one crossing the measurement moves is the one whose repeat block '
   'is much longer than its discovery block, and it is the only one: the '
   'drift grid is sized to the discovery block, so carried into a repeat '
   '%.1f times longer one step walks %.2f channels instead of %.2f'
   % (WALK[ETA]['ratio'], WALK[ETA]['walk_rep'], WALK[ETA]['walk_disc']),
   WALK[ETA]['ratio'] > LONGREP
   and all(w['ratio'] <= LONGREP for c, w in WALK.items() if c != ETA),
   'walk ratio %.2f at %s against %.2f-%.2f elsewhere; the fitted drift '
   'lands within half a step %.0f per cent of the time'
   % (WALK[ETA]['ratio'], CROSSINGS[ETA]['display'],
      min(w['ratio'] for c, w in WALK.items() if c != ETA),
      max(w['ratio'] for c, w in WALK.items() if c != ETA),
      100 * WALK[ETA]['frac_ok']))
ck('C12 the pipeline\'s own maximum over the repeat\'s drift trials is a '
   'CHECK and not a rescue: it recovers the injected carrier in every '
   'realisation, and on the real data it reads below the trigger, so no '
   'crossing returns on either statistic',
   MEAS[ETA]['p_best'] >= 1.0 and ETA_REAL < TRIG,
   'injected recovery %.3f of %d realisations; the real repeat reads %.4f '
   'against a trigger of %.1f'
   % (MEAS[ETA]['p_best'], MEAS[ETA]['n'], ETA_REAL, TRIG))

# ======================================================= macros
_LOWCIDS = sorted(LO_MEAS, key=lambda c: MEAS[c]['p'])
_low = ['%s at %.2f\\,GHz (%.2f)'
        % (tname(MEAS[c]['star']), fstellar(CROSSINGS[c], DRIVE == 14),
           MEAS[c]['p'])
        for c in _LOWCIDS]
_LOWSTR = ', '.join(_low[:-1]) + ' and ' + _low[-1]

# ★ C13 DOES NOT CHECK THE VARIABLE THAT WROTE THE STRING: it reads the
# frequencies back out of the string that is typeset and compares each with
# the ledger's own f_stellar, which is the only way a frame error can be
# caught -- both numbers are correct numbers, so `valuetwin` and
# `audit_numbers` compare values and see nothing.  And it cannot pass
# vacuously: it also requires the two frames to differ on at least one of
# the crossings printed, so a build in which the transport had silently
# become the identity would FAIL here rather than agree with itself.
_printed = [float(x) for x in re.findall(r'at ([0-9.]+)\\,GHz', _LOWSTR)]
_want = ['%.2f' % FSTELLAR[fkey(CROSSINGS[c])] for c in _LOWCIDS]
_fbad = [(MEAS[c]['star'], '%.2f' % p, w)
         for c, p, w in zip(_LOWCIDS, _printed, _want) if '%.2f' % p != w]
_fsep = max(abs(FSTELLAR[fkey(CROSSINGS[c])] - FTOPO[fkey(CROSSINGS[c])])
            for c in _LOWCIDS)
ck('C13 every frequency this round prints is the STELLAR-frame one, equal to '
   "the ledger's own f_stellar at the printed precision, read back out of "
   'the typeset string -- and the two frames differ here, so the comparison '
   'is not an identity',
   len(_printed) == len(_LOWCIDS) and not _fbad and _fsep > 1e-4,
   '%d frequencies printed, %d mismatch%s, largest frame separation %.1f MHz'
   % (len(_printed), len(_fbad), ' (%s)' % _fbad if _fbad else 'es',
      1e3 * _fsep))

# ★ C14 HOLDS A CLAIM THE PAPER MAKES IN THE MAIN TEXT AND NO GATE COULD SEE:
# that the crossings whose exclusion rules out nothing under the wider
# reading are among the ones reported untested.  `traj_v418.py`'s T4 compared
# that set against its own CALCULATED untested set, which is 7, while the
# paper prints the MEASURED one, which is 8 -- so T4 passed while the
# sentence it policed was false.  The measured set only exists here, and
# traj_v418.py runs before this generator, so the comparison belongs here.
_VAC = sorted(json.load(open(os.path.join(HERE, 'traj_v418.json')))['vacuous'])
if DRIVE == 15:                 # C14: a vacuous exclusion that is not untested
    _VAC = _VAC + [c for c in sorted(MEAS) if c not in LO_MEAS][:1]
_vout = [c for c in _VAC if c not in LO_MEAS]
ck('C14 every crossing whose exclusion rules out nothing under the wider '
   'reading is among the ones measured untested rather than excluded, and '
   'that is a SUBSET and not an identity: the measured set is the larger of '
   'the two, and the prose may not claim they are the same set',
   bool(_VAC) and not _vout and len(_VAC) <= len(LO_MEAS)
   and len(_VAC) == int(macro('ZtNWideVac')),
   '%s vacuous published, %d here, %d untested measured; outside the '
   'measured set: %s'
   % (macro('ZtNWideVac'), len(_VAC), len(LO_MEAS), _vout or 'none'))

# ★ R2-3.4 asked for the measured recovery TABULATED beside the modelled
# value, and it was reported in prose only.  One fragment, generated here
# from the same records, ordered by what is measured so that the crossings
# reported untested lead it.  C15 asserts that ordering, because the caption
# says the first HjNPowerLo rows are those crossings.
_TROWS = sorted(MEAS.values(), key=lambda v: (v['p'], v['star']))
# ★ R2-2 ASKED WHAT EACH REALISATION WAS INJECTED INTO, crossing by crossing.
# The answer is the same for all of them -- the retained per-integration
# spectra of the real data, the discovery block and every covering repeat
# block -- so the words go in the caption once and the column carries the
# number of repeat blocks the carrier was laid into.  C16 holds the claim:
# the count is the plan's own, and the campaign's records in the mode the
# referee specifies carry exactly that many blocks.
_NREP = {c: len(CROSSINGS[c]['blocks']) for c in MEAS}
_phase = {}
for _r in RAW:
    if _r.get('ok') and _r['mode'] == 'phase':
        _phase.setdefault(_r['cid'], []).append(int(_r['n_blocks']))
if DRIVE == 17:                 # C16: a block count that is not the plan's
    _NREP[sorted(_NREP)[0]] += 1
_nbad = sorted(c for c in _NREP
               if not _phase.get(c) or max(_phase[c]) != _NREP[c]
               or min(_phase[c]) != _NREP[c])
ck('C16 every realisation of every crossing was injected into the retained '
   'per-integration spectra of the discovery block and of every covering '
   'repeat block, and the tabulated block count is the plan\'s own',
   not _nbad and sum(_NREP.values()) > 0,
   '%d crossings, %d repeat blocks in all, %d disagreeing with the records %s'
   % (len(_NREP), sum(_NREP.values()), len(_nbad), _nbad[:2] or ''))
_T = ['%% GENERATED by hostinj_r19.py -- do not hand-edit.',
      r'\begin{tabular}{@{}l@{~~}r@{~~}r@{~~}r@{~~}l@{~~}r@{}}', r'\hline',
      r'Star & $\nu_\star$ (GHz) & $n_{\rm rep}$ & $\Phi$ & measured & '
      r'$N$ \\', r'\hline']
for _v in _TROWS:
    _T.append(r'%s & %.4f & %d & %.2f & %.2f (%.2f--%.2f) & %d \\'
              % (tname(_v['star']),
                 fstellar(CROSSINGS[_v['cid']], DRIVE == 14),
                 _NREP[_v['cid']],
                 _v['model'], _v['p'], _v['lo'], _v['hi'], _v['n']))
_T += [r'\hline', r'\end{tabular}']
with open(os.path.join(HERE, 'tab_hostinj_r19%s.tex' % SFX), 'w') as _fh:
    _fh.write('\n'.join(_T) + '\n')
_tlead = [v['cid'] for v in _TROWS[:len(LO_MEAS)]]
if DRIVE == 16:                 # C15: the table ordered so the lead is wrong
    _tlead = [v['cid'] for v in _TROWS[1:len(LO_MEAS) + 1]]
ck('C15 the tabulated recovery carries one row per crossing that carries an '
   'exclusion, and the %d the caption calls untested are the rows it leads '
   'with' % len(LO_MEAS),
   len(_TROWS) == len(MEAS) and set(_tlead) == set(LO_MEAS),
   '%d rows for %d crossings; leading %d rows %s the measured untested set'
   % (len(_TROWS), len(MEAS), len(_tlead),
      'are' if set(_tlead) == set(LO_MEAS) else 'ARE NOT'))
m('HjNMeas', '%d' % len(MEAS))
m('HjNModel', '%d' % N_MODEL)
m('HjNReal', '%d' % _nreal)
m('HjNBlockRole', '%d' % len(GAIN))
m('HjDevMed', '%.2f' % DEV_MED)
m('HjDevMax', '%.2f' % DEV_MAX)
m('HjDevMaxOther', '%.2f' % DEV_MAX_OTHER)
m('HjDevStarOther', tname(DEV_WORST_OTHER[1]))
m('HjRespMedPct', '%.1f' % (100 * LOSS_MED))
m('HjRespMaxPct', '%.1f' % (100 * LOSS_MAX))
m('HjRespBoundPct', '%.1f' % (100 * SCALLOP))
m('HjRespOutPct', '%.1f' % (100 * OUTSIDE))
m('HjNSteady', '%d' % len(STEADY))
m('HjCrossDev', '%.2f' % CROSS_DEV)
m('HjNPowerHi', '%d' % (len(MEAS) - len(LO_MEAS)))
m('HjNPowerLo', '%d' % len(LO_MEAS))
m('HjLowList', _LOWSTR)
m('HjNPowerTrial', '%d' % N_TRIAL_MEAS)
m('HjEtaStar', tname(CROSSINGS[ETA]['display']))
m('HjEtaMeas', '%.2f' % MEAS[ETA]['p'])
m('HjEtaLo', '%.2f' % MEAS[ETA]['lo'])
m('HjEtaHi', '%.2f' % MEAS[ETA]['hi'])
m('HjEtaLenRatio', '%.1f' % WALK[ETA]['ratio'])
m('HjEtaWalkCh', '%.1f' % WALK[ETA]['walk_rep'])
m('HjEtaFracOkPct', '%.0f' % (100 * WALK[ETA]['frac_ok']))
m('HjEtaMaxRec', '%.2f' % MEAS[ETA]['p_best'])
m('HjEtaMaxReal', '%.2f' % ETA_REAL)

assert not PROB, 'hostinj_r19: %d clause(s) FAILED: %s' % (len(PROB), PROB)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by hostinj_r19.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    fh.write('%% The recurrence recovery probability measured on injected '
             'carriers.\n')
    fh.writelines(sorted(L))
json.dump(dict(crossings=sorted(MEAS.values(), key=lambda v: v['cid']),
               walk={c: WALK[c] for c in sorted(WALK)},
               n_real_total=len(RAW), n_failed=len(BAD), frozen_sha=SHA,
               mode=MODE, dev_median=DEV_MED, dev_max=DEV_MAX,
               thr_matched=THRMATCH, n_trial_meas=N_TRIAL_MEAS,
               n_trial_model=N_TRIAL_MODEL,
               below_power_model=sorted(LO_MODEL),
               below_power_meas=sorted(LO_MEAS),
               loss_median=LOSS_MED, loss_max=LOSS_MAX,
               scallop_bound=SCALLOP, cross_harness=CROSS,
               bad_weight_blocks=sorted('%s %s' % k for k in BADW),
               t_pers_retained={c: TPERS[c] for c in sorted(TPERS)},
               eta_real_bestdrift=ETA_REAL,
               gain_ratio={'%s %s' % k: v for k, v in sorted(GAIN.items())}),
          open(OUTJ, 'w'), indent=1)
print('hostinj_r19: %d crossings, %d realisations, %d macros -> %s'
      % (len(MEAS), len(RAW), len(L), os.path.basename(OUT)))
