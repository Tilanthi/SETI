#!/usr/bin/env python3
"""Count the products `make_all.sh` regenerates, and emit it as a macro.

Counts every generated product except this script's own output.

Runs LAST in make_all.sh, after every generator and every figure, so the glob
sees the complete set.  v3.67 first put this count inside `v363_calc.py`,
which runs before the figures are built: on a clean regeneration the figure
directory was still empty there and the macro came out wrong, so the one
product that failed the byte-identical test was the file carrying the
reproducibility claim itself.  Order matters; this script exists to fix it.
"""
import glob, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
prod = (sorted(glob.glob('survey_numbers*.tex'))
        + ['tab_selection.tex', 'tab_perband.tex', 'peff_range_v367.tex']
        + sorted(glob.glob('figures/*.pdf')))
missing = [f for f in prod if not os.path.exists(f)]
assert not missing, missing
open('regen_count.tex', 'w').write(
    '\\newcommand{\\NRegenProducts}{%d}\n' % len(prod))
print('regen_count: %d products' % len(prod))
