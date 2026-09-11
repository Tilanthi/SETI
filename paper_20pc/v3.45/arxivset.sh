#!/bin/bash
# Rebuild the arXiv upload set from the manuscript's own \input and
# \includegraphics, in an empty directory, and report every gate.
cd "$(dirname "$0")"
D=${1:-/tmp/arxiv}
rm -rf "$D"; mkdir -p "$D/figures"
python3 - "$D" <<'PY'
import re, os, shutil, sys
D = sys.argv[1]
src = os.getcwd()
tex = open(src + '/technosignatures_20pc_v3.45.tex').read()
inputs = sorted(set(re.findall(r'\\input\{([^}]*)\}', tex)))
figs = sorted(set(re.findall(r'\\includegraphics\[[^\]]*\]\{([^}]*)\}', tex)))
files = ['technosignatures_20pc_v3.45.tex', 'openjournal.cls', 'epsf.sty'] + [i + '.tex' for i in inputs]
for f in files:
    shutil.copy(os.path.join(src, f), os.path.join(D, os.path.basename(f)))
for f in figs:
    shutil.copy(os.path.join(src, f), os.path.join(D, f))
print('%d items: %d tex/cls/sty + %d figures' % (len(files) + len(figs), len(files), len(figs)))
for f in figs:
    print('   ', f)
PY
cd "$D"
for i in 1 2 3; do pdflatex -interaction=nonstopmode technosignatures_20pc_v3.45.tex > /dev/null 2>&1; done
python3 - <<'PY'
import re, pymupdf
log = open('technosignatures_20pc_v3.45.log', errors='ignore').read()
print('pages:', re.findall(r'Output written.*\((\d+) pages', log),
      '| errors:', len(re.findall(r'^! .*', log, re.M)),
      '| undef:', len(re.findall(r'Warning: (?:Reference|Citation)', log)),
      '| multdef:', len(re.findall(r'multiply defined', log)),
      '| overfull:', len(re.findall(r'Overfull', log)),
      '| underfull:', len(re.findall(r'Underfull', log)),
      '| missing files:', len(re.findall(r'LaTeX Error: File', log)))
d = pymupdf.open('technosignatures_20pc_v3.45.pdf')
print('Type3:', sum(1 for p in d for f in p.get_fonts(full=True) if f[2] == 'Type3'))
PY
du -sh "$D"
