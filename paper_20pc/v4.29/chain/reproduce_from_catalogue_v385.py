#!/usr/bin/env python3
"""Referee 1, point 16: reproduce every headline number from the released
catalogue alone.

The paper states that its results regenerate from the machine-readable
catalogue.  That is a claim, and a claim about reproducibility should be
executable.  This script opens ONE file --
``per_target_results_v3.99.csv`` -- and nothing else except the generated
macro files it is checking against.  It imports no analysis module and
reads no frozen export, so anything it cannot derive is something a reader
cannot derive either.

Run it after the build.  Non-zero exit if any headline number cannot be
reproduced from the file.
"""
import math
import csv, glob, os, re, sys
import collections
import statistics as st

os.chdir(os.path.dirname(os.path.abspath(__file__)))
CAT = 'per_target_results_v3.99.csv'
ROWS = list(csv.DictReader(open(CAT)))

MAC = {}
# ★★★★ v4.18: THIS READER COULD NOT SEE ROUND 103 AT ALL, AND A MACRO IT
# CANNOT SEE WAS REPORTED AS A `skip`, WHICH IS A SILENT PASS.
# It matched `\newcommand` only.  Round 103 -- the retirement-and-alias pass,
# which is where every superseded value is REPLACED and therefore where the
# paper's adopted numbers live -- writes
# `\providecommand{\X}{}\renewcommand{\X}{value}` on one line.  So the six
# headline limits this file is for were invisible to it, and repointing the
# comparison at them turned five FAILs into six skips: the gate went from
# wrong to vacuous without a word changing in its verdict line.
# ★ Both forms are read now, `\renewcommand` WINS (it is the later
# definition, which is what pdflatex typesets), and the order of files follows
# the manuscript's own `\input` order so that round 103 is applied last --
# the same rule `adopted_e90._texval` already documents.
# ★★ And REQUIRED is enforced below: a macro named in REQUIRED may not be
# skipped.  A length check that silently measures nothing reports success for
# a paper whose abstract it never saw, and this was the same species.
_order = []
_main = [f for f in sorted(os.listdir('.'))
         if f.startswith('technosignatures_') and f.endswith('.tex')]
if len(_main) == 1:
    _order = [m + '.tex' for m in re.findall(
        r'\\input\{(?:numbers/)?(survey_numbers[A-Za-z0-9_]*)\}',
        open(_main[0], errors='ignore').read())]
_have = {os.path.basename(p) for p in [_mgp for _mgp in [os.path.basename(_p) for _p in glob.glob('numbers/survey_numbers*.tex')] if '_drive' not in _mgp]}
_files = [f for f in _order if f in _have] + sorted(_have - set(_order))
for fn in _files:
    _txt = open(os.path.join('numbers', fn), errors='ignore').read()
    for m in re.finditer(r'\\newcommand\{\\([A-Za-z]+)\}\{(.*?)\}\s*$',
                         _txt, re.M):
        MAC.setdefault(m.group(1), m.group(2))
    # later definitions override, which is what TeX does
    for m in re.finditer(r'\\renewcommand\{\\([A-Za-z]+)\}\{(.*?)\}\s*$',
                         _txt, re.M):
        MAC[m.group(1)] = m.group(2)

#: macros this file EXISTS to reproduce.  A skip on one of these is a failure.
REQUIRED = ('EirpNinetyWinLoA', 'EirpNinetyWinMedA', 'EirpNinetyWinHiA',
            'EirpNinetySysLoA', 'EirpNinetySysMedA', 'EirpNinetySysHiA',
            'NCatRows', 'NWinA', 'NWinB', 'NStars', 'NSystems')

PASS, FAIL, SKIP = [], [], []


def num(x):
    """The numeric value of a macro body, including the \\times10^{} form."""
    x = x.replace('\\,', '').replace('$', '').strip()
    m = re.match(r'^([\d.]+)\\times10\^\{(-?\d+)\}$', x)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2))
    try:
        return float(x)
    except ValueError:
        return None


