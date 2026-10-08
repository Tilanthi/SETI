#!/usr/bin/env python3
r"""Round 310: ONE CHANCE EXPECTATION, MEASURED WINDOW BY WINDOW, OVER THE
RELEASED CENSUS, WITH ONE INTERVAL AND THE TRANSFER TO STELLAR POSITIONS
APPLIED TO IT.

★ THE REFERENCE SET IS THE RELEASED CENSUS, 402 CLASS A WINDOWS -- the set the
deposited catalogue tabulates window by window and the set Sec. 3 says every
crossing and every expectation is computed over.  It was previously the 417
Class A windows of the census extent, 15 of which are archival-tail windows the
release does not tabulate and which carry two of the unattributed crossings:
the expectation was scaled to a set the deposit does not describe.  Both sides
now run over the released 402, giving \CeObs unattributed crossings against
\CeExp expected, and the two archival-tail crossings toward HD 14055 are
counted and named OUTSIDE the comparison rather than inside it.  A5 asserts the
two sides share one window set and that no tail crossing enters either.

★ THE TRANSFER TO STELLAR POSITIONS IS NOW APPLIED, NOT ONLY CARRIED AS A
WIDTH.  The expectation is a sum of CONTROL-position exceedance rates, and the
reserved blocks measure how well a control stands in for the star in exactly
that quantity: stars reach the trigger \StHoRatio times as often as their own
controls predict.  Multiplying by that measured ratio gives \CeExpX, and the
observed count sits inside the interval either way -- which is the statement
the paper must make rather than quoting the uncorrected sum alone.

★ AND THE INTERVAL IS QUOTED AS AN INTERVAL, NOT AS A TOLERANCE.  A resampled
ratio of \StHoRatio with \StHoLo--\StHoHi allowed does not support "an accuracy
of about 35 per cent"; it makes the expectation anything between \CeLo and
\CeHi, so an added population of up to \CeAddBlind events -- most of the
observed count -- would be absorbed by the width of the range.  That number is
published as a macro so no sentence can round it away.

Five earlier faults, all of them real, are recorded below.

(1) THE INTERVAL WAS sqrt(N).  The expectation is estimated from the control
    positions, so its uncertainty is the uncertainty of that estimate: the
    finite control ensemble, the fact that windows share execution blocks and
    are not independent trials, and -- dominating both -- the accuracy with
    which the reserved blocks fix the one assumption the searched data cannot
    test, that a star behaves like a control position in its own field.  All
    three are carried here by resampling execution blocks, which is the device
    the hold-out calibration already uses.  The Poisson scatter and the
    "a population would have to exceed about eleven events" sentence it
    supported are withdrawn: the interval does not support a floor, and the
    honest statement is that the comparison is consistent with chance and
    cannot see a small added population.

(2) THE MASK CORRECTION WAS CONDITIONED ON THE CROSSINGS.  The expectation was
    reduced by a figure measured over the windows that hold crossings -- a
    population whose central feature is an excess of real molecular lines, so
    the astrophysical excess was being built into the null.  What the null
    needs is the probability that a CONTROL maximum reaching the trigger falls
    inside an attribution window, and a control maximum is a noise maximum: it
    is free to land anywhere on its window's own channel grid.  So the figure
    is the share of each window's own channels that lies within the mask, in
    that star's rest frame, over every Class A window of the census and
    weighted by the window's own measured exceedance rate -- which is what
    "window by window" means on this side of the comparison.

    ★ IT MOVES, AND IT MOVES AGAINST US.  The figure in print was 9.2 per
    cent.  Measured this way it is about 23 per cent, because the windows that
    dominate the expectation are narrow line-tuned ones whose fields carry real
    emission: fifteen Class A windows lie ENTIRELY inside the mask and between
    them carry an eighth of the whole trigger expectation.  The expectation
    therefore FALLS, and the observed count moves from below it to above it.
    That is published, in that direction.

(3) TWO DERIVATIONS DISAGREED: the body reduced by 9.2 per cent and the
    appendix by the 4.3 per cent share of the searched band, and quoted the
    same product.  Neither survives; there is one derivation here and the
    appendix and the body now print the same macros.
    ★ The 9.2 per cent was also measured against the FIFTEEN-transition search
    list in the OBSERVER frame, while attribution uses the \FrNTrans-entry mask
    in the STELLAR frame.  A3 requires the null's mask to reproduce the
    ledger's own attributions, so the two can no longer be different masks.

(4) THE UNITS DID MATCH, AND THE PAPER NEVER SAID SO.  A window contributes the
    probability that a position in its field reaches the trigger, so the sum is
    an expected number of WINDOWS; a threshold crossing is defined as a window
    holding such a cell.  Measured: no window in the census holds more than one
    crossing, and the two blocks the point names carry their two crossings in
    two different spectral windows.  A3b asserts it instead of assuming it.

(5) HD 14055'S TWO CROSSINGS ARE IN BLOCKS THAT ARRIVED WITH THE ARCHIVAL
    TAIL.  Settled from the census record and not by choosing: both blocks are
    listed in `v409_census.json` as arriving with the tail, and
    `followup_stratum.json` lists them under `census_blocks_also_covering`, so
    they are not follow-up observations.  ★ They are nonetheless NOT TABULATED
    window by window in the released catalogue, which carries \NWinA{} of the
    \VnWinA{} Class A windows, and the reference set is the released one: their
    two crossings are reported beside the comparison, with their blocks named,
    and enter neither side of it.  The earlier reading carried the \VnWinA{}
    windows at the mean rate of the tabulated ones and counted the two
    crossings against that -- an expectation over a set the deposit does not
    describe.

Inputs, all read: `per_target_results_v3.99.csv`, `corrected_export_v399.json`,
`r8inputs/v409/fieldfix_v409.json`, `holdout_export_v381.json`, `ledger.json`,
`r8inputs/v409/v409_census.json`, `census_v412.json`,
`r8inputs/v409/followup_stratum.json`, the
mask and the frame chain from `maskframe_v411.py` as a module, and the macro
layer for the counts other generators own.

Ten assertions, ten drives.  `--drive 0` means "no perturbation, but do not
write a path production reads"; every drive writes `*_driveN.*` only.

    python3 chance_v414.py [--drive N]
"""
import collections
import csv
import glob
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maskframe_v411 as mf                                      # noqa: E402

