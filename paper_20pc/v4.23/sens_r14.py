#!/usr/bin/env python3
r"""round 460 -> survey_numbers_round460.tex, sens_r14.json

WHAT ALMA CAN OBSERVE, WHAT HAS BEEN SEARCHED, AND WHAT THE FLUX SCALE IS
ACTUALLY TESTED AGAINST.

Two things the background and method sections stated and could not support.

1. THE BAND LIST WAS OUT OF DATE, AND IT BEARS ON THE SURVEY'S COMPLETENESS
   RATHER THAN ONLY ON ITS PROSE.  The text said ALMA observes in Bands 3 to
   10, "eight bands".  Band 1 (35-50 GHz) has been in science operations
   since Cycle 10 and Band 2 (67-116 GHz) since Cycle 13, so the receiver
   suite is ten bands reaching down to 35 GHz, not eight reaching down to
   84.  That makes a question of fact out of what was a stylistic slip: if
   Band 1 data exist on these stars, the archive holds coverage this survey
   did not search.

   So the archive was asked.  `r14inputs/band1_archive_r14.json` is a frozen
   TAP harvest of every Band 1 and Band 2 science observation whose pointing
   centre falls inside a Band 1 half-power radius of one of the searched
   stars.  The answer is specific and it is reported in the paper either
   way: a handful of stars are covered, by a single programme, in a
   continuum mode whose channels are three orders of magnitude coarser than
   the narrowest searched here, and the data were still proprietary.  Band 2
   returns nothing at all, which is expected of a band whose first cycle
   began after the archive sweep.

2. "THE ABSOLUTE FLUX SCALE IS CHECKED TWICE FROM OUTSIDE" COUNTED AN
   INTERNAL CHECK AS AN EXTERNAL ONE.  The AU Mic comparison runs an
   independent reduction of the SAME visibilities, so it tests the extractor
   and is silent about the observatory's flux transfer; the epsilon Eri
   comparison is genuinely external and is a 28-per-cent measurement.  One
   external check at that precision cannot support a +-9 per cent term, and
   the term is in any case band-dependent.  The fractional precision of the
   one external check is computed here from the released ratio, so the
   sentence that describes it cannot drift from it.

NOTHING IS TYPED.  The star positions, channel widths and searched bands
come from the released catalogue; the Band 1 holdings from the frozen
archive harvest and its own recorded provenance; the flux-check precision
from the macro layer.  The only declared externals are ALMA's band edges and
the cycle in which each band entered science operations, which are
observatory facts and are named with their source.

    python3 sens_r14.py [--out DIR] [--drive N]

--drive 1..6 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads".
"""
import csv
import glob
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 460

DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
OUTDIR = HERE
if '--out' in sys.argv:
    OUTDIR = sys.argv[sys.argv.index('--out') + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round460%s.tex' % SUF)
assert OUT.endswith('round%d%s.tex' % (ROUND, SUF)), (ROUND, OUT)
OUT_JSON = os.path.join(OUTDIR, 'sens_r14%s.json' % SUF)

MAC, FAIL = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    MAC.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(tag, cond, detail=''):
    if not cond:
        FAIL.append(tag)
    print('  %-66s %s  %s' % (tag, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """Read a generated macro's numeric value out of the round files."""
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        mm = re.search(r'\\(?:new|renew)command\{\\%s\}\{([-+0-9.]+)\}'
                       % name, open(f, errors='replace').read())
        if mm:
            return float(mm.group(1))
    raise SystemExit('sens_r14: macro %s is not generated anywhere; it must '
                     'be written before this runs' % name)


# ------------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
ARC = json.load(open(os.path.join(HERE, 'r14inputs',
                                  'band1_archive_r14.json')))

# ===================================================================== 1
# ALMA'S RECEIVER SUITE.  EXTERNAL AND DECLARED: the band edges and the
# cycle in which each band first carried open-use science, from the
# observatory's own Proposer's Guide.  They are facts about the telescope
# and cannot be measured from our data, so they are named here once, with
# their source, and every statement in the paper is derived from them.
BAND_EDGES_GHZ = {1: (35, 50), 2: (67, 116), 3: (84, 116), 4: (125, 163),
                  5: (163, 211), 6: (211, 275), 7: (275, 373),
                  8: (385, 500), 9: (602, 720), 10: (787, 950)}
BAND_FIRST_CYCLE = {1: 10, 2: 13, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0,
                    9: 0, 10: 0}
BAND_SOURCE = ('ALMA Cycle 13 Proposer\'s Guide (band edges and the bands '
               'offered); Band 1 first offered in Cycle 10, Band 2 in '
               'Cycle 13.  EXTERNAL OBSERVATORY SPECIFICATION, not '
               'measured here.')
# The one band a published technosignature search has used, keyed by the
# search rather than typed as a count.
PRIOR_SEARCH_BANDS = {'Mason2025': 3}

N_BAND = len(BAND_EDGES_GHZ)
F_LO = min(e[0] for e in BAND_EDGES_GHZ.values())
F_HI = max(e[1] for e in BAND_EDGES_GHZ.values())
N_PRIOR = len(set(PRIOR_SEARCH_BANDS.values()))
if DRIVE == 1:
    BAND_EDGES_GHZ = {b: e for b, e in BAND_EDGES_GHZ.items() if b >= 3}
    N_BAND, F_LO = len(BAND_EDGES_GHZ), min(
        e[0] for e in BAND_EDGES_GHZ.values())
# ★ THE CLAUSE THE CORRECTED SENTENCE RESTS ON.  The paper's novelty claim
# is about frequencies above 30 GHz; it survives the correction only
# because ALMA's lowest band still starts above that line.  If a future
# receiver reached below it the claim would have to be rewritten, and this
# says so rather than leaving it to be noticed.
NOVELTY_GHZ = 30.0
ck('ALMA\'s lowest receiver band starts above the frequency the novelty '
   'claim is stated at', F_LO > NOVELTY_GHZ,
   'lowest band edge %.0f GHz against %.0f GHz' % (F_LO, NOVELTY_GHZ))
ck('the band count and the band list are one object, so "ten bands" and '
   '"35 to 950 GHz" cannot disagree',
   N_BAND == 10 and F_LO == 35 and F_HI == 950,
   '%d bands, %.0f-%.0f GHz' % (N_BAND, F_LO, F_HI))
m('SbNBand', '%d' % N_BAND)
m('SbBandLoGHz', '%.0f' % F_LO)
m('SbBandHiGHz', '%.0f' % F_HI)
m('SbBandOneLoGHz', '%.0f' % BAND_EDGES_GHZ[min(BAND_EDGES_GHZ)][0])
m('SbBandOneHiGHz', '%.0f' % BAND_EDGES_GHZ[min(BAND_EDGES_GHZ)][1])
# ★ A SMALL COUNT READS AS A WORD IN PROSE AND AS A DIGIT IN A TABLE, and
# the paper's rule is that neither may be typed.  So the word form is
# generated from the count, which keeps one owner for both.
WORD = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
        'eight', 'nine', 'ten']
m('SbNPriorBandWord', WORD[N_PRIOR])

# ===================================================================== 2
# WHAT THIS SURVEY SEARCHED, FROM THE CATALOGUE AND NOT FROM MEMORY.
SEARCHED = sorted({int(r['band']) for r in CAT})
CHAN_HZ = sorted(float(r['chanw_Hz']) for r in CAT)
ck('every band the catalogue carries is a band ALMA has',
   set(SEARCHED) <= set(BAND_EDGES_GHZ), sorted(set(SEARCHED)))
m('SbNSearchedBand', '%d' % len(SEARCHED))
m('SbChanFinestKHz', '%.1f' % (CHAN_HZ[0] / 1e3))

# ===================================================================== 3
# ★★★★ IS THERE BAND 1 COVERAGE OF THESE STARS IN THE ARCHIVE?  YES, AND
# IT IS UNUSABLE FOR THIS SEARCH FOR TWO INDEPENDENT REASONS.
B1 = ARC['hits']['1']
B2 = ARC['hits']['2']
B1_SCI = [h for h in B1 if h['science'] == 'T']
B1_STARS = sorted({h['star'] for h in B1_SCI})
B1_PROG = sorted({h['proposal'] for h in B1_SCI})
B1_CHAN_KHZ = [c for h in B1_SCI for c in h['chan_khz']]
B1_PUBLIC = [h for h in B1_SCI if h['rights'] != 'Proprietary']
B1_REL = sorted(h['release'][:10] for h in B1_SCI)
if DRIVE == 2:
    B1_PUBLIC = B1_SCI
if DRIVE == 3:
    B1_CHAN_KHZ = [CHAN_HZ[0] / 1e3]
ck('the survey\'s stars have Band 1 coverage in the archive at all, so the '
   'completeness statement is about something that exists',
   len(B1_STARS) > 0, '%d stars, %d windows, %d programme(s): %s'
   % (len(B1_STARS), len(B1_SCI), len(B1_PROG), ', '.join(B1_PROG)))
ck('none of it was public when the archive was swept, so none of it could '
   'have been searched', not B1_PUBLIC,
   'earliest release %s, latest %s' % (B1_REL[0], B1_REL[-1])
   if B1_REL else 'no rows')
RATIO = (min(B1_CHAN_KHZ) * 1e3 / CHAN_HZ[0]) if B1_CHAN_KHZ else 0.0
ck('and its narrowest channel is orders of magnitude coarser than the '
   'narrowest channel searched here, so it could not carry this search '
   'even if it were public', RATIO > 100.0,
   '%.0f MHz against %.1f kHz, a factor %.0f'
   % (min(B1_CHAN_KHZ) / 1e3, CHAN_HZ[0] / 1e3, RATIO) if B1_CHAN_KHZ
   else 'no channel widths recorded')
ck('no Band 2 science observation covers any star of this sample',
   not B2, '%d rows' % len(B2))
# ★ and the harvest is not vacuous: it saw a real archive, not an empty
# query.  A silently failed TAP call returns nothing and would otherwise
# read as "no Band 1 data exist".
NARC1 = int(ARC['n_archive']['1'])
if DRIVE == 4:
    NARC1 = 0
ck('the harvest reached a populated archive, so "nothing on these stars" '
   'is a result and not a failed query',
   NARC1 > 1000, '%d Band 1 rows in ivoa.obscore' % NARC1)

m('SbBoneNStar', '%d' % len(B1_STARS))
m('SbBoneNWin', '%d' % len(B1_SCI))
m('SbBoneNProgWord', WORD[len(B1_PROG)])
m('SbBoneChanMHz', '%.2f' % (min(B1_CHAN_KHZ) / 1e3) if B1_CHAN_KHZ else '--')
m('SbBoneChanRatio', '%.0f' % RATIO)
m('SbBoneRelYear', B1_REL[0][:4] if B1_REL else '--')
m('SbBonePbArcsec', '%.0f' % ARC['pb_arcsec'])

# ===================================================================== 4
# ★★ THE ONE EXTERNAL FLUX-SCALE CHECK, AND ITS PRECISION.
#
# Two comparisons were described as external.  The AU Mic one re-reduces the
# same visibilities through an independent pipeline: a ratio of 0.994 +- 0.014
# there is a statement about the extractor, and an error in ALMA's flux
# transfer would appear in both reductions identically and cancel.  Only the
# epsilon Eri comparison is against an independently calibrated published
# flux density, and its precision is what it is.
EPS_R, EPS_E = macro('PxEpsRatio'), macro('PxEpsRatioErr')
JAN_R, JAN_E = macro('PxJanRatio'), macro('PxJanRatioErr')
EPS_PCT = 100.0 * EPS_E / EPS_R
JAN_PCT = 100.0 * JAN_E / JAN_R
if DRIVE == 5:
    EPS_PCT = 0.5 * JAN_PCT
ck('the one external flux-scale check is far less precise than the internal '
   'extractor check, which is why the two cannot be quoted as a pair',
   EPS_PCT > 5.0 * JAN_PCT,
   'epsilon Eri +-%.0f per cent against AU Mic +-%.1f per cent'
   % (EPS_PCT, JAN_PCT))
# ★ and it is less precise than the calibration term it was offered in
# support of, which is the whole of the objection.
CAL_PCT = macro('BudComb')
if DRIVE == 6:
    CAL_PCT = 2.0 * EPS_PCT
ck('and it is less precise than the calibration term it was offered in '
   'support of, so it cannot be the evidence for it',
   EPS_PCT > CAL_PCT, 'external check +-%.0f per cent against a quoted '
   '+-%.0f per cent' % (EPS_PCT, CAL_PCT))
m('SbEpsPct', '%.0f' % EPS_PCT)
m('SbJanPct', '%.1f' % JAN_PCT)

# ===================================================================== 5
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by sens_r14.py -- do not hand-edit.\n')
    fh.write('\n'.join(MAC) + '\n')
json.dump(dict(generated_by=os.path.basename(__file__), round=ROUND,
               drive=DRIVE,
               bands=dict(n=N_BAND, lo_ghz=F_LO, hi_ghz=F_HI,
                          edges=BAND_EDGES_GHZ,
                          first_cycle=BAND_FIRST_CYCLE,
                          source=BAND_SOURCE,
                          prior_searches=PRIOR_SEARCH_BANDS,
                          searched_here=SEARCHED),
               band1=dict(n_star=len(B1_STARS), stars=B1_STARS,
                          n_win=len(B1_SCI), programmes=B1_PROG,
                          chan_khz=sorted(set(B1_CHAN_KHZ)),
                          chan_ratio=RATIO, n_public=len(B1_PUBLIC),
                          release=B1_REL, pb_arcsec=ARC['pb_arcsec'],
                          provenance=ARC['_provenance']),
               band2=dict(n_win=len(B2)),
               fluxcheck=dict(eps_ratio=EPS_R, eps_err=EPS_E,
                              eps_pct=EPS_PCT, aumic_ratio=JAN_R,
                              aumic_err=JAN_E, aumic_pct=JAN_PCT,
                              aumic_is_internal=True,
                              quoted_calibration_pct=CAL_PCT),
               fail=FAIL),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True, default=str)
print('sens_r14: %d macros -> %s' % (len(MAC), os.path.basename(OUT)))
if FAIL:
    raise SystemExit('sens_r14 FAILED: %s' % '; '.join(FAIL))