def printed(macro, got):
    """★★★ COMPARE AT THE PRECISION THE PAPER PRINTS, NOT INSIDE A BAND.

    The round-17 question was whether a five per cent tolerance belongs in a
    reproducer at all.  It does not, and this is why: the five per cent band
    was wide enough to hide the fact that this file was reading the
    SUPERSEDED `eirp_p90_W` column against the ADOPTED macro.  The two agreed
    to four per cent on the census as it stood, so the reproduction passed
    for as long as nobody enlarged the census.

    But tightening the band is the wrong fix too: these macros are printed to
    two significant figures, so `1.0e15` legitimately stands for anything
    from 0.95 to 1.05 -- five per cent -- and a one per cent band would fail
    on correct data.  A band cannot express "reproduces the printed number"
    at all.

    So this re-formats the derived value exactly as the macro is written and
    requires the two STRINGS to be equal.  That is both looser and tighter
    than any band in the right places: it allows the full rounding of the
    printed digit and nothing beyond it, and it is what a reproducer claims
    to do -- rebuild the number a reader sees.  Reading the wrong column
    parted the two by seven per cent, which is a different two-figure string
    and would have failed here on the census as it stood.
    """
    if macro not in MAC:
        SKIP.append('%s (macro absent -- retired or renamed)' % macro)
        return
    body = MAC[macro].replace('\\,', '').replace('$', '').strip()
    m = re.match(r'^([\d.]+)\\times10\^\{(-?\d+)\}$', body)
    if not m:
        SKIP.append('%s (not in the mantissa-exponent form this clause '
                    'compares)' % macro)
        return
    sig = len(m.group(1).replace('.', '').lstrip('0')) or 1
    e = int(math.floor(math.log10(abs(got)))) if got else 0
    mant = round(got / 10.0 ** e, sig - 1)
    if mant >= 10.0:                     # 9.97 -> 10.0 -> 1.0e+1
        mant, e = mant / 10.0, e + 1
    fmt = '%.*f' % (max(sig - 1, 0), mant)
    want = '%s\\times10^{%d}' % (m.group(1), int(m.group(2)))
    gotstr = '%s\\times10^{%d}' % (fmt, e)
    ok = gotstr == want
    (PASS if ok else FAIL).append(
        '%-22s derived %-16s macro %-16s %s'
        % (macro, gotstr, want, '' if ok else '(printed form differs)'))


def chk(macro, got, tol=0.0):
    """Compare a value derived here with the macro the paper typesets."""
    if macro not in MAC:
        SKIP.append('%s (macro absent -- retired or renamed)' % macro)
        return
    want = num(MAC[macro])
    if want is None:
        SKIP.append('%s (non-numeric)' % macro)
        return
    ok = abs(got - want) <= (tol if tol else 1e-9)
    (PASS if ok else FAIL).append('%-22s derived %-14s macro %-14s'
                                  % (macro, '%g' % got, '%g' % want))


F = lambda r, k: float(r[k]) if r[k] else None
A = [r for r in ROWS if r['search_class'] == 'A']
B = [r for r in ROWS if r['search_class'] == 'B']

# ------------------------------------------------------------- the sample
chk('NCatRows', len(ROWS))
chk('NWinA', len(A))
chk('NWinB', len(B))
chk('NStars', len({r['star_name'] for r in ROWS}))
chk('NSystems', len({r['system_id'] for r in ROWS}))
chk('NEB', len({r['eb'] for r in ROWS}))
chk('NSysClassA', len({r['system_id'] for r in A}))

# ------------------------------------------------------- the candidate list
chk('NCatFlagGlobal', sum(1 for r in ROWS if r['stage1_flag'] == 'True'))
chk('NCatFlagLocal', sum(1 for r in ROWS if r['stage1_flag_local'] == 'True'))
chk('NStageOneWin', sum(1 for r in ROWS if r['stage1_flag'] == 'True'))
chk('LocAllFlagGlobal', sum(1 for r in ROWS if r['stage1_flag'] == 'True'))
chk('LocAllFlagLocal', sum(1 for r in ROWS if r['stage1_flag_local'] == 'True'))
chk('LocAllLost', sum(1 for r in ROWS if r['stage1_flag'] == 'True'
                      and r['stage1_flag_local'] == 'False'))
chk('LocAllGained', sum(1 for r in ROWS if r['stage1_flag'] == 'False'
                        and r['stage1_flag_local'] == 'True'))