ROUND = 310
TRIG = 5.0
NBOOT = 20000
NREAL = 2000
SEED = 310

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])

# ★ The production name is a literal and only the drive branch is built by
#   format, so `roundcollide` can resolve the claim on round 310.
OUT_TEX = os.path.join(HERE, 'survey_numbers_round310.tex' if DRIVE is None
                       else 'survey_numbers_round310_drive%d.tex' % DRIVE)
OUT_JSON = os.path.join(HERE, 'chance_v414%s.json'
                        % ('' if DRIVE is None else '_drive%d' % DRIVE))

OUT = []
fail = []


def m(name, val):
    assert name.isalpha(), 'a macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label[:70], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """The value the macro layer publishes, in \\input order so a later
    \\renewcommand wins."""
    main = glob.glob(os.path.join(HERE, 'technosignatures_*.tex'))
    order = []
    if len(main) == 1:
        for ln in open(main[0], errors='ignore'):
            mm = re.match(r'\s*\\input\{(survey_numbers[A-Za-z0-9_]*)\}', ln)
            if mm:
                order.append(mm.group(1) + '.tex')
    val = None
    for fn in order:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        for ln in open(p, errors='ignore'):
            for nm, vv in re.findall(
                    r'\\(?:providecommand|renewcommand|newcommand)'
                    r'\{?\\([A-Za-z]+)\}?\{([^{}]*)\}', ln):
                if nm == name and vv.strip():
                    val = vv.strip()
    assert val is not None, 'no generator publishes \\%s' % name
    return val


C = mf.C_KMS
HALF = mf.MASK_HALF_KMS

# =====================================================================
# inputs
# =====================================================================
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXP = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
FFX = json.load(open(os.path.join(HERE, 'r8inputs/v409/fieldfix_v409.json')))
HOL = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
LROWS = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
CENSUS = json.load(open(os.path.join(HERE, 'r8inputs/v409/v409_census.json')))
RECON = json.load(open(os.path.join(HERE, 'census_v412.json')))
FOLLOW = json.load(open(os.path.join(
    HERE, 'r8inputs/v409/followup_stratum.json')))


# --------------------------------------------------------------- the join
# ★ A window is identified by its block and its two edges, taken as min/max of
#   the pair: a descending spectral window is written with flo above fhi in one
#   product and below it in another, and keying on the stored order loses half
#   the survey silently.  The join is then VALIDATED against the catalogue's
#   own published control maximum, and A1 requires the expectation it builds to
#   reproduce the published trigger sum.
def wkey(eb, a, b):
    a, b = float(a), float(b)
    if DRIVE == 1:
        return (eb, round(a, 3), round(b, 3))          # the stored order
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


def skey(s):
    return re.sub(r'\s+', '', s or '').lower()


BYWIN = collections.defaultdict(list)
for r in EXP:
    BYWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)
FFWIN = collections.defaultdict(list)
for r in FFX:
    FFWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)


def _pick(cands, row, namekey, maxkey):
    """One (star, window) search unit out of the window's rows.  Several
    components of one multiple share a window; they are distinguished by name
    where the names agree between products and by the published control
    maximum where they do not."""
    same = [x for x in cands if skey(x.get(namekey)) == skey(row['star_name'])]
    pool = same or cands
    if len(pool) == 1:
        return pool[0]
    return min(pool, key=lambda x: abs(float(x[maxkey])
                                       - float(row['ctrl_max_snr'] or 0)))


JOIN, NOVEC = {}, []
for i, r in enumerate(CAT):
    cands = BYWIN.get(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']), [])
    p = _pick(cands, r, 'star_name', 'ctrl_max') if cands else None
    if p is None or not (p.get('ctrl_all') or []):
        NOVEC.append(i)
        continue
    JOIN[i] = p

REPJOIN = {}
for i, r in enumerate(CAT):
    cands = FFWIN.get(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']), [])
    q = _pick(cands, r, 'star', 'ctrl_max') if cands else None
    if q is not None and q.get('ctrl_all'):
        REPJOIN[i] = q

MISMATCH = [i for i, p in JOIN.items()
            if CAT[i]['ctrl_max_snr']
            and abs(float(p['ctrl_max']) - float(CAT[i]['ctrl_max_snr'])) > 1e-3]


def ctrl_vector(i):
    """The window's own control ensemble, re-extracted where the adopted
    statistic is the re-extracted one."""
    src = REPJOIN.get(i) if i in REPJOIN else JOIN.get(i)
    return None if src is None else np.asarray(src['ctrl_all'], float)


IA = [i for i, r in enumerate(CAT) if r['search_class'] == 'A']
IB = [i for i, r in enumerate(CAT) if r['search_class'] == 'B']

PEXC = {}
for i in IA + IB:
    v = ctrl_vector(i)
    if v is not None:
        PEXC[i] = float((v >= TRIG).mean())

E_TRIG_REL = sum(PEXC[i] for i in IA if i in PEXC)

# =====================================================================
# (2) the mask fraction the NULL needs: each window's own channel grid
# =====================================================================
#: The mask is the searched transition list, in the star's rest frame, at the
#: published half-width.  A noise maximum is free to land on any channel of its
#: own window, so the probability that a control exceedance would be attributed
#: is the share of that window's channels inside the mask.  Nothing here reads
#: a crossing frequency: the quantity is a property of the grid and the frame.
#: THE ONE MASK.  A crossing is attributed when it lies inside the mask of a
#: transition the attribution uses, and `maskframe_v411` holds both the searched
#: list and the species whose coincidences are reported as coincidences rather
#: than as dispositions.  The null is reduced by the same list, so the mask that
#: lowers the expectation and the mask that classifies the crossings are one
#: object; A3 asserts the two agree on every crossing, in both directions.
NULL_TRANS = {k: v for k, v in mf.TRANS.items()
              if mf.species(k) not in mf.NOTED_SPECIES}
if DRIVE == 2:                     # the mask list and the dispositions diverge
    NULL_TRANS = dict(mf.TRANS)
REST = np.array(sorted(v[0] for v in NULL_TRANS.values()))

#: Systemic velocities exist for the stars a crossing made us measure.  Where
#: one is absent the star is taken at rest, and the sensitivity of the whole
#: factor to that choice is measured below over the full range the sample shows
#: rather than assumed small.
VSYS_SPAN = (-30.0, 30.0)


def masked_share(i, rest=REST, vsys_force=None):
    """The share of window i's own channels that the mask covers, and whether
    the star's systemic velocity was measured."""
    r = CAT[i]
    lo = min(float(r['flo_GHz']), float(r['fhi_GHz']))
    hi = max(float(r['flo_GHz']), float(r['fhi_GHz']))
    cw = float(r['chanw_Hz']) / 1e9
    n = int(round((hi - lo) / cw)) + 1
    g = lo + cw * np.arange(n)
    vb, _src = mf.vbary(r['eb'], r['flo_GHz'])
    vs, _s2, _b = mf.vsys(r['star_name'])
    known = vs is not None
    if vsys_force is not None:
        vs = vsys_force
    fs = g * (1.0 - (vb or 0.0) / C) * (1.0 + (vs or 0.0) / C)
    ins = np.zeros(n, bool)
    for fr in rest:
        ins |= (fs >= fr * (1.0 - HALF / C)) & (fs <= fr * (1.0 + HALF / C))
    return float(ins.mean()), known


