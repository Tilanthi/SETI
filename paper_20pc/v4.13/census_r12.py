#!/usr/bin/env python3
r"""round 300 -> survey_numbers_round300.tex: THE CROSSING CENSUS HAS ONE
SOURCE, AND EVERY COUNT IN THE PAPER IS CHECKED AGAINST IT.

Seven generators publish a count of the threshold crossings.  Each of them
derives it correctly from `ledger.json`, which is the one place the adopted
crossing list lives -- and that is exactly the condition under which the
counts drift apart, because a generator re-run at the wrong moment publishes
a census of a ledger that no longer exists.  This round reads the ledger
once, forms the census as SETS, and then requires every published count to
equal the set it claims to be.  It publishes almost nothing itself: a closure
whose own numbers are new is a second census, which is the defect.

                 raw = quality-passing + flagged
             attributed + unattributed = raw
    rank-leading unattributed, in each part separately

The partition by execution-block quality is kept apart from the partition by
search class on purpose.  They coincide in this survey -- the one block that
fails the quality criterion holds the whole Class~B crossing population --
and `events_r12.py` asserts that coincidence; here the two are compared
again from the other side, so that a future block failing with Class~A
windows in it stops the build instead of being reported under the other
partition's name.

THE ONE QUANTITY THIS ROUND DOES PUBLISH is the per-window occupancy of the
attribution windows (referee 2's point about the chance expectation).  The
expectation was reduced by the mask's share of the SEARCHED BAND, about four
per cent.  But the windows are line-tuned: a crossing falls on the grid of a
window chosen to contain a transition, so it lands inside an attribution
window more often than a band-average would predict.  Measured on the
crossings themselves -- the peaks with a released frequency, against the
expectation that each is free to land anywhere on its own window's channel
grid -- the figure is about nine per cent, and using it LOWERS the chance
expectation, which is the direction that runs against the null.  C5 asserts
that direction, so the favourable figure cannot come back silently.

Eight assertions, eight drives.  `--drive 0` means "no perturbation, but do not
write a path production reads"; every drive writes `*_driveN.*` only.

Usage:  python3 census_r12.py [--drive N]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 300

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

OUTNAME = 'survey_numbers_round300%s.tex' % SUF
TEXOUT = os.path.join(HERE, OUTNAME)
JSON_PATH = os.path.join(HERE, 'census_r12%s.json' % SUF)
assert OUTNAME.startswith('survey_numbers_round%d' % ROUND), OUTNAME

MAC, fail = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MAC), name
    MAC.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """Read a macro out of the published layer; last definition wins.  Never
    reads this round's own output, so the closure cannot agree with itself."""
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


def ival(name):
    """A published count as an integer, or None if it is not published."""
    v = texval(name)
    if v is None:
        return None
    v = re.sub(r'[^0-9.\-]', '', v)
    try:
        return int(round(float(v)))
    except ValueError:
        return None


# ------------------------------------------------------------- the one source
LEDGER = json.load(open(os.path.join(HERE, 'ledger.json')))
ROWS = LEDGER['rows']
SUMMARY = LEDGER['summary']

FAILBLOCK = texval('BqFailBlock')
assert FAILBLOCK, 'the failing execution block is not published'
FAILBLOCK = FAILBLOCK.replace('\\_', '_').replace('\\', '').strip()

if DRIVE == 1:                         # a row vanishes from the raw census
    ROWS = ROWS[:-1]
if DRIVE == 2:                         # the flagged block is not recognised
    FAILBLOCK = FAILBLOCK + 'x'

#: the census, as sets of (star, block, frequency) keys and not as integers.
def key(r):
    return (r['star'], r['eb'], round(float(r['freq']), 6))


RAW = set(key(r) for r in ROWS)
assert len(RAW) == len(ROWS), 'two ledger rows share one crossing key'
FLAG = set(key(r) for r in ROWS if r['eb'] == FAILBLOCK)
QP = RAW - FLAG

ATTR = set(key(r) for r in ROWS if r['attributed'])
UNATTR = RAW - ATTR
if DRIVE == 3:                         # attribution stops partitioning
    ATTR = ATTR | set(list(UNATTR)[:1])

#: "leads its own control field" = the star's statistic exceeds all of the
#: window's control positions.  `screen` is the ledger's own flag for it, and
#: `blockq_v412.py` publishes its count from the same field.
RANK = set(key(r) for r in ROWS if not r['attributed'] and r.get('screen'))
if DRIVE == 4:
    RANK = set()

QP_ATTR, QP_UN = QP & ATTR, QP - ATTR
FL_ATTR, FL_UN = FLAG & ATTR, FLAG - ATTR
QP_RANK, FL_RANK = RANK & QP, RANK & FLAG

print('census_r12: round %d%s' % (ROUND, '' if DRIVE is None
                                  else '  (drive %d)' % DRIVE))
print('  %d raw = %d quality-passing + %d in %s'
      % (len(RAW), len(QP), len(FLAG), FAILBLOCK))
