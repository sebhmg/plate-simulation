# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                             '
#                                                                                      '
#  This file is part of plate-simulation package.                                      '
#                                                                                      '
#  plate-simulation is distributed under the terms and conditions of the MIT License   '
#  (see LICENSE file at the root of this source code package).                         '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoh5py.objects import Surface


def azimuth_to_unit_vector(azimuth: float) -> np.ndarray:
    """
    Convert an azimuth to a unit vector.

    :param azimuth: Azimuth in degrees from north (0 to 360).
    :return: Unit vector in the direction of the azimuth.
    """
    theta = np.deg2rad(azimuth)
    mat_z = np.r_[
        np.c_[np.cos(theta), -np.sin(theta), 0.0],
        np.c_[np.sin(theta), np.cos(theta), 0.0],
        np.c_[0.0, 0.0, 1.0],
    ]
    return np.array([0.0, 1.0, 0.0]).dot(mat_z)


def replicate(
    surface: Surface,
    number: int,
    spacing: float,
    azimuth: float,
) -> list[Surface]:
    """
    Replicate a plate n times along an azimuth centered at origin.

    Surface names will be indexed.

    :param surface: geoh5py.Surface to be replicated.
    :param number: Number of plates returned.
    :param spacing: Spacing between plates.
    :param azimuth: Azimuth of the axis along with plates are replicated.
    """

    offsets = (np.arange(number) * spacing) - ((number - 1) * spacing / 2)
    surfaces = [surface.copy() for i in range(number - 1)] + [surface]

    for i in range(number):
        surfaces[i].vertices += azimuth_to_unit_vector(azimuth) * offsets[i]
        surfaces[i].name = f"{surface.name} offset {i + 1}"

    return surfaces
