# Contributing to NeurMito-DT

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone <approved-repository-url>
   cd neurmito
   ```
3. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make changes and test**
5. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add: your feature description"
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request**

## 🧪 Development Setup

### Install Dependencies

```bash
# Core dependencies
pip install numpy scipy matplotlib torch torchdiffeq SALib

# Development dependencies
pip install pytest pytest-cov black flake8
```

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=module1 --cov=module2
```

## 📝 Code Style

- **Python:** Follow PEP 8 (use `black` for formatting)
- **Docstrings:** Use NumPy-style docstrings
- **Type hints:** Encouraged for new code
- **Comments:** Explain WHY, not WHAT

### Example

```python
def compute_membrane_potential(calcium: float, atp: float) -> float:
    """
    Compute mitochondrial membrane potential.

    Parameters
    ----------
    calcium : float
        Mitochondrial Ca2+ concentration (mM)
    atp : float
        ATP concentration (mM)

    Returns
    -------
    float
        Membrane potential (mV)
    """
    # Nernst equation with Ca2+ correction
    return 180 - 26 * np.log(calcium / 1e-4) + 10 * atp
```

## 🧬 Types of Contributions

### 1. Bug Fixes
- Report bugs through the issue tracker of the approved release repository.
- Include minimal reproducible example
- Provide fix with tests

### 2. New Features
- Discuss proposed changes in the approved release repository first.
- Ensure compatibility with existing code
- Add tests and documentation

### 3. Documentation
- Fix typos, improve clarity
- Add examples and tutorials
- Update docstrings

### 4. New Neuron Types
To add a new neuron type:

1. Add experimental data to `data/seahorse_neuron_data.py`:
   ```python
   SEAHORSE_DATA['your_neuron_type'] = {
       'source': 'Citation',
       'basal_ocr': 100.0,
       'maximal_ocr': 250.0,
       # ...
   }
   ```

2. Calibrate parameters in `module1/figure1_neuron_comparison.py`

3. Add to `NEURON_TYPES` list

### 5. New Stress Conditions
To add a new stress factor:

1. Modify `module1/neurmito_system.py::odes()` to handle new stress
2. Update `stress` dictionary handling
3. Add documentation

## ✅ Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass (`pytest`)
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages are clear

## 🐛 Reporting Bugs

**Good bug report includes:**
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (OS, Python version, package versions)
- Minimal reproducible example

## 💬 Communication

- **Questions:** Use [GitHub Discussions](https://github.com/YOUR_USERNAME/NeurMito-DT/discussions)
- **Bugs:** Use [GitHub Issues](https://github.com/YOUR_USERNAME/NeurMito-DT/issues)
- **Feature requests:** Start a discussion first

## 📄 License and contribution terms

Contribution and licensing terms are pending approval by the repository owner
and copyright holders. Do not accept external contributions until those terms
are published.

## 🙏 Thank You!

Thank you for helping improve the reproducibility materials.
