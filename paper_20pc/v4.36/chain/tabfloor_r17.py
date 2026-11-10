#!/usr/bin/env python3
r"""tabfloor_r17.py -- is this TABLE's type big enough to read ON THE PAGE?

`figfloor_r17.py` asks that question of a figure, where the hazard is a
drawing made for one geometry and scaled into another.  A table has no
scaling: its type is whatever size declaration is in force when the `tabular`
is set, and that declaration is one token in a float that nobody reads back.
So the hazard is the opposite one -- not a silent factor, but a size nobody
ever measured.  Nothing in this build measured it: `figlegible_r17.py` walks
`\includegraphics`, and a table carries no graphic, so a table was invisible
to every check here.  Asked for the first time, the answer was that three
floats set their body at 5.0 pt: running prose, two points below the body
text of the paper and a point and a half below the floor the figures' axis
numerals are held to.

Clauses, all of them read off the written PDF and none of them off the
source:

  COUNT   every table float the document typesets must be measured.  The
          number is taken from the `\@writefile{lot}` lines the document
          writes for its own captions, which neither the parse nor the probe
          below can influence
  PROBE   the instrument must not move the subject: every rendered line of
          the probe build must match the plain build in text, size and
          position
  FLOOR   no LINE of type inside the float may print below the floor
  CLEAR   no two printed tokens on one row may stand closer than CLEAR_EM
          ems, because `240` beside `320` reads as `240320` long before the
          boxes touch
  WIDTH   the float's content may not run past the width it is given
  ENV     a float must occupy the width its environment promises
  EPOCH   the PDF must carry the build's pinned creation date

Finding the float at all is the part neither the source nor the log reports.
This module builds the manuscript once with a `\pdfsavepos` probe inside the
top and the bottom of every table float, which writes page and position for
each.  The probe is a zero-size `\hbox` with `\prevdepth` restored around
it, so it adds no glue and moves nothing, and PROBE proves that rather than
arguing it.

Sizes are reported per LINE, as the largest span on it: a subscript is a
separate span at about 0.7 of its base, and a second-order subscript at 0.5,
so reporting those as the size of the line would condemn every table in the
paper equally.  That is `figfloor_r17.py`'s rule unchanged, so the figure
floor and the table floor are one number measured one way.

★ FLOOR_PT is the REQUIRED floor and is never the size anything is drawn at:
no drive can move a check and its subject together.
★ A clause that cannot fail on a given float says NOT APPLICABLE and is not
counted as a pass.
"""
import os
import re
import subprocess
import sys

COL_PT = 245.26653          # openjournal.cls, twocolumn: \the\columnwidth
TEXT_PT = 513.11743         # openjournal.cls, twocolumn: \the\textwidth
TEXTHT_PT = 675.83984       # \the\textheight -- the width a landscape float
#                             has to play with

BUILD_EPOCH = '1577836800'                      # 2020-01-01T00:00:00Z
_EPOCH_STAMP = 'D:20200101000000Z'

FLOOR_PT = 6.5              # REQUIRED floor.  ★ The roman of this class is
#                             available at whole points only, so the sizes a
#                             table can actually be set in are 5, 6, 7, 8, 9
#                             and 10 pt: \fontsize{6.5} prints at 6 and says
#                             so only in a font warning nobody reads.  The
#                             floor therefore means \scriptsize or larger.
CLEAR_EM = 0.15             # REQUIRED clearance between two printed tokens
#                             on one row, in ems of that row's own type.
#                             The narrowest space this paper sets on purpose
#                             is the thin space of `\,`, which measures
#                             0.177-0.190 em here; a gap tighter than that is
#                             not a space anybody asked for, and the values
#                             on either side of it read as one.
TOUCH_EM = 0.02             # ink this close is one printed token: a PDF word
#                             breaks at a font change as well as at a space,
#                             so `(` and the symbol after it arrive as two
#                             words with nothing at all between them.
WIDTH_TOL_PT = 1.0          # a hanging rule or an overshooting minus sign

SP = 65536.0                # scaled points per point

_WIDTH_OF = {'table': COL_PT, 'table*': TEXT_PT,
             'sidewaystable': TEXTHT_PT, 'sidewaystable*': TEXTHT_PT}

