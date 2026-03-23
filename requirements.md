Here’s a proposal-style plan your son can use for Idea B: “Which algorithm survives noise best?” written so it sounds like a real, doable high-school research mini-project (but still connected to what CIPHER QSD does).

Project Title (pick one)

Gate Depth vs. Fidelity: Which Quantum Circuits Survive Noise Best?

How Circuit Length Affects Quantum Algorithm Accuracy Under Noise

A Small-Algorithm Noise Study Inspired by Trapped-Ion Quantum Systems

Big Idea (1–2 sentences)

Quantum computers make mistakes because of noise. This project tests the simple hypothesis: circuits with more gates (more steps) usually lose accuracy faster. The goal is to measure and compare how quickly different small circuits “break” as noise increases.

Research Question

How does circuit complexity (gate count / depth) change the fidelity (success rate) of a quantum algorithm under different noise levels?

Hypothesis

Circuit 2 (longer/deeper) will show lower fidelity than Circuit 1 (shorter) under the same noise because each extra gate is another chance for error.

What “Fidelity” Means Here (simple)

Fidelity = “How often do we get the expected answer?”

If a circuit should output 00 most of the time, and it does 80%, fidelity is high.

If it only does 30%, fidelity is low.

Tools (simple + realistic)

Qiskit (IBM’s open-source quantum toolkit)

Either:

A simulator with noise models (most reliable for experiments), and optionally

A few runs on real IBM hardware (nice bonus; hardware is noisy like real devices)

Experimental Design
Step 1 — Choose two circuits (same goal, different complexity)

Pick a task with a clear “expected result,” then create:

Circuit 1 (short):

Minimal gates to achieve the goal.

Circuit 2 (long):

Same goal, but add extra gates that ideally “cancel out” (so in a perfect world it should still give the same answer).

Example idea: add pairs like X then X (should return to original) or H then H, or add extra swaps, etc.
In real noisy systems, these “extra steps” still introduce error.

Good circuit goals:

Create a Bell pair (entanglement) and measure correlations.

Prepare a known state and measure whether you get the right bitstring.

Simple algorithm like a tiny “Deutsch-Jozsa style” example (but that can be more complex to explain).

Easy + clean choice: Bell state experiment

Expected behavior: measurements should mostly be 00 or 11, not 01/10.

Step 2 — Define “complexity” metrics

Track:

Gate count (total gates)

Circuit depth (how many layers of operations)

Step 3 — Add noise in controlled levels

Use a noise model and adjust a “noise strength knob,” for example:

Depolarizing noise (randomly flips/qubit errors)

Readout error (measurement mistakes)

Amplitude/phase damping (more “physics-like”)

Noise levels: choose something like 5–8 steps (example)

0.0 (no noise)

0.001

0.002

0.005

0.01

0.02

0.05

Step 4 — Run trials and compute fidelity

For each circuit and each noise level:

Run N shots (e.g., 2000 shots)

Compute fidelity:

If Bell test: fidelity = P(00) + P(11)

If known target state: fidelity = P(target bitstring)

Repeat each condition 3 times (optional) to show consistency.

Step 5 — Analyze results

Make 1–2 graphs:

Fidelity vs Noise Strength (Circuit 1 and Circuit 2 on same plot)

Fidelity vs Depth (optional)

Expected pattern:

Circuit 1 drops slowly

Circuit 2 drops faster

Step 6 — (Optional bonus) Compare with real device runs

Pick 1–2 noise levels (or just run both circuits on hardware).

Real device results will be noisier and lower fidelity overall.

This makes the project feel closer to real trapped-ion concerns, even if IBM devices are not trapped-ion.

Why this connects to CIPHER QSD (say this clearly)

QSD studies small quantum algorithms and measures how noise affects fidelity. This project mimics that exact workflow by:

Running small circuits

Varying noise

Measuring fidelity

Connecting results to circuit design choices (gate count/depth)

Deliverables (what he will produce)

Short proposal (1 page)

Two circuits documented and explained

Dataset table (noise level, fidelity for each circuit)

Graph(s) of results

Short conclusion: what design choices improve robustness

Timeline (8–20 hrs/week friendly)

Week 1: Setup + choose circuits

Install Qiskit, run basic circuits

Finalize Circuit 1 and Circuit 2

Decide fidelity metric

Week 2: Noise experiments

Implement noise model

Run across noise levels

Store results

Week 3: Analysis + plots

Graph fidelity curves

Write “what it means” explanation

Check if results match hypothesis

Week 4: Polish + optional hardware run

Run on IBM hardware (optional)

