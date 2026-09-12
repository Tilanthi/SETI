#!/usr/bin/env python3
"""Find short last lines (widows) in the typeset PDF.

A paragraph whose final line carries only a word or two costs a whole line of
page. Report them worst-first with enough leading text to find them in the .tex.
"""
import sys, pymupdf

PDF = sys.argv[1] if len(sys.argv) > 1 else "technosignatures_20pc_v3.55.pdf"
MAXFRAC = float(sys.argv[2]) if len(sys.argv) > 2 else 0.22

doc = pymupdf.open(PDF)
out = []
for page in doc:
    d = page.get_text("dict")
    for blk in d["blocks"]:
        if blk.get("type") != 0:
            continue
        lines = [l for l in blk["lines"] if l["spans"]]
        if len(lines) < 2:
            continue
        widths = [l["bbox"][2] - l["bbox"][0] for l in lines]
        body = max(widths)
        if body < 300:           # skip narrow material: tables, captions in boxes
            continue
        last = lines[-1]
        frac = (last["bbox"][2] - last["bbox"][0]) / body
        if frac > MAXFRAC:
            continue
        txt = lambda l: "".join(s["text"] for s in l["spans"]).strip()
        out.append((frac, page.number + 1, len(lines), txt(lines[0])[:58], txt(last)[:40]))

out.sort()
print(f"{len(out)} paragraphs with a last line under {MAXFRAC:.0%} of the measure")
for frac, pg, n, first, last in out:
    print(f"  {frac*100:5.1f}%  p{pg:3d} {n:3d}L  {first!r:62s} -> {last!r}")
