#!/usr/bin/env python3
"""Assemble the Zenodo upload: the deposit, the crossing-spectra file, the
metadata and their checksums, after checking that the two files belong to
this build and to each other.

    python3 zenodo_pack.py --spectra PATH/ALMA_Technosignatures_40pc_crossing_spectra.zip
                           --out DIR [--allow-placeholder]

Run after `make_all.sh` and `gate.sh` (it reads the deposit zip and the
metadata record `zdeposit.py` writes).  It refuses to pack when

  * (r36, author ruling 2026-11-09: the DOI is added on acceptance) the
    metadata record carries a DOI, or the deposit README does not say "DOI to
    be added on acceptance" -- Zenodo mints the DOI when the record is
    published, and no DOI string is written into anything before that
    (doigate.py D4/D5).  `--allow-placeholder` is accepted and ignored;
  * the spectra file's index.csv columns or any .npz file's array names
    differ from the ones the deposit's column description documents;
  * a member of the spectra file fails its own SHA256SUMS;
  * the crossings the spectra file holds are not crossings of the deposit's
    candidates/threshold_crossings.csv, or their number is not the number the
    article prints (\\DaNSpecCross).

Writes DIR/ALMA_Technosignatures_40pc.zip, DIR/<spectra file>,
DIR/zenodo_metadata.json (the Zenodo deposition metadata, ready to paste or
to send to the deposition API) and DIR/SHA256SUMS.  Nothing is uploaded.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser()
AP.add_argument('--spectra', required=True)
AP.add_argument('--out', required=True)
AP.add_argument('--allow-placeholder', action='store_true')
A = AP.parse_args()
FAIL = []


def ck(label, ok, note=''):
    print('  %-4s %s  %s' % ('ok' if ok else 'FAIL', label, note))
    if not ok:
        FAIL.append(label)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def macro(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^{}]*)\}' % name)
    val = None
    for fn in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if fn.startswith('survey_numbers') and fn.endswith('.tex') and '_drive' not in fn:
            for m in pat.finditer(open(os.path.join(HERE, 'numbers', fn), errors='ignore').read()):
                if m.group(1).strip():
                    val = m.group(1).strip()
    return val


META = json.load(open(os.path.join(HERE, 'zenodo_metadata_r30.json')))
DEP = os.path.join(HERE, 'ALMA_Technosignatures_40pc.zip')
print('zenodo_pack: deposit %s' % DEP)
# r36: OLD 'the manuscript DOI has been reserved and written in' (refused an
# all-zeros DOI) -> NEW: no DOI is carried at all until the record is minted.
_readme = zipfile.ZipFile(DEP).read('ALMA_Technosignatures_40pc/README.md').decode()
ck('no DOI is carried before Zenodo mints one (added on acceptance)',
   META.get('doi') is None and 'DOI to be added on acceptance' in _readme
   and not re.search(r'10\.\d{4,9}/', _readme),
   'metadata doi %r; README note %s' % (META.get('doi'), 'DOI to be added on acceptance' in _readme))

z = zipfile.ZipFile(A.spectra)
names = z.namelist()
root = names[0].split('/')[0] + '/'
sums = {}
for ln in z.read(root + 'SHA256SUMS').decode().splitlines():
    h, p = ln.split(None, 1)
    sums[root + p.strip()] = h
badsum = [n for n, h in sums.items() if hashlib.sha256(z.read(n)).hexdigest() != h]
ck('every spectra member matches its SHA256SUMS', not badsum and bool(sums),
   '%d members%s' % (len(sums), '' if not badsum else '; DIFFER %s' % badsum[:2]))
idx = list(csv.DictReader(io.StringIO(z.read(root + 'index.csv').decode())))
ck('index.csv columns are the documented ones',
   list(idx[0].keys()) == META['spectra_index_columns'],
   '%d columns' % len(idx[0]))
import numpy as np                                                     # noqa: E402
badkeys, gens = [], {1: 0, 2: 0, 3: 0}
_all = set(META['spectra_arrays'])
_g3 = set(META['spectra_arrays_gen3'])
_g2 = set(META['spectra_arrays_gen2'])
_valid = {1: _all - _g2 - _g3, 2: _all - _g3, 3: _all}
for r in idx:
    if not r['file']:
        continue
    d = np.load(io.BytesIO(z.read(root + r['file'])), allow_pickle=False)
    k = set(d.files)
    g = [gg for gg in (3, 2, 1) if k == _valid[gg]]
    if g:
        gens[g[0]] += 1
    else:
        badkeys.append(r['file'])
ck('every array file holds exactly the documented arrays of one extractor generation',
   not badkeys, '%d files, generations 1/2/3: %d/%d/%d%s'
   % (sum(1 for r in idx if r['file']), gens[1], gens[2], gens[3],
      '' if not badkeys else '; DIFFER %s' % badkeys[:2]))
dz = zipfile.ZipFile(DEP)
led = list(csv.DictReader(io.StringIO(dz.read(
    'ALMA_Technosignatures_40pc/candidates/threshold_crossings.csv').decode())))
keys = {(r['eb'], round(float(r['nu_topo_GHz']), 6)) for r in led}
outside = [(r['eb'], r['f_topo_GHz']) for r in idx
           if (r['eb'], round(float(r['f_topo_GHz']), 6)) not in keys]
ck('every spectrum belongs to a crossing of the deposit', not outside,
   '%d indexed%s' % (len(idx), '' if not outside else '; NOT IN THE DEPOSIT %s' % outside[:3]))
nspec = macro('DaNSpecCross')
nfile = sum(1 for r in idx if r['file'])
ck('the number of crossings with spectra is the number the article prints',
   nspec is not None and int(nspec) == nfile, '%d against \\DaNSpecCross = %s' % (nfile, nspec))

if FAIL:
    print('zenodo_pack: NOT PACKED -- %s' % '; '.join(FAIL))
    sys.exit(1)
os.makedirs(A.out, exist_ok=True)
out = []
for src in (DEP, A.spectra):
    dst = os.path.join(A.out, os.path.basename(src))
    shutil.copyfile(src, dst)
    out.append((sha(dst), os.path.basename(dst), os.path.getsize(dst)))
meta = dict(META['metadata'])
# r36: no 'doi' field -- Zenodo mints it on publication.
with open(os.path.join(A.out, 'zenodo_metadata.json'), 'w') as fh:
    json.dump(dict(metadata=meta), fh, indent=1)
with open(os.path.join(A.out, 'SHA256SUMS'), 'w') as fh:
    for h, n, _s in out:
        fh.write('%s  %s\n' % (h, n))
for h, n, s in out:
    print('  packed %-52s %11d bytes  sha256 %s' % (n, s, h[:16]))
print('zenodo_pack: PACKED in %s' % A.out)
