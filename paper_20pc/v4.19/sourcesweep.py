#!/usr/bin/env python3
"""sourcesweep.py -- gate the SOURCE bundle, not the typeset page.

★★★ WHY THIS EXISTS.  The journal is an arXiv overlay, so the submission is
the LaTeX source and arXiv serves that source bundle publicly.  Every check
this paper has had until now reads the typeset PDF (`genai_sweep.py`,
`abswords.py`, the LaTeX log gate).  A PDF sweep cannot see a comment, a
filename, or a figure's metadata dictionary, and all three are published.

`arxivset.sh` already copies every `.tex` comment-stripped.  That is the fix;
this is the proof.  A strip with a bug still builds a byte-identical PDF if
the bug only *keeps* comments -- A8 compares output, and a comment produces no
output, so A8 is blind in exactly the direction that matters here.  Nothing
asserted that the assembled bundle was clean until this file.

★★ WHAT IT CHECKS, on the ASSEMBLED SET rather than on the working tree,
because the assembled set is what is published:
  S1  no comment survives: no unescaped `%` with anything after it
  S2  no identity in the text: agent, referee, round, version, path, star,
      second-person directive, instruction, TODO, repository, GenAI prompt
  S3  no filename carries a round, version or referee tag
  S4  no binary (figure) metadata carries a path, user, host or e-mail
  S5  nothing resembling a credential anywhere
  S6  the sweep is not vacuous -- see below

★★★★ S6, AND WHY IT IS THE MOST IMPORTANT CHECK HERE.  This project has
found twenty-odd gates that could not fail: one that skipped for ever, one
that enforced the defect it was written to catch, two blind on a hard-coded
filename, and one that passed for five rounds while the prose it was meant to
police named a different coefficient.  So:
  S6a  the file list is built by WALKING the set, never from a manifest the
       set itself ships, and it must be non-empty
  S6b  every file walked must be READ -- read_count == walk_count, asserted,
       so a silently-skipped extension cannot hide a leak
  S6c  every pattern family must match its own positive example.  A regex
       broken by an edit then fails this instead of passing everything
  S6d  the third-party allowlist is keyed on CONTENT (md5), not on name.  An
       edited `openjournal.cls` stops being allowlisted and gets scanned
  S6e  `--selftest` plants each defect family in a copy and requires the
       sweep to fail on it, one family at a time

Usage:
    python3 sourcesweep.py --set $TMPDIR/arxivset      # gate the submission
    python3 sourcesweep.py --tree .                    # advisory, working tree
    python3 sourcesweep.py --selftest                  # drive every family
"""

import argparse
import hashlib
import os
import re
import sys

# ---------------------------------------------------------------- allowlist
# ★ Keyed on md5, not on filename (S6d).  These two files are upstream and
# are not ours to launder: `openjournal.cls` is served by the journal and our
# copy is byte-identical to it, and `epsf.sty` is Rokicki's, carrying its
# maintainer's e-mail address in its own header.  An e-mail in a file the
# journal itself distributes is not evidence about us.  Change either file and
# the pin stops matching and the file is swept like any other.
# ★ The class md5 was re-verified against the journal's own download link,
# http://www.thphys.nuim.ie/staff/pcoles/openjournal.cls, on 2026-10-13:
# 52009 bytes, aa359396071034e4bd96379ff861deae, unchanged.
THIRD_PARTY = {
    'aa359396071034e4bd96379ff861deae': 'openjournal.cls (journal copy)',
    'dccf65c3a958c390cbc0f571186d67bc': 'epsf.sty (Rokicki/Beebe, upstream)',
}

TEXT_EXT = ('.tex', '.cls', '.sty', '.bib', '.bbl', '.bst', '.txt')
BIN_EXT = ('.pdf', '.png', '.jpg', '.jpeg')

# ------------------------------------------------------------- the patterns
# ★★ CASE.  Two of the sweep's own drives failed on their own planted line
# because the whole family set was matched case-sensitively: "You should not
# change this" does not match `\byou\b`, and "Per the brief" does not match
# `\bper the brief\b`.  So most families are now case-INSENSITIVE, and the
# two that depend on case say so: `star` (a literal glyph) and `directive`
# (which identifies a sentence-initial imperative BY its capital, and matched
# "never a spectral power density" the moment it was folded).
# CASE_SENSITIVE lists the families that must not be folded.
CASE_SENSITIVE = {'star', 'directive'}

