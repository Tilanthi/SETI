#!/usr/bin/env python3
r"""r36 (N3, Referee 2 R2-7): EVERY DEPOSIT PATH THE PAPER PRINTS EXISTS IN THE DEPOSIT UNDER THAT EXACT NAME.

The article names files of the deposit in \texttt{...} (sensitivity/system_limits.csv, code/reproduce.py, ...),
some typed, some generated (\LrStageFile, \LrSigFile, table notes).  Nothing checked that each name is a member
of the archive zdeposit.py builds, so a renamed table would leave the text pointing at nothing.  This reads the
PRINTED text (pdftotext of the built PDF, so typed, generated and macro-carried names are all seen as the reader
sees them), takes every token that starts with one of the archive's own top-level directories, and requires
each to be a file (or, ending in '/', a directory) of ALMA_Technosignatures_40pc.zip.

  D1  at least MIN_PATHS paths are found (a parser that finds nothing would pass anything)
  D2  every printed path is in the archive under that exact name
Drives (write nothing): 1 one cited file removed from the archive's list; 2 a misspelt path planted in the text.

    python3 depositpaths_r36.py [--drive N]
"""
import glob
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
MIN_PATHS = 10
FAIL = []


def ck(label, ok, detail=''):
    print('  %-70s %s  %s' % (label[:70], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


_v = sorted(glob.glob(os.path.join(HERE, 'technosignatures_40pc_v*.tex')))
assert len(_v) == 1, _v
PDF = _v[0][:-4] + '.pdf'
# ★ r36 integrator (rec2g): the default reading order interleaves floats and display equations with the
#   paragraph ("code/pipeline/search/" | "EIRP90 =" | "seti_drift_search_generic.py"); -raw keeps content-stream
#   order, which is the paragraph's own (genai_sweep reads the same paths correctly in its [raw] pass).
TXT = subprocess.run(['pdftotext', '-raw', PDF, '-'], capture_output=True, text=True, check=True).stdout
if DRIVE == 2:
    TXT += '\nsee statistics/chance_alowance_table.csv\n'
Z = zipfile.ZipFile(os.path.join(HERE, 'ALMA_Technosignatures_40pc.zip'))
NAMES = Z.namelist()
TOP = NAMES[0].split('/')[0]
assert all(n.split('/')[0] == TOP for n in NAMES), 'one top-level folder'
FILES = {n[len(TOP) + 1:] for n in NAMES if not n.endswith('/')}
DIRS = {'/'.join(f.split('/')[:k]) + '/' for f in FILES for k in range(1, f.count('/') + 1)}
if DRIVE == 1:
    FILES.discard('sensitivity/system_limits.csv')
SUB = sorted({d.split('/')[0] for d in DIRS})
# a path may be broken across lines after a '/' (\allowbreak): join "dir/ name" and "dir/\nname"
# ★ r36 integrator (rec2): a path broken at a PAGE break ("catalogues/" | page number | running head |
#   "re_extraction_status.csv") was read as "catalogues/18".  The page furniture is removed before the join (a
#   bare page-number line and the two running heads), so the join sees the path the reader sees; nothing
#   else is dropped and D2 is unchanged.
_HEADS = re.compile(r'^\s*(?:\d{1,3}|White & Dey|An ALMA Archival Technosignature Search within 40 pc)\s*$')
TXT_J = '\n'.join(l for l in TXT.split('\n') if not _HEADS.match(l))
J = re.sub(r'/\s+(?=[A-Za-z0-9_])', '/', TXT_J)
PAT = re.compile(r'(?<![A-Za-z0-9_/.])((?:%s)/[A-Za-z0-9_./-]*)' % '|'.join(map(re.escape, SUB)))
FOUND = sorted({p.rstrip('.,;:') for p in PAT.findall(J)})
ck('D1 the printed text names at least %d deposit paths' % MIN_PATHS, len(FOUND) >= MIN_PATHS, '%d found' % len(FOUND))
MISS = [p for p in FOUND if not (p in FILES or (p.endswith('/') and p in DIRS))]
ck('D2 every printed deposit path is a member of %s.zip under that exact name' % TOP, not MISS,
   'missing: %s' % MISS if MISS else ', '.join(FOUND))
if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
print('depositpaths_r36: %d printed paths, all in the archive%s'
      % (len(FOUND), '' if DRIVE is None else ' -- drive %d did NOT fire' % DRIVE))
