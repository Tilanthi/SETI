#!/usr/bin/env python3
r"""Gate on the front matter's three physical claims and its three prose
instructions.  Publishes nothing.

★ THIS FILE WAS A GENERATOR AND IS NOW A GATE, AND THE REASON IS WORTH
RECORDING.  It began life as round 590, publishing \PsSheikhNHz = 200,
\PsDriftPctSheikh = 6, \PsJupAccel = 2.2 and \PsAccelRotRatio = 0.61, because
the abstract and conclusion 8 had to state the drift ceiling in nanohertz and
as a fraction of the general recommendation and no macro carried either.
Twenty minutes later the figures owner regenerated round 37 with
\AccelSheikhNHz = 200, \AccelSheikhPct = 6, \AccelJupRot = 2.2 and
\AccelJupPct = 61 -- four exact twins, because the same referee point (M9)
touches both a figure caption and the front matter and the ownership table
gives M9 to them.  Two macros for one quantity is how this project has
produced disagreeing numbers before, so round 590 is retired, the prose cites
round 37, and what survives here is the part that was never duplicated: the
independent recomputation, kept as a CROSS-CHECK on round 37 rather than as a
second source for the same number.

    1 Hz s^-1 GHz^-1 == 1e-9 s^-1 == 1 nHz exactly, so the drift ceiling the
    paper has always published as \DriftCeilLo--\DriftCeilHi is already in
    the literature's units and needed labelling, not converting.

CHECKS (rule 9: every one is driven to fail on purpose)

    S1  the nHz ceiling recomputed window by window from the released
        catalogue reproduces round 13's printed \DriftCeilLo and
        \DriftCeilHi exactly.  Not vacuous: it is computed from
        drift_max_Hz_s and the window edges, and round 13's values are read
        out of the typeset macro file, so the two paths share no code;
    S2  the general recommendation is READ from a frozen record that carries
        the sentence it was read from and a resolvable reference, and round
        37's \AccelSheikhNHz equals it.  This is the provenance of the only
        externally sourced number in the abstract;
    S3  round 37's \AccelSheikhPct is the quotient of the NARROWER ceiling
        and that recommendation, so the paper quotes the least flattering
        figure, and it is below 100 per cent;
    S4  the equatorial rotational acceleration recomputed from a Jupiter's
        radius and rotation period agrees with round 37's \AccelJupRot, and
        \AccelJupPct is its share of the default ceiling;
    S5  the omitted rotational term is MATERIAL: added to the orbit the
        default ceiling was sized for it leaves every ceiling searched.
        ★ Note what this does NOT assert.  2.2 m s^-2 of equatorial rotation
        does not on its own exceed our ceiling of \AccelCeilLo--\AccelCeilHi,
        so rotation alone would have been searched; a check that said
        otherwise would fail on correct data, which is as useless as one
        that cannot fail.  What is true is that the ceiling was sized from
        ORBITAL acceleration alone and the sum leaves it, and the direction
        is reported either way;
    S6  the abstract states the sensitivity as conditional on the carrier
        being narrower than the instrumental channel, and carries the drift
        fraction (R1-3.2, M9);
    S7  the polarisation paragraph of \S6.3 says that Stokes I retains the
        FULL intensity of a circularly polarised carrier and that what is
        lost is discrimination and not sensitivity (minor 12);
    S8  the introduction states the costs of the band as well as its
        advantages, and names the beam the Earth must lie inside (minor 10).

Usage: `python3 prosegate_r15.py [--drive N]`.  Nothing is written.
"""
import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])

FAIL = []


def ck(label, ok, detail=''):
    print('%-5s %s%s' % ('PASS' if ok else 'FAIL', label,
                         '  [%s]' % detail if detail else ''))
    if not ok:
        FAIL.append(label)


