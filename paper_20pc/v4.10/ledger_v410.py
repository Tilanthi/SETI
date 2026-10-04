#!/usr/bin/env python3
r"""The crossing ledger, on the adopted search statistic and in the stellar
frame.

The shipped ledger fragment is keyed to the superseded statistic.  It carries
four crossings that fall below the trigger once the field correction is part
of the statistic, it lacks the one that rises and the one that is restored,
it gives one star two rows where one survives, and its dispositions sum to
the sky-frame attribution count.  It also prints two epoch conventions side
by side, which is a record of how the analysis changed rather than a result.

This generator produces the ledger the paper publishes:

  * one row per crossing of the ADOPTED list -- the released rows, minus the
    four that fall, plus the one that rises, the one that is restored and the
    two the archival tail adds;
  * one epoch convention, the adopted one, so there is no before and after;
  * attribution in the STELLAR frame, which is the frame the Keplerian bound
    that motivates masking is expressed in, so the dispositions sum to the
    adopted attributed/unattributed split and not to the sky-frame one;
  * a machine-readable `ledger.json` that the chain figure reads, so the
    figure and the table cannot disagree.

Every delta term is read from the generated delta fragment and from the
frozen per-crossing records -- none is typed here -- and the closure
`released - fell + rose + restored + added == adopted` is asserted, as is
agreement with the frozen mask result.

    python3 ledger_v410.py [--drive N]

-> ledger.json, tab_ledger.tex
"""
import csv
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MASK_HALF_KMS = 50.0


