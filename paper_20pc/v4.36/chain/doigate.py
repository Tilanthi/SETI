#!/usr/bin/env python3
"""Submission gate, INVERTED: the paper may not promise a deposit that will
never exist -- and (r36) it may print NO placeholder or invented DOI anywhere.

★★★★ r36 (N4), AUTHOR RULING 2026-11-09: "the Zenodo DOI will be added after
acceptance."  The all-zeros placeholder that stood in the SIdeposit bibitem
(through \\SIdoi) is REMOVED from the manuscript, the deposit README, the
Zenodo metadata and the submission notes, and the paper says plainly that the
DOI will be added on acceptance.  D4 and the D1 exemption are restated:

  OLD D4  a placeholder DOI may stand in the manuscript if AUTHOR_ACTIONS.md
          names it as a blocker (an "ACKNOWLEDGED BLOCKER" pass); only
          `--submission` failed on it; the deposit, PDF and metadata were not
          scanned.
  NEW D4  NO placeholder DOI (all-zeros / XXXX / TBD / nnnn / "placeholder"
          suffix) and NO Zenodo DOI the author has not supplied appears in
          the manuscript (bibliography included), the PDF's text, the
          deposit (unpacked tree and every text member of the zip), the
          Zenodo metadata record, or the submission notes -- ever; there is
          no acknowledged-blocker pass any more.  The only Zenodo DOIs allowed
          are the two third-party ALMA documents, each inside its own
          \\bibitem (ALLOWED_ZENODO).
  NEW D5  the ruling's statement is present: the Data Availability statement
          says the DOI "will be added on acceptance" (once), the SIdeposit
          bibitem says "DOI to be added on acceptance" and prints no DOI or
          doi.org link, no \\SIdoi is defined, the deposit README cites the
          record with the same words, and the metadata's doi is null.
  OLD D1  "(up)on acceptance" is banned everywhere in the running text.
  NEW D1  the same ban, except for exactly the one sanctioned clause "DOI
          will be added on acceptance" (D5 requires it once; any other
          "on acceptance" -- "released on acceptance", a second DOI clause --
          still fails).
  `--drive N` (N = 1..8) plants one defect into the real sources in memory
  and must FAIL (gate.sh runs all eight); `--submission` is kept as an alias
  of the default run, which is now itself the submission check.

WHY THIS FILE CHANGED SIDES.  For several cycles this gate existed to FAIL
until an author minted a Zenodo DOI and pasted it into the Data Availability
statement.  On 2026-10-08 the author settled the question the other way:

    "For the Zenodo deposit, remove all traces of this offer from the paper,
     I will not be doing it."                            -- G. J. White

Independently of that instruction, Zenodo returns zero records for either
author and zero for the title, so the paper was promising something that did
not exist and was not going to.  A gate that waits for a DOI is therefore not
merely useless, it is pointed the wrong way: the risk is no longer a missing
identifier but a RETURNING PROMISE -- "the data release holds...", "deposited
for every crossing", "available on request" -- reintroduced by a later pass
that remembers the old wording and not the decision.

So the check is inverted.  It now asserts that the manuscript contains **no
unfulfilled promise of a deposit**, and that what replaced the promise is
still there.  That makes the instruction enforced rather than merely obeyed
once.

    python3 doigate.py                 # the gate, over the whole manuscript
    python3 doigate.py --list          # every phrase it looks for
    python3 doigate.py --selftest      # prove it fails, in every direction
    python3 doigate.py --submission    # (r36) an alias of the default run
    python3 doigate.py --drive N       # (r36) N = 1..8: one planted defect, must FAIL

WHAT IT CHECKS
  D1  no promissory phrase anywhere in the published text (comments and the
      bibliography excluded -- see below);
  D2  no DOI outside the bibliography.  A DOI in a `\\bibitem` is a citation
      to somebody else's published document (the ALMA Cycle 13 Handbook and
      Proposer's Guide both carry Zenodo DOIs and are real); a DOI in our own
      prose would be ours, and ours does not exist;
  D3  the Data Availability statement still carries the honest content that
      replaced the promise -- the public archive, the ancillary catalogues
      and the in-paper tables.  Without D3 the gate could be satisfied by
      deleting the statement, which is the failure mode that would follow
      most naturally from D1;
  D4  ★★★★ NO PLACEHOLDER DOI ANYWHERE, INCLUDING INSIDE A `\bibitem`.
      ADDED BY `r26-integrate`, 2026-10-23, BECAUSE **D2'S STATED REASON HAD
      EXPIRED AND NOTHING IN 44 GATES COULD SEE IT.**  D2 exempts a DOI in a
      `\bibitem` on the ground that *"a DOI in a `\bibitem` is a citation to
      somebody else's published document"*.  That was true when it was
      written.  Round 25 reversed the no-deposit decision, so the paper now
      cites **our own** deposit as White & Dey (2026) under the deliberate
      all-zeros placeholder (`zenodo.` + seven zeros) -- and D1, D2 and D3 all
      pass, correctly on their own clauses, while the premise of one of them
      is false.  A gate whose verdict is sound and whose reason is gone is
      this round's tenth of that species.
      D4 scans the manuscript WITHOUT stripping the bibliography, and treats
      an all-zeros / XXXX / TBD / nnnn suffix as a placeholder.  ★ SUPERSEDED
      r36 (top of this docstring: no acknowledged-blocker pass any more; the
      PDF, deposit, metadata and notes are scanned too).  Its verdict WAS:
        * placeholder present AND named in `AUTHOR_ACTIONS.md`  -> pass, and
          print it as an ACKNOWLEDGED BLOCKER, so the fact that the paper is
          not submittable is reported on every gate run instead of living in
          one person's memory;
        * placeholder present and NOT documented                -> FAIL;
        * `--submission`                                        -> FAIL on any
          placeholder at all.  That gives the author one command whose green
          verdict means "this may go to arXiv".

WHY COMMENTS ARE EXCLUDED FROM D1/D2 BUT NOT IGNORED
`%%` comments are instructions between authors and are not typeset, so a
comment that *records the decision* must not trip the gate -- and
`08_backmatter.tex` now carries exactly such a comment, quoting the
instruction.  A promise written only in a comment is not a promise to a
reader.  `strip_comments` is the same escape-aware stripper `figorphan.py`
uses, so `\\%` survives.
"""
import os
import re
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# D1.  Promissory phrases.
#
# ★ THE LIST IS DELIBERATELY MULTI-WORD.  The bare word "deposit" cannot be
#   banned: the injection appendix says, correctly and physically, that "the
#   injector deposits an unattenuated amplitude at the star" and that "a
#   fractional error eps deposits eps*S_c at the star".  Banning the stem
#   would either fail on good physics or force the physics to be reworded to
#   satisfy a gate, which is the wrong way round.  Every pattern below needs
#   an article, a possessive or a verb beside it, so it can only match a
#   sentence that is telling the reader where to GO.
PROMISES = [
    # ★ r28: `zenodo` is NO LONGER a promissory phrase.  The no-deposit decision
    #   this list was written for (2026-10-08) was reversed in round 25; the
    #   paper cites its own deposit (\citep{SIdeposit}), and Referee 1 sec. 6
    #   requires the Data Availability statement to IDENTIFY THE REPOSITORY.
    #   Naming where the archive is held is a fact, not a promise; the
    #   identifier itself is D4's business (the placeholder in the bibitem, an
    #   acknowledged blocker until the author mints the record).  Every
    #   genuinely promissory form stays banned below.
    (r'reference of record',             'claims a reference of record'),
    (r'\bminted\b',                      'promises a minted identifier'),
    (r'reviewer link',                   'promises a reviewer link'),
    (r'(?:up)?on\s+acceptance',          'promises something on acceptance'),
    (r'(?:available|obtainable)\s+(?:on|upon)\s+request',
     'says "available on request"'),
    (r'(?:available|obtainable)\s+from\s+the\s+authors',
     'says "available from the authors"'),
    (r'will\s+be\s+(?:deposited|released|made\s+available)',
     'promises a future deposit'),
    (r'the\s+data\s+release',            'points at "the data release"'),
    (r'the\s+released\s+catalogue',      'points at "the released catalogue"'),
    (r'the\s+released\s+ledger',         'points at "the released ledger"'),
    (r'the\s+deposited\s+catalogue',     'points at "the deposited catalogue"'),
    (r'the\s+deposited\s+ledger',        'points at "the deposited ledger"'),
    (r'\bin\s+the\s+deposit\b',          'points "in the deposit"'),
    (r'the\s+deposit\s+(?:says|carries|holds|contains|gives|stores|lists)',
     'says what "the deposit" carries'),
    # ★ THIS PATTERN CAUGHT ME OUT ON ITS FIRST RUN, which is the point of
    #   writing it before trusting it.  Its first form was
    #   `(?:are|is) deposited (?:for|with|system|row|window|block)`, and it
    #   fired on Appendix A's "The injected carriers are deposited WITH the
    #   correlator's own channel response" -- a true statement about the
    #   injection, not an offer of a file.  The tail is now the four ways this
    #   paper has actually written "this column is in the deposit", so the
    #   verb's object has to be a data product and not a response function.
    (r'(?:are|is)\s+deposited\s+(?:for\s+every|for\s+each|'
     r'system\s+by\s+system|row\s+by\s+row|window\s+by\s+window|'
     r'separately|as\s+a\s+file)',
     'says a quantity "is deposited"'),
    (r'the\s+release\s+(?:says|carries|holds|contains|gives|stores|lists|'
     r'records|flags)',
     'says what "the release" carries'),
    (r'supporting\s+data\s+(?:are|is)\s+available',
     'promises supporting data'),
    (r'frozen\s+release',                'points at a "frozen release"'),
]

