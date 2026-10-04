#!/usr/bin/env python3
r"""v409_calc.py -- the v4.09 round (round 102).

What this generator is for.  Four things landed after v4.08 was cut, all of
them measured on products this container no longer holds, and all of them
frozen into `r8inputs/v409/`:

  1. the 44-unit field-truncation re-extraction, harvested (157 windows, 39
     blocks).  D35 decision 1 ADOPTS the repaired $T_\star$ as the search
     statistic, which takes four released crossings below the 5.0 trigger and
     raises one;
  2. the restored HD 139084 B extraction, which is a different star from the
     primary in the same execution block and 10.3 arcsec away from it;
  3. the never-attempted tail of the archival sweep, 8 of 12 blocks searched,
     which adds two HD 14055 threshold crossings;
  4. D36's three re-runs on the fixed position key, and the naming of the one
     block the published ledger left anonymous.

HOW THE COUNTS ARE KEPT HONEST.  The deposited catalogue is, and remains, the
1651-row release: the per-window content of the 32 tail windows and of the
restored companion does not exist in this deposit, and `\NWindows` is the
denominator of some forty statistics computed on those 1651 rows.  Inventing
rows would make all of them false.  So this generator emits the v4.09 extent
under its OWN namespace (`\Vn...`), prints it as a four-step SEQUENCE, and
`V2` asserts that the sequence closes on the extent.  Nothing here redefines
a macro the catalogue owns.

THE SIX ASSERTIONS THAT MUST SURVIVE THE BUILD (V409_INPUTS, adoption list):
  V1   \VnWinA + \VnWinB == \VnWindows
  V2   the crossing delta closes: 56 - 4 + 1 + 1 + 2 == \VnNHits
  V3   the block fates sum to \FateScope          (in blockfate_v409.py)
  V4   \ClustShippedFixedP < \VnClustFixedSkyP
  V5   the near-edge excess is never emitted without its one-window share
       and a held-out half beside it
  V6   no test writes a path production reads    (checked here and in the
       selftest, which writes only to `*_driveN.*`)

Writes survey_numbers_round102.tex, tab_crossdelta_v409.tex,
tab_clust_v409.tex, tab_tail_v409.tex and repaired_v409.csv.

Usage:  v409_calc.py [--drive N]      N = 1..19 (selftest_v409.py drives them)
"""
import collections
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, 'r8inputs', 'v409')
# ★ `--drive 0` is "no perturbation, but DO NOT write a production path".
#   The gate's own baseline check needs to run the generator unperturbed, and
#   if that run landed on the real products it would be the very thing D36
#   forbids -- a test writing where production reads.  So DRIVE is None when
#   the flag is absent and an integer (including 0) when it is present, and
#   the suffix follows the flag rather than the perturbation.
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None

# ---------------------------------------------------------------------------
# V6: A TEST MUST NEVER WRITE TO THE PATH PRODUCTION READS.  D36's fourteenth
# defect was a driver that wrote the canonical population file on every run,
# including its own falsifying drives, so a deliberately corrupted population
# was left on disk and the next stage consumed it.  The rule is enforced
# mechanically here: under --drive N every output filename is suffixed, so a
# drive CANNOT overwrite a product the build reads.
SUF = '' if DRIVE is None else '_drive%d' % DRIVE


def out(name):
    stem, ext = os.path.splitext(name)
    return os.path.join(HERE, stem + SUF + ext)


OUT = []


def m(name, val):
    # ★ letters only: `\XV408` parses as `\XV` plus a typeset "408", which in
    #   the preamble is "Missing \begin{document}" and no PDF at all.  See
    #   blockfate_v409.py, where four such names were written.
    assert name.isalpha(), 'macro name %r is not letters-only' % name
    OUT.append(r'\newcommand{\%s}{%s}' % (name, val))


fail = []


def ck(tag, cond, detail=''):
    if not cond:
        fail.append(tag)
    print('  %-56s %s  %s' % (tag, 'PASS' if cond else 'FAIL', detail))


def J(name):
    return json.load(open(os.path.join(INP, name)))


C_KMS = 299792.458


def pfmt(p):
    r"""A probability as the manuscript's \pv macro expects it: an ordinary
    decimal, or LaTeX scientific notation when it is too small for one."""
    if p >= 1e-3:
        return '%.2g' % p
    e = int(math.floor(math.log10(p)))
    return r'%.1f\times10^{%d}' % (p / 10.0 ** e, e)

# the frozen 17-transition mask, byte-identical to v342_calc.py's CAT.  It is
# duplicated rather than imported because v342_calc.py is a 1300-line
# generator with side effects; V12 asserts the two agree on every transition
# this round quotes, so the copy cannot drift.
LINES = {
    'CO(1-0)':    115.2712018, 'CO(2-1)':   230.5380000, 'CO(3-2)': 345.7959899,
    'CO(4-3)':    461.0407682, 'CO(6-5)':   691.4730763,
    '13CO(2-1)':  220.3986842, 'C18O(2-1)': 219.5603541,
    'HCN(1-0)':    88.6316022, 'HCN(3-2)':  265.8864340,
    'HCO+(1-0)':   89.1885260, 'HCO+(3-2)': 267.5576259,
    'CS(5-4)':    244.9355565, 'CN(1-0)':   113.4909702,
    'SiO(5-4)':   217.1049800, 'H2CO(3-2)': 218.2221920,
    '[CI](1-0)':  492.1606510, 'H30a':      231.9009280,
}
MASK_KMS = 50.0          # the survey's own frozen mask half-width


def nearest_line(f_GHz):
    """(name, dv_kms) for the nearest transition in the SKY frame."""
    best = min(LINES.items(), key=lambda kv: abs(f_GHz / kv[1] - 1.0))
    return best[0], (f_GHz - best[1]) / best[1] * C_KMS


# ===========================================================================
# 0.  the released catalogue, which is the thing every count is measured from
# ===========================================================================
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
N_WIN = len(CAT)
N_STAR = len(set(r['star_name'] for r in CAT))
N_SYS = len(set(r['system_id'] for r in CAT))
N_CROSS = sum(1 for r in CAT if r['crossing'] == 'True')
N_A = sum(1 for r in CAT if r['search_class'] == 'A')
N_B = sum(1 for r in CAT if r['search_class'] == 'B')
H_REL = sum(float(r['on_source_s']) for r in CAT) / 3600.0
print('released catalogue: %d windows (%d A + %d B) / %d stars / %d systems / '
      '%d crossings / %.2f h' % (N_WIN, N_A, N_B, N_STAR, N_SYS, N_CROSS,
                                 H_REL))

# ===========================================================================
# 1.  the 44-unit harvest, joined to the catalogue ON THE INTERVAL
# ===========================================================================
# ★ The join note that cost the predecessor 80 of 157 windows: the catalogue's
#   `flo_GHz` is min(freqs) while a product's `freq_lo_GHz` is freqs[0], which
#   for a descending spectral axis is the MAXIMUM.  Joining on `flo` alone
#   silently loses every reversed-axis window.  Join on the interval.
R = J('reext_results.json')
ROWS = R['rows']
SUM = R['summary']
FF = {(r['eb'], r['spw']): r for r in J('fieldfix_v409.json')}


def ckey(r):
    return (r['eb'], round(min(float(r['flo_GHz']), float(r['fhi_GHz'])), 2),
            round(float(r['chanw_Hz'])))


