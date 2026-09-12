#!/usr/bin/env python3
"""Round-9 Discussion restructure (R3 Discussion reorder + R3-4 f95
demotion + R4-A7 how-to-cite).  Block surgery with MISS checks; run
once, then delete."""
import re, sys

FN = 'technosignatures_20pc_v3.47.tex'
t = open(FN).read()
miss = []

def cut(a, b):
    """Return (text_between, new_full_text) with the span removed."""
    global t
    i, j = t.find(a), t.find(b)
    if i < 0 or j < 0 or j <= i:
        miss.append('CUT %r..%r' % (a[:40], b[:40])); return None, t
    return t[i:j], t[:i] + t[j:]

# ---- anchors -------------------------------------------------------------
SUB1 = '\\subsection{What transmitter would this survey detect?}'
SUB2 = '\\subsection{An illustrative population-inference framework}'
SUB3 = '\\subsection{Priorities for the next release}'

# ---- 1. lift the pre-6.1 opening block out of the Discussion ------------
blockA, t = cut('\\section{Discussion}\n\\label{sec:discussion}\n', SUB1)
if blockA:
    blockA = blockA[len('\\section{Discussion}\n\\label{sec:discussion}\n'):]
    # trim + fix stale number inside blockA
    old = ('a false-positive\ncontrol purchased with 5.9 per cent of gross bandwidth and one')
    if old not in blockA:
        miss.append('blockA 5.9 per cent wording')
    blockA = blockA.replace(
        'a false-positive\ncontrol purchased with 5.9 per cent of gross bandwidth and one',
        'a false-positive\ncontrol purchased with \\MaskGrossPct{} per cent of gross bandwidth and one')
    old = ('The\nflagged-window dispositions -- CO towards $\\beta$\\,Pic, CP$-$72~2713\n'
           'unclassified and statistically non-significant at the survey level\n'
           '(Fig.~\\ref{fig:cp72ctrl}), AU~Mic unflagged --\n'
           'are established in \\S\\ref{sec:technosearch} and not repeated here.')
    if old not in blockA:
        miss.append('blockA dispositions sentence')
    blockA = blockA.replace(old, (
        'The flagged-window dispositions are established in\n'
        '\\S\\ref{sec:technosearch} and not repeated here.'))

# ---- 2. retitle 6.1 -------------------------------------------------------
old = '\\subsection{What transmitter would this survey detect?}'
if old not in t: miss.append('SUB1 title')
t = t.replace(old,
    '\\subsection{What signals could ALMA archival data actually detect?}')

# ---- 3. occurrence: split framework (keep) from demonstration (move) -----
demo_start = ('\\noindent \\emph{The demonstration number, with every caveat in the\n'
              'same breath.}')
demo_end = 'Because selection is on ALMA archival coverage alone,'
box_end = 'noindent\\rule{\\columnwidth}{0.4pt}\n\\medskip\n'
i = t.find(demo_start)
j = t.find(demo_end)
sub2 = t.find(SUB2)
if not (0 <= sub2 < i < j):
    miss.append('demo paragraph location (i=%d j=%d sub2=%d)' % (i, j, sub2))
else:
    demo_block = t[i:j]          # demonstration + independence paragraphs
    t = t[:i] + t[j:]

# ---- 4. replace SUB2 heading with the null-meaning subsection ------------
old = (SUB2 + '\n\\label{sec:occurrence}\n\n'
       'What a zero-detection result bounds is fully conditioned. This\n'
       'subsection demonstrates the occurrence-rate formalism that will be\n'
       'applied once configuration-dependent completeness is established for\n'
       'the completed survey; it states no survey result, no $f_{95}$ number\n'
       'appears among the headline quantities of Table~\\ref{tab:searchspace},\n'
       'and the one demonstration number below carries its strongest caveat\n'
       'in the same breath. The per-system detection probability factorises\n'
       'into four terms,')
new = ('What the zero-detection result bounds is stated once here and\n'
       'carried everywhere below: fully conditioned, on each target\'s own\n'
       'searched frequencies, epochs and morphology class. The occurrence\n'
       'formalism that will be applied once configuration-dependent\n'
       'completeness is established for the completed survey factorises the\n'
       'per-system detection probability into four terms,')
if old not in t: miss.append('SUB2 intro')
t = t.replace(old, new)

# ---- 5. insert how-to-cite pointer after the reading-rule box ------------
anchor = box_end + '\n\n' + new.split('factorises')[0]
# safer: find the box end immediately before the (former) demo start
i2 = t.find(new)
k2 = t.rfind(box_end, 0, i2)
if k2 < 0: miss.append('reading-rule box before framework')
else:
    ins = (box_end + '\n'
           '\\noindent The numerical demonstrations -- the $f_{95}$\n'
           'evaluation, its bracketing, duty-cycle variants and\n'
           'transfer-error analysis -- are consolidated in\n'
           'Appendix~\\ref{app:population}, labelled \\emph{illustrative\n'
           'calculation only}: they state no survey result, appear among no\n'
           'headline quantities (Table~\\ref{tab:searchspace}), and should\n'
           'be cited, if at all, only with the $F_i{=}D_i{=}1$ conditioning\n'
           'and the single-configuration completeness transfer attached --\n'
           'never as a measured occurrence limit, and never as a statement\n'
           'about the 40\\,pc stellar population.\n')
    t = t[:k2] + ins + t[k2 + len(box_end):]

