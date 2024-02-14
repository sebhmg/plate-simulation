#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import Surface
from octree_creation_app.params import OctreeParams
from pydantic import BaseModel, ConfigDict

from .models.params import ModelParams


class PlateSimulationParams(BaseModel):
    """
    Parameters for the plate simulation driver.

    workspace: Workspace in which the model will be built and results stored.
    topography: Surface object representing the topography.
    octree: Parameters for the octree mesh.
    model: Parameters for the background + overburden and plate model.
    simulation: Simpeg group containing simulation options and a survey.  Any
        mesh or starting model selections will be replaced by the objects
        created by the driver.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    workspace: Workspace
    topography: Surface
    octree: OctreeParams
    model: ModelParams
    simulation: SimPEGGroup