_PROBE_PRE = r"""
\newwrite\tabposfile
\immediate\openout\tabposfile=tabpos.txt
\makeatletter
\newcommand{\TPprobe}[2]{%
  \ifhmode\par\fi
  \begingroup
  \edef\tp@next{\noexpand\write\tabposfile{#1\space #2\space
    \noexpand\thepage\space \noexpand\the\noexpand\pdflastxpos\space
    \noexpand\the\noexpand\pdflastypos}}%
  \setbox\z@\hbox{\pdfsavepos\tp@next}%
  \ht\z@\z@ \dp\z@\z@ \wd\z@\z@
  \dimen@\prevdepth \nointerlineskip \box\z@ \prevdepth\dimen@
  \endgroup}
\makeatother
\begin{document}
"""

# ★ Every float environment that typesets a table, not just `table`.  The
# first version of this module knew only `table`/`table*`, and the moment the
# crossing ledger was set landscape it stopped being measured AT ALL -- the
# parse and the probe were blind in the same way, so the counts still agreed
# and the gate reported twelve of twelve passing with the worst table in the
# paper outside it.  The COUNT clause exists because of that.
_BEGIN = re.compile(r'\\begin\{(sidewaystable\*?|table\*?)\}')
_INPUT = re.compile(r'\\(?:input|include)\{([^}]+)\}')


def _strip_comments(s):
    r"""A commented-out float is not a float.  `\%` is a per-cent sign."""
    return re.sub(r'(?m)(?<!\\)%.*$', '', s)


def manuscript(here):
    main = [f for f in sorted(os.listdir(here))
            if f.startswith('technosignatures') and f.endswith('.tex')]
    assert len(main) == 1, 'cannot identify the manuscript: %r' % main
    return main[0]


def _resolve(here, name):
    for cand in (name, name + '.tex'):
        if os.path.isfile(os.path.join(here, cand)):
            return cand
    return None


def input_order(here, start=None):
    r"""Every .tex the manuscript reads, in the order it reads them.

    Depth-first through \input, which is the order LaTeX meets the floats in
    and therefore the order the probe numbers them.  ★ A table need not live
    in a section file: `tab:selfunc`'s whole float is inside the GENERATED
    fragment `tab_selection.tex`, so a walk of `sections/` alone misses it,
    and the first thing this module was asked found 13 of 14.
    """
    start = manuscript(here) if start is None else start
    out, seen = [], set()

    def walk(rel):
        if rel in seen:
            return
        seen.add(rel)
        out.append(rel)
        src = _strip_comments(open(os.path.join(here, rel), encoding='utf-8',
                                   errors='replace').read())
        for m in _INPUT.finditer(src):
            sub = _resolve(here, m.group(1))
            if sub:
                walk(sub)

    walk(start)
    return out


def find_tables(here):
    """[(idx, env, label, relfile)], idx from 1, in the order LaTeX meets
    them."""
    tabs, idx = [], 0
    for rel in input_order(here):
        src = _strip_comments(open(os.path.join(here, rel), encoding='utf-8',
                                   errors='replace').read())
        for m in _BEGIN.finditer(src):
            env = m.group(1)
            end = src.find(r'\end{%s}' % env, m.end())
            body = src[m.end():end if end > 0 else len(src)]
            lab = re.search(r'\\label\{([^}]+)\}', body)
            idx += 1
            tabs.append((idx, env, lab.group(1) if lab else '(unlabelled)',
                         rel))
    return tabs


def _patch_probe(src, counts):
    r"""Insert `\TPprobe` just inside the top and the bottom of every table
    float, numbering them from `counts['n']`."""
    out, pos = [], 0
    while True:
        m = _BEGIN.search(src, pos)
        if not m:
            out.append(src[pos:])
            break
        env = m.group(1)
        end = src.find(r'\end{%s}' % env, m.end())
        assert end > 0, r'\begin{%s} with no \end' % env
        counts['n'] += 1
        out.append(src[pos:m.end()])
        out.append('\\TPprobe{%d}{B}%%\n' % counts['n'])
        out.append(src[m.end():end])
        out.append('\\TPprobe{%d}{E}%%\n' % counts['n'])
        pos = end
    return ''.join(out)


