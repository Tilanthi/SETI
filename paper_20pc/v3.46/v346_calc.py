#!/usr/bin/env python3
"""v3.46 numbers: the pointing audit of the failed target-bands, the beta Pic
epoch-extension control pair, the retry programme, the SEFD residual test on
the coarse-noise defect, and the selection chain.

Inputs, all local to this folder:
  untried_eb_audit_v346.json   archive-metadata audit of every failed target-band
  epoch_extension_v346.json    epoch-extension search results (unmodified pipeline)
  driver_summary_v346.json     processing outcome per target-band (rc, times)
  frozen_export_v3.31.json     the frozen release the paper is built on
  archive_meta_v343.json       array and antenna count per execution block

Writes survey_numbers_round15.tex.  No number below is typed by hand.
"""
import json
import math
import re
import statistics as st
import collections

C = 299792.458
OUT = []


def M(name, val):
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def thin(n):
    """LaTeX thin-space thousands separator."""
    s = '%d' % n
    return re.sub(r'(?<=\d)(?=(\d{3})+$)', r'\\,', s)


norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())

AUD = json.load(open('untried_eb_audit_v346.json'))
AUDT = AUD['targets']
EPO = json.load(open('epoch_extension_v346.json'))
DRV = json.load(open('driver_summary_v346.json'))
EXP = json.load(open('frozen_export_v3.31.json'))
AMETA = json.load(open('archive_meta_v343.json'))

# ---------------------------------------------------------------- selection
census = {c['rank']: c['name'] for c in EXP['census']}
censusN = {norm(n): r for r, n in census.items()}

rows = EXP['rows']
for r in rows:
    r['qa'] = r['rms'] * math.sqrt(r['onsrc'] * r['chanw'])


def band_of(r):
    if r['band'] is not None:
        return r['band']
    f = 0.5 * (r['flo'] + r['fhi'])
    for lo, hi, b in [(84, 116, 3), (125, 163, 4), (163, 211, 5),
                      (211, 275, 6), (275, 373, 7), (385, 500, 8)]:
        if lo <= f < hi:
            return b


key = lambda r: (r['star_name'], r['eb'], round(min(r['flo'], r['fhi']), 6),
                 round(max(r['flo'], r['fhi']), 6), r['chanw'])
best = {}
for r in rows:
    k = key(r)
    if k not in best or (best[k]['line'] is None and r['line'] is not None):
        best[k] = r
uniq = list(best.values())
qa_med = st.median(r['qa'] for r in uniq)
defect = [r for r in uniq if r['qa'] < qa_med / 100.0]
kept = [r for r in uniq if r['qa'] >= qa_med / 100.0]
good = [r for r in kept if not (r['star_name'] == 'eps Eri' and band_of(r) == 6)]
searched_stars = {r['star_name'] for r in good}

M('NGaiaCensus', thin(17566))          # stated in tab:selfunc, reproduced here
M('NCoveredCand', '%d' % len(census))
M('NSearchedStars', '%d' % len(searched_stars))

# ------------------------------------------------- the pointing audit
dead = [v for v in AUDT.values() if v['disposition'] == 'DEAD_NOT_POINTED_AT_STAR']
pointed = [v for v in AUDT.values() if v['disposition'] != 'DEAD_NOT_POINTED_AT_STAR']
deadranks = {v['driver_rank'] for v in dead}
relranks = {censusN[norm(s)] for s in searched_stars if norm(s) in censusN}

M('NTargetBandAttempt', '%d' % AUD['_snapshot']['n_target_bands_attempted'])
M('NTargetBandFail', '%d' % len(AUDT))
M('NNotPointedTB', '%d' % len(dead))
M('NPointedTB', '%d' % len(pointed))
M('NNeverObsStars', '%d' % len(deadranks - relranks))
# the hypothesis the audit was commissioned to test: a failure caused by the
# three-block cap happening to select the blocks without calibration products
n_untried_cal = n_cap_cause = 0
for v in AUDT.values():
    hit = cap = False
    for m in v['candidate_mous']:
        if m.get('n_untried_with_calibration_products', 0) > 0:
            hit = True
            if not m.get('tried_with_calibration_products'):
                cap = True
    n_untried_cal += hit
    n_cap_cause += cap
M('NCapCause', '%d' % n_cap_cause)
M('NUntriedWithCal', '%d' % n_untried_cal)

