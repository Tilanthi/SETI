#!/usr/bin/env python3
"""Gate: no two generators may write the same survey_numbers_roundNN.tex,
and every such file the manuscript \\inputs must have exactly one writer.

Written after an occurrence-rate generator added in the v3.99 cycle
silently overwrote survey_numbers_round47.tex, which stageonenull_v399.py
owns. The build did not complain, because the macros it destroyed were
still in the .aux from the previous run. Nothing in gate.sh could see it.
The only defence is to check the writers, so this does.

Exit status 1 on any collision, missing writer, or orphan file.

★ v4.11: THE PATTERN HAD A BLIND SPOT THAT COST TWO COLLISIONS IN ONE DAY.
Every clause below matches the filename as a LITERAL, so a generator that
builds its own output name --

    OUT = 'survey_numbers_round%s.tex' % ROUND        # or f-string, or
    OUT = 'survey_numbers_round{}.tex'.format(ROUND)  # .format()

-- is invisible to it.  Three agents in round 10 claimed round 106 between
them and this gate said nothing; the only thing standing between the paper
and a quietly overwritten number was a hand-written allocation table, and
that table was written after three of them had already started.  So the
templates are now RESOLVED, with `ast`, against module-level integer
constants, comprehension ranges and loop variables -- and a template in a
write context that cannot be resolved is itself reported and FAILS, because
an unresolvable claim on an unknown round is the same hazard wearing a hat.
"""
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAT = re.compile(r'survey_numbers_round(\d+)\.tex')
# Two template shapes, and the difference matters.  `round%s.tex` hides the
# round number in the operand and must be resolved; `round103%s.tex` names
# the round and hides only the D36 drive suffix, so the round is already
# known and the operand is irrelevant.  Treating the second as unresolvable
# would fail the build on every generator that obeys D36.
TEMPLATE = re.compile(r'survey_numbers_round(\d*)(%[sd]|\{[^}]*\})\.tex')

# ---------------------------------------------------------------------------
# Resolving a format-built output name.
#
# The resolver is deliberately narrow: it answers "which round file can this
# expression name?" for the three shapes a generator in this tree actually
# uses, and says UNRESOLVED for anything else rather than guessing.  A
# guess here would invent a collision, and a gate that cries wolf gets
# switched off, which is how we got here.
_WRITE = re.compile(r"""['"]w['"]|\.write|splitext\(""")
_OUTVAR = re.compile(r'\s*(OUT|OUTNAME|OUTFILE|OUTPATH|TEX|TEXOUT|DEST)\s*=')


def _int_env(tree):
    """Module-level NAME = <int literal> bindings, which is how every
    generator in this tree declares its round number."""
    env = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value,
                                                       ast.Constant):
            if isinstance(node.value.value, (int, str)):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        env[t.id] = node.value.value
    return env


def _range_values(node):
    """range(a, b) / range(b) with literal bounds -> the integers."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == 'range'):
        return None
    args = []
    for a in node.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, int):
            args.append(a.value)
        else:
            return None
    if len(args) == 1:
        return list(range(args[0]))
    if len(args) == 2:
        return list(range(*args))
    if len(args) == 3:
        return list(range(*args))
    return None


def _resolve_operand(node, env):
    """The set of integer values an expression can take, or None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, str)):
        return {node.value}
    if isinstance(node, ast.Name) and node.id in env:
        return {env[node.id]}
    if isinstance(node, ast.Tuple) and len(node.elts) == 1:
        return _resolve_operand(node.elts[0], env)
    return None


