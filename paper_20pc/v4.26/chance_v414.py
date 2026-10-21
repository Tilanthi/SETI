#!/usr/bin/env python3
r"""Round 310: ONE CHANCE EXPECTATION, MEASURED WINDOW BY WINDOW, OVER THE
RELEASED CENSUS, WITH ONE INTERVAL AND THE TRANSFER TO STELLAR POSITIONS
APPLIED TO IT.

★★★★ AND ONE PROBABILITY IN PLACE OF THREE INTERVALS.  A single observed count
cannot be compared with an interval on its own mean: the quantity is the
probability that chance delivers a count at least as large as the one seen.
Measured at the control positions ALONE that probability is \CeProbNull, so
the count is what the control positions predict and the step to the star is
not the term that reconciles them -- the comparison never needed it.  The
three intervals the paper quoted (on the null rate, on the stepped rate, and
on the count) are replaced by that one probability, and the coverage of every
interval still quoted is stated: \CeCovPct per cent.

★★★★ AND THE STEP IS NO LONGER READ AT THE TRIGGER.  The ratio at T = 5 is
formed from the \CeStepNX above-trigger out-of-mask stellar cells that ARE the
crossings under test, so applying it calibrated the null on its own test
sample.  It is measured instead in the band \CeStepLevLo <= T < \CeStepLevHi,
on \CeStepNStar stellar events, where no carrier claim is at stake: \CeStep
(\CeStepLo--\CeStepHi at \CeCovPct per cent, resampled execution blocks)
against the \CeTrAt in print.  A band count is the difference of two
cumulative counts, so every cell belonging to a tabulated crossing is counted
in both terms and cancels -- measured, not assumed, by A14.

★★★ AND THE POPULATION THE COMPARISON CANNOT SEE IS NOW A LIMIT WITH A
COVERAGE: \CeAddLim events, the largest added population that still leaves a
count as low as the observed one credible at \CeCovPct per cent, read off the
same predictive distribution instead of off the floor of a count range.

★★ A7 IS WITHDRAWN.  It asserted "THE OBSERVED COUNT NEEDS THE MEASURED STEP
TO THE STAR" -- the statistical error itself, written into the build as a
requirement.  A7b replaces it and A9 and A13 are relabelled as the withdrawn
constructions they validate.

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

★★ THE ATTRIBUTED SHARE OF THE CONTROL EXCEEDANCES IS MEASURED ON THE
CHANNELS THEY LAND ON.  It used to be the share of a window's channel grid
that the mask covers, "a control maximum being free to fall on any channel" --
and in the same breath this calculation said that the fields which hold real
emission are where a control position most often triggers.  In those fields a
control maximum lands preferentially ON the line channels, so a uniform share
under-attributes them and INFLATES the unattributed expectation, which
flatters the null.  The retained per-channel profiles record the channel of
every control maximum, so the quantity is now measured: 88 of 302 control
exceedances land inside the mask, \CeMaskPct per cent of the trigger
expectation against \CeUnifPct per cent for a uniform landing, and the expectation falls from 28.9 to \CeExp
against \CeObs observed.  A11 validates the reconstruction -- the rebuilt
mask reproduces every stored in-mask flag and every stored grid share, which
is what stands between this and a channel-reversal defect -- and A12 publishes
the direction the bias ran.

★★ AND THE RANGE IS NOW A RANGE OF COUNTS.  \CeLo--\CeHi is the uncertainty
in the RATE; chance delivers a NUMBER, which scatters about that rate.  Drawing
a count from each resampled rate gives \CeCntLo--\CeCntHi, and the population
the comparison cannot see is read off that floor: \CeAddBlind events, not the
smaller figure the rate range alone supports.

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

The assertion and drive counts are MEASURED from the source and printed at the
end of every run rather than typed here: the pair this header carried said
"twenty-two assertions, twenty-six drives" against a file that by then held
twenty-four and twenty-eight, and a stale count in a docstring is how a
generator stops being able to say what it tests.  `--drive 0` means "no
perturbation, but do not write a path production reads"; every drive writes
`*_driveN.*` only.

    python3 chance_v414.py [--drive N]
"""
import bisect
import collections
import csv
import glob
import json
import math
import os
import re
import sys

import numpy as np
from scipy.special import gammainc, gammaincc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import manuscript as mscript                                     # noqa: E402
import maskframe_v411 as mf                                      # noqa: E402
import star_alias as sa                                          # noqa: E402
import calib_r15 as c15                                          # noqa: E402

ROUND = 310
TRIG = 5.0
NBOOT = 20000
NREAL = 2000
SEED = 310

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])

#: ★★★★ WHICH FIELD THE STATISTIC IS READ OVER.  Equation 1 divides by the
#: MAD over the control positions, so T_star is a property of the annulus as
#: well as of the cell, and the two readings of the survey -- the whole
#: primary beam and the narrower first field -- are two different statistics.
#: The adopted reading is the whole primary beam on BOTH sides of the
#: comparison.  `--field narrow` rebuilds both sides on the other one, so the
#: dependence can be reported as a measurement; it writes only
#: `*_field<name>.*` and is never a production path.
FIELD = None
for _i, _a in enumerate(sys.argv):
    if _a == '--field':
        FIELD = sys.argv[_i + 1]
assert FIELD in (None, 'adopted', 'narrow'), FIELD
SUFFIX = ('' if DRIVE is None else '_drive%d' % DRIVE) + (
    '' if FIELD is None else '_field%s' % FIELD)

# ★ The production name is a literal and only the drive branch is built by
#   format, so `roundcollide` can resolve the claim on round 310.
OUT_TEX = os.path.join(HERE, 'survey_numbers_round310.tex' if not SUFFIX
                       else 'survey_numbers_round310%s.tex' % SUFFIX)
OUT_JSON = os.path.join(HERE, 'chance_v414%s.json' % SUFFIX)
#: A FIELD RUN WRITES NO MACRO FILE AT ALL.  It is read through its JSON
#: by round 311, and a `survey_numbers_round*.tex` that nothing can input is
#: an orphan the build is right to refuse: the macros of the other reading
#: are published by the generator that compares the two, not by this one.
WRITE_TEX = FIELD is None

OUT = []
fail = []


def m(name, val):
    assert name.isalpha(), 'a macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def mval(name):
    """The value this generator has already published for `name`, read back
    from the emitted text so that a check sees the printed rounding and not
    an unrounded float."""
    pre = '\\newcommand{\\%s}{' % name
    for x in OUT:
        if x.startswith(pre):
            return x[len(pre):-1]
    raise AssertionError('not published: %s' % name)


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
    """The window's own control ensemble, read over the whole primary beam
    where that reading exists -- the adopted statistic.  Under
    `--field narrow` the first, narrower field is used instead, on this side
    of the comparison and on the observed side alike."""
    if FIELD == 'narrow':
        src = JOIN.get(i)
    else:
        src = REPJOIN.get(i) if i in REPJOIN else JOIN.get(i)
    return None if src is None else np.asarray(src['ctrl_all'], float)


CATKEY = collections.defaultdict(list)
for i, r in enumerate(CAT):
    if r['search_class'] == 'A':
        CATKEY[wkey(r['eb'], r['flo_GHz'], r['fhi_GHz'])].append(i)

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
# ★ ONE LIST, NOT A FILTERED ONE.  The species whose coincidences were reported
# as notes rather than dispositions is no longer IN the mask, so the null's mask
# and the attribution mask are the same object and there is nothing left here to
# filter.  Drive 2 still makes them diverge -- by giving the null the WHOLE
# query, which is what the released in-mask flags were stored under -- so A3
# remains a check that can fail.
NULL_TRANS = dict(mf.TRANS)
if DRIVE == 2:                     # the mask list and the dispositions diverge
    NULL_TRANS = dict(mf.TRANS_ALL)
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

W_UNIF = (sum(PEXC[i] * MASK[i] for i in IA if i in PEXC)
          / sum(PEXC[i] for i in IA if i in PEXC))
MASK_MED = float(np.median([MASK[i] for i in IA]))
N_FULL = sum(1 for i in IA if MASK[i] > 0.999)
P_FULL = sum(PEXC[i] for i in IA if i in PEXC and MASK[i] > 0.999)

# =====================================================================
# ★★ THE ATTRIBUTED SHARE IS MEASURED ON THE CHANNELS THE CONTROL MAXIMA
#    ACTUALLY LAND ON, not on the share of the grid the mask covers.
# =====================================================================
#: A control maximum is NOT free to land anywhere.  In a field that holds real
#: emission it lands preferentially on the line channels, and those fields are
#: where a control position most often reaches the trigger -- which this
#: calculation said in words while using a uniform landing in arithmetic.  The
#: bias runs one way: a uniform share under-attributes the control exceedances
#: and so INFLATES the unattributed expectation, which flatters the null.
#:
#: The retained per-channel profiles record the channel of every control
#: maximum, so the quantity is measured directly: of the control positions
#: whose window maximum reaches the trigger, the share whose own channel lies
#: inside the attribution mask.  Weighting is by the window's own exceedance
#: rate, which is the weighting the sum uses.
#:
#: THE ONE HAZARD, AND HOW IT IS CLOSED.  A channel index means nothing
#: without the direction of the window's frequency axis, and a descending
#: spectral window is stored reversed in one product and not in another.  The
#: direction is taken from the export's own flo/fhi ORDER and then VALIDATED:
#: rebuilt this way, the mask reproduces every one of the stored in-mask flags
#: and every window's stored masked share exactly (A11).  Without the
#: validation this would be a channel-reversal defect waiting to happen.
CELLS = json.load(open(os.path.join(
    HERE, 'r15inputs/cells/cells_extract_result.json')))['windows']
#: ★ THE LIST THE STORED FLAGS WERE STORED UNDER, which is the whole query and
#: not the mask: the released export carries an in-mask flag per control
#: exceedance and a grid share per window, both computed when the mask still
#: held every species the query returns.  A11 validates the RECONSTRUCTION
#: against those stored values, so it must rebuild with the list they were made
#: with; A3 is what asserts that the mask the null uses and the mask the
#: attributions use are one list.
REST_FULL = np.array(sorted(v[0] for v in mf.TRANS_ALL.values()))


def _inmask(rest, fs):
    ins = np.zeros(fs.size, bool)
    for fr in rest:
        ins |= (fs >= fr * (1.0 - HALF / C)) & (fs <= fr * (1.0 + HALF / C))
    return ins


