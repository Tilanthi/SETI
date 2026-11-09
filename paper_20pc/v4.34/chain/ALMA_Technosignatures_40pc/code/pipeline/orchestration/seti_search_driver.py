#!/usr/bin/env python3
"""
Sequential driver for the 100-star SETI search. Processes targets ONE AT A
TIME, in ranked priority order, from ranked_top100.csv, shelling out to
process_one_target.sh (which does the actual disk/load-governed work) for
each. Written in Python rather than bash specifically for robust CSV
parsing -- ranked_top100.csv has quoted, comma-containing fields (e.g.
alma_bands="3,6,9") that a naive `IFS=',' read` would mis-split.

MULTI-BAND (added 2026-08-26 per Glenn's instruction): a target's public
ALMA coverage often spans more than one band, and the pipeline previously
only ever processed one (whichever calibrated first, prioritised by finest
resolution regardless of band). Now, for each target, every distinct band
found in band_mous.json is processed as its own independent, fully-governed
"work item" (own directory, own DONE/FAILED marker, own timeout/disk
watchdog/cleanup) -- capped at SETI_MAX_BANDS_PER_TARGET (default 4) so a
handful of extremely richly-observed targets (e.g. PDS 70, 8 bands) can't
dominate the whole run's time budget; anything beyond the cap is left for a
later, explicit follow-up pass rather than processed inline here.

Usage: seti_search_driver.py [start_rank] [end_rank]
"""
import csv, subprocess, sys, time, json, os, signal, glob


def safe_target_name(name):
    """MUST exactly match process_one_target.sh's own SAFE_NAME computation
    (`tr ' /()' '____' | tr -cd 'A-Za-z0-9_-'`), since this is used purely to
    figure out which directory to clean up -- a previous version of this
    function used Python's own ad-hoc sanitisation (replacing any non-alnum
    character with '_' instead of first translating space/slash/parens and
    then DELETING anything left over), which produced a DIFFERENT path than
    the one process_one_target.sh actually created for any multi-band name
    containing brackets, e.g. 'TW Hya (Gaia DR3 ...) [B6]'. The mismatch
    meant this driver's "unconditional cleanup" was silently cleaning a
    directory that didn't exist, while the real one was never touched --
    found this 2026-08-27 after TW Hya alone accumulated 182 GB of
    uncleaned raw/work/products data and helped push disk into an emergency-
    watchdog cascade that failed ~30 subsequent targets in 30 seconds each.
    """
    translated = ''.join('_' if c in ' /()' else c for c in name)
    return ''.join(c for c in translated if c.isalnum() or c in '_-')

# Configurable via env vars (added 2026-08-28 for the <20pc volume-limited
# follow-up survey) so a second, independently-tracked run can reuse this
# same driver against a different target list/MOUS mapping/summary file,
# without touching the defaults the ranks-1-100 run already depends on.
CSV = os.environ.get('SETI_TARGET_CSV', '/data/SETI/targets/ranked_top100.csv')
ALT_MOUS = os.environ.get('SETI_ALT_MOUS', '/data/SETI/targets/alt_mous.json')
BAND_MOUS = os.environ.get('SETI_BAND_MOUS', '/data/SETI/targets/band_mous.json')
BIN = '/data/SETI/bin'
LOGDIR = '/data/SETI/logs'
os.makedirs(LOGDIR, exist_ok=True)

alt_mous = json.load(open(ALT_MOUS)) if os.path.exists(ALT_MOUS) else {}
band_mous = json.load(open(BAND_MOUS)) if os.path.exists(BAND_MOUS) else {}
MAX_BANDS_PER_TARGET = int(os.environ.get('SETI_MAX_BANDS_PER_TARGET', 4))

start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
end = int(sys.argv[2]) if len(sys.argv) > 2 else 100

print(f'### SETI search driver starting {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, '
      f'ranks {start}-{end}, multi-band (max {MAX_BANDS_PER_TARGET}/target) ###', flush=True)

with open(CSV, newline='') as f:
    rows = list(csv.DictReader(f))

