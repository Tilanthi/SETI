#!/usr/bin/env python3
r"""round 900 -> survey_numbers_round900.tex, beam_r19.json.

THE OFF-AXIS PRIMARY-BEAM PRESCRIPTION, WINDOW BY WINDOW, FOR THE TWELVE
WINDOWS WHERE THE CHOICE OF BEAM WIDTH MATTERS BY MORE THAN TEN PER CENT.

Referee 1's third issue asks seven questions about those twelve windows, and
every one of them is answered here as a measurement on the release itself.

  1  WHICH MODEL IS APPLIED.  The limits published in this paper divide the
     measured noise by a Gaussian of the observatory's documented full width,
     `\RingPbCoef` lambda/D, evaluated at each window's own dish diameter and
     own centre frequency.  The survey's pipeline had instead divided by a
     Gaussian of `\RingPbCoefCode` lambda/D -- which is the Airy first-null
     (Rayleigh) coefficient and not a half-power width at all -- and the
     documented width replaced it before any limit in this paper was formed.
     Both responses are reproduced here from the geometry, so which is which
     is a measurement and not an attribution.
  2  WHETHER THAT MODEL MATCHES THE REAL CONFIGURATION.  The dish diameter and
     the frequency are checked against the ALMA Science Archive's own obscore
     record for the execution block -- antenna array, antenna counts and
     reported frequency support -- so the check is against the observatory and
     not against another column of ours.
  3  THE LIMITS RECOMPUTED under the documented prescription, window by window.
  4  COMPARED WITH THE PER-SYSTEM TABLE, by parsing the table fragment that
     ships, so that a limit printed there and a limit computed here cannot
     part.
  5  ADOPT OR CARRY.  The difference between the two prescriptions reaches
     more than twice the quoted calibration interval, so it cannot be absorbed
     into an error bar and a choice has to be made and defended.  The
     documented Gaussian is the better supported one on every one of the
     twelve, against the blocked-aperture response that the observatory's own
     imaging software applies: it is within a few per cent where the
     Airy-null Gaussian is out by tens.  What remains after adopting it -- the
     departure of the documented Gaussian from the blocked aperture at those
     offsets -- is the residual systematic those limits carry, and it is
     emitted here so that the text can state it where the limits are quoted.
  6  WHETHER ANY OF THE TWELVE IS ITS SYSTEM'S BEST WINDOW.  One is, and it is
     the window that sets the limit of the system with the deepest limit of
     any system more than a few parsecs away, so this is not a bookkeeping
     question.
  7  WHAT MOVES.  Every system limit, best window and ordinal position is
     formed under both prescriptions and compared.

Inputs: the released catalogue, `pb_atten_fwhm_r11.csv` (the per-row response
under both widths, from `sens_r11.py`), `pbgate_v408.airy_casa` (the one owner
of the blocked-aperture form), `archive_meta_v381.json` (the archive's own
per-block record), `tab_persys_r17.tex` (the table that ships) and
`adopted_e90` for the limits.  NOTHING IS TYPED: the two coefficients and the
calibration interval come from the macro layer, the beam forms from the
generator that owns them, and every count from the length of a set.

    python3 beam_r19.py [--paper DIR] [--out DIR] [--drive N]

`--paper` is the directory the inputs are read from; it defaults to this
file's own directory, which is what it is when the file sits in the build.
--drive 1..10 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads".
"""
import csv
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 900

DRIVE = None
OUTDIR = HERE
PAPER = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
    if _a == '--paper':
        PAPER = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(OUTDIR, 'beam_r19%s.json' % SUF)

AS = math.pi / 180.0 / 3600.0
C = 299792458.0
# The agreement between the two candidate widths above which a window is
# counted here.  It is the threshold the appendix already publishes a count
# against, it is a tolerance on a model comparison and not a level in a
# response, and N1 asserts that the set it selects is that published set.
PICK_TOL = 0.10

MACROS, FAIL = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-70s %s  %s' % (label[:70], 'PASS' if ok else 'FAIL', detail))


