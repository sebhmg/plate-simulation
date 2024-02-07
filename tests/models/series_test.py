#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np
import pytest
from geoh5py import Workspace
from geoh5py.objects import Surface
from octree_creation_app.driver import OctreeDriver
from octree_creation_app.params import OctreeParams

from plate_simulation.models.events import Deposition, Erosion, Overburden
from plate_simulation.models.series import GeologyViolationError, Lithology, Scenario

# pylint: disable=unbalanced-tuple-unpacking, duplicate-code


def test_lithology(tmp_path):  # pylint: disable=too-many-locals
    with Workspace(tmp_path / "test.geoh5") as ws:
        surfaces = []
        for elevation in [0.0, -2.0, -5.0, -10.0]:
            vertices = np.array(
                [
                    [0.0, 0.0, elevation],
                    [10.0, 0.0, elevation],
                    [10.0, 10.0, elevation],
                    [0.0, 10.0, elevation],
                ]
            )
            cells = np.array([[0, 1, 2], [0, 2, 3]])

            surfaces.append(
                Surface.create(ws, name="topo", vertices=vertices, cells=cells)
            )
        topography, layer1, layer2, layer3 = surfaces

        kwargs = {
            "geoh5": ws,
            "objects": topography,
            "u_cell_size": 0.5,
            "v_cell_size": 0.5,
            "w_cell_size": 0.5,
            "horizontal_padding": 10.0,
            "vertical_padding": 10.0,
            "depth_core": 5.0,
            "minimum_level": 4,
            "diagonal_balance": False,
            "Refinement A object": topography.uid,
            "Refinement A levels": [4, 2, 1],
            "Refinement A type": "surface",
        }
        driver = OctreeDriver(OctreeParams(**kwargs))
        octree = driver.run()
        layers = [
            Deposition(surface=layer3, value=3.0),
            Deposition(surface=layer2, value=2.0),
            Deposition(surface=layer1, value=1.0),
        ]
        lithology = Lithology(history=layers)
        lithology_model = lithology.realize(mesh=octree, model=np.zeros(octree.n_cells))
        model = octree.add_data({"model": {"values": lithology_model}})

        ind_background = octree.centroids[:, 2] > -2.0
        assert all(model.values[ind_background] == 0.0)
        ind_layer_1 = (octree.centroids[:, 2] < -2.0) & (octree.centroids[:, 2] > -5.0)
        assert all(model.values[ind_layer_1] == 1.0)
        ind_layer_2 = (octree.centroids[:, 2] < -5.0) & (octree.centroids[:, 2] > -10.0)
        assert all(model.values[ind_layer_2] == 2.0)
        ind_layer_3 = octree.centroids[:, 2] < -10.0
        assert all(model.values[ind_layer_3] == 3.0)


def test_scenario(tmp_path):  # pylint: disable=too-many-locals
    with Workspace(tmp_path / "test.geoh5") as ws:
        surfaces = []
        for elevation in [0.0, -2.0, -5.0, -10.0]:
            vertices = np.array(
                [
                    [0.0, 0.0, elevation],
                    [10.0, 0.0, elevation],
                    [10.0, 10.0, elevation],
                    [0.0, 10.0, elevation],
                ]
            )
            cells = np.array([[0, 1, 2], [0, 2, 3]])

            surfaces.append(
                Surface.create(ws, name="topo", vertices=vertices, cells=cells)
            )
        topography, layer1, layer2, layer3 = surfaces

        kwargs = {
            "geoh5": ws,
            "objects": topography,
            "u_cell_size": 0.5,
            "v_cell_size": 0.5,
            "w_cell_size": 0.5,
            "horizontal_padding": 10.0,
            "vertical_padding": 10.0,
            "depth_core": 5.0,
            "minimum_level": 4,
            "diagonal_balance": False,
            "Refinement A object": topography.uid,
            "Refinement A levels": [4, 2, 1],
            "Refinement A type": "surface",
        }
        driver = OctreeDriver(OctreeParams(**kwargs))
        octree = driver.run()
        layers = [
            Deposition(surface=layer3, value=3.0),
            Deposition(surface=layer2, value=2.0),
            Deposition(surface=layer1, value=1.0),
        ]
        lithology = Lithology(history=layers)
        overburden = Overburden(topography=topography, thickness=1.0, value=10.0)
        erosion = Erosion(surface=topography)

        with pytest.raises(
            GeologyViolationError,
            match="Overburden events must occur before the final erosion in the history.",
        ):
            scenario = Scenario(
                mesh=octree,
                background=0.0,
                history=[lithology, erosion, overburden],
                name="model",
            )

        with pytest.raises(
            GeologyViolationError,
            match="The last event in a geological history must be an erosion.",
        ):
            scenario = Scenario(
                mesh=octree,
                background=0.0,
                history=[overburden, lithology],
                name="model",
            )

        scenario = Scenario(
            mesh=octree,
            background=0.0,
            history=[lithology, overburden, erosion],
            name="model",
        )
        model = scenario.geologize()

        core_region_ind = (
            (octree.centroids[:, 0] < 10.0)
            & (octree.centroids[:, 0] > 0.0)
            & (octree.centroids[:, 1] < 10.0)
            & (octree.centroids[:, 1] > 0.0)
        )
        air_ind = octree.centroids[:, 2] > 0.0
        assert all(np.isnan(model.values[air_ind & core_region_ind]))
        overburden_ind = (octree.centroids[:, 2] < 0.0) & (
            octree.centroids[:, 2] > -1.0
        )
        assert all(model.values[overburden_ind & core_region_ind] == 10.0)
        background_ind = (octree.centroids[:, 2] < -1.0) & (
            octree.centroids[:, 2] > -2.0
        )
        assert all(model.values[background_ind & core_region_ind] == 0.0)
        layer1_ind = (octree.centroids[:, 2] < -2.0) & (octree.centroids[:, 2] > -5.0)
        assert all(model.values[layer1_ind & core_region_ind] == 1.0)
        layer2_ind = (octree.centroids[:, 2] < -5.0) & (octree.centroids[:, 2] > -10.0)
        assert all(model.values[layer2_ind & core_region_ind] == 2.0)
        layer3_ind = octree.centroids[:, 2] < -10.0
        assert all(model.values[layer3_ind & core_region_ind] == 3.0)
