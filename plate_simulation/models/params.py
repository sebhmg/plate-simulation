#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np
from geoh5py.objects import ObjectBase, Surface
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class PlateParams(BaseModel):
    """
    Parameters describing an anomalous plate.

    :param name: Name to be given to the geoh5py Surface object
        representing the plate(s).
    :param plate: Value given to the plate(s).
    :param width: V-size of the plate.
    :param strike_length: U-size of the plate.
    :param dip_length: W-size of the plate.
    :param dip: Orientation of the v-axis in degree from horizontal.
    :param dip_direction: Orientation of the u axis in degree from north.
    :param reference: Point of rotation to be 'center' or 'top'.
    :param number: Number of offset plates to be created.
    :param spacing: Spacing between plates.
    :param relative_locations: If True locations are relative to survey in xy and
        mean topography in z.
    :param x_location: Easting offset relative to survey.
    :param y_location: Northing offset relative to survey.
    :param depth: plate(s) depth relative to mean topography.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    plate: float
    width: float
    strike_length: float
    dip_length: float
    dip: float = 90.0
    dip_direction: float = 90.0
    reference: str = "center"
    number: int = 1
    spacing: float = 0.0
    relative_locations: bool = False
    x_location: float = 0.0
    y_location: float = 0.0
    depth: float

    @field_validator("plate", mode="before")
    @classmethod
    def reciprocal(cls, value: float) -> float:
        return 1.0 / value

    @model_validator(mode="after")
    def single_plate(self):
        if self.number == 1:
            self.spacing = 0.0
        return self

    @property
    def halfplate(self):
        """Compute half the z-projection length of the plate."""
        return 0.5 * self.dip_length * np.sin(np.deg2rad(self.dip))

    def center(self, survey: ObjectBase, topography: Surface) -> list[float]:
        """
        Find the plate center relative to a survey and topography.

        :param survey: geoh5py survey object for plate simulation.
        :param topography: topography object.
        """
        return self._get_xy(survey) + [self._get_z(topography)]

    def _get_xy(self, survey: ObjectBase) -> list[float]:
        """Return true or relative locations in x and y."""
        if self.relative_locations:
            xy = [
                survey.vertices[:, 0].mean() + self.x_location,
                survey.vertices[:, 1].mean() + self.y_location,
            ]
        else:
            xy = [self.x_location, self.y_location]

        return xy

    def _get_z(self, topography: Surface) -> float:
        """Return true or relative locations in z."""
        if topography.vertices is None:
            raise ValueError("Topography object has no vertices.")
        if self.relative_locations:
            z = topography.vertices[:, 2].mean() - self.depth - self.halfplate
        else:
            z = self.depth

        return z


class OverburdenParams(BaseModel):
    """
    Parameters for the overburden layer.

    :param thickness: Thickness of the overburden layer.
    :param overburden: Value given to the overburden layer.
    """

    thickness: float
    overburden: float

    @field_validator("overburden", mode="before")
    @classmethod
    def reciprocal(cls, value: float) -> float:
        return 1.0 / value


class ModelParams(BaseModel):
    """
    Parameters for the blackground + overburden and plate model.

    :param name: Name to be given to the model.
    :param background: Value given to the background.
    :param overburden: Overburden layer parameters.
    :param plate: Plate parameters.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    background: float
    overburden: OverburdenParams
    plate: PlateParams

    @field_validator("background", mode="before")
    @classmethod
    def reciprocal(cls, value: float) -> float:
        return 1.0 / value
