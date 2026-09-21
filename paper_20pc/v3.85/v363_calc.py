#!/usr/bin/env python3
r"""v3.72 generated numbers.

Referee cycle after v3.62.  Two reports; the quantities they asked for that
are not already generated somewhere else are built here.

 (1) The Band 9/10 S_min unit defect and what it does to the largest retained
     primary-beam correction (referee 1, point 5).  The repair itself lives in
     `v342_calc.py`; the numbers that describe it are here, together with the
     explicit primary-beam response floor the referee asked us to adopt.
 (2) The ACA 7-m vs 12-m robustness table (referee 1, point 6).  The referee's
     stated minimum is a formal table; re-extracting 141 windows with the
     correct 7-m beam needs the raw visibilities and is out of reach in this
     cycle, so the table is what we give, with the cost stated.
 (3) Leave-one-star-out cross-validation of the radial repair (referee 1,
     point 2; referee 2, M1).  Read back from `radius_matched_v363.json`.
 (4) Recurrence coverage: what fraction of the sample the recurrence test can
     actually adjudicate (referee 2, M2), which is also the repair of the
     confusing 18-against-63 sentence in Appendix I (referee 2, minor 9).
 (5) The combined worst-case sensitivity debit, response x polarisation
     (referee 2, M5).
 (6) Drift-resolution counts by eta_drift rather than by channelisation
     (referee 1, point 10).
 (7) TRAPPIST-1 b: what fraction of orbital phase actually exceeds the drift
     ceiling (referee 2, minor 8).
 (8) The minor-planet crossmatch for the CP-72 2713 field and epoch
     (referee 2, M3).
 (9) ITU RR No. 5.340 protection of the searched union, an operator-
     independent replacement for a single FCC filing (referee 2, minor 11).

Reads only this folder; writes `survey_numbers_round29.tex`.
"""
import csv, collections, glob, json, math, os, re
_K = json.load(open('catalogue_constants.json'))  # v3.80: single source


HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = []


def M(name, val):
    OUT.append(r'\newcommand{\%s}{%s}' % (name, val))


def texval(macro):
    for fn in sorted(glob.glob('survey_numbers*.tex')):
        if fn.endswith('round29.tex'):
            continue
        m = re.search(r'\\newcommand\{\\%s\}\{(.*?)\}\s*$' % macro,
                      open(fn).read(), re.M)
        if m:
            return m.group(1)
    return None


def MA(name, val):
    """Define the macro, or -- if an earlier round already defines it --
    assert that this round reproduces it and emit nothing.

    Several of the array-split quantities were generated in round 20 from a
    different code path.  Recomputing them here and demanding agreement is the
    cheap version of the check that caught the v3.61 and v3.62 stale-literal
    defects, and it costs one line."""
    old = texval(name)
    if old is None:
        M(name, val)
    else:
        assert old == val, (name, 'round29 says %r, an earlier round says %r'
                            % (val, old))


ROWS = list(csv.DictReader(open('per_target_results_v3.85.csv')))
META = json.load(open('archive_meta_v381.json'))['ebs']
NWIN = len(ROWS)
assert NWIN == _K['n_windows'], NWIN

# =====================================================================
# (1) the S_min unit defect, and an explicit primary-beam response floor
# =====================================================================
# v342_calc.py repairs the twelve Band 9/10 rows whose S_min was written in
# millijanskys while every other row carries janskys.  Re-derive the count
# here from the released catalogue so the manuscript number cannot drift away
# from the repair: after the fix every row must satisfy
# S_min = 5 sigma_rms x (primary-beam correction).
PBCORR = [float(r['smin_mJy']) / (5.0 * float(r['rms_mJy']))
          for r in ROWS if float(r['rms_mJy']) > 0]
