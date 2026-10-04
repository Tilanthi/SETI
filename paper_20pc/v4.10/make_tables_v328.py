#!/usr/bin/env python3
# WARNING (added v3.30): the three tables this emits were hand-trimmed and
# macro-ised after generation.  Re-running it will REVERT that trimming and
# re-hardcode literal counts over the \N... macros from survey_numbers.tex.
# If you re-run it after a data refresh, re-apply the macro substitution and
# re-check the page budget before pushing.
"""Regenerate the three data tables and the released machine-readable master
table for the 0-40 pc release (v3.28).

Everything is derived; nothing is hard-coded.  The selection logic is imported
verbatim from survey_stats.py (the authoritative statistics script) by exec-ing
its header, so the sample definition cannot drift between the text, the
statistics and the tables.

Outputs
-------
  tables/tab_selection.tex        \\label{tab:selfunc}
  tables/tab_perband.tex          \\label{tab:perband}
  tables/tab_perstar.tex          \\label{tab:starsummary}
  per_target_results_v3.31.csv    released master table (all 448 extracted rows)
  tables/table_numbers_v328.json  every headline number the tables assert
"""
import json, math, csv, os, re, collections, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
TAB = os.path.join(HERE, 'tables')
os.makedirs(TAB, exist_ok=True)

# v4.07: these two used to be absolute paths into /workspace/SETI, OUTSIDE the
# version directory.  That is a reproducibility hole and it had already opened:
# v4.06 regenerated the census with an explicit `is_exo_host` into this folder
# and left the reader pointing at the older copy outside it, so the build read
# two different censuses (v381_calc.py the local one, this the external one) and
# nothing said so.  The census is now read from the deposit, and the assertion
# below refuses a path outside it.  The Gaia reference census is 50 pc of
# archival photometry, far too large to deposit, so it stays external and is
# declared as such.
RANKED = os.path.join(HERE, 'ranked_master40pc.csv')
assert os.path.dirname(os.path.abspath(RANKED)) == HERE, (
    'the census must be read from the version directory, not from %r: a file '
    'outside the deposit can change under the build' % RANKED)
GAIA = '/workspace/SETI/gaia_nearby50pc.ecsv'   # external by declaration: 50 pc
                                                # Gaia reference, not deposited

# ---------------------------------------------------------------------------
# 1.  sample definition -- reused verbatim from survey_stats.py
# ---------------------------------------------------------------------------
_src = open(os.path.join(HERE, 'survey_stats.py')).read()
_head = _src.split('S=collections.OrderedDict()')[0]
G = {}
exec(_head, G)

rows = G['rows']          # all 448 extracted windows
uniq = G['uniq']          # after de-duplication
defect = G['defect']      # noise-handling defect
withheld = G['withheld']  # eps Eri Band 6, primary-beam validity
good = G['good']          # 417 searched windows
from star_alias import sysname as sysn, canon as _canon   # v3.85: alias merge
# v4.01, referee 2 S5: one definition of the printable designation
from star_alias import designation as _desig
C_LIGHT = G['C']

_id = lambda seq: {id(r) for r in seq}
ID_UNIQ, ID_DEF, ID_WITH, ID_GOOD = _id(uniq), _id(defect), _id(withheld), _id(good)


def qa_status(r):
    if id(r) not in ID_UNIQ:
        return 'duplicate_row'
    if id(r) in ID_DEF:
        return 'noise_defect'
    if id(r) in ID_WITH:
        return 'withheld_primary_beam'
    return 'searched'


assert sum(1 for r in rows if qa_status(r) == 'searched') == len(good)

stars = sorted({_canon(r['star_name']) for r in good})   # v3.85: alias merge
systems = sorted({sysn(s) for s in stars})
NUM = collections.OrderedDict()   # every headline number the tables assert
NUM['n_rows_extracted'] = len(rows)
NUM['n_duplicate_rows'] = len(rows) - len(uniq)
NUM['n_noise_defect'] = len(defect)
NUM['n_withheld'] = len(withheld)
NUM['n_windows_searched'] = len(good)
NUM['n_stars'] = len(stars)
NUM['n_systems'] = len(systems)
# ★★ v4.09: THIS WAS THE RAW `star_name` WHILE survey_stats.py HAS USED THE
# CANONICAL ONE SINCE v3.85, so the two counts disagreed -- 116 against 112 --
# and the cross-check below PRINTED "MISMATCH" and asserted nothing for four
# versions.  The four extra pairs are stars the catalogue carries under two
# labels (a named directory and a `GaiaDR3_*` one), which is the same
# alias-key family D31 merged in the stack and D35/D36 found thirteen more
# times.  Keyed canonically the two agree, and the agreement is now ASSERTED
# rather than reported (see the cross-check block at the end of this file).
NUM['n_starbands'] = len({(_canon(r['star_name']), r['band_x']) for r in good})
NUM['n_starbands_rawname'] = len({(r['star_name'], r['band_x'])
                                  for r in good})
NUM['n_eb'] = len({r['eb'] for r in good})

# ---------------------------------------------------------------------------
# 2.  helpers
# ---------------------------------------------------------------------------
def tex_escape(s):
    out = []
    for ch in str(s):
        if ch in '%&#$':
            out.append('\\' + ch)
        elif ch == '_':
            out.append('\\_')
        elif ch == '~':
            out.append('\\textasciitilde{}')
        elif ch == '^':
            out.append('\\textasciicircum{}')
        else:
            out.append(ch)
    # collapse the multiple spaces that occur in SIMBAD identifiers; TeX would
    # collapse them anyway, so do it explicitly and predictably
    return re.sub(r'\s+', ' ', ''.join(out)).strip()