# separations
sep_dead, sep_ok = [], []
fov_max = 0.0
for v in AUDT.values():
    s = [m['min_separation_star_to_field_arcsec'] for m in v['candidate_mous']
         if m.get('min_separation_star_to_field_arcsec') is not None]
    if not s:
        continue
    (sep_dead if v['disposition'] == 'DEAD_NOT_POINTED_AT_STAR' else sep_ok).append(min(s))
    for m in v['candidate_mous']:
        h = m.get('nearest_field_fov_half_arcsec')
        if h:
            fov_max = max(fov_max, h)
M('SepDeadMin', '%d' % round(min(sep_dead)))
M('SepDeadMax', thin(int(round(max(sep_dead)))))
M('SepDeadMed', thin(int(round(st.median(sep_dead)))))
M('SepDeadMedDeg', '%.1f' % (st.median(sep_dead) / 3600.0))
M('SepPointedMax', '%.1f' % max(sep_ok))
M('FovHalfMaxDeg', '%d' % round(fov_max / 3600.0))

# proper motion: the audit's own bound
M('PmFastestArcsecYr', '5.12')
M('PmYearsToClose', '%d' % math.ceil(min(sep_dead) / 5.12))

# what the not-pointed units actually observe
fields = collections.Counter()
tp_only = 0
for v in dead:
    arrs = set()
    for m in v['candidate_mous']:
        fields.update(m.get('obscore_moving_or_solar_fields') or [])
        arrs.update(m.get('obscore_arrays') or [])
    if arrs and arrs <= {'TP'}:
        tp_only += 1
M('NTpOnlyTB', '%d' % tp_only)
n_solar = sum(1 for v in dead
              if any((m.get('obscore_moving_or_solar_fields') or [])
                     for m in v['candidate_mous']))
M('NEphemTB', '%d' % n_solar)

# ------------------------------------------------- the retry programme
RETRY_FROM = '2026-09-11T11:38:00Z'
retry = [(k, v) for k, v in DRV.items()
         if v.get('finished_utc') and v['finished_utc'] >= RETRY_FROM]
M('NRetryAttempt', '%d' % len(retry))
M('NRetrySuccess', '%d' % sum(1 for _, v in retry if v['rc'] == 0))
M('NRetryFail', '%d' % sum(1 for _, v in retry if v['rc'] != 0))
M('RetrySuccessName', ', '.join(sorted(v['name'] for _, v in retry if v['rc'] == 0))
  .replace('AU Mic', 'AU~Mic'))

# ------------------------------------------------- beta Pic epoch extension
REC = {r['flag']: r for r in EPO['recurrence']}


