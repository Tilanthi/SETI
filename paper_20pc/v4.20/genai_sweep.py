#!/usr/bin/env python3
r"""genai_sweep.py PDF -- sweep the TYPESET text for anything the journal says
it will reject as "direct evidence of the use of GenAI", plus the internal
housekeeping that would read to a referee as machine narration.

★★★ WHY IT READS THE PDF AND NOT THE SOURCE.  The rule is about what is in
the article, and the article is the typeset page: a source comment is not in
the article, a sentence is.  (The source bundle is published too, which is a
separate problem with a separate answer -- `arxivset.sh` strips every comment
out of the submission copies and proves the strip changes no byte of output.)

★★ WHY THREE RENDERINGS.  pdflatex breaks words across lines and columns and
the text layer keeps the break.  Searched naively, "de-drifted" split over two
lines reads as "de" and "drifted" and matches neither; rejoined naively it
reads as "dedrifted" and looks like an inconsistency that is not there.  Both
mistakes were made here on the same afternoon, in opposite directions.  So:
  raw   as extracted, line breaks intact
  flat  line breaks collapsed and end-of-line hyphenation rejoined
  dehy  flat with every remaining hyphen replaced by a space
A hit in any rendering is reported once, with the sentence it sits in.
★ **Report everything, judge nothing.**  Every hit on the current manuscript
is ordinary English -- "the one that prompted it", "the criterion was fixed
before any stellar position was examined" -- and which of those is harmless is
a decision for a person, not for a regular expression.

Usage
    python3 genai_sweep.py PDF
    python3 genai_sweep.py --drive

★★ `--drive` typesets a small PDF with one planted instance of each family it
can plant, and reports which fired.  **A sweep that finds nothing is
indistinguishable from a sweep that is broken.**  This one returned "clean" on
its first run against the manuscript; the drive is what made that believable,
and it caught two families that were silently matching nothing.
23 of 23 families fire on the planted text.

★ EXIT STATUS MEANS "SOMEONE SHOULD LOOK", NOT "THE PAPER IS WRONG".  Non-zero
means there are hits, and on the current manuscript all six are ordinary
English.  **Do not wire this into `gate.sh` as a hard failure**: it would be
whitelisted inside a round and then it would be one more gate that cannot
fail.  Run it before a submission and read the list.
"""
import os
import re
import sys
import pymupdf

# Families whose whole point is the CASE of the text: "do NOT", a bare "I",
# an agent name, a model name, an all-caps marker.  Folding case on these
# turns each of them into a match on ordinary prose.
CASED = ('imperative-do-not', 'first-person-sg', 'agent-name', 'llm-word',
         'todo')

PATTERNS = [
    # --- prompt-shaped / instruction-shaped language -------------------
    ('prompt-word',      r'\b(?:prompt|prompts|prompted|system prompt)\b'),
    ('hallucinat',       r'\bhallucinat\w*'),
    ('second-person',    r'(?:^|[^a-z])[Yy]ou(?:r|rs|\'ll|\'ve)?\b'),
    ('imperative-do-not',r'\bdo\s+NOT\b|\bDo\s+not\s+(?:re-?run|run|edit|touch|delete|change)\b'),
    ('handoff',          r'\bre-?run\b|\bhand\s*-?off\b|\bhanded\s+off\b|\bdo\s+not\s+rely\b'),
    ('must-you',         r'\byou\s+(?:must|should|may|need|will|can)\b'),
    ('please',           r'\bplease\b'),
    ('first-person-sg',  r'(?:^|[^A-Za-z])I\s+(?:will|have|found|ran|checked|think|note|am)\b'),
    ('lets',             r"\blet\'?s\b|\blet me\b"),
    ('todo',             r'\bTODO\b|\bFIXME\b|\bXXX\b|\bTBD\b|\bplaceholder\b|\bstub\b'),
    # --- agent and tool names -----------------------------------------
    ('agent-name',       r'\br1[0-9]\s*-\s*[a-z]{3,}\b|\bastra\b|\bclaude\b|\bchatgpt\b|\bgpt-?[0-9]\b'
                         r'|\bcopilot\b|\bgemini\b|\bllama\b|\bsubrun\b|\btaurus\b'),
    ('agent-word',       r'\bagent(?:s)?\b|\borchestrator\b|\bintegrator\b|\bscout\b|\bcritic\b'),
    ('llm-word',         r'\bLLM\b|\blarge language model\b|\bgenerative AI\b|\bGenAI\b'
                         r'|\blanguage model\b|\bartificial intelligence\b'),
    # --- internal housekeeping ----------------------------------------
    ('round-number',     r'\bround\s*-?\s*\d{1,3}\b|\bround\s+(?:eight|nine|ten|eleven|twelve)\b'),
    ('version-id',       r'\bv[0-9]\.[0-9]{1,2}\b|\bversion\s+[0-9]\.[0-9]'),
    ('referee-word',     r'\breferee\b|\brevision\b|\bresubmi\w*|\bas corrected\b|\bpreviously\b'
                         r'|\bearlier version\b|\bin the previous\b'),
    ('build-word',       r'\bgate\.sh\b|\bmake_all\b|\bpdflatex\b|\bcleanregen\b|\bbyte-identical\b'
                         r'|\bmacro\b|\bmacros\b|\bgenerator\b|\bdrive[dn]?\b|\bassertion\b|\bassert\b'),
    ('filename',         r'\b[\w./-]+\.(?:py|tex|json|csv|sh|aux|log|cls|bst|md)\b'),
    ('path',             r'(?:^|\s)/(?:workspace|shared|tmp|data)/\S+|\bsections/\w+'),
    ('stray-macro',      r'\\[A-Za-z@]{2,}'),
    ('github',           r'\bgithub\b|\bTilanthi\b|\bgit\b(?!\w)'),
    # --- promises of online-only material -----------------------------
    ('online-only',      r'\bSupporting Information\b|\bsupplementary (?:material|information|data)\b'
                         r'|\bonline[- ]only\b|\be-only\b|\bavailable online with\b'
                         r'|\belectronic version of this (?:paper|article)\b'),
    # --- other machine-narration tells --------------------------------
    ('notebook-voice',   r'\bwe now\b|\bas noted above\b|\bthis round\b|\bin this version\b'
                         r'|\bwas fixed\b|\bwe fixed\b|\bbug\b|\bdefect\b'),
]


