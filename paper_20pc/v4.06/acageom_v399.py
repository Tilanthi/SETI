#!/usr/bin/env python3
"""R2-M3 (v3.99): what actually causes the stellar-rank displacement.

Referee 2 argues that the non-exchangeability of the stellar rank is not a
primary-beam noise gradient, as this paper has claimed, but a CONTROL
GEOMETRY ERROR confined to the ACA windows.  Checking the pipeline source
confirms the premise: seti_extract_generic.py sets

    ALMA_DISH_M = 12.0
    primary_beam_arcsec(f) = 1.22 lambda / ALMA_DISH_M
    annulus = 0.14 .. 0.78 * primary_beam_arcsec

with no dependence on which array observed the block.  For an ACA 7 m
window the annulus is therefore placed at 7/12 = 58 per cent of the radius
it should occupy, and the inner edge lands at ~3.8 arcsec at 230 GHz,
INSIDE a typical ACA synthesised main lobe (~5-7 arcsec).  Controls there
are not independent of the star: they sit on the star's own synthesised
beam and collect its flux.

That predicts three things, and this generator tests all three against the
stored control vectors:

  (1) the displacement is confined to the ACA stratum;
  (2) within ACA windows the excess is at the INNER edge of the annulus,
      where the synthesised-beam contamination is, and falls outward;
  (3) 12 m windows, whose annulus is correctly placed, show no such inner
      excess.

If all three hold, the primary-beam-gradient explanation is wrong and must
be withdrawn, because a primary-beam effect would act on both arrays.

A further consequence, which referee 2 also notes and which this paper got
backwards: contaminated controls are INFLATED, so the star ranks LOW.  That
is the observed direction (median rank below 0.5).  A bias that pushes the
star low cannot manufacture star-first outliers, so the manuscript's claim
that the stage-1 excess is "an artefact of the position-dependent rank
bias" is unsupported and is withdrawn.

Writes survey_numbers_round61.tex and acageom_v399.json.
"""
# NOTE: this generator deliberately reads the PRE-REPAIR frozen export.
# It documents the control-geometry defect as it was, so it must not be
# repointed at corrected_export_v399.json. See ACA_REEXTRACTION_SPEC.md.
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round61.tex')

C_M_S = 299792458.0
SEED = 20260825
ANN_LO, ANN_HI, NPROBE = 0.14, 0.78, 512
DISH_12, DISH_ACA = 12.0, 7.0
ACA_MAX_BASELINE_M = 45.0          # ACA 7 m compact configuration

ROWS = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXP = {(r['eb'], r['flo'], r['fhi']): r for r in json.load(
    open(os.path.join(HERE, 'frozen_export_v3.81_survey.json')))['rows']}
ARCH = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))
EBS = ARCH['ebs']


def pb_arcsec(f_ghz, dish):
    return math.degrees(1.22 * (C_M_S / (f_ghz * 1e9)) / dish) * 3600.0


def probe_radii():
    """Fractional probe radii, reproduced from the pipeline's fixed seed."""
    import numpy as np
    rng = np.random.default_rng(SEED)
    # the pipeline draws the inner source ring first; reproduce that draw
    # order exactly or the probe radii will not match
    rr = np.sqrt(rng.uniform(ANN_LO ** 2, ANN_HI ** 2, NPROBE))
    rng.uniform(0, 2 * math.pi, NPROBE)
    return rr


def median(v):
    v = sorted(v)
    n = len(v)
    return float('nan') if not n else (
        v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2]))


U = probe_radii()
NB = 8
edges = [ANN_LO + (ANN_HI - ANN_LO) * k / NB for k in range(NB + 1)]
binof = [min(NB - 1, max(0, next(b for b in range(NB - 1, -1, -1)
                                 if u >= edges[b]))) for u in U]

prof = {'12m': [[] for _ in range(NB)], '7m': [[] for _ in range(NB)]}
nwin = {'12m': 0, '7m': 0}

