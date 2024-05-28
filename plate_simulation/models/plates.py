#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from geoapps_utils.transformations import rotate_xyz

from plate_simulation.models.params import PlateParams


class Plate:
    """
    Define a rotated rectangular block in 3D space

    :param params: Parameters describing the plate.
    :param surface: Surface object representing the plate.
    """

    def __init__(
        self,
        params: PlateParams,
        center_x: float = 0.0,
        center_y: float = 0.0,
        center_z: float = 0.0,
    ):
        self.params = params
        self.center_x = center_x
        self.center_y = center_y
        self.center_z = center_z

    @property
    def center(self) -> Sequence[float]:
        """Center of the block."""
        return [self.center_x, self.center_y, self.center_z]

    @property
    def triangles(self) -> np.ndarray:
        """Triangulation of the block."""
        return np.vstack(
            [
                [0, 2, 1],
                [1, 2, 3],
                [0, 1, 4],
                [4, 1, 5],
                [1, 3, 5],
                [5, 3, 7],
                [2, 6, 3],
                [3, 6, 7],
                [0, 4, 2],
                [2, 4, 6],
                [4, 5, 6],
                [6, 5, 7],
            ]
        )

    @property
    def vertices(self) -> np.ndarray:
        """Vertices for triangulation of a rectangular prism in 3D space."""

        u_1 = self.center_x - (self.params.strike_length / 2.0)
        u_2 = self.center_x + (self.params.strike_length / 2.0)
        v_1 = self.center_y - (self.params.dip_length / 2.0)
        v_2 = self.center_y + (self.params.dip_length / 2.0)
        w_1 = self.center_z - (self.params.width / 2.0)
        w_2 = self.center_z + (self.params.width / 2.0)

        vertices = np.array(
            [
                [u_1, v_1, w_1],
                [u_2, v_1, w_1],
                [u_1, v_2, w_1],
                [u_2, v_2, w_1],
                [u_1, v_1, w_2],
                [u_2, v_1, w_2],
                [u_1, v_2, w_2],
                [u_2, v_2, w_2],
            ]
        )

        return self._rotate(vertices)

    def _rotate(self, vertices: np.ndarray) -> np.ndarray:
        """Rotate vertices and adjust for reference point."""
        theta = -1 * self.params.dip_direction
        phi = -1 * self.params.dip
        rotated_vertices = rotate_xyz(vertices, self.center, theta, phi)

        return rotated_vertices