MASK, NVSYS = {}, 0
for i in IA + IB:
    f, kn = masked_share(i)
    MASK[i] = f
    NVSYS += kn and (i in IA)

if DRIVE == 7:                     # the crossing-conditioned figure comes back
    _old = float(texval('CxOccPerWinPct')) / 100.0
    for i in MASK:
        MASK[i] = _old

P_UNMASKED = {i: PEXC[i] * (1.0 - MASK[i]) for i in PEXC}
E_REL = sum(P_UNMASKED[i] for i in IA if i in P_UNMASKED)
W_MASK = 1.0 - E_REL / E_TRIG_REL                     # the share it takes
MASK_MED = float(np.median([MASK[i] for i in IA]))
N_FULL = sum(1 for i in IA if MASK[i] > 0.999)
P_FULL = sum(PEXC[i] for i in IA if i in PEXC and MASK[i] > 0.999)

#: the figure the body used to print, kept only to measure the move
OCC_OLD = float(texval('CxOccPerWinPct')) / 100.0
E_OLD = E_TRIG_REL * (1.0 - OCC_OLD)

#: the sensitivity to an unmeasured systemic velocity, measured not assumed
W_SPAN = []
for vf in VSYS_SPAN:
    e = sum(PEXC[i] * (1.0 - masked_share(i, vsys_force=vf)[0])
            for i in IA if i in PEXC)
    W_SPAN.append(1.0 - e / E_TRIG_REL)
VSYS_SENS_PCT = 100.0 * (max(W_SPAN) - min(W_SPAN))

# =====================================================================
# (5) the reference set: the RELEASED census, window by window
# =====================================================================
#: Every window on this side of the comparison is one the deposited catalogue
#: tabulates, so the expectation is a sum over rows a reader holds and nothing
#: is carried at a mean rate.  The archival-tail Class A windows are counted
#: and named, and so are the crossings in them, but outside the comparison.
N_A_REL = int(texval('NWinA'))
N_A_CEN = int(texval('VnWinA'))
N_A_TAIL = N_A_CEN - N_A_REL
N_A_REF = N_A_REL
if DRIVE == 3:
    N_A_REF = N_A_CEN              # the expectation reaches past the deposit