Final report + proposal + slides

Possible Extensions (if he wants it to sound more “researchy”)

Add a third circuit: same depth but different gate types (some gates may be more error-prone)

Test error mitigation (simple readout mitigation) and see if fidelity improves

Compare two different noise models (readout vs depolarizing)

If you want, I can turn this into a one-page “official proposal” your son can submit (with sections: Background, Research Question, Methods, Tools, Expected Outcomes, and Relevance to QSD).

You said:
Can this be simulated in IBM Qiskit or Google Cirq?
ChatGPT said:

Yes — you can do this in both IBM Qiskit and Google Cirq.

IBM Qiskit (easiest for “noise vs fidelity” experiments)

Best parts for your project:

Qiskit Aer can run circuits with custom noise models (depolarizing, amplitude damping, readout/measurement error, etc.).

You can also run the same circuits on real IBM quantum hardware (extra realism).

How you’d do it (high-level):

Build Circuit 1 (short) and Circuit 2 (same goal but longer).

Create a noise model (and vary its strength across levels).

Run many shots per noise level.

Compute fidelity (ex: for Bell state, fidelity = P(00)+P(11)).

Plot fidelity vs noise for both circuits.

Google Cirq (also works; great if he likes Google’s ecosystem)

Best parts:

Cirq supports noise by attaching noise channels (like depolarize, amplitude damping, bit-flip) to moments/operations.

You can simulate with Cirq’s simulators (and optionally use qsim if available in your environment).

How you’d do it (high-level):

Build Circuit 1 and Circuit 2 in Cirq.

Apply a NoiseModel (or insert noise gates) and sweep noise strengths.

Sample many shots, compute fidelity, plot results.

Which should he pick for a proposal?

If the goal is to be super practical and align with “small algorithms + noise + fidelity”: Qiskit is usually the smoothest path.

If he’s already leaning toward Google quantum tooling (or wants Cirq on his resume): Cirq is totally valid.

If you want, I can give you a clean “proposal-ready” paragraph that says why Qiskit/Cirq is the right simulation environment plus a tiny pseudocode outline (no heavy math).

You said:
Yes please
ChatGPT said:
Proposal-ready paragraph (you can paste directly)

My project will be simulated using either IBM Qiskit (preferred) or Google Cirq, because both platforms allow me to run small quantum circuits repeatedly while introducing controlled noise and measuring how the circuit’s accuracy changes. In Qiskit, I can use the built-in Aer noise modeling tools to apply realistic error sources such as gate errors and measurement (readout) errors, then sweep noise strength across multiple levels and compute fidelity (the probability of getting the expected outcome). In Cirq, I can apply standard noise channels (such as depolarizing or damping noise) through a noise model and run the same sweep. This directly matches the QSD research focus of understanding how noise impacts algorithm fidelity, and allows fair comparisons between a short circuit and a longer circuit that achieves the same intended result but has more opportunities for error.

Tiny pseudocode outline (simple, readable)

Inputs

Circuit 1 = short circuit (few gates)

Circuit 2 = longer circuit (same goal, more gates)

NoiseLevels = list of noise strengths (example: 0, 0.001, 0.002, 0.005, 0.01, 0.02)

Shots = 2000 (number of repeated runs per test)

Algorithm

Build Circuit 1 and Circuit 2 for the same task
Example task: create a Bell state → expected results mostly 00 or 11

For each noise in NoiseLevels:

Create a noise model with strength = noise

Run Circuit 1 with that noise for Shots

Compute fidelity for Circuit 1
(Bell fidelity = P(00) + P(11))

Run Circuit 2 with that noise for Shots

Compute fidelity for Circuit 2

Save results in a table

Plot:

x-axis: noise strength

y-axis: fidelity

two curves: Circuit 1 vs Circuit 2

Conclusion:

Check if Circuit 2 drops faster than Circuit 1

Explain why “more gates → more chances for error”

One-sentence “expected outcome” (proposal-ready)

I expect the longer circuit to show a faster drop in fidelity as noise increases, demonstrating that circuit depth and gate count strongly affect reliability, which is a key concern in real trapped-ion quantum computing systems.

If you want, I can also write a 1-page full proposal template (Title → Background → Question → Methods → Metrics → Timeline → Risks/Backup plan) that your son can submit as-is.

You said:
Can you explain me to a non technical person what is this being solved
ChatGPT said:

This project is trying to solve a very simple—but very important—problem:

Quantum computers make a lot of mistakes.
We want to figure out what kinds of quantum “programs” make fewer mistakes, and why.

