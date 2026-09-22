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
_K = json.load(open('catalogue_constants.json'))  # v3.80: the catalogue's size is written once by survey_stats.py, never retyped



# v3.80: was frozen_export_v3.31.json, a 431-window snapshot three
# catalogues out of date.  Its numbers (per-band counts, eta_drift,
# the stage-1 flag list) were being printed beside a headline computed
# from the current export.  Repointed.
d = json.load(open('frozen_export_v3.81_survey.json'))
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
assert (len(fine), len(coarse), len(good)) == \
       (_K['n_fine'], _K['n_coarse'], _K['n_windows']), \
       (len(fine), len(coarse), len(good))

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
# v3.80: Bands 9 and 10 reached this generator for the first time when it
# was repointed off the v3.31 snapshot, and the map had no names for them.
NAME = {3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight',
        9: 'Nine', 10: 'Ten'}
bw = collections.Counter(r['band_x'] for r in good)
for b in sorted(bw):
    M('BandWin' + NAME[b], '%d' % bw[b])

# ---- R1-9: 102 vs 103 execution blocks ----------------------------------
ebs_good = {r['eb'] for r in good}
def rk(r):
    return bool(r.get('ctrl_all')) and r['src_snr'] is not None
ebs_rank = {r['eb'] for r in uniq if r['eb'] and rk(r)}
extra = sorted(ebs_rank - ebs_good)
# v3.80: exactly one execution block used to be rankable but not retained, so
# the generator named it in a macro.  With 479 blocks there are several, and
# naming one of them would be arbitrary; report the count, and keep the
# single-uid macro only while it is still single, so the text that quotes it
# cannot silently become wrong.
M('EbsRetained', '%d' % len(ebs_good))
M('EbsRankAll', '%d' % len(ebs_rank))
M('EbsExtraN', '%d' % len(extra))
if len(extra) == 1:
    M('EbsExtraUid', extra[0].replace('_', r'\_'))

# ---- R2-A6: f95 sensitivity to EB intraclass correlation -----------------
ICC_RANK = 0.24                       # round-7 macro \IccRank
ebcnt = collections.Counter(r['eb'] for r in fine)
kbar = len(fine) / len(ebcnt)
deff = 1 + (kbar - 1) * ICC_RANK
# v3.46: single-sourced on the live engine (was occurrence_v328.json, frozen
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
assert len(flags) == _K['n_flagged'], \
       [(r['star_name'], r['band_x']) for r in flags]
# v3.80: four stage-1 outliers became thirteen when the catalogue grew from
# 443 to 1956 windows.  Eight of the thirteen are beta Pic, in five Band 3 and
# three Band 6 windows, every one of them within a few km/s of the systemic
# velocity on a CO transition -- one astrophysical source seen repeatedly, not
# eight independent events.  The per-flag macros are keyed on the deepest
# window of each named star so the text keeps quoting a single, defined row.
NAMED = {('bet Pic', 3): 'BpicThree', ('bet Pic', 6): 'BpicSix',
         ('HD 48370', 6): 'Hd', ('CP-72 2713', 7): 'Cp'}
deepest = {}
for r in flags:
    k = (r['star_name'], r['band_x'])
    if k in NAMED and (k not in deepest or r['star_snr'] > deepest[k]['star_snr']):
        deepest[k] = r
for k, tag in NAMED.items():
    r = deepest.get(k)
    if r is None:
        continue
    M('Zeta' + tag, '%.1f' % rzeta(r))
    M('Margin' + tag, '%+.2f' % (r['star_snr'] - r['cmax']))
M('NFlagWin', '%d' % len(flags))
M('NFlagSys', '%d' % len({r['star_name'] for r in flags}))
M('NFlagBpic', '%d' % sum(1 for r in flags if r['star_name'] == 'bet Pic'))
M('NFlagOther', '%d' % sum(1 for r in flags if r['star_name'] != 'bet Pic'))

# ---- spec-30: localise the six-window noise defect ------------------------
sib_fac = []
n_nosib = 0
for r in defect:
    sib = [q['rms'] for q in kept if q['eb'] == r['eb']
           and q['chanw'] == r['chanw'] and q is not r]
    # v3.80: with the full sweep, some defective windows are the only window
    # of their channelisation in their block, so there is no sibling to
    # compare against and the ratio is undefined.  Count them separately
    # rather than letting an infinity reach a %d format, which is what the
    # old code did the moment such a window appeared.
    if sib:
        sib_fac.append(min(sib) / r['rms'])
    else:
        n_nosib += 1
M('DefectNoSib', '%d' % n_nosib)
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
