# Virtual referee round 2 — on v3.64 (32 pp)

Reports below come from reading the typeset PDF, extracting the text back out
of every figure, and auditing the tables against `per_target_results_v3.64.csv`.

---

## Referee D — figures, and whether they say what the text says

**D1. Figure 8's right-hand axis is wrong in the way the paper spends §4 warning
against.** The axis reads "effective threshold $P_{\rm eff}=2.29\,P_{\rm trig}$
(W)". I extracted the text from `sensitivity_2d.pdf` to be sure. But
$P_{\rm eff,total}$ is a *per-window* catalogue column running ×1.33 to ×3.98,
and 2.29 is only its median. A reader who reads a specific window's effective
threshold off that axis can be wrong by 40 per cent, and the paper has just
told them $P_{\rm eff}$ is the number to use. Either plot the per-window
`eirp_eff_total_W` or label the axis as the median scaling that it is.

**D2. Figure 2 has not been renamed.** The funnel still reads "126
drift-resolved, 317 spectral-excess", and Figure 8's legend still says
"Class A: drift-search". §4.1 now says the classes are labelled by
channelisation and that "drift-resolved" is used only where the physical
criterion agrees. The figures were not regenerated with the text. This is the
same defect class as the text-side inconsistency fixed in the previous round —
it simply lives in `make_fig_funnel.py` and `make_figures_v328.py` instead of
the `.tex`.

**D3. Five figures are built but never included** (`completeness.pdf`,
`completeness_sensitivity.pdf`, `noise_qa.pdf`, `occurrence_duty.pdf`,
`selection.pdf`, `symcdf.pdf`). `occurrence_duty.pdf` in particular illustrates
the occurrence ladder that was withdrawn from Appendix I this cycle, so it is
now orphaned. Either drop them from the build or say in the data-availability
statement that the release carries figures the paper does not print.

**D4. `noise_qa.pdf` and `control_diagnostics.pdf` disagree on Band 6.** The
first says "Band 6 (220 pass)", the second "B6 (216)". 220 − 216 = 4, which is
exactly the four withheld ε Eri Band 6 windows, so the two are consistent once
you know that — but one of them calls windows "pass" that the paper withholds.
Since `noise_qa.pdf` is not printed (D3) this is invisible to a reader, which is
worse, not better: the released figure contradicts the released catalogue.

**D5. Figure 5's caption promises a per-window quantity the axis does not
carry** — see D1; check every figure caption against the axis text rather than
against the intention.

---

## Referee E — the numbers, audited

**E1. I could reproduce Table 10 exactly and I want to record that.** Every
ν in the "both statistics" table is the window centre computed from
`flo_GHz`/`fhi_GHz` in the released catalogue (115.2605, 230.5164, 230.7305,
230.5384, 217.0183, 345.1152, 345.1377), and every $T_\star$ matches
`star_snr`. The caption's warning that ν is the centre and not the crossing is
load-bearing — for CP−72 2713 the two differ by 0.85 GHz — and it is correct.
No action; I mention it because a reader should know the audit was possible.

**E2. Table 5 and the catalogue agree on all four flagged windows**, including
the dispositions verbatim. Also no action.

**E3. The four local-to-global scale ratios are still literals.** Round 1 added
"quoted from the stage-1 diagnostic products and not regenerable from the
release". That is honest but unsatisfying: it tells the reader that four numbers
in a paper whose selling point is reproducibility cannot be reproduced. Either
ship the four spectra needed, or drop the sentence and rest the argument on
$R_\sigma$, which *is* reproducible and says the same thing.

**E4. β Pictoris Band 6's window is 54 MHz wide** (230.4894–230.5433) against
~1.7 GHz for the others. That is not an error — it is a narrow spectral-line
tuning — but the paper never says it, and it matters: the window that carries
the strongest positive control is also the one whose bandwidth is smallest, so
its trials factor is not comparable with the rest. One clause.

**E5. The expected-versus-observed arithmetic should be stated once as a
probability, not twice as a ratio.** "1.2 expected, one observed" appears in
§5.4, §5.3 and §6.2. Give $P(\geq1)$ once and cross-reference it.

---

## Referee F — argument and exposition

**F1. The primary-beam gap argument added in round 1 is the strongest paragraph
in §4.3 and it is buried mid-paragraph.** "Retained windows reach 0.46 θ_PB,
the next window out sits at 0.62, nothing in between" is the sentence that
retires the referee objection. Lead with it.

**F2. The paper now has two different justifications for withholding ε Eri and
presents them as one.** The response floor is a rule about inferred-flux error;
the sidelobe transition is a statement about the beam model's validity. They
coincide here, which is worth saying explicitly — "the two criteria select the
same four windows" — rather than eliding them into a single clause.

**F3. The abstract is 1846 of 1920 characters and spends its last sentence on
scope.** That is the right last sentence. But the sentence before it
("Out of sample the control ensemble proves not exchangeable…") is now the only
place in the abstract where the repair appears, and it does not say the
dispositions are unchanged by it until the final clause. Tighten.

**F4. §5.4 says the debit that centres the held-out distribution is 0.32σ and
the conservative one is 0.15σ; Table 8 gives four "survives" values. A reader
cannot tell from the table which of the two debits each column assumes.** The
caption says both but not which is plotted. State the convention in the column
head.

**F5. Still 32 pages.** I note that both of my co-referees added requests. I
would accept 32 pages if the authors state in the cover letter why: a 31-page
target is not a journal requirement here, it is the authors' own budget.
