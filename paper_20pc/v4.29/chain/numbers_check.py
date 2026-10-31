#!/usr/bin/env python3
r"""numbers_check.py -- (v4.29, Ruling R25) the GATE copy of referee_r28/tools/numbers_move.py.

    python3 numbers_check.py --check [--drive 1|2]     (gate: exit 0 only if "nothing to do")

Identical to numbers_move.py except: it never scans itself (its own source names the macro
layer by design), and --check turns the dry run into a verdict: a macro file at the build root,
an un-repointed reference, or an unclassifiable one fails the build.  --drive 1 adds a phantom
macro file at the root, --drive 2 a generator that writes a macro file the old way; both must fail.
The original documentation follows.

numbers_move.py -- move the macro layer `survey_numbers*.tex` from the build
root (`chain/`) into `chain/numbers/` and repoint every reference, by PATTERN.

    python3 -I -B numbers_move.py TREE [--dry-run] [--report FILE] [--verbose]

TREE is a version directory (re-rooted: TREE/chain is the build root) or a
flat build root.  r28-numbers, 2026-10-29.  Report: referee_r28/NUMBERS.md.

WHAT IT DOES
  1. Inventory: every file at the build root whose NAME matches MACRO_FILE is
     a macro file.  The set is derived, never listed, so it is whatever the
     tree holds when this runs (after the text phase and the re-flag fold).
  2. Classify every reference to `survey_numbers` in every live file:
       .py   AST + tokenizer (comments, docstrings, messages are inert; every
             code use is classified by its CONTEXT -- path, name, regex,
             enumeration -- see RULES below);
       .sh   shell lines (comments inert; file operands repointed);
       .tex  the manuscript's \input lines;
       other data/prose files are inert and reported.
     Enumerations of the build root that do not mention `survey_numbers`
     (`os.listdir(HERE)`, `glob('*.tex')`, ...) are classified too, by the
     predicate applied to what they return.
  3. REFUSES, writing nothing, if any reference or enumeration falls outside
     the rules (`UNCLASSIFIED`), listing each with file:line and context.
  4. Applies the edits, moves the files, then re-scans: the second scan must
     find nothing left to do (the idempotence and completeness check).
  Re-running on a moved tree is a no-op (exit 0, "nothing to do").

RULES (each a pattern over code; the report names the rule per edit)
  P1  a macro-file literal (`survey_numbers...`, template, or glob) used as a
      PATH -- 2nd+ argument of os.path.join, 1st of open/glob/exists/..., the
      right operand of `ROOT + '/survey_numbers...'`, or a variable/param
      whose every use is such a path -- gets `numbers/` prefixed.
  P2  a macro-file NAME (a variable holding a basename: a literal also used as
      a name, a loop variable over a filtered listing, an \input capture)
      keeps its value; each PATH use of it gets 'numbers' inserted
      (os.path.join(D, n) -> os.path.join(D, 'numbers', n); open(n) ->
      open(os.path.join('numbers', n))).
  E1  an enumeration of a directory whose consumer admits ONLY macro files
      (startswith('survey_numbers'...), a macro regex) is repointed to
      D/numbers.
  E2  a BROAD enumeration of the build root (`*.tex`, all files) that can
      reach macro files is widened to include D/numbers (paths, not names).
  T1  manuscript `\input{survey_numbers...}` -> `\input{numbers/survey_numbers...}`.
  T2  a TeX snippet in code (`'\\input{survey_numbers_round997}'`) is
      repointed the same way.
  R1  a regex over the manuscript `\\input\{(survey_numbers...` gets an
      optional `(?:numbers/)?` OUTSIDE the capture, so it still yields the
      basename.
  F1  a symlink farm over the build root gets a REAL numbers/ directory of
      per-file links (a link to the directory would write THROUGH it).
  F2  a scratch directory made to look like the build root (`figures/` made
      for it) gets `numbers/` made the same way; a macro file copied into a
      scratch root is copied into its numbers/.
  S1  shell: a macro-file operand of rm/cp/ls/test outside a comment.
  INERT  comments, docstrings, messages (text with spaces), product headers,
      name predicates, dict keys, data files.
"""
import ast
import io
import json
import os
import re
import sys
import tokenize

SUB = 'numbers'
#: this gate's own source names the macro layer by design; never scanned
SELF = {'numbers_check.py', 'numbers_move.py'}
MACRO_FILE = re.compile(r'^survey_numbers(?:_[A-Za-z0-9]+)?\.tex$')
DRIVE = re.compile(r'_drive')
#: directories whose code the chain never runs (each verified in NUMBERS.md
#: against the traced chain: no process executed a file in them).
DEAD_DIRS = {'retired', 'retired_generators', '.r12sens_backup', 'notes',
             'snapshots', '__pycache__', SUB}
DEPOSIT_DIRS = {'ALMA_Technosignatures_40pc'}
SN = 'survey_numbers'
#: names a macro-layer enumeration can meet: a macro file and a drive artefact
PROBES = ('survey_numbers_round8.tex', 'survey_numbers_round8_drive1.tex')
#: the shape of a macro-file literal used as a path or a name (no spaces)
SN_LIT = re.compile(r'^/?survey_numbers[A-Za-z0-9_%{}*?\[\]().-]*$')
SN_DONE = re.compile(r'(?:^|/)numbers/survey_numbers')

JOIN = {'os.path.join', 'join', 'osp.join', 'path.join', '_join',
        '_os.path.join', '_o.path.join', 'os_path.join', '_p.join', '_osp.join'}
PATH1 = {'open', 'io.open', 'codecs.open', 'os.path.exists', 'os.path.isfile',
         'os.path.getmtime', 'os.path.getsize', 'os.remove', 'os.unlink',
         'shutil.copy', 'shutil.copy2', 'shutil.copyfile', 'Path',
         'pathlib.Path', 'os.stat', 'os.path.lexists', '_b.open', '_ro'}
GLOBF = {'glob', 'iglob'}
REF = {'re.match', 're.fullmatch', 're.search', 're.findall', 're.finditer',
       're.compile', 're.sub', '_re.findall', '_re.match', '_re.compile',
       '_re.search', '_re.finditer', 're.split'}
TEXTF = {'print', 'sys.exit', 'SystemExit', 'AssertionError', 'RuntimeError',
         'ValueError', 'KeyError', 'Exception', 'check', 'fail', 'say', 'log',
         'note', 'warn', 'die', 'err', 'ok', 'chk', 'C', 'emit', 'report',
         'FAIL', 'PASS', 'e', 'w', 'add'}
NAMEATTR = {'startswith', 'endswith'}
ENUMF = {'os.listdir', 'listdir', 'os.scandir', 'os.walk', '_os.listdir'}


# --------------------------------------------------------------------------
def dotted(f):
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        d = dotted(f.value)
        return (d + '.' + f.attr) if d else f.attr
    if isinstance(f, ast.Call):
        return dotted(f.func) + '()'
    if isinstance(f, (ast.Constant, ast.JoinedStr)):
        return '<str>'
    return ''


def is_globcall(call):
    d = dotted(call.func)
    return d.split('.')[-1] in GLOBF and not d.endswith('Path.glob')


class Mod:
    """One python module: AST, parents, byte offsets, edits."""

    def __init__(self, path, rel):
        self.path, self.rel = path, rel
        self.raw = open(path, 'rb').read()
        self.src = self.raw.decode('utf-8')
        self.tree = ast.parse(self.raw)
        self.lines = self.raw.split(b'\n')
        self.loff = [0]
        for ln in self.lines:
            self.loff.append(self.loff[-1] + len(ln) + 1)
        self.par = {}
        for n in ast.walk(self.tree):
            for c in ast.iter_child_nodes(n):
                self.par[c] = n
        self.docs = set()
        for n in ast.walk(self.tree):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef,
                              ast.AsyncFunctionDef)):
                b = n.body
                if b and isinstance(b[0], ast.Expr) and isinstance(
                        b[0].value, ast.Constant) and isinstance(
                        b[0].value.value, str):
                    self.docs.add(b[0].value)
        self.funcs = {}
        for n in ast.walk(self.tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.funcs.setdefault(n.name, n)
        self.imports_os = any(
            isinstance(n, ast.Import) and any(a.name == 'os' and not a.asname
                                              for a in n.names)
            for n in self.tree.body) or bool(re.search(
                rb'^import os\b|^import .*\bos\b', self.raw, re.M))
        self.edits = []        # (start, end, newbytes, rule, line)
        self.sites = []        # (line, class, rule, detail)
        self.unclassified = []

    # offsets -------------------------------------------------------------
    def off(self, line, col):
        return self.loff[line - 1] + col

    def span(self, n):
        return (self.off(n.lineno, n.col_offset),
                self.off(n.end_lineno, n.end_col_offset))

    def seg(self, n):
        a, b = self.span(n)
        return self.raw[a:b].decode('utf-8')

    def edit(self, a, b, new, rule, line):
        self.edits.append((a, b, new.encode('utf-8') if isinstance(new, str)
                           else new, rule, line))

    def site(self, line, cls, rule, detail=''):
        self.sites.append((line, cls, rule, detail[:140]))

    def unk(self, node, why):
        self.unclassified.append((node.lineno, why,
                                  self.lines[node.lineno - 1].decode()
                                  .strip()[:150]))

    def scope_of(self, n):
        p = self.par.get(n)
        while p is not None and not isinstance(
                p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda,
                    ast.Module)):
            p = self.par.get(p)
        return p

    def stmt_of(self, n):
        p = n
        while p is not None and not isinstance(p, ast.stmt):
            p = self.par.get(p)
        return p


# --------------------------------------------------------------------------
def prefix_literal(m, node, rule):
    """P1: insert `numbers/` before the first `survey_numbers` in the source
    text of a string literal (handles r'', implicit concatenation)."""
    a, b = m.span(node)
    seg = m.raw[a:b]
    i = seg.find(SN.encode())
    if i < 0:
        return False
    if seg[max(0, i - 8):i] == b'numbers/':
        return True
    m.edit(a + i, a + i, SUB + '/', rule, node.lineno)
    return True


def climb(m, n):
    """Walk up through string-building nodes: `lit % x`, `lit + x`,
    `a if c else lit`, `lit.format(...)`, f-strings."""
    while True:
        p = m.par.get(n)
        if isinstance(p, ast.BinOp) and isinstance(p.op, ast.Mod) and p.left is n:
            n = p
            continue
        if isinstance(p, ast.BinOp) and isinstance(p.op, ast.Add) and \
                not _is_root_plus(p) and (
                (p.left is n and isinstance(p.right, ast.Constant) and
                 isinstance(p.right.value, str)) or
                (p.right is n and isinstance(p.left, ast.Constant) and
                 isinstance(p.left.value, str) and not p.left.value.endswith('/'))):
            n = p
            continue
        if isinstance(p, ast.BinOp) and isinstance(p.op, ast.Add) and (
                isinstance(p.left, (ast.Constant, ast.JoinedStr, ast.BinOp))
                and isinstance(p.right, (ast.Constant, ast.JoinedStr,
                                         ast.BinOp, ast.Call, ast.Name))
                and not _is_root_plus(p)):
            n = p
            continue
        if isinstance(p, ast.IfExp) and n in (p.body, p.orelse):
            n = p
            continue
        if isinstance(p, ast.Attribute) and p.attr == 'format' and \
                isinstance(m.par.get(p), ast.Call) and m.par[p].func is p:
            n = m.par[p]
            continue
        if isinstance(p, ast.JoinedStr):
            n = p
            continue
        if isinstance(p, ast.Call) and dotted(p.func) in ('suffixed', 'str'):
            n = p
            continue
        return n, p


def _is_root_plus(p):
    """`ROOT + '/survey_numbers...'`"""
    return (isinstance(p.right, ast.Constant) and isinstance(p.right.value, str)
            and p.right.value.startswith('/' + SN)
            and isinstance(p.left, (ast.Name, ast.Attribute, ast.Call)))


def literal_nodes(n):
    """The Constant str nodes (with survey_numbers) under a string expr."""
    return [c for c in ast.walk(n) if isinstance(c, ast.Constant)
            and isinstance(c.value, str) and SN in c.value]


