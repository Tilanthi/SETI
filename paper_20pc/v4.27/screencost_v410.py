#!/usr/bin/env python3
"""RETIRED at v4.12 by Ruling 1.  Superseded by sens_r11.py (round 180).

This generator published what the 512-position spatial screen COSTS the
completeness: x1.44 overall, x1.15 where the control ring is noise, and a
bound in the four windows whose rings carry resolved disc emission.  Every one
of those numbers presupposes that the screen is charged against the limit --
that is, that it gates a disposition.  It does not: every unattributed
crossing goes to the recurrence test whatever its rank, so the rank annotates
a crossing rather than disposing of it, and the completeness is measured
through trigger plus localisation alone.

Two consequences, both measured rather than argued:

  * all nine of this generator's macros are unreferenced by the manuscript,
    because the two-stratum construction and the screen-cost arithmetic left
    the paper with the charge;
  * its own clause S7 -- "the adopted multiplier in the macro layer is the one
    this cost is computed against" -- became FALSE BY DESIGN the moment the
    adopted multiplier stopped being the rank-charged one.  It failed the
    build reporting `macro layer 3.03 against frozen 4.4152`, which is the
    gate correctly refusing to publish a cost against a criterion the paper
    no longer adopts.

The quantity that survives is the LIKE-FOR-LIKE rank cost, measured by
`sens_r11.py` over the same injected windows as the completeness itself and
cited once, in Sec. 5.1, as \\SensCostLike.  One campaign, one number.

It fails loudly instead of rewriting its macro file, because a build that
stops is better than a macro layer nothing typesets.  The original is kept
verbatim at retired/screencost_v410.py for provenance.

  make_all.sh: the line is deleted, not replaced.
  manuscript:  the round-105 \\input is deleted.
"""
import sys

sys.exit('screencost_v410.py is RETIRED at v4.12 (Ruling 1): the spatial rank '
         'gates no disposition, so there is no screen cost to charge.  The '
         'like-for-like rank cost is sens_r11.py\'s.  See this docstring.')
