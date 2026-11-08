"""Build the final 20-40pc extension list (ranks 121+) from the verified
crossmatch results, in the SAME schema as ranked_master20pc.csv /
band_mous_master20pc.json, then write UNIFIED master40pc files that carry
the existing verified <=20pc targets over UNCHANGED (same rank/name) and
append the new targets with fresh sequential ranks after them."""
import json, csv

cands = {c['gaia_source_id']: c for c in json.load(open('candidates_40pc_raw_prealma.json'))}
xm = json.load(open('crossmatch_40pc_results.json'))
matched = {int(k): v for k, v in xm.items() if v}

# ---- exo hostname lookup (for display names) ----
exo_pm = {}
try:
    from astropy.table import Table
    t = Table.read('exo_hosts_gaia_pm_40pc.ecsv')
    for row in t:
        exo_pm[int(row['source_id'])] = str(row['hostname'])
except Exception as e:
    print('warning: could not load exo hostnames:', e)


def best_display_name(sid, cand, matches):
    if cand['is_exo_host'] and sid in exo_pm:
        return exo_pm[sid]
    if cand['is_disk_host'] and '(' in cand['name']:
        # cand['name'] is like "Gaia DR3 123 (GJ_2006B)" -- pull out the ALMA tname
        tname = cand['name'].split('(')[-1].rstrip(')')
        return tname.replace('_', ' ')
    # else prefer a clean, non-coordinate-style ALMA target_name if one exists
    names = sorted(set(m['target_name'] for m in matches), key=len)
    for n in names:
        n_clean = n.strip()
        if not n_clean or n_clean.replace('.', '').replace('-', '').replace('+', '').isdigit():
            continue  # pure coordinate-only name, e.g. "153703.1-331927"
        return n_clean.replace('_', ' ')
    return f"Gaia DR3 {sid}"


rows_new = []
band_mous_new = {}
sorted_sids = sorted(matched.keys(), key=lambda s: cands[s]['dist_pc'])

# 2026-09-07 fix: process_one_target.sh derives its per-target working
# directory purely from the star's NAME (tr ' /()' '____' ...), NOT from
# rank+name -- if two DIFFERENT stars (different Gaia source_ids) happen to
# resolve to the identical display name (confirmed live: 4 genuine tight
# binary/multiple companion pairs, e.g. two distinct Gaia solutions both
# named "LP 476-207", positions ~1-3" apart), they would collide on the
# SAME target directory, with one star's calibration attempt silently
# clobbering the other's. Disambiguate any name collision by appending the
# Gaia source_id's last 6 digits in brackets, applied to BOTH members of
# the colliding pair (not just the second) so it's symmetric/predictable.
#
# 2026-09-27 (v4.07, referee_r8/CENSUS_DUPLICATES.md).  THE DIGIT
# DISAMBIGUATOR IS ONLY CORRECT IF THE COLLIDING SOLUTIONS ARE PLAUSIBLY THE
# SAME STAR.  best_display_name() returns the ALMA *field* name for a disk
# host, and a field name is not a stellar identity: the HD_139084B field
# contains TWO catalogued stars, 10.3" apart, so both inherited the name
# "HD 139084B" and the suffix then dressed a MISNAMED PRIMARY up as a
# plausible-looking component pair.  Measured from this very census, the three
# genuine pairs span 0.44", 1.40" and 1.55" and that one spans 10.3" -- a 7x
# gap a tolerance can sit in.  So: a collision tighter than SEP_TOL_ARCSEC is
# disambiguated by Gaia digits as before; a WIDER one must be declared in
# FIELD_NAME_COLLISIONS with each member's externally resolved identity, and
# the declared name replaces the field name outright.  An undeclared wide
# collision stops the build.
SEP_TOL_ARCSEC = 3.0
FIELD_NAME_COLLISIONS = {
    # ALMA field name -> {gaia_source_id: resolved stellar identity}
    # Identities from a live SIMBAD TAP query (proper motion and parallax both
    # reproduce to 4 significant figures), not from our own documentation.
    'HD 139084B': {
        5882581895192805632: 'HD 139084B',   # M5Ve companion, plx 25.4404
        5882581895219921024: 'HD 139084',    # = V343 Nor A, K0V SB*, plx 25.829
    },
}