# --------------------------------------------------------------------------
class Analyzer:
    def __init__(self, m, root_vars):
        self.m = m
        self.root_vars = root_vars
        self.tainted_vars = {}     # (scope, name) -> 'name' | 'path'
        self.tainted_funcs = {}    # function name -> 'name' (returns names)
        self.done_nodes = set()

    # context of an expression node ---------------------------------------
    def context(self, n):
        """Return (kind, info) for how the value of string expr `n` is used.
        kind in PATHJOIN, PATHARG, ROOTPLUS, NAMEPRED, REGEX, TEXT, ASSIGN,
        CONTAINER, HELPER, COMPARE, SUBSCRIPT, RETURN, DEFAULT, UNKNOWN."""
        m = self.m
        top, p = climb(m, n)
        if isinstance(p, ast.BinOp) and isinstance(p.op, ast.Add) and \
                _is_root_plus(p) and p.right is top:
            return 'ROOTPLUS', p
        if isinstance(p, ast.BinOp) and isinstance(p.op, ast.Mod) and \
                p.right is top:
            return 'TEXT', p
        if isinstance(p, (ast.BoolOp, ast.UnaryOp)) or (
                isinstance(p, ast.IfExp) and p.test is top) or (
                isinstance(p, (ast.If, ast.While)) and p.test is top):
            return 'NAMEOP', p
        if isinstance(p, ast.Call):
            d = dotted(p.func)
            last = d.split('.')[-1]
            if top in p.args:
                i = p.args.index(top)
                if d in JOIN or last == 'join' and d.startswith(('os.', '_os', 'osp', 'path')):
                    return ('PATHJOIN', (p, i)) if i >= 1 else ('JOINROOT', p)
                if (d in PATH1 or is_globcall(p)) and i == 0:
                    return 'PATHARG', p
                if d in REF and i == 0:
                    return 'REGEX', p
                if d in REF or last in ('match', 'fullmatch', 'search') and \
                        isinstance(p.func, ast.Attribute):
                    return 'NAMEPRED', p
                if d in ('len', 'os.path.splitext', 'os.path.basename', 're.escape',
                         'str', 'repr', 'sorted', 'set', 'list', 'tuple',
                         'any', 'all', 'enumerate', 'bool', 'int'):
                    if d in ('sorted', 'set', 'list', 'tuple'):
                        return 'COMPVALUE', p
                    return 'NAMEOP', p
                if last in NAMEATTR:
                    return 'NAMEPRED', p
                if d in TEXTF or last in ('write', 'insert', 'writelines',
                                          'format') or d == '<str>.join':
                    return 'TEXT', p
                if d in m.funcs:
                    return 'HELPER', (p, i)
                if isinstance(p.func, ast.Attribute) and last in (
                        'add', 'append', 'extend', 'update') and isinstance(
                        p.func.value, ast.Name):
                    return 'CONTAINER', p
                if isinstance(p.func, ast.Attribute) and last in (
                        'get', 'setdefault', 'pop', 'discard', 'remove',
                        'count', 'index', '__contains__'):
                    return 'NAMEOP', p
                if isinstance(p.func, ast.Attribute) and last in (
                        'startswith', 'endswith'):
                    return 'NAMEPRED', p
                if last in ('append', 'add', 'extend'):
                    return 'CONTAINER', p
                return 'UNKNOWN', 'call %s arg %d' % (d, i)
            if any(k.value is top for k in p.keywords):
                kw = [k for k in p.keywords if k.value is top][0]
                if kw.arg in ('pathname', 'file', 'path'):
                    return 'PATHARG', p
                return 'UNKNOWN', 'kw %s=' % kw.arg
            if p.func is top:
                return 'TEXT', p
            return 'UNKNOWN', 'call %s' % d
        if isinstance(p, ast.Attribute) and p.attr in NAMEATTR:
            return 'NAMEPRED', p
        if isinstance(p, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) and \
                p.elt is top:
            return 'COMPVALUE', p
        if isinstance(p, ast.Attribute) and isinstance(m.par.get(p), ast.Call) \
                and m.par[p].func is p and p.attr in (
                    'add', 'update', 'discard', 'remove', 'sort', 'append',
                    'extend', 'intersection', 'union', 'difference',
                    'issubset', 'issuperset', 'get', 'items', 'keys', 'pop',
                    'setdefault', 'copy', 'count', 'index', 'upper', 'lower',
                    'rstrip', 'lstrip', 'endswith', 'startswith', 'split',
                    'replace', 'strip', 'join', 'format', 'encode', 'rsplit'):
            return 'NAMEOP', p
        if isinstance(p, ast.BinOp) and isinstance(p.op, (ast.Sub, ast.BitAnd,
                                                          ast.BitOr, ast.BitXor)):
            return 'NAMEOP', p
        if isinstance(p, ast.BinOp) and isinstance(p.op, ast.Add) and \
                not any(isinstance(x, ast.Constant) and isinstance(x.value, str)
                        for x in (p.left, p.right)):
            return 'COMPVALUE', p
        if isinstance(p, ast.Attribute) and p.attr in ('replace', 'split',
                                                       'strip', 'join'):
            return 'TEXT', p
        if isinstance(p, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            return 'ASSIGN', p
        if isinstance(p, (ast.List, ast.Tuple, ast.Set)):
            return 'CONTAINER', p
        if isinstance(p, ast.Compare):
            return 'COMPARE', p
        if isinstance(p, (ast.Assert, ast.Raise)):
            return 'TEXT', p
        if isinstance(p, ast.Subscript):
            return 'SUBSCRIPT', p
        if isinstance(p, ast.Dict):
            return 'SUBSCRIPT', p
        if isinstance(p, ast.Return):
            return 'RETURN', p
        if isinstance(p, ast.arguments):
            return 'DEFAULT', p
        if isinstance(p, ast.FormattedValue):
            return 'TEXT', p
        if isinstance(p, ast.keyword):
            return 'TEXT', p
        if isinstance(p, ast.BoolOp) or isinstance(p, ast.UnaryOp):
            return 'UNKNOWN', 'boolop'
        if isinstance(p, ast.comprehension):
            return 'CONTAINER', p
        if isinstance(p, ast.Expr):
            return 'TEXT', p
        return 'UNKNOWN', type(p).__name__


    # ------------------------------------------------------------------
    # scoping
    def binding_scope(self, n, name):
        """The scope node that binds `name` as seen from node `n`."""
        m = self.m
        p = m.par.get(n)
        while p is not None:
            if isinstance(p, (ast.ListComp, ast.SetComp, ast.GeneratorExp,
                              ast.DictComp)):
                for g in p.generators:
                    if any(isinstance(x, ast.Name) and x.id == name
                           for x in ast.walk(g.target)):
                        return p
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.Lambda)):
                if self._binds(p, name):
                    return p
            p = m.par.get(p)
        return m.tree

    def _binds(self, fn, name):
        for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs:
            if a.arg == name:
                return True
        if fn.args.vararg and fn.args.vararg.arg == name:
            return True
        if isinstance(fn, ast.Lambda):
            return False
        for n in ast.walk(fn):
            if isinstance(n, ast.Global) and name in n.names:
                return False
        for n in ast.walk(fn):
            if isinstance(n, ast.Name) and n.id == name and \
                    isinstance(n.ctx, ast.Store):
                # bound in fn itself, not in a nested function / comprehension
                q = self.m.par.get(n)
                inner = False
                while q is not None and q is not fn:
                    if isinstance(q, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.Lambda)):
                        inner = True
                        break
                    q = self.m.par.get(q)
                if not inner:
                    return True
        return False

    def uses_of(self, name, scope):
        out = []
        for n in ast.walk(scope):
            if isinstance(n, ast.Name) and n.id == name and isinstance(
                    n.ctx, ast.Load) and self.binding_scope(n, name) is scope:
                out.append(n)
        return out

    def stores_of(self, name, scope):
        out = []
        for n in ast.walk(scope):
            if isinstance(n, ast.Name) and n.id == name and isinstance(
                    n.ctx, ast.Store) and self.binding_scope(n, name) is scope:
                out.append(n)
        return out

    # ------------------------------------------------------------------
    # is an expression a macro-file NAME source?
    def sn_literal_expr(self, e):
        """All leaves of a string expression are SN-shaped literals (or
        non-string operands of % / format).  Returns the literal nodes."""
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            return [e] if SN_LIT.match(e.value) else None
        if isinstance(e, ast.IfExp):
            a, b = self.sn_literal_expr(e.body), self.sn_literal_expr(e.orelse)
            return a + b if a is not None and b is not None else None
        if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Mod):
            return self.sn_literal_expr(e.left)
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and \
                e.func.attr == 'format':
            return self.sn_literal_expr(e.func.value)
        return None

    # ------------------------------------------------------------------
    # the variable engine
    def region_after(self, store, name, scope):
        """(start, end) byte span reached by the binding at `store` when
        the scope binds `name` more than once (straight-line approximation:
        from the store to the next store).  None when bound once."""
        m = self.m
        allst = self.stores_of(name, scope)
        if len(allst) <= 1:
            return None
        a = m.span(store)[0]

        def blocks(n):
            """ids of the statement lists enclosing n, innermost first."""
            out = []
            st = m.stmt_of(n)
            while st is not None:
                par = m.par.get(st)
                if par is None:
                    break
                for fld in ('body', 'orelse', 'finalbody', 'handlers'):
                    lst = getattr(par, fld, None)
                    if isinstance(lst, list) and st in lst:
                        out.append((id(par), fld))
                st = m.stmt_of(par) if not isinstance(par, ast.Module) else None
            return out
        mine = set(blocks(store))
        ends = []
        for x in allst:
            b = m.span(x)[0]
            if b <= a:
                continue
            bx = blocks(x)
            # a later binding ends the region only if it is not nested deeper
            # than this one (a conditional re-binding does not dominate)
            if bx and bx[0] in mine:
                ends.append(b)
        return (a, min(ends) if ends else len(m.raw))

    def var(self, name, scope, why, depth=0, region=None):
        """Classify variable `name` bound in `scope`, known to hold a
        macro-file NAME (or a container of names).  Returns its mode:
        'path' (every use is a path), 'mixed', or None on refusal.
        Edits are made here (P2 at path uses) unless the caller can prefix
        literals (mode 'path' and literal-only sources)."""
        key = (id(scope), name) if region is None else (id(scope), name, region)
        if key in self.vmode:
            return self.vmode[key]
        if region is not None and (id(scope), name) not in self.vmode:
            self.vmode[(id(scope), name)] = 'region'
        if depth > 8:
            self.m.unk(scope if hasattr(scope, 'lineno') else self.m.tree.body[0],
                       'flow too deep at %s' % name)
            return None
        self.vmode[key] = 'pending'
        m = self.m
        inreg = (lambda n: True) if region is None else (
            lambda n: region[0] <= m.span(n)[0] < region[1])
        uses = [u for u in self.uses_of(name, scope) if inreg(u)]
        kinds = [(u,) + self.context(u) for u in uses]
        # loops over this variable
        loops = [n for n in ast.walk(scope)
                 if isinstance(n, (ast.For, ast.comprehension))
                 and isinstance(n.iter, ast.Name) and n.iter.id == name
                 and self.binding_scope(n.iter, name) is scope
                 and inreg(n.iter)]
        loop_iters = {id(l.iter) for l in loops}
        direct_path = [k for k in kinds if k[1] in ('PATHJOIN', 'PATHARG')]
        rest = [k for k in kinds if k[1] not in ('PATHJOIN', 'PATHARG')
                and id(k[0]) not in loop_iters]
        sources = [x for x in self.stores_of(name, scope)
                   if region is None or region[0] <= m.span(x)[0] < region[1]]
        lit_only = bool(sources) and all(self._lit_source(s) for s in sources)
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                name in [a.arg for a in scope.args.args]:
            lit_only = lit_only and False
            param = True
        else:
            param = False
        if lit_only and direct_path and not rest and not loops:
            self.vmode[key] = 'path'
            for s in sources:
                for c in self._lit_source(s):
                    prefix_literal(m, c, 'P1var')
            m.site(sources[0].lineno, 'PATH', 'P1var', name)
            return 'path'
        ok = True
        for u, kind, info in kinds:
            if id(u) in loop_iters:
                continue
            ok &= self.dispatch(u, kind, info, name, why, depth)
        for l in loops:
            ok &= self.flow_loop(l, why, depth)
        self.vmode[key] = 'mixed' if ok else None
        return self.vmode[key]

    def dispatch(self, u, kind, info, name, why, depth):
        """One use of a NAME-valued expression."""
        m = self.m
        if kind in ('PATHJOIN', 'PATHARG'):
            return self.p2(u, kind, info, 'P2:' + why)
        if kind == 'COMPVALUE':
            return self._flow_value(info, why)
        if kind == 'JOINROOT':
            m.unk(u, '%s (a macro NAME) used as a join ROOT' % name)
            return False
        if kind in ('NAMEPRED', 'TEXT', 'COMPARE', 'SUBSCRIPT', 'REGEX',
                    'NAMEOP'):
            m.site(u.lineno, 'INERT', 'name-' + kind.lower(), name)
            return True
        if kind == 'ASSIGN':
            return self.flow_assign(u, info, why, depth)
        if kind == 'CONTAINER':
            return self.flow_container(u, info, why, depth)
        if kind == 'HELPER':
            return self.flow_helper(u, info, why, depth)
        if kind == 'RETURN':
            return self.flow_return(u, why, depth)
        if kind == 'ROOTPLUS':
            m.unk(u, 'name %s used as ROOT + name' % name)
            return False
        m.unk(u, 'name %s: %s %s' % (name, kind, info if isinstance(info, str)
                                       else ''))
        return False

    def flow_capture(self, c):
        """R1's capture group yields macro NAMES: follow them."""
        m = self.m
        top, p = climb(m, c)
        call = p if isinstance(p, ast.Call) and top in p.args else None
        if call is None and isinstance(p, ast.Assign):
            # PAT = re.compile(R): follow PAT.<fn>(...) calls
            tg = self._target(p)
            if tg is None:
                m.unk(c, 'manuscript regex assigned to a non-Name')
                return
            calls = [n for n in ast.walk(m.tree) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute)
                     and isinstance(n.func.value, ast.Name)
                     and n.func.value.id == tg.id]
            for cl in calls:
                self._from_regex_call(cl, cl.func.attr)
            return
        if call is None:
            m.unk(c, 'manuscript regex in an unknown position')
            return
        d = dotted(call.func).split('.')[-1]
        if d == 'compile':
            q = m.par.get(call)
            if isinstance(q, ast.Assign):
                self.flow_capture_assign(call, q)
                return
        self._from_regex_call(call, d)

    def flow_capture_assign(self, call, asg):
        m = self.m
        tg = self._target(asg)
        if tg is None:
            m.unk(call, 'compiled manuscript regex assigned to a non-Name')
            return
        for cl in [n for n in ast.walk(m.tree) if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Attribute)
                   and isinstance(n.func.value, ast.Name)
                   and n.func.value.id == tg.id]:
            self._from_regex_call(cl, cl.func.attr)

    def _from_regex_call(self, call, kind):
        m = self.m
        if kind == 'findall':
            # a list of names (one group) -- as a value
            p = m.par.get(call)
            if isinstance(p, (ast.For, ast.comprehension)) and p.iter is call:
                self.flow_loop(p, 'R1', 0)
            else:
                self._flow_value(call, 'R1')
            return
        if kind in ('finditer', 'match', 'search', 'fullmatch'):
            p = m.par.get(call)
            mobj = None
            scope = None
            if kind == 'finditer' and isinstance(p, (ast.For, ast.comprehension)) \
                    and p.iter is call and isinstance(p.target, ast.Name):
                mobj = p.target.id
                scope = p if isinstance(p, ast.For) else m.par.get(p)
            elif isinstance(p, ast.Assign) and self._target(p) is not None:
                mobj = self._target(p).id
                scope = m.scope_of(p)
            elif isinstance(p, ast.NamedExpr):
                mobj = p.target.id
                scope = m.scope_of(p)
            if mobj is None:
                m.unk(call, 'manuscript regex match object not bound to a name')
                return
            groups = [n for n in ast.walk(scope) if isinstance(n, ast.Call)
                      and isinstance(n.func, ast.Attribute)
                      and n.func.attr == 'group'
                      and isinstance(n.func.value, ast.Name)
                      and n.func.value.id == mobj]
            for g in groups:
                kind2, info2 = self.context(g)
                self.dispatch(g, kind2, info2, mobj + '.group', 'R1', 0)
            return
        if kind == 'sub':
            m.site(call.lineno, 'INERT', 'regex-sub', '')
            return
        m.unk(call, 'manuscript regex used by %s' % kind)

    def _lit_source(self, store):
        """Literal nodes if `store` (a Store Name) is assigned an SN literal
        expression, else None/False."""
        a = self.m.par.get(store)
        if isinstance(a, ast.Assign) and len(a.targets) == 1 and \
                a.targets[0] is store:
            return self.sn_literal_expr(a.value)
        if isinstance(a, ast.AnnAssign) and a.target is store and a.value:
            return self.sn_literal_expr(a.value)
        return None

    def p2(self, use, kind, info, rule):
        """Insert the subdirectory at one PATH use of a NAME value."""
        m = self.m
        top, p = climb(m, use)
        if kind == 'PATHJOIN':
            call, i = info
            mids = call.args[1:i]
            if any(isinstance(a, ast.Constant) and a.value == SUB
                   for a in call.args[:i]):
                return True                           # already repointed
            if any(isinstance(a, ast.Constant) and isinstance(a.value, str)
                   for a in mids):
                m.site(use.lineno, 'INERT', 'ALTDIR', m.seg(call)[:100])
                return True
            a, _ = m.span(call.args[i])
            m.edit(a, a, "'%s', " % SUB, rule, use.lineno)
            m.site(use.lineno, 'PATH', rule, m.seg(call)[:100])
            return True
        if kind == 'PATHARG':
            call = info
            seg = m.seg(top)
            if seg.startswith("os.path.join('%s', " % SUB):
                return True
            if seg.startswith("'%s/' + " % SUB):
                return True
            a, b = m.span(top)
            if not m.imports_os:
                m.edit(a, a, "'%s/' + " % SUB, rule, use.lineno)
            else:
                m.edit(a, a, "os.path.join('%s', " % SUB, rule, use.lineno)
                m.edit(b, b, ")", rule, use.lineno)
            m.site(use.lineno, 'PATH', rule, m.seg(call)[:100])
            return True
        return False

    def flow_assign(self, u, asg, why, depth):
        m = self.m
        tg = asg.targets[0] if isinstance(asg, ast.Assign) and \
            len(asg.targets) == 1 else getattr(asg, 'target', None)
        if isinstance(tg, ast.Name):
            sc = self.binding_scope(tg, tg.id)
            return self.var(tg.id, sc, why, depth + 1,
                            self.region_after(tg, tg.id, sc)) is not None
        if isinstance(tg, ast.Subscript):
            m.site(u.lineno, 'INERT', 'name-stored-in-dict', m.seg(tg)[:60])
            return True
        if isinstance(tg, ast.Tuple):
            m.site(u.lineno, 'INERT', 'name-tuple-assign', m.seg(tg)[:60])
            return True
        m.unk(u, 'name assigned to %s' % type(tg).__name__)
        return False

    def flow_loop(self, loop, why, depth):
        m = self.m
        t = loop.target
        if isinstance(t, ast.Tuple) and t.elts and isinstance(t.elts[0], ast.Name):
            t = t.elts[0]
        if isinstance(t, ast.Name):
            sc = self.binding_scope(t, t.id)
            reg = None
            if isinstance(loop, ast.For) and len(self.stores_of(t.id, sc)) > 1:
                reg = m.span(loop)
            return self.var(t.id, sc, why, depth + 1, reg) is not None
        m.unk(loop.iter, 'loop target over names')
        return False

    def flow_container(self, u, cont, why, depth):
        m = self.m
        if isinstance(cont, ast.Call):               # L.append(x)
            f = cont.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                sc = self.binding_scope(f.value, f.value.id)
                return self.var(f.value.id, sc, why, depth + 1) is not None
            if isinstance(f, ast.Attribute):
                m.site(u.lineno, 'INERT', 'name-record', m.seg(cont)[:80])
                return True
            m.unk(u, 'append to non-Name')
            return False
        top = cont
        while True:
            p = m.par.get(top)
            if isinstance(p, (ast.List, ast.Tuple, ast.Set)) or (
                    isinstance(p, ast.BinOp) and isinstance(p.op, ast.Add)) or (
                    isinstance(p, ast.Call) and dotted(p.func) in (
                        'sorted', 'list', 'set', 'tuple', 'frozenset')):
                top = p
                continue
            break
        p = m.par.get(top)
        if isinstance(p, ast.BinOp) and isinstance(p.op, ast.Mod) and \
                p.right is top or isinstance(p, (ast.Assert, ast.Raise)):
            m.site(u.lineno, 'INERT', 'name-text', '')
            return True
        if isinstance(p, (ast.Assign, ast.AnnAssign)):
            return self.flow_assign(u, p, why, depth)
        if isinstance(p, (ast.For, ast.comprehension)) and p.iter is top:
            return self.flow_loop(p, why, depth)
        if isinstance(p, ast.Compare):
            m.site(u.lineno, 'INERT', 'name-membership', m.seg(p)[:80])
            return True
        if isinstance(p, ast.Call):
            d = dotted(p.func)
            if d.split('.')[-1] in NAMEATTR:
                m.site(u.lineno, 'INERT', 'name-namepred', m.seg(p)[:80])
                return True
            if d in TEXTF or d.split('.')[-1] in ('append', 'write', 'add'):
                if d.split('.')[-1] in ('append', 'add') and isinstance(
                        p.func, ast.Attribute) and isinstance(p.func.value, ast.Name):
                    # a (name, ...) tuple appended to a record list
                    m.site(u.lineno, 'INERT', 'name-record', m.seg(p)[:80])
                    return True
                m.site(u.lineno, 'INERT', 'text', m.seg(p)[:80])
                return True
        if isinstance(p, ast.Return):
            return self.flow_return(top, why, depth)
        m.unk(u, 'container held by %s' % type(p).__name__)
        return False

    def flow_helper(self, u, info, why, depth):
        m = self.m
        call, i = info
        fn = m.funcs[dotted(call.func)]
        params = [a.arg for a in fn.args.args]
        if i >= len(params):
            if fn.args.vararg:
                m.unk(u, 'name passed through *%s of %s' % (fn.args.vararg.arg,
                                                            fn.name))
            else:
                m.unk(u, 'helper %s arg %d beyond params' % (fn.name, i))
            return False
        pname = params[i]
        if self.pmode(fn, pname) == 'path':
            # a path helper given a NAME: repoint the argument
            arg = call.args[i]
            if m.seg(arg).startswith("os.path.join('%s', " % SUB):
                return True
            if not m.imports_os:
                m.unk(u, 'no `import os` for a repointed helper argument')
                return False
            a, b = m.span(arg)
            m.edit(a, a, "os.path.join('%s', " % SUB, 'P2h:' + why, u.lineno)
            m.edit(b, b, ")", 'P2h:' + why, u.lineno)
            m.site(u.lineno, 'PATH', 'P2h', m.seg(call)[:80])
            return True
        mode = self.var(pname, fn, why + '>' + fn.name, depth + 1)
        if mode is None:
            return False
        # every call site must pass a macro-file name, else the helper's P2
        # would repoint a non-macro file too
        for c in ast.walk(m.tree):
            if isinstance(c, ast.Call) and dotted(c.func) == fn.name and \
                    len(c.args) > i:
                a = c.args[i]
                if self.sn_literal_expr(a) is not None:
                    continue
                if isinstance(a, ast.Name) and self.vmode.get(
                        (id(self.binding_scope(a, a.id)), a.id)) not in (None,):
                    if (id(self.binding_scope(a, a.id)), a.id) in self.vmode:
                        continue
                m.unk(c, 'helper %s param %s is repointed but this call '
                      'passes %s' % (fn.name, pname, m.seg(a)[:60]))
                return False
        return True

    def flow_return(self, u, why, depth):
        m = self.m
        fn = u
        while fn is not None and not isinstance(fn, (ast.FunctionDef,
                                                     ast.AsyncFunctionDef)):
            fn = m.par.get(fn)
        if fn is None:
            m.unk(u, 'return outside function')
            return False
        if fn.name in self.fret:
            return True
        self.fret.add(fn.name)
        ok = True
        for c in ast.walk(m.tree):
            if not (isinstance(c, ast.Call) and dotted(c.func) == fn.name):
                continue
            top = c
            while isinstance(m.par.get(top), ast.Call) and dotted(
                    m.par[top].func) in ('sorted', 'list', 'set', 'tuple',
                                         'len', 'enumerate'):
                top = m.par[top]
            p = m.par.get(top)
            if isinstance(p, (ast.For, ast.comprehension)) and p.iter is top:
                ok &= self.flow_loop(p, why, depth)
            elif isinstance(p, (ast.Assign, ast.AnnAssign)):
                ok &= self.flow_assign(c, p, why, depth)
            elif isinstance(p, (ast.Compare, ast.BinOp, ast.BoolOp,
                                ast.UnaryOp)) or (isinstance(p, ast.Call) and
                                                  dotted(p.func) in TEXTF):
                m.site(c.lineno, 'INERT', 'name-set', m.seg(p)[:80])
            elif isinstance(top, ast.Call) and dotted(top.func) == 'len':
                m.site(c.lineno, 'INERT', 'name-count', '')
            else:
                m.unk(c, 'result of name-returning %s in %s'
                      % (fn.name, type(p).__name__))
                ok = False
        return ok

    # ------------------------------------------------------------------
    def literal(self, c):
        """Classify one string Constant that mentions survey_numbers."""
        m = self.m
        v = c.value
        if c in m.docs or isinstance(m.par.get(c), ast.Expr):
            m.site(c.lineno, 'INERT', 'docstring')
            return
        if id(c) in self.seen:
            return
        self.seen.add(id(c))
        q = m.par.get(c)
        while q is not None and not isinstance(q, ast.stmt):
            if isinstance(q, ast.JoinedStr):
                # f-string part positions are unreliable before Python 3.12
                m.unk(c, 'macro-file name inside an f-string')
                return
            q = m.par.get(q)
        a, b = m.span(c)
        seg = m.raw[a:b].decode()
        # R1 -- a regex over the manuscript's \input lines
        if re.search(r'input\\+\{\(?(?:\?:numbers/\)\?\()?survey_numbers', seg):
            kind, info = self.context(c)
            if kind in ('REGEX', 'ASSIGN') or 'REGEX' in kind:
                if '(?:numbers/)?' in seg:
                    m.site(c.lineno, 'DONE', 'R1')
                    self.flow_capture(c)
                    return
                mm = re.search(r'\\\{\(survey_numbers|\\\{survey_numbers', seg)
                if not mm:
                    m.unk(c, 'manuscript regex of unknown shape')
                    return
                # insert the optional subdirectory OUTSIDE the capture group
                j = a + mm.start() + 2
                m.edit(j, j, '(?:%s/)?' % SUB, 'R1', c.lineno)
                m.site(c.lineno, 'REGEX', 'R1', seg[:80])
                self.flow_capture(c)
                return
        # T2 -- a TeX snippet in code
        if '\\input{' in v and SN in v:
            if '\\input{%s/' % SUB in v and '\\input{survey_numbers' not in v:
                m.site(c.lineno, 'DONE', 'T2')
                return
            for mm in re.finditer(r'input\{survey_numbers', seg):
                j = a + mm.start() + len('input{')
                m.edit(j, j, SUB + '/', 'T2', c.lineno)
            m.site(c.lineno, 'TEX', 'T2', v[:80])
            return
        if SN_DONE.search(v):
            m.site(c.lineno, 'DONE', 'P1')
            if '*' in v:
                self.p1cont_done(c)
            self.basename_followups(c)
            return
        kind, info = self.context(c)
        lit = SN_LIT.match(v) is not None
        if kind in ('PATHJOIN', 'PATHARG', 'ROOTPLUS'):
            if not lit:
                m.unk(c, 'non-filename text in a path position')
                return
            if '*' in v and kind == 'PATHARG' and is_globcall(info) and \
                    info.args and info.args[0] is c:
                # a CWD-relative glob: its entries are bare names before the
                # move; name or path semantics is decided at the end (P1g)
                self.pending_glob.append((c, info))
                return
            prefix_literal(m, c, 'P1')
            m.site(c.lineno, 'PATH', 'P1', v)
            if '*' in v and kind == 'PATHARG':
                self.p1_container(c)
            if kind == 'PATHJOIN':
                self.basename_followups(c)
            return
        if not lit:
            if kind in ('TEXT', 'ASSIGN', 'CONTAINER', 'COMPARE', 'NAMEPRED',
                        'HELPER', 'UNKNOWN', 'SUBSCRIPT', 'RETURN', 'REGEX'):
                # text with spaces / punctuation: a message, a header line, a
                # regex over SOURCE text -- not a file reference
                if kind == 'REGEX' and not re.search(r'\s', v):
                    m.site(c.lineno, 'INERT', 'regex-unanchored', v[:80])
                    return
                if kind == 'REGEX' or re.search(r'\s', v) or kind == 'TEXT' \
                        or re.search(r'[:\x00]', v):
                    m.site(c.lineno, 'INERT', 'text', v[:80])
                    return
            m.unk(c, 'non-filename literal in %s' % kind)
            return
        if kind in ('NAMEPRED', 'COMPARE', 'TEXT', 'SUBSCRIPT'):
            m.site(c.lineno, 'INERT', 'name-' + kind.lower(), v)
            return
        if kind == 'REGEX':
            m.site(c.lineno, 'INERT', 'name-regex', v)
            return
        if kind == 'ASSIGN':
            tg = self._target(info)
            if tg is None:
                if isinstance(getattr(info, 'targets', [None])[0], ast.Tuple):
                    m.site(c.lineno, 'INERT', 'name-tuple-assign', v)
                    return
                m.unk(c, 'literal assigned to non-Name')
                return
            sc = self.binding_scope(tg, tg.id)
            self.var(tg.id, sc, 'lit', 0, self.region_after(tg, tg.id, sc))
            return
        if kind == 'CONTAINER':
            if self._mixed_container(c, info):
                return
            self.flow_container(c, info, 'lit', 0)
            return
        if kind == 'HELPER':
            call, i = info
            fn = m.funcs[dotted(call.func)]
            params = [x.arg for x in fn.args.args]
            if i >= len(params):
                if fn.args.vararg and self._vararg_join(fn):
                    prefix_literal(m, c, 'P1h')
                    m.site(c.lineno, 'PATH', 'P1h*', '%s(%s)' % (fn.name, v))
                    return
                m.unk(c, 'helper arg beyond params')
                return
            mode = self.pmode(fn, params[i])
            if mode == 'path':
                prefix_literal(m, c, 'P1h')
                m.site(c.lineno, 'PATH', 'P1h', '%s(%s)' % (fn.name, v))
            elif mode == 'mixed':
                m.site(c.lineno, 'INERT', 'name-to-helper', fn.name)
            return
        if kind == 'DEFAULT':
            fn = m.par.get(info)
            pi = None
            for k, d in enumerate(info.defaults):
                if d is c or c in ast.walk(d):
                    pi = len(info.args) - len(info.defaults) + k
            if pi is None:
                m.unk(c, 'default of unknown param')
                return
            mode = self.pmode(fn, info.args[pi].arg)
            if mode == 'path':
                prefix_literal(m, c, 'P1d')
                m.site(c.lineno, 'PATH', 'P1d', v)
            return
        if kind == 'RETURN':
            self.flow_return(c, 'lit', 0)
            return
        if kind == 'COMPVALUE':
            self._flow_value(info, 'lit')
            return
        if kind == 'NAMEOP':
            m.site(c.lineno, 'INERT', 'name-op', v)
            return
        m.unk(c, 'literal in %s %s' % (kind, info if isinstance(info, str) else ''))

    def _mixed_container(self, c, cont):
        """P1m: a literal list of PRODUCT FILES mixing macro files with
        other files (`PRODUCTS = ['survey_numbers_round102.tex',
        'tab_x.tex', ...]`) iterated as paths: the loop variable is not a
        macro name, so P2 at its uses would repoint the other files too.
        Prefix the macro-file elements instead -- valid when the loop
        variable is used as a path, a key or text, never tested as a macro
        name.  Returns True if handled."""
        m = self.m
        if not isinstance(cont, (ast.List, ast.Tuple, ast.Set)):
            return False
        FN = re.compile(r'^[\w./-]+\.(tex|json|csv|pdf|txt|py|tsv|npz)$')
        strs = [e for e in cont.elts if isinstance(e, ast.Constant)
                and isinstance(e.value, str)]
        if not any(SN not in e.value and FN.match(e.value) for e in strs):
            return False
        top = cont
        while isinstance(m.par.get(top), (ast.BinOp, ast.List)):
            top = m.par[top]
        asg = m.par.get(top)
        tg = self._target(asg) if isinstance(asg, ast.Assign) else None
        if tg is None:
            return False                    # a record tuple: names
        sc = self.binding_scope(tg, tg.id)
        loops = [n for n in ast.walk(sc) if isinstance(n, (ast.For,
                                                           ast.comprehension))
                 and isinstance(n.iter, ast.Name) and n.iter.id == tg.id]
        if not loops:
            return False                    # membership only: names
        for l in loops:
            if not isinstance(l.target, ast.Name):
                return False
            body = l if isinstance(l, ast.For) else m.par.get(l)
            for u in [n for n in ast.walk(body) if isinstance(n, ast.Name)
                      and n.id == l.target.id and isinstance(n.ctx, ast.Load)]:
                k, inf = self.context(u)
                if k in ('NAMEPRED', 'REGEX'):
                    m.unk(u, 'mixed product list tested as a macro name')
                    return True
        key = ('p1m', id(cont))
        if key not in self.vmode:
            self.vmode[key] = 'p1m'
            for e in strs:
                if SN in e.value and SN_LIT.match(e.value):
                    prefix_literal(m, e, 'P1m')
                    self.seen.add(id(e))
            m.site(c.lineno, 'PATH', 'P1m', tg.id)
        return True

    def _target(self, asg):
        if isinstance(asg, ast.Assign) and len(asg.targets) == 1 and \
                isinstance(asg.targets[0], ast.Name):
            return asg.targets[0]
        if isinstance(asg, ast.AnnAssign) and isinstance(asg.target, ast.Name):
            return asg.target
        return None

    def _vararg_join(self, fn):
        """`def p(*a): return os.path.join(ROOT, *a)`"""
        va = fn.args.vararg.arg
        body = [n for n in fn.body if not (isinstance(n, ast.Expr) and
                                            isinstance(n.value, ast.Constant))]
        return len(body) == 1 and isinstance(body[0], ast.Return) and \
            isinstance(body[0].value, ast.Call) and \
            dotted(body[0].value.func) in JOIN and any(
                isinstance(a, ast.Starred) and isinstance(a.value, ast.Name)
                and a.value.id == va for a in body[0].value.args[1:])

    def _suffix_helper(self, fn, pname):
        """`def out(name): b, e = os.path.splitext(name); return
        join(ROOT, b + SFX + e)` (or a local path helper P(b + SFX + e)):
        the subdirectory a caller's literal carries survives splitext and
        the re-join, so the parameter is a PATH."""
        m = self.m
        body = [n for n in fn.body if not (isinstance(n, ast.Expr) and
                                            isinstance(n.value, ast.Constant))]
        if len(body) != 2 or not isinstance(body[0], ast.Assign) or \
                not isinstance(body[1], ast.Return):
            return False
        a0 = body[0]
        if not (isinstance(a0.targets[0], ast.Tuple) and
                len(a0.targets[0].elts) == 2 and
                isinstance(a0.value, ast.Call) and
                dotted(a0.value.func) == 'os.path.splitext' and
                isinstance(a0.value.args[0], ast.Name) and
                a0.value.args[0].id == pname):
            return False
        st, ex = [x.id for x in a0.targets[0].elts]
        r = body[1].value
        if not isinstance(r, ast.Call) or not r.args:
            return False
        last = r.args[-1]
        names = {x.id for x in ast.walk(last) if isinstance(x, ast.Name)}
        if not (isinstance(last, ast.BinOp) and st in names and ex in names):
            return False
        d = dotted(r.func)
        if d in JOIN and len(r.args) >= 2:
            return True
        if d in m.funcs:
            g = m.funcs[d]
            gp = [x.arg for x in g.args.args]
            if gp and self.pmode(g, gp[min(len(r.args) - 1, len(gp) - 1)]) == 'path':
                return True
        return False

    def basename_followups(self, c):
        """After P1 on a literal inside `V = join(ROOT, 'numbers/...')`:
        `os.path.basename(V)` is a bare NAME again and must be followed
        (`out(os.path.basename(OUT))` would otherwise write at the root)."""
        m = self.m
        st = m.stmt_of(c)
        if not isinstance(st, ast.Assign) or self._target(st) is None:
            return
        tg = self._target(st)
        sc = self.binding_scope(tg, tg.id)
        for u in self.uses_of(tg.id, sc):
            p = m.par.get(u)
            if isinstance(p, ast.Call) and dotted(p.func) == 'os.path.basename' \
                    and p.args and p.args[0] is u:
                kind, info = self.context(p)
                if kind in ('TEXT', 'NAMEOP', 'COMPARE', 'NAMEPRED'):
                    continue
                self.dispatch(p, kind, info, 'basename(%s)' % tg.id, 'B1', 0)

    def pmode(self, fn, pname):
        """Mode of helper parameter `pname`: 'path' if every use is a path
        and every call site passes an SN literal; else analysed as a name
        variable (P2 inside the helper)."""
        key = ('param', fn.name, pname)
        if key in self.vmode:
            return self.vmode[key]
        m = self.m
        if self._suffix_helper(fn, pname):
            self.vmode[key] = 'path'
            m.site(fn.lineno, 'PATH', 'helper-suffix', fn.name)
            return 'path'
        uses = self.uses_of(pname, fn)
        kinds = [self.context(u)[0] for u in uses]
        idx = [a.arg for a in fn.args.args].index(pname)
        calls = [c for c in ast.walk(m.tree) if isinstance(c, ast.Call)
                 and dotted(c.func) == fn.name]
        all_lit = all(len(c.args) > idx and self.sn_literal_expr(c.args[idx])
                      is not None for c in calls)
        if kinds and all(k in ('PATHJOIN', 'PATHARG') for k in kinds):
            # a pure path helper (`out(name)` = join(OUTDIR, name)): the
            # macro-file literals its callers pass are prefixed at the call
            # site; callers passing other files are untouched
            self.vmode[key] = 'path'
            return 'path'
        mode = self.var(pname, fn, 'param:' + fn.name)
        if mode == 'mixed' and any(k in ('PATHJOIN', 'PATHARG') for k in kinds):
            # P2 went INSIDE the helper: every caller must pass a macro name
            self.deferred.append((fn, idx, calls))
        self.vmode[key] = mode
        return mode

    # ------------------------------------------------------------------
    # enumerations that do not name survey_numbers
    def _enum_kind(self, call):
        d = dotted(call.func)
        last = d.split('.')[-1]
        if last == 'walk':
            return 'walk'
        if d in ENUMF or last in ('listdir', 'scandir'):
            return 'listdir'
        if last == 'walk' and d.endswith('walk'):
            return 'walk'
        if last in GLOBF or last in ('rglob',):
            return 'glob'
        if last == 'iterdir':
            return 'listdir'
        return None

    def _dir_is_subdir(self, e):
        """True if expression e names a SUBdirectory by literal (join(X,'figures'))."""
        if isinstance(e, ast.Call) and dotted(e.func) in JOIN:
            return any(isinstance(a, ast.Constant) and isinstance(a.value, str)
                       and a.value not in ('.', '') for a in e.args[1:])
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            return e.value not in ('.', '', './') and not e.value.startswith('/')
        if isinstance(e, ast.Name):
            vals = self._values_of(e)
            return bool(vals) and all(self._dir_is_subdir(v) for v in vals)
        if isinstance(e, ast.Call) and dotted(e.func) == 'os.path.dirname' and \
                e.args and isinstance(e.args[0], ast.Name) and \
                e.args[0].id in ('HERE', 'here'):
            return True              # the PARENT of the build root
        return False

    def _values_of(self, name_node):
        """Values assigned to a Name in its binding scope (None if any
        binding is not a plain assignment, e.g. a loop or a parameter)."""
        sc = self.binding_scope(name_node, name_node.id)
        vals = []
        for st in self.stores_of(name_node.id, sc):
            a = self.m.par.get(st)
            if isinstance(a, ast.Assign) and len(a.targets) == 1 and \
                    a.targets[0] is st:
                vals.append(a.value)
            else:
                return None
        if isinstance(sc, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                name_node.id in [x.arg for x in sc.args.args]:
            return None
        return vals

    def _preds_on(self, scope_node, name):
        """String literals in startswith/endswith/regex/`in` tests on name."""
        lits = []
        for n in ast.walk(scope_node):
            if isinstance(n, ast.Call):
                d = dotted(n.func)
                last = d.split('.')[-1]
                recv = n.func.value if isinstance(n.func, ast.Attribute) else None
                on = (isinstance(recv, ast.Name) and recv.id == name) or (
                    isinstance(recv, ast.Call) and any(
                        isinstance(x, ast.Name) and x.id == name
                        for x in ast.walk(recv)))
                if last in NAMEATTR and on:
                    for a in n.args:
                        for x in ast.walk(a):
                            if isinstance(x, ast.Constant) and isinstance(
                                    x.value, str):
                                lits.append((last, x.value))
                if d in REF and len(n.args) >= 2 and any(
                        isinstance(x, ast.Name) and x.id == name
                        for x in ast.walk(n.args[1])):
                    for x in ast.walk(n.args[0]):
                        if isinstance(x, ast.Constant) and isinstance(x.value, str):
                            lits.append(('re', x.value))
                            lits.append(('re:' + last, x.value))
                if isinstance(n.func, ast.Attribute) and n.func.attr in (
                        'match', 'fullmatch', 'search') and isinstance(
                        n.func.value, ast.Name) and n.args and any(
                        isinstance(x, ast.Name) and x.id == name
                        for x in ast.walk(n.args[0])):
                    for v in (self._values_of(n.func.value) or []):
                        if isinstance(v, ast.Call) and dotted(v.func) in REF \
                                and v.args and isinstance(v.args[0], ast.Constant):
                            lits.append(('re', v.args[0].value))
                            lits.append(('re:' + n.func.attr, v.args[0].value))
                if d in ('fnmatch.fnmatch', 'fnmatch') and n.args and any(
                        isinstance(x, ast.Name) and x.id == name
                        for x in ast.walk(n.args[0])):
                    for x in ast.walk(n.args[1]):
                        if isinstance(x, ast.Constant):
                            lits.append(('fn', str(x.value)))
        return lits

    @staticmethod
    def _reaches_sn(preds):
        """Could a name satisfying these predicates be a macro file?  Each
        startswith/endswith literal must admit 'survey_numbers_round8.tex'."""
        for probe in PROBES:
            if Analyzer._reaches_one(preds, probe):
                return True
        return False

    @staticmethod
    def _reaches_one(preds, probe):
        for kind, lit in preds:
            if kind in ('re:match', 're:fullmatch'):
                try:
                    f = re.fullmatch if kind == 're:fullmatch' else re.match
                    if not f(lit, probe) and not f(lit, SUB + '/' + probe):
                        return False
                except re.error:
                    pass
            if kind == 'startswith' and not (probe.startswith(lit) or
                                             lit.startswith(SN)):
                if lit not in ('.', '_'):
                    return False
            if kind == 'endswith' and not (probe.endswith(lit) or
                                           re.fullmatch(r'round\d+\.tex', lit)
                                           or lit.endswith('.tex')):
                return False
        return True

    @staticmethod
    def _sn_only(preds):
        for kind, lit in preds:
            if kind == 'startswith' and lit.startswith('survey_numbers'):
                return True
            if kind == 're' and 'survey_numbers' in lit:
                return True
            if kind == 'endswith' and re.fullmatch(r'round\d+\.tex', lit):
                return True
        return False

    GENERIC_INPUT = re.compile(r'input[^{]{0,24}\\\{\((\[\^\}\][*+]|\[A-Za-z0-9_/\][*+])\)')

    def generic_inputs(self):
        """R2: a GENERIC \\input capture (`\\input\{([^}]*)\}`) yields
        targets as written, which carry numbers/ after T1.  Where the module
        tests those targets as macro NAMES (`n.startswith('survey_numbers')`
        on a bare variable that is never a path), the capture must keep
        yielding names: insert `(?:numbers/)?` before the group.  Where the
        targets are only used as paths, the prefix is what locates the file
        and nothing is changed."""
        m = self.m
        sites = []
        for c in ast.walk(m.tree):
            if isinstance(c, ast.Constant) and isinstance(c.value, str) and \
                    c not in m.docs:
                seg = m.seg(c)
                if self.GENERIC_INPUT.search(seg) and SN not in seg:
                    sites.append(c)
        if not sites:
            return
        name_tests = []
        for n in ast.walk(m.tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr == 'startswith' and isinstance(
                        n.func.value, ast.Name) and n.args and isinstance(
                        n.args[0], ast.Constant) and isinstance(
                        n.args[0].value, str) and n.args[0].value.startswith(SN):
                name_tests.append(n.func.value.id)
        if not name_tests:
            for c in sites:
                m.site(c.lineno, 'INERT', 'generic-input-paths', m.seg(c)[:60])
            return
        # the tested names must never reach a path sink
        for n in ast.walk(m.tree):
            if isinstance(n, ast.Name) and n.id in name_tests and \
                    isinstance(n.ctx, ast.Load):
                k, _ = self.context(n)
                if k in ('PATHJOIN', 'PATHARG', 'ROOTPLUS'):
                    m.unk(c, 'generic \\input capture: targets tested as names '
                          'and used as paths')
                    return
        for c in sites:
            seg = m.seg(c)
            if '(?:%s/)?' % SUB in seg:
                m.site(c.lineno, 'DONE', 'R2')
                continue
            mm = self.GENERIC_INPUT.search(seg)
            j = m.span(c)[0] + mm.start(1) - 1      # the '(' of the group
            m.edit(j, j, '(?:%s/)?' % SUB, 'R2', c.lineno)
            m.site(c.lineno, 'REGEX', 'R2', seg[:60])

    def enumerations(self):
        m = self.m
        for call in [n for n in ast.walk(m.tree) if isinstance(n, ast.Call)]:
            k = self._enum_kind(call)
            if k is None:
                continue
            arg = call.args[0] if call.args else None
            if arg is not None and any(
                    isinstance(x, ast.Constant) and isinstance(x.value, str)
                    and SN in x.value for x in ast.walk(arg)):
                continue                        # an SN glob: P1 handles it
            done_e1 = arg is not None and any(
                isinstance(x, ast.Constant) and x.value == SUB
                for x in ast.walk(arg))
            if self._is_e2_done(call):
                m.site(call.lineno, 'DONE', 'E2')
                continue
            if k == 'glob':
                pat = None
                if isinstance(arg, ast.Constant):
                    pat = arg.value
                elif isinstance(arg, ast.Call) and dotted(arg.func) in JOIN \
                        and isinstance(arg.args[-1], ast.Constant):
                    pat = arg.args[-1].value
                    if self._dir_is_subdir(ast.Call(func=arg.func,
                                                    args=arg.args[:-1],
                                                    keywords=[])):
                        m.site(call.lineno, 'INERT', 'enum-subdir', m.seg(call)[:80])
                        continue
                if isinstance(arg, ast.Name):
                    vals = self._values_of(arg)
                    if vals and all(isinstance(v, ast.Constant) and
                                    isinstance(v.value, str) for v in vals):
                        pats = [v.value for v in vals]
                        if all(SN in x for x in pats):
                            continue          # the literal's own flow (P1var)
                        pat = pats[0] if len(pats) == 1 else None
                if not isinstance(pat, str):
                    v = self._computed_pattern(call, arg)
                    if v is True:
                        continue
                    self._enum_unknown(call, 'glob of a computed pattern')
                    continue
                if '/' in pat.strip('/') and not pat.startswith('*'):
                    m.site(call.lineno, 'INERT', 'enum-subdir', pat)
                    continue
                import fnmatch
                base = pat.split('/')[-1]
                if not any(fnmatch.fnmatchcase(pr, base) for pr in PROBES):
                    m.site(call.lineno, 'INERT', 'enum-cannot-reach', pat)
                    continue
                self._broad(call, 'glob', pat)
                continue
            # listdir / scandir / walk
            if arg is not None and self._dir_is_subdir(arg) and not done_e1:
                m.site(call.lineno, 'INERT', 'enum-subdir', m.seg(arg)[:60])
                continue
            # find the consumer (through sorted()/list() and `a + b`)
            top = call
            while True:
                q = m.par.get(top)
                if isinstance(q, ast.Call) and dotted(q.func) in (
                        'sorted', 'list', 'set', 'tuple') and top in q.args:
                    top = q
                    continue
                if isinstance(q, ast.BinOp) and isinstance(q.op, ast.Add):
                    top = q
                    continue
                break
            p = m.par.get(top)
            if k == 'walk':
                # os.walk RECURSES: it reaches numbers/ after the move as it
                # reached the root before.  Safe unless it prunes dirnames.
                loop = p if isinstance(p, (ast.For, ast.comprehension)) else None
                prune = False
                if loop is not None and isinstance(loop.target, ast.Tuple) and \
                        len(loop.target.elts) >= 2 and isinstance(
                            loop.target.elts[1], ast.Name):
                    dn = loop.target.elts[1].id
                    body = loop if isinstance(loop, ast.For) else m.par.get(loop)
                    for x in ast.walk(body):
                        if isinstance(x, (ast.Assign, ast.Delete, ast.AugAssign)) \
                                and any(isinstance(y, ast.Name) and y.id == dn
                                        for t in (x.targets if hasattr(x, 'targets')
                                                  else [x.target])
                                        for y in ast.walk(t)):
                            prune = True
                        if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) \
                                and isinstance(x.func.value, ast.Name) and \
                                x.func.value.id == dn and x.func.attr in (
                                    'remove', 'clear', 'pop'):
                            prune = True
                if prune and self._prune_keeps(body, dn):
                    m.site(call.lineno, 'INERT', 'walk-prune-keeps-numbers',
                           m.seg(call)[:60])
                elif prune:
                    self._broad(call, 'walk-pruning', None)
                else:
                    m.site(call.lineno, 'INERT', 'walk-recursive', m.seg(call)[:60])
                continue
            if isinstance(p, (ast.For, ast.comprehension)) and p.iter is top:
                t = p.target
                if not isinstance(t, ast.Name):
                    self._enum_unknown(call, 'listing loop target')
                    continue
                body = p if isinstance(p, ast.For) else m.par.get(p)
                preds = self._preds_on(body, t.id)
                if self._sn_only(preds):
                    self._repoint_listing(call, p, t, done=done_e1)
                    continue
                if done_e1:
                    m.site(call.lineno, 'DONE', 'E1?')
                    continue
                if not self._reaches_sn(preds):
                    m.site(call.lineno, 'INERT', 'enum-cannot-reach',
                           str(preds)[:100])
                    continue
                self._broad(call, 'listdir', preds)
                continue
            if isinstance(p, (ast.Assign,)):
                tg = self._target(p)
                if tg is not None:
                    preds = self._preds_on(m.scope_of(p) or m.tree, tg.id)
                    # names filtered later by comprehension over tg
                    if not self._reaches_sn(preds):
                        m.site(call.lineno, 'INERT', 'enum-cannot-reach',
                               str(preds)[:100])
                        continue
                    self._broad(call, 'listdir-assigned', preds)
                    continue
            if isinstance(p, ast.Compare):
                # `'x' in os.listdir(D)` -- a membership test on one name
                lits = [x.value for x in ast.walk(p) if isinstance(x, ast.Constant)
                        and isinstance(x.value, str)]
                if lits and not any(SN in l for l in lits):
                    m.site(call.lineno, 'INERT', 'enum-membership', str(lits)[:60])
                    continue
            self._broad(call, 'listdir-other', None)

    def _computed_pattern(self, call, arg):
        """A glob whose pattern is computed.  Safe if (a) it is a parameter
        of a local function whose every caller passes a literal (the macro
        ones are prefixed at the call site by P1h), or (b) its literal tail
        cannot match a macro file (another extension, or a sub-path)."""
        import fnmatch
        m = self.m
        last = arg.args[-1] if isinstance(arg, ast.Call) and dotted(
            arg.func) in JOIN else arg
        if isinstance(last, ast.Name):
            fn = m.scope_of(call)
            if isinstance(fn, ast.FunctionDef) and last.id in [
                    a.arg for a in fn.args.args]:
                i = [a.arg for a in fn.args.args].index(last.id)
                calls = [c for c in ast.walk(m.tree) if isinstance(c, ast.Call)
                         and dotted(c.func) == fn.name]
                lits = []
                for c in calls:
                    if len(c.args) <= i:
                        continue
                    a_ = c.args[i]
                    if isinstance(a_, ast.Constant):
                        lits.append(a_.value)
                    elif isinstance(a_, ast.Call) and dotted(a_.func) in JOIN \
                            and all(isinstance(x, ast.Constant) for x in a_.args):
                        lits.append('/'.join(x.value for x in a_.args))
                if calls and len(lits) == len(calls):
                    for lv in lits:
                        if SN in lv:
                            continue
                        if any(fnmatch.fnmatchcase(pr, lv) for pr in PROBES):
                            self._broad(call, 'glob-param', lv)
                    m.site(call.lineno, 'INERT', 'glob-param-literals',
                           str(lits)[:80])
                    return True
            return None
        consts = [x.value for x in ast.walk(arg) if isinstance(x, ast.Constant)
                  and isinstance(x.value, str)]
        if consts:
            tail = consts[-1]
            if re.search(r'\.(npz|json|csv|npy|fits|txt|pdf|png|py)$', tail) or \
                    '/*/' in ''.join(consts):
                m.site(call.lineno, 'INERT', 'enum-cannot-reach', tail)
                return True
        return None

    def _prune_keeps(self, body, dn):
        """Every `dn[:] = [d for d in dn if COND]` keeps 'numbers'?  COND is
        evaluated with d='numbers' and module-level literal constants."""
        m = self.m
        found = False
        for x in ast.walk(body):
            if not (isinstance(x, ast.Assign) and isinstance(x.targets[0],
                                                             ast.Subscript)
                    and isinstance(x.targets[0].value, ast.Name)
                    and x.targets[0].value.id == dn
                    and isinstance(x.value, ast.ListComp)):
                if isinstance(x, (ast.Delete, ast.AugAssign)):
                    return False
                continue
            found = True
            comp = x.value
            g = comp.generators[0]
            if not isinstance(g.target, ast.Name):
                return False
            env = {g.target.id: SUB}
            for nm in {n.id for c in g.ifs for n in ast.walk(c)
                       if isinstance(n, ast.Name)} - {g.target.id}:
                vals = self._values_of(next(n for c in g.ifs for n in ast.walk(c)
                                            if isinstance(n, ast.Name)
                                            and n.id == nm))
                if not vals or len(vals) != 1:
                    return False
                try:
                    env[nm] = ast.literal_eval(vals[0])
                except Exception:
                    return False
            for c in g.ifs:
                try:
                    if not eval(compile(ast.Expression(c), '<prune>', 'eval'),
                                {'__builtins__': {}}, env):
                        return False
                except Exception:
                    return False
        return found

    def _enum_unknown(self, call, why):
        self.m.unk(call, 'enumeration: ' + why)

    def _is_e2_done(self, call):
        m = self.m
        p = m.par.get(call)
        # [_e for _e in os.listdir(D) if _e != 'numbers']
        if isinstance(p, ast.comprehension) and any(
                isinstance(x, ast.Constant) and x.value == SUB
                for c in p.ifs for x in ast.walk(c)):
            return True
        # os.listdir(os.path.join(D, 'numbers')) inside the view / an E2g glob
        q = call
        for _ in range(6):
            q = m.par.get(q)
            if q is None:
                break
            if isinstance(q, ast.BinOp) and isinstance(q.op, ast.Add) and any(
                    isinstance(x, ast.Constant) and x.value in (SUB,) or
                    isinstance(x, ast.Constant) and isinstance(x.value, str)
                    and x.value.startswith(SUB + '/')
                    for x in ast.walk(q.right)) and any(
                    x is call for x in ast.walk(q)):
                return True
        return False

    def _repoint_listing(self, call, loop, tgt, done=False):
        """E1: the consumer admits only macro files -> list D/numbers."""
        m = self.m
        if done:
            pass
        elif call.args:
            a, b = m.span(call.args[0])
            m.edit(a, a, 'os.path.join(', 'E1', call.lineno)
            m.edit(b, b, ", '%s')" % SUB, 'E1', call.lineno)
        else:
            a, b = m.span(call)
            m.edit(b - 1, b - 1, "'%s'" % SUB, 'E1', call.lineno)
        m.site(call.lineno, 'DONE' if done else 'ENUM', 'E1', m.seg(call)[:80])
        sc = self.binding_scope(tgt, tgt.id)
        if isinstance(loop, ast.For):
            self.flow_loop(loop, 'E1', 0)
        else:
            self.var(tgt.id, sc, 'E1')
        # the comprehension's value flows on as a container of names
        if isinstance(loop, ast.comprehension):
            comp = m.par.get(loop)
            if isinstance(comp, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) \
                    and isinstance(comp.elt, ast.Name) and comp.elt.id == tgt.id:
                self.flow_container(comp, comp, 'E1c', 0) if False else \
                    self._flow_value(comp, 'E1c')

    def _flow_value(self, node, why):
        """A container-of-names VALUE: follow it to its holder."""
        m = self.m
        top = node
        while isinstance(m.par.get(top), ast.Call) and dotted(
                m.par[top].func) in ('sorted', 'list', 'set', 'tuple'):
            top = m.par[top]
        p = m.par.get(top)
        if isinstance(p, (ast.Assign, ast.AnnAssign)):
            return self.flow_assign(top, p, why, 0)
        if isinstance(p, (ast.For, ast.comprehension)) and p.iter is top:
            return self.flow_loop(p, why, 0)
        if isinstance(p, ast.Return):
            return self.flow_return(top, why, 0)
        if isinstance(p, (ast.BinOp,)):
            return self._flow_value(p, why)
        if isinstance(p, ast.Compare) or (isinstance(p, ast.Call) and
                                          dotted(p.func) in TEXTF | {'len'}):
            m.site(node.lineno, 'INERT', 'name-set', '')
            return True
        m.unk(node, 'names value held by %s' % type(p).__name__)
        return False

    def _broad(self, call, kind, info):
        """A broad enumeration that can reach macro files.  Handled only by
        the idiom rules F1/E2; anything else is UNCLASSIFIED."""
        m = self.m
        if self._farm(call):
            return
        if self._is_allowlist_listing(call):
            self.m.site(call.lineno, 'INERT', 'allowlist-gate', self.m.seg(call)[:60])
            return
        why = self._consumer_unsafe(call)
        if why:
            self.broad.append((call.lineno, kind, self.m.seg(call)[:100],
                               'consumer: ' + why))
            return
        if kind == 'glob' and self._widen_glob(call):
            return
        if kind in ('listdir', 'listdir-assigned', 'listdir-other'):
            if self._widen_listdir(call, '%s %s' % (kind, str(info)[:60])):
                return
        self.broad.append((call.lineno, kind, m.seg(call)[:100], str(info)[:100]))

    def _farm(self, call):
        """F1 / copy-all: a listing used to replicate the whole root."""
        m = self.m
        st = m.stmt_of(call)
        loop = st if isinstance(st, ast.For) and st.iter is not None and \
            any(x is call for x in ast.walk(st.iter)) else None
        txt = m.seg(st) if st is not None else ''
        if loop is not None and 'os.symlink' in txt:
            return self._farm_symlink(call, loop)
        if re.search(r"['\"]cp['\"]\s*,\s*['\"]-a['\"]|copytree", txt):
            m.site(call.lineno, 'INERT', 'copy-all', txt[:80])
            return True
        return False

    def _farm_symlink(self, call, loop):
        """F1: `for f in os.listdir(R): os.symlink(join(R, f), join(d, f))`
        would link numbers/ AS A DIRECTORY, and a write into the farm's
        numbers/ would land in the real tree.  Append a block that replaces
        the directory link by a real directory of per-file links."""
        m = self.m
        syms = [n for n in ast.walk(loop) if isinstance(n, ast.Call)
                and dotted(n.func) == 'os.symlink']
        if len(syms) != 1 or not call.args:
            m.unk(call, 'symlink farm of unknown shape')
            return True
        R = m.seg(call.args[0])
        # destination root: the first arg of the join building dst
        dstv = syms[0].args[1]
        dexpr = None
        if isinstance(dstv, ast.Name):
            for v in self._values_of(dstv) or []:
                if isinstance(v, ast.Call) and dotted(v.func) in JOIN:
                    dexpr = m.seg(v.args[0])
        elif isinstance(dstv, ast.Call) and dotted(dstv.func) in JOIN:
            dexpr = m.seg(dstv.args[0])
        if dexpr is None:
            m.unk(call, 'symlink farm: destination root not resolved')
            return True
        if b'r28-numbers F1' in m.raw[m.span(loop)[1]:m.span(loop)[1] + 200]:
            m.site(call.lineno, 'DONE', 'F1')
            return True
        ind = ' ' * loop.col_offset
        block = (
            "\n{i}# r28-numbers F1: numbers/ must be a REAL directory in the farm\n"
            "{i}# (a link to the directory would let a write go through it)\n"
            "{i}_nmd = os.path.join({d}, '{s}')\n"
            "{i}if os.path.islink(_nmd):\n"
            "{i}    os.remove(_nmd)\n"
            "{i}    os.mkdir(_nmd)\n"
            "{i}    for _nmf in os.listdir(os.path.join({r}, '{s}')):\n"
            "{i}        os.symlink(os.path.join({r}, '{s}', _nmf),\n"
            "{i}                   os.path.join(_nmd, _nmf))").format(
                i=ind, d=dexpr, r=R, s=SUB)
        b = m.span(loop)[1]
        m.edit(b, b, block, 'F1', loop.lineno)
        m.site(loop.lineno, 'FARM', 'F1', m.seg(call)[:60])
        return True

    def _consumer_unsafe(self, call):
        """E2 changes each moved entry from 'f' to 'numbers/f' (a listing)
        or 'D/f' to 'D/numbers/f' (a glob).  Safe only for consumers that
        use an entry as a PATH, test it by suffix/substring/content, count
        it, or print it.  Returns a reason if not, else ''."""
        return self._value_unsafe(call, 0)

    def _value_unsafe(self, node, depth):
        m = self.m
        if depth > 4:
            return 'too deep'
        top = node
        while True:
            q = m.par.get(top)
            if isinstance(q, ast.Call) and dotted(q.func) in (
                    'sorted', 'list', 'set', 'tuple') and top in q.args:
                top = q
                continue
            if isinstance(q, ast.BinOp) and isinstance(q.op, ast.Add):
                top = q
                continue
            break
        p = m.par.get(top)
        if isinstance(p, ast.Call) and dotted(p.func) == 'len':
            return ''
        if isinstance(p, ast.Return):
            return 'returned'
        if isinstance(p, ast.Assign) and self._target(p) is not None:
            tg = self._target(p)
            sc = self.binding_scope(tg, tg.id)
            for u in self.uses_of(tg.id, sc):
                k, inf = self.context(u)
                if k == 'NAMEOP' and isinstance(inf, ast.Call) and \
                        dotted(inf.func) == 'len':
                    continue
                if k == 'TEXT':
                    continue
                pp = m.par.get(u)
                if isinstance(pp, (ast.For, ast.comprehension)) and pp.iter is u:
                    r = self._loop_unsafe(pp)
                    if r:
                        return r
                    continue
                r = self._value_unsafe(u, depth + 1)
                if r:
                    return '%s via %s' % (r, tg.id)
            return ''
        if not (isinstance(p, (ast.For, ast.comprehension)) and p.iter is top
                and isinstance(p.target, ast.Name)):
            return 'not iterated (%s)' % type(p).__name__
        return self._loop_unsafe(p)

    def _loop_unsafe(self, p):
        m = self.m
        if not isinstance(p.target, ast.Name):
            return 'tuple loop target'
        t = p.target.id
        body = p if isinstance(p, ast.For) else m.par.get(p)
        for u in [n for n in ast.walk(body) if isinstance(n, ast.Name)
                  and n.id == t and isinstance(n.ctx, ast.Load)]:
            kind, info = self.context(u)
            if kind in ('PATHJOIN', 'PATHARG', 'TEXT', 'NAMEOP'):
                if kind == 'NAMEOP' and isinstance(info, ast.Call) and \
                        dotted(info.func) in ('os.path.splitext',):
                    return 'splitext'
                continue
            if kind == 'NAMEPRED':
                a = info
                if isinstance(a, ast.Attribute) and isinstance(m.par.get(a), ast.Call):
                    a = m.par[a]
                if isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute) \
                        and a.func.attr == 'startswith':
                    lits = [x.value for x in ast.walk(a) if isinstance(
                        x, ast.Constant) and isinstance(x.value, str)]
                    if any(SN.startswith(l) or l.startswith('s') for l in lits):
                        return 'startswith %r' % lits
                continue
            if kind == 'COMPARE':
                c = info
                if len(c.ops) == 1 and isinstance(c.ops[0], (ast.In, ast.NotIn)) \
                        and c.comparators[0] is u and isinstance(
                            c.left, ast.Constant):
                    continue                    # substring test
                other = [x for x in [c.left] + c.comparators if x is not u]
                if all(self._non_sn_value(x) for x in other):
                    continue                    # never equal to a macro name
                if all(isinstance(x, ast.Name) and (self._is_p1cont(x) or
                                                    self._input_targets(x))
                       for x in other):
                    continue                    # both sides carry numbers/
                if self._allowlist_gate(c):
                    continue
                if len(c.ops) == 1 and isinstance(c.ops[0], (ast.In, ast.NotIn)) \
                        and c.left is u and isinstance(c.comparators[0], ast.Name) \
                        and self._text_var(c.comparators[0]):
                    continue                    # a mention test in a text
                return 'compared as a name: %s' % m.seg(c)[:60]
            if kind == 'CONTAINER' and isinstance(m.par.get(u), ast.Tuple):
                continue                        # a report record
            if kind == 'SUBSCRIPT':
                continue                        # a path used as a dict key
            if kind == 'COMPVALUE':
                comp = info
                if isinstance(comp, (ast.ListComp, ast.GeneratorExp)) and \
                        comp is body:
                    continue                    # the filtered listing itself
                return 'collected into %s' % type(comp).__name__
            return '%s %s' % (kind, m.seg(u.__dict__.get('_p', u))[:40])
        return ''

    def _text_var(self, nm):
        """A comprehension variable over <dict>.items()/.values() of file
        texts (`any(f in s for p, s in pysrc.items())`)."""
        m = self.m
        p = m.par.get(nm)
        while p is not None and not isinstance(p, (ast.GeneratorExp,
                                                   ast.ListComp)):
            p = m.par.get(p)
        if p is None:
            return False
        for g in p.generators:
            names = [x.id for x in ast.walk(g.target) if isinstance(x, ast.Name)]
            if nm.id in names and isinstance(g.iter, ast.Call) and \
                    isinstance(g.iter.func, ast.Attribute) and \
                    g.iter.func.attr in ('items', 'values'):
                return True
        return False

    def _is_allowlist_listing(self, call):
        m = self.m
        st = m.stmt_of(call)
        if not isinstance(st, ast.For) or not isinstance(st.target, ast.Name):
            return False
        for n in ast.walk(st):
            if isinstance(n, ast.Compare) and n.left is not None and \
                    isinstance(n.left, ast.Name) and n.left.id == st.target.id \
                    and self._allowlist_gate(n):
                return True
        return False

    def _allowlist_gate(self, c):
        """`if n not in allowed: bad.append(...)` -- every entry outside an
        allowlist FAILS the check, so on a green tree the directory holds no
        macro file (they are never on any allowlist of names)."""
        m = self.m
        if not (len(c.ops) == 1 and isinstance(c.ops[0], ast.NotIn)):
            return False
        st = m.par.get(c)
        if not isinstance(st, ast.If) or st.test is not c:
            return False
        return any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                   and x.func.attr == 'append' and isinstance(x.func.value, ast.Name)
                   and x.func.value.id in ('bad', 'fails', 'errors', 'problems')
                   for b in st.body for x in ast.walk(b))

    def _input_targets(self, nm):
        """A Name bound to the manuscript's \\input targets AS WRITTEN
        (a generic capture), which carry numbers/ after T1 exactly as the
        widened listing's entries do."""
        for v in self._values_of(nm) or []:
            for x in ast.walk(v):
                if isinstance(x, ast.Constant) and isinstance(x.value, str) and \
                        'input' in x.value and re.search(r'\(\[\^\}\]', x.value):
                    return True
        return False

    def _is_p1cont(self, nm):
        return (id(self.binding_scope(nm, nm.id)), nm.id) in self.p1cont

    def _holder(self, node):
        """The Name a (sorted/filtered) value is assigned to, or None."""
        m = self.m
        top = node
        while True:
            q = m.par.get(top)
            if isinstance(q, ast.comprehension) and q.iter is top:
                top = m.par.get(q)
                continue
            if isinstance(q, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) and \
                    q.elt is top:
                top = q
                continue
            if isinstance(q, ast.Call) and dotted(q.func) in (
                    'sorted', 'list', 'set', 'tuple') and top in q.args:
                top = q
                continue
            break
        q = m.par.get(top)
        if isinstance(q, ast.Assign) and self._target(q) is not None:
            return self._target(q)
        return None

    def _decide_glob(self, c, gcall):
        """P1g: name semantics if the holder is compared with macro NAMES
        (an \\input capture, a literal name), else path semantics."""
        m = self.m
        if m.seg(gcall).startswith('[os.path.basename(_p) for _p in '):
            return
        h = self._holder(gcall)
        name_partner = False
        if h is not None:
            sc = self.binding_scope(h, h.id)
            for u in self.uses_of(h.id, sc):
                cmp_ = m.par.get(u)
                if isinstance(cmp_, ast.Compare) and u in cmp_.comparators:
                    x = cmp_.left
                    if isinstance(x, ast.Name) and (
                            id(self.binding_scope(x, x.id)), x.id) in self.vmode:
                        name_partner = True
                    if isinstance(x, ast.Constant) and isinstance(x.value, str) \
                            and SN in x.value:
                        name_partner = True
        if name_partner:
            a, b = m.span(gcall)
            pat = m.seg(c)
            q = pat[0] if pat[0] in '\'"' else pat[1]
            i = pat.find(SN)
            newpat = pat[:i] + SUB + '/' + pat[i:]
            m.edit(a, b, '[os.path.basename(_p) for _p in %s(%s)]' % (
                dotted(gcall.func), newpat), 'P1g-name', c.lineno)
            m.site(c.lineno, 'PATH', 'P1g-name', h.id)
            self.var(h.id, self.binding_scope(h, h.id), 'P1g')
            return
        prefix_literal(m, c, 'P1')
        m.site(c.lineno, 'PATH', 'P1g-path', m.seg(c))
        self.p1_container(c)

    def p1cont_done(self, c):
        st = self.m.stmt_of(c)
        if isinstance(st, ast.Assign) and self._target(st) is not None:
            tg = self._target(st)
            self.p1cont.add((id(self.binding_scope(tg, tg.id)), tg.id))

    def p1_container(self, c):
        """After P1 on a GLOB pattern: record the variable holding the
        results; a basename compared against it must compare basenames."""
        m = self.m
        q = c
        while True:
            pq = m.par.get(q)
            if pq is None or isinstance(pq, ast.stmt):
                break
            q = pq
        st = m.par.get(q) if not isinstance(q, ast.stmt) else q
        st = q if isinstance(q, ast.Assign) else m.stmt_of(c)
        if not isinstance(st, ast.Assign) or self._target(st) is None:
            return
        tg = self._target(st)
        sc = self.binding_scope(tg, tg.id)
        self.p1cont.add((id(sc), tg.id))
        for u in self.uses_of(tg.id, sc):
            cmp_ = m.par.get(u)
            if isinstance(cmp_, ast.Compare) and u in cmp_.comparators and \
                    len(cmp_.ops) == 1 and isinstance(cmp_.ops[0], (ast.In,
                                                                   ast.NotIn)) \
                    and isinstance(cmp_.left, ast.Call) and \
                    dotted(cmp_.left.func) == 'os.path.basename':
                a, b = m.span(u)
                m.edit(a, b, '{os.path.basename(_x) for _x in %s}' % tg.id,
                       'P1b', u.lineno)
                m.site(u.lineno, 'PATH', 'P1b', m.seg(cmp_)[:80])

    def _non_sn_value(self, x):
        """An expression that can never equal a macro-file name: a literal
        (or tuple/set of literals) without survey_numbers, or a Name bound
        only to such literals or to a technosignatures_* manuscript name."""
        if isinstance(x, ast.Constant):
            return not (isinstance(x.value, str) and SN in x.value)
        if isinstance(x, (ast.Tuple, ast.Set, ast.List)):
            return all(self._non_sn_value(e) for e in x.elts)
        if isinstance(x, ast.Name):
            vals = self._values_of(x)
            if vals:
                return all(self._non_sn_value(v) or (
                    isinstance(v, ast.Call) and 'main_file' in dotted(v.func))
                    for v in vals)
        return False

    def _premove_view(self, dexpr):
        return ("([_e for _e in os.listdir({d}) if _e != '{s}'] + "
                "[os.path.join('{s}', _e) for _e in (os.listdir(os.path.join("
                "{d}, '{s}')) if os.path.isdir(os.path.join({d}, '{s}')) "
                "else [])])").format(d=dexpr, s=SUB)

    def add_sort_key(self, srt, keytext, rule):
        """Append `, key=...` to a sorted() call.  A bare generator argument
        (`sorted(x for x in y)`) shares the call's parentheses and must be
        parenthesised first."""
        m = self.m
        b = m.span(srt)[1] - 1
        a0 = srt.args[0]
        if isinstance(a0, ast.GeneratorExp) and len(srt.args) == 1 and \
                m.span(a0)[0] == m.span(srt.func)[1]:
            m.edit(m.span(a0)[0] + 1, m.span(a0)[0] + 1, '(', rule, srt.lineno)
            m.edit(b, b, ')' + keytext, rule, srt.lineno)
        else:
            m.edit(b, b, keytext, rule, srt.lineno)

    def _sorted_key(self, call, rule):
        """If the widened listing is wrapped in sorted() without a key,
        sort by basename: the pre-move order of the names."""
        m = self.m
        p = m.par.get(call)
        if isinstance(p, ast.Call) and dotted(p.func) == 'sorted' and \
                p.args and p.args[0] is call:
            if not p.keywords:
                self.add_sort_key(p, ', key=os.path.basename', rule)
            return True
        return False

    def _widen_listdir(self, call, why):
        """E2: a broad listing of a root sees the PRE-MOVE VIEW: the root's
        entries other than numbers/, plus 'numbers/<f>' for each moved file.
        Paths built as join(D, entry) stay right; names keep their order."""
        m = self.m
        if not call.args or not m.imports_os:
            m.unk(call, 'E2 listing without an argument / without `import os`')
            return True
        d = m.seg(call.args[0])
        if '\n' in d or len(d) > 60:
            m.unk(call, 'E2 listing of a complex directory expression')
            return True
        a, b = m.span(call)
        m.edit(a, b, self._premove_view(d), 'E2', call.lineno)
        self._sorted_key(call, 'E2')
        m.site(call.lineno, 'ENUM', 'E2', why)
        return True

    def _widen_glob(self, call):
        m = self.m
        arg = call.args[0] if call.args else None
        if arg is None:
            return False
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            pat = arg.value
            alt = repr(SUB + '/' + pat)
        elif isinstance(arg, ast.Call) and dotted(arg.func) in JOIN and \
                isinstance(arg.args[-1], ast.Constant):
            pat = arg.args[-1].value
            parts = [m.seg(x) for x in arg.args[:-1]]
            alt = '%s(%s, %r, %r)' % (dotted(arg.func), ', '.join(parts), SUB, pat)
        else:
            return False
        if not re.fullmatch(r'\*\.[a-z]+|\*_drive\*(\.[a-z]+)?', pat):
            return False
        a, b = m.span(call)
        new = '(%s + %s(%s))' % (m.seg(call), dotted(call.func), alt)
        p = m.par.get(call)
        if isinstance(p, ast.comprehension) and p.iter is call:
            comp = m.par.get(p)
            el = getattr(comp, 'elt', None)
            if isinstance(el, ast.Call) and dotted(el.func) == 'os.path.basename' \
                    and isinstance(arg, ast.Call):
                # E2g-b: names made by basename() lose the subdirectory; the
                # relative path keeps it (and equals the basename at the root)
                ea, eb = m.span(el)
                m.edit(ea, eb, 'os.path.relpath(%s, %s)' % (
                    m.seg(el.args[0]), m.seg(arg.args[0])), 'E2g-b', el.lineno)
                q = comp
                while isinstance(m.par.get(q), (ast.BinOp, ast.List)):
                    q = m.par[q]
                srt = m.par.get(q)
                if isinstance(srt, ast.Call) and dotted(srt.func) == 'sorted' \
                        and not srt.keywords:
                    self.add_sort_key(srt, ", key=lambda _p: _p[%d:] if "
                                      "_p.startswith('%s/') else _p"
                                      % (len(SUB) + 1, SUB), 'E2g-b')
        m.edit(a, b, new, 'E2g', call.lineno)
        self._sorted_key(call, 'E2g')
        m.site(call.lineno, 'ENUM', 'E2g', pat)
        return True

    # ------------------------------------------------------------------
    def run(self):
        m = self.m
        self.vmode, self.fret, self.seen, self.broad = {}, set(), set(), []
        self.deferred = []
        self.mkd = set()
        self.p1cont = set()
        self.pending_glob = []
        # comments (tokenizer): inert
        try:
            for tok in tokenize.tokenize(io.BytesIO(m.raw).readline):
                if tok.type == tokenize.COMMENT and SN in tok.string:
                    m.site(tok.start[0], 'INERT', 'comment')
        except tokenize.TokenError:
            pass
        for c in sorted([n for n in ast.walk(m.tree) if isinstance(n, ast.Constant)
                         and isinstance(n.value, str) and SN in n.value],
                        key=lambda n: (n.lineno, n.col_offset)):
            self.literal(c)
        for c, gcall in self.pending_glob:
            self._decide_glob(c, gcall)
        self.enumerations()
        self.generic_inputs()
        self.scratch()
        for fn, idx, calls in self.deferred:
            for c in calls:
                if len(c.args) <= idx:
                    continue
                a_ = c.args[idx]
                if self.sn_literal_expr(a_) is not None:
                    continue
                if isinstance(a_, ast.Name) and (id(self.binding_scope(
                        a_, a_.id)), a_.id) in self.vmode:
                    continue
                m.unk(c, 'helper %s repointed inside, but this caller passes '
                      '%s' % (fn.name, m.seg(a_)[:60]))
        for ln, kind, seg, info in self.broad:
            m.unclassified.append((ln, 'BROAD %s enumeration can reach macro '
                                   'files (%s)' % (kind, info), seg))

    def scratch(self):
        """F2 / W1: directories that stand in for the build root."""
        m = self.m
        stmts = [n for n in ast.walk(m.tree) if isinstance(n, ast.Expr)
                 and isinstance(n.value, ast.Call)
                 and dotted(n.value.func) in ('os.makedirs', '_os.makedirs')]
        roots_with_sn = self._sn_roots()
        for st in stmts:
            call = st.value
            a0 = call.args[0] if call.args else None
            # F2: makedirs(join(D, 'figures')) -- a scratch made to look like
            # the build root; numbers/ is part of that look now
            if isinstance(a0, ast.Call) and dotted(a0.func) in JOIN and \
                    len(a0.args) == 2 and isinstance(a0.args[1], ast.Constant) \
                    and a0.args[1].value == 'figures' and \
                    m.seg(a0.args[0]) not in ('HERE', 'here', "'.'"):
                self._add_makedirs(st, m.seg(a0.args[0]), 'F2')
            # W1: makedirs(OUTDIR) in a generator whose macro output is
            # rooted on OUTDIR
            elif isinstance(a0, (ast.Name, ast.Attribute)) and \
                    m.seg(a0) in roots_with_sn:
                self._add_makedirs(st, m.seg(a0), 'W1')
        # F2b: a mkdtemp() directory handed to a generator as --out/--outdir
        for lst in [n for n in ast.walk(m.tree) if isinstance(n, ast.List)]:
            el = lst.elts
            for k, e in enumerate(el[:-1]):
                if isinstance(e, ast.Constant) and e.value in ('--out',
                                                              '--outdir'):
                    self._f2b(el[k + 1], lst)

    def _sn_roots(self):
        """Root expressions of joins that now carry the subdirectory."""
        m = self.m
        out = set()
        for (a, b, new, rule, line) in m.edits:
            pass
        for n in ast.walk(m.tree):
            if isinstance(n, ast.Call) and dotted(n.func) in JOIN and \
                    len(n.args) >= 2:
                lit = [x for a in n.args[1:] for x in ast.walk(a)
                       if isinstance(x, ast.Constant)
                       and isinstance(x.value, str) and SN in x.value]
                via = False
                fn = m.scope_of(n)
                if isinstance(fn, ast.FunctionDef) and any(
                        isinstance(a, ast.Name) and self.vmode.get(
                            ('param', fn.name, a.id)) == 'path'
                        for a in n.args[1:]):
                    via = True
                if (lit or via) and m.seg(n.args[0]) not in ('HERE', "'.'",
                                                            'here'):
                    out.add(m.seg(n.args[0]))
        # helper `out(name)` = join(OUTDIR, name) with a prefixed call
        return out

    def _add_makedirs(self, st, rootexpr, rule):
        m = self.m
        key = (id(m.scope_of(st)), rootexpr)
        if key in self.mkd:
            return
        self.mkd.add(key)
        line = "os.makedirs(os.path.join(%s, '%s'), exist_ok=True)" % (
            rootexpr, SUB)
        nxt = m.raw[m.span(st)[1]:m.span(st)[1] + 300].decode('utf-8', 'replace')
        if line in nxt.split('\n', 2)[1:2] or line in m.src:
            m.site(st.lineno, 'DONE', rule)
            return
        b = m.span(st)[1]
        m.edit(b, b, '\n' + ' ' * st.col_offset + line + '  # r28-numbers ' + rule,
               rule, st.lineno)
        m.site(st.lineno, 'SCRATCH', rule, rootexpr)

    def _f2b(self, arg, lst):
        m = self.m
        if not isinstance(arg, ast.Name):
            return
        cands = []
        fn = m.scope_of(lst)
        if isinstance(fn, ast.FunctionDef) and arg.id in [a.arg for a in fn.args.args]:
            i = [a.arg for a in fn.args.args].index(arg.id)
            for c in ast.walk(m.tree):
                if isinstance(c, ast.Call) and dotted(c.func) == fn.name and \
                        len(c.args) > i and isinstance(c.args[i], ast.Name):
                    cands.append(c.args[i])
        else:
            cands.append(arg)
        for nm in cands:
            for v in self._values_of(nm) or []:
                if isinstance(v, ast.Call) and dotted(v.func).endswith('mkdtemp'):
                    st = m.par.get(v)
                    self._add_makedirs(st, nm.id, 'F2b')


