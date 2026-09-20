#!/usr/bin/env python3
r"""The adopted systemic velocity of beta Pictoris, single-sourced.

Why this file exists
--------------------
Through v3.46 two generators carried two different values three paragraphs
apart in the rendered paper: round10_calc.py used VSYS_BPIC = 16.84 km/s for
the stellar-frame column of tab:bpicaudit, while v346_calc.py used 20.0 km/s
for the barycentric concordance of the recurrence blocks.  All three v3.47
referees found the contradiction independently.  The two generators now import
the value from here, so it cannot diverge again.

Which value, and why
--------------------
SIMBAD returns +16.84 km/s for beta Pic, sourced to Gaia DR3.  That is a
faithful catalogue value but it is the wrong one to adopt for a kinematic
argument about this star.  Beta Pic is A6V with v sin i ~ 130 km/s and
T_eff ~ 8000 K, inside the hot-star template regime for which Gaia DR3 radial
velocities carry a documented template-mismatch systematic (Blomme et al. 2023,
A&A 674, A7; mitigation described in Katz et al. 2023, A&A 674, A5).  DR3 is
the first release to publish radial velocities for templates in
T_eff = 7000-14500 K at all.

The gas-derived value in general use for this system is +20 km/s: Matra et al.
(2017, MNRAS 464, 1415), the CO J=2-1 analysis this paper cites for the beta Pic
gas, integrate their moment-0 maps over heliocentric velocities 14 to 26 km/s,
i.e. +-6 km/s in the frame of the star, which is an adopted systemic velocity of
20.0 km/s.

This is also what this paper's own data say.  The four blocks with a recorded
epoch put the barycentric CO peak at +19.6, +20.2, +20.4 and +20.7 km/s across
two transitions; their mean is +20.2 km/s.  Adopting 20.0 moves the three
stellar-frame offsets of tab:bpicaudit from -2.72/-3.45/-3.62 to
+0.44/-0.29/-0.46 km/s, so the correction strengthens the attribution rather
than weakening it.

The uncertainty is the literature figure and is the same size as the spread of
the measurements being compared against it, which is the honest way to quote it.
"""

VSYS_BPIC_KMS = 20.0        # km/s, heliocentric/barycentric systemic
VSYS_BPIC_ERR_KMS = 0.7     # km/s

__all__ = ['VSYS_BPIC_KMS', 'VSYS_BPIC_ERR_KMS']