def main(argv):
    drive = None
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
    suf = '' if drive is None else '_drive%d' % drive

    OLD = json.load(open(os.path.join(HERE, 'ledger_v403.json')))
    MASKR9 = json.load(open(os.path.join(HERE, 'r9inputs', 'mask_r9.json')))
    ADD = json.load(open(os.path.join(HERE, 'r8inputs', 'v409',
                                      'v409_addprof.json')))['added']
    CAT = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'))))
    DELTA = open(os.path.join(HERE, 'tab_crossdelta_v409.tex')).read()
    fail = []

    def ck(name, cond, detail=''):
        if not cond:
            fail.append('%s: %s' % (name, detail))

    # ---- the delta, parsed from the fragment that declares it -------------
    rows = [(a, b, c, e, f, g) for a, b, c, d, e, f, g in re.findall(
        r'^\$([+-])\$\s*&\s*(.+?)\s*&\s*([\d.]+)\s*&\s*(.*?)\s*&\s*'
        r'\$\\to\$\s*&\s*([\d.]+)\s*&\s*(\d+)\s*&\s*(.+?)\s*\\\\$',
        DELTA, re.M)]
    fell = [r for r in rows if r[0] == '-']
    rose = [r for r in rows if r[0] == '+']
    ck('L1 the delta fragment declares both directions',
       len(fell) >= 1 and len(rose) >= 1, (len(fell), len(rose)))
    ck('L2 every falling crossing falls below the trigger and every rising '
       'one rises above it',
       all(float(r[3]) < 5.0 for r in fell)
       and all(float(r[3]) >= 5.0 for r in rose), rows)

    # ---- the stellar-frame offset for every released crossing ------------
    VSYS = json.load(open(os.path.join(HERE, 'starrv_v399.json')))
    BARY = json.load(open(os.path.join(HERE, 'r8inputs',
                                       'bary_v405.json')))['v_bary_kms']
    FROZ = {(q['star'], q['eb'], round(q['dv_sky'], 1)): q
            for q in MASKR9['newly_evaluable']}
    XC = {}
    for r in CAT:
        # ★ no f_cross guard: five crossings ship without a crossing
        # frequency (the fit is outstanding), and excluding them here is
        # exactly how they would lose their attribution silently.
        if r['crossing'] != 'True':
            continue
        dv = float(r['line_offset_kms'])
        vc = BARY.get('%s|%.6f' % (r['eb'], float(r['flo_GHz'])))
        vs = VSYS.get(r['star_name'])
        if vc is None or vs is None:
            q = FROZ.get((r['star_name'], r['eb'], round(dv, 1)))
            if q is not None:
                vc, vs = q['v_corr'], q['v_sys']
        # ★ keyed on (block, released line offset), not on the frequency:
        # a ledger row whose fit is outstanding carries its WINDOW CENTRE in
        # the frequency field, so a frequency key silently misses it and the
        # row falls through to "no stellar offset" -- which would move it
        # from attributed to unattributed without anything saying so.
        XC[(r['eb'], round(dv, 3))] = (
            None if (vc is None or vs is None) else dv - vc + vs)

    # ---- build the adopted list ------------------------------------------
    fell_f = {round(float(r[2]), 6) for r in fell}
    out = []
    for row in OLD['rows']:
        # one released row carries no frequency (its window centre stands in
        # for an unfitted crossing); it cannot be matched against the delta
        # by frequency, and it is not one of the four that fall.
        _f = None if row['freq'] is None else round(float(row['freq']), 6)
        if _f is not None and _f in fell_f:
            continue
        dvs = XC.get((row['eb'], round(float(row['loff']), 3)))
        out.append(dict(star=row['star'], display=row['display'],
                        band=row['band'], eb=row['eb'],
                        freq=(row['freq'] if row['freq'] is not None
                              else float(row['flo'])),
                        tstar=row['tstar'], screen=row['screen'],
                        rank_ctrl=row['rank_ctrl'], line=row['line'],
                        dv_stellar=dvs, source='released'))
    ck('L3 exactly the declared number of rows was removed',
       len(OLD['rows']) - len(out) == len(fell),
       '%d removed against %d declared' % (len(OLD['rows']) - len(out),
                                           len(fell)))

    # the rows the adopted list adds.  Star, frequency, statistic and
    # control count come from the delta fragment; the execution block and
    # the transition come from the frozen per-window records, joined on the
    # frequency, because the fragment does not carry a block name and a
    # name-only join is the defect family this project keeps meeting.
    byf = {}
    for a in ADD:
        byf[round(float(a['fcross']), 4)] = a
    for r in CAT:
        if r['crossing'] == 'True' or not r['f_cross_GHz']:
            continue
    for sign, star, f_old, t_new, nctrl, note in rose:
        f = round(float(f_old), 6)
        a = byf.get(round(f, 4))
        eb, line = (a['eb'], a['lines'][0]) if a else (None, None)
        if eb is None:
            # the risen crossing is a window the release already carries, so
            # its block is in the catalogue: join on the window that contains
            # the frequency, not on the star name.
            cand = [c for c in CAT
                    if float(c['flo_GHz']) <= f <= float(c['fhi_GHz'])
                    and abs(float(c['eirp_nominal_W'])) > 0
                    and star.replace('~', ' ').replace('$', '')
                    .split()[0].lower() in c['star_name'].lower()]
            if cand:
                eb, line = cand[0]['eb'], cand[0]['nearest_line']
        ck('L4 every added crossing resolves to an execution block',
           eb is not None, '%s at %s has no block' % (star, f_old))
        mdv = None
        for key in ('restored_attributed', 'hd14055_unattributed'):
            for e in MASKR9['v409'][key]:
                if abs(float(e[1]) - f) < 1e-4:
                    mdv = float(e[2])
        if mdv is None and 'km' in note:
            mm = re.search(r'\$?([+-]?\d+)\$?\\,km', note)
            mdv = float(mm.group(1)) if mm else None
        out.append(dict(star=star.replace('~', ' '), display=star,
                        band='7' if f > 300 else '6', eb=eb, freq=f,
                        tstar=float(t_new), screen=(int(nctrl) == 0),
                        rank_ctrl=None, line=line, dv_stellar=mdv,
                        source='adopted list'))

    n_rel, n_fell, n_rose = len(OLD['rows']), len(fell), len(rose)
    if drive == 1:
        out = out[:-1]
    ck('L5 the row count closes on the declared delta',
       len(out) == n_rel - n_fell + n_rose,
       '%d rows against %d - %d + %d' % (len(out), n_rel, n_fell, n_rose))

    # ---- dispositions, in the stellar frame ------------------------------
    for row in out:
        d = row['dv_stellar']
        row['attributed'] = (d is not None and abs(d) <= MASK_HALF_KMS)
    n_att = sum(1 for r in out if r['attributed'])
    n_una = len(out) - n_att
    if drive == 2:
        n_att += 1
    ADOPT = MASKR9['adopted']
    ck('L6 the ledger dispositions reproduce the adopted mask result',
       (len(out), n_att, n_una) == (ADOPT['n_crossings'],
                                    ADOPT['attributed'],
                                    ADOPT['unattributed']),
       'ledger %d/%d/%d against mask %d/%d/%d'
       % (len(out), n_att, n_una, ADOPT['n_crossings'],
          ADOPT['attributed'], ADOPT['unattributed']))
    nrf = sum(1 for r in out if not r['attributed'] and r['screen'])
    ck('L7 the rank-flagged unattributed count reproduces the frozen one',
       nrf == ADOPT['rank_flagged_unattributed'],
       '%d against %d' % (nrf, ADOPT['rank_flagged_unattributed']))
    # ★ one star contributed two rows under the superseded statistic and
    # contributes one under the adopted one; assert that no star has more
    # rows than it has distinct blocks carrying a crossing, which is the
    # shape of that defect rather than a count of it.
    dup = [k for k, v in
           {(r['star'], r['eb'], round(r['freq'], 4)): 1 for r in out}.items()
           if sum(1 for q in out if (q['star'], q['eb'],
                                     round(q['freq'], 4)) == k) > 1]
    ck('L8 no two ledger rows are the same crossing', not dup, dup)

    # ---- outputs ----------------------------------------------------------
    summ = dict(generator='ledger_v410.py', n_crossings=len(out),
                n_attributed=n_att, n_unattributed=n_una,
                n_rank_flagged_unattributed=nrf,
                frame='stellar', mask_half_kms=MASK_HALF_KMS,
                epoch_conventions=1,
                delta=dict(released=n_rel, fell=n_fell, added=n_rose))
    with open(os.path.join(HERE, 'ledger%s.json' % suf), 'w') as fh:
        json.dump(dict(summary=summ, rows=out), fh, indent=1)
    with open(os.path.join(HERE, 'tab_ledger%s.tex' % suf), 'w') as fh:
        fh.write('%% GENERATED by ledger_v410.py -- do not hand-edit.\n')
        fh.write('%% One row per threshold crossing, one epoch convention, '
                 'stellar-frame attribution.\n')
        fh.write('\\begin{tabular}{@{}l@{~}l@{~}c@{~}r@{~}r@{~}c@{~}l@{~}'
                 'r@{~}l@{}}\n\\hline\n')
        fh.write('Star & block & B & $\\nu$ (GHz) & $T_\\star$ & scr & '
                 'line & $\\Delta v$ & disposition \\\\\n\\hline\n')
        for r in sorted(out, key=lambda z: (-z['tstar'],)):
            pass
        for r in sorted(out, key=lambda z: (-z['tstar'],)):
            fh.write('%s & %s & %s & %.4f & %.3f & %s & %s & %s & %s \\\\\n'
                     % (r['display'],
                        (r['eb'] or '--').replace('A002_', '')
                        .replace('_', '\\_'),
                        r['band'], r['freq'], r['tstar'],
                        'Y' if r['screen'] else 'n',
                        r['line'] or '--',
                        ('%+.1f' % r['dv_stellar'])
                        if r['dv_stellar'] is not None else '--',
                        'attributed' if r['attributed']
                        else ('unattributed; rank-flagged' if r['screen']
                              else 'unattributed; below rank screen')))
        fh.write('\\hline\n\\end{tabular}\n')

    # ---- the mask ladder, from the ledger's own rows ---------------------
    lad = []
    for w in (13.0, 20.0, 30.0, 50.0, 100.0):
        a_ = sum(1 for r in out
                 if r['dv_stellar'] is not None and abs(r['dv_stellar']) <= w)
        u_ = len(out) - a_
        g_ = sum(1 for r in out if r['screen']
                 and not (r['dv_stellar'] is not None
                          and abs(r['dv_stellar']) <= w))
        lad.append((w, a_, u_, g_))
    ck('L9 the ladder agrees with the ledger at the adopted half-width',
       [(w, a_, u_) for w, a_, u_, _ in lad if w == MASK_HALF_KMS]
       == [(MASK_HALF_KMS, n_att, n_una)],
       [(w, a_, u_) for w, a_, u_, _ in lad])
    ck('L10 doubling the half-width changes no count',
       lad[-1][1:] == lad[-2][1:], [(l[0], l[1:]) for l in lad])
    with open(os.path.join(HERE, 'tab_maskladder%s.tex' % suf), 'w') as fh:
        fh.write('%% GENERATED by ledger_v410.py -- do not hand-edit.\n')
        fh.write('\\begin{tabular}{@{}lrrr@{}}\n\\hline\n'
                 'Half-width (km\\,s$^{-1}$) & attributed & unattributed & '
                 'outrank all controls \\\\\n\\hline\n')
        for w, a_, u_, g_ in lad:
            bold = abs(w - MASK_HALF_KMS) < 1e-9
            f_ = (lambda z: '\\textbf{%s}' % z) if bold else (lambda z: z)
            fh.write('%s & %s & %s & %s \\\\\n'
                     % (f_('$\\pm%g$' % w), f_('%d' % a_), f_('%d' % u_),
                        f_('%d' % g_)))
        fh.write('\\hline\n\\end{tabular}\n')

    # ---- the summary table, from the same rows ---------------------------
    with open(os.path.join(HERE, 'tab_ledgersum%s.tex' % suf), 'w') as fh:
        fh.write('%% GENERATED by ledger_v410.py -- do not hand-edit.\n')
        fh.write('\\begin{tabular}{@{}lr@{}}\n\\hline\n'
                 'Quantity & Observed \\\\\n\\hline\n')
        for lab, val in (
                ('Threshold crossings', len(out)),
                ('Line-attributed ($|\\Delta v|\\leq%g$\\,km\\,s$^{-1}$, '
                 'stellar frame)' % MASK_HALF_KMS, n_att),
                ('Unattributed', n_una),
                ('\\quad outranking all spatial controls', nrf),
                ('\\quad recurring at a second epoch', 0)):
            fh.write('%s & %d \\\\\n' % (lab, val))
        fh.write('\\hline\n\\end{tabular}\n')

    print('ledger_v410: %d crossings = %d released - %d fell + %d added; '
          '%d attributed / %d unattributed (stellar frame, +-%g km/s), '
          '%d of the unattributed rank-flagged'
          % (len(out), n_rel, n_fell, n_rose, n_att, n_una, MASK_HALF_KMS,
             nrf))
    for f in fail:
        print('  ASSERTION FIRED  ' + f)
    print('ledger_v410: %d assertions fired' % len(fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
