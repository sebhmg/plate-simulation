# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                             '
#                                                                                      '
#  This file is part of plate-simulation package.                                      '
#                                                                                      '
#  plate-simulation is distributed under the terms and conditions of the MIT License   '
#  (see LICENSE file at the root of this source code package).                         '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Surface

from plate_simulation.utils import azimuth_to_unit_vector, replicate


def test_azimuth_to_unit_vector():
    assert np.allclose(azimuth_to_unit_vector(0.0), np.array([0.0, 1.0, 0.0]))
    assert np.allclose(azimuth_to_unit_vector(90.0), np.array([1.0, 0.0, 0.0]))
    assert np.allclose(azimuth_to_unit_vector(180.0), np.array([0.0, -1.0, 0.0]))
    assert np.allclose(azimuth_to_unit_vector(270.0), np.array([-1.0, 0.0, 0.0]))
    assert np.allclose(azimuth_to_unit_vector(360.0), np.array([0.0, 1.0, 0.0]))


def test_replicate_even(tmp_path):
    workspace = Workspace(tmp_path / "test.geoh5")
    surface = Surface.create(
        workspace,
        name="test",
        vertices=np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]),
        cells=np.array([[0, 1, 2], [0, 2, 3]]),
    )
    surfaces = replicate(surface, 2, 10.0, 90.0)
    assert surfaces[0].vertices is not None
    assert surfaces[1].vertices is not None
    assert surfaces[0].name == "test offset 1"
    assert np.allclose(surfaces[0].vertices.mean(axis=0), np.array([-5.0, 0.0, 0.0]))
    assert surfaces[1].name == "test offset 2"
    assert np.allclose(surfaces[1].vertices.mean(axis=0), np.array([5.0, 0.0, 0.0]))


def test_replicate_odd(tmp_path):
    workspace = Workspace(tmp_path / "test.geoh5")
    surface = Surface.create(
        workspace,
        name="test",
        vertices=np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]),
        cells=np.array([[0, 1, 2], [0, 2, 3]]),
    )
    surfaces = replicate(surface, 3, 5.0, 0.0)
    assert surfaces[0].vertices is not None
    assert surfaces[1].vertices is not None
    assert surfaces[2].vertices is not None
    assert np.allclose(surfaces[0].vertices.mean(axis=0), np.array([0.0, -5.0, 0.0]))
    assert np.allclose(surfaces[1].vertices.mean(axis=0), np.array([0.0, 0.0, 0.0]))
    assert np.allclose(surfaces[2].vertices.mean(axis=0), np.array([0.0, 5.0, 0.0]))
