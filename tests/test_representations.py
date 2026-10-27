import numpy as np

from src.polyhedra.representations import hrep_to_vertices_2d, vertices_to_hrep_2d


def test_bounded_polygon_hrep_vrep_round_trip():
    A = np.array(
        [
            [-1.0, 0.0],
            [0.0, -1.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
        ]
    )
    b = np.array([0.0, 0.0, 4.0, 3.0, 5.0])
    expected = np.array([[0.0, 0.0], [4.0, 0.0], [4.0, 1.0], [2.0, 3.0], [0.0, 3.0]])

    vertices = hrep_to_vertices_2d(A, b)
    A_round_trip, b_round_trip = vertices_to_hrep_2d(vertices)
    vertices_round_trip = hrep_to_vertices_2d(A_round_trip, b_round_trip)

    assert {tuple(np.round(v, 8)) for v in vertices} == {tuple(v) for v in expected}
    assert {tuple(np.round(v, 8)) for v in vertices_round_trip} == {tuple(v) for v in expected}
