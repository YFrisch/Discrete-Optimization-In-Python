from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, QhullError


def _as_hrep_2d(A: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float).reshape(-1)

    if A.ndim != 2 or A.shape[1] != 2:
        raise ValueError("A must have shape (m, 2).")
    if b.shape != (A.shape[0],):
        raise ValueError(f"b must have shape ({A.shape[0]},) or ({A.shape[0]}, 1).")
    if not np.all(np.isfinite(A)) or not np.all(np.isfinite(b)):
        raise ValueError("A and b must contain only finite values.")
    return A, b


def _require_nonempty_bounded_polygon(A: np.ndarray, b: np.ndarray) -> None:
    bounds = [(None, None), (None, None)]
    directions = np.vstack([np.eye(2), -np.eye(2)])

    for direction in directions:
        result = linprog(-direction, A_ub=A, b_ub=b, bounds=bounds, method="highs")
        if result.status == 2:
            raise ValueError("The inequality system is infeasible.")
        if result.status == 3:
            raise ValueError(
                "The inequality system is unbounded; include extreme rays in its V-representation."
            )
        if not result.success:
            raise RuntimeError(f"Could not analyze the inequality system: {result.message}")


# --- REPRESENTATIONS:h_to_v_2d:start
def hrep_to_vertices_2d(
    A: np.ndarray,
    b: np.ndarray,
    *,
    tol: float = 1e-9,
) -> np.ndarray:
    """Return the vertices of a bounded, full-dimensional polygon ``{x | Ax <= b}``.

    The educational 2D algorithm intersects every pair of constraint boundaries,
    keeps the feasible intersections, removes duplicates, and orders the vertices
    counterclockwise. It is intentionally simple rather than designed for large systems.
    """
    A, b = _as_hrep_2d(A, b)
    _require_nonempty_bounded_polygon(A, b)

    vertices: list[np.ndarray] = []
    for i, j in combinations(range(A.shape[0]), 2):
        boundary_matrix = A[[i, j]]
        if abs(np.linalg.det(boundary_matrix)) <= tol:
            continue

        candidate = np.linalg.solve(boundary_matrix, b[[i, j]])
        if np.all(A @ candidate <= b + tol) and not any(
            np.allclose(candidate, vertex, atol=tol, rtol=0.0) for vertex in vertices
        ):
            vertices.append(candidate)

    if len(vertices) < 3:
        raise ValueError("The feasible set is not a full-dimensional polygon.")

    V = np.vstack(vertices)
    center = V.mean(axis=0)
    angles = np.arctan2(V[:, 1] - center[1], V[:, 0] - center[0])
    return V[np.argsort(angles)]


# --- REPRESENTATIONS:h_to_v_2d:end


# --- REPRESENTATIONS:v_to_h_2d:start
def vertices_to_hrep_2d(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ``A, b`` such that ``conv(vertices) = {x | Ax <= b}`` in 2D.

    SciPy's convex hull routine identifies the supporting lines of the polygon.
    Duplicate points and points in the interior are allowed; only hull vertices matter.
    """
    vertices = np.asarray(vertices, dtype=float)
    if vertices.ndim != 2 or vertices.shape[1] != 2:
        raise ValueError("vertices must have shape (k, 2).")
    if vertices.shape[0] < 3:
        raise ValueError("At least three points are required.")
    if not np.all(np.isfinite(vertices)):
        raise ValueError("vertices must contain only finite values.")

    try:
        hull = ConvexHull(vertices)
    except QhullError as error:
        raise ValueError("The points must span a two-dimensional polygon.") from error

    # ConvexHull uses normal @ x + offset <= 0 for points inside the hull.
    A = hull.equations[:, :2]
    b = -hull.equations[:, 2]
    return A, b.reshape(-1, 1)


# --- REPRESENTATIONS:v_to_h_2d:end
