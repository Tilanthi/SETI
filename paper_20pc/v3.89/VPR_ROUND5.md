# Virtual peer review — round 5 (last look before submission)

**Remit.** Read the built PDF front to back as a reader, not an auditor; check the
things that are cheap to get wrong and expensive to print; re-verify the headline
numbers against the released catalogue one final time; check round 4's new tables
and revised captions; hunt for residue of the review process; give a submission
verdict.

**Material.** `technosignatures_40pc_v3.85.pdf` (41 pp, build of 2026-09-21
09:35:29 UTC), `technosignatures_40pc_v3.85.tex` (4575 lines),
`per_target_results_v3.85.csv` (1655 × 50), all 63 `survey_numbers*.tex`, the
`tab_*.tex` fragments, `make_fig_missing_v344.py`,
`reproduce_from_catalogue_v385.py` (executed in a sandbox copy — **36 pass,
0 FAIL, 5 skipped**, so the printed `\NReproChecks{36}` is correct and round 4's
Q25 is closed), and the LaTeX log (0 undefined refs, 0 multiply-defined, 0
overfull hboxes, 29 underfull). Eight references checked against the literature
with web search. **No file in this directory was modified.**

---

## MUST-FIX LIST (in priority order)

| # | ID | One line | Where |
|---|---|---|---|
| 1 | **R1** | The abstract's two chance expectations, 3.2 and 1.1, are not the same estimator | abstract, Fig. 3, §4.6, Table 12, conclusions |
| 2 | **R2** | §G.3.1 and Table 24 are a fossil of the 4-stage-1-window era and contradict §5.3.2 | §G.3.1, Table 24 |
| 3 | **R3** | "one observed", "the single unattributed one", "the one unattributed window" — four exist | §G.3.3, App. F, §6.4 |
| 4 | **R4** | `\BenchEffRatio` = 2.5 is hand-typed; the printed inputs give 3.2 | §4.3 |
| 5 | **R5** | A bootstrap median printed outside its own 95 % interval: 0.405 in (0.42, 0.46) | §5.3.1 |
| 6 | **R6** | Table 14 says $T_\star = 4.70$, Fig. 8 on the same page says $T_\star = 3.60$ | Table 14 / Fig. 8 / Table 13 |
| 7 | **R7** | App. F.1: "3 of the 16 … leaving 2" (16 − 3 = 13); and $P(\geq16)=0.22$ at a mean of 3.23 | App. F.1 |
| 8 | **R8** | Table 12 prints $\nu = 0.0000$ GHz on 4 of 7 rows and $\Delta v = -12161$ km s⁻¹ | Table 12 |
| 9 | **R9** | Table 17 hard-codes 19 hosts / 42 planets against the macro's 18 / 41 used four times | Table 17 vs §6.2, §6.3, §6.4 |
| 10 | **R10** | `$p=<0.01$` renders in three places | §5.3.1, Table 21, Fig. 13 |
| 11 | **R11** | Table 21: "the 15 β Pictoris windows … among 416" — 416 is the superseded 431-window freeze | Table 21 text |
| 12 | **R12** | Table 21 text: "9 of the 13 … the one lost" — four are lost, and the table says so | Table 21 text |
| 13 | **R13** | "β Pictoris CO in two transitions and **four** blocks" — eight everywhere else | §4.4 |
| 14 | **R14** | "across two transitions and **nine years**" — 8.4 yr everywhere else | §5.3.4 |
| 15 | **R15** | Table 15: ±7, ±0.2, ±2.0 combine in quadrature to ±7.3, not the printed ±8 | Table 15 |
| 16 | **R16** | "the **0** Band 9 and 10 windows, absent from the metadata snapshot" | App. A |
| 17 | **R17** | "the 12 ε Eri Band 6 windows … select the same **four** windows" | §4.3 |
| 18 | **R18** | Drift ceiling given as 3.6–3.9 m s⁻² once and 3.60–4.00 m s⁻² everywhere else | §4.3 |
| 19 | **R19** | Table 5's crossings row cross-refers Table 4, the spectral-class table | Table 5 |
| 20 | **R20** | Three places claim Table 23 audits all 66 region-max flags; it has 7 rows | §1, §4.2 ×2, Table 23 |
| 21 | **R21** | Table 10's unmeasurable row prints Re/σ = +0.00 and Im/σ = +0.56 | Table 10 |
| 22 | **R22** | Seven sentences read as replies to a referee, not as science | §4.3, §5.3, §5.3.1, §5.3.2, Table 13, §G.5 |
| 23 | **R23** | Reference list is not alphabetised; Sheikh 2025 page is 118 not 108; Manunza is a K-band survey, not L/C | References, §2 |
| 24 | **R24** | Acknowledgement still says "MOST and ASIAA (Taiwan)"; ALMA's current text is NSTC | Acknowledgements |
| 25 | **R25** | Zenodo DOI, submission tag and the White (2026) reference are all placeholders | Data Availability, References |

Everything below #25 I would accept as-is or fix only if the file is open anyway.

---

## Part A — reading it as a reader

I read the PDF front to back once without the catalogue open. The prose is
genuinely good: disciplined, unhedged where it can afford to be, and the
three-stage crossing → stage-1 → candidate logic is easier to follow than in most
SETI papers. §5.3's refusal to pick the flattering reference class, §5.3.1's
commitment-ordering argument and §5.3.2's refusal to adopt the statistic that
improves the result are the paper's best pages and no reviewer should touch them.

The places I stopped, re-read, or disbelieved, in reading order:

1. **Page 2, Tables 1 and 2 back to back.** Two glossaries. Table 1 is "Glossary"
   and Table 2 is "The definitions used throughout … Every term and every power
   scale in this paper is defined here and nowhere else" — which Table 1, sitting
   directly above it, falsifies. Eight terms are defined twice. (**R26**, MINOR.)
2. **Table 2's $p_{\rm rank,min}$ row** contains its own definition twice:
   "…the rank *resolution* of the ensemble and not an attainable false-alarm
   probability, the controls being only approximately exchangeable with the star
   (§5.3.2); the rank *resolution* of one window's control ensemble: the smallest
   per-window probability the design can express". A visible merge artefact on
   page 2. (**R27**, MINOR but the second thing a referee reads.)
3. **Abstract, "3.2 expected by chance over all searched windows or 1.1 over the
   drift-resolving ones alone".** I believed this on first reading and it is not
   true as stated — see **R1**. This is the single most likely thing in the paper
   to be caught in print.
4. **Fig. 3's funnel, step 6, "75 crossings"** sitting between "403 Class A
   windows" and "13 windows". Four of the 75 are Class B (Table 5 says so), so the
   Class A chain passes through a mixed-class number. (**R28**.)