# ==========================================================================
def build_root(tree):
    tree = os.path.abspath(tree)
    return os.path.join(tree, 'chain') if os.path.isdir(
        os.path.join(tree, 'chain')) else tree


def live_files(root):
    out = []
    for dp, dns, fns in os.walk(root):
        rel = os.path.relpath(dp, root)
        top = rel.split(os.sep)[0]
        if top in DEAD_DIRS or top in DEPOSIT_DIRS:
            dns[:] = []
            continue
        dns[:] = sorted(d for d in dns if d not in DEAD_DIRS and
                        not (dp == root and d in DEPOSIT_DIRS))
        for fn in sorted(fns):
            if dp == root and fn in SELF:
                continue
            out.append(os.path.relpath(os.path.join(dp, fn), root))
    return out


SH_TOKEN = re.compile(r'(?<![/\w])(survey_numbers[A-Za-z0-9_${}*?.\[\]-]*)')


def shell_edits(text):
    """S1: repoint macro-file operands outside comments.  Returns
    (new_text, sites, unclassified)."""
    out, sites, unk = [], [], []
    for i, line in enumerate(text.split('\n'), 1):
        code, cmt = _split_sh_comment(line)
        if SN not in code:
            if SN in cmt:
                sites.append((i, 'INERT', 'sh-comment', ''))
            out.append(line)
            continue
        if re.match(r'\s*(rm|cp|ls|test|\[|cat|mv)\b', code) or \
                re.search(r'\brm -f\b', code):
            new = SH_TOKEN.sub(lambda mm: SUB + '/' + mm.group(1), code)
            sites.append((i, 'PATH', 'S1', code.strip()[:100]))
            out.append(new + cmt)
            continue
        if re.search(r'(?:^|/|\s)numbers/survey_numbers', code):
            sites.append((i, 'DONE', 'S1', ''))
            out.append(line)
            continue
        if re.search(r'\becho\b|\bprint', code):
            sites.append((i, 'INERT', 'sh-text', code.strip()[:100]))
            out.append(line)
            continue
        unk.append((i, 'shell reference', code.strip()[:150]))
        out.append(line)
    return '\n'.join(out), sites, unk


