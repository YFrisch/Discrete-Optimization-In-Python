from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from src.polyhedra.fourier_motzkin import fourier_motzkin_eliminate


@dataclass(frozen=True)
class AffineImageStats:
    n_x_eliminated: int
    n_constraints_initial: int
    n_constraints_final: int


# --- AFFINE:image_invertible:start
def affine_image_hrep_invertible(
    A: np.ndarray,
    b: np.ndarray,
    D: np.ndarray,
    d: np.ndarray,
    *,
    tol: float = 1e-12,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Image of P = {x | A x <= b} under y = D x + d, assuming D is square invertible.

    Substitute x = D^{-1}(y - d) into A x <= b:
        A D^{-1} y <= b + A D^{-1} d
    """
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float).reshape(-1)
    D = np.asarray(D, dtype=float)
    d = np.asarray(d, dtype=float).reshape(-1)

    m, n = A.shape
    if D.shape != (n, n):
        raise ValueError(f"D must be ({n},{n}) for invertible mapping.")
    if d.shape != (n,):
        raise ValueError(f"d must have shape ({n},).")

    if abs(np.linalg.det(D)) <= tol:
        raise ValueError("D appears singular; use the projection-based method instead.")

    Dinv = np.linalg.inv(D)
    A_y = A @ Dinv
    b_y = b + (A @ Dinv @ d)
    return A_y, b_y.reshape(-1, 1)


# --- AFFINE:image_invertible:end


# --- AFFINE:image_projection:start
def affine_image_hrep_via_projection(
    A: np.ndarray,
    b: np.ndarray,
    D: np.ndarray,
    d: np.ndarray,
    *,
    tol: float = 1e-12,
) -> Tuple[np.ndarray, np.ndarray, AffineImageStats]:
    """
    General affine image via projection:

        y = D x + d
        x in {x | A x <= b}

    Build constraints in variables z = (x, y):
        A x <= b
        y - D x <= d
        -y + D x <= -d

    Then eliminate x using Fourier–Motzkin elimination.
    Suitable for *small* dimensions (educational / geometric use).
    """
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float).reshape(-1)
    D = np.asarray(D, dtype=float)
    d = np.asarray(d, dtype=float).reshape(-1)

    m, n = A.shape
    p = D.shape[0]
    if D.shape[1] != n:
        raise ValueError(f"D must have shape (p, {n}).")
    if d.shape != (p,):
        raise ValueError(f"d must have shape ({p},).")

    # z = (x, y) in R^{n+p}
    A1 = np.hstack([A, np.zeros((m, p))])
    b1 = b

    A2 = np.hstack([-D, np.eye(p)])
    b2 = d

    A3 = np.hstack([D, -np.eye(p)])
    b3 = -d

    A_ext = np.vstack([A1, A2, A3])
    b_ext = np.concatenate([b1, b2, b3]).reshape(-1, 1)

    n_constraints_initial = A_ext.shape[0]

    # eliminate x variables one by one (always index 0 since we drop columns)
    for _ in range(n):
        A_ext, b_ext, _stats = fourier_motzkin_eliminate(A_ext, b_ext, k=0, drop_k=True, tol=tol)

    stats = AffineImageStats(
        n_x_eliminated=n,
        n_constraints_initial=n_constraints_initial,
        n_constraints_final=A_ext.shape[0],
    )
    return A_ext, b_ext, stats


# --- AFFINE:image_projection:end
