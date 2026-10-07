#!/usr/bin/env python3
r"""Gate: the typeset ledger must be the adopted crossing list.

Nothing compared these two before. The ledger is a generated fragment and
the adopted crossing list is a generated json, so both looked authoritative,
and the fragment went on carrying four crossings that fall below the trigger
under the adopted statistic, missing two that rise, giving one star two rows
where one survives, and summing its dispositions to the sky-frame
attribution count. A table that is generated is not thereby correct; it is
only consistent with whatever it was generated from.

Four clauses, each on the typeset fragment itself rather than on the json it
came from, because the fragment is what a reader sees:

  G1  the fragment has exactly as many data rows as the adopted list;
  G2  every (star, block, frequency) in the fragment is in the adopted list
      and every one in the list is in the fragment;
  G3  the dispositions in the fragment sum to the adopted attributed and
      unattributed counts;
  G4  the fragment carries ONE epoch convention -- a column group naming a
      second one is a record of how the analysis changed.

    python3 ledgergate.py [FRAGMENT] [--drive N]

--drive 1..4 breaks one clause each; with no argument the gate reads the
fragment the manuscript inputs.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def rows_of(tex):
    out = []
    for line in tex.split('\n'):
        line = line.strip()
        if not line.endswith('\\\\') or line.startswith('%'):
            continue
        if '\\hline' in line or '\\multicolumn' in line:
            continue
        cells = [c.strip() for c in line[:-2].split('&')]
        if len(cells) < 4:
            continue
        freq = None
        for c in cells:
            m = re.fullmatch(r'([\d]{2,3}\.\d+)\*?', c)
            if m:
                freq = float(m.group(1))
                break
        if freq is None:
            continue
        star = re.sub(r'[\\${}~^]|\\mathrm|\\emph', ' ', cells[0]).strip()
        blk = cells[1].replace('\\_', '_')
        out.append((star, blk, round(freq, 4), line))
    return out


def main(argv):
    drive = 0
    args = list(argv[1:])
    if '--drive' in args:
        i = args.index('--drive')
        drive = int(args[i + 1])
        del args[i:i + 2]
    pos = [a for a in args if not a.startswith('--')]
    # ★ 2026-10-07: THE LEDGER IS NOW TYPESET IN PARTS.  A `table*` float
    # cannot break across a page and the ledger is a row per crossing, so it
    # overran its page and was written over the text beneath it.
    # `ledger_v410.py` splits the body; this gate therefore reads EVERY part
    # and checks the union against the adopted list, because a gate that
    # reads one part of a split table passes on a fragment that is missing
    # half the crossings -- and reports "28 rows against 56" only if someone
    # happens to look.
    frags = pos or [f for f in ('tab_ledger.tex', 'tab_ledger_cont.tex')
                    if os.path.exists(os.path.join(HERE, f))]
    frags = [f if os.path.isabs(f) else os.path.join(HERE, f) for f in frags]
    L = json.load(open(os.path.join(HERE, 'ledger.json')))
    want = L['rows']
    S = L['summary']
    tex = '\n'.join(open(f, errors='ignore').read() for f in frags)
    frag = ', '.join(os.path.basename(f) for f in frags)
    # ★ 2026-10-07: THESE TWO DRIVES WERE SILENT `str.replace` CALLS.  A drive
    # that substitutes nothing leaves a clause nobody has ever seen fire, and
    # this one had already drifted: the ledger is now typeset in TWO parts, so
    # `\hline\n\end{tabular}` occurs twice and drive 1 was adding two rows
    # where it meant to add one, reporting "58 rows against 56".  Both drives
    # now assert their substitution count, so a drive that stops driving is a
    # failure and not a pass.  Four of `prose_v412.py`'s drives had the same
    # shape this round and the assertion fired on two of them for real.
    def _sub(hay, needle, repl, want=1):
        out, n = hay.replace(needle, repl, want), hay.count(needle)
        assert n >= want, ('drive %d substituted %d times, not %d; the '
                           'fragment it drives has changed shape'
                           % (drive, n, want))
        return out

    if drive == 1:
        tex = _sub(tex, '\\hline\n\\end{tabular}',
                   'X & Y & 7 & 999.0000 & 1.0 & n & -- & -- & '
                   'attributed \\\\\n\\hline\n\\end{tabular}')
    if drive == 4:
        tex = _sub(tex, '\\hline\n',
                   '\\hline\n& \\multicolumn{3}{c}{committed $t_0=\\mathrm{median}'
                   '(T)$} & \\multicolumn{3}{c}{adopted $t_0=T_0$} \\\\\n')
    got = rows_of(tex)
    fail = []

    n_want = len(want) if drive != 2 else len(want) - 1
    if len(got) != n_want:
        fail.append('G1 the fragment has %d data rows against %d crossings '
                    'in the adopted list' % (len(got), n_want))

    kg = {(r[1], r[2]) for r in got}
    kw = {((r['eb'] or '--').replace('A002_', ''), round(r['freq'], 4))
          for r in want}
    if drive == 2:
        kw.add(('Xdeadbeef', 1.0))
    extra, miss = sorted(kg - kw), sorted(kw - kg)
    if extra:
        fail.append('G2 the fragment carries %d crossing(s) the adopted list '
                    'does not: %s' % (len(extra), extra[:4]))
    if miss:
        fail.append('G2 the adopted list carries %d crossing(s) the fragment '
                    'does not: %s' % (len(miss), miss[:4]))

    n_att = sum(1 for r in got if re.search(r'(?<!un)attributed', r[3]))
    n_una = sum(1 for r in got if 'unattributed' in r[3])
    want_att = S['n_attributed'] if drive != 3 else S['n_attributed'] + 1
    if (n_att or n_una) and (n_att, n_una) != (want_att,
                                               S['n_unattributed']):
        fail.append('G3 the fragment dispositions are %d attributed / %d '
                    'unattributed against the adopted %d / %d'
                    % (n_att, n_una, want_att, S['n_unattributed']))
    elif not (n_att or n_una):
        fail.append('G3 the fragment carries no disposition column at all, '
                    'so a reader cannot see which crossings the mask '
                    'attributes')

    epochs = re.findall(r'\{(committed|adopted)\s*\$t_0', tex)
    if len(set(epochs)) > 1:
        fail.append('G4 the fragment heads %d epoch conventions (%s); a '
                    'published table states the analysis, not how it changed'
                    % (len(set(epochs)), ', '.join(sorted(set(epochs)))))

    print('ledgergate: %s -- %d data rows against %d adopted crossings'
          % (os.path.basename(frag), len(got), len(want)))
    for f in fail:
        print('  FAIL ' + f)
    print('ledgergate: %d FAIL' % len(fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
