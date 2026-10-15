#!/usr/bin/env python3
r"""round 230 -> survey_numbers_round230.tex: THE CROSSING POPULATION SPLIT BY
DATA QUALITY, AND THE PHASE-CENTRE TEST OF THE FLAGGED BLOCK.

Two jobs, both forced by the same reading of the same four rows.

(1) THE QUALITY-PASSING POPULATION AND THE FLAGGED BLOCK, SEPARATELY.
    One execution block fails a quality criterion fixed in advance and
    carries four of the survey's threshold crossings.  Reporting it is right;
    pooling it into the headline count is not, because the headline count is
    the one the chance expectation is compared with and the one the abstract
    quotes.  So the split is computed here, from the flag predicate and the
    catalogue, and published as its own set of macros:

        56 raw crossings = 52 in quality-passing data + 4 in the failed block

    with the attribution and rank decomposition of each part.  ★ The two
    partitions of the crossing population -- by search class and by block
    quality -- turn out to coincide exactly, because the failing block holds
    the survey's entire Class B crossing population.  That is a measured
    coincidence and is asserted here, not assumed: if a future block fails
    with Class A windows in it, E1 fires rather than the paper quietly
    reporting one partition under the other's name.

(2) THE PHASE-CENTRE TEST (the referee's own physical suggestion, and it is
    a good one).  An interference feature with no geometric fringe phase --
    an intermediate-frequency spur common to all antennas is the obvious
    case -- does not fringe-track, so it accumulates at the PHASE CENTRE
    rather than at the star.  In the failing block the two are 0.06 arcsec
    apart, so the block cannot test its own hypothesis.  The survey can: the
    star lies more than 4 arcsec off the phase centre in 79 windows, out to
    8.1 arcsec, and the control annulus runs from about 4 to 22 arcsec, so in
    every one of those windows several control positions sit within a
    synthesised beam or two OF THE PHASE CENTRE while the star does not.

    If the excess follows the phase centre, those probes carry it.  The test
    is therefore: in each such window, the mean control statistic within two
    synthesised beams of the phase centre, against the mean over the controls
    AT THE SAME DISTANCE FROM THE STAR but elsewhere in azimuth.  ★ The
    radius match is not decoration.  The phase centre lies at a fixed
    distance from the star, so "near the phase centre" is also "near the
    inner edge of the annulus", and without the match any centrally
    concentrated stellar emission -- beta Pictoris' disc, in four of these
    windows -- would masquerade as a phase-centre excess.  The unmatched
    comparison is computed alongside so the size of that confound is visible.

    Nothing is re-extracted.  The control positions are recoverable exactly:
    the extractor draws them as rr = sqrt(uniform(r_in^2, r_out^2, 512)) then
    th = uniform(0, 2pi, 512) from `default_rng(seed)`, in that order, and the
    released catalogue stores the seed and both radii per window.  The
    per-position statistics are in the frozen export; the star's offset from
    the phase centre, as a VECTOR and not only a magnitude, is in the
    primary-beam audit's own geometry record (l_star, m_star in radians,
    measured from Gaia and the FIELD::PHASE_DIR of each product).

Five assertions, five drives.  `--drive 0` means "no perturbation, but do not
write a path production reads".

Usage:  python3 events_r12.py [--drive N]
"""
import collections
import csv
import json
import math
import os
import re
import statistics as st
import sys

import numpy as np

import dqflag

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 230
RAD_PER_ARCSEC = 1.0 / 206264.806247

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

OUT_NAME = 'survey_numbers_round230%s.tex' % SUF
OUT_PATH = os.path.join(HERE, OUT_NAME)
JSON_PATH = os.path.join(HERE, 'events_r12%s.json' % SUF)

#: the star must be this far off the phase centre for the window to separate
#: the two hypotheses at all.  Fixed here, once, and reported.
OFF_MIN_ARCSEC = 4.0
#: "near the phase centre" and "the same radius from the star", both in
#: synthesised beams of the observing block, with a floor so that a
#: sub-arcsecond 12 m beam cannot make the near-sample empty.
NEAR_BEAMS = 2.0
NEAR_FLOOR_ARCSEC = 2.0

OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-74s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """Read a macro out of the published layer; last definition wins.  Never
    reads this round's own output, so the gate cannot agree with itself."""
    pat = re.compile(r'\\(?:provide|renew|new)command\{?\\%s\}?\{([^}]*)\}'
                     % name)
    got = None
    for f in sorted(os.listdir(HERE)):
        if not (f.startswith('survey_numbers') and f.endswith('.tex')):
            continue
        if f.startswith('survey_numbers_round%d' % ROUND):
            continue
        for mm in pat.finditer(open(os.path.join(HERE, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                got = mm.group(1).strip()
    return got


# ---------------------------------------------------------------- the inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXPORT = json.load(open(os.path.join(
    HERE, 'corrected_export_v399.json')))['rows']
GEOM = json.load(open(os.path.join(HERE, 'pbaudit_v408', 'pbgeom.json')))
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']
LEDGER = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
FIELDFIX = json.load(open(os.path.join(
    HERE, 'r8inputs', 'v409', 'fieldfix_v409.json')))

X = [r for r in CAT if r['crossing'] == 'True']

# =========================================================== (1) THE SPLIT ==
# The flag is the published module's, not a second implementation of it, and
# the block is named by the flag rather than by a remembered name.
FLAGGED_EB = dqflag.flagged_ebs(HERE)
FAILBLOCK = texval('BqFailBlock').replace('\\_', '_')

# A ledger row is in the failed block if its own block is the failing one.
# Keyed on the block, which is what the criterion is about.
QP = [r for r in LEDGER if r['eb'] != FAILBLOCK]
FL = [r for r in LEDGER if r['eb'] == FAILBLOCK]
if DRIVE == 1:
    # the defect itself: pool the two and let the counts be the raw ones
    QP, FL = list(LEDGER), []

QP_ATT = [r for r in QP if r['attributed']]
QP_UN = [r for r in QP if not r['attributed']]
FL_UN = [r for r in FL if not r['attributed']]

# The rank statement, over each part separately, each row judged against the
# control maximum of its OWN extraction -- which is what the ledger now
# carries, and the reason the flagged block's four rows do not appear here.
def _outranks(r):
    return r['rank_ctrl'] is not None and r['tstar'] > float(r['rank_ctrl'])


QP_RANK = [r for r in QP_UN if _outranks(r)]
FL_RANK = [r for r in FL_UN if _outranks(r)]

# ★ E1.  The two partitions coincide, and that is a measurement.
XB_LEDGER = {(r['eb']) for r in LEDGER}
_cls = {}
for r in CAT:
    _cls.setdefault(r['eb'], set()).add(
        'A' if r['resolution_class'] == 'fine' else 'B')
_flag_classes = sorted(_cls.get(FAILBLOCK, set()))
_classB_x = [r for r in X if r['resolution_class'] != 'fine']
if DRIVE == 2:
    _flag_classes = ['A', 'B']
ck('E1 the failing block holds no fine-channel window, so the crossings it '
   'removes are exactly the survey Class B crossings',
   _flag_classes == ['B'] and len(_classB_x) == len(FL)
   and {r['eb'] for r in _classB_x} == {FAILBLOCK},
   'failing block classes %s, %d Class B crossings, %d in the block'
   % (_flag_classes, len(_classB_x), len(FL)))

_nraw = len(LEDGER)
if DRIVE == 3:
    QP_ATT = QP_ATT[:-1]
ck('E2 the split closes on the raw crossing count and on its own '
   'attribution decomposition',
   len(QP) + len(FL) == _nraw and len(QP_ATT) + len(QP_UN) == len(QP),
   '%d + %d against %d; %d + %d against %d'
   % (len(QP), len(FL), _nraw, len(QP_ATT), len(QP_UN), len(QP)))

# ★ E3.  The published rank-flagged count is a macro, so the two must agree
# rather than one of them being re-derived and the other remembered.
_pub_rank = int(texval('NUnattrRankFlagged'))
_pub_un = int(texval('ChnUnattrA'))
_got_rank = len(QP_RANK) + len(FL_RANK)
if DRIVE == 4:
    _got_rank += 1
ck('E3 the number of unattributed crossings outranking every control, '
   'recomputed from each row own extraction, is the published one',
   _got_rank == _pub_rank and len(QP_UN) == _pub_un,
   '%d (%d quality-passing + %d flagged) against the published %d; '
   '%d unattributed against the published %d'
   % (_got_rank, len(QP_RANK), len(FL_RANK), _pub_rank,
      len(QP_UN), _pub_un))

