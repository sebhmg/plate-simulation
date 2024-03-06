#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from plate_simulation.models.params import PlateParams


def test_plate_params():
    params = PlateParams(
        name="my plate",
        value=1.0,
        center_x=0.0,
        center_y=0.0,
        depth=0.0,
        width=10.0,
        strike_length=1000.0,
        dip=90.0,
        dip_length=500.0,
        dip_direction=0.0,
        reference="center",
        number=1,
        spacing=10.0,
    )
    assert params.spacing == 0.0