def sci(v, sf=2):
    e = int(math.floor(math.log10(abs(v))))
    return '%.*f\\times10^{%d}' % (sf - 1, v / 10.0 ** e, e)


sys.path.insert(0, PAPER)
import adopted_e90 as ae                                      # noqa: E402
import pbgate_v408 as pbg                                     # noqa: E402
# ★ The per-system table's own label function, not a second copy of it: it
# strips the SIMBAD catalogue markers `star_alias` leaves in place, and one
# system in the table is printed under the shorter form.  Using the table's
# own function is what makes the comparison against the fragment exact.
import persys_r17 as ps                                       # noqa: E402

CAT = ae.catalogue(PAPER)
PBF = list(csv.DictReader(open(os.path.join(PAPER, 'pb_atten_fwhm_r11.csv'))))
META = json.load(open(os.path.join(PAPER, 'archive_meta_v381.json')))['ebs']

# ★ THE TWO COEFFICIENTS AND THE CALIBRATION INTERVAL ARE READ, NOT TYPED.
COEF_DOC = float(ae._texval('RingPbCoef', PAPER))
COEF_NULL = float(ae._texval('RingPbCoefCode', PAPER))
CAL_PCT = float(ae._texval('BudComb', PAPER))
N_PUB = int(ae._texval('BmNAboveTenPct', PAPER))

print('beam_r19 round %d%s' % (ROUND, '' if DRIVE is None
                               else ' (drive %d)' % DRIVE))
print('  documented width %.2f lambda/D, pipeline width %.2f lambda/D, '
      'calibration interval +-%.0f per cent'
      % (COEF_DOC, COEF_NULL, CAL_PCT))

assert len(PBF) == len(CAT), (len(PBF), len(CAT))
_bad = [i for i, (p, r) in enumerate(zip(PBF, CAT))
        if p['pb_atten'] != r['pb_atten'] or p['eb'] != r['eb']]
assert not _bad, '%d rows of the response table do not pair with the ' \
                 'catalogue' % len(_bad)


def gauss_c(c, coef):
    """A Gaussian of full width `coef` lambda/D at an offset of c lambda/D."""
    return math.exp(-4.0 * math.log(2.0) * (c / coef) ** 2)


def airy_c(c, dish):
    """`pbgate_v408.airy_casa` at an offset of c lambda/D on `dish`."""
    lam = 1.0e-3                                 # any wavelength: c is scaled
    th = c * lam / dish / AS
    return pbg.airy_casa(th, lam, dish)


def offset_c(p):
    """A row's offset in units of lambda/D, from its own stored geometry."""
    return (float(p['pb_offset_arcsec'])
            / (float(p['theta_pb_fwhm_arcsec']) / COEF_DOC))


# =====================================================================
# 1  THE TWELVE WINDOWS, AND WHICH MODEL EACH OF THEM CARRIES
# =====================================================================
print('\n1  the windows where the choice of width matters by more than a '
      'tenth')
RATIO = [float(p['pb_atten_fwhm']) / float(p['pb_atten']) for p in PBF]
SEL = [i for i, x in enumerate(RATIO) if x < 1.0 / (1.0 + PICK_TOL)]
_npub = N_PUB if DRIVE != 1 else N_PUB + 1
ck('N1 the windows in which the two candidate widths part by more than a '
   'tenth are the published set, in number',
   len(SEL) == _npub, '%d selected against %s published' % (len(SEL), _npub))

ROWS = []
for i in sorted(SEL, key=lambda i: RATIO[i]):
    p, r = PBF[i], CAT[i]
    nu = 0.5 * (float(p['flo_GHz']) + float(p['fhi_GHz'])) * 1e9
    dish = float(p['dish_m'])
    c = offset_c(p)
    ROWS.append(dict(
        i=i, star=p['star_name'], eb=p['eb'], sid=r['system_id'],
        cls=r['search_class'], nu_GHz=nu / 1e9, dish=dish,
        off=float(p['pb_offset_arcsec']),
        th_stored=float(p['theta_pb_fwhm_arcsec']),
        th_calc=COEF_DOC * (C / nu) / dish / AS,
        c=c, a_pipe=float(p['pb_atten']), a_doc=float(p['pb_atten_fwhm']),
        ratio=RATIO[i],
        dev_doc=abs(gauss_c(c, COEF_DOC) / airy_c(c, dish) - 1.0),
        dev_pipe=abs(gauss_c(c, COEF_NULL) / airy_c(c, dish) - 1.0)))
