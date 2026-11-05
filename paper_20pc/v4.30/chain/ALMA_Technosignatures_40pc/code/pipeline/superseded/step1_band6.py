#!/usr/bin/env python3
"""
Band-6 variant of the calibration step, for ALMA project 2024.A.00040.S
("Monitoring Flares from TRAPPIST-1 with ALMA and JWST", PI MacGregor).

Structurally identical recipe to step1c_calibrate_allfields.py (import ->
replay pipeline flagging -> mstransform to one spw -> replay applycal ->
split target + both calibrators), but parameterised for this project's
different field names, calibrators, and MOUS/EB layout: 6 independent
epochs (MOUS), each with 5 small execution blocks, ~10 antennas (compact
array), spws 14/16/18/20 all at coarse 36.125 MHz resolution (no fine
FDM window in this project -- it's a continuum flare-monitoring setup, not
a spectral-line one). We use spw 14 (222.99-224.96 GHz, the lowest-
frequency window) as the representative search band, consistent with how
step1b/step1c picked ALMA project 2017.1.00215.S's one fine FDM window
over its three coarser TDM windows for the Band-7 result.

Usage: step1_band6.py <MOUS_TAG> <EBID> [--import]
  MOUS_TAG identifies which of the 6 epochs this EB belongs to, e.g. X1e3.
  EBID is the uid___... token, e.g. A002_X12a079b_X22389.
"""
import os, re, sys, glob, json, time, shutil, subprocess

MOUS_TAG = sys.argv[1]
EB       = sys.argv[2]
DOIMP    = '--import' in sys.argv
ROOT     = '/data/SETI'
RAW      = f'{ROOT}/raw/band6'
WORK     = f'{ROOT}/work'
ASDMD    = f'{WORK}/asdm_b6_{EB}'
MS       = f'{WORK}/uid___{EB}.ms'
CMP      = f'{WORK}/{EB}_b6_compact.ms'
CALDIR   = f'{WORK}/caltables_b6_{MOUS_TAG}'
LOG      = f'{ROOT}/logs/step1_band6_{EB}.json'

SPW      = '14'      # 222.99-224.96 GHz, 55 x 36.125 MHz channels (see docstring)
# NB: unlike the Band-7 project, this project's bandpass/flux calibrator is
# NOT fixed across the campaign -- different EBs even within the same MOUS
# use different bandpass calibrators (observed: J1924-2914 for one EB,
# J2232+1143 for others in the same epoch), presumably re-picked per EB for
# elevation/visibility. So the bandpass-cal field name is auto-detected
# from each EB's own calapply.txt below rather than hardcoded.

os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
rec = {'eb': EB, 'mous': MOUS_TAG, 'band': 6, 'steps': {}}


def mark(k, t0):
    rec['steps'][k] = round(time.time() - t0, 1)
    json.dump(rec, open(LOG, 'w'), indent=1)
    print(f'[B6:{EB}] {k}: {rec["steps"][k]} s', flush=True)


def parse_statements(path):
    out, cur, depth = [], None, 0
    for line in open(path):
        if line.startswith('#') or not line.strip():
            continue
        if cur is None:
            if re.match(r'^[a-z_]+\(', line):
                cur, depth = line.rstrip('\n'), 0
            else:
                continue
        else:
            cur += ' ' + line.strip()
        depth = cur.count('(') - cur.count(')')
        if depth <= 0:
            out.append(re.sub(r'\s+', ' ', cur))
            cur = None
    return out


def find_mous_dir():
    """The auxiliary tar's internal group/member UID differs per epoch --
    locate it generically instead of hardcoding."""
    hits = glob.glob(f'{WORK}/band6_aux/2024.A.00040.S/science_goal.*/group.*/'
                      f'member.uid___A001_X3819_{MOUS_TAG}')
    if not hits:
        raise RuntimeError(f'no MOUS dir found for tag {MOUS_TAG}')
    return hits[0]


from casatasks import importasdm, applycal, split, flagdata, mstransform

MOUSDIR = find_mous_dir()
CALSRC = f'{MOUSDIR}/calibration'
CMDLOG = glob.glob(f'{MOUSDIR}/log/*.hifa_calimage.casa_commands.log')[0]

t0 = time.time()
OKMARK = MS + '/.import_ok'
if DOIMP:
    tar = f'{RAW}/2024.A.00040.S_uid___{EB}.asdm.sdm.tar'
    # Guard against a stale/incomplete extraction directory left behind by
    # an earlier interrupted attempt -- checking isdir() alone is not
    # enough (an empty or partial dir would wrongly be treated as "already
    # extracted" and silently skipped).
    if not glob.glob(f'{ASDMD}/**/ASDM.xml', recursive=True):
        shutil.rmtree(ASDMD, ignore_errors=True)
        os.makedirs(ASDMD, exist_ok=True)
        subprocess.check_call(['tar', 'xf', tar, '-C', ASDMD])
    asdm = os.path.dirname(glob.glob(f'{ASDMD}/**/ASDM.xml', recursive=True)[0])
    shutil.rmtree(MS, ignore_errors=True)
    shutil.rmtree(MS + '.flagversions', ignore_errors=True)
    importasdm(asdm=asdm, vis=MS,
               asis='SBSummary ExecBlock Antenna Station Receiver Source '
                    'CalAtmosphere CalWVR CalPointing',
               bdfflags=True, lazy=False, process_caldevice=False,
               with_pointing_correction=True, ocorr_mode='ca',
               flagbackup=False, overwrite=True)
    open(OKMARK, 'w').write('ok')
    shutil.rmtree(ASDMD, ignore_errors=True)
    if os.path.exists(tar):
        os.remove(tar)