# ★ Each entry is (family, regex, positive_example).  The example is not
# decoration: S6c requires the regex to match it, so a regex that stops
# working is caught by the gate rather than by the next reader of the arXiv
# source.  Keep the example realistic -- these are all real lines that were
# in this tree.
PATTERNS = [
    # ★ Generic `rNN-word`, not a list of the agents we happen to have.  The
    # first draft of this line enumerated them, and it missed `r16-referee`
    # -- an agent that exists -- on its own positive example.  A gate keyed
    # on a hard-coded list of the things it knows about is the species of
    # defect this project has found most often.
    ('agent', r'\br\d{1,2}-[a-z]{3,}\b|\bastra-[a-z]+\b|\bthe integrator\b'
              r'|\bthe coordinator\b|\bsub-?agent\b',
     '%% r16-referee: the point is KEPT'),
    ('referee', r'\breferee[s]?\b|\bR[12]-\d+\b|\bminor\s*\(?[a-h]\)?\b'
                r'|\brefere[ea]\b|\breviewer\b|\brebuttal\b|\bresponse letter\b',
     '%% cited (referee 2, minor 3).'),
    ('round', r'\bround[\s_-]?\d+\b|\bround\s+(?:one|two|three|four|five|six|'
              r'seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|'
              r'sixteen|seventeen)\b',
     '%% HANDOVER (04_method.tex, round 11)'),
    ('version', r'\bv\d\.\d{1,2}\b|\bv\d{3}\b|\bV\d{3}\b|\bversion\s+\d\.\d'
                r'|\bthe previous version\b',
     '%% supersedes the v4.10 text'),
    ('path', r'/workspace/|/shared/|/home/[a-z]|/root/|/Users/|/data/SETI'
             r'|\b[A-Za-z0-9_]+\.(?:md|py|sh|json|csv|log|aux)\b',
     '%% /workspace/SETI/referee_r11/INTEGRATION_QUEUE.md'),
    ('star', r'[★☆▶►]',
     '%% * r15-prose found that'.replace('*', '★')),
    # ★★ `\bDO NOT\b` was in this family, and the family is case-folded, so
    # it matched "the two do not partition the survey identically", "which
    # the injections do not model" and five more sentences of physics.
    # Shouting is a property of the capitals, so it belongs in `directive`,
    # which is case-sensitive.  All seven lines are now in the selftest's
    # negative corpus so the mistake cannot be made twice.
    ('handover', r'\bHANDOVER\b|\bREQUEST:|\bSUPERSED|\bsupersedes\b|\bOWNER'
                 r'\b|\bthe queue\b|\bTODO\b|\bFIXME\b'
                 r'|\bdo not (?:re-?run|edit|touch|delete|change)\b',
     '%% HANDOVER -- supersedes the round-10 note.'),
    # ★ SECOND PERSON ONLY, not "an imperative verb at the start of a line".
    # The first draft anchored imperatives with `^` under re.M and produced
    # five false positives at once -- "read window by window", "never a
    # spectral power density", "use identifiers alone" -- all ordinary prose
    # that happened to wrap onto a new line, or to begin one after a macro
    # was masked out.  A line is not a sentence.  Imperatives are therefore
    # matched only where they are unambiguous: at a sentence start, in the
    # fixed forms a handover note actually uses.
    ('person2', r'\byou\b|\byour\b|\byou\'re\b|\bdon\'t\b'
                r'|\bnote that you\b|\bif you\b',
     '%% Keep the thin space: you will lose the alignment otherwise'),
    # ★ Fixed-width lookbehinds only -- Python's `re` refuses a variable one,
    # so each alternative is its own.  `(?<=% )` is there because a directive
    # most often sits in a comment, and S1 would catch that only if the
    # comment survived the strip; this family has to work on prose too.
    ('directive', r'(?:^|(?<=[.!?]\s)|(?<=[.!?]\s\s)|(?<=% ))'
                  r'(?:Do not|DO NOT|Never |Always |Make sure|Be sure|'
                  r'Check that|Leave this|Keep this|Re-?run )'
                  r'|\bDO NOT\b',
     '% Do not re-run this generator after the freeze'),
    ('instruct', r'\bas instructed\b|\bper the brief\b|\bthe brief says\b'
                 r'|\b[A-Z][a-z]+\'s instruction\b|\bstanding instruction\b'
                 r'|\bstanding ruling\b|\bhis instruction\b',
     "%% Glenn's instruction: the appendices are deliberately detailed"),
    # ★ `\bbranch\b` was here and matched "a separate branch" and "the
    # bandpass branch fails by amplitude" -- two sentences of physics.  A
    # repository is named by its own words, not by a word it shares with the
    # rest of English.
    ('repo', r'\bgithub\b|\bgitlab\b|\bTilanthi\b|\bgit (?:commit|branch|'
             r'push|log)\b|\bcommit [0-9a-f]{7,}\b|\bpull request\b',
     '%% pushed as commit d19a4e3fad5b on the github repo'),
    # ★ "prompt" is an ordinary English verb and the paper uses it: "the one
    # that prompted it".  OJA bans *prompts in the text*, which is a prompt
    # addressed to a model, so the word is only evidence in that company.
    ('genai', r'\bprompt(?:s|ed|ing)?\s+(?:the\s+)?(?:model|assistant|'
              r'agent|LLM|system|tool)\b|\bsystem prompt\b'
              r'|\bprompt (?:template|engineering)\b'
              r'|\bLarge Language Model|\bLLM\b|\bChatGPT\b|\bClaude\b'
              r'|\bGPT-\d|\bas an AI\b|\bAI assistant\b|\bagent\b',
     '%% the agent was prompted the following system prompt'),
    ('notebook', r'\bwe (?:now|then) (?:tried|found|changed|fixed)\b'
                 r'|\bthis used to\b|\bit turned out\b|\bI (?:found|wrote|'
                 r'fixed|checked)\b|\bmy own\b',
     '%% I found this the hard way; it used to be a typed literal'),
]