STARS = sorted({d['star'] for d in ROWS})
print('  %d windows, %d stars, %d blocks, bands by frequency %.0f-%.0f GHz'
      % (len(ROWS), len(STARS), len({d['eb'] for d in ROWS}),
         min(d['nu_GHz'] for d in ROWS), max(d['nu_GHz'] for d in ROWS)))

# The applied response must BE the pipeline Gaussian, evaluated at the stored
# offset with the window's own dish and own frequency, and the stored width
# must BE the documented coefficient at that frequency and dish.  Both
# directions are forward evaluations: nothing here is inverted.
_d_th = max(abs(d['th_calc'] / d['th_stored'] - 1.0) for d in ROWS)
_d_pipe = max(abs(gauss_c(d['c'], COEF_NULL) - d['a_pipe']) for d in ROWS)
_d_doc = max(abs(gauss_c(d['c'], COEF_DOC) - d['a_doc']) for d in ROWS)
if DRIVE == 2:
    _d_pipe = 0.5
ck('N2 on every one of them the response the pipeline applied is a Gaussian '
   'of the Airy-null coefficient and the response adopted is a Gaussian of '
   'the documented coefficient, each at that window\'s own dish and own '
   'centre frequency',
   _d_th < 1e-4 and _d_pipe < 1e-5 and _d_doc < 1e-5,
   'width closes to %.1e, pipeline response to %.1e, documented to %.1e'
   % (_d_th, _d_pipe, _d_doc))

# =====================================================================
# 2  WHETHER THAT CONFIGURATION IS THE ONE THE OBSERVATORY RECORDS
# =====================================================================
print('\n2  the configuration and the frequency, against the archive\'s own '
      'record')
ARR, MISS, BADF = {}, [], []
for d in ROWS:
    e = META.get(d['eb'])
    if e is None:
        MISS.append(d['eb'])
        continue
    ARR[d['eb']] = (e['array'], e.get('n_ant_12m'), e.get('n_ant_7m'))
    # the archive reports the array, and a 12 m array means 12 m dishes
    want = 12.0 if e['array'] == '12m' else 7.0
    if abs(want - d['dish']) > 1e-9:
        BADF.append((d['eb'], e['array'], d['dish']))
    # and the window's own centre frequency must lie inside a frequency range
    # the archive reports for that block
    if not any(min(f[0], f[1]) - 0.5 <= d['nu_GHz'] <= max(f[0], f[1]) + 0.5
               for f in e['freq_support']):
        BADF.append((d['eb'], 'freq', d['nu_GHz']))
if DRIVE == 3:
    BADF.append(('drive', 'forced', 0))
for e in sorted(ARR):
    print('  %-22s archive %-4s  %s x 12 m, %s x 7 m'
          % (e, ARR[e][0], ARR[e][1], ARR[e][2]))
ck('N3 the dish diameter and the observing frequency the beam model uses are '
   'the antenna configuration and the frequency coverage the ALMA archive '
   'records for the block, on every one of the twelve',
   not MISS and not BADF,
   '%d blocks resolved, %d absent from the archive record, %d disagreements'
   % (len(ARR), len(MISS), len(BADF)))
_n12 = sum(1 for d in ROWS if ARR.get(d['eb'], ('', 0, 0))[0] == '12m')

