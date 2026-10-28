# Searching for technosignatures in the ALMA archive — paper version directory

* **The paper:** [`technosignatures_40pc_v4.28.pdf`](technosignatures_40pc_v4.28.pdf)
* **The machine-readable deposit:** [`ALMA_Technosignatures_40pc.zip`](ALMA_Technosignatures_40pc.zip)

Both are byte-identical copies of the files the build writes in `chain/`. The
copies are made by the build itself (`chain/toplevel.py --sync`, the last step
of `make_all.sh` and of `gate.sh`) and the gate battery fails if either differs
from its source, so what is shown here is always what the paper is.

## Layout

| path | what it is |
|---|---|
| `chain/` | the complete build: the manuscript source `chain/technosignatures_40pc_v4.28.tex` and `chain/sections/`, every generator, frozen input, macro file, table and figure, and the gate battery |
| `chain/notes/` | the written record of the referee rounds: build notes, referee responses, push messages |
| `chain/OJA_SUBMISSION.md`, `chain/ARXIV_UPLOAD.md`, `chain/AUTHOR_ACTIONS.md` | submission notes; they sit beside the gates that check them |
| `make_all.sh`, `gate.sh`, `arxivset.sh`, `cleanregen.py` | thin wrappers that run the real scripts in `chain/` |

The build was moved into `chain/` as one unit, so no file's position relative to
any other changed: the regeneration, the gates, the arXiv package and the PDF are
byte-identical to those of the flat tree they came from.

## Rebuilding

```bash
bash make_all.sh                  # regenerate every product
bash gate.sh                      # build the PDF and run the gate battery
python3 cleanregen.py             # delete every product, rebuild twice, compare
bash arxivset.sh <dir> --force    # assemble the arXiv package
```
