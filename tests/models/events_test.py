#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Surface

from plate_simulation.models.events import Anomaly, Deposition, Erosion, Overburden
from plate_simulation.models.params import PlateParams
from plate_simulation.models.plates import Plate

from . import get_topo_mesh


def test_deposition(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        topography, octree = get_topo_mesh(ws)
        locs = topography.vertices.copy()
        locs[:, 2] -= 5.0
        surface = Surface.create(ws, vertices=locs, cells=topography.cells)

        deposition = Deposition(surface=surface, value=2.0)
        background = np.ones(octree.n_cells)
        deposition_model = deposition.realize(mesh=octree, model=background)
        model = octree.add_data({"model": {"values": deposition_model}})

        ind = octree.centroids[:, 2] < -5.0
        assert all(model.values[ind] == 2)
        assert all(model.values[~ind] == 1)


def test_erosion(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        topography, octree = get_topo_mesh(ws)
        erosion = Erosion(surface=topography)
        background = np.ones(octree.n_cells)
        erosion_model = erosion.realize(mesh=octree, model=background)
        model = octree.add_data({"model": {"values": erosion_model}})

        ind = octree.centroids[:, 2] < 0.0
        assert all(np.isfinite(model.values[ind]))
        assert all(np.isnan(model.values[~ind]))


def test_overburden(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        topography, octree = get_topo_mesh(ws)
        overburden = Overburden(topography=topography, thickness=5.0, value=2.0)
        background = np.ones(octree.n_cells)
        overburden_model = overburden.realize(mesh=octree, model=background)
        model = octree.add_data({"model": {"values": overburden_model}})

        ind = octree.centroids[:, 2] < -5.0
        assert all(model.values[ind] == 1)
        assert all(model.values[~ind] == 2)


def test_anomaly(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        _, octree = get_topo_mesh(ws)
        params = PlateParams(
            name="my plate",
            value=10.0,
            center_x=5.0,
            center_y=5.0,
            center_z=-1.5,
            width=10.0,
            strike_length=10.0,
            dip_length=1.0,
        )
        plate = Plate(ws, params)
        anomaly = Anomaly(surface=plate.surface, value=10.0)
        model = anomaly.realize(mesh=octree, model=np.ones(octree.n_cells))
        data = octree.add_data({"model": {"values": model}})
        ind = (
            (octree.centroids[:, 0] > 0.0)
            & (octree.centroids[:, 0] < 10.0)
            & (octree.centroids[:, 1] > 0.0)
            & (octree.centroids[:, 1] < 10.0)
            & (octree.centroids[:, 2] > -2.0)
            & (octree.centroids[:, 2] < -1.0)
        )
        assert all(data.values[ind] == 10.0)
