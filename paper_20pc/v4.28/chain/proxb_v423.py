#!/usr/bin/env python3
r"""proxb_v423.py -- whether the deepest stacked limit of this survey reaches
the one place in that system where a transmitter would plausibly be.

Round 961.  Writes `survey_numbers_round961.tex` and `proxb_v423.json`.

THE QUESTION, and it is a scientific one rather than a caveat.  The deepest
limit in the survey is Proxima Centauri's, and it is a stacked limit: sixty-six
epochs over six years added in the star's rest frame.  Adding epochs that way
assumes the emitter's stellar-frame frequency does not move between them, and
the tolerance is one coarse channel -- about twenty kilometres a second peak to
peak.  A transmitter on Proxima Centauri b does not satisfy that.  Its host
drags it round in eleven days at forty-seven kilometres a second, so unless the
orbit is seen nearly face-on the carrier walks across several channels between
our own epochs and the stack cancels it rather than building it.

WHAT IS COMPUTED HERE, all of it from the paper's own frozen inputs:
  * the orbital speed of each known planet of the host, from the period in the
    frozen exoplanet-archive query and the host mass in the frozen host table,
    by two independent routes that are required to agree;
  * the peak-to-peak line-of-sight excursion, 2 v sin i, against the tolerance
    the stack section already publishes;
  * the inclination at which the two are equal, and the fraction of randomly
    oriented orbits inside it;
  * THE SAME THING MEASURED ON OUR OWN EPOCHS rather than assumed: the 66
    stacked epoch times are read, folded on the planet's period, and the
    excursion they actually sample is evaluated at the least favourable
    orbital phase.  That turns "the limit does not apply" from a property of
    an idealised orbit into a property of this data set.
  * and the single-epoch limit, which DOES apply: the velocity a transmitter
    on that planet can gain inside the longest block that enters the stack,
    against the same one-channel tolerance.

Usage: proxb_v423.py [--drive N]
"""
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ v4.23: ROUND 20'S FALLBACK PATTERN, not a version pin.  This file was
# written outside the tree and read the frozen previous version; once it is
# adopted into a version directory that directory is both the input and the
# output, like every other generator here.  A bare absolute pin broke the
# build in round 20 when the predecessor was deleted, and `cleanregen.py`
# cannot see a cross-version dependency because the predecessor is always
# there while it runs.
PAPER = (HERE if os.path.exists(os.path.join(HERE, 'ledger.json'))
                else '/workspace/SETI/paper_20pc/v4.22')
ROUND = 961
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round961%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'proxb_v423%s.json' % SFX)

CKMS = 299792.458
C = CKMS * 1e3
GMSUN = 1.32712440018e20
AU = 1.495978707e11
HOST = 'Proxima Cen'

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-70s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def p(*a):
    return os.path.join(PAPER, *a)


def macro(name):
    """One macro's value out of the frozen layer of the paper, by name.  The
    layer uses both `\\newcommand` and the `\\providecommand{}{}\\renewcommand`
    idiom, sometimes two on one line, so the LAST definition on the line
    wins -- which is what TeX does too."""
    import glob
    import re
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{((?:[^{}]|\{[^{}]*\})*)\}'
                     % name)
    hit = None
    for q in sorted(glob.glob(p('survey_numbers*.tex'))):
        if '_drive' in q:
            continue
        for line in open(q):
            for mm in pat.finditer(line):
                if mm.group(1) != '':
                    hit = mm.group(1)
    if hit is None:
        raise KeyError(name)
    return hit


def texfloat(s):
    """A macro written as LaTeX scientific notation, as a float."""
    import re
    mm = re.search(r'([0-9.]+)\s*\\times\s*10\^\{?(-?[0-9]+)\}?', s)
    if mm:
        return float(mm.group(1)) * 10.0 ** int(mm.group(2))
    return float(re.sub(r'[^0-9.eE+-]', '', s))


# ---------------------------------------------------------------- inputs
PLAN = json.load(open(p('planet_periods_v361.json')))
HMASS = json.load(open(p('host_masses_v385.json')))
# ★ The frozen group file carries each group several times over (it is an
# accumulation of runs), and it carries both the census-only subset and the
# whole-archive set.  Rows are therefore deduplicated on their content and the
# one whose block count is the published one is taken; the count of distinct
# groups for the host is reported so the choice is visible.
_graw = [g for g in json.load(open(p('stack_v408', 'groups3.json')))
         if g['skey'] == HOST]
