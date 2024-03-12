#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#
#

from copy import deepcopy
from pathlib import Path
from uuid import UUID

import numpy as np
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import ObjectBase, Surface
from geoh5py.ui_json import InputFile
from simpeg_drivers.electromagnetics.time_domain.constants import (
    default_ui_json as tdem_default_ui_json,
)
from simpeg_drivers.potential_fields.gravity.constants import (
    default_ui_json as gravity_default_ui_json,
)
from simpeg_drivers.potential_fields.gravity.params import GravityParams

from plate_simulation import assets_path
from plate_simulation.driver import PlateSimulationDriver, PlateSimulationParams
from plate_simulation.mesh.params import MeshParams
from plate_simulation.models.params import ModelParams

from . import get_survey, get_topography

# pylint: disable=duplicate-code


def get_simulation_group(workspace: Workspace, survey: ObjectBase, topography: Surface):
    tem_inversion = SimPEGGroup.create(workspace)
    options = deepcopy(InputFile.stringify(tdem_default_ui_json))
    options["inversion_type"] = "tdem"
    options["forward_only"] = True
    options["geoh5"] = str(workspace.h5file)
    options["topography_object"]["value"] = str(topography.uid)
    options["data_object"]["value"] = str(survey.uid)
    options["x_channel_bool"] = True
    options["y_channel_bool"] = True
    options["z_channel_bool"] = True
    tem_inversion.options = options

    return tem_inversion


def get_input_file(filepath: Path) -> InputFile:
    with Workspace(filepath / "test.geoh5") as ws:
        with Workspace(assets_path() / "demo.geoh5") as demo_workspace:
            survey = demo_workspace.get_entity("Simulation rx")[0].copy(
                parent=ws, copy_children=False
            )
            topography = demo_workspace.get_entity("Topography")[0].copy(parent=ws)

            mask = np.zeros(survey.n_vertices, dtype=bool)
            mask[::10] = True
            new_survey = survey.copy(mask=mask)
            new_survey.cells = np.c_[
                np.arange(new_survey.n_vertices - 1),
                np.arange(1, new_survey.n_vertices),
            ]
            new_survey.transmitters.cells = np.c_[
                np.arange(new_survey.n_vertices - 1),
                np.arange(1, new_survey.n_vertices),
            ]

        simulation = get_simulation_group(ws, new_survey, topography)

        ifile = InputFile.read_ui_json(
            assets_path() / "uijson" / "plate_simulation.ui.json", validate=False
        )
        ifile.set_data_value("name", "test_tem_plate_simulation")
        ifile.set_data_value("geoh5", ws)
        ifile.set_data_value("simulation", simulation)
        ifile.set_data_value("u_cell_size", 50.0)
        ifile.set_data_value("v_cell_size", 50.0)
        ifile.set_data_value("w_cell_size", 50.0)
        ifile.set_data_value("depth_core", 600.0)
        ifile.set_data_value("max_distance", 200.0)
        ifile.set_data_value("padding_distance", 1000.0)
        ifile.set_data_value("background", 2000.0)
        ifile.set_data_value("overburden", 7500.0)
        ifile.set_data_value("thickness", 50.0)
        ifile.set_data_value("plate", 20.0)
        ifile.set_data_value("x_offset", 100.0)
        ifile.set_data_value("y_offset", 100.0)
        ifile.set_data_value("depth", -175.0)
        ifile.set_data_value("true_elevation", True)
        ifile.set_data_value("width", 100.0)
        ifile.set_data_value("strike_length", 1000.0)
        ifile.set_data_value("dip_length", 300.0)
        ifile.set_data_value("dip", 65.0)
        ifile.set_data_value("dip_direction", 65.0)
        ifile.set_data_value("number", 2)
        ifile.set_data_value("spacing", 600.0)

    return ifile