def _split_sh_comment(line):
    q = None
    for j, ch in enumerate(line):
        if q:
            if ch == q:
                q = None
            continue
        if ch in '\'"':
            q = ch
        elif ch == '#' and (j == 0 or line[j - 1] in ' \t;') and \
                not line[max(0, j - 1):j + 1] == '$#':
            return line[:j], line[j:]
    return line, ''


TEX_INPUT = re.compile(r'(\\input\{)(survey_numbers[A-Za-z0-9_]*\})')


def tex_edits(text):
    n = len(TEX_INPUT.findall(text))
    other = len(re.findall(SN, text)) - n - len(
        re.findall(r'\\input\{%s/survey_numbers' % SUB, text))
    return TEX_INPUT.sub(r'\1%s/\2' % SUB, text), n, other


def scan(root, verbose=False):
    """Classify everything; return (edits by file, report dict)."""
    rep = {'py': {}, 'sh': {}, 'tex': {}, 'data': {}, 'unclassified': []}
    edits = {}
    for rel in live_files(root):
        p = os.path.join(root, rel)
        if rel.endswith('.py'):
            try:
                m = Mod(p, rel)
            except SyntaxError as e:
                if SN in open(p, errors='ignore').read():
                    rep['unclassified'].append((rel, 0, 'SyntaxError', str(e)))
                continue
            if SN not in m.src and not re.search(
                    r'listdir|scandir|glob|walk|symlink|mkdtemp', m.src):
                continue
            an = Analyzer(m, None)
            an.run()
            if m.edits:
                edits[rel] = m.edits
            if m.sites:
                rep['py'][rel] = m.sites
            for u in m.unclassified:
                rep['unclassified'].append((rel,) + u)
        elif rel.endswith('.sh'):
            t = open(p).read()
            if SN not in t:
                continue
            new, sites, unk = shell_edits(t)
            rep['sh'][rel] = sites
            if new != t:
                edits[rel] = new
            for u in unk:
                rep['unclassified'].append((rel,) + u)
        elif rel.endswith('.tex') and ('/' not in rel or rel.startswith('sections/')):
            t = open(p, errors='replace').read()
            if SN not in t or MACRO_FILE.match(os.path.basename(rel)):
                continue
            new, n, other = tex_edits(t)
            rep['tex'][rel] = (n, other)
            if new != t:
                edits[rel] = new
            if other and not rel.startswith('sections/') and \
                    not re.match(r'technosignatures_', rel):
                pass
        else:
            if MACRO_FILE.match(os.path.basename(rel)) or DRIVE.search(rel):
                continue
            try:
                t = open(p, errors='strict').read()
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            if SN not in t:
                continue
            # a data file whose VALUE is exactly a macro-file name could be a
            # path list some code reads: refuse; prose mentions are inert
            vals = re.findall(r'["\'](survey_numbers[A-Za-z0-9_]*(?:\.tex)?)["\']', t)
            rep['data'][rel] = len(re.findall(SN, t))
            if vals and rel.endswith('.json'):
                rep['unclassified'].append(
                    (rel, 0, 'data file holds macro-file names as values', str(vals[:3])))
    return edits, rep


