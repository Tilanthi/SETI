#!/usr/bin/env python3
r"""Round 3660 (v4.36, N4): THE TITLE'S FREQUENCY RANGE IS THE WHOLE SEARCHED RANGE.

AUTHOR RULING (2026-11-09): the title's range "114--873 GHz" becomes the full
range the searched windows cover.  The Class B (coarse-channel) windows reach
below the lowest Class A window, to about 90 GHz; the lower edge is the lowest
searched window edge in the catalogue the census reads
(per_target_results_v3.99.csv, the file census_v412.py and v343_calc.py read),
ROUNDED DOWN to an integer GHz, so the printed range contains every searched
window.  The fine-channel carrier search keeps its own range,
\SurvFreqLoA--\SurvFreqHiA (v343_calc.py, round 13), in the abstract/§1 and
the body, so the two ranges are never confused.

THE UPPER EDGE.  The highest searched edge (873.09 GHz, HD 61005, Band 10) is a
Class A window's, so the whole range and the carrier range share their upper
edge and the title prints the SAME macro for it, \SurvFreqHiA (nearest integer,
873).  Rounding it UP would print 874 for the very window the body prints as
873 -- two numbers for one edge on the first page.  T3 asserts the premise
(the top edge is a Class A window's, it prints as \SurvFreqHiA, and it lies
within half a unit of the printed value); if a Class B window ever set the top
edge, T3 fails and the title needs its own upper macro.

Macros:
  \TitleFreqLo   the lowest searched window edge, rounded down (GHz)

Assertions (each driven, `--drive N`; a drive writes nothing, prints
"FAILED: T<N> ..." and exits 1):
  T1 \TitleFreqLo is floor(lowest edge) and the edge lies in [lo, lo+1)
     (drive 1: nearest-integer rounding, 90 > 89.63 -- the range would not
     contain its own lowest window)
  T2 the lowest edge is a Class B (coarse) window's and the title's lower edge
     is strictly below the carrier search's \SurvFreqLoA -- the reason for the
     ruling (drive 2: Class A rows only)
  T3 the highest edge is a Class A window's, rounds to \SurvFreqHiA, lies
     within 0.5 GHz of it, and every Class B window ends below it
     (drive 3: a Class B window planted at 873.6 GHz)
  T4 every searched window lies inside [\TitleFreqLo, \SurvFreqHiA + 0.5]
     (drive 4: a window planted at 88.9 GHz while the edge is held)
  T5 the title is generated: \PaperTitle in the main .tex prints
     \TitleFreqLo--\SurvFreqHiA and carries no frequency literal
     (drive 5: the v4.35 title, \SurvFreqLoA--\SurvFreqHiA)
  T6 the two ranges are not confused: §1 still states the fine-channel range
     (\SurvFreqLoA ... \SurvFreqHiA in one sentence) and no manuscript sentence
     puts \TitleFreqLo beside "fine" or "carrier" (drive 6: a planted
     sentence "the fine-channel carrier search spans \TitleFreqLo--...")
  T7 the same catalogue: census_v412.py and v343_calc.py read this file, and
     the archival extent \SurvFreqLo (nearest integer) is round(lowest edge)
     (drive 7: the census reading another catalogue)

    python3 titlerange_r36.py [--drive N]
"""
import csv
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
ROUND = 3660
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
CATNAME = 'per_target_results_v3.99.csv'
OUT, FAIL = {}, []


def m(k, v):
    assert k.isalpha() and k not in OUT, k
    OUT[k] = v