def esci(x, nd=1):
    """1.6e13 -> $1.6\\times10^{13}$"""
    if x is None:
        return '--'
    e = int(math.floor(math.log10(abs(x))))
    m = x / 10.0 ** e
    return '$%.*f\\times10^{%d}$' % (nd, m, e)


def eplain(x):
    """1.6e13 -> 1.62e+13 (compact form used in the per-star table)"""
    return '%.2e' % x


def merged_union(ws):
    iv = sorted((min(r['flo'], r['fhi']), max(r['flo'], r['fhi'])) for r in ws)
    mg = []
    for lo, hi in iv:
        if mg and lo <= mg[-1][1]:
            mg[-1][1] = max(mg[-1][1], hi)
        else:
            mg.append([lo, hi])
    return sum(b - a for a, b in mg), len(mg)


def fcen(r):
    return 0.5 * (r['flo'] + r['fhi'])


def drift_ceiling(r):
    """drift-rate ceiling normalised to carrier frequency, Hz/s per GHz"""
    return r['drift_max'] / fcen(r)


# ---------------------------------------------------------------------------
# 3.  name matching against the ranked census
# ---------------------------------------------------------------------------
# the export applies the archival-hygiene alias g Lup -> HD 139664; the ranked
# census still carries the old identifier, so map it back for the crossmatch
_REV_ALIAS = {'hd139664': 'glup'}
_n = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
norm = lambda s: _REV_ALIAS.get(_n(s), _n(s))
ranked = list(csv.DictReader(open(RANKED)))
by_norm = {}
for r in ranked:
    by_norm.setdefault(norm(r['name']), r)

match = {}
unmatched = []
n_exact = 0
ranked_exact = {r['name'] for r in ranked}
for s in stars:
    if s in ranked_exact:
        n_exact += 1
    m = by_norm.get(norm(s))
    if m is None:
        unmatched.append(s)
    else:
        match[s] = m
NUM['ranked_csv_exact_name_matches'] = n_exact
NUM['ranked_csv_normalised_matches'] = len(match)
NUM['ranked_csv_unmatched'] = unmatched

fnum = lambda v: (float(v) if str(v).strip() not in ('', 'None') else None)
teff = {s: fnum(m['teff']) for s, m in match.items()}
teff = {s: v for s, v in teff.items() if v is not None}
NUM['n_sample_with_teff'] = len(teff)

# distance consistency check between export and ranked census
dist_star = {}
for r in good:
    dist_star[_canon(r['star_name'])] = r['dist_pc']   # v3.85: canonical key
dmis = [(s, dist_star[s], float(m['dist_pc'])) for s, m in match.items()
        if abs(dist_star[s] - float(m['dist_pc'])) > 0.05]
NUM['distance_mismatches_export_vs_ranked'] = dmis

# v4.05 (R2-4).  `is_exo_host` is a property of HOW A STAR ENTERED THE CENSUS,
# not of the star.  build_ranked_master40pc.py writes
#     is_exo_host = c['is_exo_host'] if c['is_exo_host'] else ''
# so entries that came in through the debris-disc route leave with an EMPTY
# string -- never False -- and are never tested against the planet table.  139
# of the 168 census rows carry a blank flag; counting blanks as non-hosts, as
# the line below used to, makes 19 a LOWER BOUND rather than a count.  It is
# the fourth instance of this project's hard-coded-prose bug family.
#
# The three it misses are BD+05 1668 = GJ 273 = Luyten's Star (2 planets, the
# survey's third-nearest system and the only star in the sample that has been
# deliberately transmitted TO), Barnard's Star (4) and HD 33793 = Kapteyn's
# Star (1).  GJ 273 is missed twice over: it moves 3.7 arcsec per year, so a
# join that filters on distance agreement throws away precisely the nearest
# and fastest-moving of the three.
#
# Replacement: a POSITIONAL join of the in-sample census rows to the
# confirmed-planet table.  The flag-based count is computed first and asserted
# to reproduce the shipped 19 / 42, so the correction is measured against the
# published number rather than replacing it silently.
EXOTAB = '/workspace/SETI/exo_hosts_unique.ecsv'
EXO_RADIUS_ARCSEC = 180.0      # high-proper-motion stars; robustness below
# Deuterium-burning limit, 13 Jupiter masses, in Earth masses.  Used as the
# one mechanical criterion separating a planet host from a brown-dwarf
# companion; see the LP 736-15 adjudication below.
DBL_MEARTH = 13.0 * 317.828


def _load_exo_hosts():
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
        # one ROW per host, but the row carries the system's confirmed count;
        # len(planets) alone would under-count every multi-planet system
        h['n_planets'] = max(h['n_confirmed'], h['sy_pnum'], len(h['planets']))
        # A host every one of whose catalogued companions is above the
        # deuterium-burning limit is a brown-dwarf companion, not an
        # exoplanet host.  The criterion is mechanical and is applied to every
        # match alike; it is not a hand exclusion.
        h['sub_dbl'] = (not h['masses']
                        or any(m <= DBL_MEARTH for m in h['masses']))
    return hosts


