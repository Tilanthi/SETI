#!/usr/bin/env python3
"""Verify the deposit, from the written files and not from the generator.

    python3 zverify.py [--tree DIR] [--zip FILE]

Nine gates.  Each prints PASS or FAIL with what it measured; a FAIL is a
non-zero exit.  The point of running on the WRITTEN files is that a generator
checking its own data structures proves nothing about what shipped.

 V1  every csv parses, every row has the header's width, no stray whitespace
 V2  every documented column exists and every existing column is documented
 V3  the row counts are the article's published counts, read from its macros
 V4  no file mentions versions, edits, rounds, referees or corrections, and
     none carries a reference into a numbered section, table or figure
 V5  the joins resolve: blocks, stars, windows, crossings
 V6  the ten principal statistics rebuild from the deposited tables alone
 V7  the four reference implementations run, and the two that check themselves
     against the tables agree with them
 V8  the zip is reproducible and its manifest is the tree
 V9  every deposited number that also appears in the article equals the macro
     the article prints it from -- the mask bandwidth, the sub-trigger band and
     the completeness multiplier, none of which V1-V8 could see
 V10 every deposit path the article cites (a \texttt{dir/file} in the
     manuscript or its sections) is a member of the zip -- round 28, Ruling
     R14: the article pointed at six documentation files the deposit never
     held, and V1-V9 all read the deposit, never the article's pointers into
     it.  `--drive 3` removes one cited member from the zip's member list in
     memory and must fail V10.
"""
import argparse
import csv
import glob
import hashlib
import math
import os
import re
import statistics as st
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser()
AP.add_argument('--tree', default=os.path.join(HERE,
                                               'ALMA_Technosignatures_40pc'))
AP.add_argument('--zip', default=os.path.join(
    HERE, 'ALMA_Technosignatures_40pc.zip'))
#: ★ v4.26: the base is THIS directory, not a pinned version.  A tool that
#: hard-codes a version directory follows a stale tree at the next bump and
#: says nothing about it -- `verpin` exists for exactly that and caught this
#: one.  The deposit is verified against the build it was generated from.
AP.add_argument('--base', default=HERE)
#: ★★★★ B4 (round 26).  V5's window-key clause built BOTH SIDES AS `set`s, so
#: multiplicity was discarded before anything was compared: it could go red on
#: a key present in no window row and NEVER on a key present in several, which
#: is the condition that actually destroys a join.  405 control rows collapsed
#: to 397 keys and 1663 window rows to 1628 and V5 reported "all join", while
#: the deposit's own README told the reader to join on that key -- so the
#: article's 60 systems, 1.8e15 W median and 57 below 1e16 W were NOT
#: reproducible from the archive as documented.  The clause below compares
#: MULTISETS and asserts the documented key is unique over every table that
#: carries it.  `--drive 1` plants a duplicate so the clause is demonstrated
#: to fail on the defect it exists for; `--drive 2` deletes a window row so the
#: original missing-key condition is demonstrated as well.  A drive writes
#: nothing: this tool only reads.
AP.add_argument('--drive', type=int, default=0)
A = AP.parse_args()
DRIVE = A.drive
TREE = os.path.abspath(A.tree)
FAILED = []


def gate(name, ok, note):
    print('%-4s %-4s %s' % (name, 'PASS' if ok else 'FAIL', note))
    if not ok:
        FAILED.append(name)


def load(rel):
    with open(os.path.join(TREE, rel), newline='') as fh:
        rows = list(csv.DictReader(fh))
    return rows


CSVS = []
for d, _s, fs in os.walk(TREE):
    for fn in sorted(fs):
        if fn.endswith('.csv'):
            CSVS.append(os.path.relpath(os.path.join(d, fn), TREE))
CSVS.sort()

# ------------------------------------------------------------------------- V1
bad = []
for rel in CSVS:
    with open(os.path.join(TREE, rel), newline='') as fh:
        rdr = csv.reader(fh)
        hdr = next(rdr)
        if any(c != c.strip() or not c for c in hdr):
            bad.append('%s: header carries padding or an empty name' % rel)
        n = 0
        for row in rdr:
            n += 1
            if len(row) != len(hdr):
                bad.append('%s row %d has %d fields against %d'
                           % (rel, n, len(row), len(hdr)))
                break
            for c in row:
                if c != c.strip():
                    bad.append('%s row %d carries a padded field %r'
                               % (rel, n, c))
                    break
        if n == 0:
            bad.append('%s has no rows' % rel)
#: ★ Running the deposited code is part of the verification, and Python
#: writes a bytecode cache beside a module it imports -- which lands INSIDE
#: the tree and changes what the archive contains.  The sweep that caught it
#: stays, because the next thing to drop a file in here will not announce
#: itself either.
for _d, _s, _fs in os.walk(TREE):
    for _fn in _fs:
        _rel = os.path.relpath(os.path.join(_d, _fn), TREE)
        if _fn.endswith(('.pyc', '.pyo')) or '__pycache__' in _rel:
            bad.append('%s is a build artefact and must not be in the '
                       'archive' % _rel)
gate('V1', not bad, '%d csv files parse, %d rows in total; %s'
     % (len(CSVS), sum(len(load(r)) for r in CSVS),
        'no defects' if not bad else bad[:3]))