# =====================================================================
# 3  THE LIMITS, RECOMPUTED UNDER BOTH PRESCRIPTIONS
# =====================================================================
print('\n3  the limits of the twelve under each prescription')
E_DOC = ae.per_window(CAT, PAPER)                      # what the paper quotes
E_PIPE = ae.per_window(CAT, PAPER, _beam=False)        # the pipeline's beam
for d in ROWS:
    r = CAT[d['i']]
    d['e_pipe'] = E_PIPE[id(r)]
    d['e_doc'] = E_DOC[id(r)]
    print('  %-10s %-22s %s %7.2f GHz  off %5.2f"  A %.4f -> %.4f   '
          'EIRP90 %.3e -> %.3e  (x%.3f)'
          % (d['star'], d['eb'], d['cls'], d['nu_GHz'], d['off'],
             d['a_pipe'], d['a_doc'], d['e_pipe'], d['e_doc'],
             d['e_doc'] / d['e_pipe']))
_rev = [d for d in ROWS if d['e_doc'] < d['e_pipe'] * (1.0 - 1e-9)]
_shift = max(d['e_doc'] / d['e_pipe'] - 1.0 for d in ROWS)
if DRIVE == 4:
    _rev = [ROWS[0]]
ck('N4 the documented prescription makes the limit of every one of the twelve '
   'shallower and none of them deeper, so adopting it cannot manufacture a '
   'deeper limit anywhere',
   not _rev, '%d reversed; largest increase %.1f per cent'
   % (len(_rev), 100 * _shift))

# =====================================================================
# 4  ADOPT OR CARRY: WHICH MODEL IS BETTER SUPPORTED, AND BY HOW MUCH
# =====================================================================
print('\n4  which of the two is the better supported model, window by window')
_worse = [d for d in ROWS if d['dev_doc'] >= d['dev_pipe']]
if DRIVE == 5:
    _worse = [ROWS[0]]
ck('N5 the documented Gaussian is closer to the blocked-aperture response '
   'than the pipeline Gaussian at the offset of every one of the twelve, so '
   'the adopted model is the better supported one on each window and not '
   'merely on average',
   not _worse,
   'documented %.1f-%.1f per cent against %.1f-%.1f per cent, worst case on '
   '%d windows' % (100 * min(d['dev_doc'] for d in ROWS),
                   100 * max(d['dev_doc'] for d in ROWS),
                   100 * min(d['dev_pipe'] for d in ROWS),
                   100 * max(d['dev_pipe'] for d in ROWS), len(_worse)))
_resid = max(d['dev_doc'] for d in ROWS)
_exceeds = 100 * _shift > CAL_PCT
_inside = 100 * _resid < CAL_PCT
if DRIVE == 6:
    _exceeds = 100 * (0.5 * CAL_PCT / 100.0) > CAL_PCT
ck('N5b the difference between the two prescriptions exceeds the quoted '
   'calibration interval, so the choice cannot be absorbed into it, while '
   'the residual left after adopting the better supported one lies inside it',
   _exceeds and _inside,
   'difference %.1f per cent and residual %.1f per cent against an interval '
   'of %.0f per cent' % (100 * _shift, 100 * _resid, CAL_PCT))

# ★★ AND THE CLAIM MUST NOT BE OVERSTATED, WHICH TOOK MEASURING THE WHOLE
# CENSUS AND NOT ONLY THE TWELVE.  Formally, the pipeline Gaussian is the
# closer of the two to the blocked aperture on most rows of the census -- near
# the axis the wider Gaussian happens to follow the aperture's curvature a
# little better -- so "the documented width is the better model" is true where
# it has a consequence and false as a blanket statement.  The two populations
# separate cleanly and without overlap in offset, which is what licenses
# saying it the careful way round: where the correction matters the documented
# width is better, and where the pipeline width is formally better the two
# forms and the aperture agree to within a couple of per cent on a response
# near unity.
ALLC = []
for p in PBF:
    c, dish = offset_c(p), float(p['dish_m'])
    ref = airy_c(c, dish)
    ALLC.append((c, abs(gauss_c(c, COEF_DOC) / ref - 1.0),
                 abs(gauss_c(c, COEF_NULL) / ref - 1.0),
                 float(p['pb_atten_fwhm'])))