summary_path = os.environ.get('SETI_SUMMARY_PATH', f'{LOGDIR}/driver_summary.json')
summary = json.load(open(summary_path)) if os.path.exists(summary_path) else {}


def work_items_for(row):
    """Yield (work_key, display_name, mous_list) for every band this target
    has public ALMA coverage in (capped), or a single legacy (no-band-tag)
    item if band_mous.json has no entry for this star."""
    rank = int(row['rank'])
    name = row['name']
    by_band = band_mous.get(str(rank))
    if not by_band:
        mous_list = alt_mous.get(str(rank), [row['alma_best_mous']])
        yield str(rank), name, mous_list
        return
    bands = sorted(by_band.keys(), key=lambda b: int(b))
    skipped = bands[MAX_BANDS_PER_TARGET:]
    bands = bands[:MAX_BANDS_PER_TARGET]
    if skipped:
        print(f'  [{name}] {len(skipped)} additional band(s) {skipped} beyond the '
              f'{MAX_BANDS_PER_TARGET}-band cap -- deferred to a later follow-up pass, '
              f'not processed now', flush=True)
    for band in bands:
        yield f'{rank}_B{band}', f'{name} [B{band}]', by_band[band]


# Per-star orbital-acceleration-based drift-rate search widening (2026-08-30,
# per Glenn's instruction to account for "possible orbital motions if any
# technosignatures come from planets orbiting the star"). Generalises the
# earlier TRAPPIST-1-specific hardcoded drift bound: for every one of the
# 120 volume-limited targets, the NASA Exoplanet Archive was checked for
# confirmed planets; where present, the innermost (shortest-period, highest
# line-of-sight-acceleration) planet's own orbital motion sets a drift-rate
# floor via drift_Hz_per_s = nu * 4*pi^2*a / (P^2 * c), compared against the
# existing generic Mason et al. (2024) Eq.7-based default (12.0 Hz/s per
# GHz, itself already a x3 safety margin) and the WIDER of the two used.
# Only TRAPPIST-1 (planet b, P=1.51d) actually exceeds the generic default
# (13.34 vs 12.0 Hz/s/GHz) -- every other confirmed system in the sample is
# already covered by the existing generic bound. See
# /data/SETI/targets/drift_coeffs.json for the full per-star calculation
# (17 confirmed-planet hosts checked, kept for the eventual write-up table).
DRIFT_COEFFS_PATH = os.environ.get('SETI_DRIFT_COEFFS', '/data/SETI/targets/drift_coeffs.json')
try:
    DRIFT_COEFFS = json.load(open(DRIFT_COEFFS_PATH))
except Exception:
    DRIFT_COEFFS = {}

# Per-target wall-clock timeout overrides (added 2026-09-01 per Glenn):
# a handful of the most heavily-observed nearby stars (AU Mic, HD 69830,
# eps Eri, HN Lib, lp 876-10) have enough archival ALMA data that
# calibration+search alone consumes most of the standard 90-min
# (SETI_MAX_TARGET_SECONDS default 5400s) budget, leaving the continuum_map
# step (full tclean over all EBs/spws, the single slowest stage) almost no
# time -- these were repeatedly getting killed mid-continuum-map as
# TRANSIENT_FAILURE and cycling through retries without ever finishing. See
# /data/SETI/targets/timeout_overrides.json for the current override list
# (target base name -> seconds); anything not listed there keeps the
# standard default. Matched the same way as DRIFT_COEFFS, against both the
# bracket-stripped base_name and the raw work-item name.
TIMEOUT_OVERRIDES_PATH = os.environ.get('SETI_TIMEOUT_OVERRIDES', '/data/SETI/targets/timeout_overrides.json')
# NOTE (2026-09-02): deliberately re-read FRESH inside run_one() on every
# invocation (see load_timeout_overrides() below) rather than loaded once
# here at import time -- this driver runs for many hours/days per pass, and
# we want to be able to add newly-discovered slow-but-genuine targets to
# timeout_overrides.json on the fly without having to kill and restart the
# whole (already multi-hour-invested) driver process just to pick them up.


def load_timeout_overrides():
    try:
        return json.load(open(TIMEOUT_OVERRIDES_PATH))
    except Exception:
        return {}


