#!/usr/bin/env python3
r"""Build the job list for the cell-level search: one entry per window, with
the profile that carries that window's ADOPTED statistic already resolved.

THE RESOLUTION, AND WHY IT IS NOT A NAME JOIN
    Five profile sets exist and they disagree about the capitalisation of the
    same star's directory (`tau_Cet` against `Tau_Cet`, `HR_1010` against
    `Hr_1010`).  A join on that string silently returns the PRE-REPAIR profile
    of every repaired window -- which is what the first version of this file
    did, and 150 windows came back carrying the statistic the repair replaced,
    including the four crossings the repair takes below the trigger.

    A window is identified by its block, its spectral-window number and its
    two edges, taken as min/max of the pair because a descending window is
    stored reversed in one product and not in another.  Among the candidates a
    profile is accepted only if its own maximum reproduces the window's
    adopted statistic -- the repaired value where `repaired_v409.csv` carries
    one, the released value otherwise -- to 1e-4 relative.  Where none does,
    the window is listed as unresolved with its candidates and their values.

    A profile may be claimed by at most one window.  Two catalogue rows for
    the same component of HD 139084 B resolve to one file, and counting that
    window twice would count its cells twice.

THE ARCHIVAL-TAIL STRATUM
    Six retained profiles belong to blocks the released catalogue does not
    tabulate window by window.  Two of them hold a published crossing.  They
    are searched and labelled, never merged into the released census, and the
    inventory is read rather than named, so nothing here carries a list of
    which blocks they are.
"""
import collections
import csv
import json
import os
import re
import sys

PAPER = '/workspace/SETI/paper_20pc/v4.16'
sys.path.insert(0, PAPER)
import maskframe_v411 as mf                                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cells_jobs.json')
GATE_TOL = 1e-4

W = json.load(open(os.path.join(HERE, 'worklist_all_v409.json')))
INV = json.load(open(os.path.join(HERE, 'cells_inventory.json')))
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
REP, REPS = {}, {}
for r in csv.DictReader(open(os.path.join(PAPER, 'repaired_v409.csv'))):
    REP[(r['eb'], int(r['spw']))] = float(r['star_peak_snr_repaired'])
    REPS[(r['eb'], int(r['spw']))] = (float(r['smin_Jy_repaired']) * 1e3,
                                      float(r['rms_mJy_repaired']),
                                      float(r['on_source_s_repaired']))


