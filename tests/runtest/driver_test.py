#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#
#

from copy import deepcopy

from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile
from simpeg_drivers.potential_fields.gravity.constants import default_ui_json
from simpeg_drivers.potential_fields.gravity.params import GravityParams

from plate_simulation import assets_path
from plate_simulation.driver import PlateSimulationDriver
from plate_simulation.mesh.params import MeshParams
from plate_simulation.models.params import ModelParams

from . import get_survey, get_topography


def test_gravity_plate_simulation_params_from_input_file(tmp_path):
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
        options = deepcopy(default_ui_json)
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
        ifile.data["center_x"] = 0.0
        ifile.data["center_y"] = 0.0
        ifile.data["center_z"] = -250.0
        ifile.data["width"] = 100.0
        ifile.data["strike_length"] = 100.0
        ifile.data["dip_length"] = 100.0
        ifile.data["dip"] = 0.0
        ifile.data["dip_direction"] = 0.0

        params = PlateSimulationDriver.params_from_input_file(ifile)
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
        assert params.model.overburden.value == 0.2
        assert params.model.plate.value == 0.5
        assert params.model.plate.center_x == 0.0
        assert params.model.plate.center_y == 0.0
        assert params.model.plate.center_z == -250.0
        assert params.model.plate.width == 100.0
        assert params.model.plate.strike_length == 100.0
        assert params.model.plate.dip_length == 100.0
        assert params.model.plate.dip == 0.0
        assert params.model.plate.dip_direction == 0.0
        assert params.model.plate.reference == "center"
