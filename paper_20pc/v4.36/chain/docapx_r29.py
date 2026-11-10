#!/usr/bin/env python3
r"""docapx_r29.py -- render the six `documentation/appendix_*.md` files of the data archive (round 28, Ruling R14).

The article's appendices point at "the full treatment ... in documentation/appendix_X.md of the data archive"
six times, and until v4.29 none of the six files existed: the length reduction moved the paragraphs out of the
appendices and wrote their sources (`r28inputs/docapx/appendix_*.excerpt`, one block per moved paragraph, the
whole paragraph as it stood, so it can be read alone) but nothing rendered them into the deposit.

This module is called by `zdeposit.py`.  It renders each excerpt source with the SAME macro values the article is
built from (`zdeposit.MAC`), turns LaTeX into plain Markdown, and turns every cross-reference into words -- the
deposit carries no section, table, figure or equation number (zverify V4) -- by the title or caption of the
labelled object in this build's own `sections/*.tex`.  Citations become author-and-year from the article's own
bibliography.  Anything it cannot render (an undefined macro, an unknown label, a LaTeX command it does not know)
is collected and returned; `zdeposit.py` stops on it, so a stale excerpt cannot ship half-rendered.

    python3 -I -B docapx_r29.py [--check]     # render to stdout-summary only (writes nothing)
"""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'r28inputs', 'docapx')
FILES = ('appendix_A_smearing', 'appendix_B_spatial_normalisation', 'appendix_C_line_mask',
         'appendix_D_false_alarm', 'appendix_E_rfi', 'appendix_F_per_system')
TITLES = {
    'appendix_A_smearing': 'Spectral response, smearing, primary beam and position: the full treatment',
    'appendix_B_spatial_normalisation': 'Spatial normalisation and exchangeability: the full treatment',
    'appendix_C_line_mask': 'The molecular-line mask: the full treatment',
    'appendix_D_false_alarm': 'False alarms and chance expectations: the full treatment',
    'appendix_E_rfi': 'Interference: the full treatment',
    'appendix_F_per_system': 'Per-system limits: the full treatment',
}

GREEK = {'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'epsilon': 'ε', 'varepsilon': 'ε', 'eta': 'η',
         'theta': 'θ', 'lambda': 'λ', 'mu': 'μ', 'nu': 'ν', 'pi': 'π', 'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ',
         'phi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω', 'Delta': 'Δ', 'Sigma': 'Σ', 'Omega': 'Ω',
         'Gamma': 'Γ', 'Lambda': 'Λ', 'Phi': 'Φ'}
SYMS = {'pm': '±', 'times': '×', 'to': '→', 'rightarrow': '→', 'star': '⋆', 'approx': '≈', 'simeq': '≃',
        'leq': '≤', 'le': '≤', 'geq': '≥', 'ge': '≥', 'sim': '~', 'cdot': '·', 'ldots': '…', 'dots': '…',
        'cdots': '…', 'infty': '∞', 'propto': '∝', 'odot': '⊙', 'circ': '°', 'prime': '′', 'min': 'min',
        'max': 'max', 'log': 'log', 'ln': 'ln', 'exp': 'exp', 'lesssim': '≲', 'gtrsim': '≳', 'neq': '≠',
        'quad': ' ', 'qquad': ' ', 'S': '§', 'textbar': '|', 'ell': 'ℓ', 'odot': '⊙', 'sun': '☉',
        'deg': '°', 'textdegree': '°', 'AA': 'Å', 'oplus': '⊕', 'mid': '|', 'langle': '⟨', 'rangle': '⟩'}
DROP = {'allowbreak', 'noindent', 'centering', 'protect', 'relax', 'ensuremath', 'displaystyle', 'left', 'right',
        'big', 'Big', 'bigl', 'bigr', 'nolinebreak', 'linebreak', 'hfill', 'xspace', 'mbox', 'hbox', 'null'}
