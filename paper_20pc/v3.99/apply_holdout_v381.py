#!/usr/bin/env python3
r"""Apply the PRE-REGISTERED calibration hold-out to the completed sweep.

The rule is `holdout_rule_v371.py`, committed 2026-09-14T07:10:24Z as
`c75069040eab` -- before the archive sweep finished and before any reserved
block was searched. That timestamp is the whole point: a hold-out chosen
after seeing results is not a hold-out.

    n = int(sha256(canonical execution-block UID)[:8], 16)
    held out iff n mod 5 == 0

with two guards fixed in advance and depending only on UIDs and the
published block list: blocks already in the v3.72 release always stay in the
survey, and no system may lose every one of its blocks.

WHY THIS ROUND NEEDS IT
-----------------------
Up to v3.80 every empirically calibrated statement in the paper -- the rank
displacement, the false-alarm tail factor, the radial profile m(u), and the
claim that stage-1 status alone carries no candidate significance -- was
measured on blocks that were also in the headline sample. That is referee
1's objection to the radial repair, and it was correct. Splitting on a rule
fixed before the data makes every one of those statements out of sample by
construction. It costs 305 windows off the headline and no stars and no
systems at all.

Writes:
    frozen_export_v3.81_survey.json  the headline sample
    holdout_export_v381.json            the calibration sample
    holdout_assignment_v381.json        per-block verdict, the audit trail
"""
import json, collections, sys

import holdout_rule_v371 as HR

FULL = 'frozen_export_v3.81.json'
PUBLISHED = 'frozen_export_v3.60.json'     # the v3.72 released catalogue
SURVEY_OUT = 'frozen_export_v3.81_survey.json'
HOLD_OUT = 'holdout_export_v381.json'

full = json.load(open(FULL))
rows = full['rows']
pub = {r['eb'] for r in json.load(open(PUBLISHED))['rows'] if r['eb']}

# The system identity used by the second guard must be the same grouping the
# paper uses, so take it from the survey statistics engine's own PAIRS rule
# rather than inventing one here.
import survey_stats_systems as SS          # noqa: E402  (local helper)
sysof = SS.system_of

blocks = {}
for r in rows:
    if r['eb']:
        blocks[r['eb']] = sysof(r['star_name'])

assign = HR.assign(blocks, published=pub)
hold = {e for e, v in assign.items() if v == 'holdout'}
surv = set(blocks) - hold

rs = [r for r in rows if r['eb'] in surv]
rh = [r for r in rows if r['eb'] in hold]
assert len(rs) + len(rh) == len(rows), (len(rs), len(rh), len(rows))

# Guard 2 must actually have worked: the headline sample keeps every system.
sys_all = {sysof(r['star_name']) for r in rows}
sys_surv = {sysof(r['star_name']) for r in rs}
assert sys_all == sys_surv, sorted(sys_all - sys_surv)

survey = dict(full)
survey['rows'] = rs
survey['holdout_rule'] = {
    'rule': 'sha256(canonical EB uid)[:8] mod 5 == 0',
    'committed': '2026-09-14T07:10:24Z',
    'commit': 'c75069040eab',
    'guards': ['published blocks always survey', 'no system loses every block'],
}
json.dump(survey, open(SURVEY_OUT, 'w'))
json.dump({'snapshot': full['snapshot'], 'rows': rh,
           'holdout_rule': survey['holdout_rule']}, open(HOLD_OUT, 'w'))
json.dump(assign, open('holdout_assignment_v381.json', 'w'), indent=1)

raw = {e for e in blocks if HR.is_holdout(e)}
print('blocks              : %d' % len(blocks))
print('  raw residue hits  : %d' % len(raw))
print('  kept by guard 1   : %d (already published)' % len(raw & pub))
print('  survey / hold-out : %d / %d (%.1f per cent held out)'
      % (len(surv), len(hold), 100.0 * len(hold) / len(blocks)))
print('windows  survey %d | hold-out %d' % (len(rs), len(rh)))
print('stars    survey %d | hold-out %d'
      % (len({r['star_name'] for r in rs}), len({r['star_name'] for r in rh})))
print('systems  survey %d | hold-out %d (none lost: %s)'
      % (len(sys_surv), len({sysof(r['star_name']) for r in rh}),
         sys_all == sys_surv))
