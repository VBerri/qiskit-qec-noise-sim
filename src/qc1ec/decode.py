from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np


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


def _bits_to_index_little_endian(bits: list[int]) -> int:
    idx = 0
    for i, bit in enumerate(bits):
        if bit:
            idx |= (1 << i)
    return idx


def _index_to_bits_little_endian(idx: int, n: int) -> list[int]:
    return [1 if ((idx >> i) & 1) else 0 for i in range(n)]


def logical_success_probability(
    counts: dict[str, int],
    n: int,
    expected_logical: int,
) -> float:
    return logical_success_probability_with_data_indices(
        counts,
        total_bits=n,
        data_indices=tuple(range(n)),
        expected_logical=expected_logical,
    )


def logical_success_probability_with_data_indices(
    counts: dict[str, int],
    total_bits: int,
    data_indices: tuple[int, ...],
    expected_logical: int,
) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0

    success = 0
    for key, count in counts.items():
        bits = bits_for_qubits_from_count_key(key, total_bits)
        data_bits = [bits[i] for i in data_indices]
        logical = majority_vote(data_bits)
        if logical == expected_logical:
            success += count

    return success / total


def wilson_confidence_interval(success: float, shots: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% confidence interval for a binomial proportion.

    Returns (lower, upper) bounds.  More accurate than the normal approximation
    near p=0 or p=1, which is common at low noise levels.
    """
    if shots == 0:
        return 0.0, 1.0
    n = shots
    p_hat = success
    center = (p_hat + z**2 / (2 * n)) / (1 + z**2 / n)
    margin = z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return max(0.0, center - margin), min(1.0, center + margin)


def theoretical_repetition_success(p: float, n: int) -> float:
    """Exact logical success probability for an n-qubit majority-vote repetition code.

    P_fail = sum_{k=ceil((n+1)/2)}^{n} C(n,k) * p^k * (1-p)^(n-k)

    Args:
        p: Per-qubit physical flip probability (after idle steps).
        n: Number of physical qubits (code size).

    Returns:
        Logical success probability 1 - P_fail.
    """
    threshold = (n + 1) // 2
    fail = sum(math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(threshold, n + 1))
    return 1.0 - fail


def logical_success_probability_postselected(
    counts: dict[str, int],
    total_bits: int,
    data_indices: tuple[int, ...],
    expected_logical: int,
    min_majority_margin: int,
) -> tuple[float, float]:
    if min_majority_margin < 1:
        raise ValueError("min_majority_margin must be >= 1")

    kept_total = 0
    success = 0
    total = sum(counts.values())
    if total == 0:
        return 0.0, 0.0

    for key, count in counts.items():
        bits = bits_for_qubits_from_count_key(key, total_bits)
        data_bits = [bits[i] for i in data_indices]
        ones = sum(1 for bit in data_bits if bit)
        zeros = len(data_bits) - ones
        margin = abs(ones - zeros)

        if margin < min_majority_margin:
            continue

        kept_total += count
        logical = 1 if ones > zeros else 0
        if logical == expected_logical:
            success += count

    if kept_total == 0:
        return 0.0, 0.0

    return success / kept_total, kept_total / total


def logical_success_probability_map(
    counts: dict[str, int],
    total_bits: int,
    data_indices: tuple[int, ...],
    expected_logical: int,
    physical_flip_probability: float,
    readout_error_p: float = 0.0,
    readout_error_0to1: float | None = None,
    readout_error_1to0: float | None = None,
) -> float:
    if physical_flip_probability < 0.0 or physical_flip_probability > 1.0:
        raise ValueError("physical_flip_probability must be within [0, 1]")
    r01 = readout_error_p if readout_error_0to1 is None else readout_error_0to1
    r10 = readout_error_p if readout_error_1to0 is None else readout_error_1to0
    if r01 < 0.0 or r01 >= 1.0 or r10 < 0.0 or r10 >= 1.0:
        raise ValueError("readout error probabilities must be within [0, 1)")

    total = sum(counts.values())
    if total == 0:
        return 0.0

    success = 0
    for key, count in counts.items():
        bits = bits_for_qubits_from_count_key(key, total_bits)
        data_bits = [bits[i] for i in data_indices]

        q = physical_flip_probability
        p1_given_l0 = (1.0 - q) * r01 + q * (1.0 - r10)
        p1_given_l1 = (1.0 - q) * (1.0 - r10) + q * r01

        p1_given_l0 = min(max(p1_given_l0, 1e-12), 1.0 - 1e-12)
        p1_given_l1 = min(max(p1_given_l1, 1e-12), 1.0 - 1e-12)

        log_like_l0 = 0.0
        log_like_l1 = 0.0
        for obs in data_bits:
            if obs == 1:
                log_like_l0 += math.log(p1_given_l0)
                log_like_l1 += math.log(p1_given_l1)
            else:
                log_like_l0 += math.log(1.0 - p1_given_l0)
                log_like_l1 += math.log(1.0 - p1_given_l1)

        logical = 1 if log_like_l1 > log_like_l0 else 0
        if logical == expected_logical:
            success += count

    return success / total


def logical_success_probability_with_readout_mitigation(
    counts: dict[str, int],
    total_bits: int,
    data_indices: tuple[int, ...],
    expected_logical: int,
    readout_error_p: float,
    readout_error_0to1: float | None = None,
    readout_error_1to0: float | None = None,
) -> float:
    r01 = readout_error_p if readout_error_0to1 is None else readout_error_0to1
    r10 = readout_error_p if readout_error_1to0 is None else readout_error_1to0
    if r01 < 0.0 or r01 >= 1.0 or r10 < 0.0 or r10 >= 1.0:
        raise ValueError("readout error probabilities must be within [0, 1)")

    n_data = len(data_indices)
    if n_data == 0:
        return 0.0

    total = sum(counts.values())
    if total == 0:
        return 0.0

    dim = 1 << n_data
    observed = np.zeros(dim, dtype=float)

    for key, count in counts.items():
        bits = bits_for_qubits_from_count_key(key, total_bits)
        data_bits = [bits[i] for i in data_indices]
        obs_idx = _bits_to_index_little_endian(data_bits)
        observed[obs_idx] += count

    observed /= float(total)

    confusion = np.zeros((dim, dim), dtype=float)
    for obs_idx in range(dim):
        obs_bits = _index_to_bits_little_endian(obs_idx, n_data)
        for true_idx in range(dim):
            true_bits = _index_to_bits_little_endian(true_idx, n_data)
            prob = 1.0
            for q in range(n_data):
                if obs_bits[q] == true_bits[q]:
                    if true_bits[q] == 0:
                        prob *= (1.0 - r01)
                    else:
                        prob *= (1.0 - r10)
                else:
                    if true_bits[q] == 0:
                        prob *= r01
                    else:
                        prob *= r10
            confusion[obs_idx, true_idx] = prob

    true_est = np.linalg.pinv(confusion) @ observed
    true_est = np.clip(true_est, 0.0, None)
    norm = float(true_est.sum())
    if norm <= 0.0:
        return 0.0
    true_est /= norm

    success = 0.0
    for true_idx, prob in enumerate(true_est):
        true_bits = _index_to_bits_little_endian(true_idx, n_data)
        logical = majority_vote(true_bits)
        if logical == expected_logical:
            success += float(prob)

    return success


def logical_success_probability_stabilizer_multiround(
    counts: dict[str, int],
    total_bits: int,
    syndrome_rounds: int,
    expected_logical: int,
) -> float:
    if syndrome_rounds < 1:
        raise ValueError("syndrome_rounds must be >= 1")

    total = sum(counts.values())
    if total == 0:
        return 0.0

    data_offset = 2 * syndrome_rounds
    success = 0

    for key, count in counts.items():
        bits = bits_for_qubits_from_count_key(key, total_bits)

        s0_rounds = [bits[2 * r] for r in range(syndrome_rounds)]
        s1_rounds = [bits[2 * r + 1] for r in range(syndrome_rounds)]
        s0 = majority_vote(s0_rounds)
        s1 = majority_vote(s1_rounds)

        error_idx: int | None = None
        if (s1, s0) == (0, 1):
            error_idx = 0
        elif (s1, s0) == (1, 1):
            error_idx = 1
        elif (s1, s0) == (1, 0):
            error_idx = 2

        data_bits = [bits[data_offset + i] for i in range(3)]
        if error_idx is not None:
            data_bits[error_idx] ^= 1

        logical = majority_vote(data_bits)
        if logical == expected_logical:
            success += count

    return success / total