CRED = [
    ('token', r'\bghp_[A-Za-z0-9]{16,}|\bgithub_pat_[A-Za-z0-9_]{20,}'
              r'|\bAKIA[0-9A-Z]{16}\b|\bsk-[A-Za-z0-9]{20,}'
              r'|\bxox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY'
              r'|\bssh-rsa AAAA[0-9A-Za-z+/]{20,}',
     'ghp_0123456789abcdefghij'),
    ('secretword', r'(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|'
                   r'password|passwd|bearer)\b\s*[:=]',
     'api_key = 1234'),
]

# ★ Filenames.  These ship: a reader untars the bundle and sees the list.
# 142 files called `survey_numbers_roundNNN.tex` and a master called
# `..._v4.19.tex` are a machine-made revision history in the published set,
# which no sweep of the typeset page can see.
FNAME = [
    ('fname_round', r'round\d+', 'survey_numbers_round103.tex'),
    ('fname_ver', r'_v\d{3}\b|_v\d\.\d{1,2}\b',
     'technosignatures_40pc_v4.19.tex'),
    ('fname_ref', r'_r\d{1,2}(?:[._]|$)', 'tab_persys_r17.tex'),
]

# ★ Binary metadata.  A matplotlib figure carries Creator/Producer, and a
# figure saved by some other tool can carry the author's home directory or
# login name in /Title or /Author.  Nothing checked this before.
BINMETA = [
    ('meta_path', rb'/(?:home|Users|workspace|shared)/[A-Za-z0-9_.-]{2,}',
     b'/home/glenn/fig.py'),
    ('meta_mail', rb'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
     b'someone@example.org'),
    ('meta_host', rb'(?i)/Author\s*\(|/Title\s*\([^)]*(?:draft|referee|round)',
     b'/Author (someone)'),
]


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def comment_leaks(text):
    """Lines with an unescaped `%` that still have content after it."""
    out = []
    for i, line in enumerate(text.split('\n'), 1):
        j, n = 0, len(line)
        while j < n:
            if line[j] == '\\':
                j += 2
                continue
            if line[j] == '%':
                if line[j + 1:].strip():
                    out.append((i, line[j:][:90]))
                break
            j += 1
    return out


