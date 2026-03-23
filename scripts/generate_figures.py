"""Generate supplementary figures for the paper:
  - Theory vs simulation comparison (side-by-side panels)
  - Circuit diagram schematic (saved as PNG via matplotlib)
  - Scaling trend bar chart
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "src"))
from qc1ec.decode import theoretical_repetition_success


# ── colour palette ──────────────────────────────────────────────────────────
COLOURS = {
    1: "#555555",
    3: "#2196F3",
    5: "#E53935",
}


def _load(experiment: str) -> pd.DataFrame:
    df = pd.read_csv(RESULTS / f"{experiment}_results.csv")
    df["p"] = df["p"].round(4)
    return df


# ── 1. Theory vs Simulation (3-panel) ───────────────────────────────────────
def make_theory_vs_sim() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
    experiments = [
        ("bitflip",      "Bit-flip noise",     ["baseline_n1","bitflip_rep_n3","bitflip_rep_n5"]),
        ("phaseflip",    "Phase-flip noise",   ["baseline_n1","phaseflip_rep_n3","phaseflip_rep_n5"]),
        ("depolarizing", "Depolarizing noise", ["baseline_z_n1","bitflip_rep_n3","bitflip_rep_n5"]),
    ]

    for ax, (exp, title, methods) in zip(axes, experiments):
        df = _load(exp)
        for method in methods:
            sub = df[df["method"] == method].sort_values("p")
            if sub.empty:
                continue
            n = int(sub["n"].iloc[0])
            colour = COLOURS.get(n, "#333333")
            label_n = "baseline" if n == 1 else f"n={n}"

            # Simulated (solid + markers + shaded CI)
            ax.plot(sub["p"], sub["success"], marker="o", markersize=4,
                    color=colour, lw=1.8, label=f"sim {label_n}")
            if "success_ci_lower" in sub.columns:
                ax.fill_between(sub["p"], sub["success_ci_lower"],
                                sub["success_ci_upper"], alpha=0.15, color=colour)
            # Theoretical (dashed)
            if "success_theory" in sub.columns and sub["success_theory"].notna().any():
                ax.plot(sub["p"], sub["success_theory"], linestyle="--",
                        color=colour, lw=1.2, alpha=0.8, label=f"theory {label_n}")

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("Physical error rate  $p$", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0.55, 1.02)

    axes[0].set_ylabel("Logical success probability", fontsize=9)

    # Shared legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5,
               fontsize=8, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Simulation vs Exact Theoretical Prediction\n(dashed = theory, shaded = 95% CI)",
                 fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    out = RESULTS / "theory_vs_sim.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ── 2. Scaling trend bar chart (p = 0.10) ───────────────────────────────────
def make_scaling_bar() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    TARGET_P = 0.10
    experiment_cfg = [
        ("bitflip",      "Bit-flip noise",
         ["baseline_n1","bitflip_rep_n3","bitflip_rep_n5"],
         ["Baseline\n(n=1)", "n=3", "n=5"]),
        ("phaseflip",    "Phase-flip noise",
         ["baseline_n1","phaseflip_rep_n3","phaseflip_rep_n5"],
         ["Baseline\n(n=1)", "n=3", "n=5"]),
        ("depolarizing", "Depolarizing noise",
         ["baseline_z_n1","bitflip_rep_n3","bitflip_rep_n5"],
         ["Baseline\n(n=1)", "n=3", "n=5"]),
    ]

    bar_colours = [COLOURS[k] for k in [1, 3, 5]]

    for ax, (exp, title, methods, xlabels) in zip(axes, experiment_cfg):
        df = _load(exp)
        sub = df[df["p"].round(2) == TARGET_P]
        values, ci_lo, ci_hi = [], [], []
        for m in methods:
            row = sub[sub["method"] == m]
            if row.empty:
                values.append(0); ci_lo.append(0); ci_hi.append(0)
            else:
                v = float(row["success"].iloc[0])
                values.append(v)
                ci_lo.append(v - float(row["success_ci_lower"].iloc[0]))
                ci_hi.append(float(row["success_ci_upper"].iloc[0]) - v)

        xs = range(len(values))
        bars = ax.bar(xs, values, color=bar_colours, edgecolor="white", linewidth=0.8)
        ax.errorbar(xs, values, yerr=[ci_lo, ci_hi], fmt="none",
                    color="black", capsize=4, linewidth=1.2)

        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=7.5)

        ax.set_xticks(list(xs))
        ax.set_xticklabels(xlabels, fontsize=8)
        ax.set_title(f"{title}\n($p = {TARGET_P}$)", fontsize=10, fontweight="bold")
        ax.set_ylim(0.6, 1.05)
        ax.grid(axis="y", alpha=0.3)

    axes[0].set_ylabel("Logical success probability", fontsize=9)
    fig.suptitle("Scaling Trend: Larger Codes Improve Logical Success",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    out = RESULTS / "scaling_bar.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ── 3. Repetition code circuit schematic ────────────────────────────────────
def make_circuit_schematic() -> None:
    """Draw a simple schematic of the 3-qubit repetition code."""
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, 3.5)
    ax.axis("off")

    wire_y = [3.0, 2.0, 1.0]      # qubit wire heights (top = q0, bottom = q2)
    wire_labels = ["$q_0$ (logical)", "$q_1$ (ancilla)", "$q_2$ (ancilla)"]
    colours_wire = ["#1565C0", "#6A1B9A", "#6A1B9A"]

    # Draw wires
    for y, label, c in zip(wire_y, wire_labels, colours_wire):
        ax.annotate("", xy=(9.5, y), xytext=(0.3, y),
                    arrowprops=dict(arrowstyle="-", color=c, lw=1.5))
        ax.text(0.1, y, label, ha="right", va="center", fontsize=9, color=c)

    def box(x, y, text, bg="#E3F2FD", width=0.55, height=0.45):
        rect = mpatches.FancyBboxPatch((x - width/2, y - height/2), width, height,
                                       boxstyle="round,pad=0.05",
                                       facecolor=bg, edgecolor="#333", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center", fontsize=9, fontweight="bold")

    def cnot(x, ctrl_y, tgt_y):
        # control dot
        ax.plot(x, ctrl_y, "o", color="#333", markersize=7, zorder=5)
        # target circle with X
        circle = plt.Circle((x, tgt_y), 0.18, color="#333", fill=False, linewidth=1.5, zorder=5)
        ax.add_patch(circle)
        ax.plot([x - 0.18, x + 0.18], [tgt_y, tgt_y], color="#333", lw=1.5, zorder=5)
        ax.plot([x, x], [tgt_y - 0.18, tgt_y + 0.18], color="#333", lw=1.5, zorder=5)
        # vertical line
        ax.plot([x, x], [ctrl_y, tgt_y], color="#333", lw=1.5, zorder=4)

    def measure(x, y, label="M"):
        rect = mpatches.FancyBboxPatch((x - 0.3, y - 0.22), 0.6, 0.44,
                                       boxstyle="round,pad=0.04",
                                       facecolor="#FFF9C4", edgecolor="#F57F17", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=8)

    # ── Encode region ──
    ax.axvspan(0.4, 2.8, alpha=0.06, color="#1565C0")
    ax.text(1.6, 3.4, "Encode", ha="center", fontsize=9, color="#1565C0", style="italic")
    # |0⟩ initialise on q0
    box(0.75, wire_y[0], "$|0\\rangle$", bg="#E3F2FD")
    # |0⟩ on q1, q2
    box(0.75, wire_y[1], "$|0\\rangle$", bg="#F3E5F5")
    box(0.75, wire_y[2], "$|0\\rangle$", bg="#F3E5F5")
    # CNOT q0→q1
    cnot(1.9, wire_y[0], wire_y[1])
    # CNOT q0→q2
    cnot(2.5, wire_y[0], wire_y[2])

    # ── Noise region ──
    ax.axvspan(2.9, 6.2, alpha=0.07, color="#FF5722")
    ax.text(4.55, 3.4, "Noise (idle steps)", ha="center", fontsize=9, color="#BF360C", style="italic")
    for yi in wire_y:
        for xi in [3.4, 4.1, 4.8, 5.5]:
            box(xi, yi, "$I$", bg="#FFE0B2", width=0.4, height=0.38)
        # small X error symbol on q1 at one step
    ax.text(4.1, wire_y[1] - 0.38, "X?", ha="center", fontsize=7.5, color="#BF360C")

    # ── Decode (majority vote) ──
    ax.axvspan(6.3, 9.4, alpha=0.06, color="#2E7D32")
    ax.text(7.85, 3.4, "Decode", ha="center", fontsize=9, color="#2E7D32", style="italic")
    for yi in wire_y:
        measure(6.8, yi)
    # Majority vote box
    rect = mpatches.FancyBboxPatch((7.3, 1.6), 1.8, 1.2,
                                   boxstyle="round,pad=0.08",
                                   facecolor="#C8E6C9", edgecolor="#2E7D32", linewidth=1.5)
    ax.add_patch(rect)
    ax.text(8.2, 2.2, "Majority\nVote", ha="center", va="center",
            fontsize=9, fontweight="bold", color="#1B5E20")
    for yi in wire_y:
        ax.annotate("", xy=(7.3, 2.2), xytext=(7.1, yi),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=0.9))
    # Output
    ax.annotate("", xy=(9.4, 2.2), xytext=(9.1, 2.2),
                arrowprops=dict(arrowstyle="->", color="#2E7D32", lw=1.5))
    ax.text(9.6, 2.2, "Logical\nbit", ha="left", va="center", fontsize=9, color="#2E7D32")

    fig.suptitle("3-Qubit Bit-Flip Repetition Code: Encode → Noise → Measure → Majority Vote",
                 fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()
    out = RESULTS / "circuit_schematic.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


if __name__ == "__main__":
    print("Generating figures...")
    make_circuit_schematic()
    make_theory_vs_sim()
    make_scaling_bar()
    print("All figures done.")