# ---------------------------------------------------------------------------
# D2.  A DOI as the registries define it.  Allowed only inside a \bibitem.
DOI = re.compile(r'\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b')

# ---------------------------------------------------------------------------
# D3.  What must still be in the Data Availability statement.  These are the
# three things a reader can actually act on, so losing any of them would mean
# the promise had been deleted and nothing put in its place.
REQUIRED = (
    ('ALMA Science Archive', r'ALMA\s+Science\s+Archive'),
    ('the execution-block identifier as the retrieval key',
     r'execution[- ]block\s+identifier'),
    ('the crossing ledger named as an accompanying file',
     r'crossing\s+ledger'),
    ('a cross-reference to the master count table (the survey ledger)',
     r'\\ref\{tab:blockledger\}'),
)




# ---------------------------------------------------------------------------
# D4.  A DOI that is a placeholder rather than a record, or a Zenodo DOI the
# author has not supplied.  The suffix gives a placeholder away (all zeros, the
# form this project used until r36, or the forms a human writes when leaving a
# hole).  ★ The fixtures below build these strings by concatenation, so that
# a grep for the all-zeros DOI over the tree finds nothing at all.
Z = '10.5281/' + 'zenodo.'
PLACEHOLDER = re.compile(
    r'\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]*?'
    r'(?:0{4,}|[Xx]{3,}|TBD|tbd|[nN]{4,}|PLACEHOLDER|placeholder)'
    r'[-._;()/:A-Za-z0-9]*\b')