# ------------------------------------------------------------------------- V2
DOC = open(os.path.join(TREE, 'documentation/column_descriptions.md')).read()
documented = {}
cur = None
for ln in DOC.splitlines():
    m = re.match(r'^## `(.+)`$', ln)
    if m:
        cur = m.group(1)
        documented[cur] = []
    m = re.match(r'^\| `([A-Za-z0-9_]+)` \|', ln)
    if m and cur:
        documented[cur].append(m.group(1))
prob = []
for rel in CSVS:
    with open(os.path.join(TREE, rel), newline='') as fh:
        hdr = next(csv.reader(fh))
    doc = documented.get(rel)
    if doc is None:
        prob.append('%s is not described at all' % rel)
        continue
    if doc != hdr:
        prob.append('%s: documented %r against written %r'
                    % (rel, [c for c in doc if c not in hdr],
                       [c for c in hdr if c not in doc]))
for rel in documented:
    if rel not in CSVS:
        prob.append('%s is described and does not exist' % rel)
gate('V2', not prob,
     '%d tables described, %d columns, order and names identical to the '
     'written headers; %s'
     % (len(documented), sum(len(v) for v in documented.values()),
        'no defects' if not prob else prob[:3]))

# ------------------------------------------------------------------------- V3
_MAC = re.compile(r'\\(?:providecommand|renewcommand|newcommand)'
                  r'\{?\\([A-Za-z]+)\}?\{((?:[^{}]|\{[^{}]*\})*)\}')


def macros(base):
    import glob
    main = glob.glob(os.path.join(base, 'technosignatures_*.tex'))
    order = []
    for ln in open(main[0], errors='ignore'):
        m = re.match(r'\s*\\input\{(?:numbers/)?(survey_numbers[A-Za-z0-9_]*)\}', ln)
        if m:
            order.append(m.group(1) + '.tex')
    out = {}
    for fn in order:
        p = os.path.join(base, 'numbers', fn)
        if os.path.exists(p):
            for ln in open(p, errors='ignore'):
                for nm, vv in _MAC.findall(ln):
                    if vv.strip():
                        out[nm] = vv.strip()
    return out


MAC = macros(A.base)
WIN = load('catalogues/spectral_windows.csv')
CA = load('sensitivity/class_A_limits.csv')
CB = load('sensitivity/class_B_limits.csv')
LED = load('candidates/threshold_crossings.csv')
STARS = load('catalogues/stellar_sample.csv')
BLK = load('catalogues/execution_blocks.csv')
CTRL = load('statistics/control_field_statistics.csv')
CNT = load('catalogues/count_accounting.csv')
LINES = load('candidates/molecular_line_matches.csv')
checks = [
    ('windows', len(WIN), int(MAC['NWindows'].replace(',', ''))),
    ('Class A', len(CA), int(MAC['NWinA'].replace(',', ''))),
    ('Class B', len(CB), int(MAC['NWinB'].replace(',', ''))),
    ('crossings', len(LED), int(MAC['EvNCrossRaw'])),
    ('searched positions', len(STARS), int(MAC['NStars'])),
    ('primary-census blocks',
     sum(1 for r in BLK if r['set_name'] == 'primary census'),
     int(MAC['NEB'])),
    ('count rows', len(CNT), int(MAC['MtCountRows'])),
    #: ★★★★ S2/Z-1 (round 26).  THE QUERY A REFEREE MAKES FIRST.  The article
    #: reports 56 crossings as 50 Class A of the primary census + 2 Class A in
    #: archival-tail blocks + 4 Class B, i.e. 52 Class A in quality-passing
    #: data, and `search_class` was EMPTY on the two archival-tail rows, so
    #: `search_class == 'A'` returned 50 and blank was not even a declared
    #: value of the column.  Nothing in V1-V9 compared that column with the
    #: article, because V3 counted ROWS and not VALUES.
    ('Class A crossings by search_class',
     sum(1 for r in LED if r['search_class'] == 'A'),
     int(MAC['EvNCrossQp'])),
    ('Class B crossings by search_class',
     sum(1 for r in LED if r['search_class'] == 'B'),
     int(MAC['EvNCrossFlag'])),
]
#: and the column may only hold values the documentation declares: a blank is
#: how the 52 became 50, and a blank is not a class.
_UNDEC = sorted({(_rel, _r['search_class'])
                 for _rel, _rows in (('candidates/threshold_crossings.csv',
                                      LED),
                                     ('catalogues/spectral_windows.csv', WIN),
                                     ('statistics/'
                                      'control_field_statistics.csv', CTRL))
                 for _r in _rows if _r['search_class'] not in ('A', 'B')})
cmis = [c for c in checks if c[1] != c[2]]
gate('V3', not cmis and not _UNDEC,
     '; '.join('%s %d' % (n, g) for n, g, _w in checks)
     + ('' if not _UNDEC else
        ' UNDECLARED search_class %r' % (_UNDEC,))
     + ('' if not cmis else ' MISMATCH %r' % cmis))

# ------------------------------------------------------------------------- V4
LEAK = re.compile(r'_v\d|_round\d|_r\d\d|v\d+\.\d+|round\s?\d|referee'
                  r'|revision|resubmi|corrigend|erratum|\bdraft\b'
                  r'|this version|previous version|superseded', re.I)
XREF = re.compile(r'\bSec\.|\bAppendix\b|\bTable~?s?\s*\d|\bFig\.'
                  r'|\bFigure~?\s*\d|\bEquation~?\s*\d|\\ref|\\S\\?ref')