def probe_build(here, outdir, verbose=True):
    """Build the manuscript twice in `outdir`: once untouched, once with the
    probe.  Returns (plain pdf, probe pdf, probe aux, positions).

    Nothing is written inside `here`: every .tex the manuscript reads is
    copied into the probe directory and TEXINPUTS puts that directory first,
    so the patched copies shadow the originals and the real tree is not
    touched at all.  The plain build runs in a directory holding no patched
    copy, so its `.` resolves to nothing and it reads the originals.
    """
    main = manuscript(here)
    pdir = os.path.join(outdir, 'probe')
    cdir = os.path.join(outdir, 'plain')
    os.makedirs(pdir, exist_ok=True)
    os.makedirs(cdir, exist_ok=True)
    counts = {'n': 0}
    for rel in input_order(here):
        dst = os.path.join(pdir, rel)
        os.makedirs(os.path.dirname(dst) or pdir, exist_ok=True)
        src = open(os.path.join(here, rel), encoding='utf-8',
                   errors='replace').read()
        if _BEGIN.search(_strip_comments(src)):
            src = _patch_probe(src, counts)
        if rel == main:
            assert src.count(r'\begin{document}') == 1
            src = src.replace(r'\begin{document}', _PROBE_PRE)
        open(dst, 'w', encoding='utf-8').write(src)

    env = dict(os.environ, SOURCE_DATE_EPOCH=BUILD_EPOCH,
               TEXINPUTS='.:%s:%s//:' % (here, here))
    for d in (cdir, pdir):
        arg = os.path.join(here, main) if d is cdir else main
        for _ in range(3):
            r = subprocess.run(['pdflatex', '-interaction=nonstopmode', arg],
                               cwd=d, env=env, capture_output=True)
        assert r.returncode == 0, 'pdflatex failed in %s; see %s.log' % (
            d, os.path.join(d, main[:-4]))
        if verbose:
            print('  built %s' % os.path.join(d, main[:-4] + '.pdf'))

    pos = {}
    for ln in open(os.path.join(pdir, 'tabpos.txt'), encoding='utf-8'):
        f = ln.split()
        if len(f) == 5:
            pos.setdefault(int(f[0]), {})[f[1]] = (
                int(f[2]), int(f[3]) / SP, int(f[4]) / SP)
    return (os.path.join(cdir, main[:-4] + '.pdf'),
            os.path.join(pdir, main[:-4] + '.pdf'),
            os.path.join(pdir, main[:-4] + '.aux'), pos)


def _axes(d):
    """The reading axis and the cross axis of a line, in a y-up page frame.

    A landscape float is rotated by the PDF, not by TeX, so its glyphs carry
    a direction and its rows run UP the page.  Projecting on to the line's
    own direction puts an upright table and a landscape one in one frame, and
    every measurement below -- gaps along a row, the span of a rule, the
    width of the content -- is then the same measurement for both.
    """
    dx, dy = d[0], -d[1]            # the PDF reports y downwards
    return (dx, dy), (-dy, dx)


def _proj(box, ax):
    xs = [box[0] * ax[0] + box[1] * ax[1], box[0] * ax[0] + box[3] * ax[1],
          box[2] * ax[0] + box[1] * ax[1], box[2] * ax[0] + box[3] * ax[1]]
    return min(xs), max(xs)


def lines(pdfpath):
    """Every rendered LINE in a PDF, with the words on it.

    `size` is the largest span on the line, which is the size at which that
    line reads.  `words` are the whitespace- and font-delimited runs with
    their boxes: a PDF span breaks at a font change, not at a cell boundary,
    so span boxes cannot answer how far apart two printed values stand.
    Boxes are y-up, which is the frame `\\pdflastypos` reports in.
    """
    import pymupdf
    doc = pymupdf.open(pdfpath)
    out = []
    for pno, page in enumerate(doc, start=1):
        h = page.rect.height
        words = [(w[0], h - w[3], w[2], h - w[1], w[4]) for w in
                 page.get_text('words')]
        for blk in page.get_text('dict')['blocks']:
            for ln in blk.get('lines', []):
                on = [s for s in ln['spans'] if s['text'].strip()]
                if not on:
                    continue
                b = ln['bbox']
                box = (b[0], h - b[3], b[2], h - b[1])
                wl = [w for w in words
                      if w[0] >= box[0] - 0.1 and w[2] <= box[2] + 0.1
                      and w[1] >= box[1] - 0.1 and w[3] <= box[3] + 0.1]
                out.append({'page': pno, 'size': max(s['size'] for s in on),
                            'text': ''.join(s['text'] for s in on),
                            'box': box, 'dir': tuple(ln['dir']), 'words': wl})
    stamp = doc.metadata.get('creationDate') or ''
    npage = doc.page_count
    doc.close()
    return out, npage, stamp


