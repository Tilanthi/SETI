#!/usr/bin/env python3
r"""Round 78 (R2-M9.2): a like-for-like comparison with Mason et al. (2025).

The manuscript compared this survey's median per-system EIRP completeness
with Mason et al.'s limit for their nearest star and reported the ratio.  The
referee asks for that sentence to be deleted, because the two surveys differ
by a factor 10^4 in distance and the EIRP ratio is almost entirely the
distance term, and to be replaced by the quantity that does not depend on how
far away the target happens to be: the minimum detectable RECEIVED flux,

    F_min = S_min dnu     [W m^-2],

at matched channel width and matched completeness convention.

Mason et al. 2025, MNRAS 536, 2127 (arXiv:2411.19827), their Eq. (8) and
Table 2: 28 Gaia DR3 stars lying within the 59-arcsec fields of four ALMA
calibrators, Band 3, project 2017.1.01794.S, channels of 30.52 kHz, and
S_min = 5 x the median field r.m.s., which is 25, 27, 37 and 38 mJy in the
four fields.  Their completeness convention is therefore a bare 5-sigma
threshold, the same convention as this paper's P_trig and NOT the same as
P_90^sel.  Both are reported below.

The transcription of their numbers is checked, not assumed: the generator
reproduces their published EIRP_min for the closest target star from their
own distance, field r.m.s. and channel width, and stops the build if it
cannot.
"""
import csv
import math
import os
import statistics as st

os.chdir(os.path.dirname(os.path.abspath(__file__)))

OUT = []


def M(n, v):
    OUT.append(r'\newcommand{\%s}{%s}' % (n, v))


def sci(x, sig=2):
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sig - 1, x / 10.0 ** e, e)


# ------------------------------------------------------------ Mason et al.
MAS_DNU_HZ = 30.52e3                 # their channel width, their S2.3
MAS_SNR = 5.0                        # their detection threshold
MAS_RMS_MJY = (25.0, 27.0, 37.0, 38.0)          # their Table 2 caption
MAS_NEAREST_KPC = 1.010                          # their Table 2, field 4 row 5
MAS_NEAREST_RMS = 37.0                           # that field's r.m.s.
MAS_NEAREST_EIRP = 6.91e17                       # their published value
MAS_NSTAR = 28
MAS_NCAL = 4
PC_M = 3.0856775814913673e16
MJY_SI = 1e-29                       # 1 mJy in W m^-2 Hz^-1


def flux(rms_mjy):
    """Minimum detectable received flux, W m^-2, on their convention."""
    return MAS_SNR * rms_mjy * MJY_SI * MAS_DNU_HZ


# positive control: their own EIRP_min must come back out
_d = MAS_NEAREST_KPC * 1e3 * PC_M
_eirp = 4 * math.pi * _d ** 2 * flux(MAS_NEAREST_RMS)
assert abs(_eirp / MAS_NEAREST_EIRP - 1) < 0.01, \
    'Mason EIRP not reproduced: %.3e against %.3e' % (_eirp, MAS_NEAREST_EIRP)

MAS_F = [flux(x) for x in MAS_RMS_MJY]
M('MasonYear', '2025')
M('MasonNStar', '%d' % MAS_NSTAR)
M('MasonNCal', '%d' % MAS_NCAL)
M('MasonChanKHz', '%.2f' % (MAS_DNU_HZ / 1e3))
M('MasonRmsLo', '%.0f' % min(MAS_RMS_MJY))
M('MasonRmsHi', '%.0f' % max(MAS_RMS_MJY))
M('MasonFluxLo', '$%s$' % sci(min(MAS_F)))
M('MasonFluxHi', '$%s$' % sci(max(MAS_F)))
M('MasonFluxMed', '$%s$' % sci(st.median(MAS_F)))
M('MasonNearKpc', '%.2f' % MAS_NEAREST_KPC)
M('MasonNearEirp', '$%s$' % sci(MAS_NEAREST_EIRP))

# --------------------------------------------------------------- this work
ROWS = [r for r in csv.DictReader(open('per_target_results_v3.99.csv'))
        if r['search_class'] == 'A']


def f_trig(r):
    return float(r['smin_mJy']) * MJY_SI * float(r['chanw_Hz'])


def scale_to_mason(r):
    """S_min falls as 1/sqrt(dnu) at fixed integration time, so the received
    flux threshold S_min dnu rises as sqrt(dnu).  This puts every window on
    Mason's channel width, which is the only way the two are comparable: a
    coarse channel buys sensitivity in S_min and loses it in bandwidth."""
    return math.sqrt(MAS_DNU_HZ / float(r['chanw_Hz']))


TRIG = sorted(f_trig(r) for r in ROWS)
MATCH = sorted(f_trig(r) * scale_to_mason(r) for r in ROWS)
_sel = [(f_trig(r) * float(r['eirp_p90_sel_W']) / float(r['eirp_nominal_W']),
         f_trig(r) * scale_to_mason(r)
         * float(r['eirp_p90_sel_W']) / float(r['eirp_nominal_W']))
        for r in ROWS if r['eirp_p90_sel_W']]
SEL = sorted(x[0] for x in _sel)
SELM = sorted(x[1] for x in _sel)

M('FluxTrigBest', '$%s$' % sci(TRIG[0]))
M('FluxTrigMed', '$%s$' % sci(st.median(TRIG)))
M('FluxMatchBest', '$%s$' % sci(MATCH[0]))
M('FluxMatchMed', '$%s$' % sci(st.median(MATCH)))
M('FluxSelBest', '$%s$' % sci(SEL[0]))
M('FluxSelMed', '$%s$' % sci(st.median(SEL)))
M('FluxSelMatchBest', '$%s$' % sci(SELM[0]))
M('FluxSelMatchMed', '$%s$' % sci(SELM[1 * len(SELM) // 2]))
M('FluxChanMedKHz', '%.0f' % (st.median(float(r['chanw_Hz'])
                                        for r in ROWS) / 1e3))
# the two statements the text makes, as ratios, so neither can be mis-signed
M('FluxBestRatio', '%.0f' % (st.median(MAS_F) / MATCH[0]))
M('FluxMedRatio', '%.1f' % (st.median(MATCH) / st.median(MAS_F)))
M('FluxSelMedRatio', '%.0f' % (st.median(SELM) / st.median(MAS_F)))

with open('survey_numbers_round78.tex', 'w') as fh:
    fh.write('%% GENERATED by masoncmp_v401.py -- do not hand-edit.\n')
    fh.write('\n'.join(OUT) + '\n')

print('masoncmp: Mason F_min %.3g-%.3g W/m2 at %.2f kHz (EIRP control %.3e '
      'against published %.3e)'
      % (min(MAS_F), max(MAS_F), MAS_DNU_HZ / 1e3, _eirp, MAS_NEAREST_EIRP))
print('  this work, 5 sigma trigger, native channels: best %.3g, median %.3g'
      % (TRIG[0], st.median(TRIG)))
print('  matched to %.2f kHz:                          best %.3g, median %.3g'
      % (MAS_DNU_HZ / 1e3, MATCH[0], st.median(MATCH)))
print('  at P90^sel, matched:                          best %.3g, median %.3g'
      % (SELM[0], st.median(SELM)))
print('%d macros -> survey_numbers_round78.tex' % len(OUT))
