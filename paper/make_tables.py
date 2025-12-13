from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUTDIR = Path(__file__).resolve().parent / "tables"


def _format_df_for_tex(df: pd.DataFrame) -> pd.DataFrame:
    # Keep a compact subset of p values (article-friendly).
    keep = [0.00, 0.02, 0.04, 0.06, 0.08]
    df = df[df["p"].round(2).isin(keep)].copy()
    df["p"] = df["p"].round(2)
    return df


def write_bit_or_phase_table(kind: str) -> None:
    df = pd.read_csv(RESULTS / f"{kind}_results.csv")

    baseline = df[df.method == "baseline_n1"].set_index("p")["success"]
    n3 = df[df.method.str.contains("_n3")].set_index("p")["success"]
    n5 = df[df.method.str.contains("_n5")].set_index("p")["success"]

    out = pd.DataFrame(
        {
            "p": baseline.index,
            "baseline (n=1)": baseline.values,
            "repetition (n=3)": n3.reindex(baseline.index).values,
            "repetition (n=5)": n5.reindex(baseline.index).values,
        }
    )
    out["gain n=5"] = out["repetition (n=5)"] - out["baseline (n=1)"]
    out = _format_df_for_tex(out)

    path = OUTDIR / f"{kind}_summary.tex"
    tex = out.to_latex(
        index=False,
        float_format=lambda x: f"{x:.4f}",
        escape=False,
        caption=(
            "Logical success probability vs physical error probability $p$ "
            "for baseline and repetition-code error correction."
        ),
        label=f"tab:{kind}-summary",
    )

    # Use booktabs if available in the user's LaTeX distribution.
    tex = tex.replace("\\toprule", "\\toprule")
    path.write_text(tex, encoding="utf-8")


def write_depolarizing_table() -> None:
    df = pd.read_csv(RESULTS / "depolarizing_results.csv")

    # For depolarizing case in this project, the best method is the X-basis repetition (phaseflip_rep_*).
    pivot = df.pivot_table(index="p", columns="method", values="success")
    out = pd.DataFrame(
        {
            "p": pivot.index,
            r"baseline\_n1": pivot.get("baseline_n1"),
            r"phaseflip\_rep\_n3": pivot.get("phaseflip_rep_n3"),
            r"phaseflip\_rep\_n5": pivot.get("phaseflip_rep_n5"),
            r"bitflip\_rep\_n3": pivot.get("bitflip_rep_n3"),
            r"bitflip\_rep\_n5": pivot.get("bitflip_rep_n5"),
        }
    )
    out = _format_df_for_tex(out)

    path = OUTDIR / "depolarizing_summary.tex"
    tex = out.to_latex(
        index=False,
        float_format=lambda x: f"{x:.4f}" if pd.notna(x) else "",
        escape=False,
        caption=(
            r"Depolarizing noise results. Note that Z-basis repetition (bitflip\_rep\_*) is mismatched "
            r"to the stored $|+\rangle$ state in this experiment, giving $\approx 0.5$ even at $p=0$."
        ),
        label="tab:depolarizing-summary",
    )
    path.write_text(tex, encoding="utf-8")


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    write_bit_or_phase_table("bitflip")
    write_bit_or_phase_table("phaseflip")
    write_depolarizing_table()
    print(f"Wrote tables to: {OUTDIR}")


if __name__ == "__main__":
    main()
