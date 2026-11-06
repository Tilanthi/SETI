#!/usr/bin/env python3
"""
Step 1b: restore the ALMA pipeline calibration for one EB and produce a
compact, calibrated, TRAPPIST-1 measurement set containing only the FDM
spectral window.

Why not simply `flagmanager(mode='restore')` on the delivered flag version?
Because the delivered version was written by CASA 5.1.1, whose importasdm
lays the MS rows out differently from CASA 6.7; restoring it row-by-row
raises a shape-conformance error part-way through and silently mis-assigns
the flags it has already written.  Instead we replay the pipeline's OWN
flagdata commands, which are recorded verbatim in the delivered
casa_commands.log and are expressed as data selections (field / spw /
channel / antenna / intent) that are layout independent.

Usage: step1b_calibrate.py <EBID> [--import]
"""
import os, re, sys, glob, json, time, shutil, subprocess, tarfile

EB     = sys.argv[1]
DOIMP  = '--import' in sys.argv
ROOT   = '/data/SETI'
RAW    = f'{ROOT}/raw'
WORK   = f'{ROOT}/work'
ASDMD  = f'{WORK}/asdm_{EB}'
MS     = f'{WORK}/uid___{EB}.ms'
CMP    = f'{WORK}/{EB}_compact.ms'
MOUS   = (f'{WORK}/2017.1.00215.S/science_goal.uid___A001_X1273_X6bd/'
          f'group.uid___A001_X1273_X6be/member.uid___A001_X1273_X6bf')
CALSRC = f'{MOUS}/calibration'
CMDLOG = f'{MOUS}/log/member.uid___A001_X1273_X6bf.hifa_calimage.casa_commands.log'
CALDIR = f'{WORK}/caltables'
OUT    = f'{ROOT}/products/{EB}_trappist1_fdm.ms'
LOG    = f'{ROOT}/logs/step1b_{EB}.json'

FIELDS  = 'trappist-1,J2301-0158'   # target + phase cal (the latter is our
                                    # end-to-end calibration sanity check)
SPW_FDM = '25'                      # 345.657-347.532 GHz, 3840 x 488.281 kHz

os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
rec = {'eb': EB, 'steps': {}}


def mark(k, t0):
    rec['steps'][k] = round(time.time() - t0, 1)
    json.dump(rec, open(LOG, 'w'), indent=1)
    print(f'[{EB}] {k}: {rec["steps"][k]} s', flush=True)


def parse_statements(path):
    """Reassemble the wrapped multi-line CASA calls in casa_commands.log."""
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


from casatasks import (importasdm, applycal, split, listobs, flagdata,
                       mstransform)

# ------------------------------------------------------------------ import
t0 = time.time()
OKMARK = MS + '/.import_ok'
if DOIMP:
    tar = f'{RAW}/{EB}.asdm.sdm.tar'
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
    listobs(vis=MS, listfile=f'{ROOT}/logs/listobs_{EB}.txt', overwrite=True)
    shutil.rmtree(ASDMD, ignore_errors=True)
    if os.path.exists(tar):      # MS is written and marked good: reclaim ~50 GB
        os.remove(tar)
mark('importasdm', t0)

# ------------------------------------------- replay the pipeline's flagging
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
        print(f'[{EB}] flagdata replay skipped: {e}', flush=True)
rec['flagdata_replayed'] = napp
rec['flagdata_found'] = len(mine)
mark('flag_replay', t0)

# ------------------------------------------------- compact target-only MS
t0 = time.time()
shutil.rmtree(CMP, ignore_errors=True)
mstransform(vis=MS, outputvis=CMP, field=FIELDS, spw=SPW_FDM,
            datacolumn='data', reindex=False, keepflags=True,
            realmodelcol=False)
mark('mstransform', t0)
shutil.rmtree(MS, ignore_errors=True)          # the 90+ GB original can go
shutil.rmtree(MS + '.flagversions', ignore_errors=True)

# ------------------------------------------------------------------ applycal
t0 = time.time()
txt = open(f'{CALSRC}/uid___{EB}.ms.calapply.txt').read()
txt = re.sub(r"vis='[^']*'", 'vis=VIS', txt)
txt = re.sub(r"'/[^']*/working/([^']*)'", r"'" + CALDIR + r"/\1'", txt)
txt = re.sub(r"intent='[^']*',\s*", '', txt)   # pipeline shorthand; CASA
                                               # rejects it.  Field selection
                                               # is already unambiguous.
calls = [l for l in txt.splitlines() if l.startswith('applycal(')]
use = [c for c in calls if 'trappist-1' in c]
if not use:
    raise RuntimeError('no applycal call for the target field')
for c in use:
    exec(c.replace("spw='17,21,23,25'", f"spw='{SPW_FDM}'"),
         {'applycal': applycal, 'VIS': CMP, 'True': True, 'False': False})
rec['applycal_calls'] = len(use)
mark('applycal', t0)

# ---------------------------------------------------------------- final split
t0 = time.time()
shutil.rmtree(OUT, ignore_errors=True)
split(vis=CMP, outputvis=OUT, field='trappist-1', spw=SPW_FDM,
      datacolumn='corrected', keepflags=False, antenna='*&*')
mark('split_target', t0)

PHS = OUT.replace('_fdm.ms', '_phasecal.ms')
shutil.rmtree(PHS, ignore_errors=True)
split(vis=CMP, outputvis=PHS, field='J2301-0158', spw=SPW_FDM,
      datacolumn='corrected', keepflags=False, antenna='*&*')
shutil.rmtree(CMP, ignore_errors=True)

listobs(vis=OUT, listfile=f'{ROOT}/logs/listobs_target_{EB}.txt', overwrite=True)
rec['done'] = True
json.dump(rec, open(LOG, 'w'), indent=1)
print(f'[{EB}] STEP1b COMPLETE -> {OUT}', flush=True)
