#!/usr/bin/env python3
"""prosegate_selfref -- a build-time gate against self-reference in the paper's voice.

The defect family: any sentence that tells a reader this paper has a history --
an earlier version of itself, an earlier analysis of ours, an edit, a revision, a
response, a referee -- or that compares the work with an UNNAMED predecessor, which
reads as self-reference even when the predecessor is somebody else's paper.

It has survived into a shipped PDF in four consecutive rounds, the subtlest instance
being the two words "no longer".  So this gate is deliberately conservative:

  HARD  phrases are never legitimate in this voice and fail outright.
  SOFT  comparatives ("earlier", "previous", "the original", ...) fail UNLESS the
        antecedent is named -- operationally, unless an author-year citation appears
        in the same sentence or the one immediately before it.
  ALLOW every remaining legitimate use must be declared once, in an allow file, and
        is PINNED BY HASH to the exact sentence.  Edit the sentence and the pin
        lapses, so the gate re-fires on reworded text; that is exactly how "no longer"
        slipped through a word-level whitelist before.  An allow entry that matches
        nothing is itself a FAILURE, so dead exemptions cannot silently cover new prose.

Two input streams, because either alone is blind:
  SOURCE  sections/*.tex with LaTeX comments stripped (what an author writes)
  PDF     the typeset text, de-hyphenated and line-flattened (what a reader reads,
          including everything that arrives through a macro or a generated fragment)

Exit status 0 only when both streams are clean and every allow entry was used.

Usage:
  prosegate_selfref.py --version-dir DIR [--pdf-text FILE] [--allow FILE] [--drive N]

Drives (each must fail; a gate that has never fired is no evidence of anything):
  0  no perturbation, and writes nothing a production path reads
  1  inject a self-referring sentence into the SOURCE stream
  2  inject one into the PDF stream only
  3  perturb an allowed sentence by one character -- the pin must lapse
  4  delete an allowed sentence -- the stale allow entry must fail
  5  plant a version string of OURS in the PDF stream, outside the class's own
     front-matter slug, so that removing the slug is not a hole
"""
import argparse, glob, hashlib, os, re, sys

# ---------------------------------------------------------------- phrase lists

HARD = [
    r"\bin this version\b", r"\bthe present version\b", r"\ban earlier version\b",
    r"\bthe previous version\b", r"\bearlier draft\b", r"\bthis draft\b",
    r"\breferee\b", r"\brefereeing\b", r"\breviewer\b", r"\bthe report\b",
    r"\bin response to\b", r"\brebuttal\b", r"\bresubmi\w*", r"\berratum\b",
    r"\bcorrigendum\b", r"\bas (?:we )?(?:noted|stated|said) (?:above|earlier|previously)\b",
    r"\bwe now\b", r"\bwe have now\b", r"\bit is now\b", r"\bno longer\b",
    # "corrected FOR x" is the ordinary physics idiom and is excluded by the
    # lookahead; "the value has been corrected" is the defect.
    r"\bhas been (?:changed|revised|updated|withdrawn|removed|added)\b",
    r"\bhave been (?:changed|revised|updated|withdrawn|removed|added)\b",
    r"\b(?:has|have) been corrected\b(?!\s+for\b)",
    r"\bwe have (?:added|extended|revised|updated|changed|removed|rewritten)\b",
    r"\bwe (?:added|revised|updated|rewrote)\b",
    r"\bour (?:earlier|previous|original|first) \w+", r"\bin (?:our|the) earlier\b",
    r"\bsupersed\w+", r"\bwithdraw\w+", r"\bre-?examined\b", r"\bon reflection\b",
    r"\bsecond look\b", r"\bfirst reported\b", r"\bpreviously reported\b",
    # "round" as a referee round, never "the round $10^{15}$ W level"
    r"\bthis round\b", r"\b(?:referee|review|revision|comment)s?[- ]round\b",
    r"\bround \d+ (?:referee|comments?|revisions?|report)\b",
    r"\bv\d+\.\d+\b",
]

# comparatives: legitimate only with a named antecedent nearby
SOFT = [
    r"\bearlier\b", r"\bpreviously\b", r"\bprevious\b", r"\bprior\b",
    r"\bformerly\b", r"\boriginally\b", r"\bthe original\b", r"\bthe former\b",
    r"\binitially\b", r"\bhitherto\b", r"\bup to now\b", r"\bas before\b",
    r"\bhas since\b", r"\bhave since\b", r"\brevised\b", r"\brevision\b",
    r"\bupdated\b", r"\bre-?extract\w*", r"\bre-?analys\w*", r"\bre-?run\b",
]

