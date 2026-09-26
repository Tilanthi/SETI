#!/usr/bin/env python3
"""Round 82 (v4.04, referee 2 item 1): reconcile the two versions of the
survey's own counts, and say which extraction change removed HD 14055 and
HD 23484.

Referee 2 observed that the manuscript carries a stale "13 flagged windows,
of which 4 are unattributed" beside the current "12 stage-1 windows, of
which 2 are unattributed", and that Table 28(b) listed FOUR unattributed
outliers -- adding HD 14055 and HD 23484 -- under a caption saying two, with
61 Vir at T* = 6.16 / ring 5.88 where the results table gives 5.96 / 5.65.

The referee is right, and the cause is not a typographical one.  Those rows
come from `campaign_v372.json`, a harvest of the external calibration sample
frozen on 2026-09-17, i.e. scored by the pipeline as it then stood -- BEFORE
the ACA control-annulus repair of v3.99.  That repair re-extracted 278 blocks
whose control annuli had been placed using a primary beam computed for a
fixed 12 m dish, which puts an ACA annulus at 58 per cent of its correct
radius.

This generator does not paper over that.  It joins the PRE-repair export
(`frozen_export_v3.81.json`) to the POST-repair one
(`corrected_export_v399.json`) on (execution block, window edges) and reports
what the repair did to each of the three pre-repair unattributed outliers.
The answer is the answer to the referee's question:

  * moving the controls outward changes the noise scale sigma, which is the
    MAD ACROSS the control positions, so the repair moves the STAR's
    statistic as well as the ring's;
  * HD 14055 and HD 23484 fall behind their own rings and stop being stage-1
    events;
  * 61 Vir survives, at 5.96/5.65 -- the value the results table quotes.

Consequence the manuscript must also state: the calibration sample's
measured tail rate is a PRE-repair tail rate, and the repair removed
outliers, so that rate is an over-estimate of the post-repair one and is
quoted as a bound.

-> survey_numbers_round82.tex
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round82.tex')

PRE = json.load(open(os.path.join(HERE, 'frozen_export_v3.81.json')))['rows']
POST = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
CAMP = json.load(open(os.path.join(HERE, 'campaign_v372.json')))

M = {}


def m(k, v):
    M[k] = v


def key(r):
    lo, hi = float(r['flo']), float(r['fhi'])
    # A descending spw writes flo > fhi in the export while the catalogue
    # always writes the lower edge first, so key on min/max or half the
    # windows are silently lost (learned at v4.00, ctrlsep_v400.py).
    return (r['eb'], round(min(lo, hi), 4), round(max(lo, hi), 4))


POSTI = {key(r): r for r in POST}

# ---------------------------------------------------------------- the join
# The three unattributed outliers of the external calibration sample, as
# recorded in the frozen harvest.  Each is matched back into the PRE-repair
# export by its own statistic (the harvest does not carry the block id), then
# forward into the POST-repair export by block and window edges.
rows = []
for u in CAMP['unattrib']:
    cand = [r for r in PRE
            if r.get('star_snr') is not None
            and abs(float(r['star_snr']) - float(u['t'])) < 1e-3
            and abs(float(r['ctrl_max']) - float(u['ctrl'])) < 1e-3]
    assert len(cand) == 1, (u['star'], len(cand))
    pre = cand[0]
    post = POSTI.get(key(pre))
    assert post is not None, ('no post-repair row for', u['star'], key(pre))
    assert post.get('provenance') == 'corrected-geometry', \
        ('not re-extracted: ' + u['star'] + ' ' + str(post.get('provenance')))
    rows.append(dict(star=u['star'].replace('~', ' '),
                     eb=pre['eb'],
                     band=int(pre['band']),
                     flo=min(float(pre['flo']), float(pre['fhi'])),
                     fhi=max(float(pre['flo']), float(pre['fhi'])),
                     pre_t=float(pre['star_snr']),
                     pre_c=float(pre['ctrl_max']),
                     post_t=float(post['star_snr']),
                     post_c=float(post['ctrl_max']),
                     post_nge=int(post['n_ge_star'])))

rows.sort(key=lambda r: -r['pre_t'])
assert len(rows) == 3, len(rows)

# Every one of the three was rank 1 of 513 before the repair, by definition
# of the harvest's "unattributed outlier".
survive = [r for r in rows if r['post_nge'] == 0]
removed = [r for r in rows if r['post_nge'] > 0]
assert len(survive) == 1 and survive[0]['star'].startswith('61 Vir'), survive
assert len(removed) == 2, removed
# ... and the mechanism: in both removed cases the RING rose past the star.
for r in removed:
    assert r['post_c'] > r['post_t'], r

m('RcNPreUnattr', '%d' % len(rows))
m('RcNPreRemoved', '%d' % len(removed))
m('RcNPreSurvive', '%d' % len(survive))
m('RcCampAsOf', CAMP['asof'].split('T')[0])
m('RcRemovedList', ' and '.join(r['star'] for r in removed))

for tag, r in zip(('One', 'Two', 'Three'), rows):
    m('Rc%sStar' % tag, r['star'])
    m('Rc%sBand' % tag, '%d' % r['band'])
    m('Rc%sGHz' % tag, '%.3f' % r['flo'])
    m('Rc%sGHzHi' % tag, '%.3f' % r['fhi'])
    m('Rc%sPreT' % tag, '%.2f' % r['pre_t'])
    m('Rc%sPreC' % tag, '%.2f' % r['pre_c'])
    m('Rc%sPostT' % tag, '%.2f' % r['post_t'])
    m('Rc%sPostC' % tag, '%.2f' % r['post_c'])
    m('Rc%sPostNge' % tag, '%d' % r['post_nge'])

# ------------------------------------------------- how big the repair was
nfix = sum(1 for r in POST if r.get('provenance') == 'corrected-geometry')
m('RcNReExtracted', '%d' % nfix)
m('RcNReExtractedBlocks', '%d' % len({r['eb'] for r in POST
                                      if r.get('provenance') == 'corrected-geometry'}))

# The size of the move, over every window the repair touched and that
# carried a pre-repair counterpart: the ring is what the geometry changes,
# and the star follows it only through the shared noise scale.
dstar, dctrl = [], []
PREI = {key(r): r for r in PRE}
for r in POST:
    if r.get('provenance') != 'corrected-geometry':
        continue
    p = PREI.get(key(r))
    if p is None or p.get('star_snr') is None or r.get('star_snr') is None:
        continue
    dstar.append(float(r['star_snr']) - float(p['star_snr']))
    dctrl.append(float(r['ctrl_max']) - float(p['ctrl_max']))
import statistics as st                                      # noqa: E402
m('RcNCompared', '%d' % len(dstar))
# The MEDIAN change is near zero in both: the repair moves individual
# windows in both directions and does not bias the ensemble.  What it does
# is SCATTER them, so the typical size of the move is the informative
# statistic and is the one quoted.
m('RcMedDStar', '%+.2f' % st.median(dstar))
m('RcMedDCtrl', '%+.2f' % st.median(dctrl))
m('RcAbsDStar', '%.2f' % st.mean(abs(x) for x in dstar))
m('RcAbsDCtrl', '%.2f' % st.mean(abs(x) for x in dctrl))
# The ring is what the geometry changes directly and the star follows it
# only through the shared noise scale, so the ring must move MORE.  If that
# ever reversed, the mechanism described in the text would be wrong.
assert st.mean(abs(x) for x in dctrl) > st.mean(abs(x) for x in dstar), \
    (st.mean(abs(x) for x in dctrl), st.mean(abs(x) for x in dstar))

# ------------------------------------------------ the calibration sample
m('RcCampWindows', '%d' % CAMP['n_windows'])
m('RcCampBlocks', '%d' % CAMP['n_blocks'])
m('RcCampStars', '%d' % CAMP['n_stars'])

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by counts_v404.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('counts_v404: %d pre-repair unattributed outliers; %d removed by the '
      'ACA control-annulus repair (%s), %d survive'
      % (len(rows), len(removed), M['RcRemovedList'], len(survive)))
for r in rows:
    print('   %-10s B%d %9.3f  T %.2f/%.2f -> %.2f/%.2f  (%d controls above)'
          % (r['star'], r['band'], r['flo'], r['pre_t'], r['pre_c'],
             r['post_t'], r['post_c'], r['post_nge']))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
