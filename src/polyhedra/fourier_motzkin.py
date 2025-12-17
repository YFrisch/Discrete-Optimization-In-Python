from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class FMEStats:
    eliminated_index: int
    n_zero: int
    n_pos: int
    n_neg: int
    n_out: int


def fourier_motzkin_eliminate(
    A: np.ndarray,
    b: np.ndarray,
    k: int,
    *,
    tol: float = 1e-12,
    drop_k: bool = True,
    normalize: bool = True,
) -> Tuple[np.ndarray, np.ndarray, FMEStats]:
    """
    Fourier–Motzkin elimination: eliminate variable x_k from Ax <= b.

    Parameters
    ----------
    A : (m, n) array
        Constraint matrix.
    b : (m,) or (m,1) array
        Right-hand side.
    k : int
        Variable index to eliminate (0-based).
    tol : float
        Tolerance for deciding whether A[i,k] is zero.
    drop_k : bool
        If True, remove the k-th column from the output matrix.
        If False, keep dimension but set the k-th column to 0.
    normalize : bool
        If True, scale each inequality by max-abs coefficient (simple numeric stabilization).

    Returns
    -------
    A2, b2, stats
        Projected system in remaining variables.
    """
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float).reshape(-1)

    if A.ndim != 2:
        raise ValueError("A must be 2D")
    m, n = A.shape
    if b.shape != (m,):
        raise ValueError(f"b must have shape ({m},) or ({m},1)")
    if not (0 <= k < n):
        raise ValueError(f"k must be in [0, {n-1}]")

    ak = A[:, k]
    idx_zero = np.where(np.abs(ak) <= tol)[0]
    idx_pos = np.where(ak > tol)[0]
    idx_neg = np.where(ak < -tol)[0]

    rows = []
    rhs = []

    # Keep constraints where coefficient of x_k is zero
    for i in idx_zero:
        rows.append(A[i].copy())
        rhs.append(b[i])

    # Combine negative and positive to eliminate x_k (ak_neg < 0, ak_pos > 0)
    for i in idx_neg:
        for j in idx_pos:
            row = ak[j] * A[i] - ak[i] * A[j]
            r = ak[j] * b[i] - ak[i] * b[j]
            rows.append(row)
            rhs.append(r)

    if rows:
        A2 = np.vstack(rows)
        b2 = np.array(rhs, dtype=float)
    else:
        A2 = np.zeros((0, n), dtype=float)
        b2 = np.zeros((0,), dtype=float)

    # remove or zero-out eliminated variable
    if drop_k:
        A2 = np.delete(A2, k, axis=1)
    else:
        A2[:, k] = 0.0

    # simple scaling for stability/readability
    if normalize and A2.size > 0:
        scale = np.max(np.abs(A2), axis=1)
        scale[scale <= tol] = 1.0
        A2 = A2 / scale[:, None]
        b2 = b2 / scale

    stats = FMEStats(
        eliminated_index=k,
        n_zero=len(idx_zero),
        n_pos=len(idx_pos),
        n_neg=len(idx_neg),
        n_out=A2.shape[0],
    )
    return A2, b2.reshape(-1, 1), stats


def constraints_1d_bounds(
    a: np.ndarray, b: np.ndarray, *, tol: float = 1e-12
) -> tuple[float, float]:
    """
    Interpret a 1D system a_i x <= b_i as an interval [L, U] (may be infinite).
    """
    a = np.asarray(a, dtype=float).reshape(-1)
    b = np.asarray(b, dtype=float).reshape(-1)

    L = -np.inf
    U = np.inf
    for ai, bi in zip(a, b, strict=False):
        if abs(ai) <= tol:
            if bi < -tol:
                return np.inf, -np.inf  # infeasible
            continue
        bound = bi / ai
        if ai > 0:
            U = min(U, bound)
        else:
            L = max(L, bound)
    return float(L), float(U)
