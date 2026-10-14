#!/usr/bin/env python3
"""The ALMA project codes the searched data came from.

ALMA's data-use policy requires the project codes of archival data to be
traceable. The Acknowledgements said the blocks span "36 proposal codes" and
pointed the reader at the release; the count was a literal, and it is wrong
-- the execution blocks in the frozen catalogue carry 51 distinct codes.

★ The codes are no longer set in type. 65 of them in an acknowledgement is
padding, and traceability is a property of the deposit, not of the page: so
this generator now writes `project_codes_v413.csv`, one row per execution
block carrying its proposal code and its observing date, and asserts that
the file it has just written covers every execution block the catalogue
contains and names every code the count \\NProjCodes stands for. That is
the check the \\input of the typeset list used to stand in for, moved to
where the claim now is. The typeset fragment is still written, because it
costs nothing and the deposit may as well carry a human-readable form of
the same list, but nothing inputs it.

Driven: PROJ_DRIVE=drop empties the frozen per-block archive record and the
"every block must resolve" assertion must fire; PROJ_DRIVE=csvdrop writes
the deposit file one row short and the coverage assertion must fire.

The list is built from the same execution-block set the rest of the paper
counts (the catalogue's own `eb` column), resolved through the harvested
archive metadata, and the generator asserts that every block resolves. A
block whose code could not be recovered would otherwise drop out of an
acknowledgement silently, which is the failure mode the policy exists to
prevent.

Writes survey_numbers_round67.tex, tab_projcodes_v400.tex and
project_codes_v413.csv.
"""
import csv
import datetime
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round67.tex')
TAB = os.path.join(HERE, 'tab_projcodes_v400.tex')
DEP = os.path.join(HERE, 'project_codes_v413.csv')

CSVF = os.path.join(HERE, 'per_target_results_v3.99.csv')
META = os.path.join(HERE, 'archive_meta_v381.json')

FROZEN_MOUS = json.load(open(os.path.join(HERE, 'projcodes_mous_v400.json')))
# ★★★ v4.12 (R2 minor 9).  Two execution blocks carry NO member OUS in the
# harvested snapshot, so neither the direct nor the member-OUS route can
# reach them, and the Acknowledgements named them as unresolved.  The note
# below used to say the archive TAP service "would not answer for them".
# That was wrong: `SELECT proposal_id ... WHERE asdm_uid LIKE '%<block>%'`
# answers for both, on all three mirrors.  They are ordinary science blocks
# of accepted proposals -- 2023.1.00487.S (Band 10, HD 61005) and
# 2016.1.00878.S (Band 9, AU Mic) -- and ALMA's data-use policy requires
# their codes to be cited, so they are now resolved and acknowledged.  The
# record is frozen with its query and its date because this generator must
# not depend on a live service.
FROZEN_EB = json.load(open(os.path.join(
    HERE, 'projcodes_eb_v412.json')))['blocks']

ROWS = list(csv.DictReader(open(CSVF)))
EBS = sorted({r['eb'] for r in ROWS})
meta = json.load(open(META))['ebs']

missing = [e for e in EBS if e not in meta]
assert not missing, ('no archive metadata for %d execution block(s), so their '
                     'project codes cannot be acknowledged: %s'
                     % (len(missing), missing[:5]))

# obscore carries the project code for only a minority of execution
# blocks directly; the rest are resolved through their member OUS, which
# is the same indirection the archive-scope bookkeeping already uses. An
# EB that resolves through neither is a hard error.
by_mous = {}
for e, m in meta.items():
    for p in (m.get('project') or []):
        for o in (m.get('member_ous') or []):
            by_mous.setdefault(o, set()).add(p)

codes, unresolved, from_archive, by_eb = {}, [], [], {}
if os.environ.get('PROJ_DRIVE') == 'drop':
    FROZEN_EB = {}            # the fourth route must be load-bearing
for e in EBS:
    got = set(meta[e].get('project') or [])
    if not got:
        for o in (meta[e].get('member_ous') or []):
            got |= by_mous.get(o, set())
    if not got:
        for o in (meta[e].get('member_ous') or []):
            if o in FROZEN_MOUS:
                got.add(FROZEN_MOUS[o])
    if not got and e in FROZEN_EB:
        got.add(FROZEN_EB[e]['project'])
        from_archive.append(e)
    if not got:
        unresolved.append(e)
        continue
    for p in got:
        codes.setdefault(re.sub(r'^ADS/JAO\.ALMA#', '', p), set()).add(e)
    by_eb[e] = sorted(re.sub(r'^ADS/JAO\.ALMA#', '', p) for p in got)
# ★ An acknowledgement that quietly omits a project code is the failure
#   ALMA's policy exists to prevent, so EVERY block must resolve.
assert not unresolved, (
    '%d execution block(s) have no project code by any route: %s'
    % (len(unresolved), unresolved[:5]))
# ★ ...and the fourth route must be doing work, or it is dead weight
#   pretending to be a fix.  Driven: PROJ_DRIVE=drop empties the record and
#   the assertion above must fire.
assert from_archive, ('the frozen per-block archive record resolves nothing; '
                      'either the snapshot now carries these blocks\' member '
                      'OUS, in which case delete the record, or the record is '
                      'keyed wrongly')
for e in from_archive:
    assert meta[e].get('array'), e
    assert FROZEN_EB[e]['project'] in codes, e

