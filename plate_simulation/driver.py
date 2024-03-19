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
from param_sweeps.generate import generate
from simpeg_drivers.driver import InversionDriver

from plate_simulation.logger import get_logger
from plate_simulation.models.events import Anomaly, Erosion, Overburden
from plate_simulation.models.plates import Plate
from plate_simulation.models.series import DikeSwarm, Scenario
from plate_simulation.params import PlateSimulationParams
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
        with fetch_active_workspace(self.params.geoh5, mode="r+"):
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
                self.params.geoh5,
                self.params.model.plate,
                *self.params.model.plate.center(self.survey, self.topography),
            )

            if self.params.model.plate.number == 1:
                self._surfaces = [plate.surface]
            else:
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
            value=self.params.model.overburden.overburden,
        )

        dikes = DikeSwarm(
            [Anomaly(s, self.params.model.plate.plate) for s in self.surfaces]
        )

        erosion = Erosion(
            surface=self.params.simulation.topography_object,
        )

        scenario = Scenario(
            workspace=self.params.geoh5,
            mesh=self.mesh,
            background=self.params.model.background,
            history=[dikes, overburden, erosion],
            name=self.params.model.name,
        )

        return scenario.geologize()

    @staticmethod
    def start(ifile: str | Path | InputFile):
        """Run the plate simulation driver from an input file."""

        if isinstance(ifile, str):
            ifile = Path(ifile)

        if isinstance(ifile, Path):
            ifile = InputFile.read_ui_json(ifile)

        if ifile.data is None:  # type: ignore
            raise ValueError("Input file has no data loaded.")

        generate_sweep = ifile.data["generate_sweep"]  # type: ignore
        if generate_sweep:
            filepath = Path(ifile.path_name)  # type: ignore
            ifile.data["generate_sweep"] = False  # type: ignore
            name = filepath.name
            path = filepath.parent
            ifile.write_ui_json(name=name, path=path)  # type: ignore
            generate(  # pylint: disable=unexpected-keyword-arg
                str(filepath), update_values={"conda_environment": "plate_simulation"}
            )
            return None

        with ifile.geoh5.open():  # type: ignore
            params = PlateSimulationParams.build(ifile)
            return PlateSimulationDriver(params).run()


if __name__ == "__main__":
    file = Path(sys.argv[1])
    PlateSimulationDriver.start(file)
