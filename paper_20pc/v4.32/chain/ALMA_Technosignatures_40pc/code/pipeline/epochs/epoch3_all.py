"""Reference-epoch residual across every block with BOTH a target MS and a
surviving *_srcspec.npz.  For each window prints t0 over all rows, over the
science rows, over the nearest-to-star science field, and the search's own
times[0].  Settles whether the residual is zero unconditionally or only after
field selection.  Read-only."""
import numpy as np, json, glob, os, sys
from casatools import table, msmetadata

res = []
mslist = sorted(set(glob.glob('/data/SETI/targets/*/products/*_target.ms') +
                    glob.glob('/data/SETI/vistest/*/products/*_target.ms')))
for MS in mslist:
    eb = os.path.basename(MS).replace('_target.ms', '')
    prod = os.path.dirname(MS)
    npzs = sorted(glob.glob(os.path.join(prod, eb + '_spw*_srcspec.npz')))
    if not npzs:
        # srcspec may live in the survey target dir rather than beside the MS
        npzs = sorted(glob.glob('/data/SETI/targets/*/products/%s_spw*_srcspec.npz' % eb))
    if not npzs:
        res.append(dict(eb=eb, ms=MS, error='no srcspec')); continue
    try:
        msmd = msmetadata(); msmd.open(MS)
        try:
            sci = sorted(set(int(f) for f in
                             msmd.fieldsforintent('OBSERVE_TARGET#ON_SOURCE', False)))
        except Exception:
            sci = None
        spwmap = {}
        for d in msmd.datadescids():
            spwmap.setdefault(int(msmd.spwfordatadesc(int(d))), []).append(int(d))
        fieldpc, fieldname = {}, {}
        for f in msmd.fieldnames() and range(len(msmd.fieldnames())):
            fieldpc[f] = msmd.phasecenter(f); fieldname[f] = msmd.namesforfields(f)[0]
        msmd.close()
    except Exception as exc:
        res.append(dict(eb=eb, ms=MS, error='msmd: %r' % exc)); continue

    tb = table(); tb.open(MS)
    for npz in npzs:
        spw = int(npz.split('_spw')[-1].split('_')[0])
        if spw not in spwmap:
            continue
        try:
            z = np.load(npz, allow_pickle=True)
            t_search = float(z['times'][0]); n_search = int(len(z['times']))
            span_search = float(z['times'][-1] - z['times'][0])
            sra, sdec = float(z['t1_ra']), float(z['t1_dec'])
            dnu = float(abs(z['freqs'][1] - z['freqs'][0]))
        except Exception as exc:
            res.append(dict(eb=eb, spw=spw, error='npz: %r' % exc)); continue
        sub = tb.query('DATA_DESC_ID in %s' % json.dumps(spwmap[spw]))
        tim = np.asarray(sub.getcol('TIME')); fid = np.asarray(sub.getcol('FIELD_ID'))
        sub.close()
        fids = sorted(set(int(f) for f in np.unique(fid)))
        scif = [f for f in fids if (sci is None or f in sci)] or fids
        def sep(f):
            # true angular separation: a flat-sky difference in RA is wrong
            # across the 0/360 wrap and gave a 594,904" offset for a field
            # that is in fact on the star.
            p = fieldpc[f]
            ra, dec = float(p['m0']['value']), float(p['m1']['value'])
            sr, sd = np.radians(sra), np.radians(sdec)
            cosang = (np.sin(dec) * np.sin(sd) +
                      np.cos(dec) * np.cos(sd) * np.cos(ra - sr))
            return float(np.degrees(np.arccos(np.clip(cosang, -1, 1))) * 3600.0)
        best = min(scif, key=sep)
        def blk(m):
            t = tim[m]
            return dict(n_int=int(len(np.unique(np.round(t, 3)))), t0=float(t.min()),
                        span=float(t.max() - t.min()), dt=float(t.min() - t_search))
        res.append(dict(eb=eb, spw=spw, dnu_Hz=dnu, n_fields=len(fids),
                        n_sci_fields=len(scif), sel_field=best,
                        sel_sep_arcsec=round(sep(best), 3),
                        sel_name=fieldname.get(best, '?'),
                        all_rows=blk(np.ones(len(tim), bool)),
                        science=blk(np.isin(fid, scif)),
                        selected=blk(fid == best),
                        search=dict(t0=t_search, span=span_search, n_int=n_search)))
    tb.close()

json.dump(res, open('/data/SETI/visfit_r7/epoch_residual_all.json', 'w'), indent=1)
print('windows:', len(res))
bad = [r for r in res if 'error' in r]
print('errors:', len(bad), set(r.get('error', '')[:30] for r in bad))
hdr = '%-22s %4s %7s %9s %9s %9s %6s' % ('eb', 'spw', 'nfld', 'dt_all', 'dt_sci', 'dt_sel', 'nint_ok')
print(hdr)
for r in res:
    if 'error' in r: continue
    print('%-22s %4d %3d/%-3d %9.1f %9.1f %9.1f %s' % (
        r['eb'], r['spw'], r['n_sci_fields'], r['n_fields'],
        r['all_rows']['dt'], r['science']['dt'], r['selected']['dt'],
        'Y' if r['selected']['n_int'] == r['search']['n_int'] else
        '%d/%d' % (r['selected']['n_int'], r['search']['n_int'])))
