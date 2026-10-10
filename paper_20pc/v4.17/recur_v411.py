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
# ★★★★ v4.16: THE PREPASS, AND THE CYCLE THAT MADE IT NECESSARY.
# Table 5's last two rows are round 550's (`recurcond_v416.py`): the
# displacement the exclusion permits and what an orbit at 1 au would do over
# the same baseline.  They are READ here rather than recomputed, which is
# right -- two generators computing one quantity drift, one computing it and
# the other reading it cannot.  But `recurcond_v416.py` reads THIS file's
# `recurcols_v411.json` and round 120's \RcFrac... in return, so on a tree
# with no macro layer at all -- which is exactly what `cleanregen.py` makes,
# and what a fresh checkout is -- neither generator can go first and
# `macro('RcFreqSx')` raises `macro ... not found`.
#
# Resolved the same way `ledger_v410.py --no-recur` resolves the identical
# cycle with this file: a PREPASS writes the products the other generator
# needs and nothing else.  `--no-round550` writes `recurcols_v411.json` and
# round 120, does not read round 550, and does not emit Table 5 -- and it
# DELETES any Table 5 left from an earlier run, so the prepass cannot leave a
# tree that typesets.  The full run follows immediately in `make_all.sh`,
# re-reads round 550, re-runs A18 and writes every product.  Nothing in the
# authoritative pass is weakened, and the prepass cannot be mistaken for it.
PREPASS = '--no-round550' in sys.argv


def out(name):
    """Every product of a driven run is suffixed.  A test must never write a
    path production reads; the suffix follows the FLAG, not the perturbation."""
    b, e = os.path.splitext(name)
    return os.path.join(HERE, b + SFX + e)


TRIG = 5.0
SEP_DAY = 1.0           # the paper's own definition of an independent epoch
# ★★★ WHERE THE CONFIRMATION TEST HAS USEFUL POWER.  The criterion is that the
# repeat reach the trigger again at the predicted cell, and the reading there
# scatters by one, so a carrier persisting at an amplitude giving T_pers is
# recovered with probability Phi(T_pers - 5).  Below this probability the
# criterion is not a test of that crossing and the paper must not read its
# silence as an exclusion.  One declared level, used everywhere.
POWER = 0.90


def _phi(x):
    """The standard normal distribution function.  No new apparatus: the
    recurrence reading is centred on zero and scatters by one, measured in
    Appendix B, so the probability of clearing the trigger is this and
    nothing more."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def power_at(t_pers):
    """Probability that a carrier giving T_pers is recovered by the
    criterion."""
    return _phi(t_pers - TRIG)


def med(v):
    """The median, properly, for an even-length sample too.  Taking the upper
    middle element is this project's habit and it is not a median."""
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def namelist(items):
    """A readable list of crossings, grouped by star, built from the rows and
    never typed: `(display, frequency)` pairs in, English out.  A generator
    that names results must read them."""
    byname, order = {}, []
    for disp, f in items:
        if disp not in byname:
            byname[disp] = []
            order.append(disp)
        byname[disp].append(f)
    parts = []
    for disp in order:
        fs = ['%.2f' % f for f in sorted(byname[disp])]
        if len(fs) == 1:
            parts.append('%s at %s\\,GHz' % (tname(disp), fs[0]))
        else:
            parts.append('%s at %s and %s\\,GHz'
                         % (tname(disp), ', '.join(fs[:-1]), fs[-1]))
    if len(parts) == 1:
        return parts[0]
    return ' and '.join([', '.join(parts[:-1]), parts[-1]])


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
# ★★ EVERY FREQUENCY THIS GENERATOR NAMES IN RUNNING TEXT IS THE ONE IN THE
# STAR'S OWN FRAME.  The measurement record carries the topocentric
# frequency the correlator delivered, and the prose elsewhere quotes the same
# crossings in the stellar frame, so a list built from the record read two
# frequencies for one event -- 241.75 and 241.77 GHz for the same beta Pic
# crossing, 23 MHz apart, which is the barycentric term.  The ledger is the
# one place the transported frequency is computed, so it is read from there
# and joined on block and frequency, never on a star name.
FSTELLAR = {(r['eb'], round(float(r['freq']), 4)): r['frame']['f_stellar']
            for r in LED['rows']}