# ★ The declaration's own words, as OJA's guidelines ask for them.  Matched
# on the run-in heading rather than on a filename: a gate keyed on
# `sections/08_backmatter.tex` goes blind the day the back matter is renamed,
# and this project has had two gates fail exactly that way.
DECL_OPEN = re.compile(r'Use of generative artificial intelligence', re.I)
DECL_SHUT = re.compile(r'\\(?:section|subsection|appendix|end\s*\{document\})'
                       r'|\\bibitem', re.I)


def genai_zone(text):
    """The span of the mandated declaration, or None.

    Bounded by the construct, not by a line count: it opens at the run-in
    heading and shuts at the next sectioning command or the bibliography.
    Returning None is a finding in itself -- see S7.
    """
    m = DECL_OPEN.search(text)
    if not m:
        return None
    shut = DECL_SHUT.search(text, m.end())
    return (m.start(), shut.start() if shut else len(text))


def mask(text):
    """Blank the places a false positive lives, before the identity sweep.

    ★ Macro NAMES are masked.  `\\FixMedRank` contains `fixme`,
    `\\EtaStraddle` contains `astra` and `\\RfiNullMaxMean` contains `llm`;
    all three are real macros in this paper and all three matched a naive
    sweep.  A gate that cries wolf 200 times gets switched off, which is a
    way of having no gate.  `\\url{...}` is masked for the same reason -- a
    DOI is allowed to contain anything.
    """
    text = re.sub(r'\\url\s*\{[^}]*\}', ' ', text)
    text = re.sub(r'\\href\s*\{[^}]*\}', ' ', text)
    return re.sub(r'\\[A-Za-z@]+', ' ', text)


class Sweep:
    def __init__(self, root, advisory=False):
        self.root = os.path.abspath(root)
        self.advisory = advisory
        self.walked = []
        self.read = []
        self.skipped = []
        self.allowed = []
        self.fails = []
        self.notes = []
        self.declared = 0

    def add(self, fam, path, line, snippet):
        self.fails.append((fam, os.path.relpath(path, self.root), line,
                           snippet))

    # ------------------------------------------------------------- walking
    def walk(self):
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames
                           if d not in ('.git', '__pycache__')]
            for fn in filenames:
                self.walked.append(os.path.join(dirpath, fn))
        self.walked.sort()

    def run(self):
        self.walk()
        if not self.walked:
            self.fails.append(('S6a', '-', 0,
                               'the set is EMPTY: nothing was swept'))
            return
        for p in self.walked:
            rel = os.path.relpath(p, self.root)
            ext = os.path.splitext(p)[1].lower()
            dig = md5(p)
            if dig in THIRD_PARTY:
                self.allowed.append((rel, THIRD_PARTY[dig]))
                self.read.append(p)
                self.scan_names(rel, p)
                continue
            if ext in TEXT_EXT:
                self.scan_text(rel, p)
                self.read.append(p)
            elif ext in BIN_EXT:
                self.scan_binary(rel, p)
                self.read.append(p)
            else:
                # ★ NOT a silent skip.  An extension this gate does not know
                # how to read is itself a finding: it ships, and nobody has
                # looked inside it.  S6b would otherwise pass by shrinking
                # the denominator, which is how a gate goes vacuous.
                self.skipped.append(rel)
                self.read.append(p)
                self.add('S6b-unknown', p, 0,
                         'extension %r is not swept; it still ships' % ext)
            self.scan_names(rel, p)
        # ★★ S7: THE MANDATED DECLARATION MUST EXIST.  Without this the
        # allow-zone above would be a hole: delete the declaration and the
        # sweep would pass while the paper became unacceptable to the
        # journal for the opposite reason.  Exactly one is wanted -- two
        # would mean the acknowledgements say it twice.
        if self.declared != 1:
            self.fails.append((
                'S7-declaration', '-', 0,
                'OJA requires a generative-AI declaration in the '
                'acknowledgements and this set contains %d. "%s" was not '
                'found exactly once.' % (self.declared,
                                         DECL_OPEN.pattern)))

        # S6b: read every file walked
        if len(self.read) != len(self.walked):
            self.fails.append(('S6b', '-', 0,
                               'walked %d files but read %d'
                               % (len(self.walked), len(self.read))))

    # -------------------------------------------------------------- text
    def scan_text(self, rel, path):
        raw = open(path, errors='ignore').read()
        for line, snip in comment_leaks(raw):
            self.add('S1-comment', path, line, snip)
        masked = mask(raw)
        lines = masked.split('\n')
        zone = genai_zone(masked)
        if zone:
            self.declared += 1
        for fam, pat, _ex in PATTERNS:
            flags = re.M if fam in CASE_SENSITIVE else re.M | re.I
            for m in re.finditer(pat, masked, flags):
                # ★★★★ OJA REQUIRES A GENERATIVE-AI DECLARATION AND BANS
                # EVIDENCE OF GENERATIVE AI IN THE SAME PARAGRAPH OF its
                # guidelines.  So a gate that simply banned the vocabulary
                # would fail the compliant paper -- and this one did, the
                # moment the mandated declaration was written: it reported
                # "Large language models were used in this work" as a leak.
                # The declaration is therefore an allow-zone, bounded by the
                # construct that introduces it rather than by a line number,
                # and `S7` below requires the zone to EXIST, so the
                # allowance cannot be what makes the sweep pass.
                if fam == 'genai' and zone and zone[0] <= m.start() < zone[1]:
                    continue
                ln = masked.count('\n', 0, m.start()) + 1
                self.add('S2-' + fam, path, ln, lines[ln - 1].strip()[:90])
        for fam, pat, _ex in CRED:
            for m in re.finditer(pat, raw):
                self.add('S5-' + fam, path, raw.count('\n', 0, m.start()) + 1,
                         '<redacted %d chars -- treat as live>'
                         % (m.end() - m.start()))

    # ------------------------------------------------------------ binary
    def scan_binary(self, rel, path):
        blob = open(path, 'rb').read()
        for fam, pat, _ex in BINMETA:
            for m in re.finditer(pat, blob):
                self.add('S4-' + fam, path, 0,
                         m.group(0).decode('latin-1')[:90])
        for fam, pat, _ex in CRED:
            for m in re.finditer(pat.encode(), blob):
                self.add('S5-' + fam, path, 0, '<redacted, binary>')

    # ----------------------------------------------------------- filenames
    def scan_names(self, rel, path):
        for fam, pat, _ex in FNAME:
            if re.search(pat, os.path.basename(rel)):
                self.add('S3-' + fam, path, 0, rel)