def test_plate_simulation(tmp_path):
    ifile = get_input_file(tmp_path)
    ifile.write_ui_json("test_plate_simulation.ui.json", path=tmp_path)
    result = PlateSimulationDriver.main(
        Path(tmp_path / "test_plate_simulation.ui.json")
    )
    with Workspace(result.options["geoh5"]) as ws:
        data = ws.get_entity(UUID(result.options["data_object"]["value"]))[0]
        mesh = ws.get_entity(UUID(result.options["mesh"]["value"]))[0]
        model = [k for k in mesh.children if k.name == "starting_model"][0]

        assert len(data.property_groups) == 3
        assert all(
            k.name in [f"Iteration_0_{i}" for i in "xyz"] for k in data.property_groups
        )
        assert all(len(k.properties) == 20 for k in data.property_groups)
        assert mesh.n_cells == 14961
        assert len(np.unique(model.values)) == 4
        assert all(
            k in np.unique(model.values) for k in [1.0 / 7500, 1.0 / 2000, 1.0 / 20]
        )
        assert any(np.isnan(np.unique(model.values)))


# pylint: disable=too-many-statements
def test_plate_simulation_params_from_input_file(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        topography = get_topography(ws)
        survey = get_survey(ws, 10, 10)

        ifile = InputFile.read_ui_json(
            assets_path() / "uijson" / "plate_simulation.ui.json", validate=False
        )
        ifile.data["name"] = "test_gravity_plate_simulation"
        ifile.data["geoh5"] = ws

        # Add simulation parameter
        gravity_inversion = SimPEGGroup.create(ws)
        options = deepcopy(gravity_default_ui_json)
        options["inversion_type"] = "gravity"
        options["forward_only"] = True
        options["geoh5"] = str(ws.h5file)
        options["topography_object"]["value"] = str(topography.uid)
        options["data_object"]["value"] = str(survey.uid)
        gravity_inversion.options = options
        ifile.data["simulation"] = gravity_inversion

        # Add mesh parameters
        ifile.data["u_cell_size"] = 10.0
        ifile.data["v_cell_size"] = 10.0
        ifile.data["w_cell_size"] = 10.0
        ifile.data["depth_core"] = 400.0
        ifile.data["max_distance"] = 200.0
        ifile.data["padding_distance"] = 1500.0

        # Add model parameters
        ifile.data["background"] = 1000.0
        ifile.data["overburden"] = 5.0
        ifile.data["thickness"] = 50.0
        ifile.data["plate"] = 2.0
        ifile.data["depth"] = -250
        ifile.data["width"] = 100.0
        ifile.data["strike_length"] = 100.0
        ifile.data["dip_length"] = 100.0
        ifile.data["dip"] = 0.0
        ifile.data["dip_direction"] = 0.0
        ifile.data["number"] = 9
        ifile.data["spacing"] = 10.0
        ifile.data["x_offset"] = 10.0
        ifile.data["y_offset"] = 10.0

        params = PlateSimulationParams.build(ifile)
        assert isinstance(params.simulation, GravityParams)
        assert params.simulation.inversion_type == "gravity"
        assert params.simulation.forward_only
        assert params.simulation.geoh5.h5file == ws.h5file
        assert params.simulation.topography_object.uid == topography.uid
        assert params.simulation.data_object.uid == survey.uid

        assert isinstance(params.mesh, MeshParams)
        assert params.mesh.u_cell_size == 10.0
        assert params.mesh.v_cell_size == 10.0
        assert params.mesh.w_cell_size == 10.0
        assert params.mesh.depth_core == 400.0
        assert params.mesh.max_distance == 200.0
        assert params.mesh.padding_distance == 1500.0
        assert params.mesh.minimum_level == 8
        assert not params.mesh.diagonal_balance

        assert isinstance(params.model, ModelParams)
        assert params.model.name == "test_gravity_plate_simulation"
        assert params.model.background == 0.001
        assert params.model.overburden.thickness == 50.0
        assert params.model.overburden.overburden == 0.2
        assert params.model.plate.plate == 0.5
        assert params.model.plate.depth == -250.0
        assert params.model.plate.width == 100.0
        assert params.model.plate.strike_length == 100.0
        assert params.model.plate.dip_length == 100.0
        assert params.model.plate.dip == 0.0
        assert params.model.plate.dip_direction == 0.0
        assert params.model.plate.reference == "center"
        assert params.model.plate.number == 9
        assert params.model.plate.spacing == 10.0
        assert params.model.plate.x_offset == 10.0
        assert params.model.plate.y_offset == 10.0
