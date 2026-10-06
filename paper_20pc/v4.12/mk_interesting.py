#!/usr/bin/env python3
"""Build the short interesting-targets table for the sample section.

Every value is read from the released per-window catalogue, the frozen 40 pc
census, the confirmed-planet table and the frozen macro layer.  Nothing is
typed: the sensitivity multiplier is read out of the macro file that defines
it, so the table cannot disagree with the text.

Inclusion rule, stated in the caption and applied mechanically:
  a system enters if it lies within 15 pc and hosts at least one confirmed
  planet.  One clause, one threshold, no exceptions.
Systems are ordered by distance.  No row is chosen by hand and no star is
identified anywhere by its position in a list.

Columns: system, distance, confirmed planets, ALMA bands searched,
drift-resolving (Class A) windows, the best Class A EIRP_90, and the number of
execution blocks covering the system (repeat epochs).
"""
import csv
import json
import math
import os
import re
import sys

V = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, V)
from star_alias import canon as _canon, sysname as _sysn, designation as _desig

CAT = os.path.join(V, 'per_target_results_v3.99.csv')
RANKED = os.path.join(V, 'ranked_master40pc.csv')
EXOTAB = '/workspace/SETI/exo_hosts_unique.ecsv'
EXO_RADIUS_ARCSEC = 180.0
DBL_MEARTH = 13.0 * 317.828
D_NEAR_PC = 15.0

OUT = None
DRIVE = None
args = sys.argv[1:]
if '--drive' in args:
    i = args.index('--drive')
    DRIVE = int(args[i + 1])
    del args[i:i + 2]
if args:
    OUT = args[0]


# ----------------------------------------------------- the frozen macro layer
def macro(name):
    """The value of \\newcommand{\\name}{...}, read from the build, not typed."""
    # ★ The macro layer writes `\providecommand{\X}{}\renewcommand{\X}{v}`
    # wherever a name may or may not already exist, so a reader that knows
    # only `\newcommand` finds nothing and reports the macro absent.
    # ★ v4.12: `[^}]+` truncates a value that contains braces of its own, so
    #   `\EirpNinetyBarnLo` = `3.0\times10^{14}` came back as
    #   `3.0\times10^{14` -- a reader that silently returns a malformed
    #   number.  Allow one level of nesting, as the other macro readers in
    #   this build do.
    pat = re.compile(r'\\(?:new|renew)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})+)\}' % name)
    hits = []
    for fn in sorted(os.listdir(V)):
        if not fn.endswith('.tex'):
            continue
        m = pat.search(open(os.path.join(V, fn), errors='ignore').read())
        if m:
            hits.append((fn, m.group(1)))
    assert len(hits) == 1, (
        'the multiplier must have exactly one definition in the frozen macro '
        'layer, found %d for %s: %s' % (len(hits), name, hits))
    return hits[0][1]


# the adopted sensitivity multiplier.  Its predecessor name is retired:
# one quantity, one macro.
MULT_NAME = 'EirpNinetyMultA'
MULT = float(macro(MULT_NAME))
# ★ a sensitivity multiplier below unity would mean the completeness level is
# easier to reach than the trigger, which is impossible by construction
assert MULT > 1.0, 'the sensitivity multiplier read %r' % MULT


# --------------------------------------------------------------------- inputs
def load_exo_hosts():
    rows, hdr = [], None
    for ln in open(EXOTAB):
        if ln.startswith('#'):
            continue
        p = next(csv.reader([ln.rstrip('\n')], delimiter=' ', quotechar='"',
                            skipinitialspace=True))
        if hdr is None:
            hdr = p
            continue
        rows.append(dict(zip(hdr, p)))
    hosts = {}
    for r in rows:
        h = hosts.setdefault(r['hostname'], dict(
            hostname=r['hostname'], ra=float(r['ra']), dec=float(r['dec']),
            planets=set(), n_confirmed=int(r['n_planets_confirmed'] or 0),
            sy_pnum=int(r['sy_pnum'] or 0), masses=[]))
        h['planets'].add(r['pl_name'])
        h['n_confirmed'] = max(h['n_confirmed'],
                               int(r['n_planets_confirmed'] or 0))
        try:
            h['masses'].append(float(json.loads(r['pl_bmasse'])))
        except Exception:
            pass
    for h in hosts.values():
        h['n_planets'] = max(h['n_confirmed'], h['sy_pnum'], len(h['planets']))
        # a host all of whose catalogued companions are above the
        # deuterium-burning limit is a brown-dwarf companion, not a planet host
        h['sub_dbl'] = (not h['masses']
                        or any(m <= DBL_MEARTH for m in h['masses']))
    return hosts