def _template_names(src, fn):
    """(resolved names in write context, unresolved write-context sites).

    Walks the syntax tree rather than the text, so the operand of a `%` or
    a `.format()` or an f-string is reached as an expression and not as a
    run of characters.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set(), []
    srclines = src.split('\n')
    env = _int_env(tree)
    # comprehension and for-loop variables bound to a literal range
    loop_env = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
            vals = _range_values(node.iter)
            if vals is not None:
                loop_env.setdefault(node.target.id, set()).update(vals)
        for comp in getattr(node, 'generators', []) or []:
            if isinstance(comp.target, ast.Name):
                vals = _range_values(comp.iter)
                if vals is None and isinstance(comp.iter, ast.Call) \
                        and isinstance(comp.iter.func, ast.Name) \
                        and comp.iter.func.id in ('list', 'sorted') \
                        and comp.iter.args:
                    vals = _range_values(comp.iter.args[0])
                if vals is not None:
                    loop_env.setdefault(comp.target.id, set()).update(vals)
    full = dict(env)

    def operand(node):
        got = _resolve_operand(node, full)
        if got is not None:
            return got
        if isinstance(node, ast.Name) and node.id in loop_env:
            return set(loop_env[node.id])
        return None

    resolved, unresolved = set(), []
    for node in ast.walk(tree):
        tmpl, oper = None, None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) \
                and isinstance(node.left, ast.Constant) \
                and isinstance(node.left.value, str) \
                and TEMPLATE.search(node.left.value):
            tmpl, oper = node.left.value, node.right
        elif isinstance(node, ast.Call) \
                and isinstance(node.func, ast.Attribute) \
                and node.func.attr == 'format' \
                and isinstance(node.func.value, ast.Constant) \
                and isinstance(node.func.value.value, str) \
                and TEMPLATE.search(node.func.value.value) \
                and len(node.args) == 1:
            tmpl, oper = node.func.value.value, node.args[0]
        elif isinstance(node, ast.JoinedStr):
            parts, fvs = [], []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(str(v.value))
                else:
                    parts.append('\0')
                    fvs.append(v.value)
            joined = ''.join(parts)
            if 'survey_numbers_round\0.tex' in joined and len(fvs) == 1:
                tmpl, oper = 'survey_numbers_round%s.tex', fvs[0]
        if tmpl is None:
            continue
        # `round103%s.tex`: the round is in the template, the operand is the
        # drive suffix.  Resolve from the template and never look at the
        # operand, or every D36-compliant generator becomes "unresolvable".
        _m = TEMPLATE.search(tmpl)
        if _m and _m.group(1):
            lo = getattr(node, 'lineno', 1) - 1
            hi = getattr(node, 'end_lineno', lo + 1)
            stmt = '\n'.join(srclines[max(0, lo - 1):hi + 1])
            if _WRITE.search(stmt) or (lo < len(srclines)
                                       and _OUTVAR.match(srclines[lo])):
                resolved.add('survey_numbers_round%s.tex' % _m.group(1))
            continue
        # The enclosing statement's own text decides write vs read, exactly
        # as the literal scan does, so the two halves of this gate cannot
        # disagree about what a write is.
        lo = getattr(node, 'lineno', 1) - 1
        hi = getattr(node, 'end_lineno', lo + 1)
        stmt = '\n'.join(srclines[max(0, lo - 1):hi + 1])
        is_write = bool(_WRITE.search(stmt)) or bool(
            _OUTVAR.match(srclines[lo]) if lo < len(srclines) else None)
        if not is_write:
            continue
        vals = operand(oper)
        if vals is None:
            unresolved.append((fn, lo + 1, srclines[lo].strip()[:90]))
            continue
        for v in vals:
            resolved.add('survey_numbers_round%s.tex' % v)
    return resolved, unresolved


writers = {}
template_sites = {}
unresolved_sites = []
for fn in sorted(os.listdir(HERE)):
    if not fn.endswith('.py') or fn == os.path.basename(__file__):
        continue
    src = open(os.path.join(HERE, fn), errors='ignore').read()
    if TEMPLATE.search(src):
        got, un = _template_names(src, fn)
        unresolved_sites += un
        for name in got:
            writers.setdefault(name, set()).add(fn)
            template_sites.setdefault(name, set()).add(fn)
    # A generator "writes" a round file if it names it in a write context.
    for mm in PAT.finditer(src):
        name = mm.group(0)
        # A generator is a WRITER of a round file if the filename appears
        # either next to an explicit write, or as the value of an OUT-style
        # variable that is later written. A generator that only READS a
        # round file -- viscal_v399.py reads round38 to recombine the
        # budget -- must not be counted, so read contexts are excluded.
        line_start = src.rfind('\n', 0, mm.start()) + 1
        line_end = src.find('\n', mm.end())
        line = src[line_start:line_end if line_end > 0 else len(src)]
        near = src[max(0, mm.start() - 80):mm.end() + 80]
        is_read = ('.read()' in line or 'open(p).read' in near
                   or re.search(r'def\s+\w+\([^)]*%s' % re.escape(name),
                                src) is not None)
        # v4.06: TEX/TEXOUT added.  A gate that recognises only three
        # variable names can be defeated by choosing a fourth, which is
        # what happened: p90r7_v406.py assigned its round file to `TEX`
        # and this gate reported NO WRITER for a file a generator plainly
        # writes.  The generator was renamed to house style AND the
        # pattern widened, because the next one will pick another name.
        assigns_out = re.match(
            r'\s*(OUT|OUTNAME|OUTFILE|OUTPATH|TEX|TEXOUT|DEST)\s*=',
            line) is not None
        # v4.09: AND the pattern was defeated a second time, exactly as the
        # note above predicted it would be.  Two generators in this cycle
        # suffix every output under `--drive N` -- D36's rule that a test may
        # not write where production reads -- so the round file reaches
        # `os.path.splitext(...)` rather than an `open(..., 'w')`.  Recognise
        # that shape too, instead of waiting for a third variable name.
        assigns_out = assigns_out or 'splitext(' in line
        writes_here = ("'w'" in line or '"w"' in line or '.write' in line)
        if (writes_here or assigns_out) and not is_read:
            writers.setdefault(name, set()).add(fn)

# ★ DEFEATED A THIRD TIME, by a third variable name (`OUTNAME`, holding the
# basename so a drive suffix can be applied before the path is joined).  The
# name list is widened again, but widening it is plainly not the fix -- the
# note above predicted a third name and here it is.  So the writer is now
# also taken from the ROUND FILE'S OWN HEADER, which every generator in this
# tree writes and which no choice of variable name can hide.  The header is
# consulted only where the source scan found NO writer, so it can close a
# false "NO WRITER" without ever inventing a collision.
#
# ★ v4.11: AND THAT LAST SENTENCE WAS THE HOLE.  Suppressing the header
# wherever a writer was already found means a SECOND claimant hides the
# declared owner: a fake generator claiming round 103 made itself the sole
# writer of a file whose own header says `numbers_v410.py`, and the gate
# reported no collision.  The header is now always consulted.  It cannot
# invent a collision between a generator and itself -- `writers` is a set --
# so the only thing it can now add is a disagreement between the file's own
# declared owner and whoever the source scan caught writing it, which is
# precisely the thing worth stopping the build for.
HDR = re.compile(r'generated by ([A-Za-z0-9_]+\.py)', re.I)
for fn in sorted(os.listdir(HERE)):
    if not PAT.fullmatch(fn):
        continue
    with open(os.path.join(HERE, fn), errors='ignore') as fh:
        head = ''.join(fh.readline() for _ in range(3))
    mh = HDR.search(head)
    if mh and os.path.exists(os.path.join(HERE, mh.group(1))):
        # Normalise: the declared owner and the same name found by the
        # source scan are ONE writer, or every generator would collide with
        # itself.  Only a DIFFERENT name is added, and that is a real
        # disagreement.
        if mh.group(1) not in writers.get(fn, set()):
            writers.setdefault(fn, set()).add(mh.group(1) + ' (self-declared)')

# Rounds whose generator has been retired are shipped as frozen copies and
# restored by make_all.sh; those have a legitimate single "writer".
FROZEN = os.path.join(HERE, 'frozen_macros')
if os.path.isdir(FROZEN):
    for fn in sorted(os.listdir(FROZEN)):
        if PAT.fullmatch(fn):
            writers.setdefault(fn, set()).add('frozen_macros/ (retired)')

import manuscript  # v4.10: split manuscript
# v4.10: the manuscript is split into sections/, so this must read the
# FLATTENED document.  Reading the main file alone leaves this check
# looking at a preamble, where it can only be vacuous or wrong.
inputs = set()
for mm in re.finditer(r'\\input\{(survey_numbers_round\d+)\}', manuscript.flat()):
    inputs.add(mm.group(1) + '.tex')

fail = 0
if template_sites:
    print('resolved format-built output names (v4.11): %s'
          % '; '.join('%s <- %s' % (n, ', '.join(sorted(w)))
                      for n, w in sorted(template_sites.items())))
for fn, ln, text in unresolved_sites:
    # An output name this gate cannot resolve is not a pass.  It is the
    # blind spot that let three generators claim one round, restated.
    print('FAIL UNRESOLVED TEMPLATE %s:%d builds a round filename this gate '
          'cannot resolve: %s' % (fn, ln, text))
    fail += 1

# ★ A double claim is a FAILURE, not a note.  It used to print beside the
# orphan and missing lines in the same voice, and the whole suite returned
# zero anyway; a second writer destroys a number silently, which is strictly
# worse than a build that stops.
for name in sorted(writers, key=lambda n: int(PAT.match(n).group(1))):
    who = sorted(writers[name])
    if len(who) > 1:
        print('FAIL COLLISION %s is claimed by %d generators: %s -- the one '
              'that runs second overwrites the other\'s macros and nothing '
              'else in the build can see it'
              % (name, len(who), ', '.join(who)))
        fail += 1

for name in sorted(inputs, key=lambda n: int(PAT.match(n).group(1))):
    if name not in writers:
        print('NO WRITER %s is \\input by the manuscript but no generator '
              'writes it' % name)
        fail += 1
    if not os.path.exists(os.path.join(HERE, name)):
        print('MISSING   %s is \\input by the manuscript and does not exist'
              % name)
        fail += 1

for name in sorted(writers, key=lambda n: int(PAT.match(n).group(1))):
    if name not in inputs:
        print('ORPHAN    %s is generated but never \\input' % name)
        fail += 1

print('roundcollide: %d round files, %d inputs, %d problems'
      % (len(writers), len(inputs), fail))
# v4.06: raise rather than sys.exit, so selftest_v406.py can drive this gate's
# own detection logic in both directions.  A gate whose failure mode cannot be
# distinguished from a crash is hard to test.
assert not fail, 'roundcollide: %d problem(s)' % fail
