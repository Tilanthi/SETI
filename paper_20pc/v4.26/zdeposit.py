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
        m = re.match(r'\s*\\input\{(survey_numbers[A-Za-z0-9_]*)\}', ln)
        if m:
            order.append(m.group(1) + '.tex')
    out = {}
    for fn in order:
        p = os.path.join(BASE, fn)
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
assert NOT_MASKED, (
    'on this build the mask is the whole query, so the in_mask column and '
    'every clause that leans on it would be vacuous.  That is a legitimate '
    'state for an earlier convention and this generator will not silently '
    'deposit it as if the two lists differed.')


def in_mask(t):
    return t['spec'] not in NOT_MASKED
CHANCE = read_json('chance_v414.json')          # the chance comparison
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

# ★★ the atmospheric screen: the one crossing it removes, named by the record
# that removes it, with the radius and the species that did it.
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
assert len(DISAGREE) == 6, 'the two trigger readings now differ on %d rows, ' \
    'not 6 -- the deposit and the article must be checked together' % len(DISAGREE)

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
            theta_pb_arcsec=f(p['theta_pb_arcsec'], 3),
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
    "star joins stellar_sample.csv; eb joins execution_blocks.csv; "
    "(eb, nu_lo_GHz, nu_hi_GHz) joins the sensitivity tables; a crossing is "
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
     ('theta_pb_arcsec', 'arcsec', 'primary-beam FWHM recorded for this window; the compact array is identifiable by it'),
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
     ('telluric_factor', '', 'factor by which the remaining exceedances are reduced by the atmospheric screen, applied to the crossings on the same radius and in the same topocentric frame'),
     ('trigger_whole_beam', '', '1 where this window holds a threshold crossing under the adopted whole-beam statistic'),
     ('trigger_narrow_field', '', '1 where it holds one under the narrower extraction field'),
     ('trigger_flags_agree', '', '1 where the two readings agree, 0 on the six rows where they do not'),
     ('crossing_nu_topo_GHz', 'GHz', 'frequency of the adopted crossing this window holds, empty where it holds none; it can differ from the narrower field\'s own peak in the same window'),
     ('disposition', '', 'disposition carried in the crossing table, where there is one')],
    _windows()))


