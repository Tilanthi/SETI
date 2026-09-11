#!/bin/bash
cd /workspace/SETI/paper_20pc/v3.41/
for i in 1 2 3; do pdflatex -interaction=nonstopmode technosignatures_20pc_v3.41.tex > /dev/null 2>&1; done
python3 - <<'PY'
import re
log=open('technosignatures_20pc_v3.41.log',errors='ignore').read()
pg=re.findall(r'Output written.*\((\d+) pages',log)
err=re.findall(r'^! .*',log,re.M)
print('pages:',pg,'| errors:',len(err),'| undef refs/cites:',len(re.findall(r'Warning: (?:Reference|Citation)',log)),
      '| multdef:',len(re.findall(r'multiply defined',log)),
      '| overfull:',len(re.findall(r'Overfull',log)),'| underfull:',len(re.findall(r'Underfull',log)))
for e in err[:6]: print('  ERR',e)
for w in re.findall(r'Warning: (?:Reference|Citation)[^\n]*',log)[:8]: print('  ',w)
PY
python3 measure.py
