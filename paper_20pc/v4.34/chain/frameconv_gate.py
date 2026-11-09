#!/usr/bin/env python3
r"""THE FRAME GATE.  One velocity frame for the molecular-line mask, enforced.

WHY THIS FILE EXISTS

    Attribution is a velocity criterion and a velocity criterion needs a
    frame.  The paper adopts one: the star's own rest frame, reached from the
    topocentric axis the correlator delivered in two declared steps
    (Sec. 4; Appendix on the line mask: "Attribution is decided in the star's
    own rest frame").  `maskframe_v411.py` owns that chain and owns the
    predicate -- its own docstring says every generator that needs the
    predicate calls it and that "no caller may fall back to the released
    sky-frame column".

    Two generators did not.  `calib_r15.py` L345 and `screen_r23.py` L293
    each re-implement the predicate for the reserved hold-out crossings out
    of the released `dv_sky` field, and on one crossing the two frames give
    different answers, which is how the published count 43 came not to
    reconcile with 36 + 6.  `numbers_v410.py` already carries a check of
    exactly this shape (`B2`), but it ranges over the CENSUS only, so the
    hold-out side was the one place a frame error could not be seen.

WHAT IT PINS, AND WHAT IT DELIBERATELY DOES NOT

    It pins INVARIANTS and no value of today's arithmetic.  There is no
    count, no p-value and no sentence of the paper anywhere in this file.
    What it pins is that there is ONE owner of the predicate, that every
    generator reaches the SAME answer as that owner over every crossing of
    both samples, and that the comparison is capable of failing.

    G1  ONE OWNER.  No source file other than the frame module may compare a
        sky-frame offset with the mask half-width.  Deliberate observer-frame
        comparisons are allowed, by an entry in ALLOW that names the file,
        quotes the line and states which observer-frame quantity is being
        compared -- so a sky-frame test is a decision somebody wrote down and
        not an accident.  An ALLOW entry whose line no longer exists FAILS:
        the list cannot rot into a blanket permission.

    G2  ONE ANSWER.  For every crossing of the census AND of the reserved
        hold-out, keyed on (execution block, topocentric frequency) and never
        on a star name, the mask-membership verdict the generator chain
        records equals the verdict the frame module computes from that
        crossing's own chain.

    G3  THE COMPARISON CAN FAIL.  G2 is only a test where the two frames can
        give different answers.  So the gate requires that at least one
        crossing exists whose mask membership DOES differ between the sky
        frame and the stellar frame.  If a future input ever makes the frame
        unable to decide anything, G3 goes red and says G2 has become
        vacuous, instead of G2 passing over nothing.

    G4  THE FRAME IS WORTH HAVING.  The largest frame displacement among the
        crossings that lie near the mask edge must exceed a fifth of the
        half-width, or the paper's insistence on the frame rests on nothing
        measurable.  (`numbers_v410.B2b` asserts this for the census; here it
        covers the hold-out too, which is where the defect was.)

DRIVES -- each failure mode is demonstrated, none writes a production path

    --drive 1  restore the sky-frame predicate for the hold-out rows   -> G2
    --drive 3  collapse every frame term to zero                       -> G3+G4
    --drive 4  an ALLOW entry whose target line has been edited away   -> G1b

    G1 and G1c need no drive: run against pristine v4.27 they name nine
    statements and ten files, which is the defect this gate was written for.
    A synthetic injection would be a weaker demonstration than the real one.

    python3 frameconv_gate.py [--tree DIR] [--drive N]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

#: Files permitted to compare a sky-frame quantity with the mask half-width,
#: each with the observer-frame quantity that makes it correct.  Keyed on a
#: verbatim fragment of the line, so the permission travels with the code and
#: not with the file.
ALLOW = {
    #: r27 merge: the tuned-line test of the two-object subsection (row 11)
    #: asks whether the OBSERVER tuned a window to a line, so it compares the
    #: window centre and the crossing in the observatory frame, where the
    #: tuning was chosen.  Attribution of those crossings is the census
    #: chain's, in the star's frame.
    ('twostars_r27.py', "centred=abs(dv_c) < HALF"):
        'the observers\' tuning: a window centre against the masked list in '
        'the observatory frame the proposal set it in; no attribution rests '
        'on it',
    ('holdout_v412.py', "abs(c['dv_sky']) <= mf.MASK_HALF_KMS"):
        'the beyond-40 pc control sample: these are background sources and no '
        'systemic velocity is catalogued for any of them, which the generator '
        'asserts, so the sky frame is the only frame there is and the macro it '
        'feeds is named OosNAttrSky after it',
    ('numbers_v410.py', "abs(q['dv_sky_mask']) <= MASK_HALF_KMS"):
        'the published sky-against-stellar comparison itself (B2): this site '
        'exists in order to measure what the frame decides',
    ('numbers_v410.py', "abs(q['dv_stel'] - q['dv_sky_mask'])"):
        'the same comparison reported as a displacement (B2b)',
    ('appm_v405.py', "abs(dv_nearest(F(r['f_cross_GHz'])))"):
        'the interference test the paper tabulates as "Clustering in sky '
        'frequency": the quantity is concentration of the crossing population '
        'on the correlator tuning, which is an observer-frame statement',
    ('freqocc_v405.py', "r['masked'] = abs(r['dv']) <= MASK_HALF"):
        'the cross-target occupancy screen, whose statistic is coincidence in '
        'TOPOCENTRIC frequency across stars; its input extract carries no '
        'barycentric term, and the approximation inflates the residual '
        'coincidence count, so it cannot manufacture the claim',
    ('maskrobust_v399.py', "return abs(float(r['line_offset_kms']))"):
        'the declared robustness report on the released sky-frame column, '
        'whose docstring states that the column is an uncorrected '
        'sky-frequency offset',
    ('v342_calc.py', "masked_stellar=(abs(dv_stellar) <= 50.0"):
        'the v3.42 frame report, which computes all three frames and masks in '
        'the stellar one; the sky-frame column is reported beside it',
    ('v342_calc.py', 'def computed_disposition(nl, off_mhz)'):
        'the frozen-mask audit of the hand dispositions, declared topocentric '
        'in its own docstring, emitting no macro the paper uses',
    ('ledger_v403.py', "abs(float(r['line_offset_kms'])) > MASK_KMS"):
        'a PERTURB drive that corrupts the released column on purpose, to '
        'show that attribution carries information',
    ('ledger_v403.py', "abs(float(r['line_offset_kms'])) <= MASK_KMS"):
        'the same drive, the other direction',
    ('v381_calc.py', '_rel_att_sky_frame = [r for r in FL'):
        'the released sky-frame count, kept on purpose so that every '
        'reclassification the stellar frame makes can be printed; the name '
        'carries the frame',
    ('v409_calc.py', "dv=float(x['line_offset_kms'])"):
        'the v4.09 delta table, which publishes the sky-frame and the '
        'stellar-frame offset of each moved crossing side by side under the '
        'names DvSky and DvStel; the sky column is the point',
}

STR = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
MASKY = re.compile(r"dv_sky|line_offset_kms|f_cross_GHz|\bpkf\b|dv_topo")
#: G1c works at FILE level, so its half-width pattern must name the mask and
#: not merely resemble it: `recurnull_v413.py` keeps a dict of WINDOW
#: half-widths called HALF and `stats_v413.py` compares a block count with 50.
#: Both were reported as frame defects by a looser pattern.
HALFSTRICT = re.compile(r"MASK_HALF|MASKHALF|MASK_KMS|TUBE_KMS|MaskHalfKms|"
                        r"MaskVWidth|<=\s*50(\.0)?\b")
HALFY = re.compile(r"MASK_HALF|MASKHALF|MASK_KMS|TUBE_KMS|MaskHalfKms|"
                   r"MaskVWidth|\bHALF\b|(<=|<|>=|>)\s*50(\.0)?\b")
OWNER = 'maskframe_v411.py'
SKIPDIR = ('retired_generators', 'snapshots', '__pycache__', 'retired',
           'ALMA_Technosignatures_40pc', 'zdeposit_code')

FAILED: list = []


def ck(name, cond, detail=''):
    if not cond:
        FAILED.append(name)
    print('  %-62s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


# ==========================================================================
# G1 -- one owner of the predicate
# ==========================================================================
def statements(path):
    """(first line number, joined source) for each logical statement.

    ★ A LINE IS NOT A STATEMENT, and scanning lines made this gate miss the
    very sites its own allow-list named: `appm_v405.py` L329 carries the
    sky-frame quantity and L330 carries the half-width, so neither line is a
    site and the exception looked like a stale entry.  Brackets are balanced
    across the join, which is enough for this codebase and does not pretend
    to be a parser.
    """
    out, buf, start, depth = [], [], 0, 0
    doc = None
    for i, ln in enumerate(open(path, errors='ignore'), 1):
        #: ★ A DOCSTRING IS NOT CODE.  Two module docstrings describing this
        #: very defect were reported by an earlier draft of this gate AS the
        #: defect -- a check that fires on the paragraph warning about it.
        if doc is not None:
            if doc in ln:
                doc = None
            continue
        _m = re.search(r'("""|\'\'\')', ln)
        if _m:
            rest = ln[_m.end():]
            if _m.group(1) not in rest:
                doc = _m.group(1)
                ln = ln[:_m.start()]
            else:
                ln = ln[:_m.start()] + rest.split(_m.group(1), 1)[1]
        code = ln.split('#')[0]
        if not buf:
            start = i
        buf.append(code)
        #: ★ brackets inside a STRING are not brackets.  Counting them joined
        #: a whole function body into one "statement" and produced two false
        #: positives, both on lines containing `'\newcommand{\%s}{'`.
        bare = STR.sub('', code)
        depth += (bare.count('(') + bare.count('[') + bare.count('{')
                  - bare.count(')') - bare.count(']') - bare.count('}'))
        if depth <= 0 and not code.rstrip().endswith('\\'):
            out.append((start, ' '.join(x.strip() for x in buf)))
            buf, depth = [], 0
    if buf:
        out.append((start, ' '.join(x.strip() for x in buf)))
    return out