def rkey(r, drive_break=False):
    if drive_break:                        # --drive 1: join on flo alone
        return (r['eb'], round(r['old_freq_lo_GHz'], 2),
                round(float(r['old_chanwidth_Hz'])))
    return (r['eb'],
            round(min(r['old_freq_lo_GHz'], r['old_freq_hi_GHz']), 2),
            round(float(r['old_chanwidth_Hz'])))


BYKEY = collections.defaultdict(list)
for r in CAT:
    BYKEY[ckey(r)].append(r)

pairs, unjoined = [], []
for r in ROWS:
    if r['old_rms_combined_mJy'] is None:
        continue
    cand = BYKEY.get(rkey(r, DRIVE == 1), [])
    if not cand:
        unjoined.append((r['eb'], r['spw']))
        continue
    if len(cand) > 1:
        cand = [x for x in cand
                if abs(float(x['rms_mJy']) - r['old_rms_combined_mJy'])
                < 1e-3 * max(1.0, r['old_rms_combined_mJy'])] or cand
    pairs.append((cand[0], r))

DH_REPAIR = sum(r['new_on_source_s'] - r['old_on_source_s']
                for _, r in pairs) / 3600.0
DT = sorted(abs(r['new_star_peak_snr'] - r['old_star_peak_snr'])
            for _, r in pairs if r['new_star_peak_snr'] is not None)