def rects(pdfpath):
    """Every long thin rule a PDF draws, {page: [(x0, y0, x1, y1)]}, y-up.

    Rules are the only thing in the artefact that says where a tabular
    starts and stops: a caption, a table note and a row are all just lines of
    type.  Both orientations are kept, because a landscape table draws its
    rules down the page.
    """
    import pymupdf
    doc = pymupdf.open(pdfpath)
    out = {}
    for pno, page in enumerate(doc, start=1):
        h = page.rect.height
        for dr in page.get_drawings():
            r = dr['rect']
            if min(r.height, r.width) <= 1.6 and max(r.height, r.width) >= 20:
                out.setdefault(pno, []).append(
                    (r.x0, h - r.y1, r.x1, h - r.y0))
    doc.close()
    return out


class Meas(object):
    __slots__ = ('idx', 'env', 'label', 'page', 'npage', 'nline', 'width',
                 'extent', 'min_pt', 'min_text', 'clear', 'clear_pt',
                 'clear_pair', 'nrule', 'over')

    def __repr__(self):
        return ('<%s %s p%s %d lines  min %.2f pt>'
                % (self.label, self.env, self.page, self.nline, self.min_pt))


def measure(here, outdir, verbose=True, drive=0):
    """Measure every table float in the built PDF.  Returns {label: Meas}."""
    plain, probe, aux, pos = probe_build(here, outdir, verbose=verbose)
    tabs = find_tables(here)

    # CLAUSE COUNT.  The document counts its own tables: every \caption in a
    # table float writes one \@writefile{lot} line into the .aux.  That
    # number is not derived from the regexp above or from the probe, so a
    # float environment neither of them knows about shows up here as a
    # disagreement instead of as a silent omission.
    lot = len(re.findall(r'\\@writefile\{lot\}',
                         open(aux, encoding='utf-8', errors='replace').read()))
    n_parse = len(tabs) - (1 if drive == 5 else 0)
    assert len(pos) == n_parse == lot, (
        'the probe reports %d table floats, the sources parse to %d, and the '
        'document typeset %d table captions; a float every one of these '
        'cannot see is a float that goes unmeasured' % (len(pos), n_parse,
                                                        lot))

    # CLAUSE PROBE.  The instrument must not move the subject.  Compared on
    # every rendered line of every page, in size, text and position: if the
    # probe inserted so much as a hair of glue, everything below it on the
    # page shifts and this fails.  Without it the measurement would rest on
    # an argument about \prevdepth instead of on a fact -- and the first
    # version of the probe DID move the page, by a point and a third, by
    # keeping alive a trailing space that \par would have discarded.
    a, na, _ = lines(plain)
    b, nb, stamp = lines(probe)
    if drive == 6:
        b = b[1:]
    assert na == nb, ('the probe build has %d pages and the plain build %d'
                      % (nb, na))
    assert len(a) == len(b), ('%d lines against %d: the probe changed the '
                              'typeset page' % (len(b), len(a)))
    for x, y in zip(a, b):
        assert (x['page'] == y['page'] and abs(x['size'] - y['size']) < 1e-3
                and x['text'] == y['text']
                and max(abs(p - q) for p, q in zip(x['box'], y['box']))
                < 1e-3), ('the probe moved a line: %r against %r' % (x, y))

    rl = rects(probe)
    sideways = {}
    for idx, env, label, _rel in tabs:
        if env.startswith('sideways'):
            sideways.setdefault(pos[idx]['B'][0], []).append(label)

    out = {}
    for idx, env, label, _rel in tabs:
        p = pos[idx]
        assert 'B' in p and 'E' in p, 'probe %d is incomplete: %r' % (idx, p)
        (pb, xb, yb), (pe, _xe, ye) = p['B'], p['E']
        width = _WIDTH_OF[env]
        m = Meas()
        m.idx, m.env, m.label, m.npage, m.width = idx, env, label, nb, width
        m.page = pb if pb == pe else '%d-%d' % (pb, pe)

        if env.startswith('sideways'):
            # A landscape float is rotated by the PDF after TeX has set it,
            # so \pdfsavepos reports its own frame and not the page's: the
            # page NUMBER is still right and the coordinates are not.  The
            # float is alone on its page by construction -- `rotating` gives
            # it `[p]` -- and it is the only rotated type there, so the
            # rotated lines of that page ARE the float.  Asserted, not
            # assumed, because two of them on one page would merge.
            assert len(sideways[pb]) == 1, (
                'page %d carries %d landscape tables (%r); this measurement '
                'identifies one by its rotation and cannot separate two'
                % (pb, len(sideways[pb]), sideways[pb]))
            got = [ln for ln in b
                   if ln['page'] == pb and abs(ln['dir'][1]) > 0.9]
            near = [r for r in rl.get(pb, [])]
        else:
            got = [ln for ln in b
                   if ln['page'] == pb and ln['box'][3] <= yb + 0.5
                   and (pb != pe or ln['box'][1] >= ye - 0.5)
                   and abs(ln['dir'][1]) < 0.1
                   and xb - WIDTH_TOL_PT <= ln['box'][0]
                   <= xb + width + WIDTH_TOL_PT]
            if pe != pb:                   # a float that ran over a page
                got += [ln for ln in b if ln['page'] == pe
                        and ln['box'][1] >= ye - 0.5
                        and abs(ln['dir'][1]) < 0.1
                        and xb - WIDTH_TOL_PT <= ln['box'][0]
                        <= xb + width + WIDTH_TOL_PT]
            near = [r for r in rl.get(pb, [])
                    if ye - 0.5 <= (r[1] + r[3]) / 2 <= yb + 0.5
                    and xb - WIDTH_TOL_PT <= r[0]
                    and r[2] <= xb + width + WIDTH_TOL_PT]
        assert got, 'no text at all inside %s' % label
        m.nline = len(got)

        # FLOOR, on the smallest LINE.
        m.min_pt, worst = min(((ln['size'], ln) for ln in got),
                              key=lambda t: t[0])
        m.min_text = worst['text'][:60]

        # Everything below is in the float's own reading frame.
        rd, cr = _axes(got[0]['dir'])
        ext = [_proj(ln['box'], rd) for ln in got]
        m.extent = max(e[1] for e in ext) - min(e[0] for e in ext)
        m.over = max(0.0, m.extent - width)

        # CLEAR, between printed TOKENS and only on the ROWS -- the lines
        # between the topmost and the bottommost rule the float draws.  A
        # caption set justified can shrink a word space to a fifth of a
        # point; that is a real defect and a different one, belonging to
        # whoever owns the prose, not to the column specification.
        band = [r for r in near
                if _proj(r, rd)[1] - _proj(r, rd)[0] >= 20.0
                and _proj(r, cr)[1] - _proj(r, cr)[0] <= 1.6]
        m.nrule = len(band)
        body = []
        if len(band) >= 2:
            vs = [(_proj(r, cr)[0] + _proj(r, cr)[1]) / 2 for r in band]
            lo, hi = min(vs), max(vs)
            body = [ln for ln in got
                    if lo - 0.5 <= sum(_proj(ln['box'], cr)) / 2 <= hi + 0.5]
        gaps = []
        for ln in body:
            runs = []
            for w in sorted(ln['words'], key=lambda w: _proj(w[:4], rd)[0]):
                u0, u1 = _proj(w[:4], rd)
                v = sum(_proj(w[:4], cr)) / 2
                if (runs and u0 - runs[-1][1] <= TOUCH_EM * ln['size']
                        and abs(v - runs[-1][2]) <= 0.3 * ln['size']):
                    runs[-1] = (runs[-1][0], max(runs[-1][1], u1),
                                runs[-1][2], runs[-1][3] + w[4])
                else:
                    runs.append((u0, u1, v, w[4]))
            for u, v in zip(runs, runs[1:]):
                if abs(u[2] - v[2]) > 0.3 * ln['size']:
                    continue           # a subscript is not beside its base
                gaps.append((round((v[0] - u[1]) / ln['size'], 4),
                             v[0] - u[1], u[3][-14:], v[3][:14]))
        if gaps:
            g = min(gaps)
            m.clear, m.clear_pt, m.clear_pair = g[0], g[1], (g[2], g[3])
        else:
            m.clear, m.clear_pt, m.clear_pair = None, None, None
        out[label] = m
    return out, stamp