# =====================================================================
# (4b) the atmosphere, on one radius and in the frame the atmosphere occupies
# =====================================================================
#: An interpolated system-temperature residual occupies at least one of the
#: channels on which that temperature is measured and reaches into the wings
#: of the strong lines, so a cell within two such channels of a strong
#: atmospheric transition is treated as atmospheric.  THE RADIUS IS FIXED
#: FROM THE FROZEN SPECIFICATION AND NEVER FROM AN OBSERVED OFFSET, and it is
#: applied in the TOPOCENTRIC frame -- the atmosphere does not move with the
#: star -- to the crossings AND to the control exceedances alike.  A control
#: maximum lands on the same topocentric channels a crossing does, so
#: screening the observed side alone would lower the count against an
#: unchanged expectation and manufacture a deficit.  A23 is that symmetry.
TLSPEC = json.load(open(os.path.join(HERE, 'r15inputs/calib/calspec_r15.json')))
TSYS_RES_MHZ = float(TLSPEC['tsys_resolution_MHz'])
N_TSYS_CHAN = 2
TL_RAD = N_TSYS_CHAN * TSYS_RES_MHZ
_FLO = min(min(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in CAT)
_FHI = max(max(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in CAT)
TL_SEL = c15.telluric_lines(float(TLSPEC['t_atmosphere_K']), _FLO, _FHI)[1]
TL_ARR = sorted(x[0] for x in TL_SEL)
TL_SPECIES = {x[0]: x[1] for x in TL_SEL}


def tl_offset(f_ghz):
    """(line MHz, signed offset MHz) of the nearest atmospheric transition."""
    x = float(f_ghz) * 1e3
    j = bisect.bisect_left(TL_ARR, x)
    cand = [TL_ARR[k] for k in (j - 1, j, j + 1) if 0 <= k < len(TL_ARR)]
    best = min(cand, key=lambda a: abs(x - a))
    return float(best), float(x - best)


def telluric(r):
    """True for a crossing inside the radius of an atmospheric transition,
    read on its TOPOCENTRIC frequency.  Drive 28 reads it in the stellar
    frame instead, which is the frame the paper quotes and the wrong one."""
    f = r['frame']['f_stellar'] if DRIVE == 28 else r['freq']
    return bool(abs(tl_offset(f)[1]) <= TL_RAD)


CJOIN, CNOJOIN, VALBAD = {}, [], []
N_EXC = N_EXC_ATTR = N_EXC_FULL = N_EXC_TL = N_EXC_TL_ONLY = 0
#: ★★ v4.26 (A6).  THE SYMMETRY OF THE COMPARISON WAS STRUCTURAL AND NOTHING
#: ASSERTED IT.  The control maxima are carried to the star's own rest frame
#: through the same two velocity steps, on the same grid, as a cell at the
#: stellar position -- one grid per window serves both sides.  That is true
#: of the code and was true of no check, so the referee had to ask.  These
#: two counters put it under A11: FRAMEBAD is the number of windows whose
#: control-side velocities differ from the ones the crossing side uses, and
#: FRAMENOVSYS the number with no measured systemic velocity, which are taken
#: at rest ON BOTH SIDES and are therefore a declaration rather than a defect.
FRAMEBAD = FRAMENOVSYS = 0
EXC_BY_WIN = {}
for w in CELLS:
    if w['cls'] != 'A' or w['stratum'] == 'archival_tail':
        continue
    #: ★ The window is identified by its block and its edges; where several
    #: catalogue rows share that key -- which seven blocks do -- the star is
    #: matched through the project's own canonicaliser and, if that still
    #: leaves two, by which row's own statistic the retained profile
    #: reproduces.  A name alone would not do it: this extract carries one
    #: window under a pre-repair field name.
    k = wkey(w['eb'], w['lo'], w['hi'])
    idx = CATKEY.get(k, [])
    same = [j for j in idx
            if sa.canon(CAT[j]['star_name']) == sa.canon(w['star'])]
    cand = same or idx
    if len(cand) > 1:
        cand = [min(cand, key=lambda j: abs(float(CAT[j]['star_snr'])
                                            - w['adopted']))]
    if len(cand) != 1:
        CNOJOIN.append(w['key'])
        continue
    i = cand[0]
    r = REPJOIN.get(i) if i in REPJOIN else JOIN.get(i)
    if r is None:
        CNOJOIN.append(w['key'])
        continue
    g = np.linspace(w['lo'], w['hi'], w['nch'])
    if float(r['flo']) > float(r['fhi']):          # a descending window
        g = g[::-1]
    if DRIVE == 11:
        g = g[::-1]                                # the axis read backwards
    fs = g * (1.0 - w['v_bary'] / C) * (1.0 + w['v_sys'] / C)
    #: A6: the two velocities this grid is built with are the window's own,
    #: read back from the frame chain the crossing side uses.
    _vb, _vbs = mf.vbary(w['eb'], w['lo'])
    _vs, _vss, _b = mf.vsys(w['star'])
    if DRIVE == 29:
        _vs = (0.0 if (_vs or 0.0) else 30.0)    # the control side in another frame
    FRAMEBAD += int(_vb is None or abs(float(_vb) - w['v_bary']) > 1e-6)
    FRAMEBAD += int((_vs is None and abs(w['v_sys']) > 1e-12)
                    or (_vs is not None and abs(float(_vs) - w['v_sys']) > 1e-6))
    FRAMENOVSYS += int(_vs is None)
    im_full, im_null = _inmask(REST_FULL, fs), _inmask(REST, fs)
    if abs(float(im_full.mean()) - w['masked_share']) > 1e-9:
        VALBAD.append((w['key'], 'grid share'))
    exc = [c for c in w['ctrl'] if c['win_max'] >= TRIG]
    for c in exc:
        if bool(im_full[c['max_chan']]) != c['max_in_mask']:
            VALBAD.append((w['key'], 'channel %d' % c['max_chan']))
    #: the same radius, on the same topocentric grid the exceedance's own
    #: channel indexes into, and counted only where the molecular mask has
    #: not already taken it -- the two screens must not be double-counted.
    tlin = np.array([abs(tl_offset(float(f))[1]) <= TL_RAD for f in g])
    N_EXC += len(exc)
    N_EXC_FULL += sum(1 for c in exc if im_full[c['max_chan']])
    N_EXC_ATTR += sum(1 for c in exc if im_null[c['max_chan']])
    N_EXC_TL += sum(1 for c in exc if tlin[c['max_chan']])
    N_EXC_TL_ONLY += sum(1 for c in exc if tlin[c['max_chan']]
                         and not im_null[c['max_chan']])
    CJOIN[i] = w
    EXC_BY_WIN[i] = (len(exc), sum(1 for c in exc if im_null[c['max_chan']]))

A_MEAS = N_EXC_ATTR / float(N_EXC)
if DRIVE == 12:
    A_MEAS = W_UNIF                # the uniform landing comes back
if DRIVE == 7:
    # ★ drive 7 is the crossing-conditioned figure coming back, and until the
    # attributed share was measured it only had to perturb the grid shares.
    # It must now perturb the adopted share as well or A2 goes vacuous -- a
    # drive that stops driving anything is the defect this file keeps finding.
    A_MEAS = float(texval('CxOccPerWinPct')) / 100.0
#: the uniform-landing figure over the same windows and the same weighting,
#: so the comparison is like for like and not a comparison of two populations
W_UNIF_MEAS = (sum(PEXC[i] * MASK[i] for i in CJOIN)
               / sum(PEXC[i] for i in CJOIN))

#: the share of the exceedances that survive the molecular mask and are then
#: taken by the atmosphere as well, as a factor on every window's rate
_SURV_M = N_EXC - N_EXC_ATTR
TL_FAC = (_SURV_M - N_EXC_TL_ONLY) / float(_SURV_M) if _SURV_M else 1.0
if DRIVE == 27:
    TL_FAC = 1.0               # the observed side screened and the null not
#: the molecular mask alone, then the atmosphere on top of it, kept apart so
#: that each share is reported as its own and neither is credited to the other
P_MASKED_ONLY = {i: PEXC[i] * (1.0 - (A_MEAS if i in CJOIN else MASK[i]))
                 for i in PEXC}
P_UNMASKED = {i: P_MASKED_ONLY[i] * TL_FAC for i in PEXC}
E_REL_M = sum(P_MASKED_ONLY[i] for i in IA if i in P_MASKED_ONLY)
E_REL = sum(P_UNMASKED[i] for i in IA if i in P_UNMASKED)
W_MASK = 1.0 - E_REL_M / E_TRIG_REL                   # the share it takes
E_REL_UNIF = sum(PEXC[i] * (1.0 - MASK[i]) for i in IA if i in PEXC)
P_TRIG_MEAS = sum(PEXC[i] for i in CJOIN) / E_TRIG_REL

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

#: ★ THE SCREEN REACHES BOTH READINGS BECAUSE IT ACTS HERE.  A crossing the
#: atmosphere accounts for leaves the unattributed set exactly as an
#: attributed one does, and the narrow-field reading below is built from the
#: windows this set leaves, so the two readings cannot diverge over it.
TL_HIT = [r for r in LROWS if not adopted_attributed(r) and telluric(r)]
UNATTR = [r for r in LROWS if not adopted_attributed(r) and not telluric(r)]
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
#: Under `--field narrow` the observed side is read over the same narrower
#: field as the expectation: the per-window catalogue's own Class A crossing
#: flags, less the ones the attribution accounts for.  Both sides move
#: together, which is the only way the two readings can be compared.
if FIELD == 'narrow':
    _attrwin = {window_of(r['eb'], r['freq']) for r in LED_ATTR + TL_HIT}
    OBS_IN = [{'eb': CAT[i]['eb'], 'freq': float(CAT[i]['f_cross_GHz']),
               'display': CAT[i]['star_name'].replace(' ', '~'), 'cat': i}
              for i in IA if CAT[i]['crossing'] == 'True'
              and i not in _attrwin]
#: ★ The observed side is the unattributed crossings that lie in a RELEASED
#: Class A window -- the same set the expectation is summed over.  The tail
#: crossings are counted and named, and are not added to it.
N_OBS = len(OBS_IN)
N_TAIL = len(OBS_TAIL)
TAIL_STARS = sorted({r['display'].replace('~', ' ') for r in OBS_TAIL})
TAIL_BLOCKS = sorted({r['eb'] for r in OBS_TAIL})

#: the arithmetic route to the same count, from the macro layer
ROUTE_MACRO = (int(texval('MkUnattr')) - int(texval('EvNCrossFlag'))
               - len(OBS_TAIL) - len(TL_HIT))

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

#: ►► SHOULD-FIX 1 of the round-25 referee pass.  App. D.4 closed on \CeExpSurv
#: = 24.7 where Table A2 and everywhere else compare the same \CeObs against
#: \CeExp = 24.6, and the extra 0.1 was unexplained on the page.  It is honest
#: -- the clean coarse windows contribute a share of the expectation and NO
#: crossing to the count, so the comparison is symmetric -- but both halves of
#: that sentence were computed here, printed to the terminal and to the JSON,
#: and emitted as a macro NEITHER of them.  That is this month's fifth
#: measurement made, asserted and never printed.  Both are macros now, and the
#: assertion below is on the PRINTED values rather than the floats, because the
#: arithmetic a referee checks is the one on the page: 24.6 + 0.1 = 24.7.
CE_COARSE_ADD = E_SURV - E_CEN
if DRIVE == 30:
    #: one clean coarse window is given a crossing, which is the state in which
    #: D.4's clause becomes false: the coarse class would then add to the count
    #: as well as to the expectation and the comparison would stop being
    #: symmetric.  A24 must fail.
    OBS_B_CLEAN += 1
if DRIVE == 31:
    #: the other half: the coarse share rounds to nothing, so the page would
    #: print 24.6 + 0.0 = 24.7 and a reader adding it up would be wrong.
    CE_COARSE_ADD = 0.04

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

#: (d) the attributed share is itself measured on a finite number of control
#: exceedances, so it is redrawn as a binomial on its own measured value --
#: one draw per realisation, shared by every window, because it is one
#: measured quantity and not one per window.
A_DRAW = rng.binomial(N_EXC, A_MEAS, NREAL) / float(N_EXC)
#: (e) and so is the share the atmosphere takes: \CeTlCtrlCut of the
#: \CeTlCtrlSurv exceedances the molecular mask leaves, redrawn the same way
#: and shared by every window, because it too is one measured quantity.
TL_DRAW = (1.0 - rng.binomial(_SURV_M, 1.0 - TL_FAC, NREAL) / float(_SURV_M)
           if _SURV_M else np.ones(NREAL))
BV = np.empty((NB, NREAL))
NW = np.empty(NB)
for j, e in enumerate(EBS):
    ws = BLK[e]
    NW[j] = len(ws)
    acc = np.zeros(NREAL)
    for i in ws:
        n = NCTRL[i]
        att = A_DRAW if i in CJOIN else np.full(NREAL, MASK[i])
        acc += rng.binomial(n, PEXC[i], NREAL) / float(n) * (1.0 - att)
    BV[j] = acc * TL_DRAW

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
HO_FLO, HO_FHI = (float(np.percentile(FACTOR * HO_RATIO, 2.5)),
                  float(np.percentile(FACTOR * HO_RATIO, 97.5)))

# ★★★★ THE TRANSFER IS THE ONE MEASURED IN THE SURVEY, NOT THE ONE MEASURED
# ON EIGHT EVENTS.  Both measure the same thing -- how often a star reaches a
# level compared with a control position in its own field -- but the reserved
# blocks fix it from HO_OBS trigger events and the census fixes it from tens
# of thousands of above-threshold cells at every level from the ladder's foot
# up to the trigger.  The census ratio is the adopted transfer and the
# reserved one is the out-of-sample check; A8 requires the two to agree.
# Carrying the reserved WIDTH instead put a 0.48-1.79 multiplier on the
# expectation, and that -- not the execution blocks -- is where the 11-43
# the paper quoted came from.
TR_LAD = [r for r in json.load(open(os.path.join(HERE, 'cells_v416.json')))
          ['ladder'] if r['ratio'] is not None and r['thr'] <= TRIG]
TR_LO, TR_HI = (min(r['ratio'] for r in TR_LAD),
                max(r['ratio'] for r in TR_LAD))
TR_AT = [r['ratio'] for r in TR_LAD if r['thr'] == TRIG][0]
TR_NLEV = len(TR_LAD)
if DRIVE == 6:
    TR_LO = TR_HI = TR_AT = 1.0         # the transfer is dropped again

BOOT = (BOOT_NULL[rng.integers(0, BOOT_NULL.size, NBOOT)]
        * rng.uniform(TR_LO, TR_HI, NBOOT))
if DRIVE == 14:
    BOOT_NULL = BOOT_NULL * (N_OBS / E_CEN)   # the null alone reaches the count
LO, HI = (float(np.percentile(BOOT, 2.5)), float(np.percentile(BOOT, 97.5)))
LO_NULL, HI_NULL = (float(np.percentile(BOOT_NULL, 2.5)),
                    float(np.percentile(BOOT_NULL, 97.5)))

# =====================================================================
# THE TRANSFER TO STELLAR POSITIONS, APPLIED AND NOT ONLY CARRIED
# =====================================================================
#: The expectation is a sum of CONTROL exceedance rates.  The census measures
#: the same quantity at the star, level by level, and the ratio at the trigger
#: is the measured star-to-control difference in exactly the quantity used
#: here, so applying it is one multiplication and needs no model.  The
#: uncorrected sum is kept beside it so that the step is visible.
#: ★★★★ THE STEP APPLIED IS THE SUB-TRIGGER ONE, NOT THE TRIGGER-LEVEL ONE.
#: `TR_AT` is read at T = TRIG, where the cells that form it are the crossings
#: under test, so applying it calibrated the null on its own test sample.  The
#: step used here is `STEP`, measured in a band wholly below the trigger; it is
#: defined further down because it needs the per-window ladder, so the
#: multiplication is deferred to the same place.  Nothing is applied twice:
#: `TR_APPLIED` is set once, below, and A8 reads it there.
if DRIVE == 8:
    STEP_FACTOR_SCALE = 3.0          # the correction is not the measured one
else:
    STEP_FACTOR_SCALE = 1.0

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

#: ★★ THE RANGE ABOVE IS A RANGE ON THE EXPECTATION, AND A COUNT SCATTERS AS
#: WELL.  Chance delivers a NUMBER of crossings, so the range a reader needs
#: is the range of numbers it could deliver: a rate drawn from the resampled
#: expectation and then a count drawn from that rate.  The expectation range
#: alone understates what could hide in the comparison, and the population it
#: cannot see has to be read off the count range and not off the rate range.
CNT = (rng.poisson(np.clip(BOOT, 0.0, None)) if DRIVE != 13
       else np.round(BOOT))        # the count stops scattering about the rate
CNT_LO, CNT_HI = (float(np.percentile(CNT, 2.5)),
                  float(np.percentile(CNT, 97.5)))

#: WHAT THE COMPARISON CANNOT SEE.  If the true chance rate sat at the bottom
#: of that range, the observed count would be chance plus an added population,
#: and the comparison could not tell the two apart.  The largest such
#: population is the observed count less the floor of the count range.
ADD_BLIND = int(math.floor(N_OBS - CNT_LO))
if DRIVE == 9:
    ADD_BLIND = int(math.floor(N_OBS - LO))   # read off the rate range again

# =====================================================================
# THE COUNT IS COMPARED WITH A DISTRIBUTION OF COUNTS, AND THE STEP IS
# MEASURED WHERE NOTHING UNDER TEST CONTRIBUTES TO IT
# =====================================================================
#: ★★★★ TWO FAULTS WERE IN PRINT TOGETHER AND THEY ARE ONE FAULT.
#:
#: (a) A SINGLE OBSERVED COUNT WAS COMPARED WITH AN INTERVAL ON ITS OWN MEAN.
#:     Everything above this line is the uncertainty in the RATE.  What a
#:     reader needs is the probability that chance delivers a count at least as
#:     large as the one observed, and on the control positions ALONE that
#:     probability is `P_NULL` below.  So the count is what the control
#:     positions predict, and the step is not the term that reconciles them:
#:     the comparison never needed it.  Three intervals -- on the null rate, on
#:     the stepped rate, and on the count -- are replaced by one probability.
#:
#: (b) THE STEP WAS READ AT THE TRIGGER, WHERE THE CELLS THAT FORM IT ARE THE
#:     CROSSINGS UNDER TEST.  The ratio at T = TRIG is built from the handful of
#:     above-trigger out-of-mask stellar cells that the comparison is about, so
#:     the null was being calibrated on its own test sample.  It is therefore
#:     measured in the band STEP_LEV_LO <= T < STEP_LEV_HI, below the trigger,
#:     where no carrier claim is at stake.
#:
#:     WHY A BAND AND NOT A LEVEL.  The ladder counts are CUMULATIVE, so a
#:     count at T = 3 contains every above-trigger cell as well.  A band count
#:     is the difference of two cumulative counts, and lowering a threshold can
#:     only grow a run of channels or merge two, never split one: every cell
#:     belonging to a tabulated crossing is therefore counted in both terms and
#:     CANCELS.  `STEP_UNCANCELLED` measures that rather than assuming it.
#:     Masked channels never enter either term, because `star_out` and
#:     `ctrl_out` are the out-of-mask counts, and the mask they use is the full
#:     searched transition list -- a wider exclusion than the attribution's, so
#:     the cut is conservative in the direction that matters.
#:
#:     The interval is the device the expectation already uses, resampled
#:     execution blocks, and its coverage is stated: COV_PCT per cent.
COV_LOQ, COV_HIQ = 2.5, 97.5
COV_PCT = COV_HIQ - COV_LOQ
ALPHA = (100.0 - COV_PCT) / 100.0

STEP_LEV_LO, STEP_LEV_HI = 3.00, 4.50
if DRIVE == 15:
    STEP_LEV_HI = 6.00         # the cells under test come back into the step
_KLO, _KHI, _KTR = ('%.2f' % STEP_LEV_LO, '%.2f' % STEP_LEV_HI,
                    '%.2f' % TRIG)
A_LAD = [w for w in CELLS
         if w['cls'] == 'A' and w['stratum'] != 'archival_tail']


def _band(w, side):
    """The out-of-mask event count of one window in the sub-trigger band."""
    k = '%s_out' % side
    return w['ladder'][_KLO][k] - w['ladder'][_KHI][k]


def _step(ws):
    """Star events per window divided by control events per control position,
    over a set of windows -- the same ratio the ladder publishes, restricted
    to the band."""
    if not ws:
        return None
    s = sum(_band(w, 'star') for w in ws)
    c = sum(_band(w, 'ctrl') for w in ws)
    nc = sum(w['n_ctrl'] for w in ws)
    return ((s / len(ws)) / (c / nc)) if c else None


STEP = _step(A_LAD)
STEP_NSTAR = sum(_band(w, 'star') for w in A_LAD)
STEP_NCTRL = sum(_band(w, 'ctrl') for w in A_LAD)
#: the cells under test cancel out of a band count, measured and not assumed:
#: every above-trigger event must also be counted above the band's top edge
STEP_UNCANCELLED = sum(max(0, w['ladder'][_KTR]['star_out']
                           - w['ladder'][_KHI]['star_out']) for w in A_LAD)
#: the above-trigger out-of-mask stellar cells the trigger-level ratio -- the
#: one in print -- is formed from; these are the events under test
STEP_NX = sum(w['ladder'][_KTR]['star_out'] for w in A_LAD)
#: the masked channels the band excludes, so the exclusion is not vacuous
STEP_MASKED = (sum(w['ladder'][_KLO]['star'] for w in A_LAD)
               - sum(w['ladder'][_KLO]['star_out'] for w in A_LAD))
#: and the step is not carried by the windows that hold the crossings
STEP_NOX = _step([w for w in A_LAD if w['star_peak'] < TRIG])
STEP_XONLY = _step([w for w in A_LAD if w['star_peak'] >= TRIG])
STEP_NWINX = sum(1 for w in A_LAD if w['star_peak'] >= TRIG)

_sblk = collections.defaultdict(list)
for w in A_LAD:
    _sblk[w['eb']].append(w)
_sebs = sorted(_sblk)
_ss = np.array([sum(_band(w, 'star') for w in _sblk[e]) for e in _sebs], float)
_sc = np.array([sum(_band(w, 'ctrl') for w in _sblk[e]) for e in _sebs], float)
_snw = np.array([len(_sblk[e]) for e in _sebs], float)
_snc = np.array([sum(w['n_ctrl'] for w in _sblk[e]) for e in _sebs], float)
_spk = rng.integers(0, len(_sebs), size=(NBOOT, len(_sebs)))
STEP_BOOT = ((_ss[_spk].sum(axis=1) / _snw[_spk].sum(axis=1))
             / (_sc[_spk].sum(axis=1) / _snc[_spk].sum(axis=1)))
STEP_LO, STEP_HI = (float(np.percentile(STEP_BOOT, COV_LOQ)),
                    float(np.percentile(STEP_BOOT, COV_HIQ)))

# =====================================================================
# AND THE SAME RATIO READ WHERE THE COMPARISON USES IT: IN THE BAND THAT
# ENDS AT THE TRIGGER
# =====================================================================
#: ★★★★ THE RATIO IS NOT FLAT IN LEVEL, SO A BAND FAR BELOW THE TRIGGER DOES
#: NOT MEASURE IT AT THE TRIGGER.  The step above is read over
#: STEP_LEV_LO-STEP_LEV_HI because that is where the cells are; read level by
#: level it RISES, so the quantity the expectation needs is the one read in
#: the band whose top edge IS the trigger.
#: ONE thing keeps the cells under test out of it, and it is measured rather
#: than arranged: a band count is the difference of two cumulative counts, so
#: an above-trigger cell is counted in both terms and cancels exactly --
#: NEAR_UNCANCELLED below is 0 over every census window.  The band was
#: previously ALSO restricted to the windows whose star never reaches the
#: trigger, as a second guard.  That restriction is unnecessary, and it
#: conditions a quantity used to calibrate the null on the observed
#: candidate distribution, so it is gone: the ratio is now read over the same
#: window set the expectation is summed over.
NEAR_BAND_LO, NEAR_BAND_HI = 4.00, TRIG
if DRIVE == 23:
    NEAR_BAND_LO = STEP_LEV_LO      # the bulk comes back into the near band
NEAR_WIN = list(A_LAD)
if DRIVE == 24:
    #: the window selection comes back: the ratio is conditioned on whether
    #: the star reached the trigger, which is the observed distribution
    NEAR_WIN = [w for w in A_LAD if w['star_peak'] < TRIG]
_NLO, _NHI = '%.2f' % NEAR_BAND_LO, '%.2f' % NEAR_BAND_HI


def _nband(w, side):
    k = '%s_out' % side
    return w['ladder'][_NLO][k] - w['ladder'][_NHI][k]


NEAR_NSTAR = sum(_nband(w, 'star') for w in NEAR_WIN)
NEAR_NCTRL = sum(_nband(w, 'ctrl') for w in NEAR_WIN)
NEAR_NTRIG = sum(1 for w in NEAR_WIN if w['star_peak'] >= TRIG)
#: ★ The measurement the comment above now rests on: an above-trigger cell is
#: counted in both cumulative terms of a band count and cancels exactly, so
#: no cell under test enters the band.  This is what replaces the window
#: selection, and unlike the selection it can fail.
NEAR_UNCANCELLED = sum(max(0, w['ladder'][_KTR]['star_out']
                           - w['ladder'][_NHI]['star_out']) for w in NEAR_WIN)
_nnc = sum(w['n_ctrl'] for w in NEAR_WIN)
NEAR = (NEAR_NSTAR / len(NEAR_WIN)) / (NEAR_NCTRL / _nnc)
if DRIVE == 25:
    NEAR = 0.80                     # the transfer turns downward
_nblk = collections.defaultdict(list)
for w in NEAR_WIN:
    _nblk[w['eb']].append(w)
_nebs = sorted(_nblk)
_ns = np.array([sum(_nband(w, 'star') for w in _nblk[e]) for e in _nebs], float)
_nc = np.array([sum(_nband(w, 'ctrl') for w in _nblk[e]) for e in _nebs], float)
_nw = np.array([len(_nblk[e]) for e in _nebs], float)
_nn = np.array([sum(w['n_ctrl'] for w in _nblk[e]) for e in _nebs], float)
_npk = rng.integers(0, len(_nebs), size=(NBOOT, len(_nebs)))
NEAR_BOOT = ((_ns[_npk].sum(axis=1) / _nw[_npk].sum(axis=1))
             / (_nc[_npk].sum(axis=1) / _nn[_npk].sum(axis=1)))
NEAR_LO95, NEAR_HI95 = (float(np.percentile(NEAR_BOOT, COV_LOQ)),
                        float(np.percentile(NEAR_BOOT, COV_HIQ)))
#: the rise itself, half-level by half-level over the same windows, so that
#: "it rises towards the trigger" is a measurement and not an impression
NEAR_RISE = []
for _a, _b in (('3.00', '3.50'), ('3.50', '4.00'),
               ('4.00', '4.50'), ('4.50', '5.00')):
    _s = sum(w['ladder'][_a]['star_out'] - w['ladder'][_b]['star_out']
             for w in NEAR_WIN)
    _c = sum(w['ladder'][_a]['ctrl_out'] - w['ladder'][_b]['ctrl_out']
             for w in NEAR_WIN)
    NEAR_RISE.append((_s / len(NEAR_WIN)) / (_c / _nnc))
NEAR_MONO = all(b > a for a, b in zip(NEAR_RISE, NEAR_RISE[1:]))

#: THE PREDICTIVE PROBABILITY.  A rate is drawn from the resampling above --
#: which already carries the finite control ensembles, the measured attributed
#: share and the dependence between windows of one execution block -- and the
#: count is Poisson about it.  Averaging the Poisson upper tail over those
#: draws is that mixture evaluated exactly, with no second Monte Carlo layer.


def p_at_least(k, lam):
    """P(N >= k) for a Poisson count of mean lam, vectorised over lam."""
    return gammainc(k, np.asarray(lam, float))


def p_at_most(k, lam):
    return gammaincc(k + 1.0, np.asarray(lam, float))


BOOT_PRED = BOOT_NULL
if DRIVE == 16:
    BOOT_PRED = BOOT_NULL * 0.5     # the control positions stop predicting it
P_NULL_POINT = float(p_at_least(N_OBS, E_CEN))
P_NULL = float(p_at_least(N_OBS, BOOT_PRED).mean())
#: drive 8 scales the correction so that it is not the measured one; the
#: scale must reach the probability as well as the point expectation, or
#: drive 8 drives nothing -- which it did for exactly one iteration here.
STEP_DRAW = (STEP_BOOT[rng.integers(0, STEP_BOOT.size, BOOT_PRED.size)]
             * STEP_FACTOR_SCALE)
P_STEP_POINT = float(p_at_least(N_OBS, E_CEN * STEP))
P_STEP = float(p_at_least(N_OBS, BOOT_PRED * STEP_DRAW).mean())
#: the probability the trigger-level step in print would have given, kept only
#: to show that the verdict does not turn on which step is used
P_STEP_AT = float(p_at_least(N_OBS, BOOT_PRED * TR_AT).mean())

#: WHAT THE COMPARISON CANNOT SEE, READ OFF THE SAME DISTRIBUTION.  Not the
#: floor of a count range: the largest added population that still leaves a
#: count as low as the observed one credible at the stated coverage.  That is
#: a one-sided limit with a coverage, which the floor of an interval is not.
#:
#: ★★★★ THE EXPECTATION THE BOUND IS COMPUTED AGAINST IS NOW NAMED, BECAUSE
#: THE PAPER QUOTED TWO AND SAID WHICH FOR NEITHER.  One expectation is
#: adopted -- `E_CEN`, the sum of the measured CONTROL-position exceedance
#: rates -- and the stepped sum `E_X` is a sensitivity test and nothing else.
#: The bound belongs to the adopted one, so `LIM_BASIS` is the control-only
#: draw and A17 asserts it: a bound computed against one expectation and
#: printed beside another is not wrong by a digit, it is unattributable, and
#: no value gate can see which basis a sentence meant.  The stepped basis is
#: computed here too and REPORTED, not published, so that the reader's
#: question -- does the bound turn on the choice? -- is answered from the
#: record rather than from a second number in the text.


def _lim_against(lam):
    """Largest added population leaving P(N<=N_OBS) >= ALPHA, basis `lam`."""
    def p_low(add):
        return float(p_at_most(N_OBS, lam + add).mean())
    lo, hi = 0.0, 1.0
    while p_low(hi) > ALPHA and hi < 1.0e4:
        hi *= 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if p_low(mid) > ALPHA:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


LIM_BASIS = BOOT_PRED
if DRIVE == 18:
    #: the bound is computed against the stepped expectation while the text
    #: and `\CeExp` carry the control-only one -- the defect R2-6 reports
    LIM_BASIS = BOOT_PRED * STEP_DRAW


def _p_low(add):
    return float(p_at_most(N_OBS, LIM_BASIS + add).mean())


ADD_LIM_X = _lim_against(LIM_BASIS)
ADD_LIM = int(math.floor(ADD_LIM_X))
#: the same limit computed against the sensitivity expectation, for the record
ADD_LIM_STEP_X = _lim_against(BOOT_PRED * STEP_DRAW)
ADD_LIM_STEP = int(math.floor(ADD_LIM_STEP_X))
if DRIVE == 17:
    ADD_LIM = ADD_BLIND            # the count floor comes back as the limit

TR_APPLIED = STEP * STEP_FACTOR_SCALE
E_X = E_CEN * TR_APPLIED

# =====================================================================
# WHAT WOULD HAVE TO BE TRUE FOR THE COUNT TO READ AS AN EXCESS
# =====================================================================
#: ★★★★ THE ONE ASSUMPTION THE SEARCHED DATA CANNOT FIX FROM THE INSIDE IS
#: THAT A STAR TRIGGERS AS OFTEN AS A CONTROL POSITION IN ITS OWN FIELD.  It
#: is not defended here; the REQUIREMENT is stated instead.  R_CRIT is the
#: transfer at which the probability falls to the level, so a reader can put
#: any transfer against it and read the verdict off: the comparison reads as
#: an excess only for a transfer at or below it, which is a DEFICIT at the
#: star, and every transfer measured here is an excess.


def _p_at(r):
    return float(p_at_least(N_OBS, BOOT_PRED * r).mean())


_rlo, _rhi = 0.1, 2.0
for _ in range(80):
    _rmid = 0.5 * (_rlo + _rhi)
    if _p_at(_rmid) < ALPHA:
        _rlo = _rmid
    else:
        _rhi = _rmid
R_CRIT = 0.5 * (_rlo + _rhi)
R_CRIT_P = _p_at(R_CRIT)
E_NEAR = E_CEN * NEAR
if DRIVE == 26:
    E_NEAR = E_CEN / NEAR       # the transfer is applied the wrong way round
P_NEAR = _p_at(NEAR)
ADD_LIM_NEAR = int(math.floor(_lim_against(BOOT_PRED * NEAR)))

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
      'measured on the channels the control maxima land on: %d of %d '
      'exceedances fall inside the mask, %.1f per cent, against %.1f per cent '
      'if a maximum were free to land anywhere on its own grid (median grid '
      'share per window %.1f per cent; %d windows lie wholly inside the mask '
      'and carry %.2f of the trigger expectation; the measurement covers %d '
      'windows carrying %.3f of it, %d unjoined)'
      % (100 * W_MASK, N_EXC_ATTR, N_EXC, 100 * A_MEAS, 100 * W_UNIF_MEAS,
         100 * MASK_MED, N_FULL, P_FULL, len(CJOIN), P_TRIG_MEAS,
         len(CNOJOIN)))
print('    expected  %.2f unattributed Class A crossings at the control '
      'positions, %.2f with the measured step to the star applied, %.0f-%.0f '
      'allowed in all (%.0f-%.0f of that from the control ensembles and the '
      'blocks alone); a uniform landing would have given %.2f'
      % (E_CEN, E_X, LO, HI, LO_NULL, HI_NULL, E_REL_UNIF * SCALE))
print('    count     allowing for the scatter in a count as well, chance '
      'alone would deliver %.0f-%.0f crossings' % (CNT_LO, CNT_HI))
print('    observed  %d unattributed crossings in those windows; %d further '
      'lie in archival-tail blocks and are reported beside the comparison '
      '(%s, %s)' % (N_OBS, N_TAIL,
                    ' / '.join(TAIL_STARS), ' / '.join(TAIL_BLOCKS)))
print('    transfer  ADOPTED, from the census: a star carries %.3f-%.3f times '
      'as many above-threshold cells as a control position, over %d levels up '
      'to the trigger, where it is %.3f; applying that gives %.2f expected '
      'against the %d observed.  CHECK, from the reserved blocks: stars reach '
      'the trigger %.3f times as often as their own controls predict (%d '
      'events against %.2f, %.2f-%.2f allowed), which contains the census '
      'range and lies inside it'
      % (TR_LO, TR_HI, TR_NLEV, TR_AT, E_X, N_OBS,
         HO_RATIO, HO_OBS, HO_EXP, HO_FLO, HO_FHI))
print('    cannot see  an added population of up to %d events -- %.0f per cent '
      'of the observed count -- is absorbed by the %.1f-%.1f range'
      % (ADD_BLIND, 100.0 * ADD_BLIND / N_OBS, LO, HI))
print('    STEP      measured in the band %g <= T < %g, below the trigger: a '
      'star carries %.4f times as many out-of-mask above-threshold cells as a '
      'control position (%d star events over %d windows against %d control '
      'events over %d control positions), %.4f-%.4f at %.0f per cent coverage '
      'from %d resampled execution blocks.  %d above-trigger stellar cells '
      'cancel out of the band and %d remain uncancelled; %d masked events are '
      'excluded.  Over the %d windows that hold no crossing it is %.4f and '
      'over the %d that do it is %.4f.  The TRIGGER-LEVEL ratio in print is '
      '%.4f and is formed from those %d cells, which are the events under test'
      % (STEP_LEV_LO, STEP_LEV_HI, STEP, STEP_NSTAR, len(A_LAD), STEP_NCTRL,
         sum(w['n_ctrl'] for w in A_LAD), STEP_LO, STEP_HI, COV_PCT,
         len(_sebs), STEP_NX - STEP_UNCANCELLED, STEP_UNCANCELLED,
         STEP_MASKED, len(A_LAD) - STEP_NWINX, STEP_NOX, STEP_NWINX,
         STEP_XONLY, TR_AT, STEP_NX))
print('    PROBABILITY  a count of %d or more arises by chance with '
      'probability %.3f at the control positions alone (%.3f at the point '
      'rate %.2f), and %.3f with the step applied (expectation %.2f).  The '
      'trigger-level step in print would have given %.3f'
      % (N_OBS, P_NULL, P_NULL_POINT, E_CEN, P_STEP, E_CEN * STEP, P_STEP_AT))
print('    LIMIT     an added population of up to %.2f events (%d whole '
      'events) still leaves a count as low as %d credible at %.0f per cent; '
      'the withdrawn construction, the observed count less the floor of the '
      'count range, gave %d'
      % (ADD_LIM_X, ADD_LIM, N_OBS, COV_PCT, ADD_BLIND))
print('    BASIS     the published bound is computed against the ADOPTED '
      'expectation, the control-position sum %.2f (basis mean %.2f); against '
      'the sensitivity expectation %.2f it would be %.2f events (%d whole), '
      'so the bound quoted is the %s of the two'
      % (E_CEN, float(LIM_BASIS.mean()), E_CEN * STEP, ADD_LIM_STEP_X,
         ADD_LIM_STEP,
         'larger' if ADD_LIM_X > ADD_LIM_STEP_X else 'smaller'))
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

_cknwin = None
try:
    _cknwin = int(texval('CkNWin'))
except (AssertionError, SystemExit, TypeError, ValueError):
    print('  NOTE: \\CkNWin is not in the macro layer yet (round 510 is '
          'written later in the build), so A11\'s window cross-check is not '
          'made on this pass; %d windows were joined here and cells_v416.py '
          'owns the reconciliation' % len(CJOIN))
ck('A11 THE CHANNEL OF EVERY CONTROL EXCEEDANCE IS RECOVERED AND THE '
   'RECONSTRUCTION IS VALIDATED: rebuilt from the stored window edges and the '
   'export\'s own frequency ordering, the mask reproduces every stored '
   'in-mask flag and every window\'s stored grid share, over a set that '
   'carries almost all of the trigger expectation',
   # ★★ v4.18: `\CkNWin` is round 510's (`cells_v416.py`), which runs AFTER
   # this file, so on a clean tree the macro does not exist and a hard read
   # stopped the regeneration.  The cross-check against it is made when it is
   # there and reported when it is not; `cells_v416.py`'s own C9 asserts the
   # same reconciliation after it has run.  Which path was taken is printed
   # in the detail line.
   not VALBAD and not CNOJOIN and N_EXC > 100
   and (_cknwin is None or len(CJOIN) == _cknwin) and P_TRIG_MEAS > 0.95
   and FRAMEBAD == 0,
   '%d exceedance channels and %d windows checked, %d disagreements, %d '
   'windows unjoined; the measured set carries %.3f of the trigger '
   'expectation; %d windows whose control-side velocities differ from the '
   'ones the crossing side uses; %d with no measured systemic velocity, '
   'taken at rest on both sides; \\CkNWin %s'
   % (N_EXC, len(CJOIN), len(VALBAD), len(CNOJOIN), P_TRIG_MEAS,
      FRAMEBAD, FRAMENOVSYS,
      _cknwin if _cknwin is not None else 'not yet written -- deferred'))

ck('A12 THE ATTRIBUTED SHARE IS MEASURED ON THOSE CHANNELS AND IS LARGER THAN '
   'A UNIFORM LANDING GIVES, so the expectation falls and the observed count '
   'stands further above it -- the direction the bias ran',
   A_MEAS > W_UNIF_MEAS and E_CEN < E_REL_UNIF * SCALE
   and N_EXC_FULL >= N_EXC_ATTR and 0.0 < A_MEAS < 1.0,
   'measured %.4f (%d of %d, %d of them on a transition the attribution does '
   'not act on) against %.4f uniform; expectation %.2f against %.2f, observed '
   '%d' % (A_MEAS, N_EXC_ATTR, N_EXC, N_EXC_FULL - N_EXC_ATTR, W_UNIF_MEAS,
           E_CEN, E_REL_UNIF * SCALE, N_OBS))

#: A13 likewise: a range of counts is wider than a range of rates, which is
#: true and is not the comparison the paper now makes.
ck('A13 [withdrawn construction] the range of counts includes the scatter in a '
   'COUNT, not only the uncertainty in the rate: it is strictly wider than '
   'the rate range at both ends, and the observed count sits inside it',
   CNT_LO < LO and CNT_HI > HI and CNT_LO <= N_OBS <= CNT_HI,
   'counts %.0f-%.0f against a rate range of %.1f-%.1f; observed %d'
   % (CNT_LO, CNT_HI, LO, HI, N_OBS))

ck('A3 ONE MASK ON BOTH SIDES: the transition list that reduces the '
   'expectation attributes exactly the crossings the paper attributes, over '
   'all of them and in both directions',
   not DISAGREE and len(LED_ATTR) > 0 and not NOTED
   and len(REST) == len(mf.TRANS) and len(REST) < len(REST_FULL),
   '%d of %d crossings classified differently by the null\'s mask and by the '
   'reported disposition%s; %d coincidences reported as notes, %d transitions '
   'in the mask against %d in the query'
   % (len(DISAGREE), len(LROWS),
      '' if not DISAGREE else ': ' + ', '.join(
          '%s %.4f' % (r['display'], r['freq']) for r in DISAGREE[:4]),
      len(NOTED), len(REST), len(REST_FULL)))

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
   and N_OBS + N_TAIL + len(TL_HIT) == int(texval('EvNUnattrQp'))
   and len(OBS_FLAG) == int(texval('EvNCrossFlag'))
   and N_OBS + N_TAIL + len(OBS_FLAG) + len(TL_HIT)
   == int(texval('MkUnattr')),
   'set %d against the macro route %d; %d + %d tail + %d atmospheric against '
   'the published %s; %d in the flagged block against the published %s; '
   '%d + %d + %d + %d against the published %s'
   % (N_OBS, ROUTE_MACRO, N_OBS, N_TAIL, len(TL_HIT),
      texval('EvNUnattrQp'), len(OBS_FLAG), texval('EvNCrossFlag'),
      N_OBS, N_TAIL, len(OBS_FLAG), len(TL_HIT), texval('MkUnattr')))

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

