# r27-reflag lane driver, built by make_reflag_driver.py from epoch_extend_multi.py (914fa1c1)
#!/usr/bin/env python3
"""
epoch_extend.py -- resumable, one-EB-at-a-time driver for the ALMA-SETI
EPOCH-EXTENSION programme.

Purpose
-------
The parent survey searched, for each member OUS (MOUS), only ONE of its
archival execution blocks (EBs).  Two independent mechanisms caused this:

  (a) calibrate_generic.py's per-target download budget
      (SETI_MAX_TARGET_DOWNLOAD_GB) skipped EBs that would have breached
      the budget; and
  (b) select_finest_spw.py deduplicates candidate spectral windows *by
      spw_id across EBs* (`by_spwid`), so even when several EBs of the
      same correlator setup were successfully calibrated, only one of
      them was ever split out and searched.

The unsearched EBs are therefore independent epochs of the *same*
frequency setup on the *same* star: exactly what is needed to (i) test
whether a flagged feature RECURS and (ii) deepen limits by adding
independent integration time.

This driver processes one named EB at a time through the *unmodified*
survey pipeline, in a private target directory, and reclaims all bulk
data immediately afterwards.

Nothing under /data/SETI/bin is modified or written to.  Nothing outside
this driver's own target directories (suffixed `_EB_<eb>`) is ever
written to or deleted.

Safety invariants (hard requirements from the author)
----------------------------------------------------
 * /data free space never falls below FLOOR_GB (default 150).  Checked
   before every download AND polled every WATCHDOG_POLL_S seconds during
   every step; a breach kills the running step, reclaims this EB's bulk
   data and stops the driver rather than continuing.
 * one EB at a time, never in parallel; nice 19 + ionice idle + taskset
   to a bounded core set in the upper half of the machine (the parent
   survey pins itself to cores 0-7, so we do not even share cores).
 * immediately after each EB is searched: rm -rf raw/ work/
   products/*.ms products/*_waterfall.npz, keeping only *_result.json,
   *_search.npz, *_srcspec.npz.
 * append-only log + per-EB verdict line + JSON state file, so an
   interrupted run resumes without repeating finished work.

Usage
-----
  epoch_extend.py run     [--max-ebs N] [--only EB] [--dry-run]
  epoch_extend.py status
  epoch_extend.py collect [--out /shared/.../results.json]
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time

HOME = os.environ.get('EE_HOME', '/data/SETI/epoch_extension')
# 2026-09-21: per-lane HOME so several lanes can run concurrently, each
# with its own worklist/state/lock/verdicts. Default unchanged.
BIN = '/data/SETI/bin'
TARGETS = os.environ.get('EE_TARGETS', '/data/SETI/targets')
# 2026-09-21: overridable so a lane can stage on another filesystem.
CALIB = f'{HOME}/calib_one_eb.py'          # local copy, generic + SETI_ONLY_EB
WORKLIST = f'{HOME}/worklist.json'
STATE = f'{HOME}/state.json'
LOG = f'{HOME}/epoch_extension.log'
VERDICTS = f'{HOME}/verdicts.log'
LOCK = f'{HOME}/driver.lock'

FLOOR_GB = float(os.environ.get('EE_FLOOR_GB', 150))      # hard floor, never breach
ABORT_GB = FLOOR_GB + float(os.environ.get('EE_ABORT_MARGIN_GB', 10))
EXPANSION = float(os.environ.get('EE_EXPANSION', 3.0))    # on-disk expansion factor
MIN_HEADROOM_GB = float(os.environ.get('EE_MIN_HEADROOM_GB', 45))
CONCURRENT_RESERVE_GB = float(os.environ.get('EE_CONCURRENT_RESERVE_GB', 60))
LOAD_CEILING = float(os.environ.get('EE_LOAD_CEILING', 120))
WATCHDOG_POLL_S = int(os.environ.get('EE_WATCHDOG_POLL_S', 20))
GATE_POLL_S = int(os.environ.get('EE_GATE_POLL_S', 120))
GATE_MAX_WAIT_S = int(os.environ.get('EE_GATE_MAX_WAIT_S', 6 * 3600))
CPU_LIST = os.environ.get('EE_CPU_LIST', '112-159')       # 48 cores, upper half
NPROC = int(os.environ.get('EE_NPROC', 48))

KEEP_SUFFIXES = ('_result.json', '_search.npz', '_srcspec.npz')


# ------------------------------------------------------------------ utils
def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def log(msg, echo=True):
    line = f'[{utc()}] {msg}'
    with open(LOG, 'a') as fh:
        fh.write(line + '\n')
    if echo:
        print(line, flush=True)


def verdict(msg):
    line = f'[{utc()}] {msg}'
    with open(VERDICTS, 'a') as fh:
        fh.write(line + '\n')
    log('VERDICT ' + msg)


def free_gb(path=None):
    # 2026-09-21: default to the volume TARGETS is on. A lane staging on
    # the root filesystem used to check /data and would have filled root.
    if path is None:
        path = TARGETS if os.path.isdir(TARGETS) else '/data'
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / 1e9


def load1():
    with open('/proc/loadavg') as fh:
        return float(fh.read().split()[0])


def other_pipeline_busy():
    """True if a *foreign* survey calibration/search is running (i.e. not
    one of our own children).  Used only to reserve extra disk headroom."""
    try:
        out = subprocess.run(['pgrep', '-af', 'python3 /data/SETI/bin/'],
                             capture_output=True, text=True).stdout
    except Exception:
        return False
    for ln in out.splitlines():
        if 'calibrate_generic.py' in ln or 'continuum_map_generic.py' in ln:
            return True
    return False


def load_json(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return default


def save_state(state):
    tmp = STATE + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(state, fh, indent=1, sort_keys=True)
    os.replace(tmp, STATE)


def safe_name(name):
    return re.sub(r'[^A-Za-z0-9_-]', '', re.sub(r'[ /()]', '_', name))


# ----------------------------------------------------------------- reclaim
def reclaim(tdir, why=''):
    """Delete this EB's bulk intermediates, keep the science products.
    Refuses to touch anything that is not one of our own `*_EB_*` dirs."""
    base = os.path.basename(tdir.rstrip('/'))
    if not tdir.startswith(TARGETS + '/') or '_EB_' not in base:
        log(f'REFUSING to reclaim {tdir}: not an epoch-extension target dir')
        return
    # R2-M3(a): injections must be made INTO the visibilities, so for the
    # injection set the measurement sets have to survive the search. Opt in
    # per run with EE_KEEP_MS=1; the default is unchanged.
    if os.environ.get('EE_KEEP_MS') == '1':
        log(f'keeping {tdir} ({why}): EE_KEEP_MS=1')
        return
    before = free_gb()
    for sub in ('raw', 'work'):
        shutil.rmtree(f'{tdir}/{sub}', ignore_errors=True)
        os.makedirs(f'{tdir}/{sub}', exist_ok=True)
    prod = f'{tdir}/products'
    if os.path.isdir(prod):
        for f in sorted(os.listdir(prod)):
            p = f'{prod}/{f}'
            if f.endswith(KEEP_SUFFIXES):
                continue
            if f.endswith('.ms') or f.endswith('.ms.flagversions') or '_waterfall' in f:
                shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
    after = free_gb()
    sz = subprocess.run(['du', '-sh', tdir], capture_output=True,
                        text=True).stdout.split('\t')[0]
    log(f'reclaimed {tdir} {why}: {before:.0f} -> {after:.0f} GB free, '
        f'target dir now {sz}')


# -------------------------------------------------------------- child exec
class DiskFloorBreach(Exception):
    pass


def run_step(cmd, env, tdir, label, timeout_s):
    """Run one pipeline step throttled + watchdogged.  Returns rc.
    Raises DiskFloorBreach if free space approaches the floor."""
    full = ['nice', '-n', '19', 'ionice', '-c3', 'taskset', '-c', CPU_LIST] + cmd
    stepdir = f'{tdir}/logs'
    os.makedirs(stepdir, exist_ok=True)
    outpath = f'{stepdir}/{label}.log'
    log(f'  -> {label}: {" ".join(cmd)}  (log {outpath})')
    t0 = time.time()
    with open(outpath, 'a') as fh:
        fh.write(f'\n===== {label} {utc()} =====\n')
        fh.flush()
        proc = subprocess.Popen(full, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                start_new_session=True)
        while True:
            try:
                rc = proc.wait(timeout=WATCHDOG_POLL_S)
                break
            except subprocess.TimeoutExpired:
                if _PEAK['dirs']:   # r27-reflag D-4
                    _PEAK['peak'] = max(_PEAK['peak'], du_gb(_PEAK['dirs']))
                fgb = free_gb()
                if fgb < ABORT_GB:
                    log(f'  !! DISK WATCHDOG: {fgb:.0f} GB free < {ABORT_GB:.0f} GB '
                        f'abort threshold during {label} -- killing step')
                    _kill(proc)
                    raise DiskFloorBreach(f'{fgb:.0f} GB free during {label}')
                if time.time() - t0 > timeout_s:
                    log(f'  !! TIMEOUT: {label} exceeded {timeout_s}s -- killing step')
                    _kill(proc)
                    return 124
    log(f'  <- {label} rc={rc} in {time.time()-t0:.0f}s, free={free_gb():.0f} GB')
    return rc


def _kill(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        pass
    try:
        proc.wait(timeout=60)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass


# -------------------------------------------------------------------- gate
# 2026-09-19: a 29.6 GB block passed the 5x gate and then consumed over
# 300 GB during CASA import/applycal/split -- an expansion of more than 10x.
# The disk watchdog killed it 50 minutes in, the driver exited on "3
# consecutive aborts", the health check relaunched it, and the same block
# repeated the same 50-minute failure six times over seven hours. The gate
# estimate is a prior, so when a block proves it wrong, believe the block.
EXPANSION_RETRY = float(os.environ.get('EE_EXPANSION_RETRY', 14.0))
MAX_DISK_ABORTS = int(os.environ.get('EE_MAX_DISK_ABORTS', 99))   # r27-reflag D-5

# ---------------------------------------------------------------- r27-reflag D-1/D-2/D-4
import fcntl
BIG_GB = 15.0
BIGLOCK = '/data/paper_build/BIGBLOCK.lock'
RESERVE_DIR = os.environ.get('REFLAG_RESERVE_DIR', '/data/paper_build/reflag_r27/reserve')
LANE = os.path.basename(HOME.rstrip('/'))


def du_gb(paths):
    tot = 0
    for p in paths:
        if os.path.exists(p):
            r = subprocess.run(['du', '-sb', p], capture_output=True, text=True).stdout.split()
            tot += int(r[0]) if r else 0
    return tot / 1e9


def foreign_big_running():
    """r27-fieldtrunc lanes predate the token: wait while one runs a > 15 GB block."""
    import glob as _g
    out = []
    for sp in _g.glob('/data/paper_build/fieldtrunc_r27/lanes/*/state.json'):
        lk = os.path.join(os.path.dirname(sp), 'driver.lock')
        pid = load_json(lk, {}).get('pid')
        if not (pid and os.path.exists(f'/proc/{pid}')):
            continue
        for e, r in load_json(sp, {}).get('ebs', {}).items():
            if r.get('status') == 'running' and (r.get('size_bytes') or 0) > BIG_GB * 1e9:
                out.append(f'{sp.split("/")[-2]}:{e}')
    return out


def others_outstanding_gb():
    """Sum over OTHER live lanes (same volume) of their reserved peak not yet used."""
    import glob as _g
    tot, who = 0.0, []
    for p in _g.glob(f'{RESERVE_DIR}/*.json'):
        r = load_json(p, {})
        if r.get('lane') == LANE or not r.get('pid') or not os.path.exists(f'/proc/{r["pid"]}'):
            continue
        if os.stat(r['volume']).st_dev != os.stat(TARGETS).st_dev:
            continue
        used = du_gb(r.get('dirs', []))
        tot += max(0.0, r['peak_gb'] - used)
        who.append(f'{r["lane"]}:{r["eb"]} {r["peak_gb"]:.0f}-{used:.0f}')
    return tot, who


def publish_reservation(item, peak_gb, dirs):
    os.makedirs(RESERVE_DIR, exist_ok=True)
    json.dump(dict(lane=LANE, pid=os.getpid(), eb=item['eb'], peak_gb=peak_gb, dirs=dirs,
                   volume=TARGETS, t=utc()), open(f'{RESERVE_DIR}/{LANE}.json', 'w'))


def unreserve():
    try:
        os.remove(f'{RESERVE_DIR}/{LANE}.json')
    except OSError:
        pass


_PEAK = {'dirs': [], 'peak': 0.0}


def wait_for_headroom(item, expansion=None):
    """Block until there is enough disk and the machine is not busy.
    Returns True if clear, False if we gave up (caller skips this EB)."""
    gb = (item.get('size_bytes') or 0) / 1e9
    expansion = EXPANSION if expansion is None else expansion
    need = FLOOR_GB + max(MIN_HEADROOM_GB, expansion * gb)
    t0 = time.time()
    while True:
        _gl = open(RESERVE_DIR + '/.gate.lock', 'a'); fcntl.flock(_gl, fcntl.LOCK_EX)   # r27-reflag D-2
        fgb, lg = free_gb(), load1()
        reserve = CONCURRENT_RESERVE_GB if other_pipeline_busy() else 0.0
        _o, _who = others_outstanding_gb()   # r27-reflag D-2
        reserve += _o
        if _who:
            log(f'  gate: other lanes outstanding {_o:.0f} GB {_who}')
        reason = ''
        if fgb < need + reserve:
            reason = (f'disk: {fgb:.0f} GB free < {need + reserve:.0f} GB required '
                      f'(floor {FLOOR_GB:.0f} + peak est {max(MIN_HEADROOM_GB, expansion*gb):.0f} '
                      f'for a {gb:.1f} GB EB' +
                      (f' + {reserve:.0f} GB reserved for a concurrent survey job' if reserve else '') + ')')
        elif lg > LOAD_CEILING:
            reason = f'load: 1-min load {lg:.1f} > {LOAD_CEILING:.0f} ceiling'
        if not reason:
            log(f'  gate OK for {item["eb"]}: free={fgb:.0f} GB (need {need+reserve:.0f}), load={lg:.1f}')
            publish_reservation(item, max(MIN_HEADROOM_GB, expansion * gb), _PEAK['dirs'])   # r27-reflag D-2
            fcntl.flock(_gl, fcntl.LOCK_UN); _gl.close()
            return True
        if time.time() - t0 > GATE_MAX_WAIT_S:
            fcntl.flock(_gl, fcntl.LOCK_UN); _gl.close()   # r27-reflag D-2
            log(f'  gate GAVE UP for {item["eb"]} after {(time.time()-t0)/3600:.1f} h: {reason}')
            return False
        fcntl.flock(_gl, fcntl.LOCK_UN); _gl.close()   # r27-reflag D-2
        log(f'  gate WAITING for {item["eb"]}: {reason}')
        time.sleep(GATE_POLL_S)


# ------------------------------------------------------------------ one EB
def process_eb(item, state):
    """r27-reflag D-1: big-block token around the unchanged body."""
    gb = (item.get('size_bytes') or 0) / 1e9
    fh = None
    if gb > BIG_GB or not item.get('size_bytes'):
        fh = open(BIGLOCK, 'a')
        t0 = time.time()
        while True:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                log(f'  BIGBLOCK token held by another lane; {item["eb"]} ({gb:.1f} GB) waits')
                time.sleep(120)
                continue
            fb = foreign_big_running()
            if not fb:
                break
            fcntl.flock(fh, fcntl.LOCK_UN)
            log(f'  r27-fieldtrunc big block running {fb}; {item["eb"]} ({gb:.1f} GB) waits')
            time.sleep(300)
        log(f'  BIGBLOCK token acquired for {item["eb"]} ({gb:.1f} GB) after {time.time()-t0:.0f} s')
    tdirs = [f'{TARGETS}/{u["target_dir"]}' for u in (item.get('units') or [])] or [f'{TARGETS}/{item["target_dir"]}']
    _PEAK['dirs'], _PEAK['peak'] = tdirs, 0.0
    try:
        return _process_eb(item, state)
    finally:
        unreserve()
        r = state['ebs'].get(item['eb'], {})
        r['peak_gb'] = round(_PEAK['peak'], 2)
        r['peak_x'] = round(_PEAK['peak'] / gb, 2) if gb else None
        save_state(state)
        log(f'  r27-reflag peak footprint {item["eb"]}: {_PEAK["peak"]:.1f} GB (x{(_PEAK["peak"]/gb if gb else 0):.2f})')
        _PEAK['dirs'] = []
        if fh:
            fcntl.flock(fh, fcntl.LOCK_UN)
            fh.close()
            log(f'  BIGBLOCK token released by {item["eb"]}')


def _process_eb(item, state):
    eb = item['eb']
    tdir = f'{TARGETS}/{item["target_dir"]}'
    rec = state['ebs'].setdefault(eb, {})
    rec.update(dict(eb=eb, mous=item['mous'], band=item.get('band'),
                    star=item['star_name'], target_dir=tdir,
                    size_bytes=item.get('size_bytes'), priority=item.get('priority'),
                    started=utc(), status='running'))
    save_state(state)
    log(f'=== EB {eb}  [{item["star_name"]}]  MOUS {item["mous"]}  '
        f'{(item.get("size_bytes") or 0)/1e9:.1f} GB -> {tdir}')

    # --- pre-flight: refuse blocks the archive cannot calibrate ----------
    # Twenty blocks were burning a full auxiliary-tar download and ~30 s of
    # CASA each, repeatedly, only to report "no execution blocks were
    # successfully calibrated": ALMA offers their raw ASDM but never
    # pipeline-calibrated them, so there is nothing to apply. The delivery
    # listing shows this for free (see cal_available.py, which is
    # calibrated against 361 already-searched blocks and only refuses
    # classes with zero observed successes). An unreachable archive returns
    # "unknown", which means try, not exclude.
    try:
        import cal_available
        _bad, _why = cal_available.is_uncalibratable(eb, item['mous'])
    except Exception as _e:
        _bad, _why = False, f'screen unavailable ({_e})'
    if _bad:
        rec['status'] = 'excluded_no_calibration_available'
        rec['exclusion_reason'] = _why
        rec['finished'] = utc()
        save_state(state)
        verdict(f'{eb} {item["star_name"]}: EXCLUDED before download -- '
                f'{_why} (no pipeline calibration exists for this EB)')
        return 'continue'

    _aborts = rec.get('disk_aborts', 0)
    if _aborts >= MAX_DISK_ABORTS:
        rec['status'] = 'deferred_too_large'
        rec['finished'] = utc()
        save_state(state)
        verdict(f'{eb} {item["star_name"]}: DEFERRED -- {_aborts} disk aborts; '
                f'this block needs more free space than the volume has')
        return 'continue'
    # A block that has aborted once is re-gated on what it actually did,
    # not on the generic prior.
    _exp = float(item.get('expansion') or EXPANSION) if not _aborts else max(EXPANSION_RETRY, float(item.get('expansion') or 0))   # r27-reflag D-8
    if not wait_for_headroom(item, expansion=_exp):
        rec['status'] = 'deferred_no_headroom'
        rec['finished'] = utc()
        save_state(state)
        verdict(f'{eb} {item["star_name"]}: DEFERRED -- no disk/load headroom '
                f'(gate at {_exp:.0f}x expansion)')
        # Per-block, not a machine-wide problem: skip it and keep working.
        # A genuine disk emergency is caught by the floor check in cmd_run.
        return 'continue'

    for sub in ('raw', 'work', 'products', 'logs'):
        os.makedirs(f'{tdir}/{sub}', exist_ok=True)

    env = os.environ.copy()
    env['CASASITECONFIG'] = '/home/fetch-agi/.casa/config.py'
    for v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'NUMEXPR_NUM_THREADS'):
        env[v] = '1'
    gb = (item.get('size_bytes') or 0) / 1e9
    # full EB id as the filter substring (ALMA tar names embed
    # "uid___A002_Xd9668b_Xa9df"), so a short tail can never match the
    # wrong execution block
    env['SETI_ONLY_EB'] = eb
    for _k, _v in (item.get('env') or {}).items():   # r27-reflag D-8
        env[_k] = str(_v)
    if item.get('env'):
        log(f'  r27-reflag D-8: per-item env {item["env"]}')
    env['SETI_MAX_EBS_PER_TARGET'] = '99'            # the ONLY_EB filter does the bounding
    env['SETI_MAX_TARGET_DOWNLOAD_GB'] = f'{max(10.0, gb + 5):.1f}'
    # make the pipeline's OWN pre-download margin check enforce our floor too
    env['SETI_DOWNLOAD_SAFETY_MARGIN_GB'] = f'{FLOOR_GB:.0f}'
    if item.get('drift_coeff'):
        env['SETI_DRIFT_COEFF'] = str(item['drift_coeff'])

    # ---- 1. calibrate this one EB
    try:
        rc = run_step(['python3', CALIB, tdir, item['mous'], str(NPROC)], env, tdir,
                      'calibrate', timeout_s=max(10800, int(300 * gb)))
    except DiskFloorBreach as e:
        rec.update(status='aborted_disk', error=str(e), finished=utc(),
                   disk_aborts=rec.get('disk_aborts', 0) + 1)
        reclaim(tdir, '(disk abort)')
        save_state(state)
        verdict(f'{eb} {item["star_name"]}: ABORTED (disk floor) during calibrate '
                f'-- {e} [abort {rec["disk_aborts"]} of {MAX_DISK_ABORTS}]')
        return 'continue'
    if rc != 0:
        rec.update(status='failed_calibrate', rc=rc, finished=utc())
        reclaim(tdir, '(failed calibrate)')
        save_state(state)
        verdict(f'{eb} {item["star_name"]}: FAILED calibration rc={rc} (no search performed)')
        return 'continue'

    # verify the pipeline really calibrated OUR EB and only ours
    cs = load_json(f'{tdir}/logs/calibrate_status.json', {})
    cal_ok = sorted(k for k, v in (cs.get('ebs') or {}).items() if v.get('ok'))
    rec['calibrated_ebs'] = cal_ok
    if cal_ok != [eb]:
        rec.update(status='failed_wrong_eb', finished=utc(),
                   error=f'calibrated EBs {cal_ok} != [{eb}]')
        reclaim(tdir, '(wrong EB calibrated)')
        save_state(state)
        verdict(f'{eb} {item["star_name"]}: FAILED -- calibrate produced {cal_ok}, '
                f'not exactly the requested EB; refusing to search it')
        return 'continue'

    # r27-fieldtrunc: reclaim raw/ and work/ NOW rather than at the end.
    # calibrate_generic.py's own comment (2026-09-07): "select_finest_spw.py
    # and everything downstream only ever reads from PROD, never WORK
    # (confirmed by direct inspection)".  On the pipeline path the imported
    # uid___<EB>.ms stays in work/ until reclaim(), so on X12189 it was still
    # on disk through extraction and set the block's peak (54 GB for an
    # 11.8 GB ASDM, against 41 GB at the end of calibration).  reclaim()
    # deletes exactly these two directories at the end anyway; this only
    # moves the deletion earlier.  products/ (the calibrated target MS) is
    # untouched.
    for sub in ('raw', 'work'):
        shutil.rmtree(f'{tdir}/{sub}', ignore_errors=True)
        os.makedirs(f'{tdir}/{sub}', exist_ok=True)
    log(f'  early reclaim of {tdir}/raw and /work after calibration: '
        f'free={free_gb():.0f} GB')

    # ---- 2. split every distinct spw of this EB
    try:
        rc = run_step(['python3', f'{BIN}/select_finest_spw.py', tdir], env, tdir,
                      'spw_select', timeout_s=7200)
    except DiskFloorBreach as e:
        rec.update(status='aborted_disk', error=str(e), finished=utc(),
                   disk_aborts=rec.get('disk_aborts', 0) + 1)
        reclaim(tdir, '(disk abort)')
        save_state(state)
        verdict(f'{eb} {item["star_name"]}: ABORTED (disk floor) during spw split -- {e}')
        return 'stop'
    spwlist = load_json(f'{tdir}/logs/spw_list.json', {}).get('spw_list', [])
    if rc != 0 or not spwlist:
        rec.update(status='failed_spw_select', rc=rc, finished=utc())
        reclaim(tdir, '(failed spw select)')
        save_state(state)
        verdict(f'{eb} {item["star_name"]}: FAILED spw selection rc={rc}')
        return 'continue'
    # r27-fieldtrunc: the calibrated target MS has had its last reader.
    # select_finest_spw.py splits every window out of it into
    # products/<EB>_spwN_search.ms, and neither seti_extract_generic.py nor
    # seti_drift_search_generic.py names `_target.ms` (grep, dd1300e0 and
    # ccca9bd8): the extractor reads SETI_MS, the per-window split.  reclaim()
    # deletes it at the end; deleting it here takes ~1.36x the ASDM off the
    # extract-stage peak (16 GB of 47 GB on X12189).
    _tms = f'{tdir}/products/{eb}_target.ms'
    if os.path.isdir(_tms):
        shutil.rmtree(_tms, ignore_errors=True)
        shutil.rmtree(_tms + '.flagversions', ignore_errors=True)
        log(f'  target MS removed after spw split (last reader done): free={free_gb():.0f} GB')
    rec['n_spw'] = len(spwlist)
    rec['n_spw_configured'] = load_json(f'{tdir}/logs/spw_list.json', {}).get('n_spw_configured')
    save_state(state)

    # ---- 3. extract + drift-search each window, FOR EVERY STAR UNIT
    # r27-fieldtrunc (row 55): a block holding several catalogued stars is
    # calibrated and split ONCE, and the deposited extractor + search are then
    # run once per star, each in its own `_EB_` target directory, from the same
    # split measurement sets.  The pipeline files in /data/SETI/bin are not
    # touched; the only change from epoch_extend.py (68ebab6f) is this loop.
    # An item without `units` is one unit (itself), i.e. exactly as before.
    units = item.get('units') or [dict(target_dir=item['target_dir'],
                                        star_name=item['star_name'],
                                        ra=item['ra'], dec=item['dec'],
                                        pmra=item['pmra'], pmdec=item['pmdec'],
                                        parallax=item['parallax'],
                                        parallax_err=item.get('parallax_err', 0.001))]
    # The search step deletes {TARGET_DIR}/products/{EB}_spwN_search.ms -- the
    # shared split -- only when TARGET_DIR is the directory holding it, i.e. for
    # the primary unit.  So the loop runs window by window and, within each
    # window, the PRIMARY UNIT LAST: every other star has read the split
    # before the primary's search consumes it.
    units = sorted(units, key=lambda u: u['target_dir'] == item['target_dir'])
    assert units[-1]['target_dir'] == item['target_dir'], 'primary unit missing'
    n_ok, spw_status = 0, {}
    n_tot = 0

    def unit_env(u):
        utdir = f'{TARGETS}/{u["target_dir"]}'
        for sub in ('work', 'products', 'logs'):
            os.makedirs(f'{utdir}/{sub}', exist_ok=True)
        uenv = dict(env)
        uenv['SETI_TARGET_DIR'] = utdir
        uenv['SETI_STAR_NAME'] = u['star_name']
        uenv['SETI_STAR_RA'] = str(u['ra'])
        uenv['SETI_STAR_DEC'] = str(u['dec'])
        uenv['SETI_STAR_PMRA'] = str(u['pmra'])
        uenv['SETI_STAR_PMDEC'] = str(u['pmdec'])
        uenv['SETI_STAR_PARALLAX'] = str(u['parallax'])
        uenv['SETI_STAR_PARALLAX_ERR'] = str(u.get('parallax_err', 0.001))
        return utdir, uenv

    for e in spwlist:
        lbl = f'spw{e["spw"]}'
        for u in units:
            utdir, uenv = unit_env(u)
            n_tot += 1
            senv = dict(uenv, SETI_MS=e['ms'], SETI_SFX=f'_spw{e["spw"]}')
            try:
                rc = run_step(['python3', f'{BIN}/seti_extract_generic.py', e['eb'], str(NPROC)],
                              senv, utdir, f'extract_{lbl}', timeout_s=14400)
                if rc == 0:
                    rc = run_step(['python3', f'{BIN}/seti_drift_search_generic.py', e['eb'], str(NPROC)],
                                  senv, utdir, f'search_{lbl}', timeout_s=14400)
            except DiskFloorBreach as ex:
                rec.update(status='aborted_disk', error=str(ex), finished=utc(),
                           disk_aborts=rec.get('disk_aborts', 0) + 1,
                           spw_status=spw_status, n_spw_ok=n_ok)
                for uu in units:
                    reclaim(f'{TARGETS}/{uu["target_dir"]}', '(disk abort)')
                save_state(state)
                verdict(f'{eb} {u["star_name"]}: ABORTED (disk floor) during {lbl} -- {ex}')
                return 'stop'
            ok = (rc == 0 and os.path.exists(
                f'{utdir}/products/{e["eb"]}_spw{e["spw"]}_result.json'))
            spw_status[f'{u["target_dir"]}:{e["spw"]}'] = 'ok' if ok else f'failed(rc={rc})'
            n_ok += 1 if ok else 0
            # this unit's waterfall and the extractor's per-unit field split are bulk
            junk = [f'{utdir}/products/{e["eb"]}_spw{e["spw"]}_waterfall.npz']
            if u['target_dir'] == item['target_dir']:
                junk.append(f'{utdir}/products/{e["eb"]}_spw{e["spw"]}_search.ms')
            wdir = f'{utdir}/work'
            junk += [f'{wdir}/{f}' for f in os.listdir(wdir)
                     if f.startswith(f'{e["eb"]}_spw{e["spw"]}_field')]
            for j in junk:
                if os.path.isdir(j):
                    shutil.rmtree(j, ignore_errors=True)
                elif os.path.exists(j):
                    os.remove(j)
            rec.update(spw_status=spw_status, n_spw_ok=n_ok)
            save_state(state)

    # ---- 4. reclaim, verdict
    # r27-reflag D-3: checksum the products before any deletion
    for u in units:
        _ut = f'{TARGETS}/{u["target_dir"]}'
        _pl = sorted(f for f in os.listdir(f'{_ut}/products') if f.endswith(KEEP_SUFFIXES))
        if _pl:
            _m = subprocess.run(['md5sum'] + _pl, cwd=f'{_ut}/products', capture_output=True, text=True)
            open(f'{_ut}/logs/products.md5', 'w').write(_m.stdout)
            assert _m.returncode == 0, _m.stderr
    for u in units:
        if u['target_dir'] != item['target_dir']:
            reclaim(f'{TARGETS}/{u["target_dir"]}', '(unit complete)')
    reclaim(tdir, '(EB complete)')
    rec.update(status='done' if n_ok else 'failed_search', finished=utc(),
               n_spw_ok=n_ok, spw_status=spw_status, n_units=len(units))
    save_state(state)
    if n_ok:
        open(f'{tdir}/logs/DONE', 'a').close()
    verdict(f'{eb} {item["star_name"]} [{item.get("band")}] MOUS {item["mous"]}: '
            f'{"SEARCHED" if n_ok else "SEARCH FAILED"} '
            f'{n_ok}/{n_tot} windows ok over {len(units)} star unit(s)'
            + (f' ({spw_status})' if n_ok != n_tot else ''))
    return 'continue'


# -------------------------------------------------------------------- main
def cmd_run(args):
    if os.path.exists(LOCK):
        pid = load_json(LOCK, {}).get('pid')
        if pid and os.path.exists(f'/proc/{pid}'):
            print(f'another epoch_extend driver is running (pid {pid}); refusing')
            return 2
        log(f'stale lock from pid {pid} removed')
    with open(LOCK, 'w') as fh:
        json.dump(dict(pid=os.getpid(), started=utc()), fh)
    try:
        work = load_json(WORKLIST, [])
        state = load_json(STATE, dict(created=utc(), ebs={}))
        log(f'driver start: {len(work)} work items, free={free_gb():.0f} GB, '
            f'load={load1():.1f}, floor={FLOOR_GB:.0f} GB, cpus={CPU_LIST}')
        done_states = ('done', 'failed_calibrate', 'failed_spw_select',
                       'failed_search', 'failed_wrong_eb',
                       'skipped_already_searched',
                       # terminal, and not a failure: the archive offers the
                       # raw ASDM but no pipeline calibration was ever
                       # produced for this EB, so there is nothing to apply.
                       'excluded_no_calibration_available',
                       # terminal for this pass: proved on disk that it needs
                       # more room than the volume has. Revisit deliberately.
                       'deferred_too_large')
        n = 0
        for item in work:
            if args.only and item['eb'] != args.only:
                continue
            st = state['ebs'].get(item['eb'], {}).get('status')
            if st in done_states:
                log(f'skip {item["eb"]}: already {st}')
                continue
            if item.get('skip'):
                state['ebs'].setdefault(item['eb'], {}).update(
                    dict(status='skipped_already_searched', note=item['skip'],
                         eb=item['eb'], mous=item['mous'], star=item['star_name'],
                         target_dir=f'{TARGETS}/{item["target_dir"]}'))
                save_state(state)
                log(f'skip {item["eb"]}: {item["skip"]}')
                continue
            if free_gb() < FLOOR_GB + MIN_HEADROOM_GB:
                log(f'driver stopping: only {free_gb():.0f} GB free, below '
                    f'floor {FLOOR_GB:.0f} + {MIN_HEADROOM_GB:.0f} GB minimum '
                    f'-- this is a volume problem, not a block problem')
                break
            if args.dry_run:
                print(f'would process {item["eb"]} {item["star_name"]} '
                      f'{(item.get("size_bytes") or 0)/1e9:.1f} GB')
                continue
            try:
                what = process_eb(item, state)
            except Exception as exc:                      # noqa: BLE001
                # 2026-09-17: never let one bad item kill the run. A missing
                # worklist field used to raise KeyError out of main() and the
                # watchdog then relaunched into the same crash indefinitely.
                import traceback
                log(f'  EXCEPTION on {item.get("eb")}: {exc.__class__.__name__}: {exc}')
                log('  ' + traceback.format_exc().replace(chr(10), ' | ')[:800])
                rec = state['ebs'].setdefault(item.get('eb', '?'), {})
                rec['status'] = 'failed_driver_exception'
                rec['finished'] = utc()
                rec['error'] = f'{exc.__class__.__name__}: {exc}'[:300]
                save_state(state)
                what = 'failed_driver_exception'
            n += 1
            if what == 'stop':
                # 2026-09-12: one block that cannot fit the disk used to halt
                # the entire campaign. Skip it and carry on; stop only if
                # several fail in a row, which means a real disk problem.
                state['consec_stop'] = state.get('consec_stop', 0) + 1
                save_state(state)
                if state['consec_stop'] >= 3:
                    log('driver stopping: 3 consecutive aborts')
                    break
                log('skipping this EB and continuing (see verdict above)')
                continue
            state['consec_stop'] = 0
            if args.max_ebs and n >= args.max_ebs:
                log(f'driver stopping: --max-ebs {args.max_ebs} reached')
                break
        log(f'driver end: {n} EB(s) attempted this session, free={free_gb():.0f} GB')
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass
    return 0


def cmd_status(args):
    state = load_json(STATE, dict(ebs={}))
    work = load_json(WORKLIST, [])
    print(f'free={free_gb():.0f} GB  load={load1():.1f}  floor={FLOOR_GB:.0f} GB')
    print(f'{len(work)} work items; state has {len(state["ebs"])} entries')
    for item in work:
        r = state['ebs'].get(item['eb'], {})
        print(f'  P{item.get("priority")} {item["eb"]:<22} {item["star_name"]:<24} '
              f'{(item.get("size_bytes") or 0)/1e9:6.1f} GB  '
              f'{r.get("status","pending"):<26} {r.get("n_spw_ok","")}/{r.get("n_spw","")}')
    return 0


def cmd_collect(args):
    sys.path.insert(0, HOME)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from collect_results import collect
    collect(args.out)
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--max-ebs', type=int, default=0)
    r.add_argument('--only')
    r.add_argument('--dry-run', action='store_true')
    sub.add_parser('status')
    c = sub.add_parser('collect')
    c.add_argument('--out', default=f'{HOME}/results.json')
    args = ap.parse_args()
    os.makedirs(HOME, exist_ok=True)
    return {'run': cmd_run, 'status': cmd_status, 'collect': cmd_collect}[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main())
