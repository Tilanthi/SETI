#!/usr/bin/env python3
"""R2-num 28: list the ALMA project codes the searched data came from.

ALMA's data-use policy requires the project codes of archival data to be
cited in the paper itself, not only in a machine-readable deposit. The
Acknowledgements said the blocks span "36 proposal codes" and pointed the
reader at the release; the count was a literal, and it is wrong -- the
execution blocks in the frozen catalogue carry 51 distinct codes.

The list is built from the same execution-block set the rest of the paper
counts (the catalogue's own `eb` column), resolved through the harvested
archive metadata, and the generator asserts that every block resolves. A
block whose code could not be recovered would otherwise drop out of an
acknowledgement silently, which is the failure mode the policy exists to
prevent.

Writes survey_numbers_round67.tex and tab_projcodes_v400.tex.
"""
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round67.tex')
TAB = os.path.join(HERE, 'tab_projcodes_v400.tex')

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

codes, unresolved, from_archive = {}, [], []
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