#: ★ A reference into ANOTHER paper's table is not a dangling reference here,
#: it is a citation, and the deposit carries four of them in the provenance of
#: the external survey limits.  The clause that tells them apart is the
#: citation itself: an author-and-year on the same line.  It is the presence
#: of the attribution that makes the reference resolvable, which is exactly
#: the property that matters.
CITE = re.compile(r'[A-Z][A-Za-z]+ (?:et al\.?|and [A-Z][A-Za-z]+),? \d{4}')
hits = []
for d, _s, fs in os.walk(TREE):
    for fn in sorted(fs):
        p = os.path.join(d, fn)
        rel = os.path.relpath(p, TREE)
        if LEAK.search(fn):
            hits.append('%s: the NAME carries it' % rel)
        txt = open(p, errors='ignore').read()
        for n, ln in enumerate(txt.splitlines(), 1):
            m = LEAK.search(ln)
            if m:
                hits.append('%s:%d %r' % (rel, n, m.group(0)))
            m = XREF.search(ln)
            if m and not CITE.search(ln):
                hits.append('%s:%d cross-reference %r' % (rel, n, m.group(0)))
gate('V4', not hits,
     'swept %d files with the packaging gate own pattern plus a '
     'cross-reference clause; %s'
     % (sum(len(fs) for _d, _s, fs in os.walk(TREE)),
        'no mention of versions, edits, rounds, referees or corrections, and '
        'no reference into a numbered section, table or figure'
        if not hits else hits[:4]))

# ------------------------------------------------------------------------- V5
EBS = {r['eb'] for r in BLK}
TIDS = {r['target_id'] for r in STARS}
SNAMES = {r['star'] for r in STARS}
jp = []
if {r['eb'] for r in WIN} - EBS:
    jp.append('windows name a block the block table does not')
if {r['target_id'] for r in WIN} - TIDS:
    jp.append('windows name a position the sample table does not')
if {r['star_in_sample'] for r in LED} - SNAMES:
    jp.append('crossings name a star the sample table does not: %r'
              % sorted({r['star_in_sample'] for r in LED} - SNAMES))
_renamed = [r for r in LED if r['star'] != r['star_in_sample']]
if {r['eb'] for r in LED} - EBS:
    jp.append('crossings name a block the block table does not: %r'
              % sorted({r['eb'] for r in LED} - EBS))
# a crossing belongs to the window whose edges contain it
cont = 0
for r in LED:
    if r['in_window_catalogue'] != '1':
        continue
    f = float(r['nu_topo_GHz'])
    m = [w for w in WIN if w['eb'] == r['eb']
         and float(w['nu_lo_GHz']) <= f <= float(w['nu_hi_GHz'])]
    if len(m) >= 1:
        cont += 1
    else:
        jp.append('crossing %s %s lies in no window of its block'
                  % (r['star'], r['nu_topo_GHz']))
ntail = sum(1 for r in LED if r['in_window_catalogue'] != '1')
flagged = sum(1 for w in WIN if w['trigger_whole_beam'] == '1')
dis = [w for w in WIN if w['trigger_flags_agree'] == '0']
if flagged + ntail != len(LED):
    jp.append('%d flagged windows plus %d tail crossings against %d rows'
              % (flagged, ntail, len(LED)))
# GEN (v4.29 fold): the typed 6 was the field-repair delta of the day (9 after the fold).  The deposit states the
# number in its own column documentation; the rows must be the number the deposit says, read from the deposit.
_W2N = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12}
_cd = open(os.path.join(TREE, 'documentation', 'column_descriptions.md'), encoding='utf-8').read()
_mm = re.search(r'`trigger_flags_agree`[^\n]*0 on the (\w+) rows where they do not', _cd)
_ndis = (_W2N.get(_mm.group(1)) or int(_mm.group(1))) if _mm else None
if _ndis is None or len(dis) != _ndis:
    jp.append('%d rows where the two trigger readings differ, against the %s the deposit documents'
              % (len(dis), _ndis))
rec = load('candidates/recurrence_tests.csv')
lk = {(r['eb'], r['nu_topo_GHz']) for r in LED}
if {(r['eb'], r['nu_topo_GHz']) for r in rec} - lk:
    jp.append('recurrence rows that join no crossing')
#: ★★★★ THE WINDOW KEY, AS THE DEPOSIT DOCUMENTS IT: four fields, because a
#: window is a position in a band of a block and two stars can sit at
#: different phase centres in the same spectral window of the same execution
#: block.  `column_descriptions.md:13` has always said so; the three sentences
#: a reader actually follows said three fields and were false.  14 stars
#: collide that way here -- the three-way group PM J03433+1958 / WD 0407+179 /
#: Wolf 219 and every one of the pinned pairs -- and 35 of 1663 window rows
#: sit on a duplicated three-field key.
WKEY = ('target_id', 'eb', 'nu_lo_GHz', 'nu_hi_GHz')
KEYED = (('catalogues/spectral_windows.csv', WIN),
         ('sensitivity/class_A_limits.csv', CA),
         ('sensitivity/class_B_limits.csv', CB),
         ('statistics/control_field_statistics.csv', CTRL))


def wkey(r):
    return tuple(r[c] for c in WKEY)


