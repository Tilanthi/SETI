#!/usr/bin/env python3
r"""GATE: no macro whose value is a lower-case English word or clause may open
a sentence, anywhere in the manuscript.

WHY THIS EXISTS -- THE DEFECT CLASS, AND WHY NO OTHER GATE HERE CAN SEE IT.
A generated English word is lower case by construction: it is written to sit in
the middle of a sentence.  Put one at the start of a sentence and the page
reads

    "... and 34 do not. three of the unattributed coincide with sulphur
     monoxide ..."

-- the right value, the right macro, a sentence that parses, and a missing
capital.  Every gate in this build compares a macro with its source or with
another macro; all of them pass, because nothing about the VALUE is wrong.
`pdflatex` cannot see it either: a lower-case letter after a full stop is
perfectly legal TeX.  It is a defect that exists only on the typeset page, and
it reached the page twice in one round (`\MkNSODecideWord` in conclusion 4,
`\PrFlagXrossWord` in the abstract).

`prose_v412.py`'s `P8c` catches it in the four front-matter files, which is
where it was found.  This gate is the same rule over the WHOLE manuscript,
because the defect does not know about ownership: the two instances were in two
different agents' files, and the macro that caused the first is emitted by a
third.  ★ And `P8c`'s own first two versions were each half-blind, so this one
asserts its coverage rather than claiming it.

WHAT IT CHECKS
  W1  no lower-case-valued macro is the first token of a sentence in any
      `\input` source of the manuscript;
  W2  the sweep is not vacuous: it found lower-case-valued macros in the macro
      layer at all, it found them CITED in the prose, and every cited one was
      searched for -- the failure mode of the check it generalises;
  W3  every source file the manuscript `\input`s was actually read, so a new
      section cannot be silently outside the sweep.

HOW A SENTENCE START IS RECOGNISED.  After `.`, `!` or `?` and whitespace;
at the start of a paragraph; after `\item`; after `\noindent`.  Opening braces
and `\emph{` are stepped over, because `\emph{\Word{} ...}` opens a sentence
just as plainly as `\Word` does.  `%`-comments are stripped first: a defect
inside a comment is not on the page, and counting one is how a gate cries wolf
until it is switched off.

    python3 wordcase.py              # the gate
    python3 wordcase.py --selftest   # prove each clause can fail AND pass
"""
import os
import re
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))

#: DERIVED, NEVER TYPED -- see the identical note in `citegate.py`.  In v4.15
#: this line still read `technosignatures_40pc_v4.14.tex`, a file that does not
#: exist here, so the gate swept 0 of the 27 prose sources and 0 of the 134
#: macro-layer files and W1 passed on an empty comparison.  Two gates were
#: blind for one typed filename.
MAIN = manuscript.main_file()

DEF = re.compile(r'\\newcommand\s*\{\\([A-Za-z]+)\}\s*\{(.*)\}\s*$')
INPUT = re.compile(r'\\(?:input|include)\s*\{([^}]*)\}')

#: files that define the macro layer rather than typeset prose
LAYER = re.compile(r'(?:^|/)(survey_numbers|regen_count)[A-Za-z0-9_]*\.tex$')

#: stepped backwards over, between the macro and the sentence boundary that
#: precedes it: an opening group, an emphasis command, a tie, white space.
#: `\emph{\Word{} ...}` opens a sentence just as plainly as `\Word` does.
_SKIP_BACK = ('{', '~', '\\emph{', '\\textit{', '\\textbf{', '\\noindent')

#: a command that itself begins a sentence
_OPENER = ('\\item', '\\noindent')


def strip_comments(src):
    out = []
    for line in src.split('\n'):
        cut, esc = None, False
        for j, ch in enumerate(line):
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '%':
                cut = j
                break
        out.append(line if cut is None else line[:cut])
    return '\n'.join(out)


def _resolve(rel):
    for cand in (rel, rel + '.tex'):
        path = os.path.join(HERE, cand)
        if os.path.isfile(path):
            return cand, path
    return None, None


