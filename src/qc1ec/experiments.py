from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit import transpile
from qiskit_aer import AerSimulator

from qc1ec.circuits import MethodSpec, build_repetition_circuit
from qc1ec.decode import logical_success_probability
from qc1ec.noise import NoiseType, build_noise_model
from qc1ec.plotting import plot_success_curves


def _method_specs_for_experiment(experiment: str) -> list[MethodSpec]:
    # Baseline always included as n=1.
    if experiment == "bitflip":
        return [
            MethodSpec(name="baseline_n1", n=1, basis="Z"),
            MethodSpec(name="bitflip_rep_n3", n=3, basis="Z"),
            MethodSpec(name="bitflip_rep_n5", n=5, basis="Z"),
        ]
    if experiment == "phaseflip":
        return [
            MethodSpec(name="baseline_n1", n=1, basis="X"),
            MethodSpec(name="phaseflip_rep_n3", n=3, basis="X"),
            MethodSpec(name="phaseflip_rep_n5", n=5, basis="X"),
        ]
    if experiment == "depolarizing":
        # Under depolarizing noise (X/Y/Z), compare both encodings.
        return [
            MethodSpec(name="baseline_n1", n=1, basis="X"),
            MethodSpec(name="bitflip_rep_n3", n=3, basis="Z"),
            MethodSpec(name="bitflip_rep_n5", n=5, basis="Z"),
            MethodSpec(name="phaseflip_rep_n3", n=3, basis="X"),
            MethodSpec(name="phaseflip_rep_n5", n=5, basis="X"),
        ]
    raise ValueError(f"Unknown experiment: {experiment}")


def _noise_type_for_experiment(experiment: str) -> NoiseType:
    if experiment == "bitflip":
        return "bitflip"
    if experiment == "phaseflip":
        return "phaseflip"
    if experiment == "depolarizing":
        return "depolarizing"
    raise ValueError(f"Unknown experiment: {experiment}")


def _state_for_experiment(experiment: str) -> str:
    # Choose a state where the noise meaningfully changes the outcome.
    if experiment == "bitflip":
        return "0"  # Z-basis storage; X errors flip it.
    if experiment == "phaseflip":
        return "plus"  # X-basis storage; Z errors flip it.
    if experiment == "depolarizing":
        return "plus"  # mixes bit/phase; compare both encodings.
    raise ValueError(f"Unknown experiment: {experiment}")


def run_experiment(
    *,
    experiment: str,
    shots: int,
    idle_steps: int,
    p_values: list[float],
    seed: int,
) -> pd.DataFrame:
    methods = _method_specs_for_experiment(experiment)
    noise_type = _noise_type_for_experiment(experiment)
    state = _state_for_experiment(experiment)

    timestamp = datetime.now(timezone.utc).isoformat()

    rows: list[dict] = []

    for p in p_values:
        noise_model = build_noise_model(noise_type, p)
        backend = AerSimulator(noise_model=noise_model, seed_simulator=seed)

        circuits = []
        for method in methods:
            circuits.append(
                build_repetition_circuit(
                    n=method.n,
                    basis=method.basis,
                    state=state,
                    idle_steps=idle_steps,
                )
            )

        transpiled = transpile(circuits, backend=backend, optimization_level=0, seed_transpiler=seed)
        job = backend.run(transpiled, shots=shots)
        result = job.result()

        for idx, method in enumerate(methods):
            counts = result.get_counts(idx)
            expected_logical = 0  # all experiments target logical 0 (|0> or |+>)
            success = logical_success_probability(counts, method.n, expected_logical)

            rows.append(
                {
                    "timestamp_utc": timestamp,
                    "experiment": experiment,
                    "noise": noise_type,
                    "p": float(p),
                    "shots": int(shots),
                    "idle_steps": int(idle_steps),
                    "seed": int(seed),
                    "state": state,
                    "method": method.name,
                    "n": method.n,
                    "basis": method.basis,
                    "success": float(success),
                    "counts": str(counts),
                }
            )

    return pd.DataFrame(rows)


def run_and_save(
    *,
    experiment: str,
    shots: int,
    idle_steps: int,
    p_min: float,
    p_max: float,
    p_steps: int,
    seed: int,
    outdir: str,
) -> None:
    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)

    p_values = np.linspace(p_min, p_max, p_steps).tolist()
    df = run_experiment(
        experiment=experiment,
        shots=shots,
        idle_steps=idle_steps,
        p_values=p_values,
        seed=seed,
    )

    csv_path = out_path / f"{experiment}_results.csv"
    df.to_csv(csv_path, index=False)

    png_path = out_path / f"{experiment}_success.png"
    plot_success_curves(
        df,
        title=f"{experiment}: logical success vs noise (shots={shots}, idle_steps={idle_steps})",
        out_png=png_path,
    )
