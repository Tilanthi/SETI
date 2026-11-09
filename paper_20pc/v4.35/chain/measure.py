import sys, re
import manuscript   # v4.10: the manuscript is split into sections/
# v4.10: measure the FLATTENED document.  Measuring the main file alone would
# report 263 lines of preamble and silently say the paper had shrunk by 96 per
# cent, which is the "check that cannot fail" defect in reverse.
f = sys.argv[1] if len(sys.argv) > 1 else manuscript.main_file()
L = manuscript.flat().split('\n')
# find boundaries
ai=next(i for i,l in enumerate(L) if l.startswith('\\appendix'))
bi=next(i for i,l in enumerate(L) if l.startswith('\\begin{thebibliography}'))
main=''.join(l+'\n' for l in L[:ai])
app=''.join(l+'\n' for l in L[ai:bi])
bib=''.join(l+'\n' for l in L[bi:])
def st(s):
    # strip comment-only lines for a secondary count
    return len(s)
print(f'{f} (flattened): total lines {len(L)}  appendix@{ai+1} bib@{bi+1}')
print(f'  MAIN (1..{ai}) chars={len(main)}')
print(f'  APPX ({ai+1}..{bi}) chars={len(app)}')
print(f'  BIB  chars={len(bib)}')
