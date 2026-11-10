#!/usr/bin/env python3
r"""decorhl_r34.py -- round 3401.  ★ r36 (R2-8, option a): THE CORRECTION IS NOW ADOPTED (adopted_e90 applies
it, measured or imputed); this file now publishes the limits WITHOUT it beside the adopted ones: the median and
count before the correction (\DcSysMedNom, \DcNomNEfifteen; \DcSysMedCorr RETIRED = \EirpNinetySysMedA), the
Table F1 note's values before the correction (\DcNomClause; \DcCorrClause RETIRED), the basis counts and the
imputation rule; D1-D4 restated (old: nominal adopted, corrected beside) and D5 added.

Original docstring (v4.34):  ROUND 34, R2-4: THE HEADLINE BOTH WAYS, NOMINAL AND WITH THE
ATMOSPHERIC DECORRELATION DIVIDED OUT.

The adopted limits are nominal in decorrelation: a real carrier loses coherence through the
atmosphere and an injected one does not, so every limit is optimistic by the window's
decorrelation fraction o (decor_r13.Matcher: measured from the block's own phase-calibrator phase
rms where the delivery records it, imputed from the blocks matched in baseline where it does not,
none for the one block with neither).  o is a FLOOR (the phase rms is the calibrator's), so the
nominal value stays the adopted one; this file gives the corrected one beside it:

  * the median system limit and the count at 1e15 W with each system's best window divided by
    (1 + o), over the systems the printed summaries are taken over (round 103's \NSysALimSum:
    posflag_r31's position-conditional systems left out), the system with no estimate kept at its
    nominal value -- \DcSysMedCorr beside \EirpNinetySysMedA, and the count is sens_r18's
    \NmDecAdjNEfifteen (same population since r34), which D2 reproduces;
  * for Table F1 (every system with a limit, as the table prints them) the corrected limit of each
    system whose dec. exceeds a tenth, in the table's own units and two-figure rounding, as one
    clause for the table note (\DcCorrClause, \DcNBigTab systems).

    python3 decorhl_r34.py              # -> numbers/survey_numbers_round3401.tex
    python3 decorhl_r34.py --drive N    # N = 1..5: prints FAILED: D<N>, writes nothing, exits 1

  D1 the systems are round 103's: their number is \NSysALimSum and the nominal median and deepest
     limit print as \EirpNinetySysMedA and \EirpNinetySysLoA (drive 1)
  D2 the correction is one-sided: every corrected limit is at least the nominal, the corrected
     median lies above the nominal, the count cannot rise, and the shift and count are sens_r18's
     \NmDecAdjShiftPct / \NmDecAdjNEfifteen (drive 2)
  D3 the clause names exactly the Table F1 systems whose dec. exceeds a tenth, each at its own
     limit times (1 + dec.), in the table's 10^14 W units at two figures (drive 3)
  D4 the system with no decorrelation estimate keeps its nominal value and is in both medians
     (drive 4)
MUST FOLLOW numbers_v410.py, sens_r18.py and persys_r17.py; MUST PRECEDE macrosource.py.
"""
import decimal
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import adopted_e90 as ae          # noqa: E402
import decor_r13 as dc            # noqa: E402
import posflag_r31 as pf          # noqa: E402
import star_alias as sa           # noqa: E402

ROUND = 3401
BIG = 0.10                        # "exceeds a tenth": Table 3's / sens_r18's threshold, in words in the prose
UNIT_EXP = 14                     # Table F1's column unit (persys_r17.UNIT_EXP), asserted below
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex'
                       % (ROUND, '' if DRIVE is None else '_drive%d' % DRIVE))
OUT, FAIL = [], []


def m(k, v):
    assert k.isalpha() and k not in {x.split('}')[0][13:] for x in OUT}, k
    OUT.append('\\newcommand{\\%s}{%s}' % (k, v))


