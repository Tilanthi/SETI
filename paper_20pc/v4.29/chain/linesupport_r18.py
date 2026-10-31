#!/usr/bin/env python3
r"""Round 820: attribution is not identification -- the split of the
line-attributed crossings into those with support beyond the frequency
coincidence and those resting on the coincidence alone; and the ALMA Band 5
coverage of this survey, which is what decides whether the positronium
hyperfine frequency of the earlier searches was reachable here.

WHY THIS FILE EXISTS

Referee 1's fifth point is that a catalogued-transition coincidence inside a
+-50 km/s interval is an attribution and not an identification, so the
categorical claim that line emission produces every astrophysical false
positive is stronger than the evidence.  The counts do not move; what moves
is the evidential language, and that needs the split MEASURED rather than
asserted.  Three routes to support beyond the coincidence are available in
records this survey already holds, and each is read here:

  RECURRENCE  the predicted cell is occupied again in a later execution
              block (maskso_v414.json, verdict 'recovered');
  TRANSITION  the same star carries an attributed crossing of a DIFFERENT
              transition of the same species (ledger.json);
  GAS         an external CO survey detects gas on that sightline at the
              crossing's own LSR velocity (masklsr_v520.json cloud_matches;
              Dame & Thaddeus composite, Planck elsewhere).

A crossing with none of the three rests on the frequency coincidence alone.
For those the absence must itself be measured, not merely unrecorded: the
CO data must either cover the sightline or carry an upper limit on it, or
the "no gas" half of the statement is an absence of evidence.  A3 requires
exactly that.

AND THE BAND 5 QUESTION, WHICH THE REFEREE GOT HALF RIGHT

Referee 2's first minor point is right that 203 GHz (the positronium ground
state hyperfine splitting, the frequency of both earlier nearby-star
searches) lies inside ALMA Band 5, 163-211 GHz, so the manuscript's claim
that no magic frequency falls in an ALMA band is false.  Its proposed
remedy -- "state that the archive holds no searched Band 5 coverage of these
stars" -- is ALSO false: the census holds Band 5 windows, and writing the
referee's sentence would replace one error with another.  What is true is
measured here: the Band 5 coverage is small, is toward one star only, and
does not include the positronium frequency.

ASSERTIONS (each driven; see --drive)
    A1  the supported and coincidence-only sets partition the attributed
        crossings, are disjoint, and sum to the published \MkAttr; and
        neither is empty, so the split is not a distinction without a case
    A2  every supported crossing names at least one route, and every route
        is occupied by at least one crossing, so no route is decorative
    A3  no coincidence-only crossing satisfies any route, AND the CO data
        constrain its sightline (covered, or carrying a Planck limit), so
        the absence of gas there is a measurement and not a gap
    A4  the positronium frequency of the earlier searches lies inside the
        Band 5 edges, the census holds Band 5 windows, and none of them
        covers that frequency
    A5  the Band 5 window set read from the delivered band label is the same
        set read from the frequency edges -- two independent keys on the
        same catalogue

    python3 linesupport_r18.py [--drive N]      N in 1..7

-> survey_numbers_round820.tex, linesupport_r18.json   (written beside THIS
   file, never into the paper tree)
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The generator reads the paper's own records.  In the integrated tree this
#: file sits beside them and reads its own directory; in a wave-1 sandbox the
#: paper tree is READ-ONLY and is read from there.  Output always goes to
#: HERE, so no run of this file in a sandbox can write a path the build
#: reads.
PAPER = (HERE if os.path.exists(os.path.join(HERE, 'ledger.json'))
         else os.path.abspath(os.path.join(HERE, '..', '..',
                                           'paper_20pc', 'v4.18')))
ROUND = 820
#: ALMA Band 5, ALMA Technical Handbook; the same edges make_figures_v328.py
#: and sens_r14.py carry.
BAND5_GHZ = (163.0, 211.0)
#: Positronium ground-state hyperfine splitting, 203.3942 GHz
#: (Ishida et al. 2014), rounded as the manuscript's \SbPriorFreqGHz is.
PS_GHZ = 203.3942
_W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
      'nine', 'ten')


def _load(*p):
    return json.load(open(os.path.join(PAPER, *p), encoding='utf-8'))


def texval(name):
    """The value of a published macro, read from the round files."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^{}]*)\}'
                     % name)
    v = None
    for f in sorted(glob.glob(os.path.join(PAPER, 'numbers/survey_numbers*.tex'))):
        if '_drive' in os.path.basename(f):
            continue
        for m in pat.finditer(open(f, encoding='utf-8').read()):
            if m.group(1).strip():
                v = m.group(1).strip()
    return v


def tname(s):
    """The ledger's display name, with the spaces the paper does not break."""
    return s.replace(' ', '~')


