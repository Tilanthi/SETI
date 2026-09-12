#!/bin/bash
cd "$(dirname "$0")"
V=technosignatures_20pc_v3.54
for i in 1 2 3; do pdflatex -interaction=nonstopmode $V.tex > /dev/null 2>&1; done
python3 - "$V" <<'PY'
import re,sys
v=sys.argv[1]
log=open(v+'.log',errors='ignore').read()
pg=re.findall(r'Output written.*\((\d+) pages',log)
err=re.findall(r'^! .*',log,re.M)
print('pages:',pg,'| errors:',len(err),'| undef refs/cites:',len(re.findall(r'Warning: (?:Reference|Citation)',log)),
      '| multdef:',len(re.findall(r'multiply defined',log)),
      '| overfull:',len(re.findall(r'Overfull',log)),'| underfull:',len(re.findall(r'Underfull',log)))
for e in err[:8]: print('  ERR',e)
for w in re.findall(r'Warning: (?:Reference|Citation)[^\n]*',log)[:10]: print('  ',w)
for w in re.findall(r'(?:Overfull|Underfull)[^\n]*',log)[:12]: print('  ',w)
# appendix page split
try:
    import fitz
    d=fitz.open(v+'.pdf')
    t3=[(p.number+1,f[3]) for p in d for f in p.get_fonts(full=True) if f[2]=='Type3']
    print('Type3 fonts:',len(t3),t3[:6])
    aux=open(v+'.aux',errors='ignore').read()
    m=re.search(r'\\newlabel\{page:appstart\}\{\{[^}]*\}\{(\d+)\}',aux)
    ap=int(m.group(1)) if m else None
    print('appendix starts p.',ap,'-> MAIN',(ap-1) if ap else '?','pp, APPENDIX',(len(d)-ap+1) if ap else '?','pp')
except Exception as e: print('pdf introspection skipped:',e)
PY
python3 measure.py $V.tex
python3 pagesplit.py $V.pdf

echo "--- arXiv abstract limit ---"
python3 abstract_limit.py
python3 abschars.py $V.pdf
