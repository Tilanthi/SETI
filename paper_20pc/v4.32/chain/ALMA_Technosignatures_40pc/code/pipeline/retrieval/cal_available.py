#!/usr/bin/env python3
"""Is pipeline calibration available for a given execution block?

Why this exists
---------------
On 2026-09-17 twenty blocks of the sweep were failing in ~30 s each, always
with the same message, always AFTER a successful multi-gigabyte download of
the auxiliary tar:

    [calibrate_generic] --- EB A002_X106b646_X842 ---
    [calibrate_generic] FATAL: no execution blocks were successfully
                        calibrated for this target

Inventorying that delivery explained it. MOUS uid://A001/X2d1f/X30f offers
25 raw ASDM tars and delivers 24 ``uid___<EB>.ms.calapply.txt`` files, and
the single EB with no calapply.txt is exactly the one that kept failing. Its
sibling A002_X106b646_X1295, in the same delivery, calibrated and searched
without trouble. So ALMA distributes the raw ASDM of an execution block it
observed but never pipeline-calibrated, and nothing in the download path
notices until CASA has nothing to apply.

(A false lead worth recording: obscore's ``asdm_uid`` is NOT a per-EB index.
247 blocks that are absent from an ``asdm_uid IN (...)`` query have already
been calibrated and searched here, so "absent from obscore" proves nothing.
The calapply inventory is the real discriminator.)

``Alma.get_data_info(mous, expand_tarfiles=True)`` lists the contents of the
auxiliary tar without downloading it, so this is knowable for free, per EB,
before a single byte moves.

What is decisive and what is not
--------------------------------
Screened against 361 blocks already calibrated and searched, as a control:

    verdict                          resolved  failed  pending
    calapply                              325       0       33
    delivery_has_no_calibration            36       8       36
    eb_not_calibrated_in_delivery            0      10        4
    no_auxiliary_tar                         0       0        6
    legacy_script                            0       0        2

Only two classes are decisive, in the sense of containing no block that
later succeeded: ``eb_not_calibrated_in_delivery`` (the delivery carries
calibration for other EBs but not for this one) and ``no_auxiliary_tar``.
``delivery_has_no_calibration`` is deliberately NOT treated as decisive --
36 blocks of that class calibrated successfully, presumably by way of
calibration nested inside a ``*.calibration.tgz`` that the listing does not
expand. Those must still be attempted. A screen is only worth having if it
is calibrated against its own false-positive rate.
"""
import json, os, re, time

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'calscreen.json')

# Classes with zero successes among 361 controls; safe to refuse up front.
DECISIVE = ('eb_not_calibrated_in_delivery', 'no_auxiliary_tar')


def _load():
    try:
        with open(CACHE) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _store(d):
    tmp = CACHE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, CACHE)


def screen_mous(mous, retries=3):
    """Return {eb: verdict} for every EB the given MOUS offers.

    Raises on persistent query failure so the caller can decide; a metadata
    outage must not be silently converted into an exclusion.
    """
    from astroquery.alma import Alma
    last = None
    for attempt in range(1, retries + 1):
        try:
            info = Alma.get_data_info(mous, expand_tarfiles=True)
            urls = ' '.join(str(u) for u in info['access_url'])
            break
        except Exception as e:                      # pragma: no cover
            last = e
            if attempt == retries:
                raise
            time.sleep(4 * attempt)
    cal = set(re.findall(r'uid___(A00\d_\w+)\.ms\.calapply\.txt', urls))
    leg = set(re.findall(r'uid___(A00\d_\w+)\.ms\.scriptForCalibration\.py', urls))
    asdm = set(re.findall(r'uid___(A00\d_\w+)\.asdm\.sdm\.tar', urls))
    has_aux = '_auxiliary.tar' in urls
    out = {}
    for eb in asdm | cal | leg:
        if eb in cal:
            out[eb] = 'calapply'
        elif eb in leg:
            out[eb] = 'legacy_script'
        elif not has_aux:
            out[eb] = 'no_auxiliary_tar'
        elif not (cal or leg):
            out[eb] = 'delivery_has_no_calibration'
        else:
            out[eb] = 'eb_not_calibrated_in_delivery'
    return out


def verdict_for(eb, mous):
    """Cached per-EB verdict, or None if the archive could not be asked.

    A None return means "unknown, go ahead and try" -- never "exclude".
    """
    d = _load()
    v = d.get('verdict', {})
    if eb in v:
        return v[eb]
    try:
        fresh = screen_mous(mous)
    except Exception:
        return None
    v.update(fresh)
    d['verdict'] = v
    d.setdefault('screened_mous', [])
    if mous not in d['screened_mous']:
        d['screened_mous'].append(mous)
    _store(d)
    return v.get(eb)


def is_uncalibratable(eb, mous):
    """(bool, reason). True only for a class with no observed success."""
    v = verdict_for(eb, mous)
    if v in DECISIVE:
        return True, v
    return False, v


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3:
        print(is_uncalibratable(sys.argv[1], sys.argv[2]))
    else:
        d = _load()
        import collections
        print(collections.Counter(d.get('verdict', {}).values()))