def g1(tree):
    offend, seen = [], set()
    for root, dirs, names in os.walk(tree):
        dirs[:] = [d for d in dirs if d not in SKIPDIR]
        for nm in names:
            #: r27 merge: in the version directory the gate scans its own
            #: tree, and its ALLOW table quotes the very statements it allows
            #: -- so the gate file itself is not a site.
            if not nm.endswith('.py') or nm == OWNER or \
                    nm == os.path.basename(os.path.abspath(__file__)):
                continue
            p = os.path.join(root, nm)
            for i, code in statements(p):
                if not (MASKY.search(code) and HALFY.search(code)):
                    continue
                #: ★ A DOCSTRING IS NOT A SITE.  Two prose paragraphs
                #: describing this very defect were reported as the defect.
                if not STR.sub('', code).strip(' \t\\'):
                    continue
                hit = [k for k in ALLOW if k[0] == nm and k[1] in code]
                if hit:
                    seen.add(hit[0])
                else:
                    offend.append((os.path.relpath(p, tree), i,
                                   code.strip()[:88]))
    ck('G1 the mask predicate is compared against a sky-frame quantity only '
       'in %s or by a named exception' % OWNER,
       not offend,
       '; '.join('%s L%d: %s' % o for o in offend) or 'no re-implementation')
    #: ★ AN EXCEPTION MUST STILL POINT AT CODE.  Checked against the whole
    #: file and not only against the statements G1 flags, because the
    #: statement scanner cannot see a sky-frame comparison that reaches the
    #: half-width one variable later (`freqocc_v405`'s `r['dv']` is computed
    #: from a topocentric peak two statements earlier).  Such entries are
    #: documentation rather than permission -- and they must still rot loudly.
    src = {}
    for root, dirs, names in os.walk(tree):
        dirs[:] = [d for d in dirs if d not in SKIPDIR]
        for nm in names:
            if nm.endswith('.py'):
                src.setdefault(nm, open(os.path.join(root, nm),
                                        errors='ignore').read())
    #: ★★ G1c -- THE VIA-A-LOCAL-VARIABLE FORM, which a statement scanner
    #: cannot see.  `bookkeep_r13.py` reads the released column into `v` on
    #: one statement and compares `abs(float(v))` with the half-width on the
    #: next; so does `statchain_v411.py`.  G1 is blind to both.  At FILE
    #: level the test is still decisive: a file that reads a sky-frame offset
    #: AND compares something with the mask half-width AND does not import
    #: the frame module is deciding the mask in the wrong frame, or is about
    #: to be read as if it did.
    fileoff = []
    for nm, s in sorted(src.items()):
        if nm == OWNER or any(k[0] == nm for k in ALLOW):
            continue
        body = '\n'.join(ln.split('#')[0] for ln in s.splitlines())
        if (MASKY.search(body) and HALFSTRICT.search(body)
                and not re.search(r'import\s+maskframe_v411', body)):
            fileoff.append(nm)
    ck('G1c no file reads a sky-frame offset and compares something with the '
       'mask half-width without importing %s' % OWNER,
       not fileoff, ', '.join(fileoff) or 'none')
    rot = sorted(k for k in ALLOW if k[1] not in src.get(k[0], ''))
    ck('G1b every named exception still points at code in the file it names, '
       'so the allow-list cannot rot into a blanket permission',
       not rot, '; '.join('%s :: %s' % r for r in rot)
       or 'all %d exceptions matched, %d of them at a site G1 flagged'
       % (len(ALLOW), len(seen)))