def fstellar(c):
    return FSTELLAR[(c['eb'], round(float(c['freq_GHz']), 4))]


CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
import epochs_r14 as _ep    # the ONE determination of a block's epoch
MJD = _ep.EPOCHS            # measured where one survives, stored elsewhere

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
                # ★★ THE POWER OF THE CRITERION ON THIS CROSSING, which is
                # what turns a silence into an exclusion or leaves it a
                # silence.  Two amplitudes, because the discovery amplitude
                # is biased high: the measured one, and the trigger
                # amplitude S x 5/T_star -- the faintest carrier that could
                # have produced the crossing at all, and so the most
                # pessimistic reading available without assuming a prior.
                p_conf=power_at(S / sb),
                p_conf_trig=power_at(
                    (S / sb) * TRIG / c['discovery']['T_matched']),
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
m('RcExclMed', '%.1f' % med(EXCL))
m('RcExclMax', '%.1f' % EXCL[-1])
m('RcNExclFive', '%d' % sum(1 for e in EXCL if e >= TRIG))
# ★★ `RcFracMed` IS A MEDIAN AND MUST BE CALLED ONE.  It was printed in the
# chain figure as "carriers above \RcFracMed{} of the discovery amplitude
# excluded", which is a bound; the values run to \RcFracMax, so the figure
# claimed an exclusion the ledger refutes.  The median, the range and the
# number of crossings the test cannot exclude now travel together.
m('RcFracMed', '%.2f' % med(FFIVE))
m('RcFracMin', '%.3f' % FFIVE[0])
m('RcFracMax', '%.2f' % FFIVE[-1])
m('RcNFracHalf', '%d' % sum(1 for f in FFIVE if f <= 0.5))
# ---- where the criterion has power, and where it has not
PCONF = [(ROWS[k]['s']['p_conf'], ROWS[k]['s']['p_conf_trig'],
          ROWS[k]['c']['display'], fstellar(ROWS[k]['c']),
          ROWS[k]['s']['T_pers']) for k in QU]
PCONF.sort()
_lo = [p for p in PCONF if p[0] < POWER]
_lotrig = [p for p in PCONF if p[1] < POWER]
m('RcPowerLevel', '%.0f' % (100.0 * POWER))
m('RcNPowerHi', '%d' % (len(PCONF) - len(_lo)))
m('RcNPowerLo', '%d' % len(_lo))
m('RcNPowerLoTrig', '%d' % len(_lotrig))
m('RcPowerMin', '%.2f' % PCONF[0][0])
m('RcPowerMinTrig', '%.2f' % min(p[1] for p in PCONF))
m('RcPowerLoHi', '%.2f' % (max(p[0] for p in _lo) if _lo else 0.0))
m('RcPowerLoList', namelist([(p[2], p[3]) for p in _lo]) if _lo else 'none')
m('RcPowerLoTPersLo', '%.1f' % (min(p[4] for p in _lo) if _lo else 0.0))
m('RcPowerLoTPersHi', '%.1f' % (max(p[4] for p in _lo) if _lo else 0.0))
# ---- and the crossings whose limit on the amplitude is weakest, which is a
#      different question and a different set: the two overlap but neither
#      contains the other, so both are named.
_worst = sorted([(ROWS[k]['s']['f5'], ROWS[k]['c']['display'],
                  fstellar(ROWS[k]['c'])) for k in QU], reverse=True)
