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
    python3 doigate.py --submission    # D4 is fatal: is this submittable?

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
      all-zeros placeholder `10.5281/zenodo.0000000` -- and D1, D2 and D3 all
      pass, correctly on their own clauses, while the premise of one of them
      is false.  A gate whose verdict is sound and whose reason is gone is
      this round's tenth of that species.
      D4 scans the manuscript WITHOUT stripping the bibliography, and treats
      an all-zeros / XXXX / TBD / nnnn suffix as a placeholder.  Its verdict:
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
    ('the crossing ledger named as an accompanying file',
     r'crossing\s+ledger'),
    ('a cross-reference to the master count table', r'\\ref\{tab:counts\}'),
)


# ---------------------------------------------------------------------------
# D4.  A DOI that is a placeholder rather than a record.  The suffix is what
# gives it away: a minted Zenodo id is a 7-9 digit number that is not all
# zeros.  `0000000` is this project's deliberate choice precisely so that a
# forgotten replacement is a DEAD link and not a plausible one -- so the gate
# looks for exactly that, plus the three other forms a human writes when
# leaving a hole.
PLACEHOLDER = re.compile(
    r'\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]*?'
    r'(?:0{4,}|[Xx]{3,}|TBD|tbd|n{4,}|PLACEHOLDER|placeholder)'
    r'[-._;()/:A-Za-z0-9]*\b')
AUTHOR_ACTIONS = 'AUTHOR_ACTIONS.md'


def documented(doi):
    """Is this placeholder named in the author-actions file as a blocker?

    ★ The pass is CONDITIONAL on the documentation, and that is the whole
    design.  A gate that simply allowed the placeholder would restore the
    silence D4 exists to break; a gate that simply failed would make every
    run of a 44-gate suite red for a condition the author has already
    accepted, which trains people to ignore it.  Tying the pass to the
    written record means the only way to keep the build green is to keep the
    blocker written down.
    """
    p = os.path.join(HERE, AUTHOR_ACTIONS)
    if not os.path.exists(p):
        return False
    t = open(p, errors='ignore').read()
    return doi in t and re.search(r'blocker', t, re.I) is not None


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


def with_bibliography():
    """The manuscript as a reader sees it, BIBLIOGRAPHY INCLUDED.

    D4's population, and the reason it is a separate function: every other
    clause here deliberately looks away from the reference list, and D4 exists
    because that is where our own unminted DOI is.
    """
    return strip_comments(manuscript.flat())


def check_d4(strict=False):
    """D4: placeholder DOIs.  Returns (fatal, acknowledged)."""
    found = sorted(set(PLACEHOLDER.findall(with_bibliography())))
    fatal, ack = [], []
    for d in found:
        if strict:
            fatal.append('D4 a PLACEHOLDER DOI is still in the manuscript and '
                         'this is a --submission run: %s' % d)
        elif documented(d):
            ack.append(d)
        else:
            fatal.append('D4 a placeholder DOI is in the manuscript and it is '
                         'NOT recorded as a blocker in %s: %s'
                         % (AUTHOR_ACTIONS, d))
    return fatal, ack


def main():
    strict = '--submission' in sys.argv
    fail = check(published())
    d4fatal, d4ack = check_d4(strict)
    fail += d4fatal
    print('doigate (inverted): the paper may promise no deposit')
    for d in d4ack:
        print('  ACKNOWLEDGED BLOCKER  D4 %s is a placeholder; %s names it. '
              'The paper may NOT be submitted until it is minted or the '
              'paragraph and its bibitem are deleted together. '
              '`doigate.py --submission` fails while it is there.'
              % (d, AUTHOR_ACTIONS))
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
    print('  PASS  no promissory phrase, no DOI of ours in the running text, '
          'and the Data Availability statement still names what a reader can '
          'obtain%s'
          % (' -- but see the ACKNOWLEDGED BLOCKER above: this is NOT a '
             'submittable state' if d4ack else ''))


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
         live.replace('\\ref{tab:counts}', 'the count table'), False),
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
    # ---- D4's own cases.  They cannot go through `check()`, which strips the
    # bibliography on purpose, so they exercise the pattern and the
    # documentation condition directly.  Four directions, which is what the
    # clause has: a placeholder in a bibitem, a real DOI in a bibitem, a
    # placeholder in the running text, and the documentation condition itself.
    d4cases = [
        ('D4 placeholder inside a bibitem IS seen (D2 exempts it, D4 must not)',
         '\\bibitem[White \\& Dey(2026)]{SIdeposit} 2026, '
         'doi:10.5281/zenodo.0000000', True),
        ('D4 a real minted DOI in a bibitem is NOT a placeholder',
         '\\bibitem[C]{H} Cortes P. C., 2026, doi:10.5281/zenodo.18793803',
         False),
        ('D4 XXXX form', 'see doi:10.5281/zenodo.XXXXXXX', True),
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
    _doc = documented('10.5281/zenodo.0000000')
    _undoc = documented('10.5281/zenodo.9999999')
    if not (_doc and not _undoc):
        ok = False
    print('  %s %-58s expect hit  got %s'
          % ('ok ' if _doc else 'BAD',
             'D4 the live placeholder IS documented as a blocker',
             'hit' if _doc else 'miss'))
    print('  %s %-58s expect miss got %s'
          % ('ok ' if not _undoc else 'BAD',
             'D4 an undocumented placeholder would FAIL',
             'hit' if _undoc else 'miss'))
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
