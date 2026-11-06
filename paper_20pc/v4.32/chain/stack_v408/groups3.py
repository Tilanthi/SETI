#!/usr/bin/env python3
"""Stackable groups, THIRD pass -- merged star identity (D31 item 1).

`groups2.py` keyed on `skey`, the search-time directory name, so 23 stars were
split across two or three keys and stacked twice.  This keys on the CANONICAL
identity from `starkey.py` (release designation -> SIMBAD -> measured parallax and
position, driven both ways), and is otherwise IDENTICAL to groups2: same maximum-
interval-overlap sweep, same MIN_BLOCKS, same MIN_COMMON_CHAN.

★ THE OVERLAP CRITERION IS THE SAME ONE AS BEFORE, AND IT IS WHAT KEEPS THE MERGE
HONEST.  Merging identities does not merge windows.  A group is still built by
finding the stellar-frame frequency covered by the largest number of distinct
execution blocks, taking the intersection of exactly those windows, and requiring
>= MIN_COMMON_CHAN channels of it; the key is additionally (identity, chanwidth).
So two tunings that do not share a channel, and two different bands, cannot land
in one group -- and this file ASSERTS that for every group emitted:

  O1  every window in the group spans the common interval: sf_lo <= lo < hi <= sf_hi
  O2  the common interval is non-empty and >= MIN_COMMON_CHAN channels wide
  O3  every window in the group is in the same band and has the same channel width
  O4  one window per execution block

O1-O3 are driven the other way in `--selftest`: relaxing the key to (identity)
alone, without the channel width, is shown to violate O3, and taking the union
rather than the intersection is shown to violate O1.
"""
import json, os, sys, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import starkey

MIN_COMMON_CHAN = 64
MIN_BLOCKS = 2


def best_overlap(ws):
    """Endpoint sweep: the frequency covered by the most distinct blocks."""
    ev = []
    for w in ws:
        ev.append((w['sf_lo'], 1, w))
        ev.append((w['sf_hi'], -1, w))
    ev.sort(key=lambda e: (e[0], -e[1]))
    live, best, bestx = set(), 0, None
    for x, d, w in ev:
        if d == 1:
            live.add(id(w))
        nb = len(set(y['block'] for y in ws if id(y) in live))
        if nb > best:
            best, bestx = nb, x
        if d == -1:
            live.discard(id(w))
    return bestx, best


def build(W, ident, keyfn=None, intersect=True):
    keyfn = keyfn or (lambda w: (ident[w['skey']], round(abs(w['chanw']))))
    bykey = collections.defaultdict(list)
    for w in W:
        bykey[keyfn(w)].append(w)
    groups = []
    for k, ws in bykey.items():
        cw = k[1] if len(k) > 1 else round(abs(ws[0]['chanw']))
        pool = list(ws)
        while True:
            x, nb = best_overlap(pool)
            if x is None or nb < MIN_BLOCKS:
                break
            sel = [w for w in pool if w['sf_lo'] <= x <= w['sf_hi']]
            byblk = {}
            for w in sel:
                if w['block'] not in byblk or w['nint'] > byblk[w['block']]['nint']:
                    byblk[w['block']] = w
            sel = list(byblk.values())
            if intersect:
                lo = max(w['sf_lo'] for w in sel)
                hi = min(w['sf_hi'] for w in sel)
            else:                                   # the selftest's wrong version
                lo = min(w['sf_lo'] for w in sel)
                hi = max(w['sf_hi'] for w in sel)
            ncom = (hi - lo) / cw
            if len(sel) >= MIN_BLOCKS and ncom >= MIN_COMMON_CHAN:
                groups.append(dict(
                    # `star` is the CANONICAL identity, not sel[0]'s directory
                    # name: with keys merged, an arbitrary member's directory name
                    # would relabel bet Pic's own survivors 'GaiaDR3_4792774797...'.
                    skey=k[0], star=k[0], star_dir=sel[0]['star_n'],
                    band=sel[0]['band'], chanw=cw,
                    n_win=len(sel), n_block=len(sel),
                    mjd_min=min(w['mjd'] for w in sel),
                    mjd_max=max(w['mjd'] for w in sel),
                    sf_common_lo=lo, sf_common_hi=hi, common_chan=ncom,
                    nchan=sel[0]['nchan'], tot_int=sum(w['nint'] for w in sel),
                    has_vsys=sel[0]['has_vsys'],
                    vcorr_swing=max(w['v_corr'] for w in sel) - min(w['v_corr'] for w in sel),
                    paths=[w['path'] for w in sel],
                    n_skey_merged=len(set(w['skey'] for w in sel))))
            ids = set(id(w) for w in sel)
            pool = [w for w in pool if id(w) not in ids]
            if not pool:
                break
    return groups


def check(groups, byp, strict=True):
    """O1-O4.  Returns the list of violations instead of raising, so the
    selftest can require them."""
    bad = collections.Counter()
    for g in groups:
        ws = [byp[p] for p in g['paths']]
        for w in ws:
            if not (w['sf_lo'] <= g['sf_common_lo'] and g['sf_common_hi'] <= w['sf_hi']):
                bad['O1 a window does not span the common interval'] += 1
        if not (g['sf_common_hi'] > g['sf_common_lo']
                and g['common_chan'] >= MIN_COMMON_CHAN):
            bad['O2 empty or too-narrow common interval'] += 1
        if len(set(w['band'] for w in ws)) != 1:
            bad['O3 more than one band in a group'] += 1
        if len(set(round(abs(w['chanw'])) for w in ws)) != 1:
            bad['O3b more than one channel width in a group'] += 1
        if len(set(w['block'] for w in ws)) != len(ws):
            bad['O4 two windows from one execution block'] += 1
    if strict:
        assert not bad, dict(bad)
    return bad


def main():
    W = json.load(open(os.path.join(HERE, 'windows.json')))
    byp = {w['path']: w for w in W}
    ident, route = starkey.build(W)
    st = starkey.selftest(W, ident)
    print('identities %d from %d skeys (routes %s); %d merged identities over %d '
          'skeys, worst |dplx|/plx %.2e'
          % (len(set(ident.values())), len(ident), dict(route),
             st['n_merged_identities'], st['n_skeys_merged'], st['worst_plx']))
    G = build(W, ident)
    check(G, byp)
    print('O1-O4 pass on all %d groups' % len(G))
    if '--selftest' in sys.argv:
        b1 = check(build(W, ident, keyfn=lambda w: (ident[w['skey']],), intersect=True),
                   byp, strict=False)
        print('drive: key without channel width ->', dict(b1) or 'DID NOT FIRE')
        assert any(k.startswith('O3b') for k in b1)
        b2 = check(build(W, ident, intersect=False), byp, strict=False)
        print('drive: union instead of intersection ->', dict(b2) or 'DID NOT FIRE')
        assert any(k.startswith('O1') for k in b2)
    json.dump(G, open(os.path.join(HERE, 'groups3.json'), 'w'))
    nb = np.array([g['n_block'] for g in G])
    print('groups %d  identities %d  blocks/group median %d max %d  '
          '(groups built from >1 skey: %d)'
          % (len(G), len(set(g['skey'] for g in G)), int(np.median(nb)), nb.max(),
             sum(1 for g in G if g['n_skey_merged'] > 1)))


if __name__ == '__main__':
    main()
