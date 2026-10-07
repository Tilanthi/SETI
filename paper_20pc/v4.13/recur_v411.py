#!/usr/bin/env python3
r"""recur_v411.py -- the stellar-frame recurrence test on every unattributed
crossing, the two-number separation of searchability from confirmability, and
the single candidate table.

Round 120.  Writes `survey_numbers_round120.tex`, `tab_recurcand_v411.tex`,
`tab_visfit_v411.tex` and `recurcols_v411.json` (NOT tab_recurcols_v411.tex, retired).

WHY THIS EXISTS.  The spatial rank has no calibrated false-alarm probability,
so the paper states that it is not used as evidence for detection; and the
paper then disposed of most unattributed crossings on that rank and concluded
that none of them recurs.  Only ten had ever been tested.  The test is now run
on all of them: `r10inputs/recur_v411.json` is the measurement, made on the
retained dynamic spectra with the survey's own estimator at a single drift --
the discovery drift transported to each repeat epoch's observed frequency -- at
the channel the event's stellar-frame rest frequency lands on in that epoch.
That is the same code path and the same registration that produced the
published eta Crv exclusion, and it reproduces it to the printed digits, which
is this generator's first assertion.

THREE THINGS THE MEASUREMENT HAD TO GET RIGHT, each of which was wrong once:

* **Two extractions of one block live on this host.**  489 of 2729 retained
  windows exist in more than one directory and 372 of those pairs disagree
  about the window's own peak statistic; the per-block `_EB_` copy is the one
  the released catalogue carries.  So the discovery window is *identified* by
  reproducing the T* the paper prints for that crossing, not preferred by sort
  order.  All \RcNTested{} of them do, to better than 1e-7 relative.
* **The join from a crossing to its repeat blocks is on position**, taken from
  each product's own `t1_ra`/`t1_dec`, never on the star name: the catalogue,
  the worklist, the stack inventory and the recurrence worker spell one star
  four ways.
* **One repeat product's published noise is 1.4 microJy where its siblings are
  7-12 mJy.**  It is on the paper's own list of 27 weight-pathology products
  (`badweight.json`, \StkBadWeight), and it is dropped by that list rather than
  by a cut invented here.  Without it the combined noise of HR 1010's repeat
  coverage was wrong by a factor of 2e3.

Usage: recur_v411.py [--drive N]
"""
import csv
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round120.tex')
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE


def out(name):
    """Every product of a driven run is suffixed.  A test must never write a
    path production reads; the suffix follows the FLAG, not the perturbation."""
    b, e = os.path.splitext(name)
    return os.path.join(HERE, b + SFX + e)


TRIG = 5.0
SEP_DAY = 1.0           # the paper's own definition of an independent epoch


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
    """The ledger's display name, shortened for a narrow column.  It must NOT
    convert hyphens to en-dashes: the ledger already ships `CP$-$72 2713` with
    a maths minus, and `-` -> `--` inside that turns it into `CP$--$72`."""
    s = s.split('  Gaia')[0].split(' (Gaia')[0].split(' Gaia')[0]
    if '$' not in s:
        s = s.replace('-', '$-$')
    return s.replace(' ', '~')


def _mant(x):
    e = int(math.floor(math.log10(abs(x))))
    return [x / 10.0 ** e, e]


def linetex(s):
    """The transition name as the paper sets it: an en-dash between the
    quantum numbers, and SO's two subscripts."""
    if s == 'SO(8_8-7_7)':
        return r'SO($8_8$--$7_7$)'
    return s.replace('-', '--')


def num(x, dp=2, signed=False):
    """A number for maths mode.  An ASCII hyphen typesets as a hyphen, not a
    minus, which is why the drift rates in the shipped table read `-2056`."""
    t = ('%+.*f' if signed else '%.*f') % (dp, x)
    return t.replace('-', '-')


def mjd_to_date(mjd):
    """The calendar date of an MJD, to the day (Fliegel & van Flandern).  A
    reader asked to judge a two-hour non-recurrence needs the dates, and a
    date is not a number this project may type."""
    jd = int(math.floor(mjd + 2400001.0))
    L = jd + 68569
    n = (4 * L) // 146097
    L = L - (146097 * n + 3) // 4
    i = (4000 * (L + 1)) // 1461001
    L = L - (1461 * i) // 4 + 31
    j = (80 * L) // 2447
    d = L - (2447 * j) // 80
    L = j // 11
    mo = j + 2 - 12 * L
    y = 100 * (n - 49) + i + L
    return '%d %s %d' % (y, ('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov '
                             'Dec').split()[mo - 1], d)


def sig(x):
    """A signal-to-noise ratio is not a probability.  Print it with the
    precision it has: two digits below ten, none above twenty."""
    return ('%.1f' % x) if x < 20 else ('%.0f' % x)


M = []
fail = []


def m(k, v):
    M.append((k, v))