def sep_arcsec(ra1, de1, ra2, de2):
    d2r = math.pi / 180.0
    dra = (ra1 - ra2) * math.cos(0.5 * (de1 + de2) * d2r)
    return math.hypot(dra, de1 - de2) * 3600.0


_nk = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
_REV_ALIAS = {'hd139664': 'glup'}
nkey = lambda s: _REV_ALIAS.get(_nk(s), _nk(s))

cat = list(csv.DictReader(open(CAT)))
ranked = list(csv.DictReader(open(RANKED)))
by_norm = {}
for r in ranked:
    by_norm.setdefault(nkey(r['name']), r)

stars = sorted({_canon(r['star_name']) for r in cat})
systems = sorted({_sysn(s) for s in stars})

sysrows = {}
for r in cat:
    sysrows.setdefault(_sysn(_canon(r['star_name'])), []).append(r)

sys_census = {}
for s in stars:
    m = by_norm.get(nkey(s))
    if m is not None:
        sys_census.setdefault(_sysn(s), []).append(m)

exo = load_exo_hosts()
sys_planets = {}
for sy, ms in sys_census.items():
    best, bs = None, 1e9
    for m in ms:
        ra, de = float(m['ra']), float(m['dec'])
        for h in exo.values():
            d = sep_arcsec(ra, de, h['ra'], h['dec'])
            if d < bs:
                bs, best = d, h
    if best is not None and bs <= EXO_RADIUS_ARCSEC and best['sub_dbl']:
        sys_planets[sy] = best

# ★★★ v4.12: THE EIRP_90 COLUMN WAS NOT THE PAPER'S EIRP_90.  It was
# `eirp_nominal_W` times the BLANKET multiplier \EirpNinetyMultA, and
# `adopted_e90.py` exists precisely because that is not what the paper
# adopts: the completeness is transferred WITHIN the control-ring strata and
# the omitted annual parallax is applied.  On the noise-ring windows that
# makes this table's numbers about a quarter too shallow, and 61 Vir -- a
# row of this very table -- was printed at 1.8e14 W against an adopted
# 1.4e14.  `adopted_e90` is the single owner; use it, and assert the two
# nearest-star cells against the macros Section 5.2 prints for them.
import adopted_e90 as _ae                                    # noqa: E402
_E90 = _ae.per_window(cat, V)

# ★ R2 minor 8: the nearest-star limits must sit in one place.  Barnard's
#   Star is already a row here and its EIRP_90 cell read "--", because the
#   column was Class A only and the archive holds no fine-channel window
#   toward it.  A Class B column fills that cell -- and five others -- with
#   the limit the survey actually reached, which is the number Section 5.2
#   quotes.  Wolf 359 hosts no confirmed planet, so it cannot be a row under
#   this table's one-clause rule; it is given in the note instead.
# ----------------------------------------------------------------- the rule
cand = {}
for sy in systems:
    if sy not in sys_planets:
        continue
    ws = sysrows[sy]
    wa = [r for r in ws if r['search_class'] == 'A']
    wb = [r for r in ws if r['search_class'] == 'B']
    cand[sy] = dict(
        sy=sy, d=min(float(r['dist_pc']) for r in ws),
        npl=sys_planets[sy]['n_planets'],
        bands=sorted({int(r['band']) for r in ws}),
        nwa=len(wa),
        neb=len({r['eb'] for r in ws}),
        p90=min(_E90[id(r)] for r in wa) if wa else None,
        p90b=min(_E90[id(r)] for r in wb) if wb else None)

assert cand, 'no planet host in the sample, which cannot be right'
near = D_NEAR_PC
if DRIVE == 1:                      # the rule admits every planet host
    near = 1e3
if DRIVE == 2:                      # the rule admits almost none
    near = 2.0
rows_out = [r for r in cand.values() if r['d'] < near]
rows_out.sort(key=lambda r: r['d'])
# drives 3 and 4 REPLACE a row rather than adding one, so the row count stays
# inside the range S2 checks and the assertion under test is the one that fires
if DRIVE == 3:                      # a row that is not a planet host
    rows_out[-1] = dict(rows_out[-1], npl=0)
if DRIVE == 4:                      # the same system twice
    rows_out[-1] = dict(rows_out[0], d=rows_out[-1]['d'])
if DRIVE == 5:                      # out of distance order
    rows_out = rows_out[::-1]

# ------------------------------------------------------------------ assertions
# S1  the table is a selection of the sample, not the sample
assert 0 < len(rows_out) < len(systems), (
    'the short table is not short: %d of %d systems' % (len(rows_out),
                                                        len(systems)))
