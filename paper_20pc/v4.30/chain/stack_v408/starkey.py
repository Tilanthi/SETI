#!/usr/bin/env python3
"""CANONICAL STAR IDENTITY FOR THE STACK (D31 item 1).

The stack keyed groups on `skey`, derived from the SEARCH-TIME DIRECTORY NAME, so
the same physical star appears twice whenever it was searched once under a named
directory and once under a `GaiaDR3_*` one.  20 such pairs exist.  The cost is
not only that `\\StkNStar` overcounts: a star's epochs are split across two
independent stacks, so its limit is SHALLOWER than the data allow -- the wrong
direction for a sensitivity claim.

Three routes to the identity, in order, none of them a string guess:

  1. the RELEASE'S OWN canonicalisation.  `corrected_export_v399.json` carries
     `target` (the directory) beside `star_name` (the resolved designation) on all
     1,721 rows; 426 directories, 0 ambiguous.  Pushed through the deposit's own
     `star_alias.released`, so this cannot drift from the catalogue.
  2. an EXTERNALLY RESOLVED identity for the `GaiaDR3_<id>` directories the export
     does not name: a live SIMBAD TAP query on the Gaia DR3 identifier, frozen in
     `simbad_gaia_v408.json` (29 of 29 resolved).  This is the standard v4.07's
     own census gate C1 demands for a name collision.
  3. a case- and whitespace-insensitive match of the directory's own name against
     the set of released names from route 1 (one directory, `hd107146`).

Anything unresolved keeps its own `skey` and therefore does not merge.

★ THE MERGE IS ASSERTED, NOT ASSUMED, IN BOTH DIRECTIONS.  Parallax separates the
two cases cleanly and by a factor of five:

    same star, two directory names   relative |dplx| <= 3.0e-4  (usually 0)
    two components of one system     relative |dplx| >= 1.5e-3

so `PLX_TOL = 1e-3`.  `selftest()` requires every merge to satisfy it AND requires
eight pinned component pairs -- GJ 2006A/B, G 272-61A/B, HD 139084B [805632] /
[921024], LP 476-207's two Gaia components, TWA 3A's two, 2MASS J0524's two,
AT Mic AB / AT Mic B, and GaiaDR3 3534414590303807232 / ...594600352896 -- to
FAIL it, i.e. to stay separate.

Note that merging identities does NOT merge windows: `groups3.py` keeps the
maximum-interval-overlap construction, so two tunings that do not share a channel
still cannot land in one group, and the common interval is non-empty by
construction.
"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# v4.08: this ran out of referee_r8/stack/ and pointed at the v4.07 deposit.
# Inside the deposit it must read THIS version's own export and THIS version's
# own star_alias, or the identity could drift from the catalogue that ships
# beside it -- which is the whole point of route 1.
V = os.path.normpath(os.path.join(HERE, '..'))
PLX_TOL = 1e-3

# pairs that MUST NOT merge: two physical stars, or two identities this project
# has explicitly ruled to be separate
MUST_STAY_SEPARATE = [
    ('gj2006a', 'gj2006b'),
    ('g272-61a', 'g272-61b'),
    ('hd139084b805632', 'hd139084b921024'),
    ('lp476-207384128', 'lp476-207783296'),
    ('twa3a576064', 'twa3a696000'),
    ('2massj05241914-1601153551040', '2massj05241914-1601153717696'),
    ('nameatmicab', 'vatmicb'),
    ('gaiadr33534414590303807232', 'gaiadr33534414594600352896'),
]


def _norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def _load_release_map():
    sys.path.insert(0, V)
    from star_alias import released
    exp = json.load(open(os.path.join(V, 'corrected_export_v399.json')))['rows']
    d2n = collections.defaultdict(set)
    for r in exp:
        d2n[r['target']].add(released(' '.join(r['star_name'].replace('_', ' ').split())))
    amb = {k: v for k, v in d2n.items() if len(v) > 1}
    assert not amb, 'export directory maps to two star names: %s' % list(amb)[:3]
    return {k: sorted(v)[0] for k, v in d2n.items()}, released


def build(windows):
    """windows -> dict(skey -> canonical identity), plus a route tally."""
    d2n, released = _load_release_map()
    sim = json.load(open(os.path.join(HERE, 'simbad_gaia_v408.json')))
    byname = {_norm(v): v for v in d2n.values()}
    sdir = lambda p: p.split('/targets/')[1].split('/')[0]
    first = {}
    for w in windows:
        first.setdefault(w['skey'], w)
    out, route = {}, collections.Counter()
    for sk, w in first.items():
        dd = sdir(w['path'])
        name = None
        for c in (dd, re.sub(r'_EB_\w+$', '', dd)):
            if c in d2n:
                name, r = d2n[c], 'release'
                break
        if name is None:
            g = re.match(r'^(GaiaDR3[ _]\d+)', w['star_n'])
            key = g.group(1).replace(' ', '_') if g else None
            if key in sim:
                name, r = released(sim[key]['main_id']), 'simbad'
        if name is None and _norm(w['star_n']) in byname:
            name, r = byname[_norm(w['star_n'])], 'name'
        if name is None:
            name, r = 'skey:' + sk, 'unresolved'
        out[sk] = name
        route[r] += 1
    # ---- corroborative pass: unify identities that differ only in spelling ---
    # Two things defeat the three routes above.  (a) The export spells some stars
    # in lower case ('hd107146') where SIMBAD returns 'HD 107146'.  (b) SIMBAD's
    # main identifier is sometimes a different designation from the release's --
    # Proxima Cen is '* alf Cen C' there.  Neither is a reason to keep a star
    # split, and neither is repaired by a hand alias here: identities are unified
    # when the MEASURED parallax agrees to PLX_TOL and the positions are within
    # SEP_MAX (a proper-motion displacement across epochs, at most 15.5" in this
    # survey), which is the same criterion selftest() drives both ways.
    import math
    SEP_MAX = 30.0
    plx, pos = {}, {}
    for w in windows:
        plx.setdefault(w['skey'], w['plx'])
        pos.setdefault(w['skey'], (w['ra'], w['dec']))
    rep = {n: sorted(sk for sk in out if out[sk] == n)[0] for n in set(out.values())}
    names = sorted(rep)
    par = {n: n for n in names}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = rep[names[i]], rep[names[j]]
            if abs(plx[a] - plx[b]) / plx[a] >= PLX_TOL:
                continue
            d = math.hypot((pos[a][0] - pos[b][0]) * math.cos(math.radians(pos[a][1])),
                           pos[a][1] - pos[b][1]) * 3600.0
            if d > SEP_MAX:
                continue
            ra_, rb_ = find(names[i]), find(names[j])
            if ra_ != rb_:
                par[rb_] = ra_
                route['corroborated'] += 1
    grp = collections.defaultdict(list)
    for n in names:
        grp[find(n)].append(n)
    canon = {}
    for root, v in grp.items():
        # the release's own designation wins over a Gaia id or a bare skey
        pick = sorted(v, key=lambda n: (n.startswith('skey:'), 'GaiaDR3' in n,
                                        n.islower(), len(n)))[0]
        for n in v:
            canon[n] = pick
    out = {sk: canon[n] for sk, n in out.items()}
    return out, route


def selftest(windows, ident):
    """Drive PLX_TOL both ways."""
    plx, pos = {}, {}
    for w in windows:
        plx.setdefault(w['skey'], w['plx'])
        pos.setdefault(w['skey'], (w['ra'], w['dec']))
    groups = collections.defaultdict(list)
    for sk, n in ident.items():
        groups[n].append(sk)
    merged = {n: v for n, v in groups.items() if len(v) > 1}
    worst, worst_pair = 0.0, None
    for n, v in merged.items():
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                d = abs(plx[v[i]] - plx[v[j]]) / plx[v[i]]
                if d > worst:
                    worst, worst_pair = d, (n, v[i], v[j])
    assert worst < PLX_TOL, ('MERGED two skeys whose parallaxes differ by %.2e: %s'
                             % (worst, worst_pair))
    # and the other direction: the pinned component pairs must NOT merge, and
    # must also fail the parallax test if they were tried
    fired = 0
    for a, b in MUST_STAY_SEPARATE:
        if a not in ident or b not in ident:
            raise AssertionError('pinned pair not in the stack: %s / %s' % (a, b))
        assert ident[a] != ident[b], \
            'MERGED a pinned component pair: %s / %s -> %s' % (a, b, ident[a])
        d = abs(plx[a] - plx[b]) / plx[a]
        assert d >= PLX_TOL, ('pinned pair %s / %s agrees in parallax to %.2e, '
                              'so PLX_TOL is too loose to separate them' % (a, b, d))
        fired += 1
    return dict(n_merged_identities=len(merged),
                n_skeys_merged=sum(len(v) for v in merged.values()),
                worst_plx=worst, worst_pair=worst_pair,
                pinned_pairs_checked=fired)


if __name__ == '__main__':
    W = json.load(open(os.path.join(HERE, 'windows.json')))
    ident, route = build(W)
    print('skeys %d -> identities %d   routes %s'
          % (len(ident), len(set(ident.values())), dict(route)))
    st = selftest(W, ident)
    print('merged identities %d covering %d skeys; worst merged |dplx|/plx %.2e (%s)'
          % (st['n_merged_identities'], st['n_skeys_merged'], st['worst_plx'],
             st['worst_pair'][0] if st['worst_pair'] else '-'))
    print('pinned component pairs kept separate and shown to fail PLX_TOL: %d/%d'
          % (st['pinned_pairs_checked'], len(MUST_STAY_SEPARATE)))
    g = collections.defaultdict(list)
    for sk, n in ident.items():
        g[n].append(sk)
    for n, v in sorted(g.items()):
        if len(v) > 1:
            print('   %-22s <- %s' % (n, ', '.join(sorted(v))))
    json.dump(ident, open(os.path.join(HERE, 'starkey_v408.json'), 'w'),
              indent=0, sort_keys=True)