_gseen, GALL = set(), []
for _g in _graw:
    _k = (_g['band'], _g['chanw'], _g['n_block'], round(_g['mjd_min'], 6))
    if _k in _gseen:
        continue
    _gseen.add(_k)
    GALL.append(_g)
GRP = [g for g in GALL if int(g['n_block']) == int(macro('StkProxN'))]
WIN = json.load(open(p('stack_v408', 'windows.json')))
RES = [json.loads(l) for l in open(p('stack_v408', 'stack6_result.jsonl'))]

assert len(GRP) == 1, 'the host must form one stacked group'
G = GRP[0]
SEL = [r for r in WIN if r['path'] in set(G['paths'])]
DEEP = [r for r in RES if r['skey'] == HOST and r['band'] == G['band']
        and int(r['N']) == int(macro('StkProxN'))]
assert DEEP, 'no stack record with the published block count'
D = DEEP[0]
# the result file holds several realisations of the same stack; they must
# agree on WHICH observations were combined, which is all that is used here.
assert len({(int(r['N']), round(r['span_d'], 3)) for r in DEEP}) == 1, \
    'the stack records with that block count must combine the same epochs'

MJD = np.array(sorted(r['mjd'] for r in SEL))
DWELL = [r['t_max'] - r['t_min'] for r in SEL]
CHANW = float(G['chanw'])
# the frequency the tolerance is read at: the centre of the stellar-frame
# coverage the group's epochs have in common, which is a property of the
# stacked set and not of one realisation's peak channel.
NUSTACK = 0.5 * (float(G['sf_common_lo']) + float(G['sf_common_hi']))

m('PxHost', 'Proxima Centauri')
m('PxNGroupRaw', '%d' % len(_graw))
m('PxNGroupDistinct', '%d' % len(GALL))
m('PxNEpoch', '%d' % len(SEL))
m('PxSpanYr', '%.1f' % ((MJD.max() - MJD.min()) / 365.25))
m('PxMassMsun', '%.3f' % HMASS[HOST])
m('PxDwellMaxS', '%.0f' % max(DWELL))
m('PxDwellMedS', '%.0f' % float(np.median(DWELL)))

# ★★★★ X1 -- THE TOLERANCE IS ONE CHANNEL AS A VELOCITY, AND IT IS THE
# SECTION'S OWN PUBLISHED NUMBER.  Recomputing it from the channel width and
# the stacked spectrum's own frequency, and requiring it to reproduce the
# macro, means everything below is set against the paper's own tolerance and
# not against a tolerance invented here.  The identity asserted is
# Delta_v = c Delta_nu / nu, which stays true whatever the channel is.
TOL = CKMS * CHANW / NUSTACK
if DRIVE == 1:                      # X1: the tolerance read at the wrong band
    TOL = CKMS * CHANW / 1.0e12
_pub = float(macro('StkProxTolKms'))
ck('X1 the peak-to-peak tolerance the stack section publishes is one channel '
   'of the stacked spectrum expressed as a velocity, c dnu/nu, at that '
   "spectrum's own frequency",
   abs(TOL - _pub) < 0.05 * _pub,
   'recomputed %.2f km/s from a %.3f MHz channel at %.3f GHz against the '
   'published %.1f' % (TOL, CHANW / 1e6, NUSTACK / 1e9, _pub))
m('PxTolKms', '%.1f' % TOL)

# ---------------------------------------------------------------- the planets
# ★★★ EVERY KNOWN PLANET OF THE HOST, from the frozen archive query, so the
# generator cannot choose the one that makes the point.
PLANETS = sorted((r for r in PLAN if r['hostname'] == HOST),
                 key=lambda r: r['pl_orbper'])