ARG1 = {'emph': '*%s*', 'textit': '*%s*', 'textbf': '**%s**', 'texttt': '`%s`', 'mathrm': '%s', 'rm': '%s',
        'textrm': '%s', 'mathit': '%s', 'mathbf': '%s', 'textsc': '%s', 'text': '%s', 'textsf': '%s',
        'operatorname': '%s', 'mbox': '%s', 'hbox': '%s', 'textsuperscript': '^%s', 'textsubscript': '_%s',
        'sqrt': '√(%s)', 'dot': '%ṡ', 'bar': '%s̄', 'hat': '%ŝ', 'tilde': '%s̃', 'overline': '%s̄',
        'ensuremath': '%s', 'url': '%s', 'nolinkurl': '%s', 'textup': '%s', 'unit': '%s'}


def _labels():
    """label -> words, from this build's own sources (section titles, table/figure captions)."""
    out = {}
    secs = sorted(glob.glob(os.path.join(HERE, 'sections', '*.tex')))
    for p in secs:
        t = open(p, encoding='utf-8', errors='ignore').read()
        for m in re.finditer(r'\\(sub)*section\*?\{((?:[^{}]|\{[^{}]*\})*)\}\s*(?:%[^\n]*\n\s*)*\\label\{([^}]+)\}', t):
            out[m.group(3)] = ('section', m.group(2))
        for m in re.finditer(r'\\caption\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}', t):
            cap = m.group(1)
            lab = re.search(r'\\label\{([^}]+)\}', t[m.end():m.end() + 400])
            labin = re.search(r'\\label\{([^}]+)\}', cap)
            for lm in (labin, lab):
                if lm and lm.group(1) not in out:
                    kind = 'table' if lm.group(1).startswith('tab:') else 'figure'
                    first = re.split(r'(?<=[a-z\}])\.\s', re.sub(r'\\label\{[^}]*\}', '', cap))[0]
                    out[lm.group(1)] = (kind, first)
                    break
        for m in re.finditer(r'\\label\{(eq:[^}]+)\}', t):
            out.setdefault(m.group(1), ('equation', None))
    return out


def _bib():
    main = glob.glob(os.path.join(HERE, 'technosignatures_*.tex'))
    out = {}
    for p in main:
        for m in re.finditer(r'\\bibitem\[([^\]]+)\]\{([^}]+)\}', open(p, encoding='utf-8', errors='ignore').read()):
            lab = m.group(1)
            mm = re.match(r'(.*)\((\d{4}[a-z]?)\)\s*$', lab)
            out[m.group(2)] = (mm.group(1).strip(), mm.group(2)) if mm else (lab, '')
    return out


