#!/usr/bin/env python3
r"""round 901 -> survey_numbers_round901.tex, eta_r19.json.

THE CLASS A / CLASS B SPLIT AGAINST THE PHYSICAL CRITERION IT IS SAID TO
COINCIDE WITH, AND WHAT THE CLASS A RESULTS BECOME WITHOUT THE WINDOWS THAT
FAIL IT.

Referee 2's twelfth point: the two classes are defined on native channel
width, while the criterion that decides whether a window can discriminate a
drifting carrier at all is eta_drift = |nudot_max| tau_track / dnu_ch, and the
manuscript says in one sentence that the split coincides with that criterion
and in the next that the two do not partition the survey identically.  Both
cannot be true, and the count that settles it is not in the paper.

THE COUNTS THEMSELVES ARE ALREADY PUBLISHED -- `etadrift_v405.py` measures
them, as `\EtaDriftALo` and `\EtaDriftBHi` -- so they are VERIFIED here and
not republished: a second name for one quantity is what `valuetwin.py` exists
to refuse, and the uncited macro is the reason the referee could not find the
number.  What is new, and what the instruction asks for, is the Class A result
recomputed over the windows that pass the criterion: the union bandwidth, the
number of systems, and the median limit.

Inputs: the released catalogue (the `eta_drift` column, which `v342_calc.py`
forms as drift_max x on_source / chanw), `adopted_e90` for the limits, and the
macro layer for every published count this file checks itself against.  The
union bandwidth is formed by the same interval merge `cover_v412.py` uses, on
min/max of each window's own edges, because a descending spectral window
writes its edges reversed.

    python3 eta_r19.py [--paper DIR] [--out DIR] [--drive N]

--drive 1..8 breaks one assertion each; --drive 0 means "no perturbation, but
do not write a path production reads".
"""
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 901

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
OUT = os.path.join(OUTDIR, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(OUTDIR, 'eta_r19%s.json' % SUF)

# The criterion is eta_drift >= 1: one channel of drift across the on-source
# track.  It is the paper's own definition and carries no free parameter.
ETA_MIN = 1.0

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

CAT = ae.catalogue(PAPER)
A = [r for r in CAT if r['search_class'] == 'A']
B = [r for r in CAT if r['search_class'] == 'B']
assert len(A) + len(B) == len(CAT), 'a window is in neither class'


def tex(name):
    return ae._texval(name, PAPER)


print('eta_r19 round %d%s' % (ROUND, '' if DRIVE is None
                              else ' (drive %d)' % DRIVE))

# =====================================================================
# 1  THE TWO COUNTS, VERIFIED AGAINST THE MACROS THAT PUBLISH THEM
# =====================================================================
print('\n1  the two counts')
A_LO = [r for r in A if float(r['eta_drift']) < ETA_MIN]
B_HI = [r for r in B if float(r['eta_drift']) >= ETA_MIN]
_pub = (int(tex('EtaDriftALo')), int(tex('EtaDriftBHi')))
_got = (len(A_LO), len(B_HI))
if DRIVE == 1:
    _got = (_got[0] + 1, _got[1])
ck('E1 the number of Class A windows below the criterion and of Class B '
   'windows above it are the two the macro layer already publishes, counted '
   'from the catalogue here',
   _got == _pub, '%d and %d against %d and %d published'
   % (_got[0], _got[1], _pub[0], _pub[1]))
_npub = (int(tex('NWinA')), int(tex('NWinB')))
if DRIVE == 2:
    _npub = (_npub[0] + 1, _npub[1])
ck('E2 and they are counted over the census the paper publishes, so the '
   'counts cannot be stale with respect to it',
   (len(A), len(B)) == _npub,
   '%d Class A and %d Class B against %d and %d published'
   % (len(A), len(B), _npub[0], _npub[1]))
_nonzero = len(A_LO) > 0
if DRIVE == 3:
    _nonzero = not _nonzero
ck('E3 the Class A count is NOT zero, which is the condition under which the '
   'claim that the split coincides with the criterion has to go',
   _nonzero, '%d Class A windows cannot discriminate a drifting carrier'
   % len(A_LO))

# =====================================================================
# 2  THE CLASS A RESULT WITHOUT THEM
# =====================================================================
print('\n2  the Class A result over the windows that pass the criterion')


def union(iv):
    """Merged disjoint intervals; min/max on the pair, because a descending
    spectral window writes its edges reversed."""
    out = []
    for a, b in sorted((min(x, y), max(x, y)) for x, y in iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def band(rows):
    return sum(b - a for a, b in
               union([(float(r['flo_GHz']), float(r['fhi_GHz']))
                      for r in rows]))


E = ae.per_window(CAT, PAPER)
KEEP = [r for r in A if float(r['eta_drift']) >= ETA_MIN]
U_ALL, U_KEEP = band(A), band(KEEP)
S_ALL = {r['system_id'] for r in A}
S_KEEP = {r['system_id'] for r in KEEP}


def sysmed(rows):
    best = {}
    for r in rows:
        k = r['system_id']
        best[k] = min(best.get(k, 1e99), E[id(r)])
    return st.median(list(best.values())), best


MED_ALL, BEST_ALL = sysmed(A)
MED_KEEP, BEST_KEEP = sysmed(KEEP)
print('  union bandwidth %.3f -> %.3f GHz; systems %d -> %d; median system '
      'limit %.4e -> %.4e W' % (U_ALL, U_KEEP, len(S_ALL), len(S_KEEP),
                                MED_ALL, MED_KEEP))
_upub = float(tex('CvUnionA'))
_uok = abs(U_ALL - _upub) < 0.05
if DRIVE == 4:
    _uok = False
ck('E4 the union bandwidth formed here over all Class A windows is the '
   'published one, so the recomputed figure is formed the same way and is '
   'comparable with it',
   _uok, '%.3f against %s published' % (U_ALL, _upub))
_spub = int(tex('NSysClassA'))
if DRIVE == 5:
    _spub += 1
ck('E5 and the system count over all Class A windows is the published one',
   len(S_ALL) == _spub, '%d against %d published' % (len(S_ALL), _spub))
# ★★ THE CLAUSE HERE MUST BE AN IDENTITY AND NOT A SMALLNESS CLAIM.  The first
# version of it asserted that the three recomputed quantities move only a
# little, which is a check that can only ever fail on correct data -- and it
# duly failed, because they move: the criterion costs three systems and seven
# per cent of the union.  What can be checked is that the quantities are
# formed from the right set: a system is lost exactly when it has no passing
# Class A window, and the bandwidth lost is exactly the frequency no passing
# window covers.
_lost_sys = sorted(S_ALL - S_KEEP)
_no_pass = sorted({r['system_id'] for r in A}
                  - {r['system_id'] for r in KEEP})
if DRIVE == 6:
    _no_pass = _no_pass[1:]
ck('E6 a system is absent from the recomputed count exactly when every one of '
   'its Class A windows fails the criterion, so the count is a property of '
   'the windows and not of the order they were removed in',
   _lost_sys == _no_pass, '%d systems lost: %s'
   % (len(_lost_sys), ', '.join(_lost_sys) or 'none'))
_only = sum(b - a for a, b in union(
    [(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in A_LO]))
_cov_keep = union([(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in KEEP])
_uncov = 0.0
for a, b in union([(float(r['flo_GHz']), float(r['fhi_GHz']))
                   for r in A_LO]):
    seg = [(a, b)]
    for c, d in _cov_keep:
        nxt = []
        for x, y in seg:
            if d <= x or c >= y:
                nxt.append((x, y))
                continue
            if x < c:
                nxt.append((x, min(c, y)))
            if y > d:
                nxt.append((max(d, x), y))
        seg = nxt
    _uncov += sum(y - x for x, y in seg)
_dband_abs = U_ALL - U_KEEP
if DRIVE == 7:
    _uncov *= 2.0
ck('E7 and the union bandwidth the criterion costs is exactly the frequency '
   'that only failing windows cover, so the recomputed union is a measure of '
   'a set and not a subtraction of two numbers',
   abs(_uncov - _dband_abs) < 1e-6,
   '%.3f GHz covered only by failing windows against a union loss of %.3f '
   'GHz (%+.1f per cent)'
   % (_uncov, _dband_abs, -100 * _dband_abs / U_ALL))
_dmed = MED_KEEP / MED_ALL - 1.0
_dband = -_dband_abs / U_ALL

# =====================================================================
# 3  THE MACROS
# =====================================================================
# ★ Only what the prose cites.  `\EtaDriftALo` and `\EtaDriftBHi` already
# carry the two counts and are cited by the new sentence; the two below are
# new quantities and are what the instruction asks for.
# ★★ THE MEDIAN LIMIT IS NOT EMITTED AS A VALUE, deliberately.  Recomputed it
# is 1.43e15 W against a published 1.45e15 -- the same number to the two
# significant figures the paper prints limits to, except that the pair
# straddles a rounding boundary, so printing it would put two spellings of one
# quantity in the paper.  Two generators already publish 1.4e15 W under their
# own names, and `valuetwin.py` groups cited macros by value and unit, so a
# third would have to be declared a coincidence as well.  The prose therefore
# states the bound in words, and E8 is the gate that keeps the bound true.
m('EdrUnionGHz', '%.1f' % U_KEEP)
m('EdrNSys', '%d' % len(S_KEEP))
# ★ v4.20 (integration): the count of Class A windows that DO resolve drift,
# emitted because the coordinator's ruling on R2 minor 12 prints the
# drift-resolving subset wherever the drift claim is made -- which is the
# conclusions item stating what was searched, as well as Sec. 4.1.  It is
# len(KEEP) and not NWinA minus EtaDriftALo written out by hand.
m('EdrNWinA', '%d' % len(KEEP))
MED_BOUND = 0.02
_in = abs(_dmed) < MED_BOUND
if DRIVE == 8:
    MED_BOUND, _in = 0.001, abs(_dmed) < 0.001
ck('E8 the median Class A system limit over the windows that pass the '
   'criterion is inside the bound the text states in words, which is what '
   'makes that bound a claim the build can fail on',
   _in, 'median moves %+.2f per cent against a stated bound of %.0f per cent'
   % (100 * _dmed, 100 * MED_BOUND))

json.dump(dict(
    eta_min=ETA_MIN, n_a=len(A), n_b=len(B), n_a_below=len(A_LO),
    n_b_above=len(B_HI),
    a_below=[dict(star=r['star_name'], eb=r['eb'], flo=float(r['flo_GHz']),
                  chanw_Hz=float(r['chanw_Hz']),
                  on_source_s=float(r['on_source_s']),
                  eta=float(r['eta_drift'])) for r in A_LO],
    union_GHz=dict(all=U_ALL, passing=U_KEEP),
    n_systems=dict(all=len(S_ALL), passing=len(S_KEEP)),
    median_system_W=dict(all=MED_ALL, passing=MED_KEEP),
    systems_lost=_lost_sys, fails=FAIL),
    open(OUT_JSON, 'w'), indent=1, sort_keys=True)
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
