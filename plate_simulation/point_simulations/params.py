#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from geoapps_utils.driver.data import BaseData
from geoh5py.groups import UIJsonGroup
from geoh5py.objects import Curve, Points


class PointsSimulationParams(BaseData):
    """
    Parameters for the generation of simulations from Points values.

    :param simulation: A UIJsonGroup holding simulation parmarters.
    :param points: Points with simulation parameters.
    :param curve: Curve object to append data to.
    """

    simulation: UIJsonGroup
    points: Points
    curve: Curve | None = None
