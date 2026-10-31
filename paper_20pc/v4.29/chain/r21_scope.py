#!/usr/bin/env python3
r"""r21_scope.py -- round 950 -> survey_numbers_round950.tex, r21_scope.json.

WHAT CLASS A IS, WHICH WINDOWS CANNOT DISCRIMINATE A DRIFT, AND WHY THE COARSE
WINDOWS THAT CAN ARE NOT IN THE PRIMARY ANALYSIS.

Both referees report the same defect: Class A is defined twice, once by
channel width (405 windows) and once by a capability that 14 of those 405 do
not have, while 38 coarse windows do have it.  The definition adopted is the
channel width; the capability is reported as a subset.  This file measures
everything the three sentences that say so need, and nothing else.

WHY CHANNEL WIDTH IS THE DEFINITION, and it is not a convention.  The two
quantities are not interchangeable:

  * The channel width sets the statistic.  A channel-confined carrier is
    diluted in proportion to the channel it lands in, so the power that
    reaches the trigger scales with the channel, and the completeness that
    converts a trigger into a limit was measured by injection separately for
    each class.  A window cannot be moved between classes without moving it
    to a calibration that was not measured on it.
  * The channelisation of the sample is bimodal with an empty gap -- the
    coarsest fine window is 1.95 MHz and the finest coarse window 7.81 MHz,
    a factor of four with nothing in between -- so the split on channel width
    is unambiguous and was fixed before the search (A2).
  * eta_drift >= 1 is necessary for drift discrimination and not sufficient.
    In the 38 coarse windows that meet it the ENTIRE searched drift range
    displaces a carrier by between 1.02 and 1.35 channels of 15.6 MHz: the
    window can register a narrow carrier but cannot tell one from a static
    line, which is the capability the primary experiment is defined by.

AND WHAT EXCLUDING THEM COSTS, measured rather than asserted: the 38 lie
toward six systems, every one of which the fine-channel search already
reaches, and not one of them holds a threshold crossing.  So no system and no
crossing enters or leaves the paper with them; what they would add is
frequency, 8.45 GHz outside the Class A union, and that is stated.

ASSERTIONS (every one driven to fail on its own, --drive 1..10)

  A1  the partition is an identity: the windows below the criterion and the
      windows above it are the published \EtaDriftAOk and \EtaDriftALo and
      they sum to \NWinA.  Pins the identity, not today's values.
  A2  the class split is a split on channel width with nothing in between:
      every Class B channel is wider than every Class A channel.
  A3  the 14 are named from their own rows: the counts in the generated
      phrase sum to the number of windows below the criterion, and the
      distinct stars in it are the distinct stars of those rows.
  A4  no system is reachable only through the coarse windows that meet the
      criterion: their systems are a subset of the Class A systems.  This is
      what licenses the sentence that excluding them loses no system.
  A5  not one of those coarse windows holds a crossing, so no crossing count
      depends on the class boundary.
  A6  the median system limit read here over all \NWinA windows reproduces
      the published \EirpNinetySysMedA, which is what makes the percentage
      change over the drift-resolving subset a measurement of the same
      quantity and not of a different read-out.
  A7  the percentage change is formed from those two medians and carries the
      direction as a word, so a sentence cannot print the number with the
      wrong sense.
  A8  the subset quantities are the published ones (\EdrNWinA, \EdrNSys,
      \EdrUnionGHz), recomputed here from the catalogue.
  A10 the two coarse strata account for the whole of Class B.
  A9  the criterion is not vacuous in either direction: some Class A windows
      fail it and some Class B windows meet it.  If either set were empty the
      distinction this file exists to draw would not need drawing.

Usage: r21_scope.py [--paper DIR] [--out DIR] [--drive N]
--drive 0 means "no perturbation, but do not write a path production reads".
"""
import csv
import collections
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 950

DRIVE = None
PAPER = HERE   # the version tree this generator lives in
OUTDIR = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--paper':
        PAPER = sys.argv[_i + 1]
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'numbers/survey_numbers_round950%s.tex' % SUF)
OUT_JSON = os.path.join(OUTDIR, 'r21_scope%s.json' % SUF)