def ck(label, ok, detail=''):
    print('  %-78s %s  %s' % (label[:78], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


def tv(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{((?:[^{}]|\{[^{}]*\})*)\}' % name)
    vals = []
    for f in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if f.startswith('survey_numbers') and f.endswith('.tex') and '_drive' not in f \
                and 'round%d' % ROUND not in f:
            vals += [v for v in pat.findall(open(os.path.join(HERE, 'numbers', f), errors='ignore').read()) if v]
    assert len(set(vals)) == 1, ('macro %s defined %d times: %s' % (name, len(vals), vals[:3]))
    return vals[0]


def strip_comments(txt):
    out = []
    for line in txt.split('\n'):
        i, esc = None, False
        for k, ch in enumerate(line):
            if esc:
                esc = False
                continue
            if ch == '\\':
                esc = True
            elif ch == '%':
                i = k
                break
        out.append(line if i is None else line[:i])
    return '\n'.join(out)


# ---------------------------------------------------------------- the catalogue
ROWS = []
for r in csv.DictReader(open(os.path.join(HERE, CATNAME))):
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    ROWS.append(dict(lo=min(a, b), hi=max(a, b), cls=r['search_class'],
                     res=r['resolution_class'], star=r['star_name'], band=r['band']))
assert ROWS and {w['cls'] for w in ROWS} == {'A', 'B'}, {w['cls'] for w in ROWS}
assert all((w['cls'] == 'A') == (w['res'] == 'fine') for w in ROWS), 'class/resolution disagree'
if DRIVE == 2:
    ROWS = [w for w in ROWS if w['cls'] == 'A']
if DRIVE == 3:
    ROWS.append(dict(lo=871.9, hi=873.6, cls='B', res='coarse', star='planted', band='10'))
LOW = min(ROWS, key=lambda w: w['lo'])
TOP = max(ROWS, key=lambda w: w['hi'])
lo_edge, hi_edge = LOW['lo'], TOP['hi']
LO = int(math.floor(lo_edge)) if DRIVE != 1 else int(round(lo_edge))
if DRIVE == 4:
    ROWS.append(dict(lo=88.9, hi=90.6, cls='B', res='coarse', star='planted', band='3'))
loA, hiA = int(tv('SurvFreqLoA')), int(tv('SurvFreqHiA'))

ck('T1 the title lower edge is the lowest searched edge rounded down',
   LO == math.floor(lo_edge) and LO <= lo_edge < LO + 1,
   '%d from %.4f GHz (%s Band %s)' % (LO, lo_edge, LOW['star'], LOW['band']))
ck('T2 it is a Class B window and lies below the carrier search (SurvFreqLoA)',
   LOW['cls'] == 'B' and LO < loA, 'class %s, %d < %d' % (LOW['cls'], LO, loA))
_maxB = max([w['hi'] for w in ROWS if w['cls'] == 'B'] or [0.0])
ck('T3 the top edge is Class A, prints as SurvFreqHiA, within 0.5 GHz of it',
   TOP['cls'] == 'A' and round(hi_edge) == hiA and abs(hi_edge - hiA) <= 0.5 and _maxB < hiA,
   'top %.4f GHz (%s, class %s) -> %d; Class B top %.4f; round-up would print %d'
   % (hi_edge, TOP['star'], TOP['cls'], hiA, _maxB, math.ceil(hi_edge)))
_out = [w for w in ROWS if not (LO <= w['lo'] and w['hi'] <= hiA + 0.5)]
ck('T4 every searched window lies inside the printed title range',
   not _out, '%d windows, %d outside %d-%d' % (len(ROWS), len(_out), LO, hiA))

# ---------------------------------------------------------------- the manuscript
MAIN = sorted(f for f in os.listdir(HERE) if re.match(r'technosignatures_40pc_v[\d.]+\.tex$', f))
assert len(MAIN) == 1, MAIN
_main = strip_comments(open(os.path.join(HERE, MAIN[0])).read())
_mt = re.search(r'\\newcommand\{\\PaperTitle\}\{((?:[^{}]|\{[^{}]*\})*)\}', _main)
_title = _mt.group(1) if _mt else ''
if DRIVE == 5:
    _title = _title.replace(r'\TitleFreqLo--\SurvFreqHiA', r'\SurvFreqLoA--\SurvFreqHiA')
_lits = [d for d in re.findall(r'\d+', re.sub(r'\\[A-Za-z]+', '', _title)) if d != '40']
ck('T5 the title prints \\TitleFreqLo--\\SurvFreqHiA and no frequency literal',
   r'\TitleFreqLo--\SurvFreqHiA\,GHz' in _title and not _lits and r'\title{\PaperTitle}' in _main,
   'literals %s' % _lits)

_secs = {}
for f in sorted(os.listdir(os.path.join(HERE, 'sections'))):
    if f.endswith('.tex'):
        _secs[f] = strip_comments(open(os.path.join(HERE, 'sections', f)).read())
if DRIVE == 6:
    _secs['01_intro.tex'] += ('\nThe fine-channel carrier search spans '
                              '\\TitleFreqLo--\\SurvFreqHiA\\,GHz.\n')


def sentences(t):
    return re.split(r'(?<=[.;:])\s+(?=[A-Z\\])', ' '.join(t.split()))


_intro = [s for s in sentences(_secs.get('01_intro.tex', ''))
          if '\\SurvFreqLoA' in s and '\\SurvFreqHiA' in s]
_mix = [s[:90] for f, t in _secs.items() for s in sentences(t)
        if '\\TitleFreqLo' in s and re.search(r'fine|carrier', s, re.I)]
ck('T6 Sec. 1 states the fine-channel range; TitleFreqLo never beside fine/carrier',
   bool(_intro) and not _mix, '%d intro sentence(s); mixed %s' % (len(_intro), _mix))

_census = open(os.path.join(HERE, 'census_v412.py')).read()
if DRIVE == 7:
    _census = _census.replace(CATNAME, 'per_target_results_v3.84.csv')
_v343 = open(os.path.join(HERE, 'v343_calc.py')).read()
ck('T7 the census and round 13 read this catalogue; SurvFreqLo = round(lowest edge)',
   ("'%s'" % CATNAME) in _census and ("'/%s'" % CATNAME) in _v343
   and int(tv('SurvFreqLo')) == round(lo_edge),
   'SurvFreqLo %s, round(%.4f) = %d' % (tv('SurvFreqLo'), lo_edge, round(lo_edge)))

m('TitleFreqLo', '%d' % LO)

if FAIL:
    print('\nFAILED: %s' % '; '.join(FAIL))
    raise SystemExit(1)
if DRIVE is not None:
    print('drive %d did not fire' % DRIVE)
    raise SystemExit(0)
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round%d.tex' % ROUND)
hdr = ['%% GENERATED by titlerange_r36.py (round %d) -- do not hand-edit.' % ROUND,
       '% The title\'s frequency range: the lowest searched window edge of '
       + CATNAME + ', rounded down (author ruling 2026-11-09).']
open(OUT_TEX, 'w').write('\n'.join(hdr + ['\\newcommand{\\%s}{%s}' % kv for kv in sorted(OUT.items())]) + '\n')
print('titlerange_r36: %d macro(s) -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
