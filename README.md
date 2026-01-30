# Dominosa Solver: Architectural Prototype (Phase 1)

**A deterministic constraint-satisfaction engine for the Dominosa logic puzzle, built on a custom pointer-based graph architecture.**

---  

## Executive Summary

This project is a focused algorithmic study of the **Dominosa** (Solitaire Dominoes) puzzle, implemented using a logic-first, deterministic approach. Unlike conventional solvers that depend on external graph or tiling libraries, this system is constructed entirely from first principles to ensure transparency, controllability, and rigor in logical reasoning.

The solver models Dominosa as a constrained placement problem analogous to **Exact Cover**, implemented atop a bespoke graph abstraction (`Node`, `Edge`, and adjacency structures). Phase 1 is intentionally limited to **pure deductive heuristics**, explicitly avoiding backtracking, recursion, or probabilistic search, in order to evaluate the practical limits of deterministic inference.

---

## Technical Stack

- **Core Language:** Python 3.10+  
  (Dataclasses, static type hints, structured modules)
- **Data Structures:**  
  Custom doubly-linked grid graph (no third-party graph libraries)
- **Numerical Operations:**  
  NumPy for constant-time coordinate arithmetic
- **Visualization:**  
  PyQt6 with a custom-painted QWidget for real-time logical state rendering

---

## Algorithmic Approach (Phase 1)

The solver operates as a multi-pass deterministic inference engine. Each pass applies increasingly restrictive constraints until no further deductions are possible.

### 1. Global Uniqueness Constraint
- Maintains a global frequency map of all remaining domino pairs (the “bone pile”).
- If a specific domino value pair (e.g., `1–6`) can legally occupy only a single position on the board, that placement is forced.

### 2. Local Isolation Constraint
- Evaluates individual grid nodes.
- If a cell has exactly one remaining valid adjacent neighbor (`Active Degree == 1`), the corresponding bond is forced.

### 3. Constraint Propagation
- Every forced placement triggers a cascade:
  - Adjacent edges are invalidated.
  - Affected nodes update their available degrees.
  - The global frequency map is reduced.
- This propagation may unlock new global or local forced moves in subsequent passes.

The solver iterates these steps until it reaches a fixed point or no further deterministic moves are available.

---


