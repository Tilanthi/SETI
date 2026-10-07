# BUILD NOTES — v4.12 (referee round 11)

**PDF md5 `bedec477b9b9f37d3b51faede3fc32e1`, 26 pages.** Not pushed.
Gates: `make_all.sh` exit 0; `gate.sh` three times, exit 0, byte-identical output, same md5;
`cleanregen.py` twice, **169/169 byte-identical** each; `abswords` 245/250; `twinmacro`,
`macrosyn`, `synmacro`, `labelcheck`, `figorphan`, `ledgergate`, `intsweep`, `xrefcheck`,
`prosenum`, `consistency`, `macroleak` all clean; 0 `--drive` artefacts.

## ★★★ WHY THE CLEAN REGENERATION EXISTS — READ THIS BEFORE MOVING A GENERATOR

Round 11 produced the clearest example this build has yet given of the defect class
`cleanregen.py` is the only tool that can see.

**`sens_r11.py` and `numbers_v410.py` were CIRCULAR.** `sens_r11.py` read the Class B
completeness factor out of the macro layer — that is, out of `survey_numbers_round103.tex`,
which `numbers_v410.py` writes **from `sens_r11.json`**. On any tree where the macro files
already existed, the read returned the *previous run's* value, every assertion passed, and
the cycle was invisible. From a clean tree the macro is undefined: `MULT_B` came back `None`,
the headline dictionary stayed empty, and `numbers_v410.py` died a hundred lines later with

    KeyError: 'win_med'

**two generators away from the cause, in an error message naming neither of them.** No other
gate in this build could have found it, because every other gate reads what is on disk and
what was on disk was correct. Only deleting the products before rebuilding makes a cycle look
like a cycle.

It was broken by using `sens_r11.py`'s **own** `P90_B` — which its loop already used for every
Class B row, so `MULT_B` was never the number the headline was computed with, only the number
it was reported against — and keeping the macro layer as a cross-check **where it is defined**
and never as the source. That is the discipline `recur_v411.py` adopted for `\LNNRetained`.

The same test, in the same pass, also caught **`maskcat_v412.py`** reading `\DnuAB` sixty
lines before `freqdef_v399.py` writes it (moved below it), and **`fragstale.py`** running
above the generators whose fragments it checks (moved below them). That is the **fifth
consecutive cycle** in which a forward dependency reached a build and only the clean
regeneration found it, and the first in which the dependency was a genuine cycle rather than
an ordering slip.

**Rule for the next person: a generator may never read a macro out of the layer that any
generator downstream of it writes. If it must compare against one, it owns the measurement and
the layer is the cross-check — not the other way round.**

## Round 11 in one page

* **Ruling 1**: the 512-position spatial rank gates no disposition, so it is not charged
  against the completeness. The two-stratum construction, its unmeasured 8–20 P_trig bound and
  the screen-cost arithmetic all leave the paper. `EIRP_90` is **×3.03 P_trig** for Class A and
  ×4.17 for Class B, measured over **49 directly injected Class A windows** (12 per cent, R1-2's
  ≥40 / 10 per cent target exceeded) with 353 transferred; 49 + 353 = 402.
  **Retired with the charge:** `screencost_v410.py` (round 105), `figures/sens_strata.pdf`,
  `make_fig_chain_v411.py`, and `p90_budget_v409.py`'s claim on `\BudDominant`.
* **Ruling 2**: CP−72 2713 is reported **unattributed**. §4.2(ii) no longer claims the species
  list or the selection rule was fixed in advance, because neither was; it claims what is true,
  and Appendix C and the Data Availability statement carry the provenance.
* **Ruling 3**: the mask is a dated catalogue query — 111 transitions of 12 species.
* **The census has ONE owner**, `census_v412.py` (round 205): 56 crossings = 20 attributed + 36
  unattributed, 2 outranking all 512 controls, 0 recurring; the 4 / 31 / 1 disposition split
  published for the first time; and the released catalogue's 35 Class A unattributed reconciled
  with the ledger's 32 as **35 − 4 − 2 + 3**, the three arrivals all HD 14055.
* **Length**: main text **15.25 pp, −5.6 % against v4.11**; main-text prose words **−0.8 %**;
  main-text float area 5.03 → **3.75 pp** after `fig:funnel` and `tab:interesting` left the
  paper and `tab:ledger`, `tab:blockledger` and `fig:bpiccontrol` moved to the appendices.
  ★ **The main text is float-limited, not prose-limited**: with 32 per cent float area under
  `\flushbottom`, deleting a verbatim duplicate paragraph from §4.2 made the document 0.34 pp
  *longer*. Measure float area before cutting prose.
