import urllib.request, json
q = ("select+hostname,ra,dec,sy_dist,sy_disterr1,st_spectype,st_teff,st_rad,st_mass,"
     "sy_vmag,sy_kmag,sy_gaiamag,sy_pnum,pl_name,pl_rade,pl_bmasse,pl_orbsmax,"
     "pl_eqt,disc_year+from+pscomppars")
url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={q}&format=json"
print("fetching...")
with urllib.request.urlopen(url, timeout=180) as r:
    data = json.load(r)
print(len(data), "planet rows")
json.dump(data, open('exo_hosts_raw.json','w'))
