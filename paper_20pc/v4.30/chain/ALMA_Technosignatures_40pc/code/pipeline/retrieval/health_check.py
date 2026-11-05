#!/usr/bin/env python3
"""Hourly stall detector and self-healer for the ALMA-SETI download campaign.

WHY THIS EXISTS
---------------
On 2026-09-16/17 the campaign produced nothing for ~29 hours while every
surface indicator looked healthy: a driver process was running, the cron
watchdog was relaunching it, and state.json showed `done: 321`. The driver was
crash-looping on one malformed worklist entry. "Is the process alive" is
therefore NOT a liveness test. The only trustworthy signal is whether the
completed-block count is MOVING.

DETECTION
---------
Records (done_count, newest_log_mtime) each run in health_state.json.
  * STALL          done has not increased for >= STALL_H hours, work remains,
                   and the driver log has been silent for >= LOG_QUIET_MIN.
  * NO_DRIVER      nothing running and work remains.
  * SLOW_BUT_ALIVE done static but the log is still being written -- a big
                   block legitimately takes hours. Not a stall; left alone.

REMEDIATION LADDER (each step is logged, and only ever escalates)
-----------------------------------------------------------------
  1. NO_DRIVER            -> relaunch.
  2. STALL                -> kill driver, clear lock, relaunch.
  3. STALL again next hour -> additionally quarantine the block the driver was
                             last seen starting, as `failed_stall_quarantine`,
                             so one poisoned entry cannot loop forever.
  4. STALL a third time   -> stop trying, raise NEEDS_ATTENTION with the reason.
                             Automated remediation that keeps failing should
                             stop and ask, not thrash.

Writes health_state.json (machine-readable, for the agent to read in one
command) and appends to health.log. Safe to run from cron every hour.
"""
import glob, json, os, subprocess, sys, time

H = '/data/SETI/epoch_extension'
STATE = f'{H}/state.json'
WORK = f'{H}/worklist.json'
HS = f'{H}/health_state.json'
LOG = f'{H}/health.log'
STALL_H = 2.0
LOG_QUIET_MIN = 45.0
MAX_AUTOFIX = 3


def log(msg):
    line = '%s %s' % (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), msg)
    with open(LOG, 'a') as fh:
        fh.write(line + '\n')
    print(line)


def load(p, d):
    try:
        return json.load(open(p))
    except Exception:
        return d


def save(p, o):
    tmp = p + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(o, fh, indent=1)
    os.replace(tmp, p)


def driver_pids():
    try:
        out = subprocess.run(['pgrep', '-f', 'epoch_extend.py run'],
                             capture_output=True, text=True).stdout
        return [int(x) for x in out.split()]
    except Exception:
        return []


def newest_log():
    # Any driver log counts, not just laneA_*: a driver launched under another
    # name would otherwise look permanently silent and a healthy campaign would
    # be restarted every hour.
    pats = ('laneA_*.log', 'driver_*.log', 'watchdog_relaunch.log',
            'laneB/laneB_*.log')
    f = []
    for q in pats:
        f.extend(glob.glob(f'{H}/{q}'))
    f = sorted((x for x in f if os.path.isfile(x)), key=os.path.getmtime)
    return (f[-1], os.path.getmtime(f[-1])) if f else (None, 0.0)


def driver_env():
    """The ONE definition of the driver's tuning, read from run_env.json.

    2026-09-19: these values used to be hard-coded here as well as on the
    command line that starts the driver by hand. The floor was lowered to
    8 GB and the abort threshold to 15 GB, but this function would have
    silently relaunched with EE_FLOOR_GB=30 at the next stall and undone it
    -- the same failure as the two diverging copies of the calibrator. One
    file, read by everyone.
    """
    env = dict(os.environ)
    try:
        with open(f'{H}/run_env.json') as fh:
            env.update({k: str(v) for k, v in json.load(fh).items()})
    except Exception as e:
        log('WARNING: run_env.json unreadable (%s); relaunching with defaults' % e)
    return env


def relaunch():
    env = driver_env()
    try:
        os.remove(f'{H}/driver.lock')
    except OSError:
        pass
    stamp = time.strftime('%m%d-%H%M', time.gmtime())
    out = open(f'{H}/laneA_{stamp}.log', 'a')
    subprocess.Popen(['setsid', 'python3', '-u', 'epoch_extend.py', 'run'],
                     cwd=H, env=env, stdout=out, stderr=subprocess.STDOUT,
                     stdin=subprocess.DEVNULL, start_new_session=True)


def stop_driver():
    for sig in ('-TERM', '-TERM', '-KILL'):
        if not driver_pids():
            return True
        subprocess.run(['pkill', sig, '-f', 'epoch_extend.py run'])
        time.sleep(8)
    return not driver_pids()


