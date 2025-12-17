# Discrete Optimization in Python

Welcome traveller! 👋

This repository is a small, self-contained tutorial on **Discrete Optimization** (with a focus on **Integer Linear Optimization**) implemented in **Python** Jupyter Notebooks.

The emphasis is on **intuition + geometry** (polyhedra, projections, relaxations) and on the algorithmic ideas that make integer optimization work in practice (branch-and-bound, cutting planes, decomposition, heuristics).

```{image} _static/img/cover.png
:alt: Discrete Optimization in Python
:class: mb-2
:width: 100%
:align: center
```

**Prerequisites:**

* Basic linear algebra (vectors, matrices)
* Familiarity with linear programming
* Python + NumPy basics

For proofs and deeper theory, I’ll often point to standard references rather than reproducing full proofs in the notebooks.

**Source:**

The repository is available on [GitHub](https://github.com/YFrisch/Discrete-Optimization-In-Python).

The notebooks live in `notebooks/`. This rendered website is generated with Jupyter Book and executes the notebooks during the build. If you run notebooks locally, you can of course edit and experiment freely.

Algorithmic implementations can be found in `src/` with tests for their functionality in `tests/`.

## Start here

Use the sidebar to follow the tutorial order, starting with **01-Introduction**.

For the "full experience", it's best to go in order:

1. {doc}`01 — Introduction </notebooks/01-Introduction>`
2. {doc}`02 — Fourier Motzkin Elimination </notebooks/02-Fourier-Motzkin-Elimination>`
3. {doc}`WIP: 03 — Affine Mappings and Polar Cones </notebooks/03-Affine-Mappings-and-Polar-Cones>`
4. {doc}`WIP: 04 — Interior and Exterior Representation </notebooks/04-Interior-Exterior-Representations>`
5. {doc}`WIP: 05 — The Integer Hull </notebooks/05-The-Integer-Hull>`
6. {doc}`WIP: 06 — Branch and Bound Method </notebooks/06-Branch-And-Bound>`
7. {doc}`WIP: 07 — Unimodularity and Dual Integrality </notebooks/07-Unimodularity-and-Total-Dual-Integrality>`
8. {doc}`WIP: 08 — Gomory Cuts </notebooks/08-Fractional-and-Mixed-Integer-Gomory-Cuts>`
9. {doc}`WIP: 09 — The Knapsack Problem </notebooks/09-The-Knapsack-Problem>`
10. {doc}`WIP: 10 — The Set-Packing Polytope </notebooks/10-The-Set-Packing-Polytope>`
11. {doc}`WIP: 11 — Lagrange Relaxation </notebooks/11-Lagrange-Relaxation>`
12. {doc}`WIP: 12 — Dantzig-Wolfe Decomposition </notebooks/12-Dantzig-Wolfe-Decomposition>`
13. {doc}`WIP: 13 — Bender's Decomposition </notebooks/13-Benders-Decomposition>`
14. {doc}`WIP: 14 — Heuristics </notebooks/14-Heuristic-Methods>`
15. {doc}`WIP: 15 — Other Heuristics </notebooks/15-Other-Heuristics>`
