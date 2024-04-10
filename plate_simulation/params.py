#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from geoapps_utils.driver.data import BaseData
from geoapps_utils.driver.params import BaseParams
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from geoh5py.shared.utils import fetch_active_workspace
from pydantic import field_validator

from .mesh.params import MeshParams
from .models.params import ModelParams
from .simulations.params import SimulationParams


class PlateSimulationParams(BaseData):
    """
    Parameters for the plate simulation driver.

    geoh5: Workspace in which the model will be built and results stored.
    mesh: Parameters for the octree mesh.
    model: Parameters for the background + overburden and plate model.
    simulation: Simpeg group containing simulation options and a survey.  Any
        mesh or starting model selections will be replaced by the objects
        created by the driver.
    """

    geoh5: Workspace
    mesh: MeshParams
    model: ModelParams
    simulation: BaseParams

    @field_validator("simulation", mode="before")
    @classmethod
    def simpeg_group_to_params(cls, value: SimPEGGroup) -> BaseParams:
        if value.options is None:
            raise ValueError("SimPEGGroup must have an options dictionary.")

        with fetch_active_workspace(value.workspace, mode="r+"):
            simulation_params = SimulationParams.from_simpeg_group(
                value, workspace=value.workspace
            )
            return simulation_params