_dupnote = []
for _rel, _rows in KEYED:
    _ks = [wkey(r) for r in _rows]
    if DRIVE == 1 and _rel == 'catalogues/spectral_windows.csv':
        _ks.append(_ks[0])          # a key the join would silently collapse
    _dupnote.append('%s %d/%d' % (_rel.split('/')[-1][:-4],
                                  len(set(_ks)), len(_ks)))
    if len(set(_ks)) != len(_ks):
        _d = sorted({k for k in _ks if _ks.count(k) > 1})
        jp.append('%s: the documented window key is not unique -- %d '
                  'distinct keys over %d rows, e.g. %r'
                  % (_rel, len(set(_ks)), len(_ks), _d[:1]))
#: and the join itself, with multiplicity on BOTH sides: every control row
#: must match exactly one window row on the documented key.
_winmap = {}
for _w in WIN:
    _winmap.setdefault(wkey(_w), []).append(_w)
if DRIVE == 2:
    #: ★ THE FIRST FORM OF THIS DRIVE DID NOT FIRE, and the reason is the
    #: rule: it popped `next(iter(_winmap))`, the first window row, which no
    #: control row keys on -- the control table is Class A only.  A drive
    #: that does not fail demonstrates nothing, so it removes the window a
    #: control row DOES join.
    _winmap.pop(wkey(CTRL[0]), None)
_nojoin = [r for r in CTRL if len(_winmap.get(wkey(r), [])) != 1]
if _nojoin:
    jp.append('%d control rows do not join exactly one window on the '
              'documented key, e.g. %r'
              % (len(_nojoin), wkey(_nojoin[0])))
gate('V5', not jp,
     '%d crossings resolve to a window by containment, %d lie in '
     'archival-tail blocks and say so, %d flagged windows + %d = %d '
     'crossings, %d rows where the two trigger readings differ, %d crossing '
     'whose position the sample counts under another designation, '
     '%d recurrence rows and %d control rows all join on the documented '
     'four-field key (distinct keys/rows: %s); %s'
     % (cont, ntail, flagged, ntail, len(LED), len(dis), len(_renamed),
        len(rec), len(CTRL), ', '.join(_dupnote),
        'no defects' if not jp else jp[:3]))

# ------------------------------------------------------------------------- V6
#: the ten principal statistics, rebuilt from the deposited tables and
#: compared with what the article publishes.
try:
    from scipy.special import gammainc, gammaincc
    import numpy as np
    HAVE = True
except Exception:
    HAVE = False
V = []


def reb(name, published, got, ok, note):
    V.append((name, published, got, ok, note))


FA = [r for r in CTRL if r['search_class'] == 'A']
trig = sum(float(r['n_ctrl_trig']) / float(r['n_ctrl']) for r in FA)
left = sum(float(r['n_ctrl_trig']) / float(r['n_ctrl'])
           * (1 - float(r['mask_attr_share'])) for r in FA)
tell = sum(float(r['n_ctrl_trig']) / float(r['n_ctrl'])
           * (1 - float(r['mask_attr_share'])) * float(r['telluric_factor'])
           for r in FA)
reb('windows / A / B', '%s / %s / %s' % (MAC['NWindows'], MAC['NWinA'],
                                         MAC['NWinB']),
    '%d / %d / %d' % (len(WIN), len(CA), len(CB)), True, 'search_class')
nat = sum(1 for r in LED if r['attributed'] == '1')
reb('crossings / attributed / unattributed',
    '%s / %s / %d' % (MAC['EvNCrossRaw'], MAC['MkAttr'],
                      int(MAC['EvNCrossRaw']) - int(MAC['MkAttr'])),
    '%d / %d / %d' % (len(LED), nat, len(LED) - nat), True,
    'attributed column of the crossing table')
una = [r for r in LED if r['attributed'] != '1' and r['quality_flagged'] != '1'
       and r['in_window_catalogue'] == '1']
obs = [r for r in una if r['atmospheric_flag'] != '1']
# ★ r28: the published value was TYPED here ('32'), the one number in this
# gate not read from the article -- and it went stale the moment the mask
# changed (sulphur monoxide in: 29).  It is the compared count plus the
# atmospheric one, both macros the article prints.
_una_pub = int(MAC['CeObs']) + int(MAC['CeTlObsCut'])
reb('unattributed, quality-passing, in the window catalogue', '%d' % _una_pub,
    '%d' % len(una), len(una) == _una_pub,
    'three deposited columns, no reading of the article required')
reb('the count compared with chance', MAC['CeObs'], '%d' % len(obs),
    len(obs) == int(MAC['CeObs']),
    'the same selection with the atmospheric flag applied -- which the '
    'deposit now carries, so this count no longer needs a name read out of '
    'the article')
reb('Class A windows reaching the trigger', MAC['CeExpTrig'], '%.4f' % trig,
    abs(trig - float(MAC['CeExpTrig'])) < 0.05,
    'sum of n_ctrl_trig / n_ctrl over the fine-channel control rows')
reb('chance expectation', MAC['CeExp'], '%.4f' % tell,
    abs(tell - float(MAC['CeExp'])) < 0.05,
    'the same sum reduced by mask_attr_share and then by telluric_factor; '
    'after the mask alone %.4f' % left)
