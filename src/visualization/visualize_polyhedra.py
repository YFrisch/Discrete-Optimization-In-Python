"""Utilities for plotting low-dimensional polyhedra in half-space form.

The public :func:`visualize_polyhedron` function accepts a polyhedron described by
``A @ x <= b`` and plots it in two or three dimensions.  Two-dimensional feasible
regions are approximated on a display grid, while vertices and three-dimensional
surfaces are computed with SciPy when possible.

This module is intended for small educational examples.  It is not a replacement
for a dedicated polyhedral-computation or scientific-visualization package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class PlotResult:
    """Summary of the polyhedron information obtained while plotting.

    Attributes
    ----------
    feasible:
        Whether the polyhedron appeared feasible.  In two dimensions, this is based
        on the displayed sampling grid and any vertices found by SciPy.  It is
        ``None`` when feasibility could not be inferred, for example when filling is
        disabled and no vertices are available.
    vertices:
        Vertices computed by SciPy as an array with one vertex per row, or ``None``
        when vertices could not be computed.  Their row order is unspecified.
    """

    feasible: Optional[bool]
    vertices: Optional[np.ndarray]


def _as_2d_float(A: np.ndarray) -> np.ndarray:
    """Convert a constraint matrix to a two-dimensional floating-point array.

    Parameters
    ----------
    A:
        Array-like constraint matrix.

    Returns
    -------
    numpy.ndarray
        A floating-point view or copy of ``A``.

    Raises
    ------
    ValueError
        If ``A`` is not two-dimensional.
    """

    A = np.asarray(A, dtype=float)
    if A.ndim != 2:
        raise ValueError("A must be 2D")
    return A


def _as_1d_float(b: np.ndarray, m: int) -> np.ndarray:
    """Convert right-hand sides to a flat floating-point vector of length ``m``.

    Parameters
    ----------
    b:
        Array-like right-hand-side values.  Both one-dimensional vectors and column
        vectors are accepted.
    m:
        Required number of right-hand-side values.

    Returns
    -------
    numpy.ndarray
        The flattened floating-point vector.

    Raises
    ------
    ValueError
        If flattening ``b`` does not produce exactly ``m`` values.
    """

    b = np.asarray(b, dtype=float).reshape(-1)
    if b.shape != (m,):
        raise ValueError(f"b must have shape ({m},) or ({m},1)")
    return b


def _feasible_mask_2d(
    A: np.ndarray, b: np.ndarray, X: np.ndarray, Y: np.ndarray, tol: float
) -> np.ndarray:
    """Evaluate two-dimensional inequalities at every point of a coordinate grid.

    Parameters
    ----------
    A:
        Constraint matrix with shape ``(m, 2)``.
    b:
        Right-hand-side vector with shape ``(m,)``.
    X, Y:
        Coordinate arrays of equal shape, typically produced by
        :func:`numpy.meshgrid`.
    tol:
        Additive feasibility tolerance.  A point is accepted when every constraint
        satisfies ``A[i] @ point <= b[i] + tol``.

    Returns
    -------
    numpy.ndarray
        Boolean array with the same shape as ``X`` and ``Y``.  A true entry denotes
        a grid point satisfying every inequality.
    """

    # X and Y are meshgrids.
    pts = np.stack([X.ravel(), Y.ravel()], axis=1)  # (N,2)
    ok = (A @ pts.T).T <= (b[None, :] + tol)  # (N,m)
    return np.all(ok, axis=1).reshape(X.shape)


def _try_vertices_scipy(A: np.ndarray, b: np.ndarray) -> Optional[np.ndarray]:
    """Try to compute the vertices of a full-dimensional polyhedron with SciPy.

    The function first solves a linear program for a strictly interior point and then
    passes the half-spaces to :class:`scipy.spatial.HalfspaceIntersection`.  It is a
    best-effort helper so that two-dimensional boundary and grid plotting can still
    work when SciPy is unavailable or the polyhedron has no strict interior.

    Parameters
    ----------
    A:
        Constraint matrix with shape ``(m, n)``.
    b:
        Right-hand-side vector with shape ``(m,)``.

    Returns
    -------
    numpy.ndarray or None
        An array of shape ``(k, n)`` containing the vertices in unspecified order.
        ``None`` is returned when SciPy cannot be imported, the interior-point linear
        program fails, the polyhedron has no strict interior, or no intersections are
        produced.

    Notes
    -----
    The returned coordinates are floating-point approximations, despite being used as
    the module's "exact" alternative to grid sampling.  Errors raised by SciPy while
    constructing a half-space intersection are allowed to propagate.
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
    """Visualize a two- or three-dimensional polyhedron ``{x | A @ x <= b}``.

    In two dimensions, every constraint boundary is drawn and a binary feasibility
    mask over the requested viewing window can be rendered using grid sampling.  When
    SciPy can compute the vertices, they and their convex-hull boundary are optionally
    added.  In three dimensions, SciPy is required to compute and draw the convex-hull
    surface.

    Parameters
    ----------
    A_mat:
        Constraint matrix with shape ``(m, n)``, where ``n`` is either 2 or 3.  Row
        ``i`` contains the coefficients of the inequality
        ``A_mat[i] @ x <= b_mat[i]``.
    b_mat:
        Right-hand sides as an array with shape ``(m,)`` or ``(m, 1)``.
    xlim, ylim, zlim:
        Inclusive lower and upper display limits for the corresponding axes.  ``zlim``
        is ignored for two-dimensional plots.
    fill:
        If true, render a binary feasibility mask in a two-dimensional plot.  This
        option has no effect in three dimensions.
    grid:
        Number of sample coordinates per axis for two-dimensional feasibility shading.
        The resulting mask contains ``grid**2`` points.
    show_vertices:
        If true, draw vertices computed by SciPy.  In two dimensions, their convex-hull
        boundary is also drawn when possible.
    tol:
        Numerical tolerance used for grid feasibility tests and zero-coefficient
        checks.
    title:
        Optional title for the Matplotlib axes.

    Returns
    -------
    PlotResult
        A feasibility indication and any vertices computed while constructing the
        plot.  For a two-dimensional plot, ``feasible=False`` only means that no
        feasible grid point or vertex was found; it is not a general infeasibility
        certificate.

    Raises
    ------
    ValueError
        If the input shapes are inconsistent or the polyhedron is not two- or
        three-dimensional.
    RuntimeError
        If a three-dimensional polyhedron cannot be processed with SciPy or has no
        nonempty full-dimensional vertex representation.

    Notes
    -----
    This function creates a new Matplotlib figure but deliberately does not call
    :func:`matplotlib.pyplot.show`, allowing notebooks and applications to control when
    figures are rendered.
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

        return PlotResult(feasible=True, vertices=V)

    raise ValueError(f"visualize_polyhedron supports only 2D or 3D, got n={n}")