SCALE = N_A_REF / float(N_A_REL)
E_TRIG = E_TRIG_REL * SCALE
E_CEN = E_REL * SCALE

# =====================================================================
# the observed side: the ledger's own set, over the same windows
# =====================================================================
WINSPAN = collections.defaultdict(list)
for i, r in enumerate(CAT):
    lo, hi = float(r['flo_GHz']), float(r['fhi_GHz'])
    WINSPAN[r['eb']].append((min(lo, hi), max(lo, hi), i))


def window_of(eb, freq):
    """The released window a crossing falls in, by position in frequency and
    never by a name.  None when the block is not in the released catalogue."""
    hit = [i for lo, hi, i in WINSPAN.get(eb, [])
           if lo - 1e-6 <= freq <= hi + 1e-6]
    return hit[0] if hit else None


#: THE ATTRIBUTION RULE, APPLIED HERE WITH THE NULL'S OWN MASK.  A3 requires it
#: to reproduce every attribution the ledger makes, so the mask that reduces the
#: expectation cannot be a different list from the mask that classifies the
#: crossings.  Where the ledger is the stricter of the two the difference is
#: reported and named, because a coincidence reported as a coincidence rather
#: than as an attribution is exactly that case.
def in_null_mask(r):
    fs = r['frame']['f_stellar']
    return bool(np.any((fs >= REST * (1.0 - HALF / C))
                       & (fs <= REST * (1.0 + HALF / C))))


def adopted_attributed(r):
    """The disposition the paper reports, from the module that owns the rule:
    inside the searched mask, and not a coincidence of a noted species."""
    inside = abs(mf.nearest(r['frame']['f_stellar'], mf.TRANS)[2]) <= HALF
    return bool(inside and not mf.note_reason(r['frame']['line'],
                                              r['frame']['dv_stellar']))


LED_ATTR = [r for r in LROWS if adopted_attributed(r)]
NOTED = [r for r in LROWS if not adopted_attributed(r)
         and mf.note_reason(r['frame']['line'], r['frame']['dv_stellar'])]
DISAGREE = [r for r in LROWS if in_null_mask(r) != adopted_attributed(r)]

UNATTR = [r for r in LROWS if not adopted_attributed(r)]
if DRIVE == 4:
    UNATTR = UNATTR[:-1]                      # the set and the routes diverge

PERWIN = collections.Counter()
for r in LROWS:
    i = window_of(r['eb'], r['freq'])
    if i is not None:
        PERWIN[i] += 1
if DRIVE == 5 and PERWIN:
    PERWIN[next(iter(PERWIN))] += 1           # two crossings in one window
MAX_PER_WIN = max(PERWIN.values())
BLK_MULTI = {e: n for e, n in
             collections.Counter(r['eb'] for r in LROWS).items() if n > 1}

OBS_IN, OBS_TAIL, OBS_FLAG = [], [], []
for r in UNATTR:
    i = window_of(r['eb'], r['freq'])
    if i is None:
        OBS_TAIL.append(r)
    elif CAT[i]['search_class'] == 'A':
        OBS_IN.append(r)
    else:
        OBS_FLAG.append(r)
#: ★ The observed side is the unattributed crossings that lie in a RELEASED
#: Class A window -- the same set the expectation is summed over.  The tail
#: crossings are counted and named, and are not added to it.
N_OBS = len(OBS_IN)
N_TAIL = len(OBS_TAIL)
TAIL_STARS = sorted({r['display'].replace('~', ' ') for r in OBS_TAIL})
TAIL_BLOCKS = sorted({r['eb'] for r in OBS_TAIL})

#: the arithmetic route to the same count, from the macro layer
ROUTE_MACRO = (int(texval('MkUnattr')) - int(texval('EvNCrossFlag'))
               - len(OBS_TAIL))

#: and the census record's own verdict on where those blocks belong
TAIL_IN_CENSUS = [b for b in TAIL_BLOCKS
                  if b in FOLLOW['census_blocks_also_covering']]
TAIL_IN_FOLLOWUP = [b for b in TAIL_BLOCKS if b in FOLLOW['blocks']]
CEN_ARRIVED = {t[1]: t[3] for t in RECON['reconciliation']['arrived']}

# ----------------------------------------------- both classes, one statement
FLAG_EB = texval('BqFailBlock').replace('\\_', '_')
IB_CLEAN = [i for i in IB if CAT[i]['eb'] != FLAG_EB]
E_SURV = E_CEN + sum(P_UNMASKED[i] for i in IB_CLEAN if i in P_UNMASKED)
OBS_B_CLEAN = sum(1 for i in IB_CLEAN if CAT[i]['crossing'] == 'True')

# =====================================================================
# (1) the interval: execution blocks resampled, control ensembles with them
# =====================================================================
#: Three terms, one device.  (a) The finite control ensemble: a window's rate
#: is a fraction of \NCtrl probes, so it is redrawn as a binomial on its own
#: measured rate.  (b) Block dependence: windows share execution blocks, so the
#: BLOCKS are resampled, not the windows.  (c) The one assumption the searched
#: data cannot test -- that a star behaves like a control position in its own
#: field -- which the reserved blocks fix only to the accuracy a handful of
#: events allows; its own block resampling multiplies the expectation, centred
#: on the measured ratio so that no departure is applied, only its uncertainty.
rng = np.random.default_rng(SEED)
BLK = collections.defaultdict(list)
for i in IA:
    if i in PEXC:
        BLK[CAT[i]['eb']].append(i)