if HAVE:
    P = float(gammainc(len(obs), tell))
    reb('its probability', MAC['CeProbNull'], '%.4f' % P,
        abs(P - float(MAC['CeProbNull'])) < 0.02,
        'Poisson upper tail at the rebuilt expectation; the published figure '
        'averages this tail over the resampling the article specifies, which '
        'needs inputs that are not per-window')
    lo, hi = 0.0, 1024.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if float(gammaincc(len(obs) + 1.0, tell + mid)) > 0.05:
            lo = mid
        else:
            hi = mid
    bound = 0.5 * (lo + hi)
    reb('added-population bound', MAC['CeAddLim'],
        '%d (%.2f)' % (int(bound), bound),
        abs(bound - float(MAC['CeAddLim'])) < 1.5,
        'the largest addition to the expectation that still leaves the '
        'observed count compatible at one chance in twenty')
def texnum(s):
    """A published figure like 1.5\\times10^{15} as a float."""
    m = re.match(r'^([0-9.]+)\\times10\^\{?(-?\d+)\}?$', s.strip())
    if m:
        return float(m.group(1)) * 10.0 ** int(m.group(2))
    return float(s.replace(',', ''))


# ★ A LIMIT IS A STATEMENT ABOUT UNMASKED BANDWIDTH, and the deposit now
# carries the column that says how much of each window has any: the survey
# constrains nothing inside the attribution mask, so a window at zero is in
# no distribution of limits.  Rebuilding the headline without this column
# reproduces a figure the article does not print, which is exactly what
# this clause exists to catch.
BEST = {}
SYS = {r['target_id']: r['system'] for r in STARS}
for r in CA:
    u = r.get('unmasked_fraction', '')
    if u == '' or float(u) <= 0.0:
        continue
    s = SYS[r['target_id']]
    e = float(r['eirp_p90_W'])
    BEST[s] = min(BEST.get(s, e), e)
med = st.median(list(BEST.values()))
reb('per-system EIRP90 median', MAC['EirpNinetySysMedA'], '%.3e' % med,
    abs(med / texnum(MAC['EirpNinetySysMedA']) - 1.0) < 0.05,
    'minimum fine-channel limit per system over %d systems' % len(BEST))
reb('per-system EIRP90 span',
    '%s - %s' % (MAC['EirpNinetySysLoA'], MAC['EirpNinetySysHiA']),
    '%.3e - %.3e' % (min(BEST.values()), max(BEST.values())),
    abs(min(BEST.values()) / texnum(MAC['EirpNinetySysLoA']) - 1) < 0.05
    and abs(max(BEST.values()) / texnum(MAC['EirpNinetySysHiA']) - 1) < 0.05,
    'the same minima')
nok = sum(1 for x in V if x[3])
for name, pub, got, ok, note in V:
    print('      %-52s published %-16s rebuilt %-16s %s'
          % (name, pub, got, 'ok' if ok else 'MISMATCH'))
gate('V6', nok == len(V),
     '%d of %d principal statistics rebuild from the deposited tables alone'
     % (nok, len(V)))
print('      NOT rebuildable from the deposit, and the README says so: the '
      'interval on the chance expectation (it folds in the resampling of the '
      'attributed share and the sub-trigger transfer band) and the per-window '
      'completeness of the directly injected windows (their spectra are not '
      'deposited).')

# ------------------------------------------------------------------------- V7
code = os.path.join(TREE, 'code')
runs = [
    ['search_statistic.py', '--demo'],
    ['control_positions.py', '--check',
     '../statistics/control_field_statistics.csv'],
    ['line_mask.py', '--check', '../candidates/threshold_crossings.csv',
     '../candidates/molecular_line_matches.csv'],
    ['injection_recovery.py', '--compare',
     '../sensitivity/injection_recovery.csv'],
]
rc = []
for cmd in runs:
    _env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run([sys.executable] + cmd, cwd=code,
                       capture_output=True, text=True, env=_env)
    rc.append((cmd[0], p.returncode, p.stdout.strip().splitlines()))
gate('V7', all(r[1] == 0 for r in rc),
     '%d reference implementations run their own known-answer tests and the '
     'two that check themselves against the deposited tables agree with them'
     % len(rc))
for nm, r, out in rc:
    print('      %-26s rc=%d  %s' % (nm, r, out[0] if out else ''))
    for ln in out[1:4]:
        print('      %-26s       %s' % ('', ln))

# ------------------------------------------------------------------------- V8
z = zipfile.ZipFile(A.zip)
members = sorted(n for n in z.namelist() if not n.endswith('/'))
root = os.path.basename(TREE) + '/'
tree = sorted(root + os.path.relpath(os.path.join(d, fn), TREE)
              for d, _s, fs in os.walk(TREE) for fn in fs)
same = members == tree
bad = []
for n in members:
    if z.read(n) != open(os.path.join(os.path.dirname(TREE), n), 'rb').read():
        bad.append(n)
stamps = {i.date_time for i in z.infolist()}
h = hashlib.sha256(open(A.zip, 'rb').read()).hexdigest()
#: ►► SHOULD-FIX 7 of the round-25 referee pass.  This line said "23 members"
#: and a reader checking it against `unzip -l` sees **30**, because the archive
#: also carries its 7 directory entries.  Both numbers are right about
#: different things and only one of them was printed, so the reader's check
#: failed against a sound archive.  Print what `unzip -l` prints, and the file
#: count beside it, since the file count is the one V1-V7 reason about.
_dirents = sum(1 for n in z.namelist() if n.endswith('/'))
gate('V8', same and not bad and len(stamps) == 1,
     '%d files in %d directories = %d entries as `unzip -l` lists them, '
     'identical to the tree byte for byte, one timestamp over '
     'every member so the archive is reproducible; %d bytes, sha256 %s'
     % (len(members), _dirents, len(members) + _dirents,
        os.path.getsize(A.zip), h))

