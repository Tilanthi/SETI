#!/usr/bin/env python3
"""Half-up rounding for typeset p-values and fractions (v4.06).

`'%.2f' % 0.145` gives **0.14**, not 0.15, because 0.145 has no exact binary
representation and the nearest double is just below it -- and because C's
printf then rounds half to EVEN anyway.  A Monte-Carlo tail of 58 draws in 400
is exactly 0.145 and must print as 0.15, or the paper reports a p-value smaller
than the one it measured.  The same trap bites every exact-tenth-and-a-half
fraction a counting experiment can produce: 1/8 at three places, 29/200 at two,
7/40 at two.

`freqocc_v405.py` fixed this locally at v4.05 with a private `pct2`; it is
shared here so every generator that prints a counted fraction uses the same
rule, and so `selftest_v406.py` can drive it in both directions.
"""
import decimal
from fractions import Fraction

__all__ = ['half_up', 'naive']


def half_up(p, nd=2):
    """Format `p` to `nd` decimal places, rounding a tie AWAY FROM ZERO.

    `p` may be a float, a Fraction or a (numerator, denominator) pair.  Passing
    the pair is the safest form: it rounds the exact rational rather than the
    double nearest to it, so 58/400 is a tie and is resolved upwards.
    """
    if isinstance(p, tuple):
        num, den = p
        d = decimal.Decimal(num) / decimal.Decimal(den)
    elif isinstance(p, Fraction):
        d = decimal.Decimal(p.numerator) / decimal.Decimal(p.denominator)
    else:
        d = decimal.Decimal(repr(p))
    q = decimal.Decimal(1).scaleb(-nd)
    with decimal.localcontext() as ctx:
        ctx.prec = 40
        return str(d.quantize(q, rounding=decimal.ROUND_HALF_UP))


def naive(p, nd=2):
    """What `'%.*f'` does, kept so the difference can be demonstrated rather
    than asserted."""
    return '%.*f' % (nd, float(p))


if __name__ == '__main__':
    # Drive it in BOTH directions: the naive form must be shown to be wrong on
    # a case the survey can actually produce, and right where there is no tie.
    CASES = [((58, 400), 2, '0.15', '0.14'),      # freqocc's measured tail
             ((1, 8), 2, '0.13', '0.12'),         # 0.125, ties to even
             ((7, 40), 2, '0.18', '0.17'),        # 0.175
             ((29, 200), 2, '0.15', '0.14'),      # 0.145
             ((3, 8), 3, '0.375', '0.375')]       # no tie: both agree
    bad = []
    for frac, nd, want, naive_want in CASES:
        got, ng = half_up(frac, nd), naive(Fraction(*frac), nd)
        if got != want or ng != naive_want:
            bad.append((frac, nd, got, want, ng, naive_want))
    assert not bad, bad
    # And the failure must be REAL, not asserted: at least one case must
    # disagree, or this module is solving nothing.
    assert any(half_up(f, n) != naive(Fraction(*f), n) for f, n, _, _ in
               [(c[0], c[1], c[2], c[3]) for c in CASES]), 'no case differs'
    print('numfmt_v406: %d cases, %d where half-up differs from printf'
          % (len(CASES), sum(1 for f, n, _, _, _ in
                             [(c[0], c[1], 0, 0, 0) for c in CASES]
                             if half_up(f, n) != naive(Fraction(*f), n))))
    for frac, nd, want, naive_want in CASES:
        print('  %d/%-4d at %d places: half-up %s, printf %s%s'
              % (frac[0], frac[1], nd, half_up(frac, nd),
                 naive(Fraction(*frac), nd),
                 '   <-- WRONG' if want != naive_want else ''))
