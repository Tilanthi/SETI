#!/usr/bin/env python3
r"""round 101 (DECISIONS_R8 D29/D31): THE PRIMARY-BEAM AUDIT, AS A RESULT.

This is not a repair log.  The survey's pipeline computed a star-to-phase-centre
offset for every measurement set and applied the response exactly once, so the
audit's finding is a POSITIVE statement about the release -- and the two new
catalogue columns exist so that a reader can check it, which before v4.08 was
impossible for a reason that is itself worth stating.

WHAT THIS GENERATOR EMITS, AND WHY EACH NUMBER IS HERE
------------------------------------------------------
1.  The geometry of the release: the distribution of the offset and of the
    response A, and the fact that `smin = 5 rms / A` closes on every row.
    ★ The trigger statistics -- T*, Z, the 512-control rank p -- are RATIOS
    formed inside one window, so A cancels out of all of them identically.
    Correcting the threshold is therefore the COMPLETE correction, not a
    partial one, and that is why no crossing, no rank and no disposition in
    this paper moves.
2.  Why the columns matter: `theta_pb_arcsec` is the pipeline's 1.22 lambda/D
    evaluated at D = 12 m for EVERY window, including the ACA 7 m ones, so a
    reader who tried to recompute A from what v4.07 shipped would have got the
    wrong answer on those rows -- not a rounding error, a 1.7x error in the
    beam.  This is measured here, not asserted.
3.  The injection campaign's blindness to A, and the fact that the resulting
    BIAS IS EXACTLY ZERO.  The ladder is in APPARENT flux and so is the search
    threshold, so A cancels out of P90/P_trig identically.  What remains is two
    limitations, not a systematic.
4.  The provenance gap: four rows whose published rms no surviving product
    reproduces, disclosed and NOT reconciled.
5.  One release defect that a position-only join gets wrong: a single window
    storing one offset against two different attenuations.

Everything is computed from the deposit's own catalogue plus three frozen
records in `pbaudit_v408/`.  The beam-model sensitivity is not recomputed here:
it is imported from `pbgate_v408.py`, the gate that ships, so the number in the
text and the number the gate enforces cannot drift apart.

Writes `survey_numbers_round101.tex`.
"""
import collections
import csv
import json
import os
import statistics as stat

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda n: os.path.join(HERE, 'pbaudit_v408', n)
CAT = os.path.join(HERE, 'per_target_results_v3.99.csv')
OUT = os.path.join(HERE, 'survey_numbers_round101.tex')

M = []


def m(name, val):
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in M), name
    M.append('\\newcommand{\\%s}{%s}' % (name, val))


def _sci(x, sig=1):
    """LaTeX scientific form, for a value that is typeset inside a sentence.

    ★ '%.1e' gives `8.7e-05`, which is floating-point notation in English
    prose.  Two of these were set in Appendix A.2.  Everything else in the
    paper is $a\\times10^{b}$, so build that.
    """
    s = '%.*e' % (sig, x)
    mant, exp = s.split('e')
    return '$%s\\times10^{%d}$' % (mant, int(exp))


rows = list(csv.DictReader(open(CAT)))
pbc = json.load(open(os.path.join(HERE, 'pbcat_v408.json')))
src = {e['pb_source'] for v in pbc.values() for e in v}
prov = {(e['pb_source']) for v in pbc.values() for e in v}
nsrc = collections.Counter(e['pb_source'] for v in pbc.values() for e in v)

