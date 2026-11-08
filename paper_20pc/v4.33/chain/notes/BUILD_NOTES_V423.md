# v4.23 — build notes (referee round 22)

One self-contained PDF, **39 pp**, `technosignatures_40pc_v4.23.tex`,
`openjournal.cls`, built with `SOURCE_DATE_EPOCH=1577836800`. Target **arXiv
then OJA**: no supporting information, five ancillary files beside the PDF.

Built from v4.22 by `cp -a --reflink=never` (link count 1 and a different
inode on every file checked). ►► **v4.22 was NOT a pristine base** — five
files had been written into it by a wave-1 agent of this round — so the
baseline was proved against the **pushed v4.21** (`ddcbbc4e939b`) through the
GitHub Git Data API instead: local v4.21 is **1,207 of 1,207 common files
byte-identical** to the remote, and of the 1,254 files common to v4.22 and the
rebuilt v4.23 only **five** differ, every one of them explained
(`figures_context_v410.json` stores absolute paths containing the version
folder; `literalsweep.txt`, `.aux`, `.log` and `.pdf` embed the main file's
name — the two text files are byte-identical after substituting the version
string). The inherited tree's strays were removed: `chance_v414.py.orig`,
`figures/.bak_eirp_context.pdf` and every `__pycache__/`.

## Verification of this build
`make_all.sh` rc 0 · `gate.sh` twice rc 0, logs byte-identical, PDF md5
`a57fb5b4f812f8078ef0c7f210d68dd9` · **`cleanregen` 271/271 byte-identical**
(both passes rc 0) · `audit_numbers` **58 PASS / 0 FAIL / 13 WARN** ·
**0 overfull boxes** · **0 Type-3 fonts** · `arxivset --force` **A8
byte-identical**, A2–A6 and A10–A13 PASS, 234 items, 5 ancillary files ·
`genai_sweep --drive` **23 of 23 families fired**, 8 hits on the manuscript
and every one ordinary English · `absmeta` M1–M4 PASS · `abswords` **239
words** · `abschars` **1,480 characters** (arXiv 1920, headroom 440) ·
`abstract_limit` 1,463 · **`prosegate_selfref` PASS, 0 hits, 0 stale pins** ·
`roundcollide` 175/175 round files, 175 inputs, 0 problems · `verpin` 19 pins
into other version directories, **19 guarded, 0 FAIL** · `tabfloor` 0 of 16
floats fail · `floatfit` 0 FAIL.

## New in the build
| file | round | what |
|---|---|---|
| `edge_v423.py` | **960** | the drift grid's own edges: the fitted drifts are grid trials (no sub-step refinement anywhere in the survey), the grid is asymmetric so the declared ceiling bounds it from below only, five crossings lie on an outermost trial and are reported as lower bounds, and the one exclusion of Table 5 uses neither fitted rate |
| `proxb_v423.py` | **961** | Proxima b's orbit against the stacked limit's one-channel tolerance: 47 km s⁻¹, sin i ≤ 0.22 for the stack to apply, and 5.51 × 10¹³ W applying at any inclination |
| `epsx_v423.py` | **962** | the 32 ε Eri Band 6 windows outside the archival extension: which rule removes them, 32 of 32 offsets measured from each block's own `FIELD::PHASE_DIR`, the response floor removing none, and the 1.2 × 10¹⁴ W limit reproduced |
| `num_r22.py` | **971** | the unrecorded-decorrelation set as an **array mix** rather than a median that describes no block, the registration median in channels, one owner for the survey control median, and the provenance of the one window with two extractions |
| `r1_r22.py` | **972** | referee 1's issues 1–3 audited: the 405/391 distinction wherever the carrier search is introduced by size, 34 imputed against 26 measured decorrelation corrections over the 61 systems' best windows, the four configurations with no injected window, and the Class A/B split of Figure 1(a) |
| `verpin.py` | — | a gate, not a generator: no file may read another version directory by an unguarded absolute path |

★ **Rounds 960–962 and 971–972 were one collision.** `r22-edge` and `r22-num`
both claimed 960–962 in their own queue files in the same wave — this
project's fourth double claim and exactly the race `AGENT_RULES.md` warns
about. Edge keeps 960–962; num was renumbered to 971–972 by the integrator,
which is the `ROUND` constant, the file's own header and the manuscript's
`\input`.

## Ordering, which is the thing to read before moving anything
- `edge_v423.py` runs **twice**, and that is a dependency cycle broken in the
  only place it can be: `pairs_v415.py` needs the edge classification of every
  crossing, and `edge_v423.py`'s E0, E4, E5, E6 and E10 need the pairs the
  paper *prints*. `--flags` writes `edge_flags_v423.json` and nothing else;
  the full pass (after `pairs_v415.py` and `traj_v418.py`) publishes round
  960, `tab_edge_v423.tex` and `edge_v423.json` with every clause evaluated,
  and **E11 requires the flags the other generator consumed to be its own row
  for row**, so a stale flags file stops the build instead of reaching the
  page. Both products are in `cleanregen`'s list.
- `epsx_v423.py` **must precede `blockledger_v411.py`**, whose Table A1
  footnote d now reads `\ExRespOffLo`/`\ExRespOffHi`.
- `num_r22.py` **must follow `resp_r16.py`, `tolrecur_r21.py` and
  `numbers_v410.py`**, and `r1_r22.py` **must follow `eta_r19.py` and
  `persys_r17.py`**. ★ Both were first placed above generators whose macros
  they read back, **five consecutive full builds passed**, and only
  `cleanregen` — which deletes the products first — could see it. That is the
  seventh and eighth forward dependency of this kind in this build.

## Layout facts that were measured, not guessed
- **Table D2 is 11 columns and the two constraints pull opposite ways.** At
  `\small` it is 518.42 pt against a 513.12 pt full-width block; at
  `\footnotesize` it fits at 486.16 pt but the `rep` of $T_{\rm rep}$ then
  prints at **5.98 pt against `tabfloor_r17.py`'s 6.50 pt floor**. Shipped at
  `\small` with `\tabcolsep` 4.5 pt: 511.2 pt measured, script size 7.97 pt.
  ★ And `$T_{\rm rep}^{\rm comb}$` had to become **`$T_{\rm comb}$`**: a
  subscript carrying a superscript isolates the subscript as its own line of
  type below the floor, which is a type-floor failure and not a style choice.
- **Figure 1's caption grew by R2-8's class split and the float then
  overflowed its page by 15.5 pt.** Paid for inside the same caption, twice,
  and re-measured: 0 "Float too large" warnings.
- ★★ **The new appendix subsection sits LAST in Appendix D for a reason that
  is not style.** Next to the registration budget, where it belongs by
  subject, its table took the number **Table D1** and pushed the recurrence
  positive controls — the table Referee 2's first point is about, and which
  he and the response letter both call **Table D2** — to D3. Renumbering the
  table a referee is reading about is a cost with no benefit, so the new float
  goes last and takes the new number. The subsection's label is cited from §4
  and §5.6 and is unaffected.