class Renderer:
    def __init__(self, mac):
        self.mac = mac
        self.lab = _labels()
        self.bib = _bib()
        self.problems = []

    # -- words for a reference
    def ref_words(self, label, kind_hint=None):
        if label not in self.lab:
            self.problems.append('unknown label %s' % label)
            return 'the paper'
        kind, title = self.lab[label]
        if kind == 'equation':
            return 'the corresponding equation of the paper'
        t = self.inline(title)
        t = re.sub(r'\s+', ' ', t).strip().rstrip('.')
        if kind == 'section':
            return 'the section of the paper on “%s”' % t
        return 'the %s of the paper headed “%s”' % (kind, t)

    def cite(self, keys, paren, pre=None):
        parts = []
        for k in [x.strip() for x in keys.split(',')]:
            if k not in self.bib:
                self.problems.append('unknown citation %s' % k)
                parts.append(k)
                continue
            a, y = self.bib[k]
            a = self.inline(a)
            parts.append('%s %s' % (a, y) if paren else '%s (%s)' % (a, y))
        s = '; '.join(parts)
        if pre:
            s = s + ', ' + self.inline(pre)
        return '(%s)' % s if paren else s

    # -- the whole conversion
    def inline(self, s):
        s = s.replace('\\%', '%').replace('\\_', '_').replace('\\&', '&').replace('\\#', '#')
        s = re.sub(r'(?<!\\)%[^\n]*', '', s)                     # comments
        # references, before macros: plural forms first
        refw = lambda m: self.ref_words(m.group(1))
        s = re.sub(r'(?:Appendices|Sections|\\S\\S)~?\s*\\ref\{([^}]+)\}\s*(?:and|,)~?\s*\\ref\{([^}]+)\}',
                   lambda m: '%s and %s' % (self.ref_words(m.group(1)), self.ref_words(m.group(2))), s)
        s = re.sub(r'(?:Appendix|Section|Sec\.|\\S)~?\s*\\ref\{([^}]+)\}', refw, s)
        s = re.sub(r'(?:Tables?|Figs?\.|Figures?)~?\s*\\ref\{([^}]+)\}', refw, s)
        s = re.sub(r'(?:Eqs?\.|Equations?)~?\s*\(?\\ref\{([^}]+)\}\)?', refw, s)
        s = re.sub(r'\\eqref\{([^}]+)\}', refw, s)
        s = re.sub(r'\\ref\{([^}]+)\}', refw, s)
        s = re.sub(r'\\citep(?:\[([^\]]*)\])?\{([^}]+)\}', lambda m: self.cite(m.group(2), True, m.group(1)), s)
        s = re.sub(r'\\citet\{([^}]+)\}', lambda m: self.cite(m.group(1), False), s)
        s = re.sub(r'\\cite\{([^}]+)\}', lambda m: self.cite(m.group(1), True), s)
        s = self.expand(s)
        s = s.replace('$', '')
        s = re.sub(r'\^\{([^{}]*)\}', r'^\1', s)
        s = re.sub(r'_\{([^{}]*)\}', r'_\1', s)
        s = s.replace('{', '').replace('}', '')
        s = s.replace('\\,', ' ').replace('\\;', ' ').replace('\\:', ' ').replace('\\!', '').replace('\\ ', ' ')
        s = s.replace('\\-', '').replace('\\/', '').replace('\\\\', ' ')
        s = s.replace('~', ' ').replace('---', '—').replace('--', '–').replace('``', '“').replace("''", '”')
        if '\\' in s:
            for x in sorted(set(re.findall(r'\\[A-Za-z]+|\\.', s))):
                self.problems.append('unrendered %s' % x)
        return s

    @staticmethod
    def _group(s, i):
        """s[i] == '{': return (content, index after the matching brace)."""
        d = 0
        for j in range(i, len(s)):
            if s[j] == '{':
                d += 1
            elif s[j] == '}':
                d -= 1
                if d == 0:
                    return s[i + 1:j], j + 1
        raise ValueError('unbalanced braces')

    def _arg(self, s, i):
        """The next argument after a command: a {group}, or one token (a command or one character)."""
        while i < len(s) and s[i] == ' ':
            i += 1
        if i < len(s) and s[i] == '{':
            return self._group(s, i)
        if i < len(s) and s[i] == '\\':
            m = re.match(r'\\[A-Za-z]+', s[i:])
            if m:
                return m.group(0), i + m.end()
        return (s[i], i + 1) if i < len(s) else ('', i)

    def expand(self, s, depth=0):
        """Brace-aware expansion: macros from the build, known commands to text, accents, fractions."""
        if depth > 12:
            self.problems.append('macro expansion too deep')
            return s
        out, i = [], 0
        while i < len(s):
            c = s[i]
            if c != '\\':
                out.append(c)
                i += 1
                continue
            if i + 1 < len(s) and s[i + 1] in '_%&#$':
                out.append(s[i + 1])
                i += 2
                continue
            if i + 1 < len(s) and s[i + 1] in '"\'`^~':
                acc, i2 = s[i + 1], i + 2
                a, i2 = self._arg(s, i2)
                out.append({'"': a + '\u0308', "'": a + '\u0301', '`': a + '\u0300', '^': a + '\u0302',
                            '~': a + '\u0303'}[acc])
                i = i2
                continue
            m = re.match(r'\\([A-Za-z]+)(\{\})?', s[i:])
            if not m:
                out.append(s[i:i + 2])
                i += 2
                continue
            name, j = m.group(1), i + m.end()
            if name in ('frac', 'dfrac', 'tfrac'):
                a, j = self._arg(s, j)
                b, j = self._arg(s, j)
                out.append('(%s)/(%s)' % (self.expand(a, depth + 1), self.expand(b, depth + 1)))
            elif name in ARG1:
                a, j = self._arg(s, j)
                out.append(ARG1[name] % self.expand(a, depth + 1))
            elif name in GREEK:
                out.append(GREEK[name])
            elif name in SYMS:
                out.append(SYMS[name])
            elif name in DROP:
                pass
            elif name == 'bmod':
                out.append(' mod ')
            elif name in self.mac:
                out.append(self.expand(self.mac[name], depth + 1))
            else:
                self.problems.append('undefined macro \\%s' % name)
                out.append('[%s]' % name)
            i = j
        return ''.join(out)