# ------------------------------------------------------------- sensitivity
# ★ v4.18: THE COLUMN READ HERE IS THE ADOPTED ONE.  It was `eirp_p90_W`, the
# trigger ratio of the twenty-one-window campaign applied to each window's
# nominal power -- a well-defined quantity, but NOT the limit this paper
# quotes, which carries the re-measured class factor and the three per-window
# retentions.  The two agreed to within this check's five per cent tolerance
# on the census as it then stood, so the reproduction passed while reproducing
# the wrong column; enlarging the census parted them by seven per cent and
# that is how it was found.  `eirp_p90_adopted_W` is the deposited published
# limit, and reproducing a headline means reproducing the number printed.
# ★★★★ v4.18: AND THE MACROS COMPARED AGAINST WERE THE SUPERSEDED FAMILY TOO.
# Fixing the COLUMN was only half of it.  This file compared its derived
# limits against \PNinetyWinBestA / MedA / WorstA and \PNinetySysBestA /
# MedA / WorstA, which `v381_calc.py` computes from `eirp_p90_W` -- the same
# superseded column this file had been reading.  So both sides of the
# comparison were the retired quantity and the reproduction passed by
# agreeing with itself; reading the adopted column alone turned it into a
# 36 per cent disagreement (8.7e13 against 6.4e13) and that is how the
# second half surfaced.
# What the paper publishes is round 103's \EirpNinety{Win,Sys}{Lo,Med,Hi}A,
# and those are the five that appear in the prose.  Reproducing a headline
# means reproducing the number a reader sees, so those are what is compared.
# ★ `v381_calc.py`'s superseded family stays as it is: it runs before the
# deposit writes `eirp_p90_adopted_W`, so it CANNOT read the adopted column,
# and `retired.py` already measures that no macro it emits from the
# superseded column is cited anywhere in the manuscript.  Recorded as an open
# item rather than moved, because moving a generator that early in the chain
# is not a change to make inside an integration pass.
_P90COL = 'eirp_p90_adopted_W'
assert _P90COL in ROWS[0], ('the deposit carries no %s column: smear_r15.py '
                            '--deposit must have run' % _P90COL)
# ★★★★ AND THE COLUMN THAT SAYS WHETHER A ROW CARRIES A LIMIT AT ALL.  A
# window every channel of which lies inside the attribution mask constrains
# nothing (Sec. \ref{sec:lines}), so it is not in the distribution of
# limits.  This file's whole purpose is that the deposited catalogue is
# sufficient on its own, so the eligibility is read from the catalogue's own
# `unmasked_fraction` column and from nowhere else -- importing the rule
# from a module would be reproducing the headline from the module.
_UMCOL = 'unmasked_fraction'
assert _UMCOL in ROWS[0], ('the deposit carries no %s column: unmask_r26.py '
                           'and smear_r15.py --deposit must have run'
                           % _UMCOL)


def _lim(r):
    """The row's limit, or None where the mask leaves it no bandwidth."""
    u = r[_UMCOL]
    if u == '' or float(u) <= 0.0:
        return None
    return F(r, _P90COL)


_nfull = sum(1 for r in A if _lim(r) is None)
assert _nfull > 0, (
    'no Class A row is wholly masked, which the mask definition and the fine '
    'channelisation make impossible: the column is not the one it claims')