def designation(name, tex=False):
    """The paper's own name resolver, so a lookup keyed on a star name uses
    the same key every other tool here uses.

    ★ THE LEDGER'S STAR KEY IS NOT THE CO RECORDS' KEY.  The ledger carries
    `HIP10679` where the line-of-sight records carry `HIP 10679`, so a join
    on the raw string silently drops that star -- which is the defect family
    that has bitten this project fourteen times, and A3 caught it here on
    its first run.  Every name join in this file goes through this function
    and is asserted to resolve.
    """
    if PAPER not in sys.path:
        sys.path.insert(0, PAPER)
    import star_alias as sa
    return sa.designation(name, tex=True) if tex else sa.designation(
        name, tex=False)


def enumerate_list(items):
    items = list(items)
    if not items:
        return 'none'
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + ' and ' + items[-1]


def species(line):
    """The carrier of a transition name: 'CO(2-1)' -> 'CO'.

    Keyed on the catalogue string the ledger carries, so two rows of the
    same species are recognised whatever their quantum numbers.
    """
    return re.split(r'[(\s]', line.strip(), maxsplit=1)[0]


def main(argv):
    drive, driven = 0, False
    for i, a in enumerate(argv):
        if a == '--drive':
            drive, driven = int(argv[i + 1]), True
    suf = '_drive%d' % drive if driven else ''
    fail = []

    def ck(name, cond, detail=''):
        if not cond:
            fail.append('%s: %s' % (name, detail))
        print('  %-3s %s  %s' % (name.split()[0], 'PASS' if cond else 'FAIL',
                                 detail))

    M, D = {}, {}

    def m(k, v):
        assert k.isalpha(), k          # a macro name may hold letters only
        assert k not in M, k
        M[k] = str(v)

    LED = _load('ledger.json')['rows']
    REC = {(r['eb'], round(r['freq_GHz'], 6)): r
           for r in _load('maskso_v414.json')['recurrence']}
    CLOUD = _load('masklsr_v520.json')['cloud_matches']
    CFA = _load('r15inputs', 'co_dht_r15.json')['los']
    PLANCK = _load('r15inputs', 'co_planck_r15.json')['los']
    CAT = list(csv.DictReader(open(os.path.join(
        PAPER, 'per_target_results_v3.99.csv'), encoding='utf-8')))

    att = [r for r in LED if r['attributed']]
    cloud_keys = {(c['eb'], round(c['freq'], 6)) for c in CLOUD}
    if drive == 3:                     # a sightline with no CO record at all
        CFA = {k: v for k, v in CFA.items() if k != 'HIP 10679'}
        PLANCK = {k: v for k, v in PLANCK.items() if k != 'HIP 10679'}

    # ------------------------------------------------- the three routes
    # TRANSITION: another attributed crossing of the same species at the same
    # star, on a DIFFERENT transition.  Keyed on the star's ledger name and
    # the catalogue transition string, never on a display name.
    bystar = {}
    for r in att:
        bystar.setdefault(r['star'], []).append(r)

    rows = []
    for r in att:
        key = (r['eb'], round(r['freq'], 6))
        rec = REC.get(key, {})
        routes = []
        if rec.get('verdict') == 'recovered':
            routes.append('recurrence')
        sibs = {x['line'] for x in bystar[r['star']]
                if species(x['line']) == species(r['line'])}
        if len(sibs) > 1:
            routes.append('transition')
        if key in cloud_keys:
            routes.append('gas')
        if drive == 1 and r is att[0]:         # a row in neither set
            routes = ['bogus']
        if drive == 2 and routes:              # a supported row with no route
            routes = []
        rows.append(dict(star=r['star'], display=r['display'], eb=r['eb'],
                         freq=r['freq'], line=r['line'], tstar=r['tstar'],
                         dv_stellar=r['dv_stellar'], routes=routes))

    KNOWN = ('recurrence', 'transition', 'gas')
    supp = [x for x in rows if any(q in KNOWN for q in x['routes'])]
    alone = [x for x in rows if not x['routes']]

    n_att = texval('MkAttr')
    ck('A1 the two sets partition the attributed crossings and sum to the '
       'published attributed count, and neither is empty',
       len(supp) + len(alone) == len(att) == int(n_att)
       and not ({id(x) for x in supp} & {id(x) for x in alone})
       and len(supp) > 0 and len(alone) > 0,
       '%d supported + %d coincidence-only = %d of %s attributed'
       % (len(supp), len(alone), len(supp) + len(alone), n_att))

    occupied = {q for x in supp for q in x['routes']}
    ck('A2 every supported crossing names a route and every route is '
       'occupied',
       all(x['routes'] for x in supp) and occupied == set(KNOWN),
       'routes occupied %s' % sorted(occupied))

    constrained = []
    for x in alone:
        los = designation(x['star'])
        c, p = CFA.get(los), PLANCK.get(los)
        covered = bool(c and c.get('covered'))
        limited = p is not None and 'w_co_cone_max' in p
        constrained.append(covered or limited)
    ck('A3 no coincidence-only crossing satisfies a route, and the CO data '
       'constrain each of their sightlines',
       all(not x['routes'] for x in alone) and all(constrained)
       and len(alone) == len(constrained),
       '%d coincidence-only, %d with CO coverage or a limit'
       % (len(alone), sum(constrained)))

    # ------------------------------------------------------- Band 5
    # drive 4 puts the frequency outside Band 5; drive 6 puts it inside a
    # window the census searched.  The two halves of A4 are different
    # claims and each has to be able to fail on its own.
    ps = PS_GHZ + (12.0 if drive == 4 else 0.0)   # 215.4 GHz: outside Band 5
    if drive == 6:
        ps = 196.0                                # inside a searched window
    b5_edge, b5_label, b5_cls = [], [], []
    for r in CAT:
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        band = str(r['band']).strip()
        cls = r['search_class'].strip()
        if drive == 5 and lo > BAND5_GHZ[0] and hi < BAND5_GHZ[1]:
            band = '6'
        if drive == 7 and band == '5':
            cls = 'A'
        if hi > BAND5_GHZ[0] and lo < BAND5_GHZ[1]:
            b5_edge.append((r['star_name'], lo, hi))
            b5_cls.append(cls)
        if band == '5':
            b5_label.append((r['star_name'], lo, hi))
    covers_ps = [x for x in b5_edge if x[1] <= ps <= x[2]]

    ck('A4 the positronium frequency lies inside the Band 5 edges, the '
       'census holds Band 5 windows, and none covers it',
       BAND5_GHZ[0] < ps < BAND5_GHZ[1] and len(b5_edge) > 0
       and not covers_ps,
       '%.4f GHz in (%.0f, %.0f): %s; %d Band 5 windows; %d covering'
       % (ps, BAND5_GHZ[0], BAND5_GHZ[1],
          BAND5_GHZ[0] < ps < BAND5_GHZ[1], len(b5_edge), len(covers_ps)))

    ck('A5 the Band 5 set is the same read from the delivered band label '
       'and from the frequency edges',
       sorted(b5_edge) == sorted(b5_label) and len(b5_label) > 0,
       '%d by edges, %d by label' % (len(b5_edge), len(b5_label)))

    ck('A6 every Band 5 window the census holds is a coarse-channel one, so '
       'none of them could carry the carrier search',
       bool(b5_cls) and set(b5_cls) == {'B'},
       'search classes %s' % sorted(set(b5_cls)))

    # ------------------------------------------------------- the macros
    # ★ ONLY WHAT THE PROSE CITES IS A MACRO.  The per-route counts and the
    # Band 5 extent are evidence for the report and stay in the json: an
    # emitted macro no sentence cites is an orphan, and this tree retires
    # orphans.
    m('LnAttrSupp', len(supp))
    m('LnAttrCoinc', len(alone))
    m('LnAttrCoincWord', _W[len(alone)] if len(alone) < len(_W)
      else len(alone))
    m('LnCoincStars', enumerate_list(
        sorted({tname(x['display']) for x in alone})))
    m('LnBFiveWin', len(b5_edge))
    m('LnBFiveStars', enumerate_list(
        sorted({tname(designation(x[0], tex=True)) for x in b5_edge})))
    D['n_coincidence_only'] = len(alone)
    D['n_recurrence'] = sum(1 for x in rows if 'recurrence' in x['routes'])
    D['n_second_transition'] = sum(1 for x in rows
                                   if 'transition' in x['routes'])
    D['n_catalogued_gas'] = sum(1 for x in rows if 'gas' in x['routes'])
    D['band5_GHz'] = '%.2f' % sum(hi - lo for _, lo, hi in b5_edge)
    D['coincidence_only'] = [
        '%s %s %s %+.1f km/s T*=%.2f' % (x['display'], x['eb'], x['line'],
                                         x['dv_stellar'], x['tstar'])
        for x in alone]
    D['band5'] = ['%s %.3f-%.3f' % (s, lo, hi) for s, lo, hi in b5_edge]
    D['positronium_GHz'] = PS_GHZ

    OUT = os.path.join(HERE, 'numbers/survey_numbers_round820%s.tex' % suf)
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('%%%% GENERATED by linesupport_r18.py -- do not hand-edit.\n')
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
    json.dump(dict(generator='linesupport_r18.py', round=ROUND, drive=drive,
                   macros=M, diagnostics=D, failed=fail, rows=rows),
              open(os.path.join(HERE, 'linesupport_r18%s.json' % suf), 'w'),
              indent=1)
    print('%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
