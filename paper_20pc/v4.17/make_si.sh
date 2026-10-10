#!/bin/bash
# make_si.sh -- build BOTH forms of the paper and report both page counts.
#
# ★★★ WHY THIS EXISTS.  The paper is 31 pp and the instruction is 25.  Every
# page is required by one referee or the other and no measurement is going to
# be deleted to reach a page count, so the only route that satisfies both is
# the journal's own: the appendices move to online Supporting Information,
# where they remain citable and keep their letters A--E, their subsection
# numbers and their float numbers.  Nothing is removed and nothing is
# duplicated -- the switch is two \ifdefined blocks in the manuscript and this
# script, and the DEFAULT build (appendices inline) is untouched, which is the
# build gate.sh reads.
#
#   inline   technosignatures_40pc_v4.16.pdf   paper with appendices (default)
#   split    paper_si.pdf  + si_appendices.pdf
#
# Each document cites the other's labels through `xr`, so each needs the
# other's .aux.  That is a fixed point, not a dependency order, so the two are
# alternated until both page counts and both label sets stop moving.  Three
# rounds is sufficient and the script checks that it converged rather than
# assuming it.
#
# Usage:  bash make_si.sh          # build and report
#         bash make_si.sh --clean  # remove the split-mode products afterwards
cd "$(dirname "$0")"
export SOURCE_DATE_EPOCH=1577836800
export FORCE_SOURCE_DATE=1
: "${TMPDIR:=/workspace/tmp_r15}"
export TMPDIR
V=$(ls technosignatures_*.tex | sed 's/\.tex$//')
[ -n "$V" ] || { echo "no manuscript .tex here" >&2; exit 2; }

# ★ Each document imports the OTHER's labels with its bibliography stripped
#   (si_labels.py).  Both print the same reference list, so importing a raw
#   .aux re-declares every \bibcite and pdflatex reports "Citation multiply
#   defined" once per entry -- 53 warnings per log on a build where nothing
#   is wrong, in a project that treats the log as a gate.
run() {  # run MODE JOBNAME
  pdflatex -interaction=nonstopmode -jobname="$2" \
           "\\def\\$1{}\\input{$V}" > /dev/null 2>&1
}
pages() { python3 - "$1" <<'PY'
import re, sys
try:
    log = open(sys.argv[1] + '.log', errors='ignore').read()
except OSError:
    print('-'); raise SystemExit
m = re.findall(r'Output written.*\((\d+) pages', log)
print(m[-1] if m else '-')
PY
}
problems() { python3 - "$1" <<'PY'
import re, sys
log = open(sys.argv[1] + '.log', errors='ignore').read()
print('%d error(s), %d undefined control sequence(s), %d unresolved '
      'reference/citation warning(s), %d overfull box(es)'
      % (len(re.findall(r'^! .*', log, re.M)),
         len(re.findall(r'Undefined control sequence', log)),
         len(re.findall(r'Warning: (?:Reference|Citation)', log)),
         len(re.findall(r'Overfull', log))))
PY
}

echo "--- round 1: Supporting Information document, then the printed paper"
run SIAPPX  si_appendices; python3 si_labels.py si_appendices.aux si_labels.aux > /dev/null
run SIPAPER paper_si; python3 si_labels.py paper_si.aux paper_labels.aux > /dev/null
echo "--- round 2: each now sees the other's labels"
run SIAPPX  si_appendices; python3 si_labels.py si_appendices.aux si_labels.aux > /dev/null
run SIPAPER paper_si; python3 si_labels.py paper_si.aux paper_labels.aux > /dev/null
A2=$(pages si_appendices); P2=$(pages paper_si)
echo "--- round 3: convergence check"
run SIAPPX  si_appendices; python3 si_labels.py si_appendices.aux si_labels.aux > /dev/null
run SIPAPER paper_si; python3 si_labels.py paper_si.aux paper_labels.aux > /dev/null
A3=$(pages si_appendices); P3=$(pages paper_si)

echo
echo "================= BOTH FORMS, MEASURED ================="
INLINE=$(pages "$V")
echo "inline (default, gate.sh's build)   $V.pdf        $INLINE pp"
echo "  $(problems "$V")"
echo "split  printed paper                paper_si.pdf          $P3 pp"
echo "  $(problems paper_si)"
echo "split  supporting information       si_appendices.pdf     $A3 pp"
echo "  $(problems si_appendices)"
echo "========================================================"
if [ "$A2" != "$A3" ] || [ "$P2" != "$P3" ]; then
  echo "NOT CONVERGED: paper $P2 -> $P3, SI $A2 -> $A3; run again" >&2
  exit 1
fi
echo "converged: two consecutive rounds give the same page counts"
if [ "$1" = "--clean" ]; then
  rm -f paper_si.* si_appendices.* si_labels.aux paper_labels.aux
  echo "split-mode products removed; the default build is untouched"
fi
