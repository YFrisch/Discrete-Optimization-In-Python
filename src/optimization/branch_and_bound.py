from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor
from typing import Optional, Sequence

import numpy as np
from scipy.optimize import linprog

Bound = tuple[Optional[float], Optional[float]]


@dataclass(frozen=True)
class BranchAndBoundNode:
    """Record of one processed node in a branch-and-bound tree."""

    node_id: int
    parent_id: Optional[int]
    depth: int
    bounds: tuple[Bound, ...]
    lp_solution: Optional[np.ndarray]
    lp_bound: Optional[float]
    action: str
    branch_variable: Optional[int]
    incumbent_value: Optional[float]


@dataclass(frozen=True)
class BranchAndBoundResult:
    """Solution and search trace returned by :func:`branch_and_bound`."""

    status: str
    x: Optional[np.ndarray]
    objective: Optional[float]
    nodes: tuple[BranchAndBoundNode, ...]


def _prepare_problem(
    c: np.ndarray,
    A: np.ndarray,
    b: np.ndarray,
    bounds: Optional[Sequence[Bound]],
    integer_indices: Optional[Sequence[int]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[Bound, ...], tuple[int, ...]]:
    c = np.asarray(c, dtype=float).reshape(-1)
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float).reshape(-1)

    if c.ndim != 1 or c.size == 0:
        raise ValueError("c must be a nonempty vector.")
    if A.ndim != 2 or A.shape[1] != c.size:
        raise ValueError(f"A must have shape (m, {c.size}).")
    if b.shape != (A.shape[0],):
        raise ValueError(f"b must have shape ({A.shape[0]},) or ({A.shape[0]}, 1).")
    if not np.all(np.isfinite(c)) or not np.all(np.isfinite(A)) or not np.all(np.isfinite(b)):
        raise ValueError("c, A, and b must contain only finite values.")

    if bounds is None:
        prepared_bounds: tuple[Bound, ...] = tuple((0.0, None) for _ in range(c.size))
    else:
        if len(bounds) != c.size:
            raise ValueError(f"bounds must contain {c.size} (lower, upper) pairs.")
        converted_bounds: list[Bound] = []
        for lower, upper in bounds:
            lower_value = None if lower is None else float(lower)
            upper_value = None if upper is None else float(upper)
            if lower_value is not None and not np.isfinite(lower_value):
                raise ValueError("Finite lower bounds or None are required.")
            if upper_value is not None and not np.isfinite(upper_value):
                raise ValueError("Finite upper bounds or None are required.")
            converted_bounds.append((lower_value, upper_value))
        prepared_bounds = tuple(converted_bounds)

    if integer_indices is None:
        prepared_indices = tuple(range(c.size))
    else:
        prepared_indices = tuple(int(index) for index in integer_indices)
        if len(set(prepared_indices)) != len(prepared_indices):
            raise ValueError("integer_indices must not contain duplicates.")
        if any(index < 0 or index >= c.size for index in prepared_indices):
            raise ValueError(f"integer_indices must lie between 0 and {c.size - 1}.")

    return c, A, b, prepared_bounds, prepared_indices


def _bounds_are_consistent(bounds: tuple[Bound, ...]) -> bool:
    return all(lower is None or upper is None or lower <= upper for lower, upper in bounds)


def _with_upper_bound(bounds: tuple[Bound, ...], index: int, upper: float) -> tuple[Bound, ...]:
    child = list(bounds)
    lower, old_upper = child[index]
    child[index] = (lower, upper if old_upper is None else min(old_upper, upper))
    return tuple(child)


def _with_lower_bound(bounds: tuple[Bound, ...], index: int, lower: float) -> tuple[Bound, ...]:
    child = list(bounds)
    old_lower, upper = child[index]
    child[index] = (lower if old_lower is None else max(old_lower, lower), upper)
    return tuple(child)


