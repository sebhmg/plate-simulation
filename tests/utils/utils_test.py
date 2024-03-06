#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

import numpy as np

from plate_simulation.utils import azimuth_to_unit_vector


def test_azimuth_to_unit_vector():
    assert np.allclose(azimuth_to_unit_vector(0.0), np.array([0.0, 1.0, 0.0]))
    assert np.allclose(azimuth_to_unit_vector(90.0), np.array([1.0, 0.0, 0.0]))
    assert np.allclose(azimuth_to_unit_vector(180.0), np.array([0.0, -1.0, 0.0]))
    assert np.allclose(azimuth_to_unit_vector(270.0), np.array([-1.0, 0.0, 0.0]))
    assert np.allclose(azimuth_to_unit_vector(360.0), np.array([0.0, 1.0, 0.0]))
