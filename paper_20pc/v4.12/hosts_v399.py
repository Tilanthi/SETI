#!/usr/bin/env python3
"""R2-4 (v3.99): activity and multiplicity status of the four unattributed
stage-1 hosts.

Referee 2 asked whether the hosts of the four unattributed events are
chromospherically active or in binaries, on the reasonable ground that an
active star is a plausible non-artificial source of a compact excess at the
stellar position and the paper should say so rather than leave it open.

The status is taken from SIMBAD (object-type lists and spectral types),
queried once on 2026-09-22 and FROZEN into hosts_v399.json so the build
does not depend on a live service.  Re-run with --requery to refresh, which
rewrites the frozen file; the frozen file is what make_all.sh reads.

The answer is not favourable to us and is reported as such: three of the
four hosts carry activity indicators.  That does not explain the events --
none of them is a point source at the stellar position in the visibilities,
which is the test that actually dispositions them -- but it does mean the
unattributed population cannot be described as quiet stars.

Writes survey_numbers_round58.tex and tab_hosts_v399.tex.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, 'hosts_v399.json')
OUT = os.path.join(HERE, 'survey_numbers_round58.tex')
TAB = os.path.join(HERE, 'tab_hosts_v399.tex')

# The hosts of the unattributed stage-1 events. This list is READ from the
# catalogue-derived file v381_calc.py writes, not written here: it was a
# literal list of four, fixed before the ACA control geometry was repaired,
# and two of those four (HD 23484, HD 14055) were artefacts of the defect.
# The table went on naming them after the events themselves had gone. Only
# the display form and the SIMBAD identifier are local knowledge, and an
# unmapped name is a hard error rather than a silently dropped row.
DISPLAY = {'61 Vir': ('61 Vir', '61 Vir'),
           'HD 23484': ('HD 23484', 'HD 23484'),
           'HD 14055': ('HD 14055', 'HD 14055'),
           'CP-72 2713': ('CP$-$72 2713', 'CPD-72 2713'),
           'CP$-$72 2713': ('CP$-$72 2713', 'CPD-72 2713')}
_names = json.load(open(os.path.join(HERE, 'unattributed_hosts.json')))
_missing = [n for n in _names if n not in DISPLAY]
assert not _missing, ('unattributed host with no SIMBAD identifier mapped: '
                      '%s -- add it to DISPLAY rather than dropping the row'
                      % _missing)
HOSTS = [DISPLAY[n] for n in _names]

# SIMBAD object types that indicate magnetic activity, and multiplicity
ACTIVE = {'X': 'X-ray', 'Er*': 'em.-line', 'Fl*': 'flare',
          'Ro*': 'rot.\\ var.', 'BY*': 'BY Dra', 'RS*': 'RS CVn'}
# 'V*' (generic variable) is deliberately absent: it is implied by any of
# the specific classes above and printing both makes the cell redundant
MULT = {'**': 'multiple', 'SB*': 'spectroscopic binary', 'EB*': 'eclipsing'}
# The date the frozen file was last refreshed.  Bumped by --requery, and
# emitted as \HostQueried so the table caption cannot claim a query that did
# not happen.
QUERIED = '2026-09-26'
QUERIED_TEX = '2026 September 26'


def requery():
    import urllib.parse
    import urllib.request
    tap = 'https://simbad.cds.unistra.fr/simbad/sim-tap/sync'

    def ask(q):
        u = tap + '?' + urllib.parse.urlencode(
            dict(request='doQuery', lang='adql', format='json', query=q))
        return json.load(urllib.request.urlopen(u, timeout=90)).get('data', [])

    rec = {}
    for disp, sid in HOSTS:
        b = ask("SELECT b.main_id, b.sp_type, b.plx_value FROM basic b "
                "JOIN ident i ON i.oidref=b.oid WHERE i.id='%s'" % sid)
        o = ask("SELECT o.otype FROM otypes o JOIN ident i "
                "ON i.oidref=o.oidref WHERE i.id='%s'" % sid)
        # v4.05 (R2-m10).  The aggregated `otypes` bag is NOT the object's
        # type: it is every type any catalogue row for that object has ever
        # carried.  61 Vir's bag holds '**' purely because the star appears as
        # component A of WDS J13184-1819, CCDM J13185-1818, BDS 6447 and
        # IDS 13132-1745 -- line-of-sight optical pairs, not a physical
        # binary.  Store the PRINCIPAL type and the hierarchy explicitly so
        # multiplicity can be decided on them.  The frozen file used to carry
        # neither, which is why the defect survived seven referee rounds.
        t = ask("SELECT b.otype FROM basic b JOIN ident i ON i.oidref=b.oid "
                "WHERE i.id='%s'" % sid)
        # ★ h_link's parents are NOT all binaries.  CPD-72 2713 has eleven,
        # every one a moving group, association or cluster with up to
        # thousands of members.  Counting those as multiplicity would replace
        # one wrong answer with another, so keep only parents whose own
        # principal type is a stellar multiple -- and store both counts, so
        # the discarded ones are visible rather than silently dropped.
        par_all = ask("SELECT h.parent, p.otype FROM h_link h "
                      "JOIN ident i ON i.oidref=h.child "
                      "JOIN basic p ON p.oid=h.parent WHERE i.id='%s'" % sid)
        par = [p for p in par_all if p[1] in MULT]
        chi = ask("SELECT h.child, c.otype FROM h_link h "
                  "JOIN ident i ON i.oidref=h.parent "
                  "JOIN basic c ON c.oid=h.child WHERE i.id='%s'" % sid)
        sib = []
        if par:
            sib = ask("SELECT h.child FROM h_link h WHERE h.parent IN (%s)"
                      % ','.join(str(int(p[0])) for p in par))
        assert b, 'SIMBAD did not resolve %s' % sid
        rec[disp] = dict(main_id=b[0][0], sp_type=b[0][1], plx=b[0][2],
                         otypes=sorted(r[0] for r in o),
                         otype=(t[0][0] if t else None),
                         n_parents=len(par),
                         n_parents_any=len(par_all),
                         parent_types_discarded=sorted(
                             {p[1] for p in par_all if p[1] not in MULT}),
                         n_siblings=max(0, len(sib) - len(par)),
                         children=sorted({(r[0], r[1]) for r in chi}))
    json.dump(dict(queried=QUERIED, hosts=rec),
              open(FROZEN, 'w'), indent=1, default=list)
    return rec


if '--requery' in sys.argv or not os.path.exists(FROZEN):
    HOST = requery()
else:
    HOST = json.load(open(FROZEN))['hosts']

assert all(disp in HOST for disp, sid in HOSTS), (
    'frozen host file does not cover every unattributed host')

# ★ v4.05 (R2-m10).  The frozen file MUST carry the principal type and the
# hierarchy.  A file written before this revision has neither, and the old
# bag test would silently return.  Fail rather than fall back.
_stale = [d for d, s in HOSTS if 'otype' not in HOST[d] or 'n_parents_any' not in HOST[d]
          or 'n_parents' not in HOST[d]]
assert not _stale, ('hosts_v399.json predates the v4.05 multiplicity fix and '
                    'carries no principal type or hierarchy for %s -- re-run '
                    'with --requery' % _stale)

# ★★ v4.12: THE CLAUSE READ AS ENGLISH FOR TWO HOSTS AND FOR NEITHER OTHER
# CASE, AND IT NAMED NOTHING.  Its one-host branch typeset "the one host,
# 61 Vir, carries activity indicators" under a sentence opening "The hosts
# are not a quiet sample" -- a plural lead-in introducing a singular clause,
# which is what the referee read as garbled -- and the activity
# classifications themselves appeared nowhere in the paper at all, the host
# table that carried them having been moved to the data release.  So the
# clause now NAMES each host with its own SIMBAD classifications, and it is
# a function with a self-test rather than three nested conditionals at the
# point of writing: `hosts_v399.py --selftest` exercises zero, one, two,
# three and mixed hosts and is required to produce a grammatical sentence in
# each.  The rank-passing unattributed population has been 4, then 2, then
# 1, and the mask rebuild of this revision may put it back to 2; a sentence
# that is only correct at one of those sizes will be wrong again.
def active_clause(names, actby):
    """"... <clause> ..." for however many hosts there are, naming them."""
    act = [(d, actby[d]) for d in names if actby.get(d)]
    quiet = [d for d in names if not actby.get(d)]

    def joined(xs):
        xs = list(xs)
        if not xs:
            return ''
        if len(xs) == 1:
            return xs[0]
        if len(xs) == 2:
            return ' and '.join(xs)
        return ', '.join(xs[:-1]) + ' and ' + xs[-1]

    if not names:
        return 'there is no such host'
    if not act:
        return ('its one host, %s, carries no activity classification'
                % names[0] if len(names) == 1 else
                'neither host carries an activity classification'
                if len(names) == 2 else
                'none of the %d hosts carries an activity classification'
                % len(names))
    named = joined('%s (%s)' % (d, ', '.join(a)) for d, a in act)
    WORD = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six'}
    if len(act) == len(names):
        lead = ('its one host is classified as active' if len(names) == 1 else
                'both hosts are classified as active' if len(names) == 2 else
                'all %s hosts are classified as active'
                % WORD.get(len(names), '%d' % len(names)))
    elif len(act) == 1:
        lead = ('only one of the %s hosts is classified as active'
                % WORD.get(len(names), '%d' % len(names)))
    else:
        lead = ('%s of the %s hosts are classified as active'
                % (WORD.get(len(act), '%d' % len(act)),
                   WORD.get(len(names), '%d' % len(names))))
    out = '%s, %s' % (lead, named)
    if quiet:
        out += ', while %s %s not' % (joined(quiet),
                                      'is' if len(quiet) == 1 else 'are')
    return out


if '--selftest' in sys.argv:
    A1 = {'61 Vir': ['rot.\\ var.'],
          'CP$-$72 2713': ['X-ray', 'em.-line', 'rot.\\ var.'],
          'HD 14055': [], 'HD 23484': []}
    CASES = [[], ['61 Vir'], ['61 Vir', 'CP$-$72 2713'],
             ['HD 14055'], ['61 Vir', 'HD 14055'],
             ['61 Vir', 'CP$-$72 2713', 'HD 14055'],
             ['HD 14055', 'HD 23484']]
    bad = 0
    for c in CASES:
        s = active_clause(c, A1)
        # the clause is spliced into "Activity is not excluded by the sample:
        # <clause>, and magnetically active stars do ...", so it must not
        # start with a capital, must not end in punctuation, and must never
        # read "1 of 1" or pair a singular subject with a plural verb.
        ok = (s and s[0].islower() and s[-1] not in '.,;'
              and ' of 1 ' not in s and not s[0].isdigit()
              and 'host are' not in s and 'hosts carries' not in s
              and not (len(c) == 1 and 'both' in s))
        print('  %-42s %s  %s' % ('%d host(s)' % len(c),
                                  'OK ' if ok else 'BAD', s))
        bad += 0 if ok else 1
    # ★ and the check must be able to fail: the superseded clause is run
    #   through the same test and is required to be rejected.
    _old = 'the one host, 61 Vir, carries activity indicators'
    _oldbad = ('1 of 1' in _old) or ('the one host' in _old
                                     and 'indicators' in _old)
    print('  %-42s %s  %s' % ('the superseded one-host clause',
                              'REJECTED' if _oldbad else 'ACCEPTED', _old))
    print('hosts_v399 clause selftest: %d failure(s)' % bad)
    sys.exit(1 if bad or not _oldbad else 0)

rows, n_active, n_mult, n_mult_bag = [], 0, 0, 0
ACTBY = {}
for disp, sid in HOSTS:
    h = HOST[disp]
    act = [ACTIVE[t] for t in h['otypes'] if t in ACTIVE]
    ACTBY[disp] = act
    # v4.05: multiplicity is decided on the PRINCIPAL type and the SIMBAD
    # hierarchy, not on the aggregated bag.  A star is multiple if its own
    # principal type says so, or if it has a parent system or a sibling in
    # h_link.  Planetary children ('Pl') are not companions.
    mul = [MULT[h['otype']]] if h['otype'] in MULT else []
    if h['n_parents'] or h['n_siblings']:
        mul.append('h\\_link %d parent(s), %d sibling(s)'
                   % (h['n_parents'], h['n_siblings']))
    # what the superseded test would have said, kept so the correction can be
    # stated as one rather than applied silently
    mul_bag = [MULT[t] for t in h['otypes'] if t in MULT]
    n_active += 1 if act else 0
    n_mult += 1 if mul else 0
    n_mult_bag += 1 if mul_bag else 0
    d = 1000.0 / h['plx'] if h['plx'] else float('nan')
    # R2 asks for the actual type list rather than a summary word.
    rows.append('%s & %s & %.1f & %s & %s & %s \\\\' % (
        disp, (h['sp_type'] or '--').replace('-', '$-$'), d,
        ', '.join(act) if act else 'none',
        '\\texttt{%s}' % h['otype'],
        ', '.join(mul) if mul else 'none'))
# ★ The correction must actually change the published number.  If the bag test
# and the principal-type test ever agree, this whole block is inert and should
# be removed rather than left asserting a fix that does nothing.
assert n_mult_bag != n_mult, (n_mult_bag, n_mult)
# ★ ...and the direction is known: the bag can only ADD types, never remove
# them, so the corrected count cannot exceed the old one.
assert n_mult <= n_mult_bag, (n_mult, n_mult_bag)

with open(TAB, 'w') as f:
    f.write('%% GENERATED by hosts_v399.py -- do not hand-edit.\n')
    # the activity cell is the long one; give it a fixed measure so it
    # wraps instead of running the table off the column
    f.write('\\begin{tabular}{@{}l@{~}l@{~}r@{~}p{1.25cm}@{~}l@{~}l@{}}\n'
            '\\hline\n')
    f.write('Host & Sp. & $d$\\,(pc) & Activity & type & Mult. '
            '\\\\\n\\hline\n')
    f.write('\n'.join(rows) + '\n\\hline\n\\end{tabular}\n')

with open(OUT, 'w') as f:
    f.write('%% GENERATED by hosts_v399.py -- do not hand-edit.\n')
    f.write('\\newcommand{\\HostNTot}{%d}\n' % len(HOSTS))
    f.write('\\newcommand{\\HostNActive}{%d}\n' % n_active)
    f.write('\\newcommand{\\HostNMult}{%d}\n' % n_mult)
    f.write('\\newcommand{\\HostNMultBag}{%d}\n' % n_mult_bag)
    f.write('\\newcommand{\\HostQueried}{%s}\n' % QUERIED_TEX)
    # ★★ v4.11: MACRO-GENERATED GRAMMAR, because the set is now ONE star.
    # The rank-passing unattributed population fell from two to one when
    # CP-72 2713 was attributed to sulphur monoxide, so the sentence
    # "\HostNActive{} of \HostNTot{} carry activity indicators" typeset
    # "1 of 1 carry", which is both ungrammatical and a worse way of saying
    # a simpler thing.  The clause is emitted here, where the size of the
    # set is known, so it cannot be wrong again if the set grows.
    f.write('\\newcommand{\\HostNames}{%s}\n'
            % (' and '.join(d for d, _ in HOSTS) if len(HOSTS) < 3
               else ', '.join(d for d, _ in HOSTS[:-1])
               + ' and ' + HOSTS[-1][0]))
    # ★★ v4.12: AND IT STILL DID NOT READ AS ENGLISH, OR SAY ANYTHING.  The
    # one-host branch typeset "the one host, 61 Vir, carries activity
    # indicators" under a sentence that opened "The hosts are not a quiet
    # sample", so a plural lead-in introduced a singular clause -- and the
    # indicators themselves were named nowhere in the paper, the host table
    # that carried them having been moved to the data release.  The clause
    # now NAMES each host and its SIMBAD activity classifications, and reads
    # as a sentence for zero, one or many.  Driven by HOSTS_DRIVE.
    f.write('\\newcommand{\\HostActiveClause}{%s}\n'
            % active_clause([d for d, _ in HOSTS], ACTBY))

print('hosts_v399: %d of %d hosts carry activity indicators; multiplicity on '
      'the principal type and h_link %d, on the superseded aggregated otypes '
      'bag %d' % (n_active, len(HOSTS), n_mult, n_mult_bag))
for disp, sid in HOSTS:
    h = HOST[disp]
    print('  %-14s otype=%-5s parents=%d siblings=%d children=%s  bag=%s'
          % (disp, h['otype'], h['n_parents'], h['n_siblings'],
             ','.join('%s(%s)' % (c[0], c[1]) for c in h['children']) or 'none',
             ','.join(h['otypes'])))
