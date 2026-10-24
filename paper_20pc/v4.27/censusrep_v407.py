#!/usr/bin/env python3
r"""v4.07: the census name-collision repair, generated.

Every number the paper's disclosure sentence uses is computed here, from the
repaired census, the two extractions' own result files and the released
catalogue -- including the numbers that make the disclosure uncomfortable.

The audit that opened this (referee_r8/CENSUS_DUPLICATES.md) read the defect as
a duplication: one star entered the census twice, so delete a row.  Reading the
extractions themselves says something different and worse:

  * the two census entries are two DIFFERENT stars, V343 Nor A and B, 10.3"
    apart, both inside one ALMA primary beam, and the primary was carrying the
    secondary's name (the ALMA FIELD name) with a Gaia-digit suffix on top;
  * both were extracted, separately, at their own positions, and their
    statistics differ in all four windows;
  * `corrected_export_v399.py` matches the re-extraction harvest on
    (eb, flo, fhi) with NO star, and `acafull_v399.json` carries no target
    field, so ONE star's re-extraction was written onto BOTH rows at v3.99.
    `per_target_results_v3.84.csv`, shipped in this deposit, still carries the
    secondary's own T* = 5.6634 crossing at 345.1449 GHz; the present release
    carries the primary's 4.1526 twice.

So the four rows are kept ONCE, under the star they measure, and the companion
is disclosed as covered, extracted, and not represented in this release.  The
alternative -- rescaling the surviving EIRP to the companion's distance, as the
audit proposed -- would have published the K0V primary's data as an M5Ve
limit.

Writes survey_numbers_round100.tex.  No number below is typed by hand; the
three assertions name the input that would make each of them fail.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUTFILE = os.path.join(HERE, 'survey_numbers_round100.tex')

CEN = os.path.join(HERE, 'ranked_master40pc.csv')
CAT = os.path.join(HERE, 'per_target_results_v3.99.csv')
CAT_PRE = os.path.join(HERE, 'per_target_results_v3.84.csv')   # pre-v3.99
PAIR = os.path.join(HERE, 'r8inputs', 'hd139084_pair_results_v407.json')
AUDIT = os.path.join(HERE, 'censusfix_v407_audit.json')
EXPORT = os.path.join(HERE, 'corrected_export_v399.json')

#: the two components, by Gaia source id -- the only hand-entered fact here,
#: and it is an identity resolved externally (SIMBAD TAP: proper motion and
#: parallax both reproduce to four significant figures).
PRIMARY_SID = '5882581895219921024'      # HD 139084   = V343 Nor A, K0V SB*
COMPANION_SID = '5882581895192805632'    # HD 139084B  = M5Ve
PRIMARY = 'HD 139084'
COMPANION = 'HD 139084B'
C_KMS = 299792.458

OUT = []


def M(name, val):
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


# --------------------------------------------------------------- the census
CENSUS = list(csv.DictReader(open(CEN)))
by_sid = {str(r['gaia_source_id']): r for r in CENSUS}
A, B = by_sid[PRIMARY_SID], by_sid[COMPANION_SID]
assert (A['name'], B['name']) == (PRIMARY, COMPANION), (
    'the census does not carry the repaired names for the two V343 Nor '
    'components: %r and %r' % (A['name'], B['name']))
_dra = ((float(A['ra']) - float(B['ra']))
        * math.cos(math.radians(0.5 * (float(A['dec']) + float(B['dec']))))
        * 3600.0)
SEP = math.hypot(_dra, (float(A['dec']) - float(B['dec'])) * 3600.0)
M('CenPairNameA', PRIMARY)
M('CenPairNameB', COMPANION)
M('CenPairSep', '%.1f' % SEP)
M('CenPairDistA', '%.2f' % float(A['dist_pc']))
M('CenPairDistB', '%.2f' % float(B['dist_pc']))

# the tightest and widest genuine same-star collision groups, measured, so the
# 3" tolerance in the two checks is shown to sit in a real gap
groups = {}
for r in CENSUS:
    groups.setdefault(r['name'].split(' [')[0], []).append(r)
tight = []
for base, v in groups.items():
    if len(v) < 2:
        continue
    s = 0.0
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            d = ((float(v[i]['ra']) - float(v[j]['ra']))
                 * math.cos(math.radians(0.5 * (float(v[i]['dec'])
                                                + float(v[j]['dec'])))) * 3600)
            s = max(s, math.hypot(d, (float(v[i]['dec'])
                                      - float(v[j]['dec'])) * 3600))
    tight.append((s, base))
tight.sort()
assert tight, 'no display-name collision group survives in the census'
import census_dupcheck_v407 as _D
M('CenSepTol', '%.0f' % _D.SEP_TOL_ARCSEC)
M('CenNTightGroups', '%d' % len(tight))
M('CenTightSepMin', '%.2f' % tight[0][0])
M('CenTightSepMax', '%.2f' % tight[-1][0])
assert tight[-1][0] < SEP / 3.0, (
    'the widest surviving same-star collision (%.2f") is no longer far below '
    'the field-name collision (%.2f"), so a separation tolerance can no '
    'longer separate the two cases' % (tight[-1][0], SEP))

# --------------------------------------- the two extractions, side by side
P = json.load(open(PAIR))


def rec(sid, spw):
    # the result files are filed under the target directory, which carries the
    # last six digits of the Gaia id -- the very suffix the disambiguator added
    return P['%s|A002_Xcd8029_Xb6b0_spw%d_result.json' % (sid[-6:], spw)]


spws = sorted({int(k.split('spw')[1][0]) for k in P})
ra = [rec(PRIMARY_SID, s) for s in spws]
rb = [rec(COMPANION_SID, s) for s in spws]
M('CenPairNWin', '%d' % len(spws))
M('CenPairOffA', '%.2f' % ra[0]['primary_beam_offset_arcsec'])
M('CenPairOffB', '%.2f' % rb[0]['primary_beam_offset_arcsec'])
M('CenPairPbFwhmLo', '%.1f' % min(r['primary_beam_fwhm_arcsec']
                                 for r in ra + rb))
M('CenPairPbFwhmHi', '%.1f' % max(r['primary_beam_fwhm_arcsec']
                                  for r in ra + rb))
M('CenPairPbRespLo', '%.2f' % min(r['primary_beam_atten'] for r in ra + rb))
M('CenPairPbRespHi', '%.2f' % max(r['primary_beam_atten'] for r in ra + rb))
# the two extractions must actually differ, or there is nothing to attribute
_same = [s for s, x, y in zip(spws, ra, rb)
         if abs(x['star_peak_snr'] - y['star_peak_snr']) < 1e-6]
assert not _same, (
    'the two positions return identical statistics in window(s) %s, so they '
    'cannot be two extractions and this whole section is wrong' % _same)
M('CenPairTstarAList', ', '.join('%.2f' % r['star_peak_snr'] for r in ra))
M('CenPairTstarBList', ', '.join('%.2f' % r['star_peak_snr'] for r in rb))

# the companion's own crossing
_cr = max(rb, key=lambda r: r['star_peak_snr'])
assert _cr['star_peak_snr'] >= 5.0, (
    'the companion no longer carries a threshold crossing (max T* = %.4f), so '
    'the disclosure sentence must be rewritten' % _cr['star_peak_snr'])
_off = _cr['nearest_known_line_offset_MHz']
M('CenCompTstar', '%.2f' % _cr['star_peak_snr'])
M('CenCompFreq', '%.4f' % _cr['star_peak_freq_GHz'])
M('CenCompLine', _cr['nearest_known_line'].replace('(', '($').replace(')', '$)')
  .replace('-', '$-$').replace('($', '(').replace('$)', ')')
  if False else _cr['nearest_known_line'].replace('-', '--'))
M('CenCompLineOffKms', '%.1f' % abs(_off * 1e-3 / _cr['star_peak_freq_GHz']
                                    * C_KMS))
M('CenCompCtrlMax', '%.1f' % _cr['control_peak_snr'])
M('CenCompNGe', '%d' % _cr['n_control_ge_star'])
M('CenCompPRank', '%.3f' % ((1 + _cr['n_control_ge_star'])
                            / (_cr['n_control'] + 1)))
M('CenCompEirp', '%.2f\\times10^{15}' % (_cr['EIRP_min_W'] / 1e15))
# and it must be rank-screened: if the star beat its own control ring this
# would be a candidate, not a disclosure
assert _cr['star_peak_snr'] < _cr['control_peak_snr'], (
    'the companion crossing (%.3f) exceeds its own control-ring maximum '
    '(%.3f); it would be a stage-1 event and cannot be deferred'
    % (_cr['star_peak_snr'], _cr['control_peak_snr']))

# ------------------------------------- what the release does and does not hold
CATR = list(csv.DictReader(open(CAT)))
PRER = list(csv.DictReader(open(CAT_PRE)))
_now = [r for r in CATR if r['star_name'] in (PRIMARY, COMPANION)]
M('CenNWinRelease', '%d' % len(_now))
assert {r['star_name'] for r in _now} == {PRIMARY}, (
    'the release now carries rows for %s; the disclosure below says it does '
    'not' % sorted({r['star_name'] for r in _now}))
# the crossing WAS counted in a catalogue shipped in this deposit
_was = [r for r in PRER if r['star_name'].startswith('HD 139084B 805632')
        and r.get('crossing') == 'True']
assert len(_was) == 1, (
    'per_target_results_v3.84.csv no longer carries exactly one counted '
    'crossing for the companion (%d found); the provenance sentence rests on '
    'it' % len(_was))
M('CenLostVersion', '3.99')
M('CenLostCatalogue', r'\texttt{per\_target\_results\_v3.84.csv}')
M('CenLostTstar', '%.2f' % float(_was[0]['star_snr']))

# how many physical windows of the survey hold more than one catalogued star,
# and how many of those the re-extraction touched
EXP = json.load(open(EXPORT))
FROZ = json.load(open(os.path.join(HERE, 'frozen_export_v3.81_survey.json')))
win = {}
for r in FROZ['rows']:
    lo, hi = sorted((float(r['flo']), float(r['fhi'])))
    win.setdefault((r['eb'], round(lo, 3), round(hi, 3)), set()).add(
        r['star_name'])
M('CenNMultiStarWin', '%d' % sum(1 for v in win.values() if len(v) > 1))
_winnow = {}
for r in EXP['rows']:
    lo, hi = sorted((float(r['flo']), float(r['fhi'])))
    _winnow.setdefault((r['eb'], round(lo, 3), round(hi, 3)), set()).add(
        r['star_name'])
M('CenNMultiStarWinNow', '%d' % sum(1 for v in _winnow.values() if len(v) > 1))
_cor = EXP.get('corrected', {})
M('CenNOverwriteWin', '%d' % _cor.get('n_multistar_windows', 0))
M('CenNOverwriteRows', '%d' % _cor.get('n_multistar_rows', 0))

AUD = json.load(open(AUDIT))
M('CenNRenamed', '%d' % AUD['renamed'])
M('CenNDropped', '%d' % AUD['dropped'])
M('CenKRatio', '%.6f' % (AUD['k_export_median'] / AUD['k_first_principles']))
# the EIRP the surviving rows carry belongs to the star they are now labelled
# with, and the audit's proposed rescaling would have been in the wrong
# direction by exactly this factor
M('CenMisscale', '%.4f' % ((float(B['dist_pc']) / float(A['dist_pc'])) ** 2))

with open(OUTFILE, 'w') as fh:
    fh.write('%% GENERATED by censusrep_v407.py -- do not hand-edit.\n')
    fh.write('\n'.join(OUT) + '\n')
print('census repair: %s/%s separated %.2f", %d renamed, %d dropped, '
      'companion T* = %.2f vs its own control ring %.2f'
      % (PRIMARY, COMPANION, SEP, AUD['renamed'], AUD['dropped'],
         _cr['star_peak_snr'], _cr['control_peak_snr']))
print('macros -> %s (%d)' % (os.path.basename(OUTFILE), len(OUT)))