def selfcheck_patterns():
    """S6c: every regex must match its own positive example."""
    bad = []
    for fam, pat, ex in PATTERNS:
        flags = re.M if fam in CASE_SENSITIVE else re.M | re.I
        if not re.search(pat, ex, flags):
            bad.append('%s does not match its own example %r' % (fam, ex))
    # ★★ And the converse, on a REAL line from the paper.  `directive` is
    # the one family that depends on case, and the guard that proves it must
    # name the line it protects: Appendix A has a sentence that begins
    # "never a spectral power density", wrapped onto its own line, and an
    # earlier draft of this gate reported it as a handover directive.  The
    # guard asserts both halves -- unfolded it must miss, folded it must hit
    # -- so neither "simplify the flags" nor "the anchor is enough" can
    # quietly make it vacuous.
    REAL = 'never a spectral power density; flatness is exact only for a tone'
    _dir = next(p for f, p, _ in PATTERNS if f == 'directive')
    if re.search(_dir, REAL, re.M) is not None:
        bad.append('directive fires on real prose unfolded: %r' % REAL)
    if re.search(_dir, REAL, re.M | re.I) is None:
        bad.append('this guard has gone vacuous: folding `directive` no '
                   'longer produces the false positive it exists to '
                   'prevent, so the CASE_SENSITIVE entry is unmotivated '
                   'and must be re-derived rather than trusted')
    for group in (CRED, FNAME):
        for fam, pat, ex in group:
            if not re.search(pat, ex):
                bad.append('%s does not match its own example %r' % (fam, ex))
    for fam, pat, ex in BINMETA:
        if not re.search(pat, ex):
            bad.append('%s does not match its own example %r' % (fam, ex))
    return bad


