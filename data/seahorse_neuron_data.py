"""Provisional Seahorse-style neuronal OCR scenarios.

The numeric values are retained to drive computational scenarios only.  No entry
currently has a source-audited primary figure/table, normalization record, and
digitization log sufficient for experimental calibration.  See
``sources/R026_PUBMED_AUDIT_20260809.md`` and
``sources/R030_SEAHORSE_CANDIDATE_SCREEN_20260809.md``.
"""

# ── Summary Table for Provisional Scenario Inputs ─────────────────────────────
# Units: pmol/min/μg protein (unless noted)
# Basal, Maximal, Spare Capacity, ATP-linked, Proton Leak

SEAHORSE_DATA = {
    'cortical': {
        'source': 'Cheng et al., 2012, ASN Neuro; Rat primary cortical, DIV 7-10',
        'basal_ocr': 100.0,      # pmol/min/μg (range 80-120)
        'maximal_ocr': 240.0,    # pmol/min/μg (range 200-280)
        'spare_capacity': 140.0, # pmol/min/μg (range 100-160)
        'atp_linked': 65.0,      # pmol/min/μg (range 50-80)
        'proton_leak': 30.0,     # pmol/min/μg (range 20-40)
        'n': 12,                 # sample size
        'div': 10,               # days in vitro
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Numeric values retained as provisional model inputs; cited source/PMID audit failed.',
    },

    'hippocampal': {
        'source': 'Ferreira et al., 2015, BBA; Rat primary hippocampal, DIV 14',
        'basal_ocr': 98.0,
        'maximal_ocr': 225.0,
        'spare_capacity': 130.0,
        'atp_linked': 65.0,
        'proton_leak': 32.0,
        'n': 6,
        'div': 14,
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Numeric values retained as provisional model inputs; cited source/PMID audit failed.',
    },

    'dopaminergic': {
        'source': 'Requejo-Aguilar et al., 2014, Sci Rep; Mouse primary midbrain DA, DIV 7',
        'basal_ocr': 70.0,
        'maximal_ocr': 145.0,
        'spare_capacity': 75.0,
        'atp_linked': 42.0,
        'proton_leak': 25.0,
        'n': 4,
        'div': 7,
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Numeric values retained as provisional model inputs; cited source/PMID audit failed.',
    },

    'motor': {
        'source': 'Estimated from spinal cord motor neuron studies (Vandoorne et al., 2018, Cell Rep)',
        'basal_ocr': 95.0,
        'maximal_ocr': 230.0,
        'spare_capacity': 135.0,
        'atp_linked': 63.0,
        'proton_leak': 28.0,
        'n': 8,
        'div': 10,
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Provisional scenario input; no source-audited primary OCR record is available.',
    },

    'GABAergic': {
        'source': 'Estimated from interneuron studies (Kann et al., 2011, J Neurosci)',
        'basal_ocr': 85.0,
        'maximal_ocr': 200.0,
        'spare_capacity': 115.0,
        'atp_linked': 58.0,
        'proton_leak': 27.0,
        'n': 6,
        'div': 12,
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Provisional scenario input; no source-audited primary OCR record is available.',
    },

    'cholinergic': {
        'source': 'Estimated from basal forebrain cholinergic neuron studies',
        'basal_ocr': 78.0,
        'maximal_ocr': 170.0,
        'spare_capacity': 92.0,
        'atp_linked': 50.0,
        'proton_leak': 26.0,
        'n': 5,
        'div': 10,
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Provisional scenario input; no source-audited primary OCR record is available.',
    },

    'cerebellar': {
        'source': 'Estimated from cerebellar granule cell studies (Jekabsons & Nicholls, 2004, J Biol Chem)',
        'basal_ocr': 105.0,
        'maximal_ocr': 250.0,
        'spare_capacity': 145.0,
        'atp_linked': 70.0,
        'proton_leak': 32.0,
        'n': 8,
        'div': 8,
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Provisional scenario input; no source-audited primary OCR record is available.',
    },

    'sensory': {
        'source': 'Estimated from DRG sensory neuron studies',
        'basal_ocr': 88.0,
        'maximal_ocr': 210.0,
        'spare_capacity': 122.0,
        'atp_linked': 60.0,
        'proton_leak': 28.0,
        'n': 6,
        'div': 10,
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Provisional scenario input; no source-audited primary OCR record is available.',
    },

    'SH-SY5Y': {
        'source': 'Connolly et al., 2018, Neurotoxicology; SH-SY5Y RA+BDNF differentiated',
        'basal_ocr': 200.0,      # pmol/min/μg protein
        'maximal_ocr': 450.0,
        'spare_capacity': 250.0,
        'atp_linked': 135.0,
        'proton_leak': 62.0,
        'n': 5,
        'div': 14,
        'data_type': 'estimated',
        'provenance_status': 'unverified_source_provenance',
        'note': 'Provisional scenario input; cited source/PMID audit failed and the cell-line normalization remains unverified.',
    },
}

