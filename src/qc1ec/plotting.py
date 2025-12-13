from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_success_curves(df: pd.DataFrame, *, title: str, out_png: Path) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))

    # One line per method.
    for method_name, group in df.groupby("method"):
        group_sorted = group.sort_values("p")
        plt.plot(group_sorted["p"], group_sorted["success"], marker="o", label=method_name)

    plt.xlabel("Physical error probability p")
    plt.ylabel("Logical success probability")
    plt.ylim(0.0, 1.02)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=180)
    plt.close()
