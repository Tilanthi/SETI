"""Three numbers on A002_Xc26103_X155a (HD 48370), spw16, to settle
EPOCH_RESIDUAL_CONFLICT.md:
  (a) min(TIME) over ALL rows of the window
  (b) min(TIME) over the SELECTED science-field rows (the refit's rule)
  (c) the search's own times[0] from *_srcspec.npz
"""
import numpy as np, json, os
from casatools import table, msmetadata

MS = '/data/SETI/vistest/A002_Xc26103_X155a/products/A002_Xc26103_X155a_target.ms'
NPZ = '/data/SETI/targets/HD_48370_B6_EB_X155a/products/A002_Xc26103_X155a_spw16_srcspec.npz'
SPW = 16
out = {}

z = np.load(NPZ, allow_pickle=True)
t_search = float(z['times'][0])
span_search = float(z['times'][-1] - z['times'][0])
n_search = int(len(z['times']))
dnu = float(abs(z['freqs'][1] - z['freqs'][0]))
star_ra, star_dec = float(z['t1_ra']), float(z['t1_dec'])

msmd = msmetadata(); msmd.open(MS)
ddids = [int(d) for d in msmd.datadescids() if int(msmd.spwfordatadesc(d)) == SPW]
fids_spw = sorted(set(int(f) for f in msmd.fieldsforspw(SPW, asnames=False)))
fnames = {f: msmd.namesforfields(f)[0] for f in fids_spw}
pc = {f: msmd.phasecenter(f) for f in fids_spw}
try:
    sci = sorted(set(int(f) for f in msmd.fieldsforintent('OBSERVE_TARGET#ON_SOURCE', False)))
except Exception:
    sci = fids_spw
msmd.close()

tb = table(); tb.open(MS)
sub = tb.query('DATA_DESC_ID in %s' % json.dumps(ddids))
tim = np.asarray(sub.getcol('TIME')); fid = np.asarray(sub.getcol('FIELD_ID'))
sub.close(); tb.close()

# nearest-to-star science field (the refit's selection rule)
def sep(f):
    p = pc[f]
    ra, dec = float(p['m0']['value']), float(p['m1']['value'])
    return np.degrees(np.hypot((ra - np.radians(star_ra)) * np.cos(np.radians(star_dec)),
                               dec - np.radians(star_dec))) * 3600.0
sci_in_spw = [f for f in fids_spw if f in sci] or fids_spw
best = min(sci_in_spw, key=sep)
m_all = np.ones(len(tim), bool)
m_sci = np.isin(fid, sci_in_spw)
m_sel = fid == best

for tag, m in (('all_rows', m_all), ('science_rows', m_sci), ('selected_field', m_sel)):
    if m.sum() == 0:
        out[tag] = None; continue
    t = tim[m]
    out[tag] = dict(n_rows=int(m.sum()), n_int=int(len(np.unique(np.round(t, 3)))),
                    t0=float(t.min()), span=float(t.max() - t.min()),
                    dt_vs_search=float(t.min() - t_search))
out['search'] = dict(t0=t_search, span=span_search, n_int=n_search)
out['fields'] = {str(f): dict(name=fnames[f], sep_arcsec=round(sep(f), 3),
                              science=bool(f in sci), n_rows=int((fid == f).sum()))
                 for f in fids_spw}
out['selected_field_id'] = int(best)
out['chan_width_Hz'] = dnu
print(json.dumps(out, indent=1))
