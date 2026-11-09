#!/usr/bin/env python3
r"""decorhl_r34.py -- round 3401.  ROUND 34, R2-4: THE HEADLINE BOTH WAYS, NOMINAL AND WITH THE
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
    python3 decorhl_r34.py --drive N    # N = 1..4: prints FAILED: D<N>, writes nothing, exits 1

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
E = ae.per_window(CAT, HERE)
BEST, _lost = ae.best_by_system(CAT, E)
MATCH = dc.Matcher(HERE)
SYS = {}
for s, (r, v) in BEST.items():
    o, basis, _hi = MATCH.correction(r)
    SYS[s] = dict(v=v, o=o, basis=basis, cond=pf.is_cond(s),
                  corr=v * (1.0 + o) if o is not None else v)

# ---- D1
P = {s: d for s, d in SYS.items() if not d['cond']}
if DRIVE == 1:
    P = dict(SYS)
nom = sorted(d['v'] for d in P.values())
cor = sorted(d['corr'] for d in P.values())
ck('D1 the systems are round 103\'s: \\NSysALimSum of them, nominal median and deepest as printed',
   len(P) == int(tv('NSysALimSum')) and sci(st.median(nom)) == tv('EirpNinetySysMedA')
   and sci(nom[0]) == tv('EirpNinetySysLoA'),
   '%d systems (%s); median %s (%s)' % (len(P), tv('NSysALimSum'), sci(st.median(nom)), tv('EirpNinetySysMedA')))

# ---- D2
_n0 = sum(1 for v in nom if v <= 1e15)
_n1 = sum(1 for v in cor if v <= 1e15)
_shift = 100.0 * (st.median(cor) / st.median(nom) - 1.0)
if DRIVE == 2:
    _shift += 1.0
ck('D2 one-sided: corrected >= nominal everywhere, median above, count not raised; sens_r18\'s shift and count',
   all(d['corr'] >= d['v'] for d in P.values()) and st.median(cor) > st.median(nom) and _n1 <= _n0
   and '%.1f' % _shift == tv('NmDecAdjShiftPct') and _n1 == int(tv('NmDecAdjNEfifteen')),
   'median %.4g -> %.4g W (%+.2f %%, sens_r18 %s); count %d -> %d (sens_r18 %s)'
   % (st.median(nom), st.median(cor), _shift, tv('NmDecAdjShiftPct'), _n0, _n1, tv('NmDecAdjNEfifteen')))

# ---- D3: the Table F1 clause, over every system the table prints with a limit
big = sorted((s for s, d in SYS.items() if d['o'] is not None and d['o'] > BIG), key=lambda s: SYS[s]['v'])
if DRIVE == 3:
    big = big[1:]
_tab = open(os.path.join(HERE, 'tab_persys_r17.tex')).read()
_cells = []
for s in big:
    d = SYS[s]
    nm = sa.designation(s)
    _cells.append('%s %s' % (nm.replace(' ', '~'), two_sf(d['corr'] / 10.0 ** UNIT_EXP)))
_dec_in_tab = all(('%.0f' % (100 * SYS[s]['o'])) in _tab for s in big)
_all_big = sorted(s for s, d in SYS.items() if d['o'] is not None and d['o'] > BIG)
ck('D3 the clause names exactly the Table F1 systems with dec. above a tenth, each at limit x (1 + dec.)',
   sorted(big) == _all_big and _dec_in_tab and len(_cells) == len(big) > 0,
   '%d systems: %s' % (len(big), '; '.join(_cells)))

# ---- D4
_none = [s for s, d in P.items() if d['o'] is None]
_keep = all(P[s]['corr'] == P[s]['v'] for s in _none)
if DRIVE == 4:
    _keep = False
ck('D4 the system with no decorrelation estimate keeps its nominal value, in both medians',
   _keep and len(cor) == len(nom), '%s' % [sa.designation(s, tex=False) for s in _none])

m('DcSysMedCorr', sci(st.median(cor)))
m('DcNBigTab', '%d' % len(big))
# r34 (fresh read B3): the Table F1 note names the position-conditional systems among these rows, so its count reconciles
# with Sec. 4.1's count over the bounded-position systems
_bigc = [s for s in big if SYS[s]['cond']]
m('DcBigCondClause', ('' if not _bigc else ', the section-marked %s among %s'
                      % (' and '.join(sa.designation(s).replace(' ', '~') for s in _bigc),
                         'it' if len(big) == 1 else 'them')))
m('DcCorrClause', ', '.join(_cells[:-1]) + ' and ' + _cells[-1] if len(_cells) > 1 else _cells[0])
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
       '% R2-4: the headline with the atmospheric decorrelation divided out (nominal stays adopted).']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
print('decorhl_r34: %d macros -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