def wkey(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


def pkey(stem):
    p = stem.rstrip('/').split('/')
    return p[-3] + '__' + p[-1]


def spwof(key):
    m = re.search(r'_spw(\d+)$', key)
    return int(m.group(1)) if m else None


CATK = collections.defaultdict(list)
for i, r in enumerate(CAT):
    CATK[wkey(r['eb'], r['flo_GHz'], r['fhi_GHz'])].append(i)

BYEBSPW = collections.defaultdict(list)
for p in INV:
    BYEBSPW[(p['eb'], p['spw'])].append(p)

WLSTEM = {}
for x in W:
    WLSTEM[(x['eb'], spwof(pkey(x['stem'])), round(min(x['lo'], x['hi']), 3),
            round(max(x['lo'], x['hi']), 3))] = x['stem']


def stem_from_profile(p):
    """The extraction product behind a profile.  The profile's own file name
    begins with the target directory and ends with the product basename, which
    is how the search wrote it; the position is read from that product, so this
    is a path construction and not a name join -- if the file is absent the
    window simply has no position and is reported as such."""
    b = p['file'][:-len('_r8prof.npz')]
    if '__' in b:
        tdir, base = b.split('__', 1)
        return '/data/SETI/targets/%s/products/%s' % (tdir, base)
    return None


claimed = {}
win, unres = [], []
for x in W:
    key = pkey(x['stem'])
    spw = spwof(key)
    cat = CATK.get(wkey(x['eb'], x['lo'], x['hi']), [])
    adopted = REP.get((x['eb'], spw), x['Tstar'])
    lo, hi = min(x['lo'], x['hi']), max(x['lo'], x['hi'])
    cands = sorted(((abs(p['star_peak'] - adopted) / max(abs(adopted), 1e-12),
                     p['path'], p)
                    for p in BYEBSPW.get((x['eb'], spw), [])
                    if abs(p['lo'] - lo) <= 2e-3 and abs(p['hi'] - hi) <= 2e-3),
                   key=lambda t: (t[0], t[1]))
    pick = next((p for rel, _pa, p in cands
                 if rel <= GATE_TOL and p['path'] not in claimed), None)
    rec = dict(key=key, stem=x['stem'], eb=x['eb'], spw=spw, star=x['star'],
               cls=x['cls'], band=x['band'], lo=x['lo'], hi=x['hi'],
               cw=x['cw'], nch=x['nch'], Tstar=x['Tstar'], adopted=adopted,
               repaired=(x['eb'], spw) in REP,
               crossing=x['crossing'], fcross=x['fcross'],
               released=bool(cat), stratum='released',
               n_search_cells=(CAT[cat[0]]['n_search_cells'] if cat else None))
    smin = (float(CAT[cat[0]]['smin_mJy']) if cat else None)
    rms = (float(CAT[cat[0]]['rms_mJy']) if cat else None)
    ons = (float(CAT[cat[0]]['on_source_s']) if cat else None)
    if (x['eb'], spw) in REPS:
        smin, rms, ons = REPS[(x['eb'], spw)]
    rec.update(smin_mJy=smin, rms_mJy=rms, on_source_s=ons)
    vb, vbsrc = mf.vbary(x['eb'], x['lo'])
    vs, vssrc, _b = mf.vsys(x['star'])
    rec.update(v_bary=float(vb or 0.0), v_bary_src=vbsrc,
               v_sys=float(vs or 0.0), v_sys_known=vs is not None)
    if pick is None:
        rec['candidates'] = [dict(rel=rel, dir=p['dir'], file=p['file'],
                                  peak=p['star_peak'])
                             for rel, _pa, p in cands[:4]]
        rec['reason'] = ('its profile is claimed by another catalogue row for '
                         'the same window'
                         if any(rel <= GATE_TOL for rel, _pa, _p in cands)
                         else 'no retained profile reproduces its adopted '
                              'statistic')
        unres.append(rec)
        continue
    claimed[pick['path']] = key
    rec.update(profile=pick['path'], profile_dir=pick['dir'],
               profile_file=pick['file'], profile_peak=pick['star_peak'],
               n_candidates=len(cands))
    win.append(rec)

# ---------------------------------------------------- the archival-tail stratum
# Every retained profile no released window claims, read from the inventory.
# Where two sets hold the same block, window and statistic, one is kept.
seen = set()
for p in sorted(INV, key=lambda q: (q['eb'], q['spw'] or -1, q['dir'])):
    if p['path'] in claimed:
        continue
    sig = (p['eb'], p['spw'], round(p['lo'], 3), round(p['hi'], 3),
           round(p['star_peak'], 4))
    if sig in seen:
        continue
    if CATK.get(wkey(p['eb'], p['lo'], p['hi'])):
        continue                      # a released window, resolved or not
    seen.add(sig)
    star = re.sub(r'\s*\[[^]]*\]\s*', '', p['star_name']).strip()
    vb, vbsrc = mf.vbary(p['eb'], p['lo'])
    vs, vssrc, _b = mf.vsys(star)
    cls = 'A' if p['n_drift'] > 8 else 'B'
    win.append(dict(key=p['file'][:-len('_r8prof.npz')],
                    stem=stem_from_profile(p),
                    eb=p['eb'], spw=p['spw'], star=star, cls=cls,
                    band=None, lo=p['lo'], hi=p['hi'], cw=p['chanw'],
                    nch=p['nch'], Tstar=p['star_peak'],
                    adopted=p['star_peak'], repaired=False,
                    crossing=None, fcross=None, released=False,
                    stratum='archival_tail', n_search_cells=None,
                    smin_mJy=None, rms_mJy=None, on_source_s=None,
                    v_bary=float(vb or 0.0), v_bary_src=vbsrc,
                    v_sys=float(vs or 0.0), v_sys_known=vs is not None,
                    profile=p['path'], profile_dir=p['dir'],
                    profile_file=p['file'], profile_peak=p['star_peak'],
                    n_candidates=1))
    claimed[p['path']] = p['file']

# ------------------------- released windows searched on a profile that does
# NOT reproduce their adopted statistic.  One exists; it is searched and the
# discrepancy is printed beside it, because a window that holds a published
# crossing must not be left out of a completeness statement in silence.
covered = {(w['eb'], w['spw'], round(min(w['lo'], w['hi']), 3),
            round(max(w['lo'], w['hi']), 3)) for w in win}
best = {}
for p in INV:
    cat = CATK.get(wkey(p['eb'], p['lo'], p['hi']))
    if not cat:
        continue
    sig = (p['eb'], p['spw'], round(p['lo'], 3), round(p['hi'], 3))
    if sig in covered:
        continue
    r = CAT[cat[0]]
    rel = abs(p['star_peak'] - float(r['star_snr'])) \
        / max(abs(float(r['star_snr'])), 1e-12)
    if sig not in best or rel < best[sig][0]:
        best[sig] = (rel, p, r)
for sig, (rel, p, r) in sorted(best.items()):
    star = re.sub(r'\s*\[[^]]*\]\s*', '', p['star_name']).strip() \
        or r['star_name']
    vb, vbsrc = mf.vbary(p['eb'], p['lo'])
    vs, vssrc, _b = mf.vsys(r['star_name'])
    win.append(dict(key=p['file'][:-len('_r8prof.npz')],
                    stem=(WLSTEM.get(sig) or stem_from_profile(p)),
                    eb=p['eb'], spw=p['spw'], star=r['star_name'],
                    cls=r['search_class'], band=r['band'],
                    lo=p['lo'], hi=p['hi'], cw=p['chanw'], nch=p['nch'],
                    Tstar=float(r['star_snr']), adopted=float(r['star_snr']),
                    repaired=False, crossing=(r['crossing'] == 'True'),
                    fcross=(float(r['f_cross_GHz']) if r['f_cross_GHz']
                            else None),
                    released=True,
                    stratum=('released_prerepair' if rel <= GATE_TOL
                             else 'released_other'),
                    gate_rel=rel,
                    adopted_repaired=REP.get((p['eb'], p['spw'])), n_search_cells=r['n_search_cells'],
                    smin_mJy=float(r['smin_mJy']), rms_mJy=float(r['rms_mJy']),
                    on_source_s=float(r['on_source_s']),
                    v_bary=float(vb or 0.0), v_bary_src=vbsrc,
                    v_sys=float(vs or 0.0), v_sys_known=vs is not None,
                    profile=p['path'], profile_dir=p['dir'],
                    profile_file=p['file'], profile_peak=p['star_peak'],
                    n_candidates=1))
    claimed[p['path']] = p['file']

TRANS = {k: v[0] for k, v in mf.TRANS.items()}
TRANS_NULL = {k: v[0] for k, v in mf.TRANS.items()
              if mf.species(k) not in mf.NOTED_SPECIES}

json.dump(dict(trig=mf.TRIGGER, half=mf.MASK_HALF_KMS, c=mf.C_KMS,
               ladder=[3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0],
               gate_tol=GATE_TOL,
               n_cat=len(CAT),
               n_cat_A=sum(1 for r in CAT if r['search_class'] == 'A'),
               n_worklist=len(W), trans=TRANS, trans_null=TRANS_NULL,
               unresolved=unres, windows=win), open(OUT, 'w'), indent=1)

rel = [w for w in win if w['stratum'] == 'released']
tail = [w for w in win if w['stratum'] == 'archival_tail']
print('%d worklist windows -> %d resolved (%d released, %d archival tail), '
      '%d unresolved' % (len(W), len(win), len(rel), len(tail), len(unres)))
print('  released Class A resolved %d of the catalogue\'s %d'
      % (sum(1 for w in rel if w['cls'] == 'A'),
         sum(1 for r in CAT if r['search_class'] == 'A')))
print('  archival-tail windows: %s'
      % [(w['eb'], w['star'], round(w['Tstar'], 4)) for w in tail])
pr = [w for w in win if w['stratum'] == 'released_prerepair']
nr = [w for w in win if w['stratum'] == 'released_other']
print('  searched on the pre-repair profile (adopted statistic is the '
      'repaired one): %d, largest pre-repair maximum %.4f, largest adopted '
      '%.4f' % (len(pr), max(w['profile_peak'] for w in pr),
                max(w['adopted_repaired'] or 0 for w in pr)))
print('  searched on a profile reproducing NEITHER statistic: %d %s'
      % (len(nr), [(w['eb'], w['star'], w['cls'], round(w['adopted'], 4),
                    round(w['profile_peak'], 4)) for w in nr]))
print('  unresolved, all classes: %s'
      % dict(collections.Counter(w['cls'] for w in unres)))
print('  unresolved above the trigger: %d (the largest %.4f)'
      % (sum(1 for w in unres if w['adopted'] >= mf.TRIGGER),
         max(w['adopted'] for w in unres)))
print('  profiles claimed %d of %d inventoried' % (len(claimed), len(INV)))
print('%d transitions in the mask, %d in the null mask'
      % (len(TRANS), len(TRANS_NULL)))
