#!/usr/bin/env python3
"""Counts for the anti-AI prose pass, main text and appendices separately.

Categories follow referee 3's list so the before/after numbers are comparable
with the ones in the report:

  A  antithesis family     ", not" / "and not" / "rather than"
  B  colon-as-explainer    a mid-sentence colon not introducing a list
  C  paragraph-initial italic or bold label
  D  list-announcement opener with a spelled numeral
  E  em-dash in the source
  F  "X is not Y" as a whole sentence

Usage:  python3 prosecount.py [file.tex ...]
"""
import re
import sys

NUM = r"(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve)"


def regions(path):
    src = open(path, encoding="utf-8").read()
    lines = src.split("\n")
    app = next((i for i, l in enumerate(lines) if l.startswith(r"\appendix")),
               len(lines))
    bib = next((i for i, l in enumerate(lines)
                if l.startswith(r"\begin{thebibliography}")), len(lines))
    return {"main": lines[:app], "appendices": lines[app:bib]}


def strip_comment(line):
    return re.sub(r"(?<!\\)%.*", "", line)


def count(lines):
    body = [strip_comment(l) for l in lines]
    txt = " ".join(body)
    c = {}
    c["A: , not"] = len(re.findall(r", not\b", txt))
    c["A: and not"] = len(re.findall(r"\band not\b", txt))
    c["A: rather than"] = len(re.findall(r"\brather than\b", txt))
    # colon-as-explainer: a colon mid-sentence, not before an enumeration
    # marker, not in a macro argument, not a URL, not in maths
    exp = 0
    for l in body:
        s = re.sub(r"\$[^$]*\$", "", l)
        s = re.sub(r"\\[A-Za-z]+\{[^{}]*\}", " ", s)
        for m in re.finditer(r"(?<![:\\/])\s?:\s(?![\s\d(])", s):
            tail = s[m.end():].lstrip()
            if re.match(r"\\item|\(i+\)|\(a\)", tail):
                continue
            exp += 1
    c["B: colon-explainer"] = exp
    c["C: para-initial label"] = len(re.findall(
        r"(?m)^\\(?:emph|textit|textbf)\{", txt))
    c["D: numeral list-opener"] = len(re.findall(
        NUM + r"\s+[a-z-]+(?:\s+[a-z-]+){0,3}[^.]{0,60}:", txt))
    c["E: em-dash"] = len(re.findall(r"(?<!-)---(?!-)|\\textemdash|—", txt))
    c["F: negative definition"] = len(re.findall(
        r"(?:^|\. )[A-Z][^.]{0,80}\b(?:is|are|was|were) not\b[^.]{0,60}\.", txt))
    return c


def main():
    files = sys.argv[1:] or ["technosignatures_20pc_v3.49.tex"]
    for f in files:
        R = regions(f)
        keys = list(count(R["main"]).keys())
        cm, ca = count(R["main"]), count(R["appendices"])
        print(f"\n{f}")
        print(f"  {'construction':26s} {'main':>6s} {'app':>6s} {'total':>6s}")
        for k in keys:
            print(f"  {k:26s} {cm[k]:6d} {ca[k]:6d} {cm[k] + ca[k]:6d}")
        tot = sum(cm[k] + ca[k] for k in keys if k.startswith("A"))
        print(f"  {'A total (antithesis)':26s} "
              f"{sum(cm[k] for k in keys if k.startswith('A')):6d} "
              f"{sum(ca[k] for k in keys if k.startswith('A')):6d} {tot:6d}")


if __name__ == "__main__":
    main()