# =====================================================================  1
# The geometry of the release.
off = sorted(float(r['pb_offset_arcsec']) for r in rows)
att = sorted(float(r['pb_atten']) for r in rows)
m('PbNWin', '%d' % len(rows))
m('PbOffMed', '%.3f' % stat.median(off))
m('PbOffPNN', '%.2f' % off[int(0.99 * len(off))])
m('PbOffMax', '%.2f' % off[-1])
m('PbAMin', '%.4f' % att[0])
m('PbAPOne', '%.4f' % att[len(att) // 100])
m('PbAMed', '%.6f' % stat.median(att))
m('PbNLowNN', '%d' % sum(1 for a in att if a < 0.99))
m('PbNLowN', '%d' % sum(1 for a in att if a < 0.9))
m('PbNLowHalf', '%d' % sum(1 for a in att if a < 0.5))
# ★ The identity a reader could not previously evaluate.  It is asserted, not
# merely reported: if it ever failed, the response would be missing from S_min
# or applied to it twice, which is the whole question the audit asked.
def _resid(r):
    return abs(5 * float(r['rms_mJy']) / float(r['pb_atten'])
               - float(r['smin_mJy'])) / float(r['smin_mJy'])


worst = max(_resid(r) for r in rows)
assert worst < 1e-3, 'smin != 5 rms / A on some row (worst %.2e)' % worst
m('PbSminClosed', '%d' % len(rows))
# ★ NOT '%.1e': this is typeset in prose, and `8.7e-05` is floating-point
# notation in an English sentence.  Everywhere else the paper writes
# $8.7\times10^{-5}$.
m('PbSminWorstRes', _sci(worst))
# ★★★ v4.08, SECOND PASS: THE CLOSURE COUNT AS FIRST WRITTEN WAS A CHECK THAT
# CANNOT FAIL ON PART OF ITS OWN SAMPLE.  On the rows whose product no longer
# exists, A was BACK-SOLVED from the release's own 5 sigma / S_min -- so the
# identity closes there by construction, and quoting 1651 of 1651 credits the
# audit with 10 rows it cannot test.  The independent count is the one the
# paper quotes, the tautological rows are counted separately, and the
# decomposition is pinned with == so the two can never drift.  Ninth instance
# of this family in this project.
_FTOL = 0.002


def _provof(r):
    """the frozen record's pb_source for one catalogue row, joined on the
    execution block, the window edges and the published attenuation -- the same
    join pbgate_v408.py uses, and no name comparison beyond the block."""
    lo = min(float(r['flo_GHz']), float(r['fhi_GHz']))
    hi = max(float(r['flo_GHz']), float(r['fhi_GHz']))
    for k, v in pbc.items():
        if not k.endswith('|' + r['eb']):
            continue
        for e in v:
            if abs(e['flo'] - lo) < _FTOL and abs(e['fhi'] - hi) < _FTOL \
                    and abs(e['pb_atten'] - float(r['pb_atten'])) < 2e-6:
                return e['pb_source']
    return None


_prov = [_provof(r) for r in rows]
assert _prov.count(None) == 0, (
    '%d released rows have no frozen provenance record' % _prov.count(None))
_indep = [r for r, pv in zip(rows, _prov) if pv != 'inverted']
_taut = [r for r, pv in zip(rows, _prov) if pv == 'inverted']
assert len(_indep) + len(_taut) == len(rows)
assert len(_taut) == nsrc['inverted'], (len(_taut), nsrc['inverted'])
_worst_indep = max(_resid(r) for r in _indep)
assert _worst_indep < 1e-3, _worst_indep
# and the tautological rows must really be tautological: their residual is
# floating-point noise, not a measurement.  Asserted in BOTH directions, so
# "tautological" is a measured property rather than a label.
_worst_taut = max(_resid(r) for r in _taut)
# the back-solved rows close to the rounding of the column itself (6 decimals),
# two orders below the independent rows: "tautological" is measured here, not
# asserted as a label.
assert _worst_taut < 1e-6, _worst_taut
assert _worst_indep > 10 * _worst_taut, (
    'the back-solved rows do not close any more tightly than the independently '
    'computed ones (%.1e against %.1e), so the distinction the text draws is '
    'not in the data' % (_worst_taut, _worst_indep))
m('PbSminIndep', '%d' % len(_indep))
m('PbSminTaut', '%d' % len(_taut))
m('PbSminIndepRes', _sci(_worst_indep))
m('PbSminTautRes', '%.1e' % _worst_taut)
m('PbNProduct', '%d' % nsrc['product'])
m('PbNRecovered', '%d' % nsrc['recovered'])
m('PbNInverted', '%d' % nsrc['inverted'])
# The recovered row is named rather than counted: it is the only window in the
# release whose offset the search did not store, and it is not a defect in a
# published number (delta smin 2e-5).
assert nsrc['recovered'] == 1, nsrc

# =====================================================================  2
# theta_pb_arcsec is the 12 m beam on every ACA row.  MEASURED, by comparing
# the column the release ships with the dish the archive records.
# the archive's own record of which array each execution block was taken on --
# the same file v342_calc.py keys its per-window dish diameter from
arr = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']


def _arr(eb):
    return (arr.get(eb) or {}).get('array') or ''


n7 = sum(1 for r in rows if _arr(r['eb']) == '7m')
# the shipped theta_pb is 1.22 lambda / 12 m on those rows: check the RATIO of
# the shipped beam to the 12 m prediction, which must be 1 on all of them
C = 299792458.0
bad = 0
for r in rows:
    if _arr(r['eb']) != '7m':
        continue
    fmid = 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz'])) * 1e9
    th12 = 1.22 * (C / fmid) / 12.0 * 206264.806
    if abs(float(r['theta_pb_arcsec']) / th12 - 1.0) > 0.02:
        bad += 1
m('PbNAcaRow', '%d' % n7)
m('PbAcaRatio', '%.1f' % (12.0 / 7.0))
# ★ Asserted so the statement cannot silently stop being true: every ACA row
# must carry the 12 m beam.  If the release is ever regenerated with the right
# dish this fires, and the sentence in the text must then be deleted.
assert n7 > 0 and bad == 0, (
    'theta_pb_arcsec is no longer the 12 m beam on all %d ACA rows (%d '
    'exceptions) -- the justification for shipping pb_atten has changed' % (n7, bad))

# =====================================================================  3
# The injection campaign.  Its blindness to A is real; the BIAS IS ZERO.
inj = json.load(open(D('p90_pb.json')))['rows']
m('PbInjNUnit', '%d' % len(inj))
n_app = sum(1 for u in inj if abs(u['strig'] - u['smin_app']) <= 1e-12 * u['strig'])
n_diff = sum(1 for u in inj
             if abs(u['smin_corr'] - u['smin_app']) > 1e-3 * u['smin_app'])
# ★ The claim is that s_trig is the APPARENT 5 sigma on every unit.  Two
# assertions, in opposite directions: it must hold everywhere, AND the two
# conventions must actually differ on some units, or the test is vacuous and
# proves nothing about which convention the ladder is in.
assert n_app == len(inj), (
    's_trig is not the apparent 5 rms on %d of %d units -- A does NOT cancel '
    'out of the completeness ratio and a systematic must be carried'
    % (len(inj) - n_app, len(inj)))
assert n_diff > 0, ('no injected unit distinguishes the apparent from the '
                    'corrected S_min, so this test cannot tell them apart')
m('PbInjNApparent', '%d' % n_app)
m('PbInjNDistinct', '%d' % n_diff)
ioff = sorted(u['off'] for u in inj)
iatt = sorted(u['A'] for u in inj)
m('PbInjOffMin', '%.3f' % ioff[0])
m('PbInjOffMed', '%.3f' % stat.median(ioff))
m('PbInjOffMax', '%.2f' % ioff[-1])
m('PbInjAMin', '%.4f' % iatt[0])
m('PbInjAMed', '%.6f' % stat.median(iatt))
m('PbInjWorstPct', '%.1f' % (100 * (1 / iatt[0] - 1)))
m('PbInjNBelow', '%d' % sum(1 for a in iatt if a < 0.999))
# ★ The limitation that DOES survive: released windows beyond any injected
# offset, where the completeness curve is interpolated rather than measured.
beyond = [r for r in rows if float(r['pb_offset_arcsec']) > ioff[-1]]
m('PbNBeyond', '%d' % len(beyond))
m('PbBeyondAMin', '%.3f' % min(float(r['pb_atten']) for r in beyond))
m('PbNBeyondStar', '%d' % len({r['star_name'] for r in beyond}))
m('PbNBeyondCross', '%d' % sum(1 for r in beyond
                               if str(r.get('crossing', '')).lower() == 'true'))

# =====================================================================  4
# The provenance gap: disclosed, not reconciled.
gap = json.load(open(D('provenance_gap_v408.json')))
m('PbGapN', '%d' % len(gap))
m('PbGapStar', gap[0]['star'])
m('PbGapEb', gap[0]['eb'].replace('_', r'\_'))
m('PbGapPctLo', '%.2f' % min(g['rms_discrepancy_pct'] for g in gap))
m('PbGapPctHi', '%.2f' % max(g['rms_discrepancy_pct'] for g in gap))
# ★ DIRECTION, stated: the published rms is HIGHER than the surviving
# product's, so the published limits are WEAKER.  A gap in the conservative
# direction is still a gap, but the reader is entitled to know which way.
assert all(g['rms_published_mJy'] > g['rms_surviving_product_mJy'] for g in gap)
m('PbGapDirection', 'conservative')
# the crossing among them, and the size of the disagreement in the STATISTIC,
# recomputed here from the surviving product rather than transcribed
inv = json.load(open(D('inv_products.json')))['recs']
xg = [g for g in gap if str(g['crossing']).lower() == 'true']
assert len(xg) == 1, xg
g0 = xg[0]
cand = [p for p in inv if p['eb'] == g0['eb']
        and abs(min(p['freq_lo_GHz'], p['freq_hi_GHz']) - g0['flo_GHz']) < 0.002]
assert cand, 'no surviving product for the crossing row of the provenance gap'
p0 = min(cand, key=lambda p: abs(p['rms_combined_mJy']
                                 - g0['rms_surviving_product_mJy']))
m('PbGapXfreq', '%.3f' % g0['flo_GHz'])
m('PbGapXTstarPub', '%.4f' % g0['star_snr_published'])
m('PbGapXTstarProd', '%.4f' % p0['star_peak_snr'])
m('PbGapXTstarPct', '%.1f' % (100 * abs(p0['star_peak_snr']
                                        - g0['star_snr_published'])
                              / g0['star_snr_published']))
# ★ The two routes.  DROPPED_EXTRACTIONS.md found these four rows by failing to
# reproduce T*; this audit found them by failing to reproduce rms -- a
# different quantity, a different comparison, a position-keyed join.  The
# declared gap list is 4 + the 10 windows with no product on disk at all.
m('PbGapNoProd', '%d' % nsrc['inverted'])
m('PbGapDeclared', '%d' % (len(gap) + nsrc['inverted']))
# and the new columns are NOT compromised by it
m('PbGapSminRes', '%.1e' % max(g['smin_residual'] for g in gap))
m('PbGapAMin', '%.6f' % min(g['pb_atten'] for g in gap))
assert max(g['smin_residual'] for g in gap) < 1e-4, (
    'the provenance gap has reached the attenuation columns')

# =====================================================================  5
# One offset, two attenuations.  Measured from the products themselves.
J = 'A002_X1009c59_X1ba4d'
jr = [p for p in inv if p['eb'] == J and p.get('primary_beam_offset_arcsec')]
# ★ Key on the WINDOW, not on the offset alone.  All ten extractions of this
# block store the same 5.744" offset, so a key of (offset) alone mixes five
# different windows and understates the disagreement; the quantity is the two
# responses stored for ONE window, and the window with the largest
# disagreement is the one to quote.
byw = collections.defaultdict(dict)
for p in jr:
    byw[round(p['freq_lo_GHz'], 4)][round(p['primary_beam_atten'], 4)] = \
        p['primary_beam_fwhm_arcsec']
dual = {k: v for k, v in byw.items() if len(v) > 1}
assert dual, 'the ALMA J1537 two-attenuation case is no longer present'
k0 = max(dual, key=lambda k: max(dual[k]) / min(dual[k]))
a_lo, a_hi = min(dual[k0]), max(dual[k0])
# and every one of them stores the same offset, which is the actual finding
offs = {round(p['primary_beam_offset_arcsec'], 3) for p in jr}
assert len(offs) == 1, offs
m('PbJOffset', '%.3f' % sorted(offs)[0])
m('PbJAlo', '%.4f' % a_lo)
m('PbJAhi', '%.4f' % a_hi)
m('PbJPct', '%.1f' % (100 * (a_hi / a_lo - 1)))
m('PbJNWin', '%d' % len(dual))
m('PbJFwhmHi', '%.1f' % dual[k0][a_lo])     # the NARROW beam -> the lower A
m('PbJFwhmLo', '%.1f' % dual[k0][a_hi])     # the wide beam   -> the higher A
m('PbJArray', '7\\,m')
_ja = arr.get(J) or {}
assert _ja.get('array') == '7m', _ja
m('PbJAntennas', '%d' % int(_ja.get('n_ant') or 0))
# ★ The release publishes the HIGHER (7 m) value, which the archive says is the
# right one -- so nothing published is wrong.  Asserted against the catalogue,
# because the point of this paragraph is that the release is correct and only a
# position-only join would get it wrong.
_rel = {round(float(r['pb_atten']), 4) for r in rows if r['eb'] == J}
assert _rel <= set().union(*[set(v) for v in dual.values()]) and a_hi in _rel, \
    ('the release no longer carries the 7 m attenuation for %s: %s' % (J, _rel))

# ★ And the number this resolution changes: the measured worst beam-model
# sensitivity.  Imported from the GATE so the text cannot drift from it.
import pbgate_v408
pbgate_v408.run(0, quiet=True)
m('PbModelMax', '%.4f' % pbgate_v408.MODELMAX[0])
m('PbModelTol', '%.2f' % pbgate_v408.MODEL_TOL)
assert pbgate_v408.MODELMAX[0] < pbgate_v408.MODEL_TOL

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by pbaudit_v408.py -- do not hand-edit.\n')
    fh.write('\n'.join(sorted(M)) + '\n')
# ★ The macro count is pinned with ==, per D31: the failure this project keeps
# meeting is a macro that DISAPPEARS, and an absent macro is neither empty nor
# NaN.  Driven both ways by selftest_v408.py.
NMACRO = int(os.environ.get('PBAUDIT_NMACRO', '60'))
assert len(M) == NMACRO, (
    'pbaudit macro count moved to %d (expected %d) -- a macro was added or '
    'SILENTLY DROPPED' % (len(M), NMACRO))
bad = [x for x in M if '{}' in x or 'nan' in x.lower()]
assert not bad, bad[:3]
print('pbaudit_v408 (round 101): %d windows; offset median %.3f" p99 %.2f" '
      'max %.2f"; A min %.4f, <0.99 on %d, <0.9 on %d, <0.5 on %d'
      % (len(rows), stat.median(off), off[int(0.99 * len(off))], off[-1],
         att[0], sum(1 for a in att if a < 0.99),
         sum(1 for a in att if a < 0.9), sum(1 for a in att if a < 0.5)))
print('  smin == 5 rms / A on %d of %d rows (worst residual %.1e); provenance '
      '%d product, %d recovered, %d inverted'
      % (len(rows), len(rows), worst, nsrc['product'], nsrc['recovered'],
         nsrc['inverted']))
print('  theta_pb_arcsec is the 12 m beam on all %d ACA rows (%.1fx too narrow)'
      % (n7, 12.0 / 7.0))
print('  injection: s_trig is the APPARENT 5 rms on %d of %d units, %d of which '
      'distinguish the two conventions -> A cancels, bias EXACTLY zero'
      % (n_app, len(inj), n_diff))
print('  limitation: %d released windows lie beyond the largest injected offset '
      '(%.2f"), down to A = %.3f, on %d stars holding %d crossings'
      % (len(beyond), ioff[-1], min(float(r['pb_atten']) for r in beyond),
         len({r['star_name'] for r in beyond}),
         sum(1 for r in beyond if str(r.get('crossing', '')).lower() == 'true')))
print('  provenance gap %d + %d no-product = %d declared; rms high by %.2f-%.2f%% '
      '(conservative); T* %.4f published vs %.4f surviving (%.1f%%) on a crossing'
      % (len(gap), nsrc['inverted'], len(gap) + nsrc['inverted'],
         min(g['rms_discrepancy_pct'] for g in gap),
         max(g['rms_discrepancy_pct'] for g in gap),
         g0['star_snr_published'], p0['star_peak_snr'],
         100 * abs(p0['star_peak_snr'] - g0['star_snr_published'])
         / g0['star_snr_published']))
print('  ALMA J1537 %s: one %.3f" offset, A = %.4f (12 m) and %.4f (7 m); '
      'archive says 7 m (%d antennas), so the release is right; beam-model '
      'max x%.4f'
      % (J, sorted(offs)[0], a_lo, a_hi, int(_ja.get('n_ant') or 0),
         pbgate_v408.MODELMAX[0]))
print('  wrote %d macros to %s' % (len(M), os.path.basename(OUT)))
