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
from geoh5py import Workspace
from geoh5py.objects import Surface
from geoh5py.shared.utils import fetch_active_workspace

from plate_simulation.models.params import PlateParams


class Plate:
    """
    Define a rotated rectangular block in 3D space

    :param workspace: Workspace to create the plate surface in.
    :param params: Parameters describing the plate.
    :param surface: Surface object representing the plate.
    """

    def __init__(self, workspace: Workspace, params: PlateParams):
        self.workspace = workspace
        self.params = params
        self._surface: Surface | None = None

    @property
    def surface(self) -> Surface:
        """Surface of plate"""

        if self._surface is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._surface = Surface.create(
                    self.workspace,
                    vertices=self.vertices,
                    cells=self.triangles,
                    name=self.params.name,
                )
        return self._surface

    @property
    def center(self) -> Sequence[float]:
        """Center of the block."""
        return [
            self.params.center_x,
            self.params.center_y,
            self.params.center_z,
        ]

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

        x_1 = self.params.center_x - (self.params.strike_length / 2.0)
        x_2 = self.params.center_x + (self.params.strike_length / 2.0)
        y_1 = self.params.center_y - (self.params.width / 2.0)
        y_2 = self.params.center_y + (self.params.width / 2.0)
        z_1 = self.params.center_z - (self.params.dip_length / 2.0)
        z_2 = self.params.center_z + (self.params.dip_length / 2.0)

        vertices = np.array(
            [
                [x_1, y_1, z_1],
                [x_2, y_1, z_1],
                [x_1, y_2, z_1],
                [x_2, y_2, z_1],
                [x_1, y_1, z_2],
                [x_2, y_1, z_2],
                [x_1, y_2, z_2],
                [x_2, y_2, z_2],
            ]
        )

        return self._rotate(vertices)

    def _rotate(self, vertices: np.ndarray) -> np.ndarray:
        """Rotate vertices and adjust for reference point."""

        theta = (450.0 - np.asarray(self.params.dip_direction)) % 360.0
        phi = self.params.dip
        rotated_vertices = rotate_xyz(vertices, self.center, theta, phi)

        if self.params.reference == "top":
            offset = np.mean(rotated_vertices[4:, :], axis=0) - self.center
            self.params.center_x -= offset[0]
            self.params.center_y -= offset[1]
            self.params.center_z -= offset[2]
            rotated_vertices -= offset

        return rotated_vertices
