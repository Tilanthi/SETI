#!/usr/bin/env python3
r"""sumrule_r34.py -- the summation rule of a nested count table (r34, Referee 2 item 9).

A table whose rows nest (1, 1.1, 1.1.2, ...) invites the reader to add the rows
under a parent.  For each parent this module says what the parent IS the sum of:
  * the rows its own note names ("rows 1.1 and 1.2", "rows 5.1 to 5.5",
    "rows 2.2, 1.1.2 and 1.2 together"), or a second partition another row's
    note declares ("rows 3.3 and 3.4 split row 3 a second way");
  * otherwise all of its direct sub-rows, if they add up;
  * otherwise nothing: it is marked "not a sum", and its sub-rows are subsets.
Every NAMED sum is checked (a note that names rows that do not add up is a
failure, returned to the caller to assert), and so is every implicit one.

Pure functions, no side effects: imported by ledger_r34.py (which asserts and
drives the rule) and by zdeposit.py (which writes the annotation columns of
catalogues/count_accounting.csv).
"""
import re

_NUM = re.compile(r'^\s*(-?\d+(?:\.\d+)?)\s*$')
_RID = r'\d+(?:\.\d+)*'


def value(v):
    """an integer count, or None (a percentage, a bandwidth, a word)"""
    m = _NUM.match(str(v).replace(',', ''))
    if not m or '.' in m.group(1):
        return None
    return int(m.group(1))


def _expand(a, b, ids):
    """rows a to b, as the table orders them, at the depth of a"""
    out, on = [], False
    for r in ids:
        if r == a:
            on = True
        if on and r.count('.') == a.count('.'):
            out.append(r)
        if r == b:
            break
    return out


def named(note, ids):
    """the rows a note says its row is the sum of, or None"""
    m = re.search(r'\brows (%s) to (%s)\b' % (_RID, _RID), note)
    if m:
        return _expand(m.group(1), m.group(2), ids)
    m = re.search(r'\brows ((?:%s, )*%s) and (%s)\b' % (_RID, _RID, _RID), note)
    if m and not re.search(r'\bsplit row\b', note):
        return [x.strip() for x in m.group(1).split(',')] + [m.group(2)]
    return None


def second_splits(rows):
    """{parent: [rows]} for notes of the form 'rows X and Y split row P ...'"""
    out = {}
    for r in rows:
        m = re.search(r'\brows (%s) and (%s) split row (%s)\b' % (_RID, _RID, _RID),
                      r['what_it_counts'])
        if m:
            out.setdefault(m.group(3), []).append([m.group(1), m.group(2)])
    return out


def annotate(rows):
    """(annotations {row: (sub_rows, sum_rule)}, failures [str])"""
    import itertools
    ids = [r['row'] for r in rows]
    by = {r['row']: r for r in rows}
    splits = second_splits(rows)
    par = lambda k: k.rsplit('.', 1)[0] if '.' in k else None  # noqa: E731
    ann, fail = {}, []
    for r in rows:
        rid = r['row']
        kids = [k for k in ids if par(k) == rid]
        pv = value(r['value'])
        nm = named(r['what_it_counts'], ids)
        sums, inter = [], None
        if nm and all(k in by and par(k) == par(rid) and k != rid for k in nm):
            # a row named by its own SIBLINGS is their intersection ("with
            # both"), never their sum: it can be no larger than either
            inter = nm
            vals = [value(by[k]['value']) for k in nm]
            if pv is None or any(v is None or v < pv for v in vals):
                fail.append('row %s = %s is said to be the common part of rows %s'
                            % (rid, r['value'], ', '.join(nm)))
        elif nm:
            sums.append(nm)
        sums += splits.get(rid, [])
        if not sums and kids and pv is not None:
            kv = {k: value(by[k]['value']) for k in kids}
            cand = [k for k in kids if kv[k] is not None]
            # the consecutive leading rows first, then any combination
            combos = [cand[:n] for n in range(len(cand), 1, -1)]
            combos += [list(c) for n in range(2, min(len(cand), 6) + 1)
                       for c in itertools.combinations(cand, n)]
            for c in combos:
                if sum(kv[k] for k in c) == pv:
                    sums.append(c)
                    break
        for sm in sums:
            miss = [k for k in sm if k not in by]
            vals = [value(by[k]['value']) for k in sm if k in by]
            if miss or pv is None or any(v is None for v in vals) or sum(vals) != pv:
                fail.append('row %s = %s is said to be the sum of rows %s (%s)'
                            % (rid, r['value'], ', '.join(sm),
                               'missing %s' % miss if miss else
                               ' + '.join(str(v) for v in vals)))
        parts = []
        if inter:
            parts.append('the part common to rows ' + ', '.join(inter))
        parts += ['sum of rows ' + ', '.join(sm) for sm in sums]
        rest = [k for k in kids if not any(k in sm for sm in sums)]
        if sums and rest:
            parts.append('rows %s are not part of the sum' % ', '.join(rest))
        elif rest:
            parts.append('not a sum of rows %s' % ', '.join(rest))
        ann[rid] = (' '.join(kids), '; '.join(parts))
    return ann, fail