EBS = sorted(BLK)
NB = len(EBS)
NCTRL = {i: ctrl_vector(i).size for i in IA if i in PEXC}

BV = np.empty((NB, NREAL))
NW = np.empty(NB)
for j, e in enumerate(EBS):
    ws = BLK[e]
    NW[j] = len(ws)
    acc = np.zeros(NREAL)
    for i in ws:
        n = NCTRL[i]
        acc += rng.binomial(n, PEXC[i], NREAL) / float(n) * (1.0 - MASK[i])
    BV[j] = acc

pick = rng.integers(0, NB, size=(NBOOT, NB))
real = rng.integers(0, NREAL, size=(NBOOT, NB))
BOOT_NULL = (BV[pick, real].sum(axis=1) / NW[pick].sum(axis=1)) * N_A_REF

# the exchangeability factor, resampled over the reserved blocks
HO_FINE = [r for r in HOL if r['res'].startswith('fine')]


def ho_rate(rows):
    obs = sum(1 for r in rows if r.get('star_snr') is not None
              and float(r['star_snr']) >= TRIG)
    exp = sum(sum(1 for x in r['ctrl_all'] if x >= TRIG)
              / float(len(r['ctrl_all'])) for r in rows if r.get('ctrl_all'))
    return obs, exp


HO_OBS, HO_EXP = ho_rate(HO_FINE)
HO_RATIO = HO_OBS / HO_EXP
_by = collections.defaultdict(list)
for r in HO_FINE:
    _by[r['eb']].append(r)
_hebs = sorted(_by)
_bo = np.array([ho_rate(_by[e])[0] for e in _hebs], float)
_be = np.array([ho_rate(_by[e])[1] for e in _hebs], float)
_pk = rng.integers(0, len(_hebs), size=(NBOOT, len(_hebs)))
_so, _se = _bo[_pk].sum(axis=1), _be[_pk].sum(axis=1)
FACTOR = (_so[_se > 0] / _se[_se > 0]) / HO_RATIO
if DRIVE == 6:
    FACTOR = np.ones_like(FACTOR)       # the dominant term is dropped again

BOOT = (BOOT_NULL[rng.integers(0, BOOT_NULL.size, NBOOT)]
        * FACTOR[rng.integers(0, FACTOR.size, NBOOT)])
LO, HI = (float(np.percentile(BOOT, 2.5)), float(np.percentile(BOOT, 97.5)))
LO_NULL, HI_NULL = (float(np.percentile(BOOT_NULL, 2.5)),
                    float(np.percentile(BOOT_NULL, 97.5)))

# =====================================================================
# THE TRANSFER TO STELLAR POSITIONS, APPLIED AND NOT ONLY CARRIED
# =====================================================================
#: The expectation is a sum of CONTROL exceedance rates.  The reserved blocks
#: measure the same quantity at the star, and their ratio is the measured
#: star-to-control difference in exactly the quantity used here, so applying it
#: is one multiplication and needs no model.  The published uncorrected sum is
#: kept beside it because the ratio is itself consistent with unity.
HO_RATIO_APPLIED = HO_RATIO
if DRIVE == 8:
    HO_RATIO_APPLIED = 3.0 * HO_RATIO    # the correction is not the measured one
E_X = E_CEN * HO_RATIO_APPLIED

#: ★ WHY THE FINE-STRATUM DEPARTURE CANNOT BE TESTED BY REMOVING CROSSINGS.
#: The windows counted there are those whose star both reaches the trigger and
#: outranks every control, and reaching the trigger IS holding a crossing, so
#: the conditioned set and the crossing-bearing set are the same windows and
#: removing one empties the other.  What can be said is how many of them hold a
#: crossing the mask attributes, which is the quantity the sentence in print was
#: reaching for.  A10 asserts the identity that makes the removal impossible.
SFIRST = [i for i in IA
          if int(CAT[i]['n_ctrl_ge_star']) == 0
          and float(CAT[i]['star_snr']) >= TRIG]
ATTR_WIN = {window_of(r['eb'], r['freq']) for r in LED_ATTR}
CROSS_WIN = {window_of(r['eb'], r['freq']) for r in LROWS}
if DRIVE == 10:
    CROSS_WIN.discard(SFIRST[0])       # one of them stops holding a crossing
N_SFIRST_ATTR = sum(1 for i in SFIRST if i in ATTR_WIN)
N_SFIRST_CROSS = sum(1 for i in SFIRST if i in CROSS_WIN)

#: WHAT THE INTERVAL CANNOT SEE.  If the true chance rate sat at the bottom of
#: the resampled range, the observed count would be that rate plus an added
#: population, and the comparison could not tell the two apart.  The largest
#: such population is the observed count less the floor of the interval -- the
#: quantity "a departure of about 35 per cent" was standing in for and getting
#: wrong by more than a factor of two.
ADD_BLIND = int(math.floor(N_OBS - LO))
if DRIVE == 9:
    ADD_BLIND = int(math.floor(N_OBS - HI))   # read off the wrong end

# =====================================================================
# what was found
# =====================================================================
print('chance_v414: round %d%s' % (ROUND, '' if DRIVE is None
                                   else '  (drive %d)' % DRIVE))
