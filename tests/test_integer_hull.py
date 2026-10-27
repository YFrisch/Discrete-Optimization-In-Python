import numpy as np

from src.polyhedra.integer_hull import (
    integer_hull_vertices_2d,
    lattice_points_in_polytope_2d,
)


def test_integer_hull_of_fractional_polygon():
    A = np.array(
        [
            [-1.0, 0.0],
            [0.0, -1.0],
            [2.0, 1.0],
            [1.0, 2.0],
        ]
    )
    b = np.array([0.0, 0.0, 8.5, 8.5])
    expected_vertices = {(0, 0), (4, 0), (3, 2), (2, 3), (0, 4)}

    points = lattice_points_in_polytope_2d(A, b)
    vertices = integer_hull_vertices_2d(A, b)

    assert len(points) == 17
    assert {tuple(vertex) for vertex in vertices} == expected_vertices
