#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from __future__ import annotations

from pathlib import Path

import numpy as np
from geoh5py.objects import Octree
from geoh5py.ui_json import InputFile
from octree_creation_app.constants import default_ui_json
from octree_creation_app.driver import OctreeDriver
from octree_creation_app.params import OctreeParams
from simpeg_drivers.driver import InversionDriver

from .models.events import Anomaly, Erosion, Overburden
from .models.plates import Plate
from .models.series import Scenario
from .params import PlateSimulationParams
from .simulations.params import SimulationParams


class PlateSimulationDriver:
    def __init__(self, params: PlateSimulationParams):
        self.params = params
        self._plate: Plate | None = None
        self._mesh: Octree | None = None
        self._model: np.ndarray | None = None

    def run(self):
        """Create octree mesh, fill model, and simulate."""

        params = SimulationParams.from_simpeg_group(self.params.simulation)
        params.data_object = self.survey
        params.mesh = self.mesh
        params.starting_model = self.model
        driver = InversionDriver(params)
        driver.run()
        return self.model

    @property
    def survey(self):
        assert (
            self.params.simulation.options is not None
        ), "SimPEGGroup options must be set."
        survey = self.params.simulation.options["data_object"]["value"]
        # TODO: why do I need to open here?
        survey.workspace.open()
        return survey

    @property
    def mesh(self):
        if self._mesh is None:
            self._mesh = self.make_mesh()

        return self._mesh

    @property
    def plate(self):
        if self._plate is None:
            self._plate = Plate(self.params.workspace, self.params.model.plate)

        return self._plate

    @property
    def model(self):
        if self._model is None:
            self._model = self.make_model()

        return self._model

    def make_mesh(self):
        # TODO Prefer to dump params directly to OctreeParams.  Need to fix
        #   octree-creation-app/driver.run method.
        kwargs = {
            "geoh5": self.params.workspace,
            "objects": self.survey,
            "u_cell_size": self.params.octree.u_cell_size,
            "v_cell_size": self.params.octree.v_cell_size,
            "w_cell_size": self.params.octree.w_cell_size,
            "horizontal_padding": self.params.octree.horizontal_padding,
            "vertical_padding": self.params.octree.vertical_padding,
            "depth_core": self.params.octree.depth_core,
            "minimum_level": self.params.octree.minimum_level,
            "diagonal_balance": self.params.octree.diagonal_balance,
            "Refinement A object": self.params.topography,
            "Refinement A levels": [0, 2],
            "Refinement A type": "surface",
            "Refinement B object": self.survey,
            "Refinement B levels": [4, 2],
            "Refinement B type": "radial",
            "Refinement C object": self.plate.surface,
            "Refinement C levels": [4, 2],
            "Refinement C type": "surface",
        }
        ifile = InputFile(ui_json=dict(default_ui_json, **kwargs), validate=False)
        if not isinstance(self.params.workspace.h5file, Path):
            raise ValueError("Workspace h5file must be a Path object.")
        ifile.write_ui_json(
            name="octree.ui.json", path=self.params.workspace.h5file.parent
        )
        params = OctreeParams(ifile)

        octree_driver = OctreeDriver(params)
        return octree_driver.run()

    def make_model(self):
        overburden = Overburden(
            topography=self.params.topography,
            thickness=self.params.model.overburden.thickness,
            value=self.params.model.overburden.value,
        )

        anomaly = Anomaly(
            surface=self.plate.surface, value=self.params.model.plate.anomaly
        )

        erosion = Erosion(
            surface=self.params.topography,
        )

        scenario = Scenario(
            mesh=self.mesh,
            background=self.params.model.background,
            history=[anomaly, overburden, erosion],
            name=self.params.model.name,
        )

        return scenario.geologize()