def render_all(mac, outdir=None):
    """Render the six files.  Returns ({relpath: text}, problems)."""
    R = Renderer(mac)
    out = {}
    for stem in FILES:
        src = open(os.path.join(SRC, stem + '.excerpt'), encoding='utf-8').read()
        blocks = re.split(r'^%% ---- [^\n]*\n', src, flags=re.M)[1:]
        paras = []
        for b in blocks:
            b = '\n'.join(ln for ln in b.splitlines() if not ln.lstrip().startswith('%'))
            b = re.sub(r'\\begin\{(figure|table)\*?\}.*?(?:\\end\{\1\*?\}|\Z)', '', b, flags=re.S)
            for para in re.split(r'\n\s*\n', b):
                t = re.sub(r'\s+', ' ', R.inline(para)).strip()
                if t:
                    paras.append(t)
        body = ['# %s' % TITLES[stem], '',
                'This file holds the full text of paragraphs the article summarises, as the article argues them, '
                'with every number taken from the same computation the article prints. Where the article points '
                'here, the summary it keeps is in the paper and the complete argument is below.', '']
        for p in paras:
            body += [p, '']
        out['documentation/%s.md' % stem] = '\n'.join(body).rstrip() + '\n'
    if outdir:
        for rel, txt in out.items():
            p = os.path.join(outdir, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'w', encoding='utf-8').write(txt)
    return out, sorted(set(R.problems))


def macros_like_zdeposit():
    """The macro values exactly as zdeposit.macros() reads them (manuscript \\input order, later wins) -- for the
    stand-alone check only; inside the build zdeposit passes its own MAC."""
    _M = re.compile(r'\\(?:re)?newcommand\*?\s*\{?\\([A-Za-z]+)\}?\{((?:[^{}]|\{[^{}]*\})*)\}')
    main = glob.glob(os.path.join(HERE, 'technosignatures_*.tex'))
    out = {}
    for ln in open(main[0], errors='ignore'):
        m = re.match(r'\s*\\input\{(?:numbers/)?(survey_numbers[A-Za-z0-9_]*)\}', ln)
        if m and os.path.exists(os.path.join(HERE, 'numbers', m.group(1) + '.tex')):
            for l2 in open(os.path.join(HERE, 'numbers', m.group(1) + '.tex'), errors='ignore'):
                for nm, vv in _M.findall(l2):
                    if vv.strip():
                        out[nm] = vv.strip()
    return out


if __name__ == '__main__':
    o, prob = render_all(macros_like_zdeposit())
    for k, v in o.items():
        print('%-48s %6d chars' % (k, len(v)))
    print('%d problem(s)' % len(prob))
    for x in prob:
        print('   ', x)
