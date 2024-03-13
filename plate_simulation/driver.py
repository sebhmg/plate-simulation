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
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import Octree, Points, Surface
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from octree_creation_app.driver import OctreeDriver
from simpeg_drivers.driver import InversionDriver

from plate_simulation.logger import get_logger
from plate_simulation.mesh.params import MeshParams
from plate_simulation.models.events import Anomaly, Erosion, Overburden
from plate_simulation.models.params import ModelParams, OverburdenParams, PlateParams
from plate_simulation.models.plates import Plate
from plate_simulation.models.series import DikeSwarm, Scenario
from plate_simulation.params import PlateSimulationParams
from plate_simulation.simulations.params import SimulationParams
from plate_simulation.utils import replicate


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
        self._surfaces: list[Surface] | None = None
        self._survey: Points | None = None
        self._mesh: Octree | None = None
        self._model: FloatData | None = None
        self._logger = get_logger("Plate Simulation")

    def run(self) -> SimPEGGroup:
        """Create octree mesh, fill model, and simulate."""
        with fetch_active_workspace(self.params.workspace, mode="r+"):
            self.params.simulation.mesh = self.mesh
            self.params.simulation.starting_model = self.model

            if not isinstance(self.params.simulation.topography_object, Surface):
                raise ValueError(
                    "The topography object of the forward simulation must be a 'Surface'."
                )

        driver = InversionDriver(self.params.simulation)
        self._logger.info("running the simulation...")

        driver.run()
        self._logger.info("done.")

        return driver.out_group

    @property
    def survey(self):
        if self._survey is None:
            self._survey = self.params.simulation.data_object

        return self._survey

    @property
    def topography(self) -> Surface:
        return self.params.simulation.topography_object

    @property
    def surfaces(self) -> list[Surface]:
        """Returns a list of surfaces representing the plates for simulation."""

        if self._surfaces is None:
            plate = Plate(
                self.params.workspace,
                self.params.model.plate,
                *self.params.model.plate.center(
                    self.survey, self.topography, self.params.model.plate.true_elevation
                ),
            )

            self._surfaces = replicate(
                plate.surface,
                self.params.model.plate.number,
                self.params.model.plate.spacing,
                self.params.model.plate.dip_direction,
            )

        return self._surfaces

    @property
    def mesh(self) -> Octree:
        """Returns an octree mesh built from mesh parameters."""
        if self._mesh is None:
            self._mesh = self.make_mesh()

        return self._mesh

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

        self._logger.info("making the mesh...")
        octree_params = self.params.mesh.octree_params(
            self.survey, self.params.simulation.topography_object, self.surfaces
        )
        octree_driver = OctreeDriver(octree_params)
        mesh = octree_driver.run()

        return mesh

    def make_model(self) -> FloatData:
        """Create background + plate and overburden model from parameters."""

        self._logger.info("Building the model...")

        overburden = Overburden(
            topography=self.params.simulation.topography_object,
            thickness=self.params.model.overburden.thickness,
            value=self.params.model.overburden.value,
        )

        dikes = DikeSwarm(
            [Anomaly(s, self.params.model.plate.value) for s in self.surfaces]
        )

        erosion = Erosion(
            surface=self.params.simulation.topography_object,
        )

        scenario = Scenario(
            workspace=self.params.workspace,
            mesh=self.mesh,
            background=self.params.model.background,
            history=[dikes, overburden, erosion],
            name=self.params.model.name,
        )

        return scenario.geologize()

    @staticmethod
    def _mesh_params_from_input_file(ifile: InputFile) -> MeshParams:
        """Parse a plate simulation input file into mesh parameter object."""

        return MeshParams(
            u_cell_size=ifile.data["u_cell_size"],  # type: ignore
            v_cell_size=ifile.data["v_cell_size"],  # type: ignore
            w_cell_size=ifile.data["w_cell_size"],  # type: ignore
            padding_distance=ifile.data["padding_distance"],  # type: ignore
            depth_core=ifile.data["depth_core"],  # type: ignore
            max_distance=ifile.data["max_distance"],  # type: ignore
        )

    @staticmethod
    def _overburden_params_from_input_file(ifile: InputFile) -> OverburdenParams:
        """
        Parse a plate simulation input file into overburden parameter object.

        Converts ui.json resistivity to conductivity.
        """

        return OverburdenParams(
            thickness=ifile.data["thickness"],  # type: ignore
            value=1.0 / ifile.data["overburden"],  # type: ignore
        )

    @staticmethod
    def _plate_params_from_input_file(ifile: InputFile) -> PlateParams:
        """
        Parse a plate simulation input file into plate parameter object.

        Converts ui.json resistivity to conductivity.
        """

        return PlateParams(
            name="plate",
            value=1.0 / ifile.data["plate"],  # type: ignore
            width=ifile.data["width"],  # type: ignore
            depth=ifile.data["depth"],  # type: ignore
            strike_length=ifile.data["strike_length"],  # type: ignore
            dip_length=ifile.data["dip_length"],  # type: ignore
            dip=ifile.data["dip"],  # type: ignore
            dip_direction=ifile.data["dip_direction"],  # type: ignore
            true_elevation=ifile.data["true_elevation"],  # type: ignore
            number=ifile.data["number"],  # type: ignore
            spacing=ifile.data["spacing"],  # type: ignore
            x_offset=ifile.data["x_offset"],  # type: ignore
            y_offset=ifile.data["y_offset"],  # type: ignore
        )

    @staticmethod
    def _simulation_params_from_input_file(ifile: InputFile) -> SimulationParams:
        """Parse a plate simulation input file into simulation parameter object."""

        simulation = ifile.data["simulation"]  # type: ignore
        with fetch_active_workspace(ifile.geoh5, mode="r+"):
            simulation.options["geoh5"] = str(ifile.geoh5.h5file)
            simulation_params = SimulationParams.from_simpeg_group(
                simulation, ifile.geoh5
            )

        return simulation_params

    @staticmethod
    def _model_params_from_input_file(ifile: InputFile) -> ModelParams:
        """
        Parse a plate simulation input file into model parameter object.

        Converts ui.json resistivity to conductivity.
        """

        overburden_params = PlateSimulationDriver._overburden_params_from_input_file(
            ifile
        )
        plate_params = PlateSimulationDriver._plate_params_from_input_file(ifile)

        return ModelParams(
            name=ifile.data["name"],  # type: ignore
            background=1.0 / ifile.data["background"],  # type: ignore
            overburden=overburden_params,
            plate=plate_params,
        )

    @staticmethod
    def params_from_input_file(ifile: InputFile) -> PlateSimulationParams:
        """Parse a plate simulation input file into parameter object."""

        if ifile.data is None:
            raise ValueError("Input file has no data loaded.")

        mesh_params = PlateSimulationDriver._mesh_params_from_input_file(ifile)
        model_params = PlateSimulationDriver._model_params_from_input_file(ifile)
        simulation_params = PlateSimulationDriver._simulation_params_from_input_file(
            ifile
        )

        # TODO: Once BaseData.build is updated to handle n levels of nesting, call here.
        params = PlateSimulationParams(
            workspace=ifile.geoh5,
            mesh=mesh_params,
            model=model_params,
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

        return PlateSimulationDriver(params).run()


if __name__ == "__main__":
    file = Path(sys.argv[1])
    PlateSimulationDriver.main(file)
