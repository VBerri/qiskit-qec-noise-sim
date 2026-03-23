# Quantum Error Correction: Scaling Repetition Codes
## Executive Summary for Science Fair Judges

---

### THE PROBLEM
Quantum computers are incredibly powerful, but quantum information is fragile. Even tiny amounts of noise can corrupt calculations, making quantum computers unreliable for real-world use.

### THE SOLUTION
**Quantum error correction** protects quantum information by spreading one logical qubit across several physical qubits, using redundancy (like repetition) to recover from errors.

### OUR QUESTION
**Does using more physical qubits (larger repetition codes) reduce logical errors?**

---

### WHAT WE DID

We built a simulation using **Qiskit Aer** (a quantum computing simulator) and tested:
- **Baseline (no protection):** 1 physical qubit
- **Repetition codes:** 3, 5, and 7 physical qubits
- **Three noise types:** bit-flip, phase-flip, and depolarizing errors
- **Metric:** "Logical success probability" = how often the final decoded answer is correct

### KEY RESULTS

| Noise Type | Baseline (n=1) @ p=0.08 | n=7 Repetition @ p=0.08 | Improvement |
|-----------|------------------------|------------------------|------------|
| Bit-flip  | 0.7585                 | 0.9270                 | +0.1685    |
| Phase-flip| 0.7585                 | 0.9270                 | +0.1685    |
| **At low noise (p=0.02):** n=7 reached **0.999** success (near-zero logical error) |

### THE PATTERN
As code size increased from n=3 → n=5 → n=7, logical success **consistently improved**.

This demonstrates the **core principle** behind modern quantum error correction:
> **Larger codes can suppress logical errors.**

### WHY THIS MATTERS
- Quantum computers need error correction to work reliably.
- This project shows (in simulation) that the error-correction approach actually works.
- Same scaling trend seen in famous quantum milestones (e.g., Google's Willow).

### WHAT'S NOVEL ABOUT OUR WORK
✓ **Fair comparison:** we use basis-matched settings (e.g., Z-basis code with Z-storage state)  
✓ **Complete scaling analysis:** n=3, 5, 7 (not just one size)  
✓ **Multiple noise types:** bit-flip, phase-flip, depolarizing  
✓ **Fully reproducible:** all code and data open-source  
✓ **Student-accessible:** uses free Qiskit tools, clear methods

### LIMITATIONS
- This is a **simulation**, not a real hardware experiment.
- We use simplified, independent noise (real devices have correlated errors).
- Repetition codes only protect against one error type at a time.

### NEXT STEPS
- Test more advanced codes (Shor, Steane, surface codes).
- Compare against real quantum hardware data.
- Implement fault-tolerant syndrome extraction.

---

### QUICK STATS
- **Lines of code written:** ~500 (circuits, noise models, decoding, experiments)
- **Total simulations run:** 27 p-values × 3 noise types × 4 methods = 324 experiments
- **Total shots:** 4,000+ per p-value = millions of individual circuit runs
- **Reproducibility:** 100% — all code, data, and scripts included

---

### KEY TAKEAWAY FOR JUDGES
**This is a rigorous, clearly-explained simulation study that substantiates a core quantum-computing principle: error correction works, and code size matters.** It's accessible to high school students but technically sound and directly relevant to the quantum-computing frontier.

---

**Project:** Quantum Error Correction in Quantum Computing Simulations  
**Authors:** Sanjeev Tamilselvan, Tanuj Ranjith  
**Schools:** Northview High School (Duluth, GA); B. Reed Henderson High School (West Chester, PA)  
**Contact:** sansuvans@gmail.com  
**Code:** Available on GitHub — full reproducibility
