#!/usr/bin/env python3
"""Reference implementation of the attribution mask.

    python3 line_mask.py                                      # known answers
    python3 line_mask.py --check ../candidates/threshold_crossings.csv \\
                         ../candidates/molecular_line_matches.csv

THIS IS NOT THE SURVEY PIPELINE.  It is a short, self-contained
implementation of the published rule, written so that the rule can be read,
run and checked against the deposited tables.

THE RULE.  A threshold crossing is attributed to a catalogued transition when
its frequency IN THE STAR'S REST FRAME lies within the adopted half-width of
that transition's rest frequency.  The half-width is a velocity, so its width
in frequency scales with the transition:

    dv = c (nu_star - nu_0) / nu_0        attributed if |dv| <= dv_mask

with dv positive where the crossing lies ABOVE the transition in frequency.
The transitions are the ones deposited in molecular_line_matches.csv, and the
adopted half-width travels with each of them in that file.

FOUR THINGS THE RULE IS NOT, each of which has been read into it before:

  * It is not a detection of the transition.  A coincidence in frequency says
    the crossing is consistent with a line, and nothing more; the article
    distinguishes coincidences with corroborating evidence from coincidences
    without it, and this code decides only the coincidence.
  * It is not symmetric with a topocentric test.  The frame matters: the same
    crossing can be inside the mask in the star's frame and outside it in the
    frame the correlator delivered.  The CONTROL side of the chance
    comparison is screened in the same stellar frame, which is what makes the
    two sides comparable.
  * It is not the atmospheric screen.  That screen is topocentric, has its
    own radius, and is applied to both sides separately; it is flagged in its
    own columns in the crossing table.
  * It is not a bandwidth statement.  The width this rule costs the survey is
    the sum of the masked intervals inside the searched islands, which is in
    frequency_coverage.csv and is not the same thing as the number of
    crossings it accounts for.
"""
import argparse
import csv
import os

C_KMS = 299792.458


def dv_kms(nu_star_GHz, nu_rest_GHz):
    """Stellar-frame offset of a crossing from a transition, in km/s,
    positive where the crossing lies above the transition in frequency."""
    return C_KMS * (nu_star_GHz - nu_rest_GHz) / nu_rest_GHz


def mask_interval(nu_rest_GHz, dv_mask_kms):
    """The masked frequency interval about one transition."""
    return (nu_rest_GHz * (1.0 - dv_mask_kms / C_KMS),
            nu_rest_GHz * (1.0 + dv_mask_kms / C_KMS))


def nearest(nu_star_GHz, transitions):
    """The transition of the list nearest in velocity, and that offset.

    transitions is a sequence of (label, nu_rest_GHz, dv_mask_kms).
    Returns (label, nu_rest_GHz, dv, inside_mask).
    """
    best = None
    for label, nu0, dvm in transitions:
        d = dv_kms(nu_star_GHz, nu0)
        if best is None or abs(d) < abs(best[2]):
            best = (label, nu0, d, abs(d) <= dvm)
    return best


def attributed(nu_star_GHz, transitions):
    """Whether the crossing falls inside the mask of any transition."""
    return any(abs(dv_kms(nu_star_GHz, nu0)) <= dvm
               for _, nu0, dvm in transitions)


# --------------------------------------------------------------- known answers
def _kat():
    T = [('CO(2-1)', 230.538000, 50.0), ('CO(3-2)', 345.795990, 50.0)]

    # (1) a crossing exactly on a transition has zero offset and is attributed
    assert abs(dv_kms(230.538000, 230.538000)) < 1e-12
    assert attributed(230.538000, T)

    # (2) the sign convention: above the transition in frequency is positive
    assert dv_kms(230.600000, 230.538000) > 0
    assert dv_kms(230.500000, 230.538000) < 0

    # (3) the mask edge is the half-width: just inside is attributed, just
    # outside is not.  The edge itself is a floating-point coin toss and no
    # crossing in the survey lies within a part in a million of it.
    lo, hi = mask_interval(230.538000, 50.0)
    assert attributed(hi * (1 - 1e-9), T) and attributed(lo * (1 + 1e-9), T)
    assert not attributed(hi * (1 + 1e-6), T)
    assert not attributed(lo * (1 - 1e-6), T)

    # (4) the mask is a VELOCITY, so it is wider in frequency at a higher
    # transition.  A fixed frequency radius would mask a different velocity
    # range in every band, which is what the rule avoids.
    w2 = mask_interval(230.538000, 50.0)
    w3 = mask_interval(345.795990, 50.0)
    assert (w3[1] - w3[0]) > 1.4 * (w2[1] - w2[0])

    # (5) nearest returns the nearer of two transitions in VELOCITY, which
    # between bands is not the nearer in frequency
    label, nu0, dv, inside = nearest(345.700000, T)
    assert label == 'CO(3-2)', label
    assert not inside and dv < 0, (dv, inside)

    # (6) a crossing far from every transition is attributed to none, and
    # nearest still names the nearest one.  Being far from a MASKED line is
    # not evidence of being far from every line: the list decides the answer.
    label, nu0, dv, inside = nearest(300.000000, T)
    assert not inside and not attributed(300.000000, T)
    print('line_mask: 6 known-answer tests pass')


