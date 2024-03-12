#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Points, Surface

from plate_simulation.models.params import PlateParams


def test_plate_params(tmp_path):
    workspace = Workspace(tmp_path / "test.geoh5")
    params = PlateParams(
        name="my plate",
        plate=1.0,
        depth=100.0,
        width=20.0,
        strike_length=1500.0,
        dip_length=400.0,
        dip=90.0,
        dip_direction=0.0,
        reference="center",
        true_elevation=False,
        number=1,
        spacing=10.0,
        x_offset=10.0,
        y_offset=10.0,
    )
    assert params.spacing == 0.0

    survey = Points.create(
        workspace,
        name="survey",
        vertices=np.array([[-10, -10, 0]]),
    )
    topography = Surface.create(
        workspace,
        name="test",
        vertices=np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]),
        cells=np.array([[0, 1, 2], [0, 2, 3]]),
    )

    center = params.center(survey, topography, true_elevation=True)
    assert np.allclose(center, np.array([[0, 0, 100]]))

    center = params.center(survey, topography, true_elevation=False)
    assert np.allclose(center, np.array([[0, 0, -300]]))
