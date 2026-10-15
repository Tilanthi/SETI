#!/usr/bin/env python3
r"""si_r18.py -- the per-window catalogue as a machine-readable table, and the
macros that describe both machine-readable tables.  Round 830.
Writes `si_catalogue.txt` and `survey_numbers_round830.tex`.

WHY THIS EXISTS.  Referee 2's minor item 11: *"provide the per-window
catalogue (1663 rows: window, block, star, channel width, sigma, A, EIRP90,
crossing flag) and the crossing ledger as machine-readable supplementary
tables."*  The journal is an arXiv overlay and publishes no supporting
information of its own, so the mechanism that answers the request is an arXiv
ANCILLARY FILE: a file carried in `anc/` inside the submission package, whose
first listed intended use is "raw data for tables and plots in the article"
(info.arxiv.org/help/ancillary_files.html, re-read 2026-10-13).  Both tables
are therefore written as plain tab-separated text, each with a description of
its own columns in its own header, since an ancillary file is served exactly
as supplied -- the ledger by `ledger_v410.py`, where its rows are composed,
and the catalogue here.
★ An ancillary file is NOT REFEREED and is not part of the article, so the
paper rests no claim on either file and promises only what the files contain;
every number the paper states is in the paper.  ★ The two files are not the
same kind of thing: the ledger is the machine-readable form of a table the
paper typesets in full, and the catalogue is the window-level measurement the
paper's counts are formed from, which no page of it typesets.  Anything
written about them has to keep that distinction.

THREE THINGS THIS GENERATOR IS CAREFUL ABOUT.

 1. ★★★ THE CROSSING FLAG IS THE ADOPTED ONE, NOT THE CATALOGUE'S COLUMN.
    The catalogue's own `crossing` column is the RELEASED flag.  The adopted
    statistic drops four of those rows below the trigger and raises others
    the column does not flag, so a file that published that column beside a
    ledger built on the adopted statistic would disagree with the paper on
    thirteen rows -- and the referee's own reason for asking for these files
    is to check the paper's counts against them.  The flag here is therefore
    the adopted set, joined window by window, through the key and the
    window-containment rule `statchain_v411.py` already owns.

 2. ★★ THE TWO ARCHIVAL-TAIL CROSSINGS ARE NOT IN THIS CATALOGUE AND THE
    FILE SAYS SO.  Their execution blocks are outside the released extent,
    so \NsrCrossN of the \NWindows rows carry an adopted primary crossing
    while the ledger holds \NCross.  That is the referee's own arithmetic in
    minor 6 (1663 - 54 = 1609), it is asserted here in both directions, and
    the header states it rather than leaving a reader to find a discrepancy.

 3. ★ THE COLUMN DESCRIPTION IS BUILT FROM THE FILE'S OWN HEADER.  The
    data-availability statement in the paper describes what these files
    carry, and the description is generated here from the columns actually
    written, phrase by phrase, with the phrase list asserted to cover the
    header exactly and in order.  A sentence in the paper therefore cannot
    promise a column the file does not have.

Usage: si_r18.py [--drive N]      # N = 1..13, each breaking one assertion
"""
import csv
import json
import os
import re
import sys

