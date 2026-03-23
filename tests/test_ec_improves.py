from __future__ import annotations

import pandas as pd

from qc1ec.decode import logical_success_probability_postselected
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


def test_depolarizing_has_basis_matched_baselines() -> None:
    p = 0.03
    df = run_experiment(
        experiment="depolarizing",
        shots=500,
        idle_steps=2,
        p_values=[p],
        seed=789,
    )

    methods = set(df["method"].unique())
    assert "baseline_z_n1" in methods
    assert "baseline_x_n1" in methods


def test_method_state_matches_basis_in_depolarizing() -> None:
    p = 0.03
    df = run_experiment(
        experiment="depolarizing",
        shots=500,
        idle_steps=2,
        p_values=[p],
        seed=999,
    )

    z_states = set(df[df["basis"] == "Z"]["state"].unique())
    x_states = set(df[df["basis"] == "X"]["state"].unique())

    assert z_states == {"0"}
    assert x_states == {"plus"}


def test_bitflip_n5_scaling_improves_vs_n3_and_baseline() -> None:
    p = 0.08
    df = run_experiment(
        experiment="bitflip",
        shots=2000,
        idle_steps=4,
        p_values=[p],
        seed=1234,
    )

    baseline = _success_at(df, "baseline_n1", p)
    rep3 = _success_at(df, "bitflip_rep_n3", p)
    rep5 = _success_at(df, "bitflip_rep_n5", p)

    assert rep3 > baseline
    assert rep5 >= rep3


def test_phaseflip_n5_scaling_improves_vs_n3_and_baseline() -> None:
    p = 0.08
    df = run_experiment(
        experiment="phaseflip",
        shots=2000,
        idle_steps=4,
        p_values=[p],
        seed=5678,
    )

    baseline = _success_at(df, "baseline_n1", p)
    rep3 = _success_at(df, "phaseflip_rep_n3", p)
    rep5 = _success_at(df, "phaseflip_rep_n5", p)

    assert rep3 > baseline
    assert rep5 >= rep3


def test_depolarizing_n5_near_zero_logical_error_at_low_p() -> None:
    p = 0.02
    df = run_experiment(
        experiment="depolarizing",
        shots=4000,
        idle_steps=4,
        p_values=[p],
        seed=12345,
    )

    bitflip_n5 = _success_at(df, "bitflip_rep_n5", p)
    phaseflip_n5 = _success_at(df, "phaseflip_rep_n5", p)

    assert bitflip_n5 >= 0.985
    assert phaseflip_n5 >= 0.985


def test_postselect_decoder_kept_fraction_less_than_one_when_filtering() -> None:
    counts = {
        "00000": 50,
        "11100": 30,
        "00111": 20,
    }
    success, kept = logical_success_probability_postselected(
        counts,
        total_bits=5,
        data_indices=(0, 1, 2, 3, 4),
        expected_logical=0,
        min_majority_margin=3,
    )
    assert 0.0 <= success <= 1.0
    assert 0.0 < kept < 1.0


def test_postselection_improves_n5_logical_success_with_tradeoff() -> None:
    p = 0.08
    df_majority = run_experiment(
        experiment="bitflip",
        shots=4000,
        idle_steps=4,
        p_values=[p],
        seed=4242,
        decode_mode="majority",
    )
    df_post = run_experiment(
        experiment="bitflip",
        shots=4000,
        idle_steps=4,
        p_values=[p],
        seed=4242,
        decode_mode="postselect",
        postselect_margin=3,
    )

    maj_n5 = _success_at(df_majority, "bitflip_rep_n5", p)
    post_n5 = _success_at(df_post, "bitflip_rep_n5", p)
    kept_n5 = float(df_post[(df_post["method"] == "bitflip_rep_n5") & (df_post["p"] == p)].iloc[0]["kept_fraction"])

    assert post_n5 > maj_n5
    assert kept_n5 < 1.0


def test_map_decoder_mode_runs_and_returns_valid_scores() -> None:
    p = 0.06
    df = run_experiment(
        experiment="bitflip",
        shots=1200,
        idle_steps=4,
        p_values=[p],
        seed=2026,
        decode_mode="map",
        readout_error_p=0.05,
    )

    assert set(df["decode_mode"].unique()) == {"map"}
    assert (df["success"] >= 0.0).all()
    assert (df["success"] <= 1.0).all()


def test_stabilizer_rounds_parameter_is_applied() -> None:
    p = 0.06
    df = run_experiment(
        experiment="bitflip",
        shots=1000,
        idle_steps=3,
        p_values=[p],
        seed=2027,
        decode_mode="majority",
        stabilizer_rounds=2,
    )

    # stabilizer not included in main experiment; verify n=5 row is present
    row = df[(df["method"] == "bitflip_rep_n5") & (df["p"] == p)].iloc[0]
    assert int(row["stabilizer_rounds"]) == 2
    assert 0.0 <= float(row["success"]) <= 1.0


def test_readout_mitigation_improves_baseline_when_readout_noise_present() -> None:
    p = 0.0
    common = dict(
        experiment="bitflip",
        shots=4000,
        idle_steps=0,
        p_values=[p],
        seed=2028,
        decode_mode="majority",
        readout_error_p=0.12,
    )

    df_no_mit = run_experiment(**common, use_readout_mitigation=False)
    df_mit = run_experiment(**common, use_readout_mitigation=True)

    baseline_no_mit = _success_at(df_no_mit, "baseline_n1", p)
    baseline_mit = _success_at(df_mit, "baseline_n1", p)

    assert baseline_mit > baseline_no_mit
    assert baseline_mit > 0.95


def test_readout_mitigation_handles_asymmetric_readout_noise() -> None:
    p = 0.0
    common = dict(
        experiment="bitflip",
        shots=5000,
        idle_steps=0,
        p_values=[p],
        seed=2029,
        decode_mode="majority",
        readout_error_p=0.0,
        readout_error_0to1=0.18,
        readout_error_1to0=0.04,
    )

    df_no_mit = run_experiment(**common, use_readout_mitigation=False)
    df_mit = run_experiment(**common, use_readout_mitigation=True)

    baseline_no_mit = _success_at(df_no_mit, "baseline_n1", p)
    baseline_mit = _success_at(df_mit, "baseline_n1", p)
    assert baseline_mit > baseline_no_mit


def test_multi_round_stabilizer_n5_improves_with_readout_noise() -> None:
    p = 0.06
    common = dict(
        experiment="bitflip",
        shots=5000,
        idle_steps=3,
        p_values=[p],
        seed=2030,
        decode_mode="majority",
        readout_error_p=0.12,
    )

    df_r1 = run_experiment(**common, stabilizer_rounds=1)
    df_r3 = run_experiment(**common, stabilizer_rounds=3)

    # n=5 rep code should still perform well with readout noise
    s1 = _success_at(df_r1, "bitflip_rep_n5", p)
    s3 = _success_at(df_r3, "bitflip_rep_n5", p)
    assert s1 >= 0.7
    assert s3 >= 0.7
