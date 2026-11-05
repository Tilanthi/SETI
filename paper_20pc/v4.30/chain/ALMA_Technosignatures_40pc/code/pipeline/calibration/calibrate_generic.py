#!/usr/bin/env python3
"""
Generic, auto-detecting ALMA calibration-replay pipeline for the 100-star
SETI search. Generalises the three project-specific pipelines built for
the TRAPPIST-1 work (Band 3/6/7) into one script that works across
arbitrary ALMA projects without per-project hand-tuning, since this run
processes ~100 different projects unattended.

Auto-detected per EB (no hardcoded field/spw/calibrator names):
  - the target field: whichever field has TARGET intent in calapply.txt
  - science spws: parsed directly from calapply.txt's own spw='...' list
    (the pipeline's own calibration already excludes WVR/pointing/SQLD
    windows from this list, so it is a reliable, generic indicator)
  - calibrator field identities: classified by INTENT (BANDPASS/AMPLITUDE
    vs PHASE), not by name, since these vary per EB even within one
    project (found during the TRAPPIST-1 Band-6/7 follow-up work)
  - a stale/partial ASDM extraction directory is detected and re-extracted
    rather than silently trusted (found during the TRAPPIST-1 work)

On any failure this exits with a non-zero code and a clear log message;
the calling driver is expected to log the failure and move on to the next
target rather than treat it as fatal to the whole run.

Runs everything through the shared resource governor (nice/ionice, disk
and load checks) -- see governor.sh.

Usage: calibrate_generic.py <target_dir> <mous_uid> <max_cores>
  target_dir: e.g. /data/SETI/targets/tau_Cet
  mous_uid:   e.g. uid://A001/X121/X3b9
"""
import os, re, sys, glob, json, time, shutil, subprocess, tarfile

TARGET_DIR = sys.argv[1]
MOUS = sys.argv[2]
MAX_CORES = int(sys.argv[3]) if len(sys.argv) > 3 else 8

RAW = f'{TARGET_DIR}/raw'
WORK = f'{TARGET_DIR}/work'
PROD = f'{TARGET_DIR}/products'
LOGD = f'{TARGET_DIR}/logs'
for d in (RAW, WORK, PROD, LOGD):
    os.makedirs(d, exist_ok=True)

STATUS = f'{LOGD}/calibrate_status.json'
os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
os.environ.setdefault('OMP_NUM_THREADS', '1')

rec = {'mous': MOUS, 'target_dir': TARGET_DIR, 'ebs': {}, 'errors': []}


def save():
    json.dump(rec, open(STATUS, 'w'), indent=1)


def log(msg):
    print(f'[calibrate_generic] {msg}', flush=True)


def fail(msg):
    log(f'FATAL: {msg}')
    rec['errors'].append(msg)
    rec['done'] = False
    save()
    sys.exit(1)


# ---------------------------------------------------------------- download
def mous_to_pathstub(m):
    # uid://A001/X121/X3b9 -> A001_X121_X3b9  (matches ALMA's own file naming)
    return m.replace('uid://', '').replace('/', '_')


from astroquery.alma import Alma
import warnings
warnings.filterwarnings('ignore')
Alma.archive_url = 'https://almascience.eso.org'


def alma_file_list(mous):
    info = Alma.get_data_info(mous, expand_tarfiles=False)
    asdm, aux, sizes = [], None, {}
    for row in info:
        u = str(row['access_url'])
        fname = u.split('/')[-1]
        # astropy Table columns can be masked (missing value for some
        # rows), which raises numpy.ma.core.MaskError on int() rather than
        # a plain ValueError/TypeError -- catch broadly here (any failure
        # just means "size unknown", handled cautiously downstream), since
        # this function must never itself be why a target fails outright.
        try:
            v = row['content_length']
            if hasattr(v, 'mask') and bool(getattr(v, 'mask', False)):
                sizes[fname] = None
            else:
                sizes[fname] = int(v)
        except Exception:
            sizes[fname] = None
        if u.endswith('.asdm.sdm.tar'):
            asdm.append(fname)
        elif u.endswith('_auxiliary.tar'):
            aux = fname
    return asdm, aux, sizes


def free_bytes(path='/data'):
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize


def gentle_download(fname, destdir):
    """Single-mirror, modest-concurrency, watchdog-protected download --
    deliberately gentler than the multi-mirror/high-concurrency downloader
    built for the TRAPPIST-1 work, since this run must minimise its
    footprint on shared infrastructure, not maximise throughput.

    2026-09-05 fix: a prior version always passed -c (resume) to aria2c on
    every retry. If a partial/control file is stale or the server returns
    416 (Range Not Satisfiable) for a resume attempt, every subsequent
    retry re-attempts the exact same broken resume and fails identically
    -- this was found to be the single largest cause of permanent-skip
    failures in the survey (25/61, 41%). Fix: on any failed attempt,
    delete the partial file and its .aria2 control file before retrying,
    so the next attempt is a clean, non-resumed download rather than a
    repeat of a broken resume."""
    out = f'{destdir}/{fname}'
    if os.path.exists(out) and not os.path.exists(out + '.aria2'):
        return out
    mirror = 'https://almascience.nao.ac.jp/dataPortal'
    for attempt in range(1, 6):
        # 2026-09-14: escalate to a single, non-ranged stream after two
        # failures.  -x4/-s4/-c make aria2c issue byte-range requests; the
        # data portal answers 416 for some files, so every attempt failed
        # identically no matter how often the stale partial was cleared.
        # A request with no Range header returns 200, so attempts 3+ drop
        # the splitting and the resume flag entirely.
        if attempt <= 2:
            speed = ['-x4', '-s4', '-c']
        else:
            speed = ['-x1', '-s1', '--max-concurrent-downloads=1',
                     '--always-resume=false', '--allow-overwrite=true']
            log(f'{fname}: attempt {attempt} falling back to a single '
                f'non-ranged stream (416-class failure)')
        cmd = (['nice', '-n', '19', 'ionice', '-c3', 'aria2c']
               + speed
               + ['-k20M', '--file-allocation=none',
                  '--console-log-level=warn', '--max-tries=6',
                  '--retry-wait=15', '--lowest-speed-limit=512K',
                  '--connect-timeout=15', '--timeout=30',
                  '-d', destdir, '-o', fname, f'{mirror}/{fname}'])
        subprocess.run(cmd, check=False)
        if os.path.exists(out) and not os.path.exists(out + '.aria2'):
            return out
        log(f'download attempt {attempt} incomplete for {fname}, retrying '
            f'(clearing any stale partial/resume state first)')
        # Always clear stale partial/control state before retrying -- a
        # partial file that failed to complete should not be blindly
        # resumed again. This is the fix for the diagnosed 416
        # (Range Not Satisfiable) failure class, where -c kept resuming
        # from the same broken offset every retry and failed identically
        # 5/5 times; safe in general since aria2c simply starts fresh.
        # (Deliberately NOT using capture_output=True here -- aria2c's
        # live stdout/stderr streaming into this process's own stdout is
        # relied on for progress monitoring of large, genuinely slow
        # downloads; capturing it would hide that.)
        for stale in (out, out + '.aria2'):
            try:
                if os.path.exists(stale):
                    os.remove(stale)
            except OSError as e:
                log(f'could not remove stale file {stale}: {e}')
        time.sleep(10)
    fail(f'could not download {fname} after 5 attempts')


