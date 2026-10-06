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
    pat = re.compile(r'\\(?:new|renew)command\{\\%s\}\{([^}]+)\}' % name)
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

# ----------------------------------------------------------------- the rule
cand = {}
for sy in systems:
    if sy not in sys_planets:
        continue
    ws = sysrows[sy]
    wa = [r for r in ws if r['search_class'] == 'A']
    cand[sy] = dict(
        sy=sy, d=min(float(r['dist_pc']) for r in ws),
        npl=sys_planets[sy]['n_planets'],
        bands=sorted({int(r['band']) for r in ws}),
        nwa=len(wa),
        neb=len({r['eb'] for r in ws}),
        p90=(MULT * min(float(r['eirp_nominal_W']) for r in wa)) if wa
             else None)

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


lines = ['%% GENERATED by mk_interesting.py -- do not hand-edit.',
         '\\begin{tabular}{@{}l@{~~}r@{~~}r@{~~}l@{~~}r@{~~}r@{~~}r@{}}',
         '\\hline',
         'System & $d$ & $N_{\\rm pl}$ & Bands & $N_{\\rm A}$ & '
         'EIRP$_{90}$ & $N_{\\rm eb}$ \\\\',
         ' & (pc) & & & & (W) & \\\\',
         '\\hline']
for r in rows_out:
    lines.append('%s & %.1f & %d & %s & %d & %s & %d \\\\' % (
        tname(r['sy']), r['d'], r['npl'],
        ','.join(str(b) for b in r['bands']), r['nwa'],
        esci(r['p90']) if r['p90'] else '--', r['neb']))
lines += ['\\hline', '\\end{tabular}']
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
print('assertions          : S1-S8 pass')
