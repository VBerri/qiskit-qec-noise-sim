from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from qiskit import QuantumCircuit


Basis = Literal["Z", "X"]
State = Literal["0", "1", "plus", "minus"]


@dataclass(frozen=True)
class MethodSpec:
    name: str
    n: int
    basis: Basis


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