def sources(main=MAIN):
    """Every file the manuscript `\\input`s, transitively, split into the prose
    sources this gate sweeps and the macro-layer files it reads values from."""
    seen, prose, layer = set(), [], []
    todo = [main]
    while todo:
        cand, path = _resolve(todo.pop(0))
        if path is None or path in seen:
            continue
        seen.add(path)
        src = strip_comments(open(path, encoding='utf-8').read())
        (layer if LAYER.search(cand) else prose).append((cand, src))
        todo += INPUT.findall(src)
    return prose, layer


def lower_valued(layer):
    """Macros whose expansion begins with a lower-case letter, i.e. whose value
    is an English word or clause and not a number, a name or a unit."""
    vals = {}
    for _name, src in layer:
        for line in src.split('\n'):
            m = DEF.match(line.strip())
            if not m:
                continue
            val = m.group(2).strip()
            #: step over leading groups to find the first thing a reader sees.
            #: ★ The first version of this loop tested `val[:1] in '{\\'`, and
            #: the empty string is a substring of every string, so a macro
            #: whose value is empty spun for ever -- the gate did not fail, it
            #: never finished, which is the same thing.
            while val.startswith('{'):
                val = val[1:].strip()
            if val[:1].isalpha() and val[:1].islower():
                vals[m.group(1)] = val
    return vals


def sentence_initial(src, pos, window=160):
    """True when `src[pos:]` -- a macro call -- is the first token of a
    sentence.  Walked BACKWARDS over a BOUNDED window in a single pass.  ★ Two
    earlier versions of this function were correct and unusable: one expressed
    the rule forwards as a regex over nine hundred alternatives and backtracked
    for minutes, and one re-searched `src[:i]` from the start of the file at
    every candidate, which is quadratic.  A check that cannot finish is a check
    that gets switched off, which is the same thing as a check that cannot
    fail."""
    pre = src[max(0, pos - window):pos]
    at_file_start = pos - window < 0
    i = len(pre)
    while i > 0:
        j = i
        while j > 0 and (pre[j - 1].isspace() or pre[j - 1] == '~'):
            j -= 1
        if j > 0 and pre[j - 1] == '{':
            #: an opening group, possibly belonging to \emph / \textbf / ...
            m = re.search(r'\\[A-Za-z]+\{$', pre[:j])
            j = m.start() if m else j - 1
        if j == i:
            break
        i = j
    if i == 0:
        #: nothing but skippable material back to the window edge; only a
        #: sentence start if that edge is the start of the file
        return at_file_start
    tail = pre[:i]
    #: a blank line before it: the macro opens a paragraph
    if re.search(r'\n[ \t]*\n[ \t]*$', tail):
        return True
    if re.search(r'\\(?:item|noindent)[ \t]*$', tail):
        return True
    return tail[-1] in '.!?'


def run(prose, layer, verbose=True):
    words = lower_valued(layer)
    cited = {}
    for name, src in prose:
        for nm in re.findall(r'\\([A-Za-z]+)', src):
            if nm in words:
                cited.setdefault(nm, set()).add(name)
    opens = []
    for name, src in prose:
        for m in re.finditer(r'\\([A-Za-z]+)', src):
            nm = m.group(1)
            if nm not in words:
                continue
            if sentence_initial(src, m.start()):
                opens.append((name, nm, words[nm],
                              src[m.start():m.end() + 18]
                              .replace('\n', ' ').strip()))
    fail = []

    def ck(key, ok, detail):
        if verbose:
            print('  %-3s %-60s %s  %s'
                  % (key, _WHAT[key], 'PASS' if ok else 'FAIL', detail))
        if not ok:
            fail.append(key)

    ck('W1', not opens,
       'none' if not opens else '; '.join(
           '%s opens a sentence with \\%s = "%s" (%s)' % (f, n, v, x)
           for f, n, v, x in opens))
    #: the coverage clause.  `P8c` lost its own four word macros once by
    #: reading the wrong source for the value, so this asserts that the sweep
    #: saw lower-case macros at all, saw them used, and searched for every one
    #: it saw used.
    searched = set(words)
    ck('W2', len(words) >= 8 and len(cited) >= 4
       and set(cited) <= searched,
       '%d lower-case-valued macros in the layer, %d of them cited; not '
       'searched: %s' % (len(words), len(cited),
                         sorted(set(cited) - searched) or 'none'))
    ck('W3', len(prose) >= 20 and any(n.endswith('abstract.tex')
                                      for n, _ in prose),
       '%d prose sources swept, %d macro-layer files read'
       % (len(prose), len(layer)))
    return fail, words, cited, opens


