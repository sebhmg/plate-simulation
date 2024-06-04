#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

# pylint: disable=duplicate-code

from __future__ import annotations

from pathlib import Path

from geoh5py.data import FloatData
from geoh5py.groups import UIJsonGroup
from geoh5py.objects import Octree, Points, Surface
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile, monitored_directory_copy
from octree_creation_app.driver import OctreeDriver
from param_sweeps.generate import generate
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.params import InversionBaseParams

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
        series).
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
        self._simulation_parameters: InversionBaseParams | None = None
        self._simulation_driver: InversionDriver | None = None
        self._out_group = self.validate_out_group(self.params.out_group)

        self._logger = get_logger("Plate Simulation")

    def run(self) -> InversionDriver:
        """Create octree mesh, fill model, and simulate."""

        self._logger.info("running the simulation...")
        self.simulation_driver.run()

        with fetch_active_workspace(self.params.geoh5, mode="r+"):
            self.out_group.add_ui_json()
            if (
                self.params.monitoring_directory is not None
                and Path(self.params.monitoring_directory).is_dir()
            ):
                monitored_directory_copy(
                    str(Path(self.params.monitoring_directory).resolve()),
                    self.out_group,
                )

        self._logger.info("done.")
        self._logger.handlers.clear()

        return self.simulation_driver

    @property
    def out_group(self) -> UIJsonGroup:
        """
        Returns the output group for the simulation.
        """
        return self._out_group

    def validate_out_group(self, out_group: UIJsonGroup | None) -> UIJsonGroup:
        """
        Validate or create a UIJsonGroup to store results.

        :param value: Output group from selection.
        """
        if isinstance(out_group, UIJsonGroup):
            return out_group

        with fetch_active_workspace(self.params.geoh5, mode="r+"):
            out_group = UIJsonGroup.create(
                self.params.geoh5,
                name="Plate Simulation",
            )
            out_group.entity_type.name = "Plate Simulation"
            self.params = self.params.model_copy(update={"out_group": out_group})
            out_group.options = InputFile.stringify(
                InputFile.demote(self.params.input_file.ui_json)
            )
            out_group.metadata = None

        return out_group

    @property
    def simulation_driver(self) -> InversionDriver:
        if self._simulation_driver is None:
            with fetch_active_workspace(self.params.geoh5, mode="r+"):
                self.simulation_parameters.mesh = self.mesh
                self.simulation_parameters.starting_model = self.model

                if not isinstance(
                    self.simulation_parameters.topography_object, Surface
                ):
                    raise ValueError(
                        "The topography object of the forward simulation must be a 'Surface'."
                    )

                self.simulation_parameters.update_group_options()
                self._simulation_driver = InversionDriver(self.simulation_parameters)
                self._simulation_driver.out_group.parent = self.out_group

        return self._simulation_driver

    @property
    def simulation_parameters(self) -> InversionBaseParams:
        if self._simulation_parameters is None:
            self._simulation_parameters = self.params.simulation_parameters()

        return self._simulation_parameters

    @property
    def survey(self):
        if self._survey is None:
            self._survey = self.simulation_parameters.data_object

        return self._survey

    @property
    def topography(self) -> Surface:
        return self.simulation_parameters.topography_object

    @property
    def surfaces(self) -> list[Surface]:
        """Returns a list of surfaces representing the plates for simulation."""

        if self._surfaces is None:
            offset = (
                self.params.model.overburden.thickness
                if self.params.model.plate.reference_surface == "overburden"
                else 0.0
            )
            center = self.params.model.plate.center(
                self.survey,
                self.topography,
                depth_offset=-1 * offset,
            )
            plate = Plate(
                self.params.model.plate,
                *center,
            )
            surface = plate.create_surface(self.params.geoh5, self.out_group)

            if self.params.model.plate.number == 1:
                self._surfaces = [surface]
            else:
                self._surfaces = replicate(
                    surface,
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
            self.survey, self.simulation_parameters.topography_object, self.surfaces
        )
        octree_driver = OctreeDriver(octree_params)
        mesh = octree_driver.run()
        mesh.parent = self.out_group

        return mesh

    def make_model(self) -> FloatData:
        """Create background + plate and overburden model from parameters."""

        self._logger.info("Building the model...")

        overburden = Overburden(
            topography=self.simulation_parameters.topography_object,
            thickness=self.params.model.overburden.thickness,
            value=self.params.model.overburden.overburden,
        )

        dikes = DikeSwarm(
            [Anomaly(s, self.params.model.plate.plate) for s in self.surfaces]
        )

        erosion = Erosion(
            surface=self.simulation_parameters.topography_object,
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
    # file = Path(sys.argv[1])
    file = r"C:\Users\dominiquef\Desktop\plate_simulation_standalone.ui.json"
    PlateSimulationDriver.start(file)
