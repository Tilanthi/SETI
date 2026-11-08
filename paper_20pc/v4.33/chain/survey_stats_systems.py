#!/usr/bin/env python3
"""The paper's system grouping, in one place.

Extracted from survey_stats.py at v3.81 so the pre-registered hold-out's
second guard -- no system may lose every block -- groups systems by exactly
the rule the headline counts use. Two definitions of "system" would make the
guard protect something the paper does not report.
"""

PAIRS=[('2MASS J05241914-1601153 551040','2MASS J05241914-1601153 717696'),
       ('NAME AT Mic AB  Gaia DR3 6792436799475128960','V AT Mic B'),
       ('G 272-61A','G 272-61B'),('GJ 2006A','GJ 2006B'),
       ('LP 476-207 384128','LP 476-207 783296'),('V star TX PsA','V star WW PsA'),
       # v3.46 (referee A1): HD 139084B appears under two catalogue entries with
       # identical EB, spectral windows and on-source times but different
       # system ids and distances (39.31 / 38.72 pc).  It is one system.
       # v4.07: those two entries are the two COMPONENTS of V343 Nor, 10.3"
       # apart, and one of them was misnamed -- see censusfix_v407.py.  Still
       # one system, now written under the repaired names as well as the two
       # strings the frozen export carries, so both spellings collapse to the
       # same unit whichever export a caller was handed.
       ('HD 139084','HD 139084B'),
       ('HD 139084','HD 139084B 805632'),
       ('HD 139084','HD 139084B 921024')]

_sysof = {}
for _a, _b in PAIRS:
    _sysof[_a] = _a
    _sysof[_b] = _a


def system_of(star_name):
    return _sysof.get(star_name, star_name)
