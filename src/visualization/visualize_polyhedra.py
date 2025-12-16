import matplotlib.pyplot as plt
import numpy as np


def visualize_polyhedron(A_mat: np.array, b_mat: np.array):
    """Plots the constraints of a polyhedron given by A*x <= b.

        TODO: Fill area between constraints (feasible region)

    :param A_mat: Constraint matrix
    :param b_mat: RHS vector of constraints
    :return:
    """
    plt.figure(figsize=(10, 5))

    x0 = np.linspace(-10, 10, 100).reshape(-1, 1)

    consts = []

    for i in range(A_mat.squeeze().shape[0]):

        x1 = (b_mat[i] - A_mat[i, 0] * x0) / A_mat[i, 1]
        x1 = x1.reshape(-1, 1)
        consts.append(x1)
        plt.plot(x0, x1, color="blue")

    plt.xlim((0, 10))
    plt.ylim((0, 10))

    # plt.legend()
    plt.show()