def _sep_arcsec(a, b):
    import math
    dra = ((a['ra'] - b['ra'])
           * math.cos(math.radians(0.5 * (a['dec'] + b['dec']))) * 3600.0)
    return math.hypot(dra, (a['dec'] - b['dec']) * 3600.0)


from collections import Counter
_field_name = {sid: best_display_name(sid, cands[sid], matched[sid])
               for sid in sorted_sids}
name_counts = Counter(_field_name.values())
dupe_names = {n for n, c in name_counts.items() if c > 1}
if dupe_names:
    print(f'name collisions found (disambiguating): {dupe_names}')

#: sid -> resolved identity, for collisions too wide to be one star
RESOLVED = {}
for _nm in sorted(dupe_names):
    _mem = [sid for sid in sorted_sids if _field_name[sid] == _nm]
    _sep = max(_sep_arcsec(cands[a], cands[b])
               for a in _mem for b in _mem if a != b)
    if _sep <= SEP_TOL_ARCSEC:
        print(f'  {_nm}: {len(_mem)} solutions, max separation {_sep:.2f}" '
              f'-- same star, disambiguating by Gaia id')
        continue
    _dec = FIELD_NAME_COLLISIONS.get(_nm)
    assert _dec is not None and set(_dec) == set(_mem), (
        f'display-name collision "{_nm}" spans {_sep:.2f}", more than '
        f'{SEP_TOL_ARCSEC}", and is not declared in FIELD_NAME_COLLISIONS '
        f'with exactly these Gaia ids ({sorted(_mem)}).  Over that '
        f'separation a shared name is an ALMA FIELD name, so at least one '
        f'member is misnamed and appending Gaia digits would hide the '
        f'misnomer behind a plausible-looking pair.')
    print(f'  {_nm}: {len(_mem)} solutions, max separation {_sep:.2f}" '
          f'-- DECLARED field-name collision, resolving each identity')
    for sid in _mem:
        print(f'     {sid} -> {_dec[sid]}')
    RESOLVED.update({sid: _dec[sid] for sid in _mem})

for i, sid in enumerate(sorted_sids):
    c = cands[sid]
    matches = matched[sid]
    name = best_display_name(sid, c, matches)
    if sid in RESOLVED:
        name = RESOLVED[sid]
    elif name in dupe_names:
        name = f"{name} [{str(sid)[-6:]}]"
    bands_present = sorted(set(m['band'] for m in matches), key=lambda x: int(x) if x.isdigit() else 99)
    rows_new.append(dict(
        name=name, ra=c['ra'], dec=c['dec'], dist_pc=c['dist_pc'],
        pmra=c['pmra'], pmdec=c['pmdec'],
        alma_bands=','.join(bands_present),
        gmag=c['gmag'] if c['gmag'] is not None else '',
        teff=c['teff'] if c['teff'] is not None else '',
        # 2026-09-26 (v4.06, DECISIONS_R8 D-residue).  This line used to be
        #     is_exo_host=c['is_exo_host'] if c['is_exo_host'] else '',
        # which wrote a BLANK for every star that is not an exoplanet host, so
        # the flag became unreadable: a blank could mean "not a host" or "never
        # determined".  Downstream, make_tables_v328.py counted every blank as
        # a non-host and published 19 hosts / 42 planets where the census
        # supports 23 / 50 -- the FIFTH instance of this project's blank-field
        # bug family.  The flag is now explicit for every row this script
        # emits, and the assertion below refuses to write a census that
        # contains an undetermined one.
        is_exo_host='True' if c['is_exo_host'] else 'False',
        n_planets=c['n_planets'] if c['n_planets'] else '0',
        source='new40pc', status='needs_redo',
        gaia_source_id=sid,
    ))
    by_band = {}
    for m in matches:
        by_band.setdefault(m['band'], [])
        if m['mous'] not in by_band[m['band']]:
            by_band[m['band']].append(m['mous'])
    for b in by_band:
        by_band[b] = sorted(by_band[b], key=lambda u: next(
            (mm['sr'] for mm in matches if mm['mous'] == u and mm['band'] == b), 1e12))
    band_mous_new[str(i)] = by_band  # temp index, renumbered below

# every display name this script emits must be unique, or two different stars
# share a working directory again -- the defect the digit suffix exists to
# prevent, and which resolving a field-name collision must not reintroduce.
_dupe_final = [n for n, c in Counter(r['name'] for r in rows_new).items()
               if c > 1]
