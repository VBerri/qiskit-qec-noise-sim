from __future__ import annotations

from collections.abc import Iterable


def bits_for_qubits_from_count_key(key: str, n: int) -> list[int]:
    """Map a Qiskit count key to bits indexed by qubit/classical index.

    If we measure qubit i into classical bit i, Qiskit returns keys as
    c[n-1]...c[0].
    """
    key = key.replace(" ", "")
    if len(key) != n:
        raise ValueError(f"Expected key length {n}, got {len(key)}: {key!r}")

    bits = []
    for i in range(n):
        bits.append(1 if key[-1 - i] == "1" else 0)
    return bits


def majority_vote(bits: Iterable[int]) -> int:
    bits_list = list(bits)
    ones = sum(1 for b in bits_list if b)
    zeros = len(bits_list) - ones
    return 1 if ones > zeros else 0


def logical_success_probability(counts: dict[str, int], n: int, expected_logical: int) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0

    success = 0
    for key, count in counts.items():
        bits = bits_for_qubits_from_count_key(key, n)
        logical = majority_vote(bits)
        if logical == expected_logical:
            success += count

    return success / total