def check(m, floor=FLOOR_PT, clear=CLEAR_EM, width_tol=WIDTH_TOL_PT,
          verbose=True):
    """The clauses, on one measured float.  Returns True."""
    # CLAUSE FLOOR.
    assert m.min_pt >= floor - 5e-3, (
        'the smallest line of type in %s prints at %.2f pt against a floor '
        'of %.2f pt: %r.  That is running prose a reader has to read, and no '
        'LaTeX warning says a word about it.'
        % (m.label, m.min_pt, floor, m.min_text))

    # CLAUSE CLEAR.
    if m.clear is None:
        state = ('NOT APPLICABLE (%d rules: no rows to measure between them)'
                 % m.nrule)
    else:
        assert m.clear >= clear - 5e-4, (
            'two printed values in %s stand %.3f em apart (%.2f pt) against '
            'a required %.3f em -- %r then %r -- which is tighter than the '
            'thin space this paper sets inside a value, so they read as one'
            % (m.label, m.clear, m.clear_pt, clear, m.clear_pair[0],
               m.clear_pair[1]))
        state = '%.3f em' % m.clear

    # CLAUSE WIDTH / ENV.  The content must fit the width the environment
    # promises, and that width is the environment's, not a measured one.
    assert m.over <= width_tol, (
        '%s is set in a %s, which gives it %.1f pt, and its content runs '
        '%.2f pt past that'
        % (m.label, m.env, m.width, m.over))
    if verbose:
        print('  %-16s %-15s p%-4s %4d lines %6.1f/%6.1f pt  min %5.2f pt  '
              'clear %s' % (m.label, m.env, m.page, m.nline, m.extent,
                            m.width, m.min_pt, state))
    return True