def ck(label, ok, detail=''):
    print('  %-74s %s  %s' % (label[:74], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


def tv(name):
    v = ae._texval(name, HERE)
    assert v is not None, 'macro \\%s is not in the layer' % name
    return v


def sci(x, nd=1):
    e = int(math.floor(math.log10(x)))
    return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)


def two_sf(x):
    """persys_r17.two_sf, verbatim in behaviour: two figures, halves up."""
    d = decimal.Decimal(repr(float(x)))
    exp = d.adjusted()
    v = d.quantize(decimal.Decimal(1).scaleb(exp - 1), rounding=decimal.ROUND_HALF_UP)
    return '%.*f' % (max(0, 1 - exp), v)


# Table F1's column unit, read off the generated table's own header (persys_r17 writes it)
assert ('($10^{%d}$\\,W)' % UNIT_EXP) in open(os.path.join(HERE, 'tab_persys_r17.tex')).read(), \
    'Table F1 is no longer in units of 10^%d W' % UNIT_EXP

CAT = ae.catalogue(HERE)
E = ae.per_window(CAT, HERE)                      # ADOPTED: the decorrelation applied (r36, R2-8)
E0 = ae.per_window(CAT, HERE, _decor=False)       # the same limits without it: what v4.35 printed
BEST, _lost = ae.best_by_system(CAT, E)
BEST0, _lost0 = ae.best_by_system(CAT, E0)
MATCH = dc.Matcher(HERE)
SYS = {}
for s, (r, v) in BEST.items():
    o, basis, _hi = MATCH.correction(r)
    f, _b = ae.decor_factor(r, HERE)
    SYS[s] = dict(v=v, o=o, basis=basis, cond=pf.is_cond(s), f=f,
                  before=v / f,                  # the Table F1 row's own window without the correction
                  nom=BEST0[s][1])               # the system's best limit without the correction (re-chosen)

# ---- D1 (r36 restated: the ADOPTED median and deepest are round 103's)
P = {s: d for s, d in SYS.items() if not d['cond']}
if DRIVE == 1:
    P = dict(SYS)
adop = sorted(d['v'] for d in P.values())
nom = sorted(d['nom'] for d in P.values())
ck('D1 the systems are round 103\'s: \\NSysALimSum of them, adopted (corrected) median and deepest as printed',
   len(P) == int(tv('NSysALimSum')) and sci(st.median(adop)) == tv('EirpNinetySysMedA')
   and sci(adop[0]) == tv('EirpNinetySysLoA'),
   '%d systems (%s); median %s (%s)' % (len(P), tv('NSysALimSum'), sci(st.median(adop)), tv('EirpNinetySysMedA')))

# ---- D2 (r36 restated: one-sided, adopted against the limits without the correction)
_n0 = sum(1 for v in nom if v <= 1e15)
_n1 = sum(1 for v in adop if v <= 1e15)
_shift = 100.0 * (st.median(adop) / st.median(nom) - 1.0)
if DRIVE == 2:
    _shift += 1.0
ck('D2 one-sided: adopted >= uncorrected everywhere, median not below, count not raised; sens_r18\'s shift; '
   'the adopted count is \\NSysEfifteen',
   all(d['v'] >= d['nom'] * (1 - 1e-12) for d in P.values()) and st.median(adop) >= st.median(nom)
   and _n1 <= _n0 and '%.1f' % _shift == tv('NmDecAdjShiftPct') and _n1 == int(tv('NSysEfifteen')),
   'median %.4g W uncorrected -> %.4g W adopted (%+.2f %%, sens_r18 %s); count %d -> %d (\\NSysEfifteen %s)'
   % (st.median(nom), st.median(adop), _shift, tv('NmDecAdjShiftPct'), _n0, _n1, tv('NSysEfifteen')))

# ---- D3: the Table F1 clause, over every system the table prints with a limit: the value BEFORE the correction
big = sorted((s for s, d in SYS.items() if d['o'] is not None and d['o'] > BIG), key=lambda s: SYS[s]['v'])
if DRIVE == 3:
    big = big[1:]
_tab = open(os.path.join(HERE, 'tab_persys_r17.tex')).read()
_cells = []
for s in big:
    d = SYS[s]
    nm = sa.designation(s)
    _cells.append('%s %s' % (nm.replace(' ', '~'), two_sf(d['before'] / 10.0 ** UNIT_EXP)))
_dec_in_tab = all(('%.0f' % (100 * SYS[s]['o'])) in _tab and two_sf(SYS[s]['v'] / 10.0 ** UNIT_EXP) in _tab
                  for s in big)
_all_big = sorted(s for s, d in SYS.items() if d['o'] is not None and d['o'] > BIG)
ck('D3 the clause names exactly the Table F1 systems with dec. above a tenth, each at its tabulated limit / (1 + dec.)',
   sorted(big) == _all_big and _dec_in_tab and len(_cells) == len(big) > 0
   and all(abs(SYS[s]['f'] - (1 + SYS[s]['o'])) < 1e-12 for s in big),
   '%d systems: %s' % (len(big), '; '.join(_cells)))

# ---- D4
_none = [s for s, d in P.items() if d['o'] is None]
_keep = all(P[s]['f'] == 1.0 and P[s]['v'] == P[s]['before'] for s in _none)
if DRIVE == 4:
    _keep = False
ck('D4 the system with no decorrelation estimate keeps its value (factor 1), and is in both medians',
   _keep and len(adop) == len(nom), '%s' % [sa.designation(s, tex=False) for s in _none])

# ---- D5 (r36): the alternative for the imputed corrections -- applied to the measured ones only -- lies between
#     the uncorrected and the adopted medians, and the basis counts partition the population
_meas_only = sorted(d['v'] if d['basis'] == 'measured' else d['before'] for d in P.values())
_nb = {b: sum(1 for d in P.values() if d['basis'] == b) for b in ('measured', 'matched', 'none')}
if DRIVE == 5:
    _nb['none'] += 1
ck('D5 measured-only alternative median lies between the uncorrected and adopted ones; bases partition the systems',
   st.median(nom) * (1 - 1e-12) <= st.median(_meas_only) <= st.median(adop) * (1 + 1e-12)
   and sum(_nb.values()) == len(P) and _nb['none'] == len(_none),
   'measured-only median %.4g W; %s' % (st.median(_meas_only), _nb))

WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
m('DcSysMedNom', sci(st.median(nom)))
m('DcNomNEfifteen', '%d' % _n0)
m('DcSysMedMeasOnly', sci(st.median(_meas_only)))
# (the basis counts are r1_r22's \\NgNDec*Sys over the 60 and misc_r35's \\EdDecorNNone; not republished)
# the imputation rule, from decor_r13's own constants (no typed number)
_w = {2.0: 'two', 4.0: 'four'}
m('DcImputedRule', 'the median residual path of the measured blocks within a factor of %s in longest baseline, '
  'widened to a factor of %s where fewer than %s match'
  % (_w.get(dc.BL_MATCH, '%g' % dc.BL_MATCH), _w.get(dc.BL_MATCH ** 2, '%g' % dc.BL_MATCH ** 2),
     WORDS[dc.BL_MATCH_MIN] if dc.BL_MATCH_MIN < len(WORDS) else '%d' % dc.BL_MATCH_MIN))
m('DcNBigTab', '%d' % len(big))
# r34 (fresh read B3): the Table F1 note names the position-conditional systems among these rows, so its count reconciles
# with Sec. 4.1's count over the bounded-position systems
_bigc = [s for s in big if SYS[s]['cond']]
m('DcBigCondClause', ('' if not _bigc else ', the section-marked %s among %s'
                      % (' and '.join(sa.designation(s).replace(' ', '~') for s in _bigc),
                         'it' if len(big) == 1 else 'them')))
m('DcNomClause', ', '.join(_cells[:-1]) + ' and ' + _cells[-1] if len(_cells) > 1 else _cells[0])
m('DcCorrUnit', r'$10^{%d}$\,W' % UNIT_EXP)
_imp = [s for s in big if SYS[s]['basis'] == 'matched']
m('DcNBigTabImputed', '%d' % len(_imp))

if FAIL:
    print('\nFAILED: %s' % '; '.join(FAIL))
    raise SystemExit(1)
if DRIVE is not None:
    print('drive %d did not fire' % DRIVE)
    raise SystemExit(0)
hdr = ['%% GENERATED by decorhl_r34.py (round %d) -- do not hand-edit.' % ROUND,
       '% R2-4 / r36 R2-8: the decorrelation is ADOPTED; the limits without it beside the adopted ones.']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
print('decorhl_r34: %d macros -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
