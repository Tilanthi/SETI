#!/usr/bin/env python3
"""Submission gate, INVERTED: the paper may not promise a deposit that will
never exist.

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
      most naturally from D1.

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
    (r'zenodo',                          'names Zenodo'),
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
    ('a cross-reference to the crossing ledger', r'\\ref\{tab:ledger\}'),
    ('a cross-reference to the master count table', r'\\ref\{tab:counts\}'),
)


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
    """The body of \\section*{Data Availability}, up to the next \\section."""
    m = re.search(r'\\section\*\{Data Availability\}(.*?)(?=\\section|\Z)',
                  txt, re.S)
    return m.group(1) if m else ''


def check(body):
    """Return the list of failures.  Empty means the paper promises nothing.

    `body` is published text: comments and bibliography already removed.
    """
    fail = []
    for pat, why in PROMISES:
        for m in re.finditer(pat, body, re.I):
            lo = max(0, m.start() - 60)
            fail.append('D1 %s: ...%s...'
                        % (why, ' '.join(body[lo:m.end() + 40].split())))
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


def main():
    fail = check(published())
    print('doigate (inverted): the paper may promise no deposit')
    for f in fail:
        print('  FAIL  %s' % f)
    if fail:
        print('\n%d problem(s).  DO NOT SUBMIT, and do not "fix" this by '
              'whitelisting.' % len(fail))
        print('The author\'s instruction, 2026-10-08: "For the Zenodo '
              'deposit, remove all traces of this offer from the paper, I '
              'will not be doing it."')
        print('A quantity is either stated in the paper or it is not '
              'available.  There is no third option, and in particular '
              '"available on request" is not one.')
        raise SystemExit(1)
    print('  PASS  no promissory phrase, no DOI of ours, and the Data '
          'Availability statement still names what a reader can obtain')


def listing():
    print('doigate looks for %d promissory patterns:' % len(PROMISES))
    for pat, why in PROMISES:
        print('  %-55s %s' % (pat, why))
    print('and requires the Data Availability statement to keep:')
    for name, pat in REQUIRED:
        print('  %-55s %s' % (pat, name))


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
         with_sentence('The deposit is 10.5281/zenodo.14087731.'), False),
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
        ('the ledger cross-reference removed',
         live.replace('\\ref{tab:ledger}', 'the ledger'), False),
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
                '2026, doi:10.5281/zenodo.18793803\n'
                '\\end{thebibliography}\n', True),
        ('the decision recorded in a %% comment',
         live + '\n%% the Zenodo deposit: Glenn will not be doing it.\n',
         True),
    ]
    ok = True
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