DOCBET = [t for t in ALLC if t[1] < t[2]]
PIPBET = [t for t in ALLC if t[1] >= t[2]]
_gap = min(t[0] for t in DOCBET) > max(t[0] for t in PIPBET)
_small = max(max(t[1], t[2]) for t in PIPBET)
if DRIVE == 10:
    _gap = False
ck('N5c the rows on which the pipeline Gaussian is formally the closer of the '
   'two are a separate population in offset, on which both forms agree with '
   'the blocked aperture to a couple of per cent at a response near unity, so '
   'the adopted model is the better one wherever the correction has a '
   'consequence and is not claimed to be better everywhere',
   _gap and 100 * _small < 0.5 * CAL_PCT,
   '%d rows beyond %.3f lambda/D favour the documented width, %d within '
   '%.3f favour the pipeline width by at most %.1f per cent at a response '
   'above %.2f' % (len(DOCBET), min(t[0] for t in DOCBET), len(PIPBET),
                   max(t[0] for t in PIPBET), 100 * _small,
                   min(t[3] for t in PIPBET)))

# =====================================================================
# 5  IS ANY OF THE TWELVE ITS SYSTEM'S BEST WINDOW
# =====================================================================
print('\n5  the best window of each system, under each prescription')


def best_by_system(E, cls='A'):
    out = {}
    for r in CAT:
        if r['search_class'] != cls:
            continue
        k = r['system_id']
        if k not in out or E[id(r)] < out[k][0]:
            out[k] = (E[id(r)], r)
    return out


B_DOC, B_PIPE = best_by_system(E_DOC), best_by_system(E_PIPE)
# ★ Instruction 6 says "its stellar system", not "its Class A system", so the
# coarse search is asked the same question.  Its answer reaches no published
# per-system limit -- the paper quotes coarse limits for three stars only, and
# none of them is one of these -- but a question answered on one class and
# reported as if answered on both is how a survey statement goes wrong.
B_DOC_B = best_by_system(E_DOC, 'B')
ORD_DOC = [k for k, _ in sorted(B_DOC.items(), key=lambda kv: kv[1][0])]
ORD_PIPE = [k for k, _ in sorted(B_PIPE.items(), key=lambda kv: kv[1][0])]
SELID = {id(CAT[d['i']]): d for d in ROWS}
HITS = [SELID[id(v[1])] for v in B_DOC.values() if id(v[1]) in SELID]
if DRIVE == 7:
    HITS = []
ck('N6 the question whether one of the twelve sets its own system\'s limit is '
   'answered from the per-window limits and not assumed, and the answer is '
   'not none',
   len(HITS) >= 1, '%d of %d are their system\'s best window: %s'
   % (len(HITS), len(ROWS), ', '.join(ps.designation(d['sid'])
                                      for d in HITS) or 'none'))
HITS_B = [SELID[id(v[1])] for v in B_DOC_B.values() if id(v[1]) in SELID]
print('  and in the coarse search %d of them is its system\'s best window: %s'
      % (len(HITS_B), ', '.join('%s (%s)' % (ps.designation(d['sid']), d['eb'])
                                for d in HITS_B) or 'none'))
HIT = HITS[0] if HITS else None
for d in HITS:
    print('  %s: best window %s at %.2f GHz, %.2f" off axis, response %.4f, '
          'EIRP90 %.3e W' % (ps.designation(d['sid']), d['eb'], d['nu_GHz'],
                             d['off'], d['a_doc'], d['e_doc']))

# =====================================================================
# 6  WHAT MOVES BETWEEN THE TWO PRESCRIPTIONS, AND WHAT THE TABLE PRINTS
# =====================================================================
print('\n6  what moves, and what the per-system table prints')
MOVED = sorted(((k, B_PIPE[k][0], B_DOC[k][0]) for k in B_DOC
                if abs(B_DOC[k][0] / B_PIPE[k][0] - 1.0) > 1e-3),
               key=lambda t: -t[2] / t[1])
