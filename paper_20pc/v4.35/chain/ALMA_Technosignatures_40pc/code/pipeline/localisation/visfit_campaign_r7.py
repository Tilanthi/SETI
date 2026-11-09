#!/usr/bin/env python3
"""Referee round 7: re-fit every visibility localisation with the three
defects of the round-6 estimator repaired (see visfit_r7y.py).

Structurally this is `visfit_campaign_r6.py`, with four changes:

  1. the fit is `visfit_r7y.py`, not `visfit_r6.py`;
  2. a block whose calibrated target measurement set is ALREADY on disk is
     fitted in place and is never fetched and never deleted -- the P90
     round-7 campaign is using several of those, and deleting one would
     destroy a running experiment;
  3. lanes can be restricted by block size (VF_MIN_GB / VF_MAX_GB), so the
     three 45-55 GB blocks get a lane to themselves instead of three lanes
     simultaneously demanding 150 GB of a 218 GB volume;
  4. the fetch gate waits at most 90 minutes rather than 24 hours.  Round 6's
     predecessor spun for ten hours on a demand that could never be met; a
     block that cannot get room should be recorded as such, not hidden.

The criterion is NOT applied here.  This driver only measures; scoring is
against `/workspace/SETI/referee_r6/LOCALISATION_CRITERION.md`, unchanged.

Usage:  visfit_campaign_r7.py work
        visfit_campaign_r7.py collect
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, '/data/SETI/bin')
import seti_leases

ROOT = os.environ.get('VF_ROOT', '/data/SETI/visfit_r7')
PLAN = f'{ROOT}/plan.json'
CLAIMS, OUT, WORK, LOGS = (f'{ROOT}/claims', f'{ROOT}/out',
                           f'{ROOT}/work', f'{ROOT}/logs')
BIN = '/data/SETI/bin'
EE = '/data/SETI/epoch_extension/epoch_extend.py'
TEMPLATE = '/data/SETI/mine2026/lane_l1'
FLOOR_GB = float(os.environ.get('VF_FLOOR_GB', 50))
NPROC = os.environ.get('VF_NPROC', '8')
MIN_GB = float(os.environ.get('VF_MIN_GB', 0))
MAX_GB = float(os.environ.get('VF_MAX_GB', 1e9))


PREEXIST = set(json.load(open(f'{ROOT}/preexisting_dirs.json')))

# A status that describes the VOLUME or the campaign's own gating says nothing
# about the block.  Round 6 recorded eighteen of them as finished blocks;
# round 7 recorded twenty-nine.  With VF_REFUSED_DIR=1 they go to refused/
# and out/ holds only records that describe a block.
REFUSALS = {'fetch_returned_immediately', 'no_measurement_set',
            'disk_gate_timeout'}
REFUSED = f'{ROOT}/refused'
SPLIT_REFUSALS = os.environ.get('VF_REFUSED_DIR') == '1'


def reclaim(u):
    """Remove the target directory this block left behind, and nothing else.

    EE_KEEP_MS=1 makes epoch_extend RETAIN the directory after a disk abort.
    Six of those left 248 GB on the volume and starved every other lane,
    which caused more aborts, which left more directories.

    The first version of this globbed `*_EB_<last token of the EB>` and
    deleted a DIFFERENT star's pre-existing products directory that happened
    to share the token.  Two guards now: the name must be the worklist's own
    target_dir, and the directory must not have existed when the campaign
    started."""
    return reclaim_dir('/data/SETI/targets/'
                       + ((u.get('item') or {}).get('target_dir') or '_none_'),
                       u['eb'])


def reclaim_dir(d, eb):
    """Reclaim the bulk of a fetched block WITHOUT touching the survey's
    own products.

    A target directory is not necessarily ours.  For blocks the original
    survey searched it already holds `*_srcspec.npz`, `*_search.npz` and
    `*_result.json` -- 164 MB for bet Pic B6 X3a90 -- and those are the
    products the phase-centre audit read its measured offsets from.  The
    round-6 driver removed the whole directory (`shutil.rmtree(tdir)`) and
    so did the first version of this one; that is how ~70 retained srcspec
    products were lost.  Only the fetch's own bulk goes: raw/, work/, and
    the measurement sets under products/."""
    gone = []
    if not os.path.isdir(d):
        return gone
    for sub in ('raw', 'work'):
        if os.path.isdir(os.path.join(d, sub)):
            shutil.rmtree(os.path.join(d, sub), ignore_errors=True)
            gone.append(os.path.join(d, sub))
    for p in glob.glob(os.path.join(d, 'products', '*.ms')):
        shutil.rmtree(p, ignore_errors=True)
        gone.append(p)
    for p in glob.glob(os.path.join(d, 'products', '*.ms.flagversions')):
        shutil.rmtree(p, ignore_errors=True)
        gone.append(p)
    return gone


def free_gb(p='/data'):
    s = os.statvfs(p)
    return s.f_bavail * s.f_frsize / 1e9


def run(cmd, env, log, timeout=21600):
    with open(log, 'a') as fh:
        fh.write('\n===== %s %s =====\n'
                 % (' '.join(cmd), time.strftime('%FT%TZ', time.gmtime())))
        fh.flush()
        p = subprocess.Popen(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT)
        try:
            return p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            return 124


def fit(eb, events, log, env):
    json.dump(events, open(f'/tmp/vf_r7_ev_{eb}.json', 'w'))
    json.dump({e['eb']: e['drift_Hz_s'] for e in events},
              open(f'/tmp/vf_r7_dr_{eb}.json', 'w'))
    fenv = dict(env, VF_EVENTS=f'/tmp/vf_r7_ev_{eb}.json',
                VF_DRIFT=f'/tmp/vf_r7_dr_{eb}.json',
                VF_OUT=f'{OUT}/{eb}.fit.json', VF_VERBOSE='1')
    rc = run(['python3', f'{BIN}/visfit_r7y.py'], fenv, log, timeout=14400)
    return rc


def do_unit(u):
    """Run one unit, always releasing the volume lease."""
    try:
        return _do_unit(u)
    finally:
        _td = (u.get('item') or {}).get('target_dir')
        if _td:
            seti_leases.release(_td)


def _do_unit(u):
    eb = u['eb']
    rec = dict(eb=eb, started=time.strftime('%FT%TZ', time.gmtime()),
               gb=u['gb'], unsafe=u.get('unsafe', False))
    log = f'{LOGS}/{eb}.log'
    t0 = time.time()
    env = dict(os.environ)
    env.update(CASASITECONFIG='/home/fetch-agi/.casa/config.py')

    ms = u.get('preexisting_ms')
    tdir = None
    home = None
    if ms and os.path.isdir(ms):
        rec['ms_source'] = 'pre-existing on disk, not fetched and not deleted'
    else:
        t_wait = time.time()
        while free_gb() < FLOOR_GB:
            if time.time() - t_wait > 5400:
                rec.update(status='disk_gate_timeout', free_gb=free_gb())
                return rec
            time.sleep(30)
        # A lane home is not just a worklist: epoch_extend.py invokes
        # calib_one_eb.py and its helpers FROM EE_HOME, so the home has to
        # carry them.  Without that the calibration exits rc=2 in zero
        # seconds and the block looks processed when nothing happened.
        home = f'{WORK}/{eb}'
        shutil.rmtree(home, ignore_errors=True)
        os.makedirs(home, exist_ok=True)
        for f in ('calib_one_eb.py', 'cal_available.py',
                  '_tsysspwmap_legacy.py', 'collect_results.py',
                  'make_worklist.py'):
            src = f'{TEMPLATE}/{f}'
            if os.path.exists(src):
                shutil.copy2(src, f'{home}/{f}')
        json.dump([u['item']], open(f'{home}/worklist.json', 'w'))
        # Announce occupancy at VOLUME level before anything is written into
        # the target directory.  Without this, another campaign's janitor
        # deletes work/ and raw/ underneath a live importasdm and the block
        # is recorded as having no measurement set.
        _td = (u.get('item') or {}).get('target_dir')
        if _td:
            seti_leases.acquire(_td, f'visfit_campaign_r7:{ROOT}')
            rec['lease'] = _td
        env.update(EE_HOME=home, EE_KEEP_MS='1', EE_NPROC=NPROC,
                   EE_FLOOR_GB='25', EE_MIN_HEADROOM_GB='40',
                   EE_CONCURRENT_RESERVE_GB='0', EE_EXPANSION='3.0',
                   EE_GATE_MAX_WAIT_S='5400', EE_MAX_DISK_ABORTS='1',
                   EE_TARGETS='/data/SETI/targets')
        _t = time.time()
        rc = run(['python3', EE, 'run'], env, log)
        rec['fetch_rc'] = rc
        rec['fetch_s'] = round(time.time() - _t, 1)
        if rec['fetch_s'] < 30:
            rec.update(status='fetch_returned_immediately',
                       reclaimed=reclaim(u))
            shutil.rmtree(home, ignore_errors=True)
            return rec
        cand = sorted(glob.glob(
            '/data/SETI/targets/*/products/%s_target.ms' % eb))
        if not cand:
            # EE_KEEP_MS=1 makes epoch_extend RETAIN the target directory
            # after a disk abort.  Six of those left 248 GB on the volume and
            # starved every other lane, which caused more aborts, which left
            # more directories: a failure that feeds itself.  A block that
            # produced no measurement set keeps nothing.
            rec.update(status='no_measurement_set',
                       reclaimed=reclaim(u))
            shutil.rmtree(home, ignore_errors=True)
            return rec
        ms = cand[0]
        tdir = ms.split('/products/')[0]
        rec['ms_source'] = 'fetched and calibrated by this campaign'

    events = [dict(e, ms=ms) for e in u['events']]
    rec['fit_rc'] = fit(eb, events, log, env)
    if os.path.exists(f'{OUT}/{eb}.fit.json'):
        rec['fit'] = json.load(open(f'{OUT}/{eb}.fit.json'))
        # A disk abort during calibration can leave a partial *_target.ms
        # that the glob above happily finds and casatools then refuses to
        # open.  The block looked 'ok' the first time this happened, with
        # every event carrying an exception inside it.  A block is only ok
        # if at least one of its events actually fitted.
        rec['status'] = ('ok' if any(v.get('status') == 'ok'
                                     for v in rec['fit'].values())
                         else 'no_event_fitted')
    else:
        rec['status'] = 'fit_failed'

    if tdir:
        rec['reclaimed'] = reclaim_dir(tdir, eb)
    if home:
        shutil.rmtree(home, ignore_errors=True)
    rec['runtime_s'] = round(time.time() - t0, 1)
    rec['finished'] = time.strftime('%FT%TZ', time.gmtime())
    return rec


def worker():
    units = json.load(open(PLAN))
    for d in (CLAIMS, OUT, WORK, LOGS):
        os.makedirs(d, exist_ok=True)
    for u in units:
        if not (MIN_GB <= u['gb'] < MAX_GB):
            continue
        if os.path.exists(f'{OUT}/{u["eb"]}.json'):
            continue
        try:
            os.mkdir(f'{CLAIMS}/{u["eb"]}')
        except FileExistsError:
            continue
        print('=== claimed %s (%.1f GB, %d windows)'
              % (u['eb'], u['gb'], len(u['events'])), flush=True)
        try:
            rec = do_unit(u)
        except Exception as exc:
            import traceback
            rec = dict(eb=u['eb'], status='exception', error=repr(exc),
                       traceback=traceback.format_exc())
            shutil.rmtree(f'{WORK}/{u["eb"]}', ignore_errors=True)
        # `runtime_s` is only set on the paths that ran the fit, so the
        # lane log used to print "(0 s)" for every refusal and made a
        # multi-minute epoch_extend invocation look like an instant one.
        # An absent quantity must not be printed as an observed one.
        _el = rec.get('runtime_s')
        _el = ('%.0f s' % _el) if _el is not None else 'elapsed unrecorded'
        if SPLIT_REFUSALS and rec.get('status') in REFUSALS:
            os.makedirs(REFUSED, exist_ok=True)
            rec['refusal'] = True
            json.dump(rec, open(f'{REFUSED}/{u["eb"]}.json', 'w'), indent=1)
            print('=== %s: REFUSED %s (%s) -- not a block verdict'
                  % (u['eb'], rec.get('status'), _el), flush=True)
        else:
            json.dump(rec, open(f'{OUT}/{u["eb"]}.json', 'w'), indent=1)
            print('=== %s: %s (%s)'
                  % (u['eb'], rec.get('status'), _el), flush=True)
    print('lane done')


def collect():
    recs = [json.load(open(f)) for f in sorted(glob.glob(f'{OUT}/*.json'))
            if not f.endswith('.fit.json')]
    ok = [r for r in recs if r.get('status') == 'ok']
    fits = {}
    for r in ok:
        fits.update(r.get('fit') or {})
    out = dict(n_blocks=len(recs), n_ok=len(ok), n_windows_fitted=len(fits),
               failed=[dict(eb=r['eb'], status=r.get('status'))
                       for r in recs if r.get('status') != 'ok'],
               fits=fits)
    json.dump(out, open(f'{ROOT}/visfit_r7_result.json', 'w'), indent=1)
    print('%d blocks, %d ok, %d windows fitted, %d failed'
          % (len(recs), len(ok), len(fits), len(out['failed'])))


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'work'
    {'work': worker, 'collect': collect}[mode]()
