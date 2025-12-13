from __future__ import annotations

from typing import Literal

from qiskit_aer.noise import NoiseModel
from qiskit_aer.noise.errors import depolarizing_error, pauli_error


NoiseType = Literal["bitflip", "phaseflip", "depolarizing"]


def build_noise_model(noise_type: NoiseType, p: float) -> NoiseModel:
    if p < 0.0 or p > 1.0:
        raise ValueError("p must be within [0, 1]")

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
    return model
