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
from pydantic import BaseModel, ConfigDict

from plate_simulation.models.params import PlateParams


class Plate(BaseModel):
    """
    Define a rotated rectangular block in 3D space
    :param center_x: X-coordinate of the center of the block.
    :param center_y: Y-coordinate of the center of the block.
    :param center_z: Z-coordinate of the center of the block.
    :param length: U-size of the block.
    :param width:  V-size of the block.
    :param depth:  W-size of the block.
    :param dip: Orientation of the u-axis in degree from horizontal.
    :param azimuth: Orientation of the u axis in degree from north.
    :param reference: Point of rotation to be 'center' or 'top'.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    workspace: Workspace
    center_x: float
    center_y: float
    center_z: float
    length: float
    width: float
    depth: float
    dip: float = 0.0
    azimuth: float = 0.0
    reference: str = "center"
    _surface: Surface | None = None

    @classmethod
    def from_params(cls, params: PlateParams):
        return cls(**params.__dict__)

    @property
    def surface(self) -> Surface:
        """Surface of plate"""

        if self._surface is None:
            self._surface = Surface.create(
                self.workspace,
                vertices=self.vertices,
                cells=self.triangles,
                name=self.name,
            )
        return self._surface

    @property
    def center(self) -> Sequence[float]:
        """Center of the block."""
        return [
            self.center_x,  # pylint: disable=no-member
            self.center_y,  # pylint: disable=no-member
            self.center_z,  # pylint: disable=no-member
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

        x_1 = self.center_x - (self.length / 2.0) # pylint:disable=no-member
        x_2 = self.center_x + (self.length / 2.0) # pylint:disable=no-member
        y_1 = self.center_y - (self.width / 2.0) # pylint:disable=no-member
        y_2 = self.center_y + (self.width / 2.0) # pylint:disable=no-member
        z_1 = self.center_z - (self.depth / 2.0) # pylint:disable=no-member
        z_2 = self.center_z + (self.depth / 2.0) # pylint:disable=no-member

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

        theta = (450.0 - np.asarray(self.azimuth)) % 360.0
        phi = -self.dip
        rotated_vertices = rotate_xyz(vertices, self.center, theta, phi)

        if self.reference == "top":
            offset = np.mean(rotated_vertices[4:, :], axis=0) - self.center
            self.center_x -= offset[0] # pylint: disable=no-member
            self.center_y -= offset[1] # pylint: disable=no-member
            self.center_z -= offset[2] # pylint: disable=no-member
            rotated_vertices -= offset

        return rotated_vertices