def _sep_arcsec(ra1, de1, ra2, de2):
    d2r = math.pi / 180.0
    dra = (ra1 - ra2) * math.cos(0.5 * (de1 + de2) * d2r)
    return math.hypot(dra, de1 - de2) * 3600.0


exo_census = sum(1 for r in ranked if r['is_exo_host'].strip().lower() == 'true')
# --- the shipped, flag-based count, kept only as the falsifier -------------
_exo_sample_flag = sum(1 for s, m in match.items()
                       if m['is_exo_host'].strip().lower() == 'true')
_npl_sample_flag = sum(int(m['n_planets']) for s, m in match.items()
                       if m['n_planets'].strip())
# ★ If this stops reproducing 19 / 42 the census or the name join has moved and
# the correction below would be measured against the wrong baseline.
assert (_exo_sample_flag, _npl_sample_flag) == (19, 42), \
    ('the flag-based host count no longer reproduces the shipped 19 / 42: %s'
     % ((_exo_sample_flag, _npl_sample_flag),))
_n_blank_flag = sum(1 for r in ranked if not r['is_exo_host'].strip())
# ★ ...and the defect itself must still be present in the census file, or
# there is nothing to repair here and this block should be deleted.
assert _n_blank_flag > 0, 'no census entry carries a blank is_exo_host'

# --- the positional replacement --------------------------------------------
_exo_hosts = _load_exo_hosts()
_census_in_sample = {m['name']: m for m in match.values()}
_exo_hits = {}
for _nm, _m in sorted(_census_in_sample.items()):
    _ra, _de = float(_m['ra']), float(_m['dec'])
    _best, _bs = None, 1e9
    for _h in _exo_hosts.values():
        _s = _sep_arcsec(_ra, _de, _h['ra'], _h['dec'])
        if _s < _bs:
            _bs, _best = _s, _h
    if _bs <= EXO_RADIUS_ARCSEC:
        _exo_hits[_nm] = (_best, _bs)
exo_sample = len(_exo_hits)
npl_sample = sum(h['n_planets'] for h, _ in _exo_hits.values())
# The published counts use the archive's own definition of a confirmed planet,
# because that is what "known planets" means when the number is compared with
# anything.  Two of the matches are companions above the deuterium-burning
# limit and would not survive the IAU working definition: HR 2562 b at about
# 30 Jupiter masses, which the SHIPPED flag already counted, and
# VHS J125601.92-125723.9 b at 16, whose census row j1256-1257 is LP 736-15 --
# an M dwarf with 8 searched windows whose own wide brown-dwarf companion sits
# 5.7 arcsec away and carries the catalogued object.  Both counts are emitted;
# neither is hidden, and the criterion is the mass, applied to every match
# alike rather than to the one that was noticed.
_exo_bd = {nm for nm, (h, _) in _exo_hits.items() if not h['sub_dbl']}
# ★ If no match is above the limit this distinction is vacuous and the extra
# pair of numbers below should be deleted rather than printed.
assert _exo_bd, 'no positional match exceeds the deuterium-burning limit'
NUM['exo_hosts_above_dbl'] = sorted(_exo_bd)
NUM['exo_hosts_strict'] = exo_sample - len(_exo_bd)
NUM['exo_planets_strict'] = npl_sample - sum(
    h['n_planets'] for nm, (h, _) in _exo_hits.items() if nm in _exo_bd)
# ★ One of the two is inside the shipped 19, so the strict criterion SUBTRACTS
# from the published figure as well as adding to it.  That is the finding:
# stated, not smoothed.
NUM['exo_hosts_above_dbl_already_flagged'] = sorted(
    _exo_bd & {nm for nm, mm in _census_in_sample.items()
               if mm['is_exo_host'].strip().lower() == 'true'})
assert NUM['exo_hosts_above_dbl_already_flagged'], \
    'the deuterium-burning cut no longer touches the shipped count'
# ★ The correction may only ADD: a census row the flag calls a host and the
# sky does not would mean the positional join is broken, not the flag.
_unsupported = [nm for nm, mm in _census_in_sample.items()
                if mm['is_exo_host'].strip().lower() == 'true'
                and nm not in _exo_hits]
assert not _unsupported, ('flagged hosts with no positional counterpart: %s'
                          % _unsupported)
assert exo_sample >= _exo_sample_flag and npl_sample >= _npl_sample_flag, \
    (exo_sample, npl_sample)
# ★ And it must actually change something, or this block is dead code claiming
# a repair that did nothing.
assert exo_sample > _exo_sample_flag, (exo_sample, _exo_sample_flag)
# Robustness, measured rather than assumed: all but one match lies within a few
# arcsec, and the outlier is GJ 273's proper motion.
_wide = sorted((round(s, 1), nm) for nm, (_, s) in _exo_hits.items())
NUM['exo_host_join_radius_arcsec'] = EXO_RADIUS_ARCSEC
NUM['exo_host_join_max_sep_arcsec'] = _wide[-1][0]
NUM['exo_host_join_second_max_sep_arcsec'] = _wide[-2][0]
NUM['exo_hosts_flag_based'] = _exo_sample_flag
NUM['exo_planets_flag_based'] = _npl_sample_flag
NUM['census_rows_with_blank_flag'] = _n_blank_flag
NUM['exo_hosts_added_by_position'] = sorted(
    nm for nm, mm in _census_in_sample.items()
    if mm['is_exo_host'].strip().lower() != 'true' and nm in _exo_hits)


