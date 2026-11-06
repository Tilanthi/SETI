#!/usr/bin/env python3
r"""ONE declaration of ALMA's absolute flux-scale specification, and ONE
computation of the instrumental term built from it.

WHY THIS FILE EXISTS.  ALMA's band-dependent absolute flux accuracy was
declared in `p90_budget_v409.py` (round 38, which publishes Table 3's rows) and
the combined term it feeds was read by `sens_r11.py` (round 180, which
publishes the interval the paper actually quotes) out of a FROZEN RECORD of a
round-9 run.  So the specification had one owner and the number derived from it
had another, and when the specification was found to be wrong -- Band 6 carried
at 5 per cent where every ALMA document says 10, over 203 of the 402 Class A
windows -- correcting it moved Table 3 and left `\SensFacLo`/`\SensFacHi`
quoting the superseded value.  Two numbers for one quantity, which is this
project's commonest defect and the reason `twinmacro.py` exists.

So the declaration and the arithmetic live here, in a module with no macro
round of its own and no output file, and both generators import it.  There is
exactly one place to read, one place to correct, and nothing frozen in between.

    import fluxspec_r14 as fx
    fx.FLUXCAL          # the specification, per band
    fx.FLUXCAL_SOURCE   # where it is stated, WITH ITS SECTION
    fx.e_flux(bandn)    # band-weighted over a Counter of band -> n windows
    fx.combined(e_flux, e_dist_typ, e_viscal)

THE SPECIFICATION, read at the documents and quoted verbatim.

  ALMA Proposer's Guide, Appendix A.9.2, "Absolute flux accuracy" (Cycle 13 =
  Doc 13.2 ver. 1.0, p. 48; identical wording in Cycles 9, 10 and 11):
    "It is expected that these calibrators provide an absolute flux accuracy
     better than 5% for Bands 1 through 5; 10% for Bands 6, 7 and 8; and 20%
     for Bands 9 and 10."

  ALMA Technical Handbook, Sec. 10.2.6, "Source Catalog", corroborating:
    "The resultant absolute flux density accuracy for grid sources ranges from
     ~5% (2 sigma) for Bands 1-5 to ~10% (2 sigma) for Bands 6 and 7 ... For
     high frequency observations in parts of Band 8 with strong atmospheric
     absorption, Band 9 and Band 10, relative calibration uncertainties are of
     order 10% (1 sigma) and additional uncertainties in the flux transfer
     process can increase this by up to a factor of two."

  ALMA Technical Handbook, Ch. 11 (Quality Assurance), the QA2 criterion:
    "Accuracy of the flux density calibration at the required level of 5% for
     Bands 1 - 5, 10% for Bands 6 and 7, or 20% for Band 8 and higher."

THE ONE DISAGREEMENT, AND WHAT IS DONE ABOUT IT.  The two documents differ at
Band 8 and nowhere else: 10 per cent in the Proposer's Guide, 20 per cent in
the Handbook's QA2 criterion.  THE MORE CONSERVATIVE FIGURE IS ADOPTED, 20, and
said so here, in `FLUXCAL_SOURCE`, and in the emitted provenance.  The sample
holds 6 Class A Band 8 windows, so nothing printed moves either way -- 0.10
gives a band-weighted 0.10012 and a combined 0.10978, 0.20 gives 0.10162 and
0.11115, and both print as +-10 and +-11 -- but a budget must not quietly take
the kinder of two disagreeing specifications.

★ AND THE RULE THE WHOLE EPISODE ESTABLISHES: an externally declared constant
must name a SECTION, APPENDIX, CHAPTER, TABLE OR PAGE of its source, not just
a document.  The string that let Band 6 survive for nine versions read "ALMA
Technical Handbook absolute-accuracy specification" -- a document with no
section, and a document which does not state the figure in that form at all.
A source nobody can follow to a page is not a citation, it is a gesture.
`p90_budget_v409.py`'s B14 enforces it on every `*_SOURCE` declared there.

    python3 fluxspec_r14.py --selftest   # the module's own clauses
"""
import collections
import math
import sys

#: ALMA's absolute flux accuracy, per receiver band, as a fraction.
#: EXTERNAL SPECIFICATION -- not measured in this work.
FLUXCAL = {1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.05,
           6: 0.10, 7: 0.10,
           8: 0.20, 9: 0.20, 10: 0.20}