DT_MED = DT[len(DT) // 2]
DT_SIGNED = sorted(r['new_star_peak_snr'] - r['old_star_peak_snr']
                   for _, r in pairs if r['new_star_peak_snr'] is not None)
DT_SIGNED_MED = DT_SIGNED[len(DT_SIGNED) // 2]
# the windows where NO on-source time was recovered: the no-op subset
NOOP = [(x, r) for x, r in pairs
        if r['new_star_peak_snr'] is not None
        and abs(r['new_on_source_s'] / r['old_on_source_s'] - 1.0) < 0.01]
_dn = sorted(abs(r['new_star_peak_snr'] - r['old_star_peak_snr'])
             for _, r in NOOP)
DT_NOOP_MED = _dn[len(_dn) // 2]
DT_NOOP_MAX = _dn[-1]

FELL = sorted([(x, r) for x, r in pairs
               if x['crossing'] == 'True' and r['new_star_peak_snr'] < 5.0],
              key=lambda p: -float(p[0]['star_snr']))
ROSE = [(x, r) for x, r in pairs
        if x['crossing'] != 'True' and r['new_star_peak_snr'] is not None
        and r['new_star_peak_snr'] >= 5.0
        and r['eb'] != 'A002_Xcd8029_Xb6b0']       # the companion is item 2
print('harvest: %d windows, %d blocks, %d joined, %d unjoined; '
      'on-source %+.2f h; median |dT*| %+.3f; %d fell, %d rose'
      % (SUM['n_windows'], SUM['n_blocks'], len(pairs), len(unjoined),
         DH_REPAIR, DT_MED, len(FELL), len(ROSE)))

# ===========================================================================
# 2.  the restored HD 139084 B extraction
# ===========================================================================
AP = J('v409_addprof.json')
COMP = [r for r in ROWS if r['eb'] == 'A002_Xcd8029_Xb6b0']
COMP3 = FF[('A002_Xcd8029_Xb6b0', 3)]
PRIM3 = [r for r in CAT if r['eb'] == 'A002_Xcd8029_Xb6b0'
         and float(r['chanw_Hz']) < 1e6]
assert len(PRIM3) == 1, PRIM3
PRIM3 = PRIM3[0]
# the two components' primary-beam offsets differ by 0.116 arcsec while they
# are 10.32 arcsec apart on the sky: a pb-offset tolerance CANNOT separate
# them, which is how the 13th instance of the key family was caused.
PB_COMP = COMP3['pb_offset']
PB_PRIM = float(PRIM3['pb_offset_arcsec'])
N_139_WIN, N_139_STAR, N_139_CROSS, N_139_A = 4, 1, 1, 1

# ===========================================================================
# 3.  the never-attempted tail
# ===========================================================================
TC = J('tail_collect.json')
TAIL_DONE = [b for b in TC if b.get('done')]
TAIL_OPEN = [b for b in TC if not b.get('done')]
N_TAIL_BLOCK = len(TAIL_DONE)
N_TAIL_WIN = 4 * N_TAIL_BLOCK
N_TAIL_A, N_TAIL_B = 14, 18
N_TAIL_CROSS = 2

# ★ THE ONE TYPED NUMBER IN THE SCIENCE INPUTS, AND IT IS NOW PART-MEASURED.
#   `v409_census.py` carried `H_TAIL = 22.687` with the comment "measured: sum
#   of the 32 windows' own on_source_s".  Twelve of those 32 windows -- the
#   three HD 14055 blocks -- are in `hd14055_results.json` and their hours ARE
#   recomputed here; the other 20 are not in the deposit and the remainder is
#   carried as a DECLARED external input with its provenance named.  V11
#   asserts the computed part and pins the declared remainder.
HD = J('hd14055_results.json')
TAIL_HD_EBS = ['A002_X1190de8_Xd526', 'A002_X11adad7_X25c5e',
               'A002_X11adad7_X25dc7']
H_TAIL_HD = sum(w['ons'] for w in HD if w['eb'] in TAIL_HD_EBS) / 3600.0
H_TAIL_TOTAL = 22.687          # the tail run's own per-window sum (host)
H_TAIL_DECL = H_TAIL_TOTAL - H_TAIL_HD

# ===========================================================================
# 4.  the census as a SEQUENCE
# ===========================================================================
SEQ = [
    ('right counts, wrong content', 1655, 90, 56),
    ('honest interim', N_WIN, N_STAR, N_CROSS),
    ('companion restored', N_WIN + N_139_WIN, N_STAR + N_139_STAR,
     N_CROSS + N_139_CROSS),
    ('repaired statistic', N_WIN + N_139_WIN, N_STAR + N_139_STAR,
     N_CROSS + N_139_CROSS - len(FELL) + len(ROSE)),
    ('tail extension', N_WIN + N_139_WIN + N_TAIL_WIN, N_STAR + N_139_STAR,
     N_CROSS + N_139_CROSS - len(FELL) + len(ROSE) + N_TAIL_CROSS),
]
VN_WIN = SEQ[-1][1]
VN_STAR = SEQ[-1][2]
VN_CROSS = SEQ[-1][3]
VN_A = N_A + N_139_A + N_TAIL_A
VN_B = N_B + (N_139_WIN - N_139_A) + N_TAIL_B
VN_H = H_REL + DH_REPAIR + H_TAIL_TOTAL
VN_SAMPLE_CROSS = SEQ[-2][3]          # the frozen sample on the repaired stat

print('\nTHE SEQUENCE')
for lab, w, s, c in SEQ:
    print('  %-30s %5d windows %4d stars %4d crossings' % (lab, w, s, c))
print('v4.09 extent: %d windows (%d A + %d B) / %d stars / %d systems / '
      '%d crossings / %.2f h' % (VN_WIN, VN_A, VN_B, VN_STAR, N_SYS, VN_CROSS,
                                 VN_H))

m('VnWindows', '%d' % VN_WIN)
m('VnWinA', '%d' % VN_A)
m('VnWinB', '%d' % VN_B)
m('VnStars', '%d' % VN_STAR)
m('VnSystems', '%d' % N_SYS)
m('VnNHits', '%d' % VN_CROSS)
m('VnNHitsSample', '%d' % VN_SAMPLE_CROSS)
m('VnHours', '%.2f' % VN_H)
m('VnHoursRepair', '%.2f' % DH_REPAIR)
m('VnHoursTail', '%.2f' % H_TAIL_TOTAL)
m('VnHoursTailHD', '%.2f' % H_TAIL_HD)
m('VnHoursTailDecl', '%.2f' % H_TAIL_DECL)
m('VnSeqWrongWin', '%d' % SEQ[0][1])
m('VnSeqWrongStar', '%d' % SEQ[0][2])
m('VnSeqRestoredWin', '%d' % SEQ[2][1])
m('VnSeqRestoredHits', '%d' % SEQ[2][3])
m('VnSeqRepairedHits', '%d' % SEQ[3][3])

# ===========================================================================
# 5.  THE CROSSING DELTA -- eight rows, and the rank screen on every one
# ===========================================================================
HDR = J('hd14055_recur.json')
EV = {e['tag']: e for e in HDR['events']}
HDFF = {(w['eb'], w['spw']): w for w in HD}


def rank_of(eb, spw):
    """(n_ctrl_ge_star, n_ctrl, ctrl_max) from the REPAIRED product's own
    512-point control vector, not from a flag."""
    f = FF.get((eb, spw))
    if f is None:
        return None
    return f['n_ge'], f['n_ctrl'], f['ctrl_max'], f['star_snr'], f['pkf']


DELTA = []      # (kind, star, eb, nu_released, T_old, T_new, n_ge, n_ctrl,
                #  line, dv_kms, status)
for x, r in FELL:
    eb, spw = r['eb'], r['spw']
    rk = rank_of(eb, spw)
    DELTA.append(dict(kind='fell', star=x['star_name'], eb=eb, spw=spw,
                      nu=float(x['f_cross_GHz']),
                      t_old=float(x['star_snr']), t_new=r['new_star_peak_snr'],
                      n_ge_old=int(x['n_ctrl_ge_star']),
                      n_ge=rk[0], n_ctrl=rk[1], ctrl_max=rk[2],
                      line=x['nearest_line'],
                      dv=float(x['line_offset_kms']),
                      status='below the trigger; no longer a crossing'))
for x, r in ROSE:
    eb, spw = r['eb'], r['spw']
    rk = rank_of(eb, spw)
    ln, dv = nearest_line(rk[4])
    DELTA.append(dict(kind='rose', star=x['star_name'], eb=eb, spw=spw,
                      nu=rk[4], t_old=float(x['star_snr']),
                      t_new=r['new_star_peak_snr'],
                      n_ge_old=int(x['n_ctrl_ge_star']),
                      n_ge=rk[0], n_ctrl=rk[1], ctrl_max=rk[2],
                      line=ln, dv=dv,
                      status=None))
ln, dv = nearest_line(COMP3['pkf'])
DELTA.append(dict(kind='restored', star='HD 139084 B',
                  eb='A002_Xcd8029_Xb6b0', spw=3, nu=COMP3['pkf'],
                  t_old=float(PRIM3['star_snr']), t_new=COMP3['star_snr'],
                  n_ge_old=int(PRIM3['n_ctrl_ge_star']),
                  n_ge=COMP3['n_ge'], n_ctrl=COMP3['n_ctrl'],
                  ctrl_max=COMP3['ctrl_max'], line=ln, dv=dv,
                  status=None))
for tag in ('A', 'B'):
    e = EV[tag]
    w = HDFF[(e['eb'], e['spw'])]
    ln, dv = nearest_line(e['f_GHz'])
    # the stellar frame: the block's own barycentric term and the star's own
    # systemic velocity.  Sky-frame attribution would be the wrong test.
    dv_stel = dv - e['v_corr_kms'] + HDR['v_sys_kms']
    R_INF = [q for q in HDR['rows']
             if q['event'] == tag and not q['is_discovery'] and q['sig'] < 5e-3]
    wsum = sum(1.0 / q['sig'] ** 2 for q in R_INF)
    abar = sum(q['amp'] / q['sig'] ** 2 for q in R_INF) / wsum
    sbar = wsum ** -0.5
    DELTA.append(dict(kind='tail', star='HD 14055', eb=e['eb'], spw=e['spw'],
                      nu=e['f_GHz'], t_old=None, t_new=e['T_disc'],
                      n_ge_old=None, n_ge=None,
                      n_ctrl=w['nctrl'], ctrl_max=w['ctrl'],
                      line=ln, dv=dv, dv_stel=dv_stel,
                      excl_inf=(e['amp_disc'] - abar) / sbar,
                      excl_all=e['all_other']['exclusion_sigma'],
                      t_pers=e['amp_disc'] / sbar,
                      n_inf=len(R_INF), n_eff=e['n_eff_epochs'],
                      status='new; unattributed, excluded as persistent'))
# ★ The tail blocks' rank screens: the two new crossings' own 512-position
#   control rings, recomputed by `hd14055_chain.py` as the survey froze the
#   screen (the star must exceed ALL controls) rather than read off a flag.
#   They are carried as declared inputs because the tail products are not in
#   this deposit; V4 requires both to FAIL the screen, which is the direction
#   that matters, and the control-ring maxima in `hd14055_results.json`
#   independently exceed the star in both windows.
TAIL_NGE = {'A002_X1190de8_Xd526': 49, 'A002_X11adad7_X25c5e': 3}
TAIL_NGE_SRC = ('the two blocks\' own 512-position control rings '
                '(hd14055_chain.json, reproduced in hd14055_results.json)')
for d in DELTA:
    if d['kind'] == 'tail':
        d['n_ge'] = TAIL_NGE[d['eb']]
# ★ the status of the two line-attributed additions is WRITTEN FROM THE
#   MEASUREMENT, not typed beside it.  The science-input note for this round
#   quoted the risen crossing at "-28 km/s"; -28.1 is its offset in MHz and
#   -32.1 km/s is the velocity, so a typed status here would have shipped a
#   unit error into a table caption.
_TEXLINE = {'CO(2-1)': r'CO($2{\to}1$)',
            'CO(3-2)': r'CO($3{\to}2$)'}
for d in DELTA:
    if d['status'] is None:
        d['status'] = ('%s; %s at $%+.0f$\,km\,s$^{-1}$'
                       % ('new' if d['kind'] == 'rose' else 'restored',
                          _TEXLINE.get(d['line'], d['line']), d['dv']))

N_FELL, N_ROSE, N_RESTORED, N_TAILC = (
    sum(1 for d in DELTA if d['kind'] == k)
    for k in ('fell', 'rose', 'restored', 'tail'))
m('VnNHitsFell', '%d' % N_FELL)
m('VnNHitsRose', '%d' % N_ROSE)
m('VnNHitsRestored', '%d' % N_RESTORED)
m('VnNHitsTail', '%d' % N_TAILC)
m('VnDeltaRows', '%d' % len(DELTA))
for _d in DELTA:
    if _d['kind'] == 'rose':
        m('VnDeltaRoseDv', '%+.1f' % _d['dv'])
        m('VnDeltaRoseLine', _d['line'].replace('(2-1)', r'($2{\to}1$)'))
        m('VnDeltaRoseEB', _d['eb'].replace('_', r'\_'))
        m('VnDeltaRoseT', '%.4f' % _d['t_new'])
        m('VnDeltaRoseTOld', '%.4f' % _d['t_old'])
        _rr = [r for _x, r in ROSE][0]
        m('VnDeltaRoseRmsOld', '%.2f' % _rr['old_rms_combined_mJy'])
        m('VnDeltaRoseRmsNew', '%.2f' % _rr['new_rms_combined_mJy'])
    if _d['kind'] == 'restored':
        m('VnDeltaRestoredDv', '%+.1f' % _d['dv'])
        m('VnDeltaRestoredT', '%.4f' % _d['t_new'])
        m('VnDeltaRestoredTPrim', '%.4f' % _d['t_old'])
        m('VnDeltaRestoredCtrlMax', '%.3f' % _d['ctrl_max'])
        m('VnDeltaRestoredNGe', '%d' % _d['n_ge'])
m('VnDtMedian', '%+.3f' % DT_SIGNED_MED)
m('VnDtNoopMed', '%.3f' % DT_NOOP_MED)
m('VnDtNoopMax', '%.3f' % DT_NOOP_MAX)
m('VnDtNoopN', '%d' % len(NOOP))
m('VnDtMedianAbs', '%.3f' % DT_MED)
m('VnReextWin', '%d' % SUM['n_windows'])
m('VnReextBlock', '%d' % SUM['n_blocks'])
m('VnReextPaired', '%d' % SUM['n_paired'])
m('VnReextJoined', '%d' % len(pairs))
m('VnReextOnsrcRatio', '%.4f' % SUM['median_on_source_ratio'])
m('VnReextRmsRatio', '%.4f' % SUM['median_rms_ratio'])
m('VnReextHoursOld', '%.2f' % SUM['total_on_source_h_old'])
m('VnReextHoursNew', '%.2f' % SUM['total_on_source_h_new'])
# ★ how many of the harvest's windows a lower-edge-only join would have lost:
#   those whose spectral axis descends, so that the product's own first
#   frequency is the interval MAXIMUM
m('VnReextReversed', '%d' % sum(
    1 for r in ROWS if r['old_freq_lo_GHz'] is not None
    and r['old_freq_lo_GHz'] > r['old_freq_hi_GHz']))
m('VnDecisionDate', '2026 September 27')

print('\nTHE CROSSING DELTA')
for d in DELTA:
    print('  %-8s %-26s %-22s %12.6f  %s -> %.4f  ctrl>=star %s/%s'
          % (d['kind'], d['star'][:26], d['eb'], d['nu'],
             ('%.4f' % d['t_old']) if d['t_old'] is not None else '   --- ',
             d['t_new'], d['n_ge'], d['n_ctrl']))


def tname(s):
    s = s.split('  Gaia')[0].split(' (Gaia')[0].split(' Gaia')[0]
    s = s.replace('tau Cet', r'$\tau$~Cet').replace('eta Crv', r'$\eta$~Crv')
    return s.replace('-', '--').replace(' ', '~')


T = [r'\begin{tabular}{@{}l@{~}l@{~~}r@{~~}r@{~}c@{~}r@{~~}r@{~~}l@{}}',
     r'\hline',
     r'& Star & $\nu$ (GHz) & \multicolumn{3}{c}{$T_\star$} '
     r'& $n_{\rm c}$ & Status \\',
     r'& & & v4.08 & & v4.09 & & \\', r'\hline']
SYM = {'fell': '$-$', 'rose': '$+$', 'restored': '$+$', 'tail': '$+$'}
for d in DELTA:
    T.append(r'%s & %s & %.6f & %s & $\to$ & %.4f & %d & %s \\'
             % (SYM[d['kind']], tname(d['star']), d['nu'],
                ('%.4f' % d['t_old']) if d['t_old'] is not None else '---',
                d['t_new'], d['n_ge'], d['status']))
T += [r'\hline', r'\end{tabular}']
open(out('tab_crossdelta_v409.tex'), 'w').write(
    '%% GENERATED by v409_calc.py -- do not hand-edit.\n' + '\n'.join(T) + '\n')

# the machine-readable record of the adopted statistic, deposited beside the
# catalogue so a reader can recompute the delta rather than trust the table
with open(out('repaired_v409.csv'), 'w', newline='') as fh:
    wr = csv.writer(fh)
    wr.writerow(['eb', 'spw', 'star', 'band', 'flo_GHz', 'fhi_GHz',
                 'chanw_Hz', 'on_source_s_released', 'on_source_s_repaired',
                 'n_int_released', 'n_int_repaired', 'rms_mJy_released',
                 'rms_mJy_repaired', 'smin_Jy_released', 'smin_Jy_repaired',
                 'star_peak_snr_released', 'star_peak_snr_repaired',
                 'joined_to_catalogue'])
    joined = {(x['eb'], r['spw']) for x, r in pairs}
    for r in ROWS:
        if r['old_rms_combined_mJy'] is None:
            continue
        wr.writerow([r['eb'], r['spw'], r['star'], r['band'],
                     '%.6f' % min(r['new_freq_lo_GHz'], r['new_freq_hi_GHz']),
                     '%.6f' % max(r['new_freq_lo_GHz'], r['new_freq_hi_GHz']),
                     '%.1f' % r['new_chanwidth_Hz'],
                     '%.3f' % r['old_on_source_s'],
                     '%.3f' % r['new_on_source_s'],
                     r['old_n_int'], r['new_n_int'],
                     '%.6f' % r['old_rms_combined_mJy'],
                     '%.6f' % r['new_rms_combined_mJy'],
                     '%.8f' % r['old_S_min_measured_Jy'],
                     '%.8f' % r['new_S_min_measured_Jy'],
                     '%.4f' % r['old_star_peak_snr'],
                     '%.4f' % r['new_star_peak_snr'],
                     int((r['eb'], r['spw']) in joined)])

# ===========================================================================
# 6.  the clustering, on the repaired population
# ===========================================================================
SC = J('scan_v409.json')
POP, SHIP, RELP, REP = (SC['population'], SC['shipped'],
                        SC['released_products'], SC['repaired'])
m('VnClustNWin', '%d' % POP['n_co32_windows'])
m('VnClustNStar', '%d' % POP['n_co32_stars'])
m('VnClustNCross', '%d' % POP['n_co32_crossings'])
m('VnClustNRepointed', '%d' % POP['n_repointed'])
m('VnClustNFineLine', '%d' % POP['n_fine_line_windows'])
CLUSTKEYS = ['fixed_sky', 'scan150_sky', 'ladder_sky',
             'fixed_stel', 'scan150_stel', 'ladder_stel']
for key, tag in (('fixed_sky', 'FixedSky'), ('scan150_sky', 'ScanSky'),
                 ('ladder_sky', 'LadderSky'), ('fixed_stel', 'FixedStel'),
                 ('scan150_stel', 'ScanStel'),
                 ('ladder_stel', 'LadderStel')):
    # ★ The names here are the ones the round's own adoption list fixes, so
    #   the assertion `\ClustShippedFixedP < \ClustFixedSkyP` reads in the
    #   build exactly as it is written in the decision record.
    nobs, p = REP[key]
    m('Clust%sObs' % tag, '%d' % nobs)
    m('Clust%sP' % tag, pfmt(p))
    nobs, p = SHIP[key]
    m('ClustShipped%sObs' % tag, '%d' % nobs)
    m('ClustShipped%sP' % tag, pfmt(p))
    nobs, p = RELP[key]
    m('ClustRel%sObs' % tag, '%d' % nobs)
    m('ClustRel%sP' % tag, pfmt(p))
m('VnClustNLostToRepair', '3')
m('VnClustNLostHRTen', '2')
m('ClustShippedObs', '%d' % SHIP['fixed_sky'][0])
m('VnClustBandLo', '345.48')
m('VnClustBandHi', '345.64')

CT = [r'\begin{tabular}{@{}llr@{~}lr@{~}lr@{~}l@{}}', r'\hline',
      r'Frame & Statistic & \multicolumn{2}{c}{as shipped} '
      r'& \multicolumn{2}{c}{released products} '
      r'& \multicolumn{2}{c}{\textbf{repaired}} \\',
      r' & & $n$ & $p$ & $n$ & $p$ & $n$ & $p$ \\', r'\hline']
LBL = [('fixed_sky', 'sky', r'fixed $-300$ to $-140$\,km\,s$^{-1}$'),
       ('scan150_sky', 'sky', 'scan, position free'),
       ('ladder_sky', 'sky', 'scan, position and width free'),
       ('fixed_stel', 'stellar', r'fixed $-300$ to $-140$\,km\,s$^{-1}$'),
       ('scan150_stel', 'stellar', 'scan, position free'),
       ('ladder_stel', 'stellar', 'scan, position and width free')]


def pf(p):
    """the same value the macro carries, wrapped for math mode -- the table
    and the prose must not be able to round differently."""
    v = pfmt(p)
    return ('$%s$' % v) if '\\times' in v else v


prevframe = None
for key, frame, label in LBL:
    if prevframe is not None and frame != prevframe:
        CT.append(r'\hline')
    CT.append('%s & %s & %d & %s & %d & %s & \\textbf{%d} & \\textbf{%s} \\\\'
              % (frame if frame != prevframe else '', label,
                 SHIP[key][0], pf(SHIP[key][1]), RELP[key][0],
                 pf(RELP[key][1]), REP[key][0], pf(REP[key][1])))
    prevframe = frame
CT += [r'\hline', r'\end{tabular}']
open(out('tab_clust_v409.tex'), 'w').write(
    '%% GENERATED by v409_calc.py -- do not hand-edit.\n' + '\n'.join(CT)
    + '\n')

# ===========================================================================
# 7.  eta Crv's recurrence test
# ===========================================================================
EC = J('v409_recur_etacrv.json')
ECI = EC['informative']
m('VnEcrFreq', '%.6f' % EC['f_event_GHz'])
m('VnEcrDrift', '%.1f' % EC['drift_Hz_s'])
m('VnEcrT', '%.4f' % EC['T_published'])
m('VnEcrNWin', '%d' % EC['n_windows_on_disk'])
m('VnEcrNCover', '%d' % EC['n_covering'])
m('VnEcrOtherEB', EC['rows'][0]['eb'].replace('_', r'\_')
  if EC['rows'] else '')
m('VnEcrOtherT', '%+.3f' % ECI['T_max'])
m('VnEcrTPers', '%.2f' % ECI['T_if_persistent'])
m('VnEcrExcl', '%.2f' % ECI['exclusion_sigma'])
m('VnEcrNeff', '%.2f' % EC['n_eff'])
# the discovery's own sigma and the other epoch's, so "2.2x deeper" is a
# measured ratio and not an adjective
EC_DISC = [q for q in EC['rows'] if q['is_discovery']][0]
EC_OTH = [q for q in EC['rows'] if not q['is_discovery']][0]
m('VnEcrSigDisc', '%.5f' % EC_DISC['sig'])
m('VnEcrSigOther', '%.5f' % EC_OTH['sig'])
m('VnEcrDepthRatio', '%.2f' % (EC_DISC['sig'] / EC_OTH['sig']))
m('VnEcrDchan', '%+.1f' % EC_OTH['dchan_from_sky'])
m('VnEcrCtrlMax', '%+.2f' % EC_OTH['ctrl_T_max'])

# ===========================================================================
# 8.  HD 14055's two crossings, the exclusions, and the follow-up stratum
# ===========================================================================
FS = J('followup_stratum.json')
m('VnFollowNBlock', '%d' % FS['n_blocks'])
m('VnFollowNWin', '%d' % FS['n_windows'])
m('VnFollowHours', '%.2f' % FS['hours'])
m('VnFollowNInform', '%d' % FS['n_informative'])
m('VnFollowNInformCensus', '%d' % FS['n_informative_census'])
m('VnFollowNInformFollow', '%d' % FS['n_informative_followup'])
m('VnFollowNFine', '%d' % FS['n_fine'])
m('VnFollowNCoarse', '%d' % FS['n_coarse'])

for tag, pref in (('A', 'VnHdfA'), ('B', 'VnHdfB')):
    e = EV[tag]
    d = [x for x in DELTA if x['kind'] == 'tail' and x['eb'] == e['eb']][0]
    m(pref + 'EB', e['eb'].replace('_', r'\_'))
    m(pref + 'T', '%.4f' % e['T_disc'])
    m(pref + 'Freq', '%.6f' % e['f_GHz'])
    m(pref + 'Drift', '%+.0f' % e['drift'])
    m(pref + 'Vcorr', '%+.3f' % e['v_corr_kms'])
    m(pref + 'DvSky', '%+.1f' % d['dv'])
    m(pref + 'DvStel', '%+.1f' % d['dv_stel'])
    m(pref + 'NGe', '%d' % d['n_ge'])
    m(pref + 'Pemp', '%.4f' % (d['n_ge'] / float(d['n_ctrl'])))
    m(pref + 'CtrlMax', '%.3f' % d['ctrl_max'])
    m(pref + 'NCover', '%d' % e['n_covering'])
    m(pref + 'NInform', '%d' % d['n_inf'])
    m(pref + 'ExclInform', '%.2f' % d['excl_inf'])
    m(pref + 'ExclAll', '%.2f' % d['excl_all'])
    m(pref + 'TPers', '%.2f' % d['t_pers'])
    m(pref + 'Neff', '%.2f' % d['n_eff'])
    m(pref + 'ShallowPct', '%.1f' % (100 * e['frac_invvar_from_shallow']))
m('VnNCtrl', '%d' % DELTA[0]['n_ctrl'])
m('VnHdfNWin', '%d' % len(HD))
m('VnHdfNGeFive', '%d' % sum(1 for w in HD if w['T'] >= 5.0))
m('VnHdfCtrlBeats', '%d' % sum(1 for w in HD if w['ctrl'] > w['T']))
m('VnHdfNOther', '%d' % EV['A']['n_other'])
m('VnHdfNShallow', '%d' % (EV['A']['n_other'] - len(
    [q for q in HDR['rows']
     if q['event'] == 'A' and not q['is_discovery'] and q['sig'] < 5e-3])))
# how many covering epochs a SKY-frame match would have mis-addressed, i.e.
# where the stellar-frame match moves the cell by at least one channel
m('VnHdfNMoved', '%d' % len(
    [q for q in HDR['rows']
     if q['event'] == 'A' and not q['is_discovery']
     and abs(q['dchan_from_sky']) >= 1.0]))
m('VnHdfNDriftTrials', '125')
m('VnHdfCtrlGeFivePct', '%.1f'
  % (100.0 * sum(1 for w in HD for c in [w['ctrl']] if c >= 5.0) / len(HD)))
# the barycentric swing over every HD 14055 window on disk, which is why the
# stellar frame is not optional: 49 km/s is 58 channels of 488 kHz at 345 GHz
_bary = sorted(q['v_corr_kms'] for q in HDR['rows'])
m('VnNewBaryLo', '%+.1f' % _bary[0])
m('VnNewBaryHi', '%.1f' % _bary[-1])
m('VnNewBarySwing', '%.1f' % (_bary[-1] - _bary[0]))

# the chance set: every HD 14055 window's own control ring
HD_CTRL_N = sum(w['nctrl'] for w in HD)
m('VnHdfNCtrlMax', '%d' % HD_CTRL_N)

# ===========================================================================
# 9.  D36's three re-runs on the fixed position key
# ===========================================================================
AG = J('v409_aggrates.json')
ED = J('v409_edge_recheck.json')
AL = J('v409_allpop.json')
for cls, tag in (('A', 'A'), ('B', 'B'), ('all', 'All')):
    f, b = AG['fixed_key'][cls], AG['basename_key'][cls]
    m('VnAggRatio' + tag, '%.3f' % f['ratio'])
    m('VnAggRatioOld' + tag, '%.3f' % b['ratio'])
    m('VnAggRatio' + tag + 'Old', '%.3f' % b['ratio'])
    m('VnAggStarRate' + tag, '%.4e' % f['star_rate'])
    m('VnAggCtrlRate' + tag, '%.4e' % f['ctrl_rate'])
    m('VnAggNWin' + tag, '%d' % f['nwin'])
    m('VnAggCtrlEx' + tag, '%d' % f['cex'])
    m('VnAggCtrlExOld' + tag, '%d' % b['cex'])
    m('VnAggP' + tag, pfmt(f['poisson_p']))
m('VnAggRatioGainPct', '%.2f'
  % (100 * (AG['fixed_key']['all']['ratio']
            / AG['basename_key']['all']['ratio'] - 1)))
m('VnAggPopWin', '%d' % AL['n_old'])
m('VnAggPopDistinct', '%d' % AL['n_distinct'])
m('VnAggPopAdded', '%d' % AL['n_added'])
m('VnKeyNLostShipped', '%d' % AL['n_windows_lost_shipped'])
m('VnKeyNLostCorrected', '%d' % AL['n_windows_lost'])
m('VnKeyNCollidingBase', '%d' % AL['n_colliding_basenames'])
m('VnKeyNFineEntries', '%d' % AP['n_old_entries'])
m('VnKeyNFineDistinct', '%d' % AP['n_old_distinct'])
m('VnKeyNFineLost', '8')
m('VnKeyNReprofiled', '%d' % AP['n_new'])
m('VnKeyNInstances', '14')
m('VnOccColliding', '%d' % AG['occupancy_colliding'])
m('VnOccSeparated', '%d' % AG['occupancy_separated'])

m('VnEdgeRatio', '%.3f' % ED['pooled']['ratio'])
m('VnEdgeRatioOldKey', '2.386')
m('VnEdgeP', pfmt(ED['pooled']['poisson_p']))
m('VnEdgeDomStar', ED['dominating']['star'])
m('VnEdgeDomEB', ED['dominating']['eb'].replace('_', r'\_'))
m('VnEdgeDomN', '%d' % ED['dominating']['near_ex'])
m('VnEdgeDomPct', '%.0f' % (100 * ED['dominating']['frac']))
m('VnEdgeNoDomRatio', '%.3f' % ED['no_dominating']['ratio'])
m('VnEdgeNoDomP', '%.3f' % ED['no_dominating']['poisson_p'])
m('VnEdgeMaskRatio', '%.3f' % ED['line_masked']['ratio'])
m('VnEdgeMaskP', '%.3f' % ED['line_masked']['poisson_p'])
HALF_CLEAN, HALF_DOM = (ED['halves'] if ED['halves'][0]['ratio']
                        < ED['halves'][1]['ratio'] else ED['halves'][::-1])
m('VnEdgeHalfCleanRatio', '%.3f' % HALF_CLEAN['ratio'])
m('VnEdgeHalfCleanP', '%.2f' % HALF_CLEAN['poisson_p'])
m('VnEdgeHalfCleanN', '%d' % HALF_CLEAN['n'])
m('VnEdgeHalfDomRatio', '%.3f' % HALF_DOM['ratio'])
m('VnEdgeHalfDomP', pfmt(HALF_DOM['poisson_p']))
m('VnEdgeHalfDomN', '%d' % HALF_DOM['n'])
m('VnEdgeSeed', '20261004')

XC = J('v409_collision_xcheck.json')
m('VnXcNGroups', '%d' % XC['n_groups'])
m('VnXcNPinned', '%d' % XC['n_touching_pinned'])
m('VnXcPlxTol', '%.0e' % XC['plx_tol'])
m('VnXcNMerged', '%d' % XC['n_merged_identities'])

# ===========================================================================
# 10. CP-72 2713 and the visibility-fit coverage
# ===========================================================================
CP = json.load(open(os.path.join(HERE, 'visfit_r7v409_result.json')))
_cpk = [k for k in CP if k.startswith('CP-72')]
assert len(_cpk) == 1, _cpk
CPR = CP[_cpk[0]]
assert CPR['status'] == 'ok', CPR['status']
CPE = CPR['epoch']
# ★ READ, not typed.  Both conventions are in the fit's own record: the
#   ADOPTED epoch is the search product's own times[0] and the committed one
#   is median(TIME).  The record also carries the proof that A1 is satisfied
#   by measurement rather than by assertion --
#   `residual_channels_fit_first_to_extraction_first` is exactly zero.
m('VnCpReAdopted', '%.4f' % CPE['first']['star']['snr_re'])
m('VnCpImAdopted', '%.4f' % CPE['first']['star']['snr_im'])
m('VnCpReCommitted', '%.4f' % CPR['star']['snr_re'])
m('VnCpCtrlAdopted', '%.4f' % CPE['first']['ctrl_pos_max'])
m('VnCpCtrlCommitted', '%.4f' % CPR['ctrl_pos_max'])
m('VnCpDisp', '%.3f' % CPE['offset_channels_median_to_first'])
m('VnCpNVis', '{:,}'.format(CPR['star']['n_vis']).replace(',', r'\,'))
m('VnCpChan', '%d' % CPR['event']['chan'])
m('VnCpT', '%.3f' % CPR['event']['star_snr'])
m('VnCpResid', '%.1f' % CPE['residual_channels_fit_first_to_extraction_first'])
m('VnCpOffsetArcsec', '%.4f' % CPR['diag']['offset_arcsec'])
m('VnCpSciFrac', '%.1f' % CPR['diag']['science_row_fraction'])
# ★ READ from the ledger, not typed.  The science-input note for this round
#   quoted "52 of 56"; the deposited ledger's own count is one lower, because
#   its denominator is the 56 released crossings and it had 50 fitted before
#   this fit landed, not 51.  The number that ships is the ledger's.
def _texval(name):
    import glob as _g
    import re as _re
    for f in sorted(_g.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        mm = _re.search(r'\\newcommand\{\\%s\}\{([-+0-9.]+)\}' % name,
                        open(f, errors='replace').read())
        if mm:
            return float(mm.group(1))
    raise SystemExit('v409_calc: macro %s is not generated yet' % name)


VIS_FIT = int(_texval('LgNFit'))
VIS_UNFIT = int(_texval('LgNUntest'))
m('VnVisNFitted', '%d' % VIS_FIT)
m('VnVisNUnfitted', '%d' % VIS_UNFIT)
m('VnVisNUnfitBlocks', '%d' % int(_texval('LgNUntestBlocks')))

# ===========================================================================
# 11. the named block, and the delivery record
# ===========================================================================
NS = J('neverstarted_v409.json')
DL = J('etacrv_delivery.json')
m('VnNsEB', NS['eb'].replace('_', r'\_'))
m('VnNsStar', r'$\eta$~Crv')
m('VnNsBand', NS['band'].replace('B', ''))
m('VnNsGB', '%.1f' % NS['gb'])
m('VnNsMous', r'\texttt{%s}' % NS['mous'])
m('VnNsFate', DL['correct_fate'].replace('_', r'\_'))
m('VnNsNEB', '%d' % DL['delivery']['n_ebs_offered'])
m('VnNsNCal', '%d' % DL['delivery']['n_with_calapply'])
m('VnNsSibling', DL['delivery']['calapply'][1].replace('_', r'\_'))
m('VnNsCoverEB', DL['delivery']['calapply'][0].replace('_', r'\_'))
m('VnNsCtrlNBlock', '361')
m('VnNsCtrlNResolved', '0')
m('VnNsCtrlNFailed', '10')

# ===========================================================================
# 12. ASSERTIONS -- each one driven, and each one driven BOTH WAYS where it
#     has two directions
# ===========================================================================
print('\nassertions')

n_a, n_b, n_w = VN_A, VN_B, VN_WIN
if DRIVE == 2:
    n_b += 1
ck('V1  VnWinA + VnWinB == VnWindows', n_a + n_b == n_w,
   '%d + %d == %d' % (n_a, n_b, n_w))

closes = (N_CROSS - N_FELL + N_ROSE + N_RESTORED + N_TAILC)
if DRIVE == 3:
    closes += 1
ck('V2  the crossing delta closes on VnNHits',
   closes == VN_CROSS and (N_FELL + N_ROSE + N_RESTORED + N_TAILC) == 8,
   '%d - %d + %d + %d + %d == %d over %d rows'
   % (N_CROSS, N_FELL, N_ROSE, N_RESTORED, N_TAILC, closes, len(DELTA)))

# ★ THE REPAIR IS A NO-OP WHERE NOTHING WAS LOST, which is what distinguishes
#   a repair from a re-tuning.  THREE separate statements, because the science
#   inputs ran two of them together: `V409_INPUTS` and `DECISIONS_R8` D35/D36
#   both quote "median |dT*| = +0.071", but a median of absolute values cannot
#   carry a sign.  +0.0714 is the median SIGNED shift (the repair is unbiased);
#   the median ABSOLUTE shift is 0.3531; and the no-op claim belongs to the
#   windows where no on-source time was recovered, where it is 0.057.
lim = 0.15 if DRIVE not in (4, 5) else (0.001 if DRIVE == 4 else 1e9)
ck('V3a the repair is UNBIASED in the median signed shift',
   abs(DT_SIGNED_MED) < lim if DRIVE != 5 else abs(DT_SIGNED_MED) > lim,
   'median signed dT* = %+.4f against %.3g' % (DT_SIGNED_MED, lim))
ck('V3b and it is a no-op on the %d windows that recovered no time' % len(NOOP),
   DT_NOOP_MED < (0.1 if DRIVE != 6 else 0.0),
   'median |dT*| = %.4f, max %.3f over %d windows'
   % (DT_NOOP_MED, DT_NOOP_MAX, len(NOOP)))
ck('V3c but it is NOT a no-op on the crossings: they move materially',
   min(abs(d['t_new'] - d['t_old']) for d in DELTA
       if d['t_old'] is not None) > 0.1 if DRIVE != 7 else False,
   'crossing moves %s'
   % ['%.3f' % abs(d['t_new'] - d['t_old'])
      for d in DELTA if d['t_old'] is not None])

bad = [d['eb'] for d in DELTA if not (d['n_ge'] > 0)]
if DRIVE == 8:
    bad = ['forced']
ck('V4  all 8 delta rows have a control above the star (screen fails)',
   not bad, '%d rows, controls>=star %s'
   % (len(DELTA), [d['n_ge'] for d in DELTA]))

att = [d for d in DELTA if d['kind'] in ('rose', 'restored')]
tai = [d for d in DELTA if d['kind'] == 'tail']
ck('V5a both additions are line-attributed inside the frozen mask',
   all(abs(d['dv']) <= MASK_KMS for d in att) if DRIVE != 9 else False,
   'dv = %s km/s against +-%.0f' % (['%.1f' % d['dv'] for d in att],
                                    MASK_KMS))
ck('V5b both tail crossings are UNATTRIBUTED in the stellar frame',
   all(abs(d['dv_stel']) > MASK_KMS for d in tai) if DRIVE != 10 else False,
   'dv_stellar = %s km/s' % ['%.1f' % d['dv_stel'] for d in tai])

# V4 of the adoption list: the post-hoc band may never be printed as the
# result.  The shipped fixed-band p must be SMALLER than the corrected one,
# so transposing the two is a build failure.
p_ship = SHIP['fixed_sky'][1]
p_rep = REP['fixed_sky'][1] if DRIVE != 11 else 1e-9
ck('V6  ClustShippedFixedSkyP < ClustFixedSkyP',
   p_ship < p_rep, '%.2g < %.3f' % (p_ship, p_rep))
ck('V6b every CORRECTED clustering statistic is non-significant',
   all(REP[k][1] > 0.01 for k in CLUSTKEYS) if DRIVE != 12 else False,
   'min corrected p = %.3f' % min(REP[k][1] for k in CLUSTKEYS))

# V5 of the adoption list, enforced mechanically: the edge excess cannot be
# emitted without the one-window share and a held-out half beside it.
names = {o.split('}')[0].split('{\\')[-1] for o in OUT}
need = {'VnEdgeRatio', 'VnEdgeDomPct', 'VnEdgeHalfCleanRatio',
        'VnEdgeHalfCleanP', 'VnEdgeNoDomRatio'}
if DRIVE == 13:
    names.discard('VnEdgeHalfCleanRatio')
ck('V7  the edge excess is emitted only with its share and a held-out half',
   need <= names, 'missing %s' % sorted(need - names))
# ★★ V7c: and EMITTING them is not enough.  `retire_macros.py` strips any
#     macro the manuscript does not reference -- the mechanism that removed
#     the P90 budget's transfer row for four versions -- so D5's condition is
#     only really enforced if the manuscript REFERENCES the one-window share
#     and the held-out half wherever it quotes the pooled ratio.
import manuscript  # v4.10: split manuscript
# v4.10: the manuscript is split into sections/, so this must read the
# FLATTENED document.  Reading the main file alone leaves this check
# looking at a preamble, where it can only be vacuous or wrong.
_body = manuscript.flat()
_cited = ('\\VnEdgeRatio' in _body)
_guards = all(('\\' + n) in _body for n in
              ('VnEdgeDomPct', 'VnEdgeHalfCleanRatio', 'VnEdgeHalfCleanP',
               'VnEdgeNoDomRatio'))
if DRIVE == 18:
    _guards = False
if DRIVE == 20:
    _cited = False
# ★★ V7c AMENDED (round 9).  It used to read `(not _cited) or _guards`, i.e.
#    it only bit if the manuscript happened to quote the ratio -- so when the
#    appendix that quoted it was deleted, the check went VACUOUS and the
#    limitation it protects was left stated in words with no macro in it,
#    where neither `prosenum` nor `intsweep` can see it and a later pass can
#    delete the sentence without anything objecting.  A limitation protected
#    by nothing is not protected.  The citation is now REQUIRED, not merely
#    guarded: the pooled ratio, the one-window share, the ratio without that
#    window and the held-out half must all appear in the manuscript.
ck('V7c the manuscript cites the near-edge ratio AND the share and the half '
   'that withdraw it',
   _cited and _guards,
   'ratio cited %s, guards referenced %s' % (_cited, _guards))
ck('V7b the withdrawal survives: without the one window the ratio is ~1',
   abs(ED['no_dominating']['ratio'] - 1.0) < 0.1 if DRIVE != 14 else False,
   'x%.3f, p = %.3f' % (ED['no_dominating']['ratio'],
                        ED['no_dominating']['poisson_p']))

# the fixed key must STRENGTHEN the contrast in Class A and leave Class B
# untouched to the last digit, because every collision is a fine spw3 window
ck('V8a the fixed key strengthens the star/control contrast',
   (AG['fixed_key']['all']['ratio'] > AG['basename_key']['all']['ratio']
    if DRIVE != 15 else False),
   '%.3f > %.3f' % (AG['fixed_key']['all']['ratio'],
                    AG['basename_key']['all']['ratio']))
ck('V8b Class B is untouched, to the last digit',
   abs(AG['fixed_key']['B']['ratio'] - AG['basename_key']['B']['ratio']) < 1e-12,
   '%.12f vs %.12f' % (AG['fixed_key']['B']['ratio'],
                       AG['basename_key']['B']['ratio']))

# ★ AN ASSERTION THAT COULD ONLY EVER FAIL ON GOOD DATA IS AS USELESS AS ONE
#   THAT CANNOT FAIL (D36).  The quantity quoted for HD 14055 is the
#   informative-epoch exclusion, which must be the CONSERVATIVE one; the
#   21 ACA-sensitivity epochs are declared, not counted.
pairs_excl = [(d['excl_inf'], d['excl_all']) for d in tai]
ck('V9  the quoted exclusion is the conservative, informative-epoch one',
   all(i < a for i, a in pairs_excl) if DRIVE != 16 else False,
   ' '.join('%.2f<%.2f' % p for p in pairs_excl))
ck('V9b the 21 shallow epochs carry a negligible share of the weight',
   all(e['frac_invvar_from_shallow'] < 0.05 for e in EV.values()),
   '%s' % ['%.3f' % e['frac_invvar_from_shallow'] for e in EV.values()])

ck('V10 eta Crv has exactly two covering epochs and the other is deeper',
   EC['n_covering'] == 2 and EC_OTH['sig'] < EC_DISC['sig'],
   '%d epochs, sigma %.5f vs %.5f' % (EC['n_covering'], EC_OTH['sig'],
                                      EC_DISC['sig']))
# N_eff is EQUIVALENT DISCOVERY EPOCHS, sum (sigma_disc/sigma_i)^2, which
# EXCEEDS the epoch count whenever the other epochs are deeper.  Assert the
# identity and REPORT the direction.
neff_id = sum((EC_DISC['sig'] / q['sig']) ** 2
              for q in EC['rows'] if not q['is_discovery'])
ck('V10b N_eff closes on sum (sigma_disc/sigma_i)^2',
   abs(neff_id - EC['n_eff']) < 1e-6 * max(1.0, EC['n_eff']),
   '%.6f vs %.6f -- and it EXCEEDS n=%d, which is the deeper-epoch case'
   % (neff_id, EC['n_eff'], EC['n_covering'] - 1))

ck('V11 the computed part of the tail hours reproduces',
   abs(H_TAIL_HD - 9.334) < 0.01 and H_TAIL_DECL > 0,
   '%.3f h computed from 12 windows + %.3f h declared = %.3f h'
   % (H_TAIL_HD, H_TAIL_DECL, H_TAIL_TOTAL))

# V6 of the adoption list, checked on this generator's own behaviour
ck('V12 under a drive, no output can land on a path production reads',
   (SUF != '') if DRIVE is not None else (SUF == ''),
   'suffix %r' % SUF)

ck('V15 the visibility-fit coverage closes on the crossing count',
   VIS_FIT + VIS_UNFIT == (N_CROSS if DRIVE != 19 else N_CROSS + 1),
   '%d fitted + %d outstanding == %d released crossings'
   % (VIS_FIT, VIS_UNFIT, N_CROSS))
ck('V13 the HD 139084 pair is two stars, and pb offset cannot separate them',
   abs(PB_COMP - PB_PRIM) < 0.2 and len(COMP) == 4,
   'pb %.4f" vs %.4f", delta %.3f" against 10.32" on sky'
   % (PB_COMP, PB_PRIM, abs(PB_COMP - PB_PRIM)))

# the duplicated transition list may not drift from v342_calc.py's
src = open(os.path.join(HERE, 'v342_calc.py')).read()
ok12 = True
for nm, nu in LINES.items():
    tok = "'%s':" % nm
    i = src.find(tok)
    if i < 0:
        ok12 = False
        break
    val = src[i + len(tok):src.find(',', i)].strip()
    if abs(float(val) - nu) > 1e-9:
        ok12 = False
if DRIVE == 17:
    ok12 = False
ck('V14 the transition list agrees with v342_calc.py on all %d lines'
   % len(LINES), ok12)

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('v409_calc: %d assertion(s) failed: %s' % (len(fail),
                                                                fail))

# ===========================================================================
# 13. the tail ledger table
# ===========================================================================
TT = [r'\begin{tabular}{@{}l@{~}l@{~}r@{~}l@{}}', r'\hline',
      r'Execution block & Star & ASDM & Outcome \\',
      r' & & (GB) & \\', r'\hline']
for b in sorted(TC, key=lambda b: (not b.get('done'), b['eb'])):
    star = b['star'].split('[')[0].split('(Gaia')[0].strip()
    star = (star.replace('bet Pic', r'$\beta$~Pic')
            .replace('HD', 'HD~').replace('HD~ ', 'HD~').replace(' ', ''))
    star = star.replace('HD~', 'HD\\,')
    if b.get('done'):
        o = 'searched, 4/4'
    elif 'ABORTED' in b['verdict'] or 'aborted' in b.get('status', ''):
        o = 'aborted (working set)'
    elif b.get('status') == 'running':
        o = 'gate-bound (working set)'
    else:
        o = 'deferred (working set)'
    TT.append(r'\texttt{%s} & %s & %.1f & %s \\'
              % (b['eb'].replace('_', r'\_'), star, b['gb'], o))
TT += [r'\hline', r'\end{tabular}']
open(out('tab_tail_v409.tex'), 'w').write(
    '%% GENERATED by v409_calc.py -- do not hand-edit.\n' + '\n'.join(TT)
    + '\n')
m('VnTailNBlock', '%d' % len(TC))
m('VnTailNDone', '%d' % N_TAIL_BLOCK)
m('VnTailNWin', '%d' % N_TAIL_WIN)
m('VnTailFalsified', '2')
m('VnTailWorstRatio', '8.32')
m('VnTailFloorGB', '246')

open(out('survey_numbers_round102.tex'), 'w').write(
    '%% GENERATED by v409_calc.py -- do not hand-edit.\n' + '\n'.join(OUT)
    + '\n')
print('\nwrote %s (%d macros), %s (%d rows), %s, %s, %s'
      % (os.path.basename(out('survey_numbers_round102.tex')), len(OUT),
         os.path.basename(out('tab_crossdelta_v409.tex')), len(DELTA),
         os.path.basename(out('tab_clust_v409.tex')),
         os.path.basename(out('tab_tail_v409.tex')),
         os.path.basename(out('repaired_v409.csv'))))
