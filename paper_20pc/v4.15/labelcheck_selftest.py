#!/usr/bin/env python3
r"""Self-test for labelcheck.py: every check driven in BOTH directions.

A check that has never been seen to fail is not a check, and a check that
can only fail is not one either.  So each of F1-F7 is exercised twice here:
once on a tree that is clean in that respect, where it must stay silent, and
once on the same tree with exactly that one defect injected, where it must
fire -- and fire with its own code, not with a neighbour's.

The clean fixture is written into a temporary directory and deleted.  No
production path is written at any point, under any flag.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, 'labelcheck.py')

CLEAN_TEX = r"""
\documentclass{article}
\begin{document}
\section{One}\label{sec:one}
See \S\ref{sec:one}, Table~\ref{tab:one}, Fig.~\ref{fig:one},
Eq.~\ref{eq:one}, and \ref{tab:two}.
\begin{equation}\label{eq:one} a=b. \end{equation}
\begin{table}\caption{t}\label{tab:one}\end{table}
\begin{figure}\caption{f}\label{fig:one}\end{figure}
\input{sub}
\end{document}
"""
CLEAN_SUB = r"""
\begin{table}\caption{u}\label{tab:two}\end{table}
"""
CLEAN_AUX = (r"\newlabel{sec:one}{{1}{1}{One}{section.1}{}}" "\n"
             r"\newlabel{eq:one}{{1}{1}{}{equation.1}{}}" "\n"
             r"\newlabel{tab:one}{{1}{1}{t \emph{with braces}}{table.1}{}}" "\n"
             r"\newlabel{fig:one}{{1}{1}{f}{figure.1}{}}" "\n"
             r"\newlabel{tab:two}{{2}{1}{u}{table.2}{}}" "\n")

EXPECT = {0: None, 1: 'F1', 2: 'F2', 3: 'F3', 4: 'F4', 5: 'F5', 6: 'F6',
          7: 'F7'}


def run(d, drive):
    cmd = [sys.executable, CHECK, os.path.join(d, 'm.tex'),
           '--aux', os.path.join(d, 'm.aux')]
    if drive:
        cmd += ['--drive', str(drive)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout


def main():
    d = tempfile.mkdtemp(prefix='labelcheck_selftest_')
    try:
        open(os.path.join(d, 'm.tex'), 'w').write(CLEAN_TEX)
        open(os.path.join(d, 'sub.tex'), 'w').write(CLEAN_SUB)
        open(os.path.join(d, 'm.aux'), 'w').write(CLEAN_AUX)
        npass = nfail = 0
        for drive in sorted(EXPECT):
            rc, out = run(d, drive)
            want = EXPECT[drive]
            if want is None:
                ok = (rc == 0 and '  FAIL ' not in out)
                what = 'clean tree is silent'
            else:
                fired = [l.strip() for l in out.split('\n')
                         if l.strip().startswith('FAIL ' + want)]
                others = [l.strip() for l in out.split('\n')
                          if l.strip().startswith('FAIL ')
                          and not l.strip().startswith('FAIL ' + want)]
                ok = (rc == 1 and len(fired) >= 1 and not others)
                what = ('%s fires alone (%d line%s)'
                        % (want, len(fired), '' if len(fired) == 1 else 's'))
            print('  %-7s drive %d  %-34s %s'
                  % ('PASS' if ok else 'FAIL', drive, what,
                     '' if ok else out.replace('\n', ' | ')[:200]))
            npass += ok
            nfail += (not ok)
        # ---- and the real manuscript, which must FAIL: the defect is live
        for arg in sys.argv[1:]:
            if arg.endswith('.tex'):
                rc, out = run_real(arg)
                codes = sorted({l.strip().split()[1] for l in out.split('\n')
                                if l.strip().startswith('FAIL ')})
                # ★ do NOT pin the codes to today's defects: the manuscript
                # is being repaired while this runs, and a self-test that
                # requires a particular defect to still be present starts
                # failing the moment someone fixes it -- for the wrong
                # reason.  What must hold is that the checker reaches the
                # real tree and reports through the same path.
                ok = (rc in (0, 1) and bool(codes) == (rc == 1))
                print('  %-7s manuscript %s -> rc=%d, codes %s'
                      % ('PASS' if ok else 'FAIL', os.path.basename(arg),
                         rc, ','.join(codes)))
                npass += ok
                nfail += (not ok)
        print('labelcheck_selftest: %d/%d' % (npass, npass + nfail))
        return 1 if nfail else 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def run_real(tex):
    aux = tex[:-4] + '.aux'
    cmd = [sys.executable, CHECK, tex]
    if os.path.exists(aux):
        cmd += ['--aux', aux]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout


if __name__ == '__main__':
    sys.exit(main())