print('  join: %d of %d catalogue rows carry a control vector, %d control '
      'maxima disagree' % (len(JOIN), len(CAT), len(MISMATCH)))
print('  ONE EXPECTATION over the RELEASED census: %d Class A windows, every '
      'one of them tabulated window by window (%d further Class A windows '
      'arrived with the archival tail and are outside it)'
      % (N_A_REF, N_A_TAIL))
print('    trigger   %.2f expected to reach the trigger by chance (%.2f over '
      'the tabulated windows)' % (E_TRIG, E_TRIG_REL))
print('    mask      the attribution windows take %.1f per cent of that, '
      'measured on the windows\' own grids (median share per window %.1f per '
      'cent; %d windows lie wholly inside the mask and carry %.2f of the '
      'trigger expectation)'
      % (100 * W_MASK, 100 * MASK_MED, N_FULL, P_FULL))
print('    expected  %.2f unattributed Class A crossings, %.0f-%.0f allowed by '
      'resampling the execution blocks (%.0f-%.0f from the control ensembles '
      'and the blocks alone)' % (E_CEN, LO, HI, LO_NULL, HI_NULL))
print('    observed  %d unattributed crossings in those windows; %d further '
      'lie in archival-tail blocks and are reported beside the comparison '
      '(%s, %s)' % (N_OBS, N_TAIL,
                    ' / '.join(TAIL_STARS), ' / '.join(TAIL_BLOCKS)))
print('    transfer  stars reach the trigger %.3f times as often as their own '
      'controls predict (reserved blocks, %d against %.2f); applying that '
      'gives %.2f expected against the %d observed'
      % (HO_RATIO, HO_OBS, HO_EXP, E_X, N_OBS))
print('    cannot see  an added population of up to %d events -- %.0f per cent '
      'of the observed count -- is absorbed by the %.1f-%.1f range'
      % (ADD_BLIND, 100.0 * ADD_BLIND / N_OBS, LO, HI))
print('    the move  the figure in print was %.1f per cent and %.1f expected; '
      'the honest figure is %.1f per cent and %.1f, so the observed count '
      'moves from below the expectation to above it'
      % (100 * OCC_OLD, E_OLD * SCALE, 100 * W_MASK, E_CEN))
print('  units: the greatest number of crossings in any one window is %d; '
      '%d blocks hold more than one crossing %s'
      % (MAX_PER_WIN, len(BLK_MULTI),
         sorted((e.replace('A002_', ''), n) for e, n in BLK_MULTI.items())))
print('  HD 14055: %s' % '; '.join(
    '%s arrived with the census as "%s", census_blocks_also_covering %s, '
    'follow-up stratum %s' % (b, CEN_ARRIVED.get(b, '?'),
                              b in TAIL_IN_CENSUS, b in TAIL_IN_FOLLOWUP)
    for b in TAIL_BLOCKS))
print('  one mask: %d attributed / %d unattributed adopted, %d coincidences '
      'reported as coincidences (%s), %d crossings classified differently by '
      'the two sides'
      % (len(LED_ATTR), len(UNATTR), len(NOTED),
         ', '.join(r['display'] for r in NOTED), len(DISAGREE)))
print('  systemic velocity measured for %d of %d Class A windows; over the '
      'full +-%.0f km/s range the mask share moves %.1f points'
      % (NVSYS, len(IA), VSYS_SPAN[1], VSYS_SENS_PCT))
print('  both classes: %.2f expected against the same %d observed; the clean '
      'coarse windows hold %d crossings' % (E_SURV, N_OBS, OBS_B_CLEAN))

# =====================================================================
# assertions
# =====================================================================
print('\nassertions')
ck('A1 THE JOIN IS VALIDATED AND THE EXPECTATION IT BUILDS REPRODUCES THE '
   'PUBLISHED TRIGGER SUM over the released Class A windows',
   not MISMATCH and len(NOVEC) <= 1
   and abs(E_TRIG_REL - float(texval('StExpTrig'))) < 0.05,
   '%.3f against the published %s, %d control maxima disagree, %d rows '
   'without a vector'
   % (E_TRIG_REL, texval('StExpTrig'), len(MISMATCH), len(NOVEC)))

ck('A2 THE MASK FACTOR IS A PROPERTY OF THE WINDOWS AND NOT OF THE CROSSINGS, '
   'and it is published in the direction it moves',
   W_MASK > OCC_OLD and E_CEN < E_OLD * SCALE and 0.0 < W_MASK < 0.5,
   'window-by-window %.3f against the crossing-conditioned %.3f; expectation '
   '%.2f against %.2f' % (W_MASK, OCC_OLD, E_CEN, E_OLD * SCALE))

ck('A3 ONE MASK ON BOTH SIDES: the transition list that reduces the '
   'expectation attributes exactly the crossings the paper attributes, over '
   'all of them and in both directions',
   not DISAGREE and len(LED_ATTR) > 0 and len(NOTED) > 0,
   '%d of %d crossings classified differently by the null\'s mask and by the '
   'reported disposition%s; %d coincidences reported as coincidences'
   % (len(DISAGREE), len(LROWS),
      '' if not DISAGREE else ': ' + ', '.join(
          '%s %.4f' % (r['display'], r['freq']) for r in DISAGREE[:4]),
      len(NOTED)))

