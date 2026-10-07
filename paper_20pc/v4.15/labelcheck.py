#!/usr/bin/env python3
r"""labelcheck -- the reference layer of the manuscript, checked at source
and again against the build.

Why this exists.  A LaTeX float takes its number from the counter stepped by
its \caption, and a \label simply records whatever \@currentlabel holds.  Two
\labels inside one float therefore both record the SAME number: they are not
two reference targets, they are one target with two names, and every \ref to
the second one silently prints the first one's number.  Nothing in a normal
build says so -- there is no warning, no "multiply defined", and the PDF looks
perfectly well formed.

The same mechanism has three further forms, and all four are checked here:

  F1  two or more \labels inside one float or one numbered maths environment;
  F2  one label name defined twice (different places, same name);
  F3  a \ref whose target is never defined -- which prints "??";
  F4  a \label defined and never referenced -- a float that is typeset,
      numbered and paid for in pages but that no sentence points at;
  F5  a label whose prefix disagrees with the object it sits on, e.g. a
      `tab:` name anchored on a figure;
  F6  a \label attached to a STARRED sectioning command, which steps no
      counter, so the \ref prints the number of the enclosing numbered unit
      and a reader following it lands somewhere else entirely;
  F7  (build mode) two \newlabel entries in the .aux sharing one anchor.
      F1 and F2 find this at source; F7 finds it across file boundaries and
      is the ground truth, because it reads what LaTeX actually wrote.

F7 is deliberately parsed with a brace-counting reader rather than a regular
expression.  A regular expression over `\newlabel{..}{{..}{..}{..}{..}{}}`
breaks on any caption containing braces -- `\emph{...}` is enough -- and the
rows it breaks on are skipped in silence.  Skipping a row makes a duplicate
anchor invisible, so the shape of the bug determines which instances the
checker can see, and the ones it cannot see are exactly the ones in long,
formatted captions.  Brace counting has no such blind spot.

Usage
    python3 labelcheck.py [master.tex] [--aux FILE] [--drive N] [--quiet]

Exit status 0 if every check passes, 1 otherwise.

Driving.  Every check is exercised in BOTH directions: `--drive 0` runs the
real tree unperturbed and the checks must pass; `--drive 1..7` injects one
defect of the corresponding class into an IN-MEMORY copy and the matching
check must fire.  `--drive N` never writes anything a production path reads:
the perturbation lives in memory, and any report it emits is suffixed
`_driveN`.  The suffix follows the FLAG, not the perturbation, so `--drive 0`
is also barred from writing a production path.
"""
import os
import re
import sys

FLOATS = {'table', 'table*', 'figure', 'figure*', 'algorithm', 'algorithm*',
          'sidewaystable', 'sidewaysfigure', 'subfigure', 'subtable',
          'wrapfigure', 'wraptable', 'longtable'}
MATHENV = {'equation', 'align', 'gather', 'multline', 'eqnarray', 'flalign',
           'alignat'}
# Prefix -> the anchor kinds a label of that prefix may legally sit on.
PREFIX = {'tab': {'table', 'longtable'}, 'fig': {'figure'},
          'eq': {'equation'}, 'sec': {'section'}, 'app': {'section'},
          'page': {'section', 'table', 'figure', 'equation', 'none'}}
REFCMD = r'\\(?:auto|c|C|name|page|eq|v|V)?ref\*?\{([^}]*)\}'


# --------------------------------------------------------------- reading
def strip_comments(s):
    """Remove TeX comments without eating \\% or the newline-joining rule."""
    out = []
    for line in s.split('\n'):
        i, n = 0, len(line)
        while i < n:
            if line[i] == '\\':
                i += 2
                continue
            if line[i] == '%':
                line = line[:i]
                break
            i += 1
        out.append(line)
    return '\n'.join(out)