# ------------------------------------------------------------------------- V9
#: ★★★★ WHY V9 EXISTS.  The round-25 deposit shipped the pre-A3 line mask
#: (5.041 GHz over 111 transitions, masked fraction 4.27 per cent) and the
#: pre-B9 sub-trigger band (ratio 1.0455 over 3.0-4.5 on 34 984 cells) while
#: the article published 3.71 GHz over 96 at 3.1 per cent and 1.104 over
#: 4-5 on 1 902 cells.  V1-V8 were all green on it, and they had to be:
#: V3 checks ROW COUNTS and V6 checks the ten principal statistics --
#: windows, crossings, the observed count, the expectation, its probability,
#: the bound, the EIRP90 median and span -- and NONE of those is the mask
#: bandwidth, the sub-trigger ratio or the completeness multiplier.  Grepped
#: on the shipping tool, `FrMaskLostGHz`, `MkMaskAGHz`, `masked_GHz`,
#: `p90_multiplier` and `above_threshold` appeared in it ZERO times, so every
#: one of those quantities could be arbitrarily stale under ALL GATES PASS.
#: ★★★ V9 ASKS A DIFFERENT QUESTION FROM V6, DELIBERATELY.  V6 asks whether
#: the deposit rebuilds the article's headline science.  V9 asks whether
#: every deposited number that ALSO APPEARS IN THE ARTICLE equals the macro
#: the article prints it from.  A deposit built from another version's macro
#: layer passes V6 -- it is internally consistent, it is simply a different
#: paper -- and fails V9 on its first row.
W = []


def pin(name, published, got, ok, note):
    W.append((name, published, got, ok, note))


def _f(x):
    #: ★★ AN UNREADABLE DEPOSITED VALUE IS A FAILURE, NOT A TRACEBACK.  V9's
    #: whole purpose is to run on a deposit that is wrong, and a wrong
    #: deposit has empty and malformed cells in it -- the one this clause was
    #: written against had an empty `value` on the band rows.  A traceback
    #: there would stop the gate before it reported the other twenty
    #: findings.  NaN compares false against everything, so an unreadable
    #: cell fails its own row and no other.
    try:
        return float(str(x).replace('\\,', '').replace(',', ''))
    except ValueError:
        return float('nan')


def _merge(ivs):
    out = []
    for lo, hi in sorted(ivs):
        if out and lo <= out[-1][1]:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out


_fc = load('catalogues/frequency_coverage.csv')
_ml = load('candidates/molecular_line_matches.csv')
#: ★★ A MISSING COLUMN IS A FAIL AND NOT A SKIP.  Without `in_mask` the mask
#: cannot be told from the query, so every clause below would silently
#: measure the query and report agreement -- which is exactly the shape of
#: defect V9 exists to catch.  It is reported as a failure with its reason.
#: ★ And it is a `pin` and not an `assert` so that the band and completeness
#: clauses still get to speak: a gate that stops at its first finding hides
#: the others, and on the deposit this was written against there were three.
_HAVEMASK = bool(_ml) and 'in_mask' in _ml[0]
pin('the line table distinguishes the mask from the query',
    'in_mask present', 'present' if _HAVEMASK else 'ABSENT', _HAVEMASK,
    'molecular_line_matches.csv deposits the whole dated query; without an '
    'in_mask column the attribution mask cannot be recovered from it, the '
    'masked bandwidth below is then the query\'s, and a reader applying the '
    'documented rule attributes more crossings than the article reports')
_mk = [r for r in _ml if r.get('in_mask', '1') == '1']
_mgh = sum(float(r['masked_GHz']) for r in _fc)
_ugh = sum(float(r['width_GHz']) for r in _fc)
_ntr = sum(int(r['n_masked_transitions']) for r in _fc)
pin('mask bandwidth, archival union', MAC['FrMaskLostGHz'], '%.3f' % _mgh,
    abs(_mgh - _f(MAC['FrMaskLostGHz'])) < 0.02,
    'masked_GHz summed over the islands of frequency_coverage.csv')
pin('masked fraction of that union', MAC['FrMaskPct'],
    '%.2f' % (100.0 * _mgh / _ugh),
    abs(100.0 * _mgh / _ugh - _f(MAC['FrMaskPct'])) < 0.05,
    'the same sum over the summed island widths (%.3f GHz)' % _ugh)
pin('searched union', MAC['FrMaskUnionGHz'], '%.3f' % _ugh,
    abs(_ugh - _f(MAC['FrMaskUnionGHz'])) < 0.1, 'summed island widths')
pin('transitions in the mask', MAC['FrNTrans'],
    '%d by in_mask, %d by island' % (len(_mk), _ntr),
    len(_mk) == _ntr == int(_f(MAC['FrNTrans'])),
    'the two deposited routes to the count must agree with each other AND '
    'with the article; the deposited query holds %d rows' % len(_ml))
pin('species in the mask', MAC['FrNSpec'],
    '%d' % len({r['species'] for r in _mk}),
    len({r['species'] for r in _mk}) == int(_f(MAC['FrNSpec'])),
    'distinct species among the rows with in_mask = 1')

_C = 299792.458
_half = max(float(r['mask_half_width_kms']) for r in _mk
              if r['mask_half_width_kms'])
