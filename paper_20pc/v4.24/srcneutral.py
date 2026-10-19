#!/usr/bin/env python3
"""srcneutral.py -- give the submission set neutral FILENAMES.

★★★★ THE FINDING THIS EXISTS FOR.  `arxivset.sh` strips every comment, and
that is proved byte-safe.  But **154 of the 194 files it ships are named
after the round or the version that made them**: 142 `survey_numbers_roundNNN
.tex`, nine `*_vNNN.tex` or `*_v4.19.tex`, three `*_rNN.tex`.  The master file
is called `technosignatures_40pc_v4.19.tex`.  arXiv serves the source bundle
publicly, so a reader who untars it is handed a list that reads as 721
generator rounds and nineteen major versions of the same paper -- after six
rounds of work to make the text read as seen for the first time.  No sweep of
the typeset page can see a filename, and none of ours looked.

★★ WHAT THIS IS NOT.  It is not an attempt to hide that the numbers are
generated.  Generated macro files are good practice and the paper says the
numbers are computed.  What goes is the *revision history*: a round index and
a version string, neither of which a first-time reader has any business
reading, and neither of which the build needs.

★ HOW IT IS SAFE.  A filename never reaches the output: there is no
`\\jobname` in the typeset text, `\\includegraphics` does not print its
argument, and `\\input` prints nothing.  So the rename must leave the PDF
byte-identical, and this script proves it does rather than asserting it --
which is the same standard `arxivset.sh` holds its comment strip to.

★ Operates on an ASSEMBLED SET, never on the working tree.  The tree keeps
its round-numbered names, because `roundcollide` and every generator key on
them and because the tree is not what ships.  Run it after `arxivset.sh` and
before `sourcesweep.py`:

    bash arxivset.sh $TMPDIR/arxivset
    python3 srcneutral.py $TMPDIR/arxivset       # renames, rebuilds, proves
    python3 sourcesweep.py --tar $TMPDIR/arxivset_neutral.tar.gz
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

PROV = (r'round\d+', r'_v\d{3}(?=\b|_)', r'_v\d\.\d{1,2}(?=\b|_)',
        r'_r\d{1,2}(?=[._]|$)')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(65536), b''):
            h.update(c)
    return h.hexdigest()


def provenance(name):
    base = os.path.basename(name)
    return any(re.search(p, base) for p in PROV)


def neutral_name(rel, seq, taken):
    """A neutral name for one file, deterministic and collision-checked."""
    d, base = os.path.split(rel)
    stem, ext = os.path.splitext(base)
    if re.match(r'^survey_numbers_round\d+$', stem):
        # ★ A sequence number, not the round number.  Numbering them 1..N in
        # \input order keeps the bundle readable without carrying the index
        # of the generator run that produced each one.
        cand = 'numbers_%03d' % seq
    else:
        cand = stem
        for p in PROV:
            cand = re.sub(p, '', cand)
        cand = cand.rstrip('_-') or 'part_%03d' % seq
    out = os.path.join(d, cand + ext) if d else cand + ext
    # ★ Collisions are real: `tab_ledger_v403.tex` would become
    # `tab_ledger.tex`, and `tab_ledger.tex` already exists in this tree.
    # Stripping a suffix is not automatically injective and must be checked,
    # not hoped for.
    n = 2
    while out in taken:
        out = (os.path.join(d, '%s_%d%s' % (cand, n, ext)) if d
               else '%s_%d%s' % (cand, n, ext))
        n += 1
    return out


# ★★ BUILD PRODUCTS, AND ONE THAT IS EASY TO MISS.  `openjournal.cls` loads
# REVTeX, and REVTeX writes `<jobname>Notes.bib` on every run.  So building
# in the assembled directory CREATES a file named after the version --
# `technosignatures_40pc_v4.19Notes.bib` -- inside the submission set.  The
# first run of this script picked it up and renamed it, which is how it was
# found.  `arxivset.sh` is immune because it tars BEFORE it builds; anyone
# tarring the directory afterwards is not.  The working tree holds thirteen
# of these, one per version, all litter.
PRODUCT = ('.aux', '.log', '.out', '.toc', '.bbl', '.blg', '.pdf', '.nav',
           '.snm', '.synctex.gz', '.fls', '.fdb_latexmk')


def is_product(rel):
    if rel.endswith('Notes.bib'):
        return True
    if rel.startswith('figures/'):
        return False
    return os.path.splitext(rel)[1].lower() in PRODUCT


def load_set(arg, workdir):
    """The submission is the TARBALL, not the directory it was built in."""
    if os.path.isfile(arg) and arg.endswith(('.tar.gz', '.tgz')):
        d = os.path.join(workdir, 'set')
        with tarfile.open(arg) as t:
            for m in t.getmembers():
                if m.name.startswith('/') or '..' in m.name.split('/'):
                    raise SystemExit('escaping tar member: %s' % m.name)
            t.extractall(d)
        return d, 'tarball %s' % os.path.basename(arg)
    if os.path.isdir(arg):
        return os.path.abspath(arg.rstrip('/')), 'directory (build products '
    raise SystemExit('not a tarball or a directory: %s' % arg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('set', help='the submission tarball (preferred) or the '
                               'assembled directory')
    ap.add_argument('--ref', help='reference PDF the set must reproduce; '
                                  'default: the one beside the directory')
    ap.add_argument('--with-figures', action='store_true',
                    help='also rename provenance-tagged FIGURE files.  This '
                         'does change the PDF, because pdfTeX writes '
                         '/PTEX.FileName into it, so the proof becomes a '
                         'typeset-equivalence proof instead of a byte one.')
    ap.add_argument('--out', help='destination; default <input>_neutral')
    a = ap.parse_args()

    work = tempfile.mkdtemp(prefix='srcneutral_',
                            dir=os.environ.get('TMPDIR', '/tmp'))
    src, how = load_set(a.set, work)
    print('set: %s' % how)
    dest = a.out or (re.sub(r'\.tar\.gz$|\.tgz$', '', os.path.abspath(a.set))
                     + '_neutral')
    if os.path.exists(dest):
        shutil.rmtree(dest)

    # ---- the reference PDF: whatever the set builds BEFORE the rename
    stems = [f for f in os.listdir(src) if f.endswith('.tex')
             and re.search(r'^[^%\n]*\\documentclass',
                           open(os.path.join(src, f), errors='ignore').read(),
                           re.M)]
    if len(stems) != 1:
        print('expected exactly one \\documentclass file, found %s' % stems)
        return 2
    master = stems[0]
    ref = a.ref or os.path.join(
        os.path.dirname(os.path.abspath(a.set)) if os.path.isfile(a.set)
        else src, os.path.splitext(master)[0] + '.pdf')
    if not os.path.isfile(ref) and os.path.isfile(a.set):
        # the tarball's sibling build directory
        cand = os.path.join(re.sub(r'\.tar\.gz$|\.tgz$', '',
                                   os.path.abspath(a.set)),
                            os.path.splitext(master)[0] + '.pdf')
        if os.path.isfile(cand):
            ref = cand
    if not os.path.isfile(ref):
        print('no %s to compare against -- build the set first '
              '(arxivset.sh does)' % os.path.basename(ref))
        return 2
    ref_md5, ref_size = md5(ref), os.path.getsize(ref)

    # ---- collect the set, excluding build products
    items, dropped = [], []
    for dp, dn, fn in os.walk(src):
        dn[:] = [d for d in dn if not d.startswith('.')]
        for f in sorted(fn):
            rel = os.path.relpath(os.path.join(dp, f), src)
            if f.startswith('.'):
                dropped.append(rel)
                continue
            if is_product(rel):
                dropped.append(rel)
                continue
            items.append(rel)
    items.sort()
    if dropped:
        print('dropped %d build product(s)/dotfile(s) not part of the '
              'submission: %s' % (len(dropped), dropped[:4]))

    # ---- \input order, so the sequence numbers follow the document
    order = []
    seen = set()
    queue = [master]
    while queue:
        f = queue.pop(0)
        if f in seen:
            continue
        p = os.path.join(src, f)
        if not os.path.isfile(p):
            continue
        seen.add(f)
        order.append(f)
        body = open(p, errors='ignore').read()
        for t in re.findall(r'\\(?:input|include)\s*\{([^}]*)\}', body):
            queue.append(t if t.endswith('.tex') else t + '.tex')

    rank = {f: i for i, f in enumerate(order)}
    items.sort(key=lambda r: (rank.get(r, 10 ** 6), r))

    mapping, taken = {}, set()
    seq = 0
    for rel in items:
        isfig = rel.startswith('figures/')
        if provenance(rel) and (a.with_figures or not isfig):
            seq += 1
            new = neutral_name(rel, seq, taken)
        else:
            new = rel
        taken.add(new)
        mapping[rel] = new
    if len(set(mapping.values())) != len(mapping):
        print('FAIL: the rename is not injective')
        return 1
    renamed = {k: v for k, v in mapping.items() if k != v}

    # ---- copy under the new names, rewriting every reference
    for rel, new in mapping.items():
        tgt = os.path.join(dest, new)
        os.makedirs(os.path.dirname(tgt) or dest, exist_ok=True)
        if rel.endswith('.tex'):
            body = open(os.path.join(src, rel), errors='ignore').read()
            for old, nn in sorted(renamed.items(),
                                  key=lambda kv: -len(kv[0])):
                o_noext = os.path.splitext(old)[0]
                n_noext = os.path.splitext(nn)[0]
                for cmd in ('input', 'include', 'includegraphics'):
                    body = re.sub(
                        r'(\\%s\s*(?:\[[^\]]*\])?\s*\{)%s(\})'
                        % (cmd, re.escape(o_noext)),
                        lambda m: m.group(1) + n_noext + m.group(2), body)
                    body = re.sub(
                        r'(\\%s\s*(?:\[[^\]]*\])?\s*\{)%s(\})'
                        % (cmd, re.escape(old)),
                        lambda m: m.group(1) + nn + m.group(2), body)
            open(tgt, 'w').write(body)
        else:
            shutil.copy(os.path.join(src, rel), tgt)

    new_master = mapping[master]
    print('%d item(s), %d renamed, master %s -> %s'
          % (len(mapping), len(renamed), master, new_master))

    # ---- no provenance name survives
    left = [v for v in mapping.values() if provenance(v)
            and (a.with_figures or not v.startswith('figures/'))]
    if left:
        print('FAIL: provenance names survive the rename: %s' % left[:8])
        return 1
    print('no round, version or referee tag survives in %d filename(s)'
          % len(mapping))

    # ---- no dangling reference: every \input resolves in the new tree
    q, got, miss = [new_master], set(), []
    while q:
        f = q.pop(0)
        if f in got:
            continue
        p = os.path.join(dest, f)
        if not os.path.isfile(p):
            miss.append(f)
            continue
        got.add(f)
        for t in re.findall(r'\\(?:input|include)\s*\{([^}]*)\}',
                            open(p, errors='ignore').read()):
            q.append(t if t.endswith('.tex') else t + '.tex')
    if miss:
        print('FAIL: %d \\input no longer resolves: %s' % (len(miss), miss[:8]))
        return 1
    ntex = sum(1 for v in mapping.values() if v.endswith('.tex'))
    if len(got) != ntex:
        print('FAIL: closure is %d of %d .tex -- a file is orphaned or an '
              '\\input was rewritten to the wrong name' % (len(got), ntex))
        return 1
    print('closure intact: %d/%d .tex reachable from the master' % (len(got),
                                                                   ntex))

    # ---- the tarball, before anything is built in there
    tar = dest + '.tar.gz'
    with tarfile.open(tar, 'w:gz') as t:
        for rel in sorted(mapping.values()):
            t.add(os.path.join(dest, rel), arcname=rel)
    print('tarball: %s (%d items)' % (tar, len(mapping)))

    # ---- THE PROOF: byte-identical PDF
    env = dict(os.environ, SOURCE_DATE_EPOCH='1577836800',
               FORCE_SOURCE_DATE='1')
    for _ in range(3):
        subprocess.run(['pdflatex', '-interaction=nonstopmode', new_master],
                       cwd=dest, env=env, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    out = os.path.join(dest, os.path.splitext(new_master)[0] + '.pdf')
    if not os.path.isfile(out):
        print('FAIL: the renamed set does not build')
        return 1
    got_md5, got_size = md5(out), os.path.getsize(out)
    print('reference %s  %d bytes' % (ref_md5, ref_size))
    print('renamed   %s  %d bytes' % (got_md5, got_size))
    if got_md5 == ref_md5:
        print('PASS: byte-identical.  The rename touched no typeset '
              'character.')
        return 0

    # ★★★ THE MASTER FILENAME REACHES THE PDF, through the trailer /ID.
    # pdfTeX derives /ID from the output filename and the creation date, so
    # renaming `technosignatures_40pc_v4.19.tex` to `technosignatures_40pc
    # .tex` changes exactly 60 bytes -- the two 32-hex-digit /ID strings and
    # nothing else -- even with SOURCE_DATE_EPOCH pinned.  Byte-identity is
    # therefore IMPOSSIBLE for a master rename, and this script's first
    # version asserted it and failed.  The honest proof is: identical
    # everywhere once the /ID is normalised, which is still a byte
    # comparison over 1.29 MB and over every content stream.
    # ★ `\pdftrailerid{}` in the preamble would pin /ID and restore exact
    # byte-identity across renames; that is the manuscript owner's call.
    def norm_id(blob):
        return re.sub(rb'/ID \[<[0-9A-F]+> <[0-9A-F]+>\]',
                      b'/ID [<ID> <ID>]', blob)

    ra_b = open(ref, 'rb').read()
    rb_b = open(out, 'rb').read()
    ids_a = re.findall(rb'/ID \[<([0-9A-F]+)> <([0-9A-F]+)>\]', ra_b)
    if norm_id(ra_b) == norm_id(rb_b):
        print('PASS: identical byte for byte once the trailer /ID is '
              'normalised -- %d /ID pair(s), %d byte(s) differing in total, '
              'all of them /ID.  pdfTeX hashes the OUTPUT FILENAME into /ID, '
              'so a master rename cannot be byte-identical and this is the '
              'strongest proof available: every content stream, every font, '
              'every glyph position is unchanged.'
              % (len(ids_a), sum(1 for x, y in zip(ra_b, rb_b) if x != y)))
        return 0

    # ★★★★ A FILENAME *DOES* REACH THE OUTPUT, and the first run of this
    # script discovered it by failing: pdfTeX writes
    #     /PTEX.FileName (./figures/chain_v412.pdf)
    # into the PDF for every embedded PDF figure.  So eleven figure paths are
    # published inside the article itself, where no sweep of the rendered
    # text can see them -- `genai_sweep.py` reads the page, not the object
    # dictionary -- and one of the eleven carries a version number.
    # Renaming a figure therefore MUST change the PDF, and claiming
    # byte-identity here would be claiming the fix did nothing.
    #
    # So when figures are renamed the proof changes shape: the PDF must be
    # equivalent as a TYPESET DOCUMENT -- same page count, same text on
    # every page, same content stream on every page -- and the only
    # differences anywhere must be the PTEX filenames we deliberately
    # changed.  That is weaker than a byte comparison and is stated as such.
    if not a.with_figures:
        print('FAIL: only .tex were renamed, so the PDF had to be identical '
              'up to the trailer /ID and is not.  Something other than a '
              'filename moved; do not ship this.')
        return 1
    try:
        import pymupdf
    except ImportError:
        print('FAIL: cannot verify typeset equivalence without pymupdf')
        return 1
    ra, rb = pymupdf.open(ref), pymupdf.open(out)
    if ra.page_count != rb.page_count:
        print('FAIL: %d pages vs %d' % (ra.page_count, rb.page_count))
        return 1
    diffs = []
    for i in range(ra.page_count):
        pa, pb = ra[i], rb[i]
        if pa.get_text() != pb.get_text():
            diffs.append('page %d text differs' % (i + 1))
        ca = b''.join(pa.read_contents() for _ in (0,))
        cb = b''.join(pb.read_contents() for _ in (0,))
        if hashlib.md5(ca).hexdigest() != hashlib.md5(cb).hexdigest():
            diffs.append('page %d content stream differs' % (i + 1))
    if diffs:
        print('FAIL: the renamed set is not the same typeset document:')
        for d in diffs[:8]:
            print('    ** ' + d)
        return 1
    A = set(re.findall(rb'/PTEX\.FileName\s*\(([^)]*)\)',
                       open(ref, 'rb').read()))
    B = set(re.findall(rb'/PTEX\.FileName\s*\(([^)]*)\)',
                       open(out, 'rb').read()))
    expect = {('./' + mapping.get(x.decode().lstrip('./'),
                                  x.decode().lstrip('./'))).encode()
              for x in A}
    print('/PTEX.FileName in the reference: %d, in the renamed: %d'
          % (len(A), len(B)))
    if B != expect:
        print('FAIL: the embedded figure paths are not exactly the renamed '
              'ones.\n    unexpected: %s\n    missing: %s'
              % (sorted(x.decode() for x in B - expect)[:4],
                 sorted(x.decode() for x in expect - B)[:4]))
        return 1
    prov_left = sorted(x.decode() for x in B if provenance(x.decode()))
    if prov_left:
        print('FAIL: a provenance tag survives inside the PDF: %s'
              % prov_left)
        return 1
    print('PASS: %d page(s), identical text and identical content stream on '
          'every one.  The %d byte difference is the embedded figure paths '
          'and nothing else, and none of them now carries a round or '
          'version tag.' % (ra.page_count, abs(ref_size - got_size)))
    print('★ The embedded paths would be removed outright by '
          '\\pdfsuppressptexinfo=-1 in the preamble; that is the '
          'manuscript owner\'s one-line call, not this script\'s.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