def read_tree(master, _seen=None, _root=None):
    """Return [(path, text)] for the master and every file it \\inputs.

    ★ `\\input` is resolved relative to the WORKING DIRECTORY -- in practice
    the master's directory -- and NOT relative to the including file.  This
    read it relative to the including file, so every `\\input{tab_maskband}`
    inside `sections/app_*.tex` was looked for at `sections/tab_maskband.tex`,
    which does not exist, and the fragment was silently never read.  The cost
    was three FAILs on labels that resolve perfectly in the build -- two F3
    for `tab:maskband` and `tab:selfunc`, one F4 for `sec:linecost` -- i.e.
    a gate crying wolf, which trains its reader to ignore the real ones.
    Root first, then the including file's directory as a fallback, because
    TeX's own search path does include the latter under some engines.
    """
    _seen = _seen if _seen is not None else set()
    master = os.path.abspath(master)
    if master in _seen or not os.path.exists(master):
        return []
    _seen.add(master)
    root = _root if _root is not None else os.path.dirname(master)
    base = os.path.dirname(master)
    txt = strip_comments(open(master, errors='ignore').read())
    out = [(master, txt)]
    for m in re.finditer(r'\\(?:input|include)\s*\{([^}]+)\}', txt):
        child = m.group(1).strip()
        if not child.endswith('.tex'):
            child += '.tex'
        for cand in (os.path.join(root, child), os.path.join(base, child)):
            if os.path.exists(cand):
                out += read_tree(cand, _seen, root)
                break
    return out


# --------------------------------------------------------------- scanning
def scan(files):
    """Walk every file and attach each \\label to the object enclosing it.

    Returns (labels, refs, floats) where
      labels : [(name, path, line, kind, container_id, starred_section)]
      refs   : {name: [(path, line)]}
      floats : {container_id: (kind, path, line)}
    """
    labels, refs, floats = [], {}, {}
    for path, txt in files:
        stack = []                     # open environments, innermost last
        secno = [0]                    # a counter so containers are unique
        last_sec_starred = [False]
        pos, line = 0, 1
        tok = re.compile(r'\\begin\s*\{([^}]*)\}|\\end\s*\{([^}]*)\}'
                         r'|\\label\s*\{([^}]*)\}'
                         r'|\\(section|subsection|subsubsection|paragraph'
                         r'|subparagraph|chapter|part)(\*?)'
                         r'|' + REFCMD)
        for m in tok.finditer(txt):
            line += txt.count('\n', pos, m.start())
            pos = m.start()
            beg, end, lab, seccmd, star, ref = m.groups()
            if beg is not None:
                stack.append((beg, line))
                if beg in FLOATS or beg in MATHENV:
                    secno[0] += 1
                    cid = '%s#%d' % (os.path.basename(path), secno[0])
                    floats[cid] = (beg, path, line)
                    stack[-1] = (beg, line, cid)
            elif end is not None:
                while stack and stack[-1][0] != end:
                    stack.pop()
                if stack:
                    stack.pop()
            elif seccmd is not None:
                secno[0] += 1
                last_sec_starred[0] = (star == '*')
                cid = 'sec:%s#%d' % (os.path.basename(path), secno[0])
                floats[cid] = ('section', path, line)
                # a sectioning command closes no environment; remember it as
                # the current non-float container
                stack.append(('@section', line, cid))
                while len(stack) > 1 and stack[-2][0] == '@section':
                    stack.pop(-2)
            elif lab is not None:
                cid, kind = None, 'none'
                for fr in reversed(stack):
                    if fr[0] in FLOATS or fr[0] in MATHENV:
                        cid, kind = fr[2], fr[0]
                        break
                    if fr[0] == '@section':
                        cid, kind = fr[2], 'section'
                        break
                labels.append((lab, path, line, kind.rstrip('*'), cid,
                               kind == 'section' and last_sec_starred[0]))
            elif ref is not None:
                refs.setdefault(ref, []).append((path, line))
    return labels, refs, floats


# --------------------------------------------------------------- aux side
def aux_newlabels(path):
    """Brace-counting reader for \\newlabel.  No regex, no blind spot."""
    if not path or not os.path.exists(path):
        return None
    s = open(path, errors='ignore').read()
    out, i = [], 0

    def grp(j):
        assert s[j] == '{'
        d = 0
        for k in range(j, len(s)):
            if s[k] == '{':
                d += 1
            elif s[k] == '}':
                d -= 1
                if d == 0:
                    return s[j + 1:k], k + 1
        raise ValueError('unbalanced braces in %s' % path)

    while True:
        i = s.find('\\newlabel{', i)
        if i < 0:
            return out
        name, j = grp(i + len('\\newlabel'))
        body, i = grp(j)
        fields, k = [], 0
        while k < len(body):
            if body[k] == '{':
                v, k = _grp(body, k)
                fields.append(v)
            else:
                k += 1
        if name.endswith('@cref'):
            continue
        out.append((name, fields))