print('  quality-passing  %d attributed / %d unattributed, %d leading their '
      'own control field' % (len(QP_ATTR), len(QP_UN), len(QP_RANK)))
print('  flagged          %d attributed / %d unattributed, %d leading'
      % (len(FL_ATTR), len(FL_UN), len(FL_RANK)))
print('  whole census     %d attributed / %d unattributed, %d leading'
      % (len(ATTR), len(UNATTR), len(RANK)))

# ============================================================ the closure
#: every published count, with the set it claims to be.  A name that is not
#: in the layer at all is reported and makes C6 fail; a name that is there
#: and disagrees makes its own clause fail.
CLAIMS = [
    ('C1', 'the raw crossing total', len(RAW),
     ['CnCross', 'NCross', 'EvNCrossRaw', 'BqSurvXross']),
    ('C2', 'the quality-passing total', len(QP),
     ['EvNCrossQp', 'BqSurvXrossCut', 'BqXrossA', 'ChnXrossA']),
    ('C2', 'the flagged total', len(FLAG),
     ['EvNCrossFlag', 'BqFailNCross', 'BqXrossBLost', 'ChnXrossB',
      'CnNFlagged']),
    ('C3', 'the attributed total', len(ATTR),
     ['CnAttr', 'NAttributed', 'FrNAttr', 'MkAttrSO']),
    ('C3', 'the unattributed total', len(UNATTR),
     ['CnUnattr', 'NUnattributed', 'FrNUnattr', 'MkUnattrSO']),
    ('C3', 'the quality-passing attributed count', len(QP_ATTR),
     ['EvNAttrQp', 'ChnAttrA']),
    ('C3', 'the quality-passing unattributed count', len(QP_UN),
     ['EvNUnattrQp', 'ChnUnattrA', 'BqUnattrA']),
    ('C4', 'unattributed crossings leading their own control field',
     len(RANK), ['CnRank', 'NUnattrRankFlagged', 'MkRankSO', 'FrNRankPass']),
    ('C4', 'the same count in quality-passing data', len(QP_RANK),
     ['EvNRankQp', 'ChnRankA', 'BqRankA']),
    ('C4', 'the same count in the flagged block', len(FL_RANK),
     ['EvNRankFlag']),
]

NCHECK, MISSING, BAD, PER = 0, [], [], {}
for clause, what, want, names in CLAIMS:
    for name in names:
        got = ival(name)
        if got is None:
            MISSING.append(name)
            continue
        NCHECK += 1
        PER[clause] = PER.get(clause, 0) + 1
        if got != want:
            BAD.append((clause, name, got, want, what))

CLAUSE_WHAT = {'C1': 'the crossing total',
               'C2': 'the quality split',
               'C3': 'the attribution split',
               'C4': 'the rank-leading crossings'}
for clause in ('C1', 'C2', 'C3', 'C4'):
    bad = [b for b in BAD if b[0] == clause]
    n = PER.get(clause, 0)
    ck('%s every published count of %s equals the ledger\'s own set'
       % (clause, CLAUSE_WHAT[clause]),
       not bad and n > 0,
       '%d macro(s) compared; %s' % (n, 'all agree' if not bad else
                                     '; '.join('\\%s=%s against %d (%s)'
                                               % (b[1], b[2], b[3], b[4])
                                               for b in bad)))

# ---------------------------------------- R2-25: the per-window occupancy
#: the crossings with a released peak frequency, and how many of them fall
#: inside an attribution window, against the number expected if each peak
#: were free to land anywhere on its own window's channel grid.  Both sides
#: are `appm_v405.py`'s measurement; this round only forms the ratio and
#: compares it with the band-average figure the expectation used.
TUBE_N = ival('AppMNCrossF')
TUBE_EXP = texval('AppMTubeNull')
BAND_PCT = texval('LgMaskOccPct')
OCC_PERWIN = None
if TUBE_N and TUBE_EXP is not None:
    OCC_PERWIN = 100.0 * float(TUBE_EXP) / float(TUBE_N)
if DRIVE == 5 and OCC_PERWIN is not None:
    OCC_PERWIN = 0.5 * float(BAND_PCT)      # the favourable direction again

ck('C5 the per-window occupancy exceeds the band-average it replaces, so '
   'the switch runs AGAINST the null',
   OCC_PERWIN is not None and BAND_PCT is not None
   and OCC_PERWIN > float(BAND_PCT),
   'per window %s per cent of %s crossings against band average %s per cent'
   % ('%.1f' % OCC_PERWIN if OCC_PERWIN is not None else '?',
      TUBE_N, BAND_PCT))

NEED = 24
ck('C6 the closure is not vacuous: every census macro the paper publishes '
   'is present in the layer and was compared',
   not MISSING and NCHECK >= NEED and (DRIVE != 6),
   '%d compared, %d needed; missing from the layer: %s'
   % (NCHECK, NEED, ', '.join('\\' + x for x in MISSING) or 'none'))

