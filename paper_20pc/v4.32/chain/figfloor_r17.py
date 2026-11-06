#!/usr/bin/env python3
r"""figfloor_r17.py -- is this figure's type big enough to read ON THE PAGE?

A drawing is emitted by matplotlib at some natural width and then scaled by
\includegraphics to whatever width the float gives it.  The type a reader sees
is therefore the type the generator asked for TIMES that ratio, and the ratio
is invisible from either end: the generator cannot see the float, the float
cannot see the artwork, and pdflatex reports neither.  A figure drawn for one
geometry and placed in another prints every label at half size with nothing in
the build able to notice -- which is exactly what had happened, in this paper,
to ten of eleven figures.

This module closes that loop for any generator that imports it.  Five clauses,
measured on the file that was actually written and on the manuscript that
actually places it:

  SCALE    the artwork's natural width must equal the width the float gives it
  FLOOR    no LINE of type may print below the floor once that scale is applied
  FLOAT    the manuscript must include the file exactly once, in the expected
           environment and at the expected width
  EPOCH    the PDF must carry the build's pinned creation date, so a generator
           run by hand reproduces the one `make_all.sh` writes
  FIT      (optional) no text may run off the canvas it is drawn on

FLOOR is measured the way `figlegible_r17.py` measures it -- the largest span
on each rendered line, which is the size at which that line reads, so a
mathtext subscript at 0.7 of its base does not condemn a legible label.  The
measurement is taken from the saved PDF rather than from the font sizes the
generator asked for: those are the input to the drawing, and a check that reads
its own input is not a check.

COL_PT and TEXT_PT are the class's own \columnwidth and \textwidth, measured
from a probe build of this manuscript, not assumed.
"""
import os
import re

COL_PT = 245.26653          # openjournal.cls, twocolumn: \the\columnwidth
TEXT_PT = 513.11743         # openjournal.cls, twocolumn: \the\textwidth

# make_all.sh pins this so every build stamps the same CreationDate into every
# PDF.  A generator run by hand does not inherit it, and matplotlib then writes
# the wall clock -- which makes the figure differ from the build's for no reason
# at all and shows up as a cleanregen failure days later.
BUILD_EPOCH = '1577836800'                      # 2020-01-01T00:00:00Z
_EPOCH_STAMP = 'D:20200101000000Z'

FLOOR_PT = 6.5              # the smallest type this paper sets in a figure
GATE_PT = 6.0               # what figlegible_r17.py fails at


def pin_epoch():
    """Pin SOURCE_DATE_EPOCH if the caller was not started by make_all.sh.

    Does not override one that is already set: the build's value wins, and a
    deliberate experiment with a different epoch stays possible.  The EPOCH
    clause below checks the stamp on the written file, not this variable, so
    the two cannot agree by construction.
    """
    os.environ.setdefault('SOURCE_DATE_EPOCH', BUILD_EPOCH)
    return os.environ['SOURCE_DATE_EPOCH']


def _sources(here):
    """The manuscript and every .tex it could place a float in, concatenated,
    with comment lines removed: a commented-out float is not a float."""
    main = [f for f in sorted(os.listdir(here))
            if f.startswith('technosignatures') and f.endswith('.tex')]
    assert len(main) == 1, 'cannot identify the manuscript: %r' % main
    src = ''
    for d in (here, os.path.join(here, 'sections')):
        if not os.path.isdir(d):
            continue
        for f in sorted(([_e for _e in os.listdir(d) if _e != 'numbers'] + [os.path.join('numbers', _e) for _e in (os.listdir(os.path.join(d, 'numbers')) if os.path.isdir(os.path.join(d, 'numbers')) else [])]), key=os.path.basename):
            if f.endswith('.tex'):
                src += open(os.path.join(d, f), encoding='utf-8',
                            errors='replace').read() + '\n'
    return re.sub(r'(?m)^\s*%.*$', '', src)


def placement(here, relpath, src=None):
    """Where does the manuscript put this figure, and how wide?

    Returns (env, frac, base_pt, target_pt, opt).  `env` is 'figure' or
    'figure*'; `target_pt` is the width \includegraphics will scale the
    artwork to.
    """
    src = _sources(here) if src is None else src
    hits = list(re.finditer(
        r'\\includegraphics\[([^\]]*)\]\{%s\}' % re.escape(relpath), src))
    assert len(hits) == 1, (
        '%s is included %d times in the manuscript; this check, and the type '
        'size it protects, assume exactly one' % (relpath, len(hits)))
    opt = hits[0].group(1)
    head = src[:hits[0].start()]
    env = ('figure*' if head.rfind(r'\begin{figure*}') > head.rfind(
        r'\begin{figure}') else 'figure')
    m = re.search(r'width\s*=\s*([0-9.]*)\s*\\(columnwidth|textwidth|linewidth)',
                  opt)
    assert m, 'cannot read a width out of \\includegraphics[%s]' % opt
    frac = float(m.group(1)) if m.group(1) else 1.0
    unit = m.group(2)
    if unit == 'linewidth':
        unit = 'textwidth' if env == 'figure*' else 'columnwidth'
    base = TEXT_PT if unit == 'textwidth' else COL_PT
    return env, frac, base, frac * base, opt


