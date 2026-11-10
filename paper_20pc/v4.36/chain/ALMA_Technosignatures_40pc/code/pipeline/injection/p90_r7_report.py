#!/usr/bin/env python3
"""Turn p90_r7_result.json into the numbers the paper needs, and a markdown
summary. Reads only; computes nothing that the campaign did not measure.

Emits, per stratum: P90 through the trigger alone, through trigger +
visibility localisation, and through the round-6 committed epoch convention for
comparison; the 68 per cent interval from the cluster bootstrap over
configurations; the configuration-to-configuration transfer spread; and the two
mandatory checks.

THE TRANSFER BRACKET (R2-M3.3). The paper currently carries two brackets from
two earlier campaigns. One replaces both: the spread of each configuration's
OWN P90 about the pooled value, quoted as a multiplicative range. It is a
property of this campaign alone and needs no assumption about how one window's
completeness transfers to another, because it is measured on 40-odd windows
spanning both arrays, four bands and both channel classes.

Usage: p90_r7_report.py <result.json> <out.md>
"""
import json
import sys

import numpy as np

res = json.load(open(sys.argv[1]))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
S = {s['stratum']: s for s in res['strata']}
ORDER = [k for k in ('all', 'class A', 'class B', '12 m', 'ACA 7 m') if k in S]
ORDER += sorted(k for k in S if k.startswith('band'))


def f(v, top):
    return ('%.2f' % v) if v is not None else '>%.0f (never reaches 90%%)' % top


lines = []
w = lines.append
w('# Round-7 completeness: P90 through the new candidate chain')
w('')
w('Generated %s from `p90_r7_result.json`. Chain: **%s**.'
  % (res['generated'], res['chain']))
w('')
w('Criterion: %s. Injector: `%s`, response `%s`, peak fraction %.3f at channel '
  'centre and %.4f at a channel boundary.'
  % (res['criterion']['source'], res['injector']['script'],
     res['injector']['response'], res['injector']['peak_fraction_centre'],
     res['injector']['peak_fraction_edge']))
w('')
w('## The two mandatory checks')
w('')
top = S['all']
w('| check | requirement | measured |')
w('|---|---|---|')
w('| null: uninjected passes scored at the same cells | 0 recovered | '
  '**%d of %d** through the trigger, **%d** through trigger+localisation |'
  % (top['null_recovered'], top['null_n'], top['null_recovered_localised']))
w('| positive control at %.0f x threshold | >= 0.95 | **%.3f** trigger, '
  '**%.3f** trigger+localisation |'
  % (res['positive_control'], top['positive_control_frac'],
     top['positive_control_frac_localised']))
w('')
w('`campaign_valid = %s`. %s'
  % (res['campaign_valid'],
     'Both pass, so the completeness below may be quoted.'
     if res['campaign_valid'] else
     '**A check has FAILED: the campaign is invalid and no completeness '
     'number from it may be quoted.**'))
w('')
w('## P90 / S_trig, by stratum')
w('')
w('| stratum | configs | blocks | tones | arrays | bands | **trigger** | '
  '68 % CI | **trigger + localisation** | 68 % CI | *r6-committed epoch* |')
w('|---|--:|--:|--:|---|---|--:|---|--:|---|--:|')
for k in ORDER:
    s = S[k]
    w('| %s | %d | %d | %d | %s | %s | **%s** | %s | **%s** | %s | %s |'
      % (k, s['n_units'], s['n_blocks'], s['n_tones'],
         ', '.join(s['arrays']), ', '.join(s['bands']),
         f(s['P90_over_trigger'], s['ladder_top']),
         ('%.2f-%.2f' % tuple(s['P90_ci68'])) if s['P90_ci68'] else '-',
         f(s['P90_loc_over_trigger'], s['ladder_top']),
         ('%.2f-%.2f' % tuple(s['P90_loc_ci68'])) if s['P90_loc_ci68'] else '-',
         f(s['P90_loc_r6committed_over_trigger'], s['ladder_top'])))
w('')
w('## The transfer bracket (R2-M3.3), one, replacing both')
w('')
w('| stratum | configs with a defined P90 | min | 16th | median | 84th | max '
  '| **bracket about the pooled value** |')
w('|---|--:|--:|--:|--:|--:|--:|---|')
for k in ORDER:
    s = S[k]
    t = s['transfer_spread_loc']
    if not t or t['median'] is None:
        continue
    pooled = s['P90_loc_over_trigger']
    br = ('x%.2f to x%.2f' % (t['min'] / pooled, t['max'] / pooled)) \
        if pooled else '-'
    w('| %s | %d of %d | %.2f | %.2f | %.2f | %.2f | %.2f | %s |'
      % (k, t['n_defined'], t['n_units'], t['min'], t['p16'], t['median'],
         t['p84'], t['max'], br))
w('')
w('The bracket is the range of individual configurations\' own P90 relative to '
  'the pooled value for that stratum, measured on this campaign only. A '
  'configuration whose P90 is undefined -- recovery never reaches 90 per cent '
  'within the ladder -- is counted in `configs` and excluded from the '
  'percentiles, and the count of both is given so the exclusion is visible.')
w('')
w('## What the epoch defect costs, measured')
w('')
w('Same tones, same criterion, only the drift reference epoch differing:')
w('')
w('| stratum | trigger + localisation, corrected epoch | under the r6 '
  'committed epoch | factor |')
w('|---|--:|--:|--:|')
for k in ORDER:
    s = S[k]
    a, b = s['P90_loc_over_trigger'], s['P90_loc_r6committed_over_trigger']
    fac = ('%.2f' % (b / a)) if (a and b) else ('> %.2f' % (s['ladder_top'] / a)
                                               if a else '-')
    w('| %s | %s | %s | %s |'
      % (k, f(a, s['ladder_top']), f(b, s['ladder_top']), fac))
w('')
w('## Recovery ladders')
w('')
for k in ('all', 'class A', 'class B'):
    if k not in S:
        continue
    s = S[k]
    w('### %s (%d configurations, %d tones)' % (k, s['n_units'], s['n_tones']))
    w('')
    w('| amplitude / S_trig | tones | trigger | trigger + localisation | '
      'r6-committed epoch |')
    w('|--:|--:|--:|--:|--:|')
    for r in s['ladder']:
        w('| %.2f | %d | %.3f | %.3f | %.3f |'
          % (r['amp_over_trig'], r['n'], r['frac_trigger'],
             r['frac_trigger_and_localised'],
             r['frac_trigger_and_localised_r6committed']))
    w('')
w('## Provenance')
w('')
w('- configurations scored %d, failed %d, positive-control failures %d'
  % (res['n_units_scored'], res['n_units_failed'],
     len(res['positive_control_failures'])))
if res['positive_control_failures']:
    w('- excluded by the positive control: %s'
      % '; '.join('%s (%s)' % (a, b) for a, b in
                  res['positive_control_failures']))
if res['failed']:
    w('- not scored: %s'
      % '; '.join('%s (%s)' % (d['tag'], d['status']) for d in res['failed']))
w('- ladder %s, positive control %.0f x, %d tones requested per pass'
  % (res['ladder'], res['positive_control'], res['n_tone_requested']))
w('- reported estimator: %s' % res['estimator']['reported'])
w('- comparison estimator: %s' % res['estimator']['r6committed'])
w('- control frequencies: %s' % res['estimator']['control_frequencies'])

txt = '\n'.join(lines) + '\n'
if OUT:
    open(OUT, 'w').write(txt)
    print('written', OUT, len(txt), 'bytes')
else:
    print(txt)
