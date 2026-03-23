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
    parser.add_argument(
        "--decode-mode",
        choices=["majority", "postselect", "map"],
        default="majority",
        help="Decoder type: majority vote, confidence post-selection, or MAP (noise-aware).",
    )
    parser.add_argument(
        "--postselect-margin",
        type=int,
        default=None,
        help="Minimum vote margin to keep a shot when decode-mode=postselect (default auto: 3 for n>1).",
    )
    parser.add_argument(
        "--readout-error-p",
        type=float,
        default=0.0,
        help="Symmetric readout flip probability per qubit in [0,0.5).",
    )
    parser.add_argument(
        "--readout-error-0to1",
        type=float,
        default=None,
        help="Asymmetric readout probability P(measure 1 | true 0). Overrides --readout-error-p for 0->1.",
    )
    parser.add_argument(
        "--readout-error-1to0",
        type=float,
        default=None,
        help="Asymmetric readout probability P(measure 0 | true 1). Overrides --readout-error-p for 1->0.",
    )
    parser.add_argument(
        "--readout-mitigation",
        action="store_true",
        help="Apply readout-mitigation correction (currently with majority decoder).",
    )
    parser.add_argument(
        "--stabilizer-rounds",
        type=int,
        default=1,
        help="Number of repeated stabilizer syndrome rounds for stabilizer methods.",
    )
    parser.add_argument(
        "--single-qubit-gate-error-p",
        type=float,
        default=0.0,
        help="Depolarizing error probability for single-qubit non-id gates (x,z,h).",
    )
    parser.add_argument(
        "--cx-gate-error-p",
        type=float,
        default=0.0,
        help="Depolarizing error probability for cx gates.",
    )

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
        decode_mode=args.decode_mode,
        postselect_margin=args.postselect_margin,
        readout_error_p=args.readout_error_p,
        readout_error_0to1=args.readout_error_0to1,
        readout_error_1to0=args.readout_error_1to0,
        use_readout_mitigation=args.readout_mitigation,
        stabilizer_rounds=args.stabilizer_rounds,
        single_qubit_gate_error_p=args.single_qubit_gate_error_p,
        cx_gate_error_p=args.cx_gate_error_p,
    )


if __name__ == "__main__":
    main()