t0 = time.time()
asdm_files, aux_file, asdm_sizes = alma_file_list(MOUS)
if not asdm_files:
    fail(f'no ASDM files found for MOUS {MOUS}')
log(f'{len(asdm_files)} EB(s) for {MOUS}, aux={aux_file}')
# Cap the number of execution blocks actually calibrated per target. This
# survey is explicitly a secondary/background task across 100 targets --
# some targets have dozens of archival EBs, and fully calibrating every
# one of them would let a single richly-observed target dominate the
# whole run's compute/disk/time budget at the expense of the other 99.
# A handful of EBs is already enough integration time for a first-pass
# narrowband search and a usable continuum map; depth beyond that is a
# candidate for later, targeted follow-up rather than the first pass.
MAX_EBS = int(os.environ.get('SETI_MAX_EBS_PER_TARGET', '3'))
if len(asdm_files) > MAX_EBS:
    log(f'capping to the first {MAX_EBS} of {len(asdm_files)} EBs '
        f'(SETI_MAX_EBS_PER_TARGET) to bound this target\'s resource use')
    asdm_files = asdm_files[:MAX_EBS]

# --- size-aware download budget (added after the PDS 70 incident, where a
# single richly-observed target's EBs were individually tens of GB each --
# the 3-EB *count* cap alone let one target consume the disk's entire free
# headroom in a single download, since nothing checked cumulative BYTES
# before/during downloading, only free space once at target-start). Query
# each candidate EB's real size (ALMA exposes this via content_length,
# no download needed) and skip any EB that would breach either a hard
# per-target download ceiling or the shared floor with a safety margin,
# rather than trusting a fixed EB *count* to bound worst-case size.
# Tightened 2026-08-27 after TW Hya: a ~37 GB raw download (correctly
# bounded by the budget below) still expanded to ~133 GB of working data
# during import/calibration/split (~3.6x) plus another ~49 GB left in
# products/ -- ASDM-to-MS conversion and multi-step CASA processing (import
# -> flag -> mstransform -> applycal -> split) each keep their own copy of
# the data along the way. The budget below governs raw DOWNLOAD bytes only;
# it was not accounting for this multiplication, so a "safe" 40 GB download
# could still balloon past several times that in practice. Lowered the cap
# and raised the margin so worst-case peak footprint per target stays
# comfortably bounded even accounting for this expansion.
#
# Rebalanced 2026-08-28: the 25 GB cap over-corrected and started rejecting
# EVERY EB for targets whose individual execution blocks are themselves
# 35-41 GB (e.g. LP 876-10) -- an entirely legitimate, safe download given
# 300+ GB is typically free, just larger than the fixed cap allowed even
# for a single EB. The SAFETY_MARGIN_GB check (compared against *current*
# free disk, not a fixed total) is the check that actually prevents a
# repeat of the TW Hya incident; the fixed cap only needs to stop
# *multiple* large EBs stacking up unboundedly, so raising it back to
# comfortably cover one large EB while still capping well below what 3
# such EBs would sum to is the correct balance.
# Raised 2026-08-31 per Glenn's explicit instruction ("you can exceed the
# self-imposed download-budget cap if need be") after 4 targets -- HD 69830,
# GJ14, G 3-14, 1RXS J0336+3118 -- were found permanently skipped purely
# because their only available EB(s) are 50-80 GB each, just above the
# previous 45 GB cap (largest single-EB minimum required: GJ14's 66.9 GB).
# This fixed cap is NOT the only safety net -- the SAFETY_MARGIN_GB check
# just below independently verifies against REAL, live free disk space at
# download time (currently 340+ GB free, so an 85 GB cap leaves a huge
# margin under that check too), and the outer driver's EMERGENCY_FREE_GB
# watchdog (80 GB, polled every 30s during processing) remains the final
# backstop against the ~3.6x on-disk expansion these large downloads
# undergo during import/calibration/split. Raised just enough to cover the
# 4 known cases with headroom, not opened up unboundedly.
# 2026-09-18: ported in from the epoch_extension copy so that ONE file can
# serve both callers. The two had diverged, and the divergence cost 11 blocks:
# the 2026-09-14 sys.path fix below was applied here but never to the copy the
# sweep driver actually executes, so every early-cycle block that reached the
# legacy replay died on ModuleNotFoundError. A no-op when unset.
_ONLY = os.environ.get('SETI_ONLY_EB')
if _ONLY:
    asdm_files = [f for f in asdm_files if _ONLY in f]
    log('SETI_ONLY_EB=%s -> %d EB(s) kept' % (_ONLY, len(asdm_files)))
MAX_TARGET_DOWNLOAD_GB = float(os.environ.get('SETI_MAX_TARGET_DOWNLOAD_GB', '85'))
SAFETY_MARGIN_GB = float(os.environ.get('SETI_DOWNLOAD_SAFETY_MARGIN_GB', '100'))
downloaded_bytes = 0
kept = []
for fn in asdm_files:
    sz = asdm_sizes.get(fn)
    free_now_gb = free_bytes() / 1e9
    if sz is None:
        # Unknown size (e.g. a masked/missing archive metadata field) --
        # fail closed rather than silently trusting it: only proceed if
        # the FULL per-target budget still fits under the current free
        # margin, since we have no upper bound on what this file might
        # be. (Not purely theoretical -- this is exactly the metadata gap
        # hit on some of PDS 70's 33 candidate MOUS during the incident
        # that motivated this whole size-aware rewrite.)
        if (free_now_gb - SAFETY_MARGIN_GB) < (MAX_TARGET_DOWNLOAD_GB - downloaded_bytes / 1e9):
            log(f'  SKIPPING {fn}: size unknown (archive metadata gap) and '
                f'not enough margin ({free_now_gb:.0f} GB free) to safely '
                f'assume worst-case size -- treat this MOUS as unusable '
                f'rather than risk it')
            continue
        log(f'  WARNING: no size metadata for {fn}, proceeding cautiously '
            f'(budget/margin checked against a worst-case assumption; '
            f'also covered by the outer driver\'s live disk watchdog)')
    else:
        sz_gb = sz / 1e9
        if (downloaded_bytes + sz) / 1e9 > MAX_TARGET_DOWNLOAD_GB:
            log(f'  SKIPPING {fn} ({sz_gb:.1f} GB): would exceed this target\'s '
                f'{MAX_TARGET_DOWNLOAD_GB:.0f} GB download budget '
                f'({downloaded_bytes/1e9:.1f} GB already queued)')
            continue
        if (free_now_gb - sz_gb) < SAFETY_MARGIN_GB:
            log(f'  SKIPPING {fn} ({sz_gb:.1f} GB): only {free_now_gb:.0f} GB free, '
                f'downloading it would leave < {SAFETY_MARGIN_GB:.0f} GB safety margin')
            continue
    kept.append(fn)
    downloaded_bytes += sz or 0
