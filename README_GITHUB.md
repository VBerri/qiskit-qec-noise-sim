# Quantum Error Correction: Scaling Repetition Codes

**A reproducible study of how repetition codes reduce logical errors as code size increases.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue)
![Qiskit](https://img.shields.io/badge/Qiskit-1.2+-blueviolet)

---

## Overview

Quantum computers are powerful but fragile—noise corrupts quantum information. This project demonstrates how **repetition-code error correction** reduces logical errors as code size (distance) increases from 3 to 5 to 7 qubits.

**Key finding:** At physical error rate $p=0.08$, the baseline (n=1) achieved 0.7585 logical success, while n=7 repetition code reached 0.9270. At low noise ($p=0.02$), n=7 achieved near-zero logical error (~0.999 success).

[**Full paper:** `paper/main.pdf`](paper/main.pdf)

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/[your-username]/QC1ErrorCorrection.git
cd QC1ErrorCorrection
python -m venv .venv
.venv\Scripts\activate  # Windows
# or source .venv/bin/activate  # Mac/Linux

pip install -U pip
pip install -r requirements.txt
```

### 2. Run Experiments

```bash
# Bit-flip noise (X-basis error correction)
python scripts/run_experiments.py --experiment bitflip --shots 4000

# Phase-flip noise (Z-basis error correction)
python scripts/run_experiments.py --experiment phaseflip --shots 4000

# Depolarizing noise (mixture of bit-flip, phase-flip, and identity)
python scripts/run_experiments.py --experiment depolarizing --shots 4000
```

**Output:** CSV results in `results/` + PNG plots of logical success vs noise.

### 3. Run Tests

```bash
pytest -q
```

All tests should pass. Tests verify:
- Repetition codes improve over baseline
- Larger codes (n=7) outperform smaller codes (n=3, n=5)
- At low noise, n=7 achieves near-zero logical error (~0.999)

### 4. View & Rebuild Paper Tables

```bash
python paper/make_tables.py  # Generates LaTeX tables from CSVs
tools/tectonic/tectonic.exe paper/main.tex  # Compile PDF (Windows)
# or pdflatex (if you have TeX installed)
```

---

## Project Structure

```
QC1ErrorCorrection/
├── src/qc1ec/              # Main package
│   ├── circuits.py         # Repetition + stabilizer circuit builders
│   ├── noise.py            # Noise model definitions
│   ├── decode.py           # Decoding logic (majority vote, syndrome extraction)
│   ├── experiments.py       # Orchestration: run sweeps, collect data
│   ├── plotting.py         # Plot success curves
│   └── __main__.py         # CLI entry point
├── scripts/
│   └── run_experiments.py  # Main entry: sweep p-values, save CSVs
├── tests/
│   └── test_ec_improves.py # Unit tests for correctness
├── paper/
│   ├── main.tex           # LaTeX manuscript
│   ├── make_tables.py     # Generate tables from CSVs
│   └── tables/            # Generated .tex tables
├── results/               # Experiment outputs (CSV, PNG)
└── requirements.txt       # Python dependencies
```

---

## Methods Compared

### Baseline
- **n=1:** Single physical qubit, no error correction.

### Bit-flip Repetition Codes (Z-basis storage)
- **n=3, n=5, n=7:** Encode logical qubit as three/five/seven qubits in Z basis ($|0\rangle$ or $|1\rangle$). 
- Protects against **X (bit-flip)** errors.
- Decode: **majority vote** on measurement outcomes.

### Phase-flip Repetition Codes (X-basis storage)
- **n=3, n=5, n=7:** Encode logical qubit in X basis ($|+\rangle$ or $|-\rangle$).
- Protects against **Z (phase-flip)** errors.
- Decode: majority vote in X basis.

### Stabilizer Codes (optional)
- **Bit-flip stabilizer (n=3):** 3 data qubits + 2 ancilla qubits; measure stabilizers.
- **Phase-flip stabilizer (n=3):** Same structure, different basis.

---

## Noise Models

### Bit-flip Noise
- Each identity gate applies $X$ (bit-flip) with probability $p$.
- Represents $T_1$-like decoherence.

### Phase-flip Noise
- Each identity gate applies $Z$ (phase-flip) with probability $p$.
- Represents $T_2$-like decoherence.

### Depolarizing Noise
- Each identity gate applies a depolarizing channel with probability $p$ (mix of $X$, $Y$, $Z$).
- More realistic; tests both bit-flip and phase-flip protections simultaneously.

---

## Key Results

### Scaling Trend
Larger codes consistently reduce logical error across all noise types and all tested $p$ values ($0 \leq p \leq 0.08$).

### Example: Bit-flip Noise @ $p=0.08$
| Code | Logical Success |
|------|-----------------|
| Baseline (n=1) | 0.7585 |
| Repetition (n=3) | 0.8430 |
| Repetition (n=5) | 0.8972 |
| **Repetition (n=7)** | **0.9270** |

### Low Noise Regime @ $p=0.02$
- n=7 repetition codes reach logical success **≈ 0.999** (near-zero logical error).
- Same trend in bit-flip, phase-flip, and fair depolarizing setups.

---

## Usage Examples

### Run a single experiment with custom parameters
```bash
python scripts/run_experiments.py \
  --experiment bitflip \
  --shots 2000 \
  --idle-steps 3 \
  --p-min 0.0 \
  --p-max 0.06 \
  --p-steps 7 \
  --seed 999 \
  --outdir results
```

### In Python: build a circuit directly
```python
from qc1ec.circuits import build_repetition_circuit

circuit = build_repetition_circuit(
    n=7,
    basis="Z",
    state="0",
    idle_steps=4
)
print(circuit)
```

### In Python: run a single noise/p-value test
```python
from qc1ec.experiments import run_experiment

df = run_experiment(
    experiment="bitflip",
    shots=1000,
    idle_steps=4,
    p_values=[0.05],
    seed=12345
)
print(df[["method", "p", "success"]])
```

---

## Reproducibility

- ✅ **All code included** (src/, scripts/, tests/)
- ✅ **All raw data included** (results/*.csv)
- ✅ **Exact parameters logged** (seed, shots, idle_steps, p-values)
- ✅ **Tests pass** on fresh checkout
- ✅ **PDF generated** from LaTeX + tables

To verify:
```bash
pytest -q  # Should pass 7 tests
python scripts/run_experiments.py --experiment bitflip --shots 1000 --seed 12345
# Outputs: results/bitflip_results.csv (should match published results)
```

---

## Citation

If you use this code or data, please cite:

```bibtex
@article{tamilselvan2025qc1ec,
  title={Qubit Error Correction in Quantum Computing Simulations},
  author={Tamilselvan, Sanjeev and Ranjith, Tanuj},
  journal={Journal of Emerging Investigators},
  year={2025}
}
```

Or for preprints:
```bibtex
@misc{tamilselvan2025qc1ec_preprint,
  title={Qubit Error Correction in Quantum Computing Simulations},
  author={Tamilselvan, Sanjeev and Ranjith, Tanuj},
  year={2025},
  howpublished={GitHub},
  url={https://github.com/[your-username]/QC1ErrorCorrection}
}
```

---

## Contributing

This is an educational project by high school students. Feedback, bug reports, and suggestions are very welcome!

- **Issue:** Found a bug or want to request a feature? Open an [Issue](https://github.com/[your-username]/QC1ErrorCorrection/issues).
- **Pull Request:** Have an improvement? Submit a [PR](https://github.com/[your-username]/QC1ErrorCorrection/pulls).

---

## Limitations & Future Work

### Current Limitations
- **Simulation only:** not validated on real quantum hardware.
- **Simplified noise:** independent errors on idle gates only (no gate errors, no readout errors, no correlated noise).
- **Repetition codes only:** can't correct arbitrary errors (would need full QECC like surface codes).

### Future Directions
1. Implement fault-tolerant syndrome extraction.
2. Test Shor code, Steane code, and surface-code toy models.
3. Compare simulation predictions against IBM Quantum / other real devices.
4. Add readout errors and gate errors to noise model.
5. Study threshold behavior (physical error rate below which logical error decreases).

---

## References

- Qiskit: https://qiskit.org/
- Quantum Error Correction: Fowler et al. (2012) "Surface codes: Towards practical large-scale quantum computation"
- Repetition Codes: Terhal (2015) "Quantum error correction for quantum memories"

---

## License

This project is released under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## Authors

**Sanjeev Tamilselvan**  
Northview High School, Duluth, GA  
Email: sansuvans@gmail.com

**Tanuj Ranjith**  
B. Reed Henderson High School, West Chester, PA  
Email: tanujranjith@gmail.com

---

## Questions?

Open an issue on GitHub, or email one of the authors above.

---

**Last updated:** March 2025  
**Status:** Ready for submission to Journal of Emerging Investigators
