# BUILD RULE — read before you build. Binding on every agent in this tree.

**2026-10-04 08:3x.** Two agents built into the same derived paths this morning. For about three
minutes one of them measured a PDF it had not built — it carried that agent's new abstract with
every freshly-added macro blank. Only derived files were involved, so nothing was lost, but a
measurement taken in that window is simply wrong, and **every agent working in this tree is exposed
to it.**

## The rule

1. **Never build the shared job name.** `technosignatures_40pc_v4.10.{pdf,aux,log,out}` are now
   **read-only**, so a stray build fails loudly instead of corrupting someone's measurement
   silently. A failing build is a far better outcome than a wrong number.
2. **Build under your own job name**, into your own output directory:
   `pdflatex -jobname=<agent>-probe -output-directory=build_<agent> ...`
   Create `build_<agent>/` yourself; it is yours alone.
3. **Never symlink the shared artefacts into a scratch tree.** That is how the collision happened:
   the symlink made two builds write one path.
4. **Measure in column points, not whole pages.** The document stayed at 60 pp through a complete
   rewrite of §1 and a 27-word cut to the abstract. A page is two columns of 693.8 pt; a full-width
   float is charged at twice its height. `referee_r9/absintro/measure_absintro.py` does this
   correctly — use it rather than `pdfinfo`. ★ **Whole-page counting here is a check that cannot
   fail**, which is the defect family this project has found fourteen times.
5. **A consequence you must act on**: because the column filler absorbs small differences, cutting
   sentences does not pay. If a section must give up space, it gives up **a whole paragraph or a
   float** — not prose trimmed line by line.

## Integration

The read-only flags come off at integration, when exactly one agent builds the shared job. Until
then, if you need the shared PDF for comparison, read `../v4.09/` — which is also read-only, and is
the published reference.