# ==========================================================================
def apply_bytes(raw, edits):
    """Apply (start, end, new, rule, line) edits; overlapping edits refuse."""
    edits = sorted(set((a, b, n) for a, b, n, _, _ in edits),
                   key=lambda e: (e[0], e[1]))
    out, pos = [], 0
    for a, b, n in edits:
        if a < pos:
            raise SystemExit('numbers_move: overlapping edits at byte %d' % a)
        out.append(raw[pos:a])
        out.append(n)
        pos = b
    out.append(raw[pos:])
    return b''.join(out)


def summarise(rep):
    from collections import Counter
    c = Counter()
    for rel, sites in rep['py'].items():
        for s in sites:
            c[('py', s[1], s[2])] += 1
    for rel, sites in rep['sh'].items():
        for s in sites:
            c[('sh', s[1], s[2])] += 1
    for rel, (n, o) in rep['tex'].items():
        c[('tex', 'TEX', 'T1')] += n
    return c


SELFTEST_GOOD = {
    'technosignatures_40pc_v9.tex': '\\documentclass{article}\n'
        '\\input{survey_numbers}\n\\input{survey_numbers_round1}\n'
        '\\begin{document}x\\end{document}\n',
    'survey_numbers.tex': '\\newcommand{\\A}{1}\n',
    'survey_numbers_round1.tex': '% gen.py\n\\newcommand{\\B}{2}\n',
    'tab_x.tex': 'x\n',
    'gen.py': (
        "import os, re, glob\n"
        "HERE = os.path.dirname(os.path.abspath(__file__))\n"
        "OUT = os.path.join(HERE, 'survey_numbers_\x72ound1.tex')\n"
        "def texval(name):\n"
        "    got = None\n"
        "    for fn in sorted(os.listdir(HERE)):\n"
        "        if not (fn.startswith('survey_numbers') and fn.endswith('.tex')):\n"
        "            continue\n"
        "        mm = re.search(r'\\\\newcommand\\{\\\\%s\\}\\{([^}]*)\\}' % name,\n"
        "                       open(os.path.join(HERE, fn)).read())\n"
        "        if mm:\n"
        "            got = mm.group(1)\n"
        "    return got\n"
        "order = [m + '.tex' for m in re.findall(r'\\\\input\\{(survey_numbers[A-Za-z0-9_]*)\\}',\n"
        "         open(os.path.join(HERE, 'technosignatures_40pc_v9.tex')).read())]\n"
        "vals = [open(os.path.join(HERE, f)).read() for f in order]\n"
        "alltex = sorted(glob.glob(os.path.join(HERE, '*.tex')))\n"
        "assert texval('A') == '1' and texval('B') == '2', 'texval'\n"
        "assert len(vals) == 2, order\n"
        "assert len(alltex) >= 4, alltex\n"
        "open(OUT, 'w').write('% gen.py\\n\\\\newcommand{\\\\B}{2}\\n')\n"
        "# regression idioms (each broke a real generator during development)\n"
        "SFX = ''\n"
        "def P(name):\n"
        "    return os.path.join(HERE, name)\n"
        "def out(name):\n"
        "    b, e = os.path.splitext(name)\n"
        "    return P(b + SFX + e)\n"
        "OUT2 = os.path.join(HERE, 'survey_numbers_\x72ound2.tex')\n"
        "open(out(os.path.basename(OUT2)), 'w').write('x')\n"
        "open(out('survey_numbers_\x72ound3.tex'), 'w').write('y')\n"
        "PRODUCTS = ['survey_numbers_round1.tex', 'tab_x.tex']\n"
        "for p in PRODUCTS:\n"
        "    assert os.path.exists(os.path.join(HERE, p)), p\n"
        "for fn in sorted(os.listdir(HERE)):\n"
        "    if fn.endswith('.py'):\n"
        "        open(os.path.join(HERE, fn)).read()\n"
        "for fn in sorted(os.listdir(HERE)):\n"
        "    if fn.startswith('survey_numbers') and fn.endswith('.tex'):\n"
        "        open(os.path.join(HERE, fn)).read()\n"
        "print('GEN OK')\n"),
    'clean.sh': '# survey_numbers comment\nrm -f survey_numbers_round1_drive$d.tex\n',
}
SELFTEST_BAD = {
    'external call': "import os, foo\nfoo.bar('survey_numbers_round1.tex')\n",
    'data path list': None,
    'pruning walk': (
        "import os\nfor dp, dn, fn in os.walk('.'):\n"
        "    dn[:] = [d for d in dn if d in ('sections',)]\n"
        "    print(fn)\n"),
    'f-string': "import os\nn = 1\np = f'survey_numbers_round{n}.tex'\nopen(p)\n",
    'broad listing to unknown use': (
        "import os\nx = os.listdir('.')\nfoo(x)\n"),
}