asdm_files = kept
if not asdm_files:
    fail(f'no EB of {MOUS} fits within the per-target download budget/safety margin')
log(f'download budget: {len(asdm_files)} EB(s) kept, '
    f'~{downloaded_bytes/1e9:.1f} GB planned (cap {MAX_TARGET_DOWNLOAD_GB:.0f} GB)')
rec['n_ebs'] = len(asdm_files)
save()

# Fixed 2026-08-31 after finding this crash live (LP 649-72, G 70-43,
# G 70-44): if this MOUS's file listing has no "_auxiliary.tar" entry at
# all, alma_file_list() leaves aux_file as None -- previously this was
# passed straight into gentle_download(), which embeds the raw fname
# argument into its subprocess.run() command list, crashing with an
# opaque "TypeError: expected str, bytes or os.PathLike object, not
# NoneType" from deep inside fork_exec rather than a clear, actionable
# message. A missing auxiliary tar means there is no calibration/
# directory to extract at all, which is functionally the same situation
# as the "no casa_commands.log found" case already handled gracefully
# below -- fail with an equally clear, correctly-categorised message
# instead of an uncaught exception.
if aux_file is None:
    fail(f'no auxiliary tar (_auxiliary.tar) found in the file listing for '
         f'{MOUS} -- no calibration/ directory available to extract, likely '
         f'a non-standard or pre-pipeline delivery format for this MOUS')

aux_path = gentle_download(aux_file, RAW)
extract_root = f'{WORK}/aux'


def _extraction_looks_valid(root):
    """A directory tree only counts as a valid, complete previous
    extraction if it has BOTH a calibration/ dir AND something usable
    inside it (a casa_commands.log to replay, or a calapply.txt-driven
    per-EB caltable setup) -- not merely the calibration/ dir's mere
    presence.

    2026-09-05 fix: a directory that has calibration/ but is missing
    script/ or log/ (e.g. because a PRIOR run of this script was killed
    mid-extraction by the driver's wall-clock watchdog, a container
    restart, or any other abrupt termination that bypassed
    process_one_target.sh's own "rm -rf raw work" cleanup) was being
    silently treated as "already extracted, nothing to do" on every
    subsequent retry -- clearing a target's FAILED marker/summary-cache
    entry does NOT touch raw/work directory *contents*, and
    process_one_target.sh's `mkdir -p "$TDIR"/{raw,work,...}` preserves
    any pre-existing files/dirs rather than cleaning them. This
    masqueraded as a permanent "no casa_commands.log found"
    data-availability limitation for datasets that in fact have a
    perfectly good commands log -- independently verified against the
    live ALMA archive for several affected targets (e.g.
    2018.1.01833.S/uid___A001_X133d_X36a2 downloads and extracts cleanly
    via the exact same aria2c invocation used here, byte-identical to a
    plain curl fetch, and contains
    script/*.hifa_calimage.casa_commands.log all along) -- this was
    always a stale-extraction bug, not a genuine format gap, for cases
    like that one."""
    caldirs_ = glob.glob(f'{root}/**/calibration', recursive=True)
    if not caldirs_:
        return False
    mousdir_ = os.path.dirname(caldirs_[0])
    has_cmdlog = bool(
        glob.glob(f'{mousdir_}/**/*calimage*commands.log', recursive=True) or
        glob.glob(f'{mousdir_}/**/*.casa_commands.log', recursive=True) or
        glob.glob(f'{mousdir_}/**/*commands.log', recursive=True))
    has_calapply = bool(glob.glob(f'{caldirs_[0]}/*.ms.calapply.txt'))
    return has_cmdlog or has_calapply


if not _extraction_looks_valid(extract_root):
    shutil.rmtree(extract_root, ignore_errors=True)
    os.makedirs(extract_root, exist_ok=True)
    subprocess.run(['tar', 'xf', aux_path, '-C', extract_root], check=True)
os.remove(aux_path)
log(f'extract_aux: {time.time()-t0:.0f}s')

caldirs = glob.glob(f'{extract_root}/**/calibration', recursive=True)
if not caldirs:
    fail('no calibration/ directory found in auxiliary tar -- this MOUS may '
         'predate ALMA pipeline calibration or use a non-standard delivery')
CALSRC = caldirs[0]
MOUSDIR = os.path.dirname(CALSRC)
# The casa_commands.log naming convention varies across pipeline/cycle
# versions -- e.g. "<MOUS>.hifa_calimage.casa_commands.log" (newer,
# TRAPPIST-1-era projects) vs plain "<MOUS>.casa_commands.log" (older
# projects, e.g. Cycle 4/2016). Try progressively more permissive patterns
# rather than a single hardcoded one; prefer a calimage-tagged one if
# several are present (it is the one containing the full calibration
# recipe, as opposed to e.g. a science-imaging-only commands log).
# 2026-09-05 fix: the casa_commands.log lives under different subdirectory
# names depending on delivery format -- 'log/' in some deliveries, 'script/'
# in others (found live: 2018.1.01833.S/.../script/*.hifa_calimage.casa_
# commands.log has no 'log/' dir at all, only calibration/qa/script/ -- this
# was silently mis-diagnosed as no casa_commands.log found for every MOUS
# using this delivery convention, when the file was present all along).
# Search recursively under MOUSDIR instead of assuming one fixed subdirectory
# name, trying the same three patterns in the same preference order.
cmdlogs = (glob.glob(f'{MOUSDIR}/**/*calimage*commands.log', recursive=True) or
           glob.glob(f'{MOUSDIR}/**/*.casa_commands.log', recursive=True) or
           glob.glob(f'{MOUSDIR}/**/*commands.log', recursive=True))