ETA_MIN = 1.0                       # the paper's own criterion, no parameter
MACROS, FAIL = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' \
        % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), \
        name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-66s %s  %s' % (label[:66], 'PASS' if ok else 'FAIL', detail))


sys.path.insert(0, PAPER)
import adopted_e90 as ae                                        # noqa: E402

CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
CATAE = ae.catalogue(PAPER)
E90 = ae.per_window(CATAE, PAPER)


def tex(name):
    return ae._texval(name, PAPER)


def union(iv):
    """Merged disjoint intervals, min/max on the pair: a descending spectral
    window writes its edges reversed."""
    out = []
    for a, b in sorted((min(x, y), max(x, y)) for x, y in iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def band(rows):
    return sum(b - a for a, b in
               union([(float(r['flo_GHz']), float(r['fhi_GHz']))
                      for r in rows]))


def outside(rows, ref):
    """The frequency these rows cover that `ref` does not."""
    tot = 0.0
    for a, b in union([(float(r['flo_GHz']), float(r['fhi_GHz']))
                       for r in rows]):
        seg = [(a, b)]
        for c, d in union([(float(r['flo_GHz']), float(r['fhi_GHz']))
                           for r in ref]):
            nxt = []
            for x, y in seg:
                if d <= x or c >= y:
                    nxt.append((x, y))
                    continue
                if x < c:
                    nxt.append((x, min(c, y)))
                if y > d:
                    nxt.append((max(d, x), y))
            seg = nxt
        tot += sum(y - x for x, y in seg)
    return tot


print('r21_scope round %d%s' % (ROUND, '' if DRIVE is None
                                else ' (drive %d)' % DRIVE))

A = [r for r in CAT if r['search_class'] == 'A']
B = [r for r in CAT if r['search_class'] == 'B']
assert len(A) + len(B) == len(CAT), 'a window is in neither class'
A_LO = [r for r in A if float(r['eta_drift']) < ETA_MIN]
A_OK = [r for r in A if float(r['eta_drift']) >= ETA_MIN]
B_HI = [r for r in B if float(r['eta_drift']) >= ETA_MIN]
if DRIVE == 1:
    A_LO = A_LO[1:]

# =====================================================================
# 1  THE PARTITION, AND THE SPLIT THE DEFINITION IS MADE ON
# =====================================================================
print('\n1  the partition')
_pub = (int(tex('EtaDriftAOk')), int(tex('EtaDriftALo')), int(tex('NWinA')))
ck('A1 the drift-resolving subset and its complement are the published '
   'counts and they sum to the class',
   (len(A_OK), len(A_LO)) == _pub[:2] and len(A_OK) + len(A_LO) == _pub[2],
   '%d + %d = %d against %d + %d = %d published'
   % (len(A_OK), len(A_LO), len(A_OK) + len(A_LO), _pub[0], _pub[1], _pub[2]))

CW_A = [float(r['chanw_Hz']) for r in A]
CW_B = [float(r['chanw_Hz']) for r in B]
if DRIVE == 2:
    CW_B = CW_B + [min(CW_A)]
ck('A2 the split is a split on channel width with an empty gap: every '
   'coarse channel is wider than every fine one',
   min(CW_B) > max(CW_A), 'widest fine %.4f MHz, finest coarse %.4f MHz, '
   'a factor %.2f' % (max(CW_A) / 1e6, min(CW_B) / 1e6,
                      min(CW_B) / max(CW_A)))
m('ScChanFineMaxMHz', '%.2f' % (max(CW_A) / 1e6))
m('ScChanCoarseMinMHz', '%.2f' % (min(CW_B) / 1e6))
m('ScChanGapFac', '%.0f' % (min(CW_B) / max(CW_A)))

# =====================================================================
# 2  THE 14 THAT FALL BELOW, NAMED FROM THEIR OWN ROWS
# =====================================================================
print('\n2  the windows below the criterion')
BY = collections.Counter(r['star_name'] for r in A_LO)


def disp(s):
    """The paper's own spelling of a star name: the catalogue appends a Gaia
    designation for components Gaia resolves, names carry non-breaking
    spaces, a leading or embedded minus is a math minus, and the three Greek
    names are spelled as the paper spells them."""
    s = s.split('Gaia DR3')[0].strip()
    GREEK = {'eps Eri': '$\\epsilon$~Eridani',
             'eta Crv': '$\\eta$~Corvi',
             'beta Pic': '$\\beta$~Pictoris',
             'bet Pic': '$\\beta$~Pictoris'}
    if s in GREEK:
        return GREEK[s]
    s = s.replace(' ', '~').replace('-', '$-$')
    return s


WORD = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six',
        7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}
