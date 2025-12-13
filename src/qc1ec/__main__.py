from __future__ import annotations

from qc1ec.experiments import run_and_save


def main() -> None:
    # Convenience entrypoint for quick manual runs.
    run_and_save(
        experiment="bitflip",
        shots=2000,
        idle_steps=3,
        p_min=0.0,
        p_max=0.08,
        p_steps=9,
        seed=12345,
        outdir="results",
    )


if __name__ == "__main__":
    main()
