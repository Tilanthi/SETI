#!/usr/bin/env python3
"""Honest word-level diff between two .tex files.

Reports tokens deleted, tokens inserted, and the net change, separately for the
main text (before \appendix), the appendices, and the whole file.  A "token" is
a whitespace-separated run after LaTeX comments are stripped; macro calls and
markup count, which is why the same script must be used on both sides.

Usage:  python3 worddiff.py OLD.tex NEW.tex
"""
import difflib, re, sys


def load(path):
    txt = open(path, encoding="utf-8").read()
    txt = re.sub(r"(?<!\\)%.*", "", txt)          # strip comments
    i = txt.find("\\appendix")
    b = txt.find("\\begin{document}")
    main = txt[b:i] if i > 0 else txt[b:]
    app = txt[i:] if i > 0 else ""
    return {"main": main.split(), "appendices": app.split(),
            "whole": txt[b:].split()}


def diff(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    dele = ins = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            dele += i2 - i1
        if tag in ("replace", "insert"):
            ins += j2 - j1
    return dele, ins


old, new = load(sys.argv[1]), load(sys.argv[2])
print(f"word-diff  {sys.argv[1]}  ->  {sys.argv[2]}")
print(f"{'region':14s} {'old':>7s} {'new':>7s} {'deleted':>8s} {'inserted':>9s} {'net':>7s}")
for k in ("main", "appendices", "whole"):
    d, i = diff(old[k], new[k])
    print(f"{k:14s} {len(old[k]):7d} {len(new[k]):7d} {d:8d} {i:9d} {i-d:+7d}")