ZENODO = re.compile(r'\b10\.5281/zenodo\.[A-Za-z0-9]+')
#: The Zenodo DOIs the paper may print: published third-party documents, each
#: only inside its own \bibitem.  The deposit's own DOI joins this list on
#: acceptance, when the author supplies it (and D5 is restated with it).
ALLOWED_ZENODO = {Z + '18793803': 'ALMAHandbook', Z + '18793859': 'ALMAPropGuide'}
#: D5 / the D1 exemption: the ruling's statement, and only that statement.
SANCTIONED = re.compile(r'DOI\s+will\s+be\s+added\s+on\s+acceptance', re.I)
BIBNOTE = 'DOI to be added on acceptance'
#: What is shipped beside the PDF and must carry no placeholder either.
DEPOSIT_DIR = 'ALMA_Technosignatures_40pc'
DEPOSIT_ZIP = 'ALMA_Technosignatures_40pc.zip'
METADATA = 'zenodo_metadata_r30.json'
NOTES = ('OJA_SUBMISSION.md', 'ZENODO_UPLOAD.md', 'AUTHOR_ACTIONS.md',
         'ARXIV_UPLOAD.md', os.path.join('..', 'README.md'))
TEXT_EXT = ('.md', '.txt', '.csv', '.tsv', '.json', '.py', '.tex', '.cff',
            '.yml', '.yaml', '.sh', '')