def selftest():
    """The refusal must be DEMONSTRATED (a filter is validated only when
    shown to reject something): one clean synthetic tree that must apply,
    run, and re-run as a no-op, and one planted defect per kind that must be
    refused with nothing written."""
    import shutil
    import subprocess
    import tempfile
    import hashlib
    fails = 0
    d = tempfile.mkdtemp(prefix='numbers_move_selftest_')
    try:
        for f, t in SELFTEST_GOOD.items():
            open(os.path.join(d, f), 'w').write(t)
        r = subprocess.run([sys.executable, '-I', '-B', os.path.join(d, 'gen.py')],
                           capture_output=True, text=True)
        ok0 = 'GEN OK' in r.stdout
        rc = main([d])
        r = subprocess.run([sys.executable, '-I', '-B', os.path.join(d, 'gen.py')],
                           capture_output=True, text=True)
        stray = [f for f in os.listdir(d) if f.startswith(SN)]
        ok1 = rc == 0 and 'GEN OK' in r.stdout and os.path.isfile(
            os.path.join(d, SUB, 'survey_numbers_round1.tex')) and not \
            stray and all(os.path.isfile(os.path.join(d, SUB, 'survey_numbers_'
                                                         'round%d.tex' % k))
                          for k in (2, 3))
        src = open(os.path.join(d, 'technosignatures_40pc_v9.tex')).read()
        ok2 = '\\input{%s/survey_numbers_round1}' % SUB in src
        sh = open(os.path.join(d, 'clean.sh')).read()
        ok3 = 'rm -f %s/survey_numbers_round1_drive$d.tex' % SUB in sh and \
            '# survey_numbers comment' in sh
        h = {f: hashlib.sha256(open(os.path.join(d, f), 'rb').read()).hexdigest()
             for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))}
        rc2 = main([d])
        h2 = {f: hashlib.sha256(open(os.path.join(d, f), 'rb').read()).hexdigest()
              for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))}
        ok4 = rc2 == 0 and h == h2
        for nm, ok in (('baseline runs before the move', ok0),
                       ('moved, and the generator still runs', ok1),
                       ('manuscript \\input repointed', ok2),
                       ('shell operand repointed, comment untouched', ok3),
                       ('re-run is a no-op (idempotent)', ok4)):
            print('  selftest %-46s %s' % (nm, 'PASS' if ok else 'FAIL'))
            fails += not ok
        print('  selftest   (generator after the move: %s)' % r.stdout.strip()[-60:])
    finally:
        shutil.rmtree(d, ignore_errors=True)
    for nm, code in SELFTEST_BAD.items():
        d = tempfile.mkdtemp(prefix='numbers_move_neg_')
        try:
            for f, t in SELFTEST_GOOD.items():
                if f != 'gen.py':
                    open(os.path.join(d, f), 'w').write(t)
            if code is None:
                open(os.path.join(d, 'paths.json'), 'w').write(
                    '{"read": ["survey_numbers_round1.tex"]}\n')
            else:
                open(os.path.join(d, 'bad.py'), 'w').write(code)
            before = sorted(os.listdir(d))
            hb = {f: open(os.path.join(d, f), 'rb').read() for f in before
                  if os.path.isfile(os.path.join(d, f))}
            rc = main([d])
            after = sorted(os.listdir(d))
            ha = {f: open(os.path.join(d, f), 'rb').read() for f in after
                  if os.path.isfile(os.path.join(d, f))}
            ok = rc == 2 and before == after and hb == ha
            print('  selftest REFUSES %-38s %s' % (nm, 'PASS' if ok else
                                                   'FAIL (rc %s)' % rc))
            fails += not ok
        finally:
            shutil.rmtree(d, ignore_errors=True)
    print('numbers_move selftest: %s' % ('ALL PASS' if not fails else
                                         '%d FAIL' % fails))
    return 1 if fails else 0