# The flagged block's own star-against-ring numbers, on the extraction its
# tabulated statistic comes from.  This is the quantity the "star-localised
# excess" reading rests on, so it is printed rather than described.
FFB = [r for r in FIELDFIX if r['eb'] == FAILBLOCK]
assert FFB, 'no re-extracted record for the failing block'
_ratios = [r['star_snr'] / r['ctrl_max'] for r in FFB]
_nge = [r['n_ge'] for r in FFB]
# the same ratio formed the way the table used to print it -- a re-extracted
# star statistic over a RELEASED ring maximum -- so the size of the error is
# in the deposit rather than only in the prose.
_relring = {}
for r in X:
    if r['eb'] == FAILBLOCK:
        _relring[round(min(float(r['flo_GHz']), float(r['fhi_GHz'])), 2)] = \
            float(r['ctrl_max_snr'])
_mixed_ratios = [r['star_snr'] / _relring[round(min(r['flo'], r['fhi']), 2)]
                 for r in FFB
                 if round(min(r['flo'], r['fhi']), 2) in _relring]
assert len(_mixed_ratios) == len(FFB), (len(_mixed_ratios), len(FFB))
if DRIVE == 5:
    _ratios = [1.5] + _ratios[1:]
ck('E4 in the failing block not one crossing outranks its own control '
   'ensemble once the ensemble is read from the same extraction as the '
   'statistic', max(_ratios) < 1.0 and min(_nge) >= 1,
   'largest star/ring ratio %.3f, fewest controls above the star %d of %d'
   % (max(_ratios), min(_nge), FFB[0]['n_ctrl']))

m('EvNCrossRaw', '%d' % _nraw)
m('EvNCrossQp', '%d' % len(QP))
m('EvNCrossFlag', '%d' % len(FL))
m('EvNAttrQp', '%d' % len(QP_ATT))
m('EvNUnattrQp', '%d' % len(QP_UN))
m('EvNUnattrFlag', '%d' % len(FL_UN))
m('EvNRankQp', '%d' % len(QP_RANK))
m('EvNRankFlag', '%d' % len(FL_RANK))
m('EvFlagRingRatioHi', '%.2f' % max(_ratios))
m('EvFlagNgeLo', '%d' % min(_nge))
m('EvFlagNgeHi', '%d' % max(_nge))
m('EvFlagTStarHi', '%.1f' % max(r['star_snr'] for r in FFB))
m('EvFlagCtrlAtHi', '%.1f' % max(FFB, key=lambda r: r['star_snr'])['ctrl_max'])
m('EvFlagMixedRatioHi', '%.1f' % max(_mixed_ratios))

# ======================================== (2) THE PHASE-CENTRE TEST ========
# the per-window control vector, keyed min/max on the window edges
def _wkey(eb, band, flo, fhi):
    a, b = float(flo), float(fhi)
    return (eb, str(band), round(min(a, b), 4), round(max(a, b), 4))


CTRL = {}
for e in EXPORT:
    if e.get('ctrl_all'):
        CTRL[_wkey(e['eb'], e['band'], e['flo'], e['fhi'])] = e['ctrl_all']

# the star's offset from the phase centre, as a vector, per (block, window).
# One record per spectral window; joined by frequency containment, because
# the geometry record carries the window's median frequency and the catalogue
# its edges.
G = collections.defaultdict(list)
for r in GEOM:
    G[r['_stem'].rsplit('_spw', 1)[0]].append(
        (r['freqmed'] / 1e9,
         r['l_star'] / RAD_PER_ARCSEC, r['m_star'] / RAD_PER_ARCSEC))

SYN = {k: (v or {}).get('s_resolution_arcsec') for k, v in META.items()}


def positions(r_in, r_out, seed, n):
    """The extractor's own control draw, reproduced exactly."""
    rng = np.random.default_rng(int(seed))
    rr = np.sqrt(rng.uniform(r_in ** 2, r_out ** 2, n))
    th = rng.uniform(0, 2 * np.pi, n)
    return rr * np.cos(th), rr * np.sin(th)