# Additional provisional reference scenarios (not source-audited)
ADDITIONAL_LITERATURE = {
    'mouse_cortical': {
        'source': 'Yin et al., 2016, J Alzheimer\'s Dis; Mouse cortical, DIV 10',
        'basal_ocr': 95.0,
        'maximal_ocr': 220.0,
        'spare_capacity': 125.0,
        'atp_linked': 65.0,
        'proton_leak': 30.0,
        'n': 8,
        'div': 10,
    },

    'mouse_cortical_bhatt': {
        'source': 'Bhatt et al., 2020, Cell Death Dis; Mouse cortical, DIV 7',
        'basal_ocr': 80.0,
        'maximal_ocr': 205.0,
        'spare_capacity': 120.0,
        'atp_linked': 55.0,
        'proton_leak': 25.0,
        'n': 6,
        'div': 7,
    },

    'shsy5y_undiff': {
        'source': 'Giordano et al., 2012, Toxicol Sci; SH-SY5Y undifferentiated',
        'basal_ocr': 150.0,      # pmol/min/10^6 cells (different unit!)
        'maximal_ocr': 350.0,
        'spare_capacity': 200.0,
        'atp_linked': 100.0,
        'proton_leak': 50.0,
        'n': 4,
        'unit_note': 'per 10^6 cells, not per μg protein',
    },

    'mouse_hippocampal': {
        'source': 'Yao et al., 2011, BBA; Mouse hippocampal neurons',
        'basal_ocr': 90.0,
        'maximal_ocr': 210.0,
        'spare_capacity': 120.0,
        'atp_linked': 60.0,
        'proton_leak': 30.0,
        'n': 5,
        'div': 12,
    },
}

# Neuron type list for iteration
NEURON_TYPES = list(SEAHORSE_DATA.keys())

# ── Unverified Citation Leads (not direct references) ─────────────────────────

KEY_PAPERS = [
    'Cheng et al. (2012) ASN Neuro — cortical baseline',
    'Giordano et al. (2012) Toxicol Sci — SH-SY5Y bioenergetics',
    'Requejo-Aguilar et al. (2014) Sci Rep — primary DA neurons',
    'Ferreira et al. (2015) BBA — hippocampal',
    'Yao et al. (2011) BBA — hippocampal/estrogen',
    'Yin et al. (2016) J Alzheimer\'s Dis — mouse cortical',
    'Bhatt et al. (2020) Cell Death Dis — mouse cortical',
    'Connolly et al. (2018) Neurotoxicology — SH-SY5Y differentiation',
]

# ── Notes on Data Quality and Limitations ─────────────────────────────────────

NOTES = """
Important caveats:

1. Unit normalization matters:
   - Most data: pmol/min/μg protein
   - SH-SY5Y undiff/diff (Giordano): pmol/min/10^6 cells
   - Need cell protein content (~100-200 μg/10^6 cells) to convert

2. FCCP concentration affects maximal OCR:
   - Typical range: 0.5-2 μM
   - Check each paper's protocol before using

3. DIV (days in vitro) matters:
   - Neurons mature over time in culture
   - DIV 7-14 is typical range
   - Bioenergetics may change with DIV

4. Species differences:
   - Rat vs mouse baseline OCR can differ 10-20%
   - Neuronal subtype (cortical, hippocampal, DA) has distinct profiles

5. These values come from literature up to 2025.
   Verify against primary sources before calibration.
"""

# ── Conversion Constants ───────────────────────────────────────────────────────

# To convert from ODE units (mM/s) to experimental OCR (pmol/min/μg):
# OCR_model = J_O2 * V_mito * (60 s/min) * (1e12 pmol/mol) / (protein_mass_μg)
# V_mito ≈ 0.1 μL/mg protein (mitochondrial volume per protein)
# This will be calibrated in Module 1, Step 4

# ── Helper function to extract provisional scenario inputs ────────────────────

def get_calibration_targets(neuron_type='mouse_cortical'):
    """
    Extract provisional OCR scenario inputs.

    Parameters
    ----------
    neuron_type : str
    Key from SEAHORSE_DATA. These values are not verified experimental targets.

    Returns
    -------
    dict with keys: basal_ocr, maximal_ocr, spare_capacity, atp_linked, proton_leak
    All values in pmol/min/μg protein
    """
    if neuron_type not in SEAHORSE_DATA:
        raise ValueError(f"Unknown neuron_type: {neuron_type}. Choose from: {list(SEAHORSE_DATA.keys())}")

    data = SEAHORSE_DATA[neuron_type]
    return {
        'basal_ocr': data['basal_ocr'],
        'maximal_ocr': data['maximal_ocr'],
        'spare_capacity': data['spare_capacity'],
        'atp_linked': data['atp_linked'],
        'proton_leak': data['proton_leak'],
        'source': data['source'],
    }


if __name__ == '__main__':
    # Print summary
    print("Seahorse Neuron OCR Data Summary")
    print("=" * 60)
    for nt, data in SEAHORSE_DATA.items():
        print(f"\n{nt}:")
        print(f"  Source: {data['source']}")
        print(f"  Basal OCR: {data['basal_ocr']} pmol/min/μg")
        print(f"  Maximal OCR: {data['maximal_ocr']} pmol/min/μg")
        print(f"  Spare Capacity: {data['spare_capacity']} pmol/min/μg")
        print(f"  ATP-linked: {data['atp_linked']} pmol/min/μg")
        print(f"  Proton Leak: {data['proton_leak']} pmol/min/μg")

    print("\n" + "=" * 60)
    print("Example calibration targets for mouse_cortical:")
    targets = get_calibration_targets('mouse_cortical')
    for k, v in targets.items():
        print(f"  {k}: {v}")
