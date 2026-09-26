#!/usr/bin/env python3
"""Referee 2, item 1, last bullet: "Add to the released regeneration script an
assertion covering every integer quoted in running text, not only the 41
headline numbers."

`prosenum_v399.py` is deliberately narrow -- a handful of phrase patterns tied
to a handful of macros.  That is why the stale "13 flagged / 4 unattributed"
version survived: none of its integers matched one of those patterns.

This gate is the complement.  It enumerates EVERY integer literal in the
manuscript's running prose and requires each distinct value to be registered
in `intsweep_registry.json` with one of two dispositions:

  "macro": "<Name>"   the literal duplicates a generated macro.  The gate
                      asserts that the macro's CURRENT value still equals the
                      literal, so a number that moves in the catalogue and not
                      in the prose fails the build.  This is the class of
                      defect the referee found.

  "literal": "<why>"  the integer is not a survey quantity -- a year, a
                      transition quantum number, an ALMA band, a power of ten,
                      an instrument constant -- and the reason is recorded.

An unregistered integer fails the build.  Registering one is deliberate work,
which is the point: a new number in the prose has to be accounted for.

Running text means: the body of the manuscript with comments, math, tabular
bodies, labels, references, citations, \\input arguments, file names and the
bibliography removed.  Captions ARE included; a caption is prose a reader
believes.

Exit status 1 on any unregistered or disagreeing integer.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'technosignatures_40pc_v4.04.tex')
REG = os.path.join(HERE, 'intsweep_registry.json')


def macros():
    out = {}
    for fn in sorted(os.listdir(HERE)):
        if fn.startswith('survey_numbers') and fn.endswith('.tex'):
            for line in open(os.path.join(HERE, fn)):
                m = re.match(r'\\newcommand\{\\(\w+)\}\{(.*)\}\s*$', line.strip())
                if m:
                    out[m.group(1)] = m.group(2)
    return out


def prose(tex):
    # the preamble is not running text
    tex = tex.split(r'\begin{document}')[-1]
    # bibliography and everything after it
    tex = tex.split(r'\begin{thebibliography}')[0]
    # verbatim-ish identifiers (execution block uids, commit hashes) carry
    # digits that are not quantities
    tex = re.sub(r'\\texttt\{[^{}]*\}', ' ', tex)
    # comments
    tex = re.sub(r'(?<!\\)%.*', '', tex)
    # display and inline math
    tex = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', ' ', tex, flags=re.S)
    tex = re.sub(r'\\begin\{align\*?\}.*?\\end\{align\*?\}', ' ', tex, flags=re.S)
    tex = re.sub(r'\\\[.*?\\\]', ' ', tex, flags=re.S)
    tex = re.sub(r'(?<!\\)\$[^$]*\$', ' ', tex, flags=re.S)
    # tabular bodies: the numbers in them are generated or are table furniture
    tex = re.sub(r'\\begin\{tabular\}.*?\\end\{tabular\}', ' ', tex, flags=re.S)
    # structural arguments that legitimately carry digits
    tex = re.sub(r'\\(?:label|ref|eqref|cite[tp]?|input|includegraphics|'
                 r'bibitem|altaffiltext|newcommand|DeclareRobustCommand|'
                 r'setlength|addtolength|usepackage|documentclass|'
                 r'newcolumntype|enlargethispage|hspace|vspace|parbox|'
                 r'savebox|tabcolsep|columnwidth|textwidth)'
                 r'(\[[^\]]*\])*(\{[^{}]*\})*', ' ', tex)
    # LaTeX length and option syntax left over
    tex = re.sub(r'\[[^\]\n]{0,40}\]', ' ', tex)
    return tex


# 1{,}655 is how the manuscript writes a thousands separator.
TOKEN = re.compile(r'(?<![\w.\\])(\d{1,3}(?:\{,\}\d{3})+|\d+)(?![\w.])')


def scan():
    tex = open(TEX, errors='ignore').read()
    body = prose(tex)
    hits = {}
    for m in TOKEN.finditer(body):
        raw = m.group(1)
        val = raw.replace('{,}', '')
        ctx = re.sub(r'\s+', ' ', body[max(0, m.start() - 55):m.end() + 55]).strip()
        hits.setdefault(val, []).append(ctx)
    return hits


def main():
    hits = scan()
    if '--write' in sys.argv:
        old = json.load(open(REG)) if os.path.exists(REG) else {}
        reg = {}
        for v in sorted(hits, key=lambda x: int(x)):
            reg[v] = old.get(v, {'literal': 'UNCLASSIFIED -- classify me',
                                 'context': hits[v][0]})
        json.dump(reg, open(REG, 'w'), indent=1, sort_keys=False)
        print('intsweep: wrote %d entries to %s' % (len(reg), os.path.basename(REG)))
        return 0

    if not os.path.exists(REG):
        print('intsweep: %s missing; run with --write and classify the entries'
              % os.path.basename(REG))
        return 1
    reg = json.load(open(REG))
    MAC = macros()
    bad = []
    for v in sorted(hits, key=lambda x: int(x)):
        e = reg.get(v)
        if e is None:
            bad.append(('UNREGISTERED', v, hits[v][0]))
            continue
        if 'macro' in e:
            got = MAC.get(e['macro'])
            if got is None:
                bad.append(('MACRO MISSING', v,
                            '%s is not defined by any generator' % e['macro']))
            elif got.replace('{,}', '').replace(',', '') != v:
                bad.append(('MACRO MOVED', v,
                            r'\%s is now %s; the prose still says %s'
                            % (e['macro'], got, v)))
        elif 'literal' in e:
            if str(e['literal']).startswith('UNCLASSIFIED'):
                bad.append(('UNCLASSIFIED', v, hits[v][0]))
        else:
            bad.append(('MALFORMED', v, json.dumps(e)))

    stale = [v for v in reg if v not in hits]
    print('intsweep: %d distinct integers in running prose, %d registered, '
          '%d stale registry entries' % (len(hits), len(reg), len(stale)))
    for kind, v, ctx in bad:
        print('  %-14s %-8s %s' % (kind, v, ctx[:110]))
    if bad:
        print('intsweep: %d problem(s)' % len(bad))
        return 1
    print('intsweep: 0 problems')
    return 0


if __name__ == '__main__':
    sys.exit(main())