parts = ['%s toward %s' % (WORD.get(n, str(n)), disp(s))
         for s, n in sorted(BY.items(), key=lambda kv: (-kv[1], kv[0]))]
PHRASE = ', '.join(parts[:-1]) + ' and ' + parts[-1]
_sum = sum(BY.values())
if DRIVE == 3:
    _sum -= 1
ck('A3 the phrase that names them is built from their own rows and accounts '
   'for every one of them',
   _sum == len(A_LO) and len(BY) == len({r['star_name'] for r in A_LO}),
   '%d windows over %d stars' % (_sum, len(BY)))
m('ScLoNames', PHRASE)
m('ScLoNStar', '%d' % len(BY))
m('ScLoTauLoS', '%.0f' % min(float(r['on_source_s']) for r in A_LO))
m('ScLoTauHiS', '%.0f' % max(float(r['on_source_s']) for r in A_LO))
m('ScLoTauLoMin', '%.0f' % (min(float(r['on_source_s']) for r in A_LO) / 60))
m('ScLoTauHiMin', '%.0f' % (max(float(r['on_source_s']) for r in A_LO) / 60))
m('ScLoEtaLo', '%.2f' % min(float(r['eta_drift']) for r in A_LO))
m('ScLoEtaHi', '%.2f' % max(float(r['eta_drift']) for r in A_LO))
m('ScLoTauMedAllMin', '%.0f'
  % (st.median([float(r['on_source_s']) for r in A]) / 60))
print('  %s' % PHRASE)
print('  tracks %.0f-%.0f s against a class median of %.0f s; eta %.2f-%.2f'
      % (min(float(r['on_source_s']) for r in A_LO),
         max(float(r['on_source_s']) for r in A_LO),
         st.median([float(r['on_source_s']) for r in A]),
         min(float(r['eta_drift']) for r in A_LO),
         max(float(r['eta_drift']) for r in A_LO)))

# =====================================================================
# 3  THE COARSE WINDOWS THAT MEET THE CRITERION, AND WHAT THEY WOULD ADD
# =====================================================================
print('\n3  the coarse windows that meet the criterion')
SB = {r['system_id'] for r in B_HI}
SA = {r['system_id'] for r in A}
if DRIVE == 4:
    SB = set(SB) | {'__not_a_class_A_system__'}
ck('A4 no system is reachable only through them: their systems are a subset '
   'of the systems the fine-channel search already covers',
   SB <= SA, '%d systems, %d of them outside Class A'
   % (len(SB), len(SB - SA)))
_cross = [r for r in B_HI
          if str(r['crossing']).strip().lower() in ('1', 'true', 'yes')]
if DRIVE == 5:
    _cross = [B_HI[0]]
ck('A5 not one of them holds a threshold crossing, so no crossing count '
   'depends on the class boundary',
   not _cross, '%d crossings in %d windows' % (len(_cross), len(B_HI)))
B_LO = [r for r in B if float(r['eta_drift']) < ETA_MIN]
_bsum = len(B_LO) + len(B_HI)
if DRIVE == 10:
    _bsum -= 1
ck('A10 the coarse windows in which no searched drift leaves one channel and '
   'those in which it crosses one account for the whole of Class~B',
   _bsum == int(tex('NWinB')), '%d + %d = %d against %s published'
   % (len(B_LO), len(B_HI), _bsum, tex('NWinB')))