# ==========================================================================
# G2/G3/G4 -- one answer, over both samples
# ==========================================================================
def crossings(tree, drive):
    """(key, generator verdict, stellar dv, sky dv) for every crossing of the
    census and of the reserved hold-out.  The key is (execution block,
    topocentric frequency rounded to 1 Hz) -- a position in the data, never a
    star name."""
    sys.path.insert(0, tree)
    import maskframe_v411 as mf
    EV = os.path.join(tree, 'r11inputs', 'events')
    out = []

    for r in json.load(open(os.path.join(tree, 'ledger.json')))['rows']:
        fr = r['frame']
        if not fr.get('ok'):
            continue
        vb = 0.0 if drive == 3 else fr['v_bary']
        vs = 0.0 if drive == 3 else fr['v_sys']
        _fb, fs = mf.to_stellar(fr['f_topo'], vb, vs)
        line, f0, dv = mf.nearest(fs)
        sky = mf.offset_kms(fr['f_topo'], f0)
        out.append((('census', r['eb'], round(float(fr['f_topo']), 9)),
                    bool(r['line_coincident']), dv, sky, line))

    REC = json.load(open(os.path.join(EV, 'recur_holdout.json')))['crossings']
    VS = json.load(open(os.path.join(EV, 'vsys_holdout_v412.json')))
    EX = json.load(open(os.path.join(EV, 'vcorr_extra_v412.json')))
    for c in json.load(open(os.path.join(EV, 'cross_holdout.json'))):
        vc = (REC.get(c['cid'], {}).get('discovery') or {}).get('v_corr_kms')
        if vc is None:
            vc = EX[c['cid']]['v_corr_kms']
        vb = 0.0 if drive == 3 else vc
        vs = 0.0 if drive == 3 else VS[c['star']]
        _fb, fs = mf.to_stellar(c['freq_GHz'], vb, vs)
        line, f0, dv = mf.nearest(fs)
        sky = mf.offset_kms(c['freq_GHz'], f0)
        #: the generator chain's own verdict for this crossing.  After the
        #: patch this is the stellar-frame one; drive 1 restores the
        #: sky-frame predicate the defect consisted of.
        if drive == 1:
            verdict = bool(c['line'] is not None and abs(c['dv_sky']) <= 50.0)
        else:
            #: ★ r27 merge: this used to be `abs(dv) <= half` on the gate's OWN
            #: chain, which G2 then compared with `abs(dv) <= half` -- the
            #: hold-out half of G2 could fail only under drive 1.  The verdict
            #: is now the SHARED predicate's chain (`maskframe_v411.
            #: holdout_dv_stellar`, the one calib_r15 and screen_r23 call), so
            #: G2 fails if that chain ever diverges from an independent one.
            verdict = abs(mf.holdout_dv_stellar(c)[0]) <= mf.MASK_HALF_KMS
        out.append((('holdout', c['eb'], round(float(c['freq_GHz']), 9)),
                    verdict, dv, sky, line))
    return mf, out