import star_alias

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 830
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
# ★ Derived from ROUND and never typed again; declared on one line with the
# 'w' below so `roundcollide` can resolve the claim.
OUT = os.path.join(HERE, 'survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTCAT = os.path.join(HERE, 'si_catalogue%s.txt' % SFX)
CATCSV = os.path.join(HERE, 'per_target_results_v3.99.csv')
LEDGERJSON = os.path.join(HERE, 'ledger.json')
LEDGERTXT = os.path.join(HERE, 'si_ledger.txt')
SAMPLETEX = os.path.join(HERE, 'tab_ledgersample.tex')

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-62s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def texval(name):
    """Read a macro back out of the macro layer; the last definition wins."""
    pat = re.compile(r'\\(?:provide|renew|new)command\{?\\%s\}?\{([^}]*)\}'
                     % name)
    got = None
    for f in sorted(os.listdir(HERE)):
        if not (f.startswith('survey_numbers') and f.endswith('.tex')):
            continue
        if '_drive' in f:
            continue
        for mm in pat.finditer(open(os.path.join(HERE, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                got = mm.group(1).strip()
    if got is None:
        raise KeyError(name)
    return got


CAT = list(csv.DictReader(open(CATCSV)))
LEDGER = json.load(open(LEDGERJSON))['rows']

# ---------------------------------------------------------------- the join
# ★ THE WINDOW KEY AND THE CONTAINMENT RULE ARE `statchain_v411.py`'s, NOT A
# SECOND INVENTION.  That generator's own comment records why a name-keyed or
# (eb, flo, fhi)-keyed join is wrong here: `(eb, flo, fhi)` is not unique
# (1628 distinct over 1663 rows) and a star name is not stable across the
# export and the catalogue -- this project has fifteen name-keyed joins in
# its history, the most recent found in this round.  The key is three
# measured quantities of the window itself.


def key(r):
    return (r['eb'], round(float(r['rms_mJy']), 5),
            round(float(r['star_snr']), 4))


_CATEB = {r['eb'] for r in CAT}
LDG_IN = [r for r in LEDGER if r['eb'] in _CATEB]
LDG_OUT = [r for r in LEDGER if r['eb'] not in _CATEB]


def window_of(eb, f):
    """The catalogue row whose window contains f, in block eb, or None."""
    best, bd = None, 1e9
    for r in CAT:
        if r['eb'] != eb:
            continue
        a, b = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        d = 0.0 if a <= f <= b else min(abs(f - a), abs(f - b))
        if d < bd:
            best, bd = r, d
    return (best, bd)


if DRIVE == 5:
    # ★ A LEDGER ROW THAT FINDS NO WINDOW.  S5's count of windows carrying no
    # crossing cannot be driven on its own -- any change to a flag moves both
    # it and S4's count, and drives 1, 3 and 4 each fire it -- so this drive
    # takes S4's third clause instead, which is the failure mode that matters
    # here: a crossing the join cannot place in a window would otherwise be
    # dropped from the file in silence.
    LDG_IN = [dict(r, freq=r['freq'] + 10.0) if i == 0 else r
              for i, r in enumerate(LDG_IN)]

ADOPTED, NOWIN = {}, []
for r in LDG_IN:
    cr, d = window_of(r['eb'], r['freq'])
    if cr is None or d > 0:
        NOWIN.append((r['star'], r['eb'], r['freq']))
        continue
    k = key(cr)
    # One primary crossing to a window: the ledger says so in as many words,
    # so two ledger rows landing on one window is a defect and not a merge.
    assert k not in ADOPTED or DRIVE == 3, (
        'two ledger rows join to one window: %r' % (k,))
    ADOPTED[k] = r
if DRIVE == 4:                     # the RELEASED column, which is the defect
    ADOPTED = {key(r): None for r in CAT if r['crossing'] == 'True'}

DISPO = {}
for ln in open(LEDGERTXT, errors='ignore'):
    if ln.startswith('#') or ln.startswith('star\t'):
        continue
    f = ln.rstrip('\n').split('\t')
    if len(f) > 3:
        DISPO[(f[1], round(float(f[3]), 6))] = f[-1]

# ------------------------------------------------------- the columns, once
# (phrase for the notice, [the columns it covers], how to read each column)
# ★ One phrase may cover more than one column -- a pair of frequency limits
# is one fact about a window -- but every column must be covered exactly
# once and in order, which is what S6 checks.  "A" in the referee's list is
# not a symbol this paper defines, so both readings of it are written: the
# amplitude limit the noise sets, and the drift and acceleration ceilings the
# search covered.
COLS = [
    # ★★★★ v4.22: THE STAR COLUMN IS THE PAPER'S OWN DESIGNATION AND THE
    # EXPORT'S IDENTIFIER IS A COLUMN OF ITS OWN.  This column used to be the
    # raw `star_name` of the extraction -- `bet Pic`, `HD14055`, `BD05 1668`
    # with the sign dropped, nine names with a Gaia DR3 source id glued on --
    # so the file documented "star name, as in the paper" and was not, and
    # the deposited ledger could not be joined to it on star.
    # ★★★ AND THE IDENTIFIER IS KEPT, because collapsing it is the
    # fifteen-times-over defect of this project: the printable designation
    # merges the components of a bound pair observed in ONE block (LP 476-207,
    # 2MASS J05241914-1601153 and TWA 3A, eleven rows between them), so the
    # ROW key is `target_id` and the JOIN key is `star`.  S3 is keyed on the
    # identifier and S11 asserts the designation alone would have merged rows,
    # so neither is a check that cannot fail.
    ('the star, its system and the identifier it was extracted under',
     ['star', 'system', 'target_id'],
     ['star name, as in the paper and as in the crossing ledger',
      'system identifier; components of one system share it',
      'identifier the window was extracted under; distinguishes the '
      'components of a pair observed in one block']),
    ('the execution block and ALMA band', ['eb', 'band'],
     ['ALMA execution block (asdm) identifier',
      'ALMA receiver band']),
    ('the window\'s frequency limits and channel width', [
        'nu_lo_GHz', 'nu_hi_GHz', 'chan_width_Hz'],
     ['lower edge of the spectral window, GHz',
      'upper edge of the spectral window, GHz',
      'delivered channel width, Hz']),
    ('the on-source time', ['on_source_s'],
     ['on-source integration time at this position, s']),
    ('the noise and the amplitude limit it sets', ['rms_mJy', 'smin_mJy'],
     ['per-channel noise at the extraction position, mJy',
      'amplitude limit at the trigger, mJy']),
    ('the drift and acceleration ceilings searched', [
        'drift_max_Hz_s', 'a_max_m_s2'],
     ['largest drift rate searched in this window, Hz/s',
      'line-of-sight acceleration that corresponds to it, m/s^2']),
    ('the adopted EIRP$_{90}$ limit with its interval', [
        'eirp_p90_W', 'eirp_p90_lo_W', 'eirp_p90_hi_W'],
     ['adopted 90 per cent completeness EIRP limit, W',
      'lower end of its interval, W',
      'upper end of its interval, W']),
    ('the distance', ['dist_pc'], ['distance adopted for the star, pc']),
    ('the search class', ['search_class'],
     ['A where the window resolves a carrier, B where it is coarse']),
    ('the crossing flag', ['crossing'],
     ['1 where this window holds an adopted primary threshold crossing']),
    ('and the disposition of any crossing it holds', ['disposition'],
     ['the disposition printed in the crossing ledger, where there is one']),
]
HEADER = [c for _, cs, _ in COLS for c in cs]
DOC = [d for _, _, ds in COLS for d in ds]
if DRIVE == 6:
    HEADER.append('undescribed_extra')
    DOC.append('')

rows = []
for r in CAT:
    k = key(r)
    f_cross = ADOPTED.get(k)
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    cls = r['search_class']
    if DRIVE == 2 and not rows:
        cls = 'B' if cls == 'A' else 'A'
    _star = star_alias.designation(r['star_name'], tex=False)
    if DRIVE == 11:          # the defect itself: the raw export string
        _star = r['star_name']
    v = {
        'star': _star, 'system': r['system_id'],
        'target_id': r['star_name'],
        'eb': r['eb'], 'band': r['band'],
        'nu_lo_GHz': '%.6f' % lo, 'nu_hi_GHz': '%.6f' % hi,
        'chan_width_Hz': '%.1f' % float(r['chanw_Hz']),
        'on_source_s': '%.1f' % float(r['on_source_s']),
        'rms_mJy': '%.5f' % float(r['rms_mJy']),
        'smin_mJy': '%.5f' % float(r['smin_mJy']),
        'drift_max_Hz_s': '%.3f' % float(r['drift_max_Hz_s']),
        'a_max_m_s2': '%.4f' % float(r['a_max_m_s2']),
        'eirp_p90_W': '%.6e' % float(r['eirp_p90_adopted_W']),
        'eirp_p90_lo_W': '%.6e' % float(r['eirp_p90_adopted_lo_W']),
        'eirp_p90_hi_W': '%.6e' % float(r['eirp_p90_adopted_hi_W']),
        'dist_pc': '%.4f' % float(r['dist_pc']),
        'search_class': cls,
        'crossing': '1' if k in ADOPTED else '0',
        'disposition': ('' if f_cross is None else
                        DISPO.get((f_cross['eb'], round(f_cross['freq'], 6)),
                                  '')),
    }
    if DRIVE == 6:
        v['undescribed_extra'] = ''
    rows.append(v)
if DRIVE == 1:
    rows.pop()
if DRIVE == 3:
    rows.append(dict(rows[0]))

NWIN = int(texval('NWindows'))
NWINA, NWINB = int(texval('NWinA')), int(texval('NWinB'))
NCROSS = int(texval('NCross'))
NSRX, NSRQ = int(texval('NsrCrossN')), int(texval('NsrNWin'))
NX = sum(1 for v in rows if v['crossing'] == '1')
NQ = sum(1 for v in rows if v['crossing'] == '0')
NA = sum(1 for v in rows if v['search_class'] == 'A')
NB = sum(1 for v in rows if v['search_class'] == 'B')
# ★ KEYED ON THE IDENTIFIER, NOT ON THE DESIGNATION.  `star` is now the
# printable designation, which merges the components of a bound pair observed
# in one block; `target_id` is what the extraction was keyed on and is what
# makes a row unique.  S11 measures how many rows the designation alone would
# have merged, so this is not a distinction taken on trust.
WKEY = [(v['target_id'], v['eb'], v['nu_lo_GHz'], v['nu_hi_GHz'])
        for v in rows]
SKEY = [(v['star'], v['eb'], v['nu_lo_GHz'], v['nu_hi_GHz']) for v in rows]

print('si_r18 (round %d)%s' % (ROUND, '' if not DRIVE else
                               '  --drive %d' % DRIVE))
ck('S1 one row per catalogue window, and the classes partition it',
   len(rows) == NWIN and NWINA + NWINB == NWIN,
   '%d rows against \\NWindows %d; \\NWinA+\\NWinB = %d'
   % (len(rows), NWIN, NWINA + NWINB))
ck('S2 the search classes are the published ones',
   NA == NWINA and NB == NWINB,
   '%d A / %d B against %d / %d' % (NA, NB, NWINA, NWINB))
ck('S3 (target identifier, block, window) identifies a row uniquely',
   len(set(WKEY)) == len(WKEY),
   '%d distinct keys over %d rows' % (len(set(WKEY)), len(WKEY)))
ck('S4 the crossing flag is the ADOPTED set, and the ledger closes on it',
   NX == NSRX and NX + len(LDG_OUT) == NCROSS and not NOWIN,
   '%d flagged against \\NsrCrossN %d; +%d in blocks outside this catalogue '
   '= \\NCross %d; %d ledger rows found no window'
   % (NX, NSRX, len(LDG_OUT), NCROSS, len(NOWIN)))
ck('S5 the windows carrying no crossing are the published set',
   NQ == NSRQ, '%d against \\NsrNWin %d' % (NQ, NSRQ))
ck('S6 every column is described exactly once, in the order written',
   len(HEADER) == len(DOC) == len(set(HEADER)) and all(DOC),
   '%d columns, %d distinct, %d of %d descriptions non-empty'
   % (len(HEADER), len(set(HEADER)), sum(1 for d in DOC if d), len(DOC)))

# ---------------------------------------------- the ledger file and sample
LDGLINES = [ln.rstrip('\n') for ln in open(LEDGERTXT, errors='ignore')]
LDGHEAD = [ln for ln in LDGLINES if not ln.startswith('#')][0].split('\t')
LDGBODY = [ln for ln in LDGLINES if not ln.startswith('#')][1:]
LDGDOC = [ln for ln in LDGLINES
          if re.match(r'^#\s+\d+\s+\S', ln)]
if DRIVE == 7:
    LDGBODY = LDGBODY[:-1]
ck('S7 the ledger file is one described row per crossing',
   len(LDGBODY) == int(texval('EvNCrossRaw'))
   and len(LDGDOC) == len(LDGHEAD)
   and all(len(ln.split('\t')) == len(LDGHEAD) for ln in LDGBODY),
   '%d rows against \\EvNCrossRaw %s; %d columns, %d described'
   % (len(LDGBODY), texval('EvNCrossRaw'), len(LDGHEAD), len(LDGDOC)))

SAMP = [ln for ln in open(SAMPLETEX, errors='ignore')
        if ln.rstrip().endswith('\\\\')][1:]
NSAMP = len(SAMP) if DRIVE != 8 else len(SAMP) + 1
ck('S8 the paper\'s sample of the ledger is 5-10 rows and is counted from '
   'the fragment', 5 <= NSAMP <= 10 and NSAMP == len(SAMP),
   '%d rows in %s' % (NSAMP, os.path.basename(SAMPLETEX)))

# ★★ S9 IS A PROSE GATE, NOT A VALUE GATE, AND THAT IS THE POINT.  The sample
# shows ten of the ledger's fifteen columns, and its caption names the five it
# leaves out.  A value gate and a prose gate are different gates -- this
# project has a value gate that passed for five rounds while the prose named a
# different coefficient -- so the five omitted column titles are READ OUT of
# the two generated fragments and each is required to appear in the caption.
def _titles(p_):
    for ln in open(os.path.join(HERE, p_), errors='ignore'):
        if ln.rstrip().endswith('\\\\'):
            return [c.strip() for c in ln[:-len(' \\\\\n')].split(' & ')]
    return []


_FULLT, _SAMPT = _titles('tab_ledger.tex'), _titles(SAMPLETEX)
_OMIT = [t for t in _FULLT if t not in _SAMPT]
_CAP = open(os.path.join(HERE, 'sections', 'app_J_falsealarm.tex'),
            errors='ignore').read()
if DRIVE == 9:
    _CAP = _CAP.replace('$\\sigma_{\\rm excl}$', 'the exclusion')
_MISSED = [t for t in _OMIT if t.split(' (')[0] not in _CAP]
PSAMP = [ln for ln in open(os.path.join(HERE, 'tab_persys_sample.tex'),
                           errors='ignore')
         if ln.rstrip().endswith('\\\\')][2:]      # [0,1] are header and unit
PFULL = [ln for ln in open(os.path.join(HERE, 'tab_persys_r17.tex'),
                           errors='ignore')
         if ln.rstrip().endswith('\\\\')][2:]
# ★ The per-system table pairs two systems to a printed line, so its own first
# lines are not its first rows: the left column is the first half of the
# ordering.  The sample is one system to a line, and this requires its systems
# to be the left column of the full table's first lines, in order -- which is
# the only reading of "the first rows" that is true of both files.
_PS = [ln.split('&')[0].strip() for ln in PSAMP]
_PF = [ln.split('&')[0].strip() for ln in PFULL]
if DRIVE == 10:
    _PS = _PS[1:] + _PS[:1]
ck('S10 the per-system sample is 5-10 systems and is the first rows of the '
   'full table', 5 <= len(_PS) <= 10 and _PS == _PF[:len(_PS)],
   '%d systems of %d: %s' % (len(_PS), len(_PF), ', '.join(_PS[:3]) + ' ...'))

ck('S9 the sample\'s caption names every column the sample leaves out',
   _SAMPT and len(_SAMPT) < len(_FULLT) and not _MISSED
   and all(t in _FULLT for t in _SAMPT),
   '%d of %d columns shown; %d omitted, %d of them unnamed in the caption%s'
   % (len(_SAMPT), len(_FULLT), len(_OMIT), len(_MISSED),
      '' if not _MISSED else ': %r' % _MISSED))

# ------------------------------------------------- the files join on star
# ★★★★ S12: THE TWO DEPOSITED FILES ARE JOINABLE ON STAR, AND THE JOIN
# REPRODUCES A NUMBER THE PAPER PRINTS.  They were not: the ledger shipped
# the typeset string (`$\beta$~Pic`, and one star under both `HD 14055` and
# `HD~14055`) and this catalogue shipped the export's own identifier
# (`bet Pic`, `HD14055`, `BD05 1668` with the sign dropped), so a reader
# grouping the ledger's 56 rows by star got 6 and 2 toward the star the paper
# says holds 8 -- and no row of either file could be matched to the other.
# Both columns are now written through `star_alias.designation`, and the
# check is not that the two strings are equal by construction but that the
# GROUPING answers the paper: the star holding the most crossings and its
# count are read out of the macro layer and counted in the file.
# ★ The one star of the ledger that is absent from the catalogue is a
# COMPONENT whose windows the catalogue counts under its primary (Sec. D.5
# says so), and the check requires exactly that shape -- a catalogue name
# extended by a component letter -- rather than a hand-written exception.
LDGSTAR = [ln.split('\t')[LDGHEAD.index('star')] for ln in LDGBODY]
if DRIVE == 13:                 # one row back under a second spelling
    _i13 = LDGSTAR.index(star_alias.plain(texval('MtTopStar')))
    LDGSTAR[_i13] = LDGSTAR[_i13].replace(' ', '~')
CATSTAR = {v['star'] for v in rows}


def _primary_of(s):
    """The catalogue star this ledger name extends by a component letter."""
    cand = [c for c in CATSTAR
            if c != s and s.startswith(c) and 0 < len(s[len(c):].strip()) <= 2]
    return sorted(cand, key=len)[-1] if cand else None


_EXC = [(s, _primary_of(s)) for s in sorted(set(LDGSTAR) - CATSTAR)]
_TOPSTAR, _TOPN = star_alias.plain(texval('MtTopStar')), \
    int(texval('MtTopStarNCross'))
_SMERGE = len(SKEY) - len(set(SKEY))
_SMERGE_OK = all(len({v['system'] for v in rows if (
    v['star'], v['eb'], v['nu_lo_GHz'], v['nu_hi_GHz']) == k}) == 1
    for k in {k for k in SKEY if SKEY.count(k) > 1})
ck('S12 every star of the crossing ledger is in this catalogue but the '
   'declared components, and grouping the ledger by star gives the '
   'published count',
   all(p for _, p in _EXC) and LDGSTAR.count(_TOPSTAR) == _TOPN
   and _SMERGE_OK,
   '%d ledger rows over %d stars; %d absent from the catalogue (%s); '
   '%s holds %d of them against \\MtTopStarNCross %d; the designation alone '
   'would merge %d catalogue rows, every group one system: %s'
   % (len(LDGSTAR), len(set(LDGSTAR)), len(_EXC),
      ', '.join('%s under %s' % (s, p) for s, p in _EXC) or 'none',
      _TOPSTAR, LDGSTAR.count(_TOPSTAR), _TOPN, _SMERGE,
      'yes' if _SMERGE_OK else 'NO'))

# ------------------------------------------------------------------ output
if DRIVE == 12:        # a LaTeX residue in one field, which is the defect
    rows[0] = dict(rows[0], star='$\\beta$~Pic')
with open(OUTCAT, 'w') as fh:
    fh.write('# The per-window catalogue of the ALMA 40 pc technosignature '
             'search: one row per searched spectral window.\n')
    fh.write('# Accompanies the arXiv submission as an ancillary file '
             '(anc/).  Tab-separated; '
             'an empty field is a value that does not apply.\n')
    fh.write('# A window is identified by its target identifier, its '
             'execution block and its frequency limits; the star column is '
             'the designation this star carries in the paper and in the '
             'crossing ledger, and joins the two files.\n')
    if _EXC:
        fh.write('# Every star of the crossing ledger appears here except '
                 '%s, whose extractions are second readings of windows this '
                 'catalogue counts under %s.\n'
                 % (', '.join(s for s, _ in _EXC),
                    ', '.join(p for _, p in _EXC)))
    fh.write('# The crossing flag is the adopted one: %d of these %d windows '
             'hold an adopted primary threshold crossing.  The crossing '
             'ledger holds %d, the other %d lying in archival-tail execution '
             'blocks outside this catalogue.\n' % (NX, len(rows), NCROSS,
                                                   len(LDG_OUT)))
    fh.write('#\n# Columns:\n')
    for i, (c, d) in enumerate(zip(HEADER, DOC), 1):
        fh.write('#  %2d  %-18s %s\n' % (i, c, d))
    fh.write('#\n')
    fh.write('\t'.join(HEADER) + '\n')
    for v in rows:
        vals = [v[c] for c in HEADER]
        assert not any('\t' in x for x in vals), v
        fh.write('\t'.join(vals) + '\n')

# --------------------------------------- no LaTeX in ANY deposited file
# ★★★★ S11: THE NO-LaTeX CLAUSE COVERS ALL THREE ANCILLARY FILES.  It
# covered `si_counts.txt` only -- `counts_r15.py`'s A14, cell by cell, on the
# one file that was clean -- while the ledger shipped `$\beta$~Pic` and
# `CP$-$72 2713` in its key column and had never had the clause applied.
# ★★ IT LIVES HERE AND NOT IN `counts_r15.py` ON PURPOSE: in `make_all.sh`
# that generator runs BEFORE this one, so a clause there would have scanned a
# `si_catalogue.txt` from the previous run -- a check on a stale file, which
# is worse than no check.  This generator is the last of the three to run and
# is the only place all three files exist in their current form.
# ★ Comment lines are exempt and the data rows are not: one column
# description legitimately carries `m/s^2`, and a rule that cannot tell a
# header from a field would have to be relaxed for it.
_TEXRE = re.compile(r'[\\${}~^]')
_RESIDUE = []
for _f in (OUTCAT, LEDGERTXT, os.path.join(HERE, 'si_counts.txt')):
    _data = [l_ for l_ in open(_f, errors='ignore').read().splitlines()
             if l_ and not l_.startswith('#')][1:]
    for _ln, _l in enumerate(_data, 1):
        if _TEXRE.search(_l):
            _RESIDUE.append('%s:%d %s'
                            % (os.path.basename(_f), _ln,
                               [x for x in _l.split('\t')
                                if _TEXRE.search(x)][:2]))
ck('S11 none of the three deposited files carries LaTeX in any field',
   not _RESIDUE,
   'clean over %s' % ', '.join(os.path.basename(p) for p in
                               (OUTCAT, LEDGERTXT, 'si_counts.txt'))
   if not _RESIDUE else '%d row(s): %s' % (len(_RESIDUE),
                                           '; '.join(_RESIDUE[:3])))

# ★ The notice's wording is built from the columns written, not described
# from memory.  Oxford-comma-free list, and the last phrase already carries
# its "and".
m('SiCatColList', ', '.join(p for p, _, _ in COLS[:-1]) + ' ' + COLS[-1][0])
m('SiLdgColList', 'the star, its execution block and band, the crossing '
  'frequency in both frames, the search and control statistics, the nearest '
  'masked transition and the offset from it, the recurrence test and the '
  'disposition')
m('SiLdgSampN', '%d' % len(SAMP))
m('SiPsySampN', '%d' % len(_PS))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by si_r18.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('  %s: %d rows x %d columns' % (os.path.basename(OUTCAT), len(rows),
                                      len(HEADER)))
print('  %s: %d rows x %d columns' % (os.path.basename(LEDGERTXT),
                                      len(LDGBODY), len(LDGHEAD)))
print('  %d macros -> %s' % (len(M), os.path.basename(OUT)))
print('assertions failed: %d %s' % (len(FAIL), FAIL))
if FAIL and not DRIVE:
    raise SystemExit('si_r18: %d assertion(s) failed: %s' % (len(FAIL), FAIL))
if DRIVE and not FAIL:
    raise SystemExit('si_r18: --drive %d perturbed nothing -- a drive that '
                     'does not fire is not a drive' % DRIVE)