# an author-year citation, in either stream
CITE_SRC = re.compile(r"\\cite[a-z]*\s*(\[[^\]]*\]\s*)*\{")
CITE_PDF = re.compile(r"[A-Z][A-Za-zÀ-ɏ'`-]+"          # Name
                      r"(?:\s*(?:&|and)\s*[A-Z][A-Za-z'`-]+)?"   # & Name
                      r"(?:\s+et\s+al\.?)?"                      # et al.
                      r"\s*\(?\b(?:19|20|21)\d\d\b")             # (1994 / 2025

SENT_SPLIT = re.compile(r"(?<=[.!?])[}\])]*\s+(?=[A-Z\\$—(])|⟂")

# Structural boundaries that end a sentence even without a full stop before them.
# Without these, a figure caption and the subsection after it become one "sentence",
# and a citation anywhere in that block would license a comparative far from it.
BREAK_SRC = re.compile(r"(\\(?:item|section|subsection|subsubsection|paragraph"
                       r"|caption|label|begin|end|input)\b)")
BREAK_PDF = re.compile(r"(?<=[.})”])\s+(?=\d{1,2}(?:\.\d+)*\.?\s+[A-Z])")

# ---------------------------------------------------------------- normalisation


def strip_comments(line):
    out, i = [], 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line):
            out.append(line[i:i + 2]); i += 2; continue
        if line[i] == "%":
            break
        out.append(line[i]); i += 1
    return "".join(out)


def flatten_source(path):
    body = [strip_comments(l) for l in open(path, encoding="utf-8",
                                            errors="replace").read().split("\n")]
    t = " ".join(body)
    t = BREAK_SRC.sub(r" ⟂ \1", t)
    return re.sub(r"[ \t]+", " ", t).strip()


#: ---------------------------------------------------------------------------
#: THE CLASS'S FURNITURE IS NOT THE PAPER'S PROSE, AND IT MUST LEAVE THE PDF
#: STREAM BEFORE ANYTHING IS PINNED TO A SENTENCE.
#:
#: The running heads are interleaved into the text at every page break, so a
#: sentence that spans a page acquires "22 White & Dey" or "An ALMA Archival
#: Technosignature Search within 40 pc" in the middle of it.  That is not
#: cosmetic: the allow file PINS A SENTENCE BY HASH, so a pin taken over a
#: sentence with a running head inside it lapses the moment anything reflows.
#: A declared exemption that dies on every reflow is an invitation to
#: whitelist a word, which is the failure this gate exists to prevent.
#:
#: They are removed structurally, by strings DERIVED from the manuscript --
#: `openjournal.cls`'s own \shorttitle and \shortauthors, which are exactly
#: what it typesets as the two running heads -- and never by a word-level rule;
#: and the removal asserts it fired, because a structural exclusion that
#: silently finds nothing is a hole.
#:
#: ★★★ AND THE CLASS'S PAGE-1 SLUG IS CHECKED TO BE ABSENT RATHER THAN
#: STRIPPED.  `openjournal.cls` sets `\submitted{Version \today}` and
#: `\journalinfo{\@submitted}`, which print "Preprint typeset using LaTeX
#: style openjournal v. 09/06/15" above the title and a version slug on page 1;
#: the preamble empties both on purpose.  A slug would trip the HARD pattern
#: \bv\d+\.\d+\b, which exists to catch OUR version strings, with the
#: CLASS's version -- so if the suppression ever lapses this gate must say so
#: and not launder it.  CLASS_SLUG is therefore a REFUSAL, not a filter, and
#: the one thing it must never do is remove text.  (This clause was written
#: the other way round, as a strip with `assert n == 1`, for a class that does
#: print such a slug; under this class that assertion could only ever fail.)
#: Drive 5 plants a version string of ours in the PDF stream and must fail.
CLASS_SLUG = re.compile(r"Preprint typeset using LA?TEX style \S+"
                        r"|^\s*Version \d", re.M)
RUNHEAD_SRC = re.compile(r"\\(?:shorttitle|shortauthors)\{([^}]*)\}")