5. **Fig. 3's caption: "The three denominators the text keeps apart are"** followed
   by four things. (**R29**, trivial.)
6. **§5.3, "That is 6 astrophysical sources, not 13 events."** The sentence lands
   immediately after the nine CO events, which are two sources (β Pic and
   HD 48370). Six is the number of stage-1 *systems*. As written it reads wrong.
   (**R30**.)
7. **Table 12.** Four of seven rows carry $\nu = 0.0000$ GHz and one carries
   $\Delta v = -12161$ km s⁻¹. I assumed the table was broken before I found the
   explanation — which is in Table 11's footnote, one table earlier and for a
   different table. (**R8**.)
8. **Table 14 against Fig. 8, same page.** The table caption says "the measured
   value is 4.70"; the figure legend says "$T_\star$ epoch 2 = 3.60". Table 13
   then gives 3.60 again. (**R6**.)
9. **§G.1 and §G.3.2's "the four stage-1 windows"** are CP−72 2713, HD 48370,
   β Pic B3 and β Pic B6 — a different four from Table 11's "4 stage-1 spatial
   outliers with no astrophysical attribution". The same phrase names two
   different sets 20 pages apart. (**R31**.)
10. **§G.3.1 and Table 24.** By this point I no longer believed the appendix was
    describing the same survey as §5. See **R2**.
11. **§G.3.3's closing line, "Counts are those at this build date (2026
    September 13, 07:44 UTC)."** A build timestamp, eight days stale, in the body
    text. (**R32**.)

---

## Part B — the must-fix items, with evidence

### R1 — the abstract's two chance expectations are different estimators. MAJOR

