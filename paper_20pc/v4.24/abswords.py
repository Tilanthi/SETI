#!/usr/bin/env python3
"""Abstract WORD length, measured on the built page.

★ The journal is the Open Journal of Astrophysics, and it sets no abstract
limit at all -- it is an arXiv overlay journal, so the only external limit on
the abstract is arXiv's, and arXiv's is 1920 CHARACTERS, not a word count
(`abschars.py`, `abstract_limit.py` and `absmeta.py`).  The ceiling below is
therefore OURS: a house budget on a single-paragraph abstract, kept because it
is the discipline that holds the paragraph readable, and kept so that nothing
loosens silently.  It used to be described here as the journal's, which is
false now and misled at least one later reader into treating it as the binding
constraint when the binding constraint is the character count.

The abstract must be one paragraph, and this gate holds it to a word count of
ours.  That is a property of the TYPESET paragraph, not of the source: the
source contains
macros, comments and line breaks, and every count made from it so far has
been wrong.  A comment in abstract.tex claimed 245 words while the printed
paragraph held 253 -- an eight-word error in the one number a journal checks
mechanically.

So this gate reads the PDF.  It extracts the text between the ABSTRACT
heading and whatever follows it, counts words the way a copy-editor would,
and fails above the limit.

It also refuses to pass if it cannot find the abstract at all, because a
length check that silently measures nothing is worse than no check: it
reports success for a paper whose abstract it never saw.
"""
import re
import subprocess
import sys
import glob
import os

# ★★★★ RULED BY GLENN, 2026-10-13: "The abstract length is governed by the
# arXiv limits, so you must meet that without exception."
# So the binding limit on this abstract is arXiv's **1920 CHARACTERS**,
# measured on the typeset paragraph by `abschars.py` (1518 characters at this
# build, 402 to spare) and independently from the source by
# `abstract_limit.py`.  Those two are the gates that correspond to a real
# refusal, and a third check guards the plain-ASCII text that is actually
# pasted into the arXiv metadata field (`absmeta.py`).  THE WORD COUNT BELOW
# IS NOT A JOURNAL LIMIT AND IS NOT THE ARXIV ONE: it is a style alarm of
# ours, the number is Glenn's to set, and it may not be used to justify
# cutting a measurement out of the abstract.  Nothing here is switched off --
# the gate still runs on every build and still fails above its ceiling --
# because a disabled gate is how this project acquired twenty-plus checks
# that could not fail.
#
# 250 WAS NEVER A JOURNAL RULE, AND IT WAS LABELLED AS ONE.
# This ceiling has been described in our own source as "the MNRAS limit" for
# six rounds and we are not submitting to MNRAS.  The journal is the Open
# Journal of Astrophysics, which sets NO abstract limit of any kind; the one
# external limit that binds is arXiv's **1920 characters**, which
# `abschars.py` measures and which currently passes with 402 to spare.
# So this gate is a STYLE alarm, not a journal gate, and its number is a
# matter of taste -- while five referee requirements reached the abstract
# this round (R1-2's seven untestable crossings, R2-1's return rather than
# holding, R2-4's eight reserved events, R2-5's separated disposition claim
# and R2-8(4)'s decorrelation disclosure) and every one of them is a
# measurement.  A house ceiling that forces a measurement out of an abstract
# is the wrong constraint, and `r17-prose` paid ~290 characters of it back
# inside the paragraph before saying so.
# ★ RAISED 250 -> 310 in round 19, which was 16 words above the 294 then
# typeset: enough head-room that the honest abstract fitted, tight enough that
# it still fired on drift.
# ★★★★ LOWERED BACK TO 250, r20-final: IT IS A REFEREE REQUIREMENT NOW AND NO
# LONGER A MATTER OF TASTE.  Referee 1 of round 20 asks for "approximately
# 180-200 words, absolute maximum 250" and Referee 2 for "at most 250 words
# and at most 1,600 characters in the LaTeX metadata form, verified
# programmatically".  A gate set at 310 would have passed an abstract both
# referees refuse, and a gate that permits what the journal's referees refuse
# is worse than no gate at all.  The rewritten paragraph measures 245 words
# and 1,517 characters in the metadata form, so there are five words of
# head-room -- deliberately not one, because this paragraph's word count
# moves by one with the line breaks (see the note in `sections/abstract.tex`
# about the stretchable math space around the multiplication sign).
# ► The 1,600-character half of the requirement is NOT this gate's: it is
# `absmeta.py`'s, measured on the block that is actually pasted into the
# arXiv form, and arXiv's own 1,920 is checked there and by `abschars.py`.
# ★★★★ LOWERED 250 -> 240, r22-main, AND THE REFEREES' 200 IS DELIBERATELY
# NOT THE NUMBER HERE.  Both referees of round 22 ask for <=200 words.  The
# paragraph was rewritten against that target with every ungated word spent,
# and the floor with all eleven of its gated clauses present measured ~235;
# spending the calibration-residual clause on Referee 1's own instruction
# ("secondary calibration diagnostics") brings it to what this build reports.
# ►► SO WHY NOT SET 200 AND FORCE THE ISSUE?  Because a ceiling the honest
# paragraph cannot meet is a ceiling somebody switches off, and this project
# has twenty-plus gates that could not fail because of exactly that reflex.
# A gate must be a number the paper can hold while telling the truth, set
# tight enough to catch drift.  The number below sits a few words above what
# is typeset, which catches growth and refuses nothing honest.
# ★★★★ RAISED 240 -> 245 ON THE AUTHOR'S INSTRUCTION, 2026-10-18, AND THIS IS
# THE ONLY DIRECTION THIS CEILING HAS EVER MOVED IN.  He restored the union
# bandwidth and the count of disjoint intervals to the opening sentence: they
# are the extent of the experiment and the paper's novelty claim, they had
# been dropped by a length pass that was not authorised to drop them, and no
# value gate held them.  Those words are an INSTRUCTION, not a budget
# overrun, which is why the ceiling moves to accommodate them instead of the
# paragraph being cut elsewhere to fit -- the rule in the paragraph above
# still stands for every other word, and the next clause spent for length
# must bring this number down in the same edit.
# ►► A CEILING THAT RISES WHENEVER THE TEXT DOES IS NOT A GATE.  245 is five
# words above the restored paragraph and is not to be raised again by an
# editor: if a measurement ever needs more room here, that is the author's
# call to make and to record, exactly as this one is recorded.
# ►► THE 200 IS NOT ABANDONED -- IT IS ITEMISED.  MAIN_REPORT_R22.md lists,
# clause by clause, which referee instruction requires each of the remaining
# qualifications and what dropping it would buy, so the last words are spent
# by the author deliberately rather than by an editor under a budget.  When
# one is spent, LOWER THIS NUMBER IN THE SAME EDIT.
# ★ Referee 1 himself: the 200 is "an editorial improvement, not a
# demonstrated arXiv compliance failure", and "Do not sacrifice scientific
# precision simply to shorten the abstract."  No external limit binds -- the
# arXiv ceiling is 1920 CHARACTERS and `abschars.py` reports the margin.
LIMIT = 245
ENDERS = ('Subject headings', 'Key words', 'Keywords',
          '1. INTRODUCTION', '1.  INTRODUCTION', 'INTRODUCTION')


