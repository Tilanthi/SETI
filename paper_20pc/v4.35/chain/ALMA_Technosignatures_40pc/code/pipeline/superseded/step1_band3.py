#!/usr/bin/env python3
"""
Band-3 variant of the calibration step, for ALMA project 2017.1.00986.S
("Constraining Ultracool Dwarf Radio Emission Mechanisms and Implications
for the TRAPPIST-1 Planetary [System]"). Structurally identical recipe to
step1c_calibrate_allfields.py, parameterised for this project: field is
named 'TRAPPIST-1' (uppercase, unlike the Band-6/7 projects' 'trappist-1'),
calibrators are J0006-0623 (bandpass/flux -- the SAME source used as the
Band-7 bandpass calibrator) and J2301-0158 (phase -- also the same as
Band-7 and Band-6's phase calibrator). Only continuum/TDM spws are
available (5,7,9,11, all at coarse 31.25 MHz resolution) -- like Band 6,
there is no fine spectral-line window in this project.  We use spw 5
(89.51-91.49 GHz) as the representative search band.

Usage: step1_band3.py <EBID> [--import]
  EBID is the uid___... token, e.g. A002_Xc9831a_X443.
"""
import os, re, sys, glob, json, time, shutil, subprocess, tarfile

EB     = sys.argv[1]
DOIMP  = '--import' in sys.argv
ROOT   = '/data/SETI'
RAW    = f'{ROOT}/raw/band3'
WORK   = f'{ROOT}/work'
ASDMD  = f'{WORK}/asdm_b3_{EB}'
MS     = f'{WORK}/uid___{EB}.ms'
CMP    = f'{WORK}/{EB}_b3_compact.ms'
MOUS   = (f'{WORK}/band3_aux/2017.1.00986.S/science_goal.uid___A001_X1288_X114c/'
          f'group.uid___A001_X1288_X114d/member.uid___A001_X1288_X114e')
CALSRC = f'{MOUS}/calibration'
CMDLOG = glob.glob(f'{MOUS}/log/*.hifa_calimage.casa_commands.log')[0]
CALDIR = f'{WORK}/caltables_b3'
LOG    = f'{ROOT}/logs/step1_band3_{EB}.json'

SPW    = '5'      # 89.51-91.49 GHz, 31.25 MHz channels
FIELDS = 'TRAPPIST-1,J2301-0158,J0006-0623'

os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
rec = {'eb': EB, 'band': 3, 'steps': {}}


def mark(k, t0):
    rec['steps'][k] = round(time.time() - t0, 1)
    json.dump(rec, open(LOG, 'w'), indent=1)
    print(f'[B3:{EB}] {k}: {rec["steps"][k]} s', flush=True)


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


from casatasks import importasdm, applycal, split, flagdata, mstransform

t0 = time.time()
OKMARK = MS + '/.import_ok'
if DOIMP:
    tar = f'{RAW}/{EB}.asdm.sdm.tar'
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
    for tgz in sorted(glob.glob(f'{CALSRC}/*.caltables.tgz')):
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
        print(f'[B3:{EB}] flagdata replay skipped: {e}', flush=True)
mark('flag_replay', t0)

t0 = time.time()
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
for tag, field in (('trappist1', 'TRAPPIST-1'),
                    ('phasecal', 'J2301-0158'),
                    ('bpcal', 'J0006-0623')):
    out = f'{ROOT}/products/B3_{EB}_{tag}.ms'
    shutil.rmtree(out, ignore_errors=True)
    split(vis=CMP, outputvis=out, field=field, spw=SPW,
          datacolumn='corrected', keepflags=False, antenna='*&*')
    outs[tag] = out
shutil.rmtree(CMP, ignore_errors=True)
rec['outputs'] = outs
mark('split_all', t0)

rec['done'] = True
json.dump(rec, open(LOG, 'w'), indent=1)
print(f'[B3:{EB}] STEP1 COMPLETE -> {outs}', flush=True)
