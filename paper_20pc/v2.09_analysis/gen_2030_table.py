import json

entries = [
    dict(name="HD 45184", sptype="G2Va", dist=21.89, band=6,
         result="/workspace/SETI/ext2030_raw/ext2030/HD_45184_result.json",
         cont="/workspace/SETI/ext2030_raw/ext2030/HD_45184_continuum.json",
         note="solar analog, known exoplanet host"),
    dict(name="HD 107146", sptype="G2V", dist=27.47, band=6,
         result="/workspace/SETI/ext2030_raw/ext2030/HD_107146__Gaia_DR3_3946438125929224320__result.json",
         cont="/workspace/SETI/ext2030_raw/ext2030/HD_107146__Gaia_DR3_3946438125929224320__continuum.json",
         note="known resolved debris disk; automated candidate flag not credible, see text"),
    dict(name="HD 31392", sptype="unclassified", dist=25.76, band=6,
         result="/workspace/SETI/ext2030_raw/ext2030/HD_31392__Gaia_DR3_4824866896260056448__B6_result.json",
         cont="/workspace/SETI/ext2030_raw/ext2030/HD_31392__Gaia_DR3_4824866896260056448__B6_continuum.json",
         note=""),
    dict(name="L 836-122", sptype="M dwarf$^\\ddagger$", dist=28.70, band=7,
         result="/workspace/SETI/ext2030_raw/ext2030/L_836-122__Gaia_DR3_6298167942962279680__B7_result.json",
         cont="/workspace/SETI/ext2030_raw/ext2030/L_836-122__Gaia_DR3_6298167942962279680__B7_continuum.json",
         note="bright continuum detection, single epoch, no variability check possible"),
    dict(name="HD 92945", sptype="K1V", dist=21.51, band=7,
         result="/workspace/SETI/ext2030_raw/ext2030/hd92945__Gaia_DR3_5455707157211784832__B7_result.json",
         cont="/workspace/SETI/ext2030_raw/ext2030/hd92945__Gaia_DR3_5455707157211784832__B7_continuum.json",
         note="known resolved debris disk; continuum flagged variable (3 epochs, $\\chi^2_\\nu$=5.4)"),
    dict(name="CD-57 1054", sptype="unclassified", dist=26.87, band=7,
         result=None,
         cont="/workspace/SETI/ext2030_raw/ext2030/CD-57_1054__Gaia_DR3_4764027962957023104__B7_continuum.json",
         note="narrowband search failed; continuum only"),
    dict(name="LP 476-207", sptype="unclassified", dist=23.79, band=7,
         result=None,
         cont="/workspace/SETI/ext2030_raw/ext2030/LP_476-207__Gaia_DR3_3291643148740384128__B7_continuum.json",
         note="narrowband search failed; continuum only"),
]

lines = []
for e in entries:
    r = json.load(open(e['result'])) if e['result'] else None
    c = json.load(open(e['cont'])) if e['cont'] else None
    if r:
        lo, hi = sorted([r['freq_lo_GHz'], r['freq_hi_GHz']])
        freqrange = f"{lo:.2f}--{hi:.2f}"
        eirp = f"{r['EIRP_min_W']:.2e}"
    else:
        freqrange = "\\ldots"
        eirp = "\\ldots"
    if c:
        rms = c['image_rms_mJy']
        if c.get('continuum_source_detected'):
            flux = f"{c['image_peak_mJy']:.3f}"
        else:
            flux = f"$<${rms*5:.3f}"
        rmss = f"{rms:.4f}"
    else:
        flux = '---'; rmss = '---'
    row = f"{e['name']} & {e['band']} & {e['sptype']} & {e['dist']:.2f} & {freqrange} & {eirp} & {flux} & {rmss} & {e['note']} \\\\"
    lines.append(row)

open('/workspace/SETI/paper_20pc/table_2030pc.tex','w').write('\n'.join(lines)+'\n')
print('\n'.join(lines))
