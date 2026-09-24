#!/usr/bin/env python3
"""Star-name canonicalisation and bound-pair systems, in one place.

Three separate defects all reduce to the same thing -- one object reaching
the export under more than one string -- and each was invisible because
several generators carried their own copy of the map and were all wrong
together:

  * four stars appear under two punctuations of the same designation
    (SIMBAD's name route and its position route disagree, and two entries
    carry a leading "* "), which made 94 stars of 90 and 87 systems of 83
    and reached the paper's title;
  * TWA 3A reaches the export as two Gaia components, 37.05 and 37.13 pc,
    and was in no bound pair, so it counted as two systems;
  * one entry carries the ALMA field name rather than the star's: the
    field of `j1256-1257` contains LP 736-15, whose Gaia parallax of
    47.27 mas is the 21.154 pc the catalogue already records.

The defence against a recurrence is an identity, not vigilance: no two
systems may share a distance, asserted in v342_calc.py, and the star and
system counts are re-derived from the released catalogue by
reproduce_from_catalogue_v385.py.
"""
#: name strings that denote the same star under different punctuation
ALIAS = {
    'HD 207129 (Gaia DR3 6564091190988411520)':
        'HD 207129 Gaia DR3 6564091190988411520',
    'HD53143 (Gaia DR3 5479222240596469632)':
        'HD53143 Gaia DR3 5479222240596469632',
    '* g Lup': 'HD 139664',
    '* eta Crv': 'eta Crv',
}

#: designation repairs applied on release
NAME_REPAIR = {
    'LSR J18353259': 'LSR J1835+3259',
    'PM J034331958': 'PM J03433+1958',
    'WD 0407179':    'WD 0407+179',
    'BD05  1668':    'BD+05 1668',
    'j1256-1257':    'LP 736-15',
}

#: physically bound pairs sharing one statistical unit. Each member has
#: its own Gaia parallax, so these are components and not duplicate
#: strings: LP 476-207 at 23.7525 and 23.7875 pc, HD 139084B at 38.72 and
#: 39.31, 2MASS J05241914 at 30.99 and 31.19, TWA 3A at 37.05 and 37.13.
#: TWA 3A was missing from this list until v3.85 and counted as two
#: systems.
PAIRS = [('2MASS J05241914-1601153 551040', '2MASS J05241914-1601153 717696'),
         ('NAME AT Mic AB Gaia DR3 6792436799475128960', 'V AT Mic B'),
         ('G 272-61A', 'G 272-61B'),
         ('GJ 2006A', 'GJ 2006B'),
         ('LP 476-207 384128', 'LP 476-207 783296'),
         ('V star TX PsA', 'V star WW PsA'),
         ('HD 139084B 805632', 'HD 139084B 921024'),
         ('TWA 3A 696000', 'TWA 3A [576064]')]


def _squash(n):
    return ' '.join(str(n).split())


def canon(n):
    """The star: whitespace collapsed, target-id suffix removed, aliases
    merged."""
    n = _squash(n)
    return ALIAS.get(n, n)


_SYSOF = {}
for _a, _b in PAIRS:
    _SYSOF[_squash(_a)] = _squash(_a)
    _SYSOF[_squash(_b)] = _squash(_a)


def sysname(n):
    """The statistical unit: canonical star, then collapsed onto its pair."""
    n = canon(n)
    return _SYSOF.get(n, n)


def released(n):
    """The designation as released."""
    n = canon(n)
    return _squash(NAME_REPAIR.get(n, n))


if __name__ == '__main__':
    import csv, collections, sys
    R = list(csv.DictReader(open('per_target_results_v3.98.csv')))
    st = {released(r['star_name']) for r in R}
    sy = {sysname(r['star_name']) for r in R}
    print('stars %d, systems %d, star-bands %d'
          % (len(st), len(sy),
             len({(canon(r['star_name']), r['band']) for r in R})))
    d = collections.defaultdict(set)
    for r in R:
        d[round(float(r['dist_pc']), 2)].add(sysname(r['star_name']))
    bad = {k: v for k, v in d.items() if len(v) > 1}
    print('distances shared by two systems:', bad or 'none')


#: Suffixes appended by the target-resolution step that are not part of any
#: catalogue designation. They must be stripped for display but NOT for
#: identity, because PAIRS distinguishes components by exactly these digits.
_DISPLAY_SUFFIX = ('696000', '805632', '384128', '783296', '921024',
                   '717696', '551040', '576064', '[576064]')

#: Designations whose case is mangled in the export.
_DISPLAY_CASE = {
    'hd92945': 'HD 92945',
    'j1256-1257': 'LP 736-15',
    'Barta 161 12': 'Barta 161 12',
}


def display(n):
    """Printable designation: repairs applied, target-id suffix removed,
    case normalised. Use for figure labels and table rows only -- `canon`
    remains the identity function, since PAIRS relies on the suffixes."""
    raw = str(n)
    # NAME_REPAIR keys carry the export's own (sometimes doubled) spacing,
    # so try the raw string before the squashed one
    n = NAME_REPAIR.get(raw, NAME_REPAIR.get(_squash(raw), raw))
    n = _squash(n)
    for suf in _DISPLAY_SUFFIX:
        if n.endswith(' ' + suf):
            n = n[: -(len(suf) + 1)].strip()
    if n in _DISPLAY_CASE:
        return _DISPLAY_CASE[n]
    if n.lower().startswith('hd') and not n.startswith('HD'):
        rest = n[2:].strip()
        return 'HD ' + rest
    return n