def lines_pt(pdfpath):
    """The size of every rendered LINE in a PDF, in its own points.

    The size of a line is the largest span on it: a mathtext subscript is a
    separate span at about 0.7 of its base, and reporting that as the size of
    the line would condemn every figure in the paper equally.
    """
    import pymupdf
    doc = pymupdf.open(pdfpath)
    page = doc[0]
    out, spans = [], []
    for blk in page.get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            on = [(s['size'], s['text'].strip(), s['bbox']) for s in ln['spans']
                  if s['text'].strip()]
            if on:
                out.append(max(on))
                spans += on
    wid, hei = page.rect.width, page.rect.height
    stamp = doc.metadata.get('creationDate') or ''
    doc.close()
    return out, spans, wid, hei, stamp


def fit_width(fig, target_pt, pad_in=0.0, iters=12, tol=1e-4):
    """Resize a figure so that `savefig(bbox_inches='tight')` writes EXACTLY
    `target_pt` points wide.

    A tight bounding box is whatever the content happens to need, so a figure
    saved that way has no width its author chose: it comes out at 229.7 pt,
    the float gives it 245.3, and every label in it is quietly magnified by
    1.068 -- or, with the margins the other way about, shrunk.  The trimmed
    width is affine in the canvas width (the axes scale with it, the label
    margins are fixed by the font), so a few fixed-point steps land on the
    target to better than a tenth of a point.  Deterministic, so the figure
    still regenerates byte for byte.
    """
    for _ in range(iters):
        fig.canvas.draw()
        w_in = fig.get_tightbbox(fig.canvas.get_renderer()).width + 2 * pad_in
        r = (target_pt / 72.0) / w_in
        if abs(r - 1.0) < tol:
            return w_in * 72.0
        sz = fig.get_size_inches()
        fig.set_size_inches(sz[0] * r, sz[1])
    raise AssertionError(
        'fit_width did not converge on %.3f pt: the trimmed width is not '
        'behaving affinely in the canvas width' % target_pt)


def save_to_width(fig, path, target_pt, iters=8, tol=0.01, **savekw):
    """Save with a tight bounding box, at exactly `target_pt` points wide.

    `fit_width` predicts the trimmed width from the renderer; this closes the
    last tenth of a point by measuring the FILE.  matplotlib's own tight-bbox
    pass is not quite the bbox the renderer reports -- the difference is a
    fifth of a point, which is nothing until a 6.50 pt label has to clear a
    6.50 pt floor and misses by 0.01.  Measuring the artefact rather than
    predicting it is the same discipline as the rest of this module.
    """
    import pymupdf
    pad = savekw.get('pad_inches', 0.0)
    fit_width(fig, target_pt, pad_in=pad)
    for _ in range(iters):
        fig.savefig(path, bbox_inches='tight', **savekw)
        doc = pymupdf.open(path)
        w = doc[0].rect.width
        doc.close()
        if abs(w - target_pt) < tol:
            return w
        sz = fig.get_size_inches()
        fig.set_size_inches(sz[0] * (target_pt / w), sz[1])
        fig.canvas.draw()
    raise AssertionError(
        'save_to_width did not converge: %.4f pt written against %.4f pt '
        'asked for' % (w, target_pt))