_wsel = [w for w in _worst if w[0] >= 0.8]
m('RcNFracWeak', '%d' % len(_wsel))
m('RcFracWeakLo', '%.2f' % (min(w[0] for w in _wsel) if _wsel else 0.0))
m('RcFracWeakList',
  namelist([(w[1], w[2]) for w in _wsel]) if _wsel else 'none')
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
    # ★ The excluded amplitude fraction, which is what the section quotes:
    # the significance at which two readings of one amplitude disagree
    # saturates at the discovery significance when the repeat is deep, so it
    # is kept in the released ledger and not in the running text.
    m('Rc%sFive' % tag, '%.2f' % s['f5'])
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
        # ★★★ ROUND 14: the separation is MEASURED, through epochs_r14, not
        # read out of epochs_v386.json -- which resolved every block the
        # archive does not index by asdm_uid through its member OUS and
        # returned the earliest block of the unit, so 252 of 404 stamps are
        # shared and 90 of the 141 checkable ones are wrong.  \RcConfSysDay
        # was understated: 30 of the 60 Class A systems against 37.
        if _ep.separated([e for _a, _b, e in iv if _a <= mid <= _b], sep):
            keep.append([pts[i], pts[i + 1]])
    return union(keep), union([(a, b) for a, b, _ in iv])


def revisited(rows, sep):
    """A system two of whose execution blocks are more than `sep` days
    apart, WHETHER OR NOT they cover a common frequency.  This is the weaker
    of the two criteria and is counted only so the paper can say how much
    weaker: a revisit at a different tuning cannot retest a crossing."""
    return _ep.separated([r['eb'] for r in rows], sep)


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
# ★★★ THE MEDIAN IS NOT A BOUND, AND THIS IS THE CHECK THAT SAYS SO.  The
# previous assertion here was `max(f5) <= 1.0`, which is almost a tautology --
# f5 is a ratio of a reading to an expectation and sits near one whenever the
# repeat coverage is no deeper than the discovery -- and the figure built on
# it printed the median as though it were the worst case.  What must be true
# is that the median is strictly smaller than the largest value, so the two
# cannot be interchanged, and that the rows at the weak end are named rather
# than averaged away.  Driven at 4 by collapsing the spread.
_fm, _fx = med(FFIVE), FFIVE[-1]
if DRIVE == 4:
    _fm = _fx
ck('A4 the fraction of the discovery amplitude still excluded has a spread, '
   'so its median cannot be read as a bound, and the weak end is named',
   _fm < _fx - 0.01 and (not _wsel or _wsel[0][0] == _fx),
   'median %.2f against a largest %.2f; %d of %d at or below one half; the '
   'weakest are %s' % (_fm, _fx, sum(1 for f in FFIVE if f <= 0.5),
                       len(FFIVE), dict(M)['RcFracWeakList']))
# ★★ AND WHERE THE CRITERION HAS NO POWER IT IS NOT AN EXCLUSION.  A carrier
# persisting at the discovery amplitude clears the trigger again with
# probability Phi(T_pers-5); the crossings below the declared level are
# counted and named, and the count must not be allowed to go quietly to zero
# by a change of definition.  Driven at 17.
_nlo = len(_lo) if DRIVE != 17 else 0
ck('A16 every crossing the criterion cannot test at the declared power is '
   'counted and named',
   (_nlo == len(_lo)) and (len(_lo) == 0 or dict(M)['RcPowerLoList'] != 'none')
   and len(_lo) + (len(PCONF) - len(_lo)) == len(QU),
   '%d of %d below %.0f per cent, T_pers %.1f-%.1f: %s'
   % (len(_lo), len(QU), 100 * POWER,
      min((p[4] for p in _lo), default=0.0),
      max((p[4] for p in _lo), default=0.0),
      dict(M)['RcPowerLoList']))
# ★ the bias-corrected amplitude must be the pessimistic one, or quoting both
# buys nothing: the trigger amplitude is at or below the measured amplitude
# for every row, so its power can only be lower.
_pp = [(p[0], p[1]) for p in PCONF]
if DRIVE == 18:
    _pp = [(b, a) for a, b in _pp]