# 2026-09-06 addition: some genuinely older deliveries (pre-dating the
# automated pipeline's casa_commands.log/calapply.txt convention
# entirely -- Cycle-1/2/3-era manual reductions) instead ship a
# per-EB "*.ms.scriptForCalibration.py" containing the FULL, standalone,
# hand-written calibration recipe as literal CASA task calls -- and,
# critically, package every table those calls WOULD produce (WVR, Tsys,
# antpos, bandpass, phase, flux -- confirmed by direct inspection of a
# real delivery, 2015.1.01308.S) as already-computed artifacts in the
# same *.calibration.tgz caught by patch 1. So nothing needs to be
# SOLVED, only the apply/flag/split steps need to be REPLAYED, in
# original order, against pre-existing tables -- no calibration
# derivation, no gaincal/bandpass/setjy re-run. Detect this case instead
# of failing immediately; the per-EB loop below decides whether a given
# EB actually has a matching script.
legacy_scripts = glob.glob(f'{MOUSDIR}/**/*.ms.scriptForCalibration.py', recursive=True)
if not cmdlogs and not legacy_scripts:
    fail('no casa_commands.log found -- cannot auto-replay calibration')
CMDLOG = None
if cmdlogs:
    cmdlogs.sort(key=lambda p: ('calimage' not in p, p))
    CMDLOG = cmdlogs[0]
    log(f'using commands log: {CMDLOG}')
else:
    log(f'no casa_commands.log/calapply.txt found, but {len(legacy_scripts)} '
        f'legacy scriptForCalibration.py file(s) found -- will attempt '
        f'per-EB legacy replay')
CALDIR = f'{WORK}/caltables'
if not os.path.isdir(CALDIR):
    os.makedirs(CALDIR, exist_ok=True)
    # Different ALMA deliveries package the actual .tbl caltables under
    # different filenames -- some as "<MOUS>.caltables.tgz" (per-EB), some
    # as "<MOUS>.session_N.caltables.tar.gz" (session-level, e.g. older
    # Cycle-1/2 deliveries such as AU Mic's 2012.1.00198.S). Catch both,
    # rather than a single hardcoded pattern -- missing this class of file
    # silently leaves referenced .tbl paths nonexistent and applycal fails
    # on every EB for the whole MOUS.
    caltgz = (glob.glob(f'{CALSRC}/*.caltables.tgz') +
              glob.glob(f'{CALSRC}/*.caltables.tar.gz') +
              glob.glob(f'{CALSRC}/*.calibration.tgz'))
    # 2026-09-06 addition: older ("scriptForCalibration.py"-convention)
    # deliveries package ALL calibration tables (early WVR/Tsys/antpos
    # AND late bandpass/gain/flux) per-EB as "<EB>.calibration.tgz",
    # rather than the modern per-stage "*.caltables.tgz" naming. Adding
    # it here means these tables land in the same shared CALDIR the
    # legacy-replay path below expects, via the existing extraction
    # loop -- no separate extraction logic needed.
    if not caltgz:
        log(f'  WARNING: no *.caltables.tgz / *.caltables.tar.gz found in '
            f'{CALSRC} -- if applycal fails with "table does not exist", '
            f'this MOUS uses a caltable packaging convention not yet handled')
    for tgz in caltgz:
        with tarfile.open(tgz) as tf:
            tf.extractall(CALDIR)
log(f'calibration dir: {CALSRC}')


def _strip_comment(line):
    """Strip a trailing '#' comment from a line, but ONLY outside of
    single/double-quoted string literals. A naive line.split('#',1)[0]
    corrupts legitimate values containing a literal '#' character -- e.g.
    ALMA intent strings like 'CALIBRATE_BANDPASS#ON_SOURCE' -- found live
    (2026-09-06) while fixing parse_statements() for scriptForCalibration.py
    replay (see below); this correctly leaves those untouched while still
    stripping genuine end-of-line comments."""
    in_str = None
    for i, ch in enumerate(line):
        if in_str:
            if ch == in_str:
                in_str = None
        elif ch in ("'", '"'):
            in_str = ch
        elif ch == '#':
            return line[:i]
    return line


def parse_statements(path):
    # 2026-09-06 fix: this function was originally written for the flat,
    # machine-generated casa_commands.log format (every real statement
    # starts at column 0, one per physical-logical line, no control flow).
    # Applied unmodified to a legacy scriptForCalibration.py file, it
    # SILENTLY found ZERO replayable statements every time: those files
    # wrap every real CASA task call in an indented
    # "if(mystep in thesteps):" block, so `re.match(r'^[a-z_]+\(', line)`
    # (anchored at column 0) never matches the indented call lines at all
    # -- confirmed live on Wolf 219's real script (2015.1.00783.S): 0/19
    # statements recognised before this fix, 22 real flagdata/applycal/
    # split calls correctly found after it. Fixed by matching against the
    # STRIPPED line instead of the raw (possibly-indented) line. Also
    # strips inline '#' comments per statement (needed because these
    # scripts, unlike casa_commands.log, put comments like "field='0', #
    # J0510+1800" mid-statement; naively joining continuation lines
    # without stripping them first left the comment text of the FIRST
    # physical line syntactically swallowing the rest of the joined
    # statement when exec()'d) -- using the string-literal-aware
    # _strip_comment() above so a legitimate '#' inside a quoted value is
    # never touched. Verified byte-for-byte identical output on a real
    # casa_commands.log (1851/1851 statements, zero differences) before
    # deploying -- this function is shared with the modern-pipeline path
    # and must not regress it.
    out, cur = [], None
    for line in open(path):
        line = _strip_comment(line)
        stripped = line.strip()
        if not stripped:
            continue
        if cur is None:
            # 2026-09-06 further fix: broadened from the original
            # '^[a-z_]+\(' (function-call-only) to also recognise the
            # START of a plain assignment statement ('name = ...', not
            # '=='), needed for scriptForCalibration.py's own helper
            # variables (tsysmap = tsysspwmap(...), calspwmap = {...},
            # listOfIntents = [...]) that later KEEP_PREFIXES statements
            # reference by name -- confirmed these were previously never
            # even entering `stmts` at all (not just filtered out
            # afterward). Verified byte-for-byte no change on a real
            # casa_commands.log (which never contains bare assignment
            # lines) before deploying.
            if re.match(r'^[a-zA-Z_]\w*\s*(\(|=(?!=))', stripped):
                cur = stripped
            else:
                continue
        else:
            cur += ' ' + stripped
        # 2026-09-06 further fix: track [] and {} bracket balance too, not
        # just (). A dict/list literal spanning multiple physical lines
        # (e.g. listOfIntents' 8-line list) has ZERO parens, so the
        # original ()-only check considered it "complete" after just the
        # first physical line, truncating it -- confirmed live: this
        # broke the very listOfIntents capture this fix exists for, until
        # this was added too.
        if (cur.count('(') - cur.count(')') <= 0 and
                cur.count('[') - cur.count(']') <= 0 and
                cur.count('{') - cur.count('}') <= 0):
            out.append(re.sub(r'\s+', ' ', cur))
            cur = None
    return out


