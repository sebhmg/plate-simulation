#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from pydantic import BaseModel, ConfigDict, model_validator


class PlateParams(BaseModel):
    """
    Parameters describing an anomalous plate.

    :param name: Name to be given to the geoh5py Surface object
        representing the plate(s).
    :param plate: Value given to the plate(s).
    :param x_offset: plate(s) easting offset relative to survey.
    :param y_offset: plate(s) northing offset relative to survey.
    :param depth: plate(s) depth relative to mean topography.
    :param width: V-size of the plate.
    :param strike_length: U-size of the plate.
    :param dip_length: W-size of the plate.
    :param dip: Orientation of the v-axis in degree from horizontal.
    :param dip_direction: Orientation of the u axis in degree from north.
    :param reference: Point of rotation to be 'center' or 'top'.
    :param number: Number of offset plates to be created.
    :param spacing: Spacing between plates.
    :param x_offset: Easting offset relative to survey.
    :param y_offset: Northing offset relative to survey.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    value: float
    depth: float
    width: float
    strike_length: float
    dip_length: float
    dip: float = 90.0
    dip_direction: float = 90.0
    reference: str = "center"
    number: int = 1
    spacing: float = 0.0
    x_offset: float = 0.0
    y_offset: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def single_plate(cls, data: dict):
        if "number" in data and data["number"] == 1:
            data.pop("spacing")
        return data


class OverburdenParams(BaseModel):
    """
    Parameters for the overburden layer.

    :param thickness: Thickness of the overburden layer.
    :param overburden: Value given to the overburden layer.
    """

    thickness: float
    value: float


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
