import numpy as np

from src.optimization.branch_and_bound import branch_and_bound


def test_branch_and_bound_solves_fractional_polygon_and_records_pruning():
    A = np.array(
        [
            [-1.0, 0.0],
            [0.0, -1.0],
            [2.0, 1.0],
            [1.0, 2.0],
        ]
    )
    b = np.array([0.0, 0.0, 8.5, 8.5])

    result = branch_and_bound(np.array([1.0, 1.0]), A, b)

    assert result.status == "optimal"
    assert result.objective == 5.0
    assert tuple(result.x) in {(2.0, 3.0), (3.0, 2.0)}
    assert {node.action for node in result.nodes} >= {
        "branched",
        "integer",
        "bound",
        "infeasible",
    }


def test_branch_and_bound_only_branches_on_integer_constrained_variables():
    A = np.array([[0.0, 0.0]])
    b = np.array([0.0])
    bounds = [(0.0, 1.5), (0.0, 0.25)]

    result = branch_and_bound(
        np.array([1.0, 0.1]),
        A,
        b,
        bounds=bounds,
        integer_indices=[0],
    )

    assert result.status == "optimal"
    np.testing.assert_allclose(result.x, [1.0, 0.25])
    assert result.objective == 1.025
    assert all(node.branch_variable in {None, 0} for node in result.nodes)


def test_branch_and_bound_reports_infeasible_integer_problem():
    A = np.array([[1.0], [-1.0]])
    b = np.array([0.5, -0.5])

    result = branch_and_bound(np.array([1.0]), A, b, bounds=[(None, None)])

    assert result.status == "infeasible"
    assert result.x is None
    assert result.objective is None
