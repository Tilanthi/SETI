# FREEZE RECORD — Euclid DR1 LRD selection, spec v1.0 (pre-registration)

| item | value |
|---|---|
| spec (frozen text) | [`/workspace/LRD/release/SELECTION_SPEC_v1.0.md`](/workspace/LRD/release/SELECTION_SPEC_v1.0.md) up to the line `END OF FROZEN TEXT` (= `/srv/LRD/release/SELECTION_SPEC_v1.0.md`, = `/workspace/LRD/freeze/SELECTION_SPEC_v1.0.frozen.md`) |
| spec sha256 | `cc0208c95c4c50f61053084840f245d1acb6543f308b56da0eb240e598969905` |
| code hash (lrdlib + wp4 + dr1, /srv/LRD) | `ce7ff7d4ef695300199caf768f9d1d3e8ec2b25e4dc8f6734483ddcb163644bf` |
| runner hash (selrun.py, chain.py, fits_fallback.py, hooks/selection_dr1.sh + resolved config) | `9364e7d234fdcbdc9447ab6c09863cff6e985ce894c72f64455c54edf11e1baa` |
| analysis hashes (recorded only) | code/grism `cf9e9ec74d3cd7f3394e9073f3e8f3616b83a1ce65c96ae1c0595576a8d07e8a`; smh/code `1cf9aead2798ef6fe0e8159a7b5f9773e924dd6c8a8302acf01279bb08504be7` |
| SPEC_HASHES | `/srv/LRD/release/SPEC_HASHES.txt` (written 2026-11-11T11:37:36Z) = [`/workspace/LRD/release/SPEC_HASHES_v1.0.txt`](/workspace/LRD/release/SPEC_HASHES_v1.0.txt) |
| config | `/srv/LRD/code/release/selection_config_dr1.json`, spec.version "1.0", config sha256 (resolved) 8d3848db28e3… |
| Q1 check on frozen code | 2026-11-11T11:37:46Z, `/srv/LRD/q1ref/q1check_20261111T113746Z`: frozen True, match True, ALL 14 FINALS MATCH reference `/srv/LRD/q1ref/REFERENCE_v1.0.json` |
| hash-refusal test | `--set open.G11_lcs_snr=5` → "REFUSING: runner hash … != SPEC_HASHES", exit 10 |
| **GitHub freeze commit** | **Tilanthi/SETI `b06d23dc531e91bc2bf68c4318ea32365eccb21f`, 2026-11-11T11:40:13Z** — `paper/EUCLID_DR1_LRD_SELECTION_SPEC_v1.0.md` (blob 2124e0d9…, = frozen text) and `paper/EUCLID_DR1_LRD_SPEC_HASHES_v1.0.txt` (blob 2bb21689…), blob shas verified via the contents API |
| push-record commit | (second commit: spec copy with the §13.1 push record appended + this file) — see FREEZE report |

Verify the frozen text from any copy: `sed '/^END OF FROZEN TEXT$/q' <spec> | sha256sum` → `cc0208c9…`.
Recompute code hash: on the cluster `cd /srv/LRD && python3 -B code/release/selrun.py hash` (tar includes owner/mode metadata: recompute there).