assert len(PBCORR) == NWIN, (len(PBCORR), NWIN)
PBMAX = max(PBCORR)
assert PBMAX < 2.0, PBMAX          # the floor adopted below
N_SMIN_FIXED = sum(1 for r in ROWS if r['band'] in ('9', '10'))
M('NSminFixed', '%d' % N_SMIN_FIXED)
M('SminUnitFactor', '1000')
M('PbFloorResp', '0.5')            # response floor adopted in v3.72
M('PbFloorCorr', '2')              # equivalently, correction ceiling
M('PbMaxCheck', '%.2f' % PBMAX)
M('NPbAboveFloor', '%d' % sum(1 for x in PBCORR if x > 2.0))
# where the star sits in the beam, for the same windows
ROT = [float(x[3]) for x in json.load(open('pboffsets_v361.json'))]
# Referee A1 (round 1): a retention floor that excludes nothing looks fitted to
# the data unless the gap it sits in is shown.  `pboffsets_v361.json` carries
# the stellar offset in units of theta_PB for every progenitor window, withheld
# ones included, so the two edges of the gap can be quoted from one file.
_OFF_CAT = {(x[0], round(min(x[1], x[2]), 3)) for x in json.load(
    open('pboffsets_v361.json'))}
_CATKEY = {(r['eb'], round(min(float(r['flo_GHz']), float(r['fhi_GHz'])), 3))
           for r in ROWS}
_GAUSS = lambda u: 1.0 / math.exp(-4.0 * math.log(2.0) * u * u)
_kept = [x[3] for x in json.load(open('pboffsets_v361.json'))
         if (x[0], round(min(x[1], x[2]), 3)) in _CATKEY]
_held = [x[3] for x in json.load(open('pboffsets_v361.json'))
         if (x[0], round(min(x[1], x[2]), 3)) not in _CATKEY and x[3] > 0.5]
