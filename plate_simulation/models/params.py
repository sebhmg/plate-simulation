#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from geoh5py import Workspace
from pydantic import BaseModel, ConfigDict


class PlateParams(BaseModel):
    """
    Parameters describing an anomalous plate.

    :param name: Name to be given to the geoh5py Surface object
        representing the plate.
    :param anomaly: Value given to the plate.
    :param center_x: X-coordinate of the center of the plate.
    :param center_y: Y-coordinate of the center of the plate.
    :param center_z: Z-coordinate of the center of the plate.
    :param length: U-size of the plate.
    :param width: V-size of the plate.
    :param depth: W-size of the plate.
    :param dip: Orientation of the u-axis in degree from horizontal.
    :param azimuth: Orientation of the u axis in degree from north.
    :param reference: Point of rotation to be 'center' or 'top'.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    workspace: Workspace
    anomaly: float
    center_x: float
    center_y: float
    center_z: float
    length: float
    width: float
    depth: float
    dip: float = 0.0
    azimuth: float = 0.0
    reference: str = "center"


class OverburdenParams(BaseModel):
    """
    Parameters for the overburden layer.

    :param thickness: Thickness of the overburden layer.
    :param value: Value given to the overburden layer.
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
