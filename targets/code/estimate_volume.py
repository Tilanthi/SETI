from astroquery.alma import Alma
import json, warnings, time
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')
Alma.archive_url = 'https://almascience.eso.org'

top100 = json.load(open('ranked_top100.json'))
mous_ids = sorted(set(s['alma_best_mous'] for s in top100))
print(f"{len(mous_ids)} unique best-MOUS to size (of {len(top100)} targets)")

def get_size(mous):
    try:
        info = Alma.get_data_info(mous, expand_tarfiles=False)
        tot = 0
        for row in info:
            u = str(row['access_url'])
            if u.endswith('.asdm.sdm.tar'):
                try: tot += float(row['content_length'])
                except: pass
        return mous, tot
    except Exception as e:
        return mous, None

sizes = {}
t0 = time.time()
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(get_size, m): m for m in mous_ids}
    done = 0
    for f in as_completed(futs):
        mous, sz = f.result()
        sizes[mous] = sz
        done += 1
        if done % 20 == 0:
            print(f"  {done}/{len(mous_ids)} ({time.time()-t0:.0f}s)", flush=True)

ok = {k: v for k, v in sizes.items() if v is not None and v > 0}
print(f"\n{len(ok)}/{len(mous_ids)} sized successfully in {time.time()-t0:.0f}s")
import numpy as np
vals = np.array(list(ok.values())) / 1e9
print(f"total raw size for {len(ok)} MOUS: {vals.sum():.1f} GB")
print(f"median {np.median(vals):.2f} GB, mean {vals.mean():.2f} GB, "
      f"min {vals.min():.3f} GB, max {vals.max():.1f} GB")
json.dump({k: v for k, v in sizes.items()}, open('mous_sizes.json', 'w'))