def check(argv):
    """--check: the gate.  Exit 0 only if the build root needs nothing."""
    import shutil
    import tempfile
    drive = int(argv[argv.index('--drive') + 1]) if '--drive' in argv else None
    root = os.path.dirname(os.path.abspath(__file__))
    stray = sorted(f for f in os.listdir(root) if DRIVE.search(f) and f.startswith(SN))
    movers = sorted(f for f in os.listdir(root) if MACRO_FILE.match(f))
    if drive == 1:          # a macro file written at the build root
        movers.append('survey_numbers_round0.tex')
    edits, rep = scan(root)
    if drive == 2:          # a generator that writes a macro file the old way
        d = tempfile.mkdtemp(prefix='numbers_check_drive_')
        try:
            open(os.path.join(d, 'gen_drive.py'), 'w').write(
                "import os\nHERE = os.path.dirname(os.path.abspath(__file__))\n"
                "open(os.path.join(HERE, 'survey_numbers_\x72ound0.tex'), 'w').write('x')\n")
            e2, r2 = scan(d)
        finally:
            shutil.rmtree(d)
        edits.update({'DRIVE/' + k: v for k, v in e2.items()})
        rep['unclassified'] += r2['unclassified']
    sub = os.path.join(root, SUB)
    nsub = len([f for f in os.listdir(sub) if MACRO_FILE.match(f)]) if os.path.isdir(sub) else 0
    print('numbers_check: %d macro file(s) in %s/, %d at the build root, %d drive artefact(s) at the root, '
          '%d file(s) to edit, %d unclassified' % (nsub, SUB, len(movers), len(stray), len(edits),
                                                    len(rep['unclassified'])))
    for f in movers[:5]:
        print('  FAIL macro file at the build root: %s' % f)
    for f in sorted(edits)[:5]:
        print('  FAIL reference not repointed: %s' % f)
    for u in rep['unclassified'][:5]:
        print('  FAIL unclassified: %s:%s %s' % u[:3])
    if stray or movers or edits or rep['unclassified'] or not nsub:
        print('numbers_check: FAIL -- numbers_move.py --dry-run would not say "nothing to do"')
        return 1
    print('numbers_check: nothing to do (already applied)')
    return 0


