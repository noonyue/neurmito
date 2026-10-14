# R030A Seahorse/OCR primary-source candidate screen

**Screen date:** 2026-08-09  
**Database:** PubMed via NCBI E-utilities  
**Purpose:** identify primary-source candidates for the provisional Figure 1
neuronal OCR inputs. This is a screening record, not a data-extraction record.

## Eligibility rule

A paper can enter the Figure 1 calibration ledger only when all of the following
are recoverable from the primary source:

1. neuronal preparation, species, and culture/differentiation state;
2. experimental condition suitable for the declared baseline scenario;
3. basal, maximal, ATP-linked, and proton-leak OCR values or a reproducible
   extraction path;
4. OCR normalization unit and sample size/replicate definition;
5. a DOI/PMID and a stored figure/table or digitization record.

## Exact repository-citation searches

The following PubMed queries returned **zero** records matching the claimed
author/year/journal combinations:

- `Cheng[Author] AND 2012[DP] AND ASN Neuro[Journal]`
- `Ferreira[Author] AND 2015[DP] AND Biochimica et Biophysica Acta[Journal] AND hippocampal`
- `Requejo-Aguilar[Author] AND 2014[DP] AND Scientific Reports[Journal]`
- `Connolly[Author] AND 2018[DP] AND Neurotoxicology[Journal] AND SH-SY5Y`

This confirms that the original direct-source records cannot be recovered using
their current citation strings.

## Screened PubMed candidates

| PMID | Candidate | Relevance | Eligibility disposition |
|---:|---|---|---|
| 31931869 | Sotolongo et al., *Alzheimer's Research & Therapy* (2020), DOI 10.1186/s13195-019-0578-9 | Open full text documents a Seahorse XFe24 Mito Stress workflow in DIV7 primary rat cortical neurons and SH-SY5Y cells, including basal, maximal, proton-leak, and ATP-linked OCR calculations. | Suitable as a protocol/relative-response reference. It normalizes to Janus Green total-cell staining rather than the current pmol/min/μg protein scenario unit, so it cannot enter the absolute calibration table without a source-specific unit bridge. |
| 28237843 | Aldana et al., *Neurochemistry International* (2017), DOI 10.1016/j.neuint.2017.02.010 | Includes Seahorse assessment and primary mouse cortex/cerebellum comparator cultures. | Methodologically relevant; not a direct replacement for the stated rat cortical scenario. Needs full-text figure/unit audit before any extraction. |
| 28110213 | Sun et al., *Redox Biology* (2017), DOI 10.1016/j.redox.2016.12.029 | Seahorse metrics in a mouse hippocampal neuronal cell-line OGD/R model. | Not a healthy primary hippocampal baseline; cannot replace the current target. |
| 25016198 | Subramaniam et al., *Neurobiology of Disease* (2014), DOI 10.1016/j.nbd.2014.06.017 | Seahorse respiratory defects in alpha-synuclein mouse brain regions. | Regional tissue/transgenic comparison, not primary dopaminergic-culture OCR. |
| 35025051 | Pandey et al., *Molecular Neurobiology* (2022), DOI 10.1007/s12035-021-02667-5 | RA+BDNF differentiated SH-SY5Y Seahorse XFp experiment. | Closest procedural match for the SH-SY5Y scenario, but the abstract does not provide recoverable absolute Mito Stress values or the declared normalization. Full-text extraction still required. |
| 32165258 | Jaber et al., *Experimental Neurology* (2020), DOI 10.1016/j.expneurol.2020.113282 | Primary cortical neuron respirometry and Mito Stress Test limitations. | Method/protocol source only; not a neuron-type calibration table. |

## Full-text check of the strongest candidate

The PMC full text for PMID 31931869 confirms:

- XFe24 assay with sequential oligomycin, FCCP, and rotenone/antimycin;
- DIV7 primary rat cortical neurons and SH-SY5Y cells;
- basal, maximal, proton-leak, and ATP-production calculations;
- at least three to six independent experiments performed in triplicate.

However, its endpoint values are normalized to Janus Green whole-cell staining.
No protein-per-cell measurement or conversion factor is provided that would make
those values interchangeable with the repository's `pmol/min/μg protein`
scenario unit. It is therefore retained as a **protocol/relative-response
candidate**, not an absolute calibration source.

## R030A decision

No candidate passes the calibration eligibility rule yet. The Figure 1 inputs
remain **provisional scenarios**, and no MCMC or neuron-specific calibration may
be reinstated.

## R030B recovery protocol

For a future candidate that passes the biological-preparation screen:

1. archive the source PDF/PMC figure and citation metadata;
2. record assay plate normalization, inhibitor concentrations, replicates, and
   units;
3. digitize only the reported baseline condition with a saved project file;
4. retain the raw digitized points and a unit-conversion worksheet;
5. register the entry in a source ledger before it enters calibration;
6. rerun Figure 1 with only verified entries and report the remaining types as
   scenario-only.

## R030B unit-compatibility screen

Additional PubMed and Europe PMC full-text searches for the joint requirement
of `Seahorse`, neuronal preparation, and `pmol/min/μg` (or
`pmol/min/mg protein`) returned no qualifying public record. This negative
result does not mean such data do not exist; it means they have not been
identified in a form that can be source-audited and directly substituted into
the repository's absolute-unit OCR table.

**R030B decision as of this screen:** keep absolute calibration withheld. Do
not create a protein-normalization conversion from a cell-count, DNA-stain, or
other incompatible source without a source-specific measured bridge.
