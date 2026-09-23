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
_K = json.load(open('catalogue_constants.json'))  # v3.80: the catalogue's size is written once by survey_stats.py, never retyped



d = json.load(open('frozen_export_v3.81_survey.json'))   # v3.80: was v3.31
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
assert len(good) == _K['n_windows'], len(good)

macros = []
def M(name, val):
    macros.append('\\newcommand{\\%s}{%s}' % (name, val))

# ---- R4-B: window concentration in the most-observed systems --------------
# v3.85: these were bet Pic, AU Mic and TRAPPIST-1, hard-coded because
# they were the three most observed systems at v3.31. They are not now, and
# the manuscript's sentence claims the top three, so take the top three.
cnt = collections.Counter(r['star_name'] for r in good)
_top = cnt.most_common(3)
conc = dict(_top)
_nm = {'bet Pic': r'$\beta$~Pic', 'tau Cet': r'$\tau$~Cet',
       'BD05  1668': 'BD$+$05~1668', 'HD  33793': 'HD~33793'}
_clean = lambda n: _nm.get(n, ' '.join(n.split('  Gaia')[0].split()))
M('ConcThreeNames',
  ', '.join(_clean(n) for n, _ in _top[:-1]) + ' and ' + _clean(_top[-1][0]))
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
# v3.61: \SearchedUnionGHz, \MaskUnionPct, \MaskUnionLostGHz,
# \MaskGrossLostGHz and \MaskGrossPct MOVED to v361_calc.py, which computes
# them band by band from the RELEASED catalogue (tab:maskband).  They were
# hand-entered literals here (4.96 and 22.20 GHz) measured on the 93.1-GHz
# union of the pre-Band 9/10 catalogue, so after the v3.60 rebuild the paper
# was quoting "113.9 GHz, of which 88.2 survives masking" -- a loss of 22 per
# cent that no calculation in the release supported.  A literal with a
# provenance comment is still a literal.
# v3.80: this generator now reads the same export as everything else, so
# the union is the paper's own union, not a three-catalogue-old freeze.
# 93.1 -> 125.08 GHz. Assert against the single source rather than a
# literal, which is what let the 93.1 survive two catalogue changes.
_UNION = json.load(open('survey_stats.json'))['union_GHz']
assert abs(union - _UNION) < 0.05, (union, _UNION)
# v3.46: \EffBandGHz (87, round-1 generator) duplicated \SearchedUnionGHz
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
