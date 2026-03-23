from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from qiskit import transpile
from qiskit_aer import AerSimulator

from qc1ec.circuits import (
    MethodSpec,
    build_bitflip_stabilizer_circuit,
    build_phaseflip_stabilizer_circuit,
    build_repetition_circuit,
)
from qc1ec.decode import (
    logical_success_probability_map,
    logical_success_probability_postselected,
    logical_success_probability_stabilizer_multiround,
    logical_success_probability_with_readout_mitigation,
    logical_success_probability_with_data_indices,
    wilson_confidence_interval,
    theoretical_repetition_success,
)
from qc1ec.noise import NoiseType, build_noise_model
from qc1ec.plotting import plot_success_curves


DecodeMode = Literal["majority", "postselect", "map"]


def _effective_data_flip_probability(*, noise_type: NoiseType, p: float, idle_steps: int, basis: str) -> float:
    if idle_steps <= 0:
        return 0.0

    if noise_type == "bitflip":
        per_step = p if basis == "Z" else 0.0
    elif noise_type == "phaseflip":
        per_step = p if basis == "X" else 0.0
    elif noise_type == "depolarizing":
        per_step = (2.0 * p) / 3.0
    else:
        per_step = 0.0

    per_step = min(max(per_step, 0.0), 1.0)
    return 0.5 * (1.0 - (1.0 - 2.0 * per_step) ** idle_steps)


