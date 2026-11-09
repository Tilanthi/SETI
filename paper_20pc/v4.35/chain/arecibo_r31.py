#!/usr/bin/env python3
r"""Round 3130: THE LIMITS AGAINST WHAT AN ARECIBO-LIKE TRANSMITTER SENDS.

The author (v4.31 edit 2): with no detection, the abstract and the conclusions
state the upper limits "referencing them against what an Arecibo-like
telescope could send to the Earth" -- the Arecibo planetary radar EIRP, with
its source cited.  The value is frozen, with its citation, in
r31inputs/20261105/arecibo_eirp.json: 2e13 W (20 TW, Sheikh et al. 2025,
\citep{EarthDetectingEarth2025}, Sec. IV, after Ekers et al. 2002), with
Margot et al. (2023; 2.2e13 W) and the CWTFM normalisation of Enriquez et al.
(2017; 1e13 W) as cross-checks.  This is NOT \FomAreciboEirp (round 48), which
is the CWTFM's own order-of-magnitude normalisation and stays where it is.

It compares that EIRP with the per-system limits exactly as round 103 forms
them: each Class A system's best limit-eligible window (adopted_e90), over the
\NSysALimSum systems with a bounded position (posflag_r31 excluded).

Macros:
  \AroEirp         the Arecibo planetary-radar EIRP (math mode, W)
  \AroFreqGHz      its frequency
  \AroMedMult      the median system limit as a multiple of it
  \AroDeepMult     the deepest system limit as a multiple of it
  \AroNSysBelow    systems (of \NSysALimSum) whose limit is at or below it
  \AroNSysBelowWord  the same as a word ("no" for zero), for "no system ..."
  \AroNSysTen      systems whose limit is within ten times it
  \AroDistMedPc    the median, over the same systems, of the distance at which
                   an Arecibo-like transmitter would sit exactly at that
                   system's limit (EIRP = 4 pi d^2 S, so d_AO = d sqrt(L_AO/E));
                   i.e. how far away the data of each system would have seen it
  \AroDistMaxPc    the largest such distance (the deepest system's)
  \AroDistMaxStar  the system it belongs to

Assertions (all driven):
  R1 the frozen EIRP is the radar's P_tx G to 15 % and agrees with Margot et
     al. to 15 %, and is not the CWTFM normalisation  (drive 1)
  R2 the systems reproduce round 103: their number is \NSysALimSum and their
     median and minimum print as \EirpNinetySysMedA and \EirpNinetySysLoA
     (drive 2)
  R3 the count at or below the benchmark is the count of a set, and is zero
     exactly when the deepest multiple exceeds one  (drive 3)
  R4 the printed multiples are the ratio of the limits to the benchmark, not
     its inverse, and the median one is at least the deepest one (drive 4)
  R5 every Arecibo distance is shorter than the system's own distance where
     the limit lies above the benchmark, the median distance is at most the
     largest, and the largest belongs to the deepest-normalised system (drive 5)
  R6 (r34, R2-13) the x10 count is the same whichever side of the boundary a
     system exactly on it is put (<= and < agree on the unrounded limits), and
     the nearest system on each side is named (drive 6)
  R7 (r34, R2-4) with each system's best window divided by (1 + o), o its
     decorrelation (decor_r13; imputed where the block has no record), every
     Arecibo distance shortens or stays, the median does not lengthen, the
     largest belongs to its argmax, and the basis words are the Matcher's
     (drive 7)

r34 (R2-13): \AroMedMult and \AroDeepMult are now the ratios of the PRINTED
limit (\EirpNinetySysMedA, \EirpNinetySysLoA, two figures) to the PRINTED
benchmark (\AroEirp), at two figures, so "1.2e15 W, 60 times 2e13 W" reads
true as printed; R4 is restated to that invariant (the unrounded ratio must
lie inside the rounding of the printed limit).  The x10 boundary is <= on the
unrounded limits (R6).
r34 (R2-4): the decorrelation-corrected Arecibo distances, \AroDistMedPcDec,
\AroDistMaxPcDec, \AroDistMaxStarDec (+ \AroDistMaxDecBasis, and
\AroDistMaxBasis for the nominal one), and \AroNSysTenDec.

    python3 arecibo_r31.py [--drive N]      (N = 1..5; a drive prints
                                             "FAILED: R<N>", writes nothing
                                             and exits 1; gate.sh runs all five)
"""
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import adopted_e90 as ae  # noqa: E402
import posflag_r31 as pf  # noqa: E402
import decor_r13 as dc  # noqa: E402  r34 R2-4: the one decorrelation
import decimal  # noqa: E402