def strip_comments(txt):
    """Drop TeX comments, honouring backslash escapes (\\% is not a comment)."""
    out = []
    for line in txt.split('\n'):
        i, esc = None, False
        for k, ch in enumerate(line):
            if esc:
                esc = False
                continue
            if ch == '\\':
                esc = True
            elif ch == '%':
                i = k
                break
        out.append(line if i is None else line[:i])
    return '\n'.join(out)


def strip_bibliography(txt):
    """Remove the reference list: its DOIs belong to other people's papers."""
    return re.sub(r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}',
                  '', txt, flags=re.S)


def dataavail(txt):
    """The body of \\section*{Data availability}, up to the next \\section.

    ★ Case-INSENSITIVE on the heading, and deliberately so.  The regex used to
    be pinned to one capitalisation, so re-casing the heading -- which is a
    matter of house style, no journal here having a rule about it -- returned
    the empty string.  That is caught by this gate's own assertion below, but
    only because somebody wrote that assertion; matching either form removes
    the trap instead of relying on it.
    """
    m = re.search(r'\\section\*\{Data availability\}(.*?)(?=\\section|\Z)',
                  txt, re.S | re.I)
    return m.group(1) if m else ''


def check(body):
    """D1-D3.  Return the list of failures.  Empty means the paper promises
    nothing.  `body` is published text: comments and bibliography removed.

    r36: the one sanctioned clause ("DOI will be added on acceptance") is
    taken out before D1 looks for "on acceptance"; D5 requires it, once.
    """
    fail = []
    scan = SANCTIONED.sub('DOI-CLAUSE', body)
    for pat, why in PROMISES:
        for m in re.finditer(pat, scan, re.I):
            lo = max(0, m.start() - 60)
            fail.append('D1 %s: ...%s...'
                        % (why, ' '.join(scan[lo:m.end() + 40].split())))
    for d in DOI.findall(body):
        fail.append('D2 a DOI outside the bibliography: %s' % d)
    da = dataavail(body)
    if not da.strip():
        fail.append('D3 there is no Data Availability statement at all')
    else:
        for name, pat in REQUIRED:
            if not re.search(pat, da):
                fail.append('D3 the Data Availability statement no longer '
                            'carries %s' % name)
    return fail


def published():
    """The manuscript as a reader sees it."""
    return strip_bibliography(strip_comments(manuscript.flat()))


def with_bibliography():
    """The manuscript as a reader sees it, BIBLIOGRAPHY INCLUDED (D4/D5)."""
    return strip_comments(manuscript.flat())


