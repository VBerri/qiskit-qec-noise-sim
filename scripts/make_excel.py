"""Generate a publication-ready Excel workbook from experiment CSVs.

Sheets produced
---------------
1. README          – Legend explaining all columns and sheet structure
2. Bitflip         – Full bitflip results (all methods, all p-values)
3. Phaseflip       – Full phaseflip results
4. Depolarizing    – Full depolarizing results
5. Summary_Bitflip – Pivoted table: one column per method, rows = p-values
6. Summary_Phaseflip
7. Summary_Depolarizing
8. Theory_vs_Sim   – Side-by-side simulated vs theoretical for repetition codes
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

sys.path.insert(0, str(ROOT / "src"))
from qc1ec.decode import theoretical_repetition_success  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(experiment: str) -> pd.DataFrame:
    path = RESULTS / f"{experiment}_results.csv"
    if not path.exists():
        raise FileNotFoundError(f"Results not found: {path}\nRun the experiment first.")
    df = pd.read_csv(path)
    # Round p to avoid floating-point noise in groupby/pivot
    df["p"] = df["p"].round(4)
    return df


def _pivot(df: pd.DataFrame, value_col: str = "success") -> pd.DataFrame:
    """Pivot to methods-as-columns, p-as-rows."""
    return df.pivot_table(index="p", columns="method", values=value_col).reset_index()


def _apply_header_format(ws, workbook, cols: int) -> None:
    header_fmt = workbook.add_format({
        "bold": True,
        "bg_color": "#1F4E79",
        "font_color": "#FFFFFF",
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
    })
    for col in range(cols):
        cell = ws.cell_if_any  # not used directly — handled via set_column
    return header_fmt


def _write_df(writer: pd.ExcelWriter, df: pd.DataFrame, sheet_name: str,
              freeze: bool = True) -> None:
    """Write a DataFrame to a sheet with auto column widths and header formatting."""
    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
    wb = writer.book
    ws = writer.sheets[sheet_name]

    # Header format
    header_fmt = wb.add_format({
        "bold": True,
        "bg_color": "#1F4E79",
        "font_color": "#FFFFFF",
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
    })
    # Alternating row formats
    even_fmt = wb.add_format({"bg_color": "#DCE6F1", "border": 1, "num_format": "0.0000"})
    odd_fmt  = wb.add_format({"border": 1, "num_format": "0.0000"})
    text_even = wb.add_format({"bg_color": "#DCE6F1", "border": 1})
    text_odd  = wb.add_format({"border": 1})

    # Write headers
    for col_idx, col_name in enumerate(df.columns):
        ws.write(0, col_idx, col_name, header_fmt)

    # Write data rows with alternating colours
    for row_idx, row in enumerate(df.itertuples(index=False), start=1):
        is_even = (row_idx % 2 == 0)
        for col_idx, value in enumerate(row):
            col_name = df.columns[col_idx]
            if isinstance(value, float) and not math.isnan(value):
                fmt = even_fmt if is_even else odd_fmt
            else:
                fmt = text_even if is_even else text_odd
            ws.write(row_idx, col_idx, value, fmt)

    # Auto-fit column widths
    for col_idx, col_name in enumerate(df.columns):
        max_len = max(
            len(str(col_name)),
            df[col_name].astype(str).str.len().max() if len(df) > 0 else 0,
        )
        ws.set_column(col_idx, col_idx, min(max_len + 2, 30))

    if freeze:
        ws.freeze_panes(1, 0)


def _write_readme(writer: pd.ExcelWriter) -> None:
    wb = writer.book
    ws = wb.add_worksheet("README")
    writer.sheets["README"] = ws

    title_fmt = wb.add_format({"bold": True, "font_size": 14, "font_color": "#1F4E79"})
    h2_fmt    = wb.add_format({"bold": True, "font_size": 11, "bg_color": "#BDD7EE"})
    body_fmt  = wb.add_format({"text_wrap": True})
    key_fmt   = wb.add_format({"bold": True, "font_color": "#375623"})

    rows = [
        ("TITLE",   "Quantum Error Correction: Scaling Repetition Codes — Results Workbook"),
        ("AUTHORS", "Sanjeev Tamilselvan & Tanuj Ranjith"),
        ("DATE",    "2025"),
        ("",        ""),
        ("SHEET GUIDE", ""),
        ("Bitflip / Phaseflip / Depolarizing",
         "Full raw results: one row per (method, p-value). "
         "Includes 95% Wilson confidence intervals and theoretical predictions."),
        ("Summary_*",
         "Pivoted view: rows = physical error rate p, columns = code method. "
         "Easier to read for comparison tables in a paper."),
        ("Theory_vs_Sim",
         "Direct comparison of simulated logical success vs exact binomial formula "
         "for all repetition code sizes and noise types."),
        ("", ""),
        ("COLUMN GLOSSARY", ""),
        ("experiment",         "Noise scenario: bitflip | phaseflip | depolarizing"),
        ("noise",              "Noise type applied to idle gates"),
        ("p",                  "Physical error probability per idle step"),
        ("shots",              "Number of simulation shots (circuit executions)"),
        ("idle_steps",         "Number of noisy idle steps between encode and measure"),
        ("method",             "Circuit method name (baseline_n1, bitflip_rep_n3, …)"),
        ("n",                  "Number of physical (data) qubits in the code"),
        ("basis",              "Encoding basis: Z (bit-flip protection) or X (phase-flip)"),
        ("state",              "Logical input state: 0/plus (logical 0) or 1/minus (logical 1)"),
        ("decode_mode",        "Decoder: majority | postselect | map"),
        ("success",            "Fraction of shots decoded to the correct logical value"),
        ("success_ci_lower",   "Lower bound of 95% Wilson confidence interval"),
        ("success_ci_upper",   "Upper bound of 95% Wilson confidence interval"),
        ("success_theory",     "Exact theoretical prediction (binomial formula). NaN for stabilizer codes."),
        ("kept_fraction",      "Fraction of shots kept after post-selection (1.0 for majority/map)"),
        ("readout_error_p",    "Symmetric readout flip probability (0 = ideal measurement)"),
        ("readout_mitigated",  "Whether confusion-matrix readout mitigation was applied"),
        ("stabilizer_rounds",  "Number of syndrome extraction rounds"),
        ("", ""),
        ("NOISE MODELS", ""),
        ("Bit-flip",       "Pauli-X error with prob p applied to each qubit each idle step"),
        ("Phase-flip",     "Pauli-Z error with prob p applied to each qubit each idle step"),
        ("Depolarizing",   "Depolarizing error (X/Y/Z equally likely) with prob p per idle step"),
        ("", ""),
        ("THEORETICAL FORMULA", ""),
        ("Repetition code", "P_fail(p,n) = Σ C(n,k)·p_eff^k·(1-p_eff)^(n-k)  for k ≥ ⌈(n+1)/2⌉"),
        ("",                "where p_eff is the per-qubit flip probability accumulated over idle steps"),
        ("Baseline (n=1)", "P_success = 1 − p_eff"),
    ]

    ws.set_column(0, 0, 28)
    ws.set_column(1, 1, 72)

    for r, (key, val) in enumerate(rows):
        if key in ("TITLE", "AUTHORS", "DATE"):
            ws.write(r, 0, key, key_fmt)
            ws.write(r, 1, val, title_fmt if key == "TITLE" else body_fmt)
        elif val == "" and key != "":
            ws.merge_range(r, 0, r, 1, key, h2_fmt)
        elif key == "":
            pass
        else:
            ws.write(r, 0, key, key_fmt)
            ws.write(r, 1, val, body_fmt)

    ws.set_row(0, 20)


def _make_theory_sheet(writer: pd.ExcelWriter) -> None:
    """Build Theory vs Simulation comparison across all experiments."""
    records = []
    for experiment in ("bitflip", "phaseflip", "depolarizing"):
        df = _load(experiment)
        rep_methods = df[df["method"].str.contains("rep_n")].copy()
        for _, row in rep_methods.iterrows():
            records.append({
                "experiment":    row["experiment"],
                "noise":         row["noise"],
                "p":             row["p"],
                "method":        row["method"],
                "n":             int(row["n"]),
                "basis":         row["basis"],
                "shots":         int(row["shots"]),
                "success_sim":   row["success"],
                "ci_lower":      row.get("success_ci_lower", float("nan")),
                "ci_upper":      row.get("success_ci_upper", float("nan")),
                "success_theory": row.get("success_theory", float("nan")),
                "sim_minus_theory": (
                    row["success"] - row.get("success_theory", float("nan"))
                    if not math.isnan(row.get("success_theory", float("nan")))
                    else float("nan")
                ),
            })

    theory_df = pd.DataFrame(records).sort_values(["experiment", "n", "p"])
    _write_df(writer, theory_df, "Theory_vs_Sim")


def _make_summary_sheet(writer: pd.ExcelWriter, experiment: str) -> None:
    df = _load(experiment)

    # Pivot success
    pivot_s = _pivot(df, "success")
    # Pivot CI lower
    pivot_lo = _pivot(df, "success_ci_lower") if "success_ci_lower" in df.columns else None
    # Pivot CI upper
    pivot_hi = _pivot(df, "success_ci_upper") if "success_ci_upper" in df.columns else None
    # Pivot theory
    pivot_th = _pivot(df, "success_theory") if "success_theory" in df.columns else None

    # Assemble: for each method, add success / ci_lower / ci_upper / theory columns
    result = pivot_s[["p"]].copy()
    for method in [c for c in pivot_s.columns if c != "p"]:
        result[f"{method}__success"]   = pivot_s[method]
        if pivot_lo is not None:
            result[f"{method}__ci_low"]  = pivot_lo.get(method, float("nan"))
            result[f"{method}__ci_high"] = pivot_hi.get(method, float("nan"))
        if pivot_th is not None:
            result[f"{method}__theory"]  = pivot_th.get(method, float("nan"))

    _write_df(writer, result, f"Summary_{experiment.capitalize()}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    out_path = RESULTS / "QEC_Results_Submission.xlsx"
    print("Running experiments check...")

    # Verify all CSVs exist
    for exp in ("bitflip", "phaseflip", "depolarizing"):
        _load(exp)  # raises FileNotFoundError if missing

    print(f"Generating Excel workbook -> {out_path}")

    with pd.ExcelWriter(out_path, engine="xlsxwriter",
                        engine_kwargs={"options": {"nan_inf_to_errors": True}}) as writer:
        # 1. README sheet
        _write_readme(writer)

        # 2. Full raw results per experiment
        for exp in ("bitflip", "phaseflip", "depolarizing"):
            df = _load(exp)
            # Drop the raw counts string (too wide for Excel)
            display_cols = [c for c in df.columns if c != "counts"]
            _write_df(writer, df[display_cols], exp.capitalize())

        # 3. Summary (pivoted) sheets
        for exp in ("bitflip", "phaseflip", "depolarizing"):
            _make_summary_sheet(writer, exp)

        # 4. Theory vs Simulation sheet
        _make_theory_sheet(writer)

    print(f"\nDone!  Workbook saved to:\n  {out_path}")
    print("\nSheets:")
    print("  README              — column glossary & formula reference")
    print("  Bitflip             — full bitflip raw results")
    print("  Phaseflip           — full phaseflip raw results")
    print("  Depolarizing        — full depolarizing raw results")
    print("  Summary_Bitflip     — pivoted comparison table")
    print("  Summary_Phaseflip   — pivoted comparison table")
    print("  Summary_Depolarizing— pivoted comparison table")
    print("  Theory_vs_Sim       — simulation vs exact binomial prediction")


if __name__ == "__main__":
    main()