NUM['n_census_entries'] = len(ranked)
NUM['n_exo_hosts_census'] = exo_census
NUM['n_exo_hosts_sample'] = exo_sample
NUM['n_planets_sample'] = npl_sample

# ---------------------------------------------------------------------------
# 4.  Gaia reference census within 40 pc
# ---------------------------------------------------------------------------
PLX_FRAC = 0.10        # sigma_pi/pi quality cut
gaia = []
with open(GAIA) as f:
    hdr = None
    for ln in f:
        if ln.startswith('#'):
            continue
        p = ln.split()
        if hdr is None:
            hdr = p
            continue
        gaia.append(dict(zip(hdr, p)))


def gf(r, k):
    try:
        return float(r[k])
    except (ValueError, KeyError):
        return None


ref = []
for r in gaia:
    plx, pe = gf(r, 'parallax'), gf(r, 'parallax_error')
    if plx is None or plx <= 0 or pe is None:
        continue
    if pe / plx > PLX_FRAC:
        continue
    d = 1000.0 / plx
    if d > 40.0:
        continue
    ref.append({'d': d, 'teff': gf(r, 'teff_gspphot'),
                'bp_rp': gf(r, 'bp_rp'), 'g': gf(r, 'phot_g_mean_mag')})
NUM['gaia_rows_total'] = len(gaia)
NUM['gaia_ref_40pc'] = len(ref)
NUM['gaia_ref_40pc_with_teff'] = sum(1 for r in ref if r['teff'] is not None)
NUM['gaia_plx_quality_cut'] = 'sigma_pi/pi <= %.2f' % PLX_FRAC

SHELLS = [('$d\\le5$\\,pc', lambda d: d <= 5),
          ('5--10\\,pc', lambda d: 5 < d <= 10),
          ('10--20\\,pc', lambda d: 10 < d <= 20),
          ('20--30\\,pc', lambda d: 20 < d <= 30),
          ('30--40\\,pc', lambda d: 30 < d <= 40)]
TCLASS = [('A ($\\ge7500$\\,K)', lambda t: t >= 7500),
          ('F (6000--7500\\,K)', lambda t: 6000 <= t < 7500),
          ('G (5300--6000\\,K)', lambda t: 5300 <= t < 6000),
          ('K (3900--5300\\,K)', lambda t: 3900 <= t < 5300),
          ('M ($<3900$\\,K)', lambda t: t < 3900)]

sample_d = [dist_star[s] for s in stars]
ref_d = [r['d'] for r in ref]
ref_t = [r['teff'] for r in ref if r['teff'] is not None]
sample_t = [teff[s] for s in stars if s in teff]


def panel(census_vals, sample_vals, bins):
    out = []
    nc, ns = len(census_vals), len(sample_vals)
    for lab, f in bins:
        c = sum(1 for v in census_vals if f(v))
        s = sum(1 for v in sample_vals if f(v))
        pc, ps = 100.0 * c / nc, 100.0 * s / ns
        ratio = (ps / pc) if pc > 0 else None
        out.append((lab, c, pc, s, ps, ratio))
    return out, nc, ns


dist_panel, n_ref_d, n_smp_d = panel(ref_d, sample_d, SHELLS)
teff_panel, n_ref_t, n_smp_t = panel(ref_t, sample_t, TCLASS)
# v3.85 (round-1 self-review, C27): the body text typed "41 per cent are M
# dwarfs against 69 per cent of the census" while this table printed 36.8
# and 68.7. Emit the table's own numbers as macros.

NUM['distance_panel'] = [{'bin': re.sub(r'[\\$]|\\,|le|pc', '', l).strip(),
                          'census_n': c, 'census_pct': round(pc, 3),
                          'sample_n': s, 'sample_pct': round(ps, 2),
                          'ratio': (round(rr, 2) if rr else None)}
                         for l, c, pc, s, ps, rr in dist_panel]
NUM['teff_panel'] = [{'bin': l.split(' ')[0], 'census_n': c,
                      'census_pct': round(pc, 2), 'sample_n': s,
                      'sample_pct': round(ps, 2),
                      'ratio': (round(rr, 2) if rr else None)}
                     for l, c, pc, s, ps, rr in teff_panel]
NUM['n_ref_with_teff'] = n_ref_t
NUM['n_sample_teff_used'] = n_smp_t

# ---------------------------------------------------------------------------
# 5.  TABLE 1 -- selection function
# ---------------------------------------------------------------------------
def fmt_pct(p):
    return ('%.1f' % p) if p >= 0.1 else ('%.2f' % p)


L = []
L.append('% Generated by make_tables_v328.py -- do not edit by hand.')
L.append('\\begin{table}')
L.append('\\centering')
L.append('\\scriptsize')
L.append('\\setlength{\\tabcolsep}{4pt}')
L.append('\\caption{Selection function of the searched sample against a '
         'volume-limited reference census: Gaia~DR3 sources '
         'with $\\varpi>0$, $\\sigma_\\varpi/\\varpi\\le%.1f$ and $1/\\varpi\\le40$\\,pc '
         '(%d objects, of which %d carry a \\texttt{teff\\_gspphot} '
         'estimate, %d per cent), against the %d stars with at least one '
         'searched window. Temperatures are available '
         'for %d of the %d (all %d matched to the %d-entry '
         'ALMA-covered census, %d by exact name; %d of those matches '
         'carry a temperature), so the temperature panel is normalised '
         'over classified objects only. ``Ratio\'\' is the sample column '
         'fraction over the census column fraction; $>1$ is '
         'over-representation.}'
         % (PLX_FRAC, len(ref), NUM['gaia_ref_40pc_with_teff'],
            round(100.0 * NUM['gaia_ref_40pc_with_teff'] / len(ref)),
            len(stars), n_smp_t, len(stars), len(match), len(ranked),
            n_exact, n_smp_t))