#: ★ A6 USED TO REQUIRE `HI / LO > 2.0` -- that is, it required the transfer
#: term to DOMINATE the interval, which is the defect and not the check.  It
#: passed for as long as the transfer was fixed on eight events.  What the
#: interval has to do is carry both terms and let a reader see which is
#: larger, so the decomposition is published and the comparison between the
#: two widths is asserted rather than assumed.
ck('A6 THE INTERVAL CARRIES BOTH TERMS AND NEITHER IS HIDDEN: the resampled '
   'expectation is centred on the point estimate, the measured step to the '
   'star raises it and widens it beyond the control ensembles and the blocks '
   'alone without dominating it, and both widths are published',
   abs(float(np.median(BOOT_NULL)) - E_CEN) < 0.05 * E_CEN
   and LO > LO_NULL and HI > HI_NULL
   and (HI - LO) > (HI_NULL - LO_NULL)
   and (HI - LO) < 2.0 * (HI_NULL - LO_NULL),
   'bootstrap median %.2f against the point estimate %.2f; %.1f-%.1f against '
   '%.1f-%.1f from the blocks alone, a width of %.1f against %.1f'
   % (float(np.median(BOOT_NULL)), E_CEN, LO, HI, LO_NULL, HI_NULL,
      HI - LO, HI_NULL - LO_NULL))

