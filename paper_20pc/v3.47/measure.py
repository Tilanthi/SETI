import sys,re
f=sys.argv[1] if len(sys.argv)>1 else 'technosignatures_20pc_v3.47.tex'
L=open(f,errors='ignore').read().split('\n')
# find boundaries
ai=next(i for i,l in enumerate(L) if l.startswith('\\appendix'))
bi=next(i for i,l in enumerate(L) if l.startswith('\\begin{thebibliography}'))
main=''.join(l+'\n' for l in L[:ai])
app=''.join(l+'\n' for l in L[ai:bi])
bib=''.join(l+'\n' for l in L[bi:])
def st(s):
    # strip comment-only lines for a secondary count
    return len(s)
print(f'{f}: total lines {len(L)}  appendix@{ai+1} bib@{bi+1}')
print(f'  MAIN (1..{ai}) chars={len(main)}')
print(f'  APPX ({ai+1}..{bi}) chars={len(app)}')
print(f'  BIB  chars={len(bib)}')