# ============================================================ C7
# ★ THE TYPESET TABLE IS PART OF THE CENSUS TOO.  Table 9 is a row per
# threshold crossing and a `table*` float cannot break across a page, so it
# ran into the text beneath it -- Glenn saw that on page 25 and no gate here
# could, because pdflatex calls it an `Overfull \vbox` and carries on.
# `ledger_v410.py` now writes the body in parts.  Splitting a table is the
# obvious way to lose a row, so the parts are read back and required to
# typeset every crossing exactly once, keyed on (star, block, frequency) and
# not on a row count: two parts of 28 would also sum to 56 with one crossing
# duplicated and another missing.
LEDGER_PARTS = ['tab_ledger.tex', 'tab_ledger_cont.tex']


def _fragrows(fn):
    """(star, block, frequency) of every data row of a ledger fragment."""
    got = []
    path = os.path.join(HERE, fn)
    if not os.path.exists(path):
        return got
    for ln in open(path, errors='ignore'):
        ln = ln.strip()
        if not ln.endswith('\\\\') or ln.startswith('%'):
            continue
        cells = [c.strip() for c in ln[:-2].split('&')]
        if len(cells) < 5 or cells[0].lower().startswith('star'):
            continue
        star = re.sub(r'[\\${}~^]|\\mathrm|\\emph', ' ', cells[0]).strip()
        star = ' '.join(star.split())
        blk = cells[1].replace('\\_', '_').strip()
        try:
            freq = round(float(cells[3]), 4)
        except ValueError:
            continue
        got.append((star, blk, freq))
    return got


PARTROWS = [_fragrows(f) for f in LEDGER_PARTS]
if DRIVE == 7 and PARTROWS[0]:                   # a row lost in the split
    PARTROWS[0] = PARTROWS[0][1:]
if DRIVE == 8 and PARTROWS[0] and PARTROWS[1]:   # a row typeset twice
    PARTROWS[1] = PARTROWS[1][:-1] + [PARTROWS[0][0]]
FLAT = [k for part in PARTROWS for k in part]
ck('C7 the typeset ledger carries every crossing exactly once across its '
   'parts: the table was split so that it could not run off its page, and a '
   'split is how a row goes missing',
   len(FLAT) == len(set(FLAT)) == len(RAW)
   and all(len(p) > 0 for p in PARTROWS),
   'parts %s = %d rows, %d distinct, against %d crossings%s'
   % ('+'.join(str(len(p)) for p in PARTROWS), len(FLAT), len(set(FLAT)),
      len(RAW),
      '' if len(FLAT) == len(set(FLAT)) else '; duplicated %s'
      % [k[:2] for k in set(FLAT) if FLAT.count(k) > 1][:2]))

# ------------------------------------------------------------------ macros
m('CxLedgerPartOne', '%d' % len(PARTROWS[0]))
m('CxLedgerPartTwo', '%d' % len(PARTROWS[1]))
m('CxOccPerWinPct', '%.1f' % (OCC_PERWIN if OCC_PERWIN is not None else 0.0))
m('CxNCensusMacro', '%d' % NCHECK)

json.dump(dict(
    raw=len(RAW), quality_passing=len(QP), flagged=len(FLAG),
    failblock=FAILBLOCK,
    quality_passing_split=dict(attributed=len(QP_ATTR),
                               unattributed=len(QP_UN),
                               rank_leading=len(QP_RANK)),
    flagged_split=dict(attributed=len(FL_ATTR), unattributed=len(FL_UN),
                       rank_leading=len(FL_RANK)),
    census=dict(attributed=len(ATTR), unattributed=len(UNATTR),
                rank_leading=len(RANK)),
    ledger_summary=SUMMARY,
    occupancy=dict(per_window_pct=OCC_PERWIN,
                   band_average_pct=float(BAND_PCT) if BAND_PCT else None,
                   n_crossings_with_frequency=TUBE_N,
                   n_expected_in_window=float(TUBE_EXP) if TUBE_EXP else None),
    macros_compared=NCHECK, disagreements=[list(b) for b in BAD],
), open(JSON_PATH, 'w'), indent=1, sort_keys=True)

HDR = ['%%%% GENERATED by census_r12.py (round %d) -- do not hand-edit.' % ROUND,
       '%% The census closure: this round COMPARES every published crossing',
       '%% count with the ledger\'s own set and publishes only the one',
       '%% quantity no other generator owns -- the per-window occupancy of',
       '%% the attribution windows, which the chance expectation needs.']
with open(TEXOUT, 'w') as fh:
    fh.write('\n'.join(HDR + sorted(MAC)) + '\n')

print('census_r12: wrote %s, %d macros; %d published census counts compared'
      % (OUTNAME, len(MAC), NCHECK))
for f in fail:
    print('  ASSERTION FIRED  ' + f)
print('census_r12: %d assertions fired' % len(fail))
sys.exit(1 if fail else 0)
