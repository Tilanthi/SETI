#!/usr/bin/env python3
"""Reap the scratch of dead lanes, and release only the claims that are really
orphaned.

Working directories are named `<unit tag>.<pid>`, so a lane's scratch is
identifiable and private. That makes both questions decidable without guessing:

  * a work directory whose pid is gone is garbage, whatever else is happening;
  * a claim is orphaned only if no live process owns it -- checked against the
    `owner` file the lane writes and against any live work directory for that
    tag -- and only if the unit has produced no output.

This replaces the blanket "claim without output is an orphan" sweep, which is
true only when nothing is running and which, run while lanes were alive, gave
every in-flight unit to a second lane and stalled the campaign for an hour.

Prints one JSON line. Safe to run at any time, including with lanes running.
"""
import json
import os
import shutil
import sys

ROOT = os.environ.get('P90R7_ROOT', '/data/SETI/p90_r7')


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def main():
    work, claims, out = ROOT + '/work', ROOT + '/claims', ROOT + '/out'
    live_tags, dead_dirs, bytes_freed = set(), [], 0
    for d in sorted(os.listdir(work)) if os.path.isdir(work) else []:
        tag, _, pid = d.rpartition('.')
        if not tag or not pid.isdigit():
            continue
        if alive(int(pid)):
            live_tags.add(tag)
        else:
            p = os.path.join(work, d)
            for r, _, fs in os.walk(p):
                for f in fs:
                    try:
                        bytes_freed += os.path.getsize(os.path.join(r, f))
                    except OSError:
                        pass
            shutil.rmtree(p, ignore_errors=True)
            dead_dirs.append(d)

    released = []
    for tag in sorted(os.listdir(claims)) if os.path.isdir(claims) else []:
        if os.path.exists('%s/%s.json' % (out, tag)) or tag in live_tags:
            continue
        ow = '%s/%s/owner' % (claims, tag)
        if os.path.exists(ow):
            try:
                pid = int(open(ow).read().split()[0])
            except Exception:
                pid = None
            if pid is not None and alive(pid):
                continue          # the owner is still running, just not yet in
        shutil.rmtree('%s/%s' % (claims, tag), ignore_errors=True)
        released.append(tag)

    s = os.statvfs('/data')
    print(json.dumps(dict(dead_work_dirs=len(dead_dirs),
                          freed_GB=round(bytes_freed / 1e9, 1),
                          claims_released=released,
                          live_units=sorted(live_tags),
                          free_GB=round(s.f_bavail * s.f_frsize / 1e9, 1))))


if __name__ == '__main__':
    main()
    sys.exit(0)
