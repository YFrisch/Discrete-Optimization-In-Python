from __future__ import annotations

from itertools import product

import numpy as np
from scipy.spatial import ConvexHull

from src.polyhedra.representations import hrep_to_vertices_2d


# --- INTEGER_HULL:lattice_points:start
def lattice_points_in_polytope_2d(
    A: np.ndarray,
    b: np.ndarray,
    *,
    tol: float = 1e-9,
) -> np.ndarray:
    """Enumerate the integer points in a bounded, full-dimensional 2D polytope.

    The routine first finds a bounding box from the polytope's vertices, enumerates
    every lattice point in that box, and keeps the points satisfying ``Ax <= b``.
    This is intentionally a small-scale educational algorithm.
    """
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float).reshape(-1)
    vertices = hrep_to_vertices_2d(A, b, tol=tol)

    lower = np.ceil(vertices.min(axis=0) - tol).astype(int)
    upper = np.floor(vertices.max(axis=0) + tol).astype(int)
    if np.any(lower > upper):
        return np.empty((0, 2), dtype=int)

    candidates = np.array(
        list(product(range(lower[0], upper[0] + 1), range(lower[1], upper[1] + 1))),
        dtype=int,
    )
    feasible = np.all(A @ candidates.T <= b[:, None] + tol, axis=0)
    return candidates[feasible]


# --- INTEGER_HULL:lattice_points:end


# --- INTEGER_HULL:vertices:start
def integer_hull_vertices_2d(
    A: np.ndarray,
    b: np.ndarray,
    *,
    tol: float = 1e-9,
) -> np.ndarray:
    """Return the vertices of ``conv({x in Z^2 | Ax <= b})`` for a bounded polygon.

    Full-dimensional integer hulls are computed with a convex hull. If the integer
    points form only a point or a line segment, the corresponding one or two vertices
    are returned instead.
    """
    points = lattice_points_in_polytope_2d(A, b, tol=tol)
    if len(points) == 0:
        raise ValueError("The polytope contains no integer points.")
    if len(points) == 1:
        return points.copy()

    centered = points - points[0]
    if np.linalg.matrix_rank(centered, tol=tol) < 2:
        _, _, directions = np.linalg.svd(centered, full_matrices=False)
        scores = points @ directions[0]
        indices = np.unique([np.argmin(scores), np.argmax(scores)])
        return points[indices]

    hull = ConvexHull(points)
    return points[hull.vertices]


# --- INTEGER_HULL:vertices:end
