#!/usr/bin/env python3
"""Round-8 macro computation (v3.38).

Sources: frozen_export_v3.31.json (the rounds 5-7 freeze),
occurrence_v328.json (the f95 demonstration inputs) and
dwell_campaign_trials_v3.32.csv (the retained dwell-campaign trial log).
Rules honoured: numbers only via generated macros; macro names letter-only;
scipy.stats.kstest only for KS (not used this round).

Referee items served:
  R1-1/spec-3-4  class widths + eta_drift on the FROZEN 118/313 classes
                 (round 7 computed them on the export's res-string
                 classes, 117/322 -- a latent inconsistency of the same
                 family the referee caught)
  R1-9           102-vs-103 execution-block reconciliation
  R2-A6          f95 sensitivity to EB intraclass correlation (design effect)
  spec-20        robust standardised excess zeta for the four flags
  spec-27        independent re-derivation of the dwell-campaign criterion
  spec-30        localisation of the six-window noise defect
"""
import json, csv, math, statistics as st, collections

d = json.load(open('frozen_export_v3.31.json'))
rows = d['rows']

# --- replicate the frozen selection (survey_stats.py, identical logic) ----
def band_of(r):
    if r['band'] is not None: return r['band']
    f = 0.5 * (r['flo'] + r['fhi'])
    for lo, hi, b in [(84, 116, 3), (125, 163, 4), (163, 211, 5),
                      (211, 275, 6), (275, 373, 7), (385, 500, 8)]:
        if lo <= f < hi: return b
for r in rows:
    r['band_x'] = band_of(r)
    r['res_x'] = 'fine' if r['chanw'] < 5e6 else 'coarse'
    r['qa'] = r['rms'] * math.sqrt(r['onsrc'] * r['chanw'])
    r['cmax'] = max(r['ctrl_all']) if r['ctrl_all'] else r['ctrl_max']
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
withheld = [r for r in kept if r['star_name'] == 'eps Eri' and r['band_x'] == 6]
good = [r for r in kept if r not in withheld]
fine = [r for r in good if r['res_x'] == 'fine']
coarse = [r for r in good if r['res_x'] == 'coarse']
assert len(fine) == 118 and len(coarse) == 313 and len(good) == 431

def eta(r):
    return abs(r['drift_max']) * r['onsrc'] / r['chanw']

macros = []
def M(name, val):
    macros.append('\\newcommand{\\%s}{%s}' % (name, val))

# ---- R1-1 / spec-4: class channelisation + eta on the frozen classes ----
fw = sorted(r['chanw'] for r in fine)
cw = sorted(r['chanw'] for r in coarse)
fw_mode = collections.Counter(round(w / 1e3, 3) for w in fw).most_common(1)[0]
cw_mode = collections.Counter(round(w / 1e6, 4) for w in cw).most_common(1)[0]
M('ChanAMinKHz', '%.3f' % (fw[0] / 1e3))
M('ChanAMaxKHz', '%.3f' % (fw[-1] / 1e3))
M('ChanAMedKHz', '%.1f' % (st.median(fw) / 1e3))
M('ChanAModeKHz', '%.1f' % fw_mode[0])
M('ChanAModePct', '%d' % round(100.0 * fw_mode[1] / len(fw)))
M('ChanBMinMHz', '%.3f' % (cw[0] / 1e6))
M('ChanBMaxMHz', '%.2f' % (cw[-1] / 1e6))
M('ChanBMedMHz', '%.3f' % (st.median(cw) / 1e6))
M('ChanBModeMHz', '%.3f' % cw_mode[0])
M('ChanBModeN', '%d' % cw_mode[1])
M('ChanGapFac', '%.1f' % (cw[0] / fw[-1]))
strad = [r for r in fine if r['chanw'] >= 1e6]
assert len(strad) == 1
strad = strad[0]
M('ChanStraddleKHz', '%.3f' % (strad['chanw'] / 1e3))
M('EtaStraddle', '%.2f' % eta(strad))

ef = sorted(eta(r) for r in fine)
ec = sorted(eta(r) for r in coarse)
M('EtaAmin', '%.2f' % ef[0])
M('EtaAmed', '%.1f' % st.median(ef))
M('EtaAmax', '%d' % round(ef[-1]))
M('EtaAltOne', '%d' % sum(1 for x in ef if x < 1))
M('EtaBmin', '%.3f' % ec[0])
M('EtaBmed', '%.2f' % st.median(ec))
M('EtaBmax', '%.2f' % ec[-1])
M('EtaBgeOne', '%d' % sum(1 for x in ec if x >= 1))
M('EtaBgeOneMax', '%.2f' % max(x for x in ec if x >= 1))

def worst_half(cls):
    out = []
    for r in cls:
        nd, dm, T, cw_ = r['ndrift'], r['drift_max'], r['onsrc'], r['chanw']
        if nd is None or nd < 2 or dm is None or T is None:
            continue
        out.append((2 * abs(dm) / (nd - 1) / 2) * T / cw_)
    return max(out)
M('DgridA', '%.2f' % (math.ceil(worst_half(fine) * 100) / 100))
M('DgridB', '%.2f' % (math.ceil(worst_half(coarse) * 100) / 100))

