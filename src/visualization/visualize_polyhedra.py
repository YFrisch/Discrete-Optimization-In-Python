from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class PlotResult:
    feasible: Optional[bool]
    vertices: Optional[np.ndarray]


def _as_2d_float(A: np.ndarray) -> np.ndarray:
    A = np.asarray(A, dtype=float)
    if A.ndim != 2:
        raise ValueError("A must be 2D")
    return A


def _as_1d_float(b: np.ndarray, m: int) -> np.ndarray:
    b = np.asarray(b, dtype=float).reshape(-1)
    if b.shape != (m,):
        raise ValueError(f"b must have shape ({m},) or ({m},1)")
    return b


def _feasible_mask_2d(
    A: np.ndarray, b: np.ndarray, X: np.ndarray, Y: np.ndarray, tol: float
) -> np.ndarray:
    # X,Y are meshgrids
    pts = np.stack([X.ravel(), Y.ravel()], axis=1)  # (N,2)
    ok = (A @ pts.T).T <= (b[None, :] + tol)  # (N,m)
    return np.all(ok, axis=1).reshape(X.shape)


def _try_vertices_scipy(A: np.ndarray, b: np.ndarray) -> Optional[np.ndarray]:
    """
    Try exact vertices via scipy (HalfspaceIntersection + ConvexHull).
    Returns vertices (k,dim) or None if scipy unavailable / no interior.
    """
    try:
        from scipy.optimize import linprog
        from scipy.spatial import HalfspaceIntersection
    except Exception:
        return None

    m, n = A.shape
    norms = np.linalg.norm(A, axis=1)
    # Find interior point by maximizing t s.t. A x + norms*t <= b, t >= 0
    A_aug = np.hstack([A, norms[:, None]])
    c = np.zeros(n + 1)
    c[-1] = -1.0  # minimize -t => maximize t
    bounds = [(None, None)] * n + [(0.0, None)]

    res = linprog(c, A_ub=A_aug, b_ub=b, bounds=bounds, method="highs")
    if not res.success:
        return None
    t = float(res.x[-1])
    if t <= 1e-9:
        # Likely empty or lower-dimensional; HalfspaceIntersection needs strict interior
        return None

    interior = res.x[:n]
    # scipy wants halfspaces in form: H[:,:-1] @ x + H[:,-1] <= 0
    # Our Ax <= b -> Ax - b <= 0 => [A, -b]
    halfspaces = np.hstack([A, -b[:, None]])
    hs = HalfspaceIntersection(halfspaces, interior)
    V = np.asarray(hs.intersections, dtype=float)
    if V.size == 0:
        return None
    return V


def visualize_polyhedron(
    A_mat: np.ndarray,
    b_mat: np.ndarray,
    *,
    xlim: Tuple[float, float] = (-1.0, 10.0),
    ylim: Tuple[float, float] = (-1.0, 10.0),
    zlim: Tuple[float, float] = (-1.0, 10.0),
    fill: bool = True,
    grid: int = 250,
    show_vertices: bool = True,
    tol: float = 1e-9,
    title: Optional[str] = None,
) -> PlotResult:
    """
    Visualize Ax <= b for 2D or 3D.

    2D:
      - plots constraint boundaries
      - optionally shades feasible region (grid-based)
      - optionally tries exact vertices using scipy if available

    3D:
      - requires scipy to compute vertices/hull (otherwise raises a helpful error)

    Returns PlotResult(feasible, vertices).
    """
    A = _as_2d_float(A_mat)
    m, n = A.shape
    b = _as_1d_float(b_mat, m)

    if n == 2:
        fig, ax = plt.subplots(figsize=(8, 5))

        # 1) Shade feasible region (simple + tangible)
        if fill:
            xs = np.linspace(xlim[0], xlim[1], grid)
            ys = np.linspace(ylim[0], ylim[1], grid)
            X, Y = np.meshgrid(xs, ys)
            mask = _feasible_mask_2d(A, b, X, Y, tol=tol)

            # show as light overlay; keep default matplotlib colors
            ax.imshow(
                mask.astype(float),
                origin="lower",
                extent=(xlim[0], xlim[1], ylim[0], ylim[1]),
                alpha=0.18,
                aspect="auto",
            )

        # 2) Plot constraint boundary lines robustly
        xs_line = np.linspace(xlim[0], xlim[1], 400)
        for i in range(m):
            a0, a1 = A[i, 0], A[i, 1]
            bi = b[i]

            if abs(a1) > tol:
                ys_line = (bi - a0 * xs_line) / a1
                ax.plot(xs_line, ys_line, linewidth=1.2)
            elif abs(a0) > tol:
                # vertical line: a0*x = b => x = b/a0
                xv = bi / a0
                ax.axvline(xv, linewidth=1.2)
            else:
                # 0*x + 0*y <= b: either redundant or infeasible
                pass

        # 3) Optional: exact vertices if scipy available
        V = _try_vertices_scipy(A, b)
        if V is not None and show_vertices:
            ax.scatter(V[:, 0], V[:, 1], s=20)
            # optionally draw convex hull in 2D
            try:
                from scipy.spatial import ConvexHull

                hull = ConvexHull(V)
                cycle = np.r_[hull.vertices, hull.vertices[0]]
                ax.plot(V[cycle, 0], V[cycle, 1], linewidth=2.0)
            except Exception:
                pass

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel("$x_0$")
        ax.set_ylabel("$x_1$")
        if title:
            ax.set_title(title)
        ax.grid(True)
        plt.show()

        # Feasibility quick guess: if any pixel feasible OR vertices exist
        feasible = None
        if fill:
            feasible = bool(np.any(mask))
        if V is not None:
            feasible = True

        return PlotResult(feasible=feasible, vertices=V)

    if n == 3:
        # For 3D, we strongly prefer exact vertices/hull via scipy.
        V = _try_vertices_scipy(A, b)
        if V is None:
            raise RuntimeError(
                "3D visualization requires scipy and a polyhedron with non-empty interior.\n"
                "Install scipy (pip install scipy) and ensure the polyhedron is full-dimensional."
            )

        # Plot convex hull surface
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        try:
            from scipy.spatial import ConvexHull
        except Exception as e:
            raise RuntimeError("scipy is required for 3D ConvexHull.") from e

        hull = ConvexHull(V)

        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection="3d")

        faces = [V[simplex] for simplex in hull.simplices]
        poly = Poly3DCollection(faces, alpha=0.15)
        ax.add_collection3d(poly)

        if show_vertices:
            ax.scatter(V[:, 0], V[:, 1], V[:, 2], s=12)

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_zlim(zlim)
        ax.set_xlabel("$x_0$")
        ax.set_ylabel("$x_1$")
        ax.set_zlabel("$x_2$")
        if title:
            ax.set_title(title)

        plt.show()
        return PlotResult(feasible=True, vertices=V)

    raise ValueError(f"visualize_polyhedron supports only 2D or 3D, got n={n}")