def _grp(s, j):
    d = 0
    for k in range(j, len(s)):
        if s[k] == '{':
            d += 1
        elif s[k] == '}':
            d -= 1
            if d == 0:
                return s[j + 1:k], k + 1
    raise ValueError('unbalanced braces')


# --------------------------------------------------------------- checks
def run(master, auxpath, drive=0, quiet=False):
    files = read_tree(master)
    if not files:
        print('labelcheck: cannot read %s' % master)
        return 1
    # ---- in-memory perturbations.  Nothing is written anywhere.
    if drive:
        p, t = files[0]
        if drive == 1:                       # two labels in one float
            t = t.replace('\\end{document}', '', 1)
            t += ('\n\\begin{figure}\\caption{drive}\\label{fig:driveA}'
                  '\\label{fig:driveB}\\end{figure}\n'
                  '\\ref{fig:driveA}\\ref{fig:driveB}\n')
        elif drive == 2:                     # one name defined twice
            t += ('\n\\begin{figure}\\caption{d}\\label{fig:driveC}'
                  '\\end{figure}\n'
                  '\\begin{figure}\\caption{d}\\label{fig:driveC}'
                  '\\end{figure}\n\\ref{fig:driveC}\n')
        elif drive == 3:                     # a reference to nothing
            t += '\n\\ref{tab:driveNowhere}\n'
        elif drive == 4:                     # an orphan float
            t += ('\n\\begin{table}\\caption{d}\\label{tab:driveOrphan}'
                  '\\end{table}\n')
        elif drive == 5:                     # prefix disagrees with anchor
            t += ('\n\\begin{figure}\\caption{d}\\label{tab:driveWrong}'
                  '\\end{figure}\n\\ref{tab:driveWrong}\n')
        elif drive == 6:                     # label on a starred section
            t += '\n\\section*{drive}\\label{sec:driveStar}\n\\ref{sec:driveStar}\n'
        files = [(p, t)] + files[1:]

    labels, refs, floats = scan(files)
    aux = aux_newlabels(auxpath)
    if drive == 7 and aux is not None:
        _a = aux[0][1][3] if aux and len(aux[0][1]) > 3 else 'table.1'
        aux = list(aux) + [('tab:driveAlias', ['1', '1', 'd', _a, ''])]

    fail, notes = [], []

    def rel(p):
        return os.path.basename(p)

    # F1 -- two labels inside one float or numbered maths environment
    byc = {}
    for name, p, ln, kind, cid, _ in labels:
        if kind in {x.rstrip('*') for x in FLOATS | MATHENV}:
            byc.setdefault(cid, []).append((name, p, ln, kind))
    f1 = [(c, v) for c, v in byc.items() if len(v) > 1]
    for c, v in sorted(f1, key=lambda x: x[1][0][2]):
        fail.append('F1 one %s carries %d labels (%s:%d): %s'
                    % (v[0][3], len(v), rel(v[0][1]), v[0][2],
                       ', '.join(n for n, _, _, _ in v)))

    # F2 -- one name defined twice
    seen = {}
    for name, p, ln, kind, cid, _ in labels:
        seen.setdefault(name, []).append((p, ln))
    for name, where in sorted(seen.items()):
        if len(where) > 1:
            fail.append('F2 label %s defined %d times: %s'
                        % (name, len(where),
                           ', '.join('%s:%d' % (rel(p), l) for p, l in where)))

    # F3 -- a reference whose target is never defined
    for name in sorted(set(refs) - set(seen)):
        if name.startswith('page:') and aux is not None \
                and any(a[0] == name for a in aux):
            continue
        fail.append('F3 \\ref{%s} has no \\label anywhere (%s)'
                    % (name, ', '.join('%s:%d' % (rel(p), l)
                                       for p, l in refs[name][:3])))

    # F4 -- a label nothing references.
    # ★ F4 exists for a FLOAT that is typeset, numbered and paid for in pages
    # that no sentence points at, and for an appendix the body never cites.
    # Applied to ordinary `\\label{sec:...}` on a numbered section it fired 17
    # times on this manuscript for something no author should act on: giving
    # every section a label is normal practice and costs nothing.  Those 17
    # buried the two that were real -- an uncited appendix and an uncited
    # table.  So a sectioning label that is merely unreferenced is a NOTE;
    # a float, an equation or an appendix-level `\\section` label is a FAIL.
    _kindof = {}
    for _n, _p, _l, _k, _cid, _st in labels:
        _kindof.setdefault(_n, _k)
    _secnote = 0
    for name in sorted(set(seen) - set(refs)):
        p, ln = seen[name][0]
        kind = _kindof.get(name, 'none')
        is_app = name.startswith('app:')
        if kind == 'section' and not is_app:
            _secnote += 1
            continue
        fail.append('F4 \\label{%s} is never referenced (%s:%d)%s'
                    % (name, rel(p), ln,
                       ' -- an appendix the body never cites' if is_app
                       else ' -- a %s typeset and never cited' % kind))
    if _secnote:
        notes.append('F4 (not a failure) %d unreferenced sectioning label(s); '
                     'F4 fires only on floats, equations and appendices'
                     % _secnote)

    # F5 -- prefix disagrees with the object the label sits on
    for name, p, ln, kind, cid, _ in labels:
        pre = name.split(':')[0] if ':' in name else ''
        if pre in PREFIX and kind != 'none':
            k = 'equation' if kind in {x.rstrip('*') for x in MATHENV} \
                else kind
            if k not in PREFIX[pre]:
                fail.append('F5 \\label{%s} sits on a %s (%s:%d)'
                            % (name, k, rel(p), ln))

    # F6 -- a label on a starred sectioning command steps no counter
    for name, p, ln, kind, cid, starred in labels:
        if starred and name in refs:
            fail.append('F6 \\label{%s} is on a starred section, so \\ref '
                        'prints the enclosing unit\'s number (%s:%d)'
                        % (name, rel(p), ln))
        elif starred:
            notes.append('F6 (unreferenced) %s is on a starred section' % name)

    # F7 -- two .aux entries sharing one anchor
    if aux is None:
        notes.append('F7 skipped: no .aux (source-only run)')
    else:
        anch = {}
        for name, f in aux:
            if len(f) >= 4:
                anch.setdefault(f[3], []).append(name)
        for a, v in sorted(anch.items()):
            if len(v) > 1:
                fail.append('F7 anchor %s carries %d labels: %s'
                            % (a, len(v), ', '.join(sorted(v))))

    if not quiet:
        print('labelcheck: %d files, %d labels, %d distinct \\ref targets, '
              '%d floats/maths environments%s'
              % (len(files), len(labels), len(refs),
                 sum(1 for k in floats.values() if k[0] != 'section'),
                 '' if aux is None else ', %d aux entries' % len(aux)))
        for n in notes:
            print('  note: ' + n)
        for f in fail:
            print('  FAIL ' + f)
        print('labelcheck: %d FAIL' % len(fail))
    return 1 if fail else 0