mark('importasdm', t0)

t0 = time.time()
if not os.path.isdir(CALDIR):
    os.makedirs(CALDIR, exist_ok=True)
    for tgz in glob.glob(f'{CALSRC}/*.caltables.tgz'):
        import tarfile
        with tarfile.open(tgz) as tf:
            tf.extractall(CALDIR)
mark('extract_caltables', t0)

t0 = time.time()
stmts = parse_statements(CMDLOG)
mine = [s for s in stmts
        if s.startswith('flagdata(')
        and f"vis='uid___{EB}.ms'" in s
        and "mode='summary'" not in s
        and ".tbl'" not in s]
napp = 0
for s in mine:
    s2 = s.replace(f"vis='uid___{EB}.ms'", 'vis=VIS')
    try:
        exec(s2, {'flagdata': flagdata, 'VIS': MS, 'True': True, 'False': False})
        napp += 1
    except Exception as e:
        print(f'[B6:{EB}] flagdata replay skipped: {e}', flush=True)
mark('flag_replay', t0)

t0 = time.time()
_calapply_txt = open(f'{CALSRC}/uid___{EB}.ms.calapply.txt').read()
# Both the bandpass/flux AND the phase calibrator field can vary per EB in
# this project (observed: J1924-2914 vs J2232+1143 vs ... for bandpass;
# J2301-0158 vs J2229-0832 for phase) -- classify fields by INTENT rather
# than assuming fixed names.
_pairs = re.findall(r"field='([^']+)', intent='([^']+)'", _calapply_txt)
_by_intent = {}
for f, intent in _pairs:
    for tag in intent.split(','):
        _by_intent.setdefault(tag, set()).add(f)
_bp_candidates = (_by_intent.get('BANDPASS', set()) | _by_intent.get('AMPLITUDE', set())) - {'trappist-1'}
_ph_candidates = _by_intent.get('PHASE', set()) - {'trappist-1'} - _bp_candidates
if len(_bp_candidates) != 1:
    raise RuntimeError(f'expected exactly 1 bandpass calibrator field, found {_bp_candidates}')
if len(_ph_candidates) != 1:
    raise RuntimeError(f'expected exactly 1 phase calibrator field, found {_ph_candidates}')
BPCAL = _bp_candidates.pop()
PHASECAL = _ph_candidates.pop()
rec['bpcal_field'] = BPCAL
rec['phasecal_field'] = PHASECAL
FIELDS = f'trappist-1,{PHASECAL},{BPCAL}'
print(f'[B6:{EB}] bandpass/flux calibrator field = {BPCAL}, '
      f'phase calibrator field = {PHASECAL}', flush=True)

shutil.rmtree(CMP, ignore_errors=True)
mstransform(vis=MS, outputvis=CMP, field=FIELDS, spw=SPW,
            datacolumn='data', reindex=False, keepflags=True,
            realmodelcol=False)
mark('mstransform', t0)
shutil.rmtree(MS, ignore_errors=True)
shutil.rmtree(MS + '.flagversions', ignore_errors=True)

t0 = time.time()
txt = open(f'{CALSRC}/uid___{EB}.ms.calapply.txt').read()
txt = re.sub(r"vis='[^']*'", 'vis=VIS', txt)
txt = re.sub(r"'/[^']*/working/([^']*)'", r"'" + CALDIR + r"/\1'", txt)
# fall back: gaintable paths in this project's calapply.txt are already
# bare filenames (no /working/ prefix) -- rewrite those too
txt = re.sub(r"'(uid___[^']+\.tbl)'", r"'" + CALDIR + r"/\1'", txt)
txt = re.sub(r"intent='[^']*',\s*", '', txt)
calls = [l for l in txt.splitlines() if l.startswith('applycal(')]
if len(calls) < 2:
    raise RuntimeError(f'expected >=2 applycal calls, found {len(calls)}')
for c in calls:
    c2 = re.sub(r"spw='[0-9,]+'", f"spw='{SPW}'", c)
    exec(c2, {'applycal': applycal, 'VIS': CMP, 'True': True, 'False': False})
rec['applycal_calls'] = len(calls)
mark('applycal', t0)

t0 = time.time()
outs = {}
for tag, field in (('trappist1', 'trappist-1'),
                    ('phasecal', PHASECAL),
                    ('bpcal', BPCAL)):
    out = f'{ROOT}/products/B6_{EB}_{tag}.ms'
    shutil.rmtree(out, ignore_errors=True)
    split(vis=CMP, outputvis=out, field=field, spw=SPW,
          datacolumn='corrected', keepflags=False, antenna='*&*')
    outs[tag] = out
shutil.rmtree(CMP, ignore_errors=True)
rec['outputs'] = outs
mark('split_all', t0)

rec['done'] = True
json.dump(rec, open(LOG, 'w'), indent=1)
print(f'[B6:{EB}] STEP1 COMPLETE -> {outs}', flush=True)
