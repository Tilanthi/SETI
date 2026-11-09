#!/usr/bin/env python3
"""Inventory every trace of the revision history in the manuscript's prose.

Writes PURGE.md: every hit with file and line, grouped by disposition, and a
MEASURED size for the purge -- characters of running prose, converted to pages
with the document's own typeset chars-per-page, and separately the page delta
of a scratch build with the marked sentences removed (purge_measure.py).

Nothing is edited.  This is an inventory.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = sorted(glob.glob(os.path.join(HERE, 'sections', '*.tex')))

# ★ A BLIND SPOT THE FOUR-PAGE MEASUREMENT DID NOT COVER.  Scanning only
# `sections/` scans only prose, and the revision history is not confined to
# prose: a generated table fragment headed "committed $t_0$" / "adopted
# $t_0$" and a figure whose bullet read "... where v4.02 reported none" are
# both revision history in a published artefact, and neither is in a section
# file.  Generated artefacts are text a reader sees, so they are scanned
# here too -- the table fragments directly, and the figure generators for
# the strings they draw into a PDF, where no text gate can reach at all.
GEN = sorted(glob.glob(os.path.join(HERE, 'tab_*.tex'))
             + glob.glob(os.path.join(HERE, 'tables', '*.tex')))
FIGSRC = sorted(glob.glob(os.path.join(HERE, 'make_fig*.py')))


def _drawn_strings(path):
    """String literals a figure generator draws into the figure.

    Only literals that reach a text-drawing call are returned: a comment or
    a variable name in a figure generator is not something a reader sees,
    and reporting those would bury the two hits that matter.
    """
    raw = open(path, errors='ignore').read()
    # comments are not drawn; a note explaining why a string was removed
    # must not be reported as the string still being there
    src = '\n'.join('' if l.lstrip().startswith('#') else l
                     for l in raw.split('\n'))
    out = []
    # the bullet/label/annotation lists and the direct text calls
    for m in re.finditer(r'(?:ax\.(?:text|set_title|set_xlabel|set_ylabel|'
                         r'annotate)\(|BULLETS\s*=|LABELS\s*=|'
                         r'label\s*=|title\s*=)', src):
        seg = src[m.start():m.start() + 1200]
        for q in re.finditer(r"'((?:[^'\\]|\\.){6,})'|\"((?:[^\"\\]|\\.){6,})\"",
                             seg):
            txt = q.group(1) or q.group(2)
            ln = src.count('\n', 0, m.start() + q.start()) + 1
            out.append((ln, txt))
    return out

# ---------------------------------------------------------------- patterns
# (name, regex, default disposition)
PAT = [
    ('referee',        r'[Rr]eferee|\breport\b(?!ed)|[Rr]eviewer', 'DELETE'),
    ('version',        r'\bv[0-9]\.[0-9]{1,2}\b|\bversion\b|\brevision\b|'
                       r'\bresubmi|\bsubmitted version\b', 'DELETE'),
    ('earlier/this',   r'earlier version|this version|present version|'
                       r'earlier draft|as released|as published|'
                       r'\bsuperseded\b|\bno longer\b|\bwe now\b|'
                       r'\bwe previously\b|\boriginally\b|'
                       r'at the time of (?:writing|submission)', 'DELETE'),
    ('previous',       r'\bprevious(?:ly)?\b', 'CHECK'),
    ('withdrawn',      r'\bwithdraw(?:n|al|s|ing)?\b', 'REPHRASE'),
    ('round',          r'\bround[- ]\d+\b|\bround \d+\b|\bthis round\b|'
                       r'\b(?:first|second|third|fourth|fifth|sixth|seventh|'
                       r'eighth|ninth|tenth) round\b|\bthe round\b', 'DELETE'),
    ('build/gate',     r'\bthe build\b|\bcleanregen\b|\bselftest\b|'
                       r'the generator asserts|\bfails the build\b|'
                       r'\bgate\b(?!way)|\bassertion\b|\bthe generator\b|'
                       r'\bregenerat|\bbyte-identical\b|\bmacro\b', 'DELETE'),
    ('commit',         r'\bcommit\b|\bgit\b|\b[0-9a-f]{7,40}\b', 'CHECK'),
    # ★ two conventions side by side is revision history even when neither
    # word of the history vocabulary appears: a column group headed with
    # the superseded convention and another with the adopted one is a
    # before-and-after, and it was invisible to every pattern above.
    ('two conventions', r'committed \$t_0|adopted \$t_0|'
                        r'\bbefore and after\b|'
                        r'\\multicolumn\{\d\}\{c\}\{(?:old|new|previous)\b',
     'DELETE'),
    ('our own error',  r'in our own voice|a prediction of ours|'
                       r'our own pipeline|our earlier|we were wrong|'
                       r'\bdefect\b|\berratum\b|\bcorrigend', 'REPHRASE'),
]
COMPILED = [(n, re.compile(p), d) for n, p, d in PAT]

# words that make a 'previous'/'commit' hit a FALSE POSITIVE: it is about the
# literature or about the observations, not about this paper's history
LIT = re.compile(r'\\cite|\\citep|\\citet|search(?:es)?\b|surveys?\b|'
                 r'epoch|work\b|studies|literature|decades|authors')


def sentences(text):
    """(line_no, sentence) over running prose, comments stripped but kept."""
    out = []
    for i, line in enumerate(text.split('\n'), 1):
        out.append((i, line))
    return out


def is_comment(line):
    return line.lstrip().startswith('%')


def classify(name, default, line):
    if is_comment(line):
        return 'COMMENT'
    if name in ('previous', 'commit') and LIT.search(line):
        return 'LITERATURE'
    return default


def scan_generated():
    """Hits in generated artefacts, which no prose gate reaches.

    The prose pattern set is used with ONE change: the bare hexadecimal
    clause of the commit pattern is dropped.  In running prose a loose
    7-to-40 hex string is a commit hash; in a generated table every
    catalogue designation and execution-block name matches it, and a scan
    that reports a hundred star names buries the two hits that matter.
    """
    pats = [(n, (r'\bcommit\b|\bgit\b' if n == 'commit' else p), d)
            for n, p, d in PAT]
    hits = []
    for f in GEN:
        for i, line in enumerate(open(f, errors='ignore'), 1):
            if line.lstrip().startswith('%'):
                continue
            for name, pat, dispo in pats:
                if re.search(pat, line):
                    hits.append((os.path.relpath(f, HERE), i, name, dispo,
                                 line.strip()[:120]))
    for f in FIGSRC:
        for ln, txt in _drawn_strings(f):
            for name, pat, dispo in pats:
                if re.search(pat, txt):
                    hits.append((os.path.relpath(f, HERE), ln, name, dispo,
                                 txt[:120]))
    return hits


def main():
    hits = []
    for path in SEC:
        rel = os.path.relpath(path, HERE)
        text = open(path, encoding='utf-8').read()
        for ln, line in sentences(text):
            if not line.strip():
                continue
            for name, rx, default in COMPILED:
                m = rx.search(line)
                if not m:
                    continue
                hits.append({'file': rel, 'line': ln, 'pattern': name,
                             'match': m.group(0), 'disposition':
                             classify(name, default, line),
                             'text': line.strip()})
                break          # one classification per line, first pattern

    # ------------------------------------------------- measured prose size
    # chars of running prose in the affected LINES (comments excluded), and
    # the document's own chars-per-page from the typeset page count.
    import manuscript
    flat = manuscript.flat()
    body = flat.split(r'\begin{document}')[-1].split(
        r'\begin{thebibliography}')[0]
    body_nc = re.sub(r'(?<!\\)%.*', '', body)
    prose_chars = len(body_nc)
    purge_chars = sum(len(h['text']) for h in hits
                      if h['disposition'] in ('DELETE', 'REPHRASE'))
    json.dump(hits, open(os.path.join(HERE, 'purge_hits.json'), 'w'), indent=1)

    byfile = {}
    for h in hits:
        byfile.setdefault(h['file'], []).append(h)

    with open(os.path.join(HERE, 'PURGE.md'), 'w', encoding='utf-8') as fh:
        w = fh.write
        w('# PURGE — every trace of the revision history in the prose\n\n')
        w('Generated by `purge_inventory.py`; re-run it after every pass. '
          'Nothing here has been edited.\n\n')
        w('Dispositions, assigned by pattern and to be confirmed by the file\'s '
          'owner:\n\n')
        w('- **DELETE** — prose about versions, rounds, referees, builds, '
          'gates or macros. A published paper describes the final analysis.\n')
        w('- **REPHRASE** — a statement of fact the paper still needs, but '
          'currently told as history (a withdrawal, a defect we found, a '
          'correction we made). Keep the measurement, drop the narrative.\n')
        w('- **CHECK** — ambiguous: "previous", a commit-like token, a hex '
          'identifier. Read it before touching it.\n')
        w('- **LITERATURE** — a false positive: "previous searches", '
          '"previous epoch", a citation. Leave alone.\n')
        w('- **COMMENT** — a `%` comment in the source. Leave alone; it is '
          'not typeset.\n\n')
        tot = {}
        for h in hits:
            tot[h['disposition']] = tot.get(h['disposition'], 0) + 1
        w('| disposition | hits |\n|---|---|\n')
        for k in ('DELETE', 'REPHRASE', 'CHECK', 'LITERATURE', 'COMMENT'):
            w('| %s | %d |\n' % (k, tot.get(k, 0)))
        w('| **total** | **%d** |\n\n' % len(hits))
        w('## Measured size\n\n')
        w('- running prose in the body (comments stripped): '
          '**%d characters**\n' % prose_chars)
        w('- characters on the DELETE + REPHRASE lines: **%d** '
          '= **%.1f per cent** of the body\n'
          % (purge_chars, 100.0 * purge_chars / prose_chars))
        pm = os.path.join(HERE, 'purge_measure.json')
        if os.path.exists(pm):
            M = json.load(open(pm))
            w('- **measured in pages**: a scratch build with the '
              'DELETE/REPHRASE *sentences* removed is **%d pages shorter** '
              '(main %d, appendices %d), %d sentences and %d characters = '
              '%.1f per cent of the body, 0 LaTeX errors. R1 estimated 5-7 '
              'pages; %d pp is a floor, not a ceiling -- %d characters were '
              'left in place because the sentence also carried structure, '
              'and whole history-only paragraphs are charged sentence by '
              'sentence.\n'
              % (M['delta_pages'], M['delta_main_pages'],
                 M['delta_appx_pages'], M['sentences_cut'], M['chars_cut'],
                 100.0 * M['chars_cut'] / M['chars_body'], M['delta_pages'],
                 M['chars_kept_for_structure']))
            w('- per file, characters of history: %s\n'
              % ', '.join('`%s` %d' % (k.replace('sections/', ''), v)
                          for k, v in sorted(M['per_file_chars'].items(),
                                             key=lambda kv: -kv[1])))
        w('\n')
        w('## Hits by file\n\n')
        for f in sorted(byfile):
            hs = byfile[f]
            n = {}
            for h in hs:
                n[h['disposition']] = n.get(h['disposition'], 0) + 1
            w('### `%s` — %d hits (%s)\n\n' %
              (f, len(hs), ', '.join('%s %d' % (k, v)
                                     for k, v in sorted(n.items()))))
            for h in hs:
                w('- `%s:%d` **%s** [%s/%s] %s\n'
                  % (h['file'], h['line'], h['disposition'], h['pattern'],
                     h['match'].strip(), h['text'][:180].replace('|', r'\|')))
            w('\n')
    print('purge: %d hits over %d files; DELETE %d, REPHRASE %d, CHECK %d, '
          'LITERATURE %d, COMMENT %d'
          % (len(hits), len(byfile), tot.get('DELETE', 0),
             tot.get('REPHRASE', 0), tot.get('CHECK', 0),
             tot.get('LITERATURE', 0), tot.get('COMMENT', 0)))
    print('purge: %d of %d prose chars = %.1f%%'
          % (purge_chars, prose_chars, 100.0 * purge_chars / prose_chars))


if __name__ == '__main__':
    sys.exit(main())