def last_started_block(path):
    """The last block the driver announced starting, from its own log."""
    if not path:
        return None
    try:
        tail = subprocess.run(['tail', '-400', path], capture_output=True,
                              text=True).stdout
    except Exception:
        return None
    eb = None
    for ln in tail.splitlines():
        if '=== EB ' in ln:
            eb = ln.split('=== EB ')[1].split()[0]
    return eb


def main():
    st = load(STATE, {'ebs': {}})['ebs']
    wl = load(WORK, [])
    done = sum(1 for v in st.values()
               if v.get('status') in ('done', 'skipped_already_searched'))
    # 2026-09-20: `remaining` used to count worklist-minus-done, so blocks
    # the archive cannot supply (no pipeline calibration exists) and blocks
    # that failed terminally still counted as work outstanding. With the
    # sweep finished that left 32 phantom blocks, NO_DRIVER every ten
    # minutes, a driver relaunched to report "0 EB(s) attempted" and exit,
    # and an autofix counter climbing to 22 against a campaign that was
    # complete. A health check must agree with the driver about what is
    # left, and the driver's own done_states is the definition.
    TERMINAL = ('done', 'skipped_already_searched',
                'excluded_no_calibration_available', 'deferred_too_large',
                'failed_calibrate', 'failed_spw_select', 'failed_search',
                'failed_wrong_eb', 'failed_driver_exception',
                'failed_stall_quarantine')
    resolved = {k for k, v in st.items() if v.get('status') in TERMINAL}
    remaining = len([x for x in wl if x.get('eb') not in resolved])
    # reported separately so a completed campaign is visibly complete
    n_failed = sum(1 for v in st.values()
                   if str(v.get('status', '')).startswith('failed'))
    n_excl = sum(1 for v in st.values()
                 if v.get('status') == 'excluded_no_calibration_available')
    pids = driver_pids()
    lpath, lmt = newest_log()
    now = time.time()
    quiet_min = (now - lmt) / 60.0 if lmt else 1e9

    h = load(HS, {})
    prev_done = h.get('done')
    since = h.get('done_unchanged_since') or now
    if prev_done is None or done > prev_done:
        since = now
        h['autofix_count'] = 0
    static_h = (now - since) / 3600.0

    verdict, action = 'OK', 'none'
    if remaining == 0:
        verdict = 'COMPLETE'
        n_reset = True
    elif not pids:
        verdict, action = 'NO_DRIVER', 'relaunch'
    elif static_h >= STALL_H and quiet_min >= LOG_QUIET_MIN:
        verdict = 'STALL'
    elif static_h >= STALL_H:
        verdict = 'SLOW_BUT_ALIVE'

    n = 0 if locals().get('n_reset') else int(h.get('autofix_count') or 0)
    if verdict == 'NO_DRIVER':
        log('NO_DRIVER: %d blocks remain -> relaunching' % remaining)
        relaunch()
        n += 1
    elif verdict == 'STALL':
        if n >= MAX_AUTOFIX:
            verdict, action = 'NEEDS_ATTENTION', 'none'
            log('NEEDS_ATTENTION: %d automated fixes have not restored '
                'progress; done=%d static %.1f h, log quiet %.0f min'
                % (n, done, static_h, quiet_min))
        else:
            eb = last_started_block(lpath)
            log('STALL: done=%d static %.1f h, log quiet %.0f min, pids=%s, '
                'last block started=%s' % (done, static_h, quiet_min, pids, eb))
            stop_driver()
            action = 'restart'
            if n >= 1 and eb:
                # second failure in a row: quarantine the suspect block
                full = load(STATE, {'ebs': {}})
                rec = full['ebs'].setdefault(eb, {})
                rec['status'] = 'failed_stall_quarantine'
                rec['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                rec['error'] = 'quarantined by health_check after a repeated stall'
                save(STATE, full)
                action = 'restart+quarantine:' + eb
                log('  quarantined %s so it cannot loop again' % eb)
            relaunch()
            n += 1

    h.update({'checked': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'verdict': verdict, 'action': action, 'done': done,
              'remaining': remaining, 'driver_pids': pids,
              'done_unchanged_h': round(static_h, 2),
              'log_quiet_min': round(quiet_min, 1),
              'done_unchanged_since': since, 'autofix_count': n,
              'newest_log': os.path.basename(lpath) if lpath else None})
    save(HS, h)
    if verdict not in ('OK', 'COMPLETE', 'SLOW_BUT_ALIVE'):
        log('verdict=%s action=%s done=%d remaining=%d' % (verdict, action, done, remaining))
    print('verdict=%s done=%d remaining=%d failed=%d excluded=%d '
          'static=%.1fh quiet=%.0fmin autofix=%d'
          % (verdict, done, remaining, n_failed, n_excl, static_h,
             quiet_min, n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
