# QC1 Error Correction (Qiskit)

Small, reproducible Qiskit/Aer simulations that compare how simple **error-correction via repetition codes** changes the **logical success rate** under different noise types.

## What this project produces

- CSV tables in `results/` (one row per noise level & method)
- PNG plots in `results/` (success rate vs noise strength)

## Methods compared

- **Baseline** (no encoding, `n=1`)
- **Bit-flip repetition code** (`n=3`, `n=5`, `n=7`) — best under **X (bit-flip)** noise
- **Phase-flip repetition code** (`n=3`, `n=5`, `n=7`) — best under **Z (phase-flip)** noise

## Quickstart (Windows `cmd.exe`)

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
```

Run experiments (writes `results/*.csv` and `results/*.png`):

```cmd
python scripts\run_experiments.py --experiment bitflip --shots 4000
python scripts\run_experiments.py --experiment phaseflip --shots 4000
python scripts\run_experiments.py --experiment depolarizing --shots 4000

# Optional: confidence-based post-selection decoder (higher fidelity, fewer kept shots)
python scripts\run_experiments.py --experiment bitflip --shots 4000 --decode-mode postselect --postselect-margin 3

# Optional: noise-aware MAP decoder
python scripts\run_experiments.py --experiment bitflip --shots 4000 --decode-mode map --readout-error-p 0.05

# Optional: repeated stabilizer rounds (for stabilizer methods in bitflip/phaseflip experiments)
python scripts\run_experiments.py --experiment bitflip --shots 4000 --stabilizer-rounds 2

# Optional: readout mitigation (requires readout error configured)
python scripts\run_experiments.py --experiment bitflip --shots 4000 --readout-error-p 0.12 --readout-mitigation

# Optional: asymmetric readout model (helps show MAP decoder advantages)
python scripts\run_experiments.py --experiment bitflip --shots 4000 --decode-mode map --readout-error-0to1 0.20 --readout-error-1to0 0.02

# Optional: gate noise on CX/single-qubit gates (useful for stabilizer-round studies)
python scripts\run_experiments.py --experiment bitflip --shots 4000 --stabilizer-rounds 3 --readout-error-p 0.10 --cx-gate-error-p 0.01
```

Run tests:

```cmd
pytest
```

## Notes for article writing

- Each run stores metadata (date, shots, idle steps, seed).
- The metric reported is **logical success probability** (how often decoding matches the intended logical outcome).

## Building the Paper

To generate the LaTeX tables from the experiment results:

```cmd
python paper/make_tables.py
```

To compile the PDF using the included Tectonic engine:

```cmd
tools\tectonic\tectonic.exe paper/main.tex
```

The output PDF will be at `paper/main.pdf`.