# S2  the table claims to be 10-15 rows; if the stated rule stops delivering
#     that, the rule must be restated in the caption, not the rows trimmed
assert 10 <= len(rows_out) <= 15, (
    'the stated rule yields %d systems, outside the 10-15 the table claims; '
    'change the rule, do not trim rows by hand' % len(rows_out))
# S3  every row is a planet host, which is what the rule says
assert all(r['npl'] > 0 for r in rows_out), 'a row carries no planet'
# S4  no system appears twice, so the row count is a system count
assert len({r['sy'] for r in rows_out}) == len(rows_out), (
    'a system appears more than once')
# S5  distance-ordered, and nothing may name a star by its rank here
assert all(rows_out[i]['d'] <= rows_out[i + 1]['d']
           for i in range(len(rows_out) - 1)), 'rows are not distance-ordered'
# S6  the EIRP_90 column must vary, or it is not measuring anything
_p = [r['p90'] for r in rows_out if r['p90']]
assert _p and min(_p) < max(_p), 'the EIRP_90 column is constant or empty'
# S7  the Class A column must be informative both ways on this selection: the
#     point of the table is partly that near planet hosts lack drift coverage
_na = sum(1 for r in rows_out if r['nwa'] > 0)
assert 0 < _na < len(rows_out), (
    'every row has the same drift-resolving status (%d of %d), so the column '
    'carries no information' % (_na, len(rows_out)))
# S8  the distance clause must actually exclude something, or it is vacuous
assert len(rows_out) < len(cand), (
    'the %g pc clause excludes no planet host, so it is not a criterion'
    % D_NEAR_PC)
# S9  EVERY ROW NOW CARRIES A LIMIT.  The point of the Class B column is that
#     no row is left with two dashes: the archive reached every one of these
#     systems in at least one class, and a table of nearby planet hosts whose
#     sensitivity column is mostly "--" tells a reader nothing.
_nolimit = [r['sy'] for r in rows_out if not r['p90'] and not r['p90b']]
assert not _nolimit, ('%d row(s) carry no limit in either class: %s'
                      % (len(_nolimit), _nolimit))
# S10 and the two columns must be DIFFERENT quantities, or one of them is
#     redundant: every system with both must have a Class A limit at least as
#     deep as its Class B one, and at least one must have only Class B.
_both = [r for r in rows_out if r['p90'] and r['p90b']]
assert _both and all(r['p90'] <= r['p90b'] * 1.0 + 1e-9 for r in _both), (
    'a Class A limit is shallower than the same system\'s Class B limit')
assert any(r['p90b'] and not r['p90'] for r in rows_out), (
    'no row needs the Class B column, so it should not be there')
# S11 THE TWO NEAREST-STAR CELLS ARE THE MACROS SECTION 5.2 PRINTS.  This is
#     what "the nearest-star results sit in one place" has to mean: the same
#     number, not a second derivation of it.  Read the macro, compare, and
#     name the star by catalogue designation rather than by table position.
_near = {'EirpNinetyBarnLo': "NAME Barnards star"}


def _sfnum(tex):
    mm = re.match(r'([-\d.]+)\\times10\^\{(-?\d+)\}', (tex or '').strip())
    if not mm:
        return None, None
    mant, ex = mm.group(1), int(mm.group(2))
    dp = len(mant.split('.')[1]) if '.' in mant else 0
    return float(mant) * 10.0 ** ex, 0.5 * 10.0 ** (ex - dp)


for _mac, _sy in _near.items():
    _row = [r for r in rows_out if r['sy'] == _sy]
    if not _row:                 # not a planet host any more: nothing to pin
        continue
    _pub, _tol = _sfnum(macro(_mac))
    _got = _row[0]['p90b'] if DRIVE != 6 else _row[0]['p90b'] * 1.5
    assert _pub is not None, 'macro \\%s is not a power in scientific form' % _mac
    assert abs(_got - _pub) <= _tol, (
        '%s is tabulated at %.4g W but Section 5.2 prints \\%s = %.4g W'
        % (_sy, _got, _mac, _pub))

# --------------------------------------------------------------------- output
def esci(x, nd=1):
    e = int(math.floor(math.log10(abs(x))))
    return '$%.*f\\times10^{%d}$' % (nd, x / 10.0 ** e, e)