def main(argv):
    # ★ 2026-10-07: EVERY ONE OF THIS GATE'S SEVEN DRIVES WAS DEAD, AND THE
    # GATE REPORTED EACH AS 0 FAIL.  The positional list was built as "every
    # argument that does not begin with --", which collects the VALUE of
    # `--drive N` as well: `labelcheck.py --drive 1` took "1" to be the master
    # .tex, printed `cannot read 1`, and returned 2 before a single clause ran.
    # A caller looking for failures saw none and concluded the drive had been
    # demonstrated.  This is the same shape as `make_fig_chain_v412.py`'s
    # `sys.argv[1]`, which created a directory called `--drive`: a flag's value
    # read as a positional.  The flags and their values are now consumed before
    # the positional list is formed.
    rest = list(argv[1:])
    drive = 0
    auxpath = None
    quiet = '--quiet' in rest
    while '--quiet' in rest:
        rest.remove('--quiet')
    for flag in ('--drive', '--aux'):
        while flag in rest:
            i = rest.index(flag)
            if i + 1 >= len(rest):
                print('labelcheck: %s needs a value' % flag)
                return 2
            val = rest[i + 1]
            if flag == '--drive':
                drive = int(val)
            else:
                auxpath = val
            del rest[i:i + 2]
    args = [a for a in rest if not a.startswith('--')]
    here = os.path.dirname(os.path.abspath(__file__))
    if args:
        master = args[0]
    else:
        cand = [f for f in sorted(os.listdir(here))
                if f.endswith('.tex')
                and '\\documentclass' in open(os.path.join(here, f),
                                              errors='ignore').read(4000)]
        if not cand:
            print('labelcheck: no master .tex given and none found')
            return 2
        master = os.path.join(here, sorted(cand)[-1])
    if auxpath is None:
        guess = master[:-4] + '.aux'
        auxpath = guess if os.path.exists(guess) else None
    return run(master, auxpath, drive, quiet)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