assert _held, 'no withheld high-offset windows found'
M('PbGapKeptU', '%.2f' % max(_kept))
# Referee H2 (round 3): the floor is a rule about RESPONSE, so quote the two
# edges of the gap as responses too, not only as offsets.
M('PbGapKeptResp', '%.2f' % (1.0 / _GAUSS(max(_kept))))
M('PbGapHeldResp', '%.2f' % (1.0 / _GAUSS(min(_held))))
M('PbGapHeldU', '%.2f' % min(_held))
M('PbGapHeldCorr', '%.2f' % _GAUSS(min(_held)))
M('PbRoverThetaMax', '%.2f' % max(_kept))
M('PbRoverThetaMed', '%.3f' % sorted(ROT)[len(ROT) // 2])

# =====================================================================
# (2) ACA 7-m vs 12-m robustness table
# =====================================================================
# The two Band 9/10 execution blocks folded in at v3.62 are not in the v3.43
# archive harvest.  Their array is measured, not assumed: `b910_array_v363.json`
# records that ALMA TAP reports 0 of 45 and 0 of 44 antennas with CM (7-m)
# identifiers for them, so both are 12-m blocks.
B910 = json.load(open('b910_array_v363.json'))
assert all(v['n_cm'] == 0 for v in B910.values()), B910
EXTRA_12M = {'A002_X11d9ce7_X5257', 'A002_Xbf792a_X26ec'}


def arr_of(eb):
    if eb in EXTRA_12M:
        return '12m'
    m = META.get(eb)
    if not m:
        return None
    a = m.get('array')
    if a in ('7m', '12m'):
        return a
    # v3.80: prefer the array the metadata states. Deriving it instead from
    # a majority of antenna names disagreed with v352_calc.py on one block
    # (323 vs 322 seven-metre blocks) -- two code paths, one quantity, the
    # exact defect the cross-assertion in MA() exists to catch. One source.
    a = m.get('array')
    if a in ('7m', '12m'):
        return a
    n7, n12 = m.get('n_ant_7m', 0), m.get('n_ant_12m', 0)
    return '7m' if n7 > n12 else '12m'


SPLIT = collections.defaultdict(list)
for r in ROWS:
    a = arr_of(r['eb'])
    if a:
        SPLIT[a].append(r)
assert sum(len(v) for v in SPLIT.values()) == NWIN, \
    (sum(len(v) for v in SPLIT.values()), NWIN)

RANKFLOOR = 1.0 / 513.0
for tag, key in (('SevenM', '7m'), ('TwelveM', '12m')):
    g = SPLIT[key]
    stars = {r['star_name'] for r in g}
    syst = {r['system_id'] for r in g}
    ebs = {r['eb'] for r in g}
    cross = [r for r in g if r['crossing'] == 'True']
    s1 = [r for r in g if r['stage1_flag'] == 'True']
    rankfirst = [r for r in g if int(r['n_ctrl_ge_star']) == 0]
    MA('NWin' + tag, '%d' % len(g))
    MA('NEb' + tag, '%d' % len(ebs))
    MA('NStar' + tag, '%d' % len(stars))
    MA('NSys' + tag, '%d' % len(syst))
    MA('NCross' + tag, '%d' % len(cross))
    MA('NRankFirst' + tag, '%d' % len(rankfirst))
    MA('NStageOne' + tag, '%d' % len(s1))
    # a window is flagged at stage 1 only if it is rank-first among its 512
    # controls, so under exchangeability the chance is 1/513 per window.
    MA('ExpFlags' + tag, '%.2f' % (len(g) * RANKFLOOR))
MA('PctWinSevenM', '%.0f' % (100.0 * len(SPLIT['7m']) / NWIN))

# =====================================================================
# (3) leave-one-star-out cross-validation of the radial repair
# =====================================================================
RM = json.load(open('radius_matched_v363.json'))
LOO = RM['loo']
HO = RM['heldout']
M('LooNStars', '%d' % LOO['n_stars'])
M('LooMedian', '%.3f' % LOO['median'])
M('LooD', '%.3f' % LOO['D'])
M('LooP', ('%.4f' % LOO['p']) if LOO['p'] >= 1e-4 else
   ('%.0e' % LOO['p']).replace('e-0', r'\times10^{-') + '}')
M('HoRawMedian', '%.3f' % HO['raw_median'])
M('HoDetMedian', '%.3f' % HO['det_median'])
M('HoRawD', '%.3f' % HO['raw_D'])
M('HoDetD', '%.3f' % HO['det_D'])
M('HoN', '%d' % HO['n'])
M('RmNFlagA', '%d' % len(RM['a_flagged']))
M('RmNFlagB', '%d' % len(RM['b_flagged']))
M('RmExpA', '%.1f' % RM['a_expected'])
M('RmExpB', '%.2f' % RM['b_expected'])
MA('RmInnerN', '%d' % RM['inner_n'])
# the survey-wide side-by-side the referees asked for, as a table body
rowsA = {(d['star'], d['band']) for d in RM['a_flagged']}
rowsB = {(d['star'], d['band']) for d in RM['b_flagged']}
rel = {(d['star'], d['band']) for d in RM['released']}
M('RmAOnly', '%d' % len(rowsA - rel))
M('RmBOnly', '%d' % len(rowsB - rel))
M('RmLost', '%d' % len(rel - (rowsA & rowsB)))

# =====================================================================
# (4) recurrence coverage
# =====================================================================
NSYS = len({r['system_id'] for r in ROWS})
sys_blocks = collections.defaultdict(set)
for r in ROWS:
    sys_blocks[r['system_id']].add(r['eb'])
n_multi_searched = sum(1 for s in sys_blocks if len(sys_blocks[s]) > 1)
M('NSysRecurrence', '%d' % n_multi_searched)
M('PctSysRecurrence', '%.0f' % (100.0 * n_multi_searched / NSYS))
_multieb = texval('NSysMultiEB')
assert _multieb is not None, (
    'NSysMultiEB is missing.  retire_macros.py strips macros the manuscript '
    'does not reference, so this generator must run inside make_all.sh, after '
    'round10_calc.py has regenerated it, and the manuscript must keep at least '
    'one \\NSysMultiEB reference alive.')
M('PctSysRecurrenceArch', '%.0f' % (100.0 * int(_multieb) / NSYS))
# Referee 2's minor 9: the appendix sentence set 18 against 63 without saying
# that the 63 counts what is *archived* rather than what was searched, and the
# reader's confusion is made worse by the arithmetic accident that 81-18 is
# also 63.  Quote the difference instead, which cannot be misread.
M('NSysRecArchOnly', '%d' % (int(_multieb) - n_multi_searched))

# =====================================================================
# (5) combined worst-case sensitivity debit
# =====================================================================
han = None
for cand in ('HanFacMed', 'PeffMed', 'RespMed'):
    v = texval(cand)
    if v is not None:
        han = float(v)
        break
assert han is not None, 'no response-correction macro found'
pol = 1.41
M('DebitCombined', '%.1f' % (han * pol))
M('DebitHan', '%.2f' % han)
M('DebitPol', '%.2f' % pol)

# =====================================================================
# (6) drift resolution by eta_drift rather than by channelisation
# =====================================================================
etaA = [r for r in ROWS if r['search_class'] == 'A']
etaB = [r for r in ROWS if r['search_class'] == 'B']
nA_lt1 = sum(1 for r in etaA if float(r['eta_drift']) < 1)
nB_ge1 = sum(1 for r in etaB if float(r['eta_drift']) >= 1)
n_ge1 = sum(1 for r in ROWS if float(r['eta_drift']) >= 1)
M('NEtaResolved', '%d' % n_ge1)
M('NEtaAExceptions', '%d' % nA_lt1)
M('NEtaBExceptions', '%d' % nB_ge1)
M('PctEtaResolved', '%.0f' % (100.0 * n_ge1 / NWIN))

# =====================================================================
# (7) TRAPPIST-1 b phase fraction above the drift ceiling
# =====================================================================
TP = json.load(open('trappist_phase_v363.json'))
M('TrapPhaseLo', '%.0f' % (100 * TP['hi']['f_edge']))     # strictest ceiling
M('TrapPhaseHi', '%.0f' % (100 * TP['lo']['f_edge']))
M('TrapPhaseIsoLo', '%.1f' % (100 * TP['hi']['f_iso']))
M('TrapPhaseIsoHi', '%.0f' % (100 * TP['lo']['f_iso']))

# =====================================================================
# (8) minor-planet crossmatch for CP-72 2713
# =====================================================================
SS = json.load(open('ssobody_cp72_v363.json'))
ok = [q for q in SS['queries'] if q['status'] == 'ok']
assert ok and all(q['n'] == 0 for q in ok), [q['n'] for q in ok]
M('SsoRadius', '%.0f' % (max(q['radius_arcsec'] for q in ok) / 60.0))
M('SsoNFound', '0')
M('SsoEclLat', '%.0f' % abs(SS['ecl_lat_deg']))
M('SsoNearestBody', SS['nearest_body'])
M('SsoNearestSep', '%.0f' % SS['nearest_body_sep_deg'])
M('SsoCtrlLo', '%d' % SS['control_min'])
M('SsoCtrlHi', '%d' % SS['control_max'])

# =====================================================================
# (9) ITU RR No. 5.340
# =====================================================================
IT = json.load(open('itu5340_v363.json'))
M('ItuPct', '%.1f' % IT['rr5340_pct'])
M('ItuGHz', '%.1f' % IT['rr5340_overlap_GHz'])
M('ItuAbove', '%.0f' % IT['above275_pct'])
M('UnionCheckGHz', '%.2f' % IT['union_GHz'])

# =====================================================================
# (10) the beta Pictoris Band 6 window's trials load (round 3, referee G1)
# =====================================================================
# A revision claimed this window "carries far fewer trials" because it is only
# 54 MHz wide.  It is narrow AND finely channelised, so it holds the same
# channel count as a wide window and the survey's LARGEST drift-trial count.
# Generated here so the claim cannot be made by hand again.
_bp6 = [r for r in ROWS
        if r['star_name'].startswith('bet Pic') and r['band'] == '6'
        and r['stage1_flag'] == 'True']
# v3.80: three beta Pic Band 6 windows are now flagged at stage 1, not one.
# The statement is about the finely channelised recurring window, so take
# the one with the narrowest channel -- the property the argument rests on
# -- and record how many share the flag.
assert _bp6, 'no flagged beta Pic Band 6 window'
M('BpSixNFlagged', '%d' % len(_bp6))
_bp6 = sorted(_bp6, key=lambda r: (float(r['chanw_Hz']), r['eb']))[0]
_tr = sorted(float(r['n_drift_trials']) for r in ROWS)
# The "largest drift-trial count in the survey" claim must be re-tested on
# the enlarged catalogue rather than assumed; emit the rank either way.
_rank = sum(1 for x in _tr if x > float(_bp6['n_drift_trials'])) + 1
M('BpSixTrialRank', '%d' % _rank)
M('BpSixIsTrialMax', 'yes' if _rank == 1 else 'no')
M('BpSixBwMHz', '%.1f' % (float(_bp6['bandwidth_Hz']) / 1e6))
M('BpSixChanKHz', '%.2f' % (float(_bp6['chanw_Hz']) / 1e3))
M('BpSixNChan', '%d' % round(float(_bp6['bandwidth_Hz']) / float(_bp6['chanw_Hz'])))
M('BpSixTrials', '%d' % round(float(_bp6['n_drift_trials'])))
M('BpSixEta', '%.0f' % float(_bp6['eta_drift']))
M('TrialsMed', '%d' % round(_tr[len(_tr) // 2]))
M('NWinNarrow', '%d' % sum(1 for r in ROWS if float(r['bandwidth_Hz']) < 1e8))

# =====================================================================
# (10) uncertainty on the measured tail correction (referee 1, point 4)
# =====================================================================
# v3.67 quoted a Clopper-Pearson interval computed on \NPseudo = 220,672,
# which is the count of pooled rank values from an earlier analysis, NOT the
# number of pseudo-star trials.  The pseudo-star test uses the 16 inner probes
# of each calibration window, so the trial count is 603 x 16 = 9,648 and the
# interval is an order of magnitude wider.  `tailboot_v372.py` recomputes the
# test from the stored control vectors and bootstraps it clustered by window
# and by execution block, which is what the referee asked for.
_TB = json.load(open('tailboot_v372.json'))
M('TailNTrials', '{:,}'.format(_TB['n_trials']).replace(',', '\\,'))
M('TailNExceed', '%d' % _TB['k'])
M('TailNWinBoot', '%d' % _TB['n_windows'])
M('TailNBlockBoot', '%d' % _TB['n_blocks'])
M('TailRatioBoot', '%.1f' % _TB['ratio'])
M('TailBinomLo', '%.1f' % _TB['binomial_ci'][0])
M('TailBinomHi', '%.1f' % _TB['binomial_ci'][1])
M('TailWinLo', '%.1f' % _TB['window_ci'][0])
M('TailWinHi', '%.1f' % _TB['window_ci'][1])
M('TailBlockLo', '%.1f' % _TB['block_ci'][0])
M('TailBlockHi', '%.1f' % _TB['block_ci'][1])

# =====================================================================
# (11) why every trigger crossing is Class A (referee 1, editorial)
# =====================================================================
import statistics as _st
_cells = {}
for _c in ('A', 'B'):
    _g = [r for r in ROWS if r['search_class'] == _c]
    _cells[_c] = _st.median(
        [float(r['bandwidth_Hz']) / float(r['chanw_Hz']) * float(r['n_drift_trials'])
         for r in _g])
_cross = [r for r in ROWS if r['crossing'] == 'True']
# v3.80: on the released catalogue every trigger crossing happened to be
# Class A, and the paper explained why -- a Class B window's coarse
# channels hold ~1e4 times fewer search cells. With 1956 windows the
# statement is no longer exceptionless, so report the split instead of
# asserting the clean case. The explanation survives; the absolute claim
# does not.
_crossA = [r for r in _cross if r['search_class'] == 'A']
M('NCrossClassA', '%d' % len(_crossA))
M('NCrossClassB', '%d' % (len(_cross) - len(_crossA)))
M('PctCrossClassA',
  '%.0f' % (100.0 * len(_crossA) / len(_cross)) if _cross else '0')
M('CellsMedA', '%.1f\\times10^{5}' % (_cells['A'] / 1e5))
M('CellsMedB', '%.0f' % _cells['B'])
M('CellsRatioAB', '%.0f' % (_cells['A'] / _cells['B']))

# =====================================================================
# (12) how little of the local M-dwarf population is searched (referee 2, M1)
# =====================================================================
# Read straight out of the generated selection-function table so the two can
# never disagree: the M row gives census and searched counts in one place.
_sel = open('tab_selection.tex').read()
_m = re.search(r'\\quad M \(\$<3900\$\\,K\) & (\d+) \([^)]*\) & (\d+) ', _sel)
assert _m, 'M-dwarf row not found in tab_selection.tex'
_mcen, _msea = int(_m.group(1)), int(_m.group(2))
M('NMCensus', '{:,}'.format(_mcen).replace(',', '\\,'))
M('NMSearched', '%d' % _msea)
M('PctMSearched', '%.1f' % (100.0 * _msea / _mcen))

# =====================================================================
# (13) the external calibration sample, re-harvested 2026-09-13T19:30Z
# =====================================================================
# The campaign has continued since the counts frozen at v3.51.  These macros
# carry the live totals; the pseudo-star and radial diagnostics stay on the
# 603-window subset that retains full 512-probe control vectors, which is
# stated in the text.
_CM = json.load(open('campaign_v372.json'))
M('CampWindows', '%d' % _CM['n_windows'])
M('CampBlocks', '%d' % _CM['n_blocks'])
def _repeat_from_catalogue(star):
    """Largest stellar statistic in other blocks of the same star whose
    tuning covers this star's stage-1 window, and how many controls beat
    it there. Same rule as Table 11."""
    from star_alias import canon as _cn
    # the campaign record carries LaTeX ties and a minus sign
    tgt = _cn(str(star).replace('~', ' ').replace('$-$', '-')).replace(' ', '')
    me = [r for r in ROWS
          if _cn(r['star_name']).replace(' ', '').startswith(tgt)
          and r['stage1_flag'] == 'True']
    if not me:
        return None, None
    m0 = me[0]
    lo, hi = sorted((float(m0['flo_GHz']), float(m0['fhi_GHz'])))
    rep = [q for q in ROWS
           if _cn(q['star_name']) == _cn(m0['star_name']) and q['eb'] != m0['eb']
           and min(float(q['flo_GHz']), float(q['fhi_GHz'])) <= lo + 0.02
           and max(float(q['flo_GHz']), float(q['fhi_GHz'])) >= hi - 0.02]
    if not rep:
        return None, None
    best = max(rep, key=lambda q: float(q['star_snr']))
    return float(best['star_snr']), int(best['n_ctrl_ge_star'])


M('CampStars', '%d' % _CM['n_stars'])
M('CampMedRank', '%.3f' % _CM['median_rank'])
M('CampKsD', '%.3f' % _CM['ks_D'])
M('CampKsP', '%.0e' % _CM['ks_p'])
M('CampCross', '%d' % _CM['n_cross'])
M('CampStageOne', '%d' % _CM['n_stage1'])
M('CampStageOneCO', '%d' % _CM['n_stage1_co'])
M('CampUnattrib', '%d' % _CM['n_stage1_unattrib'])
_u = sorted(_CM['unattrib'], key=lambda x: -x['t'])
_ORD = ('One', 'Two', 'Three', 'Four', 'Five')
for _i, _e in enumerate(_u[:len(_ORD)]):
    _k = _ORD[_i]
    M('CampUn%sStar' % _k, _e['star'])
    M('CampUn%sBand' % _k, '%d' % _e['band'])
    M('CampUn%sGHz' % _k, '%.3f' % _e['flo'])
    M('CampUn%sT' % _k, '%.2f' % _e['t'])
    M('CampUn%sCtrl' % _k, '%.2f' % _e['ctrl'])
    # v3.85 (Q16): take the repeat statistic from the released catalogue,
    # matching on the window as Table 11 does. The campaign record's own
    # repeat_best_t used a looser window match and gave 5.51 for HD 14055
    # where the catalogue gives 5.42 -- which then exceeded the global
    # maximum the paper quotes.
    _rt, _rn = _repeat_from_catalogue(_e['star'])
    M('CampUn%sRepT' % _k, '%.2f' % (_rt if _rt is not None
                                     else _e['repeat_best_t']))
    M('CampUn%sRepNge' % _k, '%d' % (_rn if _rn is not None
                                     else _e['repeat_nge']))
M('CampUnList', ', '.join(_e['star'] for _e in _u[:-1]) + ' and ' + _u[-1]['star']
  if len(_u) > 1 else _u[0]['star'])
M('CampCtrlAll', '%d' % _CM.get('n_with_ctrl_all', 0))
_mon = ('January February March April May June July August September October '
        'November December').split()
_d = _CM.get('asof', '2026-09-13T00:00Z')
M('CampAsOf', '%s %s %s' % (_d[:4], _mon[int(_d[5:7]) - 1], int(_d[8:10])))
# expected unattributed outliers at the measured tail rate, over this sample
_rate = float(texval('PseudoFirstHO') or 0.0028)
M('CampExpUn', '%.1f' % (_CM['n_windows'] * _rate))

# =====================================================================
# (14) how much of the in-scope archive has now actually been searched
# =====================================================================
# The manuscript quotes "NEB of NProgenitorEBTotal", which describes the FROZEN
# RELEASE and is correct as such.  Used forward-looking ("N blocks remain
# unanalysed") it became wrong once the continuation campaign ran: most of them
# have now been searched.  `searched_ebs_v372.txt` is the list of execution
# blocks carrying a search product on the host, harvested read-only.
_all = {l.strip() for l in open('searched_ebs_v381.txt') if l.strip()}
_frozen = {r['eb'] for r in ROWS}
_meta = json.load(open('archive_meta_v381.json'))['mous']
_prog = set()
for _v in _meta.values():
    _prog |= {p if isinstance(p, str) else p.get('eb') for p in _v['progenitors']}
# v3.80: the Band 9/10 MOUS are inside the re-harvested metadata now, so
# adding them again double-counted three progenitors (659 vs 656). One
# source, as in v344_calc.py.
_prog = {p for p in _prog if p}
assert len(_prog) == int(texval('NProgenitorEBTotal')), \
    (len(_prog), texval('NProgenitorEBTotal'))
_camp = _all - _frozen
# v3.80: restrict to the progenitor population so that
# in-scope-searched + still-unsearched == total holds exactly. Two
# catalogue blocks have no recoverable member OUS and so appear in
# neither; they are reported by \NEbNoProgenitor rather than
# quietly inflating the searched count.
_in = (_frozen & _prog) | (_camp & _prog)
M('NEbNoProgenitor', '%d' % len(_frozen - _prog))
M('NEbSearchedAll', '%d' % len(_all))
M('NEbCampAll', '%d' % len(_camp))
M('NEbInScopeSearched', '%d' % len(_in))
M('PctInScopeSearched', '%.0f' % (100.0 * len(_in) / len(_prog)))
M('NEbStillUnsearched', '%d' % len(_prog - _in))
M('NEbOutOfScope', '%d' % len(_camp - _prog))

# =====================================================================
# (15) the survey-wide Bonferroni scale, asserted against its own definition
# =====================================================================
# Referee 2 found the same quantity printed as 1.2e-4 and 1.1e-4 in different
# places: `BonferroniThresh` in the round-5 freeze was computed on a superseded
# window count.  The manuscript now uses `BonfScaleCalc` only; this asserts it
# really is alpha/N on the released catalogue.
_alpha = float(texval('BonfAlpha'))
_bn = int(texval('BonfNWin'))
assert _bn == NWIN, ('BonfNWin %d != catalogue %d' % (_bn, NWIN))
_want = _alpha / _bn
_got = texval('BonfScaleCalc')
_m = re.match(r'([0-9.]+)\\times10\^\{(-?\d+)\}', _got)
assert _m, _got
_val = float(_m.group(1)) * 10 ** int(_m.group(2))
assert abs(_val - _want) / _want < 0.05, ('BonfScaleCalc %g != alpha/N %g' % (_val, _want))
M('BonfScaleChk', '%.3g' % _want)

# =====================================================================
# (16) the pre-registration timestamp, made citable (referee 2, M8)
# =====================================================================
# The manuscript asserted that the criteria were repository-timestamped before
# the validation sample was analysed.  A referee cannot check an assertion, so
# quote the commit and its date.  Both are read back from the frozen record
# rather than typed.
M('PreregHash', texval('CpCritHash') or 'see repository')
M('PreregDate', texval('CpCritDate') or 'see repository')

open('survey_numbers_round29.tex', 'w').write('\n'.join(OUT) + '\n')
print('round29: %d macros' % len(OUT))
