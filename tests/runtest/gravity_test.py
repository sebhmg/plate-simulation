#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from copy import deepcopy

from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from simpeg_drivers.constants import default_ui_json

from plate_simulation.driver import PlateSimulationDriver
from plate_simulation.mesh.params import MeshParams
from plate_simulation.models.params import ModelParams, OverburdenParams, PlateParams
from plate_simulation.params import PlateSimulationParams
from plate_simulation.simulations.params import SimulationParams

from . import get_survey, get_topography


def test_gravity_plate_simulation(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        topography = get_topography(ws)
        survey = get_survey(ws, 10, 10)

        mesh_params = MeshParams(
            u_cell_size=10.0,
            v_cell_size=10.0,
            w_cell_size=10.0,
            padding_distance=1500.0,
            depth_core=600.0,
            max_distance=200.0,
        )

        overburden_params = OverburdenParams(thickness=50.0, value=5.0)

        plate_params = PlateParams(
            name="plate",
            value=2.0,
            center_x=0.0,
            center_y=0.0,
            center_z=-250.0,
            width=100.0,
            strike_length=100.0,
            dip_length=100.0,
            dip=0.0,
            dip_direction=0.0,
            reference="center",
        )

        model_params = ModelParams(
            name="density",
            background=1000.0,
            overburden=overburden_params,
            plate=plate_params,
        )

        options = deepcopy(default_ui_json)
        options["inversion_type"] = "gravity"
        options["forward_only"] = True
        options["geoh5"] = str(ws.h5file)
        options["topography_object"]["value"] = str(topography.uid)
        options["data_object"]["value"] = str(survey.uid)

        gravity_inversion = SimPEGGroup.create(ws)
        gravity_inversion.options = options
        simulation_params = SimulationParams.from_simpeg_group(gravity_inversion, ws)

        params = PlateSimulationParams(
            workspace=ws,
            mesh=mesh_params,
            model=model_params,
            simulation=simulation_params,
        )

        driver = PlateSimulationDriver(params)
        driver.run()