def check(path, here, relpath, floor=FLOOR_PT, expect_env='figure',
          expect_frac=1.0, scale_tol=0.02, tight=False, verbose=True):
    """The clauses, on the file just written.  Returns the scale.

    `tight=True` declares that the caller saves with `bbox_inches='tight'`.
    ★ The FIT clause is then SKIPPED AND SAID TO BE SKIPPED, because it
    cannot fail: a tight bounding box is fitted to the artists, so an
    over-long label enlarges the canvas instead of running off it, and a
    label that IS cut -- one clipped by its axes -- is dropped from the PDF
    altogether and cannot be measured there either.  Driving it on such a
    figure passes, which would make it a check that cannot fail dressed as a
    check that passed.  Both states are reported rather than hidden.
    """
    env, frac, base, target, opt = placement(here, relpath)

    # CLAUSE FLOAT.  Read from the manuscript -- a different file from the one
    # being checked, and not one this generator writes, so the check cannot
    # agree with itself.  Checked first: when the float is wrong the scale is
    # wrong too, and the scale is the symptom, not the diagnosis.
    assert env == expect_env and abs(frac - expect_frac) < 1e-9, (
        '%s is drawn for a %s at %g of the width, and the manuscript places '
        'it in a %s at [%s].  The artwork, the float and the caption must all '
        'three agree; a disagreement here is invisible to every other check '
        'in this build and silently halves the type.'
        % (relpath, expect_env, expect_frac, env, opt))

    lines, spans, nat, hei, stamp = lines_pt(path)
    assert lines, 'no text at all in %s' % path

    # CLAUSE SCALE.  The artwork must be drawn at the width it is placed at.
    scale = target / nat
    assert abs(scale - 1.0) < scale_tol, (
        '%s is %.2f pt wide and the float gives it %.2f pt, so every label in '
        'it prints at %.1f per cent of the size it was drawn at'
        % (relpath, nat, target, 100 * scale))

    # CLAUSE FLOOR.  Measured on the written file, after that scale.
    small = min(lines)
    assert small[0] * scale >= floor - 5e-3, (
        'the smallest line of type in %s prints at %.2f pt against a floor of '
        '%.2f pt (drawn %.2f, scale %.4f): %r.  A reader cannot read it and no '
        'LaTeX warning says so.'
        % (relpath, small[0] * scale, floor, small[0], scale, small[1][:40]))

    # CLAUSE FIT.  Nothing may run off the canvas.  Measured on the file for
    # the same reason as the floor: matplotlib keeps Text objects for ticks
    # outside the view and they report extents far off the figure, so the same
    # question asked of the artists answers it about labels that were never
    # drawn.  A label that grows past the edge is CLIPPED in the PDF, and
    # neither an overlap check nor a vertical-containment check can see it:
    # there is nothing out there for it to collide with.
    # ★ The tolerance is a fraction of the span's own size, not a constant:
    #   a PDF span box is the font's EM box, so it stands proud of the ink by
    #   the ascender and descender, while matplotlib's tight bounding box is
    #   drawn round the ink.  A tight-bbox figure therefore has every edge
    #   label a point or so "outside" the page and is not clipped at all.
    off = [] if tight else [
        (t[1][:30], tuple(round(v, 1) for v in t[2])) for t in spans
        if t[2][0] < -0.35 * t[0] or t[2][2] > nat + 0.35 * t[0]
        or t[2][1] < -0.35 * t[0] or t[2][3] > hei + 0.35 * t[0]]
    assert not off, (
        'text runs off the %.1f x %.1f pt canvas of %s and is clipped: %r'
        % (nat, hei, relpath, off[:5]))

    # CLAUSE EPOCH.  On the stamp in the file, not on the variable that set it.
    assert stamp.startswith(_EPOCH_STAMP), (
        '%s carries CreationDate %r, not the build\'s pinned %r.  It was '
        'written without SOURCE_DATE_EPOCH, so it differs from the one '
        'make_all.sh writes and cleanregen will report it.'
        % (relpath, stamp, _EPOCH_STAMP))

    if verbose:
        print('  %-26s %-7s %7.2f pt / %7.2f pt  scale %.4f  smallest line '
              '%.2f pt (%.2f drawn)  %d lines  FIT %s'
              % (os.path.basename(relpath), env, nat, target, scale,
                 small[0] * scale, small[0], len(lines),
                 'NOT APPLICABLE (tight bbox: the clause cannot fail)'
                 if tight else 'checked'))
    return scale


def no_overlap(texts, fig, clear=1.2):
    """CLAUSE CLASH: no label may land on another.

    Artist extents, not PDF span boxes: a PDF span box is the font's full em
    box, so two labels a comfortable line apart overlap in it and the same
    question asked of the file reports a collision on every figure in the
    paper.  Ticks outside the view are dropped, because matplotlib keeps their
    Text objects alive, places them off the canvas and never draws them.
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    W = fig.get_figwidth() * fig.dpi
    H = fig.get_figheight() * fig.dpi
    box = [(t, t.get_window_extent(renderer=rend)) for t in texts
           if t.get_visible() and t.get_text().strip()]
    box = [(t, b) for t, b in box
           if b.x1 > 0 and b.x0 < W and b.y1 > 0 and b.y0 < H]
    bad = []
    for i in range(len(box)):
        for j in range(i + 1, len(box)):
            a, b = box[i][1], box[j][1]
            # `clear` is a REQUIRED CLEARANCE, not a tolerated overlap: two
            # tick labels that merely touch read as one number -- 240 beside
            # 320 reads "240320" -- so bare non-intersection is not the test.
            if (a.x0 < b.x1 + clear and b.x0 < a.x1 + clear
                    and a.y0 < b.y1 + clear and b.y0 < a.y1 + clear):
                bad.append((box[i][0].get_text()[:24],
                            box[j][0].get_text()[:24],
                            round(max(b.x0 - a.x1, a.x0 - b.x1), 2)))
    assert not bad, (
        'labels collide or sit closer than %.1f px in the rendered figure: %r'
        % (clear, bad[:6]))
    return True