p90 = sorted(v for v in (_lim(r) for r in A) if v)
printed('EirpNinetyWinLoA', p90[0])
printed('EirpNinetyWinMedA', p90[len(p90) // 2])
printed('EirpNinetyWinHiA', p90[-1])
# per system, taking each system's best window
best = {}
for r in A:
    v = _lim(r)
    if v and v < best.get(r['system_id'], float('inf')):
        best[r['system_id']] = v
bs = sorted(best.values())
# statistics.median, matching make_fig_classa_sens.py, which emits these
# macros with numpy. For the 60-system list the upper-element convention
# differs from the true median by 7 per cent -- larger than this check's
# own tolerance, so the two conventions cannot both be used.
import statistics as _st
printed('EirpNinetySysLoA', bs[0])
printed('EirpNinetySysMedA', _st.median(bs))
printed('EirpNinetySysHiA', bs[-1])

# ------------------------------------------------------------ the coverage
ivs = sorted((min(F(r, 'flo_GHz'), F(r, 'fhi_GHz')),
              max(F(r, 'flo_GHz'), F(r, 'fhi_GHz'))) for r in ROWS)
union, lo, hi = 0.0, None, None
for a, b in ivs:
    if lo is None:
        lo, hi = a, b
    elif a <= hi:
        hi = max(hi, b)
    else:
        union += hi - lo
        lo, hi = a, b
if lo is not None:
    union += hi - lo
chk('UnionGHz', union, tol=0.2)

# ------------------------------------------------------------- the geometry
chk('RingThetaMin', min(F(r, 'theta_pb_arcsec') for r in ROWS), tol=0.05)
chk('RingThetaMax', max(F(r, 'theta_pb_arcsec') for r in ROWS), tol=0.05)
chk('DistMin', min(F(r, 'dist_pc') for r in ROWS), tol=0.01)
chk('DistMax', max(F(r, 'dist_pc') for r in ROWS), tol=0.01)
chk('PctBandsSixSeven',
    100.0 * sum(1 for r in ROWS if r['band'] in ('6', '7')) / len(ROWS), tol=0.5)

# ---------------------------- quantities the round-1 self-review found stale
# Each of these was hand-typed or frozen at an earlier sample size. They are
# checked here so that the next sample change breaks the build rather than
# the paper.
chk('NHitsA', sum(1 for r in ROWS if r['crossing'] == 'True'
                  and r['search_class'] == 'A'))
chk('NHitsB', sum(1 for r in ROWS if r['crossing'] == 'True'
                  and r['search_class'] == 'B'))
chk('NSpatialA', sum(1 for r in ROWS if r['stage1_flag'] == 'True'
                     and r['search_class'] == 'A'))
_dr = [F(r, 'drift_max_Hz_s') for r in ROWS if F(r, 'drift_max_Hz_s')]
chk('DriftKHzLo', min(_dr) / 1e3, tol=0.05)
chk('DriftKHzHi', max(_dr) / 1e3, tol=0.05)
_peA = sorted(F(r, 'eirp_eff_total_W') for r in A if F(r, 'eirp_eff_total_W'))
printed('PeffWinLoA', _peA[0])
printed('PeffWinMedA', _peA[len(_peA) // 2])
printed('PeffWinHiA', _peA[-1])
_cnt = collections.Counter(r['system_id'] for r in ROWS)
chk('ConcThreeWin', sum(n for _, n in _cnt.most_common(3)))
chk('ConcThreePct', 100.0 * sum(n for _, n in _cnt.most_common(3)) / len(ROWS),
    tol=0.05)
chk('NSmearWin', sum(1 for r in ROWS if r['eta_smear']))
chk('NBandEightWin', sum(1 for r in ROWS if r['band'] == '8'))
chk('NRegionMaxFlag', sum(1 for r in ROWS
                          if r['stage1_flag_regionmax'] == 'True'))
_expo = sum(F(r, 'on_source_s') * F(r, 'bandwidth_Hz') / 1e9 for r in ROWS
            if r['on_source_s'] and r['bandwidth_Hz'])
chk('ExpoStarHrGHz', round(_expo / 3600), tol=2)
_on = sorted(F(r, 'on_source_s') for r in ROWS if F(r, 'on_source_s'))
chk('OnSrcMedWin', _on[len(_on) // 2], tol=1)

# ------------------------------------------------------------------ report
for line in PASS:
    print('  pass  %s' % line)
for line in FAIL:
    print('  FAIL  %s' % line)
for line in SKIP:
    print('  skip  %s' % line)
print('\nreproduced from %s alone: %d pass, %d FAIL, %d skipped'
      % (CAT, len(PASS), len(FAIL), len(SKIP)))
# The count must not depend on which macros retire_macros.py has dropped
# by the time this runs, or the file is not reproducible.
# NOT len(PASS): that depends on how many macros retire_macros.py has
# dropped by the time this runs, so the file would differ between an
# incremental build and a clean one. A v4.00 attempt to publish the pass
# count as well reintroduced exactly that, and the clean-regeneration test
# caught it. The retirement-independent total is the one to publish.
open('numbers/survey_numbers_round39.tex', 'w').write(
    '%% GENERATED by reproduce_from_catalogue_v385.py -- do not hand-edit.\n'
    '\\newcommand{\\NReproChecks}{%d}\n' % (len(PASS) + len(SKIP)))
# ★★ A SKIP ON A MACRO THIS FILE EXISTS FOR IS A FAILURE, NOT A NOTE.
# Pointing the six headline comparisons at the macros the paper actually
# publishes turned five FAILs into six skips, because the macro reader could
# not see round 103's `\providecommand ... \renewcommand` form -- the gate
# went from wrong to vacuous and its verdict line did not change.  The reader
# is fixed above; this clause is what makes the same thing impossible next
# time.
_missing = [n for n in REQUIRED if n not in MAC]
_skipped = [s.split()[0] for s in SKIP]
_req_skip = sorted(set(REQUIRED) & set(_skipped))
if _missing or _req_skip:
    for n in _missing:
        print('  FAIL  %-22s is REQUIRED and is not in the macro layer at '
              'all' % n)
    for n in _req_skip:
        print('  FAIL  %-22s is REQUIRED and was skipped, so it was not '
              'reproduced' % n)
    print('reproduce: %d required macro(s) not reproduced -- a skip on one of '
          'these is a silent pass' % (len(_missing) + len(_req_skip)))
sys.exit(1 if (FAIL or _missing or _req_skip) else 0)