assert not _dupe_final, ('display names still collide after resolution: %s'
                         % _dupe_final)

print(f'{len(rows_new)} new 20-40pc targets, {sum(len(v) for v in band_mous_new.values())} target-bands')

# ---- merge with existing <=20pc list, carrying it over UNCHANGED ----
existing_rows = list(csv.DictReader(open('ranked_master20pc.csv')))
existing_band_mous = json.load(open('band_mous_master20pc.json'))
max_rank = max(int(r['rank']) for r in existing_rows)
print(f'existing <=20pc list: {len(existing_rows)} targets, max rank {max_rank}')

final_rows = list(existing_rows)  # unchanged, same ranks
final_band_mous = dict(existing_band_mous)  # unchanged, same rank keys

next_rank = max_rank + 1
for i, r in enumerate(rows_new):
    rank = next_rank + i
    r2 = dict(r)
    r2['rank'] = rank
    r2['orig_rank'] = rank
    final_rows.append(r2)
    final_band_mous[str(rank)] = band_mous_new[str(i)]

fieldnames = list(existing_rows[0].keys())
# gaia_source_id is a new column not in the original schema -- append it
if 'gaia_source_id' not in fieldnames:
    fieldnames = fieldnames + ['gaia_source_id']
# ---------------------------------------------------------------------------
# 2026-09-26 (v4.06): NO CENSUS ENTRY MAY LEAVE HERE WITH AN UNDETERMINED
# EXOPLANET-HOST FLAG.  Two clauses, because the rows have two provenances and
# only one of them is this script's to fix.
#
#   (a) rows this script CREATES must carry an explicit flag.  This is a hard
#       assertion: if it ever fires, the fix is above, not here.
#   (b) rows INHERITED from ranked_master20pc.csv carry whatever the earlier
#       census builder wrote, and 96 of them are blank.  This script must not
#       silently launder them into "not a host", so the count is audited and
#       PINNED: the assertion fails if the number of undetermined flags grows,
#       which is the failure mode that would repeat the bug a sixth time.
#       Repairing those 96 means re-deriving host status positionally for the
#       <=20 pc census, which is the upstream builder's job.
_blank_new = [r for r in final_rows[len(existing_rows):]
              if not str(r.get('is_exo_host', '')).strip()]
assert not _blank_new, (
    '%d newly created census entries carry a blank is_exo_host: %s'
    % (len(_blank_new), [r['name'] for r in _blank_new[:8]]))
_blank_inherited = [r for r in final_rows[:len(existing_rows)]
                    if not str(r.get('is_exo_host', '')).strip()]
N_BLANK_INHERITED_EXPECTED = 96
assert len(_blank_inherited) == N_BLANK_INHERITED_EXPECTED, (
    'the number of inherited census entries with an undetermined '
    'is_exo_host is %d, pinned at %d.  If it GREW, an upstream builder has '
    'started writing blanks again; if it SHRANK, say so and lower the pin.'
    % (len(_blank_inherited), N_BLANK_INHERITED_EXPECTED))
json.dump({'n_rows': len(final_rows),
           'n_created': len(final_rows) - len(existing_rows),
           'n_blank_created': len(_blank_new),
           'n_blank_inherited': len(_blank_inherited),
           'blank_inherited_names': sorted(r['name']
                                           for r in _blank_inherited),
           'note': 'is_exo_host records HOW A STAR ENTERED THE CENSUS, not '
                   'whether it hosts a planet; a blank is undetermined, NOT '
                   'False.  make_tables_v328.py (v4.05) joins positionally '
                   'instead of trusting this flag.'},
          open('ranked_master40pc_flagaudit.json', 'w'), indent=1)

with open('ranked_master40pc.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in final_rows:
        w.writerow({k: r.get(k, '') for k in fieldnames})

json.dump(final_band_mous, open('band_mous_master40pc.json', 'w'), indent=1)

print(f'\nWrote ranked_master40pc.csv: {len(final_rows)} total targets (ranks 1-{next_rank + len(rows_new) - 1})')
print(f'Wrote band_mous_master40pc.json: {len(final_band_mous)} rank entries')
print(f'\nNew targets (ranks {next_rank}-{next_rank + len(rows_new) - 1}):')
for r in final_rows[len(existing_rows):]:
    print(f"  {r['rank']:>4}  {r['name']:30s} d={float(r['dist_pc']):.2f}pc bands={r['alma_bands']}")