for r in ROWS:
    eb = r['eb']
    arr = EBS.get(eb, {}).get('array')
    if arr not in ('12m', '7m'):
        continue
    e = EXP.get((eb, r['flo_GHz'], r['fhi_GHz']))
    if e is None:
        for k, v in EXP.items():
            if k[0] == eb and abs(float(k[1]) - float(r['flo_GHz'])) < 1e-6:
                e = v
                break
    if not e or not e.get('ctrl_all'):
        continue
    c = e['ctrl_all']
    if len(c) != NPROBE:
        continue
    # standardise each window by its own control median absolute deviation so
    # windows of different depth can be pooled
    m = median(c)
    ad = median([abs(x - m) for x in c]) or 1.0
    nwin[arr] += 1
    for k in range(NPROBE):
        prof[arr][binof[k]].append((c[k] - m) / (1.4826 * ad))

res = {}
for arr in ('12m', '7m'):
    res[arr] = [median(prof[arr][b]) if prof[arr][b] else float('nan')
                for b in range(NB)]

inner_12, inner_7 = res['12m'][0], res['7m'][0]
outer_12, outer_7 = median(res['12m'][NB // 2:]), median(res['7m'][NB // 2:])
exc_12 = inner_12 - outer_12
exc_7 = inner_7 - outer_7

# geometry numbers at a representative frequency
f_ref = 230.0
inner_impl = ANN_LO * pb_arcsec(f_ref, DISH_12)
inner_corr = ANN_LO * pb_arcsec(f_ref, DISH_ACA)
syn_aca = math.degrees(1.22 * (C_M_S / (f_ref * 1e9))
                       / ACA_MAX_BASELINE_M) * 3600.0

assert inner_impl < syn_aca, (
    'the implemented inner control radius %.2f" is outside the ACA '
    'synthesised beam %.2f" at %.0f GHz, so the contamination mechanism '
    'this text describes does not apply' % (inner_impl, syn_aca, f_ref))

L = ['%% GENERATED by acageom_v399.py -- do not hand-edit.\n']


def m_(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


m_('AcaDishRatioPct', '%.0f' % (100.0 * DISH_ACA / DISH_12))
m_('AcaInnerImpl', '%.1f' % inner_impl)
m_('AcaInnerCorr', '%.1f' % inner_corr)
m_('AcaSynBeam', '%.1f' % syn_aca)
m_('AcaRefFreq', '%.0f' % f_ref)
m_('AcaProfInnerSeven', '%+.2f' % inner_7)
m_('AcaProfOuterSeven', '%+.2f' % outer_7)
m_('AcaProfInnerTwelve', '%+.2f' % inner_12)
m_('AcaProfOuterTwelve', '%+.2f' % outer_12)
m_('AcaExcessSeven', '%+.2f' % exc_7)
m_('AcaExcessTwelve', '%+.2f' % exc_12)
m_('AcaNWinProfSeven', '%d' % nwin['7m'])
m_('AcaNWinProfTwelve', '%d' % nwin['12m'])
open(OUT, 'w').writelines(L)

json.dump(dict(prof_12m=res['12m'], prof_7m=res['7m'], nwin=nwin,
               inner_impl_arcsec=inner_impl, inner_corr_arcsec=inner_corr,
               aca_syn_beam_arcsec=syn_aca, excess_7m=exc_7,
               excess_12m=exc_12, bin_edges=edges),
          open(os.path.join(HERE, 'acageom_v399.json'), 'w'), indent=1)

print('acageom: windows 12m=%d 7m=%d' % (nwin['12m'], nwin['7m']))
print('  radial control profile, inner bin -> outer half (median, robust units)')
print('    12 m : %+.3f -> %+.3f   excess %+.3f' % (inner_12, outer_12, exc_12))
print('    ACA  : %+.3f -> %+.3f   excess %+.3f' % (inner_7, outer_7, exc_7))
print('  at %.0f GHz inner control at %.2f" vs ACA synth beam %.2f" '
      '(correct would be %.2f")' % (f_ref, inner_impl, syn_aca, inner_corr))
