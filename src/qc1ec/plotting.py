from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_success_curves(df: pd.DataFrame, *, title: str, out_png: Path) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)

    has_ci = "success_ci_lower" in df.columns and "success_ci_upper" in df.columns
    has_theory = "success_theory" in df.columns

    fig, ax = plt.subplots(figsize=(8, 5))

    theory_plotted: set[str] = set()

    for method_name, group in df.groupby("method"):
        group_sorted = group.sort_values("p")
        p_vals = group_sorted["p"]
        s_vals = group_sorted["success"]

        if has_ci:
            yerr_low = (s_vals - group_sorted["success_ci_lower"]).clip(lower=0)
            yerr_high = (group_sorted["success_ci_upper"] - s_vals).clip(lower=0)
            line = ax.errorbar(
                p_vals,
                s_vals,
                yerr=[yerr_low, yerr_high],
                marker="o",
                capsize=3,
                label=method_name,
            )
            color = line[0].get_color()
        else:
            (line,) = ax.plot(p_vals, s_vals, marker="o", label=method_name)
            color = line.get_color()

        # Overlay theoretical curve for repetition codes (dashed, same colour).
        if has_theory:
            theory_vals = group_sorted["success_theory"]
            if theory_vals.notna().any() and method_name not in theory_plotted:
                ax.plot(
                    p_vals,
                    theory_vals,
                    linestyle="--",
                    color=color,
                    alpha=0.6,
                    label=f"{method_name} (theory)",
                )
                theory_plotted.add(method_name)

    ax.set_xlabel("Physical error probability p")
    ax.set_ylabel("Logical success probability")

    y_min = float(df["success"].min())
    y_max = float(df["success"].max())
    if (y_max - y_min) < 0.2:
        pad = 0.02
        ax.set_ylim(max(0.0, y_min - pad), min(1.02, y_max + pad))
    else:
        ax.set_ylim(0.0, 1.02)

    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(out_png, dpi=180)
    plt.close(fig)