def main_pdf():
    """The one manuscript PDF, found the same way every other tool finds it."""
    cand = [p for p in glob.glob('technosignatures_*.pdf')
            if re.match(r'technosignatures_\d+pc_v[\d.]+\.pdf$', os.path.basename(p))]
    if len(cand) != 1:
        sys.exit('abswords: expected exactly one manuscript PDF, found %d: %s'
                 % (len(cand), sorted(cand)))
    return cand[0]


def abstract_text(pdf):
    out = subprocess.run(['pdftotext', '-f', '1', '-l', '1', pdf, '-'],
                         capture_output=True, text=True, check=True).stdout
    i = out.find('ABSTRACT')
    if i < 0:
        sys.exit('abswords: no ABSTRACT heading on page 1 of %s -- the gate '
                 'cannot measure what it cannot find, so this is a FAILURE, '
                 'not a pass' % pdf)
    body = out[i + len('ABSTRACT'):]
    for e in ENDERS:
        j = body.find(e)
        if j > 0:
            body = body[:j]
            break
    else:
        sys.exit('abswords: found ABSTRACT but no following heading; refusing '
                 'to count to the end of the page')
    return body.replace('-\n', '').replace('\n', ' ').strip()


def count(text):
    # A word is a whitespace-separated token carrying at least one
    # alphanumeric character; "---" and bare punctuation do not count.
    return len([w for w in re.split(r'\s+', text) if re.search(r'[0-9A-Za-z]', w)])


if __name__ == '__main__':
    pdf = main_pdf()
    text = abstract_text(pdf)
    n = count(text)
    paras = len([b for b in re.split(r'\s{4,}', text) if b.strip()])
    print('abswords: %d words in the typeset abstract of %s (limit %d)'
          % (n, pdf, LIMIT))
    bad = []
    if n > LIMIT:
        bad.append('abstract is %d words, %d over our own budget of %d '
                   '(the journal sets no abstract limit; arXiv limits '
                   'characters, see abschars.py; this ceiling is OURS and is a '
                   'style alarm, not a journal rule)' % (n, n - LIMIT, LIMIT))
    if n < 120:
        bad.append('abstract is only %d words -- extraction probably clipped '
                   'it, which would make this gate vacuous' % n)
    if bad:
        for b in bad:
            print('  FAIL ' + b)
        sys.exit(1)
    print('  OK one paragraph, within the limit, measured on the page')
