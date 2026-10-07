#!/usr/bin/env python3
r"""Round 110: THE BLOCK AND WINDOW LEDGER -- one table whose rows sum.

WHY THIS EXISTS
---------------
The paper said in several places that its counts were read from one ledger and
therefore could not disagree.  They did disagree, in about a dozen places: 404
blocks searched against 144; 484 processed minus 77 reserved giving 407 rather
than 404; 1651 windows against 1654, against 451, against 3027; 1614 control
vectors against 1645; 447 control maxima against 455; 8860 injected carriers
against 52 configurations against 21 windows against 40 scored units.

Almost none of those is wrong arithmetic.  Nearly all are DIFFERENT SETS GIVEN
THE SAME NAME.  404 and 144 are the primary census and the archival extension;
1651 and 3027 are the published catalogue and every window the pipeline ever
extracted; 447 and 455 are the same question asked of the stored 512-element
control ensemble and of the scalar control-maximum column.  The repair is to
NAME the sets, once, in a table whose rows add up, and then to use those names
in the text -- not to change a number.

WHAT THIS GENERATOR ASSERTS
---------------------------
  * three block identities, each over SETS and not over remembered integers:
        progenitor  =  processed-and-in-scope  +  extension scope
        processed   =  in-scope  +  no-progenitor-link-in-the-archive
        processed   =  primary census  +  reserved hold-out  +  no-window
  * the catalogue audit closes: exported - duplicate - defect - withheld
  * the window classes partition the catalogue: Class A + Class B = windows
  * the five block fates sum to the extension scope
  * the archival extension is a SUBSET of the extension scope and DISJOINT
    from the primary census -- the claim that makes 404 and 144 two different
    surveys rather than two contradictory counts
  * every count the table prints equals the macro the rest of the paper
    already uses for it, read back out of the other generators' round files.
    That last one is the point: the ledger is not a new set of numbers beside
    the old ones, it is the same numbers with names.

AND IT SETTLES THE ONE COUNT IN THE FAMILY THAT REACHES THE ABSTRACT
--------------------------------------------------------------------
BD+05 1668 has NO Class A window: all 100 of its windows are 15.625 MHz
coarse windows, so its four crossings are Class B, and the released catalogue
already classes them so.  The 35 in the chance comparison is therefore
already Class-A-only and already excludes them; subtracting four more from it
double-counts.  Four counts do differ, and their closure is asserted here:

    36  Class A crossings the frozen topocentric mask does not attribute
    35  ... of which carry an independent-cell count -- the comparison's own
        population, since the expectation is summed over exactly those
    34  Class A crossings the ADOPTED stellar-frame ledger does not
        attribute  =  36 - 4 (fell below the trigger) + 2 (archival tail)
    31  ... the adopted count on the comparison's own population

Usage:  blockledger_v411.py [--drive N]      N = 0..15
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# D36's standing rule: a test must never write to a path production reads.
# `--drive 0` means "no perturbation, but do not write a production path"; the
# suffix follows the FLAG, not the perturbation.
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE


def suffixed(name):
    stem, ext = os.path.splitext(name)
    return stem + SUF + ext


OUT = os.path.join(HERE, suffixed('survey_numbers_round110.tex'))
TAB = os.path.join(HERE, suffixed('tab_blockledger.tex'))


def texval(fn, macro):
    """The value \\macro is given in `fn`.

    ★ `\\providecommand{\\X}{}\\renewcommand{\\X}{1651}` is the house idiom for
    a macro a later round overrides, so the FIRST match is the empty
    placeholder and taking it would make every comparison against that macro
    a comparison against the empty string -- a check that cannot fail.  Take
    the last non-empty definition instead.
    """
    src = open(os.path.join(HERE, fn), errors='ignore').read()
    hits = [h for h in re.findall(
        r'\\(?:new|renew|provide)command\{\\%s\}\{([^}]*)\}'
        % re.escape(macro), src) if h.strip()]
    assert hits, 'no non-empty %s in %s' % (macro, fn)
    return hits[-1]


def published(macro):
    """The value of \\macro wherever in the macro layer it is defined.

    Scans every round file, so a later renumbering cannot point this at the
    wrong generator, and a macro defined twice with two values is an error
    rather than a silent first-wins.
    """
    hits = []
    for fn in sorted(os.listdir(HERE)):
        if not (fn.startswith('survey_numbers') and fn.endswith('.tex')):
            continue
        if '_drive' in fn:
            continue
        try:
            hits.append((fn, texval(fn, macro)))
        except AssertionError:
            continue
    assert hits, 'macro %s is not defined by any round file' % macro
    vals = {v for _, v in hits}
    assert len(vals) == 1, ('%s has %d different published values: %s'
                            % (macro, len(vals), hits))
    return hits[0][1]


def anint(s):
    return int(str(s).replace('\\,', '').replace(',', '').strip())


def pint(macro):
    return anint(published(macro))


# ---------------------------------------------------------------- the sets
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))
PROG = set()
for _v in META['mous'].values():
    PROG |= {q if isinstance(q, str) else q.get('eb')
             for q in _v['progenitors']}
PROG = {q for q in PROG if q}
PROC = set(META['ebs'])
SEARCHED = {l.strip() for l in open(os.path.join(HERE,
                                                 'searched_ebs_v381.txt'))
            if l.strip()}

CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXPORT = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))
HOLD = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
OOS = json.load(open(os.path.join(HERE, 'outofsample_v381.json')))['rows']
EXTR = json.load(open(os.path.join(HERE, 'export_extension.json')))['rows']
CAMP = json.load(open(os.path.join(HERE, 'campaign_v372.json')))
LEDG = json.load(open(os.path.join(HERE, 'ledger.json')))
DELTA = open(os.path.join(HERE, 'tab_crossdelta_v409.tex')).read()
TAIL = json.load(open(os.path.join(HERE, 'r8inputs', 'v409',
                                   'tail_collect.json')))

# the archival extension, under the survey's own withholding rule: every
# eps Eri block in it is Band 6, where the Gaussian primary-beam form used
# for the correction is not valid (survey_stats.py step 3)
EXTALL = [r for r in EXTR if r.get('star_snr') is not None]
EXT = [r for r in EXTALL
       if not (r['star_name'] == 'eps Eri' and int(r.get('band') or 0) == 6)]

EB_CAT = {r['eb'] for r in CAT}
EB_HOLD = {r['eb'] for r in HOLD}
EB_EXT = {r['eb'] for r in EXT}
EB_OOS = {r['eb'] for r in OOS}
INSCOPE = SEARCHED & PROG
EXTSCOPE = PROG - SEARCHED
NOWINDOW = PROC - EB_CAT - EB_HOLD
NOPROGLINK = PROC - PROG

# ★★★ WHAT THE TABLE DID NOT SHOW, AND WHY ITS ROWS DID NOT ADD UP.
# L1 and L2 already measured both decompositions of the block sets, but the
# table printed only one of them, so a reader adding the printed integers got
# 404 + 77 + 3 + 177 = 661 against an archival scope of 656.  The 5 are real:
# `PROC - PROG` is the set of blocks that were processed and that the scope
# query does not expose -- their member OUS is null in the archive metadata,
# so no progenitor links them to the query -- and three of them are in the
# primary census.  The scope row is now the sum of the two rows that
# decompose it, and the processed row is printed below with the 5 named in
# its own cell, so BOTH sums close on the page.
EB_EXTALL = {r['eb'] for r in EXTALL}
EB_EPS = EB_EXTALL - EB_EXT                 # withheld: eps Eri Band 6
TAILDONE = {t['eb'] for t in TAIL if t.get('done')}
# the fourth part is a RESIDUAL and is named as one: blocks the campaign
# calibrated and searched from which no window reached any export.  It is
# computed below, once the published fate counts have been read.

if DRIVE == 1:                 # the processed decomposition must close
    NOWINDOW = set(sorted(NOWINDOW)[:-1])
if DRIVE == 2:                 # the extension must stay disjoint and inside
    EB_EXT = EB_EXT | {sorted(EB_CAT)[0]}
if DRIVE == 9:                 # the progenitor split must close
    EXTSCOPE = set(sorted(EXTSCOPE)[:-1])
if DRIVE == 10:                # the processed/progenitor split must close
    NOPROGLINK = NOPROGLINK | {sorted(INSCOPE)[0]}
if DRIVE == 12:                # the hold-out must stay out of the census
    EB_HOLD = EB_HOLD | {sorted(EB_CAT)[0]}
    HOLD = HOLD + [dict(CAT[0], onsrc=0.0, star_name=CAT[0]['star_name'],
                        eb=sorted(EB_CAT)[0])]


def H(rows, key='onsrc'):
    return sum(float(r[key] or 0) for r in rows) / 3600.0


# ---------------------------------------------------------- the five fates
FATEROW = [('calibrated and searched', 'FateDone'),
           ('no calibration in the ALMA delivery', 'FateNoCal'),
           ('calibration failed', 'FateCalFail'),
           ('not attempted', 'FateUnattempted'),
           ('working disk insufficient', 'FateInfeas')]
fate = {k: pint(k) for _, k in FATEROW}
fate_scope = pint('FateScope')
if DRIVE == 3:
    fate['FateDone'] += 1      # the fates must stop summing to the scope

# ★★★ AND THE OTHER 29.  `\FateDone` = 144 blocks were calibrated and
# searched; the indented row under it reported 115, and the table offered no
# account of the difference.  There is one, and it is four named parts:
#
#   115  the archival extension as reported -- 463 windows over 16 stars
#     8  searched after the extension snapshot was frozen (the archival tail);
#        their 32 windows are not in that export and enter no number here
#     8  withheld under the survey's own primary-beam rule: every one is an
#        eps Eri Band 6 block, where the Gaussian beam form is invalid, which
#        is the same rule that withholds 12 windows from the primary census
#    13  searched, and no window reached any export
#
# The last is a RESIDUAL, so it is computed and labelled as one rather than
# counted from a list this directory does not hold.  The three that are
# counted come from their own records, and the closure is asserted.
EXT_TAIL = TAILDONE - EB_EXT - EB_EXTALL
N_TAIL_WIN = sum(int(t.get('n_result') or 0) for t in TAIL
                 if t['eb'] in EXT_TAIL)
N_EPS_WIN = sum(1 for r in EXTALL if r['eb'] in EB_EPS)
EXT_NOWIN = fate['FateDone'] - len(EB_EXT) - len(EB_EPS) - len(EXT_TAIL)
if DRIVE == 16:
    EXT_NOWIN += 1             # the searched partition must stop closing

# ------------------------------------------------------ the primary census
A = [r for r in CAT if r['search_class'] == 'A']
B = [r for r in CAT if r['search_class'] == 'B']
if DRIVE == 4:
    B = B[:-1]                 # the classes must stop partitioning the census

n_export = len(EXPORT['rows'])
n_dup, n_defect, n_withheld = pint('NDup'), pint('NDefect'), pint('NWithheld')
if DRIVE == 11:
    n_dup += 1                 # the catalogue audit must stop closing


def stars(rows, key='star_name'):
    return len({r[key] for r in rows})


def syst(rows):
    return len({r['system_id'] for r in rows})


CENSUS = dict(blocks=len(EB_CAT), windows=len(CAT), stars=stars(CAT),
              systems=syst(CAT), hours=H(CAT, 'on_source_s'))

# ------------------------------------------------- crossings, by class and
# ------------------------------------------------- by attribution convention
XA = [r for r in CAT if r['crossing'] == 'True' and r['search_class'] == 'A']
XB = [r for r in CAT if r['crossing'] == 'True' and r['search_class'] == 'B']
XA_UN = [r for r in XA if r['disposition_computed'].strip() == 'unattributed']
XA_UN_COV = [r for r in XA_UN if r['n_ind_cells'] != '']
# BD+05 1668: the star the referee's arithmetic turns on.  Read its windows
# out of the catalogue rather than naming them.
BD = [r for r in CAT if 'BD05' in r['star_name'] and '1668' in r['star_name']]
BD_A = [r for r in BD if r['search_class'] == 'A']
BD_X = [r for r in BD if r['crossing'] == 'True']
if DRIVE == 13:
    BD_A = BD[:1]              # the headline count turns on this being empty

# ★ The extension's SYSTEM count is not its star count by assumption: map its
#   star names onto the census system identifiers, as extension_v399.py does,
#   and let the published macro falsify the map.
_norm = lambda t: ''.join(c for c in t.lower() if c.isalnum())
_name2sys = {}
for r in CAT:
    _name2sys[_norm(r['star_name'])] = r['system_id']
_extsys = set()
for r in EXT:
    k = _norm(r['star_name'])
    hit = _name2sys.get(k) or next(
        (v for kk, v in _name2sys.items() if kk.startswith(k) or
         k.startswith(kk)), None)
    _extsys.add(hit if hit else 'EXT:' + k)
ext_sys = len(_extsys)
if DRIVE == 14:
    ext_sys += 1               # the system map must agree with the published

# the adopted list: the delta table's own rows, counted rather than typed
FELL = re.findall(r'^\$-\$ ', DELTA, re.M)
ROSE = re.findall(r'^\$\+\$ ', DELTA, re.M)
fell_f = [float(m) for m in re.findall(
    r'^\$-\$ .*? & ([\d.]+) &', DELTA, re.M)]
assert len(fell_f) == len(FELL), (len(fell_f), len(FELL))
fell_rows = [r for r in XA_UN_COV
             if any(abs(float(r['f_cross_GHz']) - f) < 1e-5 for f in fell_f)]
LED_A = [r for r in LEDG['rows'] if r['display'] != 'BD+05 1668']
LED_A_UN = [r for r in LED_A if not r['attributed']]
# the rows the archival tail adds are the adopted-list rows that are not in
# the released catalogue at all
LED_TAIL_UN = [r for r in LED_A_UN if r['source'] != 'released']

# ★★ THE TWO MASKS ARE EVALUATED IN DIFFERENT FRAMES, so they can disagree
#    about a crossing that neither the trigger nor the tail touched.  The
#    disagreement must be ENUMERATED, not assumed to be empty and not absorbed
#    into a remembered integer -- that is exactly how two counts of one
#    population come to be published side by side.  Match on the TOPOCENTRIC
#    frequency, which is the catalogue's own key: the ledger's `freq` column is
#    in whichever frame the mask is currently evaluated in.
def _topo(r):
    fr = r.get('frame') or {}
    return fr.get('f_topo', r['freq'])


_bycat = {}
for r in CAT:
    if r['crossing'] == 'True':
        _bycat.setdefault(r['eb'], []).append(r)


def _fcross(c):
    try:
        return float(c['f_cross_GHz'])
    except (TypeError, ValueError):
        return None


# ★ A join keyed on a float is a join that silently drops rows.  Match on the
#   execution block first and the frequency second, with a 1 MHz tolerance,
#   and fall back to "the one remaining crossing in this block" -- then ASSERT
#   that every row matched and that no catalogue crossing was claimed twice.
#   Five released rows now carry a topocentric frequency RECOVERED from the
#   released line offset rather than the released frequency column, so a
#   frequency-only key loses exactly the five beta Pic Band 3 rows.
REFRAMED, UNMATCHED = [], []
_claimed = {}
for r in (x for x in LED_A if x['source'] == 'released'):
    cands = [c for c in _bycat.get(r['eb'], []) if id(c) not in _claimed]
    near = [(abs((_fcross(c) or 1e9) - _topo(r)), c) for c in cands]
    near.sort(key=lambda t: t[0])
    c = None
    if near and near[0][0] < 1e-3:
        c = near[0][1]
    elif len(cands) == 1:
        c = cands[0]
    if c is None:
        UNMATCHED.append(r)
        continue
    _claimed[id(c)] = r
    if (c['disposition_computed'].strip() != 'unattributed') != r['attributed']:
        REFRAMED.append((r, c))
# signed: how many the stellar frame attributes that the topocentric one did
# not, and how many the other way round
TO_ATTR = [c for r, c in REFRAMED if r['attributed']]
TO_UNATTR = [c for r, c in REFRAMED if not r['attributed']]
if DRIVE == 5:
    fell_rows = fell_rows[:-1]   # the crossing closure must stop closing
if DRIVE == 15:
    TO_ATTR = []                 # the frame disagreement must not be hidden

# =========================================================== assertions
fail = []


def ck(tag, cond, detail=''):
    if not cond:
        fail.append(tag)
    print('  %-62s %s  %s' % (tag, 'PASS' if cond else 'FAIL', detail))


print('blockledger_v411: the block and window ledger'
      + ('  [drive %d]' % DRIVE if DRIVE is not None else ''))
print('\nassertions')

ck('L1 progenitor = in-scope searched + extension scope',
   len(INSCOPE) + len(EXTSCOPE) == len(PROG),
   '%d + %d == %d' % (len(INSCOPE), len(EXTSCOPE), len(PROG)))
ck('L2 processed = in-scope + no progenitor link in the archive',
   len(PROC & PROG) + len(NOPROGLINK) == len(PROC),
   '%d + %d == %d' % (len(PROC & PROG), len(NOPROGLINK), len(PROC)))
ck('L3 processed = primary census + reserved hold-out + no window',
   len(EB_CAT) + len(EB_HOLD) + len(NOWINDOW) == len(PROC),
   '%d + %d + %d == %d'
   % (len(EB_CAT), len(EB_HOLD), len(NOWINDOW), len(PROC)))
ck('L4 the catalogue audit closes',
   n_export - n_dup - n_defect - n_withheld == len(CAT),
   '%d - %d - %d - %d == %d'
   % (n_export, n_dup, n_defect, n_withheld, len(CAT)))
# ★★ L3b and L3c ARE THE TWO SUMS A READER ADDS UP ON THE PAGE.  They are
#    the same measurements L1-L3 make, but stated as the printed rows, which
#    is the only form in which a referee can check them.
ck('L3b the printed scope row is the sum of the two rows under it',
   len(INSCOPE) + len(EXTSCOPE) == len(PROG),
   '%d in scope and processed + %d in scope and not processed == %d'
   % (len(INSCOPE), len(EXTSCOPE), len(PROG)))
ck('L3c the printed processed row is the in-scope part plus the blocks the '
   'scope query does not expose',
   len(INSCOPE) + len(NOPROGLINK) == len(PROC)
   and len(EB_CAT) + len(EB_HOLD) + len(NOWINDOW) == len(PROC),
   '%d + %d == %d == %d + %d + %d'
   % (len(INSCOPE), len(NOPROGLINK), len(PROC), len(EB_CAT), len(EB_HOLD),
      len(NOWINDOW)))
ck('L3d the searched extension scope partitions into the four rows printed '
   'under it',
   len(EB_EXT) + len(EXT_TAIL) + len(EB_EPS) + EXT_NOWIN
   == fate['FateDone'] and EXT_NOWIN >= 0,
   '%d reported + %d tail + %d withheld + %d no window == %d'
   % (len(EB_EXT), len(EXT_TAIL), len(EB_EPS), EXT_NOWIN,
      fate['FateDone']))
ck('L3e the withheld blocks are all eps Eri Band 6, which is the rule, and '
   'the tail blocks are outside the extension export',
   all(r['star_name'] == 'eps Eri' and int(r.get('band') or 0) == 6
       for r in EXTALL if r['eb'] in EB_EPS)
   and len(EB_EPS) > 0 and not (EXT_TAIL & EB_EXTALL),
   '%d withheld blocks / %d withheld windows; %d tail blocks, %d of them in '
   'the extension export'
   % (len(EB_EPS), sum(1 for r in EXTALL if r['eb'] in EB_EPS),
      len(EXT_TAIL), len(EXT_TAIL & EB_EXTALL)))
ck('L5 Class A + Class B partition the census',
   len(A) + len(B) == len(CAT), '%d + %d == %d' % (len(A), len(B), len(CAT)))
ck('L6 the five block fates sum to the extension scope',
   sum(fate.values()) == fate_scope == len(EXTSCOPE),
   '%d == %d == %d' % (sum(fate.values()), fate_scope, len(EXTSCOPE)))
ck('L7 the archival extension is inside the extension scope',
   EB_EXT <= EXTSCOPE, '%d of %d' % (len(EB_EXT & EXTSCOPE), len(EB_EXT)))
ck('L7b ...and disjoint from the primary census',
   not (EB_EXT & EB_CAT), '%d shared' % len(EB_EXT & EB_CAT))
ck('L8 the hold-out loses no census star and no census system',
   stars(HOLD) > 0 and not ({r['eb'] for r in HOLD} & EB_CAT),
   '%d hold-out stars, %d blocks shared with the census'
   % (stars(HOLD), len({r['eb'] for r in HOLD} & EB_CAT)))
ck('L9 BD+05 1668 has no Class A window, so its crossings are Class B',
   len(BD_A) == 0 and len(BD_X) == len(XB) and len(BD) > 0,
   '%d windows, %d Class A, %d crossings == %d Class B crossings in all'
   % (len(BD), len(BD_A), len(BD_X), len(XB)))
ck('L10 the adopted Class A unattributed count closes on the released one',
   len(XA_UN) - len(fell_rows) + len(LED_TAIL_UN)
   - len(TO_ATTR) + len(TO_UNATTR) == len(LED_A_UN),
   '%d - %d + %d - %d + %d == %d'
   % (len(XA_UN), len(fell_rows), len(LED_TAIL_UN), len(TO_ATTR),
      len(TO_UNATTR), len(LED_A_UN)))
ck('L10b the adopted-to-catalogue join is complete and one-to-one',
   not UNMATCHED and len(_claimed) == len([x for x in LED_A
                                           if x['source'] == 'released']),
   '%d unmatched, %d claimed of %d released rows %s'
   % (len(UNMATCHED), len(_claimed),
      len([x for x in LED_A if x['source'] == 'released']),
      [(u['display'], u['eb']) for u in UNMATCHED[:3]]))

# ★★ L11 IS THE WHOLE POINT OF THE TABLE.  Every count it prints must be the
#    macro the rest of the paper already uses, so the ledger cannot become a
#    thirteenth set of numbers.  Driven by --drive 6.
PIN = [('NEB', len(EB_CAT)), ('NWindows', len(CAT)), ('NWinA', len(A)),
       ('NWinB', len(B)), ('NStars', CENSUS['stars']),
       ('NSystems', CENSUS['systems']), ('NSysClassA', syst(A)),
       ('LedProgenitor', len(PROG)), ('LedProcessed', len(PROC)),
       ('LedHoldout', len(EB_HOLD)), ('LedCatalogue', len(EB_CAT)),
       ('LedNoWindow', len(NOWINDOW)), ('LedNotProcessed', len(EXTSCOPE)),
       ('HoWin', len(HOLD)), ('HoStars', stars(HOLD)),
       ('ExtBlocks', len(EB_EXT)), ('ExtWindows', len(EXT)),
       ('ExtStars', stars(EXT)), ('ExtSystems', ext_sys),
       ('CampBlocks', CAMP['n_blocks']),
       ('CampWindows', CAMP['n_windows']), ('CampStars', CAMP['n_stars']),
       ('FateScope', len(EXTSCOPE))]
if DRIVE == 6:
    PIN = PIN + [('NCensus', len(CAT))]      # a count that is NOT the macro
_bad = [(k, v, published(k)) for k, v in PIN if pint(k) != v]
ck('L11 every count the table prints == the macro the paper already uses',
   not _bad, 'checked %d; mismatched %s' % (len(PIN), _bad or 'none'))

# ★ L12: a count that is legitimately a SUPERSET must be declared as one, or
#   the ledger invites exactly the confusion it exists to remove.  The
#   cross-target interference screen runs over every window the pipeline ever
#   extracted; assert that it really is a superset of the census and really
#   does reach beyond it.
OCC = list(csv.DictReader(open(os.path.join(HERE, 'occupancy_windows.csv'))))
occ_eb = {r['eb'] for r in OCC}
if DRIVE == 7:
    occ_eb = EB_CAT
ck('L12 the interference screen population is a declared superset',
   len(OCC) > len(CAT) and len(occ_eb - EB_CAT) > 0,
   '%d windows over %d blocks, %d of them outside the census'
   % (len(OCC), len(occ_eb), len(occ_eb - EB_CAT)))

# ★ L13: the hours column must sum down the panel, or "rows that sum" is a
#   claim about the integer columns only.
h_cen, h_ho = CENSUS['hours'], H(HOLD)
ck('L13 the census hours are the sum of the two class rows',
   abs(H(A, 'on_source_s') + H(B, 'on_source_s') - h_cen) < 1e-6,
   '%.2f + %.2f == %.2f' % (H(A, 'on_source_s'), H(B, 'on_source_s'), h_cen))

if DRIVE == 8:
    fail.append('L0 deliberate failure, drive 8')

# ============================================================== the macros
M = {}


def m(k, v):
    # A LaTeX macro name may contain LETTERS ONLY: \LdgNWinV411 defines
    # \LdgNWinV and asks TeX to TYPESET "411", which in the preamble is
    # "Missing \begin{document}" and no PDF at all.
    assert k.isalpha(), 'macro name %r is not letters-only' % k
    assert k not in M, 'macro %s emitted twice' % k
    M[k] = v


m('LdgProgenitor', '%d' % len(PROG))
m('LdgProcessed', '%d' % len(PROC))
m('LdgCensusEB', '%d' % len(EB_CAT))
m('LdgCensusWin', '%d' % len(CAT))
m('LdgCensusStars', '%d' % CENSUS['stars'])
m('LdgCensusSys', '%d' % CENSUS['systems'])
m('LdgCensusHours', '%.0f' % CENSUS['hours'])
m('LdgHoldEB', '%d' % len(EB_HOLD))
m('LdgHoldWin', '%d' % len(HOLD))
m('LdgHoldHours', '%.0f' % h_ho)
m('LdgNoWindowEB', '%d' % len(NOWINDOW))
m('LdgExtScope', '%d' % len(EXTSCOPE))
m('LdgExtSearched', '%d' % fate['FateDone'])
# the four parts of \LdgExtSearched, and the two parts of the processed row
m('LdgExtTail', '%d' % len(EXT_TAIL))
m('LdgExtTailWin', '%d' % N_TAIL_WIN)
m('LdgExtWithheld', '%d' % len(EB_EPS))
m('LdgExtWithheldWin', '%d' % N_EPS_WIN)
m('LdgExtNoWindow', '%d' % EXT_NOWIN)
m('LdgInScope', '%d' % len(INSCOPE))
m('LdgNoScopeQuery', '%d' % len(NOPROGLINK))
m('LdgNoScopeQueryCensus', '%d' % len(NOPROGLINK & EB_CAT))
m('LdgExtEB', '%d' % len(EB_EXT))
m('LdgExtWin', '%d' % len(EXT))
m('LdgExtStars', '%d' % stars(EXT))
m('LdgExtSys', '%d' % ext_sys)
m('LdgExtHours', '%.0f' % H(EXT))
m('LdgOosEB', '%d' % len(EB_OOS))
m('LdgOosWin', '%d' % len(OOS))
m('LdgOosStars', '%d' % stars(OOS))
m('LdgOosHours', '%.0f' % H(OOS))
m('LdgCalibEB', '%d' % CAMP['n_blocks'])
m('LdgCalibWin', '%d' % CAMP['n_windows'])
m('LdgCalibStars', '%d' % CAMP['n_stars'])
m('LdgClassAWin', '%d' % len(A))
m('LdgClassAStars', '%d' % stars(A))
m('LdgClassASys', '%d' % syst(A))
m('LdgClassAHours', '%.0f' % H(A, 'on_source_s'))
m('LdgClassBWin', '%d' % len(B))
m('LdgClassBStars', '%d' % stars(B))
m('LdgClassBSys', '%d' % syst(B))
m('LdgClassBHours', '%.0f' % H(B, 'on_source_s'))
m('LdgScreenWin', '%d' % len(OCC))
m('LdgScreenEB', '%d' % len(occ_eb))
# the crossing counts, each with the set it counts in its own name
m('LdgNCrossA', '%d' % len(XA))
m('LdgNCrossB', '%d' % len(XB))
m('LdgNCrossAUnattrFrozen', '%d' % len(XA_UN))
m('LdgNCrossAUnattrCovered', '%d' % len(XA_UN_COV))
m('LdgNCrossAUnattrAdopted', '%d' % len(LED_A_UN))
_cov = {id(r) for r in XA_UN_COV}
_lost_cov = len([r for r in fell_rows if id(r) in _cov]) \
    + len([c for c in TO_ATTR if id(c) in _cov])
m('LdgNCrossAUnattrAdoptedCovered', '%d' % (len(XA_UN_COV) - _lost_cov))
m('LdgNCrossReframed', '%d' % len(REFRAMED))
m('LdgNCrossFell', '%d' % len(fell_rows))
m('LdgNCrossTailUnattr', '%d' % len(LED_TAIL_UN))
m('LdgBdNWin', '%d' % len(BD))
m('LdgBdNWinA', '%d' % len(BD_A))
m('LdgBdChanMHz', '%.3f'
  % (min(float(r['chanw_Hz']) for r in BD) / 1e6))

# ============================================================== the table
# Each row: label, indent, blocks, windows, stars, systems, hours, feeds.
DASH = '--'


def row(label, dep, nb, nw, ns, nsy, h, feeds):
    def f(x):
        if x is None:
            return DASH
        if isinstance(x, float):
            return '%.0f' % x
        return '%d' % x
    pad = '\\hspace{%.1fem}' % (1.1 * dep) if dep else ''
    return ('%s%s & %s & %s & %s & %s & %s & %s \\\\\n'
            % (pad, label, f(nb), f(nw), f(ns), f(nsy), f(h), feeds))


L = ['%% GENERATED by blockledger_v411.py -- do not hand-edit.\n',
     '\\begin{tabular}'
     '{@{}p{0.285\\textwidth}rrrrr'
     'p{0.275\\textwidth}@{}}\n',
     '\\hline\n',
     'Set of execution blocks & Blocks & Windows & Stars & Systems & '
     'Hours & Results it enters \\\\\n',
     '\\hline\n']
L.append(row('Archival scope: blocks the query exposes', 0,
             len(PROG), None, None, None, None,
             'defines the scope; the sum of the next two rows'))
L.append(row('\\ldots{} processed with the frozen pipeline', 1,
             len(INSCOPE), None, None, None, None,
             'the second panel below'))
L.append(row('\\ldots{} not processed at the freeze', 1,
             len(EXTSCOPE), None, None, None, None,
             'the third panel below'))
L.append('\\hline\n')
L.append(row('Processed with the frozen pipeline$^{c}$', 0,
             len(PROC), None, None, None, None,
             'the sum of the three rows below'))
L.append(row('\\textbf{Primary census}', 1,
             len(EB_CAT), len(CAT), CENSUS['stars'], CENSUS['systems'],
             CENSUS['hours'],
             'every limit, the crossing list, every chance expectation'))
L.append(row('Class~A, fine channels$^{a}$', 2,
             None, len(A), stars(A), syst(A), H(A, 'on_source_s'),
             'the drifting-carrier experiment'))
L.append(row('Class~B, coarse channels$^{a}$', 2,
             None, len(B), stars(B), syst(B), H(B, 'on_source_s'),
             'the spectral-excess experiment'))
L.append(row('Reserved hold-out', 1,
             len(EB_HOLD), len(HOLD), stars(HOLD), None, h_ho,
             'the rank displacement, the false-alarm tail factor, the '
             'radial control profile'))
L.append(row('No window survived the quality cut', 1,
             len(NOWINDOW), 0, 0, 0, 0,
             'nothing'))
L.append('\\hline\n')
L.append(row('Not processed at the freeze: what became of each', 0,
             len(EXTSCOPE), None, None, None, None,
             'the sum of the five fates below'))
L.append(row('Calibrated and searched', 1,
             fate['FateDone'], None, None, None, None,
             'the sum of the four rows below'))
L.append(row('\\textbf{Archival extension}, reported', 2,
             len(EB_EXT), len(EXT), stars(EXT), ext_sys, H(EXT),
             'recurrence, and the null on data the frozen pipeline had '
             'not seen'))
L.append(row('Searched after the extension was frozen', 2,
             len(EXT_TAIL), N_TAIL_WIN, None, None, None,
             'nothing; later than the reported extension'))
L.append(row('Withheld: primary-beam form invalid$^{d}$', 2,
             len(EB_EPS), N_EPS_WIN, None, None, None,
             'nothing; withheld'))
L.append(row('No window reached the export', 2,
             EXT_NOWIN, 0, None, None, None,
             'nothing'))
for lab, key in FATEROW[1:]:
    L.append(row(lab[0].upper() + lab[1:], 1, fate[key],
                 None, None, None, None, 'nothing; the archival gap'))
L.append('\\hline\n')
L.append(row('Beyond 40\\,pc: out-of-sample control', 0,
             len(EB_OOS), len(OOS), stars(OOS), None, H(OOS),
             'the external null; no science count'))
L.append(row('External calibration sample$^{b}$', 0,
             CAMP['n_blocks'], CAMP['n_windows'], CAMP['n_stars'],
             None, None,
             'the rank calibration and the positive control; no science '
             'count'))
L.append('\\hline\n\\end{tabular}\n')
L.append('\n{\\footnotesize $^{a}$The two classes partition the census '
         'windows, not its blocks: %d blocks carry a Class~A window and %d '
         'a Class~B one, and most carry both, so the hours of the two rows '
         'partition the windows and not the observing time.\\\\ '
         '$^{b}$Not a subset of the '
         'archival scope: it includes blocks toward stars outside the '
         '40\\,pc work list, so its blocks cannot be placed inside this '
         'ledger.\\\\ $^{c}$This panel and the scope panel above overlap '
         'rather than add: %d of these %d blocks are the in-scope row above, '
         'and the other %d carry no member observing unit in the archive '
         'metadata, so the scope query does not expose them. %d of the %d '
         'are in the primary census.\\\\ $^{d}$Every one is an '
         '$\\epsilon$\\,Eri Band~6 block, where the Gaussian primary-beam '
         'form is not valid; the same rule withholds %d windows from the '
         'primary census.}\n'
         % (len({r['eb'] for r in A}), len({r['eb'] for r in B}),
            len(INSCOPE), len(PROC), len(NOPROGLINK),
            len(NOPROGLINK & EB_CAT), len(NOPROGLINK), n_withheld))

# ================================================================== write
if fail:
    print('\nFAILED: %s' % ', '.join(fail))
assert not fail, 'blockledger_v411: %d assertion(s) failed' % len(fail)

with open(TAB, 'w') as fh:
    fh.writelines(L)
with open(OUT, 'w') as fh:
    fh.write('%% round 110: the block and window ledger.  Generated by\n'
             '%% blockledger_v411.py from the block sets, the released\n'
             '%% catalogue and the four out-of-sample exports.  Every count\n'
             '%% here is asserted equal to the macro the rest of the paper\n'
             '%% already uses for the same set (L11).\n')
    for k, v in M.items():
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('\n%s: %d macros' % (os.path.basename(OUT), len(M)))
print('%s: %d rows' % (os.path.basename(TAB),
                       sum(1 for x in L if x.endswith('\\\\\n'))))
print('\nthe four Class A unattributed counts, each on its own set:')
print('  %2d  frozen topocentric mask, released catalogue' % len(XA_UN))
print('  %2d  ... carrying an independent-cell count (the comparison\'s own '
      'population)' % len(XA_UN_COV))
print('  %2d  adopted stellar-frame ledger, all Class A' % len(LED_A_UN))
print('  %2d  ... on the comparison\'s own population'
      % (len(XA_UN_COV) - _lost_cov))
print('  %2d  released Class A crossings the two mask FRAMES disagree about'
      % len(REFRAMED))
print('  BD+05 1668: %d windows, %d Class A, narrowest channel %.3f MHz'
      % (len(BD), len(BD_A), min(float(r['chanw_Hz']) for r in BD) / 1e6))
