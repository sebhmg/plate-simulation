#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from __future__ import annotations

from pathlib import Path

from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import fetch_active_workspace

from plate_simulation.driver import PlateSimulationDriver
from plate_simulation.params import PlateSimulationParams
from plate_simulation.series.params import SimulationSeriesParams


class SimulationSeriesDriver:
    """
    Driver for simulating background + plate + overburden model over a series
    of points parameters.

    :param params: Parameters for plate simulation (mesh, model).
    """

    def __init__(self, params: SimulationSeriesParams):
        self.params = params

    def run(self) -> SimPEGGroup:
        """Loop over the Points parameters and simulate data."""
        with fetch_active_workspace(self.params.geoh5, mode="r+") as workspace:
            input_file = InputFile.read_ui_json(self.params.plate_simulation)

            with fetch_active_workspace(input_file.geoh5) as input_geoh5:
                input_plate_parameters = PlateSimulationParams.build(input_file)
                simulation_json = input_plate_parameters.simulation.options
                simulation_json["geoh5"] = input_geoh5

                input_simulation_parameters: dict = InputFile(
                    ui_json=simulation_json, validate=False
                ).data

                survey = input_simulation_parameters["data_object"].copy(
                    parent=workspace
                )
                topography = input_simulation_parameters["topography_object"].copy(
                    parent=workspace, copy_children=False
                )

                if input_simulation_parameters["topography"] is not None:
                    input_simulation_parameters["topography"].copy(parent=topography)

                out_group = input_simulation_parameters["out_group"].copy(
                    parent=workspace, copy_children=False
                )

                # Map parameters to modify
                parameters = {
                    child.name: child.values
                    for child in self.params.point_parameters.children
                    if child.name in input_file.data
                }
                input_data = input_plate_parameters.flatten()
                input_data["simulation"] = out_group
                input_data["geoh5"] = workspace

                # Loop over vertices and update parameters
                for ind, vertex in enumerate(self.params.point_parameters.vertices):
                    # Center the position of the survey
                    mean_shift = vertex - survey.vertices.mean(axis=0)
                    mean_shift[2] = 0.0
                    survey.vertices = survey.vertices + mean_shift
                    survey.complement.vertices = survey.complement.vertices + mean_shift

                    # Set parameters for this vertex and run the simulation
                    input_data.update(
                        {name: values[ind] for name, values in parameters.items()}
                    )
                    input_data["out_group"] = None

                    plate_sim_params = PlateSimulationParams.build(input_data)
                    driver = PlateSimulationDriver(plate_sim_params).run()

                    if not self.params.save_all:
                        driver.inversion_data.entity.parent = workspace
                        workspace.remove_entity(out_group)

    @staticmethod
    def start(ifile: str | Path | InputFile):
        """Run the plate simulation driver from an input file."""

        if isinstance(ifile, str):
            ifile = Path(ifile)

        if isinstance(ifile, Path):
            ifile = InputFile.read_ui_json(ifile)

        if ifile.data is None:  # type: ignore
            raise ValueError("Input file has no data loaded.")

        with ifile.geoh5.open():  # type: ignore
            params = SimulationSeriesParams.build(ifile)

        return SimulationSeriesDriver(params).run()


if __name__ == "__main__":
    # file = Path(sys.argv[1])
    file = Path(r"C:\Users\dominiquef\Desktop\Working\point_runs.ui.json")
    SimulationSeriesDriver.start(file)
