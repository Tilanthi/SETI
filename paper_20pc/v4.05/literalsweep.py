#!/usr/bin/env python3
"""Find numbers typed into the prose that a generated macro also carries.

Round 4's structural finding was that nearly every remaining defect is one
mechanism: **a quantity that exists twice**, once as a macro and once as a
literal somebody typed. The macro moves when the sample moves; the literal
does not. Three rounds of review found eleven instances of this and the
fourth found nine more, so the answer is a tool, not more vigilance.

This script reads the manuscript, strips maths and tabular bodies, and for
every numeric literal in the running prose asks whether a macro carries
the same value. A hit is not necessarily a bug -- "5 sigma" and "two
transitions" are literals on purpose -- so it reports and ranks rather than
failing the build. What it is for is the case where the literal matches a
macro's value, because that is the one that silently goes stale, and the
case where a literal is *close* to a macro's value but not equal, because
that is a literal the sample has already moved past.

Usage:  python3 literalsweep.py [--strict]
        --strict exits non-zero if any near-miss is found.
"""
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = [f for f in glob.glob(os.path.join(HERE, 'technosignatures_40pc_v*.tex'))
       if 'Notes' not in f]
TEX.sort()
SRC = TEX[-1]

MACRO = {}
for fn in glob.glob(os.path.join(HERE, 'survey_numbers*.tex')) \
        + [os.path.join(HERE, 'regen_count.tex')]:
    if not os.path.exists(fn):
        continue
    for m in re.finditer(r'\\newcommand\{\\([A-Za-z]+)\}\{(.*?)\}\s*$',
                         open(fn).read(), re.M):
        MACRO.setdefault(m.group(1), m.group(2))


def value(body):
    b = body.replace('\\,', '').replace('$', '').replace('{', '').replace('}', '')
    m = re.match(r'^([\d.]+)\\times10\^(-?\d+)$', b)
    if m:
        try:
            return float(m.group(1)) * 10 ** int(m.group(2))
        except ValueError:
            return None
    b = b.replace(',', '')
    try:
        return float(b)
    except ValueError:
        return None


NUM = {}
for k, v in MACRO.items():
    f = value(v)
    if f is not None:
        NUM[k] = f

# Numbers that are legitimately literal: significance levels, small counts
# used as words, years, section numbers, physical constants, percentages of
# a hundred, and the frequencies of named transitions.
ALLOW = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 20, 40, 50, 90, 95,
         100, 1000, 1.96, 0.5, 0.05, 1.4826, 2.5, 1.5, 0.1, 0.9, 0.3, 0.25,
         230, 345, 115, 84, 950, 1420}

text = open(SRC).read()
# drop the preamble, maths, tabular bodies, verbatim and comments
text = text[text.index('\\begin{document}'):]
if '\\begin{thebibliography}' in text:
    text = text[:text.index('\\begin{thebibliography}')]
text = re.sub(r'(?m)(?<!\\)%.*$', '', text)
text = re.sub(r'\$[^$]*\$', ' ', text)
text = re.sub(r'\\begin\{tabular\}.*?\\end\{tabular\}', ' ', text, flags=re.S)
text = re.sub(r'\\input\{[^}]*\}', ' ', text)
text = re.sub(r'\\(?:label|ref|cite[a-z]*|includegraphics)\{[^}]*\}', ' ', text)
text = re.sub(r'\\[A-Za-z]+', ' ', text)      # macro calls are fine

EXACT, NEAR = [], []
for m in re.finditer(r'(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![\w])', text):
    lit = m.group(1)
    f = value(lit)
    if f is None or f in ALLOW or f > 1e6:
        continue
    ctx = ' '.join(text[max(0, m.start() - 55):m.end() + 45].split())
    before = text[max(0, m.start() - 24):m.start()]
    # skip star designations and years: they are numbers on purpose
    if re.search(r'(?:CP|HD|GJ|GL|LP|BD|WD|HR|HIP|TWA|UCAC|LHS|TYC|Wolf|'
                 r'Gaia DR3|2MASS)[\s\-+~]*\d*[\s\-+~]*$', before):
        continue
    if 1990 <= f <= 2100 and f == int(f):
        continue
    hits = [k for k, v in NUM.items() if v == f]
    if hits:
        EXACT.append((lit, sorted(hits)[:4], ctx))
        continue
    # a literal within 25 per cent of a macro of the same order is a
    # candidate stale value: the sample moved and the literal did not
    # A stale sample value sits within a few per cent of its macro; a
    # 25 per cent band just collects years and catalogue designations.
    cand = [(k, v) for k, v in NUM.items()
            if v and 0.95 < f / v < 1.055 and f != v and v >= 20]
    if cand and f >= 10:
        cand.sort(key=lambda kv: abs(kv[1] - f))
        NEAR.append((lit, cand[:3], ctx))

print('literal sweep of %s' % os.path.basename(SRC))
print('\n%d prose literals equal to a generated macro:' % len(EXACT))
for lit, ks, ctx in EXACT:
    print('  %-10s == %-42s  %s' % (lit, ','.join(ks), ctx[:90]))
print('\n%d prose literals within 5 per cent of a macro (possible stale value):'
      % len(NEAR))
for lit, cs, ctx in NEAR:
    print('  %-10s ~ %-42s  %s'
          % (lit, ','.join('%s=%g' % (k, v) for k, v in cs), ctx[:90]))
if '--strict' in sys.argv and (EXACT or NEAR):
    sys.exit(1)
