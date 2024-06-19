# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                             '
#                                                                                      '
#  This file is part of plate-simulation package.                                      '
#                                                                                      '
#  plate-simulation is distributed under the terms and conditions of the MIT License   '
#  (see LICENSE file at the root of this source code package).                         '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from typing import TypeVar

import numpy as np
from geoh5py.objects import ObjectBase, Surface
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
    model_validator,
)


T = TypeVar("T")


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
    :param easting: Easting offset relative to survey.
    :param northing: Northing offset relative to survey.
    :param elevation: plate(s) elevation.  May be true elevation or relative to
        overburden or topography.
    :param reference_surface: Switches between using topography and overburden as
        elevation reference of the plate.
    :param reference_type: Type of reference for plate elevation.  Can be 'mean'
        'min', or 'max'.  Resulting elevation will be relative to the mean,
        minimum, or maximum of the reference surface.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    plate: float
    width: float
    strike_length: float
    dip_length: float
    dip: float = 90.0
    dip_direction: float = 90.0
    number: int = 1
    spacing: float = 0.0
    relative_locations: bool = False
    easting: float = 0.0
    northing: float = 0.0
    elevation: float
    reference_surface: str = "topography"
    reference_type: str = "mean"

    @field_validator("reference_surface", "reference_type", mode="before")
    @classmethod
    def none_to_default(cls, value: T | None, info: ValidationInfo) -> T:
        return value or cls.model_fields[info.field_name].default  # type: ignore

    @model_validator(mode="after")
    def single_plate(self):
        if self.number == 1:
            self.spacing = 0.0
        return self

    @property
    def halfplate(self):
        """Compute half the z-projection length of the plate."""
        return 0.5 * self.dip_length * np.sin(np.deg2rad(self.dip))

    def center(
        self,
        survey: ObjectBase,
        surface: Surface,
        depth_offset: float = 0.0,
    ) -> list[float]:
        """
        Find the plate center relative to a survey and topography.

        :param survey: geoh5py survey object for plate simulation.
        :param surface: surface object to reference plate depth from.
        :param depth_offset: Additional offset to be added to the depth of the plate.
        """
        return [*self._get_xy(survey), self._get_z(surface, depth_offset)]

    def _get_xy(self, survey: ObjectBase) -> list[float]:
        """Return true or relative locations in x and y."""
        if self.relative_locations:
            xy = [
                survey.vertices[:, 0].mean() + self.easting,
                survey.vertices[:, 1].mean() + self.northing,
            ]
        else:
            xy = [self.easting, self.northing]

        return xy

    def _get_z(self, surface: Surface, offset: float = 0.0) -> float:
        """
        Return true or relative locations in z.

        :param surface: Surface object to reference plate depth from.
        :offset: Additional offset to be added to the depth.

        """
        if surface.vertices is None:
            raise ValueError("Topography object has no vertices.")
        if self.relative_locations:
            z = getattr(surface.vertices[:, 2], self.reference_type)()
            z += offset + self.elevation - self.halfplate
        else:
            z = self.elevation

        return z


class OverburdenParams(BaseModel):
    """
    Parameters for the overburden layer.

    :param thickness: Thickness of the overburden layer.
    :param overburden: Value given to the overburden layer.
    """

    thickness: float
    overburden: float


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
