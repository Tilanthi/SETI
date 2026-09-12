#!/bin/bash
# Measure every float's typeset height (pt) by patching \@largefloatcheck in a
# scratch copy.  Column height is 694 pt.  Usage: ./floatsize.sh
cd "$(dirname "$0")"
rm -rf /tmp/fm && mkdir -p /tmp/fm
cp -r figures tables *.tex *.cls *.sty *.bib /tmp/fm/ 2>/dev/null
cd /tmp/fm
python3 - <<'PY'
import re
patch=r'''\makeatletter
\let\astra@lfc\@largefloatcheck
\def\@largefloatcheck{\typeout{ASTRAFLOAT ht=\the\ht\@currbox}\astra@lfc}
\makeatother
'''
import glob
for fn in ['technosignatures_20pc_v3.51.tex']+glob.glob('tab_*.tex'):
    s=open(fn).read()
    if fn.startswith('techno'):
        s=s.replace(r'\begin{document}',patch+r'\begin{document}',1)
    s=re.sub(r'\\end\{(table\*?|figure\*?)\}',lambda m:'\\typeout{ASTRAID %s}'%m.group(1)+m.group(0),s)
    open(fn,'w').write(s)
PY
pdflatex -interaction=nonstopmode technosignatures_20pc_v3.51.tex >/dev/null 2>&1
cd - >/dev/null
python3 - <<'PY'
import re
log=open('/tmp/fm/technosignatures_20pc_v3.51.log',errors='ignore').read()
hts=[float(x) for x in re.findall(r'ASTRAFLOAT ht=([\d.]+)pt',log)]
src=open('technosignatures_20pc_v3.51.tex').read()
app=src.index('\n\\appendix')
ends=[]
for m in re.finditer(r'\\(?:input\{(tab_\w+)\}|end\{(table\*?|figure\*?)\})',src):
    if m.group(1):
        try: sub=open(m.group(1)+'.tex').read()
        except: continue
        for mm in re.finditer(r'\\end\{(table\*?|figure\*?)\}',sub):
            lab=re.search(r'\\label\{([^}]*)\}',sub)
            ends.append((m.start(),lab.group(1) if lab else '?',mm.group(1)))
    else:
        b=src.rfind('\\begin{'+m.group(2)+'}',0,m.start())
        body=src[b:m.start()]
        lab=re.search(r'\\label\{([^}]*)\}',body)
        ends.append((b,lab.group(1) if lab else '?',m.group(2)))
tm=ta=0.0
for (pos,lab,kind),h in zip(ends,hts):
    reg='APPX' if pos>app else 'MAIN'
    if reg=='MAIN': tm+=h
    else: ta+=h
    print(f"{h:7.1f}pt  {h/694*100:5.1f}%pg  {reg} {kind:7s} {lab}")
print(f"TOTAL MAIN floats {tm:8.1f}pt = {tm/694:.2f} pages")
print(f"TOTAL APPX floats {ta:8.1f}pt = {ta/694:.2f} pages")
PY
