#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np
from geoh5py.objects import Points, Surface
from SimPEG import utils


def get_survey(workspace, n_receivers, n_lines):
    X, Y = np.meshgrid(
        np.linspace(-250, 250, n_receivers), np.linspace(-250, 250, n_lines)
    )
    Z = np.zeros_like(X)

    vertices = np.c_[
        utils.mkvc(X.T),
        utils.mkvc(Y.T),
        utils.mkvc(Z.T),
    ]

    return Points.create(
        workspace,
        vertices=vertices,
        name="survey",
    )


def get_topography(workspace):
    vertices = np.array(
        [
            [-500.0, -500.0, 0.0],
            [500.0, -500.0, 0.0],
            [500.0, 500.0, 0.0],
            [-500.0, 500.0, 0.0],
        ]
    )
    cells = np.array([[0, 1, 2], [0, 2, 3]])

    return Surface.create(workspace, name="topo", vertices=vertices, cells=cells)
