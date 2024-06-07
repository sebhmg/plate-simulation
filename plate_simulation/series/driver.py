#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from __future__ import annotations

from pathlib import Path

import numpy as np
from geoh5py import Workspace
from geoh5py.groups import PropertyGroup, SimPEGGroup
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import fetch_active_workspace
from scipy.spatial import cKDTree
from simpeg_drivers.driver import InversionDriver

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
        self._tree: cKDTree | None = None
        self.params = params

    def run(self) -> SimPEGGroup:
        """Loop over the Points parameters and simulate data."""
        temp_workspace = Workspace()
        with fetch_active_workspace(self.params.geoh5, mode="r+") as workspace:
            plate_sim_params, forward_sim_params = self.transfer_simulation_parameters(
                workspace
            )
            # Map parameters to modify
            parameters = {
                child.name: child.values
                for child in self.params.point_parameters.children
                if child.name in plate_sim_params
            }
            survey = forward_sim_params["data_object"].copy(parent=temp_workspace)

        # Loop over vertices and update parameters
        for ind, vertex in enumerate(self.params.point_parameters.vertices):
            # Center the position of the survey
            mean_shift = vertex - survey.vertices.mean(axis=0)
            mean_shift[2] = 0.0
            survey.vertices = survey.vertices + mean_shift
            survey.complement.vertices = survey.complement.vertices + mean_shift

            # Set parameters for this vertex and run the simulation
            plate_sim_params.update(
                {name: values[ind] for name, values in parameters.items()}
            )
            plate_sim_params["out_group"] = None

            plate_sim_params = PlateSimulationParams.build(plate_sim_params)
            driver = PlateSimulationDriver(plate_sim_params).run()

            if not self.params.save_all:
                driver.inversion_data.entity.parent = workspace
                workspace.remove_entity(driver.out_group)

            if self.params.output_curve is not None:
                self.interpolate_on_output(driver)

    def transfer_simulation_parameters(self, workspace) -> tuple[dict, dict]:
        """
        Transfer the simulation parameters from the plate_simulation input file
        to the current workspace.
        """
        input_file = InputFile.read_ui_json(self.params.plate_simulation)

        with fetch_active_workspace(input_file.geoh5) as input_geoh5:
            plate_sim_params = input_file.data.copy()
            input_plate_parameters = PlateSimulationParams.build(plate_sim_params)
            simulation_json = input_plate_parameters.simulation.options
            simulation_json["geoh5"] = input_geoh5

            forward_sim_params: dict = InputFile(
                ui_json=simulation_json, validate=False
            ).data.copy()

            forward_sim_params["data_object"] = forward_sim_params["data_object"].copy(
                parent=workspace
            )
            forward_sim_params["topography_object"] = forward_sim_params[
                "topography_object"
            ].copy(parent=workspace, copy_children=False)

            if forward_sim_params["topography"] is not None:
                forward_sim_params["topography"] = forward_sim_params[
                    "topography"
                ].copy(parent=forward_sim_params["topography_object"])

            plate_sim_params["simulation"] = forward_sim_params["out_group"].copy(
                parent=workspace, copy_children=False
            )

        plate_sim_params["geoh5"] = workspace

        return plate_sim_params, forward_sim_params

    def interpolate_on_output(self, driver: InversionDriver):
        """
        Interpolate the output data onto the output curve.

        :param driver: The driver object containing the output data.
        """
        center = driver.inversion_data.entity.vertices.mean(axis=0)

        # Compute distance about the center of simulated data
        local_distances = np.linalg.norm(
            driver.inversion_data.entity.vertices[:, :2]
            - driver.inversion_data.entity.vertices[0, :2],
            axis=1,
        )
        local_distances -= local_distances.max() / 2.0

        _, ind = self.tree.query(center[:2])

        if (
            self.params.output_curve.vertices is None
            or self.params.output_curve.parts is None
        ):
            raise ValueError("Output curve must have vertices and parts set.")

        part_id = self.params.output_curve.parts[ind]
        part_mask = self.params.output_curve.parts == part_id

        centered_distances = (
            self.params.output_distances[part_mask] - self.params.output_distances[ind]
        )

        with self.params.geoh5.open(mode="r+") as workspace:
            survey = workspace.get_entity(driver.inversion_data.entity.uid)
            # Get the only property group
            prop_group: PropertyGroup = survey.property_groups[0]

            # Interpolate the data
            for uid in prop_group.properties:
                data = survey.get_data(uid)[0]

                if data is None:
                    raise ValueError(f"Data {uid} not found in survey {survey.name}.")

                values = np.interp(centered_distances, local_distances, data.values)
                self.params.output_curve.add_data(
                    {
                        name: {
                            "values": values,
                            "entity_type": values["entity_type"],
                            "association": "VERTEX",
                        }
                    }
                )

    @property
    def tree(self) -> cKDTree:
        """Create a horizontal KDTree for the output curve object."""
        if self._tree is None and self.params.output_curve is not None:
            self._tree = cKDTree(self.params.output_curve.vertices[:, :2])

        return self._tree

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