for k, a, b in MOVED:
    print('  %-24s %.3e -> %.3e  (x%.4f)  rank %d -> %d'
          % (ps.designation(k), a, b, b / a,
             ORD_PIPE.index(k) + 1, ORD_DOC.index(k) + 1))
N_RANK = sum(1 for i, k in enumerate(ORD_DOC) if ORD_PIPE[i] != k)
N15 = (sum(1 for v, _ in B_PIPE.values() if v <= 1e15),
       sum(1 for v, _ in B_DOC.values() if v <= 1e15))
MED = (st.median([v for v, _ in B_PIPE.values()]),
       st.median([v for v, _ in B_DOC.values()]))
print('  %d of %d systems change ordinal position; systems at 1e15 W %d -> '
      '%d; median system limit %.4e -> %.4e'
      % (N_RANK, len(ORD_DOC), N15[0], N15[1], MED[0], MED[1]))

# ★ THE TABLE THAT SHIPS IS PARSED, so that a value printed there and a value
# computed here cannot part.  This is the honest form of "compare with
# Table F1": the comparison is against the fragment, not against a memory of
# it.  The fragment prints two systems per line in units the caption fixes,
# so the exponent is recovered from the row itself rather than assumed.
TABF = os.path.join(PAPER, 'tab_persys_r17.tex')
PRINTED = {}
for line in open(TABF):
    if '&' not in line or line.lstrip().startswith('%'):
        continue
    cells = [c.strip() for c in line.replace('\\\\', '').split('&')]
    for j in range(0, len(cells) - 4, 6):
        # ★ The dagger that marks a measured completeness is set on the VALUE
        # cell, and the designation of one system in the table is shorter than
        # the catalogue's own.  Both would silently drop rows from a
        # comparison that is only meaningful over all of them, so N7 counts
        # the rows it matched and fails on a shortfall rather than reporting a
        # clean pass over a subset.
        nm = cells[j].strip()
        val = cells[j + 1].split('$')[0].strip()
        try:
            PRINTED[nm] = float(val)
        except ValueError:
            continue
_scale = None
for k in B_DOC:
    nm = ps.designation(k)
    if nm in PRINTED and PRINTED[nm]:
        _s = round(math.log10(B_DOC[k][0] / PRINTED[nm]))
        _scale = _s if _scale is None else _scale
_cmp = [(ps.designation(k), B_DOC[k][0], B_PIPE[k][0],
         PRINTED[ps.designation(k)] * 10.0 ** _scale)
        for k in B_DOC if ps.designation(k) in PRINTED]
_bad_doc = [t for t in _cmp if abs(t[1] / t[3] - 1.0) > 0.05]
_bad_pipe = [t for t in _cmp if abs(t[2] / t[3] - 1.0) > 0.05]
if DRIVE == 8:
    _bad_doc = [_cmp[0]]
ck('N7 every limit the per-system table prints is the limit the documented '
   'prescription gives, so the table already carries the adopted model and '
   'the comparison is against the fragment that ships',
   len(_cmp) == len(B_DOC) and not _bad_doc,
   '%d of %d systems matched at the printed precision, %d disagree with the '
   'documented model and %d with the pipeline model'
   % (len(_cmp), len(B_DOC), len(_bad_doc), len(_bad_pipe)))
_hitrow = ([t for t in _cmp if HIT and t[0] == ps.designation(HIT['sid'])]
           or [None])[0]
if DRIVE == 9:
    _bad_pipe = []
ck('N7b and on the system whose best window is one of the twelve the two '
   'prescriptions print differently, so that comparison can tell them apart '
   'rather than being satisfied by either',
   bool(_hitrow) and abs(_hitrow[1] / _hitrow[3] - 1.0)
   < abs(_hitrow[2] / _hitrow[3] - 1.0) and len(_bad_pipe) >= 1,
   'printed %.3e against documented %.3e and pipeline %.3e; %d systems the '
   'pipeline model would misprint'
   % (_hitrow[3] if _hitrow else 0.0, _hitrow[1] if _hitrow else 0.0,
      _hitrow[2] if _hitrow else 0.0, len(_bad_pipe)))