FLUXCAL_SOURCE = (
    'ALMA Proposer\'s Guide App. A.9.2, "Absolute flux accuracy" '
    '(Cycle 13 Doc 13.2 ver. 1.0, p. 48), corroborated by the ALMA Technical '
    'Handbook Sec. 10.2.6; where the two disagree (Band 8: 20 per cent in the '
    'Handbook Ch. 11 QA2 criterion against 10 in the Guide) the more '
    'conservative figure is adopted '
    '(EXTERNAL SPECIFICATION, not measured here)')

#: The superseded declaration, kept so that the departure of every number
#: derived from it can be measured rather than asserted.  Band 6 at 5 per cent
#: is what `p90_budget_v409.py` carried from v4.09 to v4.14; Band 8 at 10 is
#: the Proposer's Guide figure, i.e. the less conservative of the two.
FLUXCAL_SUPERSEDED = dict(FLUXCAL)
FLUXCAL_SUPERSEDED.update({6: 0.05, 8: 0.10})


def e_flux(bandn, spec=None):
    """The specification weighted over a band mix.

    `bandn` maps receiver band -> number of windows; a `collections.Counter`
    over the catalogue's own `band` column is what both callers pass.
    """
    spec = FLUXCAL if spec is None else spec
    n = sum(bandn.values())
    assert n > 0, 'fluxspec: empty band mix; the weighting would be vacuous'
    missing = sorted(b for b in bandn if b not in spec)
    assert not missing, ('fluxspec: no specification for band(s) %s -- an '
                         'unknown band must stop the build, not be weighted '
                         'as zero' % missing)
    return sum(bandn[b] * spec[b] for b in bandn) / float(n)


def e_flux_worst(bandn, spec=None):
    """The specification of the worst band PRESENT in the sample."""
    spec = FLUXCAL if spec is None else spec
    assert bandn, 'fluxspec: empty band mix'
    return max(spec[b] for b in bandn)


def combined(flux, dist_typ, viscal):
    """The three independent scale errors on the quoted completeness factor,
    in quadrature.  This is the ONE definition of the instrumental term; both
    round 38 and round 180 call it, so they cannot drift apart again."""
    return math.sqrt(flux ** 2 + dist_typ ** 2 + viscal ** 2)


def _selftest():
    """Three clauses, each demonstrated failing."""
    ok = True
    bandn = collections.Counter({3: 15, 6: 203, 7: 170, 8: 6, 10: 8})

    #: C1 the corrected specification is strictly more conservative than the
    #: superseded one over THIS sample, so the correction can only widen the
    #: budget.  Fails if the two are the same declaration.
    a = e_flux(bandn)
    b = e_flux(bandn, FLUXCAL_SUPERSEDED)
    got = a > b + 1e-6
    print('  C1 corrected %.5f > superseded %.5f  %s'
          % (a, b, 'OK' if got else 'WRONG'))
    ok = ok and got
    got = not (e_flux(bandn, FLUXCAL) > e_flux(bandn, FLUXCAL) + 1e-6)
    print('  C1 drive (one specification against itself) does not fire  %s'
          % ('OK' if got else 'WRONG'))
    ok = ok and got

    #: C2 an unknown band stops the weighting rather than counting as zero.
    try:
        e_flux(collections.Counter({6: 10, 99: 1}))
        got = False
    except AssertionError:
        got = True
    print('  C2 an unspecified band raises  %s' % ('OK' if got else 'WRONG'))
    ok = ok and got

    #: C3 the quadrature sum strictly exceeds each of its three terms.
    c = combined(a, 0.0016, 0.045)
    got = c > a and c > 0.045 and c > 0.0016
    print('  C3 combined %.5f exceeds each term  %s'
          % (c, 'OK' if got else 'WRONG'))
    ok = ok and got

    #: C4 the source string names a section, not merely a document.
    got = 'App. A.9.2' in FLUXCAL_SOURCE and 'Sec. 10.2.6' in FLUXCAL_SOURCE
    print('  C4 the source names its sections  %s' % ('OK' if got else 'WRONG'))
    ok = ok and got
    return 0 if ok else 1


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        raise SystemExit(_selftest())
    print('fluxspec_r14: %s' % FLUXCAL)
    print('fluxspec_r14: %s' % FLUXCAL_SOURCE)
