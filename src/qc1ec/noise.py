from __future__ import annotations

from typing import Literal

from qiskit_aer.noise import NoiseModel
from qiskit_aer.noise.errors import ReadoutError, depolarizing_error, pauli_error


NoiseType = Literal["bitflip", "phaseflip", "depolarizing"]


def build_noise_model(
    noise_type: NoiseType,
    p: float,
    readout_error_p: float = 0.0,
    readout_error_0to1: float | None = None,
    readout_error_1to0: float | None = None,
    single_qubit_gate_error_p: float = 0.0,
    cx_gate_error_p: float = 0.0,
) -> NoiseModel:
    if p < 0.0 or p > 1.0:
        raise ValueError("p must be within [0, 1]")
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

    if noise_type == "bitflip":
        err = pauli_error([("X", p), ("I", 1.0 - p)])
    elif noise_type == "phaseflip":
        err = pauli_error([("Z", p), ("I", 1.0 - p)])
    elif noise_type == "depolarizing":
        err = depolarizing_error(p, 1)
    else:
        raise ValueError(f"Unsupported noise_type: {noise_type}")

    model = NoiseModel()
    # Apply the error whenever we insert an explicit identity gate.
    model.add_all_qubit_quantum_error(err, ["id"])

    if single_qubit_gate_error_p > 0.0:
        sq_err = depolarizing_error(single_qubit_gate_error_p, 1)
        model.add_all_qubit_quantum_error(sq_err, ["x", "z", "h"])

    if cx_gate_error_p > 0.0:
        cx_err = depolarizing_error(cx_gate_error_p, 2)
        model.add_all_qubit_quantum_error(cx_err, ["cx"])

    r01 = readout_error_p if readout_error_0to1 is None else readout_error_0to1
    r10 = readout_error_p if readout_error_1to0 is None else readout_error_1to0
    if (r01 > 0.0) or (r10 > 0.0):
        readout = ReadoutError(
            [
                [1.0 - r01, r01],
                [r10, 1.0 - r10],
            ]
        )
        model.add_all_qubit_readout_error(readout)

    return model
