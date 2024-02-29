#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from pathlib import Path

from geoh5py.objects import ObjectBase, Surface
from octree_creation_app.params import OctreeParams
from pydantic import BaseModel


class MeshParams(BaseModel):
    """Core parameters for octree mesh creation."""

    u_cell_size: float
    v_cell_size: float
    w_cell_size: float
    padding_distance: float
    depth_core: float
    max_distance: float
    minimum_level: int = 8
    diagonal_balance: bool = False

    def octree_params(self, survey: ObjectBase, topography: Surface, plate: Surface):
        refinements = {
            "Refinement A object": topography,
            "Refinement A levels": [0, 2],
            "Refinement A type": "surface",
            "Refinement B object": survey,
            "Refinement B levels": [4, 2],
            "Refinement B type": "radial",
            "Refinement C object": plate,
            "Refinement C levels": [2, 1],
            "Refinement C type": "surface",
        }
        octree_params = OctreeParams(
            geoh5=plate.workspace,
            objects=survey,
            u_cell_size=self.u_cell_size,
            v_cell_size=self.v_cell_size,
            w_cell_size=self.w_cell_size,
            padding_distance=self.padding_distance,
            depth_core=self.depth_core,
            max_distance=self.max_distance,
            minimum_level=self.minimum_level,
            diagonal_balance=self.diagonal_balance,
            **refinements
        )
        assert isinstance(survey.workspace.h5file, Path)
        path = survey.workspace.h5file.parent
        octree_params.input_file.write_ui_json(name="octree.ui.json", path=path)
        return octree_params