assert PLANETS, 'the frozen planet list must name at least one'
GM = GMSUN * float(HMASS[HOST])
ROWS = []
for q in PLANETS:
    Pd = float(q['pl_orbper'])
    Ps = Pd * 86400.0
    # two routes to the same speed, from the period and the host mass alone
    a = (GM * Ps ** 2 / (4.0 * math.pi ** 2)) ** (1.0 / 3.0)
    v1 = 2.0 * math.pi * a / Ps
    v2 = math.sqrt(GM / a)
    if DRIVE == 6:                  # X2: one route computed from a wrong law
        v2 = math.sqrt(GM / (2.0 * a))
    v = 0.5 * (v1 + v2)
    amax = v * 2.0 * math.pi / Ps            # max line-of-sight acceleration
    pp = 2.0 * v / 1e3                       # peak to peak at sin i = 1
    sini = TOL / pp
    sini_c = min(1.0, sini)
    inc = math.degrees(math.asin(sini_c))
    piso = 1.0 - math.sqrt(max(0.0, 1.0 - sini_c ** 2))
    # ★★★★ AND THE SAME THING ON OUR OWN EPOCHS.  The phase of the orbit is
    # not known, so the excursion the epochs sample is evaluated at the
    # orbital phase LEAST favourable to this argument -- the reference time
    # that minimises it -- and that minimum is what is published.
    t0 = np.linspace(0.0, Pd, 4001)
    ss = np.sin(2.0 * np.pi * (MJD[None, :] - t0[:, None]) / Pd)
    span = ss.max(axis=1) - ss.min(axis=1)
    frac = float(span.min()) / 2.0
    if DRIVE == 2:                  # X4: epochs that sample almost no phase
        frac = 1e-4
    ROWS.append(dict(name=q['pl_name'], P_d=Pd, a_au=a / AU, v_kms=v / 1e3,
                     v_resid=abs(v1 - v2) / v, amax=amax, pp_kms=pp,
                     sini_max=sini, inc_max_deg=inc, p_iso=piso,
                     frac_sampled=frac,
                     pp_sampled_kms=pp * frac,
                     sini_sampled=TOL / (pp * frac),
                     dv_block_kms=amax * max(DWELL) / 1e3,
                     dv_block_frac=amax * max(DWELL) / 1e3 / TOL))

ck('X2 the orbital speed follows from the period and the host mass alone, '
   'and the two independent routes to it -- the circumference over the '
   'period, and the circular-orbit speed at the implied radius -- agree',
   max(r['v_resid'] for r in ROWS) < 1e-9,
   '%d planets of %s; largest fractional disagreement %.2e; speeds %s km/s'
   % (len(ROWS), HOST, max(r['v_resid'] for r in ROWS),
      ', '.join('%.1f' % r['v_kms'] for r in ROWS)))

B = [r for r in ROWS if r['name'].endswith(' b')][0]
m('PxPlanet', B['name'].replace('Proxima Cen', 'Proxima Centauri'))
m('PxPorbD', '%.3f' % B['P_d'])
m('PxAau', '%.4f' % B['a_au'])
m('PxVorbKms', '%.0f' % B['v_kms'])
m('PxPPKms', '%.0f' % B['pp_kms'])
m('PxSiniMax', '%.2f' % B['sini_max'])
m('PxIncMaxDeg', '%.0f' % B['inc_max_deg'])
m('PxIsoPct', '%.1f' % (100.0 * B['p_iso']))
m('PxFracSampled', '%.0f' % (100.0 * B['frac_sampled']))
m('PxNChanWalk', '%.0f' % (B['pp_kms'] / TOL))
m('PxAmaxMs', '%.2f' % B['amax'])

# ★★★★ X3 -- THE INCLINATION BOUND IS AN IDENTITY AND NOT A FIT.  It is
# exactly "the peak-to-peak excursion equals the tolerance", and the
# probability is exactly 1 - cos(i) for isotropic orientation.  Both forms are
# evaluated and required to close, so the bound cannot drift away from its own
# definition.
_id = all(abs(2.0 * r['v_kms'] * r['sini_max'] - TOL) < 1e-6 * TOL
          and abs(r['p_iso']
                  - (1.0 - math.cos(math.radians(r['inc_max_deg'])))) < 1e-6
          for r in ROWS if r['sini_max'] <= 1.0)
if DRIVE == 3:                      # X3: the bound detached from its meaning
    _id = False
ck('X3 the inclination bound is exactly the inclination at which the '
   'peak-to-peak excursion equals the tolerance, and the quoted fraction of '
   'orientations is exactly one minus its cosine',
   _id,
   '; '.join('%s sin i <= %.3f (i <= %.1f deg, %.1f per cent of isotropic '
             'orientations)' % (r['name'], r['sini_max'], r['inc_max_deg'],
                                100.0 * r['p_iso']) for r in ROWS))

# ★★★★ X4 -- AND IT IS A STATEMENT ABOUT OUR OWN EPOCHS.  A peak-to-peak
# excursion only matters if the epochs sample it; these do, and the fraction
# is measured at the orbital phase least favourable to the argument.
_ok = all(r['frac_sampled'] > 0.5 for r in ROWS)
ck('X4 the stacked epochs sample most of the excursion whatever the orbital '
   'phase, so the limit\'s failure to cover the planet is measured on this '
   'data set and not assumed from the orbit',
   _ok,
   '%d epochs over %.1f yr; at the least favourable phase they sample %s of '
   'the full peak-to-peak excursion'
   % (len(SEL), (MJD.max() - MJD.min()) / 365.25,
      ', '.join('%s %.1f per cent' % (r['name'], 100.0 * r['frac_sampled'])
                for r in ROWS)))

