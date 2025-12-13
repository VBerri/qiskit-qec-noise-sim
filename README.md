# QC1 Error Correction (Qiskit)

Small, reproducible Qiskit/Aer simulations that compare how simple **error-correction via repetition codes** changes the **logical success rate** under different noise types.

## What this project produces

- CSV tables in `results/` (one row per noise level & method)
- PNG plots in `results/` (success rate vs noise strength)

## Methods compared

- **Baseline** (no encoding, `n=1`)
- **Bit-flip repetition code** (`n=3`, `n=5`) — best under **X (bit-flip)** noise
- **Phase-flip repetition code** (`n=3`, `n=5`) — best under **Z (phase-flip)** noise

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
```

Run tests:

```cmd
pytest
```
# Results
The following are the results of the experiment
## PhaseFlip Result
![PhaseFlip Result](results/phaseflip_success.png)
## BitFlip Result
![BitFlip Result](results/bitflip_success.png)
## Depolarizing Result
![Depolarizing Result](results/depolarizing_success.png)