# =====================================================================
# 7  THE MACROS
# =====================================================================
# ★★ ONLY THE MACROS THE PROSE ACTUALLY CITES ARE EMITTED, and that is a rule
# of this build rather than a preference.  `retire_macros.py` deletes a macro
# the manuscript does not reference, so a generator that publishes its whole
# working leaves a round file that the next regeneration rewrites -- and the
# clean-regeneration check compares products byte for byte.  Everything else
# measured here is in `beam_r19.json`, which is evidence and not typesetting.
# ★ Nor may a new macro repeat a value another generator already publishes in
# the same unit: `\BmShiftMaxPct`, `\BmNAboveTenPct`, `\BmModelMaxPct`,
# `\BmModelMaxNullPct`, `\BmEpsAgreePct`, `\NmBeamFacWorst` and
# `\BudComb` all exist, `valuetwin.py` groups cited macros by value and unit,
# and a second name for one of them is the defect that gate was written for.
m('BnStarList', ' and '.join(ps.designation(d) for d in
                             sorted({r['sid'] for r in ROWS},
                                    key=lambda s: ps.designation(s))))
if HIT:
    m('BnBestSys', ps.designation(HIT['sid']).replace(' ', '~'))
    m('BnBestFac', '%.2f' % (1.0 / HIT['a_doc']))
    m('BnBestResp', '%.3f' % HIT['a_doc'])

json.dump(dict(
    coef_doc=COEF_DOC, coef_pipe=COEF_NULL, calib_pct=CAL_PCT,
    windows=[{k: v for k, v in d.items() if k != 'i'} for d in ROWS],
    arrays={e: dict(array=ARR[e][0], n12=ARR[e][1], n7=ARR[e][2])
            for e in ARR},
    moved=[dict(system=ps.designation(k), pipeline=a, documented=b)
           for k, a, b in MOVED],
    n_windows=len(ROWS), n_stars=len(STARS),
    n_blocks=len({d['eb'] for d in ROWS}),
    shift_max_pct=100 * _shift, resid_pct=[100 * min(d['dev_doc'] for d in ROWS),
                                          100 * _resid],
    pipe_resid_pct=[100 * min(d['dev_pipe'] for d in ROWS),
                    100 * max(d['dev_pipe'] for d in ROWS)],
    pipe_fac_worst=1.0 / min(float(p['pb_atten']) for p in PBF),
    n_doc_better=len(DOCBET), pipe_better_max_pct=100 * _small,
    best=(dict(system=ps.designation(HIT['sid']), eb=HIT['eb'],
               nu_GHz=HIT['nu_GHz'], off=HIT['off'], resp=HIT['a_doc'],
               factor=1.0 / HIT['a_doc'], eirp=HIT['e_doc'],
               rank_pipeline=ORD_PIPE.index(HIT['sid']) + 1,
               rank_documented=ORD_DOC.index(HIT['sid']) + 1)
          if HIT else None),
    best_class_b=[dict(system=ps.designation(d['sid']), eb=d['eb'],
                       nu_GHz=d['nu_GHz'], eirp=d['e_doc'])
                  for d in HITS_B],
    n_rank_move=N_RANK, n_1e15=dict(pipeline=N15[0], documented=N15[1]),
    median_system=dict(pipeline=MED[0], documented=MED[1]),
    printed_vs_computed=[dict(system=t[0], documented=t[1], pipeline=t[2],
                              printed=t[3]) for t in _cmp],
    fails=FAIL), open(OUT_JSON, 'w'), indent=1, sort_keys=True)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    fh.write('\n'.join(sorted(MACROS)) + '\n')
print('\n  wrote %s and %s' % (os.path.basename(OUT),
                               os.path.basename(OUT_JSON)))
if FAIL:
    print('  FAILURES: %s' % ', '.join(sorted(set(FAIL))))
    raise SystemExit(1)
print('  all clauses pass')
