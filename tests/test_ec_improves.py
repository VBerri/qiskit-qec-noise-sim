from __future__ import annotations

import pandas as pd

from qc1ec.experiments import run_experiment


def _success_at(df: pd.DataFrame, method: str, p: float) -> float:
    row = df[(df["method"] == method) & (df["p"] == p)].iloc[0]
    return float(row["success"])


def test_bitflip_repetition_improves_under_x_noise() -> None:
    p = 0.06
    df = run_experiment(
        experiment="bitflip",
        shots=1000,
        idle_steps=3,
        p_values=[p],
        seed=123,
    )

    baseline = _success_at(df, "baseline_n1", p)
    rep3 = _success_at(df, "bitflip_rep_n3", p)

    assert rep3 > baseline


def test_phaseflip_repetition_improves_under_z_noise() -> None:
    p = 0.06
    df = run_experiment(
        experiment="phaseflip",
        shots=1000,
        idle_steps=3,
        p_values=[p],
        seed=456,
    )

    baseline = _success_at(df, "baseline_n1", p)
    rep3 = _success_at(df, "phaseflip_rep_n3", p)

    assert rep3 > baseline
