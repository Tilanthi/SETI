#!/usr/bin/env python3
"""Submission gate: the Data Availability statement must name a real DOI.

WHY THIS EXISTS.  The reproducibility argument of this paper is an address,
not an adjective, and for several cycles the Data Availability section said
the deposit "carries a DOI minted on acceptance" -- a promise in the place
where an identifier belongs.  A referee read that and asked, correctly, how
the reproducibility claims were to be checked during review.  The statement
now has the shape it must have in the journal version and is missing exactly
one string.  Nothing in the build can see that, because a missing identifier
is not a LaTeX error and not a number a macro gate can compare.

This is therefore deliberately NOT wired into `make_all.sh`: it fails today,
by design, and a gate that blocks every build until an author mints a DOI
would simply be switched off.  It belongs in the pre-submission checklist
(AUTHOR_ACTIONS.md item 1).  Run it, and do not submit while it fails:

    python3 doigate.py                 # check the live backmatter
    python3 doigate.py --selftest      # prove the check can fail AND pass

WHAT IT CHECKS
  D1  the Data Availability section contains a syntactically valid DOI
      (prefix 10.NNNN/, as registered by DataCite/Crossref);
  D2  that DOI is not one of the placeholder spellings this project has
      used, or might use, instead of a real one;
  D3  the section still names the deposit's contents, so that a DOI is not
      inserted into a statement that has meanwhile lost its inventory.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKMATTER = os.path.join(HERE, 'sections', '08_backmatter.tex')

#: a DOI as the registries define it: the "10." prefix, a 4-9 digit
#: registrant code, a slash, then a suffix of printable non-space characters.
DOI = re.compile(r'\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b')

#: spellings that look like a DOI and are not one.  "XXXX", "NNNN", "TBD"
#: and the bare Zenodo prefix with nothing after it have all been written
#: into papers by people who meant to come back to them.
PLACEHOLDER = re.compile(r'(?:[XN]{3,}|\bTBD\b|\bTBA\b|example|'
                         r'0{6,}|123456|/\s*$)', re.I)

#: the statement must still list what is deposited.  These are the words the
#: inventory is built from; losing them would mean the DOI was inserted into
#: a statement that no longer says what it identifies.
INVENTORY = ('target catalogue', 'searched windows', 'execution-block',
             'threshold crossings', 'pipeline')


def section(text, name='Data Availability'):
    """The body of one \\section*{...}, up to the next \\section."""
    m = re.search(r'\\section\*\{%s\}(.*?)(?=\\section|\Z)' % re.escape(name),
                  text, re.S)
    assert m, 'no \\section*{%s} in %s' % (name, BACKMATTER)
    body = m.group(1)
    # comments are instructions to the authors, not published text: a DOI
    # written only in a %% comment does not count.
    return '\n'.join(l for l in body.splitlines()
                     if not l.lstrip().startswith('%'))


def check(body):
    """Return the list of failures, empty if the statement is submittable."""
    fail = []
    found = DOI.findall(body)
    if not found:
        fail.append('D1 the Data Availability statement names no DOI')
    else:
        bad = [d for d in found if PLACEHOLDER.search(d)]
        if bad:
            fail.append('D2 placeholder DOI: %s' % ', '.join(bad))
    missing = [w for w in INVENTORY if w not in body]
    if missing:
        fail.append('D3 the deposit inventory no longer mentions: %s'
                    % ', '.join(missing))
    return fail, found


def main():
    body = section(open(BACKMATTER, errors='ignore').read())
    fail, found = check(body)
    print('doigate: %s' % BACKMATTER)
    print('  DOIs found: %s' % (found or 'none'))
    for f in fail:
        print('  FAIL  %s' % f)
    if fail:
        print('\nDO NOT SUBMIT.  See AUTHOR_ACTIONS.md item 1: reserve the '
              'Zenodo DOI, insert it in the first sentence of the Data '
              'Availability statement, and create a private reviewer link '
              'for the response letter.')
        raise SystemExit(1)
    print('  PASS  a real DOI is named and the inventory is intact')


def selftest():
    """Rule 9: a check that cannot fail is not a check.  Both directions."""
    live = section(open(BACKMATTER, errors='ignore').read())
    cases = [
        ('the live statement as it stands', live, False),
        ('with a real DOI inserted',
         live.replace('cited by its\nDOI.', 'cited by its DOI\n10.5281/zenodo.14087731.'), True),
        ('with a placeholder DOI inserted',
         live.replace('cited by its\nDOI.', 'cited by its DOI\n10.5281/zenodo.XXXXXXX.'), False),
        ('with a real DOI but the inventory deleted',
         'DOI 10.5281/zenodo.14087731 and nothing else.', False),
    ]
    ok = True
    for name, body, should_pass in cases:
        fail, found = check(body)
        passed = not fail
        mark = 'ok ' if passed == should_pass else 'BAD'
        if passed != should_pass:
            ok = False
        print('  %s %-42s expect %-4s got %-4s %s'
              % (mark, name, 'pass' if should_pass else 'fail',
                 'pass' if passed else 'fail', fail))
    print('selftest: %s' % ('every direction behaves' if ok
                            else 'THE CHECK IS BROKEN'))
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
    main()
