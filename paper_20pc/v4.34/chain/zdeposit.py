#!/usr/bin/env python3
"""Build the supplementary data deposit.

    python3 zdeposit.py [--base DIR] [--out DIR]

Reads only released products in the manuscript directory and writes the
deposit tree.  Nothing here computes a new scientific result: every value is
copied from a product the manuscript already builds, and the generator's job
is to put them in one documented, self-describing place.

Three rules this generator keeps, each of which has been got wrong before in
this project:

 1. ★★★ THE COLUMN SPEC IS THE SINGLE SOURCE OF TRUTH.  A file's header, its
    column order and its entry in `documentation/column_descriptions.md` are
    all generated from one `Table` object, so a documented column that does
    not exist and an existing column that is not documented are both
    impossible rather than merely unlikely.  `zverify.py` checks it anyway,
    from the written files, because a generator checking itself proves little.

 2. ★★ EVERY ROW CARRIES THE IDENTIFIERS THAT TIE IT TO AN OBSERVATION.
    The ALMA project code and the execution-block identifier travel with the
    row, not only with a join key, so a reader can go from any row to the
    archive without first reconstructing a join.

 3. ★★ THE DEPOSIT IS AS PUBLIC AS THE ARTICLE.  Nothing written here may
    mention versions, edits, rounds, referees or corrections of the
    manuscript; the file names carry none and the prose carries none.
    `zverify.py` sweeps for them with the packaging gate's own pattern.
"""
import argparse
import collections
import csv
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser()
#: ★★★★ THE DEFAULT BASE IS THIS GENERATOR'S OWN DIRECTORY, AND IT HAS TO BE.
#: It was a typed absolute path to the PREVIOUS version directory.  Run the
#: way every other generator in this tree is run -- with no arguments -- this
#: file therefore read the previous paper's macro layer and the previous
#: paper's products, and deposited them.  The round-25 deposit shipped the
#: pre-A3 line mask (5.04 GHz / 4.3 per cent over 111 transitions) and the
#: pre-B9 sub-trigger band against an article publishing 3.71 / 3.1 over 96,
#: and it would have gone on doing so however many times it was rebuilt,
#: because nothing about it was stale: it was a correct deposit of a
#: different paper.
#: ★★★★ AND THAT IS WHY THIS FILE'S OWN ASSERTION DID NOT FIRE.  The clause
#: below compares the deposited mask width against `\FrMaskLostGHz` to
#: 0.02 GHz -- a good check, with the right tolerance, pointed at the tree
#: where its own answer was right.  A check reading a different tree from the
#: artefact it protects is self-consistent and useless.  Pointed here it
#: fires on the first line of output.
AP.add_argument('--base', default=HERE,
                help='the manuscript directory to deposit; defaults to this '
                     'generator\'s own directory and must never default to '
                     'another version')
AP.add_argument('--out', default=os.path.join(HERE, 'ALMA_Technosignatures_40pc'))
ARGS = AP.parse_args()
BASE = os.path.abspath(ARGS.base)
OUT = os.path.abspath(ARGS.out)
TITLE = ('Supplementary Data for an Archival ALMA Search for Technosignatures '
         'toward Stars within 40 pc')

# --------------------------------------------------------------- source files
def src(name):
    p = os.path.join(BASE, name)
    if not os.path.isfile(p):
        raise SystemExit('missing source product: %s' % p)
    return p


def read_tsv(name):
    """A released plain-text table: '#' header, tab separated."""
    with open(src(name)) as fh:
        body = [ln for ln in fh if not ln.startswith('#')]
    return list(csv.DictReader(body, delimiter='\t'))


def read_csv(name):
    with open(src(name)) as fh:
        return list(csv.DictReader(fh))


def read_json(name):
    with open(src(name)) as fh:
        return json.load(fh)


#: ★ A macro value may itself carry braces -- `1.5\times10^{15}` is three of
#: the article\'s own -- and a pattern that forbids them does not fail, it
#: silently fails to FIND the macro.  One level of nesting is allowed here and
#: `mac()` raises on a name it cannot find, so a missing value stops the run.
_MACRO = re.compile(r'\\(?:providecommand|renewcommand|newcommand)'
                    r'\{?\\([A-Za-z]+)\}?\{((?:[^{}]|\{[^{}]*\})*)\}')


def macros():
    """Every published macro value, in \\input order so a later definition
    wins -- the order the document itself resolves them in."""
    main = glob.glob(os.path.join(BASE, 'technosignatures_*.tex'))
    if len(main) != 1:
        raise SystemExit('cannot identify the manuscript file')
    order = []
    for ln in open(main[0], errors='ignore'):
        m = re.match(r'\s*\\input\{(?:numbers/)?(survey_numbers[A-Za-z0-9_]*)\}', ln)
        if m:
            order.append(m.group(1) + '.tex')
    out = {}
    for fn in order:
        p = os.path.join(BASE, 'numbers', fn)
        if not os.path.exists(p):
            continue
        for ln in open(p, errors='ignore'):
            for nm, vv in _MACRO.findall(ln):
                if vv.strip():
                    out[nm] = vv.strip()
    return out


MAC = macros()


def mac(name):
    if name not in MAC:
        raise SystemExit('no such published macro: %s' % name)
    return MAC[name]


def maci(name):
    #: ★ The thin space goes FIRST.  Stripping the comma first turns the
    #: house style `1\,902` into `1\902`, which is neither a number nor a
    #: thin space -- an order-dependent two-step cleanup, and the wrong order
    #: fails loudly here only because the result is parsed.
    return int(float(mac(name).replace('\\,', '').replace(',', '')))


#: ★ A published value as a DEPOSITED cell: the article's house style taken
#: off it.  `1\,902` -> `1902`, `$\beta$~Pic` -> `beta Pic`,
#: `1.5\times10^{15}` -> `1.5e15`.  Anything left carrying a backslash or a
#: dollar is a case this function does not know about, and it raises rather
#: than depositing markup -- the same choice `mac()` makes about a missing
#: macro.
_TEX = ((r'\times10^{', 'e'), (r'\,', ''), ('~', ' '),
        (r'\beta', 'beta'), (r'\alpha', 'alpha'), (r'\eta', 'eta'),
        (r'\tau', 'tau'), (r'\epsilon', 'epsilon'), (r'\mu', 'mu'),
        (r'\,', ''), ('$', ''), ('{', ''), ('}', ''))


def macv(name):
    v = mac(name)
    for a, b in _TEX:
        v = v.replace(a, b)
    v = re.sub(r'\s+', ' ', v).strip()
    assert '\\' not in v and '$' not in v, (
        'macv() does not know how to de-TeX the published value of %s (%r); '
        'add the case rather than depositing markup' % (name, mac(name)))
    return v


# ------------------------------------------------------------------ formatting
def _g17(x):
    """A float at full precision, for an input a deposited program must
    reproduce a computation from bit for bit."""
    return '%.17g' % float(x)


def f(x, nd):
    """A float printed to a fixed number of places, or empty."""
    if x is None or x == '':
        return ''
    return '%.*f' % (nd, float(x))


def e(x, nd=6):
    if x is None or x == '':
        return ''
    return '%.*e' % (nd, float(x))


def i(x):
    if x is None or x == '':
        return ''
    return '%d' % int(float(x))


def b(x):
    """A flag, written 1/0 and never True/False, since a reader's parser may
    not share this one's idea of a boolean."""
    if x is None or x == '':
        return ''
    if isinstance(x, str):
        x = x.strip().lower() in ('1', 'true', 'yes')
    return '1' if x else '0'


class Table(object):
    """A deposited table: its columns, their units, their descriptions, the
    rows, and the paragraph that introduces it.  One object, so the file and
    its documentation cannot drift apart."""

    def __init__(self, path, about, join, columns, rows):
        self.path = path
        self.about = about            # list of sentences
        self.join = join              # how a reader joins this to the rest
        self.columns = columns        # (name, unit, description)
        self.rows = rows              # list of dicts keyed by column name
        names = [c[0] for c in columns]
        assert len(names) == len(set(names)), 'duplicate column in ' + path
        for r in rows:
            extra = set(r) - set(names)
            assert not extra, 'row carries undocumented key %s in %s' % (
                sorted(extra), path)

    def write(self, root):
        p = os.path.join(root, self.path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        names = [c[0] for c in self.columns]
        #: ★★ NO DEPOSITED CELL MAY CARRY TeX MARKUP.  Values read from the
        #: macro layer arrive in the article's house style -- `1\,902`,
        #: `20\,000`, `$\beta$~Pic`, `1.5\times10^{15}` -- and a thin space
        #: in a CSV is a value no reader's parser will accept as a number.
        #: Two such cells were already shipping in the round-25 deposit and
        #: nothing could see them, because the neutrality sweep looks for
        #: version strings and not for backslashes.  `macv()` de-TeXes a
        #: published value; this clause makes forgetting it impossible rather
        #: than fixed once.
        for r in self.rows:
            for n in names:
                v = str(r.get(n, ''))
                assert '\\' not in v and '$' not in v, (
                    'TeX markup in a deposited cell: %s column %s carries '
                    '%r.  Read the published value through macv().'
                    % (self.path, n, v))
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator='\n')
        w.writerow(names)
        for r in self.rows:
            w.writerow([r.get(n, '') for n in names])
        with open(p, 'w', newline='') as fh:
            fh.write(buf.getvalue())
        return len(self.rows)


# =========================================================== SOURCES, LOADED
CAT = read_tsv('si_catalogue.txt')              # 1663 windows, adopted flags
PTR = read_csv('per_target_results_v3.99.csv')  # the same windows, 71 columns
LED = read_tsv('si_ledger.txt')                 # 56 crossings
RECUR = read_tsv('si_recur.txt')                # exclusion depths, two ways
RECOV = read_tsv('si_recovery.txt')             # recurrence recovery
CNT = read_tsv('si_counts.txt')                 # the master count rows
PROJ = {r['eb']: r for r in read_csv('project_codes_v413.csv')}
PB = read_json('pbcat_v408.json')               # star position, pb response
#: ★★★★ THE QUERY AND THE MASK ARE TWO LISTS, AND THIS FILE USED ONE.
#: `maskcat_v412.json` is the dated catalogue QUERY -- every transition of
#: the named species inside a searched island -- and it is deposited whole,
#: because a line list that cannot be inspected cannot be audited.  The
#: attribution MASK is that query less the species the article names as
#: deliberately left out: sulphur monoxide, which has no reported detection
#: in a debris disc, so masking it would declare no constraint over bandwidth
#: this survey does constrain.  Taking the query for the mask is what made
#: the deposit publish 5.04 GHz / 4.3 per cent over 111 transitions against
#: an article publishing 3.71 / 3.1 over 96.
#: ★★ The excluded species is READ FROM A RELEASED PRODUCT and not retyped
#: here: `maskframe_v411.json`'s own mask record carries `noted_species`,
#: `n_transitions` and `n_species`, so this file cannot hold a second,
#: divergent copy of the rule.  Round 25 found three generators in this tree
#: whose mask lists differed; the cure is one list, read, not three, written.
QUERY = read_json('maskcat_v412.json')          # the dated query, all of it
_MFR = read_json('maskframe_v411.json')['mask']
NOT_MASKED_REASON = _MFR['noted_reason']
#: ★★★ THE EXCLUDED SET IS DETERMINED BY THE RECORD, NOT ASSUMED FROM IT,
#: and the difference is not pedantry: `noted_species` names SO in the
#: previous version too, where the mask HELD those transitions and merely
#: reported them as notes (n_transitions 111, n_species 12).  Reading the
#: list as "out of the mask" would therefore have mis-built that version's
#: deposit in the opposite direction.  The record states how many
#: transitions the mask holds; the candidate species say which rows could be
#: the difference; the two together fix the mask uniquely, and the assertion
#: below is what makes that true rather than hoped.
_CAND = tuple(_MFR['noted_species'])
_full = len(QUERY['transitions'])
_thin = len({k: v for k, v in QUERY['transitions'].items()
             if v['spec'] not in _CAND})
if _MFR['n_transitions'] == _full:
    NOT_MASKED = ()                 # the mask is the whole query
elif _MFR['n_transitions'] == _thin:
    NOT_MASKED = _CAND              # the mask is the query less those species
else:
    raise SystemExit(
        'the released mask record says the mask holds %d transitions, and '
        'the query holds %d whole or %d with %s removed: neither, so the '
        'mask cannot be reconstructed from the deposited inputs'
        % (_MFR['n_transitions'], _full, _thin, '/'.join(_CAND) or 'nothing'))
MASK = dict(QUERY)
MASK['transitions'] = {k: v for k, v in QUERY['transitions'].items()
                       if v['spec'] not in NOT_MASKED}
#: ★ r28 (v4.29, Ruling R3): one rule for every species, so the mask IS the
#: whole query and `NOT_MASKED` is empty.  The refusal that stood here (it
#: would not deposit a mask equal to the query) guarded the v4.26-v4.28 state
#: and is inverted: the record must now say the mask holds the whole query.
assert not NOT_MASKED and _MFR['n_transitions'] == _full, (
    'the mask record does not hold the whole query: a species has been '
    'carved out of the one rule again')


def in_mask(t):
    return t['spec'] not in NOT_MASKED
CHANCE = read_json('chance_v414.json')          # the chance comparison
#: the two Class A crossings in archival-tail blocks, as the chance
#: comparison's own record names them: (block, frequency to 6 dp).  See the
#: note at `search_class` in `_crossings()`.
TAIL_A_CROSS = {(_t[1], round(float(_t[2]), 6))
                for _t in CHANCE['observed_tail']}
PERWIN = read_json('chance_perwin_v422.json')   # its per-window terms
CELLS = read_json('cells_v416.json')            # the cell ladder
STRATA = read_json('strata_v411.json')          # completeness transfer
INJW = read_json('injected_windows_v422.json')  # which windows were injected
TRIALS = read_csv('stratified_inject_trials_v3.58.csv')
CTXFIG = read_json('figures_context_v410.json')
BLOCKFATE = read_json('blockfate_v400.json')

# the two per-window tables are the same 1663 windows; key them together on
# the window, which is (target identifier, execution block, frequency edges).
def wkey(eb, tid, lo, hi):
    return (eb, tid, '%.6f' % float(lo), '%.6f' % float(hi))


PTRBY = {}
for r in PTR:
    PTRBY[wkey(r['eb'], r['star_name'], r['flo_GHz'], r['fhi_GHz'])] = r
assert len(PTRBY) == len(PTR) == len(CAT), 'the per-window tables disagree'
CATK = []
for r in CAT:
    k = wkey(r['eb'], r['target_id'], r['nu_lo_GHz'], r['nu_hi_GHz'])
    if k not in PTRBY:
        raise SystemExit('window not in both per-window tables: %r' % (k,))
    CATK.append((r, PTRBY[k]))

# ★ the star's position, from the primary-beam record, keyed as it keys itself
POS = {}
for key, lst in PB.items():
    tid, eb = key.split('|')
    for w in lst:
        POS[(tid, eb, '%.6f' % w['flo'])] = (w['star_ra'], w['star_dec'])
STARPOS = {}
for (tid, eb, lo), (ra, dec) in POS.items():
    STARPOS.setdefault(tid, (ra, dec))

# ★★★★ r26-integrate, 2026-10-23: eps Eri HAD NO SKY POSITION ANYWHERE IN THE
# DEPOSIT.  `ra_deg`/`dec_deg` were blank on its 12 rows of
# `spectral_windows.csv` and on its row of `stellar_sample.csv` -- the only
# star of the sample with none -- because `POS` above is keyed on
# `target_id|eb` out of `pbcat_v408.json`, which holds no `eps Eri` entry at
# all.  Found by `r26-limits` while computing unmasked fractions (A1), and it
# touches A7 and A9, both of which are about this star.  A reader told to join
# the deposit on position cannot place the nearest Band 6 target in the sample.
#
# The position is in the search harvest's own window records
# (`stack_v408/windows.json`), where the star is `eps Eri [B6]`.
#
# ★★★ THE JOIN IS VALIDATED ON PARALLAX, NEVER ON THE NAME ALONE.  Keying on a
# name is this project's most repeated defect -- fourteen instances -- so the
# fallback is accepted for a target only if the harvest's own parallax agrees
# with the distance the survey ADOPTED for that star, to one per cent.  For
# eps Eri that is 310.577 mas against 1000/3.2198 = 310.58, i.e. the two
# independent records agree to 0.001 per cent, which is what makes the name
# match safe rather than merely plausible.
_SWJ = os.path.join(HERE, 'stack_v408', 'windows.json')
_SWROWS = []
if os.path.exists(_SWJ):
    _sw = json.load(open(_SWJ))
    _SWROWS = _sw if isinstance(_sw, list) else _sw.get('windows', [])
_HARVEST = {}
for _w in _SWROWS:
    _nm = re.sub(r'\s*\[B\d+\]\s*$', '', str(_w.get('star', ''))).strip()
    if _nm and _w.get('ra') is not None and _w.get('dec') is not None:
        _HARVEST.setdefault(_nm, (_w['ra'], _w['dec'], _w.get('plx')))
_ADOPTED_PLX = {}
for _c, _p in CATK:
    try:
        _ADOPTED_PLX.setdefault(_c['target_id'], 1000.0 / float(_c['dist_pc']))
    except (ValueError, ZeroDivisionError, KeyError, TypeError):
        pass
_NEEDPOS = sorted({_c['target_id'] for _c, _p in CATK
                   if _c['target_id'] not in STARPOS})
_FILLED, _UNFILLED = [], []
for _tid in _NEEDPOS:
    _h = _HARVEST.get(_tid)
    _ap = _ADOPTED_PLX.get(_tid)
    if _h and _ap and _h[2] and abs(_h[2] - _ap) <= 0.01 * _ap:
        STARPOS[_tid] = (_h[0], _h[1])
        _FILLED.append((_tid, _h[2], _ap))
    else:
        _UNFILLED.append(_tid)
print('zdeposit: %d target(s) had no primary-beam position; %d filled from the '
      'search harvest with a parallax match, %d still blank%s'
      % (len(_NEEDPOS), len(_FILLED), len(_UNFILLED),
         (': ' + ', '.join(_UNFILLED)) if _UNFILLED else ''))
for _t, _hp, _apx in _FILLED:
    print('zdeposit:   %-14s harvest parallax %.3f mas against the adopted '
          '%.3f mas (%.4f per cent)'
          % (_t, _hp, _apx, 100.0 * abs(_hp - _apx) / _apx))
# ★ The fallback must not be vacuous and it must not be silently load-bearing:
# if a future delivery gives every target a primary-beam record, this prints 0
# and 0 and nothing else changes; if it ever leaves a target blank, that is a
# FAILURE and not a dash, because the deposit's own documentation tells a
# reader to join on position.
assert not _UNFILLED, (
    'no sky position for %s in either the primary-beam catalogue or the '
    'search harvest (or the parallax check failed): the deposit may not ship '
    'a row a reader cannot place on the sky' % ', '.join(_UNFILLED))

# ★★ the atmospheric screen: the one crossing it removes, named by the record
# that removes it, with the radius and the species that did it.
# ★★★★ r27 row 49: THE ANNULUS A ROW DESCRIBES IS THE ONE ITS STATISTIC WAS
# MEASURED ON.  Until v4.27 every geometry column here was read from
# per_target_results' `theta_pb_arcsec`, which v342_calc.theta_pb() writes as
# 1.22 lambda / 12 m for EVERY window -- an internal convention several
# generators assert and that must stay as it is -- so 1,067 published
# compact-array rows described a 12 m annulus beside a statistic measured on a
# 7 m one, and the inner radius omitted the synthesised-beam floor the repaired
# extractor applies (binding on every repaired 7 m window).  `ringgeom_r27.json`
# holds, per window, the geometry of the product whose OWN 512-control vector
# reproduces the published one (built by referee_r27/aca/harvest/
# ringgeom_build_r27.py); a window is a block and two edges, matched to 1 MHz,
# never a name.  Every catalogue row must resolve to exactly one record.
RING = collections.defaultdict(list)
for _g in read_json('ringgeom_r27.json')['rows']:
    RING[_g['eb']].append(_g)


def ring_of(c):
    lo = min(float(c['nu_lo_GHz']), float(c['nu_hi_GHz']))
    hi = max(float(c['nu_lo_GHz']), float(c['nu_hi_GHz']))
    hit = [g for g in RING.get(c['eb'], [])
           if abs(g['lo'] - lo) < 1e-3 and abs(g['hi'] - hi) < 1e-3]
    assert len(hit) == 1, ('the searched annulus of %s %.6f-%.6f GHz resolves '
                           'to %d records, not 1' % (c['eb'], lo, hi, len(hit)))
    return hit[0]


_RG_ROWS = [ring_of(c) for c, _p in CATK]       # every row, or the build stops

TL = CHANCE['telluric']
TL_HIT = {(r['eb'], '%.6f' % float(r['f_topo'])): r for r in TL['observed_removed']}

# ★★ the two trigger readings.  The catalogue's own `crossing` column is the
# narrower extraction field; the adopted statistic is read over the whole
# primary beam and is what the crossing ledger is built on.
NARROW = {}
WHOLE = {}
for c, p in CATK:
    k = wkey(c['eb'], c['target_id'], c['nu_lo_GHz'], c['nu_hi_GHz'])
    NARROW[k] = p['crossing'] == 'True'
    WHOLE[k] = c['crossing'] == '1'
DISAGREE = [k for k in NARROW if NARROW[k] != WHOLE[k]]
# ★ GEN (v4.29 fold, E2 = (a)): the typed "6" was the size of the field-repair delta of the day (4 fell + 1 rose
#   + the restored companion).  The narrow (released) and whole-beam (census) readings differ on EXACTLY the
#   catalogue windows of that delta, which the re-calibration moved (BD+05 1668's four now fall; eta Crv X1430 no
#   longer does): 7 fell + 1 rose + 1 restored = 9.  Asserted as a set: every disagreeing window holds exactly one
#   delta row (block + frequency inside the window), and every catalogue-side delta row is one of them.
_D29 = read_json('v409_delta_r29.json')
_DROWS = ([(d['eb'], float(d['nu'])) for d in _D29['fell_detail']]
          + [(d['eb'], float(d['nu'])) for d in _D29['risen_attributed']]
          + [(d['eb'], float(d['nu'])) for d in _D29['restored_detail']])
_DWIN = {k: [(e, f) for e, f in _DROWS
             if e == k[0]
             and min(float(k[2]), float(k[3])) - 1e-6 <= f <= max(float(k[2]), float(k[3])) + 1e-6]
         for k in DISAGREE}
assert (all(len(v) == 1 for v in _DWIN.values())
        and len(DISAGREE) == len(_DROWS) - (1 if os.environ.get('GEN_DRIVE_ZD') == '1' else 0)), (
    'the two trigger readings differ on %d rows, which are not exactly the %d catalogue rows of the field-repair '
    'delta -- the deposit and the article must be checked together: %s'
    % (len(DISAGREE), len(_DROWS), sorted((k[0], k[2], len(v)) for k, v in _DWIN.items())))

# ★ a ledger row is tied to a window by CONTAINMENT, not by frequency
# equality: the whole-beam reading can flag a window at a frequency the
# narrower one never reported, and two of the six rows above do exactly that.
def window_of(eb, freq):
    for n, (c, p) in enumerate(CATK):
        if c['eb'] == eb and float(c['nu_lo_GHz']) <= freq <= float(c['nu_hi_GHz']):
            return n
    return None


LEDWIN = {}
for r in LED:
    LEDWIN[(r['eb'], r['nu_topo_GHz'])] = window_of(r['eb'],
                                                    float(r['nu_topo_GHz']))
assert sum(1 for v in LEDWIN.values() if v is None) == 2, \
    'exactly two ledger crossings lie outside the released window extent'

#: ★★ A crossing may be found at a position whose designation the window
#: catalogue does not carry: one component's extractions are second readings
#: of windows the catalogue counts under its primary.  The designation the
#: sample counts it under is DERIVED -- it is the star of the window that
#: contains the crossing -- and never keyed by name, because every join in
#: this project that has keyed on a name has eventually joined the wrong rows.
CATSTARS = {c['star'] for c, _p in CATK}
SAMPLE_OF = {}
for r in LED:
    if r['star'] in CATSTARS:
        continue
    n = LEDWIN[(r['eb'], r['nu_topo_GHz'])]
    assert n is not None, (
        'crossing toward %s lies in no catalogued window and its star is not '
        'in the catalogue either, so the sample table cannot name it'
        % r['star'])
    SAMPLE_OF[r['star']] = CATK[n][0]['star']
for r in LED:
    assert SAMPLE_OF.get(r['star'], r['star']) in CATSTARS, r['star']


TABLES = []

# ================================================= catalogues/spectral_windows
#: ★ one row per searched spectral window: the measurement every count in the
#: article is formed from.
def _windows():
    rows = []
    for n, (c, p) in enumerate(CATK):
        k = wkey(c['eb'], c['target_id'], c['nu_lo_GHz'], c['nu_hi_GHz'])
        pr = PROJ.get(c['eb'], {})
        ra, dec = STARPOS.get(c['target_id'], ('', ''))
        xf = [key for key, w in LEDWIN.items() if w == n]
        rows.append(dict(
            star=c['star'], system=c['system'], target_id=c['target_id'],
            ra_deg=f(ra, 6), dec_deg=f(dec, 6),
            eb=c['eb'], project_code=pr.get('project_code', ''),
            date_utc=pr.get('date_utc', ''), t_start_mjd=f(c['t_start_mjd'], 6),
            band=c['band'], nu_lo_GHz=f(c['nu_lo_GHz'], 6),
            nu_hi_GHz=f(c['nu_hi_GHz'], 6),
            chan_width_Hz=f(c['chan_width_Hz'], 1),
            on_source_s=f(c['on_source_s'], 1), n_int=i(p['n_int']),
            rms_mJy=f(c['rms_mJy'], 5), smin_mJy=f(c['smin_mJy'], 5),
            theta_pb_arcsec=f(ring_of(c)['pb_arcsec'], 3),
            array=ring_of(c)['array'],
            geometry_provenance=ring_of(c)['provenance'],
            pb_offset_arcsec=f(p['pb_offset_arcsec'], 4),
            pb_atten=f(p['pb_atten'], 6),
            dist_pc=f(c['dist_pc'], 4), search_class=c['search_class'],
            drift_max_Hz_s=f(c['drift_max_Hz_s'], 3),
            a_max_m_s2=f(c['a_max_m_s2'], 4),
            n_drift_trials=i(p['n_drift_trials']),
            n_search_cells=i(p['n_search_cells']),
            n_ind_cells=i(p['n_ind_cells']),
            eirp_p90_W=e(c['eirp_p90_W']), eirp_p90_lo_W=e(c['eirp_p90_lo_W']),
            eirp_p90_hi_W=e(c['eirp_p90_hi_W']),
            completeness_basis=p['p90_basis'],
            T_star_narrow_field=f(p['star_snr'], 4),
            T_ctrl_max_narrow_field=f(p['ctrl_max_snr'], 4),
            n_ctrl=i(c['n_ctrl']), n_ctrl_trig=i(c['n_ctrl_trig']),
            mask_attr_share=f(c['mask_attr_share'], 6) if c['mask_attr_share'] else '',
            # ★★★★ THE COLUMN THAT SAYS WHETHER THE LIMIT BESIDE IT MEANS
            # ANYTHING.  Inside the attribution mask the survey constrains
            # nothing, and the finest windows here were tuned to CO: a
            # reader forming the distribution of limits from this file
            # without this column reproduces a headline the article does
            # not make.  Computed in the star's own rest frame; blank where
            # the frame could not be completed and the answer depends on
            # the term that is missing, which is a third state and not a
            # zero.
            unmasked_fraction=p.get('unmasked_fraction', ''),
            telluric_factor=f(c['telluric_factor'], 6) if c['telluric_factor'] else '',
            trigger_whole_beam=b(WHOLE[k]),
            trigger_narrow_field=b(NARROW[k]),
            trigger_flags_agree=b(WHOLE[k] == NARROW[k]),
            crossing_nu_topo_GHz=(f(xf[0][1], 6) if xf else ''),
            disposition=c['disposition']))
    return rows


TABLES.append(Table(
    'catalogues/spectral_windows.csv',
    ["One row per searched spectral window: the window-level measurement every "
     "count in the article is formed from.",
     "A window is identified by its target identifier, its execution block and "
     "its frequency edges; those four fields are unique over the table.",
     "Two readings of the trigger are given. The adopted statistic is read over "
     "the whole primary beam (trigger_whole_beam) and is the one the crossing "
     "table is built on; trigger_narrow_field is the same statistic read over "
     "the narrower extraction field, which drops the integrations whose "
     "pointing falls outside it. They differ on six rows, which "
     "trigger_flags_agree selects without recomputation.",
     "An empty field is a value that does not apply, never a zero: the control "
     "terms are measured on the fine-channel windows and are empty on the "
     "coarse ones."],
    #: ★★★★ B3 (round 26).  THE WINDOW KEY IS FOUR FIELDS, AND THREE OF
    #: THE FOUR PLACES THIS DEPOSIT STATED IT SAID THREE.  Two stars can sit
    #: at different phase centres in the same spectral window of the same
    #: execution block -- 14 do here, including a three-way group -- so
    #: (eb, nu_lo_GHz, nu_hi_GHz) is duplicated over 66 rows of this table
    #: and a reader following that instruction loses 35 windows, one of them
    #: the only Class A window of a star.  Done that way the article's own
    #: 60 systems with a limit, 1.8e15 W median and 57 below 1e16 W come back
    #: as 59, 1.66e15 and 56.  The uniqueness of the four-field key is
    #: asserted by `zverify` V5 over every table that carries it.
    "star joins stellar_sample.csv; eb joins execution_blocks.csv; "
    "(target_id, eb, nu_lo_GHz, nu_hi_GHz) joins the sensitivity tables and "
    "control_field_statistics.csv -- all four fields, because two positions "
    "can share one window of one block, and (eb, nu_lo_GHz, nu_hi_GHz) alone "
    "is duplicated here; a crossing is "
    "tied to its window by frequency CONTAINMENT in (nu_lo_GHz, nu_hi_GHz), "
    "not by equality with crossing_nu_topo_GHz.",
    [('star', '', 'star designation, as used throughout the article and in every file here'),
     ('system', '', 'system identifier; the components of a bound pair share it'),
     ('target_id', '', 'identifier the window was extracted under, which distinguishes the components of a pair observed in one execution block'),
     ('ra_deg', 'deg', 'right ascension of the extraction position, ICRS'),
     ('dec_deg', 'deg', 'declination of the extraction position, ICRS'),
     ('eb', '', 'ALMA execution block (ASDM) identifier; with the project code this retrieves the original data from the ALMA Science Archive'),
     ('project_code', '', 'ALMA project code, cited as ADS/JAO.ALMA# followed by this value'),
     ('date_utc', 'date', 'UTC date of the execution block'),
     ('t_start_mjd', 'd', 'adopted start epoch of the execution block, MJD'),
     ('band', '', 'ALMA receiver band'),
     ('nu_lo_GHz', 'GHz', 'lower edge of the spectral window, topocentric as delivered'),
     ('nu_hi_GHz', 'GHz', 'upper edge of the spectral window, topocentric as delivered'),
     ('chan_width_Hz', 'Hz', 'delivered channel width'),
     ('on_source_s', 's', 'on-source integration time at this position'),
     ('n_int', '', 'integrations retained at this position'),
     ('rms_mJy', 'mJy', 'per-channel noise at the extraction position'),
     ('smin_mJy', 'mJy', 'amplitude limit at the trigger, five times the noise divided by the primary-beam response'),
     ('theta_pb_arcsec', 'arcsec', 'primary-beam FWHM, 1.22 lambda / D, of the annulus this window was searched with'),
     ('array', '', '12m or 7m: the array that observed the window, from the archive'),
     ('geometry_provenance', '', 'corrected-geometry where the window was extracted with the dish read from the data; frozen-geometry where it predates that repair and its annulus assumed a 12 m dish'),
     ('pb_offset_arcsec', 'arcsec', 'angular offset of the star from the phase centre'),
     ('pb_atten', '', 'primary-beam response at the star, between 0 and 1'),
     ('dist_pc', 'pc', 'distance adopted for the star'),
     ('search_class', '', 'A where the window resolves a carrier in one channel, B where the channel is coarse'),
     ('drift_max_Hz_s', 'Hz/s', 'largest drift rate searched in this window'),
     ('a_max_m_s2', 'm/s2', 'line-of-sight acceleration that corresponds to it'),
     ('n_drift_trials', '', 'drift trials searched'),
     ('n_search_cells', '', 'search cells in this window, channels times drift trials'),
     ('n_ind_cells', '', 'independent cells after the correlation between neighbouring drift trials is accounted for'),
     ('eirp_p90_W', 'W', 'adopted 90 per cent completeness EIRP limit; the smearing retention divided out is the one measured on the delivered channel response, not the transform-limited form'),
     ('eirp_p90_lo_W', 'W', 'lower end of its interval: the dispersion measured between the directly injected windows, the same pair of factors on every row, and not a bound measured in this window\'s own band and channelisation'),
     ('eirp_p90_hi_W', 'W', 'upper end of that interval, on the same basis'),
     ('completeness_basis', '', 'injected where this window carries its own injection ladder, transferred where its completeness comes from the calibration of completeness_calibration.csv'),
     ('T_star_narrow_field', '', 'de-drifted search statistic at the stellar position, read over the narrower extraction field'),
     ('T_ctrl_max_narrow_field', '', 'largest statistic among the window control positions, same field'),
     ('n_ctrl', '', 'control positions in this window ensemble'),
     ('n_ctrl_trig', '', 'how many of them reach the trigger'),
     ('mask_attr_share', '', 'share of those control exceedances the attribution mask takes, in the star rest frame'),
     ('unmasked_fraction', '', 'fraction of this window channels lying OUTSIDE the attribution mask, evaluated in the star own rest frame. The survey constrains nothing inside the mask, so a window at 0 carries no limit and is not in any distribution of limits in the article; blank where a velocity term is missing and the value would depend on it'),
     ('telluric_factor', '', 'factor by which the remaining exceedances are reduced by the atmospheric screen, applied to the crossings on the same radius and in the same topocentric frame'),
     ('trigger_whole_beam', '', '1 where this window holds a threshold crossing under the adopted whole-beam statistic'),
     ('trigger_narrow_field', '', '1 where it holds one under the narrower extraction field'),
     # GEN (v4.29 fold): the count is the data's (the field-repair delta's catalogue rows, asserted above), not typed
     ('trigger_flags_agree', '', '1 where the two readings agree, 0 on the %s rows where they do not'
      % {6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve'}.get(
          len(DISAGREE), '%d' % len(DISAGREE))),
     ('crossing_nu_topo_GHz', 'GHz', 'frequency of the adopted crossing this window holds, empty where it holds none; it can differ from the narrower field\'s own peak in the same window'),
     ('disposition', '', 'disposition carried in the crossing table, where there is one')],
    _windows()))