# ★★★★ X5 -- THE LIMIT THAT DOES APPLY.  Inside one block the same transmitter
# gains at most amax * dwell, and that is a small fraction of the same
# channel, so the single-epoch limit covers the planet at any inclination.
# This is the sentence the paper has to point to, and it has to be measured on
# the longest block that actually enters the stack.
_sing = texfloat(macro('StkProxEirpSingle'))
# ★ r27 row 58 (Ruling 25): the stacked figure the paper prints is the
# census-only one; the archive-wide \StkProxEirpCal left the main text, so X5
# compares the single-epoch limit with the census stack.
_stack = texfloat(macro('SzProxEirpCensus'))
_frac = B['dv_block_frac']
if DRIVE == 4:                      # X5: a dwell as long as the orbit
    _frac = B['amax'] * B['P_d'] * 86400.0 / 1e3 / TOL
ck('X5 inside a single block the same transmitter stays well inside one '
   'channel, so the single-epoch limit applies at every inclination while '
   'the stacked one does not, and the single-epoch limit is the shallower of '
   'the two',
   _frac < 0.25 and _sing > _stack,
   'longest stacked block %.0f s; at %.3f m/s2 that is %.2f km/s, %.1f per '
   'cent of the %.1f km/s channel; single-epoch %.2e W against stacked '
   '%.2e W' % (max(DWELL), B['amax'], B['dv_block_kms'], 100.0 * _frac, TOL,
               _sing, _stack))
m('PxBlockDvKms', '%.1f' % B['dv_block_kms'])
m('PxBlockPct', '%.0f' % (100.0 * B['dv_block_frac']))
m('PxEirpSingle', macro('StkProxEirpSingle'))
m('PxEirpStack', macro('SzProxEirpCensus'))
m('PxEirpRatio', '%.1f' % (_sing / _stack))

# ★★ X6 -- EVERY PLANET, NOT THE CONVENIENT ONE.  The inner planet of the two
# is worse, so the conclusion is not an artefact of choosing b.
OUTER = [r for r in ROWS if r is not B]
m('PxNPlanet', '%d' % len(ROWS))
m('PxPlanetList', ', '.join(r['name'].split()[-1] for r in ROWS))
m('PxWorstPlanet', min(ROWS, key=lambda r: r['sini_max'])['name'].split()[-1])
m('PxWorstSini', '%.2f' % min(r['sini_max'] for r in ROWS))
ck('X6 the conclusion is not an artefact of choosing one planet: every known '
   'planet of the host is evaluated and the bound on sin i is at most the '
   "one quoted for the planet the text names",
   len(ROWS) == len([q for q in PLAN if q['hostname'] == HOST])
   and all(r['sini_max'] <= B['sini_max'] + 1e-9 for r in ROWS)
   if DRIVE != 5 else False,
   '%d planets in the frozen archive query: %s'
   % (len(ROWS),
      '; '.join('%s P=%.3f d, sin i <= %.3f'
                % (r['name'], r['P_d'], r['sini_max']) for r in ROWS)))

# ★ X7 -- THE EPOCHS READ ARE THE EPOCHS STACKED.  The group's own member list
# is used, and its count has to be the published one; otherwise this whole
# calculation could be about a different set of observations.
ck('X7 the epochs folded here are exactly the epochs the published stack '
   'combines',
   len(SEL) == len(set(G['paths'])) == int(G['n_block'])
   == int(D['N']) == int(macro('StkProxN')) if DRIVE != 7 else
   len(SEL[:-1]) == int(macro('StkProxN')),
   '%d paths matched, group says %s blocks, stack record says %s, the paper '
   'says %s' % (len(SEL), G['n_block'], D['N'], macro('StkProxN')))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by proxb_v423.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
json.dump(dict(generator='proxb_v423.py', round=ROUND, drive=DRIVE,
               tol_kms=TOL, chanw=CHANW, nu_stack=NUSTACK,
               n_epoch=len(SEL), planets=ROWS, macros=dict(M),
               failures=FAIL), open(OUTJ, 'w'), indent=1)
print('\n%d macros, %d planets, %d failures %s'
      % (len(M), len(ROWS), len(FAIL), FAIL))
sys.exit(1 if FAIL and DRIVE == 0 else 0)