ck('A3b THE UNITS MATCH BY MEASUREMENT: a window contributes the probability '
   'that a position in its field reaches the trigger, so the sum is a number '
   'of windows -- and no window holds more than one crossing',
   MAX_PER_WIN == 1 and len(BLK_MULTI) > 0,
   'greatest crossings per window %d; %d blocks hold more than one, in '
   'distinct windows' % (MAX_PER_WIN, len(BLK_MULTI)))

ck('A4 ONE POPULATION: the observed count is the ledger\'s own set of '
   'unattributed crossings lying in RELEASED Class A windows, and the '
   'arithmetic route through the macro layer agrees with the set',
   N_OBS == ROUTE_MACRO
   and N_OBS + N_TAIL == int(texval('EvNUnattrQp'))
   and len(OBS_FLAG) == int(texval('EvNCrossFlag'))
   and N_OBS + N_TAIL + len(OBS_FLAG) == int(texval('MkUnattr')),
   'set %d against the macro route %d; %d + %d tail against the published %s; '
   '%d in the flagged block against the published %s; %d + %d + %d against the '
   'published %s'
   % (N_OBS, ROUTE_MACRO, N_OBS, N_TAIL, texval('EvNUnattrQp'),
      len(OBS_FLAG), texval('EvNCrossFlag'), N_OBS, N_TAIL, len(OBS_FLAG),
      texval('MkUnattr')))

ck('A5 BOTH SIDES RUN OVER THE RELEASED CENSUS AND NOTHING ELSE: the '
   'expectation is summed over the Class A windows the deposit tabulates, '
   'every counted crossing lies in one of them, and the archival-tail '
   'crossings are named and counted outside the comparison',
   N_A_REF == N_A_REL
   and all(window_of(r['eb'], r['freq']) is not None for r in OBS_IN)
   and all(window_of(r['eb'], r['freq']) is None for r in OBS_TAIL)
   and N_TAIL == 2 and len(TAIL_BLOCKS) == 2
   and all(CEN_ARRIVED.get(b) == 'tail' for b in TAIL_BLOCKS)
   and sorted(TAIL_IN_CENSUS) == sorted(TAIL_BLOCKS)
   and not TAIL_IN_FOLLOWUP
   and N_A_TAIL > 0,
   'expectation over %d windows against the released %d; %d counted and %d '
   'set aside in %d blocks, arrival %s, census blocks %d, follow-up blocks '
   '%d; %d archival-tail Class A windows outside'
   % (N_A_REF, N_A_REL, N_OBS, N_TAIL, len(TAIL_BLOCKS),
      [CEN_ARRIVED.get(b) for b in TAIL_BLOCKS], len(TAIL_IN_CENSUS),
      len(TAIL_IN_FOLLOWUP), N_A_TAIL))

ck('A6 THE INTERVAL CARRIES THE TERM THAT DOMINATES IT: the resampled '
   'expectation is centred on the point estimate, and the exchangeability '
   'calibration widens it strictly beyond the control ensembles and the '
   'blocks alone',
   abs(float(np.median(BOOT_NULL)) - E_CEN) < 0.05 * E_CEN
   and LO < LO_NULL and HI > HI_NULL and HI / LO > 2.0,
   'bootstrap median %.2f against the point estimate %.2f; %.1f-%.1f against '
   '%.1f-%.1f from the blocks alone'
   % (float(np.median(BOOT_NULL)), E_CEN, LO, HI, LO_NULL, HI_NULL))

ck('A7 THE INTERVAL DOES NOT SUPPORT A FLOOR, which is why the sentence it '
   'used to support is withdrawn: the observed count sits inside it and so '
   'does a count a third larger',
   LO <= N_OBS <= HI and LO <= 1.33 * N_OBS <= HI,
   'observed %d and %.0f both inside %.1f-%.1f'
   % (N_OBS, 1.33 * N_OBS, LO, HI))

ck('A8 THE TRANSFER TO STELLAR POSITIONS IS APPLIED, AND IT IS THE ONE THE '
   'RESERVED BLOCKS PUBLISH: the ratio here is the hold-out\'s own, and with '
   'it applied the observed count still sits inside the interval and within a '
   'quarter of its width of the expectation',
   abs(HO_RATIO - float(texval('StHoRatio'))) < 0.005
   and HO_OBS == int(texval('StHoObs'))
   and LO <= E_X <= HI
   and abs(N_OBS - E_X) < 0.25 * (HI - LO),
   'ratio %.4f against the published %s (%d events against %s); corrected '
   'expectation %.2f against %d observed, %.2f apart in an interval %.1f wide'
   % (HO_RATIO, texval('StHoRatio'), HO_OBS, texval('StHoObs'), E_X, N_OBS,
      abs(N_OBS - E_X), HI - LO))

ck('A9 THE SIZE OF THE POPULATION THE COMPARISON CANNOT SEE IS MEASURED OFF '
   'THE INTERVAL AND IS THE LARGEST SUCH POPULATION: one more event would '
   'carry the implied chance rate below the floor of the range',
   ADD_BLIND >= 1 and N_OBS - ADD_BLIND >= LO
   and N_OBS - (ADD_BLIND + 1) < LO,
   '%d added events leave %.2f against a floor of %.2f, and %d would leave '
   '%.2f' % (ADD_BLIND, N_OBS - ADD_BLIND, LO, ADD_BLIND + 1,
             N_OBS - ADD_BLIND - 1.0))