def tname(s):
    # alias=True: this table is a reader's entry point, so the designation
    # the literature uses is printed beside the catalogue key.
    t = _desig(s, alias=True)
    # SIMBAD marks a common name with a leading "NAME "; strip the prefix
    # mechanically rather than mapping individual stars by hand
    # ★ Do NOT strip the marker here: star_alias.designation owns the
    # printable form and knows how each common name is actually written
    # ("Barnard's Star", not "Barnards star").  Stripping it first hides the
    # marker from the one function that can resolve it.
    t = re.sub(r'^(V\s*star)\s+', '', t)
    return re.sub(r'(?<!\$)-(?!\$)', '$-$', t)


# the disputed planet, flagged by reading the host out of the rows rather
# than by position: the single companion listed for Kapteyn's Star is widely
# argued to be an artefact of stellar activity, and a table of confirmed
# planets that does not say so overstates its own column.
DISPUTED = {'HD 33793': ("Kapteyn's Star", 'the single listed companion is '
                         'disputed as a stellar-activity artefact')}
_disp_rows = [r for r in rows_out if r['sy'] in DISPUTED]
assert _disp_rows, ('the disputed-planet note names %s, which is not a row '
                    'of this table' % sorted(DISPUTED))
_marks = {r['sy']: '$^{b}$' for r in _disp_rows}

# ★ ONE sensitivity column, not two.  The table is single-column in print, so
#   a second EIRP column would not fit; the deepest limit the survey reached
#   for each system is given once, with the class it came from, which is what
#   makes the cell meaningful: "--" used to mean "no fine-channel window",
#   and a reader could not tell that from "not searched".
def _best(r):
    for v, cls in ((r['p90'], 'A'), (r['p90b'], 'B')):
        if v:
            return esci(v)[:-1] + '\\,^{\\rm %s}$' % cls, cls
    return '--', None


lines = ['%% GENERATED by mk_interesting.py -- do not hand-edit.',
         '\\begin{tabular}{@{}l@{~~}r@{~~}r@{~~}l@{~~}r@{~~}r@{~~}r@{}}',
         '\\hline',
         'System & $d$ & $N_{\\rm pl}$ & Bands & $N_{\\rm A}$ & '
         'EIRP$_{90}^{a}$ & $N_{\\rm eb}$ \\\\',
         ' & (pc) & & & & (W) & \\\\',
         '\\hline']
for r in rows_out:
    lines.append('%s%s & %.1f & %d & %s & %d & %s & %d \\\\' % (
        tname(r['sy']), _marks.get(r['sy'], ''), r['d'], r['npl'],
        ','.join(str(b) for b in r['bands']), r['nwa'],
        _best(r)[0], r['neb']))
lines += ['\\hline', '\\end{tabular}', '']
# the notes: the column, the disputed planet, and Wolf 359, which this
# table's one-clause rule cannot admit because it hosts no confirmed planet
_wolfall = [sy for sy in systems if sy == 'Wolf 359']
_wolfb = (min(_E90[id(x)] for x in sysrows['Wolf 359']
              if x['search_class'] == 'B') if _wolfall else None)
notes = ['{\\footnotesize $^{a}$The deepest EIRP$_{90}$ the survey reached '
         'for the system, marked A where it comes from a drift-resolving '
         'fine-channel window and B where the archive holds only '
         'coarse-channel windows, which constrain an unresolved spectral '
         'excess rather than a drifting carrier.']
for sy, (common, why) in DISPUTED.items():
    if sy in _marks:
        notes.append(' $^{b}$%s is %s; %s.' % (tname(sy), common, why))
if _wolfb:
    notes.append(' Wolf~359, the third-nearest system searched, hosts no '
                 'confirmed planet and so does not meet this table\'s rule; '
                 'its coarse-channel limit is %s\\,W.' % esci(_wolfb))
notes.append('}')
lines.append(''.join(notes))
tex = '\n'.join(lines) + '\n'

suf = '' if DRIVE is None else '_drive%d' % DRIVE
if OUT:
    path = OUT if DRIVE is None else OUT.replace('.tex', suf + '.tex')
    open(path, 'w').write(tex)
    print('wrote', path)
else:
    print(tex)

print('multiplier          : \\%s = %.2f' % (MULT_NAME, MULT))
print('rows                : %d of %d systems' % (len(rows_out), len(systems)))
print('distance span       : %.1f - %.1f pc' % (rows_out[0]['d'],
                                                rows_out[-1]['d']))
print('with Class A        : %d of %d' % (_na, len(rows_out)))
print('EIRP_90 span        : %.3g - %.3g W' % (min(_p), max(_p)))
print('planet hosts total  : %d, of which inside %g pc: %d'
      % (len(cand), D_NEAR_PC, len(rows_out)))
print('assertions          : S1-S11 pass')
