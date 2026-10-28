#!/usr/bin/env python3
r"""tolrecur_r21.py -- round 940.  THE REGISTRATION OF THE PREDICTED CELL,
MEASURED; THE EXCLUSIONS RE-DERIVED AT A TOLERANCE MATCHED TO IT; THE ONE
DRIFT MODEL; AND THE EXCLUSION DEPTHS OVER SEPARATED BLOCKS ALONE.

Four things this generator settles, all of them read out of the retained
per-integration spectra rather than argued:

1.  WHAT THE POSITIVE CONTROL SAYS, AND WHAT IT DOES NOT.  The single-cell
    reading at the predicted cell reaches the trigger in 11 of the 13
    line-attributed crossings the criterion recovers when one block is read
    alone, and in all 13 when the covering blocks are combined.  The paper
    claimed all 13 for the single-block reading and cited for it the table
    that prints 1.48 and 3.25.  Both counts are computed here from the frozen
    reading's own record.

2.  WHY SOME PREDICTED CELLS SIT TENS OF CHANNELS FROM THE LINE.  The table's
    offset column is measured against the brightest channel of each block's
    own window.  On a spatially resolved disc line a few km/s wide, the
    brightest channel is not the line's position: the four beta Pic CO(2-1)
    crossings predict four cells spanning tens of 15.3 kHz channels, and
    every one of them lands inside the line.  So the offsets are decomposed
    here into (a) the crossing's own place in the line profile, (b) peak
    against centroid in that block, and (c) what is left -- the registration
    residual, measured as the stellar-frame velocity centroid of the same
    line read in every covering block.  That residual is a VELOCITY, which is
    the whole point: it is a fraction of a channel where channels are wide
    and several channels where they are narrow.

3.  THE EXCLUSIONS AT A MATCHED TOLERANCE.  Each exclusion is re-derived as
    the maximum over the cells within the measured registration residual of
    the predicted cell, with the threshold raised so that the false-alarm
    probability of the widened reading equals the single cell's own.  The
    depth can only weaken, which is asserted rather than hoped: the maximum
    over a set that contains the single cell is never smaller than the single
    cell, and the threshold never falls.

4.  ONE DRIFT MODEL.  The reading registers the cell by the frame transform at
    the repeat epoch and de-drifts within each observation at the rate fitted
    there.  Under that model the drift error displaces the cell by the fitted
    drift's own uncertainty across one OBSERVATION, not across the gap; the
    displacement across the gap belongs to a different model -- a carrier that
    keeps drifting -- under which the single cell is not where the carrier is
    at all, which is the stated limitation and not an error budget.  Both are
    computed, each named for its own model, and the extreme value of each is
    reported with the window, channel width and baseline that produce it.

5.  SEPARATED BLOCKS ALONE (referee 2, 8).  Every depth and recovery
    probability is recomputed using only covering blocks that satisfy the
    paper's own confirmation criterion against the discovery block -- a
    different observing session and more than a day away -- through
    `epochs_r14.confirms`, the one implementation of that criterion.

INPUTS, all tree-local:
  r21inputs/tolprof_r21.json.gz  the de-drifted stack at every channel within
                                 +-1 km/s of the predicted cell, for all 445
                                 block readings of the recurrence plan.  Read
                                 out on the archive by `tol_r21.py`, which is
                                 `r10_recur_all.py` -- the frozen reading --
                                 with the single-cell evaluation replaced by a
                                 strip of cells.  Its own gate asserts that
                                 the j = 0 column reproduces the frozen
                                 reading to the last bit; the worst difference
                                 over 445 readings was exactly zero.
  r21inputs/tolline_r21.json.gz  the same for the 15 line-attributed
                                 crossings, within +-2 km/s.
  r10inputs/recur_v411.json      the published readings and block lists
  recurcols_v411.json            the published depths
  linerecur_r20.json             the positive-control payload of Table D2
  ledger.json                    the quality flag
  epochs_r14.py                  the confirmation criterion

Usage: tolrecur_r21.py [--tree DIR] [--drive N]
16 clauses (R0-R12, R13-R15), each demonstrated to fail under its own drive.
"""
import glob
import gzip
import json
import math
import os
import re
import sys

ROUND = 940
HERE = os.path.dirname(os.path.abspath(__file__))
TREE = sys.argv[sys.argv.index('--tree') + 1] if '--tree' in sys.argv else HERE
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '_drive%d' % DRIVE if '--drive' in sys.argv else ''
# ★ THE ROUND IS NAMED IN THE TEMPLATE, not hidden in the operand.
# `roundcollide`'s resolver matches `survey_numbers_round940%s.tex` and does
# NOT match `survey_numbers_round%d%s.tex`: with the round in the operand the
# only thing that credits a writer is the self-declared header fallback, which
# is how round 920 is credited in v4.21.  Asserted against ROUND so the two
# cannot drift apart.
OUT = os.path.join(HERE, 'survey_numbers_round940%s.tex' % SFX)
assert os.path.basename(OUT) == 'survey_numbers_round%d%s.tex' % (ROUND, SFX)
OUTJ = os.path.join(HERE, 'tolrecur_r21%s.json' % SFX)
OUTC = os.path.join(HERE, 'r21inputs', 'tolsep_r21%s.json' % SFX)