def texval(name):
    """A macro's value as the macro layer defines it.  Last definition wins,
    which is the order TeX reads the round files in."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^}]*)\}'
                     % name)
    hit = None
    for fn in sorted(os.listdir(HERE)):
        if not re.match(r'survey_numbers_round\d+\.tex$', fn):
            continue
        for line in open(os.path.join(HERE, fn)):
            m = pat.search(line)
            if m and m.group(1).strip():
                hit = m.group(1)
    return hit


# --------------------------------------------------------------- the ceiling
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))


def nhz(row):
    """A window's frequency-normalised drift ceiling.  drift_max_Hz_s over the
    window's own mid frequency in GHz is Hz per second per GHz, and that is a
    nanohertz exactly, so no conversion factor is applied and none hidden."""
    lo, hi = float(row['flo_GHz']), float(row['fhi_GHz'])
    return float(row['drift_max_Hz_s']) / (0.5 * (lo + hi))


SPAN = sorted(nhz(r) for r in CAT)
if DRIVE == 1:
    #: S1 only: one window's ceiling halved, which moves the recomputed
    #: extreme without touching anything round 13 published.
    SPAN = sorted([SPAN[0] * 0.5] + SPAN[1:])

CEIL_LO, CEIL_HI = SPAN[0], SPAN[-1]
PUB_LO, PUB_HI = texval('DriftCeilLo'), texval('DriftCeilHi')

ck('S1 the nHz ceiling recomputed from the catalogue reproduces round 13',
   PUB_LO is not None and PUB_HI is not None
   and '%.1f' % CEIL_LO == PUB_LO and '%.1f' % CEIL_HI == PUB_HI,
   'recomputed %.1f--%.1f nHz over %d windows; round 13 prints %s--%s'
   % (CEIL_LO, CEIL_HI, len(SPAN), PUB_LO, PUB_HI))

# -------------------------------------------------- the published guideline
REC = json.load(open(os.path.join(HERE, 'r15inputs', 'prose',
                                  'sheikh2019_driftrange.json')))
if DRIVE == 2:
    #: S2 only: the record loses the sentence it was read from, which is what
    #: makes it a record rather than a number somebody remembered.
    REC = dict(REC)
    REC.pop('quotation')

GUIDE = float(REC['normalised_drift_nHz'])
PUB_GUIDE = texval('AccelSheikhNHz')
ck('S2 the recommendation is read from a frozen record carrying its own '
   'source, and round 37 prints that value',
   REC.get('quotation', '').strip() != ''
   and ('%g' % GUIDE) in REC.get('quotation', '')
   and REC.get('bibkey') and REC.get('doi')
   and PUB_GUIDE == '%g' % GUIDE,
   'record %g nHz from %s; round 37 prints %s'
   % (GUIDE, REC.get('reference', 'NOTHING'), PUB_GUIDE)) 

PCT = 100.0 * CEIL_LO / GUIDE
PUB_PCT = texval('AccelSheikhPct')
if DRIVE == 3:
    #: S3 only: the flattering end of the span taken as "the" fraction, which
    #: is what a reader would be misled by.
    PCT = 100.0 * CEIL_HI / GUIDE

ck('S3 the published fraction is the quotient at the NARROWER ceiling and is '
   'below 100 per cent',
   PUB_PCT is not None and 0.0 < PCT < 100.0
   and '%.0f' % PCT == PUB_PCT,
   'recomputed %.2f per cent of %g nHz (%.2f at the wider ceiling); round 37 '
   'prints %s' % (PCT, GUIDE, 100.0 * CEIL_HI / GUIDE, PUB_PCT))

# ------------------------------------------- a platform that is not reached
R_EQ_M = 71492e3                      # Jupiter equatorial radius, IAU 2015
P_ROT_S = 9.925 * 3600.0              # System III rotation period
JUP = (2.0 * math.pi / P_ROT_S) ** 2 * R_EQ_M
if DRIVE == 4:
    #: S4 only: the period taken as the sidereal DAY instead of the planet's
    #: rotation period, which is the slip this check exists to catch.
    JUP = (2.0 * math.pi / 86164.0) ** 2 * R_EQ_M

ACC_LO, ACC_HI = texval('AccelCeilLo'), texval('AccelCeilHi')
PUB_JUP, PUB_JUPPCT = texval('AccelJupRot'), texval('AccelJupPct')
ck('S4 the recomputed rotational acceleration and its share of the default '
   'ceiling agree with round 37',
   PUB_JUP is not None and PUB_JUPPCT is not None and ACC_LO is not None
   and abs(JUP - float(PUB_JUP)) / float(PUB_JUP) < 0.01
   and abs(100.0 * JUP / float(ACC_LO) - float(PUB_JUPPCT)) < 1.0,
   'recomputed %.2f m s^-2 = %.1f per cent of %s; round 37 prints %s and %s'
   % (JUP, 100.0 * JUP / float(ACC_LO), ACC_LO, PUB_JUP, PUB_JUPPCT))

JUP_S = JUP / 100.0 if DRIVE == 5 else JUP
ck('S5 the omitted rotational term is material: added to the orbit the '
   'default ceiling was sized for, it leaves every ceiling searched',
   ACC_LO is not None and ACC_HI is not None
   and float(ACC_LO) + JUP_S > float(ACC_HI),
   '%.2f + %.2f = %.2f against the largest ceiling searched %s; rotation '
   'ALONE %s it, so rotation by itself would have been searched'
   % (float(ACC_LO), JUP_S, float(ACC_LO) + JUP_S, ACC_HI,
      'exceeds' if JUP_S > float(ACC_HI) else 'does NOT exceed'))

# ------------------------------------------------------------------ S6 .. S8
#: Not numbers.  Three prose instructions of this round that a later edit
#: could quietly undo, asserted against the section files themselves.
SEC = os.path.join(HERE, 'sections')


def text(fn):
    return ' '.join(open(os.path.join(SEC, fn)).read().split())


ABS_T, DISC_T, INTRO_T = text('abstract.tex'), text('06_discussion.tex'), \
    text('01_intro.tex')
if DRIVE == 6:
    ABS_T = ABS_T.replace('narrower than', 'broader than')
if DRIVE == 7:
    DISC_T = DISC_T.replace('retains the full intensity', 'loses half')
if DRIVE == 8:
    INTRO_T = re.sub(r'Against that[^.]*\.', '', INTRO_T)

ck('S6 the abstract states the sensitivity as conditional on the carrier '
   'being narrower than the instrumental channel, and carries the drift '
   'fraction (R1-3.2, M9)',
   re.search(r'narrower than the (?:relevant )?instrumental channel', ABS_T)
   is not None
   and r'\AccelSheikhPct' in ABS_T and r'\DriftCeilLo' in ABS_T,
   'bandwidth clause %s; drift fraction %s'
   % ('present' if 'narrower than' in ABS_T else 'MISSING',
      'present' if r'\AccelSheikhPct' in ABS_T else 'MISSING'))

ck('S7 the polarisation paragraph says Stokes I retains the full intensity '
   'of a circularly polarised carrier and loses discrimination, not '
   'sensitivity (minor 12)',
   'retains the full intensity' in DISC_T and 'not sensitivity' in DISC_T
   and re.search(r'\(\\mathrm\{XX\}\+\\mathrm\{YY\}\)/2', DISC_T)
   is not None,
   'intensity clause %s; the expression %s'
   % ('present' if 'retains the full intensity' in DISC_T else 'MISSING',
      'present' if 'mathrm{XX}' in DISC_T else 'MISSING'))

ck('S8 the introduction states the costs of the band as well as its '
   'advantages, and names the beam the Earth must lie inside (minor 10)',
   re.search(r'Against that', INTRO_T) is not None
   and 'deliberately aimed' in INTRO_T and r'\BmArcsec' in INTRO_T,
   'balance %s; beam %s'
   % ('present' if 'Against that' in INTRO_T else 'MISSING',
      'present' if r'\BmArcsec' in INTRO_T else 'MISSING'))

print('prosegate_r15: %d check(s), %d FAILED' % (8, len(FAIL)))
if FAIL:
    sys.exit('prosegate_r15: FAILED %s' % FAIL)