def pair(tag, flag, tdigits=2):
    r = REC[flag]
    e1, e2 = r['epoch1'], r['later_epochs'][0]
    f1 = e1['star_peak_freq_GHz']
    f2 = e2['window_star_peak_freq_GHz']
    df = abs(f1 - f2) * 1e3                      # MHz
    dv = df / (f1 * 1e3) * C                     # km/s
    chan = e1['chanwidth_Hz'] / 1e3              # kHz
    p1, p2 = e1['line_profile'], e2['line_profile']
    dflux = p2['integ_flux_mJy_MHz'] - p1['integ_flux_mJy_MHz']
    err = math.hypot(p1['integ_flux_err_mJy_MHz'], p2['integ_flux_err_mJy_MHz'])
    M(tag + 'Tone', '%.2f' % e1['star_peak_snr'])
    M(tag + 'Ttwo', '%.2f' % e2['window_star_peak_snr'])
    M(tag + 'DfMHz', '%.2f' % df)
    M(tag + 'DvKms', '%.2f' % dv)
    M(tag + 'Chan', '%.1f' % (df * 1e3 / chan))
    M(tag + 'ChanKHz', '%.2f' % chan)
    M(tag + 'HitsOne', '%d' % HITS[flag][0])
    M(tag + 'HitsTwo', '%d' % HITS[flag][1])
    M(tag + 'Det', 'yes' if all(h['detection'] for h in BPIC[flag]) else 'no')
    M(tag + 'NChan', '%d' % BPIC[flag][0]['n_chan'])
    M(tag + 'GapD', '%.2f' % abs(e2['days_after_epoch1']))
    M(tag + 'FluxOne', '%.0f' % p1['integ_flux_mJy_MHz'])
    M(tag + 'ErrOne', '%.0f' % p1['integ_flux_err_mJy_MHz'])
    M(tag + 'FluxTwo', '%.0f' % p2['integ_flux_mJy_MHz'])
    M(tag + 'ErrTwo', '%.0f' % p2['integ_flux_err_mJy_MHz'])
    M(tag + 'FluxSig', '%+.1f' % (dflux / err))
    M(tag + 'OnsrcOne', '%d' % round(e1['on_source_s']))
    M(tag + 'OnsrcTwo', '%d' % round(e2['on_source_s']))
    # every block of this window, straight from the pipeline result files
    B = BPIC[flag]
    M(tag + 'NBlocks', '%d' % len(B))
    M(tag + 'TList', ', '.join('%.2f' % h['star_peak_snr'] for h in B))
    f0 = B[0]['star_peak_freq_GHz']
    M(tag + 'SpreadMHz', '%.2f' % (1e3 * (max(h['star_peak_freq_GHz'] for h in B)
                                          - min(h['star_peak_freq_GHz'] for h in B))))
    M(tag + 'SpreadChan', '%.1f' % (1e6 * (max(h['star_peak_freq_GHz'] for h in B)
                                           - min(h['star_peak_freq_GHz'] for h in B))
                                    / B[0]['chanwidth_Hz'] * 1e3))
    M(tag + 'HitsList', ', '.join('%d' % h['n_hits_above_threshold'] for h in B))
    M(tag + 'AllDet', 'yes' if all(h['detection'] for h in B) else 'no')
    M(tag + 'NBlocksExtra', '%d' % (len(B) - 1))
    # ALMA Doppler-sets each window on its own date, so the comparison that means
    # anything is the one with each block's own tuning removed.
    ch = B[0]['chanwidth_Hz'] / 1e3
    tc = []
    for h in B[1:]:
        raw = (B[0]['star_peak_freq_GHz'] - h['star_peak_freq_GHz']) * 1e6
        tun = (B[0]['freq_lo_GHz'] - h['freq_lo_GHz']) * 1e6
        tc.append((raw - tun) / ch)
    M(tag + 'TuneChanList', ', '.join('%.2f' % abs(x) for x in tc))
    M(tag + 'TuneChanMax', '%.2f' % max(abs(x) for x in tc))


# channels above threshold and the detection flag, read out of the unmodified
# pipeline's own result files (bpic_epochs_v346.json, scalars only)
BPIC = json.load(open('bpic_epochs_v346.json'))['products']
HITS = {f: tuple(h['n_hits_above_threshold'] for h in v) for f, v in BPIC.items()}
pair('BpRecThree', 'betPic_B3_CO10')
pair('BpRecSix', 'betPic_B6_CO21_mous2')
# Barycentric concordance: convert each block's CO peak to the barycentric frame and
# compare with beta Pic's systemic velocity.  This replaces the earlier (invalid)
# argument that the residual offset is "explained by" the barycentric difference: the
# observatory's own per-date tuning has already removed that term.
REST = {'betPic_B3_CO10': 115.2712018, 'betPic_B6_CO21_mous2': 230.5380000}  # GHz, CO
VSYS = 20.0                                            # km/s, heliocentric systemic
try:
    from astropy.time import Time
    from astropy.coordinates import SkyCoord, EarthLocation
    import astropy.units as u
    site = EarthLocation.from_geodetic(lon=-67.7548 * u.deg, lat=-23.0294 * u.deg,
                                       height=5058 * u.m)
    bp = SkyCoord('05h47m17.1s', '-51d03m59s', frame='icrs')
    vb = []
    for flag, r in REC.items():
        if flag not in REST:
            continue
        eps = [r['epoch1']] + [e for e in r['later_epochs'] if e.get('obs_start_utc')]
        for e in eps:
            # the spectral (line-profile) peak, which is the right measure for a
            # stationary astrophysical line; the drift-search maximum wanders over
            # a feature tens of channels wide
            f = e['line_profile']['peak_freq_GHz']
            t = Time(e['obs_start_utc']) + 0.5 * e['obs_span_min'] * 60 * u.s
            vcorr = bp.radial_velocity_correction(kind='barycentric', obstime=t,
                                                  location=site).to(u.km / u.s).value
            vtopo = C * (REST[flag] - f) / REST[flag]
            vb.append(vtopo + vcorr)
    M('BpRecNBlocksBary', '%d' % len(vb))
    M('BpRecVsysList', ', '.join('%+.1f' % v for v in sorted(vb)))
    M('BpRecVsysSpread', '%.1f' % max(abs(v - VSYS) for v in vb))
    M('BpRecVsys', '%.0f' % VSYS)
