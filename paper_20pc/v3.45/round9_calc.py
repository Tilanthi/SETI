#!/usr/bin/env python3
r"""Round-9 macro computation (v3.39).

Sources: frozen_export_v3.31.json (the rounds 5-8 freeze).  Rules
honoured: numbers only via generated macros; macro names letter-only;
scipy.stats.kstest only for KS (not used this round).

Referee items served:
  R4-B(sec3)      window concentration in the three most-observed systems
  R3-8            mask-exclusion framing on the unique-frequency union;
                  values derived from the generated Table tab:maskband
                  (all-species merged Union 4.96 GHz of the \UnionGHz
                  = 93.1 GHz union -- the in-paper generated authority;
                  the previously typed 87.0/5.7 per cent prose figures
                  were inconsistent with that table and are retired)
  R3-3            CP-72 2713 feature-table rows recomputed from the
                  frozen row (T*, ring max, frequency, margin, nearest
                  masked-transition offset, drift-grid shape)
"""
import json, math, statistics as st, collections

d = json.load(open('frozen_export_v3.31.json'))
rows = d['rows']

def band_of(r):
    if r['band'] is not None: return r['band']
    f = 0.5 * (r['flo'] + r['fhi'])
    for lo, hi, b in [(84, 116, 3), (125, 163, 4), (163, 211, 5),
                      (211, 275, 6), (275, 373, 7), (385, 500, 8)]:
        if lo <= f < hi: return b
C = 299792.458
for r in rows:
    r['band_x'] = band_of(r)
    r['res_x'] = 'fine' if r['chanw'] < 5e6 else 'coarse'
    r['qa'] = r['rms'] * math.sqrt(r['onsrc'] * r['chanw'])
    r['cmax'] = max(r['ctrl_all']) if r['ctrl_all'] else r['ctrl_max']
    r['vel_off'] = (r['line_off'] * 1e-3 / (0.5 * (r['flo'] + r['fhi'])) * C
                    if r.get('line_off') is not None else None)
key = lambda r: (r['star_name'], r['eb'], round(min(r['flo'], r['fhi']), 6),
                 round(max(r['flo'], r['fhi']), 6), r['chanw'])
best = {}
for r in rows:
    k = key(r)
    if k not in best or (best[k]['line'] is None and r['line'] is not None):
        best[k] = r
uniq = list(best.values())
qa_med = st.median(r['qa'] for r in uniq)
kept = [r for r in uniq if r['qa'] >= qa_med / 100.0]
withheld = [r for r in kept if r['star_name'] == 'eps Eri' and r['band_x'] == 6]
good = [r for r in kept if r not in withheld]
assert len(good) == 431

macros = []
def M(name, val):
    macros.append('\\newcommand{\\%s}{%s}' % (name, val))

# ---- R4-B: window concentration in the most-observed systems --------------
cnt = collections.Counter(r['star_name'] for r in good)
conc = {n: cnt[n] for n in ('bet Pic', 'AU Mic', 'TRAPPIST-1')}
M('ConcBpicWin', '%d' % conc['bet Pic'])
M('ConcAumicWin', '%d' % conc['AU Mic'])
M('ConcTrapWin', '%d' % conc['TRAPPIST-1'])
M('ConcThreeWin', '%d' % sum(conc.values()))
M('ConcThreePct', '%.1f' % (100.0 * sum(conc.values()) / len(good)))
M('ConcThreeSys', '%d' % len({r['system'] if 'system' in r else r['star_name']
                              for r in good
                              if r['star_name'] in conc}))

# ---- R3-8: mask-exclusion framing on the unique-frequency union -----------
# Source: generated Table tab:maskband, all-species (merged) Union column
# = 4.96 GHz, against the \UnionGHz (93.1 GHz) unique union recomputed
# here from the same frozen rows.
iv = sorted((min(r['flo'], r['fhi']), max(r['flo'], r['fhi']))
            for r in good)
merged = []
for lo, hi in iv:
    if merged and lo <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], hi)
    else:
        merged.append([lo, hi])
union = sum(b - a for a, b in merged)
MASK_UNION_LOST = 4.96            # tab:maskband, all-species merged Union
MASK_GROSS_LOST = 22.20           # tab:maskband, all-species merged Total
# Gross searched bandwidth is NOT a literal: derive it from the same frozen
# rows as everything else (the typed 700.8 was stale by 15.9 GHz, v3.41).
GROSS_BW = sum(abs(r['fhi'] - r['flo']) for r in good)
M('SearchedUnionGHz', '%.1f' % (union - MASK_UNION_LOST))
M('MaskUnionLostGHz', '%.2f' % MASK_UNION_LOST)
M('MaskUnionPct', '%.1f' % (100.0 * MASK_UNION_LOST / union))
M('MaskGrossLostGHz', '%.2f' % MASK_GROSS_LOST)
M('MaskGrossPct', '%.1f' % (100.0 * MASK_GROSS_LOST / GROSS_BW))
assert abs(union - 93.1) < 0.05, union   # consistency with \UnionGHz
# v3.45: \EffBandGHz (87, round-1 generator) duplicated \SearchedUnionGHz
# with a stale value.  Retired; \SearchedUnionGHz above is the single source.

# ---- R3-3: CP-72 2713 Band 7 feature rows ---------------------------------
cp = [r for r in good if r['star_name'] == 'CP-72 2713' and r['band_x'] == 7
      and r['star_snr'] and r['star_snr'] >= 5 and r['star_snr'] > r['cmax']]
assert len(cp) == 1
cp = cp[0]
M('CpTwoFreqGHz', '%.4f' % (0.5 * (cp['flo'] + cp['fhi'])))
M('CpTwoTstar', '%.2f' % cp['star_snr'])
M('CpTwoRingMax', '%.2f' % cp['cmax'])
M('CpTwoMargin', '%.2f' % (cp['star_snr'] - cp['cmax']))
M('CpTwoLineOffKms', '%d' % round(cp['vel_off']))
M('CpTwoNdrift', '%d' % cp['ndrift'])
M('CpTwoDriftkHzs', '%.2f' % (cp['drift_max'] / 1e3))
M('CpTwoBwGHz', '%.2f' % (abs(cp['fhi'] - cp['flo'])))
M('CpTwoOnsrcS', '%d' % round(cp['onsrc']))
assert abs(cp['star_snr'] - 5.81) < 0.005 and abs(cp['rms'] - 2.097) < 0.001

with open('survey_numbers_round9.tex', 'w') as f:
    f.write('% survey_numbers_round9.tex -- generated by round9_calc.py\n'
            '% from frozen_export_v3.31.json; mask-union framing derived\n'
            '% from the generated Table tab:maskband (4.96 GHz all-species\n'
            '% merged Union); referee round 9 (R4-B concentration, R3-8\n'
            '% mask framing, R3-3 CP-72 2713 feature rows).\n\n')
    f.write('\n'.join(macros) + '\n')

print('\n'.join(macros))
