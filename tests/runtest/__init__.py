#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np
from geoh5py.objects import Points, Surface
from geoh5py.objects.surveys.electromagnetics.airborne_tem import (
    AirborneTEMReceivers,
    AirborneTEMTransmitters,
)
from SimPEG import utils


def get_tem_survey(workspace, n_receivers, n_lines):
    X, Y = np.meshgrid(  # pylint: disable=invalid-name
        np.linspace(-250, 250, n_receivers), np.linspace(-250, 250, n_lines)
    )
    Z = np.zeros_like(X)  # pylint: disable=invalid-name

    vertices = np.c_[
        utils.mkvc(X.T),
        utils.mkvc(Y.T),
        utils.mkvc(Z.T),
    ]

    survey = AirborneTEMReceivers.create(
        workspace, vertices=vertices, name="Airborne_rx"
    )
    transmitters = AirborneTEMTransmitters.create(
        workspace, vertices=vertices, name="Airborne_tx"
    )

    dist = np.linalg.norm(
        survey.vertices[survey.cells[:, 0], :] - survey.vertices[survey.cells[:, 1], :],
        axis=1,
    )
    if n_lines > 1:
        survey.remove_cells(np.where(dist > 200.0)[0])
        transmitters.remove_cells(np.where(dist > 200.0)[0])
    survey.transmitters = transmitters

    survey.channels = np.r_[3e-04, 6e-04, 1.2e-03] * 1e3
    waveform = np.c_[
        np.r_[
            np.arange(-0.002, -0.0001, 5e-4),
            np.arange(-0.0004, 0.0, 1e-4),
            np.arange(0.0, 0.002, 5e-4),
        ]
        * 1e3
        + 2.0,
        np.r_[np.linspace(0, 1, 4), np.linspace(0.9, 0.0, 4), np.zeros(4)],
    ]
    survey.waveform = waveform
    survey.timing_mark = 2.0
    survey.unit = "Milliseconds (ms)"

    return survey


def get_survey(workspace, n_receivers, n_lines):
    X, Y = np.meshgrid(  # pylint: disable=invalid-name
        np.linspace(-250, 250, n_receivers), np.linspace(-250, 250, n_lines)
    )
    Z = np.zeros_like(X)  # pylint: disable=invalid-name

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
