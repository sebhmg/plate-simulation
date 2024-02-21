#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from __future__ import annotations

import sys
from pathlib import Path

from geoh5py.data import FloatData
from geoh5py.objects import Octree, Points
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from octree_creation_app.driver import OctreeDriver
from simpeg_drivers.driver import InversionDriver

from .mesh.params import MeshParams
from .models.events import Anomaly, Erosion, Overburden
from .models.params import ModelParams, OverburdenParams, PlateParams
from .models.plates import Plate
from .models.series import Scenario
from .params import PlateSimulationParams
from .simulations.params import SimulationParams


class PlateSimulationDriver:
    """
    Driver for simulating background + plate + overburden model.

    :param params: Parameters for plate simulation (mesh, model and
        simulations).
    :param plate: Plate object used to add anomaly to the model.
    :param mesh: Octree mesh in which model is built for the simulation.
    :param model: Model to simulate.
    :param survey: Survey object for the simulation
    """

    def __init__(self, params: PlateSimulationParams):
        self.params = params
        self._plate: Plate | None = None
        self._survey: Points | None = None
        self._mesh: Octree | None = None
        self._model: FloatData | None = None

    def run(self) -> FloatData:
        """Create octree mesh, fill model, and simulate."""
        with fetch_active_workspace(self.params.workspace, mode="r+"):
            self.params.simulation.mesh = self.mesh
            self.params.simulation.starting_model = self.model
            driver = InversionDriver(self.params.simulation)
            print("running the simulation...")
            driver.run()
            print("done.")

        return self.model

    @property
    def survey(self):
        if self._survey is None:
            self._survey = self.params.simulation.data_object

        return self._survey

    @property
    def mesh(self) -> Octree:
        """Returns an octree mesh built from mesh parameters."""
        if self._mesh is None:
            self._mesh = self.make_mesh()

        return self._mesh

    @property
    def plate(self) -> Plate:
        """Returns the plate object built from plate parameters."""
        if self._plate is None:
            self._plate = Plate(self.params.workspace, self.params.model.plate)

        return self._plate

    @property
    def model(self) -> FloatData:
        """Returns the model built from model parameters."""
        if self._model is None:
            self._model = self.make_model()

        return self._model

    def make_mesh(self) -> Octree:
        """
        Build specialized mesh for plate simulation from parameters.

        Mesh contains refinements for topography and any plates.
        """

        print("making the mesh...")
        octree_params = self.params.mesh.octree_params(
            self.survey, self.params.simulation.topography_object, self.plate.surface
        )
        octree_driver = OctreeDriver(octree_params)
        with self.survey.workspace.open():
            mesh = octree_driver.run()

        return mesh

    def make_model(self) -> FloatData:
        """Create background + plate and overburden model from parameters."""

        print("building the model...")
        overburden = Overburden(
            topography=self.params.simulation.topography_object,
            thickness=self.params.model.overburden.thickness,
            value=self.params.model.overburden.value,
        )

        anomaly = Anomaly(
            surface=self.plate.surface, value=self.params.model.plate.anomaly
        )

        erosion = Erosion(
            surface=self.params.simulation.topography_object,
        )

        scenario = Scenario(
            workspace=self.params.workspace,
            mesh=self.mesh,
            background=self.params.model.background,
            history=[anomaly, overburden, erosion],
            name=self.params.model.name,
        )

        return scenario.geologize()

    @staticmethod
    def params_from_input_file(ifile: InputFile) -> PlateSimulationParams:
        """Parse a plate simulation input file into parameter object."""

        if ifile.data is None:
            raise ValueError("Input file has no data loaded.")
        mesh_params = MeshParams(
            u_cell_size=ifile.data["u_cell_size"],
            v_cell_size=ifile.data["v_cell_size"],
            w_cell_size=ifile.data["w_cell_size"],
            padding_distance=ifile.data["padding_distance"],
            depth_core=ifile.data["depth_core"],
            max_distance=ifile.data["max_distance"],
        )

        overburden_params = OverburdenParams(
            thickness=ifile.data["thickness"], value=ifile.data["overburden"]
        )
        plate_params = PlateParams(
            name="plate",
            anomaly=ifile.data["plate"],
            center_x=ifile.data["center_x"],
            center_y=ifile.data["center_y"],
            center_z=ifile.data["center_z"],
            width=ifile.data["width"],
            strike_length=ifile.data["strike_length"],
            dip_length=ifile.data["dip_length"],
            dip=ifile.data["dip"],
            dip_direction=ifile.data["dip_direction"],
        )
        simulation = ifile.data["simulation"]
        with fetch_active_workspace(simulation.workspace, mode="r+"):
            simulation.options["geoh5"] = str(simulation.workspace.h5file)
            simulation_params = SimulationParams.from_simpeg_group(simulation)

        params = PlateSimulationParams(
            workspace=ifile.geoh5,
            mesh=mesh_params,
            model=ModelParams(
                name=ifile.data["name"],
                background=ifile.data["background"],
                overburden=overburden_params,
                plate=plate_params,
            ),
            simulation=simulation_params,
        )

        return params

    @staticmethod
    def main(ifile: Path | InputFile):
        """Run the plate simulation driver from an input file."""

        if isinstance(ifile, Path):
            ifile = InputFile.read_ui_json(ifile)

        if ifile.data is None:  # type: ignore
            raise ValueError("Input file has no data loaded.")

        params = PlateSimulationDriver.params_from_input_file(ifile)  # type: ignore
        _ = PlateSimulationDriver(params).run()


if __name__ == "__main__":
    PlateSimulationDriver.main(Path(sys.argv[1]))
