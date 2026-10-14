# NeurMito-DT Similar-Paper Search and Figure/Structure Guide

Date: 2026-08-22

Scope: papers relevant to neuronal mitochondrial energy metabolism, ODE/kinetic models, ROS-ATP-membrane-potential dynamics, bistability and critical transitions, spatial mitochondrial models, hybrid mechanistic-ML models, and computational manuscript figure organization.

## Highest-priority biological/mechanistic references

### 1. Berndt et al. (2012)

Title: Kinetic Modeling of the Mitochondrial Energy Metabolism of Neuronal Cells: The Impact of Reduced alpha-Ketoglutarate Dehydrogenase Activities on ATP Production and Generation of Reactive Oxygen Species

Journal: International Journal of Cell Biology

DOI: 10.1155/2012/757594

Why it is close: neuronal mitochondrial kinetic model; OXPHOS, ATP, membrane potential, ROS and disease-relevant enzyme perturbation.

Structure to study:

- model architecture and state variables first;
- mechanism-specific perturbation next;
- time-course and steady-state consequences;
- ROS/ATP interpretation as the biological result;
- sensitivity or parameter-dependence as supporting evidence.

Figure lesson for NeurMito-DT: use a compact model schematic, followed by perturbation-response curves and a parameter-response summary. Avoid making the architecture figure carry too many biological claims.

Sources: https://doi.org/10.1155/2012/757594 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC3376505/

### 2. Berndt, Kann and Holzhutter (2015)

Title: Physiology-Based Kinetic Modeling of Neuronal Energy Metabolism Unravels the Molecular Basis of NAD(P)H Fluorescence Transients

Journal: Journal of Cerebral Blood Flow & Metabolism

DOI: 10.1038/jcbfm.2015.70

Why it is close: detailed neuronal energy metabolism model with OXPHOS, TCA, mitochondrial membrane potential and calcium exchange, connected to experimentally observed dynamic readouts.

Structure to study:

- define the observable and why it is mechanistically ambiguous;
- introduce one reusable model rather than many unrelated models;
- test the same model under multiple stimulus/nutrient conditions;
- compare simulated and measured trajectories;
- discuss what the model can and cannot identify.

Figure lesson for NeurMito-DT: a strong results sequence is model/observable definition -> representative time courses -> condition comparison -> mechanistic decomposition -> limitations.

Sources: https://doi.org/10.1038/jcbfm.2015.70 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC4640339/

### 3. Selivanov et al. (2021)

Title: Unveiling a key role of oxaloacetate-glutamate interaction in regulation of respiration and ROS generation in nonsynaptic brain mitochondria using a kinetic model

Journal: PLOS ONE

DOI: 10.1371/journal.pone.0255164

Why it is close: brain mitochondria, kinetic modeling, respiration and ROS, with a focused mechanistic question rather than a broad platform claim.

Figure lesson for NeurMito-DT: make each figure answer one mechanistic question. Use a clear perturbation axis, explicit endpoint definitions, and a final panel that states the predicted mechanism rather than only displaying model output.

Source: https://doi.org/10.1371/journal.pone.0255164

### 4. Selivanov et al. (2009)

Title: Bistability of Mitochondrial Respiration Underlies Paradoxical Reactive Oxygen Species Generation Induced by Anoxia

Journal: PLOS Computational Biology

DOI: 10.1371/journal.pcbi.1000619

Why it is close: mitochondrial respiration, ROS, hypoxia/anoxia-reoxygenation and bistable state transitions.

Figure lesson for NeurMito-DT Figure 3:

- panel A: reaction/network mechanism;
- panel B: steady-state or bifurcation structure;
- panel C: time-dependent switching or hysteresis;
- panel D: perturbation/recovery experiment or simulation;
- final panel: parameter sensitivity and boundary robustness.

The paper explicitly connects the model-predicted high-ROS state to the transition history, which is a useful template for explaining hysteresis without overclaiming universality.

Source: https://doi.org/10.1371/journal.pcbi.1000619

### 5. Leung et al. (2021)