def epoch_clause(stamp):
    assert stamp.startswith(_EPOCH_STAMP), (
        'the PDF carries CreationDate %r, not the build\'s pinned %r: it was '
        'written without SOURCE_DATE_EPOCH and cleanregen will report it'
        % (stamp, _EPOCH_STAMP))
    return True


_DRIVES = {
    1: 'FLOOR  -- require a floor a hair above what each float prints at',
    2: 'CLEAR  -- require a clearance a hair above what each row has',
    3: 'WIDTH  -- stretch the content 1 pt past what its environment gives',
    4: 'ENV    -- measure a landscape float against one column',
    5: 'COUNT  -- lose one float from the parse',
    6: 'PROBE  -- drop one rendered line from the probe build',
    7: 'EPOCH  -- read the stamp of a PDF written without the pinned epoch',
}


def main(argv):
    here = os.path.abspath(argv[1] if len(argv) > 1 and argv[1][0] != '-'
                           else '.')
    outdir = (argv[2] if len(argv) > 2 and argv[2][0] != '-'
              else os.path.join(os.environ.get('TMPDIR', '/tmp'),
                                'tabfloor_r17'))
    drive = int(argv[argv.index('--drive') + 1]) if '--drive' in argv else 0
    print('tabfloor_r17: %s -> %s   floor %.2f pt, clearance %.3f em%s'
          % (here, outdir, FLOOR_PT, CLEAR_EM,
             '   DRIVE %d: %s' % (drive, _DRIVES[drive]) if drive else ''))
    fired = []
    try:
        ms, stamp = measure(here, outdir, drive=drive)
    except AssertionError as e:
        print('  FIRED (COUNT/PROBE): %s' % e)
        return 1
    try:
        epoch_clause('D:19700101000000Z' if drive == 7 else stamp)
    except AssertionError as e:
        print('  FIRED (EPOCH): %s' % e)
        fired.append('EPOCH')
    na = 0
    for lab in sorted(ms, key=lambda k: ms[k].idx):
        m = ms[lab]
        floor, clr, wtol = FLOOR_PT, CLEAR_EM, WIDTH_TOL_PT
        if drive == 1:
            floor = m.min_pt + 0.01
        if drive == 2 and m.clear is not None:
            clr = m.clear + 0.001
        if drive == 3:
            m.extent += m.width - m.extent + WIDTH_TOL_PT + 1.0
            m.over = m.extent - m.width
        if drive == 4 and m.env.startswith('sideways'):
            m.width, m.over = COL_PT, m.extent - COL_PT
        if m.clear is None:
            na += 1
        try:
            check(m, floor=floor, clear=clr, width_tol=wtol)
        except AssertionError as e:
            fired.append(lab)
            print('  FAIL %s: %s' % (lab, e))
    print('%d of %d floats fail; %d clause(s) NOT APPLICABLE'
          % (len([f for f in fired if f != 'EPOCH']), len(ms), na))
    return 1 if fired else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
