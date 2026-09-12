#!/usr/bin/env python3
"""Measure the page budget by region, not by counting whole pages.

The `page:appstart` label rounds to a whole page and so charges the main text
for the back matter and charges the appendices for the bibliography. This
measures the four regions in points of column and converts to pages, using the
typeset positions of the ACKNOWLEDGEMENTS heading, the APPENDIX heading and the
REFERENCES heading.
"""
import re, sys, pymupdf

V = sys.argv[1] if len(sys.argv) > 1 else "technosignatures_20pc_v3.46.pdf"
doc = pymupdf.open(V)
TOP, BOT = 43.8, 737.6
H = BOT - TOP


def find(pattern):
    for p in doc:
        for b in p.get_text("blocks"):
            t = b[4].strip().replace("\n", " ")
            if re.match(pattern, t):
                return p.number + 1, b[1]
    return None, None


pg_ack, y_ack = find(r"ACKNOWLEDGEMENTS\b")
pg_app, y_app = find(r"APPENDIX A\b|APPENDIX$")
pg_ref, y_ref = find(r"REFERENCES\b")
N = len(doc)


def pos(pg, y):
    """Content measured from the very start of the document, in points."""
    return (pg - 1) * H + (y - TOP)


end = pos(N, max(b[3] for b in doc[N - 1].get_text("blocks")))
marks = [("main text (S1-Conclusions)", 0.0, pos(pg_ack, y_ack)),
         ("back matter", pos(pg_ack, y_ack), pos(pg_app, y_app)),
         ("appendices", pos(pg_app, y_app), pos(pg_ref, y_ref)),
         ("bibliography", pos(pg_ref, y_ref), end)]
print(f"{V}: {N} pages, column height {H:.0f} pt")
for name, a, b in marks:
    print(f"  {name:28s} {(b-a)/H:5.2f} pages  ({b-a:7.1f} pt)")
print(f"  {'TOTAL':28s} {end/H:5.2f} pages")