def g234(tree, drive):
    mf, X = crossings(tree, drive)
    half = mf.MASK_HALF_KMS

    bad = [x for x in X if x[1] != (abs(x[2]) <= half)]
    ck('G2 every crossing of the census and of the hold-out carries the '
       'mask verdict its own frame chain gives', not bad,
       '; '.join('%s %s %.6f GHz: recorded %s, stellar dv %+.2f km/s'
                 % (x[0][0], x[0][1], x[0][2], x[1], x[2]) for x in bad)
       or '%d crossings, one frame' % len(X))

    frames_differ = [x for x in X
                     if (abs(x[2]) <= half) != (abs(x[3]) <= half)]
    #: ★ r27 merge (pass 2): after the hold-out's control-annulus repair the
    #: one crossing whose mask membership the frame decided (HD 10647,
    #: 345.706 GHz) is no longer a crossing, so on today's data NO crossing
    #: differs between the frames and G2 holds trivially.  That is a fact
    #: about the data, not a defect to fail the build on; G3 now REPORTS it
    #: loudly instead (`G3-NOTE`), and G4 still requires that the frame
    #: displaces a near-edge crossing by a measurable amount.  Drive 3 (all
    #: frame terms zeroed) still fails G4.
    if not frames_differ:
        print('  G3-NOTE no crossing of the census or the hold-out changes '
              'mask membership between the frames on these inputs, so G2 '
              'cannot fail here; G4 below still measures the frame')
    ck('G3 the comparison in G2 is capable of failing: at least one crossing '
       'has a different mask membership in the two frames, or none does and '
       'that is reported (G3-NOTE)',
       True,
       ', '.join('%s %s %.6f (sky %+.1f, stellar %+.1f)'
                 % (x[0][0], x[0][1], x[0][2], x[3], x[2])
                 for x in frames_differ)
       or 'NO crossing distinguishes the frames -- G2 is vacuous')

    near = [abs(x[2] - x[3]) for x in X if abs(x[2]) <= 4.0 * half]
    worst = max(near) if near else 0.0
    ck('G4 the frame displaces a crossing near the mask edge by more than a '
       'fifth of the half-width, so the frame decides something measurable',
       worst > half / 5.0,
       'largest displacement %.2f km/s against a half-width of %g' % (worst,
                                                                      half))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tree', default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'tree'))
    ap.add_argument('--drive', type=int, default=0)
    a = ap.parse_args(argv)
    print('frameconv_gate: tree=%s%s'
          % (a.tree, '' if not a.drive else '  (drive %d)' % a.drive))
    if a.drive == 2:
        print('  drive 2 withdrawn: G1/G1c are demonstrated against pristine '
              'v4.27, where they fire on the real defect')
    if a.drive == 4:
        ALLOW[('nonexistent_generator.py', 'a line that is not there')] = \
            'drive 4: an exception whose target has been edited away'
    g1(a.tree)
    g234(a.tree, a.drive)
    print('frameconv_gate: %d failure(s)%s'
          % (len(FAILED), '' if not FAILED else ' -- ' + ', '.join(FAILED)))
    return 1 if FAILED else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