def report(sw, label):
    print('=== sourcesweep: %s (%s)' % (label, sw.root))
    print('    %d file(s) walked, %d read, %d allowlisted upstream, '
          '%d unknown extension' % (len(sw.walked), len(sw.read),
                                    len(sw.allowed), len(sw.skipped)))
    for rel, why in sw.allowed:
        print('    upstream, md5-pinned: %s -- %s' % (rel, why))
    fams = {}
    for fam, rel, ln, snip in sw.fails:
        fams.setdefault(fam, []).append((rel, ln, snip))
    for fam in sorted(fams):
        rows = fams[fam]
        print('    ** %-18s %4d hit(s)' % (fam, len(rows)))
        for rel, ln, snip in rows[:6]:
            print('         %s:%s  %s' % (rel, ln or '-', snip))
        if len(rows) > 6:
            print('         ... and %d more' % (len(rows) - 6))
    if not sw.fails:
        print('    clean')
    return fams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', help='assembled submission directory to gate')
    ap.add_argument('--tar', help='the submission TARBALL -- the preferred '
                                  'mode: it holds exactly what is uploaded')
    ap.add_argument('--tree', help='working tree, advisory only')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--drive', type=int, default=None,
                    help='plant defect family N and require a FAIL')
    a = ap.parse_args()

    bad = selfcheck_patterns()
    if bad:
        print('S6c FAIL: a pattern no longer matches its own example:')
        for b in bad:
            print('    ** ' + b)
        return 2
    print('S6c PASS: %d pattern families each match their own example'
          % (len(PATTERNS) + len(CRED) + len(FNAME) + len(BINMETA)))

    if a.selftest:
        return selftest()

    if a.tree:
        sw = Sweep(a.tree, advisory=True)
        sw.run()
        report(sw, 'WORKING TREE (advisory -- this is not what ships)')
        print('advisory: exit 0 regardless; the working tree is allowed to '
              'carry a working record.')
        return 0

    if a.tar:
        # ★★ THE TARBALL IS THE RIGHT THING TO SWEEP, and gating the
        # directory instead is a mistake this gate made on its first run.
        # `arxivset.sh` writes the tarball and THEN builds in the same
        # directory, so by the time anyone looks the directory also holds a
        # .aux, a .log, a .out and a .pdf -- and the sweep dutifully reported
        # four findings against files that are not in the submission at all,
        # including an `/Author(` in the PDF it had just built itself.
        # Sweeping the artefact that is uploaded removes the whole class.
        import shutil
        import tarfile
        import tempfile
        d = tempfile.mkdtemp(prefix='sweeptar_',
                             dir=os.environ.get('TMPDIR', '/tmp'))
        try:
            with tarfile.open(a.tar) as t:
                names = [m.name for m in t.getmembers()]
                for n in names:
                    if n.startswith('/') or '..' in n.split('/'):
                        print('refusing a tarball with an escaping member: %s'
                              % n)
                        return 2
                t.extractall(d)
            sw = Sweep(d)
            sw.run()
            report(sw, 'SUBMISSION TARBALL %s' % os.path.basename(a.tar))
            if sw.fails:
                print('sourcesweep: FAIL -- %d finding(s).  This tarball is '
                      'what arXiv publishes.' % len(sw.fails))
                return 1
            print('sourcesweep: PASS')
            return 0
        finally:
            shutil.rmtree(d, ignore_errors=True)

    if not a.set:
        print('nothing to do: pass --set, --tar, --tree or --selftest')
        return 2

    sw = Sweep(a.set)
    sw.run()
    report(sw, 'ASSEMBLED SUBMISSION SET')
    if sw.fails:
        print('sourcesweep: FAIL -- %d finding(s).  This bundle is what '
              'arXiv publishes.' % len(sw.fails))
        return 1
    print('sourcesweep: PASS')
    return 0


