#!/usr/bin/env python3
r"""Round 3460 (r34, Referee 2 R2-8, R2-19): THE PRIOR-SEARCH COMPARISON, FOR THE UNION AND FOR THE MEDIAN SYSTEM.

Section 1 and the Conclusions compare this survey's bandwidth with the two 203 GHz searches of nearby stars
(Steffes & DeBoer 1994; Mauersberger et al. 1996), each in no more than \SbPriorBandMHz\,MHz of one line:
the union of the fine-channel windows is \SbPriorRatio{} times that (priorsearch_r15, from the full-precision
union that \DnuA prints rounded).  The
referee points out that a transmitter around ONE star had to fall inside that star's own coverage, not the
union over 61 stars.  So the median system's merged Class A coverage -- the column Delta nu_cov of Table F1
(persys_r17, whose P5 asserts its median is \SysUnionAMed, v381_calc) -- is put over the same denominator.

Everything is read from the catalogue the build holds and from published macros; nothing is re-extracted.

Population: every system the fine-channel (Class A) search covers, \NSysClassA, as in Table F1's
Delta nu_cov column -- coverage is a property of the observations, not of a limit, so the three systems
whose LIMIT is conditional on the adopted position (posflag_r31) keep their coverage.  The median over the
58 covered systems with a bounded position (1.8404 GHz, the same factor) is in the json for reference only.

Macros (round 3460):
  \SbPriorRatioSysMed   the median system's merged Class A coverage over the prior searches' band, a factor
  \CtRowCensusCross     (R2-19) the row of Table A1(b) that prints the census crossing count \CsNCross

Assertions (each driven: `--drive N` prints FAILED and exits 1, writes nothing):
  K1 the per-system coverage reproduces the published median \SysUnionAMed over \NSysClassA systems  (drive 1)
  K2 the union reproduces \DnuA and \SbPriorRatio with the same denominator                         (drive 2)
  K3 the median system is covered by more than the prior band and by less than the union, and the
     factor printed is that median over that denominator                                            (drive 3)
  K4 the Table A1(b) row named for the census crossings prints \CsNCross under \EvNCrossRaw           (drive 4)

    python3 covmed_r34.py [--drive N]
"""
import csv
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import posflag_r31 as PF  # noqa: E402

ROUND = 3460
DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round3460%s.tex' % SUF)
OUT_JSON = os.path.join(HERE, 'covmed_r34%s.json' % SUF)
OUT, FAIL = [], []


def m(name, val):
    assert name.isalpha(), name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-74s %s  %s' % (label[:74], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