def furniture(version_dir):
    """The running-head strings the class typesets, read from the manuscript."""
    import manuscript as _m
    main = (os.path.join(version_dir, _m.main_file())
            if os.path.isdir(version_dir) else version_dir)
    txt = open(main, encoding="utf-8", errors="replace").read()
    args = RUNHEAD_SRC.findall(txt)
    assert len(args) == 2, (
        "prosegate_selfref: expected openjournal.cls's \\shorttitle and "
        "\\shortauthors, found %r" % (args,))
    out = []
    for a in args:
        a = re.sub(r"\\[a-zA-Z]+\s*", "", a)        # control words: \textit, ...
        # ★ SPACING COMMANDS ARE SPACES ON THE PAGE, and this is where the
        # derivation failed first: \shorttitle holds "within 40\,pc", which
        # the escape rule below turns into "40,pc" while the class typesets
        # "40 pc" -- so the derived head matched nothing and the assertion
        # below fired.  A thin space, a quad and a tie are all one space here.
        a = re.sub(r"\\[,;:!> ]|~", " ", a)
        a = re.sub(r"\\(.)", r"\1", a)              # escaped characters: \& -> &
        a = a.replace("{", "").replace("}", "").strip()
        out.append(re.sub(r"\s+", " ", a))
    return out


def flatten_pdf(path, version_dir=None):
    t = open(path, encoding="utf-8", errors="replace").read()
    # ★ A REFUSAL, NOT A FILTER: the class's own preprint/version slug must not
    # be in the typeset text at all, because the preamble suppresses it.  If it
    # reappears, the paper has a version string of the class's on page 1 and
    # this gate reports it rather than removing it.
    _slug = CLASS_SLUG.search(t)
    assert _slug is None, (
        "prosegate_selfref: the class's preprint/version slug is in the "
        "typeset text (%r).  The preamble's \\submitted{}/\\journalinfo{} "
        "suppression has lapsed; fix that rather than filtering the slug out "
        "here." % _slug.group(0)[:60])
    if version_dir:
        for head in furniture(version_dir):
            rx = re.compile(r"\n[^\S\n]*(?:\d{1,3}[^\S\n]*\n+)?"
                            + re.escape(head)
                            + r"[^\S\n]*(?:\n+[^\S\n]*\d{1,3})?[^\S\n]*\n")
            t, n = rx.subn("\n", t)
            assert n >= 2, (
                "prosegate_selfref: running head %r was removed %d time(s); "
                "openjournal.cls prints one of its two heads on every page "
                "after the first, so 0 or 1 means the derivation is wrong."
                % (head, n))
    # ★ A BARE PAGE NUMBER INSIDE A HYPHENATED WORD.  Where a word breaks
    # exactly at a page edge, pdftotext emits "win-", then the next page's
    # folio on a line of its own, then "dows" -- and the de-hyphenation below
    # then produces "win25 dows", which is not a word and whose sentence no
    # later build reproduces.  This class prints the page number as a bare
    # number beside its running head, so this normalisation is the whole of
    # the folio handling here.  Removed only in that position: a line of one to
    # three digits that interrupts a hyphenated word.  It is a normalisation of
    # the stream, not a check, and the gate's verdict does not depend on it
    # firing.
    t = re.sub(r"(?<=-)\n+[^\S\n]*\d{1,3}[^\S\n]*\n+", "\n", t)
    t = t.replace("\f", " ")
    t = re.sub(r"-\n\s*", "", t)        # de-hyphenate across the line break
    t = re.sub(r"\s*\n\s*", " ", t)     # flatten: a phrase split by a line break
    # ★ No page-join sentinel is needed under this class: it prints no folio
    # line, so nothing is substituted into the middle of a word and there is
    # nothing to close up afterwards.  The two substitutions that did it are
    # deleted rather than left as no-ops.
    t = re.sub(r"\s+", " ", t).strip()
    return BREAK_PDF.sub(" ⟂ ", t)      # enumerate items and numbered headings


