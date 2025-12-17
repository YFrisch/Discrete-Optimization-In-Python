from __future__ import annotations

import numpy as np


# --- POLAR:from_generators:start
def polar_cone_hrep_from_generators(G: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    If K = cone(G) = { G λ | λ >= 0 } (columns of G are generators),
    then the polar cone is

        K^° = { y | y^T g_i <= 0 for all generators g_i }
            = { y | G^T y <= 0 }.

    Returns an H-representation A y <= b with A = G^T and b = 0.
    """
    G = np.asarray(G, dtype=float)
    if G.ndim != 2:
        raise ValueError("G must be 2D (n x r), columns are generators.")
    A = G.T
    b = np.zeros((A.shape[0], 1), dtype=float)
    return A, b


# --- POLAR:from_generators:end


# --- POLAR:generators_from_hrep:start
def polar_cone_generators_from_hrep(A: np.ndarray) -> np.ndarray:
    """
    If K = { x | A x <= 0 } is a polyhedral cone,
    then K^° = cone(A^T) = { A^T λ | λ >= 0 }.

    Returns generator matrix G = A^T (columns are generators of the polar).
    """
    A = np.asarray(A, dtype=float)
    if A.ndim != 2:
        raise ValueError("A must be 2D.")
    return A.T


# --- POLAR:generators_from_hrep:end