def macro(name):
    """A value another generator published, read from the macro layer (last definition wins, drives ignored)."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if fn.startswith('survey_numbers') and fn.endswith('.tex') and '_drive' not in fn:
            for mm in pat.finditer(open(os.path.join(HERE, 'numbers', fn), encoding='utf-8').read()):
                if mm.group(1).strip() and not mm.group(1).startswith('\\'):
                    v = mm.group(1).strip()
    if v is None:
        raise SystemExit('covmed_r34: macro \\%s not found' % name)
    return float(v.replace('\\,', '').replace(',', ''))


def union(iv):
    """merged length of a set of intervals (GHz) -- the rule of freqdef_v399 / v381_calc / persys_r17"""
    iv = sorted((min(a, b), max(a, b)) for a, b in iv)
    tot, clo, chi = 0.0, None, None
    for lo, hi in iv:
        if clo is None:
            clo, chi = lo, hi
        elif lo <= chi:
            chi = max(chi, hi)
        else:
            tot += chi - clo
            clo, chi = lo, hi
    return tot + (chi - clo if clo is not None else 0.0)


CAT = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.99.csv'))))
A = [r for r in CAT if r['search_class'] == 'A']
PERSYS = {}
for r in A:
    PERSYS.setdefault(r['system_id'], []).append((float(r['flo_GHz']), float(r['fhi_GHz'])))
COV = {s: union(v) for s, v in PERSYS.items()}
if DRIVE == 1:
    COV.pop(sorted(COV, key=COV.get)[len(COV) // 2])        # one system silently missing
vals = sorted(COV.values())
MED = st.median(vals)
MED57 = st.median(sorted(v for s, v in COV.items() if not PF.is_cond(s)))
print('round %d: %d Class A systems, median coverage %.4f GHz (%.4f over the %d with a bounded position)'
      % (ROUND, len(COV), MED, MED57, sum(1 for s in COV if not PF.is_cond(s))))

ck('K1 the per-system coverage reproduces the published median over the systems the search covers',
   len(COV) == int(macro('NSysClassA')) and abs(MED - macro('SysUnionAMed')) < 0.005,
   '%d systems (published %d), median %.4f GHz (published %.2f)'
   % (len(COV), int(macro('NSysClassA')), MED, macro('SysUnionAMed')))

DEN_MHZ = macro('SbPriorBandMHz') if DRIVE != 2 else macro('SbPriorBandMHzA')
U_A = union([iv for v in PERSYS.values() for iv in v])
ck('K2 the union reproduces the published union and the published union factor over the same denominator',
   abs(U_A - macro('DnuA')) < 0.05 and round(U_A * 1000.0 / DEN_MHZ) == int(macro('SbPriorRatio')),
   'union %.4f GHz (published %.1f); / %.0f MHz = %d (published %d)'
   % (U_A, macro('DnuA'), DEN_MHZ, round(U_A * 1000.0 / DEN_MHZ), int(macro('SbPriorRatio'))))

RATIO = MED * 1000.0 / DEN_MHZ
if DRIVE == 3:
    RATIO = macro('SbPriorRatio') + 1.0                   # the union factor printed for the median system
PRINTED = '%d' % round(RATIO)
ck('K3 the median system is covered by more than the prior band and by less than the union, and the factor '
   'printed is that median over that denominator',
   1.0 < RATIO < int(macro('SbPriorRatio')) and int(PRINTED) == round(MED * 1000.0 / DEN_MHZ) >= 2,
   '%.4f GHz / %.0f MHz = %.2f -> %s (union factor %d)' % (MED, DEN_MHZ, RATIO, PRINTED,
                                                           int(macro('SbPriorRatio'))))

# ---- R2-19: the row of Table A1(b) (tab_counts.tex, counts_r15) that holds the census crossing count, so that
# Sec. 2's "\CsNCross{} threshold crossings (Table A1b, row ...)" names a row the table prints, not a typed one.
_TROWS = []
for ln in open(os.path.join(HERE, 'tab_counts.tex'), encoding='utf-8'):
    c = [x.strip() for x in ln.rstrip().rstrip('\\').split('&')]
    if len(c) >= 3 and re.match(r'^\d+(\.\d+)*$', c[0]):
        _TROWS.append((c[0], c[1], c[2]))
_hits = [t for t in _TROWS if t[2] == r'\CsNCross']
_row = _hits[0] if (_hits and DRIVE != 4) else (_hits[-1] if _hits else None)
_parent = next((t for t in _TROWS if _row and t[0] == _row[0].rsplit('.', 1)[0]), None)
ck('K4 the census crossing count is printed in Table A1(b) on a row of the census, under the row of all '
   'crossings at the trigger, and that row is the first to print it',
   _row is not None and _row is _hits[0] and 'primary census' in _row[1]
   and _parent is not None and _parent[2] == r'\EvNCrossRaw',
   'row %s (%s) under row %s (%s)' % (_row and _row[0], _row and _row[1], _parent and _parent[0],
                                      _parent and _parent[2]))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
m('SbPriorRatioSysMed', PRINTED)
m('CtRowCensusCross', _row[0])
json.dump(dict(produced_by='covmed_r34.py', round=ROUND, n_systems=len(COV), median_cov_GHz=MED,
               median_cov_position_bounded_GHz=MED57, prior_band_MHz=DEN_MHZ, ratio_median=RATIO,
               ratio_median_position_bounded=MED57 * 1000.0 / DEN_MHZ, union_GHz=U_A,
               per_system_cov_GHz=dict(sorted(COV.items()))),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
hdr = ['%% GENERATED by covmed_r34.py (round %d) -- do not hand-edit.' % ROUND,
       '% The prior-search bandwidth comparison for the median system (R2-8); the Table A1(b) census-crossing row (R2-19).']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
print('covmed_r34: %d macro(s) -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