ROUND = 3130
DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round%d.tex' % ROUND if DRIVE is None
                       else 'numbers/survey_numbers_round%d_drive%d.tex' % (ROUND, DRIVE))
SRC = os.path.join(HERE, 'r31inputs', '20261105', 'arecibo_eirp.json')

OUT, fail = [], []
WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']


def m(name, val):
    assert name.isalpha(), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-74s %s  %s' % (label[:74], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label.split()[0])


def sci(x, nd=1):
    """Round 103's own formatter (numbers_v410.sci): two significant figures."""
    e = int(math.floor(math.log10(x)))
    return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)


def sci0(x):
    e = int(math.floor(math.log10(x)))
    return r'%d\times10^{%d}' % (round(x / 10.0 ** e), e)


def sig2(x):
    """Two significant figures, as plain text (no exponent: the multiples are 1-1000)."""
    if x >= 100:
        return '%d' % int(round(x, -int(math.floor(math.log10(x))) + 1))
    if x >= 10:
        return '%d' % int(round(x))
    return '%.1f' % x


# ---------------------------------------------------------------- the benchmark
REC = json.load(open(SRC))
L_AO = float(REC['eirp_W'])
if DRIVE == 1:
    L_AO = 1.0e13          # the CWTFM normalisation passed off as the radar's EIRP
ptg = REC['transmitter_power_W'] * 10 ** (REC['antenna_gain_dBi'] / 10.0)
margot = [c['eirp_W'] for c in REC['cross_checks'] if c['bibkey'] == 'Margot2023'][0]
fom = ae._texval('FomAreciboEirp')
ck('R1 the frozen EIRP is the radar P_tx G and Margot et al.\'s value to 15 %, and is '
   'not the CWTFM normalisation',
   abs(L_AO / ptg - 1) < 0.15 and abs(L_AO / margot - 1) < 0.15
   and REC['adopted_source']['bibkey'] == 'EarthDetectingEarth2025'
   and (fom is None or abs(L_AO / float(fom.replace(r'\times10^{', 'e').rstrip('}')) - 1) > 0.15),
   'L_AO %.3g, P_tx G %.3g, Margot %.3g, FomAreciboEirp %s' % (L_AO, ptg, margot, fom))

# ---------------------------------------------------------------- the systems, as round 103 forms them
CAT = ae.catalogue()
E = ae.per_window(CAT)
best, _lost = ae.best_by_system(CAT, E)
sysP = {s: (r, v) for s, (r, v) in best.items() if not pf.is_cond(s)}
if DRIVE == 2:
    sysP = dict(best)      # the position-conditional systems put back
vals = sorted(v for _, v in sysP.values())
med, lo = statistics.median(vals), vals[0]
n_tex = ae._texval('NSysALimSum')
med_tex, lo_tex = ae._texval('EirpNinetySysMedA'), ae._texval('EirpNinetySysLoA')
ck('R2 the systems are round 103\'s: their number, median and minimum',
   n_tex is not None and len(vals) == int(n_tex) and sci(med) == med_tex and sci(lo) == lo_tex,
   '%d (\\NSysALimSum %s), median %s (%s), min %s (%s)'
   % (len(vals), n_tex, sci(med), med_tex, sci(lo), lo_tex))

# ---------------------------------------------------------------- counts and multiples
below = sorted(s for s, (_, v) in sysP.items() if v <= L_AO)
ten = sorted(s for s, (_, v) in sysP.items() if v <= 10 * L_AO)
n_below = len(below)
if DRIVE == 3:
    n_below = sum(1 for v in vals if v <= 10 * L_AO)     # the wrong threshold
deep_mult, med_mult = lo / L_AO, med / L_AO
# ★ r34 (R2-13): the PRINTED multiples are the ratio of the printed limit to the printed benchmark, two
# figures, halves up, so the sentence "1.2e15 W, N times 2e13 W" is arithmetic a reader can check.


def _pval(tex):
    mm = tex.replace(' ', '').split(r'\times10^{')
    return decimal.Decimal(mm[0]) * decimal.Decimal(10) ** int(mm[1].rstrip('}'))


def _two(x):
    d = decimal.Decimal(x)
    return d.quantize(decimal.Decimal(1).scaleb(d.adjusted() - 1), rounding=decimal.ROUND_HALF_UP)


