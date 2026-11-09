#!/usr/bin/env python3
"""
Step 1 of the ALMA-SETI / TRAPPIST-1 pipeline.

Takes one ALMA Execution Block (EB) raw ASDM tar, restores the delivered
ALMA pipeline calibration (Cycle-5 hifa_calimage), and splits out the
TRAPPIST-1 field.

Follows Mason, Garrett, Wandia & Siemion (2024), arXiv:2411.19827, sec. 3-4.

Usage:  step1_calibrate.py <EBID>      e.g.  A002_Xcccc19_X5564
"""
import os, re, sys, glob, json, time, shutil, subprocess, tarfile

EB    = sys.argv[1]
ROOT  = '/data/SETI'
RAW   = f'{ROOT}/raw'
WORK  = f'{ROOT}/work'
ASDMD = f'{WORK}/asdm_{EB}'
MS    = f'{WORK}/uid___{EB}.ms'
MOUS  = (f'{WORK}/2017.1.00215.S/science_goal.uid___A001_X1273_X6bd/'
         f'group.uid___A001_X1273_X6be/member.uid___A001_X1273_X6bf')
CALSRC= f'{MOUS}/calibration'
CALDIR= f'{WORK}/caltables'
OUT   = f'{ROOT}/products'
LOG   = f'{ROOT}/logs/step1_{EB}.json'

FIELD   = 'trappist-1'
SPW_FDM = '23'                 # 345.62-347.50 GHz, 976.56 kHz channels
SPW_ALL = '17,21,23,25'

os.makedirs(OUT, exist_ok=True)
os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')

rec = {'eb': EB, 'steps': {}}
def mark(k, t0):
    rec['steps'][k] = round(time.time() - t0, 1)
    json.dump(rec, open(LOG, 'w'), indent=1)
    print(f'[{EB}] {k}: {rec["steps"][k]} s', flush=True)

from casatasks import importasdm, applycal, flagmanager, split, listobs

# ---------------------------------------------------------------- caltables
t0 = time.time()
if not os.path.isdir(CALDIR):
    os.makedirs(CALDIR, exist_ok=True)
    for tgz in sorted(glob.glob(f'{CALSRC}/*.caltables.tgz')):
        with tarfile.open(tgz) as tf:
            tf.extractall(CALDIR)
mark('extract_caltables', t0)

# ---------------------------------------------------------------- untar ASDM
t0 = time.time()
tar = f'{RAW}/{EB}.asdm.sdm.tar'
if not os.path.isdir(ASDMD):
    os.makedirs(ASDMD, exist_ok=True)
    subprocess.check_call(['tar', 'xf', tar, '-C', ASDMD])
# The archive tar preserves the whole ALMA project tree; the actual ASDM is
# the directory that contains ASDM.xml, several levels down under raw/.
cands = [os.path.dirname(p)
         for p in glob.glob(f'{ASDMD}/**/ASDM.xml', recursive=True)]
if not cands:
    raise RuntimeError(f'no ASDM.xml found under {ASDMD}')
asdm = cands[0]
mark('untar_asdm', t0)
print(f'[{EB}] ASDM = {asdm}', flush=True)

# free the tar as soon as it is unpacked -- disk hygiene
if os.path.exists(tar):
    os.remove(tar)

# ---------------------------------------------------------------- importasdm
t0 = time.time()
OKMARK = MS + '/.import_ok'
if os.path.isdir(MS) and not os.path.exists(OKMARK):
    print(f'[{EB}] removing partial MS from a previous attempt', flush=True)
    shutil.rmtree(MS, ignore_errors=True)
if not os.path.isdir(MS):
    importasdm(asdm=asdm, vis=MS,
               asis='SBSummary ExecBlock Antenna Station Receiver Source '
                    'CalAtmosphere CalWVR CalPointing',
               bdfflags=True, lazy=False, process_caldevice=False,
               with_pointing_correction=True, ocorr_mode='ca',
               flagbackup=False, overwrite=True)
    open(OKMARK, 'w').write('ok')
    # NB ocorr_mode must match the ALMA pipeline ('ca', i.e. cross+auto):
    # the delivered flagmanager version stores the FLAG column row-by-row,
    # so a row count that differs from the pipeline's would corrupt the
    # flag restore.  Autocorrelations are dropped again at the split.
mark('importasdm', t0)

listobs(vis=MS, listfile=f'{ROOT}/logs/listobs_{EB}.txt', overwrite=True)
shutil.rmtree(ASDMD, ignore_errors=True)          # ASDM no longer needed

# ---------------------------------------------------------------- flags
t0 = time.time()
fvtgz = f'{CALSRC}/uid___{EB}.ms.flagversions.tgz'
if os.path.exists(fvtgz):
    with tarfile.open(fvtgz) as tf:
        tf.extractall(WORK)
    try:
        flagmanager(vis=MS, mode='restore', versionname='Pipeline_Final')
        rec['flags'] = 'Pipeline_Final restored'
    except Exception as e:
        rec['flags'] = f'RESTORE FAILED: {e}'
        print(f'[{EB}] *** WARNING: pipeline flag restore failed: {e}', flush=True)
else:
    rec['flags'] = 'NO FLAGVERSIONS FOUND'
    print(f'[{EB}] *** WARNING: no flagversions tarball', flush=True)
mark('flagrestore', t0)

# ---------------------------------------------------------------- applycal
t0 = time.time()
txt = open(f'{CALSRC}/uid___{EB}.ms.calapply.txt').read()
txt = re.sub(r"vis='[^']*'", "vis=VIS", txt)                       # local MS
txt = re.sub(r"'/[^']*/working/([^']*)'", r"'" + CALDIR + r"/\1'", txt)  # local tbls
ns = {'applycal': applycal, 'VIS': MS}
ncalls = 0
for line in txt.splitlines():
    if line.startswith('applycal('):
        exec(line, ns)
        ncalls += 1
rec['applycal_calls'] = ncalls
mark('applycal', t0)

# ---------------------------------------------------------------- split
t0 = time.time()
outs = {}
for tag, spw in (('fdm', SPW_FDM), ('all', SPW_ALL)):
    o = f'{OUT}/{EB}_trappist1_{tag}.ms'
    shutil.rmtree(o, ignore_errors=True)
    split(vis=MS, outputvis=o, field=FIELD, spw=spw,
          datacolumn='corrected', keepflags=False)
    outs[tag] = o
    if tag == 'fdm':
        break          # 'all' only if explicitly wanted; FDM carries the science
rec['outputs'] = outs
mark('split', t0)

shutil.rmtree(MS, ignore_errors=True)
shutil.rmtree(MS + '.flagversions', ignore_errors=True)
rec['done'] = True
json.dump(rec, open(LOG, 'w'), indent=1)
print(f'[{EB}] STEP1 COMPLETE', flush=True)
