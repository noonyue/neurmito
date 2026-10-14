# R071 Nature Figure Contract

**Backend:** Python 3.8 / Matplotlib only.  
**Target:** Nature-family double-column figures.  
**Final canvas:** 183 mm wide, no more than 170 mm high.  
**Exports:** editable SVG, editable-text PDF, 600 dpi TIFF, 600 dpi PNG.

## Global visual contract

- Arial/Helvetica sans-serif, 6.2 pt base text, 8 pt bold lowercase panel labels.
- White background; no decorative panel borders or gridlines.
- Top/right axes spines removed; axes and ticks use 0.45–0.6 pt strokes.
- One muted semantic palette across all six figures: blue for the principal model/evidence, grey for baselines, amber for stress or caution, teal for retained/physiological states, muted red-violet for collapse or excluded states.
- Sequential maps use single-hue perceptually ordered palettes; signed residuals use a diverging map centred on zero.
- Text remains editable in SVG/PDF. Raster exports are 600 dpi.
- Figure 1 uses nine quantitative panels (a–i); its former workflow is stated in the text, the source ledger is Supplementary Table S2, and the former boundary panel is omitted. Figure 2 uses nine panels (a–i); its former architecture and protocol panels are stated in the text, and the former boundary panel is omitted. Figure 3 uses nine quantitative panels (a-i); its stress-operator schematic and claim boundary are stated in the text. Figures 4 and 5 use a–j, and Figure 6 uses a–i.

## Figure 1

**Conclusion:** source-local OCR ratios support conditional reserve mapping but not pooled absolute calibration.  
**Evidence chain:** endpoint availability -> retained/withheld endpoints -> ratio intervals -> ratio relationship -> restricted losses/parameter regions -> claim gates and group summary. The provenance workflow is described in the manuscript and the source ledger is Supplementary Table S2.  
**Archetype:** quantitative grid.  
**Review risk:** source-local values could be mistaken for new assays or external validation; the manuscript wording and supplementary source ledger must remain explicit.

## Figure 2

**Conclusion:** a hybrid residual improves recovery in a controlled hidden-residual benchmark without establishing biological generalization.  
**Evidence chain:** architecture -> locked split -> held-out trajectories -> aggregate/seed errors -> residual correction -> stress-dependent failure pattern -> paired errors -> improvement summary.  
**Archetype:** schematic-led model benchmark.  
**Review risk:** synthetic targets must not be labelled as experimental ground truth; seed count and holdout range remain visible.

## Figure 3

Figure 3 contains nine external panels (a-i). Panel f is a combined synergy-residual composite with vertically stacked DPsi and ATP maps, each retaining its own unit and colour scale.

**Conclusion:** combined computational stress operators create a narrow nonlinear endpoint transition that persists across tested robustness variants.  
**Evidence chain:** endpoint class -> membrane-potential and ATP surfaces -> cross-sections/transition band -> signed synergy residuals -> ablation/robustness summaries. The stress-operator definition and claim boundary are stated in the manuscript.  
**Archetype:** quantitative phase-map grid.  
**Review risk:** axes are computational operators, not measured exposure thresholds; colormaps must not imply unsupported precision.

## Figure 4

**Conclusion:** EWS features contain descriptive signal in the locked simulation, but the prespecified baseline remains stronger.  
**Evidence chain:** representative trajectory -> rolling variance/autocorrelation -> discrimination/calibration/uncertainty/lead time -> permutation and time-shuffle controls -> probability separation. The locked cohort design and claim boundary are stated in the manuscript.  
**Archetype:** asymmetric locked-evaluation quantitative grid (3 + 4 + 3).  
**Review risk:** no prospective, biological, or clinical validation claim; the baseline comparison must remain prominent.

## Figure 5

**Conclusion:** a position-indexed computational scenario predicts increasing distal vulnerability under stress.  
**Evidence chain:** health index -> supply/demand/ROS proxies -> threshold -> trajectories and distal/proximal vulnerability -> spatial profiles/area summary -> demand-health relationship. The spatial coordinate and scenario definition are described in the manuscript rather than shown as a panel.  
**Archetype:** spatial quantitative grid.  
**Review risk:** deterministic scenario outputs are not imaging data or a validated axonal transport solver.

## Figure 6

**Conclusion:** disease-like stress weights organize mechanistic hypotheses across shared mitochondrial axes without predicting patients or treatment effects.  
**Evidence chain:** shared-state schematic -> disease-mechanism matrix -> trajectories/projections -> cross-context summaries -> deviations/profile/checklist/ranges -> reproducibility workflow.  
**Archetype:** hypothesis-map quantitative grid.  
**Review risk:** weights are scenario definitions rather than patient-derived estimates; literature consistency is not external validation.

## Acceptance checks

- Figure 1-3 panels a-i, Figure 4 panels a-j, Figure 5 panels a-j, and Figure 6 panels a-l are present and visible.
- No text, ticks, legends, or colorbars are clipped or overlapping at 183 mm width.
- PNG/TIFF dimensions correspond to 600 dpi export; SVG contains text nodes; PDF fonts are embedded.
- Figure outputs are nonblank and visibly distinct.
- All numeric panels remain traceable to the existing audited run files or deterministic scenario code.
- Original R071 figures remain untouched; redrawn outputs are written to `figures/r071_nature/` and then copied into the submission package.
