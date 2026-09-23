#!/usr/bin/env python3
"""Structural diff of the MAIN TEXT between the backup and the current file.

Reports: lost labels, lost \input, lost float/equation environments,
lost citations, lost generated macros, lost \fbox/\parbox boxes,
lost section headings.  Anything lost is a candidate build-breaker.
"""
import re, sys, collections

CUR = "technosignatures_40pc_v3.95.tex"
BAK = sys.argv[1] if len(sys.argv) > 1 else "technosignatures_40pc_v3.95.tex.bak-subrun5"

def main_text(path):
    src = open(path, encoding="utf-8").read()
    i = src.index("\n\\appendix")
    return src[:i]

def full(path):
    return open(path, encoding="utf-8").read()

def feats(t):
    return {
        "labels": collections.Counter(re.findall(r"\\label\{([^}]*)\}", t)),
        "inputs": collections.Counter(re.findall(r"\\input\{([^}]*)\}", t)),
        "cites": collections.Counter(c.strip() for g in re.findall(r"\\cite[a-z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", t) for c in g.split(",")),
        "envs": collections.Counter(re.findall(r"\\begin\{(table\*?|figure\*?|equation|align|fbox|parbox)\}", t)),
        "fbox": collections.Counter(re.findall(r"\\fbox", t)),
        "headings": collections.Counter(re.findall(r"\\(?:sub)*section\*?\{([^}]*)\}", t)),
    }

def macros(t):
    # generated macros are \CamelCase with no args
    return collections.Counter(re.findall(r"\\([A-Z][A-Za-z]{2,})\b", t))

b, c = main_text(BAK), main_text(CUR)
fb, fc = feats(b), feats(c)
bad = 0
for k in fb:
    lost = fb[k] - fc[k]
    gained = fc[k] - fb[k]
    if lost:
        print(f"LOST {k}: {dict(lost)}")
        if k in ("labels", "inputs", "envs", "fbox"):
            bad += sum(lost.values())
    if gained and k in ("labels",):
        print(f"NEW {k}: {dict(gained)}")

# macros: check against the whole-document macro definitions
alltex = full(CUR)
defined = set(re.findall(r"\\newcommand\{?\\([A-Za-z]+)\}?", alltex))
for rf in re.findall(r"\\input\{(survey_numbers[^}]*)\}", alltex):
    try:
        defined |= set(re.findall(r"\\newcommand\{?\\([A-Za-z]+)\}?", open(rf if rf.endswith('.tex') else rf+'.tex', encoding='utf-8').read()))
    except OSError:
        pass
mb, mc = macros(b), macros(c)
lostm = {k: v for k, v in (mb - mc).items() if k in defined and mc[k] == 0}
if lostm:
    print(f"macros no longer used in main text ({len(lostm)}): {sorted(lostm)}")
newm = {k: v for k, v in (mc - mb).items()}
unknown = sorted(k for k in newm if k not in defined and k not in mb)
if unknown:
    print(f"!! NEW UNKNOWN MACRO-LIKE TOKENS: {unknown}")
    bad += len(unknown)

print(f"main chars: backup {len(b)} -> current {len(c)}  ({len(c)-len(b):+d})")
print("STRUCTURAL PROBLEMS:", bad)
