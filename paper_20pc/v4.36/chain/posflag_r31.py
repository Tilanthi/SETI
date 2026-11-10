#!/usr/bin/env python3
r"""posflag_r31 -- the systems whose limit is conditional on the adopted position.

WHY IT EXISTS.  orbpm_r18.py propagates each star's Gaia DR3 position to the
observation epoch and bounds the extraction-position error a bound companion
can cause (visual orbit, separation with masses, or the proper-motion anomaly).
For three stars it cannot: their DR3 solutions are disturbed (RUWE / excess
noise), no companion is catalogued and no Hipparcos epoch exists, so the
positional loss on their windows has NO upper bound (orbpm_r18 `unquantified`).
Their limits are therefore conditional on the adopted position, and the
summaries the paper quotes over systems -- the median, the count reaching
10^15 W and the Fig. 5 summary -- are formed WITHOUT them.  Table F1 keeps
their rows, marked.

THE SET IS orbpm_r18's OWN, but orbpm_r18.py runs after numbers_v410.py in
make_all.sh, so it cannot be read there on a clean tree.  It is therefore
frozen here, and persys_r17.py (which runs after orbpm_r18.py) asserts that
orbpm_r18.json's `unquantified` stars are exactly this set (check()).  A
change in orbpm's set fails the build instead of silently desynchronising.

  python3 posflag_r31.py      # prints the set and checks it against orbpm_r18.json
"""
import json
import os

#: orbpm_r18 rows with unquantified=True (disturbed DR3 solution, no companion,
#: no Hipparcos epoch).  system_id == star_name for all three in the catalogue.
POS_COND = ('Barta 161 12', 'HD 155555C', 'LHS 1140')

#: the table mark for these rows (the fourth of the standard note symbols)
MARK = r'$^{\S}$'


def is_cond(system_id):
    return system_id in POS_COND


def check(path='orbpm_r18.json'):
    """Assert orbpm_r18.json's unquantified set equals POS_COND; return
    (n_stars, n_windows)."""
    d = json.load(open(path))
    got = sorted({r['star'] for r in d['rows'] if r['unquantified']})
    assert got == sorted(POS_COND), (
        'posflag_r31: orbpm_r18 unquantified stars %s differ from the frozen '
        'set %s -- update POS_COND (and the text that names them)'
        % (got, sorted(POS_COND)))
    nwin = sum(r['nwin'] for r in d['rows'] if r['unquantified'])
    return len(got), nwin


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    print('posflag_r31: %d stars, %d windows: %s'
          % (check(os.path.join(here, 'orbpm_r18.json')) + (', '.join(POS_COND),)))