WIN = []
for r in CAT:
    ca = CTRL.get(_wkey(r['eb'], r['band'], r['flo_GHz'], r['fhi_GHz']))
    syn = SYN.get(r['eb'])
    if not ca or not syn:
        continue
    lo = min(float(r['flo_GHz']), float(r['fhi_GHz']))
    hi = max(float(r['flo_GHz']), float(r['fhi_GHz']))
    g = [q for q in G.get(r['eb'], []) if lo - 0.05 <= q[0] <= hi + 0.05]
    if not g:
        continue
    l0, m0 = g[0][1], g[0][2]
    WIN.append(dict(row=r, ctrl=np.asarray(ca, float), syn=float(syn),
                    l0=l0, m0=m0, off=math.hypot(l0, m0)))

OFFAX = [w for w in WIN if w['off'] > OFF_MIN_ARCSEC]
if DRIVE == 6:
    OFFAX = [w for w in WIN if w['off'] > 0.0]


def pctest(sel, radius_matched=True):
    """mean(controls near the phase centre) - mean(the comparison set), per
    window, and the comparison over windows."""
    d, nnear, ncomp = [], [], []
    for w in sel:
        r = w['row']
        l, mm_ = positions(float(r['r_in_arcsec']), float(r['r_out_arcsec']),
                           r['ring_seed'], w['ctrl'].size)
        dstar = np.hypot(l, mm_)
        dpc = np.hypot(l + w['l0'], mm_ + w['m0'])
        cut = max(NEAR_BEAMS * w['syn'], NEAR_FLOOR_ARCSEC)
        near = dpc < cut
        if radius_matched:
            shell = np.abs(dstar - w['off']) < cut
            near = near & shell
            comp = shell & ~near
        else:
            comp = ~near
        if near.sum() < 1 or comp.sum() < 2:
            continue
        d.append(float(w['ctrl'][near].mean() - w['ctrl'][comp].mean()))
        nnear.append(int(near.sum()))
        ncomp.append(int(comp.sum()))
    n = len(d)
    se = st.stdev(d) / math.sqrt(n) if n > 1 else float('nan')
    return dict(n=n, mean=st.mean(d) if n else float('nan'), se=se,
                n_near_med=int(st.median(nnear)) if n else 0,
                n_comp_med=int(st.median(ncomp)) if n else 0)


PC = pctest(OFFAX, True)
PCRAW = pctest(OFFAX, False)

# ★ E5.  The test must be able to see something: the near-the-phase-centre
# sample has to be non-empty in every window counted, and the windows counted
# have to be ones where the star and the phase centre are actually resolved
# from each other.  A vacuous test would report "no excess" for free.
_offs = [w['off'] for w in OFFAX]
_minsep = min(w['off'] / max(w['syn'], 1e-9) for w in OFFAX) if OFFAX else 0
if DRIVE == 7:
    PC = dict(PC, n=0, n_near_med=0)
ck('E5 the phase-centre test is not vacuous: every window counted has '
   'control probes near the phase centre and a star resolved from it',
   PC['n'] > 50 and PC['n_near_med'] >= 1 and PC['n_comp_med'] >= 2
   and min(_offs) > OFF_MIN_ARCSEC,
   '%d windows, median %d near probes against %d comparison probes, '
   'offsets %.1f-%.1f arcsec, closest %.2f synthesised beams'
   % (PC['n'], PC['n_near_med'], PC['n_comp_med'], min(_offs), max(_offs),
      _minsep))

# What the hypothesis would have to produce: the failing block's ring is
# elevated by this much, so an excess accumulating at the phase centre would
# have to lift the phase-centre probes by something of that order.
_ringmed = dqflag._load(HERE)['ringmed']
_surv = dqflag.survey_median(HERE)
_blockring = [v for k, v in _ringmed.items() if k[0] == FAILBLOCK]
_need = st.median(_blockring) - _surv

m('EvPcNWin', '%d' % PC['n'])
m('EvPcOffLo', '%.1f' % min(_offs))
m('EvPcOffHi', '%.1f' % max(_offs))
m('EvPcNNear', '%d' % PC['n_near_med'])
m('EvPcDiff', '%+.2f' % PC['mean'])
m('EvPcErr', '%.2f' % PC['se'])
m('EvPcBound', '%.2f' % (PC['mean'] + 2.0 * PC['se']))
m('EvPcUnmatched', '%+.2f' % PCRAW['mean'])
m('EvPcNeed', '%.1f' % _need)
m('EvPcFactor', '%.0f' % (_need / max(PC['mean'] + 2.0 * PC['se'], 1e-9)))