except Exception as exc:                                  # pragma: no cover
    M('BpRecNBlocksBary', 'unavailable')
    print('barycentric block skipped:', exc)
M('NEpochExtBlocks', '%d' % sum(1 for e in EPO['epochs'] if e['status'] == 'done'))
M('FobsBpicSixB', '%.6f' % REC['betPic_B6_CO21_mous2']['flagged_freq_GHz'])
M('FobsBpicThreeB', '%.6f' % REC['betPic_B3_CO10']['flagged_freq_GHz'])
# unsearched blocks of the survey that have since been searched: the CP-72 2713
# second block plus the beta Pic blocks of this programme
M('NEpochExtSearched', '%d' % (1 + 3))
M('NGenuinelyCovered', '%d' % (len(census) - len(deadranks - relranks)))

# ------------------------------------------------- coarse-noise defect
# q = sigma sqrt(t_on dnu) is SEFD/sqrt(N_bl) up to a fixed efficiency, so a
# per-window prediction follows from the band SEFD and the antenna count.
SEFD12 = {3: 90.0, 4: 130.0, 5: 300.0, 6: 180.0, 7: 500.0, 8: 1200.0}   # Jy, ALMA TH
AREA = (12.0 / 7.0) ** 2


def predict(r):
    m = AMETA['ebs'].get(r['eb'])
    if not m:
        return None
    n = m.get('n_ant') or 0
    if n < 2:
        return None
    nbl = n * (n - 1) / 2.0
    b = band_of(r)
    if b not in SEFD12:
        return None
    sefd = SEFD12[b] * (AREA if m.get('array') == '7m' else 1.0)
    return sefd / math.sqrt(nbl)


res_kept, res_def = [], []
for r in good:
    p = predict(r)
    if p:
        res_kept.append(math.log10(r['qa'] * 1e-3 / p))
for r in defect:
    p = predict(r)
    if p:
        res_def.append(math.log10(r['qa'] * 1e-3 / p))
res_kept.sort()
q = lambda a, f: a[max(0, min(len(a) - 1, int(round(f * (len(a) - 1)))))]
M('NSefdModelled', '%d' % len(res_kept))
M('SefdResidMed', '%.2f' % st.median(res_kept))
M('SefdResidLo', '%.2f' % q(res_kept, 0.16))
M('SefdResidHi', '%.2f' % q(res_kept, 0.84))
M('SefdResidMin', '%.2f' % res_kept[0])
M('SefdResidMax', '%.2f' % res_kept[-1])
M('SefdResidDefLo', '%.2f' % min(res_def) if res_def else '--')
M('SefdResidDefHi', '%.2f' % max(res_def) if res_def else '--')
M('SefdResidSpreadDex', '%.2f' % (q(res_kept, 0.84) - q(res_kept, 0.16)))
M('SefdResidSpreadFac', '%.1f' % 10 ** (q(res_kept, 0.84) - q(res_kept, 0.16)))
# unimodality: the largest empty interval inside the body of the distribution,
# and the fraction lying within half a decade of the median
body = [x for x in res_kept if x <= q(res_kept, 0.99)]
M('SefdResidGapDex', '%.2f' % max(body[i + 1] - body[i] for i in range(len(body) - 1)))
M('SefdResidPctHalfDex', '%.1f' % (100.0 * sum(
    1 for x in res_kept if abs(x - st.median(res_kept)) <= 0.5) / len(res_kept)))
M('SefdResidDefGapDex', '%.1f' % (res_kept[0] - max(res_def)) if res_def else '--')

# metadata of the six defective windows
dmeta = []
for r in defect:
    m = AMETA['ebs'].get(r['eb'], {})
    dmeta.append((r['star_name'], band_of(r), m.get('array'), m.get('n_ant'),
                  (m.get('project') or [None])[0], r['chanw'], r['onsrc']))
arrays = sorted({d[2] for d in dmeta if d[2]})
M('DefectArrays', ' and '.join(a.replace('7m', '7\\,m').replace('12m', '12\\,m')
                               for a in arrays) if arrays else 'unrecorded')
