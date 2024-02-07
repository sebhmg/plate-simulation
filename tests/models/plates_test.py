#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np
from geoapps_utils.transformations import rotate_xyz
from geoh5py import Workspace

from plate_simulation.models.plates import Plate


def test_plate(tmp_path):
    workspace = Workspace(tmp_path / "test.geoh5")
    plate = Plate(
        center_x=0.0,
        center_y=0.0,
        center_z=0.0,
        length=1000.0,
        width=10.0,
        depth=500.0,
    )
    vertical_striking_north = plate.surface(workspace, "my plate")
    assert vertical_striking_north.vertices is not None
    assert vertical_striking_north.extent is not None
    assert np.isclose(
        vertical_striking_north.extent[1, 0] - vertical_striking_north.extent[0, 0],
        10.0,
    )
    assert np.isclose(
        vertical_striking_north.extent[1, 1] - vertical_striking_north.extent[0, 1],
        1000.0,
    )
    assert np.isclose(
        vertical_striking_north.extent[1, 2] - vertical_striking_north.extent[0, 2],
        500.0,
    )
    assert vertical_striking_north.vertices[:, 0].mean() == plate.center_x  # pylint: disable=no-member
    assert vertical_striking_north.vertices[:, 1].mean() == plate.center_y  # pylint: disable=no-member
    assert vertical_striking_north.vertices[:, 2].mean() == plate.center_z  # pylint: disable=no-member

    plate = Plate(
        center_x=0.0,
        center_y=0.0,
        center_z=0.0,
        length=1000.0,
        width=10.0,
        depth=500.0,
        dip=45.0,
        azimuth=0.0,
        reference="center",
    )
    dipping_striking_north = plate.surface(workspace, "my other plate")
    locs = rotate_xyz(dipping_striking_north.vertices, [0.0, 0.0, 0.0], -90.0, 0.0)
    locs = rotate_xyz(locs, [0.0, 0.0, 0.0], 0.0, 45.0)
    locs = rotate_xyz(locs, [0.0, 0.0, 0.0], 90.0, 0.0)
    assert np.allclose(locs, vertical_striking_north.vertices)

    plate = Plate(
        center_x=0.0,
        center_y=0.0,
        center_z=0.0,
        length=1000.0,
        width=10.0,
        depth=500.0,
        dip=0.0,
        azimuth=45.0,
        reference="center",
    )
    vertical_striking_northeast = plate.surface(workspace, "my third plate")
    locs = rotate_xyz(vertical_striking_northeast.vertices, [0.0, 0.0, 0.0], 45.0, 0.0)
    assert np.allclose(locs, vertical_striking_north.vertices)