L.append('\\label{tab:selfunc}')
L.append('\\begin{tabular}{@{}lrrr@{}}')
L.append('\\toprule')
L.append('Property & Census & Searched & Ratio \\\\')
L.append('\\midrule')
L.append('\\multicolumn{4}{@{}l}{Distance (all %d searched stars; %d census '
         'objects)} \\\\' % (n_smp_d, n_ref_d))
for lab, c, pc, s, ps, rr in dist_panel:
    L.append('\\quad %s & %d (%s\\%%) & %d (%s\\%%) & %s \\\\'
             % (lab, c, fmt_pct(pc), s, fmt_pct(ps),
                ('%.1f' % rr) if rr else '--'))
L.append('\\midrule')
L.append('\\multicolumn{4}{@{}l}{$T_{\\rm eff}$ class$^{a}$ (%d searched; %d '
         'census)} \\\\' % (n_smp_t, n_ref_t))
for lab, c, pc, s, ps, rr in teff_panel:
    L.append('\\quad %s & %d (%s\\%%) & %d (%s\\%%) & %s \\\\'
             % (lab, c, fmt_pct(pc), s, fmt_pct(ps),
                ('%.1f' % rr) if rr else '--'))
L.append('\\midrule')
L.append('\\multicolumn{4}{@{}l}{Other axes} \\\\')
L.append('\\quad Known planet hosts$^{b}$ & %d (%s\\%%) & %d (%s\\%%) & %.1f \\\\'
         % (exo_census, fmt_pct(100.0 * exo_census / len(ranked)),
            exo_sample, fmt_pct(100.0 * exo_sample / len(stars)),
            (100.0 * exo_sample / len(stars)) / (100.0 * exo_census / len(ranked))))
L.append('\\quad Searched stars / systems & -- & %d / %d & -- \\\\'
         % (len(stars), len(systems)))
L.append('\\bottomrule')
L.append('\\end{tabular}')
L.append('')
L.append('\\smallskip')
L.append('{\\footnotesize $^{a}$Bins are temperature bins, not MK types: '
         'A $\\ge7500$, F 6000--7500, G 5300--6000, K 3900--5300, '
         'M $<3900$\\,K. Gaia \\texttt{teff\\_gspphot} is unavailable for '
         'about half the reference census, preferentially for the coolest and '
         'faintest objects, so the census M fraction is a lower limit and the '
         'earlier-type ratios are correspondingly upper limits. White dwarfs '
         'are not separable in this parameterisation and fall wherever their '
         '(unreliable) photometric temperature places them.\\\\ '
         '$^{b}$The Gaia reference census carries no planet information; the '
         'census column here is instead the %d-entry ALMA-covered census, of '
         'which %d entries are known planet hosts. The %d searched stars '
         'include %d hosts of %d known planets.}'
         % (len(ranked), exo_census, len(stars), exo_sample, npl_sample))
_mrow = [row for row in teff_panel if row[0].startswith('M ')][0]
with open(os.path.join(HERE, 'survey_numbers_round43.tex'), 'w') as _fh:
    _fh.write('%% GENERATED by make_tables_v328.py -- do not hand-edit.\n')
    _fh.write('\\newcommand{\\MPctSample}{%.0f}\n' % _mrow[4])
    _fh.write('\\newcommand{\\MPctCensus}{%.0f}\n' % _mrow[2])
    _fh.write('\\newcommand{\\MNSample}{%d}\n' % _mrow[3])
    _fh.write('\\newcommand{\\MNCensus}{%d}\n' % _mrow[1])
    _fh.write('\\newcommand{\\NTeffSample}{%d}\n' % n_smp_t)
    _fh.write('\\newcommand{\\NTeffCensus}{%d}\n' % n_ref_t)
    # R9: these were hand-set at 18/41 in make_numbers.py while this table
    # derived 19/42 from the same census match, and both were printed.
    _fh.write('\\newcommand{\\NExoHostsTab}{%d}\n' % exo_sample)
    _fh.write('\\newcommand{\\NExoPlanetsTab}{%d}\n' % npl_sample)
    # v4.05 (R2-4): the flag-based figures the paper printed through v4.04,
    # kept so the correction can be stated as a correction, and the stricter
    # count on the deuterium-burning criterion.
    _fh.write('\\newcommand{\\NExoHostsFlag}{%d}\n' % _exo_sample_flag)
    _fh.write('\\newcommand{\\NExoPlanetsFlag}{%d}\n' % _npl_sample_flag)
    _fh.write('\\newcommand{\\NExoHostsStrict}{%d}\n' % NUM['exo_hosts_strict'])
    _fh.write('\\newcommand{\\NExoPlanetsStrict}{%d}\n'
              % NUM['exo_planets_strict'])
    _fh.write('\\newcommand{\\NExoBlankFlag}{%d}\n' % _n_blank_flag)
    _fh.write('\\newcommand{\\NExoCensusRows}{%d}\n' % len(ranked))
    _fh.write('\\newcommand{\\NExoAboveDbl}{%d}\n'
              % len(NUM['exo_hosts_above_dbl']))
    _fh.write('\\newcommand{\\ExoJoinMaxSep}{%.0f}\n'
              % NUM['exo_host_join_max_sep_arcsec'])
    _fh.write('\\newcommand{\\ExoJoinNextSep}{%.0f}\n'
              % NUM['exo_host_join_second_max_sep_arcsec'])