# ===================================================== catalogues/stellar_sample
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
                                           for c, _ in g}))))
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
     ('project_codes', '', 'ALMA project codes its blocks belong to, joined by +')],
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
        th = sorted(float(p['theta_pb_arcsec']) for _, p in g)
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
assert len(QUERY['transitions']) > len(MASK['transitions']), (
    'the query is not wider than the mask, so depositing the query as the '
    'query says nothing a reader can check')

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
     "molecular_line_matches.csv WITH in_mask = 1. The %d rows of that file "
     "the mask leaves out (%s) are not included, and including them would "
     "give a larger masked width than the article publishes. The survey "
     "constrains nothing inside the masked width."
     % (len(QUERY['transitions']) - len(MASK['transitions']),
        '/'.join(NOT_MASKED))],
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
     ('n_masked_transitions', '', 'transitions of the MASK (molecular_line_matches.csv with in_mask = 1) whose rest frequency lies inside it; the rows the mask leaves out are not counted'),
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
            window_nu_lo_GHz=f(c['nu_lo_GHz'], 6) if c else '',
            window_nu_hi_GHz=f(c['nu_hi_GHz'], 6) if c else '',
            search_class=c.get('search_class', ''),
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
     ('nu_star_GHz', 'GHz', 'the same frequency in the star rest frame'),
     ('window_nu_lo_GHz', 'GHz', 'lower edge of the window that holds it, empty for the archival-tail crossings'),
     ('window_nu_hi_GHz', 'GHz', 'upper edge of that window'),
     ('search_class', '', 'class of that window, A fine or B coarse'),
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
     ('sigma_excl', '', 'depth at which a carrier persisting at the discovery flux is excluded at the predicted cell; it tests a carrier whose stellar-frame frequency is unchanged between epochs'),
     ('disposition', '', 'disposition carried in the article\'s own crossing ledger')],
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
    ["One row per transition of the dated catalogue QUERY, which is not the "
     "same list as the attribution mask: the query is deposited whole so that "
     "it can be inspected, and in_mask says which of its rows the mask holds.",
     "The query is every transition of the named species that falls inside a "
     "searched island below the adopted upper-state energy cut, together with "
     "the hydrogen recombination series, taken from one query of the "
     "catalogues named in line_catalogue.",
     "The MASK is the query less the species named in mask_exclusion_reason "
     "(%s): %d of the %d rows, over %d species. Those %d rows carry no "
     "attribution window, so their mask_ columns are empty, and they are "
     "excluded from the masked bandwidth of frequency_coverage.csv. The "
     "article reports a crossing nearest one of them as unattributed, with "
     "its offset printed beside it."
     % ('/'.join(NOT_MASKED), len(MASK['transitions']),
        len(QUERY['transitions']),
        len({t['spec'] for t in MASK['transitions'].values()}),
        len(QUERY['transitions']) - len(MASK['transitions'])),
     "A crossing is attributed where its stellar-frame frequency lies within "
     "the adopted half-width of a transition WITH in_mask = 1. Applying the "
     "same rule to every row of the query attributes more crossings than the "
     "article reports, and code/line_mask.py measures both counts and names "
     "the difference. The identification of each individual crossing is in "
     "threshold_crossings.csv; this table is the list and the accounting, not "
     "the identification."],
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
    ["One row per threshold crossing carrying a repeat-observation "
     "measurement: what the covering repeat blocks say about it, read three "
     "ways.",
     "sigma_excl_single_cell is the depth at which a carrier persisting at the "
     "discovery flux is excluded at one predicted cell. What it tests is a "
     "carrier whose stellar-frame frequency is unchanged between epochs; every "
     "crossing here has a fitted drift, which disfavours that model, so a null "
     "at this cell bears little on an accelerating carrier.",
     "The separated columns repeat the reading over covering blocks that "
     "satisfy the confirmation criterion alone -- a different observing session "
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
     ('sigma_excl_single_cell', '', 'exclusion depth at the single predicted cell, for a carrier whose stellar-frame frequency is unchanged'),
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
    ('p90_mult_adopted', '', 'adopted multiplier from the trigger amplitude to 90 per cent completeness, from completeness_calibration.csv'),
    ('eta_px_retained', '', 'fraction of the integrations retained after the phase-centre cut'),
    ('eta_smear_adopted', '', 'adopted smearing retention for this window'),
    ('eta_smear_basis', '', 'measured where the retention was measured on this window\'s own integrations, bounded where it is a bound'),
    ('eta_beam_retained', '', 'fraction of the applied primary-beam response that the observatory\'s documented beam retains, clamped at unity'),
    ('eirp_p90_W', 'W', 'adopted 90 per cent completeness EIRP limit; equals eirp_nominal_W times p90_mult_adopted divided by the three retentions'),
    ('eirp_p90_lo_W', 'W', 'lower end of its interval: for a window with its own injection ladder this is its own measurement, and for a transferred one it is the observed spread between the injected windows, the same pair of factors on every transferred row'),
    ('eirp_p90_hi_W', 'W', 'upper end of that interval, on the same basis'),
    ('completeness_basis', '', 'injected where this window carries its own injection ladder, transferred otherwise'),
    ('trigger_whole_beam', '', '1 where the window holds a threshold crossing under the adopted statistic'),
]


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
            theta_pb_arcsec=f(p['theta_pb_arcsec'], 3),
            drift_max_Hz_s=f(c['drift_max_Hz_s'], 3),
            n_drift_trials=i(p['n_drift_trials']),
            eta_drift=f(p['eta_drift'], 4),
            c_response_smear=f(p['c_response_smear'], 4),
            eirp_nominal_W=e(p['eirp_nominal_W']),
            eirp_eff_total_W=e(p['eirp_eff_total_W']),
            p90_mult_adopted=f(p['p90_mult_adopted'], 9),
            eta_px_retained=f(p['eta_px_retained'], 10),
            eta_smear_adopted=f(p['eta_smear_adopted'], 10),
            eta_smear_basis=p['eta_smear_basis'],
            eta_beam_retained=f(p['eta_beam_retained'], 10),
            eirp_p90_W=e(p['eirp_p90_adopted_W'], 9),
            eirp_p90_lo_W=e(p['eirp_p90_adopted_lo_W'], 9),
            eirp_p90_hi_W=e(p['eirp_p90_adopted_hi_W'], 9),
            completeness_basis=p['p90_basis'],
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
     "The interval is not the same kind of quantity on every row. On a window "
     "with its own injection ladder it is that window measurement; on a "
     "transferred window it is the observed spread between the injected "
     "windows, so it is the same pair of factors on every such row and is not a "
     "bound measured in that window\'s own band and channelisation.",
     "The limit is an EIRP at 90 per cent completeness for a carrier inside the "
     "searched drift range. It constrains nothing about a transmitter whose "
     "apparent acceleration exceeds that range."],
    "(eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv and "
    "control_field_statistics.csv; target_id joins stellar_sample.csv.",
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
    "(eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv; target_id joins "
    "stellar_sample.csv.",
    SENS_COLS, _sens('B')))


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
    "(eb, window_nu_lo_GHz, window_nu_hi_GHz) joins the sensitivity tables and "
    "spectral_windows.csv. One window is shared by two extraction positions; "
    "its rows carry the window and leave target_id and star empty rather than "
    "assign the trial to one of them.",
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
    mult = {}
    for c, p in CATK:
        mult.setdefault(c['search_class'], set()).add(p['p90_mult_adopted'])
    for cls, v in mult.items():
        assert len(v) == 1, 'class %s carries %d multipliers' % (cls, len(v))
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
            theta_pb_arcsec=f(p['theta_pb_arcsec'], 3),
            ring_r_in_arcsec=f(p['r_in_arcsec'], 3),
            ring_r_out_arcsec=f(p['r_out_arcsec'], 3),
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
     "The control positions lie in an annulus placed in each window\'s own "
     "synthesised and primary beams, so that none sits on the star and all lie "
     "inside the field the statistic is defined over. ring_r_in_arcsec and "
     "ring_r_out_arcsec are that annulus for the window.",
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
    "(eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv and the sensitivity "
    "tables.",
    [('star', '', 'star designation'),
     ('target_id', '', 'identifier the window was extracted under'),
     ('eb', '', 'ALMA execution block identifier'),
     ('project_code', '', 'its ALMA project code'),
     ('nu_lo_GHz', 'GHz', 'lower edge of the window'),
     ('nu_hi_GHz', 'GHz', 'upper edge of the window'),
     ('search_class', '', 'A fine or B coarse'),
     ('rms_mJy', 'mJy', 'per-channel noise at the stellar position'),
     ('theta_pb_arcsec', 'arcsec', 'recorded primary-beam FWHM'),
     ('ring_r_in_arcsec', 'arcsec', 'inner radius of the control annulus'),
     ('ring_r_out_arcsec', 'arcsec', 'outer radius of the control annulus'),
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
    return [dict(row=r['row'], count=deref(r['count']), value=r['value'],
                 what_it_counts=deref(r['what_it_counts']),
                 in_article=r['in_article']) for r in CNT]


TABLES.append(Table(
    'catalogues/count_accounting.csv',
    ["The master accounting of the survey: one row per published count, with "
     "the sub-counts each one partitions into.",
     "Every count in the article appears here, and so do the itemised rows the "
     "article does not have room for; in_article records which is which.",
     "The indented row numbers are a partition: the sub-rows of a row sum to "
     "it. Where a count appears under two parents the note says so, because a "
     "count that is reached by two routes and does not agree is a defect and "
     "not a nuance."],
    "the crossing counts are the rows of threshold_crossings.csv under the "
    "selections the notes give; the window counts are those of "
    "spectral_windows.csv.",
    [('row', '', 'row number; the sub-rows of a row partition it'),
     ('count', '', 'what is counted'),
     ('value', '', 'the published value'),
     ('what_it_counts', '', 'the qualification that travels with the count'),
     ('in_article', '', '1 where the article prints this row, 0 where it is itemisation the article has no room for')],
    _counts()))


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
FIGSRC = [
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
    ('frequency coverage per star', '',
     'the frequency intervals searched toward each star, one row per star, '
     'ordered by distance',
     'catalogues/spectral_windows.csv; catalogues/stellar_sample.csv',
     'star; nu_lo_GHz; nu_hi_GHz; search_class; dist_pc'),
    ('drift rate and acceleration searched', '',
     'the largest drift rate searched in each window against the '
     'line-of-sight acceleration it corresponds to',
     'catalogues/spectral_windows.csv',
     'drift_max_Hz_s; a_max_m_s2; chan_width_Hz; search_class'),
    ('the selection chain', '',
     'the counts at each stage of the search, from the archival scope to the '
     'crossings reported',
     'catalogues/count_accounting.csv',
     'row; count; value'),
    ('completeness by control-ring stratum', '',
     'the recovered fraction against injected amplitude, split by the '
     'stratifying rule on the brightest control position',
     'sensitivity/injection_recovery.csv; '
     'sensitivity/completeness_calibration.csv',
     'amp_sigma; detected; and the stratum rules of '
     'completeness_calibration.csv'),
    ('fine-channel sensitivity', '',
     'the distribution of the fine-channel EIRP limits, by band and by star',
     'sensitivity/class_A_limits.csv',
     'eirp_p90_W; eirp_nominal_W; band; star; dist_pc'),
    ('the threshold crossings', '',
     'every threshold crossing in frequency and statistic, with its '
     'disposition and its offset from the nearest masked transition',
     'candidates/threshold_crossings.csv; candidates/molecular_line_matches.csv',
     'nu_star_GHz; T_star; attributed; masked_dv_kms; disposition'),
    ('confirmation coverage', '',
     'for each system, the frequency coverage available for a repeat reading '
     'in a separated observing session',
     'candidates/recurrence_tests.csv; catalogues/stellar_sample.csv; '
     'catalogues/execution_blocks.csv',
     'n_rep_separated; dt_min_d; dt_max_d; system; date_utc'),
    ('completeness over the searched plane', '',
     'the completeness of the survey over frequency and EIRP, as the windows '
     'cover it',
     'catalogues/spectral_windows.csv; sensitivity/class_A_limits.csv; '
     'sensitivity/completeness_calibration.csv',
     'nu_lo_GHz; nu_hi_GHz; eirp_p90_W; p90_mult_adopted'),
    ('the control ring of one resolved disc', '',
     'the statistic at the star and at the control positions of the windows '
     'of one resolved debris disc, where the ring lies on real emission',
     'statistics/control_field_statistics.csv; '
     'candidates/threshold_crossings.csv',
     'T_star; T_ctrl_max; n_ctrl_ge_star; ring_r_in_arcsec; ring_r_out_arcsec'),
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
    ('search_statistic.py',
     'the search statistic of the published equation: the drift-aligned, '
     'inverse-variance-weighted stack, its noise scale, and the maximum over '
     'the channel-by-drift grid'),
    ('control_positions.py',
     'the control-position generator: the annulus, scaled to each window\'s own '
     'primary beam, drawn uniform in area from a fixed seed'),
    ('injection_recovery.py',
     'the injection-recovery harness: the deposition of a drifting carrier '
     'through the channel response at a random sub-channel phase, the '
     'reading, and the completeness curve'),
    ('line_mask.py',
     'the attribution mask: the stellar-frame offset of a crossing from a '
     'catalogued transition, and the half-width test'),
]


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
    p = os.path.join(root, 'documentation/column_descriptions.md')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as fh:
        fh.write('\n'.join(out).rstrip() + '\n')


README = """# {title}

This archive holds the machine-readable data behind an archival search for
narrow-band radio technosignatures toward stars within 40 pc, carried out on
public ALMA observations. It is the supporting data for the article; the
article holds the method, the reasoning and the conclusions, and is the place
to read what these tables mean.

**Cite this archive as:** {citation}

Every row here can be traced back to an observation in the ALMA Science
Archive. The execution-block identifier and the ALMA project code travel with
the row, and the project code is cited as `ADS/JAO.ALMA#` followed by its
value.

## What is here

```
{tree}
```

`documentation/column_descriptions.md` describes every file and every column,
with units. Each `.csv` is comma-separated with one header row, and the
documentation and the files are generated from one specification, so they
cannot disagree about what a column is.

**There is deliberately no separate methods document here. The article is that
document**, and it is the only account of the methods: a second description of
them inside the deposit would create a second place for them to disagree with
the first, which is the one failure this archive is designed not to have. Where
a definition is needed to use a column, `documentation/column_descriptions.md`
gives it and names the quantity the article prints; where a procedure is needed,
`code/` implements it.

The tables join on the identifiers rather than on row order:

* a **window** is (`eb`, `nu_lo_GHz`, `nu_hi_GHz`) -- its execution block and
  its frequency edges;
* a **position** is `target_id`, which distinguishes the components of a pair
  observed in one block, and `star` is the designation the components of a
  pair share;
* a **crossing** is (`eb`, `nu_topo_GHz`);
* a crossing belongs to the window whose edges **contain** its frequency. Two
  crossings lie at a frequency the narrower field reading never reported in
  the same window, so a join on a frequency column finds neither.

## What is not here, and what follows from that

The calibrated visibilities, the per-window extracted spectra and the search
pipeline that produced them are not distributed. **This execution of the
search therefore cannot be re-run from this archive.** What the archive
supports is narrower and is worth stating exactly: the published statistical
summaries can be rebuilt from these tables, row by row, and the definitions
the search rests on can be read, run and checked against them.

Two published quantities cannot be rebuilt from these tables alone, and the
article says so where it quotes them:

1. **the interval on the chance expectation.** The expectation itself rebuilds
   from `statistics/control_field_statistics.csv` -- sum each fine-channel
   window `p_trig_ctrl`, multiply each by one minus its `mask_attr_share` and
   by its `telluric_factor`. Its interval also folds in the resampling of the
   attributed share and the sub-trigger transfer band, and the resampling is
   over quantities that are not per-window.
2. **the per-window completeness of the directly injected windows.** Their
   injection was made into the retained per-integration spectra of real
   windows, and those spectra are not here. The trials of one campaign are
   deposited in `sensitivity/injection_recovery.csv`, and the calibration
   carried to every other window is in
   `sensitivity/completeness_calibration.csv`, but the measurement cannot be
   repeated from this archive.

## The code

`code/` holds four short programs. They are **reference implementations of the
published definitions**, written so that the definitions can be read, run and
checked against the tables deposited beside them. They are **not** the
pipeline that produced the survey, they do not read visibilities, and running
them does not reproduce the survey:

{codelist}

Each runs its own known-answer tests with no arguments and needs only Python 3
with `numpy`:

```
cd code
python3 search_statistic.py --demo
python3 control_positions.py --check ../statistics/control_field_statistics.csv
python3 line_mask.py --check ../candidates/threshold_crossings.csv \\
                     ../candidates/molecular_line_matches.csv
python3 injection_recovery.py --compare ../sensitivity/injection_recovery.csv
```

Two of those checks read the deposited tables and report whether the rule, as
implemented here, returns what the tables carry: the control annulus of every
window, and the nearest masked transition of every crossing.

## Provenance of the inputs

The observations are public ALMA data, identified by the project codes and
execution blocks in `catalogues/execution_blocks.csv`. The astrometry is
*Gaia* DR3 and the stellar systemic velocities are from SIMBAD. The line list
of `candidates/molecular_line_matches.csv` comes from one query of the
catalogues named in its `line_catalogue` column, through Splatalogue. The
external survey limits in `figures/figure_data.csv` are attributed, value by
value, to the published work they are taken from, with the rescaling applied
to each shown beside it.

## Conventions

* Frequencies are topocentric, as the correlator delivered them, except where
  a column name says `nu_star` or a description says the star rest frame.
* A velocity offset is positive where the crossing lies **above** the
  transition in frequency.
* EIRP limits are at 90 per cent completeness for a carrier inside the
  searched drift range; the survey constrains nothing about a transmitter
  whose apparent acceleration exceeds that range.
* The search statistic is an absolute signal-to-noise ratio, not a local
  contrast, and is read identically at the star and at every control position.
* Reaching the trigger is not a detection. No crossing in this survey is
  offered as a detection, and the dispositions in
  `candidates/threshold_crossings.csv` say what each one is.

## Licence

{licence}
"""


def write_readme(root, tree):
    code = '\n'.join('* `code/%s` -- %s;' % (n, d) for n, d in CODE)
    code = code.rstrip(';') + '.'
    txt = README.format(
        title=TITLE,
        citation=('White G. J. and Dey R., ' + TITLE + ', Zenodo, '
                  'doi:10.5281/zenodo.0000000. Please cite the '
                  'version-specific DOI printed on the record you downloaded, '
                  'together with the article it supports.'),
        tree=tree, codelist=code,
        licence=('Creative Commons Attribution 4.0 International (CC BY 4.0), '
                 'as recorded on the archive landing page. The external survey '
                 'limits in `figures/figure_data.csv` are the published values '
                 'of the works cited in that file and are reproduced there '
                 'with attribution.'))
    with open(os.path.join(root, 'README.md'), 'w') as fh:
        fh.write(txt)


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
import shutil
os.makedirs(os.path.join(OUT, 'code'))
for nm, _d in CODE:
    #: ★ v4.26: the four reference implementations live in `zdeposit_code/`
    #: in the version directory, not in a `code_src/` beside the generator's
    #: development tree -- the name is the deposit's, not the sandbox's.
    shutil.copy(os.path.join(HERE, 'zdeposit_code', nm),
                os.path.join(OUT, 'code', nm))

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
write_readme(OUT, '\n'.join(_lines))

print('%s' % TITLE)
for p, n in MANIFEST:
    print('  %-46s %6d rows' % (p, n))
print('  %-46s' % 'documentation/column_descriptions.md')
for nm, _d in CODE:
    print('  code/%-41s' % nm)