def _halfulp(tex):
    mant = tex.replace(' ', '').split(r'\times10^{')[0]
    dp = len(mant.split('.')[1]) if '.' in mant else 0
    return decimal.Decimal('0.5') * decimal.Decimal(10) ** (-dp) * (_pval(tex) / decimal.Decimal(mant))


_LP = _pval(sci0(L_AO) if abs(L_AO / 10 ** math.floor(math.log10(L_AO)) % 1) < 1e-9 else sci(L_AO))
_MEDP = _two(_pval(sci(med)) / _LP)
_DEEPP = _two(_pval(sci(lo)) / _LP)
_pr_ok = all(abs(float(pm) - true) <= float(_halfulp(sci(v)) / _LP) + 0.5 * float(
    decimal.Decimal(1).scaleb(pm.adjusted() - 1)) for pm, true, v in
    ((_MEDP, med_mult, med), (_DEEPP, deep_mult, lo)))
ck('R3 the count at or below the benchmark is a set count, zero exactly when the '
   'deepest system lies above it',
   n_below == len(below) and (n_below == 0) == (deep_mult > 1.0) and len(ten) >= n_below,
   '%d at or below (%s), %d within x10, deepest x%.3f' % (n_below, ', '.join(below) or '-', len(ten), deep_mult))
if DRIVE == 4:
    med_mult, deep_mult = L_AO / med, L_AO / lo         # the inverse ratio
ck('R4 the multiples are limit / benchmark (printed / printed, two figures, inside the printed limit\'s '
   'rounding of the unrounded ratio), and the median one is at least the deepest one',
   abs(med_mult * L_AO - med) < 1e-6 * med and abs(deep_mult * L_AO - lo) < 1e-6 * lo
   and med_mult >= deep_mult and _pr_ok and _MEDP >= _DEEPP,
   'median x%.4g (printed x%s), deepest x%.4g (printed x%s)' % (med_mult, _MEDP, deep_mult, _DEEPP))

# ---------------------------------------------------------------- the distance an Arecibo-like transmitter is seen to
dist = {}
for s, (r, v) in sysP.items():
    d = float(r['dist_pc'])
    dist[s] = (d * math.sqrt(L_AO / v), d, v)
if DRIVE == 5:
    dist = {s: (d * math.sqrt(v / L_AO), d, v) for s, (_, d, v) in dist.items()}
dao = sorted(x[0] for x in dist.values())
dmed, dmax = statistics.median(dao), dao[-1]
smax = max(dist, key=lambda s: dist[s][0])
deepnorm = max(dist, key=lambda s: math.sqrt(1.0 / dist[s][2]) * dist[s][1])
ck('R5 the Arecibo distance is below the system distance wherever the limit lies above '
   'the benchmark; median <= max; max is the deepest-normalised system',
   all(x[0] < x[1] for x in dist.values() if x[2] > L_AO) and dmed <= dmax and smax == deepnorm,
   'median %.3g pc, max %.3g pc (%s)' % (dmed, dmax, smax))

# ---------------------------------------------------------------- r34 R2-13: the x10 boundary
_lt = sorted(s for s, (_, v) in sysP.items() if v < 10 * L_AO)
_inn = max((s for s in ten), key=lambda s: sysP[s][1]) if ten else None
_out = min((s for s in sysP if s not in ten), key=lambda s: sysP[s][1])
if DRIVE == 6:
    _lt = _lt[1:]
ck('R6 the x10 count does not depend on how the boundary is treated (<= and < agree), the nearest '
   'systems either side named',
   _lt == ten and (_inn is None or sysP[_inn][1] <= 10 * L_AO < sysP[_out][1]),
   '%d within (<=), %d (<); nearest inside %s x%.3f, outside %s x%.3f'
   % (len(ten), len(_lt), _inn, sysP[_inn][1] / L_AO if _inn else 0, _out, sysP[_out][1] / L_AO))

# ---------------------------------------------------------------- r34 R2-4: decorrelation-corrected distances
MATCH = dc.Matcher(HERE)
dcor = {}
for s, (r, v) in sysP.items():
    o, basis, _hi = MATCH.correction(r)
    vc = v * (1.0 + o) if o is not None else v
    dcor[s] = (float(r['dist_pc']) * math.sqrt(L_AO / vc), basis, vc)
if DRIVE == 7:
    dcor = {s: (x[0] * 1.2, x[1], x[2]) for s, x in dcor.items()}
