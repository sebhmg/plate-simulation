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
    """Parameters for the plate simulation driver."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    workspace: Workspace
    topography: Surface
    octree: OctreeParams
    model: ModelParams
    simulation: SimPEGGroup