from casatasks import importasdm, applycal, split, flagdata, mstransform, listobs

pathstub_map = {mous_to_pathstub(MOUS.split('/')[-1]): None}  # unused placeholder

processed = []
for asdm_fname in asdm_files:
    # EB identifier: e.g. "2013.1.00588.S_uid___A002_X..._X....asdm.sdm.tar"
    m = re.search(r'uid___(A00\d_[^.]+)\.asdm\.sdm\.tar', asdm_fname)
    if not m:
        rec['errors'].append(f'unparseable filename {asdm_fname}, skipped')
        continue
    EB = m.group(1)
    _resume_ms = f'{PROD}/{EB}_target.ms'
    if os.path.isdir(_resume_ms) and os.path.exists(f'{_resume_ms}/table.dat'):
        log(f'--- EB {EB} --- already calibrated (found {_resume_ms}), skipping re-download/re-cal')
        processed.append(dict(eb=EB, ms=_resume_ms, spws=None, target_field=None))
        rec['ebs'][EB] = dict(ms=_resume_ms, spws=None, target_field=None,
                               ok=True, resumed_from_existing=True)
        save()
        continue
    log(f'--- EB {EB} ---')
    t0 = time.time()
    ASDMD = f'{WORK}/asdm_{EB}'
    MS = f'{WORK}/uid___{EB}.ms'
    CMP = f'{WORK}/{EB}_compact.ms'

    calapply_path = f'{CALSRC}/uid___{EB}.ms.calapply.txt'
    if not os.path.exists(calapply_path):
        # 2026-09-06: fall back to a legacy scriptForCalibration.py
        # replay before giving up on this EB -- see the cmdlogs/
        # legacy_scripts detection above. This handles the
        # pre-automated-pipeline delivery convention where every
        # calibration table is already pre-computed in *.calibration.tgz
        # and only needs to be APPLIED (flagdata/applycal/split, in the
        # script's own original order), not re-derived.
        legacy_matches = glob.glob(
            f'{MOUSDIR}/**/uid___{EB}.ms.scriptForCalibration.py', recursive=True)
        if not legacy_matches:
            rec['errors'].append(f'{EB}: no calapply.txt and no matching '
                                  f'scriptForCalibration.py, skipped')
            continue
        script_path = legacy_matches[0]
        log(f'  no calapply.txt; using legacy scriptForCalibration.py: '
            f'{script_path}')

        # --- import (identical logic/params to the modern path's import
        # section below, duplicated here since the legacy branch skips
        # over that section entirely) ---
        tar_fname = asdm_fname
        _sz = asdm_sizes.get(tar_fname)
        _free_gb = free_bytes() / 1e9
        if _sz and (_free_gb - _sz / 1e9) < SAFETY_MARGIN_GB:
            rec['errors'].append(f'{EB}: aborted before download -- only '
                                  f'{_free_gb:.0f} GB free, this EB is '
                                  f'{_sz/1e9:.1f} GB (safety margin breach)')
            continue
        tar_path = gentle_download(tar_fname, RAW)
        if not glob.glob(f'{ASDMD}/**/ASDM.xml', recursive=True):
            shutil.rmtree(ASDMD, ignore_errors=True)
            os.makedirs(ASDMD, exist_ok=True)
            subprocess.run(['tar', 'xf', tar_path, '-C', ASDMD], check=True)
        hits = glob.glob(f'{ASDMD}/**/ASDM.xml', recursive=True)
        if not hits:
            rec['errors'].append(f'{EB}: ASDM extraction failed (legacy path), skipped')
            os.remove(tar_path)
            continue
        asdm_dir = os.path.dirname(hits[0])
        os.remove(tar_path)
        if not glob.glob(f'{MS}/.import_ok'):
            shutil.rmtree(MS, ignore_errors=True)
            shutil.rmtree(MS + '.flagversions', ignore_errors=True)
            try:
                importasdm(asdm=asdm_dir, vis=MS,
                           asis='SBSummary ExecBlock Antenna Station Receiver Source '
                                'CalAtmosphere CalWVR CalPointing',
                           bdfflags=True, lazy=False, process_caldevice=False,
                           with_pointing_correction=True, ocorr_mode='ca',
                           flagbackup=False, overwrite=True)
                open(f'{MS}/.import_ok', 'w').write('ok')
            except Exception as e:
                rec['errors'].append(f'{EB}: importasdm failed (legacy path): {e}')
                shutil.rmtree(ASDMD, ignore_errors=True)
                continue
        shutil.rmtree(ASDMD, ignore_errors=True)
        log(f'  importasdm (legacy path): {time.time()-t0:.0f}s')

        # --- extract this EB's pre-computed calibration tables, if not
        # already done by the shared *.calibration.tgz handling above ---
        legacy_cal_tgz = glob.glob(f'{CALSRC}/uid___{EB}.calibration.tgz')
        for tgz in legacy_cal_tgz:
            marker = f'{CALDIR}/.extracted_{os.path.basename(tgz)}'
            if not os.path.exists(marker):
                with tarfile.open(tgz) as tf:
                    tf.extractall(CALDIR)
                open(marker, 'w').write('ok')

        # --- replay: extract every statement from the script, keep only
        # flagging/apply/split calls (importasdm already done above;
        # gencal/gaincal/bandpass/setjy/fluxscale deliberately SKIPPED --
        # their outputs already exist as pre-computed tables, verified by
        # direct inspection of a real delivery before this code was
        # written; re-running them would at best be redundant and at
        # worst produce a different, non-reproducible solve) ---
        stmts = parse_statements(script_path)
        SKIP_PREFIXES = ('gencal(', 'gaincal(', 'bandpass(', 'setjy(',
                          'fluxscale(', 'plotms(', 'plotcal(', 'es.',
                          'importasdm(', 'listobs(', 'flagmanager(')
        KEEP_PREFIXES = ('flagdata(', 'applycal(', 'split(', 'os.system(')
        # 2026-09-06 addition: some applycal/split calls reference helper
        # variables (a Tsys spw-mapping list, a literal dict/list of
        # constants) computed by OTHER statements earlier in the same
        # script step -- confirmed live on Wolf 219: `tsysmap =
        # tsysspwmap(...)`, `calspwmap = {0: [...], ...}`,
        # `listOfIntents = [...]`. These were previously dropped entirely
        # (not matching flagdata/applycal/split), causing every
        # downstream statement referencing them to fail with a Python
        # NameError. Capture them too: (a) literal dict/list assignments
        # (`name = {...}` / `name = [...]`) are pure data, zero execution
        # risk; (b) `tsysspwmap(...)` calls are a deterministic, standard
        # ALMA bookkeeping computation over an EXISTING (already-computed)
        # Tsys table -- not a re-derivation of any calibration solution --
        # ported verbatim in logic from the canonical NRAO
        # casarecipes/almahelpers.py (not installed in this CASA build) in
        # _tsysspwmap_legacy.py, verified against real archival data
        # before being trusted here. Deliberately NOT a general "keep
        # anything not explicitly skipped" policy -- only these two
        # specific, well-understood, low-risk patterns.
        _assign_re = re.compile(r'^\w+\s*=\s*(tsysspwmap\(|[\{\[])')
        replay_stmts = [s for s in stmts
                        if (s.startswith(KEEP_PREFIXES) or _assign_re.match(s))
                        and not s.startswith(SKIP_PREFIXES)]
        if not replay_stmts:
            rec['errors'].append(f'{EB}: legacy script has no replayable '
                                  f'flagdata/applycal/split statements, skipped')
            continue
        log(f'  legacy replay: {len(replay_stmts)} flagdata/applycal/split '
            f'statements to replay in original order')

        # Symlink this EB's tables into WORK under the bare names the
        # script's own (relative-path) statements reference -- MS is
        # already at WORK/uid___{EB}.ms, matching the script's own
        # working-directory convention exactly.
        # 2026-09-06 fix: some *.calibration.tgz archives extract to a
        # NESTED "<EB>.calibration/" subdirectory containing the actual
        # per-table files (e.g. "<EB>.calibration/<EB>.ms.tsys"), rather
        # than depositing the tables flat in CALDIR directly -- confirmed
        # live on Wolf 219 (2015.1.00783.S). The original glob only
        # matched (and symlinked) the CONTAINER directory itself under its
        # own name, never the individual files the script's statements
        # actually reference by their bare names (e.g. "<EB>.ms.tsys" as
        # a top-level name in WORK) -- so every applycal call referencing
        # such a table failed with "path must exist" even though the
        # genuine, correct table was sitting one directory level deeper.
        # Descend one level into any "<EB>.calibration"-named directory
        # and symlink its contents individually too, in addition to the
        # flat case (harmless no-op if CALDIR already has flat files).
        # 2026-09-06 fix (6th legacy-mechanism bug, found live on Wolf 219
        # EB A002_Xb25e1a_Xed74): some *.calibration.tgz archives bundle
        # not just the genuine calibration TABLES (bandpass, tsys, wvr,
        # phase_inf, etc.) but also a stray copy of the ORIGINAL PI's own
        # \.ms.split.flagversions\/\.ms.flagversions\/\.ms.split.cal.flagversions        # directories from THEIR OWN interactive reduction session --
        # confirmed live by directly inspecting the real tgz contents
        # (uid___...calibration/uid___...ms.split.flagversions is a real
        # top-level entry alongside the genuine caltables). The broad glob
        # above symlinks these in along with the real tables, so by the
        # time our OWN fresh split() call runs, WORK/<EB>.ms.split.flagversions
        # is already a symlink to the PI's bundled one -- split() then
        # fails immediately with lready exists\ on its very FIRST ever
        # invocation of this run, even on a fully clean re-run, since the
        # collision comes from the calibration.tgz itself, not from any
        # leftover state of ours. These bundled flagversions dirs are not
        # calibration tables at all (nothing in KEEP_PREFIXES/replay
        # reads from them) and we always want OUR OWN fresh flag history
        # from replaying flagdata/split in original order, not the PI's
        # -- so exclude anything ending in lagversions\ from the
        # symlink set entirely (both the flat and one-level-nested cases).
        _cal_sources = list(glob.glob(f'{CALDIR}/uid___{EB}*'))
        for _sub in list(_cal_sources):
            if os.path.isdir(_sub) and os.path.basename(_sub) == f'uid___{EB}.calibration':
                _cal_sources.extend(glob.glob(f'{_sub}/uid___{EB}*'))
        _cal_sources = [p for p in _cal_sources if not os.path.basename(p).endswith('flagversions')]
        for tbl_path in _cal_sources:
            link_path = f'{WORK}/{os.path.basename(tbl_path)}'
            if not os.path.exists(link_path):
                os.symlink(tbl_path, link_path)

        cwd_before = os.getcwd()
        os.chdir(WORK)
        ok_count = 0
        # 2026-09-06 fix: this exec() namespace MUST be created ONCE, here,
        # and reused across every statement in the loop below -- creating
        # a brand-new dict literal INSIDE the loop body (the original
        # code) meant every assignment (tsysmap = tsysspwmap(...),
        # calspwmap = {...}, listOfIntents = [...]) was thrown away the
        # instant its own exec() call returned, so every LATER statement
        # referencing that name failed with NameError -- confirmed live:
        # the assignment statements themselves executed and incremented
        # ok_count with no error, yet every applycal/split call needing
        # their result still failed, which only makes sense if each
        # exec() call was scoped independently.
        # 2026-09-14 fix: this bare import only resolves if /data/SETI/bin is on
        # sys.path, which is not guaranteed once the caller has chdir-ed into the
        # target directory (and is not the case when this runs under CASA).  The
        # branch is exercised only by early-cycle data, so the fault lay dormant
        # until three 2012-cycle blocks reached it and failed with
        # ModuleNotFoundError.  Pin the directory explicitly.
        import sys as _sys
        # abspath does NOT resolve symlinks, so a symlinked entry point would
        # pin the wrong directory; pin both, plus the known home of the helper.
        for _cand in (os.path.dirname(os.path.abspath(__file__)),
                      os.path.dirname(os.path.realpath(__file__)),
                      '/data/SETI/bin'):
            if _cand and _cand not in _sys.path:
                _sys.path.insert(0, _cand)
        from _tsysspwmap_legacy import tsysspwmap as _legacy_tsysspwmap
        _legacy_ns = {
            'flagdata': flagdata, 'applycal': applycal, 'split': split,
            'os': os, 'tsysspwmap': _legacy_tsysspwmap,
            'True': True, 'False': False,
        }
        try:
            for stmt in replay_stmts:
                # Python-2 bare T/F shortcuts used throughout these older
                # scripts (confirmed live: 'calwt = T', 'flagbackup = F').
                py_stmt = re.sub(r'(?<=[=,\[\s])T(?=[,\)\s])', 'True', stmt)
                py_stmt = re.sub(r'(?<=[=,\[\s])F(?=[,\)\s])', 'False', py_stmt)
                # 2026-09-06 fix: these scripts' own cleanup
                # (`os.system('rm -rf <name>.ms.split')`) only removes the
                # MAIN output MS, not the companion "<name>.flagversions"
                # directory CASA's split() creates alongside it -- if an
                # earlier attempt (this session's testing, or a genuinely
                # interrupted prior run) got as far as creating that
                # sibling before failing/being killed, every subsequent
                # attempt's split() call fails outright with "flagversions
                # ... already exists. Please delete it." even on an
                # otherwise fully clean re-run. Confirmed live on Wolf 219
                # (2015.1.00783.S) -- the script never anticipates this
                # because a human interactively re-running cells in a
                # live CASA session would just delete it manually.
                # Proactively clean both the target MS and its
                # flagversions sibling before every `split(...)` call,
                # matching what a human operator would routinely do.
                if py_stmt.startswith('split('):
                    _m = re.search(r"outputvis\s*=\s*'([^']+)'", py_stmt)
                    if _m:
                        shutil.rmtree(_m.group(1), ignore_errors=True)
                        shutil.rmtree(_m.group(1) + '.flagversions', ignore_errors=True)
                try:
                    exec(py_stmt, _legacy_ns)
                    ok_count += 1
                except Exception as e:
                    log(f'  legacy replay statement skipped ({e}): {py_stmt[:100]}')
        finally:
            os.chdir(cwd_before)
        log(f'  legacy replay: {ok_count}/{len(replay_stmts)} statements executed '
            f'without error')
        if ok_count == 0:
            rec['errors'].append(f'{EB}: all legacy replay statements failed, skipped')
            continue

        # The script's own final split (per direct inspection, named
        # "<EB>.ms.split.cal") is the calibrated product -- copy/rename it
        # to the exact path/convention the rest of this pipeline expects
        # (PROD/{EB}_target.ms), so everything downstream (narrowband
        # search, continuum mapping) runs completely unmodified.
        legacy_final_candidates = (
            glob.glob(f'{WORK}/uid___{EB}.ms.split.cal') or
            glob.glob(f'{WORK}/uid___{EB}.ms.split'))
        if not legacy_final_candidates:
            rec['errors'].append(f'{EB}: legacy replay ran but produced no '
                                  f'final calibrated MS (looked for '
                                  f'uid___{EB}.ms.split.cal / .ms.split), skipped')
            continue
        legacy_out = legacy_final_candidates[0]
        out_ms = f'{PROD}/{EB}_target.ms'
        shutil.rmtree(out_ms, ignore_errors=True)
        shutil.copytree(legacy_out, out_ms)
        log(f'  legacy replay: final MS copied to {out_ms}')
        # 2026-09-07 fix: once the final calibrated MS is safely copied to
        # PROD, every intermediate copy left behind in WORK by the legacy
        # replay (the raw imported "<EB>.ms", the intermediate
        # "<EB>.ms.split", and "<EB>.ms.split.cal" if distinct from
        # legacy_out) is now fully redundant -- select_finest_spw.py and
        # everything downstream only ever reads from PROD, never WORK
        # (confirmed by direct inspection). Found live on Wolf 219 (this
        # SAME MOUS/legacy script, 2015.1.00783.S): these redundant copies
        # totalled 257G for just 2 EBs and stalled the disk governor for
        # ~20min before a MANUAL one-off cleanup unblocked it. That manual
        # fix was never turned into a code change, and the same MOUS
        # recurred here (a sibling star in the same 7-object mosaic,
        # PM_J03433+1958) -- this time nobody caught it before the
        # dedicated EMERGENCY disk-kill threshold (80GB) fired mid-run,
        # a genuinely avoidable transient failure. Proactively reclaim
        # these intermediates for EVERY EB right after its own final MS
        # is safely copied out, not just at whole-target completion/failure.
        for _stale in glob.glob(f'{WORK}/uid___{EB}.ms*'):
            if os.path.abspath(_stale) == os.path.abspath(legacy_out):
                continue
            shutil.rmtree(_stale, ignore_errors=True)
        log(f'  legacy replay: reclaimed intermediate WORK copies for {EB}')
        processed.append(dict(eb=EB, ms=out_ms, spws=None, target_field=None))
        rec['ebs'][EB] = dict(ms=out_ms, spws=None, target_field=None, ok=True,
                               legacy_scriptforcal_replay=True)
        save()
        continue
    calapply_txt = open(calapply_path).read()
    pairs = re.findall(r"field='([^']*)', intent='([^']+)'", calapply_txt)
    by_intent = {}
    for f, intent in pairs:
        for tag in intent.split(','):
            by_intent.setdefault(tag, set()).add(f)
    # field='' happens in some (older/other-pipeline-version) deliveries --
    # the calapply.txt simply doesn't spell out field names explicitly.
    # Don't trust an empty string as a real field name; fall back to
    # MS-native STATE-table introspection (below, after import) in that
    # case, which is robust regardless of calapply.txt formatting quirks.
    target_fields_txt = {f for f in by_intent.get('TARGET', set()) if f}
    # spw selections appear as comma lists ("17,21,23,25"), tilde ranges
    # ("0~23"), or a mix ("0~5,10,12~15") depending on delivery/pipeline
    # version -- expand all forms generically rather than assuming one.
    spw_lists = re.findall(r"spw='([0-9,~]+)'", calapply_txt)
    if not spw_lists:
        rec['errors'].append(f'{EB}: no spw selection found, skipped')
        continue
    SPWS = set()
    for s in spw_lists:
        for tok in s.split(','):
            if '~' in tok:
                lo, hi = tok.split('~')
                SPWS.update(range(int(lo), int(hi) + 1))
            elif tok:
                SPWS.add(int(tok))
    SPWS = sorted(SPWS)
    SPW_STR = ','.join(str(x) for x in SPWS)
    log(f'  spws={SPW_STR}  (target field TBD: '
        f'{"from calapply.txt" if target_fields_txt else "from MS STATE table after import"})')

    # -------------------------------------------------------------- import
    tar_fname = asdm_fname
    # Live re-check immediately before each download, not just the
    # upfront plan above -- other users' disk usage can change at any
    # time during a long-running target (see the PDS 70 incident).
    _sz = asdm_sizes.get(tar_fname)
    _free_gb = free_bytes() / 1e9
    if _sz and (_free_gb - _sz / 1e9) < SAFETY_MARGIN_GB:
        rec['errors'].append(f'{EB}: aborted before download -- only '
                              f'{_free_gb:.0f} GB free, this EB is '
                              f'{_sz/1e9:.1f} GB (safety margin breach)')
        log(f'  ABORTING {EB}: live disk check failed just before download '
            f'({_free_gb:.0f} GB free, need {_sz/1e9:.1f} GB + '
            f'{SAFETY_MARGIN_GB:.0f} GB margin)')
        continue
    tar_path = gentle_download(tar_fname, RAW)
    if not glob.glob(f'{ASDMD}/**/ASDM.xml', recursive=True):
        shutil.rmtree(ASDMD, ignore_errors=True)
        os.makedirs(ASDMD, exist_ok=True)
        subprocess.run(['tar', 'xf', tar_path, '-C', ASDMD], check=True)
    hits = glob.glob(f'{ASDMD}/**/ASDM.xml', recursive=True)
    if not hits:
        rec['errors'].append(f'{EB}: ASDM extraction failed, skipped')
        os.remove(tar_path)
        continue
    asdm_dir = os.path.dirname(hits[0])
    os.remove(tar_path)

    if not glob.glob(f'{MS}/.import_ok'):
        shutil.rmtree(MS, ignore_errors=True)
        shutil.rmtree(MS + '.flagversions', ignore_errors=True)
        try:
            importasdm(asdm=asdm_dir, vis=MS,
                       asis='SBSummary ExecBlock Antenna Station Receiver Source '
                            'CalAtmosphere CalWVR CalPointing',
                       bdfflags=True, lazy=False, process_caldevice=False,
                       with_pointing_correction=True, ocorr_mode='ca',
                       flagbackup=False, overwrite=True)
            open(f'{MS}/.import_ok', 'w').write('ok')
        except Exception as e:
            rec['errors'].append(f'{EB}: importasdm failed: {e}')
            shutil.rmtree(ASDMD, ignore_errors=True)
            continue
    shutil.rmtree(ASDMD, ignore_errors=True)
    log(f'  importasdm: {time.time()-t0:.0f}s')

    # ------------------------------------------------- target field, MS-native
    if target_fields_txt:
        target_fields = target_fields_txt
    else:
        from casatools import table as _tbl
        target_fields = set()
        try:
            _t = _tbl()
            _t.open(MS + '/STATE')
            obsmodes = _t.getcol('OBS_MODE')
            _t.close()
            target_state_ids = {i for i, mo in enumerate(obsmodes) if 'OBSERVE_TARGET' in mo}
            _t.open(MS)
            state_ids = _t.getcol('STATE_ID')
            field_ids = _t.getcol('FIELD_ID')
            _t.close()
            tgt_field_ids = set(int(f) for f, s in zip(field_ids, state_ids)
                                if s in target_state_ids)
            _t.open(MS + '/FIELD')
            names = _t.getcol('NAME')
            _t.close()
            target_fields = {names[i] for i in tgt_field_ids}
        except Exception as e:
            log(f'  MS-native target-field detection failed: {e}')
    if not target_fields:
        rec['errors'].append(f'{EB}: no TARGET-intent field found '
                             '(neither calapply.txt nor MS STATE table), skipped')
        shutil.rmtree(MS, ignore_errors=True)
        shutil.rmtree(MS + '.flagversions', ignore_errors=True)
        continue
    if len(target_fields) > 1:
        log(f'  WARNING: {len(target_fields)} TARGET fields {target_fields}, using all')
    TFIELD = ','.join(sorted(target_fields))
    log(f'  target field(s) = {TFIELD}')

    # ---------------------------------------------------------- flag replay
    t0 = time.time()
    stmts = parse_statements(CMDLOG)
    mine = [s for s in stmts if s.startswith('flagdata(')
            and f"vis='uid___{EB}.ms'" in s
            and "mode='summary'" not in s and ".tbl'" not in s]
    for s in mine:
        s2 = s.replace(f"vis='uid___{EB}.ms'", 'vis=VIS')
        try:
            exec(s2, {'flagdata': flagdata, 'VIS': MS, 'True': True, 'False': False})
        except Exception as e:
            log(f'  flagdata replay skipped ({e})')
    log(f'  flag_replay: {time.time()-t0:.0f}s')

    # ------------------------------------------------------------ mstransform
    t0 = time.time()
    shutil.rmtree(CMP, ignore_errors=True)
    try:
        mstransform(vis=MS, outputvis=CMP, field=TFIELD, spw=SPW_STR,
                    datacolumn='data', reindex=False, keepflags=True,
                    realmodelcol=False)
    except Exception as e:
        rec['errors'].append(f'{EB}: mstransform failed: {e}')
        shutil.rmtree(MS, ignore_errors=True)
        shutil.rmtree(MS + '.flagversions', ignore_errors=True)
        continue
    shutil.rmtree(MS, ignore_errors=True)
    shutil.rmtree(MS + '.flagversions', ignore_errors=True)
    log(f'  mstransform: {time.time()-t0:.0f}s')

    # --------------------------------------------------------------- applycal
    t0 = time.time()
    txt = calapply_txt
    txt = re.sub(r"vis='[^']*'", 'vis=VIS', txt)
    txt = re.sub(r"'/[^']*/working/([^']*)'", r"'" + CALDIR + r"/\1'", txt)
    txt = re.sub(r"'(uid___[^']+\.tbl)'", r"'" + CALDIR + r"/\1'", txt)
    txt = re.sub(r"intent='[^']*',\s*", '', txt)
    calls = [l for l in txt.splitlines() if l.startswith('applycal(')]
    ok_applycal = 0
    for c in calls:
        try:
            exec(c, {'applycal': applycal, 'VIS': CMP, 'True': True, 'False': False})
            ok_applycal += 1
        except Exception as e:
            log(f'  applycal call skipped ({e})')
    if ok_applycal == 0:
        rec['errors'].append(f'{EB}: all applycal calls failed, skipped')
        shutil.rmtree(CMP, ignore_errors=True)
        continue
    log(f'  applycal: {ok_applycal}/{len(calls)} calls ok, {time.time()-t0:.0f}s')

    # ------------------------------------------------------------------ split
    t0 = time.time()
    out_ms = f'{PROD}/{EB}_target.ms'
    shutil.rmtree(out_ms, ignore_errors=True)
    try:
        split(vis=CMP, outputvis=out_ms, field=TFIELD, spw=SPW_STR,
              datacolumn='corrected', keepflags=False, antenna='*&*')
    except Exception as e:
        rec['errors'].append(f'{EB}: final split failed: {e}')
        shutil.rmtree(CMP, ignore_errors=True)
        continue
    shutil.rmtree(CMP, ignore_errors=True)
    log(f'  split: {time.time()-t0:.0f}s -> {out_ms}')
    processed.append(dict(eb=EB, ms=out_ms, spws=SPWS, target_field=TFIELD))
    rec['ebs'][EB] = dict(ms=out_ms, spws=SPWS, target_field=TFIELD, ok=True)
    save()

rec['done'] = len(processed) > 0
rec['n_processed'] = len(processed)
save()
if not processed:
    fail('no execution blocks were successfully calibrated for this target')
log(f'COMPLETE: {len(processed)}/{len(asdm_files)} EB(s) calibrated -> {PROD}')