dcv = sorted(x[0] for x in dcor.values())
smaxd = max(dcor, key=lambda s: dcor[s][0])
ten_dec = sorted(s for s, x in dcor.items() if x[2] <= 10 * L_AO)
ck('R7 decorrelation divided out: every Arecibo distance shortens or stays, the median does not lengthen, '
   'the largest is its argmax, the bases are the Matcher\'s',
   all(dcor[s][0] <= dist[s][0] * (1 + 1e-12) for s in dcor) and statistics.median(dcv) <= dmed
   and dcor[smaxd][0] == dcv[-1] and all(x[1] in ('measured', 'matched', 'none') for x in dcor.values())
   and len(ten_dec) <= len(ten),
   'median %.3g pc (nominal %.3g), max %.3g pc (%s, %s); x10 %d (nominal %d)'
   % (statistics.median(dcv), dmed, dcv[-1], smaxd, dcor[smaxd][1], len(ten_dec), len(ten)))
_BASISWORD = {'measured': 'measured', 'matched': 'imputed', 'none': 'not estimated'}

# ---------------------------------------------------------------- macros
m('AroEirp', sci0(L_AO) if abs(L_AO / 10 ** math.floor(math.log10(L_AO)) % 1) < 1e-9 else sci(L_AO))
m('AroFreqGHz', '%.2f' % REC['frequency_GHz'])
m('AroMedMult', '%s' % _MEDP)
m('AroDeepMult', '%s' % _DEEPP)
m('AroNSysBelow', '%d' % n_below)
m('AroNSysBelowWord', WORDS[n_below] if n_below < len(WORDS) else '%d' % n_below)
m('AroNSysTen', '%d' % len(ten))
m('AroDistMedPc', '%.1f' % dmed)
m('AroDistMaxPc', '%.1f' % dmax)
star = sysP[smax][0]['star_name'] if DRIVE != 5 else smax
try:
    import star_alias
    star = star_alias.designation(star)
except Exception:
    pass
m('AroDistMaxStar', star)


def _desig(s):
    try:
        import star_alias
        return star_alias.designation(sysP[s][0]['star_name'])
    except Exception:
        return s


# r34 (R2-13): the x10 boundary's neighbours; (R2-4) the corrected distances
_TWO = lambda v: '%.1f' % float(_two(v / 1e14))      # Table F1's printing of a limit, in 1e14 W  # noqa: E731
m('AroTenNearIn', _desig(_inn) if _inn else 'none')
m('AroTenNearOut', _desig(_out))
# the clause the text uses: who sits either side of the boundary, and -- where the two print alike in
# Table F1 -- that the count is taken on the unrounded limits
_ci = '%s (%s~times)' % (_desig(_inn).replace(' ', '~'), '%.1f' % (sysP[_inn][1] / L_AO)) if _inn else ''
_co = '%s (%s~times)' % (_desig(_out).replace(' ', '~'), '%.1f' % (sysP[_out][1] / L_AO))
if _inn and _TWO(sysP[_inn][1]) == _TWO(sysP[_out][1]):
    _clause = ('%s is inside it and %s just outside, although both limits print as $%s\\times10^{14}$\\,W '
               'in Table~\\ref{tab:persys}, because the count is taken on the unrounded limits'
               % (_ci, _co, _TWO(sysP[_inn][1])))
else:
    _clause = '%s is the last inside it and %s the first outside' % (_ci, _co)
m('AroTenEdgeClause', _clause)
m('AroDistMaxBasis', _BASISWORD[MATCH.correction(sysP[smax][0])[1]])
m('AroDistMedPcDec', '%.1f' % statistics.median(dcv))
m('AroDistMaxPcDec', '%.1f' % dcv[-1])
m('AroDistMaxStarDec', _desig(smaxd))
m('AroDistMaxDecBasis', _BASISWORD[dcor[smaxd][1]])
m('AroNSysTenDec', '%d' % len(ten_dec))

if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    raise SystemExit(1)
if DRIVE is not None:
    print('drive %d did not fire' % DRIVE)
    raise SystemExit(0)
hdr = ['%% GENERATED by arecibo_r31.py (round %d) -- do not hand-edit.' % ROUND,
       '% The limits against the Arecibo planetary radar EIRP (Sheikh et al. 2025;'
       ' r31inputs/20261105/arecibo_eirp.json).']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
print('arecibo_r31: %d macros -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
