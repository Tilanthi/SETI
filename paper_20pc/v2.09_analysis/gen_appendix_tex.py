import json

rows = json.load(open('/workspace/SETI/paper_20pc/paper_v209_rows.json'))
rows.sort(key=lambda r: r['dist'])

NOTES = {
    ("Proxima Cen","6"): "reprocessing queued (other spws)",
    ("Barnard's Star","7"): "narrowband search failed; partial-crossmatch epochs excluded from continuum (\\S\\ref{sec:results})",
    ("Wolf  359","7"): "narrowband search failed; partial-crossmatch epochs excluded from continuum",
    ("Sirius B","4"): "primary-beam corrected (\\S\\ref{sec:method}); reprocessing queued (other spws)",
    ("Sirius B","5"): "primary-beam corrected (\\S\\ref{sec:method}); reprocessing queued (other spws)",
    ("Sirius B","3"): "primary-beam corrected (\\S\\ref{sec:method}); reprocessing queued (other spws)",
    ("G 272-61B","3"): "unresolved UV Cet AB pair, blended flux; reprocessing queued (other spws)",
    ("G 272-61A","3"): "unresolved UV Cet AB pair, blended flux; reprocessing queued (other spws)",
    ("CD-23 14742","6"): "reprocessing queued (other spws)",
    ("eps Eri","6"): "Teff-derived sptype",
    ("tau Cet","6"): "reprocessing queued (other spws)",
    ("BD+05  1668","6"): "Teff-derived sptype",
    ("HD 33793","6"): "Kapteyn's Star; reprocessing queued (other spws)",
    ("SCR J1845-6357","6"): "narrowband search failed; M8.5V+T6 binary (Teff unavailable); partial-crossmatch epochs excluded from continuum",
    ("Wolf   28","6"): "Van Maanen's Star (white dwarf); reprocessing queued (other spws)",
    ("GJ 674","6"): "reprocessing queued (other spws)",
    ("LSR J1835+3259","3"): "known strongly-magnetically-active UCD (Hallinan et al. 2007); continuum detection, see \\S\\ref{sec:results}",
    ("Wolf  358","7"): "narrowband search failed; partial-crossmatch epochs excluded from continuum",
    ("HD 10647","6"): "corrupted spectral window excluded (see \\S\\ref{sec:results}); continuum withheld",
    ("g Lup","6"): "not the bright B-type naked-eye star of the same traditional name (Teff/dist inconsistent, see text); corrupted spectral window excluded; continuum withheld",
    ("AU Mic","3"): "narrowband complete; continuum step incomplete",
    ("AU Mic","6"): "automated candidate flag, not credible, see text",
    ("bet Pic","3"): "CO(1-0) line, automated candidate flag, see text",
    ("bet Pic","6"): "reprocessing queued (other spws)",
    ("HD 10647","7"): "reprocessing queued (other spws)",
}

def fmt_eirp(v):
    if v is None: return '---'
    return f'{v:.2e}'

lines = []
for r in rows:
    disp = r['disp']
    band = r['band']
    sptype = r['sptype']
    dist = r['dist']
    techno = r['techno']
    cont = r['cont']
    nspw_conf = r.get('n_spw_conf')
    nspw_search = len(techno)
    nspw = nspw_conf if (nspw_conf and nspw_conf >= nspw_search) else max(nspw_search, 1)
    note_extra = ""
    if r['n_anomalous']:
        note_extra = " (1 corrupted window excluded)"
    key = (disp, band)
    base_note = NOTES.get(key, "")
    if not techno:
        freqrange = '\\ldots'
        eirp = '\\ldots'
    else:
        t0 = techno[0]
        lo, hi = sorted([t0['freq_lo_GHz'], t0['freq_hi_GHz']])
        freqrange = f'{lo:.2f}--{hi:.2f}'
        eirp = fmt_eirp(t0.get('EIRP_min_W'))
    if cont:
        if cont.get('continuum_source_detected'):
            flux = f"{cont['image_peak_mJy']:.3f}"
        else:
            flux = f"$<${cont['image_rms_mJy']*5:.3f}"
        rms = f"{cont['image_rms_mJy']:.4f}"
    else:
        flux = '---'
        rms = '---'
    note = base_note if not techno else base_note + note_extra if base_note else note_extra.strip()
    row = f"{disp} & {band} & {sptype} & {dist:.2f} & {freqrange} & {nspw} & {eirp} & {flux} & {rms} & {note} \\\\"
    lines.append(row)
    # additional windows (rows 2..N), continuum blank
    if len(techno) > 1:
        for t in techno[1:]:
            lo, hi = sorted([t['freq_lo_GHz'], t['freq_hi_GHz']])
            freqrange2 = f'{lo:.2f}--{hi:.2f}'
            eirp2 = fmt_eirp(t.get('EIRP_min_W'))
            row2 = f"{disp} & {band} & {sptype} & {dist:.2f} & {freqrange2} & {nspw} & {eirp2} & --- & --- &  \\\\"
            lines.append(row2)

open('/workspace/SETI/paper_20pc/appendix_rows_v209.tex','w').write('\n'.join(lines) + '\n')
print(f'{len(lines)} table rows written')
print('\n'.join(lines[:8]))