L.append('\\end{table}')
_seltxt = '\n'.join(L) + '\n'
open(os.path.join(TAB, 'tab_selection.tex'), 'w').write(_seltxt)
# ★ and the top level, because `\input{tab_selection}` resolves THERE: TeX
# does not search `tables/`.  Writing only the subdirectory copy left a
# stale top-level file as the one actually typeset -- a shadow, invisible
# while the two agreed.  Both are written from one string, so they cannot
# drift; `fragstale.py` S4 requires them to stay byte-identical.
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  'tab_selection.tex'), 'w').write(_seltxt)

# ---------------------------------------------------------------------------
# 6.  TABLE 2 -- per-band survey characterisation
# ---------------------------------------------------------------------------
bands = sorted({r['band_x'] for r in good})
band_rows = []
for b in list(bands) + [None]:
    ws = good if b is None else [r for r in good if r['band_x'] == b]
    cw = [r['chanw'] / 1e6 for r in ws]
    dc = [drift_ceiling(r) for r in ws]
    u, nint = merged_union(ws)
    band_rows.append({
        'band': ('All' if b is None else str(b)),
        'systems': len({sysn(r['star_name']) for r in ws}),
        'eb': len({r['eb'] for r in ws}),
        'win': len(ws),
        'chanw_med_MHz': st.median(cw),
        'chanw_lo_MHz': min(cw), 'chanw_hi_MHz': max(cw),
        'union_GHz': u, 'union_intervals': nint,
        'eirp_med_W': st.median(r['eirp'] for r in ws),
        'drift_lo': min(dc), 'drift_hi': max(dc),
    })
NUM['per_band'] = band_rows


def _round_half_up(v, nd):
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(1).scaleb(-nd)
    return str(Decimal(repr(v)).quantize(q, rounding=ROUND_HALF_UP))


def cw_fmt(v):
    # half-up so that 15.625 MHz prints as 15.63, as elsewhere in the paper
    return _round_half_up(v, 3) if v < 1 else _round_half_up(v, 2)


def cw_range(lo, hi):
    a, b = cw_fmt(lo), cw_fmt(hi)
    return a if a == b else '%s--%s' % (a, b)


def dr_range(lo, hi):
    a, b = '%.1f' % lo, '%.1f' % hi
    return a if a == b else '%s--%s' % (a, b)


B = []
B.append('% Generated by make_tables_v328.py -- do not edit by hand.')
# two-column layout (v3.61): eight columns do not fit one 3.3-inch column
B.append('\\begin{table*}')
B.append('\\centering')
B.append('\\scriptsize')
B.append('\\setlength{\\tabcolsep}{4pt}')
B.append('\\caption{Per-band survey characterisation of the %d searched '
         'windows. ``Sys.\'\' counts unique stellar systems searched in the '
         'band, so a system observed in two bands is counted in both rows '
         '(%d systems, %d stars in total); ``EBs\'\' the contributing '
         'execution blocks, attributed by the provenance of the de-duplicated '
         'windows; $\\Delta\\nu_{\\rm ch}$ the '
         'native channel width in MHz (median, range in brackets); '
         '``Union\'\' the unique sky frequency searched in the band after '
         'merging overlapping windows; EIRP$_{5\\sigma}$ the median nominal '
         'threshold across the band\'s windows; $\\dot{\\nu}_{\\rm ceil}$ the '
         'range of drift-rate ceilings in Hz\\,s$^{-1}$ per GHz of carrier '
         'frequency. The ``All\'\' row is computed over the whole sample, not '
         'summed down the columns: EBs and systems recur across bands and the '
         'frequency unions are disjoint by construction.}'
         % (len(good), len(systems), len(stars)))
B.append('\\label{tab:perband}')
B.append('\\begin{tabular}{@{}c r r r l r r r@{}}')
B.append('\\hline')
B.append('Band & Sys. & EBs & Win. & $\\Delta\\nu_{\\rm ch}$ (MHz) & '
         'Union (GHz) & Med.\\ EIRP$_{5\\sigma}$ (W) & '
         '$\\dot{\\nu}_{\\rm ceil}$ \\\\')
B.append('\\hline')
for i, r in enumerate(band_rows):
    if r['band'] == 'All':
        B.append('\\hline')
    rng = cw_range(r['chanw_lo_MHz'], r['chanw_hi_MHz'])
    cwtxt = (cw_fmt(r['chanw_med_MHz']) if rng == cw_fmt(r['chanw_med_MHz'])
             else '%s (%s)' % (cw_fmt(r['chanw_med_MHz']), rng))
    B.append('%s & %d & %d & %d & %s & %.1f & %s & %s \\\\'
             % (r['band'], r['systems'], r['eb'], r['win'], cwtxt,
                r['union_GHz'], esci(r['eirp_med_W']),
                dr_range(r['drift_lo'], r['drift_hi'])))