_tube = _merge([(float(r['nu_rest_GHz']) * (1 - _half / _C),
                 float(r['nu_rest_GHz']) * (1 + _half / _C)) for r in _mk])
_isla = _merge([(float(r['nu_lo_GHz']), float(r['nu_hi_GHz']))
                for r in WIN if r['search_class'] == 'A'])
_ua = sum(hi - lo for lo, hi in _isla)
_ma = sum(sum(max(0.0, min(a[1], b[1]) - max(a[0], b[0])) for b in _tube)
          for a in _isla)
pin('mask cost of the Class A union', MAC['MkMaskAGHz'], '%.3f' % _ma,
    abs(_ma - _f(MAC['MkMaskAGHz'])) < 0.02,
    'the mask tubes intersected with the merged Class A window union '
    '(%.3f GHz in %d intervals)' % (_ua, len(_isla)))
pin('that cost as a percentage', MAC['MkMaskAPct'],
    '%.2f' % (100.0 * _ma / _ua),
    abs(100.0 * _ma / _ua - _f(MAC['MkMaskAPct'])) < 0.1,
    'the same intersection over the same union')
_nattr = sum(int(r['n_crossings_attributed'] or 0) for r in _ml)
pin('attributions / coincidences',
    '%s / %s' % (MAC['MkAttr'], MAC['MkNCoinc']),
    '%d / %d' % (_nattr, sum(1 for r in LED if r['attributed'] == '1')),
    _nattr == int(_f(MAC['MkAttr']))
    and int(_f(MAC['MkNCoinc'])) == int(_f(MAC['MkAttr'])),
    'the per-transition attributions of the line table against the crossing '
    'table; under A3 option (a) the two published counts are one number, '
    'which is the identity B14 pins')

_at = {round(float(r['threshold_sigma']), 1): r
       for r in load('statistics/above_threshold_cells.csv')}
_nd = load('statistics/null_distribution_tests.csv')


def _nv(q):
    h = [r for r in _nd if r['test'] == 'sub-trigger step'
         and r['quantity'] == q]
    return h[0] if h else None


_names = sorted({r['test'] for r in _nd})
_dup = [n for n in _names if 'sub-trigger' in n or 'near-trigger' in n]
pin('the step is deposited under one test name', 'one', '/'.join(_dup),
    len(_dup) == 1,
    'one quantity may not ship twice under two names: the deposit carried '
    'both `sub-trigger step` (the superseded 3.0-4.5 band) and '
    '`near-trigger band` (the adopted 4-5 one)')
_blo, _bhi = _nv('band_lo'), _nv('band_hi')
pin('the adopted band', '%s - %s' % (MAC['CeNearBandLo'],
                                     MAC['CeNearBandHi']),
    '%s - %s' % (_blo['value'] if _blo else '-',
                 _bhi['value'] if _bhi else '-'),
    bool(_blo) and bool(_bhi)
    and _f(_blo['value']) == _f(MAC['CeNearBandLo'])
    and _f(_bhi['value']) == _f(MAC['CeNearBandHi']),
    'the band the deposit quotes against the band the article quotes')
_r = _nv('ratio')
pin('the ratio over it', MAC['CeNear'], _r['value'] if _r else '-',
    bool(_r) and _f(_r['value']) == _f(MAC['CeNear']),
    'and it must be the adopted band, not a wider one further below the '
    'trigger where the ratio is smaller')
_ns, _nc = _nv('n_star_cells'), _nv('n_control_cells')
_lo, _hi = _f(MAC['CeNearBandLo']), _f(MAC['CeNearBandHi'])
pin('the band is a pair of rungs of the deposited ladder', 'both present',
    '%s present' % ('both' if _lo in _at and _hi in _at else 'not'),
    _lo in _at and _hi in _at,
    'otherwise the band cannot be rebuilt from the deposit at all')
_ds = (int(_at[_lo]['n_star_cells']) - int(_at[_hi]['n_star_cells']))
_dc = (int(_at[_lo]['n_control_cells']) - int(_at[_hi]['n_control_cells']))
pin('its cell counts, rebuilt from that ladder',
    '%s stellar' % MAC['CeNearNStar'], '%d / %d' % (_ds, _dc),
    bool(_ns) and _f(_ns['exact']) == _ds == int(_f(MAC['CeNearNStar']))
    and bool(_nc) and _f(_nc['exact']) == _dc,
    'above_threshold_cells.csv differenced between the two rungs the band '
    'names -- the comparison between the two deposited files whose absence '
    'let them describe two different bands')
_norm = (float(_at[_lo]['ratio']) * int(_at[_lo]['n_control_cells'])
         / int(_at[_lo]['n_star_cells']))
_rb = _ds / (_dc / _norm)
pin('and the ratio rebuilt from those counts', MAC['CeNear'], '%.4f' % _rb,
    abs(round(_rb, 3) - _f(MAC['CeNear'])) < 1e-9,
    'with the per-position normalisation read off the ladder itself rather '
    'than retyped here')
for _q, _m in (('expected_with_step', 'CeExpNear'),
               ('probability_with_step', 'CeProbNear'),
               ('added_population_bound_with_step', 'CeAddLimNear')):
    _h = _nv(_q)
    pin('the one sensitivity test: %s' % _q, MAC[_m],
        _h['value'] if _h else '-',
        bool(_h) and _f(_h['value']) == _f(MAC[_m]),
        'B9 asked for one measurement band and one sensitivity test')
