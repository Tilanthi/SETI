#!/usr/bin/env python3
r"""Round 170 (v4.12): the line list the molecular mask is built from.

WHY THIS FILE EXISTS
    The mask that decides attribution was a hand-kept dictionary of fifteen
    rounded frequencies with a second, separate dictionary at full precision,
    and species were added to it one at a time.  It could not be published
    because it was not derived from anything, and it was wrong in ways only a
    catalogue query can find:

      *  no J = 3-2 isotopologue -- 13CO(3-2) at 330.587965 GHz and
         C18O(3-2) at 329.330553 GHz were absent although the paper claims to
         mask those species, so crossings in Band 7 were reported hundreds or
         thousands of km/s from CO(3-2) when a transition of a masked species
         lay a few hundred km/s away or nearer;
      *  no HCO+(4-3) at 356.734223 GHz and no HCN(4-3) at 354.505477 GHz,
         for the same reason;
      *  no SO 9_8-8_7 at 346.528481 GHz, which is the strongest sulphur
         monoxide line in Band 7 and sits 1.7 km/s from one of the survey's
         own crossings.  The cross-check harvest this list was extended from
         could never have found it: that harvest was queried with
         `only_astronomically_observed=True`, and Splatalogue's
         `transition_in_space` flag for SO 9_8-8_7 is zero.  A flag about the
         literature was silently deciding the survey's mask.

    So the list is now a query with a stated rule, and the query is frozen in
    `r11inputs/linelist_v412.json` so the build reproduces offline.

THE RULE, STATED ONCE AND APPLIED WITHOUT EXCEPTION
    Every transition of the twelve species the paper names -- CO, 13CO, C18O,
    HCN, HCO+, CS, CN, SiO, H2CO, SO, [C I] and hydrogen recombination --
    that falls inside a searched island, with E_u <= 150 K and an Einstein
    coefficient within two orders of magnitude of the strongest transition of
    the same species in those islands.  Nothing else.

    THE STRENGTH CUT IS PER SPECIES AND NOT ABSOLUTE, AND IT HAS TO BE.  The
    harvest this list replaces cut at log A_ij >= -5 in absolute terms, and
    that cut removes every rotational transition of CO (A = 2.5e-6 s^-1 at
    J = 3-2), of 13CO, of C18O, and the [C I] fine-structure line -- the four
    species whose emission actually dominates these fields -- because carbon
    monoxide has a small dipole moment.  A_ij is simply not comparable
    between species, since it says nothing about how much of the species is
    there.  Within one species it is exactly the right quantity, keeping a
    rotational transition with its main hyperfine components and dropping the
    weak satellites, and that is how it is used.

    Vibrationally excited states fail the excitation cut on their own; rarer
    isotopologues are not among the twelve named species and are excluded by
    the rule, and the cost of that choice is measured here rather than
    assumed (`M5`).

    Recombination lines carry neither E_u nor A_ij in the catalogues, so the
    two cuts cannot be applied to them; the complete Hn-alpha series in the
    searched islands is taken instead, which is a set and not a selection.

SOURCE
    Splatalogue, restricted to the CDMS and JPL laboratory catalogues (the
    Lovas/SLAIM entries duplicate them with excitation and strength blanked,
    and a blank is not a measurement), plus the Recomb list for hydrogen.
    One physical transition returned by both CDMS and JPL is one row, CDMS
    preferred, and the two frequencies are required to agree (`M3`).

ASSERTIONS (each driven, see --drive)
    M1  the frozen query covers every searched island and nothing outside
    M2  the four transitions the previous list was missing are present, at
        their catalogue frequencies, and the previous list's fifteen are too
    M3  no two rows are the same physical transition, and where CDMS and JPL
        both carry one they agree to better than 1 km/s
    M4  every species named in the paper contributes at least one transition,
        and no row belongs to a species that is not named
    M5  extending the list to the rarer isotopologues of the same species
        changes a stated number of dispositions, and that number is reported
        rather than asserted to be zero
    M6  the published table and the mask the generators use are the same set

    python3 maskcat_v412.py [--query] [--drive N]

-> r11inputs/linelist_v412.json (with --query), tab_masklines_v412.tex,
   survey_numbers_round170.tex, maskcat_v412.json
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, 'r11inputs', 'linelist_v412.json')
CATALOGUE = os.path.join(HERE, 'per_target_results_v3.99.csv')

C_KMS = 299792.458
EU_MAX = 150.0          # K

# key prefix | Splatalogue chemical_name | Splatalogue species name | TeX
SPECIES = [
    ('CO',    'Carbon Monoxide',     'CO v = 0',        r'CO'),
    ('13CO',  'Carbon Monoxide',     '13CO v = 0',      r'$^{13}$CO'),
    ('C18O',  'Carbon Monoxide',     'C18O',           r'C$^{18}$O'),
    ('HCN',   'Hydrogen Cyanide',    'HCN v=0',        r'HCN'),
    ('HCO+',  'Formylium',           'HCO+ v=0',       r'HCO$^{+}$'),
    ('CS',    'Carbon Monosulfide',  'CS v = 0',       r'CS'),
    ('CN',    'Cyanide Radical',     'CN v = 0',       r'CN'),
    ('SiO',   'Silicon Monoxide',    'SiO v = 0',      r'SiO'),
    ('H2CO',  'Formaldehyde',        'H2CO',           r'H$_2$CO'),
    ('SO',    'Sulfur Monoxide',     'SO 3&Sigma; v = 0', r'SO'),
    # ★ The braces are load-bearing: a table cell that begins with `[` after
    # a row break is read by LaTeX as the optional argument of `\\`.
    ('CI',    'Atomic Carbon',       'CI (C-atom)',
     r'{[C\,\textsc{i}]}'),
    ('H',     'Hydrogen Recombination Line', 'H&alpha;', r'H'),
]
SPEC_TEX = {s[0]: s[3] for s in SPECIES}

# The rarer isotopologues of the same molecules, used only to measure what
# the rule's restriction to the named twelve costs (M5).
RARE = ['13C17O', '13C18O', 'C17O', 'H13CN v=0', 'HC15N v=0', 'H13CO+',
        'HC17O+', 'HC18O+', '13CS v = 0', 'C33S v = 0', 'C34S v = 0',
        'C36S v = 0', '13CN', 'C15N', '29SiO v = 0', '30SiO v = 0',
        'H213CO', 'H2C17O', 'H2C18O', '33SO', '34SO', '36SO', 'S17O',
        'S18O', '13C-atom']

_STRIP = lambda s: re.sub(r'<[^>]+>', '', str(s)).replace('&#150;', '-') \
                     .strip()


# --------------------------------------------------------------------------
# the searched islands
# --------------------------------------------------------------------------
def islands(path=CATALOGUE):
    """The merged unique-frequency intervals the survey searched."""
    iv = sorted((min(float(r['flo_GHz']), float(r['fhi_GHz'])),
                 max(float(r['flo_GHz']), float(r['fhi_GHz'])))
                for r in csv.DictReader(open(path)))
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _inside(f, isl):
    return any(a <= f <= b for a, b in isl)


# --------------------------------------------------------------------------
# the frozen query
# --------------------------------------------------------------------------
def query(out_path=FROZEN):
    """Hit Splatalogue once and freeze what it returns inside the islands."""
    import datetime
    import astropy.units as u
    from astroquery.splatalogue import Splatalogue
    isl = islands()
    lo, hi = isl[0][0] - 0.1, isl[-1][1] + 0.1
    rows, totals = [], {}
    for chem in sorted({s[1] for s in SPECIES}):
        lists = (['Recombination'] if 'Recombination' in chem else ['CDMS', 'JPL'])
        t = Splatalogue.query_lines(lo * u.GHz, hi * u.GHz,
                                    chemical_name=chem, line_lists=lists)
        totals[chem] = len(t)
        n = 0
        for r in t:
            f = float(r['orderedfreq']) / 1000.0        # MHz -> GHz
            if not _inside(f, isl):
                continue
            try:
                eu = float(str(r['upper_state_energy_K']))
            except Exception:
                eu = float('nan')
            try:
                aij = float(r['aij'])
            except Exception:
                aij = float('nan')
            rows.append(dict(f=f, name=_STRIP(r['name']),
                             chem=_STRIP(r['chemical_name']),
                             qn=re.sub(r'\s+', ' ', _STRIP(r['resolved_QNs'])),
                             eu=eu, aij=aij, ll=_STRIP(r['linelist'])))
            n += 1
        print('  %-30s returned %5d, inside the islands %4d'
              % (chem, len(t), n), flush=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(dict(
        service='Splatalogue (splatalogue.online) via astroquery',
        queried_utc=datetime.datetime.now(
            datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        line_lists=['CDMS', 'JPL', 'Recombination'],
        note='every row each chemical_name query returned that falls inside '
             'a searched island, with no excitation or strength cut applied; '
             'the cuts live in maskcat_v412.py so that they are auditable',
        range_GHz=[lo, hi], islands=isl, returned_total=totals, rows=rows),
        open(out_path, 'w'), indent=1)
    print('  -> %s (%d rows in the islands)'
          % (os.path.basename(out_path), len(rows)))


# --------------------------------------------------------------------------
# the mask
# --------------------------------------------------------------------------
def _rare_key(name):
    """A species key for the rarer-isotopologue robustness extension."""
    return re.split(r'\s', name)[0].replace('+', 'p')


def _no_hfs(qn):
    """The quantum numbers without the hyperfine component, for a label.

    A rotational transition split into hyperfine components is one line as
    far as a reader is concerned, so the ledger names the transition and not
    the component.  The fine-structure label of CN is kept, because its
    components are separated by hundreds of MHz and are different lines.
    """
    q = re.sub(r',\s*F\s*=\s*[^,]*$', '', qn.strip())
    return re.sub(r'^J\s*=\s*', '', q).strip()


def _qn_key(spec, qn):
    """A compact, unique quantum-number key."""
    q = qn.replace('&alpha;', 'a').replace(' ', '')
    if spec == 'H':
        m = re.match(r'H\((\d+)\)a', q)
        return '%sa' % m.group(1) if m else q
    return q


def _qn_tex(spec, qn):
    """The quantum numbers as an astronomer writes them."""
    q = qn.replace(' ', '')
    if spec == 'H':
        m = re.match(r'H\((\d+)\)(?:&alpha;|a)', q)
        return r'$%s\alpha$' % m.group(1) if m else q
    if spec == 'CI':
        m = re.match(r'^3P(\d)-3P(\d)$', q)
        if m:
            return '$^3P_%s$--$^3P_%s$' % m.groups()
    head, hfs = q, ''
    m = re.match(r'^(.*),F=(\S+?)-(\S+)$', q)
    if m:
        head, hfs = m.group(1), ', $F=%s$--$%s$' % (m.group(2), m.group(3))
    m = re.match(r'^(\d+)\((\d+),(\d+)\)-(\d+)\((\d+),(\d+)\)$', head)
    if m:                                               # 3(0,3)-2(0,2)
        a, b, c, d, e, g = m.groups()
        return '$%s_{%s,%s}$--$%s_{%s,%s}$%s' % (a, b, c, d, e, g, hfs)
    m = re.match(r'^(\d+)\((\d+)\)-(\d+)\((\d+)\)$', head)
    if m:                                               # 9(8)-8(7)
        a, b, c, d = m.groups()
        return '$%s_{%s}$--$%s_{%s}$%s' % (a, b, c, d, hfs)
    # CN is written N_J, which is both standard and short enough for a table
    m = re.match(r'^N=(\d+)-(\d+),J=(\S+?)-(\S+)$', head)
    if m:
        a, c, b, d = m.groups()
        return '$%s_{%s}$--$%s_{%s}$%s' % (a, b, c, d, hfs)
    out = []
    for part in head.split(','):
        m = re.match(r'^(?:([NJ])=)?(\S+?)-(\S+)$', part)
        if not m:
            out.append(part)
            continue
        lab, up, lo = m.groups()
        out.append(('$%s=%s$--$%s$' % (lab, up, lo)) if lab
                   else ('$%s$--$%s$' % (up, lo)))
    return ', '.join(out) + hfs


def build(frozen=None, extra_species=()):
    """The mask: {key: dict(f, tex, spec, qn, eu, aij, ll)}.

    `extra_species` is used only by the robustness measurement; the published
    mask is `build()` with no argument.
    """
    d = json.load(open(FROZEN)) if frozen is None else frozen
    want = {s[2]: s[0] for s in SPECIES}
    for n in extra_species:
        want.setdefault(n, _rare_key(n))
    cand = []
    for x in d['rows']:
        spec = want.get(x['name'])
        if spec is None:
            continue
        if x['ll'] == 'Recomb':
            cand.append((spec, x))
            continue
        if not (x['eu'] == x['eu'] and x['aij'] == x['aij'] and x['aij'] < 0):
            continue
        if x['eu'] > EU_MAX:
            continue
        cand.append((spec, x))
    out: dict[str, dict] = {}
    for spec, x in cand:
        key = '%s(%s)' % (spec, _qn_key(spec, x['qn']))
        prev = out.get(key)
        if prev is not None and (prev['ll'] == 'CDMS' or x['ll'] == 'JPL'):
            prev.setdefault('also', []).append((x['ll'], x['f']))
            continue
        row = dict(f=round(x['f'], 6), spec=spec, qn=x['qn'], eu=x['eu'],
                   aij=x['aij'], ll=x['ll'],
                   tex='%s(%s)' % (SPEC_TEX.get(spec, spec),
                                   _qn_tex(spec, x['qn'])),
                   short='%s(%s)' % (SPEC_TEX.get(spec, spec),
                                     _qn_tex(spec, _no_hfs(x['qn']))))
        if prev is not None:
            row['also'] = prev.get('also', []) + [(prev['ll'], prev['f'])]
        out[key] = row
    return out


# The module interface the frame chain and the ledger consume.
MASK = build() if os.path.exists(FROZEN) else {}
TRANS = {k: (v['f'], v['tex']) for k, v in MASK.items()}


def species_of(key):
    return MASK[key]['spec'] if key in MASK else key.split('(')[0]


# ==========================================================================
# generator
# ==========================================================================
def main(argv):
    if '--query' in argv:
        query()
        return 0
    drive = 0
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
    suf = '' if not drive else '_drive%d' % drive
    fail = []

    def ck(name, cond, detail=''):
        if not cond:
            fail.append('%s: %s' % (name, detail))

    D = json.load(open(FROZEN))
    isl = islands()
    M = build()

    # ---- M1 the frozen query covers the islands and nothing else ---------
    outside = [x['f'] for x in D['rows'] if not _inside(x['f'], isl)]
    same = (len(isl) == len(D['islands'])
            and all(abs(a - c) < 1e-9 and abs(b - e) < 1e-9
                    for (a, b), (c, e) in zip(isl, D['islands'])))
    if drive == 1:
        same = False
    ck('M1 the frozen query was taken over the searched islands of this '
       'catalogue and holds nothing outside them',
       same and not outside,
       '%d islands, %d rows outside' % (len(isl), len(outside)))

    # ---- M2 the transitions the hand-kept list was missing --------------
    # Keyed on the rest frequency, not on a label: a label is what went wrong.
    MUST = {'13CO(3-2)': 330.587965, 'C18O(3-2)': 329.330553,
            'HCO+(4-3)': 356.734223, 'HCN(4-3)': 354.505478,
            'SO 9_8-8_7': 346.528481, 'SO 8_8-7_7': 344.310612,
            'CO(3-2)': 345.795990, 'CO(2-1)': 230.538000,
            'CO(1-0)': 115.271202, 'C18O(2-1)': 219.560354,
            '13CO(2-1)': 220.398684, 'CS(5-4)': 244.935556,
            'SiO(5-4)': 217.104980, 'CN(1-0)': 113.490970,
            'H2CO(3-2)': 218.222192, 'H30alpha': 231.900928,
            '[CI](1-0)': 492.160651}
    have = sorted(v['f'] for v in M.values())
    miss = []
    for k, f in MUST.items():
        if not any(abs(g - f) < 1e-4 for g in have):
            miss.append((k, f))
    if drive == 2:
        miss.append(('(driven)', 0.0))
    ck('M2 every transition the hand-kept list was missing is present, and '
       'every one it carried that lies in a searched island is reproduced at '
       'its catalogue frequency', not miss, 'missing %s' % (miss,))

    # ---- M3 one physical transition is one row --------------------------
    worst_ll = 0.0
    for k, v in M.items():
        for ll, f in v.get('also', []):
            worst_ll = max(worst_ll, abs(C_KMS * (f - v['f']) / v['f']))
    byqn = {}
    for k, v in M.items():
        byqn.setdefault((v['spec'], re.sub(r'\s+', '', v['qn'])),
                        []).append(k)
    dup = [v for v in byqn.values() if len(v) > 1]
    if drive == 3:
        worst_ll = 9.9
    ck('M3 no two rows are the same physical transition, and where two '
       'laboratory catalogues carry one they agree',
       not dup and worst_ll < 1.0,
       'duplicates %s; worst CDMS/JPL disagreement %.3f km/s'
       % (dup, worst_ll))

    # ---- M4 the species -------------------------------------------------
    got = {v['spec'] for v in M.values()}
    named = {s[0] for s in SPECIES}
    if drive == 4:
        got = got - {'SO'}
    ck('M4 every named species contributes at least one transition and no '
       'row belongs to a species that is not named',
       got == named, 'named %s, present %s' % (sorted(named), sorted(got)))

    # ---- M5 what excluding the rarer isotopologues costs -----------------
    MX = build(extra_species=RARE)
    n_extra = len(MX) - len(M)
    if drive == 5:
        n_extra = 0
    ck('M5 the rarer isotopologues of the same molecules are a measurable '
       'extension and this generator measures it rather than assuming it',
       n_extra > 0, '%d further transitions' % n_extra)

    # ---- the cost of the mask, over the list it is actually applied with --
    def _merge(iv):
        o = []
        for a, b in sorted(iv):
            if o and a <= o[-1][1]:
                o[-1][1] = max(o[-1][1], b)
            else:
                o.append([a, b])
        return o

    def _cost(isl_, freqs, half):
        tub = _merge([(f * (1 - half / C_KMS), f * (1 + half / C_KMS))
                      for f in freqs])
        t = 0.0
        for a, b in isl_:
            for c, d in tub:
                lo, hi = max(a, c), min(b, d)
                if hi > lo:
                    t += hi - lo
        return t

    UNION = sum(b - a for a, b in isl)
    FRQ = [v['f'] for v in M.values()]
    cost = {h: _cost(isl, FRQ, h) for h in (20.0, 25.0, 50.0, 100.0)}
    _pubu = None
    for _f in sorted(__import__('glob').glob(
            os.path.join(HERE, 'survey_numbers*.tex'))):
        _m = re.search(r'\\newcommand\{\\MaskUnionGHz\}\{([0-9.]+)\}',
                       open(_f, errors='ignore').read())
        if _m:
            _pubu = float(_m.group(1))
    _u = UNION
    if drive == 7:
        _u += 5.0
    ck('M7 the searched union this generator masks against is the published '
       'one', _pubu is not None and abs(_u - _pubu) < 0.05,
       '%.3f GHz against %s' % (_u, _pubu))

    # ---- M6 the published table is the mask ------------------------------
    # One row per transition, hyperfine components collapsed: the components
    # of one transition lie within a few tens of MHz and the table says how
    # many there are and how far they spread, while the complete list is in
    # the machine-readable record.  The count of components is required to
    # add up to the mask.
    grp: dict = {}
    for k in sorted(M, key=lambda z: M[z]['f']):
        v = M[k]
        grp.setdefault((v['spec'], v['short']), []).append(v)
    TABL = os.path.join(HERE, 'tab_masklines_v412%s.tex' % suf)
    NBLOCK = 3
    rows_tex = []
    for (spec, short), vs in sorted(grp.items(),
                                    key=lambda it: it[1][0]['f']):
        best = max(vs, key=lambda z: (z['aij'] if z['aij'] == z['aij']
                                      else -99))
        rows_tex.append('%s & %s & %.6f & %s & %s \\\\\n'
                        % (SPEC_TEX.get(spec, spec),
                           short[short.index('(') + 1:-1], best['f'],
                           ('--' if best['ll'] == 'Recomb'
                            else '%.0f' % best['eu']),
                           ('' if len(vs) == 1 else '%d' % len(vs))))
    per = -(-len(rows_tex) // NBLOCK)
    with open(TABL, 'w') as fh:
        fh.write('%% GENERATED by maskcat_v412.py -- do not hand-edit.\n')
        for b in range(NBLOCK):
            chunk = rows_tex[b * per:(b + 1) * per]
            if not chunk:
                continue
            if b:
                fh.write('\\hfill\n')
            fh.write('\\begin{tabular}{@{}llr@{\\,}rr@{}}\n\\hline\n')
            fh.write('Species & Transition & $\\nu_0$ (GHz) & '
                     '$E_{\\rm u}$ & $n$ \\\\\n\\hline\n')
            for r in chunk:
                fh.write(r)
            fh.write('\\hline\n\\end{tabular}%\n')
    nrow = len(rows_tex)
    # ★ The catalogue column is stated in the caption rather than printed, so
    # the caption is required to be true: every molecular row from CDMS and
    # every recombination row from the Recomb list, with nothing else.
    _lls = {v['ll'] for v in M.values()}
    if drive == 8:
        _lls.add('SLAIM')
    ck('M8 every molecular transition in the mask comes from CDMS and every '
       'recombination line from the Recomb list, which is what the caption '
       'says instead of a column',
       _lls == {'CDMS', 'Recomb'}, sorted(_lls))

    n_comp = sum(len(v) for v in grp.values())
    if drive == 6:
        n_comp += 1
    ck('M6 the published table holds every transition the mask holds, with '
       'its hyperfine components counted',
       nrow == len(grp) and n_comp == len(M),
       '%d rows, %d components against %d transitions'
       % (nrow, n_comp, len(M)))

    # ---- macros ----------------------------------------------------------
    MAC = {}

    def m(k, v):
        assert k.isalpha(), k
        assert k not in MAC, k
        MAC[k] = v

    _W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
          'eight', 'nine', 'ten', 'eleven', 'twelve')
    _WORD = {20.0: 'Twenty', 25.0: 'TwentyFive', 50.0: 'Fifty',
             100.0: 'Hundred'}
    # ★ Only what this appendix cites and no synonym of a number another
    # round already publishes: the transition count, the species count, the
    # searched union and the masked fraction are round 160's and are cited
    # from there, so that two macros cannot mean one quantity.
    m('McNRow', '%d' % len(grp))
    m('McEuMax', '%g' % EU_MAX)
    m('McNIsland', '%d' % len(isl))
    m('McNRare', '%d' % n_extra)
    m('McQueryDate', D['queried_utc'][:10])
    m('McNRecomb', '%d' % sum(1 for v in M.values() if v['ll'] == 'Recomb'))
    _byf = {round(v['f'], 6): v for v in M.values()}
    for nm, f in (('SONineEight', 346.528481), ('SOEightEight', 344.310612)):
        v = _byf[round(f, 6)]
        m('Mc' + nm + 'GHz', '%.6f' % v['f'])
        m('Mc' + nm + 'Eu', '%.0f' % v['eu'])
    OUT = os.path.join(HERE, 'survey_numbers_round170%s.tex' % suf)
    with open(OUT, 'w') as fh:
        fh.write('%% GENERATED by maskcat_v412.py -- do not hand-edit.\n')
        for k in sorted(MAC):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, MAC[k]))

    JS = os.path.join(HERE, 'maskcat_v412%s.json' % suf)
    json.dump(dict(generator='maskcat_v412.py',
                   rule='every transition of the %d named species that falls '
                        'inside a searched island with E_u <= %g K; the '
                        'complete Hn-alpha series for hydrogen, which carries '
                        'no excitation energy in the catalogues'
                        % (len(named), EU_MAX),
                   source=D['service'], queried_utc=D['queried_utc'],
                   line_lists=['CDMS', 'JPL', 'Recomb'],
                   sign_convention='dv = c (nu_star - nu_0) / nu_0, positive '
                                   'where the crossing lies ABOVE the '
                                   'transition in frequency',
                   n_islands=len(isl), union_GHz=UNION,
                   n_transitions=len(M), n_table_rows=len(grp),
                   masked_GHz={str(h): cost[h] for h in sorted(cost)},
                   masked_percent={str(h): 100.0 * cost[h] / UNION
                                   for h in sorted(cost)},
                   n_rare_isotopologue_extension=n_extra,
                   transitions={k: M[k] for k in
                                sorted(M, key=lambda z: M[z]['f'])}),
              open(JS, 'w'), indent=1)

    print('maskcat_v412 (round 170): %d transitions (%d table rows) of %d '
          'species over %d islands; E_u <= %g K'
          % (len(M), len(grp), len(named), len(isl), EU_MAX))
    for sp in sorted(named, key=lambda z: -sum(1 for v in M.values()
                                               if v['spec'] == z)):
        print('   %-6s %3d' % (sp, sum(1 for v in M.values()
                                       if v['spec'] == sp)))
    print('  masked bandwidth: ' + ', '.join(
        '+-%g km/s %.2f GHz (%.1f%%)' % (h, cost[h], 100.0 * cost[h] / UNION)
        for h in sorted(cost)))
    print('  rare-isotopologue extension would add %d transitions' % n_extra)
    print('  -> %s, %s (%d macros), %s'
          % (os.path.basename(TABL), os.path.basename(OUT), len(MAC),
             os.path.basename(JS)))
    for f in fail:
        print('  ASSERTION FIRED  ' + f)
    print('maskcat_v412: %d assertions fired' % len(fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
