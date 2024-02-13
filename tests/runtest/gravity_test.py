#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from copy import deepcopy

from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from octree_creation_app.params import OctreeParams
from simpeg_drivers.constants import default_ui_json

from plate_simulation.driver import PlateSimulationDriver
from plate_simulation.models.params import ModelParams, OverburdenParams, PlateParams
from plate_simulation.params import PlateSimulationParams

from . import get_survey, get_topography


def test_gravity_plate_simulation(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        topography = get_topography(ws)
        survey = get_survey(ws, 10, 10)

        octree_params = OctreeParams(
            objects=survey,
            u_cell_size=25.0,
            v_cell_size=25.0,
            w_cell_size=25.0,
            horizontal_padding=1000.0,
            vertical_padding=1000.0,
            depth_core=500.0,
            minimum_level=4,
            diagonal_balance=False,
            refinement_A_object=topography,
            refinement_A_levels=[4, 2, 1],
            refinement_A_type="surface",
        )

        overburden_params = OverburdenParams(thickness=50.0, value=0.2)

        plate_params = PlateParams(
            name="plate",
            anomaly=0.75,
            center_x=0.0,
            center_y=0.0,
            center_z=-250.0,
            length=100.0,
            width=100.0,
            depth=100.0,
            dip=0.0,
            azimuth=0.0,
            reference="center",
        )

        model_params = ModelParams(
            name="density",
            background=0.0,
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

        params = PlateSimulationParams(
            workspace=ws,
            topography=topography,
            octree=octree_params,
            model=model_params,
            simulation=gravity_inversion,
        )

        driver = PlateSimulationDriver(params)
        driver.run()