# --- BRANCH_AND_BOUND:solve:start
def branch_and_bound(
    c: np.ndarray,
    A: np.ndarray,
    b: np.ndarray,
    *,
    bounds: Optional[Sequence[Bound]] = None,
    integer_indices: Optional[Sequence[int]] = None,
    tol: float = 1e-9,
) -> BranchAndBoundResult:
    """Maximize ``c @ x`` subject to ``A @ x <= b`` and integrality restrictions.

    The implementation uses depth-first node selection, branches on the first
    fractional integer-constrained variable, and solves LP relaxations with
    :func:`scipy.optimize.linprog`. It is intended for small teaching examples,
    not as a replacement for a production mixed-integer solver.

    ``bounds`` uses SciPy's ``(lower, upper)`` convention and defaults to
    nonnegative variables. If ``integer_indices`` is omitted, every variable is
    required to be integral.
    """
    if tol <= 0:
        raise ValueError("tol must be positive.")

    c, A, b, root_bounds, integer_indices = _prepare_problem(c, A, b, bounds, integer_indices)
    pending = [(0, None, 0, root_bounds)]
    next_node_id = 1
    history: list[BranchAndBoundNode] = []
    incumbent_x: Optional[np.ndarray] = None
    incumbent_value = -np.inf

    while pending:
        node_id, parent_id, depth, node_bounds = pending.pop()

        if not _bounds_are_consistent(node_bounds):
            history.append(
                BranchAndBoundNode(
                    node_id,
                    parent_id,
                    depth,
                    node_bounds,
                    None,
                    None,
                    "infeasible",
                    None,
                    None if incumbent_x is None else incumbent_value,
                )
            )
            continue

        relaxation = linprog(
            -c,
            A_ub=A,
            b_ub=b,
            bounds=node_bounds,
            method="highs",
        )
        if relaxation.status == 2:
            history.append(
                BranchAndBoundNode(
                    node_id,
                    parent_id,
                    depth,
                    node_bounds,
                    None,
                    None,
                    "infeasible",
                    None,
                    None if incumbent_x is None else incumbent_value,
                )
            )
            continue
        if relaxation.status == 3:
            raise ValueError("An LP relaxation is unbounded; this teaching solver requires bounds.")
        if not relaxation.success:
            raise RuntimeError(f"The LP relaxation could not be solved: {relaxation.message}")

        x_lp = np.asarray(relaxation.x, dtype=float)
        lp_bound = float(c @ x_lp)

        if incumbent_x is not None and lp_bound <= incumbent_value + tol:
            history.append(
                BranchAndBoundNode(
                    node_id,
                    parent_id,
                    depth,
                    node_bounds,
                    x_lp,
                    lp_bound,
                    "bound",
                    None,
                    incumbent_value,
                )
            )
            continue

        fractional_indices = [
            index for index in integer_indices if abs(x_lp[index] - np.rint(x_lp[index])) > tol
        ]
        if not fractional_indices:
            candidate = x_lp.copy()
            candidate[list(integer_indices)] = np.rint(candidate[list(integer_indices)])
            candidate_value = float(c @ candidate)
            if incumbent_x is None or candidate_value > incumbent_value + tol:
                incumbent_x = candidate
                incumbent_value = candidate_value
            history.append(
                BranchAndBoundNode(
                    node_id,
                    parent_id,
                    depth,
                    node_bounds,
                    x_lp,
                    lp_bound,
                    "integer",
                    None,
                    incumbent_value,
                )
            )
            continue

        branch_index = fractional_indices[0]
        left_bounds = _with_upper_bound(node_bounds, branch_index, floor(x_lp[branch_index]))
        right_bounds = _with_lower_bound(node_bounds, branch_index, ceil(x_lp[branch_index]))

        left_id = next_node_id
        right_id = next_node_id + 1
        next_node_id += 2
        # The stack is last-in, first-out, so pushing the right child first
        # makes the search process the ``x_j <= floor(x_j*)`` child first.
        pending.append((right_id, node_id, depth + 1, right_bounds))
        pending.append((left_id, node_id, depth + 1, left_bounds))
        history.append(
            BranchAndBoundNode(
                node_id,
                parent_id,
                depth,
                node_bounds,
                x_lp,
                lp_bound,
                "branched",
                branch_index,
                None if incumbent_x is None else incumbent_value,
            )
        )

    if incumbent_x is None:
        return BranchAndBoundResult("infeasible", None, None, tuple(history))
    return BranchAndBoundResult("optimal", incumbent_x, incumbent_value, tuple(history))


# --- BRANCH_AND_BOUND:solve:end
