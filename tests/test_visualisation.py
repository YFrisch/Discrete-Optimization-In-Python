import numpy as np

from src.visualization.visualize_polyhedra import visualize_polyhedron


def test_visualize_polyhedron_2d():

    A = np.array([
        [-1, 0],  # x >= 0
        [0, -1],  # y >= 0
        [1, 0],  # x <= 3
        [0, 1],  # y <= 3
        [1, 1],  # x + y <= 4
    ], dtype=float)

    b = np.array([0, 0, 3, 3, 4], dtype=float)

    visualize_polyhedron(A, b, xlim=(-1, 5), ylim=(-1, 5), title="2D test")

def test_visualize_polyhedron_3d():

    # Unit cube: 0<=x,y,z<=1
    A = np.array([
        [-1, 0, 0],
        [0, -1, 0],
        [0, 0, -1],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ], dtype=float)
    b = np.array([0, 0, 0, 1, 1, 1], dtype=float)

    visualize_polyhedron(A, b, xlim=(-0.2, 1.2), ylim=(-0.2, 1.2), zlim=(-0.2, 1.2), title="3D cube")
