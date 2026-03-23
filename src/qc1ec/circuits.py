from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from qiskit import QuantumCircuit


Basis = Literal["Z", "X"]
State = Literal["0", "1", "plus", "minus"]
MethodKind = Literal["repetition", "bitflip_stabilizer", "phaseflip_stabilizer"]


@dataclass(frozen=True)
class MethodSpec:
    name: str
    n: int
    basis: Basis
    state: State | None = None
    kind: MethodKind = "repetition"
    total_qubits: int | None = None
    data_indices: tuple[int, ...] | None = None


def build_repetition_circuit(
    *,
    n: int,
    basis: Basis,
    state: State,
    idle_steps: int,
) -> QuantumCircuit:
    if n < 1 or (n % 2) == 0:
        raise ValueError("n must be an odd integer >= 1")
    if idle_steps < 0:
        raise ValueError("idle_steps must be >= 0")

    qc = QuantumCircuit(n, n)

    # Prepare logical state on qubit 0.
    if state == "1":
        qc.x(0)
    elif state == "plus":
        qc.h(0)
    elif state == "minus":
        qc.x(0)
        qc.h(0)
    elif state == "0":
        pass
    else:
        raise ValueError(f"Unsupported state: {state}")

    if n > 1:
        if basis == "Z":
            # Ancillas already |0>.
            for i in range(1, n):
                qc.cx(0, i)
        elif basis == "X":
            # To encode repetition in X basis:
            # - prepare ancillas as |+>
            for i in range(1, n):
                qc.h(i)
            # - rotate X->Z, copy with CNOTs, rotate back
            for i in range(0, n):
                qc.h(i)
            for i in range(1, n):
                qc.cx(0, i)
            for i in range(0, n):
                qc.h(i)
        else:
            raise ValueError(f"Unsupported basis: {basis}")

    # Noisy memory: use explicit identity gates so a noise model can target "id".
    for _ in range(idle_steps):
        for i in range(n):
            qc.id(i)

    # Measure in the same basis as repetition encoding.
    if basis == "X":
        for i in range(n):
            qc.h(i)

    for i in range(n):
        qc.measure(i, i)

    return qc


def build_bitflip_stabilizer_circuit(
    *,
    state: State,
    idle_steps: int,
    syndrome_rounds: int = 1,
) -> QuantumCircuit:
    if idle_steps < 0:
        raise ValueError("idle_steps must be >= 0")
    if syndrome_rounds < 1:
        raise ValueError("syndrome_rounds must be >= 1")
    if state not in {"0", "1"}:
        raise ValueError("bit-flip stabilizer supports |0> or |1> only")

    # Data qubits: q0,q1,q2. Ancillas: q3,q4.
    # Classical layout: [2*syndrome_rounds syndrome bits] + [3 data bits].
    classical_bits = 2 * syndrome_rounds + 3
    qc = QuantumCircuit(5, classical_bits)

    # Prepare logical state on q0 and encode repetition.
    if state == "1":
        qc.x(0)
    qc.cx(0, 1)
    qc.cx(0, 2)

    # Noisy memory on data qubits.
    for _ in range(idle_steps):
        for i in range(3):
            qc.id(i)

    # Repeated syndrome extraction rounds (syndrome is decoded classically later).
    for round_idx in range(syndrome_rounds):
        qc.cx(0, 3)
        qc.cx(1, 3)
        qc.measure(3, 2 * round_idx)

        qc.cx(1, 4)
        qc.cx(2, 4)
        qc.measure(4, 2 * round_idx + 1)

        qc.reset(3)
        qc.reset(4)

    # Measure data qubits into the final 3 classical bits.
    data_offset = 2 * syndrome_rounds
    qc.measure(0, data_offset + 0)
    qc.measure(1, data_offset + 1)
    qc.measure(2, data_offset + 2)

    return qc


def build_phaseflip_stabilizer_circuit(
    *,
    state: State,
    idle_steps: int,
    syndrome_rounds: int = 1,
) -> QuantumCircuit:
    if idle_steps < 0:
        raise ValueError("idle_steps must be >= 0")
    if syndrome_rounds < 1:
        raise ValueError("syndrome_rounds must be >= 1")
    if state not in {"plus", "minus"}:
        raise ValueError("phase-flip stabilizer supports |+> or |-> only")

    # Data qubits: q0,q1,q2. Ancillas: q3,q4.
    # Classical layout: [2*syndrome_rounds syndrome bits] + [3 data bits].
    classical_bits = 2 * syndrome_rounds + 3
    qc = QuantumCircuit(5, classical_bits)

    # Prepare logical state on q0 and encode repetition in X basis.
    if state == "minus":
        qc.x(0)
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.cx(0, 1)
    qc.cx(0, 2)
    qc.h(0)
    qc.h(1)
    qc.h(2)

    # Noisy memory on data qubits.
    for _ in range(idle_steps):
        for i in range(3):
            qc.id(i)

    # Repeated syndrome extraction rounds for X stabilizers
    # (decoded classically later).
    for round_idx in range(syndrome_rounds):
        qc.h(0)
        qc.h(1)
        qc.h(2)

        qc.cx(0, 3)
        qc.cx(1, 3)
        qc.measure(3, 2 * round_idx)

        qc.cx(1, 4)
        qc.cx(2, 4)
        qc.measure(4, 2 * round_idx + 1)

        qc.h(0)
        qc.h(1)
        qc.h(2)

        qc.reset(3)
        qc.reset(4)

    # Measure data qubits in X basis into the final 3 classical bits.
    qc.h(0)
    qc.h(1)
    qc.h(2)
    data_offset = 2 * syndrome_rounds
    qc.measure(0, data_offset + 0)
    qc.measure(1, data_offset + 1)
    qc.measure(2, data_offset + 2)

    return qc