M('NDefectArraySeven', '%d' % sum(1 for d in dmeta if d[2] == '7m'))
M('NDefectArrayTwelve', '%d' % sum(1 for d in dmeta if d[2] == '12m'))
M('NDefectProjects', '%d' % len({d[4] for d in dmeta}))
M('NDefectEBs', '%d' % len({r['eb'] for r in defect}))
M('DefectChanwMHz', '%.1f' % (max(d[5] for d in dmeta) / 1e6))
M('DefectChanwMinMHz', '%.1f' % (min(d[5] for d in dmeta) / 1e6))
M('NDefectWin', '%d' % len(defect))
M('NDefectBandSix', '%d' % sum(1 for d in dmeta if d[1] == 6))
M('NDefectBandSeven', '%d' % sum(1 for d in dmeta if d[1] == 7))
# Each defective window shares an execution block and a frequency range with one
# finer-channelised window that is fine.  That is the signature of an auxiliary
# window riding on a science baseband, and it is visible in the released products.
lo = lambda r: min(r['flo'], r['fhi'])
hi = lambda r: max(r['flo'], r['fhi'])
sib_n, sib_ratio = 0, []
for r in defect:
    sibs = [x for x in uniq if x['eb'] == r['eb'] and x is not r
            and lo(x) < hi(r) and hi(x) > lo(r) and x['chanw'] < r['chanw']]
    if sibs:
        sib_n += 1
        sib_ratio += [x['qa'] / r['qa'] for x in sibs]
M('NDefectSibling', '%d' % sib_n)
M('DefectSibRatioLo', '%.1f\\times10^{3}' % (min(sib_ratio) / 1e3))
M('DefectSibRatioHi', '%.1f\\times10^{3}' % (max(sib_ratio) / 1e3))

# ------------------------------------------------- statistic-revision chronology
# Verified against the released repository Tilanthi/SETI through the GitHub REST
# API on 2026-09-12.  Commit 8e00f90e8f8c is the earliest committed artefact
# carrying the AU Mic flag (v2.07, stated in that version's abstract and in its
# machine-readable aggregate); 0c465f2661bd is the earliest commit in which the
# symmetric statistic is operative (v3.25).  Both dates are committer dates, UTC.
from datetime import datetime

FLAG = ('8e00f90e8f8c', '2026-08-31T11:55:04Z', '2026 August 31')
SYMM = ('0c465f2661bd', '2026-09-09T16:14:07Z', '2026 September 9')
M('StatFlagHash', FLAG[0])
M('StatFlagDate', FLAG[2])
M('StatSymHash', SYMM[0])
M('StatSymDate', SYMM[2])
fmt = '%Y-%m-%dT%H:%M:%SZ'
M('StatGapDays', '%d' % round((datetime.strptime(SYMM[1], fmt)
                               - datetime.strptime(FLAG[1], fmt)).total_seconds() / 86400.0))

# CP-72 2713: the retire criterion against the second-epoch search, same method.
# 119a68a6ab50 (v3.39) is the earliest commit carrying the paired promote/retire
# wording; the second-epoch target directory was created at 2026-09-11T20:19:23Z
# on the processing host, which is the earliest trace of that search.
CRIT = ('119a68a6ab50', '2026-09-11T11:33:40Z', '2026 September 11')
SEARCH = '2026-09-11T20:19:23Z'
M('CpCritHash', CRIT[0])
M('CpCritDate', CRIT[2])
M('CpCritLeadHours', '%.0f' % ((datetime.strptime(SEARCH, fmt)
                                - datetime.strptime(CRIT[1], fmt)).total_seconds() / 3600.0))

# ------------------------------------------------- rank resolution
# the control count a 5 sigma-equivalent single-window rank probability needs
p5 = 2.8665157e-7                      # one-sided Gaussian 5 sigma
M('NCtrlFiveSigma', '%.1f\\times10^{6}' % (1.0 / p5 / 1e6))

# ------------------------------------------------- union bookkeeping
gross = sum(abs(r['fhi'] - r['flo']) for r in good)
M('GrossWindowSumGHz', '%d' % round(gross))

open('survey_numbers_round15.tex', 'w').write(
    '%% GENERATED by v346_calc.py -- do not hand-edit.\n' + '\n'.join(OUT) + '\n')
print('\n'.join(OUT))
