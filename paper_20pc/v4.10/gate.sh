#!/bin/bash
cd "$(dirname "$0")"
# v4.09: pin the timestamp pdflatex stamps into the PDF (and writes into the
# log), as make_all.sh already does for the figures.  Without this the PDF is
# reproducible in content but not in bytes, so a gate re-run after a push left
# the deposited PDF differing from the one in the repository for no reason at
# all.  Same epoch as make_all.sh: 2020-01-01T00:00:00Z.
export SOURCE_DATE_EPOCH=1577836800
export FORCE_SOURCE_DATE=1
# ★ The stem is DERIVED, not typed: the manuscript filename carries the
# version, and hard-coding it here is why a version bump used to need
# thirteen edits and still broke something that failed late.  Exactly one
# manuscript .tex must exist in this directory, which is the same rule
# manuscript.main_file() enforces for the Python tools.
V=$(cd "$(dirname "$0")" && ls technosignatures_*.tex | sed 's/\.tex$//')
[ "$(printf %s "$V" | wc -l)" -eq 0 ] && [ -n "$V" ] || {
  echo "expected exactly one manuscript .tex, found: $V" >&2; exit 2; }
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

echo "--- generator/round-file ownership (v3.99: added after a silent overwrite) ---"
python3 roundcollide.py

# ---------------------------------------------------------------------------
# These four gates were in make_all.sh only.  make_all.sh regenerates; gate.sh
# checks what is on disk -- so a build that skipped the regeneration (which is
# every build during a prose pass, by the standing rule that make_all.sh must
# not run while prose is in flux) ran NONE of them.  A stray build could
# therefore hide a duplicate label, a retired macro name, an orphan figure or
# a ledger that is not the adopted crossing list, which is exactly the class of
# defect each exists to catch.  They are cheap and they read only the tree.
echo "--- the reference layer (duplicate, dangling and aliased labels) ---"
python3 labelcheck.py "$V.tex" --aux "$V.aux"
echo "--- retired macro NAMES may not appear in the manuscript ---"
python3 retired.py
echo "--- figures: none built-and-uncited, none cited-and-missing ---"
python3 figorphan.py
echo "--- the typeset ledger IS the adopted crossing list ---"
# Pass the fragment the MANUSCRIPT inputs, not the gate's own default.  Its
# docstring says it reads "the fragment the manuscript inputs" and it does
# not -- it hard-codes tab_ledger.tex -- so while the manuscript inputs any
# other ledger fragment the gate passes on a table the reader never sees.
# Deriving the argument here makes the claim true from this side.
LEDGFRAG=$(python3 - <<'PYEOF'
import re, sys
sys.path.insert(0, '.')
import manuscript
# The manuscript inputs TWO ledger fragments -- the crossing ledger and its
# summary -- and the summary is \input first, so taking the first match
# handed the gate a table with no crossing rows and it reported 3 FAIL on a
# fragment it was never meant to read.  Take the per-crossing ledger: the
# exact name if present, otherwise the tab_ledger* fragment with the most
# rows, which is the one a reader reads crossing by crossing.
cand = re.findall(r'\\input\{(tab_ledger[A-Za-z0-9_]*)\}', manuscript.flat())
if 'tab_ledger' in cand:
    print('tab_ledger.tex')
elif cand:
    import os
    print(max(cand, key=lambda c: sum(
        1 for l in open(c + '.tex', errors='ignore')
        if l.strip().endswith('\\\\'))) + '.tex')
else:
    print('tab_ledger.tex')
PYEOF
)
echo "    fragment the manuscript inputs: $LEDGFRAG"
python3 ledgergate.py "$LEDGFRAG"

echo "--- cross-reference resolution (R2-t2) ---"
python3 xrefcheck.py

echo "--- macro synonyms and ledger identities (referee 2, M2) ---"
python3 macrosyn.py
echo "--- primary-statistic consistency (referee 2, v3.99) ---"
python3 consistency_v399.py

echo "--- macro leakage (referee 2, v3.99) ---"
echo "--- prose literals vs macros (referee 2, M6) ---"
python3 prosenum_v399.py
python3 macroleak.py

echo "--- every integer in running prose is registered (referee 2, item 1) ---"
python3 intsweep.py