Title: Systems modeling predicts that mitochondria ER contact sites regulate the postsynaptic energy landscape

Journal: npj Systems Biology and Applications

DOI: 10.1038/s41540-021-00185-7

Why it is close: neuronal compartmentalized model, calcium and ATP dynamics, spatial geometry and organelle-level heterogeneity.

Figure lesson for NeurMito-DT Figure 5:

- Figure 1: model architecture, compartments, fluxes and geometry;
- Figure 2: spatial maps plus temporal traces;
- Figure 3: ATP, calcium, membrane-potential outputs and area-under-curve summaries;
- supplementary figures: parameter/diffusion sensitivity.

This is the best visual template found for showing a spatial model without making the spatial schematic and the quantitative result compete for attention.

Source: https://doi.org/10.1038/s41540-021-00185-7

### 6. Park, Lee and Choi (2011)

Title: Mitochondrial Network Determines Intracellular ROS Dynamics and Sensitivity to Oxidative Stress through Switching Inter-Mitochondrial Messengers

Journal: PLOS ONE

DOI: 10.1371/journal.pone.0023211

Why it is close: mitochondrial network organization, ROS propagation and oxidative-stress sensitivity using an agent-based model.

Figure lesson for NeurMito-DT Figure 5: pair spatial organization with propagation speed, representative trajectories and a sensitivity/threshold panel. The spatial image should be directly tied to a measurable model output.

Source: https://doi.org/10.1371/journal.pone.0023211

## Hybrid mechanistic-ML and model-uncertainty references

### 7. Faure et al. (2023)

Title: A neural-mechanistic hybrid approach improving the predictive power of genome-scale metabolic models

Journal: Nature Communications 14, 4669

DOI: 10.1038/s41467-023-40380-0

Why it is close: mechanistic layer plus trainable neural layer, custom loss with mechanistic constraints, controlled benchmarks and experimental-data evaluation.

Figure lesson for NeurMito-DT Figure 2:

- Figure 1 should explain the computational graph and where constraints enter;
- Figure 2 should be a controlled benchmark with train/validation/test separation;
- later figures should separate synthetic benchmark performance from experimental-data performance;
- show uncertainty/error bars and cross-validation details in captions.

Source: https://doi.org/10.1038/s41467-023-40380-0

### 8. Wang et al. (2019)

Title: Massive computational acceleration by using neural networks to emulate mechanism-based biological models

Journal: Nature Communications 10, 4354

DOI: 10.1038/s41467-019-12342-y

Why it is close: mechanistic simulations generate training data; neural models emulate or accelerate parameter-space exploration.

Figure lesson for NeurMito-DT Figure 2:

- clearly separate mechanistic data generation, neural training and held-out verification;
- use predicted-versus-simulated plots, representative trajectory overlays and error-vs-training-size curves;
- make acceleration a secondary result unless it is rigorously benchmarked.

Source: https://doi.org/10.1038/s41467-019-12342-y

### 9. Dou et al. (2026)

Title: Inferring stochastic dynamics by biophysical Neural ODE using single-cell transcriptomics

Journal: Nature Communications 17, 6901

DOI: 10.1038/s41467-026-73257-z

Why it is close: current Nature Communications example combining biophysical constraints, Neural ODE-style dynamics, state landscapes, bifurcation analysis and multi-stage validation.

Figure lesson for NeurMito-DT:

- overview figure should include data input, prior/mechanistic constraints, neural components, loss and downstream analyses;
- benchmark figures should use synthetic ground truth before biological applications;
- state-space/landscape figures should show attractors, flows and decision boundaries together;
- every biological application should be preceded by a method-validation figure.

Source: https://doi.org/10.1038/s41467-026-73257-z

### 10. Linden-Santangeli et al. (2025)

Title: Increasing certainty in systems biology models using Bayesian multimodel inference

Journal: Nature Communications 16, 7416

DOI: 10.1038/s41467-025-62415-4

Why it is close: ODE-based intracellular systems biology, model uncertainty, robustness to model-set changes and measurement uncertainty.