def pdf_text():
    pdfs = sorted(f for f in os.listdir(HERE)
                  if re.match(r'technosignatures_40pc_v[\d.]+\.pdf$', f))
    if len(pdfs) != 1:
        return None
    import subprocess
    r = subprocess.run(['pdftotext', '-q', os.path.join(HERE, pdfs[0]), '-'],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def shipped():
    """{label: text} for everything shipped beside the manuscript."""
    import zipfile
    out = {}
    d = os.path.join(HERE, DEPOSIT_DIR)
    for root, _dirs, files in os.walk(d):
        for f in files:
            if os.path.splitext(f)[1] in TEXT_EXT:
                p = os.path.join(root, f)
                out['deposit/' + os.path.relpath(p, d)] = open(p, errors='ignore').read()
    zp = os.path.join(HERE, DEPOSIT_ZIP)
    if os.path.exists(zp):
        with zipfile.ZipFile(zp) as z:
            for n in z.namelist():
                if os.path.splitext(n)[1] in TEXT_EXT and not n.endswith('/'):
                    out['zip:' + n] = z.read(n).decode('utf-8', 'ignore')
    for f in (METADATA,) + NOTES:
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            out[f] = open(p, errors='ignore').read()
    return out


def bibitems(txt):
    """{key: text} of every \\bibitem (to the next \\bibitem or the end)."""
    out = {}
    for m in re.finditer(r'\\bibitem(?:\[[^]]*\])?\{([^}]*)\}(.*?)(?=\\bibitem|\\end\{thebibliography\}|\Z)',
                         txt, re.S):
        out[m.group(1)] = m.group(2)
    return out


def sources(drive=None):
    """The populations D4/D5 read, with drive N's one planted defect."""
    S = dict(tex=with_bibliography(), raw=manuscript.flat(), pdf=pdf_text(),
             published=published(), ship=shipped())
    ph = Z + '0' * 7
    if drive == 1:   # the v4.35 bibitem back
        S['tex'] = S['tex'].replace(BIBNOTE, 'doi:' + ph, 1)
    elif drive == 2:  # the v4.35 deposit README citation back
        k = 'deposit/README.md'
        S['ship'][k] = S['ship'].get(k, '') + '\nCite as: Zenodo, doi:' + ph + '\n'
    elif drive == 3:  # a placeholder in the PDF's text only
        S['pdf'] = (S['pdf'] or '') + '\ndoi:' + Z + 'XXXXXXX\n'
    elif drive == 4:  # the metadata record carrying a doi again
        S['ship'][METADATA] = S['ship'].get(METADATA, '') + '\n"doi": "' + ph + '"\n'
    elif drive == 5:  # an invented (non-placeholder) Zenodo DOI in the bibitem
        S['tex'] = S['tex'].replace(BIBNOTE, 'doi:' + Z + '1234567', 1)
    elif drive == 6:  # the ruling's statement deleted from Data Availability
        S['published'] = SANCTIONED.sub('DOI is pending', S['published'])
    elif drive == 7:  # a second promise "on acceptance" (D1 exemption is one clause)
        da = dataavail(S['published'])
        S['published'] = S['published'].replace(
            da, da + '\nThe catalogue will be released on acceptance.\n')
    elif drive == 8:  # an allowed third-party DOI moved out of its own bibitem
        S['ship']['OJA_SUBMISSION.md'] = S['ship'].get('OJA_SUBMISSION.md', '') + '\n' + Z + '18793803\n'
    return S


def check_d4d5(S):
    """D4 (no placeholder / unsupplied Zenodo DOI anywhere) and D5 (the
    ruling's statement present).  Returns the list of failures."""
    fail = []
    pops = [('manuscript (with bibliography)', S['tex'])]
    if S['pdf'] is None:
        fail.append('D4 cannot read the PDF text (pdftotext / no single '
                    'technosignatures_40pc_v*.pdf): the PDF is unchecked')
    else:
        pops.append(('PDF text', S['pdf']))
    pops += sorted(S['ship'].items())
    for name, txt in pops:
        for d in sorted(set(PLACEHOLDER.findall(txt))):
            fail.append('D4 a PLACEHOLDER DOI in %s: %s' % (name, d))
    # unsupplied Zenodo DOIs: in the manuscript only inside the owner bibitem;
    # in the PDF only the allowed ones; anywhere shipped, none at all
    bib = bibitems(S['tex'])
    body_wo_bib = strip_bibliography(S['tex'])
    for d in sorted(set(ZENODO.findall(S['tex']))):
        own = ALLOWED_ZENODO.get(d)
        if own is None:
            fail.append('D4 a Zenodo DOI the author has not supplied, in the '
                        'manuscript: %s' % d)
        elif d not in bib.get(own, '') or d in body_wo_bib:
            fail.append('D4 %s is allowed only inside \\bibitem{%s}' % (d, own))
    for d in sorted(set(ZENODO.findall(S['pdf'] or ''))):
        if d not in ALLOWED_ZENODO:
            fail.append('D4 a Zenodo DOI the author has not supplied, in the '
                        'PDF text: %s' % d)
    for name, txt in sorted(S['ship'].items()):
        for d in sorted(set(ZENODO.findall(txt))):
            fail.append('D4 a Zenodo DOI in %s (nothing shipped may carry one '
                        'until the author supplies it): %s' % (name, d))
    # D5
    n = len(SANCTIONED.findall(dataavail(S['published'])))
    if n != 1:
        fail.append('D5 the Data Availability statement says the DOI "will be '
                    'added on acceptance" %d times (must be once)' % n)
    if len(SANCTIONED.findall(S['published'])) != n:
        fail.append('D5 the "will be added on acceptance" clause appears '
                    'outside the Data Availability statement')
    sid = bib.get('SIdeposit')
    if sid is None:
        fail.append('D5 there is no \\bibitem{SIdeposit}')
    else:
        rest = sid.replace(BIBNOTE, '')
        if BIBNOTE not in sid or re.search(r'doi|\\href', rest, re.I):
            fail.append('D5 the SIdeposit bibitem must say "%s" and print no '
                        'DOI or link: %s' % (BIBNOTE, ' '.join(sid.split())[:120]))
    if re.search(r'\\(?:new|renew|provide)command\{?\\SIdoi\b', S['raw']):
        fail.append('D5 \\SIdoi is defined again (a DOI macro with no DOI)')
    rd = S['ship'].get('deposit/README.md', '')
    if BIBNOTE not in rd:
        fail.append('D5 the deposit README does not cite the record with '
                    '"%s"' % BIBNOTE)
    if S['ship'].get('zip:' + DEPOSIT_DIR + '/README.md', rd) != rd:
        fail.append('D5 the zip README differs from the unpacked one')
    mt = S['ship'].get(METADATA)
    if mt is not None:
        import json
        try:
            mj = json.loads(mt)
            if mj.get('doi') is not None:
                fail.append('D5 the Zenodo metadata record carries a doi: %r'
                            % mj.get('doi'))
        except ValueError:
            fail.append('D5 the Zenodo metadata record is not valid JSON')
    return fail


def main():
    drive = None
    if '--drive' in sys.argv:
        drive = int(sys.argv[sys.argv.index('--drive') + 1])
    S = sources(drive)
    fail = check(S['published']) + check_d4d5(S)
    print('doigate (inverted): the paper may promise no deposit, and may print '
          'no placeholder or unsupplied DOI%s'
          % ('' if drive is None else ' [drive %d]' % drive))
    for f in fail:
        print('  FAIL  %s' % f)
    if fail:
        print('\nFAILED: %s' % '; '.join(sorted({f.split()[0] for f in fail})))
        print('%d problem(s).  DO NOT SUBMIT, and do not "fix" this by '
              'whitelisting.' % len(fail))
        raise SystemExit(1)
    if drive is not None:
        print('drive %d did not fire' % drive)
        raise SystemExit(0)
    print('  PASS  no promissory phrase, no DOI of ours in the running text, '
          'the Data Availability statement still names what a reader can '
          'obtain, no placeholder or unsupplied DOI in the manuscript, PDF, '
          'deposit, metadata or notes (%d shipped files read), and the DOI is '
          'stated to be added on acceptance' % len(S['ship']))


def listing():
    print('doigate looks for %d promissory patterns:' % len(PROMISES))
    for pat, why in PROMISES:
        print('  %-55s %s' % (pat, why))
    print('(exempt: the one clause %s)' % SANCTIONED.pattern)
    print('and requires the Data Availability statement to keep:')
    for name, pat in REQUIRED:
        print('  %-55s %s' % (pat, name))
    print('D4 placeholder pattern %s; allowed Zenodo DOIs %s'
          % (PLACEHOLDER.pattern, ALLOWED_ZENODO))


def selftest():
    """Rule 9: a check that cannot fail is not a check.  Both directions.

    The fixtures marked HISTORICAL are the real sentences this paper carried
    before 2026-10-08.  They are kept here on purpose: the gate's whole job is
    to recognise them if they ever come back, and a fixture invented for the
    occasion would not prove that.
    """
    live = published()
    da_ok = dataavail(live)
    assert da_ok.strip(), 'the live Data Availability statement is empty'

    def with_sentence(s):
        """Put one sentence into the live Data Availability statement."""
        return live.replace(da_ok, da_ok + '\n' + s + '\n')

    cases = [
        ('the live manuscript', live, True),
        # ---- HISTORICAL, v4.15 and earlier -------------------------------
        ('HISTORICAL the reference-of-record sentence',
         with_sentence('The reference of record is a single permanent Zenodo '
                       'deposit, cited by its DOI.'), False),
        ('HISTORICAL "the data release holds the per-window decision tree"',
         with_sentence('The data release holds the per-window decision '
                       'tree.'), False),
        ('HISTORICAL "both are deposited for every crossing"',
         with_sentence('Both are deposited for every crossing.'), False),
        ('HISTORICAL "the deposit says which of the two each row is"',
         with_sentence('The deposit says which of the two each row is.'),
         False),
        ('HISTORICAL "the \\NWindows windows of the released catalogue"',
         with_sentence('They are the windows of the released catalogue.'),
         False),
        ('HISTORICAL "a DOI minted on acceptance"',
         with_sentence('The deposit carries a DOI minted on acceptance.'),
         False),
        ('HISTORICAL "versions recorded in the frozen release"',
         with_sentence('Exact versions are recorded in the frozen release.'),
         False),
        # ---- the substitutions nobody has authorised ---------------------
        ('a real DOI of ours pasted in',
         with_sentence('The deposit is ' + Z + '14087731.'), False),
        ('"available on request"',
         with_sentence('The catalogue is available on request from the '
                       'authors.'), False),
        ('"will be deposited"',
         with_sentence('The catalogue will be deposited at publication.'),
         False),
        ('"a reviewer link is provided"',
         with_sentence('A private reviewer link is provided.'), False),
        # ---- D3: the promise deleted and nothing put in its place --------
        ('the Data Availability statement emptied',
         live.replace(da_ok, '\n'), False),
        ('the archive no longer named',
         live.replace('ALMA Science Archive', 'archive'), False),
        # ★★ r26-integrate, 2026-10-23: THIS CASE COULD NOT FAIL, AND IT HAS
        # BEEN SAYING SO.  It replaced `\\ref{tab:ledger}`, which is not in
        # the manuscript -- the Data Availability statement cites
        # `tab:blockledger`, `tab:projcodes` and `tab:counts` -- so the
        # substitution was a no-op, the body was unchanged, and the case
        # "expect fail" got "pass".  `--selftest` therefore printed
        # **THE CHECK IS BROKEN** and exited 1 in the PUSHED v4.26 tree, where
        # it was invisible because `gate.sh` runs `doigate.py` without
        # `--selftest`.  A self-test nothing runs is a check that cannot fail,
        # twice over.  Repointed at the string REQUIRED actually looks for,
        # and `--selftest` is now a clause in `gate.sh`.
        ('the master-count cross-reference removed',
         live.replace('\\ref{tab:blockledger}', 'the count table'), False),
        # ---- the two false positives the gate must NOT produce -----------
        ('physics: "the injector deposits an amplitude"',
         with_sentence('The injector deposits an unattenuated amplitude at '
                       'the star.'), True),
        ('physics: "carriers are deposited with the channel response"',
         with_sentence('The injected carriers are deposited with the '
                       "correlator's own channel response."), True),
        ('physics: "a fractional error deposits eps S_c at the star"',
         with_sentence('A fractional error $\\epsilon$ deposits $\\epsilon '
                       'S_{\\rm c}$ at the star.'), True),
        ('a bibitem DOI (stripped with the bibliography)',
         live + '\n\\begin{thebibliography}{}\n\\bibitem[C]{H} Cortes P. C., '
                '2026, doi:' + Z + '18793803\n'
                '\\end{thebibliography}\n', True),
        ('the decision recorded in a %% comment',
         live + '\n%% the Zenodo deposit: Glenn will not be doing it.\n',
         True),
    ]
    # r36: the D1 exemption is ONE clause, not the phrase
    cases += [
        ('r36 the sanctioned "DOI will be added on acceptance" clause',
         with_sentence('Its DOI will be added on acceptance.'), True),
        ('r36 any other "on acceptance" still fails',
         with_sentence('The catalogue will be released on acceptance.'), False),
        ('r36 "the code is available on acceptance" fails',
         with_sentence('The code is available on acceptance.'), False),
    ]
    # ---- D4's pattern, both directions
    d4cases = [
        ('D4 the all-zeros placeholder inside a bibitem IS seen',
         '\\bibitem[White \\& Dey(2026)]{SIdeposit} 2026, doi:' + Z + '0' * 7, True),
        ('D4 a real minted DOI in a bibitem is NOT a placeholder',
         '\\bibitem[C]{H} Cortes P. C., 2026, doi:' + Z + '18793803', False),
        ('D4 XXXX form', 'see doi:' + Z + 'X' * 7, True),
        ('D4 NNNN form (ZENODO_UPLOAD.md wrote it)', 'of the form ' + Z + 'N' * 7, True),
        ('D4 TBD form', 'see doi:10.1234/some-record-TBD', True),
        ('D4 an ordinary journal DOI is not a placeholder',
         'see doi:10.1093/mnras/stac1234', False),
    ]
    ok = True
    for name, body, should_hit in d4cases:
        hit = bool(PLACEHOLDER.search(body))
        if hit != should_hit:
            ok = False
        print('  %s %-58s expect %-4s got %s'
              % ('ok ' if hit == should_hit else 'BAD', name,
                 'hit' if should_hit else 'miss', 'hit' if hit else 'miss'))
    # ---- D4/D5 on the real sources: live passes, every drive fails
    for dv in [None] + list(range(1, 9)):
        f = check_d4d5(sources(dv)) + (check(sources(dv)['published']) if dv in (6, 7) else [])
        good = (not f) if dv is None else bool(f)
        if not good:
            ok = False
        print('  %s %-58s expect %-4s got %-4s %s'
              % ('ok ' if good else 'BAD', 'D4/D5 live sources' if dv is None
                 else 'D4/D5 drive %d planted' % dv,
                 'pass' if dv is None else 'fail', 'pass' if not f else 'fail',
                 '' if not f else '| ' + f[0][:90]))
    for name, body, should_pass in cases:
        body = strip_bibliography(strip_comments(body))
        fail = check(body)
        passed = not fail
        if passed != should_pass:
            ok = False
        print('  %s %-58s expect %-4s got %-4s %s'
              % ('ok ' if passed == should_pass else 'BAD', name,
                 'pass' if should_pass else 'fail',
                 'pass' if passed else 'fail',
                 '' if passed else '| ' + fail[0][:90]))
    print('selftest: %s' % ('every direction behaves' if ok
                            else 'THE CHECK IS BROKEN'))
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
    if '--list' in sys.argv:
        listing()
        raise SystemExit(0)
    main()
