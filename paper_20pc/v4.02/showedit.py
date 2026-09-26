#!/usr/bin/env python3
"""Print the full EDITS entry (or entries) for given ids."""
import re, sys
FILES = ['/shared/ASTRA/reviews/v352_referee_E_EDITS.md',
         '/shared/ASTRA/reviews/v352_referee_F_EDITS.md']
want = set(sys.argv[1:])
for path in FILES:
    block = open(path).read()
    if '## EDITS' in block:
        block = block.split('## EDITS', 1)[1]
    for m in re.finditer(r'^###\s+(\S+)\s*\[(MUST|SHOULD|DECLINE[^\]]*)\].*?(?=\n###\s|\Z)',
                         block, re.S | re.M):
        if m.group(1) in want:
            print('=' * 70)
            print(m.group(0).rstrip())
