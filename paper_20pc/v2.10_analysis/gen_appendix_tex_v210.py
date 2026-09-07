import json

rows = json.load(open('/workspace/SETI/paper_20pc/paper_v210_rows.json'))
rows.sort(key=lambda r: r['dist'])

NOTES = {
    ("Barnard's Star","7"): "narrowband search failed; partial-crossmatch epochs excluded from continuum (\\S\\ref{sec:barnardswolfband7})",
    ("Barnard's Star","6"): "NEW this version; first-ever ALMA technosignature search of this star, recovered via a proper-motion crossmatch fix, see \\S\\ref{sec:barnardswolf}",
    ("Wolf  359","7"): "narrowband search failed; partial-crossmatch epochs excluded from continuum",
    ("Wolf  359","6"): "NEW this version; first-ever ALMA technosignature search of this star, recovered via a proper-motion crossmatch fix, see \\S\\ref{sec:barnardswolf}",
    ("Sirius B","4"): "primary-beam corrected (\\S\\ref{sec:method})",
    ("Sirius B","5"): "primary-beam corrected (\\S\\ref{sec:method})",
    ("Sirius B","3"): "primary-beam corrected (\\S\\ref{sec:method})",
    ("G 272-61B","3"): "unresolved UV Cet AB pair, blended flux",
    ("G 272-61A","3"): "unresolved UV Cet AB pair, blended flux",
    ("eps Eri","6"): "Teff-derived sptype",
    ("tau Cet","6"): "reprocessing queued (other spws)",
    ("BD+05  1668","6"): "Teff-derived sptype",
    ("HD 33793","6"): "Kapteyn's Star; reprocessing queued (other spws)",
    ("SCR J1845-6357","6"): "narrowband search failed; M8.5V+T6 binary (Teff unavailable); partial-crossmatch epochs excluded from continuum",
    ("Wolf   28","6"): "Van Maanen's Star (white dwarf); reprocessing queued (other spws)",
    ("LSR J1835+3259","3"): "known strongly-magnetically-active UCD (Hallinan et al. 2007); continuum detection, see \\S\\ref{sec:results}",
    ("Wolf  358","7"): "narrowband search failed; partial-crossmatch epochs excluded from continuum",
    ("HD 10647","6"): "corrupted spectral window excluded (see \\S\\ref{sec:results}); continuum withheld",
    ("g Lup","6"): "not the bright B-type naked-eye star of the same traditional name (Teff/dist inconsistent, see text); corrupted spectral window excluded; continuum withheld",
    ("AU Mic","3"): "narrowband complete; continuum step incomplete",
    ("AU Mic","6"): "automated candidate flag, not credible, see text",
    ("bet Pic","3"): "CO(1-0) line, automated candidate flag, see text",
    ("Wolf  219","6"): "NEW this version; recovered via legacy calibration-script replay, see \\S\\ref{sec:fiverecoveries}",
    ("chi01 Ori","3"): "NEW this version; recovered via legacy calibration-script replay, see \\S\\ref{sec:fiverecoveries}",
    ("eta Cru","6"): "NEW this version; recovered via legacy calibration-script replay, see \\S\\ref{sec:fiverecoveries}",
    ("CD-38 10980","6"): "NEW this version; recovered via stale-marker correction, see \\S\\ref{sec:fiverecoveries}",
    ("GL 3379","6"): "NEW this version; recovered via stale-marker correction, see \\S\\ref{sec:fiverecoveries}; Teff-derived sptype",
    ("eta Crv","7"): "second independent band for this target (Band 8 already reported)",
    ("HN Lib","6"): "known exoplanet host (HN Lib b, habitable zone)",
    ("LHS 1140","6"): "known exoplanet host (LHS 1140 b/c, b in habitable zone)",
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

open('/workspace/SETI/paper_20pc/appendix_rows_v210.tex','w').write('\n'.join(lines) + '\n')
print(f'{len(lines)} table rows written')
print('\n'.join(lines[:8]))