# ----------------------------------------------------------------- selftest
DRIVES = [
    ('comment leak', 'sections/intro.tex',
     lambda t: t + '\n%% r17-source: a comment that must not ship\n',
     'S1-comment'),
    ('agent name in text', 'sections/intro.tex',
     lambda t: t + '\nThe r16-prose pass rewrote this.\n', 'S2-agent'),
    ('referee in text', 'sections/intro.tex',
     lambda t: t + '\nAs referee 2 asked in minor (c), we restate it.\n',
     'S2-referee'),
    ('round number', 'sections/intro.tex',
     lambda t: t + '\nThis was settled in round 11 of the analysis.\n',
     'S2-round'),
    ('version string', 'sections/intro.tex',
     lambda t: t + '\nSuperseding the v4.10 text entirely.\n', 'S2-version'),
    ('absolute path', 'sections/intro.tex',
     lambda t: t + '\nSee /workspace/SETI/referee_r11/notes for the detail.\n',
     'S2-path'),
    ('star marker', 'sections/intro.tex',
     lambda t: t + '\n★ the point is kept.\n', 'S2-star'),
    ('second person', 'sections/intro.tex',
     lambda t: t + '\nYou should not change the thin space here.\n',
     'S2-person2'),
    ('directive', 'sections/intro.tex',
     lambda t: t + '\nDo not re-run the generator after the freeze.\n',
     'S2-directive'),
    ('repository', 'sections/intro.tex',
     lambda t: t + '\nThe code is on github for the record.\n', 'S2-repo'),
    ('genai prompt', 'sections/intro.tex',
     lambda t: t + '\nWe prompted the model for a summary.\n', 'S2-genai'),
    ('instruction', 'sections/intro.tex',
     lambda t: t + "\nPer the brief, the appendices stay detailed.\n",
     'S2-instruct'),
    ('credential', 'sections/intro.tex',
     lambda t: t + '\nghp_0123456789abcdefghijkl\n', 'S5-token'),
    ('provenance filename', '__new__:survey_numbers_round999.tex',
     lambda t: '\\newcommand{\\Zzz}{1}\n', 'S3-fname_round'),
    ('figure metadata', '__bin__:figures/leak.pdf',
     lambda t: None, 'S4-meta_path'),
    ('empty set', '__empty__', lambda t: None, 'S6a'),
    ('unknown extension', '__new__:notes.tar',
     lambda t: 'binary-ish\n', 'S6b-unknown'),
    # ★ The allow-zone's two failure directions, both driven.
    ('declaration deleted', 'sections/back.tex',
     lambda t: t.replace('Use of generative artificial intelligence', 'Notes'),
     'S7-declaration'),
    ('declaration twice', '__new__:sections/extra.tex',
     lambda t: 'Use of generative artificial intelligence is declared.\n',
     'S7-declaration'),
    ('genai outside the zone', 'sections/intro.tex',
     lambda t: 'Large language models wrote this section.\n' + t,
     'S2-genai'),
]


def _clean_set(d):
    """★★★ A SYNTHETIC CLEAN SET, built here rather than copied.

    The drives used to be planted in a copy of the real assembled set, and
    five of seventeen then reported FAIL for the wrong reason: the family
    they planted was *already* firing on the real set, so the drive proved
    nothing either way.  That is the vacuity trap in its subtlest form -- a
    drive that cannot distinguish its own defect from the background.

    So the baseline is constructed to be clean, and the selftest ASSERTS it
    sweeps clean before planting anything.  If this corpus ever stops being
    clean, every drive below is meaningless and the selftest says so instead
    of printing a pass.
    """
    os.makedirs(os.path.join(d, 'sections'), exist_ok=True)
    os.makedirs(os.path.join(d, 'figures'), exist_ok=True)
    open(os.path.join(d, 'paper.tex'), 'w').write(
        '\\documentclass{openjournal}\n'
        '\\input{numbers}%\n'
        '\\begin{document}\n\\input{sections/intro}%\n'
        '\\input{sections/back}%\n'
        '\\includegraphics{figures/plot.pdf}\n'
        '\\end{document}\n')
    open(os.path.join(d, 'numbers.tex'), 'w').write(
        '\\newcommand{\\NWin}{402}\n'
        '\\newcommand{\\FixMedRank}{0.476}\n'
        '\\newcommand{\\EtaStraddle}{1.46}\n'
        '\\newcommand{\\RfiNullMaxMean}{2.4}\n')
    # ★★★ THE NEGATIVE CORPUS.  Every line here is a REAL sentence from this
    # paper that some draft of this gate reported as a leak.  They are kept
    # verbatim so that the next person who widens a pattern, folds a case or
    # "simplifies the flags" is told at once, instead of handing a reviewer
    # fourteen false positives and watching the gate get switched off.  A
    # gate's negative corpus is as load-bearing as its positive one, and
    # this project has never kept one before.
    open(os.path.join(d, 'sections', 'intro.tex'), 'w').write(
        'Narrowband searches above 30 GHz have covered one line.\n'
        'We read window by window the same diagnostic flags.\n'
        'It is never a spectral power density, and the two overlap\n'
        'and must not be added.  The bandpass branch fails by amplitude.\n'
        'We use identifiers alone, not names.  The one that prompted it\n'
        'was the control field.  Always-on carriers are not assumed.\n'
        'A criterion instead; the two do not partition the survey\n'
        'identically.  The third the injections do not model.  A crossing\n'
        'whose discovery products do not survive is not counted.  An\n'
        'amplitude factor describes a source those windows do not hold.\n'
        'The coincidences, and the one species we do not read as emission.\n'
        'The reserved hold-out is drawn as a separate branch of the tree.\n'
        'Systems never observed twice are declared, and no limit moves.\n')
    # ★ The corpus must carry the MANDATED declaration, or S7 fires on the
    # baseline and every drive below becomes untestable.  It is also the
    # allow-zone's only positive example.
    open(os.path.join(d, 'sections', 'back.tex'), 'w').write(
        'This work used the ALMA Science Archive.\n\n'
        '\\emph{Use of generative artificial intelligence.} Large language\n'
        'models were used in this work.  They wrote most of the software\n'
        'and drafted text, which the authors revised.\n\n'
        '\\begin{thebibliography}{}\n\\bibitem[x]{x} X.\n'
        '\\end{thebibliography}\n')
    open(os.path.join(d, 'figures', 'plot.pdf'), 'wb').write(
        b'%PDF-1.4\n/Creator (Matplotlib v3.10.9, https://matplotlib.org)\n'
        b'%%EOF\n')


