#!/usr/bin/env python3
r"""tuned_r28.py -- is the line mask's rule "the species the observers tuned
for"?  Measured from the observers' own spectral setups.  Round 2870.

WHY THIS EXISTS (referee round 28, Referee 2 M3; Ruling R3)
    Through v4.28 the mask left sulphur monoxide out of a query of twelve
    species on a debris-disc criterion ("no debris disc has a reported SO
    detection") that held for no other species: HCN, HCO+, CS, CN, SiO and
    H2CO have no debris-disc detection either.  The referee offered two
    consistent rules: (i) every species these setups cover that is detected
    in discs or molecular clouds -- SO included; or (ii) "species the
    observers tuned for", if it can be shown that SO was not tuned for.
    Rule (ii) is a claim about the mask that can be MEASURED: if the mask
    were the observers' tuning, the transitions it masks inside a window
    would be the ones that window was set up for.  This file measures it.

WHAT IT READS
    `r28inputs/tuned_r28.json` -- frozen.  For every census Class A window,
    the transition names the observers attached to the spectral window that
    holds it, from the ALMA pipeline weblog's spectral-setup page (the
    SOURCE-table "Transitions" the scheduling block carried), streamed from
    each member OUS's auxiliary tarball.  Deliveries older than the weblog
    page carry none and are counted as unknown, never as untuned.
    `maskcat_v412` (the mask, as a module) and the window catalogue.

WHAT IT EMITS (survey_numbers_round2870.tex)
    \TuNWin, \TuNWinSetup       windows, and those with a readable setup
    \TuNPair, \TuNPairTuned,    (window, masked species inside it) pairs with
    \TuPairPct                  a readable setup, and how many of them the
                                observers tuned for
    \TuNSOWin, \TuNSOTuned      windows holding an SO transition, and how many
                                were set up for SO
    \TuNUntunedSpec, \TuUntunedSpecList
                                masked species found inside a window that
                                was NOT set up for them at least once, other
                                than SO -- what rule (ii) would also drop

CHECKS (each driven to fail, --drive N writes *_driveN only)
    T1  the windows read are the published Class A census: \NWinA of them,
        matched one-to-one on block and frequency.          drive 1
    T2  the parser recognises the species it is looking for: at least one
        window's setup names CO and is counted as tuned for CO, so a zero
        below cannot be a parser that recognises nothing. drive 2
    T3  the species counted are the mask's: every species of the measured
        pairs is a species of `maskcat_v412.MASK`, and the mask is the whole
        query (one rule for every species).                  drive 3
    T4  THE MEASUREMENT RULE (ii) WOULD NEED, stated as a measurement and not
        pinned: the share of masked pairs that were tuned for is published
        whatever it is, and the clause asserts only that it is a share of a
        non-empty set and that the SO counts are a subset of it.  drive 4

    python3 tuned_r28.py [--drive N]
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 2870
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
sys.path.insert(0, HERE)
import maskcat_v412 as mc                                       # noqa: E402

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert not any(x[0] == k for x in M), k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-64s %s  %s' % (name[:64], 'PASS' if cond else 'FAIL', detail))


def macro(name):
    import glob
    pat = re.compile(r'\\(?:new|renew)command\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(HERE, 'numbers/survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for ln in open(p, encoding='utf-8'):
            mm = pat.search(ln.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


# Observer transition names are free text typed into the Observing Tool
# ("CO_v=0_3-2", "Continuum___CO_2_1_", "13CO", "Cont___SiO_5_4").  A species
# is recognised by a WHOLE TOKEN, so SO2, 34SO and H13CO+ are not the named
# species -- the rarer isotopologues are outside the twelve (maskcat M5).
TOK = {'CO': 'CO', '12CO': 'CO', 'C16O': 'CO', '13CO': '13CO', 'C18O': 'C18O',
       'HCN': 'HCN', 'HCO+': 'HCO+', 'HCOp': 'HCO+', 'CS': 'CS', 'CN': 'CN',
       'SiO': 'SiO', 'H2CO': 'H2CO', 'SO': 'SO', 'CI': 'CI', '[CI]': 'CI',
       'C-atom': 'CI'}


def species(name):
    n = re.sub(r'\(ID=\d+\)', '', name).strip()
    out = set()
    for t in re.split(r'[_\s]+', n):
        t0 = t if t.startswith('[') else re.split(r'[(\[]?v=|\(', t)[0]
        if t0 in TOK:
            out.add(TOK[t0])
        if re.fullmatch(r'H\d+(alpha|a)', t0):
            out.add('H')
    return out


TUN = json.load(open(os.path.join(HERE, 'r28inputs', 'tuned_r28.json'),
                     encoding='utf-8'))
CAT = [r for r in csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'), encoding='utf-8'))
    if r['resolution_class'] == 'fine']
MASK = mc.MASK
if DRIVE == 3:
    MASK = dict(MASK, **{'XYZ(1-0)': dict(f=230.0, spec='XYZ')})

# ---- T1 the windows are the census Class A windows -----------------------
def wkey(eb, lo, hi):
    lo, hi = sorted((float(lo), float(hi)))
    return (eb, round(lo, 5), round(hi, 5))


W = TUN['windows'][1:] if DRIVE == 1 else TUN['windows']
KC = sorted(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']) for r in CAT)
KT = sorted(wkey(w['eb'], w['flo_GHz'], w['fhi_GHz']) for w in W)
ck('T1 the windows read are the published Class A census, one-to-one',
   KC == KT and len(KC) == int(macro('NWinA')),
   '%d frozen against %d catalogued, \\NWinA %s'
   % (len(KT), len(KC), macro('NWinA')))

# ---- the pairs ------------------------------------------------------------
pairs = []                     # (window, species inside, tuned?)
nset = 0
for w in W:
    lo, hi = sorted((float(w['flo_GHz']), float(w['fhi_GHz'])))
    inside = sorted({v['spec'] for v in MASK.values() if lo <= v['f'] <= hi})
    if not w['have_setup']:
        continue
    nset += 1
    tuned = set()
    for n in w['observer_transitions']:
        tuned |= species(n)
    if DRIVE == 2:
        tuned = set()
    for sp in inside:
        pairs.append((w, sp, sp in tuned))
co_ok = any(sp == 'CO' and t for _w, sp, t in pairs)
ck('T2 the parser recognises a species the observers name (CO is counted '
   'as tuned somewhere), so a zero below is a measurement',
   co_ok, '%d CO pairs tuned' % sum(1 for _w, sp, t in pairs
                                     if sp == 'CO' and t))
specs = {sp for _w, sp, _t in pairs}
ck('T3 the species counted are the mask\'s, and the mask is the whole query',
   specs <= {v['spec'] for v in mc.MASK.values()}
   and len(mc.MASK) == len(mc.MASK_ALL) and not mc.NOT_MASKED,
   '%d species in the pairs; mask %d of %d transitions'
   % (len(specs), len(mc.MASK), len(mc.MASK_ALL)))

so = [(w, t) for w, sp, t in pairs if sp == 'SO']
untuned = sorted({sp for _w, sp, t in pairs if not t and sp != 'SO'})
ntun = sum(1 for _w, _sp, t in pairs if t)
_t4 = len(pairs) > 0 and 0 <= ntun <= len(pairs) and len(so) <= len(pairs)
if DRIVE == 4:
    _t4 = False
ck('T4 the tuned share is a share of a non-empty set of masked pairs and the '
   'SO windows are among them (reported, not pinned)', _t4,
   '%d of %d pairs tuned (%.0f%%); SO in %d windows, tuned in %d; other '
   'species masked somewhere untuned: %s'
   % (ntun, len(pairs), 100.0 * ntun / max(1, len(pairs)), len(so),
      sum(1 for _w, t in so if t), untuned))

per = {}
for _w, sp, t in pairs:
    a = per.setdefault(sp, [0, 0])
    a[0] += 1
    a[1] += int(t)
for sp in sorted(per):
    print('    %-5s inside %3d windows, tuned in %3d' % (sp, per[sp][0],
                                                       per[sp][1]))

TEXNAME = {s[0]: s[3] for s in mc.SPECIES}
TEXNAME['H'] = 'hydrogen recombination'


def _list(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


m('TuNWin', len(W))
m('TuNWinSetup', nset)
m('TuNPair', len(pairs))
m('TuNPairTuned', ntun)
m('TuPairPct', '%.0f' % (100.0 * ntun / max(1, len(pairs))))
m('TuNSOWin', len(so))
m('TuNSOTuned', sum(1 for _w, t in so if t))
m('TuNUntunedSpec', len(untuned))
m('TuUntunedSpecList', _list([TEXNAME[s] for s in untuned]))

with open(os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX)),
          'w', encoding='utf-8') as fh:
    fh.write('%% GENERATED by tuned_r28.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
json.dump(dict(per_species={k: dict(windows=v[0], tuned=v[1])
                            for k, v in per.items()},
               n_pairs=len(pairs), n_tuned=ntun, failed=FAIL),
          open(os.path.join(HERE, 'tuned_r28%s.json' % SFX), 'w'), indent=1)
print('tuned_r28: %d macros, %d assertion(s) failed %s'
      % (len(M), len(FAIL), FAIL))
sys.exit(1 if FAIL else 0)