#: ★ A7 USED TO REQUIRE A COUNT A THIRD LARGER TO SIT INSIDE THE INTERVAL,
#: which was a property of a 0.48-1.79 transfer and not a property of the
#: data.  The statement worth asserting is the finding: the observed count is
#: inside the range of counts chance could deliver, and OUTSIDE the range the
#: control ensembles and the block sharing allow on their own, so the step
#: from a control position to the star is what accounts for it.  That is one
#: position for the appendices to share and it is measured here.
#: ★★★★ A7 IS WITHDRAWN AND THIS REPLACES IT.  It read "THE OBSERVED COUNT
#: NEEDS THE MEASURED STEP TO THE STAR", and asserted that the count lies
#: OUTSIDE the range the control ensembles and the blocks allow -- which is a
#: range on a RATE, so that comparison is the statistical error itself, and
#: the assertion wrote it into the build as a requirement.  A gate that
#: enforces a defect passes for as long as the defect lasts.  What is true,
#: and what A15 quantifies, is the opposite: the count is what the control
#: positions predict, with no step at all.
ck('A7b THE COUNT IS NOT OUTSIDE WHAT CHANCE DELIVERS AT THE CONTROL '
   'POSITIONS, read as a count and not as a rate: a rate range is not a '
   'reference distribution for a count, and the two verdicts differ here',
   p_at_least(N_OBS, BOOT_NULL).mean() > ALPHA
   and not (LO_NULL <= N_OBS <= HI_NULL),
   'P(N>=%d) = %.3f against %.2f, while the rate range %.1f-%.1f excludes '
   'the count -- which is the comparison that was wrong'
   % (N_OBS, float(p_at_least(N_OBS, BOOT_NULL).mean()), ALPHA,
      LO_NULL, HI_NULL))