def _check(crossings_csv, lines_csv):
    #: ★★★★ THE QUERY IS NOT THE MASK, AND THIS FILE USED TO TAKE IT
    #: FOR ONE.  `molecular_line_matches.csv` deposits the whole dated
    #: catalogue query, because a line list that cannot be inspected cannot
    #: be audited; the attribution MASK is the subset its `in_mask` column
    #: marks.  Built from every row, the rule below attributed 21 crossings
    #: where the deposited flag is set on 18, and this check PRINTED that
    #: divergence and returned success -- a check that reports the defect
    #: inside a PASS, which is worse than no check, because it makes the
    #: inconsistency look sanctioned.  The mask now drives the rule, the
    #: equality with the deposited flag is ASSERTED, and the query is kept
    #: beside it so the difference can be shown to be exactly the excluded
    #: species rather than merely asserted to be.
    with open(lines_csv) as fh:
        _L = list(csv.DictReader(fh))
    assert _L and 'in_mask' in _L[0], (
        'molecular_line_matches.csv carries no in_mask column, so the mask '
        'cannot be separated from the query and every count below would be '
        'the query\'s')
    T = [(r['transition'], float(r['nu_rest_GHz']),
          float(r['mask_half_width_kms']))
         for r in _L if r['in_mask'] == '1']
    Q = [(r['transition'], float(r['nu_rest_GHz']),
          float(r['mask_half_width_kms']) if r['mask_half_width_kms']
          else max(float(x['mask_half_width_kms']) for x in _L
                   if x['mask_half_width_kms']))
         for r in _L]
    assert T and len(T) < len(Q), (
        'the mask is not a proper subset of the query (%d of %d), so the '
        'comparison below is vacuous' % (len(T), len(Q)))
    n = agree = 0
    worst = 0.0
    disagree = []
    with open(crossings_csv) as fh:
        for r in csv.DictReader(fh):
            if not r['masked_transition']:
                continue
            n += 1
            label, nu0, dv, inside = nearest(float(r['nu_star_GHz']), T)
            if r['masked_dv_kms']:
                worst = max(worst, abs(dv - float(r['masked_dv_kms'])))
            if label == r['masked_transition']:
                agree += 1
            else:
                disagree.append((r['star'], r['nu_topo_GHz'],
                                 r['masked_transition'], label))
    print('line_mask: %d deposited crossings carry a nearest masked '
          'transition; this rule names the same one on %d of them, and '
          'reproduces the deposited offset to %.4f km/s'
          % (n, agree, worst))
    for d in disagree:
        print('   differs: %s %s GHz deposited %s, rule gives %s' % d)
    #: ★ THE TWO COUNTS DIFFER, AND THE DIFFERENCE IS NOT A DISAGREEMENT.
    #: `molecular_line_matches.csv` deposits the WHOLE dated query, because a
    #: list that cannot be inspected cannot be audited.  The attribution MASK
    #: is that query less the species the article names as deliberately left
    #: out -- sulphur monoxide, which has no reported detection in a debris
    #: disc, so masking it would have declared no constraint over bandwidth
    #: this survey does constrain.  Run over the deposited list this rule
    #: therefore attributes more crossings than the deposited flag marks, and
    #: the extra ones are exactly the rows whose nearest transition is of a
    #: left-out species; they are counted and named here rather than left for
    #: a reader to discover as an inconsistency.  Each is reported in the
    #: article as an unattributed crossing with its offset printed beside it.
    _rows = list(csv.DictReader(open(crossings_csv)))
    _byrule = [r for r in _rows if attributed(float(r['nu_star_GHz']), T)]
    _byflag = [r for r in _rows if r['attributed'] == '1']
    _byquery = [r for r in _rows if attributed(float(r['nu_star_GHz']), Q)]
    _extra = [r for r in _byquery if r not in _byrule]
    _sp = sorted({nearest(float(r['nu_star_GHz']), Q)[0].split('(')[0]
                  for r in _extra})
    _excl = sorted({r['mask_exclusion_reason'].split(':')[0]
                    for r in _L if r['in_mask'] != '1'
                    and r.get('mask_exclusion_reason')})
    print('line_mask: the mask (%d of the %d deposited transitions) '
          'attributes %d crossings, and the deposited attributed flag is set '
          'on %d' % (len(T), len(Q), len(_byrule), len(_byflag)))
    #: ★★★ THE EQUALITY, ASSERTED.  This is the clause that must go red if
    #: a deposit is ever built from a line list the article does not use.
    assert len(_byrule) == len(_byflag), (
        'the mask attributes %d crossings and the deposited flag is set on '
        '%d: the deposited line list and the article do not agree about '
        'which transitions the mask holds'
        % (len(_byrule), len(_byflag)))
    assert all(r in _byrule for r in _byflag) \
        and all(r in _byflag for r in _byrule), (
        'the mask and the deposited flag attribute the same NUMBER of '
        'crossings and not the same crossings')
    print('line_mask: applying the same rule to the whole query instead '
          'attributes %d, the %d extra being those nearest a transition of a '
          'species the mask leaves out (%s%s); the article reports each as '
          'unattributed with its offset'
          % (len(_byquery), len(_extra), ', '.join(_sp) or 'none',
             '' if not _excl else '; excluded for: %s' % ', '.join(_excl)))
    assert all(nearest(float(r['nu_star_GHz']), Q)[0].split('(')[0]
               not in {t[0].split('(')[0] for t in T} for r in _extra), (
        'a crossing attributed by the query and not by the mask is nearest a '
        'transition of a species the mask DOES hold, which would make the '
        'difference something other than the excluded species')
    assert all(r in _byquery for r in _byrule), (
        'the mask attributes a crossing the whole query does not, which is '
        'impossible: the mask is a subset of the query')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', nargs=2,
                    metavar=('THRESHOLD_CROSSINGS_CSV',
                             'MOLECULAR_LINE_MATCHES_CSV'))
    a = ap.parse_args()
    _kat()
    if a.check:
        _check(os.path.abspath(a.check[0]), os.path.abspath(a.check[1]))