_WHAT = {
    'W1': 'no lower-case macro value opens a sentence',
    'W2': 'the sweep found, and searched for, every such macro',
    'W3': 'every prose source the manuscript inputs was read',
}


def selftest():
    prose, layer = sources()
    base, words, cited, _ = run(prose, layer, verbose=False)
    print('selftest: unperturbed ->', base or 'all clauses pass')
    ok = not base
    victim = sorted(cited)[0] if cited else sorted(words)[0]

    #: W1, driven once per prose file that cites a lower-case macro, so the
    #: coverage of the sweep is demonstrated and not asserted only.
    hits = 0
    for tgt, _ in prose:
        mod = [(n, s + ('\n\nA sentence. \\%s{} follows it.\n' % victim))
               if n == tgt else (n, s) for n, s in prose]
        got, _, _, op = run(mod, layer, verbose=False)
        if got == ['W1'] and any(f == tgt for f, _, _, _ in op):
            hits += 1
    print('  drive W1: injected into each of %d prose sources, fired in %d'
          % (len(prose), hits))
    ok = ok and hits == len(prose)

    #: the real sentence that reached the page last round.  ★ Written as a
    #: regex over the whitespace, because the first version of this drive
    #: matched a literal space where the file has a line break and so drove
    #: nothing at all -- the shape four drives in `prose_v412.py` had to be
    #: rescued from this round.  The substitution count is asserted.
    #: ★ Repointed at round 14: conclusion 4 was rewritten and the round-13
    #: sentence this drove no longer exists, so the drive raised its own
    #: substitution assertion rather than firing.  The clause it demonstrates
    #: is the same one -- a lower-case word macro pushed to the head of a
    #: sentence -- on the sentence as it now stands.
    _HIST = re.compile(r'no judgement\. Of those,\s+\\MkNSODecideWord\{\}')
    mod, nsub = [], 0
    for n, src in prose:
        if n.endswith('07_conclusions.tex'):
            src, k = _HIST.subn(
                r'no judgement. \\MkNSODecideWord{} of them are with', src)
            nsub += k
        mod.append((n, src))
    assert nsub == 1, ('drive W1-historic substituted %d times, not 1; the '
                       'sentence it drives has been reworded' % nsub)
    got, _, _, _ = run(mod, layer, verbose=False)
    hist = got == ['W1']
    print('  drive W1-historic: the round-13 conclusion-4 defect  %s'
          % ('fires' if hist else 'DOES NOT FIRE'))

    #: W2: the macro layer goes away, so there is nothing to search for
    got, _, _, _ = run(prose, [], verbose=False)
    w2 = 'W2' in got
    print('  drive W2: empty macro layer -> %s' % (got or 'nothing'))

    #: W3: the sweep loses the front matter
    got, _, _, _ = run([(n, s) for n, s in prose
                        if not n.endswith('abstract.tex')],
                       layer, verbose=False)
    w3 = got == ['W3']
    print('  drive W3: front matter dropped from the sweep -> %s'
          % (got or 'nothing'))

    #: a commented-out instance must NOT fire
    mod = [(n, s + '\n\n%% A sentence. \\%s{} follows.\n' % victim)
           if n.endswith('abstract.tex') else (n, s) for n, s in prose]
    mod = [(n, strip_comments(s)) for n, s in mod]
    got, _, _, _ = run(mod, layer, verbose=False)
    comm = not got
    print('  drive comment: a commented instance is not on the page  %s'
          % ('OK' if comm else 'WRONG'))
    return 0 if ok and hist and w2 and w3 and comm else 1


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        raise SystemExit(selftest())
    prose, layer = sources()
    print('wordcase: %d prose sources, %d macro-layer files'
          % (len(prose), len(layer)))
    fail, words, cited, _ = run(prose, layer)
    print('wordcase: %d lower-case-valued macros, %d cited, %d FAIL'
          % (len(words), len(cited), len(fail)))
    raise SystemExit(1 if fail else 0)