def run_one(work_key, rank, name, mous_list, row):
    mous_csv = ','.join(mous_list)
    ra, dec = row['ra'], row['dec']
    pmra, pmdec = row['pmra'], row['pmdec']
    dist_pc = float(row['dist_pc'])
    parallax_mas = 1000.0 / dist_pc if dist_pc > 0 else 1.0
    parallax_err_mas = 0.001  # not carried in the CSV; negligible for l/m offset purposes

    print(f'\n=== [{work_key}] {name}  ({len(mous_list)} candidate MOUS) === '
          f'{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}', flush=True)
    t0 = time.time()
    base_name_for_timeout = name.split(' [B')[0].strip()
    _timeout_overrides_now = load_timeout_overrides()
    _timeout_override = _timeout_overrides_now.get(base_name_for_timeout) or _timeout_overrides_now.get(name)
    if _timeout_override:
        MAX_TARGET_SECONDS = int(_timeout_override)
        print(f'[{name}] using overridden wall-time cap of {MAX_TARGET_SECONDS}s '
              f'(default is {int(os.environ.get("SETI_MAX_TARGET_SECONDS", 5400))}s) '
              f'per timeout_overrides.json', flush=True)
    else:
        MAX_TARGET_SECONDS = int(os.environ.get('SETI_MAX_TARGET_SECONDS', 5400))
    child_env = os.environ.copy()
    base_name = name.split(' [B')[0].strip()
    coeff_info = DRIFT_COEFFS.get(base_name) or DRIFT_COEFFS.get(name)
    if coeff_info:
        child_env['SETI_DRIFT_COEFF'] = str(coeff_info['final_coeff_hz_per_ghz'])
        if coeff_info.get('widened'):
            print(f'  [{name}] drift search WIDENED to '
                  f'{coeff_info["final_coeff_hz_per_ghz"]:.2f} Hz/s/GHz for '
                  f'{coeff_info["innermost_planet"]}\'s own orbital motion '
                  f'(generic default was {coeff_info["generic_coeff_hz_per_ghz"]:.1f})',
                  flush=True)
    proc = subprocess.Popen(
        ['bash', f'{BIN}/process_one_target.sh', str(rank), name, mous_csv,
         ra, dec, pmra, pmdec, str(parallax_mas), str(parallax_err_mas)],
        start_new_session=True, env=child_env,
    )
    safe_name = safe_target_name(name)
    tdir = f'/data/SETI/targets/{safe_name}'
    EMERGENCY_FREE_GB = int(os.environ.get('SETI_EMERGENCY_FREE_GB', 80))
    WATCHDOG_POLL_S = 30
    t_wait0 = time.time()
    rc = None
    while True:
        try:
            rc = proc.wait(timeout=WATCHDOG_POLL_S)
            break
        except subprocess.TimeoutExpired:
            pass
        if time.time() - t_wait0 > MAX_TARGET_SECONDS:
            print(f'[{name}] EXCEEDED {MAX_TARGET_SECONDS}s wall-time cap -- '
                  f'killing entire process group and moving on', flush=True)
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            rc = 124
            break
        st = os.statvfs('/data')
        free_gb = st.f_bavail * st.f_frsize / 1e9
        if free_gb < EMERGENCY_FREE_GB:
            print(f'[{name}] *** EMERGENCY: only {free_gb:.0f} GB free '
                  f'(< {EMERGENCY_FREE_GB} GB) -- killing this target '
                  f'immediately regardless of wall-clock budget ***', flush=True)
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            rc = 125
            break
    if rc in (124, 125):
        # NOTE: deliberately NOT writing logs/FAILED here (found during the
        # 2026-08-27 governance audit) -- process_one_target.sh treats that
        # exact filename as a PERMANENT skip signal (used correctly for
        # real data problems like "no usable calibration recipe"), but a
        # timeout or disk-emergency kill is a transient resource condition,
        # not a verdict on the target's data. Writing FAILED here would
        # silently no-op every future retry attempt (process_one_target.sh
        # exits 0 immediately without doing anything), which would then be
        # wrongly recorded as a successful completion. Use a distinctly
        # named, non-gating marker purely for human-readable bookkeeping;
        # this driver's own summary.json (rc != 0) is what actually governs
        # retry eligibility.
        os.makedirs(f'{tdir}/logs', exist_ok=True)
        open(f'{tdir}/logs/TRANSIENT_FAILURE', 'w').write(
            'timed out\n' if rc == 124 else 'killed by disk-emergency watchdog\n')
    # UNCONDITIONAL reclaim, run after every attempt regardless of exit path
    # (success/failure/timeout/abnormal signal death) -- covers raw/, work/,
    # and any leftover products/*.ms (see 2026-08-26 incident notes in git
    # history for why both are needed: raw/work for early-stage deaths,
    # products/*.ms for deaths during extract/search/continuum-map, after
    # calibration has already split its output there).
    for sub in ('raw', 'work'):
        d = f'{tdir}/{sub}'
        if os.path.isdir(d):
            sz = subprocess.run(['du', '-sh', d], capture_output=True, text=True).stdout.split('\t')[0]
            print(f'[{name}] outer-driver reclaim: removing leftover {d} ({sz})', flush=True)
            subprocess.run(['rm', '-rf', d])
    for ms in glob.glob(f'{tdir}/products/*.ms'):
        sz = subprocess.run(['du', '-sh', ms], capture_output=True, text=True).stdout.split('\t')[0]
        print(f'[{name}] outer-driver reclaim: removing leftover {ms} ({sz})', flush=True)
        subprocess.run(['rm', '-rf', ms])
    dt = time.time() - t0
    summary[work_key] = dict(name=name, mous_candidates=mous_list, rc=rc,
                              seconds=round(dt, 1),
                              finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    json.dump(summary, open(summary_path, 'w'), indent=1)
    status = 'OK' if rc == 0 else f'FAILED (rc={rc})'
    print(f'=== [{work_key}] {name}: {status} in {dt:.0f}s ===', flush=True)

    if rc == 125:
        # Architectural fix from the 2026-08-27 governance audit: previously
        # the driver moved straight on to the NEXT target immediately after
        # an emergency kill. If that target's own cleanup wasn't what was
        # needed to fix the disk state (e.g. the pressure came from
        # elsewhere, or reclaim genuinely wasn't enough), the very next
        # target would hit the same 80 GB emergency line within its own
        # first 30-second poll and die too -- and the one after that, and
        # so on. This is exactly what turned one real incident into ~145
        # wrongly-failed work items on 2026-08-26/27. Pause the WHOLE
        # driver here and don't attempt another target until disk is back
        # to a comfortable margin above the governor's normal floor, not
        # just above the bare emergency line.
        RECOVERY_TARGET_GB = int(os.environ.get('SETI_RECOVERY_TARGET_GB', 200))
        waited = 0
        while True:
            st = os.statvfs('/data')
            free_gb = st.f_bavail * st.f_frsize / 1e9
            if free_gb >= RECOVERY_TARGET_GB:
                print(f'[driver] disk recovered to {free_gb:.0f} GB free '
                      f'(>= {RECOVERY_TARGET_GB} GB target) -- resuming', flush=True)
                break
            print(f'[driver] PAUSED after emergency kill: {free_gb:.0f} GB free, '
                  f'waiting for >= {RECOVERY_TARGET_GB} GB before attempting another '
                  f'target ({waited}s waited so far)', flush=True)
            time.sleep(60)
            waited += 60


for row in rows:
    rank = int(row['rank'])
    if rank < start or rank > end:
        continue
    for work_key, disp_name, mous_list in work_items_for(row):
        if work_key in summary and summary[work_key].get('rc') == 0:
            print(f'[{disp_name}] already done (rc=0), skipping', flush=True)
            continue
        run_one(work_key, rank, disp_name, mous_list, row)

print(f'### driver finished {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())} ###', flush=True)
n_ok = sum(1 for v in summary.values() if v['rc'] == 0)
n_fail = sum(1 for v in summary.values() if v['rc'] != 0)
print(f'### {n_ok} succeeded, {n_fail} failed, {len(summary)} attempted total ###', flush=True)
