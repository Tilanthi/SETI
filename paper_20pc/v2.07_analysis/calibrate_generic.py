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
    footprint on shared infrastructure, not maximise throughput."""
    out = f'{destdir}/{fname}'
    if os.path.exists(out) and not os.path.exists(out + '.aria2'):
        return out
    mirror = 'https://almascience.nao.ac.jp/dataPortal'
    for attempt in range(1, 6):
        cmd = ['nice', '-n', '19', 'ionice', '-c3', 'aria2c',
               '-x4', '-s4', '-k20M', '--file-allocation=none',
               '--console-log-level=warn', '--max-tries=6', '--retry-wait=15',
               '--lowest-speed-limit=512K', '--connect-timeout=15', '--timeout=30',
               '-c', '-d', destdir, '-o', fname, f'{mirror}/{fname}']
        subprocess.run(cmd, check=False)
        if os.path.exists(out) and not os.path.exists(out + '.aria2'):
            return out
        log(f'download attempt {attempt} incomplete for {fname}, retrying')
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
MAX_TARGET_DOWNLOAD_GB = float(os.environ.get('SETI_MAX_TARGET_DOWNLOAD_GB', '45'))
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
if not glob.glob(f'{extract_root}/**/calibration', recursive=True):
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
cmdlogs = (glob.glob(f'{MOUSDIR}/log/*calimage*commands.log') or
           glob.glob(f'{MOUSDIR}/log/*.casa_commands.log') or
           glob.glob(f'{MOUSDIR}/log/*commands.log'))
if not cmdlogs:
    fail('no casa_commands.log found -- cannot auto-replay calibration')
cmdlogs.sort(key=lambda p: ('calimage' not in p, p))
CMDLOG = cmdlogs[0]
log(f'using commands log: {CMDLOG}')
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
              glob.glob(f'{CALSRC}/*.caltables.tar.gz'))
    if not caltgz:
        log(f'  WARNING: no *.caltables.tgz / *.caltables.tar.gz found in '
            f'{CALSRC} -- if applycal fails with "table does not exist", '
            f'this MOUS uses a caltable packaging convention not yet handled')
    for tgz in caltgz:
        with tarfile.open(tgz) as tf:
            tf.extractall(CALDIR)
log(f'calibration dir: {CALSRC}')


def parse_statements(path):
    out, cur = [], None
    for line in open(path):
        if line.startswith('#') or not line.strip():
            continue
        if cur is None:
            if re.match(r'^[a-z_]+\(', line):
                cur = line.rstrip('\n')
            else:
                continue
        else:
            cur += ' ' + line.strip()
        if cur.count('(') - cur.count(')') <= 0:
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
        rec['errors'].append(f'{EB}: no calapply.txt, skipped')
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