C = 299792.458
TRIG = 5.0
POWER = 0.90                      # the one declared level, as in round 120

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
    for p in sorted(glob.glob(os.path.join(TREE, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


def phi(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def iphi(p):
    """The normal quantile, by bisection: one declared tolerance, no table."""
    lo, hi = -40.0, 40.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def med(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def signed(x, fmt='%.2f'):
    """`minuscheck`: a negative value carries a real minus from the emitter."""
    return (r'\ensuremath{-}' + fmt % abs(x)) if x < 0 else fmt % x


def jload(*parts):
    """Read a tree input.  This generator's OWN inputs sit beside it, which is
    where they are in the version directory; everything else is the
    manuscript's.  Both roots are tried in that order and never a path built
    from a version number, so the generator cannot acquire a dependency on a
    predecessor version that a clean tree does not have."""
    for root in (HERE, TREE):
        p = os.path.join(root, *parts)
        if os.path.exists(p):
            if p.endswith('.gz'):
                with gzip.open(p, 'rt') as fh:
                    return json.load(fh)
            return json.load(open(p))
    raise IOError(os.path.join(*parts))


def tname(s):
    s = s.split(' Gaia')[0].strip()
    s = re.sub(r'^HD(\d)', r'HD \1', s)
    s = s.replace('bet Pic', r'$\beta$~Pic').replace('eta Crv', r'$\eta$~Crv')
    s = s.replace('CP-72', 'CP$-$72').replace('CD-57', 'CD$-$57')
    s = s.replace('BD05', 'BD+05')
    s = s.replace('ALMA J153702653-33192492',
                  r'ALMA~J153702653$-$33192492')
    return s.replace(' ', '~')


def _sname(s):
    #: the plain-text spelling the deposited files share, so si_recur.txt
    #: joins si_ledger.txt on the key its own header documents
    return SA.plain(SA.designation(s))


# =========================================================== the inputs
sys.path.insert(0, TREE)
EP = __import__('epochs_r14')
#: the house namer.  The deposited star column must carry the same string
#: si_ledger.txt does, or the join this file's own header documents does not
#: resolve for a reader.  `plain(designation(...))` is the recipe si_r18.py
#: and ledger_v410.py use; `designation(..., tex=False)` alone is NOT enough,
#: because it leaves `$\beta$~Pic` untouched.
SA = __import__('star_alias')

PROF = jload('r21inputs', 'tolprof_r21.json.gz')
LPROF = jload('r21inputs', 'tolline_r21.json.gz')
REC = jload('r10inputs', 'recur_v411.json')['crossings']
RCOL = jload('recurcols_v411.json')
LR = jload('linerecur_r20.json')
LED = jload('ledger.json')['rows']

PR = {}
for r in PROF['rows']:
    PR[(r['cid'], r['stem'])] = r

ck('R0 the read-out covers every published block reading of every tested '
   'crossing and reproduces the frozen single-cell statistic of each, which '
   'is what makes it a read-out of the published test and not a second test',
   PROF['gate_worst'] == 0.0
   and all((cid, b['stem']) in PR
           for cid, v in REC.items() if v['status'] == 'ok'
           for b in v['blocks'])
   and all(abs(PR[(cid, b['stem'])]['T_frozen_single'] - b['T_matched'])
           < 1e-9
           for cid, v in REC.items() if v['status'] == 'ok'
           for b in v['blocks'])
   and len(PROF['rows']) == int(macro('RcNRepeatMeas')) + 1,
   '%d readings, worst j=0 difference %r; the published count excludes the '
   'one flagged-weight product' % (len(PROF['rows']), PROF['gate_worst']))

# =====================================================================
# 1.  THE POSITIVE CONTROL: WHAT ONE BLOCK GIVES AND WHAT THE BLOCKS GIVE
# =====================================================================
D2 = LR['table_d2']
CTL = [v for v in D2.values() if v['verdict'] == 'recovered']
# ★★★★ THE COUNTS THE TEXT PRINTS ARE COUNTED OFF THE ROWS THE TABLE PRINTS.
# `linerecur_r20.json`'s `table_d2` carries the reading in the STRONGEST
# recovering block of any kind; the table names the strongest block the
# confirmation criterion admits, which for five of the thirteen rows is a
# different block, so counting here off `table_d2` counted a column the
# reader cannot see.  `confirm_r19.py` -- the one generator that decides
# which block each row names -- now deposits the rows as printed, and both
# counts come from there.  One quantity, one source.
CF = jload('confirm_r19.json')['table']
NSINGLE = sum(1 for v in CF if v['t_rep'] is not None and v['t_rep'] >= TRIG)
NCOMB = sum(1 for v in CF
            if v['t_rep_combined'] is not None
            and v['t_rep_combined'] >= TRIG)
NANY = sum(1 for v in CTL if v['n_block_trig'] >= 1)
if DRIVE == 1:                     # R1: a count that is not the column's
    NSINGLE = len(CF)
m('RgNCtl', '%d' % len(CF))
m('RgNCtlSingle', '%d' % NSINGLE)
m('RgNCtlComb', '%d' % NCOMB)
# ★★★ RESTATED v4.23.  This clause used to require NCOMB to equal the number
# of controls and NSINGLE to be smaller -- that is THIS ROUND'S ANSWER, not an
# invariant, and a re-measurement that recovered all thirteen in one block
# would have failed the build for being too good.  What must hold whatever the
# data say is structural: a crossing that reaches the trigger in the block the
# table names reaches it in at least one of its blocks; neither count can
# exceed the number of rows; the row count is the count the manuscript
# publishes; and both macros are the counts of the columns as printed, which
# is the defect this replaces -- a text count taken from a column the table
# does not show.  The values themselves are reported, not required.
ck('R1 both published counts are counted off the rows the table prints, and '
   'they respect the orderings that hold by construction: a row reaching the '
   'trigger in the block it names reaches it in some block, and no count '
   'exceeds the number of rows',
   NSINGLE == sum(1 for v in CF if v['t_rep'] is not None
                  and v['t_rep'] >= TRIG)
   and NSINGLE <= NANY <= len(CF) and NCOMB <= len(CF)
   and len(CF) == len(CTL) == int(macro('MkAttrRecur'))
   and all(v['recovering_eb'] for v in CF),
   '%d of %d single-block, %d of %d combined, %d recovered in at least one '
   'block' % (NSINGLE, len(CF), NCOMB, len(CF), NANY))

_below = sorted((v['t_rep'], v['star'], v['chanw_Hz']) for v in CF
                if v['t_rep'] is not None and v['t_rep'] < TRIG)
m('RgCtlLoOne', '%.2f' % _below[0][0])
m('RgCtlLoTwo', '%.2f' % _below[-1][0])
m('RgNCtlBelow', '%d' % len(_below))

# ---- the offsets, and what they are made of
# (a) the crossing's own place in the line: the spread of the stellar-frame
#     frequencies of the crossings of one line in one block;
# (b) peak against centroid: where the brightest channel sits relative to the
#     intensity-weighted centroid of the same profile;
# (c) the residual: the centroid's own offset from the predicted cell.
LRB = {}
for r in LPROF['rows']:
    LRB[(r['cid'], r['eb'])] = r


def profile(r, win_kms):
    """velocity offsets, amplitudes and statistics about the predicted cell."""
    k = r['k']
    dvch = C * r['chanw_Hz'] / (r['f_here_GHz'] * 1e9)
    j = list(range(-k, k + 1))
    dv = [x * dvch for x in j]
    amp = r['amp_mJy']
    sig = r['sig_mJy']
    T = [None if (a is None or s is None) else a / s for a, s in zip(amp, sig)]
    keep = [i for i in range(len(j)) if abs(dv[i]) <= win_kms
            and amp[i] is not None]
    return j, dv, amp, sig, T, keep, dvch


CEN = []
for r in LPROF['rows']:
    j, dv, amp, sig, T, keep, dvch = profile(r, 2.0)
    if not keep:
        continue
    tmax = max(T[i] for i in keep)
    w = [max(amp[i], 0.0) for i in keep]
    if sum(w) <= 0:
        continue
    cen = sum(dv[i] * x for i, x in zip(keep, w)) / sum(w)
    amax = max(amp[i] for i in keep)
    ipk = max(keep, key=lambda i: amp[i])
    half = [i for i in keep if amp[i] > 0.5 * amax]
    CEN.append(dict(cid=r['cid'], eb=r['eb'], star=r['star'],
                    chanw=r['chanw_Hz'], dvch=dvch, tmax=tmax,
                    t_cell=T[j.index(0)], cen=cen, peak=dv[ipk],
                    fwhm=(max(dv[i] for i in half)
                          - min(dv[i] for i in half)) if half else None))
# the registration residual is measured only where the line is actually
# detected in that block: a centroid of noise is not a measurement of
# registration.  The threshold is the paper's own trigger.
DET = [x for x in CEN if x['tmax'] >= TRIG]
if DRIVE == 2:                     # R2: a residual measured on noise
    DET = CEN
RES = [abs(x['cen']) for x in DET]
PKC = [abs(x['peak'] - x['cen']) for x in DET]
FW = [x['fwhm'] for x in DET if x['fwhm']]
DVREG = max(RES)
WORST = max(DET, key=lambda x: abs(x['cen']))
m('RgCenNBlock', '%d' % len(DET))
m('RgCenMaxKms', '%.2f' % DVREG)
m('RgCenMedKms', '%.2f' % med(RES))
m('RgCenWorstStar', tname(WORST['star']))
m('RgPkCenMaxKms', '%.2f' % max(PKC))
m('RgFwhmLoKms', '%.1f' % min(FW))
m('RgFwhmHiKms', '%.1f' % max(FW))
ck('R2 the registration residual is measured as the stellar-frame centroid '
   'of a real recurring line read in every block that detects it, it is a '
   'velocity rather than a number of channels, and it is smaller than the '
   'width of the lines it is measured on -- so it bounds the registration '
   'rather than the line',
   len(DET) > 1 and DVREG < min(FW) and all(x['tmax'] >= TRIG for x in DET),
   'residual <= %.2f km/s (median %.2f) over %d block readings of %d; the '
   'lines are %.1f-%.1f km/s wide; peak against centroid reaches %.2f km/s'
   % (DVREG, med(RES), len(DET), len(CEN), min(FW), max(FW), max(PKC)))

# the Delta c column of the control table, in channels and in velocity
OFF = [(abs(v['dchan']), abs(v['dkms']), v['chanw_Hz'], v['star'])
       for v in CF if v['dchan'] is not None]
OFFBIG = max(OFF)
m('RgOffMaxCh', '%.0f' % OFFBIG[0])
m('RgOffMaxKms', '%.2f' % OFFBIG[1])
m('RgOffMaxChanKHz', '%.1f' % (OFFBIG[2] / 1e3))
m('RgOffMedKms', '%.2f' % med([x[1] for x in OFF]))
ck('R3 the largest offset in the control table is tens of channels but a '
   'fraction of a km/s, it occurs in the finest channels of the set, and it '
   'is smaller than the lines those blocks resolve -- so the column measures '
   'the line and the channel width, not the registration',
   OFFBIG[0] > 10.0 and OFFBIG[1] < max(FW)
   and OFFBIG[2] == min(x[2] for x in OFF),
   'largest %.0f channels = %.2f km/s in %.1f kHz channels; median %.2f '
   'km/s; the lines are up to %.1f km/s wide'
   % (OFFBIG[0], OFFBIG[1], OFFBIG[2] / 1e3, med([x[1] for x in OFF]),
      max(FW)))

# ---- WHICH ROWS TEST THE REGISTRATION OF AN UNRESOLVED CARRIER, AND WHICH
#      ONLY THE FRAME CORRECTION.  The recurrence test reads one channel, so
#      the control tests that reading to a fraction of a channel only where
#      the line it recovers is itself confined to about one channel.  Where
#      the line is resolved across many channels, a cell predicted anywhere
#      inside it is inside the emission, and the row then tests the frame
#      correction to the width of the line and no better.  The division is
#      measured, line by line and block by block -- the full width at half
#      maximum of the profile in that block, in units of that block's own
#      channel -- and not asserted of a star.
_CENK = {(x['cid'], x['eb']): x for x in CEN}
_CIDOF = {'%s|%.6f' % (v['eb'], v['freq_GHz']): v['cid'] for v in D2.values()}
_PB = LR['per_block']
REGROW = []
for v in CF:
    _c = _CIDOF.get('%s|%.6f' % (v['eb'], v['freq']))
    x = _CENK.get((_c, v['recovering_eb']))
    if x is None or not x['fwhm'] or v['dchan'] is None:
        continue
    REGROW.append(dict(star=v['star'], eb=v['eb'], rec=v['recovering_eb'],
                       dch=abs(v['dchan']), fwhm_ch=x['fwhm'] / x['dvch'],
                       dkms=abs(v['dkms']) if v.get('dkms') is not None
                       else None,
                       trep=v['t_rep']))

# ★★★★ WHERE THE NUMBER IN THE $T_{\rm rep}$ COLUMN COMES FROM.  This is the
# defect of record: the column was filled from the frozen read-out's reading
# in the STRONGEST recovering block while the row named the strongest block
# the confirmation criterion admits, and for five rows those are different
# blocks -- so four rows printed a single cell above the maximum of the
# window the row names, which cannot happen.  Both quantities are real; the
# row was not.  The clause ties each printed reading to the read-out's own
# record FOR THE BLOCK THE ROW NAMES, bit for bit.
_PROV, _provbad = [], []
for v in CF:
    _c = _CIDOF.get('%s|%.6f' % (v['eb'], v['freq']))
    _hit = [p for p in _PB.get(_c, []) if p['eb'] == v['recovering_eb']]
    _tr, _dc = v['t_rep'], v['dchan']
    if DRIVE == 12:                # R13: the column the referee read
        _q = D2.get('%s|%.6f' % (v['eb'], v['freq']), {})
        _tr, _dc = _q.get('T_rep'), _q.get('dchan')
    _PROV.append((v['eb'], v['recovering_eb'], _tr))
    if (not _hit or _tr is None
            or abs(_hit[0]['T'] - _tr) > 1e-12
            or _dc is None or abs(_hit[0]['dch'] - _dc) > 1e-12):
        _provbad.append((v['eb'], v['recovering_eb']))
ck('R13 every reading the table prints is the frozen read-out\'s own reading '
   'in the block that row names -- not in some other recovering block -- '
   'bit for bit, in the statistic and in the registration alike',
   not _provbad and len(_PROV) == len(CF),
   '%d rows, %d read in a block they do not name %s'
   % (len(_PROV), len(_provbad), _provbad[:2] or ''))

if DRIVE == 13:                    # R14: a resolved line counted as a probe
    REGROW = [dict(r, fwhm_ch=1.0) for r in REGROW]
UNRES = [r for r in REGROW if r['fwhm_ch'] <= 1.0]
RESV = [r for r in REGROW if r['fwhm_ch'] > 1.0]
m('RgRegNRow', '%d' % len(REGROW))
m('RgRegNUnres', '%d' % len(UNRES))
m('RgRegNRes', '%d' % len(RESV))
m('RgRegStar', ', '.join(sorted({tname(r['star']) for r in UNRES})))
m('RgRegMaxCh', '%.2f' % max([r['dch'] for r in UNRES], default=-1.0))
# ★ R2-A8 asked for the registration residual in km/s and the product has
# carried it all along; a channel count is not a velocity until the channel
# width is beside it.
m('RgRegMaxKms', '%.3f' % max([r['dkms'] for r in UNRES
                               if r['dkms'] is not None], default=-1.0))
m('RgResFwhmChMax', '%.0f' % max([r['fwhm_ch'] for r in RESV], default=-1.0))
m('RgCtlDchAbsMed', '%.2f' % med([abs(v['dchan']) for v in CF
                                  if v['dchan'] is not None
                                  and v['t_rep'] >= TRIG]))
m('RgCtlDchMed', signed(med([v['dchan'] for v in CF
                             if v['dchan'] is not None
                             and v['t_rep'] >= TRIG])))
# ★★★ A CLAIM GATE, NOT A VALUE GATE.  The paper says the predicted cell is
# registered to a fraction of a channel.  Only the rows whose line is
# unresolved can say that, and this requires the rows the claim is made about
# to be exactly those, and the registration measured on them to be inside the
# half-channel the reading covers.  If a future re-measurement put it outside,
# the sentence in the paper would be false and this build must stop rather
# than print it.
ck('R14 the half-channel registration of the predicted cell is tested by the '
   'rows whose recovering line is confined to about one channel, and on '
   'those rows the cell lands inside the half-channel the reading covers; '
   'the rows on resolved lines test the frame correction only to the width '
   'of the line',
   bool(UNRES) and bool(RESV)
   and max([r['dch'] for r in UNRES], default=9.9) < 0.5
   and min([r['fwhm_ch'] for r in RESV], default=0.0) > 1.0
   and all(r['trep'] >= TRIG for r in UNRES),
   '%d of %d rows on a line of <= 1 channel (%s), largest |dc| %.2f ch; '
   '%d on resolved lines of up to %.0f channels, largest |dc| %.2f ch'
   % (len(UNRES), len(REGROW), ', '.join(sorted({r['star'] for r in UNRES})),
      max([r['dch'] for r in UNRES], default=-1.0), len(RESV),
      max([r['fwhm_ch'] for r in RESV], default=-1.0),
      max([r['dch'] for r in RESV], default=-1.0)))

# ★★★★ AND A GATE ON THE TYPESET TABLE, BECAUSE THAT IS WHERE THE DEFECT WAS
# VISIBLE.  Every clause upstream of here ran green for two versions while the
# printed table showed a single cell above its own window maximum in four
# rows.  This one parses the fragment the manuscript includes and makes the
# reader's own comparison on the printed digits: T_rep <= T in every row that
# does not declare a second product, and the two counts the text quotes are
# the counts of the printed columns.
_FRAG = open(os.path.join(TREE, 'tab_confirm_r19.tex')).read()
if DRIVE == 14:                    # R15: the fragment the referee read
    _FRAG = _FRAG.replace('& 17.91 & 17.91 &', '& 17.91 & 30.76 &')
_FROWS = []
for _ln in _FRAG.splitlines():
    _cells = [c.strip() for c in _ln.split('&')]
    if len(_cells) != 11 or not _cells[0] or _cells[0].startswith('%'):
        continue
    try:
        _t = float(_cells[7])
    except ValueError:
        continue
    _dag = '\\dagger' in _cells[8]
    _tr = float(re.sub(r'[^0-9.]', '', _cells[8].split('$')[0]))
    _tc = float(_cells[9])
    _FROWS.append((_cells[4], _t, _tr, _tc, _dag))
_fbad = [r for r in _FROWS if r[2] > r[1] and not r[4]]
ck('R15 in the table as typeset, no row prints a single-cell reading above '
   'the maximum of the window it was read in unless it declares the second '
   'product, and the counts the text quotes are the counts of the printed '
   'columns',
   len(_FROWS) == len(CF) and not _fbad
   and sum(1 for r in _FROWS if r[2] >= TRIG) == NSINGLE
   and sum(1 for r in _FROWS if r[3] >= TRIG) == NCOMB,
   '%d rows parsed, %d impossible %s; printed columns give %d single and '
   '%d combined above the trigger against %d and %d quoted'
   % (len(_FROWS), len(_fbad), _fbad[:1] or '',
      sum(1 for r in _FROWS if r[2] >= TRIG),
      sum(1 for r in _FROWS if r[3] >= TRIG), NSINGLE, NCOMB))

# =====================================================================
# 2.  THE REGISTRATION ERROR BUDGET, TERM BY TERM
# =====================================================================
# The computed terms are all of them fractions of a channel, because every
# one of them is a frequency the reading knows to a fraction of a channel.
# The measured residual above is a velocity, and that is the term that grows
# without limit as the channels narrow.
import csv                                                        # noqa: E402
WINOF = {}
for _r in csv.DictReader(open(os.path.join(
        TREE, 'per_target_results_v3.99.csv'))):
    WINOF.setdefault(_r['eb'], []).append(_r)


def window(eb, f):
    for r in WINOF.get(eb, []):
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if lo <= f <= hi:
            return r
    return None


DQKEY = {(r['eb'], round(float(r['freq']), 6)) for r in LED if r.get('dq')}


def blocks(v):
    """The block list the published depth is formed over: every covering
    repeat block whose weights are not the flagged pathology.  Round 700's
    own selection, so the set re-derived here cannot drift from the published
    one."""
    return [b for b in (v.get('blocks') or [])
            if not b.get('bad_weight_product')]


ROWS = []
for cid, v in sorted(REC.items()):
    if v['status'] != 'ok':
        continue
    key = '%s|%.6f' % (v['eb'], float(v['freq_GHz']))
    q = RCOL.get(key) or {}
    d = v.get('discovery') or {}
    if not blocks(v) or q.get('T_pers') is None or not d.get('amp_mJy'):
        continue
    if (v['eb'], round(float(v['freq_GHz']), 6)) in DQKEY:
        continue
    w = window(v['eb'], float(v['freq_GHz']))
    dwell = float(d['t_end_mjdsec']) - float(d['t_start_mjdsec'])
    chanw = float(w['chanw_Hz']) if w else float(d['chanw_Hz'])
    if w and w['n_drift_trials']:
        step = 2.0 * float(w['drift_max_Hz_s']) \
            / (int(w['n_drift_trials']) - 1)
    else:
        step = chanw / (2.0 * dwell)
    bl = blocks(v)
    near = min(bl, key=lambda z: abs(float(z['sep_from_discovery_h'])))
    far = max(bl, key=lambda z: abs(float(z['sep_from_discovery_h'])))
    # the frame transform's sensitivity to the systemic velocity: the SAME
    # v_sys is removed at the discovery epoch and re-applied at the repeat, so
    # it cancels to first order and what survives is second order in v/c.
    vd = float(d['v_corr_kms'])
    vsys_ch = 0.0
    for b in bl:
        vh = float(b['v_corr_kms'][0]) if isinstance(b['v_corr_kms'], list) \
            else float(b['v_corr_kms'])
        vsys_ch = max(vsys_ch, abs(float(v['freq_GHz']) * 1e9
                                   * (vh - (vd[0] if isinstance(vd, list)
                                            else vd)) / C ** 2) / chanw)
    ROWS.append(dict(
        cid=cid, star=v['star'], display=v['display'], eb=v['eb'],
        freq=float(v['freq_GHz']), chanw=chanw, step=step, dwell=dwell,
        drift=abs(float(d['drift_Hz_s'])),
        tstar=float(v['tstar']), tpers=float(q['T_pers']),
        trep=float(q['T_rep']), f5=float(q['f5']),
        ptrig=float(q['p_conf_trig']),
        dvch=C * chanw / (float(v['freq_GHz']) * 1e9),
        gap_near=abs(float(near['sep_from_discovery_h'])) * 3600.0,
        # the longest baseline is the published one, out of the depth record,
        # not re-derived from the block list: round 700 quotes `dt_max_d` and
        # a second derivation of one quantity is how two numbers for it get
        # into a paper.
        gap_far=float(q['dt_max_d']) * 86400.0,
        near_eb=near['eb'], far_eb=far['eb'],
        vsys_ch=vsys_ch, nblock=len(bl), key=key))
NQ = len(ROWS)
if DRIVE == 3:                     # R4: a crossing silently lost
    ROWS = ROWS[:-1]
    NQ = len(ROWS)
m('RgNCross', '%d' % NQ)
ck('R4 the set re-derived here is the published set of quoted exclusions, '
   "and it is round 120's own count rather than a count of my own",
   NQ == int(macro('RcNExcl')),
   '%d against %s' % (NQ, macro('RcNExcl')))

# the computed terms, in channels
GRID = 0.5                        # the predicted cell is a rounded channel
DISC = 0.5                        # so is the discovery channel
_drift_ch = [0.5 * r['step'] * r['dwell'] / r['chanw'] for r in ROWS]
_bary_ch = [1e-3 / C * r['freq'] * 1e9 / r['chanw'] for r in ROWS]
_budget = [math.sqrt(GRID ** 2 + DISC ** 2 + a ** 2 + b ** 2)
           for a, b in zip(_drift_ch, _bary_ch)]
_budget_kms = [b * r['dvch'] for b, r in zip(_budget, ROWS)]
m('RgDriftWithinChMed', '%.2f' % med(_drift_ch))
m('RgDriftWithinChMax', '%.2f' % max(_drift_ch))
m('RgVsysChMax', '%.3f' % max(r['vsys_ch'] for r in ROWS))
m('RgBaryChMax', '%.3f' % max(_bary_ch))
m('RgBudgetChMed', '%.2f' % med(_budget))
m('RgBudgetChMax', '%.2f' % max(_budget))
m('RgBudgetKmsMed', '%.2f' % med(_budget_kms))
m('RgBudgetKmsMax', '%.2f' % max(_budget_kms))
ck('R5 every computed term of the registration is a fraction of a channel '
   'and the total is of order one channel, in every window, however wide '
   'that channel is -- which is why the budget has to be stated in velocity: '
   'the measured residual is a velocity and exceeds the computed budget '
   'wherever the channels are narrower than it',
   max(_budget) < 2.0 and max(r['vsys_ch'] for r in ROWS) < 0.1
   and max(_bary_ch) < 0.1
   and DVREG > min(_budget_kms),
   'computed %.2f-%.2f channels = %.2f-%.2f km/s; the systemic-velocity term '
   'reaches %.3f channel and the ephemeris term %.3f; the measured residual '
   'is %.2f km/s'
   % (min(_budget), max(_budget), min(_budget_kms), max(_budget_kms),
      max(r['vsys_ch'] for r in ROWS), max(_bary_ch), DVREG))

# =====================================================================
# 3.  THE EXCLUSIONS AT A TOLERANCE MATCHED TO THE MEASURED RESIDUAL
# =====================================================================
# The tolerance is adopted in VELOCITY, because that is what the residual is.
# Each crossing's covering blocks are read on a common velocity grid whose
# step is the finest channel among them, every block contributing the channel
# nearest each grid point; the depth is the WORST cell of the grid, because a
# carrier could have returned at any of them, and the threshold is raised so
# that the false-alarm probability over the grid equals the single cell's.
TOL = DVREG
if DRIVE == 4:                     # R6: a tolerance below the residual
    TOL = 0.5 * DVREG
P1 = 1.0 - phi(TRIG)


def thr(n):
    """The threshold at which n independent readings have the same false-alarm
    probability as one reading at the trigger."""
    if n <= 1:
        return TRIG
    return iphi(phi(TRIG) ** (1.0 / n))


GATE = []
for r in ROWS:
    v = REC[r['cid']]
    bl = [PR[(r['cid'], b['stem'])] for b in blocks(v)]
    S = float(v['discovery']['amp_mJy'])
    fine = min(C * b['chanw_Hz'] / (b['f_here_GHz'] * 1e9) for b in bl)
    # THE TOLERANCE, in one rule: the larger of the measured registration
    # residual and one channel of the finest covering block, the second
    # clause because the computed budget is three quarters of a channel and
    # no reading can be registered more finely than the grid it is read on.
    kk = max(1, int(math.floor(TOL / fine)))
    grid = [i * fine for i in range(-kk, kk + 1)]
    best = None
    for gv in grid:
        num = 0.0
        den = 0.0
        for b in bl:
            dvch = C * b['chanw_Hz'] / (b['f_here_GHz'] * 1e9)
            jj = int(round(gv / dvch))
            if abs(jj) > b['k']:
                continue
            a = b['amp_mJy'][b['k'] + jj]
            s = b['sig_mJy'][b['k'] + jj]
            if a is None or s is None:
                continue
            num += a / s ** 2
            den += 1.0 / s ** 2
        if den <= 0:
            continue
        sbar = 1.0 / math.sqrt(den)
        abar = num / den
        z = thr(len(grid))
        f = (abar / sbar + z) / (S / sbar)
        if abs(gv) < 1e-12:
            GATE.append((r['cid'], abar / sbar, r['trep'],
                         S / sbar, r['tpers']))
            r['trep0'] = abar / sbar
            r['tpers0'] = S / sbar
            r['f50'] = (abar / sbar + TRIG) / (S / sbar)
        if best is None or f > best['f']:
            best = dict(f=f, dv=gv, trep=abar / sbar, tpers=S / sbar, z=z)
    r['ntrial'] = len(grid)
    r['ktol'] = kk
    r['z'] = best['z']
    r['f5tol'] = best['f']
    r['treptol'] = best['trep']
    r['dvtol'] = best['dv']
    r['ptrigtol'] = phi(TRIG * r['tpers'] / r['tstar'] - best['z'])
if DRIVE == 5:                     # R7: a widened depth DEEPER than the cell
    ROWS[0]['f5tol'] = 0.5 * ROWS[0]['f5']
m('RgTolKms', '%.2f' % TOL)
m('RgTolChMax', '%d' % max(r['ktol'] for r in ROWS))
m('RgNTrialMax', '%d' % max(r['ntrial'] for r in ROWS))
m('RgThrMax', '%.2f' % max(r['z'] for r in ROWS))
m('RgFracMed', '%.2f' % med([r['f5tol'] for r in ROWS]))
m('RgFracMin', '%.3f' % min(r['f5tol'] for r in ROWS))
VACT = [r for r in ROWS if r['f5tol'] >= 1.0]
UNTT = [r for r in ROWS if r['ptrigtol'] < POWER]
UNTP = [r for r in ROWS if r['ptrig'] < POWER]
m('RgNVac', '%d' % len(VACT))
m('RgNUnt', '%d' % len(UNTT))
m('RgNExcl', '%d' % (NQ - len(UNTT)))
_moved = sorted(set(x['cid'] for x in UNTT) - set(x['cid'] for x in UNTP))
m('RgNMoved', '%d' % len(_moved))
ck('R6a the central cell of the widened grid IS the published reading: the '
   'combination at zero offset reproduces each crossing\'s own $T_{\\rm rep}$ '
   'and $T_{\\rm pers}$, so the widening is measured against the published '
   'test and not against a re-implementation of it',
   len(GATE) == NQ
   and max(abs(a - b) for _, a, b, _c, _d in GATE) < 0.005
   and max(abs(c - d) for _, _a, _b, c, d in GATE) < 0.05,
   '%d crossings; worst T_rep difference %.4f, worst T_pers difference %.3f '
   '(both published rounded)'
   % (len(GATE), max(abs(a - b) for _, a, b, _c, _d in GATE),
      max(abs(c - d) for _, _a, _b, c, d in GATE)))
ck('R6 the tolerance is not smaller than the registration residual measured '
   'on real lines nor than one channel of the finest covering block, and it '
   'is set in velocity: in channels it is the single neighbouring cell where '
   'channels are wide and several cells where they are narrow',
   TOL >= DVREG and max(r['ktol'] for r in ROWS) > 1
   and min(r['ktol'] for r in ROWS) == 1
   and all(r['ktol'] * r['dvch'] >= min(TOL, r['dvch']) - 1e-9
           for r in ROWS),
   'tolerance +-%.2f km/s = %d to %d channels (%d to %d cells read); the '
   'measured residual is %.2f km/s'
   % (TOL, min(r['ktol'] for r in ROWS), max(r['ktol'] for r in ROWS),
      min(r['ntrial'] for r in ROWS),
      max(r['ntrial'] for r in ROWS), DVREG))
ck('R7 widening the cell can only weaken an exclusion, never deepen one: the '
   'maximum over a set that contains the predicted cell is never below the '
   'reading at it, and the threshold never falls below the trigger.  An '
   'INVARIANT of the construction, not a property of these data',
   all(r['f5tol'] >= r['f50'] - 1e-12 for r in ROWS)
   and all(r['z'] >= TRIG for r in ROWS)
   and all(r['treptol'] >= r['trep0'] - 1e-12 for r in ROWS),
   'median depth %.2f against the published %s, deepest %.3f against %s; '
   '%d of %d then rule out nothing and %d are untested at the %g level '
   '(%d more than the single cell)'
   % (med([r['f5tol'] for r in ROWS]), macro('RcFracMed'),
      min(r['f5tol'] for r in ROWS), macro('RcFracMin'), len(VACT), NQ,
      len(UNTT), POWER, len(_moved)))
# ★ THE FREQUENCY PRINTED IN THIS SECTION IS THE STELLAR-FRAME ONE, which is
# what every other round prints for these crossings; the topocentric value
# differs by tens of MHz and printing it here is a defect this build has made
# before.  The join is on the ledger's own (block, frequency) key.
LFS0 = {(r['eb'], round(float(r['freq']), 6)): r for r in LED}
for _r in ROWS:
    _r['fstar'] = float(LFS0[(_r['eb'], round(_r['freq'], 6))]
                        ['frame']['f_stellar'])


def flist(rs):
    return ', '.join('%s at %.2f\\,GHz' % (tname(r['display']), r['fstar'])
                     for r in sorted(rs, key=lambda r: r['fstar']))


MEASUNT = set(jload('hostinj_r19.json')['below_power_meas'])
_vacset = {r['cid'] for r in VACT}
if DRIVE == 9:                     # R7b: a vacuous exclusion NOT untested
    _vacset = _vacset | ({r['cid'] for r in ROWS} - MEASUNT)
ck('R7b every crossing whose exclusion rules out nothing at the matched '
   'tolerance is already among those the MEASURED recovery probability '
   'reports as untested rather than excluded, so the widening moves no '
   'disposition.  A SUBSET and not an identity: the measured untested set is '
   'the larger, and it is round 870\'s, not recomputed here',
   _vacset <= MEASUNT and len(_vacset) > 0
   and len(MEASUNT) == int(macro('HjNPowerLo')),
   '%d rule out nothing (%s) of the %d measured untested (%s)'
   % (len(_vacset), ', '.join(sorted(_vacset)), len(MEASUNT),
      ', '.join(sorted(MEASUNT))))
m('RgVacList', flist(VACT) if VACT else 'none')
m('RgMovedList', flist([r for r in ROWS if r['cid'] in _moved])
  if _moved else 'none')

# =====================================================================
# 4.  ONE DRIFT MODEL, AND THE TWO DISPLACEMENTS IT SEPARATES
# =====================================================================
# (a) THE READING'S OWN MODEL: the cell is registered by the frame transform,
#     and the fitted drift is used only to de-drift WITHIN each observation.
#     The drift's uncertainty therefore displaces the cell by half a grid step
#     across one observation and no further, however long the gap.
# (b) THE LIMITATION, which belongs to a DIFFERENT model: a carrier that keeps
#     drifting at the fitted rate is not in that cell at all after the gap --
#     it leaves it in seconds.  The quantity to quote for that model is the
#     time the carrier stays in the cell, not an error budget.
_within = [0.5 * r['step'] * r['dwell'] / r['chanw'] for r in ROWS]
_leave = [0.5 * r['chanw'] / r['drift'] for r in ROWS if r['drift'] > 0]
_walk = [r['drift'] * r['gap_near'] / r['chanw'] for r in ROWS]
WI = max(range(len(ROWS)), key=lambda i: _within[i])
WA = max(range(len(ROWS)), key=lambda i: _walk[i])
if DRIVE == 6:                     # R8: the two models' numbers interchanged
    _within = _walk
m('RgWithinChMed', '%.2f' % med(_within))
m('RgWithinChMax', '%.2f' % max(_within))
m('RgWithinStar', tname(ROWS[WI]['display']))
m('RgWithinFreq', '%.2f' % ROWS[WI]['freq'])
m('RgWithinChanKHz', '%.0f' % (ROWS[WI]['chanw'] / 1e3))
m('RgWithinDwellMin', '%.0f' % (ROWS[WI]['dwell'] / 60.0))
m('RgLeaveSecMed', '%.0f' % med(_leave))
m('RgWalkChMed', '%.0f' % med(_walk))
m('RgWalkStar', tname(ROWS[WA]['display']))
_wm, _we = ('%.1f' % (max(_walk) / 10.0 ** int(math.floor(math.log10(
    max(_walk)))))), '%d' % int(math.floor(math.log10(max(_walk))))
m('RgWalkChMax', _wm)
m('RgWalkChMaxExp', _we)
m('RgWalkGapD', '%.0f' % (ROWS[WA]['gap_near'] / 86400.0))
m('RgWalkChanKHz', '%.0f' % (ROWS[WA]['chanw'] / 1e3))
# the phase fraction, which is the one quantity referee 2's first major asks
# for and the one place this section can concede it without a prior.  It is
# arithmetic on two numbers the paper already prints -- the interval the
# single cell permits and the velocity excursion an orbit at the grid's own
# ceiling can produce -- under a uniform phase, and it is stated as an order
# of magnitude because that is all a uniform phase supports.  It is NOT a
# probability that any particular carrier recurs: that would need a
# population of orbits, which is a prior and not a measurement.
_dvlo, _dvhi = float(macro('RqDvLo')), float(macro('RqDvHi'))
_vexc = float(macro('EcVexcKms'))
_plo, _phi = _dvlo / _vexc, _dvhi / _vexc
if DRIVE == 11:                    # R8b: a fraction that is not a fraction
    _phi = 1.5
m('RgPhaseExpLo', '%d' % int(math.floor(math.log10(_plo))))
m('RgPhaseExpHi', '%d' % int(math.floor(math.log10(_phi))))
ck('R8b the phase fraction is the interval the reading permits divided by '
   'the excursion the searched ceiling allows, both of them already '
   'published, and it is far below one -- so a periodic carrier caught at '
   'the matching phase is a small fraction of the orbits the ceiling admits',
   0.0 < _plo <= _phi < 1e-2
   and int(math.floor(math.log10(_phi))) <= -3,
   'half-channel interval +-%.2f to %.2f km/s against +-%.0f km/s of '
   'excursion: %.1e to %.1e, i.e. 10^%d to 10^%d'
   % (_dvlo, _dvhi, _vexc, _plo, _phi,
      int(math.floor(math.log10(_plo))), int(math.floor(math.log10(_phi)))))

ck('R8 the two models are separated and each number belongs to one of them: '
   'under the reading\'s own model the drift uncertainty displaces the cell '
   'by a fraction of a channel across one observation, while a carrier that '
   'keeps drifting leaves the cell within a minute and walks orders of '
   'magnitude further across the gap than any tolerance could cover',
   max(_within) < 1.0 and med(_leave) < 600.0
   and med(_walk) > 100.0 * max(_within),
   'within one observation %.2f-%.2f channel (%.2f in the median); a '
   'drifting carrier leaves the cell in %.0f s and walks a median %.2g '
   'channels to the nearest covering block'
   % (min(_within), max(_within), med(_within), med(_leave), med(_walk)))

# the number the manuscript quotes as "648 over the longest baseline" is the
# MEDIAN of per-crossing values each taken at its own longest baseline, which
# is not a baseline of anything.  Both are computed here so the sentence can
# name what it prints.
_regfar = [0.5 * r['step'] * r['gap_far'] / r['chanw'] for r in ROWS]
_regnear = [0.5 * r['step'] * r['gap_near'] / r['chanw'] for r in ROWS]
FA = max(range(len(ROWS)), key=lambda i: _regfar[i])
m('RgRegFarMed', '%.0f' % med(_regfar))
m('RgRegFarMax', '%.0f' % max(_regfar))
m('RgRegFarStar', tname(ROWS[FA]['display']))
m('RgRegFarChanKHz', '%.0f' % (ROWS[FA]['chanw'] / 1e3))
m('RgRegFarDays', '%.0f' % (ROWS[FA]['gap_far'] / 86400.0))
ck('R9 the published figure for the carried-drift displacement at the '
   'longest baseline is a MEDIAN over the crossings and not the largest '
   'value, and the largest is an order of magnitude bigger -- so a sentence '
   'that calls the median an extreme is quoting neither',
   abs(med(_regfar) - float(macro('ZtRegChanFarMed'))) < 1.0
   and max(_regfar) > 5.0 * med(_regfar),
   'median %.0f channels (the published %s), largest %.0f at %s in %.0f kHz '
   'channels over %.0f d'
   % (med(_regfar), macro('ZtRegChanFarMed'), max(_regfar),
      ROWS[FA]['star'], ROWS[FA]['chanw'] / 1e3,
      ROWS[FA]['gap_far'] / 86400.0))

# =====================================================================
# 5.  THE DEPTHS OVER SEPARATED BLOCKS ALONE (referee 2, 8)
# =====================================================================
for r in ROWS:
    v = REC[r['cid']]
    S = float(v['discovery']['amp_mJy'])
    sep = [b for b in blocks(v) if EP.confirms(v['eb'], b['eb'])]
    if DRIVE == 7:                 # R11: a "separated-only" column that is
        sep = blocks(v)            #      silently every block after all
    if DRIVE == 10:                # R10: a criterion that ADDS coverage the
        sep = blocks(v) + sep[:1]  #      depth was never formed over
    r['nsep'] = len(sep)
    if not sep:
        r['f5sep'] = None
        r['ptrigsep'] = None
        r['trepsep'] = None
        r['tperssep'] = None
        continue
    den = sum(1.0 / float(b['sig_mJy']) ** 2 for b in sep)
    sbar = 1.0 / math.sqrt(den)
    abar = sum(float(b['amp_mJy']) / float(b['sig_mJy']) ** 2
               for b in sep) / den
    r['trepsep'] = abar / sbar
    r['tperssep'] = S / sbar
    r['f5sep'] = (abar / sbar + TRIG) / (S / sbar)
    r['ptrigsep'] = phi(TRIG * (S / sbar) / r['tstar'] - TRIG)
SEP = [r for r in ROWS if r['f5sep'] is not None]
NOSEP = [r for r in ROWS if r['f5sep'] is None]
SEPV = [r for r in SEP if r['f5sep'] >= 1.0]
SEPP = [r for r in SEP if r['ptrigsep'] >= POWER]
m('SpNSep', '%d' % len(SEP))
m('SpFracMed', '%.2f' % med([r['f5sep'] for r in SEP]))
m('SpFracMin', '%.3f' % min(r['f5sep'] for r in SEP))
m('SpFracMax', '%.2f' % max(r['f5sep'] for r in SEP))
m('SpNPower', '%d' % len(SEPP))
#: ★★ A LIMIT AT OR ABOVE ONE EXCLUDES NOTHING, so the count that carries the
#: result is the complement and not the median: `SpNVac` was computed and
#: never printed, which left the median standing beside a maximum of 11.79
#: as though the range were a range of exclusions.  Both counts are emitted
#: and the section prints both.
m('SpNVac', '%d' % len(SEPV))
m('SpNExcl', '%d' % (len(SEP) - len(SEPV)))
m('SpNoSepList', flist(NOSEP) if NOSEP else 'none')
ck('R10b the separated-only depths partition into the ones that rule out an '
   'amplitude below the discovery amplitude and the ones that rule out '
   'nothing, so neither count can be quoted as the other and the median is '
   'never offered as a bound',
   len(SEPP) <= len(SEP) and len(SEP) - len(SEPV) + len(SEPV) == len(SEP)
   and len(SEPV) > 0 and len(SEP) - len(SEPV) > 0
   and all(r['f5sep'] < 1.0 for r in SEP if r not in SEPV)
   and all(r['f5sep'] >= 1.0 for r in SEPV),
   '%d of %d below one, %d at or above it (%s); median %.2f, largest %.2f'
   % (len(SEP) - len(SEPV), len(SEP), len(SEPV),
      ', '.join('%s %.2f' % (r['star'], r['f5sep']) for r in SEPV),
      med([r['f5sep'] for r in SEP]), max(r['f5sep'] for r in SEP)))
ck('R10 the separated-only reading uses the paper\'s own confirmation '
   'criterion, through the one implementation of it, and it can only DISCARD '
   'blocks -- so the sensitivity it reaches is never better than the '
   'sensitivity over every block, which is the invariant, while the depth '
   'itself may move either way because the amplitude it averages changes too',
   all(r['nsep'] <= r['nblock'] for r in ROWS)
   and all(r['tperssep'] <= r['tpers'] + 0.05 for r in SEP)
   and len(SEP) + len(NOSEP) == NQ and len(SEP) > 0
   and {r['cid'] for r in NOSEP} == {z['cid'] for z in jload(
       'confirm_r20.json')['same_session_only']},
   '%d of %d keep a separated block (%d blocks of %d in all); median depth '
   '%.2f against %s over every block; %d still reach %g recovery; %d rule '
   'out nothing; %d have no separated coverage, the same set round 910 counts'
   % (len(SEP), NQ, sum(r['nsep'] for r in ROWS),
      sum(r['nblock'] for r in ROWS), med([r['f5sep'] for r in SEP]),
      macro('RcFracMed'), len(SEPP), POWER, len(SEPV), len(NOSEP)))
ck('R11 the published claim that the exclusions do not rest on unseparated '
   'coverage is about EXISTENCE and says nothing about depth, which is the '
   "referee's point: separated blocks alone carry strictly less inverse "
   'variance, fewer crossings reach the declared recovery level, and some '
   'crossings lose their coverage altogether',
   sum(1 for r in SEP if r['tperssep'] < r['tpers'] - 0.05) > 0
   and len(SEPP) < int(macro('RqNPowerHi'))
   and len(NOSEP) > 0,
   'separated-only median %.2f (%.3f-%.2f), %d reaching %g against the '
   'published %s over every block; %d crossings lose sensitivity and %d lose '
   'coverage entirely'
   % (med([r['f5sep'] for r in SEP]), min(r['f5sep'] for r in SEP),
      max(r['f5sep'] for r in SEP), len(SEPP), POWER, macro('RqNPowerHi'),
      sum(1 for r in SEP if r['tperssep'] < r['tpers'] - 0.05), len(NOSEP)))

# the two crossings Table 6 follows, by the ledger's own rank flag
for r in ROWS:
    r['screen'] = bool(LFS0[(r['eb'], round(r['freq'], 6))]['screen'])
SCR = sorted([r for r in ROWS if r['screen']], key=lambda r: -r['tstar'])
if DRIVE == 8:                     # R12: the pair in the other order
    SCR = SCR[::-1]
for tag, r in zip(('Sx', 'Cp'), SCR):
    m('Sp%sFracSep' % tag, '%.2f' % r['f5sep'] if r['f5sep'] is not None
      else 'n/r')
    m('Sp%sNSep' % tag, '%d' % r['nsep'])
    m('Sp%sFracTol' % tag, '%.2f' % r['f5tol'])
    m('Sp%sTolCh' % tag, '%d' % r['ktol'])
ck('R12 the two crossings the table follows are the ledger\'s own '
   'rank-leading pair, in the order another round prints them in and at the '
   'stellar-frame frequencies it prints',
   len(SCR) == 2
   and ['%.4f' % r['fstar'] for r in SCR] == [macro('RqFreqSx'),
                                              macro('RqFreqCp')],
   '%s at %s against %s'
   % ([r['star'] for r in SCR], ['%.4f' % r['fstar'] for r in SCR],
      [macro('RqFreqSx'), macro('RqFreqCp')]))

# ------------------------------------------------------------------ output
json.dump(dict(generator=os.path.basename(__file__), round=ROUND, drive=DRIVE,
               tolerance_kms=TOL, trigger=TRIG, power=POWER,
               registration=dict(residual_kms=DVREG, median_kms=med(RES),
                                 n_block=len(DET),
                                 peak_minus_centroid_kms=max(PKC),
                                 fwhm_kms=[min(FW), max(FW)],
                                 computed_channels=[min(_budget),
                                                    max(_budget)],
                                 blocks=CEN),
               controls=dict(n=len(CTL), n_single=NSINGLE, n_combined=NCOMB,
                             below=[list(x) for x in _below]),
               crossings=ROWS),
          open(OUTJ, 'w'), indent=1, default=str)
os.makedirs(os.path.dirname(OUTC), exist_ok=True)
json.dump({r['key']: dict(f5_tol=round(r['f5tol'], 4),
                          k_tol=r['ktol'], n_trial=r['ntrial'],
                          thr_tol=round(r['z'], 3),
                          p_trig_tol=round(r['ptrigtol'], 4),
                          n_sep=r['nsep'],
                          f5_sep=(round(r['f5sep'], 4)
                                  if r['f5sep'] is not None else None),
                          T_rep_sep=(round(r['trepsep'], 3)
                                     if r['trepsep'] is not None else None),
                          T_pers_sep=(round(r['tperssep'], 2)
                                      if r['tperssep'] is not None else None),
                          p_trig_sep=(round(r['ptrigsep'], 4)
                                      if r['ptrigsep'] is not None else None))
           for r in ROWS}, open(OUTC, 'w'), indent=1)

# ------------------------------------------------------- the ancillary file
# ★ R2-8 ASKS FOR A COLUMN IN THE LEDGER, AND THE LEDGER CANNOT CARRY ONE
# HERE: `si_ledger.txt` is written by `ledger_v410.py`'s second pass, which
# runs before the recurrence chain this generator sits at the end of, so
# feeding it from here would be a cycle in the build and not a column.  The
# per-crossing values therefore ship as an ancillary file of their own, keyed
# on the same (star, block, delivered frequency) triple the ledger is keyed
# on, so the two join row for row.  Same conventions as `si_ledger.txt`: tab
# separated, one row per crossing that carries an exclusion, an empty field is
# a value withheld and not a zero, and the columns are described in the file.
SIDOC = [
    ('star', 'star name as in the paper, the same string si_ledger.txt is '
             'keyed on'),
    ('eb', 'ALMA execution block (asdm) identifier of the discovery block'),
    ('nu_topo_GHz', 'crossing frequency as delivered by the correlator'),
    ('nu_star_GHz', "the same frequency in the star's rest frame"),
    ('n_rep', 'covering repeat execution blocks the published depth combines'),
    ('n_rep_sep', 'of those, blocks satisfying the confirmation criterion '
                  'against the discovery block: a different observing '
                  'session AND more than one day away'),
    ('T_pers_sep', 'statistic a carrier persisting at the discovery flux '
                   'would give at the predicted cell over those blocks alone '
                   '(empty where there are none)'),
    ('T_rep_sep', 'statistic measured there, at the carried drift'),
    ('f5_sep', 'fraction of the discovery amplitude still excluded at the '
               'trigger over separated blocks alone, (T_rep+5)/T_pers'),
    ('p_trig_sep', 'recovery probability at the trigger amplitude over those '
                   'blocks alone'),
    ('k_tol', 'half-width in channels of the matched registration tolerance, '
              'in channels of the finest covering block'),
    ('n_cell_tol', 'cells read over that tolerance'),
    ('thr_tol', 'threshold at which those cells carry the single cell\'s own '
                'false-alarm probability'),
    ('f5_tol', 'fraction of the discovery amplitude still excluded at the '
               'trigger when the reading is the worst cell of that '
               'tolerance, (T_rep+thr)/T_pers'),
    ('p_trig_tol', 'recovery probability at the trigger amplitude at that '
                   'threshold'),
]


def _f(x, fmt):
    return '' if x is None else fmt % x


#: ★ the deposited file promises a join and must deliver it.  `cleanregen`
#: compares this file with its own regeneration, so a star column that is
#: consistently WRONG passes that gate for ever; only this check can see it.
_LK = {(_sname(_l['display']), _l['eb'], '%.6f' % _l['freq']) for _l in LED}
_NJ = sum(1 for _r in ROWS
          if (_sname(_r['star']), _r['eb'], '%.6f' % _r['freq']) in _LK)
if DRIVE == 16:
    _NJ = len(ROWS) - 1          # the star column stops joining the ledger
ck('R16 every row of the deposited file resolves the join its own header '
   'documents, on (star, eb, nu_topo_GHz) against the crossing ledger, so a '
   'reader following the header loses no row',
   _NJ == len(ROWS) and len(ROWS) > 0,
   '%d of %d rows join the ledger on the documented key' % (_NJ, len(ROWS)))


with open(os.path.join(HERE, 'si_recur%s.txt' % SFX), 'w') as fh:
    fh.write('# The recurrence depths of the ALMA 40 pc technosignature '
             'search read two further ways: over covering blocks that '
             'satisfy the confirmation criterion alone, and over a cell '
             'tolerance matched to the measured stellar-frame registration '
             'of +-%.2f km/s.\n' % TOL)
    fh.write('# One row per threshold crossing carrying a quoted exclusion, '
             'in the order of the crossing ledger.  Accompanies the arXiv '
             'submission as an ancillary file (anc/), and joins '
             'si_ledger.txt on (star, eb, nu_topo_GHz).\n')
    fh.write('# Tab-separated; an empty field is a value withheld, not a '
             'zero.\n#\n# Columns:\n')
    for _i, (_k, _d) in enumerate(SIDOC, 1):
        fh.write('#  %2d  %-28s %s\n' % (_i, _k, _d))
    fh.write('#\n' + '\t'.join(k for k, _ in SIDOC) + '\n')
    for r in sorted(ROWS, key=lambda r: (_sname(r['star']), r['freq'])):
        vals = [_sname(r['star']), r['eb'],
                '%.6f' % r['freq'], '%.6f' % r['fstar'],
                '%d' % r['nblock'], '%d' % r['nsep'],
                _f(r['tperssep'], '%.2f'), _f(r['trepsep'], '%+.4f'),
                _f(r['f5sep'], '%.4f'), _f(r['ptrigsep'], '%.4f'),
                '%d' % r['ktol'], '%d' % r['ntrial'], '%.3f' % r['z'],
                '%.4f' % r['f5tol'], '%.4f' % r['ptrigtol']]
        assert not any('\t' in v for v in vals), r['cid']
        fh.write('\t'.join(vals) + '\n')
m('RgSiCols', '%d' % len(SIDOC))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by tolrecur_r21.py (round %d) -- do not '
             'hand-edit.\n' % ROUND)
    fh.write('%% The registration of the predicted cell, the exclusions at a '
             'matched tolerance, one drift model, and the depths over '
             'separated blocks alone.\n')
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('\n%-5s %-22s %8s %6s %6s %6s %6s %6s %6s %5s'
      % ('cid', 'star', 'freq', 'f5', 'f5tol', 'ktol', 'f5sep', 'nsep',
         'ptrig', 'pstol'))
for r in sorted(ROWS, key=lambda r: (r['star'], r['freq'])):
    print('%-5s %-22s %8.3f %6.3f %6.3f %6d %6s %6d %6.2f %5.2f'
          % (r['cid'], r['star'][:22], r['freq'], r['f5'], r['f5tol'],
             r['ktol'],
             ('%.3f' % r['f5sep']) if r['f5sep'] is not None else '  n/r',
             r['nsep'], r['ptrig'], r['ptrigtol']))
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
