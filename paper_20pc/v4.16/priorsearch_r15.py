#!/usr/bin/env python3
r"""priorsearch_r15.py -- round 600.  The two published searches above 30 GHz
that reached nearby stars, as macros read out of the papers' own sentences.

★★★ WHY THIS GENERATOR EXISTS.  The opening claim of this paper was "no
published search above that frequency has reached a star within 40 pc".  It was
FALSE: Steffes & DeBoer (1994) observed 40 solar-type stars within 23 pc at
203 GHz, and Mauersberger et al. (1996) included tau Cet and eps Eri -- two
stars of this very sample -- among 17 targets at the same line.  The sentence
has been rewritten to say what those two searches covered, which is the only
form of the claim that is both true and still strong.

But the rewrite typed five of their numbers straight into LaTeX, and a number
typed into LaTeX is checked by nothing.  This round has already been caught
mis-attributing two external constants -- the "nominal 0.2 per cent" bandpass
accuracy that does not appear anywhere in the 35 pages of ALMA Technical Note
15, and a Band 8 flux accuracy attributed to a Proposer's Guide that states a
different figure -- and in both cases what let the error live was a provenance
string naming a document and no page.

So every one of these numbers is published as a macro, read from
`r15inputs/integrate/priorsearch_r15.json`, which carries for each value the
SENTENCE of the source that states it.  The assertions are not of the value
against itself: each one requires the number to appear, AS A NUMBER, inside the
quotation it is attributed to.  That is the same discipline
`make_fig_context_v410.py` applies to the comparison programmes' detection
thresholds, and it is the only kind of check that can catch a value drifting
away from its source.

Macros (round 600):
    \SbPriorNSearch   how many such searches the literature holds
    \SbPriorNStarA    Steffes & DeBoer's star count
    \SbPriorDistA     their distance limit, pc
    \SbPriorFreqGHz   the positronium hyperfine line, GHz -- both searches
    \SbPriorNStarB    Mauersberger et al.'s target count
    \SbPriorBandMHz   the total bandwidth they covered, MHz
    \SbPriorNOursB    how many of THIS sample's stars their list names
    \SbPriorRatio     this survey's union bandwidth over theirs, as a factor

    python3 priorsearch_r15.py [--drive N]

Drives 1-6, each breaking exactly one clause and required to fire.  No drive
writes a path the unperturbed run writes: the suffix follows the FLAG.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round600%s.tex' % SFX)

REC = json.load(open(os.path.join(HERE, 'r15inputs', 'integrate',
                                  'priorsearch_r15.json'), encoding='utf-8'))

FAILED = []


def ck(name, cond, detail=''):
    print('  %-4s %-78s %s' % (name.split()[0], name, 'PASS' if cond
                               else 'FAIL'), end='')
    print(('  ' + detail) if detail else '')
    if not cond:
        FAILED.append(name.split()[0])


def _quoted(entry, drive_break=False):
    """The value, required to appear as a number inside its own quotation."""
    v, q = entry['value'], entry['quote']
    if drive_break:
        v = v + 1
    here = re.search(r'(?<![0-9.])%d(?![0-9])' % v, q) is not None
    return v, q, here


S = {s['key']: s for s in REC['searches']}
A, B = S['Steffes1994'], S['Mauersberger1996']

# ------------------------------------------------------------------ P1
# Every published value appears as a number in the sentence it is taken from.
# This is the clause that would have caught the Technical Note 15 figure.
_vals, _bad = {}, []
for who, sr in (('A', A), ('B', B)):
    for field, entry in sr['values'].items():
        brk = (DRIVE == 1 and who == 'A' and field == 'n_star')
        v, q, here = _quoted(entry, brk)
        _vals[who + '.' + field] = v
        if not here:
            _bad.append('%s %s = %s is not a number in the sentence it is '
                        'attributed to (%s): %r'
                        % (sr['key'], field, v, entry['where'], q[:90]))
ck('P1 every value published here appears as a number inside the quotation of '
   'the source sentence it is attributed to',
   not _bad, '%d value(s) over %d searches%s'
   % (len(_vals), len(S), '' if not _bad else '; ' + _bad[0]))

# ------------------------------------------------------------------ P2
# The two searches are the same line, which is what makes "a single spectral
# line" true of both of them together.  Stated by the data, not by us.
_fa = A['values']['freq_GHz']['value']
_lineB = re.search(r'(?<![0-9.])(\d{3})\.\d+\s*GHz',
                   B['values']['band_MHz']['quote'])
_fb = int(_lineB.group(1)) if _lineB else None
if DRIVE == 2:
    _fb = 115
ck('P2 both searches are at ONE frequency, read from each paper separately, '
   'which is what makes "a single spectral line" a statement about the pair',
   _fb is not None and _fa == _fb,
   'Steffes %s GHz, Mauersberger %s GHz' % (_fa, _fb))

# ------------------------------------------------------------------ P3
# ★★★ THE CLAUSE THAT FOUND SOMETHING.  Their target list names tau Cet and
# eps Eri, and the obvious reading -- "two of the stars searched here" -- is
# WRONG: tau Cet is in the census and eps Eri is not, because eps Eri's whole
# star band is withheld from the search by the rule of App. D (12 windows,
# \NEpsWithheld).  So the overlap with the SEARCHED sample is one star, and
# Section 1 is careful to say only what their list contained, which is true.
# What this clause requires is that every star they name be ACCOUNTED FOR on
# this side -- in the census or in the declared withheld set -- so that a
# star cannot drop silently out of the comparison and leave the sentence
# resting on a set nobody checked.  It is resolved by name against both
# files, with the aliases written out, because a name join is where this
# project loses rows.
CAT = list(csv.DictReader(open(os.path.join(HERE,
                                            'per_target_results_v3.99.csv'),
                               encoding='utf-8')))
HARVEST = json.dumps(json.load(open(os.path.join(HERE,
                                   'corrected_export_v399.json'),
                                    encoding='utf-8')))


def _norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


CENSUS = {}
for r in CAT:
    CENSUS.setdefault(_norm(r['star_name']), set()).add(r['search_class'])
ALIAS = {'eps eri': ('eps Eri', 'epsilon Eri', 'HD 22049'),
         'tau cet': ('tau Cet', 'HD 10700')}
_named = list(B['our_stars_named'])
if DRIVE == 3:
    _named = _named + ['Betelgeuse']
_in_census, _withheld, _missing = [], [], []
for nm in _named:
    cands = (nm,) + ALIAS.get(nm.lower(), ())
    hit = [c for c in cands if _norm(c) in CENSUS]
    if hit:
        _in_census.append(hit[0])
    elif any(re.search(r'"%s[_" ]' % re.escape(c), HARVEST) for c in cands):
        _withheld.append(nm)
    else:
        _missing.append(nm)
ck('P3 every star their target list names is accounted for here -- in the '
   'searched census or in the withheld harvest -- and none falls silently '
   'out of the comparison',
   not _missing and len(_in_census) + len(_withheld) == len(_named)
   and len(_in_census) > 0,
   '%d searched %s, %d withheld %s%s'
   % (len(_in_census), _in_census, len(_withheld), _withheld,
      '' if not _missing else '; UNACCOUNTED FOR: %s' % _missing))

# ------------------------------------------------------------------ P4
# ...and the overlap that IS searched carries Class A coverage, or the
# comparison would be with the archive rather than with the carrier search.
_cls = sorted({c for f in _in_census for c in CENSUS[_norm(f)]})
if DRIVE == 4:
    _cls = ['B']
ck('P4 the overlap that is searched here carries Class~A coverage, so the '
   'comparison is with the carrier experiment and not merely with the '
   'archive',
   'A' in _cls, 'classes held by %s: %s' % (_in_census, _cls))


def texnum(name):
    """A value already published by another generator, read back by name."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(os.listdir(HERE)):
        if fn.startswith('survey_numbers') and fn.endswith('.tex') \
                and '_drive' not in fn:
            for m in pat.finditer(open(os.path.join(HERE, fn),
                                       encoding='utf-8').read()):
                if m.group(1).strip() and not m.group(1).startswith('\\'):
                    v = m.group(1).strip()
    if v is None:
        raise SystemExit('macro %s not found' % name)
    return float(v)