def ck(name, cond, detail=''):
    if not cond:
        fail.append(name)
    print('  %-56s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


# ---------------------------------------------------------------- inputs
R = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
CROSS = R['crossings']
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
MJD = json.load(open(os.path.join(HERE, 'epochs_v386.json')))['mjd']

UNATTR = [r for r in LED['rows'] if not r['attributed']]
N_UNATTR = len(UNATTR)


def blocks(c):
    """The covering repeat blocks of one crossing, with the paper's own
    weight-pathology list applied.  A product whose published noise is three
    orders of magnitude below its siblings' is a noise-estimation failure, not
    a deeper observation, and the paper already names 27 of them."""
    return [b for b in c.get('blocks', []) if not b.get('bad_weight_product')]


def comb(c, bl):
    """Inverse-variance combination of the repeat coverage at the registered
    cell: what a carrier persisting at the discovery flux would have given
    there, what was measured, and the significance at which the two readings
    of one amplitude disagree.

    ★★★ ONE FORMULA, AND THE DISCOVERY'S OWN NOISE IS IN IT.

        T_pers = S / sigmabar          sigmabar = (sum 1/sigma_i^2)^(-1/2)
        T_rep  = abar / sigmabar       abar     = sum(a_i/sigma_i^2)/sum(...)
        excl   = (S - abar) / sqrt(sigma_d^2 + sigmabar^2)
               = (T_pers - T_rep) / sqrt(1 + (T_pers/T_star)^2)

    so the exclusion follows from three quantities the ledger prints and
    nothing else.  It replaces (S - abar)/sigmabar, which treats the
    discovery amplitude as exact: that reading could and did exceed the
    strength of the discovery it was built from, and it is not what a reader
    comparing two measurements of one carrier wants to know.  What the deep
    repeat coverage really buys is stated as a limit instead, `f5`: the
    fraction of the discovery amplitude that is still excluded at the
    trigger, (T_rep + 5)/T_pers.  Because a discovery amplitude selected as
    the maximum over many cells at T ~ 5 is biased high, the true amplitude
    is on average below the measured one -- and f < 1 is exactly that case,
    so the limit form carries the selection bias rather than ignoring it.
    """
    S = c['discovery']['amp_mJy']
    sd = c['discovery']['sig_mJy']
    w = [1.0 / b['sig_mJy'] ** 2 for b in bl]
    sb = 1.0 / math.sqrt(sum(w))
    ab = sum(b['amp_mJy'] * q for b, q in zip(bl, w)) / sum(w)
    return dict(n=len(bl), sbar=sb, abar=ab, T_pers=S / sb,
                T_rep=ab / sb,
                excl=(S - ab) / math.sqrt(sd * sd + sb * sb),
                excl_conditional=(S - ab) / sb,
                f5=(ab / sb + TRIG) / (S / sb),
                T_max=max(b['T_matched'] for b in bl),
                T_bestdrift_max=max(b['T_bestdrift_pub'] for b in bl),
                n_eff=(c['discovery']['sig_mJy'] / sb) ** 2,
                sep_min_h=min(abs(b['sep_from_discovery_h']) for b in bl),
                sep_max_h=max(abs(b['sep_from_discovery_h']) for b in bl),
                nearest_eb=min(bl, key=lambda b: abs(
                    b['sep_from_discovery_h']))['eb'],
                nearest_block=min(bl, key=lambda b: abs(
                    b['sep_from_discovery_h'])),
                n_day=sum(1 for b in bl
                          if abs(b['sep_from_discovery_h']) > 24.0),
                deepest_eb=min(bl, key=lambda b: b['sig_mJy'])['eb'],
                n_in_catalogue=sum(
                    1 for b in bl if b.get('in_released_catalogue')),
                n_outside_catalogue=sum(
                    1 for b in bl if not b.get('in_released_catalogue')))


ROWS, UNTESTED = {}, []
for cid, c in CROSS.items():
    if c['status'] != 'ok':
        UNTESTED.append(c)
        continue
    bl = blocks(c)
    if not bl:
        UNTESTED.append(c)
        continue
    ROWS[cid] = dict(c=c, s=comb(c, bl))

# ★★★ v4.12.  THE SET TESTED IS THE SET THE LEDGER CALLS UNATTRIBUTED, not
# the set the frozen measurement record called unattributed.  Those were the
# same thing until the line list was rebuilt; they are not now, and the
# paper's sentence is about the first.  Keyed on (block, crossing
# frequency), which is the key the ledger itself uses, never on a star name.
LUNATTR = {(r['eb'], round(float(r['freq']), 4))
           for r in LED['rows'] if not r['attributed']}
# ★★ AND THE SET CARRYING AN EXCLUSION IS SMALLER STILL.  Four crossings come
# from the one execution block that fails the predefined quality criterion.
# Their repeat readings are sound -- they are made on other blocks -- but the
# exclusion inherits the DISCOVERY amplitude, which comes from the block the
# paper calls defective, so the ledger withholds it on those rows.  The text
# used to say "every tested crossing excludes ... by at least" over all of
# them, which was false for exactly those four: they are tested and they
# carry no exclusion.  Both populations are now counted and named apart.
LDQ = {(r['eb'], round(float(r['freq']), 4))
       for r in LED['rows'] if r.get('dq')}


def _lkey(c):
    return (c['eb'], round(float(c['freq_GHz']), 4))


U = [k for k in ROWS if _lkey(ROWS[k]['c']) in LUNATTR]
UNTESTED = [q for q in UNTESTED if _lkey(q) in LUNATTR]
N_TESTED = len(U)
N_UNTESTED = len(UNTESTED)
if DRIVE == 1:                       # a crossing silently left out
    U = U[:-1]
    N_TESTED = len(U)
# ★★★ EVERY UNATTRIBUTED CROSSING IS TESTED AGAINST THE CRITERION.  The
# criterion is the trigger at the predicted stellar-frame cell, and that
# needs the crossing's frequency and a drift grid, not its amplitude; the
# one crossing whose discovery dynamic spectrum was not retained is
# therefore testable, out of the covering windows' own maxima, even though
# no exclusion can be formed for it.  So the tested population is all of
# them, and the population carrying an exclusion is the smaller number --
# two counts, named apart, where the paper used to print one for both.
N_NOSPEC = N_UNTESTED
N_ALLTEST = N_TESTED + N_NOSPEC

QU = [k for k in U if _lkey(ROWS[k]['c']) not in LDQ]
if DRIVE == 13:                      # a withheld row counted as an exclusion
    QU = list(U)
TMAX = max(ROWS[k]['s']['T_max'] for k in U)
TREPMAX = max(ROWS[k]['s']['T_rep'] for k in U)
TBD = max(ROWS[k]['s']['T_bestdrift_max'] for k in U)
EXCL = sorted(ROWS[k]['s']['excl'] for k in QU)
FFIVE = sorted(ROWS[k]['s']['f5'] for k in QU)
NREP_MEAS = sum(ROWS[k]['s']['n'] for k in U)
REP_EB = {b['eb'] for k in U for b in blocks(CROSS[k])}
REP_OUT = {b['eb'] for k in U for b in blocks(CROSS[k])
           if not b.get('in_released_catalogue')}

m('RcNUnattr', '%d' % N_UNATTR)
m('RcNTested', '%d' % N_ALLTEST)
m('RcNExclPoss', '%d' % N_TESTED)
m('RcNNoSpec', '%d' % N_NOSPEC)
m('RcNRepeatMeas', '%d' % NREP_MEAS)
m('RcNRepeatBlock', '%d' % len(REP_EB))
m('RcNRepeatFollow', '%d' % len(REP_OUT))
# ★ TWO readings of the same cell, and the paper must not use one word for
# both.  `RcTMatched` is the statistic at the discovery drift transported to
# the repeat epoch -- an unbiased amplitude, which is what the exclusion is
# built from.  `RcTMax` is the largest value found at that cell over every
# drift trial, which is what Referee 2 asks to see tabulated and is the
# conservative number; it is also what Appendix C already quotes for
# \RcCpStar{} (\CpRecT), so the two parts of the paper now agree.
m('RcTMatched', '%.2f' % TMAX)
m('RcTRepMax', '%+.2f' % TREPMAX)
m('RcTMax', '%.2f' % TBD)
m('RcNExcl', '%d' % len(QU))
m('RcNWithheld', '%d' % (len(U) - len(QU)))
m('RcExclMin', '%.1f' % EXCL[0])
m('RcExclMed', '%.1f' % EXCL[len(EXCL) // 2])
m('RcExclMax', '%.1f' % EXCL[-1])
m('RcNExclFive', '%d' % sum(1 for e in EXCL if e >= TRIG))
m('RcFracMed', '%.2f' % FFIVE[len(FFIVE) // 2])
m('RcFracMin', '%.3f' % FFIVE[0])
m('RcFracMax', '%.2f' % FFIVE[-1])
m('RcNFracHalf', '%d' % sum(1 for f in FFIVE if f <= 0.5))
m('RcNeffMax', '%.0f' % max(ROWS[k]['s']['n_eff'] for k in U))
# ★ The exclusion must be reproducible from the three quantities the ledger
# prints, for every row, or the caption's claim that every disposition can be
# reproduced from the table is false.  Checked here against the amplitudes.
_rep = []
for k in QU:
    c, s = ROWS[k]['c'], ROWS[k]['s']
    _ts = c['discovery']['T_matched'] * (1.01 if DRIVE == 14 else 1.0)
    _rep.append(abs((s['T_pers'] - s['T_rep'])
                    / math.sqrt(1.0 + (s['T_pers'] / _ts) ** 2) - s['excl']))
ck('A13 the exclusion follows from T_star, T_pers and T_rep alone, for '
   'every row that carries one', max(_rep) < 5e-3,
   'largest departure %.2e over %d rows' % (max(_rep), len(QU)))
_xmax = (max(ROWS[k]['s']['excl_conditional'] for k in QU) if DRIVE == 15
         else EXCL[-1])
ck('A14 and no exclusion exceeds the strength of the discovery it is built '
   'from', _xmax <= max(ROWS[k]['c']['discovery']['T_matched']
                        for k in QU) + 0.05,
   'largest %.2f against the largest T_star %.2f'
   % (_xmax, max(ROWS[k]['c']['discovery']['T_matched'] for k in QU)))
# the range of usable baselines, over the blocks the test actually used, in
# the units they fall in: hours at one end and years at the other.
_sh = [ROWS[k]['s']['sep_min_h'] for k in U]
_sx = [ROWS[k]['s']['sep_max_h'] for k in U]
m('RcSepMinH', '%.2f' % min(_sh))
m('RcSepMaxYr', '%.1f' % (max(_sx) / 24.0 / 365.25))
m('RcNSepSameDay', '%d' % sum(1 for h in _sh if h < 24.0))
if UNTESTED:
    q = UNTESTED[0]
    m('RcUntStar', q['display'].replace('~', '\\,'))
    m('RcUntEb', q['eb'].replace('A002_', '').replace('_', '\\_'))
    m('RcUntFreq', '%.4f' % q['freq_GHz'])
    m('RcUntT', '%.2f' % q['tstar'])
    # the repeat coverage is not the problem: it is the DISCOVERY dynamic
    # spectrum that was not retained, so there is no flux to transport.
    _same = [CROSS[b] for b in CROSS if CROSS[b]['status'] == 'ok'
             and CROSS[b]['star'] == q['star']]
    m('RcUntNRep', '%d' % (max((c['n_repeat_blocks_measured']
                                for c in _same), default=0)))

# ---- the two crossings whose star outranks every control position
# ★★ These used to be selected as "the unattributed one that outranks its
# controls" and "the attributed one", which makes the pair depend on the line
# list: move one transition into the mask and the second column silently
# becomes a different crossing, or disappears.  They are now selected by the
# property the section is about -- the star outranks every control position --
# which is a measurement and does not move when the mask is rebuilt.  The
# ordering is by discovery statistic, so `Sx` is the stronger of the two.
_SCRALL = sorted([k for k in ROWS if CROSS[k]['screen']],
                 key=lambda k: -ROWS[k]['c']['discovery']['T_matched'])
SCR = [k for k in U if CROSS[k]['screen']]
for tag, keys in (('Sx', _SCRALL[:1]), ('Cp', _SCRALL[1:2])):
    if not keys:
        continue
    k = keys[0]
    c, s = ROWS[k]['c'], ROWS[k]['s']
    m('Rc%sStar' % tag, c['display'])
    m('Rc%sFreq' % tag, '%.6f' % c['freq_GHz'])
    m('Rc%sT' % tag, '%.3f' % c['discovery']['T_matched'])
    # ★★ R2-M7: "five repeat blocks but one covering block in the
    # catalogue" is two different counts of two different sets, and the
    # table printed them as though they were one.  `NRep` is the number of
    # execution blocks measured at the predicted cell; `NRepCat` is how many
    # of those the released catalogue carries; `NCat` is how many blocks the
    # catalogue lists as covering the frequency at all, which includes
    # blocks whose dynamic spectrum was not retained and which therefore
    # cannot be measured.  All three are now printed, each labelled.
    m('Rc%sNRep' % tag, '%d' % s['n'])
    m('Rc%sNRepCat' % tag, '%d' % s['n_in_catalogue'])
    m('Rc%sNCat' % tag, '%d' % c['n_catalogue_covering_blocks'])
    m('Rc%sNearH' % tag, '%.2f' % s['sep_min_h'])
    # ★ the nearest covering epoch is not always a LATER one: all of the
    # stronger event's covering epochs precede its discovery block, and a
    # sentence saying "the next observation" would be false.
    m('Rc%sNearSign' % tag,
      'earlier' if s['nearest_block']['sep_from_discovery_h'] < 0
      else 'later')
    m('Rc%sDate' % tag,
      mjd_to_date(c['discovery']['t_start_mjdsec'] / 86400.0))
    m('Rc%sNearDate' % tag,
      mjd_to_date(s['nearest_block']['t_start_mjdsec'] / 86400.0))
    m('Rc%sSpanD' % tag, '%.0f' % (s['sep_max_h'] / 24.0))
    m('Rc%sTPers' % tag, '%.2f' % s['T_pers'])
    m('Rc%sTObs' % tag, '%.2f' % s['T_bestdrift_max'])
    m('Rc%sTObsMatched' % tag, '%+.2f' % s['T_max'])
    m('Rc%sExcl' % tag, '%.1f' % s['excl'])
    m('Rc%sFlux' % tag, '%.1f' % c['discovery']['amp_mJy'])
    m('Rc%sFluxErr' % tag, '%.1f' % c['discovery']['sig_mJy'])
    m('Rc%sDrift' % tag, '%.0f' % c['discovery']['drift_Hz_s'])
    m('Rc%sChanwkHz' % tag, '%.2f' % (c['discovery']['chanw_Hz'] / 1e3))
    m('Rc%sCtrl' % tag, '%.2f' % (c['rank_ctrl'] or 0.0))
    m('Rc%sBand' % tag, str(c['band']))
    m('Rc%sDv' % tag, '%.0f' % c['dv_stellar'])
    m('Rc%sLine' % tag, c.get('line_tex') or linetex(c['line']))
# ★ R2-minor 7: the released "2--769 d" came from a generator that knew only
# catalogue blocks, so it could not see a repeat 2.05 HOURS later in a
# follow-up execution block.  These two come from the products' own time
# stamps, over exactly the blocks the test used, and carry both units.
_scrkeys = _SCRALL
if _scrkeys:
    _h = [ROWS[k]['s']['sep_min_h'] for k in _scrkeys]
    _d = [ROWS[k]['s']['sep_max_h'] / 24.0 for k in _scrkeys]
    m('RcScrSepMinH', '%.2f' % min(_h))
    m('RcScrSepMaxD', '%.0f' % max(_d))

# ------------------------------------------- searchability, confirmability
A = [r for r in CAT if r['search_class'] == 'A']
bysys = collections.defaultdict(list)
for r in A:
    bysys[r['system_id']].append(r)


def union(iv):
    iv, o = sorted(iv), []
    for a, b in iv:
        if o and a <= o[-1][1]:
            o[-1][1] = max(o[-1][1], b)
        else:
            o.append([a, b])
    return o


def total(iv):
    return sum(b - a for a, b in iv)


def doubly(rows, sep):
    """The frequency interval of one system covered by two execution blocks
    more than `sep` days apart.  Computed on the interval boundaries, so a
    partial overlap counts only where it overlaps."""
    iv = [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
           max(float(r['flo_GHz']), float(r['fhi_GHz'])), r['eb'])
          for r in rows]
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    keep = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        ts = sorted(MJD[e] for _a, _b, e in iv
                    if _a <= mid <= _b and e in MJD)
        if any(ts[k] - ts[j] > sep
               for j in range(len(ts)) for k in range(j + 1, len(ts))):
            keep.append([pts[i], pts[i + 1]])
    return union(keep), union([(a, b) for a, b, _ in iv])


def revisited(rows, sep):
    """A system two of whose execution blocks are more than `sep` days
    apart, WHETHER OR NOT they cover a common frequency.  This is the weaker
    of the two criteria and is counted only so the paper can say how much
    weaker: a revisit at a different tuning cannot retest a crossing."""
    ts = sorted({MJD[r['eb']] for r in rows if r['eb'] in MJD})
    return any(ts[k] - ts[j] > sep
               for j in range(len(ts)) for k in range(j + 1, len(ts)))


ALLSYS = collections.defaultdict(list)
for r in CAT:
    ALLSYS[r['system_id']].append(r)

# ★★★ R2-M7, FIRST BULLET.  Two statements of "how many systems could be
# retested" disagreed, and the referee attributes it to an unstated
# denominator.  That is half of it.  They differ by TWO things, and the
# second matters more:
#   * the DENOMINATOR -- all \NSysAll{} searched systems, or the \NSysA{}
#     with a Class A window;
#   * the CRITERION -- two execution blocks more than a day apart (which is
#     what a reader counting epochs gets), or two execution blocks more than
#     a day apart THAT COVER A COMMON FREQUENCY (which is what it takes to
#     retest a crossing).  ALMA retunes between visits, so these are not the
#     same set, and the second is the one a confirmation statement may use.
# Every one of the four combinations is published, each named by both its
# denominator and its criterion, and the two the paper quotes are asserted
# to be the smaller pair.
CONF = {}
for sep, tag in ((SEP_DAY, 'Day'), (365.25, 'Yr')):
    nsys, gd, ga = 0, 0.0, 0.0
    for s, rows in bysys.items():
        d, u = doubly(rows, sep)
        ga += total(u)
        gd += total(d)
        if d:
            nsys += 1
    CONF[tag] = (nsys, gd, ga)
    nall = sum(1 for s, rows in ALLSYS.items() if doubly(rows, sep)[0])
    m('RcConfSys' + tag, '%d' % nsys)              # Class A, same frequency
    m('RcConfSysAll' + tag, '%d' % nall)           # all systems, same freq
    m('RcRevSys' + tag,                            # Class A, any revisit
      '%d' % sum(1 for s, rows in bysys.items() if revisited(rows, sep)))
    m('RcRevSysAll' + tag,                         # all systems, any revisit
      '%d' % sum(1 for s, rows in ALLSYS.items() if revisited(rows, sep)))
# ★ the systems that cannot be retested at all, which is what the protocol
# statement R2 asks for has to be about.
_nconfA = sum(1 for s, rows in bysys.items() if doubly(rows, 0.0)[0])
_nconfAll = sum(1 for s, rows in ALLSYS.items() if doubly(rows, 0.0)[0])
m('RcNoRepSys', '%d' % (len(bysys) - _nconfA))
m('RcNoRepSysAll', '%d' % (len(ALLSYS) - _nconfAll))
_nocat = sorted({e for k in U
                 for e in CROSS[k].get('catalogue_blocks_without_spectra', [])})
m('RcNCatNoSpec', '%d' % len(_nocat))
m('RcSearchSys', '%d' % len(bysys))
m('RcSearchSysAll', '%d' % len(ALLSYS))
m('RcSearchWin', '%d' % len(A))
# ★ The frequency extents are NOT emitted here.  They are the same
# quantities the coverage generator publishes as \CvUnionA, \CvConfGHzDay,
# \CvConfGHzYr and \CvConfPctDay, measured on the survey-wide union rather
# than summed over systems, and two names for one idea carrying two values
# is exactly what this round is removing.  This section quotes those.

# ------------------------------------------------------------- assertions
print('\nassertions')
_e = [k for k in ROWS if CROSS[k]['star'] == 'eta Crv']
if _e:
    s = ROWS[_e[0]]['s']
    v = (abs(s['T_pers'] - 10.95) if DRIVE != 2 else 9.0)
    # ★ Both readings are pinned, so that redefining the exclusion cannot
    # silently move the underlying measurement: the first number is the one
    # the paper quotes, the second is the same arithmetic with the discovery
    # amplitude treated as exact, and the frame transport is the third.
    ck('A1 eta Crv reproduces its published measurement under both readings',
       v < 0.02 and abs(s['excl'] - 4.81) < 0.02
       and abs(s['excl_conditional'] - 11.57) < 0.02
       and abs(s['n_eff'] - 4.79) < 0.01,
       'T_pers %.2f (10.95), excl %.2f (4.81), conditional %.2f (11.57), '
       'N_eff %.2f (4.79)'
       % (s['T_pers'], s['excl'], s['excl_conditional'], s['n_eff']))
ck('A2 every unattributed crossing is tested, and the rows whose exclusion '
   'is withheld are exactly the ones the ledger flags on quality',
   N_ALLTEST == N_UNATTR
   and len(U) - len(QU) == len(LDQ & LUNATTR)
   and len(QU) + len(LDQ & LUNATTR) + N_NOSPEC == N_UNATTR,
   '%d with an exclusion + %d withheld (%d flagged in the ledger) + %d '
   'criterion-only == %d'
   % (len(QU), len(U) - len(QU), len(LDQ & LUNATTR), N_NOSPEC, N_UNATTR))
v = TBD if DRIVE != 3 else 9.9
ck('A3 nothing reaches the trigger at the registered cell, at any drift',
   v < TRIG, 'largest drift-maximised T* over %d blocks = %.2f'
   % (NREP_MEAS, TBD))
# ★★ WHAT THE EXCLUSIONS SUPPORT, STATED AS A LIMIT RATHER THAN AS A
# SIGNIFICANCE.  "Every tested crossing is excluded above the trigger" was
# true only of the reading that treats the discovery amplitude as exact, and
# it was asserted in a form that could not notice the difference.  The claim
# that does survive is the limit: for every crossing carrying an exclusion, a
# carrier at the discovery amplitude is ruled out at the trigger, and for most
# of them a carrier well below it is too.
v = FFIVE[-1] if DRIVE != 4 else 1.5
ck('A4 a carrier at the discovery amplitude is ruled out at the trigger for '
   'every crossing carrying an exclusion',
   v <= 1.0, 'the worst case needs %.2f of the discovery amplitude; the '
   'median %.2f; %d of %d at or below one half'
   % (FFIVE[-1], FFIVE[len(FFIVE) // 2],
      sum(1 for f in FFIVE if f <= 0.5), len(FFIVE)))
_g = [c['discovery'] for c in CROSS.values() if c['status'] == 'ok']
v = max(abs(d['gate_rel']) for d in _g) if DRIVE != 5 else 1.0
ck('A5 every discovery window reproduces its published statistic',
   v < 1e-6, 'worst relative error %.1e over %d windows' % (v, len(_g)))
v = CONF['Day'][0] if DRIVE != 6 else len(bysys)
ck('A6 confirmability is strictly smaller than searchability',
   v < len(bysys), '%d of %d Class A systems have an independent repeat at '
   'the same frequency' % (CONF['Day'][0], len(bysys)))
# ★ this one can only fail if the deposit loses the pathology list, which is
# how a 1.4 microJy noise got into a combined sigma in the first place
v = R['n_bad_weight_block_measurements'] if DRIVE != 7 else 0
ck('A7 the weight-pathology list is applied and bites',
   v >= 1, '%d repeat measurement(s) dropped by badweight.json' % v)
# ★★ R2-M7: the two criteria must be demonstrably different, or publishing
# both is noise.  A revisit at any tuning is a weaker condition than a
# revisit covering the same frequency, so its count must be strictly larger
# on at least one denominator; if the two ever agree, one of them is being
# computed by the other's rule.
_mm = dict(M)
_a = (int(_mm['RcRevSysAllDay']), int(_mm['RcConfSysAllDay']))
if DRIVE == 8:
    _a = (_a[1], _a[1])
ck('A8 revisiting a system and recovering its frequencies are different '
   'conditions', _a[0] > _a[1],
   '%d of %d systems revisited after a day, %d of them at a frequency the '
   'earlier block also covered' % (_a[0], len(ALLSYS), _a[1]))
# ★ and the Class A subset cannot exceed the whole sample
v = (int(_mm['RcConfSysDay']) <= int(_mm['RcConfSysAllDay'])
     and int(_mm['RcRevSysDay']) <= int(_mm['RcRevSysAllDay'])
     ) if DRIVE != 9 else False
ck('A9 every Class A count lies inside its all-system count', v,
   'Class A %s/%s against all %s/%s' % (_mm['RcConfSysDay'],
                                        _mm['RcRevSysDay'],
                                        _mm['RcConfSysAllDay'],
                                        _mm['RcRevSysAllDay']))
# ★ the two events the section and the figure describe are selected by a
# measured property, and there must be exactly two of them
_n = len(_SCRALL) if DRIVE != 10 else 3
ck('A10 exactly two crossings outrank every control position', _n == 2,
   '%s' % [ROWS[k]['c']['display'] for k in _SCRALL])

# ------------------------------------------------------------ the tables
# (1) the recurrence columns of the crossing ledger, for ledger_v410.py
# ★★★ R2-M7, SECOND BULLET.  The ledger printed `T_max` and the event table
# printed "T_star measured", and the two disagreed -- 1.65 against 2.71 for
# one crossing and 0.96 against 3.60 for the other.  They were never the
# same quantity.  There are two readings of one cell and the paper needs
# both, so both are carried here under names that say which is which:
#
#   T_matched   the statistic at the predicted stellar-frame cell with the
#               DISCOVERY DRIFT transported to that epoch.  One cell, one
#               drift, nothing maximised, so it is an unbiased amplitude and
#               it is what the exclusion is built from.  It can be negative.
#   T_anydrift  the largest value found at that same cell over EVERY drift
#               trial.  It is a maximum over about 120 trials, so it is
#               biased upward and cannot be compared with the trigger as
#               though it were one measurement -- but it is the
#               conservative number, and it is the one a reader asking
#               "was anything there at all?" wants.
#
# Both now appear in both tables, with the same definitions and the same
# values.  `dt_min_d`/`dt_max_d` are the recurrence interval R1 asks for.
# ★★★ AND A THIRD, WHICH IS THE ONE THE EXCLUSION ACTUALLY USES AND WHICH
# THE LEDGER WAS NOT PRINTING.  `T_matched` above is the LARGEST of the
# per-block readings, and the mean of a maximum over n blocks is not zero:
# over the rows carrying exclusions it came out at +1.13 where a zero-mean
# statistic scatters by 0.18, which read as a systematic positive offset at
# the predicted cells and is nothing of the kind.  `T_rep` is the
# inverse-variance combination of the same readings -- one number for the
# whole repeat coverage, the quantity T_pers is compared against, and the
# quantity the exclusion is formed from.  Its mean over the same rows is
# -0.13.  THE LEDGER PRINTS `T_rep`; the per-block maximum is kept here and
# in the data release, where a maximum can be labelled as one.
# ★ `T_matched` IS KEPT AS AN ALIAS OF `T_rep`, DELIBERATELY.  The ledger
# generator reads this file by key name; if the key simply vanished, the
# ledger's recurrence column would quietly print "---" on every row, which is
# a blank column rather than a wrong one but is still a silent failure of a
# table whose caption promises every disposition can be reproduced from it.
# The alias carries the CORRECT value, so the ledger is right either way, and
# the maximum lives under a name that says it is one.
cols = {'_doc': 'T_rep is the inverse-variance combination of the repeat '
                'readings at the predicted cell and is what the exclusion is '
                'formed from; T_matched is a deprecated alias of it; '
                'T_matched_max is the largest single repeat block, which is '
                'a maximum over n_rep and positive on average whatever is '
                'there; T_anydrift is the largest over every drift trial at '
                'that cell; excl is (S-abar)/sqrt(sigma_d^2+sigmabar^2); '
                'excl_conditional treats the discovery amplitude as exact; '
                'f5 is the fraction of the discovery amplitude still ruled '
                'out at the trigger, (T_rep+5)/T_pers.'}
for cid, r in ROWS.items():
    c, s = r['c'], r['s']
    cols['%s|%.6f' % (c['eb'], c['freq_GHz'])] = dict(
        n_rep=s['n'], n_rep_cat=s['n_in_catalogue'],
        T_rep=round(s['T_rep'], 2),
        T_matched=round(s['T_rep'], 2),
        T_matched_max=round(s['T_max'], 2),
        T_anydrift=round(s['T_bestdrift_max'], 2),
        T_pers=round(s['T_pers'], 1), excl=round(s['excl'], 1),
        excl_conditional=round(s['excl_conditional'], 1),
        f5=round(s['f5'], 3), n_eff=round(s['n_eff'], 2),
        dt_min_d=round(s['sep_min_h'] / 24.0, 3),
        dt_max_d=round(s['sep_max_h'] / 24.0, 3),
        rank_ctrl=(None if c.get('rank_ctrl') is None
                   else round(float(c['rank_ctrl']), 2)))
for q in UNTESTED:
    cols['%s|%.6f' % (q['eb'], q['freq_GHz'])] = dict(
        n_rep=None, n_rep_cat=None, T_rep=None, T_matched=None,
        T_matched_max=None,
        T_anydrift=None, T_pers=None, excl=None, excl_conditional=None,
        f5=None, n_eff=None, dt_min_d=None, dt_max_d=None,
        rank_ctrl=(None if q.get('rank_ctrl') is None
                   else round(float(q['rank_ctrl']), 2)),
        note='dynamic spectrum not retained')
_alias = [k for k, v in cols.items()
          if k != '_doc' and v.get('T_rep') != v.get('T_matched')]
if DRIVE == 16:
    _alias = ['forced']
ck('A15 the deprecated alias carries the combined reading, so the ledger '
   'prints the right number whichever key it reads', not _alias,
   '%d row(s) where the two disagree' % len(_alias))
json.dump(cols, open(out('recurcols_v411.json'), 'w'), indent=1)

# ★ `tab_recurcols_v411.tex` is NOT written any more.  It was a second,
# smaller copy of the ledger's recurrence columns, it was never \input by
# the manuscript, and a generated table fragment that nothing typesets is a
# second place for these numbers to live and drift.  The ledger carries
# them.

# (2) the event table: everything measured about the two crossings whose
#     star outranks every control position, in one place.
def flux_eirp(c):
    d = c['discovery']
    rows = [r for r in CAT if r['eb'] == c['eb']
            and min(float(r['flo_GHz']), float(r['fhi_GHz'])) <= c['freq_GHz']
            <= max(float(r['flo_GHz']), float(r['fhi_GHz']))]
    dist = float(rows[0]['dist_pc']) if rows else None
    e = None
    if dist:
        e = (4.0 * math.pi * (dist * 3.0856775814913673e16) ** 2
             * d['amp_mJy'] * 1e-29 * d['chanw_Hz'])
    return dist, e


# ★ The disposition is the LEDGER's, not this record's.  The frozen
# recurrence input carries the attribution the mask had when it was made,
# and if the mask changes the two would disagree in the same paper.
LDISPO = {(r['eb'], round(float(r['freq']), 4)): bool(r['attributed'])
          for r in LED['rows']}
LROWX = {(r['eb'], round(float(r['freq']), 4)): r for r in LED['rows']}
ck('A11 both tabulated events have a ledger row, so the table cannot state '
   'a disposition the ledger does not',
   all((ROWS[k]['c']['eb'],
        round(float(ROWS[k]['c']['freq_GHz']), 4)) in LDISPO
       for k in _scrkeys) if DRIVE != 11 else False,
   '%s' % [(ROWS[k]['c']['display'],
            LDISPO.get((ROWS[k]['c']['eb'],
                        round(float(ROWS[k]['c']['freq_GHz']), 4))))
           for k in _scrkeys])

C1 = [r'%% GENERATED by recur_v411.py -- do not hand-edit.',
      # ★ The label column WRAPS.  Set as a bare `l` it ran 25 pt past the
      # column measure -- an overfull \hbox, which is a row of type printed
      # over the margin and which this build now treats as a failure.  A
      # fixed-width wrapping box cannot be outgrown by a longer row label.
      (r'\begin{tabular}{@{}>{\raggedright\arraybackslash}'
       r'p{0.49\columnwidth}' + '@{~~}r' * len(_scrkeys) + r'@{}}'),
      r'\hline']
HDR = [('Star', lambda c, s: c['display']),
       (r'Frequency (GHz)', lambda c, s: '%.6f' % c['freq_GHz']),
       (r'Channel width (kHz)',
        lambda c, s: '%.2f' % (c['discovery']['chanw_Hz'] / 1e3)),
       (r'Drift rate (Hz\,s$^{-1}$)',
        lambda c, s: '$%s$' % num(c['discovery']['drift_Hz_s'], 0, True)),
       (r'$T_\star$', lambda c, s: '%.3f' % c['discovery']['T_matched']),
       (r'Highest control $T$',
        lambda c, s: '%.2f' % (c['rank_ctrl'] or 0.0)),
       (r'Flux density (mJy)',
        lambda c, s: '%.1f $\\pm$ %.1f' % (c['discovery']['amp_mJy'],
                                           c['discovery']['sig_mJy'])),
       # ★ R2 minor 27.  This row is the EIRP implied by the flux in the
       # PEAK CHANNEL, which is a measurement, and not EIRP_90, which is a
       # limit.  An intrinsically unresolved carrier passed through the
       # online Hanning smoothing leaves only about half its power in that
       # channel, so the power actually radiated is about twice this -- a
       # factor that is inside EIRP_90 because the injections carry it, and
       # is NOT inside this row.  Naming the row is the fix; the caption
       # gives the factor.
       (r'Peak-channel EIRP (W)', lambda c, s: '$%.1f \\times 10^{%d}$'
        % tuple(_mant(flux_eirp(c)[1]))),
       # ★ the band, the nearest transition and the stellar-frame offset
       # are Table 9's for these two crossings and are not repeated here.
       (r'Repeat epochs measured', lambda c, s: '%d' % s['n']),
       (r'\quad in the released catalogue',
        lambda c, s: '%d' % s['n_in_catalogue']),
       (r'\quad catalogue blocks at $\nu$',
        lambda c, s: '%d' % c['n_catalogue_covering_blocks']),
       # ★ R2-minor 22: the nearest covering epoch of the stronger event is
       # EARLIER than its discovery, so neither the row label nor the text
       # may say "later"; and a block two hours away is an independent
       # execution block but not a temporally independent epoch, which is
       # R1-4.  Both are now stated as measurements: the signed separation
       # from the discovery, and how many of the covering epochs clear a day.
       (r'Observed', lambda c, s: mjd_to_date(
           c['discovery']['t_start_mjdsec'] / 86400.0)),
       (r'Nearest covering epoch', lambda c, s: mjd_to_date(
           s['nearest_block']['t_start_mjdsec'] / 86400.0)),
       (r'\quad separation (h)', lambda c, s: '$%s$' % num(
           s['nearest_block']['sep_from_discovery_h'], 2, True)),
       (r'\quad covering epochs more than a day away',
        lambda c, s: '%d' % s['n_day']),
       (r'Longest baseline (d)',
        lambda c, s: '%.0f' % (s['sep_max_h'] / 24.0)),
       (r'$T$ expected if persistent, $T_{\rm pers}$',
        lambda c, s: '%.2f' % s['T_pers']),
       (r'$T$ measured, matched drift, $T_{\rm rep}$',
        lambda c, s: '%+.2f' % s['T_rep']),
       (r'\quad largest single epoch',
        lambda c, s: '%+.2f' % s['T_max']),
       (r'\quad maximised over every drift',
        lambda c, s: '%.2f' % s['T_bestdrift_max']),
       (r'Exclusion, $\sigma_{\rm excl}$',
        lambda c, s: '%s$\\sigma$' % sig(s['excl'])),
       (r'Amplitude still excluded at $5\sigma$',
        lambda c, s: '%.2f $S$' % s['f5']),
       (r'Disposition', lambda c, s: (
           'attributed' if LDISPO.get(
               (c['eb'], round(float(c['freq_GHz']), 4)))
           else 'not confirmed'))]
C1.append(' & '.join([''] + [ROWS[k]['c']['display'] for k in _scrkeys])
          + r' \\')
C1.append(r'\hline')
for lab, fn in HDR[1:]:
    C1.append(lab + ' & '
              + ' & '.join(fn(ROWS[k]['c'], ROWS[k]['s']) for k in _scrkeys)
              + r' \\')
C1 += [r'\hline', r'\end{tabular}']
open(out('tab_recurcand_v411.tex'), 'w').write('\n'.join(C1) + '\n')

# (3) the visibility-fit table, which replaces the box inside Fig. 7
S = json.load(open(os.path.join(HERE, 'ledger_v403.json')))['summary']
# ★ R2-minor 9 is right that "12 controls" looked inconsistent with "full
# dynamic spectra survive for only 8 of 512", and it was our own fault for
# printing one number without saying which control set it belonged to.  There
# are three, they are different things, and they are now tabulated together so
# the question cannot arise again.
_NVIS = int(macro('EpNVisCtrl'))
# ★★ The number of controls with a retained dynamic spectrum is MEASURED from
# the records this generator already reads, not taken from `\LNNRetained`.
# That macro's only prose citation is being deleted this round, and
# `retire_macros.py` deletes an uncited macro from the layer -- which would
# have stopped this generator dead on the next clean build, two steps away
# from the edit that caused it.  The macro is still compared against where it
# survives, so the two cannot drift.
_RETSET = {d['n_ctrl_retained'] for d in
           [c['discovery'] for c in CROSS.values() if c['status'] == 'ok']}
assert len(_RETSET) == 1, (
    'the retained-control count is not uniform across the discovery '
    'windows: %s' % sorted(_RETSET))
_NRET = _RETSET.pop()
try:
    _NRETMAC = int(macro('LNNRetained'))
except SystemExit:
    _NRETMAC = None
ck('A12 the measured retained-control count agrees with the macro layer '
   'where the layer still defines it',
   _NRETMAC in (None, _NRET) if DRIVE != 12 else False,
   'measured %d, layer %s' % (_NRET, _NRETMAC))
_NCTRL = int(macro('NCtrl'))
m('RcNVisCtrl', '%d' % _NVIS)
m('RcNRetCtrl', '%d' % _NRET)
V = [r'%% GENERATED by recur_v411.py -- do not hand-edit.',
     r'\begin{tabular}{@{}lr@{}}', r'\hline',
     r'Crossings re-measured in the visibility domain & %d of %d \\'
     % (S['n_fitted'], S['n_crossings']),
     r'\quad consistent with a point source at the stellar position & %d \\'
     % S['n_localised_corrected'],
     r'\quad of those, unattributed & %d \\'
     % S['n_localised_unattributed_corrected'],
     r'\hline',
     r'Control positions in the image-plane rank screen & %d \\' % _NCTRL,
     r'\quad with a full dynamic spectrum retained & %d \\' % _NRET,
     r'Control positions available in the visibility fit & %d \\' % _NVIS,
     r'\hline', r'\end{tabular}']
open(out('tab_visfit_v411.tex'), 'w').write('\n'.join(V) + '\n')

# --------------------------------------------------------------- emit
with open(out(os.path.basename(OUT)), 'w') as fh:
    fh.write('%% GENERATED by recur_v411.py -- do not hand-edit.\n')
    for k, v in M:
        assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
print('tested %d of %d unattributed crossings over %d repeat-block '
      'measurements in %d distinct blocks (%d outside the released catalogue)'
      % (N_TESTED, N_UNATTR, NREP_MEAS, len(REP_EB), len(REP_OUT)))
print('largest T* at the registered cell %.2f (matched drift) / %.2f '
      '(any drift); exclusions %.1f-%.1f sigma, median %.1f'
      % (TMAX, TBD, EXCL[0], EXCL[-1], EXCL[len(EXCL) // 2]))
print('searchability %d Class A systems / %.1f GHz;  confirmability %d '
      'systems / %.1f GHz (%.0f%%) with an independent repeat at the same '
      'frequency; over years %d systems / %.1f GHz'
      % (len(bysys), CONF['Day'][2], CONF['Day'][0], CONF['Day'][1],
         100 * CONF['Day'][1] / CONF['Day'][2], CONF['Yr'][0], CONF['Yr'][1]))
if fail and DRIVE == 0:
    raise SystemExit('assertions failed: %s' % fail)
