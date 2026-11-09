#!/usr/bin/env python3
r"""Round 3110: THE CHANCE COMPARISON WITHOUT THE SPECIES ADDED TO THE MASK
AFTER THE CROSSINGS WERE INSPECTED.

The line mask was completed after the crossings had been examined (App. I),
and one species -- sulphur monoxide -- was added to it then.  The adopted
probabilities and the allowance for further crossings (\CeProbNull,
\CeAddLim) are therefore conditional on the adopted, post hoc, mask; the
two-reading correction (\FrTwoTrialP) covers the choice of extraction field
and not this one.  This generator gives the comparison a reader can set beside
them: the same chance generator, run with sulphur monoxide dropped from the
mask on BOTH sides (`chance_v414.py --mask noso`: the null's masked share and
the attribution of every observed crossing), and otherwise identical.

It does not recompute anything itself.  M1 requires the production record
(chance_v414.json) to reproduce the published adopted comparison, so the
variant differs from it by the mask and nothing else; M2 requires the variant
to attribute fewer crossings and expect more (the mask only removes); M3 that
the crossings it moves are exactly the ones whose nearest masked transition is
sulphur monoxide.

    python3 maskpost_r31.py [--drive N]
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 3110
GEN = 'chance_v414.py'

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])

OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round3110.tex' if DRIVE is None
                       else 'numbers/survey_numbers_round3110_drive%d.tex' % DRIVE)
OUT = []
fail = []


def m(name, val):
    assert name.isalpha(), name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label[:70], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def published(name, fn='numbers/survey_numbers_round310.tex'):
    for ln in open(os.path.join(HERE, fn), errors='ignore'):
        mm = re.match(r'\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$', ln)
        if mm and mm.group(1) == name:
            return mm.group(2)
    raise AssertionError('not published: %s' % name)


def run_variant():
    args = [sys.executable, os.path.join(HERE, GEN), '--mask', 'noso']
    sfx = '_masknoso'
    if DRIVE is not None:
        args += ['--drive', '0']
        sfx = '_drive0' + sfx
    target = os.path.join(HERE, 'chance_v414%s.json' % sfx)
    if os.path.exists(target):
        os.remove(target)
    p = subprocess.run(args, cwd=HERE, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    assert os.path.exists(target), ('%s did not write %s (rc %d)\n%s'
                                    % (GEN, target, p.returncode,
                                       p.stdout.decode()[-2000:]))
    return json.load(open(target))


ADO = json.load(open(os.path.join(HERE, 'chance_v414.json')))
NOS = run_variant()
if DRIVE == 1:
    NOS = dict(ADO)                  # the variant stops differing

# M1 the production record is the published comparison
ck('M1 the adopted record reproduces the published comparison',
   str(ADO['observed']) == published('CeObs')
   and '%.1f' % ADO['e_chance'] == published('CeExp')
   and ADO['added_population_limit'] == int(published('CeAddLim')),
   '%d / %.2f / %d against %s / %s / %s'
   % (ADO['observed'], ADO['e_chance'], ADO['added_population_limit'],
      published('CeObs'), published('CeExp'), published('CeAddLim')))
# M2 dropping a species can only move crossings out of the attributed set and
#    can only raise the expectation
ck('M2 without the added species more crossings are unattributed and more '
   'are expected', NOS['observed'] > ADO['observed']
   and NOS['e_chance'] > ADO['e_chance'],
   '%d > %d, %.2f > %.2f' % (NOS['observed'], ADO['observed'],
                             NOS['e_chance'], ADO['e_chance']))
# M3 the moved crossings are the ones the added species attributes
import maskframe_v411 as mf                                    # noqa: E402
_rows_a = {(r['eb'], round(float(r['freq']), 6)) for r in ADO['observed_rows']}
_rows_n = {(r['eb'], round(float(r['freq']), 6)) for r in NOS['observed_rows']}
_moved = sorted(_rows_n - _rows_a)
ck('M3 the crossings that move are exactly those the added species '
   'attributes, and none leaves the unattributed set',
   _rows_a <= _rows_n and len(_moved) == NOS['observed'] - ADO['observed'],
   '%d moved: %s' % (len(_moved), _moved))

_mc = NOS.get('mc_report', {}).get('CeProbNull', {})
_pr = _mc.get('printed') or '%.2f' % NOS['p_at_least_observed_control_only']
m('MkNoSOObs', '%d' % NOS['observed'])
m('MkNoSOExp', '%.1f' % NOS['e_chance'])
m('MkNoSOProb', _pr)
m('MkNoSOAddLim', '%d' % NOS['added_population_limit'])
m('MkNoSONMoved', '%d' % len(_moved))
m('MkNoSOSpecies', 'sulphur monoxide')

if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    if DRIVE is None:
        raise SystemExit(1)

hdr = ['%% GENERATED by maskpost_r31.py (round %d) -- do not hand-edit.' % ROUND,
       '% The chance comparison with the species added after the crossings',
       '% were inspected (sulphur monoxide) dropped from the mask on both sides.']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
print('maskpost_r31: adopted %d vs %.2f (P %s); without %s %d vs %.2f (P %s), '
      'bound %d; %d crossings move -> %s'
      % (ADO['observed'], ADO['e_chance'], published('CeProbNull'),
         'SO', NOS['observed'], NOS['e_chance'], _pr,
         NOS['added_population_limit'], len(_moved),
         os.path.basename(OUT_TEX)))