def selftest():
    """S6e: plant each defect family on its own and require a FAIL for it."""
    import shutil
    import tempfile
    tmproot = os.environ.get('TMPDIR', '/tmp')

    # ---- the baseline must be clean, or nothing below means anything
    b = tempfile.mkdtemp(prefix='swbase_', dir=tmproot)
    try:
        base = Sweep(os.path.join(b, 'set'))
        _clean_set(base.root)
        base.run()
        if base.fails:
            print('S6e ABORT: the synthetic baseline is NOT clean, so every '
                  'drive below would be untestable.  Findings:')
            for f in base.fails[:12]:
                print('    ** %s %s:%s %s' % f)
            return 2
        print('S6e baseline: %d synthetic file(s), sweeps CLEAN -- including '
              'the six prose lines and three macro names that each produced '
              'a false positive in an earlier draft of this gate'
              % len(base.walked))
    finally:
        shutil.rmtree(b, ignore_errors=True)

    ok = bad = 0
    for name, target, fn, want in DRIVES:
        d = tempfile.mkdtemp(prefix='swdrive_', dir=tmproot)
        try:
            dest = os.path.join(d, 'set')
            if target == '__empty__':
                os.makedirs(dest)
            else:
                _clean_set(dest)
                if target.startswith('__new__:'):
                    q = os.path.join(dest, target.split(':', 1)[1])
                    os.makedirs(os.path.dirname(q) or dest, exist_ok=True)
                    open(q, 'w').write(fn(''))
                elif target.startswith('__bin__:'):
                    q = os.path.join(dest, target.split(':', 1)[1])
                    os.makedirs(os.path.dirname(q), exist_ok=True)
                    open(q, 'wb').write(
                        b'%PDF-1.4\n/Title (/home/glenn/fig.py)\n%%EOF\n')
                else:
                    q = os.path.join(dest, target)
                    open(q, 'w').write(fn(open(q, errors='ignore').read()))
            sw = Sweep(dest)
            sw.run()
            got = {f for f, _, _, _ in sw.fails}
            if want in got:
                ok += 1
                print('    drive PASS  %-22s -> %s fired' % (name, want))
            else:
                bad += 1
                print('    drive FAIL  %-22s -> wanted %s, got %s'
                      % (name, want, sorted(got)[:4]))
        finally:
            shutil.rmtree(d, ignore_errors=True)
    print('--- %d/%d drives fired on their own planted defect, from a '
          'baseline proved clean' % (ok, ok + bad))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