m('ScCoarseNoDrift', '%d' % len(B_LO))
m('ScBhNSys', '%d' % len(SB))
m('ScBhChanMHz', '%.3f' % (st.median([float(r['chanw_Hz'])
                                      for r in B_HI]) / 1e6))
m('ScBhEtaLo', '%.2f' % min(float(r['eta_drift']) for r in B_HI))
m('ScBhEtaHi', '%.2f' % max(float(r['eta_drift']) for r in B_HI))
m('ScBhNewBandGHz', '%.1f' % outside(B_HI, A))
m('ScBhDiluteFac', '%.0f' % (st.median([float(r['chanw_Hz']) for r in B_HI])
                             / st.median([float(r['chanw_Hz']) for r in A])))
print('  %d windows, %d systems, channels %.3f MHz, eta %.2f-%.2f, '
      '%.2f GHz outside the Class A union, %d crossings'
      % (len(B_HI), len(SB), st.median([float(r['chanw_Hz'])
                                        for r in B_HI]) / 1e6,
         min(float(r['eta_drift']) for r in B_HI),
         max(float(r['eta_drift']) for r in B_HI), outside(B_HI, A),
         len(_cross)))

# =====================================================================
# 4  WHAT THE SUBSET CHANGES: BANDWIDTH, SYSTEMS, THE MEDIAN LIMIT
# =====================================================================
print('\n4  the Class A result over the drift-resolving subset')
KEEP = [r for r in CATAE if r['search_class'] == 'A'
        and float(r['eta_drift']) >= ETA_MIN]
ALLA = [r for r in CATAE if r['search_class'] == 'A']


def sysmed(rows):
    """The median per-system limit over a window population.

    ★ COVERAGE AND LIMIT ARE TWO DIFFERENT POPULATIONS, and only the second
    is filtered here.  The subset counts above are statements about what the
    search covers, which the attribution mask does not change; a median
    LIMIT is a statement about windows that carry one, and a window every
    channel of which lies inside the mask does not (Sec. \ref{sec:lines}).
    """
    best = {}
    for r in rows:
        if not ae.limit_eligible(r, HERE):
            continue
        k = r['system_id']
        best[k] = min(best.get(k, 1e99), E90[id(r)])
    return st.median(list(best.values())), set(best), best


MED_ALL, S_ALL, BEST_ALL = sysmed(ALLA)
MED_KEEP, S_KEEP, BEST_KEEP = sysmed(KEEP)
_pubmed = tex('EirpNinetySysMedA')          # e.g. 1.5\times10^{15}
_pubval = float(_pubmed.split('\\times')[0]) * 10 ** float(
    _pubmed.split('{')[-1].rstrip('}'))
_med = MED_ALL
if DRIVE == 6:
    _med = MED_ALL * 1.5
ck('A6 the median system limit read here over the whole class reproduces the '
   'published one, so the change over the subset is a change in the same '
   'quantity',
   abs(_med - _pubval) / _pubval < 0.05,
   '%.4g W against %.4g W published' % (_med, _pubval))
# ★★★ R2-B5: THE COMPARISON MUST BE OVER ONE POPULATION OF SYSTEMS.
# Restricting the windows cannot deepen any system's best-window limit, and
# measured here none does (0 of 57 deepen, 1 is shallower by x1.79).  A
# median that deepens can therefore only be the removal of shallow systems:
# 3 of the 60 carry no limit in the subset at all -- PM J03433+1958, Wolf
# 219 and WD 0407+179, at 3.05, 2.56 and 8.36e15 W against a median of
# 1.75e15 -- which moves the median down 17 per cent while the restriction
# itself moves it up 14.  The published -5.5 per cent was the residual, and
# it was read as a property of the subset.  Over one population the sign is
# the honest one and no caveat is needed.
MED_SAME = st.median([BEST_ALL[k] for k in S_KEEP])
PCT = 100.0 * (MED_KEEP / MED_SAME - 1.0)
SENSE = 'deeper' if PCT < 0 else 'shallower'
ck('A10 no system\'s best-window limit deepens when windows are removed, so '
   'a deepening median can only be a change of sample',
   all(BEST_KEEP[k] >= BEST_ALL[k] - 1e-6 for k in S_KEEP)
   if DRIVE != 10 else False,
   '%d of %d deepen; sample change alone %+.2f per cent, restriction alone '
   '%+.2f per cent'
   % (sum(1 for k in S_KEEP if BEST_KEEP[k] < BEST_ALL[k] - 1e-6),
      len(S_KEEP), 100.0 * (MED_SAME / MED_ALL - 1.0), PCT))