def norm(s):
    """Canonical form a hash is taken over: markup out, whitespace collapsed."""
    s = re.sub(r"\\cite[a-z]*\s*(\[[^\]]*\]\s*)*\{[^}]*\}", " CITE ", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s)
    s = re.sub(r"[{}$~\\]", " ", s)
    s = re.sub(r"[^A-Za-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def pin(s):
    return hashlib.sha1(norm(s).encode()).hexdigest()[:12]


ABBREV = {"al", "e.g", "i.e", "cf", "fig", "figs", "eq", "eqs", "no", "vs",
          "ref", "refs", "approx", "resp", "etc", "ca", "st", "pp", "ser",
          "vol", "collab", "doc", "ver", "sec", "secs", "tab", "tabs"}


def sentences(text):
    """Split into sentences without breaking after an abbreviation or an initial.

    This matters: the citation that licenses a comparative must be found in the
    same sentence, and splitting "Mauersberger et al. (1996) has since ..." after
    "al." strips the citation away and manufactures a false positive.
    """
    out, buf = [], ""
    for part in SENT_SPLIT.split(text):
        buf = (buf + " " + part).strip() if buf else part
        tail = re.sub(r"[^A-Za-z.]+$", "", buf)
        last = tail.split()[-1].rstrip(".").lower() if tail.split() else ""
        if last in ABBREV or len(last) == 1:
            continue                      # "et al." or "P." -- keep accumulating
        out.append(buf); buf = ""
    if buf:
        out.append(buf)
    return [s for s in out if s.strip()]

# ---------------------------------------------------------------- the gate


def scan(stream_name, text, cite_rx, allow, used):
    hits = []
    sents = sentences(text)
    for i, s in enumerate(sents):
        prev = sents[i - 1] if i else ""
        cited = bool(cite_rx.search(s) or cite_rx.search(prev))
        p = pin(s)
        for rx_list, kind in ((HARD, "HARD"), (SOFT, "SOFT")):
            for pat in rx_list:
                m = re.search(pat, s, re.I)
                if not m:
                    continue
                if kind == "SOFT" and cited:
                    continue
                if p in allow:
                    used.add(p)
                    continue
                hits.append(dict(stream=stream_name, kind=kind, pat=pat,
                                 text=m.group(0), pin=p, sentence=s.strip()[:300]))
    return hits


def load_allow(path):
    allow = {}
    if path and os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            allow[parts[0]] = parts[1] if len(parts) > 1 else "(no reason given)"
    return allow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version-dir", required=True)
    ap.add_argument("--pdf-text")
    ap.add_argument("--allow")
    ap.add_argument("--drive", type=int, default=0)
    ap.add_argument("--scratch", default=None,
                    help="where drives write; never a path production reads")
    a = ap.parse_args()

    allow = load_allow(a.allow)
    used = set()

    srcs = sorted(glob.glob(os.path.join(a.version_dir, "sections", "*.tex")))
    src_texts = {os.path.basename(f): flatten_source(f) for f in srcs}
    pdf_text = (flatten_pdf(a.pdf_text, a.version_dir)
                if a.pdf_text else "")

    # ---- drives: perturb only the in-memory copies, never a production path
    PROBE = ("We now report that the previous criterion has been revised in "
             "response to the referee.")
    if a.drive == 1:
        k = sorted(src_texts)[0]
        src_texts[k] = src_texts[k] + " " + PROBE
    elif a.drive == 2:
        pdf_text = pdf_text + " " + PROBE
    elif a.drive == 5:
        # ★ A version string of OURS in the typeset text must fail wherever it
        # is.  The class's own slug is refused by flatten_pdf rather than
        # filtered, so there is no exclusion for this to hide behind; the drive
        # stays because the HARD pattern that catches it is the reason the slug
        # may not be laundered.
        pdf_text = pdf_text + " The limits of v4.18 are superseded here."
    elif a.drive in (3, 4):
        if not allow:
            print("drive %d needs a non-empty allow file" % a.drive); return 2
        target = sorted(allow)[0]
        for k, t in list(src_texts.items()):
            ss = sentences(t)
            for i, s in enumerate(ss):
                if pin(s) == target:
                    if a.drive == 3:
                        ss[i] = s.rstrip(".") + " indeed."    # one-word perturbation
                    else:
                        ss[i] = "The sky is observed."         # sentence deleted
                    src_texts[k] = " ".join(ss)
                    break
        for i, s in enumerate(sentences(pdf_text)):
            if pin(s) == target:
                pdf_text = pdf_text.replace(
                    s, s.rstrip(".") + (" indeed." if a.drive == 3 else ""), 1)
                break

    hits = []
    for name, t in src_texts.items():
        hits += scan("SOURCE:" + name, t, CITE_SRC, allow, used)
    if pdf_text:
        hits += scan("PDF", pdf_text, CITE_PDF, allow, used)

    stale = sorted(set(allow) - used)

    for h in hits:
        print("FAIL %-5s %-28s %-18r %s\n       pin %s | %s"
              % (h["kind"], h["stream"], h["text"], h["pat"], h["pin"], h["sentence"]))
    for p in stale:
        print("FAIL STALE allow entry %s matches nothing: %s" % (p, allow[p]))

    print("\nprosegate_selfref: %d hit(s), %d allow entr(ies), %d stale, drive %d"
          % (len(hits), len(allow), len(stale), a.drive))
    ok = not hits and not stale
    print("prosegate_selfref: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