ck('A8 THE ADOPTED TRANSFER IS THE CENSUS ONE AND THE RESERVED BLOCKS AGREE '
   'WITH IT: the ladder is the published one, it is measured at more than one '
   'level, the reserved ratio lies inside it and the reserved interval '
   'contains it, and with the sub-trigger step applied the observed count is '
   'still what chance delivers',
   abs(TR_LO - float(texval('CkRatioLo'))) < 0.005
   and abs(TR_HI - float(texval('CkRatioHi'))) < 0.005
   and TR_NLEV >= 4
   and TR_LO <= HO_RATIO <= TR_HI
   and HO_FLO <= TR_LO and TR_HI <= HO_FHI
   and HO_OBS == int(texval('StHoObs'))
   and abs(TR_APPLIED - STEP) < 1e-9 and P_STEP > ALPHA,
   'ladder %.4f-%.4f over %d levels against the published %s-%s; reserved '
   '%.4f on %d events (%.2f-%.2f); stepped expectation %.2f against %d '
   'observed, P(N>=%d) = %.3f; applied step %.4f against the measured '
   '%.4f'
   % (TR_LO, TR_HI, TR_NLEV, texval('CkRatioLo'), texval('CkRatioHi'),
      HO_RATIO, HO_OBS, HO_FLO, HO_FHI, E_X, N_OBS, N_OBS, P_STEP,
      TR_APPLIED, STEP))