# ---- spec-5: searched windows by ALMA band (main-paper Table row) ---------
NAME = {3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight'}
bw = collections.Counter(r['band_x'] for r in good)
for b in sorted(bw):
    M('BandWin' + NAME[b], '%d' % bw[b])

# ---- R1-9: 102 vs 103 execution blocks ----------------------------------
ebs_good = {r['eb'] for r in good}
def rk(r):
    return bool(r.get('ctrl_all')) and r['src_snr'] is not None
ebs_rank = {r['eb'] for r in uniq if r['eb'] and rk(r)}
extra = ebs_rank - ebs_good
assert len(extra) == 1
uid = extra.pop()
M('EbsRetained', '%d' % len(ebs_good))
M('EbsRankAll', '%d' % len(ebs_rank))
M('EbsExtraUid', uid.replace('_', r'\_'))

# ---- R2-A6: f95 sensitivity to EB intraclass correlation -----------------
ICC_RANK = 0.24                       # round-7 macro \IccRank
ebcnt = collections.Counter(r['eb'] for r in fine)
kbar = len(fine) / len(ebcnt)
deff = 1 + (kbar - 1) * ICC_RANK
# v3.44: single-sourced on the live engine (was occurrence_v328.json, frozen
# at the pre-repair N_sys = 82 denominators)
occ = json.load(open('survey_stats_round10.json'))['occurrence']
f95 = occ['1e+16']['measured']
sumc = -math.log(0.05) / -math.log(1 - f95)      # effective no. of trials
f95i = 1 - 0.05 ** (deff / sumc)
M('EffEbsFine', '%d' % len(ebcnt))
M('EffKbar', '%.2f' % kbar)
M('EffDeff', '%.2f' % deff)
M('EffSumC', '%.1f' % sumc)
M('EffFIccPct', '%.1f' % (100 * f95i))

# ---- spec-20: robust standardised excess for the four flags --------------
def rzeta(r):
    ca = r['ctrl_all']
    med = st.median(ca)
    mad = st.median(abs(x - med) for x in ca)
    return (r['star_snr'] - med) / (1.4826 * mad)
FLAGS = {'HD 48370': 'Hd', 'bet Pic': 'BpicThree', 'CP-72 2713': 'Cp'}
# second bet Pic window (Band 6) gets its own tag
flags = [r for r in good if r['star_snr'] and r['star_snr'] >= 5
         and r['star_snr'] > r['cmax']]
assert len(flags) == 4, [(r['star_name'], r['band_x']) for r in flags]
for r in flags:
    if r['star_name'] == 'bet Pic':
        tag = 'BpicThree' if r['band_x'] == 3 else 'BpicSix'
    elif r['star_name'] == 'HD 48370':
        tag = 'Hd'
    else:
        tag = 'Cp'
    M('Zeta' + tag, '%.1f' % rzeta(r))
    M('Margin' + tag, '%+.2f' % (r['star_snr'] - r['cmax']))

# ---- spec-30: localise the six-window noise defect ------------------------
sib_fac = []
for r in defect:
    sib = [q['rms'] for q in kept if q['eb'] == r['eb']
           and q['chanw'] == r['chanw'] and q is not r]
    sib_fac.append(min(sib) / r['rms'] if sib else float('inf'))
M('DefectOnsrcLo', '%d' % min(r['onsrc'] for r in defect))
M('DefectOnsrcHi', '%d' % max(r['onsrc'] for r in defect))
M('DefectRmsLoSci', r'%.1f\times10^{-4}' % (1e4 * min(r['rms'] for r in defect)))
M('DefectRmsHiSci', r'%.1f\times10^{-4}' % (1e4 * max(r['rms'] for r in defect)))
M('DefectSibFacLo', '%d' % min(sib_fac))
M('DefectSibFacHi', '%d' % max(sib_fac))
M('DefectBandSix', '%d' % sum(1 for r in defect if r['band_x'] == 6))
M('DefectBandSeven', '%d' % sum(1 for r in defect if r['band_x'] == 7))
M('DefectNStars', '%d' % len({r['star_name'] for r in defect}))

# ---- spec-27: independent re-derivation of the dwell-campaign criterion ---
tr = list(csv.DictReader(open('dwell_campaign_trials_v3.32.csv')))
agree = mism = 0
tmin, fmax = 1e9, -1e9
for r in tr:
    snr = float(r['recovered_snr'])
    det = r['detected'] == 'True'
    if det: tmin = min(tmin, snr)
    else:   fmax = max(fmax, snr)
    if (snr >= 5.0) == det: agree += 1
    else: mism += 1
M('XcheckN', '%d' % len(tr))
M('XcheckAgree', '%d' % agree)
M('XcheckMismatch', '%d' % mism)
M('XcheckTrueMin', '%.2f' % tmin)
M('XcheckFalseMax', '%.2f' % fmax)
M('XcheckWin', '%d' % len({(r['target'], r['window']) for r in tr}))

with open('survey_numbers_round8.tex', 'w') as f:
    f.write('% survey_numbers_round8.tex -- generated by round8_calc.py\n'
            '% from frozen_export_v3.31.json + occurrence_v328.json +\n'
            '% dwell_campaign_trials_v3.32.csv (v3.31/v3.32 freezes).\n'
            '% class widths / eta on frozen classes, EB reconciliation, f95\n'
            '% ICC sensitivity, flag effect sizes, defect localisation,\n'
            '% dwell-campaign criterion cross-check; referee round 8.\n\n')
    f.write('\n'.join(macros) + '\n')

print('\n'.join(macros))
print('# frozen classes: A %d, B %d; defect stars %d'
      % (len(fine), len(coarse), len({r['star_name'] for r in defect})))