B.append('\\hline')
B.append('\\end{tabular}')
B.append('\\end{table*}')
open(os.path.join(TAB, 'tab_perband.tex'), 'w').write('\n'.join(B) + '\n')

# ---------------------------------------------------------------------------
# 7.  TABLE 3 -- per-star summary
# ---------------------------------------------------------------------------
per_star = []
for s in stars:
    ws = [r for r in good if _canon(r['star_name']) == s]   # v3.85: canonical
    per_star.append({
        'star': s,
        'dist_pc': ws[0]['dist_pc'],
        'bands': ','.join(str(b) for b in sorted({r['band_x'] for r in ws})),
        'n_win': len(ws),
        'eirp_best_W': min(r['eirp'] for r in ws),
    })
per_star.sort(key=lambda x: (x['dist_pc'], x['star']))
NUM['per_star'] = per_star
NUM['per_star_n'] = len(per_star)
NUM['per_star_eirp_best_overall'] = min(x['eirp_best_W'] for x in per_star)
NUM['per_star_deepest'] = min(per_star, key=lambda x: x['eirp_best_W'])['star']

half = (len(per_star) + 1) // 2
left, right = per_star[:half], per_star[half:]
while len(right) < len(left):
    right.append(None)

S = []
S.append('% Generated by make_tables_v328.py -- do not edit by hand.')
S.append('\\begin{table*}')
S.append('\\centering')
S.append('\\scriptsize')
S.append('\\setlength{\\tabcolsep}{3pt}')
S.append('\\caption{One row per searched star, ordered by distance; the table '
         'is split into two side-by-side blocks that read down the left block '
         'and then down the right. $d$ is the distance used by the search; '
         '``Bands\'\' lists the ALMA bands in which that star has at least one '
         'searched window; $N_{\\rm w}$ is the number of searched windows; '
         'EIRP$_{5\\sigma}$ is the deepest (smallest) nominal $5\\sigma$ '
         'threshold of any of those windows, in W. Star names are the '
         'identifiers used in the released machine-readable table '
         '(\\texttt{per\\_target\\_results\\_v3.28.csv}) and cross-reference it '
         'directly. %d stars, %d independent systems, %d searched windows; '
         'de-duplicated, noise-defect and withheld windows are excluded here '
         'but are present, and labelled, in the released file.}'
         % (len(stars), len(systems), len(good)))
S.append('\\label{tab:starsummary}')
NAMECOL = '>{\\raggedright\\arraybackslash}p{0.27\\textwidth}'
S.append('\\begin{tabular}{@{}%srlrr@{\\hspace{1.2em}}%srlrr@{}}'
         % (NAMECOL, NAMECOL))
S.append('\\hline')
S.append('Star & $d$ (pc) & Bands & $N_{\\rm w}$ & EIRP$_{5\\sigma}$ & '
         'Star & $d$ (pc) & Bands & $N_{\\rm w}$ & EIRP$_{5\\sigma}$ \\\\')
S.append('\\hline')
for a, b in zip(left, right):
    def cell(x):
        if x is None:
            return ' & & & & '
        return '%s & %.2f & %s & %d & %s' % (tex_escape(_desig(x['star'],
                                                                 tex=False)),
                                             x['dist_pc'], x['bands'],
                                             x['n_win'],
                                             eplain(x['eirp_best_W']))
    S.append('%s & %s \\\\' % (cell(a), cell(b)))
S.append('\\hline')
S.append('\\end{tabular}')
S.append('\\end{table*}')
open(os.path.join(TAB, 'tab_perstar.tex'), 'w').write('\n'.join(S) + '\n')

# ---------------------------------------------------------------------------
# 8.  released machine-readable master table (all 448 extracted windows)
# ---------------------------------------------------------------------------
DISPOSITION = {
    ('bet Pic', 3): 'circumstellar CO',
    ('bet Pic', 6): 'circumstellar CO',
    ('HD 48370', 6): 'CO cloud emission',
    ('CP-72 2713', 7): 'control-ensemble background',
}

COLS = ['star_name', 'system', 'band', 'eb', 'dist_pc', 'flo_GHz', 'fhi_GHz',
        'chanw_Hz', 'bandwidth_Hz', 'on_source_s', 'n_ant', 'rms_mJy',
        'smin_mJy', 'eirp_5sigma_W', 'drift_max_Hz_s', 'n_drift_trials',
        'resolution_class', 'star_snr', 'ctrl_max_snr', 'n_ctrl',
        'n_ctrl_ge_star', 'p_rank_addone', 'nearest_line', 'line_offset_MHz',
        'line_offset_kms', 'hit', 'spatially_significant', 'qa_status',
        'disposition']