ORDER = sorted(codes)
# cross-check against the block count the rest of the paper quotes
_neb = None
for f in sorted(os.listdir(HERE)):
    if f.startswith('survey_numbers') and f.endswith('.tex'):
        m = re.search(r'\\newcommand\{\\NEB\}\{(\d+)\}',
                      open(os.path.join(HERE, f), errors='replace').read())
        if m:
            _neb = int(m.group(1))
assert _neb is None or _neb == len(EBS), (
    'project-code list is built from %d execution blocks but the paper '
    'quotes NEB = %s' % (len(EBS), _neb))

with open(TAB, 'w') as fh:
    fh.write('%% GENERATED by projcodes_v400.py -- do not hand-edit.\n')
    fh.write(', '.join('\\mbox{%s}' % c.replace('_', '\\_') for c in ORDER))
    fh.write('\n')


# ------------------------------------------------------------- the deposit
# ★ This file is what the Acknowledgements and the Data Availability
#   section now point at, so it must exist, it must cover every block, and
#   it must be the SAME list the printed count stands for.  An
#   acknowledgement that quietly omits a project code is the failure ALMA's
#   policy exists to prevent, and moving the list off the page does not move
#   that obligation anywhere.
# ★ The epochs come from the same frozen record the rest of the paper's
#   temporal bookkeeping uses, NOT from `archive_meta`'s `t_min`: that field
#   is populated for 102 of the 404 blocks, and a deposit silently missing
#   three quarters of its dates would have been the exact failure this
#   generator already guards against for the codes.  `epochs_v386.json`
#   carries all 404 and records for each whether the epoch is the block's
#   own or its scheduling block's, so the provenance is deposited with the
#   value rather than averaged into it.
EPOCHS = json.load(open(os.path.join(HERE, 'epochs_v386.json')))
MJD0 = datetime.date(1858, 11, 17)


def _epoch(e):
    mjd = EPOCHS['mjd'].get(e)
    if mjd in (None, ''):
        return '', '', ''
    d = (MJD0 + datetime.timedelta(days=int(float(mjd)))).isoformat()
    return '%.6f' % float(mjd), d, EPOCHS['source'].get(e, '')


_rows = [(e, ';'.join(by_eb[e])) + _epoch(e) for e in EBS]
if os.environ.get('PROJ_DRIVE') == 'csvdrop':
    _rows = _rows[1:]             # the coverage assertion must fire
with open(DEP, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['eb', 'project_code', 'epoch_mjd', 'date_utc',
                'epoch_source'])
    w.writerows(_rows)

_back = list(csv.DictReader(open(DEP)))
_dep_ebs = [r['eb'] for r in _back]
_dep_codes = {c for r in _back for c in r['project_code'].split(';') if c}
assert sorted(_dep_ebs) == EBS and len(_dep_ebs) == len(set(_dep_ebs)), (
    'the deposited project-code table covers %d of the catalogue\'s %d '
    'execution blocks, so the Acknowledgements\' pointer to it is false for '
    '%s' % (len(set(_dep_ebs) & set(EBS)), len(EBS),
            sorted(set(EBS) - set(_dep_ebs))[:5]))
assert _dep_codes == set(ORDER), (
    'the deposited table names %d codes and \\NProjCodes says %d: %s'
    % (len(_dep_codes), len(ORDER),
       sorted(_dep_codes ^ set(ORDER))[:5]))
assert sum(1 for r in _back if not r['date_utc']) == 0, (
    'the deposited table carries no epoch for %d block(s), and both the '
    'Acknowledgements and the Data Availability section claim one for every '
    'block' % sum(1 for r in _back if not r['date_utc']))
assert {r['epoch_source'] for r in _back} <= {'block', 'ous'}, (
    'unknown epoch provenance in the deposit: %s'
    % sorted({r['epoch_source'] for r in _back} - {'block', 'ous'}))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by projcodes_v400.py -- do not hand-edit.\n')
    fh.write('\\newcommand{\\NProjCodes}{%d}\n' % len(ORDER))
    fh.write('\\newcommand{\\NProjCodeUnres}{%d}\n' % len(unresolved))
    fh.write('\\newcommand{\\ProjCodeUnresList}{%s}\n'
             % ', '.join('\\texttt{%s}' % u.replace('_', '\\_')
                         for u in sorted(unresolved)))
    # ★ the whole sentence, so the Acknowledgements cannot go on describing
    #   an empty set.  When every block resolves there is nothing to say.
    fh.write('\\newcommand{\\ProjCodeUnresClause}{%s}\n'
             % ('' if not unresolved else
                ' The archive metadata exposes no proposal code for %s of '
                'the \\NEB{} blocks (\\ProjCodeUnresList), which are '
                'therefore not represented in that list.'
                % ('one' if len(unresolved) == 1 else len(unresolved))))
    fh.write('\\newcommand{\\ProjCodeEbMax}{%d}\n'
             % max(len(v) for v in codes.values()))
    fh.write('\\newcommand{\\ProjCodeBiggest}{%s}\n'
             % max(ORDER, key=lambda c: len(codes[c])))

print('projcodes_v400: %d distinct project codes over %d execution blocks '
      '(largest contributes %d); %d block(s) unresolved: %s'
      % (len(ORDER), len(EBS), max(len(v) for v in codes.values()),
         len(unresolved), sorted(unresolved)))