m('EdrNSysLim', '%d' % len(S_KEEP))
if DRIVE == 7:
    SENSE = 'deeper' if PCT > 0 else 'shallower'
ck('A7 the direction of the change is read from the two medians and printed '
   'as a word, so the number cannot be printed with the wrong sense',
   (PCT < 0) == (SENSE == 'deeper'),
   'median %.4g -> %.4g W, %+.2f per cent, %s'
   % (MED_ALL, MED_KEEP, PCT, SENSE))
m('ScEdrMedPct', '%.1f' % abs(PCT))
m('ScEdrMedSense', SENSE)
# ★ the subset's SYSTEM count is a coverage statement, so it counts the
# systems the subset covers and not the smaller set that carries a limit in
# it (S_KEEP); the two differ by the systems the attribution mask leaves
# nothing of, and conflating them made this clause fail on a correct build.
_u, _s = band(KEEP), len({r['system_id'] for r in KEEP})
_pubsub = (int(tex('EdrNWinA')), int(tex('EdrNSys')), float(tex('EdrUnionGHz')))
if DRIVE == 8:
    _s += 1
ck('A8 the subset quantities recomputed here are the published ones',
   (len(KEEP), _s) == _pubsub[:2] and abs(_u - _pubsub[2]) < 0.05,
   '%d windows, %d systems, %.3f GHz against %d, %d, %s published'
   % (len(KEEP), _s, _u, _pubsub[0], _pubsub[1], _pubsub[2]))
_vac = bool(A_LO) and bool(B_HI)
if DRIVE == 9:
    _vac = not _vac
ck('A9 the criterion and the class disagree in both directions, which is '
   'the condition under which the distinction has to be drawn at all',
   _vac, '%d fine windows below it, %d coarse windows above it'
   % (len(A_LO), len(B_HI)))

json.dump(dict(
    eta_min=ETA_MIN, n_a=len(A), n_b=len(B), n_a_lo=len(A_LO),
    n_b_hi=len(B_HI), phrase=PHRASE, stars_lo=dict(BY),
    a_lo=[dict(star=r['star_name'], eb=r['eb'], flo=float(r['flo_GHz']),
               chanw_Hz=float(r['chanw_Hz']),
               on_source_s=float(r['on_source_s']),
               eta=float(r['eta_drift'])) for r in A_LO],
    b_hi=[dict(star=r['star_name'], system=r['system_id'], eb=r['eb'],
               band=r['band'], flo=float(r['flo_GHz']),
               fhi=float(r['fhi_GHz']), chanw_Hz=float(r['chanw_Hz']),
               on_source_s=float(r['on_source_s']),
               n_drift_trials=int(r['n_drift_trials']),
               eta=float(r['eta_drift'])) for r in B_HI],
    b_hi_systems=sorted(SB), b_hi_new_band_GHz=outside(B_HI, A),
    b_hi_crossings=len(_cross),
    chanw_fine_max_Hz=max(CW_A), chanw_coarse_min_Hz=min(CW_B),
    median_system_W=dict(all=MED_ALL, subset=MED_KEEP, pct=PCT, sense=SENSE),
    union_GHz=dict(all=band(ALLA), subset=_u),
    n_systems=dict(all=len(S_ALL), subset=_s), fails=FAIL),
    open(OUT_JSON, 'w'), indent=1, sort_keys=True)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    fh.write('\n'.join(sorted(MACROS)) + '\n')
print('\n  %d macros -> %s' % (len(MACROS), os.path.basename(OUT)))
if FAIL:
    print('  FAILURES: %s' % ', '.join(sorted(set(FAIL))))
    raise SystemExit(1)
print('  all clauses pass')
