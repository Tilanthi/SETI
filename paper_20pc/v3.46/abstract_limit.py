#!/usr/bin/env python3
"""arXiv abstract length gate.

arXiv rejects abstracts longer than 1920 characters as rendered. This paper's
abstract was 2682 characters at v3.44 and would have been refused at
submission; nobody caught it for nine versions. Run this in gate.sh on every
build from now on.
"""
import re, sys, glob

tex = sorted(glob.glob('technosignatures_20pc_v*.tex'))[-1]
s = open(tex).read()
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', s, re.S)
if not m:
    sys.exit('abstract not found in ' + tex)
a = m.group(1)
# strip LaTeX commands, then braces/math markers, then collapse whitespace
p = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', ' ', a)
p = re.sub(r'[{}$~\\]', ' ', p)
p = ' '.join(p.split())
LIMIT = 1920
print('abstract: %d rendered characters (arXiv limit %d) -- %s'
      % (len(p), LIMIT, 'OK' if len(p) <= LIMIT else 'OVER BY %d' % (len(p) - LIMIT)))
sys.exit(0 if len(p) <= LIMIT else 1)