ck('A17 the power at the trigger amplitude is never above the power at the '
   'measured amplitude', all(b <= a + 1e-9 for a, b in _pp),
   'lowest %.2f measured against %.2f at the trigger amplitude'
   % (PCONF[0][0], min(p[1] for p in PCONF)))
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
                'out at the trigger, (T_rep+5)/T_pers; p_conf is the '
                'probability Phi(T_pers-5) that a carrier persisting at the '
                'discovery amplitude would satisfy the confirmation '
                'criterion, and p_conf_trig the same at the trigger '
                'amplitude S x 5/T_star, which is the faintest carrier '
                'consistent with the crossing having been found at all.'}
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
        p_conf=round(s['p_conf'], 3), p_conf_trig=round(s['p_conf_trig'], 3),
        dt_min_d=round(s['sep_min_h'] / 24.0, 3),
        dt_max_d=round(s['sep_max_h'] / 24.0, 3),
        rank_ctrl=(None if c.get('rank_ctrl') is None
                   else round(float(c['rank_ctrl']), 2)))
for q in UNTESTED:
    cols['%s|%.6f' % (q['eb'], q['freq_GHz'])] = dict(
        n_rep=None, n_rep_cat=None, T_rep=None, T_matched=None,
        T_matched_max=None,
        T_anydrift=None, T_pers=None, excl=None, excl_conditional=None,
        f5=None, n_eff=None, p_conf=None, p_conf_trig=None,
        dt_min_d=None, dt_max_d=None,
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

# ★★ THE STELLAR-FRAME FREQUENCY IS THE LEDGER'S, and the two new rows of
# this table are round 550's, read by name and joined on that frequency
# rather than on the order the two events happen to come out in.  Two
# generators computing one quantity drift; one computing it and the other
# reading it cannot.
if PREPASS:
    # ★ THE PREPASS WRITES ROUND 120 AND `recurcols_v411.json`, WHICH IS ALL
    # ROUND 550 NEEDS, AND THEN REMOVES TABLE 5 so that a tree on which the
    # full pass did not follow cannot typeset: the manuscript \inputs
    # `tab_recurcand_v411.tex`, so its absence is a LaTeX error and the
    # `latexlog` gate's failure, not a quiet omission.  A18 is not "skipped":
    # the pass that skips it also destroys the only product it guards.
    DVMAC = {}
    _t5 = os.path.join(HERE, 'tab_recurcand_v411.tex')
    if os.path.exists(_t5):
        os.remove(_t5)
    print('  PREPASS (--no-round550): round 120 and recurcols_v411.json only;'
          ' Table 5 removed, A18 deferred to the full pass')
else:
    DVMAC = {macro('RqFreq' + t): (macro('RqDisp' + t), macro('RqOrb' + t),
                                   macro('RqOrbFar' + t),
                                   macro('RqNearFrac' + t))
             for t in ('Sx', 'Cp')}
    _fskeys = ['%.4f' % FSTELLAR[(ROWS[k]['c']['eb'],
                                 round(float(ROWS[k]['c']['freq_GHz']), 4))]
               for k in _scrkeys]
    if DRIVE == 19:
        _fskeys = ['%.4f' % ROWS[k]['c']['freq_GHz'] for k in _scrkeys]
    ck('A18 the displacement each tabulated event permits is round 550\'s, '
       'joined on the stellar-frame frequency, so neither row can be filled '
       'from the wrong event or from a topocentric frequency',
       all(f in DVMAC for f in _fskeys) and len(set(_fskeys)) == len(_scrkeys),
       'table keys %s against round 550 %s' % (_fskeys, sorted(DVMAC)))
    if DRIVE == 19:
        DVMAC = dict(DVMAC, **{f: ('?', '?', '?', '?') for f in _fskeys})

C1 = [r'%% GENERATED by recur_v411.py -- do not hand-edit.',
      # ★ The label column WRAPS.  Set as a bare `l` it ran 25 pt past the
      # column measure -- an overfull \hbox, which is a row of type printed
      # over the margin and which this build now treats as a failure.  A
      # fixed-width wrapping box cannot be outgrown by a longer row label.
      (r'\begin{tabular}{@{}>{\raggedright\arraybackslash}'
       r'p{0.49\columnwidth}' + '@{~~}r' * len(_scrkeys) + r'@{}}'),
      r'\hline']
HDR = [('Star', lambda c, s: c['display']),
       # ★ THE FREQUENCY IN THE STAR'S OWN FRAME COMES FIRST, because that is
       # the frame every statement about a crossing is made in; the frequency
       # the correlator delivered follows it, indented, so that a reader can
       # still find the window in the archive.  Printing one of them without
       # naming the frame is how one crossing came to be quoted at two
       # frequencies in two places.
       (r'Frequency, stellar frame (GHz)',
        lambda c, s: '%.6f' % FSTELLAR[(
            c['eb'], round(float(c['freq_GHz']), 4))]),
       (r'\quad as delivered, topocentric',
        lambda c, s: '%.6f' % c['freq_GHz']),
       (r'Drift rate (Hz\,s$^{-1}$)',
        lambda c, s: '$%s$' % num(c['discovery']['drift_Hz_s'], 0, True)),
       (r'$T_\star$', lambda c, s: '%.3f' % c['discovery']['T_matched']),
       (r'Highest control $T$',
        lambda c, s: '%.2f' % (c['rank_ctrl'] or 0.0)),
       # ★★ THE ROW IS NAMED FOR THE ESTIMATOR IT IS.  This is the amplitude
       # FITTED to the de-drifted carrier, with its own error.  The product
       # of the statistic and the window's published noise is a different
       # estimator of the same flux, carries no error, and was quoted
       # elsewhere in the paper as though the two were one measurement.
       (r'Fitted amplitude (mJy)',
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
       # ★★★★ THE LABEL WAS WRONG AND THE TWO ROWS READ AS A CONTRADICTION.
       # `n_catalogue_covering_blocks` counts the census blocks OTHER than
       # the discovery one whose window covers the frequency, INCLUDING any
       # whose dynamic spectrum was not retained; so for a crossing with one
       # census repeat the two rows printed "1" and "1", which says that the
       # only covering census block is the discovery block and that a census
       # repeat exists in it.  The difference between them is the quantity
       # worth printing -- census repeats with no retained spectrum -- and
       # that is what the third row now is.
       (r'Repeat epochs measured', lambda c, s: '%d' % s['n']),
       (r'\quad of them in the primary census',
        lambda c, s: '%d' % s['n_in_catalogue']),
       (r'\quad census repeats with no retained spectrum',
        lambda c, s: '%d' % (c['n_catalogue_covering_blocks']
                             - s['n_in_catalogue'])),
       # ★ R2-minor 22: the nearest covering epoch of the stronger event is
       # EARLIER than its discovery, so neither the row label nor the text
       # may say "later"; and a block two hours away is an independent
       # execution block but not a temporally independent epoch, which is
       # R1-4.  Both are now stated as measurements: the signed separation
       # from the discovery, and how many of the covering epochs clear a day.
       # ★ The channel width is quoted once, in the text, and the two
       # observing dates are in the ledger: a table of two columns should not
       # spend three rows on numbers another part of the paper already gives.
       (r'Nearest covering epoch, separation (h)', lambda c, s: '$%s$' % num(
           s['nearest_block']['sep_from_discovery_h'], 2, True)),
       (r'\quad covering epochs more than a day away',
        lambda c, s: '%d' % s['n_day']),
       (r'Longest baseline (d)',
        lambda c, s: '%.0f' % (s['sep_max_h'] / 24.0)),
       (r'$T$ expected if persistent, $T_{\rm pers}$',
        lambda c, s: '%.2f' % s['T_pers']),
       (r'$T$ measured, matched drift, $T_{\rm rep}$',
        lambda c, s: '$%+.2f$' % s['T_rep']),
       (r'\quad largest single epoch',
        lambda c, s: '$%+.2f$' % s['T_max']),
       (r'\quad maximised over every drift',
        lambda c, s: '%.2f' % s['T_bestdrift_max']),
       # ★★★ THE SINGLE-BLOCK READING, which assumes only the two
       # observations.  The combination above requires the carrier to return
       # to the same stellar-frame channel at the start of every covering
       # block, over the baseline the table prints four rows higher; the
       # survival of an orbiting transmitter can only be argued from this
       # pair of rows, over the interval to the nearest block.
       (r'Nearest block alone, $T_{\rm pers}$',
        lambda c, s: '%.2f' % (c['discovery']['amp_mJy']
                               / s['nearest_block']['sig_mJy'])),
       (r'\quad $T_{\rm rep}$',
        lambda c, s: '$%+.2f$' % s['nearest_block']['T_matched']),
       # ★★ THE EXCLUDED AMPLITUDE FRACTION IS THE EXCLUSION ROW, and
       # sigma_excl has been dropped from the table altogether.  The
       # significance at which the two readings disagree saturates at the
       # discovery significance when the repeat coverage is deep -- it is
       # (T_pers - T_rep)/sqrt(1 + (T_pers/T_star)^2), which tends to
       # T_star -- so on the deepest rows it restates a number the table
       # already prints two lines higher and says nothing about the repeat.
       # It stays in the released ledger, where a reader who wants it can
       # recompute it from these three columns.
       (r'Amplitude still excluded, $(T_{\rm rep}+5)/T_{\rm pers}$',
        lambda c, s: '%.2f $S$' % s['f5']),
       (r'\quad from the nearest block alone',
        lambda c, s: '%s $S$' % DVMAC[
            '%.4f' % FSTELLAR[(c['eb'],
                               round(float(c['freq_GHz']), 4))]][3]),
       # ★ WHAT THE EXCLUSION IS AN EXCLUSION OF.  The reading is taken at
       # one channel at one drift, so it holds only for a carrier whose
       # stellar-frame frequency moved by less than half that channel
       # between the two epochs.  Stated as a velocity it can be compared
       # with an orbit, which is the comparison a reader needs.
       (r'Displacement permitted (km\,s$^{-1}$)',
        lambda c, s: '$\\pm$%s' % DVMAC[
            '%.4f' % FSTELLAR[(c['eb'], round(float(c['freq_GHz']), 4))]][0]),
       (r'\quad a transmitter at 1\,au would move',
        lambda c, s: DVMAC[
            '%.4f' % FSTELLAR[(c['eb'], round(float(c['freq_GHz']), 4))]][1]),
       (r'\quad and over the longest baseline',
        lambda c, s: DVMAC[
            '%.4f' % FSTELLAR[(c['eb'], round(float(c['freq_GHz']), 4))]][2]),
       # ★ the power of the criterion on this crossing, at the measured
       #   amplitude and at the trigger amplitude.  Two numbers, one row,
       #   no new section: a reader can see at once whether the silence
       #   that follows is an exclusion or only a silence.
       # ★ The ADOPTED reading is the one at the trigger amplitude, because a
       # discovery amplitude selected as the largest of many cells is biased
       # high; the reading at the measured amplitude follows in brackets so
       # the size of that bias is visible rather than argued.
       (r'Recovery chance at $5S/T_\star$ (at $S$)',
        lambda c, s: '%.2f (%.2f)' % (s['p_conf_trig'], s['p_conf'])),
       (r'Disposition', lambda c, s: (
           'attributed' if LDISPO.get(
               (c['eb'], round(float(c['freq_GHz']), 4)))
           else 'not confirmed'))]
if not PREPASS:
    C1.append(' & '.join([''] + [ROWS[k]['c']['display'] for k in _scrkeys])
              + r' \\')
    C1.append(r'\hline')
    for lab, fn in HDR[1:]:
        C1.append(lab + ' & '
                  + ' & '.join(fn(ROWS[k]['c'], ROWS[k]['s'])
                               for k in _scrkeys)
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
