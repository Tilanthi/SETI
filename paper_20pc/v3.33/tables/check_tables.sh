#!/bin/bash
# Standalone-compile each generated table in a minimal openjournal document.
# Usage:  bash tables/check_tables.sh          (run from the v3.28 directory)
set -u
V="$(cd "$(dirname "$0")/.." && pwd)"
W=$(mktemp -d)
cp "$V"/openjournal.cls "$V"/epsf.sty "$W"/ 2>/dev/null
for t in tab_selection tab_perband tab_perstar; do
  cp "$V/tables/$t.tex" "$W"/
  cat > "$W/test_$t.tex" <<EOF
\documentclass{openjournal}
\usepackage[T1]{fontenc}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{tabularx}
\usepackage{booktabs}
\makeatletter
\renewenvironment{bottompar}{\setbox\z@\vbox\bgroup}{\egroup}
\makeatother
\begin{document}
\title{Standalone table test}
\author{X}
\begin{abstract}Standalone compile test.\end{abstract}
\section{Test}
Filler text.
\input{$t}
\end{document}
EOF
  (cd "$W" && pdflatex -interaction=nonstopmode "test_$t.tex" >/dev/null 2>&1
             pdflatex -interaction=nonstopmode "test_$t.tex" >/dev/null 2>&1)
  err=$(grep -c '^!' "$W/test_$t.log")
  ovf=$(grep -c 'Overfull' "$W/test_$t.log")
  pg=$(pdfinfo "$W/test_$t.pdf" 2>/dev/null | awk '/Pages/{print $2}')
  printf '%-14s errors=%s overfull=%s pages=%s\n' "$t" "$err" "$ovf" "$pg"
  grep -n 'Overfull' "$W/test_$t.log"
done
echo "work dir: $W"