def _method_specs_for_experiment(experiment: str) -> list[MethodSpec]:
    # Baseline always included as n=1.
    if experiment == "bitflip":
        return [
            MethodSpec(name="baseline_n1", n=1, basis="Z", state="0"),
            MethodSpec(name="bitflip_rep_n3", n=3, basis="Z", state="0"),
            MethodSpec(name="bitflip_rep_n5", n=5, basis="Z", state="0"),
        ]
    if experiment == "phaseflip":
        return [
            MethodSpec(name="baseline_n1", n=1, basis="X", state="plus"),
            MethodSpec(name="phaseflip_rep_n3", n=3, basis="X", state="plus"),
            MethodSpec(name="phaseflip_rep_n5", n=5, basis="X", state="plus"),
        ]
    if experiment == "depolarizing":
        return [
            MethodSpec(name="baseline_z_n1", n=1, basis="Z", state="0"),
            MethodSpec(name="baseline_x_n1", n=1, basis="X", state="plus"),
            MethodSpec(name="bitflip_rep_n3", n=3, basis="Z", state="0"),
            MethodSpec(name="bitflip_rep_n5", n=5, basis="Z", state="0"),
            MethodSpec(name="phaseflip_rep_n3", n=3, basis="X", state="plus"),
            MethodSpec(name="phaseflip_rep_n5", n=5, basis="X", state="plus"),
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


def _default_state_for_basis(basis: str) -> str:
    if basis == "Z":
        return "0"
    if basis == "X":
        return "plus"
    raise ValueError(f"Unknown basis: {basis}")


def _expected_logical_from_state(state: str) -> int:
    if state in {"0", "plus"}:
        return 0
    if state in {"1", "minus"}:
        return 1
    raise ValueError(f"Unknown state: {state}")


def run_experiment(
    *,
    experiment: str,
    shots: int,
    idle_steps: int,
    p_values: list[float],
    seed: int,
    decode_mode: DecodeMode = "majority",
    postselect_margin: int | None = None,
    readout_error_p: float = 0.0,
    readout_error_0to1: float | None = None,
    readout_error_1to0: float | None = None,
    use_readout_mitigation: bool = False,
    stabilizer_rounds: int = 1,
    single_qubit_gate_error_p: float = 0.0,
    cx_gate_error_p: float = 0.0,
) -> pd.DataFrame:
    if stabilizer_rounds < 1:
        raise ValueError("stabilizer_rounds must be >= 1")
    if readout_error_p < 0.0 or readout_error_p >= 0.5:
        raise ValueError("readout_error_p must be within [0, 0.5)")
    if readout_error_0to1 is not None and (readout_error_0to1 < 0.0 or readout_error_0to1 >= 1.0):
        raise ValueError("readout_error_0to1 must be within [0, 1)")
    if readout_error_1to0 is not None and (readout_error_1to0 < 0.0 or readout_error_1to0 >= 1.0):
        raise ValueError("readout_error_1to0 must be within [0, 1)")
    if single_qubit_gate_error_p < 0.0 or single_qubit_gate_error_p > 1.0:
        raise ValueError("single_qubit_gate_error_p must be within [0, 1]")
    if cx_gate_error_p < 0.0 or cx_gate_error_p > 1.0:
        raise ValueError("cx_gate_error_p must be within [0, 1]")
    effective_r01 = readout_error_p if readout_error_0to1 is None else readout_error_0to1
    effective_r10 = readout_error_p if readout_error_1to0 is None else readout_error_1to0
    if use_readout_mitigation and max(effective_r01, effective_r10) <= 0.0:
        raise ValueError("use_readout_mitigation requires nonzero readout error settings")
    if use_readout_mitigation and decode_mode != "majority":
        raise ValueError("readout mitigation currently supports decode_mode='majority' only")

    methods = _method_specs_for_experiment(experiment)
    noise_type = _noise_type_for_experiment(experiment)

    timestamp = datetime.now(timezone.utc).isoformat()

    rows: list[dict] = []

    circuits = []
    method_states: list[str] = []
    for method in methods:
        method_state = method.state or _default_state_for_basis(method.basis)
        method_states.append(method_state)

        if method.kind == "repetition":
            circuits.append(
                build_repetition_circuit(
                    n=method.n,
                    basis=method.basis,
                    state=method_state,
                    idle_steps=idle_steps,
                )
            )
        elif method.kind == "bitflip_stabilizer":
            circuits.append(
                build_bitflip_stabilizer_circuit(
                    state=method_state,
                    idle_steps=idle_steps,
                    syndrome_rounds=stabilizer_rounds,
                )
            )
        elif method.kind == "phaseflip_stabilizer":
            circuits.append(
                build_phaseflip_stabilizer_circuit(
                    state=method_state,
                    idle_steps=idle_steps,
                    syndrome_rounds=stabilizer_rounds,
                )
            )
        else:
            raise ValueError(f"Unsupported method kind: {method.kind}")

    transpile_backend = AerSimulator(seed_simulator=seed)
    transpiled = transpile(circuits, backend=transpile_backend, optimization_level=0, seed_transpiler=seed)

    for p in p_values:
        noise_model = build_noise_model(
            noise_type,
            p,
            readout_error_p=readout_error_p,
            readout_error_0to1=readout_error_0to1,
            readout_error_1to0=readout_error_1to0,
            single_qubit_gate_error_p=single_qubit_gate_error_p,
            cx_gate_error_p=cx_gate_error_p,
        )
        backend = AerSimulator(noise_model=noise_model, seed_simulator=seed)
        job = backend.run(transpiled, shots=shots)
        result = job.result()

        for idx, method in enumerate(methods):
            method_state = method_states[idx]
            counts = result.get_counts(idx)
            expected_logical = _expected_logical_from_state(method_state)
            if method.kind in {"bitflip_stabilizer", "phaseflip_stabilizer"}:
                total_bits = 2 * stabilizer_rounds + 3
                data_indices = tuple(range(2 * stabilizer_rounds, 2 * stabilizer_rounds + 3))
            else:
                total_bits = method.total_qubits or method.n
                data_indices = method.data_indices or tuple(range(method.n))

            if use_readout_mitigation:
                success = logical_success_probability_with_readout_mitigation(
                    counts,
                    total_bits=total_bits,
                    data_indices=data_indices,
                    expected_logical=expected_logical,
                    readout_error_p=readout_error_p,
                    readout_error_0to1=readout_error_0to1,
                    readout_error_1to0=readout_error_1to0,
                )
                kept_fraction = 1.0
            elif decode_mode == "majority":
                if method.kind in {"bitflip_stabilizer", "phaseflip_stabilizer"}:
                    success = logical_success_probability_stabilizer_multiround(
                        counts,
                        total_bits=total_bits,
                        syndrome_rounds=stabilizer_rounds,
                        expected_logical=expected_logical,
                    )
                else:
                    success = logical_success_probability_with_data_indices(
                        counts,
                        total_bits=total_bits,
                        data_indices=data_indices,
                        expected_logical=expected_logical,
                    )
                kept_fraction = 1.0
            elif decode_mode == "postselect":
                margin = postselect_margin
                if margin is None:
                    margin = 1 if len(data_indices) <= 1 else 3
                success, kept_fraction = logical_success_probability_postselected(
                    counts,
                    total_bits=total_bits,
                    data_indices=data_indices,
                    expected_logical=expected_logical,
                    min_majority_margin=margin,
                )
            elif decode_mode == "map":
                flip_probability = _effective_data_flip_probability(
                    noise_type=noise_type,
                    p=float(p),
                    idle_steps=idle_steps,
                    basis=method.basis,
                )
                success = logical_success_probability_map(
                    counts,
                    total_bits=total_bits,
                    data_indices=data_indices,
                    expected_logical=expected_logical,
                    physical_flip_probability=flip_probability,
                    readout_error_p=readout_error_p,
                    readout_error_0to1=readout_error_0to1,
                    readout_error_1to0=readout_error_1to0,
                )
                kept_fraction = 1.0
            else:
                raise ValueError(f"Unsupported decode_mode: {decode_mode}")

            # Confidence interval: use effective shot count (reduced by post-selection).
            effective_shots = int(kept_fraction * shots) if decode_mode == "postselect" else int(shots)
            ci_low, ci_high = wilson_confidence_interval(float(success), effective_shots)

            # Theoretical prediction for repetition codes (exact binomial formula).
            if method.kind == "repetition":
                eff_p = _effective_data_flip_probability(
                    noise_type=noise_type,
                    p=float(p),
                    idle_steps=idle_steps,
                    basis=method.basis,
                )
                success_theory = theoretical_repetition_success(eff_p, method.n)
            else:
                success_theory = float("nan")

            rows.append(
                {
                    "timestamp_utc": timestamp,
                    "experiment": experiment,
                    "noise": noise_type,
                    "p": float(p),
                    "shots": int(shots),
                    "idle_steps": int(idle_steps),
                    "seed": int(seed),
                    "state": method_state,
                    "method": method.name,
                    "n": method.n,
                    "basis": method.basis,
                    "decode_mode": decode_mode,
                    "readout_error_p": float(readout_error_p),
                    "readout_mitigated": bool(use_readout_mitigation),
                    "stabilizer_rounds": int(stabilizer_rounds),
                    "readout_error_0to1": (
                        float(readout_error_0to1) if readout_error_0to1 is not None else float(readout_error_p)
                    ),
                    "readout_error_1to0": (
                        float(readout_error_1to0) if readout_error_1to0 is not None else float(readout_error_p)
                    ),
                    "single_qubit_gate_error_p": float(single_qubit_gate_error_p),
                    "cx_gate_error_p": float(cx_gate_error_p),
                    "kept_fraction": float(kept_fraction),
                    "success": float(success),
                    "success_ci_lower": ci_low,
                    "success_ci_upper": ci_high,
                    "success_theory": success_theory,
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
    decode_mode: DecodeMode = "majority",
    postselect_margin: int | None = None,
    readout_error_p: float = 0.0,
    readout_error_0to1: float | None = None,
    readout_error_1to0: float | None = None,
    use_readout_mitigation: bool = False,
    stabilizer_rounds: int = 1,
    single_qubit_gate_error_p: float = 0.0,
    cx_gate_error_p: float = 0.0,
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
        decode_mode=decode_mode,
        postselect_margin=postselect_margin,
        readout_error_p=readout_error_p,
        readout_error_0to1=readout_error_0to1,
        readout_error_1to0=readout_error_1to0,
        use_readout_mitigation=use_readout_mitigation,
        stabilizer_rounds=stabilizer_rounds,
        single_qubit_gate_error_p=single_qubit_gate_error_p,
        cx_gate_error_p=cx_gate_error_p,
    )

    csv_path = out_path / f"{experiment}_results.csv"
    df.to_csv(csv_path, index=False)

    png_path = out_path / f"{experiment}_success.png"
    plot_success_curves(
        df,
        title=(
            f"{experiment}: logical success vs noise "
            f"(shots={shots}, idle_steps={idle_steps}, decode={decode_mode})"
        ),
        out_png=png_path,
    )
