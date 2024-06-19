# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                             '
#                                                                                      '
#  This file is part of plate-simulation package.                                      '
#                                                                                      '
#  plate-simulation is distributed under the terms and conditions of the MIT License   '
#  (see LICENSE file at the root of this source code package).                         '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
import pytest
from geoh5py import Workspace
from geoh5py.objects import Surface

from plate_simulation.models.events import Deposition, Erosion, Overburden
from plate_simulation.models.series import GeologyViolationError, Lithology, Scenario

from . import get_topo_mesh


def test_lithology(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        _, octree = get_topo_mesh(ws)
        surfaces = {}
        for n_layer, elevation in enumerate([-2.0, -5.0, -10.0]):
            vertices = np.array(
                [
                    [0.0, 0.0, elevation],
                    [10.0, 0.0, elevation],
                    [10.0, 10.0, elevation],
                    [0.0, 10.0, elevation],
                ]
            )
            cells = np.array([[0, 1, 2], [0, 2, 3]])

            surfaces[f"layer{n_layer+1}"] = Surface.create(
                ws, name="topo", vertices=vertices, cells=cells
            )

        lithology = Lithology(
            history=[
                Deposition(surface=surfaces["layer3"], value=3.0),
                Deposition(surface=surfaces["layer2"], value=2.0),
                Deposition(surface=surfaces["layer1"], value=1.0),
            ]
        )
        lithology_model = lithology.realize(mesh=octree, model=np.zeros(octree.n_cells))
        model = octree.add_data({"model": {"values": lithology_model}})

        assert all(model.values[octree.centroids[:, 2] > -2.0] == 0.0)
        ind_layer_1 = (octree.centroids[:, 2] < -2.0) & (octree.centroids[:, 2] > -5.0)
        assert all(model.values[ind_layer_1] == 1.0)
        ind_layer_2 = (octree.centroids[:, 2] < -5.0) & (octree.centroids[:, 2] > -10.0)
        assert all(model.values[ind_layer_2] == 2.0)
        assert all(model.values[octree.centroids[:, 2] < -10.0] == 3.0)


def test_scenario(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        topography, octree = get_topo_mesh(ws)
        surfaces = {}
        for n_layer, elevation in enumerate([-2.0, -5.0, -10.0]):
            surfaces[f"layer{n_layer+1}"] = Surface.create(
                ws,
                name="topo",
                vertices=np.array(
                    [
                        [0.0, 0.0, elevation],
                        [10.0, 0.0, elevation],
                        [10.0, 10.0, elevation],
                        [0.0, 10.0, elevation],
                    ]
                ),
                cells=np.array([[0, 1, 2], [0, 2, 3]]),
            )

        lithology = Lithology(
            history=[
                Deposition(surface=surfaces["layer3"], value=3.0),
                Deposition(surface=surfaces["layer2"], value=2.0),
                Deposition(surface=surfaces["layer1"], value=1.0),
            ]
        )
        overburden = Overburden(topography=topography, thickness=1.0, value=10.0)
        erosion = Erosion(surface=topography)

        with pytest.raises(
            GeologyViolationError,
            match="Overburden events must occur before the final erosion in the history.",
        ):
            Scenario(
                workspace=ws,
                mesh=octree,
                background=0.0,
                history=[lithology, erosion, overburden],
                name="model",
            )

        with pytest.raises(
            GeologyViolationError,
            match="The last event in a geological history must be an erosion.",
        ):
            Scenario(
                workspace=ws,
                mesh=octree,
                background=0.0,
                history=[overburden, lithology],
                name="model",
            )

        scenario = Scenario(
            workspace=ws,
            mesh=octree,
            background=0.0,
            history=[lithology, overburden, erosion],
            name="model",
        )
        model = scenario.geologize()
        assert model.values is not None

        ind = octree.centroids[:, 2] > 0.0
        assert all(np.isnan(model.values[ind]))
        ind = (octree.centroids[:, 2] < 0.0) & (octree.centroids[:, 2] > -1.0)
        assert all(model.values[ind] == 10.0)
        ind = (octree.centroids[:, 2] < -1.0) & (octree.centroids[:, 2] > -2.0)
        assert all(model.values[ind] == 0.0)
        ind = (octree.centroids[:, 2] < -2.0) & (octree.centroids[:, 2] > -5.0)
        assert all(model.values[ind] == 1.0)
        ind = (octree.centroids[:, 2] < -5.0) & (octree.centroids[:, 2] > -10.0)
        assert all(model.values[ind] == 2.0)
        ind = octree.centroids[:, 2] < -10.0
        assert all(model.values[ind] == 3.0)