_stale = [r for r in _nd
          if (r['quantity'] == 'band_lo' and r['value']
              and _f(r['value']) != _lo)
          or (r['quantity'] == 'ratio' and r['value']
              and r['test'].endswith('step') and _f(r['value']) != _f(MAC['CeNear']))]
pin('no superseded band survives', 'none', '%d row(s)' % len(_stale),
    not _stale,
    'the 3.0-4.5 band, published as "4.6 per cent", has zero occurrences in '
    'the article and must have none here either')

_cc = load('sensitivity/completeness_calibration.csv')
_ca = [r for r in _cc if r['stratum'] == 'class A'
       and r['quantity'] == 'p90_multiplier']
_ph = [r for r in _cc
       if r['quantity'] == 'deposited_response_phase_mean']
_ir = load('sensitivity/injection_recovery.csv')
_nw = len({(r['eb'], r['window_nu_lo_GHz']) for r in _ir})
pin('Class A completeness multiplier', MAC['EirpNinetyMultA'],
    _ca[0]['value'] if _ca else '-',
    bool(_ca) and abs(_f(_ca[0]['value'])
                      - _f(MAC['EirpNinetyMultA'])) < 0.005,
    'p90_multiplier of the class A row')
_resp = 1.0 / _f(_ph[0]['value']) if _ph else 0.0
pin('its factorisation into response x margin',
    '%s x %s' % (MAC['RpRespFac'], MAC['RpMarginNinety']),
    '%.3f x %.3f' % (_resp, _f(MAC['EirpNinetyMultA']) / _resp if _resp
                     else 0.0),
    bool(_ph) and abs(_resp - _f(MAC['RpRespFac'])) < 0.01
    and abs(_f(MAC['EirpNinetyMultA']) / _resp
            - _f(MAC['RpMarginNinety'])) < 0.01,
    'the response factor is the reciprocal of the deposited phase mean and '
    'the margin is what is left; without this a reader takes the deposited '
    'campaign 90 per cent point -- the margin term alone, near x1.2 -- as a '
    'refutation of the published x3.03')
pin('injected windows: declared against deposited',
    '%s injected' % MAC['NInjWinA'],
    '%s declared / %s deposited / %d in the trials'
    % (_ca[0]['n_injected_windows'] if _ca else '-',
       (_ca[0].get('n_injected_windows_deposited') or '-') if _ca else '-',
       _nw),
    bool(_ca) and _f(_ca[0]['n_injected_windows']) == _f(MAC['NInjWinA'])
    and _ca[0].get('n_injected_windows_deposited')
    and _f(_ca[0]['n_injected_windows_deposited']) == _nw,
    'the declared count is the article\'s; the deposited count must be the '
    'number of windows the trials table actually holds, which is the pair '
    'the deposit got wrong (49 declared beside 28 deposited)')

_wok = sum(1 for x in W if x[3])
for _name, _pub, _got, _ok, _note in W:
    print('      %-46s article %-16s deposit %-24s %s'
          % (_name[:46], str(_pub)[:16], str(_got)[:24],
             'ok' if _ok else 'MISMATCH'))
    if not _ok:
        print('      %-46s         %s' % ('', _note))
gate('V9', _wok == len(W),
     '%d of %d deposited quantities that also appear in the article agree '
     'with the macro the article prints them from' % (_wok, len(W)))

# ------------------------------------------------------------------------ V10
def _v10_cited(base):
    txt = ''
    for p in sorted(glob.glob(os.path.join(base, 'sections', '*.tex'))
                    + glob.glob(os.path.join(base, 'technosignatures_*.tex'))):
        txt += re.sub(r'(?<!\\)%[^\n]*', '', open(p, errors='ignore').read())
    out = set()
    for m in re.finditer(r'\\texttt\{', txt):
        d, j = 0, m.end() - 1
        for k in range(j, len(txt)):
            d += {'{': 1, '}': -1}.get(txt[k], 0)
            if d == 0:
                break
        c = txt[j + 1:k]
        for a, b in (('\\allowbreak', ''), ('\\_', '_'), ('\\-', ''), ('\\/', ''), (' ', '')):
            c = c.replace(a, b)
        #: ★ r28 (integrate, note 6): a path wrapped after \allowbreak carries a
        #: NEWLINE, which the ' ' replacement above left in place, so
        #: `dir/\allowbreak<newline>file` was read as 'dir/<newline>file' and
        #: reported MISSING as a bare 'dir/'.  It failed safe, but such a path
        #: was never checked by name.  All whitespace goes.
        c = re.sub(r'\s+', '', c)
        if '/' in c and '://' not in c and re.search(r'\.[A-Za-z0-9]{1,5}$', c) \
                and not c.startswith('\\'):
            out.add(c)
    return sorted(out)


_cited = _v10_cited(os.path.abspath(A.base))
_mem = set(n for n in z.namelist() if not n.endswith('/'))
if DRIVE == 3:                          # one cited member gone from the zip
    _mem.discard(root + _cited[0]) if _cited else None
_miss = [c for c in _cited if root + c not in _mem]
gate('V10', bool(_cited) and not _miss,
     '%d deposit paths cited by the article, %d of them members of the zip%s'
     % (len(_cited), len(_cited) - len(_miss),
        '' if not _miss else '; MISSING: %s' % ', '.join(_miss)))


print()
if FAILED:
    print('FAILED: %s' % ', '.join(FAILED))
    sys.exit(1)
print('ALL GATES PASS')