def sentences(text):
    # crude but adequate: split on sentence enders followed by a capital/space
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def main(path):
    doc = pymupdf.open(path)
    pagetext = [p.get_text() for p in doc]
    raw = '\n'.join(pagetext)
    flat = re.sub(r'\s+', ' ', re.sub(r'-\n', '', raw))
    dehy = flat.replace('-', ' ')
    views = {'raw': raw, 'flat': flat, 'dehy': dehy}

    # page lookup for a flat offset: build cumulative flat text per page
    page_of = []
    acc = 0
    for i, t in enumerate(pagetext):
        f = re.sub(r'\s+', ' ', re.sub(r'-\n', '', t))
        acc += len(f) + 1
        page_of.append((acc, i + 1))

    def page(off):
        for lim, pg in page_of:
            if off < lim:
                return pg
        return len(pagetext)

    total = 0
    for name, pat in PATTERNS:
        seen = {}
        for vname, text in views.items():
            for m in re.finditer(pat, text,
                                 0 if name in CASED else re.I):
                # locate the sentence
                s0 = text.rfind('.', 0, m.start()) + 1
                s1 = text.find('.', m.end())
                s1 = len(text) if s1 < 0 else s1 + 1
                sent = re.sub(r'\s+', ' ', text[s0:s1]).strip()
                key = (m.group(0).lower(), sent[:90].lower())
                if key in seen:
                    continue
                pg = page(m.start()) if vname == 'flat' else None
                seen[key] = (m.group(0), sent, vname, pg)
        if seen:
            print('\n### %s  -- %d distinct hit(s)' % (name, len(seen)))
            for hit, sent, vname, pg in sorted(seen.values(), key=lambda x: x[0].lower()):
                total += 1
                loc = 'p%s' % pg if pg else vname
                print('  [%s] %-28s | %s' % (loc, hit[:28], sent[:240]))
    print('\n==== %d hit lines across %d pattern families ====' % (total, len(PATTERNS)))
    return total


PLANT = r"""\documentclass{article}
\begin{document}
You must not re-run the first-null calibration; agent r17-compliance owns it.
This is round 42 of version v4.18 and the referee asked for it. TODO: fix the
macro in sections/05\_results.tex. The system prompt said so.
The appendices are published as online Supporting Information with the
electronic version of this paper. Do not re-run the extraction.
See make\_all.sh in the github repository and run pdflatex.
A stray macro: \textbackslash NWinA.
A large language model drafted this; ChatGPT hallucinated the reference.
Please let me know. I will check /workspace/SETI/paper.tex. This bug was
fixed in the previous revision. Claude is an agent.
\end{document}
"""


def drive():
    """Plant one instance of every family that can be planted, and report."""
    import shutil
    import subprocess
    import tempfile
    d = tempfile.mkdtemp(prefix='genai_drive')
    tex = os.path.join(d, 'drive.tex')
    open(tex, 'w').write(PLANT)
    subprocess.run(['pdflatex', '-interaction=nonstopmode', 'drive.tex'],
                   cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pdf = os.path.join(d, 'drive.pdf')
    if not os.path.exists(pdf):
        print('drive: the probe document did not build')
        return 1
    doc = pymupdf.open(pdf)
    raw = '\n'.join(p.get_text() for p in doc)
    flat = re.sub(r'\s+', ' ', re.sub(r'-\n', '', raw))
    views = (raw, flat, flat.replace('-', ' '))
    fired, silent = [], []
    for name, pat in PATTERNS:
        flags = 0 if name in CASED else re.I
        (fired if any(re.search(pat, v, flags) for v in views)
         else silent).append(name)
    shutil.rmtree(d)
    print('drive: %d of %d families fired on the planted text'
          % (len(fired), len(PATTERNS)))
    if silent:
        print('       did NOT fire: %s' % silent)
        print('       -- either the plant omits them or the pattern is dead;')
        print('          check each against its regex before trusting a clean')
        print('          sweep of the manuscript.')
    return 0 if not silent else 1


if __name__ == '__main__':
    if '--drive' in sys.argv:
        sys.exit(drive())
    sys.exit(0 if main(sys.argv[1]) == 0 else 1)