Figure lesson for NeurMito-DT: distinguish parameter uncertainty, model-form uncertainty, source heterogeneity and validation uncertainty. A confidence or uncertainty panel should not be labeled as posterior calibration unless the sampling and likelihood are real and reproducible.

Source: https://doi.org/10.1038/s41467-025-62415-4

## Early-warning and critical-transition references

### 11. Dakos et al. (2012)

Title: Methods for Detecting Early Warnings of Critical Transitions in Time Series Illustrated Using Simulated Ecological Data

Why it is close: early-warning indicators, critical slowing down, variance/autocorrelation and simulated-transition protocols.

Figure lesson for NeurMito-DT Figure 4:

- define the transition label and event time before computing indicators;
- show raw trajectories and indicator trajectories together;
- use train/validation/test separation for threshold selection;
- report negative controls and permutation tests;
- do not infer predictive gain from a descriptive trend alone.

Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC3398887/

## Digital-twin framing references

### 12. Challenges and opportunities for digital twins in precision medicine (2025)

Journal: npj Digital Medicine

Use: terminology, scope and limitations of calling a biological model a digital twin.

Figure lesson for the NeurMito-DT introduction and graphical abstract: distinguish a mechanistic in-silico model, a patient-specific digital twin and a continuously data-updated digital twin. The current NeurMito-DT manuscript is best described as a computational or prototype digital-twin framework unless individualized data assimilation is added.

Source: https://www.nature.com/articles/s41746-024-01402-3

## Recommended structure for NeurMito-DT

### Main manuscript order

1. Biological problem and unmet need: neuronal mitochondrial stress is dynamic, nonlinear and heterogeneous.
2. Framework overview: 25-state mechanistic core, stress operators, observable layer, hybrid extension and validation boundaries.
3. Figure 1: source/provenance and relative observable contract; do not present absolute calibration or MCMC as completed evidence.
4. Figure 2: controlled hybrid misspecification benchmark; report architecture, data split, loss, seeds and held-out error.
5. Figure 3: stress-combination response, transition boundary, bistability/hysteresis and robustness.
6. Figure 4: endpoint-labelled EWS diagnostics with locked thresholds and negative controls.
7. Figure 5: spatial or position-indexed heterogeneity as a hypothesis map, with solver/geometry limitations explicit.
8. Figure 6: disease-axis mechanism maps as hypothesis generation, not efficacy or patient-outcome prediction.
9. Discussion: supported claims, withheld claims, model uncertainty, transfer limits and experimental tests.

### Figure design rules extracted from the references

- Keep one dominant question per figure.
- Use panel A for architecture or protocol only when the remaining panels answer the same question.
- Put raw trajectories before derived metrics.
- Pair phase diagrams with representative time courses and a robustness panel.
- Pair spatial maps with a quantitative summary tied to the spatial variable.
- Use predicted-vs-reference plots, error distributions and held-out evaluation for ML/hybrid figures.
- Put uncertainty and negative controls in the main figure when they determine claim strength.
- Keep captions self-contained: input, model, endpoint, comparison, uncertainty and interpretation boundary.
- Prefer color-blind-safe palettes and consistent state colors across Figures 1-6.

## Priority reading list

1. Berndt et al. 2012 - closest neuronal mitochondrial ODE scaffold.
2. Selivanov et al. 2009 - best bistability/ROS transition template.
3. Leung et al. 2021 - best neuronal spatial-compartment figure template.
4. Faure et al. 2023 - best hybrid mechanistic-ML architecture and benchmark template.
5. Dou et al. 2026 - current Nature Communications Neural ODE structure.
6. Dakos et al. 2012 - EWS protocol and negative-control discipline.
7. Linden-Santangeli et al. 2025 - uncertainty and model-form qualification.

## Important use restriction

These papers should be used for structural and visual inspiration, not copied wording, panel layouts or graphical assets. The NeurMito-DT manuscript should preserve its own claim boundaries and cite the original source for any biological or methodological statement.