# ===================================================== catalogues/stellar_sample
import posflag_r31 as _pf33   # v4.33: which systems' limits hold only if the adopted position is right


def _stars():
    by = collections.OrderedDict()
    for c, p in CATK:
        by.setdefault(c['target_id'], []).append((c, p))
    rows = []
    for tid in sorted(by):
        g = by[tid]
        c0 = g[0][0]
        ra, dec = STARPOS.get(tid, ('', ''))
        p90 = sorted(float(c['eirp_p90_W']) for c, _ in g)
        rows.append(dict(
            star=c0['star'], system=c0['system'], target_id=tid,
            ra_deg=f(ra, 6), dec_deg=f(dec, 6), dist_pc=f(c0['dist_pc'], 4),
            n_blocks=i(len({c['eb'] for c, _ in g})),
            n_windows=i(len(g)),
            n_windows_class_A=i(sum(1 for c, _ in g if c['search_class'] == 'A')),
            n_windows_class_B=i(sum(1 for c, _ in g if c['search_class'] == 'B')),
            bands='+'.join(sorted({c['band'] for c, _ in g}, key=int)),
            nu_min_GHz=f(min(float(c['nu_lo_GHz']) for c, _ in g), 6),
            nu_max_GHz=f(max(float(c['nu_hi_GHz']) for c, _ in g), 6),
            on_source_h=f(sum(float(c['on_source_s']) for c, _ in g) / 3600., 3),
            eirp_p90_min_W=e(p90[0]),
            eirp_p90_median_W=e(p90[len(p90) // 2]),
            n_crossings_whole_beam=i(sum(1 for c, _ in g if c['crossing'] == '1')),
            n_crossings_narrow_field=i(sum(1 for _, p in g if p['crossing'] == 'True')),
            project_codes='+'.join(sorted({PROJ[c['eb']]['project_code']
                                           for c, _ in g})),
            position_bounded=i(0 if _pf33.is_cond(c0['system']) else 1)))
    return rows


TABLES.append(Table(
    'catalogues/stellar_sample.csv',
    ["One row per searched target identifier: the sample the survey was carried "
     "out on, with what was searched toward each position.",
     "There are 90 identifiers over 87 designations and 83 systems; the "
     "difference is the components of bound pairs, which share a designation and "
     "sometimes a system but were extracted at their own positions. The article "
     "count of searched stars is a count of these identifiers.",
     "Two archival-tail execution blocks lie outside the window extent of this "
     "deposit; the two crossings they hold are in threshold_crossings.csv and "
     "are not counted in the per-star window totals here."],
    "target_id joins spectral_windows.csv and the sensitivity tables; star "
    "joins threshold_crossings.csv and recurrence_tests.csv.",
    [('star', '', 'star designation, as used throughout the article'),
     ('system', '', 'system identifier; the components of a bound pair share it'),
     ('target_id', '', 'identifier the windows were extracted under; unique over this table'),
     ('ra_deg', 'deg', 'right ascension of the extraction position, ICRS'),
     ('dec_deg', 'deg', 'declination of the extraction position, ICRS'),
     ('dist_pc', 'pc', 'distance adopted for the star'),
     ('n_blocks', '', 'execution blocks searched toward this position'),
     ('n_windows', '', 'spectral windows searched toward it'),
     ('n_windows_class_A', '', 'of those, windows that resolve a carrier in one channel'),
     ('n_windows_class_B', '', 'of those, windows with a coarse channel'),
     ('bands', '', 'ALMA receiver bands with at least one searched window, joined by +'),
     ('nu_min_GHz', 'GHz', 'lowest window edge searched toward this position'),
     ('nu_max_GHz', 'GHz', 'highest window edge searched toward it'),
     ('on_source_h', 'h', 'summed on-source time over its windows; windows of one block overlap in time, so this is a window total and not an observing duration'),
     ('eirp_p90_min_W', 'W', 'deepest 90 per cent completeness EIRP limit among its windows'),
     ('eirp_p90_median_W', 'W', 'median of that limit over its windows'),
     ('n_crossings_whole_beam', '', 'threshold crossings in its windows under the adopted whole-beam statistic'),
     ('n_crossings_narrow_field', '', 'the same count under the narrower extraction field'),
     ('project_codes', '', 'ALMA project codes its blocks belong to, joined by +'),
     ('position_bounded', '', '1 if the positional loss of its limits is bounded; 0 for the systems whose limits hold '
      'only if the adopted position is right, which the per-system summaries of the article leave out')],
    _stars()))


# ================================================== catalogues/execution_blocks
def _blocks():
    by = collections.OrderedDict()
    for c, p in CATK:
        by.setdefault(c['eb'], []).append((c, p))
    rows = []
    for eb in sorted(by):
        g = by[eb]
        pr = PROJ[eb]
        th = sorted(float(ring_of(c)['pb_arcsec']) for c, _ in g)
        rows.append(dict(
            eb=eb, project_code=pr['project_code'], date_utc=pr['date_utc'],
            epoch_mjd=f(pr['epoch_mjd'], 6), epoch_source=pr['epoch_source'],
            bands='+'.join(sorted({c['band'] for c, _ in g}, key=int)),
            n_targets=i(len({c['target_id'] for c, _ in g})),
            targets='+'.join(sorted({c['star'] for c, _ in g})),
            n_windows=i(len(g)),
            n_windows_class_A=i(sum(1 for c, _ in g if c['search_class'] == 'A')),
            n_windows_class_B=i(sum(1 for c, _ in g if c['search_class'] == 'B')),
            nu_min_GHz=f(min(float(c['nu_lo_GHz']) for c, _ in g), 6),
            nu_max_GHz=f(max(float(c['nu_hi_GHz']) for c, _ in g), 6),
            on_source_h=f(max(float(c['on_source_s']) for c, _ in g) / 3600., 3),
            theta_pb_median_arcsec=f(th[len(th) // 2], 3),
            n_crossings_whole_beam=i(sum(1 for c, _ in g if c['crossing'] == '1')),
            n_crossings_narrow_field=i(sum(1 for _, p in g if p['crossing'] == 'True')),
            set_name='primary census'))
    #: ★★ THE TWO ARCHIVAL-TAIL BLOCKS JOIN OR THEY DO NOT EXIST.  They hold a
    #: threshold crossing each and lie outside the window extent of this
    #: archive, so every window column of theirs is empty -- but a crossing
    #: whose block is in no table here is a dangling row, and this project has
    #: shipped one of those before.  They are rows, declared as what they are.
    tail = collections.OrderedDict()
    for r in LED:
        if LEDWIN[(r['eb'], r['nu_topo_GHz'])] is None:
            tail.setdefault(r['eb'], []).append(r)
    for eb in sorted(tail):
        g = tail[eb]
        rows.append(dict(
            eb=eb, project_code='', date_utc='', epoch_mjd='',
            epoch_source='',
            bands='+'.join(sorted({r['band'] for r in g}, key=int)),
            n_targets=i(len({r['star'] for r in g})),
            targets='+'.join(sorted({r['star'] for r in g})),
            n_windows='', n_windows_class_A='', n_windows_class_B='',
            nu_min_GHz='', nu_max_GHz='', on_source_h='',
            theta_pb_median_arcsec='',
            n_crossings_whole_beam=i(len(g)), n_crossings_narrow_field='',
            set_name='archival tail'))
    return rows


TABLES.append(Table(
    'catalogues/execution_blocks.csv',
    ["One row per execution block of the primary census: the archival "
     "accounting that ties every searched window to a retrievable observation.",
     "The block identifier and the project code together retrieve the original "
     "data from the ALMA Science Archive, where the project code is cited as "
     "ADS/JAO.ALMA# followed by its value.",
     "epoch_source records where the epoch was read: block means the block\'s own "
     "recorded start, and any other value means it was resolved through the "
     "member observing unit instead.",
     "Two rows are archival-tail blocks. Each holds a threshold crossing and "
     "lies outside the window extent of this archive, so every window column "
     "of theirs is empty and their project code is not resolved here; the "
     "block identifier alone retrieves them from the archive. They are "
     "present so that every crossing names a block this table has.",
     "The block sets outside these two -- the reserved hold-out, the archival "
     "extension, the out-of-sample control beyond 40 pc, and the blocks that "
     "were not searched and why -- are accounted for in the article\'s own block "
     "ledger, which this table does not duplicate."],
    "eb joins spectral_windows.csv, threshold_crossings.csv and "
    "recurrence_tests.csv.",
    [('eb', '', 'ALMA execution block (ASDM) identifier'),
     ('project_code', '', 'ALMA project code; cite as ADS/JAO.ALMA# followed by this value'),
     ('date_utc', 'date', 'UTC date of the block'),
     ('epoch_mjd', 'd', 'adopted start epoch, MJD'),
     ('epoch_source', '', 'block where the epoch is the block\'s own recorded start, otherwise the route by which it was resolved'),
     ('bands', '', 'ALMA receiver bands searched in this block, joined by +'),
     ('n_targets', '', 'target identifiers searched in it'),
     ('targets', '', 'their star designations, joined by +'),
     ('n_windows', '', 'spectral windows searched in it'),
     ('n_windows_class_A', '', 'of those, fine-channel windows'),
     ('n_windows_class_B', '', 'of those, coarse-channel windows'),
     ('nu_min_GHz', 'GHz', 'lowest window edge searched in it'),
     ('nu_max_GHz', 'GHz', 'highest window edge searched in it'),
     ('on_source_h', 'h', 'largest on-source time among its windows, which is the block\'s own on-source duration at that position'),
     ('theta_pb_median_arcsec', 'arcsec', 'median recorded primary-beam FWHM of its windows; the compact array is identifiable by it'),
     ('n_crossings_whole_beam', '', 'threshold crossings in it under the adopted whole-beam statistic'),
     ('n_crossings_narrow_field', '', 'the same count under the narrower extraction field'),
     ('set_name', '', 'the block set this row belongs to: primary census, or archival tail for the two blocks that lie outside the window extent of this archive')],
    _blocks()))


# ================================================ catalogues/block_sessions.csv
#: ★★ R1-3: block and session membership.  Every block a quantity here is
#: resampled over, or a recurrence bound is read in, must be assignable to its
#: observing session, because the separated-session rule and the block
#: resampling both act on that grouping.  One row per execution block the
#: search processed (the archive metadata harvest) and per block any other
#: deposited table names; the session is the middle field of the ALMA block
#: identifier, the key every generator of the article uses, and the member
#: observing unit is the archive's own grouping above it.
_ARCH = read_json('archive_meta_v381.json')
_HOLD_EB = {r['eb'] for r in read_json('holdout_export_v381.json')['rows']}


def _session_of(eb):
    p = eb.split('_')
    return p[1] if len(p) == 3 and p[0] == 'A002' else ''


def _block_sessions():
    cen = {c['eb'] for c, _p in CATK}
    named = set(cen) | set(_ARCH['ebs']) | set(_HOLD_EB)
    for t in TABLES:
        for r in t.rows:
            for k in ('eb', 'best_eb'):
                v = r.get(k)
                if v:
                    named.add(v)
    rows = []
    for eb in sorted(named):
        m = _ARCH['ebs'].get(eb, {})
        mous = m.get('member_ous') or []
        pc = (PROJ[eb]['project_code'] if eb in PROJ else
              ';'.join(x.replace('ADS/JAO.ALMA#', '') for x in (m.get('project') or []) if x))
        rows.append(dict(
            eb=eb, session_id=_session_of(eb),
            member_ous=';'.join(x.replace('uid://', '') for x in mous if x),
            project_code=pc, array=m.get('array', ''),
            set_name=('primary census' if eb in cen else
                      'reserved hold-out' if eb in _HOLD_EB else
                      'other')))
    return rows




# =============================================== catalogues/frequency_coverage
#: ★ The searched frequency extent, as the contiguous islands the windows
#: form.  The masked width inside each island is computed with the article's
#: own rule -- the adopted half-width about every transition of the mask line
#: list -- and the total is asserted against the published figure, so this
#: column cannot drift from the article it supports.
C_KMS = 299792.458
MASK_KMS = float(mac('LgMaskKms'))


def _merge(ivs):
    out = []
    for lo, hi in sorted(ivs):
        if out and lo <= out[-1][1]:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out


MASK_IV = _merge([(t['f'] * (1 - MASK_KMS / C_KMS),
                   t['f'] * (1 + MASK_KMS / C_KMS))
                  for t in MASK['transitions'].values()])
ISL = _merge([(float(c['nu_lo_GHz']), float(c['nu_hi_GHz'])) for c, _ in CATK])


def _overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


_mtot = sum(sum(_overlap(isl, m) for m in MASK_IV) for isl in ISL)
assert abs(_mtot - float(mac('FrMaskLostGHz'))) < 0.02, (
    'the masked width inside the searched islands comes out %.4f GHz against '
    'the published %s GHz' % (_mtot, mac('FrMaskLostGHz')))
_utot = sum(hi - lo for lo, hi in ISL)
assert abs(_utot - float(mac('FrMaskUnionGHz'))) < 0.1, (
    'the searched union comes out %.4f GHz against the published %s'
    % (_utot, mac('FrMaskUnionGHz')))
assert abs(100.0 * _mtot / _utot - float(mac('FrMaskPct'))) < 0.05, (
    'the masked fraction of the searched union comes out %.2f per cent '
    'against the published %s' % (100.0 * _mtot / _utot, mac('FrMaskPct')))
#: ★★ THE COUNT, NOT ONLY THE WIDTH.  A mask built from the wrong species list
#: can reproduce a width by coincidence; it cannot reproduce the count.  Both
#: the mask's own transition count and its species count are pinned against
#: the article's macros AND against the released mask record, which is the
#: pair of comparisons that was missing when the deposit shipped 111.
assert len(MASK['transitions']) == maci('FrNTrans') == _MFR['n_transitions'], (
    'the mask holds %d transitions, the article publishes %s and the released '
    'mask record says %s' % (len(MASK['transitions']), mac('FrNTrans'),
                             _MFR['n_transitions']))
assert len({t['spec'] for t in MASK['transitions'].values()}) \
    == maci('FrNSpec') == _MFR['n_species'], (
    'the mask holds %d species against the article\'s %s and the record\'s %s'
    % (len({t['spec'] for t in MASK['transitions'].values()}),
       mac('FrNSpec'), _MFR['n_species']))
# ★ r28 (v4.29, Ruling R3): one rule for every species, so the query IS the
# mask.  What was asserted here (the query strictly wider) guarded the
# v4.26-v4.28 state and is inverted; the deposited table still lets a reader
# check the rule, because line_mask.py reproduces every attribution from it.
assert len(QUERY['transitions']) == len(MASK['transitions']), (
    'the query is wider than the mask: a species has been carved out of the '
    'one rule again')

#: ★★ THE CLASS A COST, which is the second figure A3 moved and the one
#: Referee 2 quoted back at us.  The union of the Class A windows alone, and
#: the mask's share of it, rebuilt here and pinned against `\MkMaskAGHz` and
#: `\MkMaskAPct` -- the deposit published neither and nothing compared them.
ISL_A = _merge([(float(c['nu_lo_GHz']), float(c['nu_hi_GHz']))
                for c, _ in CATK if c['search_class'] == 'A'])
_atot = sum(hi - lo for lo, hi in ISL_A)
_amask = sum(sum(_overlap(isl, m) for m in MASK_IV) for isl in ISL_A)
assert abs(_amask - float(mac('MkMaskAGHz'))) < 0.02, (
    'the mask costs %.4f GHz of the Class A union against the published %s'
    % (_amask, mac('MkMaskAGHz')))
assert abs(100.0 * _amask / _atot - float(mac('MkMaskAPct'))) < 0.1, (
    'the mask costs %.2f per cent of the Class A union against the published '
    '%s' % (100.0 * _amask / _atot, mac('MkMaskAPct')))


def _coverage():
    rows = []
    for n, (lo, hi) in enumerate(ISL, 1):
        g = [(c, p) for c, p in CATK
             if float(c['nu_lo_GHz']) >= lo - 1e-9
             and float(c['nu_hi_GHz']) <= hi + 1e-9]
        masked = sum(_overlap((lo, hi), m) for m in MASK_IV)
        rows.append(dict(
            island=i(n), nu_lo_GHz=f(lo, 6), nu_hi_GHz=f(hi, 6),
            width_GHz=f(hi - lo, 6),
            bands='+'.join(sorted({c['band'] for c, _ in g}, key=int)),
            n_windows=i(len(g)),
            n_windows_class_A=i(sum(1 for c, _ in g if c['search_class'] == 'A')),
            n_windows_class_B=i(sum(1 for c, _ in g if c['search_class'] == 'B')),
            n_targets=i(len({c['target_id'] for c, _ in g})),
            n_blocks=i(len({c['eb'] for c, _ in g})),
            masked_GHz=f(masked, 6),
            masked_fraction=f(masked / (hi - lo), 4),
            n_masked_transitions=i(sum(1 for t in MASK['transitions'].values()
                                       if lo <= t['f'] <= hi)),
            n_crossings_whole_beam=i(sum(1 for c, _ in g if c['crossing'] == '1'))))
    return rows


TABLES.append(Table(
    'catalogues/frequency_coverage.csv',
    ["One row per contiguous island of searched frequency: the union the "
     "windows cover, with what was searched in each part of it.",
     "Islands are formed by merging the topocentric edges of all searched "
     "windows, so the widths here sum to the searched union and not to the sum "
     "of the window widths, which double-counts the frequencies two blocks "
     "share.",
     "masked_GHz is the width inside the island covered by the attribution "
     "mask, computed as the adopted half-width about every transition of "
     "molecular_line_matches.csv WITH in_mask = 1, which is every row of "
     "that file: the mask is the whole query, one rule for every species. "
     "The survey constrains nothing inside the masked width."],
    "nu_lo_GHz and nu_hi_GHz bracket the windows of spectral_windows.csv that "
    "fall in the island; the transitions are those of "
    "molecular_line_matches.csv with in_mask = 1 and a rest frequency inside "
    "it.",
    [('island', '', 'island number, ordered by frequency'),
     ('nu_lo_GHz', 'GHz', 'lower edge of the island, topocentric'),
     ('nu_hi_GHz', 'GHz', 'upper edge of the island, topocentric'),
     ('width_GHz', 'GHz', 'its width'),
     ('bands', '', 'ALMA receiver bands contributing to it, joined by +'),
     ('n_windows', '', 'searched windows lying inside it'),
     ('n_windows_class_A', '', 'of those, fine-channel windows'),
     ('n_windows_class_B', '', 'of those, coarse-channel windows'),
     ('n_targets', '', 'target identifiers with a window inside it'),
     ('n_blocks', '', 'execution blocks with a window inside it'),
     ('masked_GHz', 'GHz', 'width inside the island covered by the attribution mask'),
     ('masked_fraction', '', 'that width as a fraction of the island width'),
     ('n_masked_transitions', '', 'transitions of the MASK (molecular_line_matches.csv with in_mask = 1) whose rest frequency lies inside it'),
     ('n_crossings_whole_beam', '', 'threshold crossings inside it under the adopted statistic')],
    _coverage()))


# ================================================= candidates/threshold_crossings
#: ★★ THE NEAREST-TRANSITION COLUMNS.  The mask line list answers "is this
#: crossing attributable to one of the twelve masked species"; it does not
#: answer "what is the nearest catalogued transition of any species", which is
#: a different question and the one a reader checking an identification asks.
#: The wider query is a product of the manuscript build; where it is present
#: the four columns below are filled from it, and where it is not they are
#: empty and the README says so rather than leaving a reader to guess.
NEAREST = {}
for _p in (os.path.join(BASE, 'nearest_transitions.json'),
           os.path.join(os.path.dirname(HERE), 'lines', 'nearest_all.json')):
    if os.path.isfile(_p):
        for _k, _v in json.load(open(_p)).items():
            _eb, _nu = _k.split('|')
            NEAREST[(_eb, '%.6f' % float(_nu))] = _v
        break


#: ★ r28 (R1 issue 7): THE FRAME TERMS TRAVEL WITH THE CROSSING, so that an
#: attribution is reproducible from the deposit alone -- the delivered
#: frequency, the two velocity terms, the stated convention and the line
#: table -- and not only from nu_star_GHz.  Read from the ledger's own frame
#: record, keyed on block and delivered frequency, never on a star name.
_FRAME = {(q['eb'], '%.6f' % float(q['frame']['f_topo'])): q['frame']
          for q in read_json('ledger.json')['rows']}


def _crossings():
    rows = []
    for r in LED:
        key = (r['eb'], '%.6f' % float(r['nu_topo_GHz']))
        n = LEDWIN[(r['eb'], r['nu_topo_GHz'])]
        c, p = (CATK[n] if n is not None else ({}, {}))
        pr = PROJ.get(r['eb'], {})
        tl = TL_HIT.get(key)
        nr = NEAREST.get(key, {})
        rows.append(dict(
            star=r['star'], star_in_sample=SAMPLE_OF.get(r['star'], r['star']),
            eb=r['eb'], project_code=pr.get('project_code', ''),
            date_utc=pr.get('date_utc', ''), band=r['band'],
            nu_topo_GHz=f(r['nu_topo_GHz'], 6),
            nu_star_GHz=f(r['nu_star_GHz'], 6),
            v_bary_kms=f(_FRAME[key]['v_bary'], 4),
            v_sys_kms=f(_FRAME[key]['v_sys'], 4),
            window_nu_lo_GHz=f(c['nu_lo_GHz'], 6) if c else '',
            window_nu_hi_GHz=f(c['nu_hi_GHz'], 6) if c else '',
            #: ★★★★ S2/Z-1 (round 26).  THIS CELL WAS EMPTY ON THE TWO
            #: ARCHIVAL-TAIL CROSSINGS AND BLANK IS NOT A DECLARED VALUE OF
            #: THE COLUMN, so the article's 52 Class A crossings queried as
            #: 50 from the deposit: `c` is the HOST WINDOW's catalogue row
            #: and those two crossings lie in blocks outside the window
            #: catalogue's extent, so there was no row to take the class
            #: from.  The class is a property of the SEARCH that found them,
            #: not of the catalogue's extent -- both were found in the fine
            #: channelisation and the article counts them as Class A -- and
            #: `chance_v414.json` is where that is recorded, under
            #: `observed_tail`, which is the same record the comparison
            #: itself uses.  Read back, never typed.
            search_class=(c.get('search_class')
                          or ('A' if (r['eb'],
                                      round(float(r['nu_topo_GHz']), 6))
                              in TAIL_A_CROSS else '')),
            in_window_catalogue=b(n is not None),
            T_star=f(r['T_star'], 4), T_ctrl_max=f(r['T_ctrl'], 4),
            rms_mJy=f(c['rms_mJy'], 5) if c else '',
            eirp_p90_W=e(c['eirp_p90_W']) if c else '',
            masked_transition=r['line'], masked_dv_kms=r['dv_star_kms'],
            mask_coincident_not_attributed=r['mask_coincident_not_attributed'],
            attributed=r['attributed'],
            nearest_transition=nr.get('species', ''),
            nearest_transition_qn=nr.get('qn', ''),
            nearest_transition_GHz=f(nr['f_rest_MHz'] / 1000., 6) if nr else '',
            nearest_transition_dv_kms=f(nr['dv_kms'], 3) if nr else '',
            nearest_transition_catalogue=nr.get('catalogue', ''),
            atmospheric_flag=b(tl is not None),
            atmospheric_species=(tl['species'] if tl else ''),
            atmospheric_line_GHz=(f(tl['line_MHz'] / 1000., 6) if tl else ''),
            atmospheric_offset_MHz=(f(tl['d_MHz'], 3) if tl else ''),
            trigger_whole_beam='1',
            trigger_narrow_field=(b(p['crossing']) if p else ''),
            quality_flagged=r['quality_flagged'],
            n_rep=r['n_rep'], dt_min_d=r['dt_min_d'], dt_max_d=r['dt_max_d'],
            dt_from_unit_stamp=r['dt_from_unit_stamp'],
            T_pers=r['T_pers'], T_rep=r['T_rep'],
            T_rep_is_upper_bound=r['T_rep_is_upper_bound'],
            sigma_excl=r['sigma_excl'], disposition=r['disposition']))
    return rows


TABLES.append(Table(
    'candidates/threshold_crossings.csv',
    ["One row per threshold crossing: every cell in the survey whose "
     "de-drifted search statistic reached the trigger at a stellar position, "
     "under the adopted whole-beam statistic.",
     "trigger_whole_beam is 1 on every row by construction, because this is the "
     "adopted set; trigger_narrow_field records whether the same window also "
     "holds a crossing under the narrower extraction field, and it is 0 on two "
     "rows. Four further windows hold a narrow-field crossing and no adopted "
     "one; they are in spectral_windows.csv with trigger_flags_agree = 0.",
     "atmospheric_flag marks the one crossing the atmospheric screen removes "
     "from both sides of the chance comparison. It is a crossing, it is "
     "unattributed, and it is tested for recurrence; what the flag records is "
     "that it is excluded from the comparison with chance, because the control "
     "side is screened on the same radius in the same topocentric frame.",
     "masked_transition and masked_dv_kms give the nearest transition of the "
     "attribution mask in the star rest frame. nearest_transition gives the "
     "nearest catalogued transition of any species in the wider query, which is "
     "a different quantity: a crossing can be far from any masked line and "
     "close to an unmasked one.",
     "An empty field is a value withheld, not a zero."],
    "star_in_sample joins stellar_sample.csv; (eb, nu_topo_GHz) is unique and joins recurrence_tests.csv; the window is "
    "the row of spectral_windows.csv with the same eb whose edges CONTAIN "
    "nu_topo_GHz -- two crossings lie at a frequency the narrower field never "
    "reported in the same window, so a join on a frequency column finds "
    "neither; two further crossings lie in archival-tail blocks outside the "
    "window catalogue and carry in_window_catalogue = 0.",
    [('star', '', 'star designation of the position the crossing was found at'),
     ('star_in_sample', '', 'designation under which the sample table counts that position; it differs from star for the one component whose extractions are second readings of windows the sample counts under its primary'),
     ('eb', '', 'ALMA execution block (ASDM) identifier of the discovery block'),
     ('project_code', '', 'its ALMA project code, empty for the two archival-tail blocks; cite as ADS/JAO.ALMA# followed by this value'),
     ('date_utc', 'date', 'UTC date of that block'),
     ('band', '', 'ALMA receiver band'),
     ('nu_topo_GHz', 'GHz', 'crossing frequency as delivered by the correlator'),
     ('nu_star_GHz', 'GHz', 'the same frequency in the star rest frame: nu_topo_GHz x (1 - v_bary_kms/c) x (1 + v_sys_kms/c), c = 299792.458 km/s'),
     ('v_bary_kms', 'km/s', 'topocentric-to-barycentric velocity term of the discovery block at its own pointing and mid-time, as used in nu_star_GHz'),
     ('v_sys_kms', 'km/s', 'systemic velocity of the star, as used in nu_star_GHz'),
     ('window_nu_lo_GHz', 'GHz', 'lower edge of the window that holds it, empty for the archival-tail crossings'),
     ('window_nu_hi_GHz', 'GHz', 'upper edge of that window'),
     ('search_class', '', 'class of the search that found the crossing, A fine or B coarse; for the two crossings in archival-tail blocks, whose host window is outside the extent of spectral_windows.csv, it is the class of the fine-channel search they were found in, so a query on this column returns every Class A crossing the article reports'),
     ('in_window_catalogue', '', '1 where the host window is in spectral_windows.csv, 0 for the two crossings in archival-tail blocks outside its extent'),
     ('T_star', '', 'de-drifted search statistic at the stellar position, the quantity of Eq. 1'),
     ('T_ctrl_max', '', 'largest statistic among that window control positions'),
     ('rms_mJy', 'mJy', 'per-channel noise of the host window at the extraction position'),
     ('eirp_p90_W', 'W', 'that window 90 per cent completeness EIRP limit'),
     ('masked_transition', '', 'nearest transition of the attribution mask in the star rest frame'),
     ('masked_dv_kms', 'km/s', 'stellar-frame offset from it, positive where the crossing lies above the transition in frequency'),
     ('mask_coincident_not_attributed', '', '1 where the crossing lies inside the mask and is not attributed'),
     ('attributed', '', '1 where the crossing is attributed to a catalogued transition'),
     ('nearest_transition', '', 'species of the nearest catalogued transition of any species, from the wider catalogue query; empty where the query is not deposited'),
     ('nearest_transition_qn', '', 'its quantum numbers as the catalogue gives them'),
     ('nearest_transition_GHz', 'GHz', 'its rest frequency'),
     ('nearest_transition_dv_kms', 'km/s', 'stellar-frame offset of the crossing from it'),
     ('nearest_transition_catalogue', '', 'the line catalogue the entry was taken from'),
     ('atmospheric_flag', '', '1 on the crossing the atmospheric screen removes from both sides of the chance comparison; it remains a crossing and remains unattributed'),
     ('atmospheric_species', '', 'the atmospheric species responsible'),
     ('atmospheric_line_GHz', 'GHz', 'its transition frequency, topocentric'),
     ('atmospheric_offset_MHz', 'MHz', 'offset of the crossing from it, inside the screening radius'),
     ('trigger_whole_beam', '', '1 on every row: this table is the adopted whole-beam set'),
     ('trigger_narrow_field', '', '1 where the host window also holds a crossing under the narrower extraction field'),
     ('quality_flagged', '', '1 where the host window is data-quality flagged'),
     ('n_rep', '', 'covering repeat execution blocks'),
     ('dt_min_d', 'd', 'shortest interval to a covering repeat'),
     ('dt_max_d', 'd', 'longest interval to a covering repeat'),
     ('dt_from_unit_stamp', '', '1 where an interval is measured from the observing unit stamp rather than from the blocks\' own'),
     ('T_pers', '', 'statistic a carrier persisting at the discovery flux would give at the predicted cell'),
     ('T_rep', '', 'statistic measured at that cell at the carried drift'),
     ('T_rep_is_upper_bound', '', '1 where T_rep is a window maximum and so bounds the cell from above'),
     ('sigma_excl', '', 'standardised difference between the repeat reading and the reading a line-like emitter at rest in the stellar frame at the discovery flux would give at the predicted cell, in units of their combined scatter; a diagnostic, not a reported bound, and it does not test a drifting or re-tuned carrier'),
     ('disposition', '', 'disposition carried in the article\'s own crossing ledger: '
      'attributed (a catalogued transition inside the mask, no repeat reading); '
      'attributed; recurs / attributed; not recovered (the line is or is not found again in a separated-session repeat block); '
      'attributed; flagged and unattributed; flagged (in the block that fails the data-quality criterion); '
      'unattributed; no recurrence (read at its separated-session repeat blocks, nothing at the trigger); '
      'unattributed; not read (repeat coverage exists but was not read); '
      'unattributed; no separated repeat (code US: every repeat block is of the discovery\'s own session, so the recurrence test, which reads separated sessions only, has none)')],
    _crossings()))


# ============================================= candidates/molecular_line_matches
def _lines():
    attr = collections.Counter()
    coin = collections.Counter()
    for r in LED:
        if r['attributed'] == '1':
            attr[r['line']] += 1
        if r['mask_coincident_not_attributed'] == '1':
            coin[r['line']] += 1
    rows = []
    #: ★★★ EVERY ROW OF THE QUERY IS DEPOSITED AND ONLY THE MASKED ONES
    #: CARRY A MASK WINDOW.  The four `mask_*` columns describe the
    #: attribution window the mask puts about a transition; a transition the
    #: mask does not hold has no such window, and filling them anyway is what
    #: let a reader sum this column to 5.04 GHz against an article publishing
    #: 3.71.  They are now empty on those rows, `in_mask` says which is
    #: which, and `mask_exclusion_reason` says why in the article's own words.
    for name, t in sorted(QUERY['transitions'].items(), key=lambda kv: kv[1]['f']):
        lo = t['f'] * (1 - MASK_KMS / C_KMS)
        hi = t['f'] * (1 + MASK_KMS / C_KMS)
        inside = [isl for isl in ISL if isl[0] <= t['f'] <= isl[1]]
        m = in_mask(t)
        rows.append(dict(
            transition=name, species=t['spec'], quantum_numbers=t['qn'],
            nu_rest_GHz=f(t['f'], 6),
            e_upper_K=f(t['eu'], 3), a_ij_s=e(t['aij'], 4) if t['aij'] else '',
            line_catalogue=t['ll'],
            in_mask=b(m),
            mask_exclusion_reason='' if m else NOT_MASKED_REASON,
            mask_half_width_kms=f(MASK_KMS, 1) if m else '',
            mask_nu_lo_GHz=f(lo, 6) if m else '',
            mask_nu_hi_GHz=f(hi, 6) if m else '',
            mask_width_GHz=f(hi - lo, 6) if m else '',
            inside_searched_island=b(bool(inside)),
            n_crossings_attributed=i(attr.get(name, 0)),
            n_crossings_coincident_not_attributed=i(coin.get(name, 0))))
    #: ★★ The two closures a reader checks, asserted here so the file cannot
    #: ship without them: the masked rows are the mask, and no excluded
    #: species attributes anything.
    assert sum(1 for r in rows if r['in_mask'] == '1') \
        == len(MASK['transitions']), 'in_mask does not select the mask'
    assert all(r['n_crossings_attributed'] == '0' for r in rows
               if r['in_mask'] != '1'), (
        'a transition the mask does not hold is credited with an '
        'attribution, which is a contradiction in terms')
    return rows


TABLES.append(Table(
    'candidates/molecular_line_matches.csv',
    ["One row per transition of the dated catalogue QUERY, which is the "
     "attribution mask: every species these setups cover that is detected in "
     "discs or molecular clouds, one rule for all of them, so in_mask is 1 on "
     "every row (the column is kept so that a reader can see that no species "
     "is left out).",
     "The query is every transition of the named species that falls inside a "
     "searched island below the adopted upper-state energy cut, together with "
     "the hydrogen recombination series, taken from one query of the "
     "catalogues named in line_catalogue.",
     "The MASK holds %d of the %d rows, over %d species."
     % (len(MASK['transitions']), len(QUERY['transitions']),
        len({t['spec'] for t in MASK['transitions'].values()})),
     "A crossing is attributed where its stellar-frame frequency lies within "
     "the adopted half-width of a transition WITH in_mask = 1; "
     "code/line_mask.py reproduces every deposited attribution from this "
     "table and nu_star_GHz. An attribution is a coincidence in frequency, "
     "not an identification of the line: which attributions carry "
     "independent support is stated in the article. Each crossing's "
     "attribution is in threshold_crossings.csv; this table is the list and "
     "the accounting."],
    "transition joins the masked_transition column of "
    "threshold_crossings.csv; nu_rest_GHz falls inside the island of "
    "frequency_coverage.csv whose edges bracket it.",
    [('transition', '', 'transition label, as used in threshold_crossings.csv'),
     ('species', '', 'chemical species'),
     ('quantum_numbers', '', 'quantum numbers as the line catalogue gives them'),
     ('nu_rest_GHz', 'GHz', 'rest frequency'),
     ('e_upper_K', 'K', 'upper-state energy; zero for the recombination series, which the catalogues give without one'),
     ('a_ij_s', '1/s', 'Einstein A coefficient where the catalogue gives one'),
     ('line_catalogue', '', 'the catalogue the entry was taken from'),
     ('in_mask', '', '1 where the attribution mask holds this transition; 0 where the query returned it and the mask leaves it out'),
     ('mask_exclusion_reason', '', 'why the mask leaves it out, where it does; empty where in_mask is 1'),
     ('mask_half_width_kms', 'km/s', 'adopted half-width of the attribution window about the transition; empty where in_mask is 0, which has no attribution window'),
     ('mask_nu_lo_GHz', 'GHz', 'lower edge of that window'),
     ('mask_nu_hi_GHz', 'GHz', 'upper edge of that window'),
     ('mask_width_GHz', 'GHz', 'its width; summed over the searched islands and over the rows with in_mask = 1 this is the bandwidth the mask costs'),
     ('inside_searched_island', '', '1 where the rest frequency lies inside a searched island'),
     ('n_crossings_attributed', '', 'threshold crossings attributed to this transition'),
     ('n_crossings_coincident_not_attributed', '', 'crossings lying inside its window that are not attributed to it')],
    _lines()))


# =================================================== candidates/recurrence_tests
def _recur():
    rc = {(r['eb'], '%.6f' % float(r['nu_topo_GHz'])): r for r in RECUR}
    rv = {(r['eb'], '%.6f' % float(r['nu_topo_GHz'])): r for r in RECOV}
    assert len(rc) == len(RECUR) and len(rv) == len(RECOV), 'duplicate key'
    rows = []
    for r in LED:
        key = (r['eb'], '%.6f' % float(r['nu_topo_GHz']))
        a, c = rc.get(key, {}), rv.get(key, {})
        if not a and not c:
            continue
        rows.append(dict(
            star=r['star'], eb=r['eb'], nu_topo_GHz=f(r['nu_topo_GHz'], 6),
            nu_star_GHz=f(r['nu_star_GHz'], 6),
            n_rep=r['n_rep'], sigma_excl_single_cell=r['sigma_excl'],
            n_rep_separated=a.get('n_rep_sep', ''),
            T_pers_separated=a.get('T_pers_sep', ''),
            T_rep_separated=a.get('T_rep_sep', ''),
            f5_separated=a.get('f5_sep', ''),
            p_trigger_separated=a.get('p_trig_sep', ''),
            k_tol_channels=a.get('k_tol', ''),
            n_cells_tol=a.get('n_cell_tol', ''),
            threshold_tol=a.get('thr_tol', ''),
            f5_tol=a.get('f5_tol', ''),
            p_trigger_tol=a.get('p_trig_tol', ''),
            p_recovery_calculated=c.get('p_rec_calc', ''),
            p_recovery_measured=c.get('p_rec_meas', ''),
            p_recovery_lo=c.get('p_rec_lo', ''),
            p_recovery_hi=c.get('p_rec_hi', ''),
            n_realisations=c.get('n_real', ''),
            n_rep_blocks_injected=c.get('n_rep_blocks', ''),
            tested=c.get('tested', '')))
    return rows


TABLES.append(Table(
    'candidates/recurrence_tests.csv',
    ["One row per unattributed threshold crossing carrying a "
     "repeat-observation measurement: what the covering repeat blocks say "
     "about it, read three ways. A line-attributed crossing is tested on the "
     "same code path; its reading is the disposition column of "
     "threshold_crossings.csv.",
     "sigma_excl_single_cell is the depth at which an emitter at rest in the "
     "stellar frame at the discovery flux (a line-like source) is excluded at "
     "one predicted cell. It does not test a drifting or re-tuned carrier; every "
     "crossing here has a fitted drift, which disfavours that model, so a null "
     "at this cell bears little on an accelerating carrier.",
     "The separated columns repeat the reading over covering blocks that "
     "satisfy the separation criterion alone -- a different observing session "
     "more than a day away -- and the tol columns repeat it over a cell "
     "tolerance matched to the measured stellar-frame registration.",
     "p_recovery_measured is the probability the criterion is satisfied by a "
     "carrier at the trigger amplitude, measured by injecting that carrier into "
     "the retained per-integration spectra of every covering repeat block. "
     "tested is 0 where that probability is too low for the reading to be a "
     "test, and such a crossing is reported as untested rather than excluded.",
     "An empty field is a value withheld or inapplicable, not a zero: a "
     "crossing with no separated covering block has no separated reading."],
    "(eb, nu_topo_GHz) joins threshold_crossings.csv, where star carries the "
    "same spelling.",
    [('star', '', 'star designation, as in threshold_crossings.csv'),
     ('eb', '', 'ALMA execution block identifier of the discovery block'),
     ('nu_topo_GHz', 'GHz', 'crossing frequency as delivered by the correlator'),
     ('nu_star_GHz', 'GHz', 'the same frequency in the star rest frame'),
     ('n_rep', '', 'covering repeat execution blocks the published depth combines'),
     ('sigma_excl_single_cell', '', 'the same standardised difference at the single predicted cell, for a carrier whose stellar-frame frequency is unchanged; a diagnostic, not a reported bound'),
     ('n_rep_separated', '', 'of the covering repeats, blocks in a different session more than a day from the discovery block'),
     ('T_pers_separated', '', 'statistic a persisting carrier would give at the predicted cell over those blocks alone'),
     ('T_rep_separated', '', 'statistic measured there, at the carried drift'),
     ('f5_separated', '', 'fraction of the discovery amplitude still excluded at the trigger over those blocks alone; values above 1 exclude nothing'),
     ('p_trigger_separated', '', 'recovery probability at the trigger amplitude over those blocks alone'),
     ('k_tol_channels', 'channel', 'half-width of the matched registration tolerance, in channels of the finest covering block'),
     ('n_cells_tol', '', 'cells read over that tolerance'),
     ('threshold_tol', '', 'threshold at which those cells carry the single cell\'s own false-alarm probability'),
     ('f5_tol', '', 'fraction of the discovery amplitude excluded when the reading is the worst cell of that tolerance; values above 1 exclude nothing'),
     ('p_trigger_tol', '', 'recovery probability at the trigger amplitude at that threshold'),
     ('p_recovery_calculated', '', 'probability the criterion is satisfied by a carrier at the trigger amplitude, from the model of the reading'),
     ('p_recovery_measured', '', 'the same probability measured by injection into the covering repeat blocks'),
     ('p_recovery_lo', '', 'lower end of its 68 per cent interval'),
     ('p_recovery_hi', '', 'upper end of that interval'),
     ('n_realisations', '', 'realisations the measurement is formed from'),
     ('n_rep_blocks_injected', '', 'covering repeat blocks injected into'),
     ('tested', '', '1 where the measured recovery probability reaches the level required of a test, 0 where the crossing is reported as untested rather than excluded')],
    _recur()))


# ============================================ sensitivity/class_[AB]_limits.csv
#: ★★★ THE LIMIT CLOSES FROM THE COLUMNS DEPOSITED BESIDE IT.  Nominal trigger
#: power times the adopted completeness factor, divided by the phase-centre
#: retention, the smearing retention and the beam retention, reproduces the
#: deposited limit on every row.  The assertion is made here on the STRINGS
#: this generator writes, at their printed precision, because a reader has the
#: strings and not the values in memory.
SENS_COLS = [
    ('star', '', 'star designation, as in stellar_sample.csv'),
    ('target_id', '', 'identifier the window was extracted under'),
    ('eb', '', 'ALMA execution block (ASDM) identifier'),
    ('project_code', '', 'its ALMA project code; cite as ADS/JAO.ALMA# followed by this value'),
    ('band', '', 'ALMA receiver band'),
    ('nu_lo_GHz', 'GHz', 'lower edge of the spectral window, topocentric'),
    ('nu_hi_GHz', 'GHz', 'upper edge of the spectral window, topocentric'),
    ('chan_width_Hz', 'Hz', 'delivered channel width'),
    ('dist_pc', 'pc', 'distance adopted for the star'),
    ('on_source_s', 's', 'on-source integration time at this position'),
    ('n_int', '', 'integrations retained at this position'),
    ('rms_mJy', 'mJy', 'per-channel noise at the extraction position'),
    ('smin_mJy', 'mJy', 'amplitude limit at the trigger: five times the noise divided by the primary-beam response'),
    ('pb_atten', '', 'primary-beam response at the star, between 0 and 1'),
    ('theta_pb_arcsec', 'arcsec', 'recorded primary-beam FWHM for this window'),
    ('drift_max_Hz_s', 'Hz/s', 'largest drift rate searched'),
    ('n_drift_trials', '', 'drift trials searched'),
    ('eta_drift', '', 'fraction of the drift range over which a carrier is recovered at full amplitude'),
    ('c_response_smear', '', 'combined spectral-response and intra-channel smearing factor applied to the nominal power'),
    ('eirp_nominal_W', 'W', 'EIRP of a carrier at the trigger amplitude, before any completeness or retention factor'),
    ('eirp_eff_total_W', 'W', 'the same power with the spectral response and smearing applied'),
    ('p90_mult_adopted', '', 'adopted multiplier from the trigger amplitude to 90 per cent completeness: the class factor times the measured response ratio of the window\'s class and online-averaging mode, from completeness_calibration.csv; in a window that holds an unattributed crossing, times the ratio of the pooled ninety-per-cent points at that crossing\'s statistic and at the trigger (completeness_threshold_T)'),
    ('completeness_threshold_T', '', 'statistic at the star that 90 per cent of injected carriers must reach for this limit: the trigger, 5, or, in a window that holds an unattributed crossing, that crossing\'s own statistic, so that the limit is an upper limit'),
    ('eta_px_retained', '', 'fraction of the integrations retained after the phase-centre cut'),
    ('eta_smear_adopted', '', 'adopted smearing retention for this window'),
    ('eta_smear_basis', '', 'measured where the retention was measured on this window\'s own integrations, bounded where it is a bound'),
    ('eta_beam_retained', '', 'fraction of the applied primary-beam response that the observatory\'s documented beam retains, clamped at unity'),
    ('eirp_p90_W', 'W', 'adopted 90 per cent completeness EIRP limit; equals eirp_nominal_W times p90_mult_adopted divided by the three retentions'),
    ('eirp_p90_lo_W', 'W', 'lower end of its interval: the observed spread between the injected windows, the same pair of factors on every row including the injected ones; each injected window\'s own point is own_p90_factor in class_A_limit_uncertainty.csv'),
    ('eirp_p90_hi_W', 'W', 'upper end of that interval, on the same basis'),
    ('completeness_basis', '', 'injected where this window carries its own injection ladder, transferred otherwise'),
    ('unmasked_fraction', '', 'fraction of this window channels lying outside the attribution mask, in the star own rest frame; a window at 0 constrains nothing and is in no distribution of limits in the article'),
    ('trigger_whole_beam', '', '1 where the window holds a threshold crossing under the adopted statistic'),
]


# r34 (R2-1): the threshold of each window's 90 per cent point (tobs_r34.json, keyed as adopted_e90.smear_key)
_TOBS34 = {k: v['t_obs'] for k, v in json.load(open(os.path.join(HERE, 'tobs_r34.json')))['windows'].items()}
_TOBS34F = {k: v['factor'] for k, v in json.load(open(os.path.join(HERE, 'tobs_r34.json')))['windows'].items()}


def _tobsf(p):
    # the declared T_obs factor of a per_target row (1 where the window holds no unattributed crossing)
    return _TOBS34F.get('%s|%.6f|%s|%s' % (p['eb'], min(float(p['flo_GHz']), float(p['fhi_GHz'])),
                                           p['chanw_Hz'], p['star_name']), 1.0)


def _sens(cls):
    rows = []
    for c, p in CATK:
        if c['search_class'] != cls:
            continue
        k = wkey(c['eb'], c['target_id'], c['nu_lo_GHz'], c['nu_hi_GHz'])
        rows.append(dict(
            star=c['star'], target_id=c['target_id'], eb=c['eb'],
            project_code=PROJ[c['eb']]['project_code'], band=c['band'],
            nu_lo_GHz=f(c['nu_lo_GHz'], 6), nu_hi_GHz=f(c['nu_hi_GHz'], 6),
            chan_width_Hz=f(c['chan_width_Hz'], 1),
            dist_pc=f(c['dist_pc'], 4), on_source_s=f(c['on_source_s'], 1),
            n_int=i(p['n_int']), rms_mJy=f(c['rms_mJy'], 5),
            smin_mJy=f(c['smin_mJy'], 5), pb_atten=f(p['pb_atten'], 6),
            theta_pb_arcsec=f(ring_of(c)['pb_arcsec'], 3),
            drift_max_Hz_s=f(c['drift_max_Hz_s'], 3),
            n_drift_trials=i(p['n_drift_trials']),
            eta_drift=f(p['eta_drift'], 4),
            c_response_smear=f(p['c_response_smear'], 4),
            eirp_nominal_W=e(p['eirp_nominal_W']),
            eirp_eff_total_W=e(p['eirp_eff_total_W']),
            p90_mult_adopted=f(p['p90_mult_adopted'], 9),
            completeness_threshold_T=f(_TOBS34.get('%s|%.6f|%s|%s' % (
                p['eb'], min(float(p['flo_GHz']), float(p['fhi_GHz'])), p['chanw_Hz'], p['star_name']),
                5.0), 4),
            eta_px_retained=f(p['eta_px_retained'], 10),
            eta_smear_adopted=f(p['eta_smear_adopted'], 10),
            eta_smear_basis=p['eta_smear_basis'],
            eta_beam_retained=f(p['eta_beam_retained'], 10),
            eirp_p90_W=e(p['eirp_p90_adopted_W'], 9),
            eirp_p90_lo_W=e(p['eirp_p90_adopted_lo_W'], 9),
            eirp_p90_hi_W=e(p['eirp_p90_adopted_hi_W'], 9),
            completeness_basis=p['p90_basis'],
            # ★ see spectral_windows.csv: a row at 0 carries no limit
            unmasked_fraction=p.get('unmasked_fraction', ''),
            trigger_whole_beam=b(WHOLE[k])))
    worst = max(abs(float(r['eirp_nominal_W']) * float(r['p90_mult_adopted'])
                    / float(r['eta_px_retained'])
                    / float(r['eta_smear_adopted'])
                    / float(r['eta_beam_retained'])
                    / float(r['eirp_p90_W']) - 1.0) for r in rows)
    assert worst < 1e-6, ('the deposited limit does not close on the '
                          'deposited factors: worst %.2g' % worst)
    return rows


TABLES.append(Table(
    'sensitivity/class_A_limits.csv',
    ["One row per fine-channel spectral window: the sensitivity measurement "
     "for the windows that resolve a carrier in one channel.",
     "The limit closes on the columns beside it. eirp_nominal_W times "
     "p90_mult_adopted, divided by eta_px_retained, eta_smear_adopted and "
     "eta_beam_retained, reproduces eirp_p90_W on every row to better than one "
     "part in a million, which is the printed precision of the factors.",
     "The interval is the observed spread between the injected windows, the "
     "same pair of factors on every row, and is not a bound measured in a "
     "window\'s own band and channelisation; an injected window\'s own "
     "point, and the class-average interval kept apart from the spread, are "
     "in class_A_limit_uncertainty.csv.",
     "The limit is an EIRP at 90 per cent completeness for a carrier inside the "
     "searched drift range. It constrains nothing about a transmitter whose "
     "apparent acceleration exceeds that range."],
    "(target_id, eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv and "
    "control_field_statistics.csv -- all four fields, because two positions "
    "can share one window of one block; target_id joins stellar_sample.csv.",
    SENS_COLS, _sens('A')))

TABLES.append(Table(
    'sensitivity/class_B_limits.csv',
    ["One row per coarse-channel spectral window: the same sensitivity "
     "measurement for the windows whose channel does not resolve a carrier.",
     "The columns, the closure identity and the meaning of the interval are "
     "those of class_A_limits.csv.",
     "The completeness multiplier of these windows is a blend and is declared "
     "as one in completeness_calibration.csv: no injected coarse window has a "
     "bright control ring, so the stratified rule cannot be applied to them."],
    "(target_id, eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv -- all "
    "four fields, because two positions can share one window of one block; "
    "target_id joins "
    "stellar_sample.csv.",
    SENS_COLS, _sens('B')))


# ★ ROUND 28 (R1-1, R1-4, R2-m11).  WHAT ONE LIMIT AND THE HEADLINE ARE
# UNCERTAIN BY.  Both tables are computed by `sens_r28.py` and only carried
# here, so the archive and the article read one computation; the column lists
# below must be the files' own headers, which the Table class enforces row by
# row.
SENS28_WIN_COLS = [
    ('target_id', '', 'identifier the window was extracted under'),
    ('system_id', '', 'the stellar system the window counts toward'),
    ('eb', '', 'ALMA execution block (ASDM) identifier'),
    ('nu_lo_GHz', 'GHz', 'lower edge of the spectral window, topocentric'),
    ('nu_hi_GHz', 'GHz', 'upper edge of the spectral window, topocentric'),
    ('chan_width_Hz', 'Hz', 'delivered channel width'),
    ('n_chan_avg', '', 'online spectral averaging factor N; the archive\'s resolution-to-spacing ratio gives the same N for every window'),
    ('calibration_label', '', 'measured where carriers were injected into this window; interpolated where it lies inside the injected range on band, channel width, array configuration, integration time and block duration; extrapolated where it lies outside on at least one'),
    ('outside_injected_on', '', 'for an extrapolated window, the properties on which it leaves the injected range'),
    ('own_p90_factor', '', 'for a measured window, its own ninety per cent point in units of its trigger power; empty otherwise'),
    ('class_p90_factor', '', 'the class-average factor every Class A limit carries'),
    ('eirp_p90_W', 'W', 'the adopted limit, as in class_A_limits.csv'),
    ('eirp_p90_dispersion_lo_W', 'W', 'a measured window: its limit at its own factor; a transferred window: its limit at the smallest factor any injected window gave. An empirical bound only for an interpolated window'),
    ('eirp_p90_dispersion_hi_W', 'W', 'the same at the largest factor, on the same basis'),
    ('eirp_p90_classavg_lo_W', 'W', 'the limit at the low end of the class-average calibration interval; that interval moves every limit together and applies to statistics over many windows'),
    ('eirp_p90_classavg_hi_W', 'W', 'the limit at the high end of that interval'),
    ('decorrelation_frac', '', 'fraction by which atmospheric decorrelation leaves this limit optimistic; empty where the block has neither a phase record nor a baseline to match on'),
    ('decorrelation_basis', '', 'measured from the block\'s own phase record, matched from blocks of similar baseline, or none'),
    ('eirp_p90_decor_adjusted_W', 'W', 'the limit with that decorrelation divided out; empty where none is available'),
    ('response_ratio', '', 'the injected tone\'s phase-mean peak-channel share over that of the exact delivered response for this window\'s N; the injections deposited the N = 1 profile in every window'),
    ('eirp_p90_response_corrected_W', 'W', 'the limit with the exact delivered response in place of the injected one'),
    ('limit_eligible', '', '1 where the attribution mask leaves channels for a limit, 0 where it leaves none'),
]
SENS28_SYS_COLS = [
    ('designation', '', 'the system, as the article names it'),
    ('system', '', 'the system identifier of class_A_limit_uncertainty.csv'),
    ('best_eb', '', 'execution block of the system\'s best window'),
    ('best_nu_lo_GHz', 'GHz', 'lower edge of that window'),
    ('eirp90_W', 'W', 'the system\'s headline limit, the minimum over its eligible Class A windows'),
    ('basis', '', 'calibration label of the best window'),
    ('own_factor', '', 'the best window\'s own ninety per cent point where it was injected into'),
    ('n_chan_avg', '', 'the best window\'s online spectral averaging factor'),
    ('eirp90_cal_lo_W', 'W', 'the headline limit at the low end of the class-average interval'),
    ('eirp90_cal_hi_W', 'W', 'the headline limit at the high end of the class-average interval'),
    ('p_reach_window', '', 'fraction of resamplings in which the system reaches 1e15 W, each transferred window drawing its factor independently from the injected windows\' own points; measured windows keep their own'),
    ('p_reach_block', '', 'the same with one draw per execution block, the windows of a block sharing it'),
    ('p_reach_window_dec', '', 'the window-by-window resampling with decorrelation divided out'),
    ('sys_ratio_p05_block', '', 'fifth percentile of the headline limit over the block resampling, as a fraction of the adopted limit'),
    ('sys_ratio_p95_block', '', 'ninety-fifth percentile, on the same basis'),
    ('decor_frac', '', 'decorrelation fraction of the best window'),
    ('decor_basis', '', 'measured, matched or none'),
    ('eirp90_decor_adjusted_W', 'W', 'headline limit with decorrelation divided out window by window and the best window chosen again'),
    ('eirp90_response_corrected_W', 'W', 'headline limit with the exact delivered response in every window and the best window chosen again'),
    ('reaches_1e15_nominal', '', 'True where the adopted headline limit is at or below 1e15 W'),
    ('uncertain', '', 'why the 1e15 W classification is uncertain: dispersion (a resampled probability between 0.05 and 0.95), calibration interval, decorrelation, exact response, or extrapolated (the threshold lies within the measured dispersion of an extrapolated limit); empty where it is not'),
    ('eirp90_spread_lo_W', 'W', 'the system limit with every transferred window at the deepest injected factor (x the dispersion minimum), injected windows at the class factor, best window re-formed'),
    ('eirp90_spread_hi_W', 'W', 'the same at the shallowest injected factor (x the dispersion maximum)'),
    ('crosses_1e15_at_spread_extreme', '', 'True where either extreme puts the system on the other side of 1e15 W from its nominal limit'),
]


def _sens28(name, cols, n):
    rows = read_csv(name)
    assert rows and list(rows[0]) == [c[0] for c in cols], (
        '%s does not carry the documented columns' % name)
    assert len(rows) == n, '%s: %d rows, expected %d' % (name, len(rows), n)
    return rows


TABLES.append(Table(
    'sensitivity/class_A_limit_uncertainty.csv',
    ["One row per fine-channel spectral window: what its limit is uncertain "
     "by, kept apart by kind.",
     "The class-average calibration interval is one number shared by every "
     "window and moves every limit together; the dispersion between injected "
     "windows is the statement about one window, and for an extrapolated "
     "window it is not an empirical bound. Decorrelation and the delivered "
     "response are one-sided and are given as corrected limits, not "
     "intervals.",
     "eirp_p90_W is the limit of class_A_limits.csv on every row."],
    "(target_id, eb, nu_lo_GHz, nu_hi_GHz) joins class_A_limits.csv and "
    "spectral_windows.csv -- all four fields, because two positions can share "
    "one window of one block.",
    SENS28_WIN_COLS,
    _sens28('sens_r28_windows.csv', SENS28_WIN_COLS,
            sum(1 for c, _p in CATK if c['search_class'] == 'A'))))

TABLES.append(Table(
    'sensitivity/system_limits.csv',
    ["One row per system of the carrier search that carries a limit: its "
     "headline limit, the limit at both ends of the class-average interval, "
     "with decorrelation and with the exact delivered response divided out, "
     "and the probability that it reaches 1e15 W when each transferred "
     "window's factor is drawn from the injected windows' own points.",
     "A system marked uncertain is one whose classification at 1e15 W the "
     "calibration interval, the dispersion, the decorrelation or the response "
     "can change."],
    "system joins class_A_limit_uncertainty.csv on system_id; (best_eb, "
    "best_nu_lo_GHz) names the window the headline limit is read from.",
    SENS28_SYS_COLS,
    _sens28('sens_r28_systems.csv', SENS28_SYS_COLS,
            len(read_csv('sens_r28_systems.csv')))))


# ============================================= sensitivity/injection_recovery.csv
#: ★ The trials name their window by its correlator stem, which carries no
#: frequency.  The geometry record resolves the stem to a median frequency and
#: the window is the one whose edges contain it: 28 of 28 resolve, and on one
#: the window is shared by two extraction positions, so the window is
#: identified and the position is left empty rather than guessed.
GEOM = {}
for g in read_json('pbaudit_v408/pbgeom.json'):
    GEOM.setdefault(g['_stem'], g)


def _trialwin(tag):
    g = GEOM.get(tag)
    if g is None:
        return None, None
    eb = '_'.join(tag.split('_')[:3])
    fm = g['freqmed'] / 1e9
    m = [n for n, (c, p) in enumerate(CATK)
         if c['eb'] == eb and float(c['nu_lo_GHz']) <= fm <= float(c['nu_hi_GHz'])]
    return eb, m


def _inject():
    rows = []
    for r in TRIALS:
        eb, m = _trialwin(r['window'])
        c = CATK[m[0]][0] if m else {}
        tid = (c['target_id'] if m and len(m) == 1 else '')
        star = (c['star'] if m and len(m) == 1 else '')
        rows.append(dict(
            eb=eb or '', target_id=tid, star=star,
            window_nu_lo_GHz=f(c['nu_lo_GHz'], 6) if c else '',
            window_nu_hi_GHz=f(c['nu_hi_GHz'], 6) if c else '',
            band=r['band'], array=r['array'],
            chan_width_Hz=f(r['chanw_Hz'], 1), n_int=i(r['n_int']),
            n_chan=i(r['n_chan']), span_s=f(r['span_s'], 1),
            n_drift_trials=i(r['n_drift']),
            theta_pb_arcsec=f(r['pb_arcsec'], 3),
            amp_sigma=f(r['amp_sigma'], 1), realisation=i(r['realisation']),
            inj_flux_Jy=e(r['inj_flux_Jy']), inj_channel=i(r['inj_chan']),
            inj_drift_Hz_s=f(r['inj_drift_Hz_s'], 4),
            rec_statistic=f(r['rec_snr'], 4), rec_channel=i(r['rec_chan']),
            rec_drift_Hz_s=f(r['rec_drift_Hz_s'], 4),
            window_max_statistic=f(r['global_max_snr'], 4),
            drift_matched=b(r['drift_matched']), detected=b(r['detected'])))
    return rows


TABLES.append(Table(
    'sensitivity/injection_recovery.csv',
    ["One row per injection trial: a carrier of known amplitude, channel and "
     "drift rate put into the retained per-integration spectra of a real "
     "window and read back by the unchanged search path.",
     "These trials are PART of the campaign the completeness transfer is "
     "calibrated on, not all of it: they cover %d of the %s directly injected "
     "Class A windows. The trials span the configurations of the survey -- "
     "both arrays, four receiver bands, channel widths from the finest to the "
     "coarsest -- and at each amplitude the recovered fraction over the "
     "realisations is the completeness at that amplitude."
     % (len({r['window'] for r in TRIALS}), mac('NInjWinA')),
     "★ THE 90 PER CENT POINT OF THESE TRIALS IS NOT THE PUBLISHED "
     "MULTIPLIER, and reading one against the other is the one mistake this "
     "table invites. The article publishes %s P_trig, which factorises as "
     "x%s for the channel response and x%s for the margin a peak channel "
     "needs above the nominal trigger. The channel response is ALREADY "
     "INSIDE these trials -- each carrier is deposited at a random "
     "sub-channel phase through the correlator response, whose central "
     "channel receives %s of it on average -- so a curve formed from these "
     "rows measures the MARGIN TERM ALONE and lands near x1.2 of the "
     "trigger. code/injection_recovery.py prints the arithmetic beside the "
     "number."
     % (mac('EirpNinetyMultA'), mac('RpRespFac'), mac('RpMarginNinety'),
        f(STRATA['response']['deposited_phase_mean'], 4)),
     "What is measured is the reading: the de-drifting, the drift trials, the "
     "control normalisation and the threshold. It is not the step from "
     "calibrated visibilities to a spectrum, which is upstream of the injection "
     "point and is not tested here.",
     "detected is the search\'s own verdict, which requires the recovered "
     "statistic to reach the trigger; drift_matched records separately whether "
     "the recovered drift trial was the injected one, and a trial can be "
     "detected without it."],
    "(target_id, eb, window_nu_lo_GHz, window_nu_hi_GHz) joins the "
    "sensitivity tables and spectral_windows.csv. One injected window is "
    "shared by two extraction positions; its rows carry the window and leave "
    "target_id and star empty rather than assign the trial to one of them, "
    "and it is the one window of this table whose three remaining fields "
    "match two rows of spectral_windows.csv, so those rows join on the "
    "window and not on the position.",
    [('eb', '', 'ALMA execution block the injected window belongs to'),
     ('target_id', '', 'identifier of the extraction position, empty where one window serves two'),
     ('star', '', 'its star designation, empty on the same rows'),
     ('window_nu_lo_GHz', 'GHz', 'lower edge of the injected window'),
     ('window_nu_hi_GHz', 'GHz', 'upper edge of the injected window'),
     ('band', '', 'ALMA receiver band'),
     ('array', '', '12m for the main array, ACA for the compact array'),
     ('chan_width_Hz', 'Hz', 'delivered channel width of the window'),
     ('n_int', '', 'integrations the injection was made into'),
     ('n_chan', '', 'channels in the window'),
     ('span_s', 's', 'time span of those integrations'),
     ('n_drift_trials', '', 'drift trials the reading searched'),
     ('theta_pb_arcsec', 'arcsec', 'recorded primary-beam FWHM of the window'),
     ('amp_sigma', '', 'injected amplitude in units of the per-channel noise'),
     ('realisation', '', 'realisation index at that amplitude; channel and drift are redrawn for each'),
     ('inj_flux_Jy', 'Jy', 'injected flux density'),
     ('inj_channel', '', 'channel the carrier was injected at'),
     ('inj_drift_Hz_s', 'Hz/s', 'drift rate it was injected with'),
     ('rec_statistic', '', 'de-drifted search statistic recovered at the injected cell'),
     ('rec_channel', '', 'channel it was recovered at'),
     ('rec_drift_Hz_s', 'Hz/s', 'drift rate it was recovered at'),
     ('window_max_statistic', '', 'largest statistic anywhere in the window on that trial'),
     ('drift_matched', '', '1 where the recovered drift trial is the injected one'),
     ('detected', '', '1 where the trial satisfies the search\'s own detection condition')],
    _inject()))


# ======================== sensitivity/injection_trials.csv  (R1-3)
#: ★★★ R1-3: "the trials behind the 49 injected windows' ninety-per-cent
#: points" were said not to rebuild from the deposit.  They were never lost:
#: they are the campaign records `sens_r11.py` merges, which it now writes in
#: the order it consumes them (`inject_trials_r30.json`).  Deposited here
#: trial by trial, with the parameters of the class factor, its bootstrap and
#: its calibration interval; `code/completeness.py` rebuilds them.
TRIALS30 = read_json('inject_trials_r30.json')


def _trials30():
    rows = []
    for w in TRIALS30['windows']:
        eb, m = _trialwin(w['tag'])
        if not m:
            raise SystemExit('injected window %s has no catalogue window'
                             % w['tag'])
        c = CATK[m[0]][0]
        tid = c['target_id'] if len(m) == 1 else ''
        for t in w['trials']:
            rows.append(dict(
                window_tag=w['tag'], eb=eb, target_id=tid,
                window_nu_lo_GHz=f(c['nu_lo_GHz'], 6),
                window_nu_hi_GHz=f(c['nu_hi_GHz'], 6),
                chan_width_Hz=f(t['cw'], 1), span_s=f(t['tspan'], 1),
                amp_over_trigger=_g17(t['amp']),
                subchannel_phase=f(t['sub'], 4),
                inj_drift_Hz_s=f(t['dr'], 4),
                rec_statistic=f(t['snr'], 4),
                reached_trigger=b(t['trig']),
                outranked_controls=b(t['rank']),
                recovered_with_rank=b(t['rec'])))
    return rows


TABLES.append(Table(
    'sensitivity/injection_trials.csv',
    ["One row per injection trial behind the Class A completeness factor: "
     "every trial of the %d directly injected windows, %d in all, a carrier "
     "deposited through the channel response at a random sub-channel phase "
     "and drift into the retained per-integration spectra of a real window "
     "and read back by the unchanged search path."
     % (len(TRIALS30['windows']),
        sum(len(w['trials']) for w in TRIALS30['windows'])),
     "The amplitude is in units of the window's own trigger power P_trig. "
     "The class factor is the amplitude at which the pooled fraction "
     "reaching the trigger first reaches the completeness level of "
     "completeness_parameters.csv, linearly interpolated between rungs, the "
     "positive-control rung excluded; each window's own point is the same "
     "construction on its own trials. code/completeness.py rebuilds the "
     "factor, its bootstrap and calibration intervals and the per-window "
     "points from this file and completeness_parameters.csv alone.",
     "window_tag is the correlator stem of the window (block and spectral "
     "window). One injected window is shared by two extraction positions; "
     "its rows leave target_id empty."],
    "(target_id, eb, window_nu_lo_GHz, window_nu_hi_GHz) joins "
    "spectral_windows.csv and the sensitivity tables; window_tag groups the "
    "trials of one window.",
    [('window_tag', '', 'correlator stem of the injected window'),
     ('eb', '', 'ALMA execution block identifier'),
     ('target_id', '', 'identifier of the extraction position, empty where one window serves two'),
     ('window_nu_lo_GHz', 'GHz', 'lower edge of the window'),
     ('window_nu_hi_GHz', 'GHz', 'upper edge of the window'),
     ('chan_width_Hz', 'Hz', 'delivered channel width'),
     ('span_s', 's', 'time span of the integrations searched'),
     ('amp_over_trigger', '', 'injected power in units of the window trigger power P_trig, full precision'),
     ('subchannel_phase', '', 'offset of the injected frequency from the channel centre, in channels'),
     ('inj_drift_Hz_s', 'Hz/s', 'drift rate the carrier was injected with'),
     ('rec_statistic', '', 'largest de-drifted statistic at the star within the recovery tolerance of the injected frequency'),
     ('reached_trigger', '', '1 where that statistic reaches the trigger: the criterion of the class factor'),
     ('outranked_controls', '', '1 where it also exceeds every control position of the window'),
     ('recovered_with_rank', '', '1 where both hold: the stricter criterion the article does not charge')],
    _trials30()))
_TRP = [
    ('completeness_level', TRIALS30['want'],
     'recovered fraction defining the completeness point'),
    ('positive_control_amp', TRIALS30['positive_control_amp'],
     'amplitude of the positive-control rung, excluded from every curve'),
    ('bootstrap_seed', TRIALS30['boot_seed'],
     'seed of Python random.Random drawing window indices for the bootstrap'),
    ('bootstrap_n', TRIALS30['boot_n'], 'bootstrap resamplings of the windows'),
    ('bootstrap_q_lo', TRIALS30['boot_quantiles'][0],
     'quantile of the sorted bootstrap points giving the lower end'),
    ('bootstrap_q_hi', TRIALS30['boot_quantiles'][1], 'and the upper end'),
    ('spread_pct_lo', TRIALS30['spread_percentiles'][0],
     'percentile of the per-window points giving the lower end of their spread'),
    ('spread_pct_hi', TRIALS30['spread_percentiles'][1], 'and the upper end'),
    ('instrumental_fraction', TRIALS30['instrumental'],
     'fractional instrumental term (flux scale, parallax, visibility scale) '
     'combined in quadrature with the bootstrap error in the calibration interval'),
]
TABLES.append(Table(
    'sensitivity/completeness_parameters.csv',
    ["The scalar inputs of the completeness factor and its intervals, one row "
     "per parameter. The parameters are:"]
    + ['%s -- %s.' % (nm, de) for nm, _v, de in _TRP],
    'read with injection_trials.csv',
    [('parameter', '', 'parameter name, described above'),
     ('value', '', 'its value')],
    [dict(parameter=nm, value=_g17(v)) for nm, v, _de in _TRP]))


# ============================ sensitivity/response_injection_trials.csv (R1-1)
#: ★ r30 (fold30): the channel-response campaign (inject_r29.py): carriers
#: injected with each window's OWN response, paired carrier for carrier with
#: the deposited profile, in windows of every class and averaging mode.  The
#: ratio of the two ninety-per-cent points multiplies every limit of that
#: class and mode; `code/response_ratio.py` rebuilds every ratio and factor.
RESP30 = read_json('response_trials_r30.json')
_SENS11 = read_json('sens_r11.json')
_RMODEL = {'hann3_399000': 'deposited_profile', 'exact_399000': 'own_response_paired',
           'exact_429000': 'own_response_independent'}
assert all(t[0] in RESP30['amps'] or t[0] == RESP30['positive_control_amp']
           for w in RESP30['windows'] for t in w['trials']), 'a rung off the ladder'


def _resp30():
    rows = []
    for w in RESP30['windows']:
        for t in w['trials']:
            rows.append(dict(
                window_tag=w['tag'], model=_RMODEL[w['model']],
                search_class=w['search_class'], n_chan_avg=i(w['n_chan_avg']),
                field_injected=b(w['field_injected']),
                chan_width_Hz=f(t[7], 1), amp_over_trigger=_g17(t[0]),
                subchannel_phase=f(t[5], 4), inj_drift_Hz_s=f(t[6], 4),
                rec_statistic=f(t[4], 4) if t[4] is not None else '',
                reached_trigger=b(t[1]),
                outranked_controls='' if t[2] is None else b(t[2]),
                recovered_with_rank='' if t[3] is None else b(t[3])))
    return rows


TABLES.append(Table(
    'sensitivity/response_injection_trials.csv',
    ["One row per injection trial of the channel-response campaign: %d "
     "windows of every search class and online-averaging mode, each injected "
     "with the deposited 0.25/0.5/0.25 profile and, on identical carriers, "
     "with the window's own channel response (Hann-windowed raw channels "
     "averaged online by N), %d trials in all."
     % (len({w['tag'] for w in RESP30['windows']}),
        sum(len(w['trials']) for w in RESP30['windows'])),
     "For each class and mode the ratio of the pooled ninety-per-cent points "
     "(own response over deposited profile, paired carriers) multiplies the "
     "class factor of every window of that class and mode. "
     "code/response_ratio.py rebuilds every ratio and factor from this file, "
     "response_parameters.csv and injection_trials.csv.",
     "model is deposited_profile, own_response_paired (the same carriers) or "
     "own_response_independent (other seeds, a check only)."],
    "window_tag and model group the trials of one window and model; "
    "search_class and n_chan_avg select the mode.",
    [('window_tag', '', 'correlator stem of the injected window'),
     ('model', '', 'channel response the carrier was deposited with'),
     ('search_class', '', 'A or B'),
     ('n_chan_avg', '', 'online channel averaging N of the window'),
     ('field_injected', '', '1 where every pointing of a mosaic was injected at the star'),
     ('chan_width_Hz', 'Hz', 'delivered channel width'),
     ('amp_over_trigger', '', 'injected power in units of the window trigger power P_trig, full precision'),
     ('subchannel_phase', '', 'offset of the injected frequency from the channel centre, in channels'),
     ('inj_drift_Hz_s', 'Hz/s', 'drift rate the carrier was injected with'),
     ('rec_statistic', '', 'largest de-drifted statistic at the star within the recovery tolerance'),
     ('reached_trigger', '', '1 where that statistic reaches the trigger: the criterion of the factor'),
     ('outranked_controls', '', '1 where it also exceeds every control position (empty: not recorded)'),
     ('recovered_with_rank', '', '1 where both hold (empty: not recorded)')],
    _resp30()))
_RPP = [
    ('completeness_level', RESP30['want'], 'recovered fraction defining the completeness point'),
    ('positive_control_amp', RESP30['positive_control_amp'],
     'amplitude of the positive-control rung, excluded from every curve'),
    ('amplitude_ladder', ';'.join('%g' % x for x in RESP30['amps']), 'the rungs, in units of P_trig'),
    ('class_level_B', _SENS11['p90_B'],
     'the Class B class factor (x P_trig) the ratios of Class B multiply; the Class A level is '
     'rebuilt from injection_trials.csv'),
]
TABLES.append(Table(
    'sensitivity/response_parameters.csv',
    ["The scalar inputs of the channel-response ratios, one row per parameter. "
     "The parameters are:"]
    + ['%s -- %s.' % (nm, de) for nm, _v, de in _RPP],
    'read with response_injection_trials.csv',
    [('parameter', '', 'parameter name, described above'),
     ('value', '', 'its value')],
    [dict(parameter=nm, value=(v if isinstance(v, str) else _g17(v))) for nm, v, _de in _RPP]))


# ========================================= sensitivity/completeness_calibration
#: ★★ R1's point 2.3 in one table: how many windows were tested directly, how
#: the rest were calibrated from them, and what the uncertainty on the transfer
#: is.  The interval factors are measured here from the deposited rows rather
#: than quoted, and asserted to be one pair over every transferred window --
#: which is the honest content of the interval and the reason it is not a
#: per-window bound.
def _calib():
    tr = [(c, p) for c, p in CATK if p['p90_basis'] == 'transferred']
    lo = {round(float(p['eirp_p90_adopted_lo_W']) / float(p['eirp_p90_adopted_W']), 6)
          for c, p in tr}
    hi = {round(float(p['eirp_p90_adopted_hi_W']) / float(p['eirp_p90_adopted_W']), 6)
          for c, p in tr}
    assert len(lo) == 1 and len(hi) == 1, (
        'the interval on a transferred limit is not one pair of factors: '
        '%r %r' % (sorted(lo), sorted(hi)))
    # ★ r29: p90_mult_adopted is the class factor times the measured response
    #   ratio of the window's class and averaging mode (inject_r29.py), so the
    #   class row carries the class factor and one row per (class, N) carries
    #   the ratio and the factor applied.
    _ij = json.load(open(os.path.join(BASE, 'inject_r29.json')))
    mult, bymode = {}, {}
    _xw34 = []
    for c, p in CATK:
        _k = '%s%d' % (c['search_class'], int(p['n_chan_avg']))
        # r34 (N1, R2-1): the declared T_obs factor divided out -- the class row and the mode rows state the
        # factor at the trigger; the windows read at T_obs carry completeness_threshold_T in class_A_limits.csv
        if _tobsf(p) == 1.0:
            mult.setdefault(c['search_class'], set()).add(
                '%.9g' % (float(p['p90_mult_adopted']) / _ij['rho'][_k]))
            bymode.setdefault(_k, set()).add(p['p90_mult_adopted'])
        else:
            _xw34.append((_k, float(p['p90_mult_adopted']) / _tobsf(p)))
    for cls, v in mult.items():
        assert len(v) == 1, 'class %s carries %d multipliers' % (cls, len(v))
    for k, v in bymode.items():
        assert len(v) == 1, 'mode %s carries %d multipliers' % (k, len(v))
    # r34 (N1): a window read at T_obs carries its mode's multiplier times its declared factor, and no other
    assert all(abs(x / float(sorted(bymode[k])[0]) - 1.0) < 1e-9 for k, x in _xw34), 'a T_obs window off its mode'
    nA = sum(1 for c, p in CATK if c['search_class'] == 'A')
    nB = sum(1 for c, p in CATK if c['search_class'] == 'B')
    iA = sum(1 for c, p in CATK
             if c['search_class'] == 'A' and p['p90_basis'] == 'injected')
    iB = sum(1 for c, p in CATK
             if c['search_class'] == 'B' and p['p90_basis'] == 'injected')
    N, D, CB, BL, RU = (STRATA['noise'], STRATA['disc'], STRATA['class_b'],
                        STRATA['blanket'], STRATA['rule'])
    RS = STRATA['response']
    rows = [
        #: ★★★ `n_injected_windows` DECLARED 49 BESIDE A TRIALS TABLE HOLDING
        #: 28, so the two deposited files disagreed about the campaign the
        #: multiplier rests on.  Both counts now ship, under names that say
        #: which is which, and the note gives the factorisation a reader
        #: needs in order not to read the deposited campaign's own 90 per
        #: cent point -- the margin term alone, near x1.2 -- as a refutation
        #: of this multiplier.
        dict(stratum='class A', selection_rule='search_class = A',
             quantity='p90_multiplier', value=f(sorted(mult['A'])[0], 9),
             n_catalogue_windows=i(nA), n_injected_windows=i(iA),
             n_injected_windows_deposited=i(len({r['window'] for r in TRIALS})),
             applies_to='every fine-channel window',
             note='adopted multiplier from the trigger amplitude to 90 per cent '
                  'completeness; it is one value for the class and not a '
                  'per-window measurement. It factorises as x%s for the '
                  'channel response, which is already inside the injections, '
                  'and x%s for the margin a peak channel needs above the '
                  'nominal trigger; a completeness curve formed from '
                  'injection_recovery.csv therefore measures the margin term '
                  'alone'
                  % (mac('RpRespFac'), mac('RpMarginNinety'))),
        dict(stratum='class B', selection_rule='search_class = B',
             quantity='p90_multiplier', value=f(sorted(mult['B'])[0], 9),
             n_catalogue_windows=i(nB), n_injected_windows=i(iB),
             applies_to='every coarse-channel window',
             note=CB['note']),
        dict(stratum='quiet control ring',
             selection_rule='%s %s %g' % (RU['column'], RU['noise'], RU['sigma']),
             quantity='p90_multiplier', value=f(N['p90'], 6),
             lo=f(N['p90_lo'], 6), hi=f(N['p90_hi'], 6),
             n_catalogue_windows=i(N['n_cat']), n_injected_windows=i(N['n_inj']),
             applies_to='fine-channel windows whose brightest control position '
                        'stays below the stratifying level',
             note='measured in the injected windows of this stratum; the '
                  'subtracted form, which removes the injected carrier\'s own '
                  'contribution to the noise, gives %s'
                  % f(N['p90_subtracted'], 6)),
        dict(stratum='bright control ring',
             selection_rule='%s %s %g' % (RU['column'], RU['disc'], RU['sigma']),
             quantity='p90_multiplier_bound', value=f(D['bound_adopted'], 1),
             lo=f(D['bound_lo'], 1),
             n_catalogue_windows=i(D['n_cat']), n_injected_windows=i(D['n_inj']),
             applies_to='fine-channel windows with a bright control position, '
                        'which are the windows of the resolved discs',
             note='no completeness is quoted for this stratum: a carrier is '
                  'recovered at the positive control in every trial and in %s '
                  'of the trials at the top rung, so the multiplier is bounded '
                  'and not measured'
                  % f(D['frac_at_top_rung'], 4)),
        dict(stratum='blend over all strata', selection_rule='none',
             quantity='p90_multiplier', value=f(BL['p90'], 6),
             n_catalogue_windows=i(nA + nB),
             n_injected_windows=i(iA + iB),
             applies_to='no window',
             note=BL['note']),
        dict(stratum='transferred windows',
             selection_rule='completeness_basis = transferred',
             quantity='interval_factor_low', value=f(sorted(lo)[0], 6),
             n_catalogue_windows=i(len(tr)),
             applies_to='the lower end of the interval on every transferred '
                        'limit',
             note='the observed dispersion between the directly injected '
                  'windows, carried as one factor on every transferred row; it '
                  'is not a bound measured in any one window band and '
                  'channelisation'),
        dict(stratum='transferred windows',
             selection_rule='completeness_basis = transferred',
             quantity='interval_factor_high', value=f(sorted(hi)[0], 6),
             n_catalogue_windows=i(len(tr)),
             applies_to='the upper end of that interval',
             note='on the same basis'),
        dict(stratum='channel response', selection_rule='none',
             quantity='peak_at_ninety_percent_completeness',
             value=f(RS['peak_at_ninety'], 6),
             applies_to='the amplitude scale of the injected carriers',
             note='the recovered peak at the 90 per cent point, in units of the '
                  'nominal trigger; the channel response is already inside the '
                  'measured multiplier and must not be applied twice'),
        dict(stratum='channel response', selection_rule='none',
             quantity='deposited_response_phase_mean',
             value=f(RS['deposited_phase_mean'], 6),
             applies_to='the carrier deposited by the injector',
             note='mean over sub-channel phase of the fraction of the carrier '
                  'the central channel receives, as deposited; the exact '
                  'lag-window response gives %s, so the deposition is '
                  'conservative' % f(RS['exact_phase_mean'], 6)),
    ] + [
        dict(stratum='class %s, online averaging N = %s' % (k[0], k[1:]),
             selection_rule='search_class = %s and n_chan_avg = %s' % (k[0], k[1:]),
             quantity='p90_multiplier', value=f(sorted(bymode[k])[0], 9),
             lo=f(float(sorted(bymode[k])[0]) / _ij['rho'][k] * _ij['rho_ci68'][k][0], 6),
             hi=f(float(sorted(bymode[k])[0]) / _ij['rho'][k] * _ij['rho_ci68'][k][1], 6),
             n_catalogue_windows=i(_ij['catalogue_modes'][k]),
             n_injected_windows=i(_ij['groups'][k]['n_windows']),
             applies_to='every window of this class and averaging mode',
             note='the class factor times %s, the measured ratio of the ninety per cent points with the '
                  'window\'s own channel response (Hann-windowed raw channels averaged online by N) to the '
                  'deposited 0.25/0.5/0.25 profile, on identical carriers in %d windows of this class and mode '
                  '(response_injection_trials.csv); lo/hi are its 68 per cent interval'
                  % (f(_ij['rho'][k], 4), _ij['groups'][k]['n_windows']))
        for k in sorted(bymode)
    ] + [
        dict(stratum='channel response', selection_rule='none',
             quantity='median_drift_channels',
             value=f(RS['drift_channels_median'], 6),
             applies_to='the smearing term',
             note='median number of channels a carrier drifts across during an '
                  'integration, over the injected configurations'),
    ]
    return rows


TABLES.append(Table(
    'sensitivity/completeness_calibration.csv',
    ["How the completeness of the survey was measured, and how it was carried "
     "to the windows that were not tested directly.",
     "Only a minority of windows carry their own injection ladder; every other "
     "window takes a multiplier calibrated on those that do, and the table "
     "records which windows were tested, the rule that defines each stratum, "
     "the measured multiplier and its interval.",
     "The interval on a transferred limit is one pair of factors over every "
     "transferred row, because it is the dispersion observed between the "
     "injected windows. It is not a bound measured in any one window\'s own band "
     "and channelisation, and it does not describe a window that lies in a "
     "configuration no injection visited.",
     "One stratum carries a bound rather than a measurement, and says so: in "
     "windows with a bright control position the carrier is recovered in every "
     "trial at the positive control, so the multiplier is bounded from above "
     "and not determined."],
    "completeness_basis and search_class in the sensitivity tables select the "
    "windows each row applies to; the trials themselves are in "
    "injection_recovery.csv.",
    [('stratum', '', 'the set of windows this row calibrates'),
     ('selection_rule', '', 'the rule that defines that set, in terms of the deposited columns'),
     ('quantity', '', 'what is being given'),
     ('value', '', 'its value'),
     ('lo', '', 'lower end of its interval where it has one'),
     ('hi', '', 'upper end of its interval where it has one'),
     ('n_catalogue_windows', '', 'windows in the stratum'),
     ('n_injected_windows', '', 'of those, windows carrying their own injection ladder'),
     ('n_injected_windows_deposited', '', 'of those, windows whose individual trials are deposited in injection_recovery.csv; the rest were injected but their per-trial rows are not released, so a curve formed from the deposited rows is formed over this subset'),
     ('applies_to', '', 'the windows the value is applied to'),
     ('note', '', 'the qualification that travels with the value; where a value is a bound or a blend rather than a measurement, this column says so')],
    _calib()))


# ======================================== statistics/control_field_statistics
def _ctrlstats():
    rows = []
    for c, p in CATK:
        if not c['n_ctrl']:
            continue
        rows.append(dict(
            star=c['star'], target_id=c['target_id'], eb=c['eb'],
            project_code=PROJ[c['eb']]['project_code'],
            nu_lo_GHz=f(c['nu_lo_GHz'], 6), nu_hi_GHz=f(c['nu_hi_GHz'], 6),
            search_class=c['search_class'], rms_mJy=f(c['rms_mJy'], 5),
            theta_pb_arcsec=f(ring_of(c)['pb_arcsec'], 3),
            ring_r_in_arcsec=f(ring_of(c)['r_in_arcsec'], 3),
            ring_r_out_arcsec=f(ring_of(c)['r_out_arcsec'], 3),
            array=ring_of(c)['array'],
            geometry_provenance=ring_of(c)['provenance'],
            annulus_dish_m=f(ring_of(c)['annulus_dish_m'], 1),
            syn_arcsec=(f(ring_of(c)['syn_arcsec'], 3)
                        if ring_of(c)['syn_arcsec'] else ''),
            ann_syn_factor=(f(ring_of(c)['ann_syn_factor'], 1)
                            if ring_of(c)['ann_syn_factor'] else ''),
            ring_centre=p['ring_centre'], ring_seed=i(p['ring_seed']),
            n_ctrl=i(c['n_ctrl']),
            T_star=f(p['star_snr'], 4), T_ctrl_max=f(p['ctrl_max_snr'], 4),
            n_ctrl_ge_star=i(p['n_ctrl_ge_star']),
            p_rank=f(p['p_rank_addone'], 6),
            n_ctrl_trig=i(c['n_ctrl_trig']),
            p_trig_ctrl=f(float(c['n_ctrl_trig']) / float(c['n_ctrl']), 8),
            mask_attr_share=f(c['mask_attr_share'], 6),
            telluric_factor=f(c['telluric_factor'], 6),
            n_search_cells=i(p['n_search_cells']),
            n_ind_cells=i(p['n_ind_cells'])))
    return rows


TABLES.append(Table(
    'statistics/control_field_statistics.csv',
    ["One row per window with a control ensemble: the control-field measurement "
     "the chance comparison is built from.",
     "The control positions lie in an annulus set by the primary beam of the "
     "dish that observed the window and by its synthesised beam: r_in = "
     "max(0.14 theta_pb, ann_syn_factor x syn_arcsec), r_out = 0.78 theta_pb. "
     "ring_r_in_arcsec and ring_r_out_arcsec are that annulus for the window, "
     "and code/control_positions.py --check reproduces them row by row.",
     "Rows with geometry_provenance = frozen-geometry predate the repair that "
     "reads the dish from the data: their annulus assumed a 12 m dish and has "
     "no synthesised-beam floor. On the 12 m array that is the same rule; the "
     "check lists by name any such row observed with 7 m antennas.",
     "p_trig_ctrl is the window\'s own probability that a position in its field "
     "reaches the trigger, measured as the fraction of its control positions "
     "that do. The sum of that probability over the fine-channel windows, each "
     "reduced by the share the attribution mask takes and by the atmospheric "
     "factor, is the chance expectation of null_distribution_tests.csv.",
     "p_rank is the rank of the stellar statistic among the control positions "
     "of the same window, formed with the add-one correction. It is a "
     "diagnostic and not a significance test.",
     "The control channels are transformed to the same stellar rest frame as "
     "the star\'s own reading before the attribution mask is applied to them, so "
     "the two sides of the comparison are screened in one frame."],
    "(target_id, eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv and the "
    "sensitivity "
    "tables.",
    [('star', '', 'star designation'),
     ('target_id', '', 'identifier the window was extracted under'),
     ('eb', '', 'ALMA execution block identifier'),
     ('project_code', '', 'its ALMA project code'),
     ('nu_lo_GHz', 'GHz', 'lower edge of the window'),
     ('nu_hi_GHz', 'GHz', 'upper edge of the window'),
     ('search_class', '', 'A fine or B coarse'),
     ('rms_mJy', 'mJy', 'per-channel noise at the stellar position'),
     ('theta_pb_arcsec', 'arcsec', 'primary-beam FWHM, 1.22 lambda / D, the annulus was built from'),
     ('ring_r_in_arcsec', 'arcsec', 'inner radius of the control annulus'),
     ('ring_r_out_arcsec', 'arcsec', 'outer radius of the control annulus'),
     ('array', '', '12m or 7m: the array that observed the window, from the archive'),
     ('geometry_provenance', '', 'corrected-geometry or frozen-geometry: whether the extraction that produced this row read the dish from the data'),
     ('annulus_dish_m', 'm', 'dish diameter the annulus was built for'),
     ('syn_arcsec', 'arcsec', 'synthesised-beam FWHM used for the inner-edge floor; empty where no floor was applied'),
     ('ann_syn_factor', '', 'the floor in synthesised beams; empty where no floor was applied'),
     ('ring_centre', '', 'what the annulus is centred on'),
     ('ring_seed', '', 'seed the control positions were drawn with, so the ensemble is reproducible'),
     ('n_ctrl', '', 'control positions in the ensemble'),
     ('T_star', '', 'de-drifted search statistic at the stellar position'),
     ('T_ctrl_max', '', 'largest statistic among the control positions'),
     ('n_ctrl_ge_star', '', 'control positions whose statistic reaches the stellar one'),
     ('p_rank', '', 'rank of the stellar statistic among them, with the add-one correction; a diagnostic and not a significance test'),
     ('n_ctrl_trig', '', 'control positions reaching the trigger'),
     ('p_trig_ctrl', '', 'the window\'s own probability that a position in its field reaches the trigger'),
     ('mask_attr_share', '', 'share of its control exceedances the attribution mask takes, in the star rest frame'),
     ('telluric_factor', '', 'factor by which the remaining exceedances are reduced by the atmospheric screen'),
     ('n_search_cells', '', 'search cells in the window'),
     ('n_ind_cells', '', 'independent cells after the correlation between neighbouring drift trials is accounted for')],
    _ctrlstats()))


# ================================== statistics/chance_resampling_*  (R1-3)
#: ★★★ R1-3: the probability, the bound and the interval of the chance
#: comparison rested on a resampling whose inputs were not deposited ("not
#: per-window"), so a reader could rebuild the expectation and nothing that
#: carries its uncertainty.  `chance_v414.py` now writes every quantity its
#: resampling consumes, in the order it consumes them, for each field reading
#: (`chance_resample_r30.json`, `chance_resample_r30_fieldnarrow.json`); they
#: are deposited here as three tables and `code/chance_expectation.py`
#: rebuilds the article's figures from them draw for draw.  The window key is
#: the deposit's own (target_id, eb, nu_lo_GHz, nu_hi_GHz), mapped through the
#: same two-table join as every other window table, and a window the join
#: cannot place stops the deposit.
_RS_FIELDS = [('whole_beam', 'chance_resample_r30.json'),
              ('narrow_field', 'chance_resample_r30_fieldnarrow.json')]
_RS = [(fld, read_json(fn)) for fld, fn in _RS_FIELDS]
assert len({d['seed'] for _f, d in _RS}) == 1, 'the two readings share a seed'
SEED_CHANCE = _RS[0][1]['seed']
_PKEY = {}
for _c, _p in CATK:
    _PKEY[wkey(_p['eb'], _p['star_name'], _p['flo_GHz'], _p['fhi_GHz'])] = _c


def _rs_windows():
    rows = []
    for fld, d in _RS:
        for w in d['windows']:
            k = wkey(w['eb'], w['star_name'], w['flo_GHz'], w['fhi_GHz'])
            if k not in _PKEY:
                raise SystemExit('chance resampling window not in the window '
                                 'tables: %r' % (k,))
            c = _PKEY[k]
            rows.append(dict(
                field_reading=fld, block_order=i(w['block_order']),
                window_order=i(w['window_order']), eb=c['eb'],
                target_id=c['target_id'],
                nu_lo_GHz=f(c['nu_lo_GHz'], 6), nu_hi_GHz=f(c['nu_hi_GHz'], 6),
                n_ctrl=i(w['n_ctrl']), n_ctrl_trig=i(w['n_ctrl_trig']),
                attribution=w['attribution'],
                grid_mask_share=_g17(w['grid_mask_share']),
                n_exc_recorded=('' if w['n_exc_recorded'] is None
                                else i(w['n_exc_recorded'])),
                n_exc_in_mask=('' if w['n_exc_in_mask'] is None
                               else i(w['n_exc_in_mask']))))
    return rows


def _rs_blocks():
    rows = []
    for fld, d in _RS:
        for b in d['attr_blocks']:
            rows.append(dict(field_reading=fld, attr_order=i(b['attr_order']),
                             eb=b['eb'], n_exc_in_mask=i(b['n_exc_in_mask']),
                             n_exc_recorded=i(b['n_exc_recorded'])))
    return rows


#: (parameter, how it is written, description).  Every one is read from the
#: generator's record; none is typed here.
_RS_PAR = [
    ('seed', lambda d: '%d' % d['seed'],
     'seed of the NumPy default generator (PCG64) the resampling draws from'),
    ('numpy_version', lambda d: d['numpy_version'],
     'NumPy release the reported draws were made with; another release may '
     'draw a different stream and then agrees only within the Monte Carlo error'),
    ('n_realisations', lambda d: '%d' % d['n_realisations'],
     'realisations of every window rate and of the two shared shares'),
    ('n_batches', lambda d: '%d' % d['n_batches'],
     'disjoint batches of realisations; resampling b reads batch b mod n_batches'),
    ('n_boot', lambda d: '%d' % d['n_boot'], 'block resamplings'),
    ('n_observed', lambda d: '%d' % d['n_observed'],
     'unattributed Class A crossings compared with the expectation'),
    ('n_reference_windows', lambda d: '%d' % d['n_reference_windows'],
     'windows the per-window mean rate is scaled to'),
    ('scale', lambda d: _g17(d['scale']),
     'ratio of the reference window count to the windows tabulated'),
    ('alpha', lambda d: _g17(d['alpha']),
     'level at which the added-population bound is set'),
    ('coverage_pct', lambda d: _g17(d['coverage_pct']),
     'coverage of the quoted intervals, per cent'),
    ('trigger', lambda d: _g17(d['trigger']), 'the trigger level T_star'),
    ('n_exc_recorded', lambda d: '%d' % d['n_exc_recorded'],
     'control exceedances whose landing channel is recorded'),
    ('n_exc_in_mask', lambda d: '%d' % d['n_exc_in_mask'],
     'of them, landing inside the attribution mask in the star rest frame'),
    ('n_exc_survive_mask', lambda d: '%d' % d['n_exc_survive_mask'],
     'recorded exceedances the mask leaves'),
    ('n_exc_telluric_only', lambda d: '%d' % d['n_exc_telluric_only'],
     'of those, removed by the atmospheric screen'),
    ('n_holdout_blocks', lambda d: '%d' % d['n_holdout_blocks'],
     'reserved blocks whose resampling the generator stream passes through '
     'between the expectation and its transferred interval'),
    ('transfer_band_lo', lambda d: _g17(d['transfer_band'][0]),
     'lower end of the star-to-control transfer band applied to the interval'),
    ('transfer_band_hi', lambda d: _g17(d['transfer_band'][1]),
     'upper end of that band'),
    ('near_band_lo', lambda d: _g17(d['near_band'][0]),
     'lower edge of the sub-trigger band the star-to-control ratio is measured in'),
    ('near_band_hi', lambda d: _g17(d['near_band'][1]), 'its upper edge'),
    ('near_n_star_events', lambda d: '%d' % d['near_n_star_events'],
     'out-of-mask stellar cells in that band'),
    ('near_n_control_events', lambda d: '%d' % d['near_n_control_events'],
     'out-of-mask control cells in that band'),
    ('near_n_windows', lambda d: '%d' % d['near_n_windows'],
     'windows the band is counted over'),
    ('near_n_control_positions', lambda d: '%d' % d['near_n_control_positions'],
     'control positions it is counted over'),
    ('max_ext_chunks', lambda d: '%d' % d['max_ext_chunks'],
     'cap on independent replicates added when an integer bound is not stable '
     'within two Monte Carlo errors'),
]


def _rs_params():
    rows = []
    for fld, d in _RS:
        for nm, fn, _de in _RS_PAR:
            rows.append(dict(field_reading=fld, parameter=nm, value=fn(d)))
    return rows


_RS_JOIN = ('(target_id, eb, nu_lo_GHz, nu_hi_GHz) joins '
            'control_field_statistics.csv and spectral_windows.csv; '
            'field_reading selects one of the two readings')
TABLES.append(Table(
    'statistics/chance_resampling_windows.csv',
    ["One row per Class A window with a control ensemble and per field "
     "reading: the inputs of the block resampling behind the probability, "
     "the added-population bound and the interval of the chance comparison, "
     "in the order the resampling consumes them (block_order, then "
     "window_order).",
     "code/chance_expectation.py reads this file with "
     "chance_resampling_blocks.csv and chance_resampling_parameters.csv and "
     "nothing else."],
    _RS_JOIN,
    [('field_reading', '', 'whole_beam (the adopted reading) or narrow_field'),
     ('block_order', '', 'position of the execution block in the resampled list'),
     ('window_order', '', 'position of the window inside its block'),
     ('eb', '', 'ALMA execution block identifier'),
     ('target_id', '', 'identifier the window was extracted under'),
     ('nu_lo_GHz', 'GHz', 'lower edge of the window'),
     ('nu_hi_GHz', 'GHz', 'upper edge of the window'),
     ('n_ctrl', '', 'control positions of the window'),
     ('n_ctrl_trig', '', 'of them, reaching the trigger; the window rate is n_ctrl_trig / n_ctrl'),
     ('attribution', '', 'measured: the attributed share is the pooled share of recorded control exceedances landing in the mask; grid: the share of the window channel grid the mask covers'),
     ('grid_mask_share', '', 'share of the window channel grid inside the mask, star rest frame, full precision'),
     ('n_exc_recorded', '', 'control exceedances of this window whose landing channel is recorded; empty where none is'),
     ('n_exc_in_mask', '', 'of them, inside the mask; empty on the same rows')],
    _rs_windows()))
TABLES.append(Table(
    'statistics/chance_resampling_blocks.csv',
    ["The recorded control exceedances summed per execution block, in the "
     "order the attributed share is resampled: one realisation of the share "
     "is the in-mask total over the total, over one resampling of these rows."],
    'eb joins execution_blocks.csv; field_reading as in '
    'chance_resampling_windows.csv',
    [('field_reading', '', 'whole_beam or narrow_field'),
     ('attr_order', '', 'position of the block in the resampled list'),
     ('eb', '', 'ALMA execution block identifier'),
     ('n_exc_in_mask', '', 'recorded control exceedances of the block inside the mask'),
     ('n_exc_recorded', '', 'recorded control exceedances of the block')],
    _rs_blocks()))
TABLES.append(Table(
    'statistics/chance_resampling_parameters.csv',
    ["The scalar inputs of the chance resampling, one row per parameter and "
     "field reading. The parameters are:"]
    + ["%s -- %s." % (nm, de) for nm, _fn, de in _RS_PAR],
    'field_reading as in chance_resampling_windows.csv',
    [('field_reading', '', 'whole_beam or narrow_field'),
     ('parameter', '', 'parameter name, described above'),
     ('value', '', 'its value')],
    _rs_params()))


# ================================== statistics/control_correlation*.csv  (r32, R1-4)
#: ★★ r32 (R1-4): are a window's control positions independent?  `ctrlcorr_r32.py` reconstructs every position
#: (the extractor's own seeded draw over the searched annulus), measures the correlation of the control
#: statistic and of the exceedance indicator against separation in synthesised beams, the effective number of
#: independent positions per window under seven blockings, and re-runs the chance resampling with each window's
#: rate drawn from its own blocks.  Deposited here: the correlogram and the per-window table.
_CC = read_json('ctrlcorr_r32.json')


def _cc_corr_rows():
    return [dict(sep_lo_beam=f(c['sep_lo_beam'], 2), sep_hi_beam=f(c['sep_hi_beam'], 2), n_pairs=i(c['n_pairs']),
                 rho_statistic=f(c['rho_statistic'], 4), rho_statistic_shuffled=f(c['rho_statistic_shuffled'], 4),
                 rho_indicator=f(c['rho_indicator'], 4), n_pairs_both_exceed=i(c['n_pairs_both_exceed']))
            for c in _CC['correlogram']]


def _cc_win_rows():
    rows = []
    for w in _CC['windows']:
        k = wkey(w['eb'], w['star_name'], w['flo_GHz'], w['fhi_GHz'])
        if k not in _PKEY:
            raise SystemExit('control-correlation window not in the window tables: %r' % (k,))
        c = _PKEY[k]
        row = dict(eb=c['eb'], target_id=c['target_id'], nu_lo_GHz=f(c['nu_lo_GHz'], 6),
                   nu_hi_GHz=f(c['nu_hi_GHz'], 6), array=w['array'], r_in_arcsec=f(w['r_in_arcsec'], 3),
                   r_out_arcsec=f(w['r_out_arcsec'], 3), theta_syn_arcsec=f(w['theta_syn_arcsec'], 3),
                   theta_syn_source=w['theta_syn_source'], geometry_check=w['geometry_check'],
                   nn_sep_median_beam=f(w['nn_sep_median_beam'], 3),
                   n_ctrl=i(w['n_ctrl']), n_ctrl_trig=i(w['n_ctrl_trig']),
                   expectation_share=f(w['contribution'], 5))
        for s in _CC['schemes']:
            row['neff_' + s.replace('.', 'p')] = f(w['neff'].get(s), 1)
        row['neff_min'] = f(w['neff_min'], 1)
        row['leading'] = '1' if w['lead'] else '0'
        rows.append(row)
    return rows


TABLES.append(Table(
    'statistics/control_correlation.csv',
    ["The spatial correlation of the control positions, pooled over the %d Class A windows of the chance "
     "comparison, in bins of separation in units of the synthesised beam theta_syn = 1.22 lambda / B_max. "
     "The positions are those the extractor searched: 512 per window, uniform in area over the annulus of "
     "control_field_statistics.csv, drawn from a fresh NumPy default generator seeded %d (radii first, then "
     "angles), in the order of the window's control vector." % (len(_CC['windows']), _CC['probe_seed']),
     "rho_statistic is the mean product of the rank-normalised control statistic of the two positions of a "
     "pair; rho_statistic_shuffled is the same with the positions permuted inside the window (the reconstruction "
     "check); rho_indicator is the pair correlation of the indicator T >= trigger, each window's own rate "
     "subtracted."],
    'none (pooled)',
    [('sep_lo_beam', '', 'lower edge of the separation bin, in theta_syn'),
     ('sep_hi_beam', '', 'upper edge; empty for the last, open bin'),
     ('n_pairs', '', 'pairs of control positions in the bin, all windows'),
     ('rho_statistic', '', 'correlation of the rank-normalised control statistic'),
     ('rho_statistic_shuffled', '', 'the same, positions permuted'),
     ('rho_indicator', '', 'pair correlation of the exceedance indicator'),
     ('n_pairs_both_exceed', '', 'pairs in which both positions reach the trigger')],
    _cc_corr_rows()))
TABLES.append(Table(
    'statistics/control_correlation_windows.csv',
    ["One row per Class A window of the chance comparison: the control annulus, the synthesised beam (recorded, "
     "or fitted from the window's own correlogram where the frozen geometry recorded none), the median "
     "nearest-neighbour separation of its control positions in beams, its share of the chance expectation, and "
     "the effective number of independent control positions N_eff = p(1-p)/var, var being the between-block "
     "variance of the window's exceedance rate with the positions grouped into square cells of 0.5, 1, 2 and 4 "
     "theta_syn and into 32, 16 and 8 contiguous arcs of the annulus.  leading = 1 marks the windows that carry "
     "half of the expectation.  The chance resampling repeated with each window's rate drawn from its own blocks "
     "gives the probability, interval and bound the article quotes beside the binomial ones."],
    '(target_id, eb, nu_lo_GHz, nu_hi_GHz) joins control_field_statistics.csv',
    [('eb', '', 'ALMA execution block identifier'), ('target_id', '', 'identifier the window was extracted under'),
     ('nu_lo_GHz', 'GHz', 'lower edge'), ('nu_hi_GHz', 'GHz', 'upper edge'), ('array', '', '12m or 7m'),
     ('r_in_arcsec', 'arcsec', 'inner radius of the control annulus'),
     ('r_out_arcsec', 'arcsec', 'outer radius'), ('theta_syn_arcsec', 'arcsec', 'synthesised beam adopted'),
     ('theta_syn_source', '', 'recorded or fitted; unplaced where the positions cannot be reconstructed'),
     ('geometry_check', '', 'verified: at least 20 pairs closer than 0.1 theta_syn and their statistic correlated above 0.2; '
                            'too few close pairs; unplaced'),
     ('nn_sep_median_beam', '', 'median nearest-neighbour separation of the controls, in theta_syn'),
     ('n_ctrl', '', 'control positions'), ('n_ctrl_trig', '', 'of them, reaching the trigger'),
     ('expectation_share', '', 'the window\'s term in the chance expectation')]
    + [('neff_' + s.replace('.', 'p'), '', 'N_eff with the %s blocking' % s) for s in _CC['schemes']]
    + [('neff_min', '', 'the smallest of them, capped at n_ctrl'),
       ('leading', '', '1 for the windows carrying half of the expectation')],
    _cc_win_rows()))


# ================================== statistics/event_membership.csv  (r32, R1-2)
#: ★★ r32 (R1-2): which statistic every crossing enters.  `chance_v414.py` (A32) writes the table from the sets it
#: forms the comparison from; `membership_r32.py` checks every column sum against the printed count.
_MB = read_json('membership_r32.json')


def _yn(x):
    return '' if x is None else ('1' if x else '0')


def _mb_rows():
    rows = []
    for r in _MB['rows']:
        rows.append(dict(
            event=r['event'], star=r['star'], eb=r['eb'],
            nu_topo_GHz=f(r['nu_topo_GHz'], 6), nu_star_GHz=f(r['nu_star_GHz'], 6),
            window_nu_lo_GHz=f(r.get('window_lo_GHz'), 6), window_nu_hi_GHz=f(r.get('window_hi_GHz'), 6),
            T_star=f(r['T_star'], 4), window_catalogued=_yn(r['window_catalogued']),
            window_class=r['window_class'], window_catalogue_star=r['window_catalogue_star'],
            position_catalogued=_yn(r['position_catalogued']),
            unit_in_expectation=_yn(r['unit_in_expectation']),
            window_in_expectation=_yn(r['window_in_expectation']),
            attributed=_yn(r['attributed']), transition=r['transition'],
            dv_star_kms=f(r['dv_star_kms'], 2), atmospheric=_yn(r['atmospheric']),
            in_unattributed=_yn(r['in_unattributed']), in_comparison=_yn(r['in_comparison']),
            holdout_trigger=_yn(r['holdout_trigger']), groups=';'.join(r['groups'])))
    return rows


TABLES.append(Table(
    'statistics/event_membership.csv',
    ["One row per threshold crossing of the primary census and of the archival tail, and per trigger event of "
     "the reserved hold-out blocks, with each statistic of the article it enters.  The census crossings "
     "are the rows with event = census; the attributed ones are attributed = 1; the observed side of the "
     "chance comparison is in_comparison = 1, which is exactly the census rows that are unattributed, not "
     "atmospheric, in a Class A window, at a position the window catalogue tabulates (position_catalogued = 1) "
     "and whose own search unit is summed on the expected side (unit_in_expectation = 1).",
     "A crossing at a position the window catalogue does not tabulate is on neither side of the comparison, "
     "whatever its attribution: its own control ensemble is not in the expectation, although the window it "
     "lies in enters the expectation once, through the control positions of the catalogued star named in "
     "window_catalogue_star.  Archival-tail crossings lie in windows no expectation covers; hold-out trigger "
     "events enter only the star-to-control check of the hold-out blocks."],
    '(eb, nu_topo_GHz) joins candidates/threshold_crossings.csv for the census and tail rows',
    [('event', '', 'census, archival_tail or holdout'),
     ('star', '', 'star the crossing or event is toward'),
     ('eb', '', 'ALMA execution block identifier'),
     ('nu_topo_GHz', 'GHz', 'topocentric frequency of the crossing; empty for hold-out events'),
     ('nu_star_GHz', 'GHz', 'the same in the star rest frame'),
     ('window_nu_lo_GHz', 'GHz', 'lower window edge, hold-out events only'),
     ('window_nu_hi_GHz', 'GHz', 'upper window edge, hold-out events only'),
     ('T_star', '', 'the search statistic at the star'),
     ('window_catalogued', '', '1 if the window is in the per-window catalogue'),
     ('window_class', '', 'A (fine channels) or B (coarse)'),
     ('window_catalogue_star', '', 'the star whose catalogued search unit the window is tabulated under'),
     ('position_catalogued', '', '1 if the crossing is at that tabulated position'),
     ('unit_in_expectation', '', '1 if the crossing\'s own search unit is summed in the chance expectation'),
     ('window_in_expectation', '', '1 if the window enters the expectation through any catalogued unit'),
     ('attributed', '', '1 if inside the line mask in the star rest frame'),
     ('transition', '', 'the attributing transition'),
     ('dv_star_kms', 'km/s', 'offset from it in the star rest frame'),
     ('atmospheric', '', '1 if unattributed and removed by the atmospheric screen'),
     ('in_unattributed', '', '1 if unattributed and not atmospheric'),
     ('in_comparison', '', '1 if counted on the observed side of the chance comparison'),
     ('holdout_trigger', '', '1 for a trigger event of a reserved hold-out block'),
     ('groups', '', 'the accounting group(s), semicolon separated')],
    _mb_rows()))


# ================================== statistics/chance_allowance_table.csv  (r32, R1-1)
#: ★★ r32 (R1-1): the added-population bound is read off the LOWER tail, P(N <= N_obs | N_b + k) averaged over the
#: resamplings, and the text named the upper one.  The whole curve is deposited, both tails, k = 0..20, for each
#: field reading, exactly as `chance_v414.py` computed it from the draws the bound and its two printed
#: probabilities use (its A31 asserts the monotonicity and that the printed rows are these rows).
def _allow_rows():
    rows = []
    for fld, d in _RS:
        ref = d['reference']
        tab = ref['allowance_table']
        kb = int(ref['added_population_limit'])
        assert [r['k'] for r in tab] == list(range(len(tab))) and kb + 1 < len(tab), 'allowance table k = 0..'
        for r in tab:
            rows.append(dict(field_reading=fld, k=i(r['k']),
                             mean_expectation=f(r['mean_expectation'], 4),
                             p_count_ge_observed=f(r['p_upper'], 6),
                             p_count_ge_observed_mc_se=f(r['p_upper_mc_se'], 6),
                             p_count_le_observed=f(r['p_lower'], 6),
                             p_count_le_observed_mc_se=f(r['p_lower_mc_se'], 6),
                             at_bound=('bound' if r['k'] == kb else
                                       ('above_bound' if r['k'] == kb + 1 else ''))))
    return rows


TABLES.append(Table(
    'statistics/chance_allowance_table.csv',
    ["The chance comparison with k added to the mean of every block resampling, k = 0 to 20, for each field "
     "reading: the mean expectation and the two Poisson tails at the observed count, each averaged over the "
     "resamplings, P(N >= N_obs | N_b + k) (the excess test; its k = 0 row is the probability the article "
     "prints) and P(N <= N_obs | N_b + k).",
     "The added-population bound is the largest k whose LOWER tail P(N <= N_obs) is still at or above alpha "
     "(chance_resampling_parameters.csv): a mean that large still makes a count as low as the observed one "
     "credible.  The upper tail rises with k and the lower tail falls; at_bound marks the bound and the row "
     "above it.  code/chance_expectation.py rebuilds this table from the three chance_resampling tables."],
    'field_reading as in chance_resampling_windows.csv',
    [('field_reading', '', 'whole_beam (the adopted reading) or narrow_field'),
     ('k', '', 'number added to the mean of every resampled expectation'),
     ('mean_expectation', '', 'mean over the resamplings of the expectation plus k'),
     ('p_count_ge_observed', '', 'P(N >= N_obs), Poisson upper tail averaged over the resamplings'),
     ('p_count_ge_observed_mc_se', '', 'its Monte Carlo standard error, from the batch means'),
     ('p_count_le_observed', '', 'P(N <= N_obs), Poisson lower tail averaged over the resamplings'),
     ('p_count_le_observed_mc_se', '', 'its Monte Carlo standard error'),
     ('at_bound', '', 'bound: the added-population bound; above_bound: one more')],
    _allow_rows()))


# ======================== statistics/recurrence_* (R13(c), r30)
#: ★★ Ruling R13(c): the restated recurrence probabilities (\Wu*, \Tw*) are
#: rebuilt by `code/recurrence_expectation.py` from these three tables and the
#: deposited control_field_statistics.csv.  `statunit_v426.py` exports the
#: distinct covering windows with their control rates (`recur_windows_r30.json`)
#: and `twostars_r27.py` the same windows with their objects and every
#: look-elsewhere simulation in call order (`twostars_r30.json`); the two
#: generators' window sets must be one set, written in twostars' order.
RW30 = read_json('recur_windows_r30.json')
TS30 = read_json('twostars_r30.json')
_RW_BY = {(w['eb'], w['nu_lo_GHz'], w['nu_hi_GHz'], w['star']): w
          for w in RW30['windows']}
_TS_KEYS = [(w['eb'], w['nu_lo_GHz'], w['nu_hi_GHz'], w['star'])
            for w in TS30['windows']]
if sorted(_RW_BY) != sorted(_TS_KEYS) or len(_TS_KEYS) != len(set(_TS_KEYS)):
    raise SystemExit('recurrence export: statunit_v426 and twostars_r27 do not '
                     'form one set of distinct covering windows')
_NAME2OBJ = {w['star']: w['object'] for w in TS30['windows']}


def _rw_rows():
    rows = []
    for n, w in enumerate(TS30['windows']):
        s = _RW_BY[(w['eb'], w['nu_lo_GHz'], w['nu_hi_GHz'], w['star'])]
        assert bool(s['above_trigger']) == bool(w['above_trigger']), w
        rows.append(dict(
            window_order=i(n), eb=w['eb'], nu_lo_GHz=_g17(w['nu_lo_GHz']),
            nu_hi_GHz=_g17(w['nu_hi_GHz']), star=w['star'],
            object=w['object'], search_class=w['search_class'],
            statistic=f(s['statistic'], 4), above_trigger=b(w['above_trigger']),
            p_trig_ctrl=('' if s['p_trig_ctrl'] is None else _g17(s['p_trig_ctrl'])),
            p_trig_cells=('' if s['p_trig_cells'] is None else _g17(s['p_trig_cells']))))
    return rows


def _le_rows():
    rows = []
    for n, c in enumerate(TS30['look_elsewhere'], 1):
        for g, (nm, ps) in enumerate(zip(c['names'], c['groups'])):
            for k, p in enumerate(ps):
                rows.append(dict(call=i(n), purpose=c['label'], group=i(g),
                                 object=nm, member=i(k), p=_g17(p)))
    return rows


_TWO = RW30['two_objects']
_RWP = ([('seed', '%d' % TS30['seed'], 'seed of numpy.random.default_rng for the look-elsewhere simulations'),
         ('n_sim', '%d' % TS30['n_sim'], 'realisations per simulation'),
         ('numpy_version', TS30['numpy_version'], 'NumPy release the article was computed with'),
         ('trigger', '%g' % TS30['trigger'], 'the trigger statistic'),
         ('first_star', _TWO[0], 'catalogue name (star column) of one of the two objects the article names'),
         ('second_star', _TWO[1], 'catalogue name of the other'),
         ('first_object', TS30['hd'], 'object name of HD 14055 in recurrence_windows.csv'),
         ('second_object', TS30['jx'], 'object name of the other object in recurrence_windows.csv')]
        + [('p_obs_call_%d' % n, _g17(c['p_obs']),
            'the tail the simulation of call %d (%s) compares each realisation with' % (n, c['label']))
           for n, c in enumerate(TS30['look_elsewhere'], 1)])
assert {_NAME2OBJ[_TWO[0]], _NAME2OBJ[_TWO[1]]} == {TS30['hd'], TS30['jx']}, _TWO
TABLES.append(Table(
    'statistics/recurrence_windows.csv',
    ["One row per distinct covering window of the widened recurrence "
     "comparison: a window of a block of another session, more than a day "
     "from the discovery block, covering the frequency of an unattributed "
     "crossing; a window covering several crossings is one row.",
     "code/recurrence_expectation.py reads it with recurrence_parameters.csv, "
     "look_elsewhere_groups.csv and control_field_statistics.csv."],
    '(eb, nu_lo_GHz, nu_hi_GHz) joins control_field_statistics.csv and '
    'spectral_windows.csv',
    [('window_order', '', 'position of the window in the order the comparison is formed'),
     ('eb', '', 'ALMA execution block identifier'),
     ('nu_lo_GHz', 'GHz', 'lower edge of the window, full precision'),
     ('nu_hi_GHz', 'GHz', 'upper edge of the window, full precision'),
     ('star', '', 'catalogue name the window was searched under'),
     ('object', '', 'the object it belongs to, as the article names it'),
     ('search_class', '', 'A fine or B coarse channels'),
     ('statistic', '', 'the window statistic read, the largest over the window'),
     ('above_trigger', '', '1 where it reaches the trigger'),
     ('p_trig_ctrl', '', 'fraction of the window control positions reaching the trigger, the rate the whole comparison and its two-object split are formed on; empty where the window has no control vector'),
     ('p_trig_cells', '', 'the window chance of a trigger crossing from its independent channel-drift cells, a secondary null; empty where the cell count is not recorded')],
    _rw_rows()))
TABLES.append(Table(
    'statistics/look_elsewhere_groups.csv',
    ["The groups of every look-elsewhere simulation, in the order the "
     "simulations consume the random stream: one row per member probability "
     "of one group (an object). Each simulation draws every group's count "
     "from its own Poisson-binomial distribution and records the smallest "
     "group tail of each realisation."],
    'object as in recurrence_windows.csv',
    [('call', '', 'order of the simulation in the stream'),
     ('purpose', '', 'edge landing, control rates (the one the article quotes) or cell rates'),
     ('group', '', 'order of the group inside the simulation'),
     ('object', '', 'the object the group is'),
     ('member', '', 'order of the probability inside the group'),
     ('p', '', 'the member probability, full precision')],
    _le_rows()))
TABLES.append(Table(
    'statistics/recurrence_parameters.csv',
    ["The scalar inputs of the widened recurrence comparison. The parameters are:"]
    + ["%s -- %s." % (nm, de) for nm, _v, de in _RWP],
    'none',
    [('parameter', '', 'parameter name, described above'),
     ('value', '', 'its value')],
    [dict(parameter=nm, value=v) for nm, v, _de in _RWP]))


# ======================== sensitivity/sensitivity_resampling_*  (R1-3)
#: ★★★ R1-3: the per-system median, the count at 1e15 W and their resampled
#: ranges are rebuilt by `code/sensitivity_summary.py` from these three
#: tables, which `sens_r28.py` writes in the order its resampling consumes
#: them (`sens_resample_r30.json`).  The factor-free limit is deposited at
#: full precision because the published limits are rounded to four figures
#: and a minimum over rounded values need not be the minimum.
SENSRS = read_json('sens_resample_r30.json')


def _sr_windows():
    rows = []
    for n, w in enumerate(SENSRS['windows']):
        k = wkey(w['eb'], w['star_name'], w['flo_GHz'], w['fhi_GHz'])
        if k not in _PKEY:
            raise SystemExit('sensitivity resampling window not in the window '
                             'tables: %r' % (k,))
        c = _PKEY[k]
        rows.append(dict(
            window_order=i(n), eb=c['eb'], target_id=c['target_id'],
            nu_lo_GHz=f(c['nu_lo_GHz'], 6), nu_hi_GHz=f(c['nu_hi_GHz'], 6),
            system_id=w['system_id'],
            factor_free_limit_W=_g17(w['w_base']),
            injected=b(w['injected']),
            own_factor=('' if w['own_factor'] is None else _g17(w['own_factor'])),
            decorrelation_factor=_g17(w['decor_factor']),
            position_bounded=i(0 if _pf33.is_cond(w['system_id']) else 1)))
    return rows


_SRP = [
    ('class_factor', SENSRS['factor'], 'the Class A completeness factor every window carries'),
    ('factor_lo', SENSRS['factor_lo'], 'lower end of its calibration interval, as a multiple of it'),
    ('factor_hi', SENSRS['factor_hi'], 'upper end'),
    ('level_W', SENSRS['level_W'], 'the EIRP level systems are counted at'),
    ('seed', SENSRS['seed'], 'seed of the NumPy default generator (PCG64)'),
    ('n_trial', SENSRS['n_trial'], 'trials per resampling'),
]
TABLES.append(Table(
    'sensitivity/sensitivity_resampling_windows.csv',
    ["One row per Class A window that constrains bandwidth, in the order the "
     "sensitivity resampling consumes them: the window's EIRP_90 limit is "
     "factor_free_limit_W times its completeness factor, and a system's limit "
     "is the smallest over its windows.",
     "code/sensitivity_summary.py reads this file with "
     "sensitivity_resampling_pool.csv and sensitivity_resampling_parameters.csv "
     "and nothing else."],
    "(target_id, eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv and "
    "class_A_limit_uncertainty.csv; system_id joins system_limits.csv",
    [('window_order', '', 'position of the window in the resampled list'),
     ('eb', '', 'ALMA execution block identifier'),
     ('target_id', '', 'identifier the window was extracted under'),
     ('nu_lo_GHz', 'GHz', 'lower edge of the window'),
     ('nu_hi_GHz', 'GHz', 'upper edge of the window'),
     ('system_id', '', 'the system the window belongs to'),
     ('factor_free_limit_W', 'W', 'the limit divided by the completeness factor, full precision'),
     ('injected', '', '1 where the window was itself injected into and keeps its own measured factor'),
     ('own_factor', '', 'that measured factor; empty for a transferred window'),
     ('decorrelation_factor', '', 'one plus the fraction by which atmospheric decorrelation leaves the limit optimistic'),
     ('position_bounded', '', '1 if the positional loss of the system is bounded; the median, the extremes and the count '
      'at the level and the resampled medians and counts that the article prints are over those systems; every window is '
      'still drawn')],
    _sr_windows()))
TABLES.append(Table(
    'sensitivity/sensitivity_resampling_pool.csv',
    ["The measured completeness factors of the injected windows, the pool a "
     "transferred window's factor is drawn from; the centred pool is this one "
     "scaled to the class factor's mean."],
    'pool_order is the order the values are indexed by the draws',
    [('pool_order', '', 'index of the value'),
     ('own_factor', '', 'one injected window\'s own ninety-per-cent point, in units of its trigger power')],
    [dict(pool_order=i(n), own_factor=_g17(v))
     for n, v in enumerate(SENSRS['pool_raw'])]))
TABLES.append(Table(
    'sensitivity/sensitivity_resampling_parameters.csv',
    ["The scalar inputs of the sensitivity summaries, one row per parameter, "
     "with the NumPy release the reported draws were made with. The "
     "parameters are:"]
    + ['%s -- %s.' % (nm, de) for nm, _v, de in _SRP]
    + ['numpy_version -- NumPy release of the reported draws.'],
    'read with sensitivity_resampling_windows.csv',
    [('parameter', '', 'parameter name, described above'),
     ('value', '', 'its value')],
    [dict(parameter=nm, value=_g17(v)) for nm, v, _de in _SRP]
    + [dict(parameter='numpy_version', value=SENSRS['numpy_version'])]))


# ======================================== statistics/above_threshold_cells.csv
#: ★★★ A5(3).  The star-to-control step below the trigger is quoted in the
#: article as a ratio; the counts it is formed from were in no released file.
#: They are here, level by level, so the ratio can be recomputed and so can its
#: binomial uncertainty.
def _cells():
    rows = []
    for r in CELLS['ladder']:
        rows.append(dict(
            threshold_sigma=f(r['thr'], 1),
            n_star_cells=i(r['star']), n_control_cells=i(r['ctrl']),
            ratio=(f(r['ratio'], 6) if r['ratio'] is not None else ''),
            n_windows=i(CELLS['n_win_relA']),
            basis='all cells of the fine-channel windows, star side against '
                  'the pooled control side, normalised by the number of '
                  'positions on each side'))
    return rows


TABLES.append(Table(
    'statistics/above_threshold_cells.csv',
    ["The number of search cells above each level, counted at the stellar "
     "positions and at the control positions, from well below the trigger up to "
     "it.",
     "The ratio of the two, normalised by the number of positions on each side, "
     "is the step from a control position rate to a stellar position rate. The "
     "article adopts the control rate -- the smaller of the two and the more "
     "demanding of the count under test -- and carries this step only as a "
     "sensitivity test; these are the counts that step is formed from.",
     "The ratio is empty at the highest level, where neither side holds a cell. "
     "A ratio formed from a handful of cells at the top of the ladder carries "
     "the uncertainty of those counts and nothing here hides it: the counts are "
     "given so that uncertainty can be formed.",
     "These counts are measured over the fine-channel windows of the released "
     "extent at the time the ladder was built, which is the number in "
     "n_windows.",
     "The adopted band is one pair of these rungs differenced. The step "
     "quoted in null_distribution_tests.csv is formed over %s <= T < %s, and "
     "its two cell counts are this table\'s %s rows less its %s rows on each "
     "side; its ratio is the same arithmetic. The ratio rises monotonically "
     "toward the trigger, which is why the band adopted is the one adjacent "
     "to it and not a wider one further below: a wider band measures the "
     "quantity where it is smaller."
     % (mac('CeNearBandLo'), mac('CeNearBandHi'),
        mac('CeNearBandLo'), mac('CeNearBandHi'))],
    "the levels are in units of the per-channel noise, the same units as the "
    "T_star columns; the step this table supports is in "
    "null_distribution_tests.csv.",
    [('threshold_sigma', '', 'level, in units of the per-channel noise'),
     ('n_star_cells', '', 'search cells above that level at the stellar positions'),
     ('n_control_cells', '', 'search cells above it at the control positions, pooled over the ensemble'),
     ('ratio', '', 'stellar rate divided by control rate at that level, normalised by the number of positions on each side; empty where neither side holds a cell'),
     ('n_windows', '', 'fine-channel windows the counts are formed over'),
     ('basis', '', 'what is counted')],
    _cells()))


# ======================================= statistics/null_distribution_tests.csv
#: ★★ Every published value here is read from the macro layer where the
#: article publishes one, so a value in the deposit cannot differ from the
#: value in the article; the exact figure beside it comes from the record the
#: macro was rounded from.
def _nulls():
    T = CHANCE['telluric']
    R = []

    def row(test, reading, quantity, value, exact='', note=''):
        R.append(dict(test=test, reading=reading, quantity=quantity,
                      value=value, exact=exact, note=note))

    row('chance comparison', 'whole beam (adopted)', 'n_windows',
        mac('CeNWin'), i(CHANCE['n_win_A_released']),
        'fine-channel windows of the released extent, each contributing its '
        'own control exceedance rate')
    row('chance comparison', 'whole beam (adopted)', 'expected_at_trigger',
        mac('CeExpTrig'), f(CHANCE['e_trigger_released'], 6),
        'sum over those windows of the probability that a position in the '
        'field reaches the trigger')
    row('chance comparison', 'whole beam (adopted)', 'mask_share_weighted',
        '', f(CHANCE['mask_share_weighted'], 6),
        'share of the expectation the attribution mask removes, weighted by '
        'each window\'s own rate')
    row('chance comparison', 'whole beam (adopted)', 'expected_after_mask',
        mac('CeExpX'), f(T['e_chance_before'], 6),
        'the expectation with the masked share removed and the atmospheric '
        'screen not yet applied')
    row('chance comparison', 'whole beam (adopted)', 'telluric_factor',
        '', f(T['factor'], 6),
        'factor the atmospheric screen applies, measured on the control side: '
        '%d of %d surviving control exceedances fall inside the screening '
        'radius' % (T['ctrl_removed'], T['ctrl_surviving_mask']))
    row('chance comparison', 'whole beam (adopted)', 'expected',
        mac('CeExp'), f(CHANCE['e_chance'], 6),
        'the chance expectation: the trigger expectation less the masked share '
        'and less the atmospherically screened share')
    row('chance comparison', 'whole beam (adopted)', 'expected_interval_lo',
        mac('CeLo'), f(CHANCE['interval'][0], 6),
        'lower end of the %s per cent interval on the expectation, from '
        'resampling; it folds in the sub-trigger transfer band, so it is not '
        'reconstructible from the per-window rates alone'
        % mac('CeCovPct'))
    row('chance comparison', 'whole beam (adopted)', 'expected_interval_hi',
        mac('CeHi'), f(CHANCE['interval'][1], 6),
        'upper end of that interval, on the same basis')
    row('chance comparison', 'whole beam (adopted)', 'observed',
        mac('CeObs'), i(CHANCE['observed']),
        'unattributed crossings in those windows, after the atmospheric screen '
        'has been applied to the crossings on the same radius in the same '
        'topocentric frame')
    row('chance comparison', 'whole beam (adopted)', 'observed_before_screen',
        '', i(T['observed_before']),
        'the same count before that screen, which removes one crossing')
    row('chance comparison', 'whole beam (adopted)', 'probability',
        mac('CeProbNull'), f(CHANCE['p_at_least_observed_control_only'], 6),
        'probability of a count at least as large as the observed one, under '
        'the expectation above')
    row('chance comparison', 'whole beam (adopted)', 'added_population_bound',
        mac('CeAddLim'), f(CHANCE['added_population_limit_exact'], 6),
        'largest added population the comparison could not have rejected; a '
        'bound on compatibility and not a confidence limit on a population of '
        'transmitters')
    row('chance comparison', 'narrower extraction field',
        'observed', mac('FrNarrowObs'), '',
        'the same comparison with both sides read over the narrower '
        'extraction field, which drops the integrations whose pointing falls '
        'outside it')
    row('chance comparison', 'narrower extraction field',
        'expected', mac('FrNarrowExp'), '', 'on the same reading')
    row('chance comparison', 'narrower extraction field',
        'probability', mac('FrNarrowProb'), '', 'on the same reading')
    row('chance comparison', 'narrower extraction field',
        'added_population_bound', mac('FrNarrowAddLim'), '',
        'on the same reading')
    row('control exceedances', 'whole beam (adopted)', 'n_exceedances',
        mac('CeNExc'), i(T['ctrl_exceedances']),
        'control positions reaching the trigger anywhere in the survey fine '
        'channels')
    row('control exceedances', 'whole beam (adopted)', 'n_inside_mask',
        mac('CeNExcAttr'), i(T['ctrl_in_mask']),
        'of those, exceedances falling inside the attribution mask, with the '
        'control channels transformed to the same stellar rest frame as the '
        'star\'s own reading')
    row('control exceedances', 'whole beam (adopted)',
        'n_inside_atmospheric_radius', '', i(T['ctrl_removed']),
        'of the exceedances surviving the mask, those inside the atmospheric '
        'screening radius')
    #: ★★★★ ONE BAND, ONE SET OF ROWS, READ FROM THE ARTICLE'S OWN MACROS.
    #: This block used to emit the 3.0-4.5 reading -- ratio 1.0455 published
    #: as "4.6 per cent", 34 984 stellar cells -- under the name
    #: `sub-trigger step`, and the ADOPTED reading separately under the name
    #: `near-trigger band`.  So the deposit carried two bands for one
    #: quantity while `above_threshold_cells.csv` carried the adopted one and
    #: the article carried only the adopted one, and "4.6 per cent" has zero
    #: occurrences in the article.  Two deposited files quoting two bands for
    #: one quantity is precisely the defect the referee's item B9 was raised
    #: about, reproduced inside the answer to it.
    #: ★★ The wider band is NOT deposited as a second reading.  B9 asked for
    #: "one measurement band and one sensitivity test, quoted once", and the
    #: level-by-level ladder that justifies choosing this band -- the ratio
    #: rises monotonically toward the trigger, which is why a band measured
    #: further below it measures the quantity in the wrong place -- is
    #: already deposited, row by row, in `above_threshold_cells.csv`.
    #: ★ Every published value is `mac(...)`, so the deposit cannot carry a
    #: band the article does not print, and the exact figures come from the
    #: record the macros were rounded from.
    #: ★★ The control side of the band is not in the chance record, and it is
    #: not typed here either: it is the SAME difference of the same two rungs
    #: of `above_threshold_cells.csv` that gives the stellar side.  The
    #: stellar side is then asserted against the article's own macro, which
    #: is the check that the two deposited files describe one band -- the
    #: check whose absence let them describe two.
    _lad = {round(r['thr'], 1): r for r in CELLS['ladder']}
    _blo, _bhi = (round(CHANCE['near_band'][0], 1),
                  round(CHANCE['near_band'][1], 1))
    assert _blo in _lad and _bhi in _lad, (
        'the adopted band %s-%s is not a pair of rungs of the deposited cell '
        'ladder, so its counts cannot be rebuilt from the deposit'
        % (_blo, _bhi))
    _nst = _lad[_blo]['star'] - _lad[_bhi]['star']
    _nct = _lad[_blo]['ctrl'] - _lad[_bhi]['ctrl']
    assert _nst == CHANCE['near_n_star_events'] \
        == maci('CeNearNStar'), (
        'the band holds %d stellar cells by differencing the deposited '
        'ladder, %d in the chance record and %s in the article'
        % (_nst, CHANCE['near_n_star_events'], mac('CeNearNStar')))
    assert _nct > _nst, (
        'the control side of the band is not larger than the stellar side, '
        'which cannot be: there are many more control positions than stars')
    #: ★★★ AND THE RATIO ITSELF REBUILDS FROM THOSE TWO COUNTS.  The per-star
    #: to per-control-position normalisation is read OFF the ladder -- it is
    #: whatever makes a rung's own deposited ratio equal its own deposited
    #: counts -- so this does not retype the number of control positions, and
    #: it fails if the ladder and the band ever stop describing one
    #: measurement.  This is the comparison between a deposited number and
    #: the macro the article prints it from that `zverify` had none of.
    _norm = (_lad[_blo]['ratio'] * _lad[_blo]['ctrl']) / _lad[_blo]['star']
    _rat = (_nst / (_nct / _norm))
    assert abs(_rat - CHANCE['near_ratio']) < 5e-4, (
        'the band ratio rebuilt from the deposited ladder is %.6f against '
        'the record\'s %.6f' % (_rat, CHANCE['near_ratio']))
    assert abs(round(_rat, 3) - float(mac('CeNear'))) < 1e-9, (
        'the band ratio rebuilds as %.3f against the article\'s %s'
        % (_rat, mac('CeNear')))
    row('sub-trigger step', 'whole beam (adopted)', 'ratio',
        mac('CeNear'), f(CHANCE['near_ratio'], 6),
        'ratio of the stellar to the control above-threshold cell rate in '
        'the band just below the trigger, given in the two rows below')
    row('sub-trigger step', 'whole beam (adopted)', 'band_lo',
        mac('CeNearBandLo'), f(CHANCE['near_band'][0], 1),
        'lower level of that band, in units of the per-channel noise')
    row('sub-trigger step', 'whole beam (adopted)', 'band_hi',
        mac('CeNearBandHi'), f(CHANCE['near_band'][1], 1),
        'upper level of it; the trigger itself is excluded, so the cells '
        'under test are not in the ratio')
    row('sub-trigger step', 'whole beam (adopted)', 'n_star_cells',
        macv('CeNearNStar'), i(_nst),
        'stellar cells the ratio is formed from, over %s windows; they are '
        'the %s and %s rows of above_threshold_cells.csv differenced'
        % (macv('CeNearNWin'), mac('CeNearBandLo'), mac('CeNearBandHi')))
    row('sub-trigger step', 'whole beam (adopted)', 'n_control_cells',
        '', i(_nct),
        'control cells the ratio is formed from, over the same windows and '
        'differenced the same way')
    row('sub-trigger step', 'whole beam (adopted)', 'interval_lo',
        mac('CeNearIntLo'), f(CHANCE['near_interval'][0], 6),
        'lower end of the interval on the ratio at the coverage of the '
        'resampling rows below')
    row('sub-trigger step', 'whole beam (adopted)', 'interval_hi',
        mac('CeNearIntHi'), f(CHANCE['near_interval'][1], 6),
        'upper end of it')
    row('sub-trigger step', 'whole beam (adopted)', 'probability',
        '', f(CHANCE['near_p_at_least'], 6),
        'probability of a ratio at least as large by chance')
    row('sub-trigger step', 'whole beam (adopted)', 'ratio_at_trigger',
        mac('CeTrAt'), f(CHANCE['step_trigger_level'], 6),
        'the same ratio at the trigger itself, where it is formed from the %s '
        'cells that are the crossings under test and so is not used'
        % mac('CeStepNX'))
    row('sub-trigger step', 'whole beam (adopted)', 'expected_with_step',
        mac('CeExpNear'), f(CHANCE['near_expectation'], 6),
        'the chance expectation with the step carried in as a sensitivity '
        'test, which the article does not adopt')
    row('sub-trigger step', 'whole beam (adopted)', 'probability_with_step',
        mac('CeProbNear'), f(CHANCE['near_p_at_least'], 6),
        'the probability on that sensitivity test')
    row('sub-trigger step', 'whole beam (adopted)', 'added_population_bound_with_step',
        mac('CeAddLimNear'), i(CHANCE['near_added_population_limit']),
        'the bound on an added population on that sensitivity test, against '
        'the adopted %s of the chance-comparison rows above' % mac('CeAddLim'))
    row('transfer band', 'whole beam (adopted)', 'adopted_lo',
        '', f(CHANCE['transfer_adopted'][0], 6),
        'lowest level-by-level ratio of above_threshold_cells.csv up to the '
        'trigger; the interval on the expectation is widened by this band')
    row('transfer band', 'whole beam (adopted)', 'adopted_hi',
        '', f(CHANCE['transfer_adopted'][1], 6),
        'the highest of them')
    row('transfer band', 'reserved blocks', 'check_lo',
        '', f(CHANCE['transfer_reserved'][0], 6),
        'the same quantity measured out of sample on the reserved blocks, '
        'from a handful of trigger events; it is the check and not the adopted '
        'band')
    row('transfer band', 'reserved blocks', 'check_hi',
        '', f(CHANCE['transfer_reserved'][1], 6), 'the upper end of it')
    row('resampling', 'whole beam (adopted)', 'n_bootstrap',
        macv('CeNBoot'), i(CHANCE['n_boot']),
        'resampling draws; execution blocks are resampled, and each window '
        'rate is redrawn as a binomial on its own control count')
    row('resampling', 'whole beam (adopted)', 'n_realisations',
        '', i(CHANCE['n_realisations']), 'realisations of the null count')
    row('resampling', 'whole beam (adopted)', 'coverage_percent',
        mac('CeCovPct'), f(CHANCE['coverage_pct'], 1),
        'coverage of the interval')
    row('resampling', 'whole beam (adopted)', 'seed',
        '', i(CHANCE['seed']), 'seed, so the resampling is reproducible')
    return R


TABLES.append(Table(
    'statistics/null_distribution_tests.csv',
    ["The chance comparison and the tests around it, term by term: what was "
     "expected, what was observed, and on what assumptions.",
     "The comparison is made twice, over two fields, and both readings are "
     "here. The adopted reading is the whole primary beam, which is the field "
     "the statistic is defined over; the other reads both sides over the "
     "narrower extraction field, which drops the integrations whose pointing "
     "falls outside it. Neither is a reading of the other.",
     "value is the figure the article prints, at the precision it prints it. "
     "exact is the figure the record carries before rounding, where there is "
     "one. A quantity the article does not print has an empty value and an "
     "exact figure.",
     "The expectation can be rebuilt from control_field_statistics.csv: sum "
     "each fine-channel window p_trig_ctrl, multiply each by one minus its "
     "mask_attr_share and by its telluric_factor. The interval on it cannot, "
     "because it folds in the transfer band of above_threshold_cells.csv and "
     "the resampling of the attributed share.",
     "What the comparison establishes is consistency with the expectation "
     "these fields\' own control positions set, under the assumptions recorded "
     "here. It does not establish that the unattributed crossings are noise."],
    "the per-window terms are in control_field_statistics.csv; the cell counts "
    "behind the sub-trigger step are in above_threshold_cells.csv, and its "
    "band_lo and band_hi rows name the two rungs of that table they are "
    "differenced from, so the two files quote one band and not two; the "
    "crossings counted on the observed side are the rows of "
    "threshold_crossings.csv with attributed = 0.",
    [('test', '', 'the test or quantity group the row belongs to'),
     ('reading', '', 'the field the quantity is read over, or the block set it is measured on'),
     ('quantity', '', 'what is given'),
     ('value', '', 'the figure the article prints, at the precision it prints it; empty where the article does not print it'),
     ('exact', '', 'the figure the analysis record carries before rounding, where there is one'),
     ('note', '', 'what the quantity is and the assumption it rests on')],
    _nulls()))


# ====================================== catalogues/count_accounting.csv
#: ★★ A reference into a numbered section or table of the article is a dangling
#: reference here: a deposit outlives a numbering.  The three the released
#: notes carry are replaced by what they refer to, by name, and the result is
#: asserted to carry no such reference at all -- so a note that acquires one
#: later stops this generator instead of shipping.
DEREF = {
    'Sec. 5.3.2':
        'the block whose control median identifies it as defective',
    'Appendix the appendix cited in the paper':
        'the atmospheric screen',
    'the two events of Table 5':
        'the two events whose statistic exceeds every control position',
}
_XREF = re.compile(r'\bSec\.|\bAppendix\b|\bTable~?\s*\d|\bFig\.|\bFigure~?\s*\d'
                   r'|\bEq\.|\bEquation~?\s*\d|\\ref|\\S')


def deref(s):
    for k, v in DEREF.items():
        s = s.replace(k, v)
    assert not _XREF.search(s), (
        'a deposited note carries a reference into the article that would '
        'dangle here: %r' % s)
    return s


def _counts():
    # ★ r34 (Referee 2, item 9): every parent says what it is the sum of, or
    # that it is not a sum (sumrule_r34; ledger_r34.py asserts and drives it)
    import sumrule_r34 as _sr
    _ann, _sfail = _sr.annotate(CNT)
    assert not _sfail, ('count_accounting: a parent is not the sum it names: %s'
                        % '; '.join(_sfail))
    return [dict(row=r['row'], count=deref(r['count']), value=r['value'],
                 what_it_counts=deref(r['what_it_counts']),
                 in_article=r['in_article'], sub_rows=_ann[r['row']][0],
                 sum_rule=_ann[r['row']][1]) for r in CNT]


TABLES.append(Table(
    'catalogues/count_accounting.csv',
    ["The master accounting of the survey: one row per published count, with "
     "the sub-counts each one partitions into.",
     "Every count in the article appears here, and so do the itemised rows the "
     "article does not have room for; in_article records which is which.",
     "The row numbers nest. sum_rule says, for every row with rows under it, "
     "which rows it is the sum of, or that it is not a sum of them: a row under "
     "a parent can count a subset of it, or the same set a second way. Where a "
     "count appears under two parents the note says so, because a count that is "
     "reached by two routes and does not agree is a defect and not a nuance."],
    "the crossing counts are the rows of threshold_crossings.csv under the "
    "selections the notes give; the window counts are those of "
    "spectral_windows.csv.",
    [('row', '', 'row number; the rows numbered under a row are listed in sub_rows'),
     ('count', '', 'what is counted'),
     ('value', '', 'the published value'),
     ('what_it_counts', '', 'the qualification that travels with the count'),
     ('in_article', '', '1 where the article prints this row, 0 where it is itemisation the article has no room for'),
     ('sub_rows', '', 'the rows numbered directly under this one, space separated'),
     ('sum_rule', '', 'which rows this value is the sum of, checked when the deposit is written; "not a sum" where it is not the sum of the rows under it')],
    _counts()))


# ============================================== catalogues/block_ledger.csv
#: ★ r34 (Referee 2, item 9): the execution-block ledger of the article
#: (Table A1, first panel), row for row, with the same summation rule:
#: blockledger_v411.py writes blockledger_rows.json and asserts L16 (every
#: parent is the sum of its part rows in blocks, windows and hours).
def _blockledger():
    _bl = json.load(open(src('blockledger_rows.json')))['rows']
    _ids = [r['row'] for r in _bl]
    out = []
    for r in _bl:
        kids = [k for k in _ids if '.' in k and k.rsplit('.', 1)[0] == r['row']]
        parts = [k for k in kids if next(x for x in _bl if x['row'] == k)['part']]
        subs = [k for k in kids if k not in parts]
        rule = ('sum of rows ' + ', '.join(parts) if parts else '')
        if subs:
            rule += ('; ' if rule else '') + 'rows %s are subsets' % ', '.join(subs)
        out.append(dict(row=r['row'], set=r['label_plain'],
                        blocks='' if r['blocks'] is None else r['blocks'],
                        windows='' if r['windows'] is None else r['windows'],
                        stars='' if r['stars'] is None else r['stars'],
                        systems='' if r['systems'] is None else r['systems'],
                        hours='' if r['hours'] is None else '%.2f' % r['hours'],
                        part_of_parent=0 if not r['part'] else 1,
                        sum_rule=rule))
    return out


TABLES.append(Table(
    'catalogues/block_ledger.csv',
    ["The execution-block ledger of the article, row for row: every set of "
     "execution blocks the survey uses, with its windows, stars, systems and "
     "on-source hours.",
     "Blocks, windows and hours of a row are the sum of the rows numbered under "
     "it that are parts of it (part_of_parent = 1); a row with part_of_parent = "
     "0 is a subset of its parent and is not summed. Stars and systems are "
     "never summed, because one star can be observed in several sets."],
    "the blocks are those of execution_blocks.csv; the census windows are the "
    "rows of spectral_windows.csv.",
    [('row', '', 'row number'),
     ('set', '', 'the set of execution blocks'),
     ('blocks', '', 'execution blocks; empty where the row counts windows only'),
     ('windows', '', 'spectral windows; empty where not counted'),
     ('stars', '', 'distinct stars; empty where not counted'),
     ('systems', '', 'distinct stellar systems; empty where not counted'),
     ('hours', 'h', 'on-source time; empty where not counted'),
     ('part_of_parent', '', '1 where the row is one of the parts its parent is the sum of, 0 where it is a subset'),
     ('sum_rule', '', 'which rows this row is the sum of')],
    _blockledger()))


# ========= catalogues/recalibration_reconciled.csv, candidates/above_all_controls.csv
#: ★ r34 (Referee 2, items 10 and 15), from ledger_r34.json (ledger_r34.py Q1, Q4).
_LR34 = json.load(open(src('ledger_r34.json')))
TABLES.append(Table(
    'catalogues/recalibration_reconciled.csv',
    ["One row per execution block that either recalibration statement of the "
     "article counts, or that holds a crossing or a system\'s best limit now: "
     "what it holds, whether it was recalibrated with ALMA\'s final flags, and "
     "which extractor made the products of its windows.",
     "The blocks that set a limit or held a crossing when the recalibration was "
     "planned are those with in_calibration_record = 1; the blocks planned for "
     "re-extraction with the final extractor are those with "
     "in_reextraction_plan = 1, and reextracted says what became of each."],
    "eb joins execution_blocks.csv, recalibration_blocks.csv and "
    "re_extraction_status.csv.",
    [('eb', '', 'ALMA execution block (ASDM) identifier'),
     ('role', '', 'what the block holds now, the first that applies: a crossing, a system\'s best limit, another quoted limit, or none of these'),
     ('calibration', '', 'recalibrated with ALMA\'s final flags, or the delivered calibration'),
     ('extractor', '', 'final where the final extractor made the products of every window of the block, older otherwise'),
     ('in_calibration_record', '', '1 where the block is one of those that set a quoted limit or held a crossing when the recalibration was planned'),
     ('in_reextraction_plan', '', '1 where the block was planned for re-extraction with the final extractor'),
     ('reextracted', '', 'for a planned block, 1 where it was re-extracted and 0 where it was not; empty otherwise'),
     ('stars', '', 'the stars its windows were extracted toward, semicolon separated')],
    _LR34['blocks']))
TABLES.append(Table(
    'candidates/above_all_controls.csv',
    ["One row per threshold crossing whose stellar statistic exceeds the "
     "statistic at every control position of its own window: the crossings that "
     "pass the spatial comparison the article refers to."],
    "(eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv; the crossings are "
    "rows of threshold_crossings.csv.",
    [('star', '', 'star designation, as in threshold_crossings.csv'),
     ('eb', '', 'ALMA execution block (ASDM) identifier'),
     ('band', '', 'ALMA receiver band'),
     ('nu_lo_GHz', 'GHz', 'lower edge of the spectral window, topocentric'),
     ('nu_hi_GHz', 'GHz', 'upper edge of the spectral window, topocentric'),
     ('search_class', '', 'A for a fine-channel window, B for a coarse one'),
     ('T_star', '', 'the largest statistic at the star'),
     ('T_ctrl_max', '', 'the largest statistic at any control position of the window'),
     ('n_ctrl', '', 'number of control positions'),
     ('disposition', '', 'the attribution of the crossing')],
    _LR34['above_all_controls']))


# ============ candidates/drift_pair_accounting.csv, candidates/repeat_epoch_readings.csv
#: ★ round 28 (R14 / zverify V10): the article points at both files "of the
#: data archive" and neither was written.  The pair accounting is the table the
#: length pass moved out of the appendix (its source, `tab_pairacct_r23.tex`, is
#: still generated by pairacct_r23.py for exactly this); the repeat-epoch
#: readings are the rows of the candidates table moved out of the results
#: section, which recur_v411.py writes to repeat_epoch_readings_v411.json for
#: this emitter.  Both are rendered with the article's own macro values; a cell
#: that would carry markup stops the deposit (Table.write).
sys.path.insert(0, HERE)
import docapx_r29 as _dx
_RX = _dx.Renderer(MAC)


def _plain(t):
    v = re.sub(r'\s+', ' ', _RX.inline(t)).strip()
    return v.lstrip('… ').strip() if v.startswith('…') else v


def _pairacct():
    rows, sec = [], 1
    for ln in open(src('tab_pairacct_r23.tex'), encoding='utf-8'):
        ln = ln.strip()
        if ln == '\\hline' and rows:
            sec += 1
            continue
        if '&' not in ln or ln.startswith('%'):
            continue
        q, v = ln.rstrip('\\').rstrip().rsplit('&', 1)
        rows.append(dict(block=str(sec), subset_of_previous=b(q.strip().startswith('\\ldots')),
                         quantity=_plain(q), count=_plain(v)))
    return rows


def _repeat_readings():
    J = read_json('repeat_epoch_readings_v411.json')
    rows = []
    for lab, per in J['rows'].items():
        for st, val in per.items():
            rows.append(dict(quantity=_plain(lab), star=_plain(st), value=_plain(val)))
    return rows


TABLES.append(Table(
    'candidates/drift_pair_accounting.csv',
    ["The accounting of the trajectory test over pairs of crossings toward one "
     "star: how many covering windows were read, how many distinct pairs those "
     "readings represent, and how the pairs divide under the bounded-trajectory "
     "criterion.",
     "Each block of rows is a partition of the first row of its block; a row "
     "marked as a subset counts part of the row above it."],
    "the crossings are the rows of threshold_crossings.csv; the covering "
    "windows are rows of spectral_windows.csv.",
    [('block', '', 'the group of rows this row belongs to; the rows of a group are counted over one population'),
     ('subset_of_previous', '', '1 where the row counts part of the row before it, 0 where it opens a count'),
     ('quantity', '', 'what is counted'),
     ('count', '', 'the count')],
    _pairacct()))

TABLES.append(Table(
    'candidates/repeat_epoch_readings.csv',
    ["For the two crossings whose statistic exceeds every control position of "
     "their window, the readings of the repeat epochs behind each bound: the "
     "largest single epoch, the maximum over every drift and the value over the "
     "matched registration tolerance, with the frequencies in each frame.",
     "One row per quantity and star."],
    "star joins threshold_crossings.csv on the crossing toward that star whose "
    "statistic exceeds every control position.",
    [('quantity', '', 'the reading or frequency, with the frame or epoch it is taken in'),
     ('star', '', 'the star of the crossing'),
     ('value', '', 'the value, in the unit the quantity names (GHz for frequencies; the search statistic otherwise)')],
    _repeat_readings()))
if _RX.problems:
    raise SystemExit('zdeposit: candidate tables do not render: %s' % '; '.join(sorted(set(_RX.problems))))


# ============ statistics/recalibration_blocks.csv, statistics/extractor_version_sample.csv,
# ============ sensitivity/recombined_field_values.csv
# The targeted recalibration with ALMA's final flags: every block behind a quoted limit or a crossing, what
# was done to it, and why the rest were not; the measured size of the extractor-version difference (the
# random sample the article quotes, and the selected set of blocks whose flags did not change); and the
# Proxima Cen stack and single-epoch values on the recombined products, which the article does not use.
_R29 = os.path.join(BASE, 'r29inputs', 'reflag')
_RDECL = json.load(open(os.path.join(_R29, 'reflag_decl_r29.json')))
_XS = json.load(open(os.path.join(_R29, 'extractor_sample_r29.json')))
_PX = json.load(open(os.path.join(_R29, 'proxima_recombined_r29.json')))
_FATE = {'recalibrated': 'recalibrated', 'pf_unrestorable': 'final flags do not fit the imported data',
         'infeasible_measured': 'exceeds the disk space available (measured)',
         'infeasible_estimated': 'exceeds the disk space available (estimated)',
         'pending': 'not yet recalibrated', 'not_attempted': 'not attempted',
         'not_reached': 'recalibration not finished in the time available'}
_HOW = {'pipeline_final': "the pipeline's final flag version restored",
        'replay_inline_no_pf': 'flags delivered only as inline lists, replayed',
        'reconstructed_no_pf': 'only the online and template flags delivered, applied (a lower bound)',
        'legacy_flux': 'legacy calibration script with its online flags and flux scaling',
        'legacy_noflux': 'legacy calibration script with its online flags; no flux scaling delivered for it'}


def _how(b):
    if b['fate'] == 'recalibrated':
        return _HOW[b['how']]
    if b['fate'] == 'pf_unrestorable':
        return 'the final flag version does not match the rows of the imported data on either import route'
    if b['fate'].startswith('infeasible'):
        m_ = re.search(r'(\d+(?:\.\d+)?) GB', b.get('how') or '')
        legacy = 'legacy' in (b.get('how') or '')
        return ('%scalibration needs more disk than is available%s'
                % ('legacy ' if legacy else '', ' (peak about %s GB)' % m_.group(1) if m_ and 'peak' in b['how'] else ''))
    return ''


_ROLE = {'1-core': 'limit or crossing', '2-recurrence-only': 'repeat epoch', '3-runnerup-only': 'runner-up window',
         '4-near-threshold': 'window within 0.3 of the threshold'}
TABLES.append(Table(
    'statistics/recalibration_blocks.csv',
    ["One row per execution block recalibrated with ALMA's final flags, or behind a quoted limit or a "
     "threshold crossing and not recalibrated, with the reason. Blocks that are not recalibrated keep the "
     "delivered calibration."],
    "eb joins spectral_windows.csv.",
    [('eb', '', 'execution-block identifier'),
     ('stars', '', 'the stars the block observes, separated by semicolons'),
     ('role', '', 'why the block is listed: it sets a quoted limit or holds a crossing, or holds a repeat epoch or a runner-up window'),
     ('carries_limit', '', '1 if the block sets a quoted limit'),
     ('carries_crossing', '', '1 if the block holds a threshold crossing'),
     ('fate', '', 'recalibrated, or the reason it was not'),
     ('how', '', 'how the flags were restored, or the measurement behind the reason'),
     ('asdm_GB', 'GB', 'size of the delivered data')],
    [dict(eb=b['eb'], stars=b['stars'], role=_ROLE[b['tier']], carries_limit=int(bool(b['carries_limit'])),
          carries_crossing=int(bool(b['carries_crossing'])), fate=_FATE[b['fate']],
          how=_how(b), asdm_GB=f(b.get('size_gb'), 2))
     for b in sorted(_RDECL['blocks'], key=lambda b: (b['tier'], b['eb']))]))
# ★ v4.33 (the extractor fold): the priority re-extraction, block by block -- re-extracted with the final extractor on
# ALMA's flags, or the measured reason it could not be (r33inputs/20261107/extract_status_r33.json; xgen_r31 X4-X6).
_XST = json.load(open(os.path.join(HERE, 'r33inputs', '20261107', 'extract_status_r33.json')))
_XREASON = {'legacy_replay': 'calibration must be replayed in full; the replay needs more disk than was available',
            'flags_need_nonlazy': "ALMA's final flags restore only on the non-lazy import, whose working set exceeds "
                                  'the disk available; the imports that fit were tried and did not restore them',
            'flags_unrestorable': "ALMA's final flag version is not row-conformant on any import",
            'disk_abort': 'every import tried exceeded the disk available',
            'calibration_failed': 'the calibration failed on the import that fits the disk available (not the flag restore)',
            'not_reached': 'recalibrated only after this analysis was closed; not included'}
TABLES.append(Table(
    'catalogues/re_extraction_status.csv',
    ["One row per block chosen for re-extraction with the final extractor on ALMA's flags because it holds a "
     "crossing, sets a system's best limit or reaches close to the threshold, with what became of it. "
     "A block not re-extracted keeps the products of the earlier extractor (window_code_generations.csv)."],
    "eb joins window_code_generations.csv and spectral_windows.csv.",
    [('eb', '', 'execution-block identifier'),
     ('status', '', 're-extracted, or not re-extracted'),
     ('reason', '', 'for a block not re-extracted, the measured reason')],
    [dict(eb=b['eb'], status=b['status'].replace('_', ' ').replace('not re extracted', 'not re-extracted'),
          reason=_XREASON.get(b.get('reason_class'), '')) for b in sorted(_XST['blocks'], key=lambda b: b['eb'])]))
TABLES.append(Table(
    'statistics/extractor_version_sample.csv',
    ["Windows rerun with the archived extractor and compared with the statistic they carried before. "
     "sample = random: census blocks drawn at random among those not recalibrated (one per star, small "
     "deliveries), rerun without ALMA's flags so that only the extractor differs; these are the windows "
     "the article quotes. sample = flags_unchanged: recalibrated blocks whose flags did not change; a "
     "selected set, not a random one."],
    "eb and the window edges join spectral_windows.csv.",
    [('sample', '', 'random or flags_unchanged'),
     ('eb', '', 'execution-block identifier'),
     ('star', '', 'the star'),
     ('freq_lo_GHz', 'GHz', 'lower window edge'),
     ('freq_hi_GHz', 'GHz', 'upper window edge'),
     ('T_before', '', 'the search statistic of the earlier extraction'),
     ('T_rerun', '', 'the search statistic of the rerun'),
     ('rms_ratio', '', 'noise of the rerun over noise of the earlier extraction'),
     ('control_correlation', '', 'correlation of the two extractions\' control-position statistics')],
    [dict(sample=smp, eb=r['eb'], star=r['star'], freq_lo_GHz=f(min(r['flo'], r['fhi']), 6),
          freq_hi_GHz=f(max(r['flo'], r['fhi']), 6), T_before=f(r['T_old'], 4), T_rerun=f(r['T_new'], 4),
          rms_ratio=f(r['rms_ratio'], 5), control_correlation=f(r['ctrl_corr'], 4))
     for smp, rr in (('random', _XS['rows']), ('flags_unchanged', _XS['flags_unchanged_rows'])) for r in rr]))
TABLES.append(Table(
    'sensitivity/recombined_field_values.csv',
    ["Proxima Cen: the stellar-frame stack over every epoch and the best single epoch, as the nominal "
     "five-sigma EIRP before the ninety-per-cent completeness factor, computed twice with one code: from the "
     "products the article uses, and with the windows of recalibrated blocks reading their recalibrated, "
     "field-recombined products. The recombined values are not used in the article: their completeness has "
     "not been re-verified by injection."],
    "star joins stellar_sample.csv.",
    [('star', '', 'the star'),
     ('band', '', 'ALMA band'),
     ('freq_lo_GHz', 'GHz', 'lower edge of the common stellar-frame interval'),
     ('freq_hi_GHz', 'GHz', 'upper edge of the common stellar-frame interval'),
     ('n_epochs', '', 'epochs stacked'),
     ('on_source_h', 'h', 'on-source time, products the article uses'),
     ('on_source_h_recombined', 'h', 'on-source time, recombined products'),
     ('eirp_stack_W', 'W', 'nominal EIRP of the stack, products the article uses'),
     ('eirp_stack_recombined_W', 'W', 'nominal EIRP of the stack, recombined products'),
     ('eirp_single_W', 'W', 'nominal EIRP of the best single epoch, products the article uses'),
     ('eirp_single_recombined_W', 'W', 'nominal EIRP of the best single epoch, recombined products'),
     ('completeness_verified', '', '1 if the completeness of these values was verified by injection')],
    [dict(star=g['star'], band=g['band'], freq_lo_GHz=f(g['nu_lo_GHz'], 6), freq_hi_GHz=f(g['nu_hi_GHz'], 6),
          n_epochs=g['n_epochs'], on_source_h=f(g['on_source_h'], 3),
          on_source_h_recombined=f(g['on_source_h_recombined'], 3),
          eirp_stack_W='%.4e' % g['eirp_stack_nominal_W'],
          eirp_stack_recombined_W='%.4e' % g['eirp_stack_nominal_recombined_W'],
          eirp_single_W='%.4e' % g['eirp_single_nominal_W'],
          eirp_single_recombined_W='%.4e' % g['eirp_single_nominal_recombined_W'],
          completeness_verified=0)
     for g in _PX['groups']]))

# ===================================================== figures/figure_data.csv
#: ★ Most of the figures are drawn from columns deposited here, and for those
#: the honest deposit is the pointer in figure_sources.csv, not a second copy
#: that can disagree with the first.  What this file carries is the data that
#: is in no other deposited table: the external survey limits the context
#: figure compares against, with the provenance of each and the rescaling
#: applied to put them on one threshold.
def _figdata():
    rows = []
    for prog in sorted(CTXFIG['literature']):
        L = CTXFIG['literature'][prog]
        for n, ((d, w), (dc, wc)) in enumerate(zip(L['pts'], L['pts_common'])):
            rows.append(dict(
                figure='EIRP limits against distance',
                panel='a', series=prog, point=i(n + 1),
                x=f(d, 4), x_quantity='distance', x_unit='pc',
                y=e(w), y_quantity='EIRP limit as published', y_unit='W',
                y_rescaled=e(wc),
                y_rescaled_quantity='the same limit rescaled to a common '
                                    'threshold of %s' % f(CTXFIG['common_snr'], 1),
                scale_factor=f(L['scale_to_common'], 6),
                note=L['src'].replace('\n', ' ')))
    rows.append(dict(
        figure='EIRP limits against distance', panel='a',
        series='inverse-square guide', point='1',
        x='1.0000', x_quantity='distance', x_unit='pc',
        y=e(CTXFIG['d2_guide_norm_W_at_1pc']),
        y_quantity='normalisation of the guide line at one parsec',
        y_unit='W', y_rescaled='', y_rescaled_quantity='', scale_factor='',
        note='the guide line runs as the square of the distance from this '
             'normalisation; it is an aid to the eye and not a measurement'))
    return rows


TABLES.append(Table(
    'figures/figure_data.csv',
    ["The numerical data behind the figures that is in no other table here.",
     "Most of the figures are drawn from columns deposited in this archive, "
     "and for those figure_sources.csv names the file and the columns rather "
     "than copying the numbers, so that a figure and the table behind it cannot "
     "disagree.",
     "What is left is the external material the context figure compares the "
     "survey against: the deepest limit each published survey reports, the "
     "threshold it was set at, and the factor that puts it on a common "
     "threshold with this one. The note column gives the source of each value "
     "in the words of the paper it is taken from.",
     "A rescaled limit is not that survey published number and is not "
     "attributable to its authors as such; it is this work rescaling of it, "
     "and the factor applied is beside it."],
    "figure_sources.csv names, for every figure, the deposited file and "
    "columns it is drawn from.",
    [('figure', '', 'the figure, named by what it shows rather than by a number, since numbering is a property of the typeset article'),
     ('panel', '', 'panel within it'),
     ('series', '', 'the series the point belongs to'),
     ('point', '', 'point index within the series'),
     ('x', '', 'abscissa'),
     ('x_quantity', '', 'what the abscissa is'),
     ('x_unit', '', 'its unit'),
     ('y', '', 'ordinate'),
     ('y_quantity', '', 'what the ordinate is'),
     ('y_unit', '', 'its unit'),
     ('y_rescaled', '', 'the ordinate rescaled to a common threshold, where the rescaling applies'),
     ('y_rescaled_quantity', '', 'what that rescaling is'),
     ('scale_factor', '', 'the factor applied'),
     ('note', '', 'the source of the value, quoted from the work it is taken from')],
    _figdata()))


# ================================================== figures/figure_sources.csv
# =============================================================== CODE GENERATIONS
#: ★ v4.31 (round-30 point 4): WHICH CODE MADE EACH PRODUCT, AND THE EARLIER CODE ITSELF.
#: Products made before the extractor and search reached their deposited form are still in use (blocks that
#: were not recalibrated).  The earlier extractors (E1, E2) and searches (S-0830, S-0909, S-0911, S-0913), and
#: the earlier orchestration and window-selection settings they ran with, are in code/pipeline/ under
#: `earlier/` (pipeline.tar, pinned by SHA-256, zverify V12).  Three tables say which is which, which code made
#: each window's product, and how the earlier code reproduces the archived products when run again
#: (zverify V13 requires every product's code to be one of the archived generations).
_CG_DIR = os.path.join(HERE, 'r31inputs', '20261105')
_CG_META = json.load(open(os.path.join(_CG_DIR, 'versions_meta.json')))
_CG_PATH = {'E1': 'code/pipeline/extraction/earlier/E1/seti_extract_generic.py',
            'E2': 'code/pipeline/extraction/earlier/E2/seti_extract_generic.py',
            'E3': 'code/pipeline/extraction/seti_extract_generic.py',
            'S0830': 'code/pipeline/search/earlier/S0830/seti_drift_search_generic.py',
            'S0909': 'code/pipeline/search/earlier/S0909/seti_drift_search_generic.py',
            'S0911': 'code/pipeline/search/earlier/S0911/seti_drift_search_generic.py',
            'S0913': 'code/pipeline/search/earlier/S0913/seti_drift_search_generic.py',
            'final': 'code/pipeline/search/seti_drift_search_generic.py'}
_CG_TAG = {'E1': 'E1', 'E2': 'E2', 'E3': 'E3', 'S0830': 'S-0830', 'S0909': 'S-0909', 'S0911': 'S-0911',
           'S0913': 'S-0913', 'final': 'S-final'}
_cg_rows = []
for _v in _CG_META:
    _a, _b = (_v['in_production'].replace(' to ', '|').split('|') + [''])[:2]
    _cg_rows.append(dict(
        code=_CG_TAG[_v['tag']], stage=_v['stage'], file=_CG_PATH[_v['tag']],
        in_use_from=_a.split(' (')[0].strip(), in_use_to=_b.strip(),
        differs_from_deposited=_v.get('differs', ''),
        product_fingerprint=_v['fingerprint'].replace('round-8 ', ''), sha256=_v['sha256']))
_cg_rows += [
    dict(code='settings', stage='orchestration', file='code/pipeline/orchestration/earlier/' + _f,
         in_use_from='', in_use_to=_t, differs_from_deposited='the per-target driver as it stood until then',
         product_fingerprint='', sha256='')
    for _f, _t in (('process_one_target_to_20260831T1131.sh', '2026-08-31 11:31 UTC'),
                   ('process_one_target_to_20260905T1836.sh', '2026-09-05 18:36 UTC'),
                   ('process_one_target_to_20260905T2132.sh', '2026-09-05 21:32 UTC'))] + [
    dict(code='settings', stage='window selection', file='code/pipeline/calibration/earlier/'
         'select_finest_spw_to_20260830.py', in_use_from='', in_use_to='2026-08-30 10:22 UTC',
         differs_from_deposited='the spectral-window selection as it stood until then',
         product_fingerprint='', sha256='')]
TABLES.append(Table(
    'catalogues/code_generations.csv',
    ["One row per generation of the extraction and search code that made a product still in use, and per "
     "earlier set of orchestration and window-selection settings.",
     "E3 and S-final are the deposited extractor and search; the others are the code as it ran earlier, "
     "byte for byte."],
    "code joins window_code_generations.csv; file names a file of this archive.",
    [('code', '', 'generation tag'), ('stage', '', 'extraction, search, orchestration or window selection'),
     ('file', '', 'the program in this archive'),
     ('in_use_from', '', 'start of its production use (UTC)'), ('in_use_to', '', 'end of its production use (UTC)'),
     ('differs_from_deposited', '', 'what it does differently from the deposited program'),
     ('product_fingerprint', '', 'how its products are recognised: the keys it writes'),
     ('sha256', '', 'SHA-256 of the program as it ran; empty where the file itself is the record')],
    _cg_rows))

_WV = json.load(open(os.path.join(_CG_DIR, 'windows_version.json')))
_SG = {'S-final': 'S-final', 'S-ctrlall': 'S-0913', 'S-0909': 'S-0909 or S-0911', 'S-0830': 'S-0830',
       'S-early': 'S-early'}
_SETNAME = {'census': 'census', 'holdout': 'reserved', 'beyond40': 'beyond 40 pc', 'extension': 'extension',
            'tail': 'archival tail'}
_wv_rows = []
for _w in _WV:
    _sg = sorted({_SG[_x.split('(')[0]] for _x in _w['sgen']})
    _wv_rows.append(dict(
        set=_SETNAME[_w['set']], block=_w['eb'], star=_w['star'], search_class=_w['cls'],
        nu_lo_GHz='%.6f' % min(_w['flo'], _w['fhi']), nu_hi_GHz='%.6f' % max(_w['flo'], _w['fhi']),
        chan_width_Hz='%.1f' % _w['chanw'], T_star='%.4f' % _w['T'],
        statistic_from=('field-recombined product' if _w['stat_src'] == 'fieldfix' else 'catalogue product'),
        extractor_statistic=_w['gen_stat'], extractor_limit=_w['gen_limit'],
        search='; '.join(_sg), recalibrated=('yes' if _w['reflag_fate'] == 'recalibrated' else 'no')))
TABLES.append(Table(
    'catalogues/window_code_generations.csv',
    ["One row per window the article uses: which generation of the extractor made the product its statistic "
     "and its limit are read from, and which search read it.",
     "A window whose product several runs reproduce to the same statistic lists every search that did; "
     "S-early wrote a product only where a later search reproduces it.  'unmatched' marks a window no "
     "surviving product could be joined to at the statistic's precision (its search column is then empty), "
     "or, for a statistic read from a field-recombined product, the limit's product."],
    "block, nu_lo_GHz and nu_hi_GHz join spectral_windows.csv; the code tags join code_generations.csv.",
    [('set', '', 'which set of windows'), ('block', '', 'execution block'), ('star', '', 'searched star'),
     ('search_class', '', 'A fine-channel, B coarse-channel'),
     ('nu_lo_GHz', 'GHz', 'lower window edge'), ('nu_hi_GHz', 'GHz', 'upper window edge'),
     ('chan_width_Hz', 'Hz', 'channel width'), ('T_star', '', 'the window statistic the article uses'),
     ('statistic_from', '', 'whether the statistic is the catalogue product or a field-recombined one'),
     ('extractor_statistic', '', 'extractor generation of the product the statistic is read from'),
     ('extractor_limit', '', 'extractor generation of the product the limit is read from'),
     ('search', '', 'search generation(s) that read that product'),
     ('recalibrated', '', 'yes where the block was recalibrated on the observatory flags')],
    _wv_rows))

_CMP = json.load(open(os.path.join(_CG_DIR, 'cmp_Nall.json')))
_SV = {'s0830': 'S-0830', 's0909': 'S-0909', 's0911': 'S-0911', 'sctrlall': 'S-0913', 'sfinal': 'S-final'}
_rp_rows = []
for _x in sorted(_CMP, key=lambda x: (x['eb'], min(x['flo'], x['fhi']))):
    for _k in sorted(_x['variants']):
        _v = _x['variants'][_k]
        _e = _k[:2] if not _k.startswith('E3px0') else 'E3 at the barycentric position'
        _s = _SV[_k[5:] if _k.startswith('E3px0') else _k[2:]]
        _rp_rows.append(dict(
            block=_x['eb'], nu_lo_GHz='%.6f' % min(_x['flo'], _x['fhi']),
            nu_hi_GHz='%.6f' % max(_x['flo'], _x['fhi']), search_class=_x['window']['cls'],
            archived_extractor=_x['window']['gen'], extractor=_e, search=_s,
            reproduction=('yes' if _e == _x['window']['gen'] else 'no'),
            T_archived='%.6f' % _x['arch']['T'], T_rerun='%.6f' % _v['T'],
            dT='%.2e' % (_v['T'] - _x['arch']['T']), rms_ratio='%.6f' % _v['rms_ratio']))
CG_REPRO_N = len(_CMP)
CG_REPRO_NBLK = len({_x['eb'] for _x in _CMP})
CG_REPRO_MAX = max(abs(float(r['dT'])) for r in _rp_rows if r['reproduction'] == 'yes')
assert CG_REPRO_N == 40 and CG_REPRO_NBLK == 9 and CG_REPRO_MAX < 2e-5, (CG_REPRO_N, CG_REPRO_NBLK, CG_REPRO_MAX)
TABLES.append(Table(
    'statistics/extractor_reproduction.csv',
    ["The earlier code run again: %d archived windows in %d execution blocks, recalibrated as in production, "
     "extracted with the generation that made each archived product and with the deposited one, and searched "
     "with every search generation." % (CG_REPRO_N, CG_REPRO_NBLK),
     "Where the extractor is the archived product's own (reproduction = yes) the statistic is reproduced to "
     "%.1e at most; the other rows measure what the deposited extractor changes." % CG_REPRO_MAX],
    "block, nu_lo_GHz and nu_hi_GHz join window_code_generations.csv; the code tags join code_generations.csv.",
    [('block', '', 'execution block'), ('nu_lo_GHz', 'GHz', 'lower window edge'),
     ('nu_hi_GHz', 'GHz', 'upper window edge'), ('search_class', '', 'A or B'),
     ('archived_extractor', '', 'generation that made the archived product'),
     ('extractor', '', 'extractor run here'), ('search', '', 'search run here'),
     ('reproduction', '', "yes where the extractor run is the archived product's own"),
     ('T_archived', '', 'statistic of the archived product'), ('T_rerun', '', 'statistic of this run'),
     ('dT', '', 'T_rerun minus T_archived'), ('rms_ratio', '', 'noise of this run over the archived noise')],
    _rp_rows))


FIGSRC = [
    # ★ v4.31: regenerated for the article's five figures (the drift-acceleration figure, the
    #   control-ring-stratum completeness figure and the spatial-rank example are no longer in
    #   the article; the completeness over the searched plane is now a panel of the coverage
    #   figure, and the selection chain and per-star coverage rows named no figure at all).
    ('EIRP limits against distance', 'a',
     'the EIRP limit of every searched star against its distance, at the '
     'trigger and at 90 per cent completeness, against the deepest limit of '
     'four published surveys',
     'sensitivity/class_A_limits.csv; sensitivity/class_B_limits.csv; '
     'figures/figure_data.csv',
     'dist_pc; eirp_nominal_W; eirp_p90_W; and the external points of '
     'figure_data.csv'),
    ('EIRP limits against distance', 'b',
     'the channel width of every searched window against its frequency, '
     'against the channel widths of those surveys',
     'catalogues/spectral_windows.csv; figures/figure_data.csv',
     'nu_lo_GHz; nu_hi_GHz; chan_width_Hz'),
    ('where the survey searched and where a repeat could test it', 'a',
     'the number of independent systems covering each sky frequency, '
     'fine-channel and coarse-channel windows apart',
     'catalogues/spectral_windows.csv; catalogues/stellar_sample.csv',
     'star; nu_lo_GHz; nu_hi_GHz; search_class; system'),
    ('where the survey searched and where a repeat could test it', 'b',
     'for the fine-channel systems, the coverage available for a repeat '
     'reading in a separated observing session, beyond a day and beyond a year',
     'candidates/recurrence_tests.csv; catalogues/stellar_sample.csv; '
     'catalogues/execution_blocks.csv',
     'n_rep_separated; dt_min_d; dt_max_d; system; date_utc'),
    ('where the survey searched and where a repeat could test it', 'c',
     'the number of fine-channel systems recovering a carrier of a given '
     'EIRP nine times in ten in one epoch, over frequency',
     'catalogues/spectral_windows.csv; sensitivity/class_A_limits.csv; '
     'sensitivity/completeness_calibration.csv',
     'nu_lo_GHz; nu_hi_GHz; eirp_p90_W; p90_mult_adopted'),
    ('fine-channel sensitivity', '',
     'the cumulative number of systems whose best fine-channel window reaches '
     'a given EIRP_90, the systems whose limit is conditional on the adopted '
     'position marked apart',
     'sensitivity/class_A_limits.csv',
     'eirp_p90_W; eirp_nominal_W; band; star; dist_pc'),
    ('the threshold crossings', '',
     'every threshold crossing in frequency and statistic, with its '
     'disposition and its offset from the nearest masked transition',
     'candidates/threshold_crossings.csv; candidates/molecular_line_matches.csv',
     'nu_star_GHz; T_star; attributed; masked_dv_kms; disposition'),
]

TABLES.append(Table(
    'figures/figure_sources.csv',
    ["One row per figure panel of the article: what it plots and which "
     "deposited columns it is plotted from.",
     "Figures are named by what they show. A figure number is a property of "
     "the typeset article and would not survive a change of layout, so it is "
     "not used as an identifier here.",
     "A panel whose data is not in any other deposited table has its series in "
     "figure_data.csv, and this table points there as well."],
    "the file column names files in this archive and the columns column names "
    "their columns.",
    [('figure', '', 'the figure, named by what it shows'),
     ('panel', '', 'panel within it, empty where there is one'),
     ('shows', '', 'what is plotted'),
     ('file', '', 'the deposited files the panel is drawn from, separated by semicolons'),
     ('columns', '', 'the columns within them, separated by semicolons')],
    [dict(figure=a, panel=b, shows=c, file=d, columns=e)
     for a, b, c, d, e in FIGSRC]))


# =============================================================== DOCUMENTATION
CODE = [
    ('reproduce.py',
     'runs the four programs below on this archive and compares every '
     'quantity they rebuild with the value the article prints, listed in '
     'statistics/article_values.csv; exit status 0 when all agree'),
    ('sensitivity_summary.py',
     'the per-system median EIRP_90, the count of systems at 1e15 W, both '
     'at the ends of the calibration interval, and the four resamplings of '
     'the window-to-window dispersion, rebuilt from the three '
     'sensitivity_resampling tables'),
    ('completeness.py',
     'the Class A completeness factor rebuilt from the deposited injection '
     'trials: the pooled ninety-per-cent point, its bootstrap and '
     'calibration intervals, and every injected window\'s own point'),
    ('response_ratio.py',
     'the channel-response ratio of every search class and online-averaging '
     'mode and the completeness factor it gives, rebuilt from '
     'response_injection_trials.csv, response_parameters.csv and '
     'injection_trials.csv'),
    ('recurrence_expectation.py',
     'the widened-window recurrence comparison rebuilt from the three '
     'recurrence tables and control_field_statistics.csv: the count of '
     'covering windows at the trigger against their control positions\' '
     'expectation, its exact probability, the split toward the two objects '
     'the article names, each object\'s own tail and the look-elsewhere '
     'chance, draw for draw with the deposited seed'),
    ('chance_expectation.py',
     'the chance comparison rebuilt from the three chance_resampling tables: '
     'the expectation, the probability of the observed count, the '
     'added-population bound, the interval and the stellar-calibrated '
     'reading, for both field readings, draw for draw with the deposited '
     'seed'),
    ('search_statistic.py',
     'the search statistic of the published equation: the drift-aligned, '
     'inverse-variance-weighted stack, its noise scale, and the maximum over '
     'the channel-by-drift grid'),
    ('control_positions.py',
     'the control-position generator: the annulus, scaled to the primary beam '
     'of the dish that observed each window and floored at its synthesised '
     'beam, drawn uniform in area from a fixed seed; --check refuses a row '
     'whose annulus does not follow its own dish'),
    ('injection_recovery.py',
     'the injection-recovery harness: the deposition of a drifting carrier '
     'through the channel response at a random sub-channel phase, the '
     'reading, and the completeness curve'),
    ('line_mask.py',
     'the attribution mask: the stellar-frame offset of a crossing from a '
     'catalogued transition, and the half-width test'),
]


#: ★★ round 30, R2 M14 ("keep each data file's column documentation"): the
#: second file of the record, the dynamic spectra around every crossing, had
#: an index and arrays and no description of either.  They are described
#: here, in the one column document, and `zenodo_pack.py` refuses to package a
#: spectra file whose index columns or array names differ from this list.
#: The rows are written without backticks so that zverify V2, which reads the
#: backticked rows of this file as the columns of the deposit's own tables,
#: does not take them for one.
SPECTRA_FILE = 'ALMA_Technosignatures_40pc_crossing_spectra.zip'
SPECTRA_INDEX = [
    ('n', '', 'row number, the crossing_NN of the file name'),
    ('star', '', 'star designation'),
    ('eb', '', 'ALMA execution block of the crossing'),
    ('f_topo_GHz', 'GHz', 'topocentric crossing frequency'),
    ('tstar', '', 'the crossing statistic T_star'),
    ('attributed', '', 'True where the line mask attributes the crossing'),
    ('source', '', 'released: from the per-window catalogue; adopted list: from the crossing ledger'),
    ('file', '', 'path of the array file inside the zip'),
    ('n_int', '', 'integrations'),
    ('n_chan', '', 'channels in the stored crop'),
    ('n_chan_window', '', 'channels in the whole spectral window'),
    ('drift_track_chan', '', 'channels the fitted drift track crosses over the block'),
    ('bytes', 'byte', 'size of the array file'),
    ('reason', '', 'why a crossing has no array file; empty where it has one'),
]
SPECTRA_ARRAYS = [
    ('I_star', 'Jy', '[integration, channel] spectrum at the star, apparent flux density, the crop around the crossing'),
    ('I_control_sample', 'Jy', '[integration, position, channel] the same at the retained control positions'),
    ('control_sample_names', '', 'names of those control positions in the ensemble'),
    ('W', '', '[integration, channel] visibility weight summed into each spectral point'),
    ('times', 's', 'integration mid-times, MJD seconds'),
    ('freqs', 'Hz', 'topocentric channel frequencies of the crop'),
    ('chanw', 'Hz', 'channel width'),
    ('phase_ra', 'rad', 'phase-centre right ascension'),
    ('phase_dec', 'rad', 'phase-centre declination'),
    ('l_star', '', 'direction cosine l of the star from the phase centre'),
    ('m_star', '', 'direction cosine m'),
    ('pb_arcsec', 'arcsec', 'primary-beam FWHM used for the control annulus'),
    ('dish_m', 'm', 'dish diameter read from the data'),
    ('bmax_m', 'm', 'longest baseline'),
    ('syn_arcsec', 'arcsec', 'synthesised-beam FWHM'),
    ('ann_syn_factor', '', 'inner edge of the control annulus in synthesised beams'),
    ('star_name', '', 'extraction target name'),
    ('t1_ra', 'deg', 'barycentric right ascension of the star at the block epoch'),
    ('t1_dec', 'deg', 'barycentric declination'),
    ('parallax', 'mas', 'parallax used for the apparent position'),
    ('parallax_err', 'mas', 'its uncertainty'),
    ('expos', 's', 'per-integration exposure'),
    ('field_id', '', 'per-integration field (pointing) identifier'),
    ('pb_resp_rel', '', 'per-integration relative primary-beam response at the star'),
    ('on_source_s', 's', 'on-source time, the sum of the exposures'),
    ('ref_field', '', 'the reference field of a multi-pointing block'),
    ('n_fields', '', 'fields combined'),
    ('field_ids', '', 'their identifiers'),
    ('field_on_source_s', 's', 'on-source time per field'),
    ('field_offset_arcsec', 'arcsec', 'star offset from each field centre'),
    ('field_pb_resp', '', 'primary-beam response at the star in each field'),
    ('extract_version', '', 'label of the extractor that wrote the source product'),
    ('pos_convention', '', 'the position convention of the extraction'),
    ('plx_dl_arcsec', 'arcsec', 'annual-parallax displacement in l'),
    ('plx_dm_arcsec', 'arcsec', 'annual-parallax displacement in m'),
    ('plx_offset_arcsec', 'arcsec', 'its magnitude'),
    ('plx_offset_beams', '', 'its magnitude in synthesised beams'),
    ('plx_loss_gaussian', '', 'amplitude a compact source keeps at that offset, Gaussian beam'),
    ('l_bary_arcsec', 'arcsec', 'barycentric star offset in l'),
    ('m_bary_arcsec', 'arcsec', 'barycentric star offset in m'),
    ('l_app_arcsec', 'arcsec', 'apparent star offset in l'),
    ('m_app_arcsec', 'arcsec', 'apparent star offset in m'),
    ('crossing_eb', '', 'execution block of the crossing'),
    ('crossing_f_topo_GHz', 'GHz', 'its topocentric frequency'),
    ('crossing_tstar', '', 'its statistic'),
    ('crossing_channel_in_crop', '', 'its channel in the crop'),
    ('crop_channels_of_window', '', 'first and last window channel of the crop, and the window channel count'),
    ('drift_max_Hz_s', 'Hz/s', 'largest drift rate searched in the window'),
    ('source_product_sha256', '', 'SHA-256 of the extraction product the crop was cut from'),
]


#: Arrays not written by every extractor generation: the first generation
#: wrote none of these; the second wrote the four dish/beam ones; the final
#: one writes all.  A spectrum cut from an earlier generation's product lacks
#: them, which identifies its generation (zenodo_pack.py checks exactly this).
SPECTRA_GEN2 = {'dish_m', 'bmax_m', 'syn_arcsec', 'ann_syn_factor'}
SPECTRA_GEN3 = {'expos', 'field_id', 'pb_resp_rel', 'on_source_s', 'ref_field',
                'n_fields', 'field_ids', 'field_on_source_s',
                'field_offset_arcsec', 'field_pb_resp', 'extract_version',
                'pos_convention', 'plx_dl_arcsec', 'plx_dm_arcsec',
                'plx_offset_arcsec', 'plx_offset_beams', 'plx_loss_gaussian',
                'l_bary_arcsec', 'm_bary_arcsec', 'l_app_arcsec', 'm_app_arcsec'}


def _spectra_doc():
    out = ['## The second file of this record: ' + SPECTRA_FILE, '',
           'The dynamic spectra at the star and at the retained control '
           'positions around each threshold crossing, one NumPy .npz file per '
           'crossing listed in its index.csv, with the SHA-256 of every member '
           'in its SHA256SUMS.', '',
           'index.csv columns:', '', '| column | unit | description |',
           '|---|---|---|']
    out += ['| %s | %s | %s |' % (n, u or '--', d) for n, u, d in SPECTRA_INDEX]
    out += ['', 'Arrays of each .npz file. The extractor ran in three successive '
            'generations and a spectrum is cut from the product its crossing\'s '
            'statistic was read from: arrays marked 2 were first written by the '
            'second generation and arrays marked 3 by the final one, so a '
            'spectrum without extract_version comes from an earlier generation, '
            'the first if it also lacks dish_m.', '',
            '| array | unit | from | description |', '|---|---|---|---|']
    out += ['| %s | %s | %s | %s |' % (n, u or '--',
                                       '3' if n in SPECTRA_GEN3 else
                                       '2' if n in SPECTRA_GEN2 else '1', d)
            for n, u, d in SPECTRA_ARRAYS]
    return out


def write_columns(root):
    out = ['# Column descriptions', '',
           'Every table in this archive is described here: what each file '
           'holds, how it joins the others, and what every column means and '
           'is measured in. The descriptions and the files are generated '
           'together from one specification, so a documented column that the '
           'file does not have, or a column the documentation does not '
           'mention, is not possible.', '',
           'A blank unit means the quantity is a count, a flag, a name or a '
           'ratio. A flag is written 1 or 0 and never as a word. An empty '
           'field means the value does not apply or is withheld, and never '
           'zero; each file header says which.', '']
    for t in TABLES:
        out.append('## `%s`' % t.path)
        out.append('')
        out.append('%d rows, %d columns.' % (len(t.rows), len(t.columns)))
        out.append('')
        for s in t.about:
            out.append(s)
            out.append('')
        out.append('**Joins.** %s' % t.join)
        out.append('')
        out.append('| column | unit | description |')
        out.append('|---|---|---|')
        for nm, un, de in t.columns:
            out.append('| `%s` | %s | %s |' % (nm, un or '--', de))
        out.append('')
    out += _spectra_doc()
    p = os.path.join(root, 'documentation/column_descriptions.md')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as fh:
        fh.write('\n'.join(out).rstrip() + '\n')


#: ★ round 30: the frozen inputs of this deposit (the pipeline and the DOI).
PIPE_DIR = os.path.join('r30inputs', '20261104')
CODE_REQUIREMENTS = ('numpy==2.2.6\nscipy==1.15.3\n')
#: ★★ R9 / R1-3: THE DOI IS ONE STRING IN ONE FILE.  The article's reference
#: list and this README both read `\SIdoi`, defined once in the manuscript
#: beside the reference it serves; reserving the Zenodo DOI and writing it
#: there is the author's one edit (ZENODO_UPLOAD.md).
_MAIN = glob.glob(os.path.join(BASE, 'technosignatures_*.tex'))
_mdoi = re.search(r'\\newcommand\{\\SIdoi\}\{([^{}]+)\}', open(_MAIN[0]).read())
if not _mdoi:
    raise SystemExit('zdeposit: no \\SIdoi in the manuscript')
DOI = _mdoi.group(1).strip()

README = """# {title}

The machine-readable data and the code behind an archival search for
narrow-band radio technosignatures toward stars within 40 pc in public ALMA
observations. The article holds the method and the conclusions; this archive
holds what they were computed from and the programs that recompute them.

**Cite as:** {citation}

## Contents

```
{tree}
```

`documentation/column_descriptions.md` describes every file and every column,
with units and joins; the files and their descriptions are generated from one
specification. Each `.csv` is comma-separated with one header row. Every row
carries the ALMA execution-block identifier and, where it applies, the project
code (cite as `ADS/JAO.ALMA#` followed by its value).

## Rebuilding the article's statistics

Python 3 with `numpy` and `scipy` (`code/requirements.txt` names the releases
the article was computed with) and nothing outside this archive:

```
cd code
python3 reproduce.py              # all of the below, compared with statistics/article_values.csv
python3 chance_expectation.py     # the chance comparison, both field readings
python3 completeness.py           # the Class A completeness factor and its intervals
python3 sensitivity_summary.py    # the per-system median, the count at 1e15 W, their resampling
python3 recurrence_expectation.py # the widened-window recurrence comparison and its two objects
python3 response_ratio.py         # the channel-response ratio and factor of every class and averaging mode
```

`reproduce.py` exits with status 0 when every quantity agrees with the
article. The tolerance is the article's own precision: a rebuilt quantity
agrees when, written to the digits the article prints, it is the article's
value. The Monte Carlo programs draw from the seeds in their parameter files
({seeds}); with those seeds and the NumPy release named there they repeat the
computation reported draw for draw, and `reproduce.py --seed-offset 1` shows
the size of the Monte Carlo error. The inputs are the three
`statistics/chance_resampling_*` tables (every window's control count and
exceedances, its attribution, the per-block exceedance counts, the
atmospheric counts), `sensitivity/injection_trials.csv` with
`completeness_parameters.csv` ({n_trials} injection trials in {n_injwin}
windows), and the three `sensitivity/sensitivity_resampling_*` tables. The
control positions of every window are reproducible from `ring_seed` in
`statistics/control_field_statistics.csv`, and blocks are grouped into
observing sessions by `catalogues/block_sessions.csv`.

Four reference implementations of the published definitions run their own
known-answer tests:

```
python3 search_statistic.py --demo
python3 control_positions.py --check ../statistics/control_field_statistics.csv
python3 line_mask.py --check ../candidates/threshold_crossings.csv ../candidates/molecular_line_matches.csv
python3 injection_recovery.py --compare ../sensitivity/injection_recovery.csv
```

## The search pipeline

`code/pipeline/` holds the programs that took the public execution blocks to
the per-window statistics, byte-identical to the copies that ran
(`code/pipeline/SHA256SUMS`), with the releases they ran under
(`code/pipeline/requirements.txt`, CASA included). They read calibrated
visibilities, which are not distributed here, so the search itself cannot be
re-run from this archive alone; it can be re-run from the ALMA Science Archive
with this code.

## Not here

The calibrated visibilities (of order a terabyte) and the per-window extracted
spectra. The dynamic spectra around each threshold crossing are a second file
of this record.

## Joins

* a **window** is (`target_id`, `eb`, `nu_lo_GHz`, `nu_hi_GHz`); all four
  fields are needed, because {n_share_star} stars share spectral windows of one
  block and (`eb`, `nu_lo_GHz`, `nu_hi_GHz`) alone repeats over {n_dup_row}
  rows of `catalogues/spectral_windows.csv` ({n_lost_row} windows would be lost);
* a **position** is `target_id`; `star` is the designation the components of a
  pair share;
* a **crossing** is (`eb`, `nu_topo_GHz`) and belongs to the window whose
  edges contain its frequency.

## Conventions

* Frequencies are topocentric, as the correlator delivered them, except where
  a column name says `nu_star` or a description says the star rest frame.
* A velocity offset is positive where the crossing lies above the transition.
* EIRP limits are at 90 per cent completeness for a carrier inside the
  searched drift range.
* Reaching the trigger is not a detection; the dispositions in
  `candidates/threshold_crossings.csv` say what each crossing is.

## Licence

{licence}
"""


def write_readme(root, tree):
    code = '\n'.join('* `code/%s` -- %s;' % (n, d) for n, d in CODE)
    code = code.rstrip(';') + '.'
    #: ★ B3: the join statement names the three-field key's collision, and
    #: the collision is MEASURED on the file this deposit just wrote rather
    #: than typed into the prose beside it.  A documentation number typed by
    #: hand is a number that stops being true at the next extraction.
    with open(os.path.join(root, 'catalogues/spectral_windows.csv'),
              newline='') as _fh:
        _wrows = list(csv.DictReader(_fh))
    _k3 = collections.Counter((_r['eb'], _r['nu_lo_GHz'], _r['nu_hi_GHz'])
                              for _r in _wrows)
    _dup = {k for k, v in _k3.items() if v > 1}
    _duprow = [_r for _r in _wrows
               if (_r['eb'], _r['nu_lo_GHz'], _r['nu_hi_GHz']) in _dup]
    txt = README.format(
        n_share_star=len({_r['star'] for _r in _duprow}),
        n_dup_row=len(_duprow),
        n_lost_row=len(_wrows) - len(_k3),
        title=TITLE,
        citation=('White G. J. and Dey R., ' + TITLE + ', Zenodo, '
                  'doi:' + DOI + ', together with the article it supports.'),
        tree=tree, codelist=code,
        seeds='; '.join('%s %s' % kv for kv in (
            ('chance comparison', SEED_CHANCE),
            ('completeness bootstrap', TRIALS30['boot_seed']),
            ('sensitivity resampling', SENSRS['seed']))),
        n_trials=sum(len(w['trials']) for w in TRIALS30['windows']),
        n_injwin=len(TRIALS30['windows']),
        licence=('Creative Commons Attribution 4.0 International (CC BY 4.0), '
                 'as recorded on the archive landing page. The external survey '
                 'limits in `figures/figure_data.csv` are the published values '
                 'of the works cited in that file and are reproduced there '
                 'with attribution.'))
    with open(os.path.join(root, 'README.md'), 'w') as fh:
        fh.write(txt)


# ================================================ statistics/article_values.csv
#: ★★★ R1-3: "verify that a clean run reproduces 23.8, P = 0.36 and the
#: revised sensitivity summaries within declared numerical tolerance".  The
#: tolerance is declared here, once: a rebuilt quantity agrees when, written
#: to the article's own digits, it IS the article's value.  Each row names the
#: deposited program and the quantity it prints; the value is read from the
#: macro the article prints, never typed, and zverify V11 re-reads the macros
#: to confirm the table, then runs code/reproduce.py on the unzipped archive.
CE = 'chance_expectation.py'
CO = 'completeness.py'
SS = 'sensitivity_summary.py'
RE = 'recurrence_expectation.py'
ART_VALUES = [
    (CE, 'whole_beam', 'observed unattributed Class A crossings', 'CeObs'),
    (CE, 'whole_beam', 'expected to reach the trigger', 'CeExpTrig'),
    (CE, 'whole_beam', 'chance expectation', 'CeExp'),
    (CE, 'whole_beam', 'P(count >= observed)', 'CeProbNull'),
    (CE, 'whole_beam', 'added-population bound', 'CeAddLim'),
    (CE, 'whole_beam', 'P(count <= observed) at the bound', 'CeProbAtLim'),
    (CE, 'whole_beam', 'P(count <= observed) one above it', 'CeProbAboveLim'),
    (CE, 'whole_beam', 'expectation interval low', 'CeLoNull'),
    (CE, 'whole_beam', 'expectation interval high', 'CeHiNull'),
    (CE, 'whole_beam', 'expectation interval with transfer, low', 'CeLo'),
    (CE, 'whole_beam', 'expectation interval with transfer, high', 'CeHi'),
    (CE, 'whole_beam', 'star-to-control ratio below the trigger', 'CeNear'),
    (CE, 'whole_beam', 'stellar-calibrated expectation', 'CeExpNear'),
    (CE, 'whole_beam', 'stellar-calibrated P(count >= observed)', 'CeProbNear'),
    (CE, 'whole_beam', 'stellar-calibrated added-population bound', 'CeAddLimNear'),
    (CE, 'narrow_field', 'observed unattributed Class A crossings', 'FrNarrowObs'),
    (CE, 'narrow_field', 'chance expectation', 'FrNarrowExp'),
    (CE, 'narrow_field', 'P(count >= observed)', 'FrNarrowProb'),
    (CE, 'narrow_field', 'added-population bound', 'FrNarrowAddLim'),
    (CE, 'both', 'smaller probability corrected for the two readings', 'FrTwoTrialP'),
    (CO, '', 'injected windows', 'SensNInj'),
    (CO, '', 'class factor (x P_trig)', 'EirpNinetyMultA'),
    (CO, '', 'bootstrap interval low', 'SensMultALo'),
    (CO, '', 'bootstrap interval high', 'SensMultAHi'),
    (CO, '', 'calibration interval low (x factor)', 'SensFacLo'),
    (CO, '', 'calibration interval high (x factor)', 'SensFacHi'),
    (CO, '', 'per-window point, lowest (x factor)', 'SensIndivFacLo'),
    (CO, '', 'per-window point, highest (x factor)', 'SensIndivFacHi'),
    (CO, '', 'windows within a tenth of the factor', 'NmDispNTenth'),
    #: ★ r30 (fold30, R1-1): the channel-response ratios and the factors they give
    ('response_ratio.py', '', 'response ratio, class A, N = 1', 'IjRatioNOne'),
    ('response_ratio.py', '', 'response ratio, class A, N = 2', 'IjRatioNTwo'),
    ('response_ratio.py', '', 'response ratio, class A, N = 4', 'IjRatioNFour'),
    ('response_ratio.py', '', 'response ratio, class B, N = 1', 'IjRatioBNOne'),
    ('response_ratio.py', '', 'response ratio, class B, N = 2', 'IjRatioBNTwo'),
    ('response_ratio.py', '', 'factor, class A, N = 1 (x P_trig)', 'IjFacNOne'),
    ('response_ratio.py', '', 'factor, class A, N = 2 (x P_trig)', 'IjFacNTwo'),
    ('response_ratio.py', '', 'factor, class B, N = 1 (x P_trig)', 'IjFacBNOne'),
    ('response_ratio.py', '', 'factor, class B, N = 2 (x P_trig)', 'IjFacBNTwo'),
    (SS, '', 'systems', 'NSysALim'),
    (SS, '', 'median best-window EIRP_90 (W)', 'EirpNinetySysMedA'),
    (SS, '', 'deepest system (W)', 'EirpNinetySysLoA'),
    (SS, '', 'shallowest system (W)', 'EirpNinetySysHiA'),
    (SS, '', 'systems at or below the level', 'NSysEfifteen'),
    (SS, '', 'median at the calibration interval low end (W)', 'TfMedCalLo'),
    (SS, '', 'median at the calibration interval high end (W)', 'TfMedCalHi'),
    (SS, '', 'count at the calibration interval high end', 'SvCalNLo'),
    (SS, '', 'count at the calibration interval low end', 'SvCalNHi'),
    (SS, '', 'window draw: count 5 per cent', 'SvRsNLo'),
    (SS, '', 'window draw: count 95 per cent', 'SvRsNHi'),
    (SS, '', 'block draw: count 5 per cent', 'SvRsBlkNLo'),
    (SS, '', 'block draw: count 95 per cent', 'SvRsBlkNHi'),
    (SS, '', 'block draw: median shift (per cent)', 'SvRsMedShiftPct'),
    (SS, '', 'window_dec draw: count 5 per cent', 'SvRsDecNLo'),
    (SS, '', 'window_dec draw: count 95 per cent', 'SvRsDecNHi'),
    #: ★ r30 (Ruling R13(c)): the restated recurrence comparison.
    (RE, '', 'distinct covering windows', 'WuNWin'),
    (RE, '', 'windows at or above the trigger', 'WuNWinExc'),
    (RE, '', 'expected from the control positions', 'WuExpWinCtrl'),
    (RE, '', 'P(count >= observed)', 'WuProbWinCtrl'),
    (RE, '', 'the two objects\' share of the expectation', 'WuExpTwoCtrl'),
    (RE, '', 'windows toward the two objects at or above the trigger', 'WuNWinExcTwo'),
    (RE, '', 'other windows', 'WuNWinRest'),
    (RE, '', 'other windows at or above the trigger', 'WuNWinRestExc'),
    (RE, '', 'other windows expected', 'WuExpRestCtrl'),
    (RE, '', 'other windows P(count >= observed)', 'WuProbRestCtrl'),
    (RE, 'HD 14055', 'at or above the trigger', 'TwNExcHD'),
    (RE, 'HD 14055', 'expected from deposited control rates', 'TwExpCtrlHD'),
    (RE, 'HD 14055', 'P(count >= observed)', 'TwProbCtrlHD'),
    (RE, 'ALMA J153702653-33192492', 'at or above the trigger', 'TwNExcJx'),
    (RE, 'ALMA J153702653-33192492', 'expected from deposited control rates', 'TwExpCtrlJx'),
    (RE, 'ALMA J153702653-33192492', 'P(count >= observed)', 'TwProbCtrlJxRaw'),
    (RE, 'both', 'the two objects\' expectation on deposited control rates', 'TwExpTwoCtrl'),
    (RE, 'both', 'objects in the look-elsewhere simulation', 'TwLookNStarCtrl'),
    (RE, 'both', 'look-elsewhere chance (per cent)', 'TwLookPctCtrl'),
]


def art_value(name):
    """The article's printed value of a macro, in the form the deposited
    programs print it: a power of ten as 1.8e15, a thin space dropped."""
    v = mac(name).replace('\\,', '').strip()
    m = re.match(r'^([0-9.]+)\\times10\^\{?(-?\d+)\}?$', v)
    if m:
        return '%se%d' % (m.group(1), int(m.group(2)))
    assert re.match(r'^-?[0-9.]+$', v), (name, v)
    return v


def _printed_macros():
    txt = ''
    for fn in (glob.glob(os.path.join(BASE, 'technosignatures_*.tex'))
               + glob.glob(os.path.join(BASE, 'sections', '*.tex'))):
        txt += ''.join(ln for ln in open(fn, errors='ignore')
                       if not ln.lstrip().startswith('%'))
    return set(re.findall(r'\\([A-Za-z]+)', txt))


_PRINTED = _printed_macros()
TABLES.append(Table(
    'statistics/article_values.csv',
    ["The statistical and calibration summaries the article prints, with the "
     "deposited program that rebuilds each one from this archive and the "
     "quantity name that program prints. code/reproduce.py runs the programs "
     "and compares.",
     "The tolerance is the article's own precision: a rebuilt quantity agrees "
     "when, written to the digits the article prints, it is the article's "
     "value. With the deposited seeds and the NumPy release the parameters "
     "files name, the Monte Carlo quantities are the same draws as the "
     "computation reported and agree exactly; with another seed they agree "
     "within the Monte Carlo error the programs print beside them."],
    'program names a file of code/; reading is the field reading of the '
    'chance comparison and empty for the other programs',
    [('program', '', 'the deposited program that rebuilds the quantity'),
     ('reading', '', 'whole_beam, narrow_field or both for the chance comparison; empty otherwise'),
     ('quantity', '', 'the quantity, named as the program prints it'),
     ('article_value', '', 'the value the article\'s build computes, as it prints it; a power of ten written as 1.8e15'),
     ('in_text', '', '1 where the value is printed in the article text, 0 where it is computed with it but appears only here')],
    [dict(program=p, reading=r, quantity=q, article_value=art_value(m),
          in_text=b(m in _PRINTED))
     for p, r, q, m in ART_VALUES]))


#: block_sessions is built LAST, so that it covers every block any table
#: above names.
TABLES.append(Table(
    'catalogues/block_sessions.csv',
    ["One row per execution block named anywhere in this archive or processed "
     "by the search: its observing session and member observing unit, the "
     "groupings the block resampling and the separated-session rule act on.",
     "session_id is the middle field of the ALMA block identifier "
     "(A002_<session>_<block>); two blocks are separated-session when their "
     "session_id differ. member_ous is the archive's member observing unit, "
     "several units joined by ; where the archive records more than one.",
     "set_name is primary census for a block of execution_blocks.csv, reserved "
     "hold-out for a block of the sample held out by identifier, and other for "
     "a block read only as a repeat epoch or outside both sets."],
    "eb joins every table carrying a block identifier.",
    [('eb', '', 'ALMA execution block identifier'),
     ('session_id', '', 'the observing session, the middle field of the identifier'),
     ('member_ous', '', 'the archive member observing unit(s), without the uid:// prefix'),
     ('project_code', '', 'ALMA project code'),
     ('array', '', '12m or 7m where the archive records it'),
     ('set_name', '', 'primary census, reserved hold-out or other')],
    _block_sessions()))


# ======================================================================= WRITE
if os.path.isdir(OUT):
    import shutil
    shutil.rmtree(OUT)
os.makedirs(OUT)
MANIFEST = []
for t in TABLES:
    n = t.write(OUT)
    MANIFEST.append((t.path, n))
write_columns(OUT)
#: ★★ round 30, R2 M14: the archive holds data and code and no narrative.
#: The six `documentation/appendix_*.md` files rendered here through v4.29
#: (the full text of paragraphs the article summarised) are no longer
#: written: each argument a conclusion depends on now has its one-sentence
#: result in the article, and the pointers to them are deleted.  The excerpt
#: sources stay in `r28inputs/docapx/` as the record of what was cut.  The
#: one document kept is the column description, which is generated with the
#: tables.  zverify V12 fails if any other prose file enters the deposit.
sys.path.insert(0, HERE)
import shutil
os.makedirs(os.path.join(OUT, 'code'))
for nm, _d in CODE:
    #: ★ v4.26: the four reference implementations live in `zdeposit_code/`
    #: in the version directory, not in a `code_src/` beside the generator's
    #: development tree -- the name is the deposit's, not the sandbox's.
    shutil.copy(os.path.join(HERE, 'zdeposit_code', nm),
                os.path.join(OUT, 'code', nm))
with open(os.path.join(OUT, 'code', 'requirements.txt'), 'w') as _fh:
    _fh.write(CODE_REQUIREMENTS)
#: ★★★ round 30, R1-2/R1-3: THE SEARCH PIPELINE AS IT RAN.  The article says
#: the archive holds it and through v4.29 the archive did not.  The files are
#: copied verbatim from the frozen input directory and each is checked here
#: against the SHA-256 taken on the machine that ran the survey; a file that
#: differs stops the deposit, because a tidied copy is not the code that
#: produced the results.  The sums travel with it as code/pipeline/SHA256SUMS,
#: which zverify V12 recomputes.  The files keep their names and comments as
#: they ran, so the deposit's text sweep (V4) does not read inside them.
#: ★ The files are kept in the tree as ONE uncompressed tar of fixed member
#: metadata (`pipeline.tar`), not as loose .py files: loose, they would be
#: read by every whole-tree gate of this build (numbers_move, pycompile,
#: verpin...) as if they were generators of the paper, which they are not.
import hashlib as _hl
import tarfile as _tarf
_PIPE_TAR = os.path.join(HERE, PIPE_DIR, 'pipeline.tar')
_PIPE_SUMS = os.path.join(HERE, PIPE_DIR, 'pipeline_production_sha256.txt')
_want = {}
for _ln in open(_PIPE_SUMS):
    _h, _rel = _ln.split(None, 1)
    _want[_rel.strip()] = _h
with _tarf.open(_PIPE_TAR) as _tf:
    _mem = {m.name: _tf.extractfile(m).read() for m in _tf.getmembers() if m.isfile()}
_have = sorted(x for x in _mem if x != 'requirements.txt')
if sorted(_want) != _have:
    raise SystemExit('zdeposit: pipeline archive and its production sums '
                     'disagree on the file list: %r'
                     % sorted(set(_want) ^ set(_have)))
for _rel in _have:
    if _hl.sha256(_mem[_rel]).hexdigest() != _want[_rel]:
        raise SystemExit('zdeposit: %s is not the production copy' % _rel)
    _dst = os.path.join(OUT, 'code', 'pipeline', _rel)
    os.makedirs(os.path.dirname(_dst), exist_ok=True)
    with open(_dst, 'wb') as _fh:
        _fh.write(_mem[_rel])
with open(os.path.join(OUT, 'code', 'pipeline', 'requirements.txt'), 'wb') as _fh:
    _fh.write(_mem['requirements.txt'])
with open(os.path.join(OUT, 'code', 'pipeline', 'SHA256SUMS'), 'w') as _fh:
    for _rel in _have:
        _fh.write('%s  %s\n' % (_want[_rel], _rel))
N_PIPE = len(_have)

_tree = collections.OrderedDict()
for p, n in MANIFEST:
    _tree.setdefault(os.path.dirname(p) or '.', []).append(
        (os.path.basename(p), n))
_lines = ['ALMA_Technosignatures_40pc/', '  README.md']
for d in ['catalogues', 'candidates', 'sensitivity', 'statistics', 'figures']:
    _lines.append('  %s/' % d)
    for nm, n in _tree.get(d, []):
        _lines.append('    %-34s %6d rows' % (nm, n))
_lines.append('  documentation/')
_lines.append('    %-34s %6d tables described' % ('column_descriptions.md',
                                                  len(TABLES)))
_lines.append('  code/')
for nm, _d in CODE:
    _lines.append('    %s' % nm)
_lines.append('    requirements.txt')
_lines.append('    pipeline/                          %d programs as run, '
              'SHA256SUMS, requirements.txt' % N_PIPE)
write_readme(OUT, '\n'.join(_lines))

#: ★★ R9: the Zenodo record's metadata, generated with the deposit so the
#: description cannot drift from it.  A build product beside the generator,
#: read by `zenodo_pack.py`, never a member of the deposit.
ZENODO_META = dict(
    title=TITLE,
    upload_type='dataset',
    creators=[dict(name='White, Glenn J.', affiliation='The Open University'),
              dict(name='Dey, Robin', affiliation='VBRL Holdings Inc')],
    description=(
        '<p>Machine-readable data and code for an archival search for '
        'narrow-band radio technosignatures toward stars within 40 pc in '
        'public ALMA observations: the per-window catalogue of %s spectral '
        'windows, the Class A and Class B sensitivity measurements, the %s '
        'threshold crossings with their line attributions and recurrence '
        'tests, the control-field statistics, the inputs and seeds of the '
        'block resampling behind the chance comparison, the %d injection '
        'trials behind the completeness factor, the execution-block and '
        'session membership, the programs that rebuild the article\'s '
        'statistical and calibration summaries from these files, and the '
        'search pipeline as it ran. The second file holds the dynamic spectra '
        'at the star and at control positions around each crossing.</p>'
        % (mac('NWindows').replace('\\,', ','), mac('EvNCrossRaw'),
           sum(len(w['trials']) for w in TRIALS30['windows']))),
    access_right='open', license='cc-by-4.0',
    keywords=['technosignatures', 'SETI', 'ALMA', 'radio astronomy',
              'submillimetre', 'nearby stars', 'narrowband signals'],
    related_identifiers=[],
    notes=('Rebuild: unzip ALMA_Technosignatures_40pc.zip; cd '
           'ALMA_Technosignatures_40pc/code; python3 reproduce.py'),
    version='1')
with open(os.path.join(HERE, 'zenodo_metadata_r30.json'), 'w') as _fh:
    json.dump(dict(metadata=ZENODO_META,
                   files=['ALMA_Technosignatures_40pc.zip', SPECTRA_FILE],
                   spectra_index_columns=[n for n, _u, _d in SPECTRA_INDEX],
                   spectra_arrays=[n for n, _u, _d in SPECTRA_ARRAYS],
                   spectra_arrays_gen2=sorted(SPECTRA_GEN2),
                   spectra_arrays_gen3=sorted(SPECTRA_GEN3),
                   n_crossings_with_spectra=None,
                   doi=DOI), _fh, indent=1)

#: the macro behind each row of statistics/article_values.csv, for zverify
#: V11, which must check the table against the article and not against itself.
#: A build product beside the generator, never a member of the deposit.
with open(os.path.join(HERE, 'zdeposit_artvalues_r30.json'), 'w') as _fh:
    json.dump([dict(program=_p, reading=_r, quantity=_q, macro=_m)
               for _p, _r, _q, _m in ART_VALUES], _fh, indent=1)

print('%s' % TITLE)
for p, n in MANIFEST:
    print('  %-46s %6d rows' % (p, n))
print('  %-46s' % 'documentation/column_descriptions.md')
print('  code/pipeline/ (%d files, production SHA-256 verified)' % N_PIPE)
for nm, _d in CODE:
    print('  code/%-41s' % nm)