# ============================ (3) THE TWO BANDS, RECONCILED ===============
# The clustering test runs over the crossings for which the release records a
# MEASURED peak frequency, in the topocentric frame, against the transition
# list the search was tuned to.  The ledger's frequency column is a different
# set in a different frame: all of the crossings, topocentric but recovered
# from the released offset where no peak was recorded, and attributed in the
# star's own frame against the published list.  The two therefore give
# different counts in the same band, which is correct and which the appendix
# must say rather than leave a reader to reconcile.
_blo = float(texval('AppMBandLo'))
_bhi = float(texval('AppMBandHi'))
_bandn = int(texval('AppMBandN'))
_bandattr = int(texval('AppMBandNAttr'))
_lg_band = [r for r in LEDGER if _blo <= r['freq'] <= _bhi]
_lg_band_attr = [r for r in _lg_band if r['attributed']]
# The test's own member list, read from its result file, so the two sides are
# the two sets and not two remembered integers.  A ledger row is an EXTRA if
# its block and frequency are in no member of the test's band.
_members = json.load(open(os.path.join(HERE, 'appm_v405.json')))[
    'scan']['crossings']['members']
_mkey = {(mem['eb'], round(mem['f'], 3)) for mem in _members}
_extra = [r for r in _lg_band
          if (r['eb'], round(r['freq'], 3)) not in _mkey]
if DRIVE == 8:
    _extra = _extra[:-1]
ck('E6 the ledger band and the clustering test band differ by exactly the '
   'rows the test cannot contain, in the total and in the attributed count '
   'alike',
   len(_members) == _bandn
   and len(_lg_band) - _bandn == len(_extra)
   and len(_lg_band_attr) - _bandattr == len(_extra),
   '%d ledger rows / %d attributed in %.3f-%.3f GHz against the test %d / '
   '%d; %d extra row(s): %s'
   % (len(_lg_band), len(_lg_band_attr), _blo, _bhi, _bandn, _bandattr,
      len(_extra), [(r['display'], r['eb']) for r in _extra]))
_diff = len(_extra)
m('EvTubeLedgerN', '%d' % len(_lg_band))
m('EvTubeLedgerAttr', '%d' % len(_lg_band_attr))
m('EvTubeExtra', '%d' % _diff)

# ------------------------------------------------------------------- output
json.dump(dict(
    failblock=FAILBLOCK, n_raw=_nraw, n_qp=len(QP), n_flag=len(FL),
    qp=dict(attributed=len(QP_ATT), unattributed=len(QP_UN),
            outranking=len(QP_RANK)),
    flagged=dict(unattributed=len(FL_UN), outranking=len(FL_RANK),
                 star_over_ring=[round(x, 4) for x in _ratios],
                 n_ge_star=_nge),
    phase_centre=dict(radius_matched=PC, unmatched=PCRAW,
                      off_min_arcsec=OFF_MIN_ARCSEC,
                      near_beams=NEAR_BEAMS,
                      block_ring_excess=_need),
), open(JSON_PATH, 'w'), indent=1, sort_keys=True)

HDR = ['%% GENERATED by events_r12.py -- do not hand-edit.',
       '%% round ' + str(ROUND) + ': the crossing population split by '
       'execution-block quality,',
       '%% and the phase-centre test of the flagged block.']
with open(OUT_PATH, 'w') as fh:
    fh.write('\n'.join(HDR + sorted(OUT)) + '\n')

print('\nevents_r12: %d raw crossings = %d quality-passing + %d flagged; '
      'quality-passing %d attributed / %d unattributed, %d outranking all '
      'controls; flagged %d unattributed, %d outranking'
      % (_nraw, len(QP), len(FL), len(QP_ATT), len(QP_UN), len(QP_RANK),
         len(FL_UN), len(FL_RANK)))
print('events_r12: phase centre -- %+.3f +- %.3f over %d windows with the '
      'star %.1f-%.1f arcsec off axis (unmatched %+.3f); the flagged '
      'block ring sits %.1f above the survey median'
      % (PC['mean'], PC['se'], PC['n'], min(_offs), max(_offs),
         PCRAW['mean'], _need))
print('events_r12: wrote %s, %d macros' % (OUT_NAME, len(OUT)))
for f in fail:
    print('  ASSERTION FIRED  ' + f)
print('events_r12: %d assertions fired' % len(fail))
sys.exit(1 if fail else 0)