ck('A10 EVERY WINDOW OF THE FINE-STRATUM DEPARTURE HOLDS A CROSSING, so the '
   'departure cannot be tested by removing the windows that hold one, and '
   'what can be said instead is how many of them the mask attributes',
   len(SFIRST) == int(texval('NStageOneFine'))
   and N_SFIRST_CROSS == len(SFIRST)
   and 0 < N_SFIRST_ATTR < len(SFIRST),
   '%d windows against the published %s; %d hold a crossing and %d hold an '
   'attributed one' % (len(SFIRST), texval('NStageOneFine'), N_SFIRST_CROSS,
                       N_SFIRST_ATTR))

# =====================================================================
# macros
# =====================================================================
m('CeNWin', '%d' % N_A_REF)
m('CeNWinTail', '%d' % N_A_TAIL)
m('CeExpTrig', '%.1f' % E_TRIG)
m('CeMaskPct', '%.0f' % (100 * W_MASK))
m('CeMaskPctMed', '%.1f' % (100 * MASK_MED))
m('CeNFullMask', '%d' % N_FULL)
m('CeExp', '%.1f' % E_CEN)
m('CeLo', '%.0f' % LO)
m('CeHi', '%.0f' % HI)
m('CeLoNull', '%.0f' % LO_NULL)
m('CeHiNull', '%.0f' % HI_NULL)
m('CeObs', '%d' % N_OBS)
m('CeExpX', '%.1f' % E_X)
m('CeAddBlind', '%d' % ADD_BLIND)
m('CeFirstAttr', '%d' % N_SFIRST_ATTR)
m('CeNTailCross', '%d' % N_TAIL)
m('CeNTailCrossWord', ['no', 'one', 'two', 'three', 'four'][N_TAIL])
m('CeTailStar', ' / '.join(s.replace(' ', '~') for s in TAIL_STARS))
m('CeExpSurv', '%.1f' % E_SURV)
m('CeNBoot', format(NBOOT, ',').replace(',', '\\,'))
m('CeNVsys', '%d' % NVSYS)
m('CeVsysSensPct', '%.1f' % VSYS_SENS_PCT)

# =====================================================================
# write
# =====================================================================
if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    if DRIVE is None:
        raise SystemExit(1)

hdr = ['%% GENERATED by chance_v414.py (round %d) -- do not hand-edit.' % ROUND,
       '%% One chance expectation for the unattributed Class A crossings,',
       '%% measured window by window over the RELEASED census and over no other',
       '%% set, with one interval from resampled execution blocks, the measured',
       '%% star-to-control transfer applied to it, and the archival-tail',
       '%% crossings named and counted outside the comparison.']
with open(OUT_TEX, 'w') as fh:
    fh.write('\n'.join(hdr + sorted(OUT)) + '\n')
json.dump(dict(round=ROUND, drive=DRIVE,
               n_win_A_reference=N_A_REF,
               n_win_A_census=N_A_CEN, n_win_A_released=N_A_REL,
               n_win_A_tail=N_A_TAIL,
               e_trigger_census=E_TRIG, e_trigger_released=E_TRIG_REL,
               mask_share_weighted=W_MASK, mask_share_median=MASK_MED,
               n_windows_wholly_masked=N_FULL,
               p_trigger_wholly_masked=P_FULL,
               mask_share_previous=OCC_OLD,
               e_chance=E_CEN, e_chance_previous_factor=E_OLD * SCALE,
               interval=[LO, HI], interval_null_only=[LO_NULL, HI_NULL],
               observed=N_OBS, observed_tabulated=len(OBS_IN),
               e_chance_transfer_applied=E_X,
               transfer_ratio=HO_RATIO, transfer_obs=HO_OBS,
               transfer_exp=HO_EXP,
               added_population_not_excluded=ADD_BLIND,
               stage_one_fine_windows=len(SFIRST),
               stage_one_fine_holding_a_crossing=N_SFIRST_CROSS,
               stage_one_fine_attributed=N_SFIRST_ATTR,
               observed_tail=[(r['display'], r['eb'], r['freq'])
                              for r in OBS_TAIL],
               observed_flagged=len(OBS_FLAG), route_macro=ROUTE_MACRO,
               max_crossings_per_window=MAX_PER_WIN,
               blocks_with_several_crossings=BLK_MULTI,
               tail_blocks_in_census=TAIL_IN_CENSUS,
               tail_blocks_in_followup=TAIL_IN_FOLLOWUP,
               census_arrival={b: CEN_ARRIVED.get(b) for b in TAIL_BLOCKS},
               mask_vs_ledger=dict(
                   n_transitions_searched=len(mf.TRANS),
                   n_transitions_attributing=len(NULL_TRANS),
                   attributed=len(LED_ATTR),
                   classified_differently=len(DISAGREE),
                   reported_as_coincidence=[r['display'] for r in NOTED]),
               vsys_measured_windows=NVSYS, vsys_sensitivity_pct=VSYS_SENS_PCT,
               e_survey=E_SURV, observed_coarse_clean=OBS_B_CLEAN,
               n_boot=NBOOT, n_realisations=NREAL, seed=SEED),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('\nwrote %s (%d macros) and %s'
      % (os.path.basename(OUT_TEX), len(OUT), os.path.basename(OUT_JSON)))