# ---- 6. move blockA under the new null-meaning subsection ----------------
# insert right after the three-cases material, i.e. before the framework
# paragraph beginning "What the zero-detection result bounds"
i3 = t.find('What the zero-detection result bounds')
if i3 < 0 or blockA is None: miss.append('insert point for blockA')
else:
    head = ('\\subsection{What does the null result mean?}\n'
            '\\label{sec:null}\n\n')
    t = t[:i3] + head + blockA + '\n' + t[i3:]

# ---- 7. retarget sec:occurrence refs -------------------------------------
n = t.count('\\ref{sec:occurrence}')
t = t.replace('\\S\\ref{sec:occurrence}', '\\S\\ref{sec:null}')
t = t.replace('(\\S\\ref{sec:occurrence}', '(\\S\\ref{sec:null}')
left = t.count('\\ref{sec:occurrence}')
print('sec:occurrence refs retargeted: %d -> %d left' % (n, left))

# ---- 8. futurework: lift "Second" into its own instrument subsection -----
i4 = t.find('\\emph{Second, use visibilities rather than extracted spectra.}')
i5 = t.find('\\emph{Third, enlarge the control ensemble')
if not (0 <= i4 < i5): miss.append('Second/Third anchors')
else:
    vis_block = t[i4:i5]
    t = t[:i4] + t[i5:]
    vis_body = vis_block[len('\\emph{Second, use visibilities rather than extracted spectra.} '):].rstrip() + '\n'
    inst = ('\\subsection{ALMA as a technosignature instrument: strengths and limits}\n'
            '\\label{sec:instrument}\n\n'
            "ALMA's advantages for this programme are four: aperture and\n"
            'receiver temperature give mm-wave sensitivities no single dish\n'
            'reaches; the tuning range, 125--495\\,GHz here, is essentially\n'
            'unsearched territory; interferometric spatial discrimination --\n'
            'the control-ring statistic of \\S\\ref{sec:statistic} -- tests a\n'
            'feature\'s position against \\NCtrl{} alternatives, which\n'
            "single-dish and beamformed searches cannot; and the archive\n"
            'itself supplies \\NEB{} public execution blocks re-processable\n'
            'without new allocations. Each strength has its mirror. Native\n'
            'channelisation reaches 15.3\\,kHz at best, orders coarser than\n'
            'the Hz resolution of dedicated narrowband surveys, so the\n'
            'search tests unresolved spectral excess, not fine structure;\n'
            'coverage is fragmented into \\UnionIntervals{} frequency islands\n'
            'weighted by other science; the molecular-line mask deliberately\n'
            'excludes \\MaskUnionPct{} per cent of the union\n'
            '(\\S\\ref{sec:technosearch}); configurations are heterogeneous,\n'
            'so no completeness transfers between them (\\S\\ref{sec:null});\n'
            'and targeting is interest-driven, not uniform (\\S\\ref{sec:sample}).\n'
            'The largest unused advantage is the visibilities themselves:\n'
            + vis_body + '\n')
    # place before the (retitled) futurework subsection
    old5 = '\\subsection{Priorities for the next release}'
    if old5 not in t: miss.append('SUB3 anchor')
    t = t.replace(old5, inst + '\n' +
        '\\subsection{A next-generation ALMA technosignature search}')

# fix ordinals in futurework after removing Second
for a, b in [('\\emph{Third, enlarge the control ensemble',
              '\\emph{Enlarge the control ensemble'),
             ('\\emph{Fourth, extend the injection campaign',
              '\\emph{Extend the injection campaign'),
             ('\\emph{First: drift discrimination on coarse windows.}',
              '\\emph{Drift discrimination on coarse windows.}')]:
    if a not in t: miss.append('ordinal %r' % a[:30])
    t = t.replace(a, b)
old = ('Four changes would enlarge what this experiment can say, ranked by\n'
       'how much signal space they buy.')
if old not in t: miss.append('futurework intro')
t = t.replace(old, ('Three changes would enlarge what this experiment can\n'
                    'say, ranked by how much signal space they buy.'))

# ---- 9. append the demo block to Appendix Q ------------------------------
i6 = t.find('\\label{app:population}')
if i6 < 0 or demo_block is None: miss.append('app:population')
else:
    anchor2 = ('still less the 40\\,pc stellar population.\n')
    j6 = t.find(anchor2, i6)
    if j6 < 0: miss.append('app Q intro anchor')
    else:
        j6 += len(anchor2)
        demo2 = ('\n\\emph{Illustrative calculation only.} The demonstration\n'
                 'number and its sensitivity analysis follow; none of it is a\n'
                 'survey result. '
                 + demo_block.removeprefix(
                     '\\noindent \\emph{The demonstration number, with every caveat in the\nsame breath.} '
                 ).replace('Appendix~\\ref{app:population}', 'this appendix') + '\n')
        t = t[:j6] + demo2 + t[j6:]

# ---- 10. Appendix Q intro wording ----------------------------------------
old = ('This appendix consolidates the material condensed in\n'
       '\\S\\ref{sec:occurrence}.')
if old not in t: miss.append('app Q intro sentence')
t = t.replace(old, ('This appendix consolidates the numerical demonstrations\n'
                    'condensed out of \\S\\ref{sec:null}, labelled\n'
                    '\\emph{illustrative calculation only} throughout.'))

open(FN, 'w').write(t)
print('MISS:', miss if miss else 'none')
sys.exit(1 if miss else 0)