out = []
n_disp = 0
for r in rows:
    ca = r['ctrl_all'] or []
    cmax = max(ca) if ca else r['ctrl_max']
    nge = sum(1 for c in ca if c >= r['star_snr'])
    p = (1 + nge) / (len(ca) + 1) if ca else None
    hit = r['star_snr'] >= 5.0
    sig = r['star_snr'] > cmax
    stat = qa_status(r)
    lo, hi = min(r['flo'], r['fhi']), max(r['flo'], r['fhi'])
    voff = (r['line_off'] * 1e-3 / fcen(r) * C_LIGHT
            if r['line_off'] is not None else None)
    disp = ''
    if stat == 'searched' and hit and sig:
        disp = DISPOSITION.get((r['star_name'], r['band_x']), '')
        n_disp += 1
    out.append({
        'star_name': r['star_name'], 'system': sysn(r['star_name']),
        'band': r['band_x'], 'eb': r['eb'],
        'dist_pc': '%.4f' % r['dist_pc'],
        'flo_GHz': '%.6f' % lo, 'fhi_GHz': '%.6f' % hi,
        'chanw_Hz': '%.4f' % r['chanw'], 'bandwidth_Hz': '%.1f' % r['bw'],
        'on_source_s': '%.2f' % r['onsrc'], 'n_ant': '',
        'rms_mJy': '%.6g' % r['rms'], 'smin_mJy': '%.6g' % (r['smin'] * 1e3),
        'eirp_5sigma_W': '%.6e' % r['eirp'],
        'drift_max_Hz_s': '%.4f' % r['drift_max'],
        'n_drift_trials': r['ndrift'], 'resolution_class': r['res_x'],
        'star_snr': '%.4f' % r['star_snr'], 'ctrl_max_snr': '%.4f' % cmax,
        'n_ctrl': len(ca) if ca else r['n_ctrl'], 'n_ctrl_ge_star': nge,
        'p_rank_addone': ('%.6f' % p) if p is not None else '',
        'nearest_line': r['line'] or '',
        'line_offset_MHz': ('%.4f' % r['line_off']) if r['line_off'] is not None else '',
        'line_offset_kms': ('%.2f' % voff) if voff is not None else '',
        'hit': 'True' if hit else 'False',
        'spatially_significant': 'True' if sig else 'False',
        'qa_status': stat, 'disposition': disp,
    })
out.sort(key=lambda x: (float(x['dist_pc']), x['star_name'], x['band'],
                        x['eb'], float(x['flo_GHz'])))
csv_path = os.path.join(HERE, 'per_target_results_v3.31.csv')
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(out)

NUM['csv_rows'] = len(out)
NUM['csv_status_counts'] = dict(collections.Counter(x['qa_status'] for x in out))
NUM['csv_n_hits_searched'] = sum(1 for x in out
                                 if x['qa_status'] == 'searched' and x['hit'] == 'True')
NUM['csv_n_spatially_significant_searched'] = sum(
    1 for x in out if x['qa_status'] == 'searched'
    and x['spatially_significant'] == 'True')
NUM['csv_n_joint_criterion'] = n_disp
NUM['csv_n_disposition_filled'] = sum(1 for x in out if x['disposition'])
NUM['csv_n_ctrl_ge_star_consistent'] = all(
    (not r['ctrl_all']) or
    (sum(1 for c in r['ctrl_all'] if c >= r['star_snr']) == r['n_ge_star'])
    for r in rows)

# ---------------------------------------------------------------------------
# 9.  cross-checks against survey_stats.json, and the number ledger
# ---------------------------------------------------------------------------
try:
    SS = json.load(open(os.path.join(HERE, 'survey_stats.json')))
    chk = {'n_windows': (len(good), SS['n_windows']),
           'n_stars': (len(stars), SS['n_stars']),
           'n_systems': (len(systems), SS['n_systems']),
           'n_starbands': (NUM['n_starbands'], SS['n_starbands']),
           'n_eb': (NUM['n_eb'], SS['n_eb']),
           'n_dup': (NUM['n_duplicate_rows'], SS['n_dup']),
           'n_defect': (len(defect), SS['n_defect']),
           'n_withheld': (len(withheld), SS['n_withheld']),
           'union_GHz': (round(band_rows[-1]['union_GHz'], 4),
                         round(SS['union_GHz'], 4)),
           'n_cross': (NUM['csv_n_hits_searched'], SS['n_cross']),
           'n_sbr': (NUM['csv_n_spatially_significant_searched'], SS['n_sbr']),
           'n_flagged': (n_disp, SS['n_flagged'])}
    NUM['crosscheck_vs_survey_stats'] = {k: {'tables': a, 'survey_stats': b,
                                             'agree': a == b}
                                         for k, (a, b) in chk.items()}
except FileNotFoundError:
    NUM['crosscheck_vs_survey_stats'] = 'survey_stats.json not found'

json.dump(NUM, open(os.path.join(TAB, 'table_numbers_v328.json'), 'w'),
          indent=1, default=str)

print('wrote tables/tab_selection.tex, tables/tab_perband.tex, '
      'tables/tab_perstar.tex')
print('wrote', csv_path, '(%d rows)' % len(out))
print('wrote tables/table_numbers_v328.json')
_bad = []
for k, v in NUM['crosscheck_vs_survey_stats'].items():
    print('  check %-14s tables=%-12s survey_stats=%-12s %s'
          % (k, v['tables'], v['survey_stats'], 'OK' if v['agree'] else 'MISMATCH'))
    if not v['agree']:
        _bad.append((k, v['tables'], v['survey_stats']))
# ★★ v4.09: AND NOW IT ASSERTS.  A cross-check that prints "MISMATCH" and
# exits zero is not a cross-check; n_starbands disagreed for four versions in
# exactly that way.  Both sides of every row must agree, and the raw-name
# count is kept beside the canonical one so the SIZE of the alias effect is
# visible rather than merely absent.
assert not _bad, ('make_tables_v328 disagrees with survey_stats.json on %s'
                  % _bad)
print('  check %-14s raw-name %d vs canonical %d (the alias merge)'
      % ('n_starbands', NUM['n_starbands_rawname'], NUM['n_starbands']))
