#!/usr/bin/env python3
"""RETIRED at v4.10.  Replaced by make_fig_context_v410.py.

This generator must not run again.  It wrote figures/eirp_context_a.pdf and
figures/eirp_context_b.pdf by copying artists out of a wide two-panel figure,
which silently dropped the legend, the titles and every `facecolor="none"`;
it drew the Arecibo planetary-radar line, which the paper no longer uses on
any figure; and its ordinate was P_90^sel taken from the catalogue column
`eirp_p90_sel_W`, which carries the RETIRED x2.88 criterion rather than the
adopted EIRP_90 = 5.70 P_trig.

It fails loudly instead of overwriting the correct panels, because a build
that stops is better than a figure that is quietly wrong.  The original file
is kept verbatim at retired/make_fig_context_v342.py for provenance.

  make_all.sh: replace
      python3 make_fig_context_v342.py
  with
      python3 make_fig_context_v410.py
  (-> numbers agent / integrator; the figures agent does not own make_all.sh)
"""
import sys

sys.exit("make_fig_context_v342.py is RETIRED at v4.10 -- run "
         "make_fig_context_v410.py instead (see this file's docstring).")
