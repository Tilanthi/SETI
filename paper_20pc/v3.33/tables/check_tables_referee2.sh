#!/bin/bash
# Standalone-compile each referee-2 table in a minimal openjournal document.
# The paper's own class and preamble; survey_numbers.tex supplies \NCtrl etc.;
# fake .aux entries satisfy the cross-references into the manuscript body so a
# standalone run has zero undefined references.
#
# Usage:  bash tables/check_tables_referee2.sh      (from the v3.30 directory)
set -u
V="$(cd "$(dirname "$0")/.." && pwd)"
W=$(mktemp -d)
cp "$V"/openjournal.cls "$V"/epsf.sty "$V"/survey_numbers.tex "$W"/ 2>/dev/null
for t in tab_bothstats tab_allhits tab_flagged_v331; do
  cp "$V/tables/$t.tex" "$W"/
  cat > "$W/test_$t.tex" <<EOF
\documentclass{openjournal}
\usepackage[T1]{fontenc}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{tabularx}
\usepackage{booktabs}
\input{survey_numbers}
\makeatletter
\renewenvironment{bottompar}{\setbox\z@\vbox\bgroup}{\egroup}
% stand in for the labels that live in the manuscript body
\@namedef{r@eq:tstar}{{1}{1}}
\@namedef{r@app:conventions}{{A}{1}}
\makeatother
\begin{document}
\title{Standalone table test}
\author{X}
\begin{abstract}Standalone compile test.\end{abstract}
\section{Test}
\showthe\textwidth
\showthe\columnwidth
Filler text.
\input{$t}
\end{document}
EOF
  (cd "$W" && pdflatex -interaction=nonstopmode "test_$t.tex" >/dev/null 2>&1
             pdflatex -interaction=nonstopmode "test_$t.tex" >/dev/null 2>&1)
  err=$(grep -c '^!' "$W/test_$t.log")
  und=$(grep -c 'undefined' "$W/test_$t.log")
  ovf=$(grep -c 'Overfull' "$W/test_$t.log")
  rows=$(grep -c '\\\\$' "$V/tables/$t.tex")
  pg=$(pdfinfo "$W/test_$t.pdf" 2>/dev/null | awk '/Pages/{print $2}')
  printf '%-18s errors=%s undefined=%s overfull=%s pages=%s texlines=%s\n' \
         "$t" "$err" "$und" "$ovf" "$pg" "$rows"
  grep -n 'Overfull\|^!' "$W/test_$t.log" | sed 's/^/    /'
done
grep -m1 -A1 '> [0-9.]*pt' "$W/test_tab_bothstats.log" | head -2
echo "work dir: $W"