def main(argv):
    if '--check' in argv:
        return check(argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    if argv[0] == '--selftest':
        return selftest()
    tree = argv[0]
    dry = '--dry-run' in argv
    repf = argv[argv.index('--report') + 1] if '--report' in argv else None
    root = build_root(tree)
    if not os.path.isdir(root):
        raise SystemExit('numbers_move: no such tree %s' % tree)
    stray = [f for f in os.listdir(root) if DRIVE.search(f) and f.startswith(SN)]
    if stray:
        raise SystemExit('numbers_move: REFUSED -- drive artefacts at the build '
                         'root (%s); remove them first' % ', '.join(sorted(stray)))
    movers = sorted(f for f in os.listdir(root) if MACRO_FILE.match(f))
    sub = os.path.join(root, SUB)
    if os.path.lexists(sub) and not os.path.isdir(sub) or os.path.islink(sub):
        raise SystemExit('numbers_move: REFUSED -- %s exists and is not a real '
                         'directory' % sub)
    already = sorted(f for f in os.listdir(sub) if MACRO_FILE.match(f)) \
        if os.path.isdir(sub) else []
    clash = sorted(set(movers) & set(already))
    if clash:
        raise SystemExit('numbers_move: REFUSED -- %d macro file(s) exist BOTH at '
                         'the root and in %s/: %s' % (len(clash), SUB, clash[:5]))
    edits, rep = scan(root)
    c = summarise(rep)
    print('numbers_move: build root %s' % root)
    print('  macro files at root: %d   already in %s/: %d' % (len(movers), SUB,
                                                            len(already)))
    for k in sorted(c):
        print('  %-4s %-8s %-22s %5d' % (k[0], k[1], k[2], c[k]))
    print('  files to edit: %d' % len(edits))
    if repf:
        json.dump({'movers': movers, 'already': already,
                   'edits': {k: (len(v) if isinstance(v, list) else 'text')
                             for k, v in edits.items()},
                   'report': rep}, open(repf, 'w'), indent=1, default=str)
    if rep['unclassified']:
        print('\nnumbers_move: REFUSED -- %d reference(s) it cannot classify '
              '(nothing written):' % len(rep['unclassified']))
        for u in rep['unclassified']:
            print('  %s:%s  %s\n        %s' % u[:4])
        return 2
    if not movers and not edits:
        print('numbers_move: nothing to do (already applied)')
        return 0
    if dry:
        print('numbers_move: dry run -- nothing written')
        return 0
    return apply(root, movers, edits)


def apply(root, movers, edits):
    import hashlib
    sub = os.path.join(root, SUB)
    # 1. edits -- ALL computed and parse-checked before ANY is written, so a
    #    defect in one edit leaves the tree untouched
    staged = {}
    for rel, e in sorted(edits.items()):
        p = os.path.join(root, rel)
        raw = open(p, 'rb').read()
        new = apply_bytes(raw, e) if isinstance(e, list) else e.encode()
        if rel.endswith('.py'):
            try:
                ast.parse(new)
            except SyntaxError as ex:
                raise SystemExit('numbers_move: REFUSED -- the edit of %s does '
                                 'not parse (%s); NOTHING was written' % (rel, ex))
        staged[rel] = new
    for rel, new in sorted(staged.items()):
        p = os.path.join(root, rel)
        st = os.stat(p)
        with open(p, 'wb') as fh:
            fh.write(new)
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
    # 2. the move (rename within one filesystem: content and mtime preserved)
    os.makedirs(sub, exist_ok=True)
    for f in movers:
        a, b = os.path.join(root, f), os.path.join(sub, f)
        h = hashlib.sha256(open(a, 'rb').read()).hexdigest()
        os.rename(a, b)
        assert hashlib.sha256(open(b, 'rb').read()).hexdigest() == h
    print('numbers_move: edited %d file(s), moved %d macro file(s) into %s/'
          % (len(edits), len(movers), SUB))
    # 3. completeness: a second scan must find nothing left to do
    edits2, rep2 = scan(root)
    left = sorted(f for f in os.listdir(root) if MACRO_FILE.match(f))
    if edits2 or left or rep2['unclassified']:
        print('numbers_move: *** SECOND SCAN NOT CLEAN *** edits %s, left %s, '
              'unclassified %s' % (sorted(edits2)[:10], left[:5],
                                   rep2['unclassified'][:5]))
        return 3
    print('numbers_move: second scan clean (idempotent); %s entries at the '
          'build root' % len(os.listdir(root)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