#: A9 validates the WITHDRAWN construction and is kept only so that the two
#: can be printed beside each other; A16 is the published one.
ck('A9 [withdrawn construction, kept for the comparison only] the population '
   'read off the range of counts is the largest such population: '
   'RANGE OF COUNTS CHANCE COULD DELIVER AND IS THE LARGEST SUCH POPULATION: '
   'one more event would carry the implied chance count below the floor of '
   'that range',
   ADD_BLIND >= 1 and N_OBS - ADD_BLIND >= CNT_LO
   and N_OBS - (ADD_BLIND + 1) < CNT_LO,
   '%d added events leave %.2f against a floor of %.2f, and %d would leave '
   '%.2f' % (ADD_BLIND, N_OBS - ADD_BLIND, CNT_LO, ADD_BLIND + 1,
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
m('CeUnifPct', '%.0f' % (100 * W_UNIF_MEAS))
m('CeNExc', '%d' % N_EXC)
m('CeNExcAttr', '%d' % N_EXC_ATTR)
m('CeCntLo', '%.0f' % CNT_LO)
m('CeCntHi', '%.0f' % CNT_HI)
m('CeMaskPctMed', '%.1f' % (100 * MASK_MED))
m('CeNFullMask', '%d' % N_FULL)
m('CeExp', '%.1f' % E_CEN)
m('CeLo', '%.0f' % LO)
m('CeHi', '%.0f' % HI)
m('CeLoNull', '%.0f' % LO_NULL)
m('CeHiNull', '%.0f' % HI_NULL)
m('CeObs', '%d' % N_OBS)
m('CeTlObsCut', '%d' % len(TL_HIT))
m('CeTlObsCutWord', ['no', 'one', 'two', 'three', 'four'][len(TL_HIT)])
m('CeTlCtrlCut', '%d' % N_EXC_TL_ONLY)
m('CeTlCtrlSurv', '%d' % _SURV_M)
m('CeTlPct', '%.0f' % (100.0 * (1.0 - TL_FAC)))
m('CeExpX', '%.1f' % E_X)
m('CeTrAt', '%.2f' % TR_AT)
m('CeAddBlind', '%d' % ADD_BLIND)
m('CeFirstAttr', '%d' % N_SFIRST_ATTR)
m('CeNTailCross', '%d' % N_TAIL)
m('CeNTailCrossWord', ['no', 'one', 'two', 'three', 'four'][N_TAIL])
m('CeTailStar', ' / '.join(s.replace(' ', '~') for s in TAIL_STARS))
m('CeExpSurv', '%.1f' % E_SURV)
m('CeExpCoarseAdd', '%.1f' % CE_COARSE_ADD)
m('CeObsCoarse', '%d' % OBS_B_CLEAN)
m('CeObsCoarseWord', ['no', 'one', 'two', 'three', 'four'][OBS_B_CLEAN]
  if OBS_B_CLEAN < 5 else '%d' % OBS_B_CLEAN)
m('CeNBoot', format(NBOOT, ',').replace(',', '\\,'))
m('CeNVsys', '%d' % NVSYS)
m('CeVsysSensPct', '%.1f' % VSYS_SENS_PCT)
m('CeProbNull', '%.2f' % P_NULL)
m('CeProbStep', '%.2f' % P_STEP)
m('CeStep', '%.3f' % STEP)
m('CeStepLo', '%.3f' % STEP_LO)
m('CeStepHi', '%.3f' % STEP_HI)
m('CeStepPct', '%.1f' % (100.0 * (STEP - 1.0)))
m('CeStepLevLo', '%g' % STEP_LEV_LO)
m('CeStepLevHi', '%g' % STEP_LEV_HI)
m('CeStepNStar', format(STEP_NSTAR, ',').replace(',', '\\,'))
m('CeStepNX', '%d' % STEP_NX)
m('CeStepNWin', '%d' % len(A_LAD))
m('CeCovPct', '%.0f' % COV_PCT)
m('CeNear', '%.3f' % NEAR)
m('CeNearIntLo', '%.3f' % NEAR_LO95)
m('CeNearIntHi', '%.3f' % NEAR_HI95)
m('CeNearBandLo', '%g' % NEAR_BAND_LO)
m('CeNearBandHi', '%g' % NEAR_BAND_HI)
m('CeNearNStar', format(NEAR_NSTAR, ',').replace(',', '\\,'))
m('CeNearNWin', '%d' % len(NEAR_WIN))
m('CeNearRiseLo', '%.2f' % NEAR_RISE[0])
m('CeNearRiseHi', '%.2f' % NEAR_RISE[-1])
m('CeExpNear', '%.1f' % E_NEAR)
m('CeProbNear', '%.2f' % P_NEAR)
m('CeAddLimNear', '%d' % ADD_LIM_NEAR)
m('CeRCrit', '%.2f' % R_CRIT)
m('CeRCritExp', '%.1f' % (R_CRIT * E_CEN))
m('CeRCritPct', '%.0f' % (100.0 * (1.0 - R_CRIT)))
m('CeAddLim', '%d' % ADD_LIM)
#: ★★★★ WHAT THE BOUND IS, PUBLISHED SO A READER SEES THE CONSTRUCTION AND NOT
#: ONLY ITS VALUE.  R1-3: \CeAddLim events can be read as a conventional 95
#: per cent upper limit on a signal population, and it is not one.  It is the
#: inversion of a one-sided test -- the largest population that can be added
#: to the ADOPTED expectation before a count as low as the observed one stops
#: being credible at the stated coverage -- evaluated on the same Poisson
#: mixture over the resampled control-position rates, so the uncertainty in
#: \CeExp is carried inside it.  The three numbers that say so are the level
#: the probability crosses and the probability either side of the crossing,
#: which is also the numerical reproduction the report asks for, and they are
#: the quantities A16 already asserts rather than three new ones.
m('CeAlphaPct', '%.0f' % (100.0 * ALPHA))
m('CeProbAtLim', '%.3f' % _p_low(ADD_LIM))
m('CeProbAboveLim', '%.3f' % _p_low(ADD_LIM + 1))

ck('A14 THE STEP IS MEASURED WHERE NOTHING UNDER TEST CONTRIBUTES TO IT: the '
   'band lies wholly below the trigger, every above-trigger stellar cell '
   'cancels between the two cumulative counts that form it, the masked '
   'channels are excluded and the exclusion is not vacuous, and the band is '
   'fixed on orders of magnitude more cells than the trigger level is',
   STEP_LEV_HI <= TRIG and STEP_LEV_LO < STEP_LEV_HI
   and STEP_UNCANCELLED == 0 and STEP_NX > 0
   and STEP_MASKED > 0 and STEP_NSTAR > 100 * STEP_NX
   and STEP is not None and STEP_NOX is not None and STEP_XONLY is not None
   and len(_sebs) > 1 and STEP_LO < STEP < STEP_HI,
   'band %g-%g, step %.4f (%.4f-%.4f at %.0f per cent over %d blocks); %d '
   'star events against %d at the trigger, %d uncancelled, %d masked '
   'excluded; %.4f without the crossing-bearing windows'
   % (STEP_LEV_LO, STEP_LEV_HI, STEP, STEP_LO, STEP_HI, COV_PCT, len(_sebs),
      STEP_NSTAR, STEP_NX, STEP_UNCANCELLED, STEP_MASKED, STEP_NOX))

#: ★★★ v4.26 (B9).  THE CLAUSE THAT KEPT THE CELLS UNDER TEST OUT OF THE BAND
#: USED TO BE THE WINDOW SELECTION (`NEAR_NTRIG == 0`), WHICH WAS TRUE BY
#: CONSTRUCTION AND THEREFORE CHECKED NOTHING -- and worse, the selection it
#: asserted conditioned a quantity used to calibrate the null on whether the
#: star had triggered, which is the outcome-conditioning this paper objects to
#: elsewhere.  It is replaced by the MEASUREMENT that makes the selection
#: unnecessary: no above-trigger cell survives the band difference.  The
#: invariant pinned is "no cell under test enters the band", which holds for
#: any band whose top edge is the trigger -- NOT "the band is 4 to 5".
ck('A20 THE TRANSFER IS ALSO READ IN A BAND THAT ENDS AT THE TRIGGER AND NO '
   'cell under test enters it: the band lies above the step band, its top '
   'edge is the trigger itself so an above-threshold cell belonging to a '
   'crossing is counted in both cumulative terms and cancels, and the ratio '
   'rises towards the trigger rather than being flat, which is why a band '
   'far below it does not measure it',
   NEAR_BAND_HI == TRIG and NEAR_BAND_LO > STEP_LEV_LO
   and NEAR_BAND_HI > STEP_LEV_HI
   and NEAR_UNCANCELLED == 0 and NEAR_NSTAR > 0 and NEAR_NCTRL > 0
   and len(_nebs) > 1 and NEAR_MONO
   and (DRIVE == 25 or NEAR_LO95 < NEAR < NEAR_HI95),
   'band %g-%g on %d windows (%d of them holding a stellar trigger), %d '
   'above-trigger cells fail to cancel out of the band, %d star events, '
   'ratio %.4f (%.4f-%.4f at %.0f per cent over %d blocks); level by level '
   '%s' % (NEAR_BAND_LO, NEAR_BAND_HI, len(NEAR_WIN), NEAR_NTRIG,
           NEAR_UNCANCELLED, NEAR_NSTAR, NEAR,
           NEAR_LO95, NEAR_HI95, COV_PCT, len(_nebs),
           ' '.join('%.4f' % r for r in NEAR_RISE)))

ck('A21 THE REQUIREMENT IS STATED RATHER THAN THE ASSUMPTION DEFENDED, AND '
   'every transfer measured at or below the trigger meets it: the critical '
   'transfer is the one at which the probability reaches the level, and it '
   'is a DEFICIT at the star while every measurement is an excess',
   abs(R_CRIT_P - ALPHA) < 1.0e-3 and R_CRIT < 1.0
   and R_CRIT < min(STEP, NEAR, HO_RATIO, TR_AT) and NEAR_LO95 > R_CRIT,
   'critical %.4f (expectation %.2f, P = %.4f) against the step %.4f, the '
   'near-trigger band %.4f (floor %.4f), the reserved blocks %.4f and the '
   'trigger-level ladder %.4f'
   % (R_CRIT, R_CRIT * E_CEN, R_CRIT_P, STEP, NEAR, NEAR_LO95, HO_RATIO,
      TR_AT))

ck('A22 THE ADOPTED EXPECTATION IS THE ONE MOST DEMANDING OF OUR OWN NULL: '
   'applying the near-trigger transfer RAISES the expectation and the '
   'probability and LOWERS the bound, so the control-only basis is the '
   'smaller expectation and the larger bound, and nothing is applied twice',
   (P_NEAR > P_NULL) == (NEAR > 1.0)
   and (E_NEAR > E_CEN) == (NEAR > 1.0)
   and (ADD_LIM_NEAR <= ADD_LIM) == (NEAR > 1.0)
   and STEP > 1.0 and NEAR > 1.0,
   'near-trigger expectation %.2f against the adopted %.2f, P %.3f against '
   '%.3f, bound %d against %d'
   % (E_NEAR, E_CEN, P_NEAR, P_NULL, ADD_LIM_NEAR, ADD_LIM))

ck('A23 THE ATMOSPHERE IS SCREENED ON BOTH SIDES OR ON NEITHER: one radius, '
   'fixed from the frozen system-temperature specification and not from any '
   'observed offset, applied in the topocentric frame to the crossings and '
   'to the control exceedances alike, so a screen can never lower the count '
   'against an unchanged expectation',
   abs(TL_RAD - N_TSYS_CHAN * TSYS_RES_MHZ) < 1e-9
   and (len(TL_HIT) > 0) == (TL_FAC < 1.0)
   and TL_FAC <= 1.0 and _SURV_M > 0
   and all(abs(tl_offset(r['freq'])[1]) <= TL_RAD
           and not adopted_attributed(r) for r in TL_HIT)
   and not any(abs(tl_offset(r['freq'])[1]) <= TL_RAD for r in UNATTR),
   'radius %.1f MHz = %d x %.2f; %d crossing(s) screened (%s); %d of %d '
   'surviving control exceedances screened, factor %.4f'
   % (TL_RAD, N_TSYS_CHAN, TSYS_RES_MHZ, len(TL_HIT),
      ', '.join('%s %.6f GHz, %+.2f MHz from %s'
                % (r['display'], r['freq'], tl_offset(r['freq'])[1],
                   TL_SPECIES[tl_offset(r['freq'])[0]]) for r in TL_HIT)
      or 'none', N_EXC_TL_ONLY, _SURV_M, TL_FAC))

ck('A15 THE COUNT IS CONSISTENT WITH THE CONTROL POSITIONS WITHOUT ANY STEP, '
   'and it is compared with a distribution of counts and not with an interval '
   'on its own mean: the rate uncertainty enters the probability, and the '
   'step moves it in the direction the step itself runs',
   0.0 < P_NULL < 1.0 and P_NULL > ALPHA
   and BOOT_PRED.std() > 0.0 and P_NULL != P_NULL_POINT
   and ((P_STEP > P_NULL) == (STEP > 1.0)),
   'P(N>=%d) = %.3f at the control positions alone against the %.2f '
   'threshold, %.3f at the point rate, %.3f with the step'
   % (N_OBS, P_NULL, ALPHA, P_NULL_POINT, P_STEP))

#: ★★ AND THE THREE PUBLISHED NUMBERS ARE THE THREE THIS CHECK TESTS.  The
#: invariant is the crossing, not today's 17: the probability printed at the
#: limit must be at or above the printed level and the one printed above it
#: below, in the printed precision, so a reader can redo the inversion from
#: the page.  Pinning the values themselves would fail the build for the
#: paper being right, which is what five gates were caught doing last round.
ck('A16 THE POPULATION THE COMPARISON CANNOT SEE IS A ONE-SIDED LIMIT WITH A '
   'COVERAGE, not the floor of an interval: at the limit a count as low as '
   'the observed one is credible at the stated coverage, one event more is '
   'not, and the two probabilities and the level are PUBLISHED so the '
   'inversion can be checked on the page',
   _p_low(ADD_LIM) >= ALPHA > _p_low(ADD_LIM + 1) and ADD_LIM >= 1
   and float(mval('CeProbAtLim')) >= float(mval('CeAlphaPct')) / 100.0
   > float(mval('CeProbAboveLim')),
   'limit %d events: P(N<=%d) = %.4f at it and %.4f one event above, against '
   '%.2f; published %s / %s either side of %s per cent'
   % (ADD_LIM, N_OBS, _p_low(ADD_LIM), _p_low(ADD_LIM + 1), ALPHA,
      mval('CeProbAtLim'), mval('CeProbAboveLim'), mval('CeAlphaPct')))

#: ★★★★ ONE ADOPTED EXPECTATION, AND THE BOUND BELONGS TO IT.  The paper
#: quoted two expectations for one comparison -- the control-position sum and
#: the same sum stepped by the sub-trigger on-star ratio -- and said which the
#: bound used for neither.  The adopted one is the control-position sum: the
#: step is measured partly on the cells under test, and the comparison is
#: satisfied without it.  A17 pins the BASIS of the bound, which no gate on
#: its value could see, because 17 events is the answer either way to within
#: one event and a right number on a wrong basis is unattributable.
#: ★★★★ v4.21: THE ONE CONJUNCT THAT READS THE MACRO LAYER IS DECLARED WHEN
#: THE MACRO LAYER DOES NOT HOLD IT YET.  `\CeExp` is published by THIS
#: generator, round 310, so on a clean tree `texval` raises and `make_all.sh`
#: stops here -- which is what `cleanregen` found.  Declared rather than
#: dropped, and printed either way, as `beam_r17.py`'s B5b is.
_PUB_CE = None
try:
    _PUB_CE = float(texval('CeExp'))
except AssertionError:
    print('  A17 the published-value conjunct is NOT ASSERTED: round 310 does '
          'not exist on a clean tree and this generator writes it; the other '
          'five conjuncts carry the clause')
ck('A17 THE BOUND IS COMPUTED AGAINST THE ADOPTED EXPECTATION, AND THE '
   'ADOPTED EXPECTATION IS THE CONTROL-POSITION ONE: the basis the limit is '
   'read off is the control-only draw whose mean is the published \\CeExp, '
   'not the stepped sum \\CeExpX, and the stepped sum is reported only as a '
   'sensitivity test',
   abs(float(LIM_BASIS.mean()) - E_CEN) < 0.02 * E_CEN
   and abs(float((BOOT_PRED * STEP_DRAW).mean()) - E_X) < 0.02 * E_X
   and abs(ADD_LIM_X - _lim_against(BOOT_PRED)) < 1e-6
   and ADD_LIM_STEP_X < ADD_LIM_X
   and (_PUB_CE is None or abs(_PUB_CE - E_CEN) < 0.05)
   and STEP > 1.0,
   'basis mean %.2f against the adopted \\CeExp %.2f (published %s) and the '
   'stepped %.2f; bound %.2f on the adopted basis against %.2f on the '
   'stepped one'
   % (float(LIM_BASIS.mean()), E_CEN,
      'absent on a clean tree' if _PUB_CE is None else '%.1f' % _PUB_CE,
      float((BOOT_PRED * STEP_DRAW).mean()), ADD_LIM_X, ADD_LIM_STEP_X))

#: ★★★ AND A VALUE GATE AND A PROSE GATE ARE DIFFERENT GATES.  Everything
#: above fixes which number is which; nothing above can see a sentence that
#: applies the step to the adopted expectation, or a bound quoted without the
#: expectation it is computed against.  Those were the two defects reported,
#: and they live in the prose, so they are gated in the prose.  Three
#: conditions, each one a sentence the manuscript must contain or must not:
#:   (a) every use of \CeExpX or \CeProbStep sits in a sentence that names it
#:       a sensitivity test -- so the stepped sum can never again be read as
#:       the adopted expectation;
#:   (b) at least TWO uses of \CeAddLim name the basis, "control position(s)"
#:       -- two, not one, so that the condition cannot be satisfied by the
#:       abstract alone, which is rewritten more often than any other passage;
#:   (c) the withdrawn phrase "part of the null by assumption" is gone, and
#:       no sentence says the step IS applied to the adopted sum;
#:   (d) ★★★★ R1-3: THE BOUND IS NEVER WORDED AS A CONFIDENCE LIMIT ON A
#:       POPULATION.  \CeAddLim is the inversion of a one-sided test against
#:       the control positions' own expectation -- what this comparison could
#:       not have rejected -- and the three constructions a reader could take
#:       it for (a confidence interval on a transmitter population, a
#:       population upper limit, a detection) are not interchangeable with it.
#:       The INVARIANT is the vocabulary and not the value: no sentence
#:       quoting the bound may carry "confidence" or "upper limit", and at
#:       least one must name it a bound on what the comparison could not
#:       reject.  Driven at 21 and 22.
#: ★ WHITESPACE IS COLLAPSED BEFORE ANYTHING ELSE TOUCHES THE TEXT, and the
#: reason is a defect this gate had for one iteration: the drives perturbed
#: the raw text while the conditions read the line-joined text, so a phrase
#: broken across two source lines -- "control\npositions" in the abstract --
#: satisfied the condition and escaped the drive that was supposed to break
#: it.  One string, read once, by the conditions and by the drives alike.
_PROSE = re.sub(r'\s+', ' ', mscript.flat())
if DRIVE == 19:
    _PROSE = _PROSE.replace('sensitivity', 'accuracy')   # the label goes
if DRIVE == 20:
    _PROSE = _PROSE.replace('control position', 'field')  # the basis goes
if DRIVE == 21:
    #: the bound dressed as the thing R1-3 says it must not be read as
    _PROSE = _PROSE.replace(
        'before a count as low as',
        'at 95 per cent confidence before a count as low as')
if DRIVE == 22:
    _PROSE = _PROSE.replace('could not have rejected', 'can exclude')
_SENT = re.split(r'(?<=[.;:])\s', _PROSE)
_STEPPED = [s for s in _SENT
            if '\\CeExpX' in s or '\\CeProbStep' in s
            or '\\CeExpNear' in s or '\\CeProbNear' in s]
_STEPPED_OK = [s for s in _STEPPED if 'sensitivit' in s.lower()]
_BOUND = [s for s in _SENT if '\\CeAddLim' in s]
_BOUND_OK = [s for s in _BOUND if 'control position' in s.lower()]
#: (d) the vocabulary, pinned as an invariant: no sentence that quotes the
#: bound may call it a confidence limit or an upper limit, and the appendix
#: must say in words what the inversion is.
#: ★★★ A SUBSTRING IS NOT A CLAIM.  This clause exists to stop the bound
#: being PRESENTED as a confidence or upper limit on a population, and the
#: first text written to satisfy R1-3 says, in as many words, that it is
#: "a bound on compatibility and not a confidence limit on a population of
#: transmitters" -- which the naive substring flagged as the very defect it
#: was written to deny.  A gate that fails on the sentence that fixes the
#: problem is a gate that will be switched off, so the DENIAL is recognised
#: and only the assertion fails.
_DENY = re.compile(r'(?:not|never|rather than|and not)\s+(?:a |an )?'
                   r'(?:population\s+)?(?:confidence|upper limit)',
                   re.I)
_BOUND_BAD = []
for s in _BOUND:
    _hits = [m for m in re.finditer(r'confidence|upper limit', s, re.I)]
    if not _hits:
        continue
    # every occurrence must be inside a denial for the sentence to be clean
    _denied = {m.start() for m in _DENY.finditer(s)}
    if all(any(0 <= h.start() - d <= 40 for d in _denied) for h in _hits):
        continue
    _BOUND_BAD.append(s)
_BOUND_NAMED = [s for s in _BOUND if 'could not have rejected' in s.lower()]
_BANNED = [p for p in ('part of the null by assumption',
                       'The step applied to the sum above')
           if p in _PROSE]
ck('A18 THE PROSE AGREES WITH THE ADOPTED CHOICE: every sentence that quotes '
   'the stepped sum or its probability calls it a sensitivity test, at least '
   'two sentences quoting the bound name the control positions it is '
   'computed against, no sentence quoting it calls it a confidence or upper '
   'limit and at least one says what it is, and the withdrawn wording that '
   'applied the step to the adopted expectation appears nowhere',
   len(_STEPPED) > 0 and _STEPPED_OK == _STEPPED
   and len(_BOUND) > 0 and len(_BOUND_OK) >= 2
   and not _BOUND_BAD and len(_BOUND_NAMED) >= 1
   and not _BANNED,
   '%d sentences quote the stepped sum, %d of them labelled a sensitivity '
   'test; %d quote the bound, %d naming the control positions, %d wording it '
   'as a confidence or upper limit, %d saying what it is; %d withdrawn '
   'phrases present %s'
   % (len(_STEPPED), len(_STEPPED_OK), len(_BOUND), len(_BOUND_OK),
      len(_BOUND_BAD), len(_BOUND_NAMED), len(_BANNED), _BANNED))

# =====================================================================
# THE PER-WINDOW DEPOSIT (referee 1, major issue 7)
# =====================================================================
#: The expectation this generator publishes is a sum over the released Class A
#: windows of two factors, and a reader who holds the per-window catalogue
#: holds NEITHER of them: the control exceedance rate measured at the window's
#: own control positions, and the share of it the attribution mask takes.  So
#: the one principal result of the paper that a reader could not rebuild from
#: the released products was this one.  The two factors are deposited here,
#: per window, keyed exactly as `si_r18.py` keys the catalogue rows it writes,
#: and the identity that makes them sufficient is asserted: summed over the
#: file they ARE the published expectation, at the trigger and after the mask.
#: ★ The rate is deposited as a COUNT and an ENSEMBLE SIZE rather than as a
#: ratio, because the interval needs the denominator -- a reader redrawing the
#: binomial cannot do it from a rounded fraction.
#: ★★★★ THE SUFFIX IS `SUFFIX`, NOT THE DRIVE ALONE.  This path carried only
#: the drive, so a `--field` run -- which exists precisely to read the other
#: field and must touch nothing production reads -- OVERWROTE the deposited
#: per-window factors with the narrower field's control ensembles.  Nothing
#: in this generator could see it: the run that did the damage was a
#: sub-process of another generator, and the damage showed up two hundred
#: lines later in `si_r18.py`, whose S13 sums these factors and got 35.51
#: against the published 36.24 at the trigger.  A test must never write a
#: path production reads, and `--field` is a test.
PERWIN_OUT = os.path.join(HERE, 'chance_perwin_v422%s.json' % SUFFIX)
PERWIN = []
for i in IA:
    r = CAT[i]
    v = ctrl_vector(i)
    PERWIN.append(dict(
        eb=r['eb'],
        rms_mJy=round(float(r['rms_mJy']), 5),
        star_snr=round(float(r['star_snr']), 4),
        n_ctrl=(None if v is None else int(v.size)),
        n_ctrl_trig=(None if v is None else int((v >= TRIG).sum())),
        mask_attr_share=(None if i not in PEXC else
                         float(A_MEAS if i in CJOIN else MASK[i])),
        telluric_factor=TL_FAC))
_E_TRIG_SUM = sum(w['n_ctrl_trig'] / float(w['n_ctrl'])
                  for w in PERWIN if w['n_ctrl_trig'] is not None)
_E_SUM = sum(w['n_ctrl_trig'] / float(w['n_ctrl'])
             * (1.0 - w['mask_attr_share']) * w['telluric_factor']
             for w in PERWIN if w['n_ctrl_trig'] is not None)
#: ★★ WHAT THIS CLAUSE IS ABOUT, STATED EXACTLY.  It sums the per-window
#: factors THIS generator emits, which go to `chance_perwin_v422.json` -- a
#: record the paper does not distribute.  So it proves the factors are
#: sufficient and does NOT prove anything about the file a reader holds; the
#: claim about the SHIPPED catalogue is `si_r18.py`'s S13, which reads
#: `si_catalogue.txt` off disk and sums its columns as a reader would.  The
#: label used to say "a reader holding the catalogue can rebuild both", which
#: was a statement about a different object -- the defect family this round
#: exists to clear out.
ck('A19 THE PER-WINDOW FACTORS THIS GENERATOR DEPOSITS ARE SUFFICIENT: summed'
   ' over them they reproduce the published expectation at the trigger and'
   ' after the mask (the same sum over the SHIPPED catalogue is S13)',
   abs(_E_TRIG_SUM - E_TRIG_REL) < 1e-9 and abs(_E_SUM - E_REL) < 1e-9
   and len(PERWIN) == N_A_REL
   and sum(1 for w in PERWIN if w['n_ctrl_trig'] is None)
   == len([i for i in IA if i not in PEXC]),
   'deposited sum %.4f at the trigger against %.4f, and %.4f after the mask '
   'against %.4f, over %d rows of which %d carry no control ensemble'
   % (_E_TRIG_SUM, E_TRIG_REL, _E_SUM, E_REL, len(PERWIN),
      sum(1 for w in PERWIN if w['n_ctrl_trig'] is None)))
#: ►► A24 exists because of SHOULD-FIX 1: App. D.4 may close on \CeExpSurv only
#: if the reader can see WHY it differs from the \CeExp every other comparison
#: uses, and the reason has two halves that must both hold -- the clean coarse
#: windows add a share of the EXPECTATION, and they add NOTHING to the COUNT.
#: If ever they held a crossing, the sentence would be false and the comparison
#: asymmetric, so the clause may not be a typed constant.  ★ The test is on the
#: PRINTED strings, not the floats: 24.6 + 0.1 must equal 24.7 as typeset, since
#: a reader who adds the page's own numbers and gets 24.7 is the only reader
#: this clause is for, and three rounded values can close individually and fail
#: to close together.
_PRN = (float('%.1f' % E_CEN), float('%.1f' % CE_COARSE_ADD),
        float('%.1f' % E_SURV))
ck('A24 THE EXTRA 0.1 IN APPENDIX D.4 IS EXPLAINED ON THE PAGE AND THE PAGE\'S '
   'OWN ARITHMETIC CLOSES: the clean coarse windows add a share of the '
   'expectation and no crossing to the count, and the three printed values '
   'sum as printed',
   abs(_PRN[0] + _PRN[1] - _PRN[2]) < 1e-9 and OBS_B_CLEAN == 0
   and CE_COARSE_ADD > 0,
   'printed %.1f + %.1f = %.1f (unrounded %.4f + %.4f = %.4f), and the clean '
   'coarse windows hold %d crossing(s)'
   % (_PRN[0], _PRN[1], _PRN[0] + _PRN[1], E_CEN, CE_COARSE_ADD, E_SURV,
      OBS_B_CLEAN))

json.dump(dict(round=ROUND, drive=DRIVE, trigger=TRIG,
               e_trigger_released=E_TRIG_REL, e_chance_released=E_REL,
               rows=PERWIN), open(PERWIN_OUT, 'w'), indent=1)

# =====================================================================
# write
# =====================================================================
if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    if DRIVE is None and FIELD is None:
        raise SystemExit(1)

hdr = ['%% GENERATED by chance_v414.py (round %d) -- do not hand-edit.' % ROUND,
       '%% One chance expectation for the unattributed Class A crossings,',
       '%% measured window by window over the RELEASED census and over no other',
       '%% set, with one interval from resampled execution blocks, the measured',
       '%% star-to-control transfer applied to it, and the archival-tail',
       '%% crossings named and counted outside the comparison.']
if WRITE_TEX:
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
               telluric=dict(radius_MHz=TL_RAD, n_tsys_channels=N_TSYS_CHAN,
                             tsys_resolution_MHz=TSYS_RES_MHZ,
                             observed_before=N_OBS + len(TL_HIT),
                             observed_after=N_OBS,
                             observed_removed=[
                                 dict(star=r['display'], eb=r['eb'],
                                      f_topo=r['freq'],
                                      d_MHz=tl_offset(r['freq'])[1],
                                      species=TL_SPECIES[
                                          tl_offset(r['freq'])[0]],
                                      line_MHz=tl_offset(r['freq'])[0])
                                 for r in TL_HIT],
                             ctrl_exceedances=N_EXC,
                             ctrl_in_mask=N_EXC_ATTR,
                             ctrl_surviving_mask=_SURV_M,
                             ctrl_removed=N_EXC_TL_ONLY,
                             factor=TL_FAC,
                             e_chance_before=E_CEN / TL_FAC if TL_FAC else None,
                             e_chance_after=E_CEN),
               e_chance_transfer_applied=E_X,
               transfer_adopted=[TR_LO, TR_HI], transfer_adopted_at=TR_AT,
               transfer_adopted_levels=TR_NLEV,
               transfer_ratio=HO_RATIO, transfer_obs=HO_OBS,
               transfer_exp=HO_EXP, transfer_reserved=[HO_FLO, HO_FHI],
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
               coverage_pct=COV_PCT,
               step_band=[STEP_LEV_LO, STEP_LEV_HI],
               step=STEP, step_interval=[STEP_LO, STEP_HI],
               step_n_star_events=STEP_NSTAR,
               step_n_control_events=STEP_NCTRL,
               step_n_trigger_cells=STEP_NX,
               step_n_uncancelled=STEP_UNCANCELLED,
               step_n_masked_excluded=STEP_MASKED,
               step_without_crossing_windows=STEP_NOX,
               step_crossing_windows_only=STEP_XONLY,
               step_n_windows=len(A_LAD),
               step_trigger_level=TR_AT,
               near_band=[NEAR_BAND_LO, NEAR_BAND_HI],
               near_ratio=NEAR, near_interval=[NEAR_LO95, NEAR_HI95],
               near_n_star_events=NEAR_NSTAR, near_n_windows=len(NEAR_WIN),
               near_rise=NEAR_RISE,
               near_expectation=E_NEAR, near_p_at_least=P_NEAR,
               near_added_population_limit=ADD_LIM_NEAR,
               critical_transfer=R_CRIT,
               critical_transfer_expectation=R_CRIT * E_CEN,
               p_at_least_observed_control_only=P_NULL,
               p_at_least_observed_control_only_point=P_NULL_POINT,
               p_at_least_observed_with_step=P_STEP,
               p_at_least_observed_with_trigger_step=P_STEP_AT,
               added_population_limit=ADD_LIM,
               added_population_limit_exact=ADD_LIM_X,
               added_population_limit_basis='control positions alone',
               added_population_limit_basis_mean=float(LIM_BASIS.mean()),
               added_population_limit_sensitivity=ADD_LIM_STEP,
               added_population_limit_sensitivity_exact=ADD_LIM_STEP_X,
               n_boot=NBOOT, n_realisations=NREAL, seed=SEED),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('\nwrote %s%s'
      % ('%s (%d macros) and ' % (os.path.basename(OUT_TEX), len(OUT))
         if WRITE_TEX else '', os.path.basename(OUT_JSON)))
