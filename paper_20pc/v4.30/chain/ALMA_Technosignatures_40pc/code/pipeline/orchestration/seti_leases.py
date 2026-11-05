#!/usr/bin/env python3
"""Volume-wide leases on target directories under /data/SETI/targets.

A lease says "some campaign is using this target directory right now".  It is
deliberately campaign-agnostic: the janitor must be able to honour a lease
written by a campaign it has never heard of.  That is the whole point -- the
round-7 recurrence lane lost three passes because occupancy was only ever
expressed inside one campaign's own claims/ directory.

Stale leases cannot wedge the volume: anything older than LEASE_MAX_AGE_S is
ignored.  Renew long units with touch().
"""
import os
import time

LEASE_DIR = '/data/SETI/leases'
LEASE_MAX_AGE_S = 6 * 3600


def acquire(target_dir, owner):
    os.makedirs(LEASE_DIR, exist_ok=True)
    p = os.path.join(LEASE_DIR, target_dir)
    with open(p, 'w') as fh:
        fh.write('%s %d %s\n' % (owner, os.getpid(),
                                 time.strftime('%FT%TZ', time.gmtime())))
    return p


def touch(target_dir):
    p = os.path.join(LEASE_DIR, target_dir)
    if os.path.exists(p):
        os.utime(p, None)


def release(target_dir):
    p = os.path.join(LEASE_DIR, target_dir)
    try:
        os.remove(p)
    except OSError:
        pass


def active(now=None):
    """Set of target_dir names currently leased by ANY campaign."""
    now = now or time.time()
    out = set()
    try:
        names = os.listdir(LEASE_DIR)
    except OSError:
        return out
    for n in names:
        p = os.path.join(LEASE_DIR, n)
        try:
            if now - os.path.getmtime(p) < LEASE_MAX_AGE_S:
                out.add(n)
        except OSError:
            pass
    return out
