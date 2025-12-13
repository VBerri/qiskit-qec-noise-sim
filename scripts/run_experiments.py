from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running this script without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qc1ec.experiments import run_and_save


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Qiskit/Aer repetition-code error-correction comparisons.")
    parser.add_argument(
        "--experiment",
        required=True,
        choices=["bitflip", "phaseflip", "depolarizing"],
        help="Noise type / scenario to run.",
    )
    parser.add_argument("--shots", type=int, default=4000)
    parser.add_argument("--idle-steps", type=int, default=4, help="How many noisy idle steps to apply.")
    parser.add_argument(
        "--p-min",
        type=float,
        default=0.0,
        help="Minimum physical error probability.",
    )
    parser.add_argument(
        "--p-max",
        type=float,
        default=0.08,
        help="Maximum physical error probability.",
    )
    parser.add_argument(
        "--p-steps",
        type=int,
        default=9,
        help="Number of points between p-min and p-max (inclusive).",
    )
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--outdir", default="results")

    args = parser.parse_args()

    run_and_save(
        experiment=args.experiment,
        shots=args.shots,
        idle_steps=args.idle_steps,
        p_min=args.p_min,
        p_max=args.p_max,
        p_steps=args.p_steps,
        seed=args.seed,
        outdir=args.outdir,
    )


if __name__ == "__main__":
    main()