**Evidence.** Abstract: "against `\ExpStageOneAll` expected by chance over all
searched windows or `\BootMeanA` over the drift-resolving ones alone".
`\ExpStageOneAll` = 3.2; `\BootMeanA` = 1.1. Table 8 defines them: 3.2 is
"$1655/(512+1)$; ideal exchangeability", with no tail factor; 1.1 is "block
resampling … over 394 drift-resolving windows", *with* the ×1.4 measured tail
factor. Checked: $1655/513 = 3.226$; $394/513 \times 1.4 = 1.075$. The like-for-like
pair is **4.4 and 1.1** (Table 8's last two rows) or **3.2 and 0.79**.

**Problem.** The abstract, the Fig. 3 funnel (step 9), §4.6 (step 9), Table 12's
caption ("consistent with the 3.2 expected by chance, $p = 0.40$") and conclusion 2
all quote 3.2, while §5.3's whole argument — the one the paper calls the honest
statement — turns on the 4.4 / 1.1 pair. A referee who reads §5.3 and then
re-reads the abstract will conclude the abstract chose the wide, un-tail-corrected
number for the denominator it likes and the narrow, tail-corrected one for the
other. That is precisely the accusation §5.3 was written to pre-empt.

**Fix.** Quote the matched pair everywhere: "against 4.4 expected by chance over
all searched windows, or 1.1 over the drift-resolving ones alone, where every
stage-1 flag in fact lies". Update Fig. 3 step 9, §4.6 step 9, Table 12's caption
and its $p$, and conclusion 2. Drop the "(abstract)" tag from Table 8's first row.
If the authors prefer to keep 3.2 in the abstract, then the abstract must also
carry its Class A partner 0.79, not 1.1.

### R2 — §G.3.1 and Table 24 describe a superseded candidate list. MAJOR

**Evidence.** §5.3.2 and §4.6 step 8: the radius-corrected statistic was run "over
all 1614 windows"; 9 windows flag under both, 4 lose the flag, 1 gains it, the
count falls **13 → 10**. §G.3.1: "Under the adopted screen the flagged set is the
released one, **4 windows**, with 0 added and 0 lost … Under radius matching the one
addition is a Class A window at $T_\star = 5.11$, against 8.1 expected … The number
of *unattributed* stage-1 outliers is **one** for every repair and every debit".
Table 24 lists exactly four windows — β Pic B3, β Pic B6, HD 48370 B6,
CP−72 2713 B7 — and rows "Flagged, whole survey 5 / 4", "Added 1 / 0",
"Expected by chance 8.1 / 0.9".

**Problem.** Two incompatible radius-correction analyses are printed 20 pages
apart, one of them built on a 4-window candidate list this paper does not have.
Neither cross-references the other. This is the most serious residual defect in
the manuscript: a referee who reads Appendix G will conclude that §5.3.2 and
§G.3.1 cannot both be from this survey, and will be right.

**Fix.** Either regenerate §G.3.1 and Table 24 on the 13-window list from the
same generator §5.3.2 uses, or delete §G.3.1 and Table 24 outright and let §5.3.2
carry the robustness check alone. Deletion is cheaper, costs one page, and loses
nothing §5.3.2 does not already say. If they stay, the sentences "the flagged set
is the released one, 4 windows" and "The number of unattributed stage-1 outliers is
one" must be regenerated too.

### R3 — the singular "one unattributed event" survives in three places. MAJOR

**Evidence.**
- §G.3.3: "the pseudo-star rate predicts 4.7 unattributed stage-1 outliers, with
  $P(\geq1) = 99$ per cent, against 3.23 predicted under exchangeability **and one
  observed**." (tex line 4373, a bare literal.)
- App. F: "under the 5σ gate 0.92 stage-1 outliers with $P(\geq1) = 0.60$ for **the
  single unattributed one**."
- §6.4: "Applied to **the one unattributed window** (§5.3) the visibility fit was
  decisive."
- §G.3.1: "The number of unattributed stage-1 outliers is **one** for every repair"
  (folded into R2).

**Problem.** Four unattributed events is the paper's headline result. Three
appendix sentences still say one. Each reads as if the authors never updated the
appendix after the sweep completed.

**Fix.** "…and four observed"; "…for the four unattributed ones, $P(\geq4)$ = …";
"Applied to the four unattributed windows (§5.3) the visibility fit was decisive".
Note that §6.4's sentence is also now *wrong in substance* — the fit was applied
to all thirteen, per Table 10.

### R4 — `\BenchEffRatio` = 2.5 is a hand-typed number that no longer follows. MAJOR

**Evidence.** `survey_numbers.tex` line 6: `\newcommand{\BenchEffRatio}{2.5}`.
§4.3 prints: "a 12-m aperture radiating 1 MW at 230 GHz with a realistic aperture
efficiency of 0.7 has $G = 5.9\times10^{8}$ and an EIRP of $5.9\times10^{14}$ W …
The median Class A effective threshold, $1.9\times10^{15}$ W, misses such a
transmitter by a factor **2.5**." $1.9\times10^{15} / 5.9\times10^{14} = 3.2$.
Against the $\eta = 1$ figure $8.4\times10^{14}$ it is 2.3. Neither is 2.5.

**Problem.** This is the sixth documented instance of the project's own recurring
bug family (`OVERCOUNT`, the 88.2 GHz literal, `PbMax`, `BENCH`,
`BonferroniThresh`), and it is a division a referee performs in ten seconds on a
number the paper offers as an illustration. `\BenchEffRatio` is not among the 36
quantities `reproduce_from_catalogue_v385.py` guards.

**Fix.** Set `\BenchEffRatio` from `\PeffWinMedA / \BenchEirpSeven` in the
generator, and add it — with `\BenchGainSeven`, `\BenchEirpSeven`,
`\BenchGainSci`, `\BenchEirpSci` — to the reproduce script as an assertion at the
point of use. The correct printed value is **3.2**.

### R5 — a bootstrap median printed outside its own 95 % interval. MAJOR

**Evidence.** §5.3.1: "…and a star-clustered bootstrap placing the median at
`\HoRankMed` (95 per cent interval `\HOBootLo`–`\HOBootHi`)" →
"**0.405 (95 per cent interval 0.42–0.46)**".

**Problem.** A point estimate outside its own confidence interval. The macros
`\HoRankMedLo` = 0.341 and `\HoRankMedHi` = 0.458 exist and are used correctly
earlier in the same subsection ("block-clustered 95 per cent 0.341–0.458"), so the
paper carries two intervals for one median, one of which is impossible. Round 1's
C11 raised this and the disposition rebutted it by pointing at the *other*
interval; on this occurrence the reviewer was right. Note 0.42–0.47 is the
*survey* interval (`\SurvBootLo/Hi`), printed one sentence later — so 0.42–0.46
looks like a mis-assignment of a neighbouring quantity.

**Fix.** Regenerate `\HOBootLo`/`\HOBootHi` from the star-clustered bootstrap that
produced 0.405, or delete the parenthesis and let the block-clustered interval
earlier in the subsection carry it. Add an assertion `lo <= med <= hi` in the
generator for every (median, interval) macro triple; it is a two-line check that
would have caught this class permanently.

### R6 — $T_\star$ for the CP−72 2713 repeat block has two values in three floats. MAJOR

**Evidence.**
- Table 14, row "T⋆ in this window": first block 5.81, repeat block **4.70**
  (`\CpTstarTwo`). Caption: "A source at the first block's flux would have
  returned $T_\star = 6.21$ there; the measured value is **4.70**."
- Fig. 8, same page, legend: "**$T_\star$ epoch 2 = 3.60**"; caption: "…while the
  star falls to **3.60**." The generator (`make_fig_missing_v344.py`, line 88)
  takes `rec["e2_drift_max_at_ch35"]["T"]`.
- Table 13(b), row "T⋆ at the same tuning, further block": **3.60**.
- §5.3.6 body: "Maximised afresh over the repeat block's own drift grid, the same
  channel returns $T_\star = 3.60$ against 5.81."
- Table 11, "repeat blocks" column: "1; $T_\star = 4.70$".

**Problem.** Two estimators (window maximum vs. drift-maximised at the event
channel) share one symbol, and the table and the figure sitting on the same page
of the same subsection disagree by 1.1 with no note. Worse, the text's description
is self-defeating: "maximised afresh over the drift grid" returning a *smaller*
number than the fixed-cell value is impossible to a reader who does not know that
4.70 is a different maximisation.

**Fix.** Give them different symbols. Suggest $T_\star^{\rm win}$ = 4.70 (maximum
over the repeat block's window) and $T_\star^{\rm cell}$ = 3.60 (drift-maximised at
the event's own channel), defined once in Table 14's caption and used consistently
in Table 11, Table 13 and Fig. 8's legend. Then the §5.3.6 sentence reads
correctly.

### R7 — App. F.1's rank-first arithmetic does not close. MAJOR

**Evidence.** §F.1: "The survey expectation is 3.23 and **16** are observed; the
execution-block clustered permutation returns $P(\geq16) = 2.2\times10^{-1}$, and
the excess is astrophysical, celestial line emission sitting at the stellar
position in **3 of the 16** (Table 12) and leaving **2** against 3.23 expected."

**Problem.** Three defects in one sentence. (i) $16 - 3 = 13$, not 2. (ii)
$P(\geq16)$ at a mean of 3.23 is of order $10^{-7}$ even with generous clustering;
0.22 is not a possible value and is the number a reader will check first. (iii)
"3 of the 16" does not match Table 12, which disposes of **9** of the 13 stage-1
windows as CO in 2 systems and 3 star–band pairs — so "3" is a pair count silently
compared with a window count. The 16 itself is right: Table 21 gives rank-first
windows 9 (12 m) + 7 (ACA) = 16, against 13 stage-1 after the 5σ gate.

**Fix.** Rewrite the passage on one unit. Something like: "The survey expectation
is 3.23 rank-first windows and 16 are observed, a factor 5.0; 13 of the 16 also
cross the 5σ gate and are the stage-1 windows of Table 12, of which 9 are celestial
line emission at the stellar position. What is left is 4 against 3.23 expected."
Replace $P(\geq16)$ with the clustered permutation value actually computed, or
delete it.

### R8 — Table 12 prints a zero frequency and a 12 000 km s⁻¹ velocity offset. MAJOR

**Evidence.** `tab_flagged_v380.tex`: β Pic B3, 61 Vir, HD 14055 and HD 23484 all
carry $\nu = 0.0000$ GHz; $\Delta v$ reads $+449$, $-12161$, $-1323$, $+328$ km s⁻¹.
Confirmed in the catalogue: `f_cross_GHz` is NaN for those rows and
`line_offset_kms` is $-12160.5$ for HD 14055 (computed from the window edge, since
there is no crossing channel).

**Problem.** The caption says $\nu$ is "the crossing channel" and $\Delta v$ "the
offset of **that channel** from the nearest laboratory rest frequency". For four of
seven rows there is no such channel, so one column is zero and the other is
meaningless — and $-12161$ km s⁻¹ is the number a referee will screenshot. Table 11
carries the correct footnote for the same fact, one table earlier and for a
different table.

**Fix.** Print an em-dash where `f_cross_GHz` is missing, print the window range as
Table 11 does, and suppress $\Delta v$ on those rows entirely (or footnote it as a
window-edge bound, not a channel offset). Carry Table 11's footnote into Table 12's
caption.

### R9 — Table 17 contradicts the exoplanet-host macros used four times. MAJOR

**Evidence.** `tab_selection.tex`: body row "Known planet hosts 20 (11.9 %) |
**19** (21.1 %) | 1.8"; footnote b: "The 90 searched stars include **19** hosts of
**42** known planets." Macros: `\NExoHosts` = **18**, `\NExoPlanets` = **41**, used
at tex lines 3009, 3010, 3113, 3114, 3187, 3193 (§6.2, §6.3, §6.4).

**Problem.** A number that exists twice — the round 1–4 signature — in the one
table a referee interested in the sample will read. §6.4's "1 of the 39 known
planets is therefore outside the searched domain and 38 are inside" also rests on
the 41, so the table's 42 breaks that count too.

**Fix.** Drive the Table 17 row and footnote from `\NExoHosts` and `\NExoPlanets`,
and add both to `reproduce_from_catalogue_v385.py` (they are derivable from the
catalogue's star list against the NASA Exoplanet Archive snapshot the release
ships). Whichever value is right, it must appear once.

### R10 — `$p=<0.01$` renders in three places. MAJOR (typography)

**Evidence.** `\HOKsP` = `<0.01`, `\KsAcaP` = `<0.001`, `\KsFineP` = `<10^{-4}`
are used as `$p=\HOKsP$` (line 2281), `$p=\KsAcaP$` (line 3902),
`$p=\KsFineP$` (line 4055). Printed: "(D = 0.08, p =< 0.01)" in §5.3.1,
"(D = 0.10, p =< 0.001)" in the Table 21 discussion, "fine D = 0.150, p =< 10⁻⁴"
in Fig. 13's caption.

**Fix.** Delete the `=` at those three use sites (the macros already carry the
relation), or rename the macros to `\HOKsPrel` and have them expand to
`{}<0.01`. Then grep the whole file for `$p=\` against every macro whose value
begins with `<`.

### R11 — Table 21's β Pictoris exclusion is a fossil of the 431-window freeze. MAJOR

**Evidence.** Table 21 discussion: "Excluding **the 15 β Pictoris windows** leaves
**one** unattributed crossing among **416**, against 3.13 expected
($P(\geq1) = 96$ per cent)." Catalogue: β Pic has **50** windows, **25** Class A,
**12** crossings, **8** stage-1. $431 - 15 = 416$, and 431 is the Class A count at
the v3.72-era freeze; the current count is 403. Meanwhile $3.13 = 1605/513$, i.e.
$1655 - 50$ — the *current* β Pic window count. The sentence mixes two vintages.

**Fix.** Regenerate the whole sentence from the catalogue. On current numbers:
excluding β Pictoris' 50 windows leaves 3 unattributed stage-1 outliers among 1605,
against 3.13 expected under exchangeability. Add `\ExclBpicWin` and the associated
counts to the reproduce script.

### R12 — Table 21's text contradicts Table 21. MAJOR

**Evidence.** "The 12 m stratum holds **9 of the 13** stage-1 outliers, **the one
lost** being HD 48370's foreground CO". The table's own rows: stage-1 outliers
12 m = 9, ACA 7 m = **4**.

**Fix.** "The 12 m stratum holds 9 of the 13 stage-1 outliers; the 4 in the ACA
stratum include HD 48370's foreground CO, the only one of them that carries an
attribution." Check which of the four is meant — the preceding paragraph says "Of
the stage-1 outliers only HD 48370 Band 6 is ACA", which is a third statement and
also contradicts the table's 4. Resolve all three against the catalogue before
printing.

### R13 — "two transitions and four blocks". MAJOR

**Evidence.** §4.4: "the recovery and localisation of β Pictoris CO in two
transitions and **four** blocks (§5.3.4)". A bare literal at tex line 1341.
Everywhere else — abstract, §1, §5.3, §5.3.4, conclusion 2 — it is **8** execution
blocks, and the catalogue confirms 8 stage-1 β Pic windows across 8 distinct EBs.

**Fix.** Replace with `\NStageOneBpicEb`.

### R14 — "across two transitions and nine years". MAJOR

**Evidence.** §5.3.4: "*The velocities agree, across two transitions and **nine
years**.*" A bare literal at tex line 2555. The same paragraph then says "over
8.4 yr from 2013-10-06 to 2022-03-03", and the abstract, §5.3.4's opening and
Table 22 all use 8.4 yr. Round 1's C55 recorded this as fixed; it was not.

**Fix.** "across two transitions and `\BpicSpanYr` years", or simply "across two
transitions and eight years".

### R15 — the P90 budget's quadrature sum does not add up. MAJOR

**Evidence.** Table 15, first block: Absolute flux scale ±7, Distance ±0.2,
Injection statistics ±2.0; "*Combined* in quadrature **±8**".
$\sqrt{7^2 + 0.2^2 + 2.0^2} = 7.28$.

**Problem.** ±8 only appears if the one-sided pointing term (+1.9), which the
table deliberately places *below* the Combined line, is folded in:
$\sqrt{7^2+0.2^2+2^2+1.9^2} = 7.5$. Either way the printed table does not produce
the printed total. §5.5 repeats "±8 per cent" twice and conclusion 3 a third time,
so this propagates to the conclusions. This is a brand-new table from round 4's
wake and is the kind of arithmetic a referee checks first in a budget table.

**Fix.** Print ±7, or move the pointing term above the line and print ±8 with the
four terms visible. Derive the total in the generator rather than typing it.

### R16 — "the 0 Band 9 and 10 windows". MAJOR (presentation)

**Evidence.** App. A: "…and the `\NNoArchRes` Band 9 and 10 windows, absent from
the metadata snapshot, take ALMA's default." `\NNoArchRes` = **0**. The count is
correct — 1509 + 146 = 1655, so no window lacks an archive resolution — but the
sentence describes an empty set, and §G.6 four pages later says "The **12**
Band 9/10 windows toward AU Mic and HD 61005 are included", which a reader will
read as a contradiction.

**Fix.** Delete the clause, or rewrite: "and every Band 9 and 10 window resolves in
the metadata snapshot." Guard it: any sentence whose subject is a macro that can
be zero needs an `\ifnum` or must be generated.

### R17 — twelve ε Eri windows, four selected. MAJOR

**Evidence.** §4.3: "Beyond it are the `\EpsEriNWin` ε Eri Band 6 windows at
1.0–3.5× … the two criteria are independent and select **the same four windows**."
`\EpsEriNWin` = 12. Bare literal at tex line 1294.

**Fix.** "select the same twelve windows" if that is the case, or state the four
explicitly. As printed the sentence contradicts its own subject.

### R18 — the drift ceiling is printed as two different ranges. MAJOR

**Evidence.** §4.3: "12–13 Hz s⁻¹ GHz⁻¹ is $(1.2$–$1.3)\times10^{-8}$ s⁻¹, that is
$|a_{\rm los}| = $ **3.6–3.9** m s⁻² independent of observing frequency".
Everywhere else — §4.2 ("$a_{\rm max} = 3.6$–4.0"), §4.5 ("12.0–13.3 Hz s⁻¹ GHz⁻¹,
line-of-sight $|a| = 3.60$–4.00"), §5.5 (iv), §6.1, Fig. 12, Table 5 — it is
3.60–4.00 m s⁻². Catalogue: `a_max_m_s2` runs 3.598–3.999.

**Problem.** The §4.3 sentence also makes TRAPPIST-1 b ($a_{\rm los} = 4.00$) look
further outside the grid than the paper elsewhere claims (it "misses by 0.01 per
cent").

**Fix.** Make §4.3 use the same macros: "12.0–13.3 Hz s⁻¹ GHz⁻¹ is
$(1.20$–$1.33)\times10^{-8}$ s⁻¹, that is $|a_{\rm los}| = 3.60$–4.00 m s⁻²".

### R19 — Table 5's crossings row cross-refers the wrong table. MAJOR

**Evidence.** Tex line 673: "Threshold crossings ($\geq5\sigma$ at the stellar
position) & `\NHits` windows (`\NHitsA` Class A, `\NHitsB` Class B;
Table~\ref{tab:specclass})". `tab:specclass` (line 517) is Table 4, "The archival
selection by spectral class", which contains nothing about crossings. Printed:
"75 windows (71 Class A, 4 Class B; Table 4)".

**Fix.** Point at Table 12 (the stage-1 dispositions) or Table 18 (the per-band
census), whichever was meant, or drop the reference. Note the related **R33**
below: the adjacent row renders "Table 7 (amplitude); Table 7 (dwell)" because
`tab:dwell` and `tab:classcomp` are two labels on one float.

### R20 — three sentences claim Table 23 audits all 66 region-max flags. MAJOR

**Evidence.**
- §1: "Table 23 audits **every window the region form flags**."
- §4.2: "§G.4 gives the comparison and Table 23 audits **every window either form
  flags**."
- §4.2 again: "§G.4 compares the two forms and audits **every window the asymmetric
  one flags**."
- Table 23's own caption is correct — "this table gives the pairs either statistic
  promotes to stage 1, **not all 66 of them**" — and the table has 7 rows.

**Problem.** Round 1's C6 corrected the caption and left the three forward
references that assert the opposite. Worse, Table 23's *title* is "The stage-1
star–band pairs, scored under both statistics", and it omits three of the seven
real stage-1 pairs (61 Vir B7, HD 14055 B7 at 330–332 GHz, HD 23484 B6) while
including two pairs that are not stage-1 at all (AU Mic, ALMA J1537−3319) and one
HD 14055 window at a different frequency (345.14 GHz) from the flagged one. A
reader who goes to Table 23 to find the four unattributed events will not find
three of them.

**Fix.** Rewrite the three forward references ("Table 23 compares the two forms on
the pairs either promotes"). Then either extend Table 23 to all seven stage-1
pairs, or retitle it "Star–band pairs on which the two statistics disagree" and say
so in §5's "13 windows against 66" sentence.

### R21 — Table 10 prints numbers for the window it says cannot be measured. MAJOR

**Evidence.** `tab_visfit_v385.tex`, last row: "β Pic | 6 | 405 900 | **+0.00** |
**+0.56** | +1.53 | track too wide to reference". Caption: "The one β Pictoris
window marked unreachable has a drift track wider than the continuum reference
leaves."

**Problem.** A referee will ask how an imaginary part of $+0.56\sigma$ is obtained
on a window with no usable continuum reference, and whether +0.00 is a measurement
or a fill value. It is a fill value.

**Fix.** Print em-dashes in Re/σ, Im/σ and ctrl on that row.

### R22 — residue of the review process. MAJOR (the author asked for this specifically)

Seven passages read as replies to a referee rather than as science. In descending
order of how obvious they are:

| Where | Text | Rewrite |
|---|---|---|
| §5.3 | "**Earlier versions of this analysis reported that three of the four had no second epoch**; that was an artefact of matching repeat blocks on a crossing frequency the release stores only sometimes, and the evidence is stronger than the claim it replaces." | Delete the sentence. The paragraph already states the result: all four have repeat coverage, 23 blocks, none recurs. |
| Table 13 caption | "…**an earlier version of this table assigned three of them to the calibration sample, which** `holdout_assignment_v381.json` **contradicts**…" | "All four are survey-sample blocks (`holdout_assignment_v381.json`)." |
| §5.3.1 | "All four are survey blocks — **we previously described three of them as belonging to the external calibration sample, which the assignment file does not support, and we withdraw the version of the argument that rested on it.**" | "All four are survey-sample blocks." Then keep the following sentence, which carries the argument. |
| §5.3.1 | "…the drift-resolved injection analysis (Appendix B) and the $P_{90}$ uncertainty budget were all built afterwards, **in response to review**." | "…were all built after the reservation." The commitment-ordering argument needs the ordering, not the cause. |
| §5.3 / §G.5 | "**This supersedes an earlier result for CP−72 2713. A single-block fit reported at an earlier stage of this work returned 5.5σ** … **We therefore adopt it and withdraw the 5.5σ point source.**" | Present the two estimators as two estimators: "A uniform single-channel fit to this window returns 5.5σ at the star; a drift-following fit that removes a continuum per integration returns −0.86σ. The window's stellar continuum is 10.9 mJy, almost exactly the 10.4 mJy the uniform fit attributes to a narrowband excess, so the drift-following value is the one we adopt." Keep §G.5's detail, drop the withdrawal narrative. |
| §4.3 | "Transfer to other bands, channelisations and integration times is **no longer assumed but measured** on 28 further configurations" | "Transfer … is measured on 28 further configurations". |
| Fig. 11 caption | "The spread between grey curves is the completeness transfer that **was previously assumed rather than measured**." | "The spread between grey curves is the completeness transfer between configurations." |
| §5.3.2 | "The stellar debit $m(0)$ is **no longer needed** and is not used in the primary analysis." | "The stellar debit $m(0)$ is not used in the primary analysis." |
| Appendix B | "…the coarse variant recovered none of 500 injections … which is **the one withdrawn result here**: the criterion produced the artefact and the pipeline suppresses nothing." | Keep the substance, drop "the one withdrawn result here". |

Two passages I would **keep** even though they refer to the paper's own history,
because they are methodological commitments and not replies: §5.3.1's
commitment-ordering paragraph, and §5.3.2's "We do not adopt the radius-corrected
statistic as the primary one, and we say why."

### R23 — the reference list. MAJOR (cheap to get wrong)

**Not alphabetised.** Six entries are out of order: `Astropy Collab.` and
`CASA Team` sit after `Blomme`; `Ginsburg` before `Gentile Fusillo`; `Müller`
before `Morrison`; `Manunza` between `Tremblay` and `Vidal`; `SpaceX` between
`Wright` and `Zhang`. Alphabetise on the sort key the bibliography style expects.

**Checked against reality (8 + 4 spot checks):**

| Reference as printed | Reality | Verdict |
|---|---|---|
| Cocconi & Morrison 1959, Nature 184, 844 | correct | ✓ |
| Drake 1960, PhT 13, 40 | correct | ✓ |
| Enriquez et al. 2017, ApJ 849, 104 | correct (692 stars, GBT) | ✓ |
| Margot et al. 2023, AJ 166, 206 | correct (11,680 stars, GBT L-band) | ✓ |
| Matrà et al. 2017, MNRAS 464, 1415 | correct (β Pic CO) | ✓ |
| Cataldi et al. 2023, ApJ 951, 111 | correct, and does cover HD 48370 | ✓ |
| Manunza et al. 2025, AcAau 233, 155 | bibcode correct | ✓ volume/page |
| **Sheikh et al. 2025, AJ 169, 108** | *Earth Detecting Earth*, **AJ 169, 118**, doi 10.3847/1538-3881/ada3c7 | ✗ **page wrong** |
| **Mason et al. 2024, MNRAS 536, 2127** | ADS bibcode **2025**MNRAS.536.2127M; arXiv 2411.19827 | ✗ year; cited as "Mason et al. (2024)" nine times |
| Wright et al. 2018, AJ 156, 260 | correct | ✓ |
| Hallinan et al. 2015, Nature 523, 568 | correct | ✓ |
| Gaia Collab. 2022, arXiv:2206.05595 | preprint cited where A&A 674, A5 (Katz et al. 2023) exists | MINOR |

**Mis-description in §2.** "a single-dish L/C-band programme at the Sardinia Radio
Telescope (Manunza et al. 2025)". That paper is *The First **High Frequency**
Technosignature Search Survey with the Sardinia Radio Telescope* — C- and K-band,
with K-band the point of it. The very next sentence, "Essentially all of that work
lies below ∼10 GHz", is weakened by the same error.

**Fix.** Correct the Sheikh page to 118; decide on Mason 2024 vs 2025 and make the
in-text year match (I would use 2025, the ADS year, and change all nine in-text
citations); rewrite the Manunza clause as "a single-dish C/K-band programme at the
Sardinia Radio Telescope" and soften "essentially all of that work lies below
∼10 GHz" accordingly; swap the Gaia preprint for the published DR3 RV paper.

### R24 — the ALMA acknowledgement is out of date. MINOR but free

**Evidence.** "…together with NRC (Canada), **MOST** and ASIAA (Taiwan), and KASI
(Republic of Korea)". Taiwan's MOST became the **National Science and Technology
Council (NSTC)** in 2022, and ALMA's standard acknowledgement text has said NSTC
since. Also absent: any funding acknowledgement, and any acknowledgement of the
ALMA Science Archive's own requested citation beyond the JAO project-code form.

**Fix.** "…NRC (Canada), NSTC and ASIAA (Taiwan), and KASI (Republic of Korea)".
Add whatever grant support applies before submission.

### R25 — three placeholders remain in the Data Availability statement. MAJOR (blocking)

**Evidence.** "the repository commit **tagged at submission**"; "The deposit carries
a DOI **minted on acceptance**"; and the References: "White G. J., 2026, MNRAS,
**submitted**", cited in §2 as the source of a numerical result
(EIRP$_{\rm min} \sim 5$–$10\times10^{13}$ W for TRAPPIST-1).

**Problem.** None of the three is a defect of the science; all three are
submission blockers. The White (2026) one is the worst: a reader cannot check a
quoted EIRP against a paper that does not exist publicly.

**Fix.** (a) Create the submission tag and name it. (b) Mint the Zenodo DOI now —
Zenodo mints on deposit, not on acceptance, and the sentence as written suggests
otherwise. (c) Either give White (2026) an arXiv identifier, or delete the quoted
EIRP range and cite it only as the origin of the target list.

---

## Part C — further defects, MINOR unless noted

**R26 (MINOR).** Tables 1 and 2 are both glossaries; Table 2 claims "Every term and
every power scale in this paper is defined here and nowhere else", which Table 1
falsifies. Merge them or drop the claim.

**R27 (MINOR).** Table 2's $p_{\rm rank,min}$ row contains its definition twice
(tex lines 390–395). Delete from "; the rank *resolution* of one window's" to the
end of the cell.

**R28 (MAJOR-adjacent).** Fig. 3 step 6 puts "75 crossings" — 71 Class A + 4
Class B — inside a chain whose step 5 is "403 Class A windows". Either print 71 at
step 6 and note the 4 Class B crossings elsewhere, or label the step "75 crossings
(71 in Class A)". §4.6 step 6 has the same problem.

**R29 (MINOR).** Fig. 3's caption: "The three denominators the text keeps apart
are the catalogued population, the 168-entry … work list, the ∼115 stars … and the
90 searched" — four items. Say "four".

**R30 (MINOR).** §5.3: "That is 6 astrophysical sources, not 13 events" follows the
nine CO events, which are two sources. Reword: "The 13 events are 6 systems, and
the 9 CO events are 2 sources."

**R31 (MAJOR-adjacent).** §G.1 ("For each of the **four stage-1 windows**"), §G.3.2
("over the **4 stage-1 windows** of the released catalogue for which the full
control vectors were retained") and App. F ("built to carry the **four stage-1
windows** past that floor") all mean {CP−72 2713, HD 48370, β Pic B3, β Pic B6} —
a different four from Table 11's "4 stage-1 spatial outliers with no astrophysical
attribution". Rename to "the four windows with retained control spectra"
throughout Appendix G.

**R32 (MINOR but embarrassing).** §G.3.3 ends "Counts are those at this build date
(2026 September 13, 07:44 UTC)" — eight days before the build the PDF carries.
Delete `\HOAsOf` and the sentence; the frozen-release date belongs in Data
Availability, not mid-appendix.

**R33 (MINOR).** Table 5 renders "Completeness, by class and experiment: **Table 7
(amplitude); Table 7 (dwell)**" because `tab:dwell` and `tab:classcomp` are two
labels on one float. Round 1's C41 was dismissed on the grounds that each label
occurs once, which is true and beside the point. Print "Table 7(a) and 7(b)".

**R34 (MINOR).** §6.2: "the remaining 97.5 GHz (**Bands 4–8**) lies wholly outside
it" — Bands 9 and 10 contribute 4 and 8 windows and 20.7 GHz of union. Write
"Bands 4–10".

**R35 (MINOR, carried from round 4's m19).** §6.4: "9 of the 13 stage-1 outliers
are molecular emission toward disc hosts, arising in 2 of the 69 debris-disc
systems searched: one flagged system in 34". One of those two is HD 48370, whose CO
the paper identifies throughout as *foreground*, not circumstellar. As a
false-positive rate for disc-selected archives the attribution is wrong. Rewrite:
"…arising in 2 of the 69 debris-disc systems, one circumstellar (β Pictoris) and
one an unrelated foreground cloud on the sight line to a disc host".

**R36 (MINOR).** §5.1: "Barnard's Star and Wolf 359 are the second- and
**fourth**-nearest stellar systems." On the standard list Wolf 359 is fifth (after
α Cen, Barnard's, Luhman 16, WISE 0855−0714) or third if brown dwarfs are
excluded. Since the sentence supports a priority claim ("these appear to be the
first"), get it right: "the second- and fifth-nearest stellar systems" (or "…the
second- and third-nearest hydrogen-burning stars").

**R37 (MINOR).** §5.3.1: "The rank distribution of the remaining `\HONoiseWin`
windows" prints 578 with no denominator anywhere near it, while §G.3.3 says "the
**599** calibration windows carrying no attributed line" and Table 13 says the
calibration sample is **1322** windows. Three counts of overlapping sets, none
reconciled. State the denominators: 1322 searched, 599 with no attributed line,
578 entering the null test (and why 21 drop out).

**R38 (MINOR).** §G.3.3: "over all **1326** calibration windows … and **327**
execution blocks", against Table 13's **1322** windows and **326** blocks. Two
off-by-small differences on the same sample. Reconcile or state what the extra four
windows are.

**R39 (MINOR).** §G.3.3: "The displacement is widespread … **23 of 27 stars**
having a median rank below 0.5" and §G.3.1's "Leaving each of the **27 calibration
stars** out of the fit", against the very next paragraph's "**The calibration
sample covers 56 stars**". Name the 27 subset ("the 27 stars with ≥5 calibration
windows", or whatever it is).

**R40 (MINOR).** §5.3.6 and §6.2 quote "**4.7** chance events the survey expects"
(`\PseudoExpFlags`), which is absent from Table 8 — the table whose caption promises
"The chance expectations quoted in this paper, and what each one assumes". Table 8
also gives 4.4 for what looks like the same quantity. Add a 4.7 row with its
assumption (pseudo-star rate over 1655 windows), or replace the two uses with 4.4.

**R41 (MINOR).** Fig. 9's caption: "×2.29 for the spectral response and
intra-integration smearing and then by ×1.2 from the injection campaign, **so a
value of 1 here is ×2.81 the trigger power**". 2.29 × 1.2 = 2.75. The 2.81 is
right — it is the median of the per-window ratio $P_{90}/P_{\rm trig}$, which I
confirmed from the catalogue — but it cannot be reached from the two rounded
factors as the sentence invites the reader to do. Say "×2.81 at the survey median".
The same rounding tension appears in Table 5, where $P_{90} = 1.2\,P_{\rm eff}$
with medians 2.4 × 10¹⁵ and 1.9 × 10¹⁵ (1.9 × 1.2 = 2.3). One footnote covering
both — "medians of ratios, not ratios of medians" — would close it.

**R42 (MINOR).** Table 7's caption describes "The **0 of 500** coarse-window entry"
which does not appear anywhere in Table 7; it is in Appendix B. Either add the
entry or move the sentence. Footnote *a* says "transfer to **the other 403** Class A
windows", which cannot be "other" than 403 of 403 — §5.5 uses 375 for the same set.

**R43 (MINOR).** Text says trial drift rates run "2–**1944**" (§4.3, §5.3.4); the
catalogue's `n_drift_trials` maxes at **1945**. Off by one in three places.

**R44 (MINOR).** §6.3's "81 of the 90 searched stars were observed under proposals
categorised *Disks and planet formation* (**Fig. 2**)" — Fig. 2 is the
spectral-class histogram and says nothing about proposal categories. Drop the
reference or point at the pointing ledger in the release.

**R45 (MINOR).** The released catalogue's `disposition` column carries a value for
**10** rows only (8 circumstellar CO, 1 foreground CO, 1 "unattributed; absent in
epoch 2"), and the Data Availability statement says exactly that. But Table 12
disposes of **13** windows including **4** unattributed pairs, so 61 Vir,
HD 14055 and HD 23484 carry "unattributed" in the paper and nothing in the
release. A reader doing the paper's own suggested column filter will not reproduce
Table 12. Either populate the column for all 13 or say in the DA statement which
three are absent and why.

**R46 (MINOR, robustness not print).** `reproduce_from_catalogue_v385.py` **skips**
five checks whose macros no longer exist (`NCatFlagGlobal`, `NCatFlagLocal`,
`LocAllFlagGlobal`, `RingThetaMin`, `RingThetaMax` — all casualties of
`retire_macros.py`). A guard that silently stops guarding when prose is trimmed is
the same failure mode as the retired-macro trap already in the project notes. Make
a skip a failure unless the macro is on an explicit retired list.

---

## Part D — what reconciles, and should not be touched

I re-derived the headline numbers from `per_target_results_v3.85.csv` directly.
Everything below matches the printed value:

- 1655 rows; **90** stars; **82** systems; **404** execution blocks; 1616 distinct
  (EB, window) datasets (1655 − 39 duplicates).
- **403** Class A / **1252** Class B; **75** crossings (**71** A + **4** B);
  **13** stage-1, **all** Class A; **66** region-max flags.
- Bands 3/4/5/6/7/8/9/10 = 112/4/4/1072/427/24/4/8, summing to 1655.
- Frequency union **118.13 GHz** in **46** islands, 89.6–873.1 GHz; Class A
  **47.74 GHz** in **26** islands, 114.0–873.1; Class B **90.50 GHz** in **35**,
  89.6–682.8; summed bandwidth **2835 GHz** = **24.0×** the union.
- $P_{90}$ Class A **6.3 × 10¹³ – 1.1 × 10¹⁷ W**, median **2.4 × 10¹⁵**; per
  system **6.3 × 10¹³ – 2.0 × 10¹⁶**, median **1.3 × 10¹⁵** over 60 systems.
- $P_{\rm eff}$ A **5.1 × 10¹³ – 9.1 × 10¹⁶**, median **1.9 × 10¹⁵**; B
  **3.7 × 10¹³ – 6.4 × 10¹⁷**, median **1.4 × 10¹⁵**.
- $P_{\rm trig}$ A **2.2 × 10¹³ – 6.8 × 10¹⁶**, median **9.4 × 10¹⁴**; B
  **1.6 × 10¹³ – 2.8 × 10¹⁷**, median **6.0 × 10¹⁴**; all-sample median
  **7.1 × 10¹⁴**.
- $P_{\rm eff}/P_{\rm trig}$ **1.33–3.98**, median **2.286** → the ×2.29 of Table 2,
  Fig. 5 and Fig. 10 is correct and does include smearing, as Table 2 says.
- $P_{90}/P_{\rm eff}$ **1.229** exactly for every window (→ "×1.2");
  $P_{90}/P_{\rm trig}$ median **2.809** (→ Fig. 9's ×2.81).
- On-source **21–5274 s**, median **2812**; $S_{\rm min}$ **0.41 mJy – 1.30 Jy**,
  median **9.8 mJy**; distances **1.3016–39.6344 pc**.
- Drift ceilings **1.086–10.47 kHz s⁻¹**; $a_{\rm max}$ **3.598–3.999 m s⁻²**;
  $\eta_{\rm drift}$ A 0.17–422 median 14.7, B 0.004–1.35 median 0.51;
  **428** windows at $\eta_{\rm drift} \geq 1$ against 403 in Class A.
- 1655/513 = **3.226**; 1616/513 = **3.150**; 403/513 = **0.786**; 1252/513 =
  **2.44**; 601/513 = **1.17**; 1054/513 = **2.05**; 0.05/1655 = **3.02 × 10⁻⁵**,
  a factor **65** below 1/513.
- Exposure 6.8 × 10⁶ s GHz = **1900** star-hour-GHz (the ×4.8 error of C51 is
  fixed). Mask cost 4.811/118.13 = **4.1 %**, band-by-band table sums correctly.
- §5.1's Barnard's Star **6.2–9.3 × 10¹³ W over 12 windows** and Wolf 359
  **7.3 × 10¹³ – 1.1 × 10¹⁴ W over 12** both check out, as does UV Ceti's
  **1.6 × 10¹³ W**.
- Table 5's 1725 − 45 − 13 − 12 = 1655; Table 3's 404/77/47/3; Table 17's
  12+13+18+19+28 = 90 and 1+9+16+6+21 = 53; Table 20's 229 − 174 = 55 and the
  1.32 × 10⁸ cells → 37.8 Gaussian expectation; Appendix B's 113 + 19 = 132 and
  113/403 = 28 %; Table 7(b)'s 1944 + 1944 = 3888; Fig. 6(b)'s 27+12+8+8+27 = 82.
- The aperture-gain worked example ($G = 5.9\times10^8$, EIRP $5.9\times10^{14}$ W
  at $\eta = 0.7$; $8.4\times10^8$ and $8.4\times10^{14}$ at $\eta = 1$) is right —
  only the *ratio* that follows it (R4) is not.
- Fig. 1 now plots 90 stars (25 Class B + 65 Class A), so round 4's Q1 is closed;
  `\NStarBands` reads 113 against the catalogue, so Q2 is closed;
  `\NReproChecks` = 36 is what the shipped script produces, so Q25 is closed.
- LaTeX: 0 undefined references, 0 multiply-defined labels, 0 overfull hboxes.

Scientifically, three things are stronger than the paper lets on and should be
protected in revision: Table 9 + Table 10 as a matched pair (a uniform test that
recovers β Pic at 10–59σ and a sensitive test that recovers it at 6–9.5σ, with
*nothing* at the star in any of the four unattributed events) is decisive evidence
and reads that way; §5.3.2's pseudo-star result is a genuine methodological
contribution that will outlive this survey; and naming the ×0.48–1.35 transfer
uncertainty "the largest term in the budget by a factor of several" is the kind of
honesty most papers bury.

---

## Part E — verdict

**Submittable after the top 25 items, not before.** The science is sound, the
catalogue reconciles with the headline numbers to the last digit, the build is
clean, and the argument is better than most of its comparators. But the paper
currently contains:

- **one statistical impossibility in print** (R5, a median outside its own
  interval);
- **one arithmetic contradiction between two floats on the same page** (R6);
- **one appendix subsection and one table describing a superseded candidate list**
  (R2);
- **four surviving singular-where-plural sentences about the headline result**
  (R3);
- **one hand-typed ratio that is 28 per cent wrong** (R4);
- **one abstract comparison that a referee will read as cherry-picking** (R1);
- and **three renderings of `p =< 0.01`** (R10).

Any one of those would draw a referee's comment. Together they would cost a
revision cycle, and R1 and R2 would cost credibility, because both look like
exactly what the paper argues against: a number chosen after the fact, and an
analysis that did not follow the data.

**Time estimate.** R10, R13, R14, R16, R17, R18, R19, R24, R29, R30, R34, R36,
R43, R44 are one-line edits — an hour in total. R1, R3, R11, R12, R15, R21, R23
are half a day. R2 is either a deletion (ten minutes, and my recommendation) or a
regeneration (half a day). R5, R6, R7, R8, R9, R20 need a generator change each.
R25 is not editorial work but author action and is the true blocker.

**What I would accept as-is.** Everything in Part D. The structure, the section
order, the length, the figure set, the two-glossary arrangement if R26's claim
sentence goes, Appendix B, Appendix D, Appendix E, and every argument in §5.3,
§5.3.1 and §5.3.2 — which should be revised for the items above and for nothing
else.

**One structural recommendation, and it is the same one round 4 made.** Every
MAJOR above except R5, R21, R22, R23, R24 and R25 is a number that exists twice:
twice as a macro and a literal (R4, R13, R14, R17), twice in a table and the text
(R9, R12, R20, R42), twice under one symbol (R6, R31), twice at two vintages (R2,
R11), or twice as two estimators presented as one (R1). The project's answer to
this — `reproduce_from_catalogue_v385.py` — guards 36 quantities and none of the
ones above. **Before the next build, add a prose-literal sweep**: extract every
numeric token in the `.tex` body that is not inside `\newcommand`, not a citation
year and not a float placement, and fail the build on any exact match to a current
macro value (it should have been a macro) or to any value in a *previous*
version's macro set (it is stale). R4, R13, R14, R17, R43 and the "416" of R11 all
die there, and so would the next five.

---

*Report prepared by an independent reviewer pass, round 5, v3.85, 2026-09-21. No
manuscript, product, macro or generator file was modified;
`reproduce_from_catalogue_v385.py` was executed only on a sandbox copy in
`/tmp`, so `survey_numbers_round39.tex` is untouched.*
