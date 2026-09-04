import json, statistics

d = json.load(open('/workspace/SETI/paper_20pc/paper_v209_raw.json'))
valid = [e for e in d if e.get('has_data')]

# Known/curated spectral types (literature + carried over from v2.08)
SPTYPE = {
    "Proxima Cen": "M6V",
    "NAME Barnard's star": "M5V",
    "Wolf  359": "M6V",
    "* alf CMa B": "DA2",           # = Sirius B
    "G 272-61B": "M6Ve",
    "G 272-61A": "M5.5Ve",
    "CD-23 14742": "M5V",
    "tau Cet": "K0V",
    "HD  33793": "sdM1",
    "Wolf   28": "DZ7",
    "GJ 674": "M3V",
    "GJ 581": "M4V",
    "GJ 849": "M4V",
    "* gam Lep": "F7V",
    "HD 285968": "M1V",
    "AU Mic": "M1Ve",
    "V* AT Mic B": "M4V",
    "NAME AT Mic AB (Gaia DR3 6792436799475128960)": "M5V",
    "* gam Vir": "F0V",
    "HR 1010 (Gaia DR3 4722135642226902656)": "G2V",
    "TRAPPIST-1": "M8V",
    "HD 38858 (Gaia DR3 3023711269067191296)": "G5V",
    "HD 207129 (Gaia DR3 6564091190988411520)": "G2V",
    "HD 23484 (Gaia DR3 4856592239127350400)": "K5V",
    "HD 10647": "G0V",
    "* eta Crv": "F2V",
    "HD53143 (Gaia DR3 5479222240596469632)": "K0V",
    "bet Pic": "F0V",
    "61 Vir": "G5V",
    # New this version -- Teff-derived (Pecaut & Mamajek 2013 dwarf scale) unless noted
    "BD+05  1668": "M5V$^\\dagger$",
    "G   9-38A": "M dwarf$^\\ddagger$",
    "G   9-38B": "M dwarf$^\\ddagger$",
    "GJ14 (Gaia DR3 383426372059603712)": "M0V$^\\dagger$",
    "HD 69830": "K0V$^\\dagger$",
    "LP  349-25": "M dwarf$^\\ddagger$",
    "LSR J1835+3259": "M8.5V$^\\ddagger$",
    "SCR J1845-6357": "M8.5V+T6$^\\ddagger$",
    "Wolf  358": "M6V$^\\dagger$",
    "eps Eri": "K2V$^\\dagger$",
    "lp 876-10 (Gaia DR3 6623351805412369024)": "M6V$^\\dagger$",
    "* g Lup": "F5V$^\\dagger$",
}
DISPLAY = {
    "* alf CMa B": "Sirius B",
    "NAME Barnard's star": "Barnard's Star",
    "* gam Lep": "gam Lep",
    "V* AT Mic B": "AT Mic B",
    "NAME AT Mic AB (Gaia DR3 6792436799475128920)": "AT Mic AB",
    "NAME AT Mic AB (Gaia DR3 6792436799475128960)": "AT Mic AB",
    "* gam Vir": "gam Vir",
    "HR 1010 (Gaia DR3 4722135642226902656)": "HR 1010",
    "HD 38858 (Gaia DR3 3023711269067191296)": "HD 38858",
    "HD 207129 (Gaia DR3 6564091190988411520)": "HD 207129",
    "HD 23484 (Gaia DR3 4856592239127350400)": "HD 23484",
    "* eta Crv": "eta Crv",
    "HD53143 (Gaia DR3 5479222240596469632)": "HD 53143",
    "HD  33793": "HD 33793",
    "GJ14 (Gaia DR3 383426372059603712)": "GJ14",
    "lp 876-10 (Gaia DR3 6623351805412369024)": "lp 876-10",
    "* g Lup": "g Lup",
}

def disp(name):
    return DISPLAY.get(name, name)

# Fully-excluded targets: genuine crossmatch failure (single MOUS, field ~52
# arcmin off target) where the continuum step's missing offset guard let a
# bogus 8-Jy "detection" through -- see text. Neither narrowband (already
# empty) nor continuum is usable.
EXCLUDE_TARGETS = {("G   9-38A", "3"), ("G   9-38B", "3")}
# Targets where the recurring corrupted-window bug (on_source_s=12.096s,
# rms ~1000x too deep, see text) contaminates the COMBINED continuum
# measurement for that band (continuum uses all configured spws together).
# Keep the other, clean narrowband windows; drop the continuum number.
CONTAMINATED_CONTINUUM = {("HD 10647", "6"), ("* g Lup", "6")}

rows = []
for e in valid:
    name = e['name']
    band = e['band']
    if (name, band) in EXCLUDE_TARGETS:
        continue
    dist = e['dist_pc']
    sptype = SPTYPE.get(name, 'unclassified')
    techno = e.get('techno', [])
    # exclude known anomalous short-integration windows (see text)
    clean_techno = [t for t in techno if not (t.get('on_source_s') and abs(t['on_source_s']-12.096) < 0.01)]
    n_anomalous = len(techno) - len(clean_techno)
    clean_techno.sort(key=lambda t: t.get('EIRP_min_W', 1e99))
    cont = e.get('continuum')
    if (name, band) in CONTAMINATED_CONTINUUM:
        cont = None
    n_spw_conf = e.get('n_spw_configured')
    n_spw_search = e.get('n_spw_searched')
    rows.append(dict(name=name, disp=disp(name), band=band, dist=dist, sptype=sptype,
                      techno=clean_techno, n_anomalous=n_anomalous, cont=cont,
                      n_spw_conf=n_spw_conf, n_spw_search=n_spw_search,
                      fatal_partial=e.get('fatal_crossmatch', False)))

rows.sort(key=lambda r: r['dist'])

json.dump(rows, open('/workspace/SETI/paper_20pc/paper_v209_rows.json','w'), indent=1, default=str)
print(f'{len(rows)} target/band rows')
n_anom = sum(r['n_anomalous'] for r in rows)
print(f'anomalous short-integration windows excluded: {n_anom}')
for r in rows:
    if r['n_anomalous']:
        print(' ->', r['name'], r['band'])
