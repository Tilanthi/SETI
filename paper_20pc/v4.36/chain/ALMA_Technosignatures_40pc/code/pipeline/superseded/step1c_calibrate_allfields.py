#!/usr/bin/env python3
"""
Step 1c: like step1b_calibrate.py, but keeps and calibrates ALL THREE
fields present in each EB (target + both calibrators), for the "search
the calibrators too" systematics check: since J0006-0623 (bandpass/flux
calibrator) and J2301-0158 (phase calibrator) are both bright, steady,
non-technosignature radio sources, running the *identical* narrowband
technosignature search on them should produce a clean non-detection. If it
doesn't, that would reveal a calibration- or pipeline-induced artefact
capable of mimicking a false positive on the real target -- exactly the
kind of check a careful referee would want to see.

Usage: step1c_calibrate_allfields.py <EBID> [--import]
"""
import os, re, sys, glob, json, time, shutil, subprocess, tarfile

EB     = sys.argv[1]
DOIMP  = '--import' in sys.argv
ROOT   = '/data/SETI'
RAW    = f'{ROOT}/raw'
WORK   = f'{ROOT}/work'
ASDMD  = f'{WORK}/asdm_{EB}'
MS     = f'{WORK}/uid___{EB}.ms'
CMP    = f'{WORK}/{EB}_compact_allfields.ms'
MOUS   = (f'{WORK}/2017.1.00215.S/science_goal.uid___A001_X1273_X6bd/'
          f'group.uid___A001_X1273_X6be/member.uid___A001_X1273_X6bf')
CALSRC = f'{MOUS}/calibration'
CMDLOG = f'{MOUS}/log/member.uid___A001_X1273_X6bf.hifa_calimage.casa_commands.log'
CALDIR = f'{WORK}/caltables'
LOG    = f'{ROOT}/logs/step1c_{EB}.json'

# NB: the bandpass/flux calibrator field is NOT fixed across the whole
# campaign -- different EBs use different bandpass calibrators (observed:
# J0006-0623 for some EBs, J2148+0657 for others), so it is auto-detected
# from each EB's own calapply.txt below rather than hardcoded.
SPW_FDM = '25'

os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
rec = {'eb': EB, 'steps': {}}


def mark(k, t0):
    rec['steps'][k] = round(time.time() - t0, 1)
    json.dump(rec, open(LOG, 'w'), indent=1)
    print(f'[{EB}] {k}: {rec["steps"][k]} s', flush=True)


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


from casatasks import (importasdm, applycal, split, listobs, flagdata,
                       mstransform)

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
    shutil.rmtree(ASDMD, ignore_errors=True)
    if os.path.exists(tar):
        os.remove(tar)
mark('importasdm', t0)

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
mark('flag_replay', t0)

t0 = time.time()
_calapply_txt = open(f'{CALSRC}/uid___{EB}.ms.calapply.txt').read()
_fields = sorted(set(re.findall(r"field='([^']+)'", _calapply_txt)))
_bpcal = [f for f in _fields if f not in ('trappist-1', 'J2301-0158')
          and ',' not in f]
if len(_bpcal) != 1:
    raise RuntimeError(f'expected exactly 1 bandpass calibrator field, found {_bpcal}')
BPCAL = _bpcal[0]
rec['bpcal_field'] = BPCAL
FIELDS = f'trappist-1,J2301-0158,{BPCAL}'
print(f'[{EB}] bandpass/flux calibrator field = {BPCAL}', flush=True)

shutil.rmtree(CMP, ignore_errors=True)
mstransform(vis=MS, outputvis=CMP, field=FIELDS, spw=SPW_FDM,
            datacolumn='data', reindex=False, keepflags=True,
            realmodelcol=False)
mark('mstransform', t0)
shutil.rmtree(MS, ignore_errors=True)
shutil.rmtree(MS + '.flagversions', ignore_errors=True)

# ------------------------------------------------------------------ applycal
# Unlike step1b (target only), here we apply BOTH recorded applycal() calls
# -- one calibrates J0006-0623 itself (BANDPASS/AMPLITUDE intent), the other
# calibrates trappist-1 + J2301-0158 (PHASE/TARGET intent) -- so all three
# fields end up correctly calibrated in the same compact MS.
t0 = time.time()
txt = open(f'{CALSRC}/uid___{EB}.ms.calapply.txt').read()
txt = re.sub(r"vis='[^']*'", 'vis=VIS', txt)
txt = re.sub(r"'/[^']*/working/([^']*)'", r"'" + CALDIR + r"/\1'", txt)
txt = re.sub(r"intent='[^']*',\s*", '', txt)
calls = [l for l in txt.splitlines() if l.startswith('applycal(')]
if len(calls) < 2:
    raise RuntimeError(f'expected >=2 applycal calls, found {len(calls)}')
for c in calls:
    exec(c.replace("spw='17,21,23,25'", f"spw='{SPW_FDM}'"),
         {'applycal': applycal, 'VIS': CMP, 'True': True, 'False': False})
rec['applycal_calls'] = len(calls)
mark('applycal', t0)

# ---------------------------------------------------------------- split all 3
t0 = time.time()
outs = {}
for tag, field in (('trappist1', 'trappist-1'),
                    ('phasecal', 'J2301-0158'),
                    ('bpcal', BPCAL)):
    out = f'{ROOT}/products/{EB}_allfields_{tag}.ms'
    shutil.rmtree(out, ignore_errors=True)
    split(vis=CMP, outputvis=out, field=field, spw=SPW_FDM,
          datacolumn='corrected', keepflags=False, antenna='*&*')
    outs[tag] = out
shutil.rmtree(CMP, ignore_errors=True)
rec['outputs'] = outs
mark('split_all', t0)

rec['done'] = True
json.dump(rec, open(LOG, 'w'), indent=1)
print(f'[{EB}] STEP1c COMPLETE -> {outs}', flush=True)
