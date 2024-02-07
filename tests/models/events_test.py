#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Surface
from octree_creation_app.driver import OctreeDriver
from octree_creation_app.params import OctreeParams

from plate_simulation.models.events import Deposition, Erosion, Overburden


def test_deposition(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        vertices = np.array(
            [
                [0.0, 0.0, 0.0],
                [10.0, 0.0, 0.0],
                [10.0, 10.0, 0.0],
                [0.0, 10.0, 0.0],
            ]
        )
        cells = np.array([[0, 1, 2], [0, 2, 3]])

        topography = Surface.create(ws, name="topo", vertices=vertices, cells=cells)

        vertices = np.array(
            [
                [0.0, 0.0, -5.0],
                [10.0, 0.0, -5.0],
                [10.0, 10.0, -5.0],
                [0.0, 10.0, -5.0],
            ]
        )
        cells = np.array([[0, 1, 2], [0, 2, 3]])

        surface = Surface.create(ws, name="boundary", vertices=vertices, cells=cells)

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

        deposition = Deposition(surface=surface, value=2.0)
        background = np.ones(octree.n_cells)
        deposition_model = deposition.realize(mesh=octree, model=background)
        model = octree.add_data({"model": {"values": deposition_model}})

        ind = octree.centroids[:, 2] < -5.0
        assert all(model.values[ind] == 2)
        assert all(model.values[~ind] == 1)


def test_erosion(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        vertices = np.array(
            [
                [0.0, 0.0, 0.0],
                [10.0, 0.0, 0.0],
                [10.0, 10.0, 0.0],
                [0.0, 10.0, 0.0],
            ]
        )
        cells = np.array([[0, 1, 2], [0, 2, 3]])

        topography = Surface.create(
            ws, name="my surface", vertices=vertices, cells=cells
        )

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

        erosion = Erosion(surface=topography)
        background = np.ones(octree.n_cells)
        erosion_model = erosion.realize(mesh=octree, model=background)
        model = octree.add_data({"model": {"values": erosion_model}})

        ind = octree.centroids[:, 2] < 0.0
        assert all(np.isfinite(model.values[ind]))
        assert all(np.isnan(model.values[~ind]))


def test_overburden(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        vertices = np.array(
            [
                [0.0, 0.0, 0.0],
                [10.0, 0.0, 0.0],
                [10.0, 10.0, 0.0],
                [0.0, 10.0, 0.0],
            ]
        )
        cells = np.array([[0, 1, 2], [0, 2, 3]])

        topography = Surface.create(
            ws, name="my surface", vertices=vertices, cells=cells
        )

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

        overburden = Overburden(topography=topography, thickness=5.0, value=2.0)
        background = np.ones(octree.n_cells)
        overburden_model = overburden.realize(mesh=octree, model=background)
        model = octree.add_data({"model": {"values": overburden_model}})

        ind = octree.centroids[:, 2] < -5.0
        assert all(model.values[ind] == 1)
        assert all(model.values[~ind] == 2)