# ------------------------------------------------------------------ P5
# The comparison the sentence rests on: this survey's union bandwidth against
# theirs.  Read from round 53 rather than restated, and required to be a large
# factor -- if it ever stops being one, the sentence stops being worth making.
_our_GHz = texnum('DnuA')
_their_MHz = float(REC['line_width_MHz'])
if DRIVE == 5:
    _their_MHz = _our_GHz * 1000.0
RATIO = _our_GHz * 1000.0 / _their_MHz
ck('P5 the bandwidth comparison the sentence rests on is a factor of more '
   'than a hundred, computed from this survey\'s own union and theirs',
   RATIO > 100,
   '%.1f GHz against %.0f MHz = x%.0f' % (_our_GHz, _their_MHz, RATIO))

# ------------------------------------------------------------------ P6
# The line both searched is inside the range this survey covers, or "above
# that frequency" would not place them in the same band as this work at all.
_lo, _hi = texnum('SurvFreqLoA'), texnum('SurvFreqHiA')
_f = float(_fa)
if DRIVE == 6:
    _f = 20.0
ck('P6 the line both searches used lies inside the range searched here, so '
   'the two are comparable and not merely adjacent',
   _lo <= _f <= _hi, '%.0f GHz inside %.0f-%.0f GHz' % (_f, _lo, _hi))

M = []


def m(name, val):
    M.append((name, val))


m('SbPriorNSearch', '%d' % REC['n_searches'])
m('SbPriorNStarA', '%d' % A['values']['n_star']['value'])
m('SbPriorDistA', '%d' % A['values']['dist_pc']['value'])
m('SbPriorFreqGHz', '%d' % _fa)
m('SbPriorNStarB', '%d' % B['values']['n_star']['value'])
m('SbPriorBandMHz', '%d' % B['values']['band_MHz']['value'])
m('SbPriorNOursB', '%d' % len(_in_census))
m('SbPriorNOursHeld', '%d' % len(_withheld))
m('SbPriorRatio', '%d' % round(RATIO))

with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('%% GENERATED by priorsearch_r15.py -- do not hand-edit.\n')
    for k, v in M:
        assert k.isalpha(), k      # a LaTeX macro name is letters only
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('wrote %s (%d macros)' % (os.path.basename(OUT), len(M)))
if FAILED:
    print('FAILED: %s' % ', '.join(FAILED))
    sys.exit(1)
print('priorsearch_r15: %d checks, 0 FAILED' % 6)
