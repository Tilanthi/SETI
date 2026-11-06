#!/usr/bin/env python3
"""Pack the deposit into a reproducible zip.

    python3 mkzip.py [--tree DIR] [--out FILE]

★★ A zip is not reproducible by default: it stores each member's modification
time and the order it was written in, so two archives of identical files
differ byte for byte and no checksum can be published for one.  Three things
are fixed here -- the member order (sorted), the member timestamp (one
constant for every member) and the external attributes (0644 for files, 0755
for directories) -- and the compression level is given explicitly rather than
taken from the library's default, which has changed between releases.
The result is byte-identical across runs and across machines, so the SHA-256
printed below can be published beside the archive.
"""
import argparse
import hashlib
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser()
AP.add_argument('--tree', default=os.path.join(HERE,
                                               'ALMA_Technosignatures_40pc'))
AP.add_argument('--out', default=os.path.join(
    HERE, 'ALMA_Technosignatures_40pc.zip'))
A = AP.parse_args()
TREE = os.path.abspath(A.tree)
OUT = os.path.abspath(A.out)
ROOT = os.path.basename(TREE)
STAMP = (2026, 1, 1, 0, 0, 0)       # one constant, so the zip is reproducible

names = []
for d, _subdirs, files in os.walk(TREE):
    for fn in files:
        p = os.path.join(d, fn)
        names.append(os.path.relpath(p, TREE))
names.sort()
dirs = sorted({os.path.dirname(n) for n in names} - {''})

if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for d in dirs:
        zi = zipfile.ZipInfo(ROOT + '/' + d + '/', date_time=STAMP)
        zi.external_attr = (0o040755 << 16) | 0x10
        z.writestr(zi, b'')
    for n in names:
        with open(os.path.join(TREE, n), 'rb') as fh:
            data = fh.read()
        zi = zipfile.ZipInfo(ROOT + '/' + n, date_time=STAMP)
        zi.external_attr = 0o100644 << 16
        zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, data)

h = hashlib.sha256(open(OUT, 'rb').read()).hexdigest()
print('%s' % OUT)
print('  %d files in %d directories' % (len(names), len(dirs)))
print('  %d bytes' % os.path.getsize(OUT))
print('  sha256 %s' % h)
