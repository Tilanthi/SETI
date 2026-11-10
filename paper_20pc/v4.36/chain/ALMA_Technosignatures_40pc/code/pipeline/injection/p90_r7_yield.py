#!/usr/bin/env python3
"""Release the campaign's large units and their transient disk.

Called by the driver when the shared volume runs low, and usable by hand. The
refit campaign has priority on /data; a large unit of this campaign holds up to
50 GB of split and copy, so yielding it is the cheapest way to give the volume
back.

★ Why this is a file and not a shell one-liner: releasing a unit means killing
its processes, and `pkill -f <unit tag>` issued over ssh matches the ssh command
line itself, because the tag is in it. Doing it from a script whose own command
line carries only the script name cannot self-match. That mistake killed my own
shell once already today.

A unit is only released if no live process is using its work directory.
"""
import json
import os
import shutil
import signal
import subprocess
import sys

ROOT = os.environ.get('P90R7_ROOT', '/data/SETI/p90_r7')
# By default the large units; or an explicit list, so that a deliberate
# reprioritisation uses the same safe owner-pid mechanism as the disk yield
# rather than a second, less careful one.
if len(sys.argv) > 1 and sys.argv[1] == '--tags':
    BIG = set(x for x in sys.argv[2].split(',') if x)
else:
    BIG = set(x for x in open(ROOT + '/big_tags.txt').read().split(',') if x)


def descendants(pid):
    """pid and every descendant, from /proc, without pattern matching."""
    kids = {}
    for d in os.listdir('/proc'):
        if not d.isdigit():
            continue
        try:
            with open('/proc/%s/stat' % d) as fh:
                f = fh.read().rsplit(')', 1)[1].split()
            kids.setdefault(int(f[1]), []).append(int(d))
        except Exception:
            continue
    out, stack = [], [pid]
    while stack:
        p = stack.pop()
        out.append(p)
        stack.extend(kids.get(p, []))
    return out


def pids_for(tag):
    """The lane that owns this unit, and its children.

    *** NOT by pattern. `pkill -f <tag>` matched every lane, because each lane
    carries the whole list of large unit tags in its P90R7_ONLY environment, so
    yielding one unit killed all of them -- including their shells, which
    silently removed four tmux windows and stalled the large Class A units for
    half an hour. The claim records its owner pid; use it.
    """
    ow = '%s/claims/%s/owner' % (ROOT, tag)
    if not os.path.exists(ow):
        return []
    try:
        pid = int(open(ow).read().split()[0])
    except Exception:
        return []
    try:
        os.kill(pid, 0)
    except OSError:
        return []
    return [p for p in descendants(pid) if p != os.getpid()]


def main():
    freed, held = [], []
    for tag in sorted(BIG):
        if os.path.exists(f'{ROOT}/out/{tag}.json'):
            continue
        wdir = f'{ROOT}/work/{tag}'
        claim = f'{ROOT}/claims/{tag}'
        if not (os.path.exists(wdir) or os.path.exists(claim)):
            continue
        for sig in (signal.SIGTERM, signal.SIGKILL):
            pids = pids_for(tag)
            if not pids:
                break
            for p in pids:
                try:
                    os.kill(p, sig)
                except ProcessLookupError:
                    pass
            import time
            time.sleep(3)
        if pids_for(tag):
            held.append(tag)
            continue
        sz = 0
        if os.path.isdir(wdir):
            sz = int(subprocess.run(['du', '-sb', wdir], capture_output=True,
                                    text=True).stdout.split()[0] or 0)
        shutil.rmtree(wdir, ignore_errors=True)
        shutil.rmtree(claim, ignore_errors=True)
        freed.append((tag, sz / 1e9))
    s = os.statvfs('/data')
    print(json.dumps(dict(released=[t for t, _ in freed],
                          released_GB=round(sum(g for _, g in freed), 1),
                          still_held=held,
                          free_GB=round(s.f_bavail * s.f_frsize / 1e9, 1))))


if __name__ == '__main__':
    main()
    sys.exit(0)
